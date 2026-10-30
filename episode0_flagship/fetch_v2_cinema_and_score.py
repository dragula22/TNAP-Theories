"""
Cloud Asset Fetcher for Flagship Episode 0 v2 (1080p Cinema Overhaul):
  1. Generates 4 full-length instrumental cinematic documentary movements via Google `lyria-3.5`
  2. Generates 12 new Full-HD `1080p` (`1920x1080`) AI Cinema B-roll shots via `gemini-omni-1.1-flash`
     (bringing our total cinema library to 21 distinct shots — 2+ angles per chapter + Cold-Open Hook!)
  3. Registers & synthesizes a test sample of David's voice on Google's `gemini-3.8-flash-tts`
     Voice Replication API (using his recorded consent clip + clean studio reference take)
     so he can compare Google's cloud voice model alongside his 100% real-voice Episode 0!
"""

from __future__ import annotations

import base64
import os
import time
import wave
import winreg
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import httpx
import numpy as np

EP0_DIR = Path(__file__).resolve().parent
CINEMA_DIR = EP0_DIR / "cinema_clips"
SCORE_DIR = EP0_DIR / "score_stems"
CINEMA_DIR.mkdir(parents=True, exist_ok=True)
SCORE_DIR.mkdir(parents=True, exist_ok=True)

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
VOICES_URL = "https://generativelanguage.googleapis.com/v1beta/voices"
TIMEOUT = httpx.Timeout(connect=15.0, read=240.0, write=30.0, pool=15.0)


def get_api_key() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, _ = winreg.QueryValueEx(k, "GEMINI_API_KEY")
            if val and str(val).strip():
                return str(val).strip()
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


LYRIA_TRACKS = [
    (
        "score_01_wonder_hook.mp3",
        "Awe-inspiring modern space documentary soundtrack inspired by Interstellar and Melodysheep: deep warm sub-bass pulse, delicate felt piano arpeggios, shimmering glass synthesizer pads, swelling solo cello and warm cathedral pipe organ building wonder. Instrumental only, strictly no vocals, no singing.",
    ),
    (
        "score_02_timeless_groove.mp3",
        "Contemplative minimalist science documentary underscore in D minor: warm analog synthesizer pad, soft marimba and celesta pulses like timeless clockwork, weightless legato strings and deep gentle bass notes. Instrumental only, strictly no vocals, no singing.",
    ),
    (
        "score_03_cosmic_tension.mp3",
        "Majestic cosmic discovery film score: deep resonant contrabass, shimmering harp harmonics, warm French horn swells, and subtle modern electronic pulse evoking vast spiral galaxies in deep space. Instrumental only, strictly no vocals, no singing.",
    ),
    (
        "score_04_grand_horizon.mp3",
        "Transcendent cinematic documentary finale score: soaring warm orchestral strings, gentle felt piano melody, glowing atmospheric synth pad, hopeful and expansive resolution. Instrumental only, strictly no vocals, no singing.",
    ),
]

