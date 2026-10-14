#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_event_jsonld import problems


def page(*blocks):
    return "".join(f'<script type="application/ld+json">{b}</script>' for b in blocks)


EVENT = '{"@type": "Event", "name": "MeshUp", "startDate": "2026-10-22T12:00:00+02:00", "location": {"@type": "VirtualLocation"}}'


class EventJsonLdTests(unittest.TestCase):
    def test_an_event_passes(self):
        self.assertEqual(problems("m", page(EVENT)), [])

    def test_a_blog_posting_is_reported(self):
        found = problems("m", page(EVENT, '{"@type": "BlogPosting"}'))
        self.assertIn("still described as a BlogPosting", found[0])

    def test_a_page_without_an_event_is_reported(self):
        self.assertEqual(problems("m", page()), ["m: no schema.org Event"])

    def test_a_missing_start_date_is_reported(self):
        found = problems("m", page('{"@type": "Event", "name": "M", "location": "Zoom"}'))
        self.assertEqual(found, ["m: the Event lacks startDate"])

    def test_broken_json_is_reported(self):
        self.assertIn("does not parse", problems("m", page('{"@type": "Event",}'))[0])


if __name__ == "__main__":
    unittest.main()
