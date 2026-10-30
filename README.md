# Theoretically Not A Physicist (`TNaP`) — `TNAP-Theories`

> **Official Open-Science & Simulation Repository for the YouTube Channel _Theoretically Not A Physicist (`TNaP`)_ and [`stoler.systems`](https://stoler.systems)**
>
> **Transparency & Responsible AI Charter:**
> I am **David Stoler**—an independent builder and outside-the-box thinker, **not** a professional physicist. With modern AI tools, curious builders who never went through a traditional physics PhD now have an extraordinary creative and mathematical partner—**provided we stay grounded, never get things twisted, and never confuse an exploratory AI-assisted toy model with proven, peer-reviewed laws of nature.**
>
> Everything in `TNAP-Theories` was developed openly with multi-agent **Gemini Argon inside Google Antigravity** and is published here so physicists, students, software engineers, and skeptics can inspect every script, run every equation, and poke holes in our assumptions.

---

## 1. Honest Peer-Review Scorecard: What Was Tested vs. What Remains Unsolved

| Tier | Status | Exact Scope in This Repository |
| :--- | :--- | :--- |
| **Symbolic Identities (`SymPy`)** | **Verified Algebraically** | Exact Bose–Einstein / McGaugh RAR interpolation bridge (`1/(1 - exp(-sqrt(y)))`), smooth 4D Euclidean catenoid waist curvature (`K_max = 24 / r_0^4 < infinity`), reciprocal two-boundary conserved double-slit current (`div j_fi = 0`), and electromagnetic impedance identity (`alpha_EM = Z_0 / (2 R_K) = 1/137.035999`). |
| **Simplified Toy Solvers (`NumPy` / `SciPy`)** | **1D / Radial Proxies Only** | 1D Split-Step Gross–Pitaevskii soliton pass-through (`4,574 km/s` Bullet Cluster offset proxy) vs. slow rebound (`14 km/s`), 1D BBN freeze-out ODE check, `DESI DR2` background expansion quadrature, and analytic `SPARC` RAR curve comparison. |
| **Major Unsolved Physics Hurdles** | **Open — Help Critique!** | **Not yet solved:** (1) Full `CLASS` / `CAMB` 2,500-multipole CMB Boltzmann acoustic peak spectrum without cold dark matter dust; (2) Full 3D relativistic magnetohydrodynamic + weak-lensing cluster merger simulation; (3) Individual MCMC mass-to-light fits across all 175 raw `SPARC` galaxy tables; (4) A single UV-complete Lorentz-covariant Standard Model Lagrangian. |

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
- **[`episode0_flagship/`](episode0_flagship/)** — Native `4K UHD` (`3840x2160`) PyTorch CUDA 3D physics rendering code, verbatim subtitle manifest, and YouTube thumbnails.

---

## 4. Published Physics Literature Parallels

Several intuitions explored here connect directly to peer-reviewed literature by professional physicists:
- **Boyle, Finn & Turok (2018)**, *Phys. Rev. Lett.* 121, 251301 — *CPT-Symmetric Universe*
- **Barbour, Koslowski & Mercati (2014 / 2020)** — *The Janus Point* (bidirectional arrows of time from a central complexity minimum)
- **Price (1996) & Wharton (2015–2020)**, *Rev. Mod. Phys.* — *All-at-Once / Two-Boundary Quantum Mechanics*
- **Verlinde (2016)**, *SciPost Phys.* 2, 016 — *Emergent Gravity and the Dark Universe*
- **Berezhiani & Khoury (2015)**, *Phys. Rev. D* 92, 103510 — *Theory of Dark Matter Superfluidity*
- **Bilson-Thompson (2005)**, *arXiv:hep-ph/0503213* — *A Topological Model of Composite Preons*

---

## 5. Spot a Flaw? Open an Issue!

Disagree with a step, spot an algebraic mistake, or know an observational constraint that sinks one of these claims? Please open a **GitHub Issue** with the script or monograph filename and tell us what we missed!
