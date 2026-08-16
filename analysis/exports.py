"""Export contact maps, strain summaries, and paper-style comparison tables."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Optional

from analysis.metrics import CaseMetrics
from analysis.roa import ContactNode
from models.devices import IMA_CS
from simulation.roa_surrogate import contacts_from_fea, niti_bridge_strain, stable_case_seed
from simulation.run_case import FEASurrogateResult, run_fea_surrogate


def export_contact_map_csv(
    path: Path,
    contacts: List[ContactNode],
    *,
    case_id: str,
    roa_mm2: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "roa_mm2", "x_mm", "y_mm", "z_mm", "force_n"])
        for n in contacts:
            w.writerow([case_id, f"{roa_mm2:.4f}", f"{n.x:.4f}", f"{n.y:.4f}", f"{n.z:.4f}", f"{n.force_n:.4f}"])


def export_strain_summary_json(
    path: Path,
    *,
    case_id: str,
    fea: FEASurrogateResult,
    device: Optional[object],
) -> None:
    payload = {
        "case_id": case_id,
        "max_principal_strain": fea.max_principal_strain,
        "coaptation_gap_mm": fea.coaptation_gap_mm,
        "pathology_severity": fea.pathology_severity,
        "contact_force_max_n": fea.contact_force_max_n,
    }
    if isinstance(device, IMA_CS):
        payload["niti_bridge_engineering_strain"] = niti_bridge_strain(device.bridge_shortening_pct)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_paper_comparison_table(metrics: List[CaseMetrics], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "case_id",
                "device",
                "shortening_pct",
                "annulus_mm",
                "ap_mm",
                "roa_mm2",
                "regurgitation_pct_sim",
                "regurgitation_pct_ref",
                "regurgitation_residual_pct",
            ]
        )
        for m in metrics:
            ref = m.reference_regurgitation_pct
            resid = m.error_vs_reference_pct()
            w.writerow(
                [
                    m.case_id,
                    m.device or "",
                    m.shortening_pct if m.shortening_pct is not None else "",
                    f"{m.annulus_circumference_mm:.2f}",
                    f"{m.ap_diameter_mm:.2f}",
                    f"{m.roa_mm2:.3f}",
                    f"{m.regurgitation_pct:.4f}",
                    f"{ref:.4f}" if ref is not None else "",
                    f"{resid:.4f}" if resid is not None else "",
                ]
            )


def export_case_artifacts(
    *,
    case_id: str,
    geometry,
    fea: FEASurrogateResult,
    device: Optional[object],
    roa_mm2: float,
    output_dir: Path,
    seed: int,
) -> None:
    contacts = contacts_from_fea(
        geometry, fea, device, seed=stable_case_seed(seed, case_id)
    )
    export_contact_map_csv(
        output_dir / "contacts" / f"{case_id}_contact_map.csv",
        contacts,
        case_id=case_id,
        roa_mm2=roa_mm2,
    )
    export_strain_summary_json(
        output_dir / "strain" / f"{case_id}_strain.json",
        case_id=case_id,
        fea=fea,
        device=device,
    )
