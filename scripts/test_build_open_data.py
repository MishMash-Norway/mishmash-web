#!/usr/bin/env python3
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_open_data as b


def make_site(root: Path):
    (root / "_directory" / "people" / "kari").mkdir(parents=True)
    (root / "_directory" / "people" / "kari" / "index.md").write_text("""---
type: person
slug: kari
name: Kari Nordmann
position: Researcher
institution: university-of-oslo
institutions: [university-of-oslo, nord-university]
wps: [WP1]
roles: [Member]
urls:
  orcid: https://orcid.org/0000-0001-0000-0000
  linkedin: ''
image: /assets/images/portraits/Kari.jpg
---
Bio with a private phone number 12345678.
""", encoding="utf-8")
    (root / "_directory" / "people" / "hidden").mkdir(parents=True)
    (root / "_directory" / "people" / "hidden" / "index.md").write_text("---\ntype: person\nslug: hidden\nname: Hidden\npublished: false\n---\n", encoding="utf-8")
    (root / "_events").mkdir()
    (root / "_events" / "2026-10-01-x.md").write_text("---\ntitle: X\ndate: 2026-10-01 12:00:00 +02:00\nend_date: 2026-10-01 13:00:00 +02:00\nlocation: Zoom\ncategories: [MeshUp]\nslug: x\n---\n", encoding="utf-8")


class RowTests(unittest.TestCase):
    def test_people_professional_fields_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); make_site(root)
            rows = b.people_rows(root)
            self.assertEqual([r["slug"] for r in rows], ["kari"])
            r = rows[0]
            self.assertEqual(r["institutions"], ["university-of-oslo", "nord-university"])
            self.assertEqual(r["identifiers"], {"orcid": "https://orcid.org/0000-0001-0000-0000"})
            self.assertNotIn("image", r)
            self.assertNotIn("bio", r)
            self.assertNotIn("12345678", json.dumps(r))

    def test_events(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); make_site(root)
            rows = b.event_rows(root)
            self.assertEqual(rows[0]["url"], "https://mishmash.no/events/x/")
            self.assertTrue(rows[0]["start"].startswith("2026-10-01"))

    def test_flatten_for_csv(self):
        flat = b.flatten({"slug": "a", "institutions": ["x", "y"], "identifiers": {"orcid": "o"}})
        self.assertEqual(flat, {"slug": "a", "institutions": "x; y", "identifiers_orcid": "o"})

    def test_write_json_and_csv(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); make_site(root)
            b.OUT = root / "data"
            b.write("people", b.people_rows(root))
            data = json.loads((root / "data" / "people.json").read_text(encoding="utf-8"))
            self.assertEqual(data["count"], 1)
            self.assertIn("licence", data)
            with (root / "data" / "people.csv").open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(rows[0]["name"], "Kari Nordmann")


if __name__ == "__main__":
    unittest.main()
