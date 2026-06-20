#!/usr/bin/env python3
"""Build a trial-level source and citation inventory for manuscript drafting."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
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


def unique_join(values: list[str]) -> str:
    seen: list[str] = []
    for value in values:
        value = (value or "").strip()
        if value and value not in seen:
            seen.append(value)
    return "; ".join(seen)


def short_citation(citation: str, limit: int = 240) -> str:
    citation = " ".join((citation or "").split())
    if len(citation) <= limit:
        return citation
    return citation[: limit - 3].rstrip() + "..."


def extract_pmids(text: str) -> list[str]:
    return re.findall(r"PMID(\d{6,9})", text or "")


def dedupe_refs(refs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for ref in refs:
        key = (
            (ref.get("pmid") or "").strip(),
            (ref.get("doi") or "").strip().lower(),
            " ".join((ref.get("citation") or "").split()).lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped


def main() -> None:
    trials = {}
    for path in [
        DATA / "processed" / "trial_master_expansion_candidates.csv",
        DATA / "processed" / "trial_master.csv",
    ]:
        for row in read_rows(path):
            trials.setdefault(row["trial_id"], row)

    pub_seed = read_rows(DATA / "interim" / "publication_core_safety_combined_seed.csv")
    fda_seed = read_rows(DATA / "interim" / "fda_core_safety_combined_seed.csv")
    ct_seed = read_rows(DATA / "interim" / "ctgov_core_safety_expansion_seed.csv")
    if not ct_seed:
        ct_seed = read_rows(DATA / "interim" / "ctgov_core_safety_seed.csv")

    pub_refs = read_rows(DATA / "processed" / "publication_reference_inventory_expansion.csv")
    pub_refs += read_rows(DATA / "processed" / "publication_reference_inventory.csv")
    for row in read_rows(DATA / "interim" / "pubmed_reference_lookup.csv"):
        pub_refs.append(
            {
                "trial_id": row.get("trial_id", ""),
                "pmid": row.get("pmid", ""),
                "doi": row.get("doi", ""),
                "citation": row.get("citation", ""),
                "reference_type": "PUBMED_LOOKUP",
            }
        )
    availability = {
        row["trial_id"]: row
        for row in read_rows(TABLES / "publication_fulltext_availability_expansion.csv")
    }
    ct_docs = read_rows(DATA / "interim" / "ctgov_source_document_expansion.csv")
    ct_docs += read_rows(DATA / "interim" / "ctgov_source_document_seed.csv")
    confirmations = read_rows(TABLES / "analysis_ready_source_auto_confirmation.csv")

    pub_docs_by_trial: dict[str, list[str]] = defaultdict(list)
    fda_docs_by_trial: dict[str, list[str]] = defaultdict(list)
    ct_docs_by_trial: dict[str, list[str]] = defaultdict(list)
    for row in pub_seed:
        pub_docs_by_trial[row["trial_id"]].append(row["document_id"])
    for row in fda_seed:
        fda_docs_by_trial[row["trial_id"]].append(row["document_id"])
    for row in ct_seed:
        ct_docs_by_trial[row["trial_id"]].append(row["document_id"])

    refs_by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pub_refs:
        refs_by_trial[row["trial_id"]].append(row)

    ct_by_doc = {row["document_id"]: row for row in ct_docs}

    local_paths_by_doc: dict[str, list[str]] = defaultdict(list)
    for row in confirmations:
        doc_id = row.get("document_id") or row.get("source_document_id") or ""
        if not doc_id:
            continue
        local_paths_by_doc[doc_id].append(row.get("source_url_or_local_path", ""))

    rows: list[dict[str, str]] = []
    for trial_id in sorted(trials):
        trial = trials[trial_id]
        refs = dedupe_refs(refs_by_trial.get(trial_id, []))
        result_refs = [r for r in refs if r.get("reference_type") == "RESULT"]
        main_article_files = availability.get(trial_id, {}).get("main_article_files", "")
        main_article_pmids = extract_pmids(main_article_files)
        matched_main_refs = [
            r for r in refs if r.get("pmid") and r.get("pmid") in main_article_pmids
        ]
        primary_pool = matched_main_refs or result_refs or refs
        primary_pool = primary_pool[:5]

        pub_doc_ids = sorted(set(pub_docs_by_trial.get(trial_id, [])))
        fda_doc_ids = sorted(set(fda_docs_by_trial.get(trial_id, [])))
        ct_doc_ids = sorted(set(ct_docs_by_trial.get(trial_id, [])))

        ct_titles = [ct_by_doc.get(doc, {}).get("document_title", "") for doc in ct_doc_ids]
        ct_dates = [ct_by_doc.get(doc, {}).get("document_date", "") for doc in ct_doc_ids]
        ct_paths = [ct_by_doc.get(doc, {}).get("url_or_local_path", "") for doc in ct_doc_ids]
        fda_paths = []
        pub_paths = []
        for doc in fda_doc_ids:
            fda_paths.extend(local_paths_by_doc.get(doc, []))
        for doc in pub_doc_ids:
            pub_paths.extend(local_paths_by_doc.get(doc, []))

        rows.append(
            {
                "trial_id": trial_id,
                "short_trial_name": trial.get("acronym", ""),
                "nct_number": trial.get("nct_number", ""),
                "structured_publication_document_ids": unique_join(pub_doc_ids),
                "structured_fda_document_ids": unique_join(fda_doc_ids),
                "structured_ctgov_document_ids": unique_join(ct_doc_ids),
                "candidate_publication_reference_count": str(len(refs)),
                "candidate_result_reference_count": str(len(result_refs)),
                "local_main_article_files": main_article_files,
                "local_main_article_pmids": unique_join(main_article_pmids),
                "matched_main_article_reference_count": str(len(matched_main_refs)),
                "candidate_publication_pmids": unique_join([r.get("pmid", "") for r in primary_pool]),
                "candidate_publication_dois": unique_join([r.get("doi", "") for r in primary_pool]),
                "candidate_publication_citations": " || ".join(
                    short_citation(r.get("citation", "")) for r in primary_pool if r.get("citation")
                ),
                "ctgov_titles": unique_join(ct_titles),
                "ctgov_result_dates": unique_join(ct_dates),
                "ctgov_local_json": unique_join(ct_paths),
                "confirmed_publication_local_files": unique_join(pub_paths),
                "confirmed_fda_local_files": unique_join(fda_paths),
                "citation_inventory_status": "primary_reference_matched_to_local_main_article"
                if len(matched_main_refs) == 1
                else (
                    "multiple_main_article_reference_matches"
                    if len(matched_main_refs) > 1
                    else (
                        "local_main_article_pmid_needs_reference_lookup"
                        if main_article_pmids
                        else (
                        "single_result_reference_candidate"
                        if len(result_refs) == 1
                        else "needs_final_reference_selection"
                        )
                    )
                ),
            }
        )

    fieldnames = [
        "trial_id",
        "short_trial_name",
        "nct_number",
        "structured_publication_document_ids",
        "structured_fda_document_ids",
        "structured_ctgov_document_ids",
        "candidate_publication_reference_count",
        "candidate_result_reference_count",
        "local_main_article_files",
        "local_main_article_pmids",
        "matched_main_article_reference_count",
        "candidate_publication_pmids",
        "candidate_publication_dois",
        "candidate_publication_citations",
        "ctgov_titles",
        "ctgov_result_dates",
        "ctgov_local_json",
        "confirmed_publication_local_files",
        "confirmed_fda_local_files",
        "citation_inventory_status",
    ]
    out_csv = TABLES / "source_citation_inventory.csv"
    write_csv(out_csv, rows, fieldnames)

    status_counts = defaultdict(int)
    for row in rows:
        status_counts[row["citation_inventory_status"]] += 1

    md_lines = [
        "# Source citation inventory",
        "",
        "This table is a working citation inventory. It records which source documents are currently used in structured extraction and which publication references are available for final reference selection.",
        "",
        "| Trial | NCT | Publication documents | FDA documents | CT.gov documents | Candidate publication references | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        refs = row["candidate_publication_citations"] or "No candidate publication reference captured"
        md_lines.append(
            "| "
            + " | ".join(
                [
                    row["short_trial_name"] or row["trial_id"],
                    row["nct_number"],
                    row["structured_publication_document_ids"] or "-",
                    row["structured_fda_document_ids"] or "-",
                    row["structured_ctgov_document_ids"] or "-",
                    refs.replace("|", "/"),
                    row["citation_inventory_status"],
                ]
            )
            + " |"
        )
    out_md = MANUSCRIPT / "source_citation_inventory.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    report = [
        "# 来源与引用底账生成报告",
        "",
        f"- 已生成：`{out_csv.relative_to(ROOT)}`",
        f"- 已生成：`{out_md.relative_to(ROOT)}`",
        f"- 覆盖 trial 数：{len(rows)}",
    ]
    for status, count in sorted(status_counts.items()):
        report.append(f"- {status}: {count}")
    report.append("")
    report.append("说明：该底账用于后续 reference checking。`needs_final_reference_selection` 表示同一 trial 有多个候选引用或没有明确 RESULT 类型引用，需要下一步核定主论文引用。")
    out_report = PROTOCOL / "source_citation_inventory_report.zh.md"
    out_report.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
