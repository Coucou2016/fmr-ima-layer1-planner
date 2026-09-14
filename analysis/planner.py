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


def _pareto_common_objectives(points: list[DesignPoint]) -> list[dict[str, Any]]:
    """Global Pareto on objectives shared by all device families.

    Objectives only:
      1. minimize physics_regurgitation_pct (leakage proxy)
      2. maximize ap_reduction_pct
    LCx / NiTi are **not** objectives here (IMA-CS feasibility constraints only).
    Never substitute 1e9 / 0.0 for missing LCx/NiTi.
    """
    feas = [p for p in points if p.feasible and p.device is not None]
    if not feas:
        return []

    def dominates(a: DesignPoint, b: DesignPoint) -> bool:
        a_leak, b_leak = a.physics_regurgitation_pct, b.physics_regurgitation_pct
        a_ap, b_ap = a.ap_reduction_pct, b.ap_reduction_pct
        better_eq = a_leak <= b_leak + 1e-12 and a_ap >= b_ap - 1e-12
        strict = a_leak < b_leak - 1e-12 or a_ap > b_ap + 1e-12
        return better_eq and strict

    frontier = []
    for p in feas:
        if any(dominates(q, p) for q in feas if q is not p):
            continue
        frontier.append(
            {
                **p.to_dict(),
                "pareto_family": "global_common_objectives",
                "pareto_objectives": {
                    "minimize_physics_regurgitation_pct": p.physics_regurgitation_pct,
                    "maximize_ap_reduction_pct": p.ap_reduction_pct,
                },
            }
        )
    frontier.sort(key=lambda d: d["physics_regurgitation_pct"])
    return frontier


def _pareto_ima_cs_family(points: list[DesignPoint]) -> list[dict[str, Any]]:
    """IMA-CS-only Pareto: leakage ↓, AP↓ ↑, LCx ↑, NiTi strain ↓ (all present)."""
    feas = [
        p
        for p in points
        if p.feasible
        and p.device == "IMA-CS"
        and p.cs_lcx_mm is not None
        and p.niti_alternating_strain_pct is not None
    ]
    if not feas:
        return []

    def dominates(a: DesignPoint, b: DesignPoint) -> bool:
        better_eq = (
            a.physics_regurgitation_pct <= b.physics_regurgitation_pct + 1e-12
            and a.ap_reduction_pct >= b.ap_reduction_pct - 1e-12
            and a.cs_lcx_mm >= b.cs_lcx_mm - 1e-12  # type: ignore[operator]
            and a.niti_alternating_strain_pct
            <= b.niti_alternating_strain_pct + 1e-12  # type: ignore[operator]
        )
        strict = (
            a.physics_regurgitation_pct < b.physics_regurgitation_pct - 1e-12
            or a.ap_reduction_pct > b.ap_reduction_pct + 1e-12
            or a.cs_lcx_mm > b.cs_lcx_mm + 1e-12  # type: ignore[operator]
            or a.niti_alternating_strain_pct
            < b.niti_alternating_strain_pct - 1e-12  # type: ignore[operator]
        )
        return better_eq and strict

    frontier = []
    for p in feas:
        if any(dominates(q, p) for q in feas if q is not p):
            continue
        frontier.append(
            {
                **p.to_dict(),
                "pareto_family": "ima_cs_family",
                "pareto_objectives": {
                    "minimize_physics_regurgitation_pct": p.physics_regurgitation_pct,
                    "maximize_ap_reduction_pct": p.ap_reduction_pct,
                    "maximize_cs_lcx_mm": p.cs_lcx_mm,
                    "minimize_niti_alternating_strain_pct": p.niti_alternating_strain_pct,
                },
            }
        )
    frontier.sort(key=lambda d: d["physics_regurgitation_pct"])
    return frontier


def _pareto_ima_ap_family(points: list[DesignPoint]) -> list[dict[str, Any]]:
    """IMA-AP-only Pareto on common objectives (no LCx/NiTi — not applicable)."""
    feas = [p for p in points if p.feasible and p.device == "IMA-AP"]
    if not feas:
        return []

    def dominates(a: DesignPoint, b: DesignPoint) -> bool:
        better_eq = (
            a.physics_regurgitation_pct <= b.physics_regurgitation_pct + 1e-12
            and a.ap_reduction_pct >= b.ap_reduction_pct - 1e-12
        )
        strict = (
            a.physics_regurgitation_pct < b.physics_regurgitation_pct - 1e-12
            or a.ap_reduction_pct > b.ap_reduction_pct + 1e-12
        )
        return better_eq and strict

    frontier = []
    for p in feas:
        if any(dominates(q, p) for q in feas if q is not p):
            continue
        frontier.append(
            {
                **p.to_dict(),
                "pareto_family": "ima_ap_family",
                "pareto_objectives": {
                    "minimize_physics_regurgitation_pct": p.physics_regurgitation_pct,
                    "maximize_ap_reduction_pct": p.ap_reduction_pct,
                },
            }
        )
    frontier.sort(key=lambda d: d["physics_regurgitation_pct"])
    return frontier


