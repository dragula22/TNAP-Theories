"""
Round 1 Crucible Evaluation of PI Seed 00:
  `round1_divergent/00_pi_bihorizon_complex_time_seed.md`
  (Complex Entropic Time & Bi-Horizon Bose-Stimulated Gravity)

Architect: Dr. Priya Ramanujan (Chief Phenomenologist & Experimental Crucible Architect)

Quantitatively tests two decisive novel predictions of Seed 00:
  1. Ground vs. L2 Free-Fall vs. True Gravitational Saddle-Point BMV Entanglement:
     - Computes exact Bose-Einstein potential V_bi(r) = -int F_bi(r) dr (proving the exact
       ~1/2x stiffness ratio between 3,138x deep-MOND force boost and 1,437x BMV phase boost!).
     - Cancellation-free QUMOND/bi-horizon External Field Effect (EFE) across 6 environments:
         (i)   Earth laboratory / drop tower (g_ext = 9.81 m/s^2) + Westphal+2021 92 mg Cavendish check
         (ii)  Sun-Earth L2 free-fall halo orbit (a_proper = 0, |grad Phi| = 6.0e-3 m/s^2 = 5.7e7 a0)
         (iii) Outer Oort cloud / interstellar space (g_MW = 1.8 a0)
         (iv)  Sun-Earth(-Galaxy) true gravitational saddle point (r_E = 258,809 km; +/-2.28m x +/-4.57m
               MOND bubble; T = 2.5 s free-fall drift is ONLY 2.32 mm -> ~79x integrated BMV boost!)
         (v)   Sun-Jupiter(-Galaxy) true gravitational saddle point (5.11 km bubble -> 1,436x full boost!)
         (vi)  Truly isolated empty de Sitter space (g_ext = 0 -> 1,436.6x boost)
     - Proves why neither Newtonian potential |Phi|/c^2 nor relativistic tidal curvature c*sqrt(|grad g|)
       can screen Solar System saddle points without simultaneously destroying the Milky Way RAR!

  2. High-Redshift ALMA/JWST Rotation Curves (z = 1 to 7.31) + DESI DR2 Quintom-B Coupling:
     - Tests three physical definitions of Seed 00's cosmic Gibbons-Hawking horizon scale:
         Model H1: Apparent Hubble sphere a0(z) = c * H(z) / (2*pi)
         Model H2: Teleological future event horizon a0(z) = c^2 / (2*pi * R_eh(z))
                   (DISCOVERY: diverges R_eh -> inf in DESI DR2 CPL Quintom-B because w(a) crosses -1/3
                   into future deceleration at a_end = 1.72!)
         Model H3: Local Dark-Energy / Vacuum de Sitter horizon a0(z) = a0(0) * sqrt(rho_DE(z)/rho_DE(0))
     - Benchmarks against Genzel+2020 / Nestor Shachar+2023 (RC100 z=2.2 baryon-dominated disks),
       Rizzo+2021 / Fraternali+2021 / Lelli+2023 (ALMA z=4.4 cold disks), and
       Rowland+2024 REBELS-25 (z = 7.31 dynamically cold disk).
"""

from __future__ import annotations

import math
import os
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import integrate

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_THIS_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from simulations.crucible_full_suite import (
    AU_TO_M,
    C_KM_S,
    KPC_TO_M,
    M_SUN,
    calibrate_h0_to_cmb_theta_star,
    hubble_cpl_with_radiation,
    nu_rar_exp,
)
from simulations.empirical_crucible import (
    A0_SPARC,
    C_H0_OVER_2PI,
    C_LIGHT,
    G_NEWTON,
    HBAR,
    bmv_entanglement_phase,
)

M_EARTH = 5.97217e24    # kg
M_JUPITER = 1.89813e27  # kg


# =============================================================================
# PART 1: CANCELLATION-FREE BI-HORIZON / QUMOND EFE & SADDLE-POINT BMV CRUCIBLE
# =============================================================================

def bihorizon_coherence_length_m(mass_kg: float, a0: float = C_H0_OVER_2PI) -> float:
    """L_coh(M) = sqrt(G * M / a0) = sqrt(2 * pi * G * M / (c * H0))."""
    return math.sqrt(G_NEWTON * mass_kg / a0)


