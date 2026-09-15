# 真实性审查 / Evidence Audit

**Date:** 2026-09-15  
**Repository:** https://github.com/Coucou2016/fmr-ima-layer1-planner  
**Public tip (pre-refresh):** `8a882f77968991b979add3d120639d06258b2d83` (`8a882f7`)  
**Scope:** Document that manuscript / report numbers come from this repo’s code and seed-42 pipeline outputs — not invented, and not Galili table values presented as our predictions.

---

## 1. Framing (non-negotiable)

| Claim allowed | Claim forbidden |
|---------------|-----------------|
| Literature-anchored Layer-1 / research-software methods paper | Clinical validated preoperative planner |
| Exploratory ranking under stated assumptions | “First CS vs AP comparison” (Galili 2022 already did LHHM) |
| `leakage_proxy_pct` / physics alias | Clinical regurgitant volume |
| MAVERIC = ARTO (IMA-AP class) | MAVERIC = Carillon; wrong Galili DOI (must be 10.1098/rsos.211464 only) |
| Dual-suture = hypothesis sensitivity (Fig. 5) | Innovation / discovery claim |
| Internal engineering CV screens on n=7 table | Patient-level external validation |

Anchor paper DOI: **10.1098/rsos.211464**. Dryad: **10.5061/dryad.bzkh1899d**.

---

## 2. Commands that regenerate evidence

```powershell
cd E:\Projects\20260522-Functional-Mitral-Regurgitation-FMR
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python run_pipeline.py --seed 42 --paper --no-export
python tools/package_reports.py
```

Optional provenance / CV refresh:

```powershell
python tools/import_galili_dryad.py --from-fixture --process
python -m analysis.fit_response_model --write
python tools/loo_evaluate.py --write
```

---

## 3. Artifact map (what feeds which claim)

| Claim family | Primary artifact | Code path |
|--------------|------------------|-----------|
| Scenario ranking / best candidate | `results/output/planner/scenario_ranking.json` (shim: `recommendation.json`) | `analysis/scenario_ranker.py` / planner |
| Response path used for paper ranking | `scenario_ranking.json` → `response_path` | `configs/design_space.yaml` |
| Fold-wise CV summary | `results/output/cross_validation/summary.json` | `analysis/fit_response_model.py` |
| Fold-wise per-case preds | `results/output/cross_validation/folds/*.json` + `loo_response_model.json` | same |
| Rule-based blend-off diagnostic | `results/output/loo_evaluation.json` → `heldout_evaluation` | `tools/loo_evaluate.py` |
| Full-train fitted params (ranking surface) | `results/output/response_model/full_train_params.json` | `analysis/fit_response_model.py` |
| Paper tables | `results/output/paper_tables/*.csv` + `paper_summary.json` | pipeline `--paper` |
| Paper figures | `results/output/paper_figures/fig1…fig5.png` | `analysis/plots.py` (SciencePlots) |
| Galili table-backed scalars | `data/processed/galili_cases.csv` / YAML cases | importer + fixtures |
| Dryad contact feature | `contact_fraction` in processed CSV / response features | `tools/import_galili_dryad.py` |

**Separation rule:** calibration / reproduction (blend ON at calibration IDs) ≠ blend-off diagnostic ≠ fold-wise CV ≠ exploratory ranking. Do not cross-quote metrics across these blocks without labeling the source.

---

## 4. Seed-42 key numbers (as of refresh; verify against JSON)

From `scenario_ranking.json` / `paper_summary.json`:

| Quantity | Value | Source field |
|----------|-------|--------------|
| `response_path` | `fitted_response` | ranking JSON |
| Best candidate | IMA-CS 20% | `best_candidate.device` / `shortening_pct` |
| AP reduction | 11.0% | `best_candidate.ap_reduction_pct` |
| Leakage proxy | ≈0.3912% | `best_candidate.leakage_proxy_pct` |
| Jet | `central` | `best_candidate.jet_location` |
| CS–LCx | 8.6 mm | `best_candidate.cs_lcx_mm` |
| n_total / n_device / n_feasible | 36 / 35 / 30 | ranking JSON |
| p_feasible_device_candidates | ≈0.8571 | ranking JSON |
| LHS N | 120 | `uncertainty.n_samples` |
| P(top-1) | ≈0.3417 | `uncertainty.p_top1` |
| Mean feasible fraction (LHS) | ≈0.8217 | `uncertainty.mean_fraction_feasible` |

