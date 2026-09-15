# A literature-anchored Layer-1 surrogate for exploratory screening of indirect mitral annuloplasty

**Short title:** FMR IMA Layer-1 exploratory surrogate

**Venue class:** computational biomechanics / research-software methods (CMBBE / *Medical Engineering & Physics* / *Royal Society Open Science*-class). This is not a clinical decision trial.

**One-sentence argument.** We release a transparent, literature-anchored algebraic surrogate that reproduces selected Galili peak-systole anchors, incorporates Dryad-derived contact features, reports true fold-wise response-model cross-validation alongside a separate rule-based blend-off diagnostic, and ranks exploratory IMA-CS / IMA-AP scenarios under explicit geometric and transfer-efficiency assumptions—without claiming new Living Heart Human Model (LHHM) finite-element analysis (FEA), clinical recommendation, or patient-level external validation.

**Reproducibility.** `python run_pipeline.py --seed 42 --paper` · `python tools/import_galili_dryad.py --from-fixture --process` · `python -m analysis.fit_response_model --write` · `python tools/loo_evaluate.py --write`

**Verification levels.** Level 0 = calibrated to / reproduced selected Galili cases. Level 1 = exploratory planning map + uncertainty-aware scenario ranker + fold-wise response diagnostic. Level 2 patient-specific LHHM / fluid–structure interaction (FSI) is out of scope.

---

## Abstract

**Background.** Computational studies of indirect mitral annuloplasty (IMA) report suture or bridge shortening together with peak-systolic geometry and leakage. Galili et al. (*R. Soc. Open Sci.* 2022; doi:10.1098/rsos.211464) compared generic coronary-sinus (IMA-CS) and anteroposterior (IMA-AP) strategies in the LHHM. Peak-systolic IMA-AP at 50% shortening yields an anteroposterior (AP) diameter of 15.9 mm (near-direct AP effect relative to disease 26.1 mm), which must not be confused with undeformed diastolic AP of 34.4 mm. Device classes also differ clinically: MAVERIC evaluates ARTO (CS–interatrial septum / IMA-AP-class), whereas Carillon and REDUCE-FMR are IMA-CS-class.

**Methods.** We implement a reproducible Python Layer-1 surrogate that couples phenomenological mechanics with a literature-calibrated leakage proxy. A configuration switch selects the response path used for ranking (`fitted_response` is the seed-42 paper default; `rule_based_proxy` is retained for diagnostics). Dryad supporting files (doi:10.5061/dryad.bzkh1899d) supply provenance and an auxiliary feature `contact_fraction` (interpolated off-table); scalar AP, regurgitant orifice area (ROA), and leakage remain table-backed unless independently derivable. Fold-wise response models \(f_{\mathrm{ROA}}(\Delta\mathrm{AP},\ \mathrm{device\ family},\ \mathrm{annular\ reduction},\ \mathrm{contact\_fraction})\) and \(f_{\mathrm{leak}}(\mathrm{ROA},\ \mathrm{coaptation\ proxy},\ \mathrm{contact},\ \mathrm{device\ mechanism})\) are fitted under true leave-one-case-out; a full-train fit supports ranking. A discrete scenario ranker minimizes `leakage_proxy_pct` subject to an AP-reduction ceiling, an illustrative nickel–titanium (NiTi) engineering screen, and a Rottländer coronary sinus–left circumflex (CS–LCx) risk-screening threshold. Latin-hypercube sampling (LHS; \(N=120\)) probes multi-parameter ranking stability. The dual-suture commissural factor is treated as hypothesis sensitivity (Figure 5), not discovery.

**Results (seed = 42).** On the held-out Galili subset, fold-wise response-model cross-validation (CV) achieves ROA mean absolute error (MAE) ≈ 6.37 mm² and leak MAE ≈ 0.245 percentage points (pp), versus a documented pre-dampen rule-based blend-off baseline of 50.18 mm² / 1.445 pp. For IMA-AP 70%, fold-wise absolute errors fall to ≈ 6.60 mm² / 0.198 pp (internal engineering screens only—not medical validation). The current dampened rule-based diagnostic yields held-out MAE ≈ 5.24 mm² / 0.043 pp; for IMA-AP 70% it predicts leak ≈ 0.07% against published 0.13% (absolute error ≈ 0.06 pp). Paper ranking therefore uses `fitted_response` for a consistent off-table response surface, not because every scalar is worse under the rule-based path. Under the planning map the ranker evaluates 36 grid points (35 device candidates) and retains 30 feasible designs (\(p_{\mathrm{feasible}}\approx 0.857\)). The best feasible candidate is IMA-CS bridge shortening 20% (AP reduction 11%; leakage proxy ≈ 0.39%; jet = central; CS–LCx = 8.6 mm at the risk-screen edge). LHS uncertainty quantification (UQ) yields \(P(\mathrm{top\text{-}1})\approx 0.34\) and mean feasible fraction ≈ 0.82.

