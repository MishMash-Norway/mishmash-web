#!/usr/bin/env python3
import unittest

from enrich_directory_from_nva import top_selected_works


class TopSelectedWorksTests(unittest.TestCase):
    def test_picks_newest_works_not_api_order(self):
        api_order = [
            {"title": "Old conference talk", "year": "2012"},
            {"title": "Recent journal article", "year": "2025"},
            {"title": "Middle book chapter", "year": "2019"},
            {"title": "Another recent article", "year": "2025"},
            {"title": "Ancient monograph", "year": "2006"},
        ]
        selected = top_selected_works(api_order, max_works=3)
        self.assertEqual(
            [work["title"] for work in selected],
            [
                "Recent journal article",
                "Another recent article",
                "Middle book chapter",
            ],
        )


if __name__ == "__main__":
    unittest.main()
