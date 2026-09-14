#!/usr/bin/env python3
"""True fold-wise response-model fit + leave-one-case-out cross-validation.

Each fold:
  - held_id out of fitting targets
  - fit f_ROA / f_leak on remaining cases only
  - MUST NOT read held ROA/leakage into fit arrays
  - AP may be prescribed geometry input
  - write fold-specific fitted params + prediction errors

Outputs under ``results/output/cross_validation/``.

This is distinct from ``tools/loo_evaluate.py`` (anchor-free casewise diagnostic
on the fixed rule-based surrogate).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.response_model import (  # noqa: E402
    fit_response_models,
    predict_case,
)
from tools.loo_evaluate import load_case_catalog  # noqa: E402

OUT_DIR = ROOT / "results" / "output" / "cross_validation"


def _strip_fitting_targets(case: dict[str, Any]) -> dict[str, Any]:
    """Geometry / contact features only — no ROA or leakage labels."""
    return {
        "id": case["id"],
        "device": case.get("device"),
        "shortening_pct": case.get("shortening_pct"),
        "ap_diameter_mm": case.get("ap_diameter_mm"),
        "annulus_circumference_mm": case.get("annulus_circumference_mm"),
        "contact_fraction": case.get("contact_fraction"),
        "cardiac_phase": case.get("cardiac_phase", "peak_systole"),
    }


def _errors(pred: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    def abs_err(pkey: str, tkey: str) -> Optional[float]:
        if pred.get(pkey) is None or truth.get(tkey) is None:
            return None
        return abs(float(pred[pkey]) - float(truth[tkey]))

    return {
        "err_roa_mm2": (
            None
            if pred.get("pred_roa_mm2") is None or truth.get("roa_mm2") is None
            else float(pred["pred_roa_mm2"]) - float(truth["roa_mm2"])
        ),
        "err_regurgitation_pct_points": (
            None
            if pred.get("pred_regurgitation_pct") is None
            or truth.get("regurgitation_pct") is None
            else float(pred["pred_regurgitation_pct"])
            - float(truth["regurgitation_pct"])
        ),
        "abs_err_roa_mm2": abs_err("pred_roa_mm2", "roa_mm2"),
        "abs_err_regurgitation_pct_points": abs_err(
            "pred_regurgitation_pct", "regurgitation_pct"
        ),
        # AP MAE is table lookup — not a predictive accuracy claim.
        "ap_role": "literature_mapping_input",
        "ap_prediction_metric_applicable": False,
        "abs_err_ap_mm_passthrough": abs_err("pred_ap_diameter_mm", "ap_diameter_mm"),
    }


HELDOUT_COMPARE_IDS = ("ima_cs_14", "ima_cs_18", "ima_ap_30", "ima_ap_70")


def run_loo_cv(*, ridge_roa: float = 0.05, ridge_leak: float = 0.05) -> dict[str, Any]:
    cases, catalog_note = load_case_catalog()
    # Peak-systole device+pathology only (skip undeformed diastole if present).
    cases = [
        c
        for c in cases
        if c.get("cardiac_phase", "peak_systole") == "peak_systole"
        and c.get("roa_mm2") is not None
        and c.get("regurgitation_pct") is not None
    ]
    all_ids = [c["id"] for c in cases]
    by_id = {c["id"]: c for c in cases}
    folds: list[dict[str, Any]] = []

    for held_id in all_ids:
        train_ids = [i for i in all_ids if i != held_id]
        train_cases = [by_id[i] for i in train_ids]
        fitting_targets = {
            "roa_mm2": [float(c["roa_mm2"]) for c in train_cases],
            "regurgitation_pct": [float(c["regurgitation_pct"]) for c in train_cases],
            "case_ids": list(train_ids),
        }
        assert held_id not in fitting_targets["case_ids"]
        held_truth = by_id[held_id]
        held_roa = float(held_truth["roa_mm2"])
        held_leak = float(held_truth["regurgitation_pct"])
        # Held truth labels must not appear as an extra row in fit arrays.
        assert len(fitting_targets["roa_mm2"]) == len(train_ids)
        assert len(fitting_targets["regurgitation_pct"]) == len(train_ids)

        params = fit_response_models(
            train_cases, ridge_roa=ridge_roa, ridge_leak=ridge_leak
        )
        feature_case = _strip_fitting_targets(held_truth)
        pred = predict_case(params, feature_case)
        row = {
            "held_id": held_id,
            "cross_validation_role": "loo_fold_wise_response_model",
            "train_ids": train_ids,
            "fitted_params": params.to_dict(),
            "fitting_audit": {
                "held_id_in_fitting_targets": False,
                "n_train": len(train_ids),
                "held_roa_mm2": held_roa,
                "held_regurgitation_pct": held_leak,
                "train_roa_mm2": fitting_targets["roa_mm2"],
                "train_regurgitation_pct": fitting_targets["regurgitation_pct"],
            },
            "published": {
                "ap_diameter_mm": held_truth.get("ap_diameter_mm"),
                "roa_mm2": held_truth.get("roa_mm2"),
                "regurgitation_pct": held_truth.get("regurgitation_pct"),
                "contact_fraction": held_truth.get("contact_fraction"),
                "cardiac_phase": held_truth.get("cardiac_phase", "peak_systole"),
            },
            **pred,
            **_errors(pred, held_truth),
        }
        folds.append(row)

    def mae(rows: list[dict[str, Any]], key: str) -> Optional[float]:
        vals = [f[key] for f in rows if isinstance(f.get(key), (int, float))]
        if not vals:
            return None
        return sum(vals) / len(vals)

    held_rows = [f for f in folds if f["held_id"] in HELDOUT_COMPARE_IDS]
    ap70 = next((f for f in folds if f["held_id"] == "ima_ap_70"), None)
    summary = {
        "label": "fold_wise_response_model_loo",
        "n": len(folds),
        "mae_roa_mm2": mae(folds, "abs_err_roa_mm2"),
        "mae_regurgitation_pct_points": mae(folds, "abs_err_regurgitation_pct_points"),
        "heldout_subset_ids": list(HELDOUT_COMPARE_IDS),
        "heldout_subset_mae_roa_mm2": mae(held_rows, "abs_err_roa_mm2"),
        "heldout_subset_mae_regurgitation_pct_points": mae(
            held_rows, "abs_err_regurgitation_pct_points"
        ),
        "ap_prediction_metric_applicable": False,
        "mae_ap_mm_note": (
            "AP is literature_mapping_input (table lookup / prescribed geometry); "
            "do not report AP MAE as predictive accuracy."
        ),
        "engineering_targets": {
            "roa_heldout_mae_mm2": 25.0,
            "leak_mae_pp": 0.5,
            "ap70_roa_abs_err_mm2": 25.0,
            "ap70_leak_abs_err_pp": 0.5,
            "note": "Internal engineering targets — NOT medical validation thresholds.",
            "compared_against": "heldout_subset_mae (same IDs as rule-based blend-off baseline)",
        },
        "baseline_rule_based_blend_off": {
            "heldout_mae_roa_mm2": 50.18,
            "heldout_mae_leak_pp": 1.445,
            "ap70_abs_err_roa_mm2": 94.17,
            "ap70_abs_err_leak_pp": 5.455,
        },
        "ima_ap_70": None
        if ap70 is None
        else {
            "abs_err_roa_mm2": ap70.get("abs_err_roa_mm2"),
            "abs_err_regurgitation_pct_points": ap70.get(
                "abs_err_regurgitation_pct_points"
            ),
            "pred_roa_mm2": ap70.get("pred_roa_mm2"),
            "published_roa_mm2": (ap70.get("published") or {}).get("roa_mm2"),
            "pred_regurgitation_pct": ap70.get("pred_regurgitation_pct"),
            "published_regurgitation_pct": (ap70.get("published") or {}).get(
                "regurgitation_pct"
            ),
        },
    }
    targets = summary["engineering_targets"]
    h_roa = summary["heldout_subset_mae_roa_mm2"]
    h_leak = summary["heldout_subset_mae_regurgitation_pct_points"]
    met = {
        "roa_mae": h_roa is not None and h_roa < targets["roa_heldout_mae_mm2"],
        "leak_mae": h_leak is not None and h_leak < targets["leak_mae_pp"],
        "ap70_roa": (
            ap70 is not None
            and ap70.get("abs_err_roa_mm2") is not None
            and ap70["abs_err_roa_mm2"] < targets["ap70_roa_abs_err_mm2"]
        ),
        "ap70_leak": (
            ap70 is not None
            and ap70.get("abs_err_regurgitation_pct_points") is not None
            and ap70["abs_err_regurgitation_pct_points"]
            < targets["ap70_leak_abs_err_pp"]
        ),
    }
    summary["engineering_targets_met"] = met
    if not all(met.values()):
        framing = (
            "rule-based exploratory emulator + fitted response diagnostic; "
            "do not claim prediction-valid surrogate"
        )
    else:
        framing = (
            "fold-wise response model met internal engineering targets on the "
            "held-out Galili subset — still not patient-level external validation"
        )
    summary["scientific_framing"] = framing

    return {
        "mode": "fold_wise_response_model_loo",
        "cross_validation_role": "true_fold_wise_fit",
        "paper_doi": "10.1098/rsos.211464",
        "dryad_doi": "10.5061/dryad.bzkh1899d",
        "catalog": catalog_note,
        "honesty": (
            "True leave-one-case-out: each fold refits f_ROA(ΔAP, device family, "
            "annular reduction, contact_fraction) and f_leak(ROA, coaptation proxy, "
            "contact, device mechanism) on the other six Galili peak-systole cases. "
            "Held-out ROA/leakage never enter fit arrays. AP is prescribed geometry "
            "input. Fixed kappa_overshort prior encodes Galili non-monotonic ROA "
            "rebound beyond ~AP50. Not patient-level external validation."
        ),
        "folds": folds,
        "summary": summary,
    }


def write_outputs(payload: dict[str, Any], out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    main = out_dir / "loo_response_model.json"
    main.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Per-fold param dumps for auditability.
    folds_dir = out_dir / "folds"
    folds_dir.mkdir(exist_ok=True)
    for fold in payload.get("folds") or []:
        hid = fold["held_id"]
        (folds_dir / f"{hid}.json").write_text(
            json.dumps(fold, indent=2), encoding="utf-8"
        )
    (out_dir / "summary.json").write_text(
        json.dumps(payload.get("summary"), indent=2), encoding="utf-8"
    )
    return main


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Fold-wise response-model LOO cross-validation"
    )
    ap.add_argument("--write", action="store_true", help=f"Write under {OUT_DIR}")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--ridge-roa", type=float, default=0.05)
    ap.add_argument("--ridge-leak", type=float, default=0.05)
    args = ap.parse_args(argv)
    payload = run_loo_cv(ridge_roa=args.ridge_roa, ridge_leak=args.ridge_leak)
    if args.write:
        path = write_outputs(payload, args.out_dir)
        print("Wrote", path)
    s = payload["summary"]
    print(
        f"Fold-wise CV held-out subset MAE: ROA={s.get('heldout_subset_mae_roa_mm2')}, "
        f"leak_pp={s.get('heldout_subset_mae_regurgitation_pct_points')}"
    )
    print(
        f"Fold-wise CV full-LOO MAE: ROA={s.get('mae_roa_mm2')}, "
        f"leak_pp={s.get('mae_regurgitation_pct_points')}"
    )
    ap70 = s.get("ima_ap_70") or {}
    print(
        f"AP70: pred_ROA={ap70.get('pred_roa_mm2')} "
        f"(pub {ap70.get('published_roa_mm2')}) "
        f"abs_err={ap70.get('abs_err_roa_mm2')}; "
        f"pred_leak={ap70.get('pred_regurgitation_pct')} "
        f"(pub {ap70.get('published_regurgitation_pct')}) "
        f"abs_err={ap70.get('abs_err_regurgitation_pct_points')}"
    )
    print("Targets met:", s.get("engineering_targets_met"))
    print("Framing:", s.get("scientific_framing"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
