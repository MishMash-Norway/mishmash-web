#!/usr/bin/env python3
import unittest

import sync_wikidata as sw


class HelperTests(unittest.TestCase):
    def test_orcid_id_from_url(self):
        self.assertEqual(
            sw.orcid_id("https://orcid.org/0000-0001-6171-8743"),
            "0000-0001-6171-8743",
        )

    def test_orcid_id_with_x_checksum(self):
        self.assertEqual(
            sw.orcid_id("https://orcid.org/0000-0002-1825-009x"),
            "0000-0002-1825-009X",
        )

    def test_orcid_id_missing(self):
        self.assertIsNone(sw.orcid_id(""))
        self.assertIsNone(sw.orcid_id(None))
        self.assertIsNone(sw.orcid_id("https://example.com/not-orcid"))

    def test_wikipedia_title(self):
        self.assertEqual(
            sw.wikipedia_title("https://en.wikipedia.org/wiki/University_of_Oslo"),
            "University of Oslo",
        )

    def test_wikipedia_title_percent_encoded(self):
        self.assertEqual(
            sw.wikipedia_title("https://en.wikipedia.org/wiki/%C3%98stfold_University_College"),
            "Østfold University College",
        )

    def test_wikipedia_title_non_english(self):
        self.assertIsNone(sw.wikipedia_title("https://no.wikipedia.org/wiki/Oslo"))

    def test_qid_to_url(self):
        self.assertEqual(sw.qid_to_url("Q186619"), "https://www.wikidata.org/wiki/Q186619")

    def test_qid_to_url_rejects_garbage(self):
        with self.assertRaises(AssertionError):
            sw.qid_to_url("not-a-qid")


if __name__ == "__main__":
    unittest.main()
