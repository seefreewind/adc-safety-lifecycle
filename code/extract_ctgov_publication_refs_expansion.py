#!/usr/bin/env python3
"""Extract CT.gov publication references for expansion candidate trials."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"
TRIALS = ROOT / "data" / "processed" / "trial_master_expansion_candidates.csv"
OUT = ROOT / "data" / "processed" / "publication_reference_inventory_expansion.csv"
TABLE_OUT = ROOT / "tables" / "publication_reference_expansion_summary.csv"


def trial_lookup() -> dict[str, dict[str, str]]:
    with TRIALS.open(newline="", encoding="utf-8") as f:
        return {row["nct_number"]: row for row in csv.DictReader(f) if row.get("nct_number")}


def extract_doi(citation: str) -> str:
    match = re.search(r"doi:\s*([^\s]+)", citation, flags=re.IGNORECASE)
    if match:
        return match.group(1).rstrip(".")
    match = re.search(r"(10\.\d{4,9}/[^\s]+)", citation)
    if match:
        return match.group(1).rstrip(".")
    return ""


def likely_primary(ref_type: str, citation: str, acronym: str) -> str:
    text = citation.lower()
    if ref_type.upper() == "RESULT" and acronym and acronym.lower().replace("-", "") in text.replace("-", ""):
        return "yes_candidate"
    if ref_type.upper() == "RESULT" and any(token in text for token in ["phase 2", "phase ii", "phase 3", "phase iii", "pivotal", "randomized", "randomised"]):
        return "possible"
    return ""


def main() -> None:
    trials = trial_lookup()
    rows = []
    summary = []
    seq = 1
    for nct, trial in sorted(trials.items(), key=lambda item: item[1]["trial_id"]):
        path = RAW_DIR / f"{nct}.json"
        if not path.exists():
            summary.append([trial["trial_id"], nct, trial["acronym"], 0, 0, "missing_json"])
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        refs = ((data.get("protocolSection") or {}).get("referencesModule") or {}).get("references") or []
        result_count = 0
        primary_candidates = 0
        for ref in refs:
            citation = ref.get("citation", "")
            ref_type = ref.get("type", "")
            primary = likely_primary(ref_type, citation, trial["acronym"])
            if ref_type.upper() == "RESULT":
                result_count += 1
            if primary:
                primary_candidates += 1
            rows.append([
                f"EXPPUBREF{seq:05d}", trial["trial_id"], trial["drug_id"], trial["approval_id"],
                nct, trial["acronym"], ref_type, ref.get("pmid", ""), extract_doi(citation),
                citation, primary, "", "needs_triage",
            ])
            seq += 1
        summary.append([trial["trial_id"], nct, trial["acronym"], len(refs), result_count, primary_candidates])

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "publication_ref_id", "trial_id", "drug_id", "approval_id", "nct_number",
            "acronym", "reference_type", "pmid", "doi", "citation",
            "is_primary_publication_candidate", "local_pdf", "review_status",
        ])
        writer.writerows(rows)

    with TABLE_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["trial_id", "nct_number", "acronym", "reference_count", "result_reference_count", "primary_candidate_count_or_status"])
        writer.writerows(summary)

    print(f"Wrote {len(rows)} expansion publication references.")
    print(f"Wrote {len(summary)} expansion publication summary rows.")


if __name__ == "__main__":
    main()
