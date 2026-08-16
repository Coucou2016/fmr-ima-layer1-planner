"""Material parameter sets for NiTi device and ePTFE suture."""

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class NiTiHyperelastic:
    """14-parameter hyperelastic NiTi model (surrogate stub for Abaqus UMAT)."""

    params: Sequence[float] = field(
        default_factory=lambda: [0.0] * 14
    )
    name: str = "NiTi_14param"

    def strain_energy(self, stretch: float) -> float:
        """Simplified neo-Hookean-like surrogate for demo."""
        mu, lam = 50.0, 100.0  # MPa-scale placeholders
        J = stretch**3
        I1 = stretch**2 + 2.0 / stretch
        return (mu / 2.0) * (I1 - 3.0) - mu * (J - 1.0) + (lam / 2.0) * (J - 1.0) ** 2


@dataclass
class EPTFESuture:
    """ePTFE suture for IMA-AP."""

    cross_section_mm2: float = 0.074
    young_modulus_mpa: float = 500.0
    name: str = "ePTFE"

    def axial_stiffness_n_per_mm(self) -> float:
        return self.young_modulus_mpa * self.cross_section_mm2
