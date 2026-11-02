"""
Episode 1 Master Audio, Sentence-Breathing Sculptor & Standalone .SRT Builder:
  'Episode 1 — Is Time Even Real? Vinyl Records, Memory & Why GPS Satellites Run Fast'

Workflow (Audio-First Lock before 4K Visual Rendering):
  1. Runs `audit_ep1_tts_whisper.py` via `.venv_voice` (BELOW_NORMAL GPU priority) so all 28
     `google_voice_chunks/chunk_00..27.wav` files have verified word timestamps and WPM checks.
  2. Polishes Whisper word tokens back to 100% canonical display spelling (`Page-Wootters`, `QuTiP`,
     `Landauer`, `Lacuna`, `Itay Griniasty`, `Unruh`, `Kerr`, `stoler.systems`) and aligns canonical
     sentence-ending punctuation from `ep1_chunks_data.py`.
  3. Fixes Episode 0's fast sentence transitions: `expand_sentence_pauses_cleanly()` inspects every
     internal sentence boundary (`.`, `?`, `!`, `:`) inside each chunk, locates the minimum-RMS
     zero-crossing silence point, and smoothly expands rushed TTS gaps (`0.15s-0.35s`) out to natural,
     unhurried human breathing pauses (`0.72s-0.88s` for statements, `0.88s-1.00s` for questions,
     with slight natural human jitter so it never sounds robotic!).
  4. Matches vocal loudness (`-19.2 dBFS` active speech) AND upper-mid vocal excitement/presence
     (`±1.6 dB` gentle 2.5 kHz tilt match across all 28 chunks) + 150ms velvet onset shaping.
  5. Mixes with Episode 0's mid-scooped velvet ambient stems at `CONST_GAIN = 0.060` (~2.5 dB warmer
     than Episode 0's `0.045`, zero sidechain pumping!) + gentle `3.6s` musical intro & Chapter 6 outro.
  6. Exports:
       • `audio_v1/Episode_1_Master_Audio_v1.wav` & `Episode_1_Master_Audio_v1.mp3` (also copied to Artifact Dir)
       • `audio_v1/episode1_v1_voice_only_mono.wav` & per-scene `audio_v1/scene00..06.wav`
       • `audio_v1/ep1_v1_manifest.json` (sample-accurate chunk, cue & word timestamps for Phase 4 4K render)
       • `Episode_1_Is_Time_Even_Real_Subtitles.srt` (100% standalone .SRT — ZERO burned-in video subtitles!)
       • `Episode_1_YouTube_Chapters.txt`
"""

from __future__ import annotations

import ctypes
import json
import math
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import imageio_ffmpeg
import numpy as np
from scipy import signal

