import unittest
from datetime import datetime, timedelta, timezone

from apps.worker.app.services.ranking import (
    _rank_papers,
    _score_paper,
    build_user_profile_vector,
    generate_reasons,
    recency_score,
)


def make_paper(
    paper_id: str,
    *,
    cluster_id: str,
    categories: list[str] | None = None,
    authors: list[str] | None = None,
    topics: list[dict] | None = None,
    published_hours_ago: int = 6,
    dismissed: bool = False,
    semantic_score: float = 0.0,
    saved_similarity: float = 0.0,
    open_similarity: float = 0.0,
    dismiss_penalty: float = 0.0,
) -> dict:
    published_at = datetime.now(timezone.utc) - timedelta(hours=published_hours_ago)
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
        "clusterId": cluster_id,
        "cluster_id": cluster_id,
        "clusterLabel": cluster_id,
        "cluster_label": cluster_id,
        "topics": topics
        or [
            {
                "slug": "retrieval-rag",
                "area_slug": "nlp",
                "confidence": 0.8,
                "is_hidden": False,
            }
        ],
        "isSaved": False,
        "isDismissed": dismissed,
        "semantic_score": semantic_score,
        "saved_similarity": saved_similarity,
        "open_similarity": open_similarity,
        "dismiss_penalty": dismiss_penalty,
    }


class RankingTests(unittest.TestCase):
    def test_user_profile_vector_has_expected_dimension(self):
        vector = build_user_profile_vector(
            selected_areas=["nlp", "multimodal"],
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
                "visible_topics": [{"slug": "retrieval-rag", "label": "Retrieval / RAG", "area_label": "NLP"}],
                "primary_category": "cs.IR",
                "cluster_label": "retrieval / benchmark",
                "author_matches": [],
            },
            ["nlp"],
            mode="digest",
        )
        labels = [reason["label"] for reason in reasons]
        self.assertIn("matches NLP", labels)
        self.assertIn("similar to papers you saved", labels)

    def test_recency_score_decays_with_age(self):
        now = datetime.now(timezone.utc)
        fresh = recency_score(now - timedelta(hours=4), now)
        stale = recency_score(now - timedelta(hours=80), now)
        self.assertGreater(fresh, stale)

    def test_open_similarity_increases_ranking_score(self):
        papers = [
            make_paper("paper-open", cluster_id="cluster-a", semantic_score=0.5, open_similarity=0.9),
            make_paper("paper-other", cluster_id="cluster-b", semantic_score=0.5, open_similarity=0.0),
        ]

        ranked = _rank_papers(
            papers,
            preferences={"areas": ["nlp"], "authors": [], "categories": ["cs.IR"]},
        )

        active = [p for p in ranked if not p["isDismissed"]]
        self.assertEqual(active[0]["id"], "paper-open")

    def test_score_paper_reads_precomputed_scores(self):
        paper = make_paper(
            "precomputed",
            cluster_id="c1",
            semantic_score=0.85,
            saved_similarity=0.7,
            open_similarity=0.5,
            dismiss_penalty=0.0,
        )
        now = datetime.now(timezone.utc)
        scored = _score_paper(
            paper,
            selected_areas=["nlp"],
            followed_authors=[],
            preferred_categories=["cs.IR"],
            now=now,
            mode="digest",
            weights={
                "semantic": 0.28,
                "topic": 0.2,
                "category": 0.1,
                "author": 0.14,
                "recency": 0.14,
                "saved_similarity": 0.09,
                "open_similarity": 0.08,
                "dismiss_penalty": -0.3,
            },
            recency_decay_days=14,
        )
        self.assertGreater(scored["base_score"], 0.0)
        self.assertIn("reasons", scored)

    def test_diversity_rerank_breaks_cluster_ties(self):
        papers = [
            make_paper("a1", cluster_id="cluster-a", semantic_score=0.9, saved_similarity=0.9),
            make_paper("a2", cluster_id="cluster-a", semantic_score=0.88, saved_similarity=0.88),
            make_paper("b1", cluster_id="cluster-b", semantic_score=0.86, saved_similarity=0.86),
        ]

        ranked = _rank_papers(
            papers,
            preferences={"areas": ["nlp"], "authors": [], "categories": ["cs.IR"]},
        )

        self.assertEqual([paper["id"] for paper in ranked[:3]], ["a1", "b1", "a2"])

    def test_dismissed_papers_do_not_consume_diversity_slots(self):
        papers = [
            make_paper("dismissed-a", cluster_id="cluster-a", semantic_score=0.9, saved_similarity=0.9, dismissed=True),
            make_paper("active-a", cluster_id="cluster-a", semantic_score=0.89, saved_similarity=0.89),
            make_paper("active-b", cluster_id="cluster-b", semantic_score=0.88, saved_similarity=0.88),
        ]

        ranked = _rank_papers(
            papers,
            preferences={"areas": ["nlp"], "authors": [], "categories": ["cs.IR"]},
        )

        active = [p for p in ranked if not p["isDismissed"]]
        self.assertEqual([paper["id"] for paper in active[:2]], ["active-a", "active-b"])

    def test_discover_diversity_caps_repeated_topic_buckets(self):
        papers = [
            make_paper("rag-1", cluster_id="cluster-a", semantic_score=0.95, saved_similarity=0.8),
            make_paper("rag-2", cluster_id="cluster-b", semantic_score=0.94, saved_similarity=0.79),
            make_paper("rag-3", cluster_id="cluster-c", semantic_score=0.93, saved_similarity=0.78),
            make_paper(
                "interp-1",
                cluster_id="cluster-d",
                semantic_score=0.9,
                saved_similarity=0.77,
                topics=[{"slug": "mechanistic-interpretability", "area_slug": "interpretability", "confidence": 0.81, "is_hidden": False}],
            ),
        ]

        ranked = _rank_papers(
            papers,
            preferences={"areas": ["nlp", "interpretability"], "authors": [], "categories": ["cs.IR"]},
            mode="discover",
        )

        active_ids = [paper["id"] for paper in ranked if not paper["isDismissed"]]
        self.assertEqual(active_ids[:3], ["rag-1", "interp-1", "rag-2"])


if __name__ == "__main__":
    unittest.main()
