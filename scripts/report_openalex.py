#!/usr/bin/env python3
"""Dry run for issue #49: what OpenAlex and Crossref would add to the results.

Read-only. Takes every DOI in site/_data/mishmash_results.yml, asks OpenAlex
for the works in batches, and reports how many resolve, their open-access
status, citation counts, whether an abstract is available, and how many
have a licence in Crossref. Nothing is written to the site.

Usage:
  python3 scripts/report_openalex.py [--out report.md]
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

UA = {"User-Agent": "MishMash-web-report/1.0 (https://mishmash.no; contact@mishmash.no)"}
MAILTO = "contact@mishmash.no"
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>?#]+?)(?=[.,;)\]]*(?:[\s?#]|$))", re.I)


def dois_of(result: dict) -> set[str]:
    found = set()
    for text in [result.get("url") or "", (result.get("citation") or {}).get("details") or ""]:
        for m in DOI_RE.finditer(text):
            found.add(m.group(1).rstrip(".").lower())
    return found


def openalex(dois: list[str]) -> dict[str, dict]:
    out = {}
    for i in range(0, len(dois), 40):
        chunk = dois[i:i + 40]
        flt = "doi:" + "|".join(f"https://doi.org/{d}" for d in chunk)
        r = requests.get("https://api.openalex.org/works",
                         params={"filter": flt, "per-page": 50, "mailto": MAILTO,
                                 "select": "id,doi,title,open_access,cited_by_count,abstract_inverted_index,primary_topic,referenced_works_count"},
                         headers=UA, timeout=60)
        r.raise_for_status()
        for w in r.json().get("results", []):
            out[(w.get("doi") or "").replace("https://doi.org/", "").lower()] = w
        time.sleep(0.3)
    return out


def crossref_licence(doi: str) -> str | None:
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", params={"mailto": MAILTO}, headers=UA, timeout=30)
        if r.status_code != 200:
            return None
        lic = r.json()["message"].get("license") or []
        return lic[0]["URL"] if lic else ""
    except requests.RequestException:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    data = yaml.safe_load((SITE_ROOT / "_data" / "mishmash_results.yml").read_text(encoding="utf-8"))
    results = data["results"]
    doi_map = {}
    for r in results:
        for d in dois_of(r):
            doi_map.setdefault(d, r)
    dois = sorted(doi_map)
    works = openalex(dois)
    oa = Counter((w.get("open_access") or {}).get("oa_status", "unknown") for w in works.values())
    cited = sum(w.get("cited_by_count", 0) for w in works.values())
    with_abstract = sum(1 for w in works.values() if w.get("abstract_inverted_index"))
    topics = Counter(((w.get("primary_topic") or {}).get("display_name") or "none") for w in works.values())
    missing = [d for d in dois if d not in works]

    lic = {}
    for d in list(works)[:40]:
        lic[d] = crossref_licence(d)
        time.sleep(0.2)
    lic_known = sum(1 for v in lic.values() if v)
    lic_none = sum(1 for v in lic.values() if v == "")
    lic_fail = sum(1 for v in lic.values() if v is None)

    L = ["# OpenAlex and Crossref dry run", "",
         f"Results in the list: {len(results)}. Results with a DOI: {len(doi_map)} (distinct DOIs: {len(dois)}).",
         f"Resolved in OpenAlex: {len(works)} of {len(dois)}.", "",
         "## What OpenAlex would add", "",
         f"- Open-access status: " + ", ".join(f"{k} {v}" for k, v in oa.most_common()),
         f"- Citations across the resolved works: {cited}",
         f"- Abstracts available: {with_abstract} of {len(works)}",
         "- Primary topics (top 8): " + "; ".join(f"{k} ({v})" for k, v in topics.most_common(8)),
         "", "## What Crossref would add (sample of up to 40 DOIs)", "",
         f"- Licence URL present: {lic_known}; no licence recorded: {lic_none}; not in Crossref or failed: {lic_fail}",
         "", f"## DOIs OpenAlex does not know ({len(missing)})", ""]
    L += [f"- {d} ({doi_map[d].get('type_label')}: {doi_map[d].get('title', '')[:70]})" for d in missing] or ["- none"]
    text = "\n".join(L) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8"); print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
