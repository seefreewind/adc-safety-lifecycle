#!/usr/bin/env python3
"""Fetch ClinicalTrials.gov v2 JSON snapshots for expansion candidate trials."""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIALS = ROOT / "data" / "processed" / "trial_master_expansion_candidates.csv"
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"
MANIFEST = ROOT / "data" / "interim" / "ctgov_expansion_fetch_manifest.csv"


def fetch_nct(nct_number: str) -> dict:
    url = "https://clinicaltrials.gov/api/v2/studies/" + urllib.parse.quote(nct_number)
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(TRIALS.open(newline="", encoding="utf-8")))
    manifest_rows = []

    for row in rows:
        nct = (row.get("nct_number") or "").strip()
        trial_id = row.get("trial_id", "")
        if not nct or nct.lower() == "unknown":
            manifest_rows.append([trial_id, nct, "", "skipped", "missing nct_number"])
            continue
        out = RAW_DIR / f"{nct}.json"
        if out.exists():
            manifest_rows.append([trial_id, nct, str(out), "already_present", ""])
            continue
        try:
            data = fetch_nct(nct)
            out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest_rows.append([trial_id, nct, str(out), "downloaded", ""])
            time.sleep(0.2)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            manifest_rows.append([trial_id, nct, "", "failed", str(exc)])

    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["trial_id", "nct_number", "local_file", "fetch_status", "notes"])
        writer.writerows(manifest_rows)

    status_counts = {}
    for item in manifest_rows:
        status_counts[item[3]] = status_counts.get(item[3], 0) + 1
    print(f"Wrote CT.gov expansion fetch manifest: {MANIFEST.relative_to(ROOT)}")
    print(status_counts)


if __name__ == "__main__":
    main()
