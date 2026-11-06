# 面向间接二尖瓣成形探索性筛选的一层文献锚定代理模型

**短标题：** FMR 间接成形一层探索性代理

**文章类型：** 计算生物力学 / 科研软件方法。本文给出文献锚定的一层代数代理与探索性情景排序，属于方法与软件贡献，不是临床决策试验。

**一句话主张：** 我们发布一套可复现的 Python 一层代理，在 Galili 峰缩期锚点与 Dryad 接触特征上完成标定与折内交叉验证，并在明确几何与传递效率假设下对 IMA-CS 与 IMA-AP 情景做探索性排序。本文不宣称新的 Living Heart Human Model（LHHM）有限元分析，也不宣称临床推荐或患者级外部验证。

**复现命令：** `python run_pipeline.py --seed 42 --paper` · `python tools/import_galili_dryad.py --from-fixture --process` · `python -m analysis.fit_response_model --write` · `python tools/loo_evaluate.py --write`

**验证层级：** 第 0 层复现选定的 Galili 算例。第 1 层加入探索性规划图、不确定度情景排序与折内响应诊断。第 2 层患者特异性 LHHM 或流固相互作用不在本文范围。

---

## 摘要

功能性质二尖瓣反流（FMR）的间接成形（IMA）计算研究常同时报告缝线或桥缩短、峰缩期几何与泄漏。Galili 等在 LHHM 中比较了冠脉窦桥型（IMA-CS）与前后径型（IMA-AP）通用策略（doi:10.1098/rsos.211464）。其峰缩期 IMA-AP 缩短 50% 时前后径（AP）为 15.9 mm，相对疾病态 26.1 mm 呈近直接 AP 效应。该值须与未变形舒张期 AP 34.4 mm 分开使用。装置类别在临床上也不同。MAVERIC 评价的是 ARTO，属于 CS–房间隔 / IMA-AP 类。Carillon 与 REDUCE-FMR 属于 IMA-CS 类。

现有高保真计算已给出机制比较，但仍缺少假设透明、可复现、能在给定约束下快速筛查剂量设定的一层科研软件层。峰缩期 AP 语义、装置类别归属、留出诚实报告与排序稳定性，仍需要可核验的方法包装。

本文实现可复现的 Python 一层代理，将现象学力学与文献标定泄漏代理结合。配置开关选择排序所用的响应路径。seed=42 论文默认路径为 `fitted_response`。`rule_based_proxy` 路径保留作诊断。Dryad 支持文件（doi:10.5061/dryad.bzkh1899d）提供来源追溯与辅助特征 `contact_fraction`，用于表外插值。标量 AP、反流口面积（ROA）与泄漏在无法独立导出时仍由表填入。折内响应模型

$$
f_{\mathrm{ROA}}(\Delta\mathrm{AP},\ \mathrm{device\ family},\ \mathrm{annular\ reduction},\ \mathrm{contact\_fraction})
\tag{1}
$$

与

$$
f_{\mathrm{leak}}(\mathrm{ROA},\ \mathrm{coaptation\ proxy},\ \mathrm{contact},\ \mathrm{device\ mechanism})
\tag{2}
$$

在真实留一算例折下拟合。全训练集拟合支撑排序。离散情景排序器在 AP 减小上限、示意性镍钛（NiTi）工程筛与 Rottländer 冠脉窦–左回旋支（CS–LCx）风险筛阈值约束下，最小化 `leakage_proxy_pct`。拉丁超立方抽样（LHS，$N=120$）探测多参数排序稳定性。双缝交界因子按假设敏感性处理（图 5）。

在 seed=42 下，留出 Galili 子集上折内响应模型交叉验证的 ROA 平均绝对误差（MAE）为 6.37 mm²，泄漏 MAE 为 0.245 个百分点（pp）。历史记录的阻尼前规则基线为 50.18 mm² / 1.445 pp。IMA-AP 70% 折内绝对误差为 6.60 mm² / 0.198 pp。上述指标为内部工程筛，不是医学验证。当前阻尼后规则路径诊断的留出 MAE 为 5.24 mm² / 0.043 pp。IMA-AP 70% 上规则路径预测泄漏 0.07%，发表值为 0.13%，绝对误差 0.06 pp。论文排序因此采用 `fitted_response`，以获得一致的表外响应面。规划图下排序器评估 36 个网格点（35 个装置候选），保留 30 个可行设计（可行比例 0.857）。最优可行候选为 IMA-CS 桥缩短 20%（AP 减小 11%，泄漏代理 0.391%，射流为中央，CS–LCx 为 8.6 mm，位于风险筛边缘）。LHS 不确定度量化给出首位概率 $P(\mathrm{top\text{-}1})=0.342$，平均可行比例 0.822。

