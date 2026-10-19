#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wikidata_centre_statements import statements

CENTRE = {
    "name": {"en": "MishMash Centre for AI and Creativity", "nb": "MishMash Senter for KI og kreativitet"},
    "short_name": "MishMash", "url": "https://mishmash.no/",
    "dates": [{"key": "started", "date": "2025-12-01"}, {"key": "ends", "date": "2030-12-31"}],
    "host": {"slug": "university-of-oslo"},
    "funder": {"wikidata": "https://www.wikidata.org/wiki/Q4356293", "url": "https://prosjektbanken.example/357438"},
    "identifiers": {"nva_project": "https://nva.example/2744839", "rcn_project": "https://prosjektbanken.example/357438"},
    "roles": [{"role": "Director", "since": "2025-12-01"}, {"role": "Deputy Director", "since": "2025-12-01"}],
}
PEOPLE = [{"roles": ["Director"], "urls": {"wikidata": "https://www.wikidata.org/wiki/Q47281555"}},
          {"roles": ["Deputy Director"], "urls": {"wikidata": "https://www.wikidata.org/wiki/Q1"}},
          {"roles": ["Director"], "urls": {"wikidata": ""}}]
INSTITUTIONS = {"university-of-oslo": {"urls": {"wikidata": "https://www.wikidata.org/wiki/Q486156"}}}


class CentreStatementTests(unittest.TestCase):
    def setUp(self):
        self.lines = statements(CENTRE, PEOPLE, INSTITUTIONS, "2026-10-16")

    def test_starts_by_creating_the_item(self):
        self.assertEqual(self.lines[0], "CREATE")

    def test_inception_is_the_start_date(self):
        self.assertTrue(any(l.startswith("LAST\tP571\t+2025-12-01T00:00:00Z/11") for l in self.lines))

    def test_the_funder_carries_the_funding_period_and_its_source(self):
        line = next(l for l in self.lines if "\tP8324\t" in l)
        self.assertIn("Q4356293\tP580\t+2025-12-01T00:00:00Z/11\tP582\t+2030-12-31T00:00:00Z/11", line)
        self.assertIn('S854\t"https://prosjektbanken.example/357438"', line)

    def test_only_a_director_with_a_wikidata_item_is_added(self):
        directors = [l for l in self.lines if "\tP1037\t" in l]
        self.assertEqual(len(directors), 1)
        self.assertIn("Q47281555\tP580\t+2025-12-01", directors[0])

    def test_roles_without_a_property_are_left_out(self):
        self.assertFalse(any("\tQ1\t" in l or l.endswith("\tQ1") for l in self.lines))

    def test_the_parent_is_the_host_cited_to_nva(self):
        line = next(l for l in self.lines if "\tP749\t" in l)
        self.assertIn('Q486156\tS854\t"https://nva.example/2744839"', line)


if __name__ == "__main__":
    unittest.main()
