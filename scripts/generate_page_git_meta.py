#!/usr/bin/env python3
"""Generate site/_data/page_git_meta.yml from git history for page source files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from repo_paths import REPO_ROOT, SITE_ROOT

COMMIT_PREFIX = "---COMMIT---"
SKIP_DIRS = {"_includes", "_layouts", "_sass", "_data", "_plugins"}
CONTENT_SUFFIXES = {".md", ".html", ".markdown"}


def site_relative_path(path: Path, site_root: Path) -> str:
    return path.relative_to(site_root).as_posix()


def iter_content_files(site_root: Path) -> set[str]:
    paths: set[str] = set()
    for path in site_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in CONTENT_SUFFIXES:
            continue
        rel_parts = path.relative_to(site_root).parts
        if rel_parts[0].startswith("_") and rel_parts[0] not in {
            "_directory",
            "_events",
            "_news",
        }:
            continue
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        paths.add(site_relative_path(path, site_root))
    return paths


def parse_git_log(site_root: Path, repo_root: Path) -> dict[str, dict[str, str]]:
    site_arg = site_root.relative_to(repo_root).as_posix()
    cmd = [
        "git",
        "log",
        "--name-only",
        f"--pretty=format:{COMMIT_PREFIX}%aI|%an",
        "--",
        f"{site_arg}/",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or "git log failed") from exc

    meta: dict[str, dict[str, str]] = {}
    current_date = ""
    current_author = ""

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(COMMIT_PREFIX):
            _, _, payload = line.partition(COMMIT_PREFIX)
            date, _, author = payload.partition("|")
            current_date = date.strip()
            current_author = normalize_author(author.strip())
            continue

        if line.startswith(f"{site_arg}/"):
            rel = line[len(site_arg) + 1 :]
        elif line.startswith("site/"):
            rel = line[len("site/") :]
        else:
            continue

        if rel not in meta and current_date and current_author:
            meta[rel] = {"date": current_date, "author": current_author}

    return meta


def normalize_author(author: str) -> str:
    lowered = author.lower()
    if lowered in {"github actions", "github-actions[bot]"}:
        return "GitHub Actions"
    return author


def write_meta(path: Path, meta: dict[str, dict[str, str]], content_paths: set[str]) -> None:
    ordered = {key: meta[key] for key in sorted(content_paths) if key in meta}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            ordered,
            sort_keys=True,
            allow_unicode=True,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate page_git_meta.yml from git history.",
    )
    parser.add_argument("--site-root", type=Path, default=SITE_ROOT)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=SITE_ROOT / "_data" / "page_git_meta.yml",
        help="Output YAML path (default: site/_data/page_git_meta.yml)",
    )
    args = parser.parse_args()

    site_root = args.site_root.resolve()
    repo_root = args.repo_root.resolve()
    content_paths = iter_content_files(site_root)
    meta = parse_git_log(site_root, repo_root)
    write_meta(args.output.resolve(), meta, content_paths)

    print(f"Wrote {len([p for p in content_paths if p in meta])} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
