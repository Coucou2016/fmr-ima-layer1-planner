# Literature-anchored Layer-1 surrogate for exploratory screening of indirect mitral annuloplasty

**Working short title:** FMR IMA Layer-1 exploratory surrogate (software / methods)

**Venue class:** computational biomechanics / research-software methods paper (CMBBE / MedEngPhys / RSOS-class) — not a clinical decision trial.

**One-sentence argument:** We provide a transparent, literature-anchored algebraic surrogate that reproduces selected Galili peak-systole anchors, supports Dryad-aware provenance and leave-one-case-out scoring, and ranks exploratory IMA-CS / IMA-AP scenarios under explicit geometric, risk-screening, and η assumption-prior uncertainty — without claiming new LHHM FEA, clinical recommendation, or independent external validation of blended cases.

**Data / reproduce:** `python run_pipeline.py --seed 42 --paper` · `python tools/import_galili_dryad.py --from-fixture --process` · `python tools/loo_evaluate.py --write`

**Verification levels:** Level 0 = calibrated to / reproduced selected Galili cases; Level 1 = exploratory planning map + uncertainty-aware scenario ranker. Level 2 patient-specific LHHM/FSI is out of scope.

---

## Abstract

**Background.** Computational IMA studies (Galili et al., *R. Soc. Open Sci.* 2022) report suture/bridge shortening with peak-systolic geometry and leakage. Peak-systolic IMA-AP 50% yields AP **15.9 mm** (near-direct AP effect), not undeformed diastole **34.4 mm**. Device classes differ: MAVERIC evaluates **ARTO** (CS–IAS / IMA-AP-class); Carillon / REDUCE-FMR are IMA-CS-class.

**Methods.** We implement a reproducible Python Layer-1 surrogate: phenomenological mechanics plus a literature-calibrated leakage proxy. Provenance prefers Dryad doi:10.5061/dryad.bzkh1899d when local archives are present, with published table scalars as a documented secondary path. Calibration vs held-out splits and leave-one-case-out scoring are explicit. A discrete scenario ranker minimizes physics leakage-proxy regurgitation subject to an AP ceiling, an illustrative NiTi engineering screen, and a Rottländer CS–LCx risk-screening threshold, reporting P(feasible), η ranking stability, and a Pareto frontier (leakage vs AP reduction vs LCx vs strain). Dual-suture commissural ×0.5 is an exploratory hypothesis parameter. Prefer patient-measured CS–LCx; the cinch slope is a labeled assumption.

**Results (seed=42).** Under the planning map the ranker evaluates 36 points and retains 30 feasible designs (P(feasible)=0.833 on the device grid). Best candidate under stated assumptions: **IMA-AP dual suture 60%** (assumption η_ap=0.30 → AP reduction **18.0%**, physics leakage-proxy **~0.074%**, jet=`central`). Best feasible IMA-CS: bridge **20%** (CS–LCx **8.6 mm** at the risk-screen edge). η assumption-prior sensitivity shifts the top-ranked setting; this is not FEA UQ. Held-out / LOO metrics score blend-off predictions against published peak-systole quantities without advertising calibration-blend cases as validated.

**Conclusions.** A literature-anchored low-order surrogate can support **exploratory screening** of IMA strategy settings with inspectable assumptions and uncertainty language. It is not a preoperative clinical decision system and must not equate physics % with clinical regurgitant volume.

**Keywords:** functional mitral regurgitation; indirect mitral annuloplasty; surrogate model; exploratory screening; research software; Layer-1

---

## 1. Introduction

Functional mitral regurgitation (FMR) reflects ventricular remodeling, annular dilatation, and impaired leaflet coaptation. Indirect mitral annuloplasty (IMA) concepts remodel annular geometry without direct leaflet repair. **IMA-CS** (Carillon-class) and **IMA-AP** (CS–IAS; ARTO / MAVERIC mechanism class) are not mechanically interchangeable.

Galili et al. (2022) compared generic IMA-CS and IMA-AP in the Living Heart Human Model. IMA-AP acts nearly directly on peak-systolic AP (disease 26.1 mm → IMA-AP 50% → **15.9 mm**). Undeformed diastolic AP 34.4 mm is a different cardiac phase.

What remains for software methods is transparent **dose translation, provenance, and exploratory ranking** under stated assumptions—not a claim of first CS-vs-AP comparison, not new FEA, and not a clinical recommendation engine.

## 2. Related work and positioning

