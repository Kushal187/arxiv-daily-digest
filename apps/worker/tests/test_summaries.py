import unittest

from apps.worker.app.services.summaries import build_extractive_summary, default_bedrock_base_url


class SummaryTests(unittest.TestCase):
    def test_extractive_summary_keeps_first_two_sentences(self):
        summary = build_extractive_summary(
            "Sentence one explains the method. Sentence two explains the result. Sentence three is extra."
        )
        self.assertEqual(summary, "Sentence one explains the method. Sentence two explains the result.")

    def test_default_bedrock_base_url_uses_openai_compat_path(self):
        self.assertEqual(
            default_bedrock_base_url("us-east-1"),
            "https://bedrock-mantle.us-east-1.api.aws/v1",
        )


if __name__ == "__main__":
    unittest.main()
