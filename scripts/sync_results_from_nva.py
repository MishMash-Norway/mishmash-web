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

from repo_paths import SITE_ROOT  # noqa: E402
from enrich_directory_from_nva import (  # noqa: E402
    NoAliasDumper,
    build_institution_lookup,
    configure_nva_auth,
    find_doi_in_object,
    get_json,
    localized_text,
    nva_api_url,
    nva_publication_url,
    normalize_publication_year,
    resolve_institution_slug,
    work_sort_key,
    _nva_request_headers,
)
from nva_publication_contributors import (  # noqa: E402
    DEFAULT_AUTHOR_ROLES,
    build_person_lookup,
    build_result_contributors,
    contributor_name,
    extract_cristin_person_id,
)
from nva_result_types import (  # noqa: E402
    nva_publication_instance_type,
    nva_result_type_label,
    result_group_type,
)

MISHMASH_NVA_PROJECT_ID = "2744839"
DEFAULT_OUTPUT = SITE_ROOT / "_data" / "mishmash_results.yml"
PAGE_SIZE = 100


def nva_publication_page_url(hit: dict) -> str:
    identifier = (hit.get("identifier") or "").strip()
    if identifier:
        return f"https://nva.sikt.no/publication/{identifier}"

    resource_id = (hit.get("id") or "").strip()
    if "/publication/" in resource_id:
        return resource_id.replace("https://api.nva.unit.no", "https://nva.sikt.no")
    return ""


