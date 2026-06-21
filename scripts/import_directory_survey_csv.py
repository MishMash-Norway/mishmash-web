#!/usr/bin/env python3
"""Import or update directory people from a MishMash survey CSV export."""

from __future__ import annotations

import argparse
import csv
import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from enrich_directory_from_nva import ORCID_PROFILE_RE, build_institution_lookup, orcid_primary_employment
from institution_short_names import suggest_short_name
from directory_io import load_entry, save_entry
from repo_paths import SITE_ROOT
from sync_directory_reciprocity import sync_directory

EMAIL_DOMAIN_TO_INSTITUTION = {
    "ntnu.no": "norwegian-university-of-science-and-technology",
    "uio.no": "university-of-oslo",
    "nla.no": "nla-university-college",
    "nb.no": "national-library-of-norway",
    "nmh.no": "norwegian-academy-of-music",
    "bi.no": "bi-norwegian-business-school",
    "kristiania.no": "kristiania-university-college",
    "uia.no": "university-of-agder",
    "uib.no": "university-of-bergen",
    "inn.no": "university-of-inland-norway",
    "uit.no": "arctic-university-of-norway",
    "nord.no": "nord-university",
    "hvl.no": "western-norway-university-of-applied-sciences",
    "oslomet.no": "oslo-metropolitan-university",
}

HOST_TO_INSTITUTION = {
    "ntnu.no": "norwegian-university-of-science-and-technology",
    "uio.no": "university-of-oslo",
    "people.uio.no": "university-of-oslo",
    "nla.no": "nla-university-college",
    "nb.no": "national-library-of-norway",
    "nmh.no": "norwegian-academy-of-music",
    "bi.no": "bi-norwegian-business-school",
    "kristiania.no": "kristiania-university-college",
    "uia.no": "university-of-agder",
    "uib.no": "university-of-bergen",
    "inn.no": "university-of-inland-norway",
    "uit.no": "arctic-university-of-norway",
    "nord.no": "nord-university",
    "hvl.no": "western-norway-university-of-applied-sciences",
    "oslomet.no": "oslo-metropolitan-university",
}

INVALID_NVA_RE = re.compile(r"/my-page/|/profile/research-profile/?$")
ORCID_ID_RE = re.compile(r"^(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$", re.I)
WP_TAG_RE = re.compile(r"^WP[1-7]$", re.I)
URL_FIELDS = (
    "personal_website",
    "institutional_website",
    "github",
    "linkedin",
    "youtube",
    "facebook",
    "mastodon",
    "instagram",
)
CSV_URL_COLUMNS = {
    "website (institution)": "institutional_website",
    "website (personal)": "personal_website",
    "github": "github",
    "linkedin": "linkedin",
    "youtube": "youtube",
    "facebook": "facebook",
    "mastodon": "mastodon",
    "instagram": "instagram",
    "orcid": "orcid",
    "nva": "nva",
}

SURVEY_COLUMN_ALIASES = {
    "Web page (personal)": "website (personal)",
    "Web page (institutional)": "website (institution)",
    "Institution/Organisation": "institution name",
    "Current position": "position",
    "Unit": "department",
    "Keywords describing your competencies relevant for MishMash": "competency keywords",
    "Keywords describing your interests in MishMash": "interest keywords",
    "Anything else you want to add?": "Comments",
}


def survey_membership_role(row: dict) -> str:
    for key, value in row.items():
        if "role" in str(key).lower() and "mishmash" in str(key).lower():
            return html.unescape(str(value or "").strip())
    return ""


def is_full_member(row: dict) -> bool:
    return survey_membership_role(row).lower().startswith("full member")


def parse_survey_roles(row: dict) -> list[str]:
    if is_full_member(row):
        return ["Member"]
    role = survey_membership_role(row)
    if role.lower().startswith("associate member"):
        return ["Associate member"]
    if "affiliate" in role.lower():
        return ["Affiliate member"]
    return ["Member"]

