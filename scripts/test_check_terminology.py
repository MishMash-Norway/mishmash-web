#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_terminology
from check_terminology import problems, same_in_both_norwegians

FULL = {
    "key": "board",
    "term": {"en": "Board", "nb": "Styret", "nn": "Styret"},
    "standard": {"en": "the governing body", "nb": "det styrende organet"},
}


class TerminologyTests(unittest.TestCase):
    def test_a_complete_entry_passes(self):
        self.assertEqual(problems([FULL]), [])

    def test_a_missing_nynorsk_term_is_reported(self):
        entry = {**FULL, "term": {"en": "Board", "nb": "Styret"}}
        self.assertEqual(problems([entry]), ["board: no nn term"])

    def test_an_empty_term_counts_as_missing(self):
        entry = {**FULL, "term": {"en": "Board", "nb": "Styret", "nn": "  "}}
        self.assertEqual(problems([entry]), ["board: no nn term"])

    def test_a_repeated_key_is_reported(self):
        self.assertIn("board: the key appears twice", problems([FULL, FULL]))

    def test_a_missing_reading_level_is_reported(self):
        entry = {**FULL, "standard": {"en": "the governing body"}}
        self.assertEqual(problems([entry]), ["board: no nb text at the standard reading level"])

    def test_identical_norwegian_forms_are_listed_not_failed(self):
        self.assertEqual(same_in_both_norwegians([FULL]), ["board: Styret"])
        self.assertEqual(problems([FULL]), [])

    def test_the_site_glossary_is_complete(self):
        if not check_terminology.GLOSSARY.exists():
            self.skipTest("glossary not present")
        import yaml
        entries = yaml.safe_load(check_terminology.GLOSSARY.read_text(encoding="utf-8")) or []
        self.assertEqual(problems(entries), [])


if __name__ == "__main__":
    unittest.main()