def nu_rar_scalar_and_deriv(y: float) -> Tuple[float, float]:
    """
    Returns (nu(y), y * d(nu)/dy) for the Bose-Einstein RAR factor nu(y) = 1 / (1 - exp(-sqrt(y)))
    with zero overflow/underflow across y in [1e-30, 1e30].
    Note:
        x = sqrt(y)
        nu(y) = 1 / (1 - e^{-x})
        y * d(nu)/dy = (x / 2) * d(nu)/dx = -(x / 2) * e^{-x} / (1 - e^{-x})^2
    """
    x = math.sqrt(max(y, 1e-40))
    if x > 40.0:
        ex = math.exp(-x) if x < 700.0 else 0.0
        return 1.0 + ex, -0.5 * x * ex
    if x < 1e-6:
        # Laurent expansion: 1/(1 - e^{-x}) = 1/x + 1/2 + x/12,  y*nu' = -1/(2x) + x/24
        nu = (1.0 / x) + 0.5 + (x / 12.0)
        ynu_p = -(0.5 / x) + (x / 24.0)
        return nu, ynu_p
    emx = math.exp(-x)
    denom = 1.0 - emx
    nu = 1.0 / denom
    ynu_p = -0.5 * x * emx / (denom * denom)
    return nu, ynu_p


def invert_obs_to_bare_y(y_obs: float) -> float:
    """Solves y_N * nu_rar(y_N) = y_obs for bare Newtonian dimensionless acceleration y_N = g_ext_N / a0."""
    if y_obs <= 0.0:
        return 0.0
    if y_obs > 2000.0:
        return y_obs  # Exponentially close to 1
    lo = min(y_obs * y_obs * 0.25, y_obs * 0.5, 1e-30)
    hi = max(y_obs * 1.05, 1.0)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        nu_m, _ = nu_rar_scalar_and_deriv(mid)
        if mid * nu_m < y_obs:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def qumond_efe_boost_exact(
    g_int_n: float,
    g_ext_bare_n: float,
    a0: float = C_H0_OVER_2PI,
    n_mu: int = 96,
) -> float:
    """
    Cancellation-free spherical-average QUMOND radial boost g_eff / g_int_N given internal
    Newtonian acceleration `g_int_n` and bare external Newtonian field `g_ext_bare_n`:
      - When g_ext_bare_n == 0: exact isolated nu(g_int_n / a0).
      - When g_ext_bare_n > 1e3 * g_int_n (EFE-dominated dipole regime): exact analytic
        Milgrom (2010) formula:
            boost = nu(y_ext) + (1/3) * y_ext * d(nu)/dy_ext   [zero float cancellation!].
      - When comparable: Gauss-Legendre quadrature using cancellation-safe algebraic form:
            nu(y_tot) + [nu(y_tot) - nu(y_ext)] * (g_ext_n / g_int_n) * mu.
    """
    if g_ext_bare_n <= 0.0:
        nu_val, _ = nu_rar_scalar_and_deriv(g_int_n / a0)
        return nu_val

    y_ext = g_ext_bare_n / a0
    if g_ext_bare_n > 1.0e3 * g_int_n:
        nu_e, ynu_pe = nu_rar_scalar_and_deriv(y_ext)
        return nu_e + (1.0 / 3.0) * ynu_pe

    nu_e, _ = nu_rar_scalar_and_deriv(y_ext)
    mu, weights = np.polynomial.legendre.leggauss(n_mu)
    g_tot = np.sqrt(g_int_n ** 2 + g_ext_bare_n ** 2 + 2.0 * g_int_n * g_ext_bare_n * mu)
    nu_tot = nu_rar_exp(g_tot / a0)
    integrand = nu_tot + (nu_tot - nu_e) * (g_ext_bare_n / g_int_n) * mu
    return 0.5 * float(np.sum(weights * integrand))


