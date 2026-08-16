# ChatGPT collab — literature / framework session (2026-08-16)

## Conversation intent

- Prefer reuse: https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65 (Senior Review FMR Layer-1)
- Goal: enable ChatGPT **web search**, solicit (1) papers to imitate, (2) full writing framework with C1–C3 placement, (3) novelty wording that does **not** claim first IMA-CS vs AP comparison.

## Blocker

Cursor `cursor-ide-browser` could not keep a stable tab this session (`No browser tab available` / viewId evaporates after `browser_tabs` `new`). `cursor-app-control.open_resource` also failed (`unknown agent`). **No paste to ChatGPT was completed.** No LocalBridge dialog observed this turn.

**Parent/user action needed:** open the Senior Review URL in a logged-in Plus session, enable browsing/web search, paste the brief below, and return the reply text to Cursor for verification.

## Text brief to paste (when browser works)

```
Role: senior advisor for an FMR IMA Layer-1 methods manuscript (Python surrogate, NOT new LHHM/Abaqus FSI).

Please use web search / browsing. Propose:
1) 5–8 papers to imitate for structure/tone (Galili RSOS 2022 IMA; MAVERIC/ARTO; Carillon/REDUCE-FMR; CMBBE/MedEngPhys-style MV computational papers). For each: what to imitate vs what not to copy.
2) A full paper writing framework/outline showing where innovations fit:
   C1 clinical dose mapping (suture% → AP%; Galili 50% suture = 0% AP)
   C2 continuous sweep + constrained preoperative planner
   C3 CS–LCx ≥8.6 mm + NiTi alternating strain <0.4%
   optional C4 dual vs single suture at matched AP%
3) How to write novelty WITHOUT claiming the first IMA-CS vs IMA-AP comparison (Galili already did that in LHHM).

Constraints: Layer-1 honesty; physics regurg % ≠ clinical regurgitant volume; η is a planning assumption; seed-42 planner recommends dual IMA-AP 60%, AP 18%, physics 0.152%, jet=central.

Return: bullet outline + novelty phrasing bank + rejection risks. Text only; do not ask me to upload files.
```

## Local verification already applied (without ChatGPT)

Cursor WebSearch confirmed:
- Galili et al. RSOS 2022;9:211464 — LHHM IMA-CS vs IMA-AP comparison (baseline to cite, not to re-claim).
- MAVERIC / ARTO — clinical AP reshaping (~14% class).
- REDUCE-FMR / Carillon — directional MR reduction; coronary compromise risk language.

Installed `nature-skills` at `C:\Users\Administrator\.cursor\skills\nature-skills` and followed `nature-writing` methods playbook into `docs/paper_framework_nature.md`.

## Git

Local-only workspace (no `.git` in project root this environment). No commit/push/PR.
