"""
Single source of truth for all 28 bite-sized recording chunks of Episode 1:
  'Episode 1 — Is Time Even Real? Vinyl Records, Memory & Why GPS Satellites Run Fast'

Follows the exact human-first Teleprompter Studio architecture from Flagship Episode 0:
  • Comfortable ~18–26 second chunks so David can record every take in one relaxed, natural breath
  • Explicit pronunciation & pacing notes on every chunk
  • Zero burned-in subtitles on video frames (standalone .SRT exported directly from audio manifest)
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
        "title": "Welcome Back: Putting Pillar 1 & 2 Under the Microscope",
        "subtitle_tag": "EPISODE 1 • THEORETICALLY NOT A PHYSICIST • STOLER.SYSTEMS",
        "cinema_clip": "ep1_scene00_welcome_observatory.mp4",
    },
    "scene01": {
        "chapter": "CHAPTER 1",
        "title": "The Illusion of 'Now' & The Frozen 4D Tapestry",
        "subtitle_tag": "WHY NOTHING ON THE COSMIC MAP ACTUALLY MOVES",
        "cinema_clip": "ep1_scene01_frozen_tapestry.mp4",
    },
    "scene02": {
        "chapter": "CHAPTER 2",
        "title": "The Brain Needle & Landauer's Law of Memory",
        "subtitle_tag": "WHY MEMORY ONLY WORKS IN ONE DIRECTION • k_B T ln(2)",
        "cinema_clip": "ep1_scene02_landauer_memory_needle.mp4",
    },
    "scene03": {
        "chapter": "CHAPTER 3",
        "title": "The 20,000-Kilometer Test: Why GPS Satellites Run Fast",
        "subtitle_tag": "SPEED SLOWING (-7.2 µs) VS. FABRIC TENSION (+45.8 µs) = +38.6 µs/DAY",
        "cinema_clip": "ep1_scene03_gps_orbit_clocks.mp4",
    },
    "scene04": {
        "chapter": "CHAPTER 4",
        "title": "Mercury's Wobble, Saturn's Radio Delay & Neutron Star Crashes",
        "subtitle_tag": "CASSINI SHAPIRO DELAY (10^-5) & GW170817 LIGHT-SPEED GRAVITY WAVES",
        "cinema_clip": "ep1_scene04_cassini_and_gw170817.mp4",
    },
    "scene05": {
        "chapter": "CHAPTER 5",
        "title": "The Honest Scorecard: What Passes & Where Spinning Black Holes Push Back",
        "subtitle_tag": "LACUNA LITERATURE AUDIT & OPEN HURDLES (KERR FRAME-DRAGGING)",
        "cinema_clip": "ep1_scene05_kerr_vortex_scorecard.mp4",
    },
    "scene06": {
        "chapter": "CHAPTER 6",
        "title": "Test It Yourself & Next Up: The Upside-Down Big Bang",
        "subtitle_tag": "OPEN PYTHON WORKBENCH ON STOLER.SYSTEMS • CHAPTER 2 PREVIEW",
        "cinema_clip": "ep1_scene06_hourglass_preview.mp4",
    },
}


_RAW_CHUNKS = [
    # --- SCENE 00: WELCOME & MISSION (3 Chunks) ---
    (
        "scene00",
        "Intro A — Welcome Back to the Crucible",
        "Warm, relaxed, conversational — welcoming viewers back after Episode 0.",
        "Welcome back, everyone. My name is David, and this is Theoretically Not A Physicist. In our flagship introduction video, we stepped back and looked at the whole map of our human-and-AI thought experiment: The Universe Inside Out. Today, we're starting our six-part deep dive—taking one big claim at a time, putting it under a microscope or telescope, and testing it against real laboratory and satellite numbers.",
    ),
    (
        "scene00",
        "Intro B — Today's Question: Is Time Even Real?",
        "Curious, slightly dramatic pause after the question 'Is time even real?'",
        "And we're starting with the single weirdest claim in the entire model: Is time even real? In Episode Zero, we compared the four-dimensional universe to a vinyl record—where yesterday, today, and tomorrow are all sitting in the groove at once, and nothing on the map actually moves. That sounds great as a metaphor. But can a frozen four-dimensional fabric actually pass hard physics tests?",
    ),
    (
        "scene00",
        "Intro C — Our Three Tests Today & Open Honesty Rule",
        "Clear, grounded roadmap — let the listener know we'll show both wins and open weaknesses.",
        "In this episode, we're going to put that idea through three ruthless checks. First, why your brain only remembers the past and never the future. Second, why GPS satellites twenty thousand kilometers above your head run thirty-eight point six microseconds fast every single day. And third, where spinning black holes push this model to its absolute limit. Let's dive in.",
    ),

    # --- SCENE 01: THE ILLUSION OF 'NOW' & THE FROZEN 4D TAPESTRY (4 Chunks) ---
    (
        "scene01",
        "Part 1A — Why 'Flowing Time' Breaks Down",
        "Thoughtful, Sagan-style pacing — make the everyday riddle feel crystal clear.",
        "Think about how strange the word 'now' really is. If time is a river flowing past us, you have to ask: how fast is that river flowing? One second per second? That's not a speed—that's a circle. Over a century ago, Albert Einstein realized that two observers moving past each other can't even agree on which events happen at the same moment. One person's 'right now' is already in the other person's past or future.",
    ),
    (
        "scene01",
        "Part 1B — The Page-Wootters Timeless Tapestry",
        "Pronunciation note: 'Page-Wootters' = 'Page Woot-erz', 'QuTiP' = 'Cue-Tip'.",
        "In nineteen eighty-three, physicists Don Page and William Wootters took that puzzle to the quantum level. They showed that the entire universe can be completely frozen—with zero total energy change and zero ticking clock outside it—and yet still look full of motion from the inside. In our Python Science Workbench using the QuTiP quantum engine, we built a toy version of this exact equation, and the outside motion comes out to literal zero.",
    ),
    (
        "scene01",
        "Part 1C — Two Observers Inside the Same Groove",
        "Paint the picture of Observer Channel A and Observer Channel B looking across the table.",
        "Here's the magic trick. When you step inside the fabric and look through a local observer channel—measuring one part of the weave against a neighboring clock thread—the frozen pattern springs to life. Even better, when we place two separate observer channels at opposite ends of our quantum grid, their views of the shared wave match to fifteen decimal places. They share one consistent reality without anything needing to 'flow' from the outside.",
    ),
    (
        "scene01",
        "Part 1D — The Big Catch",
        "Pause briefly before asking the skeptic's question.",
        "But any good skeptic should immediately raise their hand right there. If the whole four-dimensional tapestry is already sitting there—from the smooth Big Bang waist all the way out to the tangled outer rim—why does your life feel like a one-way street? Why can you remember what you had for breakfast this morning, but you can't remember what you'll have for breakfast tomorrow?",
    ),

    # --- SCENE 02: THE BRAIN NEEDLE & LANDAUER'S LAW OF MEMORY (5 Chunks) ---
    (
        "scene02",
        "Part 2A — What Is a Memory, Physically?",
        "Tactile, grounded explanation — turn 'memory' into physical atoms and heat.",
        "To answer that, we have to stop treating 'memory' like a ghost in your head and ask what a memory actually is in physics. Whether it's a photograph on your phone, a crater on the Moon, or a new synapse firing in your brain, writing down a memory means taking a piece of matter and locking it into a new record state.",
    ),
    (
        "scene02",
        "Part 2B — Rolf Landauer's 1961 Discovery",
        "Pronunciation note: 'Landauer' = 'Lan-dow-er' (rhymes with power).",
        "In nineteen sixty-one, an IBM physicist named Rolf Landauer proved one of the deepest laws in information science. He showed that resetting and locking in even a single binary bit of memory—one tiny yes-or-no record—is physically impossible unless you pay an entropy tax. You have to dump at least a tiny packet of heat, equal to Boltzmann's constant times temperature times the natural log of two, out into the surrounding fabric.",
    ),
    (
        "scene02",
        "Part 2C — Why the Brain Needle Only Reads One Way",
        "Connect the Vinyl Record needle directly to Landauer's heat tax.",
        "Now picture our four-dimensional tapestry again. At one end—what we call the Big Bang waist—the fabric is pulled super smooth, simple, and low-entropy. At the wide outer rim, the threads are tangled into trillions of microscopic knots. Because Landauer's law says every new memory has to add more microscopic tangles, any slice of your brain that contains yesterday's memories must sit on the more-tangled side of yesterday.",
    ),
    (
        "scene02",
        "Part 2D — Why Tomorrow Looks Blank",
        "Warm, aha-moment delivery — make the resolution feel effortless.",
        "In other words, you don't remember the smooth side of the tapestry because 'time moved forward.' You remember the smooth side because that's the only direction where the physical heat tax of writing a memory can be paid. When you look toward the smoother Big Bang waist, your brain holds a chain of recorded footprints. When you look toward the wider, more tangled rim, those footprints haven't been paid for yet—so we call that direction 'the open future.'",
    ),
    (
        "scene02",
        "Part 2E — The Two-Wing Mirror Twist",
        "Intriguing, mind-bending visual of the two-wing hourglass.",
        "And remember our two-wing cosmic hourglass from Episode Zero. Because the smooth waist sits right in the middle, entropy and tangling grow outward on both of the wings. That means if there's an observer living on the twin antimatter wing on the other side of the Big Bang, their brain needle also pays Landauer's heat tax outward from the waist. To them, the Big Bang is also the distant past, and their time feels just as normal as ours.",
    ),

    # --- SCENE 03: THE 20,000-KILOMETER TEST: WHY GPS SATELLITES RUN FAST (5 Chunks) ---
    (
        "scene03",
        "Part 3A — From Philosophy to Hard Engineering",
        "Energetic shift — moving from brain thermodynamics to precision satellite hardware.",
        "Okay, explaining memory is Step One. Step Two is much tougher. If time isn't a separate thing that curves in empty space—if it's just the local vibration rate of knots inside of a stretched four-dimensional fabric—can that fabric predict the exact numbers engineers see in real satellites orbiting Earth right now?",
    ),
    (
        "scene03",
        "Part 3B — How a Stretched Weave Changes Clock Rates",
        "Explain the refractive index / fabric tension idea in plain, visual English.",
        "In our model, a heavy mass like the Earth pulls the surrounding fabric inward, packing the threads denser near the ground and leaving them looser high up in space—just like glass that gets denser toward the center of a lens. When an atomic clock sits down here on Earth where the weave is tightly packed, its internal electromagnetic waves take slightly longer to bounce back and forth than they do high up in orbit.",
    ),
    (
        "scene03",
        "Part 3C — The Two Competing Clock Shifts in Orbit",
        "Walk clearly through the two opposing numbers: -7.2 microseconds vs +45.8 microseconds.",
        "Right now, thirty-one GPS satellites are circling Earth twenty thousand one hundred and eighty-four kilometers above sea level, traveling at nearly fourteen thousand kilometers an hour. Their atomic clocks feel two opposite effects at once. First, because the satellite is moving fast through the weave, its internal wave paths stretch out into diagonals—slowing the clock down by seven point two microseconds per day.",
    ),
    (
        "scene03",
        "Part 3D — The +38.6 Microsecond Verdict",
        "Punchy, concrete engineering payoff — 11.4 kilometers per day on Google Maps!",
        "Second, because the satellite is high up where Earth's pull on the fabric is much weaker, the looser weave lets the clock vibrate faster by forty-five point eight microseconds per day. Put minus seven point two and plus forty-five point eight together, and the satellite clock gains exactly thirty-eight point six microseconds every single day. If engineers didn't program that exact offset into GPS hardware, your phone's map would drift off the road by over eleven kilometers a day.",
    ),
    (
        "scene03",
        "Part 3E — The 3,189-Kilometer Zero-Crossing Sweet Spot",
        "Highlight the cool interactive discovery in Tab 7 of our Science Workbench.",
        "And when we plotted the full altitude curve in Tab Seven of our Science Workbench, you can see a really cool crossover point. Down in Low Earth Orbit at four hundred kilometers, the International Space Station moves so fast that speed-slowing wins, and astronauts actually age about twenty-eight microseconds a day slower than we do. Then, at exactly three thousand one hundred and eighty-nine kilometers up—half an Earth radius—the two effects cancel to zero.",
    ),

    # --- SCENE 04: MERCURY, CASSINI & COLLIDING NEUTRON STARS (4 Chunks) ---
    (
        "scene04",
        "Part 4A — Raising the Stakes Beyond Earth",
        "Build tension — satellite gravity is weak, so what happens near the Sun or neutron stars?",
        "Matching GPS satellites proves that a stretched fabric works in Earth's gentle gravity. Historically, though, plenty of toy gravity ideas pass weak tests near Earth and then crash and burn when gravity gets stronger. So we threw three of astrophysics' toughest precision benchmarks at our exponential weave equation.",
    ),
    (
        "scene04",
        "Part 4B — Mercury's Wobble & The Cassini Radio Test",
        "Pronunciation note: 'Cassini' = 'Kuh-see-nee', 'Shapiro' = 'Shuh-peer-oh'.",
        "First, planet Mercury orbits so close to the Sun that the extra tension in the weave makes its oval orbit slowly rotate by forty-two point nine-eight arcseconds per century. And our exponential fabric profile hits that exact number. Second, when NASA's Cassini spacecraft beamed radio signals right past the edge of the Sun on its way to Saturn, the denser weave delayed those radio waves by precisely the amount predicted, matching to within two parts in a hundred thousand.",
    ),
    (
        "scene04",
        "Part 4C — The GW170817 Neutron Star Crash",
        "Pronunciation note: 'GW170817' = 'G-W seventeen-oh-eight-seventeen'.",
        "Third, and the most dramatic of all: in August twenty seventeen, observatories detected two ultra-dense neutron stars slamming into each other a hundred and thirty million light-years away. That crash sent out both a flash of gamma-ray light and a ripple of gravity across the cosmos. After traveling for a hundred and thirty million years, the gravity wave and the light flash arrived at Earth within one point seven seconds of each other.",
    ),
    (
        "scene04",
        "Part 4D — Why Sideways Shear Waves Move at Light Speed",
        "Visual distinction between a sideways ripple on a taut string and a compression squeeze.",
        "Why did that single observation wipe out dozens of alternative gravity theories overnight? Because in our stretched fabric, both light and gravitational waves are sideways shear ripples riding on the exact same taut threads. They don't travel through two different mediums. They're two ways of plucking the same silk weave, locking their speeds together to one part in a quadrillion.",
    ),

    # --- SCENE 05: THE HONEST SCORECARD & LACUNA LITERATURE AUDIT (4 Chunks) ---
    (
        "scene05",
        "Part 5A — New Backup from the Lacuna Research Graph",
        "Pronunciation note: 'Lacuna' = 'Luh-koo-nuh', 'Griniasty' = 'Ee-tie Grin-ee-ah-stee', 'Unruh' = 'Uhn-roo'.",
        "Before we look at where this chapter struggles, I want to share a cool discovery we just made using Lacuna—a new AI research map covering over two point two million scientific papers. When we searched Lacuna for wave-medium gravity, it surfaced a remarkable physics paper by Itay Griniasty and colleagues proving—even in a real water-wave laboratory tank—that any continuous wave medium with background ripples naturally creates an Unruh horizon temperature for accelerating observers.",
    ),
    (
        "scene05",
        "Part 5B — Keeping Our Promise: Where Does Chapter 1 Sweat?",
        "Honest, transparent, zero-hype tone — this is what makes TNaP special.",
        "That gives real peer-reviewed backing to our wave-fabric intuition. Now, keeping our channel's promise, let's turn the red-team spotlight on ourselves. Where does replacing curved empty spacetime with a stretched four-dimensional weave run into real mathematical pushback?",
    ),
    (
        "scene05",
        "Part 5C — Open Hurdle #1: Spinning Black Holes (Frame Dragging)",
        "Pronunciation note: 'Kerr' = 'Kur' (rhymes with fur).",
        "Hurdle number one is spinning masses. A non-spinning star or planet just pulls the fabric inward, and our simple density formula handles that beautifully. But when a massive black hole spins at nearly the speed of light, what physicists call the Kerr metric doesn't just stretch space—it twists and drags space around like a whirlpool. To match that smoothly without extra friction, our weave can't just sit still. It has to support frictionless superfluid vortex swirl.",
    ),
    (
        "scene05",
        "Part 5C-Bonus — Self-Healing Threads & The Fishing-Reel Horizon",
        "🎬 PRONUNCIATION: 'Planck' = 'Plahnk'. Genuine excitement — this was your real live 1.000000 discovery!",
        "And get this—right while we were building this episode, another question hit me: if a black hole spins billions of times, why don't those space threads eventually snap? In our superfluid equation, the smallest scale is literally called the healing length—overstretched threads briefly melt across a single Planck width, slip one turn, and weld right back together. What's even wilder is when we checked the math of winding unbreakable Planck-tension fishing line onto a central reel, the wound sphere grew at the exact black-hole horizon radius—up to six decimal places.",
        "chunk_23b",
    ),
    (
        "scene05",
        "Part 5D — Open Hurdle #2: Event Horizons vs. Exponential Throats",
        "Explain the testable difference between a textbook black hole horizon and an ultra-dense weave throat.",
        "Hurdle number two happens right at the edge of a black hole. In textbook relativity, falling past the event horizon is a one-way trapdoor into a singular point. In an exponential weave, the thread density keeps climbing smoothly into an ultra-dense, nearly frozen throat instead of tearing into a singularity. Could future gravitational-wave ringdown detectors spot a tiny echo from that dense throat? That's a concrete way future data could prove this model right—or dead wrong.",
    ),

    # --- SCENE 06: TEST IT YOURSELF & CHAPTER 2 PREVIEW (3 Chunks) ---
    (
        "scene06",
        "Part 6A — Try the Interactive GPS & Landauer Lab Yourself",
        "Warm invitation to stoler.systems and the GitHub repo.",
        "We've added all the math and the code from today's episode into two brand-new interactive tabs in our Python Science Workbench, and published the results on stoler dot systems and our open-source GitHub repository. You can drag the satellite altitude slider yourself from the International Space Station all the way past GPS orbit and watch the speed and general relativity curves cross in real time.",
    ),
    (
        "scene06",
        "Part 6B — Living Recap Ledger & Viewer Critique Callout",
        "Remind viewers about the Post-Chapters Recap Video & Discord community check.",
        "Remember, we're also keeping a living scorecard across all six chapters. At the end of this series, we'll make a full Recap and Update video reviewing every new paper we uncover, every equation that held up, and the sharpest critiques you leave in the comments—so if you spot a flaw or a test that we missed, drop it down below. Subscribe to the channel, and tell me if you guys are interested in setting up a Discord.",
    ),
    (
        "scene06",
        "Part 6C — Next Time: The Upside-Down Big Bang",
        "Warm, cinematic sign-off.",
        "Next time, in Episode Two, we're traveling all the way to the narrow waist of the cosmic hourglass to tackle the Upside-Down Big Bang, why the cosmic microwave sky is mysteriously quiet on giant scales, and where all the universe's antimatter went. Thanks for watching, stay inquisitive, and I'll see you in Chapter Two.",
    ),
]


CHUNKS: List[ChunkSpec] = []
_orig_counter = 0
for idx, raw_item in enumerate(_RAW_CHUNKS):
    if len(raw_item) == 5:
        sc_id, lbl, coach, txt, explicit_cid = raw_item
        cid = explicit_cid
    else:
        sc_id, lbl, coach, txt = raw_item
        cid = f"chunk_{_orig_counter:02d}"
        _orig_counter += 1
    meta = SCENE_METADATA[sc_id]
    CHUNKS.append(
        {
            "num": idx,
            "chunk_id": cid,
            "scene_id": sc_id,
            "chapter": meta["chapter"],
            "scene_title": meta["title"],
            "subtitle_tag": meta["subtitle_tag"],
            "cinema_clip": meta["cinema_clip"],
            "label": lbl,
            "coaching": coach,
            "text": txt,
        }
    )


if __name__ == "__main__":
    total_words = sum(len(c["text"].split()) for c in CHUNKS)
    est_min = total_words / 145.0
    print(f"Loaded {len(CHUNKS)} chunks across {len(SCENE_METADATA)} scenes.")
    print(f"Total word count: {total_words} words (~{est_min:.1f} minutes at 145 wpm).")
