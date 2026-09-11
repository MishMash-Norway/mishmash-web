#!/usr/bin/env python3
"""Guest/visiting affiliations from NVA are not real affiliations and are ignored."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from enrich_directory_from_nva import enrich_person, is_guest_affiliation, split_guest_affiliations


def _run(index_md: Path, tmp: str):
    return enrich_person(
        index_md=index_md, root=Path(tmp), institution_lookup={}, slug_to_institution_name={},
        org_cache={}, project_cache={}, person_lookup={}, max_tags=10, max_works=10,
        dry_run=False, discover_nva=False, discover_nva_loose=False, download_images=False,
    )


def _bundle(**overrides):
    bundle = {
        "orcid": "", "position": "", "department": "", "nva_affiliations": [],
        "institution": "", "institutions": [], "guest_institutions": [], "tags": [],
        "summary": None, "selected_works": [], "other_projects": [],
        "institutional_website": "", "image_url": "",
    }
    bundle.update(overrides)
    return bundle


class GuestAffiliationTests(unittest.TestCase):
    def test_is_guest_affiliation_matches_guest_and_visiting_roles(self):
        for role in ("Guest", "Guest researcher", "Gjesteforsker", "Visiting professor", "gjest"):
            self.assertTrue(is_guest_affiliation({"role": role}), role)
        for role in ("Professor", "Associate professor", "Research fellow", ""):
            self.assertFalse(is_guest_affiliation({"role": role}), role)

    def test_split_guest_affiliations(self):
        guest = {"role": "Guest", "institutions": ["university-of-oslo"]}
        real = {"role": "Associate professor", "institutions": ["university-of-inland-norway"]}
        kept, guests = split_guest_affiliations([guest, real])
        self.assertEqual(kept, [real])
        self.assertEqual(guests, [guest])

    @patch("enrich_directory_from_nva.fetch_nva_bundle")
    def test_guest_affiliation_is_dropped_when_a_real_one_exists(self, mock_fetch):
        mock_fetch.return_value = _bundle(
            position="Associate professor", department="Department of English",
            institution="university-of-inland-norway", institutions=["university-of-inland-norway"],
            guest_institutions=["university-of-oslo"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            index_md = Path(tmp) / "index.md"
            index_md.write_text(
                "---\ntype: person\nslug: ida\nname: Ida\n"
                "position: Guest\ndepartment: Department of Musicology\n"
                "institution: university-of-oslo\n"
                "institutions:\n- university-of-inland-norway\n- university-of-oslo\n"
                "nva_affiliations:\n"
                "- role: Guest\n  unit: Department of Musicology\n  institution: university-of-oslo\n"
                "- role: Associate professor\n  unit: Department of English\n  institution: university-of-inland-norway\n"
                "urls:\n  nva: https://nva.sikt.no/research-profile/1\n---\n",
                encoding="utf-8",
            )
            changed, reason = _run(index_md, tmp)
            self.assertTrue(changed, reason)
            saved = index_md.read_text(encoding="utf-8")
            self.assertIn("position: Associate professor", saved)
            self.assertIn("department: Department of English", saved)
            self.assertIn("institution: university-of-inland-norway", saved)
            self.assertNotIn("university-of-oslo", saved)
            self.assertNotIn("role: Guest", saved)

    @patch("enrich_directory_from_nva.fetch_nva_bundle")
    def test_guest_only_person_loses_the_guest_position_and_institution(self, mock_fetch):
        mock_fetch.return_value = _bundle(guest_institutions=["university-of-oslo"])
        with tempfile.TemporaryDirectory() as tmp:
            index_md = Path(tmp) / "index.md"
            index_md.write_text(
                "---\ntype: person\nslug: dana\nname: Dana\n"
                "position: Guest\ndepartment: Department of Musicology\n"
                "institution: university-of-oslo\ninstitutions:\n- university-of-oslo\n"
                "urls:\n  nva: https://nva.sikt.no/research-profile/2\n---\n",
                encoding="utf-8",
            )
            changed, reason = _run(index_md, tmp)
            self.assertTrue(changed, reason)
            saved = index_md.read_text(encoding="utf-8")
            self.assertIn("position: ''", saved)
            self.assertIn("department: ''", saved)
            self.assertIn("institution: ''", saved)
            self.assertIn("institutions: []", saved)

    @patch("enrich_directory_from_nva.fetch_nva_bundle")
    def test_guest_institution_is_kept_when_the_person_is_also_really_employed_there(self, mock_fetch):
        mock_fetch.return_value = _bundle(
            position="Professor", department="Department of Musicology",
            institution="university-of-oslo", institutions=["university-of-oslo"],
            guest_institutions=["university-of-oslo"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            index_md = Path(tmp) / "index.md"
            index_md.write_text(
                "---\ntype: person\nslug: p\nname: P\nposition: Guest\n"
                "institution: university-of-oslo\ninstitutions:\n- university-of-oslo\n"
                "urls:\n  nva: https://nva.sikt.no/research-profile/3\n---\n",
                encoding="utf-8",
            )
            _run(index_md, tmp)
            saved = index_md.read_text(encoding="utf-8")
            self.assertIn("position: Professor", saved)
            self.assertIn("institution: university-of-oslo", saved)
            self.assertIn("- university-of-oslo", saved)

    @patch("enrich_directory_from_nva.fetch_nva_bundle")
    def test_person_is_removed_from_the_guest_institution_people_list(self, mock_fetch):
        mock_fetch.return_value = _bundle(guest_institutions=["university-of-oslo"])
        with tempfile.TemporaryDirectory() as tmp:
            inst_md = Path(tmp) / "_directory" / "institutions" / "university-of-oslo" / "index.md"
            inst_md.parent.mkdir(parents=True)
            inst_md.write_text(
                "---\ntype: institution\nslug: university-of-oslo\nname: UiO\n"
                "people:\n- alice\n- dana\n---\n\nBody text.\n",
                encoding="utf-8",
            )
            index_md = Path(tmp) / "index.md"
            index_md.write_text(
                "---\ntype: person\nslug: dana\nname: Dana\nposition: Guest\n"
                "institution: university-of-oslo\ninstitutions:\n- university-of-oslo\n"
                "urls:\n  nva: https://nva.sikt.no/research-profile/2\n---\n",
                encoding="utf-8",
            )
            _run(index_md, tmp)
            saved = inst_md.read_text(encoding="utf-8")
            self.assertIn("- alice", saved)
            self.assertNotIn("- dana", saved)
            self.assertIn("Body text.", saved)


if __name__ == "__main__":
    unittest.main()
