#!/usr/bin/env python3
"""Compare agent reviews of the generated Nynorsk with each other and with a person (issue #78, phase 2).

The review folder (default temp/nynorsk-review/) holds pages/<id>/nb.md and
nn.md, a frozen copy of the Bokmål source and the generated Nynorsk, and one
agent-<label>.json per agent, each a list of marks with page, sentence, span,
category, correction and confidence (see INSTRUCTIONS.md there).

Each mark is located in nn.md as a character range: the span, searched for
inside its sentence. Two marks agree when their ranges on the same page
overlap. A cluster of overlapping marks from N or more different agents is an
agreed mark at threshold N.

The person's answer key is the corrected page itself: a copy of nn.md saved as
pages/<id>/nn-reviewed.md with the corrections made in place. The ranges of
nn.md that the person changed are the errors. Then:

    recall    = the person's changes that an agreed mark overlaps / all of them
    precision = agreed marks that overlap a change by the person / all agreed marks

reported per threshold, per agent alone, and per category. A corrected page
is also the reviewed page for site/nn/, so the key costs no extra work.

    python3 scripts/compare_nynorsk_reviews.py                 # agreement, and the comparison if keys exist
    python3 scripts/compare_nynorsk_reviews.py --dir temp/nynorsk-review
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def locate(text: str, sentence: str, span: str) -> tuple[int, int] | None:
    """Character range of the span in the page, found inside its sentence."""
    s = text.find(sentence) if sentence else -1
    if s >= 0:
        k = sentence.find(span) if span else -1
        if k >= 0:
            return s + k, s + k + len(span)
        return s, s + len(sentence)
    k = text.find(span) if span else -1
    return (k, k + len(span)) if k >= 0 else None


def overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def clusters(marks: list[dict]) -> list[list[dict]]:
    """Group overlapping marks on one page, transitively."""
    marks = sorted(marks, key=lambda m: m["range"])
    out: list[list[dict]] = []
    end = -1
    for m in marks:
        if out and m["range"][0] < end:
            out[-1].append(m)
            end = max(end, m["range"][1])
        else:
            out.append([m])
            end = m["range"][1]
    return out


def human_changes(original: str, reviewed: str) -> list[tuple[int, int]]:
    """Ranges of the original that the person replaced or deleted; an insertion
    counts as a one-character range at its position."""
    sm = difflib.SequenceMatcher(None, original, reviewed, autojunk=False)
    ranges = []
    for op, i1, i2, _, _ in sm.get_opcodes():
        if op == "equal":
            continue
        ranges.append((i1, max(i2, i1 + 1)))
    # merge changes within a few characters of each other: one correction
    merged: list[list[int]] = []
    for a, b in ranges:
        if merged and a - merged[-1][1] <= 3:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [tuple(x) for x in merged]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, default=ROOT / "temp" / "nynorsk-review")
    args = ap.parse_args()
    d = args.dir
    pages = {p.name: (p / "nn.md").read_text(encoding="utf-8") for p in sorted((d / "pages").iterdir()) if (p / "nn.md").exists()}
    agents = sorted(f.stem[len("agent-"):] for f in d.glob("agent-*.json"))
    if not agents:
        sys.exit(f"no agent-*.json in {d}")

    marks: list[dict] = []
    unplaced = Counter()
    for a in agents:
        for m in json.loads((d / f"agent-{a}.json").read_text(encoding="utf-8")):
            text = pages.get(m.get("page"))
            r = locate(text, m.get("sentence", ""), m.get("span", "")) if text else None
            if not r:
                unplaced[a] += 1
                continue
            marks.append({**m, "agent": a, "range": r})

    print(f"agents: {', '.join(agents)}; pages: {len(pages)}")
    for a in agents:
        n = sum(1 for m in marks if m["agent"] == a)
        print(f"  {a}: {n} marks placed, {unplaced[a]} not found in the page text")

    by_page = defaultdict(list)
    for m in marks:
        by_page[m["page"]].append(m)
    agreed: list[dict] = []
    for page, ms in by_page.items():
        for c in clusters(ms):
            who = sorted({m["agent"] for m in c})
            agreed.append({
                "page": page,
                "range": [min(m["range"][0] for m in c), max(m["range"][1] for m in c)],
                "agents": who,
                "n": len(who),
                "text": pages[page][min(m["range"][0] for m in c):max(m["range"][1] for m in c)],
                "categories": sorted({m.get("category", "") for m in c}),
                "proposals": [{"agent": m["agent"], "span": m.get("span"), "correction": m.get("correction"),
                               "confidence": m.get("confidence"), "note": m.get("note")} for m in c],
            })
    agreed.sort(key=lambda c: (c["page"], c["range"]))
    print("\nproblems by number of agents that marked them:")
    for k in range(len(agents), 0, -1):
        print(f"  {k} of {len(agents)}: {sum(1 for c in agreed if c['n'] == k)}")
    (d / "agreed.json").write_text(json.dumps(agreed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written: {(d / 'agreed.json').relative_to(ROOT) if d.is_relative_to(ROOT) else d / 'agreed.json'}")

    keys = {p: (d / "pages" / p / "nn-reviewed.md") for p in pages}
    keys = {p: f for p, f in keys.items() if f.exists()}
    if not keys:
        print("\nno nn-reviewed.md yet: recall and precision need the person's corrected pages")
        return 0
    changes = {p: human_changes(pages[p], f.read_text(encoding="utf-8")) for p, f in keys.items()}
    total = sum(len(v) for v in changes.values())
    print(f"\nanswer key: {len(keys)} pages, {total} corrections by the person")

    def score(selected: list[dict]) -> tuple[float, float, int]:
        sel = [c for c in selected if c["page"] in keys]
        hit_changes = sum(1 for p, ch in changes.items() for r in ch
                          if any(c["page"] == p and overlaps(tuple(c["range"]), r) for c in sel))
        good = sum(1 for c in sel if any(overlaps(tuple(c["range"]), r) for r in changes[c["page"]]))
        return (hit_changes / total if total else 0.0, good / len(sel) if sel else 0.0, len(sel))

    print("threshold    marks   recall   precision")
    for k in range(1, len(agents) + 1):
        rec, prec, n = score([c for c in agreed if c["n"] >= k])
        print(f"  {k}+ agents  {n:5d}   {rec:6.0%}   {prec:9.0%}")
    for a in agents:
        rec, prec, n = score([{"page": m["page"], "range": list(m["range"])} for m in marks if m["agent"] == a])
        print(f"  {a:10s} {n:5d}   {rec:6.0%}   {prec:9.0%}")
    cats = Counter()
    good = Counter()
    for c in agreed:
        if c["n"] < 2 or c["page"] not in keys:
            continue
        for cat in c["categories"]:
            cats[cat] += 1
            if any(overlaps(tuple(c["range"]), r) for r in changes[c["page"]]):
                good[cat] += 1
    print("precision by category, 2+ agents:")
    for cat, n in cats.most_common():
        print(f"  {cat:16s} {good[cat]}/{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
