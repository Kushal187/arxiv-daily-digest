from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import json
import logging
from typing import Any

from ..db import advisory_lock_key, get_connection
from .arxiv import fetch_entries_for_window
from .clustering import cluster_papers
from .embeddings import embed_texts_batch, vector_literal
from .topics import infer_topics


DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.IR", "stat.ML", "cs.RO", "eess.AS"]
RETENTION_DAYS = 120
logger = logging.getLogger(__name__)


def _run_window(run_date: date) -> tuple[datetime, datetime]:
    end = datetime.combine(run_date, time.max, tzinfo=timezone.utc)
    start = end - timedelta(hours=36)
    return start, end


def _job_status(connection, job_name: str, run_date: date) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select id, status, metadata
            from job_runs
            where job_name = %s
              and run_date = %s
            limit 1
            """,
            (job_name, run_date),
        )
        return cursor.fetchone()


def _start_job(connection, job_name: str, run_date: date) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into job_runs (job_name, run_date, status, metadata)
            values (%s, %s, 'started', '{}'::jsonb)
            on conflict (job_name, run_date)
            do update set status = 'started', started_at = now(), completed_at = null, metadata = '{}'::jsonb
            """,
            (job_name, run_date),
        )


def _finish_job(connection, job_name: str, run_date: date, status: str, metadata: dict[str, Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            update job_runs
            set status = %s,
                completed_at = now(),
                metadata = %s::jsonb
            where job_name = %s
              and run_date = %s
            """,
            (status, json.dumps(metadata), job_name, run_date),
        )


def _upsert_paper(connection, paper: dict[str, Any], cluster: dict[str, Any], ingest_date: date) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into papers (
              canonical_arxiv_id,
              arxiv_version,
              source_id,
              title,
              abstract,
              authors,
              categories,
              primary_category,
              published_at,
              updated_at,
              url,
              embedding,
              ingest_date,
              classifier_metadata
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s, %s::jsonb)
            on conflict (canonical_arxiv_id, arxiv_version)
            do update set
              title = excluded.title,
              abstract = excluded.abstract,
              authors = excluded.authors,
              categories = excluded.categories,
              primary_category = excluded.primary_category,
              published_at = excluded.published_at,
              updated_at = excluded.updated_at,
              url = excluded.url,
              embedding = excluded.embedding,
              ingest_date = excluded.ingest_date,
              classifier_metadata = excluded.classifier_metadata
            returning id
            """,
            (
                paper["canonical_arxiv_id"],
                paper["arxiv_version"],
                paper["source_id"],
                paper["title"],
                paper["abstract"],
                paper["authors"],
                paper["categories"],
                paper["primary_category"],
                paper["published_at"],
                paper["updated_at"],
                paper["url"],
                vector_literal(paper["embedding"]),
                ingest_date,
                json.dumps(paper["classifier_metadata"]),
            ),
        )
        paper_id = cursor.fetchone()["id"]

        cursor.execute("delete from paper_authors where paper_id = %s", (paper_id,))
        cursor.execute("delete from paper_topics where paper_id = %s", (paper_id,))
        cursor.execute("delete from paper_clusters where paper_id = %s", (paper_id,))

        for index, author in enumerate(paper["authors"]):
            cursor.execute(
                """
                insert into paper_authors (paper_id, author_name, author_position)
                values (%s, %s, %s)
                """,
                (paper_id, author, index),
            )

        for topic in paper["topics"]:
            cursor.execute(
                """
                insert into paper_topics (paper_id, topic_slug, confidence, is_hidden, source)
                values (%s, %s, %s, %s, %s)
                """,
                (paper_id, topic["slug"], topic["confidence"], topic["is_hidden"], topic["source"]),
            )

        cursor.execute(
            """
            insert into paper_clusters (paper_id, cluster_date, cluster_id, cluster_label)
            values (%s, %s, %s, %s)
            """,
            (paper_id, cluster["cluster_date"], cluster["cluster_id"], cluster["cluster_label"]),
        )

    return paper_id


def _upsert_papers_batch(
    connection,
    papers: list[dict[str, Any]],
    clusters: dict[str, dict],
    ingest_date: date,
) -> list[str]:
    """Batch-upsert papers with minimal round-trips to the database."""
    if not papers:
        return []

    with connection.cursor() as cursor:
        paper_rows = [
            (
                paper["canonical_arxiv_id"],
                paper["arxiv_version"],
                paper["source_id"],
                paper["title"],
                paper["abstract"],
                paper["authors"],
                paper["categories"],
                paper["primary_category"],
                paper["published_at"],
                paper["updated_at"],
                paper["url"],
                vector_literal(paper["embedding"]),
                ingest_date,
                json.dumps(paper["classifier_metadata"]),
            )
            for paper in papers
        ]

        cursor.executemany(
            """
            insert into papers (
              canonical_arxiv_id, arxiv_version, source_id, title, abstract,
              authors, categories, primary_category, published_at, updated_at,
              url, embedding, ingest_date, classifier_metadata
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s, %s::jsonb)
            on conflict (canonical_arxiv_id, arxiv_version)
            do update set
              title = excluded.title, abstract = excluded.abstract,
              authors = excluded.authors, categories = excluded.categories,
              primary_category = excluded.primary_category,
              published_at = excluded.published_at, updated_at = excluded.updated_at,
              url = excluded.url, embedding = excluded.embedding,
              ingest_date = excluded.ingest_date, classifier_metadata = excluded.classifier_metadata
            """,
            paper_rows,
            returning=False,
        )

        source_ids = [paper["source_id"] for paper in papers]
        cursor.execute(
            "select id, source_id from papers where source_id = any(%s)",
            (source_ids,),
        )
        id_map = {row["source_id"]: row["id"] for row in cursor.fetchall()}

        paper_ids = [id_map[sid] for sid in source_ids]

        cursor.execute("delete from paper_authors where paper_id = any(%s)", (paper_ids,))
        cursor.execute("delete from paper_topics where paper_id = any(%s)", (paper_ids,))
        cursor.execute("delete from paper_clusters where paper_id = any(%s)", (paper_ids,))

        author_rows = []
        for paper in papers:
            pid = id_map[paper["source_id"]]
            for idx, author in enumerate(paper["authors"]):
                author_rows.append((pid, author, idx))

        if author_rows:
            cursor.executemany(
                "insert into paper_authors (paper_id, author_name, author_position) values (%s, %s, %s)",
                author_rows,
                returning=False,
            )

        topic_rows = []
        for paper in papers:
            pid = id_map[paper["source_id"]]
            for topic in paper["topics"]:
                topic_rows.append((pid, topic["slug"], topic["confidence"], topic["is_hidden"], topic["source"]))

        if topic_rows:
            cursor.executemany(
                "insert into paper_topics (paper_id, topic_slug, confidence, is_hidden, source) values (%s, %s, %s, %s, %s)",
                topic_rows,
                returning=False,
            )

        cluster_rows = []
        for paper in papers:
            pid = id_map[paper["source_id"]]
            cluster = clusters.get(
                paper["source_id"],
                {"cluster_date": ingest_date, "cluster_id": "misc", "cluster_label": "misc"},
            )
            cluster_rows.append((pid, cluster["cluster_date"], cluster["cluster_id"], cluster["cluster_label"]))

        if cluster_rows:
            cursor.executemany(
                "insert into paper_clusters (paper_id, cluster_date, cluster_id, cluster_label) values (%s, %s, %s, %s)",
                cluster_rows,
                returning=False,
            )

    return paper_ids


def _enrich_papers(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not papers:
        return []

    texts_to_embed = [f"{paper['title']}\n\n{paper['abstract']}" for paper in papers]
    embeddings = embed_texts_batch(texts_to_embed)
    enriched = []
    for paper, embedding in zip(papers, embeddings):
        topics = infer_topics(paper["title"], paper["abstract"], paper["categories"], embedding=embedding)
        paper["embedding"] = embedding
        paper["topics"] = topics
        paper["classifier_metadata"] = {
            "topic_count": len(topics),
            "max_confidence": max([topic["confidence"] for topic in topics], default=0),
        }
        enriched.append(paper)

    return enriched


def _upsert_enriched_papers(
    connection,
    papers: list[dict[str, Any]],
    *,
    cluster_date: date,
    ingest_date: date,
) -> list[str]:
    clusters = cluster_papers(papers, cluster_date)
    return _upsert_papers_batch(connection, papers, clusters, ingest_date=ingest_date)


def _history_windows(start_date: date, end_date: date, days_per_window: int = 7) -> list[tuple[datetime, datetime]]:
    windows: list[tuple[datetime, datetime]] = []
    cursor = start_date
    while cursor <= end_date:
        chunk_end_date = min(cursor + timedelta(days=days_per_window - 1), end_date)
        window_start = datetime.combine(cursor, time.min, tzinfo=timezone.utc)
        window_end = datetime.combine(chunk_end_date, time.max, tzinfo=timezone.utc)
        windows.append((window_start, window_end))
        cursor = chunk_end_date + timedelta(days=1)

    return windows


def run_daily_ingest(run_date: date | None = None, force: bool = False) -> dict[str, Any]:
    run_date = run_date or datetime.now(timezone.utc).date()
    window_start, window_end = _run_window(run_date)
    job_name = "daily-ingest"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select pg_try_advisory_xact_lock(%s) as locked", (advisory_lock_key("daily-ingest"),))
            lock_result = cursor.fetchone()

        if not lock_result["locked"]:
            return {"status": "locked", "runDate": run_date.isoformat()}

        try:
            existing = _job_status(connection, job_name, run_date)
            if existing and existing["status"] == "succeeded" and not force:
                return {"status": "skipped", "runDate": run_date.isoformat(), "reason": "already ingested"}

            _start_job(connection, job_name, run_date)

            papers = fetch_entries_for_window(DEFAULT_CATEGORIES, window_start, window_end)

            if not papers:
                is_weekday = run_date.weekday() < 5
                if is_weekday and not force:
                    logger.warning(
                        "arXiv API returned 0 papers in window [%s, %s] on weekday %s. "
                        "This is unusual and may indicate an API outage.",
                        window_start.isoformat(),
                        window_end.isoformat(),
                        run_date.isoformat(),
                    )
                else:
                    logger.info(
                        "0 papers in window [%s, %s] for run_date=%s.",
                        window_start.isoformat(),
                        window_end.isoformat(),
                        run_date.isoformat(),
                    )

            enriched = _enrich_papers(papers)
            upserted_ids = _upsert_enriched_papers(connection, enriched, cluster_date=run_date, ingest_date=run_date)

            connection.commit()
            metadata = {
                "fetched_count": len(papers),
                "upserted_count": len(upserted_ids),
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
            }
            _finish_job(connection, job_name, run_date, "succeeded", metadata)
            connection.commit()
        except Exception as exc:
            connection.rollback()
            _finish_job(connection, job_name, run_date, "failed", {"error": str(exc)})
            connection.commit()
            raise

    # Run cleanup outside the connection block so it doesn't block future ingests
    try:
        cleanup_result = run_cleanup()
        metadata["cleanup"] = cleanup_result
    except Exception as cleanup_exc:
        logger.warning("Post-ingest cleanup failed (non-fatal): %s", cleanup_exc)
        metadata["cleanup"] = {"status": "failed", "error": str(cleanup_exc)}

    return {"status": "succeeded", "runDate": run_date.isoformat(), **metadata}


def run_cleanup(retention_days: int = RETENTION_DAYS) -> dict[str, Any]:
    """Delete papers older than retention_days to keep DB size under control.

    Related rows in paper_authors, paper_topics, paper_clusters,
    paper_summaries, and user_interactions are removed via ON DELETE CASCADE.
    """
    cutoff = date.today() - timedelta(days=retention_days)
    logger.info("Running cleanup: deleting papers with ingest_date < %s", cutoff.isoformat())

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "delete from papers where ingest_date < %s",
                (cutoff,),
            )
            deleted_count = cursor.rowcount

            cursor.execute(
                "delete from job_runs where run_date < %s",
                (cutoff,),
            )
            deleted_jobs = cursor.rowcount

        connection.commit()
        logger.info("Cleanup complete: removed %s papers and %s job_runs", deleted_count, deleted_jobs)
        return {
            "status": "succeeded",
            "cutoff_date": cutoff.isoformat(),
            "deleted_papers": deleted_count,
            "deleted_job_runs": deleted_jobs,
        }


def run_history_backfill(
    start_date: date,
    end_date: date,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    categories = categories or DEFAULT_CATEGORIES
    job_name = f"history-backfill:{start_date.isoformat()}"
    windows = _history_windows(start_date, end_date)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select pg_try_advisory_xact_lock(%s) as locked", (advisory_lock_key("history-backfill"),))
            lock_result = cursor.fetchone()

        if not lock_result["locked"]:
            return {
                "status": "locked",
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
            }

        try:
            _start_job(connection, job_name, end_date)
            fetched_count = 0
            upserted_count = 0

            for index, (window_start, window_end) in enumerate(windows, start=1):
                logger.info(
                    "History backfill window %s/%s: %s -> %s",
                    index,
                    len(windows),
                    window_start.date().isoformat(),
                    window_end.date().isoformat(),
                )
                papers = fetch_entries_for_window(categories, window_start, window_end)
                fetched_count += len(papers)
                logger.info(
                    "Fetched %s papers for window %s/%s",
                    len(papers),
                    index,
                    len(windows),
                )
                enriched = _enrich_papers(papers)
                upserted_ids = _upsert_enriched_papers(
                    connection,
                    enriched,
                    cluster_date=window_end.date(),
                    ingest_date=window_end.date(),
                )
                upserted_count += len(upserted_ids)
                connection.commit()
                logger.info(
                    "Committed window %s/%s with %s upserts (running total=%s)",
                    index,
                    len(windows),
                    len(upserted_ids),
                    upserted_count,
                )

            metadata = {
                "fetched_count": fetched_count,
                "upserted_count": upserted_count,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "window_count": len(windows),
            }
            _finish_job(connection, job_name, end_date, "succeeded", metadata)
            connection.commit()
            return {"status": "succeeded", "startDate": start_date.isoformat(), "endDate": end_date.isoformat(), **metadata}
        except Exception as exc:
            connection.rollback()
            _finish_job(connection, job_name, end_date, "failed", {"error": str(exc)})
            connection.commit()
            raise
