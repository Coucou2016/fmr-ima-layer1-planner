# A literature-anchored Layer-1 surrogate for exploratory screening of indirect mitral annuloplasty

**Short title.** FMR IMA Layer-1 exploratory surrogate

**Article type.** Computational biomechanics methods / research software

**One-sentence argument.** This paper releases a reproducible algebraic Layer-1 surrogate that reproduces selected Galili peak-systole anchors, fits fold-wise response models with Dryad contact features, and ranks exploratory IMA-CS and IMA-AP scenarios under stated geometric assumptions. It does not claim new Living Heart Human Model finite-element analysis, clinical decision support, or patient-level external validation.

---

## Abstract

Functional mitral regurgitation is often treated by devices that remodel annular geometry through the coronary sinus or through anteroposterior shortening. High-fidelity finite-element studies already compare these pathways, yet a transparent low-order screening layer with inspectable assumptions and held-out diagnostics remains limited. Peak-systolic geometry and diastolic reference lengths also continue to be mixed in dose statements. We built a reproducible Python Layer-1 surrogate that combines phenomenological mechanics with a literature-calibrated leakage proxy. Dryad supporting files supply an auxiliary contact feature. Fold-wise response models for regurgitant orifice area and leakage are fitted under true leave-one-case-out, and a discrete scenario ranker minimizes the leakage proxy under an anteroposterior reduction ceiling, a nickel–titanium engineering screen, and a coronary sinus–left circumflex risk screen. On the held-out Galili subset with seed 42, fold-wise mean absolute error is 6.37 mm² for regurgitant orifice area and 0.245 percentage points for leakage. Under the planning map the ranker retains 30 of 35 device candidates as feasible. The best feasible candidate is IMA-CS bridge shortening of 20 percent, with 11.0 percent anteroposterior reduction and a leakage proxy of 0.391 percent. Latin-hypercube sampling of assumption priors yields a top-1 stability of 0.342. These results support exploratory screening under transparent assumptions. They do not support preoperative clinical use or equivalence between physics leakage proxies and clinical regurgitant volume.

**Keywords.** functional mitral regurgitation; indirect mitral annuloplasty; surrogate model; exploratory screening; research software; Layer-1

---

## 1. Introduction

### 1.1 Background and research problem

Functional mitral regurgitation (FMR) develops when ventricular remodelling, annular dilatation, and impaired leaflet coaptation leave a residual orifice in systole. Indirect mitral annuloplasty (IMA) seeks to remodel annular geometry without direct leaflet repair. Two device families recur in both clinic and computation. IMA-CS shortens a coronary-sinus bridge and belongs to the Carillon class. IMA-AP shortens a suture path between the coronary sinus and the interatrial septum and belongs to the ARTO class studied in MAVERIC. These pathways act on different geometric levers and are not interchangeable.

Dose statements for IMA require a clear cardiac phase. Peak-systolic anteroposterior (AP) diameter after device deployment is the relevant response for leakage comparisons. Undeformed diastolic AP is a different reference and cannot replace peak-systolic values in shortening arguments.

### 1.2 Previous research and knowledge gap

Galili, White Zeira and Marom (2022) compared generic IMA-CS and IMA-AP treatments in the Living Heart Human Model and quantified peak-systolic geometry and leakage after deployment [1]. Their IMA-AP 50 percent case reaches a peak-systolic AP of 15.9 mm relative to a diseased peak-systolic AP of 26.1 mm. The undeformed diastolic AP of 34.4 mm belongs to another phase. Dryad supporting files accompany that study and provide particle and contact metadata [2].

Clinical series supply geometric context at a different scale. MAVERIC evaluates the ARTO system and reports AP reductions of order 14 to 15 percent for an IMA-AP-class device [3]. Carillon studies including REDUCE-FMR inform IMA-CS directionality for regurgitation reduction [4]. Rottländer and colleagues reported coronary sinus–left circumflex (CS–LCx) distances that support risk-screening language near 8.6 mm in the distal landing zone [5]. Modular mitral finite-element tools in the medical-engineering literature show how to separate geometry drivers from functional readouts, yet they remain costly for broad exploratory grids.

