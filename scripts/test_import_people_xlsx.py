#!/usr/bin/env python3
"""Tests for the XLSX people importer (import_people_xlsx_common.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from openpyxl import Workbook

from directory_io import load_entry, save_entry
from import_people_xlsx_common import (
    apply_person_to_entry,
    build_institution_lookup,
    canonical_orcid_url,
    import_people,
    normalize_http_url,
    normalize_institution_key,
    parse_tags,
    read_people,
    route_social_urls,
    slugify,
)

PARTICIPATION_HEADERS = [
    "$submission_id",
    "Name",
    "Email address",
    "Institution/Organisation",
    "Unit",
    "Current position",
    "Do you want to be added to the MishMash directory?",
    "Web page (personal)",
    "Web page (institutional)",
    "orcid",
    "nva",
    "Keywords describing your competencies relevant for MishMash",
    "Keywords describing your interests in MishMash",
    "Work Package(s) you are interested in joining.WP1: AI for artistic performances",
    "Work Package(s) you are interested in joining.WP2: AI in artistic processes",
    "Work Package(s) you are interested in joining.I don&#39;t know",
    "Which WP(s) does it connect to?.WP6: AI for cultural heritage",
]

TEMPLATE = """---
published: false
type: person
slug: person-slug
permalink: /people/person-slug/
name: Full Name
title: Full Name
position:
department:
institution:
institutions: []
projects: []
wps: []
roles:
- Member
urls:
  personal_website: ''
  institutional_website:
  orcid:
  nva:
aliases: []
tags: []
search_keywords: []
selected_works: []
source_mentions: []
summary:
---

