#!/usr/bin/env python3
"""Say which results a reader can read for free, from OpenAlex and Crossref (issue #49).

NVA records what the centre has published, but not whether a reader without a
library subscription can open it. OpenAlex knows, and its data is CC0. For
every result in site/_data/mishmash_results.yml that carries a DOI, this
script asks OpenAlex for the open-access status and the best free copy, and
Crossref for the licence the publisher records. It writes
site/_data/results_openalex.yml, which the result card reads.

Abstracts are deliberately not taken. OpenAlex may republish them, but the
text is usually the publisher's, and the citation from NVA already carries an
abstract where the centre has one.

Usage:
  python3 scripts/enrich_results_from_openalex.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

UA = {"User-Agent": "MishMash-web/1.0 (https://mishmash.no; contact@mishmash.no)"}
MAILTO = "contact@mishmash.no"
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>?#]+?)(?=[.,;)\]]*(?:[\s?#]|$))", re.I)
OUT = SITE_ROOT / "_data" / "results_openalex.yml"

# The statuses OpenAlex uses, and whether they mean a reader can open the work.
FREE = {"gold", "green", "hybrid", "bronze", "diamond"}
STATUS_LABEL = {
    "gold": "open access", "diamond": "open access", "hybrid": "open access",
    "green": "open access (author copy)", "bronze": "free to read", "closed": "subscription",
}
LICENCE_LABEL = {
    "cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc-by-nc": "CC BY-NC", "cc-by-nc-sa": "CC BY-NC-SA",
    "cc-by-nc-nd": "CC BY-NC-ND", "cc-by-nd": "CC BY-ND", "cc0": "CC0", "public-domain": "public domain",
}


def dois_of(result: dict) -> set[str]:
    found = set()
    for text in [result.get("url") or "", (result.get("citation") or {}).get("details") or ""]:
        for m in DOI_RE.finditer(text):
            found.add(m.group(1).rstrip(".").lower())
    return found


def fetch_openalex(dois: list[str], session: requests.Session) -> dict[str, dict]:
    works: dict[str, dict] = {}
    for i in range(0, len(dois), 40):
        chunk = dois[i:i + 40]
        flt = "doi:" + "|".join(f"https://doi.org/{d}" for d in chunk)
        r = session.get("https://api.openalex.org/works",
                        params={"filter": flt, "per-page": 50, "mailto": MAILTO,
                                "select": "doi,open_access,best_oa_location,primary_location,type"},
                        headers=UA, timeout=60)
        r.raise_for_status()
        for w in r.json().get("results", []):
            key = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            if key:
                works[key] = w
        time.sleep(0.3)
    return works


def crossref_licence(doi: str, session: requests.Session) -> str | None:
    """The licence URL the publisher records, or None when there is none."""
    try:
        r = session.get(f"https://api.crossref.org/works/{doi}", params={"mailto": MAILTO},
                        headers=UA, timeout=30)
        if r.status_code != 200:
            return None
        licences = r.json()["message"].get("license") or []
    except (requests.RequestException, ValueError, KeyError):
        return None
    for lic in licences:                      # prefer the one that applies to the published version
        if lic.get("content-version") in ("vor", "am") and lic.get("URL"):
            return lic["URL"]
    return licences[0]["URL"] if licences and licences[0].get("URL") else None


def licence_code(url: str | None) -> str | None:
    """The short code for a licence URL, for Creative Commons and public domain only."""
    if not url:
        return None
    m = re.search(r"creativecommons\.org/licenses/([a-z-]+)/", url, re.I)
    if m:
        return "cc-" + m.group(1).lower()
    if re.search(r"creativecommons\.org/publicdomain/zero", url, re.I):
        return "cc0"
    if re.search(r"creativecommons\.org/publicdomain/mark", url, re.I):
        return "public-domain"
    return None


def entry_for(work: dict, licence_url: str | None) -> dict:
    oa = work.get("open_access") or {}
    status = oa.get("oa_status") or "unknown"
    best = work.get("best_oa_location") or {}
    code = licence_code(licence_url) or (best.get("license") or "").lower() or None
    if code and code not in LICENCE_LABEL:
        code = licence_code(code) if code.startswith("http") else None
    entry = {
        "status": status,
        "label": STATUS_LABEL.get(status, status),
        "free": status in FREE or bool(oa.get("is_oa")),
    }
    url = best.get("pdf_url") or best.get("landing_page_url") or oa.get("oa_url")
    if url:
        entry["url"] = url
    if code:
        entry["licence"] = code
        entry["licence_label"] = LICENCE_LABEL[code]
    if licence_url:
        entry["licence_url"] = licence_url
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = yaml.safe_load((SITE_ROOT / "_data" / "mishmash_results.yml").read_text(encoding="utf-8"))
    dois = sorted({d for r in data.get("results", []) for d in dois_of(r)})
    if not dois:
        print("enrich_results_from_openalex: no DOIs in the results; nothing to do")
        return 0

    session = requests.Session()
    works = fetch_openalex(dois, session)
    entries: dict[str, dict] = {}
    for doi in dois:
        work = works.get(doi)
        if not work:
            continue
        licence_url = crossref_licence(doi, session)
        time.sleep(0.2)
        entries[doi] = entry_for(work, licence_url)

    free = sum(1 for e in entries.values() if e["free"])
    print(f"enrich_results_from_openalex: {len(dois)} DOIs, {len(entries)} known to OpenAlex, {free} free to read")
    if args.dry_run:
        for doi, e in sorted(entries.items()):
            print(f"  {doi}: {e['label']}{' ' + e.get('licence_label', '') if e.get('licence_label') else ''}")
        return 0

    out = {
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "OpenAlex (CC0) for the open-access status and the free copy, Crossref for the licence",
        "count": len(entries),
        "free": free,
        "works": entries,
    }
    OUT.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"enrich_results_from_openalex: wrote {OUT.relative_to(SITE_ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
