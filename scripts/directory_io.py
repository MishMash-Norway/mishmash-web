#!/usr/bin/env python3
"""Shared helpers for reading and writing directory collection entries."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from repo_paths import SITE_ROOT

PERSON_PATH_RE = re.compile(r"/people/([\w-]+)/?")
INSTITUTION_PATH_RE = re.compile(r"/institutions/([\w-]+)/?")

JEKYLL_DEFAULTS = {
    "people": {"layout": "person"},
    "institutions": {"layout": "page"},
    "projects": {"layout": "page", "type": "project"},
}

LISTING_PAGE_SLUGS = {"index"}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("Missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Missing frontmatter end")
    return text[4:end], text[end + 5 :]


def load_entry(index_md: Path) -> tuple[dict, str]:
    text = index_md.read_text(encoding="utf-8")
    front, body = split_frontmatter(text)
    data = yaml.safe_load(front) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Frontmatter must be a mapping: {index_md}")
    return data, body


def save_entry(index_md: Path, data: dict, body: str) -> None:
    dumped = yaml.dump(data, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper).strip()
    index_md.write_text(f"---\n{dumped}\n---\n\n{body.lstrip()}", encoding="utf-8")


def slug_list_uses_path_refs(value) -> bool:
    items = value if isinstance(value, list) else []
    for item in items:
        if not isinstance(item, str):
            continue
        if "/people/" in item or "/institutions/" in item:
            return True
    return False


def as_slug_list(value) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str) and value.strip():
        items = [value]
    else:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            continue
        slug = normalize_person_slug(item) or normalize_institution_slug(item)
        if slug and slug not in seen:
            seen.add(slug)
            out.append(slug)
    return out


def normalize_person_slug(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    match = PERSON_PATH_RE.search(value)
    if match:
        return match.group(1)
    return value.strip("/")


def normalize_institution_slug(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    match = INSTITUTION_PATH_RE.search(value)
    if match:
        return match.group(1)
    return value.strip("/")


def extract_person_slugs(text: str) -> list[str]:
    return list(dict.fromkeys(PERSON_PATH_RE.findall(text or "")))


def extract_institution_slugs(text: str) -> list[str]:
    return list(dict.fromkeys(INSTITUTION_PATH_RE.findall(text or "")))


def apply_jekyll_defaults(data: dict, section: str, folder_name: str) -> dict:
    merged = {**JEKYLL_DEFAULTS.get(section, {}), **data}
    if not str(merged.get("slug", "")).strip():
        merged["slug"] = folder_name
    if section == "projects" and not str(merged.get("name", "")).strip():
        merged["name"] = str(merged.get("title", "")).strip() or folder_name
    return merged


def iter_directory_entries(root: Path | None = None):
    """Yield (section, folder_name, index_md, data, body) for directory collection entries."""
    site_root = (root or SITE_ROOT).resolve()
    directory_root = site_root / "_directory"
    for section in ("people", "institutions", "projects"):
        section_dir = directory_root / section
        if not section_dir.exists():
            continue
        for child in sorted(section_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue
            if child.name in LISTING_PAGE_SLUGS:
                continue
            index_md = child / "index.md"
            if not index_md.exists():
                continue
            data, body = load_entry(index_md)
            data = apply_jekyll_defaults(data, section, child.name)
            yield section, child.name, index_md, data, body
