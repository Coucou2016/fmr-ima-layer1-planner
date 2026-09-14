# Literature-anchored Layer-1 surrogate for exploratory screening of indirect mitral annuloplasty

**Working short title:** FMR IMA Layer-1 exploratory surrogate (software / methods)

**Venue class:** computational biomechanics / research-software methods paper (CMBBE / MedEngPhys / RSOS-class) — not a clinical decision trial.

**One-sentence argument:** We provide a transparent, literature-anchored algebraic surrogate that reproduces selected Galili peak-systole anchors, supports Dryad-aware provenance, reports true fold-wise response-model cross-validation (and a separate blend-off diagnostic), and ranks exploratory IMA-CS / IMA-AP scenarios under explicit geometric and η assumption-prior uncertainty — without claiming new LHHM FEA, clinical recommendation, or patient-level external validation.

**Data / reproduce:** `python run_pipeline.py --seed 42 --paper` · `python tools/import_galili_dryad.py --from-fixture --process` · `python -m analysis.fit_response_model --write` · `python tools/loo_evaluate.py --write`

**Verification levels:** Level 0 = calibrated to / reproduced selected Galili cases; Level 1 = exploratory planning map + uncertainty-aware scenario ranker + fold-wise response diagnostic. Level 2 patient-specific LHHM/FSI is out of scope.

---

## Abstract

**Background.** Computational IMA studies (Galili et al., *R. Soc. Open Sci.* 2022; doi:10.1098/rsos.211464; title: *Numerical biomechanics modelling of indirect mitral annuloplasty treatments for functional mitral regurgitation*) report suture/bridge shortening with peak-systolic geometry and leakage. Peak-systolic IMA-AP 50% yields AP **15.9 mm** (near-direct AP effect), not undeformed diastole **34.4 mm**. Device classes differ: MAVERIC evaluates **ARTO** (CS–IAS / IMA-AP-class); Carillon / REDUCE-FMR are IMA-CS-class.

**Methods.** We implement a reproducible Python Layer-1 surrogate: phenomenological mechanics plus a literature-calibrated leakage proxy, with a config-switched response path (`fitted_response` default for paper ranking; `rule_based_proxy` retained for diagnostics). Dryad (doi:10.5061/dryad.bzkh1899d) supplies primary provenance **and** an auxiliary model feature `contact_fraction` (interpolated for off-table design points); scalar AP/ROA/leakage remain table-backed unless derivable. We fit fold-wise response models `f_ROA(ΔAP, device family, annular reduction, contact_fraction)` and `f_leak(ROA, coaptation proxy, contact, device mechanism)` under true leave-one-case-out, and a full-train fit for ranking. A discrete scenario ranker minimizes `leakage_proxy_pct` subject to an AP ceiling, an illustrative NiTi engineering screen, and a Rottländer CS–LCx risk-screening threshold, reporting device-candidate P(feasible), Latin-Hypercube multi-parameter ranking stability (η_AP, η_CS, dual factor, CS–LCx baseline/slope; N≈120), and family-separated Pareto frontiers. Dual-suture commissural factor is an exploratory hypothesis **sensitivity** parameter (Fig. 5: 0.25/0.5/0.75/1.0), not a discovery claim. Ranking is assumption-driven exploratory analysis, not validated prediction.

**Results (seed=42).** Fold-wise response-model CV on the held-out Galili subset improves ROA MAE from rule-based blend-off **50.18 mm²** to about **6.37 mm²** and leak MAE from **1.445** to about **0.245** percentage points; IMA-AP 70% absolute ROA/leak errors fall from **94.17 mm² / 5.455 pp** to about **6.60 mm² / 0.198 pp** (internal engineering targets, not medical validation). Further dampening of stacked rule-based AP70 penalties reduces Galili-mapped AP70 leak from historical **≈2.46%** to **≈1.21%** (still overestimates Galili **0.13%**; paper ranking uses `fitted_response`). Under the planning map the ranker evaluates **36** total points (**35** device candidates; pathology is not a candidate) and retains **30** feasible designs (**p_feasible_device_candidates≈0.857**). With `fitted_response`, seed-42 best candidate is **IMA-CS 20%** (AP↓ 11%, leakage proxy ≈0.39%); dual-suture AP60 remains an assumption-sensitive alternative under the nominal dual hypothesis (not Innovation D discovery). LHS UQ (N=120) yields **P(top-1)≈0.34** and mean feasible fraction ≈0.82.