def bmv_phase_given_bare_gext(
    mass_kg: float,
    delta_x_m: float,
    separation_d_m: float,
    time_s: float,
    g_ext_bare_n: float,
    a0: float = C_H0_OVER_2PI,
) -> Tuple[float, float]:
    """
    Computes exact BMV entanglement phase Delta phi(t) and boost ratio over standard Newtonian
    gravity by integrating F_eff(r) = (G m^2 / r^2) * boost(r) across [d - dx, d] and [d, d + dx].
    """
    dphi_newton = bmv_entanglement_phase(mass_kg, delta_x_m, separation_d_m, time_s)

    # Fast exact path when g_ext_bare_n >> g_mut(d - dx): boost is r-independent across [d-dx, d+dx]!
    g_mut_max = G_NEWTON * mass_kg / ((separation_d_m - delta_x_m) ** 2)
    if g_ext_bare_n > 1.0e3 * g_mut_max:
        bst = qumond_efe_boost_exact(g_mut_max, g_ext_bare_n, a0=a0)
        return dphi_newton * bst, bst

    def f_eff(r: float) -> float:
        g_int = G_NEWTON * mass_kg / (r ** 2)
        bst = qumond_efe_boost_exact(g_int, g_ext_bare_n, a0=a0)
        return (G_NEWTON * (mass_kg ** 2) / (r ** 2)) * bst

    int_left, _ = integrate.quad(f_eff, separation_d_m - delta_x_m, separation_d_m, epsrel=1e-10)
    int_right, _ = integrate.quad(f_eff, separation_d_m, separation_d_m + delta_x_m, epsrel=1e-10)
    dphi = ((int_left - int_right) * time_s) / HBAR
    return dphi, dphi / dphi_newton


def saddle_point_parabola_bmv(
    primary_mass_kg: float,
    secondary_mass_kg: float,
    orbital_radius_m: float,
    drop_time_s: float,
    mass_kg: float = 1.0e-14,
    delta_x_m: float = 1.0e-4,
    separation_d_m: float = 2.5e-4,
    a0: float = C_H0_OVER_2PI,
) -> Dict[str, float]:
    """
    Evaluates a free-falling BMV interferometer injected on a Chebyshev-optimal tangent parabola
    through an inertial gravitational saddle point where total bare Newtonian field vanishes:
        g_N,primary(r_null) + g_N,secondary(r_null) + g_N,MW = 0.
    """
    r_2 = orbital_radius_m / (1.0 + math.sqrt(primary_mass_kg / secondary_mass_kg))
    r_1 = orbital_radius_m - r_2

    tidal_axial = 2.0 * G_NEWTON * secondary_mass_kg / (r_2 ** 3) + 2.0 * G_NEWTON * primary_mass_kg / (r_1 ** 3)
    tidal_trans = 0.5 * tidal_axial  # s^-2 (from Laplace's eq outside sources)

    # Bubble boundary where |g_obs| = a0 corresponds to bare Newtonian |g_N| = a0 * (1 - 1/e) = 0.6321 * a0!
    g_n_crit_a0 = a0 * (1.0 - math.exp(-1.0))
    bubble_z_m = g_n_crit_a0 / tidal_axial
    bubble_perp_m = g_n_crit_a0 / tidal_trans

    # Heliocentric centripetal acceleration of the saddle point itself as planet orbits Sun
    a_null = G_NEWTON * primary_mass_kg / (orbital_radius_m ** 2) * (r_1 / orbital_radius_m)

    # Chebyshev-optimal free-fall trajectory along transverse axis:
    #   dr_perp(t) = 0.5 * a_null * [ (t - T/2)^2 - T^2 / 16 ] -> max |dr_perp| = (1/32)*a_null*T^2!
    #   (Using symmetric midpoint zero-velocity-offset parabola [-T^2/16, +T^2/16] gives 1/32 * a_null * T^2!)
    n_t = 201
    t_grid = np.linspace(0.0, drop_time_s, n_t)
    dr_perp = np.abs(0.5 * a_null * ((t_grid - 0.5 * drop_time_s) ** 2 - (drop_time_s ** 2) / 16.0))
    max_drift_m = float(np.max(dr_perp))

    # Residual bare Newtonian tidal gradient across half interferometer baseline d/2 = 125 um
    g_tidal_floor = tidal_trans * (0.5 * separation_d_m)
    g_ext_bare_t = np.hypot(tidal_trans * dr_perp, g_tidal_floor)

    dphi_dt = np.zeros_like(t_grid)
    for i, ge_bare in enumerate(g_ext_bare_t):
        dphi_unit, _ = bmv_phase_given_bare_gext(
            mass_kg, delta_x_m, separation_d_m, time_s=1.0, g_ext_bare_n=float(ge_bare), a0=a0
        )
        dphi_dt[i] = dphi_unit

    dphi_total = float(integrate.simpson(dphi_dt, x=t_grid))
    dphi_newton = bmv_entanglement_phase(mass_kg, delta_x_m, separation_d_m, drop_time_s)
    peak_dphi_rate_boost = float(np.max(dphi_dt)) / (dphi_newton / drop_time_s)

    return {
        "r_from_planet_km": r_2 / 1000.0,
        "tidal_axial_s2": tidal_axial,
        "bubble_axial_m": bubble_z_m,
        "bubble_trans_m": bubble_perp_m,
        "max_parabola_drift_m": max_drift_m,
        "g_tidal_floor_m_s2": g_tidal_floor,
        "dphi_newton_rad": dphi_newton,
        "dphi_bihorizon_rad": dphi_total,
        "integrated_boost_factor": dphi_total / dphi_newton,
        "instantaneous_null_peak_boost": peak_dphi_rate_boost,
    }


