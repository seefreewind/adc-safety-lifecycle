#!/usr/bin/env python3
"""Scan expansion FDA P1 documents for safety-review locator pages."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"

TRIALS = PROCESSED / "trial_master_expansion_candidates.csv"
FDA_QUEUE = TABLES / "fda_expansion_priority_document_queue.csv"
OUT = PROCESSED / "fda_review_table_locator_expansion.csv"
SUMMARY_OUT = TABLES / "fda_review_locator_expansion_summary.csv"


KEYWORD_PATTERNS = [
    ("review_of_safety", re.compile(r"\breview of safety\b", re.I)),
    ("clinical_safety", re.compile(r"\bclinical safety\b|\bsafety review\b", re.I)),
    ("adverse_event", re.compile(r"\badverse event|adverse events|\bAE\b|\bAEs\b|\bTEAE\b|\bTEAEs\b", re.I)),
    ("serious_adverse_event", re.compile(r"\bserious adverse event|serious adverse events|\bSAE\b|\bSAEs\b", re.I)),
    ("grade_3_or_higher", re.compile(r"grade\s*(?:3|≥3|>=3|3/4|3-4|4|5)", re.I)),
    ("death_or_fatal", re.compile(r"\bdeath\b|\bdeaths\b|\bfatal\b", re.I)),
    ("discontinuation", re.compile(r"discontinuation|discontinued|withdrawn from treatment", re.I)),
    ("dose_modification", re.compile(r"dose reduction|dose reductions|dose interruption|dose interruptions|dose delay|dose delays", re.I)),
]

TABLE_RE = re.compile(r"(?:Table|TABLE)\s+[0-9A-Za-z.\-]+[^.\n]{0,100}")

APPROVAL_BY_APPLICATION_PREFIX = {
    "761139": ["APP001"],
    "761158": ["APP002"],
    "761137": ["APP003"],
    "761115": ["APP004"],
    "761060": ["APP006"],
    "125388": ["APP007"],
    "125399": ["APP007"],
    "125427": ["APP008"],
    "761040": ["APP009"],
    "761121": ["APP010"],
    "761196": ["APP011"],
    "761208": ["APP012"],
    "761310": ["APP014"],
    "761394": ["APP017"],
    "761464": ["APP020"],
    "761384": ["APP019"],
    "761440": ["APP016"],
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def text_from_html(path: Path) -> str:
    parser = TextExtractor()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.text()


def text_units(path: Path) -> list[tuple[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        units = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            units.append((str(i), " ".join(text.split())))
        return units
    if suffix in {".html", ".htm"}:
        return [("html", text_from_html(path))]
    return []


def doc_kind(row: dict[str, str], path: Path) -> str:
    name = path.name.lower()
    reason = row.get("priority_reason", "").lower()
    if "toc" in name or path.suffix.lower() in {".html", ".htm"}:
        return "toc_html"
    if "lbl" in name or "label" in reason:
        return "label"
    if "ltr" in name or "letter" in reason:
        return "approval_letter"
    if any(token in name for token in ["medr", "multidiscipline", "sumr", "riskr", "stat", "clinical"]):
        return "review_pdf"
    if "review" in reason or "approval package" in reason:
        return "review_or_package_pdf"
    return "other_p1_document"


def keyword_hits(text: str) -> list[str]:
    return [label for label, pattern in KEYWORD_PATTERNS if pattern.search(text)]


def table_mentions(text: str) -> list[str]:
    seen = []
    for match in TABLE_RE.finditer(text):
        mention = " ".join(match.group(0).split())
        if mention not in seen:
            seen.append(mention)
    return seen[:10]


def locator_priority(kind: str, hits: list[str], tables: list[str]) -> str:
    concept_hits = set(hits) - {"adverse_event"}
    if kind in {"review_pdf", "review_or_package_pdf"} and concept_hits and (tables or "review_of_safety" in hits):
        return "P1"
    if kind in {"review_pdf", "review_or_package_pdf"} and hits:
        return "P2"
    if kind == "label" and concept_hits:
        return "P2"
    if hits:
        return "P3"
    return ""


def snippet(text: str, hits: list[str], limit: int = 700) -> str:
    if not text:
        return ""
    first_positions = []
    lower = text.lower()
    for label in hits:
        needle = label.replace("_", " ")
        pos = lower.find(needle)
        if pos >= 0:
            first_positions.append(pos)
    start = max(0, min(first_positions) - 180) if first_positions else 0
    compact = " ".join(text[start : start + limit].split())
    return compact


def split_ids(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def approval_ids_from_filename(path: Path) -> list[str]:
    for prefix, approval_ids in APPROVAL_BY_APPLICATION_PREFIX.items():
        if path.name.startswith(prefix):
            return approval_ids
    return []


def main() -> None:
    trials = read_csv(TRIALS)
    trials_by_approval: dict[str, list[str]] = defaultdict(list)
    approvals_by_drug: dict[str, set[str]] = defaultdict(set)
    trials_by_drug: dict[str, set[str]] = defaultdict(set)
    for row in trials:
        trials_by_approval[row["approval_id"]].append(row["trial_id"])
        approvals_by_drug[row["drug_id"]].add(row["approval_id"])
        trials_by_drug[row["drug_id"]].add(row["trial_id"])

    queue = read_csv(FDA_QUEUE)
    unique_docs: dict[str, dict[str, str]] = {}
    for row in queue:
        if row["priority"] != "P1" or row["local_file_status"] != "present":
            continue
        path = row.get("expected_local_file", "")
        if not path or path in unique_docs:
            continue
        if not Path(path).exists():
            continue
        unique_docs[path] = row

    review_name_re = re.compile(r"(MedR|MedicalR|MultidisciplineR|SumR|StatR|RiskR|ClinPharmR|Approv)\.pdf$", re.I)
    for path in RAW_DIR.glob("ADC*/*.pdf"):
        if not review_name_re.search(path.name):
            continue
        drug_id = path.parent.name
        if drug_id not in approvals_by_drug:
            continue
        path_text = str(path)
        if path_text in unique_docs:
            continue
        approval_ids = approval_ids_from_filename(path)
        if not approval_ids:
            continue
        unique_docs[path_text] = {
            "drug_id": drug_id,
            "candidate_approval_ids": ";".join(approval_ids),
            "document_date": "",
            "priority_reason": "local TOC-expanded review PDF",
        }

    out_rows: list[dict[str, str]] = []
    scan_errors: list[str] = []
    seq = 1
    for source_file, row in sorted(unique_docs.items(), key=lambda item: (item[1]["drug_id"], item[0])):
        path = Path(source_file)
        kind = doc_kind(row, path)
        candidate_approval_ids = split_ids(row.get("candidate_approval_ids", ""))
        trial_ids = sorted({trial_id for approval_id in candidate_approval_ids for trial_id in trials_by_approval.get(approval_id, [])})
        if not trial_ids:
            trial_ids = sorted(trials_by_drug.get(row["drug_id"], []))
        try:
            units = text_units(path)
        except Exception as exc:  # pypdf may fail on FDA placeholders; keep the audit trail.
            scan_errors.append(f"{source_file}: {exc}")
            continue

        for page_or_unit, text in units:
            hits = keyword_hits(text)
            if not hits:
                continue
            tables = table_mentions(text)
            priority = locator_priority(kind, hits, tables)
            if not priority:
                continue
            out_rows.append({
                "locator_id": f"FDAEXPLOC{seq:05d}",
                "drug_id": row["drug_id"],
                "candidate_approval_ids": row.get("candidate_approval_ids", ""),
                "trial_ids": ";".join(trial_ids),
                "document_date": row.get("document_date", ""),
                "document_kind": kind,
                "source_file": source_file,
                "page_or_unit": page_or_unit,
                "keyword_hits": ";".join(hits),
                "table_mentions": ";".join(tables),
                "locator_priority": priority,
                "extraction_status": "needs_review",
                "snippet": snippet(text, hits),
            })
            seq += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    rows_by_trial = defaultdict(list)
    for row in out_rows:
        for trial_id in split_ids(row["trial_ids"].replace(";", ";")):
            rows_by_trial[trial_id].append(row)

    summary_rows = []
    for trial in trials:
        trial_rows = rows_by_trial.get(trial["trial_id"], [])
        counts = Counter(row["locator_priority"] for row in trial_rows)
        summary_rows.append({
            "trial_id": trial["trial_id"],
            "drug_id": trial["drug_id"],
            "approval_id": trial["approval_id"],
            "acronym": trial["acronym"],
            "fda_locator_count": str(len(trial_rows)),
            "fda_p1_locator_count": str(counts.get("P1", 0)),
            "fda_p2_locator_count": str(counts.get("P2", 0)),
            "fda_p3_locator_count": str(counts.get("P3", 0)),
            "fda_locator_status": "has_p1_review_locator" if counts.get("P1", 0) else ("has_lower_priority_locator" if trial_rows else "no_locator"),
        })

    with SUMMARY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    priority_counts = Counter(row["locator_priority"] for row in out_rows)
    kind_counts = Counter(row["document_kind"] for row in out_rows)
    p1_trials = sum(1 for row in summary_rows if row["fda_locator_status"] == "has_p1_review_locator")
    no_locator = [row for row in summary_rows if row["fda_locator_status"] == "no_locator"]

    lines = [
        "# FDA P1 safety locator 扩展扫描报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `data/processed/fda_review_table_locator_expansion.csv`",
        "- `tables/fda_review_locator_expansion_summary.csv`",
        "",
        "## 扫描结果",
        "",
        f"- 唯一本地 P1 文件：{len(unique_docs)}",
        f"- locator 行：{len(out_rows)}",
        f"- P1 review locator 行：{priority_counts.get('P1', 0)}",
        f"- P2 locator 行：{priority_counts.get('P2', 0)}",
        f"- P3 locator 行：{priority_counts.get('P3', 0)}",
        f"- 至少有 P1 FDA review locator 的 trial：{p1_trials}/{len(summary_rows)}",
        "",
        "## 文件类型贡献",
        "",
    ]
    for kind, count in sorted(kind_counts.items()):
        lines.append(f"- `{kind}`：{count}")

    lines.extend([
        "",
        "## 暂无 FDA locator 的 trial",
        "",
    ])
    if no_locator:
        for row in no_locator:
            lines.append(f"- `{row['trial_id']}` {row['acronym']} ({row['drug_id']})")
    else:
        lines.append("- 无")

    if scan_errors:
        lines.extend([
            "",
            "## 扫描失败文件",
            "",
        ])
        for item in scan_errors[:20]:
            lines.append(f"- {item}")

    lines.extend([
        "",
        "## 使用边界",
        "",
        "该结果用于定位 FDA 审评文件中的安全页。FDA 审评常使用 pooled safety population 或跨研究安全池，后续抽取必须人工确认 trial、治疗臂、分母和分析人群后才能进入数值比较。",
    ])
    (PROTOCOL / "fda_review_locator_expansion_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print("Wrote protocol/fda_review_locator_expansion_report.zh.md")


if __name__ == "__main__":
    main()