文献锚定的低阶代理可在可检查假设、诚实留出报告与不确定度表述下支持 IMA 策略设定的探索性筛查。它不是术前临床决策系统。物理泄漏代理百分比不是临床反流容积。

**关键词：** 功能性质二尖瓣反流；间接二尖瓣成形；代理模型；探索性筛查；科研软件；一层模型

---

## 1 引言

### 1.1 研究背景

功能性质二尖瓣反流由心室重塑、瓣环扩张与对合不良引起。原发性瓣叶病变不是必要条件。间接二尖瓣成形试图在不直接修补瓣叶的条件下重塑瓣环几何。文献中反复出现两类计算装置族。IMA-CS 缩短冠脉窦桥，临床对应 Carillon 类装置。IMA-AP 缩短 CS–房间隔缝线，主要作用于前后径，机制上对应 MAVERIC 评价的 ARTO。这两条路径在力学上不可互换。

### 1.2 已有工作与缺口

Galili、White Zeira 与 Marom（2022）在 Living Heart Human Model 中比较了通用 IMA-CS 与 IMA-AP，并量化装置部署后的泄漏（doi:10.1098/rsos.211464）。其峰缩期 IMA-AP 50% 算例给出 AP = 15.9 mm，显示近直接 AP 效应。未变形舒张期 AP = 34.4 mm 属于不同心相，不能进入峰缩期剂量陈述。临床系列提供不同尺度的几何语境。ARTO / MAVERIC 报告 IMA-AP 类装置约 14%–15% 的 AP 减小。Carillon / TITAN II 与 REDUCE-FMR 提供 IMA-CS 方向性信息。Rottländer 等给出 CS–LCx 解剖与程序规划语境，其中 8.6 mm 可作为风险筛阈值词汇。

高保真有限元与模块化二尖瓣工具已分别回答机制比较与几何建模问题。科研软件仍需要透明的剂量换算、来源追溯、留出诚实性，以及在明确假设下的探索性排序。本文不宣称首次计算学 CS 与 AP 比较，不引入新的 LHHM 有限元，也不提供临床推荐引擎。

### 1.3 本文工作

本文贡献一层文献锚定代理与可检查的情景排序软件。工作包括校正峰缩期 Galili AP 语义，把 MAVERIC 归属于 ARTO（IMA-AP 类），将 Dryad `contact_fraction` 放入拟合响应路径，并列报告真实折内响应诊断与更名后的规则路径 blend-off 诊断，并在拉丁超立方抽样下报告排序稳定性。适用边界写在方法与讨论中。主要结果均由 seed=42 流水线产物复现。

---

## 2 相关工作与定位

我们跟随高保真 IMA 建模论文与模块化二尖瓣方法工具的结构写法，同时贡献互补的一层软件层。

**表 1.** 文献角色与本文边界

| 角色 | 来源 | 本文借鉴 | 本文不宣称 |
|------|------|----------|------------|
| 机制有限元基线 | Galili 等，*R. Soc. Open Sci.* 2022;9:211464 | 机制、参数化、几何与功能读数；IMA-CS 与 IMA-AP 分类 | 新的 LHHM / 有限元 / SPH；CS 对 AP 的优先权主张 |
| 临床 AP 语境 | Worthley / MAVERIC（ARTO） | 几何终点与反流终点分开 | 用物理百分比标定临床反流容积 |
| CS 方向性 | Witte 等，REDUCE-FMR；Carillon TITAN II | 克制因果措辞；冠脉意识 | 用试验量级做验证 |
| LCx 筛查词汇 | Rottländer 等，2021 / 2022 | 在 CS–LCx = 8.6 mm 处使用可行与不可行筛查语言 | 证明大于等于 8.6 mm 即安全 |
| 方法工具语气 | 几何驱动二尖瓣有限元工具（*Med Eng Phys* / *CMBBE* 类） | 模块化方法；单变量扫描 | 把连续体应力接触当作代理真值 |

