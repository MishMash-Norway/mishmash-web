#!/usr/bin/env python3
"""Fill the term list from Termportalen (issue #78, phase 1).

site/_data/terms.yml holds the centre's everyday vocabulary in English, Bokmål
and Nynorsk. A person adds an entry with its Bokmål term; this script looks the
term up in the termbases on Termportalen (UiB), in the order of TERMBASES below,
and fills in the English and Nynorsk terms, the definition, the source and a
link to the entry. An entry whose source is `centre` was decided by hand and is
never touched; an entry already filled from Termportalen is refreshed only with
--refresh.

Termportalen has no open API, so the script reads the concept's own page, one
request a second, the way a browser would. A concept is found by its name: the
Bokmål term with a capital first letter, or with "(1)" after it where the
termbase has several senses. A term that is not found is left for a person.

Licences: UHR's termbase is CC BY 4.0 (attribution by the source and link on
each entry), the AI termbase is CC0.

    python3 scripts/fetch_terms_termportalen.py            # fill new entries
    python3 scripts/fetch_terms_termportalen.py --refresh  # re-read every entry from Termportalen
    python3 scripts/fetch_terms_termportalen.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

TERMS = SITE_ROOT / "_data" / "terms.yml"
BASE = "https://www.termportalen.no/tb"
# Termbase id on Termportalen, the source key written to terms.yml, licence.
TERMBASES = [("UHR", "uhr-termbase", "CC BY 4.0"), ("KI", "termportalen-ki", "CC0")]
HEADER = """\
# The centre's everyday vocabulary in English, Bokmål and Nynorsk (issue #78).
#
# Add an entry with `nb` (and `en` if you know it); scripts/fetch_terms_termportalen.py
# fills `en`, `nn`, `definition`, `source`, `url` and `checked` from Termportalen:
# UHR's termbase for higher education (CC BY 4.0) first, then the AI termbase
# (CC0). `source: centre` marks a term decided by hand, with the reason in `note`;
# the script never changes those. `nn_alternatives` are accepted Nynorsk forms
# the site does not use. scripts/build_nynorsk.py reads `nb` and `nn` so the
# Nynorsk pages use the listed term.
"""


def concept_id(term: str, sense: int | None = None) -> str:
    """Termportalen's page name for a concept: capital first letter, spaces as
    underscores, other punctuation as -XX hex (Semantic MediaWiki style)."""
    name = term[:1].upper() + term[1:]
    if sense:
        name += f" ({sense})"
    out = []
    for ch in name:
        if ch == " ":
            out.append("_")
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append("".join(f"-{b:02X}" for b in ch.encode("utf-8")))
    return "".join(out)


def nuxt_data(html: str) -> list:
    m = re.search(r'id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else []


def parse_concept(data: list, cid: str) -> dict | None:
    """Labels and definitions of the concept, by language, from the page's data.

    The page data is a flat array where an integer is a reference to another
    element. Labels are objects with an @id such as
    '<base>-3A<concept>-23prefLabel_nn_1' and a literalForm {'@language', '@value'};
    definitions have an @id ending in 'definisjon_<lang>' and a label."""
    def val(x):
        return data[x] if isinstance(x, int) and 0 <= x < len(data) else x

    found = {"pref": {}, "alt": {}, "def": {}}
    for el in data:
        if not isinstance(el, dict) or "@id" not in el:
            continue
        ident = val(el["@id"])
        if not isinstance(ident, str) or cid not in ident:
            continue
        m = re.search(r"-23(prefLabel|altLabel)_([a-z\-]+)_\d+$", ident)
        d = re.search(r"-23definisjon_([a-z\-]+)$", ident)
        if m and "literalForm" in el:
            lit = val(el["literalForm"])
            text = val(lit.get("@value")) if isinstance(lit, dict) else None
            if isinstance(text, str):
                found["pref" if m.group(1) == "prefLabel" else "alt"].setdefault(m.group(2), []).append(text.strip())
        elif d and "label" in el:
            lab = val(el["label"])
            text = val(lab.get("@value")) if isinstance(lab, dict) else None
            if isinstance(text, str):
                found["def"][d.group(1)] = " ".join(text.split())
    return found if found["pref"] else None


def lookup(term: str, session: requests.Session) -> dict | None:
    for tb, source, licence in TERMBASES:
        for sense in (None, 1):
            cid = concept_id(term, sense)
            url = f"{BASE}/{tb}/{cid}"
            time.sleep(1)
            r = session.get(url, timeout=60)
            if r.status_code != 200:
                continue
            c = parse_concept(nuxt_data(r.text), f"{tb}-3A{cid}")
            if not c:
                continue
            nb = c["pref"].get("nb", [])
            if term.lower() not in [x.lower() for x in nb + c["alt"].get("nb", [])]:
                continue
            return {"concept": c, "source": source, "licence": licence, "url": url}
    return None


def fill(entry: dict, hit: dict) -> dict:
    c = hit["concept"]
    out = dict(entry)
    if c["pref"].get("en"):
        out["en"] = c["pref"]["en"][0]
    if c["pref"].get("nn"):
        out["nn"] = c["pref"]["nn"][0]
        alts = [x for x in c["pref"]["nn"][1:] + c["alt"].get("nn", []) if x != out["nn"]]
        if alts:
            out["nn_alternatives"] = sorted(set(alts))
    definition = {k: v for k, v in c["def"].items() if k in ("nb", "nn", "en")}
    if definition:
        out["definition"] = definition
    out["source"] = hit["source"]
    out["licence"] = hit["licence"]
    out["url"] = hit["url"]
    out["checked"] = date.today().isoformat()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-read entries already filled from Termportalen")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries = yaml.safe_load(TERMS.read_text(encoding="utf-8")) or []
    session = requests.Session()
    session.headers["User-Agent"] = "mishmash.no term list (https://mishmash.no/; contact@mishmash.no)"
    found = missing = skipped = 0
    for i, e in enumerate(entries):
        if e.get("source") == "centre" or (e.get("source") and not args.refresh):
            skipped += 1
            continue
        hit = lookup(e["nb"], session)
        if not hit:
            missing += 1
            print(f"  not found: {e['nb']}")
            continue
        entries[i] = fill(e, hit)
        found += 1
        print(f"  {e['nb']} → nn {entries[i].get('nn')!r}, en {entries[i].get('en')!r} ({hit['source']})")
    print(f"found {found}, not found {missing}, left alone {skipped}")
    if not args.dry_run:
        TERMS.write_text(HEADER + "\n" + yaml.safe_dump(entries, allow_unicode=True, sort_keys=False, width=1000),
                         encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
