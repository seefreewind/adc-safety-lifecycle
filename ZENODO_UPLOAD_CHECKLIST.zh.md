# Zenodo 上传清单

## 建议上传方式

GitHub 仓库已建立：`https://github.com/seefreewind/adc-safety-lifecycle`

1. 登录 Zenodo。
2. 新建 Upload。
3. 上传本文件夹打包后的 zip：`adc_safety_lifecycle_zenodo_v0_1.zip`，或在 Zenodo 记录 `https://zenodo.org/records/20768613` 中更新文件版本。
4. Resource type 选择 `Dataset`；如果同时强调代码，可在 Description 中说明包含 analysis code。
5. Title 使用：
   `Public analytic materials for: Cross-Source Comparability of Aggregate Safety Outcomes in Pivotal Antibody-Drug Conjugate Trials: A Regulatory Evidence Study`
6. Creators：
   - Da Lin
   - Yu Zhang
7. Description 可使用 `README.md` 的第一段和 Contents 部分。
8. Keywords：
   antibody-drug conjugate; pharmacovigilance; drug safety; ClinicalTrials.gov; FDA review; adverse events; regulatory science; evidence synthesis
9. License 建议：
   - 数据和文档：Creative Commons Attribution 4.0 International，CC BY 4.0。
   - 如 Zenodo 只允许整个 deposit 统一 license，可先选 CC BY 4.0。
10. 发布后确认 DOI/record URL，并回填 manuscript 的 Data Availability 和 Code Availability；当前稿件已写入 `https://zenodo.org/records/20768613`。

## 不应上传的内容

- 下载的论文全文 PDF。
- 出版商网页文件夹或全文 HTML。
- FDA 原始 review PDF、label PDF、appendix PDF。
- `data/raw/`、`manuscript/*rendered_pages/`、本地截图、缓存文件。
- 可能包含长段版权原文摘录的 snippet/extraction raw tables。

## 投稿稿中可替换的 Data Availability 文字

After acceptance of the Zenodo record, replace the placeholder with:

`The derived analytic tables, comparability decisions, audit outputs, figure source files, and analysis code are available in Zenodo at https://zenodo.org/records/20768613 and GitHub at https://github.com/seefreewind/adc-safety-lifecycle. Copyrighted full-text articles, publisher supplementary files, and FDA source PDFs are not redistributed.`

## 投稿稿中可替换的 Code Availability 文字

`The custom code used to generate the analytic summaries, uncertainty estimates, audit outputs, and figures is available in the Zenodo record at https://zenodo.org/records/20768613 and in the GitHub repository at https://github.com/seefreewind/adc-safety-lifecycle.`