**Conclusions.** A literature-anchored low-order surrogate can support exploratory screening of IMA strategy settings with inspectable assumptions, honest held-out reporting, and uncertainty language. It is not a preoperative clinical decision system and must not equate physics leakage-proxy percentages with clinical regurgitant volume.

**Keywords:** functional mitral regurgitation; indirect mitral annuloplasty; surrogate model; exploratory screening; research software; Layer-1

**中文摘要.** 背景：功能性质二尖瓣反流（FMR）的间接成形（IMA）计算研究需区分峰缩期前后径（AP）与舒张期几何，并区分 IMA-CS 与 IMA-AP 装置类别。方法：本文给出可复现的 Python 一层代数/现象学代理，结合 Dryad 接触特征、折内响应模型交叉验证与情景排序。结果（seed=42）：折内留出子集 ROA MAE≈6.37 mm²、泄漏 MAE≈0.245 pp；排序最优候选为 IMA-CS 20%（AP↓11%，泄漏代理≈0.39%）。结论：可用于假设透明的探索性筛查，而非临床术前决策或患者级外部验证。

---

## 1. Introduction

Functional mitral regurgitation (FMR) arises from ventricular remodelling, annular dilatation, and impaired leaflet coaptation rather than primary leaflet disease alone. Indirect mitral annuloplasty (IMA) seeks to remodel annular geometry without direct leaflet repair. Two computational device families recur in the literature: IMA-CS (coronary-sinus bridge shortening; Carillon-class clinically) and IMA-AP (CS–interatrial-septum suture shortening that acts primarily on the anteroposterior diameter; ARTO / MAVERIC mechanism class). These pathways are not mechanically interchangeable.

Galili, White Zeira and Marom (2022) compared generic IMA-CS and IMA-AP treatments in the Living Heart Human Model and quantified leakage after device deployment. Their peak-systolic IMA-AP 50% case yields AP = 15.9 mm, illustrating a near-direct AP effect; undeformed diastolic AP = 34.4 mm belongs to a different cardiac phase and must not be substituted into peak-systole dose statements. Clinical series supply geometric context at different scales: ARTO/MAVERIC reports AP reductions of order 14–15% for an IMA-AP-class device, whereas Carillon / TITAN II and REDUCE-FMR inform IMA-CS directionality.

What remains for research software is transparent dose translation, provenance, held-out honesty, and exploratory ranking under stated assumptions. The present work does not claim the first computational CS-versus-AP comparison, does not introduce new LHHM FEA, and does not offer a clinical recommendation engine.

## 2. Related work and positioning

We imitate the *structure* of high-fidelity IMA modelling papers and modular mitral-valve methods tools while contributing a complementary Layer-1 software layer:

| Role | Source | What we imitate | What we do not claim |
|------|--------|-----------------|----------------------|
| Mechanistic FEA baseline | Galili et al., *R. Soc. Open Sci.* 2022;9:211464 | mechanism → parameterization → geometry → functional readout; IMA-CS vs IMA-AP taxonomy | new LHHM/FEA/SPH; “first CS vs AP” |
| Clinical AP context | Worthley / MAVERIC (ARTO) | separate geometry endpoints from MR endpoints | calibration of physics % to clinical MR volume |
| CS directionality | Witte et al., REDUCE-FMR; Carillon TITAN II | restrained causal language; coronary awareness | validation against trial magnitudes |
| LCx screening vocabulary | Rottländer et al., 2021 | feasible vs infeasible screening language at CS–LCx ≈ 8.6 mm | “≥8.6 mm is proven safe” |
| Methods-tool tone | geometry-based MV FE tools (e.g. *Med Eng Phys* / *CMBBE* modular studies) | modular Methods; isolated-variable sweeps | FE stress/contact as ground truth for our proxies |

