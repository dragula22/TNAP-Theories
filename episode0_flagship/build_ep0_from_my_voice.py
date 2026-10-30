"""
Updates `_verbatim_whisper_medium_audit.json` for any newly re-recorded chunks in `my_narration/`
using Faster-Whisper `medium.en` on RTX 5080, then runs `master_v2_audio_and_subtitles.py` so
captions and broadcast vocal mastering stay 100% synced whenever David re-records a take!
"""

from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

EP0_DIR = Path(__file__).resolve().parent
RAW_DIR = EP0_DIR / "my_narration"
AUDIT_JSON = RAW_DIR / "_verbatim_whisper_medium_audit.json"


def main() -> None:
    wavs = sorted(p for p in RAW_DIR.glob("chunk_*.wav"))
    if not wavs:
        print(f"No chunk_*.wav files found in {RAW_DIR}")
        sys.exit(1)

    existing = {}
    if AUDIT_JSON.exists():
        data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
        for ch in data.get("chunks", []):
            existing[ch["file"]] = ch

    model = None
    updated_chunks = []
    total_dur = 0.0

    for wp in wavs:
        with wave.open(str(wp), "rb") as wf:
            n_frames = wf.getnframes()
            sr = wf.getframerate()
            pcm = np.frombuffer(wf.readframes(n_frames), dtype=np.int16).astype(np.float32) / 32768.0
        dur = round(n_frames / float(sr), 3)
        total_dur += dur
        pk_db = round(20.0 * float(np.log10(max(1e-6, float(np.max(np.abs(pcm)))))), 1)

        prev = existing.get(wp.name)
        if prev and abs(prev.get("duration", 0.0) - dur) < 0.01 and abs(prev.get("peak_db", 0.0) - pk_db) < 0.15:
            updated_chunks.append(prev)
            continue

        if model is None:
            print("Loading Faster-Whisper medium.en on CUDA for updated take(s)...")
            model = WhisperModel("medium.en", device="cuda", compute_type="float16")

        print(f"Transcribing updated take: {wp.name} ({dur}s)...")
        segs, _ = model.transcribe(str(wp), word_timestamps=True)
        words = []
        full_txt = []
        for s in segs:
            full_txt.append(s.text.strip())
            for w in (s.words or []):
                if w.word.strip():
                    words.append({"text": w.word.strip(), "start": round(float(w.start), 2), "end": round(float(w.end), 2)})
        updated_chunks.append(
            {
                "file": wp.name,
                "duration": dur,
                "peak_db": pk_db,
                "text": " ".join(full_txt).strip(),
                "words": words,
            }
        )

    AUDIT_JSON.write_text(
        json.dumps({"total_duration_sec": round(total_dur, 2), "chunks": updated_chunks}, indent=2),
        encoding="utf-8",
    )
    print(f"Saved verbatim audit ({len(updated_chunks)} chunks) -> {AUDIT_JSON.name}")

    venv_py = Path(r"c:\Projects\Discovery\.venv\Scripts\python.exe")
    subprocess.run([str(venv_py), str(EP0_DIR / "master_v2_audio_and_subtitles.py")], check=True)


if __name__ == "__main__":
    main()
