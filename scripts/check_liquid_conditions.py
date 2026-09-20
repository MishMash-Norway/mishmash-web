#!/usr/bin/env python3
"""Catch the two Liquid conditions that do not mean what they look like.

Liquid has no operator precedence and no brackets. It reads a chain of `and` and
`or` from the right, one operator at a time. A chain of only `and`, or only `or`,
is safe because both are associative. A chain that mixes them is not:

    {% if a and a != '' or b and b != '' %}

reads as `a and (a != '' or (b and b != ''))`, so it demands `a` before it will
look at `b` at all. This shipped in the institution layout, where it asked for a
summary or a website or a Wikipedia link and actually required the summary. An
institution with no description lost its links as well as its prose.

The fix is to assign each test to a variable and combine the variables, one
operator per condition.

`where_exp` has the same problem and no way around it: its expression takes a
single comparison, and a filter written with `and` or `or` silently matches
nothing rather than failing.

Usage:
  python3 scripts/check_liquid_conditions.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TAG = re.compile(r"\{%-?\s*(if|elsif|unless)\s([^%]*?)-?%\}")
WHERE_EXP = re.compile(r"where_exp\s*:\s*(\"[^\"]*\"|'[^']*')\s*,\s*(\"[^\"]*\"|'[^']*')")


def offences(path: Path) -> list[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    found = []
    for number, line in enumerate(text.split("\n"), 1):
        for _, condition in TAG.findall(line):
            has_and = " and " in f" {condition} "
            has_or = " or " in f" {condition} "
            if has_and and has_or:
                found.append((number, "mixes and with or", condition.strip()[:100]))
        for _, expression in WHERE_EXP.findall(line):
            if " and " in expression or " or " in expression:
                found.append((number, "where_exp with a boolean", expression.strip()[:100]))
    return found


def main() -> int:
    tracked = subprocess.run(
        ["git", "ls-files", "site", "themes"], capture_output=True, text=True, check=True
    ).stdout.split()
    total = 0
    for name in sorted(tracked):
        if Path(name).suffix not in (".html", ".md", ".liquid"):
            continue
        found = offences(Path(name))
        if not found:
            continue
        print(f"\n{name}")
        for number, what, snippet in found:
            print(f"  {number:>4}  {what:<24} {snippet}")
        total += len(found)
    print(f"\n{total} condition{'' if total == 1 else 's'} that will not mean what it looks like")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
