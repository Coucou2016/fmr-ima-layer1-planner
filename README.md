# FMR IMA Layer-1 planner — literature-anchored low-order surrogate

**Public repository:** https://github.com/Coucou2016/fmr-ima-layer1-planner

Exploratory screening of **Indirect Mitral Annuloplasty (IMA)** strategies for functional mitral regurgitation (FMR) with a **literature-anchored Layer-1 Python surrogate**:

- **IMA-CS** — coronary sinus / Carillon-class bridge shortening
- **IMA-AP** — CS–IAS suture (ARTO / MAVERIC mechanism class)

This is an **algebraic / phenomenological mechanics proxy** plus a **literature-calibrated leakage surrogate** (SPH-*inspired*). It is **not** reduced-order FEA, not production LHHM/Abaqus FSI, and **not** a clinical decision aid. Outputs are best candidates under stated surrogate assumptions (`scenario_ranker`), not recommendations.

## Quick start (Windows)

```powershell
cd E:\Projects\20260522-Functional-Mitral-Regurgitation-FMR
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_pipeline.py --seed 42
python run_pipeline.py --seed 42 --paper
```

Tests:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
```

Sweep / scenario ranker / Dryad / LOO:

```powershell
python -m analysis.design_sweep --seed 42
python -m analysis.planner --seed 42
python tools/import_galili_dryad.py --from-fixture --process
python tools/loo_evaluate.py --write
python tools/package_reports.py
```

## Critical literature facts (Galili RSOS 2022)

Peak systole (do **not** mix with undeformed diastole AP = 34.4 mm):

| Case | ROA mm² | AP mm | Leakage % |
|------|---------|-------|-----------|
| Disease | 172.8 | 26.1 | 5.26 |
| IMA-CS 22% | 48.2 | 24.8 | 0.29 |
| IMA-AP 50% | 27.3 | **15.9** | 0.08 |
| IMA-AP 70% | 46.1 | 12.4 | 0.13 |

IMA-AP has a near-direct effect on AP diameter. Claiming IMA-AP 50% → AP 34.4 mm / 0% AP reduction was an error (fixed in P0).

**Device classes:** MAVERIC = **ARTO** (≈ IMA-AP), **not** Carillon / IMA-CS. Carillon context: TITAN II ~15% AP; REDUCE-FMR directional only. η values are **assumption priors**, not clinically calibrated constants.

## Seed-42 exploratory ranking

Under clinical/planning map, assumption η_ap=0.30, η_cs=0.55 (assumption), AP ceiling 20%, LCx risk screen:

- Evaluated **36** / feasible **30** (P(feasible)≈0.83)
- **Best candidate under assumptions:** IMA-AP dual suture **60%**, AP reduction **18.0%**, physics leakage-proxy **~0.074%**, jet=`central`
- Best IMA-CS: bridge **20%**, AP **11.0%**, CS–LCx **8.6 mm** (risk-screen edge), physics **~0.156%**
- Ranker also emits η ranking stability + Pareto frontier in `results/output/planner/scenario_ranking.json`

Physics % ≠ clinical regurgitant volume. Dual-suture ×0.5 jet factor is an **exploratory hypothesis** parameter.

## Project structure

```
configs/          Case YAML + surrogate_calibration.yaml + design_space.yaml
models/           Geometry, pathology, devices (Galili peak-systole + planning map)
simulation/       Algebraic mechanics proxy (aliases: run_fea_surrogate)
sph/              Literature-calibrated leakage proxy (SPH-inspired)
analysis/         ROA, jet, sweep, scenario_ranker, paper tables/plots
tools/            Dryad import, LOO evaluate, package_reports
data/             raw/, fixtures/, processed/galili_cases.csv
docs/             manuscript_draft.md, chatgpt_collab/
results/          reference_data.yaml, clinical_references.yaml, outputs
tests/            literature facts + invariants (not locked dual-AP60 “truth”)
```

## Calibration vs reproduction vs validation

| Term | Meaning here |
|------|----------------|
| Calibration / reproduction | Anchor blend at `pathology`, `ima_cs_22`, `ima_ap_50` |
| Held-out / LOO | `ima_cs_14/18`, `ima_ap_30/70` + leave-one-case-out (`tools/loo_evaluate.py`) |
| External validation | **Not claimed** for high-anchor-weight cases |

Dryad (doi:10.5061/dryad.bzkh1899d) is the preferred feature source when local zips are present; published table scalars are secondary. See `DATA_PROVENANCE.md`.

## Honesty checklist

- Prefer `contact_score` / `strain_risk_score` language; N/% outputs are uncalibrated proxies
- Synthetic contact-cluster ROA is visualization-only
- LCx ≥ 8.6 mm = Rottländer **risk-screening** threshold, not safety; prefer patient CT CS–LCx
- NiTi 0.4% = illustrative engineering screen only
- `11 − 0.12×shortening` CS–LCx slope = assumption
- Do not cite as deployable preoperative clinical software

## Citation / license

MIT (`LICENSE`). See `CITATION.cff`, `references.bib`, `MODEL_CARD.md`.
