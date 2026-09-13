# Model card — FMR IMA Layer-1 exploratory surrogate (stub)

## Model details
- Name: fmr-ima-layer1-planner
- Type: algebraic / phenomenological mechanics proxy + literature-calibrated leakage proxy
- Not: reduced-order FEA, production LHHM/Abaqus FSI, clinical decision support

## Intended use
- Exploratory screening / software-methods demonstration under stated assumptions
- Reproduce selected Galili RSOS 2022 peak-systole table anchors

## Out of scope
- Patient-specific validation
- Clinical recommendations
- Equating physics leakage % with clinical regurgitant volume

## Training / calibration data
- Published Galili table scalars (`results/reference_data.yaml`)
- Dryad supporting archive: doi:10.5061/dryad.bzkh1899d (import scaffold; full training P1)

## Metrics
- Calibration/reproduction at pathology, ima_cs_22, ima_ap_50
- Held-out plan for remaining Galili cases (leave-one-out)

## Ethical / safety notes
- LCx 8.6 mm = risk-screening threshold (Rottländer), not safety clearance
- NiTi 0.4% = illustrative engineering screen
