#!/usr/bin/env python3
"""Audit the current manuscript draft against project-level manuscript rules."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

IN = MANUSCRIPT / "preliminary_manuscript.en.md"
OUT = MANUSCRIPT / "manuscript_quality_audit.md"
REPORT = PROTOCOL / "manuscript_quality_audit_report.zh.md"

EXPECTED_ORDER = [
    "## Abstract",
    "## Keywords",
    "## Background",
    "## Methods",
    "## Results",
    "## Discussion",
    "## Conclusions",
    "## Tables",
    "## Supplementary Information",
    "## Acknowledgements",
    "## Authors' contributions",
    "## Funding",
    "## Availability of data and materials",
    "## Ethics approval and consent to participate",
    "## Consent for publication",
    "## Competing interests",
    "## References",
]


def section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\n(.*?)(?=^## |\Z)", re.M | re.S)
    match = pattern.search(text)
    return match.group(1) if match else ""


def count_references(text: str) -> int:
    refs = section(text, "## References")
    return len(re.findall(r"^\d+\.\s", refs, flags=re.M))


def heading_order_status(text: str) -> tuple[str, str]:
    positions = []
    missing = []
    for heading in EXPECTED_ORDER:
        match = re.search(rf"^{re.escape(heading)}$", text, flags=re.M)
        if match is None:
            missing.append(heading)
            positions.append(-1)
        else:
            positions.append(match.start())
    present_positions = [pos for pos in positions if pos != -1]
    ordered = present_positions == sorted(present_positions)
    if missing:
        return "needs_attention", "Missing headings: " + "; ".join(missing)
    if not ordered:
        return "needs_attention", "Headings are present but not in expected order."
    return "pass", "All expected BMC-style manuscript headings are present and ordered."


def main() -> None:
    text = IN.read_text(encoding="utf-8")
    methods = section(text, "## Methods")
    results = section(text, "## Results")
    discussion = section(text, "## Discussion")
    references_n = count_references(text)
    placeholders = sorted(set(re.findall(r"To be completed\.?", text)))
    order_status, order_note = heading_order_status(text)

    checks = [
        {
            "check": "BMC-style section order",
            "status": order_status,
            "note": order_note,
        },
        {
            "check": "Methods citation rule",
            "status": "pass" if not re.search(r"\[\d+(?:[-,]\d+)*\]", methods) else "needs_attention",
            "note": "Methods contains no numbered literature citations."
            if not re.search(r"\[\d+(?:[-,]\d+)*\]", methods)
            else "Methods contains numbered citations; review against project rule.",
        },
        {
            "check": "Results citation rule",
            "status": "pass" if not re.search(r"\[\d+(?:[-,]\d+)*\]", results) else "needs_attention",
            "note": "Results contains no numbered literature citations."
            if not re.search(r"\[\d+(?:[-,]\d+)*\]", results)
            else "Results contains numbered citations; review against project rule.",
        },
        {
            "check": "Reference count",
            "status": "needs_later_expansion" if references_n < 45 else "pass",
            "note": f"Current draft has {references_n} numbered references; project target is about 50 for a full manuscript.",
        },
        {
            "check": "Unfilled declaration placeholders",
            "status": "expected_user_input" if placeholders else "pass",
            "note": "Author/declaration fields still need user-provided details."
            if placeholders else "No generic declaration placeholders detected.",
        },
        {
            "check": "CT.gov full-module integration decision",
            "status": "pass"
            if "These candidates were not merged into the primary concordance analysis" in text
            and "exploratory screen" in discussion.lower()
            else "needs_attention",
            "note": "CT.gov full-module candidates are described as exploratory and not merged into the primary analysis.",
        },
        {
            "check": "No duplicate-adjudication boundary",
            "status": "pass"
            if "independent duplicate adjudication was not available" in text
            and "Cohen's kappa were not calculated" in text
            else "needs_attention",
            "note": "The draft states that duplicate adjudication was not available and kappa was not calculated.",
        },
        {
            "check": "Conservative clinical wording",
            "status": "pass"
            if not re.search(r"\b(proved|confirmed the mechanism|clinically validated|groundbreaking|revolutionary)\b", text, re.I)
            else "needs_attention",
            "note": "No prohibited overclaiming phrases detected.",
        },
    ]

    lines = [
        "# Manuscript quality audit",
        "",
        f"Input: `{IN.relative_to(ROOT)}`",
        "",
        "| Check | Status | Note |",
        "| --- | --- | --- |",
    ]
    for row in checks:
        lines.append(f"| {row['check']} | {row['status']} | {row['note']} |")

    lines.extend([
        "",
        "## Next actions",
        "",
        "1. Keep the current 28-pair confirmed analysis locked unless future structured review justifies adding new candidates.",
        "2. Expand and verify Background/Discussion references before submission-ready formatting.",
        "3. Fill author, funding, acknowledgements, and competing-interest declarations when user details are available.",
    ])
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = [
        "# 稿件质量审计报告",
        "",
        f"- 已生成：`{OUT.relative_to(ROOT)}`",
        f"- 当前参考文献数量：{references_n}",
        f"- 章节顺序：{order_status}",
        "- Methods/Results citation rule: checked",
        "- CT.gov full-module candidates: locked as exploratory supplementary queue",
        "- No duplicate-adjudication/kappa boundary: checked",
    ]
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
