#!/usr/bin/env python3
"""Set summary on institution entries from Wikipedia lead extracts."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from directory_io import load_entry, save_entry
from institution_short_names import DEFAULT_INSTITUTION_WIKIPEDIA
from repo_paths import SITE_ROOT

USER_AGENT = "mishmash-web/1.0 (directory sync; contact: mishmash.no)"


def wikipedia_title_from_url(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url.strip())
    host_parts = parsed.netloc.split(".")
    lang = host_parts[0] if host_parts and host_parts[0] not in ("www", "m") else "en"
    title = urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1])
    return lang, title


def fetch_wikipedia_summary(url: str) -> str:
    lang, title = wikipedia_title_from_url(url)
    encoded_title = urllib.parse.quote(title, safe="")
    api_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    request = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    extract = (data.get("extract") or "").strip()
    if not extract:
        raise ValueError("empty extract")
    return extract


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync institution summaries from Wikipedia.")
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument("--slug", action="append", help="Only process specific institution slug (repeatable)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing summaries")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    institutions_dir = Path(args.root).resolve() / "_directory" / "institutions"
    slugs = sorted(args.slug) if args.slug else sorted(DEFAULT_INSTITUTION_WIKIPEDIA.keys())
    updated = 0
    skipped = 0

    for slug in slugs:
        index_md = institutions_dir / slug / "index.md"
        if not index_md.exists():
            print(f"missing entry: {slug}")
            continue

        data, body = load_entry(index_md)
        urls = data.get("urls") or {}
        wikipedia = (urls.get("wikipedia") or DEFAULT_INSTITUTION_WIKIPEDIA.get(slug) or "").strip()
        if not wikipedia:
            print(f"skip {slug}: no wikipedia url")
            skipped += 1
            continue

        current = data.get("summary")
        if current and current not in ("", "null", None) and not args.force:
            print(f"skip {slug}: already has summary")
            skipped += 1
            continue

        try:
            summary = fetch_wikipedia_summary(wikipedia)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(2.0)
                try:
                    summary = fetch_wikipedia_summary(wikipedia)
                except (urllib.error.URLError, ValueError, json.JSONDecodeError, urllib.error.HTTPError) as retry_exc:
                    print(f"error {slug}: {retry_exc}")
                    skipped += 1
                    continue
            else:
                print(f"error {slug}: {exc}")
                skipped += 1
                continue
        except (urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
            print(f"error {slug}: {exc}")
            skipped += 1
            continue

        if data.get("summary") == summary:
            print(f"unchanged {slug}")
            skipped += 1
            continue

        data["summary"] = summary
        if not args.dry_run:
            save_entry(index_md, data, body)
        print(f"{'would set' if args.dry_run else 'set'} {slug}")
        updated += 1
        time.sleep(1.0)

    print(f"\nUpdated: {updated}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
