"""Continuous IMA design-space scan (Innovation E).

Default grids (configs/design_space.yaml):
- IMA-AP suture shortening 10–70% step 5%
- IMA-CS bridge shortening 10–25% step 2%
- Optional dual-suture IMA-AP series

Main figures use physics regurgitation (no YAML blend).

CLI:
    python -m analysis.design_sweep
    python -m analysis.design_sweep --paper --seed 42
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.evaluate import (
    DesignPoint,
    apply_constraints,
    evaluate_design_point,
    load_design_space,
    shortening_grid,
)
from models.pathology import apply_papillary_pathology, make_papillary_mesh
from simulation.calibration import load_surrogate_calibration


def _iter_jobs(design_space: dict[str, Any], mappings: Iterable[str]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for mapping in mappings:
        if design_space.get("sweep", {}).get("include_pathology", True):
            jobs.append(
                {
                    "device_type": None,
                    "shortening_pct": None,
                    "mapping_mode": mapping,
                    "n_sutures": 0,
                }
            )
        for pct in shortening_grid("IMA-CS", design_space):
            jobs.append(
                {
                    "device_type": "IMA-CS",
                    "shortening_pct": pct,
                    "mapping_mode": mapping,
                    "n_sutures": 0,
                }
            )
        for pct in shortening_grid("IMA-AP", design_space):
            jobs.append(
                {
                    "device_type": "IMA-AP",
                    "shortening_pct": pct,
                    "mapping_mode": mapping,
                    "n_sutures": 1,
                }
            )
        dual_cfg = design_space.get("dual_suture", {})
        if dual_cfg.get("enabled", False):
            for pct in shortening_grid("IMA-AP-dual", design_space):
                jobs.append(
                    {
                        "device_type": "IMA-AP-dual",
                        "shortening_pct": pct,
                        "mapping_mode": mapping,
                        "n_sutures": 2,
                    }
                )
    return jobs


def run_sweep(
    *,
    mappings: Optional[list[str]] = None,
    seed: int = 42,
    output_dir: Optional[Path] = None,
    design_space: Optional[dict[str, Any]] = None,
    apply_planner_constraints: bool = True,
    write_outputs: bool = True,
) -> list[DesignPoint]:
    cfg = design_space or load_design_space()
    maps = mappings or list(cfg.get("sweep", {}).get("mappings", ["galili", "clinical"]))
    cal = load_surrogate_calibration()
    elements = apply_papillary_pathology(
        make_papillary_mesh(200), posterior_fraction_passive=0.44
    )
    points: list[DesignPoint] = []
    for job in _iter_jobs(cfg, maps):
        pt = evaluate_design_point(
            device_type=job["device_type"],
            shortening_pct=job["shortening_pct"],
            mapping_mode=job["mapping_mode"],
            n_sutures=job["n_sutures"],
            elements=elements,
            calibration=cal,
            design_space=cfg,
            seed=seed,
            blend=False,
        )
        if apply_planner_constraints:
            apply_constraints(pt, cfg)
        points.append(pt)

    if write_outputs:
        out = output_dir or (ROOT / "results" / "output" / "sweep")
        out.mkdir(parents=True, exist_ok=True)
        _write_sweep_csv(points, out / "design_sweep.csv")
        (out / "design_sweep.json").write_text(
            json.dumps([p.to_dict() for p in points], indent=2),
            encoding="utf-8",
        )
    return points


def _write_sweep_csv(points: list[DesignPoint], path: Path) -> None:
    if not points:
        return
    rows = [p.to_dict() for p in points]
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main(argv: Optional[list[str]] = None) -> list[DesignPoint]:
    parser = argparse.ArgumentParser(description="FMR IMA continuous design-space sweep")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--mapping",
        choices=["clinical", "galili", "both"],
        default="both",
        help="Which AP-mapping mode(s) to scan",
    )
    parser.add_argument("--paper", action="store_true", help="Also write planner + paper tables/figures")
    args = parser.parse_args(argv)

    mappings = ["galili", "clinical"] if args.mapping == "both" else [args.mapping]
    points = run_sweep(mappings=mappings, seed=args.seed)
    print(f"Sweep points: {len(points)}")
    print(f"Wrote: {ROOT / 'results' / 'output' / 'sweep'}")

    if args.paper:
        from analysis.planner import run_planner
        from analysis.paper_tables import export_paper_bundle

        rec = run_planner(points=points, seed=args.seed)
        export_paper_bundle(sweep_points=points, recommendation=rec, seed=args.seed)
        print(f"Paper artifacts: {ROOT / 'results' / 'output' / 'paper_tables'}")
    return points


if __name__ == "__main__":
    main()
