#!/usr/bin/env python3
"""Shared helpers for XLSX-based people import scripts.

Two spreadsheet layouts are understood:

- the MishMash participation form (``Do you want to be added to the MishMash
  directory?``, ``Institution/Organisation``, ``Unit``, ``Current position``,
  ``Work Package(s) you are interested in joining.WP1: …`` columns and two
  keyword columns) — an *intake* sheet, where only rows answering ``Yes`` are
  imported;
- the directory update form (``Work package(s).WP1`` … columns, ``Tags``) — an
  *existing-member* sheet, where every row is applied.

Both share the URL columns (``orcid``, ``nva``, ``github`` …).

Merge rules, so that re-running an import (the forms are cumulative exports)
never destroys curated data:

- ``name``/``title`` are set only on new entries.
- URL fields are filled or replaced, except ``orcid``/``nva`` on an existing
  entry, which are never replaced by a different value.
- ``wps`` is the union of the stored and submitted work packages.
- ``position``, ``department``, ``institution``, ``tags`` are set on new
  entries and only fill *empty* fields on existing ones. Profiles with
  ``urls.nva`` get these fields overwritten by the nightly NVA sync anyway.
- The institution name is resolved against the ``name``, ``short_name``,
  ``slug`` and ``aliases`` of the entries in ``site/_directory/institutions``
  (exact match after normalisation, no fuzzy matching). Unresolved names are
  reported as warnings so a human can create the institution or add an alias
  and re-run; the person's ``institution`` is left empty in the meantime.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
import sys
import unicodedata

try:
    from openpyxl import load_workbook
except Exception:
    print("ERROR: openpyxl is required. Install with: pip install openpyxl", file=sys.stderr)
    raise

from directory_io import load_entry, save_entry


INCLUDE_CANDIDATES = [
    "include",
    "include in directory",
    "do you want to be added to the mishmash directory",
    "added to the mishmash directory",
    "add to directory",
    "include?",
    "in directory",
    "include_flag",
    "add_flag",
    "publish",
    "published",
    "add_to_directory",
]

URL_FIELD_ALIASES = {
    "personal_website": ["web page (personal)", "website (personal)", "personal website"],
    "institutional_website": ["web page (institutional)", "website (institution)", "institutional website"],
    "github": ["github"],
    "linkedin": ["linkedin"],
    "youtube": ["youtube"],
    "facebook": ["facebook"],
    "mastodon": ["mastodon"],
    "instagram": ["instagram"],
    "bluesky": ["bluesky"],
    "orcid": ["orcid"],
    "nva": ["nva"],
}

# Profile columns are matched on the *whole* normalised header, never by
# substring: "institution" as a substring would also hit "web page
# (institutional)".
PROFILE_FIELD_HEADERS = {
    "institution_name": ["institution/organisation", "institution/organization", "institution", "organisation", "organization"],
    "department": ["unit", "department"],
    "position": ["current position", "position"],
}

KEYWORD_HEADER_PREFIXES = [
    "keywords describing your competencies",
    "keywords describing your interests",
    "tags",
]

# Work-package columns of the participation form carry the WP in the header
# ("Work Package(s) you are interested in joining.WP1: …") and in the value
# when ticked. Columns about project ideas ("Which WP(s) does it connect
# to?") are not membership and are skipped.
WP_HEADER_MARKERS = ("work package",)
WP_HEADER_SKIP = ("connect to",)
WP_RE = re.compile(r"\bWP\s*([1-7])\b", re.IGNORECASE)

# CONTRIBUTING.md asks for 2-6 tags per profile.
MAX_TAGS = 6


def canonical_orcid_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    # Accept any input containing an ORCID iD (bare, path, or e.g. a
    # my-orcid?orcid=... dashboard URL) and canonicalize it.
    match = re.search(r"(\d{4}-\d{4}-\d{4}-[\dX]{4})", value, flags=re.IGNORECASE)
    if match:
        return f"https://orcid.org/{match.group(1).upper()}"
    # A bare 16-digit iD typed without hyphens.
    match = re.fullmatch(r"(\d{4})(\d{4})(\d{4})(\d{3}[\dX])", value, flags=re.IGNORECASE)
    if match:
        return "https://orcid.org/" + "-".join(match.groups()).upper()
    return value


def canonical_nva_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    match = re.search(r"research-profile/(\d+)", value)
    if match:
        return f"https://nva.sikt.no/research-profile/{match.group(1)}"
    if value.isdigit():
        return f"https://nva.sikt.no/research-profile/{value}"
    if value.startswith("https://nva.sikt.no/") or value.startswith("http://nva.sikt.no/"):
        # nva.sikt.no URLs without a research-profile id (my-page dashboards,
        # search links) identify nothing; drop them so they cannot clobber a
        # previously stored profile URL.
        return ""
    return ""


def normalize_http_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    # Repair a scheme typed with a single slash ("https:/example.org").
    value = re.sub(r"^(https?):/(?!/)", r"\1://", value, flags=re.IGNORECASE)
    if value.startswith("http://"):
        return "https://" + value.removeprefix("http://")
    if value.startswith("https://"):
        return value
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
        return value
    return f"https://{value.lstrip('/')}"


def first_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    for part in re.split(r"[\s,|]+", value):
        part = part.strip()
        if not part:
            continue
        if "." in part or part.startswith("http"):
            return normalize_http_url(part)
    return normalize_http_url(value)


def normalize_field_value(field_name: str, value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if field_name == "orcid":
        return canonical_orcid_url(value)
    if field_name == "nva":
        return canonical_nva_url(value)
    if field_name in {"personal_website", "institutional_website", "github", "linkedin", "youtube", "facebook"}:
        return first_url(value)
    if field_name == "instagram":
        cleaned = value.removeprefix("@").strip().strip("/")
        if "instagram.com" in cleaned:
            return first_url(cleaned)
        return f"https://www.instagram.com/{cleaned}/" if cleaned else ""
    if field_name == "mastodon":
        cleaned = value.strip().removeprefix("@").strip().strip("/")
        if "@" in cleaned and not cleaned.startswith("http"):
            handle, instance = cleaned.split("@", 1)
            if handle and instance:
                return f"https://{instance}/@{handle}"
        return first_url(cleaned)
    if field_name == "bluesky":
        cleaned = value.removeprefix("@").strip().strip("/")
        if "bsky.app/profile/" in cleaned:
            return first_url(cleaned)
        if cleaned.endswith(".bsky.social") or ".bsky.social/" in cleaned:
            handle = cleaned.split("/", 1)[0]
            return f"https://bsky.app/profile/{handle}"
        return first_url(cleaned)
    return value


SOCIAL_HOSTS = {"linkedin.com": "linkedin", "github.com": "github"}


def route_social_urls(urls: dict) -> None:
    """Move a LinkedIn or GitHub address typed into a website field to its own field.

    People often paste their LinkedIn page as "personal web page"; the
    profile has a dedicated slot for it and the website slot should stay free
    for an actual homepage.
    """
    for field in ("personal_website", "institutional_website"):
        value = urls.get(field) or ""
        host = re.sub(r"^https?://(www\.)?", "", value.lower()).split("/", 1)[0]
        for social_host, target in SOCIAL_HOSTS.items():
            if host == social_host or host.endswith("." + social_host):
                if not urls.get(target):
                    urls[target] = value
                del urls[field]
                break


def canonical_website_url(value: str) -> str:
    return normalize_http_url(value).rstrip("/") if value else ""


def dedupe_website_pair(urls: dict) -> bool:
    personal = canonical_website_url(urls.get("personal_website") or "")
    institutional = canonical_website_url(urls.get("institutional_website") or "")
    if personal and institutional and personal == institutional:
        if urls.get("institutional_website") != "":
            urls["institutional_website"] = ""
            return True
    return False


def slugify(value: str) -> str:
    # NFKD leaves ø/æ (and their upper-case forms) undecomposed, so fold them
    # explicitly before stripping to ASCII; otherwise Løve becomes lve.
    value = value.translate(str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "Ae", "ß": "ss"}))
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value[:80].strip("-")


def fix_name_case(name: str) -> str:
    """Title-case names submitted in all caps or all lower case.

    Mixed-case names are left untouched so curated forms like
    "von Arnim" or "de Seta" are never mangled.
    """
    if name and (name == name.upper() or name == name.lower()):
        return " ".join(part.capitalize() for part in name.split())
    return name


def truthy(value) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"y", "yes", "true", "1", "x", "include"}


def find_column(headers, candidates):
    for candidate in candidates:
        for index, header in enumerate(headers):
            if header and candidate in header:
                return index
    return None


def find_exact_column(headers, names):
    for name in names:
        for index, header in enumerate(headers):
            if header == name:
                return index
    return None


def normalize_header(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def cell_text(row, index):
    if index is None or index >= len(row):
        return ""
    value = row[index]
    if value is None:
        return ""
    return str(value).strip()


def find_first_value(row, headers, aliases):
    index = find_column(headers, aliases)
    return cell_text(row, index)


def parse_tags(*raw_values: str, max_tags: int = MAX_TAGS) -> list[str]:
    """Split free-text keyword fields into a deduplicated tag list."""
    tags: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        for part in re.split(r"[,;·|\n]+", raw or ""):
            tag = part.strip().strip(".").lstrip("#").strip()
            if not tag or len(tag) > 60:
                continue
            key = tag.casefold()
            if key in seen:
                continue
            seen.add(key)
            tags.append(tag)
            if len(tags) >= max_tags:
                return tags
    return tags


def wp_column_indexes(headers) -> list[int]:
    indexes = []
    for index, header in enumerate(headers):
        if not header or not any(marker in header for marker in WP_HEADER_MARKERS):
            continue
        if any(skip in header for skip in WP_HEADER_SKIP):
            continue
        indexes.append(index)
    return indexes


def parse_wps(row, headers, indexes) -> list[str]:
    wps: set[str] = set()
    for index in indexes:
        value = cell_text(row, index)
        if not value:
            continue
        match = WP_RE.search(value) or WP_RE.search(headers[index])
        if match:
            wps.add(f"WP{match.group(1)}")
    return sort_wps(wps)


def merge_wps(existing, new_items) -> list[str]:
    """Union of two work-package lists, normalised and sorted (WP1..WP7)."""
    return sort_wps(list(existing or []) + list(new_items or []))


def sort_wps(values) -> list[str]:
    cleaned = {str(v).strip().upper() for v in values or [] if str(v).strip()}
    cleaned = {v for v in cleaned if re.fullmatch(r"WP[1-7]", v)}
    return sorted(cleaned, key=lambda item: int(item[2:]))


def read_people(path: Path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    worksheet = workbook.active
    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        return [], "new"

    headers = [normalize_header(cell) for cell in rows[0]]
    name_idx = find_exact_column(headers, ["name", "full name", "display name"])
    if name_idx is None:
        name_idx = find_column(headers, ["name", "full name", "display name"]) or 0
    include_idx = find_column(headers, INCLUDE_CANDIDATES)
    sheet_kind = "new" if include_idx is not None else "existing"

    profile_idx = {field: find_exact_column(headers, names) for field, names in PROFILE_FIELD_HEADERS.items()}
    keyword_idx = [i for i, h in enumerate(headers) if h and any(h.startswith(p) for p in KEYWORD_HEADER_PREFIXES)]
    wp_idx = wp_column_indexes(headers)

    people = []
    for row in rows[1:]:
        if not row or all(cell is None for cell in row):
            continue
        name = fix_name_case(cell_text(row, name_idx))
        if not name:
            continue

        if sheet_kind == "new" and not truthy(row[include_idx]):
            continue

        urls = {}
        for field_name, aliases in URL_FIELD_ALIASES.items():
            value = find_first_value(row, headers, aliases)
            if value:
                normalized = normalize_field_value(field_name, value)
                if normalized:
                    urls[field_name] = normalized

        route_social_urls(urls)
        profile = {field: cell_text(row, index) for field, index in profile_idx.items()}
        profile["wps"] = parse_wps(row, headers, wp_idx)
        profile["tags"] = parse_tags(*(cell_text(row, i) for i in keyword_idx))

        people.append(
            {
                "name": name,
                "slug": slugify(name),
                "urls": urls,
                "profile": profile,
                "sheet_kind": sheet_kind,
            }
        )

    for person in people:
        dedupe_website_pair(person["urls"])

    return people, sheet_kind


WEBSITE_PAIR = {"personal_website": "institutional_website", "institutional_website": "personal_website"}

# Fields that identify a person; a stored value is never silently replaced
# by a different one from a form row (cumulative exports resubmit old
# mistakes on every import).
IDENTITY_URL_FIELDS = ("orcid", "nva")


def normalize_institution_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def build_institution_lookup(institutions_root: Path) -> dict[str, str]:
    """Map normalised institution names, short names, slugs and aliases to slugs."""
    lookup: dict[str, str] = {}
    if not institutions_root.is_dir():
        return lookup
    for child in sorted(institutions_root.iterdir()):
        index_md = child / "index.md"
        if child.name.startswith("_") or not index_md.exists():
            continue
        try:
            data, _ = load_entry(index_md)
        except ValueError:
            continue
        slug = str(data.get("slug") or child.name).strip() or child.name
        labels = [slug, slug.replace("-", " "), data.get("name"), data.get("short_name")]
        labels += list(data.get("aliases") or [])
        for label in labels:
            key = normalize_institution_key(label) if isinstance(label, str) else ""
            if key:
                lookup.setdefault(key, slug)
    return lookup


def resolve_institution(name: str, lookup: dict[str, str] | None) -> str:
    if not name or not lookup:
        return ""
    return lookup.get(normalize_institution_key(name), "")


def _is_empty(value) -> bool:
    return value in (None, "", [], {})


def apply_person_to_entry(
    data: dict,
    person: dict,
    is_new: bool = True,
    warnings: list | None = None,
    institution_lookup: dict[str, str] | None = None,
) -> dict:
    updated = deepcopy(data)
    updated["slug"] = person["slug"]
    if is_new or not str(updated.get("name") or "").strip():
        updated["name"] = person["name"]
        updated["title"] = person["name"]
    urls = updated.setdefault("urls", {})
    for field_name, value in person.get("urls", {}).items():
        if not value:
            continue
        normalized = normalize_field_value(field_name, value)
        if not normalized:
            continue
        existing = str(urls.get(field_name) or "").strip()
        if (
            not is_new
            and field_name in IDENTITY_URL_FIELDS
            and existing
            and existing != normalized
        ):
            if warnings is not None:
                warnings.append(
                    f"{person['slug']}: kept {field_name} {existing} (form submitted {normalized})"
                )
            continue
        if field_name in WEBSITE_PAIR:
            # The same address submitted as both personal and institutional
            # site: keep whatever the entry already has in the other slot
            # rather than blanking a stored URL.
            other = str(urls.get(WEBSITE_PAIR[field_name]) or "").strip()
            if other and canonical_website_url(other) == canonical_website_url(normalized):
                continue
        urls[field_name] = normalized
    for field_name, value in list(urls.items()):
        normalized = normalize_field_value(field_name, value)
        if normalized:
            urls[field_name] = normalized
    dedupe_website_pair(urls)

    profile = person.get("profile") or {}

    for field in ("position", "department"):
        value = (profile.get(field) or "").strip()
        if value and _is_empty(updated.get(field)):
            updated[field] = value

    submitted_wps = profile.get("wps") or []
    if submitted_wps:
        updated["wps"] = sort_wps(list(updated.get("wps") or []) + list(submitted_wps))

    tags = profile.get("tags") or []
    if tags and _is_empty(updated.get("tags")):
        updated["tags"] = list(tags)
        if _is_empty(updated.get("search_keywords")):
            updated["search_keywords"] = list(tags)

    institution_name = (profile.get("institution_name") or "").strip()
    if institution_name and _is_empty(updated.get("institution")):
        slug = resolve_institution(institution_name, institution_lookup)
        if slug:
            updated["institution"] = slug
            institutions = [i for i in (updated.get("institutions") or []) if isinstance(i, str) and i]
            if slug not in institutions:
                institutions.append(slug)
            updated["institutions"] = institutions
        elif warnings is not None:
            warnings.append(
                f"{person['slug']}: unresolved institution '{institution_name}' "
                "(create the institution entry or add the name to its aliases, then re-run)"
            )

    return updated


def build_alias_map(out_base: Path) -> dict:
    """Map slugified names and aliases of existing entries to their slug.

    Lets a form row that uses a nickname or short name (e.g. "Shayan" for
    shayan-dadman) update the existing entry instead of creating a duplicate.
    """
    alias_map = {}
    if not out_base.is_dir():
        return alias_map
    for child in sorted(out_base.iterdir()):
        index_md = child / "index.md"
        if child.name.startswith("_") or not index_md.exists():
            continue
        try:
            data, _ = load_entry(index_md)
        except ValueError:
            continue
        candidates = [str(data.get("name") or "")] + [str(a) for a in data.get("aliases") or []]
        for candidate in candidates:
            key = slugify(candidate)
            if key and key != child.name:
                alias_map[key] = child.name
    return alias_map


def drop_duplicate_identity_values(people, warnings: list) -> None:
    """Remove orcid/nva values submitted by rows for different people.

    Two people cannot share an ORCID or NVA profile, so such a value is a
    copy-paste mistake in at least one row; it is applied to neither.
    Multiple rows from the same person (common in cumulative exports) are
    fine and left alone.
    """
    for field_name in IDENTITY_URL_FIELDS:
        owners = {}
        for person in people:
            value = person.get("urls", {}).get(field_name)
            if value:
                owners.setdefault(value, set()).add(person["slug"])
        for person in people:
            value = person.get("urls", {}).get(field_name)
            if value and len(owners[value]) > 1:
                others = sorted(owners[value] - {person["slug"]})
                warnings.append(
                    f"{person['slug']}: dropped {field_name} {value} (also submitted by {', '.join(others)})"
                )
                del person["urls"][field_name]


def import_people(
    people,
    template_path: Path,
    out_base: Path,
    institutions_root: Path | None = None,
    dry_run: bool = False,
):
    """Create or update people entries. Returns (created, updated, warnings).

    ``institutions_root`` defaults to the ``institutions`` folder next to
    ``out_base``. With ``dry_run`` nothing is written; the planned actions are
    printed instead.
    """
    template_data, template_body = load_entry(template_path)
    created = 0
    updated = 0
    warnings: list[str] = []
    if not dry_run:
        out_base.mkdir(parents=True, exist_ok=True)
    alias_map = build_alias_map(out_base)
    if institutions_root is None:
        institutions_root = out_base.parent / "institutions"
    institution_lookup = build_institution_lookup(institutions_root)

    drop_duplicate_identity_values(people, warnings)

    for person in people:
        slug = person["slug"]
        if not slug:
            print(f"Skipping name with empty slug: {person['name']}")
            continue

        if not (out_base / slug / "index.md").exists() and slug in alias_map:
            warnings.append(f"{slug}: matched existing entry {alias_map[slug]} via alias")
            slug = alias_map[slug]
            person = {**person, "slug": slug}

        out_dir = out_base / slug
        out_file = out_dir / "index.md"
        if out_file.exists():
            data, body = load_entry(out_file)
            updated_data = apply_person_to_entry(
                data, person, is_new=False, warnings=warnings, institution_lookup=institution_lookup
            )
            if dry_run:
                print(f"update: {person['name']} -> {out_file}")
            elif updated_data != data:
                save_entry(out_file, updated_data, body)
            updated += 1
            continue

        created_data = apply_person_to_entry(
            template_data, person, warnings=warnings, institution_lookup=institution_lookup
        )
        created_data["permalink"] = f"/people/{slug}/"
        if dry_run:
            print(f"create: {person['name']} -> {out_file}")
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            save_entry(out_file, created_data, template_body)
        created += 1

    for warning in warnings:
        print(f"  WARNING: {warning}")

    return created, updated, warnings
