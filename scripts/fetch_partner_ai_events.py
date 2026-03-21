#!/usr/bin/env python3
"""Discover AI-focused partner events and append them to _data/partner_events.yml.

The script:
1. Reads partner links from index.md.
2. Finds likely event/calendar pages for each partner.
3. Extracts candidate events from JSON-LD or page/link heuristics.
4. Keeps only AI-related events in the future.
5. Appends non-duplicate entries to _data/partner_events.yml.

Usage:
  python3 scripts/fetch_partner_ai_events.py --dry-run
  python3 scripts/fetch_partner_ai_events.py --max-pages-per-partner 4
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


BASE_DIR = Path(__file__).resolve().parents[1]
INDEX_MD = BASE_DIR / "index.md"
PARTNER_EVENTS_YML = BASE_DIR / "_data" / "partner_events.yml"


AI_KEYWORDS = {
    "ai",
    "a.i.",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural",
    "generative",
    "algorithmic",
    "algoritm",
    "kunstig intelligens",
    "maskinl",
}

EVENT_HINTS = {
    "event",
    "events",
    "calendar",
    "programme",
    "program",
    "concert",
    "seminar",
    "workshop",
    "festival",
    "whats-happening",
    "hva-skjer",
    "forestilling",
}


@dataclass
class Partner:
    name: str
    homepage: str


@dataclass
class CandidateEvent:
    title: str
    url: str
    partner: str
    start_date: date
    end_date: date


def get_html(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": "mishmash-partner-events-bot/1.0"}
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response.text


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_date_value(value: str, default: datetime | None = None) -> date | None:
    if not value:
        return None
    try:
        dt = dateparser.parse(value, dayfirst=True, fuzzy=True, default=default)
    except Exception:
        return None
    if not dt:
        return None
    return dt.date()


def extract_date_range(text: str) -> tuple[date | None, date | None]:
    """Extract a best-effort start/end date from arbitrary text."""
    if not text:
        return (None, None)

    cleaned = normalize_whitespace(text)

    # 2026-05-27 - 2026-06-10
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:-|–|to)\s*(\d{4}-\d{2}-\d{2})", cleaned, flags=re.IGNORECASE)
    if m:
        s = parse_date_value(m.group(1))
        e = parse_date_value(m.group(2))
        return (s, e)

    # 9.06 - 13.09.2026
    m = re.search(r"(\d{1,2}\.\d{1,2})\s*(?:-|–|to)\s*(\d{1,2}\.\d{1,2}\.\d{4})", cleaned, flags=re.IGNORECASE)
    if m:
        end_dt = parse_date_value(m.group(2))
        if end_dt:
            start_guess = f"{m.group(1)}.{end_dt.year}"
            start_dt = parse_date_value(start_guess)
            if start_dt:
                return (start_dt, end_dt)

    # 27 May - 10 June 2026
    m = re.search(
        r"(\d{1,2}\s+[A-Za-z]+)\s*(?:-|–|to)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        end_dt = parse_date_value(m.group(2))
        if end_dt:
            start_dt = parse_date_value(f"{m.group(1)} {end_dt.year}")
            if start_dt:
                return (start_dt, end_dt)

    # 27 May 2026 - 10 June 2026
    m = re.search(
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s*(?:-|–|to)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        cleaned,
        flags=re.IGNORECASE,
    )
    if m:
        s = parse_date_value(m.group(1))
        e = parse_date_value(m.group(2))
        if s:
            return (s, e or s)

    # single date fallback
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", cleaned)
    if m:
        d = parse_date_value(m.group(1))
        return (d, d)

    m = re.search(r"\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b", cleaned, flags=re.IGNORECASE)
    if m:
        d = parse_date_value(m.group(1))
        return (d, d)

    return (None, None)


def is_ai_related(*texts: str) -> bool:
    blob = " ".join(t for t in texts if t).lower()
    return any(keyword in blob for keyword in AI_KEYWORDS)


def extract_partners_from_index(path: Path) -> list[Partner]:
    content = path.read_text(encoding="utf-8")
    partners: list[Partner] = []
    for match in re.finditer(r"<li><a href=\"([^\"]+)\">([^<]+)</a></li>", content):
        url = match.group(1).strip()
        name = normalize_whitespace(match.group(2))
        if not url.startswith("http"):
            continue
        partners.append(Partner(name=name, homepage=url))

    unique = {}
    for p in partners:
        unique[p.homepage] = p
    return list(unique.values())


def same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc == urlparse(b).netloc


def discover_event_pages(homepage_url: str, html: str, limit: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    pages = [homepage_url]

    for anchor in soup.find_all("a", href=True):
        href = urljoin(homepage_url, anchor.get("href", "").strip())
        if not href.startswith("http"):
            continue
        if not same_host(homepage_url, href):
            continue

        text = normalize_whitespace(anchor.get_text(" ", strip=True)).lower()
        combined = f"{href.lower()} {text}"
        if any(hint in combined for hint in EVENT_HINTS):
            if href not in pages:
                pages.append(href)
        if len(pages) >= limit:
            break

    return pages[:limit]


def parse_jsonld_events(page_url: str, partner: str, soup: BeautifulSoup) -> list[CandidateEvent]:
    events: list[CandidateEvent] = []
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

    for node in scripts:
        raw = (node.string or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        stack: list[object] = [data]
        while stack:
            current = stack.pop()
            if isinstance(current, list):
                stack.extend(current)
                continue
            if not isinstance(current, dict):
                continue

            item_type = str(current.get("@type", "")).lower()
            if "event" in item_type:
                title = normalize_whitespace(str(current.get("name", "")))
                start = parse_date_value(str(current.get("startDate", "")))
                end = parse_date_value(str(current.get("endDate", ""))) or start
                url = str(current.get("url", "")).strip() or page_url
                desc = normalize_whitespace(str(current.get("description", "")))

                if title and start and is_ai_related(title, desc):
                    events.append(
                        CandidateEvent(
                            title=title,
                            url=url,
                            partner=partner,
                            start_date=start,
                            end_date=end,
                        )
                    )

            for value in current.values():
                if isinstance(value, (dict, list)):
                    stack.append(value)

    return events


def parse_page_level_event(page_url: str, partner: str, soup: BeautifulSoup) -> list[CandidateEvent]:
    events: list[CandidateEvent] = []
    h1 = soup.find("h1")
    title = normalize_whitespace(h1.get_text(" ", strip=True)) if h1 else ""
    page_text = normalize_whitespace(soup.get_text(" ", strip=True))

    if not title:
        return events
    if not is_ai_related(title, page_text[:3000]):
        return events

    start, end = extract_date_range(page_text[:4000])
    if start:
        events.append(
            CandidateEvent(
                title=title,
                url=page_url,
                partner=partner,
                start_date=start,
                end_date=end or start,
            )
        )
    return events


def parse_link_level_events(page_url: str, partner: str, soup: BeautifulSoup) -> list[CandidateEvent]:
    events: list[CandidateEvent] = []

    for anchor in soup.find_all("a", href=True):
        title = normalize_whitespace(anchor.get_text(" ", strip=True))
        if len(title) < 6:
            continue

        parent = anchor.parent
        context = normalize_whitespace(parent.get_text(" ", strip=True)) if parent else title
        if not is_ai_related(title, context):
            continue

        start, end = extract_date_range(context)
        if not start:
            continue

        href = urljoin(page_url, anchor.get("href", "").strip())
        if not href.startswith("http"):
            continue

        events.append(
            CandidateEvent(
                title=title,
                url=href,
                partner=partner,
                start_date=start,
                end_date=end or start,
            )
        )

    return events


def extract_events_from_page(page_url: str, partner_name: str, html: str) -> list[CandidateEvent]:
    soup = BeautifulSoup(html, "html.parser")
    events: list[CandidateEvent] = []
    events.extend(parse_jsonld_events(page_url, partner_name, soup))
    events.extend(parse_page_level_event(page_url, partner_name, soup))
    events.extend(parse_link_level_events(page_url, partner_name, soup))
    return events


def load_existing_event_urls(yml_path: Path) -> set[str]:
    if not yml_path.exists():
        return set()
    text = yml_path.read_text(encoding="utf-8")
    return {m.group(1).strip() for m in re.finditer(r"^\s*url:\s*(\S+)\s*$", text, flags=re.MULTILINE)}


def dedupe_candidates(candidates: Iterable[CandidateEvent]) -> list[CandidateEvent]:
    deduped: list[CandidateEvent] = []
    seen: set[tuple[str, str]] = set()
    for c in candidates:
        key = (c.url, c.title.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    return deduped


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def append_events_to_yaml(path: Path, events: list[CandidateEvent]) -> None:
    lines: list[str] = []
    for ev in events:
        lines.append("")
        lines.append(f"- start_date: {ev.start_date.isoformat()}")
        lines.append(f"  end_date: {ev.end_date.isoformat()}")
        lines.append(f"  url: {ev.url}")
        lines.append(f"  partner: {ev.partner}")
        lines.append(f"  title: {yaml_quote(ev.title)}")

    if not lines:
        return

    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Find AI-focused partner events and update _data/partner_events.yml")
    parser.add_argument("--index", default=str(INDEX_MD), help="Path to index.md containing partner links")
    parser.add_argument("--output", default=str(PARTNER_EVENTS_YML), help="Path to partner events YAML")
    parser.add_argument("--max-partners", type=int, default=80, help="Maximum partner homepages to inspect")
    parser.add_argument("--max-pages-per-partner", type=int, default=5, help="Max discovered event pages per partner")
    parser.add_argument("--sleep", type=float, default=0.25, help="Delay between HTTP requests")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates but do not write YAML")
    args = parser.parse_args()

    partners = extract_partners_from_index(Path(args.index))
    if not partners:
        print("No partner links found in index file.")
        return

    existing_urls = load_existing_event_urls(Path(args.output))
    today = date.today()
    all_candidates: list[CandidateEvent] = []

    for partner in partners[: args.max_partners]:
        try:
            home_html = get_html(partner.homepage)
        except Exception as exc:
            print(f"Skip partner homepage fetch error: {partner.name} ({partner.homepage}) -> {exc}")
            continue

        pages = discover_event_pages(partner.homepage, home_html, limit=args.max_pages_per_partner)
        for page_url in pages:
            time.sleep(args.sleep)
            try:
                html = home_html if page_url == partner.homepage else get_html(page_url)
            except Exception:
                continue

            extracted = extract_events_from_page(page_url, partner.name, html)
            for ev in extracted:
                if ev.start_date < today:
                    continue
                if ev.url in existing_urls:
                    continue
                all_candidates.append(ev)

    final_events = dedupe_candidates(all_candidates)

    if not final_events:
        print("No new AI-focused partner events found.")
        return

    final_events.sort(key=lambda e: (e.start_date, e.end_date, e.partner.lower(), e.title.lower()))

    for ev in final_events:
        print(f"{ev.start_date.isoformat()} -> {ev.end_date.isoformat()} | {ev.partner} | {ev.title} | {ev.url}")

    if args.dry_run:
        print(f"Dry run complete. Would append {len(final_events)} events.")
        return

    append_events_to_yaml(Path(args.output), final_events)
    print(f"Appended {len(final_events)} event(s) to {args.output}.")


if __name__ == "__main__":
    main()
