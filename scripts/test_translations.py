#!/usr/bin/env python3
"""The UI strings must not have gaps.

The Nynorsk strings are generated from the Bokmål section, and every template
reads a key by name, so a key present in one language and missing in another
renders as an empty label: a menu item with a link and no text, which fails
the accessibility check. This test asserts that the language sections hold
the same keys, and that no value is empty.
"""
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

TRANSLATIONS = SITE_ROOT / "_data" / "translations.yml"


class Tests(unittest.TestCase):
    def setUp(self):
        self.data = yaml.safe_load(TRANSLATIONS.read_text(encoding="utf-8"))

    def test_same_keys_in_every_language(self):
        sections = {k: set(v) for k, v in self.data.items() if isinstance(v, dict)}
        self.assertIn("en", sections)
        self.assertIn("nb", sections)
        reference = sections["en"]
        for lang, keys in sections.items():
            missing = reference - keys
            extra = keys - reference
            self.assertFalse(missing, f"{lang} is missing: {sorted(missing)}")
            self.assertFalse(extra, f"{lang} has keys English lacks: {sorted(extra)}")

    def test_no_empty_values(self):
        for lang, section in self.data.items():
            if not isinstance(section, dict):
                continue
            empty = [k for k, v in section.items() if isinstance(v, str) and not v.strip()]
            self.assertFalse(empty, f"{lang} has empty strings: {empty}")


if __name__ == "__main__":
    unittest.main()
