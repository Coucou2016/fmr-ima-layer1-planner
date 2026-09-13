#!/usr/bin/env python3
"""Import Galili RSOS 2022 supporting data from Dryad (or local drop / fixture).

Dryad DOI: 10.5061/dryad.bzkh1899d
Paper DOI: 10.1098/rsos.211726

Dryad file inventory (API v2 version 156393):
  - Deformed_coordinates_and_contact.zip   (~315 KB)
  - Blood_leakage_-_SPH_coordinates.zip    (~20 MB)

Manual drop (when bot-wall blocks automated download):
  Place the two zips (or their unpacked trees) under::

      data/raw/galili_dryad/

  Expected layout after unpack (flexible; see ``EXPECTED_LAYOUT``)::

      data/raw/galili_dryad/
        Deformed_coordinates_and_contact.zip
        Blood_leakage_-_SPH_coordinates.zip
        # OR already unpacked:
        Deformed_coordinates_and_contact/
          cases_summary.csv          # preferred machine-readable summary
          <case_id>/contact_nodes.csv
        Blood_leakage_-_SPH_coordinates/
          <case_id>/leakage_summary.csv

Outputs:
  - data/processed/galili_cases.csv   (always)
  - data/processed/galili_cases.parquet  (if pyarrow/fastparquet available)
  - data/provenance.yaml
  - data/raw/README.md

Honesty:
  - Never mix undeformed diastole with peak-systole without ``cardiac_phase``.
  - Published table scalars from ``results/reference_data.yaml`` are a
    *secondary* path when Dryad-derived rows are absent.
  - Contact-cluster / synthetic ROA helpers elsewhere are visualization-only.

Usage::

    python tools/import_galili_dryad.py --dry-run
    python tools/import_galili_dryad.py --download
    python tools/import_galili_dryad.py --from-fixture
    python tools/import_galili_dryad.py --process
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "galili_dryad"
PROCESSED = ROOT / "data" / "processed"
PROVENANCE = ROOT / "data" / "provenance.yaml"
RAW_README = ROOT / "data" / "raw" / "README.md"
REFERENCE = ROOT / "results" / "reference_data.yaml"
FIXTURE = ROOT / "data" / "fixtures" / "galili_dryad_mini"

DRYAD_DOI = "10.5061/dryad.bzkh1899d"
# Crossref / DataCite cite the RSOS article as 10.1098/rsos.211464 (not 211726).
PAPER_DOI = "10.1098/rsos.211464"
DRYAD_LANDING = f"https://doi.org/{DRYAD_DOI}"
DRYAD_API = "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.bzkh1899d"
DRYAD_VERSION_ID = 156393
DRYAD_FILES = {
    "Deformed_coordinates_and_contact.zip": 1226888,
    "Blood_leakage_-_SPH_coordinates.zip": 1226889,
}

# Real Dryad archive basenames → Layer-1 case_id (peak systole deformed / SPH dumps).
DRYAD_CASE_NAME_MAP = {
    "fmr disease": "pathology",
    "fmr_disease": "pathology",
    "disease": "pathology",
    "ima-ap 30": "ima_ap_30",
    "ima-ap 50": "ima_ap_50",
    "ima-ap 70": "ima_ap_70",
    "ima-cs 14": "ima_cs_14",
    "ima-cs 18": "ima_cs_18",
    "ima-cs 22": "ima_cs_22",
    "ima-ap 30%": "ima_ap_30",
    "ima-ap 50%": "ima_ap_50",
    "ima-ap 70%": "ima_ap_70",
    "ima-cs 14%": "ima_cs_14",
    "ima-cs 18%": "ima_cs_18",
    "ima-cs 22%": "ima_cs_22",
    "ima_ap_30": "ima_ap_30",
    "ima_ap_50": "ima_ap_50",
    "ima_ap_70": "ima_ap_70",
    "ima_cs_14": "ima_cs_14",
    "ima_cs_18": "ima_cs_18",
    "ima_cs_22": "ima_cs_22",
    "pathology": "pathology",
}

EXPECTED_LAYOUT = """
Expected Dryad drop layout
--------------------------
data/raw/galili_dryad/
  Deformed_coordinates_and_contact.zip
  Blood_leakage_-_SPH_coordinates.zip

After unpack (importer also accepts already-unpacked folders with the same
basenames, with or without the .zip suffix):

  Deformed_coordinates_and_contact/
    cases_summary.csv
      required columns (case-insensitive):
        case_id, cardiac_phase, ap_diameter_mm
      optional: roa_mm2, contact_score, annulus_circumference_mm, notes
    <case_id>/contact_nodes.csv   # visualization / contact descriptors only
      columns: x,y,z[,force_n]

  Blood_leakage_-_SPH_coordinates/
    <case_id>/leakage_summary.csv
      columns: case_id, cardiac_phase, regurgitation_pct
      optional: n_particles_la, n_particles_aorta

