#!/usr/bin/env python3
"""Build a deliberately FLAT, folder-free mirror of this project.

The public GitHub repository for this project is intentionally published as a
**single flat directory**: no subfolders, so that an automated reader (ChatGPT,
another coding agent, a crawler, a plain script) can enumerate and fetch the
whole project — code, docs, manuscript, report, figures and core result data —
without walking a tree or guessing paths.

Provenance is not lost: every ``/`` in the original repo-relative path becomes
``__`` in the flat filename, e.g.::

    analysis/planner.py                            -> analysis__planner.py
    docs/paper.html                                -> docs__paper.html
    results/output/planner/scenario_ranking.json   -> results__output__planner__scenario_ranking.json

Two additional, purely cosmetic sanitisation rules keep the flat names
URL/spreadsheet friendly (the exact mapping is recorded for every file, so the
transform is reversible from the index):

    space -> _            "IMA-AP 30%.csv"      -> "IMA-AP_30pct.csv"
    %     -> pct

Usage
-----
    python tools/build_flat_mirror.py --dest E:\\Projects\\<name>-flat-staging
    python tools/build_flat_mirror.py --dest ... --dry-run

The script never modifies the structured working tree; it only *reads* it and
writes a fresh staging directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEPARATOR = "__"

# Directories never walked (caches, VCS internals, editors).
EXCLUDE_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "node_modules",
}

# Repo-relative directories never walked. ``data/raw/_anubis`` is excluded on
# purpose: it contains transient Anubis challenge cookies (including a signed
# auth cookie) that must never be published.
EXCLUDE_DIR_RELPATHS = {
    "data/raw/_anubis",
    "data/raw/_download_probes",
}

# Individual files never copied.
EXCLUDE_FILE_NAMES = {".coverage", ".DS_Store", "Thumbs.db"}
EXCLUDE_FILE_SUFFIXES = {".pyc", ".pyo", ".swp", ".part"}
EXCLUDE_FILE_PATTERNS = [
    re.compile(r"^\.env($|\.)"),
    re.compile(r"\.pem$"),
    re.compile(r"\.key$"),
    re.compile(r"^id_rsa"),
    re.compile(r"^\.netrc$"),
    re.compile(r"(?i)credential"),
    re.compile(r"(?i)secret"),
]

# Files this builder writes; never treated as flatten sources.
GENERATED_FILES = {
    "FLAT_FILE_INDEX.md",
    "FLAT_FILEMAP.json",
    "FLAT_LAYOUT.md",
    "START_HERE_FLAT_LAYOUT.md",
}

# Grouping used for the human-readable index.
GROUP_TITLES = {
    "entry": "Canonical entry points (paper, report, README)",
    "docs": "Documentation, manuscript, collaboration logs",
    "paperout": "Paper / report deliverables (HTML, MD, PDF)",
    "code": "Source code",
    "config": "Configuration",
    "tests": "Tests",
    "ci": "CI / packaging metadata",
    "results": "Core result data (JSON / CSV / figures)",
    "data": "Data provenance, processed tables, fixtures",
    "dryad": "Third-party Galili Dryad raw archive (unmodified)",
    "other": "Other root-level files",
}
GROUP_ORDER = [
    "entry",
    "paperout",
    "docs",
    "code",
    "config",
    "tests",
    "ci",
    "results",
    "data",
    "dryad",
    "other",
]


def sanction(name: str) -> str:
    """Make a single path component URL/spreadsheet friendly."""
    return name.replace(" ", "_").replace("%", "pct")


def flat_name(rel: str) -> str:
    parts = [p for p in rel.replace("\\", "/").split("/") if p]
    # ``.github/`` would produce a dot-prefixed (hidden) flat name; publish it as
    # ``cisrc__`` so the CI source stays visible in a plain directory listing.
    if parts and parts[0] == ".github":
        parts = ["cisrc", *parts[1:]]
    return SEPARATOR.join(sanction(p) for p in parts)


def group_for(rel: str) -> str:
    r = rel.replace("\\", "/")
    base = Path(r).name
    if r.startswith("data/raw/galili_dryad/"):
        return "dryad"
    if r.startswith("docs/chatgpt_collab/"):
        return "docs"
    if r.startswith("docs/") and base in {"paper.html", "paper.md", "paper.pdf"}:
        return "paperout"
    if r.startswith("docs/"):
        return "docs"
    if base in {"report.html", "report.md", "report.pdf"}:
        return "paperout"
    if base in {"README.md", "MODEL_CARD.md", "CITATION.cff", "LICENSE", "DATA_PROVENANCE.md"}:
        return "entry"
    if r.startswith("tests/"):
        return "tests"
    if r.startswith(".github/"):
        return "ci"
    if r.startswith("configs/"):
        return "config"
    if r.startswith("results/"):
        return "results"
    if r.startswith("data/"):
        return "data"
    if r.startswith(("analysis/", "models/", "simulation/", "sph/", "tools/")):
        return "code"
    if base.endswith((".py", ".ps1", ".sh")):
        return "code"
    if base.endswith((".yaml", ".yml", ".toml", ".ini", ".cfg")):
        return "config"
    return "other"


def is_excluded_dir(rel_parts: tuple[str, ...]) -> bool:
    if any(p in EXCLUDE_DIR_NAMES for p in rel_parts):
        return True
    rel = "/".join(rel_parts)
    return any(rel == e or rel.startswith(e + "/") for e in EXCLUDE_DIR_RELPATHS)


def is_excluded_file(path: Path) -> bool:
    name = path.name
    if name in EXCLUDE_FILE_NAMES or name in GENERATED_FILES:
        return True
    if path.suffix.lower() in EXCLUDE_FILE_SUFFIXES:
        return True
    return any(p.search(name) for p in EXCLUDE_FILE_PATTERNS)


def build_plan(root: Path) -> list[dict]:
    entries: list[dict] = []

    for dirpath, dirnames, filenames in os_walk_sorted(root):
        here = Path(dirpath)
        rel_dir = here.relative_to(root)
        parts = tuple(rel_dir.parts)
        if is_excluded_dir(parts):
            dirnames[:] = []
            continue
        dirnames[:] = sorted(d for d in dirnames if not is_excluded_dir(parts + (d,)))
        for fn in filenames:
            fp = here / fn
            if is_excluded_file(fp):
                continue
            rel = fp.relative_to(root).as_posix()
            entries.append(
                {
                    "flat": flat_name(rel),
                    "original": rel,
                    "bytes": fp.stat().st_size,
                    "group": group_for(rel),
                }
            )

    entries.sort(key=lambda e: e["original"])

    seen: dict[str, str] = {}
    for e in entries:
        prev = seen.get(e["flat"])
        if prev is not None:
            raise SystemExit(
                f"FLAT NAME COLLISION: {e['flat']!r} produced by both "
                f"{prev!r} and {e['original']!r}"
            )
        seen[e["flat"]] = e["original"]

    return entries


def os_walk_sorted(root: Path):
    import os

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        yield dirpath, dirnames, sorted(filenames)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_index(out: Path, entries: list[dict], repo_slug: str) -> None:
    total = sum(e["bytes"] for e in entries)
    by_group: dict[str, list[dict]] = {}
    for e in entries:
        by_group.setdefault(e["group"], []).append(e)

    L: list[str] = []
    L.append("# FLAT_FILE_INDEX.md")
    L.append("")
    L.append(
        "Authoritative map between the **flat** (top-level, folder-free) filenames "
        "published in this repository and their **original** relative paths in the "
        "structured working tree."
    )
    L.append("")
    L.append(
        "Naming rule: every `/` in the original path becomes `__` (double underscore). "
        "For URL-friendliness, spaces become `_` and `%` becomes `pct`. "
        "Example: `results/output/planner/scenario_ranking.json` -> "
        "`results__output__planner__scenario_ranking.json`; "
        "`data/raw/galili_dryad/.../IMA-AP 30%/MV.stl` -> "
        "`data__raw__galili_dryad__...__IMA-AP_30pct__MV.stl`."
    )
    L.append("")
    L.append("See [`FLAT_LAYOUT.md`](FLAT_LAYOUT.md) and "
             "[`START_HERE_FLAT_LAYOUT.md`](START_HERE_FLAT_LAYOUT.md) for the rationale.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- Flat files published: **{len(entries)}**")
    L.append(f"- Total payload: **{total} bytes** ({total / 1e6:.2f} MB)")
    L.append(f"- Flat separator: `{SEPARATOR}`")
    L.append(f"- Source repository tree: `{repo_slug}`")
    L.append("")
    L.append("| Group | Files | MB |")
    L.append("|-------|-------|----|")
    for g in GROUP_ORDER:
        if g not in by_group:
            continue
        n = len(by_group[g])
        mb = sum(x["bytes"] for x in by_group[g]) / 1e6
        L.append(f"| {GROUP_TITLES.get(g, g)} | {n} | {mb:.2f} |")
    L.append("")

    for g in GROUP_ORDER:
        if g not in by_group:
            continue
        L.append(f"## {GROUP_TITLES.get(g, g)}")
        L.append("")
        L.append("| Flat filename | Original path | Bytes |")
        L.append("|---------------|---------------|-------|")
        for e in by_group[g]:
            L.append(f"| `{e['flat']}` | `{e['original']}` | {e['bytes']} |")
        L.append("")

    L.append("## Machine-readable map (JSON)")
    L.append("")
    L.append("<!-- FLAT_MAP_JSON_BEGIN -->")
    L.append("```json")
    L.append(
        json.dumps(
            {
                "separator": SEPARATOR,
                "sanitisation": {"space": "_", "%": "pct"},
                "total_files": len(entries),
                "total_bytes": total,
                "files": [
                    {"flat": e["flat"], "original": e["original"], "bytes": e["bytes"],
                     "group": e["group"], "sha256": e["sha256"]}
                    for e in entries
                ],
            },
            indent=2,
        )
    )
    L.append("```")
    L.append("<!-- FLAT_MAP_JSON_END -->")
    L.append("")

    (out / "FLAT_FILE_INDEX.md").write_text("\n".join(L), encoding="utf-8")


def write_notice(out: Path, entries: list[dict], repo_slug: str) -> None:
    total = sum(e["bytes"] for e in entries)
    dryad = [e for e in entries if e["group"] == "dryad"]
    dryad_mb = sum(e["bytes"] for e in dryad) / 1e6

    (out / "START_HERE_FLAT_LAYOUT.md").write_text(
        f"""# START HERE — why this repository has no subfolders

