"""Aggregate case metrics for tables and validation."""

from dataclasses import dataclass, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class CaseMetrics:
    case_id: str
    device: Optional[str]
    shortening_pct: Optional[float]
    annulus_circumference_mm: float
    ap_diameter_mm: float
    roa_mm2: float
    regurgitation_pct: float
    pathology_severity: float
    max_principal_strain: float
    reference_regurgitation_pct: Optional[float] = None
    jet_location: Optional[str] = None
    central_roa_mm2: Optional[float] = None
    commissural_roa_mm2: Optional[float] = None
    ap_reduction_mm: Optional[float] = None
    ap_reduction_pct: Optional[float] = None
    physics_regurgitation_pct: Optional[float] = None
    cs_lcx_mm: Optional[float] = None
    niti_alternating_strain_pct: Optional[float] = None
    mapping_mode: Optional[str] = None

    def error_vs_reference_pct(self) -> Optional[float]:
        if self.reference_regurgitation_pct is None:
            return None
        return abs(self.regurgitation_pct - self.reference_regurgitation_pct)

    def to_dict(self):
        return asdict(self)


def load_reference_targets(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_metrics(rows: list[CaseMetrics], out_path: Path) -> None:
    import pandas as pd

    df = pd.DataFrame([r.to_dict() for r in rows])
    df.to_csv(out_path, index=False)
