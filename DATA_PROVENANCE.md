# Data provenance

| Source | DOI / ID | Role in Layer-1 |
|--------|----------|-----------------|
| Galili et al. RSOS 2022 | 10.1098/rsos.211726 | Peak-systole AP / ROA / leakage table anchors |
| Galili Dryad supporting | 10.5061/dryad.bzkh1899d | Preferred feature source when local zips present (`tools/import_galili_dryad.py`) |
| Published table scalars | `results/reference_data.yaml` | **Secondary** path when Dryad archives are unavailable |
| Fixture mini-tree | `data/fixtures/galili_dryad_mini/` | CI smoke layout only |
| MAVERIC (ARTO System) | clinical series | IMA-AP-class AP window context (~14–15%); **not** Carillon |
| Carillon TITAN II | clinical series | IMA-CS AP context ~15%; not η_CS fit |
| REDUCE-FMR | JACC HF 2019 | Directional regurg ↓ for Carillon / IMA-CS |
| Rottländer et al. 2021 | CS–LCx | Risk-screening threshold 8.6 mm |

## Processed table

- Output: `data/processed/galili_cases.csv` (optional `.parquet` if pyarrow available)
- Every row carries `cardiac_phase`. Undeformed diastole (AP 34.4 mm) is never merged into peak-systole ROA/leakage without that tag.
- `source_tier`: `dryad_derived` | `fixture_synthetic` | `published_table_scalars`

## Calibration vs held-out

Configured in `configs/surrogate_calibration.yaml` and mirrored in `results/reference_data.yaml`:

| Split | Case IDs | Use |
|-------|----------|-----|
| `calibration_targets` | pathology, ima_cs_22, ima_ap_50 | Anchor blend / scale setting (**reproduction**) |
| `heldout_targets` | ima_cs_14, ima_cs_18, ima_ap_30, ima_ap_70 | Blend-off scoring vs published quantities |

LOO / held-out runner: `python tools/loo_evaluate.py --write`

High anchor-weight reproduction is **not** independent external validation.

## Manual Dryad drop

If automated download hits HTTP 401 / Anubis interstitial, place:

```
data/raw/galili_dryad/Deformed_coordinates_and_contact.zip
data/raw/galili_dryad/Blood_leakage_-_SPH_coordinates.zip
```

then:

```powershell
python tools/import_galili_dryad.py --process
```

Machine-readable stub: `data/provenance.yaml`.
