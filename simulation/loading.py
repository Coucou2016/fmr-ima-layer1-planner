"""LV/LA pressure loading with phase offset."""

from dataclasses import dataclass
import numpy as np


@dataclass
class PressureLoading:
    """Biphasic LV/LA pressure curves (surrogate)."""

    duration_ms: float = 800.0
    lv_la_offset_ms: float = 50.0
    peak_systole_fraction: float = 0.75
    lv_peak_kpa: float = 16.0
    la_peak_kpa: float = 2.0

    def time_series(self, n_steps: int = 100) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        t = np.linspace(0, self.duration_ms, n_steps)
        # Simplified sinusoidal cardiac cycle
        phase = 2 * np.pi * t / self.duration_ms
        lv = self.lv_peak_kpa * np.maximum(0, np.sin(phase - np.pi / 2))
        la = self.la_peak_kpa * np.maximum(
            0, np.sin(phase - np.pi / 2 + 2 * np.pi * self.lv_la_offset_ms / self.duration_ms)
        )
        return t, lv, la

    def peak_systole_index(self, n_steps: int = 100) -> int:
        contraction_end = int(n_steps * self.peak_systole_fraction)
        return max(0, contraction_end - 1)
