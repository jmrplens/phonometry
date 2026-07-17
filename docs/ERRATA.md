← [Documentation index](README.md)

# Errata found in published sources

During the clean-room implementation of this library, every formula, constant
and worked example is re-derived and recomputed independently from the source
documents. That process occasionally surfaces defects in the sources
themselves: misprints, worked examples that contradict their own normative
text, and ambiguous wording. This file records each confirmed case with the
evidence, what the library does about it, and whether it has been reported.

The registry covers every kind of published source the library implements
from: standards (ISO, IEC, EN), guidance documents and technical reports
(EASA, ECAC, NRL), textbooks and journal papers. Non-normative sources are
marked as such in their entry.

Entries describe the specific printed editions cited. A defect listed here is
not a defect of the method; in every case the intended reading could be
established from the document itself or from physics, and the library
implements that reading with a regression test pinning it.

Status legend: **unreported** (recorded here only) / **reported** (submitted
to the issuing body, with date and reference).

---

## ISO 717-2:2020 — Annex C, example C.1 (CI of the bare floor)

- **Location:** Annex C, Table C.1 and the accompanying CI computation.
- **The print:** the 2020 reprint states CI = −10 for the bare-floor example.
- **The problem:** its own normative clause A.2.1 defines CI from the energy
  sum over 100 Hz to 2500 Hz (the first fifteen one-third-octave bands). The
  2020 reprint's value only reproduces if the 3150 Hz band is included in the
  sum (83,5238 dB, rounded 84), contradicting A.2.1. The correct sum over
  100 to 2500 Hz is 83,2613 dB, rounded 83, giving CI = −11.
- **Evidence:** independent recomputation of both sums from the printed
  per-band levels; the 2013 edition of the same example prints CI = −11.
- **Library behaviour:** implements A.2.1 as written and pins CI = −11 with
  the 2013 print as the oracle ([`tests/reference_data.py`](../tests/reference_data.py),
  conformance check
  "ISO 717-2 Annex C, Table C.1").
- **Status:** unreported.

## ISO 717-2:2020 — Annex C, example C.2 (covered floor, 800 Hz value)

- **Location:** Annex C, Table C.2.
- **The print:** the 800 Hz value of the reference floor with covering is
  printed as 71,0 dB.
- **The problem:** the normative Table 4 reference floor minus the printed
  improvement at 800 Hz gives 71,5 dB; the 71,0 dB misprint propagates into
  the example's CI chain (yielding −8 where the normative-table chain gives
  −9).
- **Evidence:** independent recomputation from Table 4 and the printed
  improvement spectrum.
- **Library behaviour:** derives the covered floor from the normative Table 4
  values; the conformance check notes the provenance explicitly.
- **Status:** unreported.

## ISO 2631-5:2018 — Annex C, NOTE 5 (female worked example)

- **Location:** Annex C, NOTE 5 (64 kg female, mz = 0,025 MPa/(m/s²)).
- **The print:** R = 0,97.
- **The problem:** exact recomputation of Formula (C.3) with the note's own
  inputs (mz = 0,025, age coefficient 0,039, b = 20, n = 20, N = 120) gives
  R = 0,9621, which rounds to 0,96. The same code reproduces the male example
  exactly (R = 1,2200 = printed 1,22), and the note's Sd = 1,40 MPa matches
  the exact 1,3992, so the discrepancy is confined to the last digit of the
  printed female R.
- **Evidence:** hand recomputation of the C.3 sum, term by term.
- **Library behaviour:** computes the exact value; the test anchor keeps the
  printed 0,97 with a tolerance that documents the recomputed 0,9621.
- **Status:** unreported.

## EN 12354-1:2000 Annex E.5 / ISO 12354-1:2017 E.3.4 (K24 clamp misprint)

- **Location:** EN 12354-1:2000, Annex E, clause E.5, and ISO 12354-1:2017,
  E.3.4 NOTE 4 (wall junction with flexible interlayers).
- **The print:** the bound on the K24 junction term is printed as
  "0 ≤ K24 ≤ −4 dB", an empty interval; the 2017 edition repeats the 2000
  misprint verbatim.
- **The problem:** the interval is impossible as printed; the accompanying
  figure and the physics (the term is a reduction bounded below) indicate
  −4 dB ≤ K24 ≤ 0 dB.
