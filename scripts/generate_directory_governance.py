#!/usr/bin/env python3
import argparse
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path

WP_LEADERS_FILE = "about/organisation/wp-leaders/index.md"
BOARD_FILE = "about/organisation/board/index.md"
COUNCIL_FILE = "about/organisation/council/index.md"
PORTRAITS_CIRCLE_DIR = "assets/images/portraits/circle"

INSTITUTION_CANONICAL = {
    "uio": "University of Oslo",
    "uib": "University of Bergen",
    "uia": "University of Agder",
    "nmh": "Norwegian Academy of Music",
    "hiof": "Ostfold University College",
    "hiø": "Ostfold University College",
    "inn": "Inland Norway University of Applied Sciences",
    "kristiania": "Kristiania University College",
    "ntnu": "Norwegian University of Science and Technology",
    "bi": "BI Norwegian Business School",
    "uit": "Arctic University of Norway",
    "nb": "National Library of Norway",
    "simulamet": "Simula Metropolitan Center for Digital Engineering",
    "aho": "Oslo School of Architecture and Design",
    "notam": "Notam - Norwegian Centre for Technology, Art and Music",
    "notam - norwegian centre for technology, art and music": "Notam - Norwegian Centre for Technology, Art and Music",
    "notam – norwegian centre for technology, art and music": "Notam - Norwegian Centre for Technology, Art and Music",
    "reimagine": "Reimagine",
    "western norway university of applied sciences": "Western Norway University of Applied Sciences",
    "australian national university": "Australian National University",
    "norsus – norwegian institute for sustainability research": "NORSUS - Norwegian Institute for Sustainability Research",
    "norsus - norwegian institute for sustainability research": "NORSUS - Norwegian Institute for Sustainability Research",
    "oslo national academy of the arts": "Oslo National Academy of the Arts",
    "simula metropolitan center for digital engineering": "Simula Metropolitan Center for Digital Engineering",
    "østfold university college": "Ostfold University College",
}


