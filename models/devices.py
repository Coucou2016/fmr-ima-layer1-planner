"""IMA-CS and IMA-AP device deformation models (algebraic / phenomenological).

Mapping modes
-------------
``galili`` (default)
    Reproduces *peak-systolic* AP diameters published by Galili et al.
    R. Soc. Open Sci. 2022. IMA-AP has a near-direct effect on AP diameter:
    disease 26.1 mm → IMA-AP 50% → **15.9 mm** (not undeformed diastole 34.4 mm).
    Undeformed/diastolic AP = 34.4 mm is a separate cardiac phase and must not
    be mixed with peak-systolic ROA/leakage in one case record.

``clinical``
    Exploratory planning map from suture/bridge shortening onto a *target*
    AP-diameter reduction window. Transfer efficiency ``eta`` (if used) is an
    **assumption prior**, not a clinically calibrated constant:

    * IMA-AP: optional ``eta_ap`` assumption so planners can talk in ~14–20% AP
      windows (ARTO/MAVERIC geometric context — same mechanism class as IMA-AP).
    * IMA-CS: prefer ``target_ap_reduction_pct`` as the planning variable.
      Any retained ``eta_cs`` is an assumption distribution mean — **not**
      fitted from MAVERIC (MAVERIC = ARTO ≠ Carillon).

See ``results/clinical_references.yaml``. This module does **not** claim FEA.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from .heart_geometry import HeartGeometry

# Undeformed / diastolic baseline (separate cardiac phase).
UNDEFORMED_DIASTOLE_AP_MM = 34.4
GALILI_BASELINE_AP_MM = UNDEFORMED_DIASTOLE_AP_MM  # legacy alias
GALILI_BASELINE_ANNULUS_MM = 118.5
GALILI_IMA_CS_22_ANNULUS_MM = 115.0

# Peak-systole Galili AP diameters (literature facts).
GALILI_PEAK_SYS_DISEASE_AP_MM = 26.1
GALILI_PEAK_SYS_IMA_AP = (
    (0.0, 26.1),
    (30.0, 20.7),
    (50.0, 15.9),
    (70.0, 12.4),
)
GALILI_PEAK_SYS_IMA_CS = (
    (0.0, 26.1),
    (14.0, 25.5),
    (18.0, 24.7),
    (22.0, 24.8),
)

# Legacy name kept so old imports do not break; value was the false AP70 claim.
GALILI_IMA_AP_70_AP_MM = 12.4
GALILI_IMA_AP_50_AP_MM = 15.9

# ARTO / MAVERIC geometric pairs (IMA-AP class) — reporting scale only.
ARTO_MAVERIC_BASELINE_AP_MM = 41.4
ARTO_MAVERIC_FOLLOWUP_AP_MM = 35.3
ARTO_MAVERIC_AP_REDUCTION_PCT = 100.0 * (
    1.0 - ARTO_MAVERIC_FOLLOWUP_AP_MM / ARTO_MAVERIC_BASELINE_AP_MM
)
# Legacy aliases (do not interpret as Carillon calibration).
MAVERIC_BASELINE_AP_MM = ARTO_MAVERIC_BASELINE_AP_MM
MAVERIC_FOLLOWUP_AP_MM = ARTO_MAVERIC_FOLLOWUP_AP_MM
MAVERIC_AP_REDUCTION_PCT = ARTO_MAVERIC_AP_REDUCTION_PCT

# Planning assumption priors (NOT clinically calibrated constants).
ASSUMPTION_ETA_IMA_AP = 0.30  # exploratory; 50% suture → 15% AP planning talk
ASSUMPTION_ETA_IMA_CS = 0.55  # exploratory prior; NOT from MAVERIC/ARTO
CLINICAL_ETA_IMA_AP = ASSUMPTION_ETA_IMA_AP  # legacy alias
CLINICAL_ETA_IMA_CS = ASSUMPTION_ETA_IMA_CS  # legacy alias — was wrongly MAVERIC/22

# Rottländer 2021 distal-landing-zone LCx *risk-screening* threshold (not "safety").
CS_LCX_RISK_SCREEN_THRESHOLD_MM = 8.6
CS_LCX_COMPRESSION_THRESHOLD_MM = CS_LCX_RISK_SCREEN_THRESHOLD_MM  # legacy alias

# NiTi alternating strain — illustrative engineering screen only.
NITI_ALTERNATING_STRAIN_MAX_PCT = 0.4


def _interp_piecewise(x: float, table: Sequence[Tuple[float, float]]) -> float:
    """Linear interpolation/extrapolation on a sorted (x, y) table."""
    pts = sorted(table, key=lambda t: t[0])
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if abs(x1 - x0) < 1e-12:
                return y1
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return pts[-1][1]


def galili_peak_systole_ap_mm(
    *,
    device: str,
    shortening_pct: float,
) -> float:
    """Published Galili peak-systolic AP (mm) vs device shortening %."""
    if device.upper().startswith("IMA-CS"):
        return _interp_piecewise(shortening_pct, GALILI_PEAK_SYS_IMA_CS)
    return _interp_piecewise(shortening_pct, GALILI_PEAK_SYS_IMA_AP)


def maveric_scale_ap_mm(
    ap_reduction_pct: float, baseline_mm: float = ARTO_MAVERIC_BASELINE_AP_MM
) -> float:
    """AP diameter on the ARTO/MAVERIC millimetre reporting scale."""
    return baseline_mm * (1.0 - max(ap_reduction_pct, 0.0) / 100.0)


def niti_alternating_strain_pct(bridge_shortening_pct: float) -> float:
    """Illustrative cyclic strain % screen for the NiTi CS bridge.

    Not a fatigue qualification. Linear screen: 0.10 + 0.012 × shortening%.
    """
    return 0.10 + 0.012 * max(bridge_shortening_pct, 0.0)


def cs_lcx_distance_mm(
    bridge_shortening_pct: float,
    baseline_cs_lcx_mm: float = 11.0,
    cinch_mm_per_pct: float = 0.12,
) -> float:
    """Distal-landing-zone CS–LCx distance after IMA-CS cinching (assumption).

    ``baseline_cs_lcx_mm`` should be patient-measured CT when available.
    Default 11.0 mm is illustrative. The ``0.12 mm per %`` cinch slope is an
    assumption, not a fitted imaging–mechanics law.
    """
    return max(0.0, baseline_cs_lcx_mm - cinch_mm_per_pct * max(bridge_shortening_pct, 0.0))


@dataclass
class IMA_CS:
    """Indirect mitral annuloplasty — coronary sinus bridge shortening (Carillon class)."""

    bridge_shortening_pct: float
    baseline_annulus_mm: float = GALILI_BASELINE_ANNULUS_MM
    ap_diameter_mm: float = GALILI_PEAK_SYS_DISEASE_AP_MM
    mapping_mode: str = "galili"
    # Assumption prior for exploratory ranking — NOT MAVERIC-calibrated.
    clinical_ap_transfer_eta: float = ASSUMPTION_ETA_IMA_CS
    # Preferred planning variable when set (overrides eta×bridge).
    target_ap_reduction_pct: Optional[float] = None
    baseline_cs_lcx_mm: float = 11.0
    cs_lcx_cinch_mm_per_pct: float = 0.12
    cardiac_phase: str = "peak_systole"

    def apply(self) -> HeartGeometry:
        delta_per_pct = (GALILI_BASELINE_ANNULUS_MM - GALILI_IMA_CS_22_ANNULUS_MM) / 22.0
        new_circ = self.baseline_annulus_mm - delta_per_pct * self.bridge_shortening_pct
        return HeartGeometry(
            ap_diameter_mm=self.resulting_ap_diameter_mm(),
            annulus_circumference_mm=max(new_circ, 100.0),
            cardiac_phase=self.cardiac_phase if self.mapping_mode == "galili" else "planning",
        )

    def resulting_ap_diameter_mm(self) -> float:
        if self.mapping_mode == "clinical":
            red = self.ap_reduction_pct() / 100.0
            # Clinical planning applies % reduction to undeformed/planning baseline.
            baseline = UNDEFORMED_DIASTOLE_AP_MM
            return baseline * (1.0 - min(0.40, max(0.0, red)))
        return galili_peak_systole_ap_mm(
            device="IMA-CS", shortening_pct=self.bridge_shortening_pct
        )

    def ap_reduction_mm(self) -> float:
        if self.mapping_mode == "clinical":
            return max(0.0, UNDEFORMED_DIASTOLE_AP_MM - self.resulting_ap_diameter_mm())
        return max(0.0, GALILI_PEAK_SYS_DISEASE_AP_MM - self.resulting_ap_diameter_mm())

    def ap_reduction_pct(self) -> float:
        if self.mapping_mode == "clinical":
            if self.target_ap_reduction_pct is not None:
                return float(self.target_ap_reduction_pct)
            # Assumption prior only — not clinically calibrated from MAVERIC/ARTO.
            return min(40.0, max(0.0, self.clinical_ap_transfer_eta * self.bridge_shortening_pct))
        base = GALILI_PEAK_SYS_DISEASE_AP_MM
        return 100.0 * self.ap_reduction_mm() / max(base, 1e-9)

    def cs_lcx_mm(self) -> float:
        return cs_lcx_distance_mm(
            self.bridge_shortening_pct,
            baseline_cs_lcx_mm=self.baseline_cs_lcx_mm,
            cinch_mm_per_pct=self.cs_lcx_cinch_mm_per_pct,
        )

    def niti_alternating_strain_pct(self) -> float:
        return niti_alternating_strain_pct(self.bridge_shortening_pct)


@dataclass
class IMA_AP:
    """IMA anterior-posterior suture (CS–IAS; ARTO / MAVERIC mechanism class)."""

    shortening_pct: float
    baseline_ap_mm: float = GALILI_PEAK_SYS_DISEASE_AP_MM
    baseline_annulus_mm: float = GALILI_BASELINE_ANNULUS_MM
    mapping_mode: str = "galili"
    clinical_ap_transfer_eta: float = ASSUMPTION_ETA_IMA_AP
    target_ap_reduction_pct: Optional[float] = None
    n_sutures: int = 1
    cardiac_phase: str = "peak_systole"

    def apply(self) -> HeartGeometry:
        annulus = self.baseline_annulus_mm - 0.05 * self.shortening_pct
        return HeartGeometry(
            ap_diameter_mm=self.resulting_ap_diameter_mm(),
            annulus_circumference_mm=annulus,
            cardiac_phase=self.cardiac_phase if self.mapping_mode == "galili" else "planning",
        )

    def resulting_ap_diameter_mm(self) -> float:
        if self.mapping_mode == "clinical":
            red = self.ap_reduction_pct() / 100.0
            baseline = UNDEFORMED_DIASTOLE_AP_MM
            return baseline * (1.0 - min(0.50, max(0.0, red)))
        return galili_peak_systole_ap_mm(
            device="IMA-AP", shortening_pct=self.shortening_pct
        )

    def ap_reduction_mm(self) -> float:
        if self.mapping_mode == "clinical":
            return max(0.0, UNDEFORMED_DIASTOLE_AP_MM - self.resulting_ap_diameter_mm())
        return max(0.0, GALILI_PEAK_SYS_DISEASE_AP_MM - self.resulting_ap_diameter_mm())

    def ap_reduction_pct(self) -> float:
        if self.mapping_mode == "clinical":
            if self.target_ap_reduction_pct is not None:
                return float(self.target_ap_reduction_pct)
            return min(50.0, max(0.0, self.clinical_ap_transfer_eta * self.shortening_pct))
        base = GALILI_PEAK_SYS_DISEASE_AP_MM
        return 100.0 * self.ap_reduction_mm() / max(base, 1e-9)

    def commissural_leak_risk(self) -> bool:
        """Proxy flag for commissural leak risk (uncalibrated score trigger).

        Dual suture delays the flag (hypothesis parameter ×0.5 on jet penalties
        elsewhere). Clinical mode uses AP reduction vs a planning ceiling.
        """
        if self.mapping_mode == "clinical":
            threshold = 28.0 if self.n_sutures >= 2 else 20.0
            return self.ap_reduction_pct() >= threshold - 1e-9
        if self.n_sutures >= 2:
            return self.shortening_pct >= 80
        return self.shortening_pct >= 70