- **Evidence:** page render of the printed clause; corroboration against the
  figure's curve family.
- **Library behaviour:** implements the clamp as −4 ≤ K24 ≤ 0 with a misprint
  note in the docstring.
- **Status:** unreported.

## ISO 12354-1:2017 — E.3.5 (double-leaf junction K24 sign)

- **Location:** E.3.5, Figure E.7 (junction of lightweight double leaf wall
  and homogeneous elements), K24 formula.
- **The print:** K24 = 3,0 + 14,1 M + 5,7 M² dB (for m2/m1 > 3).
- **The problem:** EN 12354-1:2000 prints the same relation as
  K24 = 3,0 − 14,1 M + 5,7 M² (Figure E.9, Formula (E.7)), and the 2000
  edition's own K24 curve in that figure decreases with m2/m1, corroborating
  the minus sign; the 2017 edition prints no corresponding curve. The two
  editions contradict each other and the internally consistent
  formula-plus-figure pair is the 2000 one.
- **Evidence:** page renders of both editions (ISO 12354-1:2017 printed
  p. 47; EN 12354-1:2000 printed p. 48).
- **Library behaviour:** implements the 2000 edition it cites (minus sign),
  with a code note recording the 2017 contradiction.
- **Status:** unreported.

## EN 12354-2:2000 — Formula (3) vs Annex E.3 (standardized impact level)

- **Location:** Formula (3) and worked example E.3.
- **The print:** Formula (3) defines L'nT = L'n − 10 lg(0,16·V/(A0·T0)), which
  reduces exactly to L'n − 10 lg(0,032·V), i.e. a reference volume of
  31,25 m³. Annex E.3 states "from equation (3): L'nT,w = L'n,w − 10 lg(V/30)".
- **The problem:** the annex's V/30 is a rounding of the formula's own
  constant; the two differ by a constant 0,177 dB.
- **Evidence:** direct algebra; both variants recomputed for the E.3 case
  (42,959 vs 42,782 dB, both rounding to 43 in that example).
- **Library behaviour:** implements the exact 0,032·V form and documents the
  annex's rounding.
- **Status:** unreported.

## EN 12354-3:2000 — Annex F (worked example internal inconsistencies)

- **Location:** Annex F worked example.
- **The print:** (a) the printed D2m,nT row equals R' + 1,5 dB; (b) the
  printed high-frequency-band row is inconsistent with the example's own
  partial indices.
- **The problem:** Formula (13) with the example's own inputs (V = 50 m³,
  S = 11,3 m², T0 = 0,5 s) gives D2m,nT = R' + 1,69 dB, not +1,5 dB; and the
  high-band row cannot be reproduced from the example's stated partial
  results (the self-consistent values are 35,8/38,0 dB).
- **Evidence:** recomputation of Formula (13) and of the partial-index chain.
  The example's single-number result D2m,nT,w = 33 dB is insensitive to both
  and still reproduces.
- **Library behaviour:** implements Formula (13); the test data notes both
  inconsistencies next to the affected anchors.
- **Status:** unreported.

## ISO 12999-1:2020 — Table 4 (missing 500 Hz row)

- **Location:** Table 4 (in-situ uncertainties per band).
- **The print:** the 2020 edition's table omits the 500 Hz row that the 2014
  edition prints (situation B 1,2 dB / situation C 0,8 dB).
- **The problem:** likely an editorial omission; the surrounding rows are
  unchanged between editions and the text does not mention removing the band.
- **Evidence:** side-by-side comparison of the 2014 and 2020 prints.
- **Library behaviour:** follows the 2020 print as published, with the
  omission documented in the module.
- **Status:** unreported.

## ISO 12999-2:2020 — Clause 8 wording vs Tables 4 and 5

- **Location:** Clause 8 (expression of results) and Tables 4/5.
- **The print:** the clause wording instructs rounding the standard
  uncertainty u before forming the expanded uncertainty U = k·u.
- **The problem:** the document's own Tables 4 and 5 only reproduce when U is
  computed from the unrounded u and rounded last; the literal clause wording
  fails half of the printed table entries.
- **Evidence:** recomputation of all 25 table entries under both conventions
  (round-last: 25 of 25 match; round-first: 10 of 20 mismatch).
