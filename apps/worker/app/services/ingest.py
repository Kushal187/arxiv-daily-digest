from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import json
from typing import Any

from ..db import advisory_lock_key, get_connection
from .arxiv import fetch_recent_entries
from .clustering import cluster_papers
from .embeddings import embed_text, vector_literal
from .topics import infer_topics


DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.IR", "stat.ML", "cs.RO", "eess.AS"]


def _run_window(run_date: date) -> tuple[datetime, datetime]:
    end = datetime.combine(run_date, time.max, tzinfo=timezone.utc)
    start = end - timedelta(hours=36)
    return start, end


def _job_status(connection, run_date: date) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select id, status, metadata
            from job_runs
            where job_name = 'daily-ingest'
              and run_date = %s
            limit 1
            """,
            (run_date,),
        )
        return cursor.fetchone()


def _start_job(connection, run_date: date) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into job_runs (job_name, run_date, status, metadata)
            values ('daily-ingest', %s, 'started', '{}'::jsonb)
            on conflict (job_name, run_date)
            do update set status = 'started', started_at = now(), completed_at = null, metadata = '{}'::jsonb
            """,
            (run_date,),
        )


def _finish_job(connection, run_date: date, status: str, metadata: dict[str, Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            update job_runs
            set status = %s,
                completed_at = now(),
                metadata = %s::jsonb
            where job_name = 'daily-ingest'
              and run_date = %s
            """,
            (status, json.dumps(metadata), run_date),
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


def run_daily_ingest(run_date: date | None = None, force: bool = False) -> dict[str, Any]:
    run_date = run_date or datetime.now(timezone.utc).date()
    window_start, window_end = _run_window(run_date)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select pg_try_advisory_lock(%s) as locked", (advisory_lock_key("daily-ingest"),))
            lock_result = cursor.fetchone()

        if not lock_result["locked"]:
            return {"status": "locked", "runDate": run_date.isoformat()}

        try:
            existing = _job_status(connection, run_date)
            if existing and existing["status"] == "succeeded" and not force:
                return {"status": "skipped", "runDate": run_date.isoformat(), "reason": "already ingested"}

            _start_job(connection, run_date)

            papers = [
                paper
                for paper in fetch_recent_entries(DEFAULT_CATEGORIES)
                if window_start <= paper["published_at"] <= window_end
            ]

            enriched = []
            for paper in papers:
                embedding = embed_text(f"{paper['title']}\n\n{paper['abstract']}")
                topics = infer_topics(paper["title"], paper["abstract"], paper["categories"])
                paper["embedding"] = embedding
                paper["topics"] = topics
                paper["classifier_metadata"] = {
                    "topic_count": len(topics),
                    "max_confidence": max([topic["confidence"] for topic in topics], default=0),
                }
                enriched.append(paper)

            clusters = cluster_papers(enriched, run_date)

            upserted_ids: list[str] = []
            for paper in enriched:
                cluster = clusters.get(
                    paper["source_id"],
                    {"cluster_date": run_date, "cluster_id": "misc", "cluster_label": "misc"},
                )
                paper_id = _upsert_paper(connection, paper, cluster, ingest_date=run_date)
                upserted_ids.append(paper_id)

            connection.commit()
            metadata = {
                "fetched_count": len(papers),
                "upserted_count": len(upserted_ids),
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
            }
            _finish_job(connection, run_date, "succeeded", metadata)
            connection.commit()
            return {"status": "succeeded", "runDate": run_date.isoformat(), **metadata}
        except Exception as exc:
            connection.rollback()
            _finish_job(connection, run_date, "failed", {"error": str(exc)})
            connection.commit()
            raise
        finally:
            with connection.cursor() as cursor:
                cursor.execute("select pg_advisory_unlock(%s)", (advisory_lock_key("daily-ingest"),))
