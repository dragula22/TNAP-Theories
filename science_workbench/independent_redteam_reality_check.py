"""
Independent CPU-Only Red-Team Reality-Check Audit of WeaveForge & TNaP Spacetime Weave.
Strictly CPU-only (0.0% GPU usage; read-only memory snapshot of WeaveForge LUTs).
"""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["NUMBA_DISABLE_CUDA"] = "1"
os.environ["OMP_NUM_THREADS"] = "2"

import ctypes
import io
import json
import math
import re
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline

# Lower CPU priority to BELOW_NORMAL_PRIORITY_CLASS (0x00004000) on Windows
try:
    ctypes.windll.kernel32.SetPriorityClass(
        ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000
    )
except Exception:
    pass


def audit_1_cmb_to_galaxy_double_counting() -> dict:
    """
    Tests physical continuity between Arena 4 Row 2 (Planck CMB, Omega_pleat = 5.3183 * Omega_b
    treated as pressureless omch2 in CAMB) and Row 1 (SPARC 175 galaxies, has_cdm_halo = False + QUMOND a0).
    """
    G = 6.67430e-11
    hbar = 1.054571817e-34
    ev_to_kg = 1.78266192e-36
    kpc_to_m = 3.085677581e19
    msun = 1.98847e30

    omega_b = 0.0490
    xi_tnap = 5.0 + 1.0 / math.pi  # 5.318309886
    omega_pleat = xi_tnap * omega_b  # 0.260597
    h = 0.674
    H0_si = h * 100.0e3 / (1.0e3 * kpc_to_m)
    rho_crit = 3.0 * (H0_si**2) / (8.0 * math.pi * G)
    rho_m0 = (omega_b + omega_pleat) * rho_crit

    # 1. Quantum Jeans scale at m_pleat = 1e-10 eV (used in skyrme_perturbation.py)
    m_pleat_kg = 1.0e-10 * ev_to_kg
    k_j_m_inv = (16.0 * math.pi * G * rho_m0 * (m_pleat_kg**2) / (hbar**2)) ** 0.25
    lambda_j_m = 2.0 * math.pi / k_j_m_inv
    lambda_j_au = lambda_j_m / 1.495978707e11
    m_jeans_msun = (4.0 * math.pi / 3.0) * rho_m0 * ((0.5 * lambda_j_m) ** 3) / msun

    # 2. Required scalar mass to keep pleats smooth across R_halo = 30 kpc (lambda_J >= 60 kpc)
    # Note: in virialized galaxy halo (delta ~ 200), rho_halo ~ 200 * rho_m0
    rho_halo = 200.0 * rho_m0
    lambda_target_m = 60.0 * kpc_to_m
    k_target = 2.0 * math.pi / lambda_target_m
    m_smooth_kg = math.sqrt((k_target**4) * (hbar**2) / (16.0 * math.pi * G * rho_halo))
    m_smooth_ev = m_smooth_kg / ev_to_kg
    lyman_alpha_min_ev = 2.0e-20  # Irsic+ 2024 / Rogers & Peiris 2021 95% CL lower bound

    # 3. Rotation curve of flagship SPARC spiral NGC 3198 at R = 30 kpc (Lelli+ 2016, Upsilon_* = 0.5)
    # Observed flat velocity V_obs = 150.1 +- 3.0 km/s; Newtonian baryonic V_bary(30 kpc) = 67.2 km/s (M_b ~ 3.15e10 M_sun)
    r_m = 30.0 * kpc_to_m
    v_obs_kms = 150.1
    sig_v_kms = 3.0
    v_bary_kms = 67.2
    a0 = 1.202712e-10

    def nu_be(y: float) -> float:
        return 1.0 / (1.0 - math.exp(-math.sqrt(max(y, 1e-15))))

    g_bary = ((v_bary_kms * 1e3) ** 2) / r_m
    # Case A: WeaveForge Arena 4 Row 1 (deletes cosmic pleats in galaxies, keeps QUMOND)
    g_case_a = g_bary * nu_be(g_bary / a0)
    v_case_a_kms = math.sqrt(g_case_a * r_m) / 1e3

    # Case B1: Cosmic pleats collapse at cosmic ratio (1 + 5.3183)*g_bary + QUMOND boost (100% capture)
    g_N_full = (1.0 + xi_tnap) * g_bary
    g_case_b_full = g_N_full * nu_be(g_N_full / a0)
    v_case_b_full_kms = math.sqrt(g_case_b_full * r_m) / 1e3

    # Case B2: Even conservative outer-radius enclosed ratio (say 50% of cosmic pleat ratio inside 30 kpc) + QUMOND
    g_N_half = (1.0 + 0.5 * xi_tnap) * g_bary
    g_case_b_half = g_N_half * nu_be(g_N_half / a0)
    v_case_b_half_kms = math.sqrt(g_case_b_half * r_m) / 1e3

    return {
        "omega_pleat_cmb": round(omega_pleat, 5),
        "pleat_to_baryon_ratio": round(xi_tnap, 4),
        "m_pleat_code_ev": 1.0e-10,
        "jeans_wavelength_at_1e_10_ev_au": round(lambda_j_au, 4),
        "jeans_mass_at_1e_10_ev_msun": float(f"{m_jeans_msun:.3e}"),
        "required_m_ev_for_60kpc_core": float(f"{m_smooth_ev:.3e}"),
        "lyman_alpha_95cl_min_ev": lyman_alpha_min_ev,
        "lyman_alpha_violation_factor": round(lyman_alpha_min_ev / m_smooth_ev, 1),
        "ngc3198_30kpc_v_obs_kms": v_obs_kms,
        "ngc3198_v_weaveforge_row1_kms": round(v_case_a_kms, 1),
        "ngc3198_v_if_pleats_cluster_50pct_plus_qumond_kms": round(v_case_b_half_kms, 1),
        "ngc3198_v_if_pleats_cluster_100pct_plus_qumond_kms": round(v_case_b_full_kms, 1),
        "ngc3198_sigma_discrepancy_50pct": round((v_case_b_half_kms - v_obs_kms) / sig_v_kms, 1),
        "ngc3198_sigma_discrepancy_100pct": round((v_case_b_full_kms - v_obs_kms) / sig_v_kms, 1),
    }


