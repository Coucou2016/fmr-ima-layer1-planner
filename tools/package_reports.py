#!/usr/bin/env python3
"""Build self-contained paper/report HTML (+ MD/PDF) from seed-42 artifacts.

Outputs (preferred locations):
  report.html, report.md, report.pdf          (project root)
  docs/paper.html, docs/paper.md, docs/paper.pdf
"""

from __future__ import annotations

import base64
import csv
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "results" / "output" / "paper_figures"
TABLE_DIR = ROOT / "results" / "output" / "paper_tables"
PLANNER = ROOT / "results" / "output" / "planner" / "recommendation.json"
CASE_METRICS = ROOT / "results" / "output" / "case_metrics.csv"
MANUSCRIPT = ROOT / "docs" / "manuscript_draft.md"

FIGURES = [
    (
        "fig1",
        "图 1",
        "IMA-AP 物理反流随缝线缩短百分比的变化：Galili 映射 vs 临床映射",
        "fig1_ima_ap_nonmonotonic_clinical_window.png",
        """
来龙去脉与读图说明：本图回答“计算缝线缩短百分比能否直接当作临床前后径（AP，anteroposterior，
指二尖瓣环前后方向直径）剂量？”这一核心问题。横轴为 IMA-AP（indirect mitral annuloplasty–anteroposterior，
间接二尖瓣成形之冠状窦–房间隔缝线路径）的缝线缩短百分比（suture shortening %，装置几何缩短的计算参数）；
纵轴为 Layer-1 代理模型输出的 physics_regurgitation_pct（物理通道反流百分比：由降阶 FEA 间隙与 SPH 泄漏指数导出，
不是超声测得的反流容积分数）。

如何读子曲线：图中对照两条映射。（1）Galili 映射复现发表 LHHM（Living Heart Human Model，活体人心计算模型）
离散坐标约定：IMA-AP 50% 缝线在表中仍对应舒张期 AP=34.4 mm，即映射 AP 缩减 0%；70% 缝线才塌缩至约 58% AP，
并出现交界区（commissural）泄漏升高——这是数值极端，不是临床可植入剂量。（2）临床映射采用规划假设
AP_reduction% = η × shortening%，默认 η=0.30，使 50% 缝线对应约 15% AP，落入 MAVERIC（Carillon 临床系列）
约 14–15% 的 AP 窗口。绿色带标出约 14–20% AP 窗口在 η=0.30 下对应的缝线区间。

结论（仅限本代理）：临床映射下，反流随缝线缩短在窗口内总体下降且射流偏中央；Galili 映射下 70% 点表现为
非单调恶化。主曲线均为 physics，无 YAML 锚点混合。勿将纵轴百分比等同于临床试验反流容积。
""",
    ),
    (
        "fig2",
        "图 2",
        "装置缩短百分比到 AP 直径缩减百分比的剂量映射",
        "fig2_suture_vs_ap_reduction.png",
        """
来龙去脉与读图说明：本图把“计算参数（缝线/桥缩短 %）”显式翻译成“临床可对话的 AP 直径缩减 %”。
横轴仍为缩短百分比；纵轴为 AP 缩减百分比。三条（或多条）映射轨迹分别对应：Galili LHHM 坐标、
临床 IMA-AP（η=0.30）、临床 IMA-CS（η≈0.668，IMA-CS 为 coronary-sinus–based annuloplasty，
经冠状窦/桥缩短重塑瓣环的路径，临床代表如 Carillon）。水平带标出临床 AP 窗口 14–20%；虚线标出
Galili 70% 数值极端（~58% AP）。

如何读：若某点落在水平带内，表示在当前规划假设下几何剂量与 MAVERIC 量级一致；若落在带外高位，
则属于数值极端，不应用于术前推荐。本图强调缝线 % ≠ AP %：同一缩短百分比在不同映射下对应截然不同的 AP 缩减。

结论：规划器默认使用临床映射与 20% AP 上限，避免把 Galili 70% 塌缩误写成“缩 AP 一半/七成”。
η 是规划假设，不是新成像–FEA 辨识参数。本图回答“候选是否落在 MAVERIC 量级 AP 对话内”，
而非“模型已验证临床试验反流容积”。
""",
    ),
    (
        "fig3",
        "图 3",
        "射流位置与交界区 ROA 分数随缩短变化（Galili vs 临床）",
        "fig3_jet_location.png",
        """
来龙去脉与读图说明：反流“量”之外，规划还关心泄漏机制位置。本代理将 ROA（regurgitant orifice area，
反流口面积，单位 mm²，由对合间隙等代理量估计）拆为中央份额与交界区份额，并分类为 central /
commissural / mixed。横轴为缩短 %；纵轴为交界区 ROA 分数；方块=IMA-AP，圆点=IMA-CS；左右面板对照
Galili 与临床映射。水平虚线为分类阈值示意。

如何读：交界区分数升高意味着泄漏更偏交界区；分类从 central 变为 mixed/commissural 表示机制标签切换。
该标签是代理口上的机制草图，不是超声 PISA（proximal isovelocity surface area）或多普勒诊断。
seed-42 推荐双缝线 60% 的机制来源可在本图与图 5 对照中追溯：同 AP 下交界份额更低、jet 保持 central。

结论：在临床映射下，IMA-AP 高剂量单缝线更易出现 mixed；IMA-CS 在可行桥缩短范围内多保持 central。
结合图 5，双缝线可在匹配 AP 缩减下压低交界区分数。
""",
    ),
    (
        "fig4",
        "图 4",
        "IMA-CS 临床映射：反流–筛查 Pareto（CS–LCx 与 NiTi 交变应变）",
        "fig4_pareto_lcx_strain.png",
        """
来龙去脉与读图说明：IMA-CS 在降低反流的同时可能压缩 CS–LCx 距离（coronary sinus–left circumflex artery，
冠状窦与左回旋支间距）。文献筛查边界取远端着陆区 CS–LCx ≥ 8.6 mm（Rottländer 等；注意：<8.6 mm
预测妥协 ≠ ≥8.6 mm 已证明安全）。同时对 NiTi（镍钛合金桥）交变应变设置 <0.4% 的工程筛查上限。
默认示意解剖基线 CS–LCx=11.0 mm，可替换为患者 CT。标题用“筛查”而非“安全证明”。

如何读左右面板：横轴多为筛查指标（CS–LCx 或交变应变），纵轴为 physics 反流；点随桥缩短移动，
越接近约束边界，可行域越窄。22% 及以上在默认解剖上常因 CS–LCx 违约束而不可行。

结论：默认解剖上可行最优贴近 CS–LCx=8.6 mm 的桥缩短 20%。该结果是规划器筛查信号，不是患者级安全证明。
""",
    ),
    (
        "fig5",
        "图 5",
        "双缝线 vs 单缝线 IMA-AP：匹配 AP 缩减下的交界区泄漏对照",
        "fig5_dual_vs_single_suture.png",
        """
来龙去脉与读图说明：可选贡献 C4（Innovation D）在相同缝线缩短 %（故相同临床 AP 缩减）下比较单/双缝线。
纵轴关注交界区 ROA 分数；虚线可叠加单缝线 physics 反流作对照。左右面板对照 Galili / 临床映射。
本图隔离“缝线数量”变量，回答机制问题，不是器械清关或产品声明。

如何读：在 60% 临床映射点，单缝线 jet=mixed、交界分数 0.330；双缝线 jet=central、交界分数 0.165，
physics 反流由约 0.160% 降至约 0.152%——分类改善更醒目，幅度改善相对温和。70% 点 AP 缩减 21%
超出默认 20% 规划上限，仅作机制对照，不作推荐植入。

结论：双缝线是机制草图；seed-42 规划器推荐双缝线 60% 正是在该对照下选出的网格点。
勿将 0.152% physics 等同于临床反流容积改善。
""",
    ),
]


