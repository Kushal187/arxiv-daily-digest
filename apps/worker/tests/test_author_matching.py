import unittest

from apps.worker.app.services.ranking import match_followed_authors, score_author_match


class AuthorMatchingTests(unittest.TestCase):
    def test_exact_author_match_scores_highest(self):
        self.assertEqual(score_author_match("Yann LeCun", "Yann LeCun"), 1.0)

    def test_initial_only_match_is_rejected(self):
        self.assertEqual(score_author_match("Yann LeCun", "Y. LeCun"), 0.0)

    def test_small_last_name_typo_still_matches(self):
        self.assertGreater(score_author_match("Yann Lecunn", "Yann LeCun"), 0.0)

    def test_same_last_name_with_full_given_name_variation_matches(self):
        self.assertGreater(score_author_match("Geoffrey Hinton", "Geoff Hinton"), 0.0)

    def test_match_followed_authors_returns_best_match(self):
        matches = match_followed_authors(["Yann Lecunn"], ["Alice Example", "Yann LeCun"])
        self.assertEqual(matches[0]["paper_author"], "Yann LeCun")

    def test_match_followed_authors_excludes_initial_only_false_positive(self):
        matches = match_followed_authors(["Yann LeCun"], ["Alice Example", "Y. LeCun"])
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
