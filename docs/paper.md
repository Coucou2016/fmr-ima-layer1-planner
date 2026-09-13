# 稿件草稿 / Manuscript draft (Layer-1 exploratory surrogate)

**EN title:** Literature-anchored low-order surrogate for exploratory screening of indirect mitral annuloplasty strategies

**中文工作题：** 文献锚定的低阶代理模型：间接二尖瓣成形策略的探索性筛查

**工作短题:** FMR IMA Layer-1 exploratory surrogate

**Venue class:** methods / computational biomechanics software paper (CMBBE / MedEngPhys / RSOS-class) — not a clinical decision trial.

**One-sentence argument:** We provide a transparent, literature-anchored algebraic surrogate that reproduces selected Galili peak-systole anchors and ranks exploratory IMA-CS / IMA-AP scenarios under explicit geometric and screening assumptions—without claiming new LHHM FEA, clinical recommendation, or independent external validation of blended cases.

**Data:** `python run_pipeline.py --seed 42 --paper` (reproducible Layer-1 outputs only).

**Verification levels:** Level 0 = calibrated to / reproduced selected Galili cases; Level 1 = exploratory planning map + scenario ranker. Level 2 patient-specific LHHM/FSI is out of scope.

---

## Abstract

**Background:** Computational IMA studies (Galili et al., *R. Soc. Open Sci.* 2022) report suture/bridge shortening and peak-systolic geometry/leakage. Those percentages are mechanical parameterizations. Peak-systolic IMA-AP 50% yields AP **15.9 mm** (near-direct AP effect), not undeformed diastole **34.4 mm**. Clinical device classes also differ: MAVERIC evaluates the **ARTO** (CS–IAS / IMA-AP-class) system; Carillon / REDUCE-FMR are IMA-CS-class.

**Methods:** We implement a reproducible Python Layer-1 surrogate: an algebraic mechanics proxy plus a literature-calibrated leakage proxy (SPH-inspired). Two maps are available—(i) Galili peak-systole geometry reproduction; (ii) an exploratory planning map using assumption-prior transfer efficiencies η (not clinically calibrated constants; η_CS is **not** fitted from MAVERIC/ARTO). A discrete scenario ranker minimizes physics leakage-proxy regurgitation subject to an AP ceiling, an illustrative NiTi engineering screen, and a Rottländer CS–LCx **risk-screening** threshold. Dual-suture commissural ×0.5 is an explicit hypothesis parameter. Main figures use physics only; YAML anchor blending is restricted to calibration case IDs and constitutes **reproduction**, not external validation.

**Results (seed=42):** Under the planning map the ranker evaluates 36 points and retains 30 feasible designs. Best candidate under stated assumptions: **IMA-AP dual suture 60%** (assumption η_ap=0.30 → AP reduction **18.0%**, physics leakage-proxy **~0.074%**, jet=`central`). Best feasible IMA-CS on default anatomy: bridge **20%** (CS–LCx **8.6 mm** at the risk-screen edge). Galili peak-systole map: IMA-AP 50% AP **15.9 mm**; IMA-AP 70% AP **12.4 mm** with commissural leak and higher leakage than 50%.

**Conclusions:** A literature-anchored low-order surrogate can support **exploratory screening** of IMA strategy settings with inspectable assumptions. It is not a preoperative clinical decision system, does not equate physics % with clinical regurgitant volume, and must not treat high anchor-weight reproduction as independent validation.

**Keywords:** functional mitral regurgitation; indirect mitral annuloplasty; surrogate model; exploratory screening; coronary sinus; Layer-1

### 中文摘要（要点）

文献锚定的低阶代理，用于 IMA-CS / IMA-AP 探索性筛查；纠正 Galili 峰缩期 AP 映射与 MAVERIC=ARTO 归类；η 为假设先验；输出为假设下最优候选而非临床推荐；physics % ≠ 临床反流容积。

---

## 1. Introduction

Functional mitral regurgitation (FMR) reflects ventricular remodeling, annular dilatation, and impaired leaflet coaptation. Indirect mitral annuloplasty (IMA) concepts remodel annular geometry without direct leaflet repair. **IMA-CS** (Carillon-class coronary-sinus devices) and **IMA-AP** (CS–IAS suture; ARTO / MAVERIC mechanism class) are not mechanically interchangeable.

Galili et al. (2022) compared generic IMA-CS and IMA-AP in the Living Heart Human Model and reported peak-systolic AP, ROA, and leakage. IMA-AP acts nearly directly on AP diameter (disease 26.1 mm → IMA-AP 50% → **15.9 mm**). Undeformed diastolic AP 34.4 mm is a different cardiac phase and must not be paired with peak-systolic ROA/leakage without phase tags.

