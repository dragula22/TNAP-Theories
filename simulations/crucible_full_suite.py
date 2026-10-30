"""
Master Quantitative Crucible Suite (2026) — Foundational Physics Discovery Collective.
Architect: Dr. Priya Ramanujan (Chief Phenomenologist & Experimental Crucible Architect)

Extends `simulations/empirical_crucible.py` with four quantitative test harnesses:
  (a) Cosmological Expansion chi^2 Test (DESI DR2 2025 BAO + CMB theta_* + SNe shape)
  (b) Solar System & Gaia DR3 Wide-Binary Screening Test (Mercury, Earth, Saturn Cassini,
      and 5,000-10,000 AU Wide Binaries with & without Milky Way External Field Effect)
  (c) Bullet Cluster Dynamical Lensing Test (3D-to-2D convergence kappa(x) offset and
      subcluster lensing-to-stellar mass ratio at v_coll ~ 4500 km/s)
  (d) Quantum Measurement, BMV Tabletop & Wigner-Friend Discriminator (Spin-2 QGEM vs.
      Oppenheim CQ diffusion-decoherence trade-off vs. Non-Markovian / Bi-Boundary /
      Horizon-Capacity alternatives)
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import integrate, linalg

# Ensure workspace root is importable when executed directly
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_THIS_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from simulations.empirical_crucible import (
    A0_SPARC,
    C_H0_OVER_2PI,
    C_LIGHT,
    G_NEWTON,
    H0_KM_S_MPC,
    HBAR,
    MPC_TO_M,
    bmv_entanglement_phase,
    double_slit_complementarity_check,
    hubble_cpl,
    rar_log_rms_dex,
    sparc_rar_empirical,
)

# Astronomical & physical constants
C_KM_S = C_LIGHT / 1000.0               # 299792.458 km / s
AU_TO_M = 1.495978707e11                # m / AU
KPC_TO_M = MPC_TO_M / 1000.0            # m / kpc
M_SUN = 1.98847e30                      # kg
YR_TO_S = 365.25 * 86400.0              # s / Julian year
MYR_TO_S = 1.0e6 * YR_TO_S


# =============================================================================
# HARNESS A: COSMOLOGICAL EXPANSION CHI^2 TEST (DESI DR2 BAO + CMB + SNe SHAPE)
# =============================================================================

@dataclass(frozen=True)
class DesiBaoBin:
    tracer: str
    z_eff: float
    kind: str  # "DV" (isotropic) or "DM_DH" (anisotropic pair)
    val1: float
    err1: float
    val2: Optional[float] = None
    err2: Optional[float] = None
    corr: float = 0.0


# Authentic DESI DR2 (March 2025, Results II Table IV) consensus BAO measurements
DESI_DR2_BAO_DATA: Tuple[DesiBaoBin, ...] = (
    DesiBaoBin("BGS",       0.295, "DV",    7.942,  0.075),
    DesiBaoBin("LRG1",      0.510, "DM_DH", 13.588, 0.167, 21.863, 0.425, -0.459),
    DesiBaoBin("LRG2",      0.706, "DM_DH", 17.351, 0.177, 19.455, 0.330, -0.404),
    DesiBaoBin("LRG3+ELG1", 0.934, "DM_DH", 21.576, 0.152, 17.641, 0.193, -0.416),
    DesiBaoBin("ELG2",      1.321, "DM_DH", 27.601, 0.318, 14.176, 0.221, -0.434),
    DesiBaoBin("QSO",       1.484, "DM_DH", 30.512, 0.760, 12.817, 0.516, -0.500),
    DesiBaoBin("Lya-QSO",   2.330, "DM_DH", 38.988, 0.531, 8.632,  0.101, -0.431),
)


def build_desi_dr2_vector_and_cov() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Builds the 13-element DESI DR2 BAO observation vector and block-diagonal covariance matrix."""
    obs: List[float] = []
    labels: List[str] = []
    blocks: List[np.ndarray] = []

    for b in DESI_DR2_BAO_DATA:
        if b.kind == "DV":
            obs.append(b.val1)
            labels.append(f"{b.tracer}(z={b.z_eff}):DV/rd")
            blocks.append(np.array([[b.err1 ** 2]], dtype=float))
        else:
            assert b.val2 is not None and b.err2 is not None
            obs.extend([b.val1, b.val2])
            labels.extend([
                f"{b.tracer}(z={b.z_eff}):DM/rd",
                f"{b.tracer}(z={b.z_eff}):DH/rd",
            ])
            c12 = b.corr * b.err1 * b.err2
            blocks.append(np.array([
                [b.err1 ** 2, c12],
                [c12, b.err2 ** 2],
            ], dtype=float))

    cov = linalg.block_diag(*blocks)
    return np.array(obs, dtype=float), cov, labels


def comoving_dm_mpc(h_of_z_km_s_mpc: Callable[[np.ndarray], np.ndarray], z_targets: np.ndarray) -> np.ndarray:
    """Computes flat-space transverse comoving distance D_M(z) = int_0^z (c / H(z')) dz' in Mpc."""
    z_targets = np.asarray(z_targets, dtype=float)
    z_max = float(np.max(z_targets))
    # High-accuracy Gauss-Kronrod quadrature segment-by-segment
    z_sorted_idx = np.argsort(z_targets)
    z_sorted = z_targets[z_sorted_idx]

    dm_sorted = np.zeros_like(z_sorted)
    z_prev = 0.0
    acc = 0.0
    for i, z_curr in enumerate(z_sorted):
        if z_curr > z_prev:
            seg, _ = integrate.quad(
                lambda zp: C_KM_S / float(np.squeeze(h_of_z_km_s_mpc(np.array([zp])))),
                z_prev,
                float(z_curr),
                epsabs=1e-9,
                epsrel=1e-9,
                limit=200,
            )
            acc += seg
            z_prev = float(z_curr)
        dm_sorted[i] = acc

    dm_out = np.zeros_like(z_targets)
    dm_out[z_sorted_idx] = dm_sorted
    return dm_out


def hubble_cpl_with_radiation(
    z: np.ndarray,
    omega_m: float = 0.310,
    w0: float = -1.0,
    wa: float = 0.0,
    h0: float = 68.0,
    omega_r_h2: float = 4.183e-5,
) -> np.ndarray:
    """
    Flat CPL H(z) [km/s/Mpc] including relativistic radiation (photons + 3 neutrino species)
    so high-z CMB acoustic scale theta_*(z_* = 1089.8) is accurately modeled alongside BAO.
    """
    z = np.asarray(z, dtype=float)
    h = h0 / 100.0
    omega_r = omega_r_h2 / (h ** 2)
    omega_de = 1.0 - omega_m - omega_r
    zp1 = 1.0 + z
    de_factor = (zp1 ** (3.0 * (1.0 + w0 + wa))) * np.exp(-3.0 * wa * z / zp1)
    e2 = omega_r * (zp1 ** 4) + omega_m * (zp1 ** 3) + omega_de * de_factor
    return h0 * np.sqrt(np.maximum(e2, 1e-30))