def format_cristin_name(full_name: str) -> str:
    parts = [part for part in full_name.split() if part]
    if not parts:
        return full_name.strip()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def normalize_doi(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    value = value.replace("https://doi.org/", "").replace("http://doi.org/", "")
    return value.lstrip("doi:").strip()


def format_page_range(pages) -> str:
    if not isinstance(pages, dict):
        return ""
    if pages.get("type") != "Range":
        return ""
    begin = str(pages.get("begin") or "").strip()
    end = str(pages.get("end") or "").strip()
    if begin and end and begin != end:
        return f"{begin}–{end}"
    return begin or end


def find_handle_url(hit: dict) -> str:
    for ident in hit.get("additionalIdentifiers") or []:
        if ident.get("type") == "HandleIdentifier":
            value = (ident.get("value") or "").strip()
            if value:
                return value
    return ""


def full_text_label(url: str) -> str:
    if "hdl.handle.net" in url or "/11250/" in url:
        return "archive"
    return "generic"


def anthology_entity(ref: dict) -> dict:
    ctx = ref.get("publicationContext") or {}
    entity = ctx.get("entityDescription") or {}
    return entity if isinstance(entity, dict) else {}


def build_citation_authors(
    entity: dict,
    person_lookup: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    authors: list[dict[str, str]] = []
    for entry in build_result_contributors(
        entity,
        person_lookup,
        allowed_roles=DEFAULT_AUTHOR_ROLES,
    ):
        name = entry.get("name") or ""
        author = {"display": format_cristin_name(name), "name": name}
        if entry.get("slug"):
            author["slug"] = entry["slug"]
        if entry.get("url"):
            author["url"] = entry["url"]
        authors.append(author)
    return authors


def build_citation_container_and_details(entity: dict, ref: dict) -> tuple[str, str]:
    inst = ref.get("publicationInstance") or {}
    ctx = ref.get("publicationContext") or {}
    inst_type = (inst.get("type") or "").strip()
    container_parts: list[str] = []
    detail_parts: list[str] = []

    if inst_type == "AcademicChapter":
        anthology = anthology_entity(ref)
        inner_ctx = ((anthology.get("reference") or {}).get("publicationContext") or {})
        editors = [
            format_cristin_name(contributor_name((contributor.get("identity") or {})))
            for contributor in anthology.get("contributors") or []
            if contributor_name((contributor.get("identity") or {}))
        ]
        anthology_title = localized_text(anthology.get("mainTitle"))
        if editors:
            container_parts.append(f"In {', '.join(editors)} (Eds.), {anthology_title}.")
        elif anthology_title:
            container_parts.append(f"In {anthology_title}.")
        publisher = ((inner_ctx.get("publisher") or {}).get("name") or "").strip()
        if publisher:
            detail_parts.append(f"{publisher}.")
        isbn_list = inner_ctx.get("isbnList") or []
        if isbn_list:
            detail_parts.append(f"ISBN {isbn_list[0]}.")
        series = inner_ctx.get("series") or {}
        issn = (series.get("printIssn") or series.get("onlineIssn") or "").strip()
        if issn and not isbn_list:
            detail_parts.append(f"ISSN {issn}.")
        page_range = format_page_range(inst.get("pages"))
        if page_range:
            detail_parts.append(f"p. {page_range}.")

    elif inst_type == "AcademicArticle":
        journal = (ctx.get("name") or "").strip()
        if journal:
            container_parts.append(f"{journal}.")
        issn = (ctx.get("printIssn") or ctx.get("onlineIssn") or "").strip()
        if issn:
            detail_parts.append(f"ISSN {issn}.")
        volume = str(inst.get("volume") or "").strip()
        if volume:
            detail_parts.append(f"{volume}.")
        page_range = format_page_range(inst.get("pages"))
        if page_range:
            detail_parts.append(f"p. {page_range}.")

    elif inst_type in {"ReportBasic", "ChapterInReport"} or ctx.get("type") == "Book":
        publisher = ((ctx.get("publisher") or {}).get("name") or "").strip()
        if not publisher:
            publisher = ((anthology_entity(ref).get("reference") or {}).get("publicationContext") or {}).get(
                "publisher", {}
            ).get("name", "")
            publisher = (publisher or "").strip()
        if publisher:
            detail_parts.append(f"{publisher}.")
        page_range = format_page_range(inst.get("pages"))
        if page_range:
            detail_parts.append(f"p. {page_range}.")

    elif ctx.get("type") == "Event":
        event_name = (ctx.get("name") or "").strip()
        place = ((ctx.get("place") or {}).get("name") or "").strip()
        if event_name:
            container_parts.append(f"{event_name}.")
        if place:
            detail_parts.append(f"{place}.")

    elif ctx.get("type") == "MediaContribution":
        channel = (ctx.get("disseminationChannel") or "").strip()
        medium = ((ctx.get("medium") or {}).get("type") or "").strip()
        series = ""
        part_of = ctx.get("partOf") or []
        if part_of and isinstance(part_of[0], dict):
            series = (part_of[0].get("seriesName") or "").strip()
        if series:
            container_parts.append(f"{series}.")
        elif channel:
            container_parts.append(f"{channel}.")
        elif medium:
            container_parts.append(f"{medium}.")

    elif ctx.get("type") == "ExhibitionContent":
        container_parts.append("Exhibition.")

    doi = normalize_doi(ref.get("doi") or find_doi_in_object(entity) or "")
    if doi and not doi.startswith("http"):
        detail_parts.append(f"doi: {doi}.")

    return " ".join(part for part in container_parts if part).strip(), " ".join(detail_parts).strip()


def build_citation(
    hit: dict,
    entity: dict,
    ref: dict,
    person_lookup: dict[str, dict[str, str]],
    external_url: str,
    nva_url: str,
) -> dict:
    container, details = build_citation_container_and_details(entity, ref)
    handle_url = find_handle_url(hit)
    full_text_url = handle_url or external_url or nva_url
    full_text_kind = full_text_label(full_text_url) if full_text_url else ""

    citation = {
        "authors": build_citation_authors(entity, person_lookup),
        "title": localized_text(entity.get("mainTitle")),
        "container": container,
        "details": details,
        "abstract": localized_text(entity.get("abstract")),
    }
    if full_text_url:
        citation["full_text_url"] = full_text_url
        citation["full_text_kind"] = full_text_kind
    if nva_url:
        citation["nva_url"] = nva_url
    return citation


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

    contributors = build_result_contributors(entity, person_lookup)

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

    ref = entity.get("reference") or {}
    instance_type = nva_publication_instance_type(ref)
    external_url = nva_publication_url(hit)
    nva_url = nva_publication_page_url(hit)
    citation = build_citation(hit, entity, ref, person_lookup, external_url, nva_url)

    entry = {
        "title": localized_text(entity.get("mainTitle")),
        "year": year,
        "type": instance_type,
        "type_label": nva_result_type_label(instance_type),
        "group_type": result_group_type(instance_type),
        "contributors": contributors,
        "institutions": institutions,
        "citation": citation,
    }
    if external_url:
        entry["url"] = external_url
    if nva_url:
        entry["nva_url"] = nva_url
    return entry


def result_sort_key(result: dict) -> tuple[str, int]:
    type_name = (result.get("group_type") or result.get("type") or "Other").lower()
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
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
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
