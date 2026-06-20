#!/usr/bin/env python3
"""Create a reference list for the 23 primary trial publications."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_pmids(text: str) -> list[str]:
    return re.findall(r"PMID(\d{6,9})", text or "")


def dedupe_refs(refs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for ref in refs:
        key = (
            (ref.get("pmid") or "").strip(),
            (ref.get("doi") or "").strip().lower(),
            " ".join((ref.get("citation") or "").split()).lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return out


def main() -> None:
    availability = read_rows(TABLES / "publication_fulltext_availability_expansion.csv")
    refs = read_rows(DATA / "processed" / "publication_reference_inventory_expansion.csv")
    refs += read_rows(DATA / "processed" / "publication_reference_inventory.csv")
    refs += [
        {
            "trial_id": row.get("trial_id", ""),
            "pmid": row.get("pmid", ""),
            "doi": row.get("doi", ""),
            "citation": row.get("citation", ""),
            "reference_type": "PUBMED_LOOKUP",
        }
        for row in read_rows(DATA / "interim" / "pubmed_reference_lookup.csv")
    ]
    refs = dedupe_refs(refs)

    refs_by_pmid = {row.get("pmid", ""): row for row in refs if row.get("pmid")}

    rows: list[dict[str, str]] = []
    for idx, item in enumerate(availability, start=1):
        pmids = extract_pmids(item.get("main_article_files", ""))
        pmid = pmids[0] if pmids else ""
        ref = refs_by_pmid.get(pmid, {})
        rows.append(
            {
                "reference_number": str(idx),
                "trial_id": item["trial_id"],
                "short_trial_name": item["acronym"],
                "nct_number": item["nct_number"],
                "pmid": pmid,
                "doi": ref.get("doi", ""),
                "citation": ref.get("citation", ""),
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "local_main_article_files": item.get("main_article_files", ""),
                "reference_status": "matched_primary_trial_reference" if ref.get("citation") else "missing_citation",
            }
        )

    fieldnames = [
        "reference_number",
        "trial_id",
        "short_trial_name",
        "nct_number",
        "pmid",
        "doi",
        "citation",
        "pubmed_url",
        "local_main_article_files",
        "reference_status",
    ]
    out_csv = TABLES / "primary_trial_reference_list.csv"
    write_csv(out_csv, rows, fieldnames)

    md_lines = [
        "# Primary trial publication references",
        "",
        "These references are matched to local main-article files by PMID and should be rechecked during final reference formatting.",
        "",
    ]
    for row in rows:
        md_lines.append(
            f"{row['reference_number']}. {row['citation']} PMID: {row['pmid']}. DOI: {row['doi']}. PubMed: {row['pubmed_url']}"
        )
    out_md = MANUSCRIPT / "primary_trial_reference_list.en.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    missing = [row for row in rows if row["reference_status"] != "matched_primary_trial_reference"]
    report = [
        "# 主论文参考文献清单生成报告",
        "",
        f"- 已生成：`{out_csv.relative_to(ROOT)}`",
        f"- 已生成：`{out_md.relative_to(ROOT)}`",
        f"- 主论文引用匹配：{len(rows) - len(missing)}/{len(rows)}",
    ]
    if missing:
        report.append("- 仍缺引用：" + ", ".join(row["trial_id"] for row in missing))
    else:
        report.append("- 23 个 trial 的主论文引用均已按本地 PMID 匹配。")
    (PROTOCOL / "primary_trial_reference_list_report.zh.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print("\n".join(report))


if __name__ == "__main__":
    main()
