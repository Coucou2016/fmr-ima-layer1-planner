"""Tests for FMR surrogate pipeline."""



import sys

from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))



import pytest



from models.devices import IMA_CS, IMA_AP

from models.pathology import make_papillary_mesh, apply_papillary_pathology, pathology_severity

from analysis.roa import compute_roa_from_contacts

from sph.hemodynamics import SPHSurrogate, regurgitation_fraction_from_physics

from models.heart_geometry import HeartGeometry

from simulation.run_case import run_fea_surrogate

from simulation.roa_surrogate import pipeline_roa_mm2, contacts_from_fea, stable_case_seed





def test_papillary_pathology_fraction():

    elems = make_papillary_mesh(200)

    path = apply_papillary_pathology(elems, posterior_fraction_passive=0.44)

    assert 0.40 <= pathology_severity(path) <= 0.48





def test_ima_cs_annulus_22pct():

    g = IMA_CS(bridge_shortening_pct=22).apply()

    assert abs(g.annulus_circumference_mm - 115.0) < 0.2





def test_ima_ap_ap_diameters():

    g50 = IMA_AP(shortening_pct=50).apply()

    g70 = IMA_AP(shortening_pct=70).apply()

    assert abs(g50.ap_diameter_mm - 34.4) < 0.1

    assert abs(g70.ap_diameter_mm - 14.3) < 0.2





def test_roa_from_contacts_positive():

    roa, _ = compute_roa_from_contacts([])

    assert roa > 0





def test_sph_physics_anchors():

    sph = SPHSurrogate(29000)

    g_path = HeartGeometry()

    elems = apply_papillary_pathology(make_papillary_mesh(200), posterior_fraction_passive=0.44)

    fea_path = run_fea_surrogate("pathology", g_path, elems, None)

    roa_path = pipeline_roa_mm2(g_path, fea_path, None, case_id="pathology", seed=42)

    r_path = sph.run("pathology", g_path, roa_path, coaptation_gap_mm=fea_path.coaptation_gap_mm)



    g_cs = IMA_CS(bridge_shortening_pct=22).apply()

    dev_cs = IMA_CS(bridge_shortening_pct=22)

    fea_cs = run_fea_surrogate("ima_cs_22", g_cs, elems, dev_cs)

    roa_cs = pipeline_roa_mm2(g_cs, fea_cs, dev_cs, case_id="ima_cs_22", seed=42)

    r_cs = sph.run("ima_cs_22", g_cs, roa_cs, coaptation_gap_mm=fea_cs.coaptation_gap_mm)



    g_ap = IMA_AP(shortening_pct=50).apply()

    dev_ap = IMA_AP(shortening_pct=50)

    fea_ap = run_fea_surrogate("ima_ap_50", g_ap, elems, dev_ap)

    roa_ap = pipeline_roa_mm2(g_ap, fea_ap, dev_ap, case_id="ima_ap_50", seed=42)

    r_ap = sph.run("ima_ap_50", g_ap, roa_ap, coaptation_gap_mm=fea_ap.coaptation_gap_mm)



    assert abs(r_path.regurgitation_pct - 5.26) < 0.2

    assert abs(r_cs.regurgitation_pct - 0.29) < 0.08

    assert abs(r_ap.regurgitation_pct - 0.08) < 0.08





def test_ima_ap_70_worse_than_50():

    sph = SPHSurrogate()

    g50 = IMA_AP(shortening_pct=50).apply()

    g70 = IMA_AP(shortening_pct=70).apply()

    elems = apply_papillary_pathology(make_papillary_mesh(200), posterior_fraction_passive=0.44)

    fea50 = run_fea_surrogate("ima_ap_50", g50, elems, IMA_AP(50))

    fea70 = run_fea_surrogate("ima_ap_70", g70, elems, IMA_AP(70))

    roa50 = pipeline_roa_mm2(g50, fea50, IMA_AP(50), case_id="ima_ap_50", seed=42)

    roa70 = pipeline_roa_mm2(g70, fea70, IMA_AP(70), case_id="ima_ap_70", seed=42)

    r50 = sph.run("ima_ap_50", g50, roa50, coaptation_gap_mm=fea50.coaptation_gap_mm)

    r70 = sph.run(

        "ima_ap_70",

        g70,

        roa70,

        coaptation_gap_mm=fea70.coaptation_gap_mm,

        commissural_leak=True,

    )

    assert r70.regurgitation_pct > r50.regurgitation_pct





def test_commissural_mechanism_not_arbitrary_multiplier():

    g_leak = HeartGeometry(ap_diameter_mm=14.3)

    g_ok = HeartGeometry(ap_diameter_mm=34.4)

    frac_leak = regurgitation_fraction_from_physics(g_leak, 30.0, 2.0, commissural_leak=True)

    frac_no = regurgitation_fraction_from_physics(g_ok, 30.0, 1.0, commissural_leak=False)

    assert frac_leak > frac_no * 1.25





def test_contacts_from_fea_reproducible():

    elems = make_papillary_mesh(50)

    g = HeartGeometry()

    fea = run_fea_surrogate("pathology", g, elems, None)

    seed = stable_case_seed(42, "pathology")

    c1 = contacts_from_fea(g, fea, seed=seed)

    c2 = contacts_from_fea(g, fea, seed=seed)

    assert len(c1) == len(c2)

    assert c1[0].x == c2[0].x





def test_run_pipeline_integration():

    from run_pipeline import run_all



    metrics = run_all(export_fea=False, seed=42)

    assert len(metrics) == 7

    by_id = {m.case_id: m for m in metrics}

    assert abs(by_id["pathology"].regurgitation_pct - 5.26) < 0.15

    assert abs(by_id["ima_cs_22"].regurgitation_pct - 0.29) < 0.05

    assert abs(by_id["ima_ap_50"].regurgitation_pct - 0.08) < 0.05

    assert by_id["ima_ap_70"].regurgitation_pct > by_id["ima_ap_50"].regurgitation_pct