def _pareto_frontier(points: list[DesignPoint]) -> list[dict[str, Any]]:
    """Backward-compatible alias → global common-objective Pareto."""
    return _pareto_common_objectives(points)

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


def _lhs_unit_sample(n: int, d: int, seed: int) -> np.ndarray:
    """Latin Hypercube in [0,1]^d (SciPy if available; else stratified RNG)."""
    try:
        from scipy.stats.qmc import LatinHypercube

        return LatinHypercube(d=d, seed=seed).random(n=n)
    except Exception:
        rng = np.random.default_rng(seed)
        out = np.zeros((n, d))
        for j in range(d):
            cut = (np.arange(n) + rng.random(n)) / n
            rng.shuffle(cut)
            out[:, j] = cut
        return out


def run_uncertainty_analysis(
    *,
    seed: int,
    mapping_mode: str,
    design_space: dict[str, Any],
    clinical_max_ap_reduction_pct: float,
    enforce_lcx: bool,
    patient_cs_lcx_mm: Optional[float],
    n_eta_samples: Optional[int] = None,
    eta_relative_span: float = 0.20,
    independent_eta: bool = True,
) -> dict[str, Any]:
    """Multi-parameter assumption-prior sensitivity (LHS by default).

    Parameters sampled (Latin Hypercube, N from design_space.uncertainty):
      η_AP, η_CS, dual commissural factor, CS–LCx baseline, CS–LCx cinch slope.
    Outputs: P(top-1), P(feasible), ranking stability, first-order Spearman/PRCC ranks.
    η / dual / LCx slopes are assumption priors — not clinically calibrated.
    """
    unc = design_space.get("uncertainty") or {}
    cmap = design_space.get("clinical_mapping", {})
    cons0 = design_space.get("constraints", {})
    dual0 = float(design_space.get("dual_suture", {}).get("commissural_factor", 0.5))
    eta_ap0 = float(cmap.get("ap_transfer_eta_ima_ap", 0.30))
    eta_cs0 = float(cmap.get("ap_transfer_eta_ima_cs", 0.55))

    eta_ap_lo, eta_ap_hi = [
        float(x) for x in unc.get("eta_ap_range", [eta_ap0 * 0.8, eta_ap0 * 1.2])
    ]
    eta_cs_lo, eta_cs_hi = [
        float(x) for x in unc.get("eta_cs_range", [eta_cs0 * 0.8, eta_cs0 * 1.2])
    ]
    dual_lo, dual_hi = [
        float(x) for x in unc.get("dual_commissural_factor_range", [0.25, 1.0])
    ]
    lcx_lo, lcx_hi = [
        float(x) for x in unc.get("baseline_cs_lcx_mm_range", [10.0, 12.0])
    ]
    slope_lo, slope_hi = [
        float(x) for x in unc.get("cs_lcx_cinch_mm_per_pct_range", [0.08, 0.16])
    ]

    n_default = int(unc.get("n_samples", 200))
    n_samp = int(n_eta_samples) if n_eta_samples is not None else n_default
    n_samp = max(n_samp, 9)
    sampling = str(unc.get("sampling", "latin_hypercube")).lower()

    # Sample matrix columns: eta_ap, eta_cs, dual, baseline_lcx, slope
    bounds = np.array(
        [
            [eta_ap_lo, eta_ap_hi],
            [eta_cs_lo, eta_cs_hi],
            [dual_lo, dual_hi],
            [lcx_lo, lcx_hi],
            [slope_lo, slope_hi],
        ],
        dtype=float,
    )
    param_names = [
        "eta_ap",
        "eta_cs",
        "dual_commissural_factor",
        "baseline_cs_lcx_mm",
        "cs_lcx_cinch_mm_per_pct",
    ]

    if sampling in {"latin_hypercube", "lhs", "sobol"} and independent_eta:
        unit = _lhs_unit_sample(n_samp, bounds.shape[0], seed)
        samples = bounds[:, 0] + unit * (bounds[:, 1] - bounds[:, 0])
        sampling_mode = "latin_hypercube_multiparam"
    elif independent_eta:
        rng = np.random.default_rng(seed)
        # Legacy 3×3 η corners + extras; dual/LCx fixed at nominal.
        pairs_eta: list[tuple[float, float]] = []
        grid_ap = np.linspace(eta_ap_lo, eta_ap_hi, 3)
        grid_cs = np.linspace(eta_cs_lo, eta_cs_hi, 3)
        for ea in grid_ap:
            for ec in grid_cs:
                pairs_eta.append((float(ea), float(ec)))
        n_extra = max(0, n_samp - len(pairs_eta))
        for _ in range(n_extra):
            pairs_eta.append(
                (float(rng.uniform(eta_ap_lo, eta_ap_hi)), float(rng.uniform(eta_cs_lo, eta_cs_hi)))
            )
        samples = np.array(
            [
                [ea, ec, dual0, float(cons0.get("baseline_cs_lcx_mm", 11.0)), float(cons0.get("cs_lcx_cinch_mm_per_pct", 0.12))]
                for ea, ec in pairs_eta
            ],
            dtype=float,
        )
        sampling_mode = "independent_eta_ap_cs"
    else:
        rng = np.random.default_rng(seed)
        grid = np.linspace(1.0 - eta_relative_span, 1.0 + eta_relative_span, max(3, n_samp // 2))
        extras = rng.uniform(1.0 - eta_relative_span, 1.0 + eta_relative_span, size=max(0, n_samp - len(grid)))
        factors = np.unique(np.round(np.concatenate([grid, extras]), 5))
        samples = np.array(
            [
                [
                    eta_ap0 * float(fac),
                    eta_cs0 * float(fac),
                    dual0,
                    float(cons0.get("baseline_cs_lcx_mm", 11.0)),
                    float(cons0.get("cs_lcx_cinch_mm_per_pct", 0.12)),
                ]
                for fac in factors
            ],
            dtype=float,
        )
        sampling_mode = "common_relative_factor_sensitivity"

    wins: dict[str, int] = {}
    feasible_counts: list[int] = []
    evaluated = 0
    best_keys: list[str] = []
    best_leaks: list[float] = []
    sample_rows: list[dict[str, float]] = []

    for row in samples:
        eta_ap, eta_cs, dual, base_lcx, slope = (float(x) for x in row)
        cfg = copy.deepcopy(design_space)
        cfg["clinical_mapping"]["ap_transfer_eta_ima_ap"] = eta_ap
        cfg["clinical_mapping"]["ap_transfer_eta_ima_cs"] = eta_cs
        cfg.setdefault("dual_suture", {})["commissural_factor"] = dual
        cfg.setdefault("constraints", {})["baseline_cs_lcx_mm"] = base_lcx
        cfg["constraints"]["cs_lcx_cinch_mm_per_pct"] = slope
        points = run_sweep(
            mappings=[mapping_mode],
            seed=seed,
            design_space=cfg,
            apply_planner_constraints=False,
            write_outputs=False,
        )
        # Prefer explicit patient baseline when provided; else use sampled baseline.
        patient = patient_cs_lcx_mm if patient_cs_lcx_mm is not None else base_lcx
        _apply_patient_cs_lcx(points, patient_cs_lcx_mm=patient, design_space=cfg)
        clinical = [p for p in points if p.mapping_mode == mapping_mode]
        for p in clinical:
            apply_constraints(
                p,
                cfg,
                clinical_max_ap_reduction_pct=clinical_max_ap_reduction_pct,
                enforce_lcx=enforce_lcx,
            )
        feas = [p for p in clinical if p.device is not None and p.feasible]
        device_n = len([p for p in clinical if p.device is not None])
        evaluated = device_n
        feasible_counts.append(len(feas))
        best = _best(feas)
        sample_rows.append(
            {
                "eta_ap": eta_ap,
                "eta_cs": eta_cs,
                "dual_commissural_factor": dual,
                "baseline_cs_lcx_mm": base_lcx,
                "cs_lcx_cinch_mm_per_pct": slope,
                "n_feasible": float(len(feas)),
                "best_leak_pct": float(best.physics_regurgitation_pct) if best else float("nan"),
            }
        )
        if best is not None:
            key = _point_key(best)
            wins[key] = wins.get(key, 0) + 1
            best_keys.append(key)
            best_leaks.append(float(best.physics_regurgitation_pct))

    n = max(len(samples), 1)
    p_feasible_mean = (
        float(np.mean([c / max(evaluated, 1) for c in feasible_counts]))
        if feasible_counts
        else 0.0
    )
    top = sorted(wins.items(), key=lambda kv: (-kv[1], kv[0]))
    p_top1 = round(top[0][1] / n, 4) if top else 0.0

    # First-order sensitivity: |Spearman| of each param vs best-candidate leak.
    sensitivity_ranks: list[dict[str, Any]] = []
    if len(sample_rows) >= 5 and any(np.isfinite(r["best_leak_pct"]) for r in sample_rows):
        y = np.array([r["best_leak_pct"] for r in sample_rows], dtype=float)
        mask = np.isfinite(y)
        for name in param_names:
            x = np.array([r[name] for r in sample_rows], dtype=float)
            if mask.sum() < 5:
                continue
            rho = float(np.corrcoef(np.argsort(np.argsort(x[mask])), np.argsort(np.argsort(y[mask])))[0, 1])
            sensitivity_ranks.append(
                {
                    "parameter": name,
                    "spearman_vs_best_leak": round(rho, 4),
                    "abs_spearman": round(abs(rho), 4),
                    "method": "spearman_rank_approx_prcc",
                }
            )
        sensitivity_ranks.sort(key=lambda d: (-d["abs_spearman"], d["parameter"]))

    stability = {
        "n_eta_samples": int(len(samples)),
        "n_samples": int(len(samples)),
        "n_eta_factors": int(len(samples)),  # legacy key
        "eta_relative_span": eta_relative_span,
        "eta_ap_nominal": eta_ap0,
        "eta_cs_nominal": eta_cs0,
        "eta_ap_range": [round(eta_ap_lo, 5), round(eta_ap_hi, 5)],
        "eta_cs_range": [round(eta_cs_lo, 5), round(eta_cs_hi, 5)],
        "dual_commissural_factor_range": [round(dual_lo, 5), round(dual_hi, 5)],
        "baseline_cs_lcx_mm_range": [round(lcx_lo, 5), round(lcx_hi, 5)],
        "cs_lcx_cinch_mm_per_pct_range": [round(slope_lo, 5), round(slope_hi, 5)],
        "eta_sampling_mode": sampling_mode,
        "sampling_mode": sampling_mode,
        "eta_role": "assumption_prior_distribution",
        "mean_fraction_feasible": round(p_feasible_mean, 4),
        "p_feasible": round(p_feasible_mean, 4),
        "p_feasible_at_nominal_grid": None,  # filled by caller
        "p_top1": p_top1,
        "P(top-1)": p_top1,
        "best_candidate_win_counts": [
            {"design_key": k, "n_wins": v, "win_fraction": round(v / n, 4)} for k, v in top
        ],
        "ranking_stability_top1_fraction": p_top1,
        "first_order_sensitivity_ranks": sensitivity_ranks,
        "honesty": (
            "Multi-parameter assumption-prior sensitivity (LHS when configured); "
            "not imaging–FEA identification, Abaqus/LHHM UQ, or clinical calibration. "
            "η_CS is not from MAVERIC/ARTO. "
            f"Sampling mode: {sampling_mode}; N={len(samples)}."
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
    n_eta_samples: Optional[int] = None,
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
    plan_range = cons.get("exploratory_planning_range_ap_reduction_pct") or cons.get(
        "clinical_window_ap_reduction_pct", [14.0, 20.0]
    )
    response_path = str(cfg.get("response_path", "fitted_response"))

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
    pareto_global = _pareto_common_objectives(clinical)
    pareto_cs = _pareto_ima_cs_family(clinical)
    pareto_ap = _pareto_ima_ap_family(clinical)
    pareto = pareto_global  # backward-compat primary key

    n_total_points = len(clinical)
    n_device_candidates = len(device_eval)
    n_feasible_device_candidates = len(all_feas)
    p_feasible_device_candidates = (
        (n_feasible_device_candidates / n_device_candidates) if device_eval else 0.0
    )
    # Legacy aliases (device-grid denominator — pathology is not a candidate).
    p_feasible = p_feasible_device_candidates

    if skip_uncertainty:
        uncertainty: dict[str, Any] = {
            "skipped": True,
            "mean_fraction_feasible": None,
            "ranking_stability_top1_fraction": None,
            "p_top1": None,
            "p_feasible": None,
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
    uncertainty["p_feasible_at_nominal_grid"] = round(p_feasible_device_candidates, 4)
    uncertainty["p_feasible_device_candidates"] = round(p_feasible_device_candidates, 4)

    notes = [
        "Layer-1 exploratory scenario ranker — phenomenological mechanics + literature-calibrated leakage proxy.",
        "Not full FSI / LHHM / Abaqus; not a clinical recommendation engine.",
        f"response_path={response_path} (fitted_response preferred for paper ranking; "
        "rule_based_proxy remains available for diagnostics).",
        "Objective is leakage_proxy_pct (alias physics_regurgitation_pct; no YAML anchor blend).",
        "best_candidate = best feasible grid point under stated surrogate assumptions "
        "(exploratory ranking / best under assumptions).",
        f"AP reduction ceiling = {cap:.1f}% (ARTO/MAVERIC ~14–15% IMA-AP context; "
        "Carillon TITAN II ~15% IMA-CS context; default planning max 20%).",
        f"Exploratory planning range AP↓ = {list(plan_range)} "
        "(legacy key clinical_window retained as alias).",
        "Prefer ΔAP / target_ap_reduction_pct as planning variable; η values are "
        "assumption-prior distribution means — not clinically calibrated constants; "
        "η_CS is NOT from MAVERIC/ARTO.",
        f"Dual-suture commissural factor ×{dual_factor:g} is an explicit hypothesis parameter "
        "(Fig.5 = factor sensitivity, not Innovation D discovery).",
        "LCx: prefer optional patient-measured CS–LCx baseline; "
        "cinch model `baseline − slope×shortening` is a labeled assumption "
        "(default baseline 11 mm from design_space.yaml).",
        "NiTi 0.4% = illustrative engineering screen only.",
        "Pareto: global common objectives = min leakage + max AP↓; "
        "LCx/NiTi enter only the IMA-CS family frontier (never 1e9/0 N/A fillers).",
        "Physics regurg % ≠ clinical regurgitant volume.",
        "Reported settings are grid points (suture/bridge % steps), not interpolated implants.",
        f"Feasibility counts: n_total_points={n_total_points} "
        f"(includes pathology), n_device_candidates={n_device_candidates}, "
        f"n_feasible_device_candidates={n_feasible_device_candidates}, "
        f"p_feasible_device_candidates={p_feasible_device_candidates:.4f}.",
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
        "objective": "minimize leakage_proxy_pct",
        "objective_alias": "minimize physics_regurgitation_pct",
        "ranker": "scenario_ranker",
        "mapping_mode": mapping_mode,
        "response_path": response_path,
        "framing": "exploratory_screening_best_under_assumptions",
        "constraints": {
            "clinical_max_ap_reduction_pct": cap,
            "exploratory_planning_range_ap_reduction_pct": list(plan_range),
            "clinical_window_ap_reduction_pct": list(plan_range),  # deprecated alias
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
            "dual_suture_role": "exploratory_hypothesis_parameter_sensitivity_not_discovery",
        },
        "n_total_points": n_total_points,
        "n_device_candidates": n_device_candidates,
        "n_feasible_device_candidates": n_feasible_device_candidates,
        "p_feasible_device_candidates": round(p_feasible_device_candidates, 4),
        # Legacy keys (same device-grid semantics; pathology excluded from denominator).
        "n_evaluated": n_total_points,
        "n_feasible": n_feasible_device_candidates,
        "p_feasible": round(p_feasible, 4),
        "best_candidate": _payload(best_candidate),
        "recommended": _payload(best_candidate),  # backward-compat shim
        "alternatives": {
            "best_ima_ap_single": _payload(best_ap),
            "best_ima_ap_dual": _payload(best_dual),
            "best_ima_cs": _payload(best_cs),
        },
        "pareto_global_common_objectives": pareto_global,
        "pareto_ima_cs_family": pareto_cs,
        "pareto_ima_ap_family": pareto_ap,
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
    parser.add_argument(
        "--n-eta-samples",
        type=int,
        default=None,
        help="LHS / η sample count (default: design_space.uncertainty.n_samples)",
    )
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
    print(f"Feasible device candidates: {rec.get('n_feasible_device_candidates', rec['n_feasible'])} / "
          f"{rec.get('n_device_candidates', rec['n_evaluated'])}  "
          f"P(feasible)={rec.get('p_feasible_device_candidates', rec.get('p_feasible'))}  "
          f"(n_total_points={rec.get('n_total_points', rec['n_evaluated'])})")
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
