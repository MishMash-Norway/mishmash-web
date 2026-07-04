#!/usr/bin/env python3
"""Resolve Wikidata QIDs for people and institutions, and pull basic facts.

First step of the linked-data roadmap (wiki: Web Philosophy):

1. People with an ORCID iD are matched to Wikidata items via the ORCID
   property (P496) — an exact identifier match, no name guessing.
2. Institutions with a urls.wikipedia link are matched via the English
   Wikipedia sitelink — also exact.
3. Basic facts for resolved institutions (coordinates, logo, official
   website, inception) are written to site/_data/wikidata_institutions.yml
   as generated reference data; curated files are never overwritten.

Matches are written as urls.wikidata on the entries. Existing
urls.wikidata values are left untouched.
"""
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import requests
import yaml

from directory_io import load_entry, save_entry
from repo_paths import SITE_ROOT

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "MishMash-web-sync/1.0 (https://mishmash.no; contact@mishmash.no)"

ORCID_RE = re.compile(r"orcid\.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", re.I)
WIKIPEDIA_RE = re.compile(r"en\.wikipedia\.org/wiki/([^?#]+)")
QID_RE = re.compile(r"^Q\d+$")


def orcid_id(url: str | None) -> str | None:
    m = ORCID_RE.search(url or "")
    return m.group(1).upper() if m else None


def wikipedia_title(url: str | None) -> str | None:
    m = WIKIPEDIA_RE.search(url or "")
    return requests.utils.unquote(m.group(1)).replace("_", " ") if m else None


def qid_to_url(qid: str) -> str:
    assert QID_RE.match(qid), qid
    return f"https://www.wikidata.org/wiki/{qid}"


def sparql(query: str) -> list[dict]:
    resp = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["results"]["bindings"]


def entries(root: Path, section: str):
    for child in sorted((root / "_directory" / section).iterdir()):
        index_md = child / "index.md"
        if child.name.startswith("_") or not index_md.exists():
            continue
        data, body = load_entry(index_md)
        yield child.name, index_md, data, body


def set_wikidata(index_md: Path, data: dict, body: str, qid: str, dry_run: bool) -> None:
    data.setdefault("urls", {})["wikidata"] = qid_to_url(qid)
    if not dry_run:
        save_entry(index_md, data, body)


def resolve_people(root: Path, dry_run: bool) -> int:
    pending = {}
    for slug, index_md, data, body in entries(root, "people"):
        urls = data.get("urls") or {}
        if urls.get("wikidata"):
            continue
        oid = orcid_id(urls.get("orcid"))
        if oid:
            pending[oid] = (slug, index_md, data, body)
    if not pending:
        print("people: nothing to resolve")
        return 0

    values = " ".join(f'"{oid}"' for oid in pending)
    rows = sparql(
        "SELECT ?item ?orcid WHERE { VALUES ?orcid { %s } ?item wdt:P496 ?orcid . }"
        % values
    )
    matches: dict[str, set[str]] = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        oid = row["orcid"]["value"].upper()
        if oid in pending and QID_RE.match(qid):
            matches.setdefault(oid, set()).add(qid)

    updated = 0
    for oid, qids in matches.items():
        slug, index_md, data, body = pending[oid]
        if len(qids) > 1:
            print(
                f"skip people/{slug}: ORCID {oid} matches several Wikidata items "
                f"({', '.join(sorted(qids))}) — probably duplicates; resolve manually"
            )
            continue
        qid = next(iter(qids))
        set_wikidata(index_md, data, body, qid, dry_run)
        print(f"{'would set' if dry_run else 'set'} people/{slug} -> {qid} (ORCID {oid})")
        updated += 1
    print(f"people: {updated} resolved of {len(pending)} with ORCID")
    return updated


def resolve_institutions(root: Path, dry_run: bool) -> int:
    pending = {}
    for slug, index_md, data, body in entries(root, "institutions"):
        urls = data.get("urls") or {}
        if urls.get("wikidata"):
            continue
        title = wikipedia_title(urls.get("wikipedia"))
        if title:
            pending[title] = (slug, index_md, data, body)
    if not pending:
        print("institutions: nothing to resolve")
        return 0

    updated = 0
    titles = list(pending)
    for i in range(0, len(titles), 50):
        chunk = titles[i : i + 50]
        resp = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "prop": "pageprops",
                "ppprop": "wikibase_item",
                "titles": "|".join(chunk),
                "redirects": 1,
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()["query"]
        # Map redirected/normalized titles back to what we asked for.
        back = {}
        for r in payload.get("normalized", []) + payload.get("redirects", []):
            back[r["to"]] = back.get(r["from"], r["from"])
        for page in payload.get("pages", {}).values():
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            title = back.get(page.get("title"), page.get("title"))
            if not qid or title not in pending or not QID_RE.match(qid):
                continue
            slug, index_md, data, body = pending[title]
            set_wikidata(index_md, data, body, qid, dry_run)
            print(f"{'would set' if dry_run else 'set'} institutions/{slug} -> {qid} ({title})")
            updated += 1
        time.sleep(0.5)
    print(f"institutions: {updated} resolved of {len(pending)} with Wikipedia link")
    return updated


def sync_institution_facts(root: Path, dry_run: bool) -> None:
    qids = {}
    for slug, _index_md, data, _body in entries(root, "institutions"):
        url = (data.get("urls") or {}).get("wikidata") or ""
        m = re.search(r"/(Q\d+)$", url)
        if m:
            qids[m.group(1)] = slug

    if not qids:
        print("facts: no institutions with Wikidata QIDs")
        return

    rows = sparql(
        """
        SELECT ?item ?coord ?logo ?website ?inception WHERE {
          VALUES ?item { %s }
          OPTIONAL { ?item wdt:P625 ?coord . }
          OPTIONAL { ?item wdt:P154 ?logo . }
          OPTIONAL { ?item wdt:P856 ?website . }
          OPTIONAL { ?item wdt:P571 ?inception . }
        }
        """
        % " ".join(f"wd:{q}" for q in qids)
    )
    facts: dict[str, dict] = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        slug = qids.get(qid)
        if not slug:
            continue
        entry = facts.setdefault(slug, {"qid": qid})
        if "coord" in row and "coordinates" not in entry:
            m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", row["coord"]["value"])
            if m:
                entry["coordinates"] = {"lon": float(m.group(1)), "lat": float(m.group(2))}
        if "logo" in row and "logo" not in entry:
            entry["logo"] = row["logo"]["value"]
        if "website" in row and "website" not in entry:
            entry["website"] = row["website"]["value"]
        if "inception" in row and "inception" not in entry:
            entry["inception"] = row["inception"]["value"][:10]

    out = root / "_data" / "wikidata_institutions.yml"
    header = (
        "# Generated by scripts/sync_wikidata.py — do not edit.\n"
        "# Basic institution facts pulled from Wikidata for the entries'\n"
        "# urls.wikidata QIDs. Reference data for future features.\n"
    )
    text = header + yaml.safe_dump(
        {slug: facts[slug] for slug in sorted(facts)},
        allow_unicode=True,
        sort_keys=True,
        default_flow_style=False,
    )
    if dry_run:
        print(f"facts: would write {out} ({len(facts)} institutions)")
    else:
        out.write_text(text, encoding="utf-8")
        print(f"facts: wrote {out} ({len(facts)} institutions)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-facts", action="store_true", help="only resolve QIDs")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    resolve_people(root, args.dry_run)
    resolve_institutions(root, args.dry_run)
    if not args.skip_facts:
        sync_institution_facts(root, args.dry_run)


if __name__ == "__main__":
    main()
