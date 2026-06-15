#!/usr/bin/env python3
"""Load and suggest institution short names used on the people network and in scripts."""

from __future__ import annotations

import re
from pathlib import Path

from repo_paths import SITE_ROOT

# Suggested defaults for known institutions. Prefer editing short_name in each
# institution's index.md; these are fallbacks for generators and heuristics.
DEFAULT_SHORT_NAMES: dict[str, str] = {
    "arctic-university-of-norway": "UiT",
    "australian-national-university": "ANU",
    "barratt-due-institute-of-music": "Barratt Due",
    "bergen-center-for-electronic-arts": "BEK",
    "bi-norwegian-business-school": "BI",
    "independent-consultant": "Consultant",
    "inland-norway-university-of-applied-sciences": "INN",
    "kristiania-university-college": "Kristiania",
    "kulturtanken": "Kulturtanken",
    "motioncomposer-gmbh": "MotionComposer",
    "national-library-of-norway": "NB",
    "nla-university-college": "NLA",
    "nord-university": "NORD",
    "norsus-norwegian-institute-for-sustainability-research": "NORSUS",
    "norwegian-academy-of-music": "NMH",
    "norwegian-university-of-science-and-technology": "NTNU",
    "notam-norwegian-centre-for-technology-art-and-music": "NOTAM",
    "oslo-national-academy-of-the-arts": "KHiO",
    "oslo-school-of-architecture-and-design": "AHO",
    "ostfold-university-college": "HiØF",
    "reimagine": "Reimagine",
    "screenstory": "Screenstory",
    "simula-metropolitan-center-for-digital-engineering": "Simula",
    "sintef-digital": "SINTEF",
    "super-ponni": "Super Ponni",
    "ultima-festival": "Ultima",
    "uniarts-helsinki": "Uniarts",
    "university-of-agder": "UiA",
    "university-of-bergen": "UiB",
    "university-of-cambridge": "Cambridge",
    "university-of-iceland": "HI",
    "university-of-manchester": "UoM",
    "university-of-melbourne": "UniMelb",
    "university-of-oslo": "UiO",
    "university-of-stavanger": "UiS",
    "western-norway-university-of-applied-sciences": "HVL",
}


def parse_frontmatter_field(text: str, field: str) -> str:
    match = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", text, flags=re.M)
    if not match:
        return ""
    return match.group(1).strip().strip("'\"")


def suggest_short_name(slug: str, name: str = "") -> str:
    if slug in DEFAULT_SHORT_NAMES:
        return DEFAULT_SHORT_NAMES[slug]
    if name:
        words = [w for w in re.split(r"\s+", name.strip()) if w]
        if len(words) >= 2 and all(w[0].isupper() for w in words[:2] if w):
            return "".join(w[0] for w in words[: min(3, len(words))])
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return "Org"
    return "".join(part[:1].upper() + part[1:3] for part in parts[:2])


def load_institution_short_names(directory_root: Path | None = None) -> dict[str, str]:
    root = (directory_root or SITE_ROOT).resolve()
    inst_dir = root / "_directory" / "institutions"
    short_names: dict[str, str] = {}

    if not inst_dir.exists():
        return short_names

    for child in sorted(inst_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        index_md = child / "index.md"
        if not index_md.exists():
            continue
        text = index_md.read_text(encoding="utf-8", errors="ignore")
        slug = parse_frontmatter_field(text, "slug") or child.name
        short_name = parse_frontmatter_field(text, "short_name")
        if short_name:
            short_names[slug] = short_name

    return short_names


def institution_abbrev(slug: str, directory_root: Path | None = None) -> str:
    if not slug:
        return "Org"
    short_names = load_institution_short_names(directory_root)
    if slug in short_names:
        return short_names[slug]
    if slug in DEFAULT_SHORT_NAMES:
        return DEFAULT_SHORT_NAMES[slug]
    return suggest_short_name(slug)
