---
title: "Source properties that are not errata"
description: "Properties of the published sources that look like misprints and are not, recorded so that nobody corrects the library to match them."
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

The [errata registry](/phonometry/reference/errata/) also records properties of the published sources that look like defects and are not: a difference the source discloses itself, a rounding it shares with its family, a value that is right for a form of the material the other books do not describe. They are kept here so that a future reader does not "fix" the library to match them.

## Related source properties that are not errata

Recorded here to prevent future "fixes" that would break agreement with the
published sources:

- **Norton & Karczub 2e (2003), Appendix 4 A, the densities of
  polystyrene, polyurethane and PVC:** the appendix prints $42$, $72$ and
  $66$ kg/m$^3$, where Mechel and Bies print $1070$, $900$ and $1400$ for the
  same names. The difference is not a lost digit. Each Norton & Karczub row
  also prints a Young's modulus and a bulk speed, and the three satisfy
  $E = \rho c^2$ to within a per cent, which describes the expanded or
  cellular form of the polymer; the other books describe the solid one.
  Neither page qualifies the bare name. Verified on PDF page 625 (printed
  p. 605). Registered here, and in `ACCEPTED` in
  `scripts/check_solid_agreement.py`, so that the low densities are not
  "corrected" to the solid polymer's.
- **Norton & Karczub 2e (2003), Appendix 4 C, hydrogen and oxygen at 0 and
  20 °C:** each gas is printed with the same density at both temperatures,
  $0.084$ and $1.43$ kg/m$^3$, while its speed changes as it should and air, in
  the same table, drops from $1.293$ to $1.21$ over the same interval. It is
  not registered as an erratum because the table's own columns do not settle
  it: $P = \rho c^2/\gamma$ puts these rows between $96$ and $109$ kPa, no
  further from an atmosphere than the carbon dioxide and steam rows. Verified
  on PDF page 626 (printed p. 606). The four states say so in their
  `validity` in [`PUBLISHED_FLUIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/catalogue.py),
  and the published catalogues page shows it on their density.
- **ISO 11546-1:1995 Annex A and Annex B:** Figure B.1 is captioned "Source
  spectrum for an artificial sound source constructed according to the
  guidelines given in annex A", while Annex A, which asks for a steel plate of
  4 mm by 800 mm (approx.) by 300 mm (approx.), adds in its own last paragraph
  that "the length of the steel plate used for this measurement was 600 mm"
  and that a source built to the annex may give a different spectrum. The
  figure is therefore an illustration of a source a quarter shorter than the
  approximate length the annex prescribes, and the annex says so. Verified on
  PDF page 17 (printed p. 10) and PDF page 19 (printed p. 12) of ISO
  11546-1:1995 as published in BS EN ISO 11546-1:2009. Not registered as an
  erratum because the standard discloses the difference itself; registered
  here so that
  [`ARTIFICIAL_SOURCE_EXAMPLE_LWA`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  is not read as a property of an Annex A source.

- **ISO 7235:2003, Equations (10), (21) and (22):** the ideal gas law is
  printed with $R = 287\ \text{N}\cdot\text{m}/(\text{kg}\cdot\text{K})$
  and the absolute temperature written as $\theta + 273\ ^\circ\text{C}$.
  Neither is the accurate value (287,05 and 273,15). The offset alone puts a
  density 0,051 % high at 20 °C and the gas constant adds 0,017 % to that, for
  0,069 % in all. This is a simplification and not a defect: the density it
  produces is used only in the dynamic pressure of Equations (16), (19) and
  (20), and both series of the pressure loss coefficient carry the same
  factor, so Equations (17) and (18) come out **scaled** by it rather than
  shifted, 0,069 % low, which is far under the uncertainty of a
  pressure-loss test and is what a result computed to the standard shows. The
  library keeps both printed constants, as
  [`ISO7235_AIR_GAS_CONSTANT_J_KG_K`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_measurement.py)
  and `ISO7235_ABSOLUTE_ZERO_OFFSET_K`, so that a worked result can be
  reproduced as the standard gives it, and the conformance row "Normal air
  density (Eqs. (10), (21), (22))" records the size of the gap.

- **ISO 12354-1:2017 Table L.8 / ISO 12354-2:2017 Table G.8, first row:** the
  row labelled "Int. wall 1/2 – Ext. wall 1/2" prints
  $m'_i = 219{,}0\ \text{kg/m}^2$ and $m'_{\perp i}$ (Part 2:
  $m'_\text{orthogonal}$) $= 360{,}0\ \text{kg/m}^2$, which is the assignment
  for a path *leaving the external wall*, the opposite of the direction the
  row's own label gives. Read in the row's direction the element carrying the
  path is the internal wall, so $m'_i$ should be 360,0 and the perpendicular
  mass 219,0. It is a labelling slip and nothing else: the branch is the
  rigid-T **corner** branch $K_{12} = 5{,}7 + 5{,}7 M^2$, where only $M^2$
  enters, so both assignments return the same 5,965 → 6,0 dB. The second row
  of each table, "Ext. wall 1/2 – Ext. wall 1/2", is the through branch
  $5{,}7 + 14{,}1 M + 5{,}7 M^2$, where the sign of $M$ does matter, and it is
  labelled and populated consistently ($M = \log_{10}(360/219)$ gives 9,006 →
  the printed 9,0). Verified on PDF page 89 (printed p. 83) of ISO
  12354-1:2017 and PDF page 46 (printed p. 40) of ISO 12354-2:2017. Not
  registered as an erratum because no number depends on it; registered here so
  that a future reader does not "correct" the library's per-path convention to
  match the printed row.
- **Francois-Garrison pure-water term:** the two published $A_3$ cubics do not
  meet exactly at the 20 °C switch (a step of
  $1 \cdot 10^{-7} f^2\ \text{dB/km}$, 0.1 dB/km at 1 MHz). Inherent in the
  published coefficients.
- **Ainslie-McColm simplification:** the paper's "within 10 % of
  Francois-Garrison" claim is marginally exceeded at the extreme corners of
  its stated domain (10.4 % at −6 °C / 1 MHz; 12.3 % at 7 km depth). A
  property of the published fit; both transcriptions verified digit-for-digit.
- **CNOSSOS-EU Annex II 2.3, missing equation number:** the railway section
  numbers its formulae (2.3.1), (2.3.2), (2.3.4), (2.3.5)..., with no (2.3.3)
  anywhere in Annex II. Verified on PDF page 17 (printed p. L 168/17) of
  Directive (EU) 2015/996:2015, where (2.3.2) and (2.3.4) sit one above the
  other. Nothing is missing from the method; only the numbering skips.
- **CNOSSOS-EU corrigendum of 2018, Table G-3 column codes:** the corrigendum
  is reported to head the seven $L_{r,TR}$ columns "B/S B/M B/H B/S B/M B/H
  B/H", where the first three should read "M/S M/M M/H" and the last "W", and
  Commission Delegated Directive (EU) 2021/1226 Annex point (20)(c) does
  replace that header with the corrected codes plus a new column D. It is left
  unregistered because the corrigendum itself is published only as HTML on
  EUR-Lex, so no printed page of it could be obtained here, and this registry
  does not record a claim about a printed symbol that has not been read off
  the page. The 2015 print of the same table, which was read, carries
  descriptive headers ("Mono-block sleeper on soft rail pad" and so on) and no
  defect.
- **Long, Architectural Acoustics 2e, Chapter 17, adjacent-table level:** the
  restaurant example states that "at an adjacent table 3 m (10 ft) away, the
  direct field level from our conversation is about 54 dB", where his own Eq.
  (17.50) with the $Q = 2$ and $L_W = 70\ \text{dB}$ that yield his 60 dB at
  1.2 m gives 52.5 dB. It is left unregistered because the intended reading
  cannot be established from the book: 54 dB is also what the same equation
  gives at 2.5 m (54.1 dB, and 2.5 m is the table spacing the next paragraph
  derives), and what a single 6 dB distance doubling from the rounded 60 dB
  would give, while the printed "3 m (10 ft)" is self-consistent in both units
  and is repeated in the preceding paragraph. `speech_direct_level` evaluates
  Eq. (17.50) as printed, so it returns 52.5 dB there; do not "correct" it
  toward 54 dB.
- **ICAO Annex 16 EPNL constant:** the Annex's rounded constant 13 for uniform
  0.5 s records differs from the exact $-10\log_{10}(T_0)$ form by 0.0103 dB;
  the library uses the exact form, which the ETM's integrated reference
  reproduces to five decimals.
- **Long Table 14.9 element rows:** the worked duct-borne sheet of Chapter 14
  was produced by a commercial program, as the text introducing it states, and
  several of its element rows do not follow from the tables printed beside
  them: the fan row (90/86/82/79/77/75/71/61 dB) is not what Eq. 13.1 gives
  with the Table 13.5 forward-curved constants at that duty
  (99/99/89/84/82/77/72/67 dB, and not a level shift of it), and the
  flexible-duct row (14/14/16/15/17/22/16/13 dB) is not the Table 14.4 entry
  for 12 in by 6 ft (3/5/10/15/17/16/9 dB). The library implements the printed
  equations and tables, and uses the sheet only for what it genuinely pins,
  the cascade arithmetic; its element rows are fed in as published in
  [`tests/noise_control/test_duct_path.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_duct_path.py).
  The sheet's own rounding is likewise not always self-consistent (supply row
  3 prints a *Sum* of 49 dB at 500 Hz where $76 - 28 = 48$, then a *Combined*
  consistent with 48), which is why the comparison runs at the 1 dB the
  printed sheet carries.
