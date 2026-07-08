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

&#9989; **32/32 conformance checks pass** across 7 domains and 25 standards - filters class 1 - weightings within IEC 61672-1 class 1.

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

### Filters & weightings

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61260-1:2014 Table 1 | Octave-band filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61260-1:2014 Table 1 | One-third-octave filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | A-weighting deviation vs class-1 limits (fs=48 kHz) | deviation within limits @ 1000 Hz | +0.000 dB in [-0.70, +0.70] dB | headroom +0.700 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | C-weighting deviation vs class-1 limits (fs=48 kHz) | deviation within limits @ 1000 Hz | +0.000 dB in [-0.70, +0.70] dB | headroom +0.700 dB | &#9989; |
| ISO 7196:1995 Table 2 / A.3 | G-weighting deviation vs +/-1 dB tolerance (fs=48 kHz) | deviation within limits @ 1 Hz | +0.047 dB in [-1.00, +1.00] dB | headroom +0.953 dB | &#9989; |

### Levels & dosimetry

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61672-1:2013 (Leq) | Leq of a 1 Pa 1 kHz sine | 90.97 dB (+/-0.05 dB) | 90.969 dB | -0.001 dB | &#9989; |
| IEC 61252:1995 (LEX,8h) | 8 h exposure to 90 dB(A) noise | 90 dB (+/-0.05 dB) | 90.008 dB | 0.008 dB | &#9989; |
| ISO 1996-1:2016 3.6.4 | Lden, constant 60 dB in day/evening/night | 66.3952 dB (+/-0 dB) | 66.3952 dB | 0 dB | &#9989; |

### Psychoacoustics

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 532-1:2017 Annex B.2 | Zwicker loudness N, stationary test signal 1 | 83.2957 sone (+/-0.1%) | 83.2957 sone | 0 sone | &#9989; |
| DIN 45692:2009 Clause 6 | Sharpness of the standard 1 kHz reference signal | 1 acum (+/-0 acum) | 1 acum | 0 acum | &#9989; |
| ISO 226:2023 Table B.1 | Equal-loudness contour, 60 phon @ 100 Hz | 78.5 dB SPL (+/-0.05 dB SPL) | 78.504 dB SPL | 0.004 dB SPL | &#9989; |
| ECMA-418-2:2025 Clause 5.1.8 | HMS loudness of a 1 kHz / 40 dB tone (c_N=0.0211964) | 1 sone_HMS (+/-0.03 sone_HMS) | 0.9958 sone_HMS | -0.004 sone_HMS | &#9989; |
| ECMA-418-2:2025 Clause 6.2.8 | HMS tonality of a 1 kHz / 40 dB tone (c_T=2.8758615) | 1 tu_HMS (+/-0.03 tu_HMS) | 0.9998 tu_HMS | 0 tu_HMS | &#9989; |
| ECMA-418-2:2025 Clause 7 | HMS roughness of a 1 kHz / 70 Hz / m=1 / 60 dB tone (c_R=0.0180685) | 1.0735 asper (+/-0.01 asper) [clean-room; standard target 1] | 1.0735 asper | 0 asper | &#9989; |
| ISO 532-2:2017 Clause 3.17 / Annex B.1 | Moore-Glasberg loudness of a 1 kHz / 40 dB tone (C=0.0617) | 1 sone (+/-0.01 sone) | 1.0001 sone | 0 sone | &#9989; |
| ISO 532-3:2023 Annex C.1 | Moore-Glasberg-Schlittenlacher peak LTL, steady 1 kHz / 40 dB | 1 sone (+/-0.02 sone) | 0.9996 sone | 0 sone | &#9989; |

### Speech intelligibility

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 60268-16:2020 A.2.2 | STI weighting-factor pair (500 Hz + 1 kHz bands) | 0.398 (+/-0.001) | 0.398 | 0 | &#9989; |
| IEC 60268-16:2020 A.3.1.2 | Uniform MTF m=0.5 maps to STI=0.5 | 0.5 (+/-0.01) | 0.5 | 0 | &#9989; |

### Intensity & sound power

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61043:1994 Clause 5 | Plane-wave intensity I = p^2 / (rho c) | 0.00238 W/m^2 (+/-1.5%) | 0.00239 W/m^2 | 0 W/m^2 | &#9989; |
| ISO 3744:2010 Eq. 18 | Monopole hemisphere recovers LW (r=4 m) | 95 dB (+/-0 dB) | 95 dB | 0 dB | &#9989; |
| ISO 9614-2:1996 Eq. 12 | Intensity scan recovers LW of an enclosed source | 90 dB (+/-0.000001 dB) | 90 dB | 0 dB | &#9989; |
| ISO 3741:2010 Eq. 20 | Reverberation-room method inverts to a known LW | 0 dB error | 0 dB | 0 dB | &#9989; |

### Room & building acoustics

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 3382-2:2008 5.3.3 | T30 from a synthetic exponential decay (T=1.0 s) | 1 s (+/-1%) | 1 s | 0 s | &#9989; |
| ISO 717-1 Annex C, Table C.1 | Weighted sound reduction index Rw (C;Ctr) | Rw 30 (C -2; Ctr -3) | Rw 30 (C -2; Ctr -3) | sum 31.8 dB | &#9989; |
| ISO 354:2003 Eq. 5/8 | Sabine inversion recovers absorption area | 9.212828 m^2 (+/-0 m^2) | 9.212828 m^2 | 0 m^2 | &#9989; |
| ISO 3382-3:2012 Clause 6.2 | Open-plan spatial decay rate D2,S (-6 dB/doubling) | 6 dB (+/-0 dB) | 6 dB | 0 dB | &#9989; |
| ISO 16283-3:2016 Clause 3.12 | Facade R'45 isolates the -1.5 dB incidence correction (S=A) | 38.5 dB (+/-0 dB) | 38.5 dB | 0 dB | &#9989; |
| ISO 10140-2:2021 Formula (2) | Lab airborne R on the ISO 717-1 reference shape -> Rw = 54 | Rw 54 dB | Rw 54 dB | +0 dB | &#9989; |

### Building prediction & uncertainty

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| EN 12354-1:2000 Annex H.3 | Airborne prediction R'w (direct + 12 flanking paths) | R'w 52 dB (13 paths) | R'w 52 dB (13 paths, 52.17) | +0.17 dB | &#9989; |
| EN 12354-2:2000 Annex E.3 | Impact prediction L'n,w = Ln,w,eq - dLw + K | 45 dB (+/-0 dB) | 45 dB | 0 dB | &#9989; |
| ISO 12999-1:2020 Table 2 | Airborne band uncertainty, situation A @ 1 kHz | 1.8 dB (+/-0 dB) | 1.8 dB | 0 dB | &#9989; |
| ISO 12999-1:2020 Clause 8 / Table 8 | Expanded uncertainty U = 1.96 u (95 % two-sided, Rw sit. A) | 2.352 dB (+/-0 dB) | 2.352 dB | 0 dB | &#9989; |

