#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sync_research_catalogue as rc


class Tests(unittest.TestCase):
    def test_name_normalisation_matches_accents_and_case(self):
        self.assertEqual(rc.norm("Øyvind Brandtsegg"), rc.norm("oyvind brandtsegg"))
        self.assertEqual(rc.norm("Jon-Marius Aareskjold-Drecker"), "jonmarius aareskjolddrecker")

    def test_image_only_for_permissive_licences(self):
        base = {"rc_id": 1, "thumb_url": "https://example.org/x.png"}
        self.assertIsNotNone(rc.fetch_image({**base, "licence": "cc-by"}, dry_run=True))
        self.assertIsNotNone(rc.fetch_image({**base, "licence": "cc-by-nc-nd"}, dry_run=True))
        self.assertIsNone(rc.fetch_image({**base, "licence": "all-rights-reserved"}, dry_run=True))
        self.assertIsNone(rc.fetch_image({**base, "licence": None}, dry_run=True))
        self.assertIsNone(rc.fetch_image({"licence": "cc-by"}, dry_run=True))

    def test_licence_labels(self):
        self.assertEqual(rc.LICENCE_LABEL["cc-by-nc-nd"], "CC BY-NC-ND")
        self.assertEqual(rc.LICENCE_LABEL["all-rights-reserved"], "all rights reserved")


class YearFloorTest(unittest.TestCase):
    def test_only_the_centre_period_is_kept(self):
        self.assertTrue(rc.recent_enough({"date": "2025-01-29"}))
        self.assertTrue(rc.recent_enough({"date": "2026-12-13"}))
        self.assertFalse(rc.recent_enough({"date": "2024-10-16"}))
        self.assertFalse(rc.recent_enough({"date": "2014-09-21"}))

    def test_an_exposition_without_a_usable_date_is_left_out(self):
        self.assertFalse(rc.recent_enough({}))
        self.assertFalse(rc.recent_enough({"date": ""}))
        self.assertFalse(rc.recent_enough({"date": "n.d."}))


if __name__ == "__main__":
    unittest.main()
