#!/usr/bin/env python3
import argparse
import json
import os
import re
from io import BytesIO
from itertools import product
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageDraw

from nva_result_types import nva_publication_source
from repo_paths import REPO_ROOT, SITE_ROOT


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


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

NVA_API_HOSTS = {
    "prod": "https://api.nva.unit.no",
    "test": "https://api.test.nva.aws.unit.no",
}
NVA_AUTH_HOSTS = {
    "prod": "nva-prod-ext.auth.eu-west-1.amazoncognito.com",
    "test": "nva-test-ext.auth.eu-west-1.amazoncognito.com",
}

_nva_request_headers: dict[str, str] = {}
NVA_CREDENTIALS_DIR = REPO_ROOT / "config"


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


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _token_similar(a: str, b: str) -> bool:
    if a == b:
        return True
    if not a or not b:
        return False
    if a.startswith(b) or b.startswith(a):
        return True
    if min(len(a), len(b)) >= 4 and _levenshtein(a, b) <= 1:
        return True
    return False


def names_match_for_discovery(target_norm: str, candidate_norm: str) -> bool:
    if target_norm == candidate_norm:
        return True
    target_first, target_last = first_last_tokens(target_norm)
    cand_first, cand_last = first_last_tokens(candidate_norm)
    if not target_first or not target_last or not cand_first or not cand_last:
        return False
    if not _token_similar(target_first, cand_first):
        return False
    return _token_similar(target_last, cand_last)


def _word_spelling_variants(word: str) -> set[str]:
    variants = {word}
    lower = word.lower()

    if len(word) >= 3 and lower.endswith("a"):
        variants.add(word[:-1] + ("Å" if word[-1].isupper() else "å"))

    if len(word) >= 4:
        for i, ch in enumerate(word):
            if ch.lower() == "a":
                variants.add(word[:i] + ("Å" if ch.isupper() else "å") + word[i + 1 :])

    if len(word) >= 4 and "o" in lower and "ø" not in lower:
        variants.add(word.replace("o", "ø").replace("O", "Ø"))

    if "oe" in lower:
        variants.add(re.sub("oe", "ø", word, flags=re.IGNORECASE))

    if "ae" in lower:
        variants.add(re.sub("ae", "æ", word, flags=re.IGNORECASE))

    if lower.endswith("segg") and not lower.endswith("tsegg"):
        variants.add(f"{word[:-4]}tsegg")

    return variants


def norwegian_name_search_variants(name: str) -> list[str]:
    name = re.sub(r"\s+", " ", name.strip())
    if not name:
        return []

    queries: list[str] = []

    def add(query: str):
        query = re.sub(r"\s+", " ", query.strip())
        if query and query not in queries:
            queries.append(query)

    parts = name.split()
    word_options = [_word_spelling_variants(part) for part in parts]

    add(name)
    if len(parts) >= 2:
        add(parts[-1])

    for opts in word_options:
        for alt in sorted(opts):
            add(alt)

    for i, opts in enumerate(word_options):
        for alt in sorted(opts):
            if alt == parts[i]:
                continue
            variant_parts = parts[:]
            variant_parts[i] = alt
            add(" ".join(variant_parts))

    if len(word_options) <= 3:
        for combo in product(*word_options):
            add(" ".join(combo))

    return queries


def fetch_nva_person_hits(name: str, max_results: int = 20) -> list[dict]:
    seen_ids: set[str] = set()
    hits: list[dict] = []
    for query in norwegian_name_search_variants(name):
        data = get_json(nva_api_url(f"/cristin/person?name={requests.utils.quote(query)}&results={max_results}"))
        for hit in data.get("hits") or []:
            hit_id = (hit.get("id") or "").strip()
            if hit_id and hit_id not in seen_ids:
                seen_ids.add(hit_id)
                hits.append(hit)
    return hits


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

    hits = fetch_nva_person_hits(name)
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
            if names_match_for_discovery(target_name, full_norm):
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
        elif _token_similar(cand_last, target_last):
            score += 0.9
        # Accept first-name prefix matches (sashi vs sashidharan)
        if cand_first == target_first:
            score += 1.0
        elif _token_similar(cand_first, target_first):
            score += 0.85
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


def nva_api_env() -> str:
    value = os.environ.get("NVA_API_ENV", "prod").strip().lower()
    return value if value in NVA_API_HOSTS else "prod"


def nva_api_base() -> str:
    return NVA_API_HOSTS[nva_api_env()]


