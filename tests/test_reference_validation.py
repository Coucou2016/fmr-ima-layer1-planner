"""Validate pipeline outputs against results/reference_targets.json."""

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.metrics import load_reference_targets
from run_pipeline import run_all


def _case_map(ref: dict) -> dict[str, dict]:
    return {c["id"]: c for c in ref["cases"]}


@pytest.fixture(scope="module")
def metrics():
    return run_all(export_fea=False, seed=42)


@pytest.fixture(scope="module")
def reference():
    return load_reference_targets(ROOT / "results" / "reference_targets.json")


def test_anchor_regurgitation_within_tolerance(metrics, reference):
    """Anchor tolerances: pathology ±0.15% (physics-dominated); treated cases ±0.05% with documented blend."""
    by_id = {m.case_id: m for m in metrics}
    anchors = [
        ("pathology", 5.26, 0.15),
        ("ima_cs_22", 0.29, 0.05),
        ("ima_ap_50", 0.08, 0.05),
    ]
    for case_id, target, tol in anchors:
        assert case_id in by_id
        assert abs(by_id[case_id].regurgitation_pct - target) < tol


def test_ima_ap_70_worse_than_50(metrics):
    by_id = {m.case_id: m for m in metrics}
    assert by_id["ima_ap_70"].regurgitation_pct > by_id["ima_ap_50"].regurgitation_pct


def test_geometry_targets(metrics, reference):
    ref_cases = _case_map(reference)
    by_id = {m.case_id: m for m in metrics}
    cs22 = ref_cases["ima_cs_22"]
    assert abs(by_id["ima_cs_22"].annulus_circumference_mm - cs22["annulus_circumference_mm"]) < 0.2
    ap50 = ref_cases["ima_ap_50"]
    assert abs(by_id["ima_ap_50"].ap_diameter_mm - ap50["ap_diameter_mm"]) < 0.1
    ap70 = ref_cases["ima_ap_70"]
    assert abs(by_id["ima_ap_70"].ap_diameter_mm - ap70["ap_diameter_mm"]) < 0.2


def test_ima_ap_50_roa_near_minimum(metrics, reference):
    """ROA at optimum: within 2.5 mm² of paper minimum (surrogate reporting blend documented in YAML)."""
    ref_cases = _case_map(reference)
    target_roa = ref_cases["ima_ap_50"]["roa_mm2_min"]
    by_id = {m.case_id: m for m in metrics}
    assert abs(by_id["ima_ap_50"].roa_mm2 - target_roa) < 2.5


def test_ima_ap_monotonic_through_optimum(metrics):
    by_id = {m.case_id: m for m in metrics}
    assert by_id["ima_ap_50"].regurgitation_pct < by_id["ima_ap_30"].regurgitation_pct
    assert by_id["ima_ap_50"].regurgitation_pct < by_id["pathology"].regurgitation_pct


def test_intermediate_cases_monotonic_trend_cs(metrics):
    by_id = {m.case_id: m for m in metrics}
    assert by_id["ima_cs_22"].regurgitation_pct < by_id["ima_cs_14"].regurgitation_pct
    assert by_id["ima_cs_22"].regurgitation_pct < by_id["pathology"].regurgitation_pct


def test_reference_data_yaml_covers_anchors():
    data = yaml.safe_load((ROOT / "results" / "reference_data.yaml").read_text(encoding="utf-8"))
    anchors = data["validation_anchors"]["regurgitation_pct"]
    ref = load_reference_targets(ROOT / "results" / "reference_targets.json")
    for c in ref["cases"]:
        pct = c.get("regurgitation_pct")
        if pct is not None:
            assert anchors[c["id"]] == pct


def test_calibration_report_physics_and_tradeoffs():
    run_all(export_fea=False, seed=42)
    report = json.loads(
        (ROOT / "results" / "output" / "calibration_report.json").read_text(encoding="utf-8")
    )
    assert "tradeoff_notes" in report
    pathology = next(c for c in report["cases"] if c["case_id"] == "pathology")
    assert pathology.get("physics_regurgitation_pct") is not None
