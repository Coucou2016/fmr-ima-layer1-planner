"""Exploratory IMA scenario ranker (Layer-1 surrogate).

Objective: minimize physics leakage-proxy regurgitation under stated assumptions.
Constraints (defaults from configs/design_space.yaml):
- AP diameter reduction ≤ clinical_max (default 20%)
- NiTi alternating strain < 0.4% (illustrative engineering screen; IMA-CS)
- CS–LCx ≥ 8.6 mm for IMA-CS (Rottländer risk-screening threshold), optional

Search is a discrete grid over the surrogate (honest: device settings are
stepped percentages, not a continuous implant dial). The reported
``best_candidate`` (JSON key ``recommended`` kept for backward compatibility)
is always a grid point under surrogate assumptions — not a clinical recommendation.

CLI:
    python -m analysis.planner
    python -m analysis.planner --clinical-max 20

Alias: ``run_scenario_ranker`` == ``run_planner``.
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

from analysis.design_sweep import run_sweep
from analysis.evaluate import DesignPoint, apply_constraints, load_design_space


def _best(points: list[DesignPoint]) -> Optional[DesignPoint]:
    if not points:
        return None
    return min(points, key=lambda p: (p.physics_regurgitation_pct, p.ap_reduction_pct))


def _payload(p: Optional[DesignPoint]) -> Optional[dict[str, Any]]:
    return None if p is None else p.to_dict()


def run_scenario_ranker(
    *,
    points: Optional[list[DesignPoint]] = None,
    seed: int = 42,
    mapping_mode: str = "clinical",
    clinical_max_ap_reduction_pct: Optional[float] = None,
    enforce_lcx: bool = True,
    output_dir: Optional[Path] = None,
    design_space: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Rank exploratory IMA scenarios under surrogate assumptions."""
    cfg = design_space or load_design_space()
    cons = cfg.get("constraints", {})
    cap = (
        float(clinical_max_ap_reduction_pct)
        if clinical_max_ap_reduction_pct is not None
        else float(cons.get("clinical_max_ap_reduction_pct", 20.0))
    )

    if points is None:
        points = run_sweep(
            mappings=[mapping_mode],
            seed=seed,
            design_space=cfg,
            apply_planner_constraints=False,
        )

    clinical = [p for p in points if p.mapping_mode == mapping_mode]
    for p in clinical:
        apply_constraints(
            p,
            cfg,
            clinical_max_ap_reduction_pct=cap,
            enforce_lcx=enforce_lcx,
        )

    def _family(name: str, n_sutures: Optional[int] = None) -> list[DesignPoint]:
        out = [p for p in clinical if p.device == name]
        if n_sutures is not None:
            out = [p for p in out if p.n_sutures == n_sutures]
        return out

    ap_single = [p for p in _family("IMA-AP", 1) if p.feasible]
    ap_dual = [p for p in _family("IMA-AP") if p.n_sutures >= 2 and p.feasible]
    cs = [p for p in _family("IMA-CS") if p.feasible]
    all_feas = [p for p in clinical if p.device is not None and p.feasible]

    best_ap = _best(ap_single)
    best_dual = _best(ap_dual)
    best_cs = _best(cs)
    best_candidate = _best(all_feas)

    notes = [
        "Layer-1 exploratory scenario ranker — not full FSI / LHHM / Abaqus.",
        "Objective is physics leakage-proxy regurgitation (no YAML anchor blend).",
        "best_candidate = best feasible grid point under stated surrogate assumptions "
        "(not a clinical recommendation).",
        f"AP reduction ceiling = {cap:.1f}% (ARTO/MAVERIC ~14–15% IMA-AP context; "
        "Carillon TITAN II ~15% IMA-CS context; default planning max 20%).",
        "IMA-CS LCx uses literature risk-screening threshold (Rottländer 8.6 mm) and "
        "illustrative baseline CS–LCx from design_space.yaml (prefer patient CT).",
        "η values are assumption priors — not clinically calibrated constants; "
        "η_CS is NOT from MAVERIC/ARTO.",
        "Reported settings are grid points (suture/bridge % steps), not interpolated implants.",
        "Physics regurg % ≠ clinical regurgitant volume.",
    ]
    if best_candidate is not None:
        notes.append(
            f"Best candidate under assumptions: {best_candidate.device} "
            f"{best_candidate.shortening_pct}% ({best_candidate.mapping_mode} mapping), "
            f"jet={best_candidate.jet_location}, "
            f"AP reduction {best_candidate.ap_reduction_pct:.1f}%, "
            f"physics regurg {best_candidate.physics_regurgitation_pct:.3f}%."
        )

    result = {
        "objective": "minimize physics_regurgitation_pct",
        "ranker": "scenario_ranker",
        "mapping_mode": mapping_mode,
        "constraints": {
            "clinical_max_ap_reduction_pct": cap,
            "niti_alternating_strain_pct_max": cons.get("niti_alternating_strain_pct_max", 0.4),
            "cs_lcx_min_mm": cons.get("cs_lcx_min_mm", 8.6) if enforce_lcx else None,
            "enforce_lcx": enforce_lcx,
            "baseline_cs_lcx_mm": cons.get("baseline_cs_lcx_mm"),
            "lcx_role": "risk_screening_threshold",
        },
        "n_evaluated": len(clinical),
        "n_feasible": len(all_feas),
        # Preferred key:
        "best_candidate": _payload(best_candidate),
        # Backward-compat shim:
        "recommended": _payload(best_candidate),
        "alternatives": {
            "best_ima_ap_single": _payload(best_ap),
            "best_ima_ap_dual": _payload(best_dual),
            "best_ima_cs": _payload(best_cs),
        },
        "notes": notes,
    }

    out = output_dir or (ROOT / "results" / "output" / "planner")
    out.mkdir(parents=True, exist_ok=True)
    (out / "recommendation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "scenario_ranking.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


# Backward-compatible alias
run_planner = run_scenario_ranker


def main(argv: Optional[list[str]] = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(
        description="FMR IMA exploratory scenario ranker (Layer-1 surrogate)"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clinical-max", type=float, default=None, dest="clinical_max")
    parser.add_argument("--no-lcx", action="store_true", help="Disable CS–LCx risk screen")
    parser.add_argument("--mapping", choices=["clinical", "galili"], default="clinical")
    args = parser.parse_args(argv)

    rec = run_scenario_ranker(
        seed=args.seed,
        mapping_mode=args.mapping,
        clinical_max_ap_reduction_pct=args.clinical_max,
        enforce_lcx=not args.no_lcx,
    )
    rec_pt = rec.get("best_candidate") or rec.get("recommended") or {}
    print("=== IMA exploratory scenario ranker (Layer-1 surrogate) ===")
    print(f"Feasible / evaluated: {rec['n_feasible']} / {rec['n_evaluated']}")
    if rec_pt:
        ns = rec_pt.get("n_sutures") or 0
        suture_note = f", n_sutures={int(ns)}" if rec_pt.get("device") == "IMA-AP" else ""
        print(
            f"Best candidate under assumptions: {rec_pt.get('device')} "
            f"shortening={rec_pt.get('shortening_pct')}%{suture_note}  "
            f"AP reduction={rec_pt.get('ap_reduction_pct'):.2f}%  "
            f"physics regurg={rec_pt.get('physics_regurgitation_pct'):.3f}%  "
            f"jet={rec_pt.get('jet_location')}"
        )
    else:
        print("No feasible design on this grid / constraint set.")
    print(f"Wrote: {ROOT / 'results' / 'output' / 'planner' / 'scenario_ranking.json'}")
    return rec


if __name__ == "__main__":
    main()