**Conclusions.** A literature-anchored low-order surrogate can support **exploratory screening** of IMA strategy settings with inspectable assumptions, honest held-out reporting, and uncertainty language. It is not a preoperative clinical decision system and must not equate physics % with clinical regurgitant volume.

**Keywords:** functional mitral regurgitation; indirect mitral annuloplasty; surrogate model; exploratory screening; research software; Layer-1

---

## 1. Introduction

Functional mitral regurgitation (FMR) reflects ventricular remodeling, annular dilatation, and impaired leaflet coaptation. Indirect mitral annuloplasty (IMA) concepts remodel annular geometry without direct leaflet repair. **IMA-CS** (Carillon-class) and **IMA-AP** (CS–IAS; ARTO / MAVERIC mechanism class) are not mechanically interchangeable.

Galili et al. (2022) compared generic IMA-CS and IMA-AP in the Living Heart Human Model. IMA-AP acts nearly directly on peak-systolic AP (disease 26.1 mm → IMA-AP 50% → **15.9 mm**). Undeformed diastolic AP 34.4 mm is a different cardiac phase.

What remains for software methods is transparent **dose translation, provenance, held-out honesty, and exploratory ranking** under stated assumptions—not a claim of first CS-vs-AP comparison, not new FEA, and not a clinical recommendation engine.

## 2. Related work and positioning

Galili RSOS 2022 (doi:10.1098/rsos.211464) + Dryad supporting files provide the computational leakage/ROA/AP table we anchor to. Clinical series (ARTO/MAVERIC; Carillon TITAN II; REDUCE-FMR) supply **directional / geometric context only**. This paper contributes research-software packaging, fold-wise response diagnostics, and an inspectable Layer-1 ranker, not a new high-fidelity FSI study.

## 3. Software architecture

```
configs/   surrogate_calibration.yaml, design_space.yaml, case YAML
models/    geometry, pathology, devices, response_model (fold-wise f_ROA / f_leak)
simulation/ phenomenological mechanics proxy (legacy alias run_fea_surrogate)
sph/       literature-calibrated leakage proxy (SPH-inspired; not a full SPH solver)
analysis/  ROA, jet, sweep, scenario_ranker, fit_response_model, paper tables/plots
tools/     import_galili_dryad.py, loo_evaluate.py (blend-off diagnostic), package_reports.py
data/      raw drop zone, fixtures, processed galili_cases.csv
results/output/cross_validation/  true fold-wise CV artifacts
```

Runnable entry points: `run_pipeline.py`, `python -m analysis.planner`, `python -m analysis.fit_response_model`, `python -m analysis.design_sweep`.

## 4. Methods

**Pathology and geometry.** Parametric papillary pathology (44% posterior passive). Undeformed diastole and peak systole are separate `cardiac_phase` records. AP diameter is a literature-defined geometry **input** (`ap_role: literature_mapping_input`); AP MAE is not reported as predictive accuracy.

**Device kinematics.** Galili mode interpolates published peak-systolic AP; clinical/planning mode uses assumption-prior η or preferred ΔAP. η_CS is **not** fitted from MAVERIC/ARTO. Default uncertainty uses Latin Hypercube over η_AP ∈ U(0.24,0.36), η_CS ∈ U(0.44,0.66), dual commissural factor, CS–LCx baseline, and cinch slope (N documented in `design_space.yaml`).

**Mechanics and leakage proxies.** Algebraic coaptation-gap / strain / contact proxy scores. Leakage proxy is literature-calibrated at pathology; `_sph_scale` is the pathology regurgitation fraction identity. Physics regurg % ≠ clinical regurgitant volume. Synthetic contact-cluster ROA is visualization-only (`model_weight=1`, `cluster_weight=0`); Dryad `contact_fraction` enters the fitted response path as a science feature. Official export fields: `leakage_proxy_pct`, `strain_risk_score`, `contact_score` (legacy aliases retained).

