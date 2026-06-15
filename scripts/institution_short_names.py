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

# Official websites for directory institutions (fallback when urls.website is unset in front matter).
DEFAULT_INSTITUTION_WEBSITES: dict[str, str] = {
    "arctic-university-of-norway": "https://en.uit.no/",
    "australian-national-university": "https://www.anu.edu.au/",
    "barratt-due-institute-of-music": "https://www.barrattdue.no/en",
    "bergen-center-for-electronic-arts": "https://bek.no/en/",
    "bi-norwegian-business-school": "https://www.bi.edu/",
    "inland-norway-university-of-applied-sciences": "https://www.inn.no/english/",
    "kristiania-university-college": "https://www.kristiania.no/en/",
    "kulturtanken": "https://www.kulturtanken.no/",
    "motioncomposer-gmbh": "https://motioncomposer.de/en/",
    "national-library-of-norway": "https://www.nb.no/en/",
    "nla-university-college": "https://www.nla.no/en/",
    "nord-university": "https://www.nord.no/en",
    "norsus-norwegian-institute-for-sustainability-research": "https://norsus.no/en/",
    "norwegian-academy-of-music": "https://nmh.no/en/",
    "norwegian-university-of-science-and-technology": "https://www.ntnu.edu/",
    "notam-norwegian-centre-for-technology-art-and-music": "https://notam.no/en/",
    "oslo-national-academy-of-the-arts": "https://khio.no/en",
    "oslo-school-of-architecture-and-design": "https://www.aho.no/english/",
    "ostfold-university-college": "https://www.hiof.no/english/",
    "reimagine": "https://reimagine.no/",
    "screenstory": "https://screenstory.no/",
    "simula-metropolitan-center-for-digital-engineering": "https://www.simulamet.no/",
    "sintef-digital": "https://www.sintef.no/en/",
    "super-ponni": "https://www.superponni.no/",
    "ultima-festival": "https://www.ultima.no/en/",
    "uniarts-helsinki": "https://www.uniarts.fi/en",
    "university-of-agder": "https://www.uia.no/english/index.html",
    "university-of-bergen": "https://www.uib.no/en",
    "university-of-cambridge": "https://www.cam.ac.uk/",
    "university-of-iceland": "https://www.hi.is/en",
    "university-of-manchester": "https://www.manchester.ac.uk/",
    "university-of-melbourne": "https://www.unimelb.edu.au/",
    "university-of-oslo": "https://www.uio.no/english/index.html",
    "university-of-stavanger": "https://www.uis.no/en",
    "western-norway-university-of-applied-sciences": "https://www.hvl.no/en/",
}

# English or Norwegian Wikipedia articles for directory institutions.
DEFAULT_INSTITUTION_WIKIPEDIA: dict[str, str] = {
    "arctic-university-of-norway": "https://en.wikipedia.org/wiki/UiT_The_Arctic_University_of_Norway",
    "australian-national-university": "https://en.wikipedia.org/wiki/Australian_National_University",
    "barratt-due-institute-of-music": "https://en.wikipedia.org/wiki/Barratt_Due_Institute_of_Music",
    "bergen-center-for-electronic-arts": "https://no.wikipedia.org/wiki/Bergen_senter_for_elektronisk_kunst",
    "bi-norwegian-business-school": "https://en.wikipedia.org/wiki/BI_Norwegian_Business_School",
    "inland-norway-university-of-applied-sciences": "https://en.wikipedia.org/wiki/Inland_Norway_University_of_Applied_Sciences",
    "kristiania-university-college": "https://en.wikipedia.org/wiki/Kristiania_University_College",
    "kulturtanken": "https://no.wikipedia.org/wiki/Kulturtanken",
    "national-library-of-norway": "https://en.wikipedia.org/wiki/National_Library_of_Norway",
    "nla-university-college": "https://en.wikipedia.org/wiki/NLA_University_College",
    "nord-university": "https://en.wikipedia.org/wiki/Nord_University",
    "norsus-norwegian-institute-for-sustainability-research": "https://en.wikipedia.org/wiki/NORSUS",
    "norwegian-academy-of-music": "https://en.wikipedia.org/wiki/Norwegian_Academy_of_Music",
    "norwegian-university-of-science-and-technology": "https://en.wikipedia.org/wiki/Norwegian_University_of_Science_and_Technology",
    "oslo-national-academy-of-the-arts": "https://en.wikipedia.org/wiki/Oslo_National_Academy_of_the_Arts",
    "oslo-school-of-architecture-and-design": "https://en.wikipedia.org/wiki/Oslo_School_of_Architecture_and_Design",
    "ostfold-university-college": "https://en.wikipedia.org/wiki/%C3%98stfold_University_College",
    "simula-metropolitan-center-for-digital-engineering": "https://en.wikipedia.org/wiki/Simula_Research_Laboratory",
    "sintef-digital": "https://en.wikipedia.org/wiki/SINTEF",
    "ultima-festival": "https://en.wikipedia.org/wiki/Ultima_Oslo_Contemporary_Music_Festival",
    "uniarts-helsinki": "https://en.wikipedia.org/wiki/Uniarts_Helsinki",
    "university-of-agder": "https://en.wikipedia.org/wiki/University_of_Agder",
    "university-of-bergen": "https://en.wikipedia.org/wiki/University_of_Bergen",
    "university-of-cambridge": "https://en.wikipedia.org/wiki/University_of_Cambridge",
    "university-of-iceland": "https://en.wikipedia.org/wiki/University_of_Iceland",
    "university-of-manchester": "https://en.wikipedia.org/wiki/University_of_Manchester",
    "university-of-melbourne": "https://en.wikipedia.org/wiki/University_of_Melbourne",
    "university-of-oslo": "https://en.wikipedia.org/wiki/University_of_Oslo",
    "university-of-stavanger": "https://en.wikipedia.org/wiki/University_of_Stavanger",
    "western-norway-university-of-applied-sciences": "https://en.wikipedia.org/wiki/Western_Norway_University_of_Applied_Sciences",
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
