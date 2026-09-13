# Model card — FMR IMA Layer-1 exploratory surrogate

## Model details
- Name: `fmr-ima-layer1-planner`
- Version: 0.2.0
- Type: algebraic / phenomenological mechanics proxy + literature-calibrated leakage proxy (SPH-*inspired*)
- Not: reduced-order FEA, production LHHM/Abaqus FSI, clinical decision support

## Intended use
- Exploratory screening / software-methods demonstration under stated assumptions
- Reproduce selected Galili RSOS 2022 peak-systole table anchors
- Rank discrete IMA-CS / IMA-AP grid points (`scenario_ranker`) with η assumption-prior uncertainty summaries

## Out of scope
- Patient-specific validation
- Clinical recommendations / medical device programming advice
- Equating physics leakage % with clinical regurgitant volume
- Treating synthetic contact-cluster ROA as independent validation

## Training / calibration data
- Primary when present: Dryad doi:10.5061/dryad.bzkh1899d via `tools/import_galili_dryad.py` → `data/processed/galili_cases.csv`
- Secondary: published Galili table scalars (`results/reference_data.yaml`)
- Fixture: `data/fixtures/galili_dryad_mini/` for CI only

## Metrics
- Calibration/reproduction at pathology, ima_cs_22, ima_ap_50 (blend ON)
- Held-out / LOO blend-OFF scores (`tools/loo_evaluate.py`) — transparency check, not patient-level external validation
- Scenario ranker: P(feasible), η ranking stability, Pareto frontier (leakage vs AP↓ vs LCx vs strain)

## Assumptions (labeled)
- η_ap / η_cs = assumption priors (prefer ΔAP planning variable)
- Dual-suture commissural ×0.5 = exploratory hypothesis parameter
- CS–LCx: prefer patient-measured baseline; `11 − 0.12×shortening` = labeled assumption
- LCx ≥ 8.6 mm = Rottländer risk-screening threshold, not safety clearance
- NiTi 0.4% = illustrative engineering screen

## Ethical / safety notes
- Do not cite as deployable preoperative clinical software
- Outputs are best candidates under assumptions / exploratory rankings
