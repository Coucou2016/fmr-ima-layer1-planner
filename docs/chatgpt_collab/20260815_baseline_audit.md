# Baseline audit — 2026-08-15

## Repo state

- **Git:** not a git repository (no commits). Baseline = working tree snapshot.
- **AGENTS.md / CLAUDE.md / package.json:** absent (Python research repo; N/A).
- **Docs read:** `README.md`, `docs/paper_plan.md`, `docs/manuscript_draft.md`, `.github/workflows/ci.yml`, `pytest.ini`.

## Independent verification (Cursor lead)

| Check | Result |
|-------|--------|
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q` | **PASS** (34 tests) |
| `python run_pipeline.py --seed 42 --paper --no-export` | **PASS** |
| 5 paper PNGs present | **PASS** |
| Paper tables + `eta_sensitivity.json` | **PASS** |
| Planner recommendation | IMA-AP dual 60%, AP 18.0%, jet=central, physics regurg 0.152% |

## Number consistency (manuscript vs seed-42)

| Claim in `manuscript_draft.md` | Measured | Status |
|--------------------------------|----------|--------|
| Planner dual 60%, 18.0% AP, 0.152% regurg, jet=central | matches `recommendation.json` | OK |
| η−20% → dual 70%, 16.8%, ~0.090 | actual physics **0.0895** | OK (rounding) |
| η+20% → IMA-CS 20%, ~16.0%, 0.229 | actual **16.036%**, **0.2293** | OK (rounding) |
| Galili pathology physics ~5.34 | **5.3383** | OK |
| Galili ima_ap_50 physics ~0.18 | **0.1771** | OK (slightly loose wording) |
| Dual vs single 50/60/70 table | matches `dual_vs_single_matched_ap.csv` | OK |

## Remaining gaps (prioritized for ChatGPT)

1. **P0 — English Methods prose missing.** §2 Methods is a Chinese module-mapping table only. Need a full English Methods section suitable for submission (still Layer-1 honest; no Level-2 FEA claims).
2. **P1 — English Abstract missing.** Abstract is Chinese-only; EN title exists but no EN abstract paragraph.
3. **P1 — Introduction / Discussion still Chinese outlines.** Expand EN Methods first; optionally light EN Discussion honesty on η (already partly in Chinese).
4. **P2 — CI gap (minor):** asserts `eta_sensitivity.json` but not `eta_sensitivity.csv` (both are written).
5. **P2 — `paper_summary.json` embeds absolute Windows paths** — prefer repo-relative paths for portability.
6. **P2 — Cosmetic:** `tests/test_pipeline.py` has excessive blank lines (double newlines between every statement).
7. **Not gaps:** tests green; figures regenerate; η honesty strings present; do not call surrogate “production FEA validation”.

## Forbidden claims (reaffirm)

- Do not present Level-1 surrogate as new LHHM/Abaqus FSI / production FEA validation.
- η is a planning assumption, not imaging–FEA identification.
- MAVERIC/REDUCE-FMR alignment is directionality-only.
