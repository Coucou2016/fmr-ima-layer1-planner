"""Exploratory IMA scenario ranker with assumption-prior uncertainty (Layer-1).

Objective: minimize physics leakage-proxy regurgitation under stated assumptions.

Constraints (defaults from configs/design_space.yaml):
- AP diameter reduction ≤ clinical_max (default 20%)
- NiTi alternating strain < 0.4% (illustrative engineering screen; IMA-CS)
- CS–LCx ≥ 8.6 mm for IMA-CS (Rottländer risk-screening threshold)

Uncertainty (exploratory, not FEA UQ):
- Sample η_ap / η_cs from assumption-prior distributions (or discrete ±%)
- Report P(feasible), ranking stability, and a simple Pareto frontier over
  leakage vs AP reduction vs LCx risk vs strain screen

Search is a discrete grid over the surrogate. The reported ``best_candidate``
(JSON key ``recommended`` kept for backward compatibility) is always a grid
point under surrogate assumptions — not a clinical recommendation.

CLI:
    python -m analysis.planner
    python -m analysis.planner --clinical-max 20 --patient-cs-lcx-mm 10.5
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np

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


def _point_key(p: DesignPoint | dict[str, Any]) -> str:
    if isinstance(p, DesignPoint):
        return f"{p.device}|{p.shortening_pct}|{p.n_sutures}|{p.mapping_mode}"
    return (
        f"{p.get('device')}|{p.get('shortening_pct')}|{p.get('n_sutures')}|"
        f"{p.get('mapping_mode')}"
    )


def _pareto_frontier(points: list[DesignPoint]) -> list[dict[str, Any]]:
    """Non-dominated set minimizing leakage & strain risk; maximizing AP↓ & LCx.

    Objectives (exploratory screening language — not clinical utility):
      1. minimize physics_regurgitation_pct
      2. maximize ap_reduction_pct (benefit proxy under AP ceiling)
      3. maximize cs_lcx_mm when present (else neutral)
      4. minimize niti_alternating_strain_pct when present (else neutral)
    """
    feas = [p for p in points if p.feasible and p.device is not None]
    if not feas:
        return []

    def dominates(a: DesignPoint, b: DesignPoint) -> bool:
        # a better-or-equal on all, strict on at least one
        a_leak, b_leak = a.physics_regurgitation_pct, b.physics_regurgitation_pct
        a_ap, b_ap = a.ap_reduction_pct, b.ap_reduction_pct
        a_lcx = a.cs_lcx_mm if a.cs_lcx_mm is not None else 1e9
        b_lcx = b.cs_lcx_mm if b.cs_lcx_mm is not None else 1e9
        a_st = a.niti_alternating_strain_pct if a.niti_alternating_strain_pct is not None else 0.0
        b_st = b.niti_alternating_strain_pct if b.niti_alternating_strain_pct is not None else 0.0
        better_eq = (
            a_leak <= b_leak + 1e-12
            and a_ap >= b_ap - 1e-12
            and a_lcx >= b_lcx - 1e-12
            and a_st <= b_st + 1e-12
        )
        strict = (
            a_leak < b_leak - 1e-12
            or a_ap > b_ap + 1e-12
            or a_lcx > b_lcx + 1e-12
            or a_st < b_st - 1e-12
        )
        return better_eq and strict

    frontier = []
    for p in feas:
        if any(dominates(q, p) for q in feas if q is not p):
            continue
        frontier.append(
            {
                **p.to_dict(),
                "pareto_objectives": {
                    "minimize_physics_regurgitation_pct": p.physics_regurgitation_pct,
                    "maximize_ap_reduction_pct": p.ap_reduction_pct,
                    "maximize_cs_lcx_mm_or_neutral": p.cs_lcx_mm,
                    "minimize_niti_alternating_strain_pct_or_neutral": p.niti_alternating_strain_pct,
                },
            }
        )
    frontier.sort(key=lambda d: d["physics_regurgitation_pct"])
    return frontier


def _apply_patient_cs_lcx(
    points: list[DesignPoint],
    *,
    patient_cs_lcx_mm: Optional[float],
    design_space: dict[str, Any],
) -> None:
    """Prefer optional patient-measured baseline CS–LCx; slope remains labeled assumption."""
    if patient_cs_lcx_mm is None:
        return
    cons = design_space.get("constraints", {})
    slope = float(cons.get("cs_lcx_cinch_mm_per_pct", 0.12))
    for p in points:
        if p.device != "IMA-CS" or p.shortening_pct is None:
            continue
        # Assumption slope applied to patient baseline (labeled in notes).
        p.cs_lcx_mm = float(patient_cs_lcx_mm) - slope * float(p.shortening_pct)


def run_uncertainty_analysis(
    *,
    seed: int,
    mapping_mode: str,
    design_space: dict[str, Any],
    clinical_max_ap_reduction_pct: float,
    enforce_lcx: bool,
    patient_cs_lcx_mm: Optional[float],
    n_eta_samples: int = 9,
    eta_relative_span: float = 0.20,
) -> dict[str, Any]:
    """Sweep η within ±span and summarize feasibility / ranking stability.

    η are assumption priors — not clinically calibrated constants.
    """
    rng = np.random.default_rng(seed)
    cmap = design_space.get("clinical_mapping", {})
    eta_ap0 = float(cmap.get("ap_transfer_eta_ima_ap", 0.30))
    eta_cs0 = float(cmap.get("ap_transfer_eta_ima_cs", 0.55))

    # Deterministic grid on relative factors plus a few RNG samples for stability.
    grid = np.linspace(1.0 - eta_relative_span, 1.0 + eta_relative_span, max(3, n_eta_samples // 2))
    extras = rng.uniform(1.0 - eta_relative_span, 1.0 + eta_relative_span, size=max(0, n_eta_samples - len(grid)))
    factors = np.unique(np.round(np.concatenate([grid, extras]), 5))

    wins: dict[str, int] = {}
    feasible_counts: list[int] = []
    evaluated = 0
    best_keys: list[str] = []

    for fac in factors:
        cfg = copy.deepcopy(design_space)
        cfg["clinical_mapping"]["ap_transfer_eta_ima_ap"] = eta_ap0 * float(fac)
        cfg["clinical_mapping"]["ap_transfer_eta_ima_cs"] = eta_cs0 * float(fac)
        points = run_sweep(
            mappings=[mapping_mode],
            seed=seed,
            design_space=cfg,
            apply_planner_constraints=False,
            write_outputs=False,
        )
        _apply_patient_cs_lcx(points, patient_cs_lcx_mm=patient_cs_lcx_mm, design_space=cfg)
        clinical = [p for p in points if p.mapping_mode == mapping_mode]
        for p in clinical:
            apply_constraints(
                p,
                cfg,
                clinical_max_ap_reduction_pct=clinical_max_ap_reduction_pct,
                enforce_lcx=enforce_lcx,
            )
        feas = [p for p in clinical if p.device is not None and p.feasible]
        evaluated = len(clinical)
        feasible_counts.append(len(feas))
        best = _best(feas)
        if best is not None:
            key = _point_key(best)
            wins[key] = wins.get(key, 0) + 1
            best_keys.append(key)

    n = max(len(factors), 1)
    p_feasible_mean = float(np.mean([c / max(evaluated, 1) for c in feasible_counts])) if feasible_counts else 0.0
    top = sorted(wins.items(), key=lambda kv: (-kv[1], kv[0]))
    stability = {
        "n_eta_factors": int(len(factors)),
        "eta_relative_span": eta_relative_span,
        "eta_ap_nominal": eta_ap0,
        "eta_cs_nominal": eta_cs0,
        "eta_role": "assumption_prior_distribution",
        "mean_fraction_feasible": round(p_feasible_mean, 4),
        "p_feasible_at_nominal_grid": None,  # filled by caller
        "best_candidate_win_counts": [
            {"design_key": k, "n_wins": v, "win_fraction": round(v / n, 4)} for k, v in top
        ],
        "ranking_stability_top1_fraction": round(top[0][1] / n, 4) if top else 0.0,
        "honesty": (
            "η±span sampling is assumption-prior sensitivity for exploratory ranking; "
            "not imaging–FEA identification, Abaqus/LHHM UQ, or clinical calibration. "
            "η_CS is not from MAVERIC/ARTO."
        ),
    }
    return stability


def run_scenario_ranker(
    *,
    points: Optional[list[DesignPoint]] = None,
    seed: int = 42,
    mapping_mode: str = "clinical",
    clinical_max_ap_reduction_pct: Optional[float] = None,
    enforce_lcx: bool = True,
    output_dir: Optional[Path] = None,
    design_space: Optional[dict[str, Any]] = None,
    patient_cs_lcx_mm: Optional[float] = None,
    n_eta_samples: int = 9,
    skip_uncertainty: bool = False,
) -> dict[str, Any]:
    """Rank exploratory IMA scenarios under surrogate assumptions + η uncertainty."""
    cfg = design_space or load_design_space()
    cons = cfg.get("constraints", {})
    cap = (
        float(clinical_max_ap_reduction_pct)
        if clinical_max_ap_reduction_pct is not None
        else float(cons.get("clinical_max_ap_reduction_pct", 20.0))
    )
    dual_hyp = cfg.get("dual_suture", {})
    dual_factor = float(dual_hyp.get("commissural_factor", 0.5))

    if points is None:
        points = run_sweep(
            mappings=[mapping_mode],
            seed=seed,
            design_space=cfg,
            apply_planner_constraints=False,
        )

    # Copy list so patient LCx override does not leak across callers unexpectedly.
    points = list(points)
    _apply_patient_cs_lcx(points, patient_cs_lcx_mm=patient_cs_lcx_mm, design_space=cfg)

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
    device_eval = [p for p in clinical if p.device is not None]

    best_ap = _best(ap_single)
    best_dual = _best(ap_dual)
    best_cs = _best(cs)
    best_candidate = _best(all_feas)
    pareto = _pareto_frontier(clinical)

    p_feasible = (len(all_feas) / len(device_eval)) if device_eval else 0.0

    if skip_uncertainty:
        uncertainty: dict[str, Any] = {
            "skipped": True,
            "mean_fraction_feasible": None,
            "ranking_stability_top1_fraction": None,
            "best_candidate_win_counts": [],
            "honesty": "Uncertainty sweep skipped for this call.",
        }
    else:
        uncertainty = run_uncertainty_analysis(
            seed=seed,
            mapping_mode=mapping_mode,
            design_space=cfg,
            clinical_max_ap_reduction_pct=cap,
            enforce_lcx=enforce_lcx,
            patient_cs_lcx_mm=patient_cs_lcx_mm,
            n_eta_samples=n_eta_samples,
        )
    uncertainty["p_feasible_at_nominal_grid"] = round(p_feasible, 4)

    notes = [
        "Layer-1 exploratory scenario ranker — phenomenological mechanics + literature-calibrated leakage proxy.",
        "Not full FSI / LHHM / Abaqus; not a clinical recommendation engine.",
        "Objective is physics leakage-proxy regurgitation (no YAML anchor blend).",
        "best_candidate = best feasible grid point under stated surrogate assumptions "
        "(exploratory ranking / best under assumptions).",
        f"AP reduction ceiling = {cap:.1f}% (ARTO/MAVERIC ~14–15% IMA-AP context; "
        "Carillon TITAN II ~15% IMA-CS context; default planning max 20%).",
        "Prefer ΔAP / target_ap_reduction_pct as planning variable; η values are "
        "assumption-prior distribution means — not clinically calibrated constants; "
        "η_CS is NOT from MAVERIC/ARTO.",
        f"Dual-suture commissural factor ×{dual_factor:g} is an explicit hypothesis parameter.",
        "LCx: prefer optional patient-measured CS–LCx baseline; "
        "cinch model `baseline − 0.12×shortening` is a labeled assumption "
        "(default baseline 11 mm from design_space.yaml).",
        "NiTi 0.4% = illustrative engineering screen only.",
        "Pareto frontier is multi-objective exploratory screening language "
        "(leakage vs AP reduction vs LCx vs strain) — not a medical recommendation set.",
        "Physics regurg % ≠ clinical regurgitant volume.",
        "Reported settings are grid points (suture/bridge % steps), not interpolated implants.",
    ]
    if patient_cs_lcx_mm is not None:
        notes.append(
            f"Patient-measured baseline CS–LCx = {patient_cs_lcx_mm:.2f} mm was applied "
            "with the labeled assumption slope."
        )
    else:
        notes.append(
            "No patient CS–LCx provided; using illustrative baseline_cs_lcx_mm from design_space.yaml."
        )
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
        "framing": "exploratory_screening_best_under_assumptions",
        "constraints": {
            "clinical_max_ap_reduction_pct": cap,
            "niti_alternating_strain_pct_max": cons.get("niti_alternating_strain_pct_max", 0.4),
            "cs_lcx_min_mm": cons.get("cs_lcx_min_mm", 8.6) if enforce_lcx else None,
            "enforce_lcx": enforce_lcx,
            "baseline_cs_lcx_mm": patient_cs_lcx_mm
            if patient_cs_lcx_mm is not None
            else cons.get("baseline_cs_lcx_mm"),
            "baseline_cs_lcx_source": (
                "patient_measured" if patient_cs_lcx_mm is not None else "design_space_assumption"
            ),
            "cs_lcx_cinch_mm_per_pct": cons.get("cs_lcx_cinch_mm_per_pct", 0.12),
            "cs_lcx_cinch_role": "labeled_assumption_slope",
            "lcx_role": "risk_screening_threshold",
        },
        "hypotheses": {
            "dual_suture_commissural_factor": dual_factor,
            "dual_suture_role": "exploratory_hypothesis_parameter",
        },
        "n_evaluated": len(clinical),
        "n_feasible": len(all_feas),
        "p_feasible": round(p_feasible, 4),
        "best_candidate": _payload(best_candidate),
        "recommended": _payload(best_candidate),  # backward-compat shim
        "alternatives": {
            "best_ima_ap_single": _payload(best_ap),
            "best_ima_ap_dual": _payload(best_dual),
            "best_ima_cs": _payload(best_cs),
        },
        "pareto_frontier": pareto,
        "uncertainty": uncertainty,
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
    parser.add_argument(
        "--patient-cs-lcx-mm",
        type=float,
        default=None,
        help="Optional patient-measured baseline CS–LCx (mm); slope remains assumption",
    )
    parser.add_argument("--n-eta-samples", type=int, default=9)
    parser.add_argument("--skip-uncertainty", action="store_true")
    args = parser.parse_args(argv)

    rec = run_scenario_ranker(
        seed=args.seed,
        mapping_mode=args.mapping,
        clinical_max_ap_reduction_pct=args.clinical_max,
        enforce_lcx=not args.no_lcx,
        patient_cs_lcx_mm=args.patient_cs_lcx_mm,
        n_eta_samples=args.n_eta_samples,
        skip_uncertainty=args.skip_uncertainty,
    )
    rec_pt = rec.get("best_candidate") or rec.get("recommended") or {}
    print("=== IMA exploratory scenario ranker (Layer-1 surrogate) ===")
    print(f"Feasible / evaluated: {rec['n_feasible']} / {rec['n_evaluated']}  "
          f"P(feasible)={rec.get('p_feasible')}")
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
    unc = rec.get("uncertainty") or {}
    if not unc.get("skipped"):
        print(
            f"η uncertainty: top-1 stability={unc.get('ranking_stability_top1_fraction')}, "
            f"mean feasible fraction={unc.get('mean_fraction_feasible')}, "
            f"Pareto size={len(rec.get('pareto_frontier') or [])}"
        )
    print(f"Wrote: {ROOT / 'results' / 'output' / 'planner' / 'scenario_ranking.json'}")
    return rec


if __name__ == "__main__":
    main()