From `cross_validation/summary.json`:

| Quantity | Value |
|----------|-------|
| Held-out subset MAE ROA | ≈6.3686 mm² |
| Held-out subset MAE leak | ≈0.2450 pp |
| IMA-AP70 abs err ROA / leak | ≈6.6049 mm² / ≈0.1983 pp |
| IMA-AP70 pred ROA / leak | ≈39.495 / ≈0.328% (pub 46.1 / 0.13%) |

From `loo_evaluation.json` (`heldout_evaluation.summary`) — **current dampened rule-based diagnostic**:

| Quantity | Value |
|----------|-------|
| Held-out MAE ROA | ≈5.2359 mm² |
| Held-out MAE leak | ≈0.0431 pp |
| IMA-AP70 rule pred leak | ≈0.07% (pub 0.13%; abs err ≈0.06 pp) |

Documented **historical pre-dampen baseline** (kept for comparison only; not current predictions): ROA MAE 50.18 mm², leak MAE 1.445 pp; AP70 abs err 94.17 / 5.455.

**Table-backed Galili anchors (not our predictions):** pathology 5.26% / 26.1 mm / 172.8 mm²; ima_cs_22 0.29 / 24.8 / 48.2; ima_ap_50 0.08 / **15.9** / 27.3; ima_ap_70 0.13 / 12.4 / 46.1.

---

## 5. Hash checklist (fill after regenerate)

Run after `run_pipeline.py --seed 42 --paper` and packaging:

```powershell
Get-FileHash results\output\planner\scenario_ranking.json,`
  results\output\cross_validation\summary.json,`
  results\output\loo_evaluation.json,`
  results\output\paper_tables\paper_summary.json,`
  results\output\paper_figures\fig1_ima_ap_nonmonotonic_exploratory_planning_range.png,`
  results\output\paper_figures\fig2_suture_vs_ap_reduction.png,`
  results\output\paper_figures\fig3_jet_location.png,`
  results\output\paper_figures\fig4_pareto_lcx_strain.png,`
  results\output\paper_figures\fig5_dual_vs_single_suture.png,`
  report.html, docs\paper.html -Algorithm SHA256
```

Record SHA256 digests and git `HEAD` in the collab log for this refresh.

---

## 6. Packaging self-containment checks

```powershell
python -c "from pathlib import Path; h=Path('report.html').read_text(encoding='utf-8'); print('data:image', h.count('data:image')); print('http img/css', sum(1 for s in ['src=\"http','href=\"http','cdn.'] if s in h))"
```

Expect: `data:image` ≥ 5; no external http image/CSS references in `report.html` / `docs/paper.html`.

---

## 7. Manuscript spine

User-edited narrative spine for this refresh: `docs/manuscript_draft.md` (rewritten 2026-09-15 to publishable methods style; numbers aligned to current pipeline). No newer Desktop/Downloads manuscript attachment was found.

Paper packaging: `docs/paper.md` (= manuscript copy), `docs/paper.html`, `docs/paper.pdf`.  
Report packaging: `report.html` / `report.md` / `report.pdf` (+ `docs/report.*` mirrors).

---

## 8. What is computed vs table-backed

| Quantity | Status |
|----------|--------|
| Galili published AP / ROA / leak at discrete cases | **Table-backed** (literature) |
| Dryad `contact_fraction` / `n_sph_particles` | **Extracted / fixture-derived** |
| Rule-based blend-off preds | **Computed** (fixed surrogate, blend OFF) |
| Fold-wise f_ROA / f_leak preds | **Computed** (true LOO refit) |
| Planning-map sweep ROA / leak / jet / LCx / NiTi | **Computed** under η assumptions |
| Best candidate / Pareto / LHS stability | **Computed** ranking under assumptions |
| Clinical trial MR volumes | **Not used** as calibration targets |