- **Library behaviour:** rounds last, matching the tables; the convention is
  documented and tested.
- **Status:** unreported.

## ISO 10052:2021 — Table 4 volume-range header

- **Location:** Table 4 (reverberation-index estimator), volume-range header.
- **The print:** the header reads "60 ≤ V < 150" while the body text says the
  method applies to rooms "up to 150 m³".
- **The problem:** the boundary V = 150 m³ is included by the text and
  excluded by the header.
- **Evidence:** direct comparison of header and clause text.
- **Library behaviour:** accepts V = 150 (follows the text), with the
  ambiguity noted.
- **Status:** unreported.

## ISO 17208-2:2019 — Clause 5 uncertainty band coverage

- **Location:** Clause 5 (representative expanded uncertainties).
- **The print:** 5 dB for the low-frequency bands (10 Hz to 100 Hz), 3 dB for
  the mid-frequency bands (125 Hz to 16 000 Hz), 4 dB for the high-frequency
  bands (above 20 000 Hz).
- **The problem:** the band list leaves the 20 kHz one-third-octave band
  unassigned (nothing covers 16 kHz to 20 kHz inclusive).
- **Evidence:** the clause's own enumeration.
- **Library behaviour:** applies the conservative 4 dB high-band value from
  just above 16 kHz, with the gap documented.
- **Status:** unreported.

## ECMA-418-1:2024 (3rd edition) — clause 4.1.2 (upper limit of the range of interest)

- **Location:** clause 4.1.2, the stated frequency range of interest for
  discrete tones.
- **The print:** "between 89,1 Hz and 11 220 Hz inclusive".
- **The problem:** every formula and table of the standard uses 11 200 Hz:
  the Table 2/3 band-edge fits end at 11 200 Hz, and Formulae (13)/(26)
  treat the upper end of the criterion range consistently with 11 200 Hz.
  No other clause mentions 11 220 Hz.
- **Evidence:** cross-check of the clause 4.1.2 prose against Tables 2 and 3
  and the criterion formulas of clauses 11.5/12.6.
- **Library behaviour:** uses the internally consistent 89,1 Hz to
  11 200 Hz range (upper end exclusive per the formulas), with a code note
  in [`tonality.py`](../src/phonometry/psychoacoustics/tonality.py).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition) — clause 5.1.5.2 (last block index)

- **Location:** clause 5.1.5.2, the segmentation of the zero-padded signal
  for the roughness/fluctuation-strength block sizes.
- **The print:** the index of the last block is given as
  l_last = ceil((n + s_b)/s_h).
- **The problem:** the formula is internally inconsistent: blocks placed at
  that index overrun the zero-padded signal defined by clause 5.1.2.2, and
  the resulting Formula (103) time grid becomes non-monotonic. The only
  self-consistent reading is to stop at the last block that fits inside the
  padded signal and align it flush with its end.
- **Evidence:** direct evaluation of the block start indices against the
  padded length for the clause 7.1.1 block/hop sizes; the flush-to-end
  reading reproduces the Clause 7 roughness calibration (1 asper) to
  0,9999.
- **Library behaviour:** implements the flush-to-end reading with a code
  note in [`roughness_ecma.py`](../src/phonometry/psychoacoustics/roughness_ecma.py).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition) — clause 9.1.4, Formula (127) (HSA kernel phase)

- **Location:** clause 9.1.4, Formula (127), the spectral kernel of the
  envelope analysis window used by the High-resolution Spectral Analysis.
- **The print:** the kernel's phase factor is
  exp(−j·2π·f_n(k)·(s̃_b − n_ze + n_zb − 1)).
- **The problem:** the kernel is, by construction, the DFT of the
  rectangular analysis window of Formula (120) modulated to the candidate
  rate — that is the model Formula (124) fits to the measured DFT spectrum.
  That DFT has the phase exp(−j·π·f_n·(s̃_b − n_ze + n_zb − 1)); the
  printed factor doubles it (and is also inconsistent with the π arguments
  of the printed sine terms of the same formula). With the printed phase
  the fitted model cannot reproduce the spectrum of a noiseless windowed
  sinusoid, contradicting the clause's own statement that the HSA achieves
  "theoretically infinite resolution for signals without noise".
