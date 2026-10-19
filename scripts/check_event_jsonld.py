#!/usr/bin/env python3
"""Check that every built event page describes itself as a schema.org Event.

jekyll-seo-tag describes a dated page as a BlogPosting. Event pages replace that
with an Event in site/_layouts/event.html, which search engines can list with its
date, time and place. This reads the built pages in _site/events and reports a
page whose structured data is missing, does not parse, is still a BlogPosting, or
lacks the name, start date or location an Event needs.

Run after `bundle exec jekyll build`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "_site" / "events"
BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
REQUIRED = ("name", "startDate", "location")


def problems(name: str, html: str) -> list[str]:
    try:
        types = [json.loads(b) for b in BLOCK.findall(html)]
    except json.JSONDecodeError as error:
        return [f"{name}: structured data does not parse ({error})"]
    found = []
    if any(t.get("@type") == "BlogPosting" for t in types):
        found.append(f"{name}: still described as a BlogPosting")
    events = [t for t in types if t.get("@type") == "Event"]
    if not events:
        found.append(f"{name}: no schema.org Event")
    for event in events:
        missing = [k for k in REQUIRED if not event.get(k)]
        if missing:
            found.append(f"{name}: the Event lacks {', '.join(missing)}")
    return found


def main() -> int:
    # An event page is one the event layout built: it offers the event for a calendar.
    pages = {p.parent.name: p.read_text(encoding="utf-8") for p in sorted(SITE.glob("*/index.html"))}
    pages = {name: html for name, html in pages.items() if "Add to calendar" in html}
    failing = {name: problems(name, html) for name, html in pages.items()}
    found = [line for lines in failing.values() for line in lines]
    print(f"event structured data: {len(pages)} event pages, "
          f"{sum(1 for lines in failing.values() if not lines)} as Event")
    for line in found:
        print(f"  {line}")
    if not pages:
        print("no event pages found; build the site first", file=sys.stderr)
        return 1
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
