#!/usr/bin/env python3
"""Load tag merge mappings and apply them across Jekyll front matter."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

import yaml

from directory_io import NoAliasDumper, load_entry, save_entry
from repo_paths import REPO_ROOT, SITE_ROOT

DEFAULT_MAP_PATH = REPO_ROOT / "config" / "tag_merge_map.yml"
DEFAULT_TAG_GROUPS_PATH = SITE_ROOT / "_data" / "tag_groups.yml"
DEFAULT_FIELDS = ("tags", "search_keywords")
SKIP_DIR_NAMES = {"_site", "node_modules", ".git", ".jekyll-cache"}
LOWERCASE_TITLE_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "for",
    "from",
    "in",
    "into",
    "nor",
    "of",
    "on",
    "or",
    "per",
    "so",
    "the",
    "to",
    "up",
    "via",
    "vs",
}
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def title_case_tag(tag: str) -> str:
    """Title-case ordinary tag words without changing acronyms or brand casing."""

    words = list(WORD_RE.finditer(tag))
    first_word_start = words[0].start() if words else None
    last_word_start = words[-1].start() if words else None

    def replace_word(match: re.Match[str]) -> str:
        word = match.group()
        if (
            word.casefold() in LOWERCASE_TITLE_WORDS
            and match.start() not in {first_word_start, last_word_start}
        ):
            return word.casefold()
        if word.isupper() or any(char.isupper() for char in word[1:]):
            return word
        return word[:1].upper() + word[1:].lower()

    return WORD_RE.sub(replace_word, tag)


def load_merge_config(path: Path | None = None) -> dict:
    map_path = (path or DEFAULT_MAP_PATH).resolve()
    data = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Merge map must be a mapping: {map_path}")
    return data


def build_lookup(config: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}

    merges = config.get("merges") or {}
    if not isinstance(merges, dict):
        raise ValueError("merges must be a mapping of canonical tag -> variants")

    for canonical, variants in merges.items():
        raw_canonical = str(canonical).strip()
        if not raw_canonical:
            continue
        canonical = title_case_tag(raw_canonical)
        lookup[raw_canonical] = canonical
        lookup[canonical] = canonical
        if variants is None:
            continue
        if isinstance(variants, str):
            variants = [variants]
        if not isinstance(variants, list):
            raise ValueError(f"Variants for {canonical!r} must be a list")
        for variant in variants:
            variant = str(variant).strip()
            if not variant:
                continue
            if variant in lookup and lookup[variant] != canonical:
                raise ValueError(
                    f"Conflicting mapping for {variant!r}: "
                    f"{lookup[variant]!r} vs {canonical!r}"
                )
            lookup[variant] = canonical

    aliases = config.get("aliases") or {}
    if not isinstance(aliases, dict):
        raise ValueError("aliases must be a mapping of variant -> canonical")
    for variant, canonical in aliases.items():
        variant = str(variant).strip()
        canonical = title_case_tag(str(canonical).strip())
        if not variant or not canonical:
            continue
        if variant in lookup and lookup[variant] != canonical:
            raise ValueError(
                f"Conflicting mapping for {variant!r}: "
                f"{lookup[variant]!r} vs {canonical!r}"
            )
        lookup[variant] = canonical
        lookup.setdefault(canonical, canonical)

    return lookup


def configured_fields(config: dict) -> tuple[str, ...]:
    fields = config.get("fields") or DEFAULT_FIELDS
    if isinstance(fields, str):
        fields = [fields]
    return tuple(str(field).strip() for field in fields if str(field).strip())


def tag_list_items(items) -> list[str]:
    if items is None:
        return []
    if isinstance(items, str):
        items = [items]
    if not isinstance(items, list):
        return []

    return [item.strip() for item in items if isinstance(item, str) and item.strip()]


def merge_tag_list(items, lookup: dict[str, str]) -> list[str]:
    out: list[str] = []
    seen_lower: set[str] = set()
    for tag in tag_list_items(items):
        canonical = title_case_tag(lookup.get(tag, tag))
        key = canonical.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        out.append(canonical)
    return out


def iter_frontmatter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---\n") and "\n---\n" in text[4:]:
            files.append(path)
    return files


def apply_to_frontmatter(
    path: Path,
    lookup: dict[str, str],
    fields: tuple[str, ...],
    *,
    root: Path | None = None,
    write: bool = False,
) -> list[str]:
    data, body = load_entry(path)
    changes: list[str] = []
    updated = False
    site_root = (root or SITE_ROOT).resolve()

    for field in fields:
        if field not in data:
            continue
        before = data.get(field)
        after = merge_tag_list(before, lookup)
        if tag_list_items(before) == after:
            continue
        try:
            rel = path.resolve().relative_to(site_root)
        except ValueError:
            rel = path
        changes.append(f"{rel}: {field}")
        data[field] = after
        updated = True

    if updated and write:
        save_entry(path, data, body)
    return changes


def apply_to_tag_groups(
    path: Path,
    lookup: dict[str, str],
    *,
    write: bool = False,
) -> list[str]:
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    groups = data.get("groups")
    if not isinstance(groups, list):
        return []

    changes: list[str] = []
    updated = False
    for group in groups:
        if not isinstance(group, dict) or "tags" not in group:
            continue
        before = group.get("tags")
        after = merge_tag_list(before, lookup)
        if tag_list_items(before) == after:
            continue
        label = group.get("label", "?")
        changes.append(f"{path.name}: group {label!r}")
        group["tags"] = after
        updated = True

    if updated and write:
        dumped = yaml.dump(data, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper).strip()
        path.write_text(f"{dumped}\n", encoding="utf-8")
    return changes


def collect_tag_counts(root: Path, fields: tuple[str, ...]) -> Counter:
    counts: Counter = Counter()
    for path in iter_frontmatter_files(root):
        data, _ = load_entry(path)
        for field in fields:
            for tag in merge_tag_list(data.get(field), {}):
                counts[tag] += 1
    return counts


def find_unmapped_duplicate_groups(counts: Counter, lookup: dict[str, str]) -> dict[str, list[tuple[str, int]]]:
    grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for tag, count in counts.items():
        grouped[tag.lower()].append((tag, count))

    duplicates: dict[str, list[tuple[str, int]]] = {}
    for key, variants in grouped.items():
        if len(variants) < 2:
            continue
        canonical_forms = {title_case_tag(lookup.get(tag, tag)) for tag, _ in variants}
        if len(canonical_forms) == 1:
            continue
        variants.sort(key=lambda item: (-item[1], item[0].lower()))
        duplicates[key] = variants
    return duplicates


def suggest_merge_yaml(duplicates: dict[str, list[tuple[str, int]]]) -> str:
    lines = ["merges:"]
    for variants in duplicates.values():
        canonical, _ = variants[0]
        lines.append(f"  {yaml.dump(canonical, default_flow_style=True).strip()}:")
        for variant, _ in variants[1:]:
            lines.append(f"    - {variant}")
    return "\n".join(lines)


def apply_all(
    *,
    root: Path,
    map_path: Path,
    tag_groups_path: Path,
    write: bool = False,
) -> tuple[list[str], list[str]]:
    config = load_merge_config(map_path)
    lookup = build_lookup(config)
    fields = configured_fields(config)

    file_changes: list[str] = []
    for path in iter_frontmatter_files(root):
        file_changes.extend(
            apply_to_frontmatter(path, lookup, fields, root=root, write=write)
        )

    group_changes = apply_to_tag_groups(tag_groups_path, lookup, write=write)
    return file_changes, group_changes