本文新增科研软件包装、拟合路径中的 Dryad 接触特征、折内响应诊断，以及可检查的一层情景排序器。工作定位为一层探索性软件层。

---

## 3 软件架构

仓库按功能分目录。

```
configs/    surrogate_calibration.yaml, design_space.yaml, 算例 YAML
models/     geometry, pathology, devices, response_model（折内 f_ROA / f_leak）
simulation/ 现象学力学代理（历史别名 run_fea_surrogate）
sph/        文献标定泄漏代理（SPH 启发，不是完整 SPH 求解器）
analysis/   ROA、射流、扫描、scenario_ranker、fit_response_model、论文表图
tools/      import_galili_dryad.py, loo_evaluate.py, package_reports.py
data/       原始投放区、fixtures、处理后的 galili_cases.csv
results/output/cross_validation/   真实折内交叉验证产物
results/output/planner/            scenario_ranking.json（seed=42 排序）
```

入口包括 `run_pipeline.py`、`python -m analysis.planner`、`python -m analysis.fit_response_model` 与 `python -m analysis.design_sweep`。

---

## 4 方法

### 4.1 研究对象与几何

参数化乳头肌病理（约 44% 后叶被动比例）定义疾病基线。未变形舒张期与峰缩期作为不同的 `cardiac_phase` 记录保存。AP 直径是文献定义的几何输入（`ap_role: literature_mapping_input`）。因此不把 AP 的平均绝对误差报告为预测精度。

### 4.2 问题表述与装置运动学

在 Galili 映射模式下，峰缩期 AP 跟随发表表坐标，并在离散 Galili 算例间插值。在临床 / 规划模式下，AP 减小遵循

$$
\mathrm{AP\_reduction\%}=\eta\times\mathrm{shortening\%}
\tag{3}
$$

假设先验均值为 $\eta_{\mathrm{AP}}=0.30$、$\eta_{\mathrm{CS}}=0.55$。$\eta_{\mathrm{CS}}$ 不是从 MAVERIC / ARTO 拟合得到。默认不确定度量化在 $\eta_{\mathrm{AP}}\in U(0.24,0.36)$、$\eta_{\mathrm{CS}}\in U(0.44,0.66)$、双缝交界因子、CS–LCx 基线与收紧斜率上做拉丁超立方抽样（$N=120$，见 `design_space.yaml`）。

### 4.3 实现：力学与泄漏代理

代数对合间隙、应变与接触代理分数构成现象学力学通道。泄漏代理在病理算例上按文献标定。物理反流百分比不是临床反流容积。合成接触簇 ROA 仅用于可视化（`model_weight=1`，`cluster_weight=0`）。Dryad `contact_fraction` 作为科学特征进入拟合响应路径。正式导出字段为 `leakage_proxy_pct`、`strain_risk_score` 与 `contact_score`。历史别名保留兼容。

`configs/design_space.yaml` 将 `response_path` 设为三个选项之一。`fitted_response` 是论文 / seed=42 排序默认。`rule_based_proxy` 是历史探索 / 诊断路径。`hybrid_ap_extreme` 保留规则路径，并把 AP 类过短算例转到拟合面。

### 4.4 标定与来源追溯

`tools/import_galili_dryad.py` 记录下载或手工投放，再在可用处提取 `contact_fraction` 与 `n_sph_particles`。标量 AP、ROA 与泄漏仍由表填入。导入器不会仅凭未标注瓣叶坐标发明这些标量。本地出版商 PDF 可选。Galili 文章按 DOI 10.1098/rsos.211464 与 Dryad 数据集 doi:10.5061/dryad.bzkh1899d 引用。

标定算例标识在 blend 打开时仅作复现。病理、IMA-CS 22% 与 IMA-AP 50% 为标定复现集合。IMA-CS 14%、IMA-CS 18%、IMA-AP 30% 与 IMA-AP 70% 为留出诊断集合。

### 4.5 核验：诊断与真实折内交叉验证

`tools/loo_evaluate.py` 在固定规则代理上运行无锚点 / 留一算例 blend-off 诊断，不做折内重拟合。`analysis/fit_response_model.py` 执行真实折内拟合，留出 ROA 与泄漏不进入训练数组。排序用的全训练参数写在 `results/output/response_model/`。交叉验证摘要写在 `results/output/cross_validation/`。