Cardiac phase MUST be explicit. Rows with cardiac_phase containing
'undformed'/'diastole' are stored separately and never merged into
peak-systole ROA/leakage features without the phase tag.
""".strip()

CASE_ID_ALIASES = {
    "disease": "pathology",
    "untreated": "pathology",
    "pathology": "pathology",
    "ima-cs-14": "ima_cs_14",
    "ima_cs_14": "ima_cs_14",
    "ima-cs-18": "ima_cs_18",
    "ima_cs_18": "ima_cs_18",
    "ima-cs-22": "ima_cs_22",
    "ima_cs_22": "ima_cs_22",
    "ima-ap-30": "ima_ap_30",
    "ima_ap_30": "ima_ap_30",
    "ima-ap-50": "ima_ap_50",
    "ima_ap_50": "ima_ap_50",
    "ima-ap-70": "ima_ap_70",
    "ima_ap_70": "ima_ap_70",
}


def _ua() -> dict[str, str]:
    return {"User-Agent": "fmr-ima-layer1-planner/P1 (+https://github.com/Coucou2016/fmr-ima-layer1-planner)"}


def _norm_case_id(raw: str) -> str:
    s = raw.strip().lower()
    # Strip extension and common Dryad punctuation (IMA-AP 50%.csv).
    s = re.sub(r"\.csv$", "", s)
    s = s.replace("%", "")
    if s in DRYAD_CASE_NAME_MAP:
        return DRYAD_CASE_NAME_MAP[s]
    # Compact form: "ima-ap 50" / "ima_ap_50"
    compact = re.sub(r"[\s]+", " ", s).strip()
    if compact in DRYAD_CASE_NAME_MAP:
        return DRYAD_CASE_NAME_MAP[compact]
    key = re.sub(r"[\s]+", "_", s.replace("-", "_"))
    key = key.replace("__", "_").strip("_")
    if key in DRYAD_CASE_NAME_MAP:
        return DRYAD_CASE_NAME_MAP[key]
    return CASE_ID_ALIASES.get(key, key)


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_deformed_contact_csv(path: Path) -> dict[str, Any]:
    """Parse Galili Dryad deformed leaflet+contact node dump.

    Columns: node#, x (mm), y (mm), z (mm), In contact (Y=1/N=1)
    Returns contact fraction and bounding-box extents. Does **not** invent
    published AP/ROA from these nodes (annulus landmarks are not labeled).
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(text))
    next(reader, None)  # header
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    n_contact = 0
    n = 0
    for row in reader:
        if len(row) < 5:
            continue
        try:
            x, y, z = float(row[1]), float(row[2]), float(row[3])
            c = int(float(row[4]))
        except (TypeError, ValueError):
            continue
        xs.append(x)
        ys.append(y)
        zs.append(z)
        n += 1
        if c:
            n_contact += 1
    if n == 0:
        return {"n_nodes": 0, "n_contact": 0, "contact_fraction": None}
    return {
        "n_nodes": n,
        "n_contact": n_contact,
        "contact_fraction": n_contact / n,
        "bbox_dx_mm": max(xs) - min(xs),
        "bbox_dy_mm": max(ys) - min(ys),
        "bbox_dz_mm": max(zs) - min(zs),
    }


def _count_sph_coordinate_rows(path: Path) -> int:
    """Count particle rows in SPH Coordinates.csv (full-domain cloud ≈29k)."""
    n = 0
    with path.open(encoding="utf-8-sig", errors="replace") as f:
        next(f, None)
        for line in f:
            if line.strip():
                n += 1
    return n


def _infer_device_fields(row: dict[str, Any], cid: str) -> None:
    if cid.startswith("ima_cs"):
        row["device"] = "IMA-CS"
        m = re.search(r"(\d+)$", cid)
        if m:
            row["shortening_pct"] = float(m.group(1))
    elif cid.startswith("ima_ap"):
        row["device"] = "IMA-AP"
        m = re.search(r"(\d+)$", cid)
        if m:
            row["shortening_pct"] = float(m.group(1))
    elif cid == "pathology":
        row["device"] = None
        row["shortening_pct"] = None


def _norm_phase(raw: Optional[str], *, default: str = "peak_systole") -> str:
    if raw is None or str(raw).strip() == "":
        return default
    s = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
    if "diastole" in s or "undeformed" in s or "undformed" in s:
        return "undeformed_diastole"
    if "systole" in s or "peak" in s:
        return "peak_systole"
    return s


