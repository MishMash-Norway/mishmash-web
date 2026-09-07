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

Two safety rules, both covered by `test_nva_enrich_person.py`: a failed NVA
fetch **skips the person** rather than falling back to ORCID (which would
overwrite NVA fields and flip back the next day), and an expired access
token (they live 15 minutes; a full run takes longer) is refreshed and the
request retried instead of failing.

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

Adding people: how the scripts fit together
--------------------------------------------

Several scripts write to `site/_directory/people/*/index.md`, and the nightly
workflow (`.github/workflows/enrich-directory-people.yml`) pushes to `main`
every morning. Before adding people, know who owns which field:

| Field(s) | Written by | Rule |
| --- | --- | --- |
| `name`, `title`, `slug`, `permalink` | you / the XLSX importer | Never changed by any sync. |
| `urls.*` | XLSX importer, `fill_missing_nva_orcid.py`, `discover_orcid_public_search.py` | `orcid`/`nva` on an existing entry are never replaced by a different value. |
| `wps` | XLSX importer, `assign_wps_from_mailing_lists.py` | Always merged (union), never removed. |
| `roles` | you | Never touched by the importers or the sync. |
| `position`, `department`, `institution`, `institutions`, `tags`, `search_keywords`, `summary`, `selected_works`, `image` | `enrich_directory_from_nva.py` when `urls.nva` is set | **NVA wins nightly.** Hand edits to these fields survive only for people without `urls.nva`, or when NVA has no value for the field. The XLSX importer only fills them when empty. |
| `institutions` ↔ institution `people` | `sync_directory_reciprocity.py` | Set the link on one side; the sync mirrors it (nightly, or run it yourself). |
| tag spelling | `merge_tags.py` | Title-cases tags and folds variants from `config/tag_merge_map.yml` nightly. |

Practical consequences:

- **Commit and push promptly, and pull before you push.** The nightly bot
  commits to `main` at 05:00 UTC; a stale local branch conflicts on the very
  files you edited.
- **`institution` must be a slug** from `site/_directory/institutions/`
  (`validate_directory.py` fails otherwise). Create the institution entry
  first — copy `institutions/_template/` — and list the spellings people use
  for it in its `aliases`, so the importer can resolve them.
- **Do not fight NVA.** If a person has `urls.nva` and NVA reports a
  different affiliation or tag list, fix it in NVA (or ask the person to),
  not in the file.
- **Run `python3 scripts/validate_directory.py`** before committing;
  the Web Quality Checks workflow runs the same script.

Import people from XLSX
-----------------------

`import_people_from_xlsx.py` (shared logic in `import_people_xlsx_common.py`,
tests in `test_import_people_xlsx.py`) reads the exports of the two
MishMash forms and auto-detects which one it has:

- **Participation form** (columns `Do you want to be added to the MishMash
  directory?`, `Institution/Organisation`, `Unit`, `Current position`, the
  `Work Package(s) you are interested in joining.WP…` columns and two keyword
  columns). Only rows answering **Yes** to the directory question are
  imported; rows without an answer (the question was added in June 2026) or
  answering No are skipped. The `Which WP(s) does it connect to?` columns
  describe project ideas and are ignored.
- **Directory update form** (columns `Work package(s).WP1`…`WP7`, `Tags`,
  URL columns). Every row is applied.

What it writes:

- New people are created from `people/_template/index.md` with
  `published: false`, name, URLs, work packages, position, department, tags
  (max 12, from the keyword columns) and — when the institution name resolves
  — `institution`/`institutions`. Review the entry, then set
  `published: true`.
- Existing people (matched by slug, or by `aliases` on the entry) get URLs
  filled in, `wps` merged, and empty `position`/`department`/`institution`/
  `tags` filled. Curated values, `roles`, the body text and fields the
  importer does not know about are left alone.
- Institution names are matched exactly (case- and accent-insensitive)
  against the `name`, `short_name`, `slug` and `aliases` of the institution
  entries. Unresolved names are printed as warnings and the field is left
  empty: create the institution or add an alias, then re-run — re-running is
  safe.
- A duplicated ORCID/NVA value submitted by two different people is applied
  to neither (copy-paste mistakes are common in cumulative exports).

```bash
python3 scripts/import_people_from_xlsx.py --xlsx temp/data-…xlsx --dry-run
python3 scripts/import_people_from_xlsx.py --xlsx temp/data-…xlsx
python3 scripts/sync_directory_reciprocity.py   # mirror people ↔ institutions
python3 scripts/validate_directory.py
```

Flags: `--xlsx` (defaults to the newest `.xlsx` in `temp/`), `--dry-run`,
`--template`, `--out-base`. `import_people_from_xlsx_all.py` is a
compatibility wrapper with the same behaviour.

The people roles from the participation form (Full / Associate / Affiliate
member) are *not* imported; every new entry gets `roles: [Member]`, which is
the label the people network filters on. Adjust by hand if needed.

### `import_directory_survey_csv.py` (legacy — do not use for imports)

An older importer for the same participation form. It is kept only because
`assign_wps_from_mailing_lists.py` imports two helpers from it. Do not run
it against the live directory: it ignores the directory-consent column,
rewrites `roles` from the survey answer (dropping `Work Package Leader`,
`Council Member`, …), copies free-text survey comments into the public bio,
drops front-matter fields it does not know about, and creates institutions
from a hard-coded list. Use `import_people_from_xlsx.py` instead.

Import MeshUps from XLSX
------------------------

Preview MeshUp event changes from the schedule spreadsheet:

```bash
python3 scripts/import_meshups_from_xlsx.py --xlsx "temp/MishMash Meetups.xlsx"
```

Write the event updates only after reviewing the preview:

```bash
python3 scripts/import_meshups_from_xlsx.py --xlsx "temp/MishMash Meetups.xlsx" --write
```

By default, the importer only updates events dated today or later. Use
`--include-past` only when intentionally refreshing archived MeshUps.

To add a speaker portrait and assign it to an event, add a repeatable
`--portrait NUMBER=PATH` option:

```bash
python3 scripts/import_meshups_from_xlsx.py --write --portrait 23=temp/Vinoo_Alluri.jpeg
```

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
