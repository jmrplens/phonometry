<!--
  AUTO-GENERATED FILE - DO NOT EDIT BY HAND.
  Regenerate with `make conformance` (runs scripts/conformance_report.py).
  CI regenerates it on every pull request and fails the build if it drifts.
-->

> **Auto-generated conformance report - do not hand-edit.** Produced by
> `make conformance` from the library's own computations checked against the
> referenced standards. CI regenerates it on every pull request and fails if it
> is out of date, so edit the checks in `scripts/conformance_report.py`, not this
> file. Each row pins a standard and clause to its expected normative value and
> the value the library computes. Full standards list and methodology:
> [Theory](https://github.com/jmrplens/phonometry/blob/main/docs/theory.md) -
> [Why phonometry](https://github.com/jmrplens/phonometry/blob/main/docs/why-phonometry.md).

## Numerical conformance report

&#9989; **210/210 conformance checks pass** across 32 domains and 130 standards - filters class 1 - weightings within IEC 61672-1 class 1.

### Numerical validation - filters &amp; weightings

**IEC 61260-1:2014 class per filter architecture** (order 6, one-third-octave, 100 Hz-10 kHz, fs = 48 kHz). For each architecture the table shows, at its *binding* band, the measured relative attenuation and the class-1 limit it must clear, so the number and the range it must sit in are both visible. A positive margin means the acceptance limits are met with that much room.

| Architecture | Class verdict | Binding band | Measured rel. atten. | Class-1 limit | Margin cl.1 | Margin cl.2 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| butter | Class 1 (default) | 100 Hz | +0.00 dB | &ge; -0.40 dB | +0.400 dB | +0.600 dB |
| cheby1 | By design (passband ripple) | 6310 Hz | +0.19 dB | &ge; +1.44 dB | -1.246 dB | -0.837 dB |
| cheby2 | Class 1 | 100 Hz | +0.00 dB | &ge; -0.40 dB | +0.400 dB | +0.600 dB |
| ellip | By design (passband ripple) | 10000 Hz | +0.10 dB | &ge; +1.32 dB | -1.218 dB | -0.813 dB |
| bessel | By design (soft rolloff) | 100 Hz | +12.46 dB | &ge; +16.60 dB | -4.133 dB | -3.133 dB |

Only **Butterworth** (the library default) and **Chebyshev-II** are class-compliant architectures. Chebyshev-I and elliptic trade the mask for passband ripple, and Bessel for a maximally-flat group delay (soft rolloff); they cannot satisfy the IEC 61260-1 Class 1/2 attenuation mask by construction, so they are labelled *By design* - this is expected, not a failure or regression.

**Frequency-weighting conformance** (A/C: IEC 61672-1 Table 3; G: ISO 7196 A.3). The *max deviation from nominal* is informational (it falls at a frequency extreme where the tolerance is widest and asymmetric); compliance is judged at the *binding* frequency - the one with the least headroom - where the deviation, the applicable tolerance band and the headroom are shown together.

| Curve | fs | Max dev. from nominal (info) | Binding freq | Deviation there | Tolerance band | Headroom |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| A | 48 kHz | -0.902 dB @ 20000 Hz | 1000 Hz | +0.000 dB | [-0.70, +0.70] dB | +0.700 dB |
| A | 96 kHz | -0.515 dB @ 20000 Hz | 1000 Hz | +0.000 dB | [-0.70, +0.70] dB | +0.700 dB |
| C | 48 kHz | -0.935 dB @ 20000 Hz | 1000 Hz | +0.000 dB | [-0.70, +0.70] dB | +0.700 dB |
| G | 48 kHz | +0.047 dB @ 1 Hz | 1 Hz | +0.047 dB | [-1.00, +1.00] dB | +0.953 dB |

<details>
<summary>&#9989; <b>Filters &amp; weightings</b> — 100% (6/6)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61260-1:2014 Table 1 | Octave-band filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61260-1:2014 Table 1 | One-third-octave filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61260:1995 / ANSI S1.11-2004 Table 1 | Class 0 (strictest) octave-band filter (butterworth, fs=48 kHz) | class 0 | class 0 (margin +0.150 dB) | +0.150 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | A-weighting deviation vs class-1 limits (fs=48 kHz) | deviation within limits @ 1000 Hz | +0.000 dB in [-0.70, +0.70] dB | headroom +0.700 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | C-weighting deviation vs class-1 limits (fs=48 kHz) | deviation within limits @ 1000 Hz | +0.000 dB in [-0.70, +0.70] dB | headroom +0.700 dB | &#9989; |
| ISO 7196:1995 Table 2 / A.3 | G-weighting deviation vs +/-1 dB tolerance (fs=48 kHz) | deviation within limits @ 1 Hz | +0.047 dB in [-1.00, +1.00] dB | headroom +0.953 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Levels &amp; dosimetry</b> — 100% (6/6)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61672-1:2013 (Leq) | Leq of a 1 Pa 1 kHz sine | 90.97 dB (+/-0.05 dB) | 90.969 dB | -0.001 dB | &#9989; |
| IEC 61252:1995 (LEX,8h) | 8 h exposure to 90 dB(A) noise | 90 dB (+/-0.05 dB) | 90.008 dB | 0.008 dB | &#9989; |
| ISO 1996-1:2016 3.6.4 | Lden, constant 60 dB in day/evening/night | 66.3952 dB (+/-0 dB) | 66.3952 dB | 0 dB | &#9989; |
| ISO 1996-2:2007 Annex C.5 Example 1 | Tonal audibility ΔLta (Formula C.3), 4 kHz tone | 13.7 dB (+/-0.05 dB) | 13.66 dB | -0.044 dB | &#9989; |
| ISO 1996-2:2007 Annex C.5 Example 1 | Tonal adjustment Kt (Formulae C.4-C.6) | 6 dB (+/-0 dB) | 6 dB | 0 dB | &#9989; |
| ISO 1996-2:2017 Annex G.2 | Combined measurement uncertainty u = √(Σ(cj·uj)²) | 2.18 dB (+/-0.01 dB) | 2.18 dB | -0.002 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Room acoustics</b> — 100% (5/5)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| Sabine (W. C. Sabine, 1922) | Reverberation time T = k·V/A  (V=120 m³, S=158 m², α=0.2) | 0.611825 s (+/-0.000001 s) | 0.611825 s | 0 s | &#9989; |
| Everest, Master Handbook of Acoustics 4th ed, Fig. 7-22 | Sabine RT, worked Example 1 @ 1 kHz (untreated 23.3×16×10 ft room, SI) | 3.39 s (+/-0.02 s) | 3.402 s | 0.012 s | &#9989; |
| Eyring (Norris-Eyring, 1930) | Reverberation time T = k·V/(-S·ln(1-ᾱ))  (α=0.2) | 0.548369 s (+/-0.000001 s) | 0.548369 s | 0 s | &#9989; |
| Arau-Puchades (Acustica 65, 1988, Formula 18) | T (α=0.5/0.1/0.1 per wall pair, dims 8×5×3 m) | 0.812147 s (+/-0.000001 s) | 0.812147 s | 0 s | &#9989; |
| Model identity (uniform absorption) | Arau-Puchades ≡ Eyring when ᾱ is uniform | 0.548369 s (= Eyring) | 0.548369 s | 0 s | &#9989; |

</details>

<details>
<summary>&#9989; <b>Psychoacoustics</b> — 100% (10/10)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 532-1:2017 Annex B.2 | Zwicker loudness N, stationary test signal 1 | 83.2957 sone (+/-0.1%) | 83.2957 sone | 0 sone | &#9989; |
| ISO 532-1:2017 Annex B.5 | Time-varying loudness Nmax, technical signal 14 (aircraft, free field) | 22.6399 sone (+/-0.1%) | 22.6399 sone | 0 sone | &#9989; |
| ISO 532-1:2017 Annex B.5 | Time-varying loudness Nmax, technical signal 15 (vehicle interior, diffuse field) | 9.6059 sone (+/-0.1%) | 9.6059 sone | 0 sone | &#9989; |
| DIN 45692:2009 Clause 6 | Sharpness of the standard 1 kHz reference signal | 1 acum (+/-0 acum) | 1 acum | 0 acum | &#9989; |
| ISO 226:2023 Table B.1 | Equal-loudness contour, 60 phon @ 100 Hz | 78.5 dB SPL (+/-0.05 dB SPL) | 78.504 dB SPL | 0.004 dB SPL | &#9989; |
| ECMA-418-2:2025 Clause 5.1.8 | HMS loudness of a 1 kHz / 40 dB tone (c_N=0.0211964) | 1 sone_HMS (+/-0.03 sone_HMS) | 0.9958 sone_HMS | -0.004 sone_HMS | &#9989; |
| ECMA-418-2:2025 Clause 6.2.8 | HMS tonality of a 1 kHz / 40 dB tone (c_T=2.8758615) | 1 tu_HMS (+/-0.03 tu_HMS) | 0.9998 tu_HMS | 0 tu_HMS | &#9989; |
| ECMA-418-2:2025 Clause 7 | HMS roughness of a 1 kHz / 70 Hz / m=1 / 60 dB tone (c_R=0.0180685) | 1.0735 asper (+/-0.01 asper) [clean-room; standard target 1] | 1.0735 asper | 0 asper | &#9989; |
| ISO 532-2:2017 Clause 3.17 / Annex B.1 | Moore-Glasberg loudness of a 1 kHz / 40 dB tone (C=0.0617) | 1 sone (+/-0.01 sone) | 1.0001 sone | 0 sone | &#9989; |
| ISO 532-3:2023 Annex C.1 | Moore-Glasberg-Schlittenlacher peak LTL, steady 1 kHz / 40 dB | 1 sone (+/-0.02 sone) | 0.9996 sone | 0 sone | &#9989; |

</details>

<details>
<summary>&#9989; <b>Speech transmission (IEC 60268-16)</b> — 100% (2/2)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 60268-16:2020 A.2.2 | STI weighting-factor pair (500 Hz + 1 kHz bands) | 0.398 (+/-0.001) | 0.398 | 0 | &#9989; |
| IEC 60268-16:2020 A.3.1.2 | Uniform MTF m=0.5 maps to STI=0.5 | 0.5 (+/-0.01) | 0.5 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Intensity &amp; sound power</b> — 100% (4/4)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61043:1994 Clause 5 | Plane-wave intensity I = p^2 / (rho c) | 0.00238 W/m^2 (+/-1.5%) | 0.00239 W/m^2 | 0 W/m^2 | &#9989; |
| ISO 3744:2010 Eq. 18 | Monopole hemisphere recovers LW (r=4 m) | 95 dB (+/-0 dB) | 95 dB | 0 dB | &#9989; |
| ISO 9614-2:1996 Eq. 12 | Intensity scan recovers LW of an enclosed source | 90 dB (+/-0.000001 dB) | 90 dB | 0 dB | &#9989; |
| ISO 3741:2010 Eq. 20 | Reverberation-room method inverts to a known LW | 0 dB error | 0 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Room &amp; building acoustics</b> — 100% (42/42)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 3382-2:2008 5.3.3 | T30 from a synthetic exponential decay (T=1.0 s) | 1 s (+/-1%) | 1 s | 0 s | &#9989; |
| ISO 18233:2006 (swept-sine method) | Sweep deconvolution recovers a known IIR response | 0 dB in-band error (+/-0.1 dB) | 0.0006 dB | 0.001 dB | &#9989; |
| ISO 717-1 Annex C, Table C.1 | Weighted sound reduction index Rw (C;Ctr) | Rw 30 (C -2; Ctr -3) | Rw 30 (C -2; Ctr -3) | sum 31.8 dB | &#9989; |
| ISO 717-1:2020 Annex C, Table C.2 | Enlarged range 50-5000 Hz: Rw (C; Ctr; C50-5000; Ctr,50-5000) | Rw 30 (C -2; Ctr -3; C50-5000 -2; Ctr,50-5000 -4) | Rw 30 (C -2; Ctr -3; C50-5000 -2; Ctr,50-5000 -4) | exact | &#9989; |
| ISO 717-2 Annex C, Table C.1 | Weighted impact sound pressure level Ln,w (CI) | Ln,w 79 (CI -11; sum 28.0 dB) | Ln,w 79 (CI -11; sum 28.0 dB) | +0 dB | &#9989; |
| ISO 717-2 Annex C, Table C.1 (covered) | Weighted impact level of the floor WITH covering Ln,w (CI) | Ln,w 64 (CI -3; sum 30.0 dB) | Ln,w 64 (CI -3; sum 30.0 dB) | +0 dB | &#9989; |
| ISO 717-2 Annex C, Table C.2 | Floor-covering improvement ΔLw and CI,Δ (Formulae (2)/(A.4)) | ΔLw 15 dB; CI,Δ -9 dB (Table 4 reference floor) | ΔLw 15 dB; CI,Δ -9 dB | +0 dB | &#9989; |
| ISO 354:2003 Eq. 5/8 | Sabine inversion recovers absorption area | 9.212828 m^2 (+/-0 m^2) | 9.212828 m^2 | 0 m^2 | &#9989; |
| ISO 3382-3:2012 Clause 6.2 | Open-plan spatial decay rate D2,S (-6 dB/doubling) | 6 dB (+/-0 dB) | 6 dB | 0 dB | &#9989; |
| ISO 16283-3:2016 Clause 3.12 | Facade R'45 isolates the -1.5 dB incidence correction (S=A) | 38.5 dB (+/-0 dB) | 38.5 dB | 0 dB | &#9989; |
| ISO 10140-2:2010 Formula (2) | Lab airborne R on the ISO 717-1 reference shape -> Rw = 54 | Rw 54 dB | Rw 54 dB | +0 dB | &#9989; |
| ISO 10140-5:2010+A1 Annex B, Table B.1 | Reference elements end-to-end: printed Rw (C; Ctr) of all three | Rw(C;Ctr) = 53(-1;-5) / 52(-1;-5) / 33(-1;-2) | 53(-1;-5) / 52(-1;-5) / 33(-1;-2) | exact | &#9989; |
| ISO 10140-5:2010+A1 Annex C, Table C.1 | Reference floors end-to-end: printed Ln,t,r,0,w (CI) of both | Ln,t,r,0,w(CI) = 72(0) / 75(-3) | 72(0) / 75(-3) | exact | &#9989; |
| ISO 15186-1:2000 Formula (7) | Intensity RI on the ISO 717-1 reference shape -> RI,w = 30 | RI,w 30 dB (scalar anchor RI = 34 dB) | RI,w 30 dB (RI = 34 dB) | +0 dB | &#9989; |
| ISO 15186-1:2000 Annex B, Table B.1 | Adaptation term Kc: all 18 printed rows; (B.1) reduces to (B.2) | max abs(Kc - Table B.1) <= 0,05 dB (1 dp print) | 0.046 dB (B.1 vs B.2: 4.33e-04 dB) | 0.046 dB | &#9989; |
| ISO 10052:2021 Clause 3.6 | Survey R' applies the V/7,5 minimum-area rule | 26.197888 dB (+/-0 dB) | 26.197888 dB | 0 dB | &#9989; |
| ISO 10052:2021 Clause 3.16 | Service-equipment LXY is the 3-position energy average | 32.823329 dB (+/-0 dB) | 32.823329 dB | 0 dB | &#9989; |
| ISO 10052:2021 Table 4 | Reverberation-index estimate (35 <= V < 60, type g) | k = [4.5, 5.0, 5.5, 5.5, 5.5] dB | k = [4.5, 5.0, 5.5, 5.5, 5.5] dB | exact | &#9989; |
| ISO 717-2:2020 Table 4 / Clause 5.2 | Reference-floor weighted level Ln,r,0,w and CI (ISO 16251-1 ΔLw anchor) | Ln,r,0,w = 78 dB, CI = -11 dB | Ln,r,0,w = 78 dB, CI = -11 dB | exact | &#9989; |
| ISO 16251-1:2014 / ISO 717-2 Formula (2) | Floor-covering ΔLw: zero improvement gives ΔLw = 0 | ΔLw = 0 dB (ΔL = 0 -> Ln,r = Ln,r,0) | ΔLw = 0 dB | exact | &#9989; |
| ISO 10848-1:2006 Formula (14) | Flanking Kij (simplified) matches closed form | Kij = 1.9897 dB | Kij = 1.9897 dB | exact | &#9989; |
| ISO 10848-1:2006 Formula (12) | Flanking equivalent absorption length aj at f_ref | aj = 1.2661 m | aj = 1.2661 m | exact | &#9989; |
| ISO 10848-1:2006 Clause 7.3.1 | Flanking total loss factor η = 2,2/(f·Ts) | η = 0.0044 | η = 0.0044 | exact | &#9989; |
| EN 29052-1:1992 Formula 4 | Apparent dynamic stiffness s't = 4π²·m't·fr²  (m't=200 kg/m², fr=25 Hz) | 4.934802 MN/m³ (+/-0.000001 MN/m³) | 4.934802 MN/m³ | 0 MN/m³ | &#9989; |
| EN 29052-1:1992 clause 8.2 NOTE | Enclosed-gas stiffness s'a·d = 111 MN·mm/m³ (p₀=0,1 MPa, ε=0,9) | 5.55556 MN/m³ (+/-0.0001 MN/m³) | 5.55556 MN/m³ | 0 MN/m³ | &#9989; |
| EN 29052-1:1992 Formula 2 | Floating-floor natural frequency f0 = (1/2π)√(s'/m')  (s'=10 MN/m³, m'=100 kg/m²) | 50.32921 Hz (+/-0 Hz) | 50.32921 Hz | 0 Hz | &#9989; |
| ISO 7626-1:2011 Annex A | SDOF driving-point mobility peak |Y(f0)| = 1/c  (c=5 N·s/m) | 0.2 m/(N·s) (+/-0.000001 m/(N·s)) | 0.2 m/(N·s) | 0 m/(N·s) | &#9989; |
| ISO 7626-1:2011 Annex A | SDOF static receptance H(0) = 1/k  (k=8000 N/m) | 0.000125 m/N (+/-0.0001%) | 0.000125 m/N | 0 m/N | &#9989; |
| ISO 7626-1:2011 Table 1 | FRF reciprocity: impedance × mobility = 1  (at 37 Hz) | 1 (= Z·Y) | 1 | 0 | &#9989; |
| ISO 10846-2:2008 3.17 | Transfer-stiffness level Lk = 20 lg(|k|/k0), k0 = 1 N/m  (|k| = 1 MN/m) | 120 dB (+/-0 dB) | 120 dB | 0 dB | &#9989; |
| ISO 10846-3:2002 Formula (1) | Indirect method k2,1 = -(2πf)²·m2·T  (f=500 Hz, m2=10 kg, T=0,01) | -986960.4 N/m (+/-0.1%) | -986960.4 N/m | 0 N/m | &#9989; |
| ISO 10846-1:2008 Table A.2 | FRF relation k = jω·Z at 250 Hz  (|k| recovered from impedance) | 1001249.2 N/m (+/-0.0001%) | 1001249.2 N/m | 0 N/m | &#9989; |
| ISO/TS 7849-1:2009 Formula (8) | Calibration L_v from â = 9,81 m/s² at 100 Hz  (standard's EXAMPLE) | 106.9 dB (+/-0.1 dB) | 106.9 dB | -0.02 dB | &#9989; |
| ISO/TS 7849-2:2009 Formula (15) | L_W from L_v via measured radiation factor = 10 lg(P/P0)  (round-trip) | 84.771 dB (+/-0 dB) | 84.771 dB | 0 dB | &#9989; |
| ISO/TS 7849-1:2009 Formula (12) | Impedance term: L_W − L_v = 10 lg(411/400) at ε = 1, S = S0 | 0.1178 dB (+/-0 dB) | 0.1178 dB | 0 dB | &#9989; |
| EN 15657:2018 Formula (14) | Reception-plate L_Ws = resonant-plate power P = ωη(mS)⟨v²⟩  (round-trip) | 55.545 dB (+/-0 dB) | 55.545 dB | 0 dB | &#9989; |
| EN 15657:2018 Formula (13) | Plate loss factor η = 2,2/(f·Ts) at 1 kHz, Ts = 0,3 s | 0.0073 (+/-0) | 0.0073 | 0 | &#9989; |
| EN 15657:2018 Formulae (15)/(17) + EN 12354-5 Annex I.3 | Source conversion chain reproduces Table I.8 (wall, installed) | max abs(L_Ws,inst - Table I.8) <= 0,15 dB | 0.055 dB | 0.055 dB | &#9989; |
| ISO 9611:1996 eq. (9) | Mean free velocity level (energy mean, v0 = 5e-8 m/s) | 72.3017 dB (+/-0 dB) | 72.3017 dB | 0 dB | &#9989; |
| EN 12354-5:2009 Formula (19b/19c) | Coupling term → force-source limit 10 lg(|Ys|/Re{Yi}) as |Ys|≫|Yi| | 40 dB (+/-0.01 dB) | 40.001 dB | 0.001 dB | &#9989; |
| EN 12354-5:2009 Annex I.3, Table I.9 | Flushing cistern: four paths + Formula (17) total -> 29 dB(A) | max path/total dev <= 0.15 dB; total 29 dB(A) | 0.055 dB; 29.3 dB(A) | 0.055 dB | &#9989; |
| EN 12354-5:2009 Annex I.2, Table I.6a | Whirlpool floor component: mobility correction + path 11 | max abs(dev vs Table I.6a) <= 0,15 dB | 0.1 dB | 0.1 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Building prediction &amp; uncertainty</b> — 100% (15/15)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| EN 12354-1:2000 Annex H.3 | Airborne prediction R'w (direct + 12 flanking paths) | R'w 52 dB (13 paths) | R'w 52 dB (13 paths, 52.17) | +0.17 dB | &#9989; |
| EN 12354-1:2000 Annex H.3 (paths) | All 12 printed flanking-path values Rij,w | max abs(Rij,w - printed) <= 0,05 dB | 0.042 dB | 0.042 dB | &#9989; |
| EN 12354-1:2000 Formula (5b) / Annex H.3 | DnT,w closure from R'w (both H.3 examples -> 54 dB) | DnT,w 54 dB (printed 53,8/54,3) | DnT,w 53.63 / 54.13 dB | -0.17 dB vs printed | &#9989; |
| EN 12354-2:2000 Annex E.3 | Impact prediction L'n,w = Ln,w,eq - dLw + K | 45 dB (+/-0 dB) | 45 dB | 0 dB | &#9989; |
| EN 12354-2:2000 Formula (3) / Annex E.3 | Standardized impact level L'nT,w (exact 0,032 V form -> 43 dB) | L'nT,w 43 dB (exact 42,96; E.3 prints 42,8) | L'nT,w 42.96 dB | -0.001 dB | &#9989; |
| EN 12354-3:2000 Annex F | Facade airborne prediction (R'tr,s,w / D2m,nT,w single numbers) | R'tr,s,w 31 (Ctr -3); D2m,nT,w 33 dB | R'tr,s,w 31 (Ctr -3); D2m,nT,w 33 dB | 0 | &#9989; |
| EN 12354-4:2000 Annex G / Formula (2) | Radiated LW of a wall+door segment (side 1, low bands) | LW 63/125 Hz [59.8, 61.2] dB (+/-0.1) | LW [59.8, 61.2] dB | 0.038 dB | &#9989; |
| EN 12354-4:2000 Annex E / Table G.9 | Exterior level from a finite radiating side (side 1, d = 5 m) | 36.6 dB (+/-0.05 dB) | 36.597 dB | -0.003 dB | &#9989; |
| ISO 12999-1:2020 Table 2 | Airborne band uncertainty, situation A @ 1 kHz | 1.8 dB (+/-0 dB) | 1.8 dB | 0 dB | &#9989; |
| ISO 12999-1:2020 Annex B, Table B.2 | One-decimal single numbers Rw / Rw+C50-5000 / Rw+Ctr,50-5000 | 57.4 / 56.4 / 51.1 dB | 57.4 / 56.4 / 51.1 dB | +0.00 dB | &#9989; |
| ISO 12999-1:2020 Annex B, Formulae (B.2)/(B.6) | Single-number uncertainties (uncorrelated 0,6/0,8; correlated u(Rw) 1,9) | u_uncorr 0.6 / 0.8 dB; u_corr(Rw) 1.9 dB | 0.60 / 0.79 dB; 1.90 dB | -0.00 dB | &#9989; |
| ISO 12999-1:2020 Clause 8 / Table 8 | Expanded uncertainty U = 1.96 u (95 % two-sided, Rw sit. A) | 2.352 dB (+/-0 dB) | 2.352 dB | 0 dB | &#9989; |
| ISO 12999-2:2020 Table 4 / Formula (1) | Absorption coefficient +/-U (k=2), reproducibility, 20 x 1/3-oct bands | U(k=2) = [0.33, 0.26, 0.22, 0.17, 0.13, 0.11, 0.09, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.09, 0.09, 0.09, 0.1, 0.11, 0.13, 0.16] | U(k=2) = [0.33, 0.26, 0.22, 0.17, 0.13, 0.11, 0.09, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.09, 0.09, 0.09, 0.1, 0.11, 0.13, 0.16] | exact | &#9989; |
| ISO 12999-2:2020 Table 5 / Formula (4) | Practical coefficient +/-U (k=2), reproducibility, 5 octave bands | U(k=2) = [0.09, 0.08, 0.08, 0.08, 0.1] | U(k=2) = [0.09, 0.08, 0.08, 0.08, 0.1] | exact | &#9989; |
| ISO 12999-2:2020 Clause 7, Examples 1/2 | Single-number U (k=2): alpha_w and DLalpha,NRD | alpha_w +/-0.07, DLalpha +/-1.6 dB | alpha_w +/-0.07, DLalpha +/-1.6 dB | exact | &#9989; |

</details>

<details>
<summary>&#9989; <b>Outdoor propagation &amp; occupational exposure</b> — 100% (9/9)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 9613-1:1993 Table 1 | Air attenuation @ 10 degC, 70 %, 1 kHz | 3.66 dB/km (+/-0.01 dB/km) | 3.658 dB/km | -0.002 dB/km | &#9989; |
| ISO 9613-1:1993 Table 1 | Air attenuation @ 0 degC, 20 %, 2 kHz | 34.6 dB/km (+/-0.1 dB/km) | 34.64 dB/km | 0.04 dB/km | &#9989; |
| ISO 9613-2:1996 Eq. (7) | Geometrical divergence Adiv = 20 lg(d/d0) + 11 at 100 m | 51 dB (+/-0 dB) | 51 dB | 0 dB | &#9989; |
| ISO 9613-2:1996 Table 3 | Ground b'(0) porous limit -> Agr(250 Hz) = 2(-1.5 + 10.1) | 17.2 dB (+/-0 dB) | 17.2 dB | 0 dB | &#9989; |
| ISO 9613-2:1996 clause 7.4 | Single-edge diffraction saturates at the 20 dB cap | 20 dB (+/-0 dB) | 20 dB | 0 dB | &#9989; |
| ISO 9613-2:1996 clause 7.4 | Double-edge diffraction saturates at the 25 dB cap | 25 dB (+/-0 dB) | 25 dB | 0 dB | &#9989; |
| ISO 9612:2009 Annex D | Task-based LEX,8h + U (welder day, case a) | LEX,8h 84.3; U 2.7 dB | LEX,8h 84.3; U 2.7 dB | -0.01; +0.02 dB | &#9989; |
| ISO 9612:2009 Annex E | Job-based LEX,8h + U (production line, 18 workers) | LEX,8h 88.1; U 3.8 dB | LEX,8h 88.2; U 3.8 dB | +0.06; -0.03 dB | &#9989; |
| ISO 9612:2009 Annex F | Full-day LEX,8h + U (forklift drivers) | LEX,8h 90.1; U 3.4 dB | LEX,8h 90.1; U 3.4 dB | +0.02; +0.03 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Materials: absorption, airflow &amp; impedance</b> — 100% (6/6)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 11654:1997 Annex A.1 | Weighted absorption alpha_w (no indicator) | 0.60 (class C, no indic.) | 0.60 (class C, '') | 0 | &#9989; |
| ISO 11654:1997 Annex A.2 | Weighted absorption alpha_w with M indicator | 0.60(M) | 0.60(M) | 0 | &#9989; |
| ISO 9053-2:2020 Annex A.3 | Thermal boundary-layer thickness b | 0.00183 m (+/-0.00001 m) | 0.00183 m | 0 m | &#9989; |
| ISO 9053-2:2020 Annex A.3 | Effective ratio of specific heats kappa' | 1.37 (+/-0.001) | 1.37 | 0 | &#9989; |
| ISO 10534-1:1996 Eqs (9)/(13)/(14) | Absorption from standing-wave ratio s=3 | alpha 0.75 (+/-0), \|r\| 0.5 | alpha 0.75, \|r\| 0.5000 | 0 | &#9989; |
| ISO 10534-2 Eq. (17) / Annex D | Two-microphone round trip recovers a known reflection factor | abs(r - (0.3-0.4j)) = 0 (identity, +/-1e-9) | 0 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Scattering &amp; diffusion (ISO 17497)</b> — 100% (5/5)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 17497-1:2004 Eq (2) | Reference speed of sound at 20 C | 343.2 m/s (+/-0 m/s) | 343.2 m/s | 0 m/s | &#9989; |
| ISO 17497-1:2004 Eqs (1)/(4)/(5) | Scattering coefficient (synthetic chain) | 0.0931 (+/-0) | 0.0931 | 0 | &#9989; |
| ISO 17497-1:2004 Annex A.5 | Expanded uncertainty of scattering coefficient | 0.02971 (+/-0) | 0.02971 | 0 | &#9989; |
| ISO 17497-2:2012 Formula (5) | Diffusion coefficient (autocorrelation) | 0.7367 (+/-0) | 0.7367 | 0 | &#9989; |
| ISO 17497-2:2012 Formula (8) | Zenith area factor (radians convention) | 1.57105 (+/-0) | 1.57105 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>In-situ road absorption (ISO 13472)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 13472-1:2002 Clause 4.2 | Geometrical-spreading factor Kr | 0.6667 (+/-0) | 0.6667 | 0 | &#9989; |
| ISO 13472-1:2002 Annex A | Maximum-sampled-area radius | 1.3425 m (+/-0 m) | 1.3425 m | 0 m | &#9989; |
| ISO 13472-2:2010 Clause 5.4.1 | Spot-tube upper usable frequency f_u | 1989.4 Hz (+/-0.1 Hz) | 1989.4 Hz | 0 Hz | &#9989; |

</details>

<details>
<summary>&#9989; <b>Precision sound power (ISO 3745 / 9614-3)</b> — 100% (4/4)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 3745:2012 Clause 10.5 EXAMPLE | Expanded uncertainty U (k=2) | 4.123 dB (+/-0.001 dB) | 4.123 dB | 0 dB | &#9989; |
| ISO 3745:2012 Eq (11) | K1 background floor (6 dB edge band) | 1.2563 dB (+/-0.0001 dB) | 1.2563 dB | 0 dB | &#9989; |
| ISO 3745:2012 Eq (16) | Meteorological C1 at 23 C reference | -0.1282 dB (+/-0.0001 dB) | -0.1282 dB | 0 dB | &#9989; |
| ISO 9614-3:2002 Eqs (5)/(8)/(9) | Uniform-intensity LW recovery | 80 dB (+/-0 dB) | 80 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Human vibration (ISO 8041 / 2631 / 5349)</b> — 100% (7/7)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 8041-1:2017 Table B.8 | Wk design-goal factor at 6,31 Hz | 1.054 (+/-0.1%) | 1.0544 | 0 | &#9989; |
| ISO 8041-1:2017 Table B.9 | Wm design-goal factor at 1,585 Hz | 0.9342 (+/-0.1%) | 0.9342 | 0 | &#9989; |
| ISO 8041-1:2017 Table 1 | Wh factor at the 500 rad/s reference | 0.202 (+/-0.15%) | 0.202 | 0 | &#9989; |
| ISO 5349-2:2001 Example E.2.1 | Single-tool daily exposure A(8) | 4.1 m/s^2 (+/-0.05 m/s^2) | 4.14 m/s^2 | 0.037 m/s^2 | &#9989; |
| ISO 5349-2:2001 Example E.3 | Forestry three-task A(8) | 3.6 m/s^2 (+/-0.05 m/s^2) | 3.61 m/s^2 | 0.01 m/s^2 | &#9989; |
| ISO 5349-1:2001 Eq. (C.1) | VWF 10 % lifetime Dy at A(8)=7 | 4 yr (+/-0.1 yr) | 4.04 yr | 0.042 yr | &#9989; |
| Directive 2002/44/EC Art. 3 | HAV/WBV action & limit values | HAV 2.5/5.0, WBV 0.5/1.15 m/s^2 | HAV 2.5/5.0, WBV 0.5/1.15 m/s^2 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Speech intelligibility (ANSI S3.5-1997)</b> — 100% (4/4)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ANSI S3.5-1997 Table 3 | Band-importance function normalisation | 1 (+/-0) | 1 | 0 | &#9989; |
| ANSI S3.5-1997 clause 5.4 | Equivalent masking spectrum level at 200 Hz | -1.665 (+/-0.001) | -1.665 | 0 | &#9989; |
| ANSI S3.5-1997 clause 6 | SII, standard speech in quiet, normal hearing | 0.9958 (+/-0.0005) | 0.9958 | 0 | &#9989; |
| ANSI S3.5-1997 Table 3 | Loud-effort speech spectrum level at 1 kHz | 42.16 dB (+/-0 dB) | 42.16 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Impulsive-sound prominence (NT ACOU 112)</b> — 100% (2/2)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| NT ACOU 112:2002 Formula 1 | Predicted prominence, OR=1000 dB/s, LD=30 dB | 11.9542 (+/-0.0001) | 11.9542 | 0 | &#9989; |
| NT ACOU 112:2002 Formula 2 | Adjustment KI to LAeq at prominence P=10 | 9 dB (+/-0 dB) | 9 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Room noise (ANSI S12.2-2019)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ANSI S12.2-2019 Table 1 | NC-40 curve, tangency self-consistency | 40 (+/-0) | 40 | 0 | &#9989; |
| ANSI S12.2-2019 Table D.1 | RC-31 Mark II curve, 63 Hz level | 51 (+/-0) | 51 | 0 | &#9989; |
| ANSI S12.2-2019 clause D.4 | RC-35 curve, mid-frequency average LMF | 35 (+/-0) | 35 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Hearing threshold (ISO 7029 / ISO 389-7)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 7029:2017 Table 1 | Median threshold, male age 60 at 4 kHz | 20.209 dB (+/-0.001 dB) | 20.208 dB | 0 dB | &#9989; |
| ISO 7029:2017 Table 2 | Upper spread su, male age 60 at 1 kHz | 10.153 dB (+/-0.001 dB) | 10.153 dB | 0 dB | &#9989; |
| ISO 389-7:2006 Table 1 | Free-field reference threshold at 1 kHz | 2.4 dB (+/-0 dB) | 2.4 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Measurement uncertainty (GUM / Supplement 1)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO/IEC Guide 98-3-1 clause 9.2 | Combined uncertainty, additive model | 2 (+/-0) | 2 | 0 | &#9989; |
| ISO/IEC Guide 98-3 Table G.2 | Coverage factor, p=0.99, v=16 | 2.92 (+/-0.005) | 2.921 | 0.001 | &#9989; |
| ISO/IEC Guide 98-3 Annex G.4 | Welch-Satterthwaite effective dof | 40 (+/-0) | 40 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Noise-induced hearing loss (ISO 1999)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 1999:2013 Table D.2 | Median NIPTS, 4 kHz, 90 dB, 20 yr | 13 dB (+/-0.5 dB) | 12.9 dB | -0.057 dB | &#9989; |
| ISO 1999:2013 Table D.2 | Worst-10 % NIPTS, 4 kHz, 90 dB, 20 yr | 18 dB (+/-0.5 dB) | 17.8 dB | -0.239 dB | &#9989; |
| ISO 1999:2013 Table D.4 | Worst-10 % NIPTS, 3 kHz, 100 dB, 40 yr | 60 dB (+/-0.5 dB) | 59.8 dB | -0.172 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Multiple-shock whole-body vibration (ISO 2631-5)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 2631-5:2018 Formula 3 | Daily acceleration dose, 5 x 40 m/s2 peaks | 55.97 m/s2 (+/-0.01 m/s2) | 55.97 m/s2 | -0.002 m/s2 | &#9989; |
| ISO 2631-5:2018 Formula C.3 | Stress variable R, Annex C male example | 1.22 (+/-0.01) | 1.22 | 0 | &#9989; |
| ISO 2631-5:2018 Formula C.5 | Injury probability, Annex C male example | 0.37 (+/-0.01) | 0.37 | -0.003 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Sound absorption in enclosed spaces (EN 12354-6)</b> — 100% (2/2)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| EN 12354-6:2003 Formula 1 | Equivalent absorption area, Annex E bare room | 2.26 m2 (+/-0.01 m2) | 2.26 m2 | 0.003 m2 | &#9989; |
| EN 12354-6:2003 Formula 5 | Reverberation time, Annex E bare room | 2.1 s (+/-0.1 s) | 2.1 s | 0.003 s | &#9989; |

</details>

<details>
<summary>&#9989; <b>Prominent discrete tones (ECMA-418-1)</b> — 100% (2/2)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ECMA-418-1:2024 Clause 10 Formula (2) | Critical band at 1 kHz (f1,c / f2,c / dfc) | dfc 162.2 Hz (+/-0.05 Hz); edges 922.2-1084.4 Hz | dfc 162.22 Hz; edges 922.2-1084.4 Hz | 0.017 Hz | &#9989; |
| ECMA-418-1:2024 Clause 11.6 Formula (14) | Proximity spacing dfprox at 150 / 850 Hz | 23 Hz @ 150 Hz; 63.8 Hz @ 850 Hz (+/-0.5 Hz) | 23.0 Hz; 63.8 Hz | +0.004; +0.044 Hz | &#9989; |

</details>

<details>
<summary>&#9989; <b>Tonal audibility (ISO/PAS 20065)</b> — 100% (8/8)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO/PAS 20065:2016 Formulae (12)-(14) | Audibility at 137.3 Hz, Annex E spectrum 1 | 4.99 dB (+/-0.05 dB) | 5.01 dB | 0.022 dB | &#9989; |
| ISO/PAS 20065:2016 Formula (13) | Masking index av at 137.3 / 592.2 Hz | -2.02 dB @ 137.3 Hz; -2.4 dB @ 592.2 Hz (+/-0.005 dB) | -2.017 dB; -2.400 dB | +0.003; +0.000 dB | &#9989; |
| ISO/PAS 20065:2016 Formula (20) | Mean audibility of the five spectra, Annex E | 6.96 dB (+/-0.05 dB) | 6.98 dB | 0.018 dB | &#9989; |
| ISO/PAS 20065:2016 Formula (6) | Mean narrow-band level LS from spectrum, Table E.1 | 49.22 dB (+/-0.02 dB) | 49.22 dB | -0.001 dB | &#9989; |
| ISO/PAS 20065:2016 Formula (8) | Tone level LT from spectrum, Table E.1 | 67.96 dB (+/-0.02 dB) | 67.96 dB | -0.005 dB | &#9989; |
| ISO/PAS 20065:2016 Clause 5.3.8 | Tone detection over the spectrum, Table E.1 | tones at [118.4, 137.3, 158.8] Hz | tones at [118.4, 137.3, 158.8] Hz | exact | &#9989; |
| ISO/PAS 20065:2016 Formula (17) | Multi-tone FG combination, Table E.1 | 72.15 dB (+/-0.02 dB) | 72.15 dB | -0.002 dB | &#9989; |
| ISO/PAS 20065:2016 Formulae (18)/(19) | Two-tone separation fD (DIN 45681 Annex J), 137.3 / 212 Hz | fD(137.3)=24.09, fD(212)=21.0 Hz; Annex E pair combined | fD(137.3)=24.09, fD(212)=21.00 Hz; Annex E pair combined | exact | &#9989; |

</details>

<details>
<summary>&#9989; <b>Psychoacoustic annoyance &amp; fluctuation strength (Fastl &amp; Zwicker)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| Fastl & Zwicker Eqs (16.2)-(16.4) | Psychoacoustic annoyance, worked (N5,S,F,R) tuple | 30.8167 (+/-0.001) | 30.8167 | 0 | &#9989; |
| Fastl & Zwicker Eq (10.2) | Fluctuation strength of AM broadband noise (60 dB, m=1, 4 Hz) | 3.6943 vacil (+/-0.001 vacil) | 3.6943 vacil | 0 vacil | &#9989; |
| Fastl & Zwicker Ch. 10 / Osses et al. 2016 | Fluctuation-strength calibration: 1 kHz / 60 dB / m=1 / 4 Hz AM tone | 1 vacil (+/-0.05 vacil) | 1 vacil | 0 vacil | &#9989; |

</details>

<details>
<summary>&#9989; <b>Electroacoustics: distortion &amp; frequency response</b> — 100% (7/7)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 60268-3:2013 (14.12.2-3) | THD (rel. fundamental) of a synthetic 4-harmonic signal | 0.113578 (+/-0.0001) | 0.113578 | 0 | &#9989; |
| IEC 60268-3:2013 (14.12.5) | 2nd-order harmonic distortion d2 (rel. total) | 0.099361 (+/-0.0001) | 0.099361 | 0 | &#9989; |
| IEC 60268-3:2013 (14.12.7) | SMPTE modulation distortion of a known two-tone signal | 0.126491 (+/-0.0001) | 0.126491 | 0 | &#9989; |
| IEC 60268-3:2013 (14.12.8) | CCIF difference-frequency distortion (2nd order) of a two-tone signal | 0.06 (+/-0.0001) | 0.06 | 0 | &#9989; |
| IEC 60268-3:2013 (14.12.9) | DIM of the 15 kHz / 3.15 kHz signal (Table 2, 9 products) | 0.168819 (+/-0.0001) | 0.168819 | 0 | &#9989; |
| Bendat & Piersol, Random Data 4e | H1 recovers a known first-order IIR gain at 1 kHz | 0.8954 (+/-2%) | 0.8954 | 0 | &#9989; |
| Bendat & Piersol, Random Data 4e | Ordinary coherence = 1 for a noiseless LTI path | 1 (+/-0.001) | 1 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Underwater acoustics (ISO 18405/17208/18406)</b> — 100% (6/6)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 18405:2017 / ISO 18406 Formula 7 | Sound pressure level of a synthetic tone, dB re 1 µPa | 123.0103 (+/-0.0001) | 123.0103 | 0 | &#9989; |
| ISO 18405:2017 / ISO 18406 Formulae 3-4 | Sound exposure level of a 2 s tone, dB re 1 µPa²·s | 120 (+/-0.001) | 120 | 0 | &#9989; |
| ISO 18406:2017 (6.4.2.1.3) | Peak sound pressure level of a known waveform, dB re 1 µPa | 129.5424 (+/-0.0001) | 129.5424 | 0 | &#9989; |
| ISO 17208-1:2016 | Radiated noise level from RMS pressure and distance, dB re 1 µPa·m | 46.0206 (+/-0.0001) | 46.0206 | 0 | &#9989; |
| ISO 17208-2:2019 (Formula 3) | Lloyd's-mirror surface correction ΔL at a known k·d_s | -3.5211 (+/-0.0001) | -3.5211 | 0 | &#9989; |
| ISO 18406:2017 (Formulae 8-9) | Cumulative SEL of N identical strikes = SEL_ss + 10·lg(N) | 196.9897 (+/-0) | 196.9897 | 0 | &#9989; |

</details>

<details>
<summary>&#9989; <b>Underwater sound propagation (transmission loss)</b> — 100% (12/12)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| Mackenzie (1981) nine-term equation | Speed of sound at 25 °C, 35 ‰, 1000 m (canonical check value), m/s | 1550.744 m/s (+/-0.01 m/s) | 1550.744 m/s | 0 m/s | &#9989; |
| UNESCO/Chen-Millero vs Mackenzie | Sound-speed agreement at 10 °C, 35 ‰, 1000 m (cross-model), m/s | 1506.264 m/s (+/-1 m/s) | 1506.524 m/s | 0.261 m/s | &#9989; |
| Del Grosso (1974) vs Mackenzie | Sound-speed agreement at 10 °C, 35 ‰, 1000 m (cross-model), m/s | 1506.264 m/s (+/-1 m/s) | 1506.313 m/s | 0.049 m/s | &#9989; |
| Spherical spreading 20·lg(R) | Geometrical spreading loss at R = 1000 m, dB | 60 dB (+/-0 dB) | 60 dB | 0 dB | &#9989; |
| Thorp (1967) absorption | Volume absorption α at 10 kHz (cold deep water), dB/km | 1.1498 dB/km (+/-0 dB/km) | 1.1498 dB/km | 0 dB/km | &#9989; |
| Ainslie-McColm (1998) vs Francois-Garrison (1982) | Absorption agreement at 10 kHz, 10 °C, 35 ‰, 0 m, pH 8, dB/km | 0.9603 dB/km (+/-0.096 dB/km) | 0.9866 dB/km | 0.026 dB/km | &#9989; |
| Passive sonar equation (Urick/Etter) | Figure of merit SL − (NL − DI) − DT, dB | 85 dB (+/-0 dB) | 85 dB | 0 dB | &#9989; |
| Seabed reflection (Rayleigh, normal incidence) | Bottom loss at 90° grazing, sand ρ=1900 c=1650 over water, dB | 9.0506 dB (+/-0 dB) | 9.0506 dB | 0 dB | &#9989; |
| Wenz wind noise (rule of fives) | Wind spectrum level at 1 kHz, 5 kn (canonical anchor), dB re 1 µPa²/Hz | 51.0206 dB (+/-0.0001 dB) | 51.0206 dB | 0 dB | &#9989; |
| Mellen thermal noise | Thermal spectrum level at 50 kHz, 16.85 °C (physical), dB re 1 µPa²/Hz | 19.3426 dB (+/-0 dB) | 19.3426 dB | 0 dB | &#9989; |
| JOMOPANS-ECHO ship source level | Bulker V=13.5 kn L=211 m band level at 1 kHz (File S1 oracle), dB re 1 µPa m | 161.394 dB (+/-0.01 dB) | 161.394 dB | 0 dB | &#9989; |
| UNESCO sound speed (EOS-80 canonical value) | SVEL(S = 40, T68 = 40 °C, P = 1000 bar) vs Fofonoff & Millard 1983, m/s | 1731.995 m/s (+/-0.02 m/s) | 1732.004 m/s | 0.009 m/s | &#9989; |

</details>

<details>
<summary>&#9989; <b>Underwater numerical propagation (modes / rays / PE)</b> — 100% (4/4)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| Normal modes vs ideal waveguide | Fundamental horizontal wavenumber kr1 at 20 Hz, 100 m (analytic), rad/m | 0.077662 rad/m (+/-0.0001 rad/m) | 0.077662 rad/m | 0 rad/m | &#9989; |
| Normal modes vs image-source oracle | Absolute TL at 1 km in the ideal waveguide (converged image sum), dB | 48.238 dB (+/-0.02 dB) | 48.239 dB | 0.001 dB | &#9989; |
| Ray tracing vs linear gradient | Turning depth of a 10° ray, c = 1500 + 0.05z (circular arc), m | 462.8 m (+/-1 m) | 462.8 m | 0 m | &#9989; |
| Parabolic equation vs free field | PE transmission loss at 2 km, homogeneous medium (spherical spreading), dB | 66.021 dB (+/-0.1 dB) | 66.021 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Aircraft noise (ICAO Annex 16 / IEC 61265)</b> — 100% (14/14)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ECAC Doc 29 noise fraction (half path) | Finite-segment correction ΔF for a perpendicular foot at the segment start, dB | -3.0103 dB (+/-0.001 dB) | -3.0103 dB | 0 dB | &#9989; |
| ECAC Doc 29 single-event chain | SEL of a long level flyover vs the infinite-path limit LE∞ + ΔI − Λ, dB | 83.444 dB (+/-0.01 dB) | 83.444 dB | 0 dB | &#9989; |
| ECAC Doc 29 impedance adjustment (standard atmosphere) | Acoustic-impedance adjustment of NPD data at 15 °C / 101.325 kPa (Eq. 4-6/4-7), dB | 0.074 dB (+/-0.0005 dB) | 0.0741 dB | 0 dB | &#9989; |
| ECAC Doc 29 reference workbook (segment Λ) | Lateral attenuation of a climbing segment vs the ECAC Vol 3 Part 1 workbook, dB | 6.3769 dB (+/-0.01 dB) | 6.3769 dB | 0 dB | &#9989; |
| ECAC Doc 29 start-of-roll directivity (jet) | ΔSOR behind a takeoff ground-roll segment vs the Vol 3 Part 1 workbook, dB | 0.3196 dB (+/-0.01 dB) | 0.3196 dB | 0 dB | &#9989; |
| ECAC Doc 29 start-of-roll directivity (turboprop) | ΔSOR behind a takeoff ground-roll segment (turboprop, Eq. 4-24b), dB | 1.0943 dB (+/-0.01 dB) | 1.0944 dB | 0 dB | &#9989; |
| ECAC Doc 29 workbook event assembly (JETFDS/R03, behind SOR) | Energy sum of the reference per-segment SELs vs the B-1 event total, dB | 74.73 dB (+/-0.01 dB) | 74.733 dB | 0.003 dB | &#9989; |
| SAE ARP 5534 band-attenuation continuity | SAE-Method δ_B at the 150 dB branch split (Eq. 7 vs Eq. 8), dB | 123.95 dB (+/-0.01 dB) | 123.953 dB | 0.003 dB | &#9989; |
| ECAC Doc 29 NPD interpolation | Log-linear NPD level at the log-midpoint distance (Eq. 4-4), dB | 97 dB (+/-0 dB) | 97 dB | 0 dB | &#9989; |
| SAE ARP 5534 pure-tone coefficient (ISO 9613-1) | Mid-band α at 1 kHz, 25 °C, 70 % RH, 101.325 kPa, dB/m | 0.006186 dB/m (+/-0 dB/m) | 0.006186 dB/m | 0 dB/m | &#9989; |
| ICAO Annex 16 Vol. I App. 2 Table A2-3 | Perceived noisiness at SPL(b), 1 kHz band, in noys | 1 (+/-0) | 1 | 0 | &#9989; |
| ICAO Doc 9501 ETM Vol. I Table 3-7 | Tone correction of the turbofan example, dB | 2 (+/-0) | 2 | 0 | &#9989; |
| ICAO Doc 9501 ETM Vol. I Table 4-4 | Integrated-method reference EPNL, EPNdB | 92.619 EPNdB (+/-0.01 EPNdB) | 92.619 EPNdB | 0 EPNdB | &#9989; |
| IEC 61265:1995 Table 1 | Directional-response tolerance at 4 kHz / 90°, dB | 2 dB (+/-0 dB) | 2 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Rotorcraft noise (ECAC Doc 32 / NORAH2)</b> — 100% (4/4)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ECAC Doc 32 atmospheric attenuation (Table 4) | ΔLa over a 1 km excess path at 1 kHz vs the NORAH2 guidance Table 4, dB | 6.3 dB (+/-0.2 dB) | 6.186 dB | -0.114 dB | &#9989; |
| ECAC Doc 32 spherical spreading | ΔLs at ten times the 60 m hemisphere reference distance (Eq. 24), dB | -20 dB (+/-0 dB) | -20 dB | 0 dB | &#9989; |
| ECAC Doc 32 ground effect (rigid limit) | ΔLg over a rigid surface at grazing incidence tends to +6 dB (Eq. 29), dB | 6 dB (+/-1 dB) | 6 dB | 0.002 dB | &#9989; |
| ECAC Doc 32 propagation chain (NORAH2 prototype) | LA of a single-hemisphere emission vs the NORAH2 prototype single-event history (R22 approach, 223.66 m slant), dB(A) | 55.87 dB(A) (+/-0.1 dB(A)) | 55.886 dB(A) | 0.016 dB(A) | &#9989; |

</details>

<details>
<summary>&#9989; <b>Wind-turbine noise (IEC 61400-11)</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61400-11:2012 Formula 30 | Critical bandwidth about a 500 Hz tone, Hz | 117.255 Hz (+/-0 Hz) | 117.255 Hz | 0 Hz | &#9989; |
| IEC 61400-11:2012 Formula 26 | Apparent sound power level of a single band, dB re 1 pW | 148.5139 dB (+/-0.0001 dB) | 148.5139 dB | 0 dB | &#9989; |
| IEC 61400-11:2012 Formulae 31-34 | Tonal audibility of a synthetic clean tone, dB | 16.38 dB (+/-0.06 dB) | 16.38 dB | -0.001 dB | &#9989; |

</details>