INSTITUTION_NAME_MAP = {
    "teks - trondheim electronic arts centre": "teks-trondheim-electronic-arts-centre",
    "ostfoldmuseene": "ostfold-museums",
    "universitetet i agder": "university-of-agder",
    "university of stuttgart": "university-of-stuttgart",
    "skapia": "skapia",
    "anno museum": "anno",
    "festspillene i bergen": "bergen-international-festival",
    "university of bergen": "university-of-bergen",
    "center for digital narrative/universitet i bergen": "university-of-bergen",
    "university of oslo": "university-of-oslo",
    "uio": "university-of-oslo",
    "ntnu": "norwegian-university-of-science-and-technology",
    "oslo national academy of the arts": "oslo-national-academy-of-the-arts",
    "kunsthogskolen i oslo": "oslo-national-academy-of-the-arts",
    "khio / oslo national academy of the arts": "oslo-national-academy-of-the-arts",
    "universitetet i stavanger": "university-of-stavanger",
    "mf vitenskapelig hoyskole": "mf-norwegian-school-of-theology-religion-and-society",
    "musikk i skolen": "musikk-i-skolen",
    "university of music lubeck": "university-of-music-lubeck",
    "norges musikkmuseum - ringve og rockheim": "norwegian-museum-of-music",
    "storyphone as": "storyphone",
    "i/o/lab": "i-o-lab",
    "muzziball": "muzziball",
    "oslo metropolitan university": "oslo-metropolitan-university",
    "oslomet": "oslo-metropolitan-university",
    "inland norway university of applied sciences": "university-of-inland-norway",
    "university of inland norway": "university-of-inland-norway",
    "universitetet i innlandet": "university-of-inland-norway",
    "høgskolen i innlandet": "university-of-inland-norway",
}

NEW_INSTITUTIONS: dict[str, dict[str, str]] = {
    "teks-trondheim-electronic-arts-centre": {
        "name": "TEKS – Trondheim Electronic Arts Centre",
        "short_name": "TEKS",
        "website": "https://teks.no/",
    },
    "ostfold-museums": {
        "name": "Østfoldmuseene",
        "short_name": "Østfoldmuseene",
        "website": "https://ostfoldmuseene.no/",
    },
    "university-of-stuttgart": {
        "name": "University of Stuttgart",
        "short_name": "Stuttgart",
        "website": "https://www.uni-stuttgart.de/en/",
    },
    "skapia": {
        "name": "Skapia",
        "short_name": "Skapia",
        "website": "https://skapia.no/",
    },
    "anno": {
        "name": "Anno museum",
        "short_name": "ANNO",
        "website": "https://annomuseum.no/en",
    },
    "i-o-lab": {
        "name": "i/o/lab",
        "short_name": "i/o/lab",
        "website": "",
    },
    "storyphone": {
        "name": "StoryPhone AS",
        "short_name": "StoryPhone",
        "website": "https://www.storyphone.no/",
    },
    "bergen-international-festival": {
        "name": "Festspillene i Bergen",
        "short_name": "FiB",
        "website": "https://www.fib.no/en",
    },
    "muzziball": {
        "name": "Muzziball",
        "short_name": "Muzziball",
        "website": "",
    },
    "mf-norwegian-school-of-theology-religion-and-society": {
        "name": "MF Vitenskapelig høyskole",
        "short_name": "MF",
        "website": "https://www.mf.no/en",
    },
    "musikk-i-skolen": {
        "name": "Musikk i Skolen",
        "short_name": "MiS",
        "website": "https://www.musikkiskolen.no/",
    },
    "university-of-music-lubeck": {
        "name": "University of Music Lübeck",
        "short_name": "Lübeck",
        "website": "https://www.mh-luebeck.de/en/",
    },
    "norwegian-museum-of-music": {
        "name": "Norges musikkmuseum – Ringve og Rockheim",
        "short_name": "NMM",
        "website": "https://ringve.no/en",
    },
    "oslo-metropolitan-university": {
        "name": "Oslo Metropolitan University",
        "short_name": "OsloMet",
        "website": "https://www.oslomet.no/en",
    },
}


