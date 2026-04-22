#!/usr/bin/env python3
import argparse
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

TEXT_EXTS = {".md", ".mdx", ".html", ".htm", ".txt", ".yml", ".yaml", ".json"}
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    "directory",
    "venv",
}

INSTITUTION_KEYWORDS = {
    "university", "college", "institute", "institutt", "school", "hospital",
    "lab", "laboratory", "centre", "center", "foundation", "museum",
    "kommune", "county", "ministry", "directorate", "agency", "company",
    "inc", "ltd", "as", "asa", "gmbh", "llc", "department",
}
PROJECT_KEYWORDS = {
    "project", "program", "programme", "initiative", "platform", "consortium",
    "grant", "work package", "wp", "pilot", "network",
}

KEY_TO_TYPE = {
    "author": "person",
    "authors": "person",
    "person": "person",
    "people": "person",
    "team": "person",
    "institution": "institution",
    "institutions": "institution",
    "partner": "institution",
    "partners": "institution",
    "organization": "institution",
    "organisations": "institution",
    "organizations": "institution",
    "project": "project",
    "projects": "project",
}

COMMON_STOP = {
    "home", "about", "contact", "news", "events", "read more", "learn more",
    "privacy policy", "terms", "mishmash", "norway",
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value[:80].strip("-")


def should_scan(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_EXTS:
        return False
    for p in path.parts:
        if p in EXCLUDE_DIRS:
            return False
    return True


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if not m:
        return {}
    fm = m.group(1).splitlines()
    data = defaultdict(list)
    i = 0
    while i < len(fm):
        line = fm[i]
        kvm = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not kvm:
            i += 1
            continue
        key = kvm.group(1).strip().lower()
        val = kvm.group(2).strip()

        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            data[key].extend(items)
            i += 1
            continue

        if val:
            parts = [x.strip().strip("'\"") for x in re.split(r",\s*", val) if x.strip()]
            data[key].extend(parts)
            i += 1
            continue

        i += 1
        while i < len(fm):
            li = re.match(r"^\s*-\s+(.+?)\s*$", fm[i])
            if not li:
                break
            data[key].append(li.group(1).strip().strip("'\""))
            i += 1
    return dict(data)


def looks_like_person(name: str) -> bool:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if len(parts) < 2 or len(parts) > 4:
        return False
    good = 0
    for p in parts:
        if re.match(r"^[A-ZÆØÅ][a-zæøåA-ZÆØÅ'\-]+$", p):
            good += 1
    return good >= 2


def classify(name: str, hinted_type: str | None = None) -> str | None:
    if not name:
        return None
    clean = re.sub(r"\s+", " ", name).strip(" -–—:|")
    if len(clean) < 3:
        return None
    if clean.lower() in COMMON_STOP:
        return None
    if re.search(r"https?://", clean):
        return None

    if hinted_type:
        return hinted_type

    low = clean.lower()
    if any(k in low for k in INSTITUTION_KEYWORDS):
        return "institution"
    if any(k in low for k in PROJECT_KEYWORDS):
        return "project"
    if looks_like_person(clean):
        return "person"
    return None


def collect_mentions(root: Path):
    mentions = {
        "person": defaultdict(set),
        "institution": defaultdict(set),
        "project": defaultdict(set),
    }

    for p in root.rglob("*"):
        if not p.is_file() or not should_scan(p):
            continue
        text = read_text(p)
        rel = str(p.relative_to(root))

        fm = parse_frontmatter(text)
        for key, values in fm.items():
            hinted = KEY_TO_TYPE.get(key)
            if not hinted:
                continue
            for v in values:
                t = classify(v, hinted)
                if t:
                    mentions[t][v].add(rel)

        for h in re.findall(r"(?m)^#\s+(.+)$", text):
            t = classify(h)
            if t:
                mentions[t][h].add(rel)

        for label in re.findall(r"\[([^\]]+)\]\([^)]+\)", text):
            t = classify(label)
            if t:
                mentions[t][label].add(rel)

        for title in re.findall(r"(?is)<title>(.*?)</title>", text):
            title = re.sub(r"\s+", " ", title).strip()
            t = classify(title)
            if t:
                mentions[t][title].add(rel)

    return mentions


def render_entry(entry_type: str, name: str, slug: str, sources: list[str]) -> str:
    source_block = "\n".join([f"  - {s}" for s in sources]) if sources else "  -"
    if entry_type == "person":
        return f"""---
type: person
slug: {slug}
name: {name}
image: /images/people/{slug}.jpg
institutions: []
projects: []
roles: []
urls:
  website:
  github:
  linkedin:
  orcid:
aliases: []
tags: []
search_keywords: []
source_mentions:
{source_block}
summary:
---

# {name}

"""
    if entry_type == "institution":
        return f"""---
type: institution
slug: {slug}
name: {name}
image: /images/institutions/{slug}.png
people: []
projects: []
country:
city:
urls:
  website:
  wikipedia:
aliases: []
tags: []
search_keywords: []
source_mentions:
{source_block}
summary:
---

# {name}

"""
    return f"""---
type: project
slug: {slug}
name: {name}
image: /images/projects/{slug}.jpg
people: []
institutions: []
status: active
start_date:
end_date:
urls:
  website:
  repository:
aliases: []
tags: []
search_keywords: []
source_mentions:
{source_block}
summary:
---

# {name}

"""


def write_entries(root: Path, mentions, overwrite: bool = False):
    map_dir = {"person": "people", "institution": "institutions", "project": "projects"}
    created = 0
    skipped = 0

    for t, items in mentions.items():
        base = root / "_directory" / map_dir[t]
        base.mkdir(parents=True, exist_ok=True)

        for raw_name, srcs in sorted(items.items(), key=lambda x: x[0].lower()):
            name = re.sub(r"\s+", " ", raw_name).strip()
            slug = slugify(name)
            if not slug:
                continue

            out = base / slug / "index.md"
            if out.exists() and not overwrite:
                skipped += 1
                continue

            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render_entry(t, name, slug, sorted(srcs)), encoding="utf-8")
            created += 1

    return created, skipped


def main():
    parser = argparse.ArgumentParser(description="Generate directory entries from current website content.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing index.md entries")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    mentions = collect_mentions(root)
    created, skipped = write_entries(root, mentions, overwrite=args.overwrite)

    print(f"Done. Created: {created}, skipped existing: {skipped}")
    for t in ("person", "institution", "project"):
        print(f"{t}: {len(mentions[t])} candidates found")


if __name__ == "__main__":
    main()