Bio.
"""


def write_xlsx(path: Path, headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def participation_row(name, *, institution="University of Oslo", unit="RITMO", position="Doctoral Fellow",
                      include="Yes", personal="", institutional="", orcid="", nva="",
                      competencies="", interests="", wp1="", wp2="", dont_know="", project_wp6=""):
    return [1, name, "x@example.org", institution, unit, position, include, personal, institutional,
            orcid, nva, competencies, interests, wp1, wp2, dont_know, project_wp6]


class ParticipationSheetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.xlsx = self.root / "form.xlsx"
        self.people = self.root / "people"
        self.institutions = self.root / "institutions"
        self.people.mkdir()
        self.institutions.mkdir()
        self.template = self.people / "_template" / "index.md"
        self.template.parent.mkdir()
        self.template.write_text(TEMPLATE, encoding="utf-8")
        save_entry(
            self._inst_path("university-of-oslo"),
            {"type": "institution", "slug": "university-of-oslo", "name": "University of Oslo",
             "short_name": "UiO", "aliases": ["Universitetet i Oslo"], "people": [], "projects": []},
            "Description.\n",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _inst_path(self, slug):
        path = self.institutions / slug / "index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _run(self, rows, dry_run=False):
        write_xlsx(self.xlsx, PARTICIPATION_HEADERS, rows)
        people, kind = read_people(self.xlsx)
        self.assertEqual(kind, "new")
        return import_people(people, self.template, self.people, self.institutions, dry_run=dry_run)

    def test_only_consenting_rows_are_imported(self):
        created, updated, _ = self._run([
            participation_row("Ada Lovelace", include="Yes"),
            participation_row("Not Asked", include=""),
            participation_row("Said No", include="No"),
        ])
        self.assertEqual((created, updated), (1, 0))
        self.assertTrue((self.people / "ada-lovelace" / "index.md").exists())
        self.assertFalse((self.people / "not-asked").exists())
        self.assertFalse((self.people / "said-no").exists())

    def test_new_entry_gets_profile_fields_and_stays_unpublished(self):
        self._run([participation_row(
            "Ada Lovelace", institution="Universitetet i Oslo", unit="IMV", position="Professor",
            personal="ada.example.org", orcid="0000-0001-2345-6789",
            competencies="Music Information Retrieval; Spatial Audio", interests="creativity, Spatial audio",
            wp1="WP1: AI for artistic performances", dont_know="I don't know", project_wp6="WP6: AI for cultural heritage",
        )])
        data, body = load_entry(self.people / "ada-lovelace" / "index.md")
        self.assertIs(data["published"], False)
        self.assertEqual(data["name"], "Ada Lovelace")
        self.assertEqual(data["permalink"], "/people/ada-lovelace/")
        self.assertEqual(data["position"], "Professor")
        self.assertEqual(data["department"], "IMV")
        self.assertEqual(data["institution"], "university-of-oslo")
        self.assertEqual(data["institutions"], ["university-of-oslo"])
        # WP1 ticked; "I don't know" and the project-idea WP6 column are ignored.
        self.assertEqual(data["wps"], ["WP1"])
        self.assertEqual(data["tags"], ["Music Information Retrieval", "Spatial Audio", "creativity"])
        self.assertEqual(data["search_keywords"], data["tags"])
        self.assertEqual(data["urls"]["orcid"], "https://orcid.org/0000-0001-2345-6789")
        self.assertEqual(data["urls"]["personal_website"], "https://ada.example.org")
        self.assertEqual(body.strip(), "Bio.")

    def test_unresolved_institution_warns_and_leaves_field_empty(self):
        _, _, warnings = self._run([participation_row("Ada Lovelace", institution="Unknown Corp")])
        data, _ = load_entry(self.people / "ada-lovelace" / "index.md")
        self.assertIn(data.get("institution"), (None, ""))
        self.assertTrue(any("unresolved institution 'Unknown Corp'" in w for w in warnings))

    def test_existing_entry_fills_empty_fields_and_merges_wps_only(self):
        existing = self.people / "ada-lovelace" / "index.md"
        existing.parent.mkdir()
        save_entry(existing, {
            "type": "person", "slug": "ada-lovelace", "name": "Ada King Lovelace", "title": "Ada King Lovelace",
            "position": "Countess", "department": "", "institution": "university-of-oslo",
            "institutions": ["university-of-oslo"], "wps": ["WP2", "WP7"], "roles": ["Council Member"],
            "urls": {"orcid": "https://orcid.org/0000-0009-9999-9999", "nva": ""},
            "tags": ["Curated Tag"], "search_keywords": ["Curated Tag"], "published": True,
            "other_projects": [{"title": "Keep me"}],
        }, "Hand-written bio.\n")
        created, updated, warnings = self._run([participation_row(
            "Ada Lovelace", institution="Somewhere Else", unit="New Unit", position="Professor",
            orcid="0000-0001-2345-6789", nva="https://nva.sikt.no/research-profile/42",
            competencies="Ignored, Because, Tags, Exist", wp1="WP1: AI for artistic performances",
        )])
        self.assertEqual((created, updated), (0, 1))
        data, body = load_entry(existing)
        self.assertEqual(data["name"], "Ada King Lovelace")
        self.assertEqual(data["position"], "Countess")
        self.assertEqual(data["department"], "New Unit")
        self.assertEqual(data["institution"], "university-of-oslo")
        self.assertEqual(data["wps"], ["WP1", "WP2", "WP7"])
        self.assertEqual(data["roles"], ["Council Member"])
        self.assertEqual(data["tags"], ["Curated Tag"])
        self.assertEqual(data["urls"]["orcid"], "https://orcid.org/0000-0009-9999-9999")
        self.assertEqual(data["urls"]["nva"], "https://nva.sikt.no/research-profile/42")
        self.assertEqual(data["other_projects"], [{"title": "Keep me"}])
        self.assertIs(data["published"], True)
        self.assertEqual(body.strip(), "Hand-written bio.")
        self.assertTrue(any("kept orcid" in w for w in warnings))
        # Institution is already set, so the unmatched name is not reported.
        self.assertFalse(any("unresolved institution" in w for w in warnings))

    def test_duplicate_website_does_not_blank_stored_url(self):
        existing = self.people / "ada-lovelace" / "index.md"
        existing.parent.mkdir()
        save_entry(existing, {"type": "person", "slug": "ada-lovelace", "name": "Ada Lovelace",
                              "urls": {"personal_website": "https://ada.example.org/",
                                       "institutional_website": "https://www.uio.no/ada"}}, "Bio.\n")
        self._run([participation_row("Ada Lovelace", institutional="ada.example.org")])
        data, _ = load_entry(existing)
        self.assertEqual(data["urls"]["personal_website"], "https://ada.example.org/")
        self.assertEqual(data["urls"]["institutional_website"], "https://www.uio.no/ada")

    def test_dry_run_writes_nothing(self):
        created, _, _ = self._run([participation_row("Ada Lovelace")], dry_run=True)
        self.assertEqual(created, 1)
        self.assertFalse((self.people / "ada-lovelace").exists())

    def test_alias_map_matches_short_name_to_existing_entry(self):
        existing = self.people / "ada-king-lovelace" / "index.md"
        existing.parent.mkdir()
        save_entry(existing, {"type": "person", "slug": "ada-king-lovelace", "name": "Ada King Lovelace",
                              "aliases": ["Ada Lovelace"], "urls": {}}, "Bio.\n")
        created, updated, warnings = self._run([participation_row("Ada Lovelace")])
        self.assertEqual((created, updated), (0, 1))
        self.assertFalse((self.people / "ada-lovelace").exists())
        self.assertTrue(any("via alias" in w for w in warnings))


class DirectoryFormSheetTests(unittest.TestCase):
    def test_existing_member_sheet_reads_wp_columns_and_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            xlsx = Path(tmp) / "directory.xlsx"
            headers = ["$submission_id", "Name", "Email address", "Work package(s).WP1", "Work package(s).WP6",
                       "orcid", "nva", "website (institution)", "website (personal)", "Tags"]
            write_xlsx(xlsx, headers, [[1, "Hilda Deborah", "h@example.org", "", "WP6", "0000-0003-3779-2569",
                                        "https://nva.sikt.no/research-profile/1305503", "https://www.ntnu.no/x",
                                        "https://sites.google.com/x", "imaging, image analysis"]])
            people, kind = read_people(xlsx)
        self.assertEqual(kind, "existing")
        self.assertEqual(len(people), 1)
        person = people[0]
        self.assertEqual(person["profile"]["wps"], ["WP6"])
        self.assertEqual(person["profile"]["tags"], ["imaging", "image analysis"])
        self.assertEqual(person["profile"]["institution_name"], "")
        self.assertEqual(person["urls"]["institutional_website"], "https://www.ntnu.no/x")
        self.assertEqual(person["urls"]["orcid"], "https://orcid.org/0000-0003-3779-2569")


class HelperTests(unittest.TestCase):
    def test_slugify_folds_norwegian_letters(self):
        self.assertEqual(slugify("Marianne Løken"), "marianne-loken")
        self.assertEqual(slugify("Årstein Justnes"), "arstein-justnes")
        self.assertEqual(slugify("Stine S. Skjæret"), "stine-s-skjaeret")

    def test_orcid_without_hyphens(self):
        self.assertEqual(canonical_orcid_url("0009000119291819"), "https://orcid.org/0009-0001-1929-1819")
        self.assertEqual(canonical_orcid_url("https://orcid.org/0000-0002-1825-009X"), "https://orcid.org/0000-0002-1825-009X")

    def test_linkedin_in_website_field_moves_to_linkedin(self):
        urls = {"personal_website": "https://www.linkedin.com/in/ada/", "institutional_website": "https://uio.no/ada"}
        route_social_urls(urls)
        self.assertEqual(urls, {"institutional_website": "https://uio.no/ada", "linkedin": "https://www.linkedin.com/in/ada/"})
        urls = {"personal_website": "https://se.linkedin.com/in/ada", "linkedin": "https://www.linkedin.com/in/ada/"}
        route_social_urls(urls)
        self.assertEqual(urls, {"linkedin": "https://www.linkedin.com/in/ada/"})

    def test_single_slash_scheme_is_repaired(self):
        self.assertEqual(normalize_http_url("https:/www.titanmusic.com"), "https://www.titanmusic.com")
        self.assertEqual(normalize_http_url("http:/example.org"), "https://example.org")
        self.assertEqual(normalize_http_url("example.org/x"), "https://example.org/x")

    def test_parse_tags_dedupes_and_caps(self):
        tags = parse_tags("a, b; c · A", "d\ne", max_tags=4)
        self.assertEqual(tags, ["a", "b", "c", "d"])
        self.assertEqual(len(parse_tags(", ".join(f"t{i}" for i in range(20)))), 6)

    def test_institution_lookup_normalises_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "kth-royal-institute-of-technology" / "index.md"
            path.parent.mkdir()
            save_entry(path, {"slug": "kth-royal-institute-of-technology", "name": "KTH Royal Institute of Technology",
                              "short_name": "KTH", "aliases": ["Royal Institute of Technology"]}, "x\n")
            lookup = build_institution_lookup(root)
        for label in ("KTH", "kth", "Royal Institute of Technology", "KTH Royal Institute of Technology",
                      "kth royal institute of technology"):
            self.assertEqual(lookup.get(normalize_institution_key(label)), "kth-royal-institute-of-technology", label)

    def test_apply_does_not_touch_institution_when_no_name_given(self):
        data = {"slug": "x", "name": "X", "institution": None, "urls": {}}
        out = apply_person_to_entry(data, {"slug": "x", "name": "X", "urls": {}, "profile": {}}, is_new=False)
        self.assertIsNone(out["institution"])


if __name__ == "__main__":
    unittest.main()
