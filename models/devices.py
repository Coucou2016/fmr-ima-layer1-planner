"""IMA-CS and IMA-AP device deformation models.

Mapping modes
-------------
``galili`` (default)
    Reproduces Galili et al. RSOS 2022 LHHM *geometry* at the published
    shortening settings. IMA-AP anterior–posterior (AP) diameter stays at
    the 34.4 mm baseline through 50% suture shortening and collapses to
    14.3 mm at 70% (~58% AP reduction). That 70% AP collapse is a
    numerical extreme, not a clinically attested dose.

``clinical``
    Maps suture / bridge shortening onto *clinically attainable* AP
    diameter reduction (Innovation A). Transfer efficiency ``eta`` is an
    explicit planning assumption, not a new FEA result:

    * IMA-AP: ``AP_reduction% ≈ 0.30 × suture_shortening%`` so that 50%
      suture ≈ 15% AP reduction (MAVERIC window).
    * IMA-CS: ``AP_reduction% ≈ (14.7/22) × bridge_shortening%`` so that
      Galili's 22% CS case corresponds to MAVERIC ~14.7% AP reduction.

See ``results/clinical_references.yaml`` for citations and the full
assumption table. This module does **not** claim new LHHM/Abaqus FEA.
"""

from __future__ import annotations

from dataclasses import dataclass

from .heart_geometry import HeartGeometry

# Galili LHHM diastolic baseline (this surrogate's internal geometry).
GALILI_BASELINE_AP_MM = 34.4
GALILI_BASELINE_ANNULUS_MM = 118.5
GALILI_IMA_CS_22_ANNULUS_MM = 115.0
GALILI_IMA_AP_70_AP_MM = 14.3

# MAVERIC-scale AP used only for reporting (mm), not as the FEA mesh.
MAVERIC_BASELINE_AP_MM = 41.4
MAVERIC_FOLLOWUP_AP_MM = 35.3
MAVERIC_AP_REDUCTION_PCT = 100.0 * (1.0 - MAVERIC_FOLLOWUP_AP_MM / MAVERIC_BASELINE_AP_MM)

# Clinical transfer efficiencies (planning assumptions; documented in YAML).
CLINICAL_ETA_IMA_AP = 0.30
CLINICAL_ETA_IMA_CS = MAVERIC_AP_REDUCTION_PCT / 22.0  # ~0.668

# Rottländer 2021 distal-landing-zone LCx compression threshold.
CS_LCX_COMPRESSION_THRESHOLD_MM = 8.6

# NiTi fatigue: keep *alternating* (cyclic) strain below this percent.
NITI_ALTERNATING_STRAIN_MAX_PCT = 0.4


def maveric_scale_ap_mm(ap_reduction_pct: float, baseline_mm: float = MAVERIC_BASELINE_AP_MM) -> float:
    """AP diameter on the MAVERIC millimetre scale for a given % reduction."""
    return baseline_mm * (1.0 - max(ap_reduction_pct, 0.0) / 100.0)


def niti_alternating_strain_pct(bridge_shortening_pct: float) -> float:
    """Cyclic strain % in the NiTi CS bridge during the cardiac cycle.

    Mean shortening strain is large (superelastic). Fatigue is driven by
    alternating strain; the 0.4% cap is a planning constraint, not Galili's
    engineering-strain output. Linear surrogate: 0.10 + 0.012 × shortening%.
    """
    return 0.10 + 0.012 * max(bridge_shortening_pct, 0.0)


def cs_lcx_distance_mm(
    bridge_shortening_pct: float,
    baseline_cs_lcx_mm: float = 11.0,
    cinch_mm_per_pct: float = 0.12,
) -> float:
    """Distal-landing-zone CS–LCx distance after IMA-CS cinching.

    Patient-specific ``baseline_cs_lcx_mm`` is a preoperative CT input.
    The default 11.0 mm is an illustrative anatomy, not a population mean.
    """
    return max(0.0, baseline_cs_lcx_mm - cinch_mm_per_pct * max(bridge_shortening_pct, 0.0))


