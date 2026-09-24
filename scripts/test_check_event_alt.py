#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_event_alt
from check_event_alt import key, problems, written_names

PORTRAIT = "/assets/images/portraits/Anders_Tveit_NMH.jpg"
NAMES = {key("Anders Tveit")}


def event(**front):
    base = {"title": "MeshUp #8", "location": "Zoom", "image": PORTRAIT}
    base.update(front)
    return [("meshup08.md", base, "A talk by someone.")]


class EventAltTests(unittest.TestCase):
    def test_a_named_portrait_passes(self):
        self.assertEqual(problems(event(image_alt="Anders Tveit"), NAMES), [])

    def test_a_portrait_without_alt_is_reported(self):
        self.assertEqual(problems(event(), NAMES), ["meshup08.md: a portrait with no image_alt"])

    def test_the_location_as_alt_is_reported(self):
        found = problems(event(image_alt="Zoom"), NAMES)
        self.assertEqual(len(found), 1)
        self.assertIn("repeats the location", found[0])

    def test_the_title_as_alt_is_reported(self):
        found = problems(event(image_alt="MeshUp #8"), NAMES)
        self.assertIn("repeats the title", found[0])

    def test_an_unknown_name_is_reported(self):
        found = problems(event(image_alt="Someone Else"), NAMES)
        self.assertIn("neither in the directory nor written on the page", found[0])

    def test_a_name_the_page_writes_is_accepted(self):
        events = [("wp1.md", {"title": "Webinar", "location": "Zoom", "image": PORTRAIT,
                              "image_alt": "Etienne Guichard",
                              "description": "Etienne Guichard presents."}, "body")]
        self.assertEqual(problems(events, set()), [])

    def test_an_event_without_a_portrait_is_left_alone(self):
        events = [("x.md", {"title": "X", "image": "/assets/images/bubbles/thumbs/bubbles-1.svg"}, "")]
        self.assertEqual(problems(events, set()), [])

    def test_names_compare_across_spelling(self):
        self.assertEqual(key("Pål Halvorsen"), key("Paal Halvorsen"))
        self.assertEqual(key("Eamon O'Kane"), key("Eamon OKane"))
        self.assertEqual(key("Olav Renolen Aasbø"), key("Olav Renolen Aasbo"))

    def test_written_names_reads_links_and_running_text(self):
        found = written_names({"description": "Fride H. Klykken explores trust."},
                              "[Eamon O'Kane](https://example.org) presents.")
        self.assertIn(key("Fride H. Klykken"), found)
        self.assertIn(key("Eamon O'Kane"), found)

    def test_the_site_events_all_name_their_portraits(self):
        if not check_event_alt.EVENTS.exists():
            self.skipTest("events not present")
        names = check_event_alt.directory_names()
        events = []
        for path in sorted(check_event_alt.EVENTS.glob("*.md")):
            front, body = check_event_alt.split_front_matter(path.read_text(encoding="utf-8"))
            events.append((path.name, front, body))
        self.assertEqual(problems(events, names), [])


if __name__ == "__main__":
    unittest.main()