NEW_1080P_CLIPS = [
    (
        "v2_hook01_galaxy_shatter.mp4",
        "Continuous, unbroken dramatic fast camera push-in toward a blazing spiral galaxy in deep pitch-black space, brilliant golden core and luminous sapphire outer spiral arms spinning rapidly amidst thousands of pinpoint stars, IMAX space documentary cinematography. No dialogue. No text.",
    ),
    (
        "v2_hook02_hourglass_flip.mp4",
        "Continuous, unbroken epic close-up of a monumental crystal and brushed-brass cosmic hourglass suspended in a glowing deep-space nebula, smoothly rotating 180 degrees upside down as swirling stardust funnels into a calm, mirror-smooth golden waist. Photorealistic IMAX cinema. No dialogue. No text.",
    ),
    (
        "v2_sc00_jwst_observatory.mp4",
        "Continuous, unbroken sweeping orbital shot gliding past the gleaming golden hexagonal mirror segments of the James Webb Space Telescope in deep space, reflecting distant colorful deep-field galaxies across the golden mirrors. Photorealistic space documentary. No dialogue. No text.",
    ),
    (
        "v2_sc01_dark_scaffolding.mp4",
        "Continuous, unbroken wide cosmic camera pull-back starting near a bright spiral galaxy and zooming out to reveal a vast, glowing indigo and violet three-dimensional web of cosmic filaments spanning the dark universe, Melodysheep documentary aesthetic. No dialogue. No text.",
    ),
    (
        "v2_sc02_knot_in_silk.mp4",
        "Continuous, unbroken extreme macro tracking shot gliding low across a drum-tight luminous cyan and gold silk weave in pitch-black space as three glowing threads braid themselves smoothly into a shimmering 3D trefoil knot sliding effortlessly along the fabric. No dialogue. No text.",
    ),
    (
        "v2_sc03_ink_in_water.mp4",
        "Continuous, unbroken ultra-slow-motion macro shot in a moody dark studio as a single luminous drop of golden and cyan ink falls into crystal-clear water and blooms into intricate, delicate swirling tendrils, shallow depth of field. No dialogue. No text.",
    ),
    (
        "v2_sc04_twin_wings.mp4",
        "Continuous, unbroken wide cinematic camera orbit around a glowing two-winged cosmic hourglass in deep space: cool sapphire spiral galaxies swirling in one wing and warm rose-gold mirror galaxies swirling symmetrically in the opposite wing across a smooth golden central waist. No dialogue. No text.",
    ),
    (
        "v2_sc05_laser_slits.mp4",
        "Continuous, unbroken moody dark physics laboratory tracking shot following shimmering cyan water-and-light ripples passing simultaneously through two narrow polished brass slits and painting crisp bright emerald interference stripes on a translucent screen. No dialogue. No text.",
    ),
    (
        "v2_sc06_starlight_bend.mp4",
        "Continuous, unbroken cinematic space shot skimming past the corona of a blazing golden star as a crisp beam of distant starlight visibly curves along the warped space around the star toward a blue ocean planet in the foreground. No dialogue. No text.",
    ),
    (
        "v2_sc07_spiral_outskirts.mp4",
        "Continuous, unbroken smooth cosmic camera zoom-out starting close to a blazing yellow sun surrounded by fast-orbiting inner planets and pulling far out into the serene, glowing sapphire outer spiral arms of a vast galaxy. No dialogue. No text.",
    ),
    (
        "v2_sc08_slow_dwarf_bounce.mp4",
        "Continuous, unbroken wide space documentary shot of two delicate, diffuse dwarf galaxies drifting gently toward each other in deep space; their translucent violet halo ripples compress and bounce cleanly apart in the center while their golden stars coast onward. No dialogue. No text.",
    ),
    (
        "v2_sc09_cislunar_probe.mp4",
        "Continuous, unbroken breathtaking orbital shot between a glowing blue crescent Earth and the sunlit cratered Moon in silent black space as a sleek golden scientific micro-satellite floats gently into the zero-gravity balance point between them. No dialogue. No text.",
    ),
]


def extract_media_b64_or_uri(payload: dict, media_type: str) -> tuple[Optional[str], Optional[str]]:
    top_key = f"output_{media_type}"
    ov = payload.get(top_key)
    if isinstance(ov, dict):
        if ov.get("data"):
            return ov["data"], None
        if ov.get("uri"):
            return None, ov["uri"]
    for step in payload.get("steps") or []:
        if step.get("type") == "model_output":
            for item in step.get("content") or []:
                if item.get("type") == media_type:
                    if item.get("data"):
                        return item["data"], None
                    if item.get("uri"):
                        return None, item["uri"]
    return None, None


def fetch_lyria_track(fname: str, prompt: str, api_key: str) -> str:
    out_p = SCORE_DIR / fname
    if out_p.exists() and out_p.stat().st_size > 30_000:
        msg = f"[Music SKIP] {fname} ({out_p.stat().st_size/1e6:.2f} MB)"
        print(msg, flush=True)
        return msg

    for model_id in ("lyria-3.5", "lyria-3-clip-preview"):
        t0 = time.time()
        print(f"[Music] Requesting {fname} via {model_id}...", flush=True)
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                r = client.post(
                    INTERACTIONS_URL,
                    headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                    json={"model": model_id, "input": prompt},
                )
                if r.status_code != 200:
                    print(f"[Music] {model_id} HTTP {r.status_code}: {r.text[:220]}", flush=True)
                    continue
                b64, uri = extract_media_b64_or_uri(r.json(), "audio")
                if b64:
                    raw = base64.b64decode(b64)
                elif uri:
                    dl = client.get(uri, headers={"x-goog-api-key": api_key}, follow_redirects=True)
                    dl.raise_for_status()
                    raw = dl.content
                else:
                    continue
                out_p.write_bytes(raw)
                msg = f"[Music SAVED] {fname} ({len(raw)/1e6:.2f} MB) via {model_id} in {time.time()-t0:.1f}s"
                print(msg, flush=True)
                return msg
        except Exception as exc:
            print(f"[Music] {model_id} error: {type(exc).__name__}: {exc}", flush=True)
    return f"[Music FAILED] {fname}"


