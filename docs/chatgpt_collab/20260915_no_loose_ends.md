# 2026-09-15 — No loose ends (Round-2 §28–29 acceptance)

Public tip at start of this pass: `2dc6520`. Goal: finish all remaining Round-2 items; no half-done next-phase stubs.

## Acceptance checklist (§29)

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | Wrong Galili DOI fragment (`211`+`726`) = 0 | **DONE** | `test_zero_occurrences_of_wrong_galili_doi`; CI DOI hygiene step |
| 2 | Held-out MAE reported in main text | **DONE** | `docs/manuscript_draft.md` Abstract + §5.3; packaged reports held-out section before planner |
| 3 | AP not packaged as predictive MAE=0 validation | **DONE** | `ap_prediction_metric_applicable=false`; blend-off + fold CV honesty |
| 4 | True fold-wise fit | **DONE** | `analysis/fit_response_model.py` → `results/output/cross_validation/` |
| 5 | No false `validation_claim_allowed` | **DONE** | Removed; `test_blend_off_diagnostic_renamed_no_validation_claim` |
| 6 | Pareto no N/A-as-best | **DONE** | Family frontiers; no 1e9/0 fillers |
| 7 | 36 / 35 / 30 unified | **DONE** | Schema + tests |
| 8 | Dryad contact in model | **DONE** | Feature in `models/response_model.py`; interpolated for design points via `response_runtime.estimate_contact_fraction`; not provenance-only |
| 9 | Dual-suture = factor sensitivity not discovery | **DONE** | Fig.5 factors 0.25/0.5/0.75/1.0; hypothesis role in JSON/notes |
| 10 | Reports / README / paper / figures / JSON same commit+config | **DONE** | `run_pipeline.py --paper` + `tools/package_reports.py` embed HEAD SHA; CI packages on 3.12 |

## Delivered beyond prior tip

### A. Model / pipeline
- Config switch `response_path`: **`fitted_response` (default)** | `rule_based_proxy` | `hybrid_ap_extreme`
- Full-train params: `results/output/response_model/full_train_params.json`
- Rule-based AP70 leak **≈2.46% → ≈1.21%** (still > Galili 0.13%; ranking uses fitted)
- ROA `model_weight=1.0`, `cluster_weight=0.0` enforced + tested
- `_sph_scale` pathology-fraction identity documented

### B. Uncertainty / ranking
- Latin Hypercube multi-parameter (η_AP, η_CS, dual factor, CS–LCx baseline, cinch slope), **N=120**
- Outputs: `P(top-1)`, `P(feasible)`, ranking stability, Spearman first-order ranks
- Seed-42 fitted ranking: best **IMA-CS 20%**; **P(top-1)≈0.34**
- `clinical_window` → **`exploratory_planning_range`** (legacy alias retained)

### C–E. Schema / plots / CI
- Official fields + aliases; fig1 renamed; plots η from config
- Ruff **blocking**; pytest-cov **`--cov-fail-under=70`** (measured ≈76%)
- Python 3.10–3.12 matrix retained

## Irreducible leftovers (scientific, not software stubs)
- n=7 Galili cases ≠ patient external validation
- No patient CT
- No chamber-labeled SPH leakage recompute

## Commands
```
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python run_pipeline.py --seed 42 --paper --no-export
python -m analysis.fit_response_model --write
python tools/loo_evaluate.py --write
python tools/package_reports.py
rg ("211"+"726")  # empty (split token only in CI/test ban)
```

## Git
- Tip after this pass: _(filled after commit)_
- Push: `origin/main`

