#!/usr/bin/env python3
"""Fetch EPSG:5070 geometry for the three pre-existing, verified pilot identities."""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "phase3a3" / "usgs" / "existing_pilot_geometries.json"
SERVICE = "https://hydro.nationalmap.gov/arcgis/rest/services/NHDPlus_HR/MapServer/9/query"
PILOTS = [
    {"candidate_id": "okeechobee", "name": "Lake Okeechobee", "object_id": 1787881},
    {"candidate_id": "utah_lake", "name": "Utah Lake", "object_id": 5333680},
    {"candidate_id": "upper_klamath", "name": "Upper Klamath Lake", "object_id": 5169146},
]


def main() -> None:
    results = []
    context = ssl.create_default_context(cafile=certifi.where())
    for pilot in PILOTS:
        params = {
            "objectIds": str(pilot["object_id"]),
            "outFields": (
                "OBJECTID,PERMANENT_IDENTIFIER,GNIS_ID,GNIS_NAME,AREASQKM,"
                "FTYPE,FCODE,NHDPLUSID,VPUID"
            ),
            "returnGeometry": "true",
            "outSR": "5070",
            "maxAllowableOffset": "30",
            "geometryPrecision": "2",
            "f": "geojson",
        }
        url = SERVICE + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url, headers={"User-Agent": "AquaVision-Phase3A3-existing-pilot-audit/1.0"}
        )
        record = {
            "candidate": pilot,
            "query_url": url,
            "requested_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with urllib.request.urlopen(request, timeout=30, context=context) as response:
                payload = response.read()
                record.update(
                    {
                        "http_status": response.status,
                        "response_bytes": len(payload),
                        "response_sha256": hashlib.sha256(payload).hexdigest(),
                        "payload": json.loads(payload),
                    }
                )
        except Exception as exc:  # fail-closed, sanitized diagnostic only
            record.update(
                {
                    "http_status": getattr(exc, "code", None),
                    "error_type": type(exc).__name__,
                }
            )
        results.append(record)
    document = {
        "schema_version": "phase3a3-existing-pilot-geometries-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "requests": len(results),
                "http_200": sum(record.get("http_status") == 200 for record in results),
                "features": sum(
                    len(record.get("payload", {}).get("features", [])) for record in results
                ),
                "output_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
