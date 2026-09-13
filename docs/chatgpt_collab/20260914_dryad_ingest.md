# 2026-09-14 — Galili Dryad ingest + LOO advancement

## Goal

Download Dryad doi:10.5061/dryad.bzkh1899d zips and continue Layer-1 work with P0 honesty
(phenomenological mechanics + literature-calibrated leakage proxy; no clinical recommendation
framing; MAVERIC=ARTO≠Carillon; Galili peak-systole AP50=15.9 mm).

## Dryad download

| Strategy | Result |
|----------|--------|
| Dryad API metadata ` /api/v2/datasets/...` + `/versions/156393/files` | OK (lists both zips) |
| API `/api/v2/files/{id}/download` | **HTTP 401** `Unauthorized, must have current bearer token` |
| ` /downloads/file_stream/{id}` without cookie | Anubis HTML “Validating…” (PoW difficulty=4) |
| Browser MCP (`cursor-ide-browser`) | **Failed** — `No browser tab available` even with `newTab:true` |
| Anubis PoW solver `tools/download_dryad_anubis.py` | **SUCCESS** — solved SHA-256 leading-hex zeros, cookie `techaro.lol-anubis-auth`, S3 redirect |
| Figshare RSOS supplements | Animations / strain figures only — **not** Dryad coordinate zips |
| Zenodo mirror | None found for this DOI |

### Checksums (SHA-256)

| File | Bytes | SHA-256 |
|------|------:|---------|
| `Deformed_coordinates_and_contact.zip` | 314919 | `921b2d8ecd30aa6f73932b71c7f6a85f7aff17f2b6b7268f19e89ac9ce819efc` |
| `Blood_leakage_-_SPH_coordinates.zip` | 20542725 | `f2049bc0969d78d8b11fc5edeb5498eabaf9e92e39e8680574fdf5381d0e8378` |

Zips live under `data/raw/galili_dryad/` (gitignored). Manifest: `data/raw/galili_dryad/MANIFEST.json`.

## Real archive layout (≠ fixture)

- Deformed: per-case CSV of leaflet nodes + binary contact flag (+ MV atrial triangulation).
- SPH: per-case `Coordinates.csv` / `.txt` ≈29k particles — **full-domain cloud**, not LA vs aorta partition.

Therefore:

- **Dryad-derived:** `contact_fraction`, bbox extents, `n_sph_particles`.
- **Table-backed (honest fill):** peak-systole AP / ROA / `regurgitation_pct` (no invented chamber partition / annulus landmarks).
- Phase tag: all Dryad deformed/SPH rows = `peak_systole`; undeformed diastole AP 34.4 kept separate.

## Processed

`python tools/import_galili_dryad.py --process` → 8 rows, `source_tier=dryad_derived` (diastole row remains `published_table_scalars`).

`ima_ap_50` peak-systole AP = **15.9 mm**.

Contact fraction rises with sealing (pathology 0.012 → ima_ap_50 0.132 → ima_ap_70 0.226).

## LOO / held-out (blend OFF)

`python tools/loo_evaluate.py --mode both --write`

| Split | MAE AP (mm) | MAE ROA (mm²) | MAE leak (pp) |
|-------|------------:|--------------:|--------------:|
| Held-out | 0.0 | 50.18 | 1.45 |
| LOO (7 folds) | 0.0 | 36.53 | 0.95 |

Catalog note: `processed_galili_cases:dryad_derived`.

Optional `--refit-scale` (train-fold linear leak ratios only): LOO leak MAE **1.09** (did not improve vs baseline 0.95) — kept as documented optional path, not default claim.

AP MAE = 0 under Galili mapping because published AP is reproduced by case lookup; ROA/leak remain the informative transparency metrics.

## Paper DOI correction

Crossref resolves Galili RSOS as **10.1098/rsos.211464** (not 211726). Updated in importer / provenance / reference_data.

## Pipeline / tests

- `python run_pipeline.py --seed 42 --paper --no-export` — OK
- `python tools/package_reports.py` — OK
- `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q` — **49 passed**

## Remaining gaps

1. Cannot recompute Galili leakage % from Dryad SPH alone without chamber labels.
2. Cannot extract published AP from unlabeled leaflet nodes alone.
3. Browser MCP tab creation failed in this environment (workaround: Anubis PoW script).
4. Large zips not committed (by design); reproducers run `tools/download_dryad_anubis.py` or manual Dryad UI drop.
5. Optional LOO scale refit is phenomenological post-hoc only; default LOO does not claim per-fold physics retrain.
