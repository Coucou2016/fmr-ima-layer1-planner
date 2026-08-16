# Functional Mitral Regurgitation (FMR) — IMA Computational Biomechanics

**Public repository:** https://github.com/Coucou2016/fmr-ima-layer1-planner

Computational comparison of **Indirect Mitral Annuloplasty** strategies for functional mitral regurgitation (FMR):

- **IMA-CS** — coronary sinus anchors + NiTi bridge shortening (14%, 18%, 22%)
- **IMA-AP** — suture between coronary sinus and interatrial septum (30%, 50%, 70%)

This repository provides a **Layer-1 Python 3 surrogate** (reduced-order FEA + SPH leak index) for **preoperative IMA design planning**. It is **not** a new LHHM/Abaqus FSI study and does not claim new finite-element results of the living heart model.

Paper-facing additions (see `docs/paper_plan.md`):

1. **Clinical dose mapping** — suture/bridge shortening % → AP diameter reduction (mm / %), with the MAVERIC ~14–15% window (not Galili’s 50% AP numerical extreme).
2. **Deployable planner** — continuous parameter sweep + constrained grid search.
3. **LCx safety** — CS–LCx ≥ 8.6 mm in the distal landing zone (Rottländer 2021).
4. **Jet location** — `central` / `commissural` / `mixed`, with ROA split.

## Quick start

```bash
cd e:\Projects\20260522-Functional-Mitral-Regurgitation-FMR
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt   # includes SciencePlots (Times New Roman figures, dpi≥300)
python run_pipeline.py --seed 42
python run_pipeline.py --seed 42 --paper
```

Writing scaffold: `docs/paper_framework_nature.md` (Nature-skills methods outline). Optional Cursor skill install: `~/.cursor/skills/nature-skills` (`nature-writing`).

Sweep / planner only:

```bash
python -m analysis.design_sweep --seed 42
python -m analysis.planner --seed 42
python -m analysis.design_sweep --paper --seed 42
```

