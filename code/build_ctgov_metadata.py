#!/usr/bin/env python3
"""Build source_document and Arm_Dictionary seeds from CT.gov JSON snapshots."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"
PROCESSED = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"


def read_csv_dict(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return {row[key]: row for row in csv.DictReader(f) if row.get(key)}


def main() -> None:
    trials = read_csv_dict(PROCESSED / "trial_master.csv", "nct_number")
    source_rows = []
    arm_rows = []

    for path in sorted(RAW_DIR.glob("NCT*.json")):
        nct = path.stem
        trial = trials.get(nct, {})
        trial_id = trial.get("trial_id", nct)
        drug_id = trial.get("drug_id", "")
        approval_id = trial.get("approval_id", "")
        data = json.loads(path.read_text(encoding="utf-8"))
        protocol = data.get("protocolSection") or {}
        status = protocol.get("statusModule") or {}
        title = (protocol.get("identificationModule") or {}).get("briefTitle", "")
        results = data.get("resultsSection") or {}
        ae_module = results.get("adverseEventsModule") or {}

        source_rows.append([
            f"CTGOV_{nct}", trial_id, approval_id, drug_id, "ClinicalTrials.gov", title,
            status.get("resultsFirstSubmitDate", ""), "", str(path),
            "ClinicalTrials.gov adverse events module" if ae_module else "",
            "api_v2_snapshot", "parsed" if ae_module else "no_results_module",
            "", "", "Downloaded via ClinicalTrials.gov API v2.",
        ])

        for group in ae_module.get("eventGroups", []) or []:
            group_id = group.get("id", "")
            arm_id = f"{trial_id}_{group_id}" if group_id else trial_id
            arm_rows.append([
                arm_id, trial_id, group.get("title", ""), group.get("description", ""),
                "", "", "", group.get("seriousNumAffected") or group.get("otherNumAffected") or "",
                f"ClinicalTrials.gov group from {nct}; map to manuscript arm_id before primary analysis.",
            ])

    with (INTERIM / "ctgov_source_document_seed.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "document_id", "trial_id", "approval_id", "drug_id", "source_type", "document_title",
            "document_date", "data_cutoff_date", "url_or_local_path", "analysis_population",
            "version", "extraction_status", "reviewer_1", "reviewer_2", "notes",
        ])
        writer.writerows(source_rows)

    with (INTERIM / "ctgov_arm_dictionary_seed.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "arm_id", "trial_id", "arm_name", "regimen", "dose", "schedule",
            "monotherapy_or_combination", "safety_population", "notes",
        ])
        writer.writerows(arm_rows)

    print(f"Wrote {len(source_rows)} source rows and {len(arm_rows)} arm rows.")


if __name__ == "__main__":
    main()
