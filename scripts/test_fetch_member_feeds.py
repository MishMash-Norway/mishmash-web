#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_member_feeds import parse_date, parse_feed

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>A blog</title>
<item><title>First post</title><link>https://example.org/1</link><pubDate>Tue, 02 Sep 2026 10:00:00 +0200</pubDate><description>&lt;p&gt;Some &lt;b&gt;text&lt;/b&gt;.&lt;/p&gt;</description></item>
<item><title>Second</title><link>https://example.org/2</link><pubDate>Mon, 01 Sep 2026 10:00:00 +0200</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>B</title>
<entry><title>Atom post</title><link href="https://example.org/a"/><updated>2026-09-03T08:00:00Z</updated><summary>Short</summary></entry>
</feed>"""


class Tests(unittest.TestCase):
    def test_rss(self):
        posts = parse_feed(RSS)
        self.assertEqual([p["title"] for p in posts], ["First post", "Second"])
        self.assertEqual(posts[0]["date"], "2026-09-02")
        self.assertEqual(posts[0]["summary"], "Some text .")
        self.assertIsNone(posts[1]["summary"])

    def test_atom(self):
        posts = parse_feed(ATOM)
        self.assertEqual(posts[0]["url"], "https://example.org/a")
        self.assertEqual(posts[0]["date"], "2026-09-03")

    def test_broken_feed_is_empty_not_an_error(self):
        self.assertEqual(parse_feed("<html>not a feed</html>"), [])

    def test_dates(self):
        self.assertEqual(parse_date("2026-09-04T12:00:00Z"), "2026-09-04")
        self.assertIsNone(parse_date("no date here"))


if __name__ == "__main__":
    unittest.main()
