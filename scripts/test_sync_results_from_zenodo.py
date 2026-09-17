#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_results_from_zenodo import merge, simplify

HIT = {"id": 1, "doi": "10.5281/zenodo.1", "conceptdoi": "10.5281/zenodo.0",
       "metadata": {"title": "A dataset", "resource_type": {"type": "dataset"}, "publication_date": "2026-05-01",
                    "creators": [{"name": "Nordmann, Kari", "orcid": "0000-0001-0000-0000"}], "license": {"id": "cc-by-4.0"},
                    "keywords": ["music"]},
       "files": [{"size": 100}, {"size": 250}], "links": {"self_html": "https://zenodo.org/records/1"}}


class Tests(unittest.TestCase):
    def test_simplify(self):
        r = simplify(HIT, "community")
        self.assertEqual(r["doi"], "10.5281/zenodo.1")
        self.assertEqual(r["type"], "dataset")
        self.assertEqual(r["size_bytes"], 350)
        self.assertEqual(r["creators"][0]["name"], "Nordmann, Kari")

    def test_merge_dedupes_and_marks_nva(self):
        recs = merge([HIT], [HIT], {"10.5281/zenodo.1"})
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["membership"], "community and grant")
        self.assertTrue(recs[0]["in_nva"])


if __name__ == "__main__":
    unittest.main()
