"""
Episode 2 Master Audio, Sentence-Breathing Sculptor & Standalone .SRT Builder (100% CPU-Only!):
  'Episode 2 — The Upside-Down Big Bang & Where All the Antimatter Went'

Workflow (Audio-First Lock before 4K Visual Rendering):
  1. Runs `audit_ep2_tts_whisper.py` via `.venv_voice` on CPU (`int8`, `local_files_only=True`, 0% GPU!)
     so all 31 `google_voice_chunks/chunk_00..30.wav` files have verified word timestamps and WPM checks.
  2. Polishes Whisper word tokens back to 100% canonical display spelling (`WeaveForge`, `Gaia`, `Zenodo`,
     `Penrose`, `Landauer`, `catenoid`, `COBE`, `WMAP`, `Planck`, `Lacuna`, `Wei-Ning Deng`, `Will Handley`,
     `Neil Turok`, `Latham Boyle`, `SLAC`, `BABAR`, `Lüders`, `Pauli`, `Schwinger`, `Barbour`, `Janus`,
     `Sakharov`, `LiteBIRD`, `KATRIN`, `Euclid`, `CPT`, `QCD`, `stoler.systems`) and aligns canonical
     sentence-ending punctuation from `ep2_chunks_data.py`.
  3. Expands rushed internal sentence transitions out to calm, natural human breathing pauses
     (`0.74s–0.88s` statements, `0.90s–1.02s` questions).
  4. Matches vocal loudness (`-19.2 dBFS` active speech) & gentle presence consistency (`±1.5 dB` @ 2.5 kHz)
     so all 31 chunks share one calm, warm, grounded tone (zero over-hyped spikes!).
  5. Mixes with Episode 0's mid-scooped velvet ambient stems at `CONST_GAIN = 0.060` + `3.6s` intro & outro.
  6. Exports:
       • `audio_v1/Episode_2_Master_Audio_v1.wav` & `Episode_2_Master_Audio_v1.mp3` (copied to Artifact Dir)
       • `audio_v1/episode2_v1_voice_only_mono.wav` & per-scene `audio_v1/scene00..06.wav`
       • `audio_v1/ep2_v1_manifest.json` (sample-accurate chunk, cue & word timestamps for Phase 4 4K render)
       • `Episode_2_Upside_Down_Big_Bang_Subtitles.srt` (100% standalone .SRT — ZERO burned-in frame subtitles!)
       • `Episode_2_YouTube_Chapters.txt`
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import Dict, List, Tuple

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["NUMBA_DISABLE_CUDA"] = "1"

import imageio_ffmpeg
import numpy as np
from scipy import signal

EP2_DIR = Path(__file__).resolve().parent
ROOT_DIR = EP2_DIR.parent
EP0_DIR = ROOT_DIR / "episode0_flagship"
EP1_DIR = ROOT_DIR / "episode1_time_and_memory"
for p in (str(EP2_DIR), str(EP1_DIR), str(EP0_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from ep2_chunks_data import CHUNKS, SCENE_METADATA  # noqa: E402
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
from build_ep1_master_audio_and_srt import (  # noqa: E402
    compute_presence_ratio,
    expand_sentence_pauses_cleanly,
    extract_canonical_sentence_breaks,
    fmt_srt_ts,
    group_words_into_cues_v3,
    wrap_srt_two_lines,
)

try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
except Exception:
    pass

VOICE_CHUNKS_DIR = EP2_DIR / "google_voice_chunks"
AUDIO_V1_DIR = EP2_DIR / "audio_v1"
AUDIO_V1_DIR.mkdir(parents=True, exist_ok=True)
SCORE_DIR = EP0_DIR / "score_stems"
ART_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")
VENV_VOICE_PY = ROOT_DIR / ".venv_voice" / "Scripts" / "python.exe"

INTRO_HOOK_SEC = 3.60

POST_CHUNK_PAUSE_SEC: Dict[str, float] = {
    # Scene 00 — Welcome (4 chunks)
    "chunk_00": 1.38,
    "chunk_01": 1.48,
    "chunk_02": 1.42,
    "chunk_03": 2.20,  # + 0.70s next-scene lead = 2.90s chapter break

    # Scene 01 — Penrose Paradox & Upside-Down Hourglass (4 chunks)
    "chunk_04": 1.40,
    "chunk_05": 1.65,  # Beat to let 10^(10^123) needle-tip odds sink in
    "chunk_06": 1.45,
    "chunk_07": 2.20,  # + 0.70s = 2.90s chapter break

    # Scene 02 — Cheat-Code Audit & Two-Ring Soap Film (4 chunks)
    "chunk_08": 1.55,  # Question beat after Konami controller question
    "chunk_09": 1.45,
    "chunk_10": 1.45,
    "chunk_11": 2.20,  # + 0.70s = 2.90s chapter break

    # Scene 03 — Planck Quiet Sky & Deng-Handley (4 chunks)
    "chunk_12": 1.38,
    "chunk_13": 1.48,
    "chunk_14": 1.58,  # Beat for 334 µK² quadrupole clamp payoff
    "chunk_15": 2.20,  # + 0.70s = 2.90s chapter break

    # Scene 04 — BABAR 14-Sigma Brick & Missing Antimatter (6 chunks)
    "chunk_16": 1.42,
    "chunk_17": 1.55,
    "chunk_18": 1.45,
    "chunk_19": 1.48,
    "chunk_20": 1.58,  # Beat after 'Where did all of the antimatter go?'
    "chunk_21": 2.25,  # + 0.70s = 2.95s chapter break after coin-sorter peak

    # Scene 05 — Honest Scorecard: CMB 3rd Peak & Kill-Switches (6 chunks)
    "chunk_22": 1.40,
    "chunk_23": 1.45,
    "chunk_24": 1.45,
    "chunk_25": 1.58,  # Beat for 99.92% zero-knob density match
    "chunk_26": 1.45,
    "chunk_27": 2.25,  # + 0.70s = 2.95s chapter break before Outro

    # Scene 06 — WeaveForge, Living Ledger & Episode 3 Preview (3 chunks)
    "chunk_28": 1.42,
    "chunk_29": 1.52,
    "chunk_30": 1.05,
}

NUM_WORD_MAP = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "ten": "10",
    "fourteen": "14",
    "thirty": "30",
}


def _norm_tok(s: str) -> str:
    t = re.sub(r"[^a-z0-9]", "", s.lower())
    return NUM_WORD_MAP.get(t, t)


def polish_ep2_whisper_words(cid: str, raw_words: List[dict], script_text: str) -> List[dict]:
    """
    Restores canonical Episode 2 proper-noun & scientific spellings (`WeaveForge`, `Gaia`,
    `Zenodo`, `Penrose`, `Landauer`, `catenoid`, `COBE`, `WMAP`, `Planck`, `Lacuna`,
    `Wei-Ning Deng`, `Turok`, `Latham`, `SLAC`, `BABAR`, `Lüders`, `Pauli`, `Schwinger`,
    `Barbour`, `Janus`, `Sakharov`, `JAXA`, `LiteBIRD`, `KATRIN`, `Euclid`, `CPT`, `QCD`,
    `stoler.systems`) while preserving exact millisecond word timestamps.
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

    cleaned: List[dict] = []
    i = 0
    while i < len(merged):
        cur = dict(merged[i])
        b0, p0 = _split_punct(cur["text"])
        l0 = b0.lower().replace("-", "")

        # 3-token phonetic collapses (`stoler dot systems`, `C P T`, `Q C D`, `Luh koo nuh`, `Zeh noh doh`)
        if i + 2 < len(merged):
            b1, _ = _split_punct(merged[i + 1]["text"])
            b2, p2 = _split_punct(merged[i + 2]["text"])
            l1_3 = b1.lower().replace("-", "")
            l2_3 = b2.lower().replace("-", "")
            if l0 in ("wayne", "wei", "way") and l1_3 in ("ning",) and l2_3 in ("dang", "deng", "ding"):
                cleaned.append({"text": "Wei-Ning", "start": cur["start"], "end": merged[i + 1]["end"]})
                cleaned.append({"text": "Deng" + p2, "start": merged[i + 2]["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if (l0, l1_3, l2_3) == ("physical", "review", "d"):
                cleaned.append({"text": "Physical", "start": cur["start"], "end": cur["end"]})
                cleaned.append({"text": "Review", "start": merged[i + 1]["start"], "end": merged[i + 1]["end"]})
                cleaned.append({"text": "D" + p2, "start": merged[i + 2]["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if l0 in ("stoler", "stoller", "stolar", "solar") and l1_3 == "dot" and l2_3.startswith("system"):
                cleaned.append({"text": "stoler.systems" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if (l0, l1_3, l2_3) == ("c", "p", "t"):
                cleaned.append({"text": "CPT" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if (l0, l1_3, l2_3) == ("q", "c", "d"):
                cleaned.append({"text": "QCD" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if l0 in ("luh", "la") and l1_3 in ("koo", "cu") and l2_3.startswith("nuh"):
                cleaned.append({"text": "Lacuna" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if l0 in ("kat", "cat") and l1_3 in ("uh", "a") and l2_3.startswith("noyd"):
                cleaned.append({"text": "catenoid" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if l0 in ("zeh", "ze") and l1_3 in ("noh", "no") and l2_3.startswith("doh"):
                cleaned.append({"text": "Zenodo" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if (l0, l1_3, l2_3) == ("d", "r", "4"):
                cleaned.append({"text": "DR4" + p2, "start": cur["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue

        # 2-token phonetic collapses (`Weave Forge`, `Light Bird`, `Buh bar`, `Way Ning`, `Too rock`, `Lay thum`, etc.)
        if i + 1 < len(merged):
            b1, p1 = _split_punct(merged[i + 1]["text"])
            l1 = b1.lower().replace("-", "")
            if (l0, l1) in {("weave", "forge"), ("we", "forge")}:
                cleaned.append({"text": "WeaveForge" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("guy", "uh"), ("gai", "a")}:
                cleaned.append({"text": "Gaia" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("buh", "bar"), ("ba", "bar"), ("bo", "bar"), ("boo", "bar")}:
                cleaned.append({"text": "BABAR" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("light", "bird"), ("lite", "bird")}:
                cleaned.append({"text": "LiteBIRD" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("kah", "treen"), ("ka", "trin")}:
                cleaned.append({"text": "KATRIN" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("yoo", "klid"), ("eu", "clid")}:
                cleaned.append({"text": "Euclid" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("koh", "bee"), ("co", "be")}:
                cleaned.append({"text": "COBE" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("w", "map"), ("double", "map")}:
                cleaned.append({"text": "WMAP" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("too", "rock"), ("tu", "rok")}:
                cleaned.append({"text": "Turok" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("lay", "thum"), ("la", "tham")}:
                cleaned.append({"text": "Latham" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("way", "ning"), ("wei", "ning")}:
                cleaned.append({"text": "Wei-Ning" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("loo", "derz"), ("loo", "ders"), ("lu", "ders")}:
                cleaned.append({"text": "Lüders" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("pow", "lee"), ("pau", "li")}:
                cleaned.append({"text": "Pauli" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("shving", "er"), ("schwing", "er")}:
                cleaned.append({"text": "Schwinger" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("jay", "nus"), ("ja", "nus")}:
                cleaned.append({"text": "Janus" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) == ("git", "hub"):
                cleaned.append({"text": "GitHub" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) in {("stoler", "systems"), ("stoller", "systems")}:
                cleaned.append({"text": "stoler.systems" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) == ("wave", "faces"):
                cleaned.append({"text": "wave", "start": cur["start"], "end": cur["end"]})
                cleaned.append({"text": "phases" + p1, "start": merged[i + 1]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (l0, l1) == ("two", "ended"):
                cleaned.append({"text": "two-ended" + p1, "start": cur["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue

        single_map = {
            "weaveforge": "WeaveForge",
            "weforge": "WeaveForge",
            "gaia": "Gaia",
            "guyuh": "Gaia",
            "zenodo": "Zenodo",
            "zehnohdoh": "Zenodo",
            "penrose": "Penrose",
            "penrohz": "Penrose",
            "penroses": "Penrose's",
            "penrose's": "Penrose's",
            "landauer": "Landauer",
            "landower": "Landauer",
            "landauers": "Landauer's",
            "landauer's": "Landauer's",
            "landowers": "Landauer's",
            "landower's": "Landauer's",
            "catenoid": "catenoid",
            "katuhnoyd": "catenoid",
            "cobe": "COBE",
            "kohbee": "COBE",
            "wmap": "WMAP",
            "planck": "Planck",
            "plahnk": "Planck",
            "plank": "Planck",
            "plonk": "Planck",
            "planck's": "Planck's",
            "plahnk's": "Planck's",
            "plank's": "Planck's",
            "plonks": "Planck's",
            "quadrupole": "quadrupole",
            "kwahdruhpohl": "quadrupole",
            "lacuna": "Lacuna",
            "laguna": "Lacuna",
            "luhkoonuh": "Lacuna",
            "weining": "Wei-Ning",
            "wayning": "Wei-Ning",
            "hanley": "Handley",
            "handlee": "Handley",
            "turok": "Turok",
            "toorock": "Turok",
            "latham": "Latham",
            "laythum": "Latham",
            "leighton": "Latham",
            "babar": "BABAR",
            "buhbar": "BABAR",
            "bubar": "BABAR",
            "bobar": "BABAR",
            "boobar": "BABAR",
            "baybar": "BABAR",
            "stoler.systems": "stoler.systems",
            "gerhard": "Gerhart",
            "luders": "Lüders",
            "lüders": "Lüders",
            "looderz": "Lüders",
            "loders": "Lüders",
            "pauli": "Pauli",
            "powlee": "Pauli",
            "schwinger": "Schwinger",
            "shvinger": "Schwinger",
            "barbour": "Barbour",
            "barbour's": "Barbour's",
            "barber's": "Barbour's",
            "janus": "Janus",
            "jaynus": "Janus",
            "sakharov": "Sakharov",
            "sahkuhroff": "Sakharov",
            "jaxa": "JAXA",
            "jaxa's": "JAXA's",
            "jax's": "JAXA's",
            "jacksuh's": "JAXA's",
            "litebird": "LiteBIRD",
            "lightbird": "LiteBIRD",
            "katrin": "KATRIN",
            "katrine": "KATRIN",
            "catrine": "KATRIN",
            "kahtreen": "KATRIN",
            "euclid": "Euclid",
            "yooklid": "Euclid",
            "cpt": "CPT",
            "qcd": "QCD",
            "python": "Python",
            "github": "GitHub",
            "taught": "taut",
            "waste": "waist",
            "diffusing": "defusing",
            "microkelvins": "microkelvin",
        }
        low_key = b0.lower()
        if low_key == "slack" and cid == "chunk_17":
            cur["text"] = "SLAC" + p0
        elif low_key in single_map:
            cur["text"] = single_map[low_key] + p0
        elif l0 in single_map:
            if low_key.endswith(("'s", "’s")) and not single_map[l0].endswith("'s"):
                cur["text"] = single_map[l0] + "'s" + p0
            else:
                cur["text"] = single_map[l0] + p0

        cleaned.append(cur)
        i += 1

    # Targeted phrase-level SRT cleanups
    for idx in range(len(cleaned) - 1):
        t0, t1 = cleaned[idx]["text"], cleaned[idx + 1]["text"]
        if cid == "chunk_01" and t0 == "disk" and t1 == "in":
            cleaned[idx + 1]["text"] = "and"
        if cid == "chunk_17" and t0 == "used" and t1 == "a":
            cleaned[idx + 1]["text"] = "the"
        if cid == "chunk_28" and t0 == "stoler.systems" and t1 == "in":
            cleaned[idx + 1]["text"] = "and"
        if cid == "chunk_29" and t0 == "video," and t1 == "Living":
            cleaned[idx]["text"] = "Video"
        if cid == "chunk_29" and t0 == "recap" and t1 in ("video,", "Video"):
            cleaned[idx]["text"] = "Recap"
        if cid == "chunk_30" and t0 == "bench" and t1 == "To":
            cleaned[idx + 1]["text"] = "to"
        if cid == "chunk_30" and t0 == "magic" and t1 == "Testing":
            cleaned[idx]["text"] = "magic—"
            cleaned[idx + 1]["text"] = "testing"

    # Ensure final word of chunk carries its canonical ending punctuation (., ?, !)
    if cleaned and script_text.strip():
        end_ch = script_text.strip().rstrip("\"'’”)")[-1]
        if end_ch in (".", "?", "!"):
            b_last, p_last = _split_punct(cleaned[-1]["text"])
            if not p_last or p_last != end_ch:
                cleaned[-1]["text"] = b_last + end_ch

    # Title-case channel name in chunk_00
    if cid == "chunk_00":
        for idx in range(len(cleaned) - 3):
            seq = [_split_punct(cleaned[idx + k]["text"])[0].lower() for k in range(4)]
            if seq == ["theoretically", "not", "a", "physicist"]:
                for k, cap in enumerate(("Theoretically", "Not", "A", "Physicist")):
                    _, pk = _split_punct(cleaned[idx + k]["text"])
                    cleaned[idx + k]["text"] = cap + pk

    canon_breaks = extract_canonical_sentence_breaks(script_text)
    used_idx = -1
    for prev_norm, next_norm, punct in canon_breaks:
        for k in range(used_idx + 1, len(cleaned) - 1):
            w_p = _norm_tok(cleaned[k]["text"].split("-")[-1])
            w_n = _norm_tok(cleaned[k + 1]["text"].split("-")[0])
            if w_p == prev_norm and w_n == next_norm:
                base_k, _ = _split_punct(cleaned[k]["text"])
                cleaned[k]["text"] = base_k + punct
                cleaned[k]["is_sentence_end"] = punct
                if cleaned[k + 1]["text"] and cleaned[k + 1]["text"][0].islower() and punct in (".", "?", "!"):
                    if not cleaned[k + 1]["text"].startswith("stoler."):
                        cleaned[k + 1]["text"] = cleaned[k + 1]["text"][0].upper() + cleaned[k + 1]["text"][1:]
                used_idx = k
                break

    return cleaned


def master_ep2_chunk_matched(pcm_48k: np.ndarray, words: List[dict], rng: np.random.Generator, cid: str) -> Tuple[np.ndarray, List[dict]]:
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

    # Gentle WSOLA tempo alignment if a TTS chunk ran brisk (> 150 WPM) so pace stays unhurried & calm
    if len(trimmed_words) >= 6:
        sp_dur = max(0.8, trimmed_words[-1]["end"] - trimmed_words[0]["start"])
        raw_wpm = len(trimmed_words) / (sp_dur / 60.0)
        if raw_wpm > 150.0:
            spd = max(0.91, 143.0 / raw_wpm)
            sliced = wsola_time_scale(sliced, spd, SR)
            for nw in trimmed_words:
                nw["start"] = round(nw["start"] / spd, 3)
                nw["end"] = round(nw["end"] / spd, 3)

    paced_pcm, paced_words, _ = expand_sentence_pauses_cleanly(sliced, trimmed_words, cid, rng)
    mastered = master_vocal_chunk(paced_pcm, SR)

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


def mix_ep2_soundtrack(voice_mono: np.ndarray, manifest_scenes: List[dict], ffmpeg_exe: str) -> np.ndarray:
    total_n = len(voice_mono)

    st02 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_02_timeless_groove.mp3", ffmpeg_exe, channels=2))
    st03 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_03_cosmic_tension.mp3", ffmpeg_exe, channels=2))
    st04 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_04_grand_horizon.mp3", ffmpeg_exe, channels=2))

    sc06 = next(s for s in manifest_scenes if s["id"] == "scene06")
    sc06_start = float(sc06["start_sec"])
    ch30_info = next(c for c in sc06["chunks"] if c["chunk_id"] == "chunk_30")
    t_ep3_teaser = sc06_start + float(ch30_info["local_start"])
    t_speech_end = sc06_start + float(ch30_info["local_end"])

    velvet_bed = np.zeros((total_n, 2), dtype=np.float64)
    xfade = int(5.0 * SR)
    pos = 0
    stems = [st04, st02, st03, st04, st02, st03]
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
    cosine_glide(int((t_ep3_teaser - 0.80) * SR), int((t_ep3_teaser + 2.50) * SR), CONST_GAIN, TEASER_GAIN)
    cosine_glide(int((t_speech_end + 0.25) * SR), int((t_speech_end + 1.65) * SR), TEASER_GAIN, OUTRO_SWELL_GAIN)

    fade_out_n = min(int(3.1 * SR), total_n - int((t_speech_end + 1.65) * SR))
    if fade_out_n > 10:
        b_env[-fade_out_n:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, fade_out_n))

    stereo = velvet_bed * b_env[:, None]
    stereo[:, 0] += voice_mono * 0.94
    stereo[:, 1] += voice_mono * 0.94
    return np.clip(stereo, -0.94, 0.94)


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

    for k in range(len(all_cues) - 1):
        cs, ce, txt = all_cues[k]
        nxt_s = all_cues[k + 1][0]
        if ce > nxt_s - 0.04:
            all_cues[k] = (cs, max(cs + 0.20, nxt_s - 0.04), txt)

    for cs, ce, txt in all_cues:
        srt_lines.append(f"{cue_idx}\n{fmt_srt_ts(cs)} --> {fmt_srt_ts(ce)}\n{wrap_srt_two_lines(txt)}\n")
        cue_idx += 1

    srt_path = EP2_DIR / "Episode_2_Upside_Down_Big_Bang_Subtitles.srt"
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    chap_titles = {
        "scene00": "Welcome Back: WeaveForge, Gaia DR4 Blind Lock & Pillar 3",
        "scene01": "Chapter 1 — Sir Roger Penrose's Paradox & The Upside-Down Hourglass",
        "scene02": "Chapter 2 — The 'Cheat-Code' Audit: Rewound Movie vs. Two-Ring Soap Film",
        "scene03": "Chapter 3 — Planck's Quiet Sky (334 µK²) & Cambridge's Quantized Curvature",
        "scene04": "Chapter 4 — Stanford's BABAR 14-Sigma Brick & Missing Antimatter",
        "scene05": "Chapter 5 — CMB Third Peak Pleat Rescue & Hard Kill-Switches",
        "scene06": "Chapter 6 — Fly Arena 4 Yourself & Episode 3 Preview (Double-Slit)",
    }
    ch_lines = ["CHAPTERS:"]
    for idx, sc in enumerate(manifest["scenes"]):
        sid = sc["id"]
        if sid not in chap_titles:
            continue
        ts_s = 0 if idx <= 1 else int(round(float(sc["start_sec"])))
        ch_lines.append(f"{ts_s // 60:02d}:{ts_s % 60:02d} {chap_titles[sid]}")

    chap_path = EP2_DIR / "Episode_2_YouTube_Chapters.txt"
    chap_path.write_text("\n".join(ch_lines) + "\n", encoding="utf-8")
    return srt_path, chap_path


def main() -> None:
    t0 = time.time()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    print("=== Step 1: Running CPU-Only Faster-Whisper Audit on All 31 Episode 2 Chunks ===", flush=True)
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "-1"
    env["NUMBA_DISABLE_CUDA"] = "1"
    subprocess.run(
        [str(VENV_VOICE_PY), str(EP2_DIR / "audit_ep2_tts_whisper.py")],
        check=True,
        env=env,
    )
    audit = json.loads((VOICE_CHUNKS_DIR / "_whisper_ep2_audit.json").read_text(encoding="utf-8"))

    print("\n=== Step 2: Sculpting Unhurried Sentence Breathing & Calm Tone Across 31 Chunks ===", flush=True)
    rng = np.random.default_rng(20261103)
    chunk_mastered: Dict[str, np.ndarray] = {}
    chunk_words: Dict[str, List[dict]] = {}
    pres_ratios: Dict[str, float] = {}

    for spec in CHUNKS:
        cid = spec["chunk_id"]
        wp = VOICE_CHUNKS_DIR / f"{cid}.wav"
        pcm_48k = decode_audio_48k(wp, ffmpeg_exe, channels=1)
        p_words = polish_ep2_whisper_words(cid, audit[cid]["words"], spec["text"])
        m_pcm, m_words = master_ep2_chunk_matched(pcm_48k, p_words, rng, cid)
        chunk_mastered[cid] = m_pcm
        chunk_words[cid] = m_words
        pres_ratios[cid] = compute_presence_ratio(m_pcm)

    med_pres = float(np.median(list(pres_ratios.values())))
    for spec in CHUNKS:
        cid = spec["chunk_id"]
        ratio_db = 20.0 * math.log10(max(pres_ratios[cid], 1e-4) / max(med_pres, 1e-4))
        nudge_db = float(np.clip(-0.65 * ratio_db, -1.5, 1.5))
        if abs(nudge_db) >= 0.18:
            b_eq, a_eq = peaking_eq_biquad(2500.0, nudge_db, 0.75, SR)
            adj = signal.filtfilt(b_eq, a_eq, chunk_mastered[cid])
            old_rms = math.sqrt(float(np.mean(chunk_mastered[cid] ** 2)) + 1e-12)
            new_rms = math.sqrt(float(np.mean(adj ** 2)) + 1e-12)
            chunk_mastered[cid] = np.clip(adj * (old_rms / new_rms), -0.88, 0.88)

    print("\n=== Step 3: Assembling Episode 2 Master Timeline & Millisecond Cue Manifest ===", flush=True)
    scenes_map: Dict[str, List[dict]] = {}
    for spec in CHUNKS:
        scenes_map.setdefault(spec["scene_id"], []).append(spec)

    manifest_scenes: List[dict] = [
        {
            "id": "intro00",
            "chapter": "EPISODE 2",
            "title": "The Upside-Down Big Bang & Where All the Antimatter Went",
            "subtitle_tag": "THEORETICALLY NOT A PHYSICIST • CHAPTER 2 DEEP DIVE",
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

            pause_after = POST_CHUNK_PAUSE_SEC.get(cid, 1.45)
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

    tail_s = 3.60
    all_voice_parts.append(np.zeros(int(round(tail_s * SR)), dtype=np.float64))
    manifest_scenes[-1]["duration_sec"] = round(manifest_scenes[-1]["duration_sec"] + tail_s, 3)
    manifest_scenes[-1]["end_sec"] = round(manifest_scenes[-1]["end_sec"] + tail_s, 3)
    running_sec += tail_s

    voice_full = np.concatenate(all_voice_parts)
    voice_stem_wav = AUDIO_V1_DIR / "episode2_v1_voice_only_mono.wav"
    with wave.open(str(voice_stem_wav), "wb") as wf_v:
        wf_v.setnchannels(1)
        wf_v.setsampwidth(2)
        wf_v.setframerate(SR)
        wf_v.writeframes((np.clip(voice_full, -0.96, 0.96) * 32767.0).astype(np.int16).tobytes())

    stereo_master = mix_ep2_soundtrack(voice_full, manifest_scenes, ffmpeg_exe)
    master_wav = AUDIO_V1_DIR / "Episode_2_Master_Audio_v1.wav"
    master_mp3 = AUDIO_V1_DIR / "Episode_2_Master_Audio_v1.mp3"
    save_wav_and_mp3(stereo_master, master_wav, master_mp3, ffmpeg_exe)
    shutil.copy2(str(master_mp3), str(ART_DIR / master_mp3.name))

    manifest = {
        "title": "Episode 2 — The Upside-Down Big Bang & Where All the Antimatter Went",
        "sample_rate": SR,
        "total_duration_sec": round(len(stereo_master) / float(SR), 3),
        "scenes": manifest_scenes,
    }
    manifest_p = AUDIO_V1_DIR / "ep2_v1_manifest.json"
    manifest_p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    srt_path, chap_path = export_standalone_srt_and_chapters(manifest)
    shutil.copy2(str(srt_path), str(ART_DIR / srt_path.name))

    tot_s = len(stereo_master) / float(SR)
    print(
        f"\n[EPISODE 2 MASTER AUDIO & .SRT READY in {time.time() - t0:.1f}s!]\n"
        f"  • Master MP3 : {master_mp3} ({int(tot_s // 60)}m {tot_s % 60:04.1f}s)\n"
        f"  • Master WAV : {master_wav}\n"
        f"  • Clean .SRT : {srt_path}\n"
        f"  • Chapters   : {chap_path}",
        flush=True,
    )


if __name__ == "__main__":
    main()
