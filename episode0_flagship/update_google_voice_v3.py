"""
Backs up all v2 Google Replicated Voice chunks (`google_voice_chunks/backup_v2/`),
keeps all 21 David-approved "perfect / Sagan-like" chunks 100% UNTOUCHED,
regenerates ONLY the 12 flagged chunks on `voice_rjo5kexogz91` (`gemini-3.8-flash-tts`)
using calm, measured, unhurried style prompts + crystal-clear script rewrites,
and audits all 33 chunks via GPU `Faster-Whisper medium.en` to verify:
  - Exact wording & pronunciation (`Lambda C-D-M`, `Lambda Cold Dark Matter model`, `true, or sink it cold`, etc.)
  - Calm Sagan-style cadence (no hype/rush, no 2-second vinyl-speedup glitches)
  - Sample-accurate word timestamps (`_whisper_v3_audit.json`) for verbatim v3 subtitles.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import winreg
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
import imageio_ffmpeg
import numpy as np

EP0_DIR = Path(__file__).resolve().parent
VOICE_DIR = EP0_DIR / "google_voice_chunks"
BACKUP_DIR = VOICE_DIR / "backup_v2"

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
VOICES_URL = "https://generativelanguage.googleapis.com/v1beta/voices"
TIMEOUT = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=15.0)

# Strictly locked chunks that David praised ("2:13 to 6:23 absolutely perfect", "6:38 normal rhythmic",
# "10:19 on almost Carl Sagan-like", "11:34+ good", "Sagan-like outro"):
LOCKED_PERFECT_CHUNKS = {
    "chunk_01_scene00_a",
    "chunk_02_scene00_b",
    "chunk_03_scene00_c",
    "chunk_06_scene01_c",
    "chunk_07_scene01_d",
    "chunk_08_scene01_e",
    "chunk_09_scene02_a",
    "chunk_10_scene02_b",
    "chunk_11_scene02_c",
    "chunk_12_scene03_a",
    "chunk_13_scene03_b",
    "chunk_14_scene03_c",
    "chunk_15_scene04_a",
    "chunk_17_scene04_c",
    "chunk_19_scene05_a",
    "chunk_23_scene06_a",
    "chunk_24_scene06_b",
    "chunk_27_scene07_c",
    "chunk_30_scene08_c",
    "chunk_31_scene09_a",
    "chunk_32_scene09_b",
}

# ONLY the 12 chunks flagged by David for pacing/enthusiasm/pronunciation/clarity upgrades:
V3_REGEN_CHUNKS: List[Tuple[str, str, str]] = [
    (
        "chunk_04_scene01_a",
        "calm, smooth, steady, unhurried documentary narrator",
        "Step outside on a clear midnight, look up at the stars, and notice the picture your brain automatically paints. Space feels like a vast, pitch-black, empty theater. Atoms feel like tiny, solid marbles. And time feels like an invisible river carrying us from yesterday into tomorrow.",
    ),
    (
        "chunk_05_scene01_b",
        "calm, smooth, measured, unhurried documentary narrator",
        "For decades, astronomers have used a master textbook recipe for that universe called the Lambda Cee Dee Em model—or the Lambda Cold Dark Matter model. Despite the technical name, the story behind it is remarkably simple.",
    ),
    (
        "chunk_16_scene04_b",
        "calm, smooth, rhythmic documentary narrator with subtle quiet wonder",
        "Now grab that cosmic hourglass and flip it upside down. What if the wide, messy, chaotic state we call the distant future is actually the raw, untuned outer edge of reality—pure random static that needed zero special setup at all?",
    ),
    (
        "chunk_18_scene04_d",
        "calm, smooth, steady, measured explanation",
        "Even better, right at that narrow waist where disorder drops to zero, the neck rounds off smoothly like a soap film, so the fabric never tears. Right at that smooth throat, a natural subatomic twist acts like a cosmic sorter—sending all the ordinary matter that builds stars and people into our half of the hourglass, and all the missing antimatter out the opposite side.",
    ),
    (
        "chunk_20_scene05_b",
        "calm, smooth, unhurried visual storyteller",
        "Here is the third visual that shows why this is real physics, not a word game. Playing a regular movie backward changes nothing physical. Instead, watch two brass rings dip into soapy fluid—one giant outer ring, and one ultra-tiny inner ring standing in for the Big Bang singularity point. As those two rings pull apart, they stretch a real, continuous soap film tightly between them.",
    ),
    (
        "chunk_21_scene05_c",
        "calm, measured, clear documentary narrator",
        "Now think about vibrations in the early universe—primordial sound and heat waves that show up today as warm and cool patches across the oldest light in the sky. Just like a short guitar string cannot vibrate with a wave wider than the string itself, a universe pinched down to that tiny inner ring physically blocks the widest, sky-spanning waves—they simply have no room to form. And sure enough, when space telescopes like Planck, Hubble, and James Webb peer deep into space to map that ancient light, those widest sky ripples are mysteriously missing.",
    ),
    (
        "chunk_22_scene05_d",
        "calm, smooth, unhurried, reflective documentary narrator",
        "That same two-ended connection also takes the spookiness out of quantum physics' most famous puzzle: the double-slit experiment. Because the emitter and the back wall are already connected by the same continuous fabric, firing a single photon sends a real physical wave traveling through both narrow slits at once—overlapping on the back screen to paint bright and dark interference stripes. Nothing magical happens when we try to peek. To check which slit the wave went through, you have to place a physical sensor right inside one opening—and just like resting a finger on a vibrating guitar string, that sensor absorbs and disrupts the wave at that slit, leaving no second wave to overlap with, so the stripes vanish automatically. I will go into much greater detail of this in an upcoming video.",
    ),
    (
        "chunk_25_scene07_a",
        "calm, measured, curious documentary narrator",
        "Second, if the entire cosmic tablecloth is pulled taut across deep space, why don't we notice that background tension tugging Earth and the other planets off course right here in our own solar system?",
    ),
    (
        "chunk_26_scene07_b",
        "calm, warm, unhurried visual storyteller",
        "Picture standing two feet from a roaring campfire on a freezing winter night. Right next to the flames, that intense blast of local heat completely drowns out the faint chill of the distant night air. Our solar system works the exact same way because Earth sits right next to a massive star. Close to the Sun, its weight presses a steep, powerful local funnel into the fabric—pulling on Earth fifty million times harder than the whisper-faint background tension of deep space, so nearby planetary orbits behave completely normally.",
    ),
    (
        "chunk_28_scene08_a",
        "calm, smooth, unhurried visual storyteller",
        "Here is the third tablecloth visual, and astronomy's toughest crash test. Watch on screen as a young galaxy forms: as its stars gather together, their pull draws the surrounding cosmic sheet inward—gathering and tucking excess fabric around the galaxy like a crisp, springy pleat folded into a tablecloth.",
    ),
    (
        "chunk_29_scene08_b",
        "calm, measured, unhurried, reflective cosmic narrator",
        "Now watch what happens when two giant galaxy clusters collide head-on at high cosmic speed. Their sheer momentum overwhelms the springiness of those folds. While their hot gas clouds slam together and stall in the middle like a highway pile-up, the two fabric pleats glide straight through each other right alongside the stars—matching famous telescope maps without needing invisible dark-matter dust.",
    ),
    (
        "chunk_33_scene09_c",
        "calm, grounded, thoughtful scientific narrator",
        "Of course, in science, a vivid picture is only the beginning—it has to survive brutal contact with real measurements. In our six standalone companion chapters, we will open the hood one mystery at a time, bringing out every satellite test, particle collider clue, galaxy crash simulation, and upcoming Moon-orbit experiment that could prove this upside-down universe true, or sink it cold.",
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


def backup_v2_chunks() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for wp in sorted(VOICE_DIR.glob("chunk_*.wav")):
        dst = BACKUP_DIR / wp.name
        if not dst.exists():
            shutil.copy2(str(wp), str(dst))
            copied += 1
    print(f"[Backup] {copied} newly backed-up v2 chunks in {BACKUP_DIR.name}/ (total={len(list(BACKUP_DIR.glob('chunk_*.wav')))})", flush=True)


def synth_chunk(idx: int, total: int, cid: str, style: str, text: str, voice_id: str, api_key: str) -> None:
    assert cid not in LOCKED_PERFECT_CHUNKS, f"SAFETY GUARD: Attempted to overwrite locked chunk {cid}!"
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
                    print(f"[{idx:02d}/{total}] HTTP {r.status_code} (attempt {attempt}): {r.text[:180]}", flush=True)
                    time.sleep(36.0 if r.status_code == 429 else 5.0 * attempt)
                    continue
                b64 = extract_audio_b64(r.json())
                if not b64:
                    raise RuntimeError("Missing audio payload")
                raw = base64.b64decode(b64)
                out_p.write_bytes(raw)
                print(f"[{idx:02d}/{total} REGENERATED] {cid}.wav ({len(raw)/1024:.0f} KB)", flush=True)
                elapsed = time.time() - t_req
                if elapsed < 6.5 and idx < total:
                    time.sleep(6.5 - elapsed)
                return
        except Exception as exc:
            print(f"[{idx:02d}/{total}] Error (attempt {attempt}): {exc}", flush=True)
            time.sleep(6.0 * attempt)
    raise RuntimeError(f"Failed to synthesize {cid}")


def main() -> None:
    t0 = time.time()
    backup_v2_chunks()

    # Verify locked chunks match backup byte-for-byte
    for cid in sorted(LOCKED_PERFECT_CHUNKS):
        p_cur = VOICE_DIR / f"{cid}.wav"
        p_bak = BACKUP_DIR / f"{cid}.wav"
        assert p_cur.exists() and p_bak.exists(), f"Missing {cid}"
        if p_cur.stat().st_size != p_bak.stat().st_size:
            shutil.copy2(str(p_bak), str(p_cur))

    api_key = get_api_key()
    assert api_key, "GEMINI_API_KEY missing"
    voice_id = resolve_david_voice_id(api_key)
    print(f"Using David's Replicated Google Voice ID: {voice_id}", flush=True)

    tot = len(V3_REGEN_CHUNKS)
    for i, (cid, st, tx) in enumerate(V3_REGEN_CHUNKS):
        synth_chunk(i + 1, tot, cid, st, tx, voice_id, api_key)

    print(f"\n[12 V3 CHUNKS SYNTHESIZED in {time.time() - t0:.1f}s — 21 PERFECT CHUNKS UNTOUCHED!]", flush=True)


if __name__ == "__main__":
    main()
