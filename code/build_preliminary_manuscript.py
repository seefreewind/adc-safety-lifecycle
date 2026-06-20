#!/usr/bin/env python3
"""Create a clean preliminary manuscript with blank author fields."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"


def main() -> None:
    source = MANUSCRIPT / "current_full_manuscript_draft.en.md"
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:]).lstrip()

    preliminary = "\n\n".join(
        [
            f"# {title}",
            "Authors:\n\nAffiliations:\n\nCorresponding author:",
            body,
        ]
    )

    preliminary = preliminary.replace(
        "## Authors' contributions\n\nTo be completed.",
        "## Authors' contributions\n\n",
    )

    out = MANUSCRIPT / "preliminary_manuscript.en.md"
    out.write_text(preliminary.rstrip() + "\n", encoding="utf-8")

    report = """# 初步稿件生成报告

- 已生成：`manuscript/preliminary_manuscript.en.md`
- 作者栏已留空：Authors、Affiliations、Corresponding author。
- 该文件基于当前英文工作稿生成，未覆盖 `manuscript/current_full_manuscript_draft.en.md`。
"""
    (PROTOCOL / "preliminary_manuscript_report.zh.md").write_text(report, encoding="utf-8")
    print(report.strip())


if __name__ == "__main__":
    main()
