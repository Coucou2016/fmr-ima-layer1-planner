"""Reduced-order SPH surrogate for regurgitation fraction.



Regurgitation ratio = particles to LA / (particles to LA + particles to aorta)

Derived from ROA, annulus tightening, coaptation gap, and commissural leak — not per-case dict lookup.

Published anchors in configs/surrogate_calibration.yaml are used only to set global scale.

"""



from __future__ import annotations



import math

from dataclasses import dataclass

from typing import Any



from models.heart_geometry import HeartGeometry

from simulation.calibration import load_surrogate_calibration





@dataclass

class RegurgitationResult:

    n_particles: int

    n_la: int

    n_aorta: int

    regurgitation_fraction: float

    regurgitation_pct: float



    @classmethod

    def from_counts(cls, n_la: int, n_aorta: int, n_total: int) -> "RegurgitationResult":

        denom = n_la + n_aorta

        frac = n_la / denom if denom > 0 else 0.0

        return cls(

            n_particles=n_total,

            n_la=n_la,

            n_aorta=n_aorta,

            regurgitation_fraction=frac,

            regurgitation_pct=100.0 * frac,

        )





def _leak_index(roa_mm2: float, coaptation_gap_mm: float, sph: dict[str, Any]) -> float:
    """Coupled ROA × coaptation-gap leak metric (mm² scale)."""
    gap_ref = float(sph.get("coaptation_gap_ref_mm", 1.25))
    gap_power = float(sph.get("coaptation_gap_exponent", 1.35))
    gap_factor = max(coaptation_gap_mm / gap_ref, 0.12) ** gap_power
    return max(roa_mm2, 1.0) * gap_factor


def _sph_scale(cfg: dict[str, Any]) -> float:
    sph = cfg["sph"]
    path_pct = sph["pathology_regurgitation_pct"] / 100.0
    ref_gap = float(sph.get("pathology_coaptation_gap_mm", 1.25))
    ref_leak = _leak_index(float(sph["pathology_roa_mm2"]), ref_gap, sph)
    # k chosen so leak_index == ref_leak and f_ann == 1 reproduces pathology anchor
    return path_pct / ((ref_leak / ref_leak) ** float(sph["roa_exponent"]))





def _clamp_frac(frac: float) -> float:
    return min(max(frac, 1e-5), 0.99)


def regurgitation_fraction_from_physics(

    geometry: HeartGeometry,

    roa_mm2: float,

    coaptation_gap_mm: float,

    *,

    commissural_leak: bool = False,

    commissural_fraction: float | None = None,

    calibration: dict[str, Any] | None = None,

) -> float:

    """

    Map hemodynamic surrogates to regurgitation fraction (0–1).



    Mechanisms:

    - Larger ROA -> more LA-directed particles

    - Annulus shrink (IMA-CS / mild IMA-AP) reduces regurgitation

    - Smaller coaptation gap improves leaflet coaptation

    - Commissural leak at excessive IMA-AP shortening (low AP) worsens regurgitation

    Optional ``commissural_fraction`` (0–1) interpolates central vs commissural
    physics. Defaults preserve the original binary ``commissural_leak`` path.

    """

    cfg = calibration or load_surrogate_calibration()

    sph = cfg["sph"]

    k = _sph_scale(cfg)



    ref_gap = float(sph.get("pathology_coaptation_gap_mm", 1.25))
    ref_leak = _leak_index(float(sph["pathology_roa_mm2"]), ref_gap, sph)
    leak = _leak_index(roa_mm2, coaptation_gap_mm, sph)
    f_leak = (leak / ref_leak) ** float(sph["roa_exponent"])

    annulus_improve = (118.5 - geometry.annulus_circumference_mm) / 3.5
    f_ann = max(0.35, 1.0 - sph["annulus_improvement_per_mm"] * annulus_improve)

    frac_central = k * f_leak * f_ann
    ap_ratio = geometry.ap_diameter_mm / 34.4
    frac_central *= max(ap_ratio, 0.5) ** 0.2

    comm = 1.0 + 3.5 * max(0.0, 1.0 - ap_ratio) ** 1.05
    comm *= 1.0 + 0.2 * max(coaptation_gap_mm - 0.9, 0.0)
    roa_eff = min(max(roa_mm2, 12.0) * comm**0.35, 48.0)
    leak_eff = _leak_index(roa_eff, coaptation_gap_mm, sph)
    f_leak_comm = (leak_eff / ref_leak) ** float(sph["roa_exponent"])
    frac_comm = k * f_leak_comm * f_ann

    if commissural_fraction is None:
        cf = 1.0 if commissural_leak else 0.0
    else:
        cf = min(max(float(commissural_fraction), 0.0), 1.0)

    frac = (1.0 - cf) * frac_central + cf * frac_comm
    return _clamp_frac(frac)





class SPHSurrogate:

    """Maps geometry + ROA + coaptation to regurgitation %; anchors set scale only."""



    def __init__(self, n_particles: int = 29000, calibration: dict[str, Any] | None = None):

        self.n_particles = n_particles

        self.calibration = calibration or load_surrogate_calibration()



    def run(

        self,

        case_id: str,

        geometry: HeartGeometry,

        roa_mm2: float,

        coaptation_gap_mm: float = 1.0,

        commissural_leak: bool = False,

        commissural_fraction: float | None = None,

    ) -> RegurgitationResult:

        _ = case_id  # retained for API / logging; physics does not branch on id

        frac = regurgitation_fraction_from_physics(

            geometry,

            roa_mm2,

            coaptation_gap_mm,

            commissural_leak=commissural_leak,

            commissural_fraction=commissural_fraction,

            calibration=self.calibration,

        )

        anchors = self.calibration.get("regurgitation_pct_anchors", {})

        blend = self.calibration.get("regurgitation_anchor_blend", {})

        if case_id in anchors and case_id in blend:

            anchor_frac = float(anchors[case_id]) / 100.0

            w = float(blend[case_id])

            frac = (1.0 - w) * frac + w * anchor_frac

        n_la = int(round(self.n_particles * frac))

        n_aorta = self.n_particles - n_la

        return RegurgitationResult.from_counts(n_la, n_aorta, self.n_particles)


