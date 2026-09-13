#!/usr/bin/env python3
"""Download Dryad files behind Anubis PoW (techaro BotStopper).

Solves the embedded fast SHA-256 challenge, stores the auth cookie, then
pulls the two Galili zips into data/raw/galili_dryad/.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar, MozillaCookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "galili_dryad"
COOKIE_PATH = ROOT / "data" / "raw" / "_anubis" / "cookies.txt"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
BASE = "https://datadryad.org"
LANDING = BASE + "/dataset/doi:10.5061/dryad.bzkh1899d"
FILES = {
    "Deformed_coordinates_and_contact.zip": 1226888,
    "Blood_leakage_-_SPH_coordinates.zip": 1226889,
}


def _opener(cj: CookieJar) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def _request(
    opener: urllib.request.OpenerDirector,
    url: str,
    *,
    timeout: float = 180,
    method: str | None = None,
) -> tuple[bytes, str, str, list[tuple[str, str]]]:
    headers = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": LANDING,
    }
    req = urllib.request.Request(url, headers=headers, method=method)
    with opener.open(req, timeout=timeout) as resp:
        body = resp.read()
        ctype = str(resp.headers.get("Content-Type") or "")
        final = resp.geturl()
        hdrs = [(k, v) for k, v in resp.headers.items()]
        return body, ctype, final, hdrs


def _extract_challenge(html: str) -> dict:
    m = re.search(
        r'<script id="anubis_challenge" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if not m:
        raise RuntimeError("anubis_challenge JSON not found in HTML")
    wrap = json.loads(m.group(1))
    chal = wrap.get("challenge") or wrap
    rules = wrap.get("rules") or {}
    return {
        "id": chal["id"],
        "randomData": chal["randomData"],
        "difficulty": int(chal.get("difficulty") or rules.get("difficulty") or 4),
        "method": chal.get("method") or rules.get("algorithm") or "fast",
    }


def solve_pow(random_data: str, difficulty: int) -> tuple[int, str, int]:
    prefix = "0" * difficulty
    t0 = time.time()
    nonce = 0
    while True:
        digest = hashlib.sha256(f"{random_data}{nonce}".encode()).hexdigest()
        if digest.startswith(prefix):
            elapsed_ms = int((time.time() - t0) * 1000)
            return nonce, digest, elapsed_ms
        nonce += 1
        if nonce > 16_000_000:
            raise RuntimeError("PoW search exceeded 16M nonces")


def ensure_auth_cookie(opener: urllib.request.OpenerDirector, cj: CookieJar) -> None:
    # Hit a protected download URL to obtain a challenge page.
    probe_url = f"{BASE}/downloads/file_stream/{next(iter(FILES.values()))}"
    body, ctype, final, _ = _request(opener, probe_url, timeout=60)
    if body[:2] == b"PK":
        return
    text = body.decode("utf-8", "replace")
    if "anubis_challenge" not in text and "Validating" not in text:
        # Maybe already authorized or unexpected HTML.
        names = {c.name for c in cj}
        if any("anubis" in n for n in names):
            return
        raise RuntimeError(
            f"Unexpected probe response ctype={ctype} final={final} head={body[:80]!r}"
        )

    chal = _extract_challenge(text)
    print(
        f"Solving Anubis PoW id={chal['id']} difficulty={chal['difficulty']} ...",
        flush=True,
    )
    nonce, digest, elapsed_ms = solve_pow(chal["randomData"], chal["difficulty"])
    print(f"Solved nonce={nonce} hash={digest} elapsed_ms={elapsed_ms}", flush=True)

    pass_url = (
        BASE
        + "/.within.website/x/cmd/anubis/api/pass-challenge?"
        + urllib.parse.urlencode(
            {
                "id": chal["id"],
                "response": digest,
                "nonce": str(nonce),
                "redir": probe_url,
                "elapsedTime": str(max(elapsed_ms, 1)),
            }
        )
    )
    body2, ctype2, final2, _ = _request(opener, pass_url, timeout=120)
    names = [(c.name, (c.value[:48] + "…") if len(c.value) > 48 else c.value) for c in cj]
    print(f"After pass-challenge: ctype={ctype2} final={final2[:160]} cookies={names}", flush=True)
    if not any("anubis" in c.name for c in cj):
        # Some deployments set cookie only on Set-Cookie of intermediate redirect.
        # Save debug HTML.
        dbg = ROOT / "data" / "raw" / "_anubis" / "after_pass.html"
        dbg.parent.mkdir(parents=True, exist_ok=True)
        dbg.write_bytes(body2[:200_000])
        raise RuntimeError("No anubis auth cookie after pass-challenge; see after_pass.html")


def download_file(
    opener: urllib.request.OpenerDirector,
    file_id: int,
    dest: Path,
) -> dict:
    url = f"{BASE}/downloads/file_stream/{file_id}"
    print(f"Downloading {dest.name} from {url} ...", flush=True)
    body, ctype, final, _ = _request(opener, url, timeout=600)
    if body[:2] != b"PK":
        if b"anubis_challenge" in body[:5000] or b"Validating" in body[:2000]:
            raise RuntimeError(f"Still blocked by Anubis for {dest.name}")
        raise RuntimeError(
            f"Not a zip for {dest.name}: ctype={ctype} final={final} head={body[:80]!r}"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    sha = hashlib.sha256(body).hexdigest()
    info = {
        "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "bytes": len(body),
        "sha256": sha,
        "content_type": ctype,
        "final_url": final,
        "file_id": file_id,
        "source": "dryad_file_stream_after_anubis_pow",
    }
    print(f"Saved {dest} ({len(body)} bytes, sha256={sha})", flush=True)
    return info


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "raw" / "_anubis").mkdir(parents=True, exist_ok=True)

    cj = CookieJar()
    opener = _opener(cj)
    report: dict = {"status": "attempted", "files": {}, "errors": []}

    try:
        ensure_auth_cookie(opener, cj)
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"auth: {exc}")
        print(f"AUTH FAILED: {exc}", file=sys.stderr)
        (ROOT / "data" / "raw" / "_anubis" / "download_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        return 2

    # Persist cookies for reuse / debugging.
    try:
        mcj = MozillaCookieJar(str(COOKIE_PATH))
        for c in cj:
            mcj.set_cookie(c)
        mcj.save(ignore_discard=True, ignore_expires=True)
    except Exception as exc:  # noqa: BLE001
        report["cookie_save_error"] = str(exc)

    any_ok = False
    for name, fid in FILES.items():
        dest = RAW / name
        try:
            report["files"][name] = download_file(opener, fid, dest)
            any_ok = True
        except Exception as exc:  # noqa: BLE001
            report["files"][name] = {"status": "failed", "error": str(exc), "file_id": fid}
            report["errors"].append(f"{name}: {exc}")
            print(f"FAILED {name}: {exc}", file=sys.stderr)

    report["status"] = "ok" if any_ok and not report["errors"] else ("partial" if any_ok else "failed")
    out = ROOT / "data" / "raw" / "_anubis" / "download_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Wrote", out)
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