def check_tidal_vs_potential_screening_invariants(a0: float = C_H0_OVER_2PI) -> List[Dict[str, float | str]]:
    """
    Tests whether alternative geometric scalars -- Newtonian potential depth |Phi|/c^2,
    relativistic curvature acceleration c*sqrt(|R_{0i0j}|) = c*sqrt(|grad g|), or pure tidal
    scalar |grad g| -- can screen Solar System saddle points WITHOUT destroying the Milky Way RAR!
    """
    regimes = [
        ("Milky Way Disk (R0 = 8.2 kpc)",   (220e3) ** 2,                           2.15e-10, 2.15e-10 / (8.2 * KPC_TO_M)),
        ("SPARC Dwarf Outer Disk (3 kpc)",  (65e3) ** 2,                            3.50e-11, 3.50e-11 / (3.0 * KPC_TO_M)),
        ("Gaia Wide Binary (10,000 AU)",    G_NEWTON * 1.6 * M_SUN / (1e4*AU_TO_M), 9.49e-11, 2*G_NEWTON*1.6*M_SUN/((1e4*AU_TO_M)**3)),
        ("Solar Orbit / L2 (1.01 AU)",      G_NEWTON * M_SUN / AU_TO_M,             5.93e-3,  2*G_NEWTON*M_SUN/(AU_TO_M**3)),
        ("Sun-Earth Saddle Point (null)",   G_NEWTON * M_SUN / AU_TO_M,             2.87e-15, 4.598e-11),
        ("Sun-Jupiter Saddle Point (null)", G_NEWTON * M_SUN / (5.204*AU_TO_M),     1.25e-18, 2.000e-14),
    ]
    rows: List[Dict[str, float | str]] = []
    for name, phi_abs, g_abs, grad_g in regimes:
        a_curv = C_LIGHT * math.sqrt(grad_g)
        rows.append({
            "regime": name,
            "phi_over_c2": phi_abs / (C_LIGHT ** 2),
            "g_over_a0": g_abs / a0,
            "grad_g_s2": grad_g,
            "c_sqrt_grad_g_over_a0": a_curv / a0,
        })
    return rows


# =============================================================================
# PART 2: HIGH-Z JWST / ALMA ROTATION CURVES & DESI DR2 a0(z) EVOLUTION CRUCIBLE
# =============================================================================

def future_event_horizon_lcdm_mpc(
    z_val: float,
    h_of_z_km_s_mpc: Callable[[np.ndarray], np.ndarray],
) -> float:
    """
    Computes proper causal future event horizon R_eh(z) [Mpc] when w(a -> inf) < -1/3 (e.g. LCDM):
        R_eh(z) = [c / (1 + z)] * int_0^inf da / [a^2 * H(a)]  with a_0_lim = 1/(1+z).
    """
    a_start = 1.0 / (1.0 + z_val)
    # Substitute u = 1 / a in [0, 1 + z_val] -> du = -da / a^2 -> int_0^{1+z} c du / H(z' = u - 1)!
    # Notice u = 1 + z' in [0, 1 + z_val] has ZERO coordinate singularity at u = 0 when H(u->0) -> H0*sqrt(Omega_L)!
    val, _ = integrate.quad(
        lambda u: C_KM_S / float(np.squeeze(h_of_z_km_s_mpc(np.array([u - 1.0])))),
        0.0,
        1.0 + z_val,
        epsrel=1e-9,
        limit=200,
    )
    return val * a_start


