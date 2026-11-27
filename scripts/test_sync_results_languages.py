#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_results_from_nva import nva_language_tag


class NvaResultLanguageTests(unittest.TestCase):
    def test_common_iso_639_3_codes_map_to_site_tags(self):
        cases = {
            "http://lexvo.org/id/iso639-3/eng": "en",
            "http://lexvo.org/id/iso639-3/nob": "nb",
            "http://lexvo.org/id/iso639-3/nno": "nn",
            "http://lexvo.org/id/iso639-3/fra": "fr",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(nva_language_tag(source), expected)

    def test_other_registered_language_code_is_preserved(self):
        self.assertEqual(nva_language_tag("http://lexvo.org/id/iso639-3/sme"), "sme")

    def test_missing_or_invalid_language_is_undetermined(self):
        self.assertEqual(nva_language_tag(None), "und")
        self.assertEqual(nva_language_tag("not a language tag"), "und")


if __name__ == "__main__":
    unittest.main()