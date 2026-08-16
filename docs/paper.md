# 稿件草稿 / Manuscript draft (Layer-1)

**EN title:** Clinically constrained preoperative planning of indirect mitral annuloplasty: mapping suture dose to AP-diameter reduction, jet location, and LCx safety on a Layer-1 surrogate

**中文工作题：** 临床约束下的间接二尖瓣成形术术前规划：在一层代理模型上将缝线剂量映射到前后径缩减、反流束位置与回旋支安全

**工作短题：** Clinical-dose IMA planner (Layer-1)

**Nature-skills axes:** `paper_type=methods` · `journal=generic` (CMBBE / MedEngPhys / RSOS-class; not flagship *Nature*) · framework: `docs/paper_framework_nature.md`

**One-sentence argument:** In preoperative IMA planning for FMR, we show that a Layer-1 surrogate can map suture/bridge shortening onto clinically attainable AP reduction, jet location, and LCx safety via a constrained physics-only planner, supported by Galili Level-0 anchors and seed-42 outputs, without claiming new LHHM/Abaqus FSI or first CS-vs-AP comparison.

**数据来源：** `python run_pipeline.py --seed 42 --paper`（本稿数字均来自该次可复现运行；**非**新的 Abaqus/LHHM FSI 结果）

**验证层级：** Level 0（Galili 锚点）+ Level 1（临床剂量映射 + 扫掠/规划器）。Level 2（患者特异 LHHM / 全 FSI）**不在本文范围**。

**Figures:** SciencePlots + Times New Roman, dpi≥300 (`analysis/plots.py`).

---

## Abstract（草稿）

### English abstract

**Background:** Preoperative planning for indirect mitral annuloplasty (IMA) often treats computational suture/bridge shortening percentages as if they were anteroposterior (AP) diameter reductions. Galili et al. (*R. Soc. Open Sci.* 2022) compared IMA-CS and IMA-AP in the Living Heart Human Model (LHHM), but those suture percentages are mechanical parameterizations, not clinical AP doses. In the Layer-1 Galili-mapping table used here, the published discrete **50%** suture case retains diastolic AP = **34.4 mm** (**0%** mapped AP cinch), whereas **70%** maps to ~**58%** AP collapse—a numerical extreme, not a clinical dose.

**Methods:** On a reproducible Python Layer-1 surrogate (reduced-order FEA + SPH leak index) we implement three contributions: (C1) **clinically referenced** mapping of suture/bridge shortening % to attainable AP reduction (MAVERIC ~13–15%, planning ceiling 20%); (C2) continuous design-space sweep plus constrained grid-search preoperative planner; (C3) literature-informed CS–LCx **screening** at distal landing (&lt;8.6 mm predicted compromise in Rottländer et al.; planner retains candidates with CS–LCx ≥ 8.6 mm) and NiTi alternating-strain **engineering screen** &lt; 0.4%. Optional (C4) compares dual vs single suture at matched AP reduction. Main figures use **physics** regurgitation; YAML anchor blending is restricted to Galili validation case IDs.

**Results (seed=42):** Under clinical mapping the planner evaluates 36 points and retains 30 feasible designs; it recommends **IMA-AP dual suture 60%** (η=0.30 → AP reduction **18.0%**, physics regurgitation **0.152%**, jet=`central`). The matched single-suture setting is jet=`mixed` with a higher commissural fraction. On default anatomy (baseline CS–LCx 11.0 mm), the best feasible IMA-CS is bridge shortening **20%** (CS–LCx exactly **8.6 mm**). Under Galili mapping, IMA-AP 50% remains 0% mapped AP reduction with physics regurgitation ~0.080%; 70% reaches ~58% AP reduction with `commissural` leak.

**Conclusions:** A Layer-1 surrogate can encode the clinical AP window, jet location, and LCx/NiTi screening into a deployable preoperative recommendation. Novelty is the **planning/translation layer**, not a new LHHM CS-vs-AP duel. It does not replace patient-specific LHHM/FSI, equate physics % with clinical regurgitant volume, or treat η as a newly identified FEA parameter.

