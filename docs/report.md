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
| 假设下最优候选（seed=42） | IMA-CS 20.0%（n_sutures=0）；AP↓ 11.0%；leakage_proxy≈0.3912%；jet=`central`；response_path=`fitted_response` |
| 诚实边界 | 不声称 first CS vs AP 比较；不把 physics % 当作临床反流容积；η 为规划假设 |

<div class="honesty">（Markdown 阅读提示）下文凡写「待补充」处，表示仓库当前无更高保真或患者特异证据，禁止臆造。</div>

---

## 摘要

### 中文摘要

**背景：** 间接二尖瓣成形（IMA，indirect mitral annuloplasty）术前规划常把计算文献中的缝线/桥缩短百分比直接当作前后径（AP，anteroposterior diameter，瓣环前后方向直径）缩减百分比。Galili 等（*R. Soc. Open Sci.* 2022）LHHM（Living Heart Human Model）算例表明，在本仓库 Galili 映射表约定下，IMA-AP 50% 峰缩期 AP=15.9 mm（近直接缩 AP；勿与未变形舒张期 34.4 mm 混用），而 70% 缝线才塌缩至约 58% AP——后者是数值极端而非临床剂量。

**方法：** 在可复现的 Python 一层代理（代数力学代理 + SPH-inspired 文献校准泄漏代理）上实现：（C1）缝线/桥缩短 % → 解剖 AP 缩减的假设映射（ARTO/MAVERIC 提供约 14–15% AP 可达语境；规划上限 20%；η 为假设先验，非临床标定）；（C2）连续设计空间扫掠 + 约束网格探索性情景排序；（C3）IMA-CS 远端着陆区 CS–LCx（coronary sinus–left circumflex）文献风险筛查阈值 ≥ 8.6 mm 与 NiTi 交变应变工程筛查 &lt; 0.4%；可选（C4）双缝线 vs 单缝线在相同 AP 缩减下的交界区泄漏对照（×0.5 为假设参数）。主图使用 **physics** 泄漏代理；YAML 锚点混合仅用于 Galili **校准/复现**病例 ID（非外部验证）。

**结果（seed=42）：** 先报告诚实留出/交叉验证：历史 pre-dampen 规则基 baseline MAE ROA≈50.18 mm²、泄漏≈1.445 pp；当前 dampened 规则基留出 MAE 见下文 CV 节；折内响应模型留出子集 MAE ROA≈6.37 mm²、泄漏≈0.245 pp（AP70≈6.60 mm² / 0.198 pp）。**随后**才是假设驱动的探索性排序：n_total_points=36，n_device_candidates=35，n_feasible_device_candidates=30，p_feasible_device_candidates≈0.8571；`fitted_response` 下最优候选为 **IMA-CS 20.0%**（AP↓11.0%，leakage_proxy≈0.3912%）。双缝线仅为图 5 假设敏感性，不是默认第一名。

**结论：** 一层代理可将 AP 探索性规划区间、射流位置与 LCx **风险筛查**写成探索性情景排序（非临床推荐、非已验证预测）；不能替代患者特异 LHHM/FSI。

### English abstract（与稿件一致）

Background: Preoperative planning for IMA often treats computational suture/bridge shortening percentages as if they were AP diameter reductions. Under the Galili-mapping table convention used here, IMA-AP 50% peak-systole AP = 15.9 mm (near-direct AP effect; not undeformed 34.4 mm), whereas 70% collapses AP by ~58%—a numerical extreme, not a clinical dose.

Methods: On a reproducible Python Layer-1 surrogate (algebraic mechanics + literature-calibrated leakage proxy) we implement C1–C3 (and optional C4). Main figures use physics leakage-proxy; YAML anchor blending is restricted to Galili calibration/reproduction case IDs.

Results (seed=42): Held-out / fold-wise CV first (historical rule-based baseline MAE ROA 50.18 / 1.445; fold-wise held-out subset ≈6.37 / 0.245; AP70 ≈6.60 / 0.198). Then assumption-driven ranking: 35 device candidates / 30 feasible (p≈0.8571); best under `fitted_response` is IMA-CS 20.0% (AP↓11.0%, leak≈0.3912%). Dual suture is hypothesis sensitivity (Fig. 5), not the default top rank.

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

- 舒张期基线瓣环周长 118.5 mm、AP 直径 34.4 mm；峰缩期疾病 AP 约 26.1 mm（Galili 启发参数化几何）。
- 后乳头肌病理以被动单元分数状态进入代数力学代理（`models/pathology.py`）。
- AP 为文献几何输入（`ap_role=literature_mapping_input`），不作预测 MAE。

