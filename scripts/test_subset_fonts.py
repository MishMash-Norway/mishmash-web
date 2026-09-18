"""Tests for scripts/subset_fonts.py."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import subset_fonts


class SubsetFontsTest(unittest.TestCase):
    def test_script_and_style_contents_are_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "index.html").write_text(
                "<html><head><style>.a{content:'Ж'}</style>"
                "<script>var x='中';</script></head>"
                "<body><p>Hei &amp; hå</p></body></html>",
                encoding="utf-8",
            )
            chars = subset_fonts.used_characters(d)
            self.assertNotIn("Ж", chars)
            self.assertNotIn("中", chars)
            self.assertTrue({"H", "e", "i", "&", "å"} <= chars)

    def test_json_text_is_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "search.json").write_text('[{"title": "Sławomir"}]', encoding="utf-8")
            self.assertIn("ł", subset_fonts.used_characters(d))

    def test_safety_set_covers_norwegian_and_sami(self):
        with tempfile.TemporaryDirectory() as tmp:
            chars = subset_fonts.used_characters(Path(tmp))
            for c in "æøåÆØÅáčđŋšŧž":
                self.assertIn(c, chars, c)

    def test_a_real_font_gets_smaller_and_keeps_its_characters(self):
        src = Path(__file__).resolve().parents[1] / "site" / "assets" / "fonts" / "inter-400-latin-ext.woff2"
        if not src.exists():
            self.skipTest("font sources not present")
        from fontTools.ttLib import TTFont

        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "out.woff2"
            before, after = subset_fonts.subset_file(src, dst, set("Sławomir Čapek"))
            self.assertLess(after, before / 2)
            cmap = set(TTFont(dst).getBestCmap())
            self.assertIn(ord("ł"), cmap)
            self.assertIn(ord("Č"), cmap)


if __name__ == "__main__":
    unittest.main()
