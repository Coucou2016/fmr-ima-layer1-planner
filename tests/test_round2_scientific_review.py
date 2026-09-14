"""Round-2 scientific review tests: CV, Pareto, DOI, feasibility schema."""

from __future__ import annotations

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
    assert "contact_score" in d
    assert d["contact_score"] is not None
    assert d.get("contact_fraction") is not None
    assert d.get("response_path") in {
        "fitted_response",
        "rule_based_proxy",
        "hybrid_ap_extreme",
    }


def test_roa_pipeline_weights_scientific_default():
    cal = yaml.safe_load(
        (ROOT / "configs" / "surrogate_calibration.yaml").read_text(encoding="utf-8")
    )
    for key in ("default", "ima_ap_50", "pathology"):
        block = cal["roa_pipeline"][key]
        assert abs(float(block["model_weight"]) - 1.0) < 1e-12
        assert abs(float(block["cluster_weight"]) - 0.0) < 1e-12


def test_sph_scale_is_pathology_fraction_identity():
    from simulation.calibration import load_surrogate_calibration
    from sph.hemodynamics import _sph_scale

    cfg = load_surrogate_calibration()
    assert abs(_sph_scale(cfg) - float(cfg["sph"]["pathology_regurgitation_pct"]) / 100.0) < 1e-12


def test_fitted_response_default_and_contact_fraction_feature():
    from analysis.evaluate import evaluate_design_point, load_design_space
    from models.response_runtime import estimate_contact_fraction

    cfg = load_design_space()
    assert cfg.get("response_path") == "fitted_response"
    cf = estimate_contact_fraction("IMA-AP", 70.0)
    assert abs(cf - 0.225696) < 1e-5
    pt = evaluate_design_point(
        device_type="IMA-AP",
        shortening_pct=70,
        mapping_mode="galili",
        n_sutures=1,
        blend=False,
        response_path="fitted_response",
        design_space=cfg,
    )
    assert pt.response_path == "fitted_response"
    assert pt.contact_fraction is not None
    assert pt.contact_fraction > 0.1


def test_rule_based_proxy_path_still_available():
    import copy

    from analysis.evaluate import evaluate_design_point, load_design_space

    cfg = copy.deepcopy(load_design_space())
    cfg["response_path"] = "rule_based_proxy"
    pt = evaluate_design_point(
        device_type="IMA-AP",
        shortening_pct=70,
        mapping_mode="galili",
        n_sutures=1,
        blend=False,
        design_space=cfg,
    )
    assert pt.response_path == "rule_based_proxy"
    assert pt.rule_based_leakage_proxy_pct is not None
    # Dampened AP70: historical catastrophe ~2.46% → post-dampen <1.5%
    # (Galili published 0.13%; residual overestimate remains — fitted_response
    # is the paper ranking path for AP-class extremes).
    assert pt.physics_regurgitation_pct < 1.5
    assert pt.physics_regurgitation_pct > 0.05


def test_exploratory_planning_range_config_keys():
    ds = yaml.safe_load((ROOT / "configs" / "design_space.yaml").read_text(encoding="utf-8"))
    cons = ds["constraints"]
    assert "exploratory_planning_range_ap_reduction_pct" in cons
    assert cons["exploratory_planning_range_ap_reduction_pct"] == [14.0, 20.0]


def test_lhs_uncertainty_emits_p_top1(tmp_path):
    import copy

    from analysis.evaluate import load_design_space
    from analysis.planner import run_scenario_ranker

    cfg = copy.deepcopy(load_design_space())
    cfg["uncertainty"]["n_samples"] = 12
    rec = run_scenario_ranker(
        seed=42,
        mapping_mode="clinical",
        output_dir=tmp_path,
        design_space=cfg,
        n_eta_samples=12,
    )
    unc = rec["uncertainty"]
    assert unc.get("sampling_mode") == "latin_hypercube_multiparam"
    assert unc["n_samples"] == 12
    assert "p_top1" in unc
    assert "P(top-1)" in unc
    assert "first_order_sensitivity_ranks" in unc
    assert rec["response_path"] == "fitted_response"