**Response paths.** `configs/design_space.yaml` `response_path`: `fitted_response` (paper/seed-42 default), `rule_based_proxy` (legacy exploratory), or `hybrid_ap_extreme` (rule-based with AP-class over-short routed to fitted).

**Provenance.** `tools/import_galili_dryad.py` downloads or documents manual drop; extracts Dryad `contact_fraction` and `n_sph_particles`. Scalar AP/ROA/leakage remain table-backed (not invented from unlabeled leaflet nodes).

**Diagnostics vs true CV.** `tools/loo_evaluate.py` is an **anchor-free / leave-one-case blend-off diagnostic** on the fixed rule-based surrogate (not fold-wise refit). `analysis/fit_response_model.py` performs **true fold-wise** fitting with held ROA/leak excluded from train arrays. Full-train params for ranking live under `results/output/response_model/`.

**Scenario ranker.** Minimizes `leakage_proxy_pct`; reports `n_total_points`, `n_device_candidates`, `n_feasible_device_candidates`, `p_feasible_device_candidates`, `P(top-1)`, and first-order Spearman sensitivity ranks. Pareto families: `pareto_global_common_objectives` (min leak, max AP↓), `pareto_ima_cs_family` (adds LCx/NiTi), `pareto_ima_ap_family`. Missing LCx/NiTi are never filled with 1e9/0. Dual-suture factor is an explicit hypothesis **sensitivity** (Fig. 5), not discovery. LCx prefers patient-measured baseline. The 14–20% AP band is a clinically contextualized **exploratory planning range** (anchor ~14–15%, ceiling 20%; legacy `clinical_window` alias only).

## 5. Results

### 5.1 Data provenance

Dryad archives yield deformed-contact and SPH coordinate files. Processed table `data/processed/galili_cases.csv` marks `source_tier=dryad_derived` for extracted `contact_fraction` and `n_sph_particles`. Published peak-systole AP, ROA, and leakage scalars remain table-backed fills — the importer does **not** extract independent AP, ROA, and leakage descriptors from unlabeled coordinates alone.

### 5.2 Calibration reproduction

| Case | Leakage % | Peak-sys AP mm | ROA mm² |
|------|-----------|----------------|---------|
| pathology | 5.26 | 26.1 | 172.8 |
| ima_cs_22 | 0.29 | 24.8 | 48.2 |
| ima_ap_50 | 0.08 | **15.9** | 27.3 |
| ima_ap_70 | 0.13 | 12.4 | 46.1 |

Calibration IDs with blend ON are reproduction only.

### 5.3 Anchor-free diagnostic and true fold-wise CV (includes AP70 failure/improvement)

**Rule-based blend-off diagnostic** (`tools/loo_evaluate.py`, held-out IDs): historical pre-dampen baseline MAE ROA **50.18 mm²**, leak **1.445 pp**; IMA-AP 70% previously **140.3 / 5.585%** (abs err **94.17 / 5.455**). Current dampened rule-based held-out MAE ≈ **28.6 mm² / 0.66 pp**. Critically, the rule-based path **captures a qualitative non-monotonic tendency** (Galili AP50 leak 0.08% → AP70 0.13%) but **substantially overestimates AP70 leak magnitude** (pred ≈2.46% vs published 0.13%; abs err ≈2.33 pp) — this is **not** an unqualified claim that the surrogate “reproduces Galili non-monotonic behavior.”

**True fold-wise response-model LOO** (`analysis/fit_response_model.py` → `results/output/cross_validation/`): held-out-subset MAE ROA ≈ **6.4 mm²**, leak ≈ **0.25 pp**; AP70 abs err ≈ **6.6 mm² / 0.20 pp**. Internal engineering targets (ROA MAE < 25, leak MAE < 0.5, AP70 ROA < 25, AP70 leak < 0.5) are met on this seven-case table — **not** patient-level external validation. Full seven-fold MAE remains inflated by the pathology leave-out (large ROA scale gap). AP is literature geometry input (`ap_prediction_metric_applicable=false`).

**Full held-out table (CS14 / CS18 / AP30 / AP70)** — published vs rule-based blend-off vs fold-wise response model:

