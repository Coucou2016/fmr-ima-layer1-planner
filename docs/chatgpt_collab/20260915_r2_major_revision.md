# 2026-09-15 — Round-2 major-revision follow-through

## Context

Public tip at task start: `0d08fd5`. Core P0/P1 landed in `dfa7b34` (fold-wise CV, Pareto families, DOI scrub, held-out-first reporting). This pass closes residual honesty/reporting gaps and regenerates packaged reports.

## Delivered this pass

1. **Full held-out table** (CS14 / CS18 / AP30 / AP70) in `docs/manuscript_draft.md` and `docs/paper.md`, with explicit AP70 text: qualitative non-monotonic tendency only; **substantially overestimates** rule-based leak magnitude (≈2.46% vs 0.13%) — not an unqualified “reproduces Galili non-monotonic behavior” claim.
2. **`tools/package_reports.py`**: held-out section (Markdown + HTML) before planner results; full joined rule/fold table; feasibility denominator surfaced with CV block.
3. **`contact_score`** alias populated from mechanics `contact_force_max_n` on `DesignPoint`.
4. Re-verify DOI hygiene (forbidden contiguous Galili DOI fragment absent; correct DOI **10.1098/rsos.211464**); tests + pipeline + package_reports.

## Metrics (unchanged from fold-wise fit; reported honestly)

| Metric | Baseline (rule blend-off historical) | Fold-wise held-out subset |
|--------|--------------------------------------|---------------------------|
| ROA MAE mm² | 50.18 | ≈6.37 |
| Leak MAE pp | 1.445 | ≈0.245 |
| AP70 ROA abs err | 94.17 | ≈6.60 |
| AP70 leak abs err | 5.455 | ≈0.198 |

Current dampened rule-based AP70 leak abs err remains ≈**2.33 pp** (prominent failure).

## Pareto / feasibility (from `dfa7b34`, still current)

- Global Pareto: min leakage + max AP↓ only (no 1e9/0 LCx/NiTi fillers).
- Family frontiers: `pareto_ima_cs_family` / `pareto_ima_ap_family`.
- Schema: `n_total_points=36` / `n_device_candidates=35` / `n_feasible_device_candidates=30` / `p_feasible_device_candidates≈0.857`.

## Remaining gaps

- Seven Galili cases ≠ patient-level external validation.
- Rule-based AP70 leak magnitude still fails; fold-wise AP30 leak err ≈0.70 pp (subset MAE still meets internal screen).
- Ruff remains non-blocking (legacy style debt); coverage fail-under not enforced.
- η sampling is independent assumption-prior sensitivity, not FEA UQ / full LHS.

## Commands

```
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python run_pipeline.py --seed 42 --paper --no-export
python -m analysis.fit_response_model --write
python tools/loo_evaluate.py --write
python tools/package_reports.py
```

## Git

- Follow-up commit SHA recorded after verify/push.
- No invented ChatGPT replies; no clinical-recommendation framing restored.
