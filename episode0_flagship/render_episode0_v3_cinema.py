"""
Master 1920x1080 (`1080p`) Cinema Renderer & Assembler for Flagship Episode 0 v3 ('Sagan Edition'):
  'The Universe Inside Out: A Visual Guide to the Stretched Fabric & the Upside-Down Cosmic Hourglass'

Upgrades over v2:
  1. Uses `audio_v3/ep0_v3_manifest.json` & `audio_v3/episode0_v3_master_stereo.wav`:
       - 21 perfected Google Replicated Voice chunks preserved 100% untouched
       - 12 flagged chunks re-synthesized with calm, unhurried Sagan cadence + crystal-clear rewrites
       - Generous human processing pauses (`2.4s - 3.0s`), `4.2s` silent protogalaxy pleat-tuck showcase,
         and `9.6s` wondrous musical multi-galaxy cosmic zoom-out interlude!
  2. Uses `GPU3DSceneDirectorV3` (`gpu_scenes_v3.py`) + 21 AI Cinema B-Roll shots (including 3 new `1080p`
     `gemini-omni-1.1-flash` clips: dipping soap rings, Hubble+JWST ancient light, and multi-galaxy zoom-out).
  3. Chunk-locked glassmorphic broadcast callout HUDs synchronized to the exact spoken beat, while keeping
     the 9.6-second Sagan multi-galaxy pullback 100% uncluttered widescreen IMAX cinema!
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

EP0_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EP0_DIR))

from gpu_renderer_core import smootherstep01, smoothstep01
from gpu_scenes_v3 import GPU3DSceneDirectorV3, _find_chunk
from render_episode0_v2_cinema import (
    CINEMA_DIR,
    FONTS,
    FPS,
    H,
    SR,
    W,
    CinemaClipCache,
    blit_rgba_crop,
    draw_chapter_lower_third_and_watermark,
    draw_cold_open_hook_cards,
    draw_verbatim_subtitle,
)

AUDIO_V3_DIR = EP0_DIR / "audio_v3"
MANIFEST_V3_PATH = AUDIO_V3_DIR / "ep0_v3_manifest.json"
MASTER_WAV_V3 = AUDIO_V3_DIR / "episode0_v3_master_stereo.wav"

FINAL_V3_MP4 = EP0_DIR / "Episode_0_The_Universe_Inside_Out_v3_Sagan_Edition.mp4"
FINAL_MAIN_MP4 = EP0_DIR / "Episode_0_The_Universe_Inside_Out.mp4"
ARTIFACT_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")
ARTIFACT_MP4 = ARTIFACT_DIR / "Episode_0_The_Universe_Inside_Out.mp4"


def get_v3_broll_windows(scene: dict) -> List[Tuple[float, float, str, int]]:
    """Returns dynamic, chunk-locked AI Cinema B-roll windows so B-roll NEVER covers critical 3D animations!"""
    sid = scene["id"]
    if sid == "hook00":
        return [
            (0.0, 2.5, "v2_hook01_galaxy_shatter.mp4", 1),
            (4.6, 7.3, "v2_hook02_hourglass_flip.mp4", -1),
            (9.3, 11.5, "v2_sc02_knot_in_silk.mp4", 1),
        ]
    if sid == "scene00":
        ch01 = _find_chunk(scene, "chunk_01")
        ch03 = _find_chunk(scene, "chunk_03")
        t01_s = ch01["local_start"] if ch01 else 0.7
        t03_e = ch03["local_end"] if ch03 else 68.0
        return [
            (t01_s + 9.5, t01_s + 18.8, "v2_sc00_jwst_observatory.mp4", 1),
            (max(t01_s + 24.0, t03_e - 8.8), t03_e, "v2_hook02_hourglass_flip.mp4", 1),
        ]
    if sid == "scene01":
        ch07 = _find_chunk(scene, "chunk_07")
        t07 = ch07["local_start"] if ch07 else 66.0
        return [
            (0.0, 9.6, "scene01_midnight_cosmos.mp4", 1),
            (t07 + 1.0, t07 + 10.6, "v2_sc01_dark_scaffolding.mp4", -1),
        ]
    if sid == "scene02":
        ch10 = _find_chunk(scene, "chunk_10")
        t10 = ch10["local_start"] if ch10 else 24.0
        return [
            (0.0, 9.4, "scene02_woven_fabric.mp4", 1),
            (t10 + 14.5, t10 + 23.8, "v2_sc02_knot_in_silk.mp4", 1),
        ]
    if sid == "scene03":
        ch14 = _find_chunk(scene, "chunk_14")
        t14 = ch14["local_start"] if ch14 else 44.0
        return [
            (0.0, 9.4, "scene03_vinyl_needle.mp4", 1),
            (t14 + 20.0, t14 + 29.5, "v2_sc03_ink_in_water.mp4", 1),
        ]
    if sid == "scene04":
        ch18 = _find_chunk(scene, "chunk_18")
        t18 = ch18["local_start"] if ch18 else 61.0
        return [
            (0.0, 9.4, "scene04_flipping_hourglass.mp4", 1),
            (t18 + 14.5, t18 + 24.0, "v2_sc04_twin_wings.mp4", -1),
        ]
    if sid == "scene05":
        ch20 = _find_chunk(scene, "chunk_20")
        ch21 = _find_chunk(scene, "chunk_21")
        ch22 = _find_chunk(scene, "chunk_22")
        t20_s = ch20["local_start"] if ch20 else 14.0
        t21_e = ch21["local_end"] if ch21 else 89.0
        t22_s = ch22["local_start"] if ch22 else 92.0
        return [
            # 1) New 1080p dipping brass rings shot right as chunk_20 introduces dipping two brass rings!
            #    Ends BEFORE the 3D GPU stretching + tight macro zoom into the tiny singularity ring!
            (t20_s + 5.5, t20_s + 13.8, "v3_sc05_dipping_soap_rings.mp4", 1),
            # 2) New 1080p Hubble + JWST peering toward the ancient CMB horizon at the climax of chunk_21!
            (t21_e - 8.2, t21_e + 1.2, "v3_sc05_hubble_jwst_ancient_light.mp4", 1),
            # 3) Moody physics-lab double-slit wave interference shot early in chunk_22 (before 3D Ring Sensor!)
            (t22_s + 9.0, t22_s + 17.8, "v2_sc05_laser_slits.mp4", 1),
        ]
    if sid == "scene06":
        ch24 = _find_chunk(scene, "chunk_24")
        t24 = ch24["local_start"] if ch24 else 18.0
        return [
            (0.0, 9.2, "scene06_silk_tablecloth.mp4", 1),
            (t24 + 17.5, t24 + 27.0, "v2_sc06_starlight_bend.mp4", 1),
        ]
    if sid == "scene07":
        ch26 = _find_chunk(scene, "chunk_26")
        t26 = ch26["local_start"] if ch26 else 17.5
        # Keep the entire `chunk_27` Sagan galaxy-suburbs sweep on our custom 3D Banked Bowl + Hero Stars GPU model!
        return [
            (t26 + 0.2, t26 + 9.4, "scene07_campfire_to_galaxy.mp4", 1),
        ]
    if sid == "scene08":
        ch29 = _find_chunk(scene, "chunk_29")
        t29 = ch29["local_start"] if ch29 else 30.0
        # Keep 100% of Act 8A (`0 .. t29`, protogalaxy gathering & tucking pleat + 4.2s showcase) on pure 3D GPU!
        return [
            (t29 + 0.5, t29 + 9.2, "scene08_pleat_collision.mp4", 1),
        ]
    if sid == "scene09":
        ch32 = _find_chunk(scene, "chunk_32")
        ch33 = _find_chunk(scene, "chunk_33")
        t32_e = ch32["local_end"] if ch32 else 42.5
        t33_s = ch33["local_start"] if ch33 else 52.1
        return [
            (0.0, 8.8, "scene09_braids_to_cosmos.mp4", 1),
            # During the second half of the 9.6-second wordless multi-galaxy cosmic zoom-out pause,
            # cross-dissolve seamlessly from our 175-galaxy 3D deep field into the 1080p Omni deep-field pullback!
            (t32_e + 3.4, t33_s - 0.5, "v3_sc09_deep_field_galaxies_zoom.mp4", -1),
        ]
    return []


def _draw_callout_pill(
    frame: np.ndarray,
    kicker: str,
    headline: str,
    detail: str,
    accent: Tuple[int, int, int],
    vis: float,
    x_right: int = 54,
    y_top: int = 108,
    cw: int = 560,
) -> None:
    if vis <= 0.01:
        return
    ch = 144 if detail else 108
    ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    dr.rounded_rectangle(
        (0, 0, cw - 1, ch - 1),
        radius=18,
        fill=(8, 15, 29, int(214 * vis)),
        outline=(*accent, int(155 * vis)),
        width=2,
    )
    dr.rounded_rectangle((18, 18, 24, ch - 18), radius=3, fill=(*accent, int(255 * vis)))
    dr.text((38, 16), kicker, font=FONTS["hud_hdr"], fill=(*accent, int(255 * vis)))
    dr.text((38, 50), headline, font=FONTS["hud_body"], fill=(246, 250, 255, int(255 * vis)))
    if detail:
        dr.text((38, 92), detail, font=FONTS["hud_sm"], fill=(192, 218, 245, int(238 * vis)))
    blit_rgba_crop(frame, ov, W - cw - x_right, y_top)


def draw_contextual_hud_v3(frame: np.ndarray, scene: dict, local_t: float) -> None:
    """Chunk-locked modern glassmorphic visual callouts synchronized to every v3 spoken beat."""
    sid = scene["id"]
    dur = float(scene["duration_sec"])

    # --- SCENE 00: Physics Verification Gauntlet & Hero Title Drop ---
    if sid == "scene00":
        if 11.0 <= local_t <= 29.5:
            vis = smoothstep01((local_t - 11.0) / 0.5) * smoothstep01((29.5 - local_t) / 0.6)
            cw, ch = 470, 290
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18, fill=(8, 15, 30, int(205 * vis)), outline=(100, 210, 255, int(130 * vis)), width=2)
            dr.text((24, 18), "COMPUTATIONAL & DATA GAUNTLET", font=FONTS["hud_hdr"], fill=(255, 208, 102, int(250 * vis)))
            items = [
                (14.2, "SymPy  •  Symbolic Tensor Algebra"),
                (16.8, "SciPy  •  Relativistic ODE / PDE Sims"),
                (20.0, "JWST  •  Early Deep-Field Galaxies"),
                (23.0, "Planck  •  Cosmic Sky Harmonic Maps"),
                (25.4, "SPARC  •  175 Galaxy Rotation Curves"),
            ]
            for idx, (t_on, label) in enumerate(items):
                lit = smoothstep01((local_t - t_on) / 0.45)
                yy = 58 + idx * 43
                dot_c = (105, 240, 195, int(255 * vis)) if lit > 0.2 else (95, 115, 145, int(160 * vis))
                txt_c = (245, 250, 255, int((135 + 120 * lit) * vis))
                dr.ellipse((24, yy + 7, 36, yy + 19), fill=dot_c)
                dr.text((48, yy), label, font=FONTS["hud_body"], fill=txt_c)
            blit_rgba_crop(frame, ov, W - cw - 54, 110)

        ch03 = _find_chunk(scene, "chunk_03")
        t_hero = (ch03["local_end"] - 10.2) if ch03 else (dur - 12.4)
        if local_t >= t_hero:
            vis = smoothstep01((local_t - t_hero) / 0.65) * smoothstep01((dur - 0.3 - local_t) / 0.65)
            cw, ch = 1420, 204
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=24, fill=(7, 13, 26, int(218 * vis)), outline=(255, 208, 105, int(170 * vis)), width=2)
            for txt, fnt, yy, col in (
                ("EPISODE 0  •  FLAGSHIP VISUAL INTRODUCTION", FONTS["hero_kicker"], 24, (108, 220, 255, int(255 * vis))),
                ("THE UNIVERSE INSIDE OUT", FONTS["hero_title"], 58, (250, 252, 255, int(255 * vis))),
                ("A Visual Guide to the Stretched Fabric & the Upside-Down Cosmic Hourglass", FONTS["hero_sub"], 136, (255, 212, 118, int(255 * vis))),
            ):
                bb = dr.textbbox((0, 0), txt, font=fnt)
                dr.text(((cw - (bb[2] - bb[0])) // 2, yy), txt, font=fnt, fill=col)
            blit_rgba_crop(frame, ov, (W - cw) // 2, 390)

    # --- SCENE 01: Textbook Lambda-CDM 95% Invisible Breakdown HUD ---
    elif sid == "scene01":
        ch07 = _find_chunk(scene, "chunk_07")
        ch08 = _find_chunk(scene, "chunk_08")
        t_on0 = ch07["local_start"] if ch07 else 66.0
        t_off = (ch08["local_end"] - 9.0) if ch08 else (dur - 11.0)
        if t_on0 <= local_t <= t_off:
            vis = smoothstep01((local_t - t_on0) / 0.6) * smoothstep01((t_off - local_t) / 0.6)
            cw, ch = 480, 255
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18, fill=(8, 14, 28, int(210 * vis)), outline=(165, 120, 255, int(150 * vis)), width=2)
            dr.text((24, 18), "TEXTBOOK LAMBDA-CDM RECIPE", font=FONTS["hud_hdr"], fill=(195, 165, 255, int(255 * vis)))
            bars = [
                ("Visible Stars & Atoms", 0.05, "5%", (95, 220, 255), t_on0 + 1.0),
                ("Cold Dark Matter (Glue)", 0.27, "27%", (168, 105, 255), t_on0 + 6.5),
                ("Lambda Dark Energy (Push)", 0.68, "68%", (255, 92, 122), t_on0 + 15.5),
            ]
            for i, (lbl, frac, pct, col, t_b) in enumerate(bars):
                grow = smoothstep01((local_t - t_b) / 1.1)
                yy = 58 + i * 54
                dr.text((24, yy), lbl, font=FONTS["hud_sm"], fill=(228, 236, 248, int(245 * vis)))
                dr.text((cw - 72, yy), pct, font=FONTS["hud_sm"], fill=(*col, int(255 * vis)))
                dr.rounded_rectangle((24, yy + 26, cw - 24, yy + 38), radius=6, fill=(28, 36, 56, int(200 * vis)))
                bw = max(12, int((cw - 48) * frac * grow))
                dr.rounded_rectangle((24, yy + 26, 24 + bw, yy + 38), radius=6, fill=(*col, int(245 * vis)))
            if local_t >= t_on0 + 23.0:
                p95 = smoothstep01((local_t - (t_on0 + 23.0)) / 0.5)
                dr.text((24, 218), "95% OF REALITY UNSEEN IN LABS", font=FONTS["hud_hdr"], fill=(255, 206, 98, int(255 * vis * p95)))
            blit_rgba_crop(frame, ov, W - cw - 54, 110)

    # --- SCENE 03: Active Open Question Badge (`chunk_14`) ---
    elif sid == "scene03":
        ch14 = _find_chunk(scene, "chunk_14")
        t14 = ch14["local_start"] if ch14 else 43.0
        if t14 <= local_t <= dur - 1.5:
            vis = smoothstep01((local_t - t14) / 0.55) * smoothstep01((dur - 1.5 - local_t) / 0.55)
            _draw_callout_pill(
                frame,
                "ACTIVE OPEN QUESTION",
                "Possible Thermodynamic Memory Arrow",
                "Neater Past Groove   →   Messier Ink-Spread Lock-In",
                (255, 208, 102),
                vis,
                cw=555,
            )

    # --- SCENE 04: Smooth Soap-Film Throat Matter vs. Antimatter Sorter (`chunk_18`) ---
    elif sid == "scene04":
        ch18 = _find_chunk(scene, "chunk_18")
        if ch18 and ch18["local_start"] + 8.0 <= local_t <= ch18["local_end"] + 1.2:
            vis = smoothstep01((local_t - (ch18["local_start"] + 8.0)) / 0.6) * smoothstep01((ch18["local_end"] + 1.2 - local_t) / 0.6)
            _draw_callout_pill(
                frame,
                "SMOOTH SOAP-FILM THROAT SORTER",
                "Zero Fabric Tear at Central Waist",
                "Sapphire Half: Ordinary Matter   •   Opposite Side: Antimatter",
                (112, 222, 255),
                vis,
                cw=590,
            )

    # --- SCENE 05: Tiny Singularity Zoom, Blocked Sky Waves, Hubble+JWST & Double-Slit Sensor ---
    elif sid == "scene05":
        ch20 = _find_chunk(scene, "chunk_20")
        ch21 = _find_chunk(scene, "chunk_21")
        ch22 = _find_chunk(scene, "chunk_22")
        if ch20 and ch21 and ch22:
            t20_e = ch20["local_end"]
            t21_s, t21_e = ch21["local_start"], ch21["local_end"]
            t22_s, t22_e = ch22["local_start"], ch22["local_end"]
            t_tel = t21_s + 0.56 * (t21_e - t21_s)

            # 1) Tiny Singularity Ring Macro Zoom Badge (`t20_e - 7.0 .. t20_e + 2.2`)
            if t20_e - 7.0 <= local_t <= t20_e + 2.2:
                vis = smoothstep01((local_t - (t20_e - 7.0)) / 0.55) * smoothstep01((t20_e + 2.2 - local_t) / 0.55)
                _draw_callout_pill(
                    frame,
                    "MACRO ZOOM  •  TINY INNER RING",
                    "Pinched Big Bang Singularity Throat",
                    "Soap Film Held Simultaneously by Giant Rim & Tiny Pinpoint Ring",
                    (255, 212, 108),
                    vis,
                    cw=610,
                )
            # 2) Wave Cutoff Comparison (`t21_s + 1.0 .. t_tel - 0.4`)
            elif t21_s + 1.0 <= local_t <= t_tel - 0.4:
                vis = smoothstep01((local_t - (t21_s + 1.0)) / 0.55) * smoothstep01((t_tel - 0.4 - local_t) / 0.55)
                _draw_callout_pill(
                    frame,
                    "PRIMORDIAL SOUND & HEAT WAVE CUTOFF",
                    "Red Arch: Ultra-Wide Sky Wave Blocked by Throat",
                    "Cyan Ripples: Shorter Primordial Waves Fit Cleanly on Sheet",
                    (255, 118, 132),
                    vis,
                    cw=605,
                )
            # 3) Planck, Hubble & JWST Mapping the Oldest Light (`t_tel + 0.4 .. t21_e + 1.8`)
            elif t_tel + 0.4 <= local_t <= t21_e + 1.8:
                vis = smoothstep01((local_t - (t_tel + 0.4)) / 0.55) * smoothstep01((t21_e + 1.8 - local_t) / 0.55)
                _draw_callout_pill(
                    frame,
                    "PLANCK  •  HUBBLE  •  JAMES WEBB",
                    "Mapping the Oldest Light Across Deep Space",
                    "Observed Sky Anomaly: Widest Temperature Ripples Missing",
                    (108, 224, 255),
                    vis,
                    cw=595,
                )
            # 4) Chilled-Out Double-Slit Experiment (`t22_s + 2.0 .. t22_e - 3.5`)
            elif t22_s + 2.0 <= local_t <= t22_e - 3.5:
                vis = smoothstep01((local_t - (t22_s + 2.0)) / 0.6) * smoothstep01((t22_e - 3.5 - local_t) / 0.6)
                u22 = (local_t - t22_s) / max(1.0, t22_e - t22_s)
                if u22 < 0.50:
                    _draw_callout_pill(
                        frame,
                        "DOUBLE SLIT  •  BOTH OPENINGS UNBLOCKED",
                        "Connected Fabric Carries Wave Through Both Slits",
                        "Two Wave Paths Overlap  →  Bright & Dark Interference Stripes",
                        (92, 244, 196),
                        vis,
                        cw=615,
                    )
                else:
                    _draw_callout_pill(
                        frame,
                        "WHICH-WAY SENSOR PLACED AT SLIT 1",
                        "Sensor Absorbs Wave Like a Finger on a Guitar String",
                        "No Second Wave Left to Overlap  →  Stripes Vanish Automatically",
                        (255, 196, 92),
                        vis,
                        cw=630,
                    )

    # --- SCENE 07: Solar Campfire Funnel vs. Live Galaxy Outer-Star Speeds & Tangent Escape HUD ---
    elif sid == "scene07":
        ch26 = _find_chunk(scene, "chunk_26")
        ch27 = _find_chunk(scene, "chunk_27")
        if ch26 and ch26["local_start"] + 12.0 <= local_t <= ch26["local_end"] + 1.2:
            vis = smoothstep01((local_t - (ch26["local_start"] + 12.0)) / 0.55) * smoothstep01((ch26["local_end"] + 1.2 - local_t) / 0.55)
            _draw_callout_pill(
                frame,
                "SOLAR SYSTEM  •  LOCAL CAMPFIRE GRAVITY",
                "Sun's Steep Funnel = 50,000,000x Deep-Space Tension",
                "Local Slope Completely Dominates Nearby Planetary Orbits",
                (255, 198, 92),
                vis,
                cw=605,
            )
        elif ch27 and ch27["local_start"] + 1.5 <= local_t <= dur - 1.2:
            t_g0 = ch27["local_start"] + 1.5
            vis = smoothstep01((local_t - t_g0) / 0.6) * smoothstep01((dur - 1.2 - local_t) / 0.6)
            cw, ch = 536, 282
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18, fill=(8, 15, 28, int(216 * vis)), outline=(85, 238, 190, int(155 * vis)), width=2)
            dr.text((24, 16), "WHY OUTER STARS AREN'T FLUNG OFF", font=FONTS["hud_hdr"], fill=(98, 242, 198, int(255 * vis)))

            gx0, gy0, gx1, gy1 = 48, 58, cw - 30, 188
            dr.line((gx0, gy1, gx1, gy1), fill=(140, 165, 198, int(200 * vis)), width=2)
            dr.line((gx0, gy0, gx0, gy1), fill=(140, 165, 198, int(200 * vis)), width=2)

            reveal = smoothstep01((local_t - (t_g0 + 1.0)) / 3.5)
            n_pts = max(3, int(60 * reveal))
            pts_flat, pts_kep = [], []
            for k in range(n_pts):
                r = 0.08 + 4.8 * (k / 59.0)
                px = int(gx0 + (gx1 - gx0) * (k / 59.0))
                v_kep = (r / 0.75) * math.exp(1.0 - r / 0.75) if r < 0.75 else (0.75 / r) ** 0.5
                v_flt = 1.0 - math.exp(-r / 0.55)
                pts_kep.append((px, int(gy1 - (gy1 - gy0 - 14) * min(1.05, v_kep * 0.92))))
                pts_flat.append((px, int(gy1 - (gy1 - gy0 - 14) * (0.94 * v_flt))))

            for k in range(0, len(pts_kep) - 1, 2):
                dr.line((pts_kep[k], pts_kep[k + 1]), fill=(255, 102, 118, int(205 * vis)), width=3)
            if len(pts_flat) >= 2:
                dr.line(pts_flat, fill=(82, 245, 192, int(255 * vis)), width=4)

            dr.text((24, 200), "Emerald Bowl: Taut Cloth Curves Fast Stars Inward", font=FONTS["hud_sm"], fill=(95, 245, 195, int(250 * vis)))
            dr.text((24, 226), "Red Tangent:  Flung Into Space Without Fabric Tension", font=FONTS["hud_sm"], fill=(255, 122, 134, int(240 * vis)))
            dr.text((24, 251), "Zero Invisible Dark-Matter Particles Needed", font=FONTS["hud_sm"], fill=(210, 226, 248, int(225 * vis)))
            blit_rgba_crop(frame, ov, W - cw - 54, 108)

    # --- SCENE 08: Protogalaxy Pleat-Tuck Showcase (`chunk_28` + 4.2s pause) ---
    elif sid == "scene08":
        ch28 = _find_chunk(scene, "chunk_28")
        ch29 = _find_chunk(scene, "chunk_29")
        t29_s = ch29["local_start"] if ch29 else 30.0
        if ch28 and 8.0 <= local_t <= t29_s - 0.6:
            vis = smoothstep01((local_t - 8.0) / 0.6) * smoothstep01((t29_s - 0.6 - local_t) / 0.6)
            _draw_callout_pill(
                frame,
                "NEWBORN GALAXY  •  FABRIC PLEAT FOLDING",
                "Condensing Stars Gather & Tuck Excess Sheet Inward",
                "Creates a Crisp, Springy Circumferential Tension Pleat",
                (108, 224, 255),
                vis,
                cw=605,
            )

    # --- SCENE 09: Keep Sagan Outro + 9.6s Galaxy Zoom 100% Uncluttered; Show Chapters ONLY in `chunk_33`! ---
    elif sid == "scene09":
        ch33 = _find_chunk(scene, "chunk_33")
        t33_s = ch33["local_start"] if ch33 else 52.0
        if local_t >= t33_s + 3.5:
            vis = smoothstep01((local_t - (t33_s + 3.5)) / 0.6) * smoothstep01((dur - 1.5 - local_t) / 0.8)
            cw, ch = 540, 324
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18, fill=(8, 14, 28, int(216 * vis)), outline=(105, 215, 255, int(155 * vis)), width=2)
            dr.text((24, 18), "UP NEXT  •  6 HARD-SCIENCE CHAPTERS", font=FONTS["hud_hdr"], fill=(255, 210, 104, int(255 * vis)))
            chapters = [
                "Ch. 1  •  Timeless Groove & GPS Clocks",
                "Ch. 2  •  Flipped Cosmic Hourglass & Sky Maps",
                "Ch. 3  •  Two-Ended Grip & Double-Slit Lab",
                "Ch. 4  •  175 Galaxies Without Dark Matter",
                "Ch. 5  •  Bullet Cluster & Dwarf Bounces",
                "Ch. 6  •  Atom Braids & Moon-Orbit Crucible",
            ]
            for idx, ch_txt in enumerate(chapters):
                lit = smoothstep01((local_t - (t33_s + 4.8 + idx * 2.5)) / 0.5)
                yy = 58 + idx * 42
                dr.rounded_rectangle((22, yy, cw - 22, yy + 34), radius=9, fill=(18, 32, 56, int((90 + 110 * lit) * vis)))
                dr.text((36, yy + 5), ch_txt, font=FONTS["hud_sm"], fill=(242, 248, 255, int((130 + 125 * lit) * vis)))
            blit_rgba_crop(frame, ov, W - cw - 54, 108)


def compose_frame_v3(
    director: GPU3DSceneDirectorV3,
    clip_cache: CinemaClipCache,
    scene: dict,
    local_t: float,
) -> np.ndarray:
    sid = scene["id"]
    dur = float(scene["duration_sec"])

    broll_rgb: Optional[np.ndarray] = None
    broll_alpha = 0.0
    xf = 0.65

    for w0, w1, cname, zdir in get_v3_broll_windows(scene):
        if w0 - xf <= local_t <= w1 + xf:
            f_in = 1.0 if (w0 == 0.0 and local_t < xf) else smoothstep01((local_t - (w0 - xf)) / (2.0 * xf))
            f_out = smoothstep01(((w1 + xf) - local_t) / (2.0 * xf))
            broll_alpha = max(0.0, min(1.0, f_in * f_out))
            if broll_alpha > 0.01:
                broll_rgb = clip_cache.get_frame(cname, max(0.0, local_t - w0), w1 - w0, zoom_dir=zdir)
            break

    if broll_rgb is not None and broll_alpha >= 0.995:
        frame = broll_rgb
    elif broll_rgb is not None and broll_alpha > 0.01:
        gpu_rgb = director.render_scene_frame_v3(scene, local_t)
        a_u16 = int(round(broll_alpha * 256))
        frame = ((broll_rgb.astype(np.uint16) * a_u16 + gpu_rgb.astype(np.uint16) * (256 - a_u16)) >> 8).astype(np.uint8)
    else:
        frame = director.render_scene_frame_v3(scene, local_t)

    if sid == "hook00":
        draw_cold_open_hook_cards(frame, local_t)
    else:
        # During Scene 09's 9.6s wordless Sagan multi-galaxy cosmic zoom-out, hide even the top-left watermark
        # so the viewer gets 100% pure, breathtaking widescreen cosmic wonder!
        ch32 = _find_chunk(scene, "chunk_32") if sid == "scene09" else None
        ch33 = _find_chunk(scene, "chunk_33") if sid == "scene09" else None
        in_sagan_interlude = bool(
            ch32 and ch33 and (ch32["local_end"] + 0.3 <= local_t <= ch33["local_start"] - 0.3)
        )
        if not in_sagan_interlude:
            draw_chapter_lower_third_and_watermark(frame, scene, local_t, dur)
        draw_contextual_hud_v3(frame, scene, local_t)
        draw_verbatim_subtitle(frame, scene["cues"], local_t)

    # Gentle 2.0s fade-to-black on the final musical tail!
    if sid == "scene09" and local_t > dur - 2.0:
        fade_blk = max(0.0, min(1.0, (dur - local_t) / 2.0))
        frame = (frame.astype(np.float32) * fade_blk).astype(np.uint8)

    return frame


def main() -> None:
    qa_only = "--qa-only" in sys.argv
    t0 = time.time()
    manifest = json.loads(MANIFEST_V3_PATH.read_text(encoding="utf-8"))
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    director = GPU3DSceneDirectorV3()
    clip_cache = CinemaClipCache(ffmpeg_exe)

    if qa_only:
        qa_dir = EP0_DIR / "v3_qa_frames"
        qa_dir.mkdir(exist_ok=True)
        sc_map = {s["id"]: s for s in manifest["scenes"]}

        sc05 = sc_map["scene05"]
        ch20 = _find_chunk(sc05, "chunk_20")
        ch21 = _find_chunk(sc05, "chunk_21")
        ch22 = _find_chunk(sc05, "chunk_22")

        sc07 = sc_map["scene07"]
        ch26 = _find_chunk(sc07, "chunk_26")
        ch27 = _find_chunk(sc07, "chunk_27")

        sc08 = sc_map["scene08"]
        ch28 = _find_chunk(sc08, "chunk_28")

        sc09 = sc_map["scene09"]
        ch32 = _find_chunk(sc09, "chunk_32")

        checks = [
            ("v3_01_soap_dip_stretch", "scene05", ch20["local_start"] + 16.5),
            ("v3_02_tiny_singularity_zoom", "scene05", ch20["local_end"] - 1.5),
            ("v3_03_blocked_sky_wave", "scene05", ch21["local_start"] + 10.0),
            ("v3_04_hubble_jwst_cmb_3d", "scene05", ch21["local_start"] + 26.5),
            ("v3_05_doubleslit_sensor", "scene05", ch22["local_start"] + 38.0),
            ("v3_06_solar_campfire_funnel", "scene07", ch26["local_start"] + 24.0),
            ("v3_07_galaxy_tangent_vs_bowl", "scene07", ch27["local_start"] + 18.0),
            ("v3_08_protogalaxy_pleat_tuck", "scene08", ch28["local_end"] + 2.0),
            ("v3_09_sagan_175_galaxies_zoom", "scene09", ch32["local_end"] + 2.2),
        ]
        for tag, sid, lt in checks:
            fr = compose_frame_v3(director, clip_cache, sc_map[sid], lt)
            out_p = qa_dir / f"{tag}.jpg"
            Image.fromarray(fr).save(out_p, quality=93)
            shutil.copy2(str(out_p), str(ARTIFACT_DIR / out_p.name))
            print(f"[V3 QA Frame Saved] {out_p.name} ({sid} @ {lt:.1f}s)", flush=True)
        return

    assert MASTER_WAV_V3.exists(), f"Missing {MASTER_WAV_V3}"
    total_sec = float(manifest["total_duration_sec"])
    total_frames = int(round(total_sec * FPS))

    nv_probe = subprocess.run(
        [ffmpeg_exe, "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.05", "-c:v", "h264_nvenc", "-f", "null", "-"],
        capture_output=True,
    )
    use_nvenc = nv_probe.returncode == 0
    v_codec_args = (
        ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19", "-b:v", "0"]
        if use_nvenc
        else ["-c:v", "libx264", "-preset", "fast", "-crf", "18"]
    )
    print(
        f"[V3 Encoder] Rendering {total_frames} frames ({total_sec/60:.2f} min @ 1920x1080 24fps) via "
        f"{'NVENC RTX 5080' if use_nvenc else 'libx264'}...",
        flush=True,
    )

    tmp_mp4 = EP0_DIR / "_tmp_ep0_v3_render.mp4"
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(MASTER_WAV_V3),
        *v_codec_args,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "224k",
        "-shortest",
        "-movflags", "+faststart",
        str(tmp_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert proc.stdin is not None

    scenes = manifest["scenes"]
    sc_idx = 0

    for f_idx in range(total_frames):
        gt = f_idx / FPS
        while sc_idx < len(scenes) - 1 and gt >= scenes[sc_idx]["end_sec"]:
            sc_idx += 1
        sc = scenes[sc_idx]
        lt = max(0.0, gt - sc["start_sec"])

        frame = compose_frame_v3(director, clip_cache, sc, lt)
        proc.stdin.write(frame.tobytes())

        if f_idx > 0 and f_idx % (FPS * 30) == 0:
            el = time.time() - t0
            fps_eff = f_idx / max(0.1, el)
            eta = (total_frames - f_idx) / max(0.1, fps_eff)
            print(
                f"  [{100.0*f_idx/total_frames:5.1f}%] {f_idx}/{total_frames} frames ({sc['id']}) | "
                f"{fps_eff:.1f} fps | ETA {eta:.0f}s",
                flush=True,
            )

    proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")

    shutil.move(str(tmp_mp4), str(FINAL_V3_MP4))
    shutil.copy2(str(FINAL_V3_MP4), str(FINAL_MAIN_MP4))
    shutil.copy2(str(FINAL_V3_MP4), str(ARTIFACT_MP4))
    shutil.copy2(str(FINAL_V3_MP4), str(ARTIFACT_DIR / FINAL_V3_MP4.name))
    sz_mb = FINAL_V3_MP4.stat().st_size / 1e6
    print(f"\n[V3 COMPLETE] {FINAL_V3_MP4.name} ({sz_mb:.1f} MB) in {time.time() - t0:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
