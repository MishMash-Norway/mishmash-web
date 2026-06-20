#!/usr/bin/env python3
import unittest

from enrich_directory_from_nva import (
    collect_other_projects_from_hits,
    nva_project_id_from_url,
    nva_public_project_url,
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


if __name__ == "__main__":
    unittest.main()