def normalize_institution_key(value: str) -> str:
    value = value.lower().strip()
    for src, dst in {"æ": "ae", "ø": "o", "å": "a", "ü": "u", "–": "-", "—": "-"}.items():
        value = value.replace(src, dst)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def build_institution_name_lookup(site_root: Path) -> dict[str, str]:
    lookup = {normalize_institution_key(k): v for k, v in INSTITUTION_NAME_MAP.items()}
    inst_root = site_root / "_directory" / "institutions"
    if not inst_root.exists():
        return lookup
    for child in sorted(inst_root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        index_md = child / "index.md"
        if not index_md.exists():
            continue
        data, _ = load_entry(index_md)
        slug = str(data.get("slug") or child.name).strip()
        for label in [data.get("name"), data.get("short_name"), slug.replace("-", " ")]:
            if isinstance(label, str) and label.strip():
                lookup[normalize_institution_key(label)] = slug
        for alias in data.get("aliases") or []:
            if isinstance(alias, str) and alias.strip():
                lookup[normalize_institution_key(alias)] = slug
    return lookup


def resolve_institution_slug(org_name: str, lookup: dict[str, str]) -> str:
    org_name = (org_name or "").strip()
    if not org_name:
        return ""
    key = normalize_institution_key(org_name)
    if key in lookup:
        return lookup[key]
    for known, slug in lookup.items():
        if len(known) >= 4 and (known in key or key in known):
            return slug
    return slugify(org_name)


def ensure_institution(
    slug: str,
    display_name: str,
    lookup: dict[str, str],
    *,
    dry_run: bool = False,
) -> str:
    if not slug:
        return ""
    inst_root = SITE_ROOT / "_directory" / "institutions"
    target = inst_root / slug / "index.md"
    if target.exists():
        return slug

    defaults = NEW_INSTITUTIONS.get(slug, {})
    name = defaults.get("name") or display_name or slug.replace("-", " ").title()
    short_name = defaults.get("short_name") or suggest_short_name(slug, name)
    website = defaults.get("website", "")

    data = {
        "type": "institution",
        "slug": slug,
        "name": name,
        "short_name": short_name,
        "permalink": f"/institutions/{slug}/",
        "redirect_from": [f"/directory/institutions/{slug}/"],
        "image": f"/images/institutions/{slug}.png",
        "people": [],
        "projects": [],
        "country": None,
        "city": None,
        "urls": {"website": website, "wikipedia": ""},
        "aliases": [],
        "tags": [],
        "search_keywords": [],
        "source_mentions": [],
    }

    if dry_run:
        print(f"create institution: {name} -> {target.relative_to(SITE_ROOT)}")
        return slug

    target.parent.mkdir(parents=True, exist_ok=True)
    save_entry(target, data, "Description coming soon.\n")
    lookup[normalize_institution_key(name)] = slug
    lookup[normalize_institution_key(short_name)] = slug
    print(f"Created institution {name}")
    return slug


def slugify(value: str) -> str:
    value = value.lower()
    for src, dst in {"æ": "ae", "ø": "o", "å": "a"}.items():
        value = value.replace(src, dst)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value).strip("-")
    return value[:80]


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if ORCID_ID_RE.match(value):
        return f"https://orcid.org/{value}"
    if value.startswith("orcid.org/"):
        return f"https://{value}"
    if "orcid.org/my-orcid" in value:
        match = re.search(r"orcid=((?:\d{4}-){3}[\dX]{4})", value, re.I)
        if match:
            return f"https://orcid.org/{match.group(1)}"
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
        value = f"https://{value.lstrip('/')}"
    return value


