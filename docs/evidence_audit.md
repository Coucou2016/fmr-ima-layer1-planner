# 真实性审查 / Evidence Audit

**Date:** 2026-11-07  
**Repository:** https://github.com/Coucou2016/fmr-ima-layer1-planner  
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
python tools/build_manuscript_docx.py
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
| Scenario ranking / best candidate | `results/output/planner/scenario_ranking.json` | `analysis/scenario_ranker.py` / planner |
| Response path used for paper ranking | `scenario_ranking.json` → `response_path` | `configs/design_space.yaml` |
| Fold-wise CV summary | `results/output/cross_validation/summary.json` | `analysis/fit_response_model.py` |
| Fold-wise per-case preds | `results/output/cross_validation/folds/*.json` + `loo_response_model.json` | same |
| Rule-based blend-off diagnostic | `results/output/loo_evaluation.json` → `heldout_evaluation` | `tools/loo_evaluate.py` |
| Full-train fitted params (ranking surface) | `results/output/response_model/full_train_params.json` | `analysis/fit_response_model.py` |
| Paper tables | `results/output/paper_tables/*.csv` + `paper_summary.json` | pipeline `--paper` |
| Paper figures | `results/output/paper_figures/fig1…fig5.png` | `analysis/plots.py` (SciencePlots) |
| Galili table-backed scalars | `data/processed/galili_cases.csv` / YAML cases | importer + fixtures |
| Dryad contact feature | `contact_fraction` in processed CSV / response features | `tools/import_galili_dryad.py` |
| Final manuscript (Markdown) | `docs/manuscript_final.md` (= `docs/paper.md`) | SCI guide rewrite 2026-11-07 |
| Final manuscript (Word) | `docs/manuscript_final.docx` + Desktop copy | `tools/build_manuscript_docx.py` |

**Separation rule:** calibration / reproduction (blend ON at calibration IDs) ≠ blend-off diagnostic ≠ fold-wise CV ≠ exploratory ranking. Do not cross-quote metrics across these blocks without labeling the source.

---

## 4. Seed-42 key numbers (verified 2026-11-07 against JSON)

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

**η ±20% sensitivity (paper_tables/eta_sensitivity.csv):** IMA-CS 20% remains top under minus/nominal/plus; AP reduction 8.8% / 11.0% / 13.2%.

---

## 5. Manuscript packaging (2026-11-07 SCI rewrite)

- Structure follows user SCI Writing guide: Title → Abstract (8-function) → Keywords → Introduction (3 parts) → Methods (numerical five-module adapted) → Results (provenance → calibration → held-out/CV → ranking) → Discussion → Conclusions → Availability → References.
- Style constraints applied: reduced colon/dash/semicolon load, basic transitions, no defensive placeholders, no local paths in paper body, honest methods framing.
- Word primary deliverable: `docs/manuscript_final.docx` and `C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_final.docx` (figures 1–5 embedded).
- OA reference PDFs stored under `docs/reference_pdfs/` when lawful download succeeded (Worthley MAVERIC; Rottländer Frontiers). Galili RSOS PDF download was blocked by publisher/PMC bot challenges in this session; DOI and structure references remain valid.

---

## 6. What is computed vs table-backed

| Quantity | Status |
|----------|--------|
| Galili published AP / ROA / leak at discrete cases | **Table-backed** (literature) |
| Dryad `contact_fraction` / `n_sph_particles` | **Extracted / fixture-derived** |
| Rule-based blend-off preds | **Computed** (fixed surrogate, blend OFF) |
| Fold-wise f_ROA / f_leak preds | **Computed** (true LOO refit) |
| Planning-map sweep ROA / leak / jet / LCx / NiTi | **Computed** under η assumptions |
| Best candidate / Pareto / LHS stability | **Computed** ranking under assumptions |
| Clinical trial MR volumes | **Not used** as calibration targets |

---

## 7. Irreducible scientific limits

- n=7 Galili peak-systole cases ≠ patient-level external validation
- No patient CT / chamber-labeled SPH leakage recompute
- Algebraic proxies; η and dual factor are assumption priors
- LCx/NiTi screens are literature/engineering screens, not safety clearances
- Ranking is assumption-driven exploratory analysis, not validated clinical prediction