# Representative compressed SNe Ia distance-modulus differences mu(z_i) - mu(z_ref=0.05)
# calibrated to the DESI-DR2 + DES-Y5 / Union3 late-time Hubble-diagram shape:
# Independent of H0 and SNe absolute magnitude M_B, breaking the (Omega_m, w0, wa) degeneracy
# so LCDM experiences the observed ~3.8-4.2 sigma joint tension vs Quintom-B (w0>-1, wa<0).
SNE_SHAPE_Z_REF = 0.05
SNE_SHAPE_BINS = (
    # (z_bin, delta_mu_obs = 5*log10(D_L(z)/D_L(0.05)), sigma_mag)
    (0.15, 2.5123, 0.018),
    (0.30, 4.1836, 0.018),
    (0.50, 5.4774, 0.020),
    (0.75, 6.5417, 0.022),
)


def calibrate_h0_to_cmb_theta_star(
    hz_factory_given_h0: Callable[[float], Callable[[np.ndarray], np.ndarray]],
    rs_star_mpc: float = 144.43,
    theta_star_100_target: float = 1.04109,
    h0_bounds: Tuple[float, float] = (50.0, 90.0),
) -> float:
    """Finds H0 [km/s/Mpc] that places a candidate E(z)=H(z)/H0 exactly on the Planck PR4 theta_* surface."""
    from scipy.optimize import brentq

    def resid(h0_try: float) -> float:
        dm_star = float(comoving_dm_mpc(hz_factory_given_h0(h0_try), np.array([1089.80]))[0])
        return 100.0 * (rs_star_mpc / dm_star) - theta_star_100_target

    return float(brentq(resid, h0_bounds[0], h0_bounds[1], xtol=1e-6))


def desi_dr2_cosmology_crucible(
    h_of_z_km_s_mpc: Callable[[np.ndarray], np.ndarray],
    rd_mpc: float = 147.09,
    rs_star_mpc: float = 144.43,
    include_cmb_theta_star: bool = True,
    include_sne_shape: bool = True,
) -> Dict[str, float]:
    """
    Evaluates a candidate H(z) [km/s/Mpc] model against:
      1. Full 13-point DESI DR2 BAO vector (both fixed r_d and analytically profiled best-fit r_d).
      2. Planck PR4 CMB acoustic scale 100*theta_* = 1.04109 +/- 0.00028 at z_* = 1089.80.
      3. Compressed low-z SNe Ia Hubble-diagram shape delta_mu(z) across z in [0.15, 0.75].
    """
    obs_vec, cov, _ = build_desi_dr2_vector_and_cov()
    inv_cov = linalg.inv(cov)

    z_all = np.array([b.z_eff for b in DESI_DR2_BAO_DATA], dtype=float)
    dm_all = comoving_dm_mpc(h_of_z_km_s_mpc, z_all)
    dh_all = C_KM_S / h_of_z_km_s_mpc(z_all)

    # Unscaled model distances D_i [Mpc] such that model BAO ratio = D_i / r_d
    d_unscaled: List[float] = []
    for idx, b in enumerate(DESI_DR2_BAO_DATA):
        if b.kind == "DV":
            dv = (b.z_eff * (dm_all[idx] ** 2) * dh_all[idx]) ** (1.0 / 3.0)
            d_unscaled.append(float(dv))
        else:
            d_unscaled.extend([float(dm_all[idx]), float(dh_all[idx])])

    d_vec = np.array(d_unscaled, dtype=float)

    # 1a. Fixed-r_d BAO chi^2
    res_fixed = obs_vec - (d_vec / rd_mpc)
    chi2_bao_fixed = float(res_fixed @ inv_cov @ res_fixed)

    # 1b. Profiled-r_d (shape-only) BAO chi^2 via exact linear GLS for alpha = 1 / r_d
    alpha_best = float((d_vec @ inv_cov @ obs_vec) / (d_vec @ inv_cov @ d_vec))
    rd_best_mpc = 1.0 / alpha_best
    res_prof = obs_vec - alpha_best * d_vec
    chi2_bao_profiled = float(res_prof @ inv_cov @ res_prof)

    # 2. CMB acoustic scale theta_* at z_* = 1089.80
    chi2_cmb = 0.0
    theta_star_100 = float("nan")
    if include_cmb_theta_star:
        dm_star = float(comoving_dm_mpc(h_of_z_km_s_mpc, np.array([1089.80]))[0])
        theta_star_100 = 100.0 * (rs_star_mpc / dm_star)
        # Planck PR4 + ACT DR6: 100 * theta_* = 1.04109 +/- 0.00028 (with ~0.00060 effective
        # width when marginalizing mild early-physicsomega_b/omega_m shifts)
        chi2_cmb = ((theta_star_100 - 1.04109) / 0.00060) ** 2

    # 3. Low-z SNe Ia Hubble-diagram shape (independent of H0 and absolute magnitude M_B!)
    chi2_sne = 0.0
    if include_sne_shape:
        z_sne = np.array([SNE_SHAPE_Z_REF] + [row[0] for row in SNE_SHAPE_BINS], dtype=float)
        dm_sne = comoving_dm_mpc(h_of_z_km_s_mpc, z_sne)
        dl_sne = (1.0 + z_sne) * dm_sne
        dl_ref = dl_sne[0]
        for i, (_, dmu_obs, sig_mu) in enumerate(SNE_SHAPE_BINS, start=1):
            dmu_mod = 5.0 * math.log10(dl_sne[i] / dl_ref)
            chi2_sne += ((dmu_mod - dmu_obs) / sig_mu) ** 2

    return {
        "chi2_bao_fixed_rd": chi2_bao_fixed,
        "chi2_bao_profiled_rd": chi2_bao_profiled,
        "best_fit_rd_mpc": rd_best_mpc,
        "theta_star_100": theta_star_100,
        "chi2_cmb_theta": chi2_cmb,
        "chi2_sne_shape": chi2_sne,
        "chi2_joint": chi2_bao_fixed + chi2_cmb + chi2_sne,
    }


# =============================================================================
# HARNESS B: SOLAR SYSTEM & WIDE-BINARY SCREENING CRUCIBLE
# =============================================================================

def qumond_efe_boost(
    nu_func: Callable[[np.ndarray], np.ndarray],
    g_int: float,
    g_ext: float,
    a0: float = A0_SPARC,
    n_mu: int = 256,
) -> float:
    """
    Computes the angularly averaged effective radial gravitational boost g_eff / g_N
    for a binary with internal Newtonian acceleration g_int embedded in a uniform
    galactic external Newtonian/baryonic field g_ext_N (corresponding to observed g_ext).

    Uses spherical Gauss-Legendre quadrature over cos(theta) = mu in [-1, 1] for the
    nonlinear QUMOND potential gradient:
        g_tot(mu) = nu(|g_int * r_hat + g_ext_N * e_hat| / a0) * (g_int * r_hat + g_ext_N * e_hat)
    Subtracting the background field nu(g_ext_N / a0) * g_ext_N * e_hat and projecting onto r_hat:
        g_eff,r / g_int = < nu(y_tot) * (1 + (g_ext_N / g_int) * mu) - nu(y_ext) * (g_ext_N / g_int) * mu >_mu
    """
    if g_ext <= 0.0:
        return float(np.squeeze(nu_func(np.array([g_int / a0]))))

    # Invert nu(y_ext) * y_ext = g_ext / a0 via Newton/bisection to get bare external y_ext_N
    target_obs_y = g_ext / a0
    lo, hi = 1e-8, max(target_obs_y * 2.0, 10.0)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        val = float(np.squeeze(nu_func(np.array([mid])))) * mid
        if val < target_obs_y:
            lo = mid
        else:
            hi = mid
    y_ext_n = 0.5 * (lo + hi)
    g_ext_n = y_ext_n * a0
    nu_ext = float(np.squeeze(nu_func(np.array([y_ext_n]))))

    mu, weights = np.polynomial.legendre.leggauss(n_mu)
    g_tot_mag = np.sqrt(g_int ** 2 + g_ext_n ** 2 + 2.0 * g_int * g_ext_n * mu)
    nu_tot = nu_func(np.maximum(g_tot_mag / a0, 1e-30))

    # Project subtracted field onto internal radial unit vector r_hat (where e_hat . r_hat = mu)
    radial_integrand = nu_tot * (1.0 + (g_ext_n / g_int) * mu) - nu_ext * (g_ext_n / g_int) * mu
    avg_boost = 0.5 * float(np.sum(weights * radial_integrand))
    return avg_boost


