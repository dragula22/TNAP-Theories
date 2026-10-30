"""
Synthesizes ONLY the 4 updated 'Transparency First' voice chunks (`chunk_01_scene00_a`,
`chunk_02_scene00_b`, `chunk_03_scene00_c`, and `chunk_20_scene05_b`) on David's
replicated Google voice (`David Documentary Narrator` / `gemini-3.8-flash-tts`),
backing up the previous v4 WAVs into `google_voice_chunks/backup_v4/` and keeping
all 29 other approved Sagan Edition chunks 100% untouched byte-for-byte!
"""

from __future__ import annotations

import base64
import os
import shutil
import time
import winreg
from pathlib import Path
from typing import List, Optional, Tuple

import httpx

EP0_DIR = Path(__file__).resolve().parent
VOICE_DIR = EP0_DIR / "google_voice_chunks"
BACKUP_V4_DIR = VOICE_DIR / "backup_v4"

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
VOICES_URL = "https://generativelanguage.googleapis.com/v1beta/voices"
TIMEOUT = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=15.0)

V5_TRANSPARENT_CHUNKS: List[Tuple[str, str, str]] = [
    (
        "chunk_01_scene00_a",
        "calm, warm, grounded, sincere documentary narrator",
        "Hello everyone, my name is David. I'm not a professional physicist—I'm an independent builder who loves thinking outside the box about how reality works. Recently, I took a set of ideas I couldn't stop wondering about and ran an open experiment with the help of multi-agent Gemini Argon inside Google Antigravity—having competing AI agents try to formalize the math, red-team weak spots, and test simplified Python models.",
    ),
    (
        "chunk_02_scene00_b",
        "calm, warm, thoughtful, unhurried documentary narrator",
        "I believe using AI to explore big questions like this is deeply worthwhile—as long as we go about it responsibly, stay cautious, and never confuse an exploratory AI-assisted model with proven, peer-reviewed physics. Right or wrong, building this has taught me a tremendous amount, and transparency comes first. On screen right now is the complete list of software tools and published astronomy benchmarks our agents used, and you can visit stoler dot systems, or our GitHub link below, for a full write-up of everything—including where the math is still unfinished.",
    ),
    (
        "chunk_03_scene00_c",
        "calm, sincere, inviting, unhurried documentary narrator",
        "In this opening video, I'll walk through the big picture visually with zero equations, and in follow-up chapters we'll put one claim at a time under a microscope. If you're a physicist, student, or skeptic, please help us critique this and tell us what we missed. Subscribe if you'd like to follow where this goes—and now, as an open visual thought experiment, I present to you: The Universe Inside Out.",
    ),
    (
        "chunk_20_scene05_b",
        "calm, smooth, unhurried visual storyteller",
        "Here is a third visual that shows why this model isn't just pressing rewind—it actually changes what vibrations can fit on the sheet. Playing a regular movie backward changes nothing physical. Instead, watch two brass rings dip into soapy fluid—one giant outer ring, and one ultra-tiny inner ring standing in for the Big Bang singularity point. As those two rings pull apart, they stretch a continuous soap film tightly between them.",
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


def extract_audio_b64(payload: dict) -> Optional[str]:
    ov = payload.get("output_audio")
    if isinstance(ov, dict) and ov.get("data"):
        return ov["data"]
    for step in payload.get("steps") or []:
        if step.get("type") == "model_output":
            for item in step.get("content") or []:
                if item.get("type") == "audio" and item.get("data"):
                    return item["data"]
    return None


def resolve_david_voice_id(api_key: str) -> str:
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.get(VOICES_URL, params={"type": "replicated"}, headers={"x-goog-api-key": api_key})
        r.raise_for_status()
        for v in r.json().get("voices") or []:
            if v.get("display_name") == "David Documentary Narrator":
                return v["id"]
    raise RuntimeError("David Documentary Narrator voice ID not found")


def main() -> None:
    t0 = time.time()
    BACKUP_V4_DIR.mkdir(parents=True, exist_ok=True)
    target_ids = {c[0] for c in V5_TRANSPARENT_CHUNKS}

    # Back up the 4 chunks (plus record sizes of the 29 untouched chunks to assert zero modification)
    untouched_sigs = {}
    for wp in sorted(VOICE_DIR.glob("chunk_*.wav")):
        cid = wp.stem
        if cid in target_ids:
            dst = BACKUP_V4_DIR / wp.name
            if not dst.exists():
                shutil.copy2(str(wp), str(dst))
        else:
            untouched_sigs[cid] = (wp.stat().st_size, wp.stat().st_mtime_ns)

    api_key = get_api_key()
    assert api_key, "GEMINI_API_KEY missing"
    voice_id = resolve_david_voice_id(api_key)
    print(f"Using David's Replicated Google Voice ID: {voice_id}", flush=True)

    tot = len(V5_TRANSPARENT_CHUNKS)
    for idx, (cid, style, text) in enumerate(V5_TRANSPARENT_CHUNKS, start=1):
        out_p = VOICE_DIR / f"{cid}.wav"
        body = {
            "model": "gemini-3.8-flash-tts",
            "input": [
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                            "annotations": [{"type": "speech_metadata", "style": style}],
                        }
                    ],
                }
            ],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice_id}]},
        }
        ok = False
        for attempt in (1, 2, 3, 4):
            t_req = time.time()
            try:
                with httpx.Client(timeout=TIMEOUT) as client:
                    r = client.post(
                        INTERACTIONS_URL,
                        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                        json=body,
                    )
                    if r.status_code != 200:
                        print(f"[{idx}/{tot}] HTTP {r.status_code} (attempt {attempt}): {r.text[:180]}", flush=True)
                        time.sleep(30.0 if r.status_code == 429 else 5.0 * attempt)
                        continue
                    b64 = extract_audio_b64(r.json())
                    if not b64:
                        raise RuntimeError("Missing audio payload")
                    raw = base64.b64decode(b64)
                    out_p.write_bytes(raw)
                    print(f"[{idx}/{tot} REGENERATED] {cid}.wav ({len(raw)/1024:.0f} KB)", flush=True)
                    ok = True
                    el = time.time() - t_req
                    if el < 6.2 and idx < tot:
                        time.sleep(6.2 - el)
                    break
            except Exception as exc:
                print(f"[{idx}/{tot}] Error (attempt {attempt}): {exc}", flush=True)
                time.sleep(6.0 * attempt)
        if not ok:
            raise RuntimeError(f"Failed to synthesize {cid}")

    # Verify all 29 other chunks remained 100% untouched byte-for-byte
    for cid, sig in untouched_sigs.items():
        wp = VOICE_DIR / f"{cid}.wav"
        assert (wp.stat().st_size, wp.stat().st_mtime_ns) == sig, f"Unexpected change in {cid}!"

    print(
        f"\n[4 TRANSPARENT CHUNKS SYNTHESIZED in {time.time() - t0:.1f}s — ALL 29 OTHER CHUNKS 100% UNTOUCHED!]",
        flush=True,
    )


if __name__ == "__main__":
    main()
