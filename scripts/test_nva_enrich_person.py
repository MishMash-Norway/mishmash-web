#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from enrich_directory_from_nva import apply_field, enrich_person


class NvaNightlySafetyTests(unittest.TestCase):
    def test_apply_field_skips_empty_values_by_default(self):
        data = {"position": "Professor", "institution": "old-institution"}

        changed = apply_field(data, "position", None)
        changed = apply_field(data, "institution", "", changed=changed)

        self.assertFalse(changed)
        self.assertEqual(data["position"], "Professor")
        self.assertEqual(data["institution"], "old-institution")

    @patch("enrich_directory_from_nva.fetch_nva_bundle")
    def test_enrich_person_preserves_existing_values_when_nva_is_sparse(
        self,
        mock_fetch_nva_bundle,
    ):
        mock_fetch_nva_bundle.return_value = {
            "orcid": "",
            "position": None,
            "department": None,
            "nva_affiliations": [],
            "institution": "",
            "institutions": [],
            "tags": [],
            "summary": None,
            "selected_works": [],
            "other_projects": [],
            "institutional_website": "",
            "image_url": "",
        }

        with tempfile.TemporaryDirectory() as tmp:
            index_md = Path(tmp) / "index.md"
            index_md.write_text(
                "---\n"
                "type: person\n"
                "slug: test-person\n"
                "name: Test Person\n"
                "position: Existing Position\n"
                "institution: existing-institution\n"
                "urls:\n"
                "  nva: https://nva.sikt.no/research-profile/12345\n"
                "  institutional_website: https://example.org/institution\n"
                "---\n",
                encoding="utf-8",
            )

            changed, reason = enrich_person(
                index_md=index_md,
                root=Path(tmp),
                institution_lookup={},
                slug_to_institution_name={},
                org_cache={},
                project_cache={},
                person_lookup={},
                max_tags=10,
                max_works=10,
                dry_run=False,
                discover_nva=False,
                discover_nva_loose=False,
                download_images=False,
            )

            self.assertFalse(changed, reason)
            saved = index_md.read_text(encoding="utf-8")
            self.assertIn("position: Existing Position", saved)
            self.assertIn("institution: existing-institution", saved)
            self.assertIn("institutional_website: https://example.org/institution", saved)
            self.assertNotIn("institutional_website: ''", saved)


if __name__ == "__main__":
    unittest.main()
