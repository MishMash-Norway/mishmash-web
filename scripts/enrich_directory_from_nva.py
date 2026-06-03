#!/usr/bin/env python3
import argparse
import os
import re
from io import BytesIO
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw


PERSON_PROFILE_RE = re.compile(r"/research-profile/(\d+)")
CRISTIN_RE = re.compile(r"/cristin/person/(\d+)")
ORCID_PROFILE_RE = re.compile(r"orcid\.org/((?:\d{4}-){3}[\dX]{4})", re.IGNORECASE)
PORTRAITS_CIRCLE_DIR = "assets/images/portraits/circle"
PORTRAIT_MAX_SIZE = 300
DEFAULT_MAX_WORKS = 10
DEFAULT_MAX_TAGS = 12

INSTITUTION_ABBREV = {
    "university-of-oslo": "UiO",
    "university-of-bergen": "UiB",
    "norwegian-university-of-science-and-technology": "NTNU",
    "oslo-school-of-architecture-and-design": "AHO",
    "norwegian-academy-of-music": "NMH",
    "simula-metropolitan-center-for-digital-engineering": "Simula",
    "norsus-norwegian-institute-for-sustainability-research": "NORSUS",
    "arctic-university-of-norway": "UiT",
    "university-of-agder": "UiA",
    "ostfold-university-college": "HiO",
    "inland-norway-university-of-applied-sciences": "INN",
    "western-norway-university-of-applied-sciences": "HVL",
    "oslo-national-academy-of-the-arts": "KHiO",
}

PUBLICATION_TYPE_LABELS = {
    "AcademicArticle": "Journal article",
    "AcademicChapter": "Book chapter",
    "BookAnthology": "Book",
    "ConferenceLecture": "Conference",
    "OtherPresentation": "Presentation",
    "ArtisticDesign": "Design",
}


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


def extract_orcid_id(orcid_url: str) -> str | None:
    if not orcid_url:
        return None
    match = ORCID_PROFILE_RE.search(orcid_url)
    if match:
        return match.group(1)
    cleaned = orcid_url.strip().strip("/")
    if re.fullmatch(r"(?:\d{4}-){3}[\dX]{4}", cleaned, flags=re.IGNORECASE):
        return cleaned.upper()
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


def get_orcid_json(url: str):
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()


def prefer(primary, fallback):
    if primary not in (None, "", [], {}):
        return primary
    return fallback


def normalize_publication_year(year) -> str:
    if year is None:
        return ""
    text = str(year).strip()
    if not text:
        return ""
    if len(text) == 2 and text.isdigit():
        century = "20" if int(text) < 70 else "19"
        return century + text
    return text


def work_sort_key(work: dict) -> int:
    year = normalize_publication_year(work.get("year"))
    try:
        return int(year[:4])
    except ValueError:
        return 0


def localized_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return (value.get("en") or value.get("nb") or value.get("no") or "").strip()
    return ""


def institution_abbrev(slug: str) -> str:
    if not slug:
        return "Org"
    if slug in INSTITUTION_ABBREV:
        return INSTITUTION_ABBREV[slug]
    parts = [p for p in slug.split("-") if p]
    if not parts:
        return "Org"
    return "".join(part[:1].upper() + part[1:3] for part in parts[:2])


def portrait_filename(name: str, institution_slug: str) -> str:
    parts = [p for p in re.sub(r"\([^)]*\)", " ", name).split() if p]
    stem = "_".join(parts) if parts else "person"
    return f"{stem}_{institution_abbrev(institution_slug)}.png"


def save_circle_portrait(image_bytes: bytes, dest_path: Path, max_size: int = PORTRAIT_MAX_SIZE) -> None:
    with Image.open(BytesIO(image_bytes)) as opened:
        img = opened.convert("RGBA")
        size = min(img.size)
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        img = img.crop((left, top, left + size, top + size))
        if size > max_size:
            img = img.resize((max_size, max_size), Image.Resampling.LANCZOS)
            size = max_size

        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(dest_path)


