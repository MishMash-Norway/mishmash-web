#!/usr/bin/env python3
import unittest

from nva_publication_contributors import (
    build_result_contributors,
    contributor_roles_for_instance,
    person_contributor_role,
    person_has_supervisor_role,
)


class NvaPublicationContributorsTests(unittest.TestCase):
    def test_contributor_roles_for_thesis_includes_supervisors(self):
        roles = contributor_roles_for_instance("DegreePhd")
        self.assertIn("Creator", roles)
        self.assertIn("Author", roles)
        self.assertIn("Supervisor", roles)

    def test_contributor_roles_for_journal_excludes_supervisors(self):
        roles = contributor_roles_for_instance("AcademicArticle")
        self.assertIn("Creator", roles)
        self.assertNotIn("Supervisor", roles)

    def test_build_result_contributors_keeps_roles(self):
        entity = {
            "contributors": [
                {
                    "role": {"type": "Creator"},
                    "identity": {"name": "Riccardo Simionato"},
                },
                {
                    "role": {"type": "Supervisor"},
                    "identity": {"name": "Stefano Fasciani", "id": "https://api.nva.unit.no/cristin/person/1"},
                },
                {
                    "role": {"type": "Supervisor"},
                    "identity": {"name": "Sverre Holm"},
                },
            ]
        }
        lookup = {"1": {"slug": "stefano-fasciani", "name": "Stefano Fasciani", "url": "/people/stefano-fasciani/"}}

        contributors = build_result_contributors(entity, lookup)
        self.assertEqual(
            contributors,
            [
                {"name": "Riccardo Simionato", "role": "Creator"},
                {
                    "name": "Stefano Fasciani",
                    "role": "Supervisor",
                    "slug": "stefano-fasciani",
                    "url": "/people/stefano-fasciani/",
                },
                {"name": "Sverre Holm", "role": "Supervisor"},
            ],
        )

    def test_person_has_supervisor_role(self):
        entity = {
            "contributors": [
                {"role": {"type": "Creator"}, "identity": {"id": "https://api.nva.unit.no/cristin/person/1"}},
                {"role": {"type": "Supervisor"}, "identity": {"id": "https://api.nva.unit.no/cristin/person/2"}},
            ]
        }
        self.assertFalse(person_has_supervisor_role(entity, "1"))
        self.assertTrue(person_has_supervisor_role(entity, "2"))
        self.assertEqual(person_contributor_role(entity, "2"), "Supervisor")

    def test_build_result_contributors_can_filter_roles(self):
        entity = {
            "contributors": [
                {"role": {"type": "Creator"}, "identity": {"name": "Candidate"}},
                {"role": {"type": "Supervisor"}, "identity": {"name": "Supervisor One"}},
            ]
        }
        allowed = contributor_roles_for_instance("DegreePhd")
        contributors = build_result_contributors(entity, {}, allowed_roles=allowed)
        self.assertEqual(len(contributors), 2)
        self.assertEqual(contributors[0]["role"], "Creator")
        self.assertEqual(contributors[1]["role"], "Supervisor")


if __name__ == "__main__":
    unittest.main()