Tests (Windows conda may need plugin autoload off):

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
```

Main command: **`python run_pipeline.py`**

Outputs land in `results/output/`:

| Artifact | Description |
|----------|-------------|
| `case_metrics.csv` / `.json` | Per-case scalars (discrete Galili YAML cases) |
| `paper_comparison_table.csv` | Simulated vs reference regurgitation |
| `calibration_report.json` | Residuals, blend weights, physics-before-blend, tradeoff notes |
| `sweep/design_sweep.csv` | Continuous IMA-AP / IMA-CS / dual-suture physics scan |
| `planner/recommendation.json` | Constrained preoperative recommendation + jet location |
| `paper_tables/` | Galili vs surrogate; clinical window vs extreme; Pareto; MAVERIC/REDUCE-FMR directionality; dual-vs-single; η±20% sensitivity |
| `paper_figures/*.png` | Non-monotonic IMA-AP curve, AP-dose map, jet location, Pareto, dual suture (tracked; regenerate with `--paper`) |
| `contacts/*_contact_map.csv` | Synthetic contact node maps |
| `strain/*_strain.json` | Principal strain + NiTi bridge strain |
| `fea_export/*.inp`, `*_annulus.vtk` | External solver hooks |
| `*.png` | Discrete-case regurgitation comparison plots |

Published validation numbers live in:

- `results/reference_targets.json` — pytest anchor subset
- `results/reference_data.yaml` — full paper/spec table (geometry, materials, contact patterns, trends)
- `results/clinical_references.yaml` — MAVERIC / REDUCE-FMR / LCx 8.6 mm / Galili mapping table

## Project structure

```
configs/          Case YAML (pathology, IMA-CS, IMA-AP, design_space)
models/           Geometry, materials, pathology PM logic, device + clinical AP mapping
simulation/       Pressure loading, FEA surrogate, Abaqus/VTK export hooks
sph/              ~29k-particle reduced-order regurgitation model
analysis/         ROA, jet classifier, metrics, sweep, planner, paper tables/plots
docs/paper_plan.md  C1–C3 contributions, figure list, validation levels 0/1/2
docs/manuscript_draft.md  Chinese-primary manuscript scaffold with seed-42 numbers
results/          Reference targets, clinical_references.yaml, pipeline outputs
tests/            pytest validation
run_pipeline.py   End-to-end entry point (`--sweep`, `--plan`, `--paper`)
```

## Mapping to paper / research specs

| Component | Implementation | Full FEA (commercial) |
|-----------|----------------|------------------------|
| LHHM heart (LV, LA, MV, chordae, PM, CS) | Parametric annulus/AP geometry + synthetic PM mesh | Hook: `simulation/fea_export.py` → `.inp`, `.vtk` |
| Pathology: 44% posterior PM passive, 100 mV vs 20 mV | `models/pathology.py` | Element sets in external deck |
| IMA-CS NiTi 14-param | `models/materials.py` stub + annulus shrink calibration | UMAT / *HYPERELASTIC in Abaqus |
| IMA-AP ePTFE 0.074 mm² | `models/materials.py` + `IMA_AP` geometry | Distributed coupling in solver |
| LV/LA 50 ms offset, peak systole 75% | `simulation/loading.py` | *AMPLITUDE curves in INP |
| ROA: contact + geometric search | `analysis/roa.py` + `simulation/roa_surrogate.pipeline_roa_mm2` | Post-process contact CSV |
| SPH ~29k particles, regurgitation ratio | `sph/hemodynamics.py` (ROA×gap leak index + anchors) | Full SPH code external |
| Clinical AP dose mapping + CS–LCx | `models/devices.py`, `results/clinical_references.yaml` | Patient CT + echo |
| Jet location / planner | `analysis/jet.py`, `analysis/design_sweep.py`, `analysis/planner.py` | Intra-op echo / device IFU |

### Expected validation targets

| Case | Regurgitation % | Notes |
|------|-----------------|-------|
| Pathology | 5.26 | Baseline |
| IMA-CS 22% | 0.29 | Annulus 118.5 → 115 mm |
| IMA-AP 50% | 0.08 | ROA min 27.3 mm², AP 34.4 mm |
| IMA-AP 70% | > IMA-AP 50% | AP 14.3 mm, commissural leak |

## Calibration transparency

| File | Role |
|------|------|
| `configs/surrogate_calibration.yaml` | Regurgitation anchors, blend weights (physics vs anchor), ROA anchors, SPH leak-index parameters |
| `results/reference_targets.json` | Paper targets for tests and the summary table |
| `results/output/calibration_report.json` | Per-run residuals, blend weights, and ROA vs anchor (generated by `run_pipeline.py`) |

**Regurgitation** at anchor cases: `(1 − w) × physics + w × anchor` with `w` from `regurgitation_anchor_blend`. Intermediate shortening levels are not snapped.

**ROA**: `pipeline_roa_mm2()` blends model estimate (88%) with contact-cluster area (12%). Per-case RNG uses `stable_case_seed()` (MD5 of case id) so results do not depend on `PYTHONHASHSEED`.

**SPH leak index**: `ROA × (coaptation_gap / gap_ref)^power`, scaled at pathology; commissural IMA-AP 70% uses a separate AP/gap penalty branch.

## Data provenance

| Source | Role |
|--------|------|
| `results/reference_data.yaml` | Canonical structured paper/spec numbers and trend constraints |
| `results/reference_targets.json` | Machine-readable anchors for tests and summary tables |
| `configs/surrogate_calibration.yaml` | Honest reporting calibration (blend weights, ROA pipeline weights) |
| `configs/pathology.yaml`, `ima_*_cases.yaml` | Case definitions and device parameters |

Synthetic contact maps and annulus VTK rings are **consistent with surrogate coaptation/ROA** (not clinical imaging). They exist so `analysis/roa.py` clustering and export hooks can be exercised reproducibly.

## How to verify credibility

1. Run `python run_pipeline.py --seed 42` and inspect `results/output/calibration_report.json`:
   - `physics_regurgitation_pct` vs `simulated_regurgitation_pct` shows anchor blend impact
   - `tradeoff_notes` documents mechanism vs reporting choices
2. Run `python -m pytest tests/ -q` (set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` on Windows conda if needed).
3. Compare `paper_comparison_table.csv` to `results/reference_data.yaml` anchors.
4. Confirm monotonic trends: IMA-CS 22% &lt; pathology; IMA-AP 50% optimum; IMA-AP 70% &gt; 50%.
5. Run `python run_pipeline.py --seed 42 --paper` and inspect `results/output/paper_figures/` (physics regurgitation) plus `planner/recommendation.json`.

**Main paper figures use physics regurgitation**, not the YAML blend. The blend exists only at Galili validation case IDs.

## Limitation matrix

| Topic | Validated | Illustrative only |
|-------|-----------|-------------------|
| Annulus/AP geometry at anchor cases | Yes (parametric device models) | Full 3D LHHM mesh |
| Regurgitation % at pathology / IMA-CS 22% / IMA-AP 50% | Yes (± test tolerance, blended) | Intermediate shortening exact values |
| ROA at IMA-AP 50% minimum | Yes (±2.5 mm² vs 27.3) | Cluster-derived patch area |
| NiTi 14-param hyperelastic | Material stub | Abaqus UMAT |
| SPH 29k particles | Count honored | Full Lagrangian SPH solver |
| Contact node forces | Synthetic patch | Abaqus contact export |

## File inventory

```
configs/          pathology + IMA cases + surrogate_calibration.yaml + design_space.yaml
models/           geometry, materials, pathology, devices (Galili + clinical AP mapping)
simulation/       FEA surrogate, ROA, calibration, export hooks
sph/              reduced-order hemodynamics
analysis/         ROA clustering, jet, metrics, plots, sweep, planner, paper tables
docs/             paper_plan.md, manuscript_draft.md
results/          reference_data.yaml, clinical_references.yaml, reference_targets.json, output/
tests/            pytest (pipeline, anchors, calibration, reference data, sweep/planner)
.github/workflows/ci.yml
run_pipeline.py
requirements.txt
```

**Paper figures / tables:** Everything under `results/output/` is gitignored except `.gitkeep` placeholders in `paper_figures/` and `paper_tables/`. After clone, run `python run_pipeline.py --seed 42 --paper` to regenerate the five PNGs and CSVs. CI asserts those files exist after `--paper`.

## Assumptions and limitations

1. **No live Abaqus/LHHM coupling** — `run_fea_surrogate()` is a reduced-order model relating annulus shrinkage, pathology severity, and coaptation gap to strain/contact.
2. **SPH** — particle count is honored (~29,000). Regurgitation is computed from ROA, coaptation gap, annulus tightening, and commissural-leak physics (`sph/hemodynamics.py`). Published percentages in `configs/surrogate_calibration.yaml` are blended only at validation case IDs (not hard-coded `if case_id` branches in the pipeline).
3. **ROA** — `simulation/roa_surrogate.py` estimates orifice area from coaptation gap; contact nodes are synthesized for clustering (`analysis/roa.py`). Paper ROA anchors are softly blended for reporting at pathology / IMA-AP 50%.
4. **Geometry** — diastolic AP 34.4 mm and annulus 118.5 mm are defaults; devices apply parametric deformation (`models/devices.py`).
5. **Reproducibility** — default `--seed 42`; per-case RNG via `stable_case_seed()` (MD5 of case id). Pin deps in `requirements.txt` (numpy/scipy/matplotlib/PyYAML/pandas minimum versions).
6. **ROA vs regurgitation** — IMA-AP 50% can show low regurgitation % while ROA remains near the published minimum (~27 mm²); the surrogate couples but does not equate these scalars.
7. **Design optimization** — `python -m analysis.design_sweep` and `python -m analysis.planner` (grid search on the surrogate). Constraints: AP reduction ≤ 20% (configurable), NiTi alternating strain &lt; 0.4%, IMA-CS CS–LCx ≥ 8.6 mm.
8. **Not new LHHM FEA** — do not cite sweep/planner numbers as Abaqus/LHHM results. Validation level 2 (full FSI) is out of scope; see `docs/paper_plan.md`.

## Extending to production FEA

1. Export annulus/heart meshes: `results/output/fea_export/<case>.inp`
2. Map materials from `models/materials.py` into solver cards.
3. Replace `run_fea_surrogate()` with solver subprocess reading contact nodal forces.
4. Feed ROA into `sph/hemodynamics.py` or replace SPH with exported particle VTK time series.

## License

Research / educational demo scaffold — verify clinical claims independently before any clinical use.
