"""Jet location classifier: central vs commissural vs mixed.

Mechanism (Galili / clinical):
- IMA-AP over-shortening bunches the leaflets centrally and opens the
  commissures → commissural (or mixed) residual leak.
- IMA-CS residual leak remains a central A2–P2 jet (incomplete coaptation).
- Dual suture (Innovation D) supports the commissures and lowers the
  commissural fraction at the same AP reduction.

This is a Layer-1 surrogate split of ROA, not Doppler imaging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from models.devices import IMA_AP, IMA_CS

JET_CENTRAL = "central"
JET_MIXED = "mixed"
JET_COMMISSURAL = "commissural"


@dataclass
class JetBreakdown:
    location: str
    commissural_fraction: float
    central_roa_mm2: float
    commissural_roa_mm2: float


def _location_from_fraction(frac: float) -> str:
    if frac >= 0.55:
        return JET_COMMISSURAL
    if frac >= 0.28:
        return JET_MIXED
    return JET_CENTRAL


def commissural_fraction(device: Optional[object], geometry=None) -> float:
    """Continuous commissural share of the regurgitant orifice (0–1)."""
    _ = geometry
    if device is None:
        return 0.18  # untreated FMR: predominantly central / posterior
    if isinstance(device, IMA_CS):
        return 0.10  # residual central jet
    if isinstance(device, IMA_AP):
        n_sutures = int(getattr(device, "n_sutures", 1) or 1)
        mode = getattr(device, "mapping_mode", "galili")
        if mode == "clinical":
            ap_red = device.ap_reduction_pct()
            if ap_red <= 14.0:
                frac = 0.10 + 0.005 * ap_red
            elif ap_red <= 20.0:
                frac = 0.17 + 0.040 * (ap_red - 14.0)
            else:
                frac = 0.41 + 0.060 * (ap_red - 20.0)
        else:
            s = device.shortening_pct
            if s <= 50.0:
                frac = 0.08 + 0.002 * s
            else:
                t = (s - 50.0) / 20.0
                frac = 0.18 + 0.70 * (t ** 1.2)
        if n_sutures >= 2:
            frac *= 0.50
        return min(max(frac, 0.0), 0.95)
    return 0.18


def classify_jet(
    device: Optional[object],
    geometry=None,
    *,
    roa_mm2: float = 0.0,
) -> JetBreakdown:
    frac = commissural_fraction(device, geometry)
    central = max(roa_mm2, 0.0) * (1.0 - frac)
    commissural = max(roa_mm2, 0.0) * frac
    return JetBreakdown(
        location=_location_from_fraction(frac),
        commissural_fraction=frac,
        central_roa_mm2=central,
        commissural_roa_mm2=commissural,
    )


def split_roa(roa_mm2: float, device: Optional[object], geometry=None) -> tuple[float, float]:
    jet = classify_jet(device, geometry, roa_mm2=roa_mm2)
    return jet.central_roa_mm2, jet.commissural_roa_mm2
