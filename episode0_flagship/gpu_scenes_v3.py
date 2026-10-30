"""
Episode 0 v3 ('Sagan Edition') Upgraded RTX 5080 CUDA `1920x1080` 3D Scene Director (`gpu_scenes_v3.py`):
Inherits all perfected scenes from `GPU3DSceneDirector` (`gpu_scenes_v2.py`) and adds chunk-accurate,
high-detail 3D simulations for every visual requested by David:
  1. Scene 05 Part A (`chunk_19..21`):
       - Two sculpted brushed-brass rings (one Giant Outer Ring `R=3.3` + one Ultra-Tiny Pinpoint Ring `R=0.11`)
         visibly dipping into a shimmering, rippling dark dish of iridescent soapy fluid and pulling apart
         to stretch a glistening rainbow catenoid soap film!
       - Dramatic `7:47` macro camera zoom (`dist: 9.2 -> 0.68`) right onto the tiny `R=0.11` inner ring
         to reveal it as the pinched Big Bang singularity throat, then smooth zoom back out!
       - Visual wave-cutoff demonstration: fine cyan-gold acoustic ripples fit cleanly along the pinched sheet,
         while a huge crimson sky-spanning temperature wave physically runs out of room and flattens before the throat!
       - Sculpted 3D Hubble Space Telescope (silver optical barrel + twin sapphire solar wings) & 18-segment
         Golden James Webb Space Telescope orbiting deep space and scanning the 3D Ancient Cosmic Light (`CMB`) sky dome!
  2. Scene 05 Part B (`chunk_22`):
       - Crystal-clear 3D Double-Slit wave tank: connected weave carries a single photon wave through BOTH slits
         to paint 7 bright-and-dark emerald interference stripes, until a sleek 3D Crystalline Ring Sensor closes
         around Slit 1 and physically absorbs/damps that slit's wave (like a finger muting a guitar string),
         turning the stripes into a smooth unstriped band!
  3. Scene 07 (`chunk_25..27` Sagan Galaxy Visualization):
       - Part 7A: Blazing Golden Sun pressing a steep, deep campfire-gold local funnel (`50,000,000x` stronger
         than deep space's faint stretch) around inner planets — zero confusing 'motion bubble'!
       - Part 7B (`10:19+` Sagan sweep): Unmistakable 3D explanation of WHY outer stars aren't flung out of their galaxy!
         4 blazing White-Gold Hero Outer Stars whip around the galaxy's suburbs (`R=4.95`): dashed crimson straight-line
         tangent trajectories show where they WOULD fly off into empty space if held by central starlight alone,
         while the taut, upward-banked Emerald Cosmic Tablecloth Bowl curves them smoothly inward along a closed orbit!
  4. Scene 08 (`chunk_28` + `4.2s` silent showcase -> `chunk_29` -> `chunk_30`):
       - Dedicated 29-second 3D Protogalaxy Pleat-Folding simulation: 24,000 young stars condense inward, visibly
         dragging the 340x340 cloth threads radially inward and folding up a crisp, multi-ridge 3D circumferential
         fabric pleat collar around the newborn galaxy during the 4.2s showcase pause before the cluster crash!
  5. Scene 09 (`chunk_31..32` Sagan Outro -> `9.6s` Wordless Multi-Galaxy Cosmic Zoom-Out -> `chunk_33` Caveat):
       - Continuous 3D cosmic camera pullback (`dist: 4.8 -> 84.0`) starting inside our home spiral galaxy and
         zooming steadily out across a procedural 3D Deep-Field Universe of 175 distinct tilted 3D spiral &
         elliptical galaxies (`151,000` stars!) suspended along gossamer cosmic threads!
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from gpu_renderer_core import (
    CameraMatrix,
    CameraPose,
    interpolate_camera,
    make_sphere_mesh,
    make_torus_mesh,
    make_tube_along_curve,
    smootherstep01,
    smoothstep01,
)
from gpu_scenes_v2 import GPU3DSceneDirector


def _find_chunk(scene: Optional[dict], prefix: str) -> Optional[dict]:
    if not scene:
        return None
    for ch in scene.get("chunks") or []:
        if ch["chunk_id"].startswith(prefix):
            return ch
    return None


class GPU3DSceneDirectorV3(GPU3DSceneDirector):
    """Upgraded v3 RTX 5080 1080p 3D Scene Director with chunk-locked timing & 5 major new 3D simulations."""

    def __init__(self, device: torch.device | None = None):
        super().__init__(device=device)
        self._init_hubble_telescope()
        self._init_protogalaxy_buffers()
        self._init_deep_field_universe()

    def _init_hubble_telescope(self) -> None:
        """Sculpted 3D Hubble Space Telescope (`HST`) in local coords: silver optical barrel + twin blue solar wings."""
        # Main cylindrical optical tube along local Z (`z in [-0.85, +0.85]`, radius stepped `0.28 -> 0.22`)
        z_b = torch.linspace(-0.85, 0.85, 48, device=self.dev)
        r_b = torch.where(z_b < -0.20, 0.29, 0.22)
        c_b = torch.stack([torch.zeros_like(z_b), torch.zeros_like(z_b), z_b], dim=-1)
        self.hst_body_P, self.hst_body_N = make_tube_along_curve(c_b, r_b, n_around=28)

        # Twin rectangular sapphire solar panels (`x in [-1.25, -0.34]` & `[+0.34, +1.25]`, `z in [-0.48, +0.48]`)
        u_x = torch.linspace(0.34, 1.25, 24, device=self.dev)
        v_z = torch.linspace(-0.46, 0.46, 32, device=self.dev)
        xx, zz = torch.meshgrid(u_x, v_z, indexing="ij")
        yy = torch.zeros_like(xx)
        wing_R = torch.stack([xx, yy, zz], dim=-1)
        wing_L = torch.stack([-xx, yy, zz], dim=-1)
        self.hst_wings_P = torch.cat([wing_L, wing_R], dim=0)

        # Connecting solar-boom strut along X (`[-1.25 .. +1.25]`)
        sx = torch.linspace(-1.25, 1.25, 24, device=self.dev)
        self.hst_boom_P, self.hst_boom_N = make_tube_along_curve(
            torch.stack([sx, torch.zeros_like(sx), torch.zeros_like(sx)], dim=-1), 0.032, n_around=12
        )

    def _init_protogalaxy_buffers(self) -> None:
        """24,000-star condensing young protogalaxy cloud for Scene 08 Act A (`chunk_28` + 4.2s showcase)."""
        g = torch.Generator(device="cpu")
        g.manual_seed(818)
        n = 24000
        u = torch.rand(n, generator=g)
        self.pg_r_final = 0.18 + (u ** 0.78) * 1.65
        self.pg_r_init = 1.45 + (u ** 0.65) * 4.45
        arm = torch.randint(0, 2, (n,), generator=g).float() * math.pi
        self.pg_th0 = arm + 1.8 * torch.log(self.pg_r_final + 0.3) + 0.38 * torch.randn(n, generator=g)
        self.pg_z_init = torch.randn(n, generator=g) * 1.15
        self.pg_z_final = torch.randn(n, generator=g) * 0.14

        core_w = torch.exp(-(self.pg_r_final / 0.85) ** 2)
        lum = 0.38 + 0.92 * (torch.rand(n, generator=g) ** 1.6)
        cr = (1.30 * core_w + 0.35 * (1.0 - core_w)) * lum
        cg = (0.95 * core_w + 0.78 * (1.0 - core_w)) * lum
        cb = (0.48 * core_w + 1.32 * (1.0 - core_w)) * lum

        self.pg_r_init = self.pg_r_init.to(self.dev)
        self.pg_r_final = self.pg_r_final.to(self.dev)
        self.pg_th0 = self.pg_th0.to(self.dev)
        self.pg_z_init = self.pg_z_init.to(self.dev)
        self.pg_z_final = self.pg_z_final.to(self.dev)
        self.pg_rgb = torch.stack([cr, cg, cb], dim=-1).to(self.dev)
        self.pg_sz = (1.25 + 1.15 * core_w).to(self.dev)

    def _init_deep_field_universe(self) -> None:
        """
        175 crisp Hubble/JWST Ultra-Deep-Field 3D spiral & golden elliptical galaxies (`245,000` pinpoint stars!)
        distributed isotropically across `R = 13 .. 96` for the Sagan Finale 10s Cosmic Pullback!
        """
        rng = np.random.default_rng(909)
        n_gal = 175
        stars_per_gal = 1400

        idx = np.arange(n_gal, dtype=np.float32)
        phi = math.pi * (3.0 - math.sqrt(5.0)) * idx
        cos_th = 1.0 - 2.0 * ((idx + 0.5) / n_gal)
        sin_th = np.sqrt(np.maximum(0.0, 1.0 - cos_th * cos_th))
        radii = 13.5 + 82.0 * ((idx / max(1, n_gal - 1)) ** 0.76) + rng.normal(0.0, 2.0, size=n_gal).astype(np.float32)
        # Shuffle radii independently of polar angle so near, mid, and distant galaxies fill the ENTIRE 3D sky!
        rng.shuffle(radii)
        centers = np.stack([radii * np.cos(phi) * sin_th, radii * np.sin(phi) * sin_th, radii * cos_th * 0.86], axis=-1)

        all_xyz = []
        all_rgb = []
        all_sz = []

        for g_i in range(n_gal):
            is_ellip = (g_i % 5 == 4)
            g_scale = float(rng.uniform(0.55, 1.15)) * (1.0 + 0.008 * radii[g_i])
            u = rng.random(stars_per_gal).astype(np.float32)

            if is_ellip:
                rr = (u ** 0.85) * 1.18 * g_scale
                th = rng.uniform(0.0, 2.0 * math.pi, stars_per_gal).astype(np.float32)
                ph_e = np.arccos(rng.uniform(-1.0, 1.0, stars_per_gal)).astype(np.float32)
                lx = rr * np.sin(ph_e) * np.cos(th)
                ly = rr * np.sin(ph_e) * np.sin(th) * 0.68
                lz = rr * np.cos(ph_e) * 0.50
                lum = (0.28 + 0.72 * (rng.random(stars_per_gal).astype(np.float32) ** 1.7)) * np.exp(-u * 1.15)
                rgb = np.stack([1.18 * lum, 0.84 * lum, 0.44 * lum], axis=-1)
            else:
                n_arms = 2 if (g_i % 3 != 0) else 3
                # 25% golden central bulge + 75% crisp logarithmic spiral arms & star-forming disk!
                n_bulge = stars_per_gal // 4
                is_bulge = np.arange(stars_per_gal) < n_bulge
                arm_a = rng.integers(0, n_arms, size=stars_per_gal).astype(np.float32) * (2.0 * math.pi / n_arms)
                rr_arm = (0.10 + 1.85 * (u ** 0.78)) * g_scale
                ang = arm_a + 2.15 * np.log(u + 0.14) + rng.normal(0.0, 0.24 + 0.14 * u, size=stars_per_gal).astype(np.float32)
                rr_b = (u ** 0.9) * 0.36 * g_scale
                th_b = rng.uniform(0.0, 2.0 * math.pi, stars_per_gal).astype(np.float32)
                lx = np.where(is_bulge, rr_b * np.cos(th_b), rr_arm * np.cos(ang))
                ly = np.where(is_bulge, rr_b * np.sin(th_b), rr_arm * np.sin(ang))
                lz = np.where(
                    is_bulge,
                    rng.normal(0.0, 0.12 * g_scale, size=stars_per_gal).astype(np.float32),
                    rng.normal(0.0, 0.045 * g_scale, size=stars_per_gal).astype(np.float32),
                )
                cw = np.where(is_bulge, 1.0, np.exp(-(u / 0.28) ** 2))
                lum = (0.26 + 0.78 * (rng.random(stars_per_gal).astype(np.float32) ** 1.65)) * (0.45 + 0.55 * np.exp(-0.55 * u))
                tint = g_i % 3
                if tint == 0:
                    r_c = 1.18 * cw + 0.28 * (1.0 - cw)
                    g_c = 0.86 * cw + 0.72 * (1.0 - cw)
                    b_c = 0.44 * cw + 1.28 * (1.0 - cw)
                elif tint == 1:
                    r_c = 1.15 * cw + 0.32 * (1.0 - cw)
                    g_c = 0.88 * cw + 0.85 * (1.0 - cw)
                    b_c = 0.48 * cw + 1.12 * (1.0 - cw)
                else:
                    r_c = 1.22 * cw + 0.82 * (1.0 - cw)
                    g_c = 0.84 * cw + 0.54 * (1.0 - cw)
                    b_c = 0.46 * cw + 1.08 * (1.0 - cw)
                rgb = np.stack([r_c * lum, g_c * lum, b_c * lum], axis=-1)

            q_mat, _ = np.linalg.qr(rng.normal(size=(3, 3)).astype(np.float32))
            loc_pts = np.stack([lx, ly, lz], axis=-1) @ q_mat.T + centers[g_i]
            all_xyz.append(loc_pts)
            all_rgb.append(rgb)
            all_sz.append(np.full(stars_per_gal, 0.92 if radii[g_i] < 42.0 else 0.78, dtype=np.float32))

        self.df_pts = torch.tensor(np.concatenate(all_xyz, axis=0), device=self.dev, dtype=torch.float32)
        self.df_rgb = torch.tensor(np.concatenate(all_rgb, axis=0), device=self.dev, dtype=torch.float32)
        self.df_sz = torch.tensor(np.concatenate(all_sz, axis=0), device=self.dev, dtype=torch.float32)

    def render_scene_frame_v3(self, scene: dict, t: float) -> np.ndarray:
        scene_id = scene["id"]
        dur = float(scene["duration_sec"])
        prog = max(0.0, min(1.0, t / max(0.001, dur)))

        if scene_id == "scene04":
            self._render_scene04_v3(scene, t, dur, prog)
        elif scene_id == "scene05":
            self._render_scene05_v3(scene, t, dur, prog)
        elif scene_id == "scene07":
            self._render_scene07_v3(scene, t, dur, prog)
        elif scene_id == "scene08":
            self._render_scene08_v3(scene, t, dur, prog)
        elif scene_id == "scene09":
            self._render_scene09_v3(scene, t, dur, prog)
        else:
            fn = getattr(self, f"_render_{scene_id}", self._render_scene02)
            fn(t, dur, prog)
        return self.canvas.finalize_srgb_uint8(exposure=1.06, bloom_strength=0.44)

    # -----------------------------------------------------------------------
    # SCENE 04 V3: Chunk-Locked 180-Degree Hourglass Flip + Smooth Throat Zoom
    # -----------------------------------------------------------------------
    def _render_scene04_v3(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch16 = _find_chunk(scene, "chunk_16")
        ch18 = _find_chunk(scene, "chunk_18")
        t_flip0 = ch16["local_start"] + 0.8 if ch16 else dur * 0.25
        t_throat = ch18["local_start"] + 1.5 if ch18 else dur * 0.65

        flip = smootherstep01((t - t_flip0) / 5.5)
        u_throat = smootherstep01((t - t_throat) / 6.0) * (1.0 - 0.55 * smootherstep01((t - (dur - 6.0)) / 5.0))
        dist = 11.2 - 1.4 * flip - 6.9 * u_throat
        pose = CameraPose(
            azim=0.25 + 2.85 * prog,
            elev=0.18 - 0.28 * flip * (1.0 - u_throat) + 0.10 * u_throat,
            dist=dist,
            target=(0.0, 0.0, 0.6 * (1.0 - flip)),
            roll_deg=180.0 * flip,
            fov_deg=46.0 - 3.0 * u_throat,
        )
        self._render_hourglass_core(t, flip_amt=flip, cam_pose=pose)

    # -----------------------------------------------------------------------
    # SCENE 05 V3:
    #   Act 5A-1/2: Brass Rings Dipping in Soapy Fluid -> Stretching Soap Film -> Tiny Singularity Ring Macro Zoom!
    #   Act 5A-3:   Blocked Sky-Spanning Temperature Wave vs Fine Ripples!
    #   Act 5A-4:   Sculpted 3D Hubble & JWST Peering Into Deep Space Mapping the Oldest Light!
    #   Act 5B:     Chilled-Out Double-Slit Wave + Guitar-String Finger / Ring Sensor Absorbing Slit 1!
    # -----------------------------------------------------------------------
    def _render_scene05_v3(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch20 = _find_chunk(scene, "chunk_20")
        ch21 = _find_chunk(scene, "chunk_21")
        ch22 = _find_chunk(scene, "chunk_22")

        t20_s = ch20["local_start"] if ch20 else 14.5
        t20_e = ch20["local_end"] if ch20 else 47.0
        t21_s = ch21["local_start"] if ch21 else 49.5
        t21_e = ch21["local_end"] if ch21 else 89.5
        t22_s = ch22["local_start"] if ch22 else 92.5

        if t < t22_s - 0.8:
            # Check if we are in the Hubble + JWST Deep-Space Ancient Light segment (second half of chunk_21!)
            t_telescopes = t21_s + 0.56 * (t21_e - t21_s)
            if t >= t_telescopes:
                u_tel = min(1.0, (t - t_telescopes) / max(1.0, (t22_s - 0.8) - t_telescopes))
                self._render_hubble_jwst_cmb_v3(t, u_tel)
                return

            # --- SOAP RINGS DIPPING, STRETCHING, TINY SINGULARITY ZOOM & WAVE CUTOFF ---
            # 1. Dip & Pull-Apart kinematics:
            #    Before `t20_s + 8.5s`: rings sit dipped inside the shimmering soapy dish (`z = -1.95`, `sep = 0.08`).
            #    From `t20_s + 8.5s -> t20_e - 1.5s`: rings lift out of the soapy fluid (`z: -1.95 -> 0.0`) and
            #    spread apart (`x_out: 0 -> -2.9`, `x_in: 0 -> +2.7`), stretching the iridescent soap film!
            t_dip_lift = t20_s + 8.2
            lift_u = smootherstep01((t - t_dip_lift) / 5.2)
            stretch_u = smootherstep01((t - (t_dip_lift + 2.6)) / 10.5)

            z_rings = -1.92 * (1.0 - lift_u)
            x_out = -2.95 * stretch_u
            x_in = +2.75 * stretch_u
            r_out = 3.25
            # Ultra-tiny inner ring (`R = 0.11` — 30x smaller than outer ring!) representing Big Bang singularity throat!
            r_in = 0.11

            # 2. Macro Zoom Into Tiny Singularity Ring (`t20_e - 7.5s` through the 2.5s showcase pause `t21_s - 0.4s`!)
            z_in_w = smootherstep01((t - (t20_e - 7.5)) / 2.8) * (1.0 - smootherstep01((t - (t20_e + 1.3)) / 1.6))

            # Camera smoothly tracks from dipping basin -> stretched film -> TIGHT MACRO ZOOM (`dist=0.68`!) on `(x_in, 0, z_rings)` -> wide wave view!
            base_az = -0.68 + 0.55 * min(1.0, t / max(1.0, t21_e))
            base_el = 0.30 - 0.08 * stretch_u
            base_dist = 9.8 - 1.0 * stretch_u

            cam_pose = CameraPose(
                azim=base_az * (1.0 - z_in_w) + 0.38 * z_in_w,
                elev=base_el * (1.0 - z_in_w) + 0.12 * z_in_w,
                dist=base_dist * (1.0 - z_in_w) + 0.72 * z_in_w,
                target=(
                    0.0 * (1.0 - z_in_w) + x_in * z_in_w,
                    0.0,
                    (-0.55 * (1.0 - stretch_u)) * (1.0 - z_in_w) + z_rings * z_in_w,
                ),
                fov_deg=46.0 - 7.0 * z_in_w,
            )
            cam = CameraMatrix(cam_pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.014, 0.046, 0.102), nebula_b=(0.052, 0.032, 0.078), star_gain=0.48)

            # A. Shimmering Dark Dish of Iridescent Soapy Fluid (`z = -2.05`, visible during dipping & pulling apart!)
            dish_fade = 1.0 - smootherstep01((t - (t21_s + 2.0)) / 3.0)
            if dish_fade > 0.02:
                rr_d = 4.65 * self.pol_r
                tt_d = self.pol_th
                dx = rr_d * torch.cos(tt_d)
                dy = rr_d * torch.sin(tt_d)
                # Concentric capillary liquid ripples radiating as brass rings lift out of the soapy fluid!
                rip_amp = 0.065 * math.exp(-max(0.0, t - (t_dip_lift + 4.5)) * 0.18)
                dz = -2.05 + rip_amp * torch.sin(5.2 * rr_d - 4.2 * t) * torch.exp(-rr_d * 0.32)
                P_dish = torch.stack([dx, dy, dz], dim=-1)
                iri = 0.5 + 0.5 * torch.sin(3.6 * rr_d - 1.8 * t + 0.5 * tt_d)
                dish_rgb = torch.stack(
                    [0.05 + 0.18 * iri, 0.22 + 0.28 * (1.0 - iri), 0.42 + 0.35 * iri], dim=-1
                )
                self.canvas.render_surface_mesh(
                    P_dish, dish_rgb, cam, alpha=0.82 * dish_fade, shininess=110.0,
                    specular_strength=1.55, fresnel_rgb=(0.55, 0.92, 1.0), write_depth=False
                )
                # Brushed-brass dish rim
                Pr_d, Nr_d = make_torus_mesh((0.0, 0.0, -2.02), 4.68, 0.065, 160, 20, self.dev, axis="z")
                self.canvas.render_surface_mesh(Pr_d, (0.72, 0.56, 0.22), cam, normals=Nr_d, alpha=0.88 * dish_fade, two_sided=False)

            # B. Stretched Iridescent Catenoid Soap Film between Giant Outer Ring (`x_out`, `R=3.25`) & Tiny Singularity Ring (`x_in`, `R=0.11`)!
            if lift_u > 0.03:
                span = max(0.06, x_in - x_out)
                x_lin = torch.linspace(x_out, x_in, 280, device=self.dev)
                th_lin = torch.linspace(0.0, 2.0 * math.pi, 260, device=self.dev)
                xx, tt = torch.meshgrid(x_lin, th_lin, indexing="ij")
                s01 = torch.clamp((xx - x_out) / span, 0.0, 1.0)  # 0 at Giant Outer Ring -> 1 at Tiny Inner Singularity Ring (`R=0.11`)!

                # Smooth catenoid-like soap-film funnel narrowing all the way down to `r_in = 0.11`!
                one_minus_s = torch.clamp(1.0 - s01, min=0.0, max=1.0)
                r_base = r_in + (r_out - r_in) * (one_minus_s ** 1.58)

                # Wave cutoff demonstration activates in `chunk_21` (`t >= t21_s - 0.5`)!
                wave_demo = smoothstep01((t - (t21_s - 0.5)) / 2.2)
                # 1) Short primordial waves (`n=7` standing mode): fit cleanly all along the sheet!
                short_wave = (0.045 + 0.065 * wave_demo) * torch.sin(7.0 * math.pi * s01) * torch.cos(6.0 * tt - 3.0 * t) * (1.0 - 0.72 * s01)
                # 2) Giant sky-spanning wave (`wavelength > throat`): tries to enter from wide rim, physically choked to ZERO before pinched throat!
                giant_blocked = (0.46 * wave_demo) * torch.sin(math.pi * torch.clamp(s01 * 1.45, 0.0, 1.0)) * (one_minus_s ** 3.2) * torch.cos(tt + 1.5 * t)

                rr_f = torch.clamp(r_base + short_wave + giant_blocked, min=0.04)
                fy = rr_f * torch.cos(tt)
                fz = z_rings + rr_f * torch.sin(tt)
                P_film = torch.stack([xx, fy, fz], dim=-1)

                # Rainbow thin-film soap iridescence + crimson highlight on the blocked sky-spanning wave!
                thin_phase = 5.5 * s01 + 1.5 * torch.sin(2.0 * tt - 0.8 * t)
                blk_glow = torch.clamp(torch.abs(giant_blocked) * 2.6, 0.0, 1.0)
                sh_glow = torch.clamp(torch.abs(short_wave) * 9.0, 0.0, 1.0)
                pinch_glow = torch.exp(-((1.0 - s01) / 0.08) ** 2)  # Bright golden-cyan glow right at the tiny singularity throat!

                film_rgb = torch.stack(
                    [
                        0.14 + 0.22 * (0.5 + 0.5 * torch.sin(thin_phase)) + 0.98 * blk_glow + 0.75 * pinch_glow,
                        0.58 + 0.36 * sh_glow + 0.25 * pinch_glow - 0.28 * blk_glow,
                        0.96 + 0.22 * (0.5 + 0.5 * torch.cos(thin_phase)) - 0.58 * blk_glow,
                    ],
                    dim=-1,
                )
                film_emit = torch.stack(
                    [
                        0.48 * blk_glow + 0.45 * pinch_glow,
                        0.32 * sh_glow + 0.34 * pinch_glow,
                        0.42 * sh_glow + 0.15 * pinch_glow,
                    ],
                    dim=-1,
                )
                self.canvas.render_surface_mesh(
                    P_film, film_rgb, cam, emissive_rgb=film_emit, alpha=0.80,
                    shininess=96.0, specular_strength=1.25, fresnel_rgb=(0.55, 0.96, 1.0),
                    wire_stride=9, wire_rgb=(0.62, 0.95, 1.0), wire_boost=0.34
                )

            # C. Sculpted Giant Outer Brass Ring (`R=3.25`) & Ultra-Tiny Inner Singularity Brass Ring (`R=0.11`)!
            P_out, N_out = make_torus_mesh((x_out, 0.0, z_rings), r_out, 0.095, 200, 30, self.dev, axis="x")
            P_inn, N_inn = make_torus_mesh((x_in, 0.0, z_rings), r_in, 0.022, 140, 26, self.dev, axis="x")
            self.canvas.render_surface_mesh(
                P_out, (0.95, 0.74, 0.24), cam, normals=N_out, emissive_rgb=(0.16, 0.11, 0.02),
                alpha=0.99, two_sided=False, shininess=105.0, specular_strength=1.4, supersample=(3, 3)
            )
            # Tiny inner singularity ring gleams warmly so even at wide scale & extreme close-up it is razor-sharp!
            self.canvas.render_surface_mesh(
                P_inn, (1.0, 0.86, 0.36), cam, normals=N_inn, emissive_rgb=(0.52, 0.38, 0.10),
                alpha=0.99, two_sided=False, shininess=115.0, specular_strength=1.6, supersample=(4, 4)
            )
        else:
            # --- ACT 5B (`chunk_22`): CHILLED-OUT DOUBLE-SLIT WAVE + PHYSICAL RING SENSOR ABSORBING SLIT 1 ---
            ch22_dur = (ch22["local_end"] - ch22["local_start"]) if ch22 else 52.0
            u = max(0.0, min(1.0, (t - t22_s) / max(1.0, ch22_dur)))
            # Sensor activates right when David says "place a physical sensor right inside one opening" (`u ~ 0.54`)!
            sensor_on = smootherstep01((u - 0.50) / 0.11)

            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-1.18, elev=0.46, dist=11.4, target=(0.2, 0.0, 0.2), fov_deg=46.0)),
                    (0.44, CameraPose(azim=-0.76, elev=0.34, dist=9.2, target=(0.8, 0.0, 0.35), roll_deg=-2.0, fov_deg=46.0)),
                    (0.70, CameraPose(azim=-0.92, elev=0.32, dist=8.6, target=(0.6, 0.25, 0.35), roll_deg=1.0, fov_deg=46.0)),
                    (1.00, CameraPose(azim=-0.72, elev=0.36, dist=9.8, target=(0.7, 0.0, 0.30), fov_deg=46.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.010, 0.044, 0.095), nebula_b=(0.018, 0.062, 0.068), star_gain=0.35)

            # 1. Connected 340x340 Fabric Wave Surface (`Emitter x=-4.8` -> `Slits x=-1.2, y=+-1.25` -> `Back Wall x=+4.65`)
            tx = self.grid_x * 5.5
            ty = self.grid_y * 4.6
            k_wave = 5.5
            omega = 5.8

            r_emit = torch.sqrt((tx + 4.8) ** 2 + ty ** 2 + 0.08)
            w_left = (0.28 / torch.sqrt(r_emit * 0.4 + 0.6)) * torch.cos(k_wave * r_emit - omega * t)

            d1 = torch.sqrt((tx + 1.2) ** 2 + (ty - 1.25) ** 2 + 0.04)  # Slit 1 (+1.25, where Ring Sensor sits!)
            d2 = torch.sqrt((tx + 1.2) ** 2 + (ty + 1.25) ** 2 + 0.04)  # Slit 2 (-1.25, open!)
            amp1 = 0.27 / torch.sqrt(d1 + 0.38)
            amp2 = 0.27 / torch.sqrt(d2 + 0.38)

            # When `sensor_on = 0`: both slits radiate coherently -> crisp diamond wave-interference!
            # When `sensor_on = 1`: Ring Sensor at Slit 1 absorbs/damps Slit 1's wave (like a finger muting a guitar string!),
            # leaving only Slit 2's smooth single wave -> ZERO interference stripes!
            w_slit1 = (1.0 - 0.94 * sensor_on) * amp1 * torch.cos(k_wave * d1 - omega * t)
            w_slit2 = amp2 * torch.cos(k_wave * d2 - omega * t)
            w_right = w_slit1 + w_slit2

            gate = torch.sigmoid((tx + 1.2) * 14.0)
            wz = (1.0 - gate) * w_left + gate * w_right
            P_tank = torch.stack([tx, ty, wz], dim=-1)

            crest = torch.clamp(torch.abs(wz) * 3.1, 0.0, 1.0)
            tank_rgb = torch.stack([0.05 + 0.20 * crest, 0.36 + 0.66 * crest, 0.68 + 0.42 * crest], dim=-1)
            self.canvas.render_surface_mesh(
                P_tank, tank_rgb, cam,
                emissive_rgb=torch.stack([0.04 * crest, 0.36 * crest, 0.46 * crest], dim=-1),
                alpha=0.92, shininess=92.0, specular_strength=1.2, fresnel_rgb=(0.35, 0.95, 1.0),
                wire_stride=12, wire_rgb=(0.32, 0.85, 1.0), wire_boost=0.24
            )

            # 2. Glowing Photon Emitter Orb at `(-4.8, 0, 0.22)`
            Pe, _, _ = make_sphere_mesh((-4.8, 0.0, 0.22), 0.24, 42, 30, self.dev)
            self.canvas.render_surface_mesh(Pe, (0.45, 0.95, 1.0), cam, emissive_rgb=(0.55, 0.95, 1.0), two_sided=False)

            # 3. Brushed-Brass Double-Slit Wall at `x = -1.2` (`Slit 1` at `y = +1.25`, `Slit 2` at `y = -1.25`)
            for y0, y1 in ((-4.6, -1.55), (-0.95, 0.95), (1.55, 4.6)):
                s_b = torch.linspace(y0, y1, 48, device=self.dev)
                c_b = torch.stack([torch.full_like(s_b, -1.2), s_b, torch.full_like(s_b, 0.22)], dim=-1)
                Pb, Nb = make_tube_along_curve(c_b, 0.14, n_around=16)
                self.canvas.render_surface_mesh(Pb, (0.90, 0.70, 0.25), cam, normals=Nb, two_sided=False, shininess=90.0)

            # 4. Sleek 3D Crystalline Ring Sensor right around Slit 1 (`(-1.2, +1.25, 0.20)`)!
            #    Glides smoothly into position and glows warm amber as it absorbs the Slit 1 wave!
            sens_z = 0.20 + 1.35 * (1.0 - sensor_on)
            Psens, Nsens = make_torus_mesh((-1.2, 1.25, sens_z), 0.34, 0.068, 96, 24, self.dev, axis="x")
            self.canvas.render_surface_mesh(
                Psens,
                (0.35 + 0.65 * sensor_on, 0.75 - 0.15 * sensor_on, 0.95 - 0.75 * sensor_on),
                cam,
                normals=Nsens,
                emissive_rgb=(0.85 * sensor_on, 0.42 * sensor_on, 0.08 * sensor_on),
                alpha=0.35 + 0.64 * sensor_on,
                two_sided=False,
                shininess=105.0,
                supersample=(3, 3),
            )

            # 5. Back Screen Intensity Curtain (`x = +4.65`): 7 Crisp Bright/Dark Stripes -> Smooth Unstriped Band!
            sy_scr = torch.linspace(-4.0, 4.0, 180, device=self.dev)
            sd1 = torch.sqrt(torch.tensor(5.85 ** 2, device=self.dev) + (sy_scr - 1.25) ** 2)
            sd2 = torch.sqrt(torch.tensor(5.85 ** 2, device=self.dev) + (sy_scr + 1.25) ** 2)
            env_g = torch.exp(-(sy_scr / 2.85) ** 2)
            i_coh = env_g * (torch.cos(0.5 * k_wave * (sd1 - sd2)) ** 2)
            i_single = 0.68 * torch.exp(-((sy_scr + 1.25) / 1.65) ** 2)
            intensity = (1.0 - sensor_on) * i_coh + sensor_on * i_single

            zz_s = torch.linspace(0.0, 1.0, 40, device=self.dev)
            yy_g, zz_g = torch.meshgrid(sy_scr, zz_s, indexing="ij")
            h_bar = 0.14 + 2.40 * intensity.unsqueeze(-1)
            P_scr = torch.stack([torch.full_like(yy_g, 4.65), yy_g, zz_g * h_bar], dim=-1)
            col_int = intensity.unsqueeze(-1).expand(180, 40)
            scr_rgb = torch.stack(
                [
                    0.12 + 0.92 * sensor_on * col_int,
                    0.96 * (1.0 - 0.30 * sensor_on) * col_int + 0.14,
                    0.58 * (1.0 - 0.45 * sensor_on) * col_int + 0.14,
                ],
                dim=-1,
            )
            self.canvas.render_surface_mesh(P_scr, scr_rgb, cam, emissive_rgb=scr_rgb * 0.55, alpha=0.93, shininess=70.0)

    def _render_hubble_jwst_cmb_v3(self, t: float, u: float) -> None:
        """Sculpted 3D Hubble & JWST orbiting deep space and scanning the Ancient Cosmic Light (`CMB`) Sky Sphere!"""
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=-2.35, elev=0.22, dist=7.6, target=(0.6, 0.0, 0.15), fov_deg=46.0)),
                (1.00, CameraPose(azim=-1.85, elev=0.26, dist=8.8, target=(1.2, 0.0, 0.20), fov_deg=47.0)),
            ],
            u,
        )
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.012, 0.036, 0.092), nebula_b=(0.045, 0.025, 0.075))

        # 1. Solid Velvety Ancient Cosmic Light (`CMB`) Sky Sphere in deep space at `(+5.6, 0.0, 0.30)`, `R = 2.95`!
        P_cmb, uu_c, vv_c = make_sphere_mesh((5.6, 0.0, 0.30), 2.95, 160, 110, self.dev)
        cmb_fine = (
            0.55 * torch.sin(9.0 * uu_c + 0.25 * t) * torch.sin(7.0 * vv_c)
            + 0.45 * torch.cos(15.0 * uu_c - 0.20 * t) * torch.sin(12.0 * vv_c)
            + 0.30 * torch.sin(22.0 * uu_c) * torch.cos(18.0 * vv_c)
        )
        t_norm = torch.clamp(0.5 + 0.42 * cmb_fine, 0.0, 1.0)
        cmb_rgb = torch.stack(
            [0.10 + 0.98 * (t_norm ** 1.45), 0.36 + 0.56 * torch.sin(t_norm * math.pi), 1.06 - 0.86 * t_norm],
            dim=-1,
        )
        self.canvas.render_surface_mesh(
            P_cmb, cmb_rgb, cam, emissive_rgb=cmb_rgb * 0.28, alpha=0.97, two_sided=False,
            shininess=38.0, fresnel_rgb=(0.55, 0.90, 1.0), supersample=(3, 3)
        )

        # 2. Sculpted 18-Hexagon Golden JWST in left-foreground `(-1.6, -1.55, 0.35)` aimed outward toward `(+5.6, 0, 0.3)`!
        lx = self.jwst_local_P[..., 0] * 0.78
        ly = self.jwst_local_P[..., 1] * 0.78
        lz = self.jwst_local_P[..., 2] * 0.78
        P_jwst = torch.stack([-1.6 - lz, -1.55 + lx, 0.35 + ly], dim=-1)
        N_jwst = torch.tensor([0.96, 0.25, -0.06], device=self.dev).view(1, 1, 3).expand_as(P_jwst)
        N_jwst = F.normalize(N_jwst, dim=-1)
        self.canvas.render_surface_mesh(
            P_jwst, (0.98, 0.75, 0.16), cam, normals=N_jwst, emissive_rgb=(0.26, 0.16, 0.02),
            alpha=0.99, shininess=92.0, specular_strength=1.5, fresnel_rgb=(1.0, 0.88, 0.42), supersample=(2, 2)
        )

        # 3. Sculpted Silver-and-Sapphire Hubble (`HST`) in right-foreground `(-1.5, +1.55, -0.20)` aimed along `+X`!
        hb_P = torch.stack([-1.5 + self.hst_body_P[..., 2], 1.55 + self.hst_body_P[..., 0], -0.20 + self.hst_body_P[..., 1]], dim=-1)
        hb_N = torch.stack([self.hst_body_N[..., 2], self.hst_body_N[..., 0], self.hst_body_N[..., 1]], dim=-1)
        self.canvas.render_surface_mesh(
            hb_P, (0.86, 0.90, 0.96), cam, normals=hb_N, alpha=0.99, two_sided=False, shininess=105.0, specular_strength=1.45, supersample=(2, 2)
        )
        hw_P = torch.stack([-1.5 + self.hst_wings_P[..., 1], 1.55 + self.hst_wings_P[..., 0], -0.20 + self.hst_wings_P[..., 2]], dim=-1)
        self.canvas.render_surface_mesh(
            hw_P, (0.14, 0.50, 0.98), cam, emissive_rgb=(0.06, 0.22, 0.52), alpha=0.97, shininess=88.0, supersample=(2, 2)
        )
        hbm_P = torch.stack([-1.5 + self.hst_boom_P[..., 2], 1.55 + self.hst_boom_P[..., 0], -0.20 + self.hst_boom_P[..., 1]], dim=-1)
        self.canvas.render_surface_mesh(hbm_P, (0.85, 0.72, 0.30), cam, two_sided=False)

        # 4. Translucent Observation Sightline Beams scanning across black space from JWST & Hubble onto the CMB Dome!
        for orig, col_b in (((-1.4, -1.55, 0.35), (1.0, 0.82, 0.32)), ((-0.65, 1.55, -0.20), (0.32, 0.88, 1.0))):
            s_c = torch.linspace(0.0, 1.0, 42, device=self.dev)
            tgt = (2.75, orig[1] * 0.28, 0.30 + 0.32 * math.sin(t * 0.9 + orig[1]))
            p0 = torch.tensor(orig, device=self.dev)
            p1 = torch.tensor(tgt, device=self.dev)
            curve = p0.unsqueeze(0) + s_c.unsqueeze(-1) * (p1 - p0).unsqueeze(0)
            rad_c = 0.04 + 0.58 * s_c
            Pc, Nc = make_tube_along_curve(curve, rad_c, n_around=20)
            self.canvas.render_surface_mesh(
                Pc, col_b, cam, normals=Nc, emissive_rgb=(col_b[0]*0.38, col_b[1]*0.38, col_b[2]*0.38),
                alpha=0.22, two_sided=True, write_depth=False
            )

    # -----------------------------------------------------------------------
    # SCENE 07 V3:
    #   Part 7A (`chunk_25..26`): Solar Campfire Steep Local Funnel (50,000,000x Stronger — NO weird bubble!)
    #   Part 7B (`chunk_27` Sagan Sweep): WHY Fast Outer Galaxy Stars Are NOT Flung Out of Orbit!
    # -----------------------------------------------------------------------
    def _render_scene07_v3(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch27 = _find_chunk(scene, "chunk_27")
        t27_s = (ch27["local_start"] - 1.4) if ch27 else dur * 0.52

        gal_blend = smootherstep01((t - t27_s) / 4.2)

        if gal_blend < 0.99:
            # --- PART 7A: SOLAR CAMPFIRE — STEEP LOCAL GRAVITY FUNNEL AROUND THE SUN ---
            u_sol = min(1.0, t / max(1.0, t27_s))
            pose_sol = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-0.45, elev=0.32, dist=6.4, target=(0.0, 0.0, -0.55), fov_deg=46.0)),
                    (0.60, CameraPose(azim=0.45, elev=0.20, dist=4.6, target=(0.0, 0.0, -0.75), roll_deg=3.0, fov_deg=45.0)),
                    (1.00, CameraPose(azim=1.05, elev=0.38, dist=9.8, target=(0.0, 0.0, -0.45), roll_deg=0.0, fov_deg=47.0)),
                ],
                u_sol,
            )

        if gal_blend <= 0.50:
            cam = CameraMatrix(pose_sol, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.016, 0.044, 0.102), nebula_b=(0.055, 0.030, 0.065))

            # Steep golden solar gravity funnel (`-2.65 / sqrt(r^2 + 0.55)`) — visually 50,000,000x steeper than outer rim!
            gx = self.grid_x * 7.8
            gy = self.grid_y * 7.8
            rr = torch.sqrt(gx * gx + gy * gy + 0.45)
            gz = -2.65 / rr
            P_fun = torch.stack([gx, gy, gz], dim=-1)
            warmth = torch.exp(-(rr - 0.65) * 0.62)  # Campfire local heat glow close to the Sun!
            fun_rgb = torch.stack(
                [0.06 + 0.96 * warmth, 0.24 + 0.54 * warmth, 0.52 - 0.25 * warmth], dim=-1
            )
            self.canvas.render_surface_mesh(
                P_fun, fun_rgb, cam,
                emissive_rgb=torch.stack([0.52 * warmth, 0.24 * warmth, 0.04 * warmth], dim=-1),
                alpha=0.92, shininess=76.0, wire_stride=7, wire_rgb=(0.45, 0.88, 1.0), wire_boost=0.40
            )

            # Blazing Golden Campfire Sun + Inner Planets (`Mercury, Venus, Earth, Mars`) tightly bound inside steep walls!
            Psun, _, _ = make_sphere_mesh((0.0, 0.0, -1.75), 0.72, 80, 56, self.dev)
            self.canvas.render_surface_mesh(Psun, (1.0, 0.80, 0.22), cam, emissive_rgb=(1.65, 1.02, 0.25), two_sided=False)

            for idx_p, (rp, spd, pcol, psz) in enumerate((
                (1.35, 3.2, (0.85, 0.78, 0.72), 0.09),
                (1.95, 2.3, (0.98, 0.82, 0.48), 0.12),
                (2.65, 1.7, (0.20, 0.68, 1.00), 0.14),
                (3.45, 1.2, (0.95, 0.42, 0.25), 0.11),
            )):
                pa = idx_p * 1.5 + spd * t
                px, py = rp * math.cos(pa), rp * math.sin(pa)
                pz = -2.65 / math.sqrt(rp * rp + 0.45) + psz + 0.04
                Pp, _, _ = make_sphere_mesh((px, py, pz), psz, 36, 26, self.dev)
                self.canvas.render_surface_mesh(Pp, pcol, cam, emissive_rgb=(pcol[0]*0.3, pcol[1]*0.3, pcol[2]*0.3), two_sided=False)
                th_o = torch.linspace(0.0, 2.0 * math.pi, 120, device=self.dev)
                Po, No = make_tube_along_curve(
                    torch.stack([rp * torch.cos(th_o), rp * torch.sin(th_o), torch.full_like(th_o, pz - psz * 0.6)], dim=-1),
                    0.018, n_around=10, closed=True
                )
                self.canvas.render_surface_mesh(Po, pcol, cam, normals=No, emissive_rgb=(pcol[0]*0.35, pcol[1]*0.35, pcol[2]*0.35), two_sided=False)
            return

        # --- PART 7B (`10:19+` SAGAN SWEEP): WHY FAST OUTER GALAXY STARS ARE NOT FLUNG OUT OF ORBIT! ---
        u_gal = max(0.0, min(1.0, (t - t27_s) / max(1.0, dur - t27_s)))
        r_hero = 4.85
        hero_ang0 = -0.34 * t  # Counter-clockwise/clockwise orbit angle of Hero Star #0

        # Camera sweeps wide to reveal the entire Banked Emerald Cosmic Bowl, dives down beside a fast Hero Outer Star
        # so you watch the banked cloth curve it inward instead of flying off along the red tangent, then rises majestically!
        hx0 = r_hero * math.cos(hero_ang0)
        hy0 = r_hero * math.sin(hero_ang0)
        pose_gal = interpolate_camera(
            [
                (0.00, CameraPose(azim=1.05, elev=0.40, dist=13.6, target=(0.0, 0.0, -0.2), fov_deg=47.0)),
                (0.38, CameraPose(azim=hero_ang0 - 0.95, elev=0.22, dist=6.2, target=(hx0 * 0.68, hy0 * 0.68, 0.05), roll_deg=4.0, fov_deg=45.0)),
                (0.68, CameraPose(azim=hero_ang0 - 0.55, elev=0.28, dist=8.8, target=(hx0 * 0.35, hy0 * 0.35, 0.0), roll_deg=0.0, fov_deg=46.0)),
                (1.00, CameraPose(azim=2.35, elev=0.34, dist=13.8, target=(0.0, 0.0, -0.1), fov_deg=47.0)),
            ],
            u_gal,
        )
        cam = CameraMatrix(pose_gal, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.012, 0.050, 0.108), nebula_b=(0.022, 0.072, 0.072))

        # 1. Taut Upward-Banked Emerald Cosmic Tablecloth (`z = -1.35 + 0.88 * ln(r + 0.8)`) Holding the Galaxy Suburbs!
        rr_b = 0.25 + 8.35 * self.pol_r
        tt_b = self.pol_th
        bx = rr_b * torch.cos(tt_b)
        by = rr_b * torch.sin(tt_b)
        # Notice the clear upward-sloping velodrome/trampoline bank in the outer suburbs (`r = 3.5 .. 8.5`)!
        bz = -1.45 + 0.92 * torch.log(rr_b * 0.65 + 0.75)
        P_bowl = torch.stack([bx, by, bz], dim=-1)

        rim_bank = torch.sigmoid((rr_b - 3.2) * 1.1)
        bowl_rgb = torch.stack(
            [0.04 + 0.06 * rim_bank, 0.26 + 0.38 * rim_bank, 0.32 + 0.28 * rim_bank], dim=-1
        )
        self.canvas.render_surface_mesh(
            P_bowl, bowl_rgb, cam,
            emissive_rgb=torch.stack([0.02 * rim_bank, 0.16 * rim_bank, 0.13 * rim_bank], dim=-1),
            alpha=0.80, shininess=68.0, fresnel_rgb=(0.25, 0.98, 0.78),
            wire_stride=8, wire_rgb=(0.22, 0.96, 0.78), wire_boost=0.42, write_depth=False
        )

        # 2. 46,000-Star 3D Spiral Galaxy nestled inside the Taut Cosmic Bowl!
        g_pts = self._spinning_galaxy_pts(t * 0.55, omega_flat=0.34)
        self.canvas.render_particles(g_pts, self.gal_rgb * 1.10, self.gal_sz, cam, focus_dist=pose_gal.dist)

        # 3. Closed Bright-Emerald Orbit Track at `R = 4.85` (Supported by Fabric Tension!)
        z_orb = -1.45 + 0.92 * math.log(r_hero * 0.65 + 0.75) + 0.18
        th_c = torch.linspace(0.0, 2.0 * math.pi, 220, device=self.dev)
        Porb, Norb = make_tube_along_curve(
            torch.stack([r_hero * torch.cos(th_c), r_hero * torch.sin(th_c), torch.full_like(th_c, z_orb)], dim=-1),
            0.042, n_around=16, closed=True
        )
        self.canvas.render_surface_mesh(
            Porb, (0.20, 0.98, 0.74), cam, normals=Norb, emissive_rgb=(0.12, 0.65, 0.45), alpha=0.95, two_sided=False
        )

        # 4. 4 Blazing Hero Outer Stars + Comparison of:
        #      - Dashed Crimson Straight Tangent Escape Path ("Without Fabric Tension: Flung Into Space!")
        #      - Emerald Inward Fabric-Tension Banking Arrows ("Taut Cloth Curves Fast Star Inward!")
        for k in range(4):
            ang_k = hero_ang0 + k * (0.5 * math.pi)
            sx = r_hero * math.cos(ang_k)
            sy = r_hero * math.sin(ang_k)
            # Tangent unit vector in direction of orbital motion (`d(ang)/dt < 0` -> clockwise tangent `(sin, -cos)`)
            tx_u = math.sin(ang_k)
            ty_u = -math.cos(ang_k)

            # Blazing White-Gold Hero Outer Star
            Ph, _, _ = make_sphere_mesh((sx, sy, z_orb + 0.04), 0.19, 36, 26, self.dev)
            self.canvas.render_surface_mesh(Ph, (1.0, 0.94, 0.72), cam, emissive_rgb=(1.35, 1.15, 0.75), two_sided=False)

            # Dashed Crimson Tangent Escape Segments showing where the fast star WOULD fling off without fabric tension!
            for seg_i in range(4):
                d0 = 0.35 + seg_i * 0.82
                d1_s = d0 + 0.48
                s_seg = torch.linspace(d0, d1_s, 14, device=self.dev)
                c_esc = torch.stack(
                    [sx + tx_u * s_seg, sy + ty_u * s_seg, torch.full_like(s_seg, z_orb + 0.02)], dim=-1
                )
                Pe_s, Ne_s = make_tube_along_curve(c_esc, 0.034, n_around=10)
                self.canvas.render_surface_mesh(
                    Pe_s, (1.0, 0.28, 0.34), cam, normals=Ne_s, emissive_rgb=(0.65, 0.12, 0.16), alpha=0.88, two_sided=False
                )
            # Arrowhead at tip of red escape tangent + inward emerald tension arrow from outer banked cloth!
            self._draw_3d_arrow(
                (sx + tx_u * 3.55, sy + ty_u * 3.55, z_orb + 0.02),
                (sx + tx_u * 4.25, sy + ty_u * 4.25, z_orb + 0.02),
                (1.0, 0.28, 0.34), cam, shaft_r=0.042
            )
            # Inward radial emerald tension arrow pushing from the banked cloth (`R=6.3 -> R=5.15`)!
            rx_u, ry_u = math.cos(ang_k), math.sin(ang_k)
            z_outer_bank = -1.45 + 0.92 * math.log(6.35 * 0.65 + 0.75) + 0.18
            self._draw_3d_arrow(
                (6.35 * rx_u, 6.35 * ry_u, z_outer_bank),
                (5.15 * rx_u, 5.15 * ry_u, z_orb + 0.04),
                (0.22, 0.98, 0.74), cam, shaft_r=0.048
            )

    # -----------------------------------------------------------------------
    # SCENE 08 V3:
    #   Act 8A (`chunk_28` + `4.2s` silent showcase): Young Galaxy Forming & Tucking Excess Fabric Into a Pleat!
    #   Act 8B (`chunk_29`): Toned-Down High-Speed Bullet Cluster Collision!
    #   Act 8C (`chunk_30`): Gentle Slow-Drift Dwarf Galaxy Pleat Bounce!
    # -----------------------------------------------------------------------
    def _render_scene08_v3(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch29 = _find_chunk(scene, "chunk_29")
        ch30 = _find_chunk(scene, "chunk_30")
        t29_s = ch29["local_start"] if ch29 else 30.0
        t30_s = ch30["local_start"] if ch30 else 67.0

        if t < t29_s - 0.35:
            # --- ACT 8A (`0 .. ~29.8s`, including the 4.2s silent visual pause!):
            #     YOUNG GALAXY FORMING, GATHERING & TUCKING EXCESS FABRIC INTO A CRISP PLEAT! ---
            u = max(0.0, min(1.0, t / max(1.0, t29_s - 0.35)))
            # Stars condense & tuck the fabric over `u = 0.08 .. 0.72`, then `u = 0.72 .. 1.00` (~8.5s including the 4.2s
            # silent pause!) showcases the finished gleaming 3D folded fabric pleat in a close-up orbit!
            tuck = smootherstep01((u - 0.06) / 0.64)

            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-0.95, elev=0.46, dist=12.4, target=(0.0, 0.0, -0.2), fov_deg=47.0)),
                    (0.55, CameraPose(azim=-0.15, elev=0.26, dist=7.6, target=(0.0, 0.0, 0.0), roll_deg=-3.0, fov_deg=45.0)),
                    (0.80, CameraPose(azim=0.55, elev=0.18, dist=5.1, target=(0.0, 0.0, 0.15), roll_deg=2.0, fov_deg=44.0)),
                    (1.00, CameraPose(azim=1.18, elev=0.28, dist=6.8, target=(0.0, 0.0, 0.05), roll_deg=0.0, fov_deg=45.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.016, 0.044, 0.112), nebula_b=(0.065, 0.032, 0.095))

            # 1. 340x340 Cosmic Silk Sheet Physically Pulled Radially Inward & Tucked Into a Crisp Multi-Ridge Pleat!
            gx = self.grid_x * 7.8
            gy = self.grid_y * 7.8
            rr = torch.sqrt(gx * gx + gy * gy + 0.08)
            ux = gx / rr
            uy = gy / rr

            # Smooth monotonic radial pull outside the galaxy core (`r > 1.8`) so zero central chimney forms,
            # visibly bunching threads inward right into the crisp circumferential pleat collar around `r = 2.35`!
            outer_mask = torch.sigmoid((rr - 1.95) * 2.4)
            inward_gather = 0.62 * tuck * outer_mask * torch.exp(-((rr - 3.35) / 2.15) ** 2)
            r_tucked = rr - inward_gather

            px = ux * r_tucked
            py = uy * r_tucked

            # Vertical sculpture: gentle central cradle (`-0.52`) surrounded by a gleaming, crisp double-ridge fabric pleat!
            main_pleat = 0.98 * tuck * torch.exp(-((rr - 2.35) / 0.38) ** 2)
            second_pleat = 0.44 * tuck * torch.exp(-((rr - 3.35) / 0.34) ** 2)
            pleat_trough = -0.26 * tuck * torch.exp(-((rr - 2.88) / 0.24) ** 2)
            core_dip = -0.52 * tuck * torch.exp(-(rr / 1.55) ** 2)
            pz = -0.45 + core_dip + main_pleat + pleat_trough + second_pleat
            P_pleat = torch.stack([px, py, pz], dim=-1)

            fold_glow = torch.clamp((main_pleat + second_pleat) / 0.98, 0.0, 1.2)
            cloth_rgb = torch.stack(
                [0.06 + 0.34 * fold_glow, 0.28 + 0.62 * fold_glow, 0.58 + 0.52 * fold_glow], dim=-1
            )
            self.canvas.render_surface_mesh(
                P_pleat, cloth_rgb, cam,
                emissive_rgb=torch.stack([0.08 * fold_glow, 0.36 * fold_glow, 0.58 * fold_glow], dim=-1),
                alpha=0.89, shininess=82.0, specular_strength=1.15, fresnel_rgb=(0.45, 0.95, 1.0),
                wire_stride=6, wire_rgb=(0.42, 0.92, 1.0), wire_boost=0.46
            )

            # 2. 24,000 Young Protogalaxy Stars Swirling & Condensing Into the Tucked Pleat Cradle!
            cur_r = (1.0 - tuck) * self.pg_r_init + tuck * self.pg_r_final
            cur_z = (1.0 - tuck) * self.pg_z_init + tuck * self.pg_z_final - 0.22 - 0.32 * tuck
            spin_a = self.pg_th0 - (0.35 + 0.55 * tuck) * t / torch.clamp(0.45 + 0.35 * cur_r, min=0.45)
            s_pts = torch.stack([cur_r * torch.cos(spin_a), cur_r * torch.sin(spin_a), cur_z], dim=-1)
            self.canvas.render_particles(s_pts, self.pg_rgb * (0.65 + 0.55 * tuck), self.pg_sz, cam, focus_dist=pose.dist)

        elif t < t30_s - 0.25:
            # --- ACT 8B (`chunk_29`): HIGH-SPEED BULLET CLUSTER COLLISION (PLEATS GLIDE THROUGH, GAS STALLS) ---
            u = max(0.0, min(1.0, (t - (t29_s - 0.35)) / max(1.0, (t30_s - 0.25) - (t29_s - 0.35))))
            # Map onto parent `_render_scene08` Part A (`prog_fake in [0.0, 0.67]`)
            super()._render_scene08(t, dur, u * 0.675)
        else:
            # --- ACT 8C (`chunk_30`): GENTLE SLOW-DRIFT DWARF PLEAT BOUNCE ---
            u = max(0.0, min(1.0, (t - (t30_s - 0.25)) / max(1.0, dur - (t30_s - 0.25))))
            super()._render_scene08(t, dur, 0.682 + u * 0.315)

    # -----------------------------------------------------------------------
    # SCENE 09 V3:
    #   Act 9A (`chunk_31`): 3D Braided Matter Threads -> Unified Hourglass Tapestry
    #   Act 9B (`chunk_32` + `9.6s` Wordless Sagan Musical Interlude!):
    #          Continuous Multi-Galaxy Cosmic Zoom-Out (1 Galaxy -> 175 Galaxies Across the Universe!)
    #   Act 9C (`chunk_33` Caveat): Cislunar Moon-Orbit Experiment & 6 Companion Science Chapters!
    # -----------------------------------------------------------------------
    def _render_scene09_v3(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch31 = _find_chunk(scene, "chunk_31")
        ch32 = _find_chunk(scene, "chunk_32")
        ch33 = _find_chunk(scene, "chunk_33")

        t32_s = ch32["local_start"] if ch32 else 19.0
        t32_e = ch32["local_end"] if ch32 else 42.5
        t33_s = ch33["local_start"] if ch33 else 52.0

        # Transition from Hourglass/Braids into the Continuous Multi-Galaxy Cosmic Pullback halfway through `chunk_32`
        # ("...holding galaxies together with its own quiet tension... look up at the night sky in wonder")
        # and run that unbroken cosmic pullback ALL THE WAY through the 9.6-second wordless musical pause (`t33_s - 0.4s`)!
        t_zoom_start = t32_s + 9.5

        if t < t32_s - 0.5:
            # Act 9A-1 (`chunk_31`): Unified Cosmic Hourglass Tapestry
            u = max(0.0, min(1.0, t / max(1.0, t32_s - 0.5)))
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=0.65, elev=0.22, dist=7.6, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                    (1.00, CameraPose(azim=1.65, elev=0.30, dist=11.8, target=(0.0, 0.0, 0.0), fov_deg=48.0)),
                ],
                u,
            )
            self._render_hourglass_core(t, flip_amt=1.0, cam_pose=pose)

        elif t < t_zoom_start:
            # Act 9A-2 (First 9.5s of `chunk_32`): Gleaming 3-Strand Matter Braids!
            u = (t - (t32_s - 0.5)) / max(1.0, t_zoom_start - (t32_s - 0.5))
            super()._render_scene09(t, dur, u * 0.33)

        elif t < t33_s - 0.35:
            # --- ACT 9B (`~23.5 seconds` unbroken shot spanning "...holding galaxies together... in wonder" +
            #     the ENTIRE 9.6-second soaring musical interlude!):
            #     CONTINUOUS 3D MULTI-GALAXY COSMIC ZOOM-OUT (1 HOME GALAXY -> 175 GALAXIES!) ---
            u = max(0.0, min(1.0, (t - t_zoom_start) / max(1.0, (t33_s - 0.35) - t_zoom_start)))
            u_smooth = smootherstep01(u)
            # Exponential cosmic distance pullback: starts intimate at `dist = 5.2` inside our home spiral galaxy,
            # pulls steadily back to `dist = 76.0` revealing 175 3D galaxies glittering across the deep cosmos!
            dist = 5.2 * ((76.0 / 5.2) ** (u_smooth ** 1.08))
            pose = CameraPose(
                azim=0.45 + 1.15 * u_smooth,
                elev=0.26 + 0.14 * math.sin(u_smooth * math.pi),
                dist=dist,
                target=(0.0, 0.0, 0.0),
                roll_deg=-4.0 * (1.0 - u_smooth),
                fov_deg=48.0 + 6.0 * u_smooth,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t * 0.4, nebula_a=(0.012, 0.032, 0.082), nebula_b=(0.048, 0.020, 0.075), star_gain=0.92)

            # 1. Central 46,000-Star Home Spiral Galaxy spinning serenely at the origin!
            home_pts = self._spinning_galaxy_pts(t * 0.35, omega_flat=0.22)
            self.canvas.render_particles(home_pts, self.gal_rgb * 1.12, self.gal_sz * 0.90, cam, focus_dist=None)

            # 2. 175 Distinct 3D Deep-Field Spiral & Golden Elliptical Galaxies (`245,000` stars) spanning the cosmos!
            df_fade = smoothstep01((u - 0.04) / 0.20)
            if df_fade > 0.01:
                # Slow majestic cosmic rotation of the deep field with infinite deep-space telescope focus (`focus_dist=None`)
                ang_df = 0.015 * t
                ca, sa = math.cos(ang_df), math.sin(ang_df)
                rx = ca * self.df_pts[:, 0] - sa * self.df_pts[:, 1]
                ry = sa * self.df_pts[:, 0] + ca * self.df_pts[:, 1]
                r_pts = torch.stack([rx, ry, self.df_pts[:, 2]], dim=-1)
                self.canvas.render_particles(r_pts, self.df_rgb * (1.22 * df_fade), self.df_sz, cam, focus_dist=None)

        else:
            # --- ACT 9C (`chunk_33` Closing Caveat): CISLUNAR MOON-ORBIT PROBE & 6 SCIENCE CHAPTERS ---
            u = max(0.0, min(1.0, (t - (t33_s - 0.35)) / max(1.0, dur - (t33_s - 0.35))))
            super()._render_scene09(t, dur, 0.665 + u * 0.33)
