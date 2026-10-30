"""
PI Probe: Complex-Time Horizon Thermodynamics & the Bose-Einstein Stimulated Gravity Identity.
Testing the exact mathematical identity hiding inside the empirical SPARC Radial Acceleration Relation:
    g_obs / g_bar = 1 / (1 - exp(-sqrt(g_bar / a0))) == 1 + 1 / (exp(sqrt(g_bar / a0)) - 1)
which is literally (1 + n_BE(x)) — vacuum spontaneous response (Newtonian gravity = 1)
plus stimulated Bose-Einstein horizon mode occupation n_BE(x) with dimensionless chemical/Unruh
exponent x = sqrt(g_bar / a0)!
"""

import math
import numpy as np
import sympy as sp
from empirical_crucible import (
    A0_SPARC,
    C_H0,
    C_H0_OVER_2PI,
    C_LIGHT,
    H0_SI,
    rar_log_rms_dex,
    solar_system_ppn_anomaly,
    sparc_rar_empirical,
)

# 1. Symbolic check of the Bose-Einstein identity and asymptotic expansions
x = sp.Symbol("x", positive=True)
f_rar = 1 / (1 - sp.exp(-x))
f_bose = 1 + 1 / (sp.exp(x) - 1)
diff_ident = sp.simplify(f_rar - f_bose)

series_low_g = sp.series(f_rar, x, 0, 4)

print("=== 1. Symbolic Identity Check ===")
print(f"(1 / (1 - e^-x)) - (1 + 1 / (e^x - 1)) = {diff_ident}")
print(f"Deep low-acceleration expansion (x = sqrt(g_bar/a0) -> 0): g_obs/g_bar = {series_low_g}")
print("Notice the terms:")
print("  1/x       -> sqrt(a0 / g_bar) => g_obs = sqrt(g_bar * a0) [Exact MOND / Flat Rotation Curve!]")
print("  + 1/2     -> Zero-point 1/2 * g_bar shift!")
print("  + x / 12  -> First Bernoulli thermal curvature correction!")

# 2. Why x = sqrt(g_bar / a0)? Geometric mean of local Unruh temperature and cosmic de Sitter temperature!
# Wait: Look at the two temperatures in a static patch of de Sitter-Schwarzschild space:
#   T_Unruh(baryon) = hbar * g_bar / (2 * pi * k_B * c)
#   T_dS(horizon)   = hbar * H     / (2 * pi * k_B)  => characteristic acceleration a_dS = c * H / (2 * pi)
# Suppose a gravitational dipole/quadrupole mode coupling a localized baryon at r to the cosmic horizon R_H = c/H
# has excitation energy E_mode proportional to sqrt(E_local * E_horizon) -> x = sqrt(T_Unruh_bar / T_eff)!
# Let's check what T_eff (or geometric factor on c*H0) gives exact SPARC a0:
for name, factor in [
    ("c * H0 / (2 * pi)", C_H0 / (2.0 * math.pi)),
    ("c * H0 / 6", C_H0 / 6.0),
    ("c * H0 * sqrt(Omega_Lambda) / (2 * pi)", C_H0 * math.sqrt(0.69) / (2.0 * math.pi)),
    ("c * H0 * sqrt(Omega_Lambda / 3)", C_H0 * math.sqrt(0.69 / 3.0)),
]:
    g_grid = np.logspace(-12, -8, 200)
    g_pred = sparc_rar_empirical(g_grid, a0=factor)
    rms = rar_log_rms_dex(g_pred, g_grid, a0=A0_SPARC)
    saturn_anom = solar_system_ppn_anomaly(lambda g: sparc_rar_empirical(g, a0=factor), r_au=10.0)
    print(f"\nScale ansatz: {name:38s} = {factor:.3e} m/s^2")
    print(f"  Ratio to SPARC a0 (1.20e-10): {factor / A0_SPARC:.4f}")
    print(f"  Zero-free-parameter RAR RMS vs SPARC fit: {rms:.4f} dex (SPARC intrinsic scatter ~ 0.08-0.13 dex!)")
    print(f"  Saturn 10 AU fractional anomaly |dg/g_N|: {saturn_anom:.3e}")
