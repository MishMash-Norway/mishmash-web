#!/usr/bin/env python3
import unittest

from enrich_directory_from_nva import (
    names_match_for_discovery,
    normalize_person_name_for_match,
    norwegian_name_search_variants,
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


if __name__ == "__main__":
    unittest.main()
