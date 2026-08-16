# 论文计划 / Paper plan

Layer-1 **surrogate** for preoperative IMA planning. This is **not** a new LHHM/Abaqus FSI paper and must not be written as one.

---

## Title / 题目

**EN:** Clinically constrained preoperative planning of indirect mitral annuloplasty: mapping suture dose to AP-diameter reduction, jet location, and LCx safety on a Layer-1 surrogate

**中:** 临床约束下的间接二尖瓣成形术术前规划：在一层代理模型上将缝线剂量映射到前后径缩减、反流束位置与回旋支安全

Working short title: *Clinical-dose IMA planner (Layer-1)*

---

## Contributions / 贡献点（C1–C3）

### C1 — Innovation A / 创新 A：临床剂量映射

Map **suture / bridge shortening %** onto **clinically attainable AP diameter reduction** (mm and %), instead of treating Galili’s 30/50/70% suture settings as if they were 30/50/70% AP cinch.

- MAVERIC window: 41.4 → 35.3 mm ≈ **14.7%**; 45.0 → 38.7 mm ≈ **14%**.
- Planning ceiling (default): **20%** AP reduction.
- Galili 50% suture = **0%** AP reduction in LHHM; Galili 70% = **~58%** AP reduction (14.3 mm) — numerical extreme, not a clinical dose.
- Transfer efficiency `eta` is a **documented planning assumption** (`configs/design_space.yaml`, `results/clinical_references.yaml`), not a new FEA result.

### C2 — Innovation E / 创新 E：可部署的术前设计优化代理

Continuous design-space scan + constrained grid search on the existing Python surrogate (FEA+SPH reduced-order), intended as a **preoperative planner**, not a solver replacement.

- IMA-AP: 10–70% step 5%
- IMA-CS: 10–25% step 2%
- Objective: minimize **physics** regurgitation (no YAML blend on sweep IDs)
- Output: recommended shortening + predicted `jet_location`

### C3 — Innovation C / 创新 C：LCx 安全约束

IMA-CS constraint: distal-landing-zone **CS–LCx ≥ 8.6 mm** (Rottländer 2021). Baseline CS–LCx is a patient CT input (illustrative default 11.0 mm). NiTi **alternating** strain &lt; 0.4% is a second IMA-CS constraint.

### Optional C4 — Innovation D / 可选：双缝线

Dual vs single IMA-AP suture for commissural leak at the same AP reduction (`n_sutures=2`).

---

## Methods outline / 方法提纲（mapped to modules）

| Step / 步骤 | Module |
|-------------|--------|
| Pathology + parametric annulus | `models/pathology.py`, `models/heart_geometry.py` |
| Device kinematics, Galili vs clinical mapping, CS–LCx, dual suture | `models/devices.py`, `configs/design_space.yaml` |
| Reduced-order FEA (gap, strain) | `simulation/run_case.py` |
| ROA (physics estimate; cluster only in discrete pipeline) | `simulation/roa_surrogate.py` |
| SPH leak index → physics regurgitation | `sph/hemodynamics.py` |
| Jet location ∈ {central, commissural, mixed}; ROA split | `analysis/jet.py` |
| Continuous sweep | `analysis/design_sweep.py`, `python -m analysis.design_sweep` |
| Constrained planner (grid search) | `analysis/planner.py`, `python -m analysis.planner` |
| Paper tables / figures | `analysis/paper_tables.py`, `analysis/plots.py` |
| Clinical citations | `results/clinical_references.yaml` |
| Galili anchor blend (validation cases only) | `configs/surrogate_calibration.yaml`, `run_pipeline.py` |

**Honesty:** main paper figures use `physics_regurgitation_pct`. YAML blend is restricted to Galili case IDs (`pathology`, `ima_cs_22`, `ima_ap_50`) for validation tables.

---

## Figure list / 图清单 → generated PNGs

| Fig | Content / 内容 | File |
|-----|----------------|------|
| Fig 1 | Non-monotonic IMA-AP physics regurg vs suture %; clinical window overlay | `results/output/paper_figures/fig1_ima_ap_nonmonotonic_clinical_window.png` |
| Fig 2 | Suture/bridge % vs AP reduction % (Galili vs clinical vs MAVERIC band) | `results/output/paper_figures/fig2_suture_vs_ap_reduction.png` |
| Fig 3 | Jet location / commissural fraction vs shortening | `results/output/paper_figures/fig3_jet_location.png` |
| Fig 4 | Pareto: regurg vs CS–LCx and vs NiTi alternating strain | `results/output/paper_figures/fig4_pareto_lcx_strain.png` |
| Fig 5 | Dual vs single suture (commissural fraction) | `results/output/paper_figures/fig5_dual_vs_single_suture.png` |

Tables in `results/output/paper_tables/`:

- `galili_vs_surrogate.csv` — published vs blended vs physics
- `clinical_window_vs_numerical_extreme.csv` — 15% window vs Galili 50%/70%
- `pareto_regurg_vs_safety.csv` — feasible set
- `maveric_reduce_fmr_alignment.csv` — directionality-only vs MAVERIC/REDUCE-FMR
- `dual_vs_single_matched_ap.csv` — Innovation D at matched AP reduction
- `eta_sensitivity.csv` / `.json` — planner shift under η±20%

Manuscript scaffold: `docs/manuscript_draft.md` (Chinese primary; seed-42 numbers).

---

## Validation levels / 验证层级

| Level | Meaning / 含义 | Status in this repo |
|-------|----------------|---------------------|
| **0** | Reproduce Galili published anchors on the discrete YAML cases (regurg %, ROA min, annulus/AP geometry, 50% optimum, 70% worse) | Implemented; pytest |
| **1** | Surrogate sweep + clinical dose mapping + planner constraints (this work) | Implemented; physics-only figures |
| **2** | Patient-specific LHHM / full FSI / Abaqus UMAT / 29k true SPH | **Out of scope.** Export hooks only (`simulation/fea_export.py`) |

Do not present Level-1 curves as Level-2 FEA.

---

## Limitations / 局限

1. Reduced-order FEA and SPH; no live Abaqus/LHHM coupling.
2. Clinical `eta` is an assumption so surgeons can talk in AP-mm; it is not identified from new imaging-FEA pairs.
3. Default CS–LCx anatomy (11 mm) is illustrative; the constraint is the 8.6 mm threshold plus a CT input.
4. Jet classifier splits surrogate ROA; it is not echocardiographic PISA/Doppler.
5. Grid search reports stepped implant settings; it does not invent a continuous Carillon “dial”.
6. Dual-suture series is a mechanism sketch (Innovation D), not a device clearance study.

---

## How to generate paper artifacts / 如何生成

```powershell
python run_pipeline.py --seed 42 --paper
# or
python -m analysis.design_sweep --paper --seed 42
python -m analysis.planner --seed 42
```