**Keywords:** functional mitral regurgitation; indirect mitral annuloplasty; preoperative planning; coronary sinus; LCx; Layer-1 surrogate

### 中文摘要

**背景：** 间接二尖瓣成形（IMA）术前规划常把计算文献中的缝线/桥缩短百分比直接当作前后径（AP）缩减百分比。Galili 等（*R. Soc. Open Sci.* 2022）在 LHHM 中比较了 IMA-CS 与 IMA-AP，但其缝线百分比是力学参数化而非临床 AP 剂量。在本仓库 **Galili 映射表约定**下，发表离散 **50%** 缝线病例仍保留舒张期 AP=**34.4 mm**（映射 AP 缩减 **0%**），**70%** 才塌缩至约 **58%** AP——后者是数值极端而非临床剂量。

**方法：** 在可复现的 Python 一层代理（降阶 FEA + SPH 泄漏指数）上实现三项贡献：（C1）**临床参照**映射，将缝线/桥缩短 % 翻译到可达 AP 缩减（MAVERIC ~13–15%，规划上限 20%）；（C2）连续设计空间扫掠 + 约束网格搜索术前规划器；（C3）文献知情的 CS–LCx **筛查**（Rottländer：远端着陆区 &lt;8.6 mm 预测 circumflex compromise；规划器保留 CS–LCx ≥ 8.6 mm 的候选）与 NiTi 交变应变 **工程筛查** &lt; 0.4%。可选（C4）双缝线 vs 单缝线在相同 AP 缩减下的交界区泄漏对比。主图均使用 **physics** 反流分数；YAML 锚点混合仅用于 Galili 验证病例。

**结果（seed=42）：** 临床映射下，规划器在 36 个评估点中选出 30 个可行点；推荐 **IMA-AP 双缝线 60%**（η=0.30 → AP 缩减 **18.0%**，physics 反流 **0.152%**，jet=`central`）。同剂量单缝线为 jet=`mixed`、交界区分数更高。IMA-CS 在默认解剖（基线 CS–LCx 11.0 mm）上，可行最优为桥缩短 **20%**（CS–LCx 恰为 **8.6 mm**）。Galili 映射下 IMA-AP 50% 仍为 0% 映射 AP 缩减、physics 反流约 0.08%；70% 为 ~58% AP 缩减并呈 `commissural` 泄漏。

**结论：** 一层代理可将临床 AP 窗口、射流位置与 LCx/NiTi 筛查写成可部署的术前建议；新颖性在**规划/翻译层**，而非新的 LHHM CS-vs-AP 对决。它不能替代患者特异 LHHM/FSI，不能把 physics % 当作临床反流容积，也不能把 η 当作新 FEA 辨识结果。

**关键词：** functional mitral regurgitation; indirect mitral annuloplasty; preoperative planning; coronary sinus; LCx; Layer-1 surrogate

---

## 1. Introduction

### English Introduction

Functional mitral regurgitation (FMR) arises from an adverse interaction between ventricular remodeling, mitral annular geometry, leaflet tethering, and impaired leaflet coaptation. Indirect mitral annuloplasty (IMA) approaches seek to modify this geometry without direct leaflet repair, but different device concepts act through different anatomical pathways. Coronary-sinus-based annuloplasty, represented here as IMA-CS and exemplified clinically by the Carillon concept, applies a remodeling effect through the coronary sinus and adjacent mitral annular region. An alternative concept considered in this work, IMA-AP, uses a coronary-sinus–to–interatrial-septum (CS–IAS) suture to produce an anteroposterior (AP) cinching effect. These mechanisms share the objective of improving mitral geometry, but they should not be treated as mechanically or clinically equivalent.

