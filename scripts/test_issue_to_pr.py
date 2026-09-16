#!/usr/bin/env python3
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from issue_to_pr import (
    fill_meshup,
    parse_form,
    parse_when,
    render_event,
    render_news,
    render_partner_event,
    slugify,
    tz_offset,
)

NEWS_BODY = """### Headline

Seed project on sustainable AI reports back

### Text

The seed project met in Oslo. Findings will be published in October.

Second paragraph.

### Author

Lina Plataniti

### Images

_No response_

### Rights

- [X] The text and images may be published under the site's CC BY 4.0 licence, or I have stated other terms above.
"""

EVENT_BODY = """### Kind of event

MishMash event

### Title

Workshop: Sound and machines

### Date and time

2026-10-14 17:00 to 19:30 CEST

### Place

Kilden, Kristiansand

### Link to the event page or registration

https://example.org/register

### Description

A hands-on workshop. Bring a laptop.
"""

MESHUP_BODY = """### Speaker

Kari Nordmann, University of Bergen

### Link to your profile page

https://www.uib.no/kari

### Title of the talk

Listening machines

### Abstract

What machines hear.

### Short bio

Kari studies listening.

### Preferred date

_No response_
"""

MESHUP_FILE = """---
title: "MeshUp #30 - Weekly MishMash Gathering"
date: 2026-11-05 12:00:00 +01:00
end_date: 2026-11-05 12:30:00 +01:00
location: Zoom
layout: event
categories: [MeshUp]
description: "Kari Nordmann will give MeshUp #30. Title and abstract coming soon."
slug: "meshup-30"
---

This week, Kari Nordmann will present.

## Access

Zoom links are sent to members.
"""


class ParseTests(unittest.TestCase):
    def test_parse_form_maps_headings_and_blanks(self):
        f = parse_form(NEWS_BODY)
        self.assertEqual(f["Headline"], "Seed project on sustainable AI reports back")
        self.assertEqual(f["Images"], "")
        self.assertTrue(f["Text"].startswith("The seed project met"))

    def test_slugify(self):
        self.assertEqual(slugify("Åpning: Lyd & maskiner på UiO, 2026"), "aapning-lyd-maskiner-paa-uio-2026")

    def test_parse_when(self):
        self.assertEqual(parse_when("2026-10-14 17:00 to 19:30 CEST")[:3], ("2026-10-14", "17:00", "19:30"))
        date, start, end, notes = parse_when("sometime in October")
        self.assertIsNone(date)
        self.assertEqual(len(notes), 3)

    def test_tz_offset(self):
        self.assertEqual(tz_offset("2026-07-01"), "+02:00")
        self.assertEqual(tz_offset("2026-12-01"), "+01:00")


class RenderTests(unittest.TestCase):
    def test_news(self):
        path, content = render_news(parse_form(NEWS_BODY), dt.date(2026, 9, 17))
        self.assertEqual(path.name, "2026-09-17-seed-project-on-sustainable-ai-reports.md")
        self.assertIn('title: "Seed project on sustainable AI reports back"', content)
        self.assertIn('description: "The seed project met in Oslo."', content)
        self.assertIn("layout: page", content)
        self.assertNotIn("CHECK", content)

    def test_event(self):
        path, content = render_event(parse_form(EVENT_BODY), dt.date(2026, 9, 17))
        self.assertEqual(path.name, "2026-10-14-workshop-sound-and-machines.md")
        self.assertIn("date: 2026-10-14 17:00:00 +02:00", content)
        self.assertIn("end_date: 2026-10-14 19:30:00 +02:00", content)
        self.assertIn("[More information and registration](https://example.org/register)", content)

    def test_partner_event(self):
        body = EVENT_BODY.replace("MishMash event", "Partner event")
        path, content = render_partner_event(parse_form(body), dt.date(2026, 9, 17))
        self.assertEqual(path.name, "partner_events.yml")
        self.assertIn("- start_date: 2026-10-14", content)
        self.assertIn("partner: CHECK", content)

    def test_fill_meshup(self):
        out = fill_meshup(MESHUP_FILE, parse_form(MESHUP_BODY))
        self.assertIn('title: "MeshUp #30 - Listening machines"', out)
        self.assertIn('description: "Kari Nordmann presents Listening machines."', out)
        self.assertIn("[Kari Nordmann](https://www.uib.no/kari) will present *Listening machines*", out)
        self.assertIn("## Abstract\nWhat machines hear.", out)
        self.assertIn("## Access", out)


if __name__ == "__main__":
    unittest.main()
