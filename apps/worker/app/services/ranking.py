from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from functools import lru_cache
import math
import re
import unicodedata
from typing import Any

from .embeddings import embed_text
from .summaries import get_or_create_summary


BASE_WEIGHTS = {
    "semantic": 0.34,
    "topic": 0.18,
    "category": 0.08,
    "author": 0.12,
    "recency": 0.08,
    "saved_similarity": 0.14,
    "open_similarity": 0.06,
    "dismiss_penalty": -0.18,
}
MIN_CATEGORY_FEED_SIZE = 30
DIVERSITY_RERANK_LIMIT = 50
DIVERSITY_REPEAT_PENALTY = 0.07


def normalize_author_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9\s-]", " ", normalized.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def author_name_parts(name: str) -> list[str]:
    return [part for part in normalize_author_name(name).split(" ") if part]


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for row, left_char in enumerate(left, start=1):
        diagonal = previous[0]
        previous[0] = row
        for column, right_char in enumerate(right, start=1):
            next_diagonal = previous[column]
            cost = 0 if left_char == right_char else 1
            previous[column] = min(previous[column] + 1, previous[column - 1] + 1, diagonal + cost)
            diagonal = next_diagonal

    return previous[-1]


def score_author_match(followed: str, paper_author: str) -> float:
    followed_normalized = normalize_author_name(followed)
    paper_normalized = normalize_author_name(paper_author)
    if not followed_normalized or not paper_normalized:
        return 0.0
    if followed_normalized == paper_normalized:
        return 1.0

    followed_parts = author_name_parts(followed)
    paper_parts = author_name_parts(paper_author)
    if len(followed_parts) < 2 or len(paper_parts) < 2:
        return 0.0

    followed_first = followed_parts[0]
    paper_first = paper_parts[0]
    followed_last = followed_parts[-1]
    paper_last = paper_parts[-1]

    if followed_last == paper_last:
        if followed_first == paper_first:
            return 0.92

        if min(len(followed_first), len(paper_first)) >= 3 and (
            followed_first.startswith(paper_first) or paper_first.startswith(followed_first)
        ):
            return 0.88

        if min(len(followed_first), len(paper_first)) >= 4 and levenshtein_distance(followed_first, paper_first) == 1:
            return 0.84

    if (
        followed_first == paper_first
        and len(followed_last) >= 5
        and len(paper_last) >= 5
        and levenshtein_distance(followed_last, paper_last) == 1
    ):
        return 0.8

    return 0.0


