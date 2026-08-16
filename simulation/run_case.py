"""Surrogate FEA step: geometry + pathology + device -> contact/strain scalars."""

from dataclasses import dataclass
from typing import List, Optional
from models.heart_geometry import HeartGeometry
from models.pathology import PapillaryElement, pathology_severity
from models.devices import IMA_CS, IMA_AP


@dataclass
class FEASurrogateResult:
    case_id: str
    geometry: HeartGeometry
    pathology_severity: float
    max_principal_strain: float
    contact_force_max_n: float
    coaptation_gap_mm: float


def run_fea_surrogate(
    case_id: str,
    geometry: HeartGeometry,
    elements: List[PapillaryElement],
    device: Optional[object] = None,
) -> FEASurrogateResult:
    """
    Reduced-order FEA surrogate (no Abaqus license).

    Strain and contact scale with pathology severity and annulus shrinkage.
    """
    sev = pathology_severity(elements)
    annulus_reduction = 118.5 - geometry.annulus_circumference_mm
    gap = 2.85 * sev - 0.11 * annulus_reduction

    n_sutures = int(getattr(device, "n_sutures", 1) or 1)
    mapping_mode = getattr(device, "mapping_mode", "galili")

    if isinstance(device, IMA_CS):
        gap -= 0.024 * device.bridge_shortening_pct
        if mapping_mode == "clinical":
            # Clinical mapping transmits CS cinching into AP reduction (MAVERIC).
            gap -= 0.03 * max(0.0, 34.4 - geometry.ap_diameter_mm)
        strain = 0.06 + 0.10 * sev + 0.0014 * device.bridge_shortening_pct
    elif isinstance(device, IMA_AP):
        if mapping_mode == "clinical":
            ap_red = device.ap_reduction_pct()
            gap -= 0.045 * min(ap_red, 16.0)
            over = max(0.0, ap_red - 18.0)
            penalty = 0.12 * over
            if n_sutures >= 2:
                penalty *= 0.5
            gap += penalty
            strain = 0.07 + 0.11 * sev - 0.001 * annulus_reduction
            if ap_red >= 20.0 and n_sutures < 2:
                strain += 0.01
        else:
            # Galili-calibrated branch — do not alter n_sutures==1 physics.
            if device.shortening_pct <= 50:
                gap -= 0.020 * device.shortening_pct
            else:
                over = device.shortening_pct - 50.0
                penalty = 0.035 * over + 0.75
                if n_sutures >= 2:
                    penalty *= 0.5
                gap += penalty
            strain = 0.07 + 0.11 * sev - 0.001 * annulus_reduction
            if device.commissural_leak_risk():
                strain += 0.025
    else:
        strain = 0.08 + 0.12 * sev - 0.002 * annulus_reduction

    contact = 0.5 + 2.0 * (1.0 - sev) + 0.1 * annulus_reduction
    return FEASurrogateResult(
        case_id=case_id,
        geometry=geometry,
        pathology_severity=sev,
        max_principal_strain=max(strain, 0.01),
        contact_force_max_n=max(contact, 0.1),
        coaptation_gap_mm=max(gap, 0.0),
    )
