#!/usr/bin/env python3
"""Sync MishMash project results from NVA into _data/mishmash_results.yml."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from enrich_directory_from_nva import (  # noqa: E402
    CRISTIN_RE,
    NoAliasDumper,
    build_institution_lookup,
    configure_nva_auth,
    extract_profile_id,
    get_json,
    localized_text,
    nva_api_url,
    nva_publication_source,
    nva_publication_url,
    normalize_publication_year,
    resolve_institution_slug,
    split_frontmatter,
    work_sort_key,
    _nva_request_headers,
)

MISHMASH_NVA_PROJECT_ID = "2744839"
DEFAULT_OUTPUT = ROOT / "_data" / "mishmash_results.yml"
PAGE_SIZE = 100


def extract_cristin_person_id(value: str) -> str | None:
    if not value:
        return None
    match = CRISTIN_RE.search(value)
    return match.group(1) if match else None


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


def nva_publication_page_url(hit: dict) -> str:
    identifier = (hit.get("identifier") or "").strip()
    if identifier:
        return f"https://nva.sikt.no/publication/{identifier}"

    resource_id = (hit.get("id") or "").strip()
    if "/publication/" in resource_id:
        return resource_id.replace("https://api.nva.unit.no", "https://nva.sikt.no")
    return ""


def contributor_name(identity: dict) -> str:
    name = (identity.get("name") or "").strip()
    if name:
        return name
    first = (identity.get("firstName") or "").strip()
    last = (identity.get("lastName") or "").strip()
    return f"{first} {last}".strip()


def collect_institution_urls(hit: dict) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def add(url: str) -> None:
        value = (url or "").strip()
        if value.startswith("http") and value not in seen:
            seen.add(value)
            urls.append(value)

    for key in ("curatingInstitutions", "contributorOrganizations", "topLevelOrganizations"):
        for url in hit.get(key) or []:
            if isinstance(url, str):
                add(url)

    entity = hit.get("entityDescription") or {}
    for contributor in entity.get("contributors") or []:
        for affiliation in contributor.get("affiliations") or []:
            add((affiliation.get("institutionId") or "").strip())
            add((affiliation.get("id") or "").strip())

    return urls


def parse_result_hit(
    hit: dict,
    person_lookup: dict[str, dict[str, str]],
    institution_lookup: dict[str, str],
    slug_to_institution_name: dict[str, str],
    org_cache: dict,
) -> dict:
    entity = hit.get("entityDescription") or {}
    publication_date = entity.get("publicationDate") or {}
    year = ""
    if isinstance(publication_date, dict):
        year = normalize_publication_year(publication_date.get("year"))

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

    institutions: list[dict[str, str]] = []
    seen_slugs: set[str] = set()
    for org_url in collect_institution_urls(hit):
        slug = resolve_institution_slug(org_url, org_cache, institution_lookup)
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        institutions.append(
            {
                "name": slug_to_institution_name.get(slug, slug),
                "slug": slug,
                "url": f"/institutions/{slug}/",
            }
        )

    result_type = nva_publication_source(entity.get("reference") or {})
    external_url = nva_publication_url(hit)
    nva_url = nva_publication_page_url(hit)

    entry = {
        "title": localized_text(entity.get("mainTitle")),
        "year": year,
        "type": result_type,
        "contributors": contributors,
        "institutions": institutions,
    }
    if external_url:
        entry["url"] = external_url
    if nva_url:
        entry["nva_url"] = nva_url
    return entry


def result_sort_key(result: dict) -> tuple[str, int]:
    type_name = (result.get("type") or "Other").lower()
    return (type_name, -work_sort_key(result))


def fetch_project_results(project_id: str) -> list[dict]:
    project_url = nva_api_url(f"/cristin/project/{project_id}")
    hits: list[dict] = []
    offset = 0

    while True:
        response = requests.get(
            nva_api_url("/search/resources"),
            params={
                "project": project_url,
                "size": PAGE_SIZE,
                "from": offset,
            },
            headers=_nva_request_headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        batch = data.get("hits") or []
        hits.extend(batch)
        total = int(data.get("totalHits") or 0)
        offset += len(batch)
        if not batch or offset >= total:
            break

    return hits


def fetch_project_metadata(project_id: str) -> dict:
    project = get_json(nva_api_url(f"/cristin/project/{project_id}"))
    funding = project.get("funding") or []
    rcn_grant = ""
    if funding and isinstance(funding[0], dict):
        rcn_grant = str(funding[0].get("identifier") or "").strip()

    alt_titles = project.get("alternativeTitles") or []
    title_nb = ""
    if alt_titles and isinstance(alt_titles[0], dict):
        title_nb = (alt_titles[0].get("nb") or "").strip()

    return {
        "nva_id": project_id,
        "nva_url": f"https://nva.sikt.no/projects/{project_id}",
        "rcn_grant": rcn_grant,
        "title": {
            "en": (project.get("title") or "").strip(),
            "nb": title_nb or (project.get("title") or "").strip(),
        },
    }


def sync_results(root: Path, project_id: str, output: Path) -> dict:
    configure_nva_auth()
    person_lookup = build_person_lookup(root)
    institution_lookup, slug_to_institution_name = build_institution_lookup(root)
    org_cache: dict = {}

    hits = fetch_project_results(project_id)
    results = [
        parse_result_hit(hit, person_lookup, institution_lookup, slug_to_institution_name, org_cache)
        for hit in hits
        if localized_text((hit.get("entityDescription") or {}).get("mainTitle"))
    ]
    results.sort(key=result_sort_key)

    payload = {
        "synced_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "project": fetch_project_metadata(project_id),
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.dump(payload, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync MishMash NVA project results into _data/mishmash_results.yml.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root")
    parser.add_argument("--project-id", default=MISHMASH_NVA_PROJECT_ID, help="NVA Cristin project ID")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output YAML path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()

    try:
        payload = sync_results(root, args.project_id.strip(), output)
    except Exception as exc:
        print(f"Failed to sync NVA results: {exc}")
        return 1

    linked_people = sum(
        1 for result in payload["results"] for contributor in result.get("contributors") or [] if contributor.get("slug")
    )
    linked_institutions = sum(len(result.get("institutions") or []) for result in payload["results"])
    print(f"Wrote {len(payload['results'])} results to {output}")
    print(f"Linked contributors: {linked_people}, institution links: {linked_institutions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
