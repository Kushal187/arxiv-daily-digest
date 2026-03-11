from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import re
import unicodedata
from typing import Any

from .embeddings import embed_text, vector_literal
from .summaries import get_or_create_summary
from .topics import (
    AREA_LABELS,
    TOPIC_DEFINITIONS,
    area_for_topic_slug,
    label_for_area_slug,
    label_for_topic_slug,
)


DIGEST_WEIGHTS = {
    "semantic": 0.28,
    "topic": 0.20,
    "category": 0.10,
    "author": 0.14,
    "recency": 0.14,
    "saved_similarity": 0.09,
    "open_similarity": 0.08,
    "dismiss_penalty": -0.30,
}
DISCOVER_WEIGHTS = {
    "semantic": 0.34,
    "topic": 0.19,
    "category": 0.08,
    "author": 0.1,
    "recency": 0.06,
    "saved_similarity": 0.14,
    "open_similarity": 0.11,
    "dismiss_penalty": -0.30,
}
MIN_CATEGORY_FEED_SIZE = 30
DIVERSITY_RERANK_LIMIT = 50
DIVERSITY_REPEAT_PENALTY = 0.07
DISCOVER_HEAD_COUNT = 12
DISCOVER_MAX_PER_BUCKET = 2
DISCOVER_RESULT_COUNT = 24
DISCOVER_WINDOW_DAYS = 183
DIGEST_WINDOW_DAYS = 30
INTERACTION_LOOKBACK_DAYS = 90
INTERACTION_MAX_ITEMS = 150

RESEARCH_AREA_SET = set(AREA_LABELS.keys())


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


def weighted_average_vectors(weighted_vectors: list[tuple[list[float], float]]) -> list[float]:
    import numpy as np

    if not weighted_vectors:
        return [0.0] * 384

    vectors = np.asarray([v for v, _ in weighted_vectors], dtype=np.float64)
    weights = np.asarray([w for _, w in weighted_vectors], dtype=np.float64)
    total_weight = weights.sum()
    if total_weight == 0:
        return [0.0] * vectors.shape[1]

    result = (weights[:, None] * vectors).sum(axis=0) / total_weight
    return result.tolist()


@lru_cache(maxsize=None)
def topic_prototype(slug: str) -> list[float]:
    for definition in TOPIC_DEFINITIONS:
        if definition["slug"] == slug:
            return embed_text(definition["prototype"])

    return embed_text(slug.replace("-", " "))


def build_user_profile_vector(
    selected_areas: list[str],
    saved_embeddings: list[list[float]],
    opened_embeddings: list[list[float]] | None = None,
) -> list[float]:
    weighted_vectors: list[tuple[list[float], float]] = []
    weighted_vectors.extend((topic_prototype(area), 1.0) for area in selected_areas)
    weighted_vectors.extend((embedding, 1.15) for embedding in saved_embeddings)
    weighted_vectors.extend((embedding, 0.55) for embedding in (opened_embeddings or []))
    return weighted_average_vectors(weighted_vectors)


def recency_score(published_at: datetime, now: datetime, decay_days: int = 3) -> float:
    age_days = max((now - published_at).total_seconds() / 86400.0, 0.0)
    return max(0.0, 1 - min(age_days / float(decay_days), 1.0))


