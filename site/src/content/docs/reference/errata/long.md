---
title: "Errata in Long (2014)"
description: "Errata in Long (2014): 4 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 4 entries of the [errata registry](/phonometry/reference/errata/) on Long (2014), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Long, Architectural Acoustics 2e (2014), Eq. (18.24) (sign of the microphone directivity)

- **Location:** Chapter 18, "Multiple Open Microphones", Eq. (18.24) (printed
  p. 699), the gain-before-feedback stability criterion generalised to several
  open microphones.
- **The print:**
  $Z_S + L_{H-M} + \Delta L_\text{nom} \le L_{H-L} \boldsymbol{+} D_M(\theta) - 10$,
  with the microphone directivity index entering the right-hand side with a
  plus sign.
- **The problem:** Eq. (18.24) is the number-of-open-microphones
  generalisation of Eq. (18.20) (printed p. 698), which reads
  $Z_S + L_{H-M} \le L_{H-L} \boldsymbol{-} D_M(\theta) - 10$ and which
  follows in turn from the oscillation condition Eq. (18.19),
  $Z_S + L_{H-M} = L_{H-L} - D_M(\theta)$, obtained by substituting the
  feedback-loop gain $G_S = L_{H-M} - L_{H-L} + D_M(\theta)$ (Eq. (18.18))
  into $Z_S + G_S = 0$ (Eq. (18.16)). Setting $N_m = 1$ makes
  $\Delta L_\text{nom} = 0$, so Eq. (18.24) must reduce to Eq. (18.20) and
  does not. The sign matters physically: $D_M(\theta)$ is "usually negative"
  in Long's own definition (about $-2$ to -3 dB for a cardioid pointed at the
  talker), so as printed a directional microphone would *cost* gain before
  feedback instead of buying it, inverting the chapter's own conclusion that
  "it is prudent to incorporate a cardioid or hypercardioid microphone into a
  system".
- **Evidence:** the printed equation reads
  $Z_S + L_{H-M} + \Delta L_\text{nom} \le L_{H-L} + D_M(\theta) - 10$,
  against $Z_S + L_{H-M} \le L_{H-L} - D_M(\theta) - 10$ two pages earlier,
  where the same position holds a minus. (An earlier revision of this entry
  quoted the `pdftotext` extraction,
  `Z S þ L HM þ DL nom  L HL þ D M ðqÞ  10`, in which `þ` is the ligature this
  PDF uses for "+" and every minus sign has been dropped entirely; that
  extraction cannot distinguish a plus from a minus and should never have been
  the evidence.) Verified on PDF page 697 (printed p. 699) and PDF page 696
  (printed p. 698) of Long, Architectural Acoustics 2e (2014). The minus sign
  is the one that reproduces Long's own worked special cases at $N_m = 1$:
  with $Z_S = -6\ \text{dB}$, Eq. (18.21) gives
  $L_{H-M} \le L_{H-L} - D_M(\theta) - 4$ (an omnidirectional microphone 4 dB
  below the average audience level), and Eq. (18.22) gives
  $L_{H-M} \le L_{H-L} - 2$ for a cardioid at $D_M = -2\ \text{dB}$. Neither
  special case is recoverable from the printed Eq. (18.24).
