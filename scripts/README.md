Fetch UIO / Ritmo event pages
=================================

This script fetches event pages (e.g. from the UIO / Ritmo site) and extracts basic metadata.

Quick start:

1. Install deps (recommended in a venv):

```bash
pip install -r scripts/requirements.txt
```

1. Run against a single page:

```bash
python3 scripts/fetch_uio_events.py "https://www.uio.no/.../deichman/index.html"
```

Paths default to `site/` (see `scripts/repo_paths.py`). To write elsewhere:

```bash
python3 scripts/fetch_uio_events.py "https://www.uio.no/.../deichman/index.html" --out-dir site/_events
```

1. Or provide a file with one URL per line:

```bash
python3 scripts/fetch_uio_events.py urls.txt --from-file --out-dir scripts/output
```

The script emits either JSON to stdout (`--json`) or writes Jekyll-style markdown files with front-matter into `--out-dir`.

Fetch AI-focused partner events
-------------------------------

This script scans partner links listed in `site/index.md`, discovers likely event pages,
extracts event candidates, filters for AI-focused events, and appends new items to
`site/_data/partner_events.yml`.

Quick start:

1. Install deps (same as above):

```bash
pip install -r scripts/requirements.txt
```

1. Preview what would be added:

```bash
python3 scripts/fetch_partner_ai_events.py --dry-run
```

1. Append new events to partner listing:

```bash
python3 scripts/fetch_partner_ai_events.py
```

Useful flags:

- `--max-pages-per-partner 4` limits crawl depth per partner site.
- `--max-partners 40` limits total partners scanned.
- `--output site/_data/partner_events.yml` writes to a custom destination file.

Update directory people from NVA and ORCID
------------------------------------------