- **Evidence:** independent derivation of the window DFT plus numerical
  recomputation: with π the least-squares fit recovers the constant part,
  amplitudes and phases of synthetic noiseless envelopes to machine
  precision and the Formula (135) residual vanishes; with the printed 2π
  the kernel deviates from the window DFT by amounts of the order of the
  kernel itself and the residual stays of the order of the signal energy.
- **Library behaviour:** implements the π reading, pinned by a regression
  test on the exact recovery of synthetic line pairs.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition) — clause 9.1.5, Formula (144) (bin offset)

- **Location:** clause 9.1.5, Formula (144), the modulation rate of a local
  maximum of the envelope power spectrum.
- **The print:** the rate is the three-bin amplitude-weighted centroid of
  the peak position **minus one**, scaled by Δf.
- **The problem:** clause 9.1.4 (below Formula (122)) defines the spectral
  index k as mapping to the modulation rate k·r̃_s/s̃_b with k starting at
  0. A symmetric local maximum at bin k has centroid k, and the printed
  formula then assigns it the rate (k − 1)·Δf — one full bin (0,73 Hz) low,
  which at fluctuation-strength rates is fatal (a true 1,46 Hz modulation
  would be reported as 0,73 Hz). The offset is only consistent with
  1-based spectral-line positions, contradicting the standard's own
  definition of k.
- **Evidence:** cross-check of Formula (144) against the k-to-rate mapping
  stated below Formula (122).
- **Library behaviour:** uses the centroid directly (no offset) with the
  0-based k of Formula (122).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition) — clause 9.1.7 (units of the fine-tuning constants)

- **Location:** clause 9.1.7, Formulae (149)-(152), the damped Newton fine
  tuning of the dominant modulation rate.
- **The print:** differential step Δx = 10⁻⁵, damped-step cap 2·10⁻⁴, stop
  tolerance 10⁻⁷ and an iteration limit of 40, with the starting point
  x₀ = f̃_c,imax (a rate in Hz) and the failure check
  |f_c,1,opt − f̃_c,imax| > 1,25·Δf.
- **The problem:** the constants carry no units. Read in Hz, the damped
  step is capped at 5·10⁻⁵ Hz per iteration (2·10⁻³ Hz over all 40
  iterations), so the tuning cannot move appreciably and the 1,25·Δf
  (≈ 0,92 Hz) failure check is unreachable — the whole clause would be
  inert. Read as normalized modulation rates f/r̃_s (the variable in which
  the Formula (127) kernel frequencies are expressed), the same constants
  give a 0,075 Hz damped per-iteration cap (≈ 2,9 Hz over the 39
  iterations), a 1,5·10⁻⁴ Hz stop tolerance and a reachable failure check,
  all consistent with the clause's purpose.
- **Evidence:** dimensional analysis of the printed constants against the
  0,7324 Hz spectral resolution and the failure threshold.
- **Library behaviour:** applies the constants as normalized modulation
  rates.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition) — clause 9 introduction (broken cross-reference)

- **Location:** clause 9, third paragraph of the introduction, on the
  HSA-based loudness prediction.
- **The print:** "loudness scaling is improved by using HSA-based loudness
  prediction (see Clause 0)".
- **The problem:** "Clause 0" does not exist; the HSA-based loudness
  scaling is described in clause 9.1.10 (an unresolved field reference).
- **Evidence:** the clause listing of the standard itself.
- **Library behaviour:** none required (the intended target is
  unambiguous).
- **Status:** unreported.

## ISO/PAS 20065:2016 — clause 5.3.4 (edge steepness of a distinct tone)

- **Location:** clause 5.3.4, Formulae (10)/(11), the minimum edge steepness
  of a distinct tone.
- **The print:** asymmetric formulas — the lower-edge steepness is scaled by
  f_T/2 and the upper-edge steepness by f_T (no divisor).
- **The problem:** the parent standard DIN 45681:2005-03 prints f_T/sqrt(2)
  on **both** edges, and its executable Annex J reference program does the
  same (`Frequenz(i)/Sqr(2)`). The two prints cannot both be satisfied; the
  ISO version is plausibly a typesetting corruption of the sqrt(2) factor
  (the radical dropped on one edge and halved on the other). Versus the DIN
  program the ISO print is sqrt(2) more lenient on the lower edge and
  sqrt(2) stricter on the upper; borderline tones with one-sided edge
  steepness around 17 to 34 dB/octave flip classification between the two
  readings.