- **Library behaviour:** `feedback_stability` in
  [`sound_reinforcement.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/sound_reinforcement.py)
  implements the sign of Eq. (18.20), with a note at the criterion. Both of
  Long's special cases are pinned by regression tests
  ([`tests/electroacoustics/test_sound_reinforcement.py`](https://github.com/jmrplens/phonometry/blob/main/tests/electroacoustics/test_sound_reinforcement.py))
  and by the conformance checks "Long, Architectural Acoustics 2e, Eq.
  (18.21)" and "Eq. (18.22)".
- **Status:** unreported (textbook rather than a standard, so non-normative).

## Long, Architectural Acoustics 2e (2014), Eq. (17.53) (constant of the communication bound)

- **Location:** Chapter 17, "Restaurant Design", Eq. (17.53) (printed p. 666),
  the minimum absorption per occupied table for adequate cross-table
  communication.
- **The print:** $A_\text{tab} > 6.33 r_s^2$.
- **The problem:** the bound is Eq. (17.52),
  $L_\text{SN} = 10\log_{10}[Q/(4\pi r^2)] + 10\log_{10}[A_\text{tab}/4]$,
  solved for $A_\text{tab}$ at the stated threshold
  $L_\text{SN} > -6\ \text{dB}$, which gives
  $A_\text{tab} > 16\pi \cdot 10^{-0.6} r_s^2/Q$. With the $Q = 2$ the chapter
  uses for a talker, that constant is 6.3130, not 6.33. The gap is $0.27\,\%$,
  i.e. the last printed digit: 6.33 is what $16\pi \cdot 10^{-0.6}/2$ returns
  if $10^{-0.6}$ is carried coarsely as 0.252 instead of 0.251 19. This is
  graded as a rounding-level discrepancy rather than a structural error of the
  formula, since the formula itself is confirmed by its companion (below) and
  no consistent alternative assumption reproduces 6.33 (it would require
  $Q = 1.995$).
- **Evidence:** the immediately following Eq. (17.54) is the same closed form
  at the privacy threshold $L_\text{SN} < -9\ \text{dB}$, and its printed
  constant 3.16 is exactly what $16\pi \cdot 10^{-0.9}/2 = 3.1640$ gives,
  confirming both the formula and $Q = 2$. Only the -6 dB constant is off.
  What does *not* discriminate is Long's prose one paragraph later, "at least
  6.3 or more square meters (68 sq ft) of absorption per table": $6.313\ \text{m}^2$ is
  $67.95\ \text{ft}^2$ and $6.33\ \text{m}^2$ is $68.14\ \text{ft}^2$, so both print as
  68 sq ft, and both round to $6.3\ \text{m}^2$. An earlier revision of this entry
  offered that conversion as corroboration. Verified on PDF page 665 (printed
  p. 666) of Long, Architectural Acoustics 2e (2014).
- **Library behaviour:** `absorption_per_table` in
  [`_crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/_crowd_noise.py) computes the bound
  from Eq. (17.52) rather than hardcoding either constant, so both bounds stay
  mutually consistent; the 6.313 value and the printed 3.16 are pinned by
  regression tests
  ([`tests/room/test_crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_crowd_noise.py)) and
  the 3.16 constant by the conformance check "Long, Architectural Acoustics
  2e, Eq. (17.54)".
- **Status:** unreported (textbook rather than a standard, so non-normative);
  graded as a rounding discrepancy rather than a structural defect.

## Long, Architectural Acoustics 2e (2014), Table 14.7 (round elbow rows)

- **Location:** Chapter 14, Table 14.7, "Insertion Loss of Round Elbows"
  (printed p. 541), indexed by the frequency-width product $f w$ (kHz times
  inches).
- **The print:** four rows only: $f w < 1.9$ → 0 dB; $1.9 < f w < 3.8$ → 1 dB;
  $3.8 < f w < 7.5$ → 2 dB; $f w > 15$ → 3 dB.
- **The problem:** the band $7.5 < f w < 15$ has no row at all, so the table
  jumps from $3.8 < f w < 7.5$ straight to $f w > 15$. A duct-borne
  calculation lands in that band routinely: a $24\ \text{in}$ elbow at 500 Hz
  has $f w = 12$.
- **Evidence:** the same data adapted from the same ASHRAE source appear in
  Bies, Hansen & Howard, *Engineering Noise Control* 5e, Table 8.11, indexed
  by $W/\lambda$ ($= 0.074\,f w$). Its round-elbow column has six rows,
  0/1/2/3/3/3, and gives 3 dB for $0.55 \le W/\lambda < 1.11$, which is
  exactly the $7.5 < f w < 15$ band Long omits. Long's four rows map onto
  Bies' six as follows: the first three agree entry for entry, the fourth
  ($f w > 15$, 3 dB) legitimately merges Bies' two identical top rows, and the
  band with no row is Bies' fourth. An earlier revision of this entry said
  that "Tables 14.5 and 14.6 both carry six rows" and that "the other five
  rows of the two tables agree entry for entry"; on the page, Table 14.5
  carries six rows and Table 14.6 five (it merges the same two identical top
  bands, legitimately), and Table 14.7 prints four, so neither count is right.
  Verified on PDF page 542 (printed p. 541) and PDF page 541 (printed p. 540)
  of Long, Architectural Acoustics 2e (2014).
- **Library behaviour:** `elbow_insertion_loss` in
  [`hvac.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) carries the six-row
  round column with 3 dB in the missing band, pinned by
  `test_elbow_tables_by_frequency_width_product`
  ([`tests/noise_control/test_hvac_long.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_hvac_long.py)).
- **Status:** unreported (textbook rather than a standard).

## Long, Architectural Acoustics 2e (2014), Eq. 13.28 (units of U_G)

- **Location:** Chapter 13, Eq. 13.28 (printed p. 521), the normalised
  pressure-drop coefficient $\xi = 334.9 \cdot \Delta P/(\rho_0 U_G^2)$ of the
  diffuser sound-power model.
- **The print:** the nomenclature under the equation gives "U_G = flow
  velocity prior to the diffuser (ft/min)" and, on the next line, "=
  Q/(60·S_G) (for Q in cfm)".
- **The problem:** the two statements contradict each other. $Q$ in $\text{ft}^3\text{/min}$
  divided by $60 S_G$ is a velocity in **ft/s**, not ft/min, and only the ft/s
  reading makes the constant right: $334.9/\rho_0$ with
  $\rho_0 = 0.075\ \text{lb/ft}^3$ is $4465 \cdot \Delta P/U^2$, which is the
  standard velocity-pressure relation $\Delta P/(U/4005)^2$ only when $U$ is
  converted from ft/s. Read as ft/min the coefficient comes out 3600 times too
  small. Eq. 13.27 itself declares $U_G$ in ft/s, so the "(ft/min)" label
  under Eq. 13.28 is the odd one out.
- **Evidence:** dimensional check of $Q/(60 S_G)$; reconstruction of the
  $334.9/\rho_0$ constant from the velocity-pressure relation; and the peak
  frequency. What does **not** discriminate is the overall level: Eq. 13.27
  carries $30\log_{10}\xi + 60\log_{10} U_G$, and substituting Eq. 13.28 makes
  the velocity cancel identically,
  $30\log_{10}\xi + 60\log_{10} U_G = 30\log_{10}(334.9 \Delta P/\rho_0)$. For
  the Table 14.9 supply diffuser ($S_G = 4\ \text{ft}^2$, $Q = 312$ cfm,
  $\Delta P = 0.05$ in w.g.) both readings therefore return the same
  $L_W = 45.18\ \text{dB}$. An earlier revision of this entry claimed that the
  ft/min reading "misses it by 100 dB", which is arithmetically impossible for
  a quantity that does not depend on the velocity at all. What does
  discriminate is Eq. 13.32, $f_P = 48.8 U_G$, which is the only other place
  $U_G$ enters: read in ft/s the approach velocity is $1.3\ \text{ft/s}$ and
  the peak falls at 63.4 Hz, i.e. in the 63 Hz octave, so the Eq. 13.31 shape
  puts 33.4 dB in that band against the printed 33; read in ft/min it is
  $78\ \text{ft/min}$, the peak moves to 3 806 Hz, and the same shape puts
  -8.2 dB in the 63 Hz band. Verified on PDF page 522 (printed p. 521) of
  Long, Architectural Acoustics 2e (2014).
- **Library behaviour:** `diffuser_sound_power` in
  [`hvac.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) reads $U_G$ in ft/s
  internally (SI at the interface), with the Table 14.9 row pinned by
  `test_diffuser_sound_power_reproduces_the_table_14_9_row`
  ([`tests/noise_control/test_hvac_long.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_hvac_long.py))
  and the conformance check "Long 2e Eqs. 13.27-13.33".
- **Status:** unreported (textbook rather than a standard).
