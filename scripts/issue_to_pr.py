#!/usr/bin/env python3
"""Turn an accepted issue-form submission into a branch and a pull request.

The issue forms in .github/ISSUE_TEMPLATE/ let members send a news post, an
event or a MeshUp talk without git. A maintainer reads the issue, and when it
is fit to publish runs:

    python3 scripts/issue_to_pr.py 123            # branch, commit, push, open a PR
    python3 scripts/issue_to_pr.py 123 --dry-run  # only write the file and print it

The script reads the issue with the GitHub CLI (gh), works out which form it
came from by its label (news, event, meshup), writes the file the site
expects, and opens a pull request that closes the issue. Anything it could
not parse (a time, an end time) is left as a CHECK comment in the front
matter for the maintainer to settle before merging. A correction issue has
no automatic path: the script prints the source file of the page instead.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import yaml

from repo_paths import SITE_ROOT

NO_RESPONSE = "_No response_"


# ---------------------------------------------------------------- parsing --
def parse_form(body: str) -> dict[str, str]:
    """Return {field label: value} from the Markdown GitHub renders for a form."""
    fields: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("### "):
            if current is not None:
                fields[current] = "\n".join(buf).strip()
            current = line[4:].strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        fields[current] = "\n".join(buf).strip()
    return {k: ("" if v == NO_RESPONSE else v) for k, v in fields.items()}


def slugify(text: str, max_words: int = 6) -> str:
    for a, b in (("æ", "ae"), ("ø", "oe"), ("å", "aa"), ("Æ", "ae"), ("Ø", "oe"), ("Å", "aa")):
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    words = [w for w in re.sub(r"[^a-z0-9]+", " ", text.lower()).split() if w]
    return "-".join(words[:max_words]) or "untitled"


def first_sentence(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m else text
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
TIME_RE = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def parse_when(text: str) -> tuple[str | None, str | None, str | None, list[str]]:
    """Return (date, start_time, end_time, notes) from free text such as
    '2026-10-14 17:00 to 19:30 CEST'. Missing parts become notes."""
    notes = []
    d = DATE_RE.search(text or "")
    date = f"{d.group(1)}-{d.group(2)}-{d.group(3)}" if d else None
    times = [f"{int(h):02d}:{m}" for h, m in TIME_RE.findall(text or "")]
    start = times[0] if times else None
    end = times[1] if len(times) > 1 else None
    if not date:
        notes.append("date not found in the form; set date and end_date")
    if not start:
        notes.append("start time not found; check date")
    if not end:
        notes.append("end time not found; check end_date")
    return date, start, end, notes


def tz_offset(date: str) -> str:
    """Norway: CEST from the last Sunday of March to the last Sunday of October."""
    y, m, d = (int(x) for x in date.split("-"))
    day = dt.date(y, m, d)

    def last_sunday(month: int) -> dt.date:
        last = dt.date(y, month + 1, 1) - dt.timedelta(days=1) if month < 12 else dt.date(y, 12, 31)
        return last - dt.timedelta(days=(last.weekday() + 1) % 7)

    return "+02:00" if last_sunday(3) <= day < last_sunday(10) else "+01:00"


def yaml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


# -------------------------------------------------------------- rendering --
def render_news(fields: dict[str, str], today: dt.date) -> tuple[Path, str]:
    title = fields.get("Headline", "").strip() or "Untitled"
    text = fields.get("Text", "").strip()
    author = fields.get("Author", "").strip()
    images = fields.get("Images", "").strip()
    path = SITE_ROOT / "_news" / f"{today.isoformat()}-{slugify(title)}.md"
    front = [
        "---",
        f"title: {yaml_str(title)}",
        f"date: {today.isoformat()}",
        f"author: {yaml_str(author)}",
        "layout: page",
        "categories: [Announcement]",
        f"description: {yaml_str(first_sentence(text))}",
        "image: /assets/images/bubbles/mishmash_bubbles_notext.svg",
    ]
    if images:
        front.append("# CHECK: images were attached to the issue; download them to")
        front.append("# site/assets/images/news/<slug>/, add alt text, and set image: above.")
    front.append("---")
    body = text + "\n"
    if images:
        body += "\n<!-- Images from the form (attachments on the issue):\n" + images + "\n-->\n"
    return path, "\n".join(front) + "\n\n" + body


def render_event(fields: dict[str, str], today: dt.date) -> tuple[Path, str]:
    title = fields.get("Title", "").strip() or "Untitled event"
    date, start, end, notes = parse_when(fields.get("Date and time", ""))
    place = fields.get("Place", "").strip()
    link = fields.get("Link to the event page or registration", "").strip()
    desc = fields.get("Description", "").strip()
    date = date or today.isoformat()
    off = tz_offset(date)
    path = SITE_ROOT / "_events" / f"{date}-{slugify(title)}.md"
    front = [
        "---",
        f"title: {yaml_str(title)}",
        f"date: {date} {start or '12:00'}:00 {off}",
        f"end_date: {date} {end or start or '13:00'}:00 {off}",
        f"location: {yaml_str(place)}",
        "layout: event",
        "categories: [Event]",
        "tags: []",
        f"description: {yaml_str(first_sentence(desc))}",
        "image: /assets/images/bubbles/mishmash_bubbles_notext.svg",
        f"slug: {yaml_str(slugify(title))}",
    ]
    for n in notes:
        front.append(f"# CHECK: {n}")
    front.append("---")
    body = desc + "\n"
    if link:
        body += f"\n[More information and registration]({link})\n"
    return path, "\n".join(front) + "\n\n" + body


def render_partner_event(fields: dict[str, str], today: dt.date) -> tuple[Path, str]:
    """Append an entry to _data/partner_events.yml; returns the file and the new text."""
    title = fields.get("Title", "").strip() or "Untitled event"
    date, start, end, notes = parse_when(fields.get("Date and time", ""))
    date = date or today.isoformat()
    place = fields.get("Place", "").strip()
    link = fields.get("Link to the event page or registration", "").strip()
    desc = re.sub(r"\s+", " ", fields.get("Description", "").strip())
    when = f"Time: {date}" + (f", {start}" if start else "") + (f" to {end}" if end else "") + "."
    where = f" Place: {place}." if place else ""
    entry = [
        "",
        f"- start_date: {date}",
        f"  end_date: {date}",
        f"  url: {link or 'CHECK-missing-link'}",
        "  partner: CHECK partner institution",
        f"  title: {yaml_str(title)}",
        f"  description: {yaml_str(desc + ' ' + when + where)}",
    ]
    for n in notes:
        entry.append(f"  # CHECK: {n}")
    path = SITE_ROOT / "_data" / "partner_events.yml"
    return path, "\n".join(entry) + "\n"


MESHUP_PLACEHOLDER = re.compile(r"Title and abstract coming soon", re.I)


def find_meshup_file(preferred: str, today: dt.date) -> Path | None:
    """The MeshUp file for the preferred date, else the next one still awaiting a title."""
    events = SITE_ROOT / "_events"
    d = DATE_RE.search(preferred or "")
    if d:
        hits = sorted(events.glob(f"{d.group(0)}-meshup*.md"))
        if hits:
            return hits[0]
    for f in sorted(events.glob("*-meshup*.md")):
        if f.name[:10] >= today.isoformat() and MESHUP_PLACEHOLDER.search(f.read_text(encoding="utf-8")):
            return f
    return None


def fill_meshup(existing: str, fields: dict[str, str]) -> str:
    """Put the speaker's title, abstract and bio into an existing MeshUp page."""
    speaker = fields.get("Speaker", "").strip()
    name = speaker.split(",")[0].split("(")[0].strip() or "The speaker"
    profile = fields.get("Link to your profile page", "").strip()
    talk = fields.get("Title of the talk", "").strip()
    abstract = fields.get("Abstract", "").strip()
    bio = fields.get("Short bio", "").strip()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", existing, re.S)
    if not m:
        raise ValueError("MeshUp file has no front matter")
    front, body = m.group(1), m.group(2)
    num = re.search(r"MeshUp #(\d+)", front)
    label = f"MeshUp #{num.group(1)}" if num else "MeshUp"
    front = re.sub(r'^title: .*$', f"title: {yaml_str(label + ' - ' + talk)}", front, count=1, flags=re.M)
    front = re.sub(r'^description: .*$', f"description: {yaml_str(f'{name} presents {talk}.')}", front, count=1, flags=re.M)
    link = f"[{name}]({profile})" if profile else name
    access = body[body.index("## Access"):] if "## Access" in body else ""
    new_body = (
        f"\nThis week, {link} will present *{talk}*.\n\n"
        f"## Abstract\n{abstract}\n\n"
        f"## Bio\n{bio}\n\n" + access
    )
    return f"---\n{front}\n---\n{new_body}"