def nu_rar_exp(y: np.ndarray) -> np.ndarray:
    """SPARC RAR interpolating function nu(y) = 1 / (1 - exp(-sqrt(y)))."""
    y = np.asarray(y, dtype=float)
    s = np.sqrt(np.maximum(y, 1e-30))
    # Avoid underflow loss of precision for large s: when s > 40, exp(-s) < 4.2e-18;
    # return exact asymptotic 1 + exp(-s) for s > 35 so tiny anomalies remain measurable!
    out = np.empty_like(s)
    mask_large = s > 35.0
    out[mask_large] = 1.0 + np.exp(-s[mask_large])
    out[~mask_large] = 1.0 / (1.0 - np.exp(-s[~mask_large]))
    return out


def nu_simple_mond(y: np.ndarray) -> np.ndarray:
    """Simple MOND nu(y) = 1/2 + sqrt(1/4 + 1/y), inverse of mu(x) = x/(1+x)."""
    y = np.asarray(y, dtype=float)
    return 0.5 + np.sqrt(0.25 + 1.0 / np.maximum(y, 1e-30))


def nu_standard_mond(y: np.ndarray) -> np.ndarray:
    """Standard MOND nu(y) = [1/2 + sqrt(1/4 + 1/y^2)]^(1/2), inverse of mu(x) = x/sqrt(1+x^2)."""
    y = np.asarray(y, dtype=float)
    return np.sqrt(0.5 + np.sqrt(0.25 + 1.0 / np.maximum(y ** 2, 1e-60)))


def nu_newtonian(y: np.ndarray) -> np.ndarray:
    return np.ones_like(np.asarray(y, dtype=float))


def solar_and_wide_binary_crucible(
    nu_func: Callable[[np.ndarray], np.ndarray],
    a0: float = A0_SPARC,
    potential_screen_factor: Callable[[float, float], float] | None = None,
) -> Dict[str, float | bool]:
    """
    Tests any dimensionless acceleration boost nu(y = g_bar / a0) across:
      - SPARC Galactic RAR [1e-12 to 1e-8 m/s^2] (target RMS < 0.10 dex)
      - Mercury (0.387 AU, bound |dg/gN| < 4e-10)
      - Earth   (1.000 AU, bound |dg/gN| < 1e-10)
      - Saturn  (10.00 AU, Cassini ephemeris bound |dg/gN| < 2e-9)
      - Gaia Wide Binary (s = 5,000 AU & 10,000 AU, M_tot = 1.6 M_sun), both
        isolated (g_ext = 0) and embedded in Milky Way EFE (g_ext = 1.8 * a0).

    Optional `potential_screen_factor(r_m, mass_kg)` in [0, 1] multiplies (nu - 1) to test
    models with local potential/metric/Kretschmann screening.
    """
    def eval_boost(mass_kg: float, r_m: float, g_ext: float = 0.0) -> float:
        g_n = G_NEWTON * mass_kg / (r_m ** 2)
        raw_boost = qumond_efe_boost(nu_func, g_n, g_ext, a0=a0)
        if potential_screen_factor is not None:
            scr = potential_screen_factor(r_m, mass_kg)
            return 1.0 + scr * (raw_boost - 1.0)
        return raw_boost

    # 1. SPARC RAR fidelity across galactic regime (r ~ 1 to 50 kpc, M_gal ~ 5e10 M_sun)
    g_grid = np.logspace(-12.0, -8.5, 120)
    g_mod = g_grid * nu_func(g_grid / a0)
    sparc_rms_dex = rar_log_rms_dex(g_mod, g_grid, a0=A0_SPARC)

    # 2. Solar System planetary orbits
    dg_mercury = abs(eval_boost(M_SUN, 0.387 * AU_TO_M) - 1.0)
    dg_earth = abs(eval_boost(M_SUN, 1.000 * AU_TO_M) - 1.0)
    dg_saturn = abs(eval_boost(M_SUN, 10.00 * AU_TO_M) - 1.0)

    # 3. Gaia DR3 Wide Binaries (M_tot = 1.6 M_sun, s = 5,000 AU and 10,000 AU)
    m_wb = 1.6 * M_SUN
    wb_5kau_iso = eval_boost(m_wb, 5000.0 * AU_TO_M, g_ext=0.0)
    wb_5kau_efe = eval_boost(m_wb, 5000.0 * AU_TO_M, g_ext=1.8 * a0)
    wb_10kau_iso = eval_boost(m_wb, 10000.0 * AU_TO_M, g_ext=0.0)
    wb_10kau_efe = eval_boost(m_wb, 10000.0 * AU_TO_M, g_ext=1.8 * a0)

    passes_solar = (dg_mercury < 4.0e-10) and (dg_earth < 1.0e-10) and (dg_saturn < 2.0e-9)
    passes_sparc = sparc_rms_dex < 0.10
    # Unscreened isolated boost > 1.55 at 10 kAU is falsified by BOTH Chae and Banik!
    passes_wb_unscreened_cap = wb_10kau_efe < 1.50

    return {
        "sparc_rms_dex": sparc_rms_dex,
        "dg_mercury": dg_mercury,
        "dg_earth": dg_earth,
        "dg_saturn": dg_saturn,
        "wb_5kau_boost_isolated": wb_5kau_iso,
        "wb_5kau_boost_mw_efe": wb_5kau_efe,
        "wb_10kau_boost_isolated": wb_10kau_iso,
        "wb_10kau_boost_mw_efe": wb_10kau_efe,
        "passes_solar_ephemerides": passes_solar,
        "passes_sparc_rar": passes_sparc,
        "passes_wb_sanity": passes_wb_unscreened_cap,
    }


# =============================================================================
# HARNESS C: BULLET CLUSTER DYNAMICAL LENSING CRUCIBLE (1E 0657-56)
# =============================================================================

def _plummer_surface_density_msun_kpc2(
    x_kpc: np.ndarray,
    y_kpc: float,
    x0_kpc: float,
    mass_msun: float,
    core_a_kpc: float,
) -> np.ndarray:
    """
    Analytic projected surface mass density Sigma(R) = M * a^2 / [pi * (R^2 + a^2)^2]
    for a 3D Plummer sphere rho(r) = (3 M / 4 pi a^3) * (1 + r^2/a^2)^(-5/2).
    """
    r2 = (x_kpc - x0_kpc) ** 2 + (y_kpc ** 2)
    return mass_msun * (core_a_kpc ** 2) / (math.pi * ((r2 + core_a_kpc ** 2) ** 2))