### 装置与剂量映射（C1）

- IMA-CS：NiTi 桥缩短；IMA-AP：CS–IAS 缝线缩短；可选双缝线（交界因子为假设参数）。
- Galili 映射：复现发表离散峰缩期几何（50% 缝线 → 峰缩期 AP 15.9 mm；70% → 12.4 mm）。
- 临床映射：AP_reduction% = eta * shortening%；IMA-AP η=0.30；IMA-CS η=0.55（假设先验，非 MAVERIC 拟合）；规划上限 20% AP。
- LHS（N=120）扰动 η_AP、η_CS、双缝交界因子、CS–LCx 基线与 cinch 斜率。

### 物理通道与响应路径

- 代数力学代理 → 对合间隙/应变/接触代理分数 → ROA 与 jet∈{central, commissural, mixed}。
- 文献校准泄漏代理（SPH-inspired）→ `leakage_proxy_pct`（别名 `physics_regurgitation_pct`）；physics % ≠ 临床反流容积。
- Dryad `contact_fraction` 进入 fitted 响应特征；标量 AP/ROA/leak 仍以发表表为准。
- `response_path`：seed-42 论文默认 `fitted_response`；`rule_based_proxy` 保留作诊断。
- 真折内 CV：`analysis/fit_response_model.py` → `results/output/cross_validation/`。
- 规则基 blend-off 诊断：`tools/loo_evaluate.py`（不可与折内 CV 混称）。

### 扫掠与情景排序（C2–C3）

- 默认网格：IMA-AP 10–70% step 5%；IMA-CS 10–25% step 2%；双缝线同 AP 网格。
- 目标：最小化 leakage_proxy_pct。
- 约束：AP 缩减 ≤ 20%；NiTi 交变应变工程筛查 < 0.4%；IMA-CS CS–LCx ≥ 8.6 mm（文献风险筛查）；基线 CS–LCx=11.0 mm（示意假设，可换患者 CT）。
- Pareto：全局（min leak, max AP↓）；IMA-CS 族另加 LCx/NiTi；禁止 1e9/0 填补缺失值。
- 报告点均为**网格点**，非连续插值旋钮；输出为假设下最优候选，非临床推荐。

### 可复现命令

```powershell
pip install -r requirements.txt
python run_pipeline.py --seed 42 --paper --no-export
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python tools/package_reports.py
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

**备选最佳 IMA-AP 单缝线：** 65.0%；AP↓19.5%；leakage_proxy≈0.7931%；jet=`mixed`；交界分数 0.390。

**备选最佳 IMA-CS（常与最优重合）：** 20.0%；AP↓11.0%；leakage_proxy≈0.3912%；CS–LCx=8.6 mm；NiTi=0.33999999999999997%。

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

### 图 1. IMA-AP 泄漏代理随缝线缩短变化：Galili 峰缩期映射 vs 临床 η 映射

![图 1](results/output/paper_figures/fig1_ima_ap_nonmonotonic_exploratory_planning_range.png)

**文件：** `fig1_ima_ap_nonmonotonic_exploratory_planning_range.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉（为什么画这张图）：间接二尖瓣成形（IMA，indirect mitral annuloplasty）文献常同时报告“缝线缩短百分比”
与泄漏。读者容易把计算缝线 % 直接当成临床前后径（AP，anteroposterior diameter）缩减 %。本图把同一套
Layer-1 代理放在两条映射曲线上，用来回答：缩短 % 与泄漏代理之间的关系如何随几何映射改变？

坐标与量的定义：横轴 = IMA-AP 缝线缩短 %；纵轴 = leakage_proxy_pct（泄漏代理百分比）。该量来自代数/现象学
力学通道与文献校准泄漏代理（或 fitted_response 路径），不是超声测得的反流容积分数，也不是临床试验主要终点。

如何读：（1）Galili 映射复现发表峰缩期几何：IMA-AP 50% → 峰缩期 AP=15.9 mm（疾病峰缩期 26.1 mm；近直接缩 AP），
切勿写成未变形舒张期 34.4 mm / “0% AP”。70% 进一步塌缩 AP 并在代理上显示交界区泄漏风险升高的非单调倾向。
（2）临床/规划映射采用假设先验 AP_reduction% = η × shortening%，默认 η_AP=0.30（假设先验，非成像–力学辨识，
亦非 MAVERIC 拟合）。绿色带为 exploratory planning range，把约 14–20% AP 对话窗口反投到缝线 % 轴。