**This repository is a deliberately flattened, single-directory mirror of the
`20260522-Functional-Mitral-Regurgitation-FMR` project** (Functional Mitral
Regurgitation — literature-anchored low-order surrogate for exploratory
screening of indirect mitral annuloplasty strategies). There are no
subdirectories under the repository root, and that is intentional.

Every source file, document, figure, table, machine result and verification
script sits side by side in one flat namespace so that an automated reader — a
browsing LLM, another coding agent, a script, or a human — can enumerate and
fetch the *entire* project without walking a tree, guessing paths, or being
silently blocked by directory-level access limits.

If you are an automated reviewer (ChatGPT, another agent, a crawler), the useful
reading order is:

1. `START_HERE_FLAT_LAYOUT.md` (this file) — why the layout is flat;
2. `FLAT_FILE_INDEX.md` — complete inventory + flat-name → original-path map;
3. `README.md` — the science and how to run it;
4. `docs__paper.md` / `docs__paper.html` — the manuscript;
5. `report.html` — the self-contained research report (inline CSS, base64 images);
6. `docs__evidence_audit.md` and `docs__真实性审查.md` — the evidence audit;
7. then fetch whatever specific file you need by its flat name.

---

## 1. How the flat names encode provenance

Because there are no folders, the original directory is encoded in each
filename: every `/` becomes `__`. Spaces become `_` and `%` becomes `pct` so the
name stays URL-friendly. Nothing about where a file came from is lost — the
exact flat-name → original-path mapping (with SHA-256) is in
`FLAT_FILE_INDEX.md` and machine-readably in `FLAT_FILEMAP.json`.

