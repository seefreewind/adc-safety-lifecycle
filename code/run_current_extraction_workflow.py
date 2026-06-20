#!/usr/bin/env python3
"""Run the current extraction/comparability workflow in dependency order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = [
    "build_fda_core_safety_expansion_seed.py",
    "build_combined_fda_core_safety_seed.py",
    "build_full_cohort_source_comparability_matrix.py",
    "build_full_cohort_source_comparability_matrix_detail.py",
    "build_primary_analysis_pair_candidates.py",
    "build_source_comparability_adjudication_queue.py",
    "build_p1_adjudication_recommendations.py",
    "build_p3_p4_adjudication_recommendations.py",
    "build_analysis_ready_comparison_set.py",
    "build_analysis_ready_comparison_summary_stats.py",
    "build_analysis_ready_source_confirmation_packet.py",
    "build_analysis_ready_source_auto_confirmation.py",
    "build_analysis_ready_pair_confirmation_status.py",
    "build_confirmed_analysis_ready_comparison_set.py",
    "build_full_cohort_analysis_readiness_summary.py",
    "build_manuscript_ready_summary_tables.py",
    "build_noncomparability_rationale_summary.py",
    "build_visual_audit_sample_pages.py",
    "build_visual_audit_matched_source_pages.py",
    "build_visual_source_audit_review_status.py",
    "build_final_analysis_audit_index.py",
    "build_manuscript_audit_tables.py",
    "build_confirmed_concordance_results.py",
    "build_english_manuscript_summary_tables.py",
    "extract_ctgov_full_module_safety_candidates.py",
    "build_ctgov_full_module_candidate_triage.py",
    "build_ctgov_full_module_manual_review_packet.py",
    "build_three_layer_analysis_tables.py",
    "build_robust_comparability_sensitivity.py",
    "build_source_flow_status.py",
    "build_manual_adjudication_packets.py",
    "build_manuscript_figures_tables.py",
    "build_pubmed_reference_lookup.py",
    "build_source_citation_inventory.py",
    "build_primary_trial_reference_list.py",
    "build_background_reference_list.py",
    "build_confirmed_source_appendix.py",
    "build_current_manuscript_draft.py",
    "build_preliminary_manuscript.py",
    "build_preliminary_manuscript_docx.py",
    "build_manuscript_quality_audit.py",
    "quality_control.py",
]


def main() -> None:
    for script in SCRIPTS:
        path = ROOT / "src" / script
        print(f"Running {path.relative_to(ROOT)}")
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)
    print("Current extraction/comparability workflow completed.")


if __name__ == "__main__":
    main()