# --------------------------------------------------------------- git side --
def sh(*args: str, check: bool = True) -> str:
    return subprocess.run(args, check=check, capture_output=True, text=True).stdout.strip()


def load_issue(number: int) -> dict:
    out = sh("gh", "issue", "view", str(number), "--json", "title,body,labels,url")
    return json.loads(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issue", type=int)
    ap.add_argument("--dry-run", action="store_true", help="write the file, no git, no pull request")
    args = ap.parse_args()
    today = dt.date.today()

    issue = load_issue(args.issue)
    labels = {l["name"] for l in issue.get("labels", [])}
    fields = parse_form(issue["body"] or "")

    if "correction" in labels:
        url = fields.get("Page address", "")
        print(f"Correction for {url}. Find the source with:\n  grep -rl 'permalink: {url.replace('https://mishmash.no', '')}' site/\n"
              "or open the page and use 'View on GitHub' in the footer. Nothing was written.")
        return 0

    if "meshup" in labels:
        target = find_meshup_file(fields.get("Preferred date", ""), today)
        if not target:
            print("No MeshUp page awaiting a title; create the event first.", file=sys.stderr)
            return 1
        content = fill_meshup(target.read_text(encoding="utf-8"), fields)
        kind = "MeshUp"
    elif "news" in labels:
        target, content = render_news(fields, today)
        kind = "news post"
    elif "event" in labels:
        if fields.get("Kind of event", "").strip().lower().startswith("partner"):
            target, content = render_partner_event(fields, today)
            content = target.read_text(encoding="utf-8").rstrip("\n") + "\n" + content
            kind = "partner event"
        else:
            target, content = render_event(fields, today)
            kind = "event"
    else:
        print("The issue has none of the form labels (news, event, meshup, correction).", file=sys.stderr)
        return 1

    if target.exists() and kind in ("news post", "event"):
        print(f"{target} exists already; not overwriting.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"--- {target.relative_to(SITE_ROOT.parent)} ({kind}) ---")
        print(content)
        return 0

    branch = f"form/issue-{args.issue}"
    sh("git", "checkout", "-b", branch)
    target.write_text(content, encoding="utf-8")
    sh("git", "add", str(target))
    sh("git", "commit", "-m", f"{kind[0].upper() + kind[1:]} from issue #{args.issue}: {issue['title']}")
    sh("git", "push", "-u", "origin", branch)
    pr_body = (
        f"Generated from the form in #{args.issue} by scripts/issue_to_pr.py. "
        "Read the file, settle any CHECK comments, then merge.\n\nCloses #" + str(args.issue)
    )
    pr_url = sh("gh", "pr", "create", "--title", f"{kind[0].upper() + kind[1:]}: {issue['title']}", "--body", pr_body)
    sh("gh", "issue", "comment", str(args.issue), "--body", f"Turned into a pull request: {pr_url}")
    print(pr_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
