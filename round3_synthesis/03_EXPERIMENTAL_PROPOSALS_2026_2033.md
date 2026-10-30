# Round 3 Part III: Definitive Experimental Falsification & Engineering Blueprints Dossier (2026–2033)

**Architect:** Dr. Priya Ramanujan (*Chief Phenomenologist & Experimental Crucible Architect*)  
**Collective:** Foundational Physics Discovery Collective — Round 3 Convergent Synthesis (Part III)  
**Executable SNR & Error-Budget Suite:** [r3_experimental_snr_calculator.py](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py)  
**Cross-Theory Audit & Unification Reference:** [CRUCIBLE_COMPARATIVE_AUDIT.md](file:///c:/Projects/Discovery/round2_crucible/CRUCIBLE_COMPARATIVE_AUDIT.md), [r2_cross_theory_benchmark.py](file:///c:/Projects/Discovery/simulations/r2_cross_theory_benchmark.py)

---

## Executive Summary: From Unification to Knife-Edge Falsification

In Round 2 ([CRUCIBLE_COMPARATIVE_AUDIT.md](file:///c:/Projects/Discovery/round2_crucible/CRUCIBLE_COMPARATIVE_AUDIT.md)), we proved that the four Round 1 frameworks—**VTFT** ([01_tablecloth_temporal_rheology.md](file:///c:/Projects/Discovery/round1_divergent/01_tablecloth_temporal_rheology.md)), **TTHO** ([02_tensor_horizon_presence.md](file:///c:/Projects/Discovery/round1_divergent/02_tensor_horizon_presence.md)), **BTHAT** ([03_bitemporal_holonomic_action.md](file:///c:/Projects/Discovery/round1_divergent/03_bitemporal_holonomic_action.md)), and **RVPC** ([04_compton_vacuum_condensate.md](file:///c:/Projects/Discovery/round1_divergent/04_compton_vacuum_condensate.md))—are complementary gauge projections of the unified **Bi-Horizon Holonomic Tensor-Condensate (`BHHTC`)**. Yet a foundational physical synthesis is only as strong as the experiments capable of destroying it.

This dossier presents **seven concrete, engineering-ready experimental protocols (`E1`–`E7`)**, ordered strictly by **deployment immediacy and capital cost**—from zero-dollar quantum-cloud circuits and public survey pipelines runnable **this month**, through sub-million-dollar ultrafast optics and levitated optomechanics (**2027–2029**), to dedicated cryogenic tabletop quantum gravity (**2029–2031**) and a $126.7\text{ kg}$ wet-mass Falcon 9 ESPA-Grande cislunar rideshare mission (**`JANUS-SADDLE`, 2031–2033**). Every signal-to-noise ratio, shot count, systematic floor, and propellant budget below is computed from first principles in [r3_experimental_snr_calculator.py](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py).

### Master 2026–2033 Experimental Deployment Matrix

| Protocol | Tier & Timeline | Est. Cost | Hardware / Dataset | Core Observable | Integration / Run Time | Discovery SNR | Primary Theories Separated |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| **E1** | **Immediate** (Month 1) | $\sim\$0$ *(Cloud grant)* | Quantinuum H2-1 / IBM Heron r2 ($11\text{–}27$ qubits) | Stinespring-Petz Wigner visibility $V(N_{\text{tot}})$ & $S_{\text{LF}}$ | $2.50\text{ hrs}$ (H2-1) / $42\text{ s}$ (Heron), $108\text{k}$ shots | **$58.7\sigma$** (H2) / **$45.2\sigma$** (Heron) | TTHO/`BHHTC` Page Cliff vs. Unbounded Linear QM |
| **E2** | **Immediate** (Month 1–6) | $\$0$ *(Public data)* | SPARC + DESI DR2/DR3 + 12 Mergers + Gaia DR3/DR4 | $\frac{2}{\sqrt{3}}$ $a_0(H_0)$, Ly$\alpha$ $w(z>2)$, $\lambda_{\text{cluster}}$, WB $\Delta v_{\text{orb}}$ | Archival MCMC / Fisher pipeline | **$4.5\sigma\text{–}18.1\sigma$** | VTFT vs. `BHHTC` vs. BTHAT vs. RVPC vs. $\Lambda\text{CDM}$ |
| **E3** | **Near-Term Lab** (2027) | $\sim\$250\text{k}$ | Twin $6\text{ fs}$ ITO-ENZ gated double slit + SPDC | Visibility step at $d_{\text{crit}} = c\,t_{\text{lead}} = 11.99\,\mu\text{m}$ | $70\text{ s}$ ($7\times 10^6$ heralded photons) | **$444.5\sigma$** | Orlov RVPC causal wake vs. Chen BTHAT / Std QM |
| **E4** | **Near-Term Lab** (2027–2029) | $\sim\$600\text{k}$ | $10\text{ mK}$ levitated nanodiamond NV + tunable LC | Non-analytic cusp $-\ln V_{\text{echo}} \propto (\eta_{\text{pin}}-1)^{3/2}$ | $76.7\text{ mins}$ ($2.3\times 10^5$ shots at $50\text{ Hz}$) | **$7.96\sigma$** ($\Delta\text{AIC}=+61.4$) | Vance VTFT stick-slip pinning vs. Smooth Lindblad QM |
| **E5** | **Tabletop QG** (2029–2031) | $\sim\$5\text{M}$ | Dual $10^{-14}\text{ kg}$ Stern-Gerlach NV interferometer | $(V_1, \mathcal{W}_{\text{BMV}}, S_{hh}^{\text{vac}}, f_{\text{QW}})$ | $8.0\text{ days}$ ($11,518$ drops at $60\text{ s}$ cycle) | **$5.0\sigma$** (`ENT`) / **$8.0\sigma$** (vs RVPC) | Spin-2 Graviton QGEM vs. `BHHTC` $D_{\text{sym}}$ vs. RVPC ($\mathcal{C}=0$) vs. KTM |
| **E6** | **Space Mode A** (2031–2033) | $\sim\$180\text{M}$ *(shared bus)* | `JANUS-SADDLE` at $258,809\text{ km}$ Sun-Earth null | Fast $0.6\text{–}2.5\text{ s}$ Chebyshev parabolic BMV phase | $3.3\text{ hrs}$ ($200$ drops; $2.54\text{ kg}$ Xe) | **$130.0\sigma$** (`159.8x` boost!) | Fast `BHHTC`/TTHO/BTHAT (`70.6–160x`) vs. QGEM/VTFT (`1.000x`) |
| **E7** | **Space Mode B** (2031–2033) | *Included in E6 bus* | $3.0\text{ m}$ squeezed $^{87}\text{Rb}$ BEC gradiometer on `JANUS-SADDLE` | Secular viscoelastic acceleration $\dot{a}_{\text{drift}} = 2.59\times 10^{-27}\text{ m/s}^3$ | $41.1\text{ days}$ station-kept ($46.7\text{ kg}$ total Xe) | **$5.0\sigma$** | Vance VTFT $\tau_{\text{rel}}=1.50\text{ Gyr}$ wake vs. $\Lambda\text{CDM}$ + GR ($\dot{a}=0$) |

---

## Master Programmatic Falsification Decision Tree

```mermaid
flowchart TD
    START["Start 2026-2033 Experimental Campaign"] --> E5["Protocol E5: Tabletop Dual-Readout BMV<br/>Measure Single-Arm V1(T) & Witness W_BMV = <XX> + |<ZY>|"]
    E5 -->|"V1 <= exp(-dphi/2), W <= 0.85"| STOCH["Stochastic Classical Gravity<br/>(KTM / Oppenheim Channel)<br/>Check LISA Pathfinder Squeeze"]
    E5 -->|"V1 = 0.968 oscillates, BUT W_BMV = 0.938 <= 1 (C = 0)"| E3_CHK["Localized-Core Acoustic Gravity (Orlov RVPC)<br/>Confirm via Protocol E3: 33.4 fs Double-Slit Cutoff<br/>& Gaia DR4 +4.6% Wide-Binary Boost"]
    E5 -->|"W_BMV = 1.069 > 1 (5-sigma Entangled!)"| E5C["Measure Squeezed Graviton Noise S_hh^vac<br/>& Quarter-Wave Fokker Gate (omega d/c = pi/2)"]
    E5C -->|"S_hh^vac > 0 & Retarded Damping"| QGEM_CHK["Quantized Spin-2 Graviton QGEM<br/>Test Protocol E6 Saddle: Must Give 1.000x<br/>& DESI DR3 w(z): Must Reconcile LCDM 4.2-sigma"]
    E5C -->|"S_hh^vac = 0 & Real Standing Fokker Phase"| E6["Graviton-Free Emergent Geometry!<br/>Launch JANUS-SADDLE to 258,809 km Null (Protocol E6)"]
    E6 -->|"Fast 0.6s Drop Gives 159.8x Phase Boost!"| BHHTC_BRANCH["Fast Elliptic Constraint Confirmed (BHHTC / TTHO / BTHAT)<br/>Discriminate Sub-Mechanisms via Protocols E1 & E2b:"]
    E6 -->|"Fast Drop Gives 1.0000x (Viscoelastic Freeze-Out!)"| E7["Switch JANUS-SADDLE to 41.1-Day BEC Hover (Protocol E7)<br/>+ Check Protocol E4 Aubry Cusp & E2c Old Cluster Decay"]
    E7 -->|"a_dot = 2.59e-27 m/s^3 (5-sigma) & (eta-1)^(3/2) Cusp"| VTFT_WIN["Dr. Vance's VTFT Confirmed!<br/>Check DESI DR3 w(z>2) -> -1.23 Plateau"]
    BHHTC_BRANCH -->|"E1 Shows Page Cliff at N_tot > 2 K_B<br/>& DESI DR3 w(z>2) -> -1.01"| BHHTC_WIN["Unified BHHTC / Omega-Tensor TTHO Confirmed!"]
    BHHTC_BRANCH -->|"E1 Shows V = 1.000 Everywhere<br/>& DESI DR3 w(2.0) = -1.11 Rebound"| BTHAT_WIN["Pure Unitary Two-Boundary BTHAT (Dr. Chen) Confirmed!"]
```

---

## Protocol E1 (Immediate — Month 1, Cost $\sim\$0$): Gate-Level Quantum Cloud Test of the Extended Wigner's Friend Stinespring-Petz Page Cliff

### 1.1 Physical Hypothesis & Target Law
In Standard Unbounded-Hilbert-Space QM, a super-observer ("Wigner") with quantum control over a "Friend" laboratory scrambling 1 logical spin across $N_{\text{tot}}$ qubits always recovers unit interference visibility $V(N_{\text{tot}}) = 1.000$ and maximal Local-Friendliness CHSH violation $S_{\text{LF}} = 2\sqrt{2} \approx 2.828$. By contrast, in **TTHO / `BHHTC`** ([02_tensor_horizon_crucible_defense.md](file:///c:/Projects/Discovery/round2_crucible/02_tensor_horizon_crucible_defense.md), [`r2_tensor_crucible_verification.py`](file:///c:/Projects/Discovery/simulations/r2_tensor_crucible_verification.py#L130-L256)), any physical observer or accessible holographic boundary possesses a finite Markov-blanket rank $2^{K_{\mathcal{B}}}$. Applying the exact linear CPTP **Stinespring-Petz recovery channel** (which strictly obeys relativistic no-signaling to $< 10^{-15}$) yields a flat plateau for $N_{\text{tot}} \le K_{\mathcal{B}}$ followed by the **Marchenko-Pastur Page Cliff** above $N_{\text{tot}} > 2 K_{\mathcal{B}}$:
$$V_{\text{TTHO}}(N_{\text{tot}}) \simeq \begin{cases} 1, & N_{\text{tot}} \le K_{\mathcal{B}}, \\ \dfrac{8}{3\pi}\,2^{-(N_{\text{tot}} - 2 K_{\mathcal{B}})/2}, & N_{\text{tot}} > 2 K_{\mathcal{B}}. \end{cases}$$

### 1.2 Exact Gate-Level Circuit Specification ($11\text{–}27$ Physical Qubits)
Computed in [`calc_protocol_e1_quantum_cloud`](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py#L73-L173) for **Quantinuum H2-1** ($56$ trapped-ion qubits, all-to-all connectivity, $\epsilon_{2Q} = 1.0\times 10^{-3}$, $\epsilon_{\text{SPAM}} = 1.5\times 10^{-3}$) and **IBM Heron r2** ($156$ superconducting qubits, $\epsilon_{2Q} = 3.0\times 10^{-3}$), fixing blanket capacity $K_{\mathcal{B}} = 6$ and sweeping $N_{\text{tot}} \in \{4, 6, 9, 12, 13, 14, 16, 18, 20\}$:

- **Qubit Register Map ($Q_{\text{phys}} = 1 + N_{\text{tot}} + K_{\mathcal{B}} = 11\text{ to }27\text{ qubits}$):**
  - `q[0]` ($1$ qubit): External Bell reference qubit $A$.
  - `q[1 .. K_B]` ($6$ qubits): Friend's accessible Markov-blanket register $\mathcal{H}_{\mathcal{B}}$.
  - `q[K_B+1 .. N_tot]` ($N_{\text{tot}} - 6$ qubits): Friend's internal horizon-scrambled register $\mathcal{H}_{\text{hor}}$.
  - `q[N_tot+1 .. N_tot+K_B]` ($6$ qubits): Isometric Stinespring ancilla register $\mathcal{H}_{\text{Petz}}$ implementing CPTP Petz transpose recovery unitarily without classical post-selection!
- **Gate Sequence (`Science Circuit S1`):**
  1. **Bell Preparation:** `H q[0]; CX q[0], q[1];` prepares $|\Phi^+\rangle_{A,S}$.
  2. **Friend Unitary 2-Design Brickwork Scrambler ($d_{\text{brick}} = 6$ layers, $N_{2Q,\text{scram}} = 6(N_{\text{tot}}-1)$ gates):** Alternate even/odd nearest-neighbor `SU(4)` blocks (compiled to $1$ native `ZZPhase` + single-qubit `U3` rotations per layer with pseudorandom Clifford+T Haar angles fixed ahead of time, plus Pauli twirling across 32 random compilations).
  3. **Horizon Trace (`Tr_hor`):** Leave `q[K_B+1 .. N_tot]` untouched (or mid-circuit measure & reset on H2-1 to enforce exact partial trace).
  4. **Isometric Petz Recovery Unitary $U_{\text{Petz}}$ ($28$ two-qubit gates on `q[1..K_B]` $\cup$ `q[N_tot+1..N_tot+K_B]`):** Synthesize the exact state-independent Petz Kraus isometric matrix $V_{\text{Petz}} = \sum_\ell |\ell\rangle_{\text{Petz}} \otimes R_\ell$ where $R_\ell = \frac{1}{\sqrt{2}} K_\ell^\dagger \omega_{\mathcal{B}}^{-1/2}$, routing recovered logical spin output onto `q[1]`.
  5. **Joint Wigner-Alice Tomography / CHSH Readout:** Measure `(q[0], q[1])` in Pauli $XX, YY, ZZ$ (for $V_{\text{mit}}$) and optimal Horodecki CHSH angles $(A_0, A_1) = (Z, X)$, $(W_0, W_1) = \frac{Z \pm V_{\text{eff}} X}{\sqrt{1+V_{\text{eff}}^2}}$ (for $S_{\text{LF}}$).

### 1.3 Mandatory Hardware-Noise Control Circuits (Defeating Gate-Noise Confounds)
To guarantee that exponential gate depolarization $(1 - \epsilon_{2Q})^{N_{2Q}}$ can **never** be mistaken for a Page Cliff, every $N_{\text{tot}}$ point executes two interleaved zero-parameter controls:
- **Control C1 (Full-Register Mirror Loschmidt Echo):** Applies $U_{\text{scram}}$ followed immediately by its exact gate-by-gate inverse $U_{\text{scram}}^\dagger$ across *all* $N_{\text{tot}}$ qubits ($2 N_{2Q,\text{scram}}$ gates). Under standard noisy QM, $F_{\text{echo}}(N_{\text{tot}})$ decays as a **strictly log-linear line** $\ln F_{\text{echo}} = -2\epsilon_{2Q}\cdot 6(N_{\text{tot}}-1)$, calibrating $\epsilon_{2Q}$ in situ! *(Bonus test: if physical hardware itself possesses an intrinsic horizon rank $K_{\mathcal{B}}^{\text{hw}} < 14$, even Control C1 will exhibit a sudden non-log-linear break!)*
- **Control C2 (Gate-Folded Zero-Noise Extrapolation, $1\times$ and $3\times$ Noise Stretch):** Replaces every `ZZPhase` gate $G$ with $G G^\dagger G$ on $1/3$ of the shots to extrapolate $\epsilon_{2Q} \to 0$.

### 1.4 Verified QPU Fidelity & Shot Budget Table (`Quantinuum H2-1`, $K_{\mathcal{B}} = 6$, $4,000\text{ shots/point}$)

| $N_{\text{tot}}$ | Physical Qubits $Q_{\text{phys}}$ | Science 2Q Gates | Raw $F_{\text{hw}}(\text{Sci})$ | Raw $F_{\text{hw}}(\text{Echo})$ | Mitigated $V_{\text{QM}}$ | Mitigated $V_{\text{TTHO}}$ | Uncertainty $\sigma_V$ | Predicted $S_{\text{LF}}$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `4` | `11` | `46` | `0.9522` | `0.9617` | `1.000` | **`1.0000`** | `0.0114` | `2.8284` |
| `6` | `13` | `58` | `0.9408` | `0.9389` | `1.000` | **`1.0000`** | `0.0121` | `2.8284` |
| `9` | `16` | `76` | `0.9240` | `0.9057` | `1.000` | **`0.9701`** | `0.0145` | `2.5081` |
| `12` *(Page $2K_{\mathcal{B}}$)* | `19` | `94` | `0.9075` | `0.8737` | `1.000` | **`0.7482`** | `0.0220` | `2.3157` |
| `14` | `21` | `106` | `0.8967` | `0.8529` | `1.000` | **`0.4244`** | `0.0273` | `2.1067` |
| `16` | `23` | `118` | `0.8860` | `0.8327` | `1.000` | **`0.2122`** | `0.0292` | `2.0272` |
| `18` | `25` | `130` | `0.8754` | `0.8129` | `1.000` | **`0.1061`** | `0.0299` | `2.0068` |
| `20` | `27` | `142` | `0.8650` | `0.7936` | `1.000` | **`0.0531`** | `0.0303` | `2.0017` |

- **Discovery Reach:** **$58.7\sigma$** in **$2.50\text{ QPU hours}$** on Quantinuum H2-1 ($108,000$ total shots across 9 circuit widths), or **$45.2\sigma$** in **$42\text{ seconds}$** ($0.7\text{ QPU mins}$) on IBM Heron r2!

---

## Protocol E2 (Immediate — Month 1–6, Cost $\$0$): Four-Prong Archival Multi-Survey Statistical Pipeline

Executed via [`calc_protocol_e2_archival_pipeline`](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py#L180-L241) on public/imminent catalogs with zero new hardware expenditure:

1. **Pipeline E2a — Testing the $\frac{2}{\sqrt{3}}$ Zero-Parameter Horizon Law $a_0(0) = \frac{c H_0}{\sqrt{3}\pi}$ & RVPC Knee on SPARC (175 Galaxies):**
   - Locking $H_0 = 67.00 \pm 0.50\text{ km/s/Mpc}$ from joint DESI DR2 + Planck PR4 (`Benchmark 1`), **Vance/Chen's 3D von-Mises projection** predicts $a_0^{(3D)} = \mathbf{1.1963\times 10^{-10}\text{ m/s}^2}$—agreeing with SPARC's global fit $(1.200 \pm 0.045)\times 10^{-10}\text{ m/s}^2$ (marginalizing disk $\Upsilon_{3.6} = 0.50 \pm 0.04\,M_\odot/L_\odot$) to **$0.08\sigma$**, whereas bare 1D $c H_0/(2\pi) = 1.0360\times 10^{-10}\text{ m/s}^2$ is in **$3.64\sigma$ tension**! Simultaneously fit the transition curvature $d^2\ln g_{\text{obs}}/d(\ln g_{\text{bar}})^2$ over $g_{\text{bar}} \in [0.3, 3.0]\,a_0$ on 45 bulge-free gas-rich dwarfs ($f_{\text{gas}} > 0.7$, immune to $\Upsilon_*$ systematics) to test McGaugh/BE $(1 - e^{-\sqrt{y}})^{-1}$ (`0.0017 dex`) vs. Orlov's sharper implicit superfluid transition $g(1 - e^{-g/a_0}) = g_{\text{bar}}$ (`0.0414 dex`).
2. **Pipeline E2b — DESI DR3 + Euclid Ly$\alpha$ Forest BAO ($z = 1.8\text{–}3.5$) High-$z$ $w(z)$ Derivative Test:**
   - Replace CPL $(w_0, w_a)$ in `Cobaya`/`MontePython` with a 2-bin high-$z$ projection comparing: (i) **VTFT's exact parameter-free law** $w_{\text{eff}}(z) = -1 - \frac{1}{2}q(z) \to \mathbf{-1.21}$ across $z \in [1.8, 3.2]$; (ii) **BTHAT's bi-temporal rebound** $w_{\text{2B}} \to \mathbf{-1.08}$; and (iii) **`BHHTC`/TTHO/RVPC's cosmic-web/condensation snap-back** $w_{\text{DE}}(z) = -1 + \pi f_{\text{web}}(a) \to \mathbf{-1.02}$. Four Ly$\alpha$ + QSO BAO bins ($\sigma_{D_H/r_d} = 0.45\text{–}0.95\%$) yield $\sigma(\bar{w}_{z>1.8}) = 0.042$, separating **VTFT vs. `BHHTC` at $4.52\sigma$** and **VTFT vs. BTHAT at $3.10\sigma$**.
3. **Pipeline E2c — Late-Stage Dissociative Cluster Merger Halo-Decay Regression ($t_{\text{post}} = 150\text{–}950\text{ Myr}$):**
   - Assemble weak+strong lensing convergence maps (JWST NIRCam + Euclid VIS + Chandra/XMM hydro-shock Mach timing) across 12 dissociative mergers spanning $t_{\text{post}} \in [0.15, 0.95]\text{ Gyr}$ (*1E 0657-56, MACS J0025, Abell 2744, El Gordo, Abell 520, Abell 2146, CIZA J2242, 1RXS J0603, MACS J1149, Abell 1758N, ZwCl 0008, Abell 56*). Regress $\ln[(M_{\text{lens}} - M_{\text{bar}})/M_{\text{bar,pre}}] = C_0 - \lambda_{\text{rel}}\,t_{\text{post}}$: at $11\%$ per-subcluster mass precision, $\sigma(\lambda_{\text{rel}}) = \mathbf{0.118\text{ Gyr}^{-1}}$, testing **VTFT's $\lambda_{\text{rel}} = (1.50\text{ Gyr})^{-1} = 0.667\text{ Gyr}^{-1}$ ($41.3\%$ decay at $800\text{ Myr}$) at $5.39\sigma$** against `BHHTC`/$\Lambda\text{CDM}$ ($\lambda_{\text{rel}} \le 0.03\text{ Gyr}^{-1}$).
4. **Pipeline E2d — Gaia DR4 4D $(s, e, R_{\text{gal}}, v_{\text{pec}})$ Wide-Binary Crucible:**
   - Select $N = 15,000$ halo/thick-disk and thin-disk wide binaries at $s \in [6, 15]\text{ kAU}$ vetted by Gaia DR4 epoch astrometry + RVS multi-epoch radial velocities + RUWE $< 1.15$ ($\sigma(\Delta v_{\text{orb}}) = \mathbf{0.92\%}$ including $0.85\%$ hierarchical-triple residual floor): separates **`BHHTC`/TTHO/BTHAT (`+16.6%`) vs. VTFT (`0.0%` advective screening) at $18.1\sigma$**, **`BHHTC` vs. Orlov RVPC (`+4.6%`) at $13.1\sigma$**, and **RVPC vs. VTFT at $5.0\sigma$**—plus tests VTFT's unique inverse-$v_{\text{pec}}$ dependence by splitting stars at $v_{\text{pec}} < 12\text{ km/s}$ vs. $v_{\text{pec}} > 80\text{ km/s}$!

---

## Protocol E3 (Near-Term Lab — 2027, Cost $\sim\$250\text{k}$): Symmetric ENZ-Gated Femtosecond Double-Slit Causal Wake Test

### 3.1 Resolving the Spectral-Chirp Trap via Twin ITO Epsilon-Near-Zero Gates
In **Dr. Orlov's RVPC**, single-particle double-slit interference requires the relativistic vacuum phase wake (propagating at speed $c$ through the condensate) to establish cross-slit phase coherence across separation $d$: if the slits are switched open only at lead time $t_{\text{lead}}$ prior to single-photon/soliton arrival, interference vanishes whenever $d > c\,t_{\text{lead}}$ ($\tau_{\text{wake}} = d/c = 33.36\text{ fs}$ at $d = 10\,\mu\text{m}$). Conversely, in **Standard QM and Dr. Chen's BTHAT**, closed 4D Schwinger-Keldysh holonomy loops depend solely on boundary transmission at the arrival instant $t = 0$, predicting **zero dependence on $d/c$**.

> [!WARNING]
> **Critical Experimental Trap Defeated:** Gating *only* Slit 2 with a $6\text{ fs}$ shutter imprints an asymmetric ultrafast spectral chirp $\Delta\omega \sim 1/\tau_{\text{rise}}$ on Arm 2, artificially destroying interference even in Standard QM! **Our Solution:** Gate **both Slit 1 and Slit 2 symmetrically and simultaneously** at $t = -t_{\text{lead}} = -40.0\text{ fs}$ using matched $120\text{ nm}$ Indium-Tin-Oxide (ITO) epsilon-near-zero (ENZ) pump-modulated sub-wavelength slits ($\tau_{\text{rise}} = 6.0\text{ fs}$, heralded $800\text{ nm}$ SPDC single photons with $\sigma_t = 8.0\text{ fs}$), guaranteeing exact wavepacket overlap $|\langle\chi_1|\chi_2\rangle| = 1.000$ across all $d$!

### 3.2 Quantitative Scan & Shot Budget ([`calc_protocol_e3_femtosecond_doubleslit`](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py#L248-L293))
Holding $t_{\text{lead}} = 40.0\text{ fs}$ fixed ($d_{\text{crit}} = c\,t_{\text{lead}} = \mathbf{11.99\,\mu\text{m}}$) at $10^5\text{ Hz}$ heralded SPDC rate ($10\text{ s} = 10^6$ clicks per step, $\sigma_V = 0.0042$):

| Slit Spacing $d$ [$\mu\text{m}$] | Causal Wake Time $\tau_{\text{wake}} = d/c$ [fs] | $V_{\text{QM / BTHAT}}$ | $V_{\text{Orlov RVPC}}$ | Step Significance |
| :---: | :---: | :---: | :---: | :---: |
| `5.0` | `16.68` | `0.9400` | `0.9307` | $2.2\sigma$ *(Control lock!)* |
| `10.0` | `33.36` | `0.9400` | **`0.7020`** | **$56.7\sigma$** |
| `12.0` | `40.03` | `0.9400` | **`0.4690`** | **$112.1\sigma$** |
| `15.0` | `50.03` | `0.9400` | **`0.1483`** | **$188.5\sigma$** |
| `25.0` | `83.39` | `0.9400` | **`0.0000`** | **$223.8\sigma$** |
| `40.0` | `133.43` | `0.9400` | **`0.0000`** | **$223.8\sigma$** |

- **Total Integration Time:** **$70\text{ seconds}$** across 7 motorized/lithographic slit masks $\implies$ **$444.5\sigma$ decisive test** (plus shifting pump delay to $t_{\text{lead}} = 100\text{ fs}$ must shift the exact visibility cliff from $11.99\,\mu\text{m}$ to $29.98\,\mu\text{m}$, ruling out any static diffraction artifact!).

---

## Protocol E4 (Near-Term Lab — 2027–2029, Cost $\sim\$600\text{k}$): Levitated Nanodiamond Spin-Echo Test of Vance's Non-Analytic Aubry Pinning Cusp

### 4.1 Apparatus & Non-Analytic Threshold Signature
In **Dr. Vance's VTFT** ([01_tablecloth_temporal_rheology.md](file:///c:/Projects/Discovery/round1_divergent/01_tablecloth_temporal_rheology.md)), quantum measurement is a topological **Prandtl-Tomlinson / Aubry stick-slip transition** at dimensionless pinning coupling $\eta_{\text{pin}} = 1$: below $\eta_{\text{pin}} \le 1$, reversible spin-echo refocussing completely erases elastic deformation ($\Delta S_{\text{scar}} = 0$), whereas above $\eta_{\text{pin}} > 1$ hysteretic phase-slip loops dissipate action with a **non-analytic $3/2$ critical exponent**:
$$-\ln V_{\text{echo}}(\eta_{\text{pin}}) = \gamma_{\text{bg}} + A_{\text{scar}}\,(\eta_{\text{pin}} - 1)^{3/2}\,\Theta(\eta_{\text{pin}} - 1),$$
whereas in **Standard Open-System Lindblad QM**, weak-to-moderate ancilla coupling produces a smooth analytic Taylor expansion $-\ln V_{\text{Lindblad}}(\eta) = c_0 + c_1\eta + c_2\eta^2 \in C^\infty$.

- **Experimental Realization ([`calc_protocol_e4_aubry_cusp`](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py#L300-L341)):**
  - $R = 88\text{ nm}$ ($m = 10^{-17}\text{ kg}$) nanodiamond containing a single $\text{NV}^-$ spin levitated in a $10\text{ mK}$, $10^{-11}\text{ mbar}$ Paul/diamagnetic micro-trap ($\omega_m/2\pi = 10\text{ kHz}$, Ramsey echo duration $2\tau = 2.0\text{ ms}$, background $\gamma_{\text{bg}} = 0.035 \implies V_{\text{bg}} = 0.9656$).
  - Inductively/magnetically couple the NV-oscillator displacement to a flux-tunable superconducting SQUID/LC ancilla resonator, sweeping $\eta_{\text{pin}} \in [0.50, 1.60]$ across $23$ steps ($10,000$ Ramsey shots/step at $50\text{ Hz}$ $\implies$ **$76.7\text{ minutes}$** total acquisition).
  - Fitting against the *most general competing 3-parameter smooth quadratic Lindblad curve* yields **$7.96\sigma$ ($\Delta\text{AIC} = +61.4$)** for $A_{\text{scar}} = 0.45$, with $5\sigma$ discovery sensitivity down to **$A_{\text{scar}}^{\min} = 0.2826$**.

---

## Protocol E5 (Tabletop Quantum Gravity — 2029–2031, Cost $\sim\$5\text{M}$): Dual-Readout Cryogenic BMV + Quarter-Wave Fokker & Graviton-Noise Witness

### 5.1 Four-Way Discrimination in One Apparatus
Standard QGEM proposals measure *only* joint entanglement witness $\mathcal{W}_{\text{BMV}}$, missing the extraordinary diagnostic power of combining **single-arm visibility $V_1(T)$**, **phase-rotated joint witness $\mathcal{W}_{\text{BMV}}(\alpha)$**, **squeezed vacuum graviton noise $S_{hh}^{\text{vac}}$**, and **quarter-wave causal gating** on two parallel $m = 10^{-14}\text{ kg}$ diamond-NV Stern-Gerlach interferometers ($\Delta x = 100\,\mu\text{m}$, $d = 250\,\mu\text{m}$, $T = 2.5\text{ s}$, $\Gamma_{\text{env}} = 0.01\text{ s}^{-1}$, $\Delta\phi_{\text{BMV}} = 0.2411\text{ rad}$; [`calc_protocol_e5_dual_bmv`](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py#L348-L441)):

| Observable | KTM / Oppenheim Stochastic Classical | Orlov RVPC (Core-Sourced Acoustic) | `BHHTC` / TTHO / BTHAT / VTFT (Graviton-Free Coherent) | Quantized Spin-2 Graviton QGEM |
| :--- | :---: | :---: | :---: | :---: |
| **1. Single-Arm Marginal Visibility $V_1(2.5\text{ s})$** | `0.8645` *(monotonic decay)* | **`0.9682`** *(oscillates & revives!)* | **`0.9682`** *(oscillates & revives!)* | **`0.9682`** *(oscillates & revives!)* |
| **2. Joint Witness $\mathcal{W}_{\text{BMV}} = \langle X'X'\rangle + \|\langle ZY'\rangle\|$** | `0.7474` ($\le 1$, `SEP`) | **`0.9375` ($\le 1$, `SEP`!)** | **`1.0685` ($> 1$, `ENT`!)** | **`1.0685` ($> 1$, `ENT`!)** |
| **3. Squeezed Vacuum Graviton Noise $S_{hh}^{\text{vac}}$** | Classical diffusion $> 0$ | **`0` (exact)** | **`0` (exact)** | **`> 0` ($G\hbar\omega/c^5$)** |
| **4. Quarter-Wave Gate ($\omega d/c = \pi/2$, $f_{\text{QW}}=\frac{c}{4d}$)** | Classical lag | Retarded acoustic | **Real standing Fokker $\cos(\frac{\omega d}{c})=0$** | Complex retarded radiation damping |

- **Exact Run-Time & Error Budget:**
  - Achieving $\Gamma_{\text{env}} \le 0.01\text{ s}^{-1}$ requires $P < 5\times 10^{-16}\text{ mbar}$ cryopumped chamber, $T_{\text{int}} < 0.15\text{ K}$ internal diamond phonon temperature, and a $1\,\mu\text{m}$ gold-coated SiN Casimir/patch-potential conducting shield centered between the two arms (suppressing Casimir + dipole force phase below $0.004\text{ rad} \ll 0.241\text{ rad}$).
  - **$11,518\text{ drops}$** ($5,759$ in $X'X'$ and $5,759$ in $ZY'$, taking **$8.0\text{ days}$** at a $60\text{ s}$ optical-cooling/launch cycle) establishes **$\mathcal{W}_{\text{BMV}} > 1.0000$ at $5.0\sigma$**, while **$8,062\text{ drops}$ ($5.6\text{ days}$)** separates coherent entanglement (`1.0685`) from Orlov's separable acoustic oscillation (`0.9375`) at **$8.0\sigma$**!

---

## Protocols E6 & E7 (Flagship Space — 2031–2033, Cost $\sim\$180\text{M}$): The `JANUS-SADDLE` Cislunar $258,809\text{ km}$ Gravitational Saddle-Point Mission

### 6.1 Astrodynamics & The 4-Body Lunar Saddle-Shift Discovery
As proven in [00_pi_seed_evaluation.md](file:///c:/Projects/Discovery/round2_crucible/00_pi_seed_evaluation.md) and [r1_pi_seed_crucible_test.py](file:///c:/Projects/Discovery/simulations/r1_pi_seed_crucible_test.py), free-fall in low-Earth orbit or at Sun-Earth $L_2$ fails to unscreen Bose-Einstein horizon gravity because the background potential gradient $|\nabla\Phi_\odot| = 5.93\times 10^{-3}\text{ m/s}^2 = 4.9\times 10^7\,a_0$ triggers full External Field Effect (EFE) Boltzmann freeze-out (`1.0000x`). Only at a **true inertial gravitational saddle point** where $\mathbf{g}_{N,\odot} + \mathbf{g}_{N,\oplus} + \mathbf{g}_{N,\text{Moon}} + \mathbf{g}_{N,\text{MW}} = \mathbf{0}$ does the bare gravitational field enter $|\mathbf{g}_N| \ll a_0$.

Evaluating [`calc_protocols_e6_e7_cislunar_mission`](file:///c:/Projects/Discovery/simulations/r3_experimental_snr_calculator.py#L448-L539) reveals three decisive mission-design numbers:
1. **Pocket Geometry ($r_E = 258,809.4\text{ km}$, $67.3\%$ of Lunar distance):** Axial tidal gradient $T_{xx} = +4.598\times 10^{-11}\text{ s}^{-2}$ and transverse gradient $T_{\perp} = -2.299\times 10^{-11}\text{ s}^{-2}$ carve out an ellipsoidal MOND bubble ($|\mathbf{g}_{\text{obs}}| < a_0$) of semi-axes **$\pm 1.67\text{ m}\text{ (axial)} \times \pm 3.33\text{ m}\text{ (transverse)}$** ($3.34\text{ m} \times 6.66\text{ m}$ full pocket!).
2. **4-Body Lunar Saddle Tracking:** Because the Moon orbits at $384,400\text{ km}$, at lunar quadrature $g_{\text{Moon}} = 2.28\times 10^{-5}\text{ m/s}^2$. Because $\det T_{ij} \neq 0$, lunar + Galactic gravity **never destroys the null**—instead it smoothly translates the exact 3D saddle point $\mathbf{r}_{\text{null}}(t)$ by **$867.8\text{ km}$** along a deterministic JPL DE440 ephemeris curve! `JANUS-SADDLE` locks onto $\mathbf{r}_{\text{null}}(t)$ to $\pm 2\text{ cm}$ using star trackers, DSN range-rate, and real-time nulling of its onboard 3-axis cold-atom gravity gradiometer.
3. **Single ESPA-Grande MicroSat Bus ($80\text{ kg}$ Dry Mass, $126.7\text{ kg}$ Wet Mass):** Because $\mathbf{r}_{\text{null}}(t)$ lies closer to Earth than the centrifugal $L_1$ point, hovering with $\mathbf{r}_{\text{null}}(t)$ requires continuous non-inertial thrust $a_{\text{hover}} = 5.920\times 10^{-3}\text{ m/s}^2$ (**$474\text{ mN}$** on an $80\text{ kg}$ dry spacecraft), supplied by a flight-proven $5,000\text{ s}$ $I_{\text{sp}}$ gridded xenon ion stage (NEXT-C derivative powered by $12\text{ kW}$ roll-out ROSA arrays).

---

### 6.2 Protocol E6 (Days 1–3): Fast Chebyshev Tangent-Parabola BMV Mode (`2.54 kg` Xenon!)
During Days 1–3 ($\Delta v = 1.53\text{ km/s}$, consuming just **$2.54\text{ kg}$ of xenon**), the outer spacecraft hovers symmetrically around the internal drag-free BMV vacuum chamber while pairs of $m = 10^{-14}\text{ kg}$ nanodiamonds ($\Delta x = 100\,\mu\text{m}, d = 250\,\mu\text{m}$) execute free-fall **Chebyshev-optimal transverse tangent parabolas** $\delta r_\perp(t) = \frac{1}{2}a_{\text{hover}}[(t - T/2)^2 - T^2/16]$:

- **$T = 0.6\text{ s}$ Drop Mode:** Maximum excursion from the exact null is ONLY **$199.8\,\mu\text{m}$** ($0.20\text{ mm}$)!
  - **Standard QGEM & Vance VTFT:** $\Delta\phi = \mathbf{0.0579\text{ rad}}$ (`1.000x` — VTFT frozen to $1 - e^{-0.6/\tau_{\text{rel}}} = 1.3\times 10^{-17}$!).
  - **`BHHTC` / BTHAT / TTHO:** $\Delta\phi = \mathbf{9.25\text{ rad}}$ (**`159.8x` integrated phase boost!**), reaching **$130.0\sigma$ phase discrimination in just $200\text{ drops}$ ($3.3\text{ hours}$)**!
- **$T = 2.5\text{ s}$ Drop Mode:** Maximum excursion is **$3.47\text{ mm}$** (well inside the $\pm 3,330\text{ mm}$ pocket!), yielding $\Delta\phi = \mathbf{17.03\text{ rad}}$ (**`70.6x` boost** vs. Newton `0.2411 rad`).
- **Breakthrough Hardware De-Risking ($10\times$ Lighter Mass Threshold):** Even if terrestrial labs struggle to prepare $10^{-14}\text{ kg}$ superpositions, at the cislunar saddle a **$10\times$ lighter $m = 10^{-15}\text{ kg}$ nanoparticle** achieves $\Delta\phi_{\text{saddle}}(2.5\text{ s}) = \mathbf{0.170\text{ rad}}$ (comparable to full-scale $10^{-14}\text{ kg}$ Earth BMV!)—turning `JANUS-SADDLE` into the easiest place in the inner Solar System to witness quantum gravity! *(Follow-on outer-planet rideshare to the Sun-Jupiter saddle, $\pm 3.0\text{ km}$ bubble, reaches **`1,559x` boost**!)*

---

### 6.3 Protocol E7 (Days 4–45): 41.1-Day Station-Kept Squeezed BEC Gradiometer Secular-Drift Mode
What if Protocol E6 measures `1.0000x` (`no fast saddle boost`)? That outcome eliminates fast-constraint `BHHTC`/TTHO/BTHAT, leaving a direct showdown between **Standard $\Lambda\text{CDM}$ + GR** and **Dr. Vance's VTFT** ($\tau_{\text{rel}} = 1.50\text{ Gyr}$ viscoelastic memory)!

Without changing orbit, `JANUS-SADDLE` engages continuous ion station-keeping for **$41.1\text{ days}$** ($\Delta v_{\text{tot}} = 22.54\text{ km/s}$, requiring **$46.7\text{ kg}$ total xenon** $\implies \mathbf{126.7\text{ kg}}$ total wet mass) while operating its symmetric $L_{\text{grad}} = 3.0\text{ m}$ ($r = \pm 1.50\text{ m}$ axial) spin-squeezed $^{87}\text{Rb}$ Bose-Einstein Condensate (BEC) differential atom-interferometer gradiometer ($S_{aa}^{1/2} = 1.0\times 10^{-18}\text{ m s}^{-2}\text{ Hz}^{-1/2}$; common-mode ion-thruster vibration rejected by $> 140\text{ dB}$ via symmetric dual-cloud Bragg diffraction along a single shared retro-reflecting optical cavity):
- **Equilibrium RAR Differential Excess Across $\pm 1.50\text{ m}$:** $\Delta a_{\text{eq}} = \mathbf{1.227\times 10^{-10}\text{ m/s}^2}$.
- **VTFT Secular Viscoelastic Build-Up Rate:** $\dot{a}_{\text{drift}} = \Delta a_{\text{eq}} / \tau_{\text{rel}} = \mathbf{2.592\times 10^{-27}\text{ m s}^{-3}}$ (vs. **identically $0$** in GR / $\Lambda\text{CDM}$, and **static constant** in instantaneous MOND).
- **Exact Cramér-Rao Matched-Filter Dwell Time:** Using $\sigma(\dot{a}) = \sqrt{12}\,S_{aa}^{1/2}\,T^{-3/2}$, `JANUS-SADDLE` reaches **$5.0\sigma$ detection of $\dot{a}_{\text{drift}}$ in $41.1\text{ days}$** (or $190.6\text{ days}$ with a $10^{-17}\text{ m s}^{-2}\text{ Hz}^{-1/2}$ cryogenic optical cavity backup gradiometer; modulating spacecraft axial offset by $\pm 0.8\text{ m}$ every 10 days reverses/modulates the tidal imprint to reject any linear clock/laser drift!).

---

## Summary Conclusion

Together, Protocols **E1–E7** leave **zero unobservable philosophical shelter** for any foundational ontology—standard or unorthodox:
- **Within 30 days (`E1` + `E2a`)**, existing quantum cloud processors and SPARC/DESI catalogs test the **Stinespring-Petz Page Cliff** at $>45\sigma$ and lock the **$\frac{2}{\sqrt{3}}$ zero-parameter horizon scale $a_0 = \frac{cH_0}{\sqrt{3}\pi}$** to $0.08\sigma$.
- **Within 2–3 years (`E2b–d`, `E3`, `E4`)**, DESI DR3 + Euclid, Gaia DR4, a $70\text{ s}$ femtosecond ENZ double-slit run, and a $77\text{ min}$ levitated NV spin-echo sweep cleanly separate **Orlov's causal Compton wake**, **Vance's $(\eta-1)^{3/2}$ pinning cusp & $1.5\text{ Gyr}$ relaxation**, **Chen's bi-temporal rebound**, and **`BHHTC`'s cosmic-web snap-back**.
- **By 2033 (`E5` + `JANUS-SADDLE` `E6/E7`)**, dual-readout tabletop BMV and a $126.7\text{ kg}$ cislunar saddle-point MicroSat deliver a decisive $>5\sigma\text{ to }130\sigma$ verdict on whether spacetime geometry is mediated by quantized spin-2 gravitons, classical acoustic solitons, viscoelastic chronon memory, or the graviton-free **Bi-Horizon Holonomic Tensor-Condensate**.