def write_docs() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RAW_README.write_text(
        f"""# Raw data drop zone

## Galili et al. RSOS 2022 supporting files

- Paper: https://doi.org/{PAPER_DOI}
- Dryad: https://doi.org/{DRYAD_DOI}
- Dryad API dataset: `{DRYAD_API}`
- Known version id: `{DRYAD_VERSION_ID}`

### Automated download

```powershell
python tools/import_galili_dryad.py --download
python tools/import_galili_dryad.py --process
```

Dryad's CDN may return HTTP 401 or an Anubis "Validating..." HTML interstitial
to non-browser clients. If that happens, download the two zips manually from
the Dryad UI and drop them here:

```
data/raw/galili_dryad/Deformed_coordinates_and_contact.zip
data/raw/galili_dryad/Blood_leakage_-_SPH_coordinates.zip
```

Do **not** commit large binary archives unless explicitly approved.

### Fixture (CI / offline)

```powershell
python tools/import_galili_dryad.py --from-fixture --process
```

### Phase honesty

Never mix undeformed/diastolic AP (34.4 mm) with peak-systolic ROA/leakage
without an explicit `cardiac_phase` column. See `EXPECTED_LAYOUT` in
`tools/import_galili_dryad.py`.

### Provenance tiers

| Tier | Meaning |
|------|---------|
| `dryad_derived` | Features extracted from local Dryad zips / unpacked trees |
| `fixture_synthetic` | Tiny synthetic smoke layout under `data/fixtures/` |
| `published_table_scalars` | Secondary fallback from `results/reference_data.yaml` |

Layer-1 calibration still uses published peak-systole table scalars unless a
Dryad-derived processed table is present and selected by LOO / calibration
configs.
""",
        encoding="utf-8",
    )


def _http_get(url: str, timeout: float = 60) -> tuple[bytes, str, str]:
    if url.startswith("/"):
        url = "https://datadryad.org" + url
    req = Request(url, headers=_ua())
    with urlopen(req, timeout=timeout) as resp:
        return resp.read(), str(resp.headers.get("Content-Type") or ""), resp.geturl()


