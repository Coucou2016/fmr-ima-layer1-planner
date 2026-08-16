"""Regurgitant orifice area (ROA) from contact node forces + geometric search.

Matlab-style auto identification: cluster high-contact nodes, fit minimum area ellipse.
"""

from dataclasses import dataclass
import numpy as np
from typing import List, Tuple


@dataclass
class ContactNode:
    x: float
    y: float
    z: float
    force_n: float


def _fit_ellipse_area(points: np.ndarray) -> float:
    if len(points) < 3:
        return 0.0
    cov = np.cov(points[:, :2].T)
    eigvals = np.linalg.eigvalsh(cov)
    a, b = np.sqrt(np.maximum(eigvals, 1e-6))
    return float(np.pi * a * b)


def compute_roa_from_contacts(
    nodes: List[ContactNode],
    force_threshold_n: float = 0.1,
) -> Tuple[float, np.ndarray]:
    """
    Returns (ROA_mm2, centroid_xyz).

    Demo: synthetic nodes if empty; otherwise Matlab-style clustering.
    """
    if not nodes:
        # Synthetic demo annulus leak patch
        rng = np.random.default_rng(7)
        n = 40
        angles = rng.uniform(0, 2 * np.pi, n)
        r = 2.5 + rng.normal(0, 0.3, n)
        xs = r * np.cos(angles)
        ys = r * np.sin(angles)
        forces = rng.uniform(0.2, 1.5, n)
        nodes = [
            ContactNode(x=float(x), y=float(y), z=0.0, force_n=float(f))
            for x, y, f in zip(xs, ys, forces)
        ]

    active = [n for n in nodes if n.force_n >= force_threshold_n]
    if len(active) < 3:
        return 0.0, np.zeros(3)

    pts = np.array([[n.x, n.y, n.z] for n in active])
    forces = np.array([n.force_n for n in active])
    # Weighted centroid
    centroid = np.average(pts, axis=0, weights=forces)
    # Geometric search: expand radius until 90% contact captured
    dist = np.linalg.norm(pts[:, :2] - centroid[:2], axis=1)
    for q in np.linspace(0.5, 3.0, 30):
        mask = dist <= np.quantile(dist, q)
        if mask.sum() >= 3:
            area = _fit_ellipse_area(pts[mask])
            if area > 0:
                return area, centroid
    return _fit_ellipse_area(pts), centroid
