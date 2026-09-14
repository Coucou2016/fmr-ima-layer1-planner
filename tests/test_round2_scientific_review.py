"""Round-2 scientific review tests: CV, Pareto, DOI, feasibility schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_zero_occurrences_of_wrong_galili_doi():
    """Repo must not contain the incorrect Galili DOI fragment."""
    forbidden = "211" + "726"
    bad = []
    skip_parts = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
    }
    # Self + CI mention the ban without embedding the contiguous forbidden token.
    skip_names = {
        "test_round2_scientific_review.py",
        "ci.yml",
    }
    text_suffixes = {
        ".py",
        ".md",
        ".yaml",
        ".yml",
        ".bib",
        ".cff",
        ".json",
        ".csv",
        ".txt",
        ".toml",
        ".ini",
        ".rst",
    }
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path.name in skip_names:
            continue
        if path.suffix.lower() not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if forbidden in text:
            bad.append(str(path.relative_to(ROOT)))
    assert not bad, f"Found incorrect DOI fragment in: {bad}"


def test_galili_doi_and_title_unified():
    refs = yaml.safe_load(
        (ROOT / "results" / "clinical_references.yaml").read_text(encoding="utf-8")
    )
    assert refs["galili_rsos_2022"]["doi"] == "10.1098/rsos.211464"
    assert "treatments" in refs["galili_rsos_2022"]["paper_title"].lower()
    bib = (ROOT / "references.bib").read_text(encoding="utf-8")
    assert "10.1098/rsos.211464" in bib
    assert "treatments" in bib
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "10.1098/rsos.211464" in cff
    assert "treatments" in cff


def test_fold_wise_response_model_cv_excludes_held_labels(tmp_path):
    from analysis.fit_response_model import run_loo_cv, write_outputs

    payload = run_loo_cv()
    assert payload["cross_validation_role"] == "true_fold_wise_fit"
    assert payload["summary"]["ap_prediction_metric_applicable"] is False
    for fold in payload["folds"]:
        assert fold["cross_validation_role"] == "loo_fold_wise_response_model"
        assert fold["fitting_audit"]["held_id_in_fitting_targets"] is False
        assert fold["held_id"] not in fold["train_ids"]
        assert fold["held_id"] not in fold["fitted_params"]["train_ids"]
        # Held truth ROA/leak must not be appended as an extra fit row.
        assert len(fold["fitting_audit"]["train_roa_mm2"]) == len(fold["train_ids"])
        assert len(fold["fitting_audit"]["train_regurgitation_pct"]) == len(
            fold["train_ids"]
        )
    # Engineering targets vs held-out subset baseline
    met = payload["summary"]["engineering_targets_met"]
    assert met["roa_mae"] is True
    assert met["leak_mae"] is True
    assert met["ap70_roa"] is True
    assert met["ap70_leak"] is True
    ap70 = payload["summary"]["ima_ap_70"]
    assert ap70["abs_err_roa_mm2"] < 25.0
    assert ap70["abs_err_regurgitation_pct_points"] < 0.5
    out = write_outputs(payload, tmp_path / "cross_validation")
    assert out.is_file()
    assert (tmp_path / "cross_validation" / "summary.json").is_file()


def test_blend_off_diagnostic_renamed_no_validation_claim():
    from tools.loo_evaluate import run

    payload = run("both")
    assert payload["evaluation_kind"] == "anchor_free_casewise_diagnostic"
    held = payload["heldout_evaluation"]["heldout"]
    assert held
    for r in held:
        assert "validation_claim_allowed" not in r
        assert r.get("ap_prediction_metric_applicable") is False
        assert r.get("ap_role") == "literature_mapping_input"
    diag = payload["casewise_blend_off_diagnostic"]
    assert diag["fold_wise_refit"] is False
    assert "mae_ap_mm" in diag["summary"]
    assert diag["summary"]["mae_ap_mm"] is None  # not a predictive metric
    assert diag["summary"]["ap_prediction_metric_applicable"] is False


def test_pareto_families_no_na_fillers(tmp_path):
    from analysis.planner import run_scenario_ranker

    rec = run_scenario_ranker(
        seed=42,
        mapping_mode="clinical",
        output_dir=tmp_path,
        skip_uncertainty=True,
    )
    assert "pareto_global_common_objectives" in rec
    assert "pareto_ima_cs_family" in rec
    assert "pareto_ima_ap_family" in rec
    # Global objectives never invent LCx/NiTi fillers
    for row in rec["pareto_global_common_objectives"]:
        objs = row["pareto_objectives"]
        assert set(objs) == {
            "minimize_physics_regurgitation_pct",
            "maximize_ap_reduction_pct",
        }
    for row in rec["pareto_ima_ap_family"]:
        assert row["device"] == "IMA-AP"
        assert "cs_lcx_mm" not in row["pareto_objectives"]
    for row in rec["pareto_ima_cs_family"]:
        assert row["device"] == "IMA-CS"
        assert row["pareto_objectives"]["maximize_cs_lcx_mm"] is not None


def test_feasible_schema_unifies_device_candidate_denominator(tmp_path):
    from analysis.planner import run_scenario_ranker

    rec = run_scenario_ranker(
        seed=42,
        mapping_mode="clinical",
        output_dir=tmp_path,
        skip_uncertainty=True,
    )
    assert rec["n_total_points"] == 36
    assert rec["n_device_candidates"] == 35
    assert rec["n_feasible_device_candidates"] == 30
    assert abs(rec["p_feasible_device_candidates"] - round(30 / 35, 4)) < 1e-9
    assert abs(rec["p_feasible"] - rec["p_feasible_device_candidates"]) < 1e-9


def test_maveric_arto_not_carillon_still():
    refs = yaml.safe_load(
        (ROOT / "results" / "clinical_references.yaml").read_text(encoding="utf-8")
    )
    assert refs["maveric"]["mechanism_class"] == "IMA-AP"
    assert "ARTO" in refs["maveric"]["device"] or "ARTO" in refs["maveric"]["name"]
    assert refs["carillon"]["mechanism_class"] == "IMA-CS"


def test_design_point_leakage_proxy_alias():
    from analysis.evaluate import evaluate_design_point

    pt = evaluate_design_point(
        device_type="IMA-AP",
        shortening_pct=50,
        mapping_mode="clinical",
        n_sutures=1,
        blend=False,
    )
    d = pt.to_dict()
    assert "leakage_proxy_pct" in d
    assert abs(d["leakage_proxy_pct"] - d["physics_regurgitation_pct"]) < 1e-12
    assert "strain_risk_score" in d