def try_download(*, force: bool = False) -> int:
    """Attempt Dryad metadata + file downloads. Returns 0/2.

    Strategy order:
      1. Reuse local zips if present (unless ``force``).
      2. Anubis PoW solver via ``tools/download_dryad_anubis.py`` (file_stream).
      3. Direct API ``/api/v2/files/{id}/download`` (often 401 without bearer).
    """
    write_docs()
    RAW.mkdir(parents=True, exist_ok=True)
    marker = RAW / "DOWNLOAD_ATTEMPTED.json"
    info: dict[str, Any] = {
        "dryad_doi": DRYAD_DOI,
        "api": DRYAD_API,
        "version_id": DRYAD_VERSION_ID,
        "files": {},
        "status": "attempted",
        "strategies": [],
    }
    try:
        meta_bytes, _, final = _http_get(DRYAD_API, timeout=45)
        meta = json.loads(meta_bytes.decode("utf-8"))
        info["landing_resolved"] = final
        info["title"] = meta.get("title")
        info["api_ok"] = True
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        info["api_ok"] = False
        info["api_error"] = str(exc)
        print("Dryad API metadata failed:", exc, file=sys.stderr)

    # File list (metadata only; downloads often bot-walled).
    try:
        files_bytes, _, _ = _http_get(f"/api/v2/versions/{DRYAD_VERSION_ID}/files", timeout=45)
        files_payload = json.loads(files_bytes.decode("utf-8"))
        listed = files_payload.get("_embedded", {}).get("stash:files") or []
        info["listed_files"] = [
            {
                "path": f.get("path") or f.get("name"),
                "size": f.get("size"),
                "id": (f.get("_links") or {}).get("self", {}).get("href"),
            }
            for f in listed
        ]
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        info["list_error"] = str(exc)

    any_ok = False
    missing: list[str] = []
    for fname, fid in DRYAD_FILES.items():
        dest = RAW / fname
        if dest.is_file() and dest.stat().st_size > 10_000 and not force:
            info["files"][fname] = {
                "path": str(dest),
                "status": "already_present",
                "bytes": dest.stat().st_size,
            }
            any_ok = True
        else:
            missing.append(fname)

    if missing or force:
        # Prefer Anubis PoW path (API bearer download returns 401 for anonymous).
        anubis = ROOT / "tools" / "download_dryad_anubis.py"
        if anubis.is_file():
            import runpy

            info["strategies"].append("anubis_pow_file_stream")
            print("Attempting Anubis PoW download via tools/download_dryad_anubis.py ...")
            try:
                runpy.run_path(str(anubis), run_name="__main__")
            except SystemExit as exc:
                info["anubis_exit"] = int(exc.code) if isinstance(exc.code, int) else str(exc.code)
            except Exception as exc:  # noqa: BLE001
                info["anubis_error"] = str(exc)
                print("Anubis downloader failed:", exc, file=sys.stderr)
            report_path = ROOT / "data" / "raw" / "_anubis" / "download_report.json"
            if report_path.is_file():
                try:
                    info["anubis_report"] = json.loads(report_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pass

        for fname, fid in DRYAD_FILES.items():
            dest = RAW / fname
            if dest.is_file() and dest.stat().st_size > 10_000:
                info["files"][fname] = {
                    "path": str(dest),
                    "status": "downloaded_or_present",
                    "bytes": dest.stat().st_size,
                }
                any_ok = True
                continue
            url = f"https://datadryad.org/api/v2/files/{fid}/download"
            info["strategies"].append(f"api_download:{fname}")
            try:
                data, ctype, final = _http_get(url, timeout=180)
                if data[:20].lstrip().startswith(b"<!doctype") or data[:15].lstrip().startswith(b"<html"):
                    raise RuntimeError("HTML interstitial (bot wall) instead of zip bytes")
                if len(data) < 1000:
                    raise ValueError(f"suspiciously small download ({len(data)} bytes)")
                dest.write_bytes(data)
                info["files"][fname] = {
                    "path": str(dest),
                    "status": "downloaded_api",
                    "bytes": len(data),
                    "content_type": ctype,
                    "final_url": final,
                }
                any_ok = True
                print("Downloaded", fname, len(data), "bytes")
            except Exception as exc:  # noqa: BLE001 — honest network report
                info["files"][fname] = {"status": "blocked", "error": str(exc), "url": url}
                print("Download blocked for", fname, ":", exc, file=sys.stderr)

    info["status"] = "ok" if all(
        (RAW / fn).is_file() and (RAW / fn).stat().st_size > 10_000 for fn in DRYAD_FILES
    ) else ("partial" if any_ok else "partial_or_blocked")
    if info["status"] != "ok":
        info["manual_drop"] = (
            "Download both zips from the Dryad UI and place under data/raw/galili_dryad/, "
            "then re-run: python tools/import_galili_dryad.py --process"
        )
        info["note"] = EXPECTED_LAYOUT
    marker.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("Wrote", marker)
    return 0 if info["status"] == "ok" else 2


def ensure_fixture() -> Path:
    """Create a tiny synthetic Dryad-like tree for CI smoke tests."""
    FIXTURE.mkdir(parents=True, exist_ok=True)
    deformed = FIXTURE / "Deformed_coordinates_and_contact"
    leakage = FIXTURE / "Blood_leakage_-_SPH_coordinates"
    deformed.mkdir(parents=True, exist_ok=True)
    leakage.mkdir(parents=True, exist_ok=True)

    # Peak-systole summary (independent AP / ROA / leakage columns) — all seven Galili cases.
    summary_rows = [
        {
            "case_id": "pathology",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 26.1,
            "roa_mm2": 172.8,
            "annulus_circumference_mm": 118.5,
            "contact_score": 0.82,
            "notes": "fixture mirrors published peak-systole anchors",
        },
        {
            "case_id": "ima_cs_14",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 25.5,
            "roa_mm2": 56.7,
            "annulus_circumference_mm": 117.0,
            "contact_score": 0.55,
            "notes": "fixture held-out",
        },
        {
            "case_id": "ima_cs_18",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 24.7,
            "roa_mm2": 55.3,
            "annulus_circumference_mm": 116.0,
            "contact_score": 0.48,
            "notes": "fixture held-out",
        },
        {
            "case_id": "ima_cs_22",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 24.8,
            "roa_mm2": 48.2,
            "annulus_circumference_mm": 115.0,
            "contact_score": 0.41,
            "notes": "fixture",
        },
        {
            "case_id": "ima_ap_30",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 20.7,
            "roa_mm2": 51.1,
            "annulus_circumference_mm": 112.0,
            "contact_score": 0.30,
            "notes": "fixture held-out",
        },
        {
            "case_id": "ima_ap_50",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 15.9,
            "roa_mm2": 27.3,
            "annulus_circumference_mm": 110.0,
            "contact_score": 0.22,
            "notes": "fixture — NOT undeformed 34.4",
        },
        {
            "case_id": "ima_ap_70",
            "cardiac_phase": "peak_systole",
            "ap_diameter_mm": 12.4,
            "roa_mm2": 46.1,
            "annulus_circumference_mm": 108.0,
            "contact_score": 0.35,
            "notes": "commissural leak fixture",
        },
        # Separate diastole row — must not be joined as peak-systole AP.
        {
            "case_id": "geometry_undeformed",
            "cardiac_phase": "undeformed_diastole",
            "ap_diameter_mm": 34.4,
            "roa_mm2": "",
            "annulus_circumference_mm": 118.5,
            "contact_score": "",
            "notes": "diastole geometry only",
        },
    ]
    with (deformed / "cases_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)

    for cid, gap in [("pathology", 1.2), ("ima_ap_50", 0.55), ("ima_ap_70", 0.9)]:
        cdir = deformed / cid
        cdir.mkdir(exist_ok=True)
        with (cdir / "contact_nodes.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["x", "y", "z", "force_n"])
            for i in range(8):
                w.writerow([0.1 * i, gap * 0.2, 0.0, 0.2 + 0.05 * i])

    leak_map = {
        "pathology": 5.26,
        "ima_cs_14": 0.52,
        "ima_cs_18": 0.41,
        "ima_cs_22": 0.29,
        "ima_ap_30": 0.16,
        "ima_ap_50": 0.08,
        "ima_ap_70": 0.13,
    }
    for cid, pct in leak_map.items():
        ldir = leakage / cid
        ldir.mkdir(exist_ok=True)
        with (ldir / "leakage_summary.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "case_id",
                    "cardiac_phase",
                    "regurgitation_pct",
                    "n_particles_la",
                    "n_particles_aorta",
                ],
            )
            w.writeheader()
            # Toy particle counts consistent with % (not real SPH).
            n_la = int(round(pct * 10))
            n_ao = max(1, 1000 - n_la)
            w.writerow(
                {
                    "case_id": cid,
                    "cardiac_phase": "peak_systole",
                    "regurgitation_pct": pct,
                    "n_particles_la": n_la,
                    "n_particles_aorta": n_ao,
                }
            )

    # Also zip them so --process can exercise zip paths.
    for folder_name in ("Deformed_coordinates_and_contact", "Blood_leakage_-_SPH_coordinates"):
        src = FIXTURE / folder_name
        zpath = FIXTURE / f"{folder_name}.zip"
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in src.rglob("*"):
                if p.is_file():
                    zf.write(p, arcname=str(p.relative_to(src.parent)))
    return FIXTURE


def _unzip_if_needed(zip_path: Path, dest_dir: Path, *, force: bool = False) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    marker = dest_dir / ".unpacked_ok"
    if (not force) and marker.is_file() and any(dest_dir.iterdir()):
        return dest_dir
    if dest_dir.exists() and force:
        import shutil

        shutil.rmtree(dest_dir, ignore_errors=True)
        dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    marker.write_text("ok\n", encoding="utf-8")
    return dest_dir


def _find_archive_roots(base: Path, *, force_unzip: bool = False) -> dict[str, Path]:
    """Locate deformed / leakage roots under a drop directory.

    Prefer already-unpacked directories over zips so fixture rebuilds are visible
    without fighting stale ``*_unpacked`` caches.
    """
    found: dict[str, Path] = {}
    if not base.is_dir():
        return found
    dirs: dict[str, Path] = {}
    zips: dict[str, Path] = {}
    for child in base.iterdir():
        name = child.name
        key = None
        if "deformed" in name.lower() and "contact" in name.lower():
            key = "deformed"
        elif "blood" in name.lower() or "leakage" in name.lower() or (
            "sph" in name.lower() and "coordinate" in name.lower()
        ):
            key = "leakage"
        if key is None:
            continue
        if child.is_dir() and not name.endswith("_unpacked"):
            dirs[key] = child
        elif child.is_file() and child.suffix.lower() == ".zip":
            zips[key] = child
    for key, d in dirs.items():
        found[key] = d
    for key, zpath in zips.items():
        if key in found:
            continue
        unpack = base / (zpath.stem + "_unpacked")
        try:
            _unzip_if_needed(zpath, unpack, force=force_unzip)
            found[key] = unpack
        except zipfile.BadZipFile:
            print("Skipping non-zip / HTML fake archive:", zpath, file=sys.stderr)
    return found


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def _float_or_none(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _load_table_scalar_rows() -> list[dict[str, Any]]:
    ref = yaml.safe_load(REFERENCE.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for c in ref.get("cases", []):
        rows.append(
            {
                "case_id": c["id"],
                "cardiac_phase": c.get("cardiac_phase", "peak_systole"),
                "device": c.get("device"),
                "shortening_pct": c.get("shortening_pct", c.get("bridge_shortening_pct")),
                "ap_diameter_mm": c.get("ap_diameter_mm"),
                "roa_mm2": c.get("roa_mm2"),
                "regurgitation_pct": c.get("regurgitation_pct"),
                "annulus_circumference_mm": c.get("annulus_circumference_mm"),
                "contact_descriptor": c.get("contact_pattern"),
                "leakage_descriptor": "published_leakage_fraction",
                "source_tier": "published_table_scalars",
                "source_doi": PAPER_DOI,
                "dryad_doi": DRYAD_DOI,
                "notes": "Secondary path — prefer dryad_derived when local archives present.",
            }
        )
    geo = ref.get("geometry_undeformed_diastole", {})
    if geo:
        rows.append(
            {
                "case_id": "geometry_undeformed",
                "cardiac_phase": geo.get("cardiac_phase", "undeformed_diastole"),
                "device": None,
                "shortening_pct": None,
                "ap_diameter_mm": geo.get("ap_diameter_mm"),
                "roa_mm2": None,
                "regurgitation_pct": None,
                "annulus_circumference_mm": geo.get("annulus_circumference_mm"),
                "contact_descriptor": None,
                "leakage_descriptor": None,
                "source_tier": "published_table_scalars",
                "source_doi": PAPER_DOI,
                "dryad_doi": DRYAD_DOI,
                "notes": "Diastole geometry only — not paired with peak-systole ROA/leakage.",
            }
        )
    return rows


def extract_features(
    *,
    drop_dir: Path,
    source_tier: str,
) -> list[dict[str, Any]]:
    """Extract independent AP / ROA-contact / leakage features with cardiac_phase.

    Real Galili Dryad layout (doi:10.5061/dryad.bzkh1899d):
      - Deformed ``*.csv``: leaflet nodes + binary contact flag (peak systole).
      - SPH ``*/Coordinates.csv``: full-domain particle cloud (~29k), **not**
        chamber-partitioned LA vs aorta counts — so regurgitation_pct cannot be
        recomputed from Dryad alone without fabricating a partition.
      - Published peak-systole AP / ROA / leakage remain table-backed when
        filled; contact_fraction / n_sph_particles are Dryad-derived.
    """
    roots = _find_archive_roots(drop_dir, force_unzip=True)
    by_id: dict[tuple[str, str], dict[str, Any]] = {}

    def _row(cid: str, phase: str) -> dict[str, Any]:
        key = (cid, phase)
        if key not in by_id:
            by_id[key] = {
                "case_id": cid,
                "cardiac_phase": phase,
                "device": None,
                "shortening_pct": None,
                "ap_diameter_mm": None,
                "roa_mm2": None,
                "regurgitation_pct": None,
                "annulus_circumference_mm": None,
                "contact_descriptor": None,
                "leakage_descriptor": None,
                "contact_fraction": None,
                "n_sph_particles": None,
                "source_tier": source_tier,
                "source_doi": PAPER_DOI,
                "dryad_doi": DRYAD_DOI,
                "notes": "",
            }
        return by_id[key]

    deformed = roots.get("deformed")
    if deformed is not None:
        # Fixture / curated summary CSV (optional).
        summaries = list(deformed.rglob("cases_summary.csv"))
        for sp in summaries:
            for raw in _read_csv_rows(sp):
                cid = _norm_case_id(raw.get("case_id") or raw.get("id") or "")
                if not cid:
                    continue
                phase = _norm_phase(raw.get("cardiac_phase") or raw.get("phase"))
                row = _row(cid, phase)
                row["ap_diameter_mm"] = _float_or_none(raw.get("ap_diameter_mm") or raw.get("ap_mm"))
                row["roa_mm2"] = _float_or_none(raw.get("roa_mm2") or raw.get("roa"))
                row["annulus_circumference_mm"] = _float_or_none(
                    raw.get("annulus_circumference_mm") or raw.get("annulus_mm")
                )
                cs = raw.get("contact_score")
                if cs:
                    row["contact_descriptor"] = f"contact_score={cs}"
                    try:
                        row["contact_fraction"] = float(cs)
                    except (TypeError, ValueError):
                        pass
                if raw.get("notes"):
                    row["notes"] = raw["notes"]
                _infer_device_fields(row, cid)

        for contact in deformed.rglob("contact_nodes.csv"):
            cid = _norm_case_id(contact.parent.name)
            if cid in {"deformed_coordinates_and_contact", "deformed_coordinates_and_contact_unpacked"}:
                continue
            row = _row(cid, "peak_systole")
            n_lines = max(0, sum(1 for _ in contact.open(encoding="utf-8")) - 1)
            prev = row.get("contact_descriptor") or ""
            row["contact_descriptor"] = (prev + f"; n_contact_nodes={n_lines}").strip("; ")
            _infer_device_fields(row, cid)

        # Real Dryad: per-case deformed coordinate CSVs with contact flag.
        for csv_path in deformed.rglob("*.csv"):
            name_l = csv_path.name.lower()
            if name_l == "cases_summary.csv" or name_l == "contact_nodes.csv":
                continue
            if "triangulation" in name_l:
                continue
            # Skip if this looks like a coordinates-only SPH file misplaced.
            head = csv_path.read_text(encoding="utf-8-sig", errors="replace")[:240].lower()
            if "in contact" not in head and "contact" not in head:
                continue
            cid = _norm_case_id(csv_path.stem)
            if cid in {
                "deformed_coordinates_and_contact",
                "mv_atrial_surface_triangulation",
                "coordinates",
            }:
                continue
            stats = _parse_deformed_contact_csv(csv_path)
            if not stats.get("n_nodes"):
                continue
            row = _row(cid, "peak_systole")
            _infer_device_fields(row, cid)
            frac = stats.get("contact_fraction")
            row["contact_fraction"] = frac
            parts = [
                f"n_nodes={stats['n_nodes']}",
                f"n_contact={stats['n_contact']}",
                f"contact_fraction={frac:.6f}" if isinstance(frac, float) else "",
                f"bbox_dx_mm={stats.get('bbox_dx_mm'):.3f}" if stats.get("bbox_dx_mm") is not None else "",
                f"bbox_dz_mm={stats.get('bbox_dz_mm'):.3f}" if stats.get("bbox_dz_mm") is not None else "",
                "phase=peak_systole_deformed_coords",
            ]
            row["contact_descriptor"] = "; ".join(p for p in parts if p)
            row["notes"] = (
                (row.get("notes") or "")
                + " | Dryad deformed coords: contact flag extracted; "
                "AP/ROA not invented from unlabeled leaflet nodes"
            ).strip(" |")

    leakage = roots.get("leakage")
    if leakage is not None:
        for lp in leakage.rglob("leakage_summary.csv"):
            for raw in _read_csv_rows(lp):
                cid = _norm_case_id(raw.get("case_id") or lp.parent.name)
                phase = _norm_phase(raw.get("cardiac_phase") or raw.get("phase"))
                row = _row(cid, phase)
                row["regurgitation_pct"] = _float_or_none(
                    raw.get("regurgitation_pct") or raw.get("leakage_pct")
                )
                n_la = _float_or_none(raw.get("n_particles_la"))
                n_ao = _float_or_none(raw.get("n_particles_aorta"))
                if n_la is not None and n_ao is not None:
                    row["leakage_descriptor"] = f"n_la={int(n_la)};n_ao={int(n_ao)}"
                    row["n_sph_particles"] = int(n_la) + int(n_ao)
                else:
                    row["leakage_descriptor"] = "leakage_summary"
                _infer_device_fields(row, cid)

        # Real Dryad: SPH Coordinates.csv per case (full-domain particle dump).
        for coords in leakage.rglob("Coordinates.csv"):
            cid = _norm_case_id(coords.parent.name)
            if not cid or cid.startswith("blood_leakage"):
                continue
            n_part = _count_sph_coordinate_rows(coords)
            row = _row(cid, "peak_systole")
            _infer_device_fields(row, cid)
            row["n_sph_particles"] = n_part
            row["leakage_descriptor"] = (
                f"n_sph_particles={n_part}; "
                "full_domain_cloud_not_LA_vs_aorta_partition; "
                "regurgitation_pct not recomputed from coordinates alone"
            )
            row["notes"] = (
                (row.get("notes") or "")
                + " | Dryad SPH coords counted; leakage % remains table-backed "
                "(no chamber labels in archive)"
            ).strip(" |")

    rows = list(by_id.values())
    # Phase integrity: clear ROA/leakage on diastole rows if somehow present without phase.
    for r in rows:
        if r["cardiac_phase"] == "undeformed_diastole":
            # Keep AP/annulus; drop orifice/leakage if someone mixed columns.
            if r.get("roa_mm2") is not None or r.get("regurgitation_pct") is not None:
                r["notes"] = (
                    (r.get("notes") or "")
                    + " | diastole row: ROA/leakage cleared to avoid phase mixing"
                ).strip(" |")
                r["roa_mm2"] = None
                r["regurgitation_pct"] = None
    return rows


def write_processed(rows: list[dict[str, Any]]) -> Path:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    csv_path = PROCESSED / "galili_cases.csv"
    fields = [
        "case_id",
        "cardiac_phase",
        "device",
        "shortening_pct",
        "ap_diameter_mm",
        "roa_mm2",
        "regurgitation_pct",
        "annulus_circumference_mm",
        "contact_fraction",
        "n_sph_particles",
        "contact_descriptor",
        "leakage_descriptor",
        "source_tier",
        "source_doi",
        "dryad_doi",
        "notes",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})

    # Optional parquet.
    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        parquet_path = PROCESSED / "galili_cases.parquet"
        try:
            df.to_parquet(parquet_path, index=False)
        except Exception:
            # pyarrow/fastparquet may be absent — CSV is the contract.
            pass
    except ImportError:
        pass
    return csv_path


def _archive_checksums() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for fname in DRYAD_FILES:
        path = RAW / fname
        if path.is_file() and path.stat().st_size > 0:
            out[fname] = {
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
    return out


def write_provenance(
    *,
    source_tier: str,
    n_rows: int,
    dryad_present: bool,
    notes: str,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    from datetime import datetime, timezone

    payload = {
        "galili_rsos_2022": {
            "citation": "Galili L. et al. R. Soc. Open Sci. 2022",
            "paper_doi": PAPER_DOI,
            "paper_doi_note": (
                "Crossref/DataCite article DOI is 10.1098/rsos.211464; "
                "earlier drafts incorrectly cited 10.1098/rsos.211726."
            ),
            "dryad_doi": DRYAD_DOI,
            "dryad_landing": DRYAD_LANDING,
            "dryad_api": DRYAD_API,
            "dryad_version_id": DRYAD_VERSION_ID,
            "local_path": "data/raw/galili_dryad/",
            "processed_path": "data/processed/galili_cases.csv",
            "status": source_tier,
            "dryad_archives_present": dryad_present,
            "n_processed_rows": n_rows,
            "download_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "archive_checksums": _archive_checksums(),
            "extraction_notes": (
                "Deformed CSVs → contact_fraction / bbox extents (peak systole). "
                "SPH Coordinates.csv → n_sph_particles (full-domain cloud). "
                "Published AP/ROA/leakage filled from results/reference_data.yaml "
                "when absent; not recomputed from unlabeled chamber partitions. "
                "Never mix undeformed diastole AP 34.4 mm with peak-systole ROA/leakage."
            ),
            "cardiac_phase_tagging": (
                "All Dryad-derived deformed/SPH rows tagged cardiac_phase=peak_systole; "
                "geometry_undeformed diastole row remains separate when present."
            ),
            "primary_when_present": "dryad_derived features with cardiac_phase",
            "secondary_fallback": "published_table_scalars from results/reference_data.yaml",
            "used_in_layer1": (
                "peak-systole AP / ROA / leakage anchors; LOO scores published quantities "
                "without treating calibration-blend cases as independent validation; "
                "contact_fraction is an independent Dryad-derived coaptation descriptor"
            ),
            "not_claimed": (
                "full mesh/SPH re-simulation; independent external validation of "
                "high anchor-weight blended cases; chamber-partitioned leakage "
                "recomputed solely from Dryad particle dumps"
            ),
            "notes": notes,
            "expected_layout": EXPECTED_LAYOUT,
        }
    }
    if extra:
        payload["galili_rsos_2022"].update(extra)
    PROVENANCE.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    # Lightweight manifest next to archives (no binary commit required).
    if dryad_present:
        manifest = {
            "dryad_doi": DRYAD_DOI,
            "paper_doi": PAPER_DOI,
            "checksums": _archive_checksums(),
            "download_strategy": "anubis_pow_file_stream_or_local_drop",
        }
        (RAW / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def process(*, from_fixture: bool = False, allow_table_fallback: bool = True) -> Path:
    write_docs()
    source_tier = "published_table_scalars"
    notes = ""
    rows: list[dict[str, Any]] = []

    if from_fixture:
        ensure_fixture()
        rows = extract_features(drop_dir=FIXTURE, source_tier="fixture_synthetic")
        source_tier = "fixture_synthetic"
        notes = "Built from data/fixtures/galili_dryad_mini (CI smoke)."
    else:
        dryad_roots = _find_archive_roots(RAW, force_unzip=True)
        if dryad_roots:
            rows = extract_features(drop_dir=RAW, source_tier="dryad_derived")
            source_tier = "dryad_derived"
            notes = (
                "Extracted from local Dryad archives under data/raw/galili_dryad/ "
                "(real Galili deformed contact CSVs + SPH Coordinates.csv). "
                "AP/ROA/leakage table-backed where coordinate dumps lack annulus "
                "landmarks / chamber partitions."
            )
        elif allow_table_fallback:
            rows = _load_table_scalar_rows()
            source_tier = "published_table_scalars"
            notes = (
                "Dryad zips not present or not unpackable; using published table scalars "
                "as secondary path. Re-run --download or manual drop + --process when available."
            )
        else:
            raise FileNotFoundError("No Dryad drop and table fallback disabled.")

    # If Dryad/fixture peak-systole rows lack leakage/ROA, merge table scalars
    # for missing fields only (still tag source_tier of the row).
    if source_tier in {"dryad_derived", "fixture_synthetic"}:
        table = {(r["case_id"], r["cardiac_phase"]): r for r in _load_table_scalar_rows()}
        for r in rows:
            key = (r["case_id"], r["cardiac_phase"])
            t = table.get(key)
            if t is None:
                continue
            for field in (
                "roa_mm2",
                "regurgitation_pct",
                "ap_diameter_mm",
                "device",
                "shortening_pct",
                "annulus_circumference_mm",
            ):
                if r.get(field) is None and t.get(field) is not None:
                    r[field] = t[field]
                    r["notes"] = (
                        (r.get("notes") or "")
                        + f" | filled {field} from published_table_scalars"
                    ).strip(" |")
        # Ensure undeformed diastole geometry row present for phase honesty.
        if ("geometry_undeformed", "undeformed_diastole") not in {
            (r["case_id"], r["cardiac_phase"]) for r in rows
        }:
            geo = table.get(("geometry_undeformed", "undeformed_diastole"))
            if geo:
                rows.append(dict(geo))

    csv_path = write_processed(rows)
    dryad_present = bool(_find_archive_roots(RAW))
    write_provenance(
        source_tier=source_tier,
        n_rows=len(rows),
        dryad_present=dryad_present,
        notes=notes,
    )
    print(f"Wrote {csv_path} ({len(rows)} rows, source_tier={source_tier})")
    print(f"Wrote {PROVENANCE}")
    return csv_path


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Import Galili Dryad supporting data")
    ap.add_argument("--dry-run", action="store_true", help="Write README/provenance stubs only")
    ap.add_argument("--download", action="store_true", help="Attempt Dryad file download")
    ap.add_argument("--force", action="store_true", help="Re-download even if zip present")
    ap.add_argument("--from-fixture", action="store_true", help="Build/use CI fixture tree")
    ap.add_argument("--process", action="store_true", help="Extract → data/processed/galili_cases.csv")
    ap.add_argument("--ensure-fixture", action="store_true", help="Only create fixture files")
    args = ap.parse_args(argv)

    write_docs()
    if args.ensure_fixture:
        p = ensure_fixture()
        print("Fixture at", p)
        return 0
    if args.dry_run and not (args.download or args.process or args.from_fixture):
        write_provenance(
            source_tier="stub",
            n_rows=0,
            dryad_present=False,
            notes="dry-run only",
        )
        print("Wrote data/raw/README.md and data/provenance.yaml stubs.")
        print(EXPECTED_LAYOUT)
        return 0
    rc = 0
    if args.download:
        rc = try_download(force=args.force)
    if args.from_fixture or args.process or args.download:
        # Always process after download attempt; fixture overrides drop dir.
        process(from_fixture=args.from_fixture)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