def download_nva_portrait(image_url: str, dest_path: Path) -> bool:
    if not image_url:
        return False
    headers = {}
    token = os.environ.get("NVA_API_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()
        content_type = (response.headers.get("Content-Type") or "").lower()
        if content_type.startswith("application/json"):
            return False
        save_circle_portrait(response.content, dest_path)
        return True
    except Exception:
        return False


def nva_publication_source(reference: dict) -> str:
    reference = reference or {}
    instance = reference.get("publicationInstance") or {}
    raw_type = instance.get("type") or ""
    if raw_type in PUBLICATION_TYPE_LABELS:
        return PUBLICATION_TYPE_LABELS[raw_type]
    return raw_type.replace("Academic", "").strip() or "Publication"


def find_doi_in_object(node) -> str:
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() == "doi" and isinstance(value, str) and value.strip():
                return value.strip()
            found = find_doi_in_object(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = find_doi_in_object(item)
            if found:
                return found
    return ""


def nva_publication_url(hit: dict) -> str:
    for artifact in hit.get("associatedArtifacts") or []:
        if artifact.get("type") == "AssociatedLink" and artifact.get("id"):
            return artifact["id"].strip()

    doi = find_doi_in_object(hit.get("entityDescription") or {})
    if doi:
        if doi.startswith("http"):
            return doi
        return f"https://doi.org/{doi.lstrip('https://doi.org/')}"
    return ""


def nva_selected_works(profile_id: str, max_works: int) -> list[dict[str, str]]:
    response = requests.get(
        "https://api.nva.unit.no/search/resources",
        params={"contributor": profile_id, "results": max(max_works * 3, 30)},
        timeout=30,
    )
    response.raise_for_status()
    works = []
    seen = set()

    for hit in response.json().get("hits") or []:
        entity = hit.get("entityDescription") or {}
        title = localized_text(entity.get("mainTitle"))
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        publication_date = entity.get("publicationDate") or {}
        year = ""
        if isinstance(publication_date, dict):
            year = normalize_publication_year(publication_date.get("year"))

        work = {"title": title}
        if year:
            work["year"] = year
        source = nva_publication_source(entity.get("reference") or {})
        if source:
            work["source"] = source
        url = nva_publication_url(hit)
        if url:
            work["url"] = url
        works.append(work)

    works.sort(key=work_sort_key, reverse=True)
    return works[:max_works]


def fetch_nva_bundle(
    profile_id: str,
    institution_lookup: dict[str, str],
    org_cache: dict,
    max_tags: int,
    max_works: int,
) -> dict:
    profile = get_json(f"https://api.nva.unit.no/cristin/person/{profile_id}")
    affiliation = pick_active_affiliation(profile.get("affiliations") or [])
    role_labels = ((affiliation.get("role") or {}).get("labels") or {})
    position = role_labels.get("en") or role_labels.get("nb") or ""
    org_name = fetch_org_name((affiliation.get("organization") or "").strip(), org_cache)
    org_slug = institution_lookup.get(slugify(org_name), "") if org_name else ""

    affiliations = []
    if org_slug:
        affiliations.append(org_slug)

    return {
        "name": names_to_full_name(profile.get("names") or []),
        "position": position,
        "institution": org_slug,
        "institutions": affiliations,
        "tags": keyword_labels(profile.get("keywords") or [], max_keywords=max_tags),
        "summary": background_to_summary(profile.get("background")),
        "image_url": (profile.get("image") or "").strip(),
        "orcid": find_orcid(profile.get("identifiers") or []),
        "website": ((profile.get("contactDetails") or {}).get("webPage") or "").strip(),
        "selected_works": nva_selected_works(profile_id, max_works=max_works),
        "profile_id": profile_id,
    }


def orcid_primary_employment(orcid_id: str, institution_lookup: dict[str, str]) -> tuple[str, str, str]:
    data = get_orcid_json(f"https://pub.orcid.org/v3.0/{orcid_id}/employments")
    candidates = []
    for group in data.get("affiliation-group") or []:
        for summary in group.get("summaries") or []:
            employment = summary.get("employment-summary") or {}
            if not employment:
                continue
            organization = employment.get("organization") or {}
            org_name = orcid_text_value(organization.get("name"))
            position = orcid_text_value(employment.get("role-title"))
            org_slug = institution_lookup.get(slugify(org_name), "") if org_name else ""
            display_index = orcid_text_value(employment.get("display-index"))
            try:
                rank = int(display_index)
            except ValueError:
                rank = 999
            candidates.append((rank, position, org_slug, org_name))

    if not candidates:
        return "", "", ""

    candidates.sort(key=lambda item: item[0])
    _, position, org_slug, _ = candidates[0]
    return position, org_slug, org_slug


def fetch_orcid_bundle(orcid_id: str, institution_lookup: dict[str, str], max_tags: int, max_works: int) -> dict:
    person = get_orcid_json(f"https://pub.orcid.org/v3.0/{orcid_id}/person")
    position, institution, _ = orcid_primary_employment(orcid_id, institution_lookup)
    institutions = [institution] if institution else []
    tags = orcid_keyword_labels(person, max_keywords=max_tags)
    works = orcid_selected_works(orcid_id, max_works=max_works)

    return {
        "name": orcid_name_to_full_name(person),
        "position": position,
        "institution": institution,
        "institutions": institutions,
        "tags": tags,
        "summary": orcid_biography(person),
        "image_url": "",
        "orcid": f"https://orcid.org/{orcid_id}",
        "website": (orcid_researcher_urls(person) or [""])[0],
        "selected_works": works,
        "profile_id": "",
    }


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


def merge_unique_strings(*groups: list[str], max_items: int | None = None) -> list[str]:
    merged = []
    seen = set()
    for group in groups:
        for item in group or []:
            text = (item or "").strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(text)
            if max_items is not None and len(merged) >= max_items:
                return merged
    return merged


def orcid_text_value(node) -> str:
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict):
        return (node.get("value") or "").strip()
    return ""


def orcid_name_to_full_name(person: dict) -> str:
    name = person.get("name") or {}
    given = orcid_text_value(name.get("given-names"))
    family = orcid_text_value(name.get("family-name"))
    return f"{given} {family}".strip()


def orcid_biography(person: dict) -> str:
    return orcid_text_value(person.get("biography"))


def orcid_keyword_labels(person: dict, max_keywords: int) -> list[str]:
    keywords = ((person.get("keywords") or {}).get("keyword") or [])
    labels = []
    for keyword in keywords:
        label = orcid_text_value(keyword.get("content"))
        if label:
            labels.append(label)
    return merge_unique_strings(labels, max_items=max_keywords)


def orcid_researcher_urls(person: dict) -> list[str]:
    researcher_urls = ((person.get("researcher-urls") or {}).get("researcher-url") or [])
    urls = []
    for item in researcher_urls:
        url = orcid_text_value(item.get("url"))
        if url:
            urls.append(url)
    return urls


def choose_orcid_work_url(summary: dict, group: dict) -> str:
    direct_url = orcid_text_value(summary.get("url"))
    if direct_url:
        return direct_url
    external_ids = ((group.get("external-ids") or {}).get("external-id") or [])
    for external_id in external_ids:
        external_url = orcid_text_value(external_id.get("external-id-url"))
        if external_url:
            return external_url
    return ""


def orcid_selected_works(orcid_id: str, max_works: int) -> list[dict[str, str]]:
    data = get_orcid_json(f"https://pub.orcid.org/v3.0/{orcid_id}/works")
    works = []
    seen = set()

    for group in data.get("group") or []:
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        summary = summaries[0]
        title = orcid_text_value(((summary.get("title") or {}).get("title") or {}))
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        year = orcid_text_value((summary.get("publication-date") or {}).get("year"))
        source = orcid_text_value(summary.get("journal-title")) or orcid_text_value(summary.get("type"))
        url = choose_orcid_work_url(summary, group)

        work = {"title": title}
        if year:
            work["year"] = year
        if source:
            work["source"] = source
        if url:
            work["url"] = url
        works.append(work)

    works.sort(key=work_sort_key, reverse=True)
    return works[:max_works]


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
        "selected_works",
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


def apply_field(data: dict, key: str, value, changed: bool) -> bool:
    if value in (None, "", [], {}):
        return changed
    if data.get(key) != value:
        data[key] = value
        return True
    return changed


def enrich_person(
    index_md: Path,
    root: Path,
    institution_lookup: dict[str, str],
    slug_to_institution_name: dict[str, str],
    org_cache: dict,
    max_tags: int,
    max_works: int,
    dry_run: bool,
    discover_nva: bool,
    discover_nva_loose: bool,
    download_images: bool,
):
    text = index_md.read_text(encoding="utf-8")
    front, body = split_frontmatter(text)
    data = yaml.safe_load(front) or {}

    if data.get("type") != "person":
        return False, "skip: not person"

    slug = (data.get("slug") or index_md.parent.name).strip()
    urls = data.get("urls") or {}
    if not isinstance(urls, dict):
        urls = {}

    nva_url = (urls.get("nva") or "").strip()
    orcid_url = (urls.get("orcid") or "").strip()
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
        elif not orcid_url:
            return False, reason

    if not nva_url and not orcid_url:
        return False, "skip: no urls.nva or urls.orcid"

    nva_bundle = {}
    profile_id = extract_profile_id(nva_url) if nva_url else None
    if profile_id:
        try:
            nva_bundle = fetch_nva_bundle(
                profile_id,
                institution_lookup=institution_lookup,
                org_cache=org_cache,
                max_tags=max_tags,
                max_works=max_works,
            )
            if nva_bundle.get("orcid"):
                orcid_url = nva_bundle["orcid"]
        except Exception as exc:
            if not orcid_url:
                return False, f"error: nva fetch failed: {exc}"

    orcid_bundle = {}
    orcid_id = extract_orcid_id(orcid_url)
    if orcid_url and not orcid_id:
        return False, "skip: unsupported orcid url"
    if orcid_id:
        try:
            orcid_bundle = fetch_orcid_bundle(
                orcid_id,
                institution_lookup=institution_lookup,
                max_tags=max_tags,
                max_works=max_works,
            )
        except Exception as exc:
            if not nva_bundle:
                return False, f"error: orcid fetch failed: {exc}"

    if not nva_bundle and not orcid_bundle:
        return False, "skip: no profile data"

    changed = False
    name = prefer(nva_bundle.get("name"), orcid_bundle.get("name"))
    if name:
        changed = apply_field(data, "name", name, changed) or changed
        changed = apply_field(data, "title", name, changed) or changed

    position = prefer(nva_bundle.get("position"), orcid_bundle.get("position"))
    changed = apply_field(data, "position", position, changed) or changed

    institution = prefer(nva_bundle.get("institution"), orcid_bundle.get("institution"))
    changed = apply_field(data, "institution", institution, changed) or changed

    merged_institutions = sorted(
        set((data.get("institutions") or []) + (nva_bundle.get("institutions") or []) + (orcid_bundle.get("institutions") or []))
    )
    if merged_institutions and data.get("institutions") != merged_institutions:
        data["institutions"] = merged_institutions
        changed = True

    tags = prefer(nva_bundle.get("tags"), orcid_bundle.get("tags")) or []
    if tags:
        changed = apply_field(data, "tags", tags, changed) or changed
        changed = apply_field(data, "search_keywords", tags, changed) or changed

    summary = prefer(nva_bundle.get("summary"), orcid_bundle.get("summary"))
    changed = apply_field(data, "summary", summary, changed) or changed

    selected_works = prefer(nva_bundle.get("selected_works"), orcid_bundle.get("selected_works")) or []
    if selected_works and data.get("selected_works") != selected_works:
        data["selected_works"] = selected_works
        changed = True

    website = prefer(nva_bundle.get("website"), orcid_bundle.get("website"))
    if website and not (urls.get("website") or "").strip():
        urls["website"] = website
        changed = True

    if profile_id:
        canonical_nva = f"https://nva.sikt.no/research-profile/{profile_id}"
        if urls.get("nva") != canonical_nva:
            urls["nva"] = canonical_nva
            changed = True

    if orcid_id:
        canonical_orcid = f"https://orcid.org/{orcid_id}"
        if urls.get("orcid") != canonical_orcid:
            urls["orcid"] = canonical_orcid
            changed = True

    image_url = prefer(nva_bundle.get("image_url"), orcid_bundle.get("image_url"))
    if download_images and image_url:
        portrait_name = portrait_filename(data.get("name") or slug, institution or (data.get("institution") or ""))
        portrait_path = root / PORTRAITS_CIRCLE_DIR / portrait_name
        if download_nva_portrait(image_url, portrait_path):
            image_ref = f"/{PORTRAITS_CIRCLE_DIR}/{portrait_name}"
            if data.get("image") != image_ref:
                data["image"] = image_ref
                changed = True

    data["urls"] = urls

    if not changed:
        return False, "unchanged"

    if dry_run:
        return True, "would update"

    ordered = ordered_person(data)
    dumped = yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False).strip()
    index_md.write_text(f"---\n{dumped}\n---\n\n{body.lstrip()}", encoding="utf-8")
    return True, "updated"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Enrich directory people from NVA and ORCID (NVA preferred, ORCID fallback). "
            "Updates affiliation, tags, bio, image, and recent publications."
        )
    )
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--slug", action="append", help="Only process specific person slug (repeatable)")
    parser.add_argument(
        "--max-tags",
        "--max-keywords",
        dest="max_tags",
        type=int,
        default=DEFAULT_MAX_TAGS,
        help="Maximum number of research tags/keywords to import",
    )
    parser.add_argument(
        "--max-works",
        type=int,
        default=DEFAULT_MAX_WORKS,
        help="Maximum number of publications to import (NVA preferred, ORCID fallback)",
    )
    parser.add_argument("--discover-nva", action="store_true", help="Auto-discover missing urls.nva from person name and institution")
    parser.add_argument("--discover-nva-loose", action="store_true", help="Allow a second-round looser name match for NVA discovery")
    parser.add_argument("--no-download-images", action="store_true", help="Skip downloading NVA profile pictures")
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
                root=root,
                institution_lookup=institution_lookup,
                slug_to_institution_name=slug_to_institution_name,
                org_cache=org_cache,
                max_tags=args.max_tags,
                max_works=args.max_works,
                dry_run=args.dry_run,
                discover_nva=args.discover_nva,
                discover_nva_loose=args.discover_nva_loose,
                download_images=not args.no_download_images,
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
