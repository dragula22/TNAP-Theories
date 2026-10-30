"""
Builds BOTH Complete Mastered Episode 0 Audio Tracks (and 95-second Quick-Compare Clips)
so David can audition and choose BEFORE locking the final 1080p video render:

  - Track A (`Full_Track_A_David_Real_Voice_Episode0.mp3` / `.wav`):
      100% David's real studio voice, enhanced with:
        1. Verified Quiet-Valley Internal Pause Sculpting (tightens 1.0s-2.4s teleprompter line-wrap
           hesitations down to natural 0.16s-0.46s storyteller beats via 40ms room-tone cosine crossfades,
           never touching consonants or words)
        2. Gentle Pitch-Preserving Time-Domain WSOLA Cadence Smoothing (±5% max toward ~154 WPM)
        3. Warm Broadcast Vocal EQ + Optical Leveling

  - Track B (`Full_Track_B_Google_Replicated_Voice_Episode0.mp3` / `.wav`):
      100% Google `gemini-3.8-flash-tts` Replicated David Voice (`voice_rjo5kexogz91`) across all 33 chunks,
      matched to the exact same broadcast vocal loudness.

  - Shared Fixed Music Architecture (ZERO Volume-Knob Pumping!):
      - `0:00 - 0:13.5`: Exciting Cold-Open Hook (`score_01_wonder_hook` + cinema sub-bass booms & riser)
      - `0:12.0 - 0:14.6`: ONE single smooth fade down into a whisper-quiet ambient bed
      - `0:14.6 - End of Speech`: 100% CONSTANT-FADER (`-28.5 dB` below voice), dynamically pre-leveled,
        mid-scooped (`-7 dB @ 1.3 kHz`) velvet ambient music cushion — ZERO sidechain pumping on breaths/pauses,
        ZERO orchestral crescendos competing with speech!
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
from scipy import signal

from ep0_chunks_data import SCENE_METADATA
from master_v2_audio_and_subtitles import (
    HOOK_DURATION_SEC,
    SR,
    group_words_into_cues,
    master_vocal_chunk,
    peaking_eq_biquad,
    polish_chunk_words,
)

EP0_DIR = Path(__file__).resolve().parent
RAW_VOICE_DIR = EP0_DIR / "my_narration"
GOOGLE_VOICE_DIR = EP0_DIR / "google_voice_chunks"
SCORE_DIR = EP0_DIR / "score_stems"
AUDITION_DIR = EP0_DIR / "audio_auditions"
AUDITION_DIR.mkdir(parents=True, exist_ok=True)

ART_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")


# ---------------------------------------------------------------------------
# 1. Broadcast Dialogue Pacing Sculptor + Time-Domain WSOLA (For Track A)
# ---------------------------------------------------------------------------

def rms_envelope_fast(x: np.ndarray, win_samples: int) -> np.ndarray:
    pad = np.pad(x * x, (win_samples // 2, win_samples - win_samples // 2), mode="edge")
    cs = np.cumsum(pad, dtype=np.float64)
    return np.sqrt(np.maximum(0.0, (cs[win_samples:] - cs[:-win_samples]) / float(win_samples)))


def tighten_internal_pauses(
    x: np.ndarray, words: List[dict], fs: int = SR
) -> Tuple[np.ndarray, List[dict], float]:
    """
    Finds awkward teleprompter eye-wrap pauses inside a chunk, verifies low-energy room tone
    inside each gap so consonants/breaths are NEVER clipped, and tightens excess silence cleanly
    using 40ms cosine crossfades. Returns `(edited_audio, updated_words, seconds_trimmed)`.
    """
    if len(words) < 2:
        return x, words, 0.0

    env = rms_envelope_fast(x, max(1, int(0.015 * fs)))
    xfade_n = int(0.040 * fs)  # 40ms invisible room-tone crossfade

    # Collect verified silence excisions `(cut_start_sample, cut_end_sample)` in original sample coords
    cuts: List[Tuple[int, int]] = []
    for k in range(len(words) - 1):
        w_cur = words[k]
        w_nxt = words[k + 1]
        gap = w_nxt["start"] - w_cur["end"]
        tok = w_cur["text"]

        if tok.endswith((".", "?", "!", ":")):
            target_gap = 0.45
        elif tok.endswith((",", ";", "—")):
            target_gap = 0.23
        else:
            target_gap = 0.14

        if gap <= target_gap + 0.11:
            continue

        # Search strictly inside [w_cur.end + 55ms, w_nxt.start - 55ms] for verified quiet room tone
        s_lo = int((w_cur["end"] + 0.055) * fs)
        s_hi = int((w_nxt["start"] - 0.055) * fs)
        if s_hi - s_lo < int(0.14 * fs):
            continue

        seg_env = env[s_lo:s_hi]
        quiet_thresh = max(0.008, float(np.percentile(env, 25)) * 2.2)
        quiet_mask = seg_env < quiet_thresh

        # Find longest contiguous True run in `quiet_mask`
        padded = np.concatenate([[False], quiet_mask, [False]])
        starts = np.flatnonzero(padded[1:] & ~padded[:-1])
        ends = np.flatnonzero(~padded[1:] & padded[:-1])
        if len(starts) == 0:
            continue
        best_idx = int(np.argmax(ends - starts))
        q0 = s_lo + int(starts[best_idx])
        q1 = s_lo + int(ends[best_idx])
        q_len_sec = (q1 - q0) / fs

        desired_remove = gap - target_gap
        safe_remove = min(desired_remove, q_len_sec - 0.08)
        if safe_remove < 0.07:
            continue

        rem_n = int(safe_remove * fs)
        q_mid = (q0 + q1) // 2
        c0 = max(q0 + xfade_n // 2, q_mid - rem_n // 2)
        c1 = min(q1 - xfade_n // 2, c0 + rem_n)
        if c1 - c0 >= xfade_n:
            cuts.append((c0, c1))

    if not cuts:
        return x, [dict(w) for w in words], 0.0

    # Splice audio with smooth 40ms cosine crossfades and update word timestamps
    out_segs: List[np.ndarray] = []
    new_words = [dict(w) for w in words]
    cursor = 0
    total_removed_samples = 0

    ramp_out = 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, xfade_n))
    ramp_in = 1.0 - ramp_out

    for c0, c1 in cuts:
        if c0 <= cursor + xfade_n or c1 + xfade_n >= len(x):
            continue
        # Keep everything up to c0, then crossfade [c0 : c0+xfade_n] with [c1 : c1+xfade_n]
        out_segs.append(x[cursor:c0])
        xf_seg = x[c0 : c0 + xfade_n] * ramp_out + x[c1 : c1 + xfade_n] * ramp_in
        out_segs.append(xf_seg)
        removed = c1 - c0
        total_removed_samples += removed
        cut_t_orig = c0 / fs
        rem_sec = removed / fs
        for nw in new_words:
            if nw["start"] >= cut_t_orig:
                nw["start"] -= rem_sec
                nw["end"] -= rem_sec
        cursor = c1 + xfade_n

    out_segs.append(x[cursor:])
    return np.concatenate(out_segs), new_words, total_removed_samples / fs


def wsola_time_scale(x: np.ndarray, speed: float, fs: int = SR) -> np.ndarray:
    """
    Pitch-preserving Waveform Similarity Overlap-Add (WSOLA) time-domain speech rate adjuster.
    At `speed in [0.95, 1.06]`, preserves 100% natural vocal formants & pitch with zero FFT phasiness!
    """
    if abs(speed - 1.0) < 0.012:
        return x.copy()

    win_n = int(0.030 * fs)      # 30ms Hann grain
    hop_s = win_n // 2           # 15ms synthesis hop (exact 50% Hann COLA!)
    tol_n = int(0.008 * fs)      # ±8ms pitch-period correlation search window

    hann = np.hanning(win_n)
    n_in = len(x)
    n_out = int(round(n_in / speed))
    out = np.zeros(n_out + win_n * 2, dtype=np.float64)
    norm = np.zeros(n_out + win_n * 2, dtype=np.float64)

    # First frame
    out[:win_n] += x[:win_n] * hann
    norm[:win_n] += hann
    prev_in_pos = 0
    out_pos = hop_s

    while out_pos + win_n < n_out:
        ideal_in = int(round(out_pos * speed))
        # Natural continuation from previous chosen grain (`prev_in_pos + hop_s`)
        ref_pos = prev_in_pos + hop_s
        s_min = max(0, ideal_in - tol_n)
        s_max = min(n_in - win_n - 1, ideal_in + tol_n)
        if s_max <= s_min or ref_pos + hop_s >= n_in:
            best_in = max(0, min(n_in - win_n - 1, ideal_in))
        else:
            # Align with natural continuation `x[ref_pos : ref_pos + hop_s]` via fast cross-correlation
            target_tail = x[ref_pos : ref_pos + hop_s]
            t_energy = float(np.dot(target_tail, target_tail))
            if t_energy < 1e-7:
                best_in = ideal_in
            else:
                search_strip = x[s_min : s_max + hop_s]
                corr = signal.correlate(search_strip, target_tail, mode="valid")
                best_in = s_min + int(np.argmax(corr))

        grain = x[best_in : best_in + win_n]
        out[out_pos : out_pos + win_n] += grain * hann
        norm[out_pos : out_pos + win_n] += hann
        prev_in_pos = best_in
        out_pos += hop_s

    valid = norm > 1e-4
    out[valid] /= norm[valid]
    return out[:n_out]


# ---------------------------------------------------------------------------
# 2. Velvet, Constant-Volume, Mid-Scooped Music Bed Builder (ZERO Pumping!)
# ---------------------------------------------------------------------------

def decode_audio_48k(path: Path, ffmpeg_exe: str, channels: int = 2) -> np.ndarray:
    cmd = [
        ffmpeg_exe, "-v", "error", "-i", str(path),
        "-f", "s16le", "-acodec", "pcm_s16le", "-ar", str(SR), "-ac", str(channels), "-",
    ]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    return pcm.reshape(-1, channels) if channels > 1 else pcm


def synthesize_cold_open_sfx(hook_samples: int) -> np.ndarray:
    sfx = np.zeros((hook_samples, 2), dtype=np.float64)
    t = np.arange(hook_samples, dtype=np.float64) / SR
    for t_hit in (0.25, 4.60, 9.25):
        dt = t - t_hit
        mask = (dt >= 0.0) & (dt <= 2.6)
        tau = dt[mask]
        phase = 2.0 * math.pi * (29.0 * tau + 29.0 * 0.38 * (1.0 - np.exp(-tau / 0.38)))
        env = (1.0 - np.exp(-tau / 0.018)) * np.exp(-tau / 0.95)
        boom = 0.34 * np.sin(phase) * env + 0.09 * np.sin(2.0 * phase) * env * np.exp(-tau / 0.35)
        sfx[mask, 0] += boom
        sfx[mask, 1] += boom

    r_mask = (t >= 10.2) & (t <= 13.35)
    rt = (t[r_mask] - 10.2) / 3.15
    r_env = (rt ** 2.0) * np.sin(math.pi * np.minimum(1.0, rt)) * 0.095
    sfx[r_mask, 0] += r_env * (np.sin(2 * math.pi * 293.66 * t[r_mask]) + 0.5 * np.sin(2 * math.pi * 440.0 * t[r_mask]))
    sfx[r_mask, 1] += r_env * (np.sin(2 * math.pi * 294.2 * t[r_mask]) + 0.5 * np.sin(2 * math.pi * 587.33 * t[r_mask]))
    return sfx


def prepare_velvet_ambient_stem(raw_st: np.ndarray) -> np.ndarray:
    """
    Transforms a raw music stem into a flat-dynamics, vocal-pocketed ambient documentary pad:
      1. 2.2-second sliding RMS leveler removes ALL internal crescendos / organ swells!
      2. Broad -7.0 dB vocal-band EQ scoop at 1,300 Hz + 6.5 kHz warm low-pass rolloff so
         the music sits behind the human voice and never competes with words!
    """
    st = raw_st.copy()
    mono_sq = 0.5 * (st[:, 0] ** 2 + st[:, 1] ** 2)
    win = int(2.2 * SR)
    pad = np.pad(mono_sq, (win // 2, win - win // 2), mode="edge")
    cs = np.cumsum(pad, dtype=np.float64)
    local_rms = np.sqrt(np.maximum(1e-8, (cs[win:] - cs[:-win]) / float(win)))

    # Level local RMS tightly toward 0.10 (clamping gain on ultra-quiet tails so noise isn't boosted)
    gain = np.clip(0.10 / np.maximum(local_rms, 0.015), 0.18, 2.2)
    # Extra 1.5s smoothing on gain so leveling itself is 100% imperceptible
    g_pad = np.pad(gain, (win // 2, win - win // 2), mode="edge")
    g_cs = np.cumsum(g_pad, dtype=np.float64)
    smooth_gain = (g_cs[win:] - g_cs[:-win]) / float(win)
    st *= smooth_gain[:, None]

    # Carve out human speech frequencies (-7.0 dB @ 1300 Hz, Q=0.55) + gentle 6.5 kHz warmth low-pass
    b_eq, a_eq = peaking_eq_biquad(1300.0, -7.0, 0.55, SR)
    sos_lp = signal.butter(2, 6500.0 / (0.5 * SR), btype="lowpass", output="sos")
    for ch in (0, 1):
        st[:, ch] = signal.filtfilt(b_eq, a_eq, st[:, ch])
        st[:, ch] = signal.sosfiltfilt(sos_lp, st[:, ch])

    # Normalize final velvet stem RMS to exact 0.100
    final_rms = math.sqrt(float(np.mean(st * st)) + 1e-12)
    return st * (0.100 / final_rms)


def mix_voice_with_constant_velvet_music(
    voice_mono: np.ndarray, last_speech_sec: float, ffmpeg_exe: str
) -> np.ndarray:
    """
    Mixes centered voice (`-18.2 dBFS` active RMS) with:
      - Exciting 13.5s Cold-Open Hook (`0:00 - 0:13.5`)
      - ONE smooth transition (`11.8s - 14.3s`) down to a DEAD-CONSTANT, ZERO-PUMPING
        whisper-quiet velvet ambient bed (`RMS = 0.0046` = `-28.8 dB` below voice!)
    """
    total_n = len(voice_mono)
    hook_n = int(round(HOOK_DURATION_SEC * SR))

    # 1. Cold-Open Hook music (`score_01_wonder_hook.mp3`, first 15.0s only — BEFORE the loud organ climax!)
    hook_raw = decode_audio_48k(SCORE_DIR / "score_01_wonder_hook.mp3", ffmpeg_exe, channels=2)
    hook_rms = math.sqrt(float(np.mean(hook_raw[:hook_n] ** 2)) + 1e-12)
    hook_norm = hook_raw * (0.115 / hook_rms)

    # 2. Narrated-body calm ambient stems (`score_02` & `score_04` pre-flattened & mid-scooped!)
    calm_files = ["score_02_timeless_groove.mp3", "score_04_grand_horizon.mp3", "score_03_cosmic_tension.mp3"]
    velvet_stems = [
        prepare_velvet_ambient_stem(decode_audio_48k(SCORE_DIR / fn, ffmpeg_exe, channels=2))
        for fn in calm_files
        if (SCORE_DIR / fn).exists()
    ]

    velvet_bed = np.zeros((total_n, 2), dtype=np.float64)
    xfade = int(5.0 * SR)
    pos = int(11.5 * SR)
    idx_s = 0
    while pos < total_n:
        st = velvet_stems[idx_s % len(velvet_stems)]
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

    # 3. Build the two completely independent non-pumping envelopes:
    #    - Hook envelope: bold at 0.56 (`0..11.8s`), glides smoothly to 0.0 at `14.2s` (before David's first word!)
    #    - Velvet bed envelope: glides smoothly from 0.0 at `11.8s` to ONE ROCK-STEADY CONSTANT `0.046`
    #      (`0.100 * 0.046 = 0.0046 RMS` = `-46.7 dBFS` = ~28.5 dB quieter than speech!) and NEVER MOVES during speech!
    stereo = np.zeros((total_n, 2), dtype=np.float64)

    t_fade0 = int(11.6 * SR)
    t_fade1 = int(14.1 * SR)
    fade_len = t_fade1 - t_fade0
    cos_down = 0.5 + 0.5 * np.cos(np.linspace(0.0, math.pi, fade_len))
    cos_up = 1.0 - cos_down

    # Add Cold-Open Hook (`0 .. 14.1s`) + Cold-Open SFX
    h_end = min(len(hook_norm), t_fade1)
    h_env = np.ones(h_end, dtype=np.float64) * 0.56
    if h_end > t_fade0:
        h_env[t_fade0:h_end] = 0.56 * cos_down[: h_end - t_fade0]
    stereo[:h_end] += hook_norm[:h_end] * h_env[:, None]
    stereo[:hook_n] += synthesize_cold_open_sfx(hook_n)

    # Add CONSTANT-VOLUME Velvet Ambient Bed (`11.6s .. end` — ZERO sidechain pumping!)
    CONST_BED_GAIN = 0.046
    b_env = np.zeros(total_n, dtype=np.float64)
    b_env[t_fade0:t_fade1] = CONST_BED_GAIN * cos_up
    b_env[t_fade1:] = CONST_BED_GAIN

    # Gentle outro swell AFTER the very last spoken word + 3.0s fade to silence
    t_outro = min(total_n - int(3.5 * SR), int((last_speech_sec + 0.35) * SR))
    if t_outro > t_fade1:
        tail_n = total_n - t_outro
        sw_up = min(int(1.4 * SR), tail_n // 3)
        if sw_up > 10:
            b_env[t_outro : t_outro + sw_up] = CONST_BED_GAIN + 0.038 * (0.5 - 0.5 * np.cos(np.linspace(0, math.pi, sw_up)))
            b_env[t_outro + sw_up :] = CONST_BED_GAIN + 0.038
        fade_out_n = min(int(2.8 * SR), tail_n)
        b_env[-fade_out_n:] *= 0.5 + 0.5 * np.cos(np.linspace(0, math.pi, fade_out_n))

    stereo += velvet_bed * b_env[:, None]

    # Add crisp centered narrator voice
    stereo[:, 0] += voice_mono * 0.94
    stereo[:, 1] += voice_mono * 0.94
    return np.clip(stereo, -0.94, 0.94)


def save_wav_and_mp3(stereo: np.ndarray, wav_path: Path, mp3_path: Path, ffmpeg_exe: str) -> None:
    pcm16 = (stereo * 32767.0).astype(np.int16)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())

    subprocess.run(
        [
            ffmpeg_exe, "-y", "-v", "error",
            "-i", str(wav_path),
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(mp3_path),
        ],
        check=True,
    )


# ---------------------------------------------------------------------------
# 3. Build Track A (Pacing-Polished Real Voice) & Track B (Google Replicated Voice)
# ---------------------------------------------------------------------------

def build_track_a_real_voice(ffmpeg_exe: str) -> Tuple[Path, Path]:
    print("\n=== Building Track A: David's Real Voice (Internal Pacing Sculpted + Constant Velvet Music) ===", flush=True)
    audit = json.loads((RAW_VOICE_DIR / "_verbatim_whisper_medium_audit.json").read_text(encoding="utf-8"))

    scenes_chunks: Dict[str, List[dict]] = {}
    for ch in audit["chunks"]:
        sid = re.search(r"_(scene\d+)_", ch["file"]).group(1)
        scenes_chunks.setdefault(sid, []).append(ch)

    rng = np.random.default_rng(108)
    all_parts: List[np.ndarray] = [np.zeros(int(round(HOOK_DURATION_SEC * SR)), dtype=np.float64)]
    running_sec = HOOK_DURATION_SEC
    total_trimmed_pauses = 0.0
    manifest_scenes: List[dict] = [
        {
            "id": "hook00",
            "chapter": "THE UNIVERSE INSIDE OUT",
            "title": "Cold Open: 95% Missing — Or Map Upside Down?",
            "subtitle_tag": "VISUAL COSMOLOGY TOUR • ZERO EQUATIONS",
            "duration_sec": HOOK_DURATION_SEC,
            "start_sec": 0.0,
            "end_sec": HOOK_DURATION_SEC,
            "cues": [],
        }
    ]

    for sid in sorted(scenes_chunks.keys()):
        ch_list = scenes_chunks[sid]
        meta = SCENE_METADATA[sid]
        lead_s = 0.75 if sid == "scene00" else 0.50
        gap_s = 0.34
        tail_s = 0.70

        sc_parts: List[np.ndarray] = [rng.normal(0.0, 0.00018, int(lead_s * SR))]
        cursor_s = lead_s
        sc_words: List[dict] = []

        for idx, ch in enumerate(ch_list):
            with wave.open(str(RAW_VOICE_DIR / ch["file"]), "rb") as wf:
                raw_pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0

            p_words = polish_chunk_words(ch["file"], ch["words"])
            t0_trim = max(0.0, p_words[0]["start"] - 0.18)
            t1_trim = min(len(raw_pcm) / SR, p_words[-1]["end"] + 0.24)
            sliced = raw_pcm[int(t0_trim * SR) : int(t1_trim * SR)]
            local_words = [
                {"text": w["text"], "start": max(0.0, w["start"] - t0_trim), "end": max(0.04, w["end"] - t0_trim)}
                for w in p_words
            ]

            # Step A1: Verified Quiet-Valley Internal Pause Tightening!
            tight_pcm, tight_words, trimmed_s = tighten_internal_pauses(sliced, local_words, SR)
            total_trimmed_pauses += trimmed_s

            # Step A2: Gentle WSOLA Tempo Smoothing (±5% max toward 154 WPM)
            sp_dur = max(0.5, tight_words[-1]["end"] - tight_words[0]["start"])
            wpm = len(tight_words) / (sp_dur / 60.0)
            if wpm < 144.0:
                spd = min(1.055, 152.0 / max(100.0, wpm))
            elif wpm > 170.0:
                spd = max(0.955, 162.0 / wpm)
            else:
                spd = 1.0

            if abs(spd - 1.0) >= 0.012:
                tight_pcm = wsola_time_scale(tight_pcm, spd, SR)
                for w in tight_words:
                    w["start"] /= spd
                    w["end"] /= spd

            # Step A3: Broadcast Vocal Polish + Smooth Edge Fades
            mastered = master_vocal_chunk(tight_pcm, SR)
            fn = min(int(0.030 * SR), len(mastered) // 6)
            if fn > 1:
                ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, fn))
                mastered[:fn] *= ramp
                mastered[-fn:] *= ramp[::-1]

            for w in tight_words:
                sc_words.append({"text": w["text"], "start": w["start"] + cursor_s, "end": w["end"] + cursor_s})

            sc_parts.append(mastered)
            cursor_s += len(mastered) / SR
            if idx < len(ch_list) - 1:
                sc_parts.append(rng.normal(0.0, 0.00018, int(gap_s * SR)))
                cursor_s += gap_s

        sc_parts.append(rng.normal(0.0, 0.00018, int(tail_s * SR)))
        sc_audio = np.concatenate(sc_parts)
        sc_dur = round(len(sc_audio) / SR, 3)

        manifest_scenes.append(
            {
                "id": sid,
                "chapter": meta["chapter"],
                "title": meta["title"],
                "subtitle_tag": meta["subtitle_tag"],
                "duration_sec": sc_dur,
                "start_sec": round(running_sec, 3),
                "end_sec": round(running_sec + sc_dur, 3),
                "cues": group_words_into_cues(sc_words),
            }
        )
        all_parts.append(sc_audio)
        running_sec += sc_dur

    # Add 2.8s calm music tail after final scene
    last_speech_sec = running_sec - 0.70
    all_parts.append(np.zeros(int(2.8 * SR), dtype=np.float64))
    voice_full = np.concatenate(all_parts)

    print(f"  [Track A Pacing] Tightened {total_trimmed_pauses:.1f}s of mid-chunk teleprompter hesitations cleanly!")
    stereo = mix_voice_with_constant_velvet_music(voice_full, last_speech_sec, ffmpeg_exe)

    wav_full = AUDITION_DIR / "Full_Track_A_David_Real_Voice_Episode0.wav"
    mp3_full = AUDITION_DIR / "Full_Track_A_David_Real_Voice_Episode0.mp3"
    save_wav_and_mp3(stereo, wav_full, mp3_full, ffmpeg_exe)

    # Also save 95s Quick-Compare Clip (Cold Open -> Creator Intro -> Part 1 start!)
    mp3_qc = AUDITION_DIR / "QuickCompare_A_MyVoice_Polished_95s.mp3"
    wav_qc = AUDITION_DIR / "_tmp_qc_a.wav"
    save_wav_and_mp3(stereo[: int(95.0 * SR)], wav_qc, mp3_qc, ffmpeg_exe)
    wav_qc.unlink(missing_ok=True)

    (AUDITION_DIR / "manifest_track_a.json").write_text(
        json.dumps({"total_duration_sec": round(len(stereo) / SR, 3), "scenes": manifest_scenes}, indent=2),
        encoding="utf-8",
    )
    print(f"  [Track A Saved] {mp3_full.name} ({len(stereo)/SR/60:.2f} min)", flush=True)
    return mp3_full, mp3_qc


def build_track_b_google_voice(ffmpeg_exe: str) -> Tuple[Path, Path]:
    print("\n=== Building Track B: Google Gemini 3.8 Replicated Voice + Constant Velvet Music ===", flush=True)
    wav_files = sorted(GOOGLE_VOICE_DIR.glob("chunk_*.wav"))
    assert len(wav_files) == 33, f"Expected 33 Google TTS chunks, found {len(wav_files)}"

    scenes_chunks: Dict[str, List[Path]] = {}
    for wp in wav_files:
        sid = re.search(r"_(scene\d+)_", wp.name).group(1)
        scenes_chunks.setdefault(sid, []).append(wp)

    all_parts: List[np.ndarray] = [np.zeros(int(round(HOOK_DURATION_SEC * SR)), dtype=np.float64)]
    running_sec = HOOK_DURATION_SEC

    for sid in sorted(scenes_chunks.keys()):
        ch_list = scenes_chunks[sid]
        lead_s = 0.75 if sid == "scene00" else 0.50
        gap_s = 0.36
        tail_s = 0.70

        sc_parts: List[np.ndarray] = [np.zeros(int(lead_s * SR), dtype=np.float64)]
        for idx, wp in enumerate(ch_list):
            pcm_48k = decode_audio_48k(wp, ffmpeg_exe, channels=1)
            # Safe trim of leading/trailing digital silence
            env = rms_envelope_fast(pcm_48k, int(0.015 * SR))
            voiced = np.flatnonzero(env > 0.005)
            if len(voiced) > 10:
                s0 = max(0, int(voiced[0]) - int(0.12 * SR))
                s1 = min(len(pcm_48k), int(voiced[-1]) + int(0.20 * SR))
                pcm_48k = pcm_48k[s0:s1]

            # Match active loudness cleanly to the exact same broadcast level as Track A!
            mastered = master_vocal_chunk(pcm_48k, SR)
            fn = min(int(0.025 * SR), len(mastered) // 6)
            if fn > 1:
                ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, math.pi, fn))
                mastered[:fn] *= ramp
                mastered[-fn:] *= ramp[::-1]

            sc_parts.append(mastered)
            if idx < len(ch_list) - 1:
                sc_parts.append(np.zeros(int(gap_s * SR), dtype=np.float64))

        sc_parts.append(np.zeros(int(tail_s * SR), dtype=np.float64))
        sc_audio = np.concatenate(sc_parts)
        all_parts.append(sc_audio)
        running_sec += len(sc_audio) / SR

    last_speech_sec = running_sec - 0.70
    all_parts.append(np.zeros(int(2.8 * SR), dtype=np.float64))
    voice_full = np.concatenate(all_parts)

    stereo = mix_voice_with_constant_velvet_music(voice_full, last_speech_sec, ffmpeg_exe)

    wav_full = AUDITION_DIR / "Full_Track_B_Google_Replicated_Voice_Episode0.wav"
    mp3_full = AUDITION_DIR / "Full_Track_B_Google_Replicated_Voice_Episode0.mp3"
    save_wav_and_mp3(stereo, wav_full, mp3_full, ffmpeg_exe)

    mp3_qc = AUDITION_DIR / "QuickCompare_B_GoogleVoice_95s.mp3"
    wav_qc = AUDITION_DIR / "_tmp_qc_b.wav"
    save_wav_and_mp3(stereo[: int(95.0 * SR)], wav_qc, mp3_qc, ffmpeg_exe)
    wav_qc.unlink(missing_ok=True)

    print(f"  [Track B Saved] {mp3_full.name} ({len(stereo)/SR/60:.2f} min)", flush=True)
    return mp3_full, mp3_qc


def main() -> None:
    t0 = time.time()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    mp3_a, qc_a = build_track_a_real_voice(ffmpeg_exe)
    mp3_b, qc_b = build_track_b_google_voice(ffmpeg_exe)

    for p in (mp3_a, qc_a, mp3_b, qc_b):
        shutil.copy2(str(p), str(ART_DIR / p.name))

    print(f"\n[BOTH MASTER AUDITION TRACKS READY in {time.time() - t0:.1f}s!]", flush=True)


if __name__ == "__main__":
    main()
