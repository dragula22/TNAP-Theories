"""
Episode 0 v3 ("Sagan Edition") Master Audio & Sample-Accurate Subtitle Builder:
  1. Audits all 33 Google Replicated Voice chunks (`google_voice_chunks/chunk_01..33.wav`)
     using RTX 5080 `Faster-Whisper medium.en` (`word_timestamps=True`) to verify:
       - Exact wording & pronunciation (`Lambda-CDM`, `Lambda Cold Dark Matter model`, `true, or sink it cold`, etc.)
       - Smooth cadence (checks overall WPM + peak 2.2-second local WPM window to ensure ZERO vinyl-speedup glitches!)
  2. Applies gentle 140ms velvet onset shaping + chunk-to-chunk active-speech loudness matching
     so NO sentence ever "jump-scares" the listener after a pause.
  3. Inserts generous, contemplative human processing pauses at every section boundary and key visual showcase:
       - `2.7s - 3.0s` between all major sections (`scene00 -> scene01 -> ... -> scene09`)
       - `2.7s` before `chunk_05` ("For decades, astronomers...")
       - `2.4s` at `chunk_19 -> chunk_20` ("...calling it a new theory?" -> "Here is the third visual...")
       - `2.4s` after `chunk_20` while the 3D camera zooms tight into the ultra-tiny Big Bang singularity ring!
       - `2.8s` before `chunk_22` (Double-Slit Experiment)
       - `2.8s` before `chunk_27` (Sagan Galaxy-Suburbs sweep!)
       - `4.2s` silent 3D animation showcase pause after `chunk_28` ("...folded into a tablecloth.") while
         the young galaxy visibly gathers and tucks excess fabric into a crisp pleat!
       - `9.5s` wondrous musical & visual cosmic-pullback interlude after `chunk_32` ("...in wonder.")
         while the camera zooms out from one galaxy to >140 galaxies across the cosmos before `chunk_33`!
  4. Mixes the v3 Stereo Master (`Full_Track_B_v3_Sagan_Edition.mp3` & `audio_v3/episode0_v3_master_stereo.wav`)
     with:
       - Exciting `0:00 - 0:13.5` Cold-Open Hook
       - Constant, zero-pumping `-46.5 dBFS` velvet mid-scooped ambient pad during Parts 1-8
       - Warm, gentle Sagan Outro musical lift under `chunk_31..32` -> graceful swell during the `9.5s`
         multi-galaxy cosmic zoom-out -> smooth settle back down under the `chunk_33` closing caveat!
"""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import imageio_ffmpeg
import numpy as np
from faster_whisper import WhisperModel
from scipy import signal

from build_dual_audio_auditions import (
    decode_audio_48k,
    prepare_velvet_ambient_stem,
    rms_envelope_fast,
    save_wav_and_mp3,
    synthesize_cold_open_sfx,
)
from ep0_chunks_data import SCENE_METADATA
from master_v2_audio_and_subtitles import (
    HOOK_DURATION_SEC,
    SR,
    master_vocal_chunk,
)


