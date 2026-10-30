"""
Synthesizes the full 9-scene narration for Flagship Episode 0
('The Universe Inside Out — A Visual Guide for Everyone')
in the creator's cloned voice on RTX 5080 (F5-TTS + Faster-Whisper word alignment).
Zero equations, zero intimidating jargon, natural 'Lambda see-dee-em' phonetic smoothing.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import List

import numpy as np
import soundfile as sf
import torch
from f5_tts.api import F5TTS
from faster_whisper import WhisperModel

EP0_DIR = Path(__file__).resolve().parent
AUDIO_DIR = EP0_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUB12_MANIFEST = Path(r"c:\Projects\Discovery\voice_studio\prompts_sub12s\sub12_manifest.json")

SCENES = [
    {
        "id": "scene01",
        "chapter": "PART 1",
        "title": "The Midnight Illusion & Today's '95% Invisible' Map",
        "subtitle_tag": "HOW OUR MODEL COMPARES TO TEXTBOOK LAMBDA-CDM",
        "cinema_clip": "scene01_midnight_cosmos.mp4",
        "beats": [
            (
                "take_01_warm_story",
                "Step outside on a clear midnight, look up at the stars, and notice the picture your brain automatically paints. Space feels like a vast, pitch-black, empty theater, atoms feel like tiny solid marbles, and time feels like an invisible river carrying us from yesterday into tomorrow.",
            ),
            (
                "take_04_cosmic_wonder",
                "For decades, astronomers have used a master textbook recipe for that universe called the Lambda see-dee-em model. Despite the technical name, the story behind it is remarkably simple.",
            ),
            (
                "take_03_tablecloth_analogy",
                "When telescopes measured spiral galaxies, their outer stars were whipping around way too fast, fast enough that they should have flung themselves off into deep space. And on the grandest scales, the expansion of the universe was speeding up instead of slowing down.",
            ),
            (
                "take_04_cosmic_wonder",
                "So to keep standard gravity working inside empty space, science added two giant, unseen ingredients: Cold Dark Matter, an invisible scaffolding outweighing normal stars five to one to glue galaxies together, and Lambda, or Dark Energy, an unexplained outward push filling empty space.",
            ),
            (
                "take_02_curious_question",
                "Put together, today's textbook model says ninety-five percent of reality is completely invisible, even though we have never caught a single dark-matter particle in a lab. What if nothing is missing at all, because space isn't empty, time isn't flowing, and we've been holding the cosmic map upside down?",
            ),
        ],
    },
    {
        "id": "scene02",
        "chapter": "PART 2",
        "title": "Erasing Empty Space: One Continuous Woven Fabric",
        "subtitle_tag": "CORE PICTURE: ZERO EMPTY SPACE • ONE FABRIC",
        "cinema_clip": "scene02_woven_fabric.mp4",
        "beats": [
            (
                "take_01_warm_story",
                "To see what our model is actually claiming, start by erasing empty space from your mind completely. Instead, picture the entire universe, every galaxy, every room, and every moment of history, as one tightly stretched fabric woven out of pure threads of connection.",
            ),
            (
                "take_03_tablecloth_analogy",
                "Nothing floats inside space. A beam of starlight is simply a shimmer running along those threads, like a pluck traveling down a taut guitar string. And the atoms in your hands aren't foreign pebbles dropped onto the sheet; they are tiny, twisted knots woven out of the threads themselves.",
            ),
            (
                "take_05_clear_precision",
                "That single shift in perspective is why the quantum world of the very small and the gravitational world of giant galaxies finally stop fighting each other. They aren't two separate rulebooks anymore; they are simply tiny ripples and wide stretches of the exact same cloth.",
            ),
        ],
    },
    {
        "id": "scene03",
        "chapter": "PART 3",
        "title": "Upside-Down Time (View 1): The Vinyl Record & Your Brain",
        "subtitle_tag": "TIME VISUAL #1 OF 3 • THE RECORD GROOVE & MEMORY NEEDLE",
        "cinema_clip": "scene03_vinyl_needle.mp4",
        "beats": [
            (
                "take_02_curious_question",
                "Now let's take our time with the hardest idea to wrap a human mind around: time itself. Every instinct in our body insists that the past has vanished, the future doesn't exist yet, and the present moment is a spotlight moving forward.",
            ),
            (
                "take_01_warm_story",
                "Here is the first of three ways to picture what is really going on. Imagine a finished vinyl record sitting quietly on a wooden table. The opening guitar chord, the middle chorus, and the final fade-out already exist all at once, carved side by side in the plastic. Nothing on the record is moving. Your awareness is the needle.",
            ),
            (
                "take_05_clear_precision",
                "Why does that needle feel like it glides in only one direction? Because living brains evolved on Earth to survive by burning energy and storing memories, and nature only lets a physical memory lock in where things get slightly messier, like a drop of ink spreading into water. Because you remember the neater side of the groove, riding along that slope feels from the inside like time is flowing.",
            ),
        ],
    },
    {
        "id": "scene04",
        "chapter": "PART 4",
        "title": "Upside-Down Time (View 2): Flipping the Cosmic Hourglass",
        "subtitle_tag": "TIME VISUAL #2 OF 3 • RANDOM OUTER RIM TO SMOOTH BIG BANG DRAIN",
        "cinema_clip": "scene04_flipping_hourglass.mp4",
        "beats": [
            (
                "take_02_curious_question",
                "Here is the second visual, and the boldest twist in the entire model. Standard physics assumes the universe began at the Big Bang in an unimaginably neat, tidy state, and has been falling apart into chaos ever since. That creates a famous mystery: what lined up the early universe so impossibly neatly at the start?",
            ),
            (
                "take_04_cosmic_wonder",
                "Now grab that cosmic hourglass and flip it upside down. What if the wide, messy, chaotic state we call the distant future is actually the raw, untuned outer edge of reality, pure random static that needed zero special setup at all?",
            ),
            (
                "take_03_tablecloth_analogy",
                "And what we call the Big Bang isn't an explosion out of nothing, but a smooth central pinhole drain in the middle of the fabric, pulling the cosmic sheet taut, flat, and orderly as it narrows.",
            ),
            (
                "take_05_clear_precision",
                "Even better, right at that narrow waist where disorder drops to zero, the neck rounds off smoothly like a soap film so the fabric never tears, while a natural subatomic twist acts like a coin sorter, funneling ordinary matter into our wing of the hourglass and all the missing antimatter into a mirror wing on the other side.",
            ),
        ],
    },
    {
        "id": "scene05",
        "chapter": "PART 5",
        "title": "Upside-Down Time (View 3): Two Brass Rings & Two Narrow Slits",
        "subtitle_tag": "TIME VISUAL #3 OF 3 • WHY IT ISN'T JUST A REWOUND MOVIE",
        "cinema_clip": "scene05_soap_film_slits.mp4",
        "beats": [
            (
                "take_02_curious_question",
                "At this point, any sharp listener should ask a fair question: wait a second, isn't flipping time upside down just pressing rewind on a movie and calling it a new theory?",
            ),
            (
                "take_03_tablecloth_analogy",
                "Here is the third visual that shows why this is real physics, not a word game. Playing a regular movie backward changes nothing physical. Instead, picture dipping two brass rings into soapy water, one giant outer ring and one tiny inner ring, and stretching a real soap film between them.",
            ),
            (
                "take_04_cosmic_wonder",
                "Because that film is physically held at both ends at once, wide floppy waves that are bigger than the tiny inner ring simply cannot fit on the sheet. And sure enough, when space telescopes map the oldest light across the heavens, those widest sky ripples are mysteriously quiet.",
            ),
            (
                "take_05_clear_precision",
                "That exact same two-ended grip also demystifies physics' spookiest experiment: the double slit. Like a guitar string tied down at both the launcher and the back wall at once, a single wave hums through both narrow slits simultaneously to paint striped patterns, until a warm detector touches one slit and pins the cloth right there, with zero mind-reading required.",
            ),
        ],
    },
    {
        "id": "scene06",
        "chapter": "PART 6",
        "title": "Dragging the Tablecloth (View 1): Gravity Without Bullets",
        "subtitle_tag": "TABLECLOTH VISUAL #1 OF 3 • PULLING THE SILK WEAVE TAUT",
        "cinema_clip": "scene06_silk_tablecloth.mp4",
        "beats": [
            (
                "take_03_tablecloth_analogy",
                "Now let's zoom out to planets and galaxies, and look at three distinct ways to picture how dragging and stretching this cosmic tablecloth creates gravity. First, picture pulling a giant silk tablecloth drum-tight across a frame.",
            ),
            (
                "take_01_warm_story",
                "When you press a heavy golden sphere into the middle, it doesn't fire invisible gravity bullets across empty air to lasso passing marbles. Instead, it pins and pulls the threads tighter all around itself. Any smaller world rolling nearby naturally curves inward along those strained threads, and starlight follows the exact same curved weave.",
            ),
        ],
    },
    {
        "id": "scene07",
        "chapter": "PART 7",
        "title": "Dragging the Tablecloth (View 2): The Campfire vs. Galaxy Suburbs",
        "subtitle_tag": "TABLECLOTH VISUAL #2 OF 3 • WHY DARK MATTER IS FABRIC TENSION",
        "cinema_clip": "scene07_campfire_to_galaxy.mp4",
        "beats": [
            (
                "take_02_curious_question",
                "Second: if the entire cosmic tablecloth is pulled taut between the outer rim and the central drain, why don't we feel that cosmic tension tugging Earth off course right here in our own Solar System?",
            ),
            (
                "take_01_warm_story",
                "Picture standing two feet from a roaring campfire on a freezing winter night. Close to the flames, that blast of local warmth completely drowns out the chill of the distant night air. In the exact same way, Earth whips around the Sun fast enough to wrap our Solar System inside an intense local motion bubble, millions of times stronger than the gentle background pull of deep space.",
            ),
            (
                "take_04_cosmic_wonder",
                "But now drift tens of thousands of light-years outward into the quiet, slow-moving suburbs of a spiral galaxy, far beyond the central blaze. Out there, the campfire fades, and the background tension of the cosmic tablecloth takes over. Like a taut trampoline supporting marbles near its rim, the fabric itself holds outer stars in fast, flat orbits, explaining the exact galaxy speeds astronomers blamed on Dark Matter, while balanced deep-ocean pressure in the cloth leaves only the gentle rim stretch we call Dark Energy.",
            ),
        ],
    },
    {
        "id": "scene08",
        "chapter": "PART 8",
        "title": "Dragging the Tablecloth (View 3): Fast Ghost Crashes vs. Slow Bounces",
        "subtitle_tag": "TABLECLOTH VISUAL #3 OF 3 • SPRINGY PLEATS IN GALAXY COLLISIONS",
        "cinema_clip": "scene08_pleat_collision.mp4",
        "beats": [
            (
                "take_03_tablecloth_analogy",
                "Here is the third tablecloth visual, and astronomy's toughest crash test. When a young galaxy forms, it gathers and tucks excess fabric around itself like a crisp, springy pleat folded into a tablecloth.",
            ),
            (
                "take_04_cosmic_wonder",
                "When two giant galaxy clusters smash head-on at blistering cosmic speed, their sheer momentum overwhelms the springiness of those folds. While their hot gas clouds slam together and get stuck in the middle like a highway pileup, the two giant fabric pleats slice straight through each other like ghosts right alongside the stars, matching famous telescope maps without needing dark-matter dust.",
            ),
            (
                "take_05_clear_precision",
                "Yet if two tiny galaxies graze each other at a gentle, slow drift, those springy fabric pleats actually bounce off each other in the middle while their stars coast onward, naturally leaving behind puzzling real-world galaxies that have almost no dark-matter pull at all.",
            ),
        ],
    },
    {
        "id": "scene09",
        "chapter": "PART 9",
        "title": "Stepping Back: The Whole Tapestry & Our Six Science Chapters",
        "subtitle_tag": "NEXT IN THE SERIES • 6 STANDALONE HARD-SCIENCE CHAPTERS",
        "cinema_clip": "scene09_braids_to_cosmos.mp4",
        "beats": [
            (
                "take_01_warm_story",
                "Step back for one final moment and hold the whole picture in your mind at once. No empty black void. No ticking river of time. No ninety-five percent invisible cosmic filler.",
            ),
            (
                "take_04_cosmic_wonder",
                "Just one timeless, tightly stretched fabric, pulled smooth toward a central pinhole, read like grooves on a vinyl record by living minds, holding galaxies together with its own quiet tension, and braiding its threads into the very atoms that let us look up at the night sky and wonder.",
            ),
            (
                "take_05_clear_precision",
                "Of course, in science, a vivid picture is only the beginning; it has to survive brutal contact with real measurements. In our six standalone companion chapters, we will open the hood one mystery at a time, bringing out every satellite test, particle-collider clue, galaxy crash simulation, and upcoming Moon-orbit experiment that can prove this upside-down universe right, or sink it cold.",
            ),
        ],
    },
]


def clean_for_tts(s: str) -> str:
    s = s.replace("—", ", ").replace("–", ", ").replace("’", "'")
    s = re.sub(r"\s+", " ", s).strip()
    if s and s[-1] not in ".?!":
        s += "."
    return s


def resample_linear(arr: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return arr.astype(np.float32)
    n_out = int(round(len(arr) * float(sr_out) / float(sr_in)))
    return np.interp(
        np.linspace(0.0, 1.0, n_out, endpoint=False),
        np.linspace(0.0, 1.0, len(arr), endpoint=False),
        arr,
    ).astype(np.float32)


def polish_caption_words(words: List[dict]) -> List[dict]:
    """Merges phonetic 'see dee em' or '-CDM' cleanly into 'Lambda-CDM' for crisp on-screen subtitles."""
    cleaned: List[dict] = []
    i = 0
    while i < len(words):
        w = words[i]["text"]
        wl = w.lower().strip(".,?!")
        # Collapse 'Lambda' + 'see' + 'dee' + 'em' (or similar Whisper splits) into 'Lambda-CDM'
        if wl in ("lambda", "lamda") and i + 1 < len(words):
            nxt = " ".join(x["text"].lower().strip(".,?!-") for x in words[i + 1 : i + 4])
            if nxt.startswith("see dee em") or nxt.startswith("c d m") or nxt.startswith("cdm"):
                span = 4 if (nxt.startswith("see dee em") or nxt.startswith("c d m")) else 2
                end_idx = min(len(words) - 1, i + span - 1)
                cleaned.append({"text": "Lambda-CDM", "start": words[i]["start"], "end": words[end_idx]["end"]})
                i = end_idx + 1
                continue
        if w.startswith("-CDM"):
            if cleaned and cleaned[-1]["text"].lower().rstrip(",") == "lambda":
                cleaned[-1]["text"] = "Lambda-CDM"
                cleaned[-1]["end"] = words[i]["end"]
                i += 1
                continue
        cleaned.append(words[i])
        i += 1
    return cleaned


def main() -> None:
    t0 = time.perf_counter()
    print(f"Synthesizing Episode 0 Cloned Narration on {torch.cuda.get_device_name(0)}...")
    prompts = json.loads(SUB12_MANIFEST.read_text(encoding="utf-8"))
    f5 = F5TTS(model="F5TTS_v1_Base", device="cuda")
    whisper = WhisperModel("base.en", device="cuda", compute_type="float16")

    manifest_scenes = []
    total_sec = 0.0

    for sc in SCENES:
        sc_t0 = time.perf_counter()
        chunks = []
        sr_out = 24000
        for pid, beat_txt in sc["beats"]:
            ref = prompts[pid]
            wav, sr_out, _ = f5.infer(
                ref_file=ref["wav_path"],
                ref_text=ref["ref_text"],
                gen_text=clean_for_tts(beat_txt),
                nfe_step=32,
                cfg_strength=2.0,
                speed=0.95,
            )
            arr = np.asarray(wav, dtype=np.float32)
            pk = float(np.max(np.abs(arr))) if len(arr) else 0.0
            if pk > 0.02:
                arr = arr * (0.76 / pk)
            chunks.append(arr)
            chunks.append(np.zeros(int(0.46 * sr_out), dtype=np.float32))

        full_sc = np.concatenate(chunks)
        wav_path = AUDIO_DIR / f"{sc['id']}.wav"
        sf.write(str(wav_path), full_sc, sr_out, subtype="PCM_16")
        dur = len(full_sc) / float(sr_out)
        total_sec += dur + 1.2

        # Align exact word boundaries via Faster-Whisper on RTX 5080
        aud_16k = resample_linear(full_sc, sr_out, 16000)
        segs, _ = whisper.transcribe(aud_16k, word_timestamps=True)
        raw_words = [
            {"text": w.word.strip(), "start": round(float(w.start), 3), "end": round(float(w.end), 3)}
            for seg in segs
            for w in (seg.words or [])
            if w.word.strip()
        ]
        words = polish_caption_words(raw_words)

        print(
            f"  [OK] {sc['id']} ({sc['chapter']}): {dur:5.1f}s audio | {len(words):3d} words | cloned in {time.perf_counter()-sc_t0:.1f}s"
        )
        manifest_scenes.append(
            {
                "id": sc["id"],
                "chapter": sc["chapter"],
                "title": sc["title"],
                "subtitle_tag": sc["subtitle_tag"],
                "cinema_clip": sc["cinema_clip"],
                "wav_path": str(wav_path),
                "duration_sec": round(dur, 3),
                "words": words,
            }
        )

    out_manifest = {
        "narrator": "Creator Cloned Voice (RTX 5080 F5-TTS)",
        "estimated_runtime_min": round(total_sec / 60.0, 2),
        "scenes": manifest_scenes,
    }
    (AUDIO_DIR / "ep0_manifest.json").write_text(json.dumps(out_manifest, indent=2), encoding="utf-8")
    print(f"[COMPLETE] All 9 scenes cloned ({total_sec/60.0:.2f} min total) in {time.perf_counter()-t0:.1f}s!")


if __name__ == "__main__":
    main()