内部工程筛目标为留出子集 ROA MAE 小于 25 mm²、泄漏 MAE 小于 0.5 pp，以及 IMA-AP 70% 上 ROA 绝对误差小于 25 mm²、泄漏绝对误差小于 0.5 pp。这些目标是工程筛，不是医学验证阈值。

### 4.6 情景排序器与 Pareto 家族

排序器在探索性 AP 减小上限（默认 20%）、示意性 NiTi 交变应变筛（小于 0.4%）与 CS–LCx 风险筛阈值（大于等于 8.6 mm）约束下，最小化 `leakage_proxy_pct`。LCx 阈值标注为筛查，不是安全放行。报告计数包括总点数、装置候选数、可行装置候选数、可行比例、$P(\mathrm{top\text{-}1})$ 与一阶 Spearman 敏感性秩。Pareto 家族分开报告。全局共同目标最小化泄漏并最大化 AP 减小。IMA-CS 家族另含 LCx 与 NiTi。IMA-AP 家族使用共同目标。缺失的 LCx / NiTi 值不用哨兵填充。双缝交界因子是显式假设敏感性参数（图 5：0.25 / 0.5 / 0.75 / 1.0）。14%–20% AP 带是临床语境化的探索性规划区间。

---

## 5 结果

### 5.1 数据来源与处理

处理后的表 `data/processed/galili_cases.csv` 将 Dryad 来源的 `contact_fraction` 与 `n_sph_particles` 标记为 `source_tier=dryad_derived`。发表的峰缩期 AP、ROA 与泄漏标量仍由表填入。本节数字均可由 seed=42 产物核验。

### 5.2 第 0 层标定复现

**表 2.** Galili 峰缩期表填锚点（不是本文预测）

| 算例 | 泄漏 % | 峰缩期 AP mm | ROA mm² |
|------|--------|--------------|---------|
| pathology | 5.26 | 26.1 | 172.8 |
| ima_cs_22 | 0.29 | 24.8 | 48.2 |
| ima_ap_50 | 0.08 | 15.9 | 27.3 |
| ima_ap_70 | 0.13 | 12.4 | 46.1 |

标定标识在 blend 打开时仅作复现。IMA-AP 50% 的峰缩期 AP = 15.9 mm 是后续剂量换算必须守住的文献事实。舒张期未变形 AP = 34.4 mm 不进入峰缩期剂量陈述。

### 5.3 留出诊断与真实折内交叉验证

规则路径 blend-off 诊断由 `tools/loo_evaluate.py` 生成。历史记录的阻尼前基线在留出标识上报告 ROA MAE 50.18 mm²、泄漏 MAE 1.445 pp，IMA-AP 70% 绝对误差 94.17 mm² / 5.455 pp。阻尼后当前 seed=42 诊断报告留出 MAE 为 5.24 mm² / 0.043 pp。IMA-AP 70% 上当前规则路径泄漏为 0.07%，发表值为 0.13%，绝对误差 0.06 pp。

真实折内响应模型留一验证由 `analysis/fit_response_model.py` 生成。留出子集 ROA MAE 为 6.37 mm²，泄漏 MAE 为 0.245 pp。IMA-AP 70% 绝对误差为 6.60 mm² / 0.198 pp（预测 ROA 39.5 mm² 对 46.1；预测泄漏 0.33% 对 0.13%）。内部工程筛在该七算例表上满足。这不是患者级外部验证。七折全表 MAE 会因病理留出与 ROA 量级差距而抬高。AP 预测指标仍不适用。

**表 3.** 留出算例对照（seed=42）

| 算例 | 发表 ROA | 规则 ROA（绝对误差） | 折内 ROA（绝对误差） | 发表泄漏 % | 规则泄漏（绝对误差 pp） | 折内泄漏（绝对误差 pp） |
|------|----------|----------------------|----------------------|------------|-------------------------|-------------------------|
| ima_cs_14 | 56.7 | 59.6（2.9） | 69.6（12.9） | 0.52 | 0.51（0.01） | 0.60（0.08） |
| ima_cs_18 | 55.3 | 54.9（0.4） | 53.4（1.9） | 0.41 | 0.42（0.01） | 0.42（0.01） |
| ima_ap_30 | 51.1 | 42.4（8.7） | 47.0（4.1） | 0.16 | 0.25（0.09） | 0.86（0.70） |
| ima_ap_70 | 46.1 | 37.2（8.9） | 39.5（6.6） | 0.13 | 0.07（0.06） | 0.33（0.20） |

