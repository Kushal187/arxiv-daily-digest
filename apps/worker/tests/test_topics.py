import unittest

from apps.worker.app.services.topics import infer_topics


class TopicInferenceTests(unittest.TestCase):
    def test_retrieval_rag_topic_is_detected(self):
        topics = infer_topics(
            "RAG Agents for Search",
            "We combine retrieval augmented generation with dense retrieval and agent planning.",
            ["cs.AI", "cs.IR"],
        )

        slugs = [topic["slug"] for topic in topics]
        self.assertIn("retrieval-rag", slugs)
        self.assertIn("agent-systems", slugs)

    def test_hidden_flag_is_set_for_low_confidence(self):
        topics = infer_topics(
            "A small benchmark",
            "This benchmark studies general evaluation choices.",
            ["cs.CL"],
        )

        self.assertTrue(any(topic["is_hidden"] for topic in topics))


if __name__ == "__main__":
    unittest.main()
