#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

import requests
import yaml


PERSON_PROFILE_RE = re.compile(r"/research-profile/(\d+)")
CRISTIN_RE = re.compile(r"/cristin/person/(\d+)")


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        raise ValueError("Missing frontmatter start")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Missing frontmatter end")
    front = text[4:end]
    body = text[end + 5 :]
    return front, body


def slugify(value: str) -> str:
    value = value.lower()
    replacements = {
        "æ": "ae",
        "ø": "o",
        "å": "a",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value).strip("-")
    return value


def normalize_name(value: str) -> str:
    value = value.lower()
    replacements = {
        "æ": "ae",
        "ø": "o",
        "å": "a",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ü": "u",
        "ö": "o",
        "ä": "a",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9\s-]", " ", value)
    value = re.sub(r"[-\s]+", " ", value).strip()
    return value


def normalize_person_name_for_match(value: str) -> str:
    # Remove parenthetical aliases like "Fredrik (Georg Fredrik) Graver"
    value = re.sub(r"\([^)]*\)", " ", value)
    return normalize_name(value)


def first_last_tokens(value: str) -> tuple[str, str]:
    parts = [p for p in value.split() if p]
    if not parts:
        return "", ""
    return parts[0], parts[-1]


def extract_profile_id(nva_url: str) -> str | None:
    if not nva_url:
        return None
    m = PERSON_PROFILE_RE.search(nva_url)
    if m:
        return m.group(1)
    m = CRISTIN_RE.search(nva_url)
    if m:
        return m.group(1)
    return None


def discover_profile_id_by_name(
    name: str,
    institution_slug: str,
    slug_to_institution_name: dict[str, str],
    org_cache: dict,
    allow_loose: bool,
) -> tuple[str | None, str]:
    target_name = normalize_person_name_for_match(name)
    if not target_name:
        return None, "skip: missing name"

    query = requests.utils.quote(name)
    data = get_json(f"https://api.nva.unit.no/cristin/person?name={query}&results=20")
    hits = data.get("hits") or []
    if not hits:
        return None, "skip: no nva person hits"

    exact = []
    candidates = []
    for hit in hits:
        full = names_to_full_name(hit.get("names") or [])
        full_norm = normalize_person_name_for_match(full)

        cristin_id = ""
        for ident in hit.get("identifiers") or []:
            if ident.get("type") == "CristinIdentifier" and ident.get("value"):
                cristin_id = str(ident["value"])
                break

        if not cristin_id:
            m = CRISTIN_RE.search(hit.get("id") or "")
            if m:
                cristin_id = m.group(1)

        if cristin_id:
            candidates.append((hit, cristin_id, full_norm))
            if full_norm == target_name:
                exact.append((hit, cristin_id, full_norm))

    if not exact and not allow_loose:
        return None, "skip: no exact name match"

    target_first, target_last = first_last_tokens(target_name)

    def score_candidate(full_norm: str) -> float:
        cand_first, cand_last = first_last_tokens(full_norm)
        if not cand_first or not cand_last:
            return 0.0
        score = 0.0
        if cand_last == target_last:
            score += 1.0
        # Accept first-name prefix matches (sashi vs sashidharan)
        if cand_first == target_first:
            score += 1.0
        elif cand_first.startswith(target_first) or target_first.startswith(cand_first):
            score += 0.8

        target_tokens = set(target_name.split())
        cand_tokens = set(full_norm.split())
        if target_tokens and cand_tokens:
            overlap = len(target_tokens & cand_tokens) / len(target_tokens | cand_tokens)
            score += overlap
        return score

    pool = exact if exact else candidates
    if len(pool) == 1:
        return pool[0][1], "discovered by exact name" if exact else "discovered by loose unique match"

    institution_name = (slug_to_institution_name.get(institution_slug) or "").strip()
    target_inst = normalize_name(institution_name)
    if target_inst:
        inst_matches = []
        for hit, cristin_id, full_norm in pool:
            org_names = []
            for aff in hit.get("affiliations") or []:
                org_url = (aff.get("organization") or "").strip()
                org_name = fetch_org_name(org_url, org_cache)
                if org_name:
                    org_names.append(org_name)
            if any(normalize_name(org) == target_inst for org in org_names):
                inst_matches.append((cristin_id, full_norm))

        if len(inst_matches) == 1:
            return inst_matches[0][0], "discovered by name+institution"
        if len(inst_matches) > 1:
            # Try score-based tie-break in loose mode.
            if allow_loose:
                scored = sorted(inst_matches, key=lambda x: score_candidate(x[1]), reverse=True)
                if len(scored) >= 2 and scored[0][1] and (score_candidate(scored[0][1]) - score_candidate(scored[1][1])) >= 0.4:
                    return scored[0][0], "discovered by loose score + institution"
            return None, "skip: ambiguous matches after institution filter"

    if allow_loose and not exact:
        # Conservative loose match: require strong score and clear margin.
        scored = sorted([(cid, full_norm, score_candidate(full_norm)) for _, cid, full_norm in candidates], key=lambda x: x[2], reverse=True)
        if scored and scored[0][2] >= 2.2:
            if len(scored) == 1 or (scored[0][2] - scored[1][2]) >= 0.4:
                return scored[0][0], "discovered by loose score"

    return None, "skip: ambiguous exact-name matches"