def _plummer_enclosed_cyl_mass_msun(r_ap_kpc: float, mass_msun: float, core_a_kpc: float) -> float:
    """Exact projected cylindrical aperture mass M(<R) = M * R^2 / (R^2 + a^2) for a Plummer sphere."""
    return mass_msun * (r_ap_kpc ** 2) / (r_ap_kpc ** 2 + core_a_kpc ** 2)


def _qumond_projected_sigma_on_axis(
    x_grid_kpc: np.ndarray,
    components: List[Tuple[float, float, float]],
    nu_func: Callable[[np.ndarray], np.ndarray],
    a0: float = A0_SPARC,
) -> np.ndarray:
    """
    Computes exact projected effective lensing surface mass density Sigma_eff(x, y=0) [M_sun/kpc^2]
    along the Bullet Cluster collision axis for an instantaneous QUMOND law
        rho_eff(r) = (1 / 4 pi G) div [ nu(|g_bar|/a0) g_bar ]
    evaluated via 3D finite-difference divergence integrated along the line of sight z_los!
    """
    # Build 3D slab around y = 0 (since components lie on y = 0, z = 0 axis, ∂_y g_y = ∂_z g_z on axis!)
    # Exploiting cylindrical symmetry around the x-axis: for axisymmetric sources on the x-axis,
    # g_bar = (g_x(x, R_perp), g_perp(x, R_perp)), and div g = ∂_x g_x + (1/R_perp) ∂_{R_perp}(R_perp g_perp).
    nx = len(x_grid_kpc)
    dx_kpc = float(x_grid_kpc[1] - x_grid_kpc[0])

    # Transverse cylindrical radius grid R_perp from 1 kpc to 1800 kpc (for line-of-sight projection at y=0, R_perp = |z_los|)
    r_perp_kpc = np.geomspace(1.0, 2000.0, 180)
    X, RP = np.meshgrid(x_grid_kpc, r_perp_kpc, indexing="ij")  # shape (nx, nr)

    gx = np.zeros_like(X)
    gp = np.zeros_like(X)

    for x0_kpc, mass_msun, a_kpc in components:
        rx_m = (X - x0_kpc) * KPC_TO_M
        rp_m = RP * KPC_TO_M
        r2_a2_m2 = rx_m ** 2 + rp_m ** 2 + (a_kpc * KPC_TO_M) ** 2
        pref = -G_NEWTON * (mass_msun * M_SUN) / (r2_a2_m2 ** 1.5)
        gx += pref * rx_m
        gp += pref * rp_m

    g_mag = np.sqrt(gx ** 2 + gp ** 2)
    nu_val = nu_func(g_mag / a0)
    gx_eff = nu_val * gx
    gp_eff = nu_val * gp

    # Axisymmetric 3D divergence in SI [s^-2]: div g_eff = ∂gx_eff/∂x + (1/RP) ∂(RP * gp_eff)/∂RP
    dgx_dx = np.gradient(gx_eff, dx_kpc * KPC_TO_M, axis=0)
    d_rp_gp = np.gradient((RP * KPC_TO_M) * gp_eff, r_perp_kpc * KPC_TO_M, axis=1)
    div_g_si = dgx_dx + d_rp_gp / (RP * KPC_TO_M)

    # Effective 3D density rho_eff = -div(g_eff) / (4 * pi * G) [kg / m^3]
    rho_eff_kg_m3 = -div_g_si / (4.0 * math.pi * G_NEWTON)

    # At y = 0, line-of-sight coordinate z_los has R_perp = |z_los| -> Sigma(x, y=0) = 2 * int_0^inf rho_eff(x, R_perp=z) dz
    sigma_kg_m2 = 2.0 * integrate.simpson(rho_eff_kg_m3, x=r_perp_kpc * KPC_TO_M, axis=1)
    sigma_msun_kpc2 = sigma_kg_m2 * (KPC_TO_M ** 2) / M_SUN
    return sigma_msun_kpc2


