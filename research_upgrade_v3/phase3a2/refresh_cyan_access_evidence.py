"""Refresh only the bounded NASA CyAN access-status evidence in the manifest."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "V3_DATA_PROVENANCE_MANIFEST.json"


def main() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    session = requests.Session()
    session.headers.update({"User-Agent": "AquaVision-Phase3A2-MetadataPilot/1.0"})
    updated = 0
    for evidence in payload["source_evidence"]:
        if evidence.get("source_type") != "NASA_CYAN_DAILY_LISTING_AND_BOUNDED_ACCESS":
            continue
        response = session.head(
            evidence["file_url"], timeout=30, allow_redirects=False
        )
        if response.status_code not in (301, 302, 303, 307, 308):
            raise RuntimeError(
                f"Expected authentication redirect, received HTTP {response.status_code}"
            )
        location = response.headers.get("location", "")
        if "/getfile/urs/" not in location:
            raise RuntimeError("CyAN redirect did not point to the Earthdata login flow")
        evidence["bounded_access_method"] = "HEAD"
        evidence["bounded_access_status_code"] = response.status_code
        evidence["bounded_access_location"] = location
        evidence["raster_bytes_retrieved"] = False
        evidence["access_disposition"] = "EARTHDATA_AUTHENTICATION_REQUIRED"
        updated += 1
    if updated != payload["candidate_rows"]:
        raise RuntimeError("Did not refresh every pilot candidate")
    payload["cyan_access_evidence_refreshed_at_utc"] = (
        datetime.now().astimezone().isoformat()
    )
    MANIFEST.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"updated_cyan_access_records": updated}, indent=2))


if __name__ == "__main__":
    main()
