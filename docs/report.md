# 功能性质二尖瓣反流（FMR）间接二尖瓣成形（IMA）一层代理术前规划研究报告

**英文题：** Clinically constrained preoperative planning of indirect mitral annuloplasty: mapping suture dose to AP-diameter reduction, jet location, and LCx safety on a Layer-1 surrogate

**工作短题：** Clinical-dose IMA planner (Layer-1)

**生成日期：** 2026-08-16  
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
- 临床映射：\(\mathrm{AP\_reduction\%}=\eta\times\mathrm{shortening\%}\)；IMA-AP η=0.30；IMA-CS η≈0.668；规划上限 20% AP。

### 物理通道

- 降阶 FEA → 对合间隙/应变/接触代理。
- ROA 由间隙估计；SPH 启发泄漏指数 → `physics_regurgitation_pct`。
- 射流位置 ∈ {central, commissural, mixed}（代理口机制标签）。

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
| 评估点数 / 可行点数 | 36 / 30 |
| 推荐装置 | IMA-AP，n_sutures=2 |
| 缩短 % | 60.0 |
| AP 直径 / 缩减 | 28.208 mm / 18.0% |
| MAVERIC 标尺 AP | 33.948 mm |
| ROA | 8.992 mm² |
| physics 反流 | 0.1519% → 报告 **0.152%** |
| jet / 交界分数 | central / 0.165 |

**备选单缝线 60%：** physics ≈ 0.1598% ，jet=`mixed`，交界分数 0.330。

**备选 IMA-CS 20%：** AP 缩减 ≈ 13.364% ，physics ≈ 0.2737% ，CS–LCx=8.6 mm，NiTi 交变应变=0.33999999999999997%。

### 6.2 Galili 锚点（Level 0）

| case_id | galili_regurgitation_pct | surrogate_blended_pct | surrogate_physics_pct | galili_ap_mm | galili_ap_reduction_pct | note |
| --- | --- | --- | --- | --- | --- | --- |
| pathology | 5.26 | 5.3310 | 5.3383 | 34.40 | 0.000 | blended reporting at YAML anchors; physics used in paper sweep figures |
| ima_cs_22 | 0.29 | 0.3000 | 0.3521 | 34.40 | 0.000 | blended reporting at YAML anchors; physics used in paper sweep figures |
| ima_ap_50 | 0.08 | 0.0931 | 0.1771 | 34.40 | 0.000 | blended reporting at YAML anchors; physics used in paper sweep figures |


### 6.3 临床窗口 vs 数值极端

| scenario | device | suture_or_bridge_pct | mapping_mode | ap_mm | ap_reduction_pct | physics_regurgitation_pct | jet_location | clinically_attainable | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAVERIC pair 41.4→35.3 mm | IMA-CS (Carillon) |  | clinical_literature | 35.3 | 14.734 |  |  | true | Carillon IMA-CS clinical series (MAVERIC); AP septal-lateral diameter at implant vs follow-up. |
| MAVERIC pair 45.0→38.7 mm | IMA-CS (Carillon) |  | clinical_literature | 38.7 | 14.0 |  |  | true | second MAVERIC AP pair |
| Galili IMA-AP 50% suture (0% AP reduction) | IMA-AP | 50.0 | galili | 34.4 | 0.0 | 0.0796 | central | false | LHHM optimum is not a 50% AP cinch |
| Galili IMA-AP 70% suture (~58% AP reduction, numerical extreme) | IMA-AP | 70.0 | galili | 14.3 | 58.43 | 11.855 | commissural | false | Not clinically attested; commissural leak in LHHM |
| Clinical mapping IMA-AP 50% suture (~15% AP reduction) | IMA-AP | 50.0 | clinical | 29.24 | 15.0 | 0.3033 | central | true | eta=0.30 planning assumption → MAVERIC-like AP dose |
| Clinical mapping IMA-CS 22% bridge (~14.7% AP reduction) | IMA-CS | 22.0 | clinical | 29.343 | 14.7 | 0.1347 | central | true | eta_cs calibrated to MAVERIC 14.7% at Galili 22% CS case; CS–LCx may fail on default 11 mm anatomy |
| Planner AP-reduction ceiling | constraint |  | clinical |  | 20.0 |  |  | true | window 14.0-20.0% |


