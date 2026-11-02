"""
Master Native `3840x2160` (`4K UHD`, `24 fps`) Cinema Renderer & Assembler for Episode 1:
  'Episode 1 — Is Time Even Real? Vinyl Records, Memory & Why GPS Satellites Run Fast'

Non-Negotiable Production Rules Enforced:
  1. ZERO Burned-In Subtitles on Video Frames (`GEMINI.md` Rule #1 — 100% clean 4K picture!).
     Subtitles live strictly in `Episode_1_Is_Time_Even_Real_Subtitles.srt`.
  2. Locked Option A+ ('Luminous Sapphire Slate', 39% Vibrant Mid-Tone) across every GPU scene,
     Smoked-Sapphire Keynote Pill (`(24, 38, 60, 234)` + `#7DD3FC` border), and anti-flashbang B-roll grader.
  3. Giant Native-4K Typography (`118px–136px` bold headlines, strict 2–5 word badges, pre-cached RGBA
     overlays for blazing compositing speed & crystal-clear readability on both 4K monitors and phones!).
  4. Authentic Scientist Portrait Medallions & Landmark Paper Cards (`Einstein`, `Don Page`,
     `William K. Wootters`, `Rolf Landauer`, `Itay Griniasty` PRL paper + `William G. Unruh`, `Roy Kerr`).
  5. Gentle GPU Priority (`BELOW_NORMAL_PRIORITY_CLASS = 0x00004000`) per David's preference.
"""

from __future__ import annotations

import ctypes
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
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Gentle GPU/CPU priority per David's preference ("medium / gentle priority")
try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
except Exception:
    pass

