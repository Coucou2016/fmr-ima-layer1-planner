# 2026-11-07 SCI paper → Word rewrite (disk emergency)

## Disk emergency actions
- E: was critically low (~11 MB at interrupt; later ~2 GB after cleanup).
- Deleted fake Galili Cloudflare stub `docs/reference_pdfs/Galili_2022_RSOS_211464.pdf` (~21 KB HTML, not a real PDF). Cite DOI `10.1098/rsos.211464` + Dryad `10.5061/dryad.bzkh1899d` instead of blocking on publisher PDF.
- Large optional local PDFs already off E: under
  - `C:\Users\Administrator\Desktop\FMR_reference_pdfs_moved\`
  - `F:\fmr_ref_pdfs\`
  (Worthley MAVERIC ~2.1 MB; Rottländer Frontiers ~2.7 MB)
- Staging mirror moved to `F:\_fmr_flat_staging` (regenerable via `tools/build_flat_mirror.py`).
- Cleared `__pycache__` / pytest / ruff caches under the project.
- Heavy manuscript outputs written first to Desktop (C:), then copied into `docs/` once E had headroom.

## Deliverables
1. `docs/manuscript_final.md` (synced with `docs/paper.md`)
2. Word primary: `C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_final.docx`
3. Word copy: `docs/manuscript_final.docx`
4. Desktop markdown mirror: `C:\Users\Administrator\Desktop\FMR_IMA_Layer1_manuscript_final.md`

## Style / framing applied
- Exploratory Layer-1 surrogate (not clinical planner).
- MAVERIC = ARTO (IMA-AP class); Carillon / REDUCE-FMR = IMA-CS.
- Dual suture = hypothesis sensitivity (Figure 5).
- Galili doi:10.1098/rsos.211464.
- Short sentences; reduced colon/dash/semicolon; no 链路/闭环/耦合; no 待确定 placeholders; seed-42 numbers retained.

## Key seed-42 numbers retained
- Fold-wise held-out MAE: ROA 6.37 mm², leak 0.245 pp
- IMA-AP 70% fold abs err: 6.60 mm² / 0.198 pp
- Rule-based held-out MAE: 5.24 mm² / 0.043 pp
- Ranking: n=36 / 35 device / 30 feasible / p=0.857
- Best: IMA-CS 20%, AP↓ 11%, leak proxy 0.391%, CS–LCx 8.6 mm
- LHS N=120: P(top-1)=0.342, mean feasible 0.822
- η±20%: top stays IMA-CS 20% with AP↓ 8.8 / 11.0 / 13.2%
