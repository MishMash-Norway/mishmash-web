#!/usr/bin/env python3
"""Hold the centre's vocabulary to one form per language.

`site/_data/glossary.yml` is the single record of how MishMash says a thing in
English, Bokmål and Nynorsk. The site reads it three ways: the glossary pages
list it, the inline stretchtext explanations unfold from it, and the Nynorsk
term is what the automatic Nynorsk pages show in place of the Bokmål one. It
also leaves the site as open data at /data/terminology.json, so a partner or a
translator can reuse it.

That only works when every entry carries all three languages and every key is
unique, which is what this checks. It also reports a Nynorsk term that is
identical to the Bokmål one: often correct (Styret, konsortium, medlem), but
worth a glance, so those are listed rather than failed on.

Usage:
  python3 scripts/check_terminology.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

GLOSSARY = SITE_ROOT / "_data" / "glossary.yml"
LANGUAGES = ("en", "nb", "nn")


def problems(entries: list[dict]) -> list[str]:
    found: list[str] = []
    seen: dict[str, int] = {}
    for i, entry in enumerate(entries):
        key = entry.get("key")
        if not key:
            found.append(f"entry {i} has no key")
            continue
        if key in seen:
            found.append(f"{key}: the key appears twice")
        seen[key] = i
        term = entry.get("term") or {}
        for lang in LANGUAGES:
            if not (term.get(lang) or "").strip():
                found.append(f"{key}: no {lang} term")
        standard = entry.get("standard") or {}
        for lang in ("en", "nb"):
            if not (standard.get(lang) or "").strip():
                found.append(f"{key}: no {lang} text at the standard reading level")
    return found


def same_in_both_norwegians(entries: list[dict]) -> list[str]:
    out = []
    for entry in entries:
        term = entry.get("term") or {}
        if term.get("nb") and term.get("nb") == term.get("nn"):
            out.append(f"{entry['key']}: {term['nb']}")
    return out


def main() -> int:
    if not GLOSSARY.exists():
        print(f"no glossary at {GLOSSARY}", file=sys.stderr)
        return 1
    entries = yaml.safe_load(GLOSSARY.read_text(encoding="utf-8")) or []
    found = problems(entries)
    same = same_in_both_norwegians(entries)
    print(f"terminology: {len(entries)} terms in {', '.join(LANGUAGES)}")
    if same:
        print(f"  {len(same)} written the same way in Bokmål and Nynorsk:")
        for line in same:
            print(f"    {line}")
    for line in found:
        print(f"  MISSING: {line}")
    if found:
        print("\nEvery term needs all three languages, so the Nynorsk pages and the open data\n"
              "have something to show. Add the missing one to site/_data/glossary.yml.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
