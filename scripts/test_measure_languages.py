#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure_languages import clean, declared_language, measure, paragraphs


def fake_detect(p):
    if "nettstaden" in p.lower():
        return "nn"
    if "nettstedet" in p.lower():
        return "nb"
    return "en"


class CleanTests(unittest.TestCase):
    def test_strips_markup_and_keeps_words(self):
        body = "## Heading\n\nSee [the page](/x/) and `code` {% include a.html %} **bold** <em>tag</em>.\n\n- item one two three four five"
        out = clean(body)
        self.assertNotIn("include", out)
        self.assertNotIn("<em>", out)
        self.assertIn("the page", out)
        self.assertIn("bold", out)

    def test_paragraph_threshold(self):
        self.assertEqual(paragraphs("one two\n\nthree four five six seven"), ["three four five six seven"])

    def test_declared_language(self):
        self.assertEqual(declared_language({}, Path("no/about/index.md")), "nb")
        self.assertEqual(declared_language({"lang": "nn"}, Path("nn-auto/x.md")), "nn")
        self.assertEqual(declared_language({}, Path("about/index.md")), "en")


class MeasureTests(unittest.TestCase):
    def test_counts_and_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "no").mkdir()
            (root / "no" / "a.md").write_text("---\nlang: nb\n---\nNettstedet er fint og godt for alle.\n", encoding="utf-8")
            (root / "b.md").write_text("---\ntitle: x\n---\nNettstaden er fin og god for alle her.\n", encoding="utf-8")
            (root / "internal").mkdir()
            (root / "internal" / "c.md").write_text("---\n---\nSecret words that must not be counted at all.\n", encoding="utf-8")
            r = measure(root, fake_detect)
            self.assertEqual(r["words"]["nb"], 7)
            self.assertEqual(r["words"]["nn"], 8)
            self.assertEqual(r["words"]["en"], 0)
            self.assertEqual([m["page"] for m in r["mismatches"]], ["b.md"])


if __name__ == "__main__":
    unittest.main()
