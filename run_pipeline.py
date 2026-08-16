#!/usr/bin/env python3

"""

FMR computational biomechanics demo pipeline.



Compares IMA-CS vs IMA-AP for functional mitral regurgitation (surrogate FEA + SPH).

"""



from __future__ import annotations



import argparse

import json

import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))



import numpy as np

import yaml



from models.heart_geometry import HeartGeometry

from models.pathology import make_papillary_mesh, apply_papillary_pathology

from models.devices import IMA_CS, IMA_AP

from simulation.loading import PressureLoading

from simulation.run_case import run_fea_surrogate

from simulation.fea_export import export_inp_stub, export_vtk_annulus

from simulation.roa_surrogate import pipeline_roa_mm2, niti_bridge_strain

from simulation.calibration import (
    load_surrogate_calibration,
    physics_regurgitation_by_case,
    write_calibration_report,
)
from analysis.exports import export_case_artifacts, export_paper_comparison_table

from sph.hemodynamics import SPHSurrogate

from analysis.metrics import CaseMetrics, collect_metrics, load_reference_targets

from analysis.plots import plot_regurgitation_bars, plot_comparison

from analysis.jet import classify_jet





def _load_yaml(path: Path) -> dict:

    with open(path, encoding="utf-8") as f:

        return yaml.safe_load(f)





def _reference_map(ref: dict) -> dict[str, float | None]:

    out = {}

    for c in ref.get("cases", []):

        pct = c.get("regurgitation_pct")

        out[c["id"]] = float(pct) if pct is not None else None

    return out





def build_cases() -> list[dict]:

    """All simulation cases: pathology + IMA-CS + IMA-AP."""

    cases = [{"id": "pathology", "device": None, "shortening_pct": None}]

    cs_cfg = _load_yaml(ROOT / "configs" / "ima_cs_cases.yaml")

    for c in cs_cfg["cases"]:

        cases.append(

            {

                "id": c["id"],

                "device": "IMA-CS",

                "shortening_pct": c["bridge_shortening_pct"],

            }

        )

    ap_cfg = _load_yaml(ROOT / "configs" / "ima_ap_cases.yaml")

    for c in ap_cfg["cases"]:

        cases.append(

            {

                "id": c["id"],

                "device": "IMA-AP",

                "shortening_pct": c["shortening_pct"],

            }

        )

    return cases





