"""Evaluate a single IMA design point on the Layer-1 surrogate.

Uses physics regurgitation (no YAML anchor blend) unless ``blend=True``.
Cluster-noise ROA is not used here so the sweep/planner is deterministic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from analysis.jet import classify_jet
from models.devices import (
    CS_LCX_COMPRESSION_THRESHOLD_MM,
    IMA_AP,
    IMA_CS,
    MAVERIC_BASELINE_AP_MM,
    NITI_ALTERNATING_STRAIN_MAX_PCT,
    maveric_scale_ap_mm,
)
from models.heart_geometry import HeartGeometry
from models.pathology import apply_papillary_pathology, make_papillary_mesh
from simulation.calibration import load_surrogate_calibration
from simulation.roa_surrogate import estimate_roa_mm2, niti_bridge_strain
from simulation.run_case import run_fea_surrogate
from sph.hemodynamics import regurgitation_fraction_from_physics, SPHSurrogate

ROOT = Path(__file__).resolve().parents[1]


def load_design_space(path: Path | None = None) -> dict[str, Any]:
    p = path or ROOT / "configs" / "design_space.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_clinical_references(path: Path | None = None) -> dict[str, Any]:
    p = path or ROOT / "results" / "clinical_references.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _grid(spec: dict[str, Any]) -> list[float]:
    start = float(spec["min"])
    stop = float(spec["max"])
    step = float(spec["step"])
    vals: list[float] = []
    x = start
    # Inclusive endpoint even when it does not land on the step (e.g. 10–25 step 2).
    while x <= stop + 1e-9:
        vals.append(round(x, 8))
        x += step
    if vals and vals[-1] < stop - 1e-9:
        vals.append(round(stop, 8))
    return vals


def shortening_grid(device: str, design_space: dict[str, Any] | None = None) -> list[float]:
    cfg = design_space or load_design_space()
    key = "ima_ap" if device.upper().startswith("IMA-AP") else "ima_cs"
    if device.lower() in {"dual", "ima-ap-dual"}:
        spec = cfg.get("dual_suture", {}).get("shortening_pct", cfg["ima_ap"]["shortening_pct"])
        return _grid(spec)
    return _grid(cfg[key]["shortening_pct"])


@dataclass
class DesignPoint:
    case_id: str
    device: Optional[str]
    shortening_pct: Optional[float]
    mapping_mode: str
    n_sutures: int
    annulus_circumference_mm: float
    ap_diameter_mm: float
    ap_reduction_mm: float
    ap_reduction_pct: float
    ap_diameter_maveric_scale_mm: float
    roa_mm2: float
    central_roa_mm2: float
    commissural_roa_mm2: float
    jet_location: str
    commissural_fraction: float
    physics_regurgitation_pct: float
    blended_regurgitation_pct: Optional[float]
    coaptation_gap_mm: float
    max_principal_strain: float
    niti_alternating_strain_pct: Optional[float]
    niti_engineering_strain: Optional[float]
    cs_lcx_mm: Optional[float]
    constraint_violations: list[str] = field(default_factory=list)

    @property
    def feasible(self) -> bool:
        return not self.constraint_violations

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["feasible"] = self.feasible
        d["constraint_violations"] = ",".join(self.constraint_violations)
        return d


def _make_device(
    device_type: Optional[str],
    shortening_pct: Optional[float],
    *,
    mapping_mode: str,
    n_sutures: int,
    design_space: dict[str, Any],
):
    cmap = design_space.get("clinical_mapping", {})
    cons = design_space.get("constraints", {})
    if device_type is None or shortening_pct is None:
        return None
    if device_type == "IMA-CS":
        return IMA_CS(
            bridge_shortening_pct=float(shortening_pct),
            mapping_mode=mapping_mode,
            clinical_ap_transfer_eta=float(cmap.get("ap_transfer_eta_ima_cs", 0.66818)),
            baseline_cs_lcx_mm=float(cons.get("baseline_cs_lcx_mm", 11.0)),
            cs_lcx_cinch_mm_per_pct=float(cons.get("cs_lcx_cinch_mm_per_pct", 0.12)),
        )
    if device_type in {"IMA-AP", "IMA-AP-dual"}:
        ns = 2 if device_type == "IMA-AP-dual" else n_sutures
        return IMA_AP(
            shortening_pct=float(shortening_pct),
            mapping_mode=mapping_mode,
            clinical_ap_transfer_eta=float(cmap.get("ap_transfer_eta_ima_ap", 0.30)),
            n_sutures=ns,
        )
    raise ValueError(f"Unknown device_type: {device_type}")


def evaluate_design_point(
    *,
    device_type: Optional[str],
    shortening_pct: Optional[float],
    mapping_mode: str = "galili",
    n_sutures: int = 1,
    case_id: Optional[str] = None,
    elements=None,
    calibration: Optional[dict[str, Any]] = None,
    design_space: Optional[dict[str, Any]] = None,
    seed: int = 42,
    blend: bool = False,
) -> DesignPoint:
    """Physics evaluation of one (device, shortening, mapping) point."""
    _ = seed
    cfg = design_space or load_design_space()
    cal = calibration or load_surrogate_calibration()
    if elements is None:
        elements = apply_papillary_pathology(
            make_papillary_mesh(200), posterior_fraction_passive=0.44
        )

    if device_type == "IMA-AP-dual":
        n_sutures = 2
        label = "IMA-AP"
    else:
        label = device_type

    device = _make_device(
        device_type,
        shortening_pct,
        mapping_mode=mapping_mode,
        n_sutures=n_sutures,
        design_space=cfg,
    )
    geom = device.apply() if device is not None else HeartGeometry()
    cid = case_id or _default_case_id(device_type, shortening_pct, mapping_mode, n_sutures)

    fea = run_fea_surrogate(cid, geom, elements, device)
    if isinstance(device, IMA_CS):
        fea.max_principal_strain = max(
            fea.max_principal_strain,
            niti_bridge_strain(device.bridge_shortening_pct) * 0.85,
        )

    roa = estimate_roa_mm2(geom, fea, device, case_id=cid, calibration=cal)
    jet = classify_jet(device, geom, roa_mm2=roa)
    comm_leak = bool(getattr(device, "commissural_leak_risk", lambda: False)())
    physics_frac = regurgitation_fraction_from_physics(
        geom,
        roa,
        fea.coaptation_gap_mm,
        commissural_leak=comm_leak,
        commissural_fraction=jet.commissural_fraction,
        calibration=cal,
    )

    blended_pct = None
    if blend:
        sph = SPHSurrogate(n_particles=29000, calibration=cal)
        blended_pct = sph.run(
            cid,
            geom,
            roa,
            coaptation_gap_mm=fea.coaptation_gap_mm,
            commissural_leak=comm_leak,
            commissural_fraction=jet.commissural_fraction,
        ).regurgitation_pct

    if isinstance(device, IMA_AP):
        ap_red_mm = device.ap_reduction_mm()
        ap_red_pct = device.ap_reduction_pct()
        n_sut = device.n_sutures
        niti_alt = None
        niti_eng = None
        cs_lcx = None
    elif isinstance(device, IMA_CS):
        ap_red_mm = device.ap_reduction_mm()
        ap_red_pct = device.ap_reduction_pct()
        n_sut = 0
        niti_alt = device.niti_alternating_strain_pct()
        niti_eng = niti_bridge_strain(device.bridge_shortening_pct)
        cs_lcx = device.cs_lcx_mm()
    else:
        ap_red_mm = 0.0
        ap_red_pct = 0.0
        n_sut = 0
        niti_alt = None
        niti_eng = None
        cs_lcx = None

    maveric_ap = maveric_scale_ap_mm(
        ap_red_pct,
        baseline_mm=float(cfg.get("clinical_mapping", {}).get("maveric_baseline_ap_mm", MAVERIC_BASELINE_AP_MM)),
    )

    return DesignPoint(
        case_id=cid,
        device=label,
        shortening_pct=shortening_pct,
        mapping_mode=mapping_mode,
        n_sutures=n_sut,
        annulus_circumference_mm=geom.annulus_circumference_mm,
        ap_diameter_mm=geom.ap_diameter_mm,
        ap_reduction_mm=ap_red_mm,
        ap_reduction_pct=ap_red_pct,
        ap_diameter_maveric_scale_mm=maveric_ap,
        roa_mm2=roa,
        central_roa_mm2=jet.central_roa_mm2,
        commissural_roa_mm2=jet.commissural_roa_mm2,
        jet_location=jet.location,
        commissural_fraction=jet.commissural_fraction,
        physics_regurgitation_pct=physics_frac * 100.0,
        blended_regurgitation_pct=blended_pct,
        coaptation_gap_mm=fea.coaptation_gap_mm,
        max_principal_strain=fea.max_principal_strain,
        niti_alternating_strain_pct=niti_alt,
        niti_engineering_strain=niti_eng,
        cs_lcx_mm=cs_lcx,
    )


def apply_constraints(
    point: DesignPoint,
    design_space: dict[str, Any] | None = None,
    *,
    clinical_max_ap_reduction_pct: float | None = None,
    enforce_lcx: bool = True,
) -> DesignPoint:
    """Fill ``constraint_violations`` in place and return the point."""
    cfg = design_space or load_design_space()
    cons = cfg.get("constraints", {})
    cap = (
        clinical_max_ap_reduction_pct
        if clinical_max_ap_reduction_pct is not None
        else float(cons.get("clinical_max_ap_reduction_pct", 20.0))
    )
    strain_max = float(cons.get("niti_alternating_strain_pct_max", NITI_ALTERNATING_STRAIN_MAX_PCT))
    lcx_min = float(cons.get("cs_lcx_min_mm", CS_LCX_COMPRESSION_THRESHOLD_MM))

    viol: list[str] = []
    if point.ap_reduction_pct > cap + 1e-9:
        viol.append("ap_reduction")
    if (
        point.niti_alternating_strain_pct is not None
        and point.niti_alternating_strain_pct >= strain_max - 1e-12
    ):
        viol.append("niti_alternating_strain")
    if (
        enforce_lcx
        and point.device == "IMA-CS"
        and point.cs_lcx_mm is not None
        and point.cs_lcx_mm < lcx_min - 1e-12
    ):
        viol.append("cs_lcx")
    point.constraint_violations = viol
    return point


def _default_case_id(
    device_type: Optional[str],
    shortening_pct: Optional[float],
    mapping_mode: str,
    n_sutures: int,
) -> str:
    if device_type is None:
        return f"sweep_pathology_{mapping_mode}"
    tag = "dual" if (device_type == "IMA-AP-dual" or n_sutures >= 2) else "s"
    short = "cs" if device_type == "IMA-CS" else "ap"
    pct = int(round(float(shortening_pct or 0)))
    return f"sweep_{short}_{tag}{pct}_{mapping_mode}"