论文排序优先采用 `fitted_response`，以便在规划图运动学下得到连贯的表外响应面。规则路径保留为具名的 blend-off 诊断。

图 1 给出 IMA-AP 泄漏代理随缝线缩短的变化，并标出探索性 14%–20% AP 规划带在缝线百分比空间中的位置。图 2 把装置缩短映射到 AP 减小，分别显示 Galili IMA-AP、临床 IMA-AP（$\eta=0.30$）与临床 IMA-CS（$\eta=0.55$）假设先验。图 3 显示 ROA 交界比例与射流位置标签随缩短变化。

### 5.4 探索性情景排序与不确定度

在规划图、`fitted_response` 与 seed=42 下，总点数 $n_{\mathrm{total}}=36$，装置候选 $n_{\mathrm{device}}=35$，可行数 $n_{\mathrm{feasible}}=30$，可行比例 $p_{\mathrm{feasible}}=0.857$。最优可行候选为 IMA-CS 桥缩短 20%（$\eta_{\mathrm{CS}}=0.55$，AP 减小 11.0%，泄漏代理 0.391%，射流为中央，CS–LCx 8.6 mm）。同约束下最优 IMA-AP 单缝与双缝替代方案泄漏更高（缩短 65% / AP 减小 19.5% 时泄漏代理 0.79%）。双缝按假设敏感性报告（图 5）。

LHS 多参数不确定度量化（$N=120$）给出 $P(\mathrm{top\text{-}1})=0.342$，平均可行比例 0.822。一阶 Spearman 秩主要由 CS–LCx 基线与收紧斜率主导。$\eta\pm 20\%$ 单因素敏感性仍把 IMA-CS 20% 保持为名义最优候选，同时把实现的 AP 减小移到 8.8% / 11.0% / 13.2%。可行数在 $\eta$ 减 20%、名义与加 20% 下分别为 32、30 与 26。

图 4 给出 IMA-CS 临床图上的 Pareto / 风险筛视图，纵虚线分别标记 Rottländer 8.6 mm 筛与 0.4% NiTi 工程应变筛。

### 5.5 仅方向性的临床语境对照

ARTO / MAVERIC 报告约 14%–15% 的 AP 减小（IMA-AP 类）。Carillon TITAN II 报告约 15% 的 AP 语境（IMA-CS 类）。REDUCE-FMR 提供反流方向性信息。这些量级不与物理泄漏代理百分比等同。

---

## 6 讨论

核心贡献是透明的探索性筛查软件。它校正 Galili 峰缩期 AP 语义，把 MAVERIC 归属于 ARTO 这一 IMA-AP 类装置，把 Dryad `contact_fraction` 放入拟合路径，诚实报告含 IMA-AP 70% 在内的留出与交叉验证指标，并提供带家族正确 Pareto 语言的 LHS 排序稳定性。

相对 Galili 的 LHHM 研究，我们不再争论高保真下哪种通用装置封得更好。相对临床系列，我们只借用几何窗口与筛查词汇。相对模块化二尖瓣有限元工具，我们用可检查的假设先验与快速网格排序，换取连续体保真度。

已记录的边界如下。Galili 峰缩期表仅有 7 个算例，不是患者级外部验证。没有患者 CT，也没有患者特异性心腔几何。没有从 Dryad 粒子云按心腔标注重算 SPH 泄漏。全域点云可用，但 AP、ROA 与泄漏仍由表填入。代数与现象学代理携带 $\eta$ 与双缝因子的假设先验。LCx 与 NiTi 筛是文献与工程筛，不是安全放行。排序是假设驱动的探索性分析，不是已验证预测。

双缝因子改变交界 ROA 分配与射流标签，但不改变当前网格上最优泄漏排序的主结论。该参数因此保持为假设敏感性。首位概率约 0.34 说明名义最优在多参数扰动下有稳定倾向，同时排序仍依赖 LCx 基线与收紧斜率假设。

---

## 7 结论

本文给出文献锚定的一层代理，用于在明确假设下对间接二尖瓣成形情景做探索性排序。主要可核验结论如下。

