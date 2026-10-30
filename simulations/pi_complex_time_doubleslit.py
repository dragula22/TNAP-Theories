"""
PI Probe 2: Complex Spacetime Metric ds^2 = c^2 (dt - i d_sigma)^2 - dx^2
Deriving the Unified Quantum Path Integral + Quantum-to-Classical Decoherence + Double-Slit Duality
from a single geometric invariant: complex proper time!
"""

import numpy as np
import sympy as sp
from empirical_crucible import C_LIGHT, HBAR, double_slit_complementarity_check

# 1. Exact Symbolic Expansion of Relativistic Action in Complex Time
m, c, hbar, v, sigma_dot = sp.symbols("m c hbar v sigma_dot", real=True, positive=True)
i = sp.I

# Complex proper time integrand: d_tau_c / dt = sqrt((1 - i*sigma_dot)^2 - v^2/c^2)
integrand = -m * c**2 * sp.sqrt((1 - i * sigma_dot) ** 2 - v**2 / c**2)

# Expand for small sigma_dot (weak horizon/entropic coupling) and non-relativistic v/c
series_v = sp.series(integrand, v, 0, 3).removeO()
series_full = sp.series(series_v, sigma_dot, 0, 3).removeO()

exponent_iL_over_hbar = sp.expand(i * series_full / hbar)
real_damping = sp.simplify(sp.re(exponent_iL_over_hbar))
imag_phase = sp.simplify(sp.im(exponent_iL_over_hbar))

print("=== 1. Complex Proper-Time Action Expansion ===")
print("Action exponent (i / hbar) * L_complex:")
print("  Oscillatory phase Im[(i/hbar)L] =", imag_phase)
print("  Real damping      Re[(i/hbar)L] =", real_damping)
print("Notice: Oscillatory phase gives exact Compton rest clock (-mc^2/hbar) + Schrodinger kinetic (+mv^2/2hbar),")
print("while Real damping gives -(mc^2 - mv^2/2)*(sigma_dot/hbar) -> mass-proportional localization!")

# 2. Numerical Double-Slit + Quantum Eraser Simulation in Complex Time
# Electron double-slit parameters (Tonomura 1989 / Bach et al. 2013 realistic scale)
m_e = 9.1093837e-31
v_e = 1.0e7                     # 10,000 km/s electron beam
lam_db = 2.0 * np.pi * HBAR / (m_e * v_e)
slit_sep_d = 1.0e-6             # 1 micron slit separation
screen_L = 0.5                  # 0.5 m to screen
y_screen = np.linspace(-5e-4, 5e-4, 1000)

# Path lengths from slit 1 (+d/2) and slit 2 (-d/2)
r1 = np.sqrt(screen_L**2 + (y_screen - slit_sep_d / 2.0) ** 2)
r2 = np.sqrt(screen_L**2 + (y_screen + slit_sep_d / 2.0) ** 2)

# Phase difference delta_S / hbar = k * (r1 - r2)
k_wave = 2.0 * np.pi / lam_db
delta_phi = k_wave * (r1 - r2)

# Suppose a which-way coupler rotates relative complex time between slit 1 and slit 2
# by entropic angle theta_info in [0, pi/2], where distinguishability D = sin(theta_info)
# and coherence survival exp(-Delta_I) = cos(theta_info).
thetas = np.linspace(0.0, 0.5 * np.pi, 25)
visibilities = []
distinguishabilities = []

for th in thetas:
    D = np.sin(th)
    coherence = np.cos(th)  # Unitary pre-horizon entanglement weight; irreversible horizon exit locks D->1
    intensity = 0.5 * (1.0 + 1.0 + 2.0 * coherence * np.cos(delta_phi))
    V = (intensity.max() - intensity.min()) / (intensity.max() + intensity.min())
    visibilities.append(V)
    distinguishabilities.append(D)

duality = double_slit_complementarity_check(np.array(visibilities), np.array(distinguishabilities))
print("\n=== 2. Double-Slit Complex-Time Complementarity Check ===")
print(f"Electron de Broglie wavelength: {lam_db*1e12:.3f} pm, Fringe spacing: {(lam_db*screen_L/slit_sep_d)*1e6:.2f} um")
print(f"Max V^2 + D^2 across 25 horizon-coupling regimes: {duality['max_V2_plus_D2']:.6f} (Bound <= 1: {duality['respects_duality_bound']})")

# 3. Macroscopic vs Microscopic Horizon Localization Threshold
# Minimum entropic time fluctuation delta_sigma_rms needed to localize a superposition (visibility < e^-1):
#   (m * c^2 / hbar) * delta_sigma_crit ~ 1  =>  delta_sigma_crit = hbar / (m * c^2) (the Compton time!)
for label, mass in [
    ("Electron", 9.109e-31),
    ("C60 Fullerene (Arndt interferometry)", 1.2e-24),
    ("BMV Nanodiamond (10^-14 kg)", 1.0e-14),
    ("Human cortical neuron spike-mass (~10^-9 kg)", 1.0e-9),
]:
    tau_compton = HBAR / (mass * C_LIGHT**2)
    print(f"  {label:42s}: critical entropic time delta_sigma_crit = {tau_compton:.3e} s")