- **ISO 3747:2010 Table E.1, the accuracy-grade labels:** the informative
  table of worked $\sigma_\mathrm{tot}$ examples labels its three rows
  "0,5 (accuracy grade 1)", "1,5 (accuracy grade 2)" and "3 (accuracy
  grade 3)", while the normative Table 2 of this part gives
  $\sigma_{R0}$ = 4,0 dB for survey grade 3 and the scope of ISO 3747 covers
  grades 2 and 3 only. It is the ISO 3740 family's shared illustration, not a
  statement about this method: ISO 3744:2010 Table H.1 prints the identical
  table, rows, labels and $\sigma_\mathrm{tot}$ cells alike, and ISO 3744
  covers grade 2 only. Verified on PDF page 42 (printed p. 33) and PDF page
  27 (printed p. 18) of BS EN ISO 3747:2010. The library reads
  $\sigma_{R0}$ from the normative Table 2 (1,5 dB and 4,0 dB, conformance
  check "ISO 3747:2010 Table 2 / Eq. 22") and uses Table E.1 only for its
  $\sigma_\mathrm{tot}$ = 1,6 / 2,5 / 4,3 row against $\sigma_{R0}$ = 1,5 dB,
  where the two tables agree. Do not "correct" the 3 dB row to 4,0 dB: it
  belongs to the family's illustration, not to this part's Table 2.