A computational precedent already exists: Galili, White Zeira, and Marom (*R. Soc. Open Sci.* 2022) compared generic IMA-CS and IMA-AP treatments in the Living Heart Human Model (LHHM) with finite-element and leakage analyses. That study established the treatment taxonomy and documented non-monotonic IMA-AP behavior at discrete suture settings. What remains unresolved for preoperative dialogue is **dose translation**: published suture/bridge shortening percentages are mechanical parameterizations, not clinical AP doses. In the Layer-1 Galili-mapping **table convention** used here, the published discrete 50% suture case retains diastolic AP = 34.4 mm (0% mapped AP cinch); settings such as Galili 70% therefore must not be narrated as a 70% clinical AP reduction. By contrast, MAVERIC reports of approximately **13–15%** AP diameter change provide a clinically referenced geometric window, while REDUCE-FMR supplies **directional** evidence that coronary-sinus-based remodeling can reduce mitral regurgitation. These clinical sources constrain plausibility and directionality; they do **not** validate the surrogate’s physics regurgitation percentage against trial regurgitant volumes.

The present study therefore evaluates a Layer-1 IMA **planning/translation** scaffold—a reproducible Python surrogate intentionally **not** a production finite-element model and not a re-run of LHHM FSI. It does not reproduce nonlinear tissue mechanics, contact, leaflet stress, device deployment, or patient-specific coronary-sinus deformation. Instead, it combines simplified physics-informed quantities with configurable YAML terms to rank candidate IMA-CS and IMA-AP strategies under explicit geometric and screening assumptions. For IMA-CS, distal-landing-zone CS–LCx separation enters as a literature-informed **screening** constraint (Rottländer et al.: &lt;8.6 mm predicted compromise in their ROC; the planner retains candidates with CS–LCx ≥ 8.6 mm on an illustrative baseline of **11 mm**). This is not a claim that ≥8.6 mm is universally safe, nor a patient-specific procedural clearance.

The contributions are limited to a transparent pre-FEA planning layer. **C1** provides clinically referenced mapping of suture/bridge shortening % onto attainable AP reduction. **C2** provides continuous design-space sweep plus constrained preoperative ranking with inspectable physics vs YAML origins. **C3** encodes LCx and NiTi alternating-strain **engineering screens**. Optional **C4** compares dual vs single suture at matched AP reduction. Novelty is the encoding of clinical AP dose, jet location, and screening constraints into a reproducible planner—not a claim of first computational CS-vs-AP comparison (already performed in LHHM by Galili et al.). Seed-42 planner outputs are reported in Results as internal surrogate recommendations, not clinical effect sizes.

### 中文引言要点

- FMR 与 IMA-CS（Carillon 类）/ IMA-AP（CS–IAS 缝线）机制差异，不可机械等价。
- Galili 2022 已完成 LHHM 上 CS vs AP 比较；本文新颖性=术前**剂量翻译/规划层**，非“首次比较”。
- Galili 映射表约定：50% 缝线 → 0% 映射 AP cinch（表坐标，非 Galili 临床结论）；MAVERIC AP ~13–15%；REDUCE-FMR 仅方向性。
- LCx：&lt;8.6 mm 预测风险 ≠ ≥8.6 mm 已证明安全；η 为规划假设。
- 本文贡献 C1–C3（及可选 C4）：见 `docs/paper_plan.md`；Level-1 代理，非生产 FEA / Level-2。

---

## 2. Methods

### 2.1 English Methods

This study uses a reproducible **Layer-1 Python surrogate** for preoperative IMA design planning. It is **not** a new patient-specific LHHM / Abaqus fluid–structure interaction (FSI) campaign (validation Level 2 remains out of scope; export hooks only).

**Pathology and geometry.** Posterior papillary pathology is applied as a fractional passive-element state change on a parametric papillary mesh (`models/pathology.py`). Diastolic baseline annulus circumference (118.5 mm) and AP diameter (34.4 mm) come from the Galili-inspired parametric heart geometry (`models/heart_geometry.py`).

**Device kinematics and clinically referenced dose mapping (C1).** Discrete Galili YAML cases and continuous sweep points apply IMA-CS (NiTi bridge shortening) or IMA-AP (CS–IAS suture shortening) through `models/devices.py`. Two AP mappings are available: (i) **Galili** — reproduces published LHHM discrete geometry coordinates in a planner table (IMA-AP 50% suture → **0% mapped** AP reduction at AP 34.4 mm; 70% → ~58% AP / 14.3 mm); this table convention is **not** a prose claim that “Galili clinically concluded 50% suture = 0% AP”; (ii) **clinical** — planning transfer
\[\mathrm{AP\_reduction\%}=\eta\times\mathrm{shortening\%},\]
with IMA-AP \(\eta=0.30\) (50% suture → 15% AP) and IMA-CS \(\eta\approx0.668\) (22% bridge → ~14.7% AP), documented in `configs/design_space.yaml` and `results/clinical_references.yaml`. **η is a planning assumption**, not an imaging–FEA identification. The default planning ceiling is **20%** AP reduction (MAVERIC-attested window ~13–15%). We prefer the phrase **clinically referenced mapping** over “validated clinical conversion.”

