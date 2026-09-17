#!/usr/bin/env python3
"""Publish the site's data as files others can reuse (issue #53).

Writes JSON and CSV files into site/data/ (ignored by git, built at deploy):
people, institutions, projects, results and events, each with the licence,
the generation time and the sources named. People carry only the
professional fields the privacy notice lists: name, position, department,
institutions, work packages, roles, identifiers and the address of the page.
No portraits, no contact details.

The site's own data is CC0; results and identifiers pulled from NVA, ORCID
and Wikipedia keep their sources' terms, which are named in each file.

Usage:
  python3 scripts/build_open_data.py
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from directory_io import iter_directory_entries
from repo_paths import SITE_ROOT

OUT = SITE_ROOT / "data"
SITE_URL = "https://mishmash.no"
TERMS = SITE_URL + "/about/terms/"
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>?#]+?)(?=[.,;)\]]*(?:[\s?#]|$))", re.I)

PERSON_URL_KEYS = ["orcid", "nva", "wikidata", "personal_website", "institutional_website", "github", "linkedin", "mastodon", "bluesky", "youtube", "instagram"]
INSTITUTION_URL_KEYS = ["website", "wikipedia", "wikidata", "ror"]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugs(value) -> list[str]:
    out = []
    for v in value or []:
        s = str(v).strip("/").split("/")[-1]
        if s:
            out.append(s)
    return out


def people_rows(root: Path) -> list[dict]:
    rows = []
    for section, folder, _, data, _ in iter_directory_entries(root):
        if section != "people" or data.get("published") is False:
            continue
        urls = data.get("urls") or {}
        insts = slugs([data.get("institution")] + list(data.get("institutions") or []))
        rows.append({
            "slug": data["slug"],
            "name": data.get("name") or data.get("title"),
            "url": SITE_URL + "/people/" + data["slug"] + "/",
            "position": data.get("position") or None,
            "department": data.get("department") or None,
            "institutions": list(dict.fromkeys(insts)),
            "work_packages": data.get("wps") or [],
            "roles": data.get("roles") or [],
            "projects": slugs(data.get("projects")),
            "identifiers": {k: urls.get(k) for k in PERSON_URL_KEYS if urls.get(k)},
        })
    return rows


def institution_rows(root: Path, wikidata_facts: dict) -> list[dict]:
    rows = []
    for section, folder, _, data, _ in iter_directory_entries(root):
        if section != "institutions" or data.get("published") is False:
            continue
        urls = data.get("urls") or {}
        facts = wikidata_facts.get(data["slug"]) or {}
        rows.append({
            "slug": data["slug"],
            "name": data.get("name"),
            "short_name": data.get("short_name") or None,
            "url": SITE_URL + "/institutions/" + data["slug"] + "/",
            "city": data.get("city") or None,
            "country": data.get("country") or None,
            "coordinates": facts.get("coordinates") or None,
            "identifiers": {k: urls.get(k) for k in INSTITUTION_URL_KEYS if urls.get(k)},
        })
    return rows


def project_rows(root: Path) -> list[dict]:
    rows = []
    for section, folder, _, data, _ in iter_directory_entries(root):
        if section != "projects" or data.get("published") is False:
            continue
        rows.append({
            "slug": data["slug"],
            "title": data.get("title") or data.get("name"),
            "url": SITE_URL + "/projects/" + data["slug"] + "/",
            "work_packages": data.get("wps") or [],
            "tags": data.get("tags") or [],
            "people": slugs(data.get("people")),
            "institutions": slugs(data.get("institutions")),
        })
    return rows


def result_rows(root: Path) -> list[dict]:
    path = root / "_data" / "mishmash_results.yml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = []
    for r in data.get("results") or []:
        text = " ".join([r.get("url") or "", (r.get("citation") or {}).get("details") or ""])
        doi = next((m.group(1).rstrip(".").lower() for m in DOI_RE.finditer(text)), None)
        rows.append({
            "title": r.get("title"),
            "year": r.get("year"),
            "type": r.get("type_label") or r.get("type"),
            "doi": doi,
            "nva_url": r.get("nva_url"),
            "url": r.get("url"),
            "contributors": [{"name": c.get("name"), "slug": c.get("slug")} for c in r.get("contributors") or []],
            "institutions": [i.get("slug") for i in r.get("institutions") or [] if i.get("slug")],
            "source": "NVA",
        })
    zpath = root / "_data" / "zenodo_records.yml"
    if zpath.exists():
        seen = {r["doi"] for r in rows if r.get("doi")}
        for z in (yaml.safe_load(zpath.read_text(encoding="utf-8")) or {}).get("records") or []:
            if z.get("doi") in seen:
                continue
            rows.append({
                "title": z.get("title"), "year": (z.get("date") or "")[:4] or None,
                "type": z.get("type"), "doi": z.get("doi"), "nva_url": None, "url": z.get("url"),
                "contributors": [{"name": c.get("name"), "slug": None} for c in z.get("creators") or []],
                "institutions": [], "source": "Zenodo", "licence": z.get("licence"),
            })
    return rows


def event_rows(root: Path) -> list[dict]:
    rows = []
    for f in sorted((root / "_events").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", text, re.S)
        if not m:
            continue
        d = yaml.safe_load(m.group(1)) or {}
        if d.get("draft") or d.get("subpage"):
            continue
        slug = d.get("slug") or f.stem[11:]
        rows.append({
            "slug": slug,
            "title": d.get("title"),
            "start": str(d.get("date")) if d.get("date") else None,
            "end": str(d.get("end_date")) if d.get("end_date") else None,
            "location": d.get("location"),
            "categories": d.get("categories") or [],
            "url": SITE_URL + "/events/" + slug + "/",
            "description": d.get("description"),
        })
    return rows


def flatten(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                out[f"{k}_{kk}"] = vv if not isinstance(vv, (list, dict)) else json.dumps(vv, ensure_ascii=False)
        elif isinstance(v, list):
            out[k] = "; ".join(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in v)
        else:
            out[k] = v
    return out


DATASETS = {
    "people": ("People in the MishMash directory: professional facts only", "CC0 for the site's own fields; identifiers from NVA and ORCID keep their sources' terms", ["NVA", "ORCID", "the person"]),
    "institutions": ("Partner institutions with identifiers and coordinates", "CC0; coordinates and identifiers from Wikidata (CC0)", ["Wikidata", "Wikipedia"]),
    "projects": ("MishMash projects with people, institutions and work packages", "CC0", ["the centre"]),
    "results": ("Research results registered for the centre in the national research archive, and deposits on Zenodo", "Metadata as recorded in NVA (Sikt) and Zenodo; the compilation is CC0", ["NVA", "Zenodo"]),
    "events": ("MishMash events, past and upcoming", "CC0", ["the centre"]),
}


def write(name: str, rows: list[dict]) -> None:
    title, licence, sources = DATASETS[name]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps({
        "title": title, "licence": licence, "sources": sources, "terms": TERMS,
        "generated_at": now(), "count": len(rows), "items": rows,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    flat = [flatten(r) for r in rows]
    keys = list(dict.fromkeys(k for r in flat for k in r))
    with (OUT / f"{name}.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in flat:
            w.writerow(r)


def main() -> int:
    root = SITE_ROOT
    facts_path = root / "_data" / "wikidata_institutions.yml"
    facts = yaml.safe_load(facts_path.read_text(encoding="utf-8")) if facts_path.exists() else {}
    sets = {
        "people": people_rows(root),
        "institutions": institution_rows(root, facts or {}),
        "projects": project_rows(root),
        "results": result_rows(root),
        "events": event_rows(root),
    }
    for name, rows in sets.items():
        write(name, rows)
    print("open data: " + ", ".join(f"{k} {len(v)}" for k, v in sets.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
