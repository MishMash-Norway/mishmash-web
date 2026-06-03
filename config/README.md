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
2. `config/nva-credentials.{prod|test}.json` (based on `NVA_API_ENV`, default `prod`)
3. Override path with `NVA_CREDENTIALS_FILE=/path/to/file.json`

GitHub Actions still uses repository secrets (`NVA_CLIENT_ID`, `NVA_CLIENT_SECRET`), not these files.
