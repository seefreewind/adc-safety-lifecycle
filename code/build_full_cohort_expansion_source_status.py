#!/usr/bin/env python3
"""Combine expansion CT.gov and FDA P1 document availability by trial."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    trials = read_csv(PROCESSED / "trial_master_expansion_candidates.csv")
    ctgov = {row["trial_id"]: row for row in read_csv(TABLES / "ctgov_expansion_availability.csv")}
    fda_queue = read_csv(TABLES / "fda_expansion_priority_document_queue.csv")

    fda_by_drug: dict[str, Counter] = defaultdict(Counter)
    p1_missing_urls: dict[str, list[str]] = defaultdict(list)
    for row in fda_queue:
        if row["priority"] != "P1":
            continue
        drug_id = row["drug_id"]
        fda_by_drug[drug_id][row["local_file_status"]] += 1
        if row["local_file_status"] == "missing":
            p1_missing_urls[drug_id].append(row["url_or_local_path"])

    out_rows = []
    for trial in trials:
        trial_id = trial["trial_id"]
        drug_id = trial["drug_id"]
        ct = ctgov.get(trial_id, {})
        fda_counts = fda_by_drug.get(drug_id, Counter())
        out_rows.append({
            "trial_id": trial_id,
            "approval_id": trial["approval_id"],
            "drug_id": drug_id,
            "nct_number": trial["nct_number"],
            "acronym": trial["acronym"],
            "verification_status": trial["verification_status"],
            "ctgov_ae_status": ct.get("ctgov_ae_status", "missing"),
            "ctgov_event_group_count": ct.get("event_group_count", "0"),
            "ctgov_serious_event_term_count": ct.get("serious_event_term_count", "0"),
            "ctgov_other_event_term_count": ct.get("other_event_term_count", "0"),
            "fda_p1_present_count_for_drug": fda_counts.get("present", 0),
            "fda_p1_missing_count_for_drug": fda_counts.get("missing", 0),
            "fda_p1_missing_urls_for_drug": " || ".join(p1_missing_urls.get(drug_id, [])),
            "recommended_next_step": "publication_locator_and_fda_toc_expansion",
        })

    out = TABLES / "full_cohort_expansion_source_status.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    ct_counts = Counter(row["ctgov_ae_status"] for row in out_rows)
    trials_with_fda_ready = sum(1 for row in out_rows if int(row["fda_p1_present_count_for_drug"]) > 0)
    lines = [
        "# 全队列来源扩展状态报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/full_cohort_expansion_source_status.csv`",
        "",
        "## 当前来源状态",
        "",
        f"- trial 候选：{len(out_rows)}",
        f"- CT.gov 有 AE module：{ct_counts.get('has_ae_module', 0)}",
        f"- CT.gov 暂无 AE module：{ct_counts.get('no_ae_module', 0)}",
        f"- 至少有一个 FDA P1 文件已在本地的 trial：{trials_with_fda_ready}",
        "",
        "## FDA P1 缺口",
        "",
    ]
    missing_drugs = {drug: urls for drug, urls in p1_missing_urls.items() if urls}
    if not missing_drugs:
        lines.append("- 无")
    else:
        for drug_id, urls in sorted(missing_drugs.items()):
            lines.append(f"- `{drug_id}`：{len(urls)} 个 P1 文件仍缺失")
            for url in urls[:3]:
                lines.append(f"  - {url}")
    lines.extend([
        "",
        "## 解释",
        "",
        "FDA P1 文件按 drug 计数，因为一个药物可能对应多个 approval/trial 事件。该表用于判断扩展阶段是否具备来源入口，不代表 safety 数值已经完成抽取。",
        "",
        "## 下一步",
        "",
        "1. 展开已下载 TOC，定位 medical/multidiscipline/summary review 中的安全表。",
        "2. 为 23 个 trial 扩展 publication locator。",
        "3. 将 CT.gov、FDA、publication 三类来源纳入扩展 evidence matrix，但 numeric discordance 仍需严格 A/B/C 分级。",
    ])
    (PROTOCOL / "full_cohort_expansion_source_status_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out.relative_to(ROOT)}")
    print("Wrote protocol/full_cohort_expansion_source_status_report.zh.md")


if __name__ == "__main__":
    main()
