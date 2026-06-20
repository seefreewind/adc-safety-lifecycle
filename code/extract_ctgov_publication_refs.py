#!/usr/bin/env python3
"""Extract publication references from CT.gov snapshots into a locator table."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"
TRIAL_MASTER = ROOT / "data" / "processed" / "trial_master.csv"
OUT = ROOT / "data" / "processed" / "publication_reference_inventory.csv"


def trial_lookup() -> dict[str, dict[str, str]]:
    with TRIAL_MASTER.open(newline="", encoding="utf-8") as f:
        return {row["nct_number"]: row for row in csv.DictReader(f) if row.get("nct_number")}


def extract_doi(citation: str) -> str:
    match = re.search(r"doi:\s*([^\s]+)", citation, flags=re.IGNORECASE)
    if match:
        return match.group(1).rstrip(".")
    match = re.search(r"(10\.\d{4,9}/[^\s]+)", citation)
    if match:
        return match.group(1).rstrip(".")
    return ""


def main() -> None:
    trials = trial_lookup()
    rows = []
    seq = 1
    for path in sorted(RAW_DIR.glob("NCT*.json")):
        nct = path.stem
        trial = trials.get(nct, {})
        data = json.loads(path.read_text(encoding="utf-8"))
        refs = ((data.get("protocolSection") or {}).get("referencesModule") or {}).get("references") or []
        for ref in refs:
            citation = ref.get("citation", "")
            rows.append([
                f"PUBREF{seq:05d}", trial.get("trial_id", nct), trial.get("drug_id", ""),
                nct, ref.get("type", ""), ref.get("pmid", ""), extract_doi(citation),
                citation, "", "", "needs_triage",
            ])
            seq += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "publication_ref_id", "trial_id", "drug_id", "nct_number", "reference_type",
            "pmid", "doi", "citation", "is_primary_publication_candidate",
            "supplement_url_or_file", "review_status",
        ])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} publication references.")


if __name__ == "__main__":
    main()

