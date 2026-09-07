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

    @patch("enrich_directory_from_nva.fetch_orcid_bundle")
    @patch("enrich_directory_from_nva.fetch_nva_bundle", side_effect=RuntimeError("401 Client Error"))
    def test_failed_nva_fetch_never_falls_back_to_orcid(self, mock_nva, mock_orcid):
        mock_orcid.return_value = {"position": "ORCID Title", "tags": ["orcid tag"], "institutions": []}
        with tempfile.TemporaryDirectory() as tmp:
            index_md = Path(tmp) / "index.md"
            original = (
                "---\n"
                "type: person\n"
                "slug: test-person\n"
                "name: Test Person\n"
                "position: NVA Position\n"
                "tags:\n- nva tag\n"
                "urls:\n"
                "  nva: https://nva.sikt.no/research-profile/12345\n"
                "  orcid: https://orcid.org/0000-0001-2345-6789\n"
                "---\n"
            )
            index_md.write_text(original, encoding="utf-8")
            changed, reason = enrich_person(
                index_md=index_md, root=Path(tmp), institution_lookup={}, slug_to_institution_name={},
                org_cache={}, project_cache={}, person_lookup={}, max_tags=10, max_works=10,
                dry_run=False, discover_nva=False, discover_nva_loose=False, download_images=False,
            )
            self.assertFalse(changed)
            self.assertIn("nva fetch failed", reason)
            mock_orcid.assert_not_called()
            self.assertEqual(index_md.read_text(encoding="utf-8"), original)

    def test_get_json_refreshes_token_on_401(self):
        import enrich_directory_from_nva as mod

        class Resp:
            def __init__(self, status):
                self.status_code = status
            def raise_for_status(self):
                if self.status_code >= 400:
                    raise RuntimeError(f"{self.status_code}")
            def json(self):
                return {"ok": True}

        calls = []
        def fake_get(url, headers=None, timeout=None):
            calls.append(dict(headers or {}))
            return Resp(401) if len(calls) == 1 else Resp(200)

        mod._nva_request_headers.clear()
        mod._nva_request_headers["Authorization"] = "Bearer old"
        try:
            with patch.object(mod.requests, "get", side_effect=fake_get), \
                 patch.object(mod, "resolve_nva_access_token", return_value="new"):
                self.assertEqual(mod.get_json("https://api.nva.unit.no/x"), {"ok": True})
        finally:
            mod._nva_request_headers.clear()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["Authorization"], "Bearer old")
        self.assertEqual(calls[1]["Authorization"], "Bearer new")


if __name__ == "__main__":
    unittest.main()