- **ISO 3747:2010 Annex C, $\theta_\mathrm{ref}$ = 296 K:** the annex prints
  the reference temperature of the radiation-impedance correction as 296 K
  beside a reference condition of 23,0 °C, which is 296,15 K, so at exactly
  the reference conditions $C_2 = 15 \lg(296{,}15/296) = +0{,}003\,3$ dB
  rather than zero. ISO 3741:2010 clause 9.1.4 and ISO 3744:2010 print the
  same $\theta_1$ = 296 K, so it is the family's rounding and not a misprint
  of one part; the library keeps 296 K in the shared `C2` of
  [`_sound_power_reverberation.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/_sound_power_reverberation.py)
  and pins the residual (conformance check "ISO 3747:2010 Annex C"). Do not
  "correct" it to 296,15 K.
- **ISO 3747:2010 Eq. (14), the single-event background margin:**
  $\Delta L_{Ei} = L'_{Ei,q(\mathrm{ST})} - L_{pi(\mathrm{B})}$ subtracts a
  time-averaged background level from a time-integrated single event level,
  asking only that both be measured over the same integration time $T$. The
  difference is a true margin for $T$ = 1 s; for a longer $T$ the background
  holds $10 \lg(T/T_0)$ dB more energy over the event's interval (clause 3.4,
  NOTE 1). ISO 3741:2010 Eq. (25) and ISO 3744:2010 clause 8.3.4 print the
  same line, verified on PDF page 23 (printed p. 14) of BS EN ISO 3747:2010
  and on the corresponding pages of the two siblings, so it is the family's
  convention and is not registered against one part. The library applies
  Eq. (14) as printed by default and offers `integration_time` on
  [`sound_energy_in_situ`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/_sound_power_in_situ.py)
  to carry the background to the event's interval first.

- **ISO 5136:2003, clause 5.3.4.3, the sign of Equation (8):** the clause
  says the corrections of the nose cone and the foam ball "are estimated to
  be negative and of small magnitude", and then prints
  $C_{3,4} = 10 \lg[1/(1 - U/c)^2]$ dB, which is positive whenever $U > 0$:
  at the 20 m/s the nose cone is allowed, with $c$ = 340 m/s, $+0{,}53$ dB on
  the outlet side and $-0{,}50$ dB on the inlet side. The equation's sign is
  the one the convected plane wave gives, the energy flux of a wave
  travelling with the flow being $(1 + M)^2$ times $p^2/\rho c$, so for a
  given pressure the power is higher downstream and lower upstream. It is not
  registered as an erratum because the closing sentence of the same paragraph
  reconciles the two: "With this simplification, the sound power level
  obtained by using the nose cone or foam ball is expected to be higher than
  the true sound power level." The negative correction is the modal one,
  which is unavailable and is dropped; Equation (8) is the convective part
  that is kept, and the standard says in the same breath that what is left
  biases $L_W$ high. Read on PDF page 29 (printed p. 19) of ISO 5136:2003.
  Registered here so that nobody "corrects" the sign of Equation (8), which
  [`flow_modal_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/_sound_power_in_duct.py)
  implements as printed and `test_eq8_omnidirectional_shields` in
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py)
  pins.

