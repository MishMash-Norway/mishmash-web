#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_nynorsk
from build_nynorsk import strip_marks, fix_list_markers, apply_replacements, load_glossary, nn_permalink, report_glossary_use, segment, split_front_matter, transform_page, translate_text


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

    def test_protects_single_asterisk_italics(self):
        text = "norsk (både *bokmål* og *nynorsk*), og **fet** tekst"
        parts = segment(text, GLOSSARY["keep"])
        protected = [c for p, c in parts if p]
        self.assertEqual(protected.count("*"), 4)
        self.assertIn("**", protected)
        self.assertEqual("".join(c for _, c in parts), text)
        self.assertEqual(
            translate_text(text, FakeTranslator(), GLOSSARY),
            "NORSK (BÅDE *BOKMÅL* OG *NYNORSK*), OG **FET** TEKST",
        )

    def test_nested_protection_is_merged(self):
        parts = segment('<a href="{{ url }}">tekst</a>', [])
        self.assertEqual([c for p, c in parts if p], ['<a href="{{ url }}">', "</a>"])

    def test_translate_text_keeps_structure(self):
        out = translate_text("Se **fet** tekst om MishMash i [lenke](/x/).\n\n- Punkt", FakeTranslator(), GLOSSARY)
        self.assertEqual(out, "SE **FET** TEKST OM MishMash I [LENKE](/x/).\n\n- PUNKT")

    def test_marks_are_removed_but_headings_kept(self):
        self.assertEqual(strip_marks("## Overskrift og #liste her\ngå# tapt, 2.1 # og vere#"), "## Overskrift og liste her\ngå tapt, 2.1  og vere")

    def test_ordered_list_markers_are_repaired(self):
        self.assertEqual(fix_list_markers("1 . Fyrst\n2 . Deretter"), "1. Fyrst\n2. Deretter")
        self.assertEqual(fix_list_markers("  3 . Innrykk"), "  3. Innrykk")
        self.assertEqual(fix_list_markers("Vi vann 3 . plass"), "Vi vann 3 . plass")

    def test_replacements(self):
        self.assertEqual(apply_replacements("FORSKNINGSRÅDET gir", GLOSSARY["replace"]), "Forskingsrådet gir")


class GlossaryUseTests(unittest.TestCase):
    """The glossary can fail: a rule that repairs nothing is reported, and
    --check-glossary turns that into a non-zero exit."""

    def setUp(self):
        build_nynorsk.REPLACEMENTS_USED.clear()
        self.addCleanup(build_nynorsk.REPLACEMENTS_USED.clear)

    def test_counts_what_each_rule_repaired(self):
        apply_replacements("Rå frå A og Rå frå B", {"Rå frå": "Råd frå", "Me vel ": "Vi vel "})
        self.assertEqual(build_nynorsk.REPLACEMENTS_USED, {"Rå frå": 2})

    def test_unused_rule_fails_the_check(self):
        glossary = {"replace": {"Rå frå": "Råd frå"}, "expected_unused": []}
        self.assertEqual(report_glossary_use(glossary, set(), "apy", fail=True), 1)
        self.assertEqual(report_glossary_use(glossary, set(), "apy", fail=False), 0)

    def test_rule_that_fired_passes(self):
        build_nynorsk.REPLACEMENTS_USED["Rå frå"] = 1
        glossary = {"replace": {"Rå frå": "Råd frå"}, "expected_unused": []}
        self.assertEqual(report_glossary_use(glossary, set(), "apy", fail=True), 0)

    def test_expected_unused_rule_passes(self):
        glossary = {"replace": {"Rå frå": "Råd frå"}, "expected_unused": ["Rå frå"]}
        self.assertEqual(report_glossary_use(glossary, {"Rå frå"}, "apy", fail=True), 0)

    def test_every_exempt_key_is_a_real_rule(self):
        if not build_nynorsk.GLOSSARY.exists():
            self.skipTest("glossary not present")
        g = load_glossary()
        for key in g["expected_unused"]:
            self.assertIn(key, g["replace"], f"expected_unused lists {key!r}, which is not a rule")


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
