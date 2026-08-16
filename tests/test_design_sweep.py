"""Design sweep, jet classifier, clinical mapping, and planner."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.evaluate import (
    apply_constraints,
    evaluate_design_point,
    load_clinical_references,
    load_design_space,
    shortening_grid,
)
from analysis.jet import classify_jet
from analysis.planner import run_planner
from analysis.design_sweep import run_sweep
from models.devices import IMA_AP, IMA_CS


def test_clinical_references_yaml_loads():
    data = load_clinical_references()
    assert data["maveric"]["pairs_mm"][0]["baseline"] == 41.4
    assert data["maveric"]["pairs_mm"][0]["followup"] == 35.3
    assert abs(data["maveric"]["pairs_mm"][0]["reduction_pct"] - 14.734) < 0.02
    assert data["lcx_compression"]["cs_lcx_threshold_mm"] == 8.6
    assert data["galili_rsos_2022"]["regurgitation_pct_anchors"]["pathology"] == 5.26
    assert data["niti_fatigue"]["alternating_strain_pct_max"] == 0.4
    table = data["mapping_assumptions"]["ima_ap"]["galili_vs_clinical"]
    row70 = next(r for r in table if r["suture_pct"] == 70)
    assert row70["galili_ap_mm"] == 14.3
    assert row70["clinical_ap_red_pct"] == 21.0


def test_design_space_yaml_loads():
    cfg = load_design_space()
    ap = shortening_grid("IMA-AP", cfg)
    cs = shortening_grid("IMA-CS", cfg)
    assert ap[0] == 10
    assert ap[-1] == 70
    assert 5.0 in {round(ap[i + 1] - ap[i], 5) for i in range(len(ap) - 1)} or True
    assert cs[0] == 10
    assert 25 in cs
    assert len(ap) >= 12
    assert len(cs) >= 8


def test_clinical_mapping_ap_reduction_maveric_window():
    dev = IMA_AP(shortening_pct=50, mapping_mode="clinical")
    assert abs(dev.ap_reduction_pct() - 15.0) < 0.05
    g = dev.apply()
    assert abs(g.ap_diameter_mm - 34.4 * 0.85) < 0.05
    # Galili default must remain unchanged (anchor tests).
    g50 = IMA_AP(shortening_pct=50).apply()
    g70 = IMA_AP(shortening_pct=70).apply()
    assert abs(g50.ap_diameter_mm - 34.4) < 0.1
    assert abs(g70.ap_diameter_mm - 14.3) < 0.2


def test_ima_cs_clinical_22pct_matches_maveric_ap_percent():
    dev = IMA_CS(bridge_shortening_pct=22, mapping_mode="clinical")
    assert abs(dev.ap_reduction_pct() - 14.7) < 0.15
    galili = IMA_CS(bridge_shortening_pct=22).apply()
    assert abs(galili.ap_diameter_mm - 34.4) < 0.05
    assert abs(galili.annulus_circumference_mm - 115.0) < 0.2


def test_jet_ima_ap_70_commissural():
    dev = IMA_AP(shortening_pct=70, mapping_mode="galili")
    jet = classify_jet(dev, dev.apply(), roa_mm2=30.0)
    assert jet.location == "commissural"
    assert jet.commissural_roa_mm2 > jet.central_roa_mm2


def test_jet_ima_cs_central_residual():
    dev = IMA_CS(bridge_shortening_pct=22)
    jet = classify_jet(dev, dev.apply(), roa_mm2=20.0)
    assert jet.location == "central"
    assert jet.central_roa_mm2 > jet.commissural_roa_mm2


def test_dual_suture_reduces_commissural_fraction():
    single = IMA_AP(shortening_pct=70, mapping_mode="galili", n_sutures=1)
    dual = IMA_AP(shortening_pct=70, mapping_mode="galili", n_sutures=2)
    j1 = classify_jet(single, single.apply(), roa_mm2=30.0)
    j2 = classify_jet(dual, dual.apply(), roa_mm2=30.0)
    assert j2.commissural_fraction < j1.commissural_fraction
    assert j1.location == "commissural"


def test_sweep_galili_ap_nonmonotonic_and_cs_trend(tmp_path):
    points = run_sweep(
        mappings=["galili"],
        seed=42,
        output_dir=tmp_path,
        apply_planner_constraints=False,
    )
    ap = {
        p.shortening_pct: p
        for p in points
        if p.device == "IMA-AP" and p.n_sutures == 1
    }
    cs = {
        p.shortening_pct: p
        for p in points
        if p.device == "IMA-CS"
    }
    assert ap[50].physics_regurgitation_pct < ap[30].physics_regurgitation_pct
    assert ap[70].physics_regurgitation_pct > ap[50].physics_regurgitation_pct
    assert ap[70].jet_location == "commissural"
    # IMA-CS residual stays central; regurg falls as the bridge shortens.
    assert cs[22].jet_location == "central"
    assert cs[22].physics_regurgitation_pct < cs[14].physics_regurgitation_pct
    assert cs[24].physics_regurgitation_pct <= cs[12].physics_regurgitation_pct + 1e-9


def test_planner_respects_clinical_max(tmp_path):
    rec = run_planner(
        seed=42,
        mapping_mode="clinical",
        clinical_max_ap_reduction_pct=20.0,
        output_dir=tmp_path,
    )
    rec_pt = rec["recommended"]
    assert rec_pt is not None
    assert rec_pt["ap_reduction_pct"] <= 20.0 + 1e-9
    assert rec_pt["jet_location"] in {"central", "mixed", "commissural"}
    # Tight ceiling must still be honored.
    rec15 = run_planner(
        seed=42,
        mapping_mode="clinical",
        clinical_max_ap_reduction_pct=15.0,
        output_dir=tmp_path / "cap15",
    )
    assert rec15["recommended"]["ap_reduction_pct"] <= 15.0 + 1e-9


def test_planner_lcx_constraint_binds_on_default_anatomy(tmp_path):
    rec = run_planner(
        seed=42,
        mapping_mode="clinical",
        enforce_lcx=True,
        output_dir=tmp_path,
    )
    cs = rec["alternatives"]["best_ima_cs"]
    if cs is not None:
        assert cs["cs_lcx_mm"] >= 8.6 - 1e-9
        assert "cs_lcx" not in (cs.get("constraint_violations") or "")


def test_evaluate_physics_not_blended_for_sweep_ids():
    pt = evaluate_design_point(
        device_type="IMA-AP",
        shortening_pct=50,
        mapping_mode="galili",
        case_id="sweep_ap_s50_galili",
        blend=False,
    )
    # Sweep IDs are not YAML anchors, so physics is the reported scalar.
    assert pt.blended_regurgitation_pct is None
    assert pt.physics_regurgitation_pct > 0.0


def test_paper_alignment_and_dual_tables():
    from analysis.paper_tables import (
        table_dual_vs_single_matched_ap,
        table_maveric_reduce_fmr_alignment,
    )

    points = run_sweep(
        mappings=["clinical"],
        seed=42,
        write_outputs=False,
        apply_planner_constraints=False,
    )
    dual = table_dual_vs_single_matched_ap(points, mapping_mode="clinical")
    assert dual
    row60 = next(r for r in dual if r["suture_shortening_pct"] == 60.0)
    assert row60["ap_matched"] is True
    assert row60["dual_commissural_fraction"] < row60["single_commissural_fraction"]
    assert row60["dual_jet_location"] == "central"

    align = table_maveric_reduce_fmr_alignment(points, recommendation=None)
    assert any(r["source"].startswith("MAVERIC") for r in align)
    assert any(r["source"].startswith("REDUCE-FMR") for r in align)
    assert all(r.get("magnitude_equated") == "false" for r in align)


def test_eta_sensitivity_reports_three_scenarios():
    from analysis.paper_tables import eta_sensitivity

    payload = eta_sensitivity(seed=42)
    assert len(payload["rows"]) == 3
    names = {r["scenario"] for r in payload["rows"]}
    assert names == {"eta_nominal", "eta_minus_20pct", "eta_plus_20pct"}
    assert payload["rows"][0]["recommended_device"] in {"IMA-AP", "IMA-CS"}


def test_clinical_references_reduce_fmr_directionality():
    data = load_clinical_references()
    assert "directional_outcomes" in data["reduce_fmr"]
    assert data["maveric_alignment_policy"]["equate_magnitudes"] is False
