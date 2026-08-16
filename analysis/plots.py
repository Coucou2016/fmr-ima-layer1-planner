"""Comparison plots for IMA strategies and paper figures.

All report/paper figures use SciencePlots + Times New Roman at dpi≥300.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, List, Optional

import matplotlib

# Headless / CI: always write PNGs even without a display.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# SciencePlots registers styles on import.
import scienceplots  # noqa: F401

from .metrics import CaseMetrics

PAPER_DPI = 300
REPORT_DPI = 300


@contextmanager
def _science_style(*, serif: bool = True) -> Iterator[None]:
    """Apply SciencePlots style with Times New Roman (no LaTeX required)."""
    styles = ["science", "no-latex"]
    with plt.style.context(styles):
        rc = {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "axes.linewidth": 0.8,
            "legend.fontsize": 8,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "lines.linewidth": 1.4,
            "lines.markersize": 5.5,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.dpi": PAPER_DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.05,
        }
        if not serif:
            rc["font.family"] = "sans-serif"
        with plt.rc_context(rc):
            yield


def _savefig(fig: plt.Figure, path: Path, *, dpi: int = PAPER_DPI) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


def plot_regurgitation_bars(metrics: List[CaseMetrics], out_path: Path) -> None:
    ids = [m.case_id for m in metrics]
    vals = [m.regurgitation_pct for m in metrics]
    ref = [m.reference_regurgitation_pct or 0 for m in metrics]
    x = range(len(ids))
    w = 0.35
    with _science_style():
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar([i - w / 2 for i in x], vals, width=w, label="Simulated")
        mask = [r > 0 for r in ref]
        ref_vals = [r if m else 0 for r, m in zip(ref, mask)]
        ax.bar([i + w / 2 for i in x], ref_vals, width=w, label="Paper reference", alpha=0.7)
        ax.set_xticks(list(x))
        ax.set_xticklabels(ids, rotation=45, ha="right")
        ax.set_ylabel("Regurgitation (%)")
        ax.set_title("FMR: IMA-CS vs IMA-AP — Regurgitation Fraction")
        ax.legend(frameon=False)
        fig.tight_layout()
        _savefig(fig, out_path, dpi=REPORT_DPI)


def plot_comparison(metrics: List[CaseMetrics], out_path: Path) -> None:
    with _science_style():
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        cs = [m for m in metrics if m.device == "IMA-CS"]
        ap = [m for m in metrics if m.device == "IMA-AP"]
        if cs:
            axes[0].plot(
                [m.shortening_pct for m in cs],
                [m.regurgitation_pct for m in cs],
                "o-",
                label="IMA-CS",
            )
            axes[0].set_xlabel("Bridge shortening (%)")
        if ap:
            axes[1].plot(
                [m.shortening_pct for m in ap],
                [m.regurgitation_pct for m in ap],
                "s-",
                color="C1",
                label="IMA-AP",
            )
            axes[1].set_xlabel("Suture shortening (%)")
        for ax in axes:
            ax.set_ylabel("Regurgitation (%)")
            ax.grid(True, alpha=0.3)
            ax.legend(frameon=False, fontsize=8)
        fig.suptitle("Regurgitation vs IMA shortening")
        fig.tight_layout()
        _savefig(fig, out_path, dpi=REPORT_DPI)


def _ap_single(points, mapping: str):
    return sorted(
        [
            p
            for p in points
            if p.device == "IMA-AP" and p.n_sutures == 1 and p.mapping_mode == mapping
        ],
        key=lambda p: p.shortening_pct or 0.0,
    )


def _cs(points, mapping: str):
    return sorted(
        [
            p
            for p in points
            if p.device == "IMA-CS" and p.mapping_mode == mapping
        ],
        key=lambda p: p.shortening_pct or 0.0,
    )


def _dual(points, mapping: str):
    return sorted(
        [
            p
            for p in points
            if p.device == "IMA-AP" and p.n_sutures >= 2 and p.mapping_mode == mapping
        ],
        key=lambda p: p.shortening_pct or 0.0,
    )


def plot_paper_figures(
    points: list,
    out_dir: Path,
    *,
    recommendation: Optional[dict[str, Any]] = None,
) -> dict[str, Path]:
    """Paper figures from the physics sweep (no YAML blend)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    written["fig1"] = out_dir / "fig1_ima_ap_nonmonotonic_clinical_window.png"
    _fig1_nonmonotonic(points, written["fig1"])

    written["fig2"] = out_dir / "fig2_suture_vs_ap_reduction.png"
    _fig2_dose_map(points, written["fig2"])

    written["fig3"] = out_dir / "fig3_jet_location.png"
    _fig3_jet(points, written["fig3"])

    written["fig4"] = out_dir / "fig4_pareto_lcx_strain.png"
    _fig4_pareto(points, written["fig4"], recommendation=recommendation)

    written["fig5"] = out_dir / "fig5_dual_vs_single_suture.png"
    _fig5_dual(points, written["fig5"])
    return written