def _normalize_selected_areas(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in RESEARCH_AREA_SET:
            slug = value
        else:
            slug = area_for_topic_slug(value)

        if not slug or slug in seen:
            continue

        seen.add(slug)
        normalized.append(slug)

    return normalized


def _visible_topic_records(paper_topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible = []
    for topic in paper_topics:
        if topic["is_hidden"]:
            continue

        area_slug = topic.get("area_slug") or area_for_topic_slug(topic["slug"])
        visible.append(
            {
                "slug": topic["slug"],
                "area_slug": area_slug,
                "label": label_for_topic_slug(topic["slug"]),
                "area_label": label_for_area_slug(area_slug) if area_slug else topic["slug"],
                "confidence": float(topic["confidence"]),
            }
        )

    return visible


def _topic_affinity(selected_areas: list[str], paper_topics: list[dict[str, Any]]) -> float:
    if not selected_areas:
        return 0.0

    topic_scores: dict[str, float] = {}
    for topic in paper_topics:
        if topic["is_hidden"]:
            continue

        area_slug = topic.get("area_slug") or area_for_topic_slug(topic["slug"])
        if not area_slug:
            continue

        topic_scores[area_slug] = max(topic_scores.get(area_slug, 0.0), float(topic["confidence"]))

    overlapping = [topic_scores[slug] for slug in selected_areas if slug in topic_scores]
    return max(overlapping, default=0.0)


def generate_reasons(
    feature_scores: dict[str, float],
    paper: dict[str, Any],
    selected_areas: list[str],
    *,
    mode: str,
) -> list[dict]:
    reasons: list[dict] = []
    topic_label = paper["visible_topics"][0]["label"] if paper["visible_topics"] else None
    area_label = paper["visible_topics"][0]["area_label"] if paper["visible_topics"] else None

    if feature_scores["topic"] > 0 and topic_label:
        reasons.append(
            {
                "type": "topic",
                "label": f"matches {topic_label}" if mode == "discover" else f"matches {area_label or topic_label}",
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
                "label": "fresh in the last 14 days" if mode == "discover" else "fresh in the last 14 days",
                "score": round(feature_scores["recency"], 3),
            }
        )

    if not reasons and selected_areas and paper["cluster_label"] != "misc":
        reasons.append({"type": "cluster", "label": f"grouped under {paper['cluster_label']}", "score": 0.05})

    return reasons[:3]


def _score_paper(
    paper: dict[str, Any],
    *,
    selected_areas: list[str],
    followed_authors: list[str],
    preferred_categories: list[str],
    now: datetime,
    mode: str,
    weights: dict[str, float],
    recency_decay_days: int,
) -> dict[str, Any]:
    visible_topics = _visible_topic_records(paper["topics"])
    author_matches = match_followed_authors(followed_authors, paper["authors"])
    category_overlap = set(preferred_categories).intersection(paper["categories"]) if preferred_categories else set()

    paper["visible_topics"] = visible_topics
    paper["author_matches"] = author_matches

    category_score = 0.0
    if preferred_categories and category_overlap:
        category_score = min(len(category_overlap) / len(preferred_categories), 1.0)

    feature_scores = {
        "semantic": float(paper.get("semantic_score", 0.0)),
        "topic": _topic_affinity(selected_areas, paper["topics"]),
        "category": category_score,
        "author": author_matches[0]["score"] if author_matches else 0.0,
        "recency": recency_score(paper["published_at"], now, decay_days=recency_decay_days),
        "saved_similarity": float(paper.get("saved_similarity", 0.0)),
        "open_similarity": float(paper.get("open_similarity", 0.0)),
        "dismiss_penalty": float(paper.get("dismiss_penalty", 0.0)),
    }

    base_score = sum(feature_scores[name] * weight for name, weight in weights.items())
    paper["base_score"] = round(base_score, 4)
    paper["score"] = round(base_score, 4)
    paper["reasons"] = generate_reasons(feature_scores, paper, selected_areas, mode=mode)
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


def _discover_bucket_id(paper: dict[str, Any]) -> str:
    visible_topics = paper.get("visible_topics") or []
    if visible_topics:
        return visible_topics[0]["slug"]

    return paper.get("cluster_id", "misc")


def _rerank_discover(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(papers, key=lambda item: item["base_score"], reverse=True)
    if not ordered:
        return []

    head = ordered[: min(len(ordered), 400)]
    tail = ordered[len(head):]
    selected: list[dict[str, Any]] = []
    bucket_counts: dict[str, int] = defaultdict(int)

    while head and len(selected) < DISCOVER_HEAD_COUNT:
        best_index = 0
        best_score = -10.0
        for index, candidate in enumerate(head):
            bucket = _discover_bucket_id(candidate)
            if bucket_counts[bucket] >= DISCOVER_MAX_PER_BUCKET:
                continue

            penalty = bucket_counts[bucket] * 0.08
            rerank_score = candidate["base_score"] - penalty
            if rerank_score > best_score:
                best_index = index
                best_score = rerank_score

        chosen = head.pop(best_index)
        chosen["score"] = round(best_score if best_score > -10 else chosen["base_score"], 4)
        bucket_counts[_discover_bucket_id(chosen)] += 1
        selected.append(chosen)

    remaining = sorted(head + tail, key=lambda item: item["base_score"], reverse=True)
    for paper in remaining:
        paper["score"] = round(paper["base_score"], 4)

    combined = selected + remaining
    return combined[:DISCOVER_RESULT_COUNT]


def _rank_papers(
    papers: list[dict[str, Any]],
    *,
    preferences: dict[str, Any],
    mode: str = "digest",
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    selected_areas = _normalize_selected_areas(preferences.get("areas") or preferences.get("topics") or [])
    weights = DISCOVER_WEIGHTS if mode == "discover" else DIGEST_WEIGHTS
    recency_decay_days = 90 if mode == "discover" else 14
    scored = [
        _score_paper(
            paper,
            selected_areas=selected_areas,
            followed_authors=preferences["authors"],
            preferred_categories=preferences["categories"],
            now=now,
            mode=mode,
            weights=weights,
            recency_decay_days=recency_decay_days,
        )
        for paper in papers
    ]
    active = [paper for paper in scored if not paper["isDismissed"]]
    dismissed = sorted(
        [paper for paper in scored if paper["isDismissed"]],
        key=lambda item: item["base_score"],
        reverse=True,
    )

    reranked = _rerank_discover(active) if mode == "discover" else _rerank_with_diversity(active)
    return reranked + dismissed


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

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


def _interaction_centroids(connection, user_id: str) -> dict[str, str | None]:
    """Compute centroid embeddings for save/open/dismiss interactions in a single query.

    Returns a dict mapping interaction type to a vector literal string (or None
    if the user has no interactions of that type).
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select
              avg(p.embedding) filter (where ui.interaction_type = 'save')    as save_centroid,
              avg(p.embedding) filter (where ui.interaction_type = 'open')    as open_centroid,
              avg(p.embedding) filter (where ui.interaction_type = 'dismiss') as dismiss_centroid
            from user_interactions ui
            join papers p on p.id = ui.paper_id
            where ui.user_id = %s
              and ui.created_at >= now() - interval '90 days'
              and p.embedding is not null
            """,
            (user_id,),
        )
        row = cursor.fetchone()

    def _to_literal(raw) -> str | None:
        if raw is None:
            return None
        return vector_literal(parse_vector(raw))

    return {
        "save": _to_literal(row["save_centroid"]) if row else None,
        "open": _to_literal(row["open_centroid"]) if row else None,
        "dismiss": _to_literal(row["dismiss_centroid"]) if row else None,
    }


def _paper_rows_for_window_with_scores(
    connection,
    *,
    start_at: datetime,
    end_at: datetime,
    user_id: str,
    profile_vector_literal: str,
    centroids: dict[str, str | None],
    limit: int,
) -> list[dict[str, Any]]:
    has_save = centroids["save"] is not None
    has_open = centroids["open"] is not None
    has_dismiss = centroids["dismiss"] is not None

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
              coalesce(pc.cluster_id, 'misc') as cluster_id,
              coalesce(pc.cluster_label, 'misc') as cluster_label,
              case when p.embedding is not null
                   then 1.0 - (p.embedding <=> %(profile)s::vector)
                   else 0.0
              end as semantic_score,
              case when p.embedding is not null and %(has_save)s
                   then greatest(1.0 - (p.embedding <=> %(save_centroid)s::vector), 0)
                   else 0.0
              end as saved_similarity,
              case when p.embedding is not null and %(has_open)s
                   then greatest(1.0 - (p.embedding <=> %(open_centroid)s::vector), 0)
                   else 0.0
              end as open_similarity,
              case when p.embedding is not null and %(has_dismiss)s
                   then greatest(1.0 - (p.embedding <=> %(dismiss_centroid)s::vector), 0)
                   else 0.0
              end as dismiss_penalty,
              exists(
                select 1 from user_interactions
                where user_id = %(uid)s and paper_id = p.id and interaction_type = 'save'
              ) as is_saved,
              exists(
                select 1 from user_interactions
                where user_id = %(uid)s and paper_id = p.id and interaction_type = 'dismiss'
              ) as is_dismissed
            from papers p
            left join paper_clusters pc on pc.paper_id = p.id
            where p.published_at >= %(start_at)s
              and p.published_at <= %(end_at)s
            order by p.published_at desc
            limit %(limit)s
            """,
            {
                "profile": profile_vector_literal,
                "uid": user_id,
                "start_at": start_at,
                "end_at": end_at,
                "limit": limit,
                "has_save": has_save,
                "save_centroid": centroids["save"] or profile_vector_literal,
                "has_open": has_open,
                "open_centroid": centroids["open"] or profile_vector_literal,
                "has_dismiss": has_dismiss,
                "dismiss_centroid": centroids["dismiss"] or profile_vector_literal,
            },
        )
        return cursor.fetchall()


def _single_paper_with_scores(
    connection,
    paper_id: str,
    user_id: str,
    profile_vector_literal: str,
    centroids: dict[str, str | None],
) -> dict[str, Any] | None:
    """Fetch a single paper with similarity scores computed in Postgres."""
    has_save = centroids["save"] is not None
    has_open = centroids["open"] is not None
    has_dismiss = centroids["dismiss"] is not None

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
              coalesce(pc.cluster_id, 'misc') as cluster_id,
              coalesce(pc.cluster_label, 'misc') as cluster_label,
              case when p.embedding is not null
                   then 1.0 - (p.embedding <=> %(profile)s::vector)
                   else 0.0
              end as semantic_score,
              case when p.embedding is not null and %(has_save)s
                   then greatest(1.0 - (p.embedding <=> %(save_centroid)s::vector), 0)
                   else 0.0
              end as saved_similarity,
              case when p.embedding is not null and %(has_open)s
                   then greatest(1.0 - (p.embedding <=> %(open_centroid)s::vector), 0)
                   else 0.0
              end as open_similarity,
              case when p.embedding is not null and %(has_dismiss)s
                   then greatest(1.0 - (p.embedding <=> %(dismiss_centroid)s::vector), 0)
                   else 0.0
              end as dismiss_penalty,
              exists(
                select 1 from user_interactions
                where user_id = %(uid)s and paper_id = p.id and interaction_type = 'save'
              ) as is_saved,
              exists(
                select 1 from user_interactions
                where user_id = %(uid)s and paper_id = p.id and interaction_type = 'dismiss'
              ) as is_dismissed
            from papers p
            left join paper_clusters pc on pc.paper_id = p.id
            where p.id = %(paper_id)s
            limit 1
            """,
            {
                "profile": profile_vector_literal,
                "uid": user_id,
                "paper_id": paper_id,
                "has_save": has_save,
                "save_centroid": centroids["save"] or profile_vector_literal,
                "has_open": has_open,
                "open_centroid": centroids["open"] or profile_vector_literal,
                "has_dismiss": has_dismiss,
                "dismiss_centroid": centroids["dismiss"] or profile_vector_literal,
            },
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
                "area_slug": area_for_topic_slug(row["topic_slug"]),
                "confidence": float(row["confidence"]),
                "is_hidden": bool(row["is_hidden"]),
            }
        )

    return topics


def _user_preferences(connection, user_id: str) -> dict[str, Any]:
    with connection.cursor() as cursor:
        cursor.execute(
            "select preferred_categories, profile_embedding from users where id = %s limit 1",
            (user_id,),
        )
        user_row = cursor.fetchone() or {"preferred_categories": [], "profile_embedding": None}

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

    areas = _normalize_selected_areas([row["topic_slug"] for row in topic_rows])
    return {
        "categories": user_row["preferred_categories"] or [],
        "areas": areas,
        "topics": areas,
        "authors": [row["author_name"] for row in author_rows],
        "profile_embedding": user_row.get("profile_embedding"),
    }


def _resolve_profile_vector(connection, user_id: str, preferences: dict[str, Any]) -> list[float]:
    """Return the persisted profile vector, or compute + persist it as a fallback."""
    raw = preferences.get("profile_embedding")
    if raw is not None:
        return parse_vector(raw)

    profile = build_user_profile_vector(preferences["areas"], saved_embeddings=[])
    _persist_profile_vector(connection, user_id, profile)
    return profile


def _persist_profile_vector(connection, user_id: str, profile: list[float]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "update users set profile_embedding = %s::vector, updated_at = now() where id = %s",
            (vector_literal(profile), user_id),
        )
    connection.commit()


def refresh_user_profile(connection, user_id: str) -> list[float]:
    """Recompute profile vector from current preferences + interactions and persist it."""
    preferences = _user_preferences(connection, user_id)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            select p.embedding
            from user_interactions ui
            join papers p on p.id = ui.paper_id
            where ui.user_id = %s
              and ui.interaction_type = 'save'
              and ui.created_at >= now() - make_interval(days => %s)
              and p.embedding is not null
            order by ui.created_at desc
            limit %s
            """,
            (user_id, INTERACTION_LOOKBACK_DAYS, INTERACTION_MAX_ITEMS),
        )
        saved_rows = cursor.fetchall()

        cursor.execute(
            """
            select p.embedding
            from user_interactions ui
            join papers p on p.id = ui.paper_id
            where ui.user_id = %s
              and ui.interaction_type = 'open'
              and ui.created_at >= now() - make_interval(days => %s)
              and p.embedding is not null
            order by ui.created_at desc
            limit %s
            """,
            (user_id, INTERACTION_LOOKBACK_DAYS, INTERACTION_MAX_ITEMS),
        )
        opened_rows = cursor.fetchall()

    saved_embeddings = [parse_vector(row["embedding"]) for row in saved_rows]
    opened_embeddings = [parse_vector(row["embedding"]) for row in opened_rows]

    profile = build_user_profile_vector(
        preferences["areas"],
        saved_embeddings,
        opened_embeddings=opened_embeddings,
    )
    _persist_profile_vector(connection, user_id, profile)
    return profile


def _paper_to_payload(
    row: dict[str, Any],
    topics: list[dict[str, Any]],
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
        "cluster_id": row["cluster_id"],
        "clusterId": row["cluster_id"],
        "cluster_label": row["cluster_label"],
        "clusterLabel": row["cluster_label"],
        "topics": topics,
        "isSaved": bool(row.get("is_saved", False)),
        "isDismissed": bool(row.get("is_dismissed", False)),
        "semantic_score": float(row.get("semantic_score", 0.0)),
        "saved_similarity": float(row.get("saved_similarity", 0.0)),
        "open_similarity": float(row.get("open_similarity", 0.0)),
        "dismiss_penalty": float(row.get("dismiss_penalty", 0.0)),
    }


def _serialize_topics(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "slug": topic["slug"],
            "areaSlug": topic.get("area_slug"),
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


def _visible_ranked_papers(ranked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [paper for paper in ranked if not paper["isDismissed"]]


def _window_bounds(end_date: date, *, days: int) -> tuple[datetime, datetime]:
    end_at = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)
    start_at = end_at.replace(hour=0, minute=0, second=0, microsecond=0)
    start_at = start_at - timedelta(days=days - 1)
    return start_at, end_at


def _discover_candidate_rows(
    connection,
    *,
    start_at: datetime,
    end_at: datetime,
    user_id: str,
    profile_vector_literal: str,
    centroids: dict[str, str | None],
    limit: int,
    slice_days: int = 30,
) -> list[dict[str, Any]]:
    """Collect discover candidates across the full window, not only newest papers."""
    slices: list[tuple[datetime, datetime]] = []
    cursor_end = end_at
    while cursor_end >= start_at:
        cursor_start = max(start_at, cursor_end - timedelta(days=slice_days - 1))
        slices.append((cursor_start, cursor_end))
        cursor_end = cursor_start - timedelta(seconds=1)

    if not slices:
        return []

    per_slice_limit = max(80, (limit // len(slices)) + 60)
    seen: set[str] = set()
    combined: list[dict[str, Any]] = []

    for slice_start, slice_end in slices:
        rows = _paper_rows_for_window_with_scores(
            connection,
            start_at=slice_start,
            end_at=slice_end,
            user_id=user_id,
            profile_vector_literal=profile_vector_literal,
            centroids=centroids,
            limit=per_slice_limit,
        )
        for row in rows:
            row_id = row["id"]
            if row_id in seen:
                continue
            seen.add(row_id)
            combined.append(row)
            if len(combined) >= limit:
                return combined

    return combined


def _paper_matches_area(paper: dict[str, Any], area_slug: str) -> bool:
    for topic in paper["topics"]:
        topic_area = topic.get("area_slug") or area_for_topic_slug(topic["slug"])
        if topic_area == area_slug and not topic["is_hidden"]:
            return True

    return False


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

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

    preferences = _user_preferences(connection, user_id)
    profile_vector = _resolve_profile_vector(connection, user_id, preferences)
    profile_lit = vector_literal(profile_vector)
    centroids = _interaction_centroids(connection, user_id)
    window_start, window_end = _window_bounds(resolved_date, days=DIGEST_WINDOW_DAYS)

    paper_rows = _paper_rows_for_window_with_scores(
        connection,
        start_at=window_start,
        end_at=window_end,
        user_id=user_id,
        profile_vector_literal=profile_lit,
        centroids=centroids,
        limit=400,
    )
    paper_ids = [row["id"] for row in paper_rows]
    topics_by_paper = _topics_for_papers(connection, paper_ids)

    papers = [
        _paper_to_payload(row, topics_by_paper.get(row["id"], []))
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
        ranked = _visible_ranked_papers(_rank_papers(papers, preferences=preferences, mode="digest"))
    else:
        ranked_matching = _visible_ranked_papers(_rank_papers(matching, preferences=preferences, mode="digest"))
        if len(ranked_matching) >= MIN_CATEGORY_FEED_SIZE:
            ranked = ranked_matching
        else:
            did_backfill_categories = True
            matching_ids = {paper["id"] for paper in matching}
            backfill_candidates = [paper for paper in papers if paper["id"] not in matching_ids]
            ranked_backfill = _visible_ranked_papers(
                _rank_papers(backfill_candidates, preferences=preferences, mode="digest")
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


def build_discover_response(
    connection,
    user_id: str,
    discover_date: date,
    area: str | None = None,
) -> dict[str, Any]:
    preferences = _user_preferences(connection, user_id)
    profile_vector = _resolve_profile_vector(connection, user_id, preferences)
    profile_lit = vector_literal(profile_vector)
    centroids = _interaction_centroids(connection, user_id)
    window_start, window_end = _window_bounds(discover_date, days=DISCOVER_WINDOW_DAYS)

    paper_rows = _discover_candidate_rows(
        connection,
        start_at=window_start,
        end_at=window_end,
        user_id=user_id,
        profile_vector_literal=profile_lit,
        centroids=centroids,
        limit=1800,
    )
    paper_ids = [row["id"] for row in paper_rows]
    topics_by_paper = _topics_for_papers(connection, paper_ids)
    papers = [_paper_to_payload(row, topics_by_paper.get(row["id"], [])) for row in paper_rows]

    selected_area = area if area in RESEARCH_AREA_SET else None
    if selected_area:
        papers = [paper for paper in papers if _paper_matches_area(paper, selected_area)]

    discover_preferences = {
        **preferences,
        "areas": [selected_area] if selected_area else preferences["areas"],
        "topics": [selected_area] if selected_area else preferences["areas"],
    }
    ranked = _visible_ranked_papers(_rank_papers(papers, preferences=discover_preferences, mode="discover"))

    return {
        "requestedDate": discover_date.isoformat(),
        "resolvedDate": discover_date.isoformat(),
        "windowDays": DISCOVER_WINDOW_DAYS,
        "selectedArea": selected_area,
        "papers": [_serialize_paper(paper) for paper in ranked[:DISCOVER_RESULT_COUNT]],
    }


def build_paper_response(connection, user_id: str, paper_id: str) -> dict[str, Any]:
    preferences = _user_preferences(connection, user_id)
    profile_vector = _resolve_profile_vector(connection, user_id, preferences)
    profile_lit = vector_literal(profile_vector)
    centroids = _interaction_centroids(connection, user_id)

    row = _single_paper_with_scores(connection, paper_id, user_id, profile_lit, centroids)
    if row is None:
        return {"paper": None, "summary": None, "summarySource": None}

    topics_by_paper = _topics_for_papers(connection, [paper_id])
    selected = _paper_to_payload(row, topics_by_paper.get(paper_id, []))

    now = datetime.now(timezone.utc)
    scored = _score_paper(
        selected,
        selected_areas=preferences["areas"],
        followed_authors=preferences["authors"],
        preferred_categories=preferences["categories"],
        now=now,
        mode="digest",
        weights=DIGEST_WEIGHTS,
        recency_decay_days=14,
    )

    summary, summary_source = get_or_create_summary(connection, paper_id, scored["title"], scored["abstract"])
    return {
        "paper": _serialize_paper(scored),
        "summary": summary,
        "summarySource": summary_source,
    }
