#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_event_offsets import expected, problems


def event(date):
    return f"---\ntitle: X\ndate: {date}\n---\nbody"


class EventOffsetTests(unittest.TestCase):
    def test_summer_and_winter_offsets(self):
        self.assertEqual(expected("2026-10-22", "12:00"), "+02:00")
        self.assertEqual(expected("2026-11-05", "12:00"), "+01:00")
        self.assertEqual(expected("2026-10-25", "12:00"), "+01:00")   # the day summer time ends

    def test_a_right_offset_passes(self):
        self.assertEqual(problems("m.md", event("2026-11-05 12:00:00 +01:00")), [])

    def test_a_summer_offset_in_november_is_reported(self):
        found = problems("m.md", event("2026-11-05 12:00:00 +02:00"))
        self.assertEqual(found, ["m.md: date 2026-11-05 12:00 +02:00 should be +01:00"])


if __name__ == "__main__":
    unittest.main()
