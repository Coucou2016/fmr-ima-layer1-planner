#!/usr/bin/env python3
"""Leave-one-case-out / held-out scoring for Galili peak-systole anchors.

Honesty contract
----------------
- Cases listed under ``calibration_targets`` may use regurgitation/ROA anchor
  blend for *reproduction*. Scoring those same IDs with blend ON must NOT be
  reported as independent validation.
- Cases listed under ``heldout_targets`` (and each LOO fold's held-out ID) are
  scored with blend OFF (physics / surrogate prediction vs published quantities).
- With only seven discrete Galili table cases, LOO is a transparency check —
  not a claim of patient-level external validation.
- Prefer Dryad-derived ``data/processed/galili_cases.csv`` when
  ``source_tier=dryad_derived``; otherwise use published table scalars.

Usage::

    python tools/loo_evaluate.py
    python tools/loo_evaluate.py --mode heldout
    python tools/loo_evaluate.py --mode loo --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.evaluate import evaluate_design_point  # noqa: E402
from simulation.calibration import load_surrogate_calibration  # noqa: E402

PROCESSED = ROOT / "data" / "processed" / "galili_cases.csv"
REFERENCE = ROOT / "results" / "reference_data.yaml"
CAL_YAML = ROOT / "configs" / "surrogate_calibration.yaml"
OUT_DEFAULT = ROOT / "results" / "output" / "loo_evaluation.json"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_case_catalog() -> tuple[list[dict[str, Any]], str]:
    """Return peak-systole device/pathology cases + provenance note."""
    ref = _load_yaml(REFERENCE)
    ref_cases = []
    for c in ref.get("cases", []):
        ref_cases.append(
            {
                "id": c["id"],
                "device": c.get("device"),
                "shortening_pct": c.get("shortening_pct", c.get("bridge_shortening_pct")),
                "ap_diameter_mm": c.get("ap_diameter_mm"),
                "roa_mm2": c.get("roa_mm2"),
                "regurgitation_pct": c.get("regurgitation_pct"),
                "cardiac_phase": c.get("cardiac_phase", "peak_systole"),
            }
        )
    by_id = {c["id"]: c for c in ref_cases}

    if PROCESSED.is_file():
        import csv

        rows = list(csv.DictReader(PROCESSED.open(encoding="utf-8")))
        peak = [
            r
            for r in rows
            if (r.get("cardiac_phase") or "").strip() == "peak_systole"
            and r.get("case_id")
            and r["case_id"] != "geometry_undeformed"
        ]
        tiers = {r.get("source_tier") for r in peak}
        if "dryad_derived" in tiers:
            note = "processed_galili_cases:dryad_derived"
        elif "fixture_synthetic" in tiers:
            note = "processed_galili_cases:fixture_synthetic+reference_fill"
        else:
            note = "processed_galili_cases:published_table_scalars"
        for r in peak:
            cid = r["case_id"]
            filled = {
                "id": cid,
                "device": r.get("device") or (by_id.get(cid) or {}).get("device"),
                "shortening_pct": float(r["shortening_pct"])
                if r.get("shortening_pct") not in (None, "")
                else (by_id.get(cid) or {}).get("shortening_pct"),
                "ap_diameter_mm": float(r["ap_diameter_mm"])
                if r.get("ap_diameter_mm") not in (None, "")
                else (by_id.get(cid) or {}).get("ap_diameter_mm"),
                "roa_mm2": float(r["roa_mm2"])
                if r.get("roa_mm2") not in (None, "")
                else (by_id.get(cid) or {}).get("roa_mm2"),
                "regurgitation_pct": float(r["regurgitation_pct"])
                if r.get("regurgitation_pct") not in (None, "")
                else (by_id.get(cid) or {}).get("regurgitation_pct"),
                "cardiac_phase": "peak_systole",
            }
            by_id[cid] = filled
        return list(by_id.values()), note

    return ref_cases, "reference_data.yaml:published_table_scalars"


def split_ids(cal_cfg: Optional[dict[str, Any]] = None) -> dict[str, list[str]]:
    cfg = cal_cfg or load_surrogate_calibration()
    ref = _load_yaml(REFERENCE)
    cal_ids = list(cfg.get("calibration_targets", {}).get("case_ids") or [])
    hold_ids = list(cfg.get("heldout_targets", {}).get("case_ids") or [])
    if not cal_ids:
        cal_ids = list(ref.get("calibration_targets", {}).get("case_ids") or [])
    if not hold_ids:
        hold_ids = list(ref.get("heldout_targets", {}).get("case_ids") or [])
    return {"calibration_targets": cal_ids, "heldout_targets": hold_ids}


def _predict_case(case: dict[str, Any], *, blend: bool) -> dict[str, Any]:
    device = case.get("device")
    shortening = case.get("shortening_pct")
    cid = case["id"]
    if device is None:
        pt = evaluate_design_point(
            device_type=None,
            shortening_pct=None,
            mapping_mode="galili",
            case_id=cid,
            blend=blend,
        )
    else:
        pt = evaluate_design_point(
            device_type=str(device),
            shortening_pct=float(shortening) if shortening is not None else None,
            mapping_mode="galili",
            case_id=cid,
            n_sutures=1,
            blend=blend,
        )
    pred_leak = (
        pt.blended_regurgitation_pct
        if blend and pt.blended_regurgitation_pct is not None
        else pt.physics_regurgitation_pct
    )
    return {
        "case_id": cid,
        "blend": blend,
        "pred_ap_diameter_mm": pt.ap_diameter_mm,
        "pred_roa_mm2": pt.roa_mm2,
        "pred_regurgitation_pct": pred_leak,
        "pred_physics_regurgitation_pct": pt.physics_regurgitation_pct,
        "pred_blended_regurgitation_pct": pt.blended_regurgitation_pct,
        "cardiac_phase": "peak_systole",
    }


def _errors(pred: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    def err(key_pred: str, key_truth: str) -> Optional[float]:
        if truth.get(key_truth) is None or pred.get(key_pred) is None:
            return None
        return float(pred[key_pred]) - float(truth[key_truth])

    return {
        "err_ap_mm": err("pred_ap_diameter_mm", "ap_diameter_mm"),
        "err_roa_mm2": err("pred_roa_mm2", "roa_mm2"),
        "err_regurgitation_pct_points": err("pred_regurgitation_pct", "regurgitation_pct"),
        "abs_err_ap_mm": None
        if err("pred_ap_diameter_mm", "ap_diameter_mm") is None
        else abs(err("pred_ap_diameter_mm", "ap_diameter_mm")),  # type: ignore[arg-type]
        "abs_err_roa_mm2": None
        if err("pred_roa_mm2", "roa_mm2") is None
        else abs(err("pred_roa_mm2", "roa_mm2")),  # type: ignore[arg-type]
        "abs_err_regurgitation_pct_points": None
        if err("pred_regurgitation_pct", "regurgitation_pct") is None
        else abs(err("pred_regurgitation_pct", "regurgitation_pct")),  # type: ignore[arg-type]
    }


def score_cases(
    cases: list[dict[str, Any]],
    case_ids: list[str],
    *,
    blend: bool,
    role: str,
) -> list[dict[str, Any]]:
    by_id = {c["id"]: c for c in cases}
    rows = []
    for cid in case_ids:
        truth = by_id.get(cid)
        if truth is None:
            rows.append({"case_id": cid, "role": role, "error": "case_not_found"})
            continue
        pred = _predict_case(truth, blend=blend)
        row = {
            "role": role,
            "published": {
                "ap_diameter_mm": truth.get("ap_diameter_mm"),
                "roa_mm2": truth.get("roa_mm2"),
                "regurgitation_pct": truth.get("regurgitation_pct"),
                "cardiac_phase": truth.get("cardiac_phase", "peak_systole"),
            },
            **pred,
            **_errors(pred, truth),
            "validation_claim_allowed": (not blend) and role in {"heldout", "loo_heldout"},
        }
        rows.append(row)
    return rows


def run_heldout() -> dict[str, Any]:
    cases, catalog_note = load_case_catalog()
    splits = split_ids()
    held = score_cases(
        cases, splits["heldout_targets"], blend=False, role="heldout"
    )
    # Calibration IDs scored with blend ON = reproduction only.
    calib_repro = score_cases(
        cases, splits["calibration_targets"], blend=True, role="calibration_reproduction"
    )
    # Same calibration IDs with blend OFF = physics-only diagnostic (still not
    # "validation" if those IDs informed scale setting).
    calib_physics = score_cases(
        cases, splits["calibration_targets"], blend=False, role="calibration_physics_diagnostic"
    )
    return {
        "mode": "heldout",
        "catalog": catalog_note,
        "splits": splits,
        "honesty": (
            "Held-out scores use blend=OFF. Calibration IDs with blend=ON are "
            "reproduction, not independent validation. Physics-only scores on "
            "calibration IDs remain diagnostics because those IDs informed scales."
        ),
        "heldout": held,
        "calibration_reproduction": calib_repro,
        "calibration_physics_diagnostic": calib_physics,
        "summary": _summarize(held, label="heldout_blend_off"),
    }


def run_loo() -> dict[str, Any]:
    cases, catalog_note = load_case_catalog()
    splits = split_ids()
    all_ids = [c["id"] for c in cases]
    folds = []
    for held_id in all_ids:
        # Surrogate has no per-fold retrain; LOO here means: score held-out ID
        # with blend OFF, and document that remaining IDs are the notional
        # calibration pool (anchor blend still only applies to configured
        # calibration_targets that are not the held-out ID).
        row = score_cases(cases, [held_id], blend=False, role="loo_heldout")[0]
        row["notional_calibration_pool"] = [i for i in all_ids if i != held_id]
        row["anchor_blend_applied"] = False
        row["note"] = (
            "No per-fold re-estimation of SPH/ROA scales in Layer-1; LOO reports "
            "physics prediction vs published peak-systole quantities for the "
            "held-out case_id."
        )
        folds.append(row)
    return {
        "mode": "loo",
        "catalog": catalog_note,
        "splits": splits,
        "honesty": (
            "Leave-one-case-out over seven discrete Galili peak-systole cases. "
            "Not patient-level external validation. Calibration-blend cases must "
            "not be advertised as validated when blend was used."
        ),
        "folds": folds,
        "summary": _summarize(folds, label="loo_blend_off"),
    }


def _summarize(rows: list[dict[str, Any]], *, label: str) -> dict[str, Any]:
    def mean_abs(key: str) -> Optional[float]:
        vals = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        if not vals:
            return None
        return sum(vals) / len(vals)

    return {
        "label": label,
        "n": len(rows),
        "mae_ap_mm": mean_abs("abs_err_ap_mm"),
        "mae_roa_mm2": mean_abs("abs_err_roa_mm2"),
        "mae_regurgitation_pct_points": mean_abs("abs_err_regurgitation_pct_points"),
    }


def run(mode: str = "both") -> dict[str, Any]:
    out: dict[str, Any] = {
        "paper_doi": "10.1098/rsos.211726",
        "dryad_doi": "10.5061/dryad.bzkh1899d",
    }
    if mode in {"heldout", "both"}:
        out["heldout_evaluation"] = run_heldout()
    if mode in {"loo", "both"}:
        out["loo_evaluation"] = run_loo()
    return out


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Galili held-out / LOO evaluation")
    ap.add_argument("--mode", choices=["heldout", "loo", "both"], default="both")
    ap.add_argument("--write", action="store_true", help=f"Write {OUT_DEFAULT}")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = ap.parse_args(argv)
    payload = run(args.mode)
    text = json.dumps(payload, indent=2)
    if args.write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print("Wrote", args.out)
    # Compact stdout summary
    if "heldout_evaluation" in payload:
        s = payload["heldout_evaluation"]["summary"]
        print(
            f"Held-out MAE: AP={s.get('mae_ap_mm')}, "
            f"ROA={s.get('mae_roa_mm2')}, leak_pp={s.get('mae_regurgitation_pct_points')}"
        )
    if "loo_evaluation" in payload:
        s = payload["loo_evaluation"]["summary"]
        print(
            f"LOO MAE: AP={s.get('mae_ap_mm')}, "
            f"ROA={s.get('mae_roa_mm2')}, leak_pp={s.get('mae_regurgitation_pct_points')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