- **Evidence:** side-by-side comparison of the ISO print, the DIN 45681
  print and the DIN Annex J program.
- **Library behaviour:** follows the DIN/sqrt(2) reading (it matches the
  only executable reference), with the choice recorded in
  [`tone_audibility.py`](../src/phonometry/psychoacoustics/tone_audibility.py).
- **Status:** unreported.

## DIN 45681:2005-03 — Anhang I, Tabelle I.6, row "6 FG"

- **Location:** Anhang I, Beispiel I.2 (combustion engine, spectrum j = 1),
  Tabelle I.6, the combined row "6 FG" for the three tones k = 6/7/8
  (592,2 / 629,8 / 643,3 Hz, tone levels 78,31 / 75,00 / 79,75 dB).
- **The print:** L_T = 81,11 dB together with delta L = 9,12 dB (with
  L_S = 59,53, L_G = 76,16, a_v = -2,40 at 592,2 Hz).
- **The problem:** the two cells contradict each other. The printed
  delta L = 9,12 dB only reproduces from the *plain* Formula (17) energy sum
  of the three tone levels (82,87 dB): 82,87 - 76,16 + 2,40 = 9,11. The
  printed L_T = 81,11 dB is consistent instead with the Anmerkung 2
  shared-line dedupe (the 629,8/643,3 Hz tonal runs overlap), which would
  give delta L = 7,35 dB. Every other FG row of the annex is internally
  consistent (e.g. "2 FG": L_T = 72,15, delta L = 9,18, both from the same
  sum — no lines shared there).
- **Evidence:** recomputation of both readings from the printed per-tone
  levels of Tabelle I.6; the same-page "2 FG" row as the consistent control.
- **Library behaviour:** `combined_tone_level` follows Anmerkung 2 (shared
  lines counted once), which reproduces the printed "2 FG" oracle; for the
  "6 FG" row only the delta L chain is pinned, with the contradiction
  recorded in `tests/reference_data.py`.
- **Status:** unreported.

## IEC 60268-3:2013 — clause 14.12.9.2 f) (DIM denominator)

- **Location:** clause 14.12.9.2, item f), the formula for the dynamic
  intermodulation distortion d_DIM.
- **The print:** the denominator of the printed formula is "U2".
- **The problem:** the defining clause 14.12.9.1 states the ratio of the
  r.m.s. sum of the Table 2 intermodulation product voltages "to the
  amplitude of the output voltage at the frequency f_s" — i.e. the 15 kHz
  sine component U_s, the Otala convention. The symbol U2 is used throughout
  14.12 for the total output voltage, which contradicts 14.12.9.1 (the test
  signal is dominated by the 3,15 kHz square wave, so the two denominators
  differ by several dB). Item d) of the same clause measures "the amplitudes
  of the sinusoidal signal U_s", which the f) formula then never uses.
- **Evidence:** side-by-side reading of 14.12.9.1, 14.12.9.2 d) and
  14.12.9.2 f); the historical DIM literature (Otala) defines the ratio to
  the sine amplitude.
- **Library behaviour:** follows the 14.12.9.1 definition (reference = the
  output amplitude at f_s), with a code comment at the reference measurement
  in [`distortion.py`](../src/phonometry/electroacoustics/distortion.py).
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06) — Eq. (27)

- **Location:** section A.4.2, Eq. (27) (atmospheric absorption coefficient).
- **The print:** the coefficient 6,6928·10⁻⁶ is paired with the relaxation
  frequency frO = 630,7 Hz.
- **The problem:** evaluated as printed, the equation yields nonsense
  (14,3 dB/km at 500 Hz against the guidance's own Table 4 value of 3,1).
  The physically correct pairing (6,6928·10⁻⁶ with the oxygen relaxation
  frequency, about 75 692 Hz at the reference conditions, and 1,3415·10⁻⁶
  with 630,7 Hz) reproduces Table 4 and the ISO 9613-1 pure-tone coefficient
  to 0,02 dB/km.
- **Evidence:** numeric evaluation of both pairings against Table 4.
- **Library behaviour:** implements the correct pairing; the module docstring
  carries a defensive note so the misprint is not transcribed as a "fix".
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06) — Eq. (21)

