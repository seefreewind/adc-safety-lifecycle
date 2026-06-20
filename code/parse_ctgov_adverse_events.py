#!/usr/bin/env python3
"""Parse ClinicalTrials.gov adverseEventsModule into ae_observation rows."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"
TRIAL_MASTER = ROOT / "data" / "processed" / "trial_master.csv"
OUT = ROOT / "data" / "interim" / "ctgov_ae_observation.csv"


HEADER = [
    "observation_id", "trial_id", "arm_id", "document_id", "source_type", "page_or_table_locator",
    "ae_original_term", "ae_standardized_term", "meddra_pt", "meddra_soc", "smq",
    "safety_concept", "grade_category", "seriousness", "causality", "number_events",
    "number_patients", "denominator", "percentage", "reporting_threshold",
    "analysis_population", "data_cutoff_date", "extractor", "review_status", "notes",
]


def trial_lookup() -> dict[str, dict[str, str]]:
    with TRIAL_MASTER.open(newline="", encoding="utf-8") as f:
        return {row["nct_number"]: row for row in csv.DictReader(f) if row.get("nct_number")}


def event_rows(module: dict, key: str, seriousness: str) -> list[dict]:
    return module.get(key) or []


def group_denominators(module: dict) -> dict[str, str]:
    denoms = {}
    for group in module.get("eventGroups", []) or []:
        group_id = group.get("id") or ""
        denoms[group_id] = group.get("seriousNumAffected") or group.get("otherNumAffected") or ""
    return denoms


def main() -> None:
    trials = trial_lookup()
    rows = []
    seq = 1
    for path in sorted(RAW_DIR.glob("NCT*.json")):
        nct = path.stem
        trial = trials.get(nct, {})
        trial_id = trial.get("trial_id", nct)
        data = json.loads(path.read_text(encoding="utf-8"))
        results = data.get("resultsSection") or {}
        ae_module = results.get("adverseEventsModule") or {}
        if not ae_module:
            continue

        denoms = group_denominators(ae_module)
        for key, seriousness in [
            ("seriousEvents", "serious"),
            ("otherEvents", "other_non_serious"),
        ]:
            for event in event_rows(ae_module, key, seriousness):
                term = event.get("term", "")
                organ_system = event.get("organSystem", "")
                for stat in event.get("stats", []) or []:
                    group_id = stat.get("groupId", "")
                    arm_id = f"{trial_id}_{group_id}" if group_id else trial_id
                    affected = stat.get("numAffected", "")
                    at_risk = stat.get("numAtRisk", "") or denoms.get(group_id, "")
                    percentage = ""
                    try:
                        if affected != "" and at_risk not in ("", "0", 0):
                            percentage = float(affected) / float(at_risk) * 100
                    except Exception:
                        percentage = ""
                    rows.append([
                        f"CTAE{seq:07d}", trial_id, arm_id, f"CTGOV_{nct}", "ClinicalTrials.gov",
                        "adverseEventsModule", term, "", term, organ_system, "", "",
                        "all grades", seriousness, "all-cause", "", affected, at_risk, percentage,
                        ae_module.get("frequencyThreshold", ""), "ClinicalTrials.gov reported AE population",
                        "", "script:parse_ctgov_adverse_events.py", "needs_review",
                        f"Parsed from {nct} {key}; group labels require Arm_Dictionary mapping.",
                    ])
                    seq += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} CT.gov AE observation rows to {OUT}.")


if __name__ == "__main__":
    main()