What remains limited is a reproducible low-order software layer that (i) preserves Galili peak-systole facts and device-class attribution, (ii) separates calibration reproduction from held-out diagnostics, (iii) reports true fold-wise response-model cross-validation, and (iv) ranks exploratory scenarios under explicit transfer-efficiency assumptions with uncertainty language. The present study addresses that software gap. It does not claim the first computational CS-versus-AP comparison and does not introduce new Living Heart Human Model finite-element analysis.

### 1.3 Objectives and contributions

This study aims to deliver and evaluate a literature-anchored Layer-1 surrogate for exploratory IMA screening. The work has four concrete contributions.

1. A reproducible Python package that maps IMA-CS and IMA-AP shortening onto peak-systolic AP, regurgitant orifice area (ROA), and a leakage proxy under labeled assumptions.
2. Dryad-aware contact features in a fitted response path, while scalar AP, ROA, and leakage remain table-backed unless independently derived.
3. Honest diagnostics that separate a rule-based blend-off casewise check from true fold-wise leave-one-case-out of the response models.
4. An exploratory scenario ranker with Latin-hypercube sampling of assumption priors, family-separated Pareto sets, and an explicit dual-suture sensitivity parameter that is not treated as a discovery claim.

Verification is organized in two levels. Level 0 reproduces selected Galili peak-systole anchors. Level 1 provides the planning map, fold-wise response diagnostic, and uncertainty-aware ranker. Patient-specific Level 2 fluid–structure interaction is out of scope.

---

## 2. Methods

### 2.1 Study object, data and geometry

The computational object is a parametric papillary pathology with an approximate 44 percent posterior passive fraction. Undeformed diastole and peak systole are stored as separate cardiac-phase records. Published Galili peak-systole scalars for AP, ROA, and leakage are loaded from the processed case table derived from the Dryad package and literature fixtures. AP diameter is a literature-defined geometry input. AP prediction error is therefore not reported as predictive accuracy.

Dryad files supply `contact_fraction` and particle counts where available. Scalar AP, ROA, and leakage remain table-backed fills. The importer does not invent those scalars from unlabeled leaflet coordinates alone.

### 2.2 Governing formulation

Device kinematics use one of two mapping modes. In Galili mapping mode, peak-systolic AP follows published table coordinates with interpolation between discrete cases. In clinical planning mode, AP reduction is

$$\mathrm{AP\_reduction\%}=\eta\times\mathrm{shortening\%}\qquad(1)$$

with assumption-prior means \(\eta_{\mathrm{AP}}=0.30\) and \(\eta_{\mathrm{CS}}=0.55\). The CS transfer factor is not fitted from MAVERIC or ARTO. Algebraic coaptation-gap, strain, and contact-proxy scores form the phenomenological mechanics channel. The leakage proxy is literature-calibrated at the pathology case. Physics regurgitation percentage is not clinical regurgitant volume.

Fitted response models take the form

$$f_{\mathrm{ROA}}(\Delta\mathrm{AP},\ \mathrm{device\ family},\ \mathrm{annular\ reduction},\ \mathrm{contact\_fraction})\qquad(2)$$

$$f_{\mathrm{leak}}(\mathrm{ROA},\ \mathrm{coaptation\ proxy},\ \mathrm{contact},\ \mathrm{device\ mechanism})\qquad(3)$$

A fixed over-short prior encodes the Galili non-monotonic ROA rebound beyond the IMA-AP 50 percent region. Official export fields are `leakage_proxy_pct`, `strain_risk_score`, and `contact_score`.

### 2.3 Numerical implementation and software

The package is organized as configuration cases, geometry and device models, a phenomenological mechanics proxy, a literature-calibrated leakage proxy, and analysis modules for ROA, jet location, design sweep, response-model fitting, and scenario ranking. Entry points include the seed-controlled pipeline, the planner, the fold-wise fitter, and the blend-off diagnostic. Paper figures are generated with SciencePlots using Times New Roman axis fonts. Random seed 42 is used for all reported ranking and sampling results.

