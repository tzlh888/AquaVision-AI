#!/usr/bin/env python3
"""One-shot authoritative identity queries for the frozen Phase 3A-3 pool."""

from __future__ import annotations

import hashlib
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import certifi


ROOT = Path(__file__).resolve().parents[2]
PHASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PHASE_DIR / "phase3a3_config.json"
RAW_DIR = ROOT / "data" / "raw" / "phase3a3" / "usgs"
OUTPUT_PATH = RAW_DIR / "frozen_candidate_identity_queries.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def query_candidate(
    service_url: str, candidate: dict[str, Any], timeout_seconds: int = 30
) -> dict[str, Any]:
    lon = float(candidate["longitude"])
    lat = float(candidate["latitude"])
    delta = 0.6
    params = {
        "where": f"GNIS_NAME='{candidate['name'].replace("'", "''")}'",
        "geometry": f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": (
            "OBJECTID,PERMANENT_IDENTIFIER,GNIS_ID,GNIS_NAME,AREASQKM,"
            "FTYPE,FCODE,NHDPLUSID,VPUID"
        ),
        "returnGeometry": "true",
        "outSR": "5070",
        "f": "geojson",
    }
    url = f"{service_url}/query?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AquaVision-Phase3A3-metadata-audit/1.0"},
    )
    result: dict[str, Any] = {
        "candidate": candidate,
        "query_url": url,
        "requested_at_utc": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": timeout_seconds,
    }
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
            context=ssl.create_default_context(cafile=certifi.where()),
        ) as response:
            payload = response.read()
            result.update(
                {
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "response_bytes": len(payload),
                    "response_sha256": sha256_bytes(payload),
                    "payload": json.loads(payload),
                }
            )
    except urllib.error.HTTPError as exc:
        result.update({"http_status": exc.code, "error_type": "HTTPError"})
    except urllib.error.URLError as exc:
        result.update(
            {
                "http_status": None,
                "error_type": "URLError",
                "error_reason": type(exc.reason).__name__,
            }
        )
    except TimeoutError:
        result.update({"http_status": None, "error_type": "TimeoutError"})
    return result


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    pool = config["candidate_pool"]
    candidates = pool["fallback_candidates"]
    maximum = int(pool["fallback_identity_queries_max"])
    if len(candidates) > maximum:
        raise ValueError("Frozen candidate count exceeds request limit")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results = [query_candidate(pool["service_url"], candidate) for candidate in candidates]
    document = {
        "schema_version": "phase3a3-usgs-candidate-queries-v1",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": pool["source"],
        "service_url": pool["service_url"],
        "request_count": len(results),
        "results": results,
    }
    OUTPUT_PATH.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    successes = sum(result.get("http_status") == 200 for result in results)
    features = sum(
        len(result.get("payload", {}).get("features", [])) for result in results
    )
    print(
        json.dumps(
            {
                "requests": len(results),
                "http_200": successes,
                "features": features,
                "output": str(OUTPUT_PATH),
                "output_sha256": sha256_bytes(OUTPUT_PATH.read_bytes()),
            },
            sort_keys=True,
        )
    )
    return 0 if successes else 2


if __name__ == "__main__":
    sys.exit(main())
