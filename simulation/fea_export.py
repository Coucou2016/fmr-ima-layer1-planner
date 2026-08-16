"""Export hooks for commercial FEA (Abaqus INP, VTK)."""

from pathlib import Path
from models.heart_geometry import HeartGeometry


def export_inp_stub(path: Path, case_id: str, geometry: HeartGeometry) -> None:
    """Minimal Abaqus-style input deck header for external solver."""
    lines = [
        f"*HEADING\nFMR IMA case: {case_id}\n",
        "*NODE",
    ]
    for i, (x, y, z) in enumerate(geometry.to_vtk_points(), start=1):
        lines.append(f"{i}, {x:.4f}, {y:.4f}, {z:.4f}")
    lines.extend(
        [
            "*ELEMENT, TYPE=S4R, ELSET=ANNULUS",
            "1, 1, 2, 3, 4",
            "*MATERIAL, NAME=MYOCARDIUM",
            "*ELASTIC",
            "10., 0.45",
            "*END",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def export_vtk_annulus(path: Path, geometry: HeartGeometry) -> None:
    """Legacy VTK polyline for annulus ring."""
    pts = geometry.to_vtk_points()
    n = len(pts)
    path.write_text(
        "# vtk DataFile Version 3.0\nannulus\nASCII\n"
        "DATASET POLYDATA\n"
        f"POINTS {n} float\n"
        + "".join(f"{x} {y} {z}\n" for x, y, z in pts)
        + f"LINES 1 {n + 1}\n{n} "
        + " ".join(str(i) for i in range(n))
        + f" {0}\n",
        encoding="utf-8",
    )
