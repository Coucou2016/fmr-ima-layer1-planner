# 2026-09-14 — Round-2 Major Revision implementation

## Scope

Full P0 implementation of the second-round scientific review for
`fmr-ima-layer1-planner`, plus P1 and selected P2 items.

Public tip at start: `0d08fd51c761cfdfbbb535513c1b8491510fc939`

## P0 delivered

### A. LOO rename
- `tools/loo_evaluate.py` reframed as **anchor-free / leave-one-case blend-off diagnostic**
- Removed `validation_claim_allowed`
- AP marked `ap_role: literature_mapping_input`, `ap_prediction_metric_applicable: false`
- AP MAE no longer reported as predictive accuracy

### B. True fold-wise response model CV
- `models/response_model.py` — `f_ROA` (log-linear + fixed overshoot prior) and `f_leak`
- `analysis/fit_response_model.py` — leave-one-case refit; held ROA/leak excluded from fit arrays
- Artifacts: `results/output/cross_validation/`
- Dryad `contact_fraction` is a model feature

**Held-out subset metrics (vs rule-based blend-off baseline):**

| Metric | Baseline | After fold-wise CV |
|--------|----------|--------------------|
| ROA MAE (mm²) | 50.18 | **≈6.37** |
| Leak MAE (pp) | 1.445 | **≈0.245** |
| AP70 ROA abs err | 94.17 | **≈6.60** |
| AP70 leak abs err | 5.455 | **≈0.198** |

Internal engineering targets met on held-out subset; still **not** patient-level external validation.
Rule-based path dampened AP70 (140→~54 ROA; 5.6%→~2.5% leak) but still overestimates leak magnitude vs Galili 0.13%.

### C. Manuscript / reports
- `docs/manuscript_draft.md` Results order: provenance → calibration → held-out/CV (incl. AP70) → exploratory ranking
- `tools/package_reports.py` inserts held-out/CV section before planner emphasis
- Dual60 framed as nominal dual-suture hypothesis; Δleak ~0.0018 pp; assumption-sensitive

### D. Pareto
- `pareto_global_common_objectives` (min leak, max AP↓)
- `pareto_ima_cs_family` / `pareto_ima_ap_family`
- No 1e9/0 N/A fillers

### E. P(feasible) schema
- `n_total_points=36`, `n_device_candidates=35`, `n_feasible_device_candidates=30`, `p_feasible_device_candidates=0.8571`

### F. DOI hygiene
- Correct Galili DOI **10.1098/rsos.211464**; title uses **treatments**
- Contiguous forbidden DOI fragment removed from tracked sources (CI/test ban via split token)

## P1 delivered
- ROA pipeline scientific default `model_weight=1.0`, `cluster_weight=0.0`
- Independent η_AP / η_CS sampling
- Fig.5 dual-factor sensitivity (0.25/0.5/0.75/1.0)
- Plot label cleanup (η=0.55; LCx/NiTi risk/engineering screens)
- Exploratory planning range language; MODEL_CARD Dryad=primary provenance/auxiliary descriptors
- `_sph_scale` simplified to pathology regurgitation fraction identity

## P2 delivered (partial)
- Aliases: `leakage_proxy_pct`, `strain_risk_score`
- CI: DOI hygiene test; fold-wise CV artifacts; ruff remains non-blocking (legacy style debt)
- Dual-suture demoted from abstract center

## Verification
```
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python run_pipeline.py --seed 42 --paper --no-export
python tools/package_reports.py
python -m analysis.fit_response_model --write
```

## Honesty retained
- Algebraic/phenomenological mechanics + literature-calibrated leakage proxy
- MAVERIC=ARTO≠Carillon
- Galili peak-systole AP50=15.9 mm
- No invented ChatGPT replies; no clinical-recommendation framing restored
