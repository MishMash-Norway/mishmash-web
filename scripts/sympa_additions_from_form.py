#!/usr/bin/env python3
"""List who should be added to the WP mailing lists, from a participation-form export.

Reads the newest participation-form xlsx in temp/ (or --xlsx), keeps the rows
that consented to the directory and were submitted on or after --since, and
writes one file per list (all@ and wp1@ to wp7@), temp/sympa-add-<list>.txt, in the "email name" format
that Sympa's "Add subscribers" page accepts (Manage subscribers → Add
subscribers, at https://sympa.uio.no/mishmash.no/add_request/wpN). People
already on a list according to the newest temp/wpN@mishmash.no.txt export
are left out.

    python3 scripts/sympa_additions_from_form.py --since 2026-09-08

Nothing is sent to Sympa; adding members needs a list owner's login.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("openpyxl is required: pip install openpyxl")

ROOT = Path(__file__).resolve().parent.parent
TEMP = ROOT / "temp"


def newest_participation_xlsx() -> Path | None:
    files = sorted(TEMP.glob("data-625226-*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def existing_members(wp: str) -> set[str]:
    path = TEMP / f"{wp.lower()}@mishmash.no.txt"
    if not path.exists():
        return set()
    return {line.split("\t")[0].strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if "@" in line}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", type=Path, help="Form export (default: newest temp/data-625226-*.xlsx)")
    ap.add_argument("--since", type=lambda s: datetime.fromisoformat(s), help="Only submissions on/after this date (YYYY-MM-DD)")
    ap.add_argument("--all", action="store_true", help="Include people who did not answer Yes to the directory question")
    args = ap.parse_args()

    xlsx = args.xlsx or newest_participation_xlsx()
    if not xlsx or not xlsx.exists():
        sys.exit("No participation-form export found; run scripts/fetch_nettskjema_export.py first.")
    ws = load_workbook(xlsx, read_only=True).worksheets[0]
    rows = ws.iter_rows(values_only=True)
    headers = [str(h or "").strip() for h in next(rows)]

    def col(prefix: str) -> int:
        for i, h in enumerate(headers):
            if h.lower().startswith(prefix.lower()):
                return i
        sys.exit(f"Column starting with '{prefix}' not found in {xlsx}")

    c_created, c_name, c_email = col("$created"), col("Name"), col("Email")
    c_consent = col("Do you want to be added")
    wp_cols = {}
    for i, h in enumerate(headers):
        if h.startswith("Work Package(s) you are interested in joining.WP"):
            wp_cols[h.split(".")[-1][:3]] = i

    per_list: dict[str, list[tuple[str, str]]] = {"ALL": []}
    per_list.update({wp: [] for wp in sorted(wp_cols)})
    skipped_existing = 0
    for row in rows:
        created = row[c_created]
        if isinstance(created, str):
            created = datetime.fromisoformat(created[:19])
        if args.since and created and created < args.since:
            continue
        if not args.all and str(row[c_consent] or "").strip().lower() != "yes":
            continue
        name = str(row[c_name] or "").strip()
        email = str(row[c_email] or "").strip().lower()
        if not email:
            continue
        if email not in existing_members("all"):
            per_list["ALL"].append((email, name))
        for wp, idx in wp_cols.items():
            if row[idx]:
                if email in existing_members(wp):
                    skipped_existing += 1
                    continue
                per_list[wp].append((email, name))

    TEMP.mkdir(exist_ok=True)
    total = 0
    for wp, members in per_list.items():
        if not members:
            continue
        out = TEMP / f"sympa-add-{wp.lower()}.txt"
        out.write_text("".join(f"{email} {name}\n" for email, name in members), encoding="utf-8")
        print(f"\n{wp.lower()}@mishmash.no  ({len(members)})  → https://sympa.uio.no/mishmash.no/add_request/{wp.lower()}")
        for email, name in members:
            print(f"  {email} {name}")
        total += len(members)
    print(f"\n{total} additions written to temp/sympa-add-wpN.txt; {skipped_existing} already subscribed (per the list exports in temp/).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
