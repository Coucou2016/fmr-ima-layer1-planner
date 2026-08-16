# Paper framework (Nature-skills + literature-informed)

**Axes (nature-writing):** `task=manuscript` · `paper_type=methods` · `language=zh-to-en` (scaffold bilingual) · `journal=generic` (target: computational biomechanics / CMBBE / MedEngPhys / RSOS-class methods outlet — **not** flagship *Nature* unless claims and evidence escalate).

**One-sentence argument:** In preoperative IMA planning for FMR, we show that a Layer-1 surrogate can map suture/bridge shortening onto clinically attainable AP reduction, jet location, and LCx safety, using constrained design sweep + planner on a reproducible Python physics channel, supported by Galili Level-0 anchors and seed-42 planner outputs, with the boundary that this is **not** new LHHM/Abaqus FSI and η is a planning assumption.

**Honesty boundary (non-negotiable):** Do not claim first IMA-CS vs IMA-AP comparison (Galili et al. RSOS 2022 already did that in LHHM). Do not equate physics regurgitation % with clinical regurgitant volume. Do not present η±20% as FEA UQ.

---

## 1. Suitable papers to imitate (structure / tone)

Sources: Cursor WebSearch + ChatGPT Plus web-search reply (2026-08-16) saved at `docs/chatgpt_collab/20260816_chatgpt_literature_reply.txt` (conversation https://chatgpt.com/c/6a807186-6f88-83ea-afc5-49dddcff3a65). Lead independently keeps claim discipline below.

| Role | Paper / source | What to imitate | What **not** to copy |
|------|----------------|-----------------|----------------------|
| Mechanistic FEA baseline | Galili, White Zeira, Marom. *R. Soc. Open Sci.* 2022;9:211464 | mechanism→parameterization→geometry→functional surrogate; taxonomy IMA-CS vs IMA-AP; non-monotonic IMA-AP discussion | Do **not** claim new LHHM/FEA/SPH; do **not** re-claim “first CS vs AP comparison” |
| Clinical AP window | Worthley / MAVERIC (JACC Cardiovasc Interv 2015; later 1–2 y reports): AP ≈45→38.7 mm (~14%) or 41.4→35.3–36 mm (~13–15%) | separate geometry endpoints from MR endpoints | Do not calibrate physics % to clinical MR volume; do not claim 18% modeled AP predicts ARTO efficacy |
| CS device directionality | Witte et al. REDUCE-FMR (*JACC Heart Fail* 2019) | restrained causal language; coronary compromise awareness | Not “validated against REDUCE-FMR” — only directional context |
| LCx screening | Rottländer et al. 2021 (*Catheter Cardiovasc Interv*): distal landing CS–Cx **&lt;8.6 mm** predicted compromise in their ROC | procedural-planning / feasible vs infeasible vocabulary | Do **not** say “≥8.6 mm is safe”; say literature-informed **screening** boundary |
| Methods-tool tone | de Oliveira et al. 2023 *Med Eng Phys* geometry-based MV FE tool; Siefert et al. 2015 *CMBBE* isolated geometry effects | modular Methods; isolated-variable sweeps; separate jet vs magnitude | Do not import FE stress/contact “ground truth” language |
| NiTi screen context | Kumar et al. / nitinol fatigue literature citing ~0.4% alternating-strain endurance in tested specimens; TITAN II fracture history | fatigue as **admissibility** criterion separate from efficacy | Do not claim “fatigue safe / infinite life / FDA-equivalent” |

**Critical wording fix (ChatGPT + lead accepted):** Do **not** write “Galili showed that 50% suture = 0% AP.” Prefer: *“In the Layer-1 Galili-mapping table, the published discrete 50% suture case retains diastolic AP = 34.4 mm (0% mapped AP cinch); this is a planner coordinate / discrete-case table convention, not a prose finding to attribute as Galili’s clinical conclusion.”*

**Tone target:** methods paper (RSOS/CMBBE/MedEngPhys-class), Nature-skills **claim discipline** — not flagship *Nature* unless evidence escalates.

---

## 2. Full outline (where C1–C3 fit)

### Title
Clinically constrained preoperative planning of indirect mitral annuloplasty: mapping suture dose to AP-diameter reduction, jet location, and LCx safety on a Layer-1 surrogate

### Abstract (nature-writing: context → gap → approach → result → boundary)
1. FMR / IMA clinical need (1–2 sentences).
2. Gap: suture/bridge % is not clinical AP dose; discrete Galili-mapping 50% case has 0% mapped AP cinch (AP 34.4 mm table convention); 70% is numerical extreme (~58% AP).
3. Approach: Layer-1 Python surrogate + clinical mapping (η) + constrained planner + jet/LCx.
4. Result (seed=42): dual IMA-AP 60%, AP 18%, physics regurg 0.152%, jet=`central`; η±20% flips recommendation.
5. Boundary: not production FEA; η not imaging–FEA identified.

### Introduction (paragraph jobs)
| ¶ | Job | Content |
|---|-----|---------|
| 1 | context | FMR mechanisms; IMA-CS (Carillon-class) vs IMA-AP (CS–IAS / ARTO-class) |
| 2 | gap | Computational suture % ≠ clinical AP %; cite Galili dose semantics |
| 3 | clinical scale | MAVERIC ~14–15% AP; REDUCE-FMR directionality only |
| 4 | approach + contributions | C1 dose map; C2 planner; C3 LCx/NiTi; optional C4 dual suture; Level-1 scope |

**Novelty without “first CS vs AP”:** claim *preoperative clinical-dose planning layer* that *translates* Galili-style computational settings into AP-mm space with explicit safety constraints — not a new LHHM duel.

### Related work / Background
- Percutaneous IMA devices (Carillon, ARTO/MAVERIC).
- Computational MV / FSI / LHHM (Galili as Level-2 reference).
- Planning surrogates and reduced-order models in cardiovascular device design.
- Explicit: this work sits between clinical constraint literature and full FEA.

### Methods (write first per methods playbook)
1. Pathology + parametric geometry.
2. **C1** Galili vs clinical AP mapping; η documented assumption.
3. Reduced-order FEA / ROA / SPH leak index; physics vs YAML blend boundary.
4. Jet classifier.
5. **C2** Sweep grids + planner objective (physics only).
6. **C3** CS–LCx ≥ 8.6 mm; NiTi alternating strain < 0.4%.
7. Optional **C4** dual vs single at matched AP %.
8. η±20% sensitivity protocol.
9. Reproducibility: seed 42, `run_pipeline.py --paper`, pytest golden regressions.

### Results / Experiments
1. Level-0 Galili anchors (blended + physics columns).
2. Clinical window vs numerical extreme (Fig 1–2).
3. Planner recommendation + alternatives (Fig 3–4).
4. Dual vs single matched AP (Fig 5).
5. η sensitivity table (decision flips).

### Discussion
- Dose semantics (Galili 50% = 0% AP).
- Planner as screening tool before Level-2 FEA.
- LCx illustrative anatomy caveat.
- η sensitivity as scientific signal, not bug.
- Directionality-only clinical alignment.

### Limitations / Conclusion
Mirror `docs/paper_plan.md` limitation matrix; end with bounded claim + next step (patient CT η calibration / Level-2 confirmation).

### Figures (SciencePlots + Times New Roman, dpi≥300)
Fig 1–5 as in `docs/paper_plan.md` / `results/output/paper_figures/`.

---

## 3. Novelty phrasing bank (approved)

Use:
- “We encode clinical AP dose, jet location, and LCx safety into a reproducible Layer-1 preoperative planner.”
- “We separate Galili suture parameterization from clinically attainable AP reduction.”
- “We show planner recommendations are sensitive to the transfer-efficiency assumption η.”

Avoid:
- “First computational comparison of IMA-CS and IMA-AP.”
- “Validates Carillon/ARTO efficacy.”
- “Patient-specific FSI results.”
- “Physics 0.152% equals clinical regurgitant fraction.”

---

## 4. Nature-skills compliance checklist

- [x] One-sentence argument + boundary stated
- [x] Methods paper drafting order preferred
- [x] Claim verbs calibrated
- [x] Evidence = seed-42 artifacts + golden tests
- [ ] Full EN prose polish of every section (ongoing in `manuscript_draft.md`)
- [ ] Citation manager / DOI lock via `nature-citation` (future)

---

## 5. ChatGPT collab note

Prefer pasting this framework’s §1–3 into the Senior Review chat for critique of structure/tone only (text paste, no files). Apply only advice that survives local verification against Galili/MAVERIC/REDUCE-FMR and repo outputs.
