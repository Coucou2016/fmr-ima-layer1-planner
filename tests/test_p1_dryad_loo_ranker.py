"""P1 tests: Dryad importer fixture, LOO splits, uncertainty-aware ranker."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_maveric_arto_not_carillon_clinical_refs():
    refs = yaml.safe_load((ROOT / "results" / "clinical_references.yaml").read_text(encoding="utf-8"))
    assert refs["maveric"]["mechanism_class"] == "IMA-AP"
    assert "ARTO" in refs["maveric"]["device"] or "ARTO" in refs["maveric"]["name"]
    assert refs["carillon"]["mechanism_class"] == "IMA-CS"


def test_cardiac_phase_fields_in_reference_and_processed(tmp_path, monkeypatch):
    ref = yaml.safe_load((ROOT / "results" / "reference_data.yaml").read_text(encoding="utf-8"))
    for c in ref["cases"]:
        assert c.get("cardiac_phase") == "peak_systole"
    assert ref["geometry_undeformed_diastole"]["cardiac_phase"] == "undeformed_diastole"

    # Fixture import → processed CSV with phase tags (tmp dirs — do not clobber Dryad).
    import tools.import_galili_dryad as imp

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(imp, "PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(imp, "PROVENANCE", tmp_path / "provenance.yaml")
    monkeypatch.setattr(imp, "RAW_README", tmp_path / "raw_README.md")
    monkeypatch.setattr(imp, "FIXTURE", tmp_path / "fixture")
    monkeypatch.setattr(imp, "RAW", tmp_path / "raw_galili")
    imp.ensure_fixture()
    csv_path = imp.process(from_fixture=True)
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert rows
    phases = {r["cardiac_phase"] for r in rows}
    assert "peak_systole" in phases
    assert "undeformed_diastole" in phases
    # Diastole must not carry leakage paired as peak-systole disease
    for r in rows:
        if r["cardiac_phase"] == "undeformed_diastole":
            assert r.get("regurgitation_pct") in ("", None)
            assert abs(float(r["ap_diameter_mm"]) - 34.4) < 1e-6
        if r["case_id"] == "ima_ap_50" and r["cardiac_phase"] == "peak_systole":
            assert abs(float(r["ap_diameter_mm"]) - 15.9) < 1e-6


def test_dryad_importer_smoke_fixture(tmp_path, monkeypatch):
    import tools.import_galili_dryad as imp

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(imp, "PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(imp, "PROVENANCE", tmp_path / "provenance.yaml")
    monkeypatch.setattr(imp, "RAW_README", tmp_path / "raw_README.md")
    monkeypatch.setattr(imp, "FIXTURE", tmp_path / "fixture")
    monkeypatch.setattr(imp, "RAW", tmp_path / "raw_galili")
    out = imp.process(from_fixture=True)
    assert out.is_file()
    prov = yaml.safe_load((tmp_path / "provenance.yaml").read_text(encoding="utf-8"))
    assert prov["galili_rsos_2022"]["dryad_doi"] == "10.5061/dryad.bzkh1899d"
    assert prov["galili_rsos_2022"]["status"] in {
        "fixture_synthetic",
        "dryad_derived",
        "published_table_scalars",
    }


def test_loo_heldout_split_and_no_validation_claim_on_blend():
    from tools.loo_evaluate import run, split_ids

    splits = split_ids()
    assert "pathology" in splits["calibration_targets"]
    assert "ima_ap_50" in splits["calibration_targets"]
    assert "ima_ap_70" in splits["heldout_targets"]
    assert set(splits["calibration_targets"]).isdisjoint(splits["heldout_targets"])

    payload = run("both")
    held = payload["heldout_evaluation"]["heldout"]
    assert held
    assert all(r.get("blend") is False for r in held if "blend" in r)
    assert all(r.get("validation_claim_allowed") is True for r in held if "validation_claim_allowed" in r)

    calib = payload["heldout_evaluation"]["calibration_reproduction"]
    assert calib
    assert all(r.get("blend") is True for r in calib if "blend" in r)
    assert all(r.get("validation_claim_allowed") is False for r in calib if "validation_claim_allowed" in r)

    loo = payload["loo_evaluation"]
    assert loo["summary"]["n"] >= 4
    assert "mae_ap_mm" in loo["summary"]


def test_scenario_ranker_uncertainty_and_pareto(tmp_path):
    from analysis.planner import run_scenario_ranker

    rec = run_scenario_ranker(
        seed=42,
        mapping_mode="clinical",
        output_dir=tmp_path,
        n_eta_samples=5,
    )
    assert "p_feasible" in rec
    assert 0.0 < rec["p_feasible"] <= 1.0
    unc = rec["uncertainty"]
    assert unc.get("skipped") is not True
    assert "ranking_stability_top1_fraction" in unc
    assert "best_candidate_win_counts" in unc
    assert "assumption" in (unc.get("honesty") or "").lower()
    assert isinstance(rec.get("pareto_frontier"), list)
    assert rec["hypotheses"]["dual_suture_role"] == "exploratory_hypothesis_parameter"
    assert rec["constraints"]["cs_lcx_cinch_role"] == "labeled_assumption_slope"
    assert rec["framing"] == "exploratory_screening_best_under_assumptions"
    # Compat shim present but framing is not clinical recommendation
    assert rec.get("recommended") is not None
    notes = " ".join(rec.get("notes") or []).lower()
    assert "not a clinical recommendation" in notes or "exploratory" in notes


def test_patient_cs_lcx_overrides_baseline(tmp_path):
    from analysis.planner import run_scenario_ranker

    rec = run_scenario_ranker(
        seed=42,
        mapping_mode="clinical",
        output_dir=tmp_path,
        patient_cs_lcx_mm=12.0,
        skip_uncertainty=True,
    )
    assert rec["constraints"]["baseline_cs_lcx_source"] == "patient_measured"
    best_cs = rec["alternatives"]["best_ima_cs"]
    # With higher baseline, more CS shortenings can clear 8.6 mm
    assert best_cs is not None
    assert best_cs["cs_lcx_mm"] >= 8.6 - 1e-9
