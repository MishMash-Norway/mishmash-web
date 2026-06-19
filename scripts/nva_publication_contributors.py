"""Shared helpers for NVA publication contributor lists."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from directory_io import split_frontmatter

PERSON_PROFILE_RE = re.compile(r"/research-profile/(\d+)")
CRISTIN_RE = re.compile(r"/cristin/person/(\d+)")


def extract_profile_id(url: str) -> str:
    match = PERSON_PROFILE_RE.search(url or "")
    return match.group(1) if match else ""


def extract_cristin_person_id(value: str) -> str | None:
    if not value:
        return None
    match = CRISTIN_RE.search(value)
    return match.group(1) if match else None


def contributor_name(identity: dict) -> str:
    name = (identity.get("name") or "").strip()
    if name:
        return name
    first = (identity.get("firstName") or "").strip()
    last = (identity.get("lastName") or "").strip()
    return f"{first} {last}".strip()


def build_result_contributors(
    entity: dict,
    person_lookup: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    contributors: list[dict[str, str]] = []
    for contributor in entity.get("contributors") or []:
        identity = contributor.get("identity") or {}
        name = contributor_name(identity)
        if not name:
            continue
        entry: dict[str, str] = {"name": name}
        person_id = extract_cristin_person_id(identity.get("id") or "")
        if person_id and person_id in person_lookup:
            person = person_lookup[person_id]
            entry["slug"] = person["slug"]
            entry["url"] = person["url"]
        contributors.append(entry)
    return contributors


def build_person_lookup(root: Path) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    base = root / "_directory" / "people"
    if not base.exists():
        return lookup

    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        index = child / "index.md"
        if not index.exists():
            continue
        try:
            front, _ = split_frontmatter(index.read_text(encoding="utf-8"))
            data = yaml.safe_load(front) or {}
        except Exception:
            continue

        slug = (data.get("slug") or child.name).strip()
        name = (data.get("name") or "").strip()
        urls = data.get("urls") or {}
        if not isinstance(urls, dict):
            urls = {}
        profile_id = extract_profile_id((urls.get("nva") or "").strip())
        if not profile_id or not slug:
            continue

        lookup[profile_id] = {
            "slug": slug,
            "name": name or slug,
            "url": f"/people/{slug}/",
        }

    return lookup
