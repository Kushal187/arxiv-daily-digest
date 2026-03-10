import unittest
from datetime import datetime, timedelta, timezone

from apps.worker.app.services.ranking import (
    build_user_profile_vector,
    generate_reasons,
    recency_score,
)


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
                "dismiss_penalty": 0.0,
                "diversity_penalty": 0.0,
            },
            {
                "visible_topics": ["retrieval-rag"],
                "primary_category": "cs.IR",
                "cluster_label": "retrieval / benchmark",
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


if __name__ == "__main__":
    unittest.main()
