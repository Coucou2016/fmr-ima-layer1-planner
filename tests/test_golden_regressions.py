"""Golden regressions for manuscript seed-42 planner / dose / safety claims.

These lock numbers cited in docs/manuscript_draft.md so drift between the
Layer-1 surrogate and the paper scaffold fails CI loudly.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.evaluate import evaluate_design_point
from analysis.paper_tables import eta_sensitivity, table_maveric_reduce_fmr_alignment
from analysis.planner import run_planner
from models.devices import (
    CS_LCX_COMPRESSION_THRESHOLD_MM,
    IMA_AP,
    IMA_CS,
    cs_lcx_distance_mm,
)


# Manuscript / recommendation.json seed-42 golden tuple (clinical mapping).
GOLDEN_SEED = 42
GOLDEN_DEVICE = "IMA-AP"
GOLDEN_SHORTENING = 60.0
GOLDEN_N_SUTURES = 2
GOLDEN_AP_REDUCTION_PCT = 18.0
GOLDEN_PHYSICS_REGURG_PCT = 0.152  # rounded manuscript value
GOLDEN_JET = "central"
GOLDEN_N_EVALUATED = 36
GOLDEN_N_FEASIBLE = 30


def test_dose_semantics_galili_50_pct_suture_is_zero_ap_cinch():
    """Galili suture % ≠ clinical AP %: 50% suture → 0% AP reduction."""
    galili50 = IMA_AP(shortening_pct=50, mapping_mode="galili")
    assert abs(galili50.ap_reduction_pct()) < 1e-12
    assert abs(galili50.apply().ap_diameter_mm - 34.4) < 1e-9

    clinical50 = IMA_AP(shortening_pct=50, mapping_mode="clinical")
    assert abs(clinical50.ap_reduction_pct() - 15.0) < 0.05
    # Same suture % must not imply the same AP reduction across mappings.
    assert abs(galili50.ap_reduction_pct() - clinical50.ap_reduction_pct()) > 10.0

    galili70 = IMA_AP(shortening_pct=70, mapping_mode="galili")
    assert abs(galili70.ap_reduction_pct() - 58.43) < 0.05
    assert abs(galili70.apply().ap_diameter_mm - 14.3) < 0.05


def test_golden_planner_seed42_dual_ima_ap_60(tmp_path):
    """Planner golden tuple: dual IMA-AP 60%, AP 18%, physics ≈0.152%, jet=central."""
    rec = run_planner(seed=GOLDEN_SEED, mapping_mode="clinical", output_dir=tmp_path)
    assert rec["n_evaluated"] == GOLDEN_N_EVALUATED
    assert rec["n_feasible"] == GOLDEN_N_FEASIBLE

    r = rec["recommended"]
    assert r is not None
    assert r["device"] == GOLDEN_DEVICE
    assert abs(r["shortening_pct"] - GOLDEN_SHORTENING) < 1e-9
    assert int(r["n_sutures"]) == GOLDEN_N_SUTURES
    assert abs(r["ap_reduction_pct"] - GOLDEN_AP_REDUCTION_PCT) < 0.05
    assert abs(r["physics_regurgitation_pct"] - GOLDEN_PHYSICS_REGURG_PCT) < 0.01
    assert r["jet_location"] == GOLDEN_JET
    assert r["blended_regurgitation_pct"] is None  # physics-only objective

    single = rec["alternatives"]["best_ima_ap_single"]
    assert single is not None
    assert abs(single["shortening_pct"] - 60.0) < 1e-9
    assert single["jet_location"] == "mixed"
    assert single["commissural_fraction"] > r["commissural_fraction"]


def test_cs_lcx_boundary_and_constraint_guard(tmp_path):
    """Default anatomy: bridge 20% → CS–LCx exactly 8.6 mm; 22% violates threshold."""
    assert abs(cs_lcx_distance_mm(20.0) - CS_LCX_COMPRESSION_THRESHOLD_MM) < 1e-12
    assert cs_lcx_distance_mm(22.0) < CS_LCX_COMPRESSION_THRESHOLD_MM - 1e-9

    cs20 = IMA_CS(bridge_shortening_pct=20, mapping_mode="clinical")
    cs22 = IMA_CS(bridge_shortening_pct=22, mapping_mode="clinical")
    assert abs(cs20.cs_lcx_mm() - 8.6) < 1e-12
    assert cs22.cs_lcx_mm() < 8.6 - 1e-9

    rec = run_planner(
        seed=GOLDEN_SEED,
        mapping_mode="clinical",
        enforce_lcx=True,
        output_dir=tmp_path,
    )
    best_cs = rec["alternatives"]["best_ima_cs"]
    assert best_cs is not None
    assert abs(best_cs["shortening_pct"] - 20.0) < 1e-9
    assert abs(best_cs["cs_lcx_mm"] - 8.6) < 1e-9
    assert "cs_lcx" not in (best_cs.get("constraint_violations") or "")

    # With LCx enforced, infeasible points above the threshold must be excluded.
    assert all(
        (p.get("cs_lcx_mm") is None) or (p["cs_lcx_mm"] >= 8.6 - 1e-9)
        for p in [rec["recommended"], best_cs]
        if p is not None
    )


def test_eta_sensitivity_seed42_recommendation_shifts():
    """η±20% must flip the seed-42 recommendation as documented in the manuscript."""
    payload = eta_sensitivity(seed=GOLDEN_SEED)
    by = payload["by_scenario"]

    nom = by["eta_nominal"]
    assert nom["recommended_device"] == "IMA-AP"
    assert abs(nom["recommended_shortening_pct"] - 60.0) < 1e-9
    assert int(nom["n_sutures"]) == 2
    assert abs(nom["ap_reduction_pct"] - 18.0) < 0.05
    assert abs(nom["physics_regurgitation_pct"] - 0.1519) < 0.005
    assert nom["jet_location"] == "central"

    minus = by["eta_minus_20pct"]
    assert minus["recommended_device"] == "IMA-AP"
    assert abs(minus["recommended_shortening_pct"] - 70.0) < 1e-9
    assert int(minus["n_sutures"]) == 2
    assert abs(minus["ap_reduction_pct"] - 16.8) < 0.05
    assert abs(minus["physics_regurgitation_pct"] - 0.0895) < 0.005

    plus = by["eta_plus_20pct"]
    assert plus["recommended_device"] == "IMA-CS"
    assert abs(plus["recommended_shortening_pct"] - 20.0) < 1e-9
    assert abs(plus["ap_reduction_pct"] - 16.036) < 0.05
    assert abs(plus["physics_regurgitation_pct"] - 0.2293) < 0.005

    shifts = {s["scenario"]: s for s in payload["shifts_vs_nominal"]}
    assert shifts["eta_minus_20pct"]["shortening_changed"] is True
    assert shifts["eta_plus_20pct"]["device_changed"] is True
    assert "planning-assumption" in payload["honesty"].lower() or "η" in payload["honesty"]


def test_physics_pct_not_labeled_as_clinical_regurgitant_volume():
    """Alignment / honesty export must refuse magnitude equation with trial RV%."""
    pt = evaluate_design_point(
        device_type="IMA-AP",
        shortening_pct=60,
        mapping_mode="clinical",
        case_id="sweep_ap_dual60_clinical",
        n_sutures=2,
        blend=False,
    )
    rows = table_maveric_reduce_fmr_alignment([pt], recommendation=None)
    assert rows
    assert all(r.get("magnitude_equated") == "false" for r in rows)
    policy = next(r for r in rows if r["source"] == "alignment policy")
    note = (policy.get("note") or "").lower()
    assert "physics" in note
    assert "regurgitant-volume" in note or "regurgitant volume" in note
    assert "not equate" in note or "do not equate" in note


def test_scienceplots_available_and_paper_figures_high_dpi():
    """Paper figures must be regenerable under SciencePlots at dpi≥300 sizing."""
    import scienceplots  # noqa: F401
    from matplotlib.font_manager import FontProperties, findfont

    resolved = findfont(FontProperties(family="Times New Roman"))
    assert "times" in resolved.lower()

    fig_dir = ROOT / "results" / "output" / "paper_figures"
    required = [
        "fig1_ima_ap_nonmonotonic_clinical_window.png",
        "fig2_suture_vs_ap_reduction.png",
        "fig3_jet_location.png",
        "fig4_pareto_lcx_strain.png",
        "fig5_dual_vs_single_suture.png",
    ]
    from PIL import Image

    for name in required:
        path = fig_dir / name
        assert path.is_file(), f"missing {name}; run pipeline --paper"
        w, _h = Image.open(path).size
        # ~8.5 in × 300 dpi with tight bbox ≈ ≥2000 px wide
        assert w >= 2000, f"{name} width {w} looks below dpi≥300 quality"
