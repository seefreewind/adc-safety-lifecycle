#!/usr/bin/env python3
"""Create page-level safety locators for expansion publication files."""

from __future__ import annotations

import csv
import re
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
LOCATOR = ROOT / "data" / "processed" / "publication_table_locator_expansion.csv"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"
OUT = TABLES / "publication_table_locator_expansion_detail.csv"
SNIPPETS = TABLES / "publication_safety_snippets_expansion.csv"


KEYWORDS = [
    "safety",
    "adverse event",
    "adverse events",
    "treatment-emergent",
    "serious adverse",
    "grade 3",
    "grade 4",
    "grade 5",
    "death",
    "deaths",
    "discontinuation",
    "discontinued",
    "dose reduction",
    "dose interruption",
    "dose delay",
    "fatal",
]

TABLE_RE = re.compile(r"(table\s+(?:s)?\d+[a-z]?|supplementary\s+table\s+(?:s)?\d+[a-z]?)", re.IGNORECASE)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize(text: str) -> str:
    return " ".join((text or "").split())


def keyword_hits(text: str) -> list[str]:
    lower = text.lower()
    return [kw for kw in KEYWORDS if kw in lower]


def snippet_for(text: str, hits: list[str]) -> str:
    if not hits:
        return ""
    lower = text.lower()
    positions = [lower.find(hit) for hit in hits if lower.find(hit) >= 0]
    if not positions:
        return normalize(text)[:500]
    pos = min(positions)
    start = max(pos - 220, 0)
    end = min(pos + 520, len(text))
    return normalize(text[start:end])


def pdf_pages(path: Path) -> list[tuple[str, str]]:
    reader = PdfReader(str(path))
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = normalize(page.extract_text() or "")
        except Exception:
            text = ""
        pages.append((str(idx), text))
    return pages


def html_text(path: Path) -> str:
    parser = TextExtractor()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.text()


def scan_file(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.is_dir():
        return []
    if path.suffix.lower() == ".pdf":
        units = pdf_pages(path)
    elif path.suffix.lower() in {".html", ".htm"}:
        units = [("html", html_text(path))]
    else:
        return []

    rows = []
    for page_label, text in units:
        hits = keyword_hits(text)
        if not hits:
            continue
        tables = sorted(set(match.group(1) for match in TABLE_RE.finditer(text)))
        rows.append({
            "page_or_unit": page_label,
            "keyword_hits": ";".join(hits),
            "table_mentions": ";".join(tables[:8]),
            "snippet": snippet_for(text, hits),
        })
    return rows


def locator_priority(part: str, hits: str, tables: str) -> str:
    if "supplement" in part and tables:
        return "P1"
    if "main article" in part and any(token in hits for token in ["safety", "adverse event", "serious adverse", "discontinuation"]):
        return "P1"
    if "protocol" in part and any(token in hits for token in ["dose reduction", "dose interruption", "discontinuation"]):
        return "P2"
    return "P3"


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    locators = read_csv(LOCATOR)
    detail_rows = []
    snippet_rows = []
    seq = 1
    for loc in locators:
        path = Path(loc["notes"])
        if not path.exists() or path.is_dir():
            continue
        matches = scan_file(path)
        for match in matches:
            priority = locator_priority(loc["publication_part"], match["keyword_hits"], match["table_mentions"])
            detail = {
                "detail_locator_id": f"EXPUBDET{seq:05d}",
                "trial_id": loc["trial_id"],
                "drug_id": loc["drug_id"],
                "document_id": loc["document_id"],
                "publication_part": loc["publication_part"],
                "source_file": str(path),
                "page_or_unit": match["page_or_unit"],
                "keyword_hits": match["keyword_hits"],
                "table_mentions": match["table_mentions"],
                "locator_priority": priority,
                "extraction_status": "needs_table_review",
            }
            detail_rows.append(detail)
            snippet_rows.append({
                **detail,
                "snippet": match["snippet"],
            })
            seq += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(detail_rows[0]))
        writer.writeheader()
        writer.writerows(detail_rows)

    with SNIPPETS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(snippet_rows[0]))
        writer.writeheader()
        writer.writerows(snippet_rows)

    p1_trials = sorted({row["trial_id"] for row in detail_rows if row["locator_priority"] == "P1"})
    lines = [
        "# Publication table-level locator 扩展扫描报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/publication_table_locator_expansion_detail.csv`",
        "- `tables/publication_safety_snippets_expansion.csv`",
        "",
        "## 扫描结果",
        "",
        f"- 文件级 locator：{len(locators)}",
        f"- 页码/单元级 safety locator：{len(detail_rows)}",
        f"- P1 locator 覆盖 trial：{len(p1_trials)}",
        "",
        "## 解释",
        "",
        "该表是自动页码级 locator，不直接代表数值已完成抽取。P1 表示优先进入人工/脚本化安全表抽取的位置，P2 多为 protocol 中剂量调整规则或补充性信息，P3 为背景性安全提及。",
        "",
        "## 下一步",
        "",
        "1. 从 P1 locator 中提取 core safety outcome 候选值。",
        "2. 对只有主文、缺少 supplement 的 trial，先抽取主文安全结果并标记 supplement_missing。",
        "3. 所有数值进入 source-comparability grading 前仍需保留页码、分母、治疗臂和定义。",
    ]
    (PROTOCOL / "publication_table_locator_expansion_detail_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SNIPPETS.relative_to(ROOT)}")
    print("Wrote protocol/publication_table_locator_expansion_detail_report.zh.md")


if __name__ == "__main__":
    main()
