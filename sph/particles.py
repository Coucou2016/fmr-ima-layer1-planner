"""Particle seeding for SPH surrogate (~29k particles)."""

import numpy as np


def seed_particles(n_particles: int = 29000, seed: int = 0) -> np.ndarray:
    """LV/aorta/LA volume fractions as random particle labels (demo)."""
    rng = np.random.default_rng(seed)
    # Positions in unit cube (not used in reduced-order model)
    pos = rng.random((n_particles, 3))
    return pos


def piston_volume_change(t: float, amplitude: float = 0.15) -> float:
    """Systolic piston compression fraction."""
    return amplitude * max(0.0, np.sin(2 * np.pi * t))
