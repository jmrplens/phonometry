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

&#9989; **90/90 conformance checks pass** across 21 domains and 56 standards - filters class 1 - weightings within IEC 61672-1 class 1.

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
<summary>&#9989; <b>Filters &amp; weightings</b> — 100% (5/5)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61260-1:2014 Table 1 | Octave-band filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61260-1:2014 Table 1 | One-third-octave filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | A-weighting deviation vs class-1 limits (fs=48 kHz) | deviation within limits @ 1000 Hz | +0.000 dB in [-0.70, +0.70] dB | headroom +0.700 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | C-weighting deviation vs class-1 limits (fs=48 kHz) | deviation within limits @ 1000 Hz | +0.000 dB in [-0.70, +0.70] dB | headroom +0.700 dB | &#9989; |
| ISO 7196:1995 Table 2 / A.3 | G-weighting deviation vs +/-1 dB tolerance (fs=48 kHz) | deviation within limits @ 1 Hz | +0.047 dB in [-1.00, +1.00] dB | headroom +0.953 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Levels &amp; dosimetry</b> — 100% (3/3)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61672-1:2013 (Leq) | Leq of a 1 Pa 1 kHz sine | 90.97 dB (+/-0.05 dB) | 90.969 dB | -0.001 dB | &#9989; |
| IEC 61252:1995 (LEX,8h) | 8 h exposure to 90 dB(A) noise | 90 dB (+/-0.05 dB) | 90.008 dB | 0.008 dB | &#9989; |
| ISO 1996-1:2016 3.6.4 | Lden, constant 60 dB in day/evening/night | 66.3952 dB (+/-0 dB) | 66.3952 dB | 0 dB | &#9989; |

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
<summary>&#9989; <b>Speech intelligibility</b> — 100% (2/2)</summary>

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
<summary>&#9989; <b>Room &amp; building acoustics</b> — 100% (8/8)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 3382-2:2008 5.3.3 | T30 from a synthetic exponential decay (T=1.0 s) | 1 s (+/-1%) | 1 s | 0 s | &#9989; |
| ISO 717-1 Annex C, Table C.1 | Weighted sound reduction index Rw (C;Ctr) | Rw 30 (C -2; Ctr -3) | Rw 30 (C -2; Ctr -3) | sum 31.8 dB | &#9989; |
| ISO 354:2003 Eq. 5/8 | Sabine inversion recovers absorption area | 9.212828 m^2 (+/-0 m^2) | 9.212828 m^2 | 0 m^2 | &#9989; |
| ISO 3382-3:2012 Clause 6.2 | Open-plan spatial decay rate D2,S (-6 dB/doubling) | 6 dB (+/-0 dB) | 6 dB | 0 dB | &#9989; |
| ISO 16283-3:2016 Clause 3.12 | Facade R'45 isolates the -1.5 dB incidence correction (S=A) | 38.5 dB (+/-0 dB) | 38.5 dB | 0 dB | &#9989; |
| ISO 10140-2:2010 Formula (2) | Lab airborne R on the ISO 717-1 reference shape -> Rw = 54 | Rw 54 dB | Rw 54 dB | +0 dB | &#9989; |
| ISO 9613-1:1993 Table 1 | Air attenuation @ 10 degC, 70 %, 1 kHz | 3.66 dB/km (+/-0.01 dB/km) | 3.658 dB/km | -0.002 dB/km | &#9989; |
| ISO 9613-1:1993 Table 1 | Air attenuation @ 0 degC, 20 %, 2 kHz | 34.6 dB/km (+/-0.1 dB/km) | 34.64 dB/km | 0.04 dB/km | &#9989; |

</details>

<details>
<summary>&#9989; <b>Building prediction &amp; uncertainty</b> — 100% (4/4)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| EN 12354-1:2000 Annex H.3 | Airborne prediction R'w (direct + 12 flanking paths) | R'w 52 dB (13 paths) | R'w 52 dB (13 paths, 52.17) | +0.17 dB | &#9989; |
| EN 12354-2:2000 Annex E.3 | Impact prediction L'n,w = Ln,w,eq - dLw + K | 45 dB (+/-0 dB) | 45 dB | 0 dB | &#9989; |
| ISO 12999-1:2020 Table 2 | Airborne band uncertainty, situation A @ 1 kHz | 1.8 dB (+/-0 dB) | 1.8 dB | 0 dB | &#9989; |
| ISO 12999-1:2020 Clause 8 / Table 8 | Expanded uncertainty U = 1.96 u (95 % two-sided, Rw sit. A) | 2.352 dB (+/-0 dB) | 2.352 dB | 0 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Outdoor propagation &amp; occupational exposure</b> — 100% (7/7)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 9613-2:1996 Eq. (7) | Geometrical divergence Adiv = 20 lg(d/d0) + 11 at 100 m | 51 dB (+/-0 dB) | 51 dB | 0 dB | &#9989; |
| ISO 9613-2:1996 Table 3 | Ground b'(0) porous limit -> Agr(250 Hz) = 2(-1.5 + 10.1) | 17.2 dB (+/-0 dB) | 17.2 dB | 0 dB | &#9989; |
| ISO 9613-2:1996 clause 7.4 | Single-edge diffraction saturates at the 20 dB cap | 20 dB (+/-0 dB) | 20 dB | 0 dB | &#9989; |
| ISO 9613-2:1996 clause 7.4 | Double-edge diffraction saturates at the 25 dB cap | 25 dB (+/-0 dB) | 25 dB | 0 dB | &#9989; |
| ISO 9612:2009 Annex D | Task-based LEX,8h + U (welder day, case a) | LEX,8h 84.3; U 2.7 dB | LEX,8h 84.3; U 2.7 dB | -0.01; +0.02 dB | &#9989; |
| ISO 9612:2009 Annex E | Job-based LEX,8h + U (production line, 18 workers) | LEX,8h 88.1; U 3.8 dB | LEX,8h 88.2; U 3.8 dB | +0.06; -0.03 dB | &#9989; |
| ISO 9612:2009 Annex F | Full-day LEX,8h + U (forklift drivers) | LEX,8h 90.1; U 3.4 dB | LEX,8h 90.1; U 3.4 dB | +0.02; +0.03 dB | &#9989; |

</details>

<details>
<summary>&#9989; <b>Materials: absorption, airflow &amp; impedance</b> — 100% (5/5)</summary>

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 11654:1997 Annex A.1 | Weighted absorption alpha_w (no indicator) | 0.60 (class C, no indic.) | 0.60 (class C, '') | 0 | &#9989; |
| ISO 11654:1997 Annex A.2 | Weighted absorption alpha_w with M indicator | 0.60(M) | 0.60(M) | 0 | &#9989; |
| ISO 9053-2:2020 Annex A.3 | Thermal boundary-layer thickness b | 0.00183 m (+/-0.00001 m) | 0.00183 m | 0 m | &#9989; |
| ISO 9053-2:2020 Annex A.3 | Effective ratio of specific heats kappa' | 1.37 (+/-0.001) | 1.37 | 0 | &#9989; |
| ISO 10534-1:1996 Eqs (9)/(13)/(14) | Absorption from standing-wave ratio s=3 | 0.75 (+/-0) | 0.75 | 0 | &#9989; |

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

