# Theoretically Not A Physicist (`TNaP`) — `TNAP-Theories`

> **Official Open-Science & Simulation Repository for the YouTube Channel _Theoretically Not A Physicist (`@TNaPhysicist`)_ and [`stoler.systems`](https://stoler.systems)**
> - **Watch Episode 2 (4K — The Upside-Down Big Bang & Where All the Antimatter Went):** [`https://youtu.be/cBJzvmWhCgk`](https://youtu.be/cBJzvmWhCgk)
> - **Watch Episode 1 (4K — Time, Memory, GPS & The `1.000000` Horizon):** [`https://youtu.be/gZXKEAZZLQE`](https://youtu.be/gZXKEAZZLQE)
> - **Watch Episode 0 (4K Flagship Overview):** [`https://youtu.be/Wsj3BCWtPbc`](https://youtu.be/Wsj3BCWtPbc)
>
> **Transparency & Responsible AI Charter:**
> I am **David Stoler**—an independent builder and outside-the-box thinker, **not** a professional physicist. With modern AI tools, curious builders who never went through a traditional physics PhD now have an extraordinary creative and mathematical partner—**provided we stay grounded, never get things twisted, and never confuse an exploratory AI-assisted toy model with proven, peer-reviewed laws of nature.**
>
> Everything in `TNAP-Theories` was developed openly with multi-agent **Gemini Argon inside Google Antigravity** and is published here so physicists, students, software engineers, and skeptics can inspect every script, run every equation, and poke holes in our assumptions.

---

## NEW — Official Blind Pre-Registration Ahead of ESA `Gaia DR4` (Dec 2, 2026) & `BHEX`

[![DOI v1.1.0](https://zenodo.org/badge/DOI/10.5281/zenodo.23988569.svg)](https://doi.org/10.5281/zenodo.23988569)
[![DOI Concept](https://zenodo.org/badge/DOI/10.5281/zenodo.23919216.svg)](https://doi.org/10.5281/zenodo.23919216)
[![Code License: AGPL v3](https://img.shields.io/badge/Code_License-GNU_AGPLv3-blue.svg)](LICENSE)
[![Docs & Visuals: CC BY 4.0](https://img.shields.io/badge/Papers_%26_Visuals-CC_BY_4.0-lightgrey.svg)](LICENSE-DOCS.md)

Before ESA opens the 66-month **`Gaia Data Release 4`** catalog on **December 2, 2026**, we have locked zero-free-parameter 3D conservative QUMOND wide-binary predictions and strong-field black-hole falsification cutoffs on CERN Zenodo (Version `1.1.0` DOI **`10.5281/zenodo.23988569`**, archived original Version `1.0.0` DOI **`10.5281/zenodo.23919217`**, all-versions Concept DOI **`10.5281/zenodo.23919216`**):

- **Read the Full Blind Pre-Registration (+ Nov 5 Pre-DR4 Calibration Addendum):** **[`predictions_2026_blind/PREREGISTRATION_GAIA_DR4_AND_BHEX.md`](predictions_2026_blind/PREREGISTRATION_GAIA_DR4_AND_BHEX.md)**
- **Locked Machine-Readable Manifests (`SHA-256`):**
  - **Protocol `v1` (Untouched Original):** [`predictions_2026_blind/preregistered_numbers_2026_11.json`](predictions_2026_blind/preregistered_numbers_2026_11.json) (`fa1f5cc50885f1de71fde71201a9320d6c071e44c586708207fb8fc3fe471328`)
  - **Protocol `v2` (Systematics-Hardened on `6,322` Real `Gaia DR3` Pairs):** [`predictions_2026_blind/zenodo_v2_manifest.json`](predictions_2026_blind/zenodo_v2_manifest.json) (`a59beaae575cef9f7cad46f8ad7cb72a14d2fc422d8c5ba857ebded97b6c4b9c`)
- **Verify Every Number on CPU in 12 Seconds:**
  ```bash
  python predictions_2026_blind/run_gaia_dr4_and_bhex_preregistration.py
  ```

| Blind Test | `Lambda-CDM` / GR Baseline | **Locked Zero-Knob `TNaP` Forecast** |
| :--- | :---: | :---: |
| **`Gaia DR4` Local Backyard (`d <= 300 pc`, `15,000 AU`)** | `0.00%` boost | **`+16.14%`** *(Real `Gaia DR3` `Protocol v2` dry run: **`+0.97% ± 9.48%`**, `1.6σ` `INCONCLUSIVE`)* |
| **`Gaia DR4` Galactic Compass Split (`d <= 300 pc`, `15k AU`)** | `0.00%` (`0°` vs `90°`) | **`+17.08%` (GC Aligned) vs `+15.37%` (Perp)** *(`+1.71%`)* |
| **`Gaia DR4` Environment Step (`d <= 2.5 kpc`, `15k AU`)** | `0.00% -> 0.00% -> 0.00%` | **`+12.16%` (Inner) $\to$ `+20.98%` (Thick) $\to$ `+25.64%` (Lower Halo)** *(DR3 `N_halo = 1` at `SNR <= 0.25`)* |
| **Strong-Field Black-Hole Throat (`WeaveForge v1.1.0` Row 8)** | `5.1962 r_g` (`Q_220 = 3.15` at `a=0.67`) | **Bare `exp(2U)` (`+4.63%`) FALSIFIED at `5.92σ` by LVK O4 $\to$ Episode 1 Gibbons Spool (`07_tnap_gibbons_spool`, `0` new knobs) PASSES at `0.33σ` (`+0.00%` static shadow + post-merger GW echoes)!** |

---

## 1. Honest Peer-Review Scorecard: What Was Tested vs. What Remains Unsolved

| Tier | Status | Exact Scope in This Repository |
| :--- | :--- | :--- |
| **Symbolic Identities (`SymPy`)** | **Verified Algebraically** | Exact Bose–Einstein / McGaugh RAR interpolation bridge (`1/(1 - exp(-sqrt(y)))`), smooth 4D Euclidean catenoid waist curvature (`K_max = 24 / r_0^4 < infinity`), reciprocal two-boundary conserved double-slit current (`div j_fi = 0`), Gauss–Codazzi ADM/BSSNok constraints, and electromagnetic impedance identity (`alpha_EM = Z_0 / (2 R_K) = 1/137.035999`). |
| **3D Variational PDE, BSSNok, Spin-2 GW, Fermion, Real `Gaia DR3` & `CAMB` Wind Tunnel** | **Verified Numerically (`110/110` Tests in `WeaveForge v1.1.0`)** | Unified 3D two-knot $1/r^2$ attraction, `< 1.35%` Matter–Antimatter Weak Equivalence, **5-channel causal spin-2 LIGO tensor waves ($h_+/h_\times$)**, **3D Finkelstein–Rubinstein $(-1)^{Q_H}$ spin-$1/2$ Pauli core repulsion vs. $\Delta\psi=\pi$ singlet pairing**, **20-field 3+1D ADM/BSSNok + Lichnerowicz strong-field GPU/CPU backreaction**, **unbiased `48^3` 3D Catenoid Kibble–Zurek quench + $5.0\sigma$ Weyl chiral baryogenesis**, **single-`H_0` 8-row `CAMB` + `BBN` + `S_8` + `LVK O4` + `AST` knob referee**, and **real `6,322`-pair ESA `Gaia DR3` dual-protocol (`v1`/`v2`) calibration** in [`WeaveForge v1.1.0`](https://github.com/dragula22/WeaveForge). |
| **Simplified Toy Solvers (`NumPy` / `SciPy`)** | **1D / Radial Proxies Only** | 1D Split-Step Gross–Pitaevskii Bullet Cluster pass-through (`4,574 km/s`) vs. slow rebound (`14 km/s`), 1D BBN freeze-out ODE check, and `DESI DR2` background expansion quadrature. |
| **Candid Wind-Tunnel Catches & Open Physics Seams (`v1.1.0`)** | **Open — Help Critique!** | **Caught openly by our own `WeaveForge v1.1.0` + CPU Red-Team audit:** (1) **Strong-Field Photon-Sphere No-Go & Gibbons Resolution:** Bare `exp(2U)` (`+4.63%` shadow) and even interior-only ($r < r_{\text{ph}}$) clamps fail spinning LVK O4 ringdown (`5.92σ`; empirical `2σ` shadow ceiling `<= +1.32%`), whereas zero-knob Gibbons projective saturation (`07_tnap_gibbons_spool.toml`, $R_H=2GM/c^2$) passes at `0.27σ` IMR / `0.33σ` LVK O4 (`+0.00%` shadow + Planck-spool echoes); (2) **Real `Gaia DR3` Calibration (`6,322` Pairs):** Missing RVs on faint M-dwarfs cause `+84.96%` unbound-flyby leakage in naive `Protocol v1`; hardened `Protocol v2` (`v_tilde <= 2.60` + inner triple calibration `f_hat = 0.308`) yields `+0.97% ± 9.48%` (`INCONCLUSIVE` at DR3 precision, `N_halo = 1`), awaiting `Gaia DR4` (`2.7x` sharper PMs); (3) **`CMB -> SPARC` Cross-Scale Seam:** Unscreened $\Omega_{\text{pleat}}=0.260$ double-counts in `NGC 3198` (`256 km/s`, `[WARN]` across `TNaP`, `AeST`, and `Superfluid DM`) unless post-BBN condensation + `L_scr ~ 0.25 Mpc` (`+1` knob) is derived from the action. |

---

## 2. Quick-Start: Run the Python Simulation Suites Yourself

Requires Python `3.10+` with `numpy`, `scipy`, and `sympy` (`pip install numpy scipy sympy`):

```bash
# Round 3: Quantum foundations, complex-time & two-boundary double-slit suite
python simulations/r3_unified_bhhtc_quantum_sim.py

# Round 3: Graviton-free cosmology, analytic RAR, DESI DR2 & cluster proxies
python simulations/r3_unified_bhhtc_cosmos_sim.py

# Round 4: Adversarial Red-Team kill-tests (LEP2, BBN, Kerr, cosmic-ray bounds)
python simulations/r4_redteam_falsification_suite.py

# Round 6: 1D Split-Step Gross-Pitaevskii Bullet Cluster vs. slow dwarf rebound
python simulations/r6_bullet_cluster_jwst_and_vacuum_gauntlet.py

# Round 7: Exponential solar-system horizon shielding & 3-generation ribbon braids
python simulations/r7_exponential_shielding_and_hubble_rescue.py
python simulations/r7_braid_generations_and_wick_pinhole.py

# Round 8: Electric stretch vs. magnetic twist weave split & 1/137 impedance ledger
python simulations/r8_em_duality_split_and_master_ledger.py
```

---

## 3. Repository Structure

- **[`charter/`](charter/)** — Epistemic charter & 2026 empirical survival bounds (`MICROSCOPE`, `Cassini`, `GW170817`, `Planck`, `SPARC`, `DESI DR2`, `JWST`).
- **[`round1_divergent/`](round1_divergent/)** — Four competing initial theoretical architectures (Temporal Rheology, Tensor Horizon, Bi-Temporal Holonomic Action, Compton Vacuum Condensate).
- **[`round2_crucible/`](round2_crucible/)** — Cross-theory empirical crucible & comparative audit.
- **[`round3_synthesis/`](round3_synthesis/)** — Convergent synthesis & candidate tabletop/satellite experimental falsification proposals (`E1`–`E7`).
- **[`round4_redteam/`](round4_redteam/)** — Adversarial Red-Team stress tests & survival audit.
- **[`round5_inverted_attractor/`](round5_inverted_attractor/)** — Inverted-entropy cosmic hourglass (`Chaos -> Smooth Big Bang Waist`) & reciprocal double-slit analysis.
- **[`round6_gauntlet/`](round6_gauntlet/)** — CPT two-wing antimatter sorter, 1D Bullet Cluster pleat collisions, and engineering feasibility limits.
- **[`round7_counterintuitive/`](round7_counterintuitive/)** — Unruh horizon solar-system screening, `2x` null-thread light bending, and 3-generation topological braids.
- **[`round8_master_overview/`](round8_master_overview/)** — Electric thread stretch vs. magnetic plaquette twist (`1/137`).
- **[`series_blueprint/`](series_blueprint/)** — Plain-English Episode 0 script & 6-chapter companion roadmap.
- **[`simulations/`](simulations/)** — All 29 symbolic (`SymPy`) and numerical (`NumPy`/`SciPy`) Python scripts.
- **[`science_workbench/`](science_workbench/)** — Interactive multi-engine stress-test suite (`Astropy`, `QuTiP`, `Cirq`, `py-pde`, CMB 3rd-peak Boltzmann solver, GPS `+38.64 µs/day` & `3,189 km` crossover, and `1.000000` Planck-tension black-hole spool).
- **[`episode0_flagship/`](episode0_flagship/)** — Episode 0 (`https://youtu.be/Wsj3BCWtPbc`) native `4K UHD` (`3840x2160`) PyTorch CUDA 3D physics rendering code, verbatim subtitle manifest, and YouTube thumbnails.
- **[`episode1_time_and_memory/`](episode1_time_and_memory/)** — Episode 1 (`https://youtu.be/gZXKEAZZLQE`) native `4K UHD` GPU scene engine (`ep1_gpu_scenes.py`), compositor (`render_episode1_4k.py`), chunk deck, and standalone `.srt` subtitles.
- **[`episode2_upside_down_big_bang/`](episode2_upside_down_big_bang/)** — Episode 2 (`https://youtu.be/cBJzvmWhCgk`) native `4K UHD` solid-satin 3D GPU scenes (`ep2_gpu_scenes.py`), compositor (`render_episode2_4k.py`), chunk deck, and standalone `.srt` subtitles.

---

## 4. Published Physics Literature Parallels

Several intuitions explored here connect directly to peer-reviewed literature by professional physicists:
- **Boyle, Finn & Turok (2018)**, *Phys. Rev. Lett.* 121, 251301 — *CPT-Symmetric Universe*
- **Deng & Handley (2024, 2025)**, *Phys. Rev. D* (`arXiv:2407.18225`, `arXiv:2509.10379`) — *Quantized Spatial Curvature $\Omega_K$ in Globally CPT-Symmetric Universes*
- **Faddeev & Niemi (1997)**, *Nature* 387, 58 — *Stable Knot-Like Structures in Classical Field Theory*
- **Barbour, Koslowski & Mercati (2014 / 2020)** — *The Janus Point* (bidirectional arrows of time from a central complexity minimum)
- **Price (1996) & Wharton (2015–2020)**, *Rev. Mod. Phys.* — *All-at-Once / Two-Boundary Quantum Mechanics*
- **Verlinde (2016)**, *SciPost Phys.* 2, 016 — *Emergent Gravity and the Dark Universe*
- **Berezhiani & Khoury (2015)**, *Phys. Rev. D* 92, 103510 — *Theory of Dark Matter Superfluidity*
- **Bilson-Thompson (2005)**, *arXiv:hep-ph/0503213* — *A Topological Model of Composite Preons*

---

## 5. Spot a Flaw? Open an Issue!

Disagree with a step, spot an algebraic mistake, or know an observational constraint that sinks one of these claims? Please open a **GitHub Issue** with the script or monograph filename and tell us what we missed!

---

## 6. Open-Science Dual Licensing (`AGPL-3.0` + `CC BY 4.0`)

Copyright &copy; 2026 **David Stoler** (*Theoretically Not A Physicist* — [`stoler.systems`](https://stoler.systems) | [`@TNaPhysicist`](https://www.youtube.com/@TNaPhysicist)).

- **Source Code & Simulation Engines ([`LICENSE`](LICENSE)):** Licensed under the **GNU Affero General Public License v3.0 (`AGPL-3.0-only`)**. Anyone is free to inspect, run, test, and modify the code—provided all modified or network-hosted versions **remain 100% open-source under `AGPL-3.0`** and preserve attribution to David Stoler ([`NOTICE`](NOTICE)). Closed-source or proprietary relicensing is strictly prohibited.
- **Monographs, Papers, Subtitles & Visual Assets ([`LICENSE-DOCS.md`](LICENSE-DOCS.md)):** Licensed under **Creative Commons Attribution 4.0 International (`CC BY 4.0`)**—free to share, cite, and build upon with clear attribution to David Stoler (`https://stoler.systems` / DOI [`10.5281/zenodo.23919217`](https://doi.org/10.5281/zenodo.23919217)).