**Reduced-order FEA, ROA, and SPH leak index.** Peak-systolic loading drives a reduced-order FEA surrogate relating annulus tightening, pathology severity, and coaptation gap to strain/contact (`simulation/run_case.py`, `simulation/loading.py`). Regurgitant orifice area (ROA) is estimated from coaptation gap with optional soft contact-cluster blending for discrete pipeline reporting (`simulation/roa_surrogate.py`). An SPH-inspired leak index (~29k particles honored as a count, not a full Lagrangian SPH solver) converts ROA and gap into **physics** regurgitation (`sph/hemodynamics.py`). At Galili validation case IDs only (`pathology`, `ima_cs_22`, `ima_ap_50`, …), reported regurgitation may blend physics with YAML anchors (`configs/surrogate_calibration.yaml`); **paper sweep/planner figures use physics only**. Physics regurgitation % is a surrogate metric and **must not** be equated with clinical regurgitant volume or regurgitant fraction.

**Jet location.** Surrogate ROA is split into central vs commissural shares and classified as `central` / `commissural` / `mixed` (`analysis/jet.py`). This is a mechanism label on the surrogate orifice, not echocardiographic PISA/Doppler.

**Design sweep and constrained planner (C2–C3).** Default grids: IMA-AP 10–70% step 5%; IMA-CS 10–25% step 2%; optional dual-suture IMA-AP on the same AP grid (`analysis/design_sweep.py`). The planner minimizes physics regurgitation subject to AP reduction ≤ 20%, NiTi alternating strain &lt; 0.4% (**engineering screen**, not fatigue qualification / infinite-life claim), and IMA-CS CS–LCx ≥ 8.6 mm as a literature-informed **screening** boundary based on Rottländer et al. 2021 (&lt;8.6 mm in the distal landing zone predicted compromise; **≥8.6 mm is not asserted as proven safe**), with illustrative baseline CS–LCx = 11.0 mm replaceable by patient CT (`analysis/planner.py`). Reported implants are **grid points**, not interpolated continuous dials. No Level-2 patient-specific LHHM/FSI results are claimed.

**Optional dual suture (C4).** At matched suture % (hence matched clinical AP reduction), dual vs single suture commissural fractions are compared as a mechanism sketch, not a device-clearance study.

**η sensitivity.** Planner recommendations are re-run at η±20% and exported to `eta_sensitivity.csv` / `.json`. This probes planning-assumption sensitivity, **not** Abaqus/LHHM uncertainty quantification.

**Paper artifacts.** `python run_pipeline.py --seed 42 --paper` writes five PNGs under `results/output/paper_figures/` and tables under `results/output/paper_tables/` (`analysis/paper_tables.py`, `analysis/plots.py`). Clinical literature alignment tables are **directionality-only** (AP↓ / regurg↓); magnitudes are not equated to trial regurgitant-volume percentages.

**Claim audit (Methods boundary).** Allowed: Layer-1 reproducible planning; Galili Level-0 anchors; seed-42 physics-channel planner outputs; clinically referenced AP window; LCx/NiTi screens. Forbidden: new LHHM/Abaqus cases; “first CS vs AP”; physics % = clinical volume; η as FEA-identified; “CS–LCx ≥ 8.6 mm is safe”; NiTi “fatigue cleared.”

**Honesty.** Main manuscript figures report `physics_regurgitation_pct`. This manuscript does **not** invent or report new Abaqus/LHHM cases and must not be cited as production FEA validation.

### 2.2 模块映射（中文）

