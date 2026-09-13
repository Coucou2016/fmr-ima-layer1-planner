#!/usr/bin/env python3
"""Scaffold: import Galili RSOS 2022 supporting data from Dryad.

Dryad DOI: 10.5061/dryad.bzkh1899d
Paper DOI: 10.1098/rsos.211726

This script does NOT train a new surrogate end-to-end (P1). It documents
provenance and, when network/credentials allow, downloads the archive into
data/raw/galili_dryad/.

Usage:
    python tools/import_galili_dryad.py --dry-run
    python tools/import_galili_dryad.py --download
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "galili_dryad"
PROVENANCE = ROOT / "data" / "provenance.yaml"

DRYAD_DOI = "10.5061/dryad.bzkh1899d"
# Dryad landing / API tip — may change; prefer DOI resolver.
DRYAD_LANDING = f"https://doi.org/{DRYAD_DOI}"


def write_stub_readme() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    readme = ROOT / "data" / "raw" / "README.md"
    readme.write_text(
        """# Raw data drop zone

## Galili et al. RSOS 2022 supporting files

- Paper: https://doi.org/10.1098/rsos.211726
- Dryad: https://doi.org/10.5061/dryad.bzkh1899d

Place downloaded Dryad contents under `galili_dryad/` after review of Dryad
license terms. Do not commit large binary archives unless explicitly approved.

Layer-1 currently uses *published table scalars* in `results/reference_data.yaml`.
Full Dryad time-series / mesh training is a P1 follow-on.
""",
        encoding="utf-8",
    )
    if not PROVENANCE.exists():
        PROVENANCE.write_text(
            f"""# Dataset provenance for FMR IMA Layer-1

galili_rsos_2022:
  citation: "Galili L. et al. R. Soc. Open Sci. 2022"
  paper_doi: "10.1098/rsos.211726"
  dryad_doi: "{DRYAD_DOI}"
  dryad_landing: "{DRYAD_LANDING}"
  local_path: "data/raw/galili_dryad/"
  status: "stub — download with tools/import_galili_dryad.py --download when network allows"
  used_in_layer1: "published peak-systole table scalars only (reference_data.yaml)"
  not_yet_used: "full Dryad trajectories / meshes for leave-one-out training"
""",
            encoding="utf-8",
        )


def try_download() -> int:
    write_stub_readme()
    RAW.mkdir(parents=True, exist_ok=True)
    marker = RAW / "DOWNLOAD_ATTEMPTED.json"
    try:
        req = Request(DRYAD_LANDING, headers={"User-Agent": "fmr-ima-layer1-planner/P1"})
        with urlopen(req, timeout=30) as resp:
            info = {
                "url": DRYAD_LANDING,
                "status": getattr(resp, "status", None),
                "final_url": resp.geturl(),
                "note": (
                    "Landing resolved. Manual zip download from Dryad UI may still be "
                    "required; this scaffold does not unpack proprietary archives."
                ),
            }
        marker.write_text(json.dumps(info, indent=2), encoding="utf-8")
        print("Resolved Dryad landing:", info["final_url"])
        print("Wrote", marker)
        print("Complete zip fetch/unpack remains manual / P1 follow-on.")
        return 0
    except Exception as exc:  # noqa: BLE001 — honest network stub
        marker.write_text(
            json.dumps({"url": DRYAD_LANDING, "error": str(exc)}, indent=2),
            encoding="utf-8",
        )
        print("Download blocked or failed:", exc, file=sys.stderr)
        print("Stub README + provenance written; retry when network allows.")
        return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Write stubs only")
    ap.add_argument("--download", action="store_true", help="Attempt Dryad landing fetch")
    args = ap.parse_args()
    write_stub_readme()
    print("Wrote data/raw/README.md and data/provenance.yaml stubs.")
    if args.download and not args.dry_run:
        return try_download()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