def _fig1_nonmonotonic(points, path: Path) -> None:
    galili = _ap_single(points, "galili")
    clinical = _ap_single(points, "clinical")
    with _science_style():
        fig, ax = plt.subplots(figsize=(8.5, 5.0))
        if galili:
            ax.plot(
                [p.shortening_pct for p in galili],
                [p.physics_regurgitation_pct for p in galili],
                "s-",
                color="C1",
                label="IMA-AP physics (Galili AP mapping)",
            )
        if clinical:
            ax.plot(
                [p.shortening_pct for p in clinical],
                [p.physics_regurgitation_pct for p in clinical],
                "o--",
                color="C0",
                label="IMA-AP physics (clinical AP mapping)",
            )
        ax.axvspan(46.7, 66.7, color="C2", alpha=0.12, label="Clinical AP window ~14–20% (η=0.30)")
        ax.set_xlabel("Suture shortening (%)")
        ax.set_ylabel("Physics regurgitation (%)")
        ax.set_title("IMA-AP: non-monotonic Galili curve vs clinical AP dose")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", frameon=False, fontsize=8)
        fig.tight_layout()
        _savefig(fig, path)


def _fig2_dose_map(points, path: Path) -> None:
    galili = _ap_single(points, "galili")
    clinical = _ap_single(points, "clinical")
    cs_clin = _cs(points, "clinical")
    with _science_style():
        fig, ax = plt.subplots(figsize=(8.5, 5.0))
        if galili:
            ax.plot(
                [p.shortening_pct for p in galili],
                [p.ap_reduction_pct for p in galili],
                "s-",
                color="C1",
                label="IMA-AP Galili LHHM (suture % ≠ AP %)",
            )
        if clinical:
            ax.plot(
                [p.shortening_pct for p in clinical],
                [p.ap_reduction_pct for p in clinical],
                "o--",
                color="C0",
                label="IMA-AP clinical η=0.30",
            )
        if cs_clin:
            ax.plot(
                [p.shortening_pct for p in cs_clin],
                [p.ap_reduction_pct for p in cs_clin],
                "^-",
                color="C3",
                label="IMA-CS clinical η≈0.67",
            )
        ax.axhspan(14.0, 20.0, color="C2", alpha=0.15, label="Clinical AP window 14–20%")
        ax.axhline(58.43, color="0.4", ls=":", label="Galili 70% numerical extreme (~58% AP)")
        ax.set_xlabel("Device shortening (%)")
        ax.set_ylabel("AP diameter reduction (%)")
        ax.set_title("Innovation A: map shortening % onto AP-mm / AP-% space")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best", frameon=False, fontsize=8)
        fig.tight_layout()
        _savefig(fig, path)


