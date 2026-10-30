"""
Generates all 33 chunks of Flagship Episode 0 using David's registered Google Replicated Voice
(`voice_rjo5kexogz91`) on `gemini-3.8-flash-tts`, matching David's updated Intro and his honest
open-question preface on memory & time in Part 3 (Chunk 14).
"""

from __future__ import annotations

import base64
import json
import os
import time
import winreg
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

import httpx

EP0_DIR = Path(__file__).resolve().parent
OUT_DIR = EP0_DIR / "google_voice_chunks"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
VOICES_URL = "https://generativelanguage.googleapis.com/v1beta/voices"
TIMEOUT = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=15.0)

# All 33 chunks matching David's real Episode 0 script (including his Intro & Part 3C uncertainty preface),
# with gentle phonetic spelling on 'Sim-Pie', 'Sigh-Pie', and 'Lambda C-D-M' so TTS says them naturally!
GOOGLE_TTS_CHUNKS: List[Tuple[str, str, str]] = [
    (
        "chunk_01_scene00_a",
        "warm, genuine, conversational creator welcoming viewers",
        "Hello everyone, my name is David, and in this series I'm going to introduce you to a new model of the universe that I've been working on. To check its viability, we've stress-tested this model across top computational physics tools. Some of these tools include Sim-Pie symbolic algebra, Sigh-Pie relativistic simulations, and real benchmark data from the James Webb Space Telescope, Planck cosmic sky maps, and a hundred and seventy-five galaxies.",
    ),
    (
        "chunk_02_scene00_b",
        "clear, relaxed, inviting documentary host",
        "In this first introduction video, I'll explain the core fundamentals of the model visually and in plain English, as clearly as I can. Then, in follow-up standalone videos, we'll tackle one major prediction at a time with the hard science behind it—plus links in the description to thorough technical papers covering every single calculation.",
    ),
    (
        "chunk_03_scene00_c",
        "sincere, humble, confident creator presenting a flagship film",
        "I'm someone who loves thinking outside the box, and I want to say right up front: I want this model scrutinized, challenged, and held up to a microscope. This is an evolving theory, and I'm excited to share it with all of you. Subscribe if you're new and want to follow where this goes. And now, I present to you: The Universe Inside Out — A Visual Guide to the Stretched Fabric and the Upside-Down Cosmic Hourglass.",
    ),
    (
        "chunk_04_scene01_a",
        "quiet, atmospheric cosmic storyteller painting a midnight scene",
        "Step outside on a clear midnight, look up at the stars, and notice the picture your brain automatically paints. Space feels like a vast, pitch-black, empty theater. Atoms feel like tiny, solid marbles. And time feels like an invisible river carrying us from yesterday into tomorrow.",
    ),
    (
        "chunk_05_scene01_b",
        "clear, engaging science communicator",
        "For decades, astronomers have used a master textbook recipe for that universe called the Lambda C-D-M model. Despite the technical name, the story behind it is remarkably simple.",
    ),
    (
        "chunk_06_scene01_c",
        "curious, building intrigue naturally",
        "When telescopes measured spiral galaxies, their outer stars were whipping around way too fast—fast enough that they should have flung themselves off into deep space. And on the grandest scales, the expansion of the universe was speeding up instead of slowing down.",
    ),
    (
        "chunk_07_scene01_d",
        "clear, measured explanation",
        "So, to keep standard gravity working inside empty space, science added two giant, unseen ingredients: Cold Dark Matter, an invisible scaffolding outweighing normal stars five to one to glue the galaxies together, and Lambda, or Dark Energy, an unexplained outward push filling empty space.",
    ),
    (
        "chunk_08_scene01_e",
        "thoughtful wonder, letting the closing question land cleanly",
        "Put together, today's textbook model says ninety-five percent of reality is completely invisible—even though we have never caught a single dark-matter particle in a lab. What if nothing is missing at all—because space isn't empty, time isn't flowing, and we've been holding the cosmic map upside down?",
    ),
    (
        "chunk_09_scene02_a",
        "unhurried, vivid visual storyteller",
        "To see what our model is actually claiming, start by erasing empty space from your mind completely. Instead, picture the entire universe—every galaxy, every room, and every moment of history—as one tightly stretched fabric woven out of pure threads of connection.",
    ),
    (
        "chunk_10_scene02_b",
        "tactile, grounded, clear",
        "Nothing floats inside space. A beam of starlight is simply a shimmer running along those threads, like a pluck traveling down a taut guitar string. And the atoms in your hands aren't foreign pebbles dropped onto the sheet—they are tiny, twisted knots woven out of the threads themselves.",
    ),
    (
        "chunk_11_scene02_c",
        "warm, insightful realization",
        "That single shift in perspective is why the quantum world of the very small and the gravitational world of giant galaxies finally stop fighting each other. They aren't two separate rulebooks anymore—they are simply tiny ripples and wide stretches of the exact same cloth.",
    ),
    (
        "chunk_12_scene03_a",
        "thoughtful, empathetic documentary narrator",
        "Now, let's take our time with the hardest idea to wrap a human mind around: time itself. Every instinct in our body insists that the past has vanished, the future doesn't exist yet, and the present moment is a spotlight moving forward.",
    ),
    (
        "chunk_13_scene03_b",
        "calm, vivid tabletop analogy",
        "Here is the first of three ways to picture what is really going on. Imagine a finished vinyl record sitting quietly on a wooden table. The opening chord, the middle chorus, and the final fade-out already exist all at once, carved side by side in the plastic. Nothing on the record is moving. Your awareness is the needle.",
    ),
    (
        "chunk_14_scene03_c",
        "candid, honest, thoughtful scientist sharing an open question",
        "Why does that needle feel like it glides in only one direction? That's something still up for grabs, and something we are looking more deeply at. But possibly it could be because living brains evolved on Earth to survive by burning energy and storing memories—and nature only lets a physical memory lock in where things get slightly messier, like a drop of ink spreading into water. Because you remember the neater side of the groove, riding along that slope feels from the inside like time is flowing.",
    ),
    (
        "chunk_15_scene04_a",
        "engaged, curious science storyteller",
        "Here is the second visual, and the boldest twist in the entire model. Standard physics assumes the universe began at the Big Bang in an unimaginably neat, tidy state, and has been falling apart into chaos ever since. That creates a famous mystery: what lined up the early universe so impossibly neatly at the start?",
    ),
    (
        "chunk_16_scene04_b",
        "vivid, energizing mental flip",
        "Now grab that cosmic hourglass and flip it upside down. What if the wide, messy, chaotic state we call the distant future is actually the raw, untuned outer edge of reality—pure random static that needed zero special setup at all?",
    ),
    (
        "chunk_17_scene04_c",
        "calm, smooth, clear",
        "And what we call the Big Bang isn't an explosion out of nothing, but a smooth central pinhole drain in the middle of the fabric—pulling the cosmic sheet taut, flat, and orderly as it narrows.",
    ),
    (
        "chunk_18_scene04_d",
        "fascinated, clear visual explanation",
        "Even better, right at that narrow waist where disorder drops to zero, the neck rounds off smoothly like a soap film so the fabric never tears—while a natural subatomic twist acts like a coin sorter, funneling ordinary matter into our wing of the hourglass and all the missing antimatter into a mirror wing on the other side.",
    ),
    (
        "chunk_19_scene05_a",
        "conversational, voicing a sharp listener's question",
        "At this point, any sharp listener should ask a fair question: wait a second—isn't flipping time upside down just pressing rewind on a movie and calling it a new theory?",
    ),
    (
        "chunk_20_scene05_b",
        "grounded, clear tabletop physics teacher",
        "Here is the third visual that shows why this is real physics, not a word game. Playing a regular movie backward changes nothing physical. Instead, picture dipping two brass rings into soapy water—one giant outer ring and one tiny inner ring—and stretching a real soap film between them.",
    ),
    (
        "chunk_21_scene05_c",
        "smooth, building to an observational payoff",
        "Because that film is physically held at both ends all at the same time, wide floppy waves that are bigger than the tiny inner ring simply cannot fit on the sheet. And sure enough, when space telescopes map the oldest light across the heavens, those widest sky ripples are mysteriously quiet.",
    ),
    (
        "chunk_22_scene05_d",
        "crisp, demystifying, satisfying",
        "That exact same two-ended grip also demystifies physics' spookiest experiment: the double slit. Like a guitar string tied down at both the launcher and the back wall at once, a single wave hums through both narrow slits simultaneously to paint striped patterns—until a warm detector touches one slit and pins the cloth right there, with zero mind-reading required.",
    ),
    (
        "chunk_23_scene06_a",
        "fresh chapter energy, inviting",
        "Now let's zoom out to planets and galaxies, and look at three distinct ways to picture how dragging and stretching this cosmic tablecloth creates gravity. First, picture pulling a giant silk tablecloth drum-tight across a frame.",
    ),
    (
        "chunk_24_scene06_b",
        "vivid, physical, unhurried",
        "When you press a heavy golden sphere into the middle, it doesn't fire invisible gravity bullets across empty air to lasso passing marbles. Instead, it pins and pulls the threads tighter all around itself. Any smaller world rolling nearby naturally curves inward along those strained threads—and starlight follows the exact same curved weave.",
    ),
    (
        "chunk_25_scene07_a",
        "curious, conversational question",
        "Second, if the entire cosmic tablecloth is pulled taut between the outer rim and the central drain, why don't we feel that cosmic tension tugging Earth off course right here in our own solar system?",
    ),
    (
        "chunk_26_scene07_b",
        "warm, relatable campfire story",
        "Picture standing two feet from a roaring campfire on a freezing winter night. Close to the flames, that blast of local warmth completely drowns out the chill of the distant night air. In the exact same way, Earth whips around the Sun fast enough to wrap our solar system inside an intense local motion bubble—millions of times stronger than the gentle background pull of deep space.",
    ),
    (
        "chunk_27_scene07_c",
        "expansive, majestic cosmic sweep",
        "But now drift tens of thousands of light-years outward into the quiet, slow-moving suburbs of a spiral galaxy, far beyond the central blaze. Out there, the campfire fades and the background tension of the cosmic tablecloth takes over. Like a taut trampoline supporting marbles near its rim, the fabric itself holds outer stars in a fast, flat orbit—explaining the exact galaxy speeds astronomers blamed on dark matter, while balanced deep-ocean pressure in the cloth leaves only the gentle rim stretch that we call dark energy.",
    ),
    (
        "chunk_28_scene08_a",
        "clear, setting up a dramatic cosmic test",
        "Here is the third tablecloth visual, and astronomy's toughest crash test. When a young galaxy forms, it gathers and tucks excess fabric around itself like a crisp, springy pleat folded into a tablecloth.",
    ),
    (
        "chunk_29_scene08_b",
        "dynamic, vivid cosmic collision",
        "When two giant galaxy clusters smash head-on at blistering cosmic speed, their sheer momentum overwhelms the springiness of the folds. While their hot gas clouds slam together and get stuck in the middle like a highway pile-up, the two giant fabric pleats slice straight through each other like ghosts right along with the stars—matching famous telescope maps without needing dark-matter dust.",
    ),
    (
        "chunk_30_scene08_c",
        "gentle contrast, intrigued",
        "Yet if two smaller galaxies graze each other at a gentle, slow drift, those springy fabric pleats actually bounce off each other in the middle while their stars coast onward—naturally leaving behind puzzling real-world galaxies that have almost no dark-matter pull at all.",
    ),
    (
        "chunk_31_scene09_a",
        "calm, reflective, expansive",
        "Step back for one final moment and hold the whole picture in your mind at once. No empty black void. No ticking river of time. No ninety-five percent invisible cosmic filler.",
    ),
    (
        "chunk_32_scene09_b",
        "poetic, warm, awe-inspired",
        "Just one timeless, tightly stretched fabric—pulled smooth toward a central pinhole, read like grooves on a vinyl record by living minds, holding galaxies together with its own quiet tension, and braiding its threads into the very atoms that let us look up at the night sky in wonder.",
    ),
    (
        "chunk_33_scene09_c",
        "confident, grounded scientific invite to the series",
        "Of course, in science, a vivid picture is only the beginning—it has to survive brutal contact with real measurements. In our six standalone companion chapters, we will open the hood one mystery at a time, bringing out every satellite test, particle collider clue, galaxy crash simulation, and upcoming Moon-orbit experiment that can prove this upside-down universe right, or sink it cold.",
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
    raise RuntimeError("David Documentary Narrator voice ID not found on Gemini 3.8 Flash TTS")


def synth_one(idx: int, total: int, cid: str, style: str, text: str, voice_id: str, api_key: str) -> str:
    out_p = OUT_DIR / f"{cid}.wav"
    if out_p.exists() and out_p.stat().st_size > 15_000:
        return f"[{idx:02d}/{total} SKIP] {cid}"

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
                    wait_s = 36.0 if r.status_code == 429 else 5.0 * attempt
                    time.sleep(wait_s)
                    continue
                b64 = extract_audio_b64(r.json())
                if not b64:
                    raise RuntimeError("Missing audio data")
                raw = base64.b64decode(b64)
                out_p.write_bytes(raw)
                msg = f"[{idx:02d}/{total} SAVED] {cid}.wav ({len(raw)/1024:.0f} KB)"
                print(msg, flush=True)
                # Respect Tier-1 10 RPM limit (>= 6.3s per request start-to-start)
                elapsed = time.time() - t_req
                if elapsed < 6.4:
                    time.sleep(6.4 - elapsed)
                return msg
        except Exception as exc:
            print(f"[{idx:02d}/{total}] Error (attempt {attempt}): {exc}", flush=True)
            time.sleep(6.0 * attempt)
    raise RuntimeError(f"Failed to synthesize {cid}")


def main() -> None:
    t0 = time.time()
    api_key = get_api_key()
    assert api_key, "GEMINI_API_KEY missing"
    voice_id = resolve_david_voice_id(api_key)
    print(f"Using David's Replicated Google Voice ID: {voice_id}", flush=True)

    tot = len(GOOGLE_TTS_CHUNKS)
    for i, (cid, st, tx) in enumerate(GOOGLE_TTS_CHUNKS):
        synth_one(i + 1, tot, cid, st, tx, voice_id, api_key)

    print(f"\n[ALL 33 GOOGLE REPLICATED VOICE CHUNKS READY in {time.time() - t0:.1f}s!]", flush=True)


if __name__ == "__main__":
    main()