What remains for software methods is transparent **dose translation and exploratory ranking** under stated assumptions—not a claim of first CS-vs-AP comparison, not new FEA, and not a clinical recommendation engine. MAVERIC AP pairs (~14–15%) contextualize ARTO / IMA-AP-class geometry; Carillon TITAN II (~15% AP) and REDUCE-FMR (regurg ↓ directionality) contextualize IMA-CS without fabricating η_CS from MAVERIC.

---

## 2. Methods

**Pathology and geometry.** Parametric papillary pathology (44% posterior passive). Undeformed diastole: AP 34.4 mm, annulus 118.5 mm. Galili peak-systole disease AP 26.1 mm.

**Device kinematics.** `models/devices.py`: Galili mode interpolates published peak-systolic AP; clinical/planning mode uses assumption-prior η or preferred `target_ap_reduction_pct`. η_ap=0.30 and η_cs=0.55 are **assumption priors** (`configs/design_space.yaml`). Invalid prior η_CS≈0.668 from MAVERIC→Carillon is removed.

**Mechanics and leakage proxies.** `run_mechanics_proxy` (alias `run_fea_surrogate`) returns uncalibrated coaptation-gap / strain / contact proxy scores. `sph/hemodynamics.py` is a literature-calibrated leakage proxy. Physics regurg % ≠ clinical regurgitant volume.

**Calibration vs held-out.** Calibration IDs: pathology, ima_cs_22, ima_ap_50. Held-out: ima_cs_14/18, ima_ap_30/70 with leave-one-out plan (`configs/surrogate_calibration.yaml`). High blend weight = reproduction.

**Scenario ranker.** Minimizes physics leakage proxy subject to AP ≤ 20%, NiTi alternating strain &lt; 0.4% (engineering screen), CS–LCx ≥ 8.6 mm (Rottländer risk screen; prefer patient-measured CS–LCx; cinch slope `11−0.12×shortening` is an assumption). JSON: `best_candidate` (+ compat `recommended`).

**Dual suture.** Commissural penalty ×0.5 is a hypothesis parameter; results are hypothesis-generating.

---

## 3. Results (seed=42)

### 3.1 Galili peak-systole anchors (reproduction)

| Case | Leakage % | Peak-sys AP mm | ROA mm² |
|------|-----------|----------------|---------|
| pathology | 5.26 | 26.1 | 172.8 |
| ima_cs_22 | 0.29 | 24.8 | 48.2 |
| ima_ap_50 | 0.08 | **15.9** | 27.3 |
| ima_ap_70 | 0.13 | 12.4 | 46.1 |

Surrogate blended reports at calibration IDs reproduce leakage within test tolerances. Intermediate / held-out leakage is physics-driven and not claimed as validated.

### 3.2 Exploratory scenario ranking (planning map)

- Evaluated **36** / feasible **30**
- **Best candidate under assumptions:** IMA-AP dual **60%**, AP **18.0%**, physics **~0.074%**, jet=`central`, commissural fraction **0.165**
- Single-suture 60%: physics **~0.075%**, jet=`mixed`, commissural fraction **0.33**
- Best IMA-CS: **20%** bridge, AP **11.0%**, physics **~0.156%**, CS–LCx **8.6 mm**, NiTi alt. strain **0.34%**

η±20% (assumption-prior sensitivity): dual 70% (η−, AP 16.8%, physics ~0.044%); dual 50% (η+, AP 18.0%, physics ~0.112%). Not FEA UQ.

### 3.3 Directionality-only clinical context

ARTO/MAVERIC: AP↓. Carillon TITAN II: ~15% AP context. REDUCE-FMR: regurg↓. Magnitudes not equated to physics %.

---

## 4. Discussion / limitations

Central advance: transparent literature-anchored exploratory screening software with corrected Galili peak-systole AP semantics and correct MAVERIC=ARTO device-class mapping. Limitations: algebraic proxies; held-out Galili leakage (esp. AP70) not tightly reproduced without blend; no patient-specific validation; η are priors; LCx/NiTi screens are literature/engineering screens not safety clearances.

---

## 5. Conclusion

A Layer-1 literature-anchored surrogate can rank exploratory IMA scenarios under explicit assumptions after correcting peak-systole Galili AP facts and MAVERIC device-class attribution. It should be cited as methods/software for exploratory screening—not as clinical preoperative decision support.

---

*Collab / Forbidden-claim notes:* see `docs/chatgpt_collab/20260913_p0_review_response.md` and `docs/paper_framework_nature.md` (scaffold, not main-text claims).
