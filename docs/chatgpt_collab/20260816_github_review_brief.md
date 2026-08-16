# ChatGPT brief — FMR GitHub review (2026-08-16)

**Repo (public, full code/docs readable):** https://github.com/Coucou2016/fmr-ima-layer1-planner  
**Commit:** `5c1394cfe643a4cb9ee994547c4f746ca9925f95`  
**Role:** You are text-only senior advisor. Cursor implements. You may **web-search** and **read the public GitHub repo** (no file upload needed).

## Please do (in order)

1. Open/read the GitHub repo README and skim structure.
2. Read these paths on GitHub (raw or web UI):
   - `docs/paper_framework_nature.md`
   - `docs/manuscript_draft.md`
   - `docs/paper_plan.md`
   - `analysis/planner.py`, `analysis/design_sweep.py`, `analysis/jet.py` (high level)
   - `results/clinical_references.yaml` (anchors)
3. Web-search for closely related IMA / CS annuloplasty / Galili LHHM / MAVERIC / REDUCE-FMR computational or clinical planning literature you would imitate or cite.
4. Deliver **exactly** these sections:

### A. Literature imitation list
5–10 papers/works to imitate (title, venue/year if known, what to imitate: structure / claims / figures / limitations wording). Prefer flagship biomechanics / cardiology computational papers; distinguish clinical device trials from model papers.

### B. Novelty phrasing (1 short paragraph + 3 bullet “claims we may make” + 3 “claims we must NOT make”)
Ground novelty in: Layer-1 deployable planner + clinical dose mapping (suture%→AP%) + jet location + LCx screening boundary — **not** new LHHM/Abaqus FSI.

### C. Report / paper improvements
Concrete, prioritized edits for `report.html` / `docs/manuscript_draft.md` / framework (wording only unless a factual inconsistency). Flag anything that overclaims Level-2 evidence.

### D. Residual risks for §十九
Short checklist for dual-agent packaging (reproducibility, η sensitivity, anatomy assumptions, physics% ≠ clinical regurgitant volume).

## Constraints already accepted
- Layer-1 surrogate ≠ continuum FEA / living-heart FSI.
- Galili suture % ≠ clinical AP %; MAVERIC ~14–15% AP window is the clinical reference, not Galili 50% numerical extreme.
- Seed-42 golden: dual suture 60% / AP 18% / physics regurg 0.152% / jet=central.
- LCx 8.6 mm = literature screening boundary (Rottländer), not patient-specific clearance.
- Do **not** invent diffs against unseen private files; the public repo is the source of truth.

Please reply with A–D only; keep citations honest (mark uncertain years/venues).