- **Location:** section A.3.3, Eq. (21) (flight path angle).
- **The print:** γ = acos(ΔZ/ΔS).
- **The problem:** the arccosine of the climb-to-path ratio returns the
  complement of the path angle (90° in level flight, where γ must be 0°) and
  contradicts the guidance's own use of γ as the climb/descent angle
  throughout section A.3. ECAC Doc 32, 1st ed., Eq. (10) prints the correct
  form, γ = atan(ΔZ/ΔS) with the horizontal ΔS of its Eq. (8).
- **Evidence:** evaluation in level flight; cross-check against Doc 32
  Eq. (10) and against the NORAH2 prototype input files, whose ``Vang``
  columns are climb/descent angles (0° in level segments).
- **Library behaviour:** ``flight_path_kinematics`` implements the Doc 32
  ``atan`` form; the result docstring carries the defensive note.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06) — §A.3.1 triangulation

- **Location:** section A.3.1, steps 2 to 4 (flight-condition interpolation),
  against the triangulation lookup tables shipped with the NORAH2 database
  (``*_triangulation.int``).
- **The print:** steps 2 and 3 normalise the database conditions (spans, with
  F_fc = 2 on the path angle) and step 4 computes "the Delaunay triangulation
  for the database flight conditions γ̄_j and V̄_j", i.e. of the normalised
  points, offering a lookup table as an equivalent.
- **The problem:** the lookup tables shipped with the database (which the
  guidance says are part of the hemisphere data and should not be edited) are
  the Delaunay triangulation of the raw (V, γ) conditions, not of the
  normalised ones: for the R22 set, 14 of the 27 shipped triangles differ
  from the Delaunay triangulation of the normalised conditions. A Delaunay
  triangulation is not invariant under the anisotropic normalisation, so the
  two prescriptions select different enveloping triangles for part of the
  envelope. The distance weights of Eq. (7)/(8) do use the normalised
  coordinates in the prototype (verified against its blended outputs).
- **Evidence:** recomputation of both triangulations for the R22 database;
  bin-for-bin reproduction of the prototype's per-step hemisphere selection
  with the shipped tables, and of its blended levels with normalised-space
  weights, to 0,05 dB.
- **Library behaviour:** ``flight_condition_weights`` follows the printed
  method (Delaunay of the normalised conditions) by default and accepts the
  database lookup table via ``triangles``, which reproduces the reference
  implementation exactly.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06) — Eq. (46)

- **Location:** section A.4.5, Eq. (46) (source-side ground effect weighted
  by diffraction).
- **The print:** the weighting exponent reads (ΔL_g,s′ − ΔL_d,s)/20.
- **The problem:** no term ΔL_g,s′ exists; the prose directly below the
  equation defines ΔL_d,s′ as "the attenuation due to the diffraction between
  the image source S′ and R", the receiver-side companion Eq. (47) prints the
  parallel term correctly as ΔL_d,r′, and the CNOSSOS-EU method the section
  is based on writes Δ_ground(S,O) with Δ_dif(S′,R) in that position. The
  subscript g is a misprint for d.
- **Evidence:** internal consistency of the section (its own prose and
  Eq. (47)) and the CNOSSOS-EU source of the equations.
- **Library behaviour:** implements the image-source diffraction term
  ΔL_d,s′ as defined by the prose.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06) — §A.4.5 cross-references

- **Location:** section A.4.5, the definitions under Eq. (46) and Eq. (47).
- **The print:** ΔL_d,s′, ΔL_d,s and ΔL_d,r′ are said to be "calculated as
  per eq. 44" (four occurrences: two under Eq. (46) and two under Eq. (47)).
- **The problem:** Eq. (44) is the multiple-diffraction coefficient C″; the
  attenuation due to diffraction is Eq. (42). The three cross-references point
  at the auxiliary coefficient instead of the formula they describe.
- **Evidence:** the terms are attenuations in dB, which only Eq. (42)
  produces; Eq. (44) is a dimensionless coefficient consumed by Eq. (42).
- **Library behaviour:** evaluates the image-path and direct diffraction
  terms with Eq. (42), using Eq. (44) for C″ inside it.
- **Status:** unreported.

