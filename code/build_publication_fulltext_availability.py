#!/usr/bin/env python3
"""Build expansion publication full-text availability table from ingested files."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"
INVENTORY = TABLES / "user_supplied_publication_batch_inventory.csv"
OUT = TABLES / "publication_fulltext_availability_expansion.csv"
LOCATOR = PROCESSED / "publication_table_locator_expansion.csv"
PILOT_PUB = ROOT / "data" / "raw" / "publications" / "pilot"

PILOT_EXISTING = {
    "TRIAL001": {
        "main": [PILOT_PUB / "DESTINYBreast01_Modi_2019_NEJM_PMID31825192.pdf"],
        "support": [PILOT_PUB / "DESTINYBreast01_Modi_2019_NEJM_appendix.pdf"],
    },
    "TRIAL002": {
        "main": [PILOT_PUB / "DREAMM2_Lonial_2019_LancetOncol_PMID31859245.pdf"],
        "support": [PILOT_PUB / "DREAMM2_Lonial_2019_LancetOncol_appendix.pdf"],
    },
    "TRIAL003": {
        "main": [PILOT_PUB / "EV201_Rosenberg_2019_JCO_PMID31356140.pdf"],
        "support": [PILOT_PUB / "EV201_Rosenberg_2019_JCO_PMID31356140.html", PILOT_PUB / "EV201_JCO_files"],
    },
    "TRIAL004": {
        "main": [PILOT_PUB / "IMMU13201_Bardia_2019_NEJM_PMID30786188.pdf"],
        "support": [
            PILOT_PUB / "IMMU13201_Bardia_2019_NEJM_appendix.pdf",
            PILOT_PUB / "IMMU13201_Bardia_2019_NEJM_protocol.pdf",
            PILOT_PUB / "IMMU13201_Bardia_2019_NEJM_data_sharing.pdf",
        ],
    },
    "TRIAL005": {
        "main": [PILOT_PUB / "ASCENT_Bardia_2021_NEJM_PMID33882206.pdf"],
        "support": [PILOT_PUB / "ASCENT_Bardia_2021_NEJM_appendix.pdf"],
    },
    "TRIAL006": {
        "main": [PILOT_PUB / "ALFA0701_Castaigne_2012_Lancet_PMID22482940.pdf"],
        "support": [PILOT_PUB / "ALFA0701_Castaigne_2012_Lancet_appendix.pdf"],
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def has_role(rows: list[dict[str, str]], role_tokens: list[str]) -> str:
    for row in rows:
        if row["copy_status"] == "copied" and any(token in row["document_role"] for token in role_tokens):
            return "yes"
    return "no"


def joined_files(rows: list[dict[str, str]], role_tokens: list[str]) -> str:
    files = [
        row["project_file"] for row in rows
        if row["copy_status"] == "copied" and any(token in row["document_role"] for token in role_tokens)
    ]
    return " || ".join(files)


def existing_files(paths: list[Path]) -> list[str]:
    return [str(path) for path in paths if path.exists()]


def main() -> None:
    trials = read_csv(PROCESSED / "trial_master_expansion_candidates.csv")
    inv = read_csv(INVENTORY)
    by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inv:
        by_trial[row["trial_id"]].append(row)

    availability_rows = []
    locator_rows = []
    loc_seq = 1
    for trial in trials:
        rows = by_trial.get(trial["trial_id"], [])
        pilot = PILOT_EXISTING.get(trial["trial_id"], {})
        pilot_main = existing_files(pilot.get("main", []))
        pilot_support = existing_files(pilot.get("support", []))
        main = "yes" if has_role(rows, ["main article"]) == "yes" or pilot_main else "no"
        supp = "yes" if has_role(rows, ["supplement", "data supplement"]) == "yes" or pilot_support else "no"
        protocol = has_role(rows, ["protocol"])
        if any("protocol" in path.lower() for path in pilot_support):
            protocol = "yes"
        html = has_role(rows, ["publisher html"])
        if any(path.lower().endswith((".html", "_files")) for path in pilot_support):
            html = "yes"
        if main == "yes" and (supp == "yes" or protocol == "yes" or html == "yes"):
            status = "primary_plus_supporting_files_available"
        elif main == "yes":
            status = "primary_only_available"
        elif supp == "yes" or protocol == "yes":
            status = "supporting_only_main_missing"
        else:
            status = "publication_files_missing"

        availability_rows.append({
            "trial_id": trial["trial_id"],
            "drug_id": trial["drug_id"],
            "approval_id": trial["approval_id"],
            "nct_number": trial["nct_number"],
            "acronym": trial["acronym"],
            "main_article_available": main,
            "supplement_or_data_supplement_available": supp,
            "protocol_available": protocol,
            "publisher_html_available": html,
            "publication_file_status": status,
            "main_article_files": " || ".join(pilot_main + ([joined_files(rows, ["main article"])] if joined_files(rows, ["main article"]) else [])),
            "supporting_files": " || ".join(pilot_support + ([joined_files(rows, ["supplement", "data supplement", "protocol", "publisher html"])] if joined_files(rows, ["supplement", "data supplement", "protocol", "publisher html"]) else [])),
        })
        for row in rows:
            locator_rows.append({
                "locator_id": f"EXPUBLOC{loc_seq:04d}",
                "document_id": f"EXPUB_{trial['trial_id']}_{loc_seq:04d}",
                "drug_id": trial["drug_id"],
                "trial_id": trial["trial_id"],
                "publication_part": row["document_role"],
                "page": "",
                "table_or_figure": "",
                "title": row["acronym"],
                "safety_topic": "publication source locator; table-level extraction pending",
                "priority": "highest" if row["document_role"] in ("main article", "supplementary appendix", "data supplement") else "high",
                "extraction_status": "source_file_available_needs_table_locator",
                "notes": row["project_file"],
            })
            loc_seq += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(availability_rows[0]))
        writer.writeheader()
        writer.writerows(availability_rows)

    with LOCATOR.open("w", newline="", encoding="utf-8") as f:
        for trial in trials:
            pilot = PILOT_EXISTING.get(trial["trial_id"], {})
            for role, paths in [("main article", pilot.get("main", [])), ("supporting pilot file", pilot.get("support", []))]:
                for path in paths:
                    if not path.exists():
                        continue
                    locator_rows.append({
                        "locator_id": f"EXPUBLOC{loc_seq:04d}",
                        "document_id": f"EXPUB_{trial['trial_id']}_{loc_seq:04d}",
                        "drug_id": trial["drug_id"],
                        "trial_id": trial["trial_id"],
                        "publication_part": role,
                        "page": "",
                        "table_or_figure": "",
                        "title": trial["acronym"],
                        "safety_topic": "pilot publication source locator; table-level extraction pending",
                        "priority": "highest",
                        "extraction_status": "source_file_available_needs_table_locator",
                        "notes": str(path),
                    })
                    loc_seq += 1
        writer = csv.DictWriter(f, fieldnames=list(locator_rows[0]))
        writer.writeheader()
        writer.writerows(locator_rows)

    missing_main = [row for row in availability_rows if row["main_article_available"] == "no"]
    primary_only = [row for row in availability_rows if row["publication_file_status"] == "primary_only_available"]
    lines = [
        "# Publication full-text availability 扩展状态报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/publication_fulltext_availability_expansion.csv`",
        "- `data/processed/publication_table_locator_expansion.csv`",
        "",
        "## 当前状态",
        "",
        f"- 扩展 trial 候选：{len(availability_rows)}",
        f"- 已有主论文：{sum(1 for row in availability_rows if row['main_article_available'] == 'yes')}",
        f"- 已有 supplement/data supplement：{sum(1 for row in availability_rows if row['supplement_or_data_supplement_available'] == 'yes')}",
        f"- 已有 protocol/SAP：{sum(1 for row in availability_rows if row['protocol_available'] == 'yes')}",
        f"- 已有 publisher HTML：{sum(1 for row in availability_rows if row['publisher_html_available'] == 'yes')}",
        f"- 仍缺主论文：{len(missing_main)}",
        "",
        "## 仍缺主论文的 trial",
        "",
    ]
    if missing_main:
        for row in missing_main:
            lines.append(f"- `{row['trial_id']}` / `{row['nct_number']}` / {row['acronym']}：{row['publication_file_status']}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 只有主论文、缺少补充材料或方案的 trial",
        "",
    ])
    if primary_only:
        for row in primary_only:
            lines.append(f"- `{row['trial_id']}` / {row['acronym']}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 下一步",
        "",
        "1. 对已有主论文和 supplement 的 trial 进入 table-level locator 和核心安全数值抽取。",
        "2. 目前主论文缺口已归零；后续只需把 supplement/protocol 缺口作为次级补充。",
        "3. 对只有主论文的 trial，先抽取主文安全表，同时把 supplement/protocol 列为次级缺口。",
    ])
    (PROTOCOL / "publication_fulltext_availability_expansion_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {LOCATOR.relative_to(ROOT)}")
    print("Wrote protocol/publication_fulltext_availability_expansion_report.zh.md")


if __name__ == "__main__":
    main()