- **ISO 11820:1996 Table 1 and ISO 10847:1997 Table 3, two background
  corrections that disagree:** both tables take a margin between the level
  with the source and the level without it and answer with a correction in
  decibels, and they answer differently. ISO 11820 refuses under 3 dB and then
  takes off 3, 2, 2, 1, 1, 1, 0,5 and 0,5 dB up to a margin of 10 dB; ISO
  10847 refuses under 4 dB and then takes off 2, 2, 1, 1, 1 and 1 dB up to the
  same margin. At a margin of 9 dB the first takes off 0,5 dB and the second
  1 dB. The signs differ as well, because the ISO 11820 column reads
  "corrections to be subtracted from sound pressure level measured with sound
  source operating" and prints its values positive, while the ISO 10847 column
  reads "correction to be made to the measured sound pressure level" and
  prints them negative. Neither is an erratum: they are two committees'
  tabulations of the same physical subtraction, rounded differently and
  written from opposite ends. Read on PDF page 13 (printed p. 5) of EN ISO
  11820:1996 and on PDF page 11 (printed p. 7) of ISO 10847:1997. The library
  keeps them apart as
  [`silencer_background_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_in_situ.py)
  and
  [`barrier_background_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py),
  each with its own sign convention and its own refusal, and a conformance
  check holds them against each other at the margin where they part. Do not
  merge them into one helper.
