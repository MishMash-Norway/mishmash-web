#!/usr/bin/env python3
"""Download a Nettskjema form's Excel report through the Nettskjema API v3.

The file is byte-for-byte the same report you get from "Download as Excel"
in the Nettskjema UI, so it drops straight into the existing importers:

    python3 scripts/fetch_nettskjema_export.py                    # participation form → temp/
    python3 scripts/fetch_nettskjema_export.py --form update      # directory update form
    python3 scripts/fetch_nettskjema_export.py --form 625226      # any form id
    python3 scripts/fetch_nettskjema_export.py --import           # then run the people import (dry run)
    python3 scripts/fetch_nettskjema_export.py --import --write   # ... and write the profiles

Credentials (OAuth 2.1 client credentials, see config/README.md):

1. NETTSKJEMA_ACCESS_TOKEN, an access token you already have (valid 24 h), or
2. environment variables NETTSKJEMA_CLIENT_ID and NETTSKJEMA_CLIENT_SECRET, or
3. config/nettskjema-credentials.json  ({"clientId": "...", "clientSecret": "..."}), or
4. NETTSKJEMA_CREDENTIALS_FILE=/path/to/file.json.

The client's username, <clientId>@apiclient, must be given editing
permission on each form (Settings → Permissions → Editing permissions).
Nettskjema clients expire after 365 days.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
TEMP_DIR = ROOT / "temp"
TOKEN_URL = "https://authorization.nettskjema.no/oauth2/token"
API_BASE = "https://nettskjema.no/api/v3"

FORMS = {
    "participation": 625226,   # MishMash participation form (new people, consent question)
    "update": 635360,          # directory update form (existing members)
}


def load_credentials() -> tuple[str, str]:
    client_id = os.environ.get("NETTSKJEMA_CLIENT_ID", "").strip()
    client_secret = os.environ.get("NETTSKJEMA_CLIENT_SECRET", "").strip()
    if client_id and client_secret:
        return client_id, client_secret
    override = os.environ.get("NETTSKJEMA_CREDENTIALS_FILE", "").strip()
    path = Path(override) if override else CONFIG_DIR / "nettskjema-credentials.json"
    if not path.exists():
        sys.exit(
            "No Nettskjema credentials. Set NETTSKJEMA_ACCESS_TOKEN, or NETTSKJEMA_CLIENT_ID and NETTSKJEMA_CLIENT_SECRET, "
            f"or create {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} "
            "(see config/README.md)."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    client_id = str(data.get("clientId") or data.get("client_id") or "").strip()
    client_secret = str(data.get("clientSecret") or data.get("client_secret") or "").strip()
    if not client_id or not client_secret:
        sys.exit(f"{path}: expected clientId and clientSecret")
    return client_id, client_secret


def get_token(client_id: str, client_secret: str) -> str:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = request.Request(
        TOKEN_URL,
        data=parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:300]
        sys.exit(f"Token request failed ({exc.code}): {body}\nCheck the client id/secret and that the client has not expired.")
    token = payload.get("access_token")
    if not token:
        sys.exit(f"Token response had no access_token: {payload}")
    return token


def api_get(token: str, path: str, accept: str = "application/json") -> bytes:
    req = request.Request(f"{API_BASE}{path}", headers={"Authorization": f"Bearer {token}", "Accept": accept})
    try:
        with request.urlopen(req, timeout=120) as resp:
            return resp.read()
    except error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:300]
        hint = ""
        if exc.code in (401, 403):
            hint = "\nGive <clientId>@apiclient editing permission on the form (Settings → Permissions)."
        sys.exit(f"GET {path} failed ({exc.code}): {body}{hint}")


def resolve_form(value: str) -> int:
    if value in FORMS:
        return FORMS[value]
    if value.isdigit():
        return int(value)
    sys.exit(f"Unknown form '{value}'. Use one of {', '.join(FORMS)} or a numeric form id.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--form", default="participation", help="participation (default), update, or a numeric form id")
    parser.add_argument("--out", type=Path, help="Where to save the xlsx (default: temp/data-<form>-<timestamp>.xlsx)")
    parser.add_argument("--import", dest="run_import", action="store_true", help="Run scripts/import_people_from_xlsx.py on the file afterwards")
    parser.add_argument("--write", action="store_true", help="With --import: write the profiles instead of a dry run")
    args = parser.parse_args()

    form_id = resolve_form(args.form)
    token = os.environ.get("NETTSKJEMA_ACCESS_TOKEN", "").strip()
    if not token:
        client_id, client_secret = load_credentials()
        token = get_token(client_id, client_secret)

    info = json.loads(api_get(token, f"/form/{form_id}/info"))
    title = info.get("title") or info.get("formTitle") or str(form_id)
    data = api_get(token, f"/form/{form_id}/excel-report", accept="application/octet-stream")
    if not data.startswith(b"PK"):
        sys.exit(f"The report for form {form_id} does not look like an xlsx ({len(data)} bytes).")

    out = args.out or TEMP_DIR / f"data-{form_id}-{datetime.now():%Y-%m-%d-%H%M}.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"Saved '{title}' (form {form_id}): {out} ({len(data):,} bytes)")

    if args.run_import:
        cmd = [sys.executable, str(ROOT / "scripts/import_people_from_xlsx.py"), "--xlsx", str(out)]
        if not args.write:
            cmd.append("--dry-run")
        print("Running:", " ".join(cmd))
        return subprocess.call(cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
