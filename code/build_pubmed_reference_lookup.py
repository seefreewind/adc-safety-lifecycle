#!/usr/bin/env python3
"""Look up local main-article PMIDs that are missing from the reference inventory."""

from __future__ import annotations

import csv
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "tables"
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


def text_or_empty(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text.strip()


def article_id(article: ET.Element, id_type: str) -> str:
    for node in article.findall(".//ArticleId"):
        if node.attrib.get("IdType") == id_type and node.text:
            return node.text.strip()
    return ""


def author_list(article: ET.Element) -> str:
    names = []
    for author in article.findall(".//AuthorList/Author"):
        last = text_or_empty(author.find("LastName"))
        initials = text_or_empty(author.find("Initials"))
        collective = text_or_empty(author.find("CollectiveName"))
        if last:
            names.append(f"{last} {initials}".strip())
        elif collective:
            names.append(collective)
    if len(names) > 6:
        return ", ".join(names[:6]) + ", et al."
    return ", ".join(names)


def pub_year(article: ET.Element) -> str:
    for path in [
        ".//JournalIssue/PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubMedPubDate[@PubStatus='pubmed']/Year",
    ]:
        value = text_or_empty(article.find(path))
        if value:
            return value
    medline_date = text_or_empty(article.find(".//JournalIssue/PubDate/MedlineDate"))
    match = re.search(r"\d{4}", medline_date)
    return match.group(0) if match else ""


def fetch_pubmed(pmid: str) -> dict[str, str]:
    params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
            "tool": "adc_safety_lifecycle",
            "email": "codex@example.com",
        }
    )
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"
    with urllib.request.urlopen(url, timeout=30) as response:
        xml_text = response.read()
    root = ET.fromstring(xml_text)
    article = root.find(".//PubmedArticle")
    if article is None:
        return {
            "pmid": pmid,
            "lookup_status": "not_found",
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }

    title = " ".join("".join(article.find(".//ArticleTitle").itertext()).split()) if article.find(".//ArticleTitle") is not None else ""
    title = title.rstrip(".")
    journal = text_or_empty(article.find(".//Journal/ISOAbbreviation")) or text_or_empty(article.find(".//Journal/Title"))
    volume = text_or_empty(article.find(".//JournalIssue/Volume"))
    issue = text_or_empty(article.find(".//JournalIssue/Issue"))
    pages = text_or_empty(article.find(".//Pagination/MedlinePgn"))
    year = pub_year(article)
    doi = article_id(article, "doi")
    authors = author_list(article)

    volume_issue = volume
    if issue:
        volume_issue = f"{volume}({issue})" if volume else f"({issue})"
    loc = ""
    if volume_issue and pages:
        loc = f"{volume_issue}:{pages}"
    elif volume_issue:
        loc = volume_issue
    elif pages:
        loc = pages

    authors = authors.rstrip(".")
    citation = f"{authors}. {title}. {journal}. {year}"
    if loc:
        citation += f";{loc}"
    if doi:
        citation += f". doi: {doi}"
    citation += "."

    return {
        "pmid": pmid,
        "doi": doi,
        "title": title,
        "journal": journal,
        "year": year,
        "citation": citation,
        "lookup_status": "pubmed_verified",
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }


def main() -> None:
    known_refs = read_rows(DATA / "processed" / "publication_reference_inventory_expansion.csv")
    known_refs += read_rows(DATA / "processed" / "publication_reference_inventory.csv")
    known_pmids = {row.get("pmid", "") for row in known_refs if row.get("pmid")}

    missing: list[dict[str, str]] = []
    for row in read_rows(TABLES / "publication_fulltext_availability_expansion.csv"):
        for pmid in extract_pmids(row.get("main_article_files", "")):
            if pmid not in known_pmids:
                missing.append(
                    {
                        "trial_id": row["trial_id"],
                        "acronym": row["acronym"],
                        "nct_number": row["nct_number"],
                        "pmid": pmid,
                        "main_article_files": row.get("main_article_files", ""),
                    }
                )

    rows: list[dict[str, str]] = []
    for item in missing:
        looked_up = fetch_pubmed(item["pmid"])
        rows.append({**item, **looked_up})
        time.sleep(0.34)

    fieldnames = [
        "trial_id",
        "acronym",
        "nct_number",
        "pmid",
        "doi",
        "title",
        "journal",
        "year",
        "citation",
        "lookup_status",
        "pubmed_url",
        "main_article_files",
    ]
    out_csv = DATA / "interim" / "pubmed_reference_lookup.csv"
    write_csv(out_csv, rows, fieldnames)

    report = [
        "# PubMed 引用补查报告",
        "",
        f"- 已生成：`{out_csv.relative_to(ROOT)}`",
        f"- 本地全文 PMID 缺口：{len(missing)}",
        f"- PubMed verified：{sum(1 for row in rows if row.get('lookup_status') == 'pubmed_verified')}",
    ]
    for row in rows:
        report.append(f"- {row['trial_id']} {row['acronym']}: PMID {row['pmid']}; DOI {row.get('doi', '')}")
    (PROTOCOL / "pubmed_reference_lookup_report.zh.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