This paper contributes research-software packaging, Dryad-aware contact features in a fitted response path, fold-wise response diagnostics, and an inspectable Layer-1 scenario ranker—not a new high-fidelity FSI study.

## 3. Software architecture

```
configs/    surrogate_calibration.yaml, design_space.yaml, case YAML
models/     geometry, pathology, devices, response_model (fold-wise f_ROA / f_leak)
simulation/ phenomenological mechanics proxy (legacy alias run_fea_surrogate)
sph/        literature-calibrated leakage proxy (SPH-inspired; not a full SPH solver)
analysis/   ROA, jet, sweep, scenario_ranker, fit_response_model, paper tables/plots
tools/      import_galili_dryad.py, loo_evaluate.py, package_reports.py
data/       raw drop zone, fixtures, processed galili_cases.csv
results/output/cross_validation/   true fold-wise CV artifacts
results/output/planner/            scenario_ranking.json (seed-42 ranking)
```

Entry points include `run_pipeline.py`, `python -m analysis.planner`, `python -m analysis.fit_response_model`, and `python -m analysis.design_sweep`.

## 4. Methods

### 4.1 Pathology and geometry

A parametric papillary pathology (approximately 44% posterior passive fraction) defines the diseased baseline. Undeformed diastole and peak systole are stored as separate `cardiac_phase` records. AP diameter is a literature-defined geometry input (`ap_role: literature_mapping_input`); AP MAE is therefore not reported as predictive accuracy.

### 4.2 Device kinematics and transfer efficiency

In Galili mapping mode, peak-systolic AP follows published table coordinates (interpolation between discrete Galili cases). In clinical / planning mode, AP reduction is \(\mathrm{AP\_reduction\%}=\eta\times\mathrm{shortening\%}\) with assumption-prior means \(\eta_{\mathrm{AP}}=0.30\) and \(\eta_{\mathrm{CS}}=0.55\). \(\eta_{\mathrm{CS}}\) is **not** fitted from MAVERIC/ARTO. Default UQ uses Latin hypercube sampling over \(\eta_{\mathrm{AP}}\in U(0.24,0.36)\), \(\eta_{\mathrm{CS}}\in U(0.44,0.66)\), dual commissural factor, CS–LCx baseline, and cinch slope (\(N=120\) as configured in `design_space.yaml`).

### 4.3 Mechanics and leakage proxies

Algebraic coaptation-gap, strain, and contact-proxy scores constitute the phenomenological mechanics channel. The leakage proxy is literature-calibrated at the pathology case; physics regurgitation percentage is **not** clinical regurgitant volume. Synthetic contact-cluster ROA is visualization-only (`model_weight=1`, `cluster_weight=0`). Dryad `contact_fraction` enters the fitted response path as a scientific feature. Official export fields are `leakage_proxy_pct`, `strain_risk_score`, and `contact_score` (legacy aliases retained for compatibility).

### 4.4 Response paths

`configs/design_space.yaml` sets `response_path` to one of:

- `fitted_response` — paper / seed-42 default for ranking;
- `rule_based_proxy` — legacy exploratory / diagnostic path;
- `hybrid_ap_extreme` — rule-based with AP-class over-short routed to the fitted surface.

### 4.5 Provenance (Dryad)

`tools/import_galili_dryad.py` documents download or manual drop, then extracts `contact_fraction` and `n_sph_particles` where available. Scalar AP, ROA, and leakage remain table-backed fills; the importer does not invent those scalars from unlabeled leaflet coordinates alone.

### 4.6 Diagnostics versus true fold-wise CV

`tools/loo_evaluate.py` runs an **anchor-free / leave-one-case blend-off diagnostic** on the fixed rule-based surrogate (no fold-wise refit). `analysis/fit_response_model.py` performs **true fold-wise** fitting with held ROA/leak excluded from training arrays. Full-train parameters for ranking are written under `results/output/response_model/`. Cross-validation summaries live under `results/output/cross_validation/`.

### 4.7 Scenario ranker and Pareto families