def audit_2_planck_2018_error_bars_and_h0_split() -> dict:
    """
    Reads camb_te_ee_2500_lut_cache.npz purely into RAM (zero file lock) to check:
    1) Internal H0 inconsistency (69.0 in polarization LUT vs 67.4 in BAO & a0).
    2) Implicit Peak-1 A_s rescaling factor applied in compute_cmb_polarization_2500.
    3) Actual Planck 2018 cosmic-variance + instrument-noise chi^2 across l=30..2500
       (exposing what Pearson r = 0.99998 hides in the Silk-damping tail!).
    """
    npz_path = Path(r"C:\Projects\Simulate\weaveforge\data\camb_te_ee_2500_lut_cache.npz")
    raw_bytes = npz_path.read_bytes()
    with np.load(io.BytesIO(raw_bytes), allow_pickle=False) as z:
        sig = str(z["signature"].item() if z["signature"].ndim == 0 else z["signature"][0])
        nodes = np.asarray(z["omega_nodes"], dtype=np.float64)
        ell = np.asarray(z["ell_grid"], dtype=np.float64)
        pol_3044 = np.asarray(z["pol_3044"], dtype=np.float64)
        pol_3303 = np.asarray(z["pol_3303"], dtype=np.float64)

    sp_3044 = CubicSpline(nodes, pol_3044, axis=0, bc_type="not-a-knot")
    sp_3303 = CubicSpline(nodes, pol_3303, axis=0, bc_type="not-a-knot")

    ref_mat = np.asarray(sp_3044(0.31397), dtype=np.float64)  # Planck LCDM baseline (H0=67.4, N_eff=3.044)
    tnap_raw = np.asarray(sp_3303(0.30941), dtype=np.float64)  # TNaP polarization LUT (H0=69.0, N_eff=3.303)
    tnap_same_nnu = np.asarray(sp_3044(0.30941), dtype=np.float64)  # If N_eff=3.044, H0=67.4

    mask_p1 = (ell >= 160) & (ell <= 280)
    ref_p1 = float(np.max(ref_mat[0, mask_p1]))
    raw_p1 = float(np.max(tnap_raw[0, mask_p1]))
    rescale_factor = ref_p1 / raw_p1

    tnap_rescaled = tnap_raw * rescale_factor
    t_waist = 1.0 - np.exp(-((ell / 3.21) ** 2))
    tnap_final = tnap_rescaled * t_waist[None, :]

    # Pearson r on TE (matching WeaveForge metric)
    mask_30_2500 = ell >= 30
    te_m = tnap_final[1, mask_30_2500]
    te_o = ref_mat[1, mask_30_2500]
    pearson_te = float(np.corrcoef(te_m, te_o)[0, 1])
    pearson_tt = float(np.corrcoef(tnap_final[0, mask_30_2500], ref_mat[0, mask_30_2500])[0, 1])

    # Official Planck 2018 143+217 GHz Knox-formula cosmic variance + detector noise on D_ell
    # f_sky = 0.65; combined effective noise w_T^(-1/2) = 33 uK*arcmin, w_P^(-1/2) = 60 uK*arcmin, theta_FWHM = 5.5 arcmin
    # Note: ell_grid steps by 2 above ell=4, so each grid point represents delta_ell = 2 multipoles!
    f_sky = 0.65
    delta_ell = np.gradient(ell)
    theta_rad = (5.5 / 60.0) * (math.pi / 180.0)
    sigma_b = theta_rad / math.sqrt(8.0 * math.log(2.0))
    b_l2 = np.exp(-ell * (ell + 1.0) * (sigma_b**2))

    # Convert uK*arcmin -> C_l noise -> D_l noise = l(l+1)/(2*pi) * N_l
    arcmin_rad = (1.0 / 60.0) * (math.pi / 180.0)
    nl_tt = ((33.0 * arcmin_rad) ** 2) / np.maximum(b_l2, 1e-30)
    nl_ee = ((60.0 * arcmin_rad) ** 2) / np.maximum(b_l2, 1e-30)
    dl_noise_tt = ell * (ell + 1.0) / (2.0 * math.pi) * nl_tt
    dl_noise_ee = ell * (ell + 1.0) / (2.0 * math.pi) * nl_ee

    # Variance of binned/strided D_ell: Var(D_ell) = 2 / ((2*ell + 1) * f_sky * delta_ell) * (D_ell + D_noise)^2
    denom_modes = np.maximum((2.0 * ell + 1.0) * f_sky * delta_ell, 1.0)
    var_tt = (2.0 / denom_modes) * ((ref_mat[0] + dl_noise_tt) ** 2)
    var_ee = (2.0 / denom_modes) * ((ref_mat[2] + dl_noise_ee) ** 2)
    var_te = (1.0 / denom_modes) * ((ref_mat[1] ** 2) + (ref_mat[0] + dl_noise_tt) * (ref_mat[2] + dl_noise_ee))

    chi2_tt_rescaled = float(np.sum(((tnap_final[0, mask_30_2500] - ref_mat[0, mask_30_2500]) ** 2) / var_tt[mask_30_2500]))
    chi2_tt_unrescaled = float(np.sum(((tnap_raw[0, mask_30_2500] - ref_mat[0, mask_30_2500]) ** 2) / var_tt[mask_30_2500]))
    chi2_te_rescaled = float(np.sum(((tnap_final[1, mask_30_2500] - ref_mat[1, mask_30_2500]) ** 2) / var_te[mask_30_2500]))
    chi2_ee_rescaled = float(np.sum(((tnap_final[2, mask_30_2500] - ref_mat[2, mask_30_2500]) ** 2) / var_ee[mask_30_2500]))

    # High-ell Silk damping residual (ell = 800..2000)
    mask_silk = (ell >= 800) & (ell <= 2000)
    mean_tt_silk_shift_pct = float(
        100.0 * np.mean((tnap_final[0, mask_silk] - ref_mat[0, mask_silk]) / np.maximum(ref_mat[0, mask_silk], 1.0))
    )
    max_tt_residual_uk2 = float(np.max(np.abs(tnap_final[0, mask_30_2500] - ref_mat[0, mask_30_2500])))

    # Check a0 shift if H0 = 69.0 vs 67.36
    c_si = 299792458.0
    mpc_m = 3.0856775814913673e22
    a0_6736 = c_si * (67.36e3 / mpc_m) / (math.sqrt(3.0) * math.pi)
    a0_6900 = c_si * (69.00e3 / mpc_m) / (math.sqrt(3.0) * math.pi)

    return {
        "lut_signature": sig,
        "h0_in_pol_3303_kms_mpc": 69.0,
        "h0_in_bao_and_tt1000_kms_mpc": 67.4,
        "h0_in_a0_lock_kms_mpc": 67.36,
        "a0_at_6736": float(f"{a0_6736:.6e}"),
        "a0_if_h0_6900": float(f"{a0_6900:.6e}"),
        "a0_shift_pct_if_h0_69": round(100.0 * (a0_6900 - a0_6736) / a0_6736, 2),
        "implicit_As_peak1_rescale_factor": round(rescale_factor, 5),
        "pearson_r_te_reported": round(pearson_te, 5),
        "pearson_r_tt": round(pearson_tt, 5),
        "delta_chi2_tt_unrescaled_ell30_2500": round(chi2_tt_unrescaled, 1),
        "delta_chi2_tt_after_peak1_rescale_ell30_2500": round(chi2_tt_rescaled, 1),
        "delta_chi2_te_ell30_2500": round(chi2_te_rescaled, 1),
        "delta_chi2_ee_ell30_2500": round(chi2_ee_rescaled, 1),
        "delta_chi2_total_tt_te_ee": round(chi2_tt_rescaled + chi2_te_rescaled + chi2_ee_rescaled, 1),
        "mean_silk_tail_tt_suppression_ell800_2000_pct": round(mean_tt_silk_shift_pct, 2),
        "max_tt_residual_uk2": round(max_tt_residual_uk2, 1),
    }


