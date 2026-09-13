# Data provenance

| Source | DOI / ID | Role in Layer-1 |
|--------|----------|-----------------|
| Galili et al. RSOS 2022 | 10.1098/rsos.211726 | Peak-systole AP / ROA / leakage table anchors |
| Galili Dryad supporting | 10.5061/dryad.bzkh1899d | Planned full import (`tools/import_galili_dryad.py`); not yet used for training |
| MAVERIC (ARTO System) | clinical series | IMA-AP-class AP window context (~14–15%); **not** Carillon |
| Carillon TITAN II | clinical series | IMA-CS AP context ~15%; not η_CS fit |
| REDUCE-FMR | JACC HF 2019 | Directional regurg ↓ for Carillon / IMA-CS |
| Rottländer et al. 2021 | CS–LCx | Risk-screening threshold 8.6 mm |

Machine-readable stub: `data/provenance.yaml` (created by import script).