The ranker minimizes `leakage_proxy_pct` subject to an exploratory AP-reduction ceiling (default 20%), an illustrative NiTi alternating-strain screen (<0.4%), and a CS–LCx risk-screening threshold (≥8.6 mm; labeled screening, not safety clearance). It reports `n_total_points`, `n_device_candidates`, `n_feasible_device_candidates`, `p_feasible_device_candidates`, \(P(\mathrm{top\text{-}1})\), and first-order Spearman sensitivity ranks. Pareto families are separated: global common objectives (min leak, max AP↓); IMA-CS family (adds LCx/NiTi); IMA-AP family. Missing LCx/NiTi values are never replaced with sentinel fillers. The dual-suture commissural factor is an explicit hypothesis sensitivity parameter (Figure 5: 0.25 / 0.5 / 0.75 / 1.0). The 14–20% AP band is a clinically contextualized exploratory planning range (legacy `clinical_window` alias only).

## 5. Results

### 5.1 Data provenance

Processed table `data/processed/galili_cases.csv` marks Dryad-derived `contact_fraction` and `n_sph_particles` with `source_tier=dryad_derived`. Published peak-systole AP, ROA, and leakage scalars remain table-backed.

### 5.2 Calibration reproduction (Level 0)

| Case | Leakage % | Peak-sys AP mm | ROA mm² |
|------|-----------|----------------|---------|
| pathology | 5.26 | 26.1 | 172.8 |
| ima_cs_22 | 0.29 | 24.8 | 48.2 |
| ima_ap_50 | 0.08 | **15.9** | 27.3 |
| ima_ap_70 | 0.13 | 12.4 | 46.1 |

Calibration IDs with blend ON are reproduction only.

### 5.3 Anchor-free diagnostic and true fold-wise CV

**Rule-based blend-off diagnostic** (`tools/loo_evaluate.py`). A documented pre-dampen historical baseline on the held-out IDs reported MAE ROA 50.18 mm² and leak 1.445 pp, with IMA-AP 70% absolute errors 94.17 mm² / 5.455 pp. After rule-based dampening, the current seed-42 diagnostic reports held-out MAE ≈ 5.24 mm² / 0.043 pp. For IMA-AP 70%, current rule-based leak ≈ 0.07% versus published 0.13% (absolute error ≈ 0.06 pp).

**True fold-wise response-model LOO** (`analysis/fit_response_model.py`). Held-out-subset MAE ROA ≈ 6.37 mm² and leak ≈ 0.245 pp; IMA-AP 70% absolute errors ≈ 6.60 mm² / 0.198 pp (pred ROA 39.5 mm² vs 46.1; pred leak 0.33% vs 0.13%). Internal engineering screens (ROA MAE < 25, leak MAE < 0.5, AP70 ROA < 25, AP70 leak < 0.5) are met on this seven-case table—not patient-level external validation. Full seven-fold MAE remains inflated by the pathology leave-out (large ROA scale gap). AP prediction metrics remain inapplicable.

**Held-out table (CS14 / CS18 / AP30 / AP70)** — published versus current rule-based blend-off versus fold-wise response model (seed-42 pipeline outputs):

| Case | Pub ROA | Rule ROA (abs err) | Fold ROA (abs err) | Pub leak % | Rule leak (abs err pp) | Fold leak (abs err pp) |
|------|---------|--------------------|--------------------|------------|------------------------|------------------------|
| ima_cs_14 | 56.7 | 59.6 (2.9) | 69.6 (12.9) | 0.52 | 0.51 (0.01) | 0.60 (0.08) |
| ima_cs_18 | 55.3 | 54.9 (0.4) | 53.4 (1.9) | 0.41 | 0.42 (0.01) | 0.42 (0.01) |
| ima_ap_30 | 51.1 | 42.4 (8.7) | 47.0 (4.1) | 0.16 | 0.25 (0.09) | 0.86 (0.70) |
| **ima_ap_70** | **46.1** | **37.2 (8.9)** | **39.5 (6.6)** | **0.13** | **0.07 (0.06)** | **0.33 (0.20)** |

Paper ranking prefers `fitted_response` for a coherent off-table surface under planning-map kinematics; the rule-based path remains the named blend-off diagnostic.

### 5.4 Exploratory scenario ranking (planning map, seed = 42; `fitted_response`)

