#!/usr/bin/env python3
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE_TAG = re.compile(r"^(?:[A-Za-z]{2,8}|x)(?:-[A-Za-z0-9]{1,8})*$")


def problems(path: Path) -> list[str]:
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    found = []
    for index, entry in enumerate(entries, start=1):
        code = entry.get("lang") if isinstance(entry, dict) else None
        if not isinstance(code, str) or not LANGUAGE_TAG.fullmatch(code):
            found.append(f"{path.name}: record {index} has invalid or missing lang")
    return found


class PartnerContentLanguageTests(unittest.TestCase):
    def test_partner_news_records_have_language_tags(self):
        self.assertEqual(problems(ROOT / "site" / "_data" / "partner_news.yml"), [])

    def test_partner_event_records_have_language_tags(self):
        self.assertEqual(problems(ROOT / "site" / "_data" / "partner_events.yml"), [])


if __name__ == "__main__":
    unittest.main()