1. 在 seed=42 与留出 Galili 子集上，折内响应模型 ROA MAE 为 6.37 mm²，泄漏 MAE 为 0.245 pp。IMA-AP 70% 折内绝对误差为 6.60 mm² / 0.198 pp。
2. 当前阻尼后规则路径诊断留出 MAE 为 5.24 mm² / 0.043 pp。论文排序采用 `fitted_response`，以获得一致的表外响应面。
3. 规划图下 35 个装置候选中 30 个可行。最优可行候选为 IMA-CS 桥缩短 20%，AP 减小 11.0%，泄漏代理 0.391%，CS–LCx 为 8.6 mm。
4. LHS（$N=120$）给出 $P(\mathrm{top\text{-}1})=0.342$，平均可行比例 0.822。$\eta\pm 20\%$ 敏感性保持同一名义最优设定，同时改变实现的 AP 减小。
5. 峰缩期 Galili AP 事实、MAVERIC 作为 ARTO（IMA-AP 类）的归属，以及双缝作为假设敏感性，是解释上述排序所必需的语义边界。

请按方法 / 科研软件与探索性筛查引用本文。本文不作为临床术前决策支持引用。

---

## 8 数据与代码可用性

- 代码：https://github.com/Coucou2016/fmr-ima-layer1-planner
- 许可证：MIT（`LICENSE`）
- 引用文件：`CITATION.cff` · `references.bib`
- 模型卡：`MODEL_CARD.md` · 数据来源：`DATA_PROVENANCE.md`
- 主要产物：`results/output/planner/scenario_ranking.json`、`results/output/cross_validation/summary.json`、`results/output/paper_tables/`、`results/output/paper_figures/`

---

## 图注

**图 1.** Galili 峰缩期 AP 映射与临床 $\eta$ 映射下，IMA-AP 泄漏代理随缝线缩短的变化。阴影带标出探索性 14%–20% AP 规划区间在缝线百分比空间中的位置。

**图 2.** 装置缩短到 AP 直径减小的映射。曲线分别对应 Galili IMA-AP、临床 IMA-AP（$\eta=0.30$）与临床 IMA-CS（$\eta=0.55$ 假设先验）。水平带为探索性规划区间。

**图 3.** ROA 交界比例与射流位置标签随缩短变化（Galili 与临床面板；方块为 IMA-AP，圆点为 IMA-CS）。

**图 4.** IMA-CS 临床图 Pareto / 风险筛视图：泄漏代理对 CS–LCx 距离与对 NiTi 交变应变。竖直虚线分别标记 Rottländer 8.6 mm 筛与 0.4% 工程应变筛。

**图 5.** 双缝交界因子敏感性（0.25 / 0.5 / 0.75 / 1.0）相对单缝基线。该参数为假设参数，不是发现主张。

---

## 参考文献

1. Galili L, White Zeira A, Marom G. Numerical biomechanics modelling of indirect mitral annuloplasty treatments for functional mitral regurgitation. *R Soc Open Sci.* 2022;9:211464. doi:10.1098/rsos.211464

2. Galili L, White Zeira A, Marom G. Data from: Numerical biomechanics modelling of indirect mitral annuloplasty treatments for functional mitral regurgitation. Dryad. 2022. doi:10.5061/dryad.bzkh1899d

3. Worthley S, Redwood S, Hildick-Smith D, et al. Transcatheter reshaping of the mitral annulus in patients with functional mitral regurgitation: one-year outcomes of the MAVERIC trial. *EuroIntervention.* 2021. doi:10.4244/EIJ-D-20-00484（MAVERIC 评价 ARTO；IMA-AP 类）

4. Rottländer D, et al. Procedural planning of CS-based indirect mitral annuloplasty using CT-angiography. *Catheter Cardiovasc Interv.* 2021. doi:10.1002/ccd.29824

5. Rottländer D, et al. Anatomy and topography of coronary sinus and mitral valve annulus in functional mitral regurgitation. *Front Cardiovasc Med.* 2022;9:868562. doi:10.3389/fcvm.2022.868562

6. Witte KK, et al. A randomized sham-controlled study of the safety and efficacy of the Carillon mitral contour system in patients with functional mitral regurgitation (REDUCE-FMR). *JACC Heart Fail.* 2019.（IMA-CS / Carillon 类方向性）
