"""
Empirical Crucible Benchmark Suite for Foundational Physics Discovery Collective.
Provides quantitative reference functions and observational constraints against which
candidate theoretical models in c:\\Projects\\Discovery can be numerically tested.
"""

import math
import numpy as np

# Fundamental SI constants
C_LIGHT = 2.99792458e8          # m / s
HBAR = 1.054571817e-34          # J * s
G_NEWTON = 6.67430e-11          # m^3 / (kg * s^2)
K_BOLTZ = 1.380649e-23          # J / K
MPC_TO_M = 3.085677581491367e22 # m / Mpc

# Cosmological & Galactic Reference Scales
H0_KM_S_MPC = 68.0                              # km / s / Mpc (intermediate reference)
H0_SI = (H0_KM_S_MPC * 1000.0) / MPC_TO_M       # s^-1 (~2.2037e-18 s^-1)
A0_SPARC = 1.20e-10                             # m / s^2 (McGaugh+ 2016 SPARC RAR scale)
C_H0 = C_LIGHT * H0_SI                          # ~6.607e-10 m / s^2
C_H0_OVER_2PI = C_H0 / (2.0 * math.pi)          # ~1.051e-10 m / s^2 (striking proximity to A0_SPARC!)


def sparc_rar_empirical(g_bar: np.ndarray, a0: float = A0_SPARC) -> np.ndarray:
    """
    McGaugh, Lelli & Schombert (2016) empirical Radial Acceleration Relation (RAR)
    fit to 153 SPARC galaxies (2693 data points), intrinsic scatter ~ 0.08-0.13 dex:
        g_obs = g_bar / (1 - exp(-sqrt(g_bar / a0)))
    """
    g_bar = np.asarray(g_bar, dtype=float)
    x = np.sqrt(np.maximum(g_bar / a0, 1e-30))
    return g_bar / (1.0 - np.exp(-x))


def rar_log_rms_dex(g_obs_model: np.ndarray, g_bar: np.ndarray, a0: float = A0_SPARC) -> float:
    """
    Returns RMS residual in dex between a candidate model's predicted g_obs(g_bar)
    and the empirical SPARC RAR curve across a grid of accelerations.
    Target: < 0.10 dex across 1e-12 to 1e-8 m/s^2.
    """
    g_ref = sparc_rar_empirical(g_bar, a0=a0)
    resid = np.log10(np.maximum(g_obs_model, 1e-30)) - np.log10(g_ref)
    return float(np.sqrt(np.mean(resid ** 2)))


def solar_system_ppn_anomaly(g_obs_func, r_au: float = 10.0) -> float:
    """
    Evaluates fractional anomalous acceleration |g_obs - g_N| / g_N at Saturn/Cassini orbit (~10 AU).
    Solar mass M_sun = 1.98847e30 kg.
    Cassini + planetary ephemerides require |delta g / g_N| < ~1e-8 at 10 AU.
    (Note: Naive unscreened exp(-sqrt(g/a0)) has tiny correction exp(-sqrt(g_N/a0)), whereas
    power-law interpolating functions like 1/(1 + a0/g) fail planetary ephemerides unless screened!)
    """
    m_sun = 1.98847e30
    r_m = r_au * 1.495978707e11
    g_n = G_NEWTON * m_sun / (r_m ** 2)
    g_val = float(np.squeeze(g_obs_func(np.array([g_n]))))
    return abs(g_val - g_n) / g_n


def hubble_cpl(z: np.ndarray, omega_m: float = 0.31, w0: float = -0.78, wa: float = -0.62, h0: float = 68.0) -> np.ndarray:
    """
    Hubble expansion H(z) in km/s/Mpc for flat CPL dynamical dark energy
    (representative of DESI DR2 + CMB + SNe Ia 2025-2026 preference: w0 ~ -0.78, wa ~ -0.62,
    compared to LCDM w0 = -1.0, wa = 0.0).
    """
    z = np.asarray(z, dtype=float)
    zp1 = 1.0 + z
    de_factor = (zp1 ** (3.0 * (1.0 + w0 + wa))) * np.exp(-3.0 * wa * z / zp1)
    e2 = omega_m * (zp1 ** 3) + (1.0 - omega_m) * de_factor
    return h0 * np.sqrt(e2)


def double_slit_complementarity_check(visibility: np.ndarray, distinguishability: np.ndarray) -> dict:
    """
    Checks Englert-Greenberger-Yasin duality bound V^2 + D^2 <= 1 + tol.
    """
    v2_d2 = np.asarray(visibility) ** 2 + np.asarray(distinguishability) ** 2
    max_val = float(np.max(v2_d2))
    return {
        "max_V2_plus_D2": max_val,
        "respects_duality_bound": max_val <= 1.0 + 1e-9,
    }


def bmv_entanglement_phase(mass_kg: float, delta_x_m: float, separation_d_m: float, time_s: float) -> float:
    """
    Standard Bose-Marletto-Vedral (BMV) gravitational entanglement differential phase:
        Delta phi = (G * m^2 * t / hbar) * (1/(d - dx) + 1/(d + dx) - 2/d)
    When Delta phi ~ O(1) rad and decoherence rate Gamma * t < 1, two superposed masses
    become measurably entangled if gravity coherently couples branch-by-branch.
    """
    inv_diff = (1.0 / (separation_d_m - delta_x_m)) + (1.0 / (separation_d_m + delta_x_m)) - (2.0 / separation_d_m)
    return (G_NEWTON * (mass_kg ** 2) * time_s / HBAR) * inv_diff


if __name__ == "__main__":
    print("=== Empirical Crucible Self-Check ===")
    print(f"c * H0 / (2*pi) = {C_H0_OVER_2PI:.3e} m/s^2 vs SPARC a0 = {A0_SPARC:.3e} m/s^2 (ratio = {C_H0_OVER_2PI/A0_SPARC:.3f})")
    g_grid = np.logspace(-12, -8, 100)
    print(f"SPARC RAR self-consistency RMS: {rar_log_rms_dex(sparc_rar_empirical(g_grid), g_grid):.4f} dex")
    print(f"Saturn (10 AU) fractional anomaly for exp-screened RAR: {solar_system_ppn_anomaly(sparc_rar_empirical, 10.0):.3e}")
    print(f"BMV phase (m=1e-14 kg, dx=100 um, d=250 um, t=2.5 s): {bmv_entanglement_phase(1e-14, 1e-4, 2.5e-4, 2.5):.3f} rad")
