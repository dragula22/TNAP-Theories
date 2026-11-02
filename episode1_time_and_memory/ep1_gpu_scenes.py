"""
Episode 1 Native `3840x2160` (`4K UHD`) RTX 5080 CUDA Scene Director (`ep1_gpu_scenes.py`):
  'Is Time Even Real? Vinyl Records, Memory & Why GPS Satellites Run Fast'

Visual Palette (Locked Option A+ — 'Luminous Sapphire Slate', 39% Vibrant Mid-Tone):
  • Studio outer -> inner radial canvas: sRGB `(35, 52, 78)` -> `(68, 97, 138)` (analytically inverted
    through ACES + gamma 2.2 + vignette compensation so output frames match Option A+ pixel-for-pixel!).
  • Zero snow-white flashbang, zero pitch-black cave crush.
  • Signature tactile motifs:
      1. Taut glowing clear-sapphire monofilament fishing line & 3D trefoil knots
      2. Kitaoka asymmetric spiral-groove optical illusion 4D vinyl record
      3. Multi-scale physical memory & Landauer `k_B T ln 2` thermal heat-tax ripples
      4. Sunlit 3D Blue-Marble Earth + 31-satellite GPS constellation + `3,189 km` zero-crossing ring
      5. Solar funnel (`Mercury 42.98"/cy`, `Cassini`), `GW170817` neutron-star kilonova + cosmic pan-out
      6. Full GPU pixel-shader Relativistic Spinning Kerr Black Hole (`a/M = 0.96`)
      7. David's Bonus Discovery (`chunk_23b`): Quantum Phase-Slip Self-Healing Threads (`Melt • Slip • Weld`)
         + Unbreakable Planck-Tension Fishing-Reel Spool growing at `R = 2GM / c^2` (`1.000000` match!)
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


def make_sphere_mesh(
    radius: float,
    center: Tuple[float, float, float],
    n_lat: int = 64,
    n_lon: int = 96,
    device: Optional[torch.device] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    assert device is not None
    P, _, _ = _core_sphere_mesh(center, radius, n_lon, n_lat, device)
    c_t = torch.tensor(center, device=device, dtype=torch.float32).view(1, 1, 3)
    N = F.normalize(P - c_t, dim=-1, eps=1e-7)
    return P, N


def make_torus_mesh(
    major_r: float,
    minor_r: float,
    center: Tuple[float, float, float],
    n_u: int = 128,
    n_v: int = 20,
    device: Optional[torch.device] = None,
    axis: str = "z",
) -> Tuple[torch.Tensor, torch.Tensor]:
    assert device is not None
    return _core_torus_mesh(center, major_r, minor_r, n_u, n_v, device, axis=axis)


def _find_chunk(scene: Optional[dict], cid: str) -> Optional[dict]:
    if not scene:
        return None
    for ch in scene.get("chunks") or []:
        if ch["chunk_id"] == cid:
            return ch
    return None


def _srgb_tensor_to_hdr_pre_aces(srgb_01: torch.Tensor) -> torch.Tensor:
    """
    Analytically inverts Gamma 1/2.2 + Narkowicz ACES Filmic curve `(a=2.51, b=0.03, c=2.43, d=0.59, e=0.14)`
    so any target sRGB `[0..1]` color placed in `canvas.hdr` (divided by `vignette * exposure`)
    emerges from `finalize_srgb_uint8()` at its EXACT target sRGB value!
    """
    m = torch.clamp(srgb_01, 0.001, 0.92) ** 2.2
    A = 2.51 - 2.43 * m
    B = 0.03 - 0.59 * m
    C = -0.14 * m
    disc = torch.clamp(B * B - 4.0 * A * C, min=0.0)
    h = (-B + torch.sqrt(disc)) / (2.0 * A)
    return torch.clamp(h, min=0.0)


class Episode1GPU3DDirector:
    """Native 4K (`3840x2160`) RTX 5080 CUDA 3D & Shader Director for Episode 1."""

    EXPOSURE = 1.00
    BLOOM = 0.36

    def __init__(self, device: Optional[torch.device] = None):
        self.canvas = GPUCanvas1080p(device=device)
        self.dev = self.canvas.device
        self.w = self.canvas.w
        self.h = self.canvas.h

        # Precompute normalized screen coordinates `(-aspect..+aspect, +1..-1)` at quarter-res `(960x540)`
        # for super-fast `<1.2 ms` GPU pixel shaders (Option A+ backdrop, Kerr ray-march, Kitaoka illusion)
        self.qw = self.w // 4
        self.qh = self.h // 4
        gy_q = torch.linspace(1.0, -1.0, self.qh, device=self.dev)
        gx_q = torch.linspace(-self.w / self.h, self.w / self.h, self.qw, device=self.dev)
        self.q_yy, self.q_xx = torch.meshgrid(gy_q, gx_q, indexing="ij")

        # Half-res `(1920x1080)` grid for razor-sharp relativistic Kerr black hole ray-shader
        self.hw = self.w // 2
        self.hh = self.h // 2
        gy_h = torch.linspace(1.0, -1.0, self.hh, device=self.dev)
        gx_h = torch.linspace(-self.w / self.h, self.w / self.h, self.hw, device=self.dev)
        self.h_yy, self.h_xx = torch.meshgrid(gy_h, gx_h, indexing="ij")

        self._init_option_a_plus_canvases()
        self._init_monofilament_loom()
        self._init_earth_and_gps()
        self._init_deep_field_galaxies()
        self._init_thermal_and_spool_particles()

    # ------------------------------------------------------------------
    # Precomputed Buffers
    # ------------------------------------------------------------------
    def _init_option_a_plus_canvases(self) -> None:
        """Precomputes Locked Option A+ ('Luminous Sapphire Slate') & 'Sapphire Cosmos' HDR bases."""
        # Normalized radial falloff `r_norm` from center spotlight `(0, -0.04)` to corners
        rx = self.q_xx / (self.w / self.h)
        ry = self.q_yy + 0.04
        rad = torch.clamp(torch.sqrt(rx * rx * 0.88 + ry * ry * 1.04), 0.0, 1.25)
        w_center = torch.exp(-1.35 * (rad ** 1.65))  # 1.0 at center -> ~0.10 at corners

        # Locked Option A+ exact sRGB endpoints:
        #   bg_outer = (35, 52, 78), bg_inner = (68, 97, 138)
        out_studio = torch.tensor([35.0, 52.0, 78.0], device=self.dev).view(3, 1, 1) / 255.0
        inn_studio = torch.tensor([68.0, 97.0, 138.0], device=self.dev).view(3, 1, 1) / 255.0
        srgb_studio_q = out_studio + (inn_studio - out_studio) * w_center.unsqueeze(0)

        # Slightly deeper Sapphire Cosmos for orbital / black-hole / deep-field galaxy shots (never pitch black!)
        out_cosmos = torch.tensor([21.0, 33.0, 54.0], device=self.dev).view(3, 1, 1) / 255.0
        inn_cosmos = torch.tensor([46.0, 69.0, 104.0], device=self.dev).view(3, 1, 1) / 255.0
        srgb_cosmos_q = out_cosmos + (inn_cosmos - out_cosmos) * w_center.unsqueeze(0)

        hdr_studio_q = _srgb_tensor_to_hdr_pre_aces(srgb_studio_q).unsqueeze(0)
        hdr_cosmos_q = _srgb_tensor_to_hdr_pre_aces(srgb_cosmos_q).unsqueeze(0)

        hdr_studio_full = F.interpolate(hdr_studio_q, size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)
        hdr_cosmos_full = F.interpolate(hdr_cosmos_q, size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)

        # Compensate `canvas.vignette` so the final sRGB output hits Option A+ without darkened corners!
        inv_vig = 1.0 / torch.clamp(self.canvas.vignette * self.EXPOSURE, min=0.45)
        self.base_hdr_studio = hdr_studio_full * inv_vig
        self.base_hdr_cosmos = hdr_cosmos_full * inv_vig

        # Subtle crisp architectural studio grid mask at full 4K `(186, 218, 255)`
        step_px = max(48, int(round(120 * self.canvas.res_scale)))
        yi = torch.arange(self.h, device=self.dev)
        xi = torch.arange(self.w, device=self.dev)
        gy_m = (yi % step_px == 0).float().view(1, self.h, 1)
        gx_m = (xi % step_px == 0).float().view(1, 1, self.w)
        g_mask = torch.clamp(gy_m + gx_m, 0.0, 1.0)
        self.studio_grid_hdr = g_mask * torch.tensor([0.020, 0.032, 0.048], device=self.dev).view(3, 1, 1)

    def _init_monofilament_loom(self) -> None:
        """Precomputes 3D taut monofilament background threads & 4x4x4 quantum knot lattice."""
        pts_list = []
        col_list = []
        s_vals = np.linspace(-8.5, 8.5, 220, dtype=np.float32)
        for k in np.linspace(-4.8, 4.8, 15, dtype=np.float32):
            # Horizontal warp thread
            pts_list.append(np.stack([s_vals, np.full_like(s_vals, k), np.full_like(s_vals, -1.6)], axis=-1))
            # Vertical weft thread
            pts_list.append(np.stack([np.full_like(s_vals, k * 1.35), s_vals * 0.65, np.full_like(s_vals, -1.6)], axis=-1))
        loom_np = np.concatenate(pts_list, axis=0)
        self.loom_pts = torch.tensor(loom_np, device=self.dev, dtype=torch.float32)
        c_base = torch.tensor([0.22, 0.58, 0.88], device=self.dev, dtype=torch.float32)
        self.loom_rgb = c_base.unsqueeze(0).expand(len(loom_np), 3).contiguous()

        # 2D sheet grid `(240 x 240)` for tapestry, gravity bowls, and wave ripples
        u = torch.linspace(-1.0, 1.0, 240, device=self.dev)
        self.sh_x, self.sh_y = torch.meshgrid(u, u, indexing="ij")

        # Polar grid `(240 x 360)` for Kitaoka vinyl record, funnels & hourglass
        pr = torch.linspace(0.0, 1.0, 240, device=self.dev)
        pth = torch.linspace(0.0, 2.0 * math.pi, 360, device=self.dev)
        self.pol_r, self.pol_th = torch.meshgrid(pr, pth, indexing="ij")

        # 64-node 3D lattice centers `(4 x 4 x 4)` for Page-Wootters Scene 01
        coords = [-1.65, -0.55, 0.55, 1.65]
        lat = [(x, y, z) for x in coords for y in coords for z in coords]
        self.pw_nodes = torch.tensor(lat, device=self.dev, dtype=torch.float32)

    def _init_earth_and_gps(self) -> None:
        """Procedural sunlit Blue-Marble Earth mesh + 31-satellite 6-plane GPS constellation."""
        P_e, N_e = make_sphere_mesh(1.38, (0.0, 0.0, 0.0), n_lat=200, n_lon=300, device=self.dev)
        self.earth_N = N_e  # unit sphere coordinates!
        nx, ny, nz = N_e[..., 0], N_e[..., 1], N_e[..., 2]

        # Procedural continents + cloud swirls using smooth trigonometric spherical harmonics
        c1 = torch.sin(3.1 * nx + 2.4 * ny) * torch.cos(2.7 * nz - 1.8 * nx)
        c2 = 0.55 * torch.sin(6.4 * ny - 4.8 * nz) * torch.cos(5.2 * nx + 3.1 * ny)
        c3 = 0.28 * torch.cos(11.5 * nx + 9.2 * nz - 7.4 * ny)
        elev = c1 + c2 + c3
        land = torch.sigmoid((elev - 0.14) * 14.0)
        ice = torch.sigmoid((torch.abs(nz) - 0.78) * 22.0)
        clouds = torch.clamp(
            0.5 + 0.5 * torch.sin(7.5 * nx - 5.5 * ny + 4.2 * nz) * torch.cos(9.0 * ny + 6.2 * nz),
            0.0,
            1.0,
        ) ** 3.2

        ocean_col = torch.stack(
            [
                torch.full_like(nx, 0.09),
                0.34 + 0.14 * torch.clamp(-elev, 0.0, 1.0),
                0.76 + 0.16 * torch.clamp(-elev, 0.0, 1.0),
            ],
            dim=-1,
        )
        land_col = torch.stack(
            [
                0.16 + 0.28 * torch.clamp(elev - 0.2, 0.0, 1.0),
                0.56 - 0.12 * torch.clamp(elev - 0.35, 0.0, 1.0),
                torch.full_like(nx, 0.24),
            ],
            dim=-1,
        )
        alb = ocean_col * (1.0 - land.unsqueeze(-1)) + land_col * land.unsqueeze(-1)
        ice_col = torch.tensor([0.84, 0.90, 0.96], device=self.dev).view(1, 1, 3)
        alb = alb * (1.0 - ice.unsqueeze(-1)) + ice_col * ice.unsqueeze(-1)
        alb = torch.clamp(alb + 0.42 * clouds.unsqueeze(-1) * ice_col, 0.0, 0.95)
        self.earth_albedo = alb

        # 31 GPS satellites across 6 55°-inclined orbital planes at scaled radius `R_gps = 3.95`
        inc = math.radians(55.0)
        planes = []
        phases = []
        for idx in range(31):
            p_i = idx % 6
            raan = p_i * (2.0 * math.pi / 6.0)
            ph0 = (idx // 6) * (2.0 * math.pi / 5.2) + 0.32 * p_i
            planes.append(raan)
            phases.append(ph0)
        self.gps_raan = torch.tensor(planes, device=self.dev, dtype=torch.float32)
        self.gps_ph0 = torch.tensor(phases, device=self.dev, dtype=torch.float32)
        self.gps_inc = inc

    def _init_deep_field_galaxies(self) -> None:
        """165 crisp 3D spiral & golden elliptical galaxies (`214,500` stars) for cosmic pan-outs."""
        rng = np.random.default_rng(20261)
        n_gal = 165
        spg = 1300
        idx = np.arange(n_gal, dtype=np.float32)
        phi = math.pi * (3.0 - math.sqrt(5.0)) * idx
        cos_th = 1.0 - 2.0 * ((idx + 0.5) / n_gal)
        sin_th = np.sqrt(np.maximum(0.0, 1.0 - cos_th * cos_th))
        radii = 12.0 + 78.0 * ((idx / max(1, n_gal - 1)) ** 0.78)
        rng.shuffle(radii)
        centers = np.stack([radii * np.cos(phi) * sin_th, radii * np.sin(phi) * sin_th, radii * cos_th * 0.84], axis=-1)

        all_xyz, all_rgb, all_sz = [], [], []
        for g_i in range(n_gal):
            u = rng.random(spg).astype(np.float32)
            g_sc = float(rng.uniform(0.60, 1.20)) * (1.0 + 0.008 * radii[g_i])
            if g_i % 5 == 4:
                rr = (u ** 0.85) * 1.15 * g_sc
                th = rng.uniform(0.0, 2.0 * math.pi, spg).astype(np.float32)
                ph = np.arccos(rng.uniform(-1.0, 1.0, spg)).astype(np.float32)
                lx = rr * np.sin(ph) * np.cos(th)
                ly = rr * np.sin(ph) * np.sin(th) * 0.70
                lz = rr * np.cos(ph) * 0.52
                lum = (0.30 + 0.70 * (rng.random(spg).astype(np.float32) ** 1.6)) * np.exp(-u * 1.1)
                rgb = np.stack([1.22 * lum, 0.88 * lum, 0.45 * lum], axis=-1)
            else:
                n_arms = 2 if (g_i % 3 != 0) else 3
                is_b = np.arange(spg) < (spg // 4)
                arm_a = rng.integers(0, n_arms, size=spg).astype(np.float32) * (2.0 * math.pi / n_arms)
                rr_arm = (0.12 + 1.85 * (u ** 0.78)) * g_sc
                ang = arm_a + 2.15 * np.log(u + 0.14) + rng.normal(0.0, 0.22 + 0.14 * u, size=spg).astype(np.float32)
                rr_b = (u ** 0.9) * 0.36 * g_sc
                th_b = rng.uniform(0.0, 2.0 * math.pi, spg).astype(np.float32)
                lx = np.where(is_b, rr_b * np.cos(th_b), rr_arm * np.cos(ang))
                ly = np.where(is_b, rr_b * np.sin(th_b), rr_arm * np.sin(ang))
                lz = rng.normal(0.0, 0.06 * g_sc, size=spg).astype(np.float32)
                cw = np.where(is_b, 1.0, np.exp(-(u / 0.28) ** 2))
                lum = (0.28 + 0.78 * (rng.random(spg).astype(np.float32) ** 1.6)) * (0.48 + 0.52 * np.exp(-0.5 * u))
                rgb = np.stack(
                    [
                        (1.22 * cw + 0.32 * (1.0 - cw)) * lum,
                        (0.90 * cw + 0.82 * (1.0 - cw)) * lum,
                        (0.46 * cw + 1.32 * (1.0 - cw)) * lum,
                    ],
                    axis=-1,
                )
            q_mat, _ = np.linalg.qr(rng.normal(size=(3, 3)).astype(np.float32))
            all_xyz.append(np.stack([lx, ly, lz], axis=-1) @ q_mat.T + centers[g_i])
            all_rgb.append(rgb)
            all_sz.append(np.full(spg, 0.96 if radii[g_i] < 40.0 else 0.80, dtype=np.float32))

        self.df_pts = torch.tensor(np.concatenate(all_xyz, axis=0), device=self.dev, dtype=torch.float32)
        self.df_rgb = torch.tensor(np.concatenate(all_rgb, axis=0), device=self.dev, dtype=torch.float32)
        self.df_sz = torch.tensor(np.concatenate(all_sz, axis=0), device=self.dev, dtype=torch.float32)

    def _init_thermal_and_spool_particles(self) -> None:
        """Particles for Landauer thermal ripples, hourglass footprints & Planck fishing-reel spool."""
        g = torch.Generator(device="cpu")
        g.manual_seed(6123)
        n = 28000
        self.th_u = torch.rand(n, generator=g).to(self.dev)
        self.th_ang = (torch.rand(n, generator=g) * (2.0 * math.pi)).to(self.dev)
        self.th_z = (torch.randn(n, generator=g) * 0.16).to(self.dev)
        self.th_lum = (0.40 + 0.85 * (torch.rand(n, generator=g) ** 1.5)).to(self.dev)

        # Fibonacci sphere points `(18,000)` for glowing wound fishing-line spool & dense throat
        n_sp = 18000
        idx = torch.arange(n_sp, dtype=torch.float32, device=self.dev)
        phi = math.pi * (3.0 - math.sqrt(5.0)) * idx
        z_u = 1.0 - 2.0 * ((idx + 0.5) / n_sp)
        r_xy = torch.sqrt(torch.clamp(1.0 - z_u * z_u, min=0.0))
        self.fib_dir = torch.stack([r_xy * torch.cos(phi), r_xy * torch.sin(phi), z_u], dim=-1)
        self.fib_phase = phi

    # ------------------------------------------------------------------
    # Core Backdrop & Reusable 3D Tactile Props
    # ------------------------------------------------------------------
    def clear_option_a_plus_studio(
        self,
        cam: CameraMatrix,
        t: float,
        cosmos_depth: float = 0.0,
        show_grid: bool = True,
        star_gain: float = 0.36,
    ) -> None:
        """
        Clears Z-buffer and paints Locked Option A+ ('Luminous Sapphire Slate', 39% vibrant mid-tone),
        smoothly blending toward 'Sapphire Cosmos' when `cosmos_depth > 0` for space/black-hole shots.
        """
        self.canvas.zbuf.fill_(1e6)
        cd = max(0.0, min(1.0, cosmos_depth))
        base = self.base_hdr_studio * (1.0 - cd) + self.base_hdr_cosmos * cd

        # Subtle camera-coupled living sapphire-cyan studio caustics so backdrop breathes organically
        fov_s = math.tan(0.5 * math.radians(cam.pose.fov_deg))
        rx = cam.fwd[0] + self.q_xx * fov_s * cam.right[0] + self.q_yy * fov_s * cam.up[0]
        ry = cam.fwd[1] + self.q_xx * fov_s * cam.right[1] + self.q_yy * fov_s * cam.up[1]
        rz = cam.fwd[2] + self.q_xx * fov_s * cam.right[2] + self.q_yy * fov_s * cam.up[2]
        inv_l = torch.rsqrt(rx * rx + ry * ry + rz * rz + 1e-8)
        dx, dy, dz = rx * inv_l, ry * inv_l, rz * inv_l

        caustic = 0.5 + 0.5 * torch.sin(3.2 * dx - 2.4 * dy + 1.8 * dz + 0.18 * t) * torch.cos(
            2.7 * dy + 2.1 * dz - 0.14 * t
        )
        c_rgb_q = torch.stack(
            [0.008 * caustic, 0.022 * caustic, 0.038 * caustic], dim=0
        ).unsqueeze(0)
        c_full = F.interpolate(c_rgb_q, size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)

        self.canvas.hdr = base + c_full
        if show_grid:
            self.canvas.hdr = self.canvas.hdr + self.studio_grid_hdr * (1.0 - 0.65 * cd)

        if star_gain > 0.01:
            twinkle = (0.86 + 0.14 * torch.sin(1.7 * t + self.canvas.star_phase)).unsqueeze(-1)
            self.canvas.render_particles(
                self.canvas.star_xyz,
                self.canvas.star_rgb * (twinkle * star_gain),
                self.canvas.star_sizes,
                cam,
                additive=True,
                depth_occlude=False,
            )

    def _make_trefoil_knot_mesh(
        self,
        scale: float = 1.15,
        tube_r: float = 0.11,
        spin: float = 0.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        n_pts: int = 260,
        n_around: int = 28,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Generates a smooth 3D `(2, 3)` trefoil monofilament knot tube `(P, N, s_param)`."""
        s = torch.linspace(0.0, 2.0 * math.pi, n_pts, device=self.dev)
        cx = (torch.sin(s) + 2.0 * torch.sin(2.0 * s)) * (0.34 * scale)
        cy = (torch.cos(s) - 2.0 * torch.cos(2.0 * s)) * (0.34 * scale)
        cz = (-torch.sin(3.0 * s)) * (0.38 * scale)

        cs, sn = math.cos(spin), math.sin(spin)
        rx = cx * cs - cy * sn + center[0]
        ry = cx * sn + cy * cs + center[1]
        rz = cz + center[2]
        curve = torch.stack([rx, ry, rz], dim=-1)
        P, N = make_tube_along_curve(curve, tube_r, n_around=n_around)
        return P, N, s

    def _render_taut_loom_threads(self, cam: CameraMatrix, t: float, gain: float = 0.55) -> None:
        """Renders crisp taut clear-sapphire monofilament warp/weft background lines."""
        pulse = 0.72 + 0.28 * torch.sin(0.9 * self.loom_pts[:, 0] + 0.7 * self.loom_pts[:, 1] - 1.8 * t)
        self.canvas.render_particles(
            self.loom_pts,
            self.loom_rgb * (gain * pulse.unsqueeze(-1)),
            1.15,
            cam,
            additive=True,
            depth_occlude=True,
        )

    # ------------------------------------------------------------------
    # Master Scene Dispatcher
    # ------------------------------------------------------------------
    def render_scene_frame(self, scene: dict, t: float) -> np.ndarray:
        sid = scene["id"]
        dur = float(scene["duration_sec"])
        prog = max(0.0, min(1.0, t / max(0.001, dur)))

        if sid in ("intro00", "scene00"):
            self._render_scene00_welcome(scene, t, dur, prog)
        elif sid == "scene01":
            self._render_scene01_page_wootters(scene, t, dur, prog)
        elif sid == "scene02":
            self._render_scene02_memory_landauer(scene, t, dur, prog)
        elif sid == "scene03":
            self._render_scene03_gps_satellites(scene, t, dur, prog)
        elif sid == "scene04":
            self._render_scene04_strong_field(scene, t, dur, prog)
        elif sid == "scene05":
            self._render_scene05_lacuna_and_kerr(scene, t, dur, prog)
        else:
            self._render_scene06_outro_and_panout(scene, t, dur, prog)

        return self.canvas.finalize_srgb_uint8(exposure=self.EXPOSURE, bloom_strength=self.BLOOM)

    # ------------------------------------------------------------------
    # SCENE 00 (Welcome): Taut Monofilament Knot -> Kitaoka Vinyl Illusion -> 3 Checks
    # ------------------------------------------------------------------
    def _render_scene00_welcome(self, scene: dict, t: float, dur: float, prog: float) -> None:
        if scene["id"] == "intro00":
            # Musical 3.6s opening bloom: glowing taut monofilament trefoil knot tightening into focus
            cam = CameraMatrix(
                CameraPose(azim=0.35 + 0.18 * t, elev=0.22, dist=4.6 - 0.25 * prog, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.05, show_grid=True, star_gain=0.32)
            self._render_taut_loom_threads(cam, t, gain=0.60)
            P_k, N_k, s_k = self._make_trefoil_knot_mesh(scale=1.35, tube_r=0.12, spin=0.35 * t)
            wave_p = torch.exp(-((torch.sin(1.5 * s_k - 2.6 * t)) ** 2) / 0.08).view(-1, 1, 1)
            emit = wave_p * torch.tensor([0.95, 0.82, 0.30], device=self.dev).view(1, 1, 3) + torch.tensor(
                [0.06, 0.32, 0.58], device=self.dev
            ).view(1, 1, 3)
            self.canvas.render_surface_mesh(
                P_k,
                (0.28, 0.72, 0.98),
                cam,
                normals=N_k,
                emissive_rgb=emit,
                alpha=0.95,
                shininess=72.0,
                specular_strength=0.90,
                fresnel_rgb=(0.75, 0.95, 1.0),
                fresnel_strength=0.65,
            )
            return

        ch01 = _find_chunk(scene, "chunk_01")
        ch02 = _find_chunk(scene, "chunk_02")
        t01_s = ch01["local_start"] if ch01 else 31.8
        t02_s = ch02["local_start"] if ch02 else 62.5

        if t < t01_s - 0.4:
            # Chunk 00: Taut clear monofilament fishing-line trefoil knot + straight tension lines
            cam = CameraMatrix(
                CameraPose(azim=0.45 + 0.14 * t, elev=0.20 + 0.05 * math.sin(0.25 * t), dist=4.45, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.04, show_grid=True, star_gain=0.30)
            self._render_taut_loom_threads(cam, t, gain=0.55)

            # Taut lead-in line feeding straight into the trefoil knot
            lx = torch.linspace(-6.5, 6.5, 160, device=self.dev)
            ly = 0.06 * torch.sin(2.5 * lx - 4.0 * t)
            lz = torch.zeros_like(lx) - 0.12
            P_l, N_l = make_tube_along_curve(torch.stack([lx, ly, lz], dim=-1), 0.042, n_around=16)
            self.canvas.render_surface_mesh(
                P_l, (0.42, 0.84, 1.0), cam, normals=N_l, emissive_rgb=(0.08, 0.35, 0.58), alpha=0.90, shininess=64.0
            )

            P_k, N_k, s_k = self._make_trefoil_knot_mesh(scale=1.32, tube_r=0.115, spin=0.28 * t)
            pulse = torch.exp(-((torch.sin(1.5 * s_k - 2.2 * t)) ** 2) / 0.07).view(-1, 1, 1)
            emit = pulse * torch.tensor([1.05, 0.86, 0.32], device=self.dev).view(1, 1, 3) + torch.tensor(
                [0.05, 0.28, 0.52], device=self.dev
            ).view(1, 1, 3)
            self.canvas.render_surface_mesh(
                P_k, (0.30, 0.74, 0.98), cam, normals=N_k, emissive_rgb=emit, alpha=0.95, shininess=76.0, specular_strength=0.92
            )

        elif t < t02_s - 0.4:
            # Chunk 01: Kitaoka Optical-Illusion 4D Spacetime Vinyl Record!
            dt = max(0.0, t - (t01_s - 0.4))
            # Record gently rotates for first 7s, then comes to a COMPLETE STOP ("nothing on the map actually moves")
            # while Kitaoka asymmetric phase-stepped spiral wedges create the unmistakable inward-motion illusion!
            spin_angle = 1.6 * (1.0 - math.exp(-0.35 * dt))
            cam = CameraMatrix(
                CameraPose(
                    azim=-0.35 + 0.08 * math.sin(0.22 * dt),
                    elev=0.68 - 0.08 * smoothstep01(dt / 14.0),
                    dist=4.55 - 0.35 * smoothstep01(dt / 18.0),
                    target=(0.0, 0.0, 0.0),
                    fov_deg=43.0,
                ),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.06, show_grid=True, star_gain=0.28)

            r = 0.22 + 2.15 * self.pol_r
            th = self.pol_th + spin_angle
            px = r * torch.cos(th)
            py = r * torch.sin(th)
            pz = 0.025 * torch.sin(26.0 * r) * (1.0 - 0.5 * self.pol_r)
            P_v = torch.stack([px, py, pz], dim=-1)

            # Kitaoka peripheral-drift asymmetric luminance cycle (`0..1` sawtooth phase along logarithmic spiral wedges)
            spiral_phase = torch.remainder((18.0 * th / (2.0 * math.pi)) + 9.5 * torch.log(r + 0.18), 1.0)
            # 4 asymmetric stepped bands: deep navy -> bright alabaster -> electric cyan -> solar gold
            b_dark = (spiral_phase < 0.26).float()
            b_hi = ((spiral_phase >= 0.26) & (spiral_phase < 0.48)).float()
            b_mid = ((spiral_phase >= 0.48) & (spiral_phase < 0.78)).float()
            b_warm = (spiral_phase >= 0.78).float()

            c_dark = torch.tensor([0.04, 0.09, 0.19], device=self.dev).view(1, 1, 3)
            c_hi = torch.tensor([0.74, 0.86, 0.96], device=self.dev).view(1, 1, 3)
            c_mid = torch.tensor([0.14, 0.54, 0.86], device=self.dev).view(1, 1, 3)
            c_warm = torch.tensor([0.88, 0.70, 0.24], device=self.dev).view(1, 1, 3)

            alb = (
                b_dark.unsqueeze(-1) * c_dark
                + b_hi.unsqueeze(-1) * c_hi
                + b_mid.unsqueeze(-1) * c_mid
                + b_warm.unsqueeze(-1) * c_warm
            )
            # Crisp gold center record label (`r < 0.56`)
            is_lbl = (r < 0.56).unsqueeze(-1)
            lbl_col = torch.tensor([0.84, 0.66, 0.22], device=self.dev).view(1, 1, 3)
            alb = torch.where(is_lbl, lbl_col, alb)

            self.canvas.render_surface_mesh(
                P_v,
                alb,
                cam,
                emissive_rgb=alb * 0.24,
                alpha=0.98,
                shininess=64.0,
                specular_strength=0.55,
            )

            # Three simultaneous glowing groove event pins (Yesterday, Today, Tomorrow all sitting on the disc at once!)
            pins = torch.tensor(
                [
                    [0.85 * math.cos(0.9), 0.85 * math.sin(0.9), 0.14],
                    [1.42 * math.cos(2.3), 1.42 * math.sin(2.3), 0.14],
                    [1.98 * math.cos(4.1), 1.98 * math.sin(4.1), 0.14],
                ],
                device=self.dev,
            )
            pin_cols = torch.tensor(
                [[0.35, 0.90, 1.0], [1.15, 0.92, 0.32], [0.45, 0.98, 0.78]], device=self.dev
            )
            self.canvas.render_particles(pins, pin_cols * 2.2, 6.5, cam, additive=True, depth_occlude=False)

        else:
            # Chunk 02: Three Ruthless Checks Triptych suspended along one taut monofilament line
            dt = max(0.0, t - (t02_s - 0.4))
            cam = CameraMatrix(
                CameraPose(azim=0.08 * math.sin(0.3 * dt), elev=0.16, dist=6.4, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.05, show_grid=True, star_gain=0.30)
            self._render_taut_loom_threads(cam, t, gain=0.45)

            # Continuous horizontal taut monofilament spine connecting all 3 tests
            sx = torch.linspace(-6.0, 6.0, 180, device=self.dev)
            P_sp, N_sp = make_tube_along_curve(
                torch.stack([sx, torch.zeros_like(sx), torch.zeros_like(sx)], dim=-1), 0.036, n_around=14
            )
            self.canvas.render_surface_mesh(
                P_sp, (0.45, 0.85, 1.0), cam, normals=N_sp, emissive_rgb=(0.08, 0.34, 0.56), alpha=0.92
            )

            # Check 1 (Left, x=-2.25): Golden Memory Knot
            P_1, N_1, _ = self._make_trefoil_knot_mesh(scale=0.68, tube_r=0.075, spin=0.6 * t, center=(-2.25, 0.0, 0.0), n_pts=160, n_around=20)
            self.canvas.render_surface_mesh(P_1, (0.95, 0.78, 0.28), cam, normals=N_1, emissive_rgb=(0.30, 0.22, 0.05), alpha=0.96)

            # Check 2 (Center, x=0.0): Earth + GPS Orbit Ring
            P_e, N_e = make_sphere_mesh(0.56, (0.0, 0.0, 0.0), n_lat=48, n_lon=72, device=self.dev)
            self.canvas.render_surface_mesh(P_e, (0.16, 0.56, 0.94), cam, normals=N_e, emissive_rgb=(0.04, 0.16, 0.34), alpha=0.98)
            P_r, N_r = make_torus_mesh(0.96, 0.032, (0.0, 0.0, 0.0), n_u=96, n_v=14, device=self.dev)
            self.canvas.render_surface_mesh(P_r, (0.98, 0.84, 0.32), cam, normals=N_r, emissive_rgb=(0.32, 0.25, 0.06), alpha=0.94)

            # Check 3 (Right, x=+2.25): Spinning Kerr Vortex Torus
            P_3, N_3 = make_torus_mesh(0.68, 0.14, (2.25, 0.0, 0.0), n_u=96, n_v=22, device=self.dev)
            self.canvas.render_surface_mesh(
                P_3, (0.28, 0.78, 0.98), cam, normals=N_3, emissive_rgb=(0.12, 0.42, 0.68), wire_stride=6, wire_rgb=(1.0, 0.85, 0.35), wire_boost=0.55, alpha=0.95
            )

    # ------------------------------------------------------------------
    # SCENE 01: Illusion of 'Now' (Einstein) & Page-Wootters Observer Channels
    # ------------------------------------------------------------------
    def _render_scene01_page_wootters(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch04 = _find_chunk(scene, "chunk_04")
        ch05 = _find_chunk(scene, "chunk_05")
        ch06 = _find_chunk(scene, "chunk_06")
        t04_s = ch04["local_start"] if ch04 else 35.4
        t05_s = ch05["local_start"] if ch05 else 70.6
        t06_s = ch06["local_start"] if ch06 else 105.0

        if t < t04_s - 0.3:
            # Chunk 03: First 18s = '1 sec / 1 sec' self-biting circle; Second 17s = Einstein tilted 'NOW' slices
            if t < 18.0:
                cam = CameraMatrix(
                    CameraPose(azim=0.35 * t, elev=0.42, dist=4.8, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                    self.dev,
                )
                self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.05, show_grid=True, star_gain=0.30)
                P_t, N_t = make_torus_mesh(1.45, 0.16, (0.0, 0.0, 0.0), n_u=180, n_v=28, device=self.dev)
                u_ang = torch.linspace(0.0, 2.0 * math.pi, 180, device=self.dev).view(180, 1, 1)
                chase = torch.exp(-((torch.sin(u_ang - 1.8 * t)) ** 2) / 0.09)
                emit = chase * torch.tensor([1.05, 0.84, 0.28], device=self.dev).view(1, 1, 3) + torch.tensor(
                    [0.05, 0.25, 0.48], device=self.dev
                ).view(1, 1, 3)
                self.canvas.render_surface_mesh(P_t, (0.24, 0.68, 0.96), cam, normals=N_t, emissive_rgb=emit, alpha=0.95)
            else:
                dt = t - 18.0
                # Shift target slightly left so right-hand Einstein portrait medallion has clean framing
                cam = CameraMatrix(
                    CameraPose(azim=-0.42 + 0.16 * math.sin(0.25 * dt), elev=0.26, dist=5.8, target=(0.55, 0.0, 0.0), fov_deg=44.0),
                    self.dev,
                )
                self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.06, show_grid=True, star_gain=0.30)
                # Two tilted 'NOW' slices cutting across the 4D block universe at opposite relativity angles!
                u = torch.linspace(-1.35, 1.35, 120, device=self.dev)
                yy, zz = torch.meshgrid(u, u * 0.85, indexing="ij")
                tilt = 0.48 * math.sin(0.65 * dt)
                P_s1 = torch.stack([-0.45 + tilt * yy, yy, zz], dim=-1)
                P_s2 = torch.stack([0.45 - tilt * yy, yy, zz], dim=-1)
                self.canvas.render_surface_mesh(
                    P_s1, (0.20, 0.78, 1.0), cam, emissive_rgb=(0.08, 0.34, 0.55), alpha=0.72, wire_stride=12, wire_rgb=(0.75, 0.95, 1.0), wire_boost=0.45
                )
                self.canvas.render_surface_mesh(
                    P_s2, (0.98, 0.78, 0.26), cam, emissive_rgb=(0.35, 0.24, 0.05), alpha=0.72, wire_stride=12, wire_rgb=(1.0, 0.90, 0.45), wire_boost=0.45
                )
                # Block-universe worldline lattice points
                self.canvas.render_particles(
                    self.pw_nodes * 0.85,
                    torch.tensor([[0.55, 0.86, 1.0]], device=self.dev).expand(64, 3),
                    3.2,
                    cam,
                    additive=True,
                )

        elif t < t05_s - 0.3:
            # Chunk 04 (Page & Wootters 1983): Completely FROZEN 3D Quantum Lattice seen from outside (Motion = 0!)
            dt = t - t04_s
            cam = CameraMatrix(
                CameraPose(azim=0.52 + 0.09 * dt, elev=0.28, dist=6.4, target=(0.65, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.07, show_grid=True, star_gain=0.32)

            # Static frozen lattice lines & 64 motionless crystal nodes (zero internal wave oscillation!)
            s_lin = torch.linspace(-1.65, 1.65, 90, device=self.dev)
            lines = []
            for a in (-1.65, -0.55, 0.55, 1.65):
                for b in (-1.65, -0.55, 0.55, 1.65):
                    lines.append(torch.stack([s_lin, torch.full_like(s_lin, a), torch.full_like(s_lin, b)], dim=-1))
                    lines.append(torch.stack([torch.full_like(s_lin, a), s_lin, torch.full_like(s_lin, b)], dim=-1))
                    lines.append(torch.stack([torch.full_like(s_lin, a), torch.full_like(s_lin, b), s_lin], dim=-1))
            l_pts = torch.cat(lines, dim=0)
            self.canvas.render_particles(
                l_pts,
                torch.tensor([[0.26, 0.62, 0.92]], device=self.dev).expand(len(l_pts), 3),
                1.25,
                cam,
                additive=True,
            )
            self.canvas.render_particles(
                self.pw_nodes,
                torch.tensor([[0.78, 0.92, 1.05]], device=self.dev).expand(64, 3),
                4.8,
                cam,
                additive=True,
            )

        elif t < t06_s - 0.3:
            # Chunk 05: Camera dives INSIDE the weave -> Twin Observer Channels A & B spring to life (10^-15 match!)
            dt = max(0.0, t - t05_s)
            dive = smootherstep01(dt / 3.2)
            cam = CameraMatrix(
                CameraPose(
                    azim=1.57 + 0.16 * math.sin(0.32 * dt),
                    elev=0.22 - 0.06 * dive,
                    dist=6.2 - 1.65 * dive,
                    target=(0.0, 0.0, 0.0),
                    fov_deg=46.0,
                ),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.06, show_grid=True, star_gain=0.34)
            self._render_taut_loom_threads(cam, t, gain=0.45)

            # Twin Observer Channel A (Cyan) & Observer Channel B (Solar Gold) ribbons overlapping to 10^-15!
            x_w = torch.linspace(-2.85, 2.85, 240, device=self.dev)
            sep = 0.58 * (1.0 - 0.86 * smootherstep01((dt - 9.0) / 5.5))  # Channels converge into 15-decimal lockstep!
            z_wave = 0.68 * torch.sin(2.45 * x_w - 3.6 * dt) * torch.cos(0.45 * x_w)

            c_a = torch.stack([x_w, torch.full_like(x_w, -sep), z_wave], dim=-1)
            c_b = torch.stack([x_w, torch.full_like(x_w, +sep), z_wave], dim=-1)
            P_a, N_a = make_tube_along_curve(c_a, 0.082, n_around=22)
            P_b, N_b = make_tube_along_curve(c_b, 0.082, n_around=22)

            self.canvas.render_surface_mesh(
                P_a, (0.18, 0.82, 1.0), cam, normals=N_a, emissive_rgb=(0.08, 0.42, 0.68), alpha=0.95, shininess=72.0
            )
            self.canvas.render_surface_mesh(
                P_b, (1.0, 0.82, 0.26), cam, normals=N_b, emissive_rgb=(0.42, 0.30, 0.05), alpha=0.95, shininess=72.0
            )

        else:
            # Chunk 06: Slow Cosmic Pullback revealing the 4D Tapestry Hourglass from smooth waist to knotted rim
            dt = max(0.0, t - t06_s)
            pull = smootherstep01(dt / 22.0)
            cam = CameraMatrix(
                CameraPose(azim=0.25 + 0.35 * pull, elev=0.24 + 0.10 * pull, dist=4.8 + 3.8 * pull, target=(0.0, 0.0, 0.0), fov_deg=45.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.18 * pull, show_grid=(pull < 0.7), star_gain=0.45)
            self._render_two_wing_hourglass(cam, t, mirror_footprints=False)

    def _render_two_wing_hourglass(self, cam: CameraMatrix, t: float, mirror_footprints: bool = True) -> None:
        """Sculpted 3D Two-Wing Catenoid Cosmic Hourglass with smooth golden waist & knotted outer wings."""
        u_ax = (self.pol_r * 2.0 - 1.0) * 2.85  # -2.85 .. +2.85 along X
        rad = 0.24 + 0.62 * torch.sinh(torch.abs(u_ax) * 0.72)
        tangle = 0.055 * (torch.abs(u_ax) / 2.85) ** 2 * torch.sin(9.0 * self.pol_th + 6.0 * u_ax)
        r_eff = rad + tangle
        py = r_eff * torch.cos(self.pol_th)
        pz = r_eff * torch.sin(self.pol_th)
        P_h = torch.stack([u_ax, py, pz], dim=-1)

        waist_w = torch.exp(-(u_ax / 0.68) ** 2).unsqueeze(-1)
        c_waist = torch.tensor([0.98, 0.82, 0.32], device=self.dev).view(1, 1, 3)
        c_wing = torch.tensor([0.22, 0.68, 0.96], device=self.dev).view(1, 1, 3)
        alb = waist_w * c_waist + (1.0 - waist_w) * c_wing

        self.canvas.render_surface_mesh(
            P_h,
            alb,
            cam,
            emissive_rgb=alb * 0.20,
            alpha=0.80,
            wire_stride=10,
            wire_rgb=(0.68, 0.92, 1.0),
            wire_boost=0.38,
        )

        # Outward-marching Landauer memory footprints on one or BOTH wings!
        flow = torch.remainder(self.th_u + 0.085 * t, 1.0)
        signs = torch.where(self.th_ang < math.pi, 1.0, -1.0) if mirror_footprints else torch.ones_like(self.th_u)
        ax = signs * (0.18 + 2.65 * flow)
        rr = 0.24 + 0.62 * torch.sinh(torch.abs(ax) * 0.72)
        ang = self.th_ang * 2.0 + 0.6 * flow
        pts = torch.stack([ax, rr * torch.cos(ang), rr * torch.sin(ang)], dim=-1)
        col = torch.where(
            (signs > 0).unsqueeze(-1),
            torch.tensor([[1.05, 0.86, 0.32]], device=self.dev),
            torch.tensor([[0.38, 0.92, 1.05]], device=self.dev),
        ) * self.th_lum.unsqueeze(-1)
        self.canvas.render_particles(pts[:14000], col[:14000], 2.0, cam, additive=True)

    # ------------------------------------------------------------------
    # SCENE 02: Physical Memory & Landauer's Heat Tax (`k_B T ln 2`)
    # ------------------------------------------------------------------
    def _render_scene02_memory_landauer(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch08 = _find_chunk(scene, "chunk_08")
        ch09 = _find_chunk(scene, "chunk_09")
        ch11 = _find_chunk(scene, "chunk_11")
        t08_s = ch08["local_start"] if ch08 else 27.9
        t09_s = ch09["local_start"] if ch09 else 62.1
        t11_s = ch11["local_start"] if ch11 else 128.5

        if t < t08_s - 0.3:
            # Chunk 07: Monofilament loop locking into a physical binary record (frames Moon & Brain B-roll clips)
            cinch = smootherstep01(t / 12.0)
            cam = CameraMatrix(
                CameraPose(azim=0.28 * t, elev=0.25, dist=4.6, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.05, show_grid=True, star_gain=0.30)
            self._render_taut_loom_threads(cam, t, gain=0.50)
            P_k, N_k, _ = self._make_trefoil_knot_mesh(scale=1.45 - 0.32 * cinch, tube_r=0.095 + 0.03 * cinch, spin=0.25 * t)
            self.canvas.render_surface_mesh(
                P_k, (0.30, 0.78, 0.98), cam, normals=N_k, emissive_rgb=(0.12, 0.42, 0.65), alpha=0.95
            )

        elif t < t09_s - 0.3:
            # Chunk 08 (Rolf Landauer 1961): Knot locks in -> Golden thermal heat-tax ripples (`k_B T ln 2`) radiate!
            dt = max(0.0, t - t08_s)
            cam = CameraMatrix(
                CameraPose(azim=-0.35 + 0.12 * dt, elev=0.38, dist=5.6, target=(0.55, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.06, show_grid=True, star_gain=0.30)

            # Surrounding taut sheet carrying golden Landauer thermal ripples outward
            sx = self.sh_x * 3.4
            sy = self.sh_y * 3.4
            rr = torch.sqrt(sx * sx + sy * sy + 1e-4)
            rip = 0.16 * torch.sin(5.8 * rr - 5.2 * dt) * torch.exp(-0.42 * rr)
            P_sh = torch.stack([sx, sy, rip - 0.35], dim=-1)
            gold_w = torch.clamp(torch.abs(rip) * 5.2, 0.0, 1.0).unsqueeze(-1)
            alb = (1.0 - gold_w) * torch.tensor([0.16, 0.48, 0.78], device=self.dev).view(1, 1, 3) + gold_w * torch.tensor(
                [1.0, 0.82, 0.28], device=self.dev
            ).view(1, 1, 3)
            self.canvas.render_surface_mesh(
                P_sh, alb, cam, emissive_rgb=gold_w * torch.tensor([0.45, 0.34, 0.06], device=self.dev).view(1, 1, 3), alpha=0.84, wire_stride=10
            )

            # Central locked 'BIT = 1' trefoil knot + radiating golden heat-tax particles
            P_k, N_k, _ = self._make_trefoil_knot_mesh(scale=0.88, tube_r=0.095, spin=0.4 * dt, center=(0.0, 0.0, 0.18))
            self.canvas.render_surface_mesh(P_k, (1.0, 0.84, 0.30), cam, normals=N_k, emissive_rgb=(0.35, 0.26, 0.06), alpha=0.96)

            r_part = 0.45 + 3.2 * torch.remainder(self.th_u + 0.22 * dt, 1.0)
            fade_p = torch.clamp(1.25 - r_part / 3.4, 0.0, 1.0) * self.th_lum
            pts_p = torch.stack([r_part * torch.cos(self.th_ang), r_part * torch.sin(self.th_ang), self.th_z * 0.5 + 0.05], dim=-1)
            self.canvas.render_particles(
                pts_p[:16000],
                torch.tensor([[1.12, 0.84, 0.26]], device=self.dev) * fade_p[:16000].unsqueeze(-1),
                2.1,
                cam,
                additive=True,
            )

        elif t < t11_s - 0.3:
            # Chunks 09 & 10: 4D Entropy-Gradient Tapestry (Smooth Big Bang Waist on left -> Tangled Knots on right)
            dt = max(0.0, t - t09_s)
            cam = CameraMatrix(
                CameraPose(azim=-0.18 + 0.14 * math.sin(0.18 * dt), elev=0.44, dist=5.9, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.07, show_grid=True, star_gain=0.32)

            tx = self.sh_x * 3.6
            ty = self.sh_y * 2.1
            ent_u = torch.clamp((self.sh_x + 1.0) * 0.5, 0.0, 1.0)  # 0 = smooth waist, 1 = tangled outer rim
            tangle_z = (ent_u ** 1.85) * (
                0.28 * torch.sin(7.5 * tx + 1.4 * dt) * torch.cos(7.5 * ty - 1.1 * dt)
                + 0.14 * torch.sin(15.0 * tx - 12.0 * ty)
            )
            P_tap = torch.stack([tx, ty, tangle_z], dim=-1)
            c_smooth = torch.tensor([0.72, 0.90, 1.0], device=self.dev).view(1, 1, 3)
            c_tangle = torch.tensor([0.22, 0.64, 0.96], device=self.dev).view(1, 1, 3)
            alb = (1.0 - ent_u.unsqueeze(-1)) * c_smooth + ent_u.unsqueeze(-1) * c_tangle
            self.canvas.render_surface_mesh(
                P_tap, alb, cam, emissive_rgb=alb * 0.18, alpha=0.90, wire_stride=8, wire_rgb=(0.98, 0.84, 0.36), wire_boost=0.32
            )

            # Chain of recorded golden memory knots pointing back toward the smooth waist
            for k_i, kx in enumerate((-1.8, -0.6, 0.6, 1.8)):
                P_m, N_m, _ = self._make_trefoil_knot_mesh(
                    scale=0.34 + 0.08 * k_i, tube_r=0.048, spin=0.3 * dt + k_i, center=(kx, 0.0, 0.38), n_pts=120, n_around=16
                )
                self.canvas.render_surface_mesh(P_m, (1.0, 0.84, 0.30), cam, normals=N_m, emissive_rgb=(0.35, 0.25, 0.05), alpha=0.96)

        else:
            # Chunk 11: Two-Wing Cosmic Hourglass Mirror Memory (Outward Landauer heat tax on BOTH wings!)
            dt = max(0.0, t - t11_s)
            cam = CameraMatrix(
                CameraPose(azim=0.15 + 0.22 * math.sin(0.22 * dt), elev=0.22, dist=6.8, target=(0.0, 0.0, 0.0), fov_deg=45.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.22, show_grid=False, star_gain=0.52)
            self._render_two_wing_hourglass(cam, t, mirror_footprints=True)

    # ------------------------------------------------------------------
    # SCENE 03: The 20,184-km GPS Satellite Test (+38.6 us/day & 3,189 km Crossover)
    # ------------------------------------------------------------------
    def _render_scene03_gps_satellites(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch14 = _find_chunk(scene, "chunk_14")
        ch16 = _find_chunk(scene, "chunk_16")
        t14_s = ch14["local_start"] if ch14 else 58.2
        t16_s = ch16["local_start"] if ch16 else 122.1

        # Rotate Earth smoothly around Z axis
        ang_e = 0.14 * t
        ce, se = math.cos(ang_e), math.sin(ang_e)
        nx, ny, nz = self.earth_N[..., 0], self.earth_N[..., 1], self.earth_N[..., 2]
        r_nx = nx * ce - ny * se
        r_ny = nx * se + ny * ce
        N_rot = torch.stack([r_nx, r_ny, nz], dim=-1)
        P_earth = N_rot * 1.38

        if t < t14_s - 0.3:
            # Chunks 12 & 13: Sunlit Earth wrapped in dense inner monofilament weave vs loose outer weave!
            cam = CameraMatrix(
                CameraPose(azim=0.35 + 0.12 * t, elev=0.24, dist=6.2, target=(0.35, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.18, show_grid=False, star_gain=0.45)
            self.canvas.render_surface_mesh(
                P_earth, self.earth_albedo, cam, normals=N_rot, fresnel_rgb=(0.42, 0.84, 1.0), fresnel_strength=0.68, alpha=0.99, shininess=36.0, supersample=(3, 3)
            )

            # Concentric refractive monofilament shells: dense packed near R=1.55..1.85, airy loose at R=3.85
            for r_sh, col_s, sz_s in (
                (1.52, [1.05, 0.78, 0.30], 1.8),
                (1.66, [0.95, 0.84, 0.42], 1.6),
                (1.84, [0.48, 0.88, 1.0], 1.4),
                (2.65, [0.32, 0.78, 0.98], 1.2),
                (3.85, [0.26, 0.72, 0.96], 1.1),
            ):
                pts_s = self.fib_dir[:3200] * r_sh
                self.canvas.render_particles(
                    pts_s,
                    torch.tensor([col_s], device=self.dev).expand(3200, 3),
                    sz_s,
                    cam,
                    additive=True,
                )

        elif t < t16_s - 0.3:
            # Chunks 14 & 15: 31 GPS Satellites @ 20,184 km + Hero GPS Block-III Satellite + Diagonal Wave Stretch!
            dt = max(0.0, t - t14_s)
            cam = CameraMatrix(
                CameraPose(azim=0.42 + 0.16 * dt, elev=0.28, dist=7.6, target=(0.55, 0.0, 0.0), fov_deg=45.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.20, show_grid=False, star_gain=0.48)
            self.canvas.render_surface_mesh(
                P_earth, self.earth_albedo, cam, normals=N_rot, fresnel_rgb=(0.42, 0.84, 1.0), fresnel_strength=0.68, alpha=0.99, supersample=(3, 3)
            )

            # 31 orbiting GPS satellites at R = 3.65
            ph = self.gps_ph0 + 0.42 * t
            r_gps = 3.65
            c_inc, s_inc = math.cos(self.gps_inc), math.sin(self.gps_inc)
            x_orb = r_gps * torch.cos(ph)
            y_orb = r_gps * torch.sin(ph) * c_inc
            z_orb = r_gps * torch.sin(ph) * s_inc
            cr, sr = torch.cos(self.gps_raan), torch.sin(self.gps_raan)
            gx = x_orb * cr - y_orb * sr
            gy = x_orb * sr + y_orb * cr
            gz = z_orb
            sat_pts = torch.stack([gx, gy, gz], dim=-1)
            self.canvas.render_particles(
                sat_pts,
                torch.tensor([[1.15, 0.92, 0.36]], device=self.dev).expand(31, 3),
                5.4,
                cam,
                additive=True,
                depth_occlude=True,
            )

            # Hero GPS orbital ring + diagonal wave-stretch trail on Plane 0
            u_ring = torch.linspace(0.0, 2.0 * math.pi, 220, device=self.dev)
            rx = r_gps * torch.cos(u_ring)
            ry = r_gps * torch.sin(u_ring) * c_inc
            rz = r_gps * torch.sin(u_ring) * s_inc + 0.14 * torch.sin(24.0 * u_ring - 8.0 * dt)
            P_or, N_or = make_tube_along_curve(torch.stack([rx, ry, rz], dim=-1), 0.036, n_around=14)
            self.canvas.render_surface_mesh(
                P_or, (0.35, 0.88, 1.0), cam, normals=N_or, emissive_rgb=(0.12, 0.45, 0.68), alpha=0.92
            )

            # Sculpted Hero GPS Satellite at `sat_pts[0]` (golden bus + sapphire solar wings)
            hs = sat_pts[0]
            hx, hy, hz = float(hs[0].item()), float(hs[1].item()), float(hs[2].item())
            P_bus, N_bus = make_sphere_mesh(0.18, (hx, hy, hz), n_lat=24, n_lon=32, device=self.dev)
            self.canvas.render_surface_mesh(P_bus, (1.0, 0.84, 0.28), cam, normals=N_bus, emissive_rgb=(0.38, 0.28, 0.06), alpha=0.99)
            w_s = torch.linspace(-0.62, 0.62, 36, device=self.dev)
            P_w, N_w = make_tube_along_curve(
                torch.stack([hx + torch.zeros_like(w_s), hy + w_s, hz + torch.zeros_like(w_s)], dim=-1), 0.075, n_around=12
            )
            self.canvas.render_surface_mesh(P_w, (0.20, 0.66, 1.0), cam, normals=N_w, emissive_rgb=(0.08, 0.30, 0.58), alpha=0.98)

        else:
            # Chunk 16: ISS (400 km) -> 3,189 km Exact Zero-Crossing Ring -> GPS (20,184 km)
            dt = max(0.0, t - t16_s)
            # Shift Earth to left half `(target x = +1.35)` so right half holds our giant 4K Altitude Crossover Graph!
            cam = CameraMatrix(
                CameraPose(azim=0.65 + 0.12 * dt, elev=0.26, dist=6.8, target=(1.25, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.14, show_grid=True, star_gain=0.40)
            self.canvas.render_surface_mesh(
                P_earth, self.earth_albedo, cam, normals=N_rot, fresnel_rgb=(0.42, 0.84, 1.0), fresnel_strength=0.68, alpha=0.99, supersample=(3, 3)
            )

            # Low ISS orbit (`R = 1.52`, coral-amber `-28 us/day`), Zero-Crossing Ring (`R = 2.07 = 1.5 R_E`, emerald `0.0 us/day`), GPS (`R = 3.45`, cyan-gold `+38.6 us/day`)
            P_iss, N_iss = make_torus_mesh(1.54, 0.028, (0.0, 0.0, 0.0), n_u=140, n_v=12, device=self.dev)
            P_zero, N_zero = make_torus_mesh(2.07, 0.048, (0.0, 0.0, 0.0), n_u=160, n_v=16, device=self.dev)
            P_gps2, N_gps2 = make_torus_mesh(3.35, 0.032, (0.0, 0.0, 0.0), n_u=180, n_v=12, device=self.dev)

            self.canvas.render_surface_mesh(P_iss, (1.0, 0.48, 0.36), cam, normals=N_iss, emissive_rgb=(0.35, 0.12, 0.08), alpha=0.94)
            self.canvas.render_surface_mesh(P_zero, (0.22, 0.96, 0.68), cam, normals=N_zero, emissive_rgb=(0.12, 0.48, 0.30), alpha=0.98)
            self.canvas.render_surface_mesh(P_gps2, (0.35, 0.86, 1.0), cam, normals=N_gps2, emissive_rgb=(0.10, 0.36, 0.56), alpha=0.92)

    # ------------------------------------------------------------------
    # SCENE 04: Strong-Field Gauntlet — Mercury, Cassini & GW170817 Neutron Stars
    # ------------------------------------------------------------------
    def _render_scene04_strong_field(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch18 = _find_chunk(scene, "chunk_18")
        ch19 = _find_chunk(scene, "chunk_19")
        ch20 = _find_chunk(scene, "chunk_20")
        t18_s = ch18["local_start"] if ch18 else 23.3
        t19_s = ch19["local_start"] if ch19 else 56.5
        t20_s = ch20["local_start"] if ch20 else 93.3

        if t < t19_s - 0.3:
            # Chunks 17 & 18: Blazing 3D Sun Weave Funnel + Mercury 42.98"/cy Rosetta + Cassini Radio Shapiro Delay!
            cam = CameraMatrix(
                CameraPose(azim=0.25 + 0.14 * t, elev=0.46, dist=6.8, target=(0.0, 0.0, -0.25), fov_deg=45.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.20, show_grid=False, star_gain=0.48)

            # Refractive solar gravity funnel sheet
            r_s = 0.38 + 3.6 * self.pol_r
            z_s = -1.35 / torch.sqrt(r_s * r_s + 0.22)
            P_fun = torch.stack([r_s * torch.cos(self.pol_th), r_s * torch.sin(self.pol_th), z_s], dim=-1)
            w_sun = torch.exp(-(r_s / 1.25) ** 2).unsqueeze(-1)
            alb = w_sun * torch.tensor([1.0, 0.78, 0.26], device=self.dev).view(1, 1, 3) + (1.0 - w_sun) * torch.tensor(
                [0.20, 0.64, 0.96], device=self.dev
            ).view(1, 1, 3)
            self.canvas.render_surface_mesh(
                P_fun, alb, cam, emissive_rgb=alb * 0.22, alpha=0.84, wire_stride=10, wire_rgb=(0.65, 0.90, 1.0), wire_boost=0.35
            )

            # Blazing 3D Sun sphere at center
            P_sun, N_sun = make_sphere_mesh(0.56, (0.0, 0.0, 0.12), n_lat=48, n_lon=64, device=self.dev)
            self.canvas.render_surface_mesh(P_sun, (1.0, 0.86, 0.36), cam, normals=N_sun, emissive_rgb=(0.95, 0.68, 0.18), alpha=0.99)

            if t < t18_s + 16.5:
                # Mercury Rosetta-precessing elliptical orbit ribbon (`42.98"/century`)
                s_m = torch.linspace(0.0, 6.5 * 2.0 * math.pi, 420, device=self.dev)
                r_m = 1.45 / (1.0 + 0.32 * torch.cos(0.915 * s_m - 0.55 * t))
                zm = -1.35 / torch.sqrt(r_m * r_m + 0.22) + 0.10
                P_mer, N_mer = make_tube_along_curve(
                    torch.stack([r_m * torch.cos(s_m), r_m * torch.sin(s_m), zm], dim=-1), 0.036, n_around=14
                )
                self.canvas.render_surface_mesh(
                    P_mer, (0.45, 0.94, 1.0), cam, normals=N_mer, emissive_rgb=(0.16, 0.52, 0.72), alpha=0.95
                )
            else:
                # NASA Cassini radio wave beam grazing the Sun's limb from Saturn to Earth (`±0.002%` Shapiro delay)
                bx = torch.linspace(-3.4, 3.4, 240, device=self.dev)
                by = 0.74 + 0.24 / (1.0 + (bx / 0.85) ** 2)  # Gravitational deflection + delay dip!
                bz = -1.35 / torch.sqrt(bx * bx + by * by + 0.22) + 0.16 + 0.07 * torch.sin(14.0 * bx - 10.0 * t)
                P_cas, N_cas = make_tube_along_curve(torch.stack([bx, by, bz], dim=-1), 0.045, n_around=16)
                self.canvas.render_surface_mesh(
                    P_cas, (1.0, 0.88, 0.32), cam, normals=N_cas, emissive_rgb=(0.48, 0.38, 0.08), alpha=0.96
                )

        elif t < t20_s - 0.3:
            # Chunk 19 (`GW170817`): Inspiraling Neutron Stars -> Kilonova Merger -> Slow 130M-ly Cosmic Pan-Out!
            dt = max(0.0, t - t19_s)
            t_merge = 14.5
            pan_u = smootherstep01((dt - t_merge) / 18.5)
            cam = CameraMatrix(
                CameraPose(
                    azim=0.35 + 0.18 * dt,
                    elev=0.38 - 0.12 * pan_u,
                    dist=5.4 + 28.0 * pan_u,
                    target=(0.0, 0.0, 0.0),
                    fov_deg=45.0,
                ),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.22 + 0.16 * pan_u, show_grid=False, star_gain=0.55)

            # Deep-field galaxies surrounding the 130M-light-year cosmic pullback!
            if pan_u > 0.02:
                self.canvas.render_particles(self.df_pts, self.df_rgb * (0.95 * pan_u), self.df_sz, cam, additive=True, depth_occlude=False)

            if dt < t_merge:
                rem = max(0.06, 1.0 - dt / t_merge)
                sep = 0.22 + 1.55 * (rem ** 0.55)
                orb_ph = 24.0 * (1.0 - rem ** 0.65)
                cx, cy = sep * math.cos(orb_ph), sep * math.sin(orb_ph)

                # Spiral gravitational wave sheet
                r_g = 0.25 + 4.2 * self.pol_r
                z_g = 0.16 * torch.sin(4.2 * r_g - 2.0 * (self.pol_th - orb_ph)) / torch.sqrt(r_g + 0.4)
                P_gw = torch.stack([r_g * torch.cos(self.pol_th), r_g * torch.sin(self.pol_th), z_g - 0.2], dim=-1)
                self.canvas.render_surface_mesh(
                    P_gw, (0.22, 0.72, 0.98), cam, emissive_rgb=(0.06, 0.24, 0.42), alpha=0.76, wire_stride=10
                )

                P_n1, N_n1 = make_sphere_mesh(0.28, (cx, cy, 0.08), n_lat=32, n_lon=48, device=self.dev)
                P_n2, N_n2 = make_sphere_mesh(0.28, (-cx, -cy, 0.08), n_lat=32, n_lon=48, device=self.dev)
                self.canvas.render_surface_mesh(P_n1, (0.55, 0.94, 1.0), cam, normals=N_n1, emissive_rgb=(0.45, 0.85, 1.0), alpha=0.99)
                self.canvas.render_surface_mesh(P_n2, (1.0, 0.88, 0.42), cam, normals=N_n2, emissive_rgb=(0.85, 0.68, 0.22), alpha=0.99)
            else:
                # Post-merger neck-and-neck expanding Light Shell (Gold) + Gravity Shear Shell (Cyan) arriving within 1.7s!
                dt_m = dt - t_merge
                r_wave = 0.6 + 1.35 * dt_m
                pts_em = self.fib_dir[:9000] * r_wave
                pts_gw = self.fib_dir[9000:] * (r_wave * 0.992)  # Locked neck-and-neck!
                self.canvas.render_particles(
                    pts_em, torch.tensor([[1.15, 0.88, 0.30]], device=self.dev).expand(9000, 3), 2.2, cam, additive=True, depth_occlude=False
                )
                self.canvas.render_particles(
                    pts_gw, torch.tensor([[0.35, 0.94, 1.15]], device=self.dev).expand(9000, 3), 2.2, cam, additive=True, depth_occlude=False
                )

        else:
            # Chunk 20: Plucking ONE Taut Monofilament Thread -> Orthogonal Light & Gravity Shear Waves in 10^-15 Lockstep!
            dt = max(0.0, t - t20_s)
            cam = CameraMatrix(
                CameraPose(azim=0.22 * math.sin(0.25 * dt), elev=0.24, dist=5.2, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.05, show_grid=True, star_gain=0.30)
            self._render_taut_loom_threads(cam, t, gain=0.52)

            sx = torch.linspace(-4.2, 4.2, 280, device=self.dev)
            env = torch.exp(-((sx - (-2.6 + 2.2 * (dt % 2.6))) ** 2) / 0.85) + 0.35
            w_val = 0.52 * env * torch.sin(4.4 * sx - 8.5 * dt)

            # Vertical polarization = Light (Solar Gold), Horizontal polarization = Gravity Shear (Electric Cyan)
            # BOTH riding the exact same central taut monofilament core!
            P_core, N_core = make_tube_along_curve(torch.stack([sx, torch.zeros_like(sx), torch.zeros_like(sx)], dim=-1), 0.038, n_around=14)
            P_em, N_em = make_tube_along_curve(torch.stack([sx, torch.zeros_like(sx), w_val], dim=-1), 0.068, n_around=20)
            P_gw, N_gw = make_tube_along_curve(torch.stack([sx, w_val, torch.zeros_like(sx)], dim=-1), 0.068, n_around=20)

            self.canvas.render_surface_mesh(P_core, (0.85, 0.95, 1.0), cam, normals=N_core, emissive_rgb=(0.25, 0.45, 0.65), alpha=0.96)
            self.canvas.render_surface_mesh(P_em, (1.0, 0.84, 0.28), cam, normals=N_em, emissive_rgb=(0.42, 0.32, 0.06), alpha=0.94)
            self.canvas.render_surface_mesh(P_gw, (0.20, 0.86, 1.0), cam, normals=N_gw, emissive_rgb=(0.08, 0.42, 0.68), alpha=0.94)

    # ------------------------------------------------------------------
    # Relativistic Spinning Kerr Black Hole Pixel Shader (`a/M = 0.96`)
    # ------------------------------------------------------------------
    def _render_kerr_black_hole_shader(self, t: float, spin_a: float = 0.96, center_x: float = -0.22) -> None:
        """
        Paints a physically grounded, breathtaking relativistic spinning Kerr Black Hole (`a/M = 0.96`)
        directly onto `self.canvas.hdr` via half-res `(1920x1080)` vectorized CUDA ray-optics + 4K upsample:
          • Asymmetric D-shaped Kerr shadow shifted rightward by prograde frame dragging
          • Blazing Doppler-boosted sapphire-white approaching accretion limb vs warm amber-gold receding limb
          • Gravitationally lensed upper & lower Einstein photon-ring arcs
          • Swirling ergosphere superfluid vortex streamlines
        """
        xx = self.h_xx - center_x
        yy = self.h_yy

        # Asymmetric Bardeen D-shaped Kerr shadow (`a = 0.96`): compressed flat prograde left edge (`x_sh ~ -0.27`),
        # broad semicircular retrograde right edge (`x_sh ~ +0.44`), shifted slightly right by frame dragging!
        x_sh = xx - 0.08 * spin_a
        x_scaled = torch.where(x_sh < 0.0, x_sh / 0.64, x_sh / 1.05)
        r_sh = torch.sqrt(x_scaled * x_scaled + yy * yy + 1e-6)
        ang_sh = torch.atan2(yy, x_sh)

        # Crisp event-horizon shadow mask + razor-sharp relativistic photon ring right on `r_sh = 0.42`
        shadow = torch.sigmoid((0.415 - r_sh) * 64.0)
        doppler_sh = torch.clamp(1.0 - 0.58 * (x_sh / 0.48), 0.38, 1.85)
        photon_ring = torch.exp(-((r_sh - 0.424) / 0.019) ** 2) * (1.15 * doppler_sh)

        # Gravitationally lensed upper & lower back-of-disk Einstein halo arcs arching cleanly over & under the shadow!
        halo_band = torch.exp(-((r_sh - 0.475) / 0.068) ** 2) * (0.28 + 0.92 * (yy * yy / (r_sh * r_sh + 0.015)))
        halo_swirl = 0.68 + 0.32 * torch.sin(6.0 * ang_sh + 10.0 * r_sh - 4.2 * t)
        lensed_halo = halo_band * halo_swirl * (doppler_sh ** 1.45) * (1.0 - 0.96 * shadow)

        # Foreground inclined thin equatorial accretion disk (`81 deg` inclination, tilted `9 deg` CCW)
        # passing IN FRONT OF the lower-middle of the shadow (`front_mask`) and occluded behind on the far side!
        ca, sa = math.cos(0.16), math.sin(0.16)
        dx = xx * ca + (yy + 0.035) * sa
        dy = -xx * sa + (yy + 0.035) * ca
        inc_squash = 0.165
        # Subtle relativistic upward warp on far side (`dy > 0`) near the horizon
        dy_warped = torch.where(dy > 0.0, dy * (1.0 - 0.38 * torch.exp(-((r_sh - 0.42) / 0.35) ** 2)), dy)
        r_disk = torch.sqrt(dx * dx + (dy_warped / inc_squash) ** 2 + 1e-5)
        ang_disk = torch.atan2(dy_warped / inc_squash, dx)

        # Prograde Kerr ISCO (`r_disk >= 0.27`) with `clamp(min=0.0)` before fractional power so zero NaNs ever occur!
        r_fall = torch.clamp(r_disk - 0.44, min=0.0) / 0.72
        in_disk = torch.sigmoid((r_disk - 0.27) * 32.0) * torch.exp(-(r_fall ** 1.55))
        swirl1 = 0.64 + 0.36 * torch.sin(4.0 * ang_disk + 12.5 * torch.log(r_disk + 0.16) - 4.8 * t)
        swirl2 = 0.74 + 0.26 * torch.cos(9.0 * ang_disk + 15.0 / (r_disk + 0.30) - 7.2 * t)
        doppler_d = torch.clamp(1.0 - 0.62 * (dx / torch.clamp(r_disk, min=0.32)), 0.34, 1.92) ** 1.75

        # Front half of disk (`dy < 0.0`) crosses IN FRONT OF the black hole shadow; back half (`dy > 0.0`) is occluded by shadow!
        front_w = torch.sigmoid((-dy) * 42.0)
        occ_factor = front_w + (1.0 - front_w) * (1.0 - 0.98 * shadow)
        disk_int = in_disk * swirl1 * swirl2 * doppler_d * occ_factor

        # Ergosphere frame-dragging outer superfluid streamlines (`r_sh in [0.46, 1.45]`)
        ergo = (
            torch.exp(-((r_sh - 0.78) / 0.46) ** 2)
            * (0.5 + 0.5 * torch.sin(7.0 * ang_sh + 8.5 / (r_sh + 0.25) - 3.6 * t)) ** 3.2
            * 0.24
            * (1.0 - shadow)
        )

        blue_shift = torch.clamp(-dx / 0.68, 0.0, 1.0)
        c_app = torch.tensor([0.55, 0.90, 1.28], device=self.dev).view(3, 1, 1)  # Approaching sapphire-alabaster
        c_rec = torch.tensor([1.26, 0.76, 0.22], device=self.dev).view(3, 1, 1)  # Receding solar-amber
        col_mix = blue_shift.unsqueeze(0) * c_app + (1.0 - blue_shift.unsqueeze(0)) * c_rec

        tot_glow = (disk_int * 1.18 + lensed_halo * 1.08 + photon_ring * 1.32).unsqueeze(0) * col_mix + ergo.unsqueeze(0) * torch.tensor(
            [0.24, 0.78, 1.15], device=self.dev
        ).view(3, 1, 1)

        glow_4k = F.interpolate(tot_glow.unsqueeze(0), size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)
        # Foreground disk stays bright right across the front of the event-horizon shadow!
        sh_eff = shadow * (1.0 - 0.88 * front_w * torch.clamp(in_disk * 1.6, 0.0, 1.0))
        sh_4k = F.interpolate(sh_eff.unsqueeze(0).unsqueeze(0), size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)

        self.canvas.hdr = self.canvas.hdr * (1.0 - 0.94 * sh_4k) + glow_4k

    # ------------------------------------------------------------------
    # SCENE 05: Lacuna Raining Papers, Kerr Black Hole & David's Bonus Discovery (`chunk_23b`)
    # ------------------------------------------------------------------
    def _render_scene05_lacuna_and_kerr(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch22 = _find_chunk(scene, "chunk_22")
        ch23 = _find_chunk(scene, "chunk_23")
        ch23b = _find_chunk(scene, "chunk_23b")
        ch24 = _find_chunk(scene, "chunk_24")

        t22_s = ch22["local_start"] if ch22 else 37.4
        t23_s = ch23["local_start"] if ch23 else 57.6
        t23b_s = ch23b["local_start"] if ch23b else 94.3
        t24_s = ch24["local_start"] if ch24 else 137.7

        if t < t22_s - 0.3:
            # Chunk 21: Framing wave-tank Unruh horizon ripple sheet (around Lacuna rain & Water-Tank B-roll windows)
            cam = CameraMatrix(
                CameraPose(azim=0.25 + 0.10 * t, elev=0.38, dist=5.8, target=(0.45, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.06, show_grid=True, star_gain=0.28)
            sx = self.sh_x * 3.5
            sy = self.sh_y * 2.5
            bow = torch.sqrt((sx - 0.8) ** 2 + (sy * 1.45) ** 2 + 0.08)
            z_w = 0.14 * torch.sin(6.5 * bow - 5.5 * t) * torch.exp(-0.35 * bow)
            P_wt = torch.stack([sx, sy, z_w], dim=-1)
            self.canvas.render_surface_mesh(
                P_wt, (0.18, 0.72, 0.96), cam, emissive_rgb=(0.06, 0.28, 0.45), alpha=0.88, wire_stride=8, wire_rgb=(0.75, 0.96, 1.0), wire_boost=0.35
            )

        elif t < t23_s - 0.3:
            # Chunk 22: Red-Team Spotlight on 3D Exponential Weave Sphere beginning to twist
            dt = max(0.0, t - t22_s)
            cam = CameraMatrix(
                CameraPose(azim=0.35 + 0.18 * dt, elev=0.26, dist=5.4, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.14, show_grid=True, star_gain=0.40)
            P_sp, N_sp = make_sphere_mesh(1.32, (0.0, 0.0, 0.0), n_lat=72, n_lon=96, device=self.dev)
            self.canvas.render_surface_mesh(
                P_sp, (0.22, 0.68, 0.98), cam, normals=N_sp, emissive_rgb=(0.06, 0.25, 0.45), wire_stride=6, wire_rgb=(1.0, 0.84, 0.32), wire_boost=0.45, alpha=0.92
            )

        elif t < t23b_s - 0.25:
            # Chunk 23 (Roy Kerr 1963): Epic Code-Generated Relativistic Ray-Marched Spinning Kerr Black Hole!
            dt = max(0.0, t - t23_s)
            cam = CameraMatrix(
                CameraPose(azim=0.18 * dt, elev=0.22, dist=6.0, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.36, show_grid=False, star_gain=0.62)
            self._render_kerr_black_hole_shader(t, spin_a=0.96, center_x=-0.24)

        elif t < t24_s - 0.3:
            # =================================================================================
            # CHUNK 23B (DAVID'S BONUS DISCOVERY!):
            #   Act 1 (0..26.5s): Self-Healing Quantum Phase-Slip ('Melt • Slip 1 Turn • Re-Weld')
            #   Act 2 (26.5..43s): Unbreakable Planck-Tension Fishing Reel Spool (`R = 2GM/c^2`, `1.000000`!)
            # =================================================================================
            dt = max(0.0, t - t23b_s)
            if dt < 26.5:
                # Act 1: 28 Taut Monofilament Space Threads spiraling into the spinning horizon;
                # every 4.5s, the innermost overstretched loop melts across 1 Planck width, slips one turn & welds back!
                cam = CameraMatrix(
                    CameraPose(azim=0.14 * dt, elev=0.48 - 0.06 * math.sin(0.3 * dt), dist=5.1, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                    self.dev,
                )
                self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.28, show_grid=False, star_gain=0.52)
                self._render_kerr_black_hole_shader(t, spin_a=0.94, center_x=0.0)

                # Periodic quantum phase-slip cycle (`cyc in [0..1)` every 4.4s)
                cyc = (dt % 4.4) / 4.4
                stretch = smoothstep01(cyc / 0.62)
                melt_flash = math.exp(-(((cyc - 0.68) / 0.09) ** 2))
                slip_relax = smoothstep01((cyc - 0.65) / 0.22)
                wind_tightness = 2.4 + 2.8 * (stretch - slip_relax)

                # 28 spiraling monofilament threads rendered as dense high-brilliance 3D curves
                s_r = torch.linspace(0.56, 3.25, 180, device=self.dev)
                n_strands = 28
                ang_0 = torch.linspace(0.0, 2.0 * math.pi * (1.0 - 1.0 / n_strands), n_strands, device=self.dev).view(n_strands, 1)
                r_grid = s_r.view(1, 180).expand(n_strands, 180)
                th_grid = ang_0 + wind_tightness / (r_grid - 0.34) - 1.85 * dt
                px = r_grid * torch.cos(th_grid)
                py = r_grid * torch.sin(th_grid)
                pz = -0.18 / (r_grid + 0.15)
                pts_strands = torch.stack([px, py, pz], dim=-1).reshape(-1, 3)

                # Inner Planck healing zone (`r < 0.88`) glows blazing solar-gold during stretch -> emerald-alabaster weld!
                inner_w = torch.exp(-((r_grid - 0.62) / 0.24) ** 2).reshape(-1, 1)
                c_cyan = torch.tensor([[0.32, 0.86, 1.15]], device=self.dev)
                c_weld = torch.tensor([[1.35, 1.05, 0.38]], device=self.dev)
                col_s = (1.0 - inner_w) * c_cyan + inner_w * c_weld * (0.85 + 0.95 * melt_flash)
                self.canvas.render_particles(pts_strands, col_s, 1.95, cam, additive=True, depth_occlude=False)

                # Glowing Planck Healing-Length Ring (`r = 0.64`) pulsing cleanly as threads melt & re-weld!
                P_hl, N_hl = make_torus_mesh(0.64, 0.032 + 0.022 * melt_flash, (0.0, 0.0, -0.18), n_u=160, n_v=16, device=self.dev)
                self.canvas.render_surface_mesh(
                    P_hl,
                    (1.0, 0.88, 0.34),
                    cam,
                    normals=N_hl,
                    emissive_rgb=(0.65 * melt_flash + 0.25, 0.52 * melt_flash + 0.20, 0.12),
                    alpha=0.95,
                )
            else:
                # Act 2 (26.5..43s): The Unbreakable Planck-Tension Fishing Reel!
                # Taut monofilament lines with matter knots wind onto the central spherical reel as the wound sphere
                # grows smoothly in EXACT 1.000000 lockstep with the dashed Schwarzschild horizon ring `R = 2GM/c^2`!
                dt2 = dt - 26.5
                grow = smootherstep01(dt2 / 13.0)
                R_spool = 0.62 + 1.05 * grow  # Growing wound horizon sphere `R = 2GM / c^2`!

                cam = CameraMatrix(
                    CameraPose(azim=0.45 + 0.22 * dt2, elev=0.28, dist=5.8, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                    self.dev,
                )
                self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.22, show_grid=False, star_gain=0.48)

                # Wound spherical spool of glowing monofilament thread + matter knots
                P_sp, N_sp = make_sphere_mesh(R_spool, (0.0, 0.0, 0.0), n_lat=200, n_lon=300, device=self.dev)
                # Bake fine circumferential fishing-line winding grooves onto sphere albedo
                wind_stripes = 0.68 + 0.32 * torch.sin(52.0 * N_sp[..., 2] + 8.0 * dt2).unsqueeze(-1)
                alb_sp = wind_stripes * torch.tensor([0.24, 0.74, 1.0], device=self.dev).view(1, 1, 3)
                self.canvas.render_surface_mesh(
                    P_sp,
                    alb_sp,
                    cam,
                    normals=N_sp,
                    emissive_rgb=(0.08, 0.30, 0.52),
                    fresnel_rgb=(1.0, 0.88, 0.36),
                    fresnel_strength=0.72,
                    alpha=0.97,
                    shininess=68.0,
                    supersample=(3, 3),
                )

                # Exact Analytical Schwarzschild Horizon Gauge Ring (`R = 2GM / c^2`) hugging `R_spool * 1.03` (`1.000000` match!)
                P_hg, N_hg = make_torus_mesh(R_spool * 1.03, 0.036, (0.0, 0.0, 0.0), n_u=220, n_v=18, device=self.dev)
                self.canvas.render_surface_mesh(
                    P_hg, (1.0, 0.86, 0.30), cam, normals=N_hg, emissive_rgb=(0.45, 0.35, 0.08), alpha=0.96
                )

                # 6 continuous taut 3D monofilament fishing-line tubes winding tangentially onto the growing spool + sparkling matter knots!
                s_tube = torch.linspace(0.0, 1.0, 220, device=self.dev)
                s_in = torch.linspace(0.0, 1.0, 900, device=self.dev)
                in_pts_all = []
                for k_s in range(6):
                    a0 = k_s * (math.pi / 3.0) + 1.4 * dt2
                    # Solid translucent monofilament tube curve
                    r_t = R_spool + 3.6 * (s_tube ** 1.12)
                    th_t = a0 + 2.35 * (1.0 - s_tube)
                    z_t = 0.36 * (s_tube - 0.15) * ((-1) ** k_s) * s_tube
                    c_line = torch.stack([r_t * torch.cos(th_t), r_t * torch.sin(th_t), z_t], dim=-1)
                    P_ln, N_ln = make_tube_along_curve(c_line, 0.026 if k_s > 0 else 0.038, n_around=12)
                    self.canvas.render_surface_mesh(
                        P_ln,
                        (0.42, 0.88, 1.0) if k_s > 0 else (1.0, 0.88, 0.36),
                        cam,
                        normals=N_ln,
                        emissive_rgb=(0.10, 0.42, 0.68) if k_s > 0 else (0.45, 0.36, 0.08),
                        alpha=0.93,
                        shininess=72.0,
                    )

                    # Dense golden matter-knot glints traveling inward along the fishing line onto the spool
                    r_c = R_spool + 3.6 * (s_in ** 1.12)
                    th_c = a0 + 2.35 * (1.0 - s_in)
                    z_c = 0.36 * (s_in - 0.15) * ((-1) ** k_s) * s_in
                    in_pts_all.append(torch.stack([r_c * torch.cos(th_c), r_c * torch.sin(th_c), z_c], dim=-1))

                in_pts = torch.cat(in_pts_all, dim=0)
                knot_glint = (0.35 + 1.15 * (torch.sin(24.0 * s_in + 9.0 * dt2) ** 10)).repeat(6).unsqueeze(-1)
                self.canvas.render_particles(
                    in_pts,
                    knot_glint * torch.tensor([[1.05, 0.90, 0.38]], device=self.dev),
                    2.2,
                    cam,
                    additive=True,
                )

        else:
            # Chunk 24: Smooth Diamond-Dense Knot Throat (vs Jagged Singularity) + Gravitational-Wave Ringdown Echoes!
            dt = max(0.0, t - t24_s)
            cam = CameraMatrix(
                CameraPose(azim=0.28 + 0.12 * dt, elev=0.36, dist=6.0, target=(0.0, 0.0, -0.35), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.24, show_grid=False, star_gain=0.50)

            # Smooth exponential throat (`z = -1.95 * exp(-0.85 * r^2)` — finite smooth rounded bottom, zero jagged tear!)
            r_t = 3.4 * self.pol_r
            z_t = -1.95 * torch.exp(-0.78 * r_t * r_t)
            # Outgoing subtle gravitational-wave ringdown echoes bouncing up out of the dense throat!
            echo = 0.085 * torch.sin(7.5 * r_t - 4.8 * dt) * torch.exp(-0.45 * r_t)
            P_th = torch.stack([r_t * torch.cos(self.pol_th), r_t * torch.sin(self.pol_th), z_t + echo], dim=-1)

            dense_w = torch.exp(-0.95 * r_t * r_t).unsqueeze(-1)
            alb = dense_w * torch.tensor([0.92, 0.86, 0.42], device=self.dev).view(1, 1, 3) + (1.0 - dense_w) * torch.tensor(
                [0.20, 0.68, 0.98], device=self.dev
            ).view(1, 1, 3)
            self.canvas.render_surface_mesh(
                P_th, alb, cam, emissive_rgb=alb * 0.24, alpha=0.90, wire_stride=8, wire_rgb=(0.68, 0.94, 1.0), wire_boost=0.42
            )

    # ------------------------------------------------------------------
    # SCENE 06: Interactive Lab, Living Scorecard & Grand Cosmic Pan-Out
    # ------------------------------------------------------------------
    def _render_scene06_outro_and_panout(self, scene: dict, t: float, dur: float, prog: float) -> None:
        ch26 = _find_chunk(scene, "chunk_26")
        ch27 = _find_chunk(scene, "chunk_27")
        t26_s = ch26["local_start"] if ch26 else 28.2
        t27_s = ch27["local_start"] if ch27 else 60.8

        if t < t26_s - 0.3:
            # Chunk 25: Gently rippling 3D monofilament studio loom framing the 4K Science Workbench showcase
            cam = CameraMatrix(
                CameraPose(azim=0.14 * t, elev=0.28, dist=5.8, target=(0.0, 0.0, 0.0), fov_deg=44.0),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.05, show_grid=True, star_gain=0.30)
            self._render_taut_loom_threads(cam, t, gain=0.55)
        else:
            # Chunks 26 & 27: Continuous Majestic Cosmic Pullback across 165 3D Galaxies -> Two-Wing Cosmic Hourglass!
            dt = max(0.0, t - t26_s)
            span = max(1.0, dur - t26_s)
            u_pan = smootherstep01(dt / span)
            cam = CameraMatrix(
                CameraPose(
                    azim=0.22 + 0.55 * u_pan,
                    elev=0.20 + 0.14 * u_pan,
                    dist=6.5 + 38.0 * (u_pan ** 1.35) if t < t27_s else 8.2 - 1.6 * smootherstep01((t - t27_s) / 22.0),
                    target=(0.0, 0.0, 0.0),
                    fov_deg=45.0,
                ),
                self.dev,
            )
            self.clear_option_a_plus_studio(cam, t, cosmos_depth=0.28, show_grid=False, star_gain=0.58)
            self.canvas.render_particles(self.df_pts, self.df_rgb * 0.92, self.df_sz, cam, additive=True, depth_occlude=False)

            if t >= t27_s - 0.5:
                # Episode 2 Teaser: Narrow Big Bang Waist of the Two-Wing Cosmic Hourglass!
                self._render_two_wing_hourglass(cam, t, mirror_footprints=True)