| Case | Pub ROA | Rule ROA (abs err) | Fold ROA (abs err) | Pub leak % | Rule leak (abs err pp) | Fold leak (abs err pp) |
|------|---------|--------------------|--------------------|------------|------------------------|------------------------|
| ima_cs_14 | 56.7 | 24.0 (32.7) | 69.6 (12.9) | 0.52 | 0.65 (0.13) | 0.60 (0.08) |
| ima_cs_18 | 55.3 | 17.6 (37.7) | 53.4 (1.9) | 0.41 | 0.34 (0.07) | 0.42 (0.01) |
| ima_ap_30 | 51.1 | 14.9 (36.2) | 47.0 (4.1) | 0.16 | 0.28 (0.12) | 0.86 (0.70) |
| **ima_ap_70** | **46.1** | **~35.6 (~10.5)** | **39.5 (6.6)** | **0.13** | **~1.21 (~1.08)** | **0.33 (0.20)** |

AP70 row is reported front-and-center: fold-wise meets internal engineering screens; dampened rule-based leak improved from historical ≈2.46% but still overestimates Galili 0.13% — paper ranking prefers `fitted_response`.

### 5.4 Exploratory scenario ranking (planning map, seed=42; `fitted_response`)

- **n_total_points=36**, **n_device_candidates=35**, **n_feasible_device_candidates=30**, **p_feasible_device_candidates≈0.857**
- With default **`response_path=fitted_response`**, best candidate ranked **IMA-CS bridge 20%** (η_cs=0.55 → AP reduction **11.0%**, leakage proxy **≈0.39%**, jet=`central`, CS–LCx **8.6 mm** at risk-screen edge)
- Dual-suture AP60 remains an assumption-sensitive alternative under the **nominal dual-suture hypothesis** (Fig. 5 = factor sensitivity 0.25/0.5/0.75/1.0, **not** Innovation D discovery)
- LHS multi-parameter UQ (N=120): **P(top-1)≈0.34**, mean feasible fraction ≈0.82; first-order Spearman ranks dominated by CS–LCx baseline/slope
- Pareto: global common objectives; CS/AP family frontiers without N/A fillers

### 5.5 Directionality-only clinical context

ARTO/MAVERIC: AP↓. Carillon TITAN II: ~15% AP context. REDUCE-FMR: regurg↓. Magnitudes not equated to physics %.

## 6. Discussion / limitations

Central advance: transparent exploratory screening software with corrected Galili peak-systole AP semantics, MAVERIC=ARTO mapping, Dryad `contact_fraction` in the fitted path, honest held-out/CV reporting (including AP70), LHS ranking stability, and family-correct Pareto language.

**Irreducible limits (documented, not faked):**
- **n=7** Galili peak-systole table cases — not patient-level external validation
- **No patient CT** / patient-specific chamber geometry
- **No chamber-labeled SPH leakage recompute** from Dryad particle clouds (full-domain cloud only; AP/ROA/leak remain table-backed)
- Algebraic / phenomenological proxies; η and dual factor are assumption priors
- LCx/NiTi screens are literature/engineering screens, not safety clearances
- Rule-based AP70 still overestimates leak magnitude vs Galili even after dampening; prefer fitted path for ranking

## 7. Availability

- Code: https://github.com/Coucou2016/fmr-ima-layer1-planner
- License: MIT (`LICENSE`)
- Citation: `CITATION.cff` · `references.bib`
- Model card: `MODEL_CARD.md` · Data: `DATA_PROVENANCE.md`

## 8. Conclusion

A Layer-1 literature-anchored surrogate can rank exploratory IMA scenarios under explicit assumptions after correcting peak-systole Galili AP facts and MAVERIC device-class attribution, and after reporting true fold-wise response diagnostics alongside a renamed blend-off casewise diagnostic. Cite as methods/software for exploratory screening—not as clinical preoperative decision support.

---

*Collab notes:* `docs/chatgpt_collab/20260913_p0_review_response.md`, `docs/chatgpt_collab/20260914_p1p2_implementation.md`, `docs/chatgpt_collab/20260914_round2_major_revision.md`, `docs/chatgpt_collab/20260915_r2_major_revision.md`
