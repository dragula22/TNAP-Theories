# Pre-Registered Blind Falsification Forecast: ESA `Gaia DR4` (December 2, 2026) & `BHEX` Photon Ring

- **Pre-Registration Date:** November 3, 2026 *(29 days prior to ESA `Gaia Data Release 4` on December 2, 2026)*
- **Permanent CERN Zenodo DOI:** [`10.5281/zenodo.23919217`](https://doi.org/10.5281/zenodo.23919217)
- **Author:** David Stoler — *Theoretically Not A Physicist (`@TNaPhysicist`)* | [`https://stoler.systems`](https://stoler.systems)
- **Repository:** [`https://github.com/dragula22/TNAP-Theories`](https://github.com/dragula22/TNAP-Theories)
- **Deterministic Reproduction Script:** [`run_gaia_dr4_and_bhex_preregistration.py`](run_gaia_dr4_and_bhex_preregistration.py)
- **Machine-Readable Manifest:** [`preregistered_numbers_2026_11.json`](preregistered_numbers_2026_11.json)
- **Canonical Payload `SHA-256`:** `fa1f5cc50885f1de71fde71201a9320d6c071e44c586708207fb8fc3fe471328`

---

## Plain-English Summary (Why This Document Exists)

In physics, fitting data *after* a telescope catalog opens is easy; locking zero-knob numbers in public **before** the data opens—and stating upfront what result falsifies your model—is the gold standard of honest science.

On **December 2, 2026**, the European Space Agency (ESA) releases **`Gaia Data Release 4` (`DR4`)**, doubling the astrometric time baseline to 66 months for over two billion stars (and adding dedicated Non-Single-Star inner-triple vetoes). Looking further ahead, the **Black Hole Explorer (`BHEX`)** space-VLBI mission will measure the photon-ring diameter of **`M87*`** and **`Sgr A*`** to `<= 1%` precision.

This pre-registration locks **zero-free-parameter predictions** from the exploratory *Spacetime Weave* (`TNaP`) model across both experiments before `Gaia DR4` opens:

1. **Wide Binary Stars (`Gaia DR4`):** Twin stars orbiting more than `7,000 AU` apart experience internal gravity weaker than the cosmic horizon scale $a_0$. Smooth Cold Dark Matter (`Lambda-CDM`) predicts **`0.00%` orbital speed boost everywhere**. Our 3D conservative curl-free weave equation predicts:
   - **`+16.14%`** (`[+14.81% .. +16.60%]` across published Milky Way circular-speed measurements) at `15,000 AU` in our local `< 300 pc` Solar backyard;
   - A **`+1.71%` "Galactic Compass" directional split** right inside `< 300 pc` (`+17.08%` for pairs aligned with the Galactic Center–Anticenter axis vs. `+15.37%` perpendicular—a signature hidden triple stars cannot mimic); and
   - A **more-than-doubling Galactocentric environment step** across `Gaia DR4`'s bright-star window (`d <= 2.5 kpc`), climbing from **`+12.16%`** in the Inner Disk (`R = 6.8 kpc`) to **`+20.98%`** in the Outer Thick Disk (`R = 9.8 kpc, |z| = 1.2 kpc`) and **`+25.64%`** in the Lower Halo (`R = 10.5 kpc, |z| = 2.2 kpc`).
2. **Black-Hole Photon Rings (`BHEX`):** TNaP's exponential optical weave metric (`n(U) = exp(2U)`, `A(U) = exp(-2U)`) matches Einstein identically across every 1PN Solar System test ($\gamma = 1, \beta = 1$), but diverges at 2PN strong-field order—predicting a non-spinning photon-ring shadow radius of **$2e\,r_g = 5.4366\,r_g$** vs. General Relativity's **$3\sqrt{3}\,r_g = 5.1962\,r_g$** (**`+4.63%` wider**, and `+4.63%` wider than Kerr GR at every spin $a_*$).

---

## 1. Locked Zero-Free-Parameter Equations

No tunable halo parameters, screening radii, or exponent powers are permitted. Every number in [`preregistered_numbers_2026_11.json`](preregistered_numbers_2026_11.json) follows deterministically from:

1. **Cosmic Horizon Acceleration Scale:**
   $$a_0 = \frac{c H_0}{\sqrt{3}\pi} = 1.202712 \times 10^{-10}\text{ m/s}^2 \quad (\text{Planck 2018 Paper VI } H_0 = 67.36\text{ km/s/Mpc})$$
   *(Using `Astropy Planck18` $H_0 = 67.66\text{ km/s/Mpc}$ gives $a_0 = 1.208069 \times 10^{-10}\text{ m/s}^2$, shifting boosts by $< 0.08\%$; the local `SH0ES` $H_0 = 73.04\text{ km/s/Mpc}$ variant gives $a_0 = 1.304136 \times 10^{-10}\text{ m/s}^2$, explicitly bracketed below.)*

2. **Classical Wave-Unruh / Bose–Einstein Horizon Interpolation:**
   $$\nu(y) = \frac{1}{1 - \exp\!\left(-\sqrt{y}\right)}, \qquad y \equiv \frac{|\mathbf{g}_N|}{a_0}$$
   *(Inside the inner Solar System, $\sqrt{y} \gg 1$ screens deviations to $10^{-3050}$ at Earth and $10^{-320}$ at Saturn; for $1\,M_\odot$, $g_N = a_0$ occurs at $r_{\text{crit}} = 7{,}021.8\text{ AU}$.)*

3. **3D Conservative Curl-Free Field Equation (Exact Newton's Third Law):**
   $$\nabla^2 \Phi_{\text{eff}} = -\nabla \cdot \left[\nu\!\left(\frac{|\mathbf{g}_{N,\text{bin}} + \mathbf{g}_{N,\text{MW}}|}{a_0}\right)\left(\mathbf{g}_{N,\text{bin}} + \mathbf{g}_{N,\text{MW}}\right)\right], \qquad \mathbf{g}_{\text{eff}} = -\nabla \Phi_{\text{eff}}$$
   - **Self-Consistent Milky Way Baryonic Calibration:** Rather than guessing the Milky Way's external Newtonian field $y_{N,\text{MW}} = g_{N,\text{MW}}/a_0$, QUMOND fixes it uniquely from the directly measured Galactic centripetal acceleration $g_{\text{obs,MW}} = V_c^2 / R_0$ via $y_{N,\text{MW}}\,\nu(y_{N,\text{MW}})\,a_0 = g_{\text{obs,MW}}$. For standard `GRAVITY + McMillan (2017)` ($R_0 = 8.178\text{ kpc}$, $V_c = 232.8\text{ km/s}$, $g_{\text{obs,MW}} = 2.148 \times 10^{-10}\text{ m/s}^2$), this locks **$y_{N,\odot} = 1.1843$**.
   - **Two-Body Momentum Conservation:** Computed via Milgrom (2010, *Phys. Rev. D* 81, 084007) Plummer-integrated two-body forces with isolated single-star self-fields subtracted identically (`112³` FFT, converged to `< 0.2%`).

4. **Exponential Optical Weave Metric (Strong-Field `BHEX` Test):**
   $$ds^2 = -e^{-2U} c^2 dt^2 + e^{+2U}\left(dr^2 + r^2 d\Omega^2\right), \qquad U = \frac{GM}{r c^2} = \frac{r_g}{r}$$

---

## 2. Prediction Suite I — ESA `Gaia DR4` Wide Binaries

### Test 1A: Local Solar-Neighborhood Separation Curve (`d <= 300 pc`, `0.8 + 0.8 M_sun`, `SNR ~ 56/pair`)

| Separation $s$ (`AU`) | `Lambda-CDM` (Smooth Dark Matter) | **Exact 3D `TNaP` Orbital Speed Boost** | Physical Regime |
| :---: | :---: | :---: | :--- |
| `1,000 AU` | `0.00%` | **`0.00%`** *(`-0.07%` grid noise)* | Newtonian calibration baseline (`500–2,000 AU`) |
| `2,000 AU` | `0.00%` | **`+0.25%`** | Inner campfire-screened regime |
| `3,500 AU` | `0.00%` | **`+2.37%`** | Onset of horizon transition |
| `5,000 AU` | `0.00%` | **`+5.75%`** | Mid-transition ramp |
| `7,000 AU` | `0.00%` | **`+10.31%`** | Crossing $r_{\text{crit}} = 7{,}021.8\text{ AU}$ knee |
| `10,000 AU` | `0.00%` | **`+14.48%`** | Entering Milky Way External-Field plateau |
| **`15,000 AU`** | **`0.00%`** | **`+16.14%`** | **Primary Solar-Neighborhood plateau** |
| `20,000 AU` | `0.00%` | **`+16.44%`** | Asymptotic EFE ceiling |

* **Published Milky Way $V_c$ / $H_0$ Sensitivity Bracket at `15,000 AU`:**
  - `Klioner et al. (2021)` Gaia EDR3 quasar aberration ($g_{\text{obs}} = 2.32 \times 10^{-10}\text{ m/s}^2$, $y_N = 1.3166$): **`+14.81%`**
  - `GRAVITY + McMillan (2017)` primary standard ($R_0 = 8.178\text{ kpc}, V_c = 232.8\text{ km/s}$, $y_N = 1.1843$): **`+16.14%`**
  - `Eilers et al. (2019)` ($R_0 = 8.122\text{ kpc}, V_c = 229.0\text{ km/s}$, $y_N = 1.1423$): **`+16.60%`**
  - `SH0ES` local $H_0 = 73.04\text{ km/s/Mpc}$ variant: **`+17.69%`**

---

### Test 1B: The Local "Galactic Compass" Directional Anisotropy (`d <= 300 pc`, `s = 10,000–22,000 AU`)

Because the Milky Way pulls the Solar Neighborhood toward the Galactic Center (`Sagittarius A*`, $l = 0^\circ, b = 0^\circ$), the 3D curl-free QUMOND potential is directionally pre-stretched ($\Phi_{\text{eff}} \propto [1 + \frac{1}{2}\hat{\nu}_e \sin^2\theta]/r$). Unresolved inner third stars have **zero correlation** with Galactic coordinates $(l, b)$:

| Binary Axis Orientation Relative to Galactic Center | `Lambda-CDM` | **Exact 3D `TNaP` (`15,000 AU`)** |
| :--- | :---: | :---: |
| **Aligned with Galactic Center–Anticenter ($\theta \approx 0^\circ$, $|\cos\theta_{\text{GC}}| \ge 0.75$)** | `0.00%` | **`+17.08%`** |
| **Perpendicular to Galactic Center ($\theta \approx 90^\circ$, $|\cos\theta_{\text{GC}}| \le 0.35$)** | `0.00%` | **`+15.37%`** |
| **Directional Compass Split ($\Delta_{\text{aligned} - \text{perp}}$)** | **`0.00%`** | **`+1.71%`** |

---

### Test 1C: Reachable Galactocentric Environment Gradient (`d <= 2.5 kpc` Bright Subgiants & Giants)

*Observational Note Caught Prior to Registration:* At $|z| > 5\text{ kpc}$, faint solar-type dwarfs (`G ~ 18.7 mag`) suffer proper-motion uncertainties (`~2.7 km/s`) larger than their orbital speed (`0.34 km/s`, `SNR ~ 0.1`). Within **`d <= 2.5 kpc`**, bright F-subgiants and Red Clump / RGB giants (`G <= 14.2 mag`) retain `SNR = 3.5–12` per pair in `Gaia DR4` (66 months), allowing a clean multi-sigma stack across Milky Way environments:

| Galactocentric Environment Zone (`s = 15,000 AU`) | $g_{\text{obs,MW}}$ ($\text{m/s}^2$) | $y_{N,\text{MW}}$ | `Lambda-CDM` | **Exact 3D `TNaP` Boost** |
| :--- | :---: | :---: | :---: | :---: |
| **1. Inner Disk (`R = 6.8 kpc, \|z\| < 0.3 kpc, d ~ 1.4 kpc`)** | $2.75 \times 10^{-10}$ | `1.6548` | `0.00%` | **`+12.16%`** |
| **2. Solar Neighborhood (`R = 8.18 kpc, \|z\| < 0.2 kpc, d < 0.3 kpc`)** | $2.15 \times 10^{-10}$ | `1.1843` | `0.00%` | **`+16.14%`** |
| **3. Outer Thick Disk (`R = 9.8 kpc, \|z\| = 1.2 kpc, d ~ 2.0 kpc`)** | $1.66 \times 10^{-10}$ | `0.8231` | `0.00%` | **`+20.98%`** |
| **4. Reachable Lower Halo (`R = 10.5 kpc, \|z\| = 2.2 kpc, d ~ 2.5 kpc`)** | $1.32 \times 10^{-10}$ | `0.5876` | `0.00%` | **`+25.64%`** *(> 2x Inner Disk!)* |
| **5. Deep Halo Asymptote (`R = 11.0 kpc, \|z\| = 6.0 kpc`, Future `DR5`/RV)** | $0.82 \times 10^{-10}$ | `0.2802` | `0.00%` | **`+33.28%`** |

### Locked Day-One `Gaia DR4` Quality Cuts (No Post-Hoc Cut Tuning)
1. `parallax_over_error >= 20.0` on both components.
2. `ruwe <= 1.20` on both components.
3. `non_single_star == 0` (`Gaia DR4` NSS astrometric/spectroscopic/eclipsing inner-binary veto) plus RV-consistency veto where radial velocities exist.
4. Internal self-calibration against the **exact same sample's** `500–2,000 AU` Newtonian bin (`median(v_tilde)`).

---

## 3. Prediction Suite II — `BHEX` Strong-Field Black-Hole Photon Ring

Minimizing the optical path $R_{\text{opt}}(r) = r\,e^{2 r_g / r}$ yields a photon sphere at isotropic coordinate $r_{\text{ph}} = 2\,r_g$ ($U = 1/2$) and critical shadow impact parameter $b_{\text{crit}}^{\text{TNaP}} = 2e\,r_g = \mathbf{5.436564\,r_g}$, compared to Schwarzschild General Relativity $b_{\text{crit}}^{\text{GR}} = 3\sqrt{3}\,r_g = \mathbf{5.196152\,r_g}$ (**`+4.6267%` wider**).

Crucially, in General Relativity, adding Kerr spin $a_* \in (0, 1)$ **strictly shrinks** the curve-averaged photon-ring radius below $5.1962\,r_g$ at all inclinations—meaning **GR has a hard mathematical ceiling at $5.1962\,r_g$**:

| Black-Hole Spin $a_*$ | GR Mean Ring (Edge-On $90^\circ$) | GR Mean Ring (Face-On $0^\circ$) | **`TNaP` Weave (Edge-On $90^\circ$)** | **`TNaP` Weave (Face-On $0^\circ$)** |
| :---: | :---: | :---: | :---: | :---: |
| **`0.00`** | `5.1962 r_g` *(GR Ceiling)* | `5.1962 r_g` *(GR Ceiling)* | **`5.4366 r_g`** | **`5.4366 r_g`** |
| `0.30` | `5.1873 r_g` | `5.1697 r_g` | **`5.4273 r_g`** | **`5.4089 r_g`** |
| `0.50` | `5.1706 r_g` | `5.1205 r_g` | **`5.4099 r_g`** | **`5.3574 r_g`** |
| `0.70` | `5.1430 r_g` | `5.0401 r_g` | **`5.3810 r_g`** | **`5.2733 r_g`** |
| `0.90` | `5.0981 r_g` | `4.9161 r_g` | **`5.3339 r_g`** | **`5.1435 r_g`** |
| `0.94` | `5.0853 r_g` | `4.8837 r_g` | **`5.3206 r_g`** | **`5.1097 r_g`** |
| `0.998` | `5.0614 r_g` | `4.8304 r_g` | **`5.2956 r_g`** | **`5.0539 r_g`** |

*(Because `BHEX` independently constrains spin $a_*$ and inclination $i$ from the $n=1$ photon ring's centroid shift and D-shaped asymmetry—and `GRAVITY` independently locks $M/D$ for `Sgr A*` via the S2 star orbit to `< 0.4%`—spin degeneracy cannot mask the `+4.63%` offset.)*

---

## 4. Explicit Falsification Criteria ("What Kills TNaP")

1. **`Gaia DR4` Local Falsification:** If cleanly vetted (`RUWE <= 1.20`, `NSS == 0`) local wide binaries (`d <= 300 pc`, `10,000–22,000 AU`) return a median velocity boost consistent with **`0.0%` at `>= 3 sigma`** (specifically `< +4.0%`), TNaP's Unruh-horizon galactic mechanism is **falsified**.
2. **`Gaia DR4` Environment Falsification:** If a local wide-binary boost is detected, yet the Outer Thick Disk / Lower Halo (`R >= 9.5 kpc, |z| >= 1.0 kpc`) fails to rise above the Inner Disk (`R <= 7.3 kpc`) once statistical uncertainties reach `<= 2.5%` per bin, the External Field Effect prediction is **falsified**.
3. **`BHEX` Strong-Field Falsification:** If `BHEX` measures the $n=1$ photon-ring radius of `Sgr A*` or `M87*` within `1%` of General Relativity's Kerr prediction for the independently measured $(M/D, a_*, i)$ (ruling out a `+4.63%` excess at `>= 3 sigma`), the exponential optical weave metric $n(U) = \exp(2U)$ is **falsified**.

---

## 5. Honest Open Theoretical Items (Not Claimed Solved Here)

To keep our scientific ledger 100% transparent, locking these empirical predictions does **not** mean TNaP is a finished "Theory of Everything." Two major theoretical derivations remain open work:
1. **Micro-to-Macro Gravity Emergence:** While variational 3D Skyrme–Faddeev knots (`Q_H = +7, +9, -6`) hold together stably in 3D simulations, deriving both universal $1/r^2$ knot-knot attraction and `n(U) = exp(2U)` wave refraction directly from a single coupled knot + massless weave-tension action (rather than specifying the optical metric and horizon response separately) remains our primary theoretical frontier.
2. **Full Covariant CMB Perturbation Evolution:** Evolving acoustic perturbations self-consistently through pinned $SO(3)$ pleats across all `Planck` / `Simons Observatory` `TT, TE, EE` polarization spectra up to $\ell = 2500$.

---

## 6. Pre-`Gaia DR4` Calibration Addendum — November 5, 2026 (`WeaveForge v1.1.0`, 27 Days Before `DR4`)

> **Strict Archival Integrity:** Everything in Sections 1–5 above and [`preregistered_numbers_2026_11.json`](preregistered_numbers_2026_11.json) (`SHA-256: fa1f5cc50885f1de71fde71201a9320d6c071e44c586708207fb8fc3fe471328`) is preserved **100% untouched** as **Protocol `v1`**. On November 5, 2026—27 days before `Gaia DR4` opens—stress-testing [`WeaveForge v1.1.0`](https://github.com/dragula22/WeaveForge) (`110/110` tests, commit `9e03a30`) against **real ESA `Gaia DR3` wide binaries** and **spinning `GW150914` / `LVK O4` black-hole ringdown posteriors** yielded two major pre-`DR4` discoveries documented openly below:

1. **Real ESA `Gaia DR3` Dry Run (`6,322` Isolated Pairs) & Locked [`zenodo_v2_manifest.json`](zenodo_v2_manifest.json) (`SHA-256: a59beaae575cef9f7cad46f8ad7cb72a14d2fc422d8c5ba857ebded97b6c4b9c`):**
   - Running untouched **Protocol `v1`** on `6,322` real `Gaia DR3` isolated pairs exposed a severe real-data systematic: ~70% of faint M-dwarf wide companions ($G \approx 16\text{–}19$) lack Gaia RVS radial velocities, allowing unbound moving-group flybys ($\Delta v_{2\text{D}} \sim 2\text{–}5\text{ km/s}$, $\tilde{v} \sim 7\text{–}16$) to leak into the `15,000 AU` bin and inflate the raw boost to **`+84.96% ± 34.56%`**.
   - **Protocol `v2`** locks five parameter-free wide-binary systematics guards before `Gaia DR4` opens (`sigma_v_tilde_1d <= 0.25`, exact 3D spherical tangent-triad perspective rotation, 4th-order Wardle–Kronberg Ricean perpendicular debiasing, scale-invariant bound-core window `0 < v_tilde <= 2.60`, and inner `[500, 2,000] AU` hierarchical-triple forward calibration $\hat{f}_{\text{triple}} = 0.308$ subtracting `+1.65%` triple bias).
   - **Real `Gaia DR3` Baseline (`2,811` Clean Pairs, `77` Bound Wide):** Local `10k–22k AU` boost measures **`+0.97% ± 9.48%`** (`TNaP +16.29%` vs `Lambda-CDM 0.00%`, $\Delta\chi^2 = -2.41 \to$ **`INCONCLUSIVE`** at 34-month `DR3` precision, with only **`N_halo = 1`** clean Halo pair at `SNR <= 0.25`). Both `Protocol v1` and `Protocol v2` will be executed side-by-side on Day One of `Gaia DR4` (whose 66-month baseline cuts proper-motion noise by `~2.7x` and expands clean volume `~20x`).
2. **Prediction Suite II (`BHEX` Bare `exp(2U)`) Self-Falsified at `5.92σ` by Existing Spinning `LVK O4` Ringdown $\to$ Replaced by Zero-Knob Gibbons Spool (`07_tnap_gibbons_spool.toml`):**
   - We did **not** have to wait for `BHEX` to test the bare `n(U) = exp(2U)` metric in Section 3: confronting spinning `(2,2,0)` quasinormal ringdown modes against `GW150914` (`4.76σ` IMR) and hierarchical `LVK O3b/O4` (`5.92σ`) **falsifies bare `exp(2U)` (`+4.63%` shadow) today**, and proves a **Photon-Sphere No-Go ceiling** bounding any 1PN-exact ($\gamma = \beta = 1$) static shadow excess to **`<= +1.32%` (`2σ`) / `<= +2.28%` (`3σ`)** (even an interior-only $r < r_{\text{ph}}$ clamp leaves $\Delta f_{220} = -7.00\%$).
   - Replacing `exp(2U)` with Episode 1's projective **Gibbons maximum-tension saturation** $F_{\max} = c^4/(4G)$ (`A = ((1 - U/2)/(1 + U/2))²`, `n = ((1 + U/2)³)/(1 - U/2)`, exact $R_H = 2GM/c^2$, `0` added free knobs) **passes `GW150914` at `0.27σ` and `LVK O4` Row 8 at `0.33σ`**, collapsing the static `BHEX` shadow excess to **`+0.00%`** and shifting strong-field falsification to **post-merger Planck-spool gravitational-wave echoes**.
