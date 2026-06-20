#!/usr/bin/env python3
"""Build expansion CT.gov source, arm, and core safety seed tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "clinicaltrials"
TRIALS = ROOT / "data" / "processed" / "trial_master_expansion_candidates.csv"
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "tables"


CORE_HEADER = [
    "observation_id", "trial_id", "arm_id", "document_id", "source_type",
    "page_or_table_locator", "ae_original_term", "ae_standardized_term",
    "meddra_pt", "meddra_soc", "smq", "safety_concept", "grade_category",
    "seriousness", "causality", "number_events", "number_patients",
    "denominator", "percentage", "reporting_threshold", "analysis_population",
    "data_cutoff_date", "extractor", "review_status", "notes",
]


def read_trials() -> dict[str, dict[str, str]]:
    with TRIALS.open(newline="", encoding="utf-8") as f:
        return {row["nct_number"]: row for row in csv.DictReader(f) if row.get("nct_number")}


def pct(affected: str, at_risk: str) -> str:
    try:
        if affected not in ("", None) and at_risk not in ("", None, "0", 0):
            return f"{float(affected) / float(at_risk) * 100:.3f}"
    except Exception:
        return ""
    return ""


def add_core_row(rows, seq, trial_id, group_id, nct, term, concept, seriousness, affected, at_risk, threshold, time_frame, group_title):
    rows.append([
        f"CTEXP{seq:06d}", trial_id, f"{trial_id}_{group_id}", f"CTGOV_{nct}", "ClinicalTrials.gov",
        "adverseEventsModule.eventGroups", term, term, "", "", "", concept,
        "all grades", seriousness, "all-cause", "", affected, at_risk, pct(affected, at_risk), threshold,
        "ClinicalTrials.gov adverse event group summary", "", "script:build_ctgov_expansion_metadata.py",
        "needs_review", f"group_title={group_title}; timeFrame={time_frame}",
    ])


def main() -> None:
    trials = read_trials()
    source_rows = []
    arm_rows = []
    core_rows = []
    availability_rows = []
    seq = 1

    for nct, trial in sorted(trials.items(), key=lambda item: item[1]["trial_id"]):
        path = RAW_DIR / f"{nct}.json"
        if not path.exists():
            availability_rows.append([trial["trial_id"], nct, trial["acronym"], "missing_json", 0, 0, 0, ""])
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        protocol = data.get("protocolSection") or {}
        status = protocol.get("statusModule") or {}
        ident = protocol.get("identificationModule") or {}
        results = data.get("resultsSection") or {}
        ae = results.get("adverseEventsModule") or {}
        groups = ae.get("eventGroups") or []
        source_rows.append([
            f"CTGOV_{nct}", trial["trial_id"], trial.get("approval_id", ""), trial.get("drug_id", ""),
            "ClinicalTrials.gov", ident.get("briefTitle", ""), status.get("resultsFirstSubmitDate", ""),
            "", str(path), "ClinicalTrials.gov adverse events module" if ae else "",
            "api_v2_snapshot", "parsed" if ae else "no_results_module", "", "",
            "Downloaded via ClinicalTrials.gov API v2 expansion workflow.",
        ])
        for group in groups:
            group_id = group.get("id", "")
            arm_id = f"{trial['trial_id']}_{group_id}" if group_id else trial["trial_id"]
            arm_rows.append([
                arm_id, trial["trial_id"], group.get("title", ""), group.get("description", ""),
                "", "", "", group.get("seriousNumAtRisk") or group.get("otherNumAtRisk") or "",
                f"ClinicalTrials.gov group from {nct}; expansion candidate arm mapping requires manual verification.",
            ])
            threshold = ae.get("frequencyThreshold", "")
            time_frame = ae.get("timeFrame", "")
            title = group.get("title", "")
            for term, concept, seriousness, affected, at_risk in [
                ("All-cause mortality", "fatal_adverse_event", "fatal", group.get("deathsNumAffected", ""), group.get("deathsNumAtRisk", "")),
                ("Participants affected by serious adverse events", "serious_adverse_event", "serious", group.get("seriousNumAffected", ""), group.get("seriousNumAtRisk", "")),
                ("Participants affected by other non-serious adverse events", "non_serious_adverse_event", "other_non_serious", group.get("otherNumAffected", ""), group.get("otherNumAtRisk", "")),
            ]:
                add_core_row(core_rows, seq, trial["trial_id"], group_id, nct, term, concept, seriousness, affected, at_risk, threshold, time_frame, title)
                seq += 1
        availability_rows.append([
            trial["trial_id"], nct, trial["acronym"], "has_ae_module" if ae else "no_ae_module",
            len(groups), len(ae.get("seriousEvents") or []), len(ae.get("otherEvents") or []), ae.get("timeFrame", ""),
        ])

    with (INTERIM / "ctgov_source_document_expansion.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "document_id", "trial_id", "approval_id", "drug_id", "source_type", "document_title",
            "document_date", "data_cutoff_date", "url_or_local_path", "analysis_population",
            "version", "extraction_status", "reviewer_1", "reviewer_2", "notes",
        ])
        writer.writerows(source_rows)

    with (INTERIM / "ctgov_arm_dictionary_expansion.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "arm_id", "trial_id", "arm_name", "regimen", "dose", "schedule",
            "monotherapy_or_combination", "safety_population", "notes",
        ])
        writer.writerows(arm_rows)

    with (INTERIM / "ctgov_core_safety_expansion_seed.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CORE_HEADER)
        writer.writerows(core_rows)

    with (TABLES / "ctgov_expansion_availability.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["trial_id", "nct_number", "acronym", "ctgov_ae_status", "event_group_count", "serious_event_term_count", "other_event_term_count", "ae_time_frame"])
        writer.writerows(availability_rows)

    print(f"Wrote {len(source_rows)} CT.gov expansion source rows.")
    print(f"Wrote {len(arm_rows)} CT.gov expansion arm rows.")
    print(f"Wrote {len(core_rows)} CT.gov expansion core rows.")
    print(f"Wrote {len(availability_rows)} CT.gov expansion availability rows.")


if __name__ == "__main__":
    main()
