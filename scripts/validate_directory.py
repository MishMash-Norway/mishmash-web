#!/usr/bin/env python3
import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

from directory_io import (
    apply_jekyll_defaults,
    as_slug_list,
    iter_directory_entries,
    load_entry,
    slug_list_uses_path_refs,
)
from repo_paths import SITE_ROOT

SECTIONS = ("people", "institutions", "projects")
TYPE_BY_SECTION = {
    "people": "person",
    "institutions": "institution",
    "projects": "project",
}

REQUIRED_FIELDS = {
    "person": ("type", "slug", "name", "institutions", "projects"),
    "institution": ("type", "slug", "name", "short_name", "people", "projects"),
    "project": ("type", "slug", "name", "people", "institutions"),
}

DEPRECATED_ROLES = {
    "Full member": "Member",
    "Work Package Leader Group member": "Work package leader",
    "Associate member": "Associate member",
    "Affiliate member": "Affiliate member",
    "Board Member": "Board member",
}

CANONICAL_ROLES = {
    "Member",
    "Work package leader",
    "Council member",
    "Board member",
    "Board Leader",
    "Deputy director",
    "Research advisor",
    "Administrative coordinator",
    "Director",
    "Associate member",
    "Affiliate member",
}


def load_wp_leader_slugs(root: Path) -> set[str]:
    wp_file = root / "_data" / "work_packages.yml"
    if not wp_file.exists():
        return set()
    data = yaml.safe_load(wp_file.read_text(encoding="utf-8")) or []
    return {member for wp in data for member in wp.get("members") or []}


def warn_path_style_slug_lists(relative_path, field_name: str, value, warnings: list[str]) -> None:
    if slug_list_uses_path_refs(value):
        warnings.append(
            f"{relative_path}: {field_name} uses /people/ or /institutions/ paths; use slugs instead"
        )


def normalized_name_key(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name or "")
    ascii_name = "".join(ch for ch in ascii_name if not unicodedata.combining(ch))
    ascii_name = ascii_name.casefold()
    return re.sub(r"[^a-z0-9]+", " ", ascii_name).strip()