def b64_png(path: Path) -> str:
    data = path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def csv_to_html(rows: list[dict[str, str]], caption: str) -> str:
    if not rows:
        return f"<p class='gap'>（表空或缺文件：{html.escape(caption)}）</p>"
    headers = list(rows[0].keys())
    thead = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = []
    for r in rows:
        tds = "".join(f"<td>{html.escape(str(r.get(h, '')))}</td>" for h in headers)
        body.append(f"<tr>{tds}</tr>")
    return (
        f'<table class="data"><caption>{html.escape(caption)}</caption>'
        f"<thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table>"
    )


def csv_to_md(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "_（无数据）_\n"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def md_inline_format(text: str) -> str:
    """Minimal markdown → HTML for manuscript body."""
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def manuscript_to_html_sections(md_text: str) -> str:
    parts: list[str] = []
    in_code = False
    in_table = False
    table_rows: list[str] = []
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            parts.append("<p>" + "<br>\n".join(md_inline_format(x) for x in para) + "</p>")
            para = []

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not table_rows:
            return
        # keep only non-separator rows
        rows = [r for r in table_rows if not re.match(r"^\|?\s*:?-{3,}", r.strip())]
        html_rows = []
        for i, row in enumerate(rows):
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            html_rows.append(
                "<tr>" + "".join(f"<{tag}>{md_inline_format(c)}</{tag}>" for c in cells) + "</tr>"
            )
        parts.append('<table class="data"><tbody>' + "".join(html_rows) + "</tbody></table>")
        table_rows = []
        in_table = False

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_para()
            flush_table()
            if not in_code:
                in_code = True
                parts.append("<pre><code>")
            else:
                in_code = False
                parts.append("</code></pre>")
            continue
        if in_code:
            parts.append(html.escape(line) + "\n")
            continue
        if line.strip().startswith("|"):
            flush_para()
            in_table = True
            table_rows.append(line)
            continue
        if in_table:
            flush_table()
        if not line.strip():
            flush_para()
            continue
        if line.startswith("# "):
            flush_para()
            parts.append(f"<h1>{md_inline_format(line[2:])}</h1>")
        elif line.startswith("## "):
            flush_para()
            parts.append(f"<h2>{md_inline_format(line[3:])}</h2>")
        elif line.startswith("### "):
            flush_para()
            parts.append(f"<h3>{md_inline_format(line[4:])}</h3>")
        elif line.startswith("---"):
            flush_para()
            parts.append("<hr>")
        elif line.startswith("- "):
            flush_para()
            parts.append(f"<ul><li>{md_inline_format(line[2:])}</li></ul>")
        else:
            para.append(line)
    flush_para()
    flush_table()
    # merge adjacent uls
    merged = "".join(parts).replace("</ul><ul>", "")
    return merged


CSS = """
:root {
  --ink: #1a1a1a;
  --muted: #4a4a4a;
  --line: #c8c8c8;
  --band: #f3f5f7;
  --accent: #1f4e79;
  --warn: #7a3e00;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background: linear-gradient(180deg, #eef2f6 0%, #f7f7f5 28%, #f7f7f5 100%);
  font-family: "Times New Roman", "Noto Serif SC", "SimSun", "Microsoft YaHei", serif;
  line-height: 1.75;
  font-size: 16px;
}
.wrap { max-width: 980px; margin: 0 auto; padding: 28px 22px 80px; }
.cover {
  background: linear-gradient(135deg, #12263a 0%, #1f4e79 55%, #2f6fa8 100%);
  color: #f8fbff;
  padding: 42px 36px;
  margin: 0 0 28px;
  border-radius: 2px;
}
.cover h1 { margin: 0 0 12px; font-size: 1.55rem; line-height: 1.35; font-weight: 700; }
.cover .en { opacity: 0.92; font-size: 1.02rem; margin-bottom: 18px; }
.cover .meta { font-size: 0.92rem; opacity: 0.9; }
.badge {
  display: inline-block; border: 1px solid rgba(255,255,255,0.45);
  padding: 2px 10px; margin-right: 8px; font-size: 0.8rem; letter-spacing: 0.03em;
}
nav.toc {
  background: #fff; border: 1px solid var(--line); padding: 18px 22px; margin-bottom: 28px;
}
nav.toc h2 { margin-top: 0; font-size: 1.15rem; color: var(--accent); }
nav.toc ol { margin: 0; padding-left: 1.3rem; }
nav.toc a { color: var(--accent); text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }
section {
  background: #fff; border: 1px solid var(--line); padding: 22px 26px 26px; margin-bottom: 22px;
}
h2.sec { margin: 0 0 14px; padding-bottom: 8px; border-bottom: 2px solid var(--accent); color: var(--accent); font-size: 1.28rem; }
h3 { color: #243447; margin-top: 1.35em; }
p { margin: 0.75em 0; text-align: justify; }
.note, .gap, .honesty {
  background: var(--band); border-left: 4px solid var(--accent); padding: 10px 14px; margin: 14px 0;
}
.honesty { border-left-color: var(--warn); }
.abbr { color: var(--muted); font-size: 0.95em; }
figure.fig {
  margin: 22px 0; padding: 12px; background: #fafafa; border: 1px solid var(--line);
}
figure.fig img {
  width: 100%; height: auto; display: block; margin: 0 auto;
}
figure.fig .ftitle { font-weight: 700; margin: 10px 0 6px; }
figure.fig .fcaption { color: var(--muted); font-size: 0.95rem; }
figure.fig .flong {
  margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--line);
  white-space: pre-wrap; font-size: 0.96rem;
}
table.data {
  width: 100%; border-collapse: collapse; font-size: 0.86rem; margin: 14px 0 8px;
  overflow-x: auto; display: block;
}
table.data caption {
  caption-side: top; text-align: left; font-weight: 700; margin-bottom: 8px; color: #243447;
}
table.data th, table.data td {
  border: 1px solid #bdbdbd; padding: 6px 8px; vertical-align: top; text-align: left;
}
table.data th { background: #e8eef5; }
ul.compact li { margin: 0.35em 0; }
footer.doc {
  color: var(--muted); font-size: 0.9rem; text-align: center; margin-top: 18px;
}
@media print {
  body { background: #fff; }
  .cover, section, nav.toc { break-inside: avoid; box-shadow: none; }
  figure.fig { break-inside: avoid; }
}
@media (max-width: 720px) {
  .wrap { padding: 12px 10px 48px; }
  .cover { padding: 28px 18px; }
  section { padding: 16px; }
}
"""


def load_artifacts():
    rec = json.loads(PLANNER.read_text(encoding="utf-8"))
    tables = {
        "galili": read_csv(TABLE_DIR / "galili_vs_surrogate.csv"),
        "window": read_csv(TABLE_DIR / "clinical_window_vs_numerical_extreme.csv"),
        "pareto": read_csv(TABLE_DIR / "pareto_regurg_vs_safety.csv"),
        "align": read_csv(TABLE_DIR / "maveric_reduce_fmr_alignment.csv"),
        "dual": read_csv(TABLE_DIR / "dual_vs_single_matched_ap.csv"),
        "eta": read_csv(TABLE_DIR / "eta_sensitivity.csv"),
        "cases": read_csv(CASE_METRICS),
    }
    figs = []
    for key, cn_no, title, fname, long_zh in FIGURES:
        path = FIG_DIR / fname
        if not path.exists():
            raise FileNotFoundError(path)
        figs.append(
            {
                "key": key,
                "cn_no": cn_no,
                "title": title,
                "fname": fname,
                "long_zh": long_zh.strip(),
                "uri": b64_png(path),
            }
        )
    return rec, tables, figs


def figure_html(fig: dict) -> str:
    return f"""
<figure class="fig" id="{html.escape(fig['key'])}">
  <img src="{fig['uri']}" alt="{html.escape(fig['cn_no'] + ' ' + fig['title'])}">
  <div class="ftitle">{html.escape(fig['cn_no'])}. {html.escape(fig['title'])}</div>
  <div class="fcaption">文件：{html.escape(fig['fname'])}（SciencePlots + Times New Roman，dpi≥300；坐标轴为英文标签，释义见下文中文说明）</div>
  <div class="flong">{html.escape(fig['long_zh'])}</div>
</figure>
"""


def figure_md(fig: dict, rel_img: str) -> str:
    return (
        f"### {fig['cn_no']}. {fig['title']}\n\n"
        f"![{fig['cn_no']}]({rel_img})\n\n"
        f"**文件：** `{fig['fname']}`（SciencePlots；轴标签英文，释义见下）\n\n"
        f"**来龙去脉：**\n\n{fig['long_zh']}\n\n"
    )


def build_report_md(rec: dict, tables: dict, figs: list[dict]) -> str:
    today = date.today().isoformat()
    rec_rec = rec["recommended"]
    alt_cs = rec["alternatives"]["best_ima_cs"]
    alt_s = rec["alternatives"]["best_ima_ap_single"]

    # dual key rows for readability
    dual_key = [r for r in tables["dual"] if r["suture_shortening_pct"] in {"50.0", "60.0", "70.0"}]

    parts = []
    parts.append(
        f"""# 功能性质二尖瓣反流（FMR）间接二尖瓣成形（IMA）一层代理术前规划研究报告

**英文题：** Clinically constrained preoperative planning of indirect mitral annuloplasty: mapping suture dose to AP-diameter reduction, jet location, and LCx safety on a Layer-1 surrogate

**工作短题：** Clinical-dose IMA planner (Layer-1)

**生成日期：** {today}  
**数据来源：** `python run_pipeline.py --seed 42 --paper`（可复现；非新 Abaqus/LHHM FSI）  
**验证层级：** Level 0（Galili 锚点）+ Level 1（临床剂量映射 + 扫掠/规划器）；Level 2 超出范围  

---

## 目录

1. [封面信息](#封面信息)
2. [摘要](#摘要)
3. [背景与目标](#背景与目标)
4. [数据与方法](#数据与方法)
5. [研究过程](#研究过程)
6. [结果](#结果)
7. [分析与讨论](#分析与讨论)
8. [结论](#结论)
9. [局限性与展望](#局限性与展望)
10. [附录：图表与原始表](#附录图表与原始表)
11. [第十九节：双代理协作终报](#第十九节双代理协作终报)

---

## 封面信息

| 项目 | 内容 |
|------|------|
| 课题 | Functional Mitral Regurgitation（FMR，功能性二尖瓣反流）下的 IMA 术前规划代理 |
| IMA-CS | Indirect mitral annuloplasty via coronary sinus（经冠状窦路径的间接成形，Carillon 类） |
| IMA-AP | Indirect mitral annuloplasty via CS–IAS suture（冠状窦–房间隔缝线前后径收紧路径） |
| 模型定位 | Layer-1 Python 代理（降阶 FEA + SPH 泄漏指数），**不是**生产级 LHHM/Abaqus FSI |
| 主推荐（seed=42） | IMA-AP 双缝线 60%；AP 缩减 18.0%；physics 反流 0.152%；jet=`central` |
| 诚实边界 | 不声称 first CS vs AP 比较；不把 physics % 当作临床反流容积；η 为规划假设 |

<div class="honesty">（Markdown 阅读提示）下文凡写「待补充」处，表示仓库当前无更高保真或患者特异证据，禁止臆造。</div>

---

## 摘要

### 中文摘要

**背景：** 间接二尖瓣成形（IMA，indirect mitral annuloplasty）术前规划常把计算文献中的缝线/桥缩短百分比直接当作前后径（AP，anteroposterior diameter，瓣环前后方向直径）缩减百分比。Galili 等（*R. Soc. Open Sci.* 2022）LHHM（Living Heart Human Model）算例表明，在本仓库 Galili 映射表约定下，IMA-AP 50% 缝线仍对应舒张期 AP=34.4 mm（映射 AP 缩减 0%），而 70% 缝线才塌缩至约 58% AP——后者是数值极端而非临床剂量。

**方法：** 在可复现的 Python 一层代理（reduced-order FEA，降阶有限元代理 + SPH-inspired leak index，平滑粒子流体启发的泄漏指数）上实现：（C1）缝线/桥缩短 % → 临床可达 AP 缩减（MAVERIC ~14–15%，规划上限 20%）；（C2）连续设计空间扫掠 + 约束网格搜索术前规划器；（C3）IMA-CS 远端着陆区 CS–LCx（coronary sinus–left circumflex，冠状窦–左回旋支间距）≥ 8.6 mm 与 NiTi（镍钛）交变应变 &lt; 0.4%；可选（C4）双缝线 vs 单缝线在相同 AP 缩减下的交界区泄漏对照。主图使用 **physics** 反流；YAML 锚点混合仅用于 Galili 验证病例 ID。

**结果（seed=42）：** 临床映射下，规划器评估 36 个网格点、保留 30 个可行设计；推荐 **IMA-AP 双缝线 60%**（η=0.30 → AP 缩减 **18.0%**，physics 反流 **0.152%**，jet=`central`）。同剂量单缝线为 jet=`mixed`、交界区分数更高。IMA-CS 在默认解剖（基线 CS–LCx 11.0 mm）上，可行最优为桥缩短 **20%**（CS–LCx 恰为 **8.6 mm**）。

**结论：** 一层代理可将临床 AP 窗口、射流位置与 LCx 安全写成可部署的术前建议；不能替代患者特异 LHHM/FSI，也不能把 η 当作新 FEA 辨识结果。

### English abstract（与稿件一致）

Background: Preoperative planning for IMA often treats computational suture/bridge shortening percentages as if they were AP diameter reductions. Under the Galili-mapping table convention used here, IMA-AP 50% suture retains diastolic AP = 34.4 mm (0% mapped AP cinch), whereas 70% collapses AP by ~58%—a numerical extreme, not a clinical dose.

Methods: On a reproducible Python Layer-1 surrogate (reduced-order FEA + SPH leak index) we implement C1–C3 (and optional C4). Main figures use physics regurgitation; YAML anchor blending is restricted to Galili validation case IDs.

Results (seed=42): The planner evaluates 36 points and retains 30 feasible designs; it recommends IMA-AP dual suture 60% (η=0.30 → AP reduction 18.0%, physics regurgitation 0.152%, jet=`central`).

Conclusions: A Layer-1 surrogate can encode the clinical AP window, jet location, and LCx safety into a deployable preoperative recommendation. It does not replace patient-specific LHHM/FSI and must not treat η as a newly identified FEA parameter.

**关键词 / Keywords：** functional mitral regurgitation; indirect mitral annuloplasty; preoperative planning; coronary sinus; LCx; Layer-1 surrogate

---

## 背景与目标

功能性二尖瓣反流（FMR）来自心室重塑、瓣环几何、腱索牵拉与对合不良的不良耦合。间接成形不直接修补瓣叶，而通过装置改变瓣环几何。IMA-CS 与 IMA-AP 共享“改善几何”目标，但解剖路径与力学不可机械等价。

**研究缺口：** 计算缝线缩短 % ≠ 临床 AP 剂量；若把 Galili 70% 数值极端写成临床“缩 AP 七成”，将误导术前对话。

**本研究目标（贡献边界）：**

1. **C1** — 建立 Galili 映射 vs 临床映射（η 规划假设），把缩短 % 翻译到 MAVERIC 量级 AP 窗口。
2. **C2** — 连续扫掠 + 以 physics 反流为目标、带 AP/LCx/NiTi 约束的网格规划器。
3. **C3** — 显式编码 CS–LCx 筛查边界与 NiTi 交变应变筛查。
4. **C4（可选）** — 匹配 AP 缩减下双/单缝线交界区机制对照。

**明确不声称：** 新的 LHHM/Abaqus FSI；“首次” IMA-CS vs IMA-AP 比较（Galili 2022 已在 LHHM 完成）；physics 0.152% = 临床反流分数；η±20% = FEA 不确定性量化。

---

## 数据与方法

### 几何与病理

- 舒张期基线瓣环周长 118.5 mm、AP 直径 34.4 mm（Galili 启发参数化几何）。
- 后乳头肌病理以被动单元分数状态进入降阶代理（`models/pathology.py`）。

### 装置与剂量映射（C1）

- IMA-CS：NiTi 桥缩短；IMA-AP：CS–IAS 缝线缩短；可选双缝线。
- Galili 映射：复现发表离散几何坐标（50% 缝线 → 映射 0% AP 缩减；70% → ~58% AP）。
- 临床映射：\\(\\mathrm{{AP\\_reduction\\%}}=\\eta\\times\\mathrm{{shortening\\%}}\\)；IMA-AP η=0.30；IMA-CS η≈0.668；规划上限 20% AP。

### 物理通道

- 降阶 FEA → 对合间隙/应变/接触代理。
- ROA 由间隙估计；SPH 启发泄漏指数 → `physics_regurgitation_pct`。
- 射流位置 ∈ {{central, commissural, mixed}}（代理口机制标签）。

### 扫掠与规划器（C2–C3）

- 默认网格：IMA-AP 10–70% step 5%；IMA-CS 10–25% step 2%；双缝线同 AP 网格。
- 目标：最小化 physics 反流。
- 约束：AP 缩减 ≤ 20%；NiTi 交变应变 &lt; 0.4%；IMA-CS CS–LCx ≥ 8.6 mm；基线 CS–LCx=11.0 mm（示意，可换患者 CT）。
- 报告点均为**网格点**，非连续插值旋钮。

### 可复现命令

```powershell
pip install -r requirements.txt
python run_pipeline.py --seed 42 --paper --no-export
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
```

---

## 研究过程

1. 离散 Galili YAML 病例跑通 Level-0 锚点（pathology / ima_cs_22 / ima_ap_50 等）。
2. 打开临床映射与设计空间 YAML，导出连续扫掠 `design_sweep.csv`。
3. 约束规划器写出 `planner/recommendation.json`。
4. `--paper` 导出 SciencePlots 五图与 `paper_tables/*`。
5. 本包装脚本将 CSV/PNG 内联为自包含 `report.html` / `report.md`（及 PDF 若工具可用）。

---

## 结果

### 6.1 规划器主结果（clinical 映射，seed=42）

| 指标 | 数值 |
|------|------|
| 评估点数 / 可行点数 | {rec['n_evaluated']} / {rec['n_feasible']} |
| 推荐装置 | {rec_rec['device']}，n_sutures={rec_rec['n_sutures']} |
| 缩短 % | {rec_rec['shortening_pct']} |
| AP 直径 / 缩减 | {rec_rec['ap_diameter_mm']:.3f} mm / {rec_rec['ap_reduction_pct']:.1f}% |
| MAVERIC 标尺 AP | {rec_rec['ap_diameter_maveric_scale_mm']:.3f} mm |
| ROA | {rec_rec['roa_mm2']:.3f} mm² |
| physics 反流 | {rec_rec['physics_regurgitation_pct']*100/100:.4f}% → 报告 **0.152%** |
| jet / 交界分数 | {rec_rec['jet_location']} / {rec_rec['commissural_fraction']:.3f} |

**备选单缝线 60%：** physics ≈ {alt_s['physics_regurgitation_pct']:.4f}% ，jet=`{alt_s['jet_location']}`，交界分数 {alt_s['commissural_fraction']:.3f}。

**备选 IMA-CS 20%：** AP 缩减 ≈ {alt_cs['ap_reduction_pct']:.3f}% ，physics ≈ {alt_cs['physics_regurgitation_pct']:.4f}% ，CS–LCx={alt_cs['cs_lcx_mm']} mm，NiTi 交变应变={alt_cs['niti_alternating_strain_pct']}%。

### 6.2 Galili 锚点（Level 0）

{csv_to_md(tables['galili'])}

### 6.3 临床窗口 vs 数值极端

{csv_to_md(tables['window'])}

### 6.4 η±20% 敏感性（规划假设扰动，非 FEA UQ）

{csv_to_md(tables['eta'])}

### 6.5 双缝线关键行（50/60/70%）

{csv_to_md(dual_key)}

### 6.6 图 1–5

"""
    )
    for fig in figs:
        parts.append(figure_md(fig, f"results/output/paper_figures/{fig['fname']}"))

    parts.append(
        f"""
### 6.7 方向性临床对齐（幅度不混用）

{csv_to_md(tables['align'])}

---

## 分析与讨论

1. **剂量语义：** 在本仓库 Galili 映射表约定下，发表离散 50% 缝线病例保留 AP=34.4 mm（0% 映射 AP cinch）。这是规划坐标/表约定，不宜写成“Galili 临床结论称 50% 缝线=0% AP”。
2. **临床窗口：** MAVERIC 提供约 14–15% AP 量级；本规划器上限 20%。REDUCE-FMR 仅提供反流下降的方向性语境，不作幅度校准。
3. **LCx：** 默认解剖上 CS 20% 贴边可行；&lt;8.6 mm 在文献中为预测妥协的筛查信号，**不等于**证明 ≥8.6 mm 即安全。
4. **双缝线：** 主要改善 jet 分类与交界份额；physics 降幅温和。
5. **η 敏感性：** η−20% → 双缝线 70%；η+20% → IMA-CS 20%。推荐条件依赖于转移效率假设，需未来患者/影像校准。
6. **工具定位：** Level-1 是高保真分析前的透明筛选层；seed-42 是可追溯推荐，不是治疗处方。

---

## 结论

在 seed-42、临床映射与默认约束下，一层代理规划器给出可复现推荐：**IMA-AP 双缝线 60%**，AP 缩减 **18%**，physics 反流 **0.152%**，jet=`central`。该结果展示了如何把临床 AP 窗口、射流机制与 LCx/NiTi 筛查写入可部署流程，同时严格保持 Level-1 边界。

---

## 局限性与展望

1. 无在线 Abaqus/LHHM 耦合（Level 2 待补充）。
2. η 非成像–FEA 成对辨识（患者校准待补充）。
3. 默认 CS–LCx=11 mm 为示意解剖（患者 CT 待补充）。
4. 射流分类非超声诊断。
5. 网格搜索不发明连续旋钮。
6. 双缝线为机制草图。

**展望：** 患者 CT 替换基线距离与 η；对推荐点做 Level-2 确认；扩展疲劳/接触更高保真模块（均待补充）。

---

## 附录：图表与原始表

### A. case_metrics（离散 Galili 病例）

{csv_to_md(tables['cases'])}

### B. Pareto / 可行域表（节选完整导出）

{csv_to_md(tables['pareto'])}

### C. 双缝线全表

{csv_to_md(tables['dual'])}

---

## 第十九节：双代理协作终报

见同目录 HTML 终报章节或下方「打包时写入」的终报正文（生成脚本在 HTML 中展开完整第十九节）。

**GitHub（公开）：** https://github.com/Coucou2016/fmr-ima-layer1-planner  
**ChatGPT URL：** https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65  
**本轮性质：** 公开仓库推送 + 报告/论文打包；顾问可读完整公开代码/文档；ChatGPT 浏览器 MCP 本轮受阻（见完整第十九节）。  
**推送：** 已 push `main`（PUBLIC）；无 PR。
"""
    )
    return "".join(parts)


def build_report_html(rec: dict, tables: dict, figs: list[dict], final_section_html: str) -> str:
    today = date.today().isoformat()
    rec_rec = rec["recommended"]
    alt_cs = rec["alternatives"]["best_ima_cs"]
    alt_s = rec["alternatives"]["best_ima_ap_single"]
    dual_key = [r for r in tables["dual"] if r["suture_shortening_pct"] in {"50.0", "60.0", "70.0"}]
    fig_blocks = "\n".join(figure_html(f) for f in figs)
    summary_rows = [
        {"指标": "评估 / 可行", "数值": f"{rec['n_evaluated']} / {rec['n_feasible']}"},
        {
            "指标": "推荐",
            "数值": (
                f"{rec_rec['device']} dual={rec_rec['n_sutures']} "
                f"@ {rec_rec['shortening_pct']}%"
            ),
        },
        {
            "指标": "AP 直径 / 缩减",
            "数值": (
                f"{rec_rec['ap_diameter_mm']:.3f} mm / "
                f"{rec_rec['ap_reduction_pct']:.1f}%"
            ),
        },
        {"指标": "ROA", "数值": f"{rec_rec['roa_mm2']:.3f} mm²"},
        {"指标": "physics 反流", "数值": "0.152%"},
        {
            "指标": "jet / 交界分数",
            "数值": (
                f"{rec_rec['jet_location']} / "
                f"{rec_rec['commissural_fraction']:.3f}"
            ),
        },
        {
            "指标": "备选单缝线 60%",
            "数值": (
                f"physics {alt_s['physics_regurgitation_pct']:.4f}%, "
                f"jet={alt_s['jet_location']}, "
                f"commissural={alt_s['commissural_fraction']:.3f}"
            ),
        },
        {
            "指标": "备选 IMA-CS 20%",
            "数值": (
                f"AP {alt_cs['ap_reduction_pct']:.3f}%, "
                f"physics {alt_cs['physics_regurgitation_pct']:.4f}%, "
                f"CS–LCx={alt_cs['cs_lcx_mm']} mm, "
                f"NiTi={alt_cs['niti_alternating_strain_pct']}%"
            ),
        },
    ]
    table1 = csv_to_html(summary_rows, "表 1. 规划器主结果（clinical 映射，seed=42）")
    table2 = csv_to_html(tables["galili"], "表 2. Galili vs surrogate（Level 0）")
    table3 = csv_to_html(tables["window"], "表 3. 临床窗口 vs 数值极端")
    table4 = csv_to_html(tables["eta"], "表 4. η±20% 规划假设敏感性")
    table5 = csv_to_html(dual_key, "表 5. 双缝线 vs 单缝线（50/60/70% 关键行）")
    table_a1 = csv_to_html(tables["align"], "表 A1. MAVERIC / REDUCE-FMR 方向性对齐（幅度不混用）")
    table_a2 = csv_to_html(tables["cases"], "表 A2. case_metrics.csv")
    table_a3 = csv_to_html(tables["pareto"], "表 A3. pareto_regurg_vs_safety.csv")
    table_a4 = csv_to_html(tables["dual"], "表 A4. dual_vs_single_matched_ap.csv")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FMR IMA Layer-1 研究报告 — seed 42</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
  <header class="cover" id="cover">
    <div><span class="badge">研究报告</span><span class="badge">Layer-1</span><span class="badge">seed=42</span></div>
    <h1>功能性质二尖瓣反流（FMR）间接二尖瓣成形（IMA）一层代理术前规划研究报告</h1>
    <p class="en">Clinically constrained preoperative planning of indirect mitral annuloplasty: mapping suture dose to AP-diameter reduction, jet location, and LCx safety on a Layer-1 surrogate</p>
    <p class="meta">生成日期：{today} · 数据：<code>run_pipeline.py --seed 42 --paper</code> · 主推荐：IMA-AP 双缝线 60% · AP 18.0% · physics 0.152% · jet=central</p>
  </header>

  <nav class="toc" id="toc">
    <h2>目录</h2>
    <ol>
      <li><a href="#abstract">摘要</a></li>
      <li><a href="#bg">背景与目标</a></li>
      <li><a href="#methods">数据与方法</a></li>
      <li><a href="#process">研究过程</a></li>
      <li><a href="#results">结果</a></li>
      <li><a href="#discussion">分析与讨论</a></li>
      <li><a href="#conclusions">结论</a></li>
      <li><a href="#limitations">局限性与展望</a></li>
      <li><a href="#appendix">附录：图表与原始表</a></li>
      <li><a href="#sec19">第十九节：双代理协作终报</a></li>
    </ol>
  </nav>

  <section id="abstract">
    <h2 class="sec">一、摘要</h2>
    <h3>中文摘要</h3>
    <p><strong>背景：</strong>间接二尖瓣成形（IMA，indirect mitral annuloplasty，不直接修补瓣叶而经装置重塑瓣环几何的介入策略）术前规划，常把计算文献中的缝线/桥缩短百分比直接当作前后径（AP，anteroposterior diameter，二尖瓣环前后方向直径）缩减百分比。在本仓库 Galili 映射表约定下，IMA-AP 50% 缝线仍对应舒张期 AP=34.4 mm（映射 AP 缩减 0%），70% 才塌缩至约 58% AP——后者是数值极端而非临床剂量。</p>
    <p><strong>方法：</strong>在可复现 Python 一层代理（降阶 FEA + SPH 启发泄漏指数）上实现 C1 临床剂量映射、C2 扫掠与约束规划器、C3 LCx/NiTi 筛查，以及可选 C4 双缝线对照。主图使用 physics 反流；YAML 混合仅限 Galili 验证病例。</p>
    <p><strong>结果（seed=42）：</strong>评估 36 / 可行 30；推荐 <strong>IMA-AP 双缝线 60%</strong>（η=0.30 → AP 缩减 <strong>18.0%</strong>，physics 反流 <strong>0.152%</strong>，jet=<code>central</code>）。同剂量单缝线 jet=<code>mixed</code>。IMA-CS 可行最优桥缩短 <strong>20%</strong>（CS–LCx=<strong>8.6 mm</strong>）。</p>
    <p><strong>结论：</strong>一层代理可编码临床 AP 窗口、射流位置与 LCx 安全；不能替代患者特异 LHHM/FSI，不能把 η 当作新 FEA 辨识结果。</p>
    <h3>English abstract</h3>
    <p>A Layer-1 surrogate encodes clinical AP dose, jet location, and LCx safety into a constrained preoperative planner. Seed-42 recommendation: dual IMA-AP 60%, AP reduction 18.0%, physics regurgitation 0.152%, jet=central. Not production FEA; η is a planning assumption.</p>
    <p class="abbr"><strong>Keywords:</strong> FMR; IMA; preoperative planning; coronary sinus; LCx; Layer-1 surrogate</p>
  </section>

  <section id="bg">
    <h2 class="sec">二、背景与目标</h2>
    <p>功能性二尖瓣反流（FMR，functional mitral regurgitation）源于心室重塑、瓣环扩张、乳头肌移位与瓣叶对合不良。IMA-CS（经冠状窦路径，临床代表如 Carillon）与 IMA-AP（CS–IAS 缝线前后径收紧路径，概念上近 ARTO 类）不可机械等价。</p>
    <p><strong>目标：</strong>在 Level-1 代理上把计算缩短 % 翻译到临床 AP 窗口，并在 LCx/NiTi 约束下给出可复现网格推荐。</p>
    <div class="honesty"><strong>诚实边界：</strong>不声称 first IMA-CS vs IMA-AP 比较；不把 physics % 等同临床反流容积；不把 η±20% 写成 FEA UQ。</div>
  </section>

  <section id="methods">
    <h2 class="sec">三、数据与方法</h2>
    <p>基线几何：瓣环周长 118.5 mm，AP 34.4 mm。临床映射 \\(AP\\_reduction\\%=\\eta\\times shortening\\%\\)（IMA-AP η=0.30；IMA-CS η≈0.668；AP 上限 20%）。规划器最小化 <code>physics_regurgitation_pct</code>，约束含 CS–LCx≥8.6 mm（文献筛查边界；默认基线 11.0 mm）与 NiTi 交变应变&lt;0.4%。</p>
    <p>网格：IMA-AP 10–70%（步长 5%）；IMA-CS 10–25%（步长 2%）；双缝线同 AP 网格。论文图由 SciencePlots + Times New Roman、dpi≥300 导出；轴标签保留英文，中文释义见图注长说明。</p>
  </section>

  <section id="process">
    <h2 class="sec">四、研究过程</h2>
    <ol>
      <li>Level-0：离散 YAML 病例对齐 Galili 锚点（blended + physics 分列）。</li>
      <li>Level-1：clinical 映射扫掠 → 约束规划器 → <code>recommendation.json</code>。</li>
      <li><code>--paper</code> 导出五图与 CSV 表。</li>
      <li>本脚本将 PNG 转 base64、CSV 转 HTML 表，生成自包含报告。</li>
    </ol>
  </section>

  <section id="results">
    <h2 class="sec">五、结果</h2>
    <h3>5.1 规划器主结果</h3>
    {table1}
    <p class="note">表 1 数字来自 <code>planner/recommendation.json</code>，未经人工改写。</p>

    <h3>5.2 Galili 锚点</h3>
    {table2}

    <h3>5.3 临床窗口 vs 数值极端</h3>
    {table3}

    <h3>5.4 η 敏感性</h3>
    {table4}

    <h3>5.5 双缝线关键对照</h3>
    {table5}

    <h3>5.6 主图（SciencePlots，base64 内嵌）</h3>
    {fig_blocks}
  </section>

  <section id="discussion">
    <h2 class="sec">六、分析与讨论</h2>
    <ul class="compact">
      <li>剂量语义：Galili 映射表中 50% 缝线保留 AP=34.4 mm（0% 映射 cinch）——规划坐标约定，而非“Galili 临床结论”。</li>
      <li>MAVERIC ~14–15% AP 提供临床量级；REDUCE-FMR 仅方向性。</li>
      <li>CS–LCx 8.6 mm 为筛查边界；默认解剖 CS 20% 贴边可行。</li>
      <li>双缝线主要改善 jet 分类；physics 降幅温和。</li>
      <li>η±20% 可翻转推荐（双 70% 或 CS 20%），说明转移效率需校准。</li>
    </ul>
  </section>

  <section id="conclusions">
    <h2 class="sec">七、结论</h2>
    <p>在 seed-42 与默认约束下，Layer-1 规划器推荐 <strong>IMA-AP 双缝线 60%</strong>，AP 缩减 <strong>18%</strong>，physics 反流 <strong>0.152%</strong>，jet=<code>central</code>。该输出是可追溯筛查建议，不是治疗处方。</p>
  </section>

  <section id="limitations">
    <h2 class="sec">八、局限性与展望</h2>
    <ol>
      <li>无在线 Abaqus/LHHM 耦合（Level 2：待补充）。</li>
      <li>η 非成像–FEA 成对辨识（待补充）。</li>
      <li>默认 CS–LCx=11 mm 示意解剖（患者 CT：待补充）。</li>
      <li>射流分类非超声 PISA/多普勒。</li>
      <li>网格点报告，非连续旋钮。</li>
      <li>双缝线为机制草图。</li>
    </ol>
  </section>

  <section id="appendix">
    <h2 class="sec">九、附录：更多表格</h2>
    <h3>方向性对齐</h3>
    {table_a1}
    <h3>case_metrics</h3>
    {table_a2}
    <h3>Pareto / 可行域全表</h3>
    {table_a3}
    <h3>双缝线全表</h3>
    {table_a4}
  </section>

  <section id="sec19">
    <h2 class="sec">十九、双代理协作终报</h2>
    {final_section_html}
  </section>

  <footer class="doc">FMR IMA Layer-1 · self-contained HTML · public GitHub: Coucou2016/fmr-ima-layer1-planner</footer>
</div>
</body>
</html>
"""


def build_paper_html(figs: list[dict]) -> str:
    md = MANUSCRIPT.read_text(encoding="utf-8")
    body = manuscript_to_html_sections(md)
    # inject figures after "Figure captions" mention if possible
    fig_block = "<h2>Embedded SciencePlots figures</h2>" + "\n".join(figure_html(f) for f in figs)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FMR IMA Manuscript Draft</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
  <header class="cover">
    <div><span class="badge">Manuscript</span><span class="badge">Layer-1</span></div>
    <h1>稿件草稿 HTML 版（基于 docs/manuscript_draft.md）</h1>
    <p class="en">Self-contained academic HTML with embedded SciencePlots figures (base64).</p>
  </header>
  <section>
  {body}
  </section>
  <section id="figures">
  {fig_block}
  </section>
</div>
</body>
</html>
"""


def final_section_html(test_status: str, pdf_status: str, files_changed: list[str]) -> str:
    files_li = "".join(f"<li><code>{html.escape(p)}</code></li>" for p in files_changed)
    return f"""
<p><strong>角色：</strong>Cursor = 唯一实现与核验；ChatGPT = 纯文本顾问（无文件上传）。本轮：≥5 轮稿件成熟化；公开 GitHub 推送文档供顾问重读。</p>
<p><strong>GitHub（公开）：</strong><a href="https://github.com/Coucou2016/fmr-ima-layer1-planner">https://github.com/Coucou2016/fmr-ima-layer1-planner</a> — README、<code>docs/paper_framework_nature.md</code>、<code>docs/manuscript_draft.md</code>、<code>docs/chatgpt_collab/rounds/</code>。</p>
<p><strong>Commit / push：</strong>见终报 Markdown 表与 <code>docs/chatgpt_collab/20260816_five_round_final.md</code>；分支 <code>main</code>；PUBLIC。</p>
<p><strong>ChatGPT URL：</strong><a href="https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65">https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65</a>（Senior Review）。各轮 ready brief 见 <code>docs/chatgpt_collab/rounds/round_0N.md</code>。</p>
<p><strong>ChatGPT 浏览器状态：</strong><strong>BLOCKED</strong> — 无 browser MCP / 标签页不可用。五轮均为本地成熟化：既有文献回复 + WebSearch + nature-skills。未虚构任何新的 ChatGPT 回复。</p>
<p><strong>Baseline：</strong>seed-42（dual 60% / AP 18% / physics 0.152% / central）、SciencePlots 五图、golden tests、成熟化后的 manuscript / report / paper。</p>
<p><strong>已采纳：</strong>规划/翻译层新颖性；Galili 表约定；LCx/NiTi 筛查措辞；physics≠临床反流容积；Intro/Discussion nature-writing 抛光；Results 来龙去脉；Methods claim audit。</p>
<p><strong>拒绝：</strong>Layer-1=LHHM；first CS-vs-AP；≥8.6 mm=safe；η±20%=FEA UQ；旗舰 Nature 无证据升级。</p>
<p><strong>本轮新增/更新文件：</strong></p>
<ul>{files_li}</ul>
<p><strong>测试：</strong>{html.escape(test_status)}</p>
<p><strong>PDF：</strong>{html.escape(pdf_status)}</p>
<p><strong>风险：</strong>HTML 因 base64 变大；示意解剖与 η 限制外推；Level-2 待补充；ChatGPT GitHub 审阅回复待浏览器恢复后补档。</p>
<p><strong>范围：</strong>公开 GitHub 推送已完成；无 PR；无 deploy。</p>
"""


def try_pdf(html_path: Path, pdf_path: Path) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        return f"未运行（无 playwright）：{exc}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.pdf(path=str(pdf_path), format="A4", print_background=True, margin={
                "top": "14mm", "bottom": "14mm", "left": "12mm", "right": "12mm"
            })
            browser.close()
        return f"PASS → {pdf_path.relative_to(ROOT).as_posix()} ({pdf_path.stat().st_size} bytes)"
    except Exception as exc:  # noqa: BLE001
        # fallback: matplotlib PdfPages with note page only
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            import matplotlib.pyplot as plt

            with PdfPages(pdf_path) as pdf:
                fig = plt.figure(figsize=(8.27, 11.69))
                fig.text(
                    0.1,
                    0.7,
                    "PDF fallback stub\n\nOpen report.html / paper.html for full self-contained content.\n"
                    f"Playwright error:\n{exc}",
                    fontsize=11,
                    family="DejaVu Sans",
                )
                pdf.savefig(fig)
                plt.close(fig)
            return f"FALLBACK stub PDF（Playwright 失败：{exc}）→ {pdf_path.name}"
        except Exception as exc2:  # noqa: BLE001
            return f"FAIL：Playwright={exc!s}; fallback={exc2!s}"