def nva_api_url(path: str) -> str:
    if path.startswith("http"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{nva_api_base()}{path}"


def _nva_token_error_message(response: requests.Response, env: str) -> str:
    detail = ""
    try:
        payload = response.json()
        detail = (payload.get("error_description") or payload.get("error") or "").strip()
    except Exception:
        detail = (response.text or "").strip()[:300]
    hints = [
        f"HTTP {response.status_code} from {env} token endpoint.",
        "Check NVA_CLIENT_ID and NVA_CLIENT_SECRET (password = client secret).",
        f"If Sikt sent Test credentials, run: export NVA_API_ENV=test (currently: {env}).",
    ]
    if detail:
        hints.insert(1, detail)
    return " ".join(hints)


def request_nva_access_token(client_id: str, client_secret: str, env: str) -> str:
    auth_host = NVA_AUTH_HOSTS[env]
    token_url = f"https://{auth_host}/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    scope = os.environ.get("NVA_OAUTH_SCOPE", "").strip()

    attempts: list[tuple[str, dict, dict | None]] = [
        (
            "basic-auth",
            {"grant_type": "client_credentials", **({"scope": scope} if scope else {})},
            (client_id, client_secret),
        ),
        (
            "form-credentials",
            {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                **({"scope": scope} if scope else {}),
            },
            None,
        ),
    ]

    last_response: requests.Response | None = None
    for _label, data, auth in attempts:
        response = requests.post(
            token_url,
            data=data,
            headers=headers,
            auth=auth,
            timeout=30,
        )
        last_response = response
        if response.ok:
            return (response.json().get("access_token") or "").strip()

    assert last_response is not None
    raise requests.HTTPError(
        _nva_token_error_message(last_response, env),
        response=last_response,
    )


def nva_credentials_file() -> Path | None:
    override = os.environ.get("NVA_CREDENTIALS_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    path = NVA_CREDENTIALS_DIR / f"nva-credentials.{nva_api_env()}.json"
    if path.exists():
        return path
    legacy = NVA_CREDENTIALS_DIR / "nva-credentials.json"
    if legacy.exists():
        return legacy
    return None


def load_nva_credentials_from_config() -> tuple[str, str]:
    path = nva_credentials_file()
    if not path or not path.exists():
        return "", ""
    data = json.loads(path.read_text(encoding="utf-8"))
    return (str(data.get("clientId") or "").strip(), str(data.get("clientSecret") or "").strip())


def resolve_nva_access_token() -> str:
    static = os.environ.get("NVA_API_TOKEN", "").strip()
    if static:
        return static

    client_id = os.environ.get("NVA_CLIENT_ID", "").strip()
    client_secret = os.environ.get("NVA_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        client_id, client_secret = load_nva_credentials_from_config()
    if not client_id or not client_secret:
        return ""

    return request_nva_access_token(client_id, client_secret, nva_api_env())


def configure_nva_auth() -> str:
    _nva_request_headers.clear()
    token = resolve_nva_access_token()
    if token:
        _nva_request_headers["Authorization"] = f"Bearer {token}"
        _nva_request_headers["Accept"] = "application/json"
    return token


def get_json(url: str):
    r = requests.get(url, headers=_nva_request_headers, timeout=30)
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
    headers = dict(_nva_request_headers)
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
        nva_api_url("/search/resources"),
        params={"contributor": profile_id, "results": max(max_works * 3, 30)},
        headers=_nva_request_headers,
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
    profile = get_json(nva_api_url(f"/cristin/person/{profile_id}"))
    nva_affiliations = parse_nva_affiliations(profile, org_cache, institution_lookup)
    active = active_nva_affiliations(nva_affiliations)
    primary = pick_primary_nva_affiliation(active or nva_affiliations)

    institution_slugs = []
    for aff in active:
        for slug in aff.get("institutions") or []:
            if slug and slug not in institution_slugs:
                institution_slugs.append(slug)

    extra_active = [compact_nva_affiliation(aff) for aff in active]

    return {
        "name": names_to_full_name(profile.get("names") or []),
        "position": primary.get("role") or "",
        "department": primary.get("unit") or "",
        "institution": primary.get("institution") or "",
        "institutions": sorted(institution_slugs),
        "affiliation_units": [],
        "nva_affiliations": extra_active if len(extra_active) > 1 else [],
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
            org_slug = lookup_institution_slug(org_name, institution_lookup) if org_name else ""
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


def fetch_org_data(org_url: str, cache: dict) -> dict:
    if not org_url:
        return {}
    cached = cache.get(org_url)
    if isinstance(cached, dict):
        return cached
    try:
        data = get_json(org_url)
    except Exception:
        cache[org_url] = {}
        return {}
    cache[org_url] = data if isinstance(data, dict) else {}
    return cache[org_url]


def fetch_org_name(org_url: str, cache: dict) -> str:
    data = fetch_org_data(org_url, cache)
    labels = data.get("labels") or {}
    return labels.get("en") or labels.get("nb") or data.get("name") or ""


def iter_organization_nodes(org_data: dict):
    if not org_data:
        return
    yield org_data
    for parent in org_data.get("partOf") or []:
        if isinstance(parent, dict):
            yield from iter_organization_nodes(parent)


def institution_slug_from_org_node(org_data: dict, institution_lookup: dict[str, str]) -> str:
    labels = org_data.get("labels") or {}
    for key in ("en", "nb"):
        name = (labels.get(key) or "").strip()
        slug = lookup_institution_slug(name, institution_lookup)
        if slug:
            return slug

    acronym = (org_data.get("acronym") or "").strip().upper()
    acronym_to_name = {
        "UIO": "University of Oslo",
        "NTNU": "Norwegian University of Science and Technology",
        "UIB": "University of Bergen",
        "UIT": "Arctic University of Norway",
        "NMH": "Norwegian Academy of Music",
        "AHO": "Oslo School of Architecture and Design",
        "BI": "BI Norwegian Business School",
        "HVL": "Western Norway University of Applied Sciences",
        "HIOF": "Ostfold University College",
        "INN": "Inland Norway University of Applied Sciences",
        "KHIO": "Oslo National Academy of the Arts",
        "NORSUS": "NORSUS - Norwegian Institute for Sustainability Research",
    }
    canonical = acronym_to_name.get(acronym, "")
    if canonical:
        return lookup_institution_slug(canonical, institution_lookup)
    return ""


def resolve_institution_slug(org_url: str, org_cache: dict, institution_lookup: dict[str, str]) -> str:
    """Map NVA organization URL to a directory institution slug, walking parent orgs."""
    org_data = fetch_org_data(org_url, org_cache)
    for node in iter_organization_nodes(org_data):
        slug = institution_slug_from_org_node(node, institution_lookup)
        if slug:
            return slug
    return ""


def organization_unit_chain_top_down(org_data: dict) -> list[str]:
    """Organization path from top-level institution down to the affiliated unit."""
    nodes = list(iter_organization_nodes(org_data))
    names = []
    seen = set()
    for node in reversed(nodes):
        labels = node.get("labels") or {}
        name = (labels.get("en") or labels.get("nb") or "").strip()
        key = name.lower()
        if name and key not in seen:
            seen.add(key)
            names.append(name)
    return names


def institution_slugs_from_org(org_data: dict, institution_lookup: dict[str, str]) -> list[str]:
    slugs = []
    for node in iter_organization_nodes(org_data):
        slug = institution_slug_from_org_node(node, institution_lookup)
        if slug and slug not in slugs:
            slugs.append(slug)
    return slugs


def parse_nva_affiliation(
    affiliation: dict,
    org_cache: dict,
    institution_lookup: dict[str, str],
) -> dict:
    org_url = (affiliation.get("organization") or "").strip()
    org_data = fetch_org_data(org_url, org_cache)
    role_labels = ((affiliation.get("role") or {}).get("labels") or {})
    role = role_labels.get("en") or role_labels.get("nb") or ""
    units = organization_unit_chain_top_down(org_data)
    unit = units[-1] if units else fetch_org_name(org_url, org_cache)
    inst_slugs = institution_slugs_from_org(org_data, institution_lookup)

    return {
        "active": bool(affiliation.get("active")),
        "role": role,
        "unit": unit,
        "units": units,
        "institution": inst_slugs[0] if inst_slugs else "",
        "institutions": inst_slugs,
    }


def parse_nva_affiliations(
    profile: dict,
    org_cache: dict,
    institution_lookup: dict[str, str],
) -> list[dict]:
    return [
        parse_nva_affiliation(aff, org_cache, institution_lookup)
        for aff in profile.get("affiliations") or []
        if (aff.get("organization") or "").strip()
    ]


def pick_primary_nva_affiliation(affiliations: list[dict]) -> dict:
    for aff in affiliations:
        if aff.get("active"):
            return aff
    return affiliations[0] if affiliations else {}


def active_nva_affiliations(affiliations: list[dict]) -> list[dict]:
    return [aff for aff in affiliations if aff.get("active")]


def compact_nva_affiliation(aff: dict) -> dict:
    return {
        "role": aff.get("role") or "",
        "unit": aff.get("unit") or "",
        "institution": aff.get("institution") or "",
    }


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


def lookup_institution_slug(name: str, institution_lookup: dict[str, str]) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    slug = institution_lookup.get(slugify(name), "")
    if slug:
        return slug
    lower = name.lower()
    if lower.startswith("the "):
        slug = institution_lookup.get(slugify(name[4:]), "")
        if slug:
            return slug
    if "university of applied sciences" in lower:
        alt = re.sub(
            r"university of applied sciences",
            "University College",
            name,
            flags=re.IGNORECASE,
        )
        slug = institution_lookup.get(slugify(alt), "")
        if slug:
            return slug
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
                for alias in data.get("aliases") or []:
                    alias_name = (alias or "").strip()
                    if alias_name:
                        lookup[slugify(alias_name)] = slug
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
        "department",
        "image",
        "institution",
        "institutions",
        "affiliation_units",
        "nva_affiliations",
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


def apply_field(data: dict, key: str, value, changed: bool = False, *, allow_empty: bool = False) -> bool:
    if not allow_empty and value in (None, "", [], {}):
        return changed
    if data.get(key) != value:
        data[key] = value
        return True
    return changed


def synced_field_value(nva_bundle: dict, orcid_bundle: dict, key: str):
    """When NVA data was fetched, use NVA only; otherwise ORCID fallback."""
    if nva_bundle:
        return nva_bundle.get(key)
    return orcid_bundle.get(key)


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
    from_nva = bool(nva_bundle)
    allow_empty = from_nva

    position = synced_field_value(nva_bundle, orcid_bundle, "position")
    changed = apply_field(data, "position", position, changed, allow_empty=allow_empty) or changed

    department = synced_field_value(nva_bundle, orcid_bundle, "department")
    changed = apply_field(data, "department", department, changed, allow_empty=allow_empty) or changed

    nva_affiliations = synced_field_value(nva_bundle, orcid_bundle, "nva_affiliations") or []
    changed = apply_field(data, "nva_affiliations", nva_affiliations, changed, allow_empty=allow_empty) or changed

    institution = synced_field_value(nva_bundle, orcid_bundle, "institution") or ""
    if institution or not from_nva:
        changed = apply_field(data, "institution", institution, changed, allow_empty=allow_empty) or changed

    if from_nva:
        institutions = list(nva_bundle.get("institutions") or [])
        if institutions or not data.get("institutions"):
            changed = apply_field(data, "institutions", institutions, changed, allow_empty=allow_empty) or changed
    else:
        institutions = sorted(
            set((data.get("institutions") or []) + (orcid_bundle.get("institutions") or []))
        )
        changed = apply_field(data, "institutions", institutions, changed, allow_empty=allow_empty) or changed

    tags = synced_field_value(nva_bundle, orcid_bundle, "tags") or []
    changed = apply_field(data, "tags", tags, changed, allow_empty=allow_empty) or changed
    changed = apply_field(data, "search_keywords", tags, changed, allow_empty=allow_empty) or changed

    summary = synced_field_value(nva_bundle, orcid_bundle, "summary")
    changed = apply_field(data, "summary", summary or None, changed, allow_empty=allow_empty) or changed

    selected_works = synced_field_value(nva_bundle, orcid_bundle, "selected_works") or []
    changed = apply_field(data, "selected_works", selected_works, changed, allow_empty=allow_empty) or changed

    website = synced_field_value(nva_bundle, orcid_bundle, "website") or ""
    if from_nva:
        if urls.get("website") != website:
            urls["website"] = website
            changed = True
    elif website and urls.get("website") != website:
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

    image_url = synced_field_value(nva_bundle, orcid_bundle, "image_url") or ""
    if download_images and image_url:
        portrait_name = portrait_filename(data.get("name") or slug, institution or (data.get("institution") or ""))
        portrait_path = root / PORTRAITS_CIRCLE_DIR / portrait_name
        if download_nva_portrait(image_url, portrait_path):
            image_ref = f"/{PORTRAITS_CIRCLE_DIR}/{portrait_name}"
            if data.get("image") != image_ref:
                data["image"] = image_ref
                changed = True

    data["urls"] = urls

    for key in ("affiliation_units", "nva_affiliations"):
        if key in data and not data.get(key):
            data.pop(key, None)
            changed = True

    if not changed:
        return False, "unchanged"

    if dry_run:
        return True, "would update"

    ordered = ordered_person(data)
    dumped = yaml.dump(ordered, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper).strip()
    index_md.write_text(f"---\n{dumped}\n---\n\n{body.lstrip()}", encoding="utf-8")
    return True, "updated"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Enrich directory people from NVA and ORCID. "
            "When urls.nva is set, NVA overwrites affiliation, tags, bio, publications, and website "
            "(not name/title). ORCID is used only if NVA is missing."
        )
    )
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
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

    token = configure_nva_auth()
    if token:
        creds_file = nva_credentials_file()
        source = "config file" if creds_file and creds_file.exists() and not os.environ.get("NVA_CLIENT_ID") else "environment"
        print(f"NVA API: authenticated ({nva_api_env()}, {nva_api_base()}, {source})")
    else:
        creds_hint = NVA_CREDENTIALS_DIR / f"nva-credentials.{nva_api_env()}.json"
        print("NVA API: unauthenticated (public read only; profile pictures may be unavailable)")
        print(f"  Add credentials: {creds_hint} (see config/README.md)")

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