def ascii_fold(value: str) -> str:
    replacements = {
        "æ": "ae",
        "Æ": "Ae",
        "ø": "o",
        "Ø": "O",
        "å": "a",
        "Å": "A",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def slugify(value: str) -> str:
    value = ascii_fold(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value.strip("-")


def normalize_institution(name: str) -> str:
    key = name.strip()
    key_low = key.lower()
    return INSTITUTION_CANONICAL.get(key_low, key)


def person_key(value: str) -> str:
    value = ascii_fold(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower().replace("-", " ").replace("_", " ")
    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def compact_key(value: str) -> str:
    return value.replace(" ", "")


def build_portrait_lookup(root: Path) -> dict[str, str]:
    portrait_dir = root / PORTRAITS_CIRCLE_DIR
    lookup: dict[str, str] = {}
    if not portrait_dir.exists():
        return lookup

    for img in sorted(portrait_dir.iterdir()):
        if img.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        stem = img.stem
        stem_no_affiliation = re.sub(r"_[A-Za-z0-9]+$", "", stem)
        for candidate in (stem, stem_no_affiliation):
            key = person_key(candidate)
            if key and key not in lookup:
                lookup[key] = f"/{PORTRAITS_CIRCLE_DIR}/{img.name}"
    return lookup


def resolve_person_image(name: str, slug: str, portrait_lookup: dict[str, str]) -> str:
    name_key = person_key(name)
    slug_key = person_key(slug)
    if name_key in portrait_lookup:
        return portrait_lookup[name_key]
    if slug_key in portrait_lookup:
        return portrait_lookup[slug_key]

    compact_name = compact_key(name_key)
    compact_slug = compact_key(slug_key)
    for key, path in portrait_lookup.items():
        ckey = compact_key(key)
        if ckey == compact_name or ckey == compact_slug:
            return path

    name_tokens = set(name_key.split())
    for key, path in portrait_lookup.items():
        key_tokens = set(key.split())
        # Loose fallback: at least first+last name tokens overlap with portrait stem.
        if len(name_tokens & key_tokens) >= 2:
            return path

    return f"/images/people/{slug}.jpg"


def add_person(persons: dict, name: str, url: str, institution: str, role: str, source: str):
    person = persons[name]
    person["name"] = name
    if url and not person.get("url"):
        person["url"] = url
    if institution:
        person["institutions"].add(normalize_institution(institution))
    if role:
        person["roles"].add(role)
    person["sources"].add(source)


def parse_wp_leaders(path: Path, persons: dict):
    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)\s*\(([^)]+)\)")
    for name, url, institution in pattern.findall(text):
        clean_name = name.strip()
        if clean_name.startswith("WP"):
            continue
        add_person(
            persons,
            clean_name,
            url.strip(),
            institution.strip(),
            "Work Package Leader Group member",
            str(path),
        )


def parse_board(path: Path, persons: dict):
    text = path.read_text(encoding="utf-8", errors="ignore")
    row_pattern = re.compile(r"<div class=\"board-member-row\">(.*?)</div>", re.S)
    member_pattern = re.compile(
        r"<a href=\"([^\"]+)\">([^<]+)</a><br>\s*([^<]+)<br>\s*([^<\n]+)",
        re.S,
    )

    for row in row_pattern.findall(text):
        m = member_pattern.search(row)
        if not m:
            continue
        url = m.group(1).strip()
        name = m.group(2).strip()
        institution = m.group(3).strip()
        role = m.group(4).strip()
        add_person(persons, name, url, institution, f"Board {role}", str(path))


def parse_council(path: Path, persons: dict):
    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(
        r"^\s*-\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*\(([^)]+)\)\s*$",
        re.M,
    )
    for name, url, institution in pattern.findall(text):
        add_person(
            persons,
            name.strip(),
            url.strip(),
            institution.strip(),
            "Council member",
            str(path),
        )


def ensure_templates(root: Path):
    templates = [
        root / "_directory" / "people" / "_template" / "index.md",
        root / "_directory" / "institutions" / "_template" / "index.md",
    ]
    for p in templates:
        if not p.exists():
            raise RuntimeError(f"Missing template file: {p}")


def reset_dirs(root: Path):
    for section in ("people", "institutions"):
        base = root / "_directory" / section
        if not base.exists():
            continue
        for child in base.iterdir():
            if child.name == "_template":
                continue
            if child.is_dir():
                shutil.rmtree(child)


def render_person(name: str, slug: str, person: dict, institution_slugs: list[str], image_path: str) -> str:
    roles = sorted(person["roles"])
    sources = sorted(person["sources"])
    source_block = "\n".join([f"  - {s}" for s in sources]) if sources else "  -"
    role_block = "\n".join([f"  - {r}" for r in roles]) if roles else "  -"
    inst_block = "\n".join([f"  - {s}" for s in institution_slugs]) if institution_slugs else "  -"
    position = roles[0] if roles else ""
    institution = institution_slugs[0] if institution_slugs else ""
    website = person.get("url", "")
    return f"""---
type: person
slug: {slug}
name: {name}
title: {name}
position: {position}
image: {image_path}
institution: {institution}
institutions:
{inst_block}
projects: []
roles:
{role_block}
urls:
  website: {website}
  github:
  linkedin:
  orcid:
  nva:
  youtube:
  facebook:
  mastodon:
  instagram:
aliases: []
tags: []
search_keywords: []
source_mentions:
{source_block}
summary:
---

# {name}

"""


def render_institution(name: str, slug: str, people_slugs: list[str], sources: list[str]) -> str:
    source_block = "\n".join([f"  - {s}" for s in sorted(set(sources))]) if sources else "  -"
    people_block = "\n".join([f"  - {p}" for p in sorted(set(people_slugs))]) if people_slugs else "  -"
    return f"""---
type: institution
slug: {slug}
name: {name}
image: /images/institutions/{slug}.png
people:
{people_block}
projects: []
country:
city:
urls:
  website:
  wikipedia:
aliases: []
tags: []
search_keywords: []
source_mentions:
{source_block}
summary:
---

# {name}

"""


def write_directory(root: Path, persons: dict):
    people_base = root / "_directory" / "people"
    institutions_base = root / "_directory" / "institutions"

    institution_to_people = defaultdict(set)
    institution_sources = defaultdict(list)

    for name, data in persons.items():
        for inst in data["institutions"]:
            institution_to_people[inst].add(name)
            institution_sources[inst].extend(data["sources"])

    person_name_to_slug = {name: slugify(name) for name in persons.keys()}
    institution_name_to_slug = {name: slugify(name) for name in institution_to_people.keys()}
    portrait_lookup = build_portrait_lookup(root)

    for name, data in sorted(persons.items(), key=lambda x: x[0].lower()):
        person_slug = person_name_to_slug[name]
        inst_slugs = [institution_name_to_slug[inst] for inst in sorted(data["institutions"]) if inst in institution_name_to_slug]
        image_path = resolve_person_image(name, person_slug, portrait_lookup)
        out = people_base / person_slug / "index.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_person(name, person_slug, data, inst_slugs, image_path), encoding="utf-8")

    for institution_name, people_names in sorted(institution_to_people.items(), key=lambda x: x[0].lower()):
        institution_slug = institution_name_to_slug[institution_name]
        people_slugs = [person_name_to_slug[p] for p in sorted(people_names)]
        out = institutions_base / institution_slug / "index.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            render_institution(institution_name, institution_slug, people_slugs, institution_sources[institution_name]),
            encoding="utf-8",
        )

    return len(persons), len(institution_to_people)


def main():
    parser = argparse.ArgumentParser(description="Generate people and institutions from WP leaders, board, and council.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--reset", action="store_true", help="Remove existing people/institutions entries before writing")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ensure_templates(root)

    persons = defaultdict(lambda: {
        "name": "",
        "url": "",
        "institutions": set(),
        "roles": set(),
        "sources": set(),
    })

    parse_wp_leaders(root / WP_LEADERS_FILE, persons)
    parse_board(root / BOARD_FILE, persons)
    parse_council(root / COUNCIL_FILE, persons)

    if args.reset:
        reset_dirs(root)

    people_count, institution_count = write_directory(root, persons)
    print(f"Created people: {people_count}")
    print(f"Created institutions: {institution_count}")


if __name__ == "__main__":
    main()
