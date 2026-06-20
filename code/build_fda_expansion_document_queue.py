#!/usr/bin/env python3
"""Build a prioritized FDA document queue for expansion candidates."""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

APPROVALS = PROCESSED / "approval_event_expansion_candidates.csv"
INVENTORY = PROCESSED / "fda_review_document_inventory.csv"
QUEUE = TABLES / "fda_expansion_priority_document_queue.csv"

TARGET_TOKENS = ["toc.html", "label", "lbl", "appletter", "approv", "sumr", "multidiscipline", "medr", "medical"]
REVIEW_TOKENS = ["toc.html", "sumr", "multidiscipline", "medr", "medical", "approv"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    return cleaned.strip("_")[:180] or "document"


def local_path_for(drug_id: str, url: str) -> Path:
    return RAW_DIR / drug_id / slug(url.split("/")[-1])


def days_between(a: date | None, b: date | None) -> int | None:
    if not a or not b:
        return None
    return abs((a - b).days)


def priority_for(row: dict[str, str], app_dates: list[date]) -> tuple[str, str]:
    url = row.get("url_or_local_path", "").lower()
    notes = row.get("notes", "").lower()
    doc_date = parse_date(row.get("document_date", ""))
    delta = min([d for d in (days_between(doc_date, app_date) for app_date in app_dates) if d is not None], default=None)

    if not any(token in url for token in TARGET_TOKENS):
        return "exclude", "not a target document type"
    if any(token in url for token in REVIEW_TOKENS) and ("orig" in notes or (delta is not None and delta <= 120)):
        return "P1", "review/TOC/approval package near original or key approval date"
    if ("label" in url or "lbl" in url or "appletter" in url) and delta is not None and delta <= 45:
        return "P1", "label or approval letter near approval date"
    if any(token in url for token in TARGET_TOKENS) and delta is not None and delta <= 180:
        return "P2", "target document within 180 days of approval date"
    if any(token in url for token in REVIEW_TOKENS):
        return "P2", "review-like document outside immediate approval window"
    return "P3", "lower-priority label or letter for lifecycle context"


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    approvals = read_csv(APPROVALS)
    inventory = read_csv(INVENTORY)
    app_dates_by_drug: dict[str, list[date]] = {}
    approval_ids_by_drug: dict[str, list[str]] = {}
    for app in approvals:
        drug_id = app["drug_id"]
        parsed = parse_date(app.get("approval_date", ""))
        if parsed:
            app_dates_by_drug.setdefault(drug_id, []).append(parsed)
        approval_ids_by_drug.setdefault(drug_id, []).append(app["approval_id"])

    queue_rows = []
    for row in inventory:
        drug_id = row.get("drug_id", "")
        if drug_id not in app_dates_by_drug:
            continue
        priority, reason = priority_for(row, app_dates_by_drug[drug_id])
        if priority == "exclude":
            continue
        url = row.get("url_or_local_path", "")
        local = local_path_for(drug_id, url)
        queue_rows.append({
            "priority": priority,
            "drug_id": drug_id,
            "candidate_approval_ids": ";".join(sorted(set(approval_ids_by_drug.get(drug_id, [])))),
            "document_date": row.get("document_date", ""),
            "url_or_local_path": url,
            "expected_local_file": str(local),
            "local_file_status": "present" if local.exists() else "missing",
            "inventory_document_id": row.get("document_id", ""),
            "inventory_notes": row.get("notes", ""),
            "priority_reason": reason,
        })

    order = {"P1": 0, "P2": 1, "P3": 2}
    queue_rows.sort(key=lambda r: (order[r["priority"]], r["drug_id"], r["document_date"], r["url_or_local_path"]))
    with QUEUE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(queue_rows[0]))
        writer.writeheader()
        writer.writerows(queue_rows)

    counts = {}
    missing_counts = {}
    for row in queue_rows:
        counts[row["priority"]] = counts.get(row["priority"], 0) + 1
        if row["local_file_status"] == "missing":
            missing_counts[row["priority"]] = missing_counts.get(row["priority"], 0) + 1

    lines = [
        "# FDA 扩展文件优先队列报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/fda_expansion_priority_document_queue.csv`",
        "",
        "## 队列规模",
        "",
        f"- 总候选文件：{len(queue_rows)}",
        f"- P1 文件：{counts.get('P1', 0)}，其中缺失 {missing_counts.get('P1', 0)}",
        f"- P2 文件：{counts.get('P2', 0)}，其中缺失 {missing_counts.get('P2', 0)}",
        f"- P3 文件：{counts.get('P3', 0)}，其中缺失 {missing_counts.get('P3', 0)}",
        "",
        "## 优先级定义",
        "",
        "- P1：原始批准/关键转换批准附近的 review、TOC、approval package、label 或 approval letter。",
        "- P2：批准日期 180 天内的相关 FDA 文件，或 review-like 文件但不在直接批准窗口。",
        "- P3：较低优先级的后续标签/批准信，用于 lifecycle 背景，不优先进入核心安全抽取。",
        "",
        "## 当前建议",
        "",
        "下一步只下载 P1 缺失文件。P2/P3 暂作为后续补充，不应拖慢当前全队列来源覆盖分析。",
    ]
    (PROTOCOL / "fda_expansion_document_queue_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {QUEUE.relative_to(ROOT)}")
    print("Wrote protocol/fda_expansion_document_queue_report.zh.md")
    print(counts)
    print({f"missing_{k}": v for k, v in missing_counts.items()})


if __name__ == "__main__":
    main()
