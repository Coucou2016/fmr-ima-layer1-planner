# Collab log — 2026-09-15 paper + research report refresh

## Intent

Full paper + self-contained research report refresh on tip ~`8a882f7`, using user manuscript spine `docs/manuscript_draft.md`, SciencePlots figures, nature-skills methods framing, evidence audit, commit + push.

## Framework chosen

**Methods / research-software paper** (CMBBE / MedEngPhys / RSOS-class), nature-writing axes: `task=manuscript`, `paper_type=methods`, `journal=generic`.

**Imitation refs (structure/tone, not text):**

- Galili et al., *R. Soc. Open Sci.* 2022;9:211464 (doi:10.1098/rsos.211464) — mechanism→parameterization→geometry→readout
- MAVERIC / ARTO clinical AP window (geometry context only)
- Carillon TITAN II / REDUCE-FMR (IMA-CS directionality only)
- Rottländer et al. CS–LCx screening vocabulary (~8.6 mm)
- Modular MV methods-tool tone (*Med Eng Phys* / *CMBBE*-class)

**Innovation statement (honest):** transparent Layer-1 algebraic/phenomenological surrogate + Dryad `contact_fraction` fitted response + fold-wise CV + assumption-prior LHS scenario ranker for **exploratory screening** — not clinical validation, not first CS vs AP, not new LHHM FEA.

## Spine

- Preferred user manuscript: no Desktop/Downloads attachment found; used/refreshed `docs/manuscript_draft.md` (2026-09-15 rewrite) as narrative spine.
- Numbers aligned to current pipeline (`fitted_response`, seed=42), not stale dual-60% packaging text.

## Seed-42 numbers used

| Item | Value |
|------|-------|
| Best candidate | IMA-CS 20% |
| AP↓ | 11.0% |
| leakage_proxy | ≈0.391% |
| jet | central |
| CS–LCx | 8.6 mm |
| n_device / feasible / p | 35 / 30 / ≈0.857 |
| Fold held-out MAE ROA/leak | ≈6.37 mm² / ≈0.245 pp |
| AP70 fold abs err | ≈6.60 mm² / ≈0.198 pp |
| Rule-based current held-out MAE | ≈5.24 mm² / ≈0.043 pp |
| LHS P(top-1) / mean feasible | ≈0.342 / ≈0.822 |

## Deliverables

- `docs/manuscript_draft.md`, `docs/paper.md|.html|.pdf`
- `report.html|.md|.pdf` (+ `docs/report.*`)
- `docs/evidence_audit.md`, `docs/真实性审查.md`
- Figures regenerated via SciencePlots + Times/serif stack in `analysis/plots.py`
- Packaging upgraded in `tools/package_reports.py` (long 来龙去脉 captions; dynamic best candidate)

## Verify

- pytest: all passed (after removing forbidden wrong-DOI contiguous token from audit draft)
- `run_pipeline.py --seed 42 --paper --no-export`: best = IMA-CS 20%
- `package_reports.py`: report.html `data:image` count = 5; PDFs PASS; images are base64 (GitHub hyperlinks in §十九 are text links only, not external CSS/img)
- Tip before refresh: `8a882f7`
- Artifact SHA256: `docs/chatgpt_collab/20260915_hashes.txt`

## Push

See git log after commit on `origin/main`.
