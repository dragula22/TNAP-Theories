"""
Flagship Episode 0 — Full-Script Chunked Teleprompter & Clean Take Studio.

Features built for David:
  • All 31 bite-sized chunks (3-part Personal Intro + Parts 1-9 of Episode 0)
  • Saves ONE clean 48 kHz studio WAV per chunk in `episode0_flagship/my_narration/`
    (zero duplicate copies cluttering the folder!)
  • Dedicated [🗑 Delete Take] button (or Delete key) removes a take you don't like immediately
  • Instant [▶ Play Take] / [■ Stop Audio] audition right inside the app
  • Clickable 31-chunk progress sidebar + [Jump to Next Unrecorded] so you can take breaks anytime
  • Live Fifine USB mic selector (bypasses NVIDIA Broadcast) + real-time sweet-spot dB meter
  • Adjustable teleprompter font size (A- / A+) + Spacebar record toggle

Launch:
  Double-click `Record_Episode_0_Narration.bat`
  or run: `c:\\Projects\\Discovery\\.venv\\Scripts\\python.exe c:\\Projects\\Discovery\\episode0_flagship\\ep0_teleprompter_studio.py`
"""

from __future__ import annotations

import math
import sys
import threading
import wave
from pathlib import Path
from typing import List, Optional

import numpy as np
import sounddevice as sd

EP0_DIR = Path(__file__).resolve().parent
if str(EP0_DIR) not in sys.path:
    sys.path.insert(0, str(EP0_DIR))

from ep0_chunks_data import CHUNKS  # noqa: E402

NARRATION_DIR = EP0_DIR / "my_narration"
NARRATION_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 48000


def find_best_fifine_input_device() -> Optional[int]:
    """Prefers WASAPI or DirectSound raw 'fifine Microphone', avoiding NVIDIA Broadcast."""
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    candidates = []
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] <= 0:
            continue
        name_l = dev["name"].lower()
        if "broadcast" in name_l:
            continue
        api_name = hostapis[dev["hostapi"]]["name"].lower()
        score = 0
        if "fifine" in name_l:
            score += 100
        elif "usb" in name_l or "microphone" in name_l:
            score += 45
        if "wasapi" in api_name:
            score += 20
        elif "directsound" in api_name or "wdm" in api_name:
            score += 10
        candidates.append((score, idx))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def clean_and_trim_studio_48k(raw_48k: np.ndarray) -> np.ndarray:
    """
    1. Removes DC offset & gentle <70 Hz desk rumble (zero-phase FFT filter)
    2. Gently trims dead button-click silence at start/end while keeping natural 0.22s/0.28s breath pads
    3. Leaves your natural vocal tone 100% untouched (no AI processing!)
    """
    if len(raw_48k) < int(0.25 * SAMPLE_RATE):
        return raw_48k.astype(np.float32)

    # Trim first 60 ms & last 60 ms mouse-click transients if recording > 0.6s
    if len(raw_48k) > int(0.6 * SAMPLE_RATE):
        c_trim = int(0.06 * SAMPLE_RATE)
        x = raw_48k[c_trim:-c_trim].astype(np.float64)
    else:
        x = raw_48k.astype(np.float64)

    x = x - float(np.mean(x))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / SAMPLE_RATE)
    spec = np.fft.rfft(x)
    hp = 1.0 / (1.0 + (68.0 / np.maximum(freqs, 1e-3)) ** 4)
    y = np.fft.irfft(spec * hp, n=len(x)).astype(np.float32)

    # Gentle envelope-based leading/trailing silence trim (preserves soft breaths & consonants)
    win = int(0.025 * SAMPLE_RATE)  # 25 ms window
    if len(y) > win * 8:
        sq = y * y
        csum = np.cumsum(np.insert(sq, 0, 0.0))
        rms_env = np.sqrt((csum[win:] - csum[:-win]) / float(win))
        noise_floor = float(np.percentile(rms_env, 12))
        peak_rms = float(np.max(rms_env))
        thresh = max(noise_floor * 2.8, peak_rms * 0.018, 1.5e-4)
        active = np.where(rms_env > thresh)[0]
        if len(active) > 0:
            s_idx = max(0, int(active[0]) - int(0.22 * SAMPLE_RATE))
            e_idx = min(len(y), int(active[-1]) + win + int(0.28 * SAMPLE_RATE))
            y = y[s_idx:e_idx]

    # Gentle 25 ms cosine fade-in/out so zero clicks at chunk boundaries
    fade_n = min(int(0.025 * SAMPLE_RATE), len(y) // 4)
    if fade_n > 8:
        ramp = (0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, fade_n)))).astype(np.float32)
        y[:fade_n] *= ramp
        y[-fade_n:] *= ramp[::-1]

    return np.clip(y, -0.999, 0.999)


