"""Shared helpers for NVA publication contributor lists."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from directory_io import split_frontmatter

PERSON_PROFILE_RE = re.compile(r"/research-profile/(\d+)")
CRISTIN_RE = re.compile(r"/cristin/person/(\d+)")

THESIS_INSTANCE_TYPES = frozenset(
    {"DegreePhd", "DegreeMaster", "DegreeBachelor", "DegreeLicentiate"}
)
DEFAULT_AUTHOR_ROLES = frozenset({"Creator", "Author"})
SUPERVISOR_ROLES = frozenset({"Supervisor"})


def extract_profile_id(url: str) -> str:
    match = PERSON_PROFILE_RE.search(url or "")
    return match.group(1) if match else ""


def extract_cristin_person_id(value: str) -> str | None:
    if not value:
        return None
    match = CRISTIN_RE.search(value)
    return match.group(1) if match else None


def _localized_label(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                text = (item.get("value") or item.get("en") or item.get("nb") or "").strip()
                if text:
                    return text
            elif isinstance(item, str) and item.strip():
                return item.strip()
    if isinstance(value, dict):
        return (value.get("en") or value.get("nb") or value.get("no") or value.get("value") or "").strip()
    return ""


def contributor_name(identity: dict) -> str:
    name = _localized_label(identity.get("name"))
    if name:
        return name
    first = _localized_label(identity.get("firstName"))
    last = _localized_label(identity.get("lastName"))
    return f"{first} {last}".strip()


def contributor_role(contributor: dict) -> str:
    return ((contributor.get("role") or {}).get("type") or "").strip()


def contributor_roles_for_instance(instance_type: str) -> frozenset[str]:
    roles = set(DEFAULT_AUTHOR_ROLES)
    if (instance_type or "").strip() in THESIS_INSTANCE_TYPES:
        roles |= SUPERVISOR_ROLES
    return frozenset(roles)


def person_contributor_role(entity: dict, profile_id: str) -> str:
    profile_id = str(profile_id or "").strip()
    if not profile_id:
        return ""
    for contributor in entity.get("contributors") or []:
        identity = contributor.get("identity") or {}
        person_id = extract_cristin_person_id(identity.get("id") or "")
        if person_id == profile_id:
            return contributor_role(contributor)
    return ""


def person_has_supervisor_role(entity: dict, profile_id: str) -> bool:
    return person_contributor_role(entity, profile_id) == "Supervisor"


def build_result_contributors(
    entity: dict,
    person_lookup: dict[str, dict[str, str]],
    allowed_roles: frozenset[str] | None = None,
) -> list[dict[str, str]]:
    contributors: list[dict[str, str]] = []
    for contributor in entity.get("contributors") or []:
        role = contributor_role(contributor)
        if allowed_roles is not None and role and role not in allowed_roles:
            continue
        identity = contributor.get("identity") or {}
        name = contributor_name(identity)
        if not name:
            continue
        entry: dict[str, str] = {"name": name}
        if role:
            entry["role"] = role
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
