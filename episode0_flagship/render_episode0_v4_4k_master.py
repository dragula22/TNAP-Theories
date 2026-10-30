"""
Final Master `3840x2160` (`4K UHD` / `2160p`, `24 fps`) Cinema Renderer & Assembler for Flagship Episode 0:
  'The Universe Inside Out: A Visual Guide to the Stretched Fabric & the Upside-Down Cosmic Hourglass'
  (v4 Final Sagan Master — True 4K UHD Edition)

Final Refinements & Upgrades:
  1. True Native `3840x2160` (`4K UHD`) RTX 5080 3D GPU Rendering (`set_render_resolution(3840, 2160)`):
       - 4x higher pixel count (`8.29M` pixels/frame), 4x denser GPU surface supersampling, circular 4K 5x5 star splats,
         and 1:1 normalized optical cinema bloom.
       - Unlocks YouTube's high-bitrate 4K VP9/AV1 streaming tier and pixel-for-pixel sharpness on 4K monitors.
  2. True Native `3840x2160` Vector Broadcast Typography, Glassmorphic HUDs, Graphs & Verbatim Subtitles (`2x` vector DPI).
  3. GPU Bicubic + Unsharp-Crispened `4K` AI Cinema B-Roll composited directly on the RTX 5080.
  4. Verified 100% glitch-free across `8:24` (`s01` clamped strictly to `[0, 1]` + `torch.nan_to_num` armor — zero black boxes).
  5. Updated `chunk_23_scene06_a` narration & verbatim subtitles (`"pulling a giant silk tablecloth tight across a frame"`,
     removing `"drum"` while keeping all 32 other approved Sagan Edition chunks 100% untouched).
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
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

EP0_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EP0_DIR))

from gpu_renderer_core import set_render_resolution, smootherstep01, smoothstep01

W4K, H4K = 3840, 2160
S = 2  # 2x vector coordinate & font scale over 1920x1080
FPS = 24
SR = 48000

# Activate True 4K UHD across CameraMatrix & GPUCanvas BEFORE constructing GPU3DSceneDirectorV3!
set_render_resolution(W4K, H4K)

from gpu_scenes_v3 import GPU3DSceneDirectorV3, _find_chunk
from render_episode0_v2_cinema import CinemaClipCache, load_font
from render_episode0_v3_cinema import AUDIO_V3_DIR, MANIFEST_V3_PATH, MASTER_WAV_V3, get_v3_broll_windows

FINAL_4K_MP4 = EP0_DIR / "Episode_0_The_Universe_Inside_Out_Transparent_4K_UHD.mp4"
FINAL_MAIN_MP4 = EP0_DIR / "Episode_0_The_Universe_Inside_Out.mp4"
ARTIFACT_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")
ARTIFACT_4K_MP4 = ARTIFACT_DIR / "Episode_0_The_Universe_Inside_Out_Transparent_4K_UHD.mp4"
ARTIFACT_MAIN_MP4 = ARTIFACT_DIR / "Episode_0_The_Universe_Inside_Out.mp4"

# True Native 4K Vector Fonts (`2x` point size for razor-sharp 2160p rendering!)
FONTS_4K = {
    "hook_big": load_font(58 * S, bold=True),
    "hook_sub": load_font(24 * S, semibold=True),
    "hero_kicker": load_font(22 * S, bold=True),
    "hero_title": load_font(54 * S, bold=True),
    "hero_sub": load_font(26 * S, semibold=True),
    "lt_kicker": load_font(19 * S, bold=True),
    "lt_title": load_font(32 * S, bold=True),
    "wm": load_font(17 * S, semibold=True),
    "hud_hdr": load_font(19 * S, bold=True),
    "hud_big": load_font(30 * S, bold=True),
    "hud_body": load_font(21 * S, semibold=True),
    "hud_sm": load_font(17 * S, semibold=True),
    "yt_card": load_font(17 * S, semibold=True),
    "yt_badge": load_font(16 * S, bold=True),
    "sub": load_font(33 * S, semibold=True),
}


def blit_rgba_4k(frame_rgb: np.ndarray, overlay_rgba: Image.Image, x0: int, y0: int) -> None:
    """Alpha-blends a 4K RGBA vector overlay patch onto `(2160, 3840, 3) uint8` in-place."""
    fh, fw, _ = frame_rgb.shape
    arr = np.asarray(overlay_rgba, dtype=np.uint8)
    oh, ow, _ = arr.shape
    sx0 = max(0, x0)
    sy0 = max(0, y0)
    sx1 = min(fw, x0 + ow)
    sy1 = min(fh, y0 + oh)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    ox0, oy0 = sx0 - x0, sy0 - y0
    ox1, oy1 = ox0 + (sx1 - sx0), oy0 + (sy1 - sy0)

    sub_src = arr[oy0:oy1, ox0:ox1]
    alpha = sub_src[..., 3:4].astype(np.uint16)
    if alpha.max() == 0:
        return
    dst = frame_rgb[sy0:sy1, sx0:sx1].astype(np.uint16)
    blended = (sub_src[..., :3].astype(np.uint16) * alpha + dst * (255 - alpha) + 127) // 255
    frame_rgb[sy0:sy1, sx0:sx1] = blended.astype(np.uint8)


class GPUBRoll4KUpscaler:
    """Upscales `1920x1080` Ken-Burns B-roll crops to `3840x2160` on RTX 5080 via Bicubic + Cinema Unsharp Crispener."""

    def __init__(self, device: torch.device):
        self.dev = device
        self._pinned_out = torch.empty((H4K, W4K, 3), dtype=torch.uint8, pin_memory=(device.type == "cuda"))

    def upscale_and_blend(
        self,
        broll_1080: np.ndarray,
        gpu_4k: Optional[np.ndarray] = None,
        broll_alpha: float = 1.0,
    ) -> np.ndarray:
        t_in = torch.from_numpy(broll_1080).to(self.dev, non_blocking=False).permute(2, 0, 1).unsqueeze(0).float()
        up = F.interpolate(t_in, size=(H4K, W4K), mode="bicubic", align_corners=False)
        # Subtle optical micro-contrast unsharp crispener so 1080p cinema clips match 4K crispness without halos
        blur = F.avg_pool2d(F.pad(up, (1, 1, 1, 1), mode="replicate"), kernel_size=3, stride=1)
        sharp = torch.clamp(up + 0.34 * (up - blur), 0.0, 255.0).squeeze(0).permute(1, 2, 0)

        if gpu_4k is not None and broll_alpha < 0.995:
            t_gpu = torch.from_numpy(gpu_4k).to(self.dev, non_blocking=False).float()
            mixed = torch.clamp(sharp * broll_alpha + t_gpu * (1.0 - broll_alpha), 0.0, 255.0).to(torch.uint8)
            self._pinned_out.copy_(mixed, non_blocking=False)
        else:
            self._pinned_out.copy_(sharp.to(torch.uint8), non_blocking=False)
        return self._pinned_out.numpy()


def draw_cold_open_hook_cards_4k(frame: np.ndarray, t: float) -> None:
    beats = [
        (0.25, 4.35, "95% OF REALITY IS MISSING", "ACCORDING TO TODAY'S TEXTBOOK COSMIC MAP", (110, 215, 255)),
        (4.65, 9.05, "OR IS OUR MAP UPSIDE DOWN?", "WHAT IF SPACE ISN'T EMPTY — AND TIME ISN'T FLOWING?", (255, 212, 108)),
        (9.35, 13.25, "THE UNIVERSE INSIDE OUT", "AN OPEN VISUAL THOUGHT EXPERIMENT  •  ZERO EQUATIONS", (130, 240, 210)),
    ]
    for s0, s1, big_txt, sub_txt, accent in beats:
        if s0 <= t <= s1:
            fade = smoothstep01((t - s0) / 0.35) * smoothstep01((s1 - t) / 0.35)
            cw, ch = 1380 * S, 176 * S
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            a_bg = int(195 * fade)
            a_fg = int(255 * fade)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=22 * S, fill=(7, 12, 24, a_bg), outline=(*accent, int(145 * fade)), width=2 * S)
            dr.rounded_rectangle((cw // 2 - 140 * S, 18 * S, cw // 2 + 140 * S, 23 * S), radius=3 * S, fill=(*accent, a_fg))

            bb1 = dr.textbbox((0, 0), big_txt, font=FONTS_4K["hook_big"])
            dr.text(((cw - (bb1[2] - bb1[0])) // 2, 36 * S), big_txt, font=FONTS_4K["hook_big"], fill=(248, 251, 255, a_fg))

            bb2 = dr.textbbox((0, 0), sub_txt, font=FONTS_4K["hook_sub"])
            dr.text(((cw - (bb2[2] - bb2[0])) // 2, 118 * S), sub_txt, font=FONTS_4K["hook_sub"], fill=(*accent, a_fg))

            y_slide = int((1.0 - fade) * 18 * S)
            blit_rgba_4k(frame, ov, (W4K - cw) // 2, 430 * S + y_slide)
            break


def draw_chapter_lower_third_and_watermark_4k(frame: np.ndarray, scene: dict, local_t: float) -> None:
    sid = scene["id"]
    if sid == "hook00":
        return

    wm_txt = f"{scene['chapter']}  •  {scene['title'].split(':')[0]}"
    ov_w = Image.new("RGBA", (660 * S, 46 * S), (0, 0, 0, 0))
    dw = ImageDraw.Draw(ov_w)
    bb = dw.textbbox((0, 0), wm_txt, font=FONTS_4K["wm"])
    pw = (bb[2] - bb[0]) + 34 * S
    dw.rounded_rectangle((0, 0, pw, 36 * S), radius=18 * S, fill=(8, 14, 26, 142), outline=(95, 185, 235, 88), width=S)
    dw.text((17 * S, 7 * S), wm_txt, font=FONTS_4K["wm"], fill=(205, 226, 248, 198))
    blit_rgba_4k(frame, ov_w, 42 * S, 34 * S)

    if 0.45 <= local_t <= 7.50:
        f_in = smootherstep01((local_t - 0.45) / 0.55)
        f_out = smootherstep01((7.50 - local_t) / 0.60)
        vis = f_in * f_out
        cw, ch = 980 * S, 114 * S
        ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        a_bg = int(214 * vis)
        a_fg = int(255 * vis)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18 * S, fill=(8, 14, 28, a_bg), outline=(92, 200, 255, int(135 * vis)), width=2 * S)
        dr.rounded_rectangle((16 * S, 18 * S, 23 * S, ch - 18 * S), radius=4 * S, fill=(255, 206, 96, a_fg))
        dr.text((40 * S, 18 * S), scene["subtitle_tag"], font=FONTS_4K["lt_kicker"], fill=(108, 216, 255, a_fg))
        dr.text((40 * S, 50 * S), scene["title"], font=FONTS_4K["lt_title"], fill=(246, 250, 255, a_fg))

        x_pos = 54 * S - int((1.0 - vis) * 48 * S)
        blit_rgba_4k(frame, ov, x_pos, 104 * S)


def _draw_callout_pill_4k(
    frame: np.ndarray,
    kicker: str,
    headline: str,
    detail: str,
    accent: Tuple[int, int, int],
    vis: float,
    x_right_1080: int = 54,
    y_top_1080: int = 108,
    cw_1080: int = 560,
) -> None:
    if vis <= 0.01:
        return
    cw = cw_1080 * S
    ch = (144 if detail else 108) * S
    ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    dr.rounded_rectangle(
        (0, 0, cw - 1, ch - 1),
        radius=18 * S,
        fill=(8, 15, 29, int(214 * vis)),
        outline=(*accent, int(155 * vis)),
        width=2 * S,
    )
    dr.rounded_rectangle((18 * S, 18 * S, 24 * S, ch - 18 * S), radius=3 * S, fill=(*accent, int(255 * vis)))
    dr.text((38 * S, 16 * S), kicker, font=FONTS_4K["hud_hdr"], fill=(*accent, int(255 * vis)))
    dr.text((38 * S, 50 * S), headline, font=FONTS_4K["hud_body"], fill=(246, 250, 255, int(255 * vis)))
    if detail:
        dr.text((38 * S, 92 * S), detail, font=FONTS_4K["hud_sm"], fill=(192, 218, 245, int(238 * vis)))
    blit_rgba_4k(frame, ov, W4K - cw - x_right_1080 * S, y_top_1080 * S)


def draw_contextual_hud_4k(frame: np.ndarray, scene: dict, local_t: float) -> None:
    """Chunk-locked 4K glassmorphic visual callouts synchronized to every spoken beat."""
    sid = scene["id"]
    dur = float(scene["duration_sec"])

    if sid == "scene00":
        ch01 = _find_chunk(scene, "chunk_01")
        ch02 = _find_chunk(scene, "chunk_02")
        ch03 = _find_chunk(scene, "chunk_03")
        t01_e = ch01["local_end"] if ch01 else 30.5
        t02_s = ch02["local_start"] if ch02 else 31.6
        t02_e = ch02["local_end"] if ch02 else 71.4

        # Beat 1 (during chunk_01): Multi-Agent Gemini Argon + Antigravity Intro Pill
        if 15.2 <= local_t <= t01_e + 0.6:
            vis = smoothstep01((local_t - 15.2) / 0.55) * smoothstep01((t01_e + 0.6 - local_t) / 0.55)
            _draw_callout_pill_4k(
                frame,
                "OPEN HUMAN + AI THOUGHT EXPERIMENT",
                "David  +  Gemini Argon in Google Antigravity",
                "Competing Persona Subagents  •  Adversarial Red-Team Audits",
                (108, 224, 255),
                vis,
                cw_1080=585,
            )

        # Beat 2 (during chunk_02): Complete List of Agent Tools, Solvers & Benchmarks + stoler.systems
        t_list_on = max(t02_s + 18.0, t02_e - 20.5)
        if t_list_on <= local_t <= t02_e + 1.1:
            vis = smoothstep01((local_t - t_list_on) / 0.55) * smoothstep01((t02_e + 1.1 - local_t) / 0.6)
            cw, ch = 590 * S, 344 * S
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle(
                (0, 0, cw - 1, ch - 1),
                radius=18 * S,
                fill=(8, 15, 30, int(218 * vis)),
                outline=(100, 214, 255, int(155 * vis)),
                width=2 * S,
            )
            dr.text(
                (24 * S, 16 * S),
                "COMPLETE AGENT TOOLSET & BENCHMARK LIST",
                font=FONTS_4K["hud_hdr"],
                fill=(255, 208, 102, int(255 * vis)),
            )
            items = [
                (0.3, "AI Co-Pilot: Multi-Agent Gemini Argon (Antigravity)"),
                (1.6, "Symbolic Math: Python 3.12  •  SymPy Tensor Checks"),
                (2.9, "Toy Solvers: NumPy / SciPy 1D & Radial ODE / PDEs"),
                (4.2, "Sky Benchmarks: Planck, JWST, DESI DR2 & SPARC"),
                (5.5, "Status: Exploratory Toy Models (Not Peer-Reviewed)"),
                (7.0, "Full Write-Up & Code: stoler.systems  •  GitHub"),
            ]
            for idx, (dt_on, label) in enumerate(items):
                lit = smoothstep01((local_t - (t_list_on + dt_on)) / 0.45)
                yy = (54 + idx * 46) * S
                is_link = idx == len(items) - 1
                dot_rgb = (255, 212, 102) if is_link else (95, 242, 195)
                dot_c = (*dot_rgb, int(255 * vis)) if lit > 0.2 else (95, 115, 145, int(160 * vis))
                txt_rgb = (255, 224, 132) if is_link else (244, 249, 255)
                txt_c = (*txt_rgb, int((135 + 120 * lit) * vis))
                dr.ellipse((24 * S, yy + 7 * S, 36 * S, yy + 19 * S), fill=dot_c)
                dr.text((48 * S, yy), label, font=FONTS_4K["hud_sm"], fill=txt_c)
            blit_rgba_4k(frame, ov, W4K - cw - 54 * S, 106 * S)

        t_hero = (ch03["local_end"] - 6.8) if ch03 else (dur - 9.0)
        if local_t >= t_hero:
            vis = smoothstep01((local_t - t_hero) / 0.65) * smoothstep01((dur - 0.3 - local_t) / 0.65)
            cw, ch = 1420 * S, 204 * S
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=24 * S, fill=(7, 13, 26, int(218 * vis)), outline=(255, 208, 105, int(170 * vis)), width=2 * S)
            for txt, fnt, yy, col in (
                ("OPEN HUMAN + AI THOUGHT EXPERIMENT  •  STOLER.SYSTEMS", FONTS_4K["hero_kicker"], 24 * S, (108, 220, 255, int(255 * vis))),
                ("THE UNIVERSE INSIDE OUT", FONTS_4K["hero_title"], 58 * S, (250, 252, 255, int(255 * vis))),
                ("A Visual Guide to the Stretched Fabric & the Upside-Down Cosmic Hourglass", FONTS_4K["hero_sub"], 136 * S, (255, 212, 118, int(255 * vis))),
            ):
                bb = dr.textbbox((0, 0), txt, font=fnt)
                dr.text(((cw - (bb[2] - bb[0])) // 2, yy), txt, font=fnt, fill=col)
            blit_rgba_4k(frame, ov, (W4K - cw) // 2, 390 * S)

    elif sid == "scene01":
        ch07 = _find_chunk(scene, "chunk_07")
        ch08 = _find_chunk(scene, "chunk_08")
        t_on0 = ch07["local_start"] if ch07 else 66.0
        t_off = (ch08["local_end"] - 9.0) if ch08 else (dur - 11.0)
        if t_on0 <= local_t <= t_off:
            vis = smoothstep01((local_t - t_on0) / 0.6) * smoothstep01((t_off - local_t) / 0.6)
            cw, ch = 480 * S, 255 * S
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18 * S, fill=(8, 14, 28, int(210 * vis)), outline=(165, 120, 255, int(150 * vis)), width=2 * S)
            dr.text((24 * S, 18 * S), "TEXTBOOK LAMBDA-CDM RECIPE", font=FONTS_4K["hud_hdr"], fill=(195, 165, 255, int(255 * vis)))
            bars = [
                ("Visible Stars & Atoms", 0.05, "5%", (95, 220, 255), t_on0 + 1.0),
                ("Cold Dark Matter (Glue)", 0.27, "27%", (168, 105, 255), t_on0 + 6.5),
                ("Lambda Dark Energy (Push)", 0.68, "68%", (255, 92, 122), t_on0 + 15.5),
            ]
            for i, (lbl, frac, pct, col, t_b) in enumerate(bars):
                grow = smoothstep01((local_t - t_b) / 1.1)
                yy = (58 + i * 54) * S
                dr.text((24 * S, yy), lbl, font=FONTS_4K["hud_sm"], fill=(228, 236, 248, int(245 * vis)))
                dr.text((cw - 72 * S, yy), pct, font=FONTS_4K["hud_sm"], fill=(*col, int(255 * vis)))
                dr.rounded_rectangle((24 * S, yy + 26 * S, cw - 24 * S, yy + 38 * S), radius=6 * S, fill=(28, 36, 56, int(200 * vis)))
                bw = max(12 * S, int((cw - 48 * S) * frac * grow))
                dr.rounded_rectangle((24 * S, yy + 26 * S, 24 * S + bw, yy + 38 * S), radius=6 * S, fill=(*col, int(245 * vis)))
            if local_t >= t_on0 + 23.0:
                p95 = smoothstep01((local_t - (t_on0 + 23.0)) / 0.5)
                dr.text((24 * S, 218 * S), "95% OF REALITY UNSEEN IN LABS", font=FONTS_4K["hud_hdr"], fill=(255, 206, 98, int(255 * vis * p95)))
            blit_rgba_4k(frame, ov, W4K - cw - 54 * S, 110 * S)

    elif sid == "scene03":
        ch14 = _find_chunk(scene, "chunk_14")
        t14 = ch14["local_start"] if ch14 else 43.0
        if t14 <= local_t <= dur - 1.5:
            vis = smoothstep01((local_t - t14) / 0.55) * smoothstep01((dur - 1.5 - local_t) / 0.55)
            _draw_callout_pill_4k(
                frame,
                "ACTIVE OPEN QUESTION",
                "Possible Thermodynamic Memory Arrow",
                "Neater Past Groove   →   Messier Ink-Spread Lock-In",
                (255, 208, 102),
                vis,
                cw_1080=555,
            )

    elif sid == "scene04":
        ch18 = _find_chunk(scene, "chunk_18")
        if ch18 and ch18["local_start"] + 8.0 <= local_t <= ch18["local_end"] + 1.2:
            vis = smoothstep01((local_t - (ch18["local_start"] + 8.0)) / 0.6) * smoothstep01((ch18["local_end"] + 1.2 - local_t) / 0.6)
            _draw_callout_pill_4k(
                frame,
                "SMOOTH SOAP-FILM THROAT SORTER",
                "Zero Fabric Tear at Central Waist",
                "Sapphire Half: Ordinary Matter   •   Opposite Side: Antimatter",
                (112, 222, 255),
                vis,
                cw_1080=590,
            )

    elif sid == "scene05":
        ch20 = _find_chunk(scene, "chunk_20")
        ch21 = _find_chunk(scene, "chunk_21")
        ch22 = _find_chunk(scene, "chunk_22")
        if ch20 and ch21 and ch22:
            t20_e = ch20["local_end"]
            t21_s, t21_e = ch21["local_start"], ch21["local_end"]
            t22_s, t22_e = ch22["local_start"], ch22["local_end"]
            t_tel = t21_s + 0.56 * (t21_e - t21_s)

            if t20_e - 7.0 <= local_t <= t20_e + 2.2:
                vis = smoothstep01((local_t - (t20_e - 7.0)) / 0.55) * smoothstep01((t20_e + 2.2 - local_t) / 0.55)
                _draw_callout_pill_4k(
                    frame,
                    "MACRO ZOOM  •  TINY INNER RING",
                    "Pinched Big Bang Singularity Throat",
                    "Soap Film Held Simultaneously by Giant Rim & Tiny Pinpoint Ring",
                    (255, 212, 108),
                    vis,
                    cw_1080=610,
                )
            elif t21_s + 1.0 <= local_t <= t_tel - 0.4:
                vis = smoothstep01((local_t - (t21_s + 1.0)) / 0.55) * smoothstep01((t_tel - 0.4 - local_t) / 0.55)
                _draw_callout_pill_4k(
                    frame,
                    "PRIMORDIAL SOUND & HEAT WAVE CUTOFF",
                    "Red Arch: Ultra-Wide Sky Wave Blocked by Throat",
                    "Cyan Ripples: Shorter Primordial Waves Fit Cleanly on Sheet",
                    (255, 118, 132),
                    vis,
                    cw_1080=605,
                )
            elif t_tel + 0.4 <= local_t <= t21_e + 1.8:
                vis = smoothstep01((local_t - (t_tel + 0.4)) / 0.55) * smoothstep01((t21_e + 1.8 - local_t) / 0.55)
                _draw_callout_pill_4k(
                    frame,
                    "PLANCK  •  HUBBLE  •  JAMES WEBB",
                    "Mapping the Oldest Light Across Deep Space",
                    "Observed Sky Anomaly: Widest Temperature Ripples Missing",
                    (108, 224, 255),
                    vis,
                    cw_1080=595,
                )
            elif t22_s + 2.0 <= local_t <= t22_e - 3.5:
                vis = smoothstep01((local_t - (t22_s + 2.0)) / 0.6) * smoothstep01((t22_e - 3.5 - local_t) / 0.6)
                u22 = (local_t - t22_s) / max(1.0, t22_e - t22_s)
                if u22 < 0.50:
                    _draw_callout_pill_4k(
                        frame,
                        "DOUBLE SLIT  •  BOTH OPENINGS UNBLOCKED",
                        "Connected Fabric Carries Wave Through Both Slits",
                        "Two Wave Paths Overlap  →  Bright & Dark Interference Stripes",
                        (92, 244, 196),
                        vis,
                        cw_1080=615,
                    )
                else:
                    _draw_callout_pill_4k(
                        frame,
                        "WHICH-WAY SENSOR PLACED AT SLIT 1",
                        "Sensor Absorbs Wave Like a Finger on a Guitar String",
                        "No Second Wave Left to Overlap  →  Stripes Vanish Automatically",
                        (255, 196, 92),
                        vis,
                        cw_1080=630,
                    )

    elif sid == "scene07":
        ch26 = _find_chunk(scene, "chunk_26")
        ch27 = _find_chunk(scene, "chunk_27")
        if ch26 and ch26["local_start"] + 12.0 <= local_t <= ch26["local_end"] + 1.2:
            vis = smoothstep01((local_t - (ch26["local_start"] + 12.0)) / 0.55) * smoothstep01((ch26["local_end"] + 1.2 - local_t) / 0.55)
            _draw_callout_pill_4k(
                frame,
                "SOLAR SYSTEM  •  LOCAL CAMPFIRE GRAVITY",
                "Sun's Steep Funnel = 50,000,000x Deep-Space Tension",
                "Local Slope Completely Dominates Nearby Planetary Orbits",
                (255, 198, 92),
                vis,
                cw_1080=605,
            )
        elif ch27 and ch27["local_start"] + 1.5 <= local_t <= dur - 1.2:
            t_g0 = ch27["local_start"] + 1.5
            vis = smoothstep01((local_t - t_g0) / 0.6) * smoothstep01((dur - 1.2 - local_t) / 0.6)
            cw, ch = 536 * S, 282 * S
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18 * S, fill=(8, 15, 28, int(216 * vis)), outline=(85, 238, 190, int(155 * vis)), width=2 * S)
            dr.text((24 * S, 16 * S), "WHY OUTER STARS AREN'T FLUNG OFF", font=FONTS_4K["hud_hdr"], fill=(98, 242, 198, int(255 * vis)))

            gx0, gy0, gx1, gy1 = 48 * S, 58 * S, cw - 30 * S, 188 * S
            dr.line((gx0, gy1, gx1, gy1), fill=(140, 165, 198, int(200 * vis)), width=2 * S)
            dr.line((gx0, gy0, gx0, gy1), fill=(140, 165, 198, int(200 * vis)), width=2 * S)

            reveal = smoothstep01((local_t - (t_g0 + 1.0)) / 3.5)
            n_pts = max(3, int(60 * reveal))
            pts_flat, pts_kep = [], []
            for k in range(n_pts):
                r = 0.08 + 4.8 * (k / 59.0)
                px = int(gx0 + (gx1 - gx0) * (k / 59.0))
                v_kep = (r / 0.75) * math.exp(1.0 - r / 0.75) if r < 0.75 else (0.75 / r) ** 0.5
                v_flt = 1.0 - math.exp(-r / 0.55)
                pts_kep.append((px, int(gy1 - (gy1 - gy0 - 14 * S) * min(1.05, v_kep * 0.92))))
                pts_flat.append((px, int(gy1 - (gy1 - gy0 - 14 * S) * (0.94 * v_flt))))

            for k in range(0, len(pts_kep) - 1, 2):
                dr.line((pts_kep[k], pts_kep[k + 1]), fill=(255, 102, 118, int(205 * vis)), width=3 * S)
            if len(pts_flat) >= 2:
                dr.line(pts_flat, fill=(82, 245, 192, int(255 * vis)), width=4 * S)

            dr.text((24 * S, 200 * S), "Emerald Bowl: Taut Cloth Curves Fast Stars Inward", font=FONTS_4K["hud_sm"], fill=(95, 245, 195, int(250 * vis)))
            dr.text((24 * S, 226 * S), "Red Tangent:  Flung Into Space Without Fabric Tension", font=FONTS_4K["hud_sm"], fill=(255, 122, 134, int(240 * vis)))
            dr.text((24 * S, 251 * S), "Hypothesis: Can Fabric Tension Replace Dark Matter?", font=FONTS_4K["hud_sm"], fill=(210, 226, 248, int(225 * vis)))
            blit_rgba_4k(frame, ov, W4K - cw - 54 * S, 108 * S)

    elif sid == "scene08":
        ch28 = _find_chunk(scene, "chunk_28")
        ch29 = _find_chunk(scene, "chunk_29")
        t29_s = ch29["local_start"] if ch29 else 30.0
        if ch28 and 8.0 <= local_t <= t29_s - 0.6:
            vis = smoothstep01((local_t - 8.0) / 0.6) * smoothstep01((t29_s - 0.6 - local_t) / 0.6)
            _draw_callout_pill_4k(
                frame,
                "NEWBORN GALAXY  •  FABRIC PLEAT FOLDING",
                "Condensing Stars Gather & Tuck Excess Sheet Inward",
                "Creates a Crisp, Springy Circumferential Tension Pleat",
                (108, 224, 255),
                vis,
                cw_1080=605,
            )

    elif sid == "scene09":
        ch33 = _find_chunk(scene, "chunk_33")
        t33_s = ch33["local_start"] if ch33 else 52.0
        if local_t >= t33_s + 3.5:
            vis = smoothstep01((local_t - (t33_s + 3.5)) / 0.6) * smoothstep01((dur - 1.5 - local_t) / 0.8)
            cw, ch = 540 * S, 324 * S
            ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            dr = ImageDraw.Draw(ov)
            dr.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=18 * S, fill=(8, 14, 28, int(216 * vis)), outline=(105, 215, 255, int(155 * vis)), width=2 * S)
            dr.text((24 * S, 18 * S), "UP NEXT  •  6 HARD-SCIENCE CHAPTERS", font=FONTS_4K["hud_hdr"], fill=(255, 210, 104, int(255 * vis)))
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
                yy = (58 + idx * 42) * S
                dr.rounded_rectangle((22 * S, yy, cw - 22 * S, yy + 34 * S), radius=9 * S, fill=(18, 32, 56, int((90 + 110 * lit) * vis)))
                dr.text((36 * S, yy + 5 * S), ch_txt, font=FONTS_4K["hud_sm"], fill=(242, 248, 255, int((130 + 125 * lit) * vis)))
            blit_rgba_4k(frame, ov, W4K - cw - 54 * S, 108 * S)


_DUMMY_MEASURE = ImageDraw.Draw(Image.new("RGBA", (8, 8)))


def _get_youtube_critique_prompt(scene: dict) -> Optional[Tuple[float, float, str]]:
    """
    Returns `(t_start, t_end, text)` for subtle, non-intrusive YouTube `ⓘ`-style slide-in critique prompts
    scheduled strictly during HUD-free moments across key claims so they never clutter the screen!
    """
    sid = scene["id"]
    if sid == "scene02":
        ch11 = _find_chunk(scene, "chunk_11")
        if ch11:
            t0 = ch11["local_start"] + 2.0
            return (t0, t0 + 6.8, "Spot a flaw in modeling atoms as fabric knots? Let us know in the comments or on GitHub")
    elif sid == "scene03":
        ch13 = _find_chunk(scene, "chunk_13")
        if ch13:
            t0 = ch13["local_start"] + 11.5
            return (t0, t0 + 6.8, "Am I missing something on time & memory? Share your critique at stoler.systems")
    elif sid == "scene04":
        ch16 = _find_chunk(scene, "chunk_16")
        if ch16:
            t0 = ch16["local_start"] + 5.5
            return (t0, t0 + 6.8, "Disagree with flipping the cosmic hourglass? Poke holes in the math on GitHub")
    elif sid == "scene05":
        ch19 = _find_chunk(scene, "chunk_19")
        if ch19:
            t0 = ch19["local_start"] + 3.2
            return (t0, t0 + 6.8, "Skeptical of two-boundary physics? Inspect every assumption at stoler.systems")
    elif sid == "scene06":
        ch24 = _find_chunk(scene, "chunk_24")
        if ch24:
            t0 = ch24["local_start"] + 6.0
            return (t0, t0 + 6.8, "Physicists: Where does tension-based gravity break down? Tell us in the comments")
    elif sid == "scene08":
        ch29 = _find_chunk(scene, "chunk_29")
        if ch29:
            t0 = ch29["local_start"] + 10.5
            return (t0, t0 + 6.8, "Does this 1D cluster-pleat toy model fail in 3D? Open an issue on GitHub")
    return None


def draw_youtube_critique_slide_card_4k(frame: np.ndarray, scene: dict, local_t: float) -> None:
    """
    Renders a sleek, normal-sized YouTube-style top-right slide-in info banner (`ⓘ`) inviting viewer critique.
    Slides smoothly in from the right edge over 0.48s, holds calmly, and slides back out cleanly.
    """
    spec = _get_youtube_critique_prompt(scene)
    if not spec:
        return
    t0, t1, msg = spec
    if not (t0 <= local_t <= t1):
        return

    slide_in = smootherstep01((local_t - t0) / 0.48)
    slide_out = smootherstep01((t1 - local_t) / 0.48)
    vis = slide_in * slide_out
    if vis <= 0.01:
        return

    bb = _DUMMY_MEASURE.textbbox((0, 0), msg, font=FONTS_4K["yt_card"])
    tw = bb[2] - bb[0]
    cw = tw + 68 * S
    ch = 44 * S

    ov = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)

    # Subtle dark translucent pill similar to YouTube's top-right recommended-video info card
    dr.rounded_rectangle(
        (0, 0, cw - 1, ch - 1),
        radius=22 * S,
        fill=(10, 16, 28, int(218 * vis)),
        outline=(255, 210, 108, int(145 * vis)),
        width=max(1, int(1.5 * S)),
    )

    # Crisp circular `i` badge on left
    cx, cy, cr = 22 * S, ch // 2, 12 * S
    dr.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(255, 210, 104, int(245 * vis)))
    ib = dr.textbbox((0, 0), "i", font=FONTS_4K["yt_badge"])
    dr.text(
        (cx - (ib[2] - ib[0]) // 2 - ib[0], cy - (ib[3] - ib[1]) // 2 - ib[1] - 1),
        "i",
        font=FONTS_4K["yt_badge"],
        fill=(10, 16, 28, int(255 * vis)),
    )

    dr.text(
        (44 * S, (ch - (bb[3] - bb[1])) // 2 - bb[1]),
        msg,
        font=FONTS_4K["yt_card"],
        fill=(242, 247, 255, int(250 * vis)),
    )

    # Smooth horizontal slide from right edge (`W4K + 20` -> `W4K - cw - 36*S`)
    target_x = W4K - cw - 36 * S
    offscreen_x = W4K + 16 * S
    cur_x = int(round(offscreen_x + (target_x - offscreen_x) * vis))
    blit_rgba_4k(frame, ov, cur_x, 32 * S)


def draw_verbatim_subtitle_4k(frame: np.ndarray, cues: List[dict], local_t: float) -> None:
    """Renders razor-sharp 4K vector rounded-glass verbatim subtitle pill synced to David's voice."""
    active: Optional[dict] = None
    for c in cues:
        if c["start"] - 0.05 <= local_t <= c["end"] + 0.08:
            active = c
            break
    if not active:
        return

    fade = smoothstep01((local_t - (active["start"] - 0.05)) / 0.10) * smoothstep01(
        ((active["end"] + 0.08) - local_t) / 0.10
    )
    txt = active["text"]
    bb = _DUMMY_MEASURE.textbbox((0, 0), txt, font=FONTS_4K["sub"])
    tw, th = bb[2] - bb[0], bb[3] - bb[1]

    pw = min(W4K - 240, tw + 64 * S)
    ph = th + 34 * S
    ov = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)

    dr.rounded_rectangle(
        (0, 0, pw - 1, ph - 1),
        radius=17 * S,
        fill=(6, 11, 22, int(202 * fade)),
        outline=(95, 195, 250, int(115 * fade)),
        width=2,
    )
    tx = (pw - tw) // 2 - bb[0]
    ty = (ph - th) // 2 - bb[1]
    dr.text((tx + 2, ty + 3), txt, font=FONTS_4K["sub"], fill=(0, 0, 0, int(210 * fade)))
    dr.text((tx, ty), txt, font=FONTS_4K["sub"], fill=(248, 251, 255, int(255 * fade)))

    blit_rgba_4k(frame, ov, (W4K - pw) // 2, H4K - ph - 48 * S)


def compose_frame_4k(
    director: GPU3DSceneDirectorV3,
    clip_cache: CinemaClipCache,
    upscaler: GPUBRoll4KUpscaler,
    scene: dict,
    local_t: float,
) -> np.ndarray:
    sid = scene["id"]
    dur = float(scene["duration_sec"])

    broll_1080: Optional[np.ndarray] = None
    broll_alpha = 0.0
    xf = 0.65

    for w0, w1, cname, zdir in get_v3_broll_windows(scene):
        if w0 - xf <= local_t <= w1 + xf:
            f_in = 1.0 if (w0 == 0.0 and local_t < xf) else smoothstep01((local_t - (w0 - xf)) / (2.0 * xf))
            f_out = smoothstep01(((w1 + xf) - local_t) / (2.0 * xf))
            broll_alpha = max(0.0, min(1.0, f_in * f_out))
            if broll_alpha > 0.01:
                broll_1080 = clip_cache.get_frame(cname, max(0.0, local_t - w0), w1 - w0, zoom_dir=zdir)
            break

    if broll_1080 is not None and broll_alpha >= 0.995:
        frame = upscaler.upscale_and_blend(broll_1080, None, 1.0)
    elif broll_1080 is not None and broll_alpha > 0.01:
        gpu_4k = director.render_scene_frame_v3(scene, local_t)
        frame = upscaler.upscale_and_blend(broll_1080, gpu_4k, broll_alpha)
    else:
        frame = director.render_scene_frame_v3(scene, local_t)

    if sid == "hook00":
        draw_cold_open_hook_cards_4k(frame, local_t)
    else:
        ch32 = _find_chunk(scene, "chunk_32") if sid == "scene09" else None
        ch33 = _find_chunk(scene, "chunk_33") if sid == "scene09" else None
        in_sagan_interlude = bool(
            ch32 and ch33 and (ch32["local_end"] + 0.3 <= local_t <= ch33["local_start"] - 0.3)
        )
        if not in_sagan_interlude:
            draw_chapter_lower_third_and_watermark_4k(frame, scene, local_t)
        draw_contextual_hud_4k(frame, scene, local_t)
        draw_youtube_critique_slide_card_4k(frame, scene, local_t)
        draw_verbatim_subtitle_4k(frame, scene["cues"], local_t)

    if sid == "scene09" and local_t > dur - 2.0:
        fade_blk = max(0.0, min(1.0, (dur - local_t) / 2.0))
        np.multiply(frame, fade_blk, out=frame, casting="unsafe")

    return frame


def main() -> None:
    qa_only = "--qa-only" in sys.argv
    t0 = time.time()
    manifest = json.loads(MANIFEST_V3_PATH.read_text(encoding="utf-8"))
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    director = GPU3DSceneDirectorV3()
    clip_cache = CinemaClipCache(ffmpeg_exe)
    upscaler = GPUBRoll4KUpscaler(director.dev)

    if qa_only:
        qa_dir = EP0_DIR / "v5_4k_qa"
        qa_dir.mkdir(exist_ok=True)
        sc_map = {s["id"]: s for s in manifest["scenes"]}
        sc00 = sc_map["scene00"]
        sc02 = sc_map["scene02"]
        sc05 = sc_map["scene05"]
        ch02 = _find_chunk(sc00, "chunk_02")
        ch11 = _find_chunk(sc02, "chunk_11")
        ch20 = _find_chunk(sc05, "chunk_20")

        samples = [
            ("v5_4k_01_scene00_toolset_hud", sc00, ch02["local_end"] - 7.5),
            ("v5_4k_02_youtube_critique_slide_card", sc02, ch11["local_start"] + 4.5),
            ("v5_4k_03_scene05_no_real_physics_claim", sc05, ch20["local_start"] + 3.2),
        ]
        for tag, sc_obj, lt in samples:
            fr = compose_frame_4k(director, clip_cache, upscaler, sc_obj, lt)
            out_p = qa_dir / f"{tag}.jpg"
            Image.fromarray(fr).save(out_p, quality=94)
            shutil.copy2(str(out_p), str(ARTIFACT_DIR / out_p.name))
            print(f"[4K QA Frame Saved] {out_p.name} ({fr.shape[1]}x{fr.shape[0]})", flush=True)
        return

    assert MASTER_WAV_V3.exists(), f"Missing {MASTER_WAV_V3}"
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
        f"[4K UHD Encoder] Rendering {total_frames} frames ({total_sec/60:.2f} min @ 3840x2160 24fps) via "
        f"{'NVENC RTX 5080 (H.264 High@L5.2 4K)' if use_nvenc else 'libx264'}...",
        flush=True,
    )

    tmp_mp4 = EP0_DIR / "_tmp_ep0_v4_4k_render.mp4"
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W4K}x{H4K}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(MASTER_WAV_V3),
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

    for f_idx in range(total_frames):
        gt = f_idx / FPS
        while sc_idx < len(scenes) - 1 and gt >= scenes[sc_idx]["end_sec"]:
            sc_idx += 1
        sc = scenes[sc_idx]
        lt = max(0.0, gt - sc["start_sec"])

        frame = compose_frame_4k(director, clip_cache, upscaler, sc, lt)
        proc.stdin.write(memoryview(frame))

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

    shutil.move(str(tmp_mp4), str(FINAL_4K_MP4))
    shutil.copy2(str(FINAL_4K_MP4), str(FINAL_MAIN_MP4))
    shutil.copy2(str(FINAL_4K_MP4), str(ARTIFACT_4K_MP4))
    shutil.copy2(str(FINAL_4K_MP4), str(ARTIFACT_MAIN_MP4))
    sz_mb = FINAL_4K_MP4.stat().st_size / 1e6
    print(f"\n[4K UHD MASTER COMPLETE] {FINAL_4K_MP4.name} ({sz_mb:.1f} MB) in {time.time() - t0:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
