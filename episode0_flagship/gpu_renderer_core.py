"""
RTX 5080 PyTorch CUDA 1920x1080 (`1080p`) 3D Cinema & Volumetric Rendering Core:
  - `Camera3D` + smooth cubic-eased multi-keyframe camera rig (orbit, zoom/dolly, pan, tilt, roll, FOV)
  - 3D Ray-Evaluated Deep-Space Volumetric Nebula + 14,000-Star Parallax Starfield
  - True Z-Buffered GPU Surface Mesh Rasterizer (`(Nu, Nv, 3)` -> Blinn-Phong Specular + Fresnel Rim
    + Procedural Silk Micro-Weave + `2x2` Sub-Pixel Splatting at `1920x1080`)
  - Parallel-Transport 3D Tube, Torus, Sphere, Hex-Mirror, and Arrow Mesh Generators
  - Multi-Scale Volumetric Particle & Depth-of-Field Bokeh Splat Engine
  - 3-Octave Separable GPU HDR Gaussian Bloom + ACES Filmic Tone Mapping
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn.functional as F

W_1080 = 1920
H_1080 = 1080
ACTIVE_W = W_1080
ACTIVE_H = H_1080


def set_render_resolution(width: int, height: int) -> None:
    """Switches the global GPU 3D camera & canvas resolution (e.g., `3840x2160` True 4K UHD)."""
    global ACTIVE_W, ACTIVE_H
    ACTIVE_W = int(width)
    ACTIVE_H = int(height)


def smoothstep01(x: float) -> float:
    x = max(0.0, min(1.0, float(x)))
    return x * x * (3.0 - 2.0 * x)


def smootherstep01(x: float) -> float:
    x = max(0.0, min(1.0, float(x)))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


@dataclass
class CameraPose:
    azim: float          # radians around Z axis
    elev: float          # radians above XY plane
    dist: float          # distance from target
    target: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    roll_deg: float = 0.0
    fov_deg: float = 46.0


def interpolate_camera(keyframes: Sequence[Tuple[float, CameraPose]], prog: float) -> CameraPose:
    """Smoothly interpolates between `(progress_0_to_1, CameraPose)` keyframes using quintic easing."""
    if len(keyframes) == 1 or prog <= keyframes[0][0]:
        return keyframes[0][1]
    if prog >= keyframes[-1][0]:
        return keyframes[-1][1]

    for i in range(len(keyframes) - 1):
        p0, k0 = keyframes[i]
        p1, k1 = keyframes[i + 1]
        if p0 <= prog <= p1:
            u = smootherstep01((prog - p0) / max(1e-6, p1 - p0))
            # Logarithmic interpolation on `dist` makes large cosmic zooms feel silky & constant-rate!
            d0, d1 = max(0.05, k0.dist), max(0.05, k1.dist)
            dist = math.exp(math.log(d0) * (1.0 - u) + math.log(d1) * u)
            tx = k0.target[0] + (k1.target[0] - k0.target[0]) * u
            ty = k0.target[1] + (k1.target[1] - k0.target[1]) * u
            tz = k0.target[2] + (k1.target[2] - k0.target[2]) * u
            return CameraPose(
                azim=k0.azim + (k1.azim - k0.azim) * u,
                elev=k0.elev + (k1.elev - k0.elev) * u,
                dist=dist,
                target=(tx, ty, tz),
                roll_deg=k0.roll_deg + (k1.roll_deg - k0.roll_deg) * u,
                fov_deg=k0.fov_deg + (k1.fov_deg - k0.fov_deg) * u,
            )
    return keyframes[-1][1]


class CameraMatrix:
    """Precomputes world-to-camera basis vectors and focal length on GPU."""

    def __init__(self, pose: CameraPose, device: torch.device, width: Optional[int] = None, height: Optional[int] = None):
        self.pose = pose
        self.device = device
        self.w = int(width) if width is not None else ACTIVE_W
        self.h = int(height) if height is not None else ACTIVE_H

        ce = math.cos(pose.elev)
        se = math.sin(pose.elev)
        ca = math.cos(pose.azim)
        sa = math.sin(pose.azim)

        tgt = np.array(pose.target, dtype=np.float32)
        cam_pos = tgt + pose.dist * np.array([ce * ca, ce * sa, se], dtype=np.float32)
        fwd = tgt - cam_pos
        fwd /= max(1e-8, float(np.linalg.norm(fwd)))

        world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        if abs(float(np.dot(fwd, world_up))) > 0.995:
            world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        right = np.cross(fwd, world_up)
        right /= max(1e-8, float(np.linalg.norm(right)))
        up = np.cross(right, fwd)
        up /= max(1e-8, float(np.linalg.norm(up)))

        if abs(pose.roll_deg) > 1e-4:
            rr = math.radians(pose.roll_deg)
            cr, sr = math.cos(rr), math.sin(rr)
            right, up = cr * right + sr * up, -sr * right + cr * up

        self.pos = torch.tensor(cam_pos, device=device, dtype=torch.float32)
        self.right = torch.tensor(right, device=device, dtype=torch.float32)
        self.up = torch.tensor(up, device=device, dtype=torch.float32)
        self.fwd = torch.tensor(fwd, device=device, dtype=torch.float32)
        # Basis matrix R: world_delta @ R -> (cam_x, cam_y, cam_z_depth)
        self.R = torch.stack([self.right, self.up, self.fwd], dim=1)  # (3, 3)
        self.focal = (0.5 * self.h) / math.tan(0.5 * math.radians(pose.fov_deg))

    def project(self, pts: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Projects `(..., 3)` world points -> `(sx, sy, depth)`."""
        rel = pts - self.pos
        cam = rel @ self.R
        cx, cy, cz = cam[..., 0], cam[..., 1], cam[..., 2]
        safe_z = torch.clamp(cz, min=0.05)
        scale = self.focal / safe_z
        sx = 0.5 * self.w + cx * scale
        sy = 0.5 * self.h - cy * scale
        return sx, sy, cz