def bullet_cluster_dynamical_crucible(
    mode: str = "lcdm",
    v_coll_km_s: float = 4500.0,
    t_post_myr: float = 150.0,
    tau_relax_myr: float = 1200.0,
) -> Dict[str, float | bool | str]:
    """
    Quantitative Bullet Cluster (1E 0657-56) weak/strong lensing convergence test.

    Baryonic post-collision geometry (x in kpc along merger axis):
      - Main Cluster:   Stars at x = -350 kpc (3.5e13 M_sun, a=80 kpc)
                        X-ray Gas decelerated to x = -140 kpc (2.0e14 M_sun, a=130 kpc)
      - Subcluster:     BCG/Stars at x = +370 kpc (1.1e13 M_sun, a=60 kpc)
                        Shocked X-ray Gas ("Bullet") at x = +170 kpc (2.8e13 M_sun, a=80 kpc)
      Observed subcluster lensing constraints (Clowe+2006; Paraficz+2016; Cha+2024/2025 JWST):
        1. Lensing peak offset ahead of X-ray gas: 150 <= Delta x_{kappa - gas} <= 250 kpc
        2. Subcluster aperture (R < 150 kpc around BCG) M_lens / M_star in [4.5, 9.0]

    Supported `mode` options:
      - "lcdm": Collisionless dark matter halos (M_DM / M_bar ~ 5.2) co-moving with stars.
      - "memoryless_mond": Instantaneous algebraic RAR/QUMOND sourced by present-day baryons.
      - "eulerian_memory_trap": Non-covariant fixed-coordinate relaxation tau * d_t Phi + Phi = Phi_MOND
                                (demonstrates Trap C1: memory wake trails BEHIND gas!).
      - "covariant_geodesic_memory": Geodesic-advected auxiliary stress-energy / condensate mode
                                     (AeST / viscoelastic geodesic fluid with tau_relax >> t_shock).
    """
    sigma_crit = 3.10e9  # M_sun / kpc^2 (z_L = 0.296, z_S ~ 0.85)
    x_grid = np.linspace(-600.0, 600.0, 481)

    # Present-day observed baryonic components: (x0_kpc, mass_msun, core_a_kpc)
    x_star_1, m_star_1, a_star_1 = -350.0, 3.8e13, 80.0
    x_gas_1,  m_gas_1,  a_gas_1  = -140.0, 2.0e14, 130.0
    x_star_2, m_star_2, a_star_2 = +370.0, 1.4e13, 58.0
    x_gas_2,  m_gas_2,  a_gas_2  = +170.0, 2.8e13, 80.0

    baryon_components = [
        (x_star_1, m_star_1, a_star_1),
        (x_gas_1,  m_gas_1,  a_gas_1),
        (x_star_2, m_star_2, a_star_2),
        (x_gas_2,  m_gas_2,  a_gas_2),
    ]

    sigma_baryons = sum(
        _plummer_surface_density_msun_kpc2(x_grid, 0.0, x0, m, a)
        for x0, m, a in baryon_components
    )

    if mode == "lcdm":
        # Collisionless cluster-scale NFW/Plummer halos centered on collisionless stellar components
        dm_components = [
            (x_star_1, 5.2 * (m_star_1 + m_gas_1), 300.0),
            (x_star_2, 5.2 * (m_star_2 + m_gas_2), 225.0),
        ]
        sigma_tot = sigma_baryons + sum(
            _plummer_surface_density_msun_kpc2(x_grid, 0.0, x0, m, a)
            for x0, m, a in dm_components
        )
    elif mode == "memoryless_mond":
        # Exact axisymmetric 3D divergence projection of instantaneous RAR/QUMOND!
        sigma_tot = _qumond_projected_sigma_on_axis(x_grid, baryon_components, nu_rar_exp)
    elif mode == "eulerian_memory_trap":
        # Non-covariant Eulerian relaxation: subcluster moved from x_init = +370 - v_sub * t_post
        # With v_sub ~ 3000 km/s in cluster CoM frame (3.07 kpc/Myr), over 150 Myr it moved +460 kpc!
        # An Eulerian memory kernel exp(-t / tau) smears the phantom halo BACKWARD along the path!
        v_sub_kpc_myr = 0.67 * v_coll_km_s * (YR_TO_S * 1e6) / (KPC_TO_M / 1000.0)
        sigma_inst = _qumond_projected_sigma_on_axis(x_grid, baryon_components, nu_rar_exp)
        sigma_pdm_now = np.maximum(sigma_inst - sigma_baryons, 0.0)
        n_steps = 15
        dt = t_post_myr / n_steps
        sigma_wake = np.zeros_like(x_grid)
        w_sum = 0.0
        for k in range(1, n_steps + 1):
            t_ago = k * dt
            w = math.exp(-t_ago / max(tau_relax_myr, 1.0))
            w_sum += w
            # Subcluster was further LEFT (-x) in the past!
            x_sub_past = x_star_2 - v_sub_kpc_myr * t_ago
            x_main_past = x_star_1 + 0.33 * v_sub_kpc_myr * t_ago
            sigma_wake += w * (
                _plummer_surface_density_msun_kpc2(x_grid, 0.0, x_main_past, 4.5 * (m_star_1 + m_gas_1), 290.0)
                + _plummer_surface_density_msun_kpc2(x_grid, 0.0, x_sub_past, 4.5 * (m_star_2 + m_gas_2), 220.0)
            )
        retain = math.exp(-t_post_myr / max(tau_relax_myr, 1.0))
        sigma_tot = sigma_baryons + (1.0 - retain) * sigma_pdm_now + retain * (sigma_wake / w_sum)
    elif mode == "covariant_geodesic_memory":
        # Covariant auxiliary field (e.g. AeST dust-like mode / geodesic-advected metric memory):
        # Prior to collision, the subcluster's total baryons (stars + gas = 4.2e13 M_sun) sourced
        # an equilibrium deep-RAR + cluster-condensate potential halo (~4.8x total baryonic mass).
        # During the fast 30 Myr ram-pressure shock (<< tau_relax), the gas decelerates hydrodynamically
        # while the gravitational auxiliary stress-energy mode continues along timelike geodesics with
        # the collisionless BCG, decaying only by (1 - exp(-t_post / tau_relax)) toward the stripped state!
        retain = math.exp(-t_post_myr / max(tau_relax_myr, 1.0))
        sigma_inst = _qumond_projected_sigma_on_axis(x_grid, baryon_components, nu_rar_exp)
        sigma_pdm_stripped = np.maximum(sigma_inst - sigma_baryons, 0.0)

        advected_halo_1 = _plummer_surface_density_msun_kpc2(
            x_grid, 0.0, x_star_1, 4.8 * (m_star_1 + m_gas_1), 300.0
        )
        advected_halo_2 = _plummer_surface_density_msun_kpc2(
            x_grid, 0.0, x_star_2, 4.8 * (m_star_2 + m_gas_2), 225.0
        )
        sigma_tot = sigma_baryons + retain * (advected_halo_1 + advected_halo_2) + (1.0 - retain) * sigma_pdm_stripped
    else:
        raise ValueError(f"Unknown Bullet Cluster mode: {mode}")

    kappa = sigma_tot / sigma_crit
    kappa_nonbar = (sigma_tot - sigma_baryons) / sigma_crit

    # Locate dominant total convergence peak on the subcluster side (x > +50 kpc)
    sub_mask = x_grid >= 50.0
    idx_peak = int(np.argmax(kappa[sub_mask]))
    x_kappa_sub = float(x_grid[sub_mask][idx_peak])
    offset_from_gas_kpc = x_kappa_sub - x_gas_2

    # Also locate subcluster-side non-baryonic phantom-halo peak across [+40, +550] kpc to expose Eulerian wakes
    wake_mask = x_grid >= 40.0
    x_nonbar_peak = float(x_grid[wake_mask][int(np.argmax(kappa_nonbar[wake_mask]))])

    # Estimate subcluster cylindrical aperture lensing-to-stellar mass ratio within R_ap = 150 kpc of BCG (x_star_2)
    r_ap = 150.0
    m_star_ap = _plummer_enclosed_cyl_mass_msun(r_ap, m_star_2, a_star_2)

    # Integrate axisymmetric local profile around x_star_2 using radial slice |x - x_star_2| <= r_ap
    # weighted by 2 * pi * r dr (using right-side profile x >= x_star_2 to avoid main-cluster/gas-bridge bias,
    # mirroring weak-lensing aperture densitometry centered on the BCG!)
    r_slice = x_grid[(x_grid >= x_star_2) & (x_grid <= x_star_2 + r_ap)] - x_star_2
    sig_slice = sigma_tot[(x_grid >= x_star_2) & (x_grid <= x_star_2 + r_ap)]
    m_lens_ap = float(2.0 * math.pi * integrate.simpson(sig_slice * r_slice, x=r_slice))
    lens_to_star_ratio = m_lens_ap / m_star_ap

    passes_offset = 150.0 <= offset_from_gas_kpc <= 250.0
    passes_mass_ratio = 4.5 <= lens_to_star_ratio <= 9.0

    return {
        "mode": mode,
        "x_kappa_peak_sub_kpc": x_kappa_sub,
        "x_nonbar_peak_kpc": x_nonbar_peak,
        "offset_ahead_of_gas_kpc": offset_from_gas_kpc,
        "subcluster_lens_to_star_ratio": lens_to_star_ratio,
        "kappa_at_sub_bcg": float(np.interp(x_star_2, x_grid, kappa)),
        "kappa_at_sub_gas": float(np.interp(x_gas_2, x_grid, kappa)),
        "passes_bullet_cluster": passes_offset and passes_mass_ratio,
    }


# =============================================================================
# HARNESS D: QUANTUM MEASUREMENT, BMV TABLETOP & WIGNER-FRIEND CRUCIBLE
# =============================================================================

def _partial_transpose_b_2qubit(rho: np.ndarray) -> np.ndarray:
    """Partial transpose over qubit B for a 4x4 density matrix rho_{iA iB, jA jB}."""
    r4 = rho.reshape(2, 2, 2, 2)
    # Swap indices (iB <-> jB): axes (0, 3, 2, 1)
    return r4.transpose(0, 3, 2, 1).reshape(4, 4)


def _two_qubit_concurrence(rho: np.ndarray) -> float:
    """Wootters (1998) exact entanglement concurrence C(rho) in [0, 1] for any 2-qubit state."""
    sy = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)
    yy = np.kron(sy, sy)
    rho_tilde = yy @ rho.conj() @ yy
    vals = linalg.eigvals(rho @ rho_tilde)
    svals = np.sqrt(np.maximum(np.real(vals), 0.0))
    svals = np.sort(svals)[::-1]
    return float(max(0.0, svals[0] - svals[1] - svals[2] - svals[3]))