| 步骤 | 模块 |
|------|------|
| 病理 + 参数化瓣环 | `models/pathology.py`, `models/heart_geometry.py` |
| 装置运动学、Galili vs 临床映射、CS–LCx、双缝线 | `models/devices.py`, `configs/design_space.yaml` |
| 降阶 FEA（间隙、应变） | `simulation/run_case.py` |
| ROA 物理估计 | `simulation/roa_surrogate.py` |
| SPH 泄漏指数 → physics 反流 | `sph/hemodynamics.py` |
| 射流位置 ∈ {central, commissural, mixed} | `analysis/jet.py` |
| 连续扫掠 | `analysis/design_sweep.py` |
| 约束规划器（网格搜索） | `analysis/planner.py` |
| 论文表/图 | `analysis/paper_tables.py`, `analysis/plots.py` |
| 临床引用与 η 假设 | `results/clinical_references.yaml` |
| Galili 锚点混合（仅验证病例） | `configs/surrogate_calibration.yaml`, `run_pipeline.py` |

**诚实声明：** 主文图表使用 `physics_regurgitation_pct`。YAML 混合仅限于病例 ID `pathology` / `ima_cs_22` / `ima_ap_50` 等验证表。**本稿不报告、不虚构 Abaqus/LHHM 新算例。**

**设计空间（默认）：** IMA-AP 10–70% step 5%；IMA-CS 10–25% step 2%；双缝线同 AP 网格。约束：AP 缩减 ≤ 20%；NiTi 交变应变 &lt; 0.4%；IMA-CS CS–LCx ≥ 8.6 mm（基线解剖默认 11.0 mm，可换患者 CT）。

**临床映射假设（Innovation A）：**  
\(\mathrm{AP\_reduction\%} = \eta \times \mathrm{shortening\%}\)。IMA-AP \(\eta=0.30\)（50% 缝线 → 15% AP）；IMA-CS \(\eta\approx0.668\)（22% 桥 → ~14.7% AP）。η 为规划假设，非新成像–FEA 辨识。

---

## 3. Results（叙事；seed=42 实测）

Results answer three methods-paper questions under seed 42: (i) does the Galili-mapping table reproduce Level-0 anchors without inventing new LHHM cases? (ii) does clinical η mapping place candidates inside a MAVERIC-scale AP window while exposing Galili 70% as a numerical extreme? (iii) does the constrained planner return an inspectable, reproducible recommendation with explicit LCx/NiTi screens and η sensitivity? All numeric claims below are pipeline outputs from `python run_pipeline.py --seed 42 --paper`.

### 3.1 Galili 锚点复现（Validation Level 0）

**来龙去脉：** Before any clinical-dose ranking, the surrogate must land on published Galili discrete anchors (pathology / IMA-CS 22% / IMA-AP 50%) so that later sweep curves are tethered to Level-0 geometry and regurgitation references—not free-floating heuristics. Blended columns may use YAML anchors at those case IDs only; physics columns remain the manuscript’s primary channel.

离散 YAML 病例上（混合报告 vs physics；见 `paper_tables/galili_vs_surrogate.csv`）：

| Case | Galili 反流 % | Surrogate blended % | Surrogate physics % | Galili AP mm | Galili AP 缩减 % |
|------|---------------|---------------------|---------------------|--------------|------------------|
| pathology | 5.26 | ~5.33 | ~5.34 | 34.4 | 0 |
| ima_cs_22 | 0.29 | ~0.30 | ~0.35 | 34.4 | 0 |
| ima_ap_50 | 0.08 | ~0.09 | ~0.177 | 34.4 | 0 |

扫掠（Galili 映射；Fig 1 left / Galili curve）：IMA-AP 50% → 映射 AP 缩减 **0%**，physics 反流 **~0.080%**，jet=`central`；IMA-AP 70% → AP **~58.4%**，physics 反流 **~11.9%**，jet=`commissural`（数值极端）。这解释了为何“更多缝线缩短”在 Galili 坐标上可以非单调恶化，而不能被写成单调临床剂量响应。

### 3.2 临床剂量窗口 vs 数值极端（C1）