- **Beranek & Mellow 2e Table 7.1, the Delany and Bazley column:** the table
  prints $a_1$ to $a_4$ = 0.0511, 0.0768, 0.0858, 0.175 where
  [`DELANY_BAZLEY_COEFFICIENTS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/porous.py)
  holds $C_1$, $C_3$, $C_5$, $C_7$ = 0.0571, 0.087, 0.0978, 0.189 from Bies 5e
  Table D.1. The four amplitudes are 8 % to 14 % apart and the ratios are not
  constant (1.117, 1.133, 1.140, 1.080), so no single scale factor relates
  them. The reason is the variable. Beranek's Equation (7.11), printed above
  the table on the same page, is written in $R_f/f$ with **positive**
  exponents, while Delany and Bazley, and Bies after them, write
  $X = \rho_0 f / R_f$ with negative ones. The two forms differ by exactly
  $\rho_0^{\,b}$, and solving $C = a\,\rho_0^{\,b}$ row by row gives
  $\rho_0$ = 1.16, 1.19, 1.21, $1.14\ \text{kg/m}^3$, which is the density of air in
  every row; carrying the conversion the other way with $\rho_0$ = $1.18\ \text{kg/m}^3$
  reproduces the four printed amplitudes to 1.4 %, 0.4 %, 1.5 % and 2.1 %. The
  exponents agree independently: Beranek prints $b_1$ to $b_4$ = 0.75, 0.73,
  0.70, 0.59 against $C_2$, $C_4$, $C_6$, $C_8$ = 0.754, 0.732, 0.700, 0.595,
  the same numbers to two decimals. The control is the table's other column:
  Miki's variable is $f/\sigma$ and carries no density, and Beranek's Miki
  column, 0.070, 0.107, 0.109, 0.160 with 0.632, 0.632, 0.618, 0.618, agrees
  digit for digit with the constants `miki` is written from. Verified on PDF
  page 352 (printed p. 349) of Beranek & Mellow, *Acoustics: Sound Fields,
  Transducers and Vibration* 2e (2019), and on PDF page 757 (printed p. 728)
  of Bies, Hansen & Howard, *Engineering Noise Control* 5e (2017). Neither
  book is in error: they print one regression in two variables. The library
  follows Delany and Bazley through Bies, in $X = \rho_0 f/\sigma$, so its
  amplitudes must **not** be "corrected" towards Beranek's, which would apply
  the air density a second time.

- **IEC 60268-7:2010, "the standard reference frequency" beside the standard
  measuring frequency of 500 Hz:** 7.2 b) sets "the standard measuring
  frequency" at 500 Hz, and the NOTE of 8.3.3.1 gives the reason for the
  coupler, "to avoid the effects of diaphragm resonance, leakage and standing
  waves". The part also names "the standard reference frequency" (8.3.6.2 b),
  8.6.3.1, 8.6.4.1, 8.7.2.1, 8.9.1 a)) and never defines it; IEC 60268-1:1985,
  which Clause 2 cites, does, in Clause 3: "If a measurement relates to a
  reference frequency, then, in the absence of a clear reason to the
  contrary, this shall be the standard reference frequency of 1 000 Hz". The
  comparison methods begin and end their test sequence on "the band centred on
  1 kHz" (8.6.3.2 c), 8.6.4.2 c)), while Formula (1) of the ear canal method
  prints its own reference band, 500 Hz. The two terms are not always kept
  apart: 8.7.2.1 specifies the harmonic distortion "at the standard reference
  frequency" and 8.7.2.2 b) applies the voltage "at the standard measuring
  frequency". It is not registered as an erratum because each clause can be
  read as printed. Read on PDF page 11 (printed p. 9) of IEC 60268-1:1985 and
  on PDF pages 17, 21, 23, 26 to 29 and 31 (printed pp. 15, 19, 21, 24 to 27
  and 29) of IEC 60268-7:2010. The library refers the comparison responses of
  [`field_comparison_response`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  to 1 000 Hz by default, and the ear canal response and the coupler's
  relative response to 500 Hz; the conformance row "IEC 60268-7:2010 8.6.3.1
  with IEC 60268-1:1985 Clause 3" pins the default. Do not move the
  comparison responses to 500 Hz for uniformity.