Galili RSOS 2022 + Dryad supporting files provide the computational leakage/ROA/AP table we anchor to. Clinical series (ARTO/MAVERIC; Carillon TITAN II; REDUCE-FMR) supply **directional / geometric context only**. This paper contributes research-software packaging and an inspectable Layer-1 ranker, not a new high-fidelity FSI study.

## 3. Software architecture

```
configs/   surrogate_calibration.yaml, design_space.yaml, case YAML
models/    geometry, pathology, devices (Galili peak-systole + planning map)
simulation/ phenomenological mechanics proxy (legacy alias run_fea_surrogate)
sph/       literature-calibrated leakage proxy (SPH-inspired; not a full SPH solver)
analysis/  ROA, jet, sweep, scenario_ranker, paper tables/plots
tools/     import_galili_dryad.py, loo_evaluate.py, package_reports.py
data/      raw drop zone, fixtures, processed galili_cases.csv
```

Runnable entry points: `run_pipeline.py`, `python -m analysis.planner`, `python -m analysis.design_sweep`.

## 4. Methods

**Pathology and geometry.** Parametric papillary pathology (44% posterior passive). Undeformed diastole and peak systole are separate `cardiac_phase` records.

**Device kinematics.** Galili mode interpolates published peak-systolic AP; clinical/planning mode uses assumption-prior η or preferred ΔAP. η_CS is **not** fitted from MAVERIC/ARTO.

**Mechanics and leakage proxies.** Algebraic coaptation-gap / strain / contact proxy scores. Leakage proxy is literature-calibrated at pathology. Physics regurg % ≠ clinical regurgitant volume. Synthetic contact-cluster ROA is visualization-only.

**Provenance and LOO.** `tools/import_galili_dryad.py` downloads or documents manual drop; extracts independent AP, contact, and leakage descriptors. `tools/loo_evaluate.py` scores held-out and leave-one-case-out predictions with blend OFF.

**Scenario ranker.** Minimizes physics leakage proxy; reports P(feasible), η±20% ranking stability, and Pareto frontier language. Dual-suture factor is an explicit hypothesis. LCx prefers patient-measured baseline.

## 5. Results

### 5.1 Galili peak-systole anchors (reproduction)

| Case | Leakage % | Peak-sys AP mm | ROA mm² |
|------|-----------|----------------|---------|
| pathology | 5.26 | 26.1 | 172.8 |
| ima_cs_22 | 0.29 | 24.8 | 48.2 |
| ima_ap_50 | 0.08 | **15.9** | 27.3 |
| ima_ap_70 | 0.13 | 12.4 | 46.1 |

### 5.2 Exploratory scenario ranking (planning map, seed=42)

- Evaluated **36** / feasible **30** (P(feasible)≈0.83)
- **Best candidate under assumptions:** IMA-AP dual **60%**, AP **18.0%**, physics **~0.074%**, jet=`central`
- Best IMA-CS: **20%** bridge, CS–LCx **8.6 mm** at risk-screen edge
- Dual-suture jet rule: exploratory hypothesis only
- η uncertainty: ranking stability reported in `scenario_ranking.json` → `uncertainty`

### 5.3 Held-out / LOO (blend OFF)

See `results/output/loo_evaluation.json`. Calibration IDs with blend ON are reproduction only.

### 5.4 Directionality-only clinical context

ARTO/MAVERIC: AP↓. Carillon TITAN II: ~15% AP context. REDUCE-FMR: regurg↓. Magnitudes not equated to physics %.

## 6. Discussion / limitations

Central advance: transparent exploratory screening software with corrected Galili peak-systole AP semantics, MAVERIC=ARTO mapping, Dryad-aware provenance, and uncertainty-aware ranking language. Limitations: algebraic proxies; Dryad CDN may require manual zip drop; LOO is not patient-level external validation; η are priors; LCx/NiTi screens are literature/engineering screens not safety clearances.

## 7. Availability

- Code: https://github.com/Coucou2016/fmr-ima-layer1-planner
- License: MIT (`LICENSE`)
- Citation: `CITATION.cff` · `references.bib`
- Model card: `MODEL_CARD.md` · Data: `DATA_PROVENANCE.md`

## 8. Conclusion

A Layer-1 literature-anchored surrogate can rank exploratory IMA scenarios under explicit assumptions after correcting peak-systole Galili AP facts and MAVERIC device-class attribution. Cite as methods/software for exploratory screening—not as clinical preoperative decision support.

---

*Collab notes:* `docs/chatgpt_collab/20260913_p0_review_response.md`, `docs/chatgpt_collab/20260914_p1p2_implementation.md`