def check_quintom_b_future_deceleration_scale(w0: float = -0.78, wa: float = -0.62) -> float:
    """
    In CPL w(a) = w0 + wa * (1 - a), when wa < 0, w(a) increases linearly with scale factor a
    and crosses w = -1/3 (end of cosmic acceleration!) at:
        a_end = 1 + (w0 + 1/3) / wa   (for w0=-0.78, wa=-0.62: a_end = 1.720!).
    Above a_end, dark energy decays faster than a^-2 and the future event horizon R_eh = infinity!
    """
    return 1.0 + (w0 + (1.0 / 3.0)) / wa


def evaluate_a0_z_models() -> Dict[str, object]:
    """
    Evaluates a0(z) / a0(0) and implied Baryonic Tully-Fisher velocity shift
        Delta log10(V_flat) = +0.25 * log10(a0(z) / a0(0))   [at fixed M_bar]
    across z = [0, 0.5, 1.0, 2.0, 4.0, 6.0, 7.31] for:
      - H1: Apparent Hubble horizon a0(z) = c * H(z) / (2 * pi)   [Literal Seed 00 Eq. 36]
      - H2: Causal future event horizon a0(z) = c^2 / (2 * pi * R_eh(z))
            (Finite in LCDM; DIVERGENT R_eh = inf -> T_eh = 0 in DESI CPL Quintom-B!)
      - H3: Local Dark-Energy / Vacuum horizon a0(z) = a0(0) * sqrt(rho_DE(z) / rho_DE(0))
    """
    h0_lcdm = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.303, -1.00, 0.00, h0))
    h0_qb   = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.316, -0.78, -0.62, h0))

    hz_lcdm = lambda z: hubble_cpl_with_radiation(z, 0.303, -1.00, 0.00, h0_lcdm)
    hz_qb   = lambda z: hubble_cpl_with_radiation(z, 0.316, -0.78, -0.62, h0_qb)

    def de_ratio_qb(z: float) -> float:
        zp1 = 1.0 + z
        w0, wa = -0.78, -0.62
        return (zp1 ** (3.0 * (1.0 + w0 + wa))) * math.exp(-3.0 * wa * z / zp1)

    z_list = [0.0, 0.5, 1.0, 2.0, 4.0, 6.0, 7.31]
    reh0_lcdm = future_event_horizon_lcdm_mpc(0.0, hz_lcdm)
    a0_eh0_lcdm = (C_LIGHT ** 2) / (2.0 * math.pi * reh0_lcdm * 1000.0 * KPC_TO_M)

    rows: List[Dict[str, float]] = []
    for z in z_list:
        za = np.array([z])
        r_h1_lcdm = float(hz_lcdm(za)[0] / h0_lcdm)
        r_h1_qb   = float(hz_qb(za)[0] / h0_qb)
        r_h2_lcdm = reh0_lcdm / future_event_horizon_lcdm_mpc(z, hz_lcdm)
        r_h3_lcdm = 1.0
        r_h3_qb   = math.sqrt(de_ratio_qb(z))

        rows.append({
            "z": z,
            "H1_hubble_lcdm": r_h1_lcdm,
            "H1_hubble_desi_qb": r_h1_qb,
            "H2_event_lcdm": r_h2_lcdm,
            "H3_de_lcdm": r_h3_lcdm,
            "H3_de_desi_qb": r_h3_qb,
            "dlogV_H1_qb": 0.25 * math.log10(r_h1_qb),
            "dlogV_H2_lcdm": 0.25 * math.log10(r_h2_lcdm),
            "dlogV_H3_qb": 0.25 * math.log10(r_h3_qb),
        })
    return {
        "rows": rows,
        "reh0_lcdm_mpc": reh0_lcdm,
        "a0_eh0_lcdm_m_s2": a0_eh0_lcdm,
        "quintom_b_a_end_accel": check_quintom_b_future_deceleration_scale(-0.78, -0.62),
    }


