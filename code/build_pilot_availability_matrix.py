#!/usr/bin/env python3
"""Build a pilot source-availability matrix for workflow tracking."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_CT = ROOT / "data" / "raw" / "clinicaltrials"
RAW_FDA = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"
OUT = ROOT / "tables" / "pilot_source_availability.csv"


def main() -> None:
    trials = list(csv.DictReader((PROCESSED / "trial_master.csv").open(newline="", encoding="utf-8")))
    pub_refs = list(csv.DictReader((PROCESSED / "publication_reference_inventory.csv").open(newline="", encoding="utf-8")))
    primary_by_trial = {
        r["trial_id"]: r for r in pub_refs if r.get("is_primary_publication_candidate") == "yes"
    }

    rows = []
    for trial in trials:
        nct = trial["nct_number"]
        ct_file = RAW_CT / f"{nct}.json"
        has_ct = ct_file.exists()
        has_ct_results = False
        has_ct_ae = False
        if has_ct:
            data = json.loads(ct_file.read_text(encoding="utf-8"))
            results = data.get("resultsSection") or {}
            has_ct_results = bool(results)
            has_ct_ae = bool(results.get("adverseEventsModule"))

        fda_files = list(RAW_FDA.glob(f"{trial['drug_id']}/*.pdf"))
        rows.append([
            trial["trial_id"], trial["drug_id"], trial["acronym"], nct,
            "yes" if has_ct else "no",
            "yes" if has_ct_results else "no",
            "yes" if has_ct_ae else "no",
            len(fda_files),
            "yes" if trial["trial_id"] in primary_by_trial else "no",
            primary_by_trial.get(trial["trial_id"], {}).get("doi", ""),
            "needs_manual_extraction" if not has_ct_ae or len(fda_files) == 0 else "ready_for_locator_review",
        ])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "trial_id", "drug_id", "trial_acronym", "nct_number", "ctgov_snapshot",
            "ctgov_results_module", "ctgov_adverse_events_module", "downloaded_fda_pdf_count",
            "primary_publication_candidate", "primary_publication_doi", "next_status",
        ])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} pilot availability rows.")


if __name__ == "__main__":
    main()

