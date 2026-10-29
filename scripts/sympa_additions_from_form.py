#!/usr/bin/env python3
"""List who should be added to the WP mailing lists, from a participation-form export.

Reads the newest participation-form xlsx in temp/ (or --xlsx), keeps the rows
submitted on or after --since, and writes one file per work package list (wp1@ to wp7@), temp/sympa-add-<list>.txt, in the "email name" format
that Sympa's "Add subscribers" page accepts (Manage subscribers → Add
subscribers, at https://sympa.uio.no/mishmash.no/add_request/wpN). People
already on a list according to the newest temp/wpN@mishmash.no.txt export
are left out.

Everyone who submits the form goes on the lists. The question about the
directory only decides whether the person is shown on the website.

A person who submitted the form more than once is listed once on each list. A name written
all in capitals or all in lower case is capitalised.

A name submitted as a first name only is replaced by the full name of the
directory entry that has it as an alias, so the lists carry the same name as
the website.

    python3 scripts/sympa_additions_from_form.py --since 2026-09-08
    python3 scripts/sympa_additions_from_form.py --since 2026-09-08 --open

With --open the script goes through the lists one at a time: it puts the
list's block on the clipboard, opens the list's "Add subscribers" page in the
browser, and waits for Enter before the next list. Paste into the box, press
Add, and come back to the terminal. xclip is used when it is installed;
without it the clipboard is held by Tk, and the script must stay running
until the last paste.

The same additions are also written as sympaadmin commands to
temp/sympa-commands.txt, one "add" line per person and list. sympaadmin is
UiO's command-line client for Sympa and is installed on login.uio.no; it adds
members through Sympa's SOAP interface as the list owner, with no browser:

    ssh -t login.uio.no sympaadmin < temp/sympa-commands.txt

It reads ~/.sympaadmin.ini on login.uio.no (soapuser = the owner address,
soapserver = https://sympa.uio.no/mishmash.no-sympasoap for the mishmash.no
lists) and asks for the UiO password. "list admin" shows which lists it sees.

The script itself sends nothing to Sympa.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from directory_io import load_entry
from repo_paths import SITE_ROOT

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


def full_names_by_alias() -> dict[str, str]:
    names = {}
    for index_md in (SITE_ROOT / "_directory" / "people").glob("*/index.md"):
        data, _ = load_entry(index_md)
        for alias in data.get("aliases") or []:
            if data.get("name"):
                names[str(alias).strip().lower()] = data["name"]
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", type=Path, help="Form export (default: newest temp/data-625226-*.xlsx)")
    ap.add_argument("--since", type=lambda s: datetime.fromisoformat(s), help="Only submissions on/after this date (YYYY-MM-DD)")
    ap.add_argument("--open", action="store_true", help="Open each list's Add subscribers page with its block on the clipboard, one list at a time")
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
    wp_cols = {}
    for i, h in enumerate(headers):
        if h.startswith("Work Package(s) you are interested in joining.WP"):
            wp_cols[h.split(".")[-1][:3]] = i

    by_alias = full_names_by_alias()
    seen: set[tuple[str, str]] = set()
    # all@ is built in Sympa from the work package lists, so it is never added
    # to directly. Someone who ticked no work package reaches no list at all,
    # and is named at the end instead.
    per_list: dict[str, list[tuple[str, str]]] = {wp: [] for wp in sorted(wp_cols)}
    no_wp: list[tuple[str, str]] = []
    skipped_existing = 0
    for row in rows:
        created = row[c_created]
        if isinstance(created, str):
            created = datetime.fromisoformat(created[:19])
        if args.since and created and created < args.since:
            continue
        name = str(row[c_name] or "").strip()
        name = by_alias.get(name.lower(), name)
        if name.isupper() or name.islower():
            name = name.title()
        email = str(row[c_email] or "").strip().lower()
        if not email:
            continue
        if not any(row[idx] for idx in wp_cols.values()) and (email, name) not in no_wp:
            no_wp.append((email, name))
        for wp, idx in wp_cols.items():
            if row[idx]:
                if email in existing_members(wp):
                    skipped_existing += 1
                    continue
                if (email, wp) in seen:
                    continue
                seen.add((email, wp))
                per_list[wp].append((email, name))

    TEMP.mkdir(exist_ok=True)
    total = 0
    commands = [f"add {email} {wp.lower()}@mishmash.no\n" for wp, members in per_list.items() for email, _ in members]
    (TEMP / "sympa-commands.txt").write_text("".join(commands), encoding="utf-8")
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
    if total:
        print("sympaadmin commands: temp/sympa-commands.txt  →  ssh -t login.uio.no sympaadmin < temp/sympa-commands.txt")
    if no_wp:
        print(f"\n{len(no_wp)} ticked no work package, so they reach no list (all@ is built from the WP lists):")
        for email, name in no_wp:
            print(f"  {email} {name}")
    if args.open and total:
        open_pages(per_list)
    return 0


def open_pages(per_list: dict) -> None:
    """One list at a time: block on the clipboard, add page in the browser, wait for Enter.

    xclip holds the clipboard by itself when it is installed. Without it the
    text is held by Tk, which only works while this script keeps answering
    the browser's requests, so the wait for Enter pumps Tk's events.
    """
    import select
    import shutil
    import subprocess
    xclip = shutil.which("xclip")
    clip = None
    if not xclip:
        import tkinter
        clip = tkinter.Tk()
        clip.withdraw()
    todo = [(wp, m) for wp, m in per_list.items() if m]
    for i, (wp, members) in enumerate(todo, 1):
        url = f"https://sympa.uio.no/mishmash.no/add_request/{wp.lower()}"
        block = "".join(f"{email} {name}\n" for email, name in members)
        if xclip:
            subprocess.run([xclip, "-selection", "clipboard"], input=block.encode("utf-8"), check=True)
        else:
            clip.clipboard_clear()
            clip.clipboard_append(block)
            clip.update()
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n[{i}/{len(todo)}] {wp.lower()}@mishmash.no: {len(members)} on the clipboard, page opened. Paste into the box and press Add.")
        print("Press Enter for the next list... " if i < len(todo) else "Press Enter when the last one is added... ", end="", flush=True)
        while not select.select([sys.stdin], [], [], 0.05)[0]:
            if clip:
                clip.update()
        sys.stdin.readline()
    if clip:
        clip.destroy()


if __name__ == "__main__":
    sys.exit(main())
