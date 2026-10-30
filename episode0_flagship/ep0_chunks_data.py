"""
Single source of truth for all 31 bite-sized recording chunks of Flagship Episode 0:
  'The Universe Inside Out: A Visual Guide to the Stretched Fabric & Upside-Down Cosmic Hourglass'

Includes David's personal 3-chunk Creator Intro (scene00) followed by Parts 1–9 (scene01..scene09)
broken into comfortable ~15-25 second chunks so every take is easy to read in one relaxed breath.
"""

from __future__ import annotations

from typing import List, TypedDict


class ChunkSpec(TypedDict):
    num: int
    chunk_id: str
    scene_id: str
    chapter: str
    scene_title: str
    subtitle_tag: str
    cinema_clip: str
    label: str
    coaching: str
    text: str


SCENE_METADATA = {
    "scene00": {
        "chapter": "WELCOME",
        "title": "David's Introduction: An Open Human + AI Thought Experiment",
        "subtitle_tag": "MADE WITH GEMINI ARGON IN ANTIGRAVITY • STOLER.SYSTEMS",
        "cinema_clip": "scene01_midnight_cosmos.mp4",
    },
    "scene01": {
        "chapter": "PART 1",
        "title": "The Midnight Illusion & Today's '95% Invisible' Map",
        "subtitle_tag": "HOW OUR MODEL COMPARES TO TEXTBOOK LAMBDA-CDM",
        "cinema_clip": "scene01_midnight_cosmos.mp4",
    },
    "scene02": {
        "chapter": "PART 2",
        "title": "Erasing Empty Space: One Continuous Woven Fabric",
        "subtitle_tag": "CORE PICTURE: ZERO EMPTY SPACE • ONE FABRIC",
        "cinema_clip": "scene02_woven_fabric.mp4",
    },
    "scene03": {
        "chapter": "PART 3",
        "title": "Upside-Down Time (View 1): The Vinyl Record & Your Brain",
        "subtitle_tag": "TIME VISUAL #1 OF 3 • THE RECORD GROOVE & MEMORY NEEDLE",
        "cinema_clip": "scene03_vinyl_needle.mp4",
    },
    "scene04": {
        "chapter": "PART 4",
        "title": "Upside-Down Time (View 2): Flipping the Cosmic Hourglass",
        "subtitle_tag": "TIME VISUAL #2 OF 3 • RANDOM OUTER RIM TO SMOOTH BIG BANG DRAIN",
        "cinema_clip": "scene04_flipping_hourglass.mp4",
    },
    "scene05": {
        "chapter": "PART 5",
        "title": "Upside-Down Time (View 3): Two Brass Rings & Two Narrow Slits",
        "subtitle_tag": "TIME VISUAL #3 OF 3 • WHY IT ISN'T JUST A REWOUND MOVIE",
        "cinema_clip": "scene05_soap_film_slits.mp4",
    },
    "scene06": {
        "chapter": "PART 6",
        "title": "Dragging the Tablecloth (View 1): Gravity Without Bullets",
        "subtitle_tag": "TABLECLOTH VISUAL #1 OF 3 • PULLING THE SILK WEAVE TAUT",
        "cinema_clip": "scene06_silk_tablecloth.mp4",
    },
    "scene07": {
        "chapter": "PART 7",
        "title": "Dragging the Tablecloth (View 2): The Campfire vs. Galaxy Suburbs",
        "subtitle_tag": "TABLECLOTH VISUAL #2 OF 3 • COULD TENSION MIMIC DARK MATTER?",
        "cinema_clip": "scene07_campfire_to_galaxy.mp4",
    },
    "scene08": {
        "chapter": "PART 8",
        "title": "Dragging the Tablecloth (View 3): Fast Ghost Crashes vs. Slow Bounces",
        "subtitle_tag": "TABLECLOTH VISUAL #3 OF 3 • SPRINGY PLEATS IN GALAXY COLLISIONS",
        "cinema_clip": "scene08_pleat_collision.mp4",
    },
    "scene09": {
        "chapter": "PART 9",
        "title": "Stepping Back: The Whole Tapestry & Our Six Science Chapters",
        "subtitle_tag": "NEXT IN THE SERIES • 6 STANDALONE HARD-SCIENCE CHAPTERS",
        "cinema_clip": "scene09_braids_to_cosmos.mp4",
    },
}


