"""
Broadcast Vocal Mastering & Sample-Accurate Verbatim Subtitle Builder for Episode 0 v2:
  - Loads all 33 real human studio WAV chunks recorded by David (`48 kHz`)
    plus `_verbatim_whisper_medium_audit.json`.
  - Trims button-click dead air safely using Whisper word boundaries + 0.24s breath pad,
    applies a transparent broadcast documentary vocal chain (HPF 78 Hz, warm body +1.2 dB @ 135 Hz,
    mud cut -2.2 dB @ 275 Hz, presence +2.0 dB @ 3.8 kHz, split-band de-esser, and chunk-to-chunk
    active-speech loudness matching so all 33 takes sound like one continuous studio performance).
  - Preserves 100% of David's actual spoken words (including his honest uncertainty preface on
    memory/time in Chunk 14 and his Intro phrasing) while fixing Whisper homophones & punctuation.
  - Outputs `audio_v2/scene00.wav` .. `audio_v2/scene09.wav` (`48 kHz` 16-bit PCM)
    and `audio_v2/ep0_v2_manifest.json` (including the 13.5s `hook00` Cold-Open Hook!).
"""

from __future__ import annotations

import json
import re
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy import signal

from ep0_chunks_data import SCENE_METADATA

EP0_DIR = Path(__file__).resolve().parent
RAW_DIR = EP0_DIR / "my_narration"
OUT_DIR = EP0_DIR / "audio_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SR = 48000
HOOK_DURATION_SEC = 13.50


# ---------------------------------------------------------------------------
# Broadcast Biquad EQ & Dynamics Helpers
# ---------------------------------------------------------------------------

def peaking_eq_biquad(fc: float, gain_db: float, q: float, fs: int = SR) -> Tuple[np.ndarray, np.ndarray]:
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * fc / fs
    alpha = np.sin(w0) / (2.0 * q)
    cos_w0 = np.cos(w0)

    b0 = 1.0 + alpha * A
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / A
    return np.array([b0 / a0, b1 / a0, b2 / a0]), np.array([1.0, a1 / a0, a2 / a0])


def high_shelf_biquad(fc: float, gain_db: float, fs: int = SR) -> Tuple[np.ndarray, np.ndarray]:
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * fc / fs
    cos_w0 = np.cos(w0)
    alpha = np.sin(w0) / 2.0 * np.sqrt(2.0)
    sqrtA2alpha = 2.0 * np.sqrt(A) * alpha

    b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + sqrtA2alpha)
    b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
    b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - sqrtA2alpha)
    a0 = (A + 1.0) - (A - 1.0) * cos_w0 + sqrtA2alpha
    a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
    a2 = (A + 1.0) - (A - 1.0) * cos_w0 - sqrtA2alpha
    return np.array([b0 / a0, b1 / a0, b2 / a0]), np.array([1.0, a1 / a0, a2 / a0])