def run_all(export_fea: bool = True, seed: int = 42) -> list[CaseMetrics]:

    pathology_cfg = _load_yaml(ROOT / "configs" / "pathology.yaml")

    ref = load_reference_targets(ROOT / "results" / "reference_targets.json")

    ref_pct = _reference_map(ref)

    cal = load_surrogate_calibration()



    elements = make_papillary_mesh(200)

    elements = apply_papillary_pathology(

        elements,

        posterior_fraction_passive=pathology_cfg["papillary_muscle"]["posterior_fraction_passive"],

        passive_threshold_mV=pathology_cfg["papillary_muscle"]["active_threshold_mV"],

        sa_threshold_mV=pathology_cfg["papillary_muscle"]["sa_threshold_mV"],

    )



    loading = PressureLoading(

        lv_la_offset_ms=pathology_cfg["loading"]["lv_la_phase_offset_ms"],

        peak_systole_fraction=pathology_cfg["loading"]["peak_systole_fraction"],

    )

    _ = loading.time_series()  # ensure loading builds



    sph = SPHSurrogate(

        n_particles=pathology_cfg["sph"]["n_particles"],

        calibration=cal,

    )

    results_dir = ROOT / "results" / "output"

    export_dir = results_dir / "fea_export"

    results_dir.mkdir(parents=True, exist_ok=True)

    if export_fea:

        export_dir.mkdir(parents=True, exist_ok=True)



    metrics: list[CaseMetrics] = []
    coaptation_gaps: dict[str, float] = {}
    geometries: dict[str, HeartGeometry] = {}
    commissural_flags: dict[str, bool] = {}

    baseline = HeartGeometry()

    for case in build_cases():

        case_id = case["id"]

        device_obj = None

        geom = baseline

        commissural = False



        if case["device"] == "IMA-CS":

            device_obj = IMA_CS(bridge_shortening_pct=case["shortening_pct"])

            geom = device_obj.apply()

        elif case["device"] == "IMA-AP":

            device_obj = IMA_AP(shortening_pct=case["shortening_pct"])

            geom = device_obj.apply()

            commissural = device_obj.commissural_leak_risk()



        fea = run_fea_surrogate(case_id, geom, elements, device_obj)

        if isinstance(device_obj, IMA_CS):

            fea.max_principal_strain = max(

                fea.max_principal_strain,

                niti_bridge_strain(device_obj.bridge_shortening_pct) * 0.85,

            )



        roa = pipeline_roa_mm2(
            geom, fea, device_obj, case_id=case_id, seed=seed, calibration=cal
        )

        coaptation_gaps[case_id] = fea.coaptation_gap_mm
        geometries[case_id] = geom
        commissural_flags[case_id] = commissural

        if export_fea:
            export_case_artifacts(
                case_id=case_id,
                geometry=geom,
                fea=fea,
                device=device_obj,
                roa_mm2=roa,
                output_dir=results_dir,
                seed=seed,
            )

        reg = sph.run(

            case_id,

            geom,

            roa,

            coaptation_gap_mm=fea.coaptation_gap_mm,

            commissural_leak=commissural,

        )



        if export_fea:

            export_inp_stub(export_dir / f"{case_id}.inp", case_id, geom)

            export_vtk_annulus(export_dir / f"{case_id}_annulus.vtk", geom)



        jet = classify_jet(device_obj, geom, roa_mm2=roa)
        ap_red_mm = 0.0
        ap_red_pct = 0.0
        cs_lcx = None
        niti_alt = None
        if isinstance(device_obj, IMA_AP):
            ap_red_mm = device_obj.ap_reduction_mm()
            ap_red_pct = device_obj.ap_reduction_pct()
        elif isinstance(device_obj, IMA_CS):
            ap_red_mm = device_obj.ap_reduction_mm()
            ap_red_pct = device_obj.ap_reduction_pct()
            cs_lcx = device_obj.cs_lcx_mm()
            niti_alt = device_obj.niti_alternating_strain_pct()

        metrics.append(

            CaseMetrics(

                case_id=case_id,

                device=case["device"],

                shortening_pct=case["shortening_pct"],

                annulus_circumference_mm=geom.annulus_circumference_mm,

                ap_diameter_mm=geom.ap_diameter_mm,

                roa_mm2=roa,

                regurgitation_pct=reg.regurgitation_pct,

                pathology_severity=fea.pathology_severity,

                max_principal_strain=fea.max_principal_strain,

                reference_regurgitation_pct=ref_pct.get(case_id),

                jet_location=jet.location,

                central_roa_mm2=jet.central_roa_mm2,

                commissural_roa_mm2=jet.commissural_roa_mm2,

                ap_reduction_mm=ap_red_mm,

                ap_reduction_pct=ap_red_pct,

                cs_lcx_mm=cs_lcx,

                niti_alternating_strain_pct=niti_alt,

                mapping_mode="galili",

            )

        )



    physics_by_case = physics_regurgitation_by_case(
        metrics,
        coaptation_gaps=coaptation_gaps,
        geometries=geometries,
        commissural=commissural_flags,
        calibration=cal,
    )
    for m in metrics:
        if m.case_id in physics_by_case:
            m.physics_regurgitation_pct = physics_by_case[m.case_id] * 100.0
    collect_metrics(metrics, results_dir / "case_metrics.csv")
    with open(results_dir / "case_metrics.json", "w", encoding="utf-8") as f:
        json.dump([m.to_dict() for m in metrics], f, indent=2)
    write_calibration_report(
        metrics,
        ref,
        cal,
        results_dir / "calibration_report.json",
        physics_by_case=physics_by_case,
    )
    export_paper_comparison_table(metrics, results_dir / "paper_comparison_table.csv")



    plot_regurgitation_bars(metrics, results_dir / "regurgitation_comparison.png")

    plot_comparison(metrics, results_dir / "regurgitation_vs_shortening.png")



    _print_summary(metrics)

    return metrics





