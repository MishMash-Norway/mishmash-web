#!/usr/bin/env python3
"""Check that the compute access lookup covers every partner institution.

The lookup at /internal/compute/ works from `site/_data/compute_access.yml`.
Every institution in the directory must either map to a category that exists or
be listed as deliberately excluded, or the page silently shows a visitor
nothing. This test fails the build instead.
"""

import sys
from pathlib import Path

import yaml

from repo_paths import SITE_ROOT

DATA = SITE_ROOT / "_data" / "compute_access.yml"
INSTITUTIONS = SITE_ROOT / "_directory" / "institutions"

REQUIRED_CATEGORY_FIELDS = [
    "label",
    "covers",
    "start_here",
    "chat",
    "transcription",
    "fine_tuning",
    "national",
    "european",
    "ask",
]


def directory_slugs() -> set[str]:
    return {
        d.name
        for d in INSTITUTIONS.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "index.md").exists()
    }


def main() -> int:
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    categories = data.get("categories") or {}
    mapped = data.get("institutions") or {}
    errors = []

    for name, category in categories.items():
        for field in REQUIRED_CATEGORY_FIELDS:
            if not (category or {}).get(field):
                errors.append(f"category '{name}' is missing '{field}'")

    if not data.get("last_checked"):
        errors.append("compute_access.yml has no last_checked date")
    if not data.get("universal_note"):
        errors.append("compute_access.yml has no universal_note")

    excluded = data.get("excluded") or {}
    slugs = directory_slugs()
    accounted = set(mapped) | set(excluded)

    for slug in sorted(slugs - accounted):
        errors.append(f"institution '{slug}' is neither categorised nor excluded in compute_access.yml")
    for slug in sorted(accounted - slugs):
        errors.append(f"compute_access.yml lists '{slug}', which is not in the directory")
    for slug in sorted(set(mapped) & set(excluded)):
        errors.append(f"institution '{slug}' is both categorised and excluded")
    for slug, reason in sorted(excluded.items()):
        if not reason:
            errors.append(f"excluded institution '{slug}' has no reason given")

    for slug, entry in sorted(mapped.items()):
        category = (entry or {}).get("category")
        if not category:
            errors.append(f"institution '{slug}' has no category")
        elif category not in categories:
            errors.append(f"institution '{slug}' uses unknown category '{category}'")
        for service in ((entry or {}).get("local") or {}).get("services") or []:
            if not service.get("name") or not service.get("note"):
                errors.append(f"institution '{slug}' has a local service without a name or note")

    if errors:
        print(f"compute access lookup: {len(errors)} problem(s)")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"compute access lookup: {len(slugs)} partner institutions, "
        f"{len(mapped)} answered across {len(categories)} categories, "
        f"{len(excluded)} deliberately excluded"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