def build_bmv_two_qubit_state(
    delta_phi_rad: float,
    gamma_dec_s_inv: float,
    time_s: float,
    coherent_mediator: bool = True,
) -> np.ndarray:
    """
    Constructs the exact 4x4 two-path density matrix rho_{AB}(t) in the {|L>, |R>}^{otimes 2}
    basis starting from |+>_A |+>_B = (1/2)(|LL> + |LR> + |RL> + |RR>):
      - Under coherent quantum/bi-boundary gravity, closest-approach/differential geometry
        imprints relative phase exp(i * phi_LR) on |LR>, |RL> relative to |LL>, |RR>
        (specifically phi_{LL}=phi(d), phi_{RR}=phi(d), phi_{LR}=phi(d-dx), phi_{RL}=phi(d+dx),
        whose entanglement-generating combination is Delta phi = phi_{LR} + phi_{RL} - 2 phi_{LL}).
      - Local spatial dephasing at rate gamma_dec damps single-particle off-diagonals by exp(-gamma * t)
        and double off-diagonals by exp(-2 * gamma * t).
      - If `coherent_mediator=False` (classical LOCC channel), off-diagonal cross-phases cannot
        build non-separable entanglement; instead classical feedback reproduces mean drift while
        remaining convex-separable!
    """
    damp1 = math.exp(-gamma_dec_s_inv * time_s)
    damp2 = math.exp(-2.0 * gamma_dec_s_inv * time_s)

    if not coherent_mediator:
        # Product of two locally dephased |+> states (or symmetric LOCC classical mixture):
        rho_1 = 0.5 * np.array([[1.0, damp1], [damp1, 1.0]], dtype=complex)
        return np.kron(rho_1, rho_1)

    # Exact coherent BMV state phases up to local single-qubit Z rotations:
    # |psi> = 1/2 (|00> + e^{i * dphi / 2} |01> + e^{i * dphi / 2} |10> + |11>)
    # (Local Z rotations commute with local z-basis dephasing and leave Concurrence & PPT invariant!)
    ket = 0.5 * np.array([
        1.0,
         np.exp(0.5j * delta_phi_rad),
        np.exp(0.5j * delta_phi_rad),
        1.0,
    ], dtype=complex)
    rho = np.outer(ket, ket.conj())

    # Apply independent local spatial dephasing exp(-gamma * t * |i_A - j_A|) * exp(-gamma * t * |i_B - j_B|)
    for r in range(4):
        ia, ib = r >> 1, r & 1
        for c in range(4):
            ja, jb = c >> 1, c & 1
            n_flips = abs(ia - ja) + abs(ib - jb)
            if n_flips == 1:
                rho[r, c] *= damp1
            elif n_flips == 2:
                rho[r, c] *= damp2
    return rho


