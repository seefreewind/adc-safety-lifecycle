# Drug Safety 下一版稿件视觉检查报告

Date: 2026-06-19

## 文件

- Markdown：`manuscript/drug_safety_revision_manuscript.en.md`
- DOCX：`manuscript/drug_safety_revision_manuscript.docx`
- 渲染 PDF：`manuscript/drug_safety_revision_rendered_pages/drug_safety_revision_manuscript.pdf`
- 页面 PNG：`manuscript/drug_safety_revision_rendered_pages/page_*.png`

## 本轮修改后检查结果

- Word 渲染成功，共 34 页；已应用双倍行距、页码和按页重启的行号设置。
- 摘要中不再把 269 个 algorithm-generated candidate pairs 作为主结果解释；主要结果仍为 17/53 jointly reported strata。
- Methods 已删除 `project inventory` 和 `local main trial publication` 等内部项目语言，改为 FDA/Drugs@FDA/label/registry/publication 的可重复识别链。
- ClinicalTrials.gov all-cause mortality 已与 fatal adverse-event reporting 分开处理；Supplementary Table S1 显示 Fatal AE 为 0/23 overall、all-cause mortality record 为 19/23 overall。
- Table 3C 已改为 36 个 jointly reported but non-comparable strata 的原因域，不再使用 248 个 generated pair 原因计数。
- Figure 3 已改为 stratum pathway 和 value-pair pathway 两条流程，不再把不同单位画在同一柱状 attrition 图中。
- Figure 4 已改为 absolute percentage-point difference，避免 Source 2 minus Source 1 的方向性歧义；2 pp 线标明为描述性参考线。
- 抽查页面：Figure 3 第 12 页、Figure 4 第 13 页、Table 2/3 第 16 页、Supplementary Table S1 第 21 页，未见明显遮挡、重叠或截断。
- Declarations 页面显示正常；AI tool use disclosure 已加入。作者、单位、基金、利益冲突和贡献仍按用户要求留空或待补充。

## 仍需人工介入

1. 投稿前重新检索 FDA 与 ClinicalTrials.gov 最新记录，并记录最终检索日期。
2. 若有条件，安排真实第二审核者复核 53 个 jointly reported strata 和 28 个 analysis-ready pairs。
3. 建立 OSF、Zenodo 或 GitHub 数据/代码仓库，并替换 Data Availability 和 Code Availability 中的待完成表述。
4. 补齐 Authors、Affiliations、Corresponding author、Funding、Conflicts of Interest、Acknowledgements、Authors' Contributions。
5. 按 Drug Safety/Vancouver 要求逐条核验参考文献格式、DOI、卷期页码，并准备 STROBE checklist。

## 模拟双人评审边界

- 已生成模拟双人评审记录，但仅作为 internal stress test。
- 模拟结果不得在投稿稿中写作真实 independent human reviewer agreement 或真实 Cohen's kappa。
- 正式 Drug Safety 版稿件只报告 structured audit trail、source confirmation、visual audit 和敏感性分析。
