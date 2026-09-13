# P1 + P2 implementation log — 2026-09-14

## Goal

Fully implement remaining review items after P0 (`17237bc`): Dryad/LOO pipeline,
uncertainty-aware scenario ranking, terminology hygiene, and research-software packaging.

## A. Push / sync

- Local tip at start: `17237bc` (ahead of `origin/main` @ `4e3cc69` by 1).
- `git push origin main` retried; GitHub HTTPS (443) hung / intermittent.
- Continued all work locally; push retried at end of session.

## B. Dryad pipeline

- `tools/import_galili_dryad.py` fleshed out:
  - API metadata + file inventory (version `156393`; two zips).
  - Download attempt; Dryad CDN returns **401** / Anubis HTML interstitial → **manual drop documented**.
  - Expected layout + `data/raw/README.md` + `data/provenance.yaml`.
  - Extraction of AP / contact / leakage descriptors with mandatory `cardiac_phase`.
  - Outputs `data/processed/galili_cases.csv` (+ parquet if available).
  - CI fixture: `data/fixtures/galili_dryad_mini/` via `--from-fixture`.
  - Provenance tiers: `dryad_derived` > `fixture_synthetic` > `published_table_scalars` (secondary).
- `tools/loo_evaluate.py`: held-out + leave-one-case-out blend-OFF scoring; calibration blend-ON marked reproduction-only.
- `DATA_PROVENANCE.md` rewritten with real content.

**Dryad status:** metadata reachable; **zip download blocked** (bot wall). Stub+fixture path implemented; manual drop path documented.

## C. Uncertainty-aware scenario ranking

- `analysis/planner.py` upgraded:
  - `p_feasible`, η assumption-prior sampling, ranking stability, Pareto frontier.
  - Dual-suture commissural factor explicit hypothesis in JSON.
  - Optional `--patient-cs-lcx-mm`; cinch slope labeled assumption.
  - Framing: exploratory screening / best under assumptions (compat `recommended` shim retained).
- `configs/design_space.yaml`: `dual_suture.commissural_factor: 0.5`.

## D. Terminology

- Contact-cluster ROA marked visualization-only (`analysis/roa.py`, `simulation/roa_surrogate.py`).
- Jet dual rule: exploratory hypothesis (`analysis/jet.py`).
- README / MODEL_CARD / manuscript retitled toward software-methods paper.
- Avoid restoring clinical-recommendation framing.

## E. P2 packaging

- `LICENSE` (MIT), `CITATION.cff`, `references.bib`, `MODEL_CARD.md`, `DATA_PROVENANCE.md`
- `pyproject.toml` (setuptools layout; `run_pipeline.py` remains runnable)
- CI matrix Python 3.10–3.12; optional ruff (continue-on-error); pytest-cov
- SciencePlots font: Times → Liberation/STIX/DejaVu fallback (`analysis/plots.py`)

## F. Manuscript

- `docs/manuscript_draft.md` restructured to 8-section software/methods outline.

## G. Tests / commands run

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python tools/import_galili_dryad.py --from-fixture --process
python tools/loo_evaluate.py --write
python run_pipeline.py --seed 42 --paper --no-export
python tools/package_reports.py
```

## Remaining gaps

- Real Dryad zip unpack on this host (requires manual browser download past Anubis).
- No per-fold re-estimation of SPH/ROA scales in LOO (documented transparency check).
- `tools/package_reports.py` HTML may still contain older FEA/SPH wording in Chinese packaging templates — prefer regenerated English manuscript + `scenario_ranking.json` as source of truth; further HTML scrub optional.
- Public push may still fail on GitHub 443.
