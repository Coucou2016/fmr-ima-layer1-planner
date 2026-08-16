# Round 03 — Results narrative + figure 来龙去脉

**Date:** 2026-08-16  
**Mode:** Local maturation (ChatGPT browser **BLOCKED**)

## (1) Ready brief for ChatGPT

For each of Fig 1–5 in the public repo / manuscript, propose a 3–5 sentence “来龙去脉” (why the figure exists → how to read → what decision it supports) without inventing new numbers. Seed-42 truth only: dual 60%, AP 18%, physics 0.152%, jet=central; η table flips; CS 20% at CS–LCx 8.6 mm.

Also flag any Results prose that still equates physics % with clinical regurgitant volume.

## (2) Advisor reply status

**No live ChatGPT reply.** Local expansion of Results + strengthening `tools/package_reports.py` figure captions (report.html source).

## (3) Independent verify

- Cross-checked planner JSON / η CSV: 36/30, dual 60%, 18%, 0.152%, η flips match tables already in draft.
- Existing report figure blocks were already strong; added explicit planner-decision links and “筛查≠安全” title language for Fig 4.

## (4) Applied edits

- Results §3: methods-paper framing paragraph + **来龙去脉** lead-ins for 3.1–3.5.
- Figure captions Fig 1–5: physics≠clinical volume; LCx screening; mechanism-sketch for Fig 5.
- `package_reports.py` FIGURES fig2–fig5 caption text strengthened for report.html regeneration.

## (5) Packaging / tests

Deferred to Round 05 regenerate (HTML/MD/PDF will pick up new captions).

## Accepted / Rejected

| Item | Decision |
|------|----------|
| Per-subsection 来龙去脉 | **Accepted** |
| New FEA/LHHM numbers | **Rejected** (none invented) |
| Dual suture as device clearance | **Rejected** |

## Files touched

- `docs/manuscript_draft.md`
- `tools/package_reports.py`
- `docs/chatgpt_collab/rounds/round_03.md`