def fetch_cinema_1080p(idx: int, total: int, fname: str, prompt: str, api_key: str) -> str:
    out_p = CINEMA_DIR / fname
    if out_p.exists() and out_p.stat().st_size > 30_000:
        msg = f"[Clip {idx}/{total} SKIP] {fname} ({out_p.stat().st_size/1e6:.2f} MB)"
        print(msg, flush=True)
        return msg

    body = {
        "model": "gemini-omni-1.1-flash",
        "input": prompt,
        "response_format": {
            "type": "video",
            "aspect_ratio": "16:9",
            "resolution": "1080p",
            "duration": "10s",
        },
    }
    for attempt in (1, 2):
        t0 = time.time()
        print(f"[Clip {idx}/{total}] Requesting 1080p {fname} (attempt {attempt})...", flush=True)
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                r = client.post(
                    INTERACTIONS_URL,
                    headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                    json=body,
                )
                if r.status_code != 200:
                    print(f"[Clip {idx}/{total}] HTTP {r.status_code}: {r.text[:240]}", flush=True)
                    if attempt == 1:
                        wait_s = 38.0 if r.status_code == 429 else 5.0
                        print(f"[Clip {idx}/{total}] Waiting {wait_s:.0f}s for spend-rate window...", flush=True)
                        time.sleep(wait_s)
                        continue
                    return f"[Clip {idx}/{total} FAILED] {fname}"
                b64, uri = extract_media_b64_or_uri(r.json(), "video")
                if b64:
                    raw = base64.b64decode(b64)
                elif uri:
                    dl = client.get(uri, headers={"x-goog-api-key": api_key}, follow_redirects=True)
                    dl.raise_for_status()
                    raw = dl.content
                else:
                    raise RuntimeError("No video payload in response")
                out_p.write_bytes(raw)
                msg = f"[Clip {idx}/{total} SAVED] {fname} ({len(raw)/1e6:.2f} MB) in {time.time()-t0:.1f}s"
                print(msg, flush=True)
                return msg
        except Exception as exc:
            print(f"[Clip {idx}/{total}] Attempt {attempt} exception: {type(exc).__name__}: {exc}", flush=True)
            if attempt == 1:
                time.sleep(3.0)
    return f"[Clip {idx}/{total} FAILED] {fname}"