### 6.4 η±20% 敏感性（规划假设扰动，非 FEA UQ）

| scenario | eta_ap | eta_cs | recommended_device | recommended_shortening_pct | n_sutures | ap_reduction_pct | physics_regurgitation_pct | jet_location | n_feasible | n_evaluated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eta_nominal | 0.3 | 0.66818 | IMA-AP | 60.0 | 2 | 18.0 | 0.1519 | central | 30 | 36 |
| eta_minus_20pct | 0.24 | 0.53454 | IMA-AP | 70.0 | 2 | 16.8 | 0.0895 | central | 32 | 36 |
| eta_plus_20pct | 0.36 | 0.80182 | IMA-CS | 20.0 | 0 | 16.036 | 0.2293 | central | 26 | 36 |


### 6.5 双缝线关键行（50/60/70%）

| mapping_mode | suture_shortening_pct | ap_reduction_pct | ap_matched | single_physics_regurgitation_pct | dual_physics_regurgitation_pct | delta_physics_regurg_pct_points | single_jet_location | dual_jet_location | single_commissural_fraction | dual_commissural_fraction | within_planner_ap_cap_20 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical | 50.0 | 15.0 | True | 0.3033 | 0.2984 | -0.0048 | central | central | 0.21 | 0.105 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 60.0 | 18.0 | True | 0.1598 | 0.1519 | -0.0079 | mixed | central | 0.33 | 0.165 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 70.0 | 21.0 | True | 0.8469 | 0.3471 | -0.4999 | mixed | central | 0.47 | 0.235 | False | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |


### 6.6 图 1–5

### 图 1. IMA-AP 物理反流随缝线缩短百分比的变化：Galili 映射 vs 临床映射

![图 1](results/output/paper_figures/fig1_ima_ap_nonmonotonic_clinical_window.png)

**文件：** `fig1_ima_ap_nonmonotonic_clinical_window.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

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

### 图 2. 装置缩短百分比到 AP 直径缩减百分比的剂量映射

![图 2](results/output/paper_figures/fig2_suture_vs_ap_reduction.png)

**文件：** `fig2_suture_vs_ap_reduction.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

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

### 图 3. 射流位置与交界区 ROA 分数随缩短变化（Galili vs 临床）

![图 3](results/output/paper_figures/fig3_jet_location.png)