def master_vocal_chunk(x: np.ndarray, fs: int = SR) -> np.ndarray:
    """Applies gentle NPR/Nova broadcast EQ, smooth de-essing, optical leveling, and loudness match."""
    y = x.astype(np.float64) - np.mean(x)

    # 1. 78 Hz sub-rumble high-pass + 17 kHz ultrasonic roll-off
    sos_hp = signal.butter(2, 78.0 / (0.5 * fs), btype="highpass", output="sos")
    sos_lp = signal.butter(2, 17200.0 / (0.5 * fs), btype="lowpass", output="sos")
    y = signal.sosfiltfilt(sos_hp, y)
    y = signal.sosfiltfilt(sos_lp, y)

    # 2. Warm chest (+1.2 dB @ 135 Hz), mud cleanup (-2.2 dB @ 275 Hz), clarity (+1.9 dB @ 3800 Hz), air (+1.0 dB @ 9500 Hz)
    for fc, gdb, q in ((135.0, 1.2, 1.1), (275.0, -2.2, 1.4), (3800.0, 1.9, 1.0)):
        b, a = peaking_eq_biquad(fc, gdb, q, fs)
        y = signal.filtfilt(b, a, y)
    bs, as_ = high_shelf_biquad(9500.0, 1.0, fs)
    y = signal.filtfilt(bs, as_, y)

    # 3. Gentle split-band de-esser (5.5 kHz - 9.8 kHz)
    sos_sib = signal.butter(2, [5500.0 / (0.5 * fs), 9800.0 / (0.5 * fs)], btype="bandpass", output="sos")
    sib = signal.sosfiltfilt(sos_sib, y)
    win = max(1, int(0.008 * fs))
    sib_env = np.sqrt(np.convolve(sib * sib, np.ones(win) / win, mode="same") + 1e-12)
    sib_thresh = 0.042
    over = np.maximum(sib_env / sib_thresh, 1.0)
    sib_gain_red = 1.0 - (over ** -0.55)  # 0 when below thresh, up to ~0.45 on sharp sibilants
    y = y - sib * sib_gain_red

    # 4. Smooth optical-style envelope compressor (ratio ~2.1:1 above -22 dBFS)
    env_win = max(1, int(0.035 * fs))
    env = np.sqrt(np.convolve(y * y, np.ones(env_win) / env_win, mode="same") + 1e-12)
    comp_thresh = 0.080
    ratio = 2.1
    gain_db = np.where(
        env > comp_thresh,
        (1.0 / ratio - 1.0) * 20.0 * np.log10(np.maximum(env / comp_thresh, 1.0)),
        0.0,
    )
    # Smooth gain curve (60ms release feel)
    sm_win = max(1, int(0.060 * fs))
    gain_lin = np.convolve(10.0 ** (gain_db / 20.0), np.ones(sm_win) / sm_win, mode="same")
    y = y * gain_lin

    # 5. Match active-speech RMS across all 33 chunks (-19.2 dBFS active speech target)
    frame_len = int(0.050 * fs)
    n_frames = max(1, len(y) // frame_len)
    frames = y[: n_frames * frame_len].reshape(n_frames, frame_len)
    f_rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    active = f_rms[f_rms > np.percentile(f_rms, 30) * 1.15]
    speech_rms = float(np.median(active)) if len(active) > 0 else float(np.sqrt(np.mean(y * y) + 1e-12))
    target_rms = 10.0 ** (-19.2 / 20.0)  # ~0.1096
    scale = np.clip(target_rms / max(speech_rms, 1e-4), 0.55, 2.6)
    y = y * scale

    # 6. Transparent soft-knee peak ceiling at -1.4 dBFS (0.851)
    ceiling = 0.85
    abs_y = np.abs(y)
    knee = 0.72
    mask = abs_y > knee
    if np.any(mask):
        excess = (abs_y[mask] - knee) / (ceiling - knee)
        y[mask] = np.sign(y[mask]) * (knee + (ceiling - knee) * np.tanh(excess))
    return np.clip(y, -0.88, 0.88)


# ---------------------------------------------------------------------------
# Verbatim Word Token Polisher (Preserves 100% of David's Spoken Words!)
# ---------------------------------------------------------------------------

def polish_chunk_words(chunk_file: str, raw_words: List[dict]) -> List[dict]:
    """
    Merges Whisper split-hyphen/percent tokens and fixes homophones/punctuation
    while strictly keeping every single word David actually spoke and its exact start/end!
    """
    # Step 1: Merge tokens where next token starts with '-' or is '%'
    merged: List[dict] = []
    for w in raw_words:
        txt = w["text"].strip()
        if not txt:
            continue
        if merged and (txt.startswith("-") or txt == "%"):
            merged[-1]["text"] = merged[-1]["text"] + txt
            merged[-1]["end"] = w["end"]
        else:
            merged.append({"text": txt, "start": float(w["start"]), "end": float(w["end"])})

    # Step 2: Direct word-level homophone & spelling fixes
    exact_map = {
        "SimPi": "SymPy",
        "SimPi,": "SymPy,",
        "SciPi": "SciPy",
        "SciPi,": "SciPy,",
        "Starlight": "starlight",
    }
    for w in merged:
        if w["text"] in exact_map:
            w["text"] = exact_map[w["text"]]

    # Step 3: Contextual multi-word hyphen/homophone fixes (preserving token count or merging hyphen pairs)
    i = 0
    cleaned: List[dict] = []
    while i < len(merged):
        cur = merged[i]
        nxt = merged[i + 1] if i + 1 < len(merged) else None
        prv = cleaned[-1] if cleaned else None

        # Merge two-word hyphenated compounds neatly
        pair_lower = (cur["text"].lower(), nxt["text"].lower().rstrip(".,?!:")) if nxt else ("", "")
        punct = ""
        if nxt:
            m = re.search(r"([.,?!:]+)$", nxt["text"])
            if m:
                punct = m.group(1)

        hyphen_pairs = {
            ("stress", "tested"): "stress-tested",
            ("fade", "out"): "fade-out",
            ("mind", "reading"): "mind-reading",
            ("light", "years"): "light-years",
            ("upside", "down"): "upside-down",
        }
        if pair_lower in hyphen_pairs and nxt is not None:
            rep = hyphen_pairs[pair_lower] + punct
            if cur["text"][0].isupper():
                rep = rep[0].upper() + rep[1:]
            cleaned.append({"text": rep, "start": cur["start"], "end": nxt["end"]})
            i += 2
            continue

        # Fix "dark matter pool" -> "dark-matter pull" in chunk_30
        if chunk_file.startswith("chunk_30") and cur["text"].lower() == "pool" and prv and prv["text"].lower() == "matter":
            cur = {**cur, "text": "pull"}

        # Fix Whisper hearing "in" for unstressed "and" in 3 specific phrases
        if chunk_file.startswith("chunk_11") and cur["text"] == "in" and prv and prv["text"] == "ripples":
            cur = {**cur, "text": "and"}
        if chunk_file.startswith("chunk_15") and cur["text"] == "in" and prv and prv["text"].startswith("visual"):
            cur = {**cur, "text": "and"}
        if chunk_file.startswith("chunk_28") and cur["text"] == "in" and prv and prv["text"].startswith("visual"):
            if prv["text"] == "visual":
                cleaned[-1]["text"] = "visual,"
            cur = {**cur, "text": "and"}

        # Restore missing sentence punctuation in chunk_21
        if chunk_file.startswith("chunk_21"):
            if cur["text"] == "time" and nxt and nxt["text"] == "Wide":
                cur = {**cur, "text": "time,"}
                merged[i + 1]["text"] = "wide"
            elif cur["text"] == "sheet" and nxt and nxt["text"] == "and":
                cur = {**cur, "text": "sheet."}
                merged[i + 1]["text"] = "And"
            elif cur["text"] == "Sure":
                cur = {**cur, "text": "sure"}
            elif cur["text"] == "enough":
                cur = {**cur, "text": "enough,"}
            elif cur["text"] == "heavens":
                cur = {**cur, "text": "heavens,"}
            elif cur["text"] == "quiet" and nxt is None:
                cur = {**cur, "text": "quiet."}

        # Capitalize leading "but" in chunk_27
        if chunk_file.startswith("chunk_27") and i == 0 and cur["text"] == "but":
            cur = {**cur, "text": "But"}

        cleaned.append(cur)
        i += 1

    # Title-case the Episode Title Drop at the end of chunk_03_scene00_c
    if chunk_file.startswith("chunk_03"):
        for idx in range(len(cleaned)):
            # Look for "you," followed by "the" "universe" "inside"
            if (
                idx + 3 < len(cleaned)
                and cleaned[idx]["text"].lower().startswith("you")
                and cleaned[idx + 1]["text"].lower() == "the"
                and cleaned[idx + 2]["text"].lower() == "universe"
            ):
                cleaned[idx]["text"] = "you:"
                title_map = {
                    "the": "The",
                    "universe": "Universe",
                    "inside": "Inside",
                    "out,": "Out —",
                    "a": "A",
                    "visual": "Visual",
                    "guide": "Guide",
                    "stretched": "Stretched",
                    "fabric": "Fabric",
                    "upside-down": "Upside-Down",
                    "cosmic": "Cosmic",
                    "hourglass.": "Hourglass.",
                }
                for j in range(idx + 1, len(cleaned)):
                    low = cleaned[j]["text"].lower()
                    if low in title_map and not (low == "the" and j > idx + 2):
                        cleaned[j]["text"] = title_map[low]
                break

    return cleaned


def group_words_into_cues(words: List[dict], max_words: int = 9, max_chars: int = 56) -> List[dict]:
    """Groups timestamped words into crisp broadcast subtitle cues breaking cleanly on punctuation."""
    cues: List[dict] = []
    buf: List[dict] = []

    def flush_buf() -> None:
        if not buf:
            return
        text = " ".join(w["text"] for w in buf)
        cues.append(
            {
                "start": round(buf[0]["start"], 3),
                "end": round(buf[-1]["end"] + 0.14, 3),
                "text": text,
                "words": [
                    {"text": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
                    for w in buf
                ],
            }
        )
        buf.clear()

    for idx, w in enumerate(words):
        buf.append(w)
        cur_chars = sum(len(x["text"]) for x in buf) + max(0, len(buf) - 1)
        tok = w["text"]
        strong_punct = tok.endswith((".", "?", "!", ":", "—"))
        comma_punct = tok.endswith((",", ";"))
        long_pause_ahead = (
            idx + 1 < len(words) and (words[idx + 1]["start"] - w["end"]) >= 0.42
        )

        if strong_punct and len(buf) >= 3:
            flush_buf()
        elif (comma_punct or long_pause_ahead) and (len(buf) >= 5 or cur_chars >= 34):
            flush_buf()
        elif len(buf) >= max_words or cur_chars >= max_chars:
            flush_buf()

    flush_buf()

    # Prevent tiny overlaps between consecutive cues
    for k in range(len(cues) - 1):
        if cues[k]["end"] > cues[k + 1]["start"] - 0.03:
            cues[k]["end"] = round(max(cues[k]["start"] + 0.20, cues[k + 1]["start"] - 0.03), 3)
    return cues


# ---------------------------------------------------------------------------
# Main Mastering & Scene Stitching Pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    audit_path = RAW_DIR / "_verbatim_whisper_medium_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    # Group chunks by scene_id (`chunk_01_scene00_a.wav` -> `scene00`)
    scenes_chunks: Dict[str, List[dict]] = {}
    for ch in audit["chunks"]:
        m = re.search(r"_(scene\d+)_", ch["file"])
        assert m, f"Cannot parse scene_id from {ch['file']}"
        sid = m.group(1)
        scenes_chunks.setdefault(sid, []).append(ch)

    rng = np.random.default_rng(42)

    manifest_scenes: List[dict] = [
        {
            "id": "hook00",
            "chapter": "THE UNIVERSE INSIDE OUT",
            "title": "Cold Open: 95% Missing — Or Map Upside Down?",
            "subtitle_tag": "VISUAL COSMOLOGY TOUR • ZERO EQUATIONS",
            "audio_file": None,
            "duration_sec": HOOK_DURATION_SEC,
            "start_sec": 0.0,
            "end_sec": HOOK_DURATION_SEC,
            "cues": [
                {
                    "start": 0.35,
                    "end": 4.25,
                    "text": "Today's textbook map says 95% of reality is completely invisible.",
                    "words": [],
                },
                {
                    "start": 4.55,
                    "end": 8.95,
                    "text": "What if nothing is missing — and we've been holding the cosmic map upside down?",
                    "words": [],
                },
                {
                    "start": 9.25,
                    "end": 13.10,
                    "text": "One stretched fabric. One flipped cosmic hourglass. Zero equations.",
                    "words": [],
                },
            ],
        }
    ]

    running_time = HOOK_DURATION_SEC

    for sid in sorted(scenes_chunks.keys()):
        ch_list = scenes_chunks[sid]
        meta = SCENE_METADATA[sid]

        lead_pad_sec = 0.45 if sid == "scene00" else 0.55
        inter_chunk_gap_sec = 0.42
        tail_pad_sec = 0.85

        stitched_parts: List[np.ndarray] = [
            rng.normal(0.0, 0.00025, int(lead_pad_sec * SR))
        ]
        cursor_sec = lead_pad_sec
        scene_words: List[dict] = []

        for idx, ch in enumerate(ch_list):
            wav_p = RAW_DIR / ch["file"]
            with wave.open(str(wav_p), "rb") as wf:
                assert wf.getframerate() == SR
                raw_pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0

            polished_words = polish_chunk_words(ch["file"], ch["words"])
            first_w_start = polished_words[0]["start"] if polished_words else 0.0
            last_w_end = polished_words[-1]["end"] if polished_words else len(raw_pcm) / SR

            # Safe breath-preserving trim window: keep 0.24s before first word & 0.30s after last word
            trim_start_sec = max(0.0, first_w_start - 0.24)
            trim_end_sec = min(len(raw_pcm) / SR, last_w_end + 0.30)

            s0 = int(trim_start_sec * SR)
            s1 = max(s0 + int(0.2 * SR), int(trim_end_sec * SR))
            sliced = raw_pcm[s0:s1]

            # Broadcast vocal polish
            mastered = master_vocal_chunk(sliced, SR)

            # Smooth 35ms cosine edge fades so zero click/gate artifacts ever occur
            fade_n = min(int(0.035 * SR), len(mastered) // 6)
            if fade_n > 1:
                ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, fade_n))
                mastered[:fade_n] *= ramp
                mastered[-fade_n:] *= ramp[::-1]

            # Shift word timestamps into scene-local coordinates
            for w in polished_words:
                w_s = max(0.0, w["start"] - trim_start_sec) + cursor_sec
                w_e = max(w_s + 0.04, w["end"] - trim_start_sec) + cursor_sec
                scene_words.append({"text": w["text"], "start": w_s, "end": w_e})

            stitched_parts.append(mastered)
            cursor_sec += len(mastered) / SR

            if idx < len(ch_list) - 1:
                gap = rng.normal(0.0, 0.00025, int(inter_chunk_gap_sec * SR))
                stitched_parts.append(gap)
                cursor_sec += inter_chunk_gap_sec

        stitched_parts.append(rng.normal(0.0, 0.00025, int(tail_pad_sec * SR)))
        cursor_sec += tail_pad_sec

        scene_audio = np.concatenate(stitched_parts)
        out_wav = OUT_DIR / f"{sid}.wav"
        pcm16 = (np.clip(scene_audio, -0.98, 0.98) * 32767.0).astype(np.int16)
        with wave.open(str(out_wav), "wb") as wf_out:
            wf_out.setnchannels(1)
            wf_out.setsampwidth(2)
            wf_out.setframerate(SR)
            wf_out.writeframes(pcm16.tobytes())

        dur_sec = round(len(pcm16) / SR, 3)
        cues = group_words_into_cues(scene_words)

        manifest_scenes.append(
            {
                "id": sid,
                "chapter": meta["chapter"],
                "title": meta["title"],
                "subtitle_tag": meta["subtitle_tag"],
                "audio_file": out_wav.name,
                "duration_sec": dur_sec,
                "start_sec": round(running_time, 3),
                "end_sec": round(running_time + dur_sec, 3),
                "cues": cues,
            }
        )
        print(
            f"[Mastered] {sid} ({meta['chapter']}): {dur_sec:6.2f}s | {len(cues):2d} verbatim cues | "
            f"first='{cues[0]['text'][:44]}...'"
        )
        running_time += dur_sec

    manifest = {
        "title": "The Universe Inside Out: A Visual Guide to the Stretched Fabric & the Upside-Down Cosmic Hourglass",
        "sample_rate": SR,
        "total_duration_sec": round(running_time, 3),
        "scenes": manifest_scenes,
    }
    manifest_p = OUT_DIR / "ep0_v2_manifest.json"
    manifest_p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n[DONE] Total Episode 0 v2 duration: {running_time/60.0:.2f} min ({running_time:.1f}s) -> {manifest_p}")


if __name__ == "__main__":
    main()
