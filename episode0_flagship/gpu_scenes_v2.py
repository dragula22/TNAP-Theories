"""
All 11 High-Detail, Dynamically Filmed 3D Scenes (`hook00` + `scene00`..`scene09`)
for Flagship Episode 0 v2 (`1920x1080` RTX 5080 CUDA Edition).
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F

from gpu_renderer_core import (
    CameraMatrix,
    CameraPose,
    GPUCanvas1080p,
    interpolate_camera,
    make_sphere_mesh,
    make_torus_mesh,
    make_tube_along_curve,
    smootherstep01,
    smoothstep01,
)


class GPU3DSceneDirector:
    """Holds precomputed GPU particle/grid buffers and renders any Episode 0 v2 scene at `1920x1080`."""

    def __init__(self, device: torch.device | None = None):
        self.canvas = GPUCanvas1080p(device=device)
        self.dev = self.canvas.device

        # Shared high-density UV grids (340 x 340 = 115,600 shaded facets -> ~462,000 sub-splats)
        u1 = torch.linspace(-1.0, 1.0, 340, device=self.dev)
        self.grid_x, self.grid_y = torch.meshgrid(u1, u1, indexing="ij")

        # Polar grid (r, theta) for vinyl record, hourglass, trampoline, gravity bowls
        r_lin = torch.linspace(0.0, 1.0, 260, device=self.dev)
        th_lin = torch.linspace(0.0, 2.0 * math.pi, 360, device=self.dev)
        self.pol_r, self.pol_th = torch.meshgrid(r_lin, th_lin, indexing="ij")

        self._init_galaxy_buffers()
        self._init_dark_matter_web()
        self._init_hourglass_particles()
        self._init_cluster_collision_buffers()
        self._init_jwst_hex_mirrors()

    def _init_galaxy_buffers(self) -> None:
        """46,000-star multi-arm logarithmic spiral galaxy with golden bulge, blue arms & pink H-II knots."""
        g = torch.Generator(device="cpu")
        g.manual_seed(101)
        n = 46000
        arm_id = torch.randint(0, 4, (n,), generator=g).float()
        # Radial distribution: dense bulge + extended exponential disk
        u = torch.rand(n, generator=g)
        rad = torch.where(u < 0.24, (u / 0.24) ** 0.75 * 1.45, 0.75 + ((u - 0.24) / 0.76) ** 0.82 * 5.35)
        scatter = (0.14 + 0.08 * rad) * torch.randn(n, generator=g)
        theta0 = arm_id * (0.5 * math.pi) + 1.55 * torch.log(rad + 0.35) + scatter
        z = torch.randn(n, generator=g) * (0.34 * torch.exp(-rad / 1.6) + 0.055)

        # Colors: golden core -> sapphire/cyan spiral arms + 8% bright magenta/rose H-II star-forming knots
        core_w = torch.exp(-(rad / 1.55) ** 2)
        hii = (torch.rand(n, generator=g) < 0.075) & (rad > 1.2) & (torch.abs(scatter) < 0.16)

        cr = torch.where(hii, 1.35, 1.25 * core_w + 0.28 * (1.0 - core_w))
        cg = torch.where(hii, 0.36, 0.92 * core_w + 0.68 * (1.0 - core_w))
        cb = torch.where(hii, 0.78, 0.42 * core_w + 1.25 * (1.0 - core_w))
        lum = (0.30 + 0.95 * (torch.rand(n, generator=g) ** 1.8)) * (0.55 + 0.75 * core_w)

        self.gal_r = rad.to(self.dev)
        self.gal_th0 = theta0.to(self.dev)
        self.gal_z = z.to(self.dev)
        self.gal_rgb = (torch.stack([cr, cg, cb], dim=-1) * lum.unsqueeze(-1)).to(self.dev)
        self.gal_sz = torch.where(hii, 2.5, 1.15 + 1.1 * core_w).to(self.dev)

    def _init_dark_matter_web(self) -> None:
        """3D cosmic web filament nodes & edges wrapping the galaxy for Scene 01 & Hook."""
        rng = np.random.default_rng(77)
        # 42 nodes on two concentric deformed shells (R=4.2 and R=7.4)
        pts = []
        for r_shell, count in ((4.2, 16), (7.5, 26)):
            idx = np.arange(count, dtype=np.float32)
            phi = math.pi * (3.0 - math.sqrt(5.0)) * idx
            y = 1.0 - (idx / max(1, count - 1)) * 2.0
            rr = np.sqrt(np.maximum(0.0, 1.0 - y * y))
            x = np.cos(phi) * rr
            z = np.sin(phi) * rr * 0.68  # slightly oblate halo
            jit = rng.normal(0.0, 0.28, size=(count, 3)).astype(np.float32)
            pts.append(np.stack([x, y, z], axis=-1) * r_shell + jit)
        nodes = np.concatenate(pts, axis=0)

        # Connect nearest neighbors into 3D filament tubes
        segs = []
        for i in range(len(nodes)):
            d = np.linalg.norm(nodes - nodes[i], axis=-1)
            nn = np.argsort(d)[1:4]
            for j in nn:
                if i < j:
                    segs.append((nodes[i], nodes[j]))
        self.dm_nodes = torch.tensor(nodes, device=self.dev, dtype=torch.float32)
        self.dm_segs = segs

        # Pre-batch all Dark Matter web filament tubes into ONE single GPU mesh `(M_all, 12, 3)` for 25x speedup!
        dm_Ps, dm_Ns = [], []
        s_lin = torch.linspace(0.0, 1.0, 56, device=self.dev).unsqueeze(-1)
        for a, b in segs:
            pa = torch.tensor(a, device=self.dev, dtype=torch.float32)
            pb = torch.tensor(b, device=self.dev, dtype=torch.float32)
            P_seg, N_seg = make_tube_along_curve(pa + s_lin * (pb - pa), 0.048, n_around=14)
            dm_Ps.append(P_seg)
            dm_Ns.append(N_seg)
        self.dm_web_P = torch.cat(dm_Ps, dim=0)
        self.dm_web_N = torch.cat(dm_Ns, dim=0)

    def _init_hourglass_particles(self) -> None:
        """38,000 swirling cosmic particles for the Two-Winged Catenoid Hourglass (Scene 04 & Hook)."""
        g = torch.Generator(device="cpu")
        g.manual_seed(404)
        n = 38000
        self.hg_u0 = torch.rand(n, generator=g).to(self.dev)          # axial flow phase 0..1
        self.hg_ang0 = (torch.rand(n, generator=g) * 6.28318).to(self.dev)
        self.hg_jit = (torch.randn(n, 3, generator=g) * 0.14).to(self.dev)
        self.hg_wing = torch.where(torch.rand(n, generator=g) < 0.5, 1.0, -1.0).to(self.dev)
        self.hg_lum = (0.35 + 0.95 * (torch.rand(n, generator=g) ** 1.6)).to(self.dev)

    def _init_cluster_collision_buffers(self) -> None:
        """42,000 particles for Bullet Cluster collision (stars vs shock-heated gas clouds)."""
        g = torch.Generator(device="cpu")
        g.manual_seed(808)
        n_gas = 26000
        n_stars = 16000
        self.cl_gas_side = torch.where(torch.arange(n_gas) < n_gas // 2, -1.0, 1.0).to(self.dev)
        self.cl_gas_loc = (torch.randn(n_gas, 3, generator=g) * torch.tensor([0.95, 1.15, 0.85])).to(self.dev)
        self.cl_star_side = torch.where(torch.arange(n_stars) < n_stars // 2, -1.0, 1.0).to(self.dev)
        self.cl_star_loc = (torch.randn(n_stars, 3, generator=g) * torch.tensor([0.75, 0.90, 0.70])).to(self.dev)

    def _init_jwst_hex_mirrors(self) -> None:
        """18 hexagonal mirror centers (2 concentric rings around central aperture) for JWST sculpture."""
        d = 0.62
        centers: List[Tuple[float, float]] = []
        # Ring 1 (6 hexes)
        for k in range(6):
            ang = k * math.pi / 3.0
            centers.append((d * math.cos(ang), d * math.sin(ang)))
        # Ring 2 (12 hexes)
        for k in range(6):
            a0 = k * math.pi / 3.0
            a1 = (k + 1) * math.pi / 3.0
            p0 = (2.0 * d * math.cos(a0), 2.0 * d * math.sin(a0))
            p1 = (2.0 * d * math.cos(a1), 2.0 * d * math.sin(a1))
            centers.append(p0)
            centers.append((0.5 * (p0[0] + p1[0]), 0.5 * (p0[1] + p1[1])))
        self.jwst_centers = centers
        # Pre-build solid 18-hexagon mirror faces `(18 * 36, 73, 3)` in local XY plane (true flat-edged hexagons!)
        r_lin = torch.linspace(0.0, 0.285, 36, device=self.dev)
        th_lin = torch.linspace(0.0, 2.0 * math.pi, 73, device=self.dev)
        rr_h, tt_h = torch.meshgrid(r_lin, th_lin, indexing="ij")
        # Exact polar equation of a regular flat-sided hexagon: r_hex(theta) = cos(pi/6) / cos((theta mod pi/3) - pi/6)
        sector = torch.remainder(tt_h, math.pi / 3.0) - (math.pi / 6.0)
        hex_scale = math.cos(math.pi / 6.0) / torch.cos(sector)
        hx_loc = rr_h * hex_scale * torch.cos(tt_h)
        hy_loc = rr_h * hex_scale * torch.sin(tt_h)
        hex_tiles = []
        for cx, cy in centers:
            lx = cx + hx_loc
            ly = cy + hy_loc
            lz = -0.035 * (lx * lx + ly * ly)
            hex_tiles.append(torch.stack([lx, ly, lz], dim=-1))
        self.jwst_local_P = torch.cat(hex_tiles, dim=0)

    # -----------------------------------------------------------------------
    # Helper: Render 3D Arrow (Cylindrical Shaft + Conical Tip)
    # -----------------------------------------------------------------------
    def _draw_3d_arrow(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        rgb: Tuple[float, float, float],
        cam: CameraMatrix,
        shaft_r: float = 0.06,
    ) -> None:
        p0 = torch.tensor(start, device=self.dev, dtype=torch.float32)
        p1 = torch.tensor(end, device=self.dev, dtype=torch.float32)
        vec = p1 - p0
        length = float(torch.norm(vec).item())
        if length < 1e-3:
            return
        s = torch.linspace(0.0, 1.0, 48, device=self.dev)
        curve = p0.unsqueeze(0) + s.unsqueeze(-1) * vec.unsqueeze(0)
        # Taper last 22% as conical arrowhead!
        rad = torch.where(s < 0.78, shaft_r, shaft_r * 2.5 * (1.0 - s) / 0.22)
        P, N = make_tube_along_curve(curve, rad, n_around=20)
        self.canvas.render_surface_mesh(
            P,
            rgb,
            cam,
            normals=N,
            emissive_rgb=(rgb[0] * 0.45, rgb[1] * 0.45, rgb[2] * 0.45),
            alpha=0.95,
            two_sided=False,
            shininess=64.0,
        )

    def _spinning_galaxy_pts(self, t: float, omega_flat: float = 0.22) -> torch.Tensor:
        """Computes flat-rotation-curve 3D positions `(46000, 3)` at time `t`."""
        ang = self.gal_th0 - (omega_flat * t) / torch.clamp(0.45 + 0.28 * self.gal_r, min=0.45)
        gx = self.gal_r * torch.cos(ang)
        gy = self.gal_r * torch.sin(ang)
        return torch.stack([gx, gy, self.gal_z], dim=-1)

    # -----------------------------------------------------------------------
    # SCENE DISPATCHER
    # -----------------------------------------------------------------------
    def render_scene_frame(self, scene_id: str, t: float, dur: float) -> np.ndarray:
        prog = max(0.0, min(1.0, t / max(0.001, dur)))
        fn = getattr(self, f"_render_{scene_id}", self._render_scene02)
        fn(t, dur, prog)
        return self.canvas.finalize_srgb_uint8(exposure=1.06, bloom_strength=0.44)

    # -----------------------------------------------------------------------
    # HOOK 00: 13.5s Fast-Cut Cold-Open Visual Hook!
    # -----------------------------------------------------------------------
    def _render_hook00(self, t: float, dur: float, prog: float) -> None:
        if prog < 0.34:
            # Beat 1 (0 - 4.6s): High-speed plunge into spiral galaxy trapped in fracturing violet Dark Matter cage!
            u = prog / 0.34
            pose = interpolate_camera(
                [
                    (0.0, CameraPose(azim=0.4, elev=0.62, dist=16.5, roll_deg=-8.0, fov_deg=50.0)),
                    (1.0, CameraPose(azim=1.45, elev=0.22, dist=5.4, roll_deg=6.0, fov_deg=54.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.03, 0.03, 0.13), nebula_b=(0.09, 0.02, 0.12))
            g_pts = self._spinning_galaxy_pts(t * 2.2)
            self.canvas.render_particles(g_pts, self.gal_rgb * 1.15, self.gal_sz, cam, focus_dist=pose.dist)

            # Glowing violet dark-matter cage filaments pulsing (1 batched GPU draw call!)
            pulse = 0.55 + 0.45 * math.sin(t * 5.0)
            self.canvas.render_surface_mesh(
                self.dm_web_P, (0.48, 0.22, 0.95), cam, normals=self.dm_web_N,
                emissive_rgb=(0.32 * pulse, 0.10, 0.72 * pulse), alpha=0.75, two_sided=False, write_depth=False, supersample=(1, 2)
            )
        elif prog < 0.68:
            # Beat 2 (4.6 - 9.2s): Monumental 180-degree 3D Cosmic Hourglass Flip!
            u = (prog - 0.34) / 0.34
            self._render_hourglass_core(t * 1.6, flip_amt=smootherstep01(u), cam_pose=CameraPose(
                azim=0.5 + 1.2 * u,
                elev=0.18 + 0.15 * math.sin(u * math.pi),
                dist=10.8 - 4.2 * smootherstep01(u),
                roll_deg=180.0 * smootherstep01(u),
                fov_deg=48.0,
            ))
        else:
            # Beat 3 (9.2 - 13.5s): Low-altitude supersonic skim over gleaming golden-cyan silk weave into knot!
            u = (prog - 0.68) / 0.32
            pose = interpolate_camera(
                [
                    (0.0, CameraPose(azim=-0.8, elev=0.16, dist=9.5, target=(-2.2, 0.0, 0.0), roll_deg=-10.0, fov_deg=52.0)),
                    (1.0, CameraPose(azim=0.35, elev=0.26, dist=3.1, target=(0.0, 0.0, 0.25), roll_deg=0.0, fov_deg=46.0)),
                ],
                u,
            )
            self._render_silk_and_knot_core(t * 1.5, pose, knot_weight=smootherstep01(u))

    # -----------------------------------------------------------------------
    # SCENE 00: David's Personal Intro — JWST, Planck, SymPy/SciPy & Hero Reveal
    # -----------------------------------------------------------------------
    def _render_scene00(self, t: float, dur: float, prog: float) -> None:
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=-0.65, elev=0.28, dist=9.6, target=(-2.2, 0.0, 0.3), fov_deg=45.0)),
                (0.22, CameraPose(azim=0.15, elev=0.18, dist=4.6, target=(-2.8, 1.2, 0.5), roll_deg=4.0, fov_deg=44.0)),
                (0.42, CameraPose(azim=0.85, elev=0.24, dist=5.4, target=(2.4, 1.0, 0.4), roll_deg=-3.0, fov_deg=45.0)),
                (0.68, CameraPose(azim=1.55, elev=0.34, dist=10.5, target=(0.0, 0.0, 0.2), fov_deg=46.0)),
                (0.84, CameraPose(azim=2.15, elev=0.22, dist=7.8, target=(0.0, 0.0, 0.4), fov_deg=46.0)),
                (1.00, CameraPose(azim=2.65, elev=0.26, dist=9.2, target=(0.0, 0.0, 0.3), fov_deg=46.0)),
            ],
            prog,
        )
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.018, 0.052, 0.125), nebula_b=(0.075, 0.035, 0.095))

        # 1. Central stretched cosmic silk floor (z = -1.6) with gentle golden harmonic waves
        gx = self.grid_x * 9.5
        gy = self.grid_y * 9.5
        rr = torch.sqrt(gx * gx + gy * gy + 0.25)
        gz = -1.65 - 1.35 * torch.exp(-rr * 0.45) + 0.14 * torch.sin(1.4 * rr - 1.6 * t)
        P_floor = torch.stack([gx, gy, gz], dim=-1)
        self.canvas.render_surface_mesh(
            P_floor,
            (0.06, 0.24, 0.46),
            cam,
            alpha=0.84,
            shininess=56.0,
            fresnel_rgb=(0.25, 0.82, 1.0),
            wire_stride=10,
            wire_rgb=(0.32, 0.85, 1.0),
            wire_boost=0.36,
        )

        # 2. Sculpted Solid 18-Segment Golden JWST Mirror Array floating at (-2.9, 1.3, 0.65) — 1 batched GPU draw!
        yaw = 0.48 + 0.14 * math.sin(0.4 * t)
        cy_w, sy_w = math.cos(yaw), math.sin(yaw)
        lx = self.jwst_local_P[..., 0]
        ly = self.jwst_local_P[..., 1]
        lz = self.jwst_local_P[..., 2]
        wx = -2.9 + sy_w * lx + cy_w * lz
        wy = 1.3 + cy_w * lx - sy_w * lz
        wz = 0.65 + ly
        P_jwst = torch.stack([wx, wy, wz], dim=-1)
        N_jwst = torch.tensor([cy_w, -sy_w, 0.12], device=self.dev).view(1, 1, 3).expand_as(P_jwst)
        N_jwst = F.normalize(N_jwst, dim=-1)
        self.canvas.render_surface_mesh(
            P_jwst,
            (0.98, 0.74, 0.16),
            cam,
            normals=N_jwst,
            emissive_rgb=(0.24, 0.15, 0.02),
            alpha=0.99,
            shininess=84.0,
            specular_strength=1.45,
            fresnel_rgb=(1.0, 0.88, 0.42),
            supersample=(1, 1),
        )

        # 3. Sculpted 3D Planck CMB Acoustic Harmonics Sphere at (2.6, 1.1, 0.65)
        P_cmb, uu_c, vv_c = make_sphere_mesh((2.6, 1.1, 0.65), 0.95, 110, 70, self.dev)
        cmb_temp = (
            torch.sin(5.0 * uu_c + 0.5 * t) * torch.sin(4.0 * vv_c)
            + 0.6 * torch.cos(9.0 * uu_c - 0.3 * t) * torch.sin(7.0 * vv_c)
        )
        t_norm = torch.clamp(0.5 + 0.42 * cmb_temp, 0.0, 1.0)
        cmb_rgb = torch.stack(
            [
                0.12 + 0.95 * (t_norm ** 1.5),
                0.35 + 0.55 * torch.sin(t_norm * math.pi),
                1.05 - 0.85 * t_norm,
            ],
            dim=-1,
        )
        self.canvas.render_surface_mesh(
            P_cmb, cmb_rgb, cam, alpha=0.96, two_sided=False, shininess=42.0, fresnel_rgb=(0.5, 0.9, 1.0)
        )

        # 4. Central Twin-Winged Golden-Sapphire Cosmic Hourglass & Orbital Verification Rings
        u_hg = torch.linspace(-1.0, 1.0, 180, device=self.dev)
        th_hg = torch.linspace(0.0, 2.0 * math.pi, 200, device=self.dev)
        uu_h, tt_h = torch.meshgrid(u_hg, th_hg, indexing="ij")
        rad_h = 0.38 * torch.cosh(1.65 * uu_h)
        hx = rad_h * torch.cos(tt_h + 0.35 * t)
        hy = rad_h * torch.sin(tt_h + 0.35 * t)
        hz = 0.45 + 1.55 * uu_h
        waist_glow = torch.exp(-(uu_h * 4.2) ** 2)
        hg_rgb = torch.stack(
            [
                0.18 + 0.85 * waist_glow + 0.55 * torch.clamp(-uu_h, min=0.0),
                0.56 + 0.32 * waist_glow,
                0.98 - 0.45 * torch.clamp(-uu_h, min=0.0),
            ],
            dim=-1,
        )
        self.canvas.render_surface_mesh(
            torch.stack([hx, hy, hz], dim=-1),
            hg_rgb,
            cam,
            emissive_rgb=torch.stack([0.38 * waist_glow, 0.26 * waist_glow, 0.08 * waist_glow], dim=-1),
            alpha=0.80,
            shininess=72.0,
            wire_stride=12,
            wire_rgb=(0.98, 0.84, 0.45),
            wire_boost=0.35,
        )

        # Two sleek gyroscope verification rings (`SymPy` & `SciPy` precision orbits)
        for idx_r, (ang_tilt, r_maj, col_r) in enumerate(((0.48, 2.35, (0.30, 0.88, 1.0)), (-0.52, 2.85, (0.98, 0.78, 0.30)))):
            th_r = torch.linspace(0.0, 2.0 * math.pi, 180, device=self.dev)
            spin = t * (0.45 if idx_r == 0 else -0.35)
            rx = r_maj * torch.cos(th_r + spin)
            ry = r_maj * torch.sin(th_r + spin) * math.cos(ang_tilt)
            rz = 0.45 + r_maj * torch.sin(th_r + spin) * math.sin(ang_tilt)
            Pr, Nr = make_tube_along_curve(torch.stack([rx, ry, rz], dim=-1), 0.032, n_around=16, closed=True)
            self.canvas.render_surface_mesh(Pr, col_r, cam, normals=Nr, emissive_rgb=(col_r[0]*0.3, col_r[1]*0.3, col_r[2]*0.3), two_sided=False)

        # Mini 175-Galaxy SPARC swirl in foreground-right
        g_pts = self._spinning_galaxy_pts(t * 0.9) * 0.36 + torch.tensor([0.0, -3.1, -0.35], device=self.dev)
        self.canvas.render_particles(g_pts[::2], self.gal_rgb[::2], self.gal_sz[::2] * 0.85, cam)

    # -----------------------------------------------------------------------
    # SCENE 01: Midnight Illusion & Textbook Lambda-CDM (95% Invisible)
    # -----------------------------------------------------------------------
    def _render_scene01(self, t: float, dur: float, prog: float) -> None:
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=0.20, elev=0.14, dist=6.5, target=(0.0, 0.0, 0.4), fov_deg=50.0)),
                (0.24, CameraPose(azim=0.75, elev=0.38, dist=7.2, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                (0.48, CameraPose(azim=1.45, elev=0.20, dist=4.8, target=(1.8, 0.0, 0.0), roll_deg=5.0, fov_deg=45.0)),
                (0.76, CameraPose(azim=2.25, elev=0.34, dist=14.8, target=(0.0, 0.0, 0.0), roll_deg=0.0, fov_deg=48.0)),
                (1.00, CameraPose(azim=2.95, elev=0.26, dist=11.5, target=(0.0, 0.0, 0.0), roll_deg=180.0 * smoothstep01((prog - 0.87) / 0.13), fov_deg=47.0)),
            ],
            prog,
        )
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.015, 0.035, 0.095), nebula_b=(0.065, 0.020, 0.105))

        # Phase A (0 - 24%): Floating solid-marble atoms & river-of-time ribbon dissolving as we enter the galaxy
        if prog < 0.28:
            fade_m = 1.0 - smoothstep01((prog - 0.18) / 0.10)
            for k in range(5):
                ang = k * 1.256 + 0.35 * t
                center = (2.1 * math.cos(ang), 2.1 * math.sin(ang), 0.55 + 0.25 * math.sin(t + k))
                Ps, _, _ = make_sphere_mesh(center, 0.28, 48, 32, self.dev)
                self.canvas.render_surface_mesh(
                    Ps, (0.85, 0.88, 0.95), cam, alpha=0.92 * fade_m, two_sided=False, shininess=90.0, specular_strength=1.2
                )

        # Always-present 46,000-star 3D Spiral Galaxy spinning rapidly!
        g_pts = self._spinning_galaxy_pts(t * 1.35, omega_flat=0.38)
        self.canvas.render_particles(g_pts, self.gal_rgb * 1.12, self.gal_sz, cam, focus_dist=pose.dist)

        # Outer velocity tangential streaks (showing outer stars whipping way too fast: 25%..65%)
        if 0.22 < prog < 0.72:
            v_fade = smoothstep01((prog - 0.22) / 0.08) * (1.0 - smoothstep01((prog - 0.62) / 0.10))
            for k in range(8):
                base_a = k * (math.pi / 4.0) - 0.55 * t
                arc = torch.linspace(base_a, base_a - 0.42, 36, device=self.dev)
                r_orb = 4.65 + 0.35 * (k % 2)
                curve = torch.stack([r_orb * torch.cos(arc), r_orb * torch.sin(arc), torch.zeros_like(arc)], dim=-1)
                Pt, Nt = make_tube_along_curve(curve, 0.036, n_around=12)
                self.canvas.render_surface_mesh(
                    Pt, (0.20, 0.92, 1.0), cam, normals=Nt,
                    emissive_rgb=(0.15 * v_fade, 0.65 * v_fade, 0.85 * v_fade), alpha=0.85 * v_fade, two_sided=False
                )

        # Phase C (52% - 92%): Giant 3D Violet Cold Dark Matter Filament Scaffolding (27%) + Crimson Dark Energy Arrows (68%)
        if prog > 0.50:
            dm_in = smoothstep01((prog - 0.50) / 0.10) * (1.0 - 0.65 * smoothstep01((prog - 0.88) / 0.12))
            self.canvas.render_surface_mesh(
                self.dm_web_P,
                (0.52, 0.24, 0.96),
                cam,
                normals=self.dm_web_N,
                emissive_rgb=(0.28 * dm_in, 0.10 * dm_in, 0.62 * dm_in),
                alpha=0.75 * dm_in,
                two_sided=False,
                write_depth=False,
                supersample=(1, 2),
            )
            # Glowing violet halo nodes
            node_rgb = torch.tensor([0.72, 0.38, 1.25], device=self.dev).expand(len(self.dm_nodes), 3) * dm_in
            self.canvas.render_particles(self.dm_nodes, node_rgb, 3.8, cam)

        if 0.62 < prog < 0.94:
            de_in = smoothstep01((prog - 0.62) / 0.08) * (1.0 - smoothstep01((prog - 0.88) / 0.06))
            stretch = 1.0 + 0.16 * math.sin(t * 1.8)
            for k in range(10):
                ang = k * (2.0 * math.pi / 10.0) + 0.12 * t
                elev_a = 0.28 * math.sin(k * 1.7)
                r0, r1 = 6.2, 8.6 * stretch
                dx, dy, dz = math.cos(ang) * math.cos(elev_a), math.sin(ang) * math.cos(elev_a), math.sin(elev_a)
                self._draw_3d_arrow(
                    (r0 * dx, r0 * dy, r0 * dz),
                    (r1 * dx, r1 * dy, r1 * dz),
                    (1.15 * de_in, 0.24 * de_in, 0.38 * de_in),
                    cam,
                    shaft_r=0.065,
                )

    # -----------------------------------------------------------------------
    # SCENE 02: Erasing Empty Space — Silk Weave, Guitar Pluck & 3D Trefoil Knot
    # -----------------------------------------------------------------------
    def _render_silk_and_knot_core(self, t: float, pose: CameraPose, knot_weight: float) -> None:
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.012, 0.055, 0.12), nebula_b=(0.05, 0.03, 0.09), star_gain=0.45)

        gx = self.grid_x * 8.5
        gy = self.grid_y * 8.5
        r2 = gx * gx + gy * gy

        # Travelling golden starlight wave packet ("like a pluck traveling down a guitar string")
        pkt_x = ((t * 2.8) % 14.0) - 7.0
        pluck = 0.55 * torch.exp(-((gx - pkt_x) ** 2) / 0.75) * torch.exp(-(gy ** 2) / 2.2) * torch.cos(6.5 * (gx - pkt_x))

        # Local dimple & rotational twist where the 3D Trefoil Atom Knot sits at (0, 0, 0.35)
        dimple = -0.85 * knot_weight * torch.exp(-r2 / 1.85)
        quantum_ripples = 0.11 * torch.sin(2.4 * gx - 1.9 * t) * torch.cos(2.4 * gy + 1.5 * t)
        gz = dimple + pluck + quantum_ripples

        P_cloth = torch.stack([gx, gy, gz], dim=-1)

        # Rich silk micro-weave albedo + golden starlight shimmer emission
        shimmer = torch.abs(pluck) * 2.4
        base_col = torch.stack(
            [
                0.06 + 0.95 * shimmer,
                0.30 + 0.72 * shimmer,
                0.62 + 0.18 * shimmer,
            ],
            dim=-1,
        )
        emit_col = torch.stack([0.85 * shimmer, 0.58 * shimmer, 0.12 * shimmer], dim=-1)

        self.canvas.render_surface_mesh(
            P_cloth,
            base_col,
            cam,
            emissive_rgb=emit_col,
            alpha=0.92,
            shininess=68.0,
            specular_strength=0.85,
            fresnel_rgb=(0.35, 0.90, 1.0),
            wire_stride=6,
            wire_rgb=(0.38, 0.88, 1.0),
            wire_boost=0.42,
        )

        # Sculpted 3-Strand 3D Trefoil Torus Knot ("atoms are tiny twisted knots woven out of the threads")
        if knot_weight > 0.02:
            s = torch.linspace(0.0, 2.0 * math.pi, 360, device=self.dev)
            spin = 0.55 * t
            scale_k = 0.52 * knot_weight
            kx = scale_k * (torch.sin(s + spin) + 2.0 * torch.sin(2.0 * s + spin))
            ky = scale_k * (torch.cos(s + spin) - 2.0 * torch.cos(2.0 * s + spin))
            kz = 0.42 + scale_k * (-torch.sin(3.0 * s))
            Pk, Nk = make_tube_along_curve(torch.stack([kx, ky, kz], dim=-1), 0.115 * knot_weight, n_around=28, closed=True)

            # Iridescent cyan-to-gold harmonic coloring along the knot strand
            c_t = 0.5 + 0.5 * torch.sin(3.0 * s).view(-1, 1, 1).expand(360, 28, 1)
            k_rgb = torch.cat(
                [
                    0.20 + 0.85 * c_t,
                    0.75 + 0.18 * c_t,
                    1.05 - 0.65 * c_t,
                ],
                dim=-1,
            )
            self.canvas.render_surface_mesh(
                Pk,
                k_rgb,
                cam,
                normals=Nk,
                emissive_rgb=k_rgb * 0.28,
                alpha=0.99,
                two_sided=False,
                shininess=92.0,
                specular_strength=1.25,
                fresnel_rgb=(1.0, 0.92, 0.55),
                supersample=(4, 4),
            )

    def _render_scene02(self, t: float, dur: float, prog: float) -> None:
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=-0.75, elev=0.52, dist=13.5, target=(0.0, 0.0, 0.0), fov_deg=48.0)),
                (0.32, CameraPose(azim=-0.10, elev=0.18, dist=6.2, target=(-1.2, 0.0, 0.1), roll_deg=-4.0, fov_deg=46.0)),
                (0.52, CameraPose(azim=0.65, elev=0.15, dist=2.55, target=(0.0, 0.0, 0.38), roll_deg=3.0, fov_deg=44.0)),
                (0.72, CameraPose(azim=1.65, elev=0.22, dist=2.85, target=(0.0, 0.0, 0.35), roll_deg=0.0, fov_deg=44.0)),
                (1.00, CameraPose(azim=2.45, elev=0.44, dist=10.8, target=(0.0, 0.0, 0.0), fov_deg=47.0)),
            ],
            prog,
        )
        knot_w = smoothstep01((prog - 0.34) / 0.14)
        self._render_silk_and_knot_core(t, pose, knot_weight=knot_w)

    # -----------------------------------------------------------------------
    # SCENE 03: Vinyl Record Spacetime, Macro Stylus Groove & Ink-in-Water Memory
    # -----------------------------------------------------------------------
    def _render_scene03(self, t: float, dur: float, prog: float) -> None:
        # Stylus rides slowly along radius r_needle = 3.25 at angle th_needle
        th_needle = 0.65 + 0.55 * prog
        r_needle = 3.25
        nx_tip = r_needle * math.cos(th_needle)
        ny_tip = r_needle * math.sin(th_needle)

        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=-0.85, elev=0.56, dist=11.8, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                (0.28, CameraPose(azim=th_needle - 0.85, elev=0.28, dist=5.6, target=(nx_tip * 0.6, ny_tip * 0.6, 0.15), fov_deg=45.0)),
                (0.52, CameraPose(azim=th_needle - 1.15, elev=0.14, dist=2.35, target=(nx_tip, ny_tip, 0.15), roll_deg=4.0, fov_deg=42.0)),
                (0.78, CameraPose(azim=th_needle - 0.55, elev=0.22, dist=3.45, target=(nx_tip, ny_tip, 0.45), roll_deg=-2.0, fov_deg=45.0)),
                (1.00, CameraPose(azim=th_needle + 0.25, elev=0.38, dist=7.6, target=(0.0, 0.0, 0.25), fov_deg=46.0)),
            ],
            prog,
        )
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.022, 0.038, 0.095), nebula_b=(0.075, 0.042, 0.065), star_gain=0.55)

        # 1. Sculpted 3D Obsidian-Sapphire Vinyl Record Disc (`R = 0.35 .. 5.8`) with real 3D carved waveform grooves!
        rr = 0.30 + 5.55 * self.pol_r
        tt = self.pol_th
        vx = rr * torch.cos(tt)
        vy = rr * torch.sin(tt)

        # Concentric audio grooves modulated by harmonic music waveforms ("opening chord, middle chorus, fade-out")
        groove_wave = 0.055 * torch.sin(26.0 * rr + 0.35 * torch.sin(14.0 * tt) + 0.22 * torch.cos(32.0 * tt * rr * 0.2))
        vz = torch.where(rr > 1.15, groove_wave, 0.04)
        P_disc = torch.stack([vx, vy, vz], dim=-1)

        # Highlight the active groove ring + past ("neater") vs future ("messier") arc around the needle!
        ring_dist = torch.abs(rr - r_needle)
        active_ring = torch.exp(-(ring_dist / 0.14) ** 2)
        ang_diff = torch.atan2(torch.sin(tt - th_needle), torch.cos(tt - th_needle))
        past_glow = active_ring * torch.sigmoid(-ang_diff * 5.0)   # Neat cyan memory side
        fut_glow = active_ring * torch.sigmoid(ang_diff * 5.0)     # Messier golden entropy side

        disc_rgb = torch.stack(
            [
                0.045 + 0.85 * torch.where(rr < 1.12, 1.0, 0.0) + 0.95 * fut_glow,
                0.065 + 0.62 * torch.where(rr < 1.12, 1.0, 0.0) + 0.82 * past_glow + 0.52 * fut_glow,
                0.115 + 0.18 * torch.where(rr < 1.12, 1.0, 0.0) + 1.05 * past_glow,
            ],
            dim=-1,
        )
        disc_emit = torch.stack(
            [0.55 * fut_glow, 0.45 * past_glow + 0.28 * fut_glow, 0.65 * past_glow], dim=-1
        )
        self.canvas.render_surface_mesh(
            P_disc,
            disc_rgb,
            cam,
            emissive_rgb=disc_emit,
            alpha=0.97,
            two_sided=False,
            shininess=88.0,
            specular_strength=1.15,
            fresnel_rgb=(0.45, 0.78, 1.0),
            supersample=(3, 2),
        )

        # 2. Brushed-Brass Center Spindle + Sculpted 3D Tonearm & Glowing Diamond Stylus Needle!
        pivot = torch.tensor([5.6, -3.2, 1.35], device=self.dev)
        head = torch.tensor([nx_tip, ny_tip, 0.42], device=self.dev)
        tip = torch.tensor([nx_tip, ny_tip, 0.04], device=self.dev)
        arm_s = torch.linspace(0.0, 1.0, 96, device=self.dev).unsqueeze(-1)
        arm_curve = pivot + arm_s * (head - pivot) + torch.tensor([0.0, 0.0, 0.25], device=self.dev) * torch.sin(arm_s * math.pi)
        Pa, Na = make_tube_along_curve(arm_curve, 0.055, n_around=28)
        self.canvas.render_surface_mesh(
            Pa, (0.94, 0.76, 0.32), cam, normals=Na, alpha=0.99, two_sided=False, shininess=96.0, specular_strength=1.3, supersample=(4, 3)
        )

        # Diamond stylus cone descending from head -> groove tip
        st_s = torch.linspace(0.0, 1.0, 48, device=self.dev)
        st_curve = head.unsqueeze(0) + st_s.unsqueeze(-1) * (tip - head).unsqueeze(0)
        Ps, Ns = make_tube_along_curve(st_curve, 0.075 * (1.0 - 0.82 * st_s), n_around=28)
        self.canvas.render_surface_mesh(
            Ps, (0.85, 0.96, 1.0), cam, normals=Ns, emissive_rgb=(0.55, 0.85, 1.0), alpha=0.99, two_sided=False, shininess=110.0, supersample=(4, 4)
        )

        # 3. Chunk 14 (54% - 100%): Billowing 3D Multi-Tendril Ink-in-Water Entropy Cloud blooming from the groove!
        if prog > 0.50:
            ink_w = smoothstep01((prog - 0.50) / 0.14)
            # 24 intertwined swirling vortex tendrils x 1,100 particles = 26,400 volumetric ink particles!
            s_t = torch.linspace(0.0, 1.0, 1100, device=self.dev).unsqueeze(0)   # (1, 1100)
            k_id = torch.arange(24, device=self.dev, dtype=torch.float32).unsqueeze(1)  # (24, 1)
            ang_i = th_needle + 0.03 + 1.35 * s_t * ink_w + 0.06 * torch.sin(k_id * 2.1 + 4.0 * s_t)
            bloom_r = (s_t ** 1.15) * 0.92 * ink_w
            swirl_a = k_id * (2.0 * math.pi / 24.0) + 4.8 * s_t - 0.85 * t + 0.7 * torch.sin(9.0 * s_t + k_id)
            rad_off = bloom_r * (0.25 + 0.75 * torch.abs(torch.sin(3.3 * k_id + 5.0 * s_t)))
            r_i = r_needle + rad_off * torch.cos(swirl_a)
            zi = 0.06 + bloom_r * 0.75 + rad_off * 0.65 * torch.sin(swirl_a)
            ix = (r_i * torch.cos(ang_i)).reshape(-1)
            iy = (r_i * torch.sin(ang_i)).reshape(-1)
            iz = zi.reshape(-1)
            s_flat = s_t.expand(24, 1100).reshape(-1)
            ink_pts = torch.stack([ix, iy, iz], dim=-1)
            ink_rgb = torch.stack(
                [
                    (0.18 + 0.95 * s_flat) * ink_w,
                    (0.82 - 0.22 * s_flat) * ink_w,
                    (1.05 - 0.72 * s_flat) * ink_w,
                ],
                dim=-1,
            ) * 0.24
            self.canvas.render_particles(ink_pts, ink_rgb, 1.3 + 2.2 * s_flat, cam, focus_dist=pose.dist)

    # -----------------------------------------------------------------------
    # SCENE 04: Flipping the Cosmic Hourglass & Soap-Film Antimatter Sorter
    # -----------------------------------------------------------------------
    def _render_hourglass_core(self, t: float, flip_amt: float, cam_pose: CameraPose) -> None:
        cam = CameraMatrix(cam_pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.018, 0.048, 0.115), nebula_b=(0.085, 0.028, 0.085))

        # Sculpted 3D Catenoid Soap-Film Hourglass (`R(z) = r0 * cosh(z / a)` — smooth non-singular waist!)
        z_lin = torch.linspace(-3.4, 3.4, 280, device=self.dev)
        th_lin = torch.linspace(0.0, 2.0 * math.pi, 260, device=self.dev)
        zz, tt = torch.meshgrid(z_lin, th_lin, indexing="ij")

        r0 = 0.46
        rad = r0 * torch.cosh(0.68 * zz)
        # Add subtle chiral subatomic twist near the waist!
        twist = 0.35 * t + 0.55 * torch.tanh(1.2 * zz)
        hx = rad * torch.cos(tt + twist)
        hy = rad * torch.sin(tt + twist)
        P_hg = torch.stack([hx, hy, zz], dim=-1)

        waist_w = torch.exp(-(zz / 0.62) ** 2)
        upper_w = torch.sigmoid(zz * 2.2)   # Sapphire Matter Wing
        lower_w = torch.sigmoid(-zz * 2.2)  # Rose-Gold Mirror Antimatter Wing

        hg_rgb = torch.stack(
            [
                0.14 * upper_w + 0.92 * lower_w + 0.95 * waist_w,
                0.62 * upper_w + 0.36 * lower_w + 0.78 * waist_w,
                1.05 * upper_w + 0.52 * lower_w + 0.32 * waist_w,
            ],
            dim=-1,
        )
        hg_emit = torch.stack([0.48 * waist_w, 0.36 * waist_w, 0.10 * waist_w], dim=-1)
        self.canvas.render_surface_mesh(
            P_hg,
            hg_rgb,
            cam,
            emissive_rgb=hg_emit,
            alpha=0.72,
            shininess=84.0,
            specular_strength=1.05,
            fresnel_rgb=(0.95, 0.85, 0.55),
            wire_stride=12,
            wire_rgb=(0.75, 0.90, 1.0),
            wire_boost=0.28,
            write_depth=False,
        )

        # Glowing Golden Soap-Film Waist Ring (`z = 0`, smooth zero-entropy throat)
        Pw, Nw = make_torus_mesh((0.0, 0.0, 0.0), r0, 0.048, 180, 28, self.dev, axis="z")
        self.canvas.render_surface_mesh(
            Pw, (1.0, 0.84, 0.32), cam, normals=Nw, emissive_rgb=(0.55, 0.42, 0.10), alpha=0.98, two_sided=False, shininess=96.0
        )

        # 38,000 swirling cosmic particles: flowing INWARD from wide chaotic outer rim -> smooth central waist!
        flow = (self.hg_u0 - 0.11 * t) % 1.0  # 1.0 (outer chaotic rim) -> 0.0 (central pinhole drain)
        z_mag = 0.06 + 3.35 * (flow ** 1.15)
        zp = self.hg_wing * z_mag
        rp = r0 * torch.cosh(0.68 * zp)
        # Chaotic jitter at outer rim (`flow ~ 1`), crystal-smooth order at waist (`flow -> 0`)!
        chaos = (flow ** 1.8).unsqueeze(-1) * 1.45
        ang_p = self.hg_ang0 + self.hg_wing * (1.8 / (0.28 + flow)) + 0.30 * t
        px = rp * torch.cos(ang_p) + self.hg_jit[:, 0] * chaos.squeeze(-1)
        py = rp * torch.sin(ang_p) + self.hg_jit[:, 1] * chaos.squeeze(-1)
        pz = zp + self.hg_jit[:, 2] * chaos.squeeze(-1) * 0.5

        is_up = (self.hg_wing > 0).float()
        w_gl = torch.exp(-(z_mag / 0.55) ** 2)
        pr = (0.22 * is_up + 1.15 * (1.0 - is_up) + 0.90 * w_gl) * self.hg_lum
        pg = (0.76 * is_up + 0.44 * (1.0 - is_up) + 0.72 * w_gl) * self.hg_lum
        pb = (1.20 * is_up + 0.62 * (1.0 - is_up) + 0.25 * w_gl) * self.hg_lum
        self.canvas.render_particles(
            torch.stack([px, py, pz], dim=-1),
            torch.stack([pr, pg, pb], dim=-1) * 0.78,
            1.2 + 1.4 * w_gl,
            cam,
            focus_dist=cam_pose.dist,
        )

    def _render_scene04(self, t: float, dur: float, prog: float) -> None:
        # At prog = 0.26..0.44 ("grab that cosmic hourglass and flip it upside down"), camera rolls 180 degrees!
        flip = smootherstep01((prog - 0.25) / 0.18)
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=0.25, elev=0.18, dist=11.5, target=(0.0, 0.0, 0.8), roll_deg=0.0, fov_deg=47.0)),
                (0.25, CameraPose(azim=0.75, elev=0.12, dist=10.8, target=(0.0, 0.0, 0.0), roll_deg=0.0, fov_deg=47.0)),
                (0.45, CameraPose(azim=1.45, elev=-0.14, dist=9.6, target=(0.0, 0.0, 0.0), roll_deg=180.0, fov_deg=47.0)),
                (0.70, CameraPose(azim=2.25, elev=0.10, dist=2.85, target=(0.0, 0.0, 0.0), roll_deg=180.0, fov_deg=43.0)),
                (1.00, CameraPose(azim=3.15, elev=0.20, dist=7.8, target=(0.0, 0.0, 0.0), roll_deg=180.0, fov_deg=46.0)),
            ],
            prog,
        )
        self._render_hourglass_core(t, flip_amt=flip, cam_pose=pose)

    # -----------------------------------------------------------------------
    # SCENE 05: Two Brass Rings Soap Film + Live GPU 3D Double-Slit Wave Tank
    # -----------------------------------------------------------------------
    def _render_scene05(self, t: float, dur: float, prog: float) -> None:
        if prog < 0.56:
            # PART 5A (0 - 56%): Two Sculpted 3D Brushed-Brass Rings + Iridescent Soap Film Filtering Giant Sky Waves!
            u = prog / 0.56
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-0.75, elev=0.34, dist=10.8, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                    (0.50, CameraPose(azim=0.15, elev=0.18, dist=5.2, target=(0.8, 0.0, 0.0), roll_deg=3.0, fov_deg=44.0)),
                    (1.00, CameraPose(azim=0.95, elev=0.28, dist=7.6, target=(0.0, 0.0, 0.0), roll_deg=0.0, fov_deg=46.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.015, 0.048, 0.105), nebula_b=(0.055, 0.035, 0.075))

            # Asymmetric horizontal catenoid soap film between Giant Outer Brass Ring (x=-2.8, R=3.2) and Tiny Inner Brass Ring (x=+2.6, R=0.62)
            x_lin = torch.linspace(-2.8, 2.6, 260, device=self.dev)
            th_lin = torch.linspace(0.0, 2.0 * math.pi, 260, device=self.dev)
            xx, tt = torch.meshgrid(x_lin, th_lin, indexing="ij")
            s01 = (xx + 2.8) / 5.4  # 0 at outer ring -> 1 at tiny inner ring

            # Smooth soap-film profile + fine standing harmonic modes pinned to ZERO at both rings (`sin(n*pi*s01)`)!
            r_base = 0.62 + 2.58 * ((1.0 - s01) ** 1.45)
            fine_harmonics = 0.085 * torch.sin(5.0 * math.pi * s01) * torch.cos(6.0 * tt - 2.6 * t)
            # Giant floppy red wave attempting to enter from outer ring, exponentially rejected before tiny ring!
            rejected_floppy = 0.28 * torch.sin(math.pi * s01 * 0.6) * ((1.0 - s01) ** 2.6) * torch.cos(tt + 1.8 * t)
            rr = r_base + fine_harmonics + rejected_floppy

            fy = rr * torch.cos(tt)
            fz = rr * torch.sin(tt)
            P_film = torch.stack([xx, fy, fz], dim=-1)

            rej_glow = torch.clamp(torch.abs(rejected_floppy) * 3.2, 0.0, 1.0)
            har_glow = torch.clamp(torch.abs(fine_harmonics) * 8.0, 0.0, 1.0)
            film_rgb = torch.stack(
                [
                    0.12 + 0.95 * rej_glow,
                    0.58 + 0.42 * har_glow - 0.25 * rej_glow,
                    0.96 + 0.20 * har_glow - 0.55 * rej_glow,
                ],
                dim=-1,
            )
            self.canvas.render_surface_mesh(
                P_film,
                film_rgb,
                cam,
                emissive_rgb=torch.stack([0.45 * rej_glow, 0.35 * har_glow, 0.45 * har_glow], dim=-1),
                alpha=0.80,
                shininess=90.0,
                fresnel_rgb=(0.45, 0.95, 1.0),
                wire_stride=10,
                wire_rgb=(0.55, 0.95, 1.0),
                wire_boost=0.32,
            )

            # Giant Outer Brushed-Brass Ring & Tiny Inner Brushed-Brass Ring
            P_out, N_out = make_torus_mesh((-2.8, 0.0, 0.0), 3.20, 0.11, 200, 32, self.dev, axis="x")
            P_inn, N_inn = make_torus_mesh((2.6, 0.0, 0.0), 0.62, 0.075, 140, 28, self.dev, axis="x")
            for Pr, Nr in ((P_out, N_out), (P_inn, N_inn)):
                self.canvas.render_surface_mesh(
                    Pr, (0.95, 0.74, 0.24), cam, normals=Nr, emissive_rgb=(0.18, 0.12, 0.02),
                    alpha=0.99, two_sided=False, shininess=105.0, specular_strength=1.4, supersample=(3, 3)
                )
        else:
            # PART 5B (56 - 100%): Live GPU 3D Double-Slit Ripple Tank + Descending Warm Amber Detector Pin!
            u = (prog - 0.56) / 0.44
            det_pin = smootherstep01((u - 0.58) / 0.14)  # Detector touches Slit A at u ~ 0.62!

            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-1.15, elev=0.52, dist=12.2, target=(0.0, 0.5, 0.0), fov_deg=46.0)),
                    (0.45, CameraPose(azim=-0.55, elev=0.26, dist=7.4, target=(1.2, 0.0, 0.2), roll_deg=-3.0, fov_deg=45.0)),
                    (0.72, CameraPose(azim=-0.85, elev=0.22, dist=4.4, target=(-0.6, 1.15, 0.3), roll_deg=2.0, fov_deg=43.0)),
                    (1.00, CameraPose(azim=-0.65, elev=0.36, dist=9.6, target=(0.8, 0.0, 0.2), fov_deg=46.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.010, 0.045, 0.095), nebula_b=(0.02, 0.065, 0.065), star_gain=0.35)

            # 340x340 3D Ripple Tank Surface (`x in [-5.5, 5.5]`, barrier wall at `x = -1.2`, two slits at `y = +-1.15`)
            tx = self.grid_x * 5.6
            ty = self.grid_y * 4.6
            k_wave = 5.4
            omega = 6.2

            # Incoming plane-like standing wave left of barrier (`x < -1.2`)
            w_left = 0.22 * torch.cos(k_wave * tx - omega * t) * torch.exp(-(ty / 3.4) ** 2)

            # Diffracted cylindrical waves from Slit A (`y = +1.15`) and Slit B (`y = -1.15`) right of barrier (`x > -1.2`)
            d1 = torch.sqrt((tx + 1.2) ** 2 + (ty - 1.15) ** 2 + 0.04)
            d2 = torch.sqrt((tx + 1.2) ** 2 + (ty + 1.15) ** 2 + 0.04)
            amp1 = 0.26 / torch.sqrt(d1 + 0.4)
            amp2 = 0.26 / torch.sqrt(d2 + 0.4)

            # Coherent two-slit interference vs pinned single-slit/incoherent sum when warm detector touches Slit A!
            psi_coherent = amp1 * torch.cos(k_wave * d1 - omega * t) + amp2 * torch.cos(k_wave * d2 - omega * t)
            psi_pinned = amp2 * torch.cos(k_wave * d2 - omega * t) + 0.25 * amp1 * torch.cos(k_wave * d1 - omega * t + 2.4)
            w_right = (1.0 - det_pin) * psi_coherent + det_pin * psi_pinned

            gate = torch.sigmoid((tx + 1.2) * 14.0)
            wz = (1.0 - gate) * w_left + gate * w_right
            P_tank = torch.stack([tx, ty, wz], dim=-1)

            crest = torch.clamp(torch.abs(wz) * 3.0, 0.0, 1.0)
            tank_rgb = torch.stack(
                [0.05 + 0.22 * crest, 0.36 + 0.65 * crest, 0.68 + 0.42 * crest], dim=-1
            )
            self.canvas.render_surface_mesh(
                P_tank, tank_rgb, cam, emissive_rgb=torch.stack([0.04 * crest, 0.35 * crest, 0.45 * crest], dim=-1),
                alpha=0.93, shininess=96.0, specular_strength=1.25, fresnel_rgb=(0.35, 0.95, 1.0)
            )

            # Sculpted 3D Brushed-Brass Barrier Wall Segments at `x = -1.2` leaving open slits at `y = +-1.15`
            for y0, y1 in ((-4.6, -1.42), (-0.88, 0.88), (1.42, 4.6)):
                s_b = torch.linspace(y0, y1, 48, device=self.dev)
                c_b = torch.stack([torch.full_like(s_b, -1.2), s_b, torch.full_like(s_b, 0.22)], dim=-1)
                Pb, Nb = make_tube_along_curve(c_b, 0.14, n_around=16)
                self.canvas.render_surface_mesh(Pb, (0.90, 0.70, 0.25), cam, normals=Nb, two_sided=False, shininess=90.0)

            # Back Screen Interference Intensity Pillars at `x = +4.6`!
            sy_scr = torch.linspace(-4.0, 4.0, 160, device=self.dev)
            sd1 = torch.sqrt(torch.tensor(5.8 ** 2, device=self.dev) + (sy_scr - 1.15) ** 2)
            sd2 = torch.sqrt(torch.tensor(5.8 ** 2, device=self.dev) + (sy_scr + 1.15) ** 2)
            env_g = torch.exp(-(sy_scr / 2.85) ** 2)
            i_coh = env_g * (torch.cos(0.5 * k_wave * (sd1 - sd2)) ** 2)
            i_inc = 0.55 * ( torch.exp(-((sy_scr - 1.15) / 1.1) ** 2) + torch.exp(-((sy_scr + 1.15) / 1.1) ** 2) )
            intensity = (1.0 - det_pin) * i_coh + det_pin * i_inc

            zz_s = torch.linspace(0.0, 1.0, 40, device=self.dev)
            yy_g, zz_g = torch.meshgrid(sy_scr, zz_s, indexing="ij")
            h_bar = 0.12 + 2.35 * intensity.unsqueeze(-1)
            P_scr = torch.stack([torch.full_like(yy_g, 4.65), yy_g, zz_g * h_bar], dim=-1)
            col_int = intensity.unsqueeze(-1).expand(160, 40)
            scr_rgb = torch.stack(
                [
                    0.12 + 0.95 * det_pin * col_int,
                    0.95 * (1.0 - 0.35 * det_pin) * col_int + 0.15,
                    0.55 * (1.0 - 0.5 * det_pin) * col_int + 0.15,
                ],
                dim=-1,
            )
            self.canvas.render_surface_mesh(
                P_scr, scr_rgb, cam, emissive_rgb=scr_rgb * 0.55, alpha=0.92, shininess=70.0
            )

            # Warm 3D Amber Detector Probe descending onto Slit A (`(-1.2, +1.15)`)!
            z_probe = 2.4 - 2.15 * det_pin
            p_curve = torch.stack(
                [
                    torch.full((32,), -1.2, device=self.dev),
                    torch.full((32,), 1.15, device=self.dev),
                    torch.linspace(z_probe + 1.5, z_probe, 32, device=self.dev),
                ],
                dim=-1,
            )
            r_pr = torch.linspace(0.14, 0.04, 32, device=self.dev)
            Pp, Np = make_tube_along_curve(p_curve, r_pr, n_around=20)
            self.canvas.render_surface_mesh(
                Pp, (1.0, 0.55, 0.12), cam, normals=Np,
                emissive_rgb=(0.85 * det_pin, 0.35 * det_pin, 0.05), alpha=0.98, two_sided=False, shininess=95.0, supersample=(4, 4)
            )

    # -----------------------------------------------------------------------
    # SCENE 06: Silk Tablecloth Gravity, Orbiting Earth/Moon & Curved Starlight
    # -----------------------------------------------------------------------
    def _render_scene06(self, t: float, dur: float, prog: float) -> None:
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=-0.95, elev=0.58, dist=13.2, target=(0.0, 0.0, -0.4), fov_deg=47.0)),
                (0.38, CameraPose(azim=-0.15, elev=0.17, dist=6.4, target=(0.0, 0.0, -0.5), roll_deg=-4.0, fov_deg=45.0)),
                (0.72, CameraPose(azim=0.75, elev=0.14, dist=4.6, target=(0.6, 0.4, -0.35), roll_deg=3.0, fov_deg=44.0)),
                (1.00, CameraPose(azim=1.45, elev=0.26, dist=7.8, target=(0.0, 0.0, -0.4), fov_deg=46.0)),
            ],
            prog,
        )
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.015, 0.048, 0.115), nebula_b=(0.055, 0.032, 0.085))

        # 1. Drum-tight 340x340 Silk Tablecloth depressed & radially strained by central Golden Sun!
        press = smoothstep01(prog / 0.18)
        gx = self.grid_x * 8.2
        gy = self.grid_y * 8.2
        rr = torch.sqrt(gx * gx + gy * gy + 0.35)
        # Radial inward thread pull (`pins and pulls the threads tighter all around itself`)
        pull = 1.0 - 0.24 * press / (rr + 0.65)
        px = gx * pull
        py = gy * pull
        pz = -2.35 * press / torch.sqrt(gx * gx + gy * gy + 1.15)
        P_silk = torch.stack([px, py, pz], dim=-1)

        strain = press * torch.exp(-rr * 0.42)
        silk_rgb = torch.stack(
            [0.06 + 0.55 * strain, 0.28 + 0.52 * strain, 0.58 + 0.35 * strain], dim=-1
        )
        self.canvas.render_surface_mesh(
            P_silk, silk_rgb, cam,
            emissive_rgb=torch.stack([0.22 * strain, 0.18 * strain, 0.05 * strain], dim=-1),
            alpha=0.90, shininess=72.0, wire_stride=7, wire_rgb=(0.38, 0.88, 1.0), wire_boost=0.42
        )

        # 2. Blazing Volumetric 3D Golden Sun Sphere nestled into the central silk funnel
        sun_z = -2.18 * press + 0.85
        Psun, _, _ = make_sphere_mesh((0.0, 0.0, sun_z), 0.82, 90, 60, self.dev)
        self.canvas.render_surface_mesh(
            Psun, (1.0, 0.78, 0.22), cam, emissive_rgb=(1.45, 0.92, 0.24), alpha=0.99, two_sided=False, shininess=40.0
        )

        # 3. Blue Ocean Earth + Tiny Moon rolling smoothly along the strained geodesic bowl!
        orb_r = 3.35
        orb_a = 0.85 * t
        ex, ey = orb_r * math.cos(orb_a), orb_r * math.sin(orb_a)
        ez = -2.35 * press / math.sqrt(orb_r * orb_r + 1.15) + 0.28
        P_earth, uu_e, vv_e = make_sphere_mesh((ex, ey, ez), 0.27, 64, 44, self.dev)
        land = (torch.sin(3.0 * uu_e + 1.5 * t) * torch.cos(2.5 * vv_e)) > 0.22
        e_rgb = torch.stack(
            [
                torch.where(land, 0.18, 0.08),
                torch.where(land, 0.68, 0.44),
                torch.where(land, 0.28, 0.96),
            ],
            dim=-1,
        )
        self.canvas.render_surface_mesh(P_earth, e_rgb, cam, two_sided=False, shininess=75.0, fresnel_rgb=(0.55, 0.88, 1.0))

        # Glowing Earth geodesic orbit ribbon
        th_o = torch.linspace(0.0, 2.0 * math.pi, 180, device=self.dev)
        Po, No = make_tube_along_curve(
            torch.stack([orb_r * torch.cos(th_o), orb_r * torch.sin(th_o), torch.full_like(th_o, ez - 0.18)], dim=-1),
            0.025, n_around=12, closed=True
        )
        self.canvas.render_surface_mesh(Po, (0.30, 0.85, 1.0), cam, normals=No, emissive_rgb=(0.12, 0.45, 0.65), two_sided=False)

        # 4. Sculpted Golden Beam of Starlight visibly curving along the strained silk weave (`prog > 0.52`)!
        if prog > 0.46:
            ray_w = smoothstep01((prog - 0.46) / 0.14)
            sx_l = torch.linspace(-7.5, 7.5, 220, device=self.dev)
            b_imp = 1.65
            # Relativistic deflection curve around Sun (`y` bends inward near `x = 0` and dips along funnel!)
            defl = -0.95 * press * (torch.atan(sx_l / b_imp) + 0.5 * math.pi) / math.pi
            sy_l = b_imp + defl
            sz_l = -2.35 * press / torch.sqrt(sx_l * sx_l + sy_l * sy_l + 1.15) + 0.35
            Pr, Nr = make_tube_along_curve(torch.stack([sx_l, sy_l, sz_l], dim=-1), 0.048 * ray_w, n_around=16)
            # Travelling photon pulse along curved ray
            ph_pos = ((t * 5.2) % 15.0) - 7.5
            pulse = (0.35 + 1.35 * torch.exp(-((sx_l - ph_pos) ** 2) / 1.1)).view(-1, 1, 1).expand(220, 16, 1)
            r_col = torch.cat([1.15 * pulse, 0.92 * pulse, 0.38 * pulse], dim=-1) * ray_w
            self.canvas.render_surface_mesh(Pr, r_col, cam, normals=Nr, emissive_rgb=r_col * 0.75, two_sided=False)

    # -----------------------------------------------------------------------
    # SCENE 07: Continuous Cosmic Pullback — Solar Campfire Bubble -> Galaxy Trampoline
    # -----------------------------------------------------------------------
    def _render_scene07(self, t: float, dur: float, prog: float) -> None:
        # Logarithmic zoom-out from tight inside the blazing Solar System (`dist=1.35`) to full Spiral Galaxy (`dist=14.2`)!
        pose = interpolate_camera(
            [
                (0.00, CameraPose(azim=0.25, elev=0.24, dist=1.45, target=(2.4, 0.0, 0.05), fov_deg=46.0)),
                (0.38, CameraPose(azim=0.95, elev=0.20, dist=1.85, target=(2.4, 0.0, 0.05), roll_deg=4.0, fov_deg=46.0)),
                (0.68, CameraPose(azim=1.75, elev=0.36, dist=9.8, target=(0.4, 0.0, -0.1), roll_deg=0.0, fov_deg=47.0)),
                (1.00, CameraPose(azim=2.45, elev=0.30, dist=13.2, target=(0.0, 0.0, -0.15), fov_deg=47.0)),
            ],
            prog,
        )
        cam = CameraMatrix(pose, self.dev)
        self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.014, 0.052, 0.11), nebula_b=(0.025, 0.075, 0.075))

        # 1. Emerald Cosmic Trampoline Tablecloth cradling the entire Spiral Galaxy!
        gal_vis = smoothstep01((prog - 0.34) / 0.22)
        if gal_vis > 0.01:
            gx = self.grid_x * 8.6
            gy = self.grid_y * 8.6
            rr = torch.sqrt(gx * gx + gy * gy + 0.5)
            # Logarithmic trampoline tension bowl (`V(r) ~ v_flat^2 ln(r)` -> flat orbital speeds!)
            gz = -0.85 + 0.42 * torch.log(rr / 2.5 + 0.35)
            P_tramp = torch.stack([gx, gy, gz], dim=-1)
            self.canvas.render_surface_mesh(
                P_tramp,
                (0.05, 0.36 * gal_vis, 0.32 * gal_vis),
                cam,
                alpha=0.76 * gal_vis,
                shininess=64.0,
                fresnel_rgb=(0.25, 0.98, 0.78),
                wire_stride=8,
                wire_rgb=(0.22, 0.95, 0.76),
                wire_boost=0.38 * gal_vis,
                write_depth=False,
            )

        # 2. 46,000-Star Spiral Galaxy (with our Solar System nestled at `(2.4, 0.0, 0.05)` in one spiral arm!)
        g_pts = self._spinning_galaxy_pts(t * 0.45, omega_flat=0.26)
        if gal_vis > 0.02:
            self.canvas.render_particles(g_pts, self.gal_rgb * (0.25 + 0.85 * gal_vis), self.gal_sz, cam, focus_dist=pose.dist)

        # 3. Our Blazing Solar System + Warm Golden "Roaring Campfire" Local Motion Bubble at `(2.4, 0.0, 0.05)`!
        sol_c = (2.4, 0.0, 0.05)
        Psun, _, _ = make_sphere_mesh(sol_c, 0.16, 56, 40, self.dev)
        self.canvas.render_surface_mesh(
            Psun, (1.0, 0.82, 0.25), cam, emissive_rgb=(1.75, 1.10, 0.28), two_sided=False
        )

        # Fast-whipping inner planets (Mercury, Venus, Earth, Mars) inside the campfire bubble
        for idx_p, (rp, spd, pcol, psz) in enumerate((
            (0.28, 4.6, (0.85, 0.78, 0.72), 0.028),
            (0.42, 3.3, (0.98, 0.82, 0.48), 0.036),
            (0.58, 2.5, (0.22, 0.68, 1.00), 0.042),
            (0.74, 1.8, (0.95, 0.42, 0.25), 0.032),
        )):
            pa = idx_p * 1.4 + spd * t
            px, py = sol_c[0] + rp * math.cos(pa), sol_c[1] + rp * math.sin(pa)
            Pp, _, _ = make_sphere_mesh((px, py, sol_c[2]), psz, 32, 24, self.dev)
            self.canvas.render_surface_mesh(Pp, pcol, cam, emissive_rgb=(pcol[0]*0.3, pcol[1]*0.3, pcol[2]*0.3), two_sided=False)
            if prog < 0.65:
                th_p = torch.linspace(0.0, 2.0 * math.pi, 96, device=self.dev)
                Po, No = make_tube_along_curve(
                    torch.stack([sol_c[0] + rp * torch.cos(th_p), sol_c[1] + rp * torch.sin(th_p), torch.full_like(th_p, sol_c[2])], dim=-1),
                    0.007, n_around=8, closed=True
                )
                self.canvas.render_surface_mesh(Po, pcol, cam, normals=No, emissive_rgb=(pcol[0]*0.35, pcol[1]*0.35, pcol[2]*0.35), two_sided=False)

        # Translucent Warm Amber-Gold "Local Campfire Motion Bubble" Shell (`R = 0.88`)
        bub_alpha = 0.55 * (1.0 - 0.55 * gal_vis)
        Pbub, _, _ = make_sphere_mesh(sol_c, 0.88, 84, 56, self.dev)
        self.canvas.render_surface_mesh(
            Pbub,
            (0.95, 0.52, 0.12),
            cam,
            emissive_rgb=(0.42, 0.20, 0.03),
            alpha=bub_alpha,
            shininess=80.0,
            fresnel_rgb=(1.0, 0.72, 0.25),
            fresnel_strength=0.95,
            write_depth=False,
        )

    # -----------------------------------------------------------------------
    # SCENE 08: Fast Bullet Cluster Ghost Crash vs. Slow Dwarf Pleat Bounce
    # -----------------------------------------------------------------------
    def _render_scene08(self, t: float, dur: float, prog: float) -> None:
        if prog < 0.68:
            # PART 8A (0 - 68%): Blistering-Speed Bullet Cluster Head-On Collision!
            u = prog / 0.68
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-1.15, elev=0.36, dist=12.8, target=(0.0, 0.0, 0.0), fov_deg=47.0)),
                    (0.48, CameraPose(azim=-0.35, elev=0.16, dist=7.6, target=(0.0, 0.0, 0.2), roll_deg=-4.0, fov_deg=45.0)),
                    (1.00, CameraPose(azim=0.55, elev=0.28, dist=9.8, target=(0.0, 0.0, 0.0), roll_deg=0.0, fov_deg=46.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.018, 0.042, 0.115), nebula_b=(0.085, 0.025, 0.065))

            # Separation trajectory: clusters start at x = +-4.5, smash through x = 0 at u = 0.36, exit to x = +-3.8!
            sep = 4.6 - 13.0 * u  # +4.6 -> 0 at u=0.35 -> -8.4 (ghosted straight through!)
            x_pleat_L = -0.55 * sep   # Left cluster starts at -2.5, crosses 0, exits to +4.6!
            x_pleat_R = +0.55 * sep   # Right cluster starts at +2.5, crosses 0, exits to -4.6!

            # 1. Cosmic Tablecloth with TWO Crisp Springy Sapphire Soliton Pleats slicing through each other like ghosts!
            gx = self.grid_x * 8.4
            gy = self.grid_y * 6.5
            rL2 = (gx - x_pleat_L) ** 2 + gy ** 2
            rR2 = (gx - x_pleat_R) ** 2 + gy ** 2
            pleat_L = 1.45 * torch.exp(-rL2 / 1.45)
            pleat_R = 1.45 * torch.exp(-rR2 / 1.45)
            gz = -0.85 + pleat_L + pleat_R
            P_cloth = torch.stack([gx, gy, gz], dim=-1)

            pl_glow = torch.clamp((pleat_L + pleat_R) / 1.6, 0.0, 1.2)
            c_rgb = torch.stack([0.06 + 0.18 * pl_glow, 0.28 + 0.62 * pl_glow, 0.58 + 0.55 * pl_glow], dim=-1)
            self.canvas.render_surface_mesh(
                P_cloth, c_rgb, cam,
                emissive_rgb=torch.stack([0.05 * pl_glow, 0.28 * pl_glow, 0.52 * pl_glow], dim=-1),
                alpha=0.84, shininess=78.0, wire_stride=7, wire_rgb=(0.35, 0.88, 1.0), wire_boost=0.40
            )

            # 2. Collisionless White-Gold Cluster Galaxies/Stars riding straight through with the two fabric pleats!
            star_cx = torch.where(self.cl_star_side < 0, x_pleat_L, x_pleat_R)
            star_pts = self.cl_star_loc + torch.stack([star_cx, torch.zeros_like(star_cx), torch.full_like(star_cx, 0.55)], dim=-1)
            star_rgb = torch.tensor([1.15, 0.98, 0.78], device=self.dev).expand_as(star_pts) * 0.85
            self.canvas.render_particles(star_pts, star_rgb, 1.7, cam)

            # 3. Hot X-Ray Gas Clouds (`26,000` crimson-orange particles) slamming into a bow-shock pancake stuck in the middle!
            hit = smoothstep01((u - 0.26) / 0.18)
            gas_cx_free = torch.where(self.cl_gas_side < 0, x_pleat_L, x_pleat_R)
            gas_cx = (1.0 - 0.86 * hit) * gas_cx_free  # Gas stalls near x = 0!
            # Compress along X into bow-shock pancake and flare outward in Y/Z!
            gx_p = gas_cx + self.cl_gas_loc[:, 0] * (1.0 - 0.58 * hit)
            gy_p = self.cl_gas_loc[:, 1] * (1.0 + 0.65 * hit)
            gz_p = 0.55 + self.cl_gas_loc[:, 2] * (1.0 + 0.55 * hit)
            gas_pts = torch.stack([gx_p, gy_p, gz_p], dim=-1)
            shock_heat = hit * torch.exp(-(gx_p ** 2) / 1.2)
            gas_rgb = torch.stack(
                [
                    0.85 + 0.65 * shock_heat,
                    0.22 + 0.45 * shock_heat,
                    0.28 - 0.12 * shock_heat,
                ],
                dim=-1,
            ) * 0.55
            self.canvas.render_particles(gas_pts, gas_rgb, 2.4 + 1.4 * shock_heat, cam)
        else:
            # PART 8B (68 - 100%): Gentle Slow-Drift Dwarf Galaxies — Springy Fabric Pleats Bounce while Stars Coast Free!
            u = (prog - 0.68) / 0.32
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-0.75, elev=0.34, dist=9.6, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                    (0.55, CameraPose(azim=0.10, elev=0.22, dist=6.2, target=(0.0, 0.0, 0.1), fov_deg=44.0)),
                    (1.00, CameraPose(azim=0.75, elev=0.30, dist=8.4, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.022, 0.038, 0.105), nebula_b=(0.065, 0.028, 0.115))

            # Pleats approach gently, compress at x = +-0.85 around u = 0.42, and REBOUND back outward!
            pleat_d = 0.85 + 2.8 * abs(u - 0.42) / 0.58
            # Meanwhile stars coast gently past each other (`-2.4 -> +2.2`) leaving dark-matter-free dwarf galaxies!
            star_d = 2.4 - 4.8 * u

            gx = self.grid_x * 7.5
            gy = self.grid_y * 5.8
            pL = 1.25 * torch.exp(-((gx + pleat_d) ** 2 + gy ** 2) / 1.35)
            pR = 1.25 * torch.exp(-((gx - pleat_d) ** 2 + gy ** 2) / 1.35)
            P_cloth = torch.stack([gx, gy, -0.75 + pL + pR], dim=-1)
            pg = torch.clamp((pL + pR) / 1.3, 0.0, 1.2)
            self.canvas.render_surface_mesh(
                P_cloth,
                torch.stack([0.28 + 0.48 * pg, 0.16 + 0.25 * pg, 0.55 + 0.55 * pg], dim=-1),
                cam,
                emissive_rgb=torch.stack([0.28 * pg, 0.10 * pg, 0.48 * pg], dim=-1),
                alpha=0.86, shininess=75.0, wire_stride=7, wire_rgb=(0.75, 0.52, 1.0), wire_boost=0.38
            )

            # Golden dwarf-galaxy stars coasting onward free of their bounced fabric pleats!
            scx = torch.where(self.cl_star_side < 0, -star_d, star_d)
            s_pts = self.cl_star_loc * 0.65 + torch.stack([scx, torch.zeros_like(scx), torch.full_like(scx, 0.45)], dim=-1)
            s_rgb = torch.tensor([1.20, 0.92, 0.45], device=self.dev).expand_as(s_pts) * 0.78
            self.canvas.render_particles(s_pts[::2], s_rgb[::2], 1.8, cam)

    # -----------------------------------------------------------------------
    # SCENE 09: 3D Ribbon Braids -> Whole Cosmic Tapestry -> Cislunar Moon Probe
    # -----------------------------------------------------------------------
    def _render_scene09(self, t: float, dur: float, prog: float) -> None:
        if prog < 0.34:
            # Beat A (0 - 34%): Close Orbit Around 3 Gleaming Sculpted 3D Braided Matter Ribbons!
            u = prog / 0.34
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-0.65, elev=0.22, dist=3.2, target=(0.0, 0.0, 0.0), roll_deg=-6.0, fov_deg=44.0)),
                    (1.00, CameraPose(azim=0.95, elev=0.30, dist=6.4, target=(0.0, 0.0, 0.0), roll_deg=0.0, fov_deg=46.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.018, 0.052, 0.12), nebula_b=(0.075, 0.032, 0.095))

            s = torch.linspace(-3.6, 3.6, 320, device=self.dev)
            colors = ((0.22, 0.88, 1.0), (1.0, 0.80, 0.26), (0.98, 0.42, 0.68))
            for k in range(3):
                ph = k * (2.0 * math.pi / 3.0) + 0.85 * t
                bx = s
                by = 0.68 * torch.sin(1.85 * s + ph)
                bz = 0.68 * torch.cos(1.85 * s + 0.5 * ph)
                Pb, Nb = make_tube_along_curve(torch.stack([bx, by, bz], dim=-1), 0.145, n_around=28)
                col = colors[k]
                self.canvas.render_surface_mesh(
                    Pb, col, cam, normals=Nb, emissive_rgb=(col[0]*0.28, col[1]*0.28, col[2]*0.28),
                    alpha=0.99, two_sided=False, shininess=98.0, specular_strength=1.35, supersample=(4, 4)
                )
        elif prog < 0.66:
            # Beat B (34 - 66%): Grand Unified Tapestry — Stretched Fabric + Twin-Wing Cosmic Hourglass + Galaxies!
            u = (prog - 0.34) / 0.32
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=0.85, elev=0.22, dist=7.2, target=(0.0, 0.0, 0.0), fov_deg=46.0)),
                    (1.00, CameraPose(azim=1.85, elev=0.32, dist=12.4, target=(0.0, 0.0, 0.0), fov_deg=48.0)),
                ],
                u,
            )
            self._render_hourglass_core(t, flip_amt=1.0, cam_pose=pose)
        else:
            # Beat C (66 - 100%): Upcoming Cislunar Earth-Moon Saddle-Point Experiment & 6 Companion Chapters!
            u = (prog - 0.66) / 0.34
            pose = interpolate_camera(
                [
                    (0.00, CameraPose(azim=-0.85, elev=0.26, dist=7.8, target=(-0.6, 0.0, 0.0), fov_deg=45.0)),
                    (1.00, CameraPose(azim=0.25, elev=0.18, dist=4.6, target=(0.2, 0.0, 0.1), fov_deg=44.0)),
                ],
                u,
            )
            cam = CameraMatrix(pose, self.dev)
            self.canvas.clear_and_render_sky(cam, t, nebula_a=(0.015, 0.048, 0.115), nebula_b=(0.045, 0.035, 0.095))

            # Cislunar gravitational saddle sheet between Blue Earth (`x = -2.4`) and Cratered Moon (`x = +2.4`)
            gx = self.grid_x * 6.2
            gy = self.grid_y * 4.8
            rE = torch.sqrt((gx + 2.4) ** 2 + gy ** 2 + 0.55)
            rM = torch.sqrt((gx - 2.4) ** 2 + gy ** 2 + 0.35)
            gz = -0.35 - 1.55 / rE - 0.58 / rM
            self.canvas.render_surface_mesh(
                torch.stack([gx, gy, gz], dim=-1),
                (0.06, 0.28, 0.52),
                cam,
                alpha=0.84,
                shininess=68.0,
                wire_stride=8,
                wire_rgb=(0.35, 0.88, 1.0),
                wire_boost=0.38,
            )

            # Blue Ocean Earth at `(-2.4, 0, 0.35)`
            Pe, uue, vve = make_sphere_mesh((-2.4, 0.0, 0.35), 0.72, 80, 56, self.dev)
            land = (torch.sin(3.0 * uue + 0.35 * t) * torch.cos(2.5 * vve)) > 0.20
            e_rgb = torch.stack([torch.where(land, 0.16, 0.07), torch.where(land, 0.65, 0.42), torch.where(land, 0.26, 0.96)], dim=-1)
            self.canvas.render_surface_mesh(Pe, e_rgb, cam, two_sided=False, shininess=78.0, fresnel_rgb=(0.55, 0.88, 1.0))

            # Cratered Silver Moon at `(+2.4, 0, 0.25)`
            Pm, uum, vvm = make_sphere_mesh((2.4, 0.0, 0.25), 0.34, 60, 42, self.dev)
            crat = 0.62 + 0.16 * torch.sin(7.0 * uum) * torch.cos(6.0 * vvm)
            self.canvas.render_surface_mesh(Pm, torch.stack([crat, crat, crat * 1.04], dim=-1), cam, two_sided=False, shininess=28.0)

            # Sleek Golden Cislunar Micro-Probe hovering right at the zero-gravity saddle (`x = +0.85`)!
            probe_pos = (0.85, 0.15 * math.sin(t * 0.9), 0.22 + 0.06 * math.cos(t * 1.1))
            Pp, _, _ = make_sphere_mesh(probe_pos, 0.11, 36, 26, self.dev)
            self.canvas.render_surface_mesh(Pp, (1.0, 0.82, 0.26), cam, emissive_rgb=(0.65, 0.48, 0.12), two_sided=False, shininess=110.0)
            # Solar wings on the cislunar probe
            sw = torch.linspace(-0.48, 0.48, 28, device=self.dev)
            Pw, Nw = make_tube_along_curve(
                torch.stack([torch.full_like(sw, probe_pos[0]), probe_pos[1] + sw, torch.full_like(sw, probe_pos[2])], dim=-1),
                0.032, n_around=12
            )
            self.canvas.render_surface_mesh(Pw, (0.25, 0.72, 1.0), cam, normals=Nw, emissive_rgb=(0.12, 0.35, 0.65), two_sided=False)