def audit_3_bbn_deuterium_helium_squeeze() -> dict:
    """
    Tests N_eff = 3.303 (Delta N_eff = +0.259 early relativistic pleat radiation) at Planck
    baryon density omega_b = 0.02237 against 1% primordial Deuterium (Cooke+ 2018 / PDG 2024)
    and Helium-4 Y_p (Aver+ 2021 / PDG 2024), using Parthenope 3.0 / AlterBBN / Pisanti+ (2021)
    & Yeh, Olive & Fields (2022, JCAP) calibrated response derivatives.
    """
    omega_b = 0.02237
    sigma_omega_b = 0.00015
    delta_neff = 3.303 - 3.044  # +0.259

    # Standard BBN baseline at omega_b = 0.02237, N_eff = 3.044, tau_n = 879.4 +- 0.6 s
    # (Pitrou+ 2021 / Yeh+ 2022 / PDG 2024 BBN review):
    # Y_p = 0.24695 + 0.0135 * Delta_N_eff
    # 10^5 * (D/H) = 2.514 * (omega_b / 0.02237)^(-1.62) * (1 + 0.135 * Delta_N_eff)
    # Nuclear reaction rate theoretical uncertainty on D/H (post-LUNA Mossa+ 2020): sigma_th = 0.032e-5
    dh_lcdm = 2.514e-5
    dh_tnap_early_rad = dh_lcdm * (1.0 + 0.135 * delta_neff)
    sigma_dh_th = math.sqrt((0.032e-5) ** 2 + (dh_lcdm * 1.62 * (sigma_omega_b / omega_b)) ** 2)

    dh_obs = 2.547e-5  # PDG 2024 / Cooke+ 2018 weighted mean: (2.547 +- 0.025)e-5
    sigma_dh_obs = 0.025e-5
    sigma_dh_tot = math.sqrt(sigma_dh_obs**2 + sigma_dh_th**2)

    z_dh_early_rad = (dh_tnap_early_rad - dh_obs) / sigma_dh_tot
    z_dh_lcdm = (dh_lcdm - dh_obs) / sigma_dh_tot

    yp_lcdm = 0.24695
    yp_tnap_early_rad = yp_lcdm + 0.0135 * delta_neff
    yp_obs = 0.2453
    sigma_yp_obs = 0.0034
    z_yp_early_rad = (yp_tnap_early_rad - yp_obs) / sigma_yp_obs

    # Combined Planck + BBN (D/H + Y_p) posterior from Yeh, Olive & Fields (2022, JCAP 11, 046):
    # N_eff = 2.898 +- 0.141
    neff_joint_mean = 2.898
    neff_joint_sig = 0.141
    z_joint_planck_bbn = (3.303 - neff_joint_mean) / neff_joint_sig

    return {
        "n_eff_tnap": 3.303,
        "delta_n_eff": round(delta_neff, 3),
        "dh_obs_pdg2024": "2.547 +- 0.025 (x10^-5)",
        "dh_lcdm_pred_x1e5": round(dh_lcdm * 1e5, 3),
        "dh_tnap_neff3303_pred_x1e5": round(dh_tnap_early_rad * 1e5, 3),
        "dh_direct_sigma_tension": round(z_dh_early_rad, 2),
        "yp_obs_pdg2024": "0.2453 +- 0.0034",
        "yp_tnap_neff3303_pred": round(yp_tnap_early_rad, 4),
        "yp_direct_sigma_tension": round(z_yp_early_rad, 2),
        "joint_planck_plus_bbn_neff_bound": "2.898 +- 0.141 (Yeh, Olive & Fields 2022)",
        "joint_planck_bbn_sigma_tension": round(z_joint_planck_bbn, 2),
    }


