# MODEL_CARD.md — FMR IMA Layer-1 exploratory surrogate

## Model details
- Name: `fmr-ima-layer1-planner`
- Version: 0.3.1
- Type: algebraic / phenomenological mechanics proxy + literature-calibrated leakage proxy (SPH-*inspired*) + fold-wise / full-train response models
- Not: reduced-order FEA, production LHHM/Abaqus FSI, clinical decision support

## Intended use
- Exploratory screening / software-methods demonstration under stated assumptions
- Reproduce selected Galili RSOS 2022 peak-systole table anchors (doi:10.1098/rsos.211464)
- Rank discrete IMA-CS / IMA-AP grid points (`scenario_ranker`) with Latin-Hypercube multi-parameter assumption-prior uncertainty
- Report true fold-wise response-model CV (`analysis/fit_response_model.py`) and a separate blend-off diagnostic (`tools/loo_evaluate.py`)

## Response paths (`configs/design_space.yaml` → `response_path`)
| Path | Role |
|------|------|
| **`fitted_response`** (default) | Full-train `f_ROA` / `f_leak` for paper / seed-42 ranking; Dryad `contact_fraction` is an **input feature** (neighbor-interpolated off table) |
| `rule_based_proxy` | Legacy exploratory algebraic + SPH-inspired leak (diagnostics / comparison) |
| `hybrid_ap_extreme` | Rule-based except IMA-AP shortening >50% routed through fitted |

## Out of scope
- Patient-specific validation / patient CT
- Clinical recommendations / medical device programming advice
- Equating physics leakage % with clinical regurgitant volume
- Treating synthetic contact-cluster ROA as independent validation (`cluster_weight=0`)
- Reporting AP MAE as predictive accuracy (AP is literature mapping input)
- Chamber-labeled SPH leakage recompute from Dryad particle clouds

## Training / calibration data
- **Primary provenance when present:** Dryad doi:10.5061/dryad.bzkh1899d via `tools/import_galili_dryad.py` → `data/processed/galili_cases.csv`
- **Auxiliary features in fitted path:** `contact_fraction`, `n_sph_particles` (full-domain cloud; **not** LA↔aorta partition)
- **Scalar AP / ROA / leakage:** table-backed from published Galili peak-systole values unless independently derivable from labeled coordinates
- Fixture: `data/fixtures/galili_dryad_mini/` for CI only

## Official output fields
- `leakage_proxy_pct` (alias of `physics_regurgitation_pct`)
- `strain_risk_score` (alias of `max_principal_strain`)
- `contact_score` (mechanics contact proxy)
- Deprecated aliases retained for compat

## Metrics
- Calibration/reproduction at pathology, ima_cs_22, ima_ap_50 (blend ON)
- Anchor-free / leave-one-case blend-off diagnostic — **not** fold-wise LOO validation
- True fold-wise response-model CV — internal engineering targets only
- Scenario ranker: feasibility schema 36/35/30; `P(top-1)`, `P(feasible)`, Spearman first-order ranks; family-separated Pareto

## Assumptions (labeled)
- η_ap / η_cs = assumption priors (prefer ΔAP planning variable); LHS-sampled with dual factor + CS–LCx baseline/slope (N≈120)
- Dual-suture commissural factor = exploratory hypothesis **sensitivity** (0.25/0.5/0.75/1.0), not discovery
- CS–LCx: prefer patient-measured baseline; cinch slope = labeled assumption
- LCx ≥ 8.6 mm = Rottländer risk-screening threshold, not safety clearance
- NiTi 0.4% = illustrative engineering screen
- 14–20% AP band = **exploratory planning range** (anchor ~14–15%, ceiling 20%)

## Ethical / safety notes
- Do not cite as deployable preoperative clinical software
- Outputs are best candidates under assumptions / exploratory rankings
- Ranking is assumption-driven exploratory analysis, not validated prediction
- Irreducible: n=7 Galili cases; no patient CT; no chamber-labeled SPH leak recompute