Three response paths are available. The paper default for ranking is `fitted_response`. The rule-based path is retained for diagnostics. A hybrid path routes AP-class over-short cases to the fitted surface.

### 2.4 Parameters and calibration

Calibration case identifiers with blend on are pathology, IMA-CS 22 percent, and IMA-AP 50 percent. Agreement at these identifiers is reproduction of literature anchors. It is not independent validation. Planning-map grids use the clinical mapping with the transfer factors above. Default uncertainty quantification draws Latin-hypercube samples over

$$\eta_{\mathrm{AP}}\in U(0.24,0.36),\quad \eta_{\mathrm{CS}}\in U(0.44,0.66)$$

together with the dual commissural factor, CS–LCx baseline, and cinch slope, with \(N=120\) samples as configured in the design-space file.

### 2.5 Verification, validation and evaluation

Two diagnostics are reported separately.

**Rule-based blend-off diagnostic.** The fixed rule-based surrogate is evaluated with blend off on the held-out identifiers IMA-CS 14 percent, IMA-CS 18 percent, IMA-AP 30 percent, and IMA-AP 70 percent. No fold-wise refit is performed.

**True fold-wise response-model cross-validation.** Each leave-one-case-out fold refits Equations (2) and (3) on the other six Galili peak-systole cases. Held-out ROA and leakage never enter the training arrays. Full-train parameters support ranking.

**Scenario ranker.** The ranker minimizes `leakage_proxy_pct` subject to an exploratory AP-reduction ceiling of 20 percent, an illustrative nickel–titanium alternating-strain screen below 0.4 percent, and a CS–LCx risk-screening threshold of 8.6 mm. Feasibility counts exclude the pathology point from the device-candidate denominator. Pareto families are separated into global common objectives, an IMA-CS family that adds LCx and NiTi, and an IMA-AP family. Missing LCx or NiTi values are never replaced by sentinel fillers. The dual-suture commissural factor is an explicit hypothesis sensitivity parameter.

Error metrics use mean absolute error (MAE) for ROA in mm² and for leakage in percentage points (pp).

$$\mathrm{MAE}=\frac{1}{N}\sum_{i=1}^{N}\left|y_i^{\mathrm{pred}}-y_i^{\mathrm{obs}}\right|\qquad(4)$$

Internal engineering screens on the seven-case table are ROA MAE below 25 mm², leak MAE below 0.5 pp, and the same absolute-error ceilings for the IMA-AP 70 percent fold. These screens are engineering checks only. They are not medical validation thresholds.

---

## 3. Results

### 3.1 Data provenance

The processed Galili case table marks Dryad-derived contact fraction and particle counts with a Dryad source tier. Published peak-systole AP, ROA, and leakage remain table-backed. Seed 42 pipeline outputs feed all quantitative claims below.

### 3.2 Calibration reproduction (Level 0)

Table 1 lists selected Galili peak-systole anchors used for Level 0 reproduction. Calibration identifiers with blend on reproduce literature leakage and geometry. They are not held-out predictions.

**Table 1.** Selected Galili peak-systole anchors used for Level 0 reproduction.

| Case | Leakage % | Peak-sys AP (mm) | ROA (mm²) |
|------|-----------|------------------|-----------|
| pathology | 5.26 | 26.1 | 172.8 |
| ima_cs_22 | 0.29 | 24.8 | 48.2 |
| ima_ap_50 | 0.08 | 15.9 | 27.3 |
| ima_ap_70 | 0.13 | 12.4 | 46.1 |

Figure 1 shows the IMA-AP leakage proxy against suture shortening under Galili peak-systole AP mapping and under clinical \(\eta\) mapping. The shaded band marks the exploratory 14 to 20 percent AP planning range expressed in suture-percent space through \(\eta_{\mathrm{AP}}\). Figure 2 maps device shortening onto AP-diameter reduction for Galili IMA-AP, clinical IMA-AP, and clinical IMA-CS.

### 3.3 Held-out diagnostics and fold-wise cross-validation

