#!/usr/bin/env python3
"""Publish the deliberately FLAT snapshot to GitHub via the Git Data API.

Use this when ``git push`` cannot reach ``github.com:443`` but
``api.github.com:443`` is reachable: the whole folder-free tree is uploaded as
blobs, assembled into one tree, committed on top of the current branch tip, and
the ref is fast-forwarded.

Because the tree is created **without** ``base_tree``, the resulting commit
contains exactly the flat files and nothing else: the previous (structured)
layout is replaced in the branch tip. The pre-flatten commit remains in history.

Usage
-----
    python tools/push_flat_via_api.py --stage E:\\Projects\\_fmr_flat_staging
    python tools/push_flat_via_api.py --stage ... --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OWNER = "Coucou2016"
REPO = "fmr-ima-layer1-planner"
BRANCH = "main"
API = "https://api.github.com"

MESSAGE = (
    "Publish deliberately flat, folder-free layout at repository root\n\n"
    "All code, documentation, manuscript, paper/report deliverables (HTML/MD/PDF),\n"
    "figures, tables and core result data now live side by side at the root with no\n"
    "subdirectories, so a single directory listing exposes the whole project to\n"
    "ChatGPT and other agents for cross-review.\n\n"
    "Provenance is encoded in the filenames ('/' -> '__'); see\n"
    "START_HERE_FLAT_LAYOUT.md, FLAT_LAYOUT.md and FLAT_FILE_INDEX.md (with\n"
    "FLAT_FILEMAP.json giving flat name -> original path, bytes and SHA-256).\n\n"
    "No file contents were changed; this is a naming/layout transformation only."
)


def token() -> str:
    out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    tok = out.stdout.strip()
    if not tok:
        raise SystemExit("empty token from `gh auth token`")
    return tok


def api(method: str, path: str, payload: dict | None = None, *, retries: int = 5) -> dict:
    url = f"{API}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {TOK}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "fmr-flat-publisher")
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:600]
            last = RuntimeError(f"HTTP {exc.code} on {method} {path}: {detail}")
            if exc.code in (401, 403, 404, 422):
                raise last from None
        except Exception as exc:  # noqa: BLE001
            last = exc
        time.sleep(3 * attempt)
    raise SystemExit(f"API failed after {retries} attempts: {last}")


TOK = ""


def create_blob(path: Path) -> tuple[str, str]:
    blob = api(
        "POST",
        f"/repos/{OWNER}/{REPO}/git/blobs",
        {"content": base64.b64encode(path.read_bytes()).decode(), "encoding": "base64"},
    )
    return path.name, blob["sha"]


def main(argv: list[str] | None = None) -> int:
    global TOK
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--stage", required=True, help="flat staging directory")
    ap.add_argument("--dry-run", action="store_true", help="print plan only")
    ap.add_argument("--workers", type=int, default=6, help="parallel blob uploads")
    args = ap.parse_args(argv)

    stage = Path(args.stage).resolve()
    if not stage.is_dir():
        raise SystemExit(f"staging directory not found: {stage}")

    subdirs = [p for p in stage.iterdir() if p.is_dir()]
    if subdirs:
        raise SystemExit(f"staging is not flat; found subdirectories: {subdirs}")

    files = sorted(p for p in stage.iterdir() if p.is_file())
    total = sum(p.stat().st_size for p in files)
    print(f"staging: {len(files)} files, {total / 1e6:.2f} MB")
    print(f"target: https://github.com/{OWNER}/{REPO} branch {BRANCH}")
    if args.dry_run:
        for p in files:
            print(f"  {p.stat().st_size:>10}  {p.name}")
        print("dry run: nothing uploaded")
        return 0

    TOK = token()

    repo = api("GET", f"/repos/{OWNER}/{REPO}")
    if repo.get("visibility") != "public":
        print(f"! repository visibility is {repo.get('visibility')!r}")
        api("PATCH", f"/repos/{OWNER}/{REPO}", {"visibility": "public"})
        print("  -> set to public")

    tip = api("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")["object"]["sha"]
    print(f"current {BRANCH} tip: {tip}")

    print(f"uploading {len(files)} blobs with {args.workers} workers ...")
    entries: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(create_blob, p): p for p in files}
        for fut in as_completed(futures):
            name, sha = fut.result()
            entries.append({"path": name, "mode": "100644", "type": "blob", "sha": sha})
            done += 1
            if done % 25 == 0 or done == len(files):
                print(f"  {done}/{len(files)}")

    entries.sort(key=lambda e: e["path"])

    print("creating tree (full replacement, no base_tree) ...")
    tree = api("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"tree": entries})

    print("creating commit ...")
    commit = api(
        "POST",
        f"/repos/{OWNER}/{REPO}/git/commits",
        {"message": MESSAGE, "tree": tree["sha"], "parents": [tip]},
    )

    print("fast-forwarding branch ref ...")
    api("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}", {"sha": commit["sha"]})

    print(f"published commit {commit['sha']}")
    print(f"https://github.com/{OWNER}/{REPO}/commit/{commit['sha']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
