"""Fold-wise phenomenological response models for Galili peak-systole cases.

Honesty
-------
- AP diameter is a **literature-defined geometry INPUT** (``ap_role:
  literature_mapping_input``), not a predicted output of these fits.
- ``f_ROA`` and ``f_leak`` are low-order algebraic fits on n≈6 train folds —
  exploratory diagnostics, not patient-level external validation.
- Dryad ``contact_fraction`` enters as a model feature (not provenance-only).
- Overshoot prior ``kappa_overshort`` is a documented phenomenological constant
  (Galili non-monotonic ROA rebound beyond ~AP50), not estimated from the
  held-out case.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import numpy as np

DISEASE_AP_MM = 26.1
UNDEFORMED_ANNULUS_MM = 118.5
# Soft optimum ΔAP near Galili IMA-AP 50% (26.1−15.9=10.2 mm).
OVERSHORT_DELTA_AP_REF_MM = 10.2
PATHOLOGY_ROA_REF = 172.8
# Fixed prior: at AP70 ΔAP≈13.7 → (3.5)^2 * 1.85 ≈ 22.7 mm² rebound toward ~46.
KAPPA_OVERSHORT_PRIOR = 1.85


@dataclass
class ResponseModelParams:
    """Fitted coefficients for one train fold."""

    roa_coef: list[float]
    leak_coef: list[float]
    train_ids: list[str]
    ridge_roa: float = 0.05
    ridge_leak: float = 0.05
    kappa_overshort: float = KAPPA_OVERSHORT_PRIOR
    feature_names_roa: list[str] = field(
        default_factory=lambda: [
            "intercept",
            "delta_ap_mm",
            "is_ima_ap",
            "is_ima_cs",
            "annular_reduction_mm",
            "contact_fraction",
            "is_ap_x_delta",
            "is_cs_x_annular",
        ]
    )
    feature_names_leak: list[str] = field(
        default_factory=lambda: [
            "intercept",
            "log_roa_ratio",
            "coaptation_proxy",
            "contact_fraction",
            "is_ima_ap",
            "is_ima_cs",
            "overshort_sq",
        ]
    )
    roa_space: str = "log_plus_overshort_prior"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _device_flags(device: Optional[str]) -> tuple[float, float]:
    d = (device or "").upper()
    if d.startswith("IMA-AP"):
        return 1.0, 0.0
    if d.startswith("IMA-CS"):
        return 0.0, 1.0
    return 0.0, 0.0


def _annular_reduction_mm(case: dict[str, Any]) -> float:
    circ = case.get("annulus_circumference_mm")
    if circ is None or circ == "":
        device = (case.get("device") or "").upper()
        sh = case.get("shortening_pct")
        if device.startswith("IMA-CS") and sh is not None:
            return float(sh) * 0.16
        return 0.0
    return max(0.0, UNDEFORMED_ANNULUS_MM - float(circ))


def _delta_ap(case: dict[str, Any]) -> float:
    ap = float(case.get("ap_diameter_mm") or DISEASE_AP_MM)
    return max(0.0, DISEASE_AP_MM - ap)


def _overshort_sq(case: dict[str, Any]) -> float:
    return max(0.0, _delta_ap(case) - OVERSHORT_DELTA_AP_REF_MM) ** 2


def _coaptation_proxy(case: dict[str, Any]) -> float:
    delta = _delta_ap(case)
    improve = 0.04 * min(delta, OVERSHORT_DELTA_AP_REF_MM)
    over = max(0.0, delta - OVERSHORT_DELTA_AP_REF_MM)
    return max(0.2, 1.25 - improve + 0.08 * over)


def roa_feature_vector(case: dict[str, Any]) -> np.ndarray:
    """Log-linear features; overshoot handled by fixed prior add-on."""
    delta = _delta_ap(case)
    is_ap, is_cs = _device_flags(case.get("device"))
    contact = float(case.get("contact_fraction") or 0.0)
    annular = _annular_reduction_mm(case)
    return np.array(
        [
            1.0,
            delta,
            is_ap,
            is_cs,
            annular,
            contact,
            is_ap * delta,
            is_cs * annular,
        ],
        dtype=float,
    )


def leak_feature_vector(case: dict[str, Any], *, roa_mm2: float) -> np.ndarray:
    is_ap, is_cs = _device_flags(case.get("device"))
    contact = float(case.get("contact_fraction") or 0.0)
    coapt = _coaptation_proxy(case)
    log_ratio = np.log(max(float(roa_mm2), 2.0) / PATHOLOGY_ROA_REF)
    return np.array(
        [
            1.0,
            log_ratio,
            coapt,
            contact,
            is_ap,
            is_cs,
            _overshort_sq(case),
        ],
        dtype=float,
    )


def _ridge_fit(X: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    n_feat = X.shape[1]
    a = X.T @ X + ridge * np.eye(n_feat)
    b = X.T @ y
    return np.linalg.solve(a, b)


def _overshort_addon(case: dict[str, Any], kappa: float) -> float:
    is_ap, _ = _device_flags(case.get("device"))
    if is_ap < 0.5:
        return 0.0
    return float(kappa) * _overshort_sq(case)


def fit_response_models(
    train_cases: list[dict[str, Any]],
    *,
    ridge_roa: float = 0.05,
    ridge_leak: float = 0.05,
    kappa_overshort: float = KAPPA_OVERSHORT_PRIOR,
) -> ResponseModelParams:
    """Fit f_ROA and f_leak on train folds only (held ROA/leak must be absent)."""
    if len(train_cases) < 3:
        raise ValueError("Need at least 3 training cases for response-model fit")

    # Subtract fixed overshoot prior before log-fit so coefficients learn the
    # monotone component; rebound is restored at predict time.
    X_roa = np.vstack([roa_feature_vector(c) for c in train_cases])
    y_roa_lin = []
    for c in train_cases:
        base = max(float(c["roa_mm2"]) - _overshort_addon(c, kappa_overshort), 2.0)
        y_roa_lin.append(np.log(base))
    roa_coef = _ridge_fit(X_roa, np.array(y_roa_lin, dtype=float), ridge_roa)

    X_leak = np.vstack(
        [
            leak_feature_vector(c, roa_mm2=float(c["roa_mm2"]))
            for c in train_cases
        ]
    )
    y_leak = np.array(
        [float(c["regurgitation_pct"]) for c in train_cases], dtype=float
    )
    y_leak_t = np.sqrt(np.clip(y_leak, 0.0, None))
    leak_coef = _ridge_fit(X_leak, y_leak_t, ridge_leak)

    return ResponseModelParams(
        roa_coef=roa_coef.tolist(),
        leak_coef=leak_coef.tolist(),
        train_ids=[str(c["id"]) for c in train_cases],
        ridge_roa=ridge_roa,
        ridge_leak=ridge_leak,
        kappa_overshort=kappa_overshort,
    )


def predict_roa(params: ResponseModelParams, case: dict[str, Any]) -> float:
    x = roa_feature_vector(case)
    log_roa = float(np.dot(params.roa_coef, x))
    base = float(max(np.exp(log_roa), 2.0))
    return base + _overshort_addon(case, params.kappa_overshort)


def predict_leak(
    params: ResponseModelParams,
    case: dict[str, Any],
    *,
    roa_mm2: Optional[float] = None,
) -> float:
    roa = float(roa_mm2) if roa_mm2 is not None else predict_roa(params, case)
    x = leak_feature_vector(case, roa_mm2=roa)
    sqrt_leak = float(np.dot(params.leak_coef, x))
    pred = max(sqrt_leak, 0.0) ** 2
    return float(min(pred, 20.0))


def predict_case(params: ResponseModelParams, case: dict[str, Any]) -> dict[str, Any]:
    """Predict ROA and leak; AP is passthrough literature geometry input."""
    ap = case.get("ap_diameter_mm")
    roa = predict_roa(params, case)
    leak = predict_leak(params, case, roa_mm2=roa)
    return {
        "pred_ap_diameter_mm": float(ap) if ap is not None else None,
        "pred_roa_mm2": roa,
        "pred_regurgitation_pct": leak,
        "ap_role": "literature_mapping_input",
        "ap_prediction_metric_applicable": False,
    }