def first_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    for part in re.split(r"[\s,|]+", value):
        part = part.strip()
        if not part:
            continue
        if "." in part or part.startswith("http"):
            return normalize_url(part)
    return normalize_url(value)


def normalize_survey_row(row: dict) -> dict:
    out = dict(row)
    for new_key, canonical in SURVEY_COLUMN_ALIASES.items():
        raw = row.get(new_key)
        if raw is None:
            continue
        value = str(raw).strip()
        if value and not out.get(canonical):
            out[canonical] = value
    return out

def valid_nva_url(value: str) -> str:
    value = normalize_url(value)
    if not value or INVALID_NVA_RE.search(value):
        return ""
    if "nva.sikt.no/research-profile/" in value:
        return value
    return ""


def host_from_url(value: str) -> str:
    value = normalize_url(value)
    if not value:
        return ""
    host = urlparse(value).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def institution_from_orcid(orcid_url: str) -> tuple[str, str, str]:
    match = ORCID_PROFILE_RE.search(orcid_url or "")
    if not match:
        return "", "", ""
    lookup, _ = build_institution_lookup(SITE_ROOT)
    return orcid_primary_employment(match.group(1), lookup)


def institution_slug_from_email_domain(domain: str) -> str:
    domain = (domain or "").strip().lower()
    if not domain:
        return ""
    if domain in EMAIL_DOMAIN_TO_INSTITUTION:
        return EMAIL_DOMAIN_TO_INSTITUTION[domain]
    for known_domain, slug in EMAIL_DOMAIN_TO_INSTITUTION.items():
        if domain.endswith(f".{known_domain}"):
            return slug
    return ""


def institution_from_row(row: dict, lookup: dict[str, str]) -> str:
    org_name = (row.get("institution name") or row.get("Institution/Organisation") or "").strip()
    if org_name:
        slug = resolve_institution_slug(org_name, lookup)
        if slug:
            return slug

    email = (row.get("Email address") or "").strip().lower()
    if "@" in email:
        domain = email.split("@", 1)[1]
        slug = institution_slug_from_email_domain(domain)
        if slug:
            return slug

    for column in ("website (institution)", "website (personal)"):
        host = host_from_url(row.get(column, ""))
        if host in HOST_TO_INSTITUTION:
            return HOST_TO_INSTITUTION[host]
        for known_host, slug in HOST_TO_INSTITUTION.items():
            if host.endswith(known_host):
                return slug
    return ""