def _fig3_jet(points, path: Path) -> None:
    with _science_style():
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
        color = {"central": "C0", "mixed": "C1", "commissural": "C3"}
        for ax, mapping, title in (
            (axes[0], "galili", "Galili AP mapping"),
            (axes[1], "clinical", "Clinical AP mapping"),
        ):
            series = _ap_single(points, mapping) + _cs(points, mapping)
            for p in series:
                marker = "s" if p.device == "IMA-AP" else "o"
                ax.scatter(
                    p.shortening_pct,
                    p.commissural_fraction,
                    c=color.get(p.jet_location, "0.5"),
                    marker=marker,
                    s=45,
                    zorder=3,
                )
            ap = _ap_single(points, mapping)
            if ap:
                ax.plot(
                    [p.shortening_pct for p in ap],
                    [p.commissural_fraction for p in ap],
                    "-",
                    color="0.6",
                    lw=1,
                    label="IMA-AP",
                )
            cs = _cs(points, mapping)
            if cs:
                ax.plot(
                    [p.shortening_pct for p in cs],
                    [p.commissural_fraction for p in cs],
                    "--",
                    color="0.4",
                    lw=1,
                    label="IMA-CS",
                )
            ax.axhline(0.28, color="0.5", ls=":", lw=0.8)
            ax.axhline(0.55, color="0.5", ls=":", lw=0.8)
            ax.set_title(title)
            ax.set_xlabel("Shortening (%)")
            ax.grid(True, alpha=0.3)
            ax.legend(frameon=False, fontsize=8)
        axes[0].set_ylabel("Commissural fraction of ROA")
        fig.suptitle("Jet location vs shortening (squares=IMA-AP, circles=IMA-CS)")
        fig.tight_layout()
        _savefig(fig, path)


def _fig4_pareto(points, path: Path, recommendation: Optional[dict[str, Any]] = None) -> None:
    cs = _cs(points, "clinical")
    with _science_style():
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        if cs:
            axes[0].plot(
                [p.cs_lcx_mm for p in cs],
                [p.physics_regurgitation_pct for p in cs],
                "o-",
                color="C0",
            )
            for p in cs:
                axes[0].annotate(
                    f"{int(p.shortening_pct)}%",
                    (p.cs_lcx_mm, p.physics_regurgitation_pct),
                    fontsize=7,
                )
        axes[0].axvline(8.6, color="C3", ls="--", label="Rottländer 8.6 mm")
        axes[0].set_xlabel("CS–LCx distance (mm)")
        axes[0].set_ylabel("Physics regurgitation (%)")
        axes[0].set_title("IMA-CS: regurg vs LCx safety")
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(frameon=False, fontsize=8)

        if cs:
            axes[1].plot(
                [p.niti_alternating_strain_pct for p in cs],
                [p.physics_regurgitation_pct for p in cs],
                "s-",
                color="C1",
            )
        axes[1].axvline(0.4, color="C3", ls="--", label="Alternating strain 0.4%")
        axes[1].set_xlabel("NiTi alternating strain (%)")
        axes[1].set_ylabel("Physics regurgitation (%)")
        axes[1].set_title("IMA-CS: regurg vs NiTi fatigue strain")
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(frameon=False, fontsize=8)

        rec = (recommendation or {}).get("recommended") or {}
        if rec.get("device") == "IMA-CS" and rec.get("cs_lcx_mm") is not None:
            axes[0].scatter(
                [rec["cs_lcx_mm"]],
                [rec["physics_regurgitation_pct"]],
                marker="*",
                s=140,
                c="k",
                zorder=4,
            )

        fig.suptitle("Pareto view (clinical mapping; illustrative CS–LCx anatomy)")
        fig.tight_layout()
        _savefig(fig, path)


def _fig5_dual(points, path: Path) -> None:
    with _science_style():
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        for mapping, ax in (("galili", axes[0]), ("clinical", axes[1])):
            single = _ap_single(points, mapping)
            dual = _dual(points, mapping)
            if single:
                ax.plot(
                    [p.shortening_pct for p in single],
                    [p.commissural_fraction for p in single],
                    "s-",
                    label="Single suture",
                )
                ax.plot(
                    [p.shortening_pct for p in single],
                    [p.physics_regurgitation_pct for p in single],
                    "s--",
                    alpha=0.7,
                    label="Single — physics regurg %",
                )
            if dual:
                ax.plot(
                    [p.shortening_pct for p in dual],
                    [p.commissural_fraction for p in dual],
                    "o-",
                    label="Dual suture",
                )
            ax.set_title(f"{mapping} mapping")
            ax.set_xlabel("Suture shortening (%)")
            ax.set_ylabel("Commissural fraction / regurg %")
            ax.grid(True, alpha=0.3)
            ax.legend(frameon=False, fontsize=8)
        fig.suptitle("Innovation D: dual vs single IMA-AP (commissural leak)")
        fig.tight_layout()
        _savefig(fig, path)
