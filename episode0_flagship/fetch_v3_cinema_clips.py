"""
Generates 3 targeted Full-HD `1080p` (`1920x1080`) AI Cinema B-Roll shots via `gemini-omni-1.1-flash`
specifically supporting David's v3 visual requests:
  1. `v3_sc05_dipping_soap_rings.mp4`:
       Two polished brass rings (one large, one tiny pinpoint ring) dipping into iridescent soapy fluid
       and pulling apart to stretch a glistening catenoid soap film between them.
  2. `v3_sc05_hubble_jwst_ancient_light.mp4`:
       Hubble and James Webb Space Telescopes in deep space peering out toward the glowing ancient
       Cosmic Microwave Background temperature sky map.
  3. `v3_sc09_deep_field_galaxies_zoom.mp4`:
       Continuous breathtaking cosmic zoom-out starting near one spiral galaxy and pulling back
       to reveal hundreds of luminous galaxies spanning deep space (for the ~10s Sagan Outro interlude).
"""

from __future__ import annotations

import base64
import os
import time
import winreg
from pathlib import Path
from typing import Optional

import httpx

EP0_DIR = Path(__file__).resolve().parent
CINEMA_DIR = EP0_DIR / "cinema_clips"
CINEMA_DIR.mkdir(parents=True, exist_ok=True)

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
TIMEOUT = httpx.Timeout(connect=15.0, read=300.0, write=30.0, pool=15.0)

V3_CLIPS = [
    (
        "v3_sc05_dipping_soap_rings.mp4",
        "Continuous, unbroken macro physics studio shot in moody dramatic lighting: two polished brushed-brass rings—one large outer ring and one very tiny inner ring—dip into a dark reflective dish of iridescent soapy liquid and smoothly pull apart, stretching a glistening, rainbow-shimmering catenoid soap film tightly between the large ring and the tiny pinpoint ring. Photorealistic 8k cinema. No dialogue. No text.",
    ),
    (
        "v3_sc05_hubble_jwst_ancient_light.mp4",
        "Continuous, unbroken awe-inspiring deep-space documentary shot gliding past the iconic golden hexagonal mirror of the James Webb Space Telescope and the silver Hubble Space Telescope orbiting in pitch-black space, peering outward toward a vast luminous cosmic horizon of the oldest light mottled in sapphire blue and warm golden temperature ripples. Photorealistic IMAX space cinema. No dialogue. No text.",
    ),
    (
        "v3_sc09_deep_field_galaxies_zoom.mp4",
        "Continuous, unbroken breathtaking cosmic camera pull-back starting near one majestic glowing spiral galaxy and zooming smoothly further and further out through deep space to reveal dozens, then hundreds of luminous spiral and golden elliptical galaxies glittering across the vast universe. Photorealistic Melodysheep IMAX space documentary. No dialogue. No text.",
    ),
]


def get_api_key() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, _ = winreg.QueryValueEx(k, "GEMINI_API_KEY")
            if val and str(val).strip():
                return str(val).strip()
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


def extract_video(payload: dict) -> tuple[Optional[str], Optional[str]]:
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


def main() -> None:
    api_key = get_api_key()
    assert api_key, "GEMINI_API_KEY missing"

    for idx, (fname, prompt) in enumerate(V3_CLIPS, start=1):
        out_p = CINEMA_DIR / fname
        if out_p.exists() and out_p.stat().st_size > 50_000:
            print(f"[{idx}/{len(V3_CLIPS)} SKIP] {fname} ({out_p.stat().st_size/1e6:.2f} MB)", flush=True)
            continue

        for res in ("1080p", "720p"):
            t0 = time.time()
            print(f"[{idx}/{len(V3_CLIPS)}] Requesting {fname} ({res})...", flush=True)
            body = {
                "model": "gemini-omni-1.1-flash",
                "input": prompt,
                "response_format": {
                    "type": "video",
                    "aspect_ratio": "16:9",
                    "resolution": res,
                    "duration": "10s",
                },
            }
            try:
                with httpx.Client(timeout=TIMEOUT) as client:
                    r = client.post(
                        INTERACTIONS_URL,
                        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                        json=body,
                    )
                    if r.status_code != 200:
                        print(f"[{idx}/{len(V3_CLIPS)}] HTTP {r.status_code} ({res}): {r.text[:200]}", flush=True)
                        if r.status_code == 429:
                            time.sleep(25.0)
                        continue
                    b64, uri = extract_video(r.json())
                    if b64:
                        raw = base64.b64decode(b64)
                    elif uri:
                        dl = client.get(uri, headers={"x-goog-api-key": api_key}, follow_redirects=True)
                        dl.raise_for_status()
                        raw = dl.content
                    else:
                        continue
                    out_p.write_bytes(raw)
                    print(f"[{idx}/{len(V3_CLIPS)} SAVED] {fname} ({res}, {len(raw)/1e6:.2f} MB) in {time.time()-t0:.1f}s", flush=True)
                    if idx < len(V3_CLIPS):
                        time.sleep(14.0)
                    break
            except Exception as exc:
                print(f"[{idx}/{len(V3_CLIPS)}] Exception ({res}): {exc}", flush=True)
                time.sleep(6.0)


if __name__ == "__main__":
    main()