与 seed-42 排序的关系：本图解释剂量语义，不单独给出“最优装置”。seed-42 在 fitted_response + 临床映射下
最优候选是 IMA-CS 20%（见图 4 / 表 1），IMA-AP 曲线在此图中主要用于对照映射约定。

诚实边界：纵轴 ≠ 临床反流容积；Galili 峰缩期事实来自 doi:10.1098/rsos.211464；本仓库不新跑 LHHM/Abaqus。

### 图 2. 装置缩短百分比到 AP 直径缩减百分比的剂量映射

![图 2](results/output/paper_figures/fig2_suture_vs_ap_reduction.png)

**文件：** `fig2_suture_vs_ap_reduction.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉：图 1 看“缩短→泄漏”，本图看“缩短→AP 缩减”，把剂量翻译问题单独拆开，避免把泄漏变化误读成 AP 剂量。

坐标：横轴 = 装置缩短 %（IMA-AP 缝线或 IMA-CS 桥）；纵轴 = AP 直径缩减 %。三条轨迹：（i）Galili 峰缩期 IMA-AP
（近直接缩 AP）；（ii）规划 IMA-AP（η_AP=0.30）；（iii）规划 IMA-CS（η_CS=0.55，假设先验，不是从 MAVERIC/ARTO
回归得到）。水平带 14–20% 为探索性规划窗口；MAVERIC=ARTO 属 IMA-AP 类语境，Carillon/TITAN II 属 IMA-CS 语境。

如何读：同一缩短 % 在不同映射下对应的 AP% 可以相差很大。这正是 Layer-1“翻译层”存在的理由：计算缝线坐标
与临床 AP 对话窗口不是同一坐标。点线“数值极端”标出 Galili 高剂量 IMA-AP 相对疾病的大幅 AP 塌缩，提醒勿把
70% 缝线写成“临床缩 AP 七成”。

与结果衔接：seed-42 最优 IMA-CS 20% 在 η_CS=0.55 下对应 AP↓≈11%（低于 14–20% 窗口下沿，但仍在 AP 上限 20%
与 LCx/NiTi 约束内因泄漏代理更低而胜出）。窗口是语境带，不是硬可行域的唯一定义。

### 图 3. 射流位置与交界区 ROA 分数随缩短变化（Galili vs 临床）

![图 3](results/output/paper_figures/fig3_jet_location.png)

**文件：** `fig3_jet_location.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉：除泄漏“量”外，筛查还关心泄漏机制位置。ROA（regurgitant orifice area，反流口面积，mm²）在本代理中
由对合间隙等代数量估计，并拆成中央份额与交界区份额；再按阈值分为 central / mixed / commissural。本图把该
机制标签随缩短 % 的变化画出来，左右对照 Galili 与临床映射。

读图约定：横轴 = 缩短 %；纵轴 = 交界区 ROA 分数；方块 = IMA-AP，圆点 = IMA-CS；水平虚线为分类阈值示意。
标签是代理口上的机制草图，不是超声 PISA（proximal isovelocity surface area）或多普勒诊断结论。

如何联系 seed-42：在 fitted_response 排序下，最优候选 IMA-CS 20% 的 jet=`central`（交界分数约 0.10）。IMA-AP
高剂量单缝线在临床映射上更易进入 mixed；双缝线交界因子则在图 5 单独做假设敏感性，不在本图宣称“发现更优术式”。

结论（代理内）：机制标签随映射与剂量变化；可与表 1 / 图 5 交叉阅读，但不得把 jet 分类写成临床影像学验证。

### 图 4. IMA-CS 临床映射：泄漏代理–筛查 Pareto（CS–LCx 与 NiTi 交变应变）

![图 4](results/output/paper_figures/fig4_pareto_lcx_strain.png)

**文件：** `fig4_pareto_lcx_strain.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉：IMA-CS（经冠状窦路径）在减小泄漏代理的同时，可能缩短 CS–LCx（coronary sinus–left circumflex artery，
冠状窦与左回旋支）距离。文献风险筛查常用远端着陆区 CS–LCx 约 8.6 mm 作为“预测冠状动脉妥协”的 ROC 语境阈值
（Rottländer 等）。同时对 NiTi（镍钛）桥交变应变设置 <0.4% 的工程筛查上限。默认示意解剖基线 CS–LCx=11.0 mm
（design_space 假设，可换成患者 CT）。标题语言是“筛查”，不是“安全证明”。

读图：左面板横轴 CS–LCx (mm)、纵轴泄漏代理 %；右面板横轴 NiTi 交变应变 %、纵轴泄漏代理 %。点随桥缩短移动；
越贴近约束边界，可行域越窄。星号（若出现）标记 seed-42 情景排序在假设下的最优 IMA-CS 候选。

与 seed-42 的直接对应：最优候选为桥缩短 20%，AP↓11%，泄漏代理≈0.39%，CS–LCx=8.6 mm（贴边），NiTi 交变应变
≈0.34%。更高桥缩短常因 CS–LCx <8.6 mm 被判不可行。这是网格筛查信号，不是患者级安全性结论。

### 图 5. 双缝线交界因子敏感性（0.25/0.5/0.75/1.0）——假设参数，非发现声称

![图 5](results/output/paper_figures/fig5_dual_vs_single_suture.png)

**文件：** `fig5_dual_vs_single_suture.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉：双缝线（dual suture）在匹配 AP 缩减下可能改变交界区 ROA 份额。本仓库把“交界因子”写成显式假设参数，
并在 0.25/0.5/0.75/1.0 上做敏感性，而不是把它包装成已证实的术式创新（禁止 Innovation D / discovery 话术）。

