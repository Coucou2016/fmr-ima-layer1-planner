"""Posterior papillary muscle pathology (LHHM-inspired element state change)."""

from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class PapillaryElement:
    id: int
    region: str  # "anterior" | "posterior"
    active: bool
    activation_threshold_mV: float = 20.0


def make_papillary_mesh(n_elements: int = 200) -> List[PapillaryElement]:
    """Synthetic papillary muscle element list."""
    n_post = n_elements // 2
    elements = []
    for i in range(n_elements):
        region = "posterior" if i < n_post else "anterior"
        elements.append(
            PapillaryElement(
                id=i,
                region=region,
                active=True,
                activation_threshold_mV=20.0,
            )
        )
    return elements


def apply_papillary_pathology(
    elements: List[PapillaryElement],
    posterior_fraction_passive: float = 0.44,
    passive_threshold_mV: float = 100.0,
    sa_threshold_mV: float = 20.0,
) -> List[PapillaryElement]:
    """
    Convert fraction of posterior PM elements from active to passive.

    Matches paper: 44% posterior elements, threshold 100 mV vs SA 20 mV.
    """
    posterior = [e for e in elements if e.region == "posterior"]
    n_passive = int(round(len(posterior) * posterior_fraction_passive))
    rng = np.random.default_rng(42)
    passive_ids = set(rng.choice([e.id for e in posterior], size=n_passive, replace=False))

    out = []
    for e in elements:
        if e.id in passive_ids:
            out.append(
                PapillaryElement(
                    id=e.id,
                    region=e.region,
                    active=False,
                    activation_threshold_mV=passive_threshold_mV,
                )
            )
        else:
            out.append(
                PapillaryElement(
                    id=e.id,
                    region=e.region,
                    active=True,
                    activation_threshold_mV=sa_threshold_mV,
                )
            )
    return out


def pathology_severity(elements: List[PapillaryElement]) -> float:
    """Fraction of posterior elements that are passive (0–1)."""
    post = [e for e in elements if e.region == "posterior"]
    if not post:
        return 0.0
    return sum(1 for e in post if not e.active) / len(post)
