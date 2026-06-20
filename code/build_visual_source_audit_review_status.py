#!/usr/bin/env python3
"""Record visual review status for matched source audit pages."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATCHED = ROOT / "tables" / "visual_source_audit_matched_pages.csv"
OUT = ROOT / "tables" / "visual_source_audit_review_status.csv"
REPORT_OUT = ROOT / "protocol" / "visual_source_audit_review_status_report.zh.md"

STATUS = {
    ("EXPUB_TRIAL014_0001", "Supplementary Table S7, page_or_unit 36"): (
        "visual_audit_pass",
        "Matched page shows Supplementary Table S7 with serious AE rows for both arms.",
    ),
    ("FDA_ADC006_MDR_761137_ORIG1", "Table 74, FDA review pp184-185"): (
        "visual_audit_pass_multpage_table",
        "Matched page shows continuation of Table 74; table spans adjacent FDA review pages and is supported by the text-layer confirmation.",
    ),
    ("FDA_ADC007_MDR_761139_ORIG1", "Table 35, FDA review p174"): (
        "visual_audit_pass",
        "Matched page shows Table 35 serious adverse events in the primary studies.",
    ),
    ("FDA_ADC007_MDR_761139_ORIG1", "Table 38, FDA review p177"): (
        "visual_audit_pass",
        "Matched page shows Table 38 adverse events associated with dose interruption.",
    ),
    ("FDA_ADC007_MDR_761139_ORIG1", "Table 41, FDA review p183"): (
        "visual_audit_pass",
        "Matched page shows Table 41 most frequent TEAEs and related FDA text.",
    ),
    ("FDA_ADC008_MDR_761115_ORIG1", "FDA review text p87"): (
        "visual_audit_pass",
        "Matched page contains the FDA reviewer text on permanent discontinuation due to TEAEs.",
    ),
    ("FDA_ADC009_MDR_761158_ORIG1", "Table 27, FDA review p148"): (
        "visual_audit_pass",
        "Matched page shows FDA Table 27 with DREAMM-2 TEAE overview values.",
    ),
    ("PUB_DESTINY_APP", "Supplementary Table S3, appendix p11"): (
        "visual_audit_pass",
        "Matched page shows Supplementary Table S3 with overall safety rows for the RP2D cohort.",
    ),
    ("PUB_DREAMM_MAIN", "main article p6"): (
        "visual_audit_pass",
        "Matched page shows DREAMM-2 publication narrative with any AE, dose delay, dose reduction, and discontinuation values.",
    ),
    ("PUB_DREAMM_MAIN", "main article p7 and appendix Table S1 p10"): (
        "visual_audit_pass_summary_text",
        "Matched page shows publication summary text with serious AE values; detailed supplementary table remains available for final audit if needed.",
    ),
    ("PUB_DREAMM_MAIN", "main article p7-8"): (
        "visual_audit_pass_summary_text",
        "Matched page shows publication summary text with fatal serious AE values.",
    ),
    ("PUB_EV201_MAIN", "Table A3, PDF p17"): (
        "visual_audit_pass",
        "Matched page shows EV-201 Table A3 with treatment-related AE values.",
    ),
    ("PUB_EV201_MAIN", "Table A4, PDF p17"): (
        "visual_audit_pass",
        "Matched page shows EV-201 Table A4 with all-cause AE values.",
    ),
    ("PUB_EV201_MAIN", "main text p7"): (
        "visual_audit_pass",
        "Matched page shows EV-201 narrative text on treatment-related death outside the safety reporting period.",
    ),
    ("PUB_IMMU_APP", "Supplementary Table S1, appendix p18"): (
        "visual_audit_pass",
        "Matched page shows Supplementary Table S1 with discontinuation reasons in the efficacy population.",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows = []
    for row in read_csv(MATCHED):
        key = (row["document_id"], row["locator"])
        status, note = STATUS.get(key, ("visual_audit_pending", "No visual review status recorded."))
        out = dict(row)
        out["visual_audit_status"] = status
        out["visual_audit_note"] = note
        rows.append(out)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_status = Counter(row["visual_audit_status"] for row in rows)
    REPORT_OUT.write_text(
        "\n".join([
            "# Visual source audit review status 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/visual_source_audit_review_status.csv`",
            "",
            "## 视觉审计状态",
            "",
            *[f"- {status}: {count}" for status, count in sorted(by_status.items())],
            "",
            "## 说明",
            "",
            "该审计基于自动匹配渲染页和人工视觉抽查。`visual_audit_pass_summary_text` 表示页面中可见摘要或正文数值；如最终提交需更严格表格级审计，可补充渲染对应 supplementary table。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
