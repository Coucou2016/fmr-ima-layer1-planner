"""Runtime helpers: full-train response fit, contact_fraction for design points.

Honesty
-------
- Full-train params are for exploratory ranking under ``response_path=fitted_response``.
- Fold-wise LOO CV (``analysis/fit_response_model.py``) remains the honesty path.
- ``contact_fraction`` for off-table design points is Dryad-neighbor interpolation
  (auxiliary feature), not a new SPH chamber measurement.
"""

from __future__ import annotationsimport jsonfrom pathlib import Pathfrom typing import Any, Optionalimport numpy as npimport yamlfrom models.response_model import (    ResponseModelParams,    fit_response_models,    predict_case,)ROOT = Path(__file__).resolve().parents[1]
PARAMS_PATH = ROOT / "results" / "output" / "response_model" / "full_train_params.json"

# Dryad / table-backed contact anchors (peak systole).
_CONTACT_ANCHORS: dict[str, list[tuple[float, float]]] = {
    "IMA-AP": [(30.0, 0.053737), (50.0, 0.131656), (70.0, 0.225696)],
    "IMA-CS": [(14.0, 0.080362), (18.0, 0.086712), (22.0, 0.099414)],
}
_PATHOLOGY_CONTACT = 0.011724


def estimate_contact_fraction(
    device: Optional[str],
    shortening_pct: Optional[float],
    *,
    catalog: Optional[list[dict[str, Any]]] = None,
) -> float:
    """Interpolate Dryad contact_fraction by device family and shortening.

    Pathology → published/Dryad pathology contact. Unknown device → pathology.
    Outside anchor range → linear clamp to nearest endpoint.
    """
    _ = catalog
    if device is None or shortening_pct is None:
        return float(_PATHOLOGY_CONTACT)
    fam = "IMA-AP" if str(device).upper().startswith("IMA-AP") else (
        "IMA-CS" if str(device).upper().startswith("IMA-CS") else None
    )
    if fam is None:
        return float(_PATHOLOGY_CONTACT)
    anchors = _CONTACT_ANCHORS[fam]
    xs = np.array([a[0] for a in anchors], dtype=float)
    ys = np.array([a[1] for a in anchors], dtype=float)
    s = float(shortening_pct)
    if s <= xs[0]:
        return float(ys[0])
    if s >= xs[-1]:
        return float(ys[-1])
    return float(np.interp(s, xs, ys))


def load_peak_systole_cases() -> list[dict[str, Any]]:
    """Load Galili peak-systole rows for full-train fit (table ± Dryad)."""
    from tools.loo_evaluate import load_case_catalog

    cases, _note = load_case_catalog()
    return [
        c
        for c in cases
        if c.get("cardiac_phase", "peak_systole") == "peak_systole"
        and c.get("roa_mm2") is not None
        and c.get("regurgitation_pct") is not None
    ]


def fit_full_train_params(
    *,
    ridge_roa: float = 0.05,
    ridge_leak: float = 0.05,
) -> ResponseModelParams:
    cases = load_peak_systole_cases()
    if len(cases) < 3:
        raise RuntimeError("Need ≥3 Galili peak-systole cases for full-train fit")
    return fit_response_models(cases, ridge_roa=ridge_roa, ridge_leak=ridge_leak)


def write_full_train_params(
    params: Optional[ResponseModelParams] = None,
    path: Path = PARAMS_PATH,
) -> Path:
    p = params or fit_full_train_params()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "role": "full_train_response_model_for_ranking",
        "honesty": (
            "Fitted on all available Galili peak-systole cases for exploratory "
            "ranking when response_path=fitted_response. Not a substitute for "
            "fold-wise LOO CV honesty metrics."
        ),
        "params": p.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_full_train_params(path: Path = PARAMS_PATH) -> ResponseModelParams:
    if not path.is_file():
        params = fit_full_train_params()
        write_full_train_params(params, path)
        return params
    raw = json.loads(path.read_text(encoding="utf-8"))
    d = raw.get("params") or raw
    return ResponseModelParams(
        roa_coef=list(d["roa_coef"]),
        leak_coef=list(d["leak_coef"]),
        train_ids=list(d.get("train_ids") or []),
        ridge_roa=float(d.get("ridge_roa", 0.05)),
        ridge_leak=float(d.get("ridge_leak", 0.05)),
        kappa_overshort=float(d.get("kappa_overshort", 1.85)),
    )


def case_dict_from_design(
    *,
    device: Optional[str],
    shortening_pct: Optional[float],
    ap_diameter_mm: float,
    annulus_circumference_mm: float,
    contact_fraction: float,
) -> dict[str, Any]:
    return {
        "id": "design_point",
        "device": device,
        "shortening_pct": shortening_pct,
        "ap_diameter_mm": ap_diameter_mm,
        "annulus_circumference_mm": annulus_circumference_mm,
        "contact_fraction": contact_fraction,
        "cardiac_phase": "peak_systole",
    }


def predict_design(
    params: ResponseModelParams,
    case: dict[str, Any],
) -> dict[str, Any]:
    return predict_case(params, case)


def default_response_path(design_space: Optional[dict[str, Any]] = None) -> str:
    if design_space is None:
        cfg_path = ROOT / "configs" / "design_space.yaml"
        with open(cfg_path, encoding="utf-8") as f:
            design_space = yaml.safe_load(f)
    path = str(
        (design_space or {}).get("response_path")
        or (design_space or {}).get("response", {}).get("path")
        or "fitted_response"
    ).strip()
    if path not in {"fitted_response", "rule_based_proxy", "hybrid_ap_extreme"}:
        raise ValueError(f"Unknown response_path: {path}")
    return path
