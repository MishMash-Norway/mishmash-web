"""Tests for scripts/enrich_results_from_openalex.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich_results_from_openalex as e


class DoiTest(unittest.TestCase):
    def test_doi_is_read_from_the_link_and_the_citation(self):
        r = {"url": "https://doi.org/10.5334/tismir.223",
             "citation": {"details": "In: Proceedings. https://doi.org/10.1145/3802842.3802884."}}
        self.assertEqual(e.dois_of(r), {"10.5334/tismir.223", "10.1145/3802842.3802884"})

    def test_a_result_without_a_doi_yields_none(self):
        self.assertEqual(e.dois_of({"url": "https://nva.sikt.no/registration/abc"}), set())


class LicenceTest(unittest.TestCase):
    def test_creative_commons_urls_become_codes(self):
        self.assertEqual(e.licence_code("https://creativecommons.org/licenses/by/4.0/"), "cc-by")
        self.assertEqual(e.licence_code("http://creativecommons.org/licenses/by-nc-nd/4.0"), "cc-by-nc-nd")
        self.assertEqual(e.licence_code("https://creativecommons.org/publicdomain/zero/1.0/"), "cc0")

    def test_a_publisher_licence_page_is_not_a_code(self):
        self.assertIsNone(e.licence_code("https://www.elsevier.com/tdm/userlicense/1.0/"))
        self.assertIsNone(e.licence_code(None))


class EntryTest(unittest.TestCase):
    def test_a_gold_work_is_free_and_carries_its_licence(self):
        work = {"open_access": {"oa_status": "gold", "is_oa": True},
                "best_oa_location": {"landing_page_url": "https://example.org/a", "license": "cc-by"}}
        entry = e.entry_for(work, "https://creativecommons.org/licenses/by/4.0/")
        self.assertTrue(entry["free"])
        self.assertEqual(entry["label"], "open access")
        self.assertEqual(entry["licence_label"], "CC BY")
        self.assertEqual(entry["url"], "https://example.org/a")

    def test_a_closed_work_is_not_free_and_gets_no_link(self):
        entry = e.entry_for({"open_access": {"oa_status": "closed", "is_oa": False}}, None)
        self.assertFalse(entry["free"])
        self.assertNotIn("url", entry)
        self.assertNotIn("licence", entry)

    def test_an_author_copy_is_marked_as_such(self):
        entry = e.entry_for({"open_access": {"oa_status": "green", "is_oa": True},
                             "best_oa_location": {"pdf_url": "https://repo.example/a.pdf"}}, None)
        self.assertEqual(entry["status"], "green")
        self.assertTrue(entry["free"])
        self.assertEqual(entry["url"], "https://repo.example/a.pdf")

    def test_a_publisher_licence_is_not_shown_as_a_code(self):
        work = {"open_access": {"oa_status": "hybrid", "is_oa": True}, "best_oa_location": {}}
        entry = e.entry_for(work, "https://www.elsevier.com/tdm/userlicense/1.0/")
        self.assertNotIn("licence_label", entry)
        self.assertEqual(entry["licence_url"], "https://www.elsevier.com/tdm/userlicense/1.0/")


if __name__ == "__main__":
    unittest.main()