A documented pre-dampen historical baseline on the held-out identifiers reported MAE of 50.18 mm² for ROA and 1.445 pp for leakage, with IMA-AP 70 percent absolute errors of 94.17 mm² and 5.455 pp. After rule-based dampening, the current seed-42 blend-off diagnostic reports held-out MAE of 5.24 mm² for ROA and 0.043 pp for leakage. For IMA-AP 70 percent the rule-based path predicts leakage of 0.07 percent against the published 0.13 percent, an absolute error of 0.06 pp.

True fold-wise response-model leave-one-case-out on the held-out subset yields MAE of 6.37 mm² for ROA and 0.245 pp for leakage. For IMA-AP 70 percent the fold-wise absolute errors are 6.60 mm² and 0.198 pp, with predicted ROA 39.5 mm² versus published 46.1 mm² and predicted leakage 0.33 percent versus published 0.13 percent. Internal engineering screens on this seven-case table are met. Full seven-fold MAE remains inflated by the pathology leave-out because of the large ROA scale gap. AP prediction metrics remain inapplicable.

Table 2 compares published values with the current rule-based blend-off diagnostic and the fold-wise response model on the four held-out identifiers.

**Table 2.** Held-out Galili cases. Published values versus current rule-based blend-off and fold-wise response-model predictions (seed 42).

| Case | Pub ROA | Rule ROA (abs err) | Fold ROA (abs err) | Pub leak % | Rule leak (abs err pp) | Fold leak (abs err pp) |
|------|---------|--------------------|--------------------|------------|------------------------|------------------------|
| ima_cs_14 | 56.7 | 59.6 (2.9) | 69.6 (12.9) | 0.52 | 0.51 (0.01) | 0.60 (0.08) |
| ima_cs_18 | 55.3 | 54.9 (0.4) | 53.4 (1.9) | 0.41 | 0.42 (0.01) | 0.42 (0.01) |
| ima_ap_30 | 51.1 | 42.4 (8.7) | 47.0 (4.1) | 0.16 | 0.25 (0.09) | 0.86 (0.70) |
| ima_ap_70 | 46.1 | 37.2 (8.9) | 39.5 (6.6) | 0.13 | 0.07 (0.06) | 0.33 (0.20) |

Paper ranking uses the fitted response path to obtain a coherent off-table surface under planning-map kinematics. The rule-based path remains the named blend-off diagnostic.

### 3.4 Exploratory scenario ranking under assumptions

Under the clinical planning map with `fitted_response` and seed 42, the ranker evaluates 36 grid points. Of these, 35 are device candidates and 30 are feasible, giving a feasible fraction of 0.857. The best feasible candidate is IMA-CS bridge shortening of 20 percent. With \(\eta_{\mathrm{CS}}=0.55\) this setting yields AP reduction of 11.0 percent, leakage proxy of 0.391 percent, a central jet label, and CS–LCx distance of 8.6 mm at the risk-screen edge. The best IMA-AP single and dual alternatives under the same constraints remain higher-leakage near 0.79 percent at 65 percent shortening and 19.5 percent AP reduction.

Figure 3 shows commissural fraction of ROA and jet-location labels versus shortening. Figure 4 shows the IMA-CS clinical-map Pareto view of leakage proxy against CS–LCx distance and against NiTi alternating strain. Figure 5 reports dual-suture commissural-factor sensitivity at 0.25, 0.5, 0.75, and 1.0 relative to the single-suture baseline. Dual suture is a hypothesis parameter in this study.

Latin-hypercube multi-parameter sampling with \(N=120\) yields a top-1 stability of 0.342 and a mean feasible fraction of 0.822. First-order Spearman ranks are dominated by the CS–LCx baseline and the cinch slope. One-at-a-time \(\eta\pm 20\) percent sensitivity keeps IMA-CS 20 percent as the nominal top candidate while shifting realized AP reduction to 8.8 percent, 11.0 percent, and 13.2 percent under the minus, nominal, and plus settings.

### 3.5 Directionality-only clinical context