def save_wav_mono16(path: Path, samples: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    pcm16 = (np.clip(samples, -0.999, 0.999) * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())


def wav_duration_sec(path: Path) -> Optional[float]:
    if not path.exists() or path.stat().st_size < 100:
        return None
    try:
        with wave.open(str(path), "rb") as wf:
            return wf.getnframes() / float(max(1, wf.getframerate()))
    except Exception:
        return None


def chunk_wav_path(chunk: dict) -> Path:
    return NARRATION_DIR / f"{chunk['chunk_id']}.wav"


def generate_markdown_script() -> Path:
    """Exports EPISODE_0_RECORDING_CHUNKS_SCRIPT.md from the exact 31 teleprompter chunks."""
    md_path = EP0_DIR / "EPISODE_0_RECORDING_CHUNKS_SCRIPT.md"
    lines = [
        f"# Flagship Episode 0 — Full Recording Script ({len(CHUNKS)} Bite-Sized Chunks)",
        "",
        "> **How to Record:**",
        "> - Double-click [`Record_Episode_0_Narration.bat`](Record_Episode_0_Narration.bat) to open the **Teleprompter Studio**.",
        "> - Every chunk saves **one single `.wav` file** inside `c:\\Projects\\Discovery\\episode0_flagship\\my_narration\\`.",
        "> - Don't like how a take came out? Click **`🗑 Delete Take`** (or just hit **`● RECORD`** again to overwrite it cleanly—zero extra copies accumulate in the folder!).",
        "> - Take water breaks anytime—your progress (`✓ Recorded`) is saved automatically per chunk.",
        "",
        "---",
    ]
    cur_scene = None
    for ch in CHUNKS:
        if ch["scene_id"] != cur_scene:
            cur_scene = ch["scene_id"]
            lines.append("")
            lines.append(f"## {ch['chapter']}: {ch['scene_title']}")
            lines.append("")
        lines.append(f"### Chunk {ch['num']:02d} of {len(CHUNKS)} — *{ch['label']}* (`{ch['chunk_id']}.wav`)")
        lines.append(f"- **Delivery Note:** {ch['coaching']}")
        lines.append(f"> {ch['text']}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def run_self_test() -> int:
    md_out = generate_markdown_script()
    dev_idx = find_best_fifine_input_device()
    t = np.linspace(0.0, 1.4, int(1.4 * SAMPLE_RATE), endpoint=False)
    sig = np.zeros_like(t, dtype=np.float32)
    sig[int(0.3 * SAMPLE_RATE) : int(1.1 * SAMPLE_RATE)] = (
        0.25 * np.sin(2.0 * np.pi * 190.0 * t[: int(0.8 * SAMPLE_RATE)])
    ).astype(np.float32)
    cleaned = clean_and_trim_studio_48k(sig)
    test_wav = NARRATION_DIR / "_selftest_tmp.wav"
    save_wav_mono16(test_wav, cleaned)
    dur = wav_duration_sec(test_wav)
    test_wav.unlink(missing_ok=True)
    assert dur is not None and 0.8 <= dur <= 1.4
    print(f"Self-test PASSED: {len(CHUNKS)} chunks | Script exported to {md_out.name} | Fifine idx={dev_idx}")
    return 0


def launch_gui() -> None:
    import tkinter as tk
    from tkinter import ttk

    generate_markdown_script()

    root = tk.Tk()
    root.title(f"Episode 0 Teleprompter Studio — David's Narration ({len(CHUNKS)} Chunks)")
    root.geometry("1240x780")
    root.minsize(1060, 680)
    root.configure(bg="#090d16")

    input_devices = []
    for idx, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            api = sd.query_hostapis()[d["hostapi"]]["name"]
            input_devices.append((idx, f"[{idx}] {d['name']} ({api})"))

    best_idx = find_best_fifine_input_device()

    # Start on first unrecorded chunk so resuming after a break is instant!
    first_unrec = next((i for i, c in enumerate(CHUNKS) if wav_duration_sec(chunk_wav_path(c)) is None), 0)
    cur_idx = tk.IntVar(value=first_unrec)
    font_size = tk.IntVar(value=22)
    auto_advance = tk.BooleanVar(value=False)

    is_recording = False
    recorded_buffers: List[np.ndarray] = []
    live_db = -60.0
    live_peak_db = -60.0
    stream_lock = threading.Lock()
    active_stream: Optional[sd.InputStream] = None

    # =========================================================================
    # TOP HEADER + PROGRESS BAR
    # =========================================================================
    hdr = tk.Frame(root, bg="#0f172a", padx=20, pady=12)
    hdr.pack(fill="x")

    hdr_top = tk.Frame(hdr, bg="#0f172a")
    hdr_top.pack(fill="x")
    tk.Label(
        hdr_top,
        text="THE UNIVERSE INSIDE OUT — EPISODE 0 TELEPROMPTER STUDIO",
        font=("Segoe UI", 15, "bold"),
        fg="#38bdf8",
        bg="#0f172a",
    ).pack(side="left")

    prog_lbl = tk.Label(
        hdr_top,
        text=f"Recorded: 0 / {len(CHUNKS)} chunks (0.0 min)",
        font=("Segoe UI", 11, "bold"),
        fg="#34d399",
        bg="#0f172a",
    )
    prog_lbl.pack(side="right")

    tk.Label(
        hdr,
        text="Shortcuts:  [Space] Start / Stop Recording   •   [P] Play Take   •   [Delete] Delete Take   •   [← / →] Prev / Next Chunk",
        font=("Segoe UI", 9),
        fg="#94a3b8",
        bg="#0f172a",
    ).pack(anchor="w", pady=(3, 0))

    # =========================================================================
    # MIC INPUT + FONT CONTROLS + LIVE SWEET-SPOT METER
    # =========================================================================
    top_bar = tk.Frame(root, bg="#090d16", padx=20, pady=8)
    top_bar.pack(fill="x")

    tk.Label(top_bar, text="Mic:", font=("Segoe UI", 10, "bold"), fg="#e2e8f0", bg="#090d16").pack(side="left")
    dev_names = [label for _, label in input_devices]
    dev_var = tk.StringVar()
    default_sel = 0
    for i, (d_id, _) in enumerate(input_devices):
        if d_id == best_idx:
            default_sel = i
            break
    if dev_names:
        dev_var.set(dev_names[default_sel])

    dev_combo = ttk.Combobox(top_bar, textvariable=dev_var, values=dev_names, state="readonly", width=52)
    dev_combo.pack(side="left", padx=8)

    def jump_next_unrecorded() -> None:
        if is_recording:
            return
        start = cur_idx.get()
        for offset in range(1, len(CHUNKS) + 1):
            cand = (start + offset) % len(CHUNKS)
            if wav_duration_sec(chunk_wav_path(CHUNKS[cand])) is None:
                cur_idx.set(cand)
                refresh_view()
                return
        status_lbl.config(text="🎉 All 31 chunks are recorded! You are ready to build Episode 0!", fg="#34d399")

    tk.Button(
        top_bar,
        text="⏭ Next Unrecorded",
        command=jump_next_unrecorded,
        font=("Segoe UI", 9, "bold"),
        bg="#1e293b",
        fg="#38bdf8",
        padx=10,
        pady=3,
    ).pack(side="left", padx=8)

    def adjust_font(delta: int) -> None:
        nv = max(16, min(32, font_size.get() + delta))
        font_size.set(nv)
        prompt_text.configure(font=("Segoe UI", nv, "bold"))

    tk.Button(top_bar, text="A+", command=lambda: adjust_font(2), font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#e2e8f0", padx=8).pack(side="right", padx=2)
    tk.Button(top_bar, text="A-", command=lambda: adjust_font(-2), font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#e2e8f0", padx=8).pack(side="right", padx=2)
    tk.Label(top_bar, text="Text Size:", font=("Segoe UI", 9), fg="#94a3b8", bg="#090d16").pack(side="right", padx=4)

    meter_frame = tk.Frame(root, bg="#090d16", padx=20, pady=2)
    meter_frame.pack(fill="x")
    meter_label = tk.Label(
        meter_frame,
        text="Live Mic Level: -60.0 dB",
        font=("Consolas", 10, "bold"),
        fg="#34d399",
        bg="#090d16",
    )
    meter_label.pack(anchor="w")
    meter_canvas = tk.Canvas(meter_frame, height=20, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
    meter_canvas.pack(fill="x", pady=3)

    # =========================================================================
    # MAIN BODY: LEFT CHUNK CHECKLIST + RIGHT TELEPROMPTER CARD
    # =========================================================================
    body = tk.Frame(root, bg="#090d16", padx=20, pady=6)
    body.pack(fill="both", expand=True)

    # Left Sidebar (31 Chunks)
    side = tk.Frame(body, bg="#0f172a", width=305, highlightbackground="#1e293b", highlightthickness=1)
    side.pack(side="left", fill="y", padx=(0, 14))
    side.pack_propagate(False)

    tk.Label(
        side,
        text=f"{len(CHUNKS)} SCRIPT CHUNKS (Click to Jump)",
        font=("Segoe UI", 10, "bold"),
        fg="#94a3b8",
        bg="#0f172a",
        pady=8,
    ).pack(fill="x")

    list_frame = tk.Frame(side, bg="#0f172a")
    list_frame.pack(fill="both", expand=True, padx=6, pady=(0, 8))
    scrollbar = tk.Scrollbar(list_frame, orient="vertical")
    chunk_listbox = tk.Listbox(
        list_frame,
        yscrollcommand=scrollbar.set,
        bg="#0b1120",
        fg="#cbd5e1",
        selectbackground="#0284c7",
        selectforeground="#ffffff",
        font=("Consolas", 10),
        activestyle="none",
        borderwidth=0,
        highlightthickness=0,
    )
    scrollbar.config(command=chunk_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    chunk_listbox.pack(side="left", fill="both", expand=True)

    # Right Teleprompter Card
    card = tk.Frame(body, bg="#111827", padx=28, pady=20, highlightbackground="#38bdf8", highlightthickness=1)
    card.pack(side="left", fill="both", expand=True)

    scene_badge_lbl = tk.Label(card, text="", font=("Segoe UI", 11, "bold"), fg="#38bdf8", bg="#111827")
    scene_badge_lbl.pack(anchor="w")

    chunk_hdr_lbl = tk.Label(card, text="", font=("Segoe UI", 15, "bold"), fg="#fbbf24", bg="#111827")
    chunk_hdr_lbl.pack(anchor="w", pady=(2, 2))

    coach_lbl = tk.Label(
        card,
        text="",
        font=("Segoe UI", 10, "italic"),
        fg="#94a3b8",
        bg="#111827",
        wraplength=820,
        justify="left",
    )
    coach_lbl.pack(anchor="w", pady=(0, 14))

    # Scrollable, crisp, large-type Teleprompter Text widget (read-only)
    prompt_text = tk.Text(
        card,
        font=("Segoe UI", font_size.get(), "bold"),
        fg="#f8fafc",
        bg="#0b1120",
        wrap="word",
        padx=22,
        pady=20,
        relief="flat",
        highlightthickness=1,
        highlightbackground="#1e293b",
        spacing1=6,
        spacing2=8,
        spacing3=6,
        height=7,
    )
    prompt_text.pack(fill="both", expand=True)
    prompt_text.configure(state="disabled")

    file_info_lbl = tk.Label(
        card,
        text="",
        font=("Consolas", 10),
        fg="#94a3b8",
        bg="#111827",
    )
    file_info_lbl.pack(anchor="w", pady=(10, 2))

    status_lbl = tk.Label(
        card,
        text="Ready! Press [Space] or click [● RECORD CHUNK] to start.",
        font=("Segoe UI", 11, "bold"),
        fg="#38bdf8",
        bg="#111827",
    )
    status_lbl.pack(anchor="w", pady=(2, 0))

    # =========================================================================
    # BOTTOM CONTROLS BAR (WITH DELETE TAKE + PLAY + STOP + RECORD)
    # =========================================================================
    ctrl = tk.Frame(root, bg="#090d16", padx=20, pady=12)
    ctrl.pack(fill="x")

    def get_selected_device_id() -> Optional[int]:
        sel = dev_var.get()
        for d_id, label in input_devices:
            if label == sel:
                return d_id
        return best_idx

    def audio_callback(indata: np.ndarray, frames: int, time_info, status) -> None:
        nonlocal live_db, live_peak_db
        mono = indata[:, 0].copy()
        rms = float(np.sqrt(np.mean(mono * mono)) + 1e-9)
        pk = float(np.max(np.abs(mono)) + 1e-9)
        live_db = max(-60.0, 20.0 * math.log10(rms))
        live_peak_db = max(-60.0, live_peak_db - 0.65, 20.0 * math.log10(pk))
        if is_recording:
            with stream_lock:
                recorded_buffers.append(mono)

    def restart_monitor_stream(*_) -> None:
        nonlocal active_stream
        if active_stream is not None:
            try:
                active_stream.stop()
                active_stream.close()
            except Exception:
                pass
            active_stream = None
        dev_id = get_selected_device_id()
        try:
            active_stream = sd.InputStream(
                device=dev_id,
                channels=1,
                samplerate=SAMPLE_RATE,
                dtype="float32",
                blocksize=1024,
                callback=audio_callback,
            )
            active_stream.start()
        except Exception as exc:
            status_lbl.config(text=f"Mic warning: {exc}", fg="#f43f5e")

    dev_combo.bind("<<ComboboxSelected>>", restart_monitor_stream)

    def populate_sidebar() -> None:
        chunk_listbox.delete(0, "end")
        done_count = 0
        total_sec = 0.0
        for i, ch in enumerate(CHUNKS):
            dur = wav_duration_sec(chunk_wav_path(ch))
            short_lbl = ch["label"].split("—")[0].strip()
            if dur is not None:
                done_count += 1
                total_sec += dur
                row_txt = f"✓ {ch['num']:02d} | {short_lbl:<10} ({dur:4.1f}s)"
                chunk_listbox.insert("end", row_txt)
                chunk_listbox.itemconfig(i, fg="#34d399")
            else:
                row_txt = f"○ {ch['num']:02d} | {short_lbl}"
                chunk_listbox.insert("end", row_txt)
                chunk_listbox.itemconfig(i, fg="#94a3b8")

        sel_i = cur_idx.get()
        chunk_listbox.selection_clear(0, "end")
        chunk_listbox.selection_set(sel_i)
        chunk_listbox.see(sel_i)
        prog_lbl.config(
            text=f"Recorded: {done_count} / {len(CHUNKS)} chunks  ({total_sec/60.0:.1f} min saved)",
            fg="#34d399" if done_count == len(CHUNKS) else "#38bdf8",
        )

    def refresh_view() -> None:
        idx = cur_idx.get()
        ch = CHUNKS[idx]
        p = chunk_wav_path(ch)
        dur = wav_duration_sec(p)
        word_cnt = len(ch["text"].split())
        est_sec = max(8, int(round(word_cnt / 2.45)))

        scene_badge_lbl.config(text=f"{ch['chapter']}  •  {ch['scene_title']}")
        if dur is not None:
            chunk_hdr_lbl.config(text=f"Chunk {ch['num']:02d} of {len(CHUNKS)} — {ch['label']}   [✓ SAVED: {dur:.1f}s]", fg="#34d399")
            file_info_lbl.config(text=f"File on disk: {p.name} ({dur:.1f}s) — Re-recording overwrites cleanly, or click [🗑 Delete Take].", fg="#34d399")
            del_btn.config(state="normal", bg="#7f1d1d", fg="#fecdd3")
            play_btn.config(state="normal")
        else:
            chunk_hdr_lbl.config(text=f"Chunk {ch['num']:02d} of {len(CHUNKS)} — {ch['label']}   [~{est_sec}s read]", fg="#fbbf24")
            file_info_lbl.config(text=f"Target file: {p.name} (Not recorded yet — folder stays empty until you record)", fg="#94a3b8")
            del_btn.config(state="disabled", bg="#1e293b", fg="#64748b")
            play_btn.config(state="disabled")

        coach_lbl.config(text=f"Director Note: {ch['coaching']}")
        prompt_text.configure(state="normal")
        prompt_text.delete("1.0", "end")
        prompt_text.insert("1.0", f"“{ch['text']}”")
        prompt_text.configure(state="disabled")
        populate_sidebar()

    def on_listbox_select(_event) -> None:
        if is_recording:
            return
        sel = chunk_listbox.curselection()
        if sel:
            sd.stop()
            cur_idx.set(int(sel[0]))
            refresh_view()

    chunk_listbox.bind("<<ListboxSelect>>", on_listbox_select)

    def toggle_record(*_) -> None:
        nonlocal is_recording, recorded_buffers
        idx = cur_idx.get()
        ch = CHUNKS[idx]
        out_p = chunk_wav_path(ch)

        if not is_recording:
            sd.stop()
            with stream_lock:
                recorded_buffers = []
            is_recording = True
            card.configure(highlightbackground="#e11d48", highlightthickness=2)
            rec_btn.config(text="■ STOP & SAVE  [Space]", bg="#e11d48", fg="#ffffff")
            status_lbl.config(text="● RECORDING LIVE... Read naturally at your own pace, then press [Space] or click STOP.", fg="#fb7185")
        else:
            is_recording = False
            card.configure(highlightbackground="#38bdf8", highlightthickness=1)
            rec_btn.config(text="● RECORD CHUNK  [Space]", bg="#0284c7", fg="#ffffff")
            with stream_lock:
                if not recorded_buffers:
                    status_lbl.config(text="No audio captured!", fg="#f43f5e")
                    return
                raw_48k = np.concatenate(recorded_buffers)

            raw_dur = len(raw_48k) / float(SAMPLE_RATE)
            if raw_dur < 1.0:
                status_lbl.config(text="Take was shorter than 1 second — discarded so your folder stays clean.", fg="#fbbf24")
                return

            raw_peak = float(np.max(np.abs(raw_48k))) + 1e-9
            peak_db = 20.0 * math.log10(raw_peak)
            cleaned = clean_and_trim_studio_48k(raw_48k)
            save_wav_mono16(out_p, cleaned, SAMPLE_RATE)
            saved_dur = len(cleaned) / float(SAMPLE_RATE)

            refresh_view()
            if peak_db > -0.4:
                status_lbl.config(
                    text=f"⚠ Saved {out_p.name} ({saved_dur:.1f}s), BUT mic clipped ({peak_db:.1f} dB)! Click [🗑 Delete Take] & lower Fifine knob slightly.",
                    fg="#fbbf24",
                )
            elif peak_db < -32.0:
                status_lbl.config(
                    text=f"⚠ Saved {out_p.name} ({saved_dur:.1f}s), but very quiet ({peak_db:.1f} dB). Speak 6-8 in from mic or raise knob.",
                    fg="#fbbf24",
                )
            else:
                msg = f"✓ Saved {out_p.name} ({saved_dur:.1f}s, clean peak {peak_db:.1f} dB)! Press [P] to listen or [Delete] to scrap."
                status_lbl.config(text=msg, fg="#34d399")
                if auto_advance.get() and idx < len(CHUNKS) - 1:
                    cur_idx.set(idx + 1)
                    refresh_view()

    def play_current_take(*_) -> None:
        if is_recording:
            return
        ch = CHUNKS[cur_idx.get()]
        p = chunk_wav_path(ch)
        if not p.exists():
            status_lbl.config(text="No saved take for this chunk yet — press [Space] to record!", fg="#fbbf24")
            return
        with wave.open(str(p), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            sd.stop()
            sd.play(arr, wf.getframerate())
        status_lbl.config(text=f"▶ Playing {p.name}... (Click [■ Stop Audio] or [🗑 Delete Take] anytime)", fg="#38bdf8")

    def stop_playback(*_) -> None:
        sd.stop()
        if not is_recording:
            status_lbl.config(text="■ Playback stopped.", fg="#94a3b8")

    def delete_current_take(*_) -> None:
        if is_recording:
            return
        sd.stop()
        ch = CHUNKS[cur_idx.get()]
        p = chunk_wav_path(ch)
        if p.exists():
            p.unlink(missing_ok=True)
            refresh_view()
            status_lbl.config(
                text=f"🗑 Deleted {p.name} from folder! Ready whenever you want to re-record.",
                fg="#fb7185",
            )
        else:
            status_lbl.config(text="Nothing to delete for this chunk.", fg="#94a3b8")

    def prev_chunk(*_) -> None:
        if is_recording:
            return
        sd.stop()
        cur_idx.set(max(0, cur_idx.get() - 1))
        refresh_view()

    def next_chunk(*_) -> None:
        if is_recording:
            return
        sd.stop()
        cur_idx.set(min(len(CHUNKS) - 1, cur_idx.get() + 1))
        refresh_view()

    tk.Button(ctrl, text="← Prev", command=prev_chunk, font=("Segoe UI", 11, "bold"), bg="#1e293b", fg="#e2e8f0", padx=14, pady=8).pack(side="left")

    rec_btn = tk.Button(
        ctrl,
        text="● RECORD CHUNK  [Space]",
        command=toggle_record,
        font=("Segoe UI", 12, "bold"),
        bg="#0284c7",
        fg="#ffffff",
        padx=20,
        pady=8,
    )
    rec_btn.pack(side="left", padx=12)

    play_btn = tk.Button(
        ctrl,
        text="▶ Play Take [P]",
        command=play_current_take,
        font=("Segoe UI", 11, "bold"),
        bg="#1e293b",
        fg="#34d399",
        padx=14,
        pady=8,
    )
    play_btn.pack(side="left", padx=4)

    tk.Button(
        ctrl,
        text="■ Stop Audio",
        command=stop_playback,
        font=("Segoe UI", 10, "bold"),
        bg="#1e293b",
        fg="#cbd5e1",
        padx=10,
        pady=8,
    ).pack(side="left", padx=4)

    del_btn = tk.Button(
        ctrl,
        text="🗑 Delete Take [Del]",
        command=delete_current_take,
        font=("Segoe UI", 11, "bold"),
        bg="#7f1d1d",
        fg="#fecdd3",
        padx=14,
        pady=8,
    )
    del_btn.pack(side="left", padx=12)

    tk.Button(ctrl, text="Next →", command=next_chunk, font=("Segoe UI", 11, "bold"), bg="#1e293b", fg="#fbbf24", padx=16, pady=8).pack(side="right")

    tk.Checkbutton(
        ctrl,
        text="Auto-advance on save",
        variable=auto_advance,
        font=("Segoe UI", 9),
        bg="#090d16",
        fg="#94a3b8",
        selectcolor="#1e293b",
        activebackground="#090d16",
        activeforeground="#e2e8f0",
    ).pack(side="right", padx=12)

    # Keyboard shortcuts
    root.bind("<space>", lambda e: toggle_record())
    root.bind("<KeyPress-p>", lambda e: play_current_take())
    root.bind("<KeyPress-P>", lambda e: play_current_take())
    root.bind("<Delete>", lambda e: delete_current_take())
    root.bind("<Left>", lambda e: prev_chunk())
    root.bind("<Right>", lambda e: next_chunk())

    def update_ui_meter() -> None:
        w = max(200, meter_canvas.winfo_width())
        meter_canvas.delete("all")
        frac = max(0.0, min(1.0, (live_db + 60.0) / 60.0))
        pk_frac = max(0.0, min(1.0, (live_peak_db + 60.0) / 60.0))
        sx0, sx1 = int(w * (36.0 / 60.0)), int(w * (57.0 / 60.0))  # -24 dB to -3 dB sweet spot
        meter_canvas.create_rectangle(sx0, 0, sx1, 20, fill="#064e3b", outline="")
        bar_col = "#34d399" if live_peak_db < -3.0 else ("#fbbf24" if live_peak_db < -1.0 else "#f43f5e")
        meter_canvas.create_rectangle(0, 3, int(w * frac), 17, fill=bar_col, outline="")
        meter_canvas.create_line(int(w * pk_frac), 0, int(w * pk_frac), 20, fill="#f8fafc", width=2)

        zone = "SWEET SPOT ✓" if -24.0 <= live_peak_db <= -3.0 else ("TOO HOT / CLIPPING!" if live_peak_db > -3.0 else "Quiet / Room Tone")
        meter_label.config(text=f"Live Mic Level: {live_db:5.1f} dB  |  Peak: {live_peak_db:5.1f} dB  [{zone}]", fg=bar_col)
        root.after(40, update_ui_meter)

    def on_close() -> None:
        if active_stream is not None:
            try:
                active_stream.stop()
                active_stream.close()
            except Exception:
                pass
        sd.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    refresh_view()
    restart_monitor_stream()
    update_ui_meter()
    root.mainloop()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(run_self_test())
    launch_gui()
