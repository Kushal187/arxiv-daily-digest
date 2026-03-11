from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from apps.worker.app.services.arxiv import canonicalize_identifier, fetch_entries_for_window, fetch_recent_entries, parse_feed


SAMPLE_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2503.12345v2</id>
    <updated>2026-03-08T11:00:00Z</updated>
    <published>2026-03-08T10:00:00Z</published>
    <title>  Retrieval Augmented Agents  </title>
    <summary>  We study retrieval augmented planning. </summary>
    <author><name>Alice Example</name></author>
    <author><name>Bob Example</name></author>
    <category term="cs.AI" />
    <category term="cs.IR" />
  </entry>
</feed>
"""


class ArxivParsingTests(unittest.TestCase):
    def test_canonicalize_identifier(self):
        canonical_id, version = canonicalize_identifier("http://arxiv.org/abs/2503.12345v2")
        self.assertEqual(canonical_id, "2503.12345")
        self.assertEqual(version, 2)

    def test_parse_feed(self):
        papers = parse_feed(SAMPLE_FEED)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["source_id"], "2503.12345v2")
        self.assertEqual(papers[0]["authors"], ["Alice Example", "Bob Example"])
        self.assertEqual(papers[0]["primary_category"], "cs.AI")

    def test_fetch_recent_entries_dedupes_same_paper_across_categories(self):
        duplicate = parse_feed(SAMPLE_FEED)[0]

        with patch(
            "apps.worker.app.services.arxiv._fetch_entries_for_categories",
            side_effect=[[duplicate], [duplicate]],
        ):
            papers = fetch_recent_entries(["cs.AI", "cs.IR"], max_results_per_category=5)

        self.assertEqual(len(papers), 1)

    def test_fetch_entries_for_window_pages_combined_categories(self):
        duplicate = parse_feed(SAMPLE_FEED)[0]
        second = {**duplicate, "canonical_arxiv_id": "2503.99999", "source_id": "2503.99999v2"}
        window_start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        window_end = datetime(2026, 3, 7, 23, 59, 59, tzinfo=timezone.utc)

        with patch(
            "apps.worker.app.services.arxiv._fetch_entries_for_window",
            side_effect=[[duplicate], [second], []],
        ) as fetch_window, patch("apps.worker.app.services.arxiv.time.sleep") as sleep:
            papers = fetch_entries_for_window(
                ["cs.AI", "cs.IR"],
                window_start,
                window_end,
                page_size=1,
                max_pages=5,
                request_delay_seconds=0.0,
            )

        self.assertEqual({paper["canonical_arxiv_id"] for paper in papers}, {"2503.99999", "2503.12345"})
        self.assertEqual(fetch_window.call_count, 3)
        self.assertEqual(sleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()