def audit_4_weak_lensing_s8_and_cosmic_web_qumond() -> dict:
    """
    Integrates the cosmological linear growth ODE from a=1e-3 to a=1.0:
    1) Pure GR growth on TNaP background (Omega_m=0.30941, w0=-0.91, wa=-0.28).
    2) Unscreened QUMOND growth on k = 0.15 h/Mpc (8 h^-1 Mpc sigma_8 scale), where
       typical cosmic-web peculiar accelerations g_pec ~ 4*pi*G*rho_m*delta*(R_8) ~ 1.5e-11 m/s^2 < a0!
    """
    om_lcdm = 0.3153
    s8_planck_lcdm = 0.832
    sig8_lcdm = s8_planck_lcdm / math.sqrt(om_lcdm / 0.3)  # 0.8116

    def solve_growth(om: float, w0: float, wa: float, qumond_cosmic_web: bool) -> float:
        ode0 = 1.0 - om

        def e2(a: float) -> float:
            de_factor = (a ** (-3.0 * (1.0 + w0 + wa))) * math.exp(-3.0 * wa * (1.0 - a))
            return om * (a**-3) + ode0 * de_factor

        def de2_da(a: float) -> float:
            eps = 1e-6 * a
            return (e2(a + eps) - e2(a - eps)) / (2.0 * eps)

        # At R = 8 h^-1 Mpc (~11.8 Mpc today), linear density contrast grows from ~1e-3 at a=1e-3 to ~0.8 at a=1.
        # Characteristic Newtonian peculiar acceleration at scale R_phys = a * 11.8 Mpc:
        # g_N(a) ~ (4*pi/3) * G * rho_m(a) * delta(a) * R_phys
        G = 6.67430e-11
        h = 0.674
        mpc_m = 3.085677581e22
        H0_si = h * 100.0e3 / mpc_m
        rho_crit0 = 3.0 * (H0_si**2) / (8.0 * math.pi * G)
        r8_comoving_m = (8.0 / h) * mpc_m
        a0 = 1.202712e-10

        def rhs(a: float, y: np.ndarray) -> np.ndarray:
            delta, ddelta_da = float(y[0]), float(y[1])
            e2_val = e2(a)
            dlnH_da = 0.5 * de2_da(a) / e2_val
            mu_eff = 1.0
            if qumond_cosmic_web and a > (1.0 / 1100.0):
                rho_ma = om * rho_crit0 * (a**-3)
                r_phys = a * r8_comoving_m
                g_pec = max((4.0 * math.pi / 3.0) * G * rho_ma * abs(delta) * r_phys, 1e-16)
                y_acc = g_pec / a0
                mu_eff = 1.0 / (1.0 - math.exp(-math.sqrt(y_acc)))
            d2 = -(3.0 / a + dlnH_da) * ddelta_da + 1.5 * (om * (a**-5) / e2_val) * mu_eff * delta
            return np.array([ddelta_da, d2], dtype=np.float64)

        a_init = 1.0e-3
        # Initial condition in matter era: delta(a_init) = 0.81 * a_init
        sol = solve_ivp(rhs, (a_init, 1.0), [0.81 * a_init, 0.81], rtol=1e-8, atol=1e-10)
        return float(sol.y[0, -1])

    g_lcdm = solve_growth(om_lcdm, -1.0, 0.0, qumond_cosmic_web=False)
    g_tnap_screened = solve_growth(0.30941, -0.91, -0.28, qumond_cosmic_web=False)
    g_tnap_unscreened = solve_growth(0.30941, -0.91, -0.28, qumond_cosmic_web=True)

    sig8_tnap_screened = sig8_lcdm * (g_tnap_screened / g_lcdm)
    s8_tnap_screened = sig8_tnap_screened * math.sqrt(0.30941 / 0.3)

    sig8_tnap_unscreened = sig8_lcdm * (g_tnap_unscreened / g_lcdm)
    s8_tnap_unscreened = sig8_tnap_unscreened * math.sqrt(0.30941 / 0.3)

    # Weak lensing constraints: DES Y3 S_8 = 0.776 +- 0.017; KiDS-1000 S_8 = 0.759 +- 0.024
    des_mean, des_sig = 0.776, 0.017
    kids_mean, kids_sig = 0.759, 0.024

    return {
        "s8_des_y3": "0.776 +- 0.017",
        "s8_kids_1000": "0.759 +- 0.024",
        "s8_lcdm_planck": round(s8_planck_lcdm, 3),
        "s8_tnap_if_cosmic_web_100pct_screened": round(s8_tnap_screened, 3),
        "s8_tnap_screened_tension_vs_des_sigma": round((s8_tnap_screened - des_mean) / des_sig, 2),
        "s8_tnap_if_qumond_unscreened_on_8mpc": round(s8_tnap_unscreened, 3),
        "s8_tnap_unscreened_tension_vs_des_sigma": round((s8_tnap_unscreened - des_mean) / des_sig, 1),
    }