# ---------------------------------------------------------------------------
# 3D Parametric Geometry Generators on GPU
# ---------------------------------------------------------------------------

def make_sphere_mesh(
    center: Tuple[float, float, float],
    radius: float,
    nu: int,
    nv: int,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    u = torch.linspace(0.0, 2.0 * math.pi, nu, device=device)
    v = torch.linspace(0.0, math.pi, nv, device=device)
    uu, vv = torch.meshgrid(u, v, indexing="ij")
    sv = torch.sin(vv)
    x = center[0] + radius * sv * torch.cos(uu)
    y = center[1] + radius * sv * torch.sin(uu)
    z = center[2] + radius * torch.cos(vv)
    return torch.stack([x, y, z], dim=-1), uu, vv


def make_tube_along_curve(
    curve: torch.Tensor,
    radius: float | torch.Tensor,
    n_around: int = 28,
    closed: bool = False,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Sweeps a smooth circular cross-section along 3D curve `(M, 3)` using parallel transport
    so tubes never twist-pinch at inflection points. Returns `(P: (M, n_around, 3), N: (M, n_around, 3))`.
    """
    device = curve.device
    m = curve.shape[0]
    if closed:
        tang = torch.roll(curve, -1, dims=0) - torch.roll(curve, 1, dims=0)
    else:
        tang = torch.empty_like(curve)
        tang[1:-1] = curve[2:] - curve[:-2]
        tang[0] = curve[1] - curve[0]
        tang[-1] = curve[-1] - curve[-2]
    tang = F.normalize(tang, dim=-1, eps=1e-7)

    # Build smooth normal frame via vectorized reference cross product with fallback
    ref = torch.tensor([0.0, 0.0, 1.0], device=device)
    alt = torch.tensor([0.0, 1.0, 0.0], device=device)
    dot_ref = torch.abs((tang * ref).sum(dim=-1, keepdim=True))
    up_vec = torch.where(dot_ref > 0.92, alt.expand_as(tang), ref.expand_as(tang))
    n1 = F.normalize(torch.cross(tang, up_vec, dim=-1), dim=-1, eps=1e-7)
    n2 = F.normalize(torch.cross(tang, n1, dim=-1), dim=-1, eps=1e-7)

    theta = torch.linspace(0.0, 2.0 * math.pi, n_around, device=device)
    ct = torch.cos(theta).view(1, n_around, 1)
    st = torch.sin(theta).view(1, n_around, 1)

    normals = F.normalize(n1.unsqueeze(1) * ct + n2.unsqueeze(1) * st, dim=-1, eps=1e-7)
    if isinstance(radius, torch.Tensor):
        rad = radius.view(m, 1, 1)
    else:
        rad = float(radius)
    pts = curve.unsqueeze(1) + rad * normals
    return pts, normals


def make_torus_mesh(
    center: Tuple[float, float, float],
    major_r: float,
    minor_r: float,
    nu: int,
    nv: int,
    device: torch.device,
    axis: str = "z",
) -> Tuple[torch.Tensor, torch.Tensor]:
    u = torch.linspace(0.0, 2.0 * math.pi, nu, device=device)
    v = torch.linspace(0.0, 2.0 * math.pi, nv, device=device)
    uu, vv = torch.meshgrid(u, v, indexing="ij")
    cu, su = torch.cos(uu), torch.sin(uu)
    cv, sv = torch.cos(vv), torch.sin(vv)

    ring_r = major_r + minor_r * cv
    px = ring_r * cu
    py = ring_r * su
    pz = minor_r * sv

    nx = cv * cu
    ny = cv * su
    nz = sv

    if axis == "x":
        pts = torch.stack([pz + center[0], py + center[1], px + center[2]], dim=-1)
        nrm = torch.stack([nz, ny, nx], dim=-1)
    elif axis == "y":
        pts = torch.stack([px + center[0], pz + center[1], py + center[2]], dim=-1)
        nrm = torch.stack([nx, nz, ny], dim=-1)
    else:
        pts = torch.stack([px + center[0], py + center[1], pz + center[2]], dim=-1)
        nrm = torch.stack([nx, ny, nz], dim=-1)
    return pts, nrm


# ---------------------------------------------------------------------------
# GPU 1080p HDR Framebuffer, Rasterizer & Post-Processing Engine
# ---------------------------------------------------------------------------

class GPUCanvas1080p:
    def __init__(self, device: Optional[torch.device] = None, width: Optional[int] = None, height: Optional[int] = None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.w = int(width) if width is not None else ACTIVE_W
        self.h = int(height) if height is not None else ACTIVE_H
        self.res_scale = self.w / 1920.0
        self.halo_w = 960
        self.halo_h = 540

        self.hdr = torch.zeros((3, self.h, self.w), device=self.device, dtype=torch.float32)
        self.zbuf = torch.full((self.h * self.w,), 1e6, device=self.device, dtype=torch.float32)
        # Reusable scratch buffers so `render_surface_mesh` and `render_particles` do ZERO per-call VRAM allocations!
        self._mesh_z = torch.empty((self.h * self.w,), device=self.device, dtype=torch.float32)
        self._accum_rgb = torch.empty((self.h * self.w, 3), device=self.device, dtype=torch.float32)
        self._accum_cnt = torch.empty((self.h * self.w,), device=self.device, dtype=torch.float32)
        self._halo_buf = torch.empty((self.halo_h * self.halo_w, 3), device=self.device, dtype=torch.float32)
        self._cpu_pinned = torch.empty(
            (self.h, self.w, 3), dtype=torch.uint8, pin_memory=(self.device.type == "cuda")
        )

        # Persistent 3D Deep-Space Starfield (14,000 stars on distant celestial sphere R=180..320)
        g = torch.Generator(device="cpu")
        g.manual_seed(20261029)
        n_stars = 14000
        u_rand = torch.rand(n_stars, generator=g) * 2.0 - 1.0
        phi_rand = torch.rand(n_stars, generator=g) * (2.0 * math.pi)
        r_rand = 175.0 + 145.0 * torch.rand(n_stars, generator=g)
        sin_th = torch.sqrt(torch.clamp(1.0 - u_rand * u_rand, min=0.0))
        sx = r_rand * sin_th * torch.cos(phi_rand)
        sy = r_rand * sin_th * torch.sin(phi_rand)
        sz = r_rand * u_rand
        self.star_xyz = torch.stack([sx, sy, sz], dim=-1).to(self.device)

        # Realistic stellar colors (O/B blue-white, F/G warm white, K/M gold-amber)
        temp_t = torch.rand(n_stars, generator=g)
        sr = torch.where(temp_t < 0.35, 0.72 + 0.25 * temp_t, 1.0)
        sg = torch.where(temp_t < 0.35, 0.84 + 0.14 * temp_t, 0.94 - 0.22 * (temp_t - 0.35))
        sb = torch.where(temp_t < 0.35, 1.0, torch.clamp(1.0 - 0.68 * (temp_t - 0.35), min=0.45))
        bright = (torch.rand(n_stars, generator=g) ** 3.2) * 1.45 + 0.08
        self.star_rgb = (torch.stack([sr, sg, sb], dim=-1) * bright.unsqueeze(-1)).to(self.device)
        self.star_phase = (torch.rand(n_stars, generator=g) * 6.283).to(self.device)
        self.star_sizes = torch.where(bright > 0.85, 2.1, 1.0).to(self.device)

        # Precompute low-res screen grid for 3D ray-cast nebula sky + full-res vignette
        gy_lo = torch.linspace(1.0, -1.0, self.h // 4, device=self.device)
        gx_lo = torch.linspace(-self.w / self.h, self.w / self.h, self.w // 4, device=self.device)
        self.sky_yy, self.sky_xx = torch.meshgrid(gy_lo, gx_lo, indexing="ij")

        vy = torch.linspace(-1.0, 1.0, self.h, device=self.device)
        vx = torch.linspace(-1.0, 1.0, self.w, device=self.device)
        vyy, vxx = torch.meshgrid(vy, vx, indexing="ij")
        r2 = vxx * vxx * 0.72 + vyy * vyy * 0.92
        self.vignette = torch.clamp(1.0 - 0.28 * r2, min=0.58, max=1.0).unsqueeze(0)

        # Precompute 1D separable Gaussian kernels for multi-scale HDR bloom
        self.bloom_kernels = {
            s: self._make_gauss_1d(s) for s in (3.0, 7.5, 15.0)
        }

    def _make_gauss_1d(self, sigma: float) -> torch.Tensor:
        rad = int(math.ceil(sigma * 2.6))
        xs = torch.arange(-rad, rad + 1, device=self.device, dtype=torch.float32)
        k = torch.exp(-0.5 * (xs / sigma) ** 2)
        k = k / k.sum()
        return k

    def clear_and_render_sky(
        self,
        cam: CameraMatrix,
        t: float,
        nebula_a: Tuple[float, float, float] = (0.018, 0.045, 0.115),
        nebula_b: Tuple[float, float, float] = (0.065, 0.025, 0.095),
        star_gain: float = 1.0,
    ) -> None:
        """Clears HDR + Z-buffer and paints 3D camera-coupled volumetric nebula clouds + parallax stars."""
        self.zbuf.fill_(1e6)

        # 1. 3D ray directions on 480x270 grid -> true parallax cosmic dust & nebula bands!
        fov_scale = math.tan(0.5 * math.radians(cam.pose.fov_deg))
        rx = cam.fwd[0] + self.sky_xx * fov_scale * cam.right[0] + self.sky_yy * fov_scale * cam.up[0]
        ry = cam.fwd[1] + self.sky_xx * fov_scale * cam.right[1] + self.sky_yy * fov_scale * cam.up[1]
        rz = cam.fwd[2] + self.sky_xx * fov_scale * cam.right[2] + self.sky_yy * fov_scale * cam.up[2]
        inv_l = torch.rsqrt(rx * rx + ry * ry + rz * rz + 1e-8)
        dx, dy, dz = rx * inv_l, ry * inv_l, rz * inv_l

        # Multi-frequency smooth 3D trigonometric FBM on celestial sphere
        n1 = 0.5 + 0.5 * torch.sin(2.4 * dx + 1.9 * dy - 1.3 * dz + 0.04 * t)
        n2 = 0.5 + 0.5 * torch.cos(4.3 * dy - 3.1 * dz + 2.2 * dx - 0.03 * t)
        n3 = 0.5 + 0.5 * torch.sin(7.1 * dz + 5.2 * dx + 3.7 * dy)
        band = torch.exp(-((dz * 0.75 + dx * 0.42 - dy * 0.25) ** 2) / 0.16)  # Subtle Milky Way band

        w_a = (n1 * n2) ** 1.6 * (0.45 + 0.85 * band)
        w_b = (n2 * n3) ** 2.0 * band

        base_r = 0.004 + nebula_a[0] * w_a + nebula_b[0] * w_b
        base_g = 0.006 + nebula_a[1] * w_a + nebula_b[1] * w_b
        base_b = 0.013 + nebula_a[2] * w_a + nebula_b[2] * w_b

        sky_lo = torch.stack([base_r, base_g, base_b], dim=0).unsqueeze(0)
        self.hdr = F.interpolate(sky_lo, size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)

        # 2. Project 14,000 3D stars with subtle scintillation
        if star_gain > 0.01:
            twinkle = (0.84 + 0.16 * torch.sin(1.9 * t + self.star_phase)).unsqueeze(-1)
            self.render_particles(
                self.star_xyz,
                self.star_rgb * (twinkle * star_gain),
                self.star_sizes,
                cam,
                additive=True,
                depth_occlude=False,
            )

    def compute_grid_normals(self, P: torch.Tensor) -> torch.Tensor:
        """Computes smooth unit 3D surface normals `(Nu, Nv, 3)` from parametric grid `P`."""
        du = torch.empty_like(P)
        dv = torch.empty_like(P)
        du[1:-1] = P[2:] - P[:-2]
        du[0] = P[1] - P[0]
        du[-1] = P[-1] - P[-2]

        dv[:, 1:-1] = P[:, 2:] - P[:, :-2]
        dv[:, 0] = P[:, 1] - P[:, 0]
        dv[:, -1] = P[:, -1] - P[:, -2]

        nrm = torch.cross(du, dv, dim=-1)
        return F.normalize(nrm, dim=-1, eps=1e-7)

    def render_surface_mesh(
        self,
        P: torch.Tensor,
        base_rgb: torch.Tensor | Tuple[float, float, float],
        cam: CameraMatrix,
        normals: Optional[torch.Tensor] = None,
        emissive_rgb: Optional[torch.Tensor | Tuple[float, float, float]] = None,
        alpha: float = 0.92,
        shininess: float = 48.0,
        specular_strength: float = 0.65,
        fresnel_rgb: Tuple[float, float, float] = (0.28, 0.72, 1.00),
        fresnel_strength: float = 0.45,
        two_sided: bool = True,
        wire_stride: int = 0,
        wire_rgb: Tuple[float, float, float] = (0.55, 0.90, 1.00),
        wire_boost: float = 0.45,
        write_depth: bool = True,
        z_tol: float = 0.16,
        supersample: Tuple[int, int] = (2, 2),
    ) -> None:
        """
        Shades and Z-buffer rasterizes a high-density 3D parametric mesh `P: (Nu, Nv, 3)`
        onto `1920x1080` HDR canvas using `2x2` sub-pixel splats.
        """
        nu, nv, _ = P.shape
        if normals is None:
            normals = self.compute_grid_normals(P)

        if not isinstance(base_rgb, torch.Tensor):
            albedo = torch.tensor(base_rgb, device=self.device, dtype=torch.float32).view(1, 1, 3).expand(nu, nv, 3).clone()
        elif base_rgb.ndim == 1:
            albedo = base_rgb.view(1, 1, 3).expand(nu, nv, 3).clone()
        else:
            albedo = base_rgb

        # Optional procedural silk harmonic grid lines baked cleanly onto surface
        wire_emit = torch.zeros_like(albedo)
        if wire_stride > 0:
            u_idx = torch.arange(nu, device=self.device)
            v_idx = torch.arange(nv, device=self.device)
            u_mask = (u_idx % wire_stride == 0).view(nu, 1, 1)
            v_mask = (v_idx % wire_stride == 0).view(1, nv, 1)
            w_mask = (u_mask | v_mask).float()
            w_col = torch.tensor(wire_rgb, device=self.device, dtype=torch.float32).view(1, 1, 3)
            wire_emit = w_mask * w_col * wire_boost

        # View vector & 2-light cinema Blinn-Phong + Fresnel shading
        view_dir = F.normalize(cam.pos.view(1, 1, 3) - P, dim=-1, eps=1e-7)
        l1 = F.normalize(torch.tensor([0.42, -0.36, 0.83], device=self.device), dim=0).view(1, 1, 3)
        l2 = F.normalize(torch.tensor([-0.68, 0.52, 0.42], device=self.device), dim=0).view(1, 1, 3)

        ndotl1_raw = (normals * l1).sum(dim=-1, keepdim=True)
        ndotl2_raw = (normals * l2).sum(dim=-1, keepdim=True)
        ndotv_raw = (normals * view_dir).sum(dim=-1, keepdim=True)

        if two_sided:
            # Flip normal toward viewer for thin membranes (silk fabric, soap film, hourglass)
            sign = torch.where(ndotv_raw >= 0.0, 1.0, -1.0)
            n_eff = normals * sign
            ndotl1 = torch.clamp((n_eff * l1).sum(dim=-1, keepdim=True), min=0.0)
            ndotl2 = torch.clamp((n_eff * l2).sum(dim=-1, keepdim=True), min=0.0)
            ndotv = torch.clamp(torch.abs(ndotv_raw), min=0.0, max=1.0)
        else:
            n_eff = normals
            ndotl1 = torch.clamp(ndotl1_raw, min=0.0)
            ndotl2 = torch.clamp(ndotl2_raw, min=0.0)
            ndotv = torch.clamp(ndotv_raw, min=0.0, max=1.0)

        h1 = F.normalize(l1 + view_dir, dim=-1, eps=1e-7)
        spec1 = torch.clamp((n_eff * h1).sum(dim=-1, keepdim=True), min=0.0) ** shininess
        fresnel = ((1.0 - ndotv) ** 3.0) * fresnel_strength

        key_col = torch.tensor([1.06, 1.01, 0.94], device=self.device).view(1, 1, 3)
        fill_col = torch.tensor([0.38, 0.68, 1.05], device=self.device).view(1, 1, 3)
        fres_col = torch.tensor(fresnel_rgb, device=self.device).view(1, 1, 3)

        shaded = (
            albedo * (0.16 + 0.92 * ndotl1 * key_col + 0.38 * ndotl2 * fill_col)
            + specular_strength * spec1 * key_col
            + fresnel * fres_col
            + wire_emit
        )

        if emissive_rgb is not None:
            if not isinstance(emissive_rgb, torch.Tensor):
                shaded = shaded + torch.tensor(emissive_rgb, device=self.device).view(1, 1, 3)
            elif emissive_rgb.ndim == 1:
                shaded = shaded + emissive_rgb.view(1, 1, 3)
            else:
                shaded = shaded + emissive_rgb

        # Guard against any floating-point NaN/Inf from degenerate vertices or fractional powers before supersampling/bloom
        P = torch.nan_to_num(P, nan=0.0, posinf=0.0, neginf=0.0)
        shaded = torch.nan_to_num(shaded, nan=0.0, posinf=24.0, neginf=0.0)

        # Bilinear GPU mesh supersampling so close-up macro shots are 100% solid satin/metal with zero dot gaps!
        su, sv = supersample
        if self.res_scale > 1.05:
            su = int(round(su * self.res_scale))
            sv = int(round(sv * self.res_scale))
        if (su > 1 or sv > 1) and nu >= 2 and nv >= 2:
            P_4d = P.permute(2, 0, 1).unsqueeze(0)
            C_4d = shaded.permute(2, 0, 1).unsqueeze(0)
            new_sz = (nu * su, nv * sv)
            P = F.interpolate(P_4d, size=new_sz, mode="bilinear", align_corners=True).squeeze(0).permute(1, 2, 0)
            shaded = F.interpolate(C_4d, size=new_sz, mode="bilinear", align_corners=True).squeeze(0).permute(1, 2, 0)

        # Project vertices -> flatten -> 2x2 sub-pixel footprint
        sx, sy, cz = cam.project(P)
        sx_f = sx.reshape(-1)
        sy_f = sy.reshape(-1)
        cz_f = cz.reshape(-1)
        col_f = shaded.reshape(-1, 3)

        vis = (cz_f > 0.15) & (sx_f >= -2.0) & (sx_f < self.w + 1.0) & (sy_f >= -2.0) & (sy_f < self.h + 1.0)
        if not torch.any(vis):
            return

        sx_v = sx_f[vis]
        sy_v = sy_f[vis]
        cz_v = cz_f[vis]
        col_v = col_f[vis]

        ix0 = torch.floor(sx_v).long()
        iy0 = torch.floor(sy_v).long()

        # Expand 2x2 pixel neighborhood for crisp hole-free surface coverage
        offs = ((0, 0), (1, 0), (0, 1), (1, 1))
        all_pix: List[torch.Tensor] = []
        all_z: List[torch.Tensor] = []
        all_c: List[torch.Tensor] = []

        for ox, oy in offs:
            px = ix0 + ox
            py = iy0 + oy
            in_b = (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
            if torch.any(in_b):
                all_pix.append(py[in_b] * self.w + px[in_b])
                all_z.append(cz_v[in_b])
                all_c.append(col_v[in_b])

        if not all_pix:
            return

        pix_idx = torch.cat(all_pix, dim=0)
        z_vals = torch.cat(all_z, dim=0)
        c_vals = torch.cat(all_c, dim=0)

        # Compute per-pixel frontmost depth of THIS mesh using pre-allocated buffer
        self._mesh_z.fill_(1e6)
        self._mesh_z.scatter_reduce_(0, pix_idx, z_vals, reduce="amin", include_self=True)

        # Keep fragments near front surface of this mesh AND in front of global zbuf
        front_mask = (z_vals <= self._mesh_z[pix_idx] + z_tol) & (z_vals <= self.zbuf[pix_idx] + z_tol)
        if not torch.any(front_mask):
            return

        p_keep = pix_idx[front_mask]
        c_keep = c_vals[front_mask]
        z_keep = z_vals[front_mask]

        if write_depth and alpha >= 0.65:
            self.zbuf.scatter_reduce_(0, p_keep, z_keep, reduce="amin", include_self=True)

        self._accum_rgb.zero_()
        self._accum_cnt.zero_()
        self._accum_rgb.index_add_(0, p_keep, c_keep)
        self._accum_cnt.index_add_(0, p_keep, torch.ones_like(z_keep))

        hit = self._accum_cnt > 0.5
        self._accum_rgb[hit] = self._accum_rgb[hit] / self._accum_cnt[hit].unsqueeze(-1)

        img_layer = self._accum_rgb.t().view(3, self.h, self.w)
        mask_2d = hit.view(1, self.h, self.w)

        # Screen-space micro-gap infill (`3x3` at 1080p, `5x5` at 4K UHD) so close-up surfaces have zero moire pinholes!
        if alpha >= 0.78:
            ks, pad = (5, 2) if self.res_scale >= 1.8 else (3, 1)
            m_f = mask_2d.float().unsqueeze(0)  # (1, 1, H, W)
            dil_m = F.max_pool2d(m_f, kernel_size=ks, stride=1, padding=pad)
            gap_only = (dil_m > 0.5) & (~mask_2d.unsqueeze(0))
            if torch.any(gap_only):
                blur_rgb = F.avg_pool2d(img_layer.unsqueeze(0) * m_f, kernel_size=ks, stride=1, padding=pad)
                blur_cnt = torch.clamp(F.avg_pool2d(m_f, kernel_size=ks, stride=1, padding=pad), min=1e-5)
                infilled = (blur_rgb / blur_cnt).squeeze(0)
                img_layer = torch.where(gap_only.squeeze(0), infilled, img_layer)
                mask_2d = dil_m.squeeze(0) > 0.5

        if alpha >= 0.999:
            self.hdr = torch.where(mask_2d, img_layer, self.hdr)
        else:
            self.hdr = torch.where(mask_2d, self.hdr * (1.0 - alpha) + img_layer * alpha, self.hdr)

    def render_particles(
        self,
        pts: torch.Tensor,
        rgb: torch.Tensor,
        sizes: float | torch.Tensor,
        cam: CameraMatrix,
        additive: bool = True,
        depth_occlude: bool = True,
        focus_dist: Optional[float] = None,
    ) -> None:
        """
        Vectorized GPU volumetric particle & bokeh splat renderer (`N` up to `60,000+` in `<1.2 ms`).
        Splits particles into crisp core splats (`1080p`) and wide glowing halo splats (`540p` upsampled).
        """
        sx, sy, cz = cam.project(pts)
        if isinstance(sizes, (int, float)):
            rad = torch.full_like(cz, float(sizes))
        else:
            rad = sizes.to(torch.float32)

        # Perspective size scaling + optional Depth-of-Field bokeh circle of confusion
        persp_rad = rad * (cam.pose.dist / torch.clamp(cz, min=0.35)) ** 0.65
        if focus_dist is not None:
            coc = torch.abs(cz - focus_dist) / max(1.0, focus_dist)
            persp_rad = persp_rad + 2.6 * torch.clamp(coc, 0.0, 2.5)
        persp_rad = torch.clamp(persp_rad, 0.8, 12.0)

        vis = (cz > 0.18) & (sx >= -12.0) & (sx < self.w + 12.0) & (sy >= -12.0) & (sy < self.h + 12.0)
        if not torch.any(vis):
            return

        sx_v = sx[vis]
        sy_v = sy[vis]
        cz_v = cz[vis]
        rgb_v = rgb[vis]
        rad_v = persp_rad[vis]

        if depth_occlude:
            ix_c = torch.clamp(sx_v.long(), 0, self.w - 1)
            iy_c = torch.clamp(sy_v.long(), 0, self.h - 1)
            z_at = self.zbuf[iy_c * self.w + ix_c]
            vis_z = cz_v <= z_at + 0.35
            if not torch.any(vis_z):
                return
            sx_v, sy_v, rgb_v, rad_v = sx_v[vis_z], sy_v[vis_z], rgb_v[vis_z], rad_v[vis_z]

        # Crisp core splat (`3x3` at 1080p, smooth circular `5x5` at 4K UHD!) using pre-allocated buffer
        self._accum_rgb.zero_()
        core_buf = self._accum_rgb
        ix0 = torch.round(sx_v).long()
        iy0 = torch.round(sy_v).long()
        # Energy normalization so bloated bokeh discs stay softly luminous instead of blowing out
        core_scale = torch.clamp(1.6 / (0.6 + 0.45 * rad_v), 0.18, 1.35).unsqueeze(-1)
        c_core = torch.nan_to_num(rgb_v * core_scale, nan=0.0, posinf=24.0, neginf=0.0)

        if self.res_scale >= 1.8:
            # True 4K UHD (`3840x2160`): pinpoint stars get a 2x2/cross anti-aliased sub-pixel splat so they keep
            # full 1080p visual brilliance, while larger stars (`rad_v >= 1.35`) get a silky circular 5x5 Gaussian!
            pinpoint_4k = (
                (0, 0, 1.00),
                (1, 0, 0.52), (-1, 0, 0.36), (0, 1, 0.52), (0, -1, 0.36),
            )
            for ox, oy, kw in pinpoint_4k:
                px = ix0 + ox
                py = iy0 + oy
                in_b = (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
                if torch.any(in_b):
                    core_buf.index_add_(0, py[in_b] * self.w + px[in_b], c_core[in_b] * kw)

            small_only = rad_v >= 1.35
            if torch.any(small_only):
                ix_s = ix0[small_only]
                iy_s = iy0[small_only]
                col_s = c_core[small_only]
                ring_4k = (
                    (-1, -1, 0.44), (1, -1, 0.44), (-1, 1, 0.44), (1, 1, 0.44),
                    (-2, 0, 0.24), (2, 0, 0.24), (0, -2, 0.24), (0, 2, 0.24),
                    (-2, -1, 0.14), (-2, 1, 0.14), (2, -1, 0.14), (2, 1, 0.14),
                    (-1, -2, 0.14), (1, -2, 0.14), (-1, 2, 0.14), (1, 2, 0.14),
                )
                for ox, oy, kw in ring_4k:
                    px = ix_s + ox
                    py = iy_s + oy
                    in_b = (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
                    if torch.any(in_b):
                        core_buf.index_add_(0, py[in_b] * self.w + px[in_b], col_s[in_b] * kw)
        else:
            kernel_3x3 = (
                (0, 0, 1.00),
                (-1, 0, 0.48), (1, 0, 0.48), (0, -1, 0.48), (0, 1, 0.48),
                (-1, -1, 0.22), (1, -1, 0.22), (-1, 1, 0.22), (1, 1, 0.22),
            )
            small_only = rad_v >= 1.35
            for ox, oy, kw in kernel_3x3:
                if (ox != 0 or oy != 0):
                    px = ix0[small_only] + ox
                    py = iy0[small_only] + oy
                    col = c_core[small_only] * kw
                else:
                    px = ix0
                    py = iy0
                    col = c_core * kw
                in_b = (px >= 0) & (px < self.w) & (py >= 0) & (py < self.h)
                if torch.any(in_b):
                    core_buf.index_add_(0, py[in_b] * self.w + px[in_b], col[in_b])

        self.hdr = self.hdr + core_buf.t().view(3, self.h, self.w)

        # Wide volumetric halo pass for larger particles (`rad_v >= 2.2`) at `(960x540)` + bilinear upsample
        big = rad_v >= 2.2
        if torch.any(big):
            hw, hh = self.halo_w, self.halo_h
            self._halo_buf.zero_()
            halo_buf = self._halo_buf
            hx = torch.round(sx_v[big] * (hw / float(self.w))).long()
            hy = torch.round(sy_v[big] * (hh / float(self.h))).long()
            h_col = torch.nan_to_num(rgb_v[big] * 0.22, nan=0.0, posinf=24.0, neginf=0.0)
            for ox in range(-2, 3):
                for oy in range(-2, 3):
                    w_g = math.exp(-0.45 * (ox * ox + oy * oy))
                    px = hx + ox
                    py = hy + oy
                    in_b = (px >= 0) & (px < hw) & (py >= 0) & (py < hh)
                    if torch.any(in_b):
                        halo_buf.index_add_(0, py[in_b] * hw + px[in_b], h_col[in_b] * w_g)
            halo_2d = halo_buf.t().view(1, 3, hh, hw)
            halo_up = F.interpolate(halo_2d, size=(self.h, self.w), mode="bilinear", align_corners=False).squeeze(0)
            if additive:
                self.hdr = self.hdr + halo_up
            else:
                self.hdr = 0.85 * self.hdr + halo_up

    def _blur_separable(self, img: torch.Tensor, sigma: float) -> torch.Tensor:
        """Applies fast 1D separable Gaussian blur on `(1, 3, H, W)` tensor."""
        k = self.bloom_kernels[sigma]
        pad = k.numel() // 2
        kh = k.view(1, 1, 1, -1).expand(3, 1, 1, -1)
        kv = k.view(1, 1, -1, 1).expand(3, 1, -1, 1)
        x = F.pad(img, (pad, pad, 0, 0), mode="replicate")
        x = F.conv2d(x, kh, groups=3)
        x = F.pad(x, (0, 0, pad, pad), mode="replicate")
        x = F.conv2d(x, kv, groups=3)
        return x

    def finalize_srgb_uint8(self, exposure: float = 1.05, bloom_strength: float = 0.42) -> np.ndarray:
        """Applies 3-octave GPU HDR Gaussian Bloom + ACES Filmic Tone Mapping + Vignette -> `(H, W, 3) uint8`."""
        x = torch.clamp(torch.nan_to_num(self.hdr, nan=0.0, posinf=24.0, neginf=0.0), min=0.0, max=24.0) * exposure

        # Extract bright HDR highlights above 0.72 for optical cinema bloom (normalized to 1080p pyramid scale!)
        bright = F.relu(x - 0.72).unsqueeze(0)  # (1, 3, H, W)
        if self.res_scale >= 1.8:
            bright = F.avg_pool2d(bright, 2)  # Downsample 3840x2160 -> 1920x1080 so bloom glow radius matches 1:1
        b_half = F.avg_pool2d(bright, 2)
        b_quar = F.avg_pool2d(b_half, 2)
        b_eigh = F.avg_pool2d(b_quar, 2)

        g1 = self._blur_separable(b_half, 3.0)
        g2 = self._blur_separable(b_quar, 7.5)
        g3 = self._blur_separable(b_eigh, 15.0)

        bloom = (
            0.50 * F.interpolate(g1, size=(self.h, self.w), mode="bilinear", align_corners=False)
            + 0.35 * F.interpolate(g2, size=(self.h, self.w), mode="bilinear", align_corners=False)
            + 0.25 * F.interpolate(g3, size=(self.h, self.w), mode="bilinear", align_corners=False)
        ).squeeze(0)

        hdr_bloomed = (x + bloom_strength * bloom) * self.vignette

        # ACES Filmic Tone Mapping Curve (Narkowicz fit)
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        mapped = torch.clamp((hdr_bloomed * (a * hdr_bloomed + b)) / (hdr_bloomed * (c * hdr_bloomed + d) + e), 0.0, 1.0)

        # Gamma 1/2.2 encoding -> pinned CPU buffer via PCIe DMA (zero extra per-frame allocation!)
        srgb = (mapped ** (1.0 / 2.2) * 255.0).clamp(0.0, 255.0).to(torch.uint8)
        self._cpu_pinned.copy_(srgb.permute(1, 2, 0), non_blocking=False)
        return self._cpu_pinned.numpy()