| Flat prefix | Original location | Contents |
|---|---|---|
| `docs__` | `docs/` | Manuscript, paper framework, evidence audit, collaboration logs |
| `docs__paper.*` | `docs/paper.*` | Paper deliverables: HTML / MD / PDF |
| `report.*` | repo root | Research report: HTML / MD / PDF |
| `analysis__` | `analysis/` | Sweep, planner/scenario ranker, response-model fitting, ROA, jet, plots, paper tables |
| `models__` | `models/` | Geometry, pathology, devices, material, response models |
| `simulation__` | `simulation/` | Case runner (mechanics proxy), ROA surrogate, calibration, loading, exports |
| `sph__` | `sph/` | SPH-*inspired* leakage proxy and particle helpers |
| `tools__` | `tools/` | Importer, downloader, CV evaluation, report packager, this builder |
| `configs__` | `configs/` | Design space, case tables, pathology, surrogate calibration |
| `tests__` | `tests/` | Unit + golden-regression + round-2 scientific tests |
| `results__` | `results/` | Reference data, clinical references, and `results/output/**` core results |
| `data__processed__` | `data/processed/` | Processed Galili case table (CSV + parquet) |
| `data__fixtures__` | `data/fixtures/` | Small Dryad fixture used by CI |
| `data__raw__galili_dryad__` | `data/raw/galili_dryad/` | Third-party Galili Dryad raw archive (zips + unpacked), unmodified |
| `cisrc__` | `.github/` | CI workflow source (see note below) |

