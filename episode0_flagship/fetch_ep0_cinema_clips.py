"""
Cloud-only AI Cinema Video Fetcher for Flagship Episode 0 (0% local GPU / <1% CPU).
Calls the official Gemini Interactions REST endpoint (`POST /v1beta/interactions`) directly
via `httpx` so HTTP 429 (`Retry-After: 11621`) fails fast in <1s with a clear diagnostic
instead of triggering the SDK's silent multi-hour sleep loop.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import httpx

EP0_DIR = Path(__file__).resolve().parent
JOBS_FILE = EP0_DIR / "omni_cinema_jobs.json"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
TIMEOUT = httpx.Timeout(connect=15.0, read=210.0, write=30.0, pool=15.0)


def extract_video_b64_or_uri(payload: dict) -> tuple[Optional[str], Optional[str]]:
    # Top-level or nested inside steps[].content[]
    ov = payload.get("output_video")
    if isinstance(ov, dict):
        if ov.get("data"):
            return ov["data"], None
        if ov.get("uri"):
            return None, ov["uri"]
    for step in payload.get("steps") or []:
        if step.get("type") == "model_output":
            for item in step.get("content") or []:
                if item.get("type") == "video":
                    if item.get("data"):
                        return item["data"], None
                    if item.get("uri"):
                        return None, item["uri"]
    return None, None


def fetch_one(idx: int, total: int, job: dict, api_key: str) -> tuple[bool, str]:
    out_path = Path(job["output"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 20_000:
        mb = out_path.stat().st_size / 1e6
        msg = f"[{idx}/{total}] SKIP (already exists): {out_path.name} ({mb:.2f} MB)"
        print(msg, flush=True)
        return True, msg

    rf: dict = {"type": "video", "aspect_ratio": job.get("aspect_ratio", "16:9")}
    if job.get("resolution"):
        rf["resolution"] = job["resolution"]
    if job.get("duration"):
        rf["duration"] = job["duration"]
    body = {
        "model": "gemini-omni-1.1-flash",
        "input": job["prompt"],
        "response_format": rf,
    }

    for attempt in (1, 2):
        t0 = time.time()
        print(f"[{idx}/{total}] Requesting {out_path.name} (attempt {attempt})...", flush=True)
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                r = client.post(
                    INTERACTIONS_URL,
                    headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                    json=body,
                )
                dt = time.time() - t0
                if r.status_code != 200:
                    err_txt = r.text[:400].replace("\n", " ")
                    msg = f"[{idx}/{total}] HTTP {r.status_code} in {dt:.1f}s for {out_path.name}: {err_txt}"
                    print(msg, flush=True)
                    # Do NOT sleep/retry on Free-Tier quota=0 or 401/403!
                    if r.status_code in (400, 401, 403) or "Free Tier" in r.text or "limit: 0" in r.text:
                        return False, msg
                    if attempt == 1:
                        time.sleep(5.0)
                        continue
                    return False, msg

                data = r.json()
                b64_data, uri = extract_video_b64_or_uri(data)
                if b64_data:
                    raw = base64.b64decode(b64_data)
                elif uri:
                    dl = client.get(uri, headers={"x-goog-api-key": api_key}, follow_redirects=True)
                    dl.raise_for_status()
                    raw = dl.content
                else:
                    raise RuntimeError(f"200 OK but no video in steps (status={data.get('status')})")

                out_path.write_bytes(raw)
                msg = f"[{idx}/{total}] SAVED {out_path.name} ({len(raw)/1e6:.2f} MB) in {time.time()-t0:.1f}s"
                print(msg, flush=True)
                return True, msg
        except Exception as exc:
            dt = time.time() - t0
            print(f"[{idx}/{total}] Exception after {dt:.1f}s: {type(exc).__name__}: {exc}", flush=True)
            if attempt == 2:
                return False, f"[{idx}/{total}] FAILED {out_path.name}: {type(exc).__name__}"
            time.sleep(3.0)
    return False, f"[{idx}/{total}] FAILED {out_path.name}"


def get_fresh_api_key() -> str:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, _ = winreg.QueryValueEx(k, "GEMINI_API_KEY")
            if val and str(val).strip():
                return str(val).strip()
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


def main() -> None:
    api_key = get_fresh_api_key()
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set.", flush=True)
        sys.exit(1)

    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    total = len(jobs)

    # Preflight check on Job 1 first so we fail fast in <1s if project is still on Free Tier!
    ok0, msg0 = fetch_one(1, total, jobs[0], api_key)
    if not ok0 and ("Free Tier" in msg0 or "limit: 0" in msg0 or "HTTP 401" in msg0 or "HTTP 403" in msg0):
        print("\n[FAST-FAIL] Stopping immediately instead of hanging: API key project is still on Free Tier.", flush=True)
        sys.exit(2)

    t_start = time.time()
    print(f"Preflight succeeded! Fetching remaining {total - 1} clips (2 gentle cloud workers)...", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fetch_one, i + 1, total, jobs[i], api_key) for i in range(1, total)]
        results = [ok0] + [f.result()[0] for f in as_completed(futs)]

    n_ok = sum(1 for x in results if x)
    print(f"Finished: {n_ok}/{total} AI cinema clips ready in {time.time() - t_start:.1f}s.", flush=True)
    if n_ok < total:
        sys.exit(3)


if __name__ == "__main__":
    main()