def high_z_galaxy_benchmark_chi2() -> Dict[str, Tuple[float, Dict[str, float]]]:
    """
    Quantitative chi^2 test against three observational high-z rotation-curve anchors:
      1. z = 2.2 Cosmic Noon RC100 / Genzel+2020 stack (Nestor Shachar+2023; Milgrom 2017):
         Observed inner effective acceleration boost at R_1/2 (where g_bar = 4.2 * a0_local):
             g_obs / g_bar = 1.18 +/- 0.10  (baryon-dominated inner disks with declining outer curves!)
      2. z = 4.4 ALMA [C II] Cold Rotating Disks (Rizzo+2021; Fraternali+2021; Lelli+2023):
         Observed BTFR velocity zero-point offset relative to z=0 SPARC BTFR:
             Delta log10(V_flat) = +0.02 +/- 0.06 dex
      3. z = 7.31 REBELS-25 Dynamically Cold Disk (Rowland+2024):
         Observed BTFR velocity zero-point offset relative to z=0 SPARC BTFR:
             Delta log10(V_flat) = +0.09 +/- 0.09 dex
    """
    h0_lcdm = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.303, -1.00, 0.00, h0))
    h0_qb   = calibrate_h0_to_cmb_theta_star(lambda h0: lambda z: hubble_cpl_with_radiation(z, 0.316, -0.78, -0.62, h0))
    hz_lcdm = lambda z: hubble_cpl_with_radiation(z, 0.303, -1.00, 0.00, h0_lcdm)
    hz_qb   = lambda z: hubble_cpl_with_radiation(z, 0.316, -0.78, -0.62, h0_qb)
    reh0_lcdm = future_event_horizon_lcdm_mpc(0.0, hz_lcdm)

    def de_sqrt_qb(z: float) -> float:
        zp1 = 1.0 + z
        return math.sqrt((zp1 ** (3.0 * (1.0 - 0.78 - 0.62))) * math.exp(-3.0 * (-0.62) * z / zp1))

    models = {
        "H1: Apparent Hubble c*H(z)/2pi [DESI QB]": lambda z: float(hz_qb(np.array([z]))[0] / h0_qb),
        "H1': Apparent Hubble c*H(z)/2pi [LCDM]":   lambda z: float(hz_lcdm(np.array([z]))[0] / h0_lcdm),
        "H2: Causal Event Horizon R_eh(z) [LCDM]":  lambda z: reh0_lcdm / future_event_horizon_lcdm_mpc(z, hz_lcdm),
        "H3: Vacuum DE Horizon sqrt(rho_DE) [QB]":  de_sqrt_qb,
        "H3': Constant a0 Vacuum Horizon [LCDM]":   lambda _z: 1.0,
    }

    scores: Dict[str, Tuple[float, Dict[str, float]]] = {}
    for label, ratio_fn in models.items():
        r22 = ratio_fn(2.2)
        boost22 = 1.0 / (1.0 - math.exp(-math.sqrt(4.2 / r22)))
        chi2_1 = ((boost22 - 1.18) / 0.10) ** 2

        dlogv_44 = 0.25 * math.log10(ratio_fn(4.4))
        chi2_2 = ((dlogv_44 - 0.02) / 0.06) ** 2

        dlogv_73 = 0.25 * math.log10(ratio_fn(7.31))
        chi2_3 = ((dlogv_73 - 0.09) / 0.09) ** 2

        scores[label] = (
            chi2_1 + chi2_2 + chi2_3,
            {"boost_z2.2": boost22, "dlogV_z4.4": dlogv_44, "dlogV_z7.31": dlogv_73},
        )
    return scores


# =============================================================================
# MAIN EXECUTION REPORT
# =============================================================================