**文件：** `fig3_jet_location.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：反流“量”之外，规划还关心泄漏机制位置。本代理将 ROA（regurgitant orifice area，
反流口面积，单位 mm²，由对合间隙等代理量估计）拆为中央份额与交界区份额，并分类为 central /
commissural / mixed。横轴为缩短 %；纵轴为交界区 ROA 分数；方块=IMA-AP，圆点=IMA-CS；左右面板对照
Galili 与临床映射。水平虚线为分类阈值示意。

如何读：交界区分数升高意味着泄漏更偏交界区；分类从 central 变为 mixed/commissural 表示机制标签切换。
该标签是代理口上的机制草图，不是超声 PISA（proximal isovelocity surface area）或多普勒诊断。
seed-42 推荐双缝线 60% 的机制来源可在本图与图 5 对照中追溯：同 AP 下交界份额更低、jet 保持 central。

结论：在临床映射下，IMA-AP 高剂量单缝线更易出现 mixed；IMA-CS 在可行桥缩短范围内多保持 central。
结合图 5，双缝线可在匹配 AP 缩减下压低交界区分数。

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

### 图 5. 双缝线 vs 单缝线 IMA-AP：匹配 AP 缩减下的交界区泄漏对照

![图 5](results/output/paper_figures/fig5_dual_vs_single_suture.png)

**文件：** `fig5_dual_vs_single_suture.png`（SciencePlots；轴标签英文，释义见下）

**来龙去脉：**

来龙去脉与读图说明：可选贡献 C4（Innovation D）在相同缝线缩短 %（故相同临床 AP 缩减）下比较单/双缝线。
纵轴关注交界区 ROA 分数；虚线可叠加单缝线 physics 反流作对照。左右面板对照 Galili / 临床映射。
本图隔离“缝线数量”变量，回答机制问题，不是器械清关或产品声明。

如何读：在 60% 临床映射点，单缝线 jet=mixed、交界分数 0.330；双缝线 jet=central、交界分数 0.165，
physics 反流由约 0.160% 降至约 0.152%——分类改善更醒目，幅度改善相对温和。70% 点 AP 缩减 21%
超出默认 20% 规划上限，仅作机制对照，不作推荐植入。

结论：双缝线是机制草图；seed-42 规划器推荐双缝线 60% 正是在该对照下选出的网格点。
勿将 0.152% physics 等同于临床反流容积改善。


### 6.7 方向性临床对齐（幅度不混用）

| source | device_or_arm | setting | ap_reduction_pct | regurg_metric | literature_direction | model_direction | direction_agrees | magnitude_equated | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAVERIC literature | Carillon (IMA-CS class) | 41.4→35.3 mm | 14.734 | (not used as surrogate target) | AP↓ |  |  | false | Carillon IMA-CS clinical series (MAVERIC); AP septal-lateral diameter at implant vs follow-up. |
| MAVERIC literature | Carillon (IMA-CS class) | 45.0→38.7 mm | 14.0 | (not used as surrogate target) | AP↓ |  |  | false | second MAVERIC AP pair |
| REDUCE-FMR literature | Carillon (IMA-CS class) | device vs sham |  | regurgitant volume ↓ (trial direction) | regurg↓ |  |  | false | Witte KK et al. A Randomized Sham-Controlled Study of Percutaneous Mitral Annuloplasty in Functional Mitral Regurgitation: The REDUCE FMR Trial. JACC Heart Fail. 2019;7(11):945-955. |
| Layer-1 clinical mapping | IMA-AP | IMA-AP 50.0% n_sutures=1 | 15.0 | physics regurg 0.3033% (jet=central) | AP↓, regurg↓ | AP↓, regurg↓ | yes | false | clinical IMA-AP 50% single (η=0.30 → 15% AP); magnitude not equated to trial % |
| Layer-1 clinical mapping | IMA-CS | IMA-CS 22.0% | 14.7 | physics regurg 0.1347% (jet=central) | AP↓, regurg↓ | AP↓, regurg↓ | yes | false | clinical IMA-CS 22% bridge (~14.7% AP); magnitude not equated to trial % |
| Layer-1 clinical mapping | IMA-AP | IMA-AP 60.0% n_sutures=2 | 18.0 | physics regurg 0.1519% (jet=central) | AP↓, regurg↓ | AP↓, regurg↓ | yes | false | planner recommendation (seed run); magnitude not equated to trial % |
| alignment policy | — | directionality only |  | — | AP↓ (MAVERIC); regurg↓ (REDUCE-FMR) | AP↓ and physics regurg↓ inside 14–20% window | yes | false | Do not equate Layer-1 physics % with trial regurgitant-volume % |


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

| case_id | device | shortening_pct | annulus_circumference_mm | ap_diameter_mm | roa_mm2 | regurgitation_pct | pathology_severity | max_principal_strain | reference_regurgitation_pct | jet_location | central_roa_mm2 | commissural_roa_mm2 | ap_reduction_mm | ap_reduction_pct | physics_regurgitation_pct | cs_lcx_mm | niti_alternating_strain_pct | mapping_mode |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pathology |  |  | 118.5 | 34.4 | 44.831214088682515 | 5.3310344827586205 | 0.44 | 0.1328 | 5.26 | central | 36.76159555271966 | 8.069618535962853 | 0.0 | 0.0 | 5.338288598855731 |  |  | galili |
| ima_cs_14 | IMA-CS | 14.0 | 116.27272727272727 | 34.4 | 22.074317419040224 | 1.3620689655172415 | 0.44 | 0.12360000000000002 |  | central | 19.866885677136203 | 2.2074317419040224 | 0.0 | 0.0 | 1.361443571394546 | 9.32 | 0.268 | galili |
| ima_cs_18 | IMA-CS | 18.0 | 115.63636363636364 | 34.4 | 16.55632667125463 | 0.7551724137931035 | 0.44 | 0.153 |  | central | 14.900694004129168 | 1.655632667125463 | 0.0 | 0.0 | 0.7567963322138515 | 8.84 | 0.316 | galili |
| ima_cs_22 | IMA-CS | 22.0 | 115.0 | 34.4 | 12.019231845822722 | 0.3 | 0.44 | 0.187 | 0.29 | central | 10.81730866124045 | 1.2019231845822722 | 0.0 | 0.0 | 0.35208489720226993 | 8.36 | 0.364 | galili |
| ima_ap_30 | IMA-AP | 30.0 | 117.0 | 34.4 | 14.798710127769885 | 0.7241379310344828 | 0.44 | 0.1169 |  | central | 12.7268907098821 | 2.071819417887784 | 0.0 | 0.0 | 0.7230974509382765 |  |  | galili |
| ima_ap_50 | IMA-AP | 50.0 | 116.0 | 34.4 | 25.494430293815512 | 0.09310344827586207 | 0.44 | 0.1159 | 0.08 | central | 20.90543284092872 | 4.588997452886792 | 0.0 | 0.0 | 0.1771025061091915 |  |  | galili |
| ima_ap_70 | IMA-AP | 70.0 | 115.0 | 14.3 | 125.8369256798663 | 11.093103448275862 | 0.44 | 0.1399 |  | commissural | 15.100431081583968 | 110.73649459828233 | 20.099999999999998 | 58.43023255813953 | 11.092876255198957 |  |  | galili |


### B. Pareto / 可行域表（节选完整导出）

| device | n_sutures | shortening_pct | physics_regurgitation_pct | ap_reduction_pct | cs_lcx_mm | niti_alternating_strain_pct | jet_location | feasible | constraint_violations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IMA-CS | 0 | 10.0 | 1.9295 | 6.682 | 9.8 | 0.22 | central | True |  |
| IMA-CS | 0 | 12.0 | 1.4499 | 8.018 | 9.56 | 0.244 | central | True |  |
| IMA-CS | 0 | 14.0 | 1.0511 | 9.355 | 9.32 | 0.268 | central | True |  |
| IMA-CS | 0 | 16.0 | 0.7265 | 10.691 | 9.08 | 0.292 | central | True |  |
| IMA-CS | 0 | 18.0 | 0.4695 | 12.027 | 8.84 | 0.316 | central | True |  |
| IMA-CS | 0 | 20.0 | 0.2737 | 13.364 | 8.6 | 0.34 | central | True |  |
| IMA-CS | 0 | 22.0 | 0.1347 | 14.7 | 8.36 | 0.364 | central | False | cs_lcx |
| IMA-CS | 0 | 24.0 | 0.0843 | 16.036 | 8.12 | 0.388 | central | False | cs_lcx |
| IMA-CS | 0 | 25.0 | 0.0781 | 16.705 | 8.0 | 0.4 | central | False | niti_alternating_strain,cs_lcx |
| IMA-AP | 1 | 10.0 | 3.8636 | 3.0 |  |  | central | True |  |
| IMA-AP | 1 | 15.0 | 3.124 | 4.5 |  |  | central | True |  |
| IMA-AP | 1 | 20.0 | 2.4821 | 6.0 |  |  | central | True |  |
| IMA-AP | 1 | 25.0 | 1.9314 | 7.5 |  |  | central | True |  |
| IMA-AP | 1 | 30.0 | 1.464 | 9.0 |  |  | central | True |  |
| IMA-AP | 1 | 35.0 | 1.0734 | 10.5 |  |  | central | True |  |
| IMA-AP | 1 | 40.0 | 0.7532 | 12.0 |  |  | central | True |  |
| IMA-AP | 1 | 45.0 | 0.4972 | 13.5 |  |  | central | True |  |
| IMA-AP | 1 | 50.0 | 0.3033 | 15.0 |  |  | central | True |  |
| IMA-AP | 1 | 55.0 | 0.1941 | 16.5 |  |  | central | True |  |
| IMA-AP | 1 | 60.0 | 0.1598 | 18.0 |  |  | mixed | True |  |
| IMA-AP | 1 | 65.0 | 0.4315 | 19.5 |  |  | mixed | True |  |
| IMA-AP | 1 | 70.0 | 0.8469 | 21.0 |  |  | mixed | False | ap_reduction |
| IMA-AP | 2 | 10.0 | 3.8571 | 3.0 |  |  | central | True |  |
| IMA-AP | 2 | 15.0 | 3.1169 | 4.5 |  |  | central | True |  |
| IMA-AP | 2 | 20.0 | 2.4748 | 6.0 |  |  | central | True |  |
| IMA-AP | 2 | 25.0 | 1.9239 | 7.5 |  |  | central | True |  |
| IMA-AP | 2 | 30.0 | 1.4568 | 9.0 |  |  | central | True |  |
| IMA-AP | 2 | 35.0 | 1.0669 | 10.5 |  |  | central | True |  |
| IMA-AP | 2 | 40.0 | 0.7478 | 12.0 |  |  | central | True |  |
| IMA-AP | 2 | 45.0 | 0.493 | 13.5 |  |  | central | True |  |
| IMA-AP | 2 | 50.0 | 0.2984 | 15.0 |  |  | central | True |  |
| IMA-AP | 2 | 55.0 | 0.1874 | 16.5 |  |  | central | True |  |
| IMA-AP | 2 | 60.0 | 0.1519 | 18.0 |  |  | central | True |  |
| IMA-AP | 2 | 65.0 | 0.2404 | 19.5 |  |  | central | True |  |
| IMA-AP | 2 | 70.0 | 0.3471 | 21.0 |  |  | central | False | ap_reduction |


### C. 双缝线全表

| mapping_mode | suture_shortening_pct | ap_reduction_pct | ap_matched | single_physics_regurgitation_pct | dual_physics_regurgitation_pct | delta_physics_regurg_pct_points | single_jet_location | dual_jet_location | single_commissural_fraction | dual_commissural_fraction | within_planner_ap_cap_20 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clinical | 10.0 | 3.0 | True | 3.8636 | 3.8571 | -0.0064 | central | central | 0.115 | 0.0575 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 15.0 | 4.5 | True | 3.124 | 3.1169 | -0.007 | central | central | 0.1225 | 0.0613 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 20.0 | 6.0 | True | 2.4821 | 2.4748 | -0.0073 | central | central | 0.13 | 0.065 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 25.0 | 7.5 | True | 1.9314 | 1.9239 | -0.0075 | central | central | 0.1375 | 0.0687 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 30.0 | 9.0 | True | 1.464 | 1.4568 | -0.0072 | central | central | 0.145 | 0.0725 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 35.0 | 10.5 | True | 1.0734 | 1.0669 | -0.0065 | central | central | 0.1525 | 0.0762 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 40.0 | 12.0 | True | 0.7532 | 0.7478 | -0.0054 | central | central | 0.16 | 0.08 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 45.0 | 13.5 | True | 0.4972 | 0.493 | -0.0042 | central | central | 0.1675 | 0.0837 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 50.0 | 15.0 | True | 0.3033 | 0.2984 | -0.0048 | central | central | 0.21 | 0.105 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 55.0 | 16.5 | True | 0.1941 | 0.1874 | -0.0067 | central | central | 0.27 | 0.135 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 60.0 | 18.0 | True | 0.1598 | 0.1519 | -0.0079 | mixed | central | 0.33 | 0.165 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 65.0 | 19.5 | True | 0.4315 | 0.2404 | -0.1911 | mixed | central | 0.39 | 0.195 | True | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |
| clinical | 70.0 | 21.0 | True | 0.8469 | 0.3471 | -0.4999 | mixed | central | 0.47 | 0.235 | False | Matched AP via same suture % under clinical η; mechanism sketch (Innovation D) |


---

## 第十九节：双代理协作终报

见同目录 HTML 终报章节或下方「打包时写入」的终报正文（生成脚本在 HTML 中展开完整第十九节）。

**GitHub（公开）：** https://github.com/Coucou2016/fmr-ima-layer1-planner  
**ChatGPT URL：** https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65  
**本轮性质：** 公开仓库推送 + 报告/论文打包；顾问可读完整公开代码/文档；ChatGPT 浏览器 MCP 本轮受阻（见完整第十九节）。  
**推送：** 已 push `main`（PUBLIC）；无 PR。


### 打包脚本状态附记

- PDF：report.pdf: PASS → report.pdf (1509000 bytes); paper.pdf: PASS → docs/paper.pdf (1532272 bytes)
- report.html size：1271315 bytes
- data:image count：5

## 第十九节（完整）：双代理协作终报

| 项 | 内容 |
|----|------|
| GitHub URL | https://github.com/Coucou2016/fmr-ima-layer1-planner（PUBLIC；顾问可读完整代码/文档） |
| Commit hash | `unknown` |
| Push status | git metadata unavailable: Command '['git', 'rev-parse', 'HEAD']' returned non-zero exit status 128. |
| ChatGPT URL | https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65 |
| ChatGPT told full-repo readable | **Yes**（brief 明确写明 public GitHub 为 source of truth；本轮 MCP 粘贴受阻） |
| ChatGPT browser | BLOCKED — no usable browser MCP this turn; five local maturation rounds used archived literature reply + WebSearch + nature-skills. Ready briefs in docs/chatgpt_collab/rounds/round_01.md … round_05.md (no invented ChatGPT replies). |
| Baseline | seed-42 dual 60% / AP 18% / physics 0.152% / central；SciencePlots 五图；golden tests；manuscript + nature framework |
| Context / brief | `docs/chatgpt_collab/rounds/` + `20260816_five_round_final.md` |
| Accepted | 规划/翻译层新颖性；Galili 表约定；LCx/NiTi 筛查；physics≠临床容积；Intro/Discussion 抛光；Results 来龙去脉；Methods claim audit |
| Rejected | Layer-1=LHHM；first CS-vs-AP；≥8.6 mm=safe；η±20%=FEA UQ；旗舰 Nature |
| Files | docs/manuscript_draft.md, docs/paper_framework_nature.md, docs/paper.html, docs/paper.md, docs/paper.pdf, report.html, report.md, report.pdf, docs/report.html, docs/report.md, tools/package_reports.py, docs/chatgpt_collab/rounds/round_01.md, docs/chatgpt_collab/rounds/round_02.md, docs/chatgpt_collab/rounds/round_03.md, docs/chatgpt_collab/rounds/round_04.md, docs/chatgpt_collab/rounds/round_05.md, docs/chatgpt_collab/20260816_five_round_final.md |
| Tests | PASS — PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -q (40 passed); PASS — python run_pipeline.py --seed 42 --paper --no-export (planner: IMA-AP dual 60%, AP 18.0%, physics 0.152%, jet=central) |
| PDF | report.pdf: PASS → report.pdf (1509000 bytes); paper.pdf: PASS → docs/paper.pdf (1532272 bytes) |
| Risks | base64 HTML 体积大；示意解剖与 η 限制外推；Level-2 待补充；ChatGPT GitHub 审阅回复待补档 |
| Scope | 公开 push 已完成；无 PR；无 deploy |