**Example.** `analysis/planner.py` becomes `analysis__planner.py`;
`results/output/planner/scenario_ranking.json` becomes
`results__output__planner__scenario_ranking.json`;
`data/raw/galili_dryad/Blood_leakage_-_SPH_coordinates_unpacked/Blood leakage - SPH coordinates/IMA-AP 30%/MV.stl`
becomes
`data__raw__galili_dryad__Blood_leakage_-_SPH_coordinates_unpacked__Blood_leakage_-_SPH_coordinates__IMA-AP_30pct__MV.stl`.

---

## 2. Publication scope

This mirror carries **{len(entries)} files, {total / 1e6:.2f} MB**.

- **Core result data included on purpose:** everything under `results/output/`
  (planner/scenario ranking, cross-validation folds, response-model parameters,
  paper tables as CSV/JSON, published figures as PNG) plus `data/processed/`
  and the reference/provenance tables. Every number quoted in the paper or the
  report can be traced back to one of these files.
- **Third-party raw archive included on purpose:** the unmodified Galili Dryad
  archive (**{dryad_mb:.2f} MB**, {len(dryad)} files: the two official zips plus
  their unpacked contents). It is redistributed here **only to make the
  provenance chain auditable end-to-end** (published coordinates → derived
  descriptors). It is third-party material governed by its own Dryad licence
  (doi:10.5061/dryad.bzkh1899d), not an output of this project. Checksums are
  recorded in `data__raw__galili_dryad__MANIFEST.json`, in
  `FLAT_FILEMAP.json`, and in `data__provenance.yaml`.
- **Deliberately excluded:** Python caches, virtual environments, `.coverage`
  artefacts, and the transient `data/raw/_anubis` challenge-cookie directory
  (which contains a signed session cookie and must never be published).

---

## 3. What this layout changes (and what it does not)

- **Unchanged:** file contents, hashes, and therefore every scientific result.
  This is a naming/layout transformation only.
- **Changed:** module import paths. In the flat repository the Python packages
  (`analysis`, `models`, `simulation`, `sph`, `tools`) no longer exist as
  directories, so `python run_pipeline.py` and `pytest` are expected to be run
  from the structured working tree (or after restoring it, see §4), not from
  this flat snapshot.
- **CI:** the workflow source is published as a top-level file
  (`.github/workflows/ci.yml` → `cisrc__workflows__ci.yml`) so that it travels
  with the snapshot; GitHub Actions therefore does **not** execute it in this
  repository. The CI history of the structured repository remains on the
  structured branch history.
- **Nothing was edited to create this mirror.** No result was recomputed, no
  number was retyped, and no figure was re-rendered for the flat snapshot.

---

## 4. Reproducing and reversing the flat layout

Regenerate this snapshot from the structured tree with:

```bash
python tools/build_flat_mirror.py --dest <DEST_DIR>
```