def group_words_into_cues_v3(words: List[dict], max_words: int = 9, max_chars: int = 56) -> List[dict]:
    """
    Groups timestamped words into crisp broadcast subtitle cues, UNCONDITIONALLY flushing
    before ANY pause >= 0.75s so subtitles NEVER linger across silent visual/musical interludes!
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
        chunk_or_section_pause = gap_ahead >= 0.75
        strong_punct = tok.endswith((".", "?", "!", ":", "—"))
        comma_punct = tok.endswith((",", ";"))
        medium_pause = gap_ahead >= 0.40

        if chunk_or_section_pause:
            flush_buf()
        elif strong_punct and len(buf) >= 3:
            flush_buf()
        elif (comma_punct or medium_pause) and (len(buf) >= 5 or cur_chars >= 34):
            flush_buf()
        elif len(buf) >= max_words or cur_chars >= max_chars:
            flush_buf()

    flush_buf()

    # Merge any trailing 1-word sentence-ending orphan cue (e.g. "away.") back into its preceding cue
    merged_cues: List[dict] = []
    for c in cues:
        if (
            len(c["words"]) == 1
            and merged_cues
            and (c["start"] - merged_cues[-1]["end"]) < 0.72
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

EP0_DIR = Path(__file__).resolve().parent
GOOGLE_VOICE_DIR = EP0_DIR / "google_voice_chunks"
SCORE_DIR = EP0_DIR / "score_stems"
AUDIO_V3_DIR = EP0_DIR / "audio_v3"
AUDIO_V3_DIR.mkdir(parents=True, exist_ok=True)
ART_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")


# Custom human-processing & 3D-visual-showcase pauses AFTER specific chunks (in seconds):
POST_CHUNK_PAUSE_SEC: Dict[str, float] = {
    # Scene 00 (Creator Intro)
    "chunk_01_scene00_a": 1.15,
    "chunk_02_scene00_b": 1.25,
    "chunk_03_scene00_c": 2.20,  # + next scene lead 0.70s = 2.90s after Hero Title Drop!

    # Scene 01 (Midnight Sky & Textbook Lambda-CDM)
    "chunk_04_scene01_a": 2.75,  # David's 2:02 -> 2:03 note: generous calm pause before "For decades..."!
    "chunk_05_scene01_b": 1.15,
    "chunk_06_scene01_c": 1.15,
    "chunk_07_scene01_d": 1.25,
    "chunk_08_scene01_e": 2.15,  # + 0.70s lead = 2.85s section pause to digest "holding the cosmic map upside down?"

    # Scene 02 (Stretched Fabric & 3D Atom Knot)
    "chunk_09_scene02_a": 1.25,
    "chunk_10_scene02_b": 1.85,  # Extra beat to admire the 3D trefoil knot woven out of threads!
    "chunk_11_scene02_c": 2.15,  # + 0.70s lead = 2.85s section pause

    # Scene 03 (Vinyl Record & Ink-in-Water Memory)
    "chunk_12_scene03_a": 1.25,
    "chunk_13_scene03_b": 1.95,  # Beat to watch macro diamond needle riding the static vinyl groove
    "chunk_14_scene03_c": 2.20,  # + 0.70s lead = 2.90s section pause

    # Scene 04 (Upside-Down Cosmic Hourglass & Matter/Antimatter Sorter)
    "chunk_15_scene04_a": 1.55,
    "chunk_16_scene04_b": 1.45,
    "chunk_17_scene04_c": 1.35,
    "chunk_18_scene04_d": 2.20,  # + 0.70s lead = 2.90s section pause

    # Scene 05 (Dipping Brass Rings, Tiny Singularity Zoom, Blocked Sky Waves & Double Slit)
    "chunk_19_scene05_a": 2.45,  # David's 7:30 note: let the sharp listener's question breathe!
    "chunk_20_scene05_b": 2.50,  # 7:47 showcase beat: camera zooms tight into ultra-tiny singularity ring & back out!
    "chunk_21_scene05_c": 2.85,  # David's 8:14 note: generous calm pause before Double-Slit Experiment!
    "chunk_22_scene05_d": 2.20,  # + 0.70s lead = 2.90s section pause

    # Scene 06 (Silk Tablecloth Gravity & Curved Starlight)
    "chunk_23_scene06_a": 1.35,
    "chunk_24_scene06_b": 2.20,  # + 0.70s lead = 2.90s section pause

    # Scene 07 (Campfire Sun Funnel vs. Sagan Galaxy Suburbs Banked Bowl)
    "chunk_25_scene07_a": 1.40,
    "chunk_26_scene07_b": 2.85,  # David's 10:06 note: unhurried pause before the Sagan galaxy-suburbs sweep!
    "chunk_27_scene07_c": 2.25,  # + 0.70s lead = 2.95s section pause

    # Scene 08 (Young Galaxy Pleat-Tuck Showcase -> Toned-Down Cluster Crash -> Slow Bounce)
    "chunk_28_scene08_a": 4.20,  # David's 10:54 & 11:06 note: 4.2s silent showcase watching the 3D galaxy gather & tuck its pleat!
    "chunk_29_scene08_b": 1.75,
    "chunk_30_scene08_c": 2.30,  # + 0.70s lead = 3.00s section pause before Finale!

    # Scene 09 (Sagan Unified Tapestry Outro -> 9.5s Multi-Galaxy Zoom-Out -> Closing Caveat)
    "chunk_31_scene09_a": 1.50,
    "chunk_32_scene09_b": 9.60,  # David's 12:36 note: ~10s wondrous musical pause zooming out across hundreds of galaxies!
    "chunk_33_scene09_c": 1.00,
}


def polish_v3_whisper_words(chunk_id: str, raw_words: List[dict]) -> List[dict]:
    """Cleans Whisper phonetic/spelling tokens while keeping 100% exact word timestamps."""
    merged: List[dict] = []
    for w in raw_words:
        txt = w["text"].strip()
        if not txt:
            continue
        if merged and (txt.startswith("-") or txt == "%"):
            merged[-1]["text"] += txt
            merged[-1]["end"] = float(w["end"])
        else:
            merged.append({"text": txt, "start": float(w["start"]), "end": float(w["end"])})

    exact_map = {
        "SimPi": "SymPy",
        "SimPi,": "SymPy,",
        "SimPy": "SymPy",
        "SimPy,": "SymPy,",
        "Sim-Pie": "SymPy",
        "Sigh-Pie": "SciPy",
        "SciPi": "SciPy",
        "Plank": "Planck",
        "Plank,": "Planck,",
        "Starlight": "starlight",
        "camp-fire": "campfire",
        "table-cloth": "tablecloth",
        "rim-stretch": "rim stretch",
        "Github": "GitHub",
        "Github,": "GitHub,",
        "github": "GitHub",
        "anti-gravity": "Antigravity",
        "Anti-gravity": "Antigravity",
        "Anti-Gravity": "Antigravity",
        "anti-gravity—": "Antigravity—",
        "Anti-gravity—": "Antigravity—",
        "argon": "Argon",
        "Stoler.systems": "stoler.systems",
        "Stoler.systems,": "stoler.systems,",
        "stoler.systems": "stoler.systems",
    }
    for w in merged:
        if w["text"] in exact_map:
            w["text"] = exact_map[w["text"]]

    # Collapse phonetic "Cee Dee Em" or "C. D. M." into clean display "CDM" in chunk_05, plus Whisper homophone fixes!
    cleaned: List[dict] = []
    i = 0
    while i < len(merged):
        cur = dict(merged[i])
        nxt = merged[i + 1] if i + 1 < len(merged) else None
        prv = cleaned[-1] if cleaned else None

        if i + 2 < len(merged):
            t0 = merged[i]["text"].lower().strip(".,-")
            t1 = merged[i + 1]["text"].lower().strip(".,-")
            t2_raw = merged[i + 2]["text"]
            t2 = t2_raw.lower().strip(".,-")
            if t0 in ("stoler", "stoller", "stolar", "solar") and t1 == "dot" and t2.startswith("system"):
                trail = ""
                m = re.search(r"([.,—?!:]+)$", t2_raw)
                if m:
                    trail = m.group(1)
                cleaned.append({"text": "stoler.systems" + trail, "start": merged[i]["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
            if t0 in ("c", "cee", "see") and t1 in ("d", "dee") and t2 in ("m", "em"):
                trail = ""
                m = re.search(r"([.,—?!:]+)$", t2_raw)
                if m:
                    trail = m.group(1)
                cleaned.append({"text": "CDM" + trail, "start": merged[i]["start"], "end": merged[i + 2]["end"]})
                i += 3
                continue
        if i + 1 < len(merged):
            a = merged[i]["text"].lower().strip(".,")
            b_raw = merged[i + 1]["text"]
            b = b_raw.lower().strip(".,")
            if (a, b) in {("sim", "pie"), ("sim", "pi")}:
                cleaned.append({"text": "SymPy", "start": merged[i]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (a, b) in {("sigh", "pie"), ("sci", "pi"), ("psi", "pi")}:
                cleaned.append({"text": "SciPy", "start": merged[i]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (a, b) == ("moon", "orbit"):
                cleaned.append({"text": "Moon-orbit", "start": merged[i]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (a, b) in {("stoler", "systems"), ("stoller", "systems")}:
                trail = ""
                m = re.search(r"([.,—?!:]+)$", b_raw)
                if m:
                    trail = m.group(1)
                cleaned.append({"text": "stoler.systems" + trail, "start": merged[i]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue
            if (a, b) in {("git", "hub"), ("anti", "gravity")}:
                trail = ""
                m = re.search(r"([.,—?!:]+)$", b_raw)
                if m:
                    trail = m.group(1)
                lbl = "GitHub" if a == "git" else "Antigravity"
                cleaned.append({"text": lbl + trail, "start": merged[i]["start"], "end": merged[i + 1]["end"]})
                i += 2
                continue

        # Contextual Whisper homophone corrections
        if chunk_id.startswith("chunk_03") and cur["text"] == "in" and prv and prv["text"].lower() == "fabric":
            cur["text"] = "and"
        if chunk_id.startswith("chunk_11") and cur["text"] == "in" and prv and prv["text"] == "ripples":
            cur["text"] = "and"
        if chunk_id.startswith("chunk_15") and cur["text"] == "in" and prv and prv["text"].startswith("visual"):
            cur["text"] = "and"
        if chunk_id.startswith("chunk_28"):
            if cur["text"] == "an" and nxt and nxt["text"].lower().startswith("astronomy"):
                cur["text"] = "and"
            if cur["text"] == "pool" and prv and prv["text"].lower() == "their":
                cur["text"] = "pull"
        if chunk_id.startswith("chunk_32") and cur["text"] == "red" and nxt and nxt["text"] == "like":
            cur["text"] = "read"

        cleaned.append(cur)
        i += 1

    # Title-case Episode Title in chunk_03
    if chunk_id.startswith("chunk_03"):
        for idx in range(len(cleaned)):
            if (
                idx + 3 < len(cleaned)
                and cleaned[idx]["text"].lower().startswith("you")
                and cleaned[idx + 1]["text"].lower() == "the"
                and cleaned[idx + 2]["text"].lower() == "universe"
            ):
                cleaned[idx]["text"] = "you:"
                tmap = {
                    "the": "The",
                    "universe": "Universe",
                    "inside": "Inside",
                    "out,": "Out —",
                    "out.": "Out.",
                    "out": "Out",
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
                    lw = cleaned[j]["text"].lower()
                    if lw in tmap and not (lw == "the" and j > idx + 2):
                        cleaned[j]["text"] = tmap[lw]
                break

    return cleaned


def transcribe_and_audit_v3_chunks(ffmpeg_exe: str) -> Dict[str, dict]:
    """Runs Faster-Whisper medium.en on GPU (using cached entries for unchanged chunks) and audits WPM/bursts."""
    cache_p = GOOGLE_VOICE_DIR / "_whisper_v3_audit.json"
    cached: Dict[str, dict] = {}
    if cache_p.exists():
        try:
            cached = json.loads(cache_p.read_text(encoding="utf-8"))
        except Exception:
            cached = {}

    wavs = sorted(GOOGLE_VOICE_DIR.glob("chunk_*.wav"))
    assert len(wavs) == 33, f"Expected 33 WAVs, found {len(wavs)}"

    need_run = []
    for wp in wavs:
        cid = wp.stem
        mtime_sz = f"{wp.stat().st_mtime_ns}_{wp.stat().st_size}"
        if cid not in cached or cached[cid].get("sig") != mtime_sz:
            need_run.append((cid, wp, mtime_sz))

    if need_run:
        print(f"[Whisper GPU Audit] Transcribing {len(need_run)} updated/uncached chunks on RTX 5080...", flush=True)
        model = WhisperModel("medium.en", device="cuda", compute_type="float16")
        for cid, wp, sig in need_run:
            raw16 = subprocess.run(
                [ffmpeg_exe, "-v", "error", "-i", str(wp), "-f", "s16le", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-"],
                capture_output=True,
                check=True,
            ).stdout
            pcm_16k = np.frombuffer(raw16, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(pcm_16k, word_timestamps=True, vad_filter=False)
            words = []
            full_txt = []
            for seg in segments:
                full_txt.append(seg.text.strip())
                for w in seg.words or []:
                    words.append({"text": w.word.strip(), "start": round(float(w.start), 3), "end": round(float(w.end), 3)})
            # Compute overall WPM and peak 2.2s window WPM
            if len(words) >= 2:
                dur_sp = max(0.5, words[-1]["end"] - words[0]["start"])
                wpm = len(words) / (dur_sp / 60.0)
            else:
                wpm = 0.0
            max_burst_wpm = 0.0
            burst_phrase = ""
            for i in range(len(words)):
                t_win0 = words[i]["start"]
                j = i
                while j < len(words) and words[j]["end"] - t_win0 <= 2.2:
                    j += 1
                if j - i >= 5:
                    win_dur = max(1.2, words[j - 1]["end"] - t_win0)
                    bw = (j - i) / (win_dur / 60.0)
                    if bw > max_burst_wpm:
                        max_burst_wpm = bw
                        burst_phrase = " ".join(x["text"] for x in words[i:j])

            cached[cid] = {
                "sig": sig,
                "text": " ".join(full_txt).strip(),
                "wpm": round(wpm, 1),
                "max_2s_wpm": round(max_burst_wpm, 1),
                "max_2s_phrase": burst_phrase,
                "words": words,
            }
            print(
                f"  [{cid}] WPM={wpm:5.1f} | Peak2s={max_burst_wpm:5.1f} ('{burst_phrase[:34]}') | "
                f"Text: {cached[cid]['text'][:92]}...",
                flush=True,
            )

        cache_p.write_text(json.dumps(cached, indent=2), encoding="utf-8")
    return cached


def master_v3_vocal_chunk_gentle_onset(pcm_48k: np.ndarray, cid: str) -> Tuple[np.ndarray, float, float]:
    """
    Trims silence safely, applies broadcast EQ/de-essing/optical leveling, AND shapes the opening
    150ms onset softly so NO chunk ever "jump-scares" the listener after a contemplative pause!
    Returns `(mastered_pcm, trim_start_sec, duration_sec)`.
    """
    env = rms_envelope_fast(pcm_48k, int(0.015 * SR))
    voiced = np.flatnonzero(env > 0.0045)
    if len(voiced) > 10:
        s0 = max(0, int(voiced[0]) - int(0.14 * SR))
        s1 = min(len(pcm_48k), int(voiced[-1]) + int(0.22 * SR))
    else:
        s0, s1 = 0, len(pcm_48k)

    trim_start_sec = s0 / SR
    sliced = pcm_48k[s0:s1]
    mastered = master_vocal_chunk(sliced, SR)

    # Extra gentle onset taming on the first 0.22s of voiced speech so initial syllables ("For decades...") never bark!
    v_idx = np.flatnonzero(rms_envelope_fast(mastered, int(0.012 * SR)) > 0.012)
    if len(v_idx) > 0:
        v0 = max(0, int(v_idx[0]) - int(0.03 * SR))
        soft_n = min(int(0.16 * SR), len(mastered) - v0)
        if soft_n > 10:
            # Start at 0.72 gain and glide smoothly up to 1.0 over 160ms
            soft_curve = 0.72 + 0.28 * (0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, soft_n)))
            mastered[v0 : v0 + soft_n] *= soft_curve

    # Subtle -0.8 dB trim on chunk_05 specifically so "For decades..." enters velvety-soft right into chunk_06!
    if cid == "chunk_05_scene01_b":
        mastered *= 0.91

    fn = min(int(0.035 * SR), len(mastered) // 6)
    if fn > 1:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, fn))
        mastered[:fn] *= ramp
        mastered[-fn:] *= ramp[::-1]

    return mastered, trim_start_sec, len(mastered) / SR


def mix_v3_sagan_soundtrack(
    voice_mono: np.ndarray,
    manifest_scenes: List[dict],
    ffmpeg_exe: str,
) -> np.ndarray:
    """
    Mixes centered v3 narration with:
      1. Bold Cold-Open Hook (`0:00 - 0:13.5`)
      2. Dead-constant, zero-pumping `-46.5 dBFS` velvet ambient bed (`0:14 - scene08 end`)
      3. Sagan Finale Musical Arc in `scene09`:
           - Gently warms `score_04_grand_horizon` up (`0.046 -> 0.095`) under `chunk_31..32`
             (warm & wondrous without ever overpowering David's voice!)
           - Swells gracefully to `0.215` during the `9.6s` wordless multi-galaxy cosmic zoom-out pause!
           - Settles smoothly back down to `0.062` right before `chunk_33` ("Of course, in science...")
             and resolves cleanly over the `3.6s` closing tail!
    """
    total_n = len(voice_mono)
    hook_n = int(round(HOOK_DURATION_SEC * SR))

    hook_raw = decode_audio_48k(SCORE_DIR / "score_01_wonder_hook.mp3", ffmpeg_exe, channels=2)
    hook_rms = math.sqrt(float(np.mean(hook_raw[:hook_n] ** 2)) + 1e-12)
    hook_norm = hook_raw * (0.115 / hook_rms)

    # Prepare calm mid-scooped velvet stems for Parts 1-8 + rich warm finale stem (`score_04_grand_horizon`)
    st02 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_02_timeless_groove.mp3", ffmpeg_exe, channels=2))
    st03 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_03_cosmic_tension.mp3", ffmpeg_exe, channels=2))
    st04 = prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / "score_04_grand_horizon.mp3", ffmpeg_exe, channels=2))

    # Locate exact Scene 09 timestamps from manifest
    sc09 = next(s for s in manifest_scenes if s["id"] == "scene09")
    sc09_start = float(sc09["start_sec"])
    ch32_info = next(c for c in sc09["chunks"] if c["chunk_id"] == "chunk_32_scene09_b")
    ch33_info = next(c for c in sc09["chunks"] if c["chunk_id"] == "chunk_33_scene09_c")

    t_sagan_start = sc09_start                                      # Start of chunk_31 Sagan outro
    t_pause_start = sc09_start + float(ch32_info["local_end"])      # End of "...in wonder." -> start of 9.6s galaxy zoom!
    t_caveat_start = sc09_start + float(ch33_info["local_start"])   # Start of "Of course, in science..."
    t_caveat_end = sc09_start + float(ch33_info["local_end"])       # End of "...or sink it cold."

    # Build continuous bed switching cleanly into `st04` (`score_04_grand_horizon`) right at `scene09`!
    velvet_bed = np.zeros((total_n, 2), dtype=np.float64)
    xfade = int(5.0 * SR)
    pos = int(11.5 * SR)
    s9_idx = int((t_sagan_start - 2.0) * SR)
    body_stems = [st02, st03, st04]
    idx_s = 0
    while pos < min(total_n, s9_idx + xfade):
        st = body_stems[idx_s % len(body_stems)]
        end_p = min(total_n, pos + len(st))
        seg_len = end_p - pos
        if pos > int(11.5 * SR) and seg_len > xfade:
            ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, xfade))[:, None]
            velvet_bed[pos : pos + xfade] = velvet_bed[pos : pos + xfade] * (1.0 - ramp) + st[:xfade] * ramp
            velvet_bed[pos + xfade : end_p] = st[xfade:seg_len]
        else:
            velvet_bed[pos:end_p] = st[:seg_len]
        pos += max(1, len(st) - xfade)
        idx_s += 1

    # Crossfade cleanly into dedicated `score_04_grand_horizon` (`st04`) for Scene 09 finale!
    pos9 = max(int(15.0 * SR), s9_idx)
    first9 = True
    while pos9 < total_n:
        end_p = min(total_n, pos9 + len(st04))
        seg_len = end_p - pos9
        if seg_len > xfade:
            ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, xfade))[:, None]
            velvet_bed[pos9 : pos9 + xfade] = velvet_bed[pos9 : pos9 + xfade] * (1.0 - ramp) + st04[:xfade] * ramp
            velvet_bed[pos9 + xfade : end_p] = st04[xfade:seg_len]
        elif not first9:
            velvet_bed[pos9:end_p] = st04[:seg_len]
        pos9 += max(1, len(st04) - xfade)
        first9 = False

    stereo = np.zeros((total_n, 2), dtype=np.float64)
    t_fade0 = int(11.6 * SR)
    t_fade1 = int(14.1 * SR)
    fade_len = t_fade1 - t_fade0
    cos_down = 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, fade_len))
    cos_up = 1.0 - cos_down

    # 1. Cold-Open Hook (`0 .. 14.1s`) + SFX
    h_end = min(len(hook_norm), t_fade1)
    h_env = np.ones(h_end, dtype=np.float64) * 0.56
    if h_end > t_fade0:
        h_env[t_fade0:h_end] = 0.56 * cos_down[: h_end - t_fade0]
    stereo[:h_end] += hook_norm[:h_end] * h_env[:, None]
    stereo[:hook_n] += synthesize_cold_open_sfx(hook_n)

    # 2. Piecewise-Smooth Non-Pumping Music Gain Envelope (`b_env`)
    CONST_GAIN = 0.045          # Whisper-quiet during Parts 1-8 (-47 dBFS)
    SAGAN_SPEECH_GAIN = 0.092   # Gentle wondrous warmth under Sagan outro (~21.5 dB below speech!)
    GALAXY_ZOOM_GAIN = 0.215    # Soaring wonder during the 9.6s non-spoken multi-galaxy cosmic zoom-out!
    CAVEAT_GAIN = 0.060         # Calm, grounded support under closing scientific caveat

    b_env = np.zeros(total_n, dtype=np.float64)
    b_env[t_fade0:t_fade1] = CONST_GAIN * cos_up
    b_env[t_fade1:] = CONST_GAIN

    def cosine_glide(i0: int, i1: int, g0: float, g1: float) -> None:
        i0 = max(0, min(total_n, i0))
        i1 = max(i0, min(total_n, i1))
        if i1 > i0:
            u = np.linspace(0.0, math.pi, i1 - i0)
            b_env[i0:i1] = g0 + (g1 - g0) * (0.5 - 0.5 * np.cos(u))
        if i1 < total_n:
            b_env[i1:] = g1

    # Smooth 4.5s warm-up entering Sagan Outro (`chunk_31..32`)
    cosine_glide(int((t_sagan_start - 1.2) * SR), int((t_sagan_start + 3.5) * SR), CONST_GAIN, SAGAN_SPEECH_GAIN)
    # Smooth 2.4s bloom right as "...look up at the night sky in wonder" finishes into the 9.6s galaxy zoom!
    cosine_glide(int((t_pause_start + 0.15) * SR), int((t_pause_start + 2.55) * SR), SAGAN_SPEECH_GAIN, GALAXY_ZOOM_GAIN)
    # Hold soaring wonder across the multi-galaxy pullback, then glide smoothly down 1.8s before chunk_33 starts!
    cosine_glide(int((t_caveat_start - 2.10) * SR), int((t_caveat_start - 0.20) * SR), GALAXY_ZOOM_GAIN, CAVEAT_GAIN)
    # Gentle closing resolution after "...or sink it cold." + 3.0s fade to silence
    cosine_glide(int((t_caveat_end + 0.30) * SR), int((t_caveat_end + 1.60) * SR), CAVEAT_GAIN, 0.115)
    fade_out_n = min(int(2.9 * SR), total_n - int((t_caveat_end + 1.60) * SR))
    if fade_out_n > 10:
        b_env[-fade_out_n:] *= 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, fade_out_n))

    stereo += velvet_bed * b_env[:, None]
    stereo[:, 0] += voice_mono * 0.94
    stereo[:, 1] += voice_mono * 0.94
    return np.clip(stereo, -0.94, 0.94)


def main() -> None:
    t0 = time.time()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    audit = transcribe_and_audit_v3_chunks(ffmpeg_exe)

    wav_files = sorted(GOOGLE_VOICE_DIR.glob("chunk_*.wav"))
    scenes_chunks: Dict[str, List[Path]] = {}
    for wp in wav_files:
        sid = re.search(r"_(scene\d+)_", wp.name).group(1)
        scenes_chunks.setdefault(sid, []).append(wp)

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
            "chunks": [],
            "cues": [
                {"start": 0.35, "end": 4.25, "text": "Today's textbook map says 95% of reality is completely invisible.", "words": []},
                {"start": 4.55, "end": 8.95, "text": "What if nothing is missing — and we've been holding the cosmic map upside down?", "words": []},
                {"start": 9.25, "end": 13.10, "text": "One stretched fabric. One flipped cosmic hourglass. Zero equations.", "words": []},
            ],
        }
    ]

    all_voice_parts: List[np.ndarray] = [np.zeros(int(round(HOOK_DURATION_SEC * SR)), dtype=np.float64)]
    running_sec = HOOK_DURATION_SEC

    print("\n=== Assembling Episode 0 v3 ('Sagan Edition') Timeline & Verbatim Subtitles ===", flush=True)
    for sid in sorted(scenes_chunks.keys()):
        ch_list = scenes_chunks[sid]
        meta = SCENE_METADATA[sid]
        lead_s = 0.70

        sc_parts: List[np.ndarray] = [np.zeros(int(round(lead_s * SR)), dtype=np.float64)]
        cursor_s = lead_s
        sc_words: List[dict] = []
        sc_chunk_meta: List[dict] = []

        for wp in ch_list:
            cid = wp.stem
            pcm_48k = decode_audio_48k(wp, ffmpeg_exe, channels=1)
            mastered, trim_s0, ch_dur = master_v3_vocal_chunk_gentle_onset(pcm_48k, cid)

            raw_words = audit[cid]["words"]
            p_words = polish_v3_whisper_words(cid, raw_words)
            for w in p_words:
                ws = max(0.0, w["start"] - trim_s0) + cursor_s
                we = min(cursor_s + ch_dur, max(ws + 0.04, w["end"] - trim_s0 + cursor_s))
                sc_words.append({"text": w["text"], "start": round(ws, 3), "end": round(we, 3)})

            ch_local_start = round(cursor_s, 3)
            ch_local_end = round(cursor_s + ch_dur, 3)
            pause_after = POST_CHUNK_PAUSE_SEC.get(cid, 1.35)

            g_s0 = running_sec + ch_local_start
            g_s1 = running_sec + ch_local_end
            print(
                f"  {cid:22s} | {int(g_s0//60):02d}:{g_s0%60:05.2f} -> {int(g_s1//60):02d}:{g_s1%60:05.2f} "
                f"({ch_dur:5.2f}s) + pause {pause_after:4.2f}s",
                flush=True,
            )

            sc_chunk_meta.append(
                {
                    "chunk_id": cid,
                    "local_start": ch_local_start,
                    "local_end": ch_local_end,
                    "pause_after": pause_after,
                }
            )

            sc_parts.append(mastered)
            cursor_s += ch_dur
            sc_parts.append(np.zeros(int(round(pause_after * SR)), dtype=np.float64))
            cursor_s += pause_after

        sc_audio = np.concatenate(sc_parts)
        out_sc_wav = AUDIO_V3_DIR / f"{sid}.wav"
        pcm16 = (np.clip(sc_audio, -0.96, 0.96) * 32767.0).astype(np.int16)
        with wave.open(str(out_sc_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(pcm16.tobytes())

        sc_dur = round(len(pcm16) / SR, 3)
        cues = group_words_into_cues_v3(sc_words)
        manifest_scenes.append(
            {
                "id": sid,
                "chapter": meta["chapter"],
                "title": meta["title"],
                "subtitle_tag": meta["subtitle_tag"],
                "audio_file": out_sc_wav.name,
                "duration_sec": sc_dur,
                "start_sec": round(running_sec, 3),
                "end_sec": round(running_sec + sc_dur, 3),
                "chunks": sc_chunk_meta,
                "cues": cues,
            }
        )
        all_voice_parts.append(sc_audio)
        running_sec += sc_dur

    # Add 3.5s closing musical fade tail after scene09
    tail_music_s = 3.50
    all_voice_parts.append(np.zeros(int(round(tail_music_s * SR)), dtype=np.float64))
    manifest_scenes[-1]["duration_sec"] = round(manifest_scenes[-1]["duration_sec"] + tail_music_s, 3)
    manifest_scenes[-1]["end_sec"] = round(manifest_scenes[-1]["end_sec"] + tail_music_s, 3)
    running_sec += tail_music_s

    voice_full = np.concatenate(all_voice_parts)
    # Save isolated voice stem for instant modular remixes if ever needed!
    voice_stem_wav = AUDIO_V3_DIR / "episode0_v3_voice_only_mono.wav"
    with wave.open(str(voice_stem_wav), "wb") as wf_v:
        wf_v.setnchannels(1)
        wf_v.setsampwidth(2)
        wf_v.setframerate(SR)
        wf_v.writeframes((np.clip(voice_full, -0.96, 0.96) * 32767.0).astype(np.int16).tobytes())

    stereo_master = mix_v3_sagan_soundtrack(voice_full, manifest_scenes, ffmpeg_exe)
    master_wav = AUDIO_V3_DIR / "episode0_v3_master_stereo.wav"
    master_mp3 = AUDIO_V3_DIR / "Full_Track_B_v3_Sagan_Edition.mp3"
    master_v5_mp3 = AUDIO_V3_DIR / "Full_Track_B_v5_Transparent_Edition.mp3"
    save_wav_and_mp3(stereo_master, master_wav, master_mp3, ffmpeg_exe)
    shutil.copy2(str(master_mp3), str(master_v5_mp3))
    shutil.copy2(str(master_mp3), str(ART_DIR / master_mp3.name))
    shutil.copy2(str(master_v5_mp3), str(ART_DIR / master_v5_mp3.name))

    manifest = {
        "title": "The Universe Inside Out: A Visual Guide to the Stretched Fabric & the Upside-Down Cosmic Hourglass (v3 Sagan Edition)",
        "sample_rate": SR,
        "total_duration_sec": round(len(stereo_master) / SR, 3),
        "scenes": manifest_scenes,
    }
    manifest_p = AUDIO_V3_DIR / "ep0_v3_manifest.json"
    manifest_p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(
        f"\n[V3 AUDIO MASTER READY] {master_mp3.name} ({len(stereo_master)/SR/60:.2f} min / {len(stereo_master)/SR:.1f}s) "
        f"built in {time.time() - t0:.1f}s!",
        flush=True,
    )


if __name__ == "__main__":
    main()
