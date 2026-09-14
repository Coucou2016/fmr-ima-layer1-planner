# FMR IMA Layer-1 planner — literature-anchored low-order surrogate

**Public repository:** https://github.com/Coucou2016/fmr-ima-layer1-planner

Exploratory screening of **Indirect Mitral Annuloplasty (IMA)** strategies for functional mitral regurgitation (FMR) with a **literature-anchored Layer-1 Python surrogate**:

- **IMA-CS** — coronary sinus / Carillon-class bridge shortening
- **IMA-AP** — CS–IAS suture (ARTO / MAVERIC mechanism class)

This is an **algebraic / phenomenological mechanics proxy** plus a **literature-calibrated leakage surrogate** (SPH-*inspired*). It is **not** reduced-order FEA, not production LHHM/Abaqus FSI, and **not** a clinical decision aid. Outputs are best candidates under stated surrogate assumptions (`scenario_ranker`), not recommendations. Ranking is assumption-driven exploratory analysis, not validated prediction.

## Quick start (Windows)

```powershell
cd E:\Projects\20260522-Functional-Mitral-Regurgitation-FMR
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py --seed 42
python run_pipeline.py --seed 42 --paper --no-export
```

Tests:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
```

Sweep / scenario ranker / Dryad / diagnostics / true CV:

```powershell
python -m analysis.design_sweep --seed 42
python -m analysis.planner --seed 42
python tools/import_galili_dryad.py --from-fixture --process
python tools/loo_evaluate.py --write
python -m analysis.fit_response_model --write
python tools/package_reports.py
```

## Critical literature facts (Galili RSOS 2022, doi:10.1098/rsos.211464)

Peak systole (do **not** mix with undeformed diastole AP = 34.4 mm):

| Case | ROA mm² | AP mm | Leakage % |
|------|---------|-------|-----------|
| Disease | 172.8 | 26.1 | 5.26 |
| IMA-CS 22% | 48.2 | 24.8 | 0.29 |
| IMA-AP 50% | 27.3 | **15.9** | 0.08 |
| IMA-AP 70% | 46.1 | 12.4 | 0.13 |

IMA-AP has a near-direct effect on AP diameter. Claiming IMA-AP 50% → AP 34.4 mm / 0% AP reduction was an error (fixed in P0).

**Device classes:** MAVERIC = **ARTO** (≈ IMA-AP), **not** Carillon / IMA-CS. Carillon context: TITAN II ~15% AP; REDUCE-FMR directional only. η values are **assumption priors**, not clinically calibrated constants.

## Seed-42 exploratory ranking

Under clinical/planning map, `response_path=fitted_response` (default), assumption η_ap=0.30, η_cs=0.55, AP ceiling 20%, LCx risk screen, LHS UQ N=120:

- **n_total_points=36**, **n_device_candidates=35**, **n_feasible_device_candidates=30**, **p_feasible_device_candidates≈0.857** (pathology is not a candidate)
- Best candidate under fitted path: **IMA-CS bridge 20%**, AP reduction **11.0%**, leakage proxy **≈0.39%**, jet=`central`, CS–LCx **8.6 mm** (risk-screen edge)
- Dual-suture AP60 remains an assumption-sensitive alternative (Fig. 5 = factor sensitivity, **not** discovery); Δleak vs matched single is tiny under the rule path and ranking is assumption-driven
- Ranker emits `P(top-1)` / ranking stability + family-separated Pareto frontiers in `results/output/planner/scenario_ranking.json`

Switch paths in `configs/design_space.yaml`: `fitted_response` | `rule_based_proxy` | `hybrid_ap_extreme`.

Physics % ≠ clinical regurgitant volume. Official fields: `leakage_proxy_pct`, `strain_risk_score`, `contact_score` (legacy aliases retained).

## Held-out / CV honesty

- `tools/loo_evaluate.py` = **anchor-free / leave-one-case blend-off diagnostic** on the fixed rule-based surrogate (not fold-wise refit; AP MAE N/A)
- `analysis/fit_response_model.py` = **true fold-wise** `f_ROA` / `f_leak` CV with Dryad `contact_fraction` as a feature → `results/output/cross_validation/`
- Full-train params for ranking → `results/output/response_model/full_train_params.json`
- Rule-based AP70 leak dampened ≈2.46% → ≈1.21% (still overestimates Galili 0.13%); paper ranking uses fitted path
- Report held-out / CV **before** planner ranking in manuscript and packaged reports

## Irreducible limits

- n=7 Galili peak-systole cases ≠ patient-level external validation
- No patient CT / chamber-labeled SPH leakage recompute
- Algebraic proxies; η and dual factor are assumption priors

## Project structure

```
configs/          Case YAML + surrogate_calibration.yaml + design_space.yaml
models/           Geometry, pathology, devices, response_model, response_runtime
simulation/       Algebraic mechanics proxy (aliases: run_fea_surrogate)
sph/              Literature-calibrated leakage proxy (SPH-inspired)
analysis/         ROA, jet, sweep, scenario_ranker, fit_response_model, paper tables/plots
tools/            Dryad import, blend-off diagnostic, package_reports
data/             raw/, fixtures/, processed/galili_cases.csv
docs/             manuscript_draft.md, chatgpt_collab/
results/          reference_data.yaml, clinical_references.yaml, outputs
tests/            literature facts + round-2 scientific review invariants
```

## Calibration vs reproduction vs validation

Blend-ON at calibration IDs = **reproduction**, not independent validation. Fold-wise CV on seven Galili table cases is an internal engineering diagnostic, not patient-level external validation.