This script refreshes `site/_directory/people/*/index.md` from [NVA](https://nva.sikt.no/) and [ORCID](https://orcid.org/). When a person has `urls.nva`, **NVA overwrites** synced fields: affiliation (`institution`, `institutions` from **active** affiliations only, `department` for the primary unit), tags, bio, publications, institutional website, and portrait. ORCID fills `personal_website` when NVA is missing. Inactive NVA affiliations are ignored. `name` and `title` are never changed.

Updated fields:

- Affiliation (`position`, `institution`, `institutions`)
- Tags (`tags` and `search_keywords`, from research topics)
- Bio (`summary`)
- Portrait (`image`, downloaded from NVA when available)
- Recent publications (`selected_works`, up to 10 — newest eligible works after filtering lectures, media, and supervisor-only entries)

A GitHub Actions workflow runs this once per day (`.github/workflows/enrich-directory-people.yml`), including a sync of MishMash project results to `site/_data/mishmash_results.yml` for `/results/`.

### NVA API access (UiO / MishMash)

Request credentials from Sikt using the [NVA API access form](https://sikt.no/tjenester/nasjonalt-vitenarkiv-nva/hjelpeside-nva/teknisk-dokumentasjon-nva) (customer institution, contact person, purpose, Test/Prod). Sikt returns a **client ID** and **client secret** for OAuth2 client credentials ([authentication docs](https://github.com/BIBSYSDEV/nva-api-documentation/blob/main/scenarios/authenticating/index.md)).

Suggested form values for MishMash:

| Field | Value |
| --- | --- |
| Kundeinstitusjon | UiO |
| Kontaktperson | Alexander Refsum Jensenius |
| E-post | a.r.jensenius@imv.uio.no |
| Bruksområde | MishMash-nettsider (directory people profiles) |
| Tilgang | **Prod** for the live site; **Test** optional for local experiments |

After you receive credentials from Sikt (JSON files with `clientId` and `clientSecret`):

1. **Local config folder** (recommended, gitignored):

```bash
cp /path/to/uio-web-credentials\ 1.json config/nva-credentials.prod.json
cp /path/to/uio-web-credentials.json config/nva-credentials.test.json
```

See `config/README.md`. The SMS password is not the OAuth client secret.

2. **Or environment variables** (never commit):

```bash
export NVA_API_ENV=prod
export NVA_CLIENT_ID='…'
export NVA_CLIENT_SECRET='…'
```

3. **Verify**:

```bash
pip install -r scripts/requirements.txt
python3 scripts/test_nva_api_auth.py
```

4. **GitHub Actions** — in the MishMash repo go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
| --- | --- |
| `NVA_CLIENT_ID` | client ID from Sikt |
| `NVA_CLIENT_SECRET` | client secret from Sikt |

The workflow sets `NVA_API_ENV=prod` automatically. Tokens expire after 15 minutes; the script fetches a fresh token on each run.

API hosts ([nva-api-documentation](https://github.com/BIBSYSDEV/nva-api-documentation)): production `https://api.nva.unit.no`, test `https://api.test.nva.aws.unit.no`. Swagger UI: [swagger-ui.nva.unit.no](https://swagger-ui.nva.unit.no/#/).

```bash
pip install -r scripts/requirements.txt
python3 scripts/enrich_directory_from_nva.py --discover-nva --discover-nva-loose --max-works 10
python3 scripts/sync_results_from_nva.py
```

Useful flags:

- `--slug <slug>` process one person (repeatable)
- `--dry-run` report changes without writing files
- `--no-download-images` skip portrait downloads

Fill Missing NVA and ORCID Links Only
-------------------------------------

This script only updates missing `urls.nva` and `urls.orcid` in
`site/_directory/people/*/index.md`, without changing other profile fields.

Quick start:

```bash
python3 scripts/fill_missing_nva_orcid.py --dry-run
python3 scripts/fill_missing_nva_orcid.py --discover-nva-loose
```

Useful flags:

- `--slug <slug>` process one person (repeatable)
- `--discover-nva-loose` allow looser name matching
- `--dry-run` report changes without writing files

Discover ORCID via public ORCID search
---------------------------------------

`scripts/fill_missing_nva_orcid.py` only finds an ORCID iD when it is already
linked from an NVA profile. This complementary script queries the public
ORCID registry directly (no credentials required) for people still missing
`urls.orcid`, and only fills it in when a candidate's ORCID employment
history overlaps with the person's known institution or department. Run
`fill_missing_nva_orcid.py` first, then use this script for the remainder.

```bash
python3 scripts/discover_orcid_public_search.py --dry-run
python3 scripts/discover_orcid_public_search.py
```

Ambiguous candidates (multiple institution-matched hits) and unverified
candidates (a single hit with no institution data to confirm) are printed for
manual review rather than applied automatically.

Useful flags:

- `--slug <slug>` process one person (repeatable)
- `--dry-run` report changes without writing files

Assign Work Packages from sympa mailing list dumps
---------------------------------------------------

MishMash's WP1-WP7 mailing lists are the closest thing to a source of truth
for who is affiliated with which work package. Export each list from sympa
as `wp{N}@mishmash.no.txt` (one `email<TAB>Name` per line) into a folder
(`temp/` is gitignored and the default), then run:

```bash
python3 scripts/assign_wps_from_mailing_lists.py --dumps-dir temp --dry-run
python3 scripts/assign_wps_from_mailing_lists.py --dumps-dir temp
```

This adds the matching `WPN` tag to each matched person's `wps` front matter
list (merged, no duplicates). Entries that cannot be matched by name, slug,
or email local-part are printed as unmatched so they can be followed up
manually (e.g. contacted to fill in the directory survey) or checked by hand
against the directory (misspellings, non-ASCII names, or nickname/legal-name
mismatches are common causes of missed matches).

Import people from XLSX
-----------------------

The XLSX importer now auto-detects the sheet type:

- intake sheets with an include column only import rows that are marked for inclusion
- existing-member sheets update matching people entries with URL data

Use the canonical XLSX importer for MishMash directory entries:

```bash
python3 scripts/import_people_from_xlsx.py
```

If you still have the older entrypoint name, it is kept as a compatibility wrapper:

```bash
python3 scripts/import_people_from_xlsx_all.py
```

Useful flags on the canonical importer:

- `--xlsx path/to/file.xlsx` selects a different spreadsheet.
- `--template path/to/index.md` uses a different directory template.
- `--out-base path/to/output` writes entries to another people directory.

Combine image slices
--------------------

This script reads two images and creates one combined image where:

- the left side comes from the first image
- the right side comes from the second image

Quick start:

```bash
python3 scripts/combine_image_slices.py first.png second.png combined.png
```

Optional flags:

- `--left-ratio 0.5` keeps 50% of the first image width from the left edge.
- `--right-ratio 0.5` keeps 50% of the second image width from the right edge.

Example:

```bash
python3 scripts/combine_image_slices.py first.jpg second.jpg output.jpg --left-ratio 0.4 --right-ratio 0.6
```

Merge similar tags
------------------

Tags appear in directory profiles, events, and `search_keywords`, and roles appear in
directory profiles (`roles`). `merge_tags.py` normalizes both mapping and capitalization,
including role labels used by the site filters:

- Merge configured variants into canonical values from `config/tag_merge_map.yml`.
- Normalize capitalization to title case (for example `machine learning` -> `Machine Learning`,
  `work package leader` -> `Work Package Leader`) while keeping connector words such as
  `and`, `of`, and `to` lowercase when they are in the middle.
- Normalize role labels such as `Board member`, `Council member`, `Work package leader`, and `Member`.

Quick start:

```bash
python3 scripts/merge_tags.py --report
python3 scripts/merge_tags.py --dry-run
python3 scripts/merge_tags.py
```

Useful flags:

- `--suggest` with `--report` prints YAML for unmapped duplicate groups.
- `--map path/to/tag_merge_map.yml` uses a custom mapping file.
- `--tag-groups site/_data/tag_groups.yml` also updates people-network tag groups.

Tag clustering
--------------

The `/search/` and `/people/network/` pages support two cluster sources:

- `source: runtime` in [site/_data/tag_clustering.yml](site/_data/tag_clustering.yml) uses the current in-browser clustering.
- `source: offline` loads precomputed groups from [site/assets/data/tag-clusters.json](site/assets/data/tag-clusters.json).

When offline mode is enabled, the UI still uses the same slider and tag-group controls, but only cluster counts that actually exist in `tag-clusters.json` are selectable.

Quick toggle example:

```yaml
# site/_data/tag_clustering.yml
source: offline
offline_clusters_path: /assets/data/tag-clusters.json
```

Use `source: runtime` to fall back to browser-side clustering without changing the page UI.

Wikidata identifiers and facts
------------------------------

`sync_wikidata.py` connects directory entries to Wikidata (first step of the
linked-data roadmap in the wiki's Web Philosophy page):

- People with an ORCID iD are matched exactly via Wikidata's ORCID property
  (P496); ORCIDs matching several Wikidata items (duplicates) are skipped
  with a warning for manual resolution.
- Institutions are matched exactly via their English Wikipedia article.
- Matches are written as `urls.wikidata` on the entries; existing values are
  never overwritten.
- Basic facts for resolved institutions (coordinates, logo, official
  website, inception) are written to `site/_data/wikidata_institutions.yml`
  as generated reference data.

```bash
python3 scripts/sync_wikidata.py --dry-run
python3 scripts/sync_wikidata.py
python3 scripts/sync_wikidata.py --skip-facts   # only resolve QIDs
```

The directory validator warns about malformed `urls.wikidata` values.
