# ChatGPT engineering task brief — FMR Layer-1 paper advance (2026-08-15)

## Attachment

- ZIP: `fmr_source_baseline_20260815.zip`
- Size: 68382 bytes
- SHA-256: `FB81A567268F97B6140FF342CDEDBEE9504FF7A6AC42D1025083228260B97A6C`
- Git baseline: **no commits** (directory is not a git repository); dirty working-tree snapshot after local pytest + `--paper` run.
- Secret-scan: OK (45 files packaged; no `.env`/keys/tokens).

## Background / goals

Python Layer-1 **surrogate** for preoperative Indirect Mitral Annuloplasty (IMA) planning (IMA-CS / IMA-AP). Contributions C1–C3 (+ optional dual-suture D) are implemented. Tests and `run_pipeline.py --seed 42 --paper --no-export` already pass on Cursor’s machine.

**User need:** continue advancing the paper/pipeline; find remaining problems; fix and push work forward.

**Primary remaining gap:** manuscript Methods (and Abstract) lack English prose suitable for an English-facing paper scaffold. Code/CI are largely green.

## Architecture & boundaries

- Entry: `run_pipeline.py` (`--seed`, `--paper`, `--no-export`, sweep/plan flags).
- Packages: `models/`, `simulation/`, `sph/`, `analysis/`, `configs/`, `tests/`, `results/` (references only in ZIP; generated `results/output/**` excluded).
- Honesty: Level-0 Galili anchors + Level-1 clinical mapping/planner. **Level-2 LHHM/Abaqus FSI out of scope.**
- Main paper figures use **physics** regurgitation; YAML blend only at Galili validation case IDs.
- η (transfer efficiency) is a **planning assumption**, not new FEA identification.
- Do **not** call this surrogate “production FEA validation”.

## Scope (do these)

### Must deliver (P0)

1. Add a full **English Methods** section to `docs/manuscript_draft.md` (keep existing Chinese Methods table; add bilingual structure, e.g. `## 2. Methods` with EN prose + retain CN mapping).
   - Cover: pathology/geometry; Galili vs clinical AP mapping (`η`); reduced-order FEA + ROA + SPH leak index; jet classifier; design sweep grid; constrained planner (AP≤20%, NiTi alt strain <0.4%, CS–LCx≥8.6 mm); paper artifact generation; validation levels 0/1 vs 2 out of scope.
   - Numbers must match seed-42 outputs already documented (planner dual 60% / 18% AP / 0.152% physics; η±20% table; Galili anchors). Prefer citing measured rounded values from `paper_tables/` semantics rather than inventing new digits.
   - Explicit honesty paragraphs on blend vs physics, η, illustrative CS–LCx baseline 11.0 mm, directionality-only clinical alignment.

2. Add an **English Abstract** paragraph under/beside the existing Chinese Abstract (same factual claims as Chinese Abstract / Results).

### Should deliver (P1) if low cost

3. Tighten manuscript Galili physics wording for `ima_ap_50` from “~0.18” to “~0.177” (or “0.177”) to match `galili_vs_surrogate.csv`.
4. Optionally add 1–2 short English Discussion bullets on η sensitivity honesty (without rewriting the whole Discussion).
5. CI: also assert `results/output/paper_tables/eta_sensitivity.csv` exists (json already asserted).
6. Optional: write `paper_summary.json` table/figure paths as **repo-relative** instead of absolute Windows paths (behavioral change only in JSON strings; no metric change).

### Out of scope

- No new FEA solver, no claiming Level-2 validation.
- No git commit/push/PR (Cursor lead applies patches locally).
- No dependency upgrades unless required for a failing test you introduce.
- No large refactors of surrogate physics.

## Deliverables

1. **Unified diff patch** (preferred) and/or full file contents for changed files.
2. **Short report** (≤1 page): files touched, what changed, tests you expect Cursor to run, residual risks.
3. If patch is large, prioritize `docs/manuscript_draft.md` first, then CI/path polish.

## Required tests (Cursor will run after apply)

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD=1; python -m pytest tests/ -q
python run_pipeline.py --seed 42 --paper --no-export
```

Acceptance also checks 5 PNGs under `results/output/paper_figures/` and paper tables including `eta_sensitivity.json` (+ csv if you add CI assert).

## Forbidden claims / actions

- Do not describe outputs as production FEA / new LHHM / Abaqus FSI validation.
- Do not equate Layer-1 physics regurgitation % with trial regurgitant-volume magnitudes.
- Do not invent new numeric results that contradict seed-42 tables.
- Do not include secrets, `.env`, or generated bulky `results/output` blobs in the reply ZIP if any.
- Do not ask the human to run commands for you; provide patch + report only.

## Acceptance criteria

- [ ] English Abstract present and consistent with seed-42 planner/η/Galili facts.
- [ ] English Methods present, module-faithful, honesty-compliant, no Level-2 claims.
- [ ] No regressions: pytest all pass; paper pipeline regenerates 5 figures + tables.
- [ ] Any code/CI edits are minimal and justified.
- [ ] Short report lists residual risks.

## Cursor lead independent verification notes (already done)

- 34/34 pytest PASS.
- Paper pipeline PASS; planner recommendation matches manuscript core numbers.
- ZIP secret-scan OK.