EP1_DIR = Path(__file__).resolve().parent
ROOT_DIR = EP1_DIR.parent
EP0_DIR = ROOT_DIR / "episode0_flagship"
for p in (str(EP1_DIR), str(EP0_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from ep1_chunks_data import CHUNKS, SCENE_METADATA  # noqa: E402
from master_v2_audio_and_subtitles import (  # noqa: E402
    SR,
    master_vocal_chunk,
    peaking_eq_biquad,
)
from build_dual_audio_auditions import (  # noqa: E402
    decode_audio_48k,
    prepare_velvet_ambient_stem,
    rms_envelope_fast,
    save_wav_and_mp3,
    wsola_time_scale,
)


def group_words_into_cues_v3(words: List[dict], max_words: int = 9, max_chars: int = 56) -> List[dict]:
    """
    Groups timestamped words into crisp broadcast subtitle cues, UNCONDITIONALLY flushing
    before ANY pause >= 0.68s so subtitles NEVER linger across sentence or chapter pauses!
    """
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
        gap_ahead = (words[idx + 1]["start"] - w["end"]) if (idx + 1 < len(words)) else 9.9
        sentence_or_chunk_pause = gap_ahead >= 0.68
        strong_punct = tok.endswith((".", "?", "!", ":", "—"))
        comma_punct = tok.endswith((",", ";"))
        medium_pause = gap_ahead >= 0.38

        if sentence_or_chunk_pause:
            flush_buf()
        elif strong_punct and len(buf) >= 3:
            flush_buf()
        elif (comma_punct or medium_pause) and (len(buf) >= 5 or cur_chars >= 34):
            flush_buf()
        elif len(buf) >= max_words or cur_chars >= max_chars:
            flush_buf()

    flush_buf()

    merged_cues: List[dict] = []
    for c in cues:
        if (
            len(c["words"]) == 1
            and merged_cues
            and (c["start"] - merged_cues[-1]["end"]) < 0.65
            and len(merged_cues[-1]["words"]) <= 10
        ):
            prev = merged_cues[-1]
            prev["words"].extend(c["words"])
            prev["text"] = " ".join(w["text"] for w in prev["words"])
            prev["end"] = c["end"]
        else:
            merged_cues.append(c)
    cues = merged_cues

    for k in range(len(cues) - 1):
        if cues[k]["end"] > cues[k + 1]["start"] - 0.04:
            cues[k]["end"] = round(max(cues[k]["start"] + 0.18, cues[k + 1]["start"] - 0.04), 3)
    return cues

try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
except Exception:
    pass

VOICE_CHUNKS_DIR = EP1_DIR / "google_voice_chunks"
AUDIO_V1_DIR = EP1_DIR / "audio_v1"
AUDIO_V1_DIR.mkdir(parents=True, exist_ok=True)
SCORE_DIR = EP0_DIR / "score_stems"
ART_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")
VENV_VOICE_PY = ROOT_DIR / ".venv_voice" / "Scripts" / "python.exe"

INTRO_HOOK_SEC = 3.60

# Generous inter-chunk & chapter-end pauses (seconds):
POST_CHUNK_PAUSE_SEC: Dict[str, float] = {
    # Scene 00 — Welcome (3 chunks)
    "chunk_00": 1.35,
    "chunk_01": 1.50,
    "chunk_02": 2.15,  # + 0.70s next-scene lead = 2.85s chapter break

    # Scene 01 — Illusion of Now & Page-Wootters (4 chunks)
    "chunk_03": 1.40,
    "chunk_04": 1.40,
    "chunk_05": 1.65,  # Beat to let 15-decimal observer match sink in
    "chunk_06": 2.20,  # + 0.70s lead = 2.90s chapter break after breakfast riddle

    # Scene 02 — Brain Needle & Landauer's Law (5 chunks)
    "chunk_07": 1.35,
    "chunk_08": 1.45,
    "chunk_09": 1.40,
    "chunk_10": 1.55,
    "chunk_11": 2.20,  # + 0.70s lead = 2.90s chapter break after Two-Wing twist

    # Scene 03 — 20,000-km GPS Test (5 chunks)
    "chunk_12": 1.40,
    "chunk_13": 1.45,
    "chunk_14": 1.35,
    "chunk_15": 1.75,  # Beat for 11.4 km highway drift visual payoff
    "chunk_16": 2.20,  # + 0.70s lead = 2.90s chapter break after 3,189 km zero-crossing

    # Scene 04 — Mercury, Cassini & GW170817 (4 chunks)
    "chunk_17": 1.35,
    "chunk_18": 1.50,
    "chunk_19": 1.65,  # Beat for 1.7-second neutron star photo finish
    "chunk_20": 2.20,  # + 0.70s lead = 2.90s chapter break

    # Scene 05 — Lacuna & Honest Red-Team Scorecard (5 chunks incl. chunk_23b)
    "chunk_21": 1.45,
    "chunk_22": 1.45,
    "chunk_23": 1.55,
    "chunk_23b": 1.65, # Beat to let 1.000000 six-decimal fishing-reel discovery sink in!
    "chunk_24": 2.25,  # + 0.70s lead = 2.95s chapter break before Outro

    # Scene 06 — Interactive Lab, Discord & Episode 2 Preview (3 chunks)
    "chunk_25": 1.40,
    "chunk_26": 1.55,
    "chunk_27": 1.00,
}


NUM_WORD_MAP = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "eleven": "11",
    "fourteen": "14",
    "fifteen": "15",
    "seventeen": "17",
    "twenty": "20",
    "eighty": "80",
    "four": "4",
}


def _norm_tok(s: str) -> str:
    t = re.sub(r"[^a-z0-9]", "", s.lower())
    return NUM_WORD_MAP.get(t, t)


def extract_canonical_sentence_breaks(script_text: str) -> List[Tuple[str, str, str]]:
    """
    Extracts `(prev_word_norm, next_word_norm, punct)` for every internal sentence boundary
    in `script_text` so even if Whisper omits a period, we still restore punctuation AND
    expand the inter-sentence pause cleanly!
    """
    # Normalize spaced em-dashes away so only true `.`, `?`, `!`, `:` sentence/colon breaks are captured
    clean = script_text.replace("—", ", ")
    tokens = clean.split()
    breaks: List[Tuple[str, str, str]] = []
    for i in range(len(tokens) - 1):
        cur = tokens[i].rstrip("\"'’”)")
        if cur and cur[-1] in (".", "?", "!", ":"):
            punct = cur[-1]
            # Exclude decimal dots inside single tokens (already safe since cur[-1] is trailing)
            w_prev = _norm_tok(cur[:-1].split("-")[-1])
            w_next = _norm_tok(tokens[i + 1].split("-")[0])
            if w_prev and w_next:
                breaks.append((w_prev, w_next, punct))
    return breaks


def polish_ep1_whisper_words(cid: str, raw_words: List[dict], script_text: str) -> List[dict]:
    """
    Restores canonical proper-noun spellings (`Wootters`, `QuTiP`, `Landauer`, `Lacuna`,
    `Itay Griniasty`, `Unruh`, `Kerr`, `stoler.systems`) and canonical sentence punctuation
    while preserving 100% exact Whisper audio word timestamps.
    """
    merged: List[dict] = []
    for w in raw_words:
        txt = w["text"].strip()
        if not txt:
            continue
        if merged and (txt.startswith(("-", ",", ".")) or txt in ("%", "'s", "’s")):
            merged[-1]["text"] += txt
            merged[-1]["end"] = float(w["end"])
        else:
            merged.append({"text": txt, "start": float(w["start"]), "end": float(w["end"])})

    def _split_punct(tok: str) -> Tuple[str, str]:
        m = re.search(r"([.,?!:;—]+)$", tok)
        if m:
            return tok[: m.start()], m.group(1)
        return tok, ""

    # Multi-token phonetic collapses (`Cue-Tip` -> `QuTiP`, `Ee-tie Grin-ee-ah-stee` -> `Itay Griniasty`, etc.)
    cleaned: List[dict] = []
    i = 0
    while i < len(merged):
        cur = dict(merged[i])
        b0, p0 = _split_punct(cur["text"])
        l0 = b0.lower().replace("-", "")

        # 3-token checks (`stoler dot systems`)
        if i + 2 < len(merged):
            b1, _ = _split_punct(merged[i + 1]["text"])
            b2, p2 = _split_punct(merged[i + 2]["text"])
            if l0 in ("stoler", "stoller", "stolar", "solar") and b1.lower() == "dot" and b2.lower().startswith("system"):
                cleaned.append({"text": "stoler.systems" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if l0 in ("luh", "la") and b1.lower() in ("koo", "cu") and b2.lower().startswith("nuh"):
                cleaned.append({"text": "Lacuna" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue

        # 2-token checks
        if i + 1 < len(merged):
            b1, p1 = _split_punct(merged[i + 1]["text"])
            l1 = b1.lower().replace("-", "")
            if (l0, l1) in {("cue", "tip"), ("q", "tip"), ("queue", "tip")}:
                cleaned.append({"text": "QuTiP" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("woot", "ers"), ("woot", "erz"), ("wood", "ers")}:
                cleaned.append({"text": "Wootters" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("uhn", "roo"), ("un", "roo"), ("un", "ruh")}:
                cleaned.append({"text": "Unruh" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("stoler", "systems"), ("stoller", "systems")}:
                cleaned.append({"text": "stoler.systems" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) == ("git", "hub"):
                cleaned.append({"text": "GitHub" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if l0 in ("plank", "plahnk", "planck", "plonk") and l1 == "tension":
                cleaned.append({"text": "Planck-tension" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) == ("black", "hole") and i + 2 < len(merged) and merged[i + 2]["text"].lower().startswith("horizon"):
                cleaned.append({"text": "black-hole" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if l0 in ("itai", "eetie", "etie", "itay", "ita") and (
                l1.startswith("grin") or l1.startswith("green")
            ):
                cleaned.append({"text": "Itay", "start": cur["start"], "end": cur["end"]})
                cleaned.append({"text": "Griniasty" + p1, "start": merged[i + 1]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue

        # Single-token exact normalizations
        single_map = {
            "wooters": "Wootters",
            "wouters": "Wootters",
            "wooders": "Wootters",
            "wootters": "Wootters",
            "wooters'": "Wootters'",
            "cuetip": "QuTiP",
            "qtip": "QuTiP",
            "q-tip": "QuTiP",
            "cue-tip": "QuTiP",
            "python": "Python",
            "lacuna": "Lacuna",
            "laguna": "Lacuna",
            "luhkoonuh": "Lacuna",
            "lakuna": "Lacuna",
            "unruh": "Unruh",
            "uhnroo": "Unruh",
            "unroo": "Unruh",
            "unra": "Unruh",
            "landower": "Landauer",
            "landauer": "Landauer",
            "landowers": "Landauer's",
            "landauer's": "Landauer's",
            "griniasti": "Griniasty",
            "greeniasti": "Griniasty",
            "griniasty": "Griniasty",
            "itai": "Itay",
            "eetie": "Itay",
            "cur": "Kerr",
            "kur": "Kerr",
            "kerr": "Kerr",
            "github": "GitHub",
            "stoler.systems": "stoler.systems",
            "stolar.systems": "stoler.systems",
            "stoller.systems": "stoler.systems",
            "taught": "taut",
            "plank": "Planck",
            "plahnk": "Planck",
            "planck": "Planck",
            "plonk": "Planck",
        }
        low_key = b0.lower()
        if low_key in single_map:
            # Avoid turning 'cur' into 'Kerr' unless in chunk_23
            if low_key not in ("cur", "kur") or cid == "chunk_23":
                cur["text"] = single_map[low_key] + p0
        elif l0 in single_map and low_key not in ("cur", "kur"):
            if low_key.endswith("'s") or low_key.endswith("’s"):
                cur["text"] = "Landauer's" + p0
            else:
                cur["text"] = single_map[l0] + p0

        # Fix 'waste' -> 'waist' homophone in cosmic hourglass chunks, and 'winds' -> 'wins' / 'moved' -> 'moves' in chunk_16
        if low_key == "waste" and cid in ("chunk_06", "chunk_09", "chunk_10", "chunk_11", "chunk_27"):
            cur["text"] = "waist" + p0
        if low_key == "winds" and cid == "chunk_16":
            cur["text"] = "wins" + p0
        if low_key == "moved" and cid == "chunk_16":
            cur["text"] = "moves" + p0
        if low_key == "check" and cid == "chunk_23b":
            cur["text"] = "checked" + p0

        cleaned.append(cur)
        i += 1

    # Fix false mid-sentence capitalizations in chunk_03 ('us You' -> 'us, you', 'other Can't' -> 'other can't')
    if cid == "chunk_03":
        for idx in range(len(cleaned) - 1):
            if cleaned[idx]["text"] == "us" and cleaned[idx + 1]["text"] == "You":
                cleaned[idx]["text"] = "us,"
                cleaned[idx + 1]["text"] = "you"
            if cleaned[idx]["text"] == "other" and cleaned[idx + 1]["text"] in ("Can't", "Can’t"):
                cleaned[idx + 1]["text"] = "can't"

    # Fix false period Whisper placed inside comma list in chunk_27 ('Big Bang. Why' -> 'Big Bang, why')
    if cid == "chunk_27":
        for idx in range(len(cleaned) - 1):
            if cleaned[idx]["text"] == "Bang." and cleaned[idx + 1]["text"] == "Why":
                cleaned[idx]["text"] = "Bang,"
                cleaned[idx + 1]["text"] = "why"

    # Ensure final word of chunk carries its canonical ending punctuation (., ?, !)
    if cleaned and script_text.strip():
        end_ch = script_text.strip().rstrip("\"'’”)")[-1]
        if end_ch in (".", "?", "!"):
            b_last, p_last = _split_punct(cleaned[-1]["text"])
            if not p_last:
                cleaned[-1]["text"] = b_last + end_ch

    # Title-case channel & series names in chunk_00
    if cid == "chunk_00":
        for idx in range(len(cleaned) - 3):
            seq = [_split_punct(cleaned[idx + k]["text"])[0].lower() for k in range(4)]
            if seq == ["theoretically", "not", "a", "physicist"]:
                for k, cap in enumerate(("Theoretically", "Not", "A", "Physicist")):
                    _, pk = _split_punct(cleaned[idx + k]["text"])
                    cleaned[idx + k]["text"] = cap + pk
            if seq == ["the", "universe", "inside", "out"]:
                for k, cap in enumerate(("The", "Universe", "Inside", "Out")):
                    _, pk = _split_punct(cleaned[idx + k]["text"])
                    cleaned[idx + k]["text"] = cap + pk

    # Mark exact canonical sentence-ending indices from `script_text` so zero sentence breaks are missed
    # and false mid-clause periods don't trigger unexpected pauses!
    canon_breaks = extract_canonical_sentence_breaks(script_text)
    used_idx = -1
    for prev_norm, next_norm, punct in canon_breaks:
        for k in range(used_idx + 1, len(cleaned) - 1):
            w_p = _norm_tok(cleaned[k]["text"].split("-")[-1])
            w_n = _norm_tok(cleaned[k + 1]["text"].split("-")[0])
            if w_p == prev_norm and w_n == next_norm:
                base_k, pk = _split_punct(cleaned[k]["text"])
                cleaned[k]["text"] = base_k + punct
                cleaned[k]["is_sentence_end"] = punct
                if cleaned[k + 1]["text"] and cleaned[k + 1]["text"][0].islower() and punct in (".", "?", "!"):
                    if not cleaned[k + 1]["text"].startswith("stoler."):
                        cleaned[k + 1]["text"] = cleaned[k + 1]["text"][0].upper() + cleaned[k + 1]["text"][1:]
                used_idx = k
                break

    return cleaned


def expand_sentence_pauses_cleanly(
    pcm_48k: np.ndarray,
    words: List[dict],
    cid: str,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, List[dict], List[float]]:
    """
    Inspects every internal sentence boundary (`.`, `?`, `!`, `:`) inside a chunk, locates the
    quietest minimum-RMS zero-crossing point between sentences, and smoothly expands rushed TTS
    sentence transitions out to unhurried human breathing pauses:
      • Statements (`.`): `0.74s – 0.88s`
      • Questions (`?`):  `0.90s – 1.02s`
      • Colons (`:`):     `0.55s – 0.64s`
    Returns `(expanded_pcm, updated_words, list_of_final_sentence_gaps)`.
    """
    if len(words) < 2:
        return pcm_48k, words, []

    env_6ms = rms_envelope_fast(pcm_48k, max(1, int(0.006 * SR)))
    xfade_n = int(0.016 * SR)  # 16ms cosine micro-ramp at zero-crossing valley
    ramp_out = 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, xfade_n))
    ramp_in = 1.0 - ramp_out

    insertions: List[Tuple[int, int, int, float]] = []  # `(word_k, split_sample, n_add_samples, min_rms)`
    final_gaps: List[float] = []

    for k in range(len(words) - 1):
        tok = words[k]["text"].rstrip("\"'’”)")
        if not tok:
            continue
        last_ch = words[k].get("is_sentence_end") or (tok[-1] if tok[-1] in (".", "?", "!", ":") else "")
        if not last_ch:
            continue
        if len(tok) == 2 and tok[0].isupper() and last_ch == ".":
            continue

        if last_ch == "?":
            target_gap = float(rng.uniform(0.90, 1.02))
        elif last_ch in (".", "!"):
            target_gap = float(rng.uniform(0.74, 0.88))
        else:  # ':'
            target_gap = float(rng.uniform(0.55, 0.64))

        t0 = float(words[k]["end"])
        t1 = float(words[k + 1]["start"])
        # Search ±130ms around boundary so coarse Whisper timestamps never miss the acoustic dip!
        s_lo = max(xfade_n + 1, int((t0 - 0.13) * SR))
        s_hi = min(len(pcm_48k) - xfade_n - 2, int((max(t1, t0) + 0.14) * SR))
        if s_hi <= s_lo + 20:
            continue

        valley_idx = s_lo + int(np.argmin(env_6ms[s_lo:s_hi]))
        min_rms = float(env_6ms[valley_idx])
        if min_rms > 0.045:
            continue

        # Snap `valley_idx` to nearest zero-crossing within ±2.5ms
        zc_lo = max(xfade_n + 1, valley_idx - int(0.0025 * SR))
        zc_hi = min(len(pcm_48k) - xfade_n - 2, valley_idx + int(0.0025 * SR))
        seg_zc = pcm_48k[zc_lo : zc_hi + 1]
        zc_candidates = np.flatnonzero(seg_zc[:-1] * seg_zc[1:] <= 0.0)
        if len(zc_candidates) > 0:
            nearest = zc_candidates[int(np.argmin(np.abs((zc_lo + zc_candidates) - valley_idx)))]
            split_s = zc_lo + int(nearest)
        else:
            split_s = valley_idx

        # Strict silence threshold (`<= 0.006`) so quiet consonant tails aren't mistaken for pause silence!
        q_thresh = min(0.006, max(0.0025, min_rms * 1.7))
        q_left = split_s
        while q_left > max(0, int((t0 - 0.18) * SR)) and env_6ms[q_left] < q_thresh:
            q_left -= 1
        q_right = split_s
        while q_right < min(len(env_6ms) - 1, int((max(t1, t0) + 0.18) * SR)) and env_6ms[q_right] < q_thresh:
            q_right += 1
        acoustic_gap = (q_right - q_left) / float(SR)
        existing_gap = max(0.03, max(0.0, t1 - t0), acoustic_gap)

        if existing_gap >= target_gap - 0.03:
            final_gaps.append(round(existing_gap, 3))
            continue

        add_sec = target_gap - existing_gap
        n_add = int(round(add_sec * SR))
        if n_add >= int(0.04 * SR):
            insertions.append((k, split_s, n_add, min_rms))
            final_gaps.append(round(existing_gap + add_sec, 3))

    if not insertions:
        return pcm_48k, [dict(w) for w in words], final_gaps

    out_segs: List[np.ndarray] = []
    cursor = 0
    applied: List[Tuple[int, int, int]] = []
    for word_k, split_s, n_add, min_rms in insertions:
        if split_s <= cursor + xfade_n:
            continue
        floor_std = min(0.00006, max(1e-6, min_rms * 0.35))
        pad = rng.normal(0.0, floor_std, n_add + 2 * xfade_n)

        s_pre = split_s - xfade_n
        out_segs.append(pcm_48k[cursor:s_pre])
        out_segs.append(pcm_48k[s_pre:split_s] * ramp_out + pad[:xfade_n] * ramp_in)
        out_segs.append(pad[xfade_n : xfade_n + n_add])
        out_segs.append(pad[xfade_n + n_add :] * ramp_out + pcm_48k[split_s : split_s + xfade_n] * ramp_in)
        cursor = split_s + xfade_n
        applied.append((word_k, split_s, n_add))

    out_segs.append(pcm_48k[cursor:])

    # Shift word timestamps strictly by word index `m > word_k` so even `t1 == t0` boundaries get exact gaps!
    upd_words = []
    for idx_w, w in enumerate(words):
        shift_before = sum(n_add / float(SR) for wk, _, n_add in applied if idx_w > wk)
        ws = float(w["start"]) + shift_before
        we = float(w["end"]) + shift_before
        # Clamp word `word_k` end to `split_s` if Whisper marked its end slightly past the acoustic dip
        for wk, sp_s, _ in applied:
            if idx_w == wk:
                sp_t = sp_s / float(SR) + sum(na / float(SR) for wk2, _, na in applied if wk2 < wk)
                we = min(we, max(ws + 0.04, sp_t))
            elif idx_w == wk + 1:
                sp_t_after = sp_s / float(SR) + sum(na / float(SR) for wk2, _, na in applied if wk2 <= wk)
                ws = max(ws, sp_t_after)
                we = max(we, ws + 0.05)
        upd_words.append({"text": w["text"], "start": round(ws, 3), "end": round(we, 3)})

    return np.concatenate(out_segs), upd_words, final_gaps


def compute_presence_ratio(x: np.ndarray) -> float:
    sos_lo = signal.butter(2, [140.0 / (0.5 * SR), 750.0 / (0.5 * SR)], btype="bandpass", output="sos")
    sos_hi = signal.butter(2, [1400.0 / (0.5 * SR), 4200.0 / (0.5 * SR)], btype="bandpass", output="sos")
    e_lo = float(np.sqrt(np.mean(signal.sosfiltfilt(sos_lo, x) ** 2) + 1e-12))
    e_hi = float(np.sqrt(np.mean(signal.sosfiltfilt(sos_hi, x) ** 2) + 1e-12))
    return e_hi / max(e_lo, 1e-6)


def master_ep1_chunk_matched(pcm_48k: np.ndarray, words: List[dict], rng: np.random.Generator, cid: str) -> Tuple[np.ndarray, List[dict]]:
    """
    1. Trims leading/trailing digital silence safely while keeping word timestamps locked.
    2. Gently relaxes any brisk TTS chunk (`> 152 WPM`) via pitch-preserving WSOLA (`speed >= 0.91`)
       so all 28 chunks share the same relaxed, steady human cadence.
    3. Expands internal sentence breaks to natural `0.74s-1.02s` pauses (`expand_sentence_pauses_cleanly`).
    4. Applies broadcast vocal EQ, de-essing, optical compression, `-19.2 dBFS` active-speech RMS match,
       and soft `150ms` onset shaping so no chunk ever barks after a pause.
    """
    env = rms_envelope_fast(pcm_48k, int(0.015 * SR))
    voiced = np.flatnonzero(env > 0.0045)
    if len(voiced) > 10:
        s0 = max(0, int(voiced[0]) - int(0.14 * SR))
        s1 = min(len(pcm_48k), int(voiced[-1]) + int(0.24 * SR))
    else:
        s0, s1 = 0, len(pcm_48k)

    trim_s0 = s0 / float(SR)
    sliced = pcm_48k[s0:s1]
    trimmed_words = []
    for w in words:
        nw = dict(w)
        nw["start"] = round(max(0.0, float(w["start"]) - trim_s0), 3)
        nw["end"] = round(max(0.04, float(w["end"]) - trim_s0), 3)
        trimmed_words.append(nw)

    # Gentle WSOLA tempo alignment if a TTS chunk ran brisk (`> 152 WPM`)
    if len(trimmed_words) >= 6:
        sp_dur = max(0.8, trimmed_words[-1]["end"] - trimmed_words[0]["start"])
        raw_wpm = len(trimmed_words) / (sp_dur / 60.0)
        if raw_wpm > 152.0:
            spd = max(0.91, 145.0 / raw_wpm)
            sliced = wsola_time_scale(sliced, spd, SR)
            for nw in trimmed_words:
                nw["start"] = round(nw["start"] / spd, 3)
                nw["end"] = round(nw["end"] / spd, 3)

    # Step 3: Expand internal sentence pauses so David NEVER rushes into the next sentence!
    paced_pcm, paced_words, gaps = expand_sentence_pauses_cleanly(sliced, trimmed_words, cid, rng)

    # Step 3: Broadcast vocal chain
    mastered = master_vocal_chunk(paced_pcm, SR)

    # Gentle 150ms onset shaping on chunk opening syllable
    v_idx = np.flatnonzero(rms_envelope_fast(mastered, int(0.012 * SR)) > 0.012)
    if len(v_idx) > 0:
        v0 = max(0, int(v_idx[0]) - int(0.03 * SR))
        soft_n = min(int(0.15 * SR), len(mastered) - v0)
        if soft_n > 10:
            soft_curve = 0.74 + 0.26 * (0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, soft_n)))
            mastered[v0 : v0 + soft_n] *= soft_curve

    fn = min(int(0.035 * SR), len(mastered) // 6)
    if fn > 1:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, fn))
        mastered[:fn] *= ramp
        mastered[-fn:] *= ramp[::-1]

    return mastered, paced_words


def mix_ep1_soundtrack(voice_mono: np.ndarray, manifest_scenes: List[dict], ffmpeg_exe: str) -> np.ndarray:
    """
    Mixes centered Episode 1 narration with:
      • Warm, inviting `3.6s` atmospheric opening bloom (`0:00 – 0:03.6`) fading cleanly before speech
      • Steady, non-pumping velvet ambient bed at `CONST_GAIN = 0.060` (`+2.5 dB` warmer than Episode 0's `0.045`,
        mid-scooped `-7 dB @ 1300 Hz` so words stay 100% crystal clear!)
      • Gentle `0.082` warmth under the Episode 2 preview (`chunk_27`) + graceful `0.145` closing resolution!
    """
    total_n = len(voice_mono)

    st02 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_02_timeless_groove.mp3", ffmpeg_exe, channels=2))
    st03 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_03_cosmic_tension.mp3", ffmpeg_exe, channels=2))
    st04 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_04_grand_horizon.mp3", ffmpeg_exe, channels=2))

    sc06 = next(s for s in manifest_scenes if s["id"] == "scene06")
    sc06_start = float(sc06["start_sec"])
    ch27_info = next(c for c in sc06["chunks"] if c["chunk_id"] == "chunk_27")
    t_ep2_teaser = sc06_start + float(ch27_info["local_start"])
    t_speech_end = sc06_start + float(ch27_info["local_end"])

    # Build continuous 5.0s-crossfaded velvet stereo stem across the entire episode
    velvet_bed = np.zeros((total_n, 2), dtype=np.float64)
    xfade = int(5.0 * SR)
    pos = 0
    stems = [st02, st04, st03, st02, st04]
    idx_s = 0
    while pos < total_n:
        st = stems[idx_s % len(stems)]
        end_p = min(total_n, pos + len(st))
        seg_len = end_p - pos
        if pos > 0 and seg_len > xfade:
            ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, xfade))[:, None]
            velvet_bed[pos : pos + xfade] = velvet_bed[pos : pos + xfade] * (1.0 - ramp) + st[:xfade] * ramp
            velvet_bed[pos + xfade : end_p] = st[xfade:seg_len]
        else:
            velvet_bed[pos:end_p] = st[:seg_len]
        pos += max(1, len(st) - xfade)
        idx_s += 1

    # Gain envelope:
    #   0.00s -> 0.55s: smooth fade-in to warm intro chord (`0.185`)
    #   2.20s -> 3.90s: smooth glide down to steady `CONST_GAIN = 0.060` (~2.5 dB warmer than Episode 0's 0.045!)
    #   chunk_27 teaser: gentle lift to `0.082`, then `0.145` closing chord after final word + 3.2s fade out!
    INTRO_GAIN = 0.185
    CONST_GAIN = 0.060
    TEASER_GAIN = 0.082
    OUTRO_SWELL_GAIN = 0.145

    b_env = np.ones(total_n, dtype=np.float64) * CONST_GAIN

    def cosine_glide(i0: int, i1: int, g0: float, g1: float) -> None:
        i0 = max(0, min(total_n, i0))
        i1 = max(i0, min(total_n, i1))
        if i1 > i0:
            u = np.linspace(0.0, math.pi, i1 - i0)
            b_env[i0:i1] = g0 + (g1 - g0) * (0.5 - 0.5 * np.cos(u))
        if i1 < total_n:
            b_env[i1:] = g1

    cosine_glide(0, int(0.55 * SR), 0.0, INTRO_GAIN)
    cosine_glide(int(2.20 * SR), int(3.95 * SR), INTRO_GAIN, CONST_GAIN)
    cosine_glide(int((t_ep2_teaser - 0.80) * SR), int((t_ep2_teaser + 2.50) * SR), CONST_GAIN, TEASER_GAIN)
    cosine_glide(int((t_speech_end + 0.25) * SR), int((t_speech_end + 1.65) * SR), TEASER_GAIN, OUTRO_SWELL_GAIN)

    fade_out_n = min(int(3.1 * SR), total_n - int((t_speech_end + 1.65) * SR))
    if fade_out_n > 10:
        b_env[-fade_out_n:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, fade_out_n))

    stereo = velvet_bed * b_env[:, None]
    stereo[:, 0] += voice_mono * 0.94
    stereo[:, 1] += voice_mono * 0.94
    return np.clip(stereo, -0.94, 0.94)


def fmt_srt_ts(sec: float) -> str:
    ms_total = max(0, int(round(sec * 1000.0)))
    hh = ms_total // 3_600_000
    rem = ms_total % 3_600_000
    mm = rem // 60_000
    rem %= 60_000
    ss = rem // 1000
    ms = rem % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def wrap_srt_two_lines(text: str, max_line: int = 42) -> str:
    if len(text) <= max_line:
        return text
    words = text.split()
    best_split = len(words) // 2
    best_diff = 999
    for idx in range(1, len(words)):
        l1 = " ".join(words[:idx])
        l2 = " ".join(words[idx:])
        diff = abs(len(l1) - len(l2)) + (40 if max(len(l1), len(l2)) > max_line + 8 else 0)
        if diff < best_diff:
            best_diff = diff
            best_split = idx
    return " ".join(words[:best_split]) + "\n" + " ".join(words[best_split:])


def export_standalone_srt_and_chapters(manifest: dict) -> Tuple[Path, Path]:
    srt_lines: List[str] = []
    cue_idx = 1
    all_cues: List[Tuple[float, float, str]] = []
    for sc in manifest["scenes"]:
        s0 = float(sc["start_sec"])
        for c in sc.get("cues") or []:
            cs = s0 + float(c["start"])
            ce = s0 + float(c["end"])
            txt = c["text"].strip()
            if txt:
                all_cues.append((cs, ce, txt))

    # Prevent any cross-scene overlap
    for k in range(len(all_cues) - 1):
        cs, ce, txt = all_cues[k]
        nxt_s = all_cues[k + 1][0]
        if ce > nxt_s - 0.04:
            all_cues[k] = (cs, max(cs + 0.20, nxt_s - 0.04), txt)

    for cs, ce, txt in all_cues:
        srt_lines.append(f"{cue_idx}\n{fmt_srt_ts(cs)} --> {fmt_srt_ts(ce)}\n{wrap_srt_two_lines(txt)}\n")
        cue_idx += 1

    srt_path = EP1_DIR / "Episode_1_Is_Time_Even_Real_Subtitles.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    # YouTube `CHAPTERS:` timestamp block (always starting at 00:00!)
    chap_titles = {
        "scene00": "Welcome Back: Is Time Even Real?",
        "scene01": "Chapter 1 — Why 'Flowing Time' Breaks Down & Page-Wootters",
        "scene02": "Chapter 2 — The Brain Needle & Landauer's Heat Tax of Memory",
        "scene03": "Chapter 3 — The 20,000-km GPS Test (+38.6 Microseconds/Day)",
        "scene04": "Chapter 4 — Mercury, Cassini & Colliding Neutron Stars (GW170817)",
        "scene05": "Chapter 5 — Lacuna AI Audit & Honest Black Hole Hurdles (Kerr)",
        "scene06": "Chapter 6 — Interactive Python Lab, Discord & Episode 2 Preview",
    }
    ch_lines = ["CHAPTERS:"]
    for idx, sc in enumerate(manifest["scenes"]):
        sid = sc["id"]
        if sid not in chap_titles:
            continue
        ts_s = 0 if idx <= 1 else int(round(float(sc["start_sec"])))
        ch_lines.append(f"{ts_s // 60:02d}:{ts_s % 60:02d} {chap_titles[sid]}")

    chap_path = EP1_DIR / "Episode_1_YouTube_Chapters.txt"
    chap_path.write_text("\n".join(ch_lines) + "\n", encoding="utf-8")
    return srt_path, chap_path


def main() -> None:
    t0 = time.time()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Step 1: Run CUDA Faster-Whisper audit via `.venv_voice`
    print("=== Step 1: Running Verbatim Faster-Whisper Audit on All 28 Chunks ===", flush=True)
    subprocess.run(
        [str(VENV_VOICE_PY), str(EP1_DIR / "audit_ep1_tts_whisper.py")],
        check=True,
    )
    audit = json.loads((VOICE_CHUNKS_DIR / "_whisper_ep1_audit.json").read_text(encoding="utf-8"))

    # Step 2: Master each chunk + expand internal sentence breaks + match vocal presence/excitement!
    print("\n=== Step 2: Sculpting Unhurried Sentence Breathing & Matching Excitement Across 28 Chunks ===", flush=True)
    rng = np.random.default_rng(20261102)
    chunk_mastered: Dict[str, np.ndarray] = {}
    chunk_words: Dict[str, List[dict]] = {}
    pres_ratios: Dict[str, float] = {}

    for spec in CHUNKS:
        cid = spec["chunk_id"]
        wp = VOICE_CHUNKS_DIR / f"{cid}.wav"
        pcm_48k = decode_audio_48k(wp, ffmpeg_exe, channels=1)
        p_words = polish_ep1_whisper_words(cid, audit[cid]["words"], spec["text"])
        m_pcm, m_words = master_ep1_chunk_matched(pcm_48k, p_words, rng, cid)
        chunk_mastered[cid] = m_pcm
        chunk_words[cid] = m_words
        pres_ratios[cid] = compute_presence_ratio(m_pcm)

    # Subtle ±1.6 dB presence-band match (`2.5 kHz`) toward episode median so excitement stays ultra-consistent!
    med_pres = float(np.median(list(pres_ratios.values())))
    for spec in CHUNKS:
        cid = spec["chunk_id"]
        ratio_db = 20.0 * math.log10(max(pres_ratios[cid], 1e-4) / max(med_pres, 1e-4))
        nudge_db = float(np.clip(-0.65 * ratio_db, -1.6, 1.6))
        if abs(nudge_db) >= 0.18:
            b_eq, a_eq = peaking_eq_biquad(2500.0, nudge_db, 0.75, SR)
            adj = signal.filtfilt(b_eq, a_eq, chunk_mastered[cid])
            # Re-lock active speech RMS to exact -19.2 dBFS
            old_rms = math.sqrt(float(np.mean(chunk_mastered[cid] ** 2)) + 1e-12)
            new_rms = math.sqrt(float(np.mean(adj ** 2)) + 1e-12)
            chunk_mastered[cid] = np.clip(adj * (old_rms / new_rms), -0.88, 0.88)

    # Step 3: Assemble timeline scene-by-scene
    print("\n=== Step 3: Assembling Episode 1 Master Timeline & Millisecond Cue Manifest ===", flush=True)
    scenes_map: Dict[str, List[dict]] = {}
    for spec in CHUNKS:
        scenes_map.setdefault(spec["scene_id"], []).append(spec)

    manifest_scenes: List[dict] = [
        {
            "id": "intro00",
            "chapter": "EPISODE 1",
            "title": "Is Time Even Real? Vinyl Records, Memory & GPS Clocks",
            "subtitle_tag": "THEORETICALLY NOT A PHYSICIST • CHAPTER 1 DEEP DIVE",
            "audio_file": None,
            "duration_sec": INTRO_HOOK_SEC,
            "start_sec": 0.0,
            "end_sec": INTRO_HOOK_SEC,
            "chunks": [],
            "cues": [],
        }
    ]
    all_voice_parts: List[np.ndarray] = [np.zeros(int(round(INTRO_HOOK_SEC * SR)), dtype=np.float64)]
    running_sec = INTRO_HOOK_SEC

    for sid in sorted(scenes_map.keys()):
        specs = scenes_map[sid]
        meta = SCENE_METADATA[sid]
        lead_s = 0.25 if sid == "scene00" else 0.70

        sc_parts: List[np.ndarray] = [np.zeros(int(round(lead_s * SR)), dtype=np.float64)]
        cursor_s = lead_s
        sc_words: List[dict] = []
        sc_chunk_meta: List[dict] = []

        for spec in specs:
            cid = spec["chunk_id"]
            m_pcm = chunk_mastered[cid]
            ch_dur = len(m_pcm) / float(SR)
            for w in chunk_words[cid]:
                ws = round(w["start"] + cursor_s, 3)
                we = round(min(cursor_s + ch_dur, max(ws + 0.04, w["end"] + cursor_s)), 3)
                sc_words.append({"text": w["text"], "start": ws, "end": we})

            pause_after = POST_CHUNK_PAUSE_SEC.get(cid, 1.40)
            g_s0 = running_sec + cursor_s
            g_s1 = g_s0 + ch_dur
            print(
                f"  {cid} ({sid}) | {int(g_s0 // 60):02d}:{g_s0 % 60:05.2f} -> {int(g_s1 // 60):02d}:{g_s1 % 60:05.2f} "
                f"({ch_dur:5.2f}s) + pause {pause_after:4.2f}s",
                flush=True,
            )

            sc_chunk_meta.append(
                {
                    "chunk_id": cid,
                    "label": spec["label"],
                    "local_start": round(cursor_s, 3),
                    "local_end": round(cursor_s + ch_dur, 3),
                    "global_start": round(g_s0, 3),
                    "global_end": round(g_s1, 3),
                    "pause_after": pause_after,
                }
            )
            sc_parts.append(m_pcm)
            cursor_s += ch_dur
            sc_parts.append(np.zeros(int(round(pause_after * SR)), dtype=np.float64))
            cursor_s += pause_after

        sc_audio = np.concatenate(sc_parts)
        sc_wav = AUDIO_V1_DIR / f"{sid}.wav"
        pcm16 = (np.clip(sc_audio, -0.96, 0.96) * 32767.0).astype(np.int16)
        with wave.open(str(sc_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm16.tobytes())

        sc_dur = round(len(pcm16) / float(SR), 3)
        cues = group_words_into_cues_v3(sc_words)
        manifest_scenes.append(
            {
                "id": sid,
                "chapter": meta["chapter"],
                "title": meta["title"],
                "subtitle_tag": meta["subtitle_tag"],
                "audio_file": sc_wav.name,
                "duration_sec": sc_dur,
                "start_sec": round(running_sec, 3),
                "end_sec": round(running_sec + sc_dur, 3),
                "chunks": sc_chunk_meta,
                "cues": cues,
            }
        )
        all_voice_parts.append(sc_audio)
        running_sec += sc_dur

    # Add 3.6s closing musical tail after Chapter 6 sign-off
    tail_s = 3.60
    all_voice_parts.append(np.zeros(int(round(tail_s * SR)), dtype=np.float64))
    manifest_scenes[-1]["duration_sec"] = round(manifest_scenes[-1]["duration_sec"] + tail_s, 3)
    manifest_scenes[-1]["end_sec"] = round(manifest_scenes[-1]["end_sec"] + tail_s, 3)
    running_sec += tail_s

    voice_full = np.concatenate(all_voice_parts)
    voice_stem_wav = AUDIO_V1_DIR / "episode1_v1_voice_only_mono.wav"
    with wave.open(str(voice_stem_wav), "wb") as wf_v:
        wf_v.setnchannels(1)
        wf_v.setsampwidth(2)
        wf_v.setframerate(SR)
        wf_v.writeframes((np.clip(voice_full, -0.96, 0.96) * 32767.0).astype(np.int16).tobytes())

    stereo_master = mix_ep1_soundtrack(voice_full, manifest_scenes, ffmpeg_exe)
    master_wav = AUDIO_V1_DIR / "Episode_1_Master_Audio_v1.wav"
    master_mp3 = AUDIO_V1_DIR / "Episode_1_Master_Audio_v1.mp3"
    save_wav_and_mp3(stereo_master, master_wav, master_mp3, ffmpeg_exe)
    shutil.copy2(str(master_mp3), str(ART_DIR / master_mp3.name))

    manifest = {
        "title": "Episode 1 — Is Time Even Real? Vinyl Records, Memory & Why GPS Satellites Run Fast",
        "sample_rate": SR,
        "total_duration_sec": round(len(stereo_master) / float(SR), 3),
        "scenes": manifest_scenes,
    }
    manifest_p = AUDIO_V1_DIR / "ep1_v1_manifest.json"
    manifest_p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    srt_path, chap_path = export_standalone_srt_and_chapters(manifest)
    shutil.copy2(str(srt_path), str(ART_DIR / srt_path.name))

    tot_s = len(stereo_master) / float(SR)
    print(
        f"\n[EPISODE 1 MASTER AUDIO & .SRT READY in {time.time() - t0:.1f}s!]\n"
        f"  • Master MP3 : {master_mp3} ({int(tot_s // 60)}m {tot_s % 60:04.1f}s)\n"
        f"  • Master WAV : {master_wav}\n"
        f"  • Clean .SRT : {srt_path}\n"
        f"  • Chapters   : {chap_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
