"""
Generates Test Plates 6 and 7 on CPU (0% GPU usage) for `stoler.systems` and Episode 1:
  - `test_06_lacuna_unruh_and_cpt_cmb.png`:
      4-panel verification of the Lacuna 2.23M-paper research graph discoveries
      (Griniasty et al. Classical Wave-Medium Unruh Spectrum, Solar-System-to-Gaia Wide-Binary
       Screening + Disk-vs-Halo Gradient, Deng & Handley CPT-Symmetric Quantized Curvature Ladder,
       and the 3-Peak CMB Acoustic Stress-Test).
  - `test_07_episode1_gps_and_landauer_lab.png`:
      4-panel verification for Episode 1 ("Is Time Even Real? Memory, Relativity & GPS Satellites"):
      (Continuous Orbital Clock Shift from ISS -24.6 us/day through 3,189 km Zero-Crossing to GPS +38.6 us/day,
       Uncorrected Navigation Drift km/day, Landauer Memory Arrow dQ >= k_B T ln2 on Static 4D Tapestry,
       and Strong-Field 2PN Black-Hole Shadow Discriminator for BHEX).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["NUMBA_DISABLE_CUDA"] = "1"

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WB_DIR = Path(__file__).resolve().parent
if str(WB_DIR) not in sys.path:
    sys.path.insert(0, str(WB_DIR))

from physics_engines import (  # noqa: E402
    run_episode1_gps_and_landauer_lab,
    run_lacuna_unruh_and_cmb_crucible,
)

RESULTS_DIR = WB_DIR.parent / "website_stoler_systems" / "public" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

BG_DARK = "#070C18"
PANEL_BG = "#0D1528"
CYAN = "#5CE1E6"
GOLD = "#FFD166"
EMERALD = "#34D399"
ROSE = "#FB7185"
MUTED = "#94A3B8"
TEXT = "#F1F5F9"


def style_ax(ax: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.set_title(title, color=TEXT, fontsize=11.5, fontweight="bold", pad=9)
    ax.set_xlabel(xlabel, color="#CBD5E1", fontsize=9.8)
    ax.set_ylabel(ylabel, color="#CBD5E1", fontsize=9.8)
    ax.tick_params(colors="#94A3B8", labelsize=8.8)
    ax.grid(True, color="#1E293B", linestyle="--", linewidth=0.7, alpha=0.75)
    for spine in ax.spines.values():
        spine.set_color("#1E293B")


def build_plate_6() -> Path:
    lac = run_lacuna_unruh_and_cmb_crucible(
        galactic_height_kpc=0.0,
        waist_cutoff_ell=3.4,
        weave_potential_coupling=1.0,
    )

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 9.6), dpi=150)
    fig.patch.set_facecolor(BG_DARK)
    fig.suptitle(
        "TEST PLATE 6 • Lacuna 2.23M-Paper Research Graph Audit: Classical Wave Unruh Analog & CPT-Symmetric CMB Crucible",
        color=TEXT,
        fontsize=14,
        fontweight="bold",
        y=0.975,
    )

    # Panel 1: Griniasty et al. Classical Wave-Medium Unruh Spectrum
    ax1 = axes[0, 0]
    style_ax(
        ax1,
        "1. Classical Wave-Medium Unruh Spectrum (Griniasty et al., PRL)",
        "Dimensionless Rindler Frequency x = 2π c_s Ω / a",
        "Normalized Spectral Density / Occupation",
    )
    ax1.plot(lac["x_freq"], lac["power_spectrum_norm"], color=CYAN, lw=2.6, label="Pullback Power Spectrum x³ / (eˣ - 1)")
    ax1.plot(lac["x_freq"], np.minimum(lac["bose_einstein_occ"], 2.2), color=GOLD, lw=2.0, ls="--", label="Bose-Einstein Factor N(x) = 1 / (eˣ - 1)")
    ax1.axvline(2.821, color=EMERALD, lw=1.4, ls=":")
    ax1.text(3.05, 1.05, "Exact Wien Peak (x = 2.82)\nin Classical Wave Medium!", color=EMERALD, fontsize=8.8, fontweight="bold")
    ax1.set_ylim(0, 1.38)
    ax1.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.5, loc="upper right")

    # Panel 2: Solar System Campfire to Gaia DR4 Wide-Binary Disk vs Halo Test
    ax2 = axes[0, 1]
    style_ax(
        ax2,
        "2. Solar System Screening (<165 AU) to Gaia Wide-Binary Disk vs. Halo Test",
        "Heliocentric / Binary Star Separation r [AU] (Log Scale)",
        "Orbital Velocity Boost Δv / v_Newton [%]",
    )
    ax2.set_xscale("log")
    ax2.plot(lac["r_au_grid"], lac["vel_boost_isolated_pct"], color=MUTED, lw=1.8, ls=":", label="Isolated Star (Zero External Field)")
    ax2.plot(lac["r_au_grid"], lac["vel_boost_halo_pct"], color=GOLD, lw=2.5, ls="--", label="Gaia Halo Wide Binaries (|z_gal|=6 kpc → +27–31%)")
    ax2.plot(lac["r_au_grid"], lac["vel_boost_disk_pct"], color=CYAN, lw=2.8, label="Gaia Disk Wide Binaries (|z_gal|=0 kpc → +15–18%)")
    ax2.axvline(lac["r_crit_au"], color=ROSE, lw=1.8, ls="--")
    ax2.text(420.0, 39.0, f"Campfire Edge\nr_crit = {lac['r_crit_au']:,.0f} AU\n(g_N = a₀)", color=ROSE, fontsize=8.6, fontweight="bold")
    ax2.annotate(
        "Earth (10⁻³⁰⁵⁰) & Saturn (10⁻³²⁰):\n100% Screened Inside Campfire!",
        xy=(10.0, 0.5),
        xytext=(0.7, 22),
        arrowprops=dict(arrowstyle="->", color=EMERALD, lw=1.3),
        color=EMERALD,
        fontsize=8.5,
        fontweight="bold",
    )
    ax2.set_ylim(-2, 58)
    ax2.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.2, loc="upper left")

    # Panel 3: Deng & Handley (2024/2025) Quantized Spatial Curvature & Low-l Quadrupole Suppression
    ax3 = axes[1, 0]
    style_ax(
        ax3,
        "3. CPT-Symmetric Waist Clamping: Low-ℓ Quadrupole Suppression (Deng & Handley)",
        "Large-Angle CMB Multipole ℓ (ℓ = 2 Quadrupole to ℓ = 25)",
        "Large-Angle Power D_ℓ [µK²]",
    )
    ell_low = lac["ell"][:24]
    ax3.plot(ell_low, lac["dl_lcdm"][:24], color=MUTED, lw=2.2, ls="--", marker="o", ms=4, label="Standard ΛCDM (D₂ ≈ 1080–1150 µK²)")
    ax3.plot(ell_low, lac["dl_tnap"][:24], color=CYAN, lw=2.8, marker="s", ms=4.5, label=f"TNaP CPT-Waist Clamped (D₂ = {lac['c2_tnap_uk2']:.0f} µK²)")
    ax3.scatter([2], [331.0], color=GOLD, s=90, zorder=6, label="Planck 2018 Observed Quadrupole (331 µK²)")
    ax3.annotate(
        "71% Quadrupole Suppression at ℓ=2\n(Matches Planck 331 µK² Without\nTouching ℓ ≥ 10!)",
        xy=(2.0, 338.0),
        xytext=(6.2, 310.0),
        arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.5),
        color=GOLD,
        fontsize=8.6,
        fontweight="bold",
    )
    ax3.set_ylim(0, 1450)
    ax3.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.3, loc="lower right")

    # Panel 4: Honest 3-Peak CMB Acoustic Stress-Test (l = 2 to 1000)
    ax4 = axes[1, 1]
    style_ax(
        ax4,
        "4. Honest 3-Peak CMB Stress-Test: Retarded Weave Memory vs. #1 Open Gap",
        "Angular Multipole ℓ (ℓ₁=220, ℓ₂=537, ℓ₃=815)",
        "CMB Acoustic Power D_ℓ [µK²]",
    )
    ax4.plot(lac["ell"], lac["dl_lcdm"], color=MUTED, lw=2.0, ls=":", label=f"Planck ΛCDM Benchmark (R₃₂ = {lac['r32_lcdm']:.2f})")
    ax4.plot(lac["ell"], lac["dl_baryon_only"], color=ROSE, lw=2.0, ls="--", label=f"No-Pleat Baryons Only (Bump 3 Collapses: R₃₂ = {lac['r32_baryon']:.2f})")
    ax4.plot(lac["ell"], lac["dl_tnap"], color=CYAN, lw=2.7, label=f"Pinned Pleat I: 0.55 kpc Weave (R₃₂ = {lac['r32_tnap']:.2f}, ΔN_eff=+0.26)")
    ax4.plot(lac["ell"], lac["dl_tnap_aest"], color=EMERALD, lw=2.0, ls="-.", label=f"Pinned Pleat II: AeST Timelike Slip (R₃₂ = {lac['r32_tnap_aest']:.2f})")
    ax4.annotate(
        "Bullet Cluster in Reverse (σ_T = 0):\nUncharged SO(3) Pleat Holds Bowl Open\n→ Rescues 92–99% of Bump 3 (0 Knobs)!",
        xy=(815, float(lac["dl_tnap"][813])),
        xytext=(535, 3850),
        arrowprops=dict(arrowstyle="->", color=EMERALD, lw=1.5),
        color=EMERALD,
        fontsize=8.5,
        fontweight="bold",
    )
    ax4.set_ylim(0, 6200)
    ax4.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.0, loc="upper right")

    plt.tight_layout(rect=[0.0, 0.01, 1.0, 0.95])
    out_path = RESULTS_DIR / "test_06_lacuna_unruh_and_cpt_cmb.png"
    fig.savefig(out_path, facecolor=BG_DARK)
    plt.close(fig)
    return out_path


def build_plate_7() -> Path:
    ep1 = run_episode1_gps_and_landauer_lab(
        probe_altitude_km=20184.0,
        observer_slice_idx=24,
        ambient_temp_k=310.15,
    )

    fig, axes = plt.subplots(2, 2, figsize=(15.5, 9.6), dpi=150)
    fig.patch.set_facecolor(BG_DARK)
    fig.suptitle(
        "TEST PLATE 7 • Episode 1 Lab: GPS +38.6 µs/day Relativistic Clock Budget, 3,189 km Zero-Crossing & Landauer Memory Arrow",
        color=TEXT,
        fontsize=14,
        fontweight="bold",
        y=0.975,
    )

    # Panel 1: Continuous Altitude Clock Rate Law
    ax1 = axes[0, 0]
    style_ax(
        ax1,
        "1. Continuous Orbital Clock Rate Law: Special vs. General Relativity (Weave Strain)",
        "Satellite Altitude Above Earth Surface h [km]",
        "Clock Rate Shift vs. Ground [µs / day]",
    )
    ax1.plot(ep1["h_grid_km"], ep1["dt_gr_us_day"], color=EMERALD, lw=2.3, ls="--", label="Weave Strain / GR Speedup (+ΔΦ/c²)")
    ax1.plot(ep1["h_grid_km"], ep1["dt_sr_us_day"], color=ROSE, lw=2.3, ls=":", label="Orbital Speed / SR Slowing (-v²/2c²)")
    ax1.plot(ep1["h_grid_km"], ep1["dt_net_us_day"], color=CYAN, lw=3.0, label="Net Atomic Clock Shift (GR + SR)")
    ax1.axhline(0.0, color="#64748B", lw=1.1)
    ax1.axvline(ep1["h_zero_cross_km"], color=GOLD, lw=1.6, ls="--")
    ax1.scatter([400.0, ep1["h_zero_cross_km"], 20184.0, 35786.0], [-24.57, 0.0, 38.64, 46.65], color=GOLD, s=55, zorder=6)
    ax1.annotate(
        "Exact Zero-Crossing\nh = 3,189 km (1.5 R_Earth)\nSR = GR → 0.00 µs/day!",
        xy=(ep1["h_zero_cross_km"], 0.0),
        xytext=(5200.0, -10.5),
        arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.3),
        color=GOLD,
        fontsize=8.5,
        fontweight="bold",
    )
    ax1.annotate(
        "GPS Orbit (20,184 km):\n-7.21 + 45.85 = +38.64 µs/day",
        xy=(20184.0, 38.64),
        xytext=(16500.0, 15.0),
        arrowprops=dict(arrowstyle="->", color=CYAN, lw=1.4),
        color=CYAN,
        fontsize=8.6,
        fontweight="bold",
    )
    ax1.set_ylim(-34, 56)
    ax1.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.3, loc="lower right")

    # Panel 2: Mission Benchmark Bar Comparison & Navigation Drift
    ax2 = axes[0, 1]
    style_ax(
        ax2,
        "2. Key Space Missions: Net Clock Drift & Uncorrected Google Maps Error",
        "Orbital Regime / Spacecraft Mission",
        "Clock Shift [µs/day] & Map Drift [km/day]",
    )
    names = ["ISS LEO\n(400 km)", "Zero-Crossing\n(3,189 km)", "LAGEOS\n(5,900 km)", "GPS Block III\n(20,184 km)", "GEO Ring\n(35,786 km)"]
    net_vals = [-24.57, 0.00, 13.39, 38.64, 46.65]
    drift_km = [abs(v) * 0.299792 for v in net_vals]
    x_pos = np.arange(len(names))
    bars1 = ax2.bar(x_pos - 0.18, net_vals, width=0.35, color=CYAN, label="Net Clock Shift [µs/day]")
    bars2 = ax2.bar(x_pos + 0.18, drift_km, width=0.35, color=GOLD, label="Uncorrected Positioning Error [km/day]")
    ax2.axhline(0.0, color="#64748B", lw=1.0)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(names, fontsize=8.5, color=TEXT)
    for b in bars1:
        yval = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2.0, yval + (1.8 if yval >= 0 else -4.2), f"{yval:+.1f} µs", ha="center", color=CYAN, fontsize=8.0, fontweight="bold")
    for b in bars2:
        yval = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2.0, yval + 1.8, f"{yval:.1f} km", ha="center", color=GOLD, fontsize=8.0, fontweight="bold")
    ax2.set_ylim(-33, 56)
    ax2.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.5, loc="upper left")

    # Panel 3: Landauer Memory Arrow on the Static 4D Tapestry
    ax3 = axes[1, 0]
    style_ax(
        ax3,
        "3. Landauer's Memory Law (ΔQ ≥ k_B T ln 2 = 2.97×10⁻²¹ J/bit at 310 K)",
        "Static 4D Tapestry Slice Index k (0 = Smooth Waist → 40 = Tangled Rim)",
        "Entropy / Stored Memory Records [bits]",
    )
    bar_cols = [CYAN if k <= ep1["observer_slice_idx"] else "#1E293B" for k in ep1["slice_grid"]]
    ax3.bar(ep1["slice_grid"], ep1["recorded_memory_bits"], color=bar_cols, alpha=0.85, label="Accessible Brain Memory Records at Slice k=24")
    ax3.plot(ep1["slice_grid"], ep1["s_ent_bits"], color=GOLD, lw=2.6, ls="--", label="Coarse-Grained Entanglement Entropy S_ent(k)")
    ax3.axvline(ep1["observer_slice_idx"], color="#FFFFFF", lw=2.0, ls="-")
    ax3.text(ep1["observer_slice_idx"] + 1.0, 48, "Brain Needle 'Now' (k=24)\n• Left (k≤24): Paid Landauer Heat\n• Right (k>24): 0.0 Bits ('Open Future')", color=TEXT, fontsize=8.4, fontweight="bold")
    ax3.set_ylim(0, 128)
    ax3.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.3, loc="upper left")

    # Panel 4: Strong-Field 1PN Exact Match vs 2PN Black-Hole Shadow Discriminator
    ax4 = axes[1, 1]
    style_ax(
        ax4,
        "4. Strong-Field Weave Audit: 1PN Exact Match vs. 2PN BHEX Shadow Test",
        "Dimensionless Gravitational Potential U = GM / (r c²)",
        "Effective Optical Refractive Index n(U)",
    )
    ax4.plot(ep1["u_grid"], ep1["n_weave_exp"], color=CYAN, lw=2.8, label="Exponential Weave n(U) = exp(2U) (Throat: 5.437 r_g)")
    ax4.plot(ep1["u_grid"], ep1["n_schwarzschild"], color=ROSE, lw=2.3, ls="--", label="Isotropic Schwarzschild GR (Horizon: 5.196 r_g)")
    ax4.annotate(
        "Solar System & GPS (U < 10⁻⁵):\nExact 1PN Match (γ = 1, β = 1,\nCassini 10⁻⁵ & Mercury 42.98\"/cy)",
        xy=(0.08, 1.18),
        xytext=(0.14, 7.5),
        arrowprops=dict(arrowstyle="->", color=EMERALD, lw=1.4),
        color=EMERALD,
        fontsize=8.5,
        fontweight="bold",
    )
    ax4.annotate(
        "Black-Hole Photon Ring (U ~ 0.5–1.0):\n+4.63% Larger Shadow Radius!\nDecisive Test for BHEX Space VLBI",
        xy=(1.0, float(np.exp(2.0))),
        xytext=(0.45, 14.5),
        arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.4),
        color=GOLD,
        fontsize=8.5,
        fontweight="bold",
    )
    ax4.set_ylim(0.8, 22.0)
    ax4.legend(facecolor=BG_DARK, edgecolor="#334155", labelcolor=TEXT, fontsize=8.3, loc="upper left")

    plt.tight_layout(rect=[0.0, 0.01, 1.0, 0.95])
    out_path = RESULTS_DIR / "test_07_episode1_gps_and_landauer_lab.png"
    fig.savefig(out_path, facecolor=BG_DARK)
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    import base64
    import shutil
    from io import BytesIO
    from PIL import Image

    p6 = build_plate_6()
    p7 = build_plate_7()
    print(f"Generated {p6.name} ({p6.stat().st_size // 1024} KB)")
    print(f"Generated {p7.name} ({p7.stat().st_size // 1024} KB)")

    art_dir = Path(r"C:\Users\david\.gemini\antigravity\brain\24d450e3-3bf2-4f95-baa8-6f3120d34d3b")
    if art_dir.exists():
        shutil.copy2(p6, art_dir / p6.name)
        shutil.copy2(p7, art_dir / p7.name)

        def to_b64_jpeg(p: Path) -> str:
            img = Image.open(p).convert("RGB")
            img.thumbnail((1100, 680), Image.Resampling.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=88)
            raw = buf.getvalue()
            b64 = base64.b64encode(raw).decode("ascii")
            assert base64.b64decode(b64, validate=True) == raw
            return f"data:image/jpeg;base64,{b64}"

        u6 = to_b64_jpeg(p6)
        u7 = to_b64_jpeg(p7)
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  body {{ margin:0; padding:10px 14px; background:#070c18; color:#f1f5f9; font-family:Segoe UI,sans-serif; }}
  .hdr {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
  .title {{ font-size:13.5px; font-weight:700; color:#5ce1e6; }}
  .sub {{ font-size:11px; color:#94a3b8; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  .card {{ background:#0d1528; border:1px solid rgba(92,225,230,0.3); border-radius:10px; padding:8px; }}
  .card h4 {{ margin:0 0 6px 0; font-size:11.5px; color:#ffd166; }}
  .card img {{ width:100%; height:auto; border-radius:6px; display:block; }}
</style>
</head>
<body>
  <div class="hdr">
    <div class="title">New Workbench Test Plates 6 &amp; 7 — Lacuna Literature Crucible + Episode 1 GPS &amp; Landauer Lab</div>
    <div class="sub">CPU-Rendered • Added to Science Workbench (Tabs 6 &amp; 7) + stoler.systems</div>
  </div>
  <div class="grid">
    <div class="card">
      <h4>Plate 6: Lacuna Unruh Wave Analog (Griniasty et al.) &amp; CPT CMB Peaks (Deng &amp; Handley)</h4>
      <img src="{u6}" alt="Test Plate 6"/>
    </div>
    <div class="card">
      <h4>Plate 7: Episode 1 Lab — GPS +38.6 µs/day, 3,189 km Zero-Crossing &amp; Landauer Memory Arrow</h4>
      <img src="{u7}" alt="Test Plate 7"/>
    </div>
  </div>
</body>
</html>"""
        (art_dir / "plates_6_and_7_preview.html").write_text(html, encoding="utf-8")
        print("Copied plates to artifact dir & built byte-verified inline preview HTML!")