def parse_tags(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    tags: list[str] = []
    seen: set[str] = set()
    for part in re.split(r",\s*", raw.strip()):
        tag = part.strip().lstrip("#").strip()
        if not tag:
            continue
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            tags.append(tag)
    return tags


def parse_work_packages(row: dict) -> list[str]:
    wps: list[str] = []
    seen: set[str] = set()
    for key, value in row.items():
        if not value or "work package" not in str(key).lower():
            continue
        match = re.search(r"\bWP([1-7])\b", str(value), re.I)
        if not match:
            match = re.search(r"WP(\d)", str(key), re.I)
        if match:
            label = f"WP{match.group(1)}"
            if label.lower() not in seen:
                seen.add(label.lower())
                wps.append(label)
    for n in range(1, 8):
        value = (row.get(f"Work package(s).WP{n}") or "").strip()
        if value and value.upper() not in seen:
            seen.add(value.upper())
            wps.append(value.upper())
    return sorted(wps, key=lambda item: int(item[2:]))

def strip_wp_tags(items: list | None) -> list[str]:
    return [item for item in (items or []) if isinstance(item, str) and not WP_TAG_RE.match(item.strip())]


def merge_wps(existing: list | None, new_items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in list(existing or []) + list(new_items or []):
        if not isinstance(item, str):
            continue
        value = item.strip().upper()
        if not WP_TAG_RE.match(value):
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return sorted(out, key=lambda item: int(item[2:]))


def merge_unique(existing: list | None, new_items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in list(existing or []) + new_items:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def merge_urls(existing: dict | None, incoming: dict[str, str]) -> dict[str, str]:
    merged = {key: "" for key in URL_FIELDS + ("orcid", "nva")}
    for key, value in (existing or {}).items():
        if isinstance(value, str):
            merged[key] = value.strip()
    for key, value in incoming.items():
        if value and not merged.get(key):
            merged[key] = value
    return merged


def build_person_data(
    row: dict,
    existing: dict | None,
    lookup: dict[str, str],
    *,
    skip_orcid: bool = False,
) -> tuple[dict, str]:
    row = normalize_survey_row(row)
    name = (row.get("Name") or "").strip()
    existing = existing or {}
    existing_name = str(existing.get("name") or "").strip()
    if existing_name and len(existing_name.split()) > len(name.split()):
        name = existing_name
    slug = existing.get("slug") or slugify(name)
    institution = institution_from_row(row, lookup)
    wp_tags = parse_work_packages(row)
    csv_tags = merge_unique(
        merge_unique(
            parse_tags(row.get("Tags", "")),
            parse_tags(row.get("competency keywords", "")),
        ),
        parse_tags(row.get("interest keywords", "")),
    )
    comments = (row.get("Comments") or row.get("Anything else you want to add?") or "").strip()
    survey_position = (row.get("position") or row.get("Current position") or "").strip()
    survey_department = (row.get("department") or row.get("Unit") or "").strip()

    incoming_urls: dict[str, str] = {}
    for csv_col, url_key in CSV_URL_COLUMNS.items():
        raw = (row.get(csv_col) or "").strip()
        if not raw:
            continue
        if url_key in {"personal_website", "institutional_website"}:
            normalized = first_url(raw)
        elif url_key == "nva":
            normalized = valid_nva_url(raw)
        elif url_key == "orcid":
            normalized = normalize_url(raw)
            if "orcid.org" not in normalized:
                normalized = ""
        else:
            normalized = normalize_url(raw)
        if normalized:
            incoming_urls[url_key] = normalized

    if not institution and not skip_orcid:
        orcid_url = incoming_urls.get("orcid") or normalize_url((existing or {}).get("urls", {}).get("orcid", ""))
        if orcid_url:
            position, inst_slug, department = institution_from_orcid(orcid_url)
            institution = inst_slug
            if institution and not (existing or {}).get("position") and position:
                existing = dict(existing or {})
                existing.setdefault("position", position)
            if institution and not (existing or {}).get("department") and department and department != institution:
                existing = dict(existing or {})
                existing.setdefault("department", department)

    existing = existing or {}
    institutions = merge_unique(existing.get("institutions"), [institution] if institution else [])
    primary_institution = (
        str(existing.get("institution") or "").strip()
        or institution
        or (institutions[0] if institutions else "")
    )
    if primary_institution:
        institutions = merge_unique(institutions, [primary_institution])

    wps = merge_wps(existing.get("wps"), wp_tags)
    tags = merge_unique(strip_wp_tags(existing.get("tags")), csv_tags)
    search_keywords = merge_unique(strip_wp_tags(existing.get("search_keywords")), tags)

    data = {
        "type": "person",
        "slug": slug,
        "name": name,
        "title": name,
        "position": existing.get("position") or survey_position or "",
        "department": existing.get("department") or survey_department or "",
        "institution": primary_institution,
        "institutions": institutions,
        "wps": wps,
        "projects": existing.get("projects") or [],
        "roles": parse_survey_roles(row),
        "urls": merge_urls(existing.get("urls"), incoming_urls),
        "aliases": existing.get("aliases") or [],
        "tags": tags,
        "search_keywords": search_keywords,
        "selected_works": existing.get("selected_works") or [],
        "source_mentions": existing.get("source_mentions") or [],
        "summary": existing.get("summary") or (comments if comments and not comments.lower().startswith("more sites:") else None),
        "permalink": existing.get("permalink") or f"/people/{slug}/",
        "redirect_from": existing.get("redirect_from") or [f"/directory/people/{slug}/"],
    }

    for optional in ("layout", "image", "nva_affiliations", "affiliation_units", "published"):
        if optional in existing and existing[optional] not in (None, "", []):
            data[optional] = existing[optional]

    if not data.get("summary"):
        data.pop("summary", None)

    if existing and existing.get("_body"):
        body = existing["_body"]
        if comments and comments not in body and not comments.lower().startswith("more sites:"):
            body = f"{body.rstrip()}\n\n{comments}\n"
    elif comments and not comments.lower().startswith("more sites:"):
        body = f"{comments}\n"
    else:
        body = "Bio coming soon.\n"

    return data, body


def find_existing_slug(people_root: Path, name: str, email: str = "") -> Path | None:
    slug = slugify(name)
    candidate = people_root / slug / "index.md"
    if candidate.exists():
        return candidate

    email = (email or "").strip().lower()
    if "@" in email:
        local = email.split("@", 1)[0].replace(".", "-").replace("_", "-")
        for variant in {local, slugify(local)}:
            if not variant:
                continue
            email_candidate = people_root / variant / "index.md"
            if email_candidate.exists():
                return email_candidate

    target = name.strip().lower()
    for index_md in people_root.glob("*/index.md"):
        if index_md.parent.name in {"_template"}:
            continue
        data, _ = load_entry(index_md)
        if str(data.get("name", "")).strip().lower() == target:
            return index_md

    name_slug = slugify(name)
    if name_slug.count("-") >= 2:
        tail = "-".join(name_slug.split("-")[-2:])
        for index_md in people_root.glob("*/index.md"):
            if index_md.parent.name in {"_template"}:
                continue
            if index_md.parent.name == tail or index_md.parent.name.endswith(f"-{tail}"):
                return index_md
    return None


def load_survey_rows(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=";"))

    if suffix in {".xlsx", ".xlsm"}:
        try:
            import openpyxl
        except ImportError as exc:
            raise SystemExit("openpyxl is required for .xlsx imports (pip install openpyxl)") from exc
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        worksheet = workbook.active
        rows = list(worksheet.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        parsed: list[dict[str, str]] = []
        for row in rows[1:]:
            values = ["" if cell is None else str(cell).strip() for cell in row]
            if not any(values):
                continue
            parsed.append(dict(zip(headers, values)))
        return parsed

    raise SystemExit(f"Unsupported survey file type: {path.suffix}")


def import_csv(csv_path: Path, dry_run: bool = False, *, full_members_only: bool = True) -> dict[str, int]:
    people_root = SITE_ROOT / "_directory" / "people"
    stats = {"created": 0, "updated": 0, "skipped": 0, "skipped_not_full_member": 0, "institutions_created": 0}
    lookup = build_institution_name_lookup(SITE_ROOT)
    rows = [normalize_survey_row(row) for row in load_survey_rows(csv_path)]

    if full_members_only:
        stats["skipped_not_full_member"] = sum(1 for row in rows if not is_full_member(row))
        rows = [row for row in rows if is_full_member(row)]

    pending_institutions: dict[str, str] = {}
    for row in rows:
        org_name = (row.get("institution name") or row.get("Institution/Organisation") or "").strip()
        if org_name:
            slug = resolve_institution_slug(org_name, lookup)
            if slug:
                pending_institutions.setdefault(slug, org_name)
        slug = institution_from_row(row, lookup)
        if slug and slug in NEW_INSTITUTIONS and slug not in pending_institutions:
            pending_institutions[slug] = NEW_INSTITUTIONS[slug].get("name", slug)

    for slug, org_name in sorted(pending_institutions.items()):
        before = (SITE_ROOT / "_directory" / "institutions" / slug / "index.md").exists()
        ensure_institution(slug, org_name, lookup, dry_run=dry_run)
        if not before and not dry_run and (SITE_ROOT / "_directory" / "institutions" / slug / "index.md").exists():
            stats["institutions_created"] += 1

    for row in rows:
        name = (row.get("Name") or "").strip()
        if not name:
            stats["skipped"] += 1
            continue

        existing_path = find_existing_slug(people_root, name, row.get("Email address", ""))
        existing_data: dict | None = None
        existing_body = ""
        if existing_path:
            existing_data, existing_body = load_entry(existing_path)
            existing_data["_body"] = existing_body

        data, body = build_person_data(row, existing_data, lookup, skip_orcid=dry_run)
        slug = data["slug"]
        target = people_root / slug / "index.md"

        if dry_run:
            action = "update" if existing_path else "create"
            print(f"{action}: {name} -> {target.relative_to(SITE_ROOT)}")
            if existing_path:
                stats["updated"] += 1
            else:
                stats["created"] += 1
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        save_entry(target, data, body)
        if existing_path:
            stats["updated"] += 1
            print(f"Updated {name}")
        else:
            stats["created"] += 1
            print(f"Created {name}")

    if not dry_run:
        sync_directory(SITE_ROOT, dry_run=False)

    return stats


def fill_missing_institutions(dry_run: bool = False) -> int:
    """Add institution affiliations from ORCID for people missing them."""
    people_root = SITE_ROOT / "_directory" / "people"
    updated = 0
    for index_md in sorted(people_root.glob("*/index.md")):
        if index_md.parent.name.startswith("_"):
            continue
        data, body = load_entry(index_md)
        insts = [i for i in (data.get("institutions") or []) if isinstance(i, str) and i.strip()]
        primary = str(data.get("institution") or "").strip()
        if insts or primary:
            continue
        orcid_url = normalize_url((data.get("urls") or {}).get("orcid", ""))
        if not orcid_url:
            continue
        position, institution, department = institution_from_orcid(orcid_url)
        if not institution:
            continue
        data["institution"] = institution
        data["institutions"] = [institution]
        if position and not data.get("position"):
            data["position"] = position
        if department and department != institution and not data.get("department"):
            data["department"] = department
        if dry_run:
            print(f"would update {data.get('name')} -> {institution}")
        else:
            save_entry(index_md, data, body)
            print(f"Updated {data.get('name')} -> {institution}")
        updated += 1
    if updated and not dry_run:
        sync_directory(SITE_ROOT, dry_run=False)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", type=Path, help="Path to survey CSV or XLSX export")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--all-members",
        action="store_true",
        help="Import all survey respondents, not only full members",
    )
    parser.add_argument(
        "--fill-missing-institutions",
        action="store_true",
        help="Fill missing affiliations from ORCID for all directory people",
    )
    args = parser.parse_args()

    if args.fill_missing_institutions:
        count = fill_missing_institutions(dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Filled institutions for {count} people.")
        return

    if not args.csv_path:
        parser.error("csv_path is required unless --fill-missing-institutions is used")

    stats = import_csv(args.csv_path.resolve(), dry_run=args.dry_run, full_members_only=not args.all_members)
    if args.dry_run:
        print(
            f"Dry run: {stats['created']} would be created, "
            f"{stats['updated']} would be updated, "
            f"{stats['skipped_not_full_member']} skipped (not full members)."
        )
    else:
        print(
            "Done: "
            f"{stats['created']} people created, "
            f"{stats['updated']} updated, "
            f"{stats['institutions_created']} institutions created, "
            f"{stats['skipped']} skipped."
        )
        if stats["skipped_not_full_member"]:
            print(f"Skipped {stats['skipped_not_full_member']} respondents who are not full members.")
        if not args.all_members:
            print("Only full members were imported (use --all-members to import everyone).")


if __name__ == "__main__":
    main()