def main():
    parser = argparse.ArgumentParser(description="Validate directory people/institutions/projects entries.")
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    directory_root = root / "_directory"
    wp_leader_slugs = load_wp_leader_slugs(root)

    errors = []
    warnings = []

    if not directory_root.exists():
        print(f"ERROR: Missing {directory_root}")
        sys.exit(1)

    entries = {
        "person": {},
        "institution": {},
        "project": {},
    }

    for section in SECTIONS:
        section_dir = directory_root / section
        expected_type = TYPE_BY_SECTION[section]
        if not section_dir.exists():
            warnings.append(f"Missing section directory: directory/{section}")
            continue

        for child in sorted(section_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue

            index_md = child / "index.md"
            if not index_md.exists():
                errors.append(f"Missing file: {index_md.relative_to(root)}")
                continue

            try:
                fm, _ = load_entry(index_md)
            except ValueError as exc:
                errors.append(f"{index_md.relative_to(root)}: {exc}")
                continue

            fm = apply_jekyll_defaults(fm, section, child.name)

            for req in REQUIRED_FIELDS[expected_type]:
                if req not in fm:
                    errors.append(f"{index_md.relative_to(root)} missing required field '{req}'")

            if expected_type == "institution":
                short_name = str(fm.get("short_name", "")).strip()
                if not short_name:
                    errors.append(f"{index_md.relative_to(root)} missing or empty short_name")

            actual_type = str(fm.get("type", "")).strip()
            if actual_type != expected_type:
                errors.append(
                    f"{index_md.relative_to(root)} has type '{actual_type}', expected '{expected_type}'"
                )

            slug = str(fm.get("slug", "")).strip()
            if not slug:
                errors.append(f"{index_md.relative_to(root)} has empty slug")
                continue

            if slug != child.name:
                errors.append(
                    f"{index_md.relative_to(root)} slug '{slug}' does not match folder '{child.name}'"
                )

            wikidata_url = str(((fm.get("urls") or {}).get("wikidata")) or "").strip()
            if wikidata_url and not re.match(
                r"^https://www\.wikidata\.org/wiki/Q\d+$", wikidata_url
            ):
                warnings.append(
                    f"{index_md.relative_to(root)}: malformed urls.wikidata '{wikidata_url}'"
                )

            # Without an explicit permalink, Jekyll publishes the entry at
            # /<section>/<slug>/index/ and links to /<section>/<slug>/ break.
            expected_permalink = f"/{section}/{slug}/"
            permalink = str(fm.get("permalink", "")).strip()
            if not permalink:
                errors.append(
                    f"{index_md.relative_to(root)} missing permalink '{expected_permalink}'"
                )
            elif permalink != expected_permalink:
                errors.append(
                    f"{index_md.relative_to(root)} permalink '{permalink}' should be '{expected_permalink}'"
                )

            if slug in entries[expected_type]:
                other = entries[expected_type][slug]["path"]
                errors.append(
                    f"Duplicate slug '{slug}' in {index_md.relative_to(root)} and {other.relative_to(root)}"
                )
                continue

            entries[expected_type][slug] = {
                "path": index_md,
                "name": str(fm.get("name", "")).strip(),
                "institutions": as_slug_list(fm.get("institutions", [])),
                "projects": as_slug_list(fm.get("projects", [])),
                "people": as_slug_list(fm.get("people", [])),
            }

            rel = index_md.relative_to(root)
            if expected_type == "person":
                for role in fm.get("roles") or []:
                    if role in DEPRECATED_ROLES:
                        warnings.append(
                            f"{rel}: deprecated role '{role}' (use '{DEPRECATED_ROLES[role]}')"
                        )
                    elif role not in CANONICAL_ROLES:
                        warnings.append(f"{rel}: non-standard role '{role}'")
                if slug in wp_leader_slugs and "Work package leader" not in (fm.get("roles") or []):
                    warnings.append(
                        f"{rel}: listed in work_packages.yml but missing 'Work package leader' role"
                    )
                urls = fm.get("urls") or {}
                if not (urls.get("nva") or urls.get("orcid")):
                    warnings.append(f"{rel}: missing urls.nva and urls.orcid (will not auto-sync from NVA)")

            if expected_type == "institution":
                warn_path_style_slug_lists(rel, "people", fm.get("people"), warnings)
                warn_path_style_slug_lists(rel, "projects", fm.get("projects"), warnings)

            if expected_type == "project":
                warn_path_style_slug_lists(rel, "people", fm.get("people"), warnings)
                warn_path_style_slug_lists(rel, "institutions", fm.get("institutions"), warnings)

            if expected_type == "person":
                warn_path_style_slug_lists(rel, "institutions", fm.get("institutions"), warnings)
                warn_path_style_slug_lists(rel, "projects", fm.get("projects"), warnings)

    people = entries["person"]
    institutions = entries["institution"]
    projects = entries["project"]

    for pslug, p in people.items():
        ppath = p["path"].relative_to(root)
        for islug in p["institutions"]:
            if islug not in institutions:
                errors.append(f"{ppath}: unknown institution reference '{islug}'")
        for prslug in p["projects"]:
            if prslug not in projects:
                errors.append(f"{ppath}: unknown project reference '{prslug}'")

    for islug, inst in institutions.items():
        ipath = inst["path"].relative_to(root)
        for pslug in inst["people"]:
            if pslug not in people:
                errors.append(f"{ipath}: unknown person reference '{pslug}'")
        for prslug in inst["projects"]:
            if prslug not in projects:
                errors.append(f"{ipath}: unknown project reference '{prslug}'")

    for prslug, proj in projects.items():
        prpath = proj["path"].relative_to(root)
        for pslug in proj["people"]:
            if pslug not in people:
                errors.append(f"{prpath}: unknown person reference '{pslug}'")
        for islug in proj["institutions"]:
            if islug not in institutions:
                errors.append(f"{prpath}: unknown institution reference '{islug}'")

        # A project's institutions should cover its participants' institutions.
        participant_insts = {
            islug
            for pslug in proj["people"]
            if pslug in people
            for islug in people[pslug]["institutions"]
        }
        uncovered = participant_insts - set(proj["institutions"])
        if uncovered:
            warnings.append(
                f"{prpath}: institutions missing for participants' affiliations: "
                + ", ".join(sorted(uncovered))
            )

    for pslug, p in people.items():
        ppath = p["path"].relative_to(root)

        for islug in p["institutions"]:
            if islug in institutions and pslug not in institutions[islug]["people"]:
                errors.append(
                    f"{ppath}: person->institution '{islug}' not reciprocated in institution.people"
                )

        for prslug in p["projects"]:
            if prslug in projects and pslug not in projects[prslug]["people"]:
                errors.append(
                    f"{ppath}: person->project '{prslug}' not reciprocated in project.people"
                )

    for islug, inst in institutions.items():
        ipath = inst["path"].relative_to(root)
        for prslug in inst["projects"]:
            if prslug in projects and islug not in projects[prslug]["institutions"]:
                errors.append(
                    f"{ipath}: institution->project '{prslug}' not reciprocated in project.institutions"
                )

    for islug, inst in institutions.items():
        ipath = inst["path"].relative_to(root)
        for pslug in inst["people"]:
            if pslug in people and islug not in people[pslug]["institutions"]:
                errors.append(
                    f"{ipath}: institution.people '{pslug}' not reciprocated in person.institutions"
                )

    for prslug, proj in projects.items():
        prpath = proj["path"].relative_to(root)
        for pslug in proj["people"]:
            if pslug in people and prslug not in people[pslug]["projects"]:
                errors.append(
                    f"{prpath}: project.people '{pslug}' not reciprocated in person.projects"
                )
        for islug in proj["institutions"]:
            if islug in institutions and prslug not in institutions[islug]["projects"]:
                errors.append(
                    f"{prpath}: project.institutions '{islug}' not reciprocated in institution.projects"
                )

    people_by_name_key = {}
    for pslug, p in people.items():
        key = normalized_name_key(p.get("name", ""))
        if not key:
            continue
        people_by_name_key.setdefault(key, []).append((pslug, p["name"], p["path"].relative_to(root)))

    for key, items in sorted(people_by_name_key.items()):
        if len(items) < 2:
            continue
        details = ", ".join(f"{slug} ({path})" for slug, _name, path in items)
        errors.append(
            f"duplicate person names (accent-insensitive) for '{key}': {details}"
        )

    print("Directory validation report")
    print("---------------------------")
    print(f"People:        {len(people)}")
    print(f"Institutions:  {len(institutions)}")
    print(f"Projects:      {len(projects)}")
    print(f"Warnings:      {len(warnings)}")
    print(f"Errors:        {len(errors)}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\nOK: all checks passed.")


if __name__ == "__main__":
    main()
