# 2026-11-07 SCI paper Word rewrite

## Task

Rewrite FMR IMA Layer-1 project into a complete publishable English Word manuscript following the Desktop SCI Writing guide, Nature proposal/writing skills, and humanizer anti-slop constraints. Align all numbers to seed-42 pipeline outputs.

## Deliverables shipped

| Artifact | Path |
|----------|------|
| Final Markdown | `docs/manuscript_final.md` |
| Paper mirror | `docs/paper.md` (copied from final) |
| Word manuscript | `docs/manuscript_final.docx` |
| Desktop Word copy | `C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_final.docx` |
| Evidence audit | `docs/evidence_audit.md` (refreshed) |
| References | `references.bib` (expanded with DOIs) |
| Docx builder | `tools/build_manuscript_docx.py` |
| OA PDFs | `docs/reference_pdfs/Worthley_MAVERIC_EuroIntervention.pdf`, `docs/reference_pdfs/Rottlander_2022_Frontiers_CS_MVA.pdf` |

## Paper structure used (SCI guide)

1. Title (methods / model evaluation framing)
2. Abstract (eight functional sentences)
3. Keywords
4. Introduction (background → literature gap → objectives)
5. Methods (object/data → formulation → implementation → calibration → verification)
6. Results (provenance → Level-0 calibration → held-out/CV → ranking → clinical directionality)
7. Discussion (interpretation → literature comparison → limits)
8. Conclusions (overview + five verifiable points)
9. Availability / reproducibility / statements
10. References with DOIs

## Seed-42 numbers included

- Fold-wise held-out MAE ROA 6.37 mm², leak 0.245 pp
- IMA-AP70 fold abs err 6.60 mm² / 0.198 pp
- Rule-based held-out MAE 5.24 mm² / 0.043 pp
- Ranking: 36 / 35 / 30 feasible, p≈0.857
- Best: IMA-CS 20%, AP↓ 11.0%, leak proxy 0.391%, jet central, CS–LCx 8.6 mm
- LHS N=120, P(top-1)≈0.342, mean feasible≈0.822
- η±20%: AP↓ 8.8 / 11.0 / 13.2%, top device unchanged

## OA refs downloaded

- Worthley MAVERIC EuroIntervention PDF: success
- Rottländer Frontiers CS–MVA PDF: success
- Galili RSOS 2022 PDF: blocked by Cloudflare / PMC captcha in this environment; DOI 10.1098/rsos.211464 retained; Unpaywall confirms OA CC-BY without direct PDF URL in API

## Humanizer / style application

Cloning of named GitHub humanizer repos failed (E: disk nearly full). Principles still applied from skill guidance and user hard rules: fewer colons/dashes/semicolons, basic transitions, no defensive placeholders, no “first CS vs AP”, MAVERIC=ARTO, dual suture = hypothesis sensitivity, paper ≠ work report.

## Pipeline / test status

- Existing seed-42 JSON artifacts used as ground truth (scenario_ranking, CV summary, loo_evaluation, paper_tables).
- Full pytest run started but aborted due to disk pressure / hung process on E: (~1 GB free).
- Docx build succeeded; figures 1–5 embedded from `results/output/paper_figures/`.
- Re-run recommended when disk space is restored: `python run_pipeline.py --seed 42 --paper` then `python tools/build_manuscript_docx.py`.

## Irreducible limits (unchanged)

n=7 Galili table; no patient CT; no chamber-labeled SPH recompute; η/dual priors; LCx/NiTi screens only; ranking exploratory not clinical.
