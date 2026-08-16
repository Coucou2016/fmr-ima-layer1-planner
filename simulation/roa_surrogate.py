"""ROA estimate and synthetic contact nodes from FEA surrogate outputs."""

from __future__ import annotations

import hashlib
import math
from typing import Any, List, Optional

import numpy as np

from analysis.roa import ContactNode, compute_roa_from_contacts
from models.devices import IMA_AP, IMA_CS
from models.heart_geometry import HeartGeometry
from simulation.calibration import load_surrogate_calibration
from simulation.run_case import FEASurrogateResult


def stable_case_seed(base_seed: int, case_id: str) -> int:
    """Deterministic per-case seed (avoids PYTHONHASHSEED randomization of hash())."""
    digest = hashlib.md5(case_id.encode("utf-8")).hexdigest()
    return base_seed + int(digest[:8], 16) % 10000


def _roa_anchor_key(case_id: str) -> Optional[str]:
    return {
        "pathology": "pathology_typical",
        "ima_ap_50": "ima_ap_50_minimum",
    }.get(case_id)


def _pipeline_weights(case_id: str, calibration: dict[str, Any]) -> tuple[float, float]:
    roa_pipe = calibration.get("roa_pipeline", {})
    default = roa_pipe.get("default", {"model_weight": 0.88, "cluster_weight": 0.12})
    case_cfg = roa_pipe.get(case_id, default)
    return float(case_cfg.get("model_weight", 0.88)), float(case_cfg.get("cluster_weight", 0.12))


def estimate_roa_mm2(
    geometry: HeartGeometry,
    fea: FEASurrogateResult,
    device: Optional[object] = None,
    *,
    case_id: Optional[str] = None,
    calibration: Optional[dict[str, Any]] = None,
) -> float:
    """
    Effective regurgitant orifice area (mm²) from coaptation gap and device mechanism.

    Uses elliptical-orifice proxy (mm scale), not full annulus ellipse area.
    IMA-AP 50% targets minimum ROA; 70% adds commissural jet area despite AP reduction.
    """
    cfg = calibration or load_surrogate_calibration()
    gap = fea.coaptation_gap_mm
    minor = max(1.55 * gap + 0.95, 0.9)
    major = minor * (1.38 + 0.005 * geometry.annulus_circumference_mm)
    roa = math.pi * minor * major

    if isinstance(device, IMA_AP):
        mapping_mode = getattr(device, "mapping_mode", "galili")
        n_sutures = int(getattr(device, "n_sutures", 1) or 1)
        if mapping_mode == "clinical":
            ap_red = device.ap_reduction_pct()
            optim = 0.90 + 0.004 * abs(ap_red - 15.0)
            roa *= min(optim, 1.20)
            over = max(0.0, ap_red - 18.0)
            if over > 0.0:
                jet_minor = 0.55 + 0.12 * over
                if n_sutures >= 2:
                    jet_minor *= 0.55
                roa += math.pi * jet_minor * (jet_minor * 1.25)
        elif device.shortening_pct <= 50:
            optim = 0.88 + 0.002 * abs(device.shortening_pct - 50.0)
            roa *= optim
        elif device.commissural_leak_risk():
            ap_deficit = max(0.0, (34.4 - geometry.ap_diameter_mm) / 20.0)
            jet_minor = 0.85 + 0.95 * ap_deficit
            if n_sutures >= 2:
                jet_minor *= 0.55
            jet_major = jet_minor * 1.35
            roa += math.pi * jet_minor * jet_major

    roa = max(roa, 2.0)

    cid = case_id or getattr(fea, "case_id", None)
    anchors = cfg.get("roa_mm2_anchors", {})
    blend_weights = cfg.get("roa_anchor_blend_weight", {})
    anchor_key = _roa_anchor_key(cid) if cid else None
    if anchor_key and anchor_key in anchors:
        w = float(
            blend_weights.get(
                anchor_key,
                0.92 if anchor_key == "ima_ap_50_minimum" else 0.18,
            )
        )
        roa = (1.0 - w) * roa + w * float(anchors[anchor_key])

    return roa


def pipeline_roa_mm2(
    geometry: HeartGeometry,
    fea: FEASurrogateResult,
    device: Optional[object],
    *,
    case_id: str,
    seed: int = 42,
    calibration: Optional[dict[str, Any]] = None,
) -> float:
    """
    Effective ROA used by the pipeline: model estimate + contact-cluster area.

    Per-case model/cluster weights come from configs/surrogate_calibration.yaml so
    published ROA anchors (e.g. IMA-AP 50% minimum) are not washed out by cluster noise.
    """
    cfg = calibration or load_surrogate_calibration()
    model_weight, cluster_weight = _pipeline_weights(case_id, cfg)
    roa_model = estimate_roa_mm2(
        geometry, fea, device, case_id=case_id, calibration=cfg
    )
    contacts = contacts_from_fea(
        geometry, fea, device, seed=stable_case_seed(seed, case_id)
    )
    roa_cluster, _ = compute_roa_from_contacts(contacts)
    w_m = max(0.0, min(model_weight, 1.0))
    w_c = max(0.0, min(cluster_weight, 1.0))
    if w_m + w_c <= 0:
        w_m, w_c = 1.0, 0.0
    else:
        total = w_m + w_c
        w_m, w_c = w_m / total, w_c / total
    return w_m * roa_model + w_c * max(roa_cluster, 1.0)


def contacts_from_fea(
    geometry: HeartGeometry,
    fea: FEASurrogateResult,
    device: Optional[object] = None,
    *,
    n_nodes: int = 48,
    seed: int = 7,
) -> List[ContactNode]:
    """Synthetic high-force contact patch sized by coaptation gap (for ROA clustering)."""
    rng = np.random.default_rng(seed)
    gap = max(fea.coaptation_gap_mm, 0.2)
    r_mean = math.sqrt(
        max(
            estimate_roa_mm2(geometry, fea, device, case_id=getattr(fea, "case_id", None))
            / math.pi,
            0.5,
        )
    )
    angles = rng.uniform(0, 2 * np.pi, n_nodes)
    r = r_mean * (0.85 + 0.15 * rng.random(n_nodes))
    forces = rng.uniform(0.15, 1.0, n_nodes) * (1.0 + 1.0 / (1.0 + gap))
    return [
        ContactNode(
            x=float(r[i] * math.cos(angles[i])),
            y=float(r[i] * math.sin(angles[i])),
            z=0.0,
            force_n=float(forces[i]),
        )
        for i in range(n_nodes)
    ]


def niti_bridge_strain(shortening_pct: float) -> float:
    """Engineering strain in NiTi bridge from prescribed shortening (%)."""
    return max(shortening_pct / 100.0, 0.0)
