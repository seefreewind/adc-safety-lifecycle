#!/usr/bin/env python3
"""Extract CT.gov adverseEventsModule group-level core safety summaries."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "clinicaltrials"
TRIAL_MASTER = ROOT / "data" / "processed" / "trial_master.csv"
OUT = ROOT / "data" / "interim" / "ctgov_core_safety_seed.csv"

HEADER = [
    "observation_id", "trial_id", "arm_id", "document_id", "source_type",
    "page_or_table_locator", "ae_original_term", "ae_standardized_term",
    "meddra_pt", "meddra_soc", "smq", "safety_concept", "grade_category",
    "seriousness", "causality", "number_events", "number_patients",
    "denominator", "percentage", "reporting_threshold", "analysis_population",
    "data_cutoff_date", "extractor", "review_status", "notes",
]


def trial_lookup() -> dict[str, str]:
    with TRIAL_MASTER.open(newline="", encoding="utf-8") as f:
        return {row["nct_number"]: row["trial_id"] for row in csv.DictReader(f) if row.get("nct_number")}


def add_row(rows, seq, trial_id, group_id, nct, term, concept, seriousness, affected, at_risk, threshold, time_frame, group_title):
    pct = ""
    try:
        if affected not in ("", None) and at_risk not in ("", None, "0", 0):
            pct = round(float(affected) / float(at_risk) * 100, 3)
    except Exception:
        pct = ""
    rows.append([
        f"CTCORE{seq:05d}", trial_id, f"{trial_id}_{group_id}", f"CTGOV_{nct}", "ClinicalTrials.gov",
        "adverseEventsModule.eventGroups", term, term, "", "", "", concept,
        "all grades", seriousness, "all-cause", "", affected, at_risk, pct, threshold,
        "ClinicalTrials.gov adverse event group summary", "", "script:build_ctgov_core_safety_seed.py",
        "needs_review", f"group_title={group_title}; timeFrame={time_frame}",
    ])


def main() -> None:
    trials = trial_lookup()
    rows = []
    seq = 1
    for path in sorted(RAW.glob("NCT*.json")):
        nct = path.stem
        trial_id = trials.get(nct, nct)
        data = json.loads(path.read_text(encoding="utf-8"))
        ae = ((data.get("resultsSection") or {}).get("adverseEventsModule") or {})
        if not ae:
            continue
        threshold = ae.get("frequencyThreshold", "")
        time_frame = ae.get("timeFrame", "")
        for group in ae.get("eventGroups") or []:
            group_id = group.get("id", "")
            title = group.get("title", "")
            add_row(rows, seq, trial_id, group_id, nct, "All-cause mortality",
                    "fatal_adverse_event", "fatal",
                    group.get("deathsNumAffected", ""), group.get("deathsNumAtRisk", ""),
                    threshold, time_frame, title)
            seq += 1
            add_row(rows, seq, trial_id, group_id, nct, "Participants affected by serious adverse events",
                    "serious_adverse_event", "serious",
                    group.get("seriousNumAffected", ""), group.get("seriousNumAtRisk", ""),
                    threshold, time_frame, title)
            seq += 1
            add_row(rows, seq, trial_id, group_id, nct, "Participants affected by other non-serious adverse events",
                    "non_serious_adverse_event", "other_non_serious",
                    group.get("otherNumAffected", ""), group.get("otherNumAtRisk", ""),
                    threshold, time_frame, title)
            seq += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} CT.gov core safety seed rows to {OUT}.")


if __name__ == "__main__":
    main()

