#!/usr/bin/env python3
"""Data for the term atlas lab page (/lab/term-atlas/), from Termportalen.

Reads every concept of Termportalen's termbase for artificial intelligence
(CC0) and the entries of site/_data/terms.yml (UHR's termbase, CC BY 4.0, and
the centre's own choices), and writes site/lab/term-atlas/terms.json with, per
concept:

- the term in Bokmål, Nynorsk and English, and the definitions Termportalen gives;
- links: which other concepts its Bokmål definition uses (whole words, with
  up to four letters of inflection), for the web of definitions;
- the distance between the Bokmål and the Nynorsk term (identical, a small
  change, a different word) and what Apertium makes of the Bokmål term, for
  the Bokmål and Nynorsk view;
- the Bokmål pages of mishmash.no that use the term.

Termportalen has no open API; the concept pages are read one a second, as in
fetch_terms_termportalen.py. The list of AI concepts is read from the
termbase's own page (the concepts it links to); a concept that page does not
link to is missed, and the count is printed.

    python3 scripts/build_term_atlas.py
"""
from __future__ import annotations

import difflib
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
from fetch_terms_termportalen import BASE, nuxt_data, parse_concept
from build_nynorsk import Translator, strip_marks, strip_links

OUT = SITE_ROOT / "lab" / "term-atlas" / "terms.json"
TERMS = SITE_ROOT / "_data" / "terms.yml"
UA = "mishmash.no term atlas (https://mishmash.no/lab/term-atlas/; contact@mishmash.no)"


def ki_concept_ids(session: requests.Session) -> list[str]:
    ids: set[str] = set()
    for page in (1, 2, 3):
        r = session.get(f"{BASE}/KI", params={"page": page} if page > 1 else None, timeout=60)
        ids |= set(re.findall(r'/tb/KI/([^"\s<?#]+)', r.text))
        time.sleep(1)
    return sorted(ids)


def first(labels: dict, lang: str) -> str:
    return " ".join((labels.get(lang) or [""])[0].split())


def kind_of(nb: str, nn: str) -> str:
    if nb.lower() == nn.lower():
        return "same"
    return "close" if difflib.SequenceMatcher(None, nb.lower(), nn.lower()).ratio() >= 0.7 else "different"


def main() -> int:
    session = requests.Session()
    session.headers["User-Agent"] = UA
    concepts: list[dict] = []

    ids = ki_concept_ids(session)
    print(f"AI termbase: {len(ids)} concepts linked from the termbase page")
    for cid in ids:
        url = f"{BASE}/KI/{cid}"
        time.sleep(1)
        r = session.get(url, timeout=60)
        c = parse_concept(nuxt_data(r.text), f"KI-3A{cid}") if r.status_code == 200 else None
        if not c or not first(c["pref"], "nb"):
            print(f"  skipped: {cid}")
            continue
        if first(c["pref"], "nb").lower() in {x["nb"].lower() for x in concepts}:
            print(f"  same Bokmål term as an earlier concept, kept once: {cid}")
            continue
        concepts.append({
            "id": "ki-" + cid.lower(), "source": "termportalen-ki", "licence": "CC0", "url": url,
            "nb": first(c["pref"], "nb"), "nn": first(c["pref"], "nn"), "en": first(c["pref"], "en"),
            "definition": {k: v for k, v in c["def"].items() if k in ("nb", "nn", "en")},
        })

    seen = {x["nb"].lower() for x in concepts}
    urls = {x["url"] for x in concepts}
    for e in yaml.safe_load(TERMS.read_text(encoding="utf-8")) or []:
        if not e.get("nn") or e["nb"].lower() in seen or (e.get("url") and e["url"] in urls):
            continue
        concepts.append({
            "id": "term-" + re.sub(r"\W+", "-", e["nb"].lower()).strip("-"),
            "source": e.get("source", ""), "licence": e.get("licence", "CC0" if e.get("source") == "centre" else ""),
            "url": e.get("url", ""), "nb": e["nb"], "nn": e["nn"], "en": e.get("en", ""),
            "definition": e.get("definition") or {},
        })

    # The web of definitions: concept A uses concept B when B's Bokmål term
    # occurs in A's Bokmål definition as a whole word, inflected or not.
    pats = {c["id"]: re.compile(r"(?<!\w)" + re.escape(c["nb"].lower()) + r"\w{0,4}(?!\w)") for c in concepts}
    for c in concepts:
        text = (c["definition"].get("nb") or "").lower()
        c["uses"] = sorted(o["id"] for o in concepts if o["id"] != c["id"] and pats[o["id"]].search(text))

    # Bokmål and Nynorsk, and what the machine makes of it.
    tr = Translator()
    for c in concepts:
        if not c["nn"]:
            continue
        c["kind"] = kind_of(c["nb"], c["nn"])
        c["apertium"] = " ".join(strip_marks(tr.translate(c["nb"])).split())
        c["apertium_ok"] = c["apertium"].lower() == c["nn"].lower()

    # Pages of mishmash.no that use the term, from the Bokmål sources.
    pages = []
    for f in sorted((SITE_ROOT / "no").rglob("index.md")):
        if "internal" in f.parts:
            continue
        text = f.read_text(encoding="utf-8")
        m = re.search(r"^permalink:\s*(\S+)", text, re.M)
        title = re.search(r"^title:\s*\"?(.+?)\"?\s*$", text, re.M)
        url = m.group(1) if m else "/" + f.relative_to(SITE_ROOT).parent.as_posix() + "/"
        pages.append((url, title.group(1) if title else url, strip_links(text).lower()))
    for c in concepts:
        rx = re.compile(r"(?<!\w)" + re.escape(c["nb"].lower()) + r"\w{0,4}(?!\w)")
        c["pages"] = [{"url": u, "title": t} for u, t, body in pages if rx.search(body)][:8]

    data = {
        "generated": date.today().isoformat(),
        "sources": {
            "termportalen-ki": {"name": "Termportalen: Kunstig intelligens", "url": f"{BASE}/KI", "licence": "CC0"},
            "uhr-termbase": {"name": "Termportalen: Universitets- og høgskolerådets termbase", "url": f"{BASE}/UHR", "licence": "CC BY 4.0"},
            "centre": {"name": "MishMash", "url": "https://mishmash.no/", "licence": "CC0"},
        },
        "concepts": concepts,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    links = sum(len(c["uses"]) for c in concepts)
    kinds = {k: sum(1 for c in concepts if c.get("kind") == k) for k in ("same", "close", "different")}
    wrong = sum(1 for c in concepts if c.get("apertium_ok") is False)
    print(f"concepts {len(concepts)}, definition links {links}, nb/nn {kinds}, Apertium differs from the listed term {wrong}")
    print(f"written: {OUT.relative_to(SITE_ROOT.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
