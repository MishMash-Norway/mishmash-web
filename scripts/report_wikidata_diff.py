#!/usr/bin/env python3
"""Report where the directory and Wikidata disagree, and what each side lacks.

Read-only: nothing is written to the directory or to Wikidata. The report is
the first step of issue #45 (Wikidata as the hub): it shows, per institution
and person with a Wikidata item, which facts differ, which facts Wikidata
holds that the site could pull, and which facts the site holds that a
reviewed bot could write back.

Usage:
  python3 scripts/report_wikidata_diff.py            # Markdown to stdout
  python3 scripts/report_wikidata_diff.py --out report.md
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from repo_paths import SITE_ROOT
from sync_wikidata import entries, orcid_id, sparql

QID_RE = re.compile(r"(Q\d+)")


def qid_of(data: dict) -> str | None:
    m = QID_RE.search((data.get("urls") or {}).get("wikidata") or "")
    return m.group(1) if m else None


def norm_url(u: str | None) -> str:
    u = (u or "").strip().lower().rstrip("/")
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return re.sub(r"/(index\.html?|english|en|eng|startsida|home)$", "", u)


def values_clause(qids: list[str]) -> str:
    return " ".join(f"wd:{q}" for q in qids)


def fetch_institutions(qids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"short": set(), "ror": set(), "site": set(), "aliases": set()})
    for i in range(0, len(qids), 60):
        chunk = qids[i:i + 60]
        rows = sparql(f"""
          SELECT ?item ?label ?short ?website ?ror ?enwiki ?logo WHERE {{
            VALUES ?item {{ {values_clause(chunk)} }}
            OPTIONAL {{ ?item rdfs:label ?label FILTER(LANG(?label) = "en") }}
            OPTIONAL {{ ?item wdt:P1813 ?short }}
            OPTIONAL {{ ?item wdt:P856 ?website }}
            OPTIONAL {{ ?item wdt:P6782 ?ror }}
            OPTIONAL {{ ?item wdt:P154 ?logo }}
            OPTIONAL {{ ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }}
          }}""")
        for r in rows:
            q = r["item"]["value"].rsplit("/", 1)[-1]
            d = out[q]
            if "label" in r: d["label"] = r["label"]["value"]
            if "short" in r: d["short"].add(r["short"]["value"])
            if "website" in r: d["site"].add(r["website"]["value"])
            if "ror" in r: d["ror"].add(r["ror"]["value"])
            if "logo" in r: d["logo"] = r["logo"]["value"]
            if "enwiki" in r: d["enwiki"] = r["enwiki"]["value"]
    return out


def fetch_people(qids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"employers": {}, "orcid": set(), "website": set()})
    for i in range(0, len(qids), 60):
        chunk = qids[i:i + 60]
        rows = sparql(f"""
          SELECT ?item ?label ?orcid ?employer ?employerLabel ?website WHERE {{
            VALUES ?item {{ {values_clause(chunk)} }}
            OPTIONAL {{ ?item rdfs:label ?label FILTER(LANG(?label) = "en") }}
            OPTIONAL {{ ?item wdt:P496 ?orcid }}
            OPTIONAL {{ ?item wdt:P108 ?employer . ?employer rdfs:label ?employerLabel FILTER(LANG(?employerLabel) = "en") }}
            OPTIONAL {{ ?item wdt:P856 ?website }}
          }}""")
        for r in rows:
            q = r["item"]["value"].rsplit("/", 1)[-1]
            d = out[q]
            if "label" in r: d["label"] = r["label"]["value"]
            if "orcid" in r: d["orcid"].add(r["orcid"]["value"].upper())
            if "employer" in r:
                d["employers"][r["employer"]["value"].rsplit("/", 1)[-1]] = r.get("employerLabel", {}).get("value", "")
            if "website" in r: d["website"].add(r["website"]["value"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    insts = list(entries(SITE_ROOT, "institutions"))
    people = list(entries(SITE_ROOT, "people"))
    inst_qid = {slug: qid_of(d) for slug, _, d, _ in insts}
    qid_inst = {q: s for s, q in inst_qid.items() if q}

    lines = ["# Directory versus Wikidata", ""]
    differ: list[str] = []
    pull: list[str] = []
    push: list[str] = []
    unresolved = [s for s, q in inst_qid.items() if not q]

    wd = fetch_institutions([q for q in inst_qid.values() if q])
    for slug, _, d, _ in insts:
        q = inst_qid[slug]
        if not q:
            continue
        w = wd.get(q, {})
        name = d.get("name") or slug
        if w.get("label") and w["label"] != name:
            differ.append(f"- {name} ({q}): site name differs from the Wikidata label \"{w['label']}\"")
        site_web = norm_url((d.get("urls") or {}).get("website"))
        wd_webs = {norm_url(x) for x in w.get("site", set())}
        if site_web and wd_webs and site_web not in wd_webs:
            differ.append(f"- {name} ({q}): website {site_web} on the site, {', '.join(sorted(wd_webs))} on Wikidata")
        if not site_web and wd_webs:
            pull.append(f"- {name}: official website {', '.join(sorted(w['site']))}")
        if site_web and not wd_webs:
            push.append(f"- {name} ({q}): official website (P856) {(d.get('urls') or {}).get('website')}")
        short = d.get("short_name")
        if short and w.get("short") and short not in w["short"]:
            differ.append(f"- {name} ({q}): short name {short} on the site, {', '.join(sorted(w['short']))} on Wikidata")
        if short and not w.get("short"):
            push.append(f"- {name} ({q}): short name (P1813) {short}")
        if w.get("ror") and not (d.get("urls") or {}).get("ror"):
            pull.append(f"- {name}: ROR identifier {', '.join(sorted(w['ror']))}")
        if w.get("logo") and not d.get("image"):
            pull.append(f"- {name}: logo on Commons {w['logo']}")
        site_wp = norm_url((d.get("urls") or {}).get("wikipedia"))
        if w.get("enwiki") and site_wp and norm_url(w["enwiki"]) != site_wp:
            differ.append(f"- {name} ({q}): Wikipedia link differs: {site_wp} vs {norm_url(w['enwiki'])}")

    lines += [f"Institutions: {len(insts)} entries, {len(qid_inst)} with a Wikidata item, {len(unresolved)} without.", ""]

    pq = {slug: qid_of(d) for slug, _, d, _ in people}
    wp = fetch_people([q for q in pq.values() if q])
    p_differ: list[str] = []
    p_pull: list[str] = []
    p_push: list[str] = []
    for slug, _, d, _ in people:
        q = pq[slug]
        if not q:
            continue
        w = wp.get(q, {})
        name = d.get("name") or slug
        if w.get("label") and w["label"] != name:
            p_differ.append(f"- {name} ({q}): Wikidata label is \"{w['label']}\"")
        oid = orcid_id((d.get("urls") or {}).get("orcid"))
        if oid and w.get("orcid") and oid not in w["orcid"]:
            p_differ.append(f"- {name} ({q}): ORCID {oid} on the site, {', '.join(sorted(w['orcid']))} on Wikidata")
        site_insts = list(dict.fromkeys([d.get("institution")] + list(d.get("institutions") or [])))
        site_inst_qids = {inst_qid.get(s) for s in site_insts if s and inst_qid.get(s)}
        emp = w.get("employers", {})
        if site_inst_qids and emp and not (site_inst_qids & set(emp)):
            p_differ.append(f"- {name} ({q}): employer on Wikidata is {', '.join(sorted(emp.values()))}; the site lists {', '.join(s for s in site_insts if s)}")
        if site_inst_qids and not emp:
            p_push.append(f"- {name} ({q}): employer (P108) {', '.join(qid_inst[x] for x in site_inst_qids)}")
        web = (d.get("urls") or {}).get("personal_website")
        if web and not w.get("website"):
            p_push.append(f"- {name} ({q}): official website (P856) {web}")
        if not web and w.get("website"):
            p_pull.append(f"- {name}: website {', '.join(sorted(w['website']))}")
    p_unresolved = sum(1 for q in pq.values() if not q)
    lines += [f"People: {len(people)} entries, {len(pq) - p_unresolved} with a Wikidata item, {p_unresolved} without (no ORCID match).", ""]

    def section(title: str, items: list[str]) -> None:
        lines.append(f"## {title} ({len(items)})")
        lines.append("")
        lines.extend(items or ["- none"])
        lines.append("")

    section("Institutions: facts that differ", differ)
    section("Institutions: facts Wikidata has and the site could pull", pull)
    section("Institutions: facts the site has and Wikidata lacks (write-back candidates)", push)
    section("Institutions without a Wikidata item", [f"- {s}" for s in unresolved])
    section("People: facts that differ", p_differ)
    section("People: facts Wikidata has and the site could pull", p_pull)
    section("People: facts the site has and Wikidata lacks (write-back candidates)", p_push)

    text = "\n".join(lines)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
