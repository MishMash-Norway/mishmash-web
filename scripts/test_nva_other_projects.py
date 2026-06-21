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
                "projects": [
                    {
                        "name": "Norwegian Centre for Embodied AI (NCEI)",
                        "id": "https://api.nva.unit.no/cristin/project/2762680",
                    },
                    {
                        "name": "MishMash",
                        "id": "https://api.nva.unit.no/cristin/project/2744839",
                    },
                ]
            },
            {
                "projects": [
                    {
                        "name": "RITMO Centre for Interdisciplinary Studies in Rhythm, Time and Motion",
                        "id": "https://api.nva.unit.no/cristin/project/568602",
                    }
                ]
            },
        ]
        projects = collect_other_projects_from_hits(hits)
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

    @patch("enrich_directory_from_nva.get_json")
    @patch("enrich_directory_from_nva.requests.get")
    def test_nva_other_projects_filters_inactive(self, mock_get, mock_get_json):
        mock_get.return_value.json.return_value = {
            "hits": [
                {
                    "projects": [
                        {
                            "name": "Active Project",
                            "id": "https://api.nva.unit.no/cristin/project/1001",
                        },
                        {
                            "name": "Ended Project",
                            "id": "https://api.nva.unit.no/cristin/project/1002",
                        },
                    ]
                }
            ],
            "totalHits": 1,
        }
        mock_get.return_value.raise_for_status = lambda: None

        def project_payload(_url):
            if _url.endswith("/1001"):
                return {"endDate": "2027-01-01T00:00:00Z"}
            if _url.endswith("/1002"):
                return {"endDate": "2020-01-01T00:00:00Z"}
            raise AssertionError(_url)

        mock_get_json.side_effect = project_payload

        projects = nva_other_projects("1328", project_cache={})
        self.assertEqual(
            projects,
            [
                {
                    "title": "Active Project",
                    "url": "https://nva.sikt.no/projects/1001",
                    "nva_id": "1001",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
