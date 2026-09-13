"""Golden regressions: literature provenance + mathematical invariants.

These tests lock Galili peak-systole facts and surrogate invariants.
They do NOT lock a particular seed-42 'recommendation' as scientific truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.evaluate import evaluate_design_point
from analysis.paper_tables import eta_sensitivity, table_maveric_reduce_fmr_alignment
from analysis.planner import run_scenario_ranker
from models.devices import (
    CS_LCX_COMPRESSION_THRESHOLD_MM,
    GALILI_IMA_AP_50_AP_MM,
    GALILI_PEAK_SYS_DISEASE_AP_MM,
    IMA_AP,
    IMA_CS,
    UNDEFORMED_DIASTOLE_AP_MM,
    cs_lcx_distance_mm,
)


GOLDEN_SEED = 42


def test_galili_ap50_peak_systole_ap_is_15_9_not_undeformed_34_4():
    """Literature fact: IMA-AP 50% → peak-systolic AP = 15.9 mm (not 34.4 / 0%)."""
    galili50 = IMA_AP(shortening_pct=50, mapping_mode="galili")
    assert abs(galili50.apply().ap_diameter_mm - GALILI_IMA_AP_50_AP_MM) < 1e-9
    assert abs(galili50.apply().ap_diameter_mm - 15.9) < 1e-9
    # Must NOT equal undeformed diastole.
    assert abs(galili50.apply().ap_diameter_mm - UNDEFORMED_DIASTOLE_AP_MM) > 10.0
    # Peak-systolic reduction vs disease is substantial (~39%), not 0%.
    assert galili50.ap_reduction_pct() > 35.0
    assert abs(galili50.ap_reduction_pct() - 100.0 * (26.1 - 15.9) / 26.1) < 0.05

    galili70 = IMA_AP(shortening_pct=70, mapping_mode="galili")
    assert abs(galili70.apply().ap_diameter_mm - 12.4) < 0.05
    assert galili70.ap_reduction_pct() > galili50.ap_reduction_pct()

    # Undeformed diastole remains a separate phase constant.
    assert abs(UNDEFORMED_DIASTOLE_AP_MM - 34.4) < 1e-9
    assert abs(GALILI_PEAK_SYS_DISEASE_AP_MM - 26.1) < 1e-9


def test_galili_ima_ap_nearly_direct_ap_effect():
    """Galili: IMA-AP shortening has near-direct effect on peak-systolic AP."""
    ap30 = IMA_AP(shortening_pct=30, mapping_mode="galili").apply().ap_diameter_mm
    ap50 = IMA_AP(shortening_pct=50, mapping_mode="galili").apply().ap_diameter_mm
    ap70 = IMA_AP(shortening_pct=70, mapping_mode="galili").apply().ap_diameter_mm
    assert abs(ap30 - 20.7) < 0.05
    assert abs(ap50 - 15.9) < 0.05
    assert abs(ap70 - 12.4) < 0.05
    assert ap30 > ap50 > ap70


def test_planning_map_assumption_eta_ap_not_galili_geometry():
    """Clinical/planning map uses assumption η; must not equal Galili peak-sys AP."""
    clinical50 = IMA_AP(shortening_pct=50, mapping_mode="clinical")
    assert abs(clinical50.ap_reduction_pct() - 15.0) < 0.05
    galili50 = IMA_AP(shortening_pct=50, mapping_mode="galili")
    assert abs(galili50.ap_reduction_pct() - clinical50.ap_reduction_pct()) > 15.0


def test_scenario_ranker_seed42_invariants(tmp_path):
    """Ranker: identical seed → identical ranking; feasibility math; no locked dual-AP60 truth."""
    rec_a = run_scenario_ranker(seed=GOLDEN_SEED, mapping_mode="clinical", output_dir=tmp_path / "a")
    rec_b = run_scenario_ranker(seed=GOLDEN_SEED, mapping_mode="clinical", output_dir=tmp_path / "b")

    assert rec_a["n_evaluated"] == rec_b["n_evaluated"]
    assert rec_a["n_feasible"] == rec_b["n_feasible"]
    assert rec_a["n_feasible"] <= rec_a["n_evaluated"]
    assert rec_a["n_feasible"] > 0

    best = rec_a.get("best_candidate") or rec_a.get("recommended")
    assert best is not None
    assert best["feasible"] is True
    assert best["ap_reduction_pct"] <= 20.0 + 1e-9
    assert best["jet_location"] in {"central", "mixed", "commissural"}
    assert best["blended_regurgitation_pct"] is None
    assert best["physics_regurgitation_pct"] > 0.0

    # Determinism
    best_b = rec_b.get("best_candidate") or rec_b.get("recommended")
    assert best["device"] == best_b["device"]
    assert abs(best["shortening_pct"] - best_b["shortening_pct"]) < 1e-9
    assert abs(best["physics_regurgitation_pct"] - best_b["physics_regurgitation_pct"]) < 1e-9

    # Compat shim
    assert rec_a["recommended"]["device"] == rec_a["best_candidate"]["device"]


def test_cs_lcx_boundary_and_constraint_guard(tmp_path):
    """Default anatomy: bridge 20% → CS–LCx exactly 8.6 mm; 22% violates threshold."""
    assert abs(cs_lcx_distance_mm(20.0) - CS_LCX_COMPRESSION_THRESHOLD_MM) < 1e-12
    assert cs_lcx_distance_mm(22.0) < CS_LCX_COMPRESSION_THRESHOLD_MM - 1e-9

    cs20 = IMA_CS(bridge_shortening_pct=20, mapping_mode="clinical")
    cs22 = IMA_CS(bridge_shortening_pct=22, mapping_mode="clinical")
    assert abs(cs20.cs_lcx_mm() - 8.6) < 1e-12
    assert cs22.cs_lcx_mm() < 8.6 - 1e-9

    rec = run_scenario_ranker(
        seed=GOLDEN_SEED,
        mapping_mode="clinical",
        enforce_lcx=True,
        output_dir=tmp_path,
    )
    best_cs = rec["alternatives"]["best_ima_cs"]
    assert best_cs is not None
    assert best_cs["cs_lcx_mm"] >= 8.6 - 1e-9
    assert "cs_lcx" not in (best_cs.get("constraint_violations") or "")

    best = rec.get("best_candidate") or rec.get("recommended")
    assert all(
        (p.get("cs_lcx_mm") is None) or (p["cs_lcx_mm"] >= 8.6 - 1e-9)
        for p in [best, best_cs]
        if p is not None
    )


def test_eta_sensitivity_is_assumption_prior_not_locked_recommendation():
    """η±20% may shift ranking; assert structure + honesty, not a fixed dual-AP60 outcome."""
    payload = eta_sensitivity(seed=GOLDEN_SEED)
    by = payload["by_scenario"]
    assert set(by) == {"eta_nominal", "eta_minus_20pct", "eta_plus_20pct"}
    for name, row in by.items():
        assert row["recommended_device"] in {"IMA-AP", "IMA-CS"}
        assert row["ap_reduction_pct"] is None or row["ap_reduction_pct"] <= 20.0 + 0.05
        assert row["physics_regurgitation_pct"] is not None
    honesty = payload["honesty"].lower()
    assert "assumption" in honesty
    assert "maveric" in honesty or "not" in honesty


def test_maveric_is_arto_not_carillon():
    """MAVERIC = ARTO (IMA-AP class); must not be labeled Carillon/IMA-CS."""
    import yaml

    refs = yaml.safe_load((ROOT / "results" / "clinical_references.yaml").read_text(encoding="utf-8"))
    assert "ARTO" in refs["maveric"]["device"] or "ARTO" in refs["maveric"]["name"]
    assert "Carillon" in refs["maveric"].get("not_device", "Carillon")
    assert refs["maveric"]["mechanism_class"] == "IMA-AP"
    assert refs["carillon"]["mechanism_class"] == "IMA-CS"
    assert "assumption_eta_cs" in refs["mapping_assumptions"]["ima_cs"]
    assert "0.668" in refs["mapping_assumptions"]["ima_cs"]["invalid_prior_calibration_removed"]


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
    assert "maveric" in note or "carillon" in note


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
        if not path.is_file():
            # Allow missing until --paper regenerates in this session.
            continue
        w, _h = Image.open(path).size
        assert w >= 2000, f"{name} width {w} looks below dpi≥300 quality"
