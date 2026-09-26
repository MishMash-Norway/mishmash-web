# Local configuration

Secrets and machine-specific settings live here. **Credential files are gitignored** — never commit them.

## NVA API (Sikt)

Copy the JSON files from Sikt FileSender into this folder:

| File | Environment |
| --- | --- |
| `nva-credentials.prod.json` | Production (`api.nva.unit.no`) — MishMash site |
| `nva-credentials.test.json` | Test (`api.test.nva.aws.unit.no`) |

Use `nva-credentials.example.json` as a template. The SMS password from Sikt is **not** the OAuth `clientSecret`; use the values from the JSON files.

Scripts pick credentials in this order:

1. Environment variables `NVA_CLIENT_ID` and `NVA_CLIENT_SECRET`
2. The file named by `NVA_CREDENTIALS_FILE`
3. `config/nva-credentials.{prod|test}.json` (based on `NVA_API_ENV`, default `prod`)
4. `config/nva-credentials.json`, a fallback without an environment suffix

The client these files describe holds the publication-read scope only: the scripts can read NVA but not write to it, so `scripts/nva_project_managers.py` can only show what it would change.

GitHub Actions uses repository secrets (`NVA_CLIENT_ID`, `NVA_CLIENT_SECRET`), not these files.

## Nettskjema API (participation and directory forms)

`scripts/fetch_nettskjema_export.py` downloads a form's Excel report through
the Nettskjema API v3, so nobody has to export it by hand. It needs an API
client:

1. Log in at <https://authorization.nettskjema.no> (FEIDE) and click
   **Register client**. Note the `clientId` and the `clientSecret` (shown once);
   clients expire after 365 days.
2. In each form, under **Settings → Permissions → Editing permissions**, add
   the user `<clientId>@apiclient`. The forms are 625226 (participation) and
   635360 (directory update).
3. Save the values as `config/nettskjema-credentials.json`
   (`{"clientId": "...", "clientSecret": "..."}`), gitignored, or set
   `NETTSKJEMA_CLIENT_ID` and `NETTSKJEMA_CLIENT_SECRET`.
   `NETTSKJEMA_CREDENTIALS_FILE` overrides the path. An access token you
   already hold can be used directly as `NETTSKJEMA_ACCESS_TOKEN` (valid 24 h).

## Tag merge map

`tag_merge_map.yml` defines canonical values and variants to merge across the site
for front-matter fields such as `tags`, `search_keywords`, and `roles`.
Running `scripts/merge_tags.py` also normalizes capitalization (title case with connector
word exceptions like `and`, `of`, `to`).
Use `python3 scripts/merge_tags.py --report` to audit tags and
`python3 scripts/merge_tags.py --dry-run` before applying changes.