`FLAT_FILEMAP.json` (and the JSON block inside `FLAT_FILE_INDEX.md`) records for
every file its flat name, original repo-relative path, byte size and SHA-256, so
you can verify any file you fetched is the one this snapshot describes, and you
can reconstruct the structured tree by inverting the mapping.

---

*Generated by `tools/build_flat_mirror.py`. Source repository tree:*
`{repo_slug}`
""",
        encoding="utf-8",
    )

    (out / "FLAT_LAYOUT.md").write_text(
        f"""# FLAT_LAYOUT.md — the folder-free layout is intentional

This repository deliberately has **no subdirectories**. All {len(entries)} files
(code, documentation, manuscript, report, figures, tables and core result data,
{total / 1e6:.2f} MB) live at the repository root.

## Why

1. **Machine readability.** A browsing LLM or another agent can list one
   directory and see the entire project, instead of walking a tree and risking
   missing an important artefact.
2. **Frictionless cross-review.** Reviewers can fetch any file by its flat name
   with a single request, without reconstructing paths.
3. **No hidden artefacts.** With no folders there is nowhere for a result file
   to hide behind an ignore rule, so everything that produced a reported number
   is visible in the same directory listing.

## Convention

`/` → `__`, space → `_`, `%` → `pct`. The complete, machine-readable
flat-name → original-path map (with byte sizes and SHA-256) is in
`FLAT_FILEMAP.json` and duplicated for humans in `FLAT_FILE_INDEX.md`.

## Consequences you should know about

- Python packages are not importable in this flat snapshot; run the pipeline and
  tests from the structured working tree (see `START_HERE_FLAT_LAYOUT.md` §3–4).
- GitHub Actions does not run here; the workflow file is published as
  `cisrc__workflows__ci.yml` for inspection.
- File contents are byte-identical to the structured source tree.

*Generated by `tools/build_flat_mirror.py`.*
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--dest", required=True, help="staging directory to create")
    ap.add_argument("--root", default=str(REPO_ROOT), help="structured source root")
    ap.add_argument("--repo-slug", default="https://github.com/Coucou2016/fmr-ima-layer1-planner")
    ap.add_argument("--dry-run", action="store_true", help="print plan, copy nothing")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    dest = Path(args.dest).resolve()

    entries = build_plan(root)
    total = sum(e["bytes"] for e in entries)
    print(f"planned flat files: {len(entries)}  ({total / 1e6:.2f} MB)")

    if args.dry_run:
        for e in entries:
            print(f"  {e['original']}  ->  {e['flat']}  ({e['bytes']} B)")
        print("dry run: nothing written")
        return 0

    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for e in entries:
        src = root / e["original"]
        e["sha256"] = sha256(src)
        shutil.copy2(src, dest / e["flat"])

    write_index(dest, entries, args.repo_slug)
    write_notice(dest, entries, args.repo_slug)

    (dest / "FLAT_FILEMAP.json").write_text(
        json.dumps(
            {
                "purpose": (
                    "Deliberate folder-free snapshot; key = flat root-level filename, "
                    "value = original repo-relative path, size and SHA-256"
                ),
                "source_repo": args.repo_slug,
                "separator": SEPARATOR,
                "sanitisation": {"space": "_", "%": "pct"},
                "n_files": len(entries),
                "total_bytes": total,
                "files": {
                    e["flat"]: {
                        "original_path": e["original"],
                        "bytes": e["bytes"],
                        "sha256": e["sha256"],
                        "group": e["group"],
                    }
                    for e in entries
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Minimal ignore rules: this snapshot intentionally tracks nearly everything.
    (dest / ".gitignore").write_text(
        "# Intentionally minimal: this snapshot is meant to be fully visible.\n"
        "__pycache__/\n*.py[cod]\n.pytest_cache/\n.ruff_cache/\n.mypy_cache/\n"
        ".coverage\n.coverage.*\nhtmlcov/\ncoverage.xml\n.DS_Store\nThumbs.db\n",
        encoding="utf-8",
    )

    dirs = [p for p in dest.iterdir() if p.is_dir()]
    print(f"staged {len(entries)} files -> {dest}")
    print(f"subdirectories in staging (must be 0): {len(dirs)}")
    if dirs:
        for d in dirs:
            print(f"  ! {d.name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