EP1_DIR = Path(__file__).resolve().parent
ROOT_DIR = EP1_DIR.parent
EP0_DIR = ROOT_DIR / "episode0_flagship"
for p in (str(EP1_DIR), str(EP0_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from gpu_renderer_core import set_render_resolution, smootherstep01, smoothstep01  # noqa: E402

W4K, H4K = 3840, 2160
FPS = 24
SR = 48000

# Activate True Native 4K UHD BEFORE importing Episode1GPU3DDirector!
set_render_resolution(W4K, H4K)

from ep1_gpu_scenes import Episode1GPU3DDirector, _find_chunk  # noqa: E402

AUDIO_V1_DIR = EP1_DIR / "audio_v1"
MANIFEST_PATH = AUDIO_V1_DIR / "ep1_v1_manifest.json"
MASTER_WAV_PATH = AUDIO_V1_DIR / "Episode_1_Master_Audio_v1.wav"
PORTRAITS_DIR = EP1_DIR / "portraits"
CINEMA_EP1_DIR = EP1_DIR / "cinema_clips"
CINEMA_EP0_DIR = EP0_DIR / "cinema_clips"
ARTIFACT_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")

FINAL_4K_MP4 = EP1_DIR / "Episode_1_Is_Time_Even_Real_4K_UHD.mp4"
ARTIFACT_4K_MP4 = ARTIFACT_DIR / "Episode_1_Is_Time_Even_Real_4K_UHD.mp4"

# Locked Option A+ ('Luminous Sapphire Slate') Typography & Card Constants
PILL_BG = (24, 38, 60, 236)
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
    "giant": load_font_4k(124, bold=True),       # Giant 3-5 word Keynote pop-out!
    "hero": load_font_4k(96, bold=True),         # Secondary hero badge
    "kicker": load_font_4k(46, bold=True),       # Crisp gold/cyan kicker above giant headline
    "lt_kicker": load_font_4k(38, bold=True),    # Chapter lower-third kicker
    "lt_title": load_font_4k(64, bold=True),     # Chapter lower-third title
    "wm": load_font_4k(32, bold=False),          # Subtle top-left chapter breadcrumb
    "p_name": load_font_4k(54, bold=True),       # Scientist portrait name
    "p_role": load_font_4k(36, bold=False),      # Scientist year / discovery line
    "paper_j": load_font_4k(34, bold=True),      # Journal header
    "paper_t": load_font_4k(46, bold=True),      # Paper title
    "paper_a": load_font_4k(34, bold=False),     # Paper authors
    "graph_t": load_font_4k(48, bold=True),      # Graph header
    "graph_lbl": load_font_4k(36, bold=True),    # Graph callouts
    "graph_ax": load_font_4k(30, bold=False),    # Graph axes
}


def blit_rgba_fast(frame_rgb: np.ndarray, patch_arr: np.ndarray, x0: int, y0: int, opacity: float = 1.0) -> None:
    """Blends pre-rasterized RGBA uint8 numpy patch onto `(2160, 3840, 3)` frame with smooth opacity."""
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
# Pre-Cached Overlay Factory (Keynote Pills, Portrait Medallions, Paper Cards)
# ---------------------------------------------------------------------------

class OverlayLibrary4K:
    """Pre-renders and caches crisp 4K RGBA badges, scientist medallions & paper cards."""

    def __init__(self) -> None:
        self._pills: Dict[tuple, np.ndarray] = {}
        self._portraits: Dict[str, np.ndarray] = {}
        self._custom: Dict[str, np.ndarray] = {}
        self._build_scientist_cards()
        self._build_static_showcase_cards()

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
        kw = bb_k[2] - bb_k[0]
        hw = bb_h[2] - bb_h[0]
        hh = bb_h[3] - bb_h[1]

        pad_x = 76
        cw = max(kw, hw) + pad_x * 2 + 24
        ch = 268 if giant else 228

        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=38, fill=PILL_BG, outline=PILL_BORDER, width=4)
        # Left vertical luminous accent bar
        dr.rounded_rectangle((28, 34, 42, ch - 34), radius=7, fill=(*accent, 255))

        dr.text((68, 30), kicker, font=f_kick, fill=(*accent, 255))
        y_h = 92 if giant else 86
        # Crisp subtle shadow for instant 4K pop
        dr.text((71, y_h + 4 - bb_h[1]), headline, font=f_head, fill=(10, 18, 32, 190))
        dr.text((68, y_h - bb_h[1]), headline, font=f_head, fill=(*TEXT_ALABASTER, 255))

        arr = np.asarray(im, dtype=np.uint8)
        self._pills[key] = arr
        return arr

    def _make_circular_portrait(self, img_path: Path, diam: int = 260, ring_col: Tuple[int, int, int] = ACCENT_GOLD) -> Image.Image:
        src = Image.open(img_path).convert("RGB")
        # Crop slightly toward upper-center so faces/heads stay cleanly centered
        cropped = ImageOps.fit(src, (diam, diam), method=Image.Resampling.LANCZOS, centering=(0.5, 0.30))
        mask = Image.new("L", (diam, diam), 0)
        ImageDraw.Draw(mask).ellipse((4, 4, diam - 5, diam - 5), fill=255)

        out = Image.new("RGBA", (diam + 16, diam + 16), (0, 0, 0, 0))
        d_out = ImageDraw.Draw(out)
        d_out.ellipse((2, 2, diam + 13, diam + 13), fill=(18, 30, 48, 240), outline=(*ring_col, 245), width=6)
        out.paste(cropped, (8, 8), mask)
        return out

    def _make_single_scientist_card(
        self,
        slug: str,
        name: str,
        years_tag: str,
        discovery_line: str,
        paper_cite: str = "",
        accent: Tuple[int, int, int] = ACCENT_GOLD,
    ) -> np.ndarray:
        cw, ch = 1200, (376 if paper_cite else 326)
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=36, fill=PILL_BG, outline=PILL_BORDER, width=4)

        p_path = PORTRAITS_DIR / f"{slug}.png"
        if p_path.exists():
            med = self._make_circular_portrait(p_path, diam=244, ring_col=accent)
            im.paste(med, (34, (ch - med.height) // 2), med)

        tx = 320
        dr.text((tx, 38), years_tag, font=FONTS["lt_kicker"], fill=(*accent, 255))
        dr.text((tx, 90), name, font=FONTS["p_name"], fill=(*TEXT_ALABASTER, 255))
        dr.text((tx, 166), discovery_line, font=FONTS["p_role"], fill=(*TEXT_MUTED, 255))
        if paper_cite:
            dr.rounded_rectangle((tx, 232, cw - 38, 336), radius=18, fill=(16, 28, 46, 235), outline=(125, 211, 252, 130), width=2)
            dr.text((tx + 22, 246), "LANDMARK PAPER", font=FONTS["wm"], fill=(*ACCENT_CYAN, 255))
            dr.text((tx + 22, 284), paper_cite, font=FONTS["paper_a"], fill=(*TEXT_ALABASTER, 255))
        return np.asarray(im, dtype=np.uint8)

    def _build_scientist_cards(self) -> None:
        # 1. Albert Einstein (chunk_03)
        self._portraits["einstein"] = self._make_single_scientist_card(
            "einstein",
            "Albert Einstein",
            "RELATIVITY OF SIMULTANEITY  •  1905",
            "Moving observers slice 'Right Now' differently",
            "Annalen der Physik 17, 891 (1905)",
            ACCENT_GOLD,
        )

        # 2. Don Page & William K. Wootters Dual Card + 1983 Paper (chunk_04)
        cw, ch = 1360, 440
        im_pw = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im_pw)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=38, fill=PILL_BG, outline=PILL_BORDER, width=4)
        for idx, (slug, nm, aff) in enumerate(
            [
                ("don_page", "Don N. Page", "Univ. of Alberta"),
                ("william_wootters", "William K. Wootters", "Williams College"),
            ]
        ):
            ox = 38 + idx * 655
            p_p = PORTRAITS_DIR / f"{slug}.png"
            if p_p.exists():
                med = self._make_circular_portrait(p_p, diam=198, ring_col=ACCENT_CYAN if idx == 0 else ACCENT_GOLD)
                im_pw.paste(med, (ox, 36), med)
            dr.text((ox + 232, 66), "QUANTUM TIME  •  1983", font=FONTS["wm"], fill=(*ACCENT_GOLD, 255))
            dr.text((ox + 232, 108), nm, font=FONTS["paper_t"], fill=(*TEXT_ALABASTER, 255))
            dr.text((ox + 232, 170), aff, font=FONTS["p_role"], fill=(*TEXT_MUTED, 255))

        # Bottom full-width 1983 Paper strip
        dr.rounded_rectangle((38, 274, cw - 38, ch - 32), radius=22, fill=(15, 26, 44, 242), outline=(253, 224, 71, 175), width=3)
        dr.text((66, 292), "PHYSICAL REVIEW D 27, 2885 (1983)  •  PAGE-WOOTTERS MECHANISM", font=FONTS["paper_j"], fill=(*ACCENT_GOLD, 255))
        dr.text((66, 342), '"Evolution Without Evolution: Dynamics Described by Stationary Observables"', font=FONTS["paper_a"], fill=(*TEXT_ALABASTER, 255))
        self._portraits["page_wootters"] = np.asarray(im_pw, dtype=np.uint8)

        # 3. Rolf Landauer (chunk_08)
        self._portraits["landauer"] = self._make_single_scientist_card(
            "rolf_landauer",
            "Rolf Landauer",
            "IBM RESEARCH  •  1961",
            "Every locked bit of memory pays a heat tax",
            "IBM J. Res. Dev. 5, 183 (1961)  •  Q >= k_B T ln 2",
            ACCENT_GOLD,
        )

        # 4. Itay Griniasty PRL Paper + William G. Unruh Portrait Showcase (chunk_21 — caught from Lacuna rain!)
        cw_g, ch_g = 1420, 446
        im_gu = Image.new("RGBA", (cw_g, ch_g), (0, 0, 0, 0))
        d_gu = ImageDraw.Draw(im_gu)
        d_gu.rounded_rectangle((0, 0, cw_g - 1, ch_g - 1), radius=38, fill=PILL_BG, outline=PILL_BORDER, width=4)

        # Left: Stylized luminous ivory-sapphire Manuscript Page Card caught from the Lacuna sky!
        d_gu.rounded_rectangle((36, 36, 860, ch_g - 36), radius=24, fill=(230, 238, 249, 248), outline=(125, 211, 252, 255), width=4)
        d_gu.text((64, 58), "LACUNA 2.2M PAPER DISCOVERY  •  PHYS. REV. LETT.", font=FONTS["wm"], fill=(24, 62, 118, 255))
        d_gu.text((64, 110), "Classical Analogue of the", font=FONTS["paper_t"], fill=(15, 26, 44, 255))
        d_gu.text((64, 166), "Unruh Effect in Water Waves", font=FONTS["paper_t"], fill=(15, 26, 44, 255))
        d_gu.text((64, 242), "Itay Griniasty, Ulf Leonhardt et al.", font=FONTS["p_role"], fill=(30, 58, 102, 255))
        d_gu.rounded_rectangle((64, 308, 830, 382), radius=14, fill=(24, 42, 68, 245))
        d_gu.text((86, 324), "Wave medium + ripples -> Horizon temperature!", font=FONTS["paper_a"], fill=(*ACCENT_GOLD, 255))

        # Right: William G. Unruh Portrait Medallion
        u_path = PORTRAITS_DIR / "william_unruh.png"
        if u_path.exists():
            med_u = self._make_circular_portrait(u_path, diam=210, ring_col=ACCENT_CYAN)
            im_gu.paste(med_u, (1015, 42), med_u)
        d_gu.text((920, 282), "William G. Unruh", font=FONTS["paper_t"], fill=(*TEXT_ALABASTER, 255))
        d_gu.text((920, 342), "Unruh Horizon Effect (1976)", font=FONTS["p_role"], fill=(*ACCENT_CYAN, 255))
        self._portraits["griniasty_unruh"] = np.asarray(im_gu, dtype=np.uint8)

        # 5. Roy Kerr (chunk_23)
        self._portraits["roy_kerr"] = self._make_single_scientist_card(
            "roy_kerr",
            "Roy P. Kerr",
            "SPINNING BLACK HOLE METRIC  •  1963",
            "Rotating mass twists & drags space into a vortex",
            "Phys. Rev. Lett. 11, 237 (1963)  •  Kerr Geometry",
            ACCENT_CYAN,
        )

    def _build_static_showcase_cards(self) -> None:
        # 1. GPS Highway Drift Mini-Map Card (chunk_15: 11.4 km/day off-road without +38.6 us/day!)
        cw, ch = 1060, 440
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=36, fill=PILL_BG, outline=PILL_BORDER, width=4)
        dr.text((44, 32), "WITHOUT +38.6 us/DAY OFFSET", font=FONTS["lt_kicker"], fill=(*ACCENT_CORAL, 255))
        dr.text((44, 82), "11.4 KM / DAY DRIFT", font=FONTS["hero"], fill=(*TEXT_ALABASTER, 255))

        # Stylized sapphirine highway grid + true emerald route vs drifting coral pin
        mx0, my0, mx1, my1 = 44, 206, cw - 44, ch - 36
        dr.rounded_rectangle((mx0, my0, mx1, my1), radius=22, fill=(16, 28, 46, 245), outline=(125, 211, 252, 120), width=2)
        for gx in range(mx0 + 90, mx1, 110):
            dr.line([(gx, my0), (gx, my1)], fill=(65, 98, 142, 95), width=2)
        for gy in range(my0 + 55, my1, 60):
            dr.line([(mx0, gy), (mx1, gy)], fill=(65, 98, 142, 95), width=2)
        # Highway curve
        hy_mid = (my0 + my1) // 2 + 24
        dr.line([(mx0 + 24, hy_mid), (mx1 - 24, hy_mid)], fill=(52, 211, 153, 235), width=12)
        # Drift vector arrow
        dr.line([(mx0 + 210, hy_mid), (mx1 - 220, my0 + 48)], fill=(251, 146, 60, 245), width=8)
        dr.ellipse((mx0 + 194, hy_mid - 16, mx0 + 226, hy_mid + 16), fill=(52, 211, 153, 255))
        dr.ellipse((mx1 - 238, my0 + 30, mx1 - 202, my0 + 66), fill=(251, 146, 60, 255))
        dr.text((mx1 - 186, my0 + 28), "OFF ROAD!", font=FONTS["graph_lbl"], fill=(*ACCENT_CORAL, 255))
        dr.text((mx0 + 250, hy_mid + 18), "True Highway (+38.6 us Locked)", font=FONTS["paper_a"], fill=(*ACCENT_EMERALD, 255))
        self._custom["gps_drift_map"] = np.asarray(im, dtype=np.uint8)

        # 2. Interactive Science Workbench & stoler.systems Dual Showcase (chunk_25)
        cw2, ch2 = 2480, 1180
        im2 = Image.new("RGBA", (cw2, ch2), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(im2)
        d2.rounded_rectangle((0, 0, cw2 - 1, ch2 - 1), radius=42, fill=PILL_BG, outline=PILL_BORDER, width=5)
        d2.text((58, 36), "OPEN-SOURCE PYTHON SCIENCE WORKBENCH  •  LIVE NOW", font=FONTS["lt_kicker"], fill=(*ACCENT_GOLD, 255))
        d2.text((58, 86), "stoler.systems   •   github.com/dragula22/TNAP-Theories", font=FONTS["lt_title"], fill=(*TEXT_ALABASTER, 255))

        p_tab7 = ARTIFACT_DIR / "test_07_episode1_gps_and_landauer_lab.png"
        p_cmb = ARTIFACT_DIR / "cmb_third_bump_explained.png"
        for idx_p, (pp, cap) in enumerate(
            [
                (p_tab7, "TAB 7: Interactive GPS Altitude Slider & Page-Wootters QuTiP Engine"),
                (p_cmb, "TAB 6.2 UPDATE: 99.92% CMB 3rd-Peak Acoustic Rescue (Zero Free Knobs)"),
            ]
        ):
            bx = 58 + idx_p * 1200
            by = 190
            bw, bh = 1164, 920
            d2.rounded_rectangle((bx, by, bx + bw, by + bh), radius=26, fill=(16, 26, 44, 248), outline=(125, 211, 252, 165), width=3)
            if pp.exists():
                sub_im = Image.open(pp).convert("RGB")
                sub_fit = ImageOps.contain(sub_im, (bw - 32, bh - 96), method=Image.Resampling.LANCZOS)
                im2.paste(sub_fit, (bx + (bw - sub_fit.width) // 2, by + 20))
            cap_col = ACCENT_CYAN if idx_p == 0 else ACCENT_EMERALD
            d2.text((bx + 28, by + bh - 62), cap, font=FONTS["paper_a"], fill=(*cap_col, 255))
        self._custom["workbench_showcase"] = np.asarray(im2, dtype=np.uint8)

        # 3. 6-Chapter Living Recap Scorecard & Discord Community Card (chunk_26)
        cw3, ch3 = 1860, 880
        im3 = Image.new("RGBA", (cw3, ch3), (0, 0, 0, 0))
        d3 = ImageDraw.Draw(im3)
        d3.rounded_rectangle((0, 0, cw3 - 1, ch3 - 1), radius=40, fill=PILL_BG, outline=PILL_BORDER, width=5)
        d3.text((56, 38), "LIVING SERIES SCORECARD  ->  POST-CHAPTERS RECAP VIDEO", font=FONTS["lt_kicker"], fill=(*ACCENT_GOLD, 255))
        d3.text((56, 92), "Every Discovery, Stress-Test & Viewer Critique Logged", font=FONTS["lt_title"], fill=(*TEXT_ALABASTER, 255))

        rows = [
            ("EPISODE 1 (TODAY)", "Page-Wootters 10^-15  •  GPS +38.6 us  •  Planck Spool 1.000000", ACCENT_EMERALD),
            ("EPISODE 2 (NEXT)", "Upside-Down Big Bang Waist  •  Quiet CMB Sky  •  Antimatter Twin", ACCENT_CYAN),
            ("CHAPTERS 3 - 6", "Double-Slit Wave  •  Galaxy Pleats (99.92% 3rd Peak)  •  Red-Team Lab", ACCENT_GOLD),
            ("FINALE MILESTONE", "Full Recap & Living-Update Video + Discord Community Review!", ACCENT_EMERALD),
        ]
        for r_i, (k_txt, v_txt, col_r) in enumerate(rows):
            ry = 200 + r_i * 152
            d3.rounded_rectangle((56, ry, cw3 - 56, ry + 130), radius=22, fill=(16, 28, 46, 240), outline=(*col_r, 175), width=3)
            d3.text((88, ry + 18), k_txt, font=FONTS["paper_j"], fill=(*col_r, 255))
            d3.text((88, ry + 66), v_txt, font=FONTS["p_role"], fill=(*TEXT_ALABASTER, 255))
        self._custom["living_scorecard"] = np.asarray(im3, dtype=np.uint8)


# ---------------------------------------------------------------------------
# Live Animated 4K GPS Altitude Crossover Graph (`chunk_16`)
# ---------------------------------------------------------------------------

def draw_gps_crossover_graph_4k(frame: np.ndarray, progress_01: float, opacity: float) -> None:
    """Draws the animated Tab 7 GPS Altitude Crossover Curve (`ISS -28 us` -> `3,189 km Zero` -> `GPS +38.6 us`)."""
    if opacity <= 0.01:
        return
    gw, gh = 1660, 1020
    im = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, gw - 1, gh - 1), radius=38, fill=PILL_BG, outline=PILL_BORDER, width=4)

    dr.text((52, 34), "SCIENCE WORKBENCH TAB 7  •  ALTITUDE CROSSOVER", font=FONTS["lt_kicker"], fill=(*ACCENT_GOLD, 255))
    dr.text((52, 86), "Speed Slowing vs. Looser Weave Speed-Up", font=FONTS["graph_t"], fill=(*TEXT_ALABASTER, 255))

    px0, py0, px1, py1 = 150, 210, gw - 74, gh - 118
    pw, ph = px1 - px0, py1 - py0
    dr.rounded_rectangle((px0, py0, px1, py1), radius=18, fill=(15, 25, 42, 242), outline=(125, 211, 252, 110), width=2)

    # Y-axis range: -40 to +55 us/day
    y_min, y_max = -40.0, 55.0
    h_max = 25000.0  # km

    def map_pt(h_km: float, us_val: float) -> Tuple[int, int]:
        ux = max(0.0, min(1.0, h_km / h_max))
        uy = max(0.0, min(1.0, (us_val - y_min) / (y_max - y_min)))
        return int(px0 + ux * pw), int(py1 - uy * ph)

    # Zero horizontal line!
    _, y_zero = map_pt(0.0, 0.0)
    dr.line([(px0, y_zero), (px1, y_zero)], fill=(191, 219, 254, 175), width=3)
    dr.text((40, y_zero - 20), "0 us", font=FONTS["graph_ax"], fill=(*TEXT_ALABASTER, 230))
    for y_tick in (-30, +20, +40):
        _, yt = map_pt(0.0, float(y_tick))
        dr.line([(px0, yt), (px1, yt)], fill=(75, 108, 152, 70), width=2)
        dr.text((28, yt - 18), f"{y_tick:+d}", font=FONTS["graph_ax"], fill=(*TEXT_MUTED, 195))

    for h_tick, lbl in ((3189, "3,189 km"), (10000, "10,000 km"), (20184, "20,184 km (GPS)")):
        xt, _ = map_pt(float(h_tick), 0.0)
        dr.line([(xt, py0), (xt, py1)], fill=(75, 108, 152, 75), width=2)
        dr.text((xt - 65, py1 + 18), lbl, font=FONTS["graph_ax"], fill=(*TEXT_MUTED, 225))

    # Physics formula: R_E = 6378.137 km, GM = 3.986004418e14 m^3/s^2
    R_E = 6378.137
    # Surface gravity timescale factor: GM/(R_E*c^2) * 86400e6 = 60.06 us/day
    K_SURF = 60.06
    h_sweep = max(250.0, h_max * smootherstep01(progress_01))
    hs = np.linspace(150.0, h_sweep, 180)

    pts_sr, pts_gr, pts_net = [], [], []
    for h_v in hs:
        ratio = R_E / (R_E + h_v)
        gr = K_SURF * (1.0 - ratio)
        sr = -0.5 * K_SURF * ratio
        net = gr + sr
        pts_sr.append(map_pt(float(h_v), float(sr)))
        pts_gr.append(map_pt(float(h_v), float(gr)))
        pts_net.append(map_pt(float(h_v), float(net)))

    if len(pts_net) >= 2:
        dr.line(pts_sr, fill=(251, 146, 60, 185), width=5)
        dr.line(pts_gr, fill=(125, 211, 252, 185), width=5)
        dr.line(pts_net, fill=(253, 224, 71, 255), width=10)

    # Highlight 3 landmark dots as the curve sweeps past them!
    landmarks = [
        (400.0, -28.2, "ISS (400 km): -28 us/day", ACCENT_CORAL, (26, 18)),
        (3189.0, 0.0, "ZERO-CROSSING: 3,189 km", ACCENT_EMERALD, (24, -56)),
        (20184.0, 38.6, "GPS: +38.6 us/day", ACCENT_GOLD, (-360, -64)),
    ]
    for h_m, v_m, txt_m, col_m, (dx_l, dy_l) in landmarks:
        if h_sweep >= h_m:
            mx, my = map_pt(h_m, v_m)
            dr.ellipse((mx - 15, my - 15, mx + 15, my + 15), fill=(*col_m, 255), outline=(255, 255, 255, 240), width=4)
            dr.text((mx + dx_l, my + dy_l), txt_m, font=FONTS["graph_lbl"], fill=(*col_m, 255))

    blit_rgba_fast(frame, np.asarray(im, dtype=np.uint8), W4K - gw - 88, 560, opacity=opacity)


# ---------------------------------------------------------------------------
# Cinema B-Roll Cache & Anti-Flashbang Option A+ 4K Upscaler
# ---------------------------------------------------------------------------

class Ep1CinemaClipCache:
    """Decodes Episode 1 `1080p` cinema MP4s lazily at `2048x1152` for smooth Ken Burns 4K upscaling."""

    OV_W, OV_H = 2048, 1152

    def __init__(self, ffmpeg_exe: str) -> None:
        self.ffmpeg_exe = ffmpeg_exe
        self._loaded: Dict[str, List[np.ndarray]] = {}

    def get_frame(
        self,
        clip_name: str,
        local_t: float,
        dur_win: float,
        zoom_dir: int = 1,
        playback_rate: float = 1.0,
    ) -> Optional[np.ndarray]:
        p = CINEMA_EP1_DIR / clip_name
        if not p.exists():
            p = CINEMA_EP0_DIR / clip_name
        if not p.exists():
            return None

        if clip_name not in self._loaded:
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

        idx = min(len(frames) - 1, max(0, int(round(local_t * playback_rate * FPS))))
        src = frames[idx]

        # Subtle Ken Burns crop (`2048x1152` -> `1920x1080`)
        u = max(0.0, min(1.0, local_t / max(0.2, dur_win)))
        if zoom_dir < 0:
            u = 1.0 - u
        max_dx = self.OV_W - 1920
        max_dy = self.OV_H - 1080
        ox = int(round(0.5 * max_dx * u))
        oy = int(round(0.5 * max_dy * u))
        return src[oy : oy + 1080, ox : ox + 1920]


class GPUBRoll4KOptionAPlus:
    """
    Upscales `1920x1080` cinema B-roll to `3840x2160` on RTX 5080 via Bicubic + Unsharp Crispener,
    AND applies a soft anti-flashbang highlight shoulder (`<= 236` soft alabaster) + Option A+ shadow tint
    so every B-roll shot blends seamlessly into Luminous Sapphire Slate!
    """

    def __init__(self, device: torch.device) -> None:
        self.dev = device
        self._pinned = torch.empty((H4K, W4K, 3), dtype=torch.uint8, pin_memory=(device.type == "cuda"))
        self._tint_floor = torch.tensor([18.0, 28.0, 44.0], device=device).view(1, 3, 1, 1)

    def upscale_and_blend(
        self,
        broll_1080: np.ndarray,
        gpu_4k: Optional[np.ndarray] = None,
        broll_alpha: float = 1.0,
    ) -> np.ndarray:
        arr_in = broll_1080 if broll_1080.flags.writeable else broll_1080.copy()
        t_in = torch.from_numpy(arr_in).to(self.dev, non_blocking=False).permute(2, 0, 1).unsqueeze(0).float()
        up = F.interpolate(t_in, size=(H4K, W4K), mode="bicubic", align_corners=False)
        blur = F.avg_pool2d(F.pad(up, (1, 1, 1, 1), mode="replicate"), kernel_size=3, stride=1)
        sharp = up + 0.30 * (up - blur)

        # Soft anti-flashbang shoulder above 205 -> gently rolls highlights to <= 236 soft alabaster!
        over = F.relu(sharp - 205.0)
        graded = torch.where(sharp > 205.0, 205.0 + 31.0 * torch.tanh(over / 48.0), sharp)
        # Lift pitch-black B-roll shadows gently toward Sapphire Slate
        graded = torch.maximum(graded, self._tint_floor * 0.75)
        graded_hwc = torch.clamp(graded, 0.0, 238.0).squeeze(0).permute(1, 2, 0)

        if gpu_4k is not None and broll_alpha < 0.995:
            t_gpu = torch.from_numpy(gpu_4k).to(self.dev, non_blocking=False).float()
            mixed = torch.clamp(graded_hwc * broll_alpha + t_gpu * (1.0 - broll_alpha), 0.0, 255.0).to(torch.uint8)
            self._pinned.copy_(mixed, non_blocking=False)
        else:
            self._pinned.copy_(graded_hwc.to(torch.uint8), non_blocking=False)
        return self._pinned.numpy()


def get_ep1_broll_windows(scene: dict) -> List[Tuple[float, float, str, int, float]]:
    """Returns `(w_start, w_end, clip_filename, zoom_dir, playback_rate)` in scene-local seconds."""
    sid = scene["id"]
    if sid == "scene02":
        ch07 = _find_chunk(scene, "chunk_07")
        s0 = ch07["local_start"] if ch07 else 0.7
        return [
            # "Whether it's a photograph on your phone, a crater on the moon..."
            (s0 + 11.4, s0 + 16.8, "ep1_moon_asteroid_crater_memory.mp4", 1, 1.0),
            # "...or a new synapse firing in your brain, writing down a memory..."
            (s0 + 16.8, s0 + 25.4, "ep1_brain_neurons_synapse_memory.mp4", 1, 0.92),
        ]
    if sid == "scene05":
        ch21 = _find_chunk(scene, "chunk_21")
        s21 = ch21["local_start"] if ch21 else 0.7
        return [
            # "...using Lacuna, a new AI research map covering over 2.2 million scientific papers..."
            (s21 + 3.4, s21 + 15.2, "ep1_lacuna_papers_rain_umbrellas.mp4", 1, 0.66),
            # "...proving even in a real water wave laboratory tank... Unruh horizon temperature"
            (s21 + 22.8, s21 + 35.4, "ep1_water_wave_unruh_tank.mp4", 1, 0.65),
        ]
    return []


# ---------------------------------------------------------------------------
# Chapter Lower-Thirds & Chunk-Synced Giant 4K Keynote Overlays
# ---------------------------------------------------------------------------

def draw_chapter_header_and_lower_third_4k(
    frame: np.ndarray,
    lib: OverlayLibrary4K,
    scene: dict,
    local_t: float,
) -> None:
    sid = scene["id"]
    if sid == "intro00":
        # Opening Episode 1 Hero Card (0.3s -> 3.4s)
        vis = smoothstep01((local_t - 0.15) / 0.45) * smoothstep01((3.50 - local_t) / 0.45)
        pill = lib.get_keynote_pill(
            "THEORETICALLY NOT A PHYSICIST  •  EPISODE 1",
            "IS TIME EVEN REAL?",
            ACCENT_GOLD,
            giant=True,
        )
        blit_rgba_fast(frame, pill, (W4K - pill.shape[1]) // 2, H4K - pill.shape[0] - 130, opacity=vis)
        return

    # Subtle top-left smoked-sapphire breadcrumb pill
    wm_key = f"wm_{sid}"
    if wm_key not in lib._custom:
        wm_txt = f"{scene['chapter']}  •  {scene['title']}"
        dummy = ImageDraw.Draw(Image.new("RGBA", (16, 16)))
        bb = dummy.textbbox((0, 0), wm_txt, font=FONTS["wm"])
        pw = (bb[2] - bb[0]) + 64
        ph = 72
        im_w = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        dw = ImageDraw.Draw(im_w)
        dw.rounded_rectangle((0, 0, pw - 1, ph - 1), radius=36, fill=(20, 32, 52, 182), outline=(125, 211, 252, 125), width=2)
        dw.text((32, 16), wm_txt, font=FONTS["wm"], fill=(219, 234, 254, 228))
        lib._custom[wm_key] = np.asarray(im_w, dtype=np.uint8)
    blit_rgba_fast(frame, lib._custom[wm_key], 76, 62, opacity=1.0)

    # Opening 6.8s Chapter Lower-Third Banner
    if 0.35 <= local_t <= 7.20:
        vis = smootherstep01((local_t - 0.35) / 0.55) * smootherstep01((7.20 - local_t) / 0.60)
        lt_key = f"lt_{sid}"
        if lt_key not in lib._custom:
            cw, ch = 1980, 224
            im_l = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dl = ImageDraw.Draw(im_l)
            dl.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=34, fill=PILL_BG, outline=PILL_BORDER, width=4)
            dl.rounded_rectangle((30, 32, 44, ch - 32), radius=7, fill=(*ACCENT_GOLD, 255))
            dl.text((74, 34), scene["subtitle_tag"], font=FONTS["lt_kicker"], fill=(*ACCENT_CYAN, 255))
            dl.text((74, 96), scene["title"], font=FONTS["lt_title"], fill=(*TEXT_ALABASTER, 255))
            lib._custom[lt_key] = np.asarray(im_l, dtype=np.uint8)
        x_slide = 76 - int((1.0 - vis) * 72)
        blit_rgba_fast(frame, lib._custom[lt_key], x_slide, 162, opacity=vis)


def _draw_timed_pill(
    frame: np.ndarray,
    lib: OverlayLibrary4K,
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
        x, y = (W4K - pw) // 2, H4K - ph - 118
    elif pos == "top_right":
        x, y = W4K - pw - 86, 162
    else:  # bottom_left
        x, y = 86, H4K - ph - 118
    y_anim = y + int((1.0 - vis) * 26)
    blit_rgba_fast(frame, pill, x, y_anim, opacity=vis)


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
    blit_rgba_fast(frame, card_arr, x, y + int((1.0 - vis) * 28), opacity=vis)


def draw_scene_keynote_overlays_4k(
    frame: np.ndarray,
    lib: OverlayLibrary4K,
    scene: dict,
    local_t: float,
) -> None:
    """
    Strictly ONE clean focal Keynote badge or Portrait/Paper card per spoken beat —
    giant 124px crisp typography, max 2–5 words per headline, ZERO subtitle clutter!
    """
    sid = scene["id"]

    if sid == "scene00":
        c0 = _find_chunk(scene, "chunk_00")
        c1 = _find_chunk(scene, "chunk_01")
        c2 = _find_chunk(scene, "chunk_02")
        s0, e0 = (c0["local_start"], c0["local_end"]) if c0 else (0.25, 30.8)
        s1, e1 = (c1["local_start"], c1["local_end"]) if c1 else (32.2, 61.1)
        s2, e2 = (c2["local_start"], c2["local_end"]) if c2 else (62.6, 89.9)

        _draw_timed_pill(frame, lib, local_t, s0 + 13.5, e0, "6-PART CHAPTER DEEP DIVE", "ONE CLAIM AT A TIME", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s1 + 3.0, s1 + 11.5, "CHAPTER 1 CORE QUESTION", "IS TIME EVEN REAL?", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s1 + 12.2, e1, "4D VINYL RECORD UNIVERSE", "ZERO OUTSIDE MOTION", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s2 + 4.5, s2 + 11.2, "CHECK #1  •  MEMORY", "PAST VS. FUTURE", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s2 + 11.6, s2 + 20.5, "CHECK #2  •  20,184 KM", "+38.6 us / DAY FAST", ACCENT_EMERALD)
        _draw_timed_pill(frame, lib, local_t, s2 + 20.9, e2, "CHECK #3  •  RED TEAM", "SPINNING BLACK HOLES", ACCENT_CYAN)

    elif sid == "scene01":
        c3 = _find_chunk(scene, "chunk_03")
        c4 = _find_chunk(scene, "chunk_04")
        c5 = _find_chunk(scene, "chunk_05")
        c6 = _find_chunk(scene, "chunk_06")
        s3, e3 = (c3["local_start"], c3["local_end"]) if c3 else (0.7, 34.6)
        s4, e4 = (c4["local_start"], c4["local_end"]) if c4 else (36.0, 69.9)
        s5, e5 = (c5["local_start"], c5["local_end"]) if c5 else (71.3, 104.0)
        s6, e6 = (c6["local_start"], c6["local_end"]) if c6 else (105.7, 132.2)

        _draw_timed_pill(frame, lib, local_t, s3 + 9.0, s3 + 17.6, "HOW FAST DOES TIME FLOW?", "1 SEC / 1 SEC = CIRCLE", ACCENT_GOLD)
        # Albert Einstein Portrait Card!
        ec = lib._portraits["einstein"]
        _draw_timed_card(frame, ec, local_t, s3 + 18.2, e3, W4K - ec.shape[1] - 88, 170)
        _draw_timed_pill(frame, lib, local_t, s3 + 22.0, e3, "TILTED 'NOW' SLICES", "NO UNIVERSAL 'NOW'", ACCENT_CYAN)

        # Don Page & William K. Wootters Dual Portrait + 1983 Paper Card!
        pwc = lib._portraits["page_wootters"]
        _draw_timed_card(frame, pwc, local_t, s4 + 1.4, s4 + 21.5, W4K - pwc.shape[1] - 84, 166)
        _draw_timed_pill(frame, lib, local_t, s4 + 22.0, e4, "QUTIP QUANTUM WORKBENCH", "OUTSIDE MOTION = 0", ACCENT_GOLD)

        _draw_timed_pill(frame, lib, local_t, s5 + 2.5, s5 + 15.0, "INSIDE LOCAL OBSERVER CHANNEL", "WEAVE SPRINGS TO LIFE", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s5 + 16.0, e5, "OBSERVER CHANNELS A & B", "15-DECIMAL MATCH", ACCENT_EMERALD)

        _draw_timed_pill(frame, lib, local_t, s6 + 15.0, e6, "THE SKEPTIC'S RIDDLE", "WHY REMEMBER ONLY PAST?", ACCENT_GOLD)

    elif sid == "scene02":
        c7 = _find_chunk(scene, "chunk_07")
        c8 = _find_chunk(scene, "chunk_08")
        c9 = _find_chunk(scene, "chunk_09")
        c10 = _find_chunk(scene, "chunk_10")
        c11 = _find_chunk(scene, "chunk_11")
        s7, e7 = (c7["local_start"], c7["local_end"]) if c7 else (0.7, 26.6)
        s8, e8 = (c8["local_start"], c8["local_end"]) if c8 else (27.9, 60.7)
        s9, e9 = (c9["local_start"], c9["local_end"]) if c9 else (62.1, 93.9)
        s10, e10 = (c10["local_start"], c10["local_end"]) if c10 else (95.3, 127.0)
        s11, e11 = (c11["local_start"], c11["local_end"]) if c11 else (128.5, 164.0)

        _draw_timed_pill(frame, lib, local_t, s7 + 11.4, s7 + 16.7, "PHYSICAL MEMORY IN ROCK", "LUNAR IMPACT CRATER", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s7 + 16.9, e7, "PHYSICAL MEMORY IN BRAIN", "LOCKED SYNAPSE STATE", ACCENT_CYAN)

        # Rolf Landauer Portrait + 1961 IBM Paper Card!
        lc = lib._portraits["landauer"]
        _draw_timed_card(frame, lc, local_t, s8 + 1.2, s8 + 19.5, W4K - lc.shape[1] - 88, 170)
        _draw_timed_pill(frame, lib, local_t, s8 + 19.8, e8, "LANDAUER'S HEAT TAX", "k_B T ln 2 PER BIT", ACCENT_GOLD)

        _draw_timed_pill(frame, lib, local_t, s9 + 4.5, s9 + 16.0, "BIG BANG WAIST -> OUTER RIM", "SMOOTH TO TANGLED", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s9 + 18.0, e9, "THERMODYNAMIC ARROW", "MEMORIES ADD TANGLES", ACCENT_GOLD)

        _draw_timed_pill(frame, lib, local_t, s10 + 7.0, s10 + 19.5, "WHY WE REMEMBER YESTERDAY", "HEAT TAX PAID OUTWARD", ACCENT_EMERALD)
        _draw_timed_pill(frame, lib, local_t, s10 + 20.2, e10, "UNPAID FOOTPRINTS AHEAD", "THE OPEN FUTURE", ACCENT_CYAN)

        _draw_timed_pill(frame, lib, local_t, s11 + 8.5, e11, "TWO-WING COSMIC HOURGLASS", "PAST = SMOOTH WAIST", ACCENT_GOLD)

    elif sid == "scene03":
        c12 = _find_chunk(scene, "chunk_12")
        c13 = _find_chunk(scene, "chunk_13")
        c14 = _find_chunk(scene, "chunk_14")
        c15 = _find_chunk(scene, "chunk_15")
        c16 = _find_chunk(scene, "chunk_16")
        s12, e12 = (c12["local_start"], c12["local_end"]) if c12 else (0.7, 25.9)
        s13, e13 = (c13["local_start"], c13["local_end"]) if c13 else (27.3, 57.5)
        s14, e14 = (c14["local_start"], c14["local_end"]) if c14 else (58.9, 87.3)
        s15, e15 = (c15["local_start"], c15["local_end"]) if c15 else (88.7, 121.1)
        s16, e16 = (c16["local_start"], c16["local_end"]) if c16 else (122.8, 154.9)

        _draw_timed_pill(frame, lib, local_t, s12 + 12.0, e12, "HARD ENGINEERING BENCHMARK", "REAL ORBITING CLOCKS", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s13 + 4.0, s13 + 16.5, "REFRACTIVE WEAVE GRADIENT", "DENSE LOW  •  LOOSE HIGH", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s13 + 17.5, e13, "SEA-LEVEL ATOMIC CLOCK", "TICKS SLIGHTLY SLOWER", ACCENT_CYAN)

        _draw_timed_pill(frame, lib, local_t, s14 + 2.0, s14 + 13.0, "31 GPS SATELLITES IN ORBIT", "20,184 KM ALTITUDE", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s14 + 16.5, e14, "ORBITAL SPEED STRETCH (SR)", "-7.2 us / DAY SLOWER", ACCENT_CORAL)

        _draw_timed_pill(frame, lib, local_t, s15 + 3.5, s15 + 12.2, "LOOSER HIGH WEAVE (GR)", "+45.8 us / DAY FASTER", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s15 + 12.6, s15 + 23.2, "-7.2  +  45.8  NET GAIN", "+38.6 us / DAY!", ACCENT_EMERALD)

        # Highway drift map card at end of chunk_15!
        dm = lib._custom["gps_drift_map"]
        _draw_timed_card(frame, dm, local_t, s15 + 23.4, e15 + 1.0, W4K - dm.shape[1] - 88, H4K - dm.shape[0] - 110)

        # Live Animated Altitude Crossover Graph across chunk_16!
        if s16 + 0.8 <= local_t <= e16 + 1.2:
            vis_g = smoothstep01((local_t - (s16 + 0.8)) / 0.6) * smoothstep01((e16 + 1.2 - local_t) / 0.6)
            prog_g = max(0.0, min(1.0, (local_t - (s16 + 2.5)) / max(1.0, (e16 - s16 - 5.5))))
            draw_gps_crossover_graph_4k(frame, prog_g, vis_g)
        _draw_timed_pill(frame, lib, local_t, s16 + 22.0, e16 + 0.8, "EXACT HALF EARTH RADIUS", "3,189 KM = ZERO DRIFT", ACCENT_EMERALD, pos="bottom_left", giant=False)

    elif sid == "scene04":
        c17 = _find_chunk(scene, "chunk_17")
        c18 = _find_chunk(scene, "chunk_18")
        c19 = _find_chunk(scene, "chunk_19")
        c20 = _find_chunk(scene, "chunk_20")
        s17, e17 = (c17["local_start"], c17["local_end"]) if c17 else (0.7, 22.6)
        s18, e18 = (c18["local_start"], c18["local_end"]) if c18 else (24.0, 55.7)
        s19, e19 = (c19["local_start"], c19["local_end"]) if c19 else (57.2, 92.4)
        s20, e20 = (c20["local_start"], c20["local_end"]) if c20 else (94.0, 122.2)

        _draw_timed_pill(frame, lib, local_t, s17 + 12.0, e17, "EXPONENTIAL WEAVE METRIC", "3 STRONG-FIELD TESTS", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s18 + 3.0, s18 + 16.0, "MERCURY ORBIT PRECESSION", '42.98" / CENTURY', ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s18 + 17.5, e18, "NASA CASSINI RADIO DELAY", "MATCHES TO ±0.002%", ACCENT_EMERALD)

        _draw_timed_pill(frame, lib, local_t, s19 + 4.5, s19 + 16.0, "AUGUST 2017  •  GW170817", "130M LIGHT-YEARS", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s19 + 23.0, e19 + 0.8, "LIGHT + GRAVITY ARRIVAL", "1.7 SEC PHOTO FINISH", ACCENT_EMERALD)

        _draw_timed_pill(frame, lib, local_t, s20 + 8.5, s20 + 19.0, "ONE SINGLE TAUT WEAVE", "SAME SILK THREADS", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s20 + 19.5, e20, "WAVE SPEED LOCKSTEP", "1 PART IN 10^15", ACCENT_GOLD)

    elif sid == "scene05":
        c21 = _find_chunk(scene, "chunk_21")
        c22 = _find_chunk(scene, "chunk_22")
        c23 = _find_chunk(scene, "chunk_23")
        c23b = _find_chunk(scene, "chunk_23b")
        c24 = _find_chunk(scene, "chunk_24")
        s21, e21 = (c21["local_start"], c21["local_end"]) if c21 else (0.7, 36.6)
        s22, e22 = (c22["local_start"], c22["local_end"]) if c22 else (38.1, 56.8)
        s23, e23 = (c23["local_start"], c23["local_end"]) if c23 else (58.2, 93.4)
        s23b, e23b = (c23b["local_start"], c23b["local_end"]) if c23b else (95.0, 136.8)
        s24, e24 = (c24["local_start"], c24["local_end"]) if c24 else (138.4, 174.6)

        _draw_timed_pill(frame, lib, local_t, s21 + 4.2, s21 + 12.2, "LACUNA AI RESEARCH MAP", "2.2M+ PHYSICS PAPERS", ACCENT_GOLD)
        # Smooth transition from falling Lacuna page -> Griniasty PRL Paper + Unruh Portrait Card!
        guc = lib._portraits["griniasty_unruh"]
        _draw_timed_card(frame, guc, local_t, s21 + 12.6, s21 + 24.5, (W4K - guc.shape[1]) // 2, 168)
        _draw_timed_pill(frame, lib, local_t, s21 + 25.0, e21, "LABORATORY WATER WAVE TANK", "UNRUH WAVE HORIZON", ACCENT_CYAN)

        _draw_timed_pill(frame, lib, local_t, s22 + 6.5, e22, "HONEST RED-TEAM AUDIT", "WHERE IT GETS TOUGH", ACCENT_CORAL)

        # Roy Kerr Portrait Card + Relativistic Spinning Black Hole!
        rkc = lib._portraits["roy_kerr"]
        _draw_timed_card(frame, rkc, local_t, s23 + 12.5, s23 + 26.5, W4K - rkc.shape[1] - 86, 168)
        _draw_timed_pill(frame, lib, local_t, s23 + 27.0, e23, "HURDLE #1  •  KERR SPIN", "SUPERFLUID VORTEX SWIRL", ACCENT_CYAN)

        # =========================================================================
        # CHUNK 23B KEYNOTE CALLOUTS: Self-Healing Planck Slip + 1.000000 Spool!
        # =========================================================================
        _draw_timed_pill(frame, lib, local_t, s23b + 4.5, s23b + 12.2, "NEW EPISODE 1 INSIGHT", "WHY DON'T THREADS SNAP?", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s23b + 12.6, s23b + 26.5, "QUANTUM PHASE-SLIP HEALING", "MELT  •  SLIP  •  RE-WELD", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s23b + 27.0, s23b + 35.0, "PLANCK-TENSION FISHING REEL", "WINDING SPACE ON SPOOL", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s23b + 35.3, e23b + 1.1, "R = 2GM / c²  HORIZON MATCH", "1.000000  (6 DECIMALS!)", ACCENT_EMERALD)

        _draw_timed_pill(frame, lib, local_t, s24 + 12.5, s24 + 24.5, "HURDLE #2  •  NO SINGULARITY", "DENSE FROZEN THROAT", ACCENT_GOLD)
        _draw_timed_pill(frame, lib, local_t, s24 + 25.0, e24, "FALSIFIABLE PREDICTION", "RINGDOWN WAVE ECHO?", ACCENT_CYAN)

    elif sid == "scene06":
        c25 = _find_chunk(scene, "chunk_25")
        c26 = _find_chunk(scene, "chunk_26")
        c27 = _find_chunk(scene, "chunk_27")
        s25, e25 = (c25["local_start"], c25["local_end"]) if c25 else (0.7, 27.5)
        s26, e26 = (c26["local_start"], c26["local_end"]) if c26 else (28.9, 59.9)
        s27, e27 = (c27["local_start"], c27["local_end"]) if c27 else (61.5, 87.1)

        wb = lib._custom["workbench_showcase"]
        _draw_timed_card(frame, wb, local_t, s25 + 1.5, e25 + 0.5, (W4K - wb.shape[1]) // 2, 460)

        sc_card = lib._custom["living_scorecard"]
        _draw_timed_card(frame, sc_card, local_t, s26 + 1.5, s26 + 21.5, (W4K - sc_card.shape[1]) // 2, 480)
        _draw_timed_pill(frame, lib, local_t, s26 + 22.0, e26, "COMMUNITY CHECK  •  COMMENTS", "WANT A TNAP DISCORD?", ACCENT_GOLD)

        _draw_timed_pill(frame, lib, local_t, s27 + 1.5, s27 + 18.0, "NEXT TIME  •  EPISODE 2", "UPSIDE-DOWN BIG BANG", ACCENT_CYAN)
        _draw_timed_pill(frame, lib, local_t, s27 + 20.5, e27 + 1.5, "THANKS FOR WATCHING!", "STAY INQUISITIVE", ACCENT_GOLD)


def compose_ep1_frame_4k(
    director: Episode1GPU3DDirector,
    clip_cache: Ep1CinemaClipCache,
    upscaler: GPUBRoll4KOptionAPlus,
    lib: OverlayLibrary4K,
    scene: dict,
    local_t: float,
) -> np.ndarray:
    sid = scene["id"]
    dur = float(scene["duration_sec"])

    broll_1080: Optional[np.ndarray] = None
    broll_alpha = 0.0
    xf = 0.70

    for w0, w1, cname, zdir, prate in get_ep1_broll_windows(scene):
        if w0 - xf <= local_t <= w1 + xf:
            f_in = smoothstep01((local_t - (w0 - xf)) / (2.0 * xf))
            f_out = smoothstep01(((w1 + xf) - local_t) / (2.0 * xf))
            broll_alpha = max(0.0, min(1.0, f_in * f_out))
            if broll_alpha > 0.01:
                broll_1080 = clip_cache.get_frame(cname, max(0.0, local_t - w0), w1 - w0, zoom_dir=zdir, playback_rate=prate)
            break

    if broll_1080 is not None and broll_alpha >= 0.995:
        frame = upscaler.upscale_and_blend(broll_1080, None, 1.0)
    elif broll_1080 is not None and broll_alpha > 0.01:
        gpu_4k = director.render_scene_frame(scene, local_t)
        frame = upscaler.upscale_and_blend(broll_1080, gpu_4k, broll_alpha)
    else:
        frame = director.render_scene_frame(scene, local_t)

    draw_chapter_header_and_lower_third_4k(frame, lib, scene, local_t)
    draw_scene_keynote_overlays_4k(frame, lib, scene, local_t)

    # Gentle fade-in at 0:00 and graceful fade-out at the very end of Chapter 6
    if sid == "intro00" and local_t < 0.65:
        fade_in = max(0.0, min(1.0, local_t / 0.65))
        np.multiply(frame, fade_in, out=frame, casting="unsafe")
    elif sid == "scene06" and local_t > dur - 2.4:
        fade_out = max(0.0, min(1.0, (dur - local_t) / 2.4))
        np.multiply(frame, fade_out, out=frame, casting="unsafe")

    return frame


def main() -> None:
    qa_only = "--qa-only" in sys.argv
    t0 = time.time()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    print("Initializing Episode 1 Native 4K UHD (3840x2160) GPU Director & Overlay Library...", flush=True)
    director = Episode1GPU3DDirector()
    clip_cache = Ep1CinemaClipCache(ffmpeg_exe)
    upscaler = GPUBRoll4KOptionAPlus(director.dev)
    lib = OverlayLibrary4K()

    sc_map = {s["id"]: s for s in manifest["scenes"]}

    if qa_only:
        qa_dir = EP1_DIR / "qa_frames_4k"
        qa_dir.mkdir(exist_ok=True)
        samples = [
            ("qa01_vinyl_illusion", sc_map["scene00"], _find_chunk(sc_map["scene00"], "chunk_01")["local_start"] + 16.0),
            ("qa02_page_wootters_portraits", sc_map["scene01"], _find_chunk(sc_map["scene01"], "chunk_04")["local_start"] + 8.0),
            ("qa03_observer_channels_match", sc_map["scene01"], _find_chunk(sc_map["scene01"], "chunk_05")["local_start"] + 21.0),
            ("qa04_landauer_portrait_heat_tax", sc_map["scene02"], _find_chunk(sc_map["scene02"], "chunk_08")["local_start"] + 10.0),
            ("qa05_gps_crossover_graph", sc_map["scene03"], _find_chunk(sc_map["scene03"], "chunk_16")["local_start"] + 26.0),
            ("qa06_lacuna_griniasty_unruh", sc_map["scene05"], _find_chunk(sc_map["scene05"], "chunk_21")["local_start"] + 16.5),
            ("qa07_kerr_black_hole_roy_kerr", sc_map["scene05"], _find_chunk(sc_map["scene05"], "chunk_23")["local_start"] + 18.0),
            ("qa08_chunk23b_fishing_reel_1000000", sc_map["scene05"], _find_chunk(sc_map["scene05"], "chunk_23b")["local_start"] + 37.5),
        ]
        grid = Image.new("RGB", (3840, 2160), (24, 38, 60))
        for idx, (tag, sc_obj, lt) in enumerate(samples):
            fr = compose_ep1_frame_4k(director, clip_cache, upscaler, lib, sc_obj, lt)
            out_p = qa_dir / f"{tag}.jpg"
            im_fr = Image.fromarray(fr)
            im_fr.save(out_p, quality=93)
            thumb = im_fr.resize((960, 540), Image.Resampling.LANCZOS)
            grid.paste(thumb, ((idx % 4) * 960, (idx // 4) * 540))
            print(f"  [QA 4K OK] {out_p.name} ({fr.shape[1]}x{fr.shape[0]})", flush=True)
        grid_p = qa_dir / "_qa_8frame_contact_sheet.jpg"
        grid.save(grid_p, quality=93)
        print(f"[QA COMPLETE in {time.time() - t0:.1f}s] Contact sheet -> {grid_p}", flush=True)
        return

    assert MASTER_WAV_PATH.exists(), f"Missing {MASTER_WAV_PATH}"
    total_sec = float(manifest["total_duration_sec"])
    total_frames = int(round(total_sec * FPS))

    nv_probe = subprocess.run(
        [
            ffmpeg_exe, "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=3840x2160:d=0.05",
            "-c:v", "h264_nvenc", "-profile:v", "high", "-level", "5.2", "-f", "null", "-",
        ],
        capture_output=True,
    )
    use_nvenc = nv_probe.returncode == 0
    v_codec_args = (
        ["-c:v", "h264_nvenc", "-preset", "p5", "-profile:v", "high", "-level", "5.2", "-cq", "19", "-b:v", "0"]
        if use_nvenc
        else ["-c:v", "libx264", "-preset", "fast", "-crf", "18"]
    )
    print(
        f"[4K UHD MASTER RENDER] {total_frames} frames ({total_sec/60:.2f} min @ 3840x2160 24fps, ZERO burned-in subtitles) via "
        f"{'NVENC RTX 5080 (BELOW_NORMAL priority)' if use_nvenc else 'libx264'}...",
        flush=True,
    )

    tmp_mp4 = EP1_DIR / "_tmp_ep1_4k_render.mp4"
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W4K}x{H4K}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(MASTER_WAV_PATH),
        *v_codec_args,
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        "-movflags", "+faststart",
        str(tmp_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert proc.stdin is not None

    scenes = manifest["scenes"]
    sc_idx = 0
    t_render0 = time.time()

    for f_idx in range(total_frames):
        gt = f_idx / float(FPS)
        while sc_idx < len(scenes) - 1 and gt >= scenes[sc_idx]["end_sec"]:
            sc_idx += 1
        sc = scenes[sc_idx]
        lt = max(0.0, gt - float(sc["start_sec"]))

        frame = compose_ep1_frame_4k(director, clip_cache, upscaler, lib, sc, lt)
        proc.stdin.write(memoryview(frame))

        if f_idx > 0 and f_idx % (FPS * 30) == 0:
            el = time.time() - t_render0
            fps_eff = f_idx / max(0.1, el)
            eta = (total_frames - f_idx) / max(0.1, fps_eff)
            print(
                f"  [{100.0 * f_idx / total_frames:5.1f}%] {f_idx}/{total_frames} frames ({sc['id']}) | "
                f"{fps_eff:5.1f} fps | ETA {eta:4.0f}s",
                flush=True,
            )

    proc.stdin.close()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")

    shutil.move(str(tmp_mp4), str(FINAL_4K_MP4))
    shutil.copy2(str(FINAL_4K_MP4), str(ARTIFACT_4K_MP4))
    sz_mb = FINAL_4K_MP4.stat().st_size / 1e6
    print(f"\n[EPISODE 1 4K UHD MASTER COMPLETE] {FINAL_4K_MP4} ({sz_mb:.1f} MB) in {time.time() - t0:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
