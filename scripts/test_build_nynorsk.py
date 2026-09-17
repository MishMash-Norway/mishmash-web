#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_nynorsk import strip_marks, apply_replacements, nn_permalink, segment, split_front_matter, transform_page, translate_text


class FakeTranslator:
    """Upper-cases the text so the test can see what was and was not translated."""
    local = False

    def translate(self, text):
        return text.upper()


GLOSSARY = {"keep": ["MishMash", "MeshUp"], "replace": {"FORSKNINGSRÅDET": "Forskingsrådet"}}


class SegmentTests(unittest.TestCase):
    def test_protects_liquid_code_links_emphasis_and_names(self):
        text = "Se {% include x.html %} og `kode` i [lenke](/no/om/) med **fet** tekst, NVA og MishMash."
        parts = segment(text, GLOSSARY["keep"])
        protected = [c for p, c in parts if p]
        for span in ["{% include x.html %}", "`kode`", "](/no/om/)", "**", "NVA", "MishMash"]:
            self.assertIn(span, protected)
        self.assertEqual("".join(c for _, c in parts), text)

    def test_nested_protection_is_merged(self):
        parts = segment('<a href="{{ url }}">tekst</a>', [])
        self.assertEqual([c for p, c in parts if p], ['<a href="{{ url }}">', "</a>"])

    def test_translate_text_keeps_structure(self):
        out = translate_text("Se **fet** tekst om MishMash i [lenke](/x/).\n\n- Punkt", FakeTranslator(), GLOSSARY)
        self.assertEqual(out, "SE **FET** TEKST OM MishMash I [LENKE](/x/).\n\n- PUNKT")

    def test_marks_are_removed_but_headings_kept(self):
        self.assertEqual(strip_marks("## Overskrift og #liste her\ngå# tapt, 2.1 # og vere#"), "## Overskrift og liste her\ngå tapt, 2.1  og vere")

    def test_replacements(self):
        self.assertEqual(apply_replacements("FORSKNINGSRÅDET gir", GLOSSARY["replace"]), "Forskingsrådet gir")


class PageTests(unittest.TestCase):
    def test_transform_page(self):
        src = """---
layout: page
lang: nb
title: Om MishMash
permalink: /no/about/
translation_url: /about/
redirect_from:
  - /no/om/
---

Første avsnitt om MishMash.

{% include partner-list.html lang="nb" %}
"""
        out = transform_page(src, Path("about/index.md"), FakeTranslator(), GLOSSARY)
        data, _, body = split_front_matter(out)
        self.assertEqual(data["lang"], "nn")
        self.assertEqual(data["permalink"], "/nn/about/")
        self.assertEqual(data["title"], "OM MishMash")
        self.assertEqual(data["translation"]["source_url"], "/no/about/")
        self.assertTrue(data["translation"]["automatic"])
        self.assertNotIn("redirect_from", data)
        self.assertIn("FØRSTE AVSNITT OM MishMash.", body)
        self.assertIn('{% include partner-list.html lang="nb" %}', body)

    def test_permalink(self):
        self.assertEqual(nn_permalink("/no/results/pulse/"), "/nn/results/pulse/")


if __name__ == "__main__":
    unittest.main()