def _print_summary(metrics: list[CaseMetrics]) -> None:

    print("\n=== FMR IMA Pipeline Results ===\n")

    print(f"{'Case':<14} {'Regurg %':>10} {'Ref %':>10} {'ROA mm2':>10} {'Annulus':>10} {'AP':>8}")

    print("-" * 70)

    for m in metrics:

        ref = f"{m.reference_regurgitation_pct:.2f}" if m.reference_regurgitation_pct is not None else "—"

        print(

            f"{m.case_id:<14} {m.regurgitation_pct:>10.2f} {ref:>10} "

            f"{m.roa_mm2:>10.2f} {m.annulus_circumference_mm:>10.1f} {m.ap_diameter_mm:>8.1f}"

        )

    key = {m.case_id: m for m in metrics}

    if "ima_ap_70" in key and "ima_ap_50" in key:

        worse = key["ima_ap_70"].regurgitation_pct > key["ima_ap_50"].regurgitation_pct

        print(f"\nIMA-AP 70% worse than 50%: {worse}")

    print(f"\nOutputs: {ROOT / 'results' / 'output'}")





def main():

    parser = argparse.ArgumentParser(description="FMR IMA computational biomechanics pipeline")

    parser.add_argument("--no-export", action="store_true", help="Skip INP/VTK export")

    parser.add_argument("--seed", type=int, default=42, help="RNG seed for contact patch synthesis")

    parser.add_argument("--sweep", action="store_true", help="Continuous design-space sweep (physics)")

    parser.add_argument("--plan", action="store_true", help="Constrained preoperative planner")

    parser.add_argument(
        "--paper",
        action="store_true",
        help="Sweep + planner + paper tables/figures (physics regurgitation)",
    )

    args = parser.parse_args()

    np.random.seed(args.seed)

    metrics = run_all(export_fea=not args.no_export, seed=args.seed)

    if args.sweep or args.plan or args.paper:
        from analysis.design_sweep import run_sweep
        from analysis.planner import run_planner
        from analysis.paper_tables import export_paper_bundle

        points = run_sweep(seed=args.seed)
        rec = None
        if args.plan or args.paper:
            rec = run_planner(points=points, seed=args.seed)
            rec_pt = rec.get("recommended") or {}
            if rec_pt:
                ns = rec_pt.get("n_sutures") or 0
                suture_note = f" dual" if rec_pt.get("device") == "IMA-AP" and ns >= 2 else ""
                print(
                    "\nPlanner: "
                    f"{rec_pt.get('device')}{suture_note} {rec_pt.get('shortening_pct')}%  "
                    f"AP reduction {rec_pt.get('ap_reduction_pct'):.2f}%  "
                    f"jet={rec_pt.get('jet_location')}  "
                    f"physics regurg {rec_pt.get('physics_regurgitation_pct'):.3f}%"
                )
        if args.paper:
            physics_map = {m.case_id: (m.physics_regurgitation_pct or 0) / 100.0 for m in metrics}
            export_paper_bundle(
                sweep_points=points,
                recommendation=rec,
                pipeline_metrics=metrics,
                physics_by_case=physics_map,
                seed=args.seed,
            )
            print(f"Paper tables: {ROOT / 'results' / 'output' / 'paper_tables'}")
            print(f"Paper figures: {ROOT / 'results' / 'output' / 'paper_figures'}")

    return metrics





if __name__ == "__main__":

    main()