**来龙去脉（Fig 1–2）：** Fig 1 contrasts physics regurgitation vs suture % under Galili vs clinical (η=0.30) mappings and paints the ~14–20% AP suture band under η=0.30. Fig 2 makes the translation explicit: shortening % → AP reduction %, with a horizontal clinical window and a marker for the Galili 70% extreme. Together they answer whether a candidate is “in the MAVERIC-scale conversation” or “still a computational extreme.”

见 `clinical_window_vs_numerical_extreme.csv`：

- MAVERIC：41.4→35.3 mm（**14.7%**）、45.0→38.7 mm（**14%**）——几何终点，非本代理反流标定。
- 临床映射 IMA-AP 50%：AP **15.0%**，physics 反流 **~0.30%**，jet=`central`。
- 临床映射 IMA-CS 22%：AP **~14.7%**，physics 反流 **~0.13%**；在默认 11 mm 基线上 CS–LCx 可能触及 8.6 mm 筛查边界（见规划器）。
- 规划上限：**20%** AP 缩减。

**方向性对齐（非幅度等同）：** `maveric_reduce_fmr_alignment.csv` 将模型在临床窗口内的 AP↓ / 反流↓ 与 MAVERIC（AP↓）及 REDUCE-FMR（反流↓）文献方向对照；**不**声称百分比幅度可互换，**不**声称 “validated against” 试验终点。

### 3.3 约束术前规划器（C2 + C3）

**来龙去脉（Fig 3–4 + planner JSON）：** Fig 3 tracks jet / commissural-fraction trajectories that the planner must not ignore when ranking “low regurg.” Fig 4 shows why IMA-CS candidates can be cut by CS–LCx and NiTi screens even when physics regurg falls. The planner objective is minimize physics regurg subject to AP ≤ 20%, NiTi screen, and LCx screen; outputs are grid points.

`planner/recommendation.json`（clinical 映射）：

- 评估 **36** / 可行 **30**。
- **推荐：** IMA-AP **双缝线 60%**，AP 缩减 **18.0%**（AP 28.21 mm；MAVERIC 标尺 ~33.9 mm），ROA ~9.0 mm²，physics 反流 **0.152%**，jet=`central`，交界区分数 **0.165**。
- 备选单缝线同 60%：physics **0.160%**，jet=`mixed`，交界区分数 **0.330**。
- 备选 IMA-CS **20%**：AP 缩减 **~13.4%**，physics **0.274%**，CS–LCx **8.6 mm**（筛查贴边，非“已证明安全”），NiTi 交变应变 **0.34%**（&lt;0.4% 工程筛查）。

η±20% 敏感性见 `eta_sensitivity.json` / `.csv`（规划假设扰动，非 FEA 不确定性量化）：

| 情景 | η_ap | 推荐 | AP 缩减 % | physics 反流 % |
|------|------|------|-----------|----------------|
| nominal | 0.30 | IMA-AP dual 60% | 18.0 | 0.152 |
| −20% | 0.24 | IMA-AP dual 70% | 16.8 | 0.0895 |
| +20% | 0.36 | IMA-CS 20% | 16.036 | 0.2293 |

**解读：** η 升高使同一缝线 % 更快触顶 20% AP 上限，可行 AP 网格变窄，推荐可跳到可行 IMA-CS；η 降低则允许更高缝线 % 仍落在窗口内。说明规划器对转移效率假设敏感——η 需患者/影像校准，而非固定物理常数。

### 3.4 射流位置与双缝线（C4 / Innovation D）

**来龙去脉（Fig 5）：** At matched suture % (hence matched clinical AP %), dual vs single suture mainly changes commissural ROA share and jet label. Fig 5 and `dual_vs_single_matched_ap.csv` isolate that mechanism without claiming a cleared dual-suture device.

| 缝线 % | AP 缩减 % | 单缝线 jet / 交界分数 / physics % | 双缝线 jet / 交界分数 / physics % |
|--------|-----------|-----------------------------------|-----------------------------------|
| 50 | 15.0 | central / 0.210 / 0.303 | central / 0.105 / 0.298 |
| 60 | 18.0 | mixed / 0.330 / 0.160 | central / 0.165 / 0.152 |
| 70 | 21.0* | mixed / 0.470 / 0.847 | central / 0.235 / 0.347 |