def get_json(url: str):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def names_to_full_name(names: list[dict]) -> str:
    first = ""
    last = ""
    for item in names or []:
        if item.get("type") == "FirstName":
            first = item.get("value", "")
        if item.get("type") == "LastName":
            last = item.get("value", "")
    return f"{first} {last}".strip()


def find_orcid(identifiers: list[dict]) -> str:
    for ident in identifiers or []:
        if ident.get("type") == "ORCID" and ident.get("value"):
            return f"https://orcid.org/{ident['value']}"
    return ""


def pick_active_affiliation(affiliations: list[dict]) -> dict:
    for aff in affiliations or []:
        if aff.get("active"):
            return aff
    return affiliations[0] if affiliations else {}


def fetch_org_name(org_url: str, cache: dict) -> str:
    if not org_url:
        return ""
    if org_url in cache:
        return cache[org_url]
    try:
        data = get_json(org_url)
    except Exception:
        cache[org_url] = ""
        return ""

    labels = data.get("labels") or {}
    name = labels.get("en") or labels.get("nb") or data.get("name") or ""
    cache[org_url] = name
    return name


def keyword_labels(keywords: list[dict], max_keywords: int) -> list[str]:
    out = []
    seen = set()
    for kw in keywords or []:
        label = (kw.get("label") or {}).get("en") or (kw.get("label") or {}).get("nb") or ""
        label = label.strip()
        if not label:
            continue
        low = label.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(label)
        if len(out) >= max_keywords:
            break
    return out


def background_to_summary(background) -> str:
    if isinstance(background, str):
        return background.strip()
    if isinstance(background, dict):
        return (background.get("en") or background.get("no") or background.get("nb") or "").strip()
    return ""


