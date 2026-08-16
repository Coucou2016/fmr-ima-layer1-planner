"""Parametric mitral annulus / AP geometry (diastole baseline)."""

from dataclasses import dataclass
import math


@dataclass
class HeartGeometry:
    """Simplified annulus as ellipse; AP and annulus circumference from paper."""

    ap_diameter_mm: float = 34.4
    annulus_circumference_mm: float = 118.5

    @property
    def annulus_radius_mm(self) -> float:
        return self.annulus_circumference_mm / (2.0 * math.pi)

    def roa_proxy_mm2(self, coaptation_gap_mm: float = 0.0) -> float:
        """Elliptical leak-orifice proxy (mm² scale), not full annulus area."""
        gap = max(coaptation_gap_mm, 0.0)
        minor = max(1.55 * gap + 0.95, 0.9)
        major = minor * (1.38 + 0.005 * self.annulus_circumference_mm)
        return math.pi * minor * major

    def to_vtk_points(self) -> list[tuple[float, float, float]]:
        """Ring of points for VTK export hook."""
        n = 64
        r = self.annulus_radius_mm
        pts = []
        for i in range(n):
            theta = 2.0 * math.pi * i / n
            x = r * math.cos(theta)
            y = self.ap_diameter_mm / 2.0 * math.sin(theta)
            z = 0.0
            pts.append((x, y, z))
        return pts
