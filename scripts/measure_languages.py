#!/usr/bin/env python3
"""Measure how much of the site's text is in Bokmål, Nynorsk and English.

Språkrådet measures state websites with the Målfrid crawler, which counts
words per language in the harvested pages. This script does the same on the
site's own sources before the build: every page and collection document
(except the internal pages and the interface themes, which search engines do
not index either) is stripped of front matter, Liquid, HTML and Markdown,
split into paragraphs, and each paragraph of five words or more is classified
with a language detector that tells Bokmål and Nynorsk apart. Words are
counted by detected language, and pages whose detected language disagrees
with the language they declare are listed for a maintainer.

The result goes to site/_data/language_share.yml (ignored by git) and is shown
on /about/languages/.

Usage:
  python3 scripts/measure_languages.py
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

OUT = SITE_ROOT / "_data" / "language_share.yml"
SKIP_PARTS = {"_site", "_includes", "_layouts", "_data", "_sass", "assets", "internal", "ui", "chat", "node_modules"}
CODES = {"BOKMAL": "nb", "NYNORSK": "nn", "ENGLISH": "en"}
MIN_WORDS = 5

STRIP = [
    (re.compile(r"```.*?```", re.S), " "),
    (re.compile(r"\{%-?.*?-?%\}", re.S), " "),
    (re.compile(r"\{\{.*?\}\}", re.S), " "),
    (re.compile(r"<script.*?</script>", re.S | re.I), " "),
    (re.compile(r"<style.*?</style>", re.S | re.I), " "),
    (re.compile(r"<[^>]+>", re.S), " "),
    (re.compile(r"`[^`\n]*`"), " "),
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), " "),
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"https?://\S+"), " "),
    (re.compile(r"^\s{0,3}#{1,6}\s+", re.M), ""),
    (re.compile(r"^\s*[-*+]\s+|^\s*\d+\.\s+", re.M), ""),
    (re.compile(r"^\s*\|.*\|\s*$", re.M), " "),
    (re.compile(r"[*_>|]"), " "),
]


def split_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        data = {}
    return data, m.group(2)


def clean(body: str) -> str:
    for rx, rep in STRIP:
        body = rx.sub(rep, body)
    return body


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.split()) >= MIN_WORDS]


def declared_language(data: dict, rel: Path) -> str:
    lang = data.get("lang")
    if lang:
        return str(lang)
    if rel.parts and rel.parts[0] in ("no", "nn-auto", "nn"):
        return "nb" if rel.parts[0] == "no" else "nn"
    return "en"


def iter_sources(root: Path):
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix not in (".md", ".html"):
            continue
        rel = f.relative_to(root)
        if any(p in SKIP_PARTS for p in rel.parts):
            continue
        if any(p.startswith("_") and p not in ("_news", "_events", "_directory") for p in rel.parts[:-1]):
            continue
        if rel.parts[-1].startswith("_"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---"):
            continue
        data, body = split_front_matter(text)
        if data.get("published") is False or data.get("draft") is True:
            continue
        yield rel, data, body


def measure(root: Path, detect) -> dict:
    """detect(paragraph) -> 'nb' | 'nn' | 'en' | None."""
    words = Counter()
    pages = defaultdict(int)
    mismatches = []
    for rel, data, body in iter_sources(root):
        declared = declared_language(data, rel)
        per_page = Counter()
        for p in paragraphs(clean(body)):
            code = detect(p) or declared
            n = len(p.split())
            words[code] += n
            per_page[code] += n
        total = sum(per_page.values())
        if total:
            pages[declared] += 1
            own = per_page.get(declared, 0)
            if own / total < 0.7:
                mismatches.append({"page": rel.as_posix(), "declared": declared,
                                   "detected": {k: v for k, v in per_page.most_common()}})
    total = sum(words.values()) or 1
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "paragraphs of five words or more from the page sources, classified with the lingua language detector (Bokmål, Nynorsk, English); internal pages and interface themes excluded",
        "words": {k: words.get(k, 0) for k in ("nb", "nn", "en")},
        "share_percent": {k: round(100 * words.get(k, 0) / total, 1) for k in ("nb", "nn", "en")},
        "norwegian_share_percent": {
            "nb": round(100 * words.get("nb", 0) / ((words.get("nb", 0) + words.get("nn", 0)) or 1), 1),
            "nn": round(100 * words.get("nn", 0) / ((words.get("nb", 0) + words.get("nn", 0)) or 1), 1),
        },
        "pages": {k: pages.get(k, 0) for k in ("nb", "nn", "en")},
        "mismatches": mismatches,
    }


def lingua_detector():
    from lingua import Language, LanguageDetectorBuilder
    det = LanguageDetectorBuilder.from_languages(Language.BOKMAL, Language.NYNORSK, Language.ENGLISH).build()

    def detect(p: str):
        lang = det.detect_language_of(p)
        return CODES.get(lang.name) if lang else None
    return detect


def main() -> int:
    result = measure(SITE_ROOT, lingua_detector())
    OUT.write_text("# Generated by scripts/measure_languages.py. Do not edit.\n"
                   + yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    w = result["words"]
    print(f"languages: nb {w['nb']} words, nn {w['nn']}, en {w['en']}; "
          f"Norwegian text {result['norwegian_share_percent']['nn']} % Nynorsk; "
          f"{len(result['mismatches'])} pages disagree with their declared language")
    return 0


if __name__ == "__main__":
    sys.exit(main())