_RAW_CHUNKS = [
    # --- SCENE 00: DAVID'S PERSONAL INTRO (3 Chunks) ---
    (
        "scene00",
        "Intro A — Welcome & Physics Tools Used",
        "Warm, genuine, conversational — just you introducing your project to curious viewers. ('SymPy' = 'Sim-Pie', 'SciPy' = 'Sigh-Pie').",
        "Hello everyone, my name is David, and in this series I'm going to introduce you to a new model of the universe that I've been working on. To check its viability, we've stress-tested this model across top computational physics tools—including SymPy symbolic algebra, SciPy relativistic simulations, and real benchmark data from the James Webb Space Telescope, Planck cosmic sky maps, and a hundred and seventy-five galaxies.",
    ),
    (
        "scene00",
        "Intro B — How This Series Is Organized",
        "Relaxed, clear roadmap of Episode 0 vs. the deeper standalone science chapters.",
        "In this first introduction video, I'll explain the core fundamentals of the model visually and in plain English, as clearly as I can. Then, in follow-up standalone videos, we'll tackle one major prediction at a time with the hard science behind it—plus links in the description to thorough technical papers covering every single calculation.",
    ),
    (
        "scene00",
        "Intro C — Open Scrutiny & Title Drop",
        "Sincere, humble, confident; pause half a beat before presenting the title at the end.",
        "I'm someone who loves thinking outside the box, and I want to say right up front: I want this model scrutinized, challenged, and held up to a microscope. This is an evolving theory, and I'm excited to share it with all of you. Subscribe if you're new and want to follow where this goes—and now, I present to you: The Universe Inside Out, A Visual Guide to the Stretched Fabric and the Upside-Down Cosmic Hourglass.",
    ),

    # --- SCENE 01: COLD OPEN & LAMBDA-CDM (5 Chunks) ---
    (
        "scene01",
        "Part 1A — Looking Up at Midnight",
        "Quiet, atmospheric storytelling — paint the midnight sky in the listener's head.",
        "Step outside on a clear midnight, look up at the stars, and notice the picture your brain automatically paints. Space feels like a vast, pitch-black, empty theater, atoms feel like tiny solid marbles, and time feels like an invisible river carrying us from yesterday into tomorrow.",
    ),
    (
        "scene01",
        "Part 1B — What 'Lambda-CDM' Means",
        "Say 'Lambda-C-D-M' smoothly like three crisp letters.",
        "For decades, astronomers have used a master textbook recipe for that universe called the Lambda-CDM model. Despite the technical name, the story behind it is remarkably simple.",
    ),
    (
        "scene01",
        "Part 1C — Fast Galaxies & Speeding Expansion",
        "Build gentle curiosity on 'way too fast' and 'speeding up'.",
        "When telescopes measured spiral galaxies, their outer stars were whipping around way too fast—fast enough that they should have flung themselves off into deep space. And on the grandest scales, the expansion of the universe was speeding up instead of slowing down.",
    ),
    (
        "scene01",
        "Part 1D — The Two Invisible Ingredients",
        "Clear contrast between Cold Dark Matter (glue) and Lambda Dark Energy (push).",
        "So to keep standard gravity working inside empty space, science added two giant, unseen ingredients: Cold Dark Matter, an invisible scaffolding outweighing normal stars five to one to glue galaxies together; and Lambda, or Dark Energy, an unexplained outward push filling empty space.",
    ),
    (
        "scene01",
        "Part 1E — The 95% Question",
        "Let the closing question land with real wonder.",
        "Put together, today's textbook model says ninety-five percent of reality is completely invisible—even though we have never caught a single dark-matter particle in a lab. What if nothing is missing at all—because space isn't empty, time isn't flowing, and we've been holding the cosmic map upside down?",
    ),

    # --- SCENE 02: ONE CONTINUOUS WOVEN FABRIC (3 Chunks) ---
    (
        "scene02",
        "Part 2A — Erasing Empty Space",
        "Unhurried, vivid mental reset.",
        "To see what our model is actually claiming, start by erasing empty space from your mind completely. Instead, picture the entire universe—every galaxy, every room, and every moment of history—as one tightly stretched fabric woven out of pure threads of connection.",
    ),
    (
        "scene02",
        "Part 2B — Light as a Pluck, Atoms as Knots",
        "Tactile and physical — plucking a guitar string, tying a knot in cloth.",
        "Nothing floats inside space. A beam of starlight is simply a shimmer running along those threads, like a pluck traveling down a taut guitar string. And the atoms in your hands aren't foreign pebbles dropped onto the sheet—they are tiny, twisted knots woven out of the threads themselves.",
    ),
    (
        "scene02",
        "Part 2C — Why Small & Giant Stop Fighting",
        "Warm 'aha!' payoff.",
        "That single shift in perspective is why the quantum world of the very small and the gravitational world of giant galaxies finally stop fighting each other. They aren't two separate rulebooks anymore—they are simply tiny ripples and wide stretches of the exact same cloth.",
    ),

    # --- SCENE 03: UPSIDE-DOWN TIME VIEW #1 — VINYL RECORD (3 Chunks) ---
    (
        "scene03",
        "Part 3A — The Illusion of the Moving Spotlight",
        "Empathetic — acknowledge how weird timelessness feels at first.",
        "Now let's take our time with the hardest idea to wrap a human mind around: time itself. Every instinct in our body insists that the past has vanished, the future doesn't exist yet, and the present moment is a spotlight moving forward.",
    ),
    (
        "scene03",
        "Part 3B — Time View #1: The Vinyl Record",
        "Pause briefly before 'Nothing on the record is moving. Your awareness is the needle.'",
        "Here is the first of three ways to picture what is really going on. Imagine a finished vinyl record sitting quietly on a wooden table. The opening guitar chord, the middle chorus, and the final fade-out already exist all at once, carved side by side in the plastic. Nothing on the record is moving. Your awareness is the needle.",
    ),
    (
        "scene03",
        "Part 3C — Why Memories Point One Way",
        "Clear, grounded everyday analogy (ink spreading in water).",
        "Why does that needle feel like it glides in only one direction? Because living brains evolved on Earth to survive by burning energy and storing memories—and nature only lets a physical memory lock in where things get slightly messier, like a drop of ink spreading into water. Because you remember the neater side of the groove, riding along that slope feels from the inside like time is flowing.",
    ),

    # --- SCENE 04: UPSIDE-DOWN TIME VIEW #2 — FLIPPING THE HOURGLASS (4 Chunks) ---
    (
        "scene04",
        "Part 4A — The Tidy-Start Mystery",
        "Curious setup of standard cosmology's biggest puzzle.",
        "Here is the second visual—and the boldest twist in the entire model. Standard physics assumes the universe began at the Big Bang in an unimaginably neat, tidy state, and has been falling apart into chaos ever since. That creates a famous mystery: what lined up the early universe so impossibly neatly at the start?",
    ),
    (
        "scene04",
        "Part 4B — Time View #2: Flip the Hourglass",
        "Big visual moment — physically flipping the hourglass in your voice.",
        "Now grab that cosmic hourglass and flip it upside down. What if the wide, messy, chaotic state we call the distant future is actually the raw, untuned outer edge of reality—pure random static that needed zero special setup at all?",
    ),
    (
        "scene04",
        "Part 4C — The Smooth Big Bang Drain",
        "Smooth, calm delivery.",
        "And what we call the Big Bang isn't an explosion out of nothing, but a smooth central pinhole drain in the middle of the fabric, pulling the cosmic sheet taut, flat, and orderly as it narrows.",
    ),
    (
        "scene04",
        "Part 4D — Soap-Film Waist & Twin Antimatter Wing",
        "Picture a smooth curved soap film sorting coins left and right.",
        "Even better, right at that narrow waist where disorder drops to zero, the neck rounds off smoothly like a soap film so the fabric never tears—while a natural subatomic twist acts like a coin sorter, funneling ordinary matter into our wing of the hourglass and all the missing antimatter into a mirror wing on the other side.",
    ),

    # --- SCENE 05: UPSIDE-DOWN TIME VIEW #3 — TWO BRASS RINGS & SLITS (4 Chunks) ---
    (
        "scene05",
        "Part 5A — The Skeptic's Rewind Question",
        "Voice the skeptic's question naturally and playfully.",
        "At this point, any sharp listener should ask a fair question: wait a second—isn't flipping time upside down just pressing rewind on a movie and calling it a new theory?",
    ),
    (
        "scene05",
        "Part 5B — Time View #3: Two Brass Rings & Soap Film",
        "Clear tabletop visual — one giant ring, one tiny ring.",
        "Here is the third visual that shows why this is real physics, not a word game. Playing a regular movie backward changes nothing physical. Instead, picture dipping two brass rings into soapy water—one giant outer ring and one tiny inner ring—and stretching a real soap film between them.",
    ),
    (
        "scene05",
        "Part 5C — Filtering Out Giant Sky Waves",
        "Connect the tabletop soap film directly to real telescope maps.",
        "Because that film is physically held at both ends at once, wide floppy waves that are bigger than the tiny inner ring simply cannot fit on the sheet. And sure enough, when space telescopes map the oldest light across the heavens, those widest sky ripples are mysteriously quiet.",
    ),
    (
        "scene05",
        "Part 5D — The Double Slit Without Spooky Mind-Reading",
        "Crisp payoff — guitar string tied at both ends.",
        "That exact same two-ended grip also demystifies physics' spookiest experiment: the double slit. Like a guitar string tied down at both the launcher and the back wall at once, a single wave hums through both narrow slits simultaneously to paint striped patterns—until a warm detector touches one slit and pins the cloth right there, with zero mind-reading required.",
    ),

    # --- SCENE 06: TABLECLOTH VIEW #1 — SILK GRAVITY (2 Chunks) ---
    (
        "scene06",
        "Part 6A — Tablecloth View #1: Pulling Silk Drum-Tight",
        "Fresh chapter energy — zooming out to planets and stars.",
        "Now let's zoom out to planets and galaxies, and look at three distinct ways to picture how dragging and stretching this cosmic tablecloth creates gravity. First, picture pulling a giant silk tablecloth drum-tight across a frame.",
    ),
    (
        "scene06",
        "Part 6B — Curving Along Strained Threads",
        "Tactile, grounded explanation of orbits and starlight.",
        "When you press a heavy golden sphere into the middle, it doesn't fire invisible gravity bullets across empty air to lasso passing marbles. Instead, it pins and pulls the threads tighter all around itself. Any smaller world rolling nearby naturally curves inward along those strained threads—and starlight follows the exact same curved weave.",
    ),

    # --- SCENE 07: TABLECLOTH VIEW #2 — CAMPFIRE VS. GALAXY SUBURBS (3 Chunks) ---
    (
        "scene07",
        "Part 7A — Why Earth Doesn't Feel the Cosmic Tug",
        "Curious everyday question.",
        "Second: if the entire cosmic tablecloth is pulled taut between the outer rim and the central drain, why don't we feel that cosmic tension tugging Earth off course right here in our own Solar System?",
    ),
    (
        "scene07",
        "Part 7B — Tablecloth View #2: The Roaring Campfire",
        "Warm, vivid winter campfire analogy.",
        "Picture standing two feet from a roaring campfire on a freezing winter night. Close to the flames, that blast of local warmth completely drowns out the chill of the distant night air. In the exact same way, Earth whips around the Sun fast enough to wrap our Solar System inside an intense local motion bubble, millions of times stronger than the gentle background pull of deep space.",
    ),
    (
        "scene07",
        "Part 7C — Quiet Galaxy Suburbs & Trampoline Tension",
        "Unhurried Brian Cox sense of scale out in the galaxy outskirts.",
        "But now drift tens of thousands of light-years outward into the quiet, slow-moving suburbs of a spiral galaxy, far beyond the central blaze. Out there, the campfire fades, and the background tension of the cosmic tablecloth takes over. Like a taut trampoline supporting marbles near its rim, the fabric itself holds outer stars in fast, flat orbits—explaining the exact galaxy speeds astronomers blamed on Dark Matter, while balanced deep-ocean pressure in the cloth leaves only the gentle rim stretch we call Dark Energy.",
    ),

    # --- SCENE 08: TABLECLOTH VIEW #3 — SPRINGY PLEATS IN CRASHES (3 Chunks) ---
    (
        "scene08",
        "Part 8A — Tablecloth View #3: Folding a Springy Pleat",
        "Tactile — folding excess tablecloth into a crisp, springy pleat.",
        "Here is the third tablecloth visual—and astronomy's toughest crash test. When a young galaxy forms, it gathers and tucks excess fabric around itself like a crisp, springy pleat folded into a tablecloth.",
    ),
    (
        "scene08",
        "Part 8B — Blistering High-Speed Cluster Crashes",
        "Energetic momentum on the fast crash vs. gas pileup.",
        "When two giant galaxy clusters smash head-on at blistering cosmic speed, their sheer momentum overwhelms the springiness of those folds. While their hot gas clouds slam together and get stuck in the middle like a highway pileup, the two giant fabric pleats slice straight through each other like ghosts right alongside the stars—matching famous telescope maps without needing dark-matter dust.",
    ),
    (
        "scene08",
        "Part 8C — Gentle Slow Grazing Bounces",
        "Contrast with a gentle, slow bounce.",
        "Yet if two tiny galaxies graze each other at a gentle, slow drift, those springy fabric pleats actually bounce off each other in the middle while their stars coast onward—naturally leaving behind puzzling real-world galaxies that have almost no dark-matter pull at all.",
    ),

    # --- SCENE 09: CLOSING WONDER & ROADMAP TO CHAPTERS 1–6 (3 Chunks) ---
    (
        "scene09",
        "Part 9A — Holding the Whole Picture at Once",
        "Calm, spacious, reflective pause.",
        "Step back for one final moment and hold the whole picture in your mind at once. No empty black void. No ticking river of time. No ninety-five percent invisible cosmic filler.",
    ),
    (
        "scene09",
        "Part 9B — One Timeless Woven Tapestry",
        "Warm poetic cadence — let the wonder breathe.",
        "Just one timeless, tightly stretched fabric—pulled smooth toward a central pinhole, read like grooves on a vinyl record by living minds, holding galaxies together with its own quiet tension, and braiding its threads into the very atoms that let us look up at the night sky and wonder.",
    ),
    (
        "scene09",
        "Part 9C — Inviting the Hard-Science Chapters",
        "Strong, inviting documentary finale!",
        "Of course, in science, a vivid picture is only the beginning—it has to survive brutal contact with real measurements. In our six standalone companion chapters, we will open the hood one mystery at a time, bringing out every satellite test, particle-collider clue, galaxy crash simulation, and upcoming Moon-orbit experiment that can prove this upside-down universe right, or sink it cold.",
    ),
]


def get_all_chunks() -> List[ChunkSpec]:
    out: List[ChunkSpec] = []
    scene_counts: dict[str, int] = {}
    for idx, (sc_id, label, coaching, text) in enumerate(_RAW_CHUNKS, start=1):
        letter_i = scene_counts.get(sc_id, 0)
        scene_counts[sc_id] = letter_i + 1
        letter = chr(ord("a") + letter_i)
        meta = SCENE_METADATA[sc_id]
        out.append(
            {
                "num": idx,
                "chunk_id": f"chunk_{idx:02d}_{sc_id}_{letter}",
                "scene_id": sc_id,
                "chapter": meta["chapter"],
                "scene_title": meta["title"],
                "subtitle_tag": meta["subtitle_tag"],
                "cinema_clip": meta["cinema_clip"],
                "label": label,
                "coaching": coaching,
                "text": text,
            }
        )
    return out


CHUNKS: List[ChunkSpec] = get_all_chunks()
