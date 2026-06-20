#!/usr/bin/env python3
"""Build a source appendix for documents used in confirmed comparisons."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def unique_join(values: list[str]) -> str:
    out: list[str] = []
    for value in values:
        value = (value or "").strip()
        if value and value not in out:
            out.append(value)
    return "; ".join(out)


def source_url(row: dict[str, str]) -> str:
    fda_public_urls = {
        "FDA_ADC006_MDR_761137_ORIG1": "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2019/761137Orig1s000MultidisciplineR.pdf",
        "FDA_ADC007_MDR_761139_ORIG1": "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2019/761139Orig1s000MultidisciplineR.pdf",
        "FDA_ADC008_MDR_761115_ORIG1": "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2020/761115Orig1s000MultidisciplineR.pdf",
        "FDA_ADC009_MDR_761158_ORIG1": "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2020/761158Orig1s000MultidisciplineR.pdf",
    }
    if row["document_id"] in fda_public_urls:
        return fda_public_urls[row["document_id"]]
    if row["source"] == "ClinicalTrials.gov":
        document_id = row["document_id"]
        if document_id.startswith("CTGOV_"):
            nct = document_id.replace("CTGOV_", "")
            return f"https://clinicaltrials.gov/study/{nct}"
    if row["source"] == "publication":
        return row.get("local_path", "")
    if row["source"] == "FDA review":
        return row.get("local_path", "")
    return row.get("local_path", "")


def main() -> None:
    confirmations = read_rows(TABLES / "analysis_ready_source_auto_confirmation.csv")

    grouped: dict[tuple[str, str, str], dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for row in confirmations:
        key = (row["source"], row["document_id"], row.get("local_path", ""))
        grouped[key]["trial_id"].append(row["trial_id"])
        grouped[key]["analysis_tier"].append(row["analysis_tier"])
        grouped[key]["comparison_id"].append(row["comparison_id"])
        grouped[key]["locator"].append(row["locator"])
        grouped[key]["term"].append(row["term"])
        grouped[key]["auto_confirmation_status"].append(row["auto_confirmation_status"])

    rows: list[dict[str, str]] = []
    for idx, ((source, document_id, local_path), values) in enumerate(sorted(grouped.items()), start=1):
        seed = {
            "source": source,
            "document_id": document_id,
            "local_path": local_path,
        }
        rows.append(
            {
                "source_appendix_id": f"SRCAPP{idx:03d}",
                "source_type": source,
                "document_id": document_id,
                "trial_ids": unique_join(values["trial_id"]),
                "analysis_tiers": unique_join(values["analysis_tier"]),
                "comparison_ids": unique_join(values["comparison_id"]),
                "locators_used": unique_join(values["locator"]),
                "terms_confirmed": unique_join(values["term"]),
                "source_url_or_local_path": source_url(seed),
                "confirmation_status": unique_join(values["auto_confirmation_status"]),
                "source_appendix_note": "Public ClinicalTrials.gov URL generated from NCT identifier."
                if source == "ClinicalTrials.gov"
                else (
                    "Local publication source file; formal journal citation is listed in the primary trial references."
                    if source == "publication"
                    else "Public FDA accessdata PDF URL verified by filename."
                ),
            }
        )

    fieldnames = [
        "source_appendix_id",
        "source_type",
        "document_id",
        "trial_ids",
        "analysis_tiers",
        "comparison_ids",
        "locators_used",
        "terms_confirmed",
        "source_url_or_local_path",
        "confirmation_status",
        "source_appendix_note",
    ]
    out_csv = TABLES / "confirmed_source_appendix.csv"
    write_csv(out_csv, rows, fieldnames)

    md_lines = [
        "# Confirmed source appendix",
        "",
        "This appendix lists source documents used in confirmed analysis-ready comparisons. FDA review rows currently use local PDF paths; public FDA accessdata URLs should be added before journal submission.",
        "",
        "| ID | Source type | Document ID | Trial(s) | Locator(s) | Source URL or local path | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        md_lines.append(
            "| "
            + " | ".join(
                [
                    row["source_appendix_id"],
                    row["source_type"],
                    row["document_id"],
                    row["trial_ids"],
                    row["locators_used"].replace("|", "/"),
                    row["source_url_or_local_path"].replace("|", "/"),
                    row["source_appendix_note"].replace("|", "/"),
                ]
            )
            + " |"
        )
    out_md = MANUSCRIPT / "confirmed_source_appendix.en.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    report = [
        "# Confirmed source appendix 生成报告",
        "",
        f"- 已生成：`{out_csv.relative_to(ROOT)}`",
        f"- 已生成：`{out_md.relative_to(ROOT)}`",
        f"- 来源文档数：{len(rows)}",
        f"- FDA review 文档数：{sum(1 for row in rows if row['source_type'] == 'FDA review')}",
        f"- ClinicalTrials.gov 文档数：{sum(1 for row in rows if row['source_type'] == 'ClinicalTrials.gov')}",
        f"- publication 文档数：{sum(1 for row in rows if row['source_type'] == 'publication')}",
    ]
    (PROTOCOL / "confirmed_source_appendix_report.zh.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print("\n".join(report))


if __name__ == "__main__":
    main()
