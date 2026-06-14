#!/usr/bin/env python3
import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from enrich_directory_from_nva import (
    download_nva_portrait,
    names_match_for_discovery,
    normalize_person_name_for_match,
    norwegian_name_search_variants,
)

# Minimal 1x1 PNG
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class NorwegianNameSearchTests(unittest.TestCase):
    def test_variants_add_diacritics_and_surname(self):
        variants = norwegian_name_search_variants("Gro Skaland")
        self.assertIn("Gro Skaland", variants)
        self.assertIn("Skaland", variants)
        self.assertIn("Gro Skåland", variants)
        self.assertIn("Skåland", variants)

    def test_variants_handle_o_to_ø(self):
        variants = norwegian_name_search_variants("Eivind Rossaak")
        self.assertIn("Eivind Røssaak", variants)
        self.assertIn("Røssaak", variants)

    def test_variants_handle_brandsegg_typo(self):
        variants = norwegian_name_search_variants("Oyvind Brandsegg")
        self.assertIn("Brandtsegg", variants)
        self.assertIn("Oyvind Brandtsegg", variants)
        self.assertIn("Øyvind Brandtsegg", variants)

    def test_fuzzy_name_match_allows_one_edit_on_surname(self):
        target = normalize_person_name_for_match("Oyvind Brandsegg")
        candidate = normalize_person_name_for_match("Øyvind Brandtsegg")
        self.assertTrue(names_match_for_discovery(target, candidate))

    def test_fuzzy_name_match_requires_first_name_agreement(self):
        target = normalize_person_name_for_match("Gro Skaland")
        candidate = normalize_person_name_for_match("Ann Kjersti Skaland")
        self.assertFalse(names_match_for_discovery(target, candidate))


class NvaPortraitDownloadTests(unittest.TestCase):
    @patch("enrich_directory_from_nva.requests.get")
    def test_download_nva_portrait_decodes_json_base64(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
            raise_for_status=lambda: None,
            json=lambda: {"base64Data": base64.b64encode(TINY_PNG).decode("ascii")},
        )
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "portrait.png"
            self.assertTrue(download_nva_portrait("https://api.nva.unit.no/cristin/person/1/picture", dest))
            self.assertTrue(dest.with_suffix(".jpg").exists())


if __name__ == "__main__":
    unittest.main()