\*70% 临床映射 AP 缩减 21% 超出默认 20% 规划上限，表中作机制对照，不作为推荐植入。

**要点：** 双缝线在匹配 AP 缩减下降低交界区 ROA 份额，并在 60% 处将 jet 从 `mixed` 拉回 `central`；physics 反流降幅相对温和。这是机制草图，非器械清关研究。

### 3.5 LCx / 应变 Pareto（C3）

**来龙去脉（Fig 4）：** IMA-CS 临床映射下，反流随桥缩短下降，同时 CS–LCx 逼近 8.6 mm 筛查线、交变应变逼近 0.4% 工程筛查。默认解剖上可行集以 CS–LCx 约束截断；患者 CT 基线替换后推荐会移动。贴边可行 ≠ 患者安全证明。

---

## 4. Figure captions（Fig 1–5）

**Fig 1.** IMA-AP physics 反流随缝线缩短 % 的变化：Galili AP 映射（非单调，70% 恶化）与临床 η=0.30 映射对照；绿色带为约 14–20% AP 窗口对应的缝线区间（η=0.30）。主曲线为 physics，无 YAML 混合。纵轴 ≠ 临床反流容积。文件：`fig1_ima_ap_nonmonotonic_clinical_window.png`。

**Fig 2.** 装置缩短 % → AP 直径缩减 %：Galili LHHM 表坐标（缝线 % ≠ AP %）、临床 IMA-AP（η=0.30）、临床 IMA-CS（η≈0.67）；水平带为临床 AP 窗口 14–20%；虚线标 Galili 70% 数值极端（~58% AP）。文件：`fig2_suture_vs_ap_reduction.png`。

**Fig 3.** 射流位置 / 交界区 ROA 分数随缩短变化（方=IMA-AP，圆=IMA-CS）；左右分别为 Galili 与临床映射。水平虚线为分类阈值示意；标签非 PISA/多普勒。文件：`fig3_jet_location.png`。

**Fig 4.** IMA-CS 临床映射 Pareto：physics 反流 vs CS–LCx（Rottländer &lt;8.6 mm 预测风险 → 规划器筛查线）及 vs NiTi 交变应变 0.4% 工程筛查。基线 CS–LCx=11.0 mm 为示意解剖；≥8.6 mm ≠ 已证明安全。文件：`fig4_pareto_lcx_strain.png`。

**Fig 5.** Innovation D：双缝线 vs 单缝线 IMA-AP 的交界区分数（及单缝线 physics 反流虚线）在 Galili / 临床映射下的对照——机制草图。文件：`fig5_dual_vs_single_suture.png`。

---

## 5. Discussion

### English Discussion

The central advance is not a new LHHM duel between IMA-CS and IMA-AP—Galili et al. already performed that comparison—but a transparent **Layer-1 planning/translation** layer that keeps experimental suture shortening separate from modeled and clinical AP reduction. In the Galili-mapping **table convention**, the published discrete 50% suture case retains diastolic AP = 34.4 mm (0% mapped AP cinch). Galili-derived percentages therefore define a mechanical parameterization rather than a clinical dose scale, and Galili 70% should not be narrated as a 70% therapeutic AP dose.

A rival reading—that “more suture shortening is always better”—is rejected by the Galili-mapping sweep itself: the 70% point maps to ~58% AP collapse with commissural leak rise. Another rival reading—that Layer-1 physics regurgitation % can stand in for clinical regurgitant volume—is rejected by construction: the metric is a surrogate leak index, reported separately from YAML blend, and never calibrated to trial MR volumes. MAVERIC’s approximately **13–15%** AP change and REDUCE-FMR’s directional CS remodeling therefore test geometric/directional plausibility only.

Coronary anatomy remains a binding screen on IMA-CS strategies. The scaffold retains CS–LCx ≥ **8.6 mm** because Rottländer et al. found distal-landing &lt;8.6 mm predictive of compromise—not because ≥8.6 mm is proven universally safe. With illustrative baseline **11 mm**, the CS **20%** candidate sits on the modeled edge of the admissible region. That is a planner caution, not proof of patient safety or hazard: vessel deformation, device contact, and deployment are out of scope.

