#!/usr/bin/env python3
"""Verify NVA API credentials (OAuth client credentials or static bearer token)."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from enrich_directory_from_nva import (  # noqa: E402
    configure_nva_auth,
    get_json,
    nva_api_base,
    nva_api_env,
    nva_api_url,
)


def main() -> int:
    try:
        token = configure_nva_auth()
    except Exception as exc:
        print(f"NVA token request failed: {exc}")
        print("Tips:")
        print("  - NVA_CLIENT_ID = client ID from Sikt (not your UiO username)")
        print("  - NVA_CLIENT_SECRET = password from Sikt")
        print("  - If credentials are for Test: export NVA_API_ENV=test")
        print("  - Optional scope from Sikt: export NVA_OAUTH_SCOPE='resource/scope'")
        return 1

    if not token:
        print("No NVA credentials found.")
        print("Set NVA_CLIENT_ID + NVA_CLIENT_SECRET, or place config/nva-credentials.prod.json")
        print("Optional: NVA_API_ENV=prod|test (default: prod), NVA_CREDENTIALS_FILE")
        return 1

    env = nva_api_env()
    base = nva_api_base()
    print(f"OK: obtained access token for {env} ({base})")

    # Public-style read that should work with or without auth.
    search = get_json(nva_api_url("/cristin/person?name=Jensenius&results=1"))
    hits = search.get("hits") or []
    print(f"OK: person search returned {len(hits)} hit(s)")

    if not hits:
        return 0

    person_id = None
    for ident in hits[0].get("identifiers") or []:
        if ident.get("type") == "CristinIdentifier":
            person_id = ident.get("value")
            break
    if not person_id:
        print("Skip: portrait test (no Cristin id in first hit)")
        return 0

    profile = get_json(nva_api_url(f"/cristin/person/{person_id}"))
    image_url = (profile.get("image") or "").strip()
    if not image_url:
        print("Note: profile has no image URL in NVA")
        return 0

    import requests

    response = requests.get(
        image_url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    if response.status_code == 200 and not (response.headers.get("Content-Type") or "").startswith(
        "application/json"
    ):
        print(f"OK: profile picture endpoint reachable ({len(response.content)} bytes)")
        return 0

    print(f"Portrait endpoint returned HTTP {response.status_code}")
    print("If this fails, confirm Prod/Test credentials match NVA_API_ENV.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