def test_google_voice_replication(api_key: str) -> None:
    """Tests Google's `gemini-3.8-flash-tts` Voice Replication using David's recorded consent + clean 24k chunk."""
    consent_p = Path(r"c:\Projects\Discovery\voice_studio\recordings\take_06_cloud_consent_optional_24k.wav")
    ref_48k_p = EP0_DIR / "my_narration" / "chunk_04_scene01_a.wav"
    audition_out = Path(r"c:\Projects\Discovery\voice_studio\google_gemini_replicated_voice_audition.wav")
    if not consent_p.exists() or not ref_48k_p.exists():
        print("[VoiceRep] Consent or reference WAV missing, skipping optional cloud voice test.", flush=True)
        return
    if audition_out.exists() and audition_out.stat().st_size > 20_000:
        print("[VoiceRep] Google Replicated Voice audition already exists.", flush=True)
        return

    try:
        # Downsample chunk_04 (22.9s) cleanly from 48k -> 24k 16-bit mono WAV in memory
        with wave.open(str(ref_48k_p), "rb") as wf:
            pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)[::2]
        tmp_ref24 = EP0_DIR / "my_narration" / "_tmp_ref24k_for_google.wav"
        with wave.open(str(tmp_ref24), "wb") as wf_out:
            wf_out.setnchannels(1)
            wf_out.setsampwidth(2)
            wf_out.setframerate(24000)
            wf_out.writeframes(pcm.tobytes())

        source_b64 = base64.b64encode(tmp_ref24.read_bytes()).decode("utf-8")
        consent_b64 = base64.b64encode(consent_p.read_bytes()).decode("utf-8")
        tmp_ref24.unlink(missing_ok=True)

        with httpx.Client(timeout=TIMEOUT) as client:
            # Check if already registered
            r_list = client.get(VOICES_URL, params={"type": "replicated"}, headers={"x-goog-api-key": api_key})
            voice_id = None
            if r_list.status_code == 200:
                for v in r_list.json().get("voices") or []:
                    if v.get("display_name") == "David Documentary Narrator":
                        voice_id = v.get("id")
                        break
            if not voice_id:
                print("[VoiceRep] Registering David's voice on Gemini 3.8 Flash TTS...", flush=True)
                r_create = client.post(
                    VOICES_URL,
                    headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                    json={
                        "store": True,
                        "voice": {
                            "model": "gemini-3.8-flash-tts",
                            "type": "replicated",
                            "display_name": "David Documentary Narrator",
                            "replicated": {
                                "source_audio": {"mime_type": "audio/wav", "data": source_b64},
                                "consent_audio": {"mime_type": "audio/wav", "data": consent_b64},
                            },
                        },
                    },
                )
                if r_create.status_code in (200, 201):
                    voice_id = r_create.json().get("id")
                    print(f"[VoiceRep] Created persistent Google Voice ID: {voice_id}", flush=True)
                else:
                    print(f"[VoiceRep] Create returned {r_create.status_code}: {r_create.text[:240]}", flush=True)
                    return

            if voice_id:
                r_tts = client.post(
                    INTERACTIONS_URL,
                    headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                    json={
                        "model": "gemini-3.8-flash-tts",
                        "input": [
                            {
                                "type": "user_input",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Welcome back to Chapter One of The Universe Inside Out. Today we are putting timeless grooves and GPS satellite clocks directly under the microscope.",
                                        "annotations": [{"type": "speech_metadata", "style": "warm, natural documentary storyteller"}],
                                    }
                                ],
                            }
                        ],
                        "response_format": {"type": "audio"},
                        "generation_config": {"speech_config": [{"voice": voice_id}]},
                    },
                )
                if r_tts.status_code == 200:
                    b64, _ = extract_media_b64_or_uri(r_tts.json(), "audio")
                    if b64:
                        audition_out.write_bytes(base64.b64decode(b64))
                        print(f"[VoiceRep] Saved Google Replicated Voice audition: {audition_out.name}", flush=True)
                else:
                    print(f"[VoiceRep] TTS returned {r_tts.status_code}: {r_tts.text[:220]}", flush=True)
    except Exception as exc:
        print(f"[VoiceRep] Optional test exception: {type(exc).__name__}: {exc}", flush=True)


def main() -> None:
    t0 = time.time()
    api_key = get_api_key()
    assert api_key, "GEMINI_API_KEY missing"

    print("=== Stage 1A: Generating 4 Lyria 3.5 Instrumental Documentary Movements ===", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(fetch_lyria_track, fn, pr, api_key) for fn, pr in LYRIA_TRACKS]
        for f in as_completed(futs):
            _ = f.result()

    print("\n=== Stage 1B: Testing Google Gemini 3.8 Flash TTS Voice Replication ===", flush=True)
    test_google_voice_replication(api_key)

    print(f"\n=== Stage 1C: Generating {len(NEW_1080P_CLIPS)} New 1080p Gemini Omni Cinema Clips ===", flush=True)
    tot = len(NEW_1080P_CLIPS)
    with ThreadPoolExecutor(max_workers=1) as pool:
        futs = [pool.submit(fetch_cinema_1080p, i + 1, tot, fn, pr, api_key) for i, (fn, pr) in enumerate(NEW_1080P_CLIPS)]
        for f in as_completed(futs):
            _ = f.result()

    print(f"\n[ALL CLOUD ASSETS READY in {time.time() - t0:.1f}s!]", flush=True)


if __name__ == "__main__":
    main()
