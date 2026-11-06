# 2026-11-07 中文 SCI 文稿 + 带目录 Word

## 任务
将 FMR IMA Layer-1 论文先写成完整中文稿，再导出带目录的 Word（.docx），数字与 seed-42 JSON 对齐。

## 依据
- Desktop SCI Writing 指南：功能顺序 Title / 八句摘要 / Keywords / Intro 三部分 / Methods 对象–表述–实现–标定–核验 / Results 逻辑块 / Discussion / Conclusions / Availability / References
- nature-proposal-writer + nature-writing：证据先于文字，主张边界诚实
- 中文去 AI 味约束：少冒号破折号分号、短句、基础过渡、避免 链路/闭环/耦合、无待确定占位、少用 不要/而不是

## 核验数字（seed=42，相对 JSON）
| 量 | 值 | 来源 |
|----|----|------|
| 折内留出 ROA / leak MAE | 6.37 mm² / 0.245 pp | `cross_validation/summary.json` |
| IMA-AP70 折内 abs err | 6.60 / 0.198 | 同上 |
| 规则留出 MAE | 5.24 / 0.043 | `loo_evaluation.json` |
| 排序 | 36 / 35 / 30，p=0.857 | `planner/recommendation.json` |
| 最优 | IMA-CS 20%，AP↓11.0%，leak 0.391%，LCx 8.6 mm | 同上 |
| LHS | N=120，P(top-1)=0.342，mean feasible 0.822 | 同上 |
| η±20% | 仍为 IMA-CS 20%，AP↓ 8.8 / 11.0 / 13.2 | `paper_tables/eta_sensitivity` |

## 交付物
1. `docs/manuscript_zh_final.md`
2. `docs/manuscript_zh_final.docx`
3. `C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_zh_final.docx`（主写路径，含 TOC 域 + Heading 样式 + 静态大纲 + 图 1–5）
4. 构建脚本：`tools/build_manuscript_zh_docx.py`

## OA PDF
- 已用本地：`F:\fmr_ref_pdfs\Worthley_MAVERIC_EuroIntervention.pdf`
- 已用本地：`F:\fmr_ref_pdfs\Rottlander_2022_Frontiers_CS_MVA.pdf`
- Galili RSOS：按 DOI 10.1098/rsos.211464 引用（出版商 PDF 常被 Cloudflare 拦截，未强下到 E:）

## Word TOC 说明
文档含 `w:fldChar` TOC 域与 Heading 1/2 样式。打开 Word 后右键目录 → 更新域即可生成带页码目录。静态大纲在更新前也可阅读。

## 磁盘
E: 余量偏紧。Word 先写 Desktop（C:），再复制到 `docs/`。