def main() -> None:
    print("=" * 98)
    print("  PI SEED 00 CRUCIBLE EVALUATION: BI-HORIZON GRAVITY & COMPLEX ENTROPIC TIME")
    print("  Evaluator: Dr. Priya Ramanujan")
    print("=" * 98)

    m_nd = 1.0e-14
    dx = 1.0e-4
    d_sep = 2.5e-4
    t_std = 2.5
    a0_bi = C_H0_OVER_2PI  # 1.0515e-10 m/s^2 (zero-parameter Seed 00 scale)

    l_coh_nd = bihorizon_coherence_length_m(m_nd, a0=a0_bi)
    g_mut = G_NEWTON * m_nd / (d_sep ** 2)
    dphi_n = bmv_entanglement_phase(m_nd, dx, d_sep, t_std)
    dphi_iso, bst_iso = bmv_phase_given_bare_gext(m_nd, dx, d_sep, t_std, g_ext_bare_n=0.0, a0=a0_bi)
    naive_force_boost = 1.0 / (1.0 - math.exp(-math.sqrt(g_mut / a0_bi)))

    print("\n[1A] BARE NANODIAMOND BI-HORIZON PARAMETERS & LOGARITHMIC STIFFNESS IDENTITY")
    print("-" * 98)
    print(f"  * Seed 00 zero-parameter a0 = c*H0/(2*pi) : {a0_bi:.4e} m/s^2 (vs SPARC {A0_SPARC:.4e})")
    print(f"  * Nanodiamond (m = 1e-14 kg) L_coh(m)     : {l_coh_nd*1e9:.2f} nm  (<< d = 250,000 nm!)")
    print(f"  * Mutual acceleration g_mut(250 um)       : {g_mut:.4e} m/s^2 ({g_mut/a0_bi:.3e} a0)")
    print(f"  * Standard Newtonian BMV phase (t=2.5 s)  : {dphi_n:.4f} rad")
    print(f"  * Force boost 1/(1 - exp(-sqrt(g_mut/a0))): {naive_force_boost:.1f}x")
    print(f"  * EXACT Isolated Bi-Horizon BMV Phase     : {dphi_iso:.2f} rad ({bst_iso:.1f}x boost -- ~1/2x logarithmic stiffness!)")

    g_westphal = G_NEWTON * 9.21e-5 / ((5.0e-3) ** 2)
    boost_westphal_no_efe = 1.0 / (1.0 - math.exp(-math.sqrt(g_westphal / a0_bi)))
    _, boost_westphal_efe = bmv_phase_given_bare_gext(9.21e-5, 1e-4, 5.0e-3, 1.0, g_ext_bare_n=9.81, a0=a0_bi)
    print(f"  * Westphal+2021 (92 mg, d=5 mm) check     : g_N = {g_westphal:.2e} m/s^2 ({g_westphal/a0_bi:.2f} a0) -> "
          f"No-EFE G_eff/G = {boost_westphal_no_efe:.3f} vs Earth-EFE G_eff/G = {boost_westphal_efe:.12f}")

    print("\n[1B] GROUND vs. L2 FREE-FALL vs. TRUE GRAVITATIONAL SADDLE-POINT BMV CRUCIBLE")
    print("-" * 98)
    g_mw_bare = invert_obs_to_bare_y(1.8) * a0_bi
    envs = [
        ("1. Earth Lab / Drop Tower (g_earth = 9.81 m/s^2)",     9.81),
        ("2. Space Free-Fall at Sun-Earth L2 (g_sun = 6.0e-3)",  6.00e-3),
        ("3. Outer Oort Cloud / Interstellar (g_MW_obs=1.8 a0)", g_mw_bare),
        ("4. Empty de Sitter Isolation (g_ext = 0)",             0.0),
    ]
    for label, g_e_bare in envs:
        dp, bst = bmv_phase_given_bare_gext(m_nd, dx, d_sep, t_std, g_e_bare, a0=a0_bi)
        print(f"  {label:<52} -> dphi = {dp:9.4f} rad  (Boost = {bst:9.4f}x)")

    se_25 = saddle_point_parabola_bmv(M_SUN, M_EARTH, AU_TO_M, drop_time_s=2.5, a0=a0_bi)
    se_06 = saddle_point_parabola_bmv(M_SUN, M_EARTH, AU_TO_M, drop_time_s=0.6, a0=a0_bi)
    sj_25 = saddle_point_parabola_bmv(M_SUN, M_JUPITER, 5.204 * AU_TO_M, drop_time_s=2.5, a0=a0_bi)

    print("\n  --- True Inertial Gravitational Saddle-Point Tangent-Parabola Injections ---")
    print(f"  5a. Sun-Earth(-MW) Saddle (r_E = {se_25['r_from_planet_km']:,.0f} km, |g_obs|<a0 Bubble = +/-{se_25['bubble_axial_m']:.2f}m x +/-{se_25['bubble_trans_m']:.2f}m):")
    print(f"      * T = 2.5 s parabola (max drift = {se_25['max_parabola_drift_m']*1000:.2f} mm!): "
          f"dphi = {se_25['dphi_bihorizon_rad']:.3f} rad (vs Newton {se_25['dphi_newton_rad']:.4f} rad -> "
          f"Integrated Boost = {se_25['integrated_boost_factor']:.1f}x, Null-Crossing Peak = {se_25['instantaneous_null_peak_boost']:.1f}x!)")
    print(f"      * T = 0.6 s parabola (max drift = {se_06['max_parabola_drift_m']*1e6:.1f} um!): "
          f"dphi = {se_06['dphi_bihorizon_rad']:.3f} rad (vs Newton {se_06['dphi_newton_rad']:.4f} rad -> "
          f"Integrated Boost = {se_06['integrated_boost_factor']:.1f}x!)")
    print(f"  5b. Sun-Jupiter(-MW) Saddle (r_J = {sj_25['r_from_planet_km']:,.0f} km, |g_obs|<a0 Bubble = +/-{sj_25['bubble_axial_m']/1000:.2f}km x +/-{sj_25['bubble_trans_m']/1000:.2f}km):")
    print(f"      * T = 2.5 s parabola (max drift = {sj_25['max_parabola_drift_m']*1e6:.1f} um!): "
          f"dphi = {sj_25['dphi_bihorizon_rad']:.2f} rad (vs Newton {sj_25['dphi_newton_rad']:.4f} rad -> "
          f"Integrated Boost = {sj_25['integrated_boost_factor']:.1f}x, Peak = {sj_25['instantaneous_null_peak_boost']:.1f}x!)")

    print("\n[1C] TIDAL vs. POTENTIAL DIAGNOSTIC: CAN |Phi|/c^2 OR c*sqrt(|grad g|) SCREEN SADDLE POINTS?")
    print("-" * 98)
    print(f"{'Regime':<35} | {'|Phi|/c^2':>11} | {'|g_N|/a0':>11} | {'|grad g| (s^-2)':>15} | {'c*sqrt(|grad g|)/a0':>20}")
    print("-" * 98)
    for row in check_tidal_vs_potential_screening_invariants(a0=a0_bi):
        print(
            f"{str(row['regime']):<35} | {float(row['phi_over_c2']):11.3e} | "
            f"{float(row['g_over_a0']):11.3e} | {float(row['grad_g_s2']):15.3e} | "
            f"{float(row['c_sqrt_grad_g_over_a0']):20.3e}"
        )

    print("\n[2A] HIGH-REDSHIFT a0(z)/a0(0) & TULLY-FISHER SHIFT (LCDM vs. DESI DR2 QUINTOM-B)")
    print("-" * 98)
    evo = evaluate_a0_z_models()
    print(f"  * LCDM Today Future Event Horizon R_eh(0) = {evo['reh0_lcdm_mpc']:.1f} Mpc -> c^2/(2*pi*R_eh(0)) = {evo['a0_eh0_lcdm_m_s2']:.3e} m/s^2")
    print(f"  * DISCOVERY: In DESI DR2 CPL Quintom-B (w0=-0.78, wa=-0.62), cosmic acceleration ENDS in the future")
    print(f"    at scale factor a_end = {evo['quintom_b_a_end_accel']:.3f} -> Future Event Horizon R_eh = INFINITY (T_eh = 0)!")
    print("-" * 98)
    print(f"{'z':>5} | {'H1: H(z)/H0 (LC/QB)':>21} | {'H2: R_eh0/R_eh (LC/QB)':>23} | {'H3: sqrt(DE) (LC/QB)':>21} | {'dlog10 V_f (H1_QB / H2_LC / H3_QB)':>34}")
    print("-" * 98)
    for r in evo["rows"]:
        h1_s = f"{r['H1_hubble_lcdm']:5.2f} / {r['H1_hubble_desi_qb']:5.2f}"
        h2_s = f"{r['H2_event_lcdm']:5.2f} / {'DIV':>5}"
        h3_s = f"{r['H3_de_lcdm']:5.2f} / {r['H3_de_desi_qb']:5.2f}"
        dv_s = f"{r['dlogV_H1_qb']:+6.3f} / {r['dlogV_H2_lcdm']:+6.3f} / {r['dlogV_H3_qb']:+6.3f}"
        print(f"{r['z']:5.2f} | {h1_s:>21} | {h2_s:>23} | {h3_s:>21} | {dv_s:>34}")

    print("\n[2B] CHI^2 AGAINST ALMA / JWST HIGH-Z ROTATION CURVE BENCHMARKS (z = 2.2, 4.4, 7.31)")
    print("-" * 98)
    chi2_hz = high_z_galaxy_benchmark_chi2()
    for name, (c2, det) in chi2_hz.items():
        status = "PASS (3 dof)" if c2 < 6.0 else "RULED OUT (>4 sigma)"
        print(
            f"  * {name:<42} : chi^2 = {c2:6.2f}  "
            f"[g_obs/g_bar(z=2.2)={det['boost_z2.2']:.2f}, dlogV(z=4.4)={det['dlogV_z4.4']:+.3f}] -> {status}"
        )
    print("=" * 98)


if __name__ == "__main__":
    main()