ARTO and MAVERIC report AP reductions of order 14 to 15 percent for an IMA-AP-class device. Carillon TITAN II reports AP context near 15 percent for an IMA-CS-class device. REDUCE-FMR supports regurgitation-reduction directionality for IMA-CS. These magnitudes are not equated to physics leakage-proxy percentages.

---

## 4. Discussion

### 4.1 Interpretation of main findings

The central result is that a literature-anchored Layer-1 surrogate can reproduce selected Galili anchors, report honest held-out and fold-wise diagnostics, and rank exploratory IMA scenarios under labeled assumptions. The fitted path is preferred for ranking because it supplies a consistent off-table surface when planning-map kinematics leave the discrete Galili table. The rule-based path remains useful as a blend-off diagnostic and can show smaller held-out MAE on some scalars after dampening. That fact does not make the rule-based path the ranking surface for off-table planning.

The best feasible seed-42 candidate under the stated screens is a moderate IMA-CS bridge shortening. This ranking is assumption-driven. It is not a claim that IMA-CS is clinically superior to IMA-AP. Galili’s high-fidelity study already compared the two families in the Living Heart Human Model. The present software layer answers a different question about transparent exploratory screening.

### 4.2 Comparison with existing studies

Relative to Galili et al. [1], we inherit the IMA-CS versus IMA-AP taxonomy and the peak-systole leakage and ROA readouts. We do not re-litigate which generic device seals better in high fidelity. Relative to MAVERIC and ARTO [3], we borrow geometric windows only and keep MAVERIC attributed to ARTO as an IMA-AP-class mechanism. Relative to Carillon and REDUCE-FMR [4], we borrow directionality language only. Relative to Rottländer CS–LCx work [5], we use the 8.6 mm threshold as a risk screen rather than a safety clearance. Relative to modular mitral finite-element tools, we trade continuum fidelity for inspectable assumption priors and rapid grid ranking.

### 4.3 Limitations and applicability

Several limits are irreducible with the present evidence base.

1. The Galili peak-systole table contains seven cases. Fold-wise metrics are internal engineering diagnostics on that table. They are not patient-level external validation.
2. No patient computed tomography and no patient-specific chamber geometry enter the surrogate.
3. Chamber-labeled SPH leakage is not recomputed from Dryad particle clouds. Full-domain clouds are available, yet AP, ROA, and leakage remain table-backed.
4. Transfer efficiencies and the dual commissural factor are assumption priors. They are not imaging–finite-element identifications.
5. LCx and NiTi screens are literature and engineering screens. They are not safety clearances.
6. Ranking is exploratory analysis under assumptions. It is not validated clinical prediction.

Within these limits the package is suitable for methods-oriented exploratory screening, reproducible teaching of dose translation, and hypothesis-sensitive design grids. It is not suitable as a preoperative decision system.

---

## 5. Conclusions

This study investigated exploratory screening of indirect mitral annuloplasty using a literature-anchored Layer-1 algebraic surrogate with Dryad contact features, fold-wise response diagnostics, and an assumption-aware scenario ranker. The principal conclusions are as follows.

1. Selected Galili peak-systole anchors are reproduced at Level 0, including the IMA-AP 50 percent peak-systolic AP of 15.9 mm, while diastolic AP of 34.4 mm is kept out of peak-systole dose statements.
2. On the held-out Galili subset, fold-wise response-model MAE is 6.37 mm² for ROA and 0.245 pp for leakage. IMA-AP 70 percent fold-wise absolute errors are 6.60 mm² and 0.198 pp. Internal engineering screens are met on the seven-case table.
3. Under the seed-42 planning map with the fitted response path, 30 of 35 device candidates are feasible. The best feasible candidate is IMA-CS bridge shortening of 20 percent, with AP reduction 11.0 percent and leakage proxy 0.391 percent.
4. Latin-hypercube sampling of assumption priors yields top-1 stability of 0.342 and mean feasible fraction of 0.822. Dual suture remains a hypothesis sensitivity parameter.
5. The findings support transparent exploratory screening within the tested Galili-table and assumption ranges. They do not establish clinical preoperative decision support or equate physics leakage proxies with clinical regurgitant volume.

