# Round 04 — Methods completeness + claim audit

**Date:** 2026-08-16  
**Mode:** Local maturation (ChatGPT browser **BLOCKED**)

## (1) Ready brief for ChatGPT

Audit Methods claims against this forbidden list; return only phrases that still violate:

1. “validated clinical conversion” (prefer clinically referenced mapping)
2. “CS–LCx ≥ 8.6 mm is safe”
3. NiTi “fatigue safe / cleared / infinite life”
4. Level-2 / patient-specific FSI results claimed as done
5. physics regurgitation % presented as clinical regurgitant volume
6. η presented as imaging–FEA identification

Also list any missing Methods elements for a methods paper (assumptions, grids, objective, reproducibility seed).

## (2) Advisor reply status

**No live ChatGPT reply.** Local claim audit against literature reply + WebSearch Rottländer wording.

## (3) Independent verify

- Grep/manual pass on Methods: added explicit claim-audit paragraph.
- Confirmed Galili mapping described as table convention in Methods C1.
- Confirmed NiTi and LCx described as screens; MAVERIC window ~13–15%.

## (4) Applied edits

- Methods C1–C3: clinically referenced mapping; Galili table-convention disclaimer; LCx screening; NiTi engineering screen; no Level-2 claims.
- Added **Claim audit (Methods boundary)** allow/forbid list.
- Physics % ≠ clinical volume stated at leak-index paragraph.

## (5) Packaging / tests

Deferred to Round 05.

## Accepted / Rejected

| Item | Decision |
|------|----------|
| Clinically referenced mapping | **Accepted** |
| Explicit Methods claim audit box | **Accepted** |
| “Validated against REDUCE-FMR” | **Rejected** |
| Level-2 claims | **Rejected** |

## Files touched

- `docs/manuscript_draft.md`
- `docs/chatgpt_collab/rounds/round_04.md`
