import unittest
from datetime import datetime, timedelta, timezone

from apps.worker.app.services.ranking import (
    build_user_profile_vector,
    generate_reasons,
    rank_papers_for_user,
    recency_score,
)


def make_paper(
    paper_id: str,
    *,
    cluster_id: str,
    embedding: list[float] | None = None,
    categories: list[str] | None = None,
    authors: list[str] | None = None,
    topics: list[dict] | None = None,
    published_hours_ago: int = 6,
    dismissed: bool = False,
) -> dict:
    published_at = datetime.now(timezone.utc) - timedelta(hours=published_hours_ago)
    vector = embedding if embedding is not None else [0.0] * 384
    return {
        "id": paper_id,
        "sourceId": paper_id,
        "canonicalArxivId": paper_id,
        "arxivVersion": 1,
        "title": f"Paper {paper_id}",
        "abstract": "Abstract",
        "authors": authors or ["Alice Example"],
        "categories": categories or ["cs.IR"],
        "primaryCategory": (categories or ["cs.IR"])[0],
        "primary_category": (categories or ["cs.IR"])[0],
        "publishedAt": published_at.isoformat(),
        "published_at": published_at,
        "updatedAt": published_at.isoformat(),
        "url": f"https://arxiv.org/abs/{paper_id}",
        "embedding": vector,
        "clusterId": cluster_id,
        "cluster_id": cluster_id,
        "clusterLabel": cluster_id,
        "cluster_label": cluster_id,
        "topics": topics
        or [
            {
                "slug": "retrieval-rag",
                "confidence": 0.8,
                "is_hidden": False,
            }
        ],
        "isSaved": False,
        "isDismissed": dismissed,
    }


class RankingTests(unittest.TestCase):
    def test_user_profile_vector_has_expected_dimension(self):
        vector = build_user_profile_vector(
            selected_topics=["retrieval-rag", "agent-systems"],
            followed_authors=["Alice Example"],
            saved_embeddings=[[0.1] * 384],
        )
        self.assertEqual(len(vector), 384)

    def test_reason_generation_prefers_topic_and_saved_similarity(self):
        reasons = generate_reasons(
            {
                "semantic": 0.8,
                "topic": 1.0,
                "category": 0.0,
                "author": 0.0,
                "recency": 0.4,
                "saved_similarity": 0.7,
                "open_similarity": 0.0,
                "dismiss_penalty": 0.0,
            },
            {
                "visible_topics": ["retrieval-rag"],
                "primary_category": "cs.IR",
                "cluster_label": "retrieval / benchmark",
                "author_matches": [],
            },
            ["retrieval-rag"],
        )
        labels = [reason["label"] for reason in reasons]
        self.assertIn("matches retrieval-rag", labels)
        self.assertIn("similar to papers you saved", labels)

    def test_recency_score_decays_with_age(self):
        now = datetime.now(timezone.utc)
        fresh = recency_score(now - timedelta(hours=4), now)
        stale = recency_score(now - timedelta(hours=80), now)
        self.assertGreater(fresh, stale)

    def test_open_interactions_increase_ranking_score(self):
        papers = [
            make_paper("paper-open", cluster_id="cluster-a", embedding=[1.0] + [0.0] * 383),
            make_paper("paper-other", cluster_id="cluster-b", embedding=[0.0] * 384),
        ]

        ranked = rank_papers_for_user(
            papers,
            selected_topics=["retrieval-rag"],
            followed_authors=[],
            preferred_categories=["cs.IR"],
            saved_embeddings=[],
            dismissed_embeddings=[],
            opened_embeddings=[[1.0] + [0.0] * 383],
        )

        self.assertEqual(ranked[0]["id"], "paper-open")

    def test_diversity_rerank_breaks_cluster_ties(self):
        papers = [
            make_paper("a1", cluster_id="cluster-a", embedding=[1.0] + [0.0] * 383),
            make_paper("a2", cluster_id="cluster-a", embedding=[0.98] + [0.0] * 383),
            make_paper("b1", cluster_id="cluster-b", embedding=[0.96] + [0.0] * 383),
        ]

        ranked = rank_papers_for_user(
            papers,
            selected_topics=["retrieval-rag"],
            followed_authors=[],
            preferred_categories=["cs.IR"],
            saved_embeddings=[[1.0] + [0.0] * 383],
            dismissed_embeddings=[],
            opened_embeddings=[],
        )

        self.assertEqual([paper["id"] for paper in ranked[:3]], ["a1", "b1", "a2"])

    def test_dismissed_papers_do_not_consume_diversity_slots(self):
        papers = [
            make_paper("dismissed-a", cluster_id="cluster-a", embedding=[1.0] + [0.0] * 383, dismissed=True),
            make_paper("active-a", cluster_id="cluster-a", embedding=[0.99] + [0.0] * 383),
            make_paper("active-b", cluster_id="cluster-b", embedding=[0.98] + [0.0] * 383),
        ]

        ranked = rank_papers_for_user(
            papers,
            selected_topics=["retrieval-rag"],
            followed_authors=[],
            preferred_categories=["cs.IR"],
            saved_embeddings=[[1.0] + [0.0] * 383],
            dismissed_embeddings=[],
            opened_embeddings=[],
        )

        self.assertEqual([paper["id"] for paper in ranked[:2]], ["active-a", "active-b"])


if __name__ == "__main__":
    unittest.main()