For seed 42, the planner selects dual-suture AP **60%** (modeled AP **18%**, physics regurg **0.152%**, jet=`central`). The most salient dual-suture effect is jet-class change; the regurgitation-surrogate reduction is mild. The 0.152% value must **not** be equated with clinical regurgitant volume, fraction, or treatment effect. Ranking also requires visibility into scoring: paper sweep/planner figures use physics; YAML blend is confined to Galili case IDs. A plausible ranking does not prove the physics component is correct—only that the recommendation is inspectable and reproducible.

Sensitivity to η is interpretive signal, not a bug. A **±20%** change can move the preference from dual AP 60% to dual AP 70% or CS 20%. The nominal recommendation is therefore conditional on η; future work should calibrate η from patient/imaging pairs rather than treat η±20% as Abaqus/LHHM uncertainty quantification.

Overall, the Layer-1 scaffold is a hypothesis-ranking and screening tool preceding higher-fidelity analysis. It organizes competing IMA concepts, enforces simplified anatomical screens, exposes sensitivity, and yields reproducible rankings, but it cannot substitute for patient-specific mechanics, production FEA, benchtop validation, or clinical evidence. The seed-42 result is a traceable surrogate recommendation, not a therapeutic prescription.

### 中文讨论

1. **Galili 表约定：** 发表离散 50% 缝线病例保留 AP=34.4 mm（0% 映射 AP cinch）——规划坐标，不宜写成“Galili 临床结论称 50% 缝线=0% AP”。
2. **临床 ~13–15% 窗口：** MAVERIC 几何参照；规划默认上限 20%；避免把 Galili 70% 塌缩当剂量。
3. **LCx 筛查：** &lt;8.6 mm 预测风险 ≠ ≥8.6 mm 已证明安全；默认 11→20% 桥处贴边可行仅为规划警示。
4. **双缝线：** 匹配 AP 下主要改善交界区分类，physics 反流降幅温和——机制讨论，非优越器械宣称。
5. **与 REDUCE-FMR / MAVERIC：** 仅方向对齐；幅度不混用；勿写 validated against。
6. **η 敏感性：** η±20% 可改变推荐，说明转移效率需校准，非 FEA UQ。
7. **定位：** 规划/翻译层；seed-42 是可追溯推荐而非治疗处方；非 Level-2。

---

## 6. Limitations

1. 降阶 FEA + SPH；无在线 Abaqus/LHHM 耦合。
2. η 为规划假设，非新成像–FEA 成对辨识。
3. 默认 CS–LCx 解剖（11 mm）为示意；阈值 8.6 mm + 患者 CT 才是临床输入。
4. 射流分类拆分代理 ROA，非超声 PISA/多普勒。
5. 网格搜索报告步进植入设置，不发明连续“旋钮”。
6. 双缝线系列为机制草图（Innovation D）。

---

## 7. Validation levels

| Level | 含义 | 本仓库状态 |
|-------|------|------------|
| **0** | 复现 Galili 发表锚点（反流、ROA、几何趋势） | 已实现；pytest |
| **1** | 扫掠 + 临床剂量映射 + 规划约束 + 论文图 | 已实现；physics 主图 |
| **2** | 患者特异 LHHM / 全 FSI / Abaqus UMAT / 真 29k SPH | **超出范围**；仅有 `fea_export` 钩子 |

勿将 Level-1 曲线表述为 Level-2 FEA。

---

## 8. How to regenerate

```powershell
pip install -r requirements.txt   # includes SciencePlots
python run_pipeline.py --seed 42 --paper --no-export
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
```

图表输出：`results/output/paper_figures/`（SciencePlots + Times New Roman，`dpi≥300`；该目录在 `results/output/` 下默认被 gitignore；需本地/CI 再生）。

写作框架：`docs/paper_framework_nature.md`（nature-writing methods 轴；勿声称 first IMA-CS vs AP 比较）。

Golden regressions：`tests/test_golden_regressions.py`（planner seed-42 元组、Galili 50%→0% AP、CS–LCx/η 守卫）。