def build_institution_lookup(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    lookup = {}
    slug_to_name = {}
    base = root / "_directory" / "institutions"
    if not base.exists():
        return lookup, slug_to_name
    for child in base.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        index = child / "index.md"
        if not index.exists():
            continue
        try:
            front, _ = split_frontmatter(index.read_text(encoding="utf-8", errors="ignore"))
            data = yaml.safe_load(front) or {}
            name = (data.get("name") or "").strip()
            slug = (data.get("slug") or child.name).strip()
            if name and slug:
                lookup[slugify(name)] = slug
                slug_to_name[slug] = name
        except Exception:
            continue
    return lookup, slug_to_name


def ordered_person(data: dict) -> dict:
    key_order = [
        "type",
        "slug",
        "name",
        "title",
        "position",
        "image",
        "institution",
        "institutions",
        "projects",
        "roles",
        "urls",
        "aliases",
        "tags",
        "search_keywords",
        "source_mentions",
        "summary",
    ]

    ordered = {}
    for key in key_order:
        if key in data:
            ordered[key] = data[key]

    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value

    urls = ordered.get("urls") or {}
    if isinstance(urls, dict):
        url_order = [
            "website",
            "github",
            "linkedin",
            "orcid",
            "nva",
            "youtube",
            "facebook",
            "mastodon",
            "instagram",
        ]
        ordered_urls = {}
        for k in url_order:
            v = urls.get(k, "")
            ordered_urls[k] = "" if v is None else v
        for k, v in urls.items():
            if k not in ordered_urls:
                ordered_urls[k] = "" if v is None else v
        ordered["urls"] = ordered_urls

    return ordered


def enrich_person(
    index_md: Path,
    institution_lookup: dict[str, str],
    slug_to_institution_name: dict[str, str],
    org_cache: dict,
    max_keywords: int,
    dry_run: bool,
    discover_nva: bool,
    discover_nva_loose: bool,
):
    text = index_md.read_text(encoding="utf-8")
    front, body = split_frontmatter(text)
    data = yaml.safe_load(front) or {}

    if data.get("type") != "person":
        return False, "skip: not person"

    urls = data.get("urls") or {}
    nva_url = (urls.get("nva") or "").strip()
    if not nva_url and discover_nva:
        discovered_id, reason = discover_profile_id_by_name(
            name=(data.get("name") or ""),
            institution_slug=(data.get("institution") or "").strip(),
            slug_to_institution_name=slug_to_institution_name,
            org_cache=org_cache,
            allow_loose=discover_nva_loose,
        )
        if discovered_id:
            nva_url = f"https://nva.sikt.no/research-profile/{discovered_id}"
            urls["nva"] = nva_url
            data["urls"] = urls
        else:
            return False, reason

    if not nva_url:
        return False, "skip: no urls.nva"

    profile_id = extract_profile_id(nva_url)
    if not profile_id:
        return False, "skip: unsupported nva url"

    profile = get_json(f"https://api.nva.unit.no/cristin/person/{profile_id}")
    full_name = names_to_full_name(profile.get("names") or [])
    orcid = find_orcid(profile.get("identifiers") or [])

    contact = profile.get("contactDetails") or {}
    website = (contact.get("webPage") or "").strip()

    affiliation = pick_active_affiliation(profile.get("affiliations") or [])
    role_labels = ((affiliation.get("role") or {}).get("labels") or {})
    position = role_labels.get("en") or role_labels.get("nb") or ""
    org_name = fetch_org_name((affiliation.get("organization") or "").strip(), org_cache)
    org_slug = institution_lookup.get(slugify(org_name), "") if org_name else ""

    kws = keyword_labels(profile.get("keywords") or [], max_keywords=max_keywords)
    summary = background_to_summary(profile.get("background"))

    changed = False
    if full_name and data.get("name") != full_name:
        data["name"] = full_name
        data["title"] = full_name
        changed = True

    if position and data.get("position") != position:
        data["position"] = position
        changed = True

    if org_slug and data.get("institution") != org_slug:
        data["institution"] = org_slug
        changed = True

    existing_insts = data.get("institutions") or []
    if not isinstance(existing_insts, list):
        existing_insts = []
    if org_slug and org_slug not in existing_insts:
        existing_insts.append(org_slug)
        data["institutions"] = sorted(set(existing_insts))
        changed = True

    if kws:
        data["search_keywords"] = kws
        changed = True

    if summary and not (data.get("summary") or "").strip():
        data["summary"] = summary
        changed = True

    if orcid and urls.get("orcid") != orcid:
        urls["orcid"] = orcid
        changed = True

    canonical_nva = f"https://nva.sikt.no/research-profile/{profile_id}"
    if urls.get("nva") != canonical_nva:
        urls["nva"] = canonical_nva
        changed = True

    if website and not (urls.get("website") or "").strip():
        urls["website"] = website
        changed = True

    data["urls"] = urls

    if not changed:
        return False, "unchanged"

    if dry_run:
        return True, "would update"

    ordered = ordered_person(data)
    dumped = yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False).strip()
    index_md.write_text(f"---\n{dumped}\n---\n\n{body.lstrip()}" , encoding="utf-8")
    return True, "updated"


def main():
    parser = argparse.ArgumentParser(description="Enrich directory people entries from NVA profile URLs.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--slug", action="append", help="Only process specific person slug (repeatable)")
    parser.add_argument("--max-keywords", type=int, default=12, help="Maximum number of NVA keywords to import")
    parser.add_argument("--discover-nva", action="store_true", help="Auto-discover missing urls.nva from person name and institution")
    parser.add_argument("--discover-nva-loose", action="store_true", help="Allow a second-round looser name match for NVA discovery")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    people_base = root / "_directory" / "people"
    if not people_base.exists():
        raise SystemExit(f"Missing directory: {people_base}")

    slugs = set(args.slug or [])
    institution_lookup, slug_to_institution_name = build_institution_lookup(root)
    org_cache = {}

    updated = 0
    skipped = 0

    for person_dir in sorted(people_base.iterdir()):
        if not person_dir.is_dir() or person_dir.name.startswith("_"):
            continue
        if slugs and person_dir.name not in slugs:
            continue
        index_md = person_dir / "index.md"
        if not index_md.exists():
            continue

        try:
            changed, msg = enrich_person(
                index_md,
                institution_lookup=institution_lookup,
                slug_to_institution_name=slug_to_institution_name,
                org_cache=org_cache,
                max_keywords=args.max_keywords,
                dry_run=args.dry_run,
                discover_nva=args.discover_nva,
                discover_nva_loose=args.discover_nva_loose,
            )
            if changed:
                updated += 1
            else:
                skipped += 1
            print(f"{person_dir.name}: {msg}")
        except Exception as exc:
            skipped += 1
            print(f"{person_dir.name}: error: {exc}")

    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
