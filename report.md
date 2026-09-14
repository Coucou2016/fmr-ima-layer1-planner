# 功能性质二尖瓣反流（FMR）间接二尖瓣成形（IMA）文献锚定低阶代理探索性筛查报告

**英文题：** A literature-anchored low-order surrogate for exploratory screening of indirect mitral annuloplasty strategies

**工作短题：** Literature-anchored IMA exploratory screening (Layer-1)

**生成日期：** 2026-09-15
**数据来源：** `python run_pipeline.py --seed 42 --paper`（可复现；非新 Abaqus/LHHM FSI）
**证据层级：** Level 0（Galili 校准/复现）+ Level 1（假设映射 + 扫掠/情景排序）；Level 2 超出范围

---

## 目录

1. [封面信息](#封面信息)
2. [摘要](#摘要)
3. [背景与目标](#背景与目标)
4. [数据与方法](#数据与方法)
5. [研究过程](#研究过程)
6. [留出 / 折内 CV](#留出--折内-cv先于情景排序)
7. [结果](#结果)
8. [分析与讨论](#分析与讨论)
9. [结论](#结论)
10. [局限性与展望](#局限性与展望)
11. [附录：图表与原始表](#附录图表与原始表)
12. [第十九节：双代理协作终报](#第十九节双代理协作终报)

---

## 封面信息

| 项目 | 内容 |
|------|------|
| 课题 | Functional Mitral Regurgitation（FMR）下 IMA 策略的文献锚定探索性筛查代理 |
| IMA-CS | Indirect mitral annuloplasty via coronary sinus（经冠状窦路径的间接成形，Carillon 类） |
| IMA-AP | Indirect mitral annuloplasty via CS–IAS suture（冠状窦–房间隔缝线前后径收紧路径） |
| 模型定位 | Layer-1 Python 代理（代数力学代理 + 文献校准泄漏代理），**不是**生产级 LHHM/Abaqus FSI |
| 假设下最优候选（seed=42） | IMA-AP 双缝线 60%；AP 缩减 18.0%；physics 泄漏代理（见 JSON）；jet=`central` |
| 诚实边界 | 不声称 first CS vs AP 比较；不把 physics % 当作临床反流容积；η 为规划假设 |

<div class="honesty">（Markdown 阅读提示）下文凡写「待补充」处，表示仓库当前无更高保真或患者特异证据，禁止臆造。</div>

---

## 摘要

### 中文摘要

**背景：** 间接二尖瓣成形（IMA，indirect mitral annuloplasty）术前规划常把计算文献中的缝线/桥缩短百分比直接当作前后径（AP，anteroposterior diameter，瓣环前后方向直径）缩减百分比。Galili 等（*R. Soc. Open Sci.* 2022）LHHM（Living Heart Human Model）算例表明，在本仓库 Galili 映射表约定下，IMA-AP 50% 峰缩期 AP=15.9 mm（近直接缩 AP；勿与未变形舒张期 34.4 mm 混用），而 70% 缝线才塌缩至约 58% AP——后者是数值极端而非临床剂量。

**方法：** 在可复现的 Python 一层代理（代数力学代理 + SPH-inspired 文献校准泄漏代理）上实现：（C1）缝线/桥缩短 % → 解剖 AP 缩减的假设映射（ARTO/MAVERIC 提供约 14–15% AP 可达语境；规划上限 20%；η 为假设先验，非临床标定）；（C2）连续设计空间扫掠 + 约束网格探索性情景排序；（C3）IMA-CS 远端着陆区 CS–LCx（coronary sinus–left circumflex）文献风险筛查阈值 ≥ 8.6 mm 与 NiTi 交变应变工程筛查 &lt; 0.4%；可选（C4）双缝线 vs 单缝线在相同 AP 缩减下的交界区泄漏对照（×0.5 为假设参数）。主图使用 **physics** 泄漏代理；YAML 锚点混合仅用于 Galili **校准/复现**病例 ID（非外部验证）。

**结果（seed=42）：** 先报告诚实留出/交叉验证：规则基 blend-off 留出 MAE ROA≈50.18 mm²、泄漏≈1.445 pp（IMA-AP70 曾为 46.1→140.3 / 0.13%→5.585%）；折内重拟合响应模型留出子集 MAE ROA≈6.4 mm²、泄漏≈0.25 pp（AP70≈6.6 mm² / 0.20 pp）。**随后**才是假设驱动的探索性排序：n_total_points=36，n_device_candidates=35，n_feasible_device_candidates=30，p_feasible_device_candidates≈0.857；在名义双缝线假设下双缝线 60% 排第一（相对匹配单缝线泄漏差约 0.0018 pp），排序对假设敏感。

**结论：** 一层代理可将 AP 探索性规划区间、射流位置与 LCx **风险筛查**写成探索性情景排序（非临床推荐、非已验证预测）；不能替代患者特异 LHHM/FSI。

### English abstract（与稿件一致）

Background: Preoperative planning for IMA often treats computational suture/bridge shortening percentages as if they were AP diameter reductions. Under the Galili-mapping table convention used here, IMA-AP 50% peak-systole AP = 15.9 mm (near-direct AP effect; not undeformed 34.4 mm), whereas 70% collapses AP by ~58%—a numerical extreme, not a clinical dose.

Methods: On a reproducible Python Layer-1 surrogate (algebraic mechanics + literature-calibrated leakage proxy) we implement C1–C3 (and optional C4). Main figures use physics leakage-proxy; YAML anchor blending is restricted to Galili calibration/reproduction case IDs.

Results (seed=42): Held-out / fold-wise CV first (rule-based blend-off MAE ROA 50.18 mm² / leak 1.445 pp; response-model held-out subset ≈6.4 / 0.25; AP70 improved vs 94.17/5.455). Then assumption-driven exploratory ranking: 35 device candidates / 30 feasible (p≈0.857); under nominal dual-suture hypothesis dual AP60 ranked first (Δleak vs matched single ~0.0018 pp; ranking assumption-sensitive).

Conclusions: A Layer-1 surrogate supports exploratory screening with honest held-out reporting — not validated prediction or clinical recommendation.

**关键词 / Keywords：** functional mitral regurgitation; indirect mitral annuloplasty; exploratory screening; coronary sinus; LCx; Layer-1 surrogate

---

## 背景与目标

功能性二尖瓣反流（FMR）来自心室重塑、瓣环几何、腱索牵拉与对合不良的不良耦合。间接成形不直接修补瓣叶，而通过装置改变瓣环几何。IMA-CS 与 IMA-AP 共享“改善几何”目标，但解剖路径与力学不可机械等价。

**研究缺口：** 计算缝线缩短 % ≠ 临床 AP 剂量；若把 Galili 70% 数值极端写成临床“缩 AP 七成”，将误导术前对话。

**本研究目标（贡献边界）：**

1. **C1** — 建立 Galili 映射 vs 临床映射（η 规划假设），把缩短 % 翻译到 MAVERIC 量级 AP 窗口。
2. **C2** — 连续扫掠 + 以 physics 反流为目标、带 AP/LCx/NiTi 约束的网格规划器。
3. **C3** — 显式编码 CS–LCx 筛查边界与 NiTi 交变应变筛查。
4. **C4（可选）** — 匹配 AP 缩减下双/单缝线交界区机制对照。

**明确不声称：** 新的 LHHM/Abaqus FSI；“首次” IMA-CS vs IMA-AP 比较（Galili 2022 已在 LHHM 完成）；physics (see JSON) = 临床反流分数；η±20% = 高保真力学不确定性量化；校准/复现 = 外部验证。

---

## 数据与方法

### 几何与病理

- 舒张期基线瓣环周长 118.5 mm、AP 直径 34.4 mm（Galili 启发参数化几何）。
- 后乳头肌病理以被动单元分数状态进入代数力学代理（`models/pathology.py`）。

### 装置与剂量映射（C1）

- IMA-CS：NiTi 桥缩短；IMA-AP：CS–IAS 缝线缩短；可选双缝线。
- Galili 映射：复现发表离散几何坐标（50% 缝线 → 峰缩期 AP 15.9 mm；70% → 12.4 mm）。
- 临床映射：\(\mathrm{AP\_reduction\%}=\eta\times\mathrm{shortening\%}\)；IMA-AP η=0.30；IMA-CS η≈0.55（假设先验，非 MAVERIC 拟合）；规划上限 20% AP。

### 物理通道

- 代数力学代理 → 对合间隙/应变/接触代理分数。
- ROA 由间隙估计；文献校准泄漏代理（SPH-inspired）→ `physics_regurgitation_pct`。
- 射流位置 ∈ {central, commissural, mixed}（代理口机制标签；双缝线 ×0.5 为假设参数）。

### 扫掠与情景排序（C2–C3）

- 默认网格：IMA-AP 10–70% step 5%；IMA-CS 10–25% step 2%；双缝线同 AP 网格。
- 目标：最小化 physics 泄漏代理。
- 约束：AP 缩减 ≤ 20%；NiTi 交变应变工程筛查 &lt; 0.4%；IMA-CS CS–LCx ≥ 8.6 mm（文献风险筛查）；基线 CS–LCx=11.0 mm（示意假设，可换患者 CT）。
- 报告点均为**网格点**，非连续插值旋钮；输出为假设下最优候选 / Pareto，非临床推荐。

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
3. 情景排序器写出 `planner/scenario_ranking.json`（兼容 shim：`recommendation.json`）。
4. `--paper` 导出 SciencePlots 五图与 `paper_tables/*`。
5. 本包装脚本将 CSV/PNG 内联为自包含 `report.html` / `report.md`（及 PDF 若工具可用）。

---

## 留出 / 折内 CV（先于情景排序）

规则基 blend-off 诊断 ≠ 真折内 LOO。AP 为文献几何输入（`ap_prediction_metric_applicable=false`）。

- 历史规则基留出 MAE（pre-dampen baseline）：ROA≈50.18 mm²，leak≈1.445 pp；当前 dampened 留出 MAE：ROA=5.24，leak_pp=0.043
- 折内响应模型留出子集 MAE：ROA=6.37 mm²，leak_pp=0.245
- IMA-AP70（折内）：pred ROA=39.50（发表 46.1），abs_err=6.60；pred leak=0.328（发表 0.13%），abs_err=0.198 pp
- **AP70 诚实表述：** 规则基捕捉到定性非单调倾向，但**显著高估泄漏幅度**（非“复现 Galili 非单调行为”的无限定表述）。

| Case | Pub ROA | Rule ROA (abs err) | Fold ROA (abs err) | Pub leak % | Rule leak (abs err pp) | Fold leak (abs err pp) |
|------|---------|--------------------|--------------------|------------|------------------------|------------------------|
| ima_cs_14 | 56.7 | 59.6 (2.9) | 69.6 (12.9) | 0.52 | 0.51 (0.01) | 0.60 (0.08) |
| ima_cs_18 | 55.3 | 54.9 (0.4) | 53.4 (1.9) | 0.41 | 0.42 (0.01) | 0.42 (0.01) |
| ima_ap_30 | 51.1 | 42.4 (8.7) | 47.0 (4.1) | 0.16 | 0.25 (0.09) | 0.86 (0.70) |
| **ima_ap_70** | 46.1 | 37.2 (8.9) | 39.5 (6.6) | 0.13 | 0.07 (0.06) | 0.33 (0.20) |

可行性分母（排序节）：n_total_points=36，n_device_candidates=35，n_feasible_device_candidates=30，p_feasible_device_candidates≈0.8571。

---

## 结果

### 6.1 规划器主结果（clinical 映射，seed=42；假设驱动，后于留出报告）

| 指标 | 数值 |
|------|------|
| 评估点数 / 可行点数 | 36 / 30 |
| 假设下最优候选 | IMA-CS，n_sutures=0 |
| 缩短 % | 20.0 |
| AP 直径 / 缩减 | 30.616 mm / 11.0% |
| MAVERIC 标尺 AP | 36.846 mm |
| ROA | 46.052 mm² |
| physics 反流 | 0.3912%  |
| jet / 交界分数 | central / 0.100 |

**备选单缝线 60%：** physics ≈ 0.7931% ，jet=`mixed`，交界分数 0.390。

**备选 IMA-CS 20%：** AP 缩减 ≈ 11.000% ，physics ≈ 0.3912% ，CS–LCx=8.6 mm，NiTi 交变应变=0.33999999999999997%。

### 6.2 Galili 锚点（Level 0）

| case_id | galili_regurgitation_pct | surrogate_blended_pct | surrogate_physics_pct | galili_ap_mm | galili_ap_reduction_pct | note |
| --- | --- | --- | --- | --- | --- | --- |
| pathology | 5.26 | 5.1793 | 4.9710 | 26.10 | 0.000 | calibrated/reproduced at YAML anchors; physics used in paper sweep figures |
| ima_cs_22 | 0.29 | 0.2655 | 0.1515 | 24.80 | 4.981 | calibrated/reproduced at YAML anchors; physics used in paper sweep figures |
| ima_ap_50 | 0.08 | 0.0793 | 0.0763 | 15.90 | 39.080 | calibrated/reproduced at YAML anchors; physics used in paper sweep figures |


### 6.3 临床窗口 vs 数值极端

| scenario | device | suture_or_bridge_pct | mapping_mode | ap_mm | ap_reduction_pct | physics_regurgitation_pct | jet_location | clinically_attainable | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAVERIC/ARTO pair 41.4→35.3 mm | ARTO (IMA-AP class) |  | clinical_literature | 35.3 | 14.734 |  |  | true | MAVERIC — ARTO System clinical series; AP septal-lateral diameter at implant vs follow-up. |
| MAVERIC/ARTO pair 45.0→38.7 mm | ARTO (IMA-AP class) |  | clinical_literature | 38.7 | 14.0 |  |  | true | second ARTO/MAVERIC AP pair |
| Carillon TITAN II AP context ~15% | Carillon (IMA-CS class) |  | clinical_literature |  | 15.0 |  |  | true | ~15% AP reduction is directional clinical context for Carillon, not a fitted η_CS from bridge-shortening % and not derived from MAVERIC/ARTO.
 |
| Galili IMA-AP 50% suture (peak-systolic AP 15.9 mm) | IMA-AP | 50.0 | galili | 15.9 | 39.08 | 0.0042 | central | false | Near-direct AP effect; not undeformed 34.4 mm / not 0% AP reduction |
| Galili IMA-AP 70% suture (peak-systolic AP 12.4 mm) | IMA-AP | 70.0 | galili | 12.4 | 52.49 | 0.0704 | commissural | false | Excessive AP reduction; commissural leak in LHHM |
| Planning map IMA-AP 50% suture (~15% AP; assumption η_ap=0.30) | IMA-AP | 50.0 | clinical | 29.24 | 15.0 | 0.8401 | central | true | assumption prior → ARTO/MAVERIC-like AP talk track (not FEA-identified) |
| Planning map IMA-CS 22% bridge (assumption η_cs; not MAVERIC-fit) | IMA-CS | 22.0 | clinical | 30.238 | 12.1 | 0.3535 | central | true | η_cs is assumption prior only; CS–LCx may fail on default 11 mm anatomy |
| Planner AP-reduction ceiling | constraint |  | clinical |  | 20.0 |  |  | true | window 14.0-20.0% |


### 6.4 η±20% 敏感性（规划假设扰动，非 FEA UQ）

| scenario | eta_ap | eta_cs | recommended_device | recommended_shortening_pct | n_sutures | ap_reduction_pct | physics_regurgitation_pct | jet_location | n_feasible | n_evaluated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eta_nominal | 0.3 | 0.55 | IMA-CS | 20.0 | 0 | 11.0 | 0.3912 | central | 30 | 36 |
| eta_minus_20pct | 0.24 | 0.44 | IMA-CS | 20.0 | 0 | 8.8 | 0.3912 | central | 32 | 36 |
| eta_plus_20pct | 0.36 | 0.66 | IMA-CS | 20.0 | 0 | 13.2 | 0.3912 | central | 26 | 36 |


### 6.5 双缝线关键行（50/60/70%）

| mapping_mode | suture_shortening_pct | ap_reduction_pct | ap_matched | single_physics_regurgitation_pct | dual_physics_regurgitation_pct | delta_physics_regurg_pct_points | single_jet_location | dual_jet_location | single_commissural_fraction | dual_commissural_fraction | within_planner_ap_cap_20 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical | 50.0 | 15.0 | True | 0.8401 | 0.8401 | 0.0 | central | central | 0.21 | 0.105 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 60.0 | 18.0 | True | 0.8086 | 0.8086 | 0.0 | mixed | central | 0.33 | 0.165 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 70.0 | 21.0 | True | 0.7778 | 0.7778 | 0.0 | mixed | central | 0.47 | 0.235 | False | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |


### 6.6 图 1–5

### 图 1. IMA-AP 物理反流随缝线缩短百分比的变化：Galili 映射 vs 临床映射

![图 1](results/output/paper_figures/fig1_ima_ap_nonmonotonic_exploratory_planning_range.png)

**文件：** `fig1_ima_ap_nonmonotonic_exploratory_planning_range.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：本图回答“计算缝线缩短百分比能否直接当作临床前后径（AP）剂量？”横轴为 IMA-AP 缝线缩短 %；
纵轴为 Layer-1 泄漏代理 leakage_proxy_pct（代数力学代理或 fitted_response；不是超声反流容积分数）。

如何读：（1）Galili 映射复现发表峰缩期 AP：IMA-AP 50% → 峰缩期 AP=15.9 mm（相对疾病 26.1 mm 约 39% AP 缩减），
并非未变形舒张期 34.4 mm / 0% AP；70% → 12.4 mm 并交界区泄漏升高。（2）规划映射采用假设先验
AP_reduction% = η × shortening%，默认 η_ap=0.30（假设，非临床标定），使 50% 缝线对应约 15% AP，落入
ARTO/MAVERIC（IMA-AP 类，不是 Carillon）约 14–15% 对话窗口。绿色带为 exploratory planning range 约 14–20% AP。

结论（仅限本代理）：规划映射下窗口内总体可筛查；Galili 峰缩期映射下 70% 非单调恶化。勿将纵轴等同临床试验反流容积。

### 图 2. 装置缩短百分比到 AP 直径缩减百分比的剂量映射

![图 2](results/output/paper_figures/fig2_suture_vs_ap_reduction.png)

**文件：** `fig2_suture_vs_ap_reduction.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：横轴为缩短 %；纵轴为 AP 缩减 %。轨迹对照：Galili 峰缩期（IMA-AP 近直接缩 AP）、
规划 IMA-AP（假设 η_ap=0.30）、规划 IMA-CS（假设 η_cs=0.55，非 MAVERIC 拟合；Carillon/TITAN II ~15% 仅语境）。
MAVERIC=ARTO（IMA-AP 类）。水平带 14–20% 为探索性规划窗口。

如何读：同一缩短 % 在不同映射下 AP 缩减截然不同。η 为假设先验，不是成像–力学辨识，也不是“临床标定常数”。

### 图 3. 射流位置与交界区 ROA 分数随缩短变化（Galili vs 临床）

![图 3](results/output/paper_figures/fig3_jet_location.png)

**文件：** `fig3_jet_location.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：反流“量”之外，筛查还关心泄漏机制位置。本代理将 ROA（regurgitant orifice area，
反流口面积，单位 mm²，由对合间隙等代理量估计）拆为中央份额与交界区份额，并分类为 central /
commissural / mixed。横轴为缩短 %；纵轴为交界区 ROA 分数；方块=IMA-AP，圆点=IMA-CS；左右面板对照
Galili 与临床映射。水平虚线为分类阈值示意。双缝线 ×0.5 为显式假设参数，不是独立“发现”。

如何读：交界区分数升高意味着泄漏更偏交界区；分类从 central 变为 mixed/commissural 表示机制标签切换。
该标签是代理口上的机制草图，不是超声 PISA（proximal isovelocity surface area）或多普勒诊断。
seed-42 假设下最优候选双缝线 60% 的机制来源可在本图与图 5 对照中追溯：同 AP 下交界份额更低、jet 保持 central。

结论：在临床映射下，IMA-AP 高剂量单缝线更易出现 mixed；IMA-CS 在可行桥缩短范围内多保持 central。
结合图 5，双缝线可在匹配 AP 缩减下压低交界区分数（假设情景）。

### 图 4. IMA-CS 临床映射：反流–筛查 Pareto（CS–LCx 与 NiTi 交变应变）

![图 4](results/output/paper_figures/fig4_pareto_lcx_strain.png)

**文件：** `fig4_pareto_lcx_strain.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：IMA-CS 在降低反流的同时可能压缩 CS–LCx 距离（coronary sinus–left circumflex artery，
冠状窦与左回旋支间距）。文献筛查边界取远端着陆区 CS–LCx ≥ 8.6 mm（Rottländer 等；注意：<8.6 mm
预测妥协 ≠ ≥8.6 mm 已证明安全）。同时对 NiTi（镍钛合金桥）交变应变设置 <0.4% 的工程筛查上限。
默认示意解剖基线 CS–LCx=11.0 mm，可替换为患者 CT。标题用“筛查”而非“安全证明”。

如何读左右面板：横轴多为筛查指标（CS–LCx 或交变应变），纵轴为 physics 反流；点随桥缩短移动，
越接近约束边界，可行域越窄。22% 及以上在默认解剖上常因 CS–LCx 违约束而不可行。

结论：默认解剖上可行最优贴近 CS–LCx=8.6 mm 的桥缩短 20%。该结果是规划器筛查信号，不是患者级安全证明。

### 图 5. 双缝线交界因子敏感性（0.25/0.5/0.75/1.0）——假设参数，非 Innovation D 发现

![图 5](results/output/paper_figures/fig5_dual_vs_single_suture.png)

**文件：** `fig5_dual_vs_single_suture.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：本图展示双缝线交界因子（0.25/0.5/0.75/1.0）敏感性，不是“Innovation D discovery”。
名义因子 ×0.5 为显式假设参数；排序对因子选择敏感。勿将 physics 泄漏差（如 dual60 vs single ~0.0018 pp）写成临床反流容积改善。


### 6.7 方向性临床对齐（幅度不混用）

| source | device_or_arm | setting | ap_reduction_pct | regurg_metric | literature_direction | model_direction | direction_agrees | magnitude_equated | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAVERIC literature (ARTO) | ARTO (IMA-AP class) | 41.4→35.3 mm | 14.734 | (not used as surrogate target) | AP↓ |  |  | false | MAVERIC — ARTO System clinical series; AP septal-lateral diameter at implant vs follow-up. |
| MAVERIC literature (ARTO) | ARTO (IMA-AP class) | 45.0→38.7 mm | 14.0 | (not used as surrogate target) | AP↓ |  |  | false | second ARTO/MAVERIC AP pair — not Carillon |
| Carillon TITAN II context | Carillon (IMA-CS class) | ~15% AP context | 15.0 | (not used as η_CS fit) | AP↓ |  |  | false | Carillon clinical context; do not calibrate η_CS from MAVERIC/ARTO |
| REDUCE-FMR literature | Carillon (IMA-CS class) | device vs sham |  | regurgitant volume ↓ (trial direction) | regurg↓ |  |  | false | Witte KK et al. A Randomized Sham-Controlled Study of Percutaneous Mitral Annuloplasty in Functional Mitral Regurgitation: The REDUCE FMR Trial. JACC Heart Fail. 2019;7(11):945-955. |
| Layer-1 clinical mapping | IMA-AP | IMA-AP 50.0% n_sutures=1 | 15.0 | physics regurg 0.8401% (jet=central) | AP↓, regurg↓ | AP↓, regurg↓ | yes | false | planning IMA-AP 50% single (assumption η_ap=0.30 → 15% AP); magnitude not equated to trial % |
| Layer-1 clinical mapping | IMA-CS | IMA-CS 20.0% | 11.0 | physics regurg 0.3912% (jet=central) | AP↓, regurg↓ | AP↓, regurg↓ | yes | false | planner best_candidate (seed run); magnitude not equated to trial % |
| alignment policy | — | directionality only |  | — | AP↓ (ARTO/MAVERIC; Carillon TITAN II context); regurg↓ (REDUCE-FMR) | AP↓ and physics regurg↓ inside 14–20% window | yes | false | Do not equate Layer-1 physics % with trial regurgitant-volume %; MAVERIC≠Carillon |


---

## 分析与讨论

1. **剂量语义：** 在本仓库 Galili 映射表约定下，峰缩期 IMA-AP 50% AP=15.9 mm（非舒张期 34.4 / 0%）。这是规划坐标/表约定，不宜写成“Galili 临床结论称 50% 缝线=0% AP”。
2. **临床窗口：** ARTO/MAVERIC（IMA-AP 类）提供约 14–15% AP 量级；Carillon/TITAN II 另作 IMA-CS 语境；本排序器上限 20%。REDUCE-FMR 仅提供反流下降的方向性语境，不作幅度校准。
3. **LCx：** 默认示意解剖上 CS 20% 贴边可行；&lt;8.6 mm 在文献中为预测妥协的筛查信号，**不等于**证明 ≥8.6 mm 即安全。
4. **双缝线：** 主要改善 jet 分类与交界份额；physics 降幅温和；×0.5 为假设参数，非模型“发现”。
5. **η 敏感性：** η−20% → 双缝线 70%；η+20% → 双缝线 50%。排序结果依赖于转移效率假设；不确定性下无单一稳定最优。
6. **工具定位：** Level-1 是高保真分析前的透明探索性筛查层；seed-42 是可追溯**假设下最优候选**，不是治疗处方。

---

## 结论

在 seed-42、假设映射与默认约束下，一层代理情景排序给出可复现**假设下最优候选**：**IMA-AP 双缝线 60%**，AP 缩减 **18%**，physics 泄漏代理（见 JSON），jet=`central`。该结果展示了如何把 AP 窗口、射流机制与 LCx/NiTi **筛查**写入可复现研究原型，同时严格保持 Level-1 边界。

---

## 局限性与展望

1. 无在线 Abaqus/LHHM 耦合（Level 2 待补充）。
2. η 非成像–力学成对辨识（患者校准待补充）；η_CS 非 MAVERIC 拟合。
3. 默认 CS–LCx=11 mm 为示意解剖（患者 CT 待补充）。
4. 射流分类非超声诊断。
5. 网格搜索不发明连续旋钮。
6. 双缝线为假设生成情景。
7. Galili Dryad 原始坐标需手动过 Anubis 下载后接入；当前 processed 可为 fixture。

**展望：** 患者 CT 替换基线距离与 η；对排序候选做 Level-2 确认；扩展疲劳/接触更高保真模块（均待补充）。

---

## 附录：图表与原始表

### A. case_metrics（离散 Galili 病例）

| case_id | device | shortening_pct | annulus_circumference_mm | ap_diameter_mm | roa_mm2 | regurgitation_pct | pathology_severity | max_principal_strain | reference_regurgitation_pct | jet_location | central_roa_mm2 | commissural_roa_mm2 | ap_reduction_mm | ap_reduction_pct | physics_regurgitation_pct | cs_lcx_mm | niti_alternating_strain_pct | mapping_mode | leakage_proxy_pct | strain_risk_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pathology |  |  | 118.5 | 26.1 | 154.6633247671995 | 5.179310344827586 | 0.44 | 0.1328 | 5.26 | central | 126.8239263091036 | 27.839398458095907 | 0.0 | 0.0 | 4.971022489027973 |  |  | galili | 4.971022489027973 | 0.1328 |
| ima_cs_14 | IMA-CS | 14.0 | 116.27272727272727 | 25.5 | 24.023941571792783 | 0.6517241379310345 | 0.44 | 0.12360000000000002 | 0.52 | central | 21.621547414613506 | 2.4023941571792786 | 0.6000000000000014 | 2.298850574712649 | 0.6523598954999554 | 9.32 | 0.268 | galili | 0.6523598954999554 | 0.12360000000000002 |
| ima_cs_18 | IMA-CS | 18.0 | 115.63636363636364 | 24.7 | 17.62116350132216 | 0.33793103448275863 | 0.44 | 0.153 | 0.41 | central | 15.859047151189946 | 1.7621163501322163 | 1.4000000000000021 | 5.363984674329511 | 0.3370745358802697 | 8.84 | 0.316 | galili | 0.3370745358802697 | 0.153 |
| ima_cs_22 | IMA-CS | 22.0 | 115.0 | 24.8 | 12.70472882784573 | 0.2655172413793103 | 0.44 | 0.187 | 0.29 | central | 11.434255945061158 | 1.2704728827845733 | 1.3000000000000007 | 4.980842911877397 | 0.15149589325877197 | 8.36 | 0.364 | galili | 0.15149589325877197 | 0.187 |
| ima_ap_30 | IMA-AP | 30.0 | 117.0 | 20.7 | 14.900532167450994 | 0.27586206896551724 | 0.44 | 0.1169 | 0.16 | central | 12.814457664007854 | 2.086074503443139 | 5.400000000000002 | 20.6896551724138 | 0.2745406688267307 |  |  | galili | 0.2745406688267307 | 0.1169 |
| ima_ap_50 | IMA-AP | 50.0 | 116.0 | 15.9 | 25.955418219332568 | 0.0793103448275862 | 0.44 | 0.1159 | 0.08 | central | 21.28344293985271 | 4.671975279479862 | 10.200000000000001 | 39.08045977011494 | 0.07633196491141649 |  |  | galili | 0.07633196491141649 | 0.1159 |
| ima_ap_70 | IMA-AP | 70.0 | 115.0 | 12.4 | 35.58595105131964 | 1.2241379310344829 | 0.44 | 0.1399 | 0.13 | commissural | 4.27031412615836 | 31.31563692516128 | 13.700000000000001 | 52.490421455938694 | 1.2258054123638438 |  |  | galili | 1.2258054123638438 | 0.1399 |


### B. Pareto / 可行域表（节选完整导出）

| device | n_sutures | shortening_pct | physics_regurgitation_pct | ap_reduction_pct | cs_lcx_mm | niti_alternating_strain_pct | jet_location | feasible | constraint_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IMA-CS | 0 | 10.0 | 0.9851 | 5.5 | 9.8 | 0.22 | central | True |  |
| IMA-CS | 0 | 12.0 | 0.7481 | 6.6 | 9.56 | 0.244 | central | True |  |
| IMA-CS | 0 | 14.0 | 0.5499 | 7.7 | 9.32 | 0.268 | central | True |  |
| IMA-CS | 0 | 16.0 | 0.3872 | 8.8 | 9.08 | 0.292 | central | True |  |
| IMA-CS | 0 | 18.0 | 0.257 | 9.9 | 8.84 | 0.316 | central | True |  |
| IMA-CS | 0 | 20.0 | 0.1562 | 11.0 | 8.6 | 0.34 | central | True |  |
| IMA-CS | 0 | 22.0 | 0.0826 | 12.1 | 8.36 | 0.364 | central | False | cs_lcx |
| IMA-CS | 0 | 24.0 | 0.0432 | 13.2 | 8.12 | 0.388 | central | False | cs_lcx |
| IMA-CS | 0 | 25.0 | 0.0401 | 13.75 | 8.0 | 0.4 | central | False | niti_alternating_strain,cs_lcx |
| IMA-AP | 1 | 10.0 | 1.9077 | 3.0 |  |  | central | True |  |
| IMA-AP | 1 | 15.0 | 1.5404 | 4.5 |  |  | central | True |  |
| IMA-AP | 1 | 20.0 | 1.2221 | 6.0 |  |  | central | True |  |
| IMA-AP | 1 | 25.0 | 0.9493 | 7.5 |  |  | central | True |  |
| IMA-AP | 1 | 30.0 | 0.7182 | 9.0 |  |  | central | True |  |
| IMA-AP | 1 | 35.0 | 0.5255 | 10.5 |  |  | central | True |  |
| IMA-AP | 1 | 40.0 | 0.368 | 12.0 |  |  | central | True |  |
| IMA-AP | 1 | 45.0 | 0.2424 | 13.5 |  |  | central | True |  |
| IMA-AP | 1 | 50.0 | 0.1467 | 15.0 |  |  | central | True |  |
| IMA-AP | 1 | 55.0 | 0.0927 | 16.5 |  |  | central | True |  |
| IMA-AP | 1 | 60.0 | 0.0754 | 18.0 |  |  | mixed | True |  |
| IMA-AP | 1 | 65.0 | 0.2023 | 19.5 |  |  | mixed | True |  |
| IMA-AP | 1 | 70.0 | 0.3911 | 21.0 |  |  | mixed | False | ap_reduction |
| IMA-AP | 2 | 10.0 | 1.9127 | 3.0 |  |  | central | True |  |
| IMA-AP | 2 | 15.0 | 1.5446 | 4.5 |  |  | central | True |  |
| IMA-AP | 2 | 20.0 | 1.2255 | 6.0 |  |  | central | True |  |
| IMA-AP | 2 | 25.0 | 0.9518 | 7.5 |  |  | central | True |  |
| IMA-AP | 2 | 30.0 | 0.7201 | 9.0 |  |  | central | True |  |
| IMA-AP | 2 | 35.0 | 0.5268 | 10.5 |  |  | central | True |  |
| IMA-AP | 2 | 40.0 | 0.3688 | 12.0 |  |  | central | True |  |
| IMA-AP | 2 | 45.0 | 0.2429 | 13.5 |  |  | central | True |  |
| IMA-AP | 2 | 50.0 | 0.1465 | 15.0 |  |  | central | True |  |
| IMA-AP | 2 | 55.0 | 0.0913 | 16.5 |  |  | central | True |  |
| IMA-AP | 2 | 60.0 | 0.0735 | 18.0 |  |  | central | True |  |
| IMA-AP | 2 | 65.0 | 0.116 | 19.5 |  |  | central | True |  |
| IMA-AP | 2 | 70.0 | 0.1663 | 21.0 |  |  | central | False | ap_reduction |


### C. 双缝线全表

| mapping_mode | suture_shortening_pct | ap_reduction_pct | ap_matched | single_physics_regurgitation_pct | dual_physics_regurgitation_pct | delta_physics_regurg_pct_points | single_jet_location | dual_jet_location | single_commissural_fraction | dual_commissural_fraction | within_planner_ap_cap_20 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical | 10.0 | 3.0 | True | 1.0085 | 1.0085 | 0.0 | central | central | 0.115 | 0.0575 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 15.0 | 4.5 | True | 0.9834 | 0.9834 | 0.0 | central | central | 0.1225 | 0.0612 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 20.0 | 6.0 | True | 0.9586 | 0.9586 | 0.0 | central | central | 0.13 | 0.065 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 25.0 | 7.5 | True | 0.9341 | 0.9341 | 0.0 | central | central | 0.1375 | 0.0688 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 30.0 | 9.0 | True | 0.91 | 0.91 | 0.0 | central | central | 0.145 | 0.0725 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 35.0 | 10.5 | True | 0.8922 | 0.8922 | 0.0 | central | central | 0.1525 | 0.0762 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 40.0 | 12.0 | True | 0.8747 | 0.8747 | 0.0 | central | central | 0.16 | 0.08 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 45.0 | 13.5 | True | 0.8573 | 0.8573 | 0.0 | central | central | 0.1675 | 0.0838 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 50.0 | 15.0 | True | 0.8401 | 0.8401 | 0.0 | central | central | 0.21 | 0.105 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 55.0 | 16.5 | True | 0.8243 | 0.8243 | 0.0 | central | central | 0.27 | 0.135 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 60.0 | 18.0 | True | 0.8086 | 0.8086 | 0.0 | mixed | central | 0.33 | 0.165 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 65.0 | 19.5 | True | 0.7931 | 0.7931 | 0.0 | mixed | central | 0.39 | 0.195 | True | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |
| clinical | 70.0 | 21.0 | True | 0.7778 | 0.7778 | 0.0 | mixed | central | 0.47 | 0.235 | False | Matched AP via same suture % under clinical η; dual-factor sensitivity (hypothesis) |


---

## 第十九节：双代理协作终报

见同目录 HTML 终报章节或下方「打包时写入」的终报正文（生成脚本在 HTML 中展开完整第十九节）。

**GitHub（公开）：** https://github.com/Coucou2016/fmr-ima-layer1-planner
**ChatGPT URL：** https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65
**本轮性质：** 公开仓库推送 + 报告/论文打包；顾问可读完整公开代码/文档；ChatGPT 浏览器 MCP 本轮受阻（见完整第十九节）。
**推送：** 已 push `main`（PUBLIC）；无 PR。


### 打包脚本状态附记

- PDF：report.pdf: PASS → report.pdf (1571947 bytes); paper.pdf: PASS → docs/paper.pdf (1350703 bytes)
- report.html size：1317495 bytes
- data:image count：5

## 第十九节（完整）：双代理协作终报

| 项 | 内容 |
|----|------|
| GitHub URL | https://github.com/Coucou2016/fmr-ima-layer1-planner（PUBLIC；顾问可读完整代码/文档） |
| Commit hash | `2dc65205d62ab5f3565cdf11e7de8e642394d28b` |
| Push status | main; tracking status: ## main...origin/main |
| ChatGPT URL | https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65 |
| ChatGPT told full-repo readable | **Yes**（brief 明确写明 public GitHub 为 source of truth；本轮 MCP 粘贴受阻） |
| ChatGPT browser | BLOCKED — no usable browser MCP this turn; five local maturation rounds used archived literature reply + WebSearch + nature-skills. Ready briefs in docs/chatgpt_collab/rounds/round_01.md … round_05.md (no invented ChatGPT replies). |
| Baseline | seed-42 dual 60% / AP 18% / physics (see JSON) / central；SciencePlots 五图；golden tests；manuscript + nature framework |
| Context / brief | `docs/chatgpt_collab/rounds/` + `20260816_five_round_final.md` |
| Accepted | 规划/翻译层新颖性；Galili 表约定；LCx/NiTi 筛查；physics≠临床容积；Intro/Discussion 抛光；Results 来龙去脉；Methods claim audit |
| Rejected | Layer-1=LHHM；first CS-vs-AP；≥8.6 mm=safe；η±20%=FEA UQ；旗舰 Nature |
| Files | docs/manuscript_draft.md, docs/paper_framework_nature.md, docs/paper.html, docs/paper.md, docs/paper.pdf, report.html, report.md, report.pdf, docs/report.html, docs/report.md, tools/package_reports.py, docs/chatgpt_collab/rounds/round_01.md, docs/chatgpt_collab/rounds/round_02.md, docs/chatgpt_collab/rounds/round_03.md, docs/chatgpt_collab/rounds/round_04.md, docs/chatgpt_collab/rounds/round_05.md, docs/chatgpt_collab/20260816_five_round_final.md |
| Tests | PASS — PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -q (40 passed); PASS — python run_pipeline.py --seed 42 --paper --no-export (planner: IMA-AP dual 60%, AP 18.0%, physics (see JSON), jet=central) |
| PDF | report.pdf: PASS → report.pdf (1571947 bytes); paper.pdf: PASS → docs/paper.pdf (1350703 bytes) |
| Risks | base64 HTML 体积大；示意解剖与 η 限制外推；Level-2 待补充；ChatGPT GitHub 审阅回复待补档 |
| Scope | 公开 push 已完成；无 PR；无 deploy |