---

## Data and code availability

Source code and configuration files are available at https://github.com/Coucou2016/fmr-ima-layer1-planner under the MIT license. Galili supporting data are available from Dryad under doi:10.5061/dryad.bzkh1899d. Seed-42 pipeline outputs used in this manuscript live under the repository results tree. A model card and data provenance note accompany the package.

## Reproducibility

The reported figures and tables regenerate with

```text
python run_pipeline.py --seed 42 --paper
python tools/import_galili_dryad.py --from-fixture --process
python -m analysis.fit_response_model --write
python tools/loo_evaluate.py --write
```

## Acknowledgements

The authors thank the public release of the Galili Royal Society Open Science study and Dryad package, which make Level 0 reproduction and Dryad-aware features possible.

## Competing interests

The authors declare no competing interests.

## Funding

No specific funding was received for this software methods study beyond institutional computing resources.

---

## References

[1] Galili L, White Zeira A, Marom G. Numerical biomechanics modelling of indirect mitral annuloplasty treatments for functional mitral regurgitation. R Soc Open Sci. 2022;9:211464. doi:10.1098/rsos.211464

[2] Galili L, White Zeira A, Marom G. Data from: Numerical biomechanics modelling of indirect mitral annuloplasty treatments for functional mitral regurgitation. Dryad. 2022. doi:10.5061/dryad.bzkh1899d

[3] Worthley S, Redwood S, Hildick-Smith D, et al. Transcatheter reshaping of the mitral annulus in patients with functional mitral regurgitation: one-year outcomes of the MAVERIC trial. EuroIntervention. 2021. doi:10.4244/EIJ-D-20-00484

[4] Witte KK, et al. REDUCE-FMR Investigators. Carillon mitral contour system for functional mitral regurgitation. JACC Heart Fail. 2019. Directional regurgitant-volume context for IMA-CS / Carillon class.

[5] Rottländer D, et al. Procedural planning of CS-based indirect mitral annuloplasty using CT-angiography. Catheter Cardiovasc Interv. 2021. doi:10.1002/ccd.29824 (CS–LCx landing-zone screen near 8.6 mm used as literature risk screen only)

[6] Rottländer D, et al. Anatomy and topography of coronary sinus and mitral valve annulus in functional mitral regurgitation. Front Cardiovasc Med. 2022;9:868562. doi:10.3389/fcvm.2022.868562

---

## Figure captions

**Figure 1.** IMA-AP leakage proxy versus suture shortening under Galili peak-systole AP mapping and clinical \(\eta\) mapping. The shaded band marks the exploratory 14–20% AP planning range expressed in suture-% space via \(\eta_{\mathrm{AP}}\).

**Figure 2.** Device shortening mapped onto AP-diameter reduction for Galili IMA-AP, clinical IMA-AP (\(\eta=0.30\)), and clinical IMA-CS (\(\eta=0.55\) assumption prior). The horizontal band marks the exploratory planning range.

**Figure 3.** Commissural fraction of ROA and jet-location labels versus shortening for Galili and clinical panels. Squares mark IMA-AP. Circles mark IMA-CS.

**Figure 4.** IMA-CS clinical-map Pareto and risk-screen view. Leakage proxy versus CS–LCx distance and versus NiTi alternating strain. Vertical dashed lines mark the Rottländer 8.6 mm screen and the 0.4% engineering strain screen.

**Figure 5.** Dual-suture commissural-factor sensitivity (0.25 / 0.5 / 0.75 / 1.0) versus single-suture baseline. Hypothesis parameter, not discovery.

---

## Table note

All seed-42 scalars in Results come from `results/output/planner/scenario_ranking.json`, `results/output/cross_validation/summary.json`, and `results/output/loo_evaluation.json` regenerated by the public pipeline. Physics leakage-proxy percentages are not clinical regurgitant volumes. MAVERIC evaluates ARTO (IMA-AP class). Dual suture is hypothesis sensitivity.
