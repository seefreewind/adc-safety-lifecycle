#!/usr/bin/env python3
"""Fetch ClinicalTrials.gov v2 study JSON snapshots for trial_master rows."""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_MASTER = ROOT / "data" / "processed" / "trial_master.csv"
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"


def fetch_nct(nct_number: str) -> dict:
    url = "https://clinicaltrials.gov/api/v2/studies/" + urllib.parse.quote(nct_number)
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not TRIAL_MASTER.exists():
        raise FileNotFoundError(TRIAL_MASTER)

    with TRIAL_MASTER.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fetched = 0
    for row in rows:
        nct = (row.get("nct_number") or "").strip()
        if not nct or nct.lower() == "unknown":
            continue
        out = RAW_DIR / f"{nct}.json"
        if out.exists():
            continue
        data = fetch_nct(nct)
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        fetched += 1
        time.sleep(0.2)

    print(f"Fetched {fetched} ClinicalTrials.gov records.")


if __name__ == "__main__":
    main()

