#!/usr/bin/env python3
import unittest
from datetime import date
from unittest.mock import patch

from enrich_directory_from_nva import (
    collect_other_projects_from_hits,
    nva_project_id_from_url,
    nva_project_is_active,
    nva_other_projects,
    nva_public_project_url,
    parse_nva_date,
)


class NvaOtherProjectsTests(unittest.TestCase):
    def test_nva_project_id_from_url(self):
        self.assertEqual(
            nva_project_id_from_url("https://api.nva.unit.no/cristin/project/2762680"),
            "2762680",
        )

    def test_nva_public_project_url(self):
        self.assertEqual(nva_public_project_url("2762680"), "https://nva.sikt.no/projects/2762680")

    def test_collect_other_projects_from_hits(self):
        hits = [
            {
                "title": "Norwegian Centre for Embodied AI (NCEI)",
                "id": "https://api.nva.unit.no/cristin/project/2762680",
                "endDate": "2030-01-01T00:00:00Z",
            },
            {
                "title": "MishMash",
                "id": "https://api.nva.unit.no/cristin/project/2744839",
            },
            {
                "title": "Musical Gestures",
                "id": "https://api.nva.unit.no/cristin/project/277450",
                "endDate": "2007-07-01T00:00:00Z",
            },
            {
                "title": "RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion",
                "id": "https://api.nva.unit.no/cristin/project/568602",
            },
        ]
        projects = collect_other_projects_from_hits(hits, today=date(2026, 9, 27))
        self.assertEqual(
            projects,
            {
                "2762680": "Norwegian Centre for Embodied AI (NCEI)",
                "568602": "RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion",
            },
        )

    def test_parse_nva_date(self):
        self.assertEqual(parse_nva_date("2027-06-20T00:00:00Z"), date(2027, 6, 20))
        self.assertIsNone(parse_nva_date(""))

    def test_nva_project_is_active(self):
        today = date(2026, 6, 17)
        self.assertTrue(
            nva_project_is_active({"endDate": "2027-06-20T00:00:00Z"}, today=today)
        )
        self.assertFalse(
            nva_project_is_active({"endDate": "2008-12-31T00:00:00Z"}, today=today)
        )
        self.assertTrue(nva_project_is_active({}, today=today))
        self.assertFalse(
            nva_project_is_active({"startDate": "2027-01-01T00:00:00Z"}, today=today)
        )

    def test_nva_project_status_wins_over_dates(self):
        today = date(2026, 6, 17)
        self.assertTrue(nva_project_is_active({"status": "ACTIVE"}, today=today))
        self.assertFalse(
            nva_project_is_active(
                {"status": "CONCLUDED", "endDate": "2027-06-20T00:00:00Z"}, today=today
            )
        )
        self.assertFalse(nva_project_is_active({"status": "NOTSTARTED"}, today=today))

    @patch("enrich_directory_from_nva.requests.get")
    def test_nva_other_projects_queries_participant_and_follows_pages(self, mock_get):
        pages = [
            {
                "hits": [{"title": "Beta", "id": "https://api.nva.unit.no/cristin/project/1002"}],
                "nextResults": "https://api.nva.unit.no/cristin/project?page=2&participant=1328",
            },
            {
                "hits": [{"title": "Alpha", "id": "https://api.nva.unit.no/cristin/project/1001"}],
            },
        ]
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.side_effect = pages

        projects = nva_other_projects("1328")

        first_call, second_call = mock_get.call_args_list
        self.assertTrue(first_call.args[0].endswith("/cristin/project"))
        self.assertEqual(first_call.kwargs["params"]["participant"], "1328")
        self.assertEqual(second_call.args[0], pages[0]["nextResults"])
        self.assertEqual(
            projects,
            [
                {"title": "Alpha", "url": "https://nva.sikt.no/projects/1001", "nva_id": "1001"},
                {"title": "Beta", "url": "https://nva.sikt.no/projects/1002", "nva_id": "1002"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
