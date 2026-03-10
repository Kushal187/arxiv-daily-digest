import unittest

from apps.worker.app.services.arxiv import canonicalize_identifier, parse_feed


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


if __name__ == "__main__":
    unittest.main()
