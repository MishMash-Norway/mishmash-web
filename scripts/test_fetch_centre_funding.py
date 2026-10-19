#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_centre_funding import funding_from_page


def page(project):
    data = {"props": {"pageProps": {"initialState": {"PROJECT": {"project": project}}}}}
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'


class CentreFundingTests(unittest.TestCase):
    def test_reads_amount_programme_and_years(self):
        found = funding_from_page(page({
            "currentActivity": {"activity": "IKTFORSKNING-IKTFORSKNING", "totalFunding": 1000.4},
            "duration": {"startYear": 2025, "endYear": 2030},
            "fundingBodies": ["Kunnskapsdepartementet"]}))
        self.assertEqual(found["amount_nok"], 1000)
        self.assertEqual(found["amount_million_nok"], 0.0)
        self.assertEqual(found["programme"], "IKTFORSKNING")
        self.assertEqual((found["start_year"], found["end_year"]), (2025, 2030))

    def test_the_amount_in_millions_has_one_decimal(self):
        found = funding_from_page(page({"currentActivity": {"activity": "X-X", "totalFunding": 257308740.48}}))
        self.assertEqual(found["amount_million_nok"], 257.3)

    def test_a_page_without_an_amount_is_refused(self):
        with self.assertRaises(ValueError):
            funding_from_page(page({"currentActivity": {}, "totalFunding": 0}))

    def test_a_page_without_data_is_refused(self):
        with self.assertRaises(ValueError):
            funding_from_page("<html></html>")


if __name__ == "__main__":
    unittest.main()