读图：左右为 Galili / 临床映射；曲线为不同因子下的交界分数；虚线为单缝线对照。名义因子 ×0.5 仅是默认假设。

与主排序的关系：seed-42 默认 fitted_response 排序的第一名是 IMA-CS 20%，不是双缝线 60%。本图回答“若坚持双缝
假设，机制标签如何随因子变”，用于诚实展示假设敏感性；不得把图中 physics/机制差写成临床反流容积改善。


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
4. **双缝线：** 图 5 显示交界因子敏感性；×0.5 为假设参数，非模型“发现”；默认排序第一名不是双缝线。
5. **η 敏感性：** 当前 `fitted_response` 下 η±20% 仍保持 IMA-CS 20% 为名义最优，但实现 AP↓ 变为 8.8% / 11.0% / 13.2%；LHS top-1 稳定性见 uncertainty JSON。
6. **工具定位：** Level-1 是高保真分析前的透明探索性筛查层；seed-42 是可追溯**假设下最优候选**，不是治疗处方。

---

## 结论

在 seed-42、`fitted_response`、假设映射与默认约束下，一层代理情景排序给出可复现**假设下最优候选**：**IMA-CS 20.0%**，AP 缩减 **11.0%**，leakage_proxy **0.3912%**，jet=`central`。该结果展示了如何把 AP 窗口、射流机制与 LCx/NiTi **筛查**写入可复现研究原型，同时严格保持 Level-1 边界。

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
| IMA-CS | 0 | 10.0 | 0.6137 | 5.5 | 9.8 | 0.22 | central | True |  |
| IMA-CS | 0 | 12.0 | 0.5646 | 6.6 | 9.56 | 0.244 | central | True |  |
| IMA-CS | 0 | 14.0 | 0.5175 | 7.7 | 9.32 | 0.268 | central | True |  |
| IMA-CS | 0 | 16.0 | 0.4732 | 8.8 | 9.08 | 0.292 | central | True |  |
| IMA-CS | 0 | 18.0 | 0.4309 | 9.9 | 8.84 | 0.316 | central | True |  |
| IMA-CS | 0 | 20.0 | 0.3912 | 11.0 | 8.6 | 0.34 | central | True |  |
| IMA-CS | 0 | 22.0 | 0.3535 | 12.1 | 8.36 | 0.364 | central | False | cs_lcx |
| IMA-CS | 0 | 24.0 | 0.3164 | 13.2 | 8.12 | 0.388 | central | False | cs_lcx |
| IMA-CS | 0 | 25.0 | 0.2987 | 13.75 | 8.0 | 0.4 | central | False | niti_alternating_strain,cs_lcx |
| IMA-AP | 1 | 10.0 | 1.0085 | 3.0 |  |  | central | True |  |
| IMA-AP | 1 | 15.0 | 0.9834 | 4.5 |  |  | central | True |  |
| IMA-AP | 1 | 20.0 | 0.9586 | 6.0 |  |  | central | True |  |
| IMA-AP | 1 | 25.0 | 0.9341 | 7.5 |  |  | central | True |  |
| IMA-AP | 1 | 30.0 | 0.91 | 9.0 |  |  | central | True |  |
| IMA-AP | 1 | 35.0 | 0.8922 | 10.5 |  |  | central | True |  |
| IMA-AP | 1 | 40.0 | 0.8747 | 12.0 |  |  | central | True |  |
| IMA-AP | 1 | 45.0 | 0.8573 | 13.5 |  |  | central | True |  |
| IMA-AP | 1 | 50.0 | 0.8401 | 15.0 |  |  | central | True |  |
| IMA-AP | 1 | 55.0 | 0.8243 | 16.5 |  |  | central | True |  |
| IMA-AP | 1 | 60.0 | 0.8086 | 18.0 |  |  | mixed | True |  |
| IMA-AP | 1 | 65.0 | 0.7931 | 19.5 |  |  | mixed | True |  |
| IMA-AP | 1 | 70.0 | 0.7778 | 21.0 |  |  | mixed | False | ap_reduction |
| IMA-AP | 2 | 10.0 | 1.0085 | 3.0 |  |  | central | True |  |
| IMA-AP | 2 | 15.0 | 0.9834 | 4.5 |  |  | central | True |  |
| IMA-AP | 2 | 20.0 | 0.9586 | 6.0 |  |  | central | True |  |
| IMA-AP | 2 | 25.0 | 0.9341 | 7.5 |  |  | central | True |  |
| IMA-AP | 2 | 30.0 | 0.91 | 9.0 |  |  | central | True |  |
| IMA-AP | 2 | 35.0 | 0.8922 | 10.5 |  |  | central | True |  |
| IMA-AP | 2 | 40.0 | 0.8747 | 12.0 |  |  | central | True |  |
| IMA-AP | 2 | 45.0 | 0.8573 | 13.5 |  |  | central | True |  |
| IMA-AP | 2 | 50.0 | 0.8401 | 15.0 |  |  | central | True |  |
| IMA-AP | 2 | 55.0 | 0.8243 | 16.5 |  |  | central | True |  |
| IMA-AP | 2 | 60.0 | 0.8086 | 18.0 |  |  | central | True |  |
| IMA-AP | 2 | 65.0 | 0.7931 | 19.5 |  |  | central | True |  |
| IMA-AP | 2 | 70.0 | 0.7778 | 21.0 |  |  | central | False | ap_reduction |


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

