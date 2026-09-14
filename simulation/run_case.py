"""Algebraic / phenomenological mechanics proxy (not FEA).

Legacy names ``run_fea_surrogate`` / ``FEASurrogateResult`` remain as aliases.
Outputs such as coaptation gap and strain are **uncalibrated proxy scores**,
not finite-element solutions.
"""

from dataclasses import dataclass
from typing import List, Optional

from models.heart_geometry import HeartGeometry
from models.pathology import PapillaryElement, pathology_severity
from models.devices import (
    GALILI_PEAK_SYS_DISEASE_AP_MM,
    IMA_CS,
    IMA_AP,
    UNDEFORMED_DIASTOLE_AP_MM,
)


@dataclass
class MechanicsProxyResult:
    """Uncalibrated proxy scores from the algebraic mechanics surrogate."""

    case_id: str
    geometry: HeartGeometry
    pathology_severity: float
    max_principal_strain: float  # strain_risk_score (proxy)
    contact_force_max_n: float  # contact_score (proxy)
    coaptation_gap_mm: float


# Backward-compatible alias
FEASurrogateResult = MechanicsProxyResult


def run_mechanics_proxy(
    case_id: str,
    geometry: HeartGeometry,
    elements: List[PapillaryElement],
    device: Optional[object] = None,
) -> MechanicsProxyResult:
    """
    Phenomenological / algebraic mechanics surrogate (no Abaqus / no FE mesh).

    Strain and contact scale with pathology severity and annulus shrinkage.
    Reported N/%-like outputs are uncalibrated proxy scores.
    """
    sev = pathology_severity(elements)
    annulus_reduction = 118.5 - geometry.annulus_circumference_mm
    gap = 2.85 * sev - 0.11 * annulus_reduction

    n_sutures = int(getattr(device, "n_sutures", 1) or 1)
    mapping_mode = getattr(device, "mapping_mode", "galili")
    disease_ap = GALILI_PEAK_SYS_DISEASE_AP_MM

    if isinstance(device, IMA_CS):
        gap -= 0.024 * device.bridge_shortening_pct
        if mapping_mode == "clinical":
            # Planning map transmits CS cinching into AP reduction (assumption).
            gap -= 0.03 * max(0.0, UNDEFORMED_DIASTOLE_AP_MM - geometry.ap_diameter_mm)
        else:
            # Mild peak-systolic AP change vs disease in Galili CS cases.
            gap -= 0.02 * max(0.0, disease_ap - geometry.ap_diameter_mm)
        strain = 0.06 + 0.10 * sev + 0.0014 * device.bridge_shortening_pct
    elif isinstance(device, IMA_AP):
        if mapping_mode == "clinical":
            ap_red = device.ap_reduction_pct()
            gap -= 0.045 * min(ap_red, 16.0)
            over = max(0.0, ap_red - 18.0)
            penalty = 0.12 * over
            if n_sutures >= 2:
                penalty *= 0.5  # dual-suture jet hypothesis parameter
            gap += penalty
            strain = 0.07 + 0.11 * sev - 0.001 * annulus_reduction
            if ap_red >= 20.0 and n_sutures < 2:
                strain += 0.01
        else:
            # Galili peak-systole branch: AP shortens nearly directly with suture %.
            # Over-shortening opens gap modestly (qualitative non-monotonicity) without
            # stacking a pathology-scale leak (Galili 0.08→0.13%, not 0.08→5%).
            ap_red = device.ap_reduction_pct()
            if device.shortening_pct <= 50:
                gap -= 0.020 * device.shortening_pct
                gap -= 0.01 * max(0.0, ap_red - 15.0)
            else:
                over = device.shortening_pct - 50.0
                penalty = 0.012 * over + 0.15
                if n_sutures >= 2:
                    penalty *= 0.5  # hypothesis parameter
                gap += penalty
            strain = 0.07 + 0.11 * sev - 0.001 * annulus_reduction
            if device.commissural_leak_risk():
                strain += 0.025
    else:
        strain = 0.08 + 0.12 * sev - 0.002 * annulus_reduction

    contact = 0.5 + 2.0 * (1.0 - sev) + 0.1 * annulus_reduction
    return MechanicsProxyResult(
        case_id=case_id,
        geometry=geometry,
        pathology_severity=sev,
        max_principal_strain=max(strain, 0.01),
        contact_force_max_n=max(contact, 0.1),
        coaptation_gap_mm=max(gap, 0.0),
    )


# Backward-compatible alias
run_fea_surrogate = run_mechanics_proxy
