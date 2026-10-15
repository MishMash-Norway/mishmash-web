#!/usr/bin/env python3
"""Check that every event's date and end_date carry Oslo's UTC offset for that day.

Jekyll converts an event time to the site's Europe/Oslo time zone, so a
November MeshUp written as 12:00 +02:00 is shown at 11:00. This reads the
front matter of site/_events and reports a time whose offset is not the one
Oslo uses on that date: +02:00 in summer time, +01:00 otherwise.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

EVENTS = Path(__file__).resolve().parent.parent / "site" / "_events"
OSLO = ZoneInfo("Europe/Oslo")
LINE = re.compile(r"^(date|end_date):\s*['\"]?(\d{4}-\d\d-\d\d) (\d\d:\d\d)(?::\d\d)? ([+-]\d\d:\d\d)", re.M)


def expected(day: str, time: str) -> str:
    local = datetime.fromisoformat(f"{day} {time}").replace(tzinfo=OSLO)
    minutes = int(local.utcoffset().total_seconds() // 60)
    return f"{'+' if minutes >= 0 else '-'}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


def problems(name: str, text: str) -> list[str]:
    front = text.split("---", 2)[1] if text.startswith("---") else ""
    return [f"{name}: {field} {day} {time} {offset} should be {expected(day, time)}"
            for field, day, time, offset in LINE.findall(front) if offset != expected(day, time)]


def main() -> int:
    paths = sorted(EVENTS.glob("*.md"))
    found = [line for p in paths for line in problems(p.name, p.read_text(encoding="utf-8"))]
    print(f"event times: {len(paths)} events, {len(found)} with the wrong UTC offset")
    for line in found:
        print(f"  {line}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