- PDF：report.pdf: PASS → report.pdf (1629188 bytes); paper.pdf: PASS → docs/paper.pdf (1427721 bytes)
- report.html size：1359529 bytes
- data:image count：5

## 第十九节（完整）：双代理协作终报

| 项 | 内容 |
|----|------|
| GitHub URL | https://github.com/Coucou2016/fmr-ima-layer1-planner（PUBLIC；顾问可读完整代码/文档） |
| Commit hash | `8a882f77968991b979add3d120639d06258b2d83` |
| Push status | main; tracking status: ## main...origin/main |
| ChatGPT URL | https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65 |
| ChatGPT told full-repo readable | **Yes**（brief 明确写明 public GitHub 为 source of truth；本轮 MCP 粘贴受阻） |
| ChatGPT browser | BLOCKED — no usable browser MCP this turn; five local maturation rounds used archived literature reply + WebSearch + nature-skills. Ready briefs in docs/chatgpt_collab/rounds/round_01.md … round_05.md (no invented ChatGPT replies). |
| Baseline | seed-42 IMA-CS 20% / AP↓11% / leakage_proxy≈0.391% / central / fitted_response；SciencePlots 五图；golden tests；manuscript + nature framework |
| Context / brief | `docs/chatgpt_collab/rounds/` + `20260816_five_round_final.md` |
| Accepted | 规划/翻译层新颖性；Galili 表约定；LCx/NiTi 筛查；physics≠临床容积；Intro/Discussion 抛光；Results 来龙去脉；Methods claim audit |
| Rejected | Layer-1=LHHM；first CS-vs-AP；≥8.6 mm=safe；η±20%=FEA UQ；旗舰 Nature |
| Files | docs/manuscript_draft.md, docs/paper_framework_nature.md, docs/paper.html, docs/paper.md, docs/paper.pdf, report.html, report.md, report.pdf, docs/report.html, docs/report.md, tools/package_reports.py, docs/chatgpt_collab/rounds/round_01.md, docs/chatgpt_collab/rounds/round_02.md, docs/chatgpt_collab/rounds/round_03.md, docs/chatgpt_collab/rounds/round_04.md, docs/chatgpt_collab/rounds/round_05.md, docs/chatgpt_collab/20260816_five_round_final.md |
| Tests | PASS — PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -q; PASS — python run_pipeline.py --seed 42 --paper --no-export (planner: IMA-CS 20%, AP↓11.0%, leakage_proxy≈0.391%, jet=central, response_path=fitted_response) |
| PDF | report.pdf: PASS → report.pdf (1629188 bytes); paper.pdf: PASS → docs/paper.pdf (1427721 bytes) |
| Risks | base64 HTML 体积大；示意解剖与 η 限制外推；Level-2 待补充；ChatGPT GitHub 审阅回复待补档 |
| Scope | 公开 push 已完成；无 PR；无 deploy |
