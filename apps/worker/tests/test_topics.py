import unittest

from apps.worker.app.services.embeddings import embed_text
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

    def test_embedding_similarity_recovers_topic_without_exact_phrase(self):
        text = "Dense retrieval systems for ranking enterprise search results with reranking pipelines."
        topics = infer_topics(
            "Enterprise search pipelines",
            text,
            ["cs.IR"],
            embedding=embed_text(f"Enterprise search pipelines\n\n{text}"),
        )

        slugs = [topic["slug"] for topic in topics]
        self.assertIn("information-retrieval", slugs)


if __name__ == "__main__":
    unittest.main()
