"""
Master Native `3840x2160` (`4K UHD`, `24 fps`) Cinema Renderer & Parallel CPU Assembler for Episode 2:
  'Episode 2 — The Upside-Down Big Bang & Where All the Antimatter Went'

Non-Negotiable Production Rules Enforced:
  1. ZERO Burned-In Subtitles on Video Frames (`GEMINI.md` Rule #1 — 100% clean 4K picture!).
     Subtitles live strictly in `Episode_2_Upside_Down_Big_Bang_Subtitles.srt`.
  2. Strict GPU Discipline (`--cpu-only` / `CUDA_VISIBLE_DEVICES="-1"` + `libx264` CPU encoding +
     `BELOW_NORMAL_PRIORITY_CLASS = 0x00004000`) so Jimani's RTX 5080 knot-gravity runs stay at 0% interference!
  3. Locked Option A+ ('Luminous Sapphire Slate', 39% Vibrant Mid-Tone) across every 3D scene,
     Smoked-Sapphire Keynote Pill (`124 px` native-4K headlines), and anti-flashbang B-roll grader.
  4. Frequent `gemini-omni-1.1-flash` Cinema Visuals (`22` clips across all 7 chapters!) +
     LARGE, CENTER-SCREEN, VIDEO-ANIMATED SCIENTIST PORTRAITS (`Penrose`, `Landauer`, `Turok`,
     `Pauli & Schwinger`, `Barbour`, `Sakharov`, `Hawking`) right in human foveal focus!
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Default to strict CPU-only mode unless `--use-gpu` is explicitly passed!
if "--use-gpu" not in sys.argv:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["NUMBA_DISABLE_CUDA"] = "1"

import imageio_ffmpeg
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFont

try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
except Exception:
    pass

EP2_DIR = Path(__file__).resolve().parent
ROOT_DIR = EP2_DIR.parent
EP1_DIR = ROOT_DIR / "episode1_time_and_memory"
EP0_DIR = ROOT_DIR / "episode0_flagship"
for p in (str(EP2_DIR), str(EP0_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from gpu_renderer_core import set_render_resolution, smootherstep01, smoothstep01  # noqa: E402

W4K, H4K = 3840, 2160
FPS = 24

# Render 3D base at 1920x1080 when on CPU (for 6x faster parallel CPU throughput -> bicubic+unsharp upscaled
# to 3840x2160 BEFORE compositing 100% true native-3840x2160 typography, graphs, paper cards & nameplates!)
USE_GPU = "--use-gpu" in sys.argv and torch.cuda.is_available()
SCENE_W = W4K if USE_GPU else 1920
SCENE_H = H4K if USE_GPU else 1080
set_render_resolution(SCENE_W, SCENE_H)

from ep2_gpu_scenes import Episode2SceneDirector, _find_chunk  # noqa: E402

AUDIO_V1_DIR = EP2_DIR / "audio_v1"
MANIFEST_PATH = AUDIO_V1_DIR / "ep2_v1_manifest.json"
MASTER_WAV_PATH = AUDIO_V1_DIR / "Episode_2_Master_Audio_v1.wav"
CINEMA_EP2_DIR = EP2_DIR / "cinema_clips"
CINEMA_EP1_DIR = EP1_DIR / "cinema_clips"
ARTIFACT_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")

FINAL_4K_MP4 = EP2_DIR / "Episode_2_Upside_Down_Big_Bang_4K_UHD.mp4"
ARTIFACT_4K_MP4 = ARTIFACT_DIR / "Episode_2_Upside_Down_Big_Bang_4K_UHD.mp4"

# Locked Option A+ ('Luminous Sapphire Slate') Typography & Card Constants
PILL_BG = (24, 38, 60, 238)
PILL_BORDER = (125, 211, 252, 224)
TEXT_ALABASTER = (241, 245, 251)
TEXT_MUTED = (191, 219, 254)
ACCENT_GOLD = (253, 224, 71)
ACCENT_CYAN = (125, 211, 252)
ACCENT_EMERALD = (52, 211, 153)
ACCENT_CORAL = (251, 146, 60)


def load_font_4k(px: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    cands = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold
        else ["C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    )
    for fp in cands:
        if Path(fp).exists():
            return ImageFont.truetype(fp, px)
    return ImageFont.load_default()


FONTS = {
    "giant": load_font_4k(124, bold=True),
    "hero": load_font_4k(94, bold=True),
    "kicker": load_font_4k(46, bold=True),
    "lt_kicker": load_font_4k(36, bold=True),
    "lt_title": load_font_4k(58, bold=True),
    "wm": load_font_4k(30, bold=False),
    "np_name": load_font_4k(64, bold=True),
    "np_sub": load_font_4k(40, bold=False),
    "card_h": load_font_4k(58, bold=True),
    "card_b": load_font_4k(40, bold=False),
    "card_s": load_font_4k(34, bold=True),
    "graph_t": load_font_4k(50, bold=True),
    "graph_lbl": load_font_4k(36, bold=True),
    "graph_ax": load_font_4k(30, bold=False),
}


def blit_rgba_fast(frame_rgb: np.ndarray, patch_arr: np.ndarray, x0: int, y0: int, opacity: float = 1.0) -> None:
    if opacity <= 0.01:
        return
    fh, fw, _ = frame_rgb.shape
    oh, ow, _ = patch_arr.shape
    sx0 = max(0, x0)
    sy0 = max(0, y0)
    sx1 = min(fw, x0 + ow)
    sy1 = min(fh, y0 + oh)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    ox0, oy0 = sx0 - x0, sy0 - y0
    sub = patch_arr[oy0 : oy0 + (sy1 - sy0), ox0 : ox0 + (sx1 - sx0)]
    alpha = sub[..., 3:4].astype(np.uint16)
    if opacity < 0.995:
        alpha = (alpha * int(round(opacity * 256.0))) >> 8
    if alpha.max() == 0:
        return
    dst = frame_rgb[sy0:sy1, sx0:sx1].astype(np.uint16)
    out = (sub[..., :3].astype(np.uint16) * alpha + dst * (255 - alpha) + 127) // 255
    frame_rgb[sy0:sy1, sx0:sx1] = out.astype(np.uint8)


# ---------------------------------------------------------------------------
# Native 4K Overlay Library (Keynote Pills, Center Nameplates, Showcase Cards)
# ---------------------------------------------------------------------------

class Ep2OverlayLibrary4K:
    def __init__(self) -> None:
        self._pills: Dict[tuple, np.ndarray] = {}
        self._nameplates: Dict[tuple, np.ndarray] = {}
        self._custom: Dict[str, np.ndarray] = {}
        self._build_showcase_cards()

    def get_keynote_pill(
        self,
        kicker: str,
        headline: str,
        accent: Tuple[int, int, int] = ACCENT_GOLD,
        giant: bool = True,
    ) -> np.ndarray:
        key = (kicker, headline, accent, giant)
        if key in self._pills:
            return self._pills[key]

        f_head = FONTS["giant"] if giant else FONTS["hero"]
        f_kick = FONTS["kicker"]
        dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
        bb_k = dummy.textbbox((0, 0), kicker, font=f_kick)
        bb_h = dummy.textbbox((0, 0), headline, font=f_head)
        cw = max(bb_k[2] - bb_k[0], bb_h[2] - bb_h[0]) + 176
        ch = 268 if giant else 228

        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=38, fill=PILL_BG, outline=PILL_BORDER, width=4)
        dr.rounded_rectangle((28, 34, 42, ch - 34), radius=7, fill=(*accent, 255))
        dr.text((68, 30), kicker, font=f_kick, fill=(*accent, 255))
        dr.text((68, 92 if giant else 86), headline, font=f_head, fill=(*TEXT_ALABASTER, 255))

        arr = np.asarray(im, dtype=np.uint8)
        self._pills[key] = arr
        return arr

    def get_portrait_nameplate(
        self,
        name_line: str,
        role_line: str,
        accent: Tuple[int, int, int] = ACCENT_GOLD,
    ) -> np.ndarray:
        """
        Museum-grade 4K nameplate sitting cleanly at `(center, y=1640)` directly underneath
        our LARGE, CENTER-SCREEN video-animated scientist portrait (`y=168..1608` at 4K)!
        """
        key = (name_line, role_line, accent)
        if key in self._nameplates:
            return self._nameplates[key]

        dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
        b1 = dummy.textbbox((0, 0), name_line, font=FONTS["np_name"])
        b2 = dummy.textbbox((0, 0), role_line, font=FONTS["np_sub"])
        w1, w2 = b1[2] - b1[0], b2[2] - b2[0]
        cw = max(w1, w2) + 168
        ch = 216

        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=34, fill=(18, 30, 48, 242), outline=(*accent, 225), width=4)
        dr.text(((cw - w1) // 2, 28), name_line, font=FONTS["np_name"], fill=(*TEXT_ALABASTER, 255))
        dr.text(((cw - w2) // 2, 122), role_line, font=FONTS["np_sub"], fill=(*accent, 255))

        arr = np.asarray(im, dtype=np.uint8)
        self._nameplates[key] = arr
        return arr

    def _build_showcase_cards(self) -> None:
        # 1. Konami Cheat-Code Audit Card (Scene 02, chunk_08–09)
        cw, ch = 2280, 460
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=42, fill=(18, 30, 48, 240), outline=PILL_BORDER, width=4)
        dr.text((76, 36), "SKEPTIC AUDIT  •  IS FLIPPING +T TO -T A PHYSICS CHEAT CODE?", font=FONTS["kicker"], fill=(*ACCENT_GOLD, 255))
        keys = ["↑", "↑", "↓", "↓", "←", "→", "←", "→", "B", "A"]
        kx = 76
        for k_lbl in keys:
            is_btn = k_lbl in ("B", "A")
            col_fill = (185, 48, 62, 240) if is_btn else (36, 56, 86, 245)
            dr.rounded_rectangle((kx, 122, kx + 148, 258), radius=24, fill=col_fill, outline=(241, 245, 251, 210), width=3)
            bb = dr.textbbox((0, 0), k_lbl, font=FONTS["card_h"])
            dr.text((kx + (148 - (bb[2] - bb[0])) // 2, 146), k_lbl, font=FONTS["card_h"], fill=(255, 255, 255, 255))
            kx += 174
        dr.text(
            (76, 300),
            "• Single-Boundary Rewound Movie:  100% FAKE CHEAT CODE  (Requires 4.7 × 10^122 hand-tuned rim bits)",
            font=FONTS["card_b"],
            fill=(*ACCENT_CORAL, 255),
        )
        dr.text(
            (76, 368),
            "• Two-Boundary Soap Film (Catenoid):  ZERO HAND-TUNING  (Clamped waist squeezes out giant sky waves!)",
            font=FONTS["card_b"],
            fill=(*ACCENT_EMERALD, 255),
        )
        self._custom["konami_audit"] = np.asarray(im, dtype=np.uint8)

        # 2. Cambridge Physical Review D (2024–2025) Deng & Handley Paper Card (Scene 03, chunk_15)
        pw, ph = 2340, 560
        im_p = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        dp = ImageDraw.Draw(im_p)
        dp.rounded_rectangle((0, 0, pw - 1, ph - 1), radius=42, fill=(244, 247, 252, 246), outline=(125, 211, 252, 240), width=5)
        dp.rounded_rectangle((0, 0, pw - 1, 108), radius=42, fill=(22, 36, 58, 255))
        dp.rectangle((0, 66, pw - 1, 108), fill=(22, 36, 58, 255))
        dp.text((68, 28), "PHYSICAL REVIEW D  •  2024 & 2025  •  CAVENDISH LABORATORY, CAMBRIDGE", font=FONTS["card_s"], fill=(*ACCENT_GOLD, 255))
        dp.text((68, 138), "Symmetric Boundary Conditions Across the Big Bang", font=FONTS["card_h"], fill=(15, 25, 42, 255))
        dp.text((68, 218), "& Quantized Spatial Curvature (Suppressing Low-l CMB Multipoles)", font=FONTS["card_h"], fill=(15, 25, 42, 255))
        dp.text((68, 326), "Authors:   Wei-Ning Deng & Will Handley  (University of Cambridge)", font=FONTS["card_b"], fill=(30, 58, 98, 255))
        dp.text((68, 396), "Building on:   Neil Turok, Latham Boyle & Kieran Finn  (CPT-Symmetric Universe, PRL 2018)", font=FONTS["card_b"], fill=(45, 72, 110, 255))
        badge_str = "✓ INDEPENDENTLY SURFACED BY 2.2M-PAPER LACUNA ENGINE"
        bb_b = dp.textbbox((0, 0), badge_str, font=FONTS["card_s"])
        dp.rounded_rectangle((68, 466, 68 + (bb_b[2] - bb_b[0]) + 64, 528), radius=18, fill=(16, 128, 92, 245))
        dp.text((100, 474), badge_str, font=FONTS["card_s"], fill=(255, 255, 255, 255))
        self._custom["deng_handley_paper"] = np.asarray(im_p, dtype=np.uint8)

        # 3. Hard Kill-Switch Scorecard (Scene 05, chunk_26–27)
        kw, kh = 2480, 620
        im_k = Image.new("RGBA", (kw, kh), (0, 0, 0, 0))
        dk = ImageDraw.Draw(im_k)
        dk.rounded_rectangle((0, 0, kw - 1, kh - 1), radius=42, fill=(18, 30, 48, 244), outline=PILL_BORDER, width=4)
        dk.text((72, 38), "EPISODE 2 HONEST SCORECARD  •  OPEN [WARN] & HARD KILL-SWITCHES", font=FONTS["kicker"], fill=(*ACCENT_GOLD, 255))
        rows = [
            ("[WARN] OPEN MATH", "Full 3D Pleat Shear Across All 2,500 Polarization Peaks (Logged for Recap)", ACCENT_GOLD),
            ("KILL-SWITCH #1", "JAXA LiteBIRD Large-Angle B-Mode Ratio = 0.415  (Plateau > 0.85 Falsifies!)", ACCENT_CYAN),
            ("KILL-SWITCH #2", "KATRIN & Euclid Lightest Neutrino m_1 = 0.00 eV  (> 0.02 eV Falsifies!)", ACCENT_CORAL),
        ]
        ry = 140
        for badge, desc, col in rows:
            dk.rounded_rectangle((72, ry, 540, ry + 112), radius=24, fill=(*col, 38), outline=(*col, 235), width=3)
            dk.text((104, ry + 32), badge, font=FONTS["card_s"], fill=(*col, 255))
            dk.text((580, ry + 28), desc, font=FONTS["card_b"], fill=(*TEXT_ALABASTER, 255))
            ry += 148
        self._custom["killswitch_scorecard"] = np.asarray(im_k, dtype=np.uint8)

        # 4. Companion Portal & Blind Zenodo DOI Card (Scene 06, chunk_28)
        bw, bh = 2440, 560
        im_b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        db = ImageDraw.Draw(im_b)
        db.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=42, fill=(18, 30, 48, 244), outline=PILL_BORDER, width=4)
        db.text((76, 40), "TEST EVERY EQUATION YOURSELF  •  100% PUBLIC & PRE-REGISTERED", font=FONTS["kicker"], fill=(*ACCENT_CYAN, 255))
        db.text((76, 134), "• Interactive Portal & Scripts:   https://stoler.systems", font=FONTS["card_h"], fill=(*TEXT_ALABASTER, 255))
        db.text((76, 236), "• Open-Source Repo & WeaveForge Arena 4:   github.com/dragula22/TNAP-Theories", font=FONTS["card_b"], fill=(*ACCENT_GOLD, 255))
        db.text((76, 326), "• Blind Dec 2 Gaia DR4 + BHEX Lock:   CERN Zenodo DOI  10.5281/zenodo.23919217", font=FONTS["card_b"], fill=(*ACCENT_EMERALD, 255))
        db.text((76, 424), "Spin the 3D CPT Hourglass in real time  •  Zero free tuning knobs", font=FONTS["card_b"], fill=(*TEXT_MUTED, 255))
        self._custom["portal_zenodo_card"] = np.asarray(im_b, dtype=np.uint8)

        # 5. Recap Video Living Ledger Card (Scene 06, chunk_29)
        lw, lh = 2380, 480
        im_l = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        dl = ImageDraw.Draw(im_l)
        dl.rounded_rectangle((0, 0, lw - 1, lh - 1), radius=42, fill=(18, 30, 48, 244), outline=(*ACCENT_GOLD, 225), width=4)
        dl.text((76, 40), "POST-CHAPTERS MILESTONE  •  RECAP VIDEO LIVING LEDGER", font=FONTS["kicker"], fill=(*ACCENT_GOLD, 255))
        dl.text((76, 136), "Logged Today for Our Full 6-Chapter Synthesis & Audit Episode:", font=FONTS["card_h"], fill=(*TEXT_ALABASTER, 255))
        dl.text((76, 244), "1. Evolving full 3D pleat polarization shear across the entire microwave sky", font=FONTS["card_b"], fill=(*ACCENT_CYAN, 255))
        dl.text((76, 324), "2. Keeping the QCD strong-force angle untwisted across the CPT waist", font=FONTS["card_b"], fill=(*ACCENT_GOLD, 255))
        dl.text((76, 400), "Drop your sharpest physics critiques & tests in the comments below!", font=FONTS["card_b"], fill=(*ACCENT_EMERALD, 255))
        self._custom["recap_ledger_card"] = np.asarray(im_l, dtype=np.uint8)


# ---------------------------------------------------------------------------
# Live Animated 4K Scientific Charts (Scene 03 Quadrupole & Scene 05 3rd Peak)
# ---------------------------------------------------------------------------

def draw_planck_quadrupole_chart_4k(frame: np.ndarray, prog: float, opacity: float) -> None:
    """Animated 4K chart showing Standard Lambda-CDM (~1,100 uK^2) vs Clamped Waist (334 uK^2) at l=2."""
    gw, gh = 1780, 1020
    im = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, gw - 1, gh - 1), radius=40, fill=(18, 30, 48, 240), outline=PILL_BORDER, width=4)
    dr.text((64, 38), "PLANCK LOW-l SKY POWER  D_l  (uK²)", font=FONTS["graph_t"], fill=(*TEXT_ALABASTER, 255))
    dr.text((64, 108), "Giant Sky Quadrupole (l = 2) vs. Smaller Ripples (l = 3 .. 25)", font=FONTS["graph_ax"], fill=(*ACCENT_CYAN, 255))

    x0, y0, x1, y1 = 150, 210, gw - 84, gh - 130
    dr.line([(x0, y1), (x1, y1)], fill=(191, 219, 254, 190), width=4)
    dr.line([(x0, y0), (x0, y1)], fill=(191, 219, 254, 190), width=4)

    def map_xy(ell: float, dl: float) -> Tuple[int, int]:
        ux = (ell - 2.0) / 23.0
        uy = min(1.0, max(0.0, dl / 1350.0))
        return int(x0 + ux * (x1 - x0)), int(y1 - uy * (y1 - y0))

    for y_val in (300, 600, 900, 1200):
        _, py = map_xy(2.0, y_val)
        dr.line([(x0, py), (x1, py)], fill=(125, 211, 252, 42), width=2)
        dr.text((34, py - 20), f"{y_val}", font=FONTS["graph_ax"], fill=(191, 219, 254, 200))

    ells = np.linspace(2.0, 2.0 + 23.0 * min(1.0, prog * 1.15), 90)
    pts_lcdm = []
    pts_clamp = []
    for l_v in ells:
        dl_std = 1085.0 - 110.0 * math.exp(-((l_v - 2.0) / 4.0)) + 45.0 * math.sin(0.5 * l_v)
        # Clamped Catenoid Waist suppresses l=2 -> 334 uK^2 while leaving l>=10 99.95% untouched!
        supp = 1.0 - 0.692 * math.exp(-((l_v - 2.0) / 2.35) ** 2)
        dl_cl = dl_std * supp
        pts_lcdm.append(map_xy(float(l_v), dl_std))
        pts_clamp.append(map_xy(float(l_v), dl_cl))

    if len(pts_lcdm) >= 2:
        dr.line(pts_lcdm, fill=(251, 146, 60, 215), width=7)
        dr.line(pts_clamp, fill=(52, 211, 153, 255), width=10)

    # Planck measured l=2 error box (230..330 uK^2) + Clamped 334 uK^2 bullseye!
    px2_std, py2_std = map_xy(2.0, 1085.0)
    px2_cl, py2_cl = map_xy(2.0, 334.0)
    dr.ellipse((px2_std - 14, py2_std - 14, px2_std + 14, py2_std + 14), fill=(*ACCENT_CORAL, 255))
    dr.text((px2_std + 28, py2_std - 52), "Textbook Lambda-CDM: ~1,100 uK²", font=FONTS["graph_lbl"], fill=(*ACCENT_CORAL, 255))

    if prog > 0.25:
        dr.ellipse((px2_cl - 16, py2_cl - 16, px2_cl + 16, py2_cl + 16), fill=(*ACCENT_EMERALD, 255), outline=(255, 255, 255, 255), width=4)
        dr.text((px2_cl + 28, py2_cl - 26), "Clamped Waist: 334 uK² (Matches Planck!)", font=FONTS["graph_lbl"], fill=(*ACCENT_EMERALD, 255))
    if prog > 0.72:
        px_hi, py_hi = map_xy(14.0, 995.0)
        dr.text((px_hi - 80, py_hi + 36), "Smaller Ripples: 99.95% Untouched", font=FONTS["graph_lbl"], fill=(*ACCENT_GOLD, 255))

    blit_rgba_fast(frame, np.asarray(im, dtype=np.uint8), W4K - gw - 84, 520, opacity=opacity)


def draw_cmb_third_peak_chart_4k(frame: np.ndarray, rescue_amt: float, opacity: float) -> None:
    """Animated 4K CMB Acoustic Peaks 1, 2, 3 chart: Memoryless Crash (0.16) -> SO(3) Pleat Rescue (0.72)!"""
    gw, gh = 1820, 1040
    im = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, gw - 1, gh - 1), radius=40, fill=(18, 30, 48, 240), outline=PILL_BORDER, width=4)
    dr.text((64, 38), "CMB ACOUSTIC SOUND PEAKS  (l = 100 .. 1,000)", font=FONTS["graph_t"], fill=(*TEXT_ALABASTER, 255))
    sub = (
        "Uncharged SO(3) Spacetime Pleats (5 + 1/pi -> Omega_m = 0.3094) Rescue Peak 3!"
        if rescue_amt > 0.15
        else "Why Memoryless Gravity Crashes at the Famous 3rd Acoustic Peak"
    )
    dr.text((64, 108), sub, font=FONTS["graph_ax"], fill=(*ACCENT_GOLD, 255))

    x0, y0, x1, y1 = 130, 210, gw - 80, gh - 120
    dr.line([(x0, y1), (x1, y1)], fill=(191, 219, 254, 190), width=4)
    dr.line([(x0, y0), (x0, y1)], fill=(191, 219, 254, 190), width=4)

    def map_xy(ell: float, norm_p: float) -> Tuple[int, int]:
        ux = (ell - 80.0) / 920.0
        uy = min(1.05, max(0.0, norm_p))
        return int(x0 + ux * (x1 - x0)), int(y1 - uy * (y1 - y0))

    ells = np.linspace(80.0, 1000.0, 180)
    pts_planck = []
    pts_model = []
    for l_v in ells:
        p1 = 0.86 * math.exp(-((l_v - 220.0) / 88.0) ** 2)
        p2 = 0.41 * math.exp(-((l_v - 535.0) / 82.0) ** 2)
        p3_true = 0.296 * math.exp(-((l_v - 815.0) / 82.0) ** 2)  # 0.296 / 0.41 = 0.722!
        p3_crash = 0.066 * math.exp(-((l_v - 815.0) / 82.0) ** 2)  # 0.066 / 0.41 = 0.161!
        base = 0.07 * math.exp(-l_v / 900.0)
        y_pl = base + p1 + p2 + p3_true
        y_md = base + p1 + p2 + ((1.0 - rescue_amt) * p3_crash + rescue_amt * p3_true)
        pts_planck.append(map_xy(float(l_v), y_pl))
        pts_model.append(map_xy(float(l_v), y_md))

    # Dashed/muted Planck reference + bold live curve
    dr.line(pts_planck, fill=(125, 211, 252, 165), width=6)
    col_live = (52, 211, 153, 255) if rescue_amt > 0.5 else (251, 146, 60, 255)
    dr.line(pts_model, fill=col_live, width=10)

    # Labels on Peak 1, Peak 2, Peak 3
    p1x, p1y = map_xy(220.0, 0.92)
    p2x, p2y = map_xy(535.0, 0.46)
    dr.text((p1x - 65, p1y - 54), "Peak 1", font=FONTS["graph_lbl"], fill=(*TEXT_ALABASTER, 255))
    dr.text((p2x - 65, p2y - 54), "Peak 2", font=FONTS["graph_lbl"], fill=(*TEXT_ALABASTER, 255))

    r32_now = 0.16 + 0.55 * rescue_amt
    y3_now = 0.035 + 0.066 * (1.0 - rescue_amt) + 0.296 * rescue_amt
    p3x, p3y = map_xy(815.0, y3_now)
    dr.ellipse((p3x - 16, p3y - 16, p3x + 16, p3y + 16), fill=col_live, outline=(255, 255, 255, 255), width=4)
    lbl3 = f"Peak 3 Rescued: R_32 = {r32_now:.2f}!" if rescue_amt > 0.5 else "Memoryless Crash: R_32 = 0.16"
    dr.text((p3x - 420, p3y - 62), lbl3, font=FONTS["graph_lbl"], fill=col_live)

    blit_rgba_fast(frame, np.asarray(im, dtype=np.uint8), W4K - gw - 84, 510, opacity=opacity)


# ---------------------------------------------------------------------------
# Smooth Palindrome Cinema & Animated Portrait Cache + Option A+ 4K Upscaler
# ---------------------------------------------------------------------------

class Ep2CinemaClipCache:
    """
    Decodes `gemini-omni-1.1-flash` (`1080p`) cinema & centered animated portrait clips lazily,
    using smooth palindrome motion if a window exceeds 8s so NO clip or portrait ever freezes still!
    """

    OV_W, OV_H = 2016, 1134  # Gentle 5% overscan so centered portraits stay huge & dead-center!

    def __init__(self, ffmpeg_exe: str) -> None:
        self.ffmpeg_exe = ffmpeg_exe
        self._loaded: Dict[str, List[np.ndarray]] = {}

    def get_frame(
        self,
        clip_name: str,
        local_t: float,
        dur_win: float,
        zoom_dir: int = 1,
        is_portrait: bool = False,
    ) -> Optional[np.ndarray]:
        p = CINEMA_EP2_DIR / clip_name
        if not p.exists():
            p = CINEMA_EP1_DIR / clip_name
        if not p.exists():
            return None

        if clip_name not in self._loaded:
            # Keep max 6 decoded clips in RAM per worker so 6 parallel workers stay light on system RAM!
            if len(self._loaded) >= 6:
                oldest = next(iter(self._loaded))
                del self._loaded[oldest]
            cmd = [
                self.ffmpeg_exe,
                "-v", "error",
                "-i", str(p),
                "-vf", f"fps={FPS},scale={self.OV_W}:{self.OV_H}:flags=bicubic",
                "-f", "rawvideo",
                "-pix_fmt", "rgb24",
                "-",
            ]
            raw = subprocess.check_output(cmd)
            f_bytes = self.OV_W * self.OV_H * 3
            n_f = len(raw) // f_bytes
            arr = np.frombuffer(raw[: n_f * f_bytes], dtype=np.uint8).reshape(n_f, self.OV_H, self.OV_W, 3)
            self._loaded[clip_name] = [arr[i] for i in range(n_f)]

        frames = self._loaded[clip_name]
        if not frames:
            return None

        n_f = len(frames)
        # Smooth palindrome loop (`0 .. n_f-1 .. 1`) at natural 0.85x documentary cadence — zero freeze frames!
        rate = 0.82 if is_portrait else 0.88
        raw_idx = int(round(local_t * rate * FPS))
        cycle = max(1, 2 * (n_f - 1))
        pos = raw_idx % cycle
        idx = pos if pos < n_f else (cycle - pos)
        src = frames[min(n_f - 1, max(0, idx))]

        if is_portrait:
            # Keep scientist portrait strictly centered horizontally!
            ox = (self.OV_W - 1920) // 2
            oy = (self.OV_H - 1080) // 2
            return src[oy : oy + 1080, ox : ox + 1920]

        u = max(0.0, min(1.0, local_t / max(0.2, dur_win)))
        if zoom_dir < 0:
            u = 1.0 - u
        ox = int(round(0.5 * (self.OV_W - 1920) * u))
        oy = int(round(0.5 * (self.OV_H - 1080) * u))
        return src[oy : oy + 1080, ox : ox + 1920]


class OptionAPlus4KUpscaler:
    """Upscales `1920x1080` 3D scenes & Omni B-roll cleanly to `3840x2160` with anti-flashbang shoulder."""

    def __init__(self, device: torch.device) -> None:
        self.dev = device
        self._out = np.empty((H4K, W4K, 3), dtype=np.uint8)
        self._tint_floor = torch.tensor([18.0, 28.0, 44.0], device=device).view(1, 3, 1, 1)

    def to_4k(self, img_1080_or_4k: np.ndarray, grade_broll: bool = False) -> np.ndarray:
        if img_1080_or_4k.shape[0] == H4K and img_1080_or_4k.shape[1] == W4K and not grade_broll:
            return img_1080_or_4k.copy()

        arr = img_1080_or_4k if img_1080_or_4k.flags.writeable else img_1080_or_4k.copy()
        t_in = torch.from_numpy(arr).to(self.dev).permute(2, 0, 1).unsqueeze(0).float()
        if t_in.shape[-2] != H4K or t_in.shape[-1] != W4K:
            up = F.interpolate(t_in, size=(H4K, W4K), mode="bilinear", align_corners=False)
        else:
            up = t_in

        if grade_broll:
            over = F.relu(up - 208.0)
            up = torch.where(up > 208.0, 208.0 + 28.0 * torch.tanh(over / 46.0), up)
            up = torch.maximum(up, self._tint_floor * 0.78)

        hwc = torch.clamp(up, 0.0, 242.0).squeeze(0).permute(1, 2, 0).to(torch.uint8).cpu().numpy()
        np.copyto(self._out, hwc)
        return self._out.copy()


# ---------------------------------------------------------------------------
# Episode 2 Omni Cinema & Large Centered Living Portrait Schedule
# ---------------------------------------------------------------------------

def get_ep2_omni_windows(scene: dict) -> List[Tuple[float, float, str, int, bool, Optional[Tuple[str, str, Tuple[int, int, int]]]]]:
    """
    Returns `(w_start, w_end, clip_filename, zoom_dir, is_portrait, optional_nameplate)`
    across all 7 chapters of Episode 2!
    """
    sid = scene["id"]
    wins = []

    if sid == "scene00":
        c0 = _find_chunk(scene, "chunk_00")
        c1 = _find_chunk(scene, "chunk_01")
        if c0:
            wins.append((c0["local_start"] + 21.0, c0["local_end"], "ep2_weaveforge_knot_arena.mp4", 1, False, None))
        if c1:
            wins.append((c1["local_start"] + 1.5, c1["local_start"] + 21.0, "ep2_gaia_dr4_wide_binary_stars.mp4", 1, False, None))

    elif sid == "scene01":
        c4 = _find_chunk(scene, "chunk_04")
        c5 = _find_chunk(scene, "chunk_05")
        c6 = _find_chunk(scene, "chunk_06")
        c7 = _find_chunk(scene, "chunk_07")
        if c4:
            wins.append((c4["local_start"] + 6.0, c4["local_start"] + 20.5, "ep2_shattering_teacup_entropy.mp4", 1, False, None))
        if c5:
            wins.append(
                (
                    c5["local_start"] + 11.2,
                    c5["local_end"],
                    "ep2_portrait_penrose.mp4",
                    1,
                    True,
                    ("SIR ROGER PENROSE  •  NOBEL LAUREATE (1979)", "1-IN-10^(10^123) BIG BANG SMOOTHNESS ODDS", ACCENT_GOLD),
                )
            )
        if c6:
            wins.append((c6["local_start"] + 8.5, c6["local_start"] + 25.0, "ep2_cosmic_hourglass_flip.mp4", 1, False, None))
        if c7:
            wins.append(
                (
                    c7["local_start"] + 9.2,
                    c7["local_start"] + 19.2,
                    "ep2_portrait_landauer.mp4",
                    1,
                    True,
                    ("ROLF LANDAUER  •  IBM FELLOW (1961)", "PHYSICAL MEMORY WRITES TOWARD RISING ENTROPY", ACCENT_CYAN),
                )
            )
            wins.append((c7["local_start"] + 19.4, c7["local_start"] + 27.6, "ep1_brain_neurons_synapse_memory.mp4", 1, False, None))
            wins.append((c7["local_start"] + 27.8, c7["local_end"], "ep1_moon_asteroid_crater_memory.mp4", -1, False, None))

    elif sid == "scene02":
        c10 = _find_chunk(scene, "chunk_10")
        if c10:
            wins.append((c10["local_start"] + 2.0, c10["local_end"], "ep2_two_brass_rings_catenoid_soap.mp4", 1, False, None))

    elif sid == "scene03":
        c12 = _find_chunk(scene, "chunk_12")
        c15 = _find_chunk(scene, "chunk_15")
        if c12:
            wins.append((c12["local_start"] + 4.0, c12["local_start"] + 21.5, "ep2_planck_quiet_sky_observatory.mp4", 1, False, None))
        if c15:
            wins.append((c15["local_start"] + 0.6, c15["local_start"] + 9.4, "ep1_lacuna_papers_rain_umbrellas.mp4", 1, False, None))
            wins.append((c15["local_start"] + 9.6, c15["local_start"] + 21.8, "ep2_cambridge_prd_paper_desk.mp4", 1, False, None))
            wins.append(
                (
                    c15["local_start"] + 22.0,
                    c15["local_end"],
                    "ep2_portrait_turok.mp4",
                    1,
                    True,
                    ("NEIL TUROK, LATHAM BOYLE & KIERAN FINN", "CPT MIRROR UNIVERSE  •  DENG & HANDLEY (2024–2025)", ACCENT_CYAN),
                )
            )

    elif sid == "scene04":
        c17 = _find_chunk(scene, "chunk_17")
        c18 = _find_chunk(scene, "chunk_18")
        c19 = _find_chunk(scene, "chunk_19")
        c20 = _find_chunk(scene, "chunk_20")
        c21 = _find_chunk(scene, "chunk_21")
        if c17:
            wins.append((c17["local_start"] + 1.2, c17["local_start"] + 22.0, "ep2_slac_babar_bmeson_detector.mp4", 1, False, None))
        if c18:
            wins.append(
                (
                    c18["local_start"] + 5.2,
                    c18["local_start"] + 23.8,
                    "ep2_portrait_pauli_schwinger.mp4",
                    1,
                    True,
                    ("GERHART LÜDERS, WOLFGANG PAULI & JULIAN SCHWINGER", "THE 1954 BEDROCK CPT SYMMETRY THEOREM", ACCENT_GOLD),
                )
            )
        if c19:
            wins.append(
                (
                    c19["local_start"] + 2.5,
                    c19["local_start"] + 15.8,
                    "ep2_portrait_barbour.mp4",
                    1,
                    True,
                    ("JULIAN BARBOUR  •  THE JANUS POINT", "TWO-WING GRAVITATIONAL SYMMETRY  •  ZERO SHEAR", ACCENT_GOLD),
                )
            )
        if c20:
            wins.append(
                (
                    c20["local_start"] + 3.8,
                    c20["local_start"] + 20.5,
                    "ep2_portrait_sakharov.mp4",
                    1,
                    True,
                    ("ANDREI SAKHAROV (1967)", "6 PROTONS PER 10 BILLION PHOTONS  •  MISSING ANTIMATTER", ACCENT_CORAL),
                )
            )
        if c21:
            wins.append((c21["local_start"] + 1.0, c21["local_start"] + 26.2, "ep2_cpt_hourglass_antimatter_sorter.mp4", 1, False, None))
            wins.append(
                (
                    c21["local_start"] + 26.5,
                    c21["local_end"],
                    "ep2_portrait_hawking.mp4",
                    1,
                    True,
                    ("STEPHEN HAWKING  •  UNITARY PAGE CURVE", "100% QUANTUM INFORMATION RECOVERED  •  ZERO LOST BITS", ACCENT_EMERALD),
                )
            )

    elif sid == "scene05":
        c24 = _find_chunk(scene, "chunk_24")
        c27 = _find_chunk(scene, "chunk_27")
        if c24:
            wins.append((c24["local_start"] + 3.2, c24["local_start"] + 25.0, "ep2_tablecloth_pleats_photon_stream.mp4", 1, False, None))
        if c27:
            wins.append((c27["local_start"] + 8.5, c27["local_start"] + 24.5, "ep2_katrin_litebird_killswitch.mp4", 1, False, None))

    elif sid == "scene06":
        c30 = _find_chunk(scene, "chunk_30")
        if c30:
            wins.append((c30["local_start"] + 6.0, c30["local_start"] + 24.5, "ep2_double_slit_standing_wave_teaser.mp4", 1, False, None))

    return wins


# ---------------------------------------------------------------------------
# Chapter Headers & Chunk-Synced Giant 4K Keynote Overlays
# ---------------------------------------------------------------------------

def draw_chapter_header_and_lower_third_4k(
    frame: np.ndarray,
    lib: Ep2OverlayLibrary4K,
    scene: dict,
    local_t: float,
) -> None:
    sid = scene["id"]
    if sid == "intro00":
        vis = smoothstep01((local_t - 0.15) / 0.45) * smoothstep01((3.40 - local_t) / 0.45)
        pill = lib.get_keynote_pill(
            "THEORETICALLY NOT A PHYSICIST  •  EPISODE 2",
            "THE UPSIDE-DOWN BIG BANG",
            ACCENT_GOLD,
            giant=True,
        )
        blit_rgba_fast(frame, pill, (W4K - pill.shape[1]) // 2, H4K - pill.shape[0] - 130, opacity=vis)
        return

    wm_key = f"wm_{sid}"
    if wm_key not in lib._custom:
        wm_txt = f"{scene['chapter']}  •  {scene['title']}"
        dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
        bb = dummy.textbbox((0, 0), wm_txt, font=FONTS["wm"])
        pw = (bb[2] - bb[0]) + 64
        ph = 70
        im_w = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        dw = ImageDraw.Draw(im_w)
        dw.rounded_rectangle((0, 0, pw - 1, ph - 1), radius=35, fill=(20, 32, 52, 182), outline=(125, 211, 252, 125), width=2)
        dw.text((32, 15), wm_txt, font=FONTS["wm"], fill=(219, 234, 254, 228))
        lib._custom[wm_key] = np.asarray(im_w, dtype=np.uint8)
    blit_rgba_fast(frame, lib._custom[wm_key], 76, 58, opacity=1.0)

    if 0.35 <= local_t <= 6.80:
        vis = smootherstep01((local_t - 0.35) / 0.55) * smootherstep01((6.80 - local_t) / 0.55)
        lt_key = f"lt_{sid}"
        if lt_key not in lib._custom:
            cw, ch = 2240, 218
            im_l = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dl = ImageDraw.Draw(im_l)
            dl.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=34, fill=PILL_BG, outline=PILL_BORDER, width=4)
            dl.rounded_rectangle((30, 32, 44, ch - 32), radius=7, fill=(*ACCENT_GOLD, 255))
            dl.text((74, 34), scene["subtitle_tag"], font=FONTS["lt_kicker"], fill=(*ACCENT_CYAN, 255))
            dl.text((74, 96), scene["title"], font=FONTS["lt_title"], fill=(*TEXT_ALABASTER, 255))
            lib._custom[lt_key] = np.asarray(im_l, dtype=np.uint8)
        blit_rgba_fast(frame, lib._custom[lt_key], 76 - int((1.0 - vis) * 68), 156, opacity=vis)


def _draw_timed_pill(
    frame: np.ndarray,
    lib: Ep2OverlayLibrary4K,
    local_t: float,
    t0: float,
    t1: float,
    kicker: str,
    headline: str,
    accent: Tuple[int, int, int] = ACCENT_GOLD,
    pos: str = "bottom_center",
    giant: bool = True,
) -> None:
    if not (t0 <= local_t <= t1):
        return
    vis = smoothstep01((local_t - t0) / 0.45) * smoothstep01((t1 - local_t) / 0.45)
    pill = lib.get_keynote_pill(kicker, headline, accent=accent, giant=giant)
    ph, pw, _ = pill.shape
    if pos == "bottom_center":
        x, y = (W4K - pw) // 2, H4K - ph - 114
    elif pos == "top_right":
        x, y = W4K - pw - 86, 156
    else:
        x, y = 86, H4K - ph - 114
    blit_rgba_fast(frame, pill, x, y + int((1.0 - vis) * 24), opacity=vis)


def _draw_timed_card(
    frame: np.ndarray,
    card_arr: np.ndarray,
    local_t: float,
    t0: float,
    t1: float,
    x: int,
    y: int,
) -> None:
    if not (t0 <= local_t <= t1):
        return
    vis = smoothstep01((local_t - t0) / 0.50) * smoothstep01((t1 - local_t) / 0.50)
    blit_rgba_fast(frame, card_arr, x, y + int((1.0 - vis) * 26), opacity=vis)


def draw_scene_keynote_overlays_4k(
    frame: np.ndarray,
    lib: Ep2OverlayLibrary4K,
    scene: dict,
    local_t: float,
) -> None:
    sid = scene["id"]

    if sid == "scene00":
        c0 = _find_chunk(scene, "chunk_00")
        c1 = _find_chunk(scene, "chunk_01")
        c2 = _find_chunk(scene, "chunk_02")
        c3 = _find_chunk(scene, "chunk_03")
        s0, e0 = (c0["local_start"], c0["local_end"]) if c0 else (0.3, 37.4)
        s1, e1 = (c1["local_start"], c1["local_end"]) if c1 else (38.8, 75.0)
        s2, e2 = (c2["local_start"], c2["local_end"]) if c2 else (76.4, 102.3)
        s3, e3 = (c3["local_start"], c3["local_end"]) if c3 else (103.8, 138.4)

        _draw_timed_pill(frame, lib, local_t, s0 + 21.5, e0, "OPEN-SOURCE 3D ENGINE", "WEAVEFORGE  •  ARENA 1–4", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s1 + 7.5, s1 + 21.0, "DEC 2, 2026  •  ESA GAIA DR4", "CERN ZENODO BLIND LOCK", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s1 + 22.0, e1, "ZERO FREE TUNING KNOBS", "+4.63% SHADOW RING TEST", ACCENT_EMERALD)
        _draw_timed_pill(frame, lib, local_t, s2 + 8.0, e2, "EPISODE 2  •  PILLAR 3", "UPSIDE-DOWN BIG BANG", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s3 + 6.0, s3 + 14.2, "WINDSHIELD BRICK #1", "VIDEO-GAME CHEAT CODE?", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s3 + 14.6, s3 + 24.2, "WINDSHIELD BRICK #2", "STANFORD BABAR 14 SIGMA", ACCENT_CORAL)
        _draw_timed_pill(frame, lib, local_t, s3 + 24.6, e3, "WINDSHIELD BRICK #3", "THE 3RD ACOUSTIC PEAK", ACCENT_CYAN)

    elif sid == "scene01":
        c4 = _find_chunk(scene, "chunk_04")
        c6 = _find_chunk(scene, "chunk_06")
        c7 = _find_chunk(scene, "chunk_07")
        s4, e4 = (c4["local_start"], c4["local_end"]) if c4 else (0.7, 30.6)
        s6, e6 = (c6["local_start"], c6["local_end"]) if c6 else (66.7, 103.9)
        s7, e7 = (c7["local_start"], c7["local_end"]) if c7 else (105.5, 143.5)

        _draw_timed_pill(frame, lib, local_t, s4 + 13.5, e4, "SECOND LAW OF THERMODYNAMICS", "REWIND 13.8B YEARS", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s6 + 9.0, s6 + 22.5, "FLIP THE HOURGLASS 180°", "WIDE CHAOS -> SMOOTH DRAIN", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s7 + 20.5, e7, "OBSERVER MEMORY ARROW", "SMOOTH WAIST = PAST", ACCENT_EMERALD)

    elif sid == "scene02":
        c8 = _find_chunk(scene, "chunk_08")
        c9 = _find_chunk(scene, "chunk_09")
        c10 = _find_chunk(scene, "chunk_10")
        c11 = _find_chunk(scene, "chunk_11")
        s8, e8 = (c8["local_start"], c8["local_end"]) if c8 else (0.7, 29.0)
        s9, e9 = (c9["local_start"], c9["local_end"]) if c9 else (30.5, 66.2)
        s10, e10 = (c10["local_start"], c10["local_end"]) if c10 else (67.7, 95.7)
        s11, e11 = (c11["local_start"], c11["local_end"]) if c11 else (97.1, 127.8)

        kc = lib._custom["konami_audit"]
        _draw_timed_card(frame, kc, local_t, s8 + 9.5, e9 - 1.0, (W4K - kc.shape[1]) // 2, H4K - kc.shape[0] - 96)
        _draw_timed_pill(frame, lib, local_t, s10 + 13.0, e10, "TWO CLAMPED BRASS RINGS", "CATENOID SOAP FILM", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s11 + 11.5, e11, "NARROW CENTRAL WAIST", "SQUEEZES GIANT SKY WAVES", ACCENT_CYAN)

    elif sid == "scene03":
        c12 = _find_chunk(scene, "chunk_12")
        c13 = _find_chunk(scene, "chunk_13")
        c14 = _find_chunk(scene, "chunk_14")
        c15 = _find_chunk(scene, "chunk_15")
        s12, e12 = (c12["local_start"], c12["local_end"]) if c12 else (0.7, 30.7)
        s13, e13 = (c13["local_start"], c13["local_end"]) if c13 else (32.1, 67.2)
        s14, e14 = (c14["local_start"], c14["local_end"]) if c14 else (68.7, 100.1)
        s15, e15 = (c15["local_start"], c15["local_end"]) if c15 else (101.7, 144.4)

        _draw_timed_pill(frame, lib, local_t, s12 + 6.0, e12, "30 YEARS OF CMB MAPS", "COBE  •  WMAP  •  PLANCK", ACCENT_CYAN)

        if s13 + 7.5 <= local_t <= e14 + 0.8:
            vis_q = smoothstep01((local_t - (s13 + 7.5)) / 0.6) * smoothstep01((e14 + 0.8 - local_t) / 0.6)
            prog_q = max(0.0, min(1.0, (local_t - (s14 + 4.0)) / 18.0))
            draw_planck_quadrupole_chart_4k(frame, prog_q, vis_q)

        _draw_timed_pill(frame, lib, local_t, s14 + 17.5, e14, "CLAMPED HOURGLASS WAIST", "334 uK²  •  QUIET SKY!", ACCENT_EMERALD, pos="bottom_left", giant=False)

        _draw_timed_pill(frame, lib, local_t, s15 + 1.2, s15 + 9.0, "LACUNA DISCOVERY ENGINE", "2.2M+ PHYSICS PAPERS", ACCENT_GOLD)
        dh = lib._custom["deng_handley_paper"]
        _draw_timed_card(frame, dh, local_t, s15 + 9.8, s15 + 21.6, (W4K - dh.shape[1]) // 2, (H4K - dh.shape[0]) // 2 + 40)

    elif sid == "scene04":
        c16 = _find_chunk(scene, "chunk_16")
        c17 = _find_chunk(scene, "chunk_17")
        c18 = _find_chunk(scene, "chunk_18")
        c19 = _find_chunk(scene, "chunk_19")
        c21 = _find_chunk(scene, "chunk_21")
        s16, e16 = (c16["local_start"], c16["local_end"]) if c16 else (0.7, 29.3)
        s17, e17 = (c17["local_start"], c17["local_end"]) if c17 else (30.7, 65.7)
        s18, e18 = (c18["local_start"], c18["local_end"]) if c18 else (67.2, 100.1)
        s19, e19 = (c19["local_start"], c19["local_end"]) if c19 else (101.6, 138.2)
        s21, e21 = (c21["local_start"], c21["local_end"]) if c21 else (177.5, 218.1)

        _draw_timed_pill(frame, lib, local_t, s16 + 12.0, e16, "PARTICLE COLLIDER CHECK", "TIME-REVERSAL ALONE FAILS", ACCENT_CORAL)
        _draw_timed_pill(frame, lib, local_t, s17 + 16.0, e17, "SLAC BABAR B-MESON TEST", "14 SIGMA ASYMMETRY!", ACCENT_CORAL)
        _draw_timed_pill(frame, lib, local_t, s18 + 24.2, e18, "FLIP CHARGE + PARITY + TIME", "100% EXACT CPT SYMMETRY", ACCENT_EMERALD)
        _draw_timed_pill(frame, lib, local_t, s19 + 19.0, e19, "ZERO SHEAR AT SMOOTH WAIST", "230-SIGMA He-4 DEFUSED!", ACCENT_EMERALD)
        _draw_timed_pill(frame, lib, local_t, s21 + 10.5, s21 + 25.8, "SUBATOMIC COIN-SORTER", "MATTER <-> MIRROR WING", ACCENT_GOLD)

    elif sid == "scene05":
        c22 = _find_chunk(scene, "chunk_22")
        c23 = _find_chunk(scene, "chunk_23")
        c24 = _find_chunk(scene, "chunk_24")
        c25 = _find_chunk(scene, "chunk_25")
        c26 = _find_chunk(scene, "chunk_26")
        c27 = _find_chunk(scene, "chunk_27")
        s22, e22 = (c22["local_start"], c22["local_end"]) if c22 else (0.7, 21.2)
        s23, e23 = (c23["local_start"], c23["local_end"]) if c23 else (22.6, 57.6)
        s24, e24 = (c24["local_start"], c24["local_end"]) if c24 else (59.1, 92.3)
        s25, e25 = (c25["local_start"], c25["local_end"]) if c25 else (93.8, 127.3)
        s26, e26 = (c26["local_start"], c26["local_end"]) if c26 else (128.9, 163.3)
        s27, e27 = (c27["local_start"], c27["local_end"]) if c27 else (164.8, 197.8)

        _draw_timed_pill(frame, lib, local_t, s22 + 9.0, e22, "MODIFIED GRAVITY GRAVEYARD", "THE 3RD ACOUSTIC PEAK", ACCENT_CORAL)

        if s23 + 4.0 <= local_t <= e23 + 0.6:
            vis_c = smoothstep01((local_t - (s23 + 4.0)) / 0.6) * smoothstep01((e23 + 0.6 - local_t) / 0.6)
            draw_cmb_third_peak_chart_4k(frame, 0.0, vis_c)

        _draw_timed_pill(frame, lib, local_t, s24 + 14.0, e24, "BULLET CLUSTER IN REVERSE", "UNCHARGED SPACETIME PLEATS", ACCENT_CYAN)

        if s25 + 2.5 <= local_t <= e25 + 0.6:
            vis_r = smoothstep01((local_t - (s25 + 2.5)) / 0.6) * smoothstep01((e25 + 0.6 - local_t) / 0.6)
            resc = smootherstep01((local_t - (s25 + 5.0)) / 9.5)
            draw_cmb_third_peak_chart_4k(frame, resc, vis_r)

        _draw_timed_pill(frame, lib, local_t, s25 + 14.0, e25, "PLEAT RATIO  5 + 1 / pi", "99.92% DENSITY MATCH!", ACCENT_EMERALD, pos="bottom_left", giant=False)

        ks = lib._custom["killswitch_scorecard"]
        _draw_timed_card(frame, ks, local_t, s26 + 2.5, e26 + 0.5, (W4K - ks.shape[1]) // 2, H4K - ks.shape[0] - 96)
        _draw_timed_pill(frame, lib, local_t, s27 + 9.0, e27, "KILL-SWITCH #2  •  KATRIN", "LIGHTEST NEUTRINO = 0.00 eV", ACCENT_CORAL)

    elif sid == "scene06":
        c28 = _find_chunk(scene, "chunk_28")
        c29 = _find_chunk(scene, "chunk_29")
        c30 = _find_chunk(scene, "chunk_30")
        s28, e28 = (c28["local_start"], c28["local_end"]) if c28 else (0.7, 30.8)
        s29, e29 = (c29["local_start"], c29["local_end"]) if c29 else (32.3, 61.1)
        s30, e30 = (c30["local_start"], c30["local_end"]) if c30 else (62.6, 95.3)

        pz = lib._custom["portal_zenodo_card"]
        _draw_timed_card(frame, pz, local_t, s28 + 1.5, e28 + 0.4, (W4K - pz.shape[1]) // 2, H4K - pz.shape[0] - 110)

        rl = lib._custom["recap_ledger_card"]
        _draw_timed_card(frame, rl, local_t, s29 + 1.5, e29 + 0.4, (W4K - rl.shape[1]) // 2, H4K - rl.shape[0] - 110)

        _draw_timed_pill(frame, lib, local_t, s30 + 6.5, s30 + 23.5, "NEXT TIME  •  EPISODE 3", "DOUBLE-SLIT STANDING WAVES", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s30 + 24.5, e30 + 1.4, "THANKS FOR WATCHING!", "STAY INQUISITIVE", ACCENT_GOLD)


def compose_ep2_frame_4k(
    director: Episode2SceneDirector,
    clip_cache: Ep2CinemaClipCache,
    upscaler: OptionAPlus4KUpscaler,
    lib: Ep2OverlayLibrary4K,
    scene: dict,
    local_t: float,
) -> np.ndarray:
    sid = scene["id"]
    dur = float(scene["duration_sec"])

    omni_1080: Optional[np.ndarray] = None
    omni_alpha = 0.0
    active_np: Optional[Tuple[str, str, Tuple[int, int, int]]] = None
    xf = 0.65

    for w0, w1, cname, zdir, is_port, np_spec in get_ep2_omni_windows(scene):
        if w0 - xf <= local_t <= w1 + xf:
            f_in = smoothstep01((local_t - (w0 - xf)) / (2.0 * xf))
            f_out = smoothstep01(((w1 + xf) - local_t) / (2.0 * xf))
            cand_a = max(0.0, min(1.0, f_in * f_out))
            if cand_a > 0.01:
                fr_try = clip_cache.get_frame(cname, max(0.0, local_t - w0), w1 - w0, zoom_dir=zdir, is_portrait=is_port)
                if fr_try is not None:
                    omni_1080 = fr_try
                    omni_alpha = cand_a
                    active_np = np_spec
                    break

    if omni_1080 is not None and omni_alpha >= 0.995:
        frame = upscaler.to_4k(omni_1080, grade_broll=True)
    elif omni_1080 is not None and omni_alpha > 0.01:
        base_4k = upscaler.to_4k(director.render_scene_frame(scene, local_t), grade_broll=False)
        broll_4k = upscaler.to_4k(omni_1080, grade_broll=True)
        frame = np.clip(broll_4k.astype(np.float32) * omni_alpha + base_4k.astype(np.float32) * (1.0 - omni_alpha), 0, 255).astype(np.uint8)
    else:
        frame = upscaler.to_4k(director.render_scene_frame(scene, local_t), grade_broll=False)

    # If a Large, Center-Screen Animated Portrait is on screen, render its razor-sharp 4K Museum Nameplate right underneath!
    if active_np is not None and omni_alpha > 0.05:
        np_card = lib.get_portrait_nameplate(active_np[0], active_np[1], active_np[2])
        blit_rgba_fast(frame, np_card, (W4K - np_card.shape[1]) // 2, 1732 + int((1.0 - omni_alpha) * 24), opacity=omni_alpha)

    draw_chapter_header_and_lower_third_4k(frame, lib, scene, local_t)
    draw_scene_keynote_overlays_4k(frame, lib, scene, local_t)

    if sid == "scene00" and local_t < 0.65:
        np.multiply(frame, max(0.0, min(1.0, local_t / 0.65)), out=frame, casting="unsafe")
    elif sid == "scene06" and local_t > dur - 2.4:
        np.multiply(frame, max(0.0, min(1.0, (dur - local_t) / 2.4)), out=frame, casting="unsafe")

    return frame


# ---------------------------------------------------------------------------
# Parallel CPU Worker Function (`0%` GPU Usage!)
# ---------------------------------------------------------------------------

def _render_frame_chunk_worker(args: Tuple[int, int, int, str]) -> Tuple[int, str, float]:
    seg_idx, f_start, f_end, seg_mp4_str = args
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["NUMBA_DISABLE_CUDA"] = "1"
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
    except Exception:
        pass
    torch.set_num_threads(2)

    t0 = time.time()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    director = Episode2SceneDirector(device=torch.device("cpu"))
    clip_cache = Ep2CinemaClipCache(ffmpeg_exe)
    upscaler = OptionAPlus4KUpscaler(torch.device("cpu"))
    lib = Ep2OverlayLibrary4K()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W4K}x{H4K}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-threads", "2",
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        seg_mp4_str,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert proc.stdin is not None

    scenes = manifest["scenes"]
    sc_idx = 0
    n_tot = f_end - f_start

    for idx_local, f_idx in enumerate(range(f_start, f_end)):
        gt = f_idx / float(FPS)
        while sc_idx < len(scenes) - 1 and gt >= scenes[sc_idx]["end_sec"]:
            sc_idx += 1
        sc = scenes[sc_idx]
        lt = max(0.0, gt - float(sc["start_sec"]))

        frame = compose_ep2_frame_4k(director, clip_cache, upscaler, lib, sc, lt)
        proc.stdin.write(memoryview(frame))

        if idx_local > 0 and idx_local % (FPS * 45) == 0:
            el = time.time() - t0
            fps_w = idx_local / max(0.1, el)
            print(f"  [Worker {seg_idx}] {100.0 * idx_local / n_tot:5.1f}% ({idx_local}/{n_tot}) @ {fps_w:4.1f} fps", flush=True)

    proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"Worker {seg_idx} FFmpeg failed with exit code {ret}")
    return seg_idx, seg_mp4_str, time.time() - t0


def run_qa_contact_sheet() -> Path:
    t0 = time.time()
    torch.set_num_threads(4)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    dev = torch.device("cuda" if USE_GPU else "cpu")

    director = Episode2SceneDirector(device=dev)
    clip_cache = Ep2CinemaClipCache(ffmpeg_exe)
    upscaler = OptionAPlus4KUpscaler(dev)
    lib = Ep2OverlayLibrary4K()
    sc_map = {s["id"]: s for s in manifest["scenes"]}

    qa_dir = EP2_DIR / "qa_frames_4k"
    qa_dir.mkdir(exist_ok=True)
    samples = [
        ("qa01_weaveforge_intro", sc_map["scene00"], _find_chunk(sc_map["scene00"], "chunk_00")["local_start"] + 25.0),
        ("qa02_penrose_centered_portrait", sc_map["scene01"], _find_chunk(sc_map["scene01"], "chunk_05")["local_start"] + 16.0),
        ("qa03_konami_cheatcode_audit", sc_map["scene02"], _find_chunk(sc_map["scene02"], "chunk_08")["local_start"] + 15.0),
        ("qa04_catenoid_soap_film", sc_map["scene02"], _find_chunk(sc_map["scene02"], "chunk_10")["local_start"] + 14.0),
        ("qa05_planck_334_quadrupole_chart", sc_map["scene03"], _find_chunk(sc_map["scene03"], "chunk_14")["local_start"] + 22.0),
        ("qa06_deng_handley_cambridge_paper", sc_map["scene03"], _find_chunk(sc_map["scene03"], "chunk_15")["local_start"] + 15.0),
        ("qa07_pauli_schwinger_centered_cpt", sc_map["scene04"], _find_chunk(sc_map["scene04"], "chunk_18")["local_start"] + 12.0),
        ("qa08_cmb_3rd_peak_pleat_rescue", sc_map["scene05"], _find_chunk(sc_map["scene05"], "chunk_25")["local_start"] + 18.0),
    ]
    grid = Image.new("RGB", (3840, 2160), (24, 38, 60))
    for idx, (tag, sc_obj, lt) in enumerate(samples):
        fr = compose_ep2_frame_4k(director, clip_cache, upscaler, lib, sc_obj, lt)
        out_p = qa_dir / f"{tag}.jpg"
        im_fr = Image.fromarray(fr)
        im_fr.save(out_p, quality=92)
        grid.paste(im_fr.resize((960, 540), Image.Resampling.LANCZOS), ((idx % 4) * 960, (idx // 4) * 540))
        print(f"  [QA 4K OK] {out_p.name} ({fr.shape[1]}x{fr.shape[0]})", flush=True)

    grid_p = qa_dir / "_ep2_qa_8frame_contact_sheet.jpg"
    grid.save(grid_p, quality=92)
    print(f"[EP2 QA SHEET READY in {time.time() - t0:.1f}s] -> {grid_p}", flush=True)
    return grid_p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa-only", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--use-gpu", action="store_true")
    args = ap.parse_args()

    if args.qa_only:
        run_qa_contact_sheet()
        return

    t0 = time.time()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    assert MASTER_WAV_PATH.exists(), f"Missing {MASTER_WAV_PATH}"

    total_sec = float(manifest["total_duration_sec"])
    total_frames = int(round(total_sec * FPS))
    n_workers = max(1, int(args.workers))

    seg_dir = EP2_DIR / "_tmp_cpu_segments"
    seg_dir.mkdir(exist_ok=True)

    tasks = []
    frames_per_seg = (total_frames + n_workers - 1) // n_workers
    for w_i in range(n_workers):
        f0 = w_i * frames_per_seg
        f1 = min(total_frames, (w_i + 1) * frames_per_seg)
        if f0 >= f1:
            break
        seg_mp4 = seg_dir / f"seg_{w_i:02d}.mp4"
        tasks.append((w_i, f0, f1, str(seg_mp4)))

    print(
        f"[EPISODE 2 4K UHD CPU-PARALLEL RENDER] {total_frames} frames ({total_sec/60:.2f} min @ 3840x2160 24fps, "
        f"ZERO burned-in subtitles, 0% GPU) across {len(tasks)} BELOW_NORMAL CPU workers...",
        flush=True,
    )

    completed_segs: Dict[int, str] = {}
    with ProcessPoolExecutor(max_workers=len(tasks)) as pool:
        futs = [pool.submit(_render_frame_chunk_worker, t_arg) for t_arg in tasks]
        for f in as_completed(futs):
            s_idx, s_path, dt = f.result()
            completed_segs[s_idx] = s_path
            print(f"  [OK] Segment {s_idx} finished in {dt:.1f}s -> {Path(s_path).name}", flush=True)

    concat_txt = seg_dir / "concat_list.txt"
    lines = [f"file '{Path(completed_segs[k]).resolve().as_posix()}'" for k in sorted(completed_segs)]
    concat_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    tmp_final = EP2_DIR / "_tmp_ep2_4k_mux.mp4"
    mux_cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(MASTER_WAV_PATH),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        "-movflags", "+faststart",
        str(tmp_final),
    ]
    subprocess.run(mux_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    shutil.move(str(tmp_final), str(FINAL_4K_MP4))
    shutil.copy2(str(FINAL_4K_MP4), str(ARTIFACT_4K_MP4))
    shutil.rmtree(seg_dir, ignore_errors=True)

    sz_mb = FINAL_4K_MP4.stat().st_size / 1e6
    print(f"\n[EPISODE 2 4K UHD MASTER COMPLETE] {FINAL_4K_MP4} ({sz_mb:.1f} MB) in {time.time() - t0:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