def match_followed_authors(followed_authors: list[str], paper_authors: list[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for followed in followed_authors:
        best_match: dict[str, Any] | None = None
        for paper_author in paper_authors:
            score = score_author_match(followed, paper_author)
            if best_match is None or score > best_match["score"]:
                best_match = {
                    "followed": followed,
                    "paper_author": paper_author,
                    "score": score,
                }

        if best_match and best_match["score"] >= 0.8:
            matches.append(best_match)

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0

    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return numerator / (left_norm * right_norm)


def weighted_average_vectors(weighted_vectors: list[tuple[list[float], float]]) -> list[float]:
    if not weighted_vectors:
        return [0.0] * 384

    length = len(weighted_vectors[0][0])
    totals = [0.0] * length
    total_weight = 0.0

    for vector, weight in weighted_vectors:
        total_weight += weight
        for index, value in enumerate(vector):
            totals[index] += value * weight

    if total_weight == 0:
        return [0.0] * length

    return [value / total_weight for value in totals]


@lru_cache(maxsize=None)
def topic_prototype(slug: str) -> list[float]:
    return embed_text(slug.replace("-", " "))


def build_user_profile_vector(
    selected_topics: list[str],
    followed_authors: list[str],
    saved_embeddings: list[list[float]],
    opened_embeddings: list[list[float]] | None = None,
) -> list[float]:
    weighted_vectors: list[tuple[list[float], float]] = []
    weighted_vectors.extend((topic_prototype(topic), 1.0) for topic in selected_topics)
    weighted_vectors.extend((embed_text(author), 0.9) for author in followed_authors)
    weighted_vectors.extend((embedding, 1.15) for embedding in saved_embeddings)
    weighted_vectors.extend((embedding, 0.55) for embedding in (opened_embeddings or []))
    return weighted_average_vectors(weighted_vectors)


def recency_score(published_at: datetime, now: datetime) -> float:
    age_hours = max((now - published_at).total_seconds() / 3600.0, 0.0)
    return max(0.0, 1 - min(age_hours / 72.0, 1.0))


def similarity_to_interactions(paper_vector: list[float], embeddings: list[list[float]]) -> float:
    if not embeddings:
        return 0.0

    return max(cosine_similarity(paper_vector, embedding) for embedding in embeddings)


def _topic_affinity(selected_topics: list[str], paper_topics: list[dict[str, Any]]) -> float:
    if not selected_topics:
        return 0.0

    topic_scores = {
        topic["slug"]: float(topic["confidence"])
        for topic in paper_topics
        if not topic["is_hidden"]
    }
    overlapping = [topic_scores[slug] for slug in selected_topics if slug in topic_scores]
    return max(overlapping, default=0.0)


def generate_reasons(feature_scores: dict[str, float], paper: dict[str, Any], selected_topics: list[str]) -> list[dict]:
    reasons: list[dict] = []

    if feature_scores["topic"] > 0 and paper["visible_topics"]:
        reasons.append(
            {
                "type": "topic",
                "label": f"matches {paper['visible_topics'][0]}",
                "score": round(feature_scores["topic"], 3),
            }
        )

    if feature_scores["saved_similarity"] > 0.15:
        reasons.append(
            {
                "type": "saved_similarity",
                "label": "similar to papers you saved",
                "score": round(feature_scores["saved_similarity"], 3),
            }
        )

    if feature_scores["author"] > 0 and paper["author_matches"]:
        reasons.append(
            {
                "type": "author",
                "label": f"author you follow: {paper['author_matches'][0]['followed']}",
                "score": round(feature_scores["author"], 3),
            }
        )

    if feature_scores["category"] > 0:
        reasons.append(
            {
                "type": "category",
                "label": f"inside {paper['primary_category']}",
                "score": round(feature_scores["category"], 3),
            }
        )

    if feature_scores["recency"] > 0.1 and len(reasons) < 3:
        reasons.append(
            {
                "type": "freshness",
                "label": "fresh in the last 72 hours",
                "score": round(feature_scores["recency"], 3),
            }
        )

    if not reasons and selected_topics and paper["cluster_label"] != "misc":
        reasons.append({"type": "cluster", "label": f"grouped under {paper['cluster_label']}", "score": 0.05})

    return reasons[:3]


def _score_paper(
    paper: dict[str, Any],
    *,
    selected_topics: list[str],
    followed_authors: list[str],
    preferred_categories: list[str],
    profile_vector: list[float],
    saved_embeddings: list[list[float]],
    opened_embeddings: list[list[float]],
    dismissed_embeddings: list[list[float]],
    now: datetime,
) -> dict[str, Any]:
    paper_vector = paper["embedding"]
    visible_topics = [topic["slug"] for topic in paper["topics"] if not topic["is_hidden"]]
    author_matches = match_followed_authors(followed_authors, paper["authors"])
    category_overlap = set(preferred_categories).intersection(paper["categories"]) if preferred_categories else set()

    paper["visible_topics"] = visible_topics
    paper["author_matches"] = author_matches

    feature_scores = {
        "semantic": cosine_similarity(profile_vector, paper_vector),
        "topic": _topic_affinity(selected_topics, paper["topics"]),
        "category": 1.0 if category_overlap else 0.0,
        "author": author_matches[0]["score"] if author_matches else 0.0,
        "recency": recency_score(paper["published_at"], now),
        "saved_similarity": similarity_to_interactions(paper_vector, saved_embeddings),
        "open_similarity": similarity_to_interactions(paper_vector, opened_embeddings),
        "dismiss_penalty": similarity_to_interactions(paper_vector, dismissed_embeddings),
    }

    base_score = sum(feature_scores[name] * weight for name, weight in BASE_WEIGHTS.items())
    paper["base_score"] = round(base_score, 4)
    paper["score"] = round(base_score, 4)
    paper["reasons"] = generate_reasons(feature_scores, paper, selected_topics)
    return paper


def _rerank_with_diversity(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(papers, key=lambda item: item["base_score"], reverse=True)
    head = ordered[:DIVERSITY_RERANK_LIMIT]
    tail = ordered[DIVERSITY_RERANK_LIMIT:]
    selected: list[dict[str, Any]] = []
    surfaced_clusters: dict[str, int] = defaultdict(int)

    while head:
        best_index = 0
        best_score = -10.0
        for index, candidate in enumerate(head):
            penalty = 0.0
            if candidate["cluster_id"] != "misc":
                penalty = surfaced_clusters[candidate["cluster_id"]] * DIVERSITY_REPEAT_PENALTY

            rerank_score = candidate["base_score"] - penalty
            if rerank_score > best_score:
                best_index = index
                best_score = rerank_score

        paper = head.pop(best_index)
        paper["score"] = round(best_score, 4)
        if paper["cluster_id"] != "misc":
            surfaced_clusters[paper["cluster_id"]] += 1
        selected.append(paper)

    for paper in tail:
        paper["score"] = round(paper["base_score"], 4)

    return selected + tail


def rank_papers_for_user(
    papers: list[dict[str, Any]],
    selected_topics: list[str],
    followed_authors: list[str],
    preferred_categories: list[str],
    saved_embeddings: list[list[float]],
    dismissed_embeddings: list[list[float]],
    opened_embeddings: list[list[float]] | None = None,
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    profile_vector = build_user_profile_vector(
        selected_topics,
        followed_authors,
        saved_embeddings,
        opened_embeddings=opened_embeddings or [],
    )

    scored = [
        _score_paper(
            paper,
            selected_topics=selected_topics,
            followed_authors=followed_authors,
            preferred_categories=preferred_categories,
            profile_vector=profile_vector,
            saved_embeddings=saved_embeddings,
            opened_embeddings=opened_embeddings or [],
            dismissed_embeddings=dismissed_embeddings,
            now=now,
        )
        for paper in papers
    ]
    active = [paper for paper in scored if not paper["isDismissed"]]
    dismissed = sorted(
        [paper for paper in scored if paper["isDismissed"]],
        key=lambda item: item["base_score"],
        reverse=True,
    )

    return _rerank_with_diversity(active) + dismissed


def parse_vector(raw_value: Any) -> list[float]:
    if raw_value is None:
        return [0.0] * 384

    if isinstance(raw_value, list):
        return [float(value) for value in raw_value]

    text = str(raw_value).strip("[]")
    if not text:
        return [0.0] * 384

    return [float(part) for part in text.split(",")]


def _latest_available_digest_date(connection, requested_date: date) -> date | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select ingest_date
            from papers
            where ingest_date <= %s
            group by ingest_date
            order by ingest_date desc
            limit 1
            """,
            (requested_date,),
        )
        row = cursor.fetchone()

    return row["ingest_date"] if row else None


def _paper_rows_for_date(connection, digest_date: date) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
              p.id,
              p.source_id,
              p.canonical_arxiv_id,
              p.arxiv_version,
              p.title,
              p.abstract,
              p.authors,
              p.categories,
              p.primary_category,
              p.published_at,
              p.updated_at,
              p.url,
              p.embedding,
              coalesce(pc.cluster_id, 'misc') as cluster_id,
              coalesce(pc.cluster_label, 'misc') as cluster_label
            from papers p
            left join paper_clusters pc on pc.paper_id = p.id
            where p.ingest_date = %s
            order by p.published_at desc
            limit 250
            """,
            (digest_date,),
        )
        return cursor.fetchall()


def _paper_row_by_id(connection, paper_id: str) -> dict[str, Any] | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
              p.id,
              p.source_id,
              p.canonical_arxiv_id,
              p.arxiv_version,
              p.title,
              p.abstract,
              p.authors,
              p.categories,
              p.primary_category,
              p.published_at,
              p.updated_at,
              p.url,
              p.embedding,
              coalesce(pc.cluster_id, 'misc') as cluster_id,
              coalesce(pc.cluster_label, 'misc') as cluster_label
            from papers p
            left join paper_clusters pc on pc.paper_id = p.id
            where p.id = %s
            limit 1
            """,
            (paper_id,),
        )
        return cursor.fetchone()


def _topics_for_papers(connection, paper_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not paper_ids:
        return {}

    with connection.cursor() as cursor:
        cursor.execute(
            """
            select paper_id, topic_slug, confidence, is_hidden
            from paper_topics
            where paper_id = any(%s)
            order by confidence desc
            """,
            (paper_ids,),
        )
        rows = cursor.fetchall()

    topics: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        topics[row["paper_id"]].append(
            {
                "slug": row["topic_slug"],
                "confidence": float(row["confidence"]),
                "is_hidden": bool(row["is_hidden"]),
            }
        )

    return topics


def _user_preferences(connection, user_id: str) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            "select preferred_categories from users where id = %s limit 1",
            (user_id,),
        )
        user_row = cursor.fetchone() or {"preferred_categories": []}

        cursor.execute(
            "select topic_slug from user_topic_preferences where user_id = %s order by topic_slug asc",
            (user_id,),
        )
        topic_rows = cursor.fetchall()

        cursor.execute(
            "select author_name from user_followed_authors where user_id = %s order by author_name asc",
            (user_id,),
        )
        author_rows = cursor.fetchall()

    return {
        "categories": user_row["preferred_categories"] or [],
        "topics": [row["topic_slug"] for row in topic_rows],
        "authors": [row["author_name"] for row in author_rows],
    }


def _interaction_embeddings(connection, user_id: str, interaction_type: str) -> tuple[set[str], list[list[float]]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select ui.paper_id, p.embedding
            from user_interactions ui
            join papers p on p.id = ui.paper_id
            where ui.user_id = %s
              and ui.interaction_type = %s
            """,
            (user_id, interaction_type),
        )
        rows = cursor.fetchall()

    return (
        {row["paper_id"] for row in rows},
        [parse_vector(row["embedding"]) for row in rows if row["embedding"] is not None],
    )


def _paper_to_payload(
    row: dict[str, Any],
    topics: list[dict[str, Any]],
    saved_ids: set[str],
    dismissed_ids: set[str],
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "canonicalArxivId": row["canonical_arxiv_id"],
        "arxivVersion": row["arxiv_version"],
        "title": row["title"],
        "abstract": row["abstract"],
        "authors": row["authors"],
        "categories": row["categories"],
        "primary_category": row["primary_category"],
        "primaryCategory": row["primary_category"],
        "published_at": row["published_at"],
        "publishedAt": row["published_at"].isoformat(),
        "updatedAt": row["updated_at"].isoformat(),
        "url": row["url"],
        "embedding": parse_vector(row["embedding"]),
        "cluster_id": row["cluster_id"],
        "clusterId": row["cluster_id"],
        "cluster_label": row["cluster_label"],
        "clusterLabel": row["cluster_label"],
        "topics": topics,
        "isSaved": row["id"] in saved_ids,
        "isDismissed": row["id"] in dismissed_ids,
    }


def _serialize_topics(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "slug": topic["slug"],
            "confidence": topic["confidence"],
            "isHidden": topic["is_hidden"],
        }
        for topic in topics
    ]


def _serialize_paper(paper: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": paper["id"],
        "sourceId": paper["sourceId"],
        "canonicalArxivId": paper["canonicalArxivId"],
        "arxivVersion": paper["arxivVersion"],
        "title": paper["title"],
        "abstract": paper["abstract"],
        "authors": paper["authors"],
        "categories": paper["categories"],
        "primaryCategory": paper["primaryCategory"],
        "publishedAt": paper["publishedAt"],
        "updatedAt": paper["updatedAt"],
        "url": paper["url"],
        "clusterLabel": paper["clusterLabel"],
        "topics": _serialize_topics(paper["topics"]),
        "reasons": paper["reasons"],
        "score": paper["score"],
        "isSaved": paper["isSaved"],
        "isDismissed": paper["isDismissed"],
    }


def _rank_digest_pool(
    papers: list[dict[str, Any]],
    *,
    preferences: dict[str, Any],
    saved_embeddings: list[list[float]],
    opened_embeddings: list[list[float]],
    dismissed_embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    return rank_papers_for_user(
        papers,
        selected_topics=preferences["topics"],
        followed_authors=preferences["authors"],
        preferred_categories=preferences["categories"],
        saved_embeddings=saved_embeddings,
        dismissed_embeddings=dismissed_embeddings,
        opened_embeddings=opened_embeddings,
    )


def _visible_ranked_papers(ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [paper for paper in ranked if not paper["isDismissed"]]


def build_digest_response(connection, user_id: str, digest_date: date) -> dict[str, Any]:
    resolved_date = _latest_available_digest_date(connection, digest_date)
    if resolved_date is None:
        return {
            "requestedDate": digest_date.isoformat(),
            "resolvedDate": digest_date.isoformat(),
            "isFallback": False,
            "didBackfillCategories": False,
            "papers": [],
        }

    paper_rows = _paper_rows_for_date(connection, resolved_date)
    paper_ids = [row["id"] for row in paper_rows]
    topics_by_paper = _topics_for_papers(connection, paper_ids)
    preferences = _user_preferences(connection, user_id)
    saved_ids, saved_embeddings = _interaction_embeddings(connection, user_id, "save")
    dismissed_ids, dismissed_embeddings = _interaction_embeddings(connection, user_id, "dismiss")
    _opened_ids, opened_embeddings = _interaction_embeddings(connection, user_id, "open")

    papers = [
        _paper_to_payload(row, topics_by_paper.get(row["id"], []), saved_ids, dismissed_ids)
        for row in paper_rows
    ]
    preferred_categories = set(preferences["categories"])
    matching = (
        [paper for paper in papers if preferred_categories.intersection(paper["categories"])]
        if preferred_categories
        else papers
    )

    did_backfill_categories = False
    if not preferred_categories:
        ranked = _visible_ranked_papers(
            _rank_digest_pool(
                papers,
                preferences=preferences,
                saved_embeddings=saved_embeddings,
                opened_embeddings=opened_embeddings,
                dismissed_embeddings=dismissed_embeddings,
            )
        )
    else:
        ranked_matching = _visible_ranked_papers(
            _rank_digest_pool(
                matching,
                preferences=preferences,
                saved_embeddings=saved_embeddings,
                opened_embeddings=opened_embeddings,
                dismissed_embeddings=dismissed_embeddings,
            )
        )
        if len(ranked_matching) >= MIN_CATEGORY_FEED_SIZE:
            ranked = ranked_matching
        else:
            did_backfill_categories = True
            matching_ids = {paper["id"] for paper in matching}
            backfill_candidates = [paper for paper in papers if paper["id"] not in matching_ids]
            ranked_backfill = _visible_ranked_papers(
                _rank_digest_pool(
                    backfill_candidates,
                    preferences=preferences,
                    saved_embeddings=saved_embeddings,
                    opened_embeddings=opened_embeddings,
                    dismissed_embeddings=dismissed_embeddings,
                )
            )
            needed = max(MIN_CATEGORY_FEED_SIZE - len(ranked_matching), 0)
            ranked = ranked_matching + ranked_backfill[:needed]

    response_papers = [_serialize_paper(paper) for paper in ranked]
    return {
        "requestedDate": digest_date.isoformat(),
        "resolvedDate": resolved_date.isoformat(),
        "isFallback": resolved_date != digest_date,
        "didBackfillCategories": did_backfill_categories,
        "papers": response_papers,
    }


def build_paper_response(connection, user_id: str, paper_id: str) -> dict[str, Any]:
    row = _paper_row_by_id(connection, paper_id)
    if row is None:
        return {"paper": None, "summary": None, "summarySource": None}

    preferences = _user_preferences(connection, user_id)
    saved_ids, saved_embeddings = _interaction_embeddings(connection, user_id, "save")
    dismissed_ids, dismissed_embeddings = _interaction_embeddings(connection, user_id, "dismiss")
    _opened_ids, opened_embeddings = _interaction_embeddings(connection, user_id, "open")
    topics_by_paper = _topics_for_papers(connection, [paper_id])
    selected = _paper_to_payload(row, topics_by_paper.get(paper_id, []), saved_ids, dismissed_ids)

    ranked = rank_papers_for_user(
        [selected],
        selected_topics=preferences["topics"],
        followed_authors=preferences["authors"],
        preferred_categories=preferences["categories"],
        saved_embeddings=saved_embeddings,
        dismissed_embeddings=dismissed_embeddings,
        opened_embeddings=opened_embeddings,
    )[0]

    summary, summary_source = get_or_create_summary(connection, paper_id, ranked["title"], ranked["abstract"])
    return {
        "paper": _serialize_paper(ranked),
        "summary": summary,
        "summarySource": summary_source,
    }
