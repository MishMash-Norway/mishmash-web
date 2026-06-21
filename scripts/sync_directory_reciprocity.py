#!/usr/bin/env python3
"""Normalize project front matter and keep reciprocal directory links in sync."""

from __future__ import annotations

import argparse
from pathlib import Path

from directory_io import (
    as_slug_list,
    extract_institution_slugs,
    extract_person_slugs,
    iter_directory_entries,
    save_entry,
    slug_list_uses_path_refs,
)
from repo_paths import SITE_ROOT


def sorted_unique(values) -> list[str]:
    return sorted({value for value in values if value})


def migrate_project_fields(data: dict, slug: str, body: str) -> dict:
    updated = dict(data)
    updated["type"] = "project"
    updated["slug"] = slug
    updated["name"] = str(updated.get("name") or updated.get("title") or slug).strip()

    people = set(as_slug_list(updated.get("people")))
    people.update(extract_person_slugs(body))

    institutions = set(as_slug_list(updated.get("institutions")))
    institutions.update(extract_institution_slugs(body))

    updated["people"] = sorted_unique(people)
    updated["institutions"] = sorted_unique(institutions)
    updated.setdefault("projects", [])
    return updated


def sync_directory(root: Path, dry_run: bool = False) -> dict[str, int]:
    people: dict[str, dict] = {}
    institutions: dict[str, dict] = {}
    projects: dict[str, dict] = {}
    bodies: dict[str, str] = {}
    paths: dict[str, Path] = {}

    raw_projects: dict[str, dict] = {}

    for section, slug, index_md, data, body in iter_directory_entries(root):
        key = f"{section}:{slug}"
        paths[key] = index_md
        bodies[key] = body
        if section == "people":
            people[slug] = data
        elif section == "institutions":
            institutions[slug] = data
        elif section == "projects":
            raw_projects[slug] = data
            projects[slug] = migrate_project_fields(dict(data), slug, body)

    valid_people = set(people)
    valid_institutions = set(institutions)
    valid_projects = set(projects)

    person_institutions = {
        slug: {inst for inst in as_slug_list(data.get("institutions")) if inst in valid_institutions}
        for slug, data in people.items()
    }
    for slug, data in people.items():
        primary = str(data.get("institution") or "").strip()
        if primary in valid_institutions:
            person_institutions.setdefault(slug, set()).add(primary)
    person_projects = {
        slug: {project for project in as_slug_list(data.get("projects")) if project in valid_projects}
        for slug, data in people.items()
    }

    institution_people = {
        slug: {person for person in as_slug_list(data.get("people")) if person in valid_people}
        for slug, data in institutions.items()
    }
    institution_projects = {
        slug: {project for project in as_slug_list(data.get("projects")) if project in valid_projects}
        for slug, data in institutions.items()
    }

    project_people = {
        slug: {person for person in as_slug_list(data.get("people")) if person in valid_people}
        for slug, data in projects.items()
    }
    project_institutions = {
        slug: {inst for inst in as_slug_list(data.get("institutions")) if inst in valid_institutions}
        for slug, data in projects.items()
    }

    for person_slug, inst_slugs in person_institutions.items():
        for inst_slug in inst_slugs:
            institution_people.setdefault(inst_slug, set()).add(person_slug)

    for inst_slug, person_slugs in institution_people.items():
        for person_slug in person_slugs:
            person_institutions.setdefault(person_slug, set()).add(inst_slug)

    for person_slug, project_slugs in person_projects.items():
        for project_slug in project_slugs:
            project_people.setdefault(project_slug, set()).add(person_slug)

    for project_slug, person_slugs in project_people.items():
        for person_slug in person_slugs:
            person_projects.setdefault(person_slug, set()).add(project_slug)

    for project_slug, inst_slugs in project_institutions.items():
        for inst_slug in inst_slugs:
            institution_projects.setdefault(inst_slug, set()).add(project_slug)

    for inst_slug, project_slugs in institution_projects.items():
        for project_slug in project_slugs:
            project_institutions.setdefault(project_slug, set()).add(inst_slug)

    changed = {"people": 0, "institutions": 0, "projects": 0}

    for slug, data in people.items():
        new_institutions = sorted_unique(person_institutions.get(slug, set()))
        new_projects = sorted_unique(person_projects.get(slug, set()))
        if (
            new_institutions != as_slug_list(data.get("institutions"))
            or new_projects != as_slug_list(data.get("projects"))
            or slug_list_uses_path_refs(data.get("institutions"))
            or slug_list_uses_path_refs(data.get("projects"))
        ):
            data["institutions"] = new_institutions
            data["projects"] = new_projects
            if not dry_run:
                save_entry(paths[f"people:{slug}"], data, bodies[f"people:{slug}"])
            changed["people"] += 1

    for slug, data in institutions.items():
        new_people = sorted_unique(institution_people.get(slug, set()))
        new_projects = sorted_unique(institution_projects.get(slug, set()))
        if (
            new_people != as_slug_list(data.get("people"))
            or new_projects != as_slug_list(data.get("projects"))
            or slug_list_uses_path_refs(data.get("people"))
            or slug_list_uses_path_refs(data.get("projects"))
        ):
            data["people"] = new_people
            data["projects"] = new_projects
            if not dry_run:
                save_entry(paths[f"institutions:{slug}"], data, bodies[f"institutions:{slug}"])
            changed["institutions"] += 1

    for slug, data in projects.items():
        body = bodies[f"projects:{slug}"]
        raw = raw_projects[slug]
        updated = migrate_project_fields(dict(data), slug, body)
        updated["people"] = sorted_unique(project_people.get(slug, set()))
        updated["institutions"] = sorted_unique(project_institutions.get(slug, set()))
        expected_name = str(raw.get("name") or raw.get("title") or slug).strip()
        if (
            updated.get("type") != raw.get("type")
            or updated.get("slug") != raw.get("slug")
            or str(updated.get("name", "")).strip() != expected_name
            or updated["people"] != as_slug_list(raw.get("people"))
            or updated["institutions"] != as_slug_list(raw.get("institutions"))
            or slug_list_uses_path_refs(raw.get("people"))
            or slug_list_uses_path_refs(raw.get("institutions"))
        ):
            if not dry_run:
                save_entry(paths[f"projects:{slug}"], updated, body)
            changed["projects"] += 1

    return changed


def main():
    parser = argparse.ArgumentParser(
        description="Normalize project front matter and sync reciprocal directory links."
    )
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    changed = sync_directory(Path(args.root).resolve(), dry_run=args.dry_run)
    mode = "would update" if args.dry_run else "updated"
    print(
        f"{mode.capitalize()} people: {changed['people']}, "
        f"institutions: {changed['institutions']}, projects: {changed['projects']}"
    )


if __name__ == "__main__":
    main()
