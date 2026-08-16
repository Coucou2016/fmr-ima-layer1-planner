"""Calibration transparency and reproducibility."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from simulation.roa_surrogate import stable_case_seed, pipeline_roa_mm2
from models.heart_geometry import HeartGeometry
from models.pathology import make_papillary_mesh, apply_papillary_pathology
from simulation.run_case import run_fea_surrogate
from simulation.calibration import load_surrogate_calibration
from run_pipeline import run_all


def test_stable_case_seed_independent_of_python_hash():
    a = stable_case_seed(42, "ima_cs_22")
    b = stable_case_seed(42, "ima_cs_22")
    assert a == b
    assert stable_case_seed(42, "pathology") != stable_case_seed(42, "ima_cs_22")


def test_calibration_report_written():
    run_all(export_fea=False, seed=42)
    report = ROOT / "results" / "output" / "calibration_report.json"
    assert report.is_file()
    import json

    data = json.loads(report.read_text(encoding="utf-8"))
    assert "regurgitation_anchor_blend" in data
    assert any(c["case_id"] == "ima_ap_50" for c in data["cases"])
    ap50 = next(c for c in data["cases"] if c["case_id"] == "ima_ap_50")
    assert ap50.get("anchor_blend_weight") is not None


def test_pipeline_roa_near_ap50_minimum():
    elems = apply_papillary_pathology(make_papillary_mesh(200), posterior_fraction_passive=0.44)
    from models.devices import IMA_AP

    g = IMA_AP(shortening_pct=50).apply()
    dev = IMA_AP(shortening_pct=50)
    fea = run_fea_surrogate("ima_ap_50", g, elems, dev)
    roa = pipeline_roa_mm2(g, fea, dev, case_id="ima_ap_50", seed=42)
    assert abs(roa - 27.3) < 2.5