- \(n_{\mathrm{total}}=36\), \(n_{\mathrm{device\ candidates}}=35\), \(n_{\mathrm{feasible}}=30\), \(p_{\mathrm{feasible}}\approx 0.857\)
- Best feasible candidate: **IMA-CS bridge 20%** (\(\eta_{\mathrm{CS}}=0.55\) → AP reduction **11.0%**, leakage proxy **≈0.391%**, jet = `central`, CS–LCx **8.6 mm**)
- Best IMA-AP single / dual alternatives under the same constraints remain higher-leakage (≈0.79% at 65% shortening / 19.5% AP↓); dual suture is reported as hypothesis sensitivity (Figure 5), not as Innovation D discovery
- LHS multi-parameter UQ (\(N=120\)): \(P(\mathrm{top\text{-}1})\approx 0.342\), mean feasible fraction ≈ 0.822; first-order Spearman ranks are dominated by CS–LCx baseline and cinch slope
- \(\eta\pm 20\%\) one-at-a-time sensitivity keeps IMA-CS 20% as the nominal top candidate while shifting realized AP reduction (8.8% / 11.0% / 13.2%)

### 5.5 Directionality-only clinical context

ARTO/MAVERIC: AP↓ of order 14–15% (IMA-AP class). Carillon TITAN II: ~15% AP context (IMA-CS class). REDUCE-FMR: regurgitation↓ directionality. Magnitudes are not equated to physics leakage-proxy percentages.

## 6. Discussion

The central contribution is transparent exploratory screening software: corrected Galili peak-systole AP semantics, MAVERIC = ARTO device-class attribution, Dryad `contact_fraction` in the fitted path, honest held-out / CV reporting (including IMA-AP 70%), LHS ranking stability, and family-correct Pareto language.

Relative to Galili’s LHHM study, we do not re-litigate which generic device seals better in high fidelity. Relative to clinical series, we borrow geometric windows and screening vocabulary only. Relative to modular mitral FE tools, we trade continuum fidelity for inspectable assumption priors and rapid grid ranking.

**Limitations (documented, not papered over):**

- \(n=7\) Galili peak-systole table cases — not patient-level external validation
- No patient CT / patient-specific chamber geometry
- No chamber-labeled SPH leakage recompute from Dryad particle clouds (full-domain cloud only; AP/ROA/leak remain table-backed)
- Algebraic / phenomenological proxies; \(\eta\) and dual factor are assumption priors
- LCx/NiTi screens are literature / engineering screens, not safety clearances
- Ranking is assumption-driven exploratory analysis, not validated prediction

## 7. Availability

- Code: https://github.com/Coucou2016/fmr-ima-layer1-planner
- License: MIT (`LICENSE`)
- Citation: `CITATION.cff` · `references.bib`
- Model card: `MODEL_CARD.md` · Data: `DATA_PROVENANCE.md`

## 8. Conclusion

A Layer-1 literature-anchored surrogate can rank exploratory IMA scenarios under explicit assumptions after correcting peak-systole Galili AP facts and MAVERIC device-class attribution, and after reporting true fold-wise response diagnostics alongside a renamed blend-off casewise diagnostic. Cite as methods / research software for exploratory screening—not as clinical preoperative decision support.

---

## Figure captions (SciencePlots; English axis labels)

**Figure 1.** IMA-AP leakage proxy versus suture shortening under Galili peak-systole AP mapping and clinical \(\eta\) mapping. The shaded band marks the exploratory 14–20% AP planning range expressed in suture-% space via \(\eta_{\mathrm{AP}}\).

**Figure 2.** Device shortening mapped onto AP-diameter reduction for Galili IMA-AP, clinical IMA-AP (\(\eta=0.30\)), and clinical IMA-CS (\(\eta=0.55\) assumption prior). Horizontal band: exploratory planning range.

**Figure 3.** Commissural fraction of ROA and jet-location labels versus shortening (Galili vs clinical panels; squares = IMA-AP, circles = IMA-CS).

**Figure 4.** IMA-CS clinical-map Pareto / risk-screen view: leakage proxy versus CS–LCx distance and versus NiTi alternating strain. Vertical dashed lines mark the Rottländer 8.6 mm screen and the 0.4% engineering strain screen.

**Figure 5.** Dual-suture commissural-factor sensitivity (0.25 / 0.5 / 0.75 / 1.0) versus single-suture baseline—hypothesis parameter, not discovery.