@dataclass
class IMA_CS:
    """Indirect mitral annuloplasty — coronary sinus bridge shortening."""

    bridge_shortening_pct: float
    baseline_annulus_mm: float = GALILI_BASELINE_ANNULUS_MM
    ap_diameter_mm: float = GALILI_BASELINE_AP_MM
    mapping_mode: str = "galili"
    clinical_ap_transfer_eta: float = CLINICAL_ETA_IMA_CS
    baseline_cs_lcx_mm: float = 11.0
    cs_lcx_cinch_mm_per_pct: float = 0.12

    def apply(self) -> HeartGeometry:
        # Calibrated: 22% shortening -> 118.5 -> 115 mm circumference
        delta_per_pct = (GALILI_BASELINE_ANNULUS_MM - GALILI_IMA_CS_22_ANNULUS_MM) / 22.0
        new_circ = self.baseline_annulus_mm - delta_per_pct * self.bridge_shortening_pct
        return HeartGeometry(
            ap_diameter_mm=self.resulting_ap_diameter_mm(),
            annulus_circumference_mm=max(new_circ, 100.0),
        )

    def resulting_ap_diameter_mm(self) -> float:
        if self.mapping_mode == "clinical":
            red = min(0.40, max(0.0, self.clinical_ap_transfer_eta * self.bridge_shortening_pct / 100.0))
            return self.ap_diameter_mm * (1.0 - red)
        return self.ap_diameter_mm

    def ap_reduction_mm(self) -> float:
        return max(0.0, self.ap_diameter_mm - self.resulting_ap_diameter_mm())

    def ap_reduction_pct(self) -> float:
        return 100.0 * self.ap_reduction_mm() / max(self.ap_diameter_mm, 1e-9)

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
    """IMA anterior-posterior suture between CS and interatrial septum."""

    shortening_pct: float
    baseline_ap_mm: float = GALILI_BASELINE_AP_MM
    baseline_annulus_mm: float = GALILI_BASELINE_ANNULUS_MM
    mapping_mode: str = "galili"
    clinical_ap_transfer_eta: float = CLINICAL_ETA_IMA_AP
    n_sutures: int = 1

    def apply(self) -> HeartGeometry:
        annulus = self.baseline_annulus_mm - 0.05 * self.shortening_pct
        return HeartGeometry(
            ap_diameter_mm=self.resulting_ap_diameter_mm(),
            annulus_circumference_mm=annulus,
        )

    def resulting_ap_diameter_mm(self) -> float:
        if self.mapping_mode == "clinical":
            red = min(0.50, max(0.0, self.clinical_ap_transfer_eta * self.shortening_pct / 100.0))
            return self.baseline_ap_mm * (1.0 - red)
        # Galili LHHM: AP unchanged through 50% suture; 70% -> 14.3 mm.
        if self.shortening_pct <= 50:
            return self.baseline_ap_mm
        t = (self.shortening_pct - 50) / 20.0
        return self.baseline_ap_mm + t * (GALILI_IMA_AP_70_AP_MM - self.baseline_ap_mm)

    def ap_reduction_mm(self) -> float:
        return max(0.0, self.baseline_ap_mm - self.resulting_ap_diameter_mm())

    def ap_reduction_pct(self) -> float:
        return 100.0 * self.ap_reduction_mm() / max(self.baseline_ap_mm, 1e-9)

    def commissural_leak_risk(self) -> bool:
        """Binary flag used by the Galili-calibrated FEA/SPH path.

        Dual suture delays the flag (Innovation D). Clinical mode uses AP
        reduction vs the 20% planning ceiling rather than suture %.
        """
        if self.mapping_mode == "clinical":
            threshold = 28.0 if self.n_sutures >= 2 else 20.0
            return self.ap_reduction_pct() >= threshold - 1e-9
        if self.n_sutures >= 2:
            return self.shortening_pct >= 80
        return self.shortening_pct >= 70
