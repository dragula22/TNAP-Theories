"""
Episode 2 3D Mathematical Scene Director (`ep2_gpu_scenes.py`):
  'Episode 2 — The Upside-Down Big Bang & Where All the Antimatter Went'

Runs cleanly on BOTH CPU (`CUDA_VISIBLE_DEVICES="-1"`, 0% GPU impact while Jimani runs!)
and CUDA (`RTX 5080`), strictly enforcing Locked Option A+ ('Luminous Sapphire Slate',
39% vibrant mid-tone: sRGB `(35, 52, 78) -> (68, 97, 138)`).

3D Physics Scenes:
  • `scene00`: WeaveForge Two-Knot Collision/Orbit Tank + Gaia DR4 Wide-Binary Halo + Entering Hourglass
  • `scene01`: Penrose `1-in-10^(10^123)` Phase-Space Needle + 180-Degree Upside-Down Hourglass Drain
  • `scene02`: Single-Boundary Rim Scattering vs. Two-Ring Brushed-Brass Catenoid Soap Film + Wave Squeeze
  • `scene03`: Rotating 3D Planck CMB Sky Sphere (`l=2` Quadrupole vs Acoustic Ripples) + Quantized Steps
  • `scene04`: Entangled B-Meson 14-Sigma Asymmetry + CPT Symmetry Rings + Two-Wing Sakharov Coin-Sorter
  • `scene05`: Cosmic Drumhead Gravity Bowls + Uncharged `SO(3)` Spacetime Pleats ('Bullet Cluster in Reverse')
  • `scene06`: WeaveForge Arena 4 Spin + Two-Ended Double-Slit Standing-Wave Interference Teaser
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from gpu_renderer_core import (
    CameraMatrix,
    CameraPose,
    GPUCanvas1080p,
    make_sphere_mesh as _core_sphere_mesh,
    make_torus_mesh as _core_torus_mesh,
    make_tube_along_curve,
    smootherstep01,
    smoothstep01,
)


def _find_chunk(scene: Optional[dict], cid: str) -> Optional[dict]:
    if not scene:
        return None
    for ch in scene.get("chunks") or []:
        if ch["chunk_id"] == cid:
            return ch
    return None


def _srgb_tensor_to_hdr_pre_aces(srgb_01: torch.Tensor) -> torch.Tensor:
    m = torch.clamp(srgb_01, 0.001, 0.92) ** 2.2
    A = 2.51 - 2.43 * m
    B = 0.03 - 0.59 * m
    C = -0.14 * m
    disc = torch.clamp(B * B - 4.0 * A * C, min=0.0)
    h = (-B + torch.sqrt(disc)) / (2.0 * A)
    return torch.clamp(h, min=0.0)


def make_trefoil_tube(
    center: Tuple[float, float, float],
    scale: float,
    tube_r: float,
    phase: float,
    chirality: float,
    device: torch.device,
    n_seg: int = 150,
    n_sides: int = 16,
) -> Tuple[torch.Tensor, torch.Tensor]:
    t = np.linspace(0.0, 2.0 * math.pi, n_seg, endpoint=True, dtype=np.float32)
    x = scale * (np.sin(t + phase) + 2.0 * np.sin(2.0 * t + phase)) * 0.34
    y = scale * (np.cos(t + phase) - 2.0 * np.cos(2.0 * t + phase)) * 0.34 * chirality
    z = scale * (-np.sin(3.0 * t + phase)) * 0.38
    pts = torch.tensor(np.stack([x + center[0], y + center[1], z + center[2]], axis=-1), device=device, dtype=torch.float32)
    return make_tube_along_curve(pts, tube_r, n_around=n_sides, closed=True)


class Episode2SceneDirector:
    """Option A+ ('Luminous Sapphire Slate') 3D Mathematical Scene Director for Episode 2."""

    EXPOSURE = 1.00
    BLOOM = 0.35

    def __init__(self, device: Optional[torch.device] = None):
        self.canvas = GPUCanvas1080p(device=device)
        self.dev = self.canvas.device
        self.w = self.canvas.w
        self.h = self.canvas.h

        self.qw = max(64, self.w // 4)
        self.qh = max(36, self.h // 4)
        gy_q = torch.linspace(1.0, -1.0, self.qh, device=self.dev)
        gx_q = torch.linspace(-self.w / self.h, self.w / self.h, self.qw, device=self.dev)
        self.q_yy, self.q_xx = torch.meshgrid(gy_q, gx_q, indexing="ij")

        self._init_option_a_plus_canvases()
        self._init_loom_and_grids()
        self._init_cmb_sphere_and_galaxies()
        self._init_coin_sorter_particles()

    def _init_option_a_plus_canvases(self) -> None:
        rx = self.q_xx / (self.w / self.h)
        ry = self.q_yy + 0.04
        rad = torch.clamp(torch.sqrt(rx * rx * 0.88 + ry * ry * 1.04), 0.0, 1.25)
        w_center = torch.exp(-1.35 * (rad ** 1.65))

        out_studio = torch.tensor([35.0, 52.0, 78.0], device=self.dev).view(3, 1, 1) / 255.0
        inn_studio = torch.tensor([68.0, 97.0, 138.0], device=self.dev).view(3, 1, 1) / 255.0
        srgb_studio_q = out_studio + (inn_studio - out_studio) * w_center.unsqueeze(0)

        out_cosmos = torch.tensor([22.0, 34.0, 55.0], device=self.dev).view(3, 1, 1) / 255.0
        inn_cosmos = torch.tensor([48.0, 72.0, 108.0], device=self.dev).view(3, 1, 1) / 255.0
        srgb_cosmos_q = out_cosmos + (inn_cosmos - out_cosmos) * w_center.unsqueeze(0)

        hdr_studio_full = F.interpolate(
            _srgb_tensor_to_hdr_pre_aces(srgb_studio_q).unsqueeze(0),
            size=(self.h, self.w),
            mode="bilinear",
            align_corners=False,
        ).squeeze(0)
        hdr_cosmos_full = F.interpolate(
            _srgb_tensor_to_hdr_pre_aces(srgb_cosmos_q).unsqueeze(0),
            size=(self.h, self.w),
            mode="bilinear",
            align_corners=False,
        ).squeeze(0)

        inv_vig = 1.0 / torch.clamp(self.canvas.vignette * self.EXPOSURE, min=0.45)
        self.base_hdr_studio = hdr_studio_full * inv_vig
        self.base_hdr_cosmos = hdr_cosmos_full * inv_vig

        step_px = max(48, int(round(120 * self.canvas.res_scale)))
        yi = torch.arange(self.h, device=self.dev)
        xi = torch.arange(self.w, device=self.dev)
        gy_m = (yi % step_px == 0).float().view(1, self.h, 1)
        gx_m = (xi % step_px == 0).float().view(1, 1, self.w)
        g_mask = torch.clamp(gy_m + gx_m, 0.0, 1.0)
        self.studio_grid_hdr = g_mask * torch.tensor([0.018, 0.030, 0.045], device=self.dev).view(3, 1, 1)

    def _init_loom_and_grids(self) -> None:
        pts_list = []
        s_vals = np.linspace(-8.5, 8.5, 180, dtype=np.float32)
        for k in np.linspace(-4.8, 4.8, 13, dtype=np.float32):
            pts_list.append(np.stack([s_vals, np.full_like(s_vals, k), np.full_like(s_vals, -2.1)], axis=-1))
            pts_list.append(np.stack([np.full_like(s_vals, k * 1.35), s_vals * 0.65, np.full_like(s_vals, -2.1)], axis=-1))
        loom_np = np.concatenate(pts_list, axis=0)
        self.loom_pts = torch.tensor(loom_np, device=self.dev, dtype=torch.float32)
        c_base = torch.tensor([0.22, 0.58, 0.88], device=self.dev, dtype=torch.float32)
        self.loom_rgb = c_base.unsqueeze(0).expand(len(loom_np), 3).contiguous()

        # Parametric grids for Hourglass / Catenoid `(110 x 160)` and Sheet / Pleats `(140 x 140)`
        uz = torch.linspace(-1.0, 1.0, 110, device=self.dev)
        uth = torch.linspace(0.0, 2.0 * math.pi, 160, device=self.dev)
        self.hg_z, self.hg_th = torch.meshgrid(uz, uth, indexing="ij")

        ux = torch.linspace(-1.0, 1.0, 140, device=self.dev)
        self.sh_x, self.sh_y = torch.meshgrid(ux, ux, indexing="ij")

        # 3D Wireframe Cube edges for WeaveForge Arena box
        box_lines = []
        b = 2.6
        corners = [(-b, -b, -b), (b, -b, -b), (b, b, -b), (-b, b, -b), (-b, -b, b), (b, -b, b), (b, b, b), (-b, b, b)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
        u_line = np.linspace(0.0, 1.0, 60, dtype=np.float32)[:, None]
        for i0, i1 in edges:
            p0 = np.array(corners[i0], dtype=np.float32)
            p1 = np.array(corners[i1], dtype=np.float32)
            box_lines.append(p0[None, :] * (1.0 - u_line) + p1[None, :] * u_line)
        box_np = np.concatenate(box_lines, axis=0)
        self.box_pts = torch.tensor(box_np, device=self.dev, dtype=torch.float32)
        self.box_rgb = torch.tensor([0.38, 0.78, 1.05], device=self.dev).unsqueeze(0).expand(len(box_np), 3).contiguous()

    def _init_cmb_sphere_and_galaxies(self) -> None:
        P_s, _, _ = _core_sphere_mesh((0.0, 0.0, 0.0), 1.95, 180, 120, self.dev)
        self.cmb_unit = F.normalize(P_s, dim=-1, eps=1e-7)
        nx, ny, nz = self.cmb_unit[..., 0], self.cmb_unit[..., 1], self.cmb_unit[..., 2]

        # Quadrupole `l=2` spherical harmonic mode vs fine `l=12..28` acoustic speckles
        self.cmb_quad = 1.5 * (nz * nz - 0.3333) + 0.85 * (nx * nx - ny * ny)
        fine1 = torch.sin(11.0 * nx + 8.5 * ny) * torch.cos(10.2 * nz - 7.4 * nx)
        fine2 = 0.65 * torch.sin(19.5 * ny - 15.0 * nz) * torch.cos(17.2 * nx + 13.0 * ny)
        self.cmb_fine = fine1 + fine2

        # Deep-field galaxy cloud `(110 galaxies x 900 stars = 99,000 stars)`
        rng = np.random.default_rng(20262)
        n_gal, spg = 110, 900
        idx = np.arange(n_gal, dtype=np.float32)
        phi = math.pi * (3.0 - math.sqrt(5.0)) * idx
        cos_th = 1.0 - 2.0 * ((idx + 0.5) / n_gal)
        sin_th = np.sqrt(np.maximum(0.0, 1.0 - cos_th * cos_th))
        radii = 14.0 + 70.0 * ((idx / max(1, n_gal - 1)) ** 0.78)
        rng.shuffle(radii)
        centers = np.stack([radii * np.cos(phi) * sin_th, radii * np.sin(phi) * sin_th, radii * cos_th * 0.84], axis=-1)

        all_xyz, all_rgb, all_sz = [], [], []
        for g_i in range(n_gal):
            u = rng.random(spg).astype(np.float32)
            g_sc = float(rng.uniform(0.65, 1.20)) * (1.0 + 0.008 * radii[g_i])
            arm_a = rng.integers(0, 2, size=spg).astype(np.float32) * math.pi
            rr = (0.12 + 1.80 * (u ** 0.78)) * g_sc
            ang = arm_a + 2.15 * np.log(u + 0.14) + rng.normal(0.0, 0.24, size=spg).astype(np.float32)
            lx = rr * np.cos(ang)
            ly = rr * np.sin(ang)
            lz = rng.normal(0.0, 0.06 * g_sc, size=spg).astype(np.float32)
            cw = np.exp(-(u / 0.30) ** 2)
            lum = (0.30 + 0.75 * (rng.random(spg).astype(np.float32) ** 1.6)) * (0.48 + 0.52 * np.exp(-0.5 * u))
            rgb = np.stack(
                [
                    (1.22 * cw + 0.34 * (1.0 - cw)) * lum,
                    (0.90 * cw + 0.82 * (1.0 - cw)) * lum,
                    (0.46 * cw + 1.30 * (1.0 - cw)) * lum,
                ],
                axis=-1,
            )
            q_mat, _ = np.linalg.qr(rng.normal(size=(3, 3)).astype(np.float32))
            all_xyz.append(np.stack([lx, ly, lz], axis=-1) @ q_mat.T + centers[g_i])
            all_rgb.append(rgb)
            all_sz.append(np.full(spg, 0.95 if radii[g_i] < 40.0 else 0.80, dtype=np.float32))

        self.df_pts = torch.tensor(np.concatenate(all_xyz, axis=0), device=self.dev, dtype=torch.float32)
        self.df_rgb = torch.tensor(np.concatenate(all_rgb, axis=0), device=self.dev, dtype=torch.float32)
        self.df_sz = torch.tensor(np.concatenate(all_sz, axis=0), device=self.dev, dtype=torch.float32)

    def _init_coin_sorter_particles(self) -> None:
        g = torch.Generator(device="cpu")
        g.manual_seed(202602)
        n = 14000
        self.cs_u = torch.rand(n, generator=g).to(self.dev)
        self.cs_ang = (torch.rand(n, generator=g) * (2.0 * math.pi)).to(self.dev)
        self.cs_rad = (0.18 + 0.82 * torch.sqrt(torch.rand(n, generator=g))).to(self.dev)
        self.cs_sign = torch.where(torch.arange(n, device=self.dev) % 2 == 0, 1.0, -1.0)

    def clear_option_a_plus(
        self,
        cam: CameraMatrix,
        t: float,
        cosmos_mix: float = 0.15,
        show_grid: bool = True,
        show_loom: bool = True,
    ) -> None:
        self.canvas.zbuf.fill_(1e6)
        cm = max(0.0, min(1.0, float(cosmos_mix)))
        self.canvas.hdr.copy_(self.base_hdr_studio * (1.0 - cm) + self.base_hdr_cosmos * cm)
        if show_grid:
            self.canvas.hdr.add_(self.studio_grid_hdr * (1.0 - 0.55 * cm))

        # Subtle parallax starfield & distant galaxies for depth
        twinkle = (0.85 + 0.15 * torch.sin(1.8 * t + self.canvas.star_phase)).unsqueeze(-1)
        self.canvas.render_particles(
            self.canvas.star_xyz,
            self.canvas.star_rgb * (twinkle * (0.30 + 0.55 * cm)),
            self.canvas.star_sizes,
            cam,
            additive=True,
            depth_occlude=False,
        )
        if cm > 0.25:
            self.canvas.render_particles(
                self.df_pts,
                self.df_rgb * (0.45 * cm),
                self.df_sz,
                cam,
                additive=True,
                depth_occlude=False,
            )
        if show_loom:
            self.canvas.render_particles(
                self.loom_pts,
                self.loom_rgb * 0.26,
                1.0,
                cam,
                additive=True,
                depth_occlude=True,
            )

    def _draw_two_wing_hourglass(
        self,
        cam: CameraMatrix,
        t: float,
        waist_r: float = 0.28,
        height_z: float = 2.65,
        ripple_amp: float = 0.08,
        single_wing: bool = False,
        clamp_quadrupole: float = 0.0,
        dual_color_cpt: bool = False,
    ) -> None:
        z_u = (0.5 + 0.5 * self.hg_z) if single_wing else self.hg_z
        z = z_u * height_z
        th = self.hg_th

        # True Catenoid / Hyperbolic Hourglass neck: `r(z) = waist_r * cosh(z / scale)`
        r_base = waist_r * torch.cosh(z / 1.18)

        # Fine acoustic ripples fit cleanly; giant m=2 quadrupole gets squeezed as `clamp_quadrupole -> 1`
        fine_rip = ripple_amp * (torch.abs(z_u) ** 1.15) * torch.sin(9.0 * z - 3.2 * t + 5.0 * th)
        quad_rip = (0.20 * (1.0 - 0.82 * clamp_quadrupole)) * torch.cos(2.0 * th + 1.1 * t) * torch.cos(0.9 * z)
        r = torch.clamp(r_base + fine_rip + quad_rip, min=0.08)

        P = torch.stack([r * torch.cos(th), r * torch.sin(th), z], dim=-1)
        N = self.canvas.compute_grid_normals(P)

        abs_u = torch.abs(z_u)
        waist_glow = torch.exp(-((z / 0.42) ** 2))
        if dual_color_cpt:
            # Upper wing (`z > 0`): warm solar gold/sapphire matter; Lower mirror wing (`z < 0`): electric cyan/rose antimatter
            pos_w = torch.sigmoid(z * 4.5)
            col_top = torch.stack([0.85 - 0.35 * abs_u, 0.72 - 0.18 * abs_u, 0.36 + 0.52 * abs_u], dim=-1)
            col_bot = torch.stack([0.24 + 0.18 * abs_u, 0.74 - 0.12 * abs_u, torch.full_like(abs_u, 0.96)], dim=-1)
            alb = col_top * pos_w.unsqueeze(-1) + col_bot * (1.0 - pos_w.unsqueeze(-1))
        else:
            alb = torch.stack(
                [
                    0.22 + 0.55 * waist_glow + 0.16 * abs_u,
                    0.56 + 0.34 * waist_glow,
                    0.92 - 0.18 * waist_glow,
                ],
                dim=-1,
            )
        emissive = torch.stack([0.42 * waist_glow, 0.38 * waist_glow, 0.22 * waist_glow], dim=-1)
        self.canvas.render_surface_mesh(
            P, alb, cam, normals=N, shininess=56.0, specular_strength=0.85, emissive_rgb=emissive, wire_stride=10, wire_boost=0.20, supersample=(3, 3)
        )

        # Brushed-brass clamping rings at Waist (`z=0`) and Outer Boundary (`z=+height_z` and `-height_z`)
        P_w, N_w = _core_torus_mesh((0.0, 0.0, 0.0), waist_r + 0.03, 0.048, 120, 16, self.dev, axis="z")
        self.canvas.render_surface_mesh(
            P_w, (0.95, 0.78, 0.32), cam, normals=N_w, shininess=72.0, specular_strength=1.1, emissive_rgb=(0.24, 0.18, 0.05), supersample=(2, 2)
        )
        r_outer = float(waist_r * math.cosh(height_z / 1.18))
        P_top, N_top = _core_torus_mesh((0.0, 0.0, height_z), r_outer, 0.055, 140, 16, self.dev, axis="z")
        self.canvas.render_surface_mesh(P_top, (0.82, 0.66, 0.30), cam, normals=N_top, shininess=64.0, specular_strength=0.95, supersample=(2, 2))
        if not single_wing:
            P_bot, N_bot = _core_torus_mesh((0.0, 0.0, -height_z), r_outer, 0.055, 140, 16, self.dev, axis="z")
            self.canvas.render_surface_mesh(P_bot, (0.45, 0.78, 0.96), cam, normals=N_bot, shininess=64.0, specular_strength=0.95, supersample=(2, 2))

    # ------------------------------------------------------------------
    # Scene Dispatchers (`scene00` .. `scene06`)
    # ------------------------------------------------------------------
    def render_scene_frame(self, scene: dict, t: float) -> np.ndarray:
        sid = scene["id"]
        dur = max(1.0, float(scene["duration_sec"]))
        prog = max(0.0, min(1.0, t / dur))

        if sid == "scene00":
            self._render_scene00(scene, t, dur, prog)
        elif sid == "scene01":
            self._render_scene01(scene, t, dur, prog)
        elif sid == "scene02":
            self._render_scene02(scene, t, dur, prog)
        elif sid == "scene03":
            self._render_scene03(scene, t, dur, prog)
        elif sid == "scene04":
            self._render_scene04(scene, t, dur, prog)
        elif sid == "scene05":
            self._render_scene05(scene, t, dur, prog)
        else:
            self._render_scene06(scene, t, dur, prog)

        return self.canvas.finalize_srgb_uint8(exposure=self.EXPOSURE, bloom_strength=self.BLOOM)

    def _render_scene00(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c1 = _find_chunk(scene, "chunk_01")
        c2 = _find_chunk(scene, "chunk_02")
        t_gaia = c1["local_start"] if c1 else 39.0
        t_hg = c2["local_start"] if c2 else 76.0

        if t < t_gaia:
            # Act 0A: WeaveForge 3D Box with Two Orbiting / Scattering Trefoil Knots
            pose = CameraPose(azim=0.45 + 0.35 * (t / max(1.0, t_gaia)), elev=0.28, dist=8.2, fov_deg=44.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.18, show_grid=True, show_loom=True)
            self.canvas.render_particles(self.box_pts, self.box_rgb * 0.65, 1.3, cam, additive=True, depth_occlude=True)

            sep = 1.45 + 0.45 * math.cos(1.35 * t)
            ang = 0.55 * t
            c_a = (sep * math.cos(ang), sep * math.sin(ang), 0.15 * math.sin(1.2 * t))
            c_b = (-c_a[0], -c_a[1], -c_a[2])
            Pa, Na = make_trefoil_tube(c_a, 1.25, 0.11, 1.8 * t, 1.0, self.dev)
            Pb, Nb = make_trefoil_tube(c_b, 1.25, 0.11, -1.8 * t + 1.57, 1.0, self.dev)
            self.canvas.render_surface_mesh(Pa, (0.32, 0.78, 1.0), cam, normals=Na, shininess=72.0, specular_strength=1.1, emissive_rgb=(0.06, 0.18, 0.30), supersample=(2, 2))
            self.canvas.render_surface_mesh(Pb, (0.98, 0.80, 0.32), cam, normals=Nb, shininess=72.0, specular_strength=1.1, emissive_rgb=(0.24, 0.16, 0.04), supersample=(2, 2))

        elif t < t_hg:
            # Act 0B: Gaia DR4 Wide Twin Binary Stars + +4.63% Black Hole Photon Ring
            u = (t - t_gaia) / max(1.0, t_hg - t_gaia)
            pose = CameraPose(azim=0.8 + 0.55 * u, elev=0.32 - 0.08 * u, dist=7.6 - 1.0 * u, fov_deg=45.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.58, show_grid=False, show_loom=False)

            # Wide binary orbit trace + twin golden stars
            Pr, Nr = _core_torus_mesh((0.0, 0.0, 0.0), 2.15, 0.022, 160, 12, self.dev, axis="z")
            self.canvas.render_surface_mesh(Pr, (0.45, 0.80, 1.0), cam, normals=Nr, shininess=48.0, emissive_rgb=(0.10, 0.24, 0.38), supersample=(2, 2))
            orb = 1.15 * t
            for sgn, col in ((1.0, (1.0, 0.86, 0.42)), (-1.0, (0.68, 0.88, 1.0))):
                sx, sy = sgn * 2.15 * math.cos(orb), sgn * 2.15 * math.sin(orb)
                Ps, Ns = _core_sphere_mesh((sx, sy, 0.0), 0.24, 48, 32, self.dev)[0], None
                c_t = torch.tensor((sx, sy, 0.0), device=self.dev).view(1, 1, 3)
                Ns = F.normalize(Ps - c_t, dim=-1, eps=1e-7)
                self.canvas.render_surface_mesh(Ps, col, cam, normals=Ns, shininess=64.0, emissive_rgb=col, supersample=(2, 2))

        else:
            # Act 0C: Flying Toward the Narrow Waist of the Two-Wing Cosmic Hourglass
            u = smootherstep01((t - t_hg) / max(1.0, dur - t_hg))
            pose = CameraPose(azim=0.35 + 1.1 * u, elev=0.22 - 0.10 * u, dist=9.6 - 2.6 * u, fov_deg=45.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.32, show_grid=True, show_loom=True)
            self._draw_two_wing_hourglass(cam, t, waist_r=0.30, height_z=2.65, dual_color_cpt=True)

    def _render_scene01(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c6 = _find_chunk(scene, "chunk_06")
        t_flip = (c6["local_start"] + 3.0) if c6 else dur * 0.52
        flip = smootherstep01((t - t_flip) / 6.5)

        pose = CameraPose(
            azim=0.30 + 1.85 * prog,
            elev=0.24 - 0.16 * flip,
            dist=8.6 - 1.4 * math.sin(math.pi * prog),
            roll_deg=180.0 * flip,
            fov_deg=45.0,
        )
        cam = CameraMatrix(pose, self.dev)
        self.clear_option_a_plus(cam, t, cosmos_mix=0.28, show_grid=True, show_loom=True)
        self._draw_two_wing_hourglass(cam, t, waist_r=0.26, height_z=2.6, ripple_amp=0.11, single_wing=(flip < 0.05))

        # Flowing Landauer / entropy particles streaming away from the smooth Big Bang waist
        u_p = torch.remainder(self.cs_u + 0.11 * t, 1.0)
        z_p = (u_p * 2.55) * self.cs_sign
        r_p = 0.26 * torch.cosh(z_p / 1.18) * (0.35 + 0.65 * self.cs_rad)
        xyz = torch.stack([r_p * torch.cos(self.cs_ang + 0.4 * t), r_p * torch.sin(self.cs_ang + 0.4 * t), z_p], dim=-1)
        col = torch.stack([0.95 * u_p + 0.30, torch.full_like(u_p, 0.78), 1.0 - 0.45 * u_p], dim=-1) * 0.55
        self.canvas.render_particles(xyz, col, 1.2, cam, additive=True, depth_occlude=True)

    def _render_scene02(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c10 = _find_chunk(scene, "chunk_10")
        c11 = _find_chunk(scene, "chunk_11")
        t_soap = c10["local_start"] if c10 else dur * 0.48
        t_clamp = c11["local_start"] if c11 else dur * 0.74

        if t < t_soap:
            # Single-boundary scattered rim waves failing to converge without 10^122 hand-tuned phases
            pose = CameraPose(azim=0.25 + 0.8 * prog, elev=0.46, dist=7.8, fov_deg=44.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.12, show_grid=True, show_loom=False)

            x = self.sh_x * 3.4
            y = self.sh_y * 3.4
            r = torch.sqrt(x * x + y * y + 0.02)
            # Noisy uncoordinated inward/outward wave interference
            z = (
                0.22 * torch.sin(4.2 * r + 3.4 * t)
                + 0.16 * torch.cos(5.1 * x - 3.7 * y - 2.8 * t)
                + 0.14 * torch.sin(6.3 * y + 2.4 * x + 2.1 * t)
            )
            P = torch.stack([x, y, z], dim=-1)
            N = self.canvas.compute_grid_normals(P)
            hot = torch.sigmoid((torch.abs(z) - 0.18) * 10.0)
            alb = torch.stack([0.24 + 0.68 * hot, 0.54 - 0.14 * hot, 0.90 - 0.45 * hot], dim=-1)
            self.canvas.render_surface_mesh(P, alb, cam, normals=N, shininess=56.0, specular_strength=0.90, wire_stride=10, wire_boost=0.22, supersample=(4, 4))
        else:
            # Two-Ring Brushed-Brass Catenoid Soap Film clamping giant waves!
            clamp_u = smootherstep01((t - t_clamp) / 6.0)
            pose = CameraPose(azim=0.55 + 1.4 * prog, elev=0.20 + 0.08 * clamp_u, dist=7.6 - 1.2 * clamp_u, fov_deg=44.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.16, show_grid=True, show_loom=True)
            self._draw_two_wing_hourglass(
                cam, t, waist_r=0.24, height_z=2.45, ripple_amp=0.07, single_wing=True, clamp_quadrupole=clamp_u
            )

    def _render_scene03(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c14 = _find_chunk(scene, "chunk_14")
        t_clamp = c14["local_start"] if c14 else dur * 0.45
        clamp_u = smootherstep01((t - t_clamp) / 5.5)

        # Shift CMB sphere slightly left during chart window so both breathe cleanly!
        shift_y = -1.25 * smootherstep01((t - (t_clamp - 1.0)) / 2.0) * (1.0 - smootherstep01((t - (t_clamp + 30.0)) / 2.0))
        pose = CameraPose(azim=0.40 + 1.35 * prog, elev=0.22, dist=6.6, target=(0.0, -shift_y, 0.0), fov_deg=44.0)
        cam = CameraMatrix(pose, self.dev)
        self.clear_option_a_plus(cam, t, cosmos_mix=0.45, show_grid=False, show_loom=False)

        # 3D Rotating Planck CMB Sphere: Quadrupole `l=2` quiets down by 3x when `clamp_u -> 1`!
        temp = (1.0 - 0.72 * clamp_u) * self.cmb_quad + 0.42 * self.cmb_fine
        r_disp = 1.95 + 0.06 * temp
        P = self.cmb_unit * r_disp.unsqueeze(-1)
        N = self.canvas.compute_grid_normals(P)

        u_col = torch.clamp(0.5 + 0.48 * temp, 0.0, 1.0)
        # Authentic Planck-inspired sapphire -> alabaster -> warm gold colormap
        alb = torch.stack(
            [
                0.14 + 0.84 * (u_col ** 1.35),
                0.38 + 0.48 * torch.sin(math.pi * u_col),
                0.94 - 0.72 * (u_col ** 1.5),
            ],
            dim=-1,
        )
        self.canvas.render_surface_mesh(P, alb, cam, normals=N, shininess=38.0, specular_strength=0.55, emissive_rgb=alb * 0.16, supersample=(4, 4))

    def _render_scene04(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c18 = _find_chunk(scene, "chunk_18")
        c19 = _find_chunk(scene, "chunk_19")
        t_cpt = c18["local_start"] if c18 else 66.0
        t_wings = c19["local_start"] if c19 else 101.0

        if t < t_cpt:
            # Entangled B-meson asymmetric oscillation (`A -> B` fast gold arc vs `B -> A` slower coral arc)
            pose = CameraPose(azim=0.35 + 0.65 * prog, elev=0.26, dist=7.2, fov_deg=44.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.22, show_grid=True, show_loom=True)

            Pa, Na = make_trefoil_tube((-1.85, 0.0, 0.0), 1.25, 0.11, 2.2 * t, 1.0, self.dev)
            Pb, Nb = make_trefoil_tube((1.85, 0.0, 0.0), 1.25, 0.11, -2.2 * t, -1.0, self.dev)
            self.canvas.render_surface_mesh(Pa, (0.34, 0.80, 1.0), cam, normals=Na, shininess=64.0, emissive_rgb=(0.08, 0.22, 0.34), supersample=(2, 2))
            self.canvas.render_surface_mesh(Pb, (0.98, 0.78, 0.30), cam, normals=Nb, shininess=64.0, emissive_rgb=(0.24, 0.16, 0.04), supersample=(2, 2))

            # Asymmetric upper & lower transition arcs
            s = np.linspace(-1.6, 1.6, 90, dtype=np.float32)
            top_curve = torch.tensor(np.stack([s, np.zeros_like(s), 0.95 * (1.0 - (s / 1.6) ** 2)], axis=-1), device=self.dev, dtype=torch.float32)
            bot_curve = torch.tensor(np.stack([s, np.zeros_like(s), -0.62 * (1.0 - (s / 1.6) ** 2)], axis=-1), device=self.dev, dtype=torch.float32)
            Pt, Nt = make_tube_along_curve(top_curve, 0.055, n_around=14, closed=False)
            Pbot, Nbot = make_tube_along_curve(bot_curve, 0.035, n_around=14, closed=False)
            self.canvas.render_surface_mesh(Pt, (0.32, 0.92, 0.68), cam, normals=Nt, shininess=64.0, emissive_rgb=(0.08, 0.28, 0.18), supersample=(2, 2))
            self.canvas.render_surface_mesh(Pbot, (0.98, 0.52, 0.26), cam, normals=Nbot, shininess=64.0, emissive_rgb=(0.28, 0.10, 0.04), supersample=(2, 2))

        elif t < t_wings:
            # Three interlocking C, P, T gyroscopic symmetry rings locking into alignment!
            u = smootherstep01((t - t_cpt) / max(1.0, t_wings - t_cpt))
            pose = CameraPose(azim=0.5 + 1.1 * u, elev=0.25, dist=7.4, fov_deg=44.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.24, show_grid=True, show_loom=True)
            for rad_r, ax, col in ((2.15, "x", (0.98, 0.82, 0.30)), (1.72, "y", (0.35, 0.82, 1.0)), (1.30, "z", (0.28, 0.92, 0.68))):
                Pr, Nr = _core_torus_mesh((0.0, 0.0, 0.0), rad_r, 0.075, 140, 18, self.dev, axis=ax)
                self.canvas.render_surface_mesh(Pr, col, cam, normals=Nr, shininess=72.0, specular_strength=1.0, emissive_rgb=(col[0]*0.2, col[1]*0.2, col[2]*0.2), supersample=(2, 2))

        else:
            # Two-Wing Back-to-Back CPT Hourglass + Subatomic Matter/Antimatter Coin-Sorter!
            u = (t - t_wings) / max(1.0, dur - t_wings)
            pose = CameraPose(azim=0.45 + 1.65 * u, elev=0.16, dist=8.4 - 0.8 * math.sin(math.pi * u), fov_deg=45.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.35, show_grid=True, show_loom=False)
            self._draw_two_wing_hourglass(cam, t, waist_r=0.26, height_z=2.65, ripple_amp=0.06, dual_color_cpt=True)

            # Coin-sorter streams: +sign (Golden protons -> +Z wing), -sign (Cyan antiprotons -> -Z mirror wing)
            u_p = torch.remainder(self.cs_u + 0.16 * t, 1.0)
            z_p = (0.08 + 2.50 * u_p) * self.cs_sign
            r_p = 0.25 * torch.cosh(z_p / 1.18) * (0.25 + 0.65 * self.cs_rad)
            ang_p = self.cs_ang + 0.8 * t * self.cs_sign
            xyz = torch.stack([r_p * torch.cos(ang_p), r_p * torch.sin(ang_p), z_p], dim=-1)
            is_pos = (self.cs_sign > 0).float().unsqueeze(-1)
            col = is_pos * torch.tensor([1.05, 0.82, 0.28], device=self.dev) + (1.0 - is_pos) * torch.tensor([0.28, 0.86, 1.10], device=self.dev)
            self.canvas.render_particles(xyz, col * 0.72, 1.35, cam, additive=True, depth_occlude=True)

    def _render_scene05(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c24 = _find_chunk(scene, "chunk_24")
        t_pleats = c24["local_start"] if c24 else 57.0
        pleat_on = smootherstep01((t - t_pleats) / 4.5)

        pose = CameraPose(azim=0.42 + 1.25 * prog, elev=0.38 - 0.08 * pleat_on, dist=7.6, fov_deg=44.0)
        cam = CameraMatrix(pose, self.dev)
        self.clear_option_a_plus(cam, t, cosmos_mix=0.16, show_grid=True, show_loom=False)

        x = self.sh_x * 3.3
        y = self.sh_y * 3.3
        r2 = x * x + y * y

        # Before `t_pleats`: gravity bowl empties & bounces flat (`R_32 = 0.16` crash!)
        # After `t_pleats`: 3 deep uncharged `SO(3)` geometric pleats stay pinned while golden photon waves pass right through!
        bounce = math.cos(2.8 * t) * (1.0 - pleat_on)
        bowl = -0.85 * bounce * torch.exp(-r2 / 1.45)

        pleat_folds = -0.58 * pleat_on * (
            torch.exp(-((x + 1.45) / 0.34) ** 2)
            + 1.15 * torch.exp(-(x / 0.36) ** 2)
            + torch.exp(-((x - 1.45) / 0.34) ** 2)
        )
        photon_wave = 0.085 * torch.sin(4.4 * x - 5.2 * t)

        z = bowl + pleat_folds + photon_wave
        P = torch.stack([x, y, z], dim=-1)
        N = self.canvas.compute_grid_normals(P)

        crest = torch.sigmoid(math.sin(1.0) * torch.sin(4.4 * x - 5.2 * t) * 5.0)
        pleat_glow = torch.clamp(-pleat_folds / 0.65, 0.0, 1.0)
        alb = torch.stack(
            [
                0.20 + 0.62 * crest + 0.18 * pleat_glow,
                0.52 + 0.32 * crest + 0.28 * pleat_glow,
                0.88 - 0.38 * crest + 0.12 * pleat_glow,
            ],
            dim=-1,
        )
        em = torch.stack([0.22 * crest, 0.16 * crest + 0.14 * pleat_glow, 0.24 * pleat_glow], dim=-1)
        self.canvas.render_surface_mesh(P, alb, cam, normals=N, shininess=58.0, specular_strength=0.92, emissive_rgb=em, wire_stride=10, wire_boost=0.24, supersample=(4, 4))

    def _render_scene06(self, scene: dict, t: float, dur: float, prog: float) -> None:
        c30 = _find_chunk(scene, "chunk_30")
        t_ds = c30["local_start"] if c30 else dur * 0.62

        if t < t_ds:
            # Arena 4 3D CPT Hourglass spinning inside WeaveForge wireframe tank
            pose = CameraPose(azim=0.55 + 1.6 * prog, elev=0.24, dist=8.2, fov_deg=44.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.26, show_grid=True, show_loom=True)
            self.canvas.render_particles(self.box_pts * 1.12, self.box_rgb * 0.55, 1.2, cam, additive=True, depth_occlude=True)
            self._draw_two_wing_hourglass(cam, t, waist_r=0.26, height_z=2.45, dual_color_cpt=True)
        else:
            # Episode 3 Preview: Taut Two-Ended Standing-Wave Double-Slit Interference Tank -> Cosmic Pan-Out!
            u = smootherstep01((t - t_ds) / max(1.0, dur - t_ds))
            pan_out = smootherstep01((u - 0.58) / 0.42)
            pose = CameraPose(azim=-0.95 + 0.55 * u, elev=0.40 - 0.12 * pan_out, dist=7.4 + 14.0 * pan_out, fov_deg=45.0)
            cam = CameraMatrix(pose, self.dev)
            self.clear_option_a_plus(cam, t, cosmos_mix=0.22 + 0.65 * pan_out, show_grid=(pan_out < 0.5), show_loom=False)

            x = self.sh_x * 3.2
            y = self.sh_y * 3.2
            # Two slits at `(-0.65, -0.4)` and `(+0.65, -0.4)` generating crisp standing-wave interference fringes!
            d1 = torch.sqrt((x + 0.68) ** 2 + (y + 0.55) ** 2 + 0.04)
            d2 = torch.sqrt((x - 0.68) ** 2 + (y + 0.55) ** 2 + 0.04)
            src_wave = 0.14 * torch.sin(5.5 * y - 4.5 * t) * torch.sigmoid((-0.55 - y) * 8.0)
            interf = 0.12 * (torch.sin(5.5 * d1 - 4.5 * t) + torch.sin(5.5 * d2 - 4.5 * t)) * torch.sigmoid((y + 0.55) * 8.0)
            z = src_wave + interf
            P = torch.stack([x, y, z], dim=-1)
            N = self.canvas.compute_grid_normals(P)
            fringe = torch.clamp(torch.abs(interf) / 0.22, 0.0, 1.0)
            alb = torch.stack([0.20 + 0.22 * fringe, 0.54 + 0.40 * fringe, 0.90 - 0.16 * fringe], dim=-1)
            self.canvas.render_surface_mesh(P, alb, cam, normals=N, shininess=62.0, specular_strength=0.95, emissive_rgb=alb * (0.24 * fringe.unsqueeze(-1)), wire_stride=12, wire_boost=0.20, supersample=(4, 4))
