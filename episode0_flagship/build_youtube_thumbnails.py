"""
Builds 3 YouTube-Studio-Ready (`1920x1080`, `< 1.9 MB` sRGB JPEG — guaranteed under YouTube's strict 2 MB limit,
with bottom-right `16:00` duration badge safe-zone respected!) high-CTR thumbnails for Episode 0:
  1. `YT_Thumbnail_A_Upside_Down_Hourglass.jpg` — Cosmic Hourglass hero + '95% MISSING?' / 'UPSIDE DOWN?'
  2. `YT_Thumbnail_B_No_Dark_Matter.jpg`        — Stretched Fabric Galaxy Bowl + 'NO DARK MATTER?'
  3. `YT_Thumbnail_C_Split_Cosmic_Map.jpg`      — Split Paradox ('95% INVISIBLE' vs '0% MISSING' / 'FLIP THE MAP')
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

EP0_DIR = Path(__file__).resolve().parent
THUMB_DIR = EP0_DIR / "thumbnails"
ART_DIR = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")
W, H = 1920, 1080


def load_heavy_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in (
        "C:/Windows/Fonts/seguibl.ttf",   # Segoe UI Black (ultra-clean modern YouTube display font)
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/impact.ttf",
    ):
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def load_bold_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def fit_cover_1080p(img_path: Path) -> Image.Image:
    im = Image.open(img_path).convert("RGB")
    iw, ih = im.size
    target_ar = W / H
    src_ar = iw / ih
    if src_ar > target_ar:
        new_w = int(round(ih * target_ar))
        x0 = (iw - new_w) // 2
        im = im.crop((x0, 0, x0 + new_w, ih))
    elif src_ar < target_ar:
        new_h = int(round(iw / target_ar))
        y0 = (ih - new_h) // 2
        im = im.crop((0, y0, iw, y0 + new_h))
    im = im.resize((W, H), Image.Resampling.LANCZOS)
    # Subtle contrast & vibrance boost so thumbnail pops on YouTube homepage & mobile
    im = ImageEnhance.Contrast(im).enhance(1.10)
    im = ImageEnhance.Color(im).enhance(1.12)
    return im


def apply_left_scrim(base_rgb: Image.Image, width_frac: float = 0.56, max_alpha: int = 195) -> Image.Image:
    """Applies a smooth dark cinematic gradient on the left so white/gold text has 100% contrast."""
    arr = np.linspace(1.0, 0.0, int(W * width_frac), dtype=np.float32) ** 1.45
    alpha_row = np.zeros((W,), dtype=np.uint8)
    alpha_row[: len(arr)] = (arr * max_alpha).astype(np.uint8)
    alpha_2d = np.tile(alpha_row, (H, 1))
    scrim = Image.new("RGBA", (W, H), (4, 8, 18, 255))
    scrim.putalpha(Image.fromarray(alpha_2d, mode="L"))
    return Image.alpha_composite(base_rgb.convert("RGBA"), scrim)


def apply_corner_scrim(base_rgb: Image.Image, cx: float, cy: float, rx: float, ry: float, max_alpha: int = 205) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W]
    d2 = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    w = np.clip(1.0 - d2, 0.0, 1.0) ** 1.5
    scrim = Image.new("RGBA", (W, H), (4, 8, 18, 255))
    scrim.putalpha(Image.fromarray((w * max_alpha).astype(np.uint8), mode="L"))
    return Image.alpha_composite(base_rgb.convert("RGBA"), scrim)


def draw_glow_headline(
    canvas_rgba: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int, int],
    stroke_width: int = 8,
) -> None:
    """Draws ultra-crisp YouTube display text with soft ambient shadow + dark keyline stroke."""
    x, y = xy
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    ds.text((x + 6, y + 10), text, font=font, fill=(0, 0, 0, 235), stroke_width=stroke_width + 6, stroke_fill=(0, 0, 0, 235))
    sh = sh.filter(ImageFilter.GaussianBlur(radius=14))
    canvas_rgba.alpha_composite(sh)

    dr = ImageDraw.Draw(canvas_rgba)
    dr.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=(5, 9, 20, 255),
    )


def save_youtube_jpg(im_rgba: Image.Image, filename: str) -> Path:
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    rgb = im_rgba.convert("RGB")
    out_p = THUMB_DIR / filename
    # Guarantee < 1.90 MB for YouTube Studio (< 2 MB hard cap)
    for q in (94, 91, 88, 85):
        rgb.save(out_p, format="JPEG", quality=q, subsampling=0, optimize=True)
        if out_p.stat().st_size <= 1_920_000:
            break
    shutil.copy2(str(out_p), str(ART_DIR / filename))
    print(f"[Thumbnail Ready] {filename} ({out_p.stat().st_size / 1024:.0f} KB)", flush=True)
    return out_p


def build_all() -> None:
    f_huge = load_heavy_font(132)
    f_xl = load_heavy_font(114)
    f_lg = load_heavy_font(96)
    f_pill = load_bold_font(42)
    f_tag = load_bold_font(44)

    # -----------------------------------------------------------------------
    # THUMBNAIL A: Upside-Down Cosmic Hourglass ("95% MISSING?" / "UPSIDE DOWN?")
    # -----------------------------------------------------------------------
    bg1 = THUMB_DIR / "thumb_bg_01_flipped_hourglass.png"
    if bg1.exists():
        c1 = apply_left_scrim(fit_cover_1080p(bg1), width_frac=0.58, max_alpha=205)
        dr = ImageDraw.Draw(c1)
        # Top crimson-gold curiosity pill
        dr.rounded_rectangle((74, 92, 505, 170), radius=20, fill=(215, 38, 68, 242), outline=(255, 214, 110, 255), width=4)
        dr.text((106, 103), "95% MISSING?", font=f_pill, fill=(255, 252, 245, 255))

        draw_glow_headline(c1, (72, 210), "OUR MAP", f_xl, (248, 252, 255, 255), stroke_width=9)
        draw_glow_headline(c1, (72, 342), "IS UPSIDE", f_xl, (255, 214, 92, 255), stroke_width=9)
        draw_glow_headline(c1, (72, 474), "DOWN.", f_huge, (255, 214, 92, 255), stroke_width=10)

        # Clean bottom-left visual guide subtitle pill (well away from bottom-right 16:00 badge!)
        dr = ImageDraw.Draw(c1)
        dr.rounded_rectangle((74, 888, 690, 964), radius=18, fill=(8, 18, 36, 225), outline=(102, 224, 255, 215), width=3)
        dr.text((104, 900), "A VISUAL GUIDE  •  0 EQUATIONS", font=load_bold_font(36), fill=(132, 232, 255, 255))
        save_youtube_jpg(c1, "YT_Thumbnail_A_Upside_Down_Hourglass.jpg")

    # -----------------------------------------------------------------------
    # THUMBNAIL B: Stretched Fabric Galaxy Bowl ("NO DARK MATTER?")
    # -----------------------------------------------------------------------
    bg2 = THUMB_DIR / "thumb_bg_02_no_dark_matter_galaxy.png"
    if bg2.exists():
        c2 = apply_corner_scrim(fit_cover_1080p(bg2), cx=340, cy=280, rx=980, ry=680, max_alpha=205)
        draw_glow_headline(c2, (74, 78), "NO DARK", f_huge, (255, 255, 255, 255), stroke_width=10)
        draw_glow_headline(c2, (74, 222), "MATTER?", f_huge, (255, 212, 84, 255), stroke_width=10)

        dr2 = ImageDraw.Draw(c2)
        dr2.rounded_rectangle((78, 404, 686, 484), radius=20, fill=(10, 26, 44, 232), outline=(92, 245, 198, 240), width=4)
        dr2.text((110, 417), "ONE STRETCHED FABRIC", font=f_pill, fill=(112, 250, 208, 255))
        save_youtube_jpg(c2, "YT_Thumbnail_B_No_Dark_Matter.jpg")

    # -----------------------------------------------------------------------
    # THUMBNAIL C: Split Paradox ("95% INVISIBLE" vs "0% MISSING" / "THE UNIVERSE INSIDE OUT")
    # -----------------------------------------------------------------------
    bg3 = THUMB_DIR / "thumb_bg_03_split_map_paradox.png"
    if bg3.exists():
        c3 = fit_cover_1080p(bg3).convert("RGBA")
        c3 = apply_corner_scrim(c3.convert("RGB"), cx=480, cy=920, rx=900, ry=340, max_alpha=185)
        dr3 = ImageDraw.Draw(c3)

        # Top-left OLD MODEL pill
        dr3.rounded_rectangle((64, 58, 556, 140), radius=20, fill=(36, 12, 34, 232), outline=(255, 96, 128, 245), width=4)
        dr3.text((98, 71), "95% INVISIBLE?", font=f_tag, fill=(255, 138, 160, 255))

        # Top-right NEW MODEL pill
        dr3.rounded_rectangle((W - 556, 58, W - 64, 140), radius=20, fill=(8, 28, 42, 232), outline=(98, 245, 202, 245), width=4)
        dr3.text((W - 516, 71), "NOTHING MISSING", font=f_tag, fill=(118, 252, 212, 255))

        # Bold bottom-left punchline (clear of bottom-right YouTube timer!)
        draw_glow_headline(c3, (68, 795), "INSIDE OUT.", load_heavy_font(124), (255, 216, 92, 255), stroke_width=10)
        save_youtube_jpg(c3, "YT_Thumbnail_C_Split_Cosmic_Map.jpg")


if __name__ == "__main__":
    build_all()
