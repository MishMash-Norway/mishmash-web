#!/usr/bin/env python3
import unittest

from nva_result_types import orcid_result_group_type, orcid_work_type_label


class OrcidWorkTypeTests(unittest.TestCase):
    def test_maps_journal_article(self):
        self.assertEqual(orcid_work_type_label("journal-article"), "Journal article")
        self.assertEqual(orcid_result_group_type("journal-article"), "Journal article")

    def test_maps_conference_paper(self):
        self.assertEqual(orcid_work_type_label("conference-paper"), "Conference paper")
        self.assertEqual(orcid_result_group_type("conference-paper"), "Conference")

    def test_unknown_type_title_cases(self):
        self.assertEqual(orcid_work_type_label("technical-standard"), "Technical Standard")


if __name__ == "__main__":
    unittest.main()