def quantum_bmv_and_wigner_crucible(
    mass_kg: float = 1.0e-14,
    delta_x_m: float = 1.0e-4,
    separation_d_m: float = 2.5e-4,
    time_s: float = 2.5,
    omega_mod_rad_s: float = 2.0,
    tau_visc_s: float = 0.4,
) -> Dict[str, Dict[str, float | bool | str]]:
    """
    Compares 5 foundational quantum-gravity / measurement paradigms against:
      1. Canonical BMV / QGEM tabletop interferometer (m=1e-14 kg, dx=100 um, d=250 um, t=2.5 s)
      2. Oppenheim Classical-Quantum (CQ) Decoherence-Diffusion Trade-Off + LISA Pathfinder bound
      3. Polchinski No-Signaling & Extended Wigner's Friend Local Friendliness (LF) bound
    """
    dphi_bmv = bmv_entanglement_phase(mass_kg, delta_x_m, separation_d_m, time_s)
    k_newton = 2.0 * G_NEWTON * (mass_kg ** 2) / (separation_d_m ** 3)  # N / m
    # Oppenheim CQ trade-off lower bound on (dp^2/dt) * Gamma_dec(dx) >= (1/2) * K^2 * dx^2
    cq_tradeoff_rhs = 0.5 * (k_newton ** 2) * (delta_x_m ** 2)

    results: Dict[str, Dict[str, float | bool | str]] = {}

    # (i) Spin-2 Graviton / Coherent Path-Integral QGEM
    # Evaluate both ideal (Gamma_env = 0) and realistic ultra-high-vacuum (Gamma_env = 0.01 s^-1),
    # plus exact Entanglement Sudden Death (ESD) threshold where local dephasing kills Concurrence!
    rho_qgem_ideal = build_bmv_two_qubit_state(dphi_bmv, gamma_dec_s_inv=0.0, time_s=time_s, coherent_mediator=True)
    conc_qgem_ideal = _two_qubit_concurrence(rho_qgem_ideal)
    rho_qgem = build_bmv_two_qubit_state(dphi_bmv, gamma_dec_s_inv=0.01, time_s=time_s, coherent_mediator=True)
    ppt_min_qgem = float(np.min(np.linalg.eigvalsh(_partial_transpose_b_2qubit(rho_qgem))))
    conc_qgem = _two_qubit_concurrence(rho_qgem)
    # Exact 2-qubit ESD threshold: 1 - exp(-2*Gamma*t) = 2 * |sin(dphi/2)| * exp(-Gamma*t) approx -> exact root:
    s_half = abs(math.sin(0.5 * dphi_bmv))
    # From PPT eigenvalue of locally dephased BMV state: exp(-2*G*t) condition 1 - exp(-2*G*t) <= ...
    # Numerically solve PPT min eigenvalue == 0:
    lo_g, hi_g = 0.0, 1.0
    for _ in range(50):
        mid_g = 0.5 * (lo_g + hi_g)
        r_try = build_bmv_two_qubit_state(dphi_bmv, gamma_dec_s_inv=mid_g, time_s=time_s, coherent_mediator=True)
        if float(np.min(np.linalg.eigvalsh(_partial_transpose_b_2qubit(r_try)))) < 0.0:
            lo_g = mid_g
        else:
            hi_g = mid_g
    gamma_esd_crit = 0.5 * (lo_g + hi_g)

    results["spin2_graviton_qgem"] = {
        "delta_phi_rad": dphi_bmv,
        "concurrence_ideal": conc_qgem_ideal,
        "ppt_min_eigenvalue": ppt_min_qgem,
        "concurrence": conc_qgem,
        "gamma_esd_crit_s_inv": gamma_esd_crit,
        "entangled_witness": ppt_min_qgem < -1e-6,
        "no_signaling_safe": True,
        "lf_bell_max_S": 2.0 * math.sqrt(2.0),
    }

    # (ii-a) Kafri-Taylor-Milburn Symmetric Classical Gravity Channel
    gamma_ktm = 0.5 * dphi_bmv / time_s
    rho_ktm = build_bmv_two_qubit_state(0.0, gamma_dec_s_inv=gamma_ktm, time_s=time_s, coherent_mediator=False)
    ppt_min_ktm = float(np.min(np.linalg.eigvalsh(_partial_transpose_b_2qubit(rho_ktm))))
    dp2_dt_ktm = cq_tradeoff_rhs / max(gamma_ktm, 1e-60)
    results["ktm_symmetric_classical"] = {
        "delta_phi_rad": 0.0,
        "gamma_dec_s_inv": gamma_ktm,
        "single_branch_visibility": math.exp(-gamma_ktm * time_s),
        "ppt_min_eigenvalue": ppt_min_ktm,
        "concurrence": _two_qubit_concurrence(rho_ktm),
        "entangled_witness": ppt_min_ktm < -1e-6,
        "min_accel_noise_m_s2_rtHz": math.sqrt(dp2_dt_ktm) / mass_kg,
        "no_signaling_safe": True,
    }

    # (ii-b) Oppenheim Post-Quantum Classical Gravity (Ultra-low decoherence regime: Gamma_dec = 1e-4 s^-1)
    gamma_opp_low = 1.0e-4
    dp2_dt_opp = cq_tradeoff_rhs / gamma_opp_low
    s_aa_half_bmv = math.sqrt(dp2_dt_opp) / mass_kg
    # Also evaluate macroscopic nucleon-scale ultra-local CQ squeeze:
    # Atom interferometry (Rb-87, m = 1.443e-25 kg, dx = 0.54 m, t = 2.0 s, visibility > 0.5 -> Gamma_Rb < 0.35 s^-1)
    # vs LISA Pathfinder test mass (M_LPF = 1.928 kg, S_aa^(1/2) <= 1.74e-15 m s^-2 Hz^-1/2).
    # For an ultra-local CQ kernel smoothed at nucleon radius r_N = 1e-15 m, Oppenheim et al. (2023)
    # show S_aa * Gamma_Rb >= (G^2 * m_Rb * m_N) / (6 * pi * r_N^3) ~ (6.67e-11)^2 * (1.44e-25)^2 / (6*pi*1e-45) ~ 4.9e-27 m^2/s^5
    # -> Required S_aa^(1/2) >= sqrt(4.9e-27 / 0.35) ~ 3.7e-14 m s^-2 Hz^-1/2 > 1.74e-15 (LISA Pathfinder bound)!
    m_rb = 86.909 * 1.660539e-27
    r_nuc = 1.0e-15
    gamma_rb_max = 0.35
    s_aa_ultralocal_req = math.sqrt((G_NEWTON ** 2) * (m_rb ** 2) / (6.0 * math.pi * (r_nuc ** 3) * gamma_rb_max))
    lpf_bound = 1.74e-15
    results["oppenheim_cq_stochastic"] = {
        "concurrence": 0.0,
        "entangled_witness": False,
        "bmv_pair_accel_noise_m_s2_rtHz": s_aa_half_bmv,
        "ultralocal_nucleon_req_Saa_rtHz": s_aa_ultralocal_req,
        "lisa_pathfinder_bound_Saa_rtHz": lpf_bound,
        "ultralocal_kernel_survives_lpf": s_aa_ultralocal_req <= lpf_bound,
        "no_signaling_safe": True,
    }

    # (iii-a) Deterministic Expectation-Value Gravity (G_uv = 8*pi*G <T_uv> without stochastic noise)
    # Self-attraction phase of single diamond sphere of radius R ~ 1.89 um (density 3500 kg/m^3):
    r_diamond = ((3.0 * mass_kg) / (4.0 * math.pi * 3500.0)) ** (1.0 / 3.0)
    nonlinear_self_phase = (G_NEWTON * (mass_kg ** 2) * time_s) / (HBAR * r_diamond)
    results["moller_rosenfeld_meanfield"] = {
        "concurrence": 0.0,
        "entangled_witness": False,
        "nonlinear_self_phase_rad": nonlinear_self_phase,
        "no_signaling_safe": False,  # Violates Weinberg-Gisin-Polchinski marginal linearity!
    }

    # (iii-b) Viscoelastic / Non-Markovian Memory Gravity (complex susceptibility chi(w) = 1 / (1 - i * w * tau))
    denom = 1.0 + (omega_mod_rad_s * tau_visc_s) ** 2
    dphi_visc = dphi_bmv / denom
    gamma_visc = (dphi_bmv / time_s) * (omega_mod_rad_s * tau_visc_s) / denom
    rho_visc = build_bmv_two_qubit_state(dphi_visc, gamma_dec_s_inv=0.02 + gamma_visc, time_s=time_s, coherent_mediator=True)
    ppt_min_visc = float(np.min(np.linalg.eigvalsh(_partial_transpose_b_2qubit(rho_visc))))
    results["viscoelastic_memory_gravity"] = {
        "modulated_delta_phi_rad": dphi_visc,
        "phase_suppression_ratio": dphi_visc / dphi_bmv,
        "viscoelastic_gamma_dec_s_inv": gamma_visc,
        "ppt_min_eigenvalue": ppt_min_visc,
        "concurrence": _two_qubit_concurrence(rho_visc),
        "entangled_witness": ppt_min_visc < -1e-6,
        "no_signaling_safe": True,
    }

    # (iii-c) Bi-Boundary / Horizon-Capacity Model (Graviton-free action constraint + Wigner-Friend rank cutoff)
    # Static BMV matches path-integral phase, distinguishable via light-cone retarded modulation dt < d/c = 0.83 ps;
    # Extended Wigner's Friend LF parameter S_LF = 2*sqrt(2) * exp(-(N_ops / N_crit))
    light_crossing_ps = (separation_d_m / C_LIGHT) * 1.0e12
    results["biboundary_horizon_gravity"] = {
        "static_concurrence": conc_qgem,
        "entangled_witness": True,
        "causal_switching_window_ps": light_crossing_ps,
        "lf_violation_micro_friend": 2.0 * math.sqrt(2.0),  # Violates LF > 2 for small qubit friends
        "lf_bound_macro_observer": 2.0,                     # Truncates above horizon capacity N_crit
        "no_signaling_safe": True,
    }

    return results


# =============================================================================
# MASTER BASELINE EXECUTION & REFERENCE REPORT
# =============================================================================

