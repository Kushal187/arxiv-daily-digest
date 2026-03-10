from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
import math
import re
import unicodedata
from typing import Any

from .embeddings import embed_text
from .summaries import get_or_create_summary


WEIGHTS = {
    "semantic": 0.42,
    "topic": 0.16,
    "category": 0.08,
    "author": 0.12,
    "recency": 0.08,
    "saved_similarity": 0.18,
    "dismiss_penalty": -0.2,
    "diversity_penalty": -0.06,
}


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
    if not followed_parts or not paper_parts:
        return 0.0

    followed_last = followed_parts[-1]
    paper_last = paper_parts[-1]
    followed_first_initial = followed_parts[0][0]
    paper_first_initial = paper_parts[0][0]

    if followed_last == paper_last and followed_first_initial == paper_first_initial:
        return 0.9

    if (
        followed_first_initial == paper_first_initial
        and len(followed_last) >= 5
        and len(paper_last) >= 5
        and levenshtein_distance(followed_last, paper_last) <= 1
    ):
        return 0.78

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
        if best_match and best_match["score"] > 0:
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


def average_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return [0.0] * 384

    length = len(vectors[0])
    totals = [0.0] * length
    for vector in vectors:
        for index, value in enumerate(vector):
            totals[index] += value

    return [value / len(vectors) for value in totals]


def topic_prototype(slug: str) -> list[float]:
    return embed_text(slug.replace("-", " "))


def build_user_profile_vector(
    selected_topics: list[str], followed_authors: list[str], saved_embeddings: list[list[float]]
) -> list[float]:
    vectors = [topic_prototype(topic) for topic in selected_topics]
    vectors.extend(embed_text(author) for author in followed_authors)
    vectors.extend(saved_embeddings)
    return average_vectors(vectors)


def recency_score(published_at: datetime, now: datetime) -> float:
    age_hours = max((now - published_at).total_seconds() / 3600.0, 0.0)
    return max(0.0, 1 - min(age_hours / 72.0, 1.0))


def similarity_to_saved(paper_vector: list[float], saved_embeddings: list[list[float]]) -> float:
    if not saved_embeddings:
        return 0.0

    return max(cosine_similarity(paper_vector, embedding) for embedding in saved_embeddings)


