#!/usr/bin/env python3
import unittest
from pathlib import Path

import check_readability as cr


class LixTests(unittest.TestCase):
    def test_simple_text_scores_lower(self):
        simple = (
            "The cat sat on the mat. It was a nice day. We like to play. "
            "The sun is out. Birds sing in the tree. We eat some food. "
            "Then we go home. It is fun. The dog runs fast. We laugh a lot."
        )
        complex_ = (
            "Multidisciplinary collaboration necessitates methodological "
            "pluralism, integrating computational, ethnographic, and "
            "philosophical perspectives across institutional boundaries while "
            "simultaneously addressing epistemological tensions inherent in "
            "cross-sectoral knowledge production frameworks."
        )
        self.assertLess(cr.lix(simple), cr.lix(complex_))

    def test_short_text_returns_none(self):
        self.assertIsNone(cr.lix("Too short to score."))


class StripMarkupTests(unittest.TestCase):
    def test_removes_liquid_html_links(self):
        text = (
            '{% include stretch.html term="ai" %} Hello <em>world</em> '
            "[link text](/somewhere/) ![alt](/img.png)"
        )
        cleaned = cr.strip_markup(text)
        self.assertNotIn("include", cleaned)
        self.assertNotIn("<em>", cleaned)
        self.assertIn("link text", cleaned)
        self.assertNotIn("/somewhere/", cleaned)


class CheckPageTests(unittest.TestCase):
    LEVELS = ["simple", "standard", "advanced"]

    def test_warns_on_missing_level(self):
        body = (
            "## Section\n\n"
            '<div class="adaptive" data-for="simple" markdown="1">\nA cat.\n</div>\n'
            '<div class="adaptive" data-for="standard" markdown="1">\nA cat too.\n</div>\n'
        )
        warnings = []
        cr.check_page(Path("test.md"), body, self.LEVELS, warnings)
        self.assertEqual(len(warnings), 1)
        self.assertIn("advanced", warnings[0])

    def test_no_warning_when_all_covered(self):
        body = (
            "## Section\n\n"
            '<div class="adaptive" data-for="simple standard" markdown="1">\nA cat.\n</div>\n'
            '<div class="adaptive" data-for="advanced" markdown="1">\nA feline specimen.\n</div>\n'
        )
        warnings = []
        cr.check_page(Path("test.md"), body, self.LEVELS, warnings)
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
