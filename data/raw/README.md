# Raw data drop zone

## Galili et al. RSOS 2022 supporting files

- Paper: https://doi.org/10.1098/rsos.211726
- Dryad: https://doi.org/10.5061/dryad.bzkh1899d
- Dryad API dataset: `https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.bzkh1899d`
- Known version id: `156393`

### Automated download

```powershell
python tools/import_galili_dryad.py --download
python tools/import_galili_dryad.py --process
```

Dryad's CDN may return HTTP 401 or an Anubis "Validating..." HTML interstitial
to non-browser clients. If that happens, download the two zips manually from
the Dryad UI and drop them here:

```
data/raw/galili_dryad/Deformed_coordinates_and_contact.zip
data/raw/galili_dryad/Blood_leakage_-_SPH_coordinates.zip
```

Do **not** commit large binary archives unless explicitly approved.

### Fixture (CI / offline)

```powershell
python tools/import_galili_dryad.py --from-fixture --process
```

### Phase honesty

Never mix undeformed/diastolic AP (34.4 mm) with peak-systolic ROA/leakage
without an explicit `cardiac_phase` column. See `EXPECTED_LAYOUT` in
`tools/import_galili_dryad.py`.

### Provenance tiers

| Tier | Meaning |
|------|---------|
| `dryad_derived` | Features extracted from local Dryad zips / unpacked trees |
| `fixture_synthetic` | Tiny synthetic smoke layout under `data/fixtures/` |
| `published_table_scalars` | Secondary fallback from `results/reference_data.yaml` |

Layer-1 calibration still uses published peak-systole table scalars unless a
Dryad-derived processed table is present and selected by LOO / calibration
configs.
