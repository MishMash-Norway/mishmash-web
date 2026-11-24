#!/usr/bin/env python3
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from directory_io import (
    apply_jekyll_defaults,
    as_slug_list,
    normalize_institution_slug,
    normalize_person_slug,
)
from sync_directory_reciprocity import migrate_project_fields


class DirectoryOrcidExceptionTests(unittest.TestCase):
    def validate_person(self, slug, orcid=""):
        with tempfile.TemporaryDirectory() as temporary_directory:
            site_root = Path(temporary_directory)
            person_directory = site_root / "_directory" / "people" / slug
            person_directory.mkdir(parents=True)
            person = {
                "type": "person",
                "slug": slug,
                "name": "Test Person",
                "permalink": f"/people/{slug}/",
                "institutions": [],
                "projects": [],
                "roles": ["Member"],
                "published": True,
                "urls": {"orcid": orcid},
            }
            (person_directory / "index.md").write_text(
                "---\n" + yaml.safe_dump(person) + "---\n", encoding="utf-8"
            )
            return subprocess.run(
                [sys.executable, str(Path(__file__).with_name("validate_directory.py")), "--root", str(site_root)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_anna_without_orcid_is_warned(self):
        result = self.validate_person("anna-myking")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("approved individual exception", result.stdout)

    def test_other_member_without_orcid_fails(self):
        result = self.validate_person("another-person")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("every member needs an ORCID", result.stdout)

    def test_anna_with_orcid_requires_exception_removal(self):
        result = self.validate_person("anna-myking", "https://orcid.org/0000-0002-1825-0097")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("remove 'anna-myking' from ORCID_APPROVED_EXCEPTIONS", result.stdout)


class DirectoryIoTests(unittest.TestCase):
    def test_normalize_person_slug(self):
        self.assertEqual(normalize_person_slug("/people/foo-bar/"), "foo-bar")
        self.assertEqual(normalize_person_slug("foo-bar"), "foo-bar")

    def test_normalize_institution_slug(self):
        self.assertEqual(
            normalize_institution_slug("/institutions/university-of-oslo/"),
            "university-of-oslo",
        )

    def test_as_slug_list_strips_paths(self):
        self.assertEqual(
            as_slug_list(["/people/a/", "b", "/people/c/"]),
            ["a", "b", "c"],
        )

    def test_slug_list_uses_path_refs(self):
        from directory_io import slug_list_uses_path_refs

        self.assertTrue(slug_list_uses_path_refs(["/people/a/"]))
        self.assertFalse(slug_list_uses_path_refs(["a", "b"]))

    def test_apply_jekyll_defaults_for_projects(self):
        data = apply_jekyll_defaults(
            {"layout": "page", "title": "Example Project"},
            "projects",
            "example-project",
        )
        self.assertEqual(data["type"], "project")
        self.assertEqual(data["slug"], "example-project")
        self.assertEqual(data["name"], "Example Project")

    def test_migrate_project_fields_parses_body_links(self):
        body = (
            "## People\n"
            "- Leader: [Ada Lovelace](/people/ada-lovelace/)\n"
            "## Institutions\n"
            "- [University of Oslo](/institutions/university-of-oslo/)\n"
        )
        migrated = migrate_project_fields(
            {"layout": "page", "title": "Demo"},
            "demo",
            body,
        )
        self.assertEqual(migrated["type"], "project")
        self.assertEqual(migrated["slug"], "demo")
        self.assertEqual(migrated["people"], ["ada-lovelace"])
        self.assertEqual(migrated["institutions"], ["university-of-oslo"])


class EnrichOrcidTests(unittest.TestCase):
    def test_orcid_biography_reads_content_field(self):
        from enrich_directory_from_nva import orcid_biography

        person = {"biography": {"content": "Researcher in music technology."}}
        self.assertEqual(orcid_biography(person), "Researcher in music technology.")

    def test_orcid_biography_falls_back_to_value_field(self):
        from enrich_directory_from_nva import orcid_biography

        person = {"biography": {"value": "Legacy biography text."}}
        self.assertEqual(orcid_biography(person), "Legacy biography text.")

    def test_orcid_keyword_labels_split_comma_separated_values(self):
        from enrich_directory_from_nva import orcid_keyword_labels, split_keyword_label

        self.assertEqual(
            split_keyword_label("Music, Technology, Instruments"),
            ["Music", "Technology", "Instruments"],
        )
        person = {
            "keywords": {
                "keyword": [
                    {"content": "Music, Technology, Instruments, Artificial Intelligence"},
                ]
            }
        }
        self.assertEqual(
            orcid_keyword_labels(person, max_keywords=10),
            ["Music", "Technology", "Instruments", "Artificial Intelligence"],
        )


class NvaDepartmentTests(unittest.TestCase):
    def test_primary_department_prefers_department_over_stab(self):
        from enrich_directory_from_nva import primary_department_from_units

        units = [
            "University of Oslo",
            "Faculty of Humanities",
            "Department of Musicology",
            "IMV stab",
        ]
        self.assertEqual(primary_department_from_units(units), "Department of Musicology")

    def test_primary_department_falls_back_to_faculty(self):
        from enrich_directory_from_nva import primary_department_from_units

        units = ["University of Oslo", "Faculty of Humanities", "IMV stab"]
        self.assertEqual(primary_department_from_units(units), "Faculty of Humanities")

    def test_sanitize_display_text_strips_vertical_tab(self):
        from enrich_directory_from_nva import sanitize_display_text

        self.assertEqual(
            sanitize_display_text("Dødehavsrullene\v– de eldgamle manuskriptene \vog de falske fragmentene"),
            "Dødehavsrullene – de eldgamle manuskriptene og de falske fragmentene",
        )


class NvaContributorTests(unittest.TestCase):
    def test_build_result_contributors_links_directory_people(self):
        from nva_publication_contributors import build_result_contributors

        entity = {
            "contributors": [
                {
                    "identity": {
                        "id": "https://api.nva.unit.no/cristin/person/12345",
                        "name": "Ada Lovelace",
                    }
                },
                {
                    "identity": {
                        "id": "https://api.nva.unit.no/cristin/person/99999",
                        "name": "Unknown Person",
                    }
                },
            ]
        }
        lookup = {
            "12345": {
                "slug": "ada-lovelace",
                "name": "Ada Lovelace",
                "url": "/people/ada-lovelace/",
            }
        }
        contributors = build_result_contributors(entity, lookup)
        self.assertEqual(len(contributors), 2)
        self.assertEqual(contributors[0]["name"], "Ada Lovelace")
        self.assertEqual(contributors[0]["slug"], "ada-lovelace")
        self.assertEqual(contributors[1]["name"], "Unknown Person")
        self.assertNotIn("slug", contributors[1])


if __name__ == "__main__":
    unittest.main()
