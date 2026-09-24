#!/usr/bin/env python3
"""Every picture of a person on an event page must say who it is.

The event layout used to fall back to the event's location for the alternative
text of its picture, so a screen reader announced "Zoom" where the speaker's
name belonged. The UiO web team reported it on 24 September 2026 as a failure of
WCAG 1.1.1, and the fix is `image_alt` in the event's front matter.

This checks that an event whose picture is a portrait carries one, that it is
not simply the location or the title, and that the name is one the site can
stand behind: it must be a person in the directory, or a name the event's own
description or body writes out. Nothing here invents a name.

Usage:
  python3 scripts/check_event_alt.py
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

EVENTS = SITE_ROOT / "_events"
PEOPLE = SITE_ROOT / "_directory" / "people"
NORDIC = str.maketrans({"ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae", "å": "a", "Å": "a"})


def key(value: str) -> str:
    """Compare names without being caught by å/aa, accents or punctuation."""
    value = value.translate(NORDIC)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.replace("'", "").replace("\u2019", "")   # O'Kane and OKane are one name
    return " ".join(re.sub(r"[^a-z]+", " ", value.lower()).replace("aa", "a").split())


def split_front_matter(text: str) -> tuple[dict, str]:
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except yaml.YAMLError:
        return {}, parts[2]


def directory_names() -> set[str]:
    names = set()
    for path in sorted(PEOPLE.glob("*/index.md")):
        front, _ = split_front_matter(path.read_text(encoding="utf-8"))
        if front.get("name"):
            names.add(key(front["name"]))
    return names


def written_names(front: dict, body: str) -> set[str]:
    text = (front.get("description") or "") + " " + body
    found = set(re.findall(r"\[([A-ZÅÆØ][^\]]{2,50})\]\(", body))
    found |= set(re.findall(r"\b([A-ZÅÆØ][\wåæøéèü'.-]+(?: [A-ZÅÆØ][\wåæøéèü'.-]+){1,3})\b", text))
    return {key(n) for n in found}


def problems(events: list[tuple[str, dict, str]], names: set[str]) -> list[str]:
    found = []
    for name, front, body in events:
        image = front.get("image") or ""
        if "/portraits/" not in image:
            continue
        alt = (front.get("image_alt") or "").strip()
        if not alt:
            found.append(f"{name}: a portrait with no image_alt")
            continue
        if key(alt) == key(front.get("location") or "\0"):
            found.append(f"{name}: image_alt repeats the location, {alt!r}")
            continue
        if key(alt) == key(front.get("title") or "\0"):
            found.append(f"{name}: image_alt repeats the title, {alt!r}")
            continue
        if key(alt) not in names and key(alt) not in written_names(front, body):
            found.append(f"{name}: {alt!r} is neither in the directory nor written on the page")
    return found


def main() -> int:
    names = directory_names()
    events = []
    for path in sorted(EVENTS.glob("*.md")):
        front, body = split_front_matter(path.read_text(encoding="utf-8"))
        events.append((path.name, front, body))
    portraits = [e for e in events if "/portraits/" in (e[1].get("image") or "")]
    found = problems(events, names)
    print(f"event pictures: {len(portraits)} portraits across {len(events)} events, "
          f"{len(portraits) - len(found)} named")
    for line in found:
        print(f"  {line}")
    if found:
        print("\nAn event whose picture shows a person needs image_alt in its front matter, and the\n"
              "name has to be the one the directory or the page itself uses.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
