#!/usr/bin/env python3
"""Create verified candidate references for Background and Discussion claims."""

from __future__ import annotations

import csv
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

BACKGROUND_PMIDS = [
    {
        "pmid": "33558752",
        "claim_support": "ADC therapeutic index, approval landscape, clinical potential, systemic toxicity limitations",
    },
    {
        "pmid": "37308581",
        "claim_support": "ADC mechanism, expanding oncology use, targets, payloads, and late-phase development",
    },
    {
        "pmid": "21366476",
        "claim_support": "ClinicalTrials.gov results database structure and reporting issues",
    },
    {
        "pmid": "35482320",
        "claim_support": "ClinicalTrials.gov safety-result availability, completeness, and concordance for FDA-approved drugs",
    },
    {
        "pmid": "26269118",
        "claim_support": "Comparison of serious adverse events in ClinicalTrials.gov and corresponding journal articles",
    },
    {
        "pmid": "25009136",
        "claim_support": "Differences in serious-adverse-event reporting between registries and journal articles",
    },
    {
        "pmid": "36408673",
        "claim_support": "Treatment-related adverse events of antibody-drug conjugates across clinical trials",
    },
    {
        "pmid": "29027591",
        "claim_support": "Clinical toxicity of antibody-drug conjugates and payload-related safety patterns",
    },
    {
        "pmid": "34647966",
        "claim_support": "Interstitial lung disease associated with anti-ERBB2 antibody-drug conjugates",
    },
    {
        "pmid": "39303762",
        "claim_support": "Ocular adverse events associated with antibody-drug conjugates",
    },
    {
        "pmid": "38502995",
        "claim_support": "Clinical management and monitoring of adverse events of special interest for datopotamab deruxtecan",
    },
    {
        "pmid": "35964548",
        "claim_support": "Clinical management considerations for trastuzumab deruxtecan adverse events",
    },
    {
        "pmid": "37100738",
        "claim_support": "CONSORT Harms 2022 reporting guideline for harms in randomized trials",
    },
    {
        "pmid": "29907552",
        "claim_support": "Limitations of maximum-grade adverse-event reporting in hematologic malignancy trials",
    },
    {
        "pmid": "32452660",
        "claim_support": "Quality of adverse-event reporting in phase III breast and colorectal cancer trials",
    },
    {
        "pmid": "30653255",
        "claim_support": "Adverse-event reporting quality in randomized trials of immune checkpoint inhibitors",
    },
    {
        "pmid": "22985899",
        "claim_support": "Adherence to CONSORT harms-reporting recommendations in clinical-trial publications",
    },
    {
        "pmid": "33168656",
        "claim_support": "FDA approval summary example for sacituzumab govitecan and regulatory safety evidence",
    },
    {
        "pmid": "33753456",
        "claim_support": "FDA approval summary example for fam-trastuzumab deruxtecan in HER2-positive breast cancer",
    },
    {
        "pmid": "36780610",
        "claim_support": "FDA approval summary example for fam-trastuzumab deruxtecan in HER2-low breast cancer",
    },
    {
        "pmid": "36415085",
        "claim_support": "Tisotumab vedotin review and safety considerations",
    },
    {
        "pmid": "35404158",
        "claim_support": "Sacituzumab govitecan clinical role and safety context in solid tumors",
    },
    {
        "pmid": "39007226",
        "claim_support": "Antibody-drug conjugates in hematologic malignancies and safety context",
    },
    {
        "pmid": "32657795",
        "claim_support": "Antibody-drug conjugates in breast cancer and treatment-development context",
    },
]


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
    return ""


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
        root = ET.fromstring(response.read())
    article = root.find(".//PubmedArticle")
    if article is None:
        return {"pmid": pmid, "lookup_status": "not_found"}

    title_node = article.find(".//ArticleTitle")
    title = " ".join("".join(title_node.itertext()).split()).rstrip(".") if title_node is not None else ""
    journal = text_or_empty(article.find(".//Journal/ISOAbbreviation")) or text_or_empty(article.find(".//Journal/Title"))
    volume = text_or_empty(article.find(".//JournalIssue/Volume"))
    issue = text_or_empty(article.find(".//JournalIssue/Issue"))
    pages = text_or_empty(article.find(".//Pagination/MedlinePgn"))
    year = pub_year(article)
    doi = article_id(article, "doi")
    authors = author_list(article).rstrip(".")
    volume_issue = f"{volume}({issue})" if volume and issue else volume or (f"({issue})" if issue else "")
    loc = f"{volume_issue}:{pages}" if volume_issue and pages else volume_issue or pages
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
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "lookup_status": "pubmed_verified",
    }


def main() -> None:
    rows: list[dict[str, str]] = []
    for offset, item in enumerate(BACKGROUND_PMIDS, start=24):
        row = fetch_pubmed(item["pmid"])
        row["reference_number"] = str(offset)
        row["claim_support"] = item["claim_support"]
        rows.append(row)
        time.sleep(0.34)

    fieldnames = [
        "reference_number",
        "pmid",
        "doi",
        "title",
        "journal",
        "year",
        "citation",
        "pubmed_url",
        "claim_support",
        "lookup_status",
    ]
    out_csv = TABLES / "background_discussion_reference_list.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md_lines = [
        "# Background and Discussion candidate references",
        "",
        "These references were fetched from PubMed and mapped to specific Background/Discussion claims. Final submission formatting and claim-level verification are still required.",
        "",
    ]
    for row in rows:
        md_lines.append(
            f"{row['reference_number']}. {row['citation']} PMID: {row['pmid']}. DOI: {row['doi']}. PubMed: {row['pubmed_url']}"
        )
        md_lines.append(f"   - Supports: {row['claim_support']}")
    out_md = MANUSCRIPT / "background_discussion_reference_list.en.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    report = [
        "# Background/Discussion 候选引用生成报告",
        "",
        f"- 已生成：`{out_csv.relative_to(ROOT)}`",
        f"- 已生成：`{out_md.relative_to(ROOT)}`",
        f"- PubMed verified：{sum(1 for row in rows if row['lookup_status'] == 'pubmed_verified')}/{len(rows)}",
        "- 说明：这些引用已插入主稿候选编号，但投稿前仍需逐句核验 claim alignment。",
    ]
    (PROTOCOL / "background_discussion_reference_list_report.zh.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print("\n".join(report))


if __name__ == "__main__":
    main()