def penalty_from_dismissed(paper_vector: list[float], dismissed_embeddings: list[list[float]]) -> float:
    if not dismissed_embeddings:
        return 0.0

    return max(cosine_similarity(paper_vector, embedding) for embedding in dismissed_embeddings)


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

    if feature_scores["saved_similarity"] > 0.1:
        reasons.append(
            {
                "type": "saved_similarity",
                "label": "similar to papers you saved",
                "score": round(feature_scores["saved_similarity"], 3),
            }
        )

    if feature_scores["author"] > 0:
        author_label = "author you follow"
        if paper["author_matches"]:
            author_label = f"author you follow: {paper['author_matches'][0]['followed']}"
        reasons.append(
            {
                "type": "author",
                "label": author_label,
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

    if feature_scores["recency"] > 0.05 and len(reasons) < 3:
        reasons.append(
            {
                "type": "freshness",
                "label": "fresh in the last 72 hours",
                "score": round(feature_scores["recency"], 3),
            }
        )

    if not reasons and selected_topics:
        reasons.append({"type": "cluster", "label": f"grouped under {paper['cluster_label']}", "score": 0.05})

    return reasons[:3]


def rank_papers_for_user(
    papers: list[dict[str, Any]],
    selected_topics: list[str],
    followed_authors: list[str],
    preferred_categories: list[str],
    saved_embeddings: list[list[float]],
    dismissed_embeddings: list[list[float]],
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    profile_vector = build_user_profile_vector(selected_topics, followed_authors, saved_embeddings)
    surfaced_clusters: dict[str, int] = defaultdict(int)
    ranked: list[dict[str, Any]] = []

    for paper in papers:
        paper_vector = paper["embedding"]
        visible_topics = [topic["slug"] for topic in paper["topics"] if not topic["is_hidden"]]
        paper["visible_topics"] = visible_topics
        author_matches = match_followed_authors(followed_authors, paper["authors"])
        paper["author_matches"] = author_matches

        feature_scores = {
            "semantic": cosine_similarity(profile_vector, paper_vector),
            "topic": 1.0 if set(selected_topics).intersection(visible_topics) else 0.0,
            "category": 1.0 if paper["primary_category"] in preferred_categories else 0.0,
            "author": author_matches[0]["score"] if author_matches else 0.0,
            "recency": recency_score(paper["published_at"], now),
            "saved_similarity": similarity_to_saved(paper_vector, saved_embeddings),
            "dismiss_penalty": penalty_from_dismissed(paper_vector, dismissed_embeddings),
            "diversity_penalty": float(surfaced_clusters[paper["cluster_id"]] > 0),
        }

        score = sum(feature_scores[name] * weight for name, weight in WEIGHTS.items())
        paper["score"] = round(score, 4)
        paper["reasons"] = generate_reasons(feature_scores, paper, selected_topics)
        ranked.append(paper)
        surfaced_clusters[paper["cluster_id"]] += 1

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def parse_vector(raw_value: Any) -> list[float]:
    if raw_value is None:
        return [0.0] * 384

    if isinstance(raw_value, list):
        return [float(value) for value in raw_value]

    text = str(raw_value).strip("[]")
    if not text:
        return [0.0] * 384

    return [float(part) for part in text.split(",")]


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

    return ({row["paper_id"] for row in rows}, [parse_vector(row["embedding"]) for row in rows if row["embedding"] is not None])


def _paper_to_payload(row: dict[str, Any], topics: list[dict[str, Any]], saved_ids: set[str], dismissed_ids: set[str]) -> dict[str, Any]:
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


def build_digest_response(connection, user_id: str, digest_date: date) -> dict[str, Any]:
    paper_rows = _paper_rows_for_date(connection, digest_date)
    paper_ids = [row["id"] for row in paper_rows]
    topics_by_paper = _topics_for_papers(connection, paper_ids)
    preferences = _user_preferences(connection, user_id)
    saved_ids, saved_embeddings = _interaction_embeddings(connection, user_id, "save")
    dismissed_ids, dismissed_embeddings = _interaction_embeddings(connection, user_id, "dismiss")

    papers = []
    for row in paper_rows:
        papers.append(_paper_to_payload(row, topics_by_paper.get(row["id"], []), saved_ids, dismissed_ids))

    ranked = rank_papers_for_user(
        papers,
        selected_topics=preferences["topics"],
        followed_authors=preferences["authors"],
        preferred_categories=preferences["categories"],
        saved_embeddings=saved_embeddings,
        dismissed_embeddings=dismissed_embeddings,
    )

    response_papers = [_serialize_paper(paper) for paper in ranked if not paper["isDismissed"]]

    return {"date": digest_date.isoformat(), "papers": response_papers}


def build_paper_response(connection, user_id: str, paper_id: str) -> dict[str, Any]:
    row = _paper_row_by_id(connection, paper_id)
    if row is None:
        return {"paper": None, "summary": None}

    preferences = _user_preferences(connection, user_id)
    saved_ids, saved_embeddings = _interaction_embeddings(connection, user_id, "save")
    dismissed_ids, dismissed_embeddings = _interaction_embeddings(connection, user_id, "dismiss")
    topics_by_paper = _topics_for_papers(connection, [paper_id])
    selected = _paper_to_payload(row, topics_by_paper.get(paper_id, []), saved_ids, dismissed_ids)

    ranked = rank_papers_for_user(
        [selected],
        selected_topics=preferences["topics"],
        followed_authors=preferences["authors"],
        preferred_categories=preferences["categories"],
        saved_embeddings=saved_embeddings,
        dismissed_embeddings=dismissed_embeddings,
    )[0]

    summary = get_or_create_summary(connection, paper_id, ranked["title"], ranked["abstract"])
    return {"paper": _serialize_paper(ranked), "summary": summary}
