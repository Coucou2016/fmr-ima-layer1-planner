# Model card — FMR IMA Layer-1 exploratory surrogate

## Model details
- Name: `fmr-ima-layer1-planner`
- Version: 0.3.0
- Type: algebraic / phenomenological mechanics proxy + literature-calibrated leakage proxy (SPH-*inspired*) + fold-wise response-model diagnostic
- Not: reduced-order FEA, production LHHM/Abaqus FSI, clinical decision support

## Intended use
- Exploratory screening / software-methods demonstration under stated assumptions
- Reproduce selected Galili RSOS 2022 peak-systole table anchors (doi:10.1098/rsos.211464)
- Rank discrete IMA-CS / IMA-AP grid points (`scenario_ranker`) with independent η_AP/η_CS assumption-prior uncertainty
- Report true fold-wise response-model CV (`analysis/fit_response_model.py`) and a separate blend-off diagnostic (`tools/loo_evaluate.py`)

## Out of scope
- Patient-specific validation
- Clinical recommendations / medical device programming advice
- Equating physics leakage % with clinical regurgitant volume
- Treating synthetic contact-cluster ROA as independent validation
- Reporting AP MAE as predictive accuracy (AP is literature mapping input)

## Training / calibration data
- **Primary provenance when present:** Dryad doi:10.5061/dryad.bzkh1899d via `tools/import_galili_dryad.py` → `data/processed/galili_cases.csv` for **auxiliary descriptors** (`contact_fraction`, `n_sph_particles`)
- **Scalar AP / ROA / leakage:** table-backed from published Galili peak-systole values unless independently derivable from labeled coordinates (current archive does not support inventing AP/ROA/leak from unlabeled nodes)
- Fixture: `data/fixtures/galili_dryad_mini/` for CI only

## Metrics
- Calibration/reproduction at pathology, ima_cs_22, ima_ap_50 (blend ON)
- Anchor-free / leave-one-case blend-off diagnostic (`tools/loo_evaluate.py`) — **not** fold-wise LOO validation
- True fold-wise response-model CV (`results/output/cross_validation/`) — internal engineering targets only
- Scenario ranker: `n_total_points`, `n_device_candidates`, `n_feasible_device_candidates`, `p_feasible_device_candidates`; family-separated Pareto frontiers

## Assumptions (labeled)
- η_ap / η_cs = assumption priors (prefer ΔAP planning variable); sampled independently by default
- Dual-suture commissural factor = exploratory hypothesis parameter (sensitivity 0.25/0.5/0.75/1.0)
- CS–LCx: prefer patient-measured baseline; `11 − 0.12×shortening` = labeled assumption
- LCx ≥ 8.6 mm = Rottländer risk-screening threshold, not safety clearance
- NiTi 0.4% = illustrative engineering screen
- 14–20% AP band = clinically contextualized exploratory planning range (anchor ~14–15%, ceiling 20%)

## Ethical / safety notes
- Do not cite as deployable preoperative clinical software
- Outputs are best candidates under assumptions / exploratory rankings
- Ranking is assumption-driven exploratory analysis, not validated prediction
