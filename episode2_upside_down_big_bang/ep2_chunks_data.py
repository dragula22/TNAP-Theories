"""
Single source of truth for all 31 bite-sized recording chunks of Episode 2:
  'Episode 2 — The Upside-Down Big Bang & Where All the Antimatter Went'

Incorporates:
  • All of David's natural on-the-spot phrasing tweaks from his Teleprompter Studio recording session
  • David's Numerical Digits Rule (years & numbers written as clean digits: 1979, 2012, 13.8 billion, 334, 0.72, etc.)
  • Explicit 🎬 PRONUNCIATION & pacing notes on every chunk
  • Zero burned-in subtitles on video frames (standalone .SRT exported directly from locked master audio)
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
        "title": "WeaveForge, Blind Gaia DR4 Lock & Entering the Cosmic Hourglass",
        "subtitle_tag": "EPISODE 2 • THEORETICALLY NOT A PHYSICIST • STOLER.SYSTEMS",
        "cinema_clip": "ep2_scene00_welcome_hourglass.mp4",
    },
    "scene01": {
        "chapter": "CHAPTER 1",
        "title": "Penrose's Needle-Tip Paradox & Turning the Big Bang Upside Down",
        "subtitle_tag": "1-IN-10^(10^123) ODDS • INVERTED ENTROPY SMOOTHING DRAIN",
        "cinema_clip": "ep2_scene01_penrose_upside_down_hourglass.mp4",
    },
    "scene02": {
        "chapter": "CHAPTER 2",
        "title": "The 'Cheat-Code' Audit: Rewound Movie vs. Two-Ring Soap Film",
        "subtitle_tag": "WHY TWO CLAMPED BOUNDARIES SQUEEZE OUT GIANT SKY WAVES",
        "cinema_clip": "ep2_scene02_two_ring_catenoid_soapfilm.mp4",
    },
    "scene03": {
        "chapter": "CHAPTER 3",
        "title": "Cosmic Receipt #1: Planck's Quiet Sky & Cambridge's Quantized Curvature",
        "subtitle_tag": "QUADRUPOLE CLAMP (334 µK²) & DENG–HANDLEY (2024–2025) CPT STEPS",
        "cinema_clip": "ep2_scene03_planck_quadrupole_and_lacuna.mp4",
    },
    "scene04": {
        "chapter": "CHAPTER 4",
        "title": "The BABAR 14-Sigma Brick & Where All the Universe's Antimatter Went",
        "subtitle_tag": "LÜDERS–PAULI–SCHWINGER CPT MIRROR WINGS • SUBATOMIC COIN-SORTER",
        "cinema_clip": "ep2_scene04_babar_cpt_twin_wings.mp4",
    },
    "scene05": {
        "chapter": "CHAPTER 5",
        "title": "The Honest Scorecard: The CMB Third Peak Rescue & Hard Kill-Switches",
        "subtitle_tag": "'BULLET CLUSTER IN REVERSE' PLEATS (Ω_m = 0.3094) • LITEBIRD & KATRIN TESTS",
        "cinema_clip": "ep2_scene05_cmb_third_peak_scorecard.mp4",
    },
    "scene06": {
        "chapter": "CHAPTER 6",
        "title": "Fly Through the 3D Hourglass Yourself & Next Up: The Double-Slit",
        "subtitle_tag": "WEAVEFORGE ARENA 4 • ZENODO DOI LOCKED • EPISODE 3 PREVIEW",
        "cinema_clip": "ep2_scene06_doubleslit_preview.mp4",
    },
}


_RAW_CHUNKS = [
    # --- SCENE 00: WELCOME, WEAVEFORGE & GAIA DR4 BLIND LOCK (4 Chunks) ---
    (
        "scene00",
        "Intro A — Welcome Back & Building WeaveForge",
        "Warm, calm, conversational — welcoming viewers back after Episode 1.",
        "Welcome back, everyone. My name is David, and this is Theoretically Not A Physicist. Since Episode 1—where we put frozen 4-dimensional time, human memory, GPS satellite clocks, and spinning black hole horizons under the microscope—we have hit two big milestones behind the scenes. First off, we built an open-source 3-dimensional physics engine called WeaveForge, so we can actually throw knots, galaxies, and cosmic membranes into a virtual box and watch where our equations hold up—or break.",
    ),
    (
        "scene00",
        "Intro B — Carving Our Blind Gaia DR4 Prediction in Stone",
        "🎬 PRONUNCIATION: 'Gaia' = 'GUY-uh'  |  'Zenodo' = 'zeh-NOH-doh'. Calm, grounded scientific honesty.",
        "Second, ahead of the European Space Agency opening the vault on Gaia Data Release 4 next month on December 2nd, we just locked an official, timestamped CERN Zenodo prediction in stone. With zero free tuning knobs, we published exact orbital speed boosts for wide twin stars across the Milky Way disk and halo—plus a 4.63% wider black hole shadow test. If December's star data disagrees, our galactic rule is falsified on the spot.",
    ),
    (
        "scene00",
        "Intro C — Today's Deep Dive: The Upside-Down Big Bang",
        "Curious, calm lift as you introduce the cosmic hourglass waist.",
        "With those blind predictions locked in the vault, today in Episode 2 we are traveling all the way to the narrow waist of the cosmic hourglass to test Pillar 3 of our model: The Upside-Down Big Bang, why the oldest light in the night sky is mysteriously quiet on giant scales, and where all the universe's missing antimatter went.",
    ),
    (
        "scene00",
        "Intro D — Three Heavy Bricks We're Throwing Today",
        "🎬 PRONUNCIATION: 'BABAR' = 'Buh-BAR' (like Babar the elephant)  |  'sigma' = 'SIG-muh'. Clear roadmap.",
        "And just like Episode 1, we're going to throw three heavy bricks straight at our own idea. First: isn't flipping the cosmic arrow of entropy just a cheap video-game cheat code? Second: didn't Stanford's BABAR particle collider already prove at 14 sigma that subatomic physics runs differently forward and backward in time? And third: how could a universe without dark matter particles possibly survive the famous third peak in the Cosmic Microwave Background? Let's dive in.",
    ),

    # --- SCENE 01: PENROSE'S PARADOX & TURNING THE HOURGLASS UPSIDE DOWN (4 Chunks) ---
    (
        "scene01",
        "Part 1A — Rewinding the Second Law of Thermodynamics",
        "Unhurried storytelling — everyday coffee cup to 13.8 billion years ago.",
        "Let's start with a riddle that has haunted cosmology for half a century. In everyday life, the Second Law of Thermodynamics feels like common sense: left alone, ice cubes melt, cream mixes into hot coffee, and tidy rooms get messier. Disorder—what physicists call entropy—goes up. That sounds completely harmless, until you rewind the cosmic movie 13.8 billion years back to the Big Bang.",
    ),
    (
        "scene01",
        "Part 1B — Sir Roger Penrose's Needle-Tip Calculation",
        "🎬 PRONUNCIATION: 'Penrose' = 'PEN-rohz'. Pause slightly before the giant odds.",
        "If disorder has been climbing for nearly 14 billion years, then the baby universe had to start in a state of almost unimaginable gravitational smoothness. How smooth? Back in 1979, Nobel laureate Sir Roger Penrose calculated the odds of getting our smooth Big Bang by pure chance out of every lumpy black-hole mess that same energy could have formed. The odds are 1 in 10, raised to the power of 10 to the 123.",
    ),
    (
        "scene01",
        "Part 1C — Turning the Cosmic Hourglass Upside Down",
        "Thoughtful 'what if' — contrast balancing a needle with water draining smooth.",
        "Even cosmic inflation doesn't erase that riddle—it has to assume the tiny patch that inflated started extraordinarily smooth in the first place. So in our thought experiment, we turned the hourglass upside down. What if the universe didn't 'begin' at the smooth narrow end at all? What if messy, tangled chaos out on a wide outer rim is the natural, zero-fine-tuning boundary—and the Big Bang is a narrow topological drain at the center where 4-dimensional fabric wrinkles get pulled flat and smooth?",
    ),
    (
        "scene01",
        "Part 1D — Why Nobody Sees Broken Teacups Jump Off the Floor",
        "🎬 PRONUNCIATION: 'Landauer' = 'LAN-dow-er' (rhymes with power). Callback to Episode 1.",
        "Now hold on—if the mathematical smoothing runs inward toward the Big Bang waist, why don't we see shattered teacups leap off the kitchen floor? Remember what we proved in Episode 1 with Rolf Landauer's law of memory: a physical brain can only write new memories in the direction where heat and disorder increase. So any living observer woven inside that timeless tapestry automatically remembers the smooth Big Bang waist as 'the distant past' and experiences the wider, messier weave as 'the future.'",
    ),

    # --- SCENE 02: THE 'KONAMI CHEAT-CODE' AUDIT — TWO-RING SOAP FILM (4 Chunks) ---
    (
        "scene02",
        "Part 2A — Asking My Own Blunt Skeptic Question",
        "Natural questioning inflection at the end — quoting your own Round 6 pushback!",
        "When we first wrote that down, I stopped the whole session and asked the AI team a blunt question: 'Wait a second—isn't flipping plus-t to minus-t on a blackboard the ultimate physics cheat code? Like typing Up, Up, Down, Down, Left, Right, B, A on an old Nintendo controller—just swapping the words start and finish without explaining a single piece of the physics?'",
    ),
    (
        "scene02",
        "Part 2B — When Flipping Time Really IS a Fake Cheat Code",
        "🎬 PRONUNCIATION: 'Penrose' = 'PEN-rohz'. Candid, measured reveal.",
        "When we ran the information math, the answer was: yes. If you only specify one boundary and play a movie in reverse, it is a 100% fake cheat code. To make scattered ocean waves converge onto one tiny central spot by luck, you'd have to secretly hand-tune 4.7 times 10 to the 122 bits of hidden wave phases out on the rim. You haven't solved Penrose's miracle—you just hid it underneath the rug.",
    ),
    (
        "scene02",
        "Part 2C — Dipping Two Brass Hoops Into Soapy Water",
        "🎬 PRONUNCIATION: 'catenoid' = 'KAT-uh-noyd' (curved soap-film hourglass neck). Tactile visual imagery.",
        "Everything changes, though, when a physical sheet is clamped at both ends—like dipping a wide, noisy brass hoop and a tiny, smooth central ring into soapy water. You don't hand-tune a single soap molecule on the outer hoop. Tension across the whole 4-dimensional weave automatically pulls the film into a smooth, curved hourglass neck—a shape mathematicians call a catenoid—all on its own.",
    ),
    (
        "scene02",
        "Part 2D — Why a Narrow Waist Squeezes Out Giant Sky Ripples",
        "Land the testable consequence clearly and deliberately.",
        "Better yet, a two-ring soap film makes a concrete telescope prediction that a rewound movie never could. Because every standing wave on the fabric has to physically fit between the outer boundary and that narrow central waist, super-wide ripples—waves wider than the waist itself—get squeezed down. If our universe really is a two-boundary hourglass weave, the largest temperature ripples across the entire night sky have to be unusually quiet.",
    ),

    # --- SCENE 03: COSMIC RECEIPT #1 — PLANCK'S QUIET SKY & DENG-HANDLEY (4 Chunks) ---
    (
        "scene03",
        "Part 3A — Checking 30 Years of Space Telescope Maps",
        "🎬 PRONUNCIATION: 'COBE' = 'KOH-bee'  |  'WMAP' = 'DUB-uhl-yoo-map'  |  'Planck' = 'PLAHNK'.",
        "So let's look up at the real sky and check. For more than 30 years—starting with NASA's COBE satellite, then WMAP, and finally the European Space Agency's Planck Space Observatory—astronomers have mapped the Cosmic Microwave Background, the faint fossil glow left over from the hot early universe. Across small and medium patches of the sky, textbook cosmology matches those ripples with breathtaking precision.",
    ),
    (
        "scene03",
        "Part 3B — The Mysterious Quiet Quadrupole",
        "🎬 PRONUNCIATION: 'quadrupole' = 'KWAHD-ruh-pohl'  |  'Lambda-CDM' = 'LAM-duh see-dee-em'  |  'microkelvin' = 'MY-kroh-kel-vin'.",
        "Yet on the single widest scale spanning the entire heavens—a giant four-lobed wave called the quadrupole—all three space missions saw something eerie. Standard Lambda-CDM expects that giant sky wave to ring at nearly 1,100 microkelvin squared. Instead, Planck measured it down around 230 to 330 microkelvin squared—more than three times quieter than expected.",
    ),
    (
        "scene03",
        "Part 3C — Clamping the Waist at 334 Microkelvin Squared",
        "🎬 PRONUNCIATION: 'Planck' = 'PLAHNK'. Calm, grounded scientific payoff.",
        "In textbook cosmology, that missing power is usually shrugged off as a fluke—rolling an unlucky cosmic die because we only have one universe to measure. When we clamped our hourglass waist at the cosmic horizon scale in Python, every smaller ripple across the sky stayed 99.95% untouched, while the giant quadrupole dropped automatically to 334 microkelvin squared—landing right inside Planck's quiet sky.",
    ),
    (
        "scene03",
        "Part 3D — Lacuna Surfaces Deng & Handley at Cambridge",
        "🎬 PRONUNCIATION: 'Lacuna' = 'luh-KOO-nuh'  |  'Wei-Ning Deng' = 'WAY-ning DENG'  |  'Turok' = 'TOO-rock'  |  'Latham' = 'LAY-thum'.",
        "And here's where our 2.2-million-paper Lacuna discovery engine gave us chills. It uncovered two peer-reviewed Physical Review D papers from 2024 and 2025 by Wei-Ning Deng and Will Handley at Cambridge University, building on earlier mirror-universe work by Neil Turok, Latham Boyle, and Kieran Finn. Independently in quantum cosmology, they proved that symmetric boundary conditions across the Big Bang force spatial curvature into quantized steps and naturally suppress those exact giant sky waves.",
    ),

    # --- SCENE 04: THE BABAR 14-SIGMA BRICK & MISSING ANTIMATTER (6 Chunks) ---
    (
        "scene04",
        "Part 4A — Brick #2: Particle Accelerators Push Back Hard",
        "Thoughtful pivot — bring out the collider brick!",
        "Passing that quiet-sky check felt amazing—for about 10 minutes, until we threw brick number two straight at our own windshield. If our upside-down hourglass simply reversed time by itself as it narrowed into the Big Bang, there is an absolute dealbreaker waiting inside particle accelerators here on Earth: nature does not run identically forward and backward when you only flip time.",
    ),
    (
        "scene04",
        "Part 4B — Stanford's BABAR Detector & the 14-Sigma Wall",
        "🎬 PRONUNCIATION: 'SLAC' = 'SLACK'  |  'BABAR' = 'Buh-BAR'  |  'B-mesons' = 'BEE MEZ-onz'.",
        "In 2012, physicists at Stanford's SLAC National Accelerator Laboratory used the BABAR detector to watch entangled subatomic particles called B-mesons flip back and forth between two quantum states. Flipping from state A to state B did not happen at the same speed as flipping from state B back to state A—proving microscopic time-reversal violation at more than 14 sigma. 5 sigma wins a Nobel Prize; 14 sigma means naive time-reversal alone is dead on arrival.",
    ),
    (
        "scene04",
        "Part 4C — Lüders, Pauli, Schwinger & Full CPT Symmetry",
        "🎬 PRONUNCIATION: 'Lüders' = 'LOO-derz'  |  'Pauli' = 'POW-lee'  |  'Schwinger' = 'SHVING-er'  |  'CPT' = 'see-pee-tee'.",
        "So how can a symmetric Big Bang throat survive BABAR? Through one of the bedrock theorems of modern physics, proved in the 1950s by Gerhart Lüders, Wolfgang Pauli, and Julian Schwinger: CPT symmetry. Nature breaks time-reversal T on its own, and it breaks mirror reflection P and matter-antimatter swap C—but when you flip Charge, Parity, and Time all together, every single law of particle physics stays 100% exact.",
    ),
    (
        "scene04",
        "Part 4D — Two Mirror Wings & Defusing the Helium-4 Bomb",
        "🎬 PRONUNCIATION: 'Janus' = 'JAY-nus'  |  'Julian Barbour' = 'JOO-lee-un BAR-ber'  |  'Turok' = 'TOO-rock'.",
        "Look at what that forces our cosmic hourglass to look like—connecting directly to Julian Barbour's gravitational Janus point and Turok, Boyle, and Finn's CPT universe. Instead of ending at a sharp wall, the narrow Big Bang neck joins two wings back-to-back. Right at that smooth waist, mirror symmetry forces cosmic shear to zero—instantly defusing a 230-sigma Big Bang Helium-4 explosion that nearly wrecked an earlier draft of our math.",
    ),
    (
        "scene04",
        "Part 4E — Andrei Sakharov's Missing Antimatter Mystery",
        "🎬 PRONUNCIATION: 'Andrei Sakharov' = 'AHN-dray SAH-kuh-roff'. Calm wonder around the missing antimatter puzzle.",
        "And then an unexpected prize drops right into our lap. Back in 1967, physicist Andrei Sakharov laid out one of science's biggest mysteries: if energy turns into matter and antimatter in equal pairs, why didn't the young universe annihilate completely into pure light? Today, for every 10 billion photons in space, our cosmos has about 6 leftover protons—and virtually zero antiprotons. Where did all of the antimatter go?",
    ),
    (
        "scene04",
        "Part 4F — The Subatomic Coin-Sorter & Unitary Black Holes",
        "🎬 PRONUNCIATION: 'BABAR' = 'Buh-BAR'  |  'Hawking' = 'HAW-king'  |  'unitary' = 'YOO-nih-tair-ee'.",
        "Across a two-wing CPT hourglass, the Big Bang waist itself carries exact zero net matter charge—nothing lopsided had to appear out of nothing. Instead, that exact BABAR time-and-charge asymmetry acts like a subatomic coin-sorter at the pinch: sorting 6 protons per 10 billion photons onto our wing, and 6 antiprotons per 10 billion photons onto our twin mirror wing. Even better, clamping both boundaries keeps Stephen Hawking's black-hole radiation curve completely unitary—recovering 100% of quantum information with zero lost bits.",
    ),

    # --- SCENE 05: HONEST SCORECARD — CMB THIRD PEAK & HARD KILL-SWITCHES (6 Chunks) ---
    (
        "scene05",
        "Part 5A — Brick #3: The Famous 'Third Bump' Graveyard",
        "Grounded, transparent Responsible-AI tone — pivot squarely into the hardest hurdle.",
        "Now, you know our rule on this channel: we never show where a model shines without showing where the math sweats. And the biggest historical graveyard for every theory without dark matter particles sits right inside that exact Planck map of the early sky—at a landmark called the third acoustic peak.",
    ),
    (
        "scene05",
        "Part 5B — Why Our First Memoryless Test Crashed Hard",
        "🎬 PRONUNCIATION: 'Planck' = 'PLAHNK'. Explain the cosmic drumhead bounce in plain, vivid English.",
        "Before atoms formed, hot protons and electrons fell into gravity bowls, compressed like a drumhead, and bounced back out under fierce photon pressure. Cold dark matter ignores light, sitting quietly in each bowl so Planck's third sound peak stays nearly as tall as the second—at 0.72. When we first ran memoryless fabric gravity, the bowls emptied during the bounce and our third peak crashed to 0.16.",
    ),
    (
        "scene05",
        "Part 5C — 'The Bullet Cluster in Reverse': Uncharged Spacetime Pleats",
        "Tactile tablecloth fold imagery — make 'uncharged pleats' click effortlessly.",
        "That failure forced us to look closer at the 3-dimensional weave itself. Just like you can fold a wrinkle—a pleat—into a taut tablecloth without tying a knot in a single thread, space itself can hold uncharged geometric pleats. Because those pleats have zero electric charge, blinding early-universe photons pass straight through them without pushing them around. It's the famous Bullet Cluster collision playing out in reverse inside the baby universe.",
    ),
    (
        "scene05",
        "Part 5D — The 99.92% Density Match (Zero Free Knobs)",
        "🎬 PRONUNCIATION: 'Planck' = 'PLAHNK'. Calm, clear payoff.",
        "What's even wilder, the hoop-buckling stiffness of our 3-dimensional weave gives a pleat-to-knot energy ratio of 5 plus 1 over pi. That lands total effective matter density at 0.3094—matching Planck's measured 0.3097 to 99.92% with zero free knobs, and lifting that third acoustic peak right back into the 0.66 to 0.72 bullseye.",
    ),
    (
        "scene05",
        "Part 5E — Our Open Yellow Warning Badge & LiteBIRD Kill-Switch",
        "🎬 PRONUNCIATION: 'JAXA' = 'JACK-suh'  |  'LiteBIRD' = 'LIGHT-bird'. Candid WeaveForge [WARN] honesty.",
        "Still, as we flag a bright yellow warning badge inside WeaveForge, treating 3-dimensional pleats as a smooth background fluid is an approximation; evolving full pleat shear across all 2,500 polarization peaks is still open work. Plus, JAXA's upcoming LiteBIRD satellite can sink our narrow waist outright: our model predicts a large-angle B-mode ratio of 0.415, whereas a flat plateau above 0.85 falsifies it.",
    ),
    (
        "scene05",
        "Part 5F — Kill-Switch #2: The Zero-Mass Lightest Neutrino Test",
        "🎬 PRONUNCIATION: 'CPT' = 'see-pee-tee'  |  'KATRIN' = 'KAH-treen'  |  'Euclid' = 'YOO-klid'.",
        "And here's Kill-Switch Number 2: an exact two-wing CPT pinch across a smooth Big Bang waist predicts that the lightest of the three neutrinos has literal zero mass—0.00 electron-volts. So if the KATRIN laboratory experiment or the Euclid Space Telescope proves the lightest neutrino weighs above two hundredths of an electron-volt, our exact two-wing pinch goes straight into the trash—no moving goalposts.",
    ),

    # --- SCENE 06: EXPLORE WEAVEFORGE & STOLER.SYSTEMS + EPISODE 3 PREVIEW (3 Chunks) ---
    (
        "scene06",
        "Part 6A — Spin the 3D Hourglass & Check Our Blind Zenodo Lock",
        "🎬 PRONUNCIATION: 'catenoid' = 'KAT-uh-noyd'  |  'BABAR' = 'Buh-BAR'  |  'Gaia' = 'GUY-uh'  |  'Zenodo' = 'zeh-NOH-doh'.",
        "Every single script and simulation from today's episode—from the two-ring catenoid sky clamp and BABAR coin-sorter to our pre-registered December 2nd Gaia DR4 blind prediction on CERN Zenodo—is live right now on stoler.systems and our public GitHub repository. You can also open Arena 4 inside WeaveForge to spin the 3-dimensional CPT hourglass in real time.",
    ),
    (
        "scene06",
        "Part 6B — Living Recap Ledger & Physicists Welcome in the Comments",
        "🎬 PRONUNCIATION: 'QCD' = 'cue-see-dee'. Warm, open invitation to critics and viewers.",
        "Every open yellow badge from today—especially evolving full pleat polarization across the whole microwave sky and keeping the QCD strong-force angle untwisted at the waist—is logged on our Recap Video Living Ledger. Once we finish all six chapters, we'll film a dedicated Recap and Update episode reviewing every equation that held up, anything that broke, and the sharpest critiques you leave in the comments below.",
    ),
    (
        "scene06",
        "Part 6C — Next Time in Episode 3: The Double-Slit Without Spooky Magic",
        "Warm, calm, cinematic sign-off.",
        "Next time, in Episode 3, we're zooming from the cosmic hourglass right down to the quantum lab bench to tackle the strangest experiment in all of science: The Double-Slit Experiment Without Spooky Magic—testing whether two-ended standing waves on a taut weave can explain quantum interference and entanglement without particles ever splitting in two. Subscribe if you're enjoying the journey, stay inquisitive, and I'll see you in Chapter 3.",
    ),
]


CHUNKS: List[ChunkSpec] = []
for idx, raw_item in enumerate(_RAW_CHUNKS):
    if len(raw_item) == 5:
        sc_id, lbl, coach, txt, explicit_cid = raw_item
        cid = explicit_cid
    else:
        sc_id, lbl, coach, txt = raw_item
        cid = f"chunk_{idx:02d}"
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
