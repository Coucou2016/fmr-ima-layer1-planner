# P0 scientific review response (2026-09-13)

External review: framing as clinical preoperative decision paper → Reject & Resubmit.
After P0 fixes + repositioning as literature-anchored exploratory low-order surrogate / software-methods paper → Major Revision range.

## Corrections shipped

### 1. Galili AP mapping (CRITICAL)
- **Removed** false premise: IMA-AP 50% → AP 34.4 mm → 0% AP reduction.
- **Locked** peak-systole facts: disease AP 26.1 mm; IMA-AP 50% AP **15.9 mm**; IMA-AP 70% AP 12.4 mm; ROA disease 172.8 mm²; leakage anchors unchanged in %.
- Undeformed diastole AP 34.4 mm kept only with explicit `cardiac_phase`.
- Files: `results/reference_data.yaml`, `results/reference_targets.json`, `models/devices.py`, golden tests.

### 2. MAVERIC ≠ Carillon (CRITICAL)
- MAVERIC = **ARTO** (CS–IAS) ≈ IMA-AP mechanism class.
- Deleted η_CS ≈ 0.668 fitted from MAVERIC 41.4→35.3 at Galili CS 22%.
- Added Carillon / TITAN II ~15% AP context + REDUCE-FMR directionality without fabricating η_CS from MAVERIC.
- η retained only as **assumption priors** (`η_ap=0.30`, `η_cs=0.55`); prefer `target_ap_reduction` as planning variable.

### 3. Terminology downgrade
- “Reduced-order FEA” → algebraic / phenomenological mechanics proxy (`run_mechanics_proxy`; FEA aliases kept).
- “SPH surrogate” → literature-calibrated leakage proxy / SPH-inspired.
- Planner “recommendation” → `best_candidate` / `scenario_ranker` (JSON shim `recommended` retained).
- LCx 8.6 mm → risk-screening threshold; NiTi 0.4% → engineering screen; dual ×0.5 → hypothesis parameter.
- Calibration/reproduction ≠ external validation (“calibrated to and reproduced selected Galili cases”).

### 4. Calibration / held-out split
- `calibration_targets`: pathology, ima_cs_22, ima_ap_50
- `heldout_targets`: ima_cs_14/18, ima_ap_30/70 + leave-one-out plan (Dryad P1)

### 5. Golden tests
- Lock literature provenance + invariants + determinism.
- Do **not** lock dual AP60 / 0.152 / central as scientific truth.
- Assert MAVERIC=ARTO.

### 6. Repositioning
- Title/claims toward exploratory screening surrogate / software-methods.
- README Windows activate path fixed; clinical/deployable language removed.

## Seed-42 after P0 (honest)
- Best candidate under assumptions: IMA-AP dual 60%, AP 18.0%, physics leakage-proxy **~0.074%**, jet=central (36 eval / 30 feasible).
- Ranking coincidence with prior dual-60 pick does **not** restore old Galili AP mapping or MAVERIC=Carillon claims.
- η±20%: dual 70% (η−) / dual 50% (η+) under current assumption priors — sensitivity of ranking, not FEA UQ.

## Remaining P1 / P2
- Dryad import (`doi:10.5061/dryad.bzkh1899d`), leave-one-out scoring, MODEL_CARD / DATA_PROVENANCE.
- Uncertainty-aware / Pareto ranking language enrichment.
- Full pyproject/ruff/matrix CI (P2).