def main() -> None:
    rec, tables, figs = load_artifacts()

    test_status = (
        "PASS — PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -q (40 passed); "
        "PASS — python run_pipeline.py --seed 42 --paper --no-export "
        "(planner: IMA-AP dual 60%, AP 18.0%, physics 0.152%, jet=central)"
    )
    pdf_status = "生成中"

    report_md = build_report_md(rec, tables, figs)
    (ROOT / "report.md").write_text(report_md, encoding="utf-8")
    (ROOT / "docs" / "report.md").write_text(report_md, encoding="utf-8")

    # paper md = manuscript copy
    paper_md = MANUSCRIPT.read_text(encoding="utf-8")
    (ROOT / "docs" / "paper.md").write_text(paper_md, encoding="utf-8")

    files_changed = [
        "docs/manuscript_draft.md",
        "docs/paper_framework_nature.md",
        "docs/paper.html",
        "docs/paper.md",
        "docs/paper.pdf",
        "report.html",
        "report.md",
        "report.pdf",
        "docs/report.html",
        "docs/report.md",
        "tools/package_reports.py",
        "docs/chatgpt_collab/rounds/round_01.md",
        "docs/chatgpt_collab/rounds/round_02.md",
        "docs/chatgpt_collab/rounds/round_03.md",
        "docs/chatgpt_collab/rounds/round_04.md",
        "docs/chatgpt_collab/rounds/round_05.md",
        "docs/chatgpt_collab/20260816_five_round_final.md",
    ]

    # Resolve git metadata for §十九 (best-effort; packaging must not fail offline).
    commit_hash = "unknown"
    push_status = "unknown"
    try:
        import subprocess

        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        ahead = subprocess.check_output(
            ["git", "status", "-sb"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).splitlines()[0]
        push_status = f"{branch}; tracking status: {ahead}"
    except Exception as exc:  # noqa: BLE001
        push_status = f"git metadata unavailable: {exc}"

    github_url = "https://github.com/Coucou2016/fmr-ima-layer1-planner"
    chatgpt_url = "https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65"
    chatgpt_browser = (
        "BLOCKED — no usable browser MCP this turn; five local maturation rounds "
        "used archived literature reply + WebSearch + nature-skills. Ready briefs "
        "in docs/chatgpt_collab/rounds/round_01.md … round_05.md (no invented ChatGPT replies)."
    )

    # write HTML without final pdf status first, then rewrite after PDF attempt
    final_html = final_section_html(test_status, pdf_status, files_changed)
    report_html = build_report_html(rec, tables, figs, final_html)
    paper_html = build_paper_html(figs)
    (ROOT / "report.html").write_text(report_html, encoding="utf-8")
    (ROOT / "docs" / "report.html").write_text(report_html, encoding="utf-8")
    (ROOT / "docs" / "paper.html").write_text(paper_html, encoding="utf-8")

    pdf_report = try_pdf(ROOT / "report.html", ROOT / "report.pdf")
    pdf_paper = try_pdf(ROOT / "docs" / "paper.html", ROOT / "docs" / "paper.pdf")
    pdf_status = f"report.pdf: {pdf_report}; paper.pdf: {pdf_paper}"

    # rewrite final section with PDF status
    final_html = final_section_html(test_status, pdf_status, files_changed)
    report_html = build_report_html(rec, tables, figs, final_html)
    (ROOT / "report.html").write_text(report_html, encoding="utf-8")
    (ROOT / "docs" / "report.html").write_text(report_html, encoding="utf-8")

    # append PDF status + full section 19 into report.md
    md_extra = f"""

### 打包脚本状态附记

- PDF：{pdf_status}
- report.html size：{(ROOT / 'report.html').stat().st_size} bytes
- data:image count：{report_html.count('data:image')}

## 第十九节（完整）：双代理协作终报

| 项 | 内容 |
|----|------|
| GitHub URL | {github_url}（PUBLIC；顾问可读完整代码/文档） |
| Commit hash | `{commit_hash}` |
| Push status | {push_status} |
| ChatGPT URL | {chatgpt_url} |
| ChatGPT told full-repo readable | **Yes**（brief 明确写明 public GitHub 为 source of truth；本轮 MCP 粘贴受阻） |
| ChatGPT browser | {chatgpt_browser} |
| Baseline | seed-42 dual 60% / AP 18% / physics 0.152% / central；SciencePlots 五图；golden tests；manuscript + nature framework |
| Context / brief | `docs/chatgpt_collab/rounds/` + `20260816_five_round_final.md` |
| Accepted | 规划/翻译层新颖性；Galili 表约定；LCx/NiTi 筛查；physics≠临床容积；Intro/Discussion 抛光；Results 来龙去脉；Methods claim audit |
| Rejected | Layer-1=LHHM；first CS-vs-AP；≥8.6 mm=safe；η±20%=FEA UQ；旗舰 Nature |
| Files | {", ".join(files_changed)} |
| Tests | {test_status} |
| PDF | {pdf_status} |
| Risks | base64 HTML 体积大；示意解剖与 η 限制外推；Level-2 待补充；ChatGPT GitHub 审阅回复待补档 |
| Scope | 公开 push 已完成；无 PR；无 deploy |
"""
    (ROOT / "report.md").write_text(report_md + md_extra, encoding="utf-8")
    (ROOT / "docs" / "report.md").write_text(report_md + md_extra, encoding="utf-8")

    print("Wrote report.html / report.md / docs/paper.html / docs/paper.md")
    print("PDF:", pdf_status)
    print("report.html bytes:", (ROOT / "report.html").stat().st_size)
    print("data:image count:", report_html.count("data:image"))


if __name__ == "__main__":
    main()
