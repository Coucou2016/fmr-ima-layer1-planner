"""Load surrogate calibration anchors (separate from derived case physics)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_surrogate_calibration(path: Path | None = None) -> dict[str, Any]:
    p = path or ROOT / "configs" / "surrogate_calibration.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _tradeoff_notes(calibration: dict[str, Any]) -> list[str]:
    blend = calibration.get("regurgitation_anchor_blend", {})
    sph = calibration.get("sph", {})
    notes = [
        "Regurgitation at anchor cases uses (1-w)*physics + w*anchor; intermediate cases are physics-only.",
        "Coaptation gap exponent is elevated so small post-device gaps strongly reduce leak index (mechanism).",
        f"Current anchor blend weights: pathology={blend.get('pathology')}, "
        f"ima_cs_22={blend.get('ima_cs_22')}, ima_ap_50={blend.get('ima_ap_50')}.",
        "ROA at IMA-AP 50% uses high model weight and roa_anchor_blend_weight toward paper minimum.",
        "ROA and regurgitation % are coupled but not identical scalars in this surrogate.",
    ]
    if sph.get("coaptation_gap_exponent", 0) > 2.0:
        notes.append(
            "coaptation_gap_exponent > 2 reflects steep sensitivity of effective leak to leaflet coaptation."
        )
    return notes


def write_calibration_report(
    metrics: list,
    reference: dict[str, Any],
    calibration: dict[str, Any],
    out_path: Path,
    *,
    physics_by_case: dict[str, float] | None = None,
) -> None:
    """Write anchor residuals, blend weights, and physics-vs-anchor tradeoffs."""
    import json

    ref_by_id = {c["id"]: c for c in reference.get("cases", [])}
    anchors_pct = calibration.get("regurgitation_pct_anchors", {})
    blend = calibration.get("regurgitation_anchor_blend", {})
    roa_anchors = calibration.get("roa_mm2_anchors", {})

    rows = []
    for m in metrics:
        ref_case = ref_by_id.get(m.case_id, {})
        physics_pct = None
        if physics_by_case and m.case_id in physics_by_case:
            physics_pct = physics_by_case[m.case_id] * 100.0
        row = {
            "case_id": m.case_id,
            "simulated_regurgitation_pct": m.regurgitation_pct,
            "physics_regurgitation_pct": physics_pct,
            "reference_regurgitation_pct": m.reference_regurgitation_pct,
            "regurgitation_residual_pct": m.error_vs_reference_pct(),
            "anchor_blend_weight": blend.get(m.case_id),
            "published_regurgitation_anchor": anchors_pct.get(m.case_id),
            "simulated_roa_mm2": m.roa_mm2,
            "reference_roa_mm2_min": ref_case.get("roa_mm2_min"),
        }
        if m.case_id == "ima_ap_50" and "ima_ap_50_minimum" in roa_anchors:
            row["roa_anchor_mm2"] = roa_anchors["ima_ap_50_minimum"]
            row["roa_residual_vs_anchor_mm2"] = abs(
                m.roa_mm2 - float(roa_anchors["ima_ap_50_minimum"])
            )
        rows.append(row)

    payload = {
        "calibration_file": str(ROOT / "configs" / "surrogate_calibration.yaml"),
        "regurgitation_anchor_blend": blend,
        "regurgitation_pct_anchors": anchors_pct,
        "roa_mm2_anchors": roa_anchors,
        "tradeoff_notes": _tradeoff_notes(calibration),
        "cases": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def physics_regurgitation_by_case(
    metrics: list,
    *,
    coaptation_gaps: dict[str, float],
    geometries: dict[str, Any],
    commissural: dict[str, bool],
    calibration: dict[str, Any],
) -> dict[str, float]:
    """Pre-blend regurgitation fraction per case (for audit)."""
    from sph.hemodynamics import regurgitation_fraction_from_physics

    out: dict[str, float] = {}
    for m in metrics:
        g = geometries[m.case_id]
        gap = coaptation_gaps[m.case_id]
        out[m.case_id] = regurgitation_fraction_from_physics(
            g,
            m.roa_mm2,
            gap,
            commissural_leak=commissural.get(m.case_id, False),
            calibration=calibration,
        )
    return out