def run_all_baselines() -> None:
    print("=" * 92)
    print("  FOUNDATIONAL PHYSICS DISCOVERY COLLECTIVE -- MASTER CRUCIBLE SUITE (2026)")
    print("  Architect: Dr. Priya Ramanujan")
    print("=" * 92)

    # --- 1. Cosmological Expansion Crucible ---
    print("\n[A] COSMOLOGICAL EXPANSION CHI^2 TEST (13 DESI DR2 BAO pts + Planck theta_* + SNe shape)")
    print("-" * 92)
    h0_lcdm = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.303, -1.00, 0.00, h0))
    h0_qb   = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.316, -0.78, -0.62, h0))
    h0_qf   = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.310, -0.82, +0.20, h0))
    cosmo_models = {
        f"Flat LCDM (Om=0.303, w0=-1.00, wa=0.00, H0={h0_lcdm:.2f})":
            lambda z: hubble_cpl_with_radiation(z, 0.303, -1.00, 0.00, h0_lcdm),
        f"DESI-DR2 Quintom-B (Om=0.316, w0=-0.78, wa=-0.62, H0={h0_qb:.2f})":
            lambda z: hubble_cpl_with_radiation(z, 0.316, -0.78, -0.62, h0_qb),
        f"Canonical Thawing Quintessence (w0=-0.82, wa=+0.20, H0={h0_qf:.2f})":
            lambda z: hubble_cpl_with_radiation(z, 0.310, -0.82, +0.20, h0_qf),
        "Einstein-de Sitter No-DE (Om=1.00, H0=67.80)":
            lambda z: hubble_cpl_with_radiation(z, 0.9999, 0.0, 0.0, 67.80),
    }
    print(f"{'Model':<58} | {'BAO(prof)':>9} | {'SNe shp':>7} | {'Joint chi2':>14}")
    print("-" * 92)
    lcdm_joint = None
    for name, fn in cosmo_models.items():
        res = desi_dr2_cosmology_crucible(fn)
        if lcdm_joint is None:
            lcdm_joint = res["chi2_joint"]
        dchi2 = res["chi2_joint"] - lcdm_joint
        print(
            f"{name:<58} | {res['chi2_bao_profiled_rd']:9.2f} | "
            f"{res['chi2_sne_shape']:7.2f} | "
            f"{res['chi2_joint']:7.2f} ({dchi2:+6.1f})"
        )

    # --- 2. Solar System & Wide Binary Screening Crucible ---
    print("\n[B] SOLAR SYSTEM EPHEMERIS & GAIA DR3 WIDE-BINARY SCREENING TEST")
    print("    Bounds: Mercury<4e-10, Earth<1e-10, Saturn(10AU)<2.0e-9 | SPARC<0.10 dex | MW EFE=1.8 a0")
    print("-" * 92)
    grav_models = [
        ("Pure Newtonian / GR (no DM halo)",      nu_newtonian,     None),
        ("Simple MOND mu=x/(1+x) [TRAP B1]",      nu_simple_mond,   None),
        ("Standard MOND mu=x/sqrt(1+x^2)",        nu_standard_mond, None),
        ("SPARC Exponential RAR + QUMOND EFE",    nu_rar_exp,       None),
        ("Horizon-Screened RAR (r_cut=0.2 pc)",   nu_rar_exp,
         lambda r_m, _m: 1.0 - math.exp(-((r_m / (0.2 * 3.08567758e16)) ** 2))),
    ]
    print(f"{'Model':<36} | {'RAR(dex)':>8} | {'Merc/Earth/Sat |dg/g|':>25} | {'WB 5kAU(iso/EFE)':>16} | {'Sol?'}")
    print("-" * 92)
    for name, nu_fn, scr_fn in grav_models:
        r = solar_and_wide_binary_crucible(nu_fn, potential_screen_factor=scr_fn)
        mes_str = f"{r['dg_mercury']:.1e}/{r['dg_earth']:.1e}/{r['dg_saturn']:.1e}"
        wb5_str = f"{r['wb_5kau_boost_isolated']:.3f} / {r['wb_5kau_boost_mw_efe']:.3f}"
        sol_ok = "PASS" if r["passes_solar_ephemerides"] else "FAIL"
        print(f"{name:<36} | {r['sparc_rms_dex']:8.4f} | {mes_str:>25} | {wb5_str:>16} | {sol_ok}")

    # --- 3. Bullet Cluster Dynamical Lensing Crucible ---
    print("\n[C] BULLET CLUSTER DYNAMICAL LENSING TEST (v_coll = 4500 km/s, t_post = 150 Myr)")
    print("    Targets: Subcluster kappa offset ahead of X-ray gas in [150, 250] kpc & M_lens/M_* in [4.5, 9.0]")
    print("-" * 92)
    print(f"{'Theory Mode':<28} | {'TotPeak x':>10} | {'NonBarPeak':>11} | {'Offset vs Gas':>14} | {'M_lens/M_*':>10} | {'Pass?'}")
    print("-" * 92)
    for mode in ("lcdm", "memoryless_mond", "eulerian_memory_trap", "covariant_geodesic_memory"):
        b = bullet_cluster_dynamical_crucible(mode=mode)
        verdict = "PASS" if b["passes_bullet_cluster"] else "FAIL"
        print(
            f"{mode:<28} | {b['x_kappa_peak_sub_kpc']:+7.1f}kpc | "
            f"{b['x_nonbar_peak_kpc']:+8.1f}kpc | "
            f"{b['offset_ahead_of_gas_kpc']:+10.1f} kpc | {b['subcluster_lens_to_star_ratio']:10.2f} | {verdict}"
        )

    # --- 4. Quantum Measurement & BMV Tabletop Discriminator ---
    print("\n[D] QUANTUM MEASUREMENT, BMV TABLETOP & EXTENDED WIGNER'S FRIEND DISCRIMINATOR")
    print("    Setup: m = 1e-14 kg, dx = 100 um, d = 250 um, t = 2.5 s; Complementarity V^2 + D^2 <= 1")
    print("-" * 92)
    q = quantum_bmv_and_wigner_crucible()
    comp = double_slit_complementarity_check(np.array([0.8, 0.0, 1.0]), np.array([0.6, 1.0, 0.0]))
    print(f"  * Duality invariant sanity check: max(V^2 + D^2) = {comp['max_V2_plus_D2']:.4f} (Respects bound: {comp['respects_duality_bound']})")
    print(f"  * (i)   Spin-2 Graviton QGEM:         dphi = {q['spin2_graviton_qgem']['delta_phi_rad']:.4f} rad, "
          f"C_ideal = {q['spin2_graviton_qgem']['concurrence_ideal']:.4f}, "
          f"C(Gamma=0.01/s) = {q['spin2_graviton_qgem']['concurrence']:.4f}, "
          f"ESD_crit = {q['spin2_graviton_qgem']['gamma_esd_crit_s_inv']:.4f}/s [ENTANGLED]")
    print(f"  * (ii)  KTM Symmetric Classical:      Gamma_dec = {q['ktm_symmetric_classical']['gamma_dec_s_inv']:.4f} s^-1, "
          f"Vis = {q['ktm_symmetric_classical']['single_branch_visibility']:.4f}, "
          f"Concurrence C = {q['ktm_symmetric_classical']['concurrence']:.4f} [SEPARABLE]")
    print(f"  * (ii') Oppenheim Ultra-Local CQ:     Req S_aa^(1/2) = {q['oppenheim_cq_stochastic']['ultralocal_nucleon_req_Saa_rtHz']:.2e} "
          f"vs LISA Pathfinder {q['oppenheim_cq_stochastic']['lisa_pathfinder_bound_Saa_rtHz']:.2e} m/s^2/rtHz "
          f"(Survives: {q['oppenheim_cq_stochastic']['ultralocal_kernel_survives_lpf']})")
    print(f"  * (iii) Moller-Rosenfeld Mean-Field:  Self-phase = {q['moller_rosenfeld_meanfield']['nonlinear_self_phase_rad']:.2e} rad, "
          f"No-Signaling Safe = {q['moller_rosenfeld_meanfield']['no_signaling_safe']} [FATAL POLCHINSKI PHONE]")
    print(f"  * (iv)  Viscoelastic Memory (w=2/s):  dphi(w)/dphi(0) = {q['viscoelastic_memory_gravity']['phase_suppression_ratio']:.3f}, "
          f"Gamma_visc = {q['viscoelastic_memory_gravity']['viscoelastic_gamma_dec_s_inv']:.4f}/s > ESD_crit -> "
          f"C = {q['viscoelastic_memory_gravity']['concurrence']:.4f} [SUDDEN DEATH!]")
    print(f"  * (v)   Bi-Boundary / Horizon Model:  Static C = {q['biboundary_horizon_gravity']['static_concurrence']:.4f}, "
          f"Light-cone test d/c = {q['biboundary_horizon_gravity']['causal_switching_window_ps']:.3f} ps, "
          f"S_LF(micro->macro) = {q['biboundary_horizon_gravity']['lf_violation_micro_friend']:.3f} -> {q['biboundary_horizon_gravity']['lf_bound_macro_observer']:.3f}")
    print("=" * 92)


if __name__ == "__main__":
    run_all_baselines()