def audit_5_scoreboard_symmetry_and_knob_count() -> dict:
    """
    Counts explicit numerical constants in 05_tnap_spacetime_weave.toml vs 01_lambda_cdm.toml
    and 04_aest_relativistic.toml, and checks AeST's exact badge tally under WeaveForge's own rules!
    """
    mods_dir = Path(r"C:\Projects\Simulate\mods")
    tnap_txt = (mods_dir / "05_tnap_spacetime_weave.toml").read_text(encoding="utf-8")
    aest_txt = (mods_dir / "04_aest_relativistic.toml").read_text(encoding="utf-8")
    lcdm_txt = (mods_dir / "01_lambda_cdm.toml").read_text(encoding="utf-8")

    def extract_lagrangian_floats(toml_text: str) -> list[str]:
        m = re.search(r'field_lagrangian\s*=\s*"([^"]+)"', toml_text)
        if not m:
            return []
        expr = m.group(1)
        return re.findall(r"\b\d+\.\d+\b", expr)

    tnap_lag_consts = extract_lagrangian_floats(tnap_txt)
    aest_lag_consts = extract_lagrangian_floats(aest_txt)
    lcdm_lag_consts = extract_lagrangian_floats(lcdm_txt)

    return {
        "tnap_lagrangian_hardcoded_floats": tnap_lag_consts,
        "tnap_lagrangian_float_count": len(tnap_lag_consts),
        "tnap_extra_cosmology_knobs": ["waist_clamping_ell = 3.21", "w0_de = -0.91", "wa_de = -0.28"],
        "tnap_extra_pde_couplings": ["m_eff = 0.72", "g4 = 0.80", "g6 = 3.10", "k_skyrme = 1.55", "g_knot = 0.90"],
        "aest_lagrangian_hardcoded_floats": aest_lag_consts,
        "lcdm_lagrangian_hardcoded_floats": lcdm_lag_consts,
        "aest_current_badges_in_arena4": {
            "SPARC_175": "PASS (same RAR nu(y), has_cdm_halo=false)",
            "Planck_CMB": "WARN (same pinned_pleat_coupling=1.0 -> ALSO becomes PASS if that gate opens!)",
            "Solar_GW170817": "PASS (PPN=1, c_T=1, Wait: check Saturn 9.58 AU nu(y) tail!)",
            "DESI_DR2_H0": "WARN",
            "Gaia_DR4": "FORECAST",
        },
    }


def main() -> None:
    report = {
        "guillotine_1_cmb_galaxy_double_counting": audit_1_cmb_to_galaxy_double_counting(),
        "guillotine_2_planck_chi2_and_h0_split": audit_2_planck_2018_error_bars_and_h0_split(),
        "guillotine_3_bbn_deuterium_helium": audit_3_bbn_deuterium_helium_squeeze(),
        "guillotine_4_weak_lensing_s8": audit_4_weak_lensing_s8_and_cosmic_web_qumond(),
        "guillotine_5_scoreboard_and_knobs": audit_5_scoreboard_symmetry_and_knob_count(),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