## RANDI 3.1 Physics Description (NRL, Breeding et al.) — Table 2

- **Location:** Table 2 (representative ship source levels).
- **The print:** two cells deviate from the report's own Eqs. (2) to (5)
  evaluated with the Table 1 average lengths and speeds: the Merchant value
  at 25 Hz (about 3 dB high) and the Tanker value at 300 Hz (about 1 dB low).
  The Fishing Vessel row is not reproducible from the Table 1 averages at
  all (a constant offset of about 3,8 dB suggests different assumed inputs).
- **The problem:** the report does not state the exact inputs used for
  Table 2, and two cells contradict its own equations while every Large
  Tanker and Super Tanker cell agrees to 0,06 dB.
- **Evidence:** recomputation of all 25 cells from Eqs. (2) to (5).
- **Library behaviour:** the regression test pins the reproducible rows and
  excludes the contradicting cells with the rationale in the test.
- **Status:** unreported (technical report rather than a standard).

## Osses, García & Kohlrausch (2016), fluctuation-strength model — Eq. (3)

- **Location:** Eq. (3), the critical-band-rate (Bark) transformation of the
  excitation-pattern front-end.
- **The print:** z(f) = 13·arctan(0,76·10⁻⁴·f) + 3,5·arctan((f/7500)²).
- **The problem:** the first coefficient is the Zwicker-Terhardt 0,76·10⁻³
  with the exponent misprinted. The paper's own anchors disprove the print:
  it states 0,5 Bark = 50 Hz and 23,5 Bark = 13,2 kHz (section 2.1.2) and
  15 Bark = 2,7 kHz (section 3.1), all of which require 10⁻³. With 10⁻⁴,
  z(1 kHz) = 1,05 instead of 8,51 Bark and the model's 47 filter centres
  would span 491 Hz to 20 kHz instead of 50 Hz to 13,2 kHz.
- **Evidence:** evaluation of Eq. (3) under both exponents against the
  paper's printed Bark/frequency anchors.
- **Library behaviour:** implements 0,76·10⁻³ with a note at the formula;
  the carrier-frequency sweep test would catch a regression to the printed
  value ([`fluctuation_strength.py`](../src/phonometry/psychoacoustics/fluctuation_strength.py)).
- **Status:** unreported (conference paper rather than a standard).

## Medwin & Clay, Fundamentals of Acoustical Oceanography (1998) — Eq. 3.4.29

- **Location:** the Francois-Garrison boric-acid term as transcribed by the
  textbook (Eq. 3.4.29).
- **The print:** the boric-acid factor is printed as A1 = (8,68/c)·10^(0,78 pH − 5).
- **The problem:** the original paper (Francois & Garrison 1982, JASA 72,
  Part II, Eq. (10) and Fig. 7) prints 8,86; the digits are transposed. Only
  8,86 reproduces the paper's own Table IV: with 8,68 the boric-dominated
  cells at 0,6 to 30 kHz sit up to 1,7 % below the printed totals (worst
  relative case 2 kHz, 10 °C, S = 35: 0,1209 vs the printed 0,123 dB/km).
- **Evidence:** recomputation of all sampled Table IV cells under both
  coefficients against the paper's printed values.
- **Library behaviour:** implements the paper's 8,86 with a defensive note;
  the pinned Table IV set includes the boric-dominated rows.
- **Status:** unreported (textbook rather than a standard).

---

## Related source properties that are not errata

Recorded here to prevent future "fixes" that would break agreement with the
published sources:

- **Francois-Garrison pure-water term:** the two published A3 cubics do not
  meet exactly at the 20 °C switch (a step of 1·10⁻⁷·f² dB/km, 0,1 dB/km at
  1 MHz). Inherent in the published coefficients.
- **Ainslie-McColm simplification:** the paper's "within 10 % of
  Francois-Garrison" claim is marginally exceeded at the extreme corners of
  its stated domain (10,4 % at −6 °C / 1 MHz; 12,3 % at 7 km depth). A
  property of the published fit; both transcriptions verified digit-for-digit.
- **ICAO Annex 16 EPNL constant:** the Annex's rounded constant 13 for
  uniform 0,5 s records differs from the exact −10·lg(T0) form by 0,0103 dB;
  the library uses the exact form, which the ETM's integrated reference
  reproduces to five decimals.
