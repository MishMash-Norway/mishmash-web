#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from directory_io import (
    apply_jekyll_defaults,
    as_slug_list,
    normalize_institution_slug,
    normalize_person_slug,
)
from sync_directory_reciprocity import migrate_project_fields


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


if __name__ == "__main__":
    unittest.main()
