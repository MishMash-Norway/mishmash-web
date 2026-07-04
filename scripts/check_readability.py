#!/usr/bin/env python3
"""Readability checks for adaptive reading levels.

Scans site pages with `adaptive: true` front matter, extracts the
<div class="adaptive" data-for="..."> variant blocks, and

1. warns when a heading section covers some reading levels but not all
   (a level with no block sees nothing for that section), and
2. computes a LIX readability score per level per page and warns when
   the levels are not ordered simple <= standard <= advanced.

LIX = words/sentences + 100 * longwords(>6 chars)/words works for both
Norwegian and English. Guidance: <30 easy, 40-50 difficult, >60 very
difficult.

Non-blocking by default (exit 0); use --strict to exit 1 on warnings.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

from repo_paths import SITE_ROOT

BLOCK_RE = re.compile(
    r'<div class="adaptive" data-for="([^"]+)"[^>]*>(.*?)</div>', re.S
)
HEADING_RE = re.compile(r"^##\s+(.+)$", re.M)


def load_levels(root: Path) -> list[str]:
    data = yaml.safe_load((root / "_data" / "audiences.yml").read_text(encoding="utf-8"))
    return [g["key"] for g in data["groups"]]


def strip_reference_section(text: str) -> str:
    """Drop a trailing References/Referanser section — bibliography
    entries are not prose and skew the LIX score."""
    return re.split(
        r"^##\s+(?:References|Referanser)\b.*$", text, maxsplit=1, flags=re.M | re.I
    )[0]


def strip_markup(text: str) -> str:
    text = re.sub(r"\{%.*?%\}", " ", text, flags=re.S)  # liquid tags/includes
    text = re.sub(r"\{\{.*?\}\}", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)  # html
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> text
    text = re.sub(r"\{:[^}]*\}", " ", text)  # kramdown attribute lists
    text = re.sub(r"[*_`#>|-]", " ", text)
    return text


def lix(text: str) -> float | None:
    words = re.findall(r"[A-Za-zÆØÅæøåÉéÈè0-9']+", text)
    if len(words) < 20:
        return None
    sentences = max(1, len(re.findall(r"[.!?:]+(?:\s|$)", text)))
    long_words = sum(1 for w in words if len(w) > 6)
    return len(words) / sentences + 100 * long_words / len(words)


def adaptive_pages(root: Path):
    for path in root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(fm, dict) and fm.get("adaptive"):
            yield path, text[m.end():]


def check_page(path: Path, body: str, levels: list[str], warnings: list[str]) -> dict:
    # Section coverage: between consecutive ## headings, adaptive blocks
    # should cover every level (or none at all).
    sections = re.split(HEADING_RE, body)
    # re.split with one capture group yields [pre, title1, body1, title2, ...]
    for i in range(1, len(sections), 2):
        title, section = sections[i].strip(), sections[i + 1]
        covered = {
            level
            for match in BLOCK_RE.finditer(section)
            for level in match.group(1).split()
        }
        missing = [lv for lv in levels if lv not in covered]
        if covered and missing:
            warnings.append(
                f"{path}: section '{title}' has adaptive blocks but no "
                f"variant for: {', '.join(missing)}"
            )

    # LIX per level over the whole page.
    per_level: dict[str, str] = {lv: "" for lv in levels}
    for match in BLOCK_RE.finditer(body):
        for level in match.group(1).split():
            if level in per_level:
                per_level[level] += " " + strip_reference_section(match.group(2))
    return {lv: lix(strip_markup(t)) for lv, t in per_level.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 on warnings")
    args = parser.parse_args()

    root = SITE_ROOT
    levels = load_levels(root)
    warnings: list[str] = []
    found = False

    for path, body in sorted(adaptive_pages(root)):
        found = True
        scores = check_page(path, body, levels, warnings)
        shown = "  ".join(
            f"{lv}={scores[lv]:.0f}" if scores[lv] is not None else f"{lv}=n/a"
            for lv in levels
        )
        print(f"{path.relative_to(root.parent)}: LIX {shown}")
        ordered = [scores[lv] for lv in levels if scores[lv] is not None]
        if any(b < a - 2 for a, b in zip(ordered, ordered[1:])):
            warnings.append(
                f"{path}: readability not increasing with level ({shown}) — "
                "a simpler level reads harder than a more advanced one"
            )

    if not found:
        print("No adaptive pages found.")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
        return 1 if args.strict else 0
    print("\nOK: adaptive readability checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
