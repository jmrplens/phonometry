---
title: "Errata in published sources"
description: "Defects found in the standards, guidance documents and textbooks the library implements from: misprints, worked examples that contradict their own clauses, and what the library does about each one."
---

Implementing a standard clean-room means re-deriving every formula, constant
and worked example from the source document rather than from anyone else's
code. Done across hundreds of documents, that process finds defects in the
sources themselves: a worked example that contradicts its own normative
clause, a constant with a digit dropped in typesetting, a cross-reference that
points at the wrong equation.

This page is the registry of those findings. Each entry names the printed
edition and the exact location, quotes what the document says, shows why it
cannot be right, gives the independent evidence, and states which reading the
library implements and which regression test pins it. A defect listed here is
never a defect of the *method*: in every case the intended reading could be
established from the document itself or from physics.

Read it alongside the [conformance report](/phonometry/reference/conformance/),
which shows the numbers the library computes; this page explains the handful of
places where the printed expected value is the thing that is wrong.

The registry is maintained in
[`docs/ERRATA.md`](https://github.com/jmrplens/phonometry/blob/main/docs/ERRATA.md)
and transplanted here at build time by `make site-reports`, so the two cannot
disagree.

<!-- BEGIN GENERATED BODY - transplanted from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never the text below. -->

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
implements that reading. Where the reading changes a number the library
reports, the entry names the check or test that pins it; where the defect is a
label, a cross-reference or a table the library never reads, the entry records
that no change was required.

Status legend: **unreported** (recorded here only) / **reported** (submitted
to the issuing body, with date and reference).

A claim that turns on the exact characters of a formula, constant,
coefficient, symbol, inequality or table cell is verified against **the page
as printed**, and its Evidence bullet cites that page by PDF page index and
printed folio. Extracted text may locate a page; it is never quoted as "the
print", because PDF text layers delete glyphs silently (most of the sources
cited here emit no `√` at all, so `f_T/√2` extracts as `f_T/2`). The page
offset of each document is established empirically, because it differs per
document and drifts between chapters of the same book. Entries that rest on
something else, a recomputation or a comparison of two sentences, say so
either in a leading notice or on the allowlist of
[`scripts/check_errata_evidence.py`](https://github.com/jmrplens/phonometry/blob/main/scripts/check_errata_evidence.py),
which is the check that enforces the rule; see
[CONTRIBUTING.md](https://github.com/jmrplens/phonometry/blob/main/CONTRIBUTING.md#6-filing-an-errata-entry).

A Spanish edition of this registry, translated entry for entry, is maintained
in [ERRATA.es.md](https://github.com/jmrplens/phonometry/blob/main/docs/ERRATA.es.md). The wording here is the authoritative one,
and quoted print, mathematics and printed values are reproduced there
untranslated; `make site-reports` holds the two editions to the same entries
in the same order.


---

## ISO 717-2:2020, Annex C, example C.1 (CI of the bare floor)

- **Location:** Annex C, Table C.1 (printed p. 17) and the accompanying $C_I$
  computation printed in the same cell.
- **The print:** $L_{n,\text{sum}} = 83{,}523\,8\ldots = 84\ \text{dB}$ and
  $C_I = 84 - 15 - 79 = -10\ \text{dB}$ for the bare-floor example.
- **The problem:** two independent defects in the same cell. (a) Clause A.2.1
  defines $C_I$ from the energy sum over 100 Hz to 2500 Hz (the first fifteen
  one-third-octave bands); the printed value only reproduces if the 3150 Hz
  band is included, contradicting A.2.1. The correct sum over 100 Hz to 2500
  Hz is 83,2613 dB, rounded 83, giving $C_I = -11$. (b) Even read as the
  sixteen-band sum the printed digits are wrong in the last place: the
  bare-floor $L_n$ column sums to 83,523 4 dB, not the printed 83,523 **8**
  dB. The defect is confined to that cell, since the with-covering column of
  the same table prints $L_{n,\text{sum}} = 76{,}059\,3\ldots$ and recomputes
  to 76,059 29 dB, reproducing every printed digit. Neither (a) nor (b)
  changes the rounded 84 dB, so only (a) moves $C_I$.
- **Evidence:** independent recomputation of both sums from the printed
  per-band levels (16 bands 83,523 38 dB, 15 bands 83,261 27 dB, with-covering
  16 bands 76,059 29 dB); the 2013 edition of the same example prints
  $C_I = -11$. Verified on PDF page 23 (printed p. 17) and PDF page 17
  (printed p. 11) of ISO 717-2:2020, and of PDF page 22 (printed p. 14) of ISO
  717-2:2013.
- **Library behaviour:** implements A.2.1 as written and pins $C_I = -11$ with
  the 2013 print as the oracle
  ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data), conformance check
  "ISO 717-2 Annex C, Table C.1").
- **Status:** unreported.

## ISO 717-2:2020, Annex C, example C.2 (covered floor: 800 Hz value and CI chain)

- **Location:** Annex C, Table C.2 (printed p. 18), the $\Delta L_w$ /
  $\Delta L_\text{lin}$ worked example.
- **The print:** (a) the 800 Hz reference-floor value is printed as 71,0 dB;
  (b) the $C_I$ line prints
  $L_{n,\text{sum}} = 75{,}252\,7\ldots = 75\ \text{dB}$ and
  $C_I = 75 - 15 - 63 = -3\ \text{dB}$, feeding
  $\Delta L_\text{lin} = 78 - 11 - (63 - 3) = 7\ \text{dB}$.
- **The problem:** two independent defects. (a) The normative Table 4
  reference floor is 71,5 dB at 800 Hz, and the column itself is a clean +0,5
  dB per one-third octave ramp from 67,0 dB at 100 Hz to 72,0 dB at 1000 Hz,
  which the printed 71,0 dB breaks by repeating the 630 Hz cell. The misprint
  propagates along its own row and into the table's total, three further cells
  the table prints and this entry previously did not name: the
  $L_{n,r,0} - \Delta L$ cell at 800 Hz is printed 64,0 dB
  ($= 71{,}0 - 7{,}0$) where 71,5 gives 64,5; the unfavourable deviation is
  printed 3,0 dB ($= 64{,}0 - 61$) where the corrected cell gives 3,5; and the
  printed `Sum 27,9` is the sum of the thirteen unfavourable deviations
  including that 3,0, where the corrected chain gives 28,4. None of it moves
  the rating: 28,4 dB is still below the 32,0 dB shift criterion, so
  $L_{n,w,r} = 63\ \text{dB}$ and $\Delta L_w = 15\ \text{dB}$ either way. (b)
  The printed 75,2527 dB is exactly the energy sum of the *wrong column over
  the wrong range*: the measured floor "with covering" over all sixteen bands
  100 Hz to 3150 Hz. A.2.1 defines $C_I$ from the reference floor with
  covering (the $L_{n,r,0} - \Delta L$ column) over 100 Hz to 2500 Hz (15
  bands), which gives 75,674 dB (printed chain) or 75,710 dB (corrected 800 Hz
  cell), both round to 76 dB, so $C_{I,r} = 76 - 15 - 63 = -2$ either way,
  giving $C_{I,\Delta} = -11 - (-2) = -9$ and
  $\Delta L_\text{lin} = 6\ \text{dB}$, not the printed −3 / −8 / 7 dB chain.
- **Evidence:** independent recomputation of every candidate sum and of every
  cell of the 800 Hz row from the printed per-band values; the printed 75,2527
  reproduces to all printed digits only as the 16-band sum of the
  with-covering column, and every other cell of the $L_{n,r,0} - \Delta L$ and
  deviation columns reproduces exactly from the printed reference floor, so
  the 800 Hz row is the only one that does not. Verified on PDF page 24
  (printed p. 18) and PDF page 13 (printed p. 7) of ISO 717-2:2020.
- **Library behaviour:** derives the covered reference floor from the
  normative Table 4 values and sums per A.2.1, pinning
  $\Delta L_w = 15\ \text{dB}$ and $C_{I,\Delta} = -9$; the conformance check
  notes the provenance explicitly.
- **Status:** unreported.

## ISO 2631-5:2018, Annex C worked examples (male displayed formula, female R)

- **Location:** Annex C: the displayed male worked example (82 kg male,
  $m_z = 0{,}029\ \text{MPa}/(\text{m/s}^2)$, printed p. 19) and NOTE 5 (64 kg
  female, $m_z = 0{,}025\ \text{MPa}/(\text{m/s}^2)$, printed p. 20).
- **The print:** (a) the male example is displayed as

  $$
  R = \left\{ \sum_{i=0}^{20-1}
  \left[ \frac{1{,}62\ \text{MPa}\,(120)^{1/6}}
  {6{,}75\ \text{MPa} - 0{,}052\ \text{MPa}\,(20+i)} \right]^{6}
  \right\}^{1/6} \approx 1{,}22
  $$

  and (b) NOTE 5 states $R = 0{,}97$ for the female case.
- **The problem:** two independent defects. (a) The displayed male formula
  omits the $-S_{\text{stat},i}$ term that normative Formula (C.3) puts in the
  denominator, and that the same annex fixes at
  $S_\text{stat} = 0{,}029 \cdot 9{,}81 = 0{,}281\ \text{MPa}$ in the sentence
  that follows the where-list of Formula (C.3). Evaluated exactly as displayed
  the sum gives $R = 1{,}1497$, which prints as 1,15, not the printed 1,22;
  restoring the missing term gives 1,2168 with the printed
  $S_\text{stat} = 0{,}281\ \text{MPa}$ and 1,2177 with the exact
  $m_z \cdot 9{,}81 = 0{,}2845\ \text{MPa}$, i.e. the printed 1,22 either way.
  The printed *result* is therefore right and the printed *formula* is not.
  (b) Exact recomputation of Formula (C.3) with NOTE 5's own inputs
  ($m_z = 0{,}025$, age coefficient 0,039, $b = 20$, $n = 20$, $N = 120$)
  gives $R = 0{,}9621$, which rounds to 0,96; the same code reproduces the
  male example exactly, and the note's $S_d = 1{,}40\ \text{MPa}$ matches the
  exact 1,3992, so the discrepancy is confined to the last digit of the
  printed female $R$.
- **Evidence:** term-by-term recomputation of the C.3 sum under both readings
  of the denominator, with the male example as the discriminator: the printed
  1,22 is reachable only with $-S_\text{stat}$, and 1,15 only without it.
  Verified on PDF pages 23 (printed p. 17), 24 (printed p. 18), 25 (printed p.
  19) and 26 (printed p. 20) of ISO 2631-5:2018.
- **Library behaviour:** implements Formula (C.3) as written, with
  $-S_\text{stat}$; the male anchor pins 1,22 and the female test anchor keeps
  the printed 0,97 with a tolerance that documents the recomputed 0,9621.
- **Status:** unreported.

## Ainslie (2010), Equation (4.6) vs its own folio 177, and the exponent of Equation (4.13)

- **Location:** *Principles of Sonar Performance Modelling* (Springer 2010),
  Equation (4.6) on printed folio 127; the sea-water density quoted in
  Section 4.4 on printed folio 177; Equation (4.13) on printed folio 135.
- **The print:** Equation (4.6) gives the density of sea water as
  $\hat\rho = 1027 + 4{,}3\times10^{-7}\hat P_\mathrm{w} + 0{,}75[S-35] -
  0{,}16[\hat T-10] - 0{,}004[\hat T-10]^2$, attributed to Pierce (1989,
  p. 34), with the units fixed by Equations (4.7) to (4.10) on folio 128:
  pressure in pascals, temperature in degrees Celsius, density in kg/m³.
  Equation (4.4) on folio 127 defines that pressure as
  $P_\mathrm{w}(z) = P_\mathrm{atm} + \int_0^z \rho g\,\mathrm{d}\zeta$,
  and Equation (4.11) on folio 128 evaluates it to $98\,066{,}5 \times 1{,}04
  = 101\,989{,}16$ Pa at the surface. Folio 177 then states, for the ratios
  that scale the Bachman sediment correlations, "*standard conditions involving
  atmospheric pressure, a temperature of 23 °C, and salinity 35*" with
  $\rho_\mathrm{w} = 1024{,}2$ kg/m³.
- **The problem:** two defects, of different kinds.

  (a) The 1024,2 of folio 177 does not follow from Equation (4.6) read with
  Equation (4.4). At 23 °C, salinity 35 and one atmosphere the equation gives
  1024,287 9, which prints as 1024,3. The printed 1024,2 is what the equation
  gives with its pressure term set to zero, that is, reading $P_\mathrm{w}$ as
  a gauge pressure against the definition the same chapter states. The
  difference is 0,043 9 kg/m³, or 4,3 parts in a hundred thousand.

  (b) Equation (4.13), which rearranges (4.6) to estimate salinity from a
  measured density, prints the pressure coefficient as $4{,}3\times10^{-5}$
  where (4.6) has $4{,}3\times10^{-7}$. Two orders of magnitude, and not a
  restatement of a different quantity: it is the same coefficient in the same
  role. Carried through at 23 °C it gives 1028,63 kg/m³ against 1024,29, an
  error of 0,42 %.
- **Evidence:** Equation (4.6) evaluated at the stated conditions with the
  pressure of Equation (4.11), against the value folio 177 prints; and the two
  printed exponents compared directly. Verified on PDF pages 157, 158, 165 and
  207 (printed pp. 127, 128, 135 and 177) of the Springer 2010 edition.
- **Library behaviour:** implements Equation (4.6) with the absolute pressure
  its own Equation (4.4) defines, because a printed definition outranks a
  rounded quotation of a derived value three chapters later. The discrepancy is
  below every tolerance in this library, so nothing turns on the choice; what
  would have turned on it is picking a side silently. Equation (4.13) is not
  implemented ([`tests/fluids/test_water.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_water.py),
  conformance checks "Sea water (Ainslie 2010)").
- **Status:** unreported.

## ISO 9053-2:2020, Annex A.3 (two air properties credited to a document that does not print them)

- **Location:** Annex A.3, printed folio 13 (PDF page 17) for the first four
  values and printed folio 14 (PDF page 18) for the fifth.
- **The print:** "The following physical properties for air, valid at 23 °C,
  101,325 kPa and 50 % RH, are used for the calculation (values from
  IEC 61094-2:2009):", followed by $c_0 = 345{,}9$ m/s, $\rho_0 = 1{,}186$
  kg/m³, $\kappa = 1{,}400\,8$, $k_\mathrm{a} = 0{,}023\,55$ J/(s·m·K) and,
  overleaf, $C_\mathrm{P} = 938{,}7$ J/(kg·K).
- **The problem:** two of the five are not IEC 61094-2:2009 values. Table F.1 of
  that standard (printed folio 40) tabulates exactly five quantities at this
  state: $\rho$, $c_0$, $\kappa$, $\eta$ and the thermal **diffusivity**
  $\alpha_t = 2{,}115\,317 \times 10^{-5}$ m²/s. It does not tabulate the
  thermal conductivity or the specific heat capacity; those appear in Annex F
  only as the two expressions under Clause F.6, which print no values. The three
  Annex A.3 values that do match are precisely the three Table F.1 cells rounded
  to four figures ($345{,}866\,52 \to 345{,}9$; $1{,}186\,084\,8 \to
  1{,}186$; $1{,}400\,757\,3 \to 1{,}400\,8$). The two that do not match are
  precisely the two quantities Table F.1 does not print: evaluated at the same
  state, Clause F.6 gives $k_\mathrm{a} = 0{,}025\,434\,1$ J/(s·m·K) and
  $C_\mathrm{P} = 1013{,}74$ J/(kg·K), each larger than the printed pair by the
  same factor 1,0800.

  The common factor is not a coincidence and not a unit difference. The pair is
  locked to the tabulated diffusivity: $0{,}023\,55 / (1{,}186 \times
  2{,}115\,317 \times 10^{-5}) = 938{,}708\,5$, which prints as 938,7. So one
  of the two came from elsewhere and the other was computed back through
  Formula (F.5) to keep $\alpha_t$ right. Which one is foreign is settled by
  thermodynamics rather than by preference: $C_\mathrm{P} = 938{,}7$ J/(kg·K) is
  27,19 J/(mol·K), below the rigid-rotor diatomic floor $(7/2)R = 29{,}10$
  J/(mol·K), so it is not air at any temperature, in any unit, per mass or per
  mole, and the Annex F expression for $C_\mathrm{P}$ never falls below about
  1013 J/(kg·K) anywhere from 200 K to 400 K. The conductivity 0,023 55
  J/(s·m·K), by contrast, is a real conductivity of air: it is what the Annex F
  expression gives near −1,4 °C, outside the 15 °C to 27 °C domain Annex F
  prints for itself.
- **Consequence for the annex's own example:** none. Formula (A.5) uses
  $k_\mathrm{a}$ and $C_\mathrm{P}$ only through the combination
  $k_\mathrm{a}/(\rho_0 c_0 C_\mathrm{P})$, and the common factor cancels
  there, so both pairs give the printed $b = 1{,}83 \times 10^{-3}$ m and
  $\kappa' = 1{,}370$. The defect is invisible inside Annex A.3 and appears only
  when either constant is read out on its own, as a document credited with
  publishing it.
- **Evidence:** the two printed pages against IEC 61094-2:2009 Table F.1
  (printed folio 40) and Clause F.6 (printed folio 39); the Clause F.6
  expressions evaluated at 23 °C, 101 325 Pa and 50 % RH, which reproduce the
  printed $\alpha_t$ to $1{,}0 \times 10^{-7}$ relative; the molar heat
  capacity implied by 938,7 J/(kg·K) against the diatomic floor. IEC 61094-2:2009
  is not a normative reference of ISO 9053-2:2020; it appears only as
  Bibliography item [4]. Verified on PDF page 17 (printed p. 13) and PDF page 18
  (printed p. 14) of ISO 9053-2:2020, and on PDF page 42 (printed p. 40) and PDF
  page 41 (printed p. 39) of BS EN 61094-2:2009.
- **Library behaviour:** the conformance rows that reproduce Annex A.3 pass the
  five values the annex prints, so they reproduce the standard rather than merely
  agree with it. The defaults a caller receives are the same air state computed
  from IEC 61094-2:2009 Annex F, which is what the annex says it is using; both
  land on the printed $b$ and $\kappa'$ ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data),
  conformance checks "ISO 9053-2:2020 Annex A.3").
- **Status:** unreported.

## EN 12354-1:2000 Formula (E.5) / ISO 12354-1:2017 E.3.4 (K24 clamp misprint)

- **Location:** EN 12354-1:2000, Annex E, the wall-junction-with-flexible-
  interlayers block printed under Figure E.5 and numbered Formula (E.5)
  (printed p. 46), and ISO 12354-1:2017, E.3.4 NOTE 4. Annex E of the 2000
  edition has only two numbered clauses, E.1 "Determination methods" and E.2
  "Empirical data", so "E.5" is a formula number, not a clause; an earlier
  revision of this entry cited it as a clause.
- **The print:** $K_{24} = 3{,}7 + 14{,}1 M + 5{,}7 M^{2}\ \text{dB}$;
  $0 \le K_{24} \le -4\ \text{dB}$ ; $0\ \text{dB / octave}$, i.e. the bound
  on the $K_{24}$ junction term is an empty interval; the 2017 edition repeats
  the 2000 misprint verbatim.
- **The problem:** the interval is impossible as printed; the accompanying
  figure and the physics (the term is a reduction bounded below) indicate
  $-4\ \text{dB} \le K_{24} \le 0\ \text{dB}$.
- **Evidence:** the Figure E.5 curve family on the same page runs the $K_{24}$
  branch from 0 dB down to about −4 dB over the plotted mass ratios, which is
  the interval read in the other order. Verified on PDF page 48 (printed p.
  46) of EN 12354-1:2000 and PDF page 52 (printed p. 46) of ISO 12354-1:2017.
- **Library behaviour:** implements the clamp as $-4 \le K_{24} \le 0$ with a
  misprint note in the docstring.
- **Status:** unreported.

## EN 12354-1:2000, Figure E.9 (E.7) (K24 stated in the figure-axis mass ratio)

- **Location:** Annex E, Figure E.9 / Formula (E.7) (junction of lightweight
  double leaf wall and homogeneous elements), the $K_{24}$ line.
- **The print:** $K_{24} = 3{,}0 - 14{,}1 M + 5{,}7 M^{2}\ \text{dB}$ (for
  $m_2/m_1 > 3$), under a figure whose x-axis is $m_2/m_1$.
- **The problem:** Annex E defines $M$ per transmission path as
  $M = \lg(m'_{\perp,i}/m'_i)$ (perpendicular element over the element
  carrying the path). The $K_{24}$ path 2→4 is carried by the homogeneous
  element ($m_2 = m_4$) with the leaf ($m_1$) perpendicular, so the per-path
  $M$ is $\log_{10}(m_1/m_2)$, but the printed $K_{24}$ line only matches its
  own figure's curve when $M$ is read as the x-axis variable
  $\log_{10}(m_2/m_1)$ (e.g. −2,4 dB at $m_2/m_1 = 3$, −5,4 dB at 10). Read
  with the annex's declared $M$, the line contradicts the figure by
  $28{,}2 \cdot |\log_{10}(m_2/m_1)|\ \text{dB}$. The same edition's other
  $K_{24}$ line (Figure E.5, Formula (E.5)) *does* follow the declared
  per-path $M$, so the two $K_{24}$ prints of the 2000 edition silently use
  different conventions. ISO 12354-1:2017 E.3.5 prints the relation
  consistently in the per-path convention of its Formula (E.3),
  $K_{24} = 3{,}0 + 14{,}1 M + 5{,}7 M^{2}$; the two editions agree
  numerically (an earlier revision of this entry read the 2017 print as a sign
  misprint; re-derivation against both editions' figures shows it is a
  convention recast, not a defect of the 2017 text).
- **Evidence:** numerical evaluation of both forms against the Figure E.9
  curve. Verified on PDF page 44 (printed p. 42), PDF page 48 (printed p. 46)
  and PDF page 50 (printed p. 48) of EN 12354-1:2000, and of PDF page 53
  (printed p. 47) of ISO 12354-1:2017, whose E.3.5 prints its K24 line beside
  a Figure E.7 that carries no mass-ratio axis at all.
- **Library behaviour:** implements the per-path convention uniformly
  (`junction_vibration_reduction`, mass_ratio = $m'_{\perp,i}/m'_i$ for every
  branch), so the E.7 double-leaf branch takes leaf-over-homogeneous ratios
  below 1/3 and evaluates $3{,}0 + 14{,}1 M + 5{,}7 M^2$.
- **Status:** unreported.

## EN 12354-2:2000, Formula (3) vs Annex E.3 (standardized impact level)

- **Location:** Formula (3) and worked example E.3.
- **The print:** Formula (3) defines
  $L'_{nT} = L'_n - 10 \lg(0{,}16 \cdot V/(A_0 \cdot T_0))$, which reduces
  exactly to $L'_n - 10 \lg(0{,}032 \cdot V)$, i.e. a reference volume of
  $31{,}25\ \text{m}^3$. Annex E.3 states "from equation (3):
  $L'_{nT,w} = L'_{n,w} - 10 \lg(V/30)$".
- **The problem:** the annex's $V/30$ is a rounding of the formula's own
  constant; the two differ by a constant 0,177 dB.
- **Evidence:** direct algebra; both variants recomputed for the E.3 case
  (42,959 vs 42,782 dB, both rounding to 43 in that example). Verified on PDF
  page 7 (printed p. 5) and PDF page 34 (printed p. 32) of EN 12354-2:2000.
- **Library behaviour:** implements the exact $0{,}032 \cdot V$ form and
  documents the annex's rounding.
- **Status:** unreported.

## EN 12354-3:2000, Formula (5) (reduced form of the normalized level difference)

- **Location:** clause 3.1.5 "Relations between quantities", Formula (5)
  (printed p. 6).
- **The print:**
  $D_{2m,n} = D_{2m,nT} - 10 \lg[0{,}16\,V/(T_0 A_0)] = D_{2m,nT} - 10 \lg 0{,}32\,V\ \text{dB}$.
- **The problem:** the reduced form is off by a factor of ten. Six lines above
  it, the where-list of clause 3.1.4 defines $A_0$ as "the reference
  equivalent sound absorption area, in square metres, for dwellings given as
  10 m²", and the where-list of clause 3.1.3 on the preceding page defines
  $T_0$ as "the reference reverberation time, in seconds, for dwellings given
  as 0,5 s". So $0{,}16/(T_0 A_0) = 0{,}16/5 = 0{,}032$, not 0,32. Applied as
  printed, the reduced form shifts every normalized façade level difference by
  exactly $10\log_{10} 10 = 10\ \text{dB}$. The exact analogue in the
  companion part, EN 12354-2:2000 Formula (3), prints the same algebra
  correctly:
  $L'_{nT} = L'_n - 10 \lg[0{,}16\,V/(A_0 T_0)] = L'_n - 10 \lg 0{,}032\,V\ \text{dB}$.
  ISO 12354-3:2017 dropped the reduced form altogether: its Formula (5) prints
  only $D_{2m,n} = D_{2m,nT} - 10 \lg[C_\text{sab} V/(A_0 T_0)]$ with
  $C_\text{sab} = 0{,}16\ \text{s/m}$.
- **Evidence:** direct algebra with the standard's own $A_0$ and $T_0$, and
  the side-by-side comparison with the correctly reduced Formula (3) of Part
  2. Verified on PDF page 8 (printed p. 6) and PDF page 7 (printed p. 5) of EN
  12354-3:2000, on PDF page 7 (printed p. 5) of EN 12354-2:2000 for its
  Formula (3), and on PDF page 12 (printed p. 6) of ISO 12354-3:2017 for the
  2017 Formulae (4) and (5).
- **Library behaviour:** unaffected. No code path implements the reduced form:
  the façade model computes $D_{2m,nT}$ from Formula (13)
  ([`facade.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/prediction/facade.py)), and the
  survey method converts with the unreduced
  $D_{2m,n} = D_{2m} + k + 10\log_{10}[A_0 T_0/(0{,}16 V)]$ of ISO 10052
  Clause 3.15
  ([`survey_insulation.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/measurement/survey_insulation.py)).
  The two standardization constants that *are* pre-folded elsewhere in the
  library are both correct: $0{,}032$ for the Part 2 impact form and $0{,}32$
  for the Part 1 airborne form
  $D_{nT} = R' + 10\log_{10}(0{,}16 V/(T_0 S_s))$, where the denominator is an
  area rather than $A_0$.
- **Status:** unreported.

## EN 12354-3:2000, Formula (13) vs its own Annex F example (the "6" constant)

- **Location:** clause 4.1, Formula (13) (printed p. 9), against the worked
  example of Annex F (printed pp. 27-28).
- **The print:** Formula (13) gives
  $D_{2m,nT} = R' + \Delta L_\text{fs} + 10 \lg[V/(6 T_0 S)]\ \text{dB}$,
  while the Annex F.1.3 result table prints a $D_{2m,nT}$ row that is exactly
  $R' + 1{,}5\ \text{dB}$ in all five octave bands and in the single-number
  column (25,9/23,0/26,4/36,9/39,0 against 24,4/21,5/24,9/35,4/37,5, and 29,3
  against 27,8).
- **The problem:** on this constant the *example* is self-consistent and the
  *formula* is the outlier. (Two cells of the same annex table do not follow
  from its element rows, which is the subject of the next entry; the printed
  $+1,5$ dB row holds in every band regardless, so the two defects are
  independent.) With the example's own inputs ($V = 50\ \text{m}^3$,
  $S = 11{,}3\ \text{m}^2$, $T_0 = 0{,}5\ \text{s}$,
  $\Delta L_\text{fs} = 0$), the Sabine form gives
  $10\log_{10}[0{,}16 \cdot 50/(0{,}5 \cdot 11{,}3)] = 1{,}5104\ \text{dB}$,
  which is the printed +1,5 dB row; Formula (13) as printed gives
  $10\log_{10}[50/(6 \cdot 0{,}5 \cdot 11{,}3)] = 1{,}6877\ \text{dB}$. The
  gap is the constant: Formula (13)'s "6" is a rounded $1/0{,}16 = 6{,}25$,
  and $10\log_{10}(6{,}25/6) = 0{,}177\ \text{dB}$ is exactly the discrepancy.
  ISO 12354-3:2017 replaced it with an explicit Sabine constant, printing
  Formula (4) as
  $D_{2m,nT} = R' + \Delta L_\text{fs} + [10 \lg(C_\text{sab} V/(T_0 S))]$
  with $C_\text{sab} = 0{,}16\ \text{s/m}$, which is the constant the 2000
  example already used. A previous revision of this entry attributed the 1,5
  dB row to the example; the attribution is the other way round.
- **Evidence:** evaluation of both constants against the printed Annex F rows,
  which agree with 0,16 to the 0,05 dB the table carries and disagree with the
  rounded 6 by a uniform 0,18 dB; and the 2017 recast, which adopts the
  example's constant. The example's single-number result
  $D_{2m,nT,w} = 33\ \text{dB}$ is insensitive to the difference and
  reproduces either way. Verified on PDF pages 11 (printed p. 9), 29 (printed
  p. 27) and 30 (printed p. 28) of EN 12354-3:2000, and of PDF page 12
  (printed p. 6) of ISO 12354-3:2017.
- **Library behaviour:** implements Formula (13) as printed, with the rounded
  6; the test data records that the Annex F rows follow the exact 0,16
  constant and sit 0,18 dB below the model.
- **Status:** unreported.

## EN 12354-3:2000, Annex F.1.3 (the 1 kHz and 2 kHz R' cells)

- **Location:** Annex F, table F.1.3 "Results for façade" (printed p. 28), the
  `R' (equation 10)` row.
- **The print:** $R'$ = 24,4 / 21,5 / 24,9 / 35,4 / 37,5 dB at 125 / 250 / 500
  / 1000 / 2000 Hz.
- **The problem:** the last two cells do not follow from the table's own
  element rows. Formula (10), $R' = -10\log_{10} \sum \tau_{e,i}$, applied to
  the four $-10\log_{10} \tau_e$ columns printed immediately above gives 24,41
  / 21,50 / 24,86 / **35,78** / **37,99** dB. The first three cells reproduce
  to the 0,05 dB the table carries; the 1 kHz and 2 kHz cells are printed 0,4
  dB and 0,5 dB low.
- **Evidence:** energy summation of the printed element rows band by band (1
  kHz: 60,7 / 40,0 / 46,6 / 38,5 dB; 2 kHz: 66,7 / 41,0 / 43,6 / 44,5 dB). The
  $D_{2m,nT}$ row below is a uniform $R' + 1{,}5\ \text{dB}$ in every band
  including those two, so it inherits the same offset, and the single-number
  result $D_{2m,nT,w} = 33\ \text{dB}$ is insensitive to it and still
  reproduces. Verified on PDF page 30 (printed p. 28) of EN 12354-3:2000.
- **Library behaviour:** the test data notes the inconsistency next to the
  affected anchor.
- **Status:** unreported.

## EN 12354-5:2009, Table F.1 and clause F.4.2 (reference force printed as 1 pN)

- **Location:** Annex F, clause F.4.2: the symbol list of Formula (F.9), the
  sentence introducing the closed form, and the caption of Table F.1 (printed
  p. 59).
- **The print:** "$L_F$ is the force level in the source room, in dB re 1 pN";
  "$L_F = 10\lg 2{,}5f/10^{-12}$ dB re 1 pN or $L_F = 10\lg 0{,}8f/10^{-12}$ dB
  re 1 pN for one-third octave bands"; and "Table F.1 – Force level $L_F$ re
  1 pN for the ISO tapping machine in octave bands", whose eight cells read
  139, 142, 145, 148, 151, 154, 156 and 156 dB.
- **The problem:** the reference force of those levels is $10^{-6}$ N, not
  1 pN. Three independent readings agree, and none of them is compatible with
  the printed reference. **(a) The annex's own algebra.** A power level re
  1 pW built from a force level and a mobility is
  $L_W = L_F + 10\lg(F_0^2 Y / W_0)$. Formula (D.5a) prints
  $L_{Ws,c} = L_{F,eq} + 10\lg Y_s$ and Formula (D.9a) prints
  $L_{Ws,c} = L_F - 5 - 10\lg f$, which is the same expression evaluated at
  the mass-like source mobility $Y_s = (2\pi f M)^{-1}$ of a 0,5 kg tapping
  hammer. Neither carries a term for $F_0^2/W_0$, so both balance only when
  $F_0^2 / W_0 = 1\ \text{s}^{-1}$, that is $F_0 = 10^{-6}$ N; read re 1 pN
  each would fall 120 dB short of the level it defines. The velocity
  counterpart, Formula (D.10a), does print its reference term
  $10\lg(v_\text{ref}^2/W_\text{ref})$ and states the result cancels the
  $10\lg Z_s$ exactly, which it does at the $10^{-9}$ m/s the standard itself
  gives as the velocity-level reference in clause F.4.2. The annex is
  therefore explicit and correct about the velocity reference and silent about
  the force one. **(b) The machine that produces the table.** The ISO tapping
  machine drops 0,5 kg hammers from 40 mm at ten impacts per second, so each
  impact transfers a momentum of 0,443 N·s and the force is a 10 Hz impulse
  train every harmonic of which carries 6,26 N r.m.s. Summing the harmonics
  that fall inside each octave band gives 139,4 / 142,4 / 145,4 / 148,4 /
  151,4 / 154,4 dB re $10^{-6}$ N from 31,5 Hz to 1 kHz, reproducing the first
  six cells of Table F.1 to within 0,5 dB; the 2 kHz and 4 kHz cells sit below
  that line, which is the roll-off the standard itself flags with "up till
  about 1000 Hz". Re 1 pN the same cells would describe forces of tens of
  micronewtons, which no impact machine produces. **(c) The companion
  standard.** EN 15657:2018 Formula (15), which is where the structure-borne
  source data of Annex D comes from in the first place, writes the same
  force-to-power conversion "in dB re $F_0 = 10^{-6}$ N", and $10^{-6}$ N is
  the preferred reference force of ISO 1683.
- **Evidence:** verified on PDF pages 61 and 62 (printed pp. 59 and 60) of
  BS EN 12354-5:2009, carrying clause F.4.2 with the symbol list of
  Formula (F.9), the closed form, the whole of Table F.1 and the symbol list
  of Formula (F.11) with its $10^{-9}$ m/s velocity reference; and on PDF
  pages 45, 48 and 50 (printed pp. 43, 46 and 48) of the same edition,
  carrying Formulae (D.5a), (D.9a) and (D.10a).
- **Library behaviour:** ships the printed cells unchanged and documents them
  re $10^{-6}$ N. `tapping_machine_force_level` returns the eight values of
  Table F.1, `tapping_machine_force_level_estimate` the closed form and
  `tapping_machine_characteristic_power_level` Formula (D.9a) as printed;
  `test_table_f1_is_referred_to_1e_6_newton_not_1_piconewton` pins the reading
  against the mechanics of the machine.
- **Status:** unreported.

## EN 12354-5:2009, Figure D.3 Key (three curves under one symbol)

- **Location:** Annex D, the Key of Figure D.3 (printed p. 47).
- **The print:** three key rows, each labelled with the same symbol:
  $L_{Ws,c,A} = 124\ \text{dB}$, $L_{Ws,c,A} = 119\ \text{dB}$ and
  $L_{Ws,c,A} = 102\ \text{dB}$.
- **The problem:** the figure's own caption reads "Structure-borne sound power
  for the ISO-tapping machine: characteristic source power, installed power on
  a wooden floor and installed power on a concrete floor; the A-weighted power
  level is also indicated". Only the first curve is a characteristic power; the
  other two are installed powers and their A-weighted totals are
  $L_{Ws,\text{inst},A}$. The plotted curves settle the assignment: the first
  is flat at about 114,5 dB re 1 pW, which is the frequency-independent
  Formula (D.9a) result for the tapping machine, while the other two rise with
  frequency and lie below it, the concrete floor lowest, as
  $L_{Ws,c} - D_{C,i}$ requires.
- **Evidence:** verified on PDF page 49 (printed p. 47) of BS EN 12354-5:2009,
  the page carrying Figure D.3 with its Key and its caption.
- **Library behaviour:** none required; no value is read from Figure D.3.
  `test_formula_d9a_is_flat_at_about_115_db_per_third_octave` pins the flat
  characteristic curve that the first key row belongs to.
- **Status:** unreported.

## ISO 12354-1:2017 Table L.3 / ISO 12354-2:2017 Table G.3 (perimeter sums)

- **Location:** the input-data block below Table L.3 (printed p. 81) and the
  identical block below Table G.3 (printed p. 38), which lists the perimeter
  absorption sum $\sum l_k \alpha_k$ of Formula (C.1) for the worked example.
- **The print:** one value per element *type*: separating floor 2,364 m
  ($S = 20\ \text{m}^2$), external wall 2,375 m ($S = 11\ \text{m}^2$),
  internal wall 1,840 m ($S = 13{,}75\ \text{m}^2$).
- **The problem:** Formula (C.1) needs one sum per *element*, and the example
  has five elements with three different areas. Only two of the three printed
  values reproduce the columns they are supposed to drive: 2,375 m with
  $S = 11\ \text{m}^2$ gives external wall 1 exactly, and 1,840 m with
  $S = 13{,}75\ \text{m}^2$ gives internal wall **2** exactly. The separating
  floor's printed 2,364 m does not reproduce its own column at any band
  (0,074 9 against the printed 0,083 1 at 50 Hz, 0,026 4 against 0,029 0 at
  500 Hz); 2,659 m does, at every band. The two elements with no printed value
  need 2,548 m (external wall 2, $S = 13{,}75\ \text{m}^2$) and 1,636 m
  (internal wall 1, $S = 11\ \text{m}^2$).
- **Evidence:** all five sums re-derived from Formula (C.4),
  $\alpha_k = \sum_j \sqrt{f_{c,j}/f_\text{ref}}\ 10^{-K_{ij}/10}$, over the
  example's own junction geometry with the unrounded Annex E indices: 2,659 /
  2,375 / 2,548 / 1,636 / 1,839 m. The derivation returns the two printed
  values that are self-consistent with their own columns (2,375 m, and 1,839 m
  against the printed 1,840 m) and supplies the three that are missing or
  wrong, and every $\eta_\text{tot,situ}$ column of Table L.3 / G.3 then
  reproduces to $5 \cdot 10^{-5}$. The printed values applied to the wrong
  element of the same type miss by far more than that rounding: 2,375 m on
  external wall 2 gives 0,108 5 against the printed 0,114 9 at 50 Hz, and
  1,840 m on internal wall 1 gives 0,085 0 against 0,077 0.
- **Library behaviour:** `in_situ_total_loss_factor` takes $\sum l_k \alpha_k$
  as an input and `perimeter_absorption_coefficient` implements Formula (C.4);
  the Annex L fixture derives all five sums that way rather than using the
  printed block, and says so
  ([`tests/building/prediction/test_detailed_model.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_detailed_model.py)).
- **Status:** unreported.

## ISO 12354-1:2017 Table L.3 / ISO 12354-2:2017 Table G.3 (external wall ηint)

- **Location:** the same input-data block, external-wall line.
- **The print:** $\eta_\text{int} = 0{,}013$ for the 365 mm autoclaved aerated
  concrete external walls.
- **The problem:** the example's own element specification, and Annex B Table
  B.3 for autoclaved aerated concrete, give 0,012 5. Only 0,012 5 reproduces
  the tabulated $\eta_\text{tot,situ}$: at 500 Hz Formula (C.1) gives
  $0{,}012\,5 + 0{,}001\,41 + 0{,}034\,57 = 0{,}048\,5$, the printed value,
  where 0,013 would give 0,049 0.
- **Evidence:** term-by-term recomputation of Formula (C.1) for both external
  walls at every band with each candidate $\eta_\text{int}$.
- **Library behaviour:** the Annex L fixture uses 0,012 5.
- **Status:** unreported.

## ISO 12354-1:2017, Table L.4 (second path block labelled 2d)

- **Location:** Annex L, Table L.4 (printed p. 82), the right-hand block
  headed "Transmission path 2d".
- **The print:** the block gives $\alpha_{i,\text{situ}}$ = 6,3 to 14,1,
  $D_{v,ij,\text{situ}}$ = 11,0 to 13,6 and $R_{ij}$ = 43,9 to 84,6 dB.
- **The problem:** those are the numbers of path **4d** (internal wall 2 to
  the separating floor), not of path 2d (external wall 2). Table L.1 of the
  same annex prints the whole $R_{4d}$ column, 43,9 to 84,6 dB, and the
  block's $R_{ij}$ column is that column cell for cell. What settles it band
  by band is the other two columns, which cannot be confused: external wall 2
  has $\alpha_{i,\text{situ}} = 10{,}3\ \text{m}$ at 50 Hz
  ($S = 13{,}75\ \text{m}^2$, $\eta_\text{tot} = 0{,}114\,9$) while internal
  wall 2 has 6,3 m ($\eta_\text{tot} = 0{,}070\,3$), the printed value; and
  $D_{v,ij,\text{situ}}$ follows the floor-to-internal-wall $K_{ij}$ of 8,8
  dB, which gives 11,0 to 13,6 dB, not the floor-to-external-wall 6,4 dB,
  which gives 9,6 to 11,9 dB.
- **Evidence:** independent recomputation of Formulae (10), (11) and (15) for
  both candidate paths at every band. Path 4d reproduces all three columns of
  the block, $\alpha_{i,\text{situ}}$ to 0,05 m and $D_{v,ij,\text{situ}}$ and
  $R_{ij}$ to 0,05 dB, which is the printed resolution. Path 2d departs from
  the block's $R_{ij}$ column by 0,1 dB to 7,0 dB depending on the band, and
  comes closest between 100 Hz and 160 Hz (0,5 / 0,5 / 0,1 dB), so $R_{ij}$
  alone does not identify the path over those bands; $\alpha_{i,\text{situ}}$
  (10,3 against 6,3 m at 50 Hz) and $D_{v,ij,\text{situ}}$ (1,4 dB to 1,7 dB
  apart in every band) do.
- **Library behaviour:** the test that asserts the block builds it as path 4d
  and names the mislabelling.
- **Status:** unreported.

## ISO 12354-1:2017, Table L.1 (non-integer weighted ratings)

- **Location:** Annex L, Table L.1 (printed p. 79), the $R_w$ row and the
  sentence below it, and the corresponding $L_{n,w}$ row of ISO 12354-2:2017
  Table G.1.
- **The print:** the $R_w$ row gives one decimal for every path (75,1 / 84,5 /
  70,6 / … and 57,8 in the total column) while the sentence immediately below
  states $R'_w\,(C\,;\,C_\text{tr}) = 57{,}9\ (-2\,;\,-8)\ \text{dB}$.
- **The problem:** ISO 717-1 rates by shifting the reference curve **in 1 dB
  steps**, so a weighted rating is an integer; the printed one-decimal values
  are the reference curve shifted *continuously* until the sum of unfavourable
  deviations equals exactly 32,0 dB. The airborne $R_w$ row of Table L.1
  *truncates* that continuous value to one decimal while the sentence below it
  rounds, which is why the same quantity appears twice as 57,8 and 57,9; the
  impact $L_{n,w}$ row of Table G.1 rounds instead (29,58 prints as 29,6 and
  40,98 as 41,0), so the truncation is a property of the airborne row only.
  The spectrum adaptation terms inherit the offset: with the ISO 717-1 rating
  of 57 dB they are $C = -1$ and $C_\text{tr} = -7$, and the printed (−2 ; −8)
  is exactly the pair shifted by the same 0,86 dB.
- **Evidence:** a continuous-shift solve of the ISO 717-1 reference curve
  against the printed per-band spectra reproduces every printed value in both
  rows ($R_{Dd}$ 75,12 against 75,1; $R_{D1}$ 84,54 against 84,5; $R_{11}$
  70,66 against 70,6; the total 57,86 against 57,8 / 57,9; on the impact side
  $L_{n,Df1}$ 29,58 against 29,6 and the total 40,98 against 41,0), whereas
  the ISO 717-1 1 dB-step ratings of the same spectra are 75, 84, 70 and 57
  dB. Verified on PDF page 85 (printed p. 79) of ISO 12354-1:2017.
- **Library behaviour:** `weighted_rating` / `weighted_impact_rating`
  implement ISO 717-1/-2 as written, so the detailed model returns
  $R'_w = 57\ \text{dB}$ and $L'_{n,w} = 41\ \text{dB}$ ($C_I = 2$) for the
  example; the test pins those and documents the printed values.
- **Status:** unreported.

## ISO 12354-2:2017, Table G.1 (50 Hz to 80 Hz flanking columns)

- **Location:** Annex G, Table G.1 (printed p. 36), the four $L_{n,Df}$
  columns, 50 Hz, 63 Hz and 80 Hz rows.
- **The print:** $L_{n,Df1}$ = 47,3 / 44,9 / 46,2 dB.
- **The problem:** Table G.4 of the same annex prints the same path Df for
  external wall 1, from the same inputs, as 47,8 / 45,9 / 47,0 dB. The two
  tables cannot both be right, and from 100 Hz upwards they agree exactly.
- **Evidence:** Formula (12) evaluated from the annex's own Table G.3 columns
  ($L_{n,\text{situ}}$, $R_\text{situ}$) and the Table G.4
  $D_{v,ij,\text{situ}}$ and $\Delta L_\text{situ}$ columns gives 47,80 /
  45,85 / 46,95 dB, reproducing the printed 47,8 / 45,9 / 47,0 of Table G.4 to
  0,05 dB and Table G.1 only from 100 Hz upwards. Carrying the same
  recomputation through the whole chain puts external wall 2 low by 0,5 dB to
  1,0 dB over the same three bands and the two internal walls low by up to 0,5
  dB at 50 Hz and 63 Hz (their 80 Hz cells agree). From 100 Hz upwards no
  flanking column deviates by more than 0,15 dB. Correcting the affected cells
  raises the printed total $L'_n$ only slightly: 58,6 to 58,7 dB at 50 Hz,
  57,0 to 57,2 dB at 63 Hz, 55,9 to 56,1 dB at 80 Hz.
- **Library behaviour:** the test asserts Table G.4 in full, the Table G.1
  direct column over the whole range, and the Table G.1 flanking columns from
  100 Hz upwards, naming the disagreement.
- **Status:** unreported.

## ISO 12354-2:2017, Table G.8 (junction Kij and m'i)

- **Location:** Annex G, Table G.8 (printed p. 40), the internal wall to
  external wall rigid T junction.
- **The print:** row "Int. wall 1/2 - Ext. wall 1/2" gives
  $K_{ij} = 6{,}6\ \text{dB}$; the row below it, "Ext. wall 1/2 - Ext. wall
  1/2", gives $m'_i = 2{,}19\ \text{kg/m}^2$.
- **The problem:** two independent misprints. The rigid-T corner branch
  $K_{12} = 5{,}7 + 5{,}7 M^2$ with $M = \log_{10}(360/219) = 0{,}215\,6$
  gives 5,97, i.e. **6,0**, and ISO 12354-1:2017 Table L.8 prints 6,0 for the
  identical junction of the identical example. And the external wall's mass
  per unit area is $219{,}0\ \text{kg/m}^2$ throughout the example, not 2,19
  (a factor 100).
- **Evidence:** Annex E evaluation of the corner branch; the same table's own
  other rows and the whole of ISO 12354-1 Annex L use
  $219{,}0\ \text{kg/m}^2$. Verified on PDF page 46 (printed p. 40) of ISO
  12354-2:2017, whose Table G.8 mass columns are headed `m'i` and
  `m'orthogonal`, and PDF page 89 (printed p. 83) of ISO 12354-1:2017.
- **Library behaviour:** uses 6,0 dB and $219{,}0\ \text{kg/m}^2$.
- **Status:** unreported.

## ISO 12354-2:2017, Table G.6 (mislabelled row)

- **Location:** Annex G, Table G.6 (printed p. 40), internal wall to
  separating floor rigid cross junction.
- **The print:** a row labelled "Ext. wall 1/2 – Int. wall 1/2" with `m'i` =
  360,0, `m'orthogonal` = 484,0 and $K_{ij} = 11{,}0\ \text{dB}$.
- **The problem:** Table G.6 describes the *internal wall to separating floor*
  cross junction; no external wall meets it. The masses and the value are
  those of the in-line internal-wall path, and ISO 12354-1:2017 Table L.6
  prints the same row correctly as "Int. wall 1/2 - Int. wall 1/2".
- **Evidence:** the rigid-cross through branch $8{,}7 + 17{,}1 M + 5{,}7 M^2$
  with $M = \log_{10}(484/360)$ gives 10,99, the printed 11,0, for the
  internal wall. Verified on PDF page 46 (printed p. 40) of ISO 12354-2:2017
  and PDF page 89 (printed p. 83) of ISO 12354-1:2017.
- **Library behaviour:** treats the row as the internal-wall in-line path.
- **Status:** unreported.

## ISO 12354-1:2017 Table L.10 / ISO 12354-2:2017 Table G.10 (element label)

- **Location:** the simplified-model input table of both parts, fourth row:
  Table L.10 (printed p. 84) and Table G.10 (printed p. 41).
- **The print:** ISO 12354-1 prints "Internal wall 4 (F = f = 4)"; ISO 12354-2
  prints "Internal wall 4 (f4)": the two parts label the row differently, and
  an earlier revision of this entry quoted the Part 1 form for both.
- **The problem:** the example has two internal walls; the element indexed
  $F = f = 4$ is internal wall **2**
  ($5{,}00\ \text{m} \times 2{,}75\ \text{m}$, $S = 13{,}75\ \text{m}^2$), as
  the detailed-model tables of the same annexes label it.
- **Evidence:** the row's own $S = 13{,}75\ \text{m}^2$ and
  $l_{ij} = 5{,}0\ \text{m}$ match internal wall 2 of Table L.1 / G.1.
  Verified on PDF page 90 (printed p. 84) of ISO 12354-1:2017 and of PDF page
  47 (printed p. 41) of ISO 12354-2:2017, with the detailed-model column
  labels read on PDF page 85 (printed p. 79) of ISO 12354-1:2017 and of PDF
  page 42 (printed p. 36) of ISO 12354-2:2017.
- **Library behaviour:** none needed; the numbers are unaffected.
- **Status:** unreported.

## ISO 12354-1:2017, Table D.1 (1 600 Hz covered by two rows)

- **Location:** Annex D, Table D.1 (printed p. 39), which reads the weighted
  sound reduction index improvement of an interior lining off its resonance
  frequency.
- **The print:** the last two rows are "630 to 1 600 -> -10" and "1 600 <= f0
  <= 5 000 -> -5".
- **The problem:** 1 600 Hz belongs to both rows, with different values, and
  Clause D.2.2 requires $f_0$ to be "rounded to the centre frequency of the
  one-third-octave band in which fo falls", so 1 600 Hz is a value the table
  is actually read at rather than an unreachable edge. Because the rounding is
  mandatory, the ambiguity is not a single point: every raw resonance
  frequency in the 1 600 Hz band, that is from 1 412,5 Hz to 1 778,3 Hz (ISO
  266 band edges), lands on it. Every other boundary in the table is a
  distinct band centre (200, 250, 315, 400, 500 Hz), and no other pair of rows
  overlaps.
- **Evidence:** the printed table itself, on PDF page 45 (printed p. 39) of
  ISO 12354-1:2017: the two rows are separately ruled and share the endpoint
  verbatim, "630 to 1 600" and "1 600 <= f0 <= 5 000". Neither row can be
  discarded, because 630 Hz to 1 250 Hz has no other entry and 2 000 Hz to
  5 000 Hz has none either. The predecessor edition gives the earlier,
  unambiguous reading: EN 12354-1:2000 Table D.3, verified on PDF page 43
  (printed p. 41) of that edition, prints the same pair of rows as "630 -
  1 600 -> -10" and "> 1 600 -> -5", strictly greater, so in 2000 exactly
  1 600 Hz took -10 dB with nothing to decide. The 2017 rewrite replaced ">
  1 600" with "1 600 <= f0 <= 5 000" while leaving "630 to 1 600" untouched,
  which is what creates the overlap; what the rewrite intended at the shared
  endpoint the text does not say.
- **Library behaviour:** `weighted_lining_improvement` returns the more
  conservative -10 dB at exactly 1 600 Hz and -5 dB above it, the 2000
  reading, with the ambiguity named in the docstring and pinned in
  [`tests/building/prediction/test_resilient_layers.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_resilient_layers.py).
- **Status:** unreported.

- **Related, not an erratum:** NOTE 1 of the same table sets a floor of 0 dB
  on the 30 Hz to 160 Hz branch $74{,}4 - 20\log_{10}(f_0) - R_w/2$. Inside
  the validity box Clause D.2.2 states for the table
  ($30\ \text{Hz} \le f_0 \le 160\ \text{Hz}$,
  $20\ \text{dB} \le R_w \le 60\ \text{dB}$) the branch never reaches it: its
  minimum is $74{,}4 - 20\log_{10}(160) - 60/2 = 0{,}32\ \text{dB}$. The floor
  is therefore inactive for every input the table is stated for, but it was
  not always: the 2000 edition tabulated the low branch as four discrete rows
  ending in "160 -> 28 - Rw/2", whose minimum is $28 - 60/2 = -2\ \text{dB}$,
  so NOTE 1 was operative there. The 2017 continuous fit sits 2,3 dB above it
  at that corner and left the note vestigial. The library keeps the floor
  because the note is still printed.

## ISO 15186-1, Clause 3.9, Formula (8) (sign of the 10 lg N term)

- **Location:** Clause 3.9, Formula (8) (printed p. 3), the intensity element
  normalized level difference for N small building elements measured together.
  The print read here is **BS EN ISO 15186-1:2003**, the identical-text
  British adoption; the entry previously carried the heading ":2000", the year
  of the ISO edition the library's docstrings cite, which is not the copy that
  was read.
- **The print:**
  $D_{I,n,e} = L_{p1} - 6 - (L_{In} + 10 \lg(S_m/A_0) + 10 \lg(N))$, i.e. the
  $10 \lg N$ term is subtracted.
- **The problem:** the subtracted sign cannot be derived. Measuring $N$
  identical units within one measurement surface raises the transmitted power
  (and hence $L_{In} + 10\log_{10} S_m$) by $10\log_{10} N$, so recovering the
  per-unit $D_{I,n,e}$ requires *adding* $10\log_{10} N$. The pressure-based
  equivalent, ISO 10140-2:2010 Formula (6), prints exactly that correction
  ($D_{n,e} = L_1 - L_2 + 10\log_{10}(nA_0/A)$), and ISO 15186-2:2010 Formula
  (12) prints Formula (8) without any $N$ term (the $N = 1$ case, with which
  both signs agree). As printed, installing more units would *lower* the
  per-unit rating by $20\log_{10} N$ relative to the derivable value.
- **Evidence:** derivation from the diffuse-field receiving-room relation
  $L_2 = L_W + 10\log_{10}(4/A)$ against ISO 10140-2:2010 Formula (6);
  cross-check against ISO 15186-2:2010 Formula (12) and Hopkins, *Sound
  Insulation* (2007), Eq. 3.45. Verified on PDF page 11 (printed p. 3) of BS
  EN ISO 15186-1:2003, with the cross-check read on PDF page 11 (printed p.
  11) of ISO 10140-2:2010. **Part 3 of the same series settles it in the
  series' own words:** ISO 15186-3:2002, Clause 3.9, Formula (8) states the
  same quantity as
  $D_{I,n,e} = L_{pS} - 9 - [L_{In} - 10 \lg(A_0/S_m) - 10 \lg N]$, whose
  bracket carries $10 \lg N$ with the opposite outer sign, i.e. the
  $+10\log_{10} N$ derived here. Read on PDF page 10 (printed p. 4) of BS EN
  ISO 15186-3:2010.
- **Library behaviour:** implements the derivable per-unit form
  (`intensity_element_normalized_difference`, $+10\log_{10} N$) and emits a
  warning whenever $n > 1$, where the result deviates from the print.
- **Status:** unreported.

## ISO 15186-3:2002, Annex A, Table A.1 (steel-sandwich column irreproducible from its own inputs)

- **Location:** Annex A (normative), A.2 and Table A.1, "Calculated sound
  reduction index (at 1 013 hPa and 23 °C)", the qualification example a
  laboratory checks its facility against. The print read here is **BS EN ISO
  15186-3:2010**, the identical-text British adoption of ISO 15186-3:2002,
  PDF page 18 (printed p. 12).
- **The print:** two columns of six one-third-octave values, 50 Hz to 160 Hz.
  The plaster-board column is headed "10 kg/m²" over a "Test opening 10 m²"
  and reads 10,7 / 11,9 / 13,4 / 14,8 / 16,3 / 17,9. The steel column is
  headed "17 kg/m²" over a "Test opening 1,25 m × 1,50 m" and reads
  21,3 / 21,2 / 21,7 / 22,7 / 23,8 / 25,1. A.2 also states that "the
  dimensions of the free part of the panel are 1,162 m × 1,412 m".
- **The problem:** no reading of the inputs printed beside the steel column
  reproduces it. With the test opening (1,875 m²) and the stated mass, the six
  computed values fall 1,27 dB to 0,72 dB below the printed ones. The 0,55 dB
  spread between those two ends rules out any surface mass at that area,
  because a mass error shifts $R_0 = 20 \lg(\pi f m / \rho c)$ by the same amount
  in every band. With the free part of the panel (1,640744 m²) the residual is
  nearly flat, mean 0,562 dB, but it still spreads 0,102 dB end to end, which
  is the whole width of the printed decimal, so it is not the constant offset a
  wrong mass alone would leave either.

  No single input closes it to the 0,05 dB that one-decimal printing allows.
  The best surface mass alone, over the free part, is 18,13 kg/m² and leaves
  0,051 dB; the best static pressure alone is 950 hPa and leaves 0,051 dB; the
  best temperature alone, over the test opening, is 63 °C and leaves 0,052 dB.
  The last two contradict the caption, which fixes the climate at 1 013 hPa and
  23 °C, and the plaster-board column reproduces at exactly that climate, so the
  two columns cannot be read at different ones.

  The only reading that does reproduce all six values moves two inputs at once:
  an area of about 1,654 m², near the free part but not equal to it, together
  with a surface mass of about 18,16 kg/m². That mass is not available to the
  specimen described. Solid steel 2,2 mm thick is 16,9 kg/m² to 17,3 kg/m², and
  the leaf is a steel/resin/steel sandwich, so its surface mass is necessarily
  below that. The plaster-board column of the same table, from the same
  formulas at the same climate, reproduces all six of its values to within
  0,050 dB.
- **Evidence:** Formulas (A.1) to (A.5) evaluated at the stated 1 013 hPa and
  23 °C, read on PDF pages 17 and 18 (printed pp. 11 and 12) of BS EN ISO
  15186-3:2010. ISO 140-3:1995, C.2.4, which A.2 cites as the source of the
  specimen, describes the 2,2 mm steel/resin/steel leaf but states no surface
  mass, so the 17 kg/m² is not carried over from there. No corrigendum to
  Annex A was found.
- **Library behaviour:** `limp_panel_reduction_index` implements Formulas
  (A.1) to (A.5) as printed. The conformance suite anchors them on the
  plaster-board column alone; the steel column is deliberately not used as an
  oracle.
- **Status:** unreported.

## ISO 10848-1:2006, Clause 8.1.1, Formula (20) (spurious π in the critical frequency)

- **Location:** Clause 8.1.1, Formula (20), the thin-plate critical frequency
  used by the test-facility flanking criterion of Formula (19).
- **The print:** $f_c = c_0^{2} / (1{,}8\ c_L \cdot h \cdot \pi)$.
- **The problem:** the constant 1,8 is itself the rounded
  $2\pi/\sqrt{12} \approx 1{,}814$ of the thin-plate dispersion relation, so
  the extra $\pi$ double-counts it and would misplace $f_c$ by a factor $\pi$
  (e.g. a 100 mm concrete element with $c_L = 3500\ \text{m/s}$: 187 Hz
  without the $\pi$, 59 Hz with it, far from any measured coincidence dip).
- **Evidence:** derivation from the thin-plate dispersion relation (Hopkins,
  *Sound Insulation* (2007), Eq. 2.201, $f_c = c_0^2/(1{,}8 c_L h)$); ISO
  12354-1:2017 prints the same $\pi$-free form in its symbol definitions
  ($f_c = c_0^2/(1{,}8 c_L t)$).
- **Library behaviour:** implements the $\pi$-free form
  (`phonometry.building.measurement.flanking_transmission.critical_frequency`),
  with a misprint note in the docstring.
- **Status:** corrected upstream: ISO 10848-1:2017 (second edition) prints
  the $\pi$-free form in its Formula (5), $f_c = c_0^2/(1{,}8 h c_L)$,
  confirming the 2006 print as a misprint. No report is needed. The entry is
  retained because the library cites the 2006 edition, whose print carries the
  defect; the 2017 edition stands as the confirmation.

## ISO 10846-2:2008, 7.6.1 (the unidirectionality pre-run cross-referenced to 6.1, Inequality (1))

- **Location:** clause 7.6.1, "General", the paragraph on the pre-run that
  checks the direction of the input motion.
- **The print:** "A further pre-run shall be performed to check that the
  acceleration in the excitation direction exceeds the acceleration in other
  directions. Measurement results, which do not meet the condition of **6.1,
  Inequality (1)**, shall be excluded from the evaluation of the dynamic
  stiffness function."
- **The problem:** 6.1, Inequality (1), is the blocked-output condition
  $\Delta L_{1,2} = L_{a1} - L_{a2} \geqslant 20$ dB, a level difference
  between the input and the output sides, which a check of the directions at
  the input cannot test. The condition the pre-run tests is 6.4, "Unwanted
  input vibrations", Inequality (3),
  $L_{a(\mathrm{excitation})} - L_{a(\mathrm{unwanted})} \geqslant 15$ dB.
  The same sentence in the companion parts points to their own
  unwanted-input clause: ISO 10846-3:2002 7.5.1 to 6.4, ISO 10846-4:2003
  7.6.1 to 6.5 and ISO 10846-5:2008 7.6.1 to its Inequality (2). Followed as
  printed, the sentence excludes the lines where the output is not blocked
  and keeps those where the input moves in the wrong direction.
- **Evidence:** the reference read against the clauses it can mean. Verified
  on PDF page 24 (printed p. 16, 7.6.1), PDF page 20 (printed p. 12, 6.1) and
  PDF page 21 (printed p. 13, 6.4) of BS EN ISO 10846-2:2008, the UK
  implementation of ISO 10846-2:2008 (second edition); the companion
  sentences on PDF page 33 (printed p. 23) of BS EN ISO 10846-3:2002, PDF
  page 36 (printed p. 26) of BS EN ISO 10846-4:2003 and PDF page 23 (printed
  p. 15) of BS EN ISO 10846-5:2009.
- **Library behaviour:** follows the intended target. `check_unwanted_input`
  judges the unidirectionality of Part 2 against the 15 dB of its
  Inequality (3), and `check_blocked_output` keeps the 20 dB of
  Inequality (1) for the output side. The reference changes no number the
  library reports.
- **Status:** unreported (cross-reference defect, no numerical consequence).

## ISO 10846-4:2003, 6.2 NOTE 1 (the bound of Inequality (3) printed as 05 dB)

- **Location:** clause 6.2, "Measurement of blocking force in the direct
  method", NOTE 1 to Inequality (3).
- **The print:** "Inequality (3) is equivalent to the requirement that
  $|L_{F_\mathrm{b}} - L_{F_2}| \leqslant 05$ dB."
- **The problem:** the decimal comma is missing: the bound is 0,5 dB, not
  5 dB. Inequality (3) itself, $m_0 \leqslant 0{,}06 \times 10^{L_{F2}/20} /
  10^{L_{a2}/20}$ kg, limits the inertia force $m_0 a_2$ to 6 % of the
  measured force, so the two force levels differ by at most
  $20\lg 1{,}06 = 0{,}51$ dB with the inertia force in phase and
  $-20\lg 0{,}94 = 0{,}54$ dB against it: 0,5 dB, a tenth of what the note
  reads. ISO 10846-2:2008, which states the same inequality for resilient
  supports (its Inequality (2)), prints the same note with the comma in
  place, "$L_{F_2'} - L_{F_2} \leqslant 0{,}5$ dB".
- **Evidence:** the note beside the inequality it restates, and the same note
  in the companion part. Verified on PDF page 30 (printed p. 20) of BS EN ISO
  10846-4:2003, the UK implementation of ISO 10846-4:2003 (first edition), and
  on PDF page 21 (printed p. 13) of BS EN ISO 10846-2:2008.
- **Library behaviour:** no change required, since the library computes the
  inequality, not the note. `check_output_mass` reports the bias the mass can
  cause, `bias_bound_db`, which is 0,54 dB on the bound, and the conformance
  check "ISO 10846-4:2003 6.2 NOTE 1" holds it against the 0,5 dB the note
  means.
- **Status:** unreported.

## UNE-EN 15657:2018, Clause 7.1, Formula (14) (reference mass dimensionally inconsistent with the quantity it normalises)

- **Location:** Clause 7.1, the sentence introducing Formula (14) (printed
  p. 14) and Formula (14) itself (printed p. 15), the structural power level
  injected into the reception plate.
- **The print:** the sentence reads "a partir del nivel de velocidad promediado
  espacialmente de la placa $L_v$, de la **masa por unidad de superficie** $m$,
  del área de la placa $S$ y del factor de pérdida $\eta$, utilizando
  $f_0 = 1$ Hz, $m_0 = 1$ kg y $S_0 = 1$ m² como referencias", above
  $L_{Ws} = \left(10\lg\left(\dfrac{2\pi f m \eta S}{f_0 \cdot m_0 \cdot S_0}\right)\right)\text{dB} + L_v - 60\ \text{dB}$.
- **The problem:** the same sentence defines $m$ as a mass per unit area, in
  kg/m², and its reference $m_0$ as 1 kg. With $m$ in kg/m² and $S$ in m², the
  group $2\pi f\,\eta\,m\,S / (f_0 m_0 S_0)$ is dimensionless only if $m_0$ is
  1 kg/m²; as printed it carries a leftover m⁻². The closing constant confirms
  the intended reading: $10\lg(f_0 m_0 S_0 v_0^2 / P_0) = -60$ dB with
  $v_0 = 10^{-9}$ m/s and $P_0 = 1$ pW closes in watts only when $f_0 m_0 S_0$
  has the units of an area density times an area times a frequency. The numeric
  result is unaffected, because $10\lg(1) = 0$ whichever unit is attached, which
  is why the slip survives a worked example.
- **Evidence:** dimensional analysis of Formula (14) against the definition of
  $m$ in the sentence above it, and against the $-60$ dB constant it closes on;
  the sentence and the formula were read as images, not from extracted text.
  Verified on PDF page 14 (printed p. 14) and PDF page 15 (printed p. 15) of
  UNE-EN 15657:2018. Only the Spanish-language adoption was read, so this entry
  does not establish whether the English EN 15657:2018 print carries the same
  reference.
- **Library behaviour:** no change required. `characteristic_reception_plate_power`
  takes `mass_per_area` in kg/m² and reproduces the standard's own worked values,
  so the intended reading is the implemented one; the guide and the docstring
  keep the printed reference and name this entry beside it.
- **Status:** unreported.

## ISO 12999-1:2020, Table 4 (missing 500 Hz row)

- **Location:** Table 4 (in-situ uncertainties per band).
- **The print:** the 2020 edition's table omits the 500 Hz row that the 2014
  edition prints (situation B 1,2 dB / situation C 0,8 dB).
- **The problem:** likely an editorial omission; the surrounding rows are
  unchanged between editions and the text does not mention removing the band.
- **Evidence:** side-by-side comparison of the 2014 and 2020 prints.
- **Library behaviour:** follows the 2020 print as published, with the
  omission documented in the module.
- **Status:** unreported.

## ISO 12999-2:2020, Clause 8 wording vs Tables 4 and 5

- **Location:** Clause 8 **"Reporting uncertainties"** (printed pp. 5-6), the
  where-list under Formula (10), against the worked Tables 4 and 5 (printed p.
  7). An earlier revision of this entry called the clause "expression of
  results", which is not its printed title.
- **The print:** the where-list defines $u$ as "the standard uncertainty
  determined in accordance with Clause 5, Clause 6 or Clause 7 **rounded to
  two decimal digits for absorption coefficients** or one decimal digit for
  all other quantities", and Formula (10) then forms $U = k \cdot u$.
- **The problem:** the document's own Tables 4 and 5 only reproduce when $U$
  is computed from the unrounded $u$ and rounded last. Neither table prints a
  $u$ column at all (each has only the coefficient $\alpha_s$ or $\alpha_p$
  and $\pm U$ with $k = 2$), so the printed $U$ values are the whole of the
  evidence, and 11 of the 25 are unreachable under the literal clause wording.
- **Evidence:** recomputation of all 25 entries (Table 4: 20 rows, Table 5: 5
  rows) from Formula (1) with the Table 1 constants and from Formula (4) with
  the Table 2 constants, under both conventions. Round-last reproduces 25 of
  25; round-first misses 11 of 25 (63, 125, 160, 200, 250, 1250, 1600, 2000,
  3150 and 4000 Hz of Table 4, and 250 Hz of Table 5). An earlier revision of
  this entry quoted the count as "10 of 20", which is neither the right
  numerator nor the right number of entries. Verified on PDF pages 9 (printed
  p. 3), 10 (printed p. 4), 11 (printed p. 5) and 13 (printed p. 7) of ISO
  12999-2:2020.
- **Library behaviour:** rounds last, matching the tables; the convention is
  documented and tested.
- **Status:** unreported.

## ISO 12999-2:2020, Table 5 (octave-band data under a one-third-octave header)

- **Location:** clause 8, Table 5 "Example for the practical sound absorption
  coefficient, αp, and its expanded uncertainty under reproducibility
  conditions" (printed p. 7).
- **The print:** the frequency column of Table 5 is headed **"One-third octave
  midband frequency / Hz"** and its rows are 250, 500, 1 000, 2 000 and 4 000
  Hz.
- **The problem:** those five frequencies are the **octave**-band series of
  ISO 11654, which is what the practical sound absorption coefficient
  $\alpha_p$ is defined over; they are not a one-third-octave series, and no
  one-third octave band is missing between them. The document contradicts
  itself on the same quantity two pages earlier: Table 2, which supplies the
  $m$ and $n$ constants of Formula (4) for exactly these five frequencies, is
  headed "Octave midband frequency". The same header text stands over Table 4
  on the same page, where it is correct: that table carries a genuine
  one-third-octave series, 63 Hz to 5 000 Hz in 20 rows.
- **Evidence:** the five tabulated frequencies themselves, and the "Octave
  midband frequency" header of Table 2 for the same $\alpha_p$ constants.
  Verified on PDF page 13 (printed p. 7) and PDF page 11 (printed p. 5) of ISO
  12999-2:2020.
- **Library behaviour:** `_TABLE2` in
  [`uncertainty.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/uncertainty.py) is
  keyed by *octave* midband frequency, following Table 2 and the ISO 11654
  definition of $\alpha_p$ rather than the Table 5 header.
- **Status:** unreported.

## ISO 10052:2021, Table 4 volume-range header

- **Location:** Table 4 (reverberation-index estimator), volume-range header.
- **The print:** the header reads "60 ≤ V < 150" while the body text says the
  method applies to rooms "up to 150 m³".
- **The problem:** the boundary $V = 150\ \text{m}^3$ is included by the text
  and excluded by the header.
- **Evidence:** direct comparison of header and clause text.
- **Library behaviour:** accepts $V = 150$ (follows the text), with the
  ambiguity noted.
- **Status:** unreported.

## ISO 16283-1:2014, Clause 6 (a source-room reverberation time)

- **Location:** Clause 6 "General", the paragraph on the reverberation time
  (printed p. 6).
- **The print:** "For the reverberation time, the low-frequency procedure
  shall be used for the 50 Hz, 63 Hz, and 80 Hz one-third octave bands in
  **the source and/or receiving room** when its volume is smaller than 25 m³
  (calculated to the nearest cubic metre)."
- **The problem:** ISO 16283-1 measures no source-room reverberation time, so
  there is nothing in the source room for a reverberation-time procedure to be
  used on. The first paragraph of the same clause, five paragraphs and a
  NOTE earlier,
  lists the required measurements as "the sound pressure levels in both rooms
  with the source(s) operating, the background noise in the receiving room ...
  and the reverberation times **in the receiving room**". Clause 10, which is
  where the reverberation-time procedures are actually specified, says the same
  thing four times over: its heading is "Reverberation time **in the receiving
  room** (default and low-frequency procedure)", its Clause 10.1 scopes the
  whole clause to "the receiving room", its Clause 10.3 branches on whether
  "the receiving room has a volume larger than or equal to 25 m³", and its
  Clause 10.4 applies the low-frequency procedure "when **the receiving room**
  volume is smaller than 25 m³". The phrase is correct two paragraphs
  above, one of them the NOTE,
  where it belongs: the *sound pressure level* really is measured in both rooms
  and its low-frequency procedure really does apply to either. It was carried
  down into the reverberation-time sentence, where only one room exists. The
  other two parts print the same sentence with one room: ISO 16283-2:2020
  Clause 6 and ISO 16283-3:2016 Clause 6 both read "in the receiving room when
  its volume is smaller than 25 m³", so Part 1 is the outlier of the three.
- **Evidence:** the sentence on PDF page 12 (printed p. 6) of ISO 16283-1:2014,
  identical on PDF page 14 (printed p. 6) of BS EN ISO 16283-1:2014; Clause 10
  and its subclauses on PDF pages 23 and 24 (printed pp. 17 and 18) of the same
  document; and the one-room version of the sentence on PDF page 13 (printed p.
  7) of ISO 16283-2:2020 and PDF page 16 (printed p. 10) of ISO 16283-3:2016.
- **Library behaviour:** the 63 Hz octave substitution is a receiving-room
  operation in every part, following Clause 10; a source-room procedure that
  carries a 63 Hz octave reverberation time is refused, and a source-room call
  takes no reverberation times at all. The corner procedure for the *level*,
  which is the paragraph the phrase belongs to, does admit both rooms in
  ISO 16283-1 and the airborne entry point offers both.
- **Status:** unreported.

## ISO 16283-2:2020, Clause 8.3 (a source room in an impact measurement)

- **Location:** Clause 8.3 "Microphone positions", last paragraph (printed p.
  15).
- **The print:** "For the 50 Hz, 63 Hz and 80 Hz one-third octave bands,
  calculate the low-frequency energy-average sound pressure level **for the
  source and/or receiving room** according to 8.5."
- **The problem:** an impact measurement has no source-room sound pressure
  level to calculate. Every other statement of the same procedure in the same
  part names one room: Clause 6 introduces it as used "in the receiving room
  when its volume is smaller than 25 m³" (printed p. 6), Clause 8.1 repeats "in
  the receiving room" (printed p. 14), Clause 8.5 builds
  $L_\text{i,Corner}$ from corners of the receiving room (printed p. 16), and
  Formulae (1) and (3), which the same sentence sends the reader to, are
  written in $L_\text{i}$, the energy-average impact sound pressure level in
  the receiving room. The phrase is correct where it comes from: ISO 16283-1
  Clause 8.3 says "for the source and/or receiving room" of an airborne
  measurement, where both rooms do carry a level. It was carried across into
  the impact part and survived the revision unchanged.
- **Evidence:** the sentence on PDF page 21 (printed p. 15) of ISO 16283-2:2020
  beside the same sentence on PDF page 23 (printed p. 15) of the ISO/DIS
  16283-2 text circulated as BSI DPC 13/30269186 DC, and the airborne original
  on PDF page 21 (printed p. 15) of ISO 16283-1:2014.
- **Library behaviour:** the impact entry point takes a receiving-room
  low-frequency procedure and nothing else, following Clause 6, 8.1 and 8.5;
  only the airborne entry point, where ISO 16283-1 Clause 8.1 really does admit
  both rooms, offers a source-room one.
- **Status:** unreported.

## ISO 16283-2:2020, Clause 10.3 (a receiving room of exactly 25 m³)

- **Location:** Clause 10.3 "Default procedure" for the reverberation time
  (printed p. 18).
- **The print:** "for all one-third octave bands between 50 Hz and 5 000 Hz
  when the receiving room has a volume **larger than** 25 m³ (calculated to the
  nearest cubic metre) and between 100 Hz and 5 000 Hz when the receiving room
  has a volume smaller than 25 m³ (calculated to the nearest cubic metre)".
- **The problem:** a receiving room that rounds to exactly 25 m³ falls in
  neither branch, so the clause states no frequency range for it. The other two
  parts print "larger than **or equal to** 25 m³" in the otherwise identical
  sentence, which closes the boundary. The intended reading is not in doubt:
  the trigger of Clause 8.1 and Clause 10.4 is "smaller than 25 m³" in all
  three parts, so 25 m³ belongs to the larger branch and takes the full 50 Hz
  to 5 000 Hz default range.
- **Evidence:** PDF page 24 (printed p. 18) of ISO 16283-2:2020, against PDF
  page 24 (printed p. 18) of ISO 16283-1:2014 and PDF page 24 (printed p. 18)
  of ISO 16283-3:2016, both of which carry the "or equal to". The gap is not a
  2020 slip and not an artefact of a draft: the ISO/DIS text on PDF page 26
  (printed p. 18) of BSI DPC 13/30269186 DC already read the same way, and so
  does the published previous edition, whose Clause 10.3 on PDF page 25
  (printed p. 25) of UNE-EN ISO 16283-2:2016, the Spanish translation of
  ISO 16283-2:2015, reads "un volumen **superior a** 25 m³" with no "o igual
  a". The wording has stood unchanged across two editions and one revision.
- **Library behaviour:** the trigger predicate is the strict "smaller than
  25 m³" the three parts share, so a room of exactly 25 m³ takes the default
  procedure in every part and no gap exists.
- **Status:** unreported.

## ISO 17208-2:2019, Clause 5 uncertainty band coverage

- **Location:** Clause 5 (representative expanded uncertainties), printed p.
  4.
- **The print:** "5 dB for the low frequency (10 Hz to 100 Hz) bands, 3 dB for
  the mid frequency (125 Hz to 16 000 Hz) bands, and 4 dB for the high
  frequency (**>20 000 Hz**) bands".
- **The problem:** the 20 kHz one-third-octave band itself is left unassigned:
  the mid range ends at 16 kHz *inclusive* and the high range starts strictly
  above 20 kHz. ISO 17208-1:2016, from which clause 5 says the values are
  taken, prints the same three ranges with "**≥20 000 Hz**", which closes the
  gap; Part 2 degraded the $\ge$ to a $>$. The 20 kHz band is not a corner
  case for this document: ISO 17208-1 Table 1 requires the measurement to
  cover "20 000 Hz (minimum)" as its upper one-third-octave band. An earlier
  revision of this entry said "nothing covers 16 kHz to 20 kHz inclusive",
  which is wrong at the lower end: 16 kHz is covered.
- **Evidence:** the two clauses side by side. Verified on PDF page 10 (printed
  p. 4) of ISO 17208-2:2019 and PDF page 22 (printed p. 16) of ISO
  17208-1:2016.
- **Library behaviour:** applies the conservative 4 dB high-band value from
  the 20 kHz band upwards, following Part 1, with the gap documented.
- **Status:** unreported.

## ECMA-418-1:2024 (3rd edition), clause 4.1.1 NOTE 2 (upper limit of the discrete-tone range)

- **Location:** clause **4.1.1** "frequency range of interest", NOTE 2
  (printed p. 2). An earlier revision of this entry cited clause 4.1.2, which
  is the definition of "ITT equipment" and says nothing about frequency.
- **The print:** "From viewpoint of test implementation by using FFT analyser,
  the frequency range of discrete tones are between 89,1 Hz and 11 220 Hz
  inclusive, referred to *the discrete tone frequency range of interest*."
- **The problem:** every formula and table of the standard works to 11 200 Hz:
  the Table 2 and Table 3 band-edge fits are stated for
  $11\,200 \ge f_t > 1\,600$, and clauses 10, 12.3 and 12.4 permit FFT data
  with $f_1 < 89{,}1\ \text{Hz}$ and $f_2 > 11\,200\ \text{Hz}$. The two
  numbers are the same quantity to different precision rather than a
  typographical error: $10\,000 \cdot 2^{1/6} = 11\,224{,}6\ \text{Hz}$ is the
  upper edge of the 10 kHz one-third-octave band that closes the range of
  interest, which rounds to 11 220 Hz at four significant figures and to
  11 200 Hz at three. An earlier revision of this entry called it a typo and
  added that "no other clause mentions 11 220 Hz"; the last x-axis tick of
  Figure 6 (printed p. 20) is labelled 11220. What clause 4.1 does carry is a
  structural defect: 4.1.2 "ITT equipment" repeats 4.1.1's NOTE 1 verbatim
  ("This range was selected to be identical to that of ECMA-74:2022, 3.1.3"),
  although 4.1.2 defines no range at all, and clause 10 then cross-references
  "NOTE 1 of 4.1.2" for the discrete-tone range, which is the duplicated note
  rather than the NOTE 2 that states it.
- **Evidence:** the arithmetic above, and the Table 2/3 ranges and Figure 6
  axis read side by side with NOTE 2. Verified on PDF page 10 (printed p. 2),
  PDF page 18 (printed p. 10), PDF page 25 (printed p. 17) and PDF page 28
  (printed p. 20) of ECMA-418-1:2024 (3rd edition).
- **Library behaviour:** uses the internally consistent $89{,}1\ \text{Hz}$ to
  11 200 Hz range (upper end exclusive per the formulas), with a code note in
  [`tonality.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tonality.py).
- **Status:** unreported.

## ECMA-418-1:2024 (3rd edition), Formula (21) (repeated constant term)

- **Location:** clause 12.3, Formula (21) (printed p. 17), the curve fit for
  the lower band-edge frequency $f_{1,L}$ of the lower critical band.
- **The print:** $f_{1,L} = C_{L,0} + C_{L,0} f_t + C_{L,2} f_t^{2}$.
- **The problem:** the linear coefficient repeats the constant term. The
  where-list immediately below the formula declares "$C_{L,0}$, $C_{L,1}$,
  $C_{L,2}$ are constants given in Table 2", Table 2 tabulates a $C_{L,1}$
  column, and the parallel Formula (22) for the upper band edge prints
  $f_{2,U} = C_{U,0} + C_{U,1} f_t + C_{U,2} f_t^{2}$ correctly. The misprint
  is numerically fatal, not cosmetic: over the middle fit range
  ($171{,}4 \le f_t \le 1\,600$) Table 2 gives $C_{L,0} = -149{,}5$ and
  $C_{L,1} = 1{,}001$, so the printed form returns
  $-149{,}5 - 149{,}5 f_t - 6{,}90 \cdot 10^{-5} f_t^2$, negative everywhere,
  instead of a band edge a little below $f_t$.
- **Evidence:** the formula, its own where-list and Table 2 on one page, with
  Formula (22) as the consistent control. Verified on PDF page 25 (printed p.
  17) of ECMA-418-1:2024 (3rd edition).
- **Library behaviour:** implements the $C_{L,1}$ reading, which is the only
  one that returns a usable band edge, with a code note in
  [`tonality.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tonality.py).
- **Status:** unreported.

## ECMA-418-1:2024 (3rd edition), clause 11.3 (unresolved field references)

- **Location:** clause 11.3 "Determination of masking noise level" (printed p.
  12), the sentence introducing the critical bandwidth.
- **The print:** "The critical bandwidth Δf_c is determined from Formula
  **Error! Reference source not found.Error! Reference source not found.**
  with f_0 set equal to the frequency of the discrete tone under
  investigation, f_t".
- **The problem:** two unresolved word-processor field references were
  typeset, in bold, in place of the formula numbers, and shipped in the
  published third edition. The intended targets are unambiguous from the rest
  of the sentence, which goes on to name Formulae (4) and (5) or (7) and (8)
  for the band edges: the critical bandwidth itself is Formula (2), and
  Formula (3) is the relation $f_2 - f_1 = \Delta f_c$ that turns it into band
  edges.
- **Evidence:** the clause as printed. Verified on PDF page 20 (printed p.
  12), PDF page 18 (printed p. 10) and PDF page 30 (printed p. 22) of
  ECMA-418-1:2024 (3rd edition).
- **Library behaviour:** none required; the library implements the critical
  bandwidth from Formulae (3)/(6) directly.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 5.1.5.2 (last block index)

- **Location:** clause 5.1.5.2, the segmentation of the zero-padded signal for
  the roughness/fluctuation-strength block sizes.
- **The print:** the index of the last block is given as
  $l_\text{last} = \lceil (n + s_b)/s_h \rceil$.
- **The problem:** the formula is internally inconsistent: blocks placed at
  that index overrun the zero-padded signal defined by clause 5.1.2.2, and the
  resulting Formula (103) time grid becomes non-monotonic. The only
  self-consistent reading is to stop at the last block that fits inside the
  padded signal and align it flush with its end.
- **Evidence:** direct evaluation of the block start indices against the
  padded length for the clause 7.1.1 block/hop sizes; the flush-to-end reading
  reproduces the Clause 7 roughness calibration ($1\ \text{asper}$) to
  $0{,}9999$.
- **Library behaviour:** implements the flush-to-end reading with a code note
  in
  [`roughness_ecma.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/roughness_ecma.py).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9.1.4, Formula (127) (HSA kernel phase)

- **Location:** clause 9.1.4, Formula (127), the spectral kernel of the
  envelope analysis window used by the High-resolution Spectral Analysis.
- **The print:** the kernel's phase factor is
  $\exp(-j \cdot 2\pi \cdot f_n(k) \cdot (\tilde{s}_b - n_{ze} + n_{zb} - 1))$.
- **The problem:** the kernel is, by construction, the DFT of the rectangular
  analysis window of Formula (120) modulated to the candidate rate; that is
  the model Formula (124) fits to the measured DFT spectrum. That DFT has the
  phase
  $\exp(-j \cdot \pi \cdot f_n \cdot (\tilde{s}_b - n_{ze} + n_{zb} - 1))$;
  the printed factor doubles it (and is also inconsistent with the $\pi$
  arguments of the printed sine terms of the same formula). With the printed
  phase the fitted model cannot reproduce the spectrum of a noiseless windowed
  sinusoid, contradicting the clause's own statement that the HSA achieves
  "theoretically infinite resolution for signals without noise".
- **Evidence:** independent derivation of the window DFT plus numerical
  recomputation: with $\pi$ the least-squares fit recovers the constant part,
  amplitudes and phases of synthetic noiseless envelopes to machine precision
  and the Formula (135) residual vanishes; with the printed $2\pi$ the kernel
  deviates from the window DFT by amounts of the order of the kernel itself
  and the residual stays of the order of the signal energy.
- **Library behaviour:** implements the $\pi$ reading, pinned by a regression
  test on the exact recovery of synthetic line pairs.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9.1.5, Formula (144) (bin offset)

- **Location:** clause 9.1.5, Formula (144), the modulation rate of a local
  maximum of the envelope power spectrum.
- **The print:** the rate is the three-bin amplitude-weighted centroid of the
  peak position **minus one**, scaled by $\Delta f$.
- **The problem:** clause 9.1.4 (below Formula (122)) defines the spectral
  index $k$ as mapping to the modulation rate
  $k \cdot \tilde{r}_s/\tilde{s}_b$ with $k$ starting at 0. A symmetric local
  maximum at bin $k$ has centroid $k$, and the printed formula then assigns it
  the rate $(k - 1) \cdot \Delta f$, one full bin ($0{,}73\ \text{Hz}$) low,
  which at fluctuation-strength rates is fatal (a true $1{,}46\ \text{Hz}$
  modulation would be reported as $0{,}73\ \text{Hz}$). The offset is only
  consistent with 1-based spectral-line positions, contradicting the
  standard's own definition of $k$.
- **Evidence:** cross-check of Formula (144) against the $k$-to-rate mapping
  stated below Formula (122).
- **Library behaviour:** uses the centroid directly (no offset) with the
  0-based $k$ of Formula (122).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9.1.7 (units of the fine-tuning constants)

- **Location:** clause 9.1.7, Formulae (149)-(152), the damped Newton fine
  tuning of the dominant modulation rate.
- **The print:** differential step $\Delta x = 10^{-5}$, damped-step cap
  $2 \cdot 10^{-4}$, stop tolerance $10^{-7}$ and an iteration limit of 40,
  with the starting point $x_0 = \tilde{f}_{c,i_\text{max}}$ (a rate in Hz)
  and the failure check
  $|f_{c,1,\text{opt}} - \tilde{f}_{c,i_\text{max}}| > 1{,}25 \cdot \Delta f$.
- **The problem:** the constants carry no units. Read in Hz, the damped step
  is capped at $5 \cdot 10^{-5}\ \text{Hz}$ per iteration
  ($2 \cdot 10^{-3}\ \text{Hz}$ over all 40 iterations), so the tuning cannot
  move appreciably and the $1{,}25 \cdot \Delta f$
  ($\approx 0{,}92\ \text{Hz}$) failure check is unreachable; the whole clause
  would be inert. Read as normalized modulation rates $f/\tilde{r}_s$ (the
  variable in which the Formula (127) kernel frequencies are expressed), the
  same constants give a $0{,}075\ \text{Hz}$ damped per-iteration cap
  ($\approx 2{,}9\ \text{Hz}$ over the 39 iterations), a
  $1{,}5 \cdot 10^{-4}\ \text{Hz}$ stop tolerance and a reachable failure
  check, all consistent with the clause's purpose.
- **Evidence:** dimensional analysis of the printed constants against the
  $0{,}7324\ \text{Hz}$ spectral resolution and the failure threshold.
- **Library behaviour:** applies the constants as normalized modulation rates.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9 introduction (broken cross-reference)

- **Location:** clause 9, third paragraph of the introduction, on the
  HSA-based loudness prediction.
- **The print:** "loudness scaling is improved by using HSA-based loudness
  prediction (see Clause 0)".
- **The problem:** "Clause 0" does not exist; the HSA-based loudness scaling
  is described in clause 9.1.10 (an unresolved field reference).
- **Evidence:** the clause listing of the standard itself.
- **Library behaviour:** none required (the intended target is unambiguous).
- **Status:** unreported.

## ISO/PAS 20065:2016, clause 5.3.4 (edge steepness of a distinct tone)

- **Location:** clause 5.3.4, Formulae (10)/(11) (printed p. 9), the minimum
  edge steepness of a distinct tone.
- **The print:** the two edges are scaled differently:
  $\Delta L_u = (f_T/2) \cdot (L_{T\text{max}} - L_u)/(f_T - f_u) \ge 24\ \text{dB}$
  and
  $\Delta L_o = f_T \cdot (L_{T\text{max}} - L_o)/(f_o - f_T) \ge 24\ \text{dB}$.
- **The problem:** the parent standard DIN 45681:2005-03 prints $f_T/\sqrt{2}$
  on **both** edges (Gleichungen (10)/(11), printed p. 14), and its executable
  Anhang J reference program does the same (`Frequenz(i)/Sqr(2)`). The two
  prints cannot both be satisfied. Neither ISO factor is the DIN one: on the
  lower edge $1/2 < 1/\sqrt{2}$, so the ISO print returns a level difference
  $\sqrt{2}$ **smaller** and is therefore **stricter**; on the upper edge the
  divisor is absent altogether, so the ISO print returns $\sqrt{2}$ **larger**
  and is **more lenient**. An earlier revision of this entry had the two
  directions the other way round and described the upper edge as "halved",
  where in fact the divisor is missing rather than halved. Borderline tones
  with one-sided edge steepness between $24/\sqrt{2} = 17$ and
  $24 \cdot \sqrt{2} = 34\ \text{dB/octave}$ flip classification between the
  two readings.
- **Evidence:** side-by-side comparison of the ISO print, the DIN 45681 print
  and the DIN Anhang J program. The DIN radicals are exactly the case the page
  rule exists for: `pdftotext` drops the `√` glyph from both DIN formulae, so
  the extracted text reads `f_T/2` and matches the ISO print, while the page
  itself reads `f_T/√2`. Verified on PDF page 13 (printed p. 9) of ISO/PAS
  20065:2016 and PDF page 14 (printed p. 14) of DIN 45681:2005-03.
- **Library behaviour:** follows the DIN/$\sqrt{2}$ reading (it matches the
  only executable reference), with the choice recorded in
  [`tone_audibility.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tone_audibility.py).
- **Status:** unreported.

## DIN 45681:2005-03, Anhang I, Tabelle I.6, row "6 FG"

- **Location:** Anhang I, Beispiel I.2 (combustion engine, spectrum $j = 1$),
  Tabelle I.6, the combined row "6 FG" for the three tones $k = 6/7/8$
  ($592{,}2$ / $629{,}8$ / $643{,}3\ \text{Hz}$, tone levels $78{,}31$ /
  $75{,}00$ / $79{,}75\ \text{dB}$).
- **The print:** $L_T = 81{,}11\ \text{dB}$ together with
  $\Delta L = 9{,}12\ \text{dB}$ (with $L_S = 59{,}53$, $L_G = 76{,}16$,
  $a_v = -2{,}40$ at $592{,}2\ \text{Hz}$).
- **The problem:** the two cells contradict each other. The printed
  $\Delta L = 9{,}12\ \text{dB}$ only reproduces from the *plain* Formula (17)
  energy sum of the three tone levels ($82{,}873\,4\ \text{dB}$):
  $82{,}87 - 76{,}16 + 2{,}40 = 9{,}11$. The printed
  $L_T = 81{,}11\ \text{dB}$ is that same sum less exactly
  $1{,}763\ \text{dB}$, and taken at face value it would give
  $\Delta L = 7{,}35\ \text{dB}$.
- **Evidence:** recomputation from the printed per-tone levels of Tabelle I.6.
  The offset is the discriminator and it is a constant, not a deduplication:
  $82{,}873\,4 - 81{,}11 = 1{,}763\ \text{dB}$, and $1{,}76\ \text{dB}$ is
  $10\log_{10} 1{,}5$, the standard's own Hanning effective-bandwidth
  correction (clause 5.3.2). The same offset appears in the "5 FG" row of
  Tabelle I.10 (printed p. 46), where the two member tones at $705{,}2$ and
  $732{,}1\ \text{Hz}$ have $L_T = 55{,}12$ and $54{,}23\ \text{dB}$, sum to
  $57{,}708\ \text{dB}$, and are printed as $55{,}95\ \text{dB}$,
  $1{,}758\ \text{dB}$ lower, and there the printed
  $\Delta L = 3{,}22\ \text{dB}$ follows the printed $L_T$ exactly
  ($55{,}95 - 55{,}28 + 2{,}55 = 3{,}22$), so the Tabelle I.10 row is
  internally consistent and the Tabelle I.6 row is not. The third combined
  row, "2 FG" of the same Tabelle I.6, carries no offset at all: its three
  member levels $64{,}56$ / $67{,}96$ / $68{,}63\ \text{dB}$ sum to
  $72{,}149\ \text{dB}$ against a printed $72{,}15\ \text{dB}$, and its
  $\Delta L$ follows. A previous revision of this entry attributed the
  $81{,}11\ \text{dB}$ cell to the Anmerkung 2 shared-line deduplication; that
  diagnosis is unsupported, because a deduplication removes an arbitrary
  amount of energy while all the offsets observed here are the same 1,76 dB.
  Verified on PDF page 41 (printed p. 41) and PDF page 46 (printed p. 46) of
  DIN 45681:2005-03.
- **Library behaviour:** `combined_tone_level` follows Anmerkung 2 (shared
  lines counted once), which reproduces the printed "2 FG" oracle; for the "6
  FG" row only the $\Delta L$ chain is pinned, with the contradiction recorded
  in `tests/reference_data/`.
- **Status:** unreported.

## DIN 45681:2005-03, Anhang I, Tabellen I.2 and I.10 (wrong spectrum index in a column header)

- **Location:** Anhang I, the column headers of Tabelle I.2 (printed p. 37,
  spectrum $j = 2$) and Tabelle I.10 (printed p. 46, spectrum $j = 24$).
- **The print:** every column of Tabelle I.2 is subscripted with the spectrum
  index 2 (`f_T 2,k`, `f_1 2,k`, `f_2 2,k`, `L_S 2,k`, `L_T 2,k`, `L_G 2,k`,
  `a_v 2,k`, `u_2,k`) except the audibility column, which is headed
  **`ΔL_1,k`**. Every column of Tabelle I.10 is subscripted 24 (`f_T 24,k`,
  `ΔL 24,k`, `f_1 24,k`, `f_2 24,k`, `L_S 24,k`, `L_T 24,k`, `L_G 24,k`,
  `u 24,k`) except the masking column, which is headed **`a_v 1,k`**.
- **The problem:** both tables carry the spectrum index of the *first*
  spectrum in one column. Tabelle I.2's own caption reads "des zweiten
  Spektrums (j = 2)" and Tabelle I.10's "des 24. Spektrums (j = 24)", and the
  body values belong to those spectra: the $\Delta L$ column of Tabelle I.2 is
  the audibility of the $j = 2$ tones ($8{,}53\ \text{dB}$ at
  $627{,}2\ \text{Hz}$, which the Anmerkung below the table calls "die
  maßgebliche Differenz ΔL_2"), and the $a_v$ column of Tabelle I.10 is the
  masking index of the $j = 24$ tones. The index 1 is right in exactly one
  table of the annex, Tabelle I.6, which is the $j = 1$ table of Beispiel I.2
  and carries both `ΔL_1,k` and `a_v 1,k` legitimately.
- **Evidence:** the tables' own captions, their neighbouring column
  subscripts, and the Anmerkung under each. Verified on PDF page 37 (printed
  p. 37), PDF page 46 (printed p. 46), and PDF page 41 (printed p. 41) of DIN
  45681:2005-03.
- **Library behaviour:** none needed; the numbers are unaffected. The
  regression fixtures index both tables by their caption's spectrum.
- **Status:** unreported.

## IEC 60268-1:1985, Appendix A, Figure A1 (last shunt capacitor printed as 41.47 nF)

- **Location:** Appendix A, "Noise weighting network and quasi-peak meter",
  Figure A1 "Weighting network" (printed p. 29), drawing 0641/85. The French
  print of the same artwork (printed p. 28) carries the same value as
  `41,47 nF`.
- **The print:** the last shunt capacitor of the ladder, the one across the
  600 Ω amplifier input, is labelled **41.47 nF**.
- **The problem:** it should be **31.47 nF**, which is what ITU-R BS.468-4
  Figure 1a prints for the same network. Every other element of Figure A1
  matches BS.468-4 Figure 1a exactly: 600 Ω source, 13.85 nF, 12.88 mH,
  26.82 nF, 33.06 nF, 9.21 nF, 26.49 mH and Z = 600 Ω. The intended reading is
  not in doubt, because the document contradicts itself: evaluated against
  Table AI, printed two pages earlier in the same annex, the 31.47 nF ladder
  reproduces all 21 rows to a maximum of **0.050 dB** and violates no
  tolerance, while the 41.47 nF ladder is out by up to **2.252 dB** (at
  31 500 Hz) with a root-mean-square error of 1.055 dB and **breaks Table AI's
  own tolerance column at seven frequencies**, every one from 8 000 Hz to
  20 000 Hz: −0.40 dB against ±0.40 at 8 kHz, −0.74 against ±0.60 at 9 kHz,
  −1.16 against ±0.80 at 10 kHz, −1.85 against ±1.20 at 12.5 kHz, −1.98
  against ±1.40 at 14 kHz, −2.05 against ±1.60 at 16 kHz and −2.12 against
  ±2.00 at 20 kHz. Sweeping the capacitor to minimise the error against
  Table AI lands on 31.4798 nF.
- **Evidence:** the two ladders evaluated independently by an ABCD chain
  product over the seven printed reactive elements between the printed 600 Ω
  source and load, normalised at 1 kHz, and compared row by row with Table AI
  and its tolerance column. Neither Amendment 1:1988 (which replaces Table AII
  only) nor Amendment 2:1988 (which replaces sub-clause 12.1, on producing a
  uniform alternating magnetic field) touches Figure A1, so the misprint
  stands in the current document as amended. Verified on PDF page 31 (printed
  p. 29) and PDF page 29 (printed p. 27), which carries Table AI, of IEC
  60268-1:1985, and on PDF page 1 (printed p. 1) of Recommendation ITU-R
  BS.468-4.
- **Library behaviour:** unaffected. The weighting network is built from the
  BS.468-4 Figure 1a component values in
  [`filters/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/weighting.py), with
  31.47 nF, and the Table 1 rows are the oracle. The entry matters because IEC
  60268-3:2013 sub-clause 14.12.11 sends a reader to "a weighting network
  complying with Appendix A of IEC 60268-1", so a clean-room implementation
  started from IEC 60268-3 lands on the wrong capacitor.
- **Status:** unreported.

## IEC 60268-1:1985, Appendix A, Table AII (lower-limit row slipped one column)

- **Location:** Appendix A, Table AII, the tone-burst dynamic characteristic
  of the quasi-peak meter, "Limited values — lower limit" row (printed p. 31).
- **The print:** the lower limit (%) row reads
  `13.5 | 22.4 | 34 | 41 | 44 | 44 | 50 | 68` for the 1, 2, 5, 10, 20, 50, 100
  and 200 ms columns, while the (dB) row printed immediately beneath it reads
  `−17.4 | −13.0 | −9.3 | −7.7 | −7.1 | −6.0 | −4.7 | −3.3`.
- **The problem:** the 50 ms and 100 ms cells contradict their own dB cells.
  −6.0 dB is 50.1 %, not 44 %, and −4.7 dB is 58.2 %, not 50 %. The percentage
  row has slipped one column to the right from 50 ms onwards, carrying the
  20 ms and 50 ms values into the two cells after them; the dB row and the
  200 ms cell stayed where they belong. ITU-R BS.468-4 Table 2 prints
  `... | 44 | 50 | 58 | 68` for the same four columns.
- **Evidence:** the two rows of the same table read against each other, and
  against the corresponding row of ITU-R BS.468-4 Table 2. **Corrected by
  Amendment 1:1988-01**, whose English sheet is headed "Page 31 / Replace
  Table AII by the following:" and prints the lower limit row as
  `13.5 | 22.4 | 34 | 41 | 44 | 50 | 58 | 68`, matching BS.468-4; every other
  cell of the replacement table is identical to the base print, so this row is
  the entire substantive content of the amendment. Verified on PDF page 33
  (printed p. 31) of IEC 60268-1:1985, on PDF page 3 (printed p. 3) of IEC
  60268-1:1985 Amendment 1:1988, and on PDF page 4 (printed p. 4) of
  Recommendation ITU-R BS.468-4.
- **Library behaviour:** unaffected. The eleven acceptance windows are
  transcribed from BS.468-4 Tables 2 and 3 in
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data), which agree with the
  amended IEC table. Recorded because the unamended base document is the one a
  reader is likely to hold, and it widens the 50 ms and 100 ms acceptance
  windows by 1.1 dB and 1.3 dB at the bottom.
- **Status:** unreported (corrected by the issuing body in 1988).

## ITU-R BS.468-4, Table 2, 5 ms upper limit (the dB cell should read −6.7)

- **Location:** clause 2.1, Table 2, "Limiting values — upper limit", the 5 ms
  column (printed p. 4). The same pair of cells is printed identically in
  IEC 60268-1:1985 Table AII and in the Amendment 1:1988 table that replaces
  it, so the defect is inherited from the CCIR text rather than introduced by
  either edition.
- **The print:** `46` in the (%) row and `−6.6` in the (dB) row.
- **The problem:** the two disagree. 46 % is 20 lg(0.46) = **−6.745 dB**, and
  −6.6 dB is 46.8 %. All 33 cells of Tables 2 and 3 were audited against their
  own counterpart; 32 agree to within 0.050 dB, the rounding of a
  two-significant-figure percentage, and this one is out by 0.145 dB. The
  neighbouring 5 ms *lower* limit (`34`, `−9.3`) is out by 0.070 dB and is
  benign, because 34 % as a rounded two-figure percentage covers 33.5 % to
  34.5 %, that is −9.500 dB to −9.241 dB, and −9.3 lies inside it. The upper
  cell is not benign: 46 % covers 45.5 % to 46.5 %, that is −6.840 dB to
  −6.651 dB, which excludes −6.6.
- **Which cell is wrong:** the dB one. Read as percentages, the acceptance
  window is a very steady −1.4 dB / +1.2 dB about the reference reading for
  every duration from 5 ms to 200 ms (+1.18 to +1.24 dB above, −1.37 to
  −1.45 dB below). 46 % puts the 5 ms upper limit +1.214 dB above its
  reference, on that pattern; 46.774 %, which is what −6.6 dB means, would put
  it +1.360 dB above, off it. So 46 % is right and the dB cell should read
  **−6.7**.
- **Evidence:** 20 lg of each printed percentage compared with the printed dB
  cell beside it, for all 24 cells of Table 2 and all 9 of Table 3, and the
  upper- and lower-limit offsets about the reference row recomputed across the
  five durations from 5 ms to 200 ms. Verified on PDF page 4 (printed p. 4) of
  Recommendation ITU-R BS.468-4, on PDF page 33 (printed p. 31) of IEC
  60268-1:1985, and on PDF page 3 (printed p. 3) of IEC 60268-1:1985
  Amendment 1:1988.
- **Library behaviour:** the percentage rows are primary and the dB rows are
  derived from them, which is the decision this entry forces. The eleven
  acceptance windows are stored as percentages in
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data) and checked as
  percentages, in the test suite and in the conformance rows "ITU-R BS.468-4
  Table 2" and "ITU-R BS.468-4 Table 3".
- **Status:** unreported.

## IEC 60268-1:1985, Appendix A, Table AI (16 000 Hz tolerance printed as ±1.65)

- **Location:** Appendix A, Table AI, the tolerance column, 16 000 Hz row
  (printed p. 27; the French Tableau AI on printed p. 26 prints the same
  value).
- **The print:** `±1.65 1)`.
- **The problem:** ITU-R BS.468-4 Table 1 and AES17-2015 Table 1 both print
  **±1.6** for the same row, and the table's own footnote 1) is what settles
  it: the marked tolerances "are obtained by a linear interpolation on a
  logarithmic graph on the basis of values specified for the frequencies used
  to define the mask, i.e. 31.5 Hz, 100 Hz, 1 000 Hz, 5 000 Hz, 6 300 Hz, and
  20 000 Hz". Interpolated on that rule between (6 300 Hz, 0 dB) and
  (20 000 Hz, ±2.0 dB), 16 000 Hz gives 1.6137 dB, which rounds to 1.6 at one
  decimal and to 1.61 at two. No rounding of the rule produces 1.65, and no
  alternative anchor pair does either: taking the 6 300 Hz to 31 500 Hz line
  instead gives 1.6216 dB. The value is also anomalous within its own column,
  which is quoted to one decimal everywhere else.
- **Evidence:** the footnote rule applied to all 14 marked rows of the same
  column, which reproduces every one of them (63 Hz 1.400, 200 Hz 0.8495,
  400 Hz 0.6990, 800 Hz 0.5485, 3 150 and 4 000 Hz 0.5000, 7 100 Hz 0.2070,
  8 000 Hz 0.4136, 9 000 Hz 0.6175, 10 000 Hz 0.7999, 12 500 Hz 1.1863,
  14 000 Hz 1.3825, 31 500 Hz 2.7865) and 16 000 Hz alone disagrees with what
  is printed. Not corrected by Amendment 1:1988 or Amendment 2:1988. Verified
  on PDF page 29 (printed p. 27) of IEC 60268-1:1985 and on PDF page 2
  (printed p. 2) of Recommendation ITU-R BS.468-4.
- **Library behaviour:** none needed. The tolerance mask is taken from
  BS.468-4 Table 1, and the realised digital curve is held to a far tighter
  bound than the mask anyway: the mask governs a measuring instrument
  comprising the amplifier and the network, not a filter's departure from the
  nominal curve.
- **Status:** unreported.

## IEC 60268-3:2013, clause 14.12.9.2 f) (DIM denominator)

- **Location:** clause 14.12.9.2, item f) (printed p. 39), the formula for the
  dynamic intermodulation distortion $d_\text{DIM}$.
- **The print:**
  $d_\text{DIM} = (\sum_{i=1}^{9} {U'_i}^{2})^{1/2} / U_2 \times 100\ \%$.
- **The problem:** the denominator is one of the nine terms of its own
  numerator. Table 2 of the same clause (printed p. 38) defines $U_2$ as the
  intermodulation component at $f_s - 2f_q = 8{,}70\ \text{kHz}$, and item d)
  defines $U_1, U_2, \ldots U_i$ as exactly those components, so the sum
  $i = 1\ldots9$ runs over $U_1 \ldots U_9$ and includes $U_2$. Meanwhile the
  defining clause 14.12.9.1 states the ratio of the r.m.s. sum of the Table 2
  intermodulation product voltages "to the amplitude of the output voltage at
  the frequency f_s", i.e. the 15 kHz sine component $U_s$, the Otala
  convention, and item d) measures "the amplitudes of the sinusoidal signal
  $U_s$" precisely so that it can be used, which the f) formula then never
  does. The denominator should be $U_s$. An earlier revision of this entry
  said that "U2 is used throughout 14.12 for the total output voltage"; that
  is false, in both the English and the French print.
- **Evidence:** Table 2, item d) and item f) read together in both language
  columns of the bilingual edition; the historical DIM literature (Otala)
  defines the ratio to the sine amplitude. Verified on PDF page 41 (printed p.
  39), PDF page 40 (printed p. 38), which carries Table 2, and PDF page 102
  (printed p. 100), which carries the same item f) in the French column, of
  IEC 60268-3:2013.
- **Library behaviour:** follows the 14.12.9.1 definition (reference = the
  output amplitude at $f_s$), with a code comment at the reference measurement
  in [`distortion.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/distortion.py).
- **Status:** unreported.

## IEC 60268-16:2011, Table M.1 (the beta row states the wrong redundancy term)

- **Location:** Annex M, Table M.1 "Example calculation", step 4, the row
  labelled "Sum of beta\*$MTI$ = $MTI_k$ $\times$ beta weighting" (printed
  p. 67), directly below the matching alpha row.
- **The print:** the label reads $MTI_k \times \beta_k$, and the seven cells
  of the row read 0,059 | 0,052 | 0,045 | 0,008 | 0,037 | 0,081 | 0,000,
  summed on the next page as $\sum \text{beta*}MTI = 0{,}282$.
- **The problem:** the label and the cells state different quantities, and the
  label is the one that is wrong. Clause A.5.6 of the same edition (printed
  p. 47) defines the index as
  $STI = \sum_{k=1}^{7} \alpha_k \times MTI_k -
  \sum_{k=1}^{6} \beta_k \times \sqrt{MTI_k \times MTI_{k+1}}$: the redundancy
  term is the *geometric mean of two adjacent bands*, not the band's own
  $MTI_k$. Read against the table's own MTI row, $\beta_k \times MTI_k$ gives
  0,062 | 0,051 | 0,044 | 0,008 | 0,036 | 0,076, summing to 0,277, which
  disagrees with five of the six printed cells and with the printed total.
  $\beta_k\sqrt{MTI_k MTI_{k+1}}$ reproduces all six cells and the 0,282
  total. The seventh cell is not part of either reading: the redundancy sum
  stops at $k = 6$ because the 8 kHz band has no band above it to pair with,
  so its 0,000 is the placeholder of a column with no redundancy partner, not
  a term. The alpha row above it, labelled the same way, is
  correct, because there the label and A.5.6 do agree.
- **Evidence:** both readings recomputed from the table's own step 4c MTI row
  and compared cell by cell with the printed row and with its printed total;
  A.5.6 read against the label. The defect does not move this example's
  answer, since $1{,}040 - 0{,}277 = 0{,}763$ and $1{,}040 - 0{,}282 =
  0{,}758$ both print as the STI 0,76 the table ends on, which is how a label
  contradicting the normative formula survives a worked example. Verified on
  PDF page 69 (printed p. 67) and PDF page 49 (printed p. 47) of
  IEC 60268-16:2011.
- **Library behaviour:** implements A.5.6 with the redundancy term as printed
  there, in
  [`_index_from_corrected_mtf`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sti.py); the pairwise
  weighting-factor test of A.2.2 pins it independently, and the conformance
  rows "IEC 60268-16:2020 A.2.2" and "IEC 60268-16 Annex M" both read the
  index it produces.
- **Status:** unreported.

## IEC 60268-16:2011, Table M.1 (I_k tabulated a million times its neighbours)

- **Location:** Annex M, Table M.1, the row "Combined squared sound pressure
  $I_k$, MPa$^2$" of step 2 (printed p. 64) and of step 3 (printed p. 65),
  read with the $I_{am,k}$ and $I_{rt,k}$ rows below it.
- **The print:** for the 77,9 dB signal of the 125 Hz band, step 2 prints
  $I_k$ = 61,7, and four rows below it prints $I_{rt,k}$ = 40 000 for the
  46 dB reception threshold of the same band.
- **The problem:** two defects in one row. The unit is impossible: at 77,9 dB
  re 20 µPa the squared sound pressure is $0{,}0247\ \text{Pa}^2$, so the cell
  cannot be 61,7 MPa$^2$ under any reading of the prefix. What the row
  actually tabulates is the dimensionless intensity ratio
  $10^{L/10} = 61\,722\,596$ divided by $10^{6}$. And that divisor is not
  applied to the two quantities the standard adds to $I_k$ in the very next
  rows: $I_{am,k}$ and $I_{rt,k}$ are tabulated as the plain ratio, 40 000
  being $10^{4,6} = 39\,811$ rounded, undivided. A reader who forms
  $I_k + I_{am,k} + I_{rt,k}$ from the cells as printed understates its first
  term by $10^{6}$. The printed "adjustment to remove masking and
  threshold" row is the check: 1,019 at 500 Hz is
  $(I_k + I_{am,k} + I_{rt,k})/I_k$ only once $I_k$ is restored to
  26 305 192; formed from the cells as printed the same expression reads
  19 279.
- **Evidence:** every cell of both $I_k$ rows recomputed as $10^{L/10}$ from
  the combined levels printed above them, and every cell of the $I_{am,k}$ and
  $I_{rt,k}$ rows recomputed as $amf_k \times I_{k-1}$ and $10^{ART_k/10}$;
  the first set reproduces at $10^{-6}$ of the computed value and the second
  two at $10^{0}$. Verified on PDF page 66 (printed p. 64) and PDF page 67
  (printed p. 65) of IEC 60268-16:2011.
- **Library behaviour:** carries all three quantities on one scale, the plain
  ratio to $p_0^2 = (20\ \mu\text{Pa})^2$, in the correction of
  [`sti.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sti.py); the transcription in
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data) keeps the printed cells
  verbatim and names the $10^{6}$ it rescales them by, and the conformance row
  "IEC 60268-16 Annex M" reads the adjustment they feed.
- **Status:** unreported.

## IEC 60268-16:2011, Table M.1 (step 3 I_am,k at 250 Hz)

- **Location:** Annex M, Table M.1, step 3, the $I_{am,k}$ row, 250 Hz column
  (printed p. 65).
- **The print:** 2 850 000, the same value as the 500 Hz cell beside it.
- **The problem:** the cell does not round from the quantity it names. With
  the operational levels printed two rows above, $I_{am,k}$ at 250 Hz is the
  auditory masking factor of the 125 Hz band times that band's combined
  intensity, $0{,}01463507 \times 195\,339\,273 = 2\,858\,804$, which at the
  three significant figures the row is printed to reads 2 860 000. The 500 Hz
  cell is correct: its 2 852 252 does print as 2 850 000. The two cells are
  reproduced together only by carrying the *rounded* $amf \times 1000 = 14{,}6$
  of the row above instead of the factor itself, and step 2 shows that is not
  what the table does, since its two corresponding cells are printed apart, as
  508 000 and 507 000, which only the unrounded factor gives.
- **Evidence:** both cells recomputed from the printed operational speech and
  noise levels, and the step 2 pair recomputed the same way as a control. The
  defect changes nothing downstream: the masking and threshold correction of
  the band is 0,985552 with the correct value against 0,985596 with the
  printed one, and the row prints 0,986 either way. Verified on PDF page 67
  (printed p. 65) and PDF page 66 (printed p. 64) of IEC 60268-16:2011.
- **Library behaviour:** computes $I_{am,k}$ from the unrounded masking factor.
  The transcription in [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data)
  keeps the printed cell and the test
  `test_annex_m_step3_masking_intensity_at_250_hz_is_the_printed_erratum`
  asserts the computed value against 2 858 804 and against the print, so the
  one cell of the table that is not an oracle cannot quietly become one.
- **Status:** unreported.

## UNE-EN 61043:1999, clause 6.1 (class 2 frequency range dropped in translation)

- **Location:** clause 6.1 "Rango de frecuencias", the class 2 sentence, of
  UNE-EN 61043 (April 1999), which declares itself "la versión oficial, en
  español, de la Norma Europea EN 61043 de enero 1994, que a su vez adopta la
  Norma Internacional CEI 61043:1993".
- **The print:** a single sentence, "Los procesadores de clase 2 deberán
  cubrir, al menos, el rango desde 45 Hz a 5,6 kHz en bandas de octava."
- **The problem:** the EN/IEC text gives class 2 processors two alternative
  ranges, not one: "Class 2 processors shall, at least, cover the range from
  45 Hz to 7,1 kHz in one-third octave bands, **or** the range from 45 Hz to
  5,6 kHz in one octave bands" (BS EN 61043:1994, clause 6.1). The translation
  drops the first alternative. The omission is normative rather than
  editorial: it removes one of the two ways clause 6.1 can be satisfied, and a
  reader of the Spanish text alone would conclude that class 2 is *defined*
  over octave bands, so that a one-third-octave chain verified over the 22
  tabulated bands from 50 Hz to $6{,}3\ \text{kHz}$ could not attest class 2
  over its full range.
- **Evidence:** side-by-side reading of clause 6.1 in both prints. The class 1
  sentence is word-for-word equivalent in the two documents, so the divergence
  is confined to the class 2 sentence. The Spanish print also contradicts
  itself: its Table 2 tabulates the pressure-residual intensity index for
  class 2 processors at all 22 one-third-octave centres, and its faithfully
  translated Note 2 ("Para procesadores con análisis en bandas de octavas
  únicamente, los requisitos se aplican únicamente a las frecuencias centrales
  de las bandas de octava") carves out octave-only processors as a special
  case. Both are redundant if every class 2 processor is an octave-band one.
- **Library behaviour:** implements the EN/IEC reading.
  [`verify_intensity_class`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/intensity_compliance.py)
  treats the full 22-band one-third-octave set as attesting either class, and
  the 7-band octave set (63 Hz to 4 kHz) as a class 2 alternative that never
  attests class 1, with both branches pinned by regression tests
  ([`tests/emission/test_intensity_compliance.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_intensity_compliance.py)).
- **Status:** unreported (national translation, not the issuing body's text).

## IEC 61183:1994, note to A.1.8 (two equal-area angles that break the list's own symmetry)

- **Location:** Annex A, the NOTE after the symbol list of Formulas (A.1) and
  (A.2), under A.1.8 (printed folio 10), which lists the directions of a
  division of the sphere into 38 elements of equal area.
- **The print:** "The angles of incidence will be 0°, 32,6°, 50,8°, 65,1°,
  **77,9°**, 90°, 102,2°, 114,9°, 129,2°, 147,4°, 180°, 212,6°, 230,8°,
  245,1°, 257,8°, 270°, **282,1°**, 294,9°, 309,2°, 327,4° in the horizontal
  plane and the same angles with the exception of 0° and 180° in the vertical
  plane."
- **The problem:** the division is symmetric about the grazing direction: the
  note places a single element on each pole and one at 90°, and 38 equal
  elements with a cap at each pole leave nine rings of four elements each,
  mirror images of one another about 90°. Every pair of the printed list obeys
  that symmetry except one: $32{,}6 + 147{,}4$, $50{,}8 + 129{,}2$ and
  $65{,}1 + 114{,}9$ are all $180{,}0°$, while $77{,}9 + 102{,}2 = 180{,}1°$.
  The same slip appears on the second half of the circle, where $257{,}8°$ is
  $180° + 77{,}8°$ but $282{,}1°$ is $360° - 77{,}9°$. The direction that
  halves each element's area in polar angle, $\phi_k = \arccos[1 - (4k -
  1)/19]$, reproduces all the other printed angles to their 0,1° and gives
  $77{,}846°$ and $282{,}154°$ for the fourth ring, which read **77,8°** and
  **282,2°**.
- **Evidence:** the construction evaluated for the nine rings and compared
  with the twenty printed angles. Verified on PDF page 14 (printed p. 10) of
  BS EN 61183:1995, the English text of EN 61183:1994, which is IEC 1183:1994
  (now IEC 61183:1994) unchanged.
- **Library behaviour:** `metrology.equal_area_incidence_angles` computes the
  directions from the construction instead of transcribing them, and the
  conformance row on the note checks the other eighteen printed angles; the
  tests pin the two corrected values
  ([`tests/metrology/test_random_incidence.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_random_incidence.py)).
  Formula (A.5) weighs every reading by 1/38 whatever its direction, so a
  directivity factor is not affected by the slip; only where the source is
  placed is.
- **Status:** unreported.

## UNE-EN ISO 9614-1:2010, clause 9.1 (the sign dropped from "signed magnitude" in translation)

- **Location:** clause 9.1, the symbol list under Formula (11)
  $P_i = I_{\mathrm{n}i} \cdot S_i$, of UNE-EN ISO 9614-1 (March 2010), which
  declares itself "la versión en español de la Norma Europea EN ISO
  9614-1:2009", the European adoption of ISO 9614-1:1993.
- **The print:** "$I_{\mathrm{n}i}$ es el **módulo** de la componente de la
  intensidad acústica normal medida en la posición $i$ sobre la superficie de
  medida". The ISO original reads "$I_{\mathrm{n}i}$ is the **signed
  magnitude** of the normal sound intensity component measured at position $i$
  on the measurement surface".
- **The problem:** *módulo* is the absolute value, so the qualifier that
  carried the sign is gone, and the sign is what the rest of the method turns
  on. The Spanish print then contradicts itself twice over. The same clause 9.1
  gives, two paragraphs below that line, the conversion to apply when the level
  of a position is written $(-)\,XX$ dB:
  $I_{\mathrm{n}i} = -I_0 \times 10^{XX/10}$, a negative $I_{\mathrm{n}i}$.
  Clause 3.6.1, which defines the very quantity Formula (11) computes, calls
  $I_{\mathrm{n}i}$ "la componente normal, **con su signo**, de la intensidad
  acústica medida en la posición $i$", and A.2.3 calls it "el **valor
  algebraico** de la componente de intensidad acústica normal". And clause 9.2
  makes $\sum_i P_i$ *being negative* the condition that puts a frequency band
  outside the method, which no sum of magnitudes and positive areas can ever
  be. Read as a magnitude the method loses the one thing measurement at
  discrete points is for: separating the energy leaving the source from the
  energy flowing back in through part of the surface, which is what $F_3$
  (Formulae (A.6) and (A.7)) and $F_4$ (Formulae (A.8) and (A.9)) are built to
  quantify from the algebraic mean of the same $I_{\mathrm{n}i}$.
- **Evidence:** the two prints of the same symbol list, set side by side, and
  the three Spanish clauses read against one another. PDF pages 10, 18 and 22
  (printed pp. 10, 18 and 22) of UNE-EN ISO 9614-1:2010; PDF page 12 (printed
  p. 7) of ISO 9614-1:1993, where the qualifier is present.
- **Library behaviour:** implements the signed reading throughout, which is the
  ISO text.
  [`sound_power_intensity_points`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  sums signed partial powers, flags the bands whose sum is not positive as
  outside the method, and reports $F_3 - F_2$ as the excess the inward flow
  produces; `normal_intensity_from_levels` carries the $(-)$ of the print as a
  separate argument, because the printed level never holds it. Pinned by
  `test_a_genuinely_negative_partial_power_is_kept_and_summed` and the signed
  conversion tests in
  [`tests/emission/test_sound_power_intensity_points.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_intensity_points.py).
- **Status:** unreported (national translation, not the issuing body's text: a
  reader working from the ISO edition has nothing to work around).

## UNE-EN ISO 9614-1:2010, clause A.2.3 (modulus bars on the algebraic intensity level)

- **Location:** Annex A, clause A.2.3, the "donde" list under Formula (A.6)
  $F_3 = \overline{L_p} - \overline{L_{I_\mathrm{n}}}$.
- **The print:** the second entry of the list is typeset
  $\overline{L_{|I_\mathrm{n}|}}$, with the absolute-value bars, and reads "es
  el valor algebraico del nivel de intensidad acústica superficial, en
  decibelios, calculado a partir de la ecuación (A.7)". Formula (A.7), three
  lines below on the same page, is labelled $\overline{L_{I_\mathrm{n}}}$,
  without the bars.
- **The problem:** the barred symbol is A.2.2's, the level of the mean
  *magnitude* of Formula (A.5), which is exactly what $F_2$ subtracts. With the
  bars, $F_3$ and $F_2$ would be the same indicator and the whole of A.2.3
  would be redundant; the sentence beside the symbol says "valor algebraico"
  and points at (A.7), which takes the algebraic mean. The ISO original prints
  the same entry without the bars and describes it as "the surface normal
  signed intensity level", so the bars are the translation's own typesetting.
- **Evidence:** the symbol as set in the two editions, and the barless (A.7) on
  the same page as the barred entry. PDF page 22 (printed p. 22) of UNE-EN ISO
  9614-1:2010; PDF page 15 (printed p. 10) of ISO 9614-1:1993.
- **Library behaviour:** none required. `field_indicators` in
  [`intensity.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/intensity.py) forms $F_3$ from
  the algebraic mean of Formula (A.7) and $F_2$ from the mean magnitude of
  Formula (A.5), which is what makes $F_3 - F_2$ the inward-flow excess the
  Annex B gate is written on. Registered as a label defect.
- **Status:** unreported (national translation, not the issuing body's text).

## ISO 9614-1:1993, clause B.1.3 ($F_4$ cross-referenced to A.2.3, which defines $F_3$)

- **Location:** Annex B, clause B.1.3, the sentence introducing the two
  separate evaluations of $F_4$ that Formula (B.4) consumes.
- **The print:** "Calculate indicator $F_4$ separately according to **A.2.3**",
  over the two items "a) for the segment subset $N_\alpha$ having total area
  $S_\alpha$, and" and "b) for the remaining segments". The Spanish edition
  renders the same clause number: "Calcular el indicador $F_4$ separadamente
  de acuerdo al apartado A.2.3 para: a) el subconjunto de segmentos $N_\alpha$
  con área total $S_\alpha$, y b) los segmentos restantes."
- **The problem:** A.2.3 is "Negative partial power indicator", which defines
  $F_3$ by Formulae (A.6) and (A.7). $F_4$ is A.2.4, "Field non-uniformity
  indicator", Formulae (A.8) and (A.9). Followed as printed, the reference
  computes the wrong indicator for $F_4(\alpha)$ and $F_4(1-\alpha)$, and those
  are what size the new positions in Formula (B.4). Both editions carry the
  same clause numbering, so the defect is the issuing body's.
- **Evidence:** the reference and the headings of A.2.3 and A.2.4 read against
  each other. PDF pages 18 and 15 to 16 (printed pp. 13 and 10 to 11) of ISO
  9614-1:1993; the same sentence at PDF page 24 (printed p. 24) of UNE-EN ISO
  9614-1:2010.
- **Library behaviour:** follows the intended target. $F_4(\alpha)$ and
  $F_4(1-\alpha)$ are computed per A.2.4 in
  [`partial_power_concentration`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py).
  The reference changes no number the library reports, so no other change was
  needed.
- **Status:** unreported (cross-reference defect, no numerical consequence).

## UNE-EN ISO 9614-1:2010, clause 10.5 c) (an equation number replaced by a chapter that is not there)

- **Location:** clause 10.5 c), "Datos acústicos", the reporting requirement
  that accompanies the level of a band which does not satisfy criterion 2.
- **The print:** "Una referencia a la incertidumbre prevista en el nivel de
  potencia acústica determinada para cada banda de frecuencia en la que no se
  satisfaga el criterio 2 del anexo B, **de acuerdo a la ecuación (véase el
  capítulo B.3)**." The ISO original reads "A statement of the predicted
  uncertainty in the sound power level determined for each frequency band, in
  which criterion 2 of annex B is not satisfied, **according to equation
  (B.3)**."
- **The problem:** the number that identified the equation has been moved into
  a cross-reference and changed on the way. "De acuerdo a la ecuación ( )"
  names no equation, and what the parenthesis names instead is not part of the
  document: Annex B divides into B.1, with B.1.1 to B.1.5, and B.2, and stops
  there, so there is no chapter B.3 to look up. The requirement is unusable as
  printed unless the reader recognises Formula (B.3), the 95 % confidence
  interval $10 \lg (1 \pm 2 F_4 / \sqrt{N})$, which clause B.1.2 introduces
  with this very condition attached to it.
- **Evidence:** the two prints of the same item, and the divisions of Annex B
  as its headings run. PDF pages 20 and 23 to 26 (printed pp. 20 and 23 to 26)
  of UNE-EN ISO 9614-1:2010; PDF page 14 (printed p. 9) of ISO 9614-1:1993,
  where the equation number is present.
- **Library behaviour:** reports the interval of Formula (B.3) for every band,
  so the statement clause 10.5 c) asks for can be made about any band that
  needs it. `confidence_interval` on
  [`DiscretePointIntensityResult`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  carries the pair, and `criterion_2` says which bands the requirement applies
  to. The defect changes no number, only where a reader is sent to find the
  formula.
- **Status:** unreported (national translation, not the issuing body's text).

## ISO 9614-1:1993, Table B.3 (actions c and d both claim $F_3 - F_2 = 1$ dB)

- **Location:** Table B.3, "Actions to be taken to increase grade of accuracy
  of determination", the criterion cells of the action-c and action-d rows.
- **The print:** action c is conditioned on "Criterion 2 not satisfied and
  1 dB $\leq (F_3 - F_2) \leq$ 3 dB"; action d on "Criterion 2 not satisfied
  and $(F_3 - F_2) \leq$ 1 dB, and the procedure of 8.3.2 either fails or is
  not selected". Both inequalities are printed non-strict, in both editions.
- **The problem:** the two rows overlap at exactly $F_3 - F_2 = 1$ dB, where
  the table prescribes two different actions for one state: increase the
  density of positions uniformly (c), or move the surface out and keep the
  positions (d). A normative decision table is not implementable while that
  holds. The document settles it elsewhere: Figure B.1's fifth decision diamond
  is "$(F_3 - F_2) \leq$ 1 dB ?", and its **Yes** branch is the one that leads
  to the optional procedure and to action d, so 1 dB belongs to d and c begins
  above it. Clause 8.3.2 agrees, opening the optional procedure "if
  $F_3 - F_2 \leq$ 1 dB".
- **Evidence:** the two criterion cells, the diamond and its branches, and the
  clause 8.3.2 condition. PDF pages 19, 20 and 12 (printed pp. 14, 15 and 7) of
  ISO 9614-1:1993; the same three places at PDF pages 26, 27 and 17 (printed
  pp. 26, 27 and 17) of UNE-EN ISO 9614-1:2010.
- **Library behaviour:** follows Figure B.1 and clause 8.3.2. `required_actions`
  on
  [`DiscretePointIntensityResult`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  answers a band that fails criterion 2 with action c above 1 dB and action d
  at 1 dB and below, pinned at the boundary itself by
  `test_action_d_is_the_action_at_exactly_one_decibel` in
  [`tests/emission/test_sound_power_intensity_points.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_intensity_points.py).
- **Status:** unreported.

## ISO 9614-1:1993, equations (A.1) and (A.8) (the normalizing intensity without its overbar)

- **Location:** Annex A, clause A.2.1, equation (A.1) for the temporal
  variability indicator $F_1$, and clause A.2.4, equation (A.8) for the field
  non-uniformity indicator $F_4$.
- **The print:** both equations open with the factor $1/I_\mathrm{n}$, an
  unbarred symbol, while the deviation inside the sum is written against a
  clearly overbarred $\overline{I_\mathrm{n}}$:
  $F_1 = \frac{1}{I_\mathrm{n}} \sqrt{\frac{1}{M-1}\sum_k (I_{\mathrm{n}k} -
  \overline{I_\mathrm{n}})^2}$ and
  $F_4 = \frac{1}{I_\mathrm{n}} \sqrt{\frac{1}{N-1}\sum_i (I_{\mathrm{n}i} -
  \overline{I_\mathrm{n}})^2}$. Both editions set them the same way.
- **The problem:** the symbol lists that follow define only the overbarred one
  ("$\overline{I_\mathrm{n}}$ is the mean value of $I_\mathrm{n}$ for $M$
  short-time-average samples", A.2.1; "$\overline{I_\mathrm{n}}$ is the surface
  normal sound intensity calculated from equation (A.9)", A.2.4). The unbarred
  $I_\mathrm{n}$ is clause 3.4's normal intensity at a point, so as printed a
  coefficient of variation is divided by an unspecified single value rather
  than by the mean its own numerator is taken about. Both indicators are
  coefficients of variation and admit no other normalization.
- **Evidence:** the two equations and the symbol lists beneath them, where the
  bar is absent above the divisor and unbroken above the symbol inside the sum.
  PDF pages 15 and 16 (printed pp. 10 and 11) of ISO 9614-1:1993; the same two
  equations at PDF pages 21 and 22 (printed pp. 21 and 22) of UNE-EN ISO
  9614-1:2010.
- **Library behaviour:** none required. The coefficient of variation behind
  `field_indicators` and `temporal_variability_indicator` in
  [`intensity.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/intensity.py) divides by the
  algebraic mean, and refuses a mean that is not positive rather than dividing
  by it. Registered as a typographic defect.
- **Status:** unreported (typographic).

## UNE-EN ISO 9614-1:2010, Note 11 to clause B.1.3 (half a level, and a recommendation made a requirement)

- **Location:** Note 11, immediately after the Formula (B.4) block of clause
  B.1.3, which qualifies the choice of the Table B.2 factor $C$ for an
  A-weighted determination.
- **The print:** "Si la contribución total al **nivel de** potencia acústica
  ponderado A de las bandas de tercio de octava en el margen de frecuencias de
  800 Hz a 5 000 Hz es menos de la mitad del **nivel total**, entonces **deben**
  usarse los valores de $C$ para las bandas de tercio de octava de 200 Hz a
  630 Hz." The ISO original reads "If the total contribution to the A-weighted
  sound **power** from the one-third-octave bands in the frequency range 800 Hz
  to 5 000 Hz is less than half the total **power**, then the values of $C$ for
  the one-third-octave band 200 Hz to 630 Hz **should** be used."
- **The problem:** two departures in one sentence. Half of a *level* is not a
  defined operation, so the Spanish print states a condition that cannot be
  evaluated as written; the original conditions on half the *power*, which is a
  contribution 3 dB or more below the total and is decidable. And *should*, a
  recommendation under the ISO/IEC drafting rules, becomes *deben*, which reads
  as a requirement, so the two prints do not even agree on whether the
  substitution is optional.
- **Evidence:** the two prints of the same note. PDF page 25 (printed p. 25) of
  UNE-EN ISO 9614-1:2010; PDF page 18 (printed p. 13) of ISO 9614-1:1993.
- **Library behaviour:** implements the power reading, and applies the
  substitution whenever the condition holds rather than leaving it to the
  caller, which satisfies both prints. `_a_weighted_factor` in
  [`sound_power_intensity_points.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  compares the summed A-weighted contribution of the 800 Hz to 5 kHz bands with
  half the total contribution and reads the 200 Hz to 630 Hz row of Table B.2
  when it falls short.
- **Status:** unreported (national translation, not the issuing body's text).

## ISO 3744:2010, 8.3.4, Equation (21) (a time-integrated level compared with a time-averaged one)

- **Location:** clause 8.3.4, Equation (21) and the symbol list beneath it
  (PDF page 31, printed p. 25) of ISO 3744:2010, read against the definitions
  of clauses 3.3 and 3.4 (PDF page 9, printed p. 3). The same construction is
  printed as ISO 3741:2010 Equation (25) (PDF page 33, printed p. 24, with its
  symbol list on PDF page 34, printed p. 25) as ISO 3747:2010 Equation
  (14) (PDF pages 22 and 23, printed pp. 13 and 14), and as ISO 3746:2010
  Equation (15) in clause 8.4.2 (PDF page 25, printed p. 16), which is the
  survey-grade route the library takes for `grade='survey'`.
- **The print:** $K_1 = -10 \lg\left(1 - 10^{-0{,}1\,\Delta L_E}\right)$ dB
  with $\Delta L_E = \overline{L'_{E(\mathrm{ST})}} - \overline{L_{p(\mathrm{B})}}$,
  where $\overline{L'_{E(\mathrm{ST})}}$ "is the mean frequency-band or
  A-weighted single event time-integrated sound pressure level" and
  $\overline{L_{p(\mathrm{B})}}$ "is the mean frequency-band or A-weighted
  time-averaged sound pressure level of the background noise", followed by
  "The integration time $T = t_2 - t_1$ and other measurement parameters shall
  be the same for the measurement of the single event time-integrated sound
  pressure level $L'_{Ei(\mathrm{ST})}$ and of the background noise level
  $L_{pi(\mathrm{B})}$."
- **The problem:** the two levels do not share a reference quantity, and the
  correction subtracts one energy from another. By clause 3.4, $L_E$ is
  $\int_{t_1}^{t_2} p^2\,\mathrm{d}t$ re $E_0 = (20\ \mu\text{Pa})^2\,\text{s}$;
  by clause 3.3, $L_{p,T}$ is $\frac{1}{T}\int_{t_1}^{t_2} p^2\,\mathrm{d}t$
  re $p_0^2$. Their difference is a ratio of energies only when $T = 1$ s. Over
  the common interval $T$ the background contributes the energy
  $L_{p(\mathrm{B})} + 10 \lg(T/T_0)$ (the identity of clause 3.4 NOTE 1), so
  the printed $\Delta L_E$ exceeds the signal-to-background energy ratio by
  $10 \lg(T/T_0)$ and $K_1$ is under-estimated for every $T > 1$ s: a burst
  whose energy is 6 dB above the background's in a 10 s interval reads as
  16 dB above it and earns no correction, where the criterion of 8.2.3 puts
  $K_1$ at its largest admissible value, 1,3 dB. The twin chain of 8.2, where
  both levels are time-averaged, has no such term, and 8.3.3 requires the
  single event levels to be averaged "in the same way as for the
  time-averaged sound pressure levels described in 8.2.2", so the intended
  reading is the one under which the two chains coincide for a source that is
  steady over $T$, $L_J = L_W + 10 \lg(T/T_0)$, and that is the reading under
  which the insistence on one integration time for both measurements does any
  work.
- **Evidence:** Verified on PDF page 31 (printed p. 25) of ISO 3744:2010 for
  the equation and its symbol list, and on PDF page 9 (printed p. 3) for the
  definitions of clauses 3.3 and 3.4 with NOTE 1; the same construction read
  on PDF pages 33 and 34 (printed pp. 24 and 25) of BS EN ISO 3741:2010 and on
  PDF pages 22 and 23 (printed pp. 13 and 14) of BS EN ISO 3747:2010.
- **Library behaviour:** `sound_energy_pressure`, `sound_energy_reverberation`
  and `sound_energy_comparison` compare the background as its exposure over
  the same interval, $L_{p(\mathrm{B})} + 10 \lg(T/T_0)$, and require
  `integration_time` with the background of the source under test, which is
  the one compared against an event level. The reference source of
  `sound_energy_comparison` is steady, so `background_levels_ref` is corrected
  by the time-averaged rule of 9.1.2 instead and takes no window; the criteria and the
  clamp of 8.2.3 (and of 9.1.2 in ISO 3741) are then applied to that margin.
  `tests/emission/test_sound_energy.py` pins $K_1 = 1{,}2563$ dB for a 78 dB
  burst over a 62 dB background in a 10 s window, and
  $L_J = L_W + 10 \lg(T/T_0)$ field by field on both families; the
  conformance report carries the identity as "ISO 3744:2010 Eq. 23 / clause
  3.4 NOTE 1".
- **Status:** unreported.

## ISO 3744:2010, 8.3.4 (the correction named K_1i in the text and K_1 in Equation (21))

- **Location:** clause 8.3.4, first sentence and Equation (21) (PDF page 31,
  printed p. 25).
- **The print:** "The background noise correction, $K_{1i}$, shall be
  calculated using Equation (21):" followed by
  $K_1 = -10 \lg\left(1 - 10^{-0{,}1\,\Delta L_E}\right)$ dB with $\Delta L_E$
  formed from the two means over the measurement surface,
  $\overline{L'_{E(\mathrm{ST})}}$ and $\overline{L_{p(\mathrm{B})}}$.
- **The problem:** the sentence names a per-position correction and the
  equation defines a single one from surface means. The twin clause 8.2.3
  names $K_1$ in both places and forms it from the same surface means
  (Equation (16)), and 8.3.5 subtracts the unsubscripted $K_1$ in Equation
  (22). The subscript is the per-microphone convention of ISO 3741:2010
  clauses 9.1.2 and 9.2.2 ($K_{1i}$, Equations (14) and (25)), where each
  position is corrected before the average, and does not belong to this
  clause.
- **Evidence:** Verified on PDF page 31 (printed p. 25) of ISO 3744:2010,
  against clause 8.2.3 on PDF page 29 (printed p. 23).
- **Library behaviour:** `sound_energy_pressure` forms one $K_1$ per band from
  the surface means, as Equation (21) prints it and as `sound_power_pressure`
  does for Equation (16); no per-position correction is applied in the
  ISO 3744 chain. No change was required.
- **Status:** unreported.

## ISO/PAS 1996-3:2022, Clause 5 (cross-references of r and d)

- **Location:** Clause 5, Formula (2), the definitions of the symbols of the
  prominence $P = 3\log_{10}[r/(\text{dB/s})] + 2\log_{10}(d/\text{dB})$.
- **The print:** "r is the onset rate (OR) as defined in 3.4" and "d is the
  level difference (LD) as defined in 3.5".
- **The problem:** the two cross-references are swapped. The document's own
  terms and definitions set 3.4 as the *level difference* LD ("difference in
  decibels of L_pAF between the level of the end point L_e and the level of
  the starting point L_s of the onset") and 3.5 as the *onset rate* OR ("slope
  in decibels per second of the straight line that gives the best
  approximation to the onset"). Read literally, Formula (2) would take three
  times the logarithm of a level difference plus twice the logarithm of a
  slope, inverting the weights the method assigns to the two quantities. The
  spelled-out names in the same list ("the onset rate (OR)", "the level
  difference (LD)") and the units given for each ("dB/s" for $r$, "dB" for
  $d$) make the intended reading unambiguous.
- **Evidence:** side-by-side reading of 3.4, 3.5 and the Clause 5 symbol list;
  the units printed with each symbol contradict the clause numbers printed
  with them.
- **Library behaviour:** implements the spelled-out reading, weighting the
  onset rate by 3 and the level difference by 2 (`predicted_prominence` in
  [`impulsive_sound.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/impulsive_sound.py)),
  which is also the NT ACOU 112:2002 form the PAS carries over.
- **Status:** unreported.

## ISO 13474:2009, Annex A.2 (the level of each class credited to Equations (7) and (8))

- **Location:** Annex A (informative), A.2, the paragraph above Table A.3
  that says how its levels were obtained.
- **The print:** "For each octave band, the sound exposure level at location
  A was calculated using Equations (7) and (8). From this, the A-weighted
  sound exposure level for each excess-attenuation class was determined."
- **The problem:** Equations (7) and (8) are the long-term average
  single-event sound exposure level and rating level,
  $10 \lg \left[\sum_{k}\sum_{l} \wp_{\mathrm{atm},k}\,\wp_{\mathrm{exc},l}\,10^{0{,}1 L_{E,\mathrm{w},k,l}}\right]$
  dB, with $K$ added in the exponent of Equation (8): one number summed over
  every class, from levels already weighted in frequency, with no octave band
  and no class left in it. The paragraph describes a band level for each
  excess-attenuation class and then the A-weighted level of each class drawn
  from it, which are Equation (4), $L_{E,k,l}(j)$, and Equation (5). The
  annex itself uses Equation (7) one step later, for LT1, a single value
  printed on Figure A.3 that it says was "calculated using Equation (7)". The
  cross-reference should read Equations (4) and (5).
- **Evidence:** the paragraph read on PDF page 39 (printed p. 31), Equation
  (4) on PDF page 15 (printed p. 7), Equation (5) on PDF page 16 (printed
  p. 8), Equations (7) and (8) on PDF page 17 (printed p. 9) and the LT1
  sentence on PDF page 42 (printed p. 34), all of BS ISO 13474:2009, the UK
  implementation of ISO 13474:2009 (first edition, 2009-06-15).
- **Library behaviour:** the levels of Table A.3 are taken as printed;
  `frequency_weighted_sel` evaluates Equation (5) and `long_term_sel`
  Equations (7) and (8)
  ([`exposure_distribution.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/exposure_distribution.py)),
  each under the equation its clause gives it. No change was required.
- **Status:** unreported.

## ISO 13474:2009, Annex A.2 (the shift of Equation (22) printed as 1,04 dB)

- **Location:** Annex A (informative), A.2, the paragraph below Figure A.1 that
  spreads the class density for turbulence.
- **The print:** the paragraph opens with "a normal distribution having a
  standard deviation equal to 5 dB" and continues "In this example, the mean
  value was shifted by an amount, Δμ, equal to 1,04 dB [from Equation (22)]";
  Figure A.3 repeats $\sigma = 5{,}0$ dB.
- **The problem:** Equation (22) is the mean of a lognormal variable and
  evaluates to $\Delta\mu = \sigma^2 \ln 10 / 20$, which is $2{,}878$ dB at
  $\sigma = 5$ dB. $1{,}04$ dB is its value at $\sigma = 3$ dB ($1{,}036$ dB),
  a standard deviation the annex does not use. The rest of the annex was
  computed with $2{,}878$ dB. The shift keeps the energetic mean of every
  subclass at its centre, which is why the printed LT2 of 37,0 dB agrees with
  the printed LT1 of 37,0 dB; with $\Delta\mu = 1{,}04$ dB and $\sigma = 5$ dB
  every level of the spread distribution moves up by $1{,}84$ dB, LT2 reads
  38,8 dB, the peak of Figure A.2 moves from about 30,5 dB to 32,3 dB, and
  $L_{50}$ reads 33,3 dB against the printed 31,5 dB.
- **Evidence:** the paragraph read on PDF page 42 (printed p. 34), Equation
  (22) on PDF page 21 (printed p. 13), Figures A.2 and A.3 on PDF pages 43
  and 44 (printed pp. 35 and 36), all of BS ISO 13474:2009, the UK
  implementation of ISO 13474:2009 (first edition, 2009-06-15). Every value
  was recomputed from Table A.3 on PDF page 40 (printed p. 32) of the same
  document.
- **Library behaviour:** the shift is Equation (22) in closed form,
  [`turbulence_level_shift`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/exposure_distribution.py),
  $2{,}878$ dB at 5 dB, and it is not a parameter a caller can set. The
  conformance check "ISO 13474:2009 Equation (22)" holds it against the
  printed integral evaluated by quadrature, and "ISO 13474:2009 Equation
  (A.4), Figure A.3" holds LT2 at the printed 37,0 dB.
- **Status:** unreported.

## ISO 13474:2009, Annex A.2, Figure A.3 (exceedance levels that are not the roots of Equation (25))

- **Location:** Annex A (informative), Figure A.3, the exceedance levels
  printed beside the cumulative curve.
- **The print:** $L_{95} = 21{,}7$ dB, $L_{50} = 31{,}5$ dB,
  $L_{10} = 40{,}6$ dB, $L_{5} = 43{,}2$ dB and $L_{1} = 48{,}0$ dB, beside
  $\sigma = 5{,}0$ dB.
- **The problem:** Equation (24) defines the probability that the level
  exceeds $x$ as $\int_x^{\infty} \rho^{*}(x')\,\mathrm{d}x'$ and Equation (25)
  the $n$-percent exceedance level as its root. On the distribution of Table
  A.4 spread as A.2 describes, they give 21,6; 31,5; 40,5; 43,0 and 47,5 dB:
  $L_{50}$ agrees and the other four print 0,1 dB to 0,5 dB higher, the more
  so the rarer the level. The annex does not say how it computed them. One
  reading is consistent with the print: a cumulative curve formed from 15 dB,
  where the drawn curves of Figures A.2 and A.3 begin (their axes start at
  10 dB), rather than from minus infinity,
  $1 - \int_{15}^{x} \rho^{*}(x')\,\mathrm{d}x'$; the drawn curve of Figure
  A.3 begins at 15 dB on the line of 1, which is what that reading draws and
  where Equation (24) gives 0,998. Fed the 07:00 to 19:00
  column of Table A.3 as printed, which sums to 1,0004, it gives 21,69;
  31,49; 40,58; 43,16 and 47,97 dB, all five to the printed digit; it then
  adds about 0,17 % to every exceedance, the 0,21 % of the distribution below
  15 dB less the 0,04 % by which the printed column exceeds one, which moves
  the levels at the smallest percentages most. Fed the full-precision
  probabilities that reproduce Table A.4, the same reading gives 21,69;
  31,49; 40,59; 43,17 and 48,05 dB, and $L_{1}$ would print 48,1 dB. The
  reading is therefore a hypothesis and not a reconstruction of the figure;
  what is established is that four of the five printed levels are not the
  roots of Equation (25).
- **Evidence:** Figure A.3 on PDF page 44 (printed p. 36), Figure A.2 on PDF
  page 43 (printed p. 35) and Equations (24) and (25) on PDF page 21 (printed
  p. 13), all of BS ISO 13474:2009, the UK implementation of ISO 13474:2009
  (first edition, 2009-06-15). The levels were recomputed from Table A.3 on
  PDF page 40 (printed p. 32) of the same document.
- **Library behaviour:** `SelDistribution.exceedance` evaluates Equation (24)
  to infinity in closed form and `SelDistribution.exceedance_level` solves
  Equation (25)
  ([`exposure_distribution.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/exposure_distribution.py)),
  so the example returns 21,6; 31,5; 40,5; 43,0 and 47,5 dB. The conformance
  check "ISO 13474:2009 Equation (25), Figure A.3" holds $L_{50}$ at the
  printed 31,5 dB; the other four printed levels have no conformance check.
- **Status:** unreported.

## ISO/TS 12913-3:2019, Annex A.3 (the perceived affective quality called part 3)

- **Location:** Annex A (informative), A.3, the paragraph that introduces
  Formulas (A.1) and (A.2).
- **The print:** "The results from part 3 (see A.1) are further processed to
  derive the values on two dimensions (pleasantness and eventfulness) for each
  site."
- **The problem:** the eight attributes the two formulas read (annoying, calm,
  chaotic, eventful, monotonous, pleasant, uneventful, vibrant) are the
  perceived affective quality, which is part 2 of the Method A questionnaire
  everywhere else the documents name it: in Table A.1 on the page before
  ("2 (perceived affective quality)"), in the A.2 paragraph that assigns its
  scale values 5 to 1 ("questionnaire part 2 (see Figure C.4 ...)"), in the
  title of A.3 itself ("based on perceived affective quality responses"), and
  in ISO/TS 12913-2:2018, C.3.1.3 and Figure C.4, "Questionnaire part 2:
  Perceived affective quality". Part 3 is the single overall rating of
  Figure C.5, "Overall, how would you describe the present surrounding sound
  environment?", which has no attributes and cannot feed either formula. The
  cross-reference "(see A.1)" does not help: A.1 is the general clause and
  names no part. The sentence should read "part 2 (see A.2 and Table A.1)".
- **Evidence:** the sentence on PDF page 11 (printed p. 5), Table A.1 and the
  A.2 paragraphs on PDF page 10 (printed p. 4), both of ISO/TS 12913-3:2019
  (first edition, 2019-12); C.3.1.3 on PDF page 21 (printed p. 15) and
  Figures C.4 and C.5 on PDF page 22 (printed p. 16) of ISO/TS 12913-2:2018
  (first edition).
- **Library behaviour:** `pleasantness_eventfulness` applies Formulas (A.1)
  and (A.2) to the eight attributes of part 2, the only reading under which
  they can be evaluated
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No change was required. The 2025 edition of ISO/TS 12913-3 revises Annex A
  and has not been checked for this entry.
- **Status:** unreported.

## ISO/TS 12913-3:2019, Formula (A.3) (a stray factor 1)

- **Location:** Annex A (informative), A.4, Formula (A.3), Spearman's rank
  correlation coefficient for untied ranks.
- **The print:**
  $r_\mathrm{spearman} = 1 - 1\,\dfrac{6\cdot\sum_{i=1}^{n} d_i^2}{n\cdot(n^2 - 1)}$,
  with a "1" standing between the minus sign and the fraction.
- **The problem:** the coefficient for untied ranks is
  $1 - 6\sum d_i^2 / \left[n(n^2 - 1)\right]$, which is what the page gives if
  the stray "1" is read as a factor of one. Read the way a mixed number is
  written, $1\,\tfrac{a}{b} = 1 + \tfrac{a}{b}$, it would give
  $r = -6\sum d_i^2 / \left[n(n^2 - 1)\right]$, which is zero for identical
  rankings instead of one. Formula (A.4) on the same page reduces to the
  usual coefficient when there are no ties, so the intended form is not in
  doubt; the "1" is a typesetting remnant.
- **Evidence:** Formula (A.3) on PDF page 12 (printed p. 6) of
  ISO/TS 12913-3:2019 (first edition, 2019-12).
- **Library behaviour:** `spearman_rank_correlation` evaluates
  $1 - 6\sum d_i^2 / \left[n(n^2 - 1)\right]$ without ties and Formula (A.4)
  with them; the conformance rows hold the first to Pearson's coefficient of
  the ranks and the second to `scipy.stats.spearmanr`
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No change was required.
- **Status:** unreported.

## ISO/TS 12913-3:2019, Formula (A.4) (the where-list of the tie counts)

- **Location:** Annex A (informative), A.4, the where-list under Formula
  (A.4), Spearman's rank correlation coefficient for tied ranks.
- **The print:** "$t_j$ is the number of in $t_j$ tied ranks of the variable
  $x$; $u_j$ is the number of in $u_j$ tied ranks of the variable $y$;
  $k(x)$ and $k(y)$ are the numbers of tied ranks of the variables $x$ and
  $y$", under
  $T = \sum_{j=1}^{k(x)} (t_j^3 - t_j)/12$ and
  $U = \sum_{j=1}^{k(y)} (u_j^3 - u_j)/12$.
- **The problem:** the first two definitions are not sentences ("the number
  of in $t_j$ tied ranks") and define $t_j$ by itself. The sums need $t_j$
  to be the number of values sharing the $j$-th tied rank of $x$ ($u_j$ the
  same for $y$), and $k(x)$, $k(y)$ to be the number of such groups of ties
  in each variable, which "the numbers of tied ranks" does not say. The
  intended reading is the usual tie correction of Spearman's coefficient,
  which is what makes (A.4) Pearson's coefficient of the average ranks.
- **Evidence:** the where-list on PDF page 13 (printed p. 7), under Formula
  (A.4) on PDF page 12 (printed p. 6), of ISO/TS 12913-3:2019 (first
  edition, 2019-12).
- **Library behaviour:** `spearman_rank_correlation` sums
  $(t_j^3 - t_j)/12$ over the groups of equal values of each variable, and a
  conformance row holds Formula (A.4) so read to `scipy.stats.spearmanr` on
  93 real answers with heavy ties
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No change was required.
- **Status:** unreported.

## ISO/TS 12913-3:2019, Formula (B.2) ($x_I$ for $x_i$)

- **Location:** Annex B (informative), B.3, the where-list under Formula
  (B.2), the covariance of Pearson's correlation coefficient.
- **The print:** "$\bar{x}$ is the arithmetic mean value of the array $x_I$;"
  with a capital $I$, followed by "$\bar{y}$ is the arithmetic mean value of
  the array $y_i$;".
- **The problem:** the index is the lower-case $i$ of the sum in (B.2),
  $\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})/n$, and of the line for
  $\bar{y}$ just under it; $x_I$ names no array of the annex.
- **Evidence:** the where-list on PDF page 15 (printed p. 9) of
  ISO/TS 12913-3:2019 (first edition, 2019-12).
- **Library behaviour:** `pearson_correlation` takes $\bar{x}$ as the mean of
  the $x_i$ ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No change was required.
- **Status:** unreported.

## ISO/TS 12913-2:2018, A.3 f), NOTE (exponent 3 for a cube root)

- **Location:** Annex A (normative), A.3 f), the NOTE on the root mean cubed
  loudness $N_\mathrm{rmc}$.
- **The print:** "The root mean cubed loudness (cubic mean), Nrmc, is
  computed by determining the mean of all loudness values raised to the power
  of 3 with a subsequent application of the exponent 3 as shown in the
  following formula:
  $N_\mathrm{rmc} = \sqrt[3]{\frac{1}{n}\sum_{i=1}^{n} N_i^3}$".
- **The problem:** the text and the formula under it disagree. The formula
  takes the cube root of the mean of the cubes, a subsequent exponent of
  $1/3$, which is what a cubic mean is and what returns a loudness in sone;
  the text says the subsequent exponent is 3, which would give the mean cube
  raised to the third power, $\left(\frac{1}{n}\sum N_i^3\right)^3$, in
  sone to the ninth. The sentence should read "a subsequent application of
  the exponent 1/3". ISO 532-1:2017, 6.4, NOTE, describes the energy mean of
  the loudness level in the same shape and gets it right: a power of about
  3,322 and then a power law "with the exponent lg(2)", its inverse.
- **Evidence:** the NOTE and its formula on PDF page 14 (printed p. 8) of
  ISO/TS 12913-2:2018 (first edition, 2018-08); ISO 532-1:2017, 6.4, on PDF
  page 22 (printed p. 16).
- **Library behaviour:** `binaural_indicators` computes $N_\mathrm{rmc}$ of
  each ear by the formula, the cube root of the mean of the cubes of the
  loudness over time, and a conformance row holds it to that formula
  ([`soundscape_binaural.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape_binaural.py)).
  No change was required.
- **Status:** unreported.

## ISO/TS 12913-2:2018, C.3.2.3 against Figure C.7 (three scales in the text, four in the figure)

- **Location:** Annex C (informative), C.3.2.3, "Soundwalk data collection
  part 1: Assessment of the sound environment", and Figure C.7 below it.
- **The print:** the text reads "The participants should assess a site on
  three different five-point unipolar continuous-category scales with
  additional verbal labelling ranging from "not at all" to "extremely"." The
  figure prints four scales: "How loud is it here?", "How unpleasant is it
  here?" and "How appropriate is the sound to the surrounding?", labelled from
  "not at all" to "extremely", and "How often would you like to visit this
  place again?", labelled "never", "rarely", "sometimes", "often",
  "very often".
- **The problem:** the text and the figure it introduces disagree on the
  number of scales and on their labels. Either the fourth scale belongs to
  Method B, and the text should say four and name its second set of labels,
  or it does not, and the figure should not print it. ISO/TS 12913-3:2019 B.2
  and Table B.1 speak of "the five-point unipolar continuous-category scales"
  without a number and do not settle it.
- **Evidence:** C.3.2.3 and Figure C.7 on PDF page 24 (printed p. 18) of
  ISO/TS 12913-2:2018 (first edition); B.2 and Table B.1 on PDF page 14
  (printed p. 8) of ISO/TS 12913-3:2019.
- **Library behaviour:** `METHOD_B_SCALES` holds the four scales of the
  figure, as printed, and `method_b_summary` takes a table of three or four
  of them, so a study that used either reading is summarised under its own
  questions ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
- **Status:** unreported.

## ISO/TS 12913-2:2018, Figures C.2 to C.4 ("extend" for "extent", "reponse" for "response")

- **Location:** Annex C (informative), the questionnaire of Method A: the
  questions of Figures C.2, C.3 and C.4 and the instruction line under each.
- **The print:** "To what extend do you presently hear the following four
  types of sounds?" (Figure C.2), "To what extend do you presently hear the
  following three types of sounds?" (Figure C.3), "For each of the 8 scales
  below, to what extend do you agree or disagree that the present surrounding
  sound environment is..." (Figure C.4); and "Please tick off one reponse
  alternative per type of sound" (Figures C.2 and C.3), "Please tick off one
  reponse alternative per scale" (Figure C.4).
- **The problem:** "extend" is a verb; the question asks "to what extent",
  which Figure C.6 of the same annex spells correctly ("Overall, to what
  extent is the present surrounding sound environment appropriate to the
  present place?"). "reponse" is a misspelling of "response". The figures are
  a questionnaire meant to be put in front of participants as printed, so the
  slips reach the field unless the study corrects them.
- **Evidence:** Figures C.2 and C.3 on PDF page 21 (printed p. 15), Figures
  C.4 and C.6 on PDF page 22 (printed p. 16), all of ISO/TS 12913-2:2018
  (first edition).
- **Library behaviour:** `METHOD_A_SCALES` and `METHOD_A_ALTERNATIVE_PART_1`
  transcribe the questions and instructions as printed, misspellings
  included, so the table can be compared with the page; the docstring of
  `QuestionnaireScale` says a study printing its own questionnaire from it
  should correct them
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
- **Status:** unreported.

## ISO 3744:2010, H.4.2.7 (the altitude correction and the divisor under it)

- **Location:** Annex H (informative), H.4.2.7 "Meteorological and radiation
  impedance corrections", the paragraph that sizes $u_{C_1+C_2}$ from the
  Annex G correction.
- **The print:** "At 120 m altitude and 23 °C the correction is zero and at
  500 m altitude the correction is 0,6 dB. Assuming a triangular distribution
  for this uncertainty, the standard deviation is
  $s_\mathrm{met} = 0{,}6/\sqrt{6} = 0{,}3\ \mathrm{dB}$."
- **The problem:** two independent defects in one sentence pair.
  (a) Annex G, which is normative and which this paragraph points at, gives
  $C_1 + C_2 = 0{,}394$ dB at 500 m and 23,0 °C, not 0,6 dB. The reading is
  self-validating: the same two equations give $-4{,}6 \times 10^{-5}$ dB at
  120 m and 23,0 °C, which is the "zero" the same sentence prints, so the
  constants and the temperature terms are being read as the standard intends.
  0,6 dB is reached at about 697 m at 23,0 °C, or at 500 m only if the air is
  at 30,1 °C.
  (b) $0{,}6/\sqrt{6} = 0{,}245$, not 0,3. The quotient does not give the
  result printed beside it: 0,3 dB is exactly $0{,}6/2$, so either the divisor
  or the result is wrong. For a triangular distribution of half-width $a$ the
  standard deviation is $a/\sqrt{6}$, which is the divisor the sentence names.
- **Evidence:** H.4.2.7 read on PDF page 82 (printed p. 73), against Annex G
  Equations (G.1) and (G.2) with $a = 2{,}2560 \times 10^{-5}$ m$^{-1}$,
  $b = 5{,}2553$, $\theta_0 = 314$ K and $\theta_1 = 296$ K on PDF pages 73 and
  74 (printed pp. 64 and 65), all of BS EN ISO 3744:2010. Both values were
  recomputed from the printed equations alone.
- **Library behaviour:** the Annex H uncertainty budget is not modelled, so no
  published number depends on either figure. The Annex G correction itself is
  evaluated from Equations (G.1) and (G.2) by
  [`reference_atmosphere_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power.py),
  and the conformance check "ISO 3744:2010 Annex G / H.4.2.7" pins the half of
  the paragraph that is right: the correction vanishes at 120 m and 23 °C.
- **Status:** unreported.

## ISO 9613-2:1996, Table 2 (15 °C / 80 % / 1 kHz cell)

- **Location:** Table 2, "Atmospheric attenuation coefficient α for octave
  bands of noise", row 15 °C / 80 % relative humidity, column 1 kHz.
- **The print:** $\alpha = 4{,}1\ \text{dB/km}$.
- **The problem:** Table 2 is a rounded extract of ISO 9613-1, to which the
  clause itself defers ("For values of α at atmospheric conditions not covered
  in table 2, see ISO 9613-1"). Evaluating the ISO 9613-1 pure-tone formula at
  1 kHz, $15\ ^\circ\text{C}$, $80\ \%$ RH and $101{,}325\ \text{kPa}$ gives
  $4{,}1511\ \text{dB/km}$, which rounds to $4{,}2$, not the printed $4{,}1$.
  The neighbouring cells of the same row round correctly (2 kHz: $8{,}338$ ->
  printed $8{,}3$; 4 kHz: $23{,}86$ -> $23{,}7$ at the exact band centre), as
  do the 1 kHz cells of the other rows ($15\ ^\circ\text{C}$ / $50\ \%$:
  $4{,}164$ -> printed $4{,}2$), so the defect is confined to this cell.
- **Evidence:** independent evaluation of the ISO 9613-1 coefficient at both
  the nominal and the exact band-centre frequency ($4{,}1511\ \text{dB/km}$
  either way, 1 kHz being both).
- **Library behaviour:** unaffected. The library never reads Table 2: it
  computes $A_\text{atm}$ from the ISO 9613-1 formula directly
  ([`air_absorption.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/air_absorption.py)),
  so it yields $4{,}15\ \text{dB/km}$ for this condition.
- **Status:** unreported.

## ISO/TR 17534-3:2015, Table 20 (q credited to the wrong footnote of ISO 9613-2 Table 3)

- **Location:** Table 20, "Single number step by step results" of test case
  T08, the row naming the middle-region overlap factor $q$.
- **The print:** `q (ISO 9613-2:1996, Table 3, footnote 1)`.
- **The problem:** footnote 1 of ISO 9613-2:1996, Table 3 is about which ground
  factor and which height each outer region takes ("For calculating $A_s$, take
  $G = G_s$ and $h = h_s$..."). It says nothing about $q$. The factor $q$ is
  defined by footnote 2 of the same table, which is where the guideline itself
  sends the reader in the four other places it prints the row: Table 3 (T01),
  Table 8 (T04), Table 14 (T06) and Table 22 (T09) all read "Table 3
  footnote 2". Table 20 is the single occurrence that reads footnote 1, and the
  value it carries, $q = 0{,}23$, is the one footnote 2 produces.
- **Evidence:** the row was read on PDF page 23 (printed p. 17) of
  ISO/TR 17534-3:2015, and the four consistent occurrences of the same row on
  PDF pages 13, 16, 20 and 41 (printed pp. 7, 10, 14 and 35) of the same
  edition; the two footnotes it points at were read on PDF page 10 (printed
  p. 8) of ISO 9613-2:1996.
- **Library behaviour:** unaffected. The typographical slip is in a
  cross-reference, not in a number, and
  [`ground_attenuation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/outdoor_propagation.py)
  implements $q$ from footnote 2, which is what reproduces the printed 0,23.
- **Status:** unreported.

## VDI 2081 Blatt 1:2001, Section 6.7.3 (the symbol list of Equation (36) sends A back to Equation (36))

- **Location:** Section 6.7.3, the symbol list under Equation (36), the entry
  for the equivalent absorption area ``A``.
- **The print:** "A  äquivalente Absorptionsfläche; in m², Gleichung (36)" /
  "A  is the equivalent absorption area; in m², Equation (36)".
- **The problem:** Equation (36) is the level equation the list belongs to,
  $L_P = L_W + 10\lg[Q/(4\pi r^2) + 4/A]$, in which ``A`` is an input. It
  does not define ``A``. The guideline defines it twice further down the same
  section: Equation (37), $A = 0{,}163\,V/T$, and Equation (39),
  $A = \sum \alpha_i S_n + \sum A_n$. The reference is a self-reference, and
  it stands in both language columns, so it is a typesetting slip in the
  original rather than a translation one.
- **Evidence:** verified on PDF page 43 (printed p. 43) of VDI 2081
  Blatt 1:2001-07, with Equations (37) and (39) on PDF pages 44 and 44
  (printed pp. 44 and 44) of the same print.
- **Library behaviour:** unaffected. The slip is in a cross-reference, not in a
  number;
  [`room_effect`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) takes ``A`` as an
  argument and
  [`sabine_absorption_area`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/steady_field.py)
  implements Equation (37).
- **Status:** unreported.

## VDI 2081 Blatt 1:2001, Section 6.7.3 (the English column calls a hemispherical propagation spherical)

- **Location:** Section 6.7.3, the sentence stating where the reverberation
  field begins, immediately after Equation (36b).
- **The print:** German, "Der Nachhallbereich beginnt bei **halbkugelförmiger**
  Schallausbreitung in einer Entfernung, die größer ist als
  $r_H = 0{,}2\sqrt{A}$"; English, "The reverberation area begins as a
  **spherical** sound propagation at a distance which is greater than
  $r_H = 0.2\sqrt{A}$".
- **The problem:** *halbkugelförmig* is hemispherical, not spherical, and the
  printed constant sides with the German. The reverberation radius is
  $r_H = \sqrt{Q A / 16\pi}$, which is $0{,}199\sqrt{A}$ at the $Q = 2$ of a
  half space and $0{,}141\sqrt{A}$ at the $Q = 1$ of a full one. Only the
  first rounds to the printed $0{,}2$. A reader following the English column
  would take $0{,}2\sqrt{A}$ for the spherical radius and place the
  reverberation field 41 % too far out.
- **Evidence:** verified on PDF page 44 (printed p. 44) of VDI 2081
  Blatt 1:2001-07, both columns of the same sentence read side by side.
- **Library behaviour:** unaffected.
  [`critical_distance`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/steady_field.py) takes ``Q`` as
  an argument and states the hemispherical reading in its own text.
- **Status:** unreported.

## ANSI S3.5-1997, Annex C worked examples (official WG S3-79 errata)

> **Not verified against the page.** ANSI S3.5-1997 is not held locally
> (the R package `SII` vignette is held, not the standard),
> so what this entry calls "the print" is the working group's own description
> of it, not a page this project has read. The recomputations below are
> independent and do reproduce, but the *printed characters* rest on the
> errata list alone. The standard is on the maintainer's pending-acquisition
> list; when a copy arrives the entry is to be re-verified against the print of
> printed pp. 21-22 and this notice removed.

- **Location:** Annex C, Table C.1 (octave-band worked example, p. 21) and
  Table C.2 (one-third-octave worked example, p. 22) of the 1997 printing.
- **The print (per the working group's errata):** (a) Table C.1, row $i = 5$,
  the level-distortion factor $L_i$ under Step 6 is printed as $0.10$; (b)
  Table C.2, first row, the self-speech-masking slope $C_i$ is printed as
  $-45.59$.
- **The problem:** both cells contradict the standard's own normative
  formulas. (a) Clause 5.7 with the example's inputs ($E'_5 = 20\ \text{dB}$,
  $U_5 = 9.33\ \text{dB}$) gives $L_5 = 1 - (20 - 9.33 - 10)/160 = 0.9958$,
  which prints to two decimals as $1.00$, not $0.10$. (b) Clause 5.4 with the
  example's inputs ($B_1 = 40\ \text{dB}$, $f_1 = 160\ \text{Hz}$) gives
  $C_1 = -80 + 0.6 (40 + 10\log_{10} 160 - 6.353) = -46.587$, which prints as
  $-46.59$, not $-45.59$; the example's $Z_i$ column is only consistent with
  the corrected slope ($Z_2$ recomputes to $34.658$ = printed 34.66 dB,
  whereas the misprinted slope would give 34.76 dB). The Table C.1 example is
  the octave-band procedure and the Table C.2 example the one-third-octave
  procedure, so one cell of each is affected.
- **Evidence:** the official errata list published by ASA Working Group S3-79,
  the committee that maintains ANSI S3.5, on its support site (sii.to): "Page
  21, Table C1, row i=5, column Li under Step 6: the value printed as 0.10
  should be changed to 1.00" and "Page 22, Table C2, the first row of numbers,
  value −45.59 should be −46.59"; plus independent recomputation of both cells
  from the normative clauses (above). The same list carries five further
  corrections (a reference spelling, the Tables 1-4 caption wording recorded
  in the next entry, the insertion gain $G_i$ missing from Eq. 23, and two
  Annex B fixes, a cross-reference "B16" that should read "B15" and a wording
  change about the audio-visual approximation); none of those touches a
  formula this library implements. The source is the WG S3-79 errata list at
  sii.to/html/errata.html (captured 2026-07-30, re-checked live 2026-08-04).
  It is not the printed page and cannot substitute for it, which is why this
  entry carries the notice above.
- **Library behaviour:** unaffected; the library computes the corrected values
  from the normative clauses and always did. Its Annex C.2 anchors
  ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data),
  `ANSIS3_5_ANNEX_C1*` and `ANSIS3_5_ANNEX_C2*`) pin the errata-consistent
  chain of both examples, cross-checked to double precision against the
  working group's own reference implementation `SII.C` and its published
  test-case results. The Table C.1 cell is pinned directly: the
  level-distortion factor of clause 5.7 for row $i = 5$ of the Annex C.1
  octave-band example computes to $0.99581$, which prints as the corrected
  $1.00$.
- **Status:** published corrections by the issuing working group; nothing to
  report upstream.

## ANSI S3.5-1997, captions of Tables 1 to 4 (official WG S3-79 erratum)

> **Not verified against the page.** As with the entry above, ANSI S3.5-1997 is not
> held locally, so the wording of the four captions is taken from the working
> group's errata list rather than from a page this project has read. The
> argument that the tables carry no threshold column is independent and does
> hold against the transcribed constants. Re-verify against the print of
> printed pp. 3-5 when the standard is acquired.

- **Location:** the captions of Tables 1, 2, 3 and 4 (pp. 3-5 of the 1997
  printing), the constant tables of the four band procedures: critical band
  (21 bands), equally-contributing critical band (17 bands), one-third octave
  (18 bands) and octave (6 bands).
- **The print (per the working group's errata):** each caption lists the
  quantities the table tabulates and includes the phrase "hearing threshold
  levels,".
- **The problem:** none of the four tables tabulates a hearing threshold
  level. Each carries the band centre frequency (and, for Tables 1, 2 and 4,
  the band limits), the band-importance function $I_i$, the standard speech
  spectrum level $U_i$ by vocal effort and the reference internal noise
  spectrum level $X_i$. The hearing threshold level $T'_i$ is a *user input*
  to the procedure (clause 5.5, where the equivalent internal noise spectrum
  level is $X'_i = X_i + T'_i$), which is exactly the quantity the caption
  invites the reader to look for in the table and to confuse with $X_i$.
- **Evidence:** the official errata list published by ASA Working Group S3-79,
  the committee that maintains ANSI S3.5, on its support site (sii.to): "Pages
  3-5, Tables 1-4: In each of the **figure** captions the phrase 'hearing
  threshold levels,' should be deleted" (the WG S3-79 errata list at
  sii.to/html/errata.html, captured 2026-07-30, re-checked live 2026-08-04; an
  earlier revision of this entry dropped the word "figure" from the
  quotation); plus the tables themselves, which have no such column.
- **Library behaviour:** unaffected. The four tables are implemented with the
  columns they actually carry, exposed per procedure by `sii_procedure()` as
  `band_importance`, `speech_spectrum` ($U_i$) and `internal_noise` ($X_i$),
  and the hearing threshold stays the `threshold=` argument of
  `speech_intelligibility_index`
  ([`src/phonometry/speech/sii.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sii.py)).
- **Status:** published correction by the issuing working group; nothing to
  report upstream.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), Eq. (27)

- **Location:** section A.4.2, Eq. (27) (atmospheric absorption coefficient)
  and the sentence defining its symbols, printed p. 21.
- **The print:** Eq. (27) pairs the coefficient $6.6928 \cdot 10^{-6}$ with
  $f_{rO}$ and $1.3415 \cdot 10^{-6}$ with $f_{rN}$, and the sentence below
  reads "the variables f_rN = 75692 Hz and f_rO = 630.7 Hz represent the
  vibrational relaxation frequencies of oxygen and nitrogen respectively".
- **The problem:** the two subscripts are swapped in the definition sentence.
  The *values* match the *names* it gives them (75 692 Hz is the oxygen
  relaxation frequency and 630.7 Hz the nitrogen one at the reference
  conditions), but they are assigned to the opposite symbols, so the equation
  as printed multiplies the oxygen coefficient by the nitrogen relaxation
  frequency and vice versa. Evaluated that way it gives 14.2 dB/km at 500 Hz
  against the guidance's own Table 4 value of 3.1 dB/km; with $f_{rO}$ and
  $f_{rN}$ exchanged it gives 3.07 dB/km, reproducing Table 4 and the ISO
  9613-1 pure-tone coefficient to 0.02 dB/km. An earlier revision of this
  entry quoted the printed value as 14.3 dB/km and framed the defect as a
  wrong pairing of the coefficients rather than as swapped subscripts in the
  definition.
- **Evidence:** numeric evaluation of Eq. (27) with the printed assignment and
  with the assignment exchanged, against the Table 4 500 Hz cell on the same
  page. Verified on PDF page 20 (printed p. 21) of NORAH2 SC01.D1.5d
  (EASA.2020.FC.06):2024.
- **Library behaviour:** implements the correct pairing; the module docstring
  carries a defensive note so the misprint is not transcribed as a "fix".
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), Eq. (21)

- **Location:** section A.3.3, Eq. (21) (flight path angle).
- **The print:** $\gamma = \text{acos}(\Delta Z/\Delta S)$.
- **The problem:** the arccosine of the climb-to-path ratio returns the
  complement of the path angle ($90^\circ$ in level flight, where $\gamma$
  must be $0^\circ$) and contradicts the guidance's own use of $\gamma$ as the
  climb/descent angle throughout section A.3. ECAC Doc 32, 1st ed., Eq. (10)
  prints the correct form, $\gamma = \text{atan}(\Delta Z/\Delta S)$ with the
  horizontal $\Delta S$ of its Eq. (8).
- **Evidence:** evaluation in level flight; cross-check against Doc 32 Eq.
  (10) and against the NORAH2 prototype input files, whose ``Vang`` columns
  are climb/descent angles ($0^\circ$ in level segments).
- **Library behaviour:** ``flight_path_kinematics`` implements the Doc 32
  ``atan`` form; the result docstring carries the defensive note.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), §A.3.1 triangulation

- **Location:** section A.3.1, steps 2 to 4 (flight-condition interpolation),
  against the triangulation lookup tables shipped with the NORAH2 database
  (``*_triangulation.int``).
- **The print:** steps 2 and 3 normalise the database conditions (spans, with
  $F_{fc} = 2$ on the path angle) and step 4 computes "the Delaunay
  triangulation for the database flight conditions γ̄_j and V̄_j", i.e. of the
  normalised points, offering a lookup table as an equivalent.
- **The problem:** the lookup tables shipped with the database (which the
  guidance says are part of the hemisphere data and should not be edited) are
  the Delaunay triangulation of the raw $(V, \gamma)$ conditions, not of the
  normalised ones: for the R22 set, 14 of the 27 shipped triangles differ from
  the Delaunay triangulation of the normalised conditions. A Delaunay
  triangulation is not invariant under the anisotropic normalisation, so the
  two prescriptions select different enveloping triangles for part of the
  envelope. The distance weights of Eq. (7)/(8) do use the normalised
  coordinates in the prototype (verified against its blended outputs).
- **Evidence:** recomputation of both triangulations for the R22 database;
  bin-for-bin reproduction of the prototype's per-step hemisphere selection
  with the shipped tables, and of its blended levels with normalised-space
  weights, to 0.05 dB.
- **Library behaviour:** ``flight_condition_weights`` follows the printed
  method (Delaunay of the normalised conditions) by default and accepts the
  database lookup table via ``triangles``, which reproduces the reference
  implementation exactly.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), Eq. (46)

- **Location:** section A.4.5, Eq. (46) (source-side ground effect weighted by
  diffraction).
- **The print:** the weighting exponent reads
  $(\Delta L_{g,s'} - \Delta L_{d,s})/20$.
- **The problem:** no term $\Delta L_{g,s'}$ exists; the prose directly below
  the equation defines $\Delta L_{d,s'}$ as "the attenuation due to the
  diffraction between the image source S′ and R", the receiver-side companion
  Eq. (47) prints the parallel term correctly as $\Delta L_{d,r'}$, and the
  CNOSSOS-EU method the section is based on writes $\Delta_\text{ground}(S,O)$
  with $\Delta_\text{dif}(S',R)$ in that position. The subscript $g$ is a
  misprint for $d$.
- **Evidence:** internal consistency of the section (its own prose and Eq.
  (47)) and the CNOSSOS-EU source of the equations.
- **Library behaviour:** implements the image-source diffraction term
  $\Delta L_{d,s'}$ as defined by the prose.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), §A.4.5 cross-references

- **Location:** section A.4.5, the definitions under Eq. (46) (printed p. 32)
  and Eq. (47) (printed p. 33).
- **The print:** four cross-references to eq. 44, in **three** different
  wordings: "calculated as per eq. 44" for $\Delta L_{d,s'}$ and again for
  $\Delta L_{d,s}$ under Eq. (46); "calculated as in eq. 44" for
  $\Delta L_{d,r'}$ under Eq. (47); and "calculated as in Subsection eq. 44"
  for $\Delta L_{d,s}$ under Eq. (47). An earlier revision of this entry
  quoted all four with the first wording.
- **The problem:** Eq. (44) is the multiple-diffraction coefficient $C''$; the
  attenuation due to diffraction is Eq. (42). All four cross-references point
  at the auxiliary coefficient instead of the formula they describe, and the
  fourth also carries a dangling "Subsection" with no subsection number after
  it.
- **Evidence:** the terms are attenuations in dB, which only Eq. (42)
  produces; Eq. (44) is a dimensionless coefficient consumed by Eq. (42).
  Verified on PDF pages 31 and 32 (printed pp. 32 and 33) of NORAH2 SC01.D1.5d
  (EASA.2020.FC.06):2024.
- **Library behaviour:** evaluates the image-path and direct diffraction terms
  with Eq. (42), using Eq. (44) for $C''$ inside it.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), §A.3.5 Approach 3 (full-rpm idle base)

- **Location:** section A.3.5, Approach 3, step 3 (printed p. 18), against the
  "Fl. idle" row of Table 3 (printed pp. 18-19).
- **The print:** the step reads "add offset of 12 dB\* to derive out of ground
  hover from the in-ground hover disk, -12 dB\* to derive reduced-rpm idle from
  in-ground hover disk, and -2.5 dB\* to derive full-rpm idle from out of
  ground hover"; the table prints
  $LA_{\mathrm{FL.idle}}(\theta) = LA_{\mathrm{HIGE}}(\theta) - 2.5\ \mathrm{dB}^*$.
- **The problem:** the prose derives full-rpm idle from out-of-ground hover
  where the table derives it from in-ground hover, and the two prescriptions
  land 12 dB apart (via the prose,
  $LA_{\mathrm{HOGE}}(\theta) - 2.5 = LA_{\mathrm{HIGE}}(\theta) + 9.5$; via
  the table, $LA_{\mathrm{HIGE}}(\theta) - 2.5$). Only the table keeps the
  physical ordering of the conditions (full-rpm idle above reduced-rpm idle,
  both below in-ground hover). The paragraph that introduces these phases, at
  the end of section A.3.3 (printed p. 17), is itself left unfinished ("For
  specific phases of a flight such as, turns, hover, taxiing"), pointing at an
  editing pass the section did not get.
- **Evidence:** the corrections shipped with the V2.0.74 public database are
  all relative to the in-ground-hover disk (`Fullrpmidle -2` in every type's
  interpolation lookup file), agreeing with the table and not with the prose.
  Verified on PDF pages 16, 17 and 18 (printed pp. 17, 18 and 19) of NORAH2
  SC01.D1.5d (EASA.2020.FC.06):2024.
- **Library behaviour:** `hover_derived_hemisphere` applies every Table 3
  offset from the in-ground-hover hemisphere, as the table prints; the
  docstring states the base condition explicitly.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), §A.3.5 taxi assignment

- **Location:** section A.3.5, last paragraph (printed p. 19).
- **The print:** "To include taxiing for helicopters with and without wheels
  into the noise calculation the measured and derived hemispheres for
  in-ground hover and full-rpm idle respectively should be employed."
- **The problem:** read literally, the "respectively" pairs the wheeled
  helicopter with the in-ground-hover source and the wheel-less one with
  full-rpm idle, which is the reverse of the operations it models: a
  helicopter without wheels can only taxi by hovering in ground effect, and a
  wheeled helicopter ground-taxis on its wheels with the rotor at governed
  idle, not producing lift. The two lists read as transposed. No oracle
  settles it (the public release ships no taxi verification case), so the
  pairing is corrected from the physics of the operations alone.
- **Evidence:** internal comparison of the two prose lists against the
  operations they name. Verified on PDF page 18 (printed p. 19) of NORAH2
  SC01.D1.5d (EASA.2020.FC.06):2024.
- **Library behaviour:** no function is affected (the rule selects between two
  hemispheres the reader has already built); the rotorcraft guide documents
  the physical pairing, wheel-less taxi on the in-ground-hover hemisphere and
  wheeled taxi on the full-rpm-idle one, with this caveat.
- **Status:** unreported.

## NORAH2 rotorcraft guidance SC01.D1.5d (EASA.2020.FC.06), Table 3 offsets vs the shipped corrections

- **Location:** Table 3, Approach 3 column (printed pp. 18-19), against the
  `&CORRECTIONS` block of the interpolation lookup files shipped with the
  NORAH2 V2.0.74 public release.
- **The print:** offsets of +12 dB\* (out-of-ground hover), -12 dB\*
  (reduced-rpm idle) and -2.5 dB\* (full-rpm idle) from the in-ground-hover
  disk, with the asterisked note that they were derived from measurements
  with inverted microphones on ground plates and "may not be valid for other
  microphone setups".
- **The problem:** the reference database the guidance builds on ships
  different values: every one of the eleven per-type triangulation lookup
  files (``*_triangulation.int``) of the public release carries `Corr_dB`
  8, -10 and -2 for the same three
  operations, so the published constants and the database disagree by 4, 2
  and 0.5 dB. The guidance, whose section A.3.1 declares the shipped lookup
  data part of the hemisphere database and not to be edited, does not mention
  the difference, and its note questions the validity of the published values
  without naming the ones actually shipped.
- **Evidence:** the identical `&CORRECTIONS` blocks of the eleven
  triangulation lookup files (``*_triangulation.int``) of the V2.0.74 public
  release; the published
  constants verified on PDF pages 17 and 18 (printed pp. 18 and 19) of NORAH2
  SC01.D1.5d (EASA.2020.FC.06):2024.
- **Library behaviour:** `hover_derived_hemisphere` defaults to the published
  Table 3 constants and accepts a measured or database correction as
  ``offset_db``; the end-to-end hover verification case passes the database's
  +8 dB explicitly, and the docstring records the divergence.
- **Status:** unreported.

## RANDI 3.1 Physics Description (NRL, Breeding et al.), Table 2

- **Location:** Table 2 (representative ship source levels).
- **The print:** two cells deviate from the report's own Eqs. (2) to (5)
  evaluated with the Table 1 average lengths and speeds: the Merchant value at
  25 Hz (about 3 dB high) and the Tanker value at 300 Hz (about 1 dB low). The
  Fishing Vessel row is not reproducible from the Table 1 averages at all (a
  constant offset of about 3.8 dB suggests different assumed inputs).
- **The problem:** the report does not state the exact inputs used for Table
  2, and two cells contradict its own equations while every Large Tanker and
  Super Tanker cell agrees to 0.06 dB.
- **Evidence:** recomputation of all 25 cells from Eqs. (2) to (5).
- **Library behaviour:** the regression test pins the reproducible rows and
  excludes the contradicting cells with the rationale in the test.
- **Status:** unreported (technical report rather than a standard).

## Osses, García & Kohlrausch (2016), fluctuation-strength model, Eq. (3)

- **Location:** Eq. (3), the critical-band-rate (Bark) transformation of the
  excitation-pattern front-end.
- **The print:**
  $z(f) = 13 \cdot \arctan(0.76 \cdot 10^{-4} \cdot f) + 3.5 \cdot \arctan((f/7500)^2)$.
- **The problem:** the first coefficient is the Zwicker-Terhardt
  $0.76 \cdot 10^{-3}$ with the exponent misprinted. The paper's own anchors
  disprove the print: it states $0.5\ \text{Bark} = 50\ \text{Hz}$ and
  $23.5\ \text{Bark} = 13.2\ \text{kHz}$ (section 2.1.2) and
  $15\ \text{Bark} = 2.7\ \text{kHz}$ (section 3.1), all of which require
  $10^{-3}$. With $10^{-4}$, $z(1\ \text{kHz}) = 1.05$ instead of
  $8.51\ \text{Bark}$ and the model's 47 filter centres would span 491 Hz to
  20 kHz instead of 50 Hz to 13.2 kHz.
- **Evidence:** evaluation of Eq. (3) under both exponents against the paper's
  printed Bark/frequency anchors. The printed section 2.1.2 range "0.5 Bark
  (50 Hz) to 23.5 Bark (13.2 kHz)" and the section 3.1 anchor "15 Bark (2.7
  kHz)" all reproduce under the Zwicker-Terhardt $0.76 \cdot 10^{-3}$ (50.6
  Hz, 13.07 kHz and 2.71 kHz) and none of them under the printed exponent.
  Verified on PDF page 4 (printed p. 4) of Osses, García & Kohlrausch,
  ICA:2016, with the anchors on PDF page 7 (printed p. 7) of the same paper.
- **Library behaviour:** implements $0.76 \cdot 10^{-3}$ with a note at the
  formula; the carrier-frequency sweep test would catch a regression to the
  printed value
  ([`fluctuation_strength.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/fluctuation_strength.py)).
- **Status:** unreported (conference paper rather than a standard).

## Medwin & Clay, Fundamentals of Acoustical Oceanography (1998), Eq. (3.4.30) (boric-acid coefficient)

- **Location:** the Francois-Garrison boric-acid term as transcribed by the
  textbook, **Eq. (3.4.30), printed p. 110**. An earlier revision of this
  entry cited Eq. 3.4.29, which is the total-absorption sum of the three terms
  on printed p. 109; the boric-acid block is the equation after it.
- **The print:**
  $A_1 = (8.68/c) \cdot 10^{0.78\,\text{pH} - 5}\ \text{dB km}^{-1}\ \text{kHz}^{-1}$.
- **The problem:** the original paper (Francois & Garrison 1982, JASA 72, Part
  II, Eq. (10) and Fig. 7) prints 8.86; the digits are transposed. Only 8.86
  reproduces the paper's own Table IV: with 8.68 the boric-dominated cells at
  $0.6$ to 30 kHz sit up to $1.7\,\%$ below the printed totals (worst relative
  case 2 kHz, 10 °C, $S = 35$: $0.1209$ vs the printed 0.123 dB/km).
- **Evidence:** recomputation of all sampled Table IV cells under both
  coefficients against the paper's printed values. Verified on PDF page 131
  (printed p. 110) of Medwin & Clay, Fundamentals of Acoustical Oceanography
  (1998), and on PDF pages 8 and 9 (printed pp. 1886 and 1887) of Francois &
  Garrison (1982), JASA 72, Part II, which print the paper's own
  $A_1 = (8.86/c) \cdot 10^{0.78\,\text{pH} - 5}$.
- **Library behaviour:** implements the paper's 8.86 with a defensive note;
  the pinned Table IV set includes the boric-dominated rows.
- **Status:** unreported (textbook rather than a standard).

## Medwin & Clay (1998), Eq. (3.4.30) (sound speed printed as q)

- **Location:** the same Eq. (3.4.30) block, printed p. 110, its last line.
- **The print:** $q = 1412 + 3.21T + 1.19 S + 0.0167 z\ \text{m/s}$.
- **The problem:** the quantity the block needs is the sound speed $c$, which
  is what the two lines above it divide by ($A_1 = 8.68/c$, and
  $A_2 = 21.44 S/c$ in the magnesium-sulfate block on the same page). No
  symbol $q$ is defined anywhere in the section, so the transcribed system is
  not closed: a reader following the printed symbols has no value for $c$.
  Francois & Garrison 1982 Part II prints the same polynomial as
  $c = 1412 + 3.21 T + 1.19 S + 0.0167 D$, introduced by "where c is the sound
  speed (m/s), given approximately by".
- **Evidence:** the block's own use of $c$ two lines above, and the source
  paper. Verified on PDF page 131 (printed p. 110) and PDF page 130 (printed
  p. 109) of Medwin & Clay (1998), and of PDF page 8 (printed p. 1886) of
  Francois & Garrison 1982 Part II (JASA 72).
- **Library behaviour:** unaffected; the absorption model takes the sound
  speed from the same polynomial under the name `c`.
- **Status:** unreported (textbook rather than a standard).

---

## Maa (1998), "Potential of microperforated panel absorber", JASA 104(5), Eq. (5b)

- **Location:** Eq. (5b), the mass-reactance coefficient of the
  microperforated panel, printed as
  $k_m = 1 + [1 + k^2/2]^{-1/2} + 0.85\,d/t$.
- **The print:** the first bracket term reads $(1 + k^2/2)^{-1/2}$.
- **The problem:** the same paper's Eq. (4), from which (5b) is factored,
  prints the term as $(3^2 + k^2/2)^{-1/2}$, and only that form reproduces the
  Crandall low-$k$ limit $Z_1 \to (4/3) j\omega\rho_0 t$ of the paper's own
  Eq. (3a): at $k \to 0$ the printed (5b) gives an internal mass factor of 2
  instead of 4/3. The paper's own Fig. 1 confirms it: with
  $0.85 \cdot d/t = 0.85$ the plotted $k_m$ starts near $2.2$ ($= 4/3 + 0.85$)
  at $k = 0.1$, not at $2.85$.
- **Evidence:** recomputation of both bracket variants against Eq. (4), Eq.
  (3a) and the Fig. 1 curve; the exact Bessel solution of Eq. (2) agrees with
  Eq. (4) within Maa's stated $\sim 6\,\%$ only with the $3^2$ form (the 1
  form errs by $>30\,\%$ at low $k$). Verified on PDF page 2 (printed p. 2862)
  of Maa (1998), "Potential of microperforated panel absorber", JASA 104(5),
  which carries Eq. (4) and Eq. (5b) fifteen lines apart on the same column.
- **Library behaviour:** implements the exact Eq. (2) (no approximation), so
  the misprint does not enter the code; the regression test
  ``test_maa_exact_vs_wide_range_approximation`` pins the exact solution to
  the corrected Eq. (4) form.
- **Status:** unreported (journal paper; the correct form appears in Maa's
  earlier 1975/1987 papers and in secondary literature).

## Jiménez, Groby, Pagneux & Romero-García (2017), Appl. Sci. 7(6), 618, Eqs. (7)-(8)

- **Location:** Eqs. (7) and (8), the rectangular-duct visco-thermal effective
  density and bulk modulus (Stinson's series, used for the square necks and
  cavities of the slit + Helmholtz-resonator absorber).
- **The print:** the leading normalising constant of both series is 4:
  $\rho_\text{eff} = -\rho_0 \cdot a^2 b^2/(4 \cdot G_\rho^2 \cdot \Sigma)$
  and the matching $4 \cdot (\gamma - 1) \cdot G_\kappa^2/(a^2 b^2)$ factor
  inside $\kappa_\text{eff}$.
- **The problem:** the correct constant is 64 (a factor-16 error). Only 64
  reproduces the exact limits of the model: as the boundary layers vanish
  $\rho_\text{eff} \to \rho_0$ and $\kappa_\text{eff} \to \kappa_0$ (the
  printed 4 gives $16 \cdot \rho_0$), and at DC the square duct's
  $j\omega \cdot \rho_\text{eff}$ tends to the exact Shah-London Poiseuille
  flow resistivity: the series value $a^6/(64 \cdot S_0) = 28.4542$ matches
  $fRe/2 = 28.455$ (in units of $\eta/a^2$), where $S_0$ is the double
  transverse-mode sum at $G = 0$; the printed 4 gives sixteen times that.
- **Evidence:** evaluation of both constants against the boundary-layer-free
  limits and the Shah-London exact square-duct value; the wide-duct limit of
  the series also only matches the papers' own slit model (Eq. (6)) with 64.
- **Library behaviour:** implements 64 with a docstring note; the limits are
  pinned in
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py)
  and the conformance check "Poiseuille limit (Stinson 1991)".
- **Status:** unreported (journal paper rather than a standard).

## Jiménez et al. (2017), Appl. Sci. 7(6), 618 / Sci. Rep. 7, 5389, slit-radiation term

- **Location:** Appl. Sci. Eq. (3), the characteristic radiation impedance of
  the slits, and the identical Methods reprint in the metadiffusers paper
  (Sci. Rep. 7, 5389, Eq. (5)).
- **The print:**
  $Z_{\Delta l_\text{slit}} = -i\omega \cdot \Delta l_\text{slit} \cdot \rho_0/(\phi t \cdot S_0)$.
- **The problem:** the term models the added radiation mass of the slit mouth,
  but the printed $-i\omega$ prefactor is an opposite-time-convention
  ($e^{-i\omega t}$) expression inconsistent with the papers' otherwise
  $e^{+i\omega t}$ transfer-matrix chain (the $+i$ off-diagonal slit matrices
  of Appl. Sci. Eq. (2) and the $-i$ cotangent-type resonator impedance).
  Transcribed literally into that chain, the correction raises the slit-panel
  resonance where an added mass must lower it: for a 1 mm slit with a 30 mm
  lattice step and 50 mm period the absorption peak moves from 378.6 Hz to
  386.8 Hz as printed, against 370.8 Hz with the mass sign. The neck end
  corrections of the same model behave correctly (they lower the resonator
  resonance).
- **Evidence:** numerical evaluation of both signs of the correction against
  the uncorrected panel; the direction of the neck end corrections of the same
  papers as the consistent control.
- **Library behaviour:** uses the added-mass sign ($+j\omega$ in the
  $e^{+j\omega t}$ convention of the library), conjugating the printed term
  exactly as it conjugates the papers' Stinson duct series; direction and peak
  are pinned by ``test_slit_radiation_correction_lowers_resonance`` in
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py).
- **Status:** unreported (journal papers rather than standards).

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Table 5.1

- **Location:** Table 5.1, "Coefficient and exponent values in the Delany and
  Bazley, Miki and modified Miki models", row "Miki [6,7]", coefficient $r$.
- **The print:** $r = 0.0109$.
- **The problem:** the original source (Miki 1990, J. Acoust. Soc. Jpn (E)
  11(1), Eq. (34)) prints
  $\beta(f) = (\omega/c_0)[1 + 0.109 \cdot (f/\sigma)^{-0.618}]$; the table
  drops a digit. With 0.0109 the real part of the Miki wavenumber at
  $f/\sigma = 0.01$ is $1.19$ instead of $2.88$, inconsistent with the same
  table's Delany-Bazley row ($3.10$ from its own $r = 0.0862$, $s = -0.693$)
  and with the "modified Miki" row the book itself derives from it.
- **Evidence:** digit check against the original Miki (1990) paper (Eqs.
  (30)–(34)) and cross-computation of both variants at the fit-range edge.
  Verified on PDF page 168 (printed p. 149) of Attenborough & Van Renterghem,
  Predicting Outdoor Sound 2e:2021, and on PDF page 4 (printed p. 22) of Miki,
  J. Acoust. Soc. Jpn (E) 11(1):1990.
- **Library behaviour:** implements Miki's original 0.109; the digitization
  point $f/\sigma = 0.1$ is pinned in ``tests/reference_data/`` and in the
  conformance check "Miki 1990 Eqs. (30)-(34)".
- **Status:** unreported (textbook rather than a standard).

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Eq. (5.13)

- **Location:** Eq. (5.13), the Johnson-Champoux-Allard bulk complex density,
  with $G(\Lambda) = \sqrt{1 - 4iT\eta\rho_0\omega/(R_S^2\Lambda^2\Omega^2)}$.
- **The print:** the tortuosity $T$ appears to the first power inside
  $G(\Lambda)$.
- **The problem:** Johnson et al. (1987) and the standard JCA formulation (Cox
  & D'Antonio 3e Eq. (6.19); Allard & Atalla) carry $T^2 = \alpha_\infty^2$
  there. The first-power print breaks the high-frequency asymptote that
  defines the viscous characteristic length: with $T^2$ the density tends to
  $(T\rho_0/\Omega)(1 + (1 - j)\delta_v/\Lambda)$ with
  $\delta_v = \sqrt{2\eta/\rho_0\omega}$, while the printed form tends to a
  $\delta_v/(\Lambda\sqrt{T})$ correction, which for $T = 2$ means an error of
  $29\,\%$ in the boundary-layer term for the same $\Lambda$.
- **Evidence:** asymptotic expansion of both variants against the Johnson et
  al. definition of $\Lambda$ and against Cox & D'Antonio Eq. (6.19); the
  library's high-frequency JCA test pins the $T^2$ behaviour. Verified on PDF
  page 173 (printed p. 154) of Predicting Outdoor Sound 2e:2021.
- **Library behaviour:** implements the standard $T^2$ form (Cox & D'Antonio
  Eq. (6.19)); the asymptote is pinned in
  ``test_high_frequency_density_asymptote``.
- **Status:** unreported (textbook rather than a standard).

## Bies, Hansen & Howard, Engineering Noise Control 5e (2017), Eq. (8.141)

- **Location:** Section 8.9.1, Eq. (8.141) (printed p. 461), the transmission
  loss of a muffler from the elements of its total four-pole matrix.
- **The print:**
  $$
  TL = 10 \lg\left[ \left(\frac{1+M_n}{1+M_1}\right)^2 \cdot \tfrac{1}{4} \cdot
  \left| \frac{Z_{A1}}{Z_{An}} T_{11} + \frac{T_{12}}{Z_{An}}
  + Z_{A1} T_{21} + \frac{Z_{An}}{Z_{A1}} T_{22} \right|^2 \right],
  $$
  i.e. with the impedance ratio $Z_{A1}/Z_{An}$ weighting $T_{11}$ and its
  inverse weighting $T_{22}$.
- **The problem:** the source the equation itself cites (Munjal, *Acoustics of
  Ducts and Mufflers* 2e, Eq. (3.27), p. 105) carries the overall prefactor
  $Z_{An}/Z_{A1}$ (equivalently $\sqrt{S_1/S_n}$ inside a $20\log_{10}$ form)
  with $T_{11}$ unweighted and $Z_{A1}/Z_{An}$ on $T_{22}$. As printed, Eq.
  (8.141) fails the sudden-expansion limit: a zero-length element ($T = I$)
  between $S_1 = 0.01\ \text{m}^2$ and $S_n = 0.02\ \text{m}^2$ is a sudden
  area expansion with the classic
  $TL = 10\log_{10}[(1+m)^2/(4m)] = 0.512\ \text{dB}$ ($m = S_n/S_1 = 2$), but
  the printed equation gives
  $\tfrac{1}{4} \cdot (Z_{A1}/Z_{An} + Z_{An}/Z_{A1})^2 = 1.938\ \text{dB}$.
  Reading the ratios as an overall $Z_{A1}/Z_{An}$ prefactor instead is also
  wrong: it gives 6.532 dB on the same oracle and violates reciprocity
  ($11.34$ vs -0.70 dB for an expansion chamber between unequal pipes; a
  negative TL for a passive element). The misprint is invisible whenever the
  inlet and outlet areas are equal, where every variant reduces to Eq.
  (8.148).
- **Evidence:** numeric evaluation of the zero-length identity element and of
  an unequal-port expansion chamber under the printed form, the inverted
  prefactor and Munjal Eq. (3.27); only Munjal's form reproduces the
  sudden-expansion classic (0.512 dB, both directions) and is reciprocal.
- **Library behaviour:** `transmission_loss` in
  [`silencers.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencers.py) implements
  Munjal Eq. (3.27), with the sudden-expansion limit and TL reciprocity pinned
  by regression tests
  ([`tests/noise_control/test_silencers.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_silencers.py))
  and a defensive note at the formula.
- **Status:** unreported (textbook rather than a standard).

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
  6.3 or more square meters (68 sq ft) of absorption per table": 6.313 m² is
  $67.95\ \text{ft}^2$ and 6.33 m² is $68.14\ \text{ft}^2$, so both print as
  68 sq ft, and both round to 6.3 m². An earlier revision of this entry
  offered that conversion as corroboration. Verified on PDF page 665 (printed
  p. 666) of Long, Architectural Acoustics 2e (2014).
- **Library behaviour:** `absorption_per_table` in
  [`crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/crowd_noise.py) computes the bound
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
- **The problem:** the two statements contradict each other. $Q$ in ft³/min
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

## Vigran, Building Acoustics (2008), Figure 8.37 caption (carpet stiffness exponent)

- **Non-normative source** (textbook).
- **Location:** section 8.4.2, the caption of Figure 8.37 on printed p. 320 /
  pdf p. 341, which labels the predicted improvement curves of two floor
  coverings laid on a heavyweight floor.
- **The print:** "Predicted improvement with a linear model: stiffness of
  carpet squares 3.2·10^6 N/m, vinyl covering 5.2·10^6 N/m." (Vigran writes
  the decimal separator as a period.)
- **The problem:** the carpet exponent is one order too high. The body text
  introducing the figure, on printed p. 321, says of the carpet squares that
  "we have assumed that the covering has the same stiffness as used in Figure
  8.36", and Figure 8.36 is labelled $s = 3.2 \cdot 10^{5}\ \text{N/m}$ inside
  the plot, the same value the body text on printed p. 320 gives for it. The
  vinyl value in the same caption is correct.
- **Evidence:** printed p. 320 states $3.2 \cdot 10^{5}\ \text{N/m}$ "giving a
  resonance frequency f0 of approximately 130 Hz with a hammer mass of 0.5
  kg", and $\sqrt{3.2 \cdot 10^{5}/0.5}/(2\pi) = 127.3\ \text{Hz}$ reproduces
  that while $\sqrt{3.2 \cdot 10^{6}/0.5}/(2\pi) = 402.6\ \text{Hz}$ is a
  frequency that appears nowhere in the section. The same arithmetic applied
  to the caption's vinyl value gives
  $\sqrt{5.2 \cdot 10^{6}/0.5}/(2\pi) = 513.3\ \text{Hz}$ against the
  "approximately 510 Hz" printed on p. 321, which fixes the formula and the
  hammer mass the author used. Graphically, the two dashed prediction curves
  of Fig. 8.37 are about two octaves apart, matching the stiffness ratio
  $5.2 \cdot 10^{6}/(3.2 \cdot 10^{5}) = 16.25$ (a factor 4.03 in frequency)
  and not $5.2 \cdot 10^{6}/(3.2 \cdot 10^{6}) = 1.63$ (a factor 1.27).
  Verified on PDF page 341 (printed p. 320) of Vigran, Building
  Acoustics:2008, on which both caption exponents read 6 unambiguously and the
  body text of the same page reads $3.2 \cdot 10^{5}\ \text{N/m}$, with the
  surrounding argument read on PDF page 340 (printed p. 319) and PDF page 342
  (printed p. 321) of the same edition.
- **Library behaviour:** none needed; the library takes the covering stiffness
  from the user through `covering_contact_stiffness`, and the printed cut-off
  frequencies it is anchored on come from Hopkins rather than from this
  caption.
- **Status:** unreported.

## Norton & Karczub, Fundamentals of Noise and Vibration Analysis for Engineers 2e (2003), Eq. (6.56)

- **Location:** Section 6.6.1, Eq. (6.56), the coupling loss factor of two
  homogeneous plates joined by $N$ point connections (printed p. 418).
- **The print:** the denominator bracket
  $(\rho_{s1}^2 h_1^2 c_{L1}^2 + \rho_{s2}^2 h_2^2 c_{L2}^2)$ appears to the
  first power.
- **The problem:** as printed the expression is not dimensionless. The
  prefactor $4 N h_1 c_{L1}/(\sqrt{3}\,\omega S_1)$ already has the dimensions
  of $\text{m}^2\,\text{s}^{-1}$ over $\text{m}^2\,\text{s}^{-1}$, i.e. unity,
  so the remaining ratio of the two bracketed products must be dimensionless
  too. That requires the sum to be squared, $A_1 A_2/(A_1 + A_2)^2$.
- **Evidence:** the book's own answer to problem 6.13 (printed p. 617). With
  the squared denominator the twelve-bolt aluminium pair gives
  $\eta_{12} = 1.43 \cdot 10^{-2}$ at 125 Hz against the printed
  $1.44 \cdot 10^{-2}$, and matches the whole 125 Hz to 2 kHz column to better
  than $0.7\,\%$; with the printed (unsquared) denominator the result is not a
  loss factor at all. Verified on PDF page 438 (printed p. 418) of Norton &
  Karczub, Fundamentals of Noise and Vibration Analysis for Engineers 2e:2003.
- **Library behaviour:** `point_connection_coupling_loss_factor` in
  [`junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/junction_transmission.py)
  implements the squared form, with the printed column pinned by a regression
  test
  ([`tests/vibration/structural/test_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_junction_transmission.py))
  and a note at the formula.
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), problem 6.13 answer (eta_21 column)

- **Location:** Answers to problems, problem 6.13 (printed p. 617), the two
  $\eta_{21}$ columns of the welded and bolted tables.
- **The print:** for the two aluminium plates (plate 1: 3 mm, 2.5 m × 1.2 m;
  plate 2: 5.5 mm, 2.0 m × 1.2 m) the answer gives, at 125 Hz,
  $\eta_{21} = 5.77 \cdot 10^{-3}$ (welded) and $2.64 \cdot 10^{-2}$ (bolted).
- **The problem:** both columns are exactly the corresponding $\eta_{12}$
  column multiplied by $h_2/h_1 = 1.833$. The SEA consistency relationship is
  $n_1 \eta_{12} = n_2 \eta_{21}$ (Eq. 6.8) with the flat-plate modal density
  $n = S\sqrt{12}/(2 c_L h)$ of Eq. (6.25), so the correct factor is
  $n_1/n_2 = (S_1 h_2)/(S_2 h_1) = 2.292$. The printed column drops the plate
  area ratio $S_1/S_2 = 1.25$.
- **Evidence:** the ratio of the printed columns is 1.8333 to five digits in
  every band of both tables, which is $h_2/h_1$ exactly; the $\eta_{12}$
  columns themselves reproduce from Eqs. (6.52) to (6.56) to better than 0.7
  %. Verified on PDF page 637 (printed p. 617) of Norton & Karczub 2e:2003,
  the page that carries both answer tables.
- **Library behaviour:** the $\eta_{12}$ columns are used as the regression
  oracle; $\eta_{21}$ is obtained from Eq. (6.8) with the full modal
  densities, and a test pins the 2.292 ratio explicitly
  ([`tests/vibration/structural/test_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_junction_transmission.py)).
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), problem 6.10 (platform area)

- **Location:** Problems, problem 6.10 (printed pp. 593-594) and its answer
  (printed p. 617): a satellite platform coupled to an aluminium cylinder, 500
  Hz octave, printed answers $\eta_{12} = 4.26 \cdot 10^{-4}$,
  $\eta_{21} = 3.92 \cdot 10^{-4}$ and $\Pi_\text{in} = 1.31\ \text{W}$.
- **The print:** the statement gives the aluminium platform as "5 mm thick and
  3.5 m × 3 m", i.e. 10.5 m².
- **The problem:** that area is inconsistent with the three printed answers.
  Eq. (6.12) fixes $E_1/E_2 = (\eta_2 + \eta_{21})/\eta_{12} = 6.554$ from the
  printed loss factors alone, whereas the stated geometry with the printed
  velocities (27.2 and 13.2 mm/s) gives 7.88. The energy ratio is independent
  of the modal densities and of the wave speed, so no choice of those can
  reconcile it; only the platform area can. The area the answers imply is 8.73
  m², which is $3.5 \times 3$ minus the $\pi(0.75\ \text{m})^2$ footprint of
  the cylinder that Fig. P6.10 shows passing through the platform.
- **Evidence:** with 8.73 m² the inversion of Eqs. (6.15), (6.8) and (6.10)
  returns $\eta_{12} = 4.256 \cdot 10^{-4}$, $\eta_{21} = 3.910 \cdot 10^{-4}$
  and $\Pi_\text{in} = 1.306\ \text{W}$, i.e. all three printed answers within
  0.4 %; the cylinder's own energy and modal density come out unchanged either
  way. Verified on PDF page 613 (printed p. 593), which carries the statement
  and its dimensions, and PDF page 637 (printed p. 617), which carries the
  three answers, of Norton & Karczub 2e:2003.
- **Library behaviour:** `power_injection_clf` in
  [`experimental_sea.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/experimental_sea.py)
  implements the inversion as published; the regression test uses the free
  platform area and documents the discrepancy
  ([`tests/vibration/structural/test_experimental_sea.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_experimental_sea.py)).
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), problem 3.14 (structural loss factor)

- **Location:** Problems, problem 3.14 (printed p. 580) and its answer
  (printed p. 611): the octave-band transmission loss of a 20 mm particle
  board panel.
- **The print:** the statement gives the panel a structural loss factor of
  "~1.5 × 10⁻²"; the answer gives 27 dB at 8 kHz and 38.6 dB at 16 kHz.
- **The problem:** those two values are above the panel's critical frequency
  (4885 Hz for Appendix 4 particle board, $f_c t = 97.7\ \text{m/s}$) and
  therefore follow Cremer's Eq. (3.110), which contains $10\log_{10}(\eta)$.
  With $\eta = 1.5 \cdot 10^{-2}$ the equation gives 37.0 dB and 48.5 dB, ten
  decibels above the printed answers; with $\eta = 1.5 \cdot 10^{-3}$ it gives
  27.0 dB and 38.5 dB.
- **Evidence:** the 10 dB offset is exactly one decade of $10\log_{10}(\eta)$,
  and the frequency dependence of the printed pair independently fixes
  $f_c = 4939\ \text{Hz}$ against the Appendix 4 value of 4885 Hz. The eight
  values below coincidence reproduce exactly from Eq. (3.104) and do not
  involve $\eta$. The discrepancy is a decade in a printed exponent, so the
  two figures were read as images rather than through the text layer. Verified
  on PDF page 600 (printed p. 580) and PDF page 631 (printed p. 611) of Norton
  & Karczub 2e (2003).
- **Library behaviour:** the regression test uses $\eta = 1.5 \cdot 10^{-3}$,
  the value the printed answers require
  ([`tests/building/prediction/test_panel_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_panel_transmission.py)).
- **Status:** unreported (textbook rather than a standard).

---

## Vigran, Building Acoustics (2008), Eq. (9.18) (receiving-side coefficient)

- **Location:** Section 9.2.3.2, Eq. (9.18) (printed p. 339), the transmission
  factor of the one-dimensional suspended-ceiling plenum model after Mechel
  (1980).
- **The print:** the denominator reads $m_S L_S \cdot m_R L_R h$ with the
  **unprimed** $m_R$, while the exponent of the same expression carries the
  primed $m'_R = m_R + s_R \tau_R / h$ of Eq. (9.17).
- **The problem:** the two sides of the plenum are integrated the same way.
  The receiving-side integral is
  $\int_0^{L_R} \exp(-\varepsilon m'_R x)\,dx = (1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R)$,
  so the factor that normalises it must be $m'_R L_R$, exactly as the
  source-side one is $m_S L_S$. Read literally, the printed expression is not
  a transmission factor at all: it carries a spurious
  $m'_R/m_R = 1 + s_R \tau_R/(h m_R)$, so it grows without bound as the plenum
  damping falls. Two consequences are visible with ordinary inputs
  ($L_S = L_R = 5\ \text{m}$, $h = 0.6\ \text{m}$,
  $R_S = R_R = 25\ \text{dB}$, $\varepsilon = 2$, $s_S = s_R = 0.5$): the
  model **diverges as the plenum damping vanishes**, giving
  $R_\text{cl} = 40.26\ \text{dB}$ at $m_R = 0.01\ \text{1/m}$ but only 26.48
  dB at $10^{-4}$ and 6.64 dB at $10^{-6}$, against the finite 40.85 dB that
  the derived reading returns for the same bare plenum, where the leakage term
  $s_R \tau_R/h$ bounds the path; a plenum with no absorber at all is
  therefore predicted arbitrarily worse than the leak-limited value rather
  than equal to it. It also **breaks energy conservation**, returning
  $\tau_\text{cl} = 4.45$ at $R_S = R_R = 6\ \text{dB}$, $m_R = 0.01$ and
  $\tau_\text{cl} = 829$ at $R_S = R_R = 0\ \text{dB}$, $m_R = 10^{-3}$.
- **Evidence:** with $m'_R$ in the denominator every one of those pathologies
  disappears: $\tau_\text{cl}$ flattens onto the leak-limited value as the
  damping vanishes, where the printed form keeps growing, and is bounded above
  by 1 because
  $(1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R L_R) \le 1$, and
  reduces to Vigran's own small-attenuation result, Eq. (9.19)
  $\tau_\text{cl} = \varepsilon^2 \tau_S \tau_R L_R/(4h)$, whenever $m_S L_S$
  and $m'_R L_R$ are both small. With the printed $m_R$ the same limit picks
  up the factor $m'_R/m_R$, which diverges, so Eq. (9.18) as printed does not
  reduce to Eq. (9.19) at all: the two equations the book presents as a pair
  are inconsistent with each other. Verified on PDF page 361 (printed p. 339)
  of Vigran, Building Acoustics:2008, which shows the denominator carrying the
  unprimed $m_R$ while the exponent of the same expression carries the primed
  $m'_R$ of Eq. (9.17).
- **Library behaviour:** `plenum_flanking_reduction_index` in
  [`ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/prediction/ceiling_plenum.py)
  implements the derived $m'_R$ in both the exponent and the denominator, with
  the reading documented at the formula, and rejects a transmission factor
  above unity rather than reporting a negative sound reduction index. Tests
  pin the physics the model owes (monotonicity in the damping, the
  $\tau_\text{cl} \le 1$ bound, the size of the Eq. (9.17) leakage term at a
  realistic ceiling) and the one property that separates the two readings: a
  bare plenum no worse than the undamped Eq. (9.20) value
  ([`tests/building/prediction/test_ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_ceiling_plenum.py)).
- **Status:** unreported (textbook rather than a standard). Mechel's original
  1980 paper, which Vigran reproduces, was not available to check whether the
  misprint originates there.

## Real Decreto 1367/2007, Annex IV A.3.3 (Kf and Ki threshold tables)

- **Location:** Annex IV, section A.3.3, the $K_f$ (low-frequency) and $K_i$
  (impulsive) correction tables, middle row of each.
- **The print:** both tables print the 3 dB row as "Si 10 > Lf <= 15" and "Si
  10 > Li <= 15" respectively (BOE-A-2007-18397, consolidated text).
- **The problem:** the condition as printed is unsatisfiable. It reads "10
  greater than Lf" and "Lf at most 15" simultaneously, which would select
  levels below 10 dB, but the row above it already assigns those to 0 dB ("Si
  Lf <= 10") and the row below covers "Si Lf > 15". The three rows only
  partition the range under the reading $10 < L_f \le 15$, so the ">" is a
  typeset inversion of "<".
- **Evidence:** the bracketing rows leave no other consistent reading; the
  identical construction appears in both tables, and the equivalent tables in
  the autonomous-community noise regulations that transpose this Annex print
  `10 < Lf <= 15`. Verified on PDF page 26 (printed p. 26) of Real Decreto
  1367/2007, BOE-A-2007-18397 consolidated text, on which the ">" of both
  middle rows is unambiguous against the "<=" glyphs of the same cell.
- **Library behaviour:**
  [`low_frequency_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/spain.py)
  and `impulsive_correction` implement $10 < L \le 15$, with a regression test
  pinning the three branches at the 10 dB and 15 dB boundaries.
- **Status:** unreported (national regulation, not a standards body).

---

## Commission Directive (EU) 2015/996, Annex II 2.2.1 (octave-band range of the road source)

- **Location:** the Annex, point 2.2.1, second paragraph under the heading
  "Traffic flow" (OJ L 168, 1.7.2015, p. 8).
- **The print:** "these sound power levels are calculated for each octave band
  i from 125 Hz to 4 kHz".
- **The problem:** the road source model contradicts its own coefficient
  database. Every band-dependent table of Appendix F, both in the 2015 text
  and in the version replaced by (EU) 2021/1226, is printed over the eight
  octave bands **63 Hz to 8 kHz** (Table F-3 has no frequency columns at all),
  and point 2.1.1 of the same Annex defines the frequency range of the method
  as 63 Hz to 8 kHz. A calculation restricted to 125 Hz - 4 kHz would silently
  discard the 63 Hz and 8 kHz bands, which Appendix F tabulates like every
  other.
- **Evidence:** corrected by the corrigendum published in OJ L 5, 10.1.2018,
  p. 35, which reads in full: 'On page 8, in the Annex, in point 2.2.1, in the
  second paragraph under the heading "Traffic flow": for: "each octave band i
  from 125 Hz to 4 kHz", read: "each octave band i from 63 Hz to 8 kHz"'. The
  same corrigendum also adds "octave bands" to the frequency range of 2.1.1.
  Verified on PDF page 8 (printed p. L 168/8) of Commission Directive (EU)
  2015/996:2015 for the printed restriction, on PDF page 1 (printed p. L 5/35)
  of the corrigendum for both items, and on PDF page 4 (printed p. L 168/4)
  and PDF page 124 (printed p. L 168/124) of the Directive for the conformant
  range.
- **Library behaviour:**
  [`cnossos_road`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/cnossos_road.py)
  works over the corrected 63 Hz to 8 kHz grid (`ROAD_OCTAVE_BANDS`), pinned
  by `test_octave_bands_are_the_corrected_range` and by the workbook cases,
  whose published levels cover all eight bands.
- **Status:** corrected by the issuing body (corrigendum of 10 January 2018);
  recorded because the uncorrected 2015 text is still the one most often
  downloaded and quoted.

---

## Ainslie, Principles of Sonar Performance Modelling (2010), Eq. (9.57)

*Textbook, not a standard.*

- **Location:** Section 9.1.1.2.4 (printed p. 457), the transition range
  between the mode-stripping and single-mode regimes of the Weston flux model.
- **The print:** $r_\text{MS} \approx k^2 H_e^3/(9\eta)$, where $H$ is the
  water depth, $H_e$ the Weston effective depth of Eq. (9.55),
  $k = \omega/c_w$ and $\eta$ the reflection loss gradient.
- **The problem:** the sentence immediately above it prescribes the
  derivation, "estimated by equating θ_n and θ_eff with n = 3/2". The two
  angles are four printed pages apart, not on the same page as an earlier
  revision of this entry stated:
  - Eq. (9.47), $\theta_\text{eff} = (\pi H/(4\eta r))^{1/2}$, **printed p.
    453**, with the **true water depth $H$** (it comes from the multipath
    integral Eq. (9.46), whose $1/(rH)$ prefactor is the cylinder area
    $A_\text{CS} = 2\pi r H$ of Eq. (9.44), so $H$ is the depth that counts
    bottom bounces);
  - Eq. (9.56), $\theta_n \approx n\pi/(k H_e)$, **printed p. 457**, with the
    **effective depth $H_e$** (mode angles are set by the apparent
    pressure-release boundary).

  Equating them at $n = 3/2$ gives $\pi H/(4\eta r) = 9\pi^2/(4k^2H_e^2)$,
  that is **$r_\text{MS} = k^2H_e^2H/(9\pi\eta)$**. The printed form is larger
  by $\pi H_e/H$. The factor $\pi$ is unconditional: it survives even if $H_e$
  is substituted for $H$ in Eq. (9.47), which is presumably how the printed
  $H_e^3$ arose, and that reading would give $k^2H_e^3/(9\pi\eta)$, still
  $\pi$ below the print. The residual $H_e/H$ is the depth substitution
  itself, and it tends to 1 at high frequency. The other transition of the
  same section, Eq. (9.50) $r_\text{CS} = \pi H/(4\eta\psi_c^2)$, follows its
  own derivation exactly (it is where Eq. (9.42) and Eq. (9.49) cross), so the
  defect is confined to Eq. (9.57).
- **Evidence:** the symbolic re-derivation above, checked numerically for
  $H = 50\ \text{m}$, $f = 250\ \text{Hz}$, $c_w = 1500\ \text{m/s}$ over the
  Table 9.1 sand seabed ($\eta = 0.28\ \text{Np/rad}$, $\psi_c = 33.56^\circ$,
  $H_e = 53.63\ \text{m}$, $k = 1.047\ \text{m}^{-1}$):

  | | $r_\text{MS}$ | $\theta_\text{eff}$ there (Eq. 9.47) |
  |---|---|---|
  | derivation, $k^2H_e^2H/(9\pi\eta)$ | 19.9 km | 4.808° |
  | printed Eq. (9.57), $k^2H_e^3/(9\eta)$ | 67.1 km | 2.619° |

  The ratio $67.1/19.9$ is $\pi H_e/H = 3.3695$ to every digit carried. The
  angle column is an independent check that does not depend on how the
  derivation is read: the first two mode angles of Eq. (9.56) are
  $\theta_1 = 3.205^\circ$ and $\theta_2 = 6.410^\circ$, so
  $\theta_{3/2} = 4.808^\circ$. At the derived range the effective angle is
  exactly $\theta_{3/2}$, halfway between the first two modes, which is what
  the text asks for. At the printed range it has fallen to 2.619°, **below
  $\theta_1$ itself**: the second mode would have been stripped long before,
  so that range cannot be where the single-mode regime begins. Both printed
  formulae are confirmed on PDF page 483 (printed p. 453) and PDF page 487
  (printed p. 457) of Ainslie, Principles of Sonar Performance Modelling
  (2010).
- **Library behaviour:** `weston_regime_boundaries` in
  [`propagation/weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/propagation/weston_regimes.py)
  implements the derivation-consistent $k^2H_e^2H/(9\pi\eta)$, which is also
  what keeps $\theta_\text{eff}$ defined with $H$ everywhere the module
  evaluates Eq. (9.47). The equating rule is pinned by
  `test_mode_stripping_boundary_equates_theta_eff_with_mode_3_over_2`, which
  rebuilds both angles from the printed equations rather than from the
  implementation, and the shared definition of $\theta_\text{eff}$ by
  `test_composite_loss_and_the_boundary_use_the_same_effective_angle` (both in
  [`tests/underwater/propagation/test_weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/tests/underwater/propagation/test_weston_regimes.py)).
- **Status:** unreported (textbook rather than a standard).

---

## NMFS (2024) Updated Technical Guidance v3.0, Table 5 / Table ES2 (otariid C)

*Regulatory guidance document, not a standard.*

- **Location:** Table 5 (printed p. 25), repeated as Table ES2 (printed p. 3)
  and again as Table 8 (printed p. 35): the auditory weighting parameter $C$
  of the otariid pinniped in-water group (OW / OCW).
- **The print:** $C = 1.37\ \text{dB}$.
- **The problem:** the correct value is 1.36 dB. NMFS states so itself in the
  table's own footnote: "During the public comment period, an error was
  identified with the Navy's rounding, where this value should be 1.36,
  instead of 1.37. Because this is such a minor error and to remain consistent
  with the Navy, NMFS decided rely upon the value the Navy originally
  provided." The document therefore knowingly publishes the wrong digit.
- **Evidence:** independent recomputation of $C$ from its own definition, the
  negated peak of $W(f)$, with the same row's parameters $a = 1.58$, $b = 5$,
  $f_1 = 2.53\ \text{kHz}$, $f_2 = 43.8\ \text{kHz}$: $C = 1.3643\ \text{dB}$,
  which rounds to 1.36. The published weighted TTS onset of the same row
  ($179\ \text{dB} = K + C$ with $K = 178$) is unaffected by the third digit.
  The same recomputation reproduces every other row of the table to the
  printed two decimals, so the OW row is the only one that does not round from
  its own parameters. Verified on PDF page 36 (printed p. 25), PDF page 14
  (printed p. 3) and PDF page 46 (printed p. 35) of NMFS Updated Technical
  Guidance v3.0:2024, all three carrying 1.37 with the identical footnote.
- **Library behaviour:**
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py)
  implements 1.36 and keeps the printed 1.37 available as
  `WeightingParameters.c_db_as_printed`, so an assessment that must reproduce
  the published table verbatim still can. Pinned by
  `test_nmfs_2024_otariid_c_uses_the_corrected_1_36`.
- **Status:** unreported (the issuing body has already documented it).

---

## Southall et al. (2019), Aquatic Mammals 45(2), Table 7 (impulsive peak SPL)

*Peer-reviewed journal paper, not a standard.*

- **Location:** Table 7 (printed p. 156), the impulsive-noise TTS and PTS
  onset criteria; the two in-air carnivore rows PCA and OCA.
- **The print:** PCA TTS peak SPL 138 and PTS peak SPL 144; OCA TTS peak SPL
  161 and PTS peak SPL 167 $\text{dB re } 20\ \mu\text{Pa}$.
- **The problem:** all four are typographical errors. The authors' own errata
  (*Aquatic Mammals* 45(5), 569-572, DOI 10.1578/AM.45.5.2019.569) names all
  four on printed p. 569, "There are four typographical errors in Table 7 on
  page 156", and reprints the corrected table on printed p. 570: PCA 155 and
  161, OCA 170 and 176. The same errata also corrects the column headed "B" in
  Table 5 to the parameter b of Eq. (2), which it likewise calls a
  typographical error.
- **Evidence:** the errata itself, which names each wrong value and its
  replacement, corroborated by the article's own extrapolation rule. Note
  first what does *not* discriminate. The PTS peak = TTS peak + 6 dB rule of
  printed p. 155 is satisfied by the printed pair as well ($144 - 138 = 6$,
  just as $161 - 155 = 6$), so it says nothing about which pair is right. Nor
  does the duplication visible in the printed rows, where the peak-SPL TTS
  entry equals that same row's PTS-onset **SEL** entry (PCA 123 / 138 / 138 /
  144 and OCA 146 / 161 / 161 / 167, reading TTS SEL, TTS peak, PTS SEL, PTS
  peak): for these two in-air rows that equality is forced by two rules the
  article states on printed p. 155, both adding 15 dB to the same base TTS
  SEL, so it would hold whatever the SEL values were. An earlier revision of
  this entry read that equality as the signature of a column slip; it is
  instead the printed table being internally consistent with the article's own
  in-air method, which is what makes the errata the only thing that settles
  the matter.
  - **Value.** The corrected numbers are close to what the article's
    extrapolation rule produces, with the caveat that the rule is not stated
    for these rows. Printed p. 155 sets the impulsive peak-SPL TTS onset of a
    group without direct data at the hearing threshold at the frequency of
    best sensitivity $f_0$ plus 159 dB, and restricts that rule explicitly to
    the in-water groups: "For other species groups **in water** (LF, SI, PCW,
    and OCW), 159 dB was added to the value of the hearing threshold at f₀".
    It works the rule through for PCW: "Peak SPL TTS onset was estimated as
    212 dB re 1 µPa (53 dB at f₀ + 159 dB)". Evaluating the Table 2 group
    audiogram at the Table 4 $f_0$ reproduces the three in-water rows the
    errata does not touch (SI 219.6 against a published 220; PCW 212.5 against
    212; OCW 226.1 against 226), which validates the rule where the article
    applies it. Extending it to the two in-air carnivore rows, which the
    article does not do, gives PCA $-4.6\ \text{dB re } 20\ \mu\text{Pa}$ at
    2.3 kHz and OCA $11.4\ \text{dB re } 20\ \mu\text{Pa}$ at 10 kHz, hence
    **154.4** and **170.4**. Those reproduce the corrected 155 and 170 to
    within 0.6 dB and are 16 dB and 9 dB away from the printed 138 and 161,
    which is what makes them corroborating rather than confirming; note that
    154.4 rounds to 154, not to 155, and an earlier revision of this entry
    claimed that it rounded to the corrected value.
  - **A second, unrepaired inconsistency.** Printed p. 155 states that for the
    in-air carnivores specifically "a nominal 15 dB offset is used ... between
    the SEL-based TTS threshold and the peak SPL-based threshold", which
    reproduces the *printed* 138 and 161 from the SEL column. That sentence,
    not the +159 dB rule, is the one the article's own method applies to PCA
    and OCA. The errata resolves the conflict in favour of values consistent
    with the +159 dB rule, so it supersedes the sentence as well as the table;
    the sentence is left standing in the article.
  Verified on PDF page 31 (printed p. 155) and PDF page 32 (printed p. 156) of
  Southall et al. (2019), Aquatic Mammals 45(2), which carry the "in water
  (LF, SI, PCW, and OCW)" restriction, the 15 dB in-air offset in the same
  paragraph, both statements of the +6 dB rule, and the article's Table 7 with
  the PCA row 123 / 138 / 138 / 144 and the OCA row 146 / 161 / 161 / 167. The
  errata is a publication of its own, *Aquatic Mammals* 45(5), 569-572, bound
  at the end of the copy the authors distribute: verified there on PDF page
  109 (printed p. 569), which names all four values and their replacements,
  and PDF page 110 (printed p. 570), which reprints Table 7 with PCA 123 / 155
  / 138 / 161 and OCA 146 / 170 / 161 / 176.
- **Library behaviour:** the errata-corrected values are the ones implemented
  in
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py),
  pinned by `test_southall_table_7_errata_values_are_implemented`, with the
  +159 dB rule itself checked against the audiogram in
  `test_southall_impulsive_peak_spl_is_threshold_at_f0_plus_159_db` for the
  in-water groups the article restricts it to and, separately and with the
  extrapolation labelled as such, for PCA and OCA.
- **Status:** reported by the authors themselves (errata published 2019).

## Directive (EU) 2015/996, Annex II 2.3.2 (roughness conversion in km/h)

- **Location:** the "Definition" paragraph of *Wheel and rail roughness* (OJ L
  168, 1.7.2015, p. 19) and the first paragraph after formula (2.3.11) (p.
  21).
- **The print:** "it shall be converted to a frequency spectrum f = v/λ, where
  f is the centre band frequency of a given 1/3 octave band in Hz, λ is the
  wavelength in m, and **v is the train speed in km/h**", and, for impact
  noise, "using the relation λ = v/f, where f is the 1/3 octave band centre
  frequency in Hz and **v is the s-th vehicle speed of the t-th vehicle type
  in km/h**".
- **The problem:** dimensionally impossible. A frequency in hertz is a speed
  in metres per second divided by a wavelength in metres; reading the speed in
  km/h into $f = v/\lambda$ multiplies every frequency by 3,6, placing the
  whole roughness spectrum a factor 3,6 too high in frequency, which is more
  than an octave and a half.
- **Evidence:** verified on PDF page 19 (printed p. L 168/19) and PDF page 21
  (printed p. L 168/21) of Directive (EU) 2015/996. The corrigendum of OJ L 5,
  10.1.2018, p. 35 replaces "km/h" by "m/s" in both places. The flow equation
  (2.3.2) genuinely does take its speed in km/h, which is what makes the
  misprint plausible.
- **Library behaviour:** `roughness_to_frequency` converts the speed to m/s
  before dividing, as corrected, and its docstring says so. The reference
  implementation the Commission published with the source module does the
  same, and the 123 committed workbook cases would not reproduce otherwise.
- **Status:** unreported (corrected by the issuing body in 2018).

## Directive (EU) 2015/996, Appendix G, Table G-1, second table (wrong symbol)

- **Location:** Table G-1, "Coefficients Lr,TR,i and Lr,VEH,i for rail and
  wheel roughness", second table (OJ L 168, 1.7.2015, pp. 130-131).
- **The print:** the second table is headed **$L_{r,VEH,i}$**, the same symbol
  as the first.
- **The problem:** its two columns are "EN ISO 3095:2013 (Well maintained and
  very smooth)" and "Average network (Normally maintained smooth)", which are
  the rail-roughness classes E and M of digit 2 of the track descriptor in
  Table [2.3.b]. The table is the **rail** roughness $L_{r,TR,i}$, the
  quantity the table's own title announces and which is otherwise missing from
  Appendix G.
- **Evidence:** verified on PDF page 130 (printed p. L 168/130) of Directive
  (EU) 2015/996:2015, the page carrying the header of the second table. The
  corrigendum of OJ L 5, 10.1.2018 re-titles it $L_{r,TR,i}$, and Commission
  Delegated Directive (EU) 2021/1226 Annex point (20)(a) reprints it under
  that symbol when it replaces it, verified on PDF page 35 (printed p. L
  269/99) of that Directive.
- **Library behaviour:** `rail_roughness` returns the second table of G-1 as
  the rail roughness of (2.3.7) and `wheel_roughness` returns the first as the
  wheel roughness, which is the only assignment under which the classes of
  Table [2.3.b] can be reached at all.
- **Status:** unreported (corrected by the issuing body in 2018).

## Directive (EU) 2015/996, Appendix G, Table G-5, 6 350 Hz row (50 dB notch)

- **Location:** Table G-5, "Coefficients LW,0,idling for traction noise", the
  6 350 Hz row of the "Diesel locomotive (c. 2 200 kW)" pair (OJ L 168,
  1.7.2015, p. 138).
- **The print:** Source A **31,4** dB and Source B **30,7** dB.
- **The problem:** both are about 50 dB below their own neighbours in the same
  column: 90,5 / 89,5 dB at 5 000 Hz and 81,2 / 80,6 dB at 8 000 Hz. No
  physical traction source has a 50 dB notch one third of an octave wide, and
  no other column of the table has anything comparable. The leading digit 8
  was lost.
- **Evidence:** verified on PDF page 138 (printed p. L 168/138) of Directive
  (EU) 2015/996:2015, which carries the 5 000, 6 350 and 8 000 Hz rows and the
  "Diesel locomotive (c. 2 200 kW)" column header. Commission Delegated
  Directive (EU) 2021/1226 Annex point (20)(f), verified on PDF page 39
  (printed p. L 269/103) of that Directive, replaces the 4th column, 25th row
  by "81,4" and the 5th column, 25th row by "80,7", restoring the monotone
  roll-off. The same two values appear as 31,41 and 30,71 in the IMAGINE
  catalogue file the Commission distributes with its reference source module,
  so the error predates the Directive.
- **Library behaviour:** ships the corrected 81,4 / 80,7 and pins them,
  together with the assertion that neither value is more than 10 dB from
  either neighbour, in `test_table_g5_carries_the_2021_correction_at_6300_hz`.
- **Status:** unreported (corrected by the issuing body in 2021).

## Directive (EU) 2015/996, Appendix G, band and wavelength labels

- **Location:** the frequency column of Tables G-3, G-5 and G-6 and the
  wavelength column of Table G-1 (OJ L 168, 1.7.2015, pp. 129-140).
- **The print:** the 1/3-octave band centres are labelled **316 Hz**, **3 160
  Hz** and **6 350 Hz**, and the wavelengths **120 mm**, **12 mm**, **3,2 mm**
  and **1,2 mm**.
- **The problem:** neither series is the preferred one. The nominal 1/3-octave
  centres of IEC 61260-1 are 315, 3 150 and 6 300 Hz, and the R10 preferred
  numbers around those wavelengths are 125, 12,5, 3,15 and 1,25 mm. The
  Commission's own catalogue files, distributed with the reference source
  module, use the preferred wavelength series throughout.
- **Evidence:** verified on PDF pages 129, 130, 131, 133, 134, 135, 137 and
  138 (printed pp. L 168/129 to L 168/138) of Directive (EU) 2015/996:2015,
  which carry every occurrence of the four wavelengths and of the three band
  labels. Commission Delegated Directive (EU) 2021/1226 Annex point (20)(c)
  replaces the $L_{H,TR,i}$ section of Table G-3 outright and points (20)(d),
  (f) and (g) replace the three frequency labels in the remaining sections and
  in Tables G-5 and G-6; the tables it replaces outright carry the preferred
  wavelengths. But point (20)(a) replaces only "the second table" of Table
  G-1, so the wavelength labels 120, 12, 3,2 and 1,2 mm still stand on the
  **first** table of G-1, the wheel roughness $L_{r,VEH,i}$, which is the one
  table that keeps them.
- **Library behaviour:** the frequency grid is the IEC 61260-1 one throughout.
  The wavelength grids are kept as printed, one per table, and each roughness
  spectrum is resampled on its own grid rather than forced onto a common one,
  which is what `_WAVELENGTHS_WHEEL` and `_WAVELENGTHS_STANDARD` are for; the
  difference between the two is pinned by
  `test_wheel_roughness_keeps_the_non_standard_wavelength_grid`.
- **Status:** unreported (frequency labels corrected by the issuing body in
  2021; the wheel-roughness wavelength labels stand).

## Directive (EU) 2015/996, Annex II 2.3.2, curve squeal (unassigned endpoints)

- **Location:** the *Squeal* paragraph (OJ L 168, 1.7.2015, p. 21).
- **The print:** "The emission level to be used is determined for curves with
  radius below **or equal to** 500 m and for sharper curves and branch-outs of
  points with radii below 300 m", and then "squeal noise shall be considered
  by adding 8 dB for **R < 300 m** and 5 dB for **300 m < R < 500 m**".
- **The problem:** the two open intervals leave $R = 300\ \text{m}$ and
  $R = 500\ \text{m}$ with no excess at all, and $R = 500\ \text{m}$ is
  explicitly inside the scope the same paragraph has just set. A 500 m curve
  therefore falls out of a rule written to include it.
- **Evidence:** verified on PDF page 21 (printed p. L 168/21) of Directive
  (EU) 2015/996:2015, on which both inequalities of the rule sentence are
  strict while the scope sentence above them reads "below or equal to 500 m".
  Commission Delegated Directive (EU) 2021/1226 Annex point (4)(b), verified
  on PDF page 4 (printed p. L 269/68) of that Directive, replaces the
  paragraph with a table whose intervals are closed, "R <= 300 m" and "300 m <
  R <= 500 m".
- **Library behaviour:** `curve_squeal_excess` implements the 2021 table, so
  $R = 300\ \text{m}$ returns 8 dB and $R = 500\ \text{m}$ returns 5 dB; the
  boundaries are pinned in `test_curve_squeal_rule_of_2021`.
- **Status:** unreported (corrected by the issuing body in 2021).

---

## Allard & Atalla, Propagation of Sound in Porous Media 2e (2009), Eq. (6.85)

*Textbook, not a standard.*

- **Location:** Sect. 6.5.2 (printed p. 123), the second form of the
  shear-wave velocity ratio $\mu_3$.
- **The print:**
  $\mu_3 = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{22})$, offered as
  an alternative to Eq. (6.84), $\mu_3 = -\rho_{12}/\rho_{22}$.
- **The problem:** the two printed forms are not equal. Substituting the shear
  wavenumber of Eq. (6.83),
  $\delta_3^2 = (\omega^2/N)(\rho_{11}\rho_{22} - \rho_{12}^2)/\rho_{22}$,
  into the printed Eq. (6.85) gives $-\rho_{12}^2/\rho_{22}^2$, which is Eq.
  (6.84) multiplied by the spurious factor $\rho_{12}/\rho_{22}$. The
  denominator should read $\omega^2\rho_{12}$.
- **Evidence:** the book's own derivation. Eq. (6.80), printed p. 122, is
  $-\omega^2\rho_{11}\psi_s - \omega^2\rho_{12}\psi_f = N\nabla^2\psi_s = -N\delta_3^2\psi_s$,
  so $(N\delta_3^2 - \omega^2\rho_{11})\psi_s = \omega^2\rho_{12}\psi_f$ and
  therefore
  $\mu_3 = \psi_f/\psi_s = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{12})$.
  With that reading the two forms agree identically wherever $\rho_{12}$ is
  non-zero; at $\rho_{12} = 0$ the corrected quotient is $0/0$ while Eq.
  (6.84) stays defined and gives $\mu_3 = -\rho_{12}/\rho_{22} = 0$, which is
  the value to use there. The printed form instead differs from Eq. (6.84) by
  the factor $\rho_{12}/\rho_{22}$, so it coincides with it only where that
  ratio is exactly 0 or exactly 1. With
  $\rho_{12}/\rho_{22} = \rho_0/(\phi\rho_\text{eq}) - 1$ those two cases ask
  for $\rho_\text{eq} = \rho_0/\phi$ and $\rho_\text{eq} = \rho_0/(2\phi)$,
  both real; the effective density of a lossy porous medium is complex, so
  neither is ever met. Verified on PDF page 132 (printed p. 123) of Allard &
  Atalla, Propagation of Sound in Porous Media 2e:2009, which carries both
  printed forms, and on the facing page for Eq. (6.80).
- **Library behaviour:** `biot_waves` implements Eq. (6.84) as printed, and
  `test_shear_velocity_ratio_matches_the_corrected_second_printed_form` checks
  it against the corrected Eq. (6.85) over four decades of frequency, and also
  asserts that the form exactly as printed disagrees.
- **Status:** unreported.

---

## Allard & Atalla 2e (2009), Eq. (11.48) and Table 11.1 (poroelastic layer)

*Textbook, not a standard.*

- **Location:** Sect. 11.3.3 (printed pp. 251-252), the fluid normal stress
  $\sigma_{33}^f$ of a poroelastic layer and the matrix $[\Gamma]$ it feeds.
- **The print:** Eq. (11.48) reads

  $$
  \sigma_{33}^f = \sum_i (Q + R\mu_i)(k_t^2 + k_{i3}^2)
  \left\{ -(A_i - A'_i)\cos(k_{i3}x_3) + j(A_i - A'_i)\sin(k_{33}x_3) \right\}
  $$

  and Table 11.1 writes $k_{i3}$ in the two columns that carry $\mu_1$, $D_1$
  and $E_1$.
- **The problem:** two independent misprints in the same equation, plus a
  subscript slip in the table.
  - The coefficient of the *symmetric* amplitude $(A_i + A'_i)$ is missing:
    Eq. (11.48) attaches both terms to $(A_i - A'_i)$, which would leave the
    first and third columns of $[\Gamma]$ with no $\sigma_{33}^f$ entry at
    all, contradicting Table 11.1, whose row 6 prints $-E_1 \cos(k_{13}x_3)$
    and $-E_2 \cos(k_{23}x_3)$ in exactly those columns. The first term is
    $-(A_i + A'_i)\cos(k_{i3} x_3)$.
  - The sine carries $k_{33}$, the *shear* wave-number component, inside a sum
    over the two compressional waves $i = 1, 2$. It must be $k_{i3}$. Table
    11.1 again gives the intended reading: its row 6 has
    $j E_1 \sin(k_{13}x_3)$ and $j E_2 \sin(k_{23}x_3)$, and zero in both
    shear columns, because a shear wave produces no dilatation and therefore
    no $\sigma_{33}^f$.
  - Table 11.1 prints the running subscript $k_{i3}$ in its first two columns,
    which belong to the first compressional wave alone: the $\mu_1$, $D_1$ and
    $E_1$ in the same columns make $k_{13}$ the only consistent reading.
- **Evidence:** the two readings above are forced by Table 11.1, which the
  same page declares to be the tabulation of Eqs. (11.37), (11.38) and
  (11.46)-(11.48). They are also what the stress-strain relation Eq. (11.41),
  $\sigma_{33}^f = R\,\mathrm{div}\,u_f + Q\,\mathrm{div}\,u_s$, gives when
  the displacement potentials of Eqs. (11.22)-(11.25) are differentiated
  directly. Verified on PDF page 257 (printed p. 251) and PDF page 258
  (printed p. 252) of Allard & Atalla, Propagation of Sound in Porous Media
  2e:2009, which carry Eq. (11.48) and the two Table 11.1 columns as printed.
- **Library behaviour:** the $[\Gamma]$ of Table 11.1 is implemented with the
  corrected readings, and
  `test_gamma_matches_the_field_rebuilt_from_the_potentials` checks all
  thirty-six of its entries at three frequencies, three depths and three
  angles of incidence against the field rebuilt from Eqs. (11.22)-(11.28)
  without going through the table.
- **Status:** unreported.

---

## Allard & Atalla 2e (2009), Sect. 6.6.3 (thickness of the second sample)

*Textbook, not a standard.*

- **Location:** Sect. 6.6.3, printed p. 129, the two glass-wool samples whose
  measured and predicted surface impedances are Figures 6.10 and 6.11.
- **The print:** the first sentence says the impedances are shown "for l = 10
  cm and l = 5.4 cm"; two sentences later the peak of the second sample is
  placed at "860 Hz for l = 5.6 cm", and the caption of Figure 6.11 says "l =
  5.6 cm".
- **The problem:** the two thicknesses cannot both be right.
- **Evidence:** textual, and only textual. Two printed statements carry 5.6
  cm, the sentence about the 860 Hz peak and the independent caption of Figure
  6.11, against one carrying 5.4 cm; a single slip in the opening sentence is
  the shorter explanation than the same slip made twice. The numbers do
  **not** settle it, and this entry does not claim they do. The book gives no
  peak-finding rule, and the answer follows the rule chosen:
  - Taking the peak as the maximum of $\text{Im}(Z_s)$, Eq. (6.107) on the
    fully specified Table 6.1 glass wool gives 863.5 Hz for 5.6 cm (+0.4 %
    against the printed 860) and 896.2 Hz for 5.4 cm (+4.2 %), which favours
    5.6 cm. But the same rule puts the undisputed 10 cm sample at 480.0 Hz
    against its printed 470, a +2.1 % bias of the same size as the effect
    being resolved.
  - Taking the peak as the maximum of $|Z_s - Z_{s,\text{rigid}}|$, which is
    the departure the same paragraph describes ("close to each other, except
    around the peaks which are not predicted by the one-wave model"), the 10
    cm sample lands at 469.2 Hz (-0.2 %) and **both** printed frequencies then
    come out of the pair (10 cm, 5.4 cm): 861.2 Hz for 5.4 cm (+0.1 %) against
    831.0 Hz for 5.6 cm (-3.4 %). That rule favours 5.4 cm.
  - Scaling the 10 cm peak is no help either, and leans the other way from the
    conclusion: $470 \times (10/5.4) = 870\ \text{Hz}$ is 10 Hz from the
    published 860, $470 \times (10/5.6) = 839\ \text{Hz}$ is 21 Hz from it.
  - The agreement of "860 Hz" with "5.6 cm" is in any case partly circular,
    since both sit in the same clause: it tests that sentence against itself,
    not which of the two sentences is the misprint.
  Verified on PDF page 138 (printed p. 129) of Allard & Atalla, Propagation of
  Sound in Porous Media 2e:2009, on which the lone 5.4 cm and the 5.6 cm of
  the 860 Hz clause sit on the same page, and on PDF page 139 (printed p. 130)
  of the same edition for the Figure 6.11 caption, the second sentence
  carrying 5.6 cm.
- **Library behaviour:** recorded, with no effect on the implementation.
  `test_impedance_peak_of_the_thin_layer_resolves_the_printed_thickness` pins
  the 5.6 cm peak against the published 860 Hz under the $\text{Im}(Z_s)$ rule
  and checks that the 5.4 cm reading is the worse of the two under that rule.
- **Status:** unreported, and the weakest of the four entries here: the
  conclusion rests on the two-against-one reading of the printed page, not on
  a computation.

---

## Allard & Atalla 2e (2009), Sect. 6.5.4 (the frame-borne velocity ratio)

*Textbook, not a standard.*

- **Location:** Sect. 6.5.4, printed p. 125, the one sentence of the book that
  quotes computed values of $\mu_b$ for the Table 6.1 glass wool.
- **The print:** "The ratio modulus $|\mu_b|$ of the velocities of the frame
  and the air for the frame-borne wave decreases from 1.0 at 50 Hz to 0.82 at
  1500 Hz."
- **The problem:** the two quoted values are the *real part* of $\mu_b$, not
  its modulus. $\mu_b$ is complex, and the sentence names the modulus
  explicitly.
- **Evidence:** on the fully specified Table 6.1 material the model gives
  $\mu_b(1500\ \text{Hz}) = 0.811 + 0.473j$. Its real part is **0.811**, 1.1 %
  from the printed 0.82; its modulus is **0.939**, 14.5 % away. Read as the
  real part, the sentence is right at both ends and describes a monotone
  decrease: $\text{Re}(\mu_b)$ is 1.002 at 50 Hz and passes through 0.82 at
  1467 Hz, 2.2 % from the printed 1500 Hz. Read as the modulus it is right at
  neither: $|\mu_b|$ is 1.002 at 50 Hz but *rises* to 1.008 by 400 Hz before
  turning over, and only reaches 0.82 at 2634 Hz, 76 % above the printed
  frequency. No admissible reading of the printed inputs closes that gap. With
  the loss factor at 0 or at 0.2, the viscous length halved or doubled,
  $\Lambda' = 2\Lambda$ in place of the printed $1.1 \cdot 10^{-4}\ \text{m}$,
  the resistivity halved or doubled, the tortuosity at 1 or the Poisson
  coefficient at 0.3, $|\mu_b(1500)|$ moves only between 0.874 and 1.073. The
  closest of the eight, 0.874 at zero loss factor, is still 6.6 % from the
  printed 0.82, and it loses the 495 Hz branch crossing of the same section
  altogether; the only variant that keeps that crossing
  ($\Lambda' = 2\Lambda$, 495.2 Hz) leaves $|\mu_b|$ at 0.937. Reading the
  sentence as $\text{Re}(\mu_b)$ needs no variant at all. Verified on PDF page
  134 (printed p. 125) of Allard & Atalla, Propagation of Sound in Porous
  Media 2e:2009, which carries the sentence and its 0.82.
- **Library behaviour:** `biot_waves` computes $\mu_b$ from Eq. (6.71) as
  printed. The conformance row and
  `test_frame_borne_velocity_ratio_matches_the_two_published_values` are
  written against $\text{Re}(\mu_b)$, and say so.
- **Status:** unreported.

---

## Allard & Atalla 2e (2009), Table 11.7 (the figure its caption names)

*Textbook, not a standard.*

- **Location:** Table 11.7, PDF page 280, printed p. 274, the parameter table
  of the carpet, screen and fibrous layer of Sect. 11.7.2.
- **The print:** the caption reads "The parameters used to predict the surface
  impedance of the material represented in Figure 11.6".
- **The problem:** Figure 11.6 is on printed p. 266 and is the plastic foam
  under a sheet of glass wool, whose parameters are Table 11.3. The structure
  Table 11.7 tabulates, a carpet in two layers over an impervious screen over
  a fibrous layer, is Figure 11.16, printed on the same page as the table.
- **Evidence:** the prose beside Figure 11.16 says the material parameters are
  given in Table 11.7, and the four row names of the table are the four layers
  Figure 11.16 labels. Verified on PDF page 280 (printed p. 274) and PDF page
  272 (printed p. 266) of Allard & Atalla, Propagation of Sound in Porous
  Media 2e:2009.
- **Library behaviour:** the three porous rows are transcribed as printed and
  the data file's `about` names Figure 11.16 as the structure, with the
  caption's own wording quoted.
- **Status:** unreported.

---

## Allard & Atalla 2e (2009), Table 11.8 (the thickness of the glass wool)

*Textbook, not a standard.*

- **Location:** Table 11.8, PDF page 281, printed p. 275, the glass wool
  bonded onto an aluminium plate for the normal-incidence transmission example
  of Sect. 11.7.3.
- **The print:** the table gives the glass wool a thickness of 3,8 mm; the
  prose of Sect. 11.7.3 on the facing folio says "A layer of the glass wool
  studied in Section 6.5.4, of thickness 5 cm, is bonded on to a plate of
  aluminium, of thickness 1 mm".
- **The problem:** the two thicknesses differ by more than an order of
  magnitude and cannot both describe the layer of Figure 11.18.
- **Evidence:** the plate agrees between the two, 1 mm in both, which is what
  makes the glass wool the disagreeing cell rather than a column read out of
  order. Verified on PDF page 281 (printed p. 275) for the table and PDF page
  280 (printed p. 274) for the sentence, in Allard & Atalla, Propagation of
  Sound in Porous Media 2e:2009.
- **Library behaviour:** the row carries the printed 3,8 mm, and its `note`
  records the sentence. Nothing computes with the thickness: the equivalent
  fluid of this specimen does not use it.
- **Status:** unreported.

---

## Allard & Atalla 2e (2009), Table 11.9 (the thickness of the plate)

*Textbook, not a standard.*

- **Location:** Table 11.9, PDF page 282, printed p. 276, the foam and plate
  of the diffuse-field transmission example of Sect. 11.7.4.
- **The print:** the plate row gives a thickness of 1,6 mm; the prose of
  Sect. 11.7.4 on the facing folio says "The material is a foam of thickness
  h = 2 . 54 cm bonded onto a 0.6 mm aluminium plate".
- **The problem:** 1,6 against 0,6 mm for the same plate.
- **Evidence:** the foam agrees between the two, the table's 25,4 mm being the
  sentence's 2,54 cm, which places the disagreement in the plate row alone.
  Verified on PDF page 282 (printed p. 276) for the table and PDF page 281
  (printed p. 275) for the sentence, in Allard & Atalla, Propagation of Sound
  in Porous Media 2e:2009.
- **Library behaviour:** the plate is not a porous material and is not in the
  catalogue; the foam row's `note` records the disagreement so that a reader
  reproducing the figure knows which plate the curve assumes.
- **Status:** unreported.

---

## Allard & Atalla 2e (2009), Table 13.2 (the Young's modulus of the rockwool)

*Textbook, not a standard.*

- **Location:** Table 13.2, PDF page 341, printed p. 337, the 5,75 cm rockwool
  with a central perforation of the double-porosity example.
- **The print:** the column headed E (Pa) carries 4400 for a frame of
  130 kg/m3.
- **The problem:** a frame modulus of 4,4 kPa at that density gives a frame
  wave speed of $\sqrt{4400/130} = 5,8$ m/s, so the quarter-wave resonance of
  a 5,75 cm layer lands near 25 Hz. The text on the next page says the
  numerical model captures "the skeleton resonance occurring around 1350 Hz",
  which the printed modulus cannot produce: 1350 Hz would need about 12,7 MPa,
  three orders of magnitude above the cell.
- **Evidence:** arithmetic on the page's own two cells against the page's own
  sentence. Nothing on the page says what the modulus should be, so this entry
  reports the inconsistency and does not repair it. Verified on PDF page 341
  (printed p. 337) for the table and PDF page 342 (printed p. 338) for the
  sentence, in Allard & Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Library behaviour:** the row carries the printed 4400 Pa and its `note`
  records the resonance the text reports. No example of this library computes
  a skeleton resonance from it.
- **Status:** unreported.

---

## ECAC Doc 29, 5th ed., Volume 2, Appendix B, Eq. (B-41) (descent deceleration)

- **Location:** Appendix B, section B7.1.1, the deceleration $a$ defined under
  Eq. (B-41), on the page that carries Eq. (B-40) and Eq. (B-41).
- **The print:**
  $a = k^2 \left(\left(\left(\mathrm{Pt1(NextSeg)}_{TAS} - w\right)/\cos\gamma\right)^2 - \left(\left(\mathrm{Point1}_{TAS} - w\right)/\cos\gamma\right)^2\right) / \left(2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma\right)$,
  that is both ground speeds divided by $\cos\gamma$ over twice the slant
  length of the segment.
- **The problem:** the descent slope is counted twice. The mean deceleration
  along the flight path is the change in the square of the along-path speed
  over twice the path length; the printed expression converts the speeds to
  along-path values *and* uses a path length that is already the slant one, so
  it overstates $|a|$ by $1/\cos^2\gamma$. The 4th edition's Eq. (B-21) is
  self-consistent, and the denominator is not what changed: it reads
  $2 \cdot \Delta s/\cos\gamma$ with $\Delta s$ "the ground distance covered",
  which is the same slant length the 5th edition writes as
  $2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma$.
  What changed is the numerator. The 4th edition's Eq. (B-22) defines the
  speeds it divides as *groundspeeds*, $V = V_C\cos\gamma/\sqrt{\sigma} - w$,
  that is the true airspeed resolved into the horizontal plane, so dividing
  each by $\cos\gamma$ correctly restores an along-path speed. The 5th edition
  feeds Eq. (B-41) the profile points' own $\mathrm{TAS}$, which is along-path
  already, and kept the division. Doc 29's own reference results decide it: of
  the twelve points of Volume 3 Part 2 case 2D, flown entirely at that step
  type, nine are reached by the deceleration. The plain ground speeds reproduce
  the tabulated thrust at every one of the twelve, worst deviation 0.047 lb,
  while the printed divided speeds fall short at all nine, by 6.05, 5.47, 4.02,
  3.81, 4.56, 4.45, 0.29, 6.35 and 6.41 lb in profile order: always low, and
  never within the workbook's own 0.05 lb of printed precision. The drag term
  beside it does keep the $\cos\gamma$ the same equation prints, which the same
  points confirm to the same 0.05 lb.
- **Evidence:** reproduction of Volume 3 Part 2 sheet `D1-(Arrival_Results)`
  case 2D under each reading. Verified on PDF page 104 (printed p. B-31) of
  ECAC.CEAC Doc 29, 5th ed., Volume 2: Technical guide, which carries
  Eq. (B-40), Eq. (B-41) and the deceleration under it, and on PDF page 90
  (printed p. B-15) of ECAC.CEAC Doc 29, 4th edition, Volume 2, which carries
  Eq. (B-21) and, immediately under it, the Eq. (B-22) that defines its $V_1$
  and $V_2$ as groundspeeds and so decides the reading.
- **Library behaviour:** `flight_performance` computes the deceleration from
  the plain ground speeds over the slant length, and the helper's docstring
  carries the departure and the numbers above.
  `test_arrival_case_reproduces_every_profile_point` pins all 124 arrival
  points, and the conformance row *ECAC Doc 29 Appendix B approach thrust*
  pins the descent thrust of case 2A.
- **Status:** unreported.

## ECAC Doc 29, 5th ed., Volume 2, Appendix B, Eq. (B-18) (runway gradient)

- **Location:** Appendix B, section B6.1.1, the average acceleration $a$
  defined under Eq. (B-18).
- **The print:** "$a$ is the average acceleration (ft/s$^2$) along the runway,
  equal to: $a = \left(V_C/\sqrt{\sigma}\right)^2/\left(2 \cdot s_{TOw}\right)$",
  with "$V_C$ is the Calibrated Airspeed (**kt**) at *Point2*" and $s_{TOw}$ in
  feet on the same page.
- **The problem:** the expression is declared in ft/s$^2$ and evaluates in
  kt$^2$/ft. The missing factor is $k^2 = 1.68781^2 = 2.8487$, the square of
  the knots-to-feet-per-second constant Doc 29 fixes in B2.2 and carries
  explicitly in Eq. (B-24) and Eq. (B-41), which build accelerations out of the
  same kind of expression. It is not cosmetic: $a$ enters only through
  $a/(a - g\,G_R)$, so understating it by 2.85 overstates the gradient
  correction, and at a 1 % upslope with $V_{CTO} = 162.65$ kt and
  $s_{TOw} = 4900$ ft the dimensionally correct 7.69 ft/s$^2$ gives a factor of
  1.0437 against the literal reading's 1.1353: 8.8 % of take-off distance. The
  4th edition carries the same omission, so it is inherited rather than
  introduced, and prints $\left(V_C\sqrt{\sigma}\right)^2$ where the 5th prints
  $\left(V_C/\sqrt{\sigma}\right)^2$; only the 5th edition's placement is a
  speed the aeroplane has, since $V_C/\sqrt{\sigma}$ is the true airspeed of
  Eq. (B-7).
- **Evidence:** dimensional analysis against the same document's Eq. (B-24)
  and Eq. (B-41). Verified on PDF page 90 (printed p. B-17) of ECAC.CEAC
  Doc 29, 5th ed., Volume 2: Technical guide, and, for the inherited half, on
  PDF page 86 (printed p. B-11) of ECAC.CEAC Doc 29, 4th edition, Volume 2,
  where the same definition sits under Eq. (B-11) and reads
  $\left(V_C\cdot\sqrt{\sigma}\right)^2/\left(2\cdot s_{TOw}\right)$, ft/s$^2$.
  This one cannot be
  arbitrated against the reference results: Volume 3 Part 2's departure case
  sheet `C8-(Departure_Cases)` has no runway-gradient column, so all 17
  reference cases are flown at $G_R = 0$, where Eq. (B-18) is the identity.
- **Library behaviour:** `flight_performance` restores $k^2$ and takes the 5th
  edition's $\sqrt{\sigma}$ placement; the helper's docstring states both
  departures and that no reference case can detect either.
- **Status:** unreported.

## ECAC Doc 29, 5th ed., Volume 2, Appendix B, Eq. (B-21) (mid-step airspeed)

- **Location:** Appendix B, section B6.1.2, the mid-step corrected net thrust
  $\overline{CNT}$ defined under Eq. (B-21), in the branch that computes it from
  Eq. (B-12), that is for every aeroplane the propeller coefficient table
  carries. B4.1 and B4.2 split the turboprops between them without stating a
  rule, so this is not the same set as "the turboprops": of the 20 in ANP v2.3,
  11 sit in the propeller table and reach Eq. (B-12), the other 9 sit in the jet
  table and reach Eq. (B-9), and the 8 piston aeroplanes are all in the
  propeller table.
- **The print:** $\overline{CNT}$ "is the Corrected Net Thrust of the aircraft
  when being located at mid-step, i.e. at the altitude
  $Alt = E_{Apt} + \left(\mathrm{Point\ 1\_Height} + \mathrm{Point\ 2\_Height}\right)/2$",
  and then, under "In the case of Eq. B-12,",
  $V_T = \sqrt{0.5\left(\left(\mathrm{Point\ 2\_TAS}\right)^2 + \left(\mathrm{Point\ 1\_TAS}\right)^2\right)}$,
  the root mean square of the two endpoint true airspeeds.
- **The problem:** the speed contradicts the altitude named one line above it. A
  Climb step is flown at a held calibrated airspeed, so the true airspeed at the
  mid-step altitude is fixed and is $V_C/\sqrt{\sigma}$ evaluated at the
  mid-step $\sigma$ (Eq. B-7); the root mean square of the two endpoint values
  is a different number. The two branches of the same list therefore describe
  two different aeroplanes at the one point they both call mid-step: the jet
  branch prints
  $V_C = \mathrm{Point\ 2\_TAS} \cdot \sqrt{\sigma_{Point\ 2}}$, which is
  the step's own held calibrated airspeed and so places the aeroplane at
  $V_C/\sqrt{\sigma}$ halfway up, while the Eq. (B-12) branch places it at the
  root mean square of the ends. The mean also reads as transplanted. Section
  B6.1.3, for the Accelerate step, is built on exactly this root mean square
  and is self-consistent about it, giving *both* branches the same
  $\overline{V_T} = \sqrt{\left(V_{T2}^2 + V_{T1}^2\right)/2}$ and converting
  it for the jet form with the mid-step $\sqrt{\sigma_{Alt}}$; B6.1.2 keeps the
  Eq. (B-12) line but replaces the jet line with a Point 2 quantity, and only
  one of the two survives the substitution. Of the candidates the printed one
  is the largest: at constant $V_C$ the true airspeed rises convexly with
  altitude, so the root mean square exceeds the arithmetic mean, which exceeds
  the mid-altitude value. Eq. (B-12) makes thrust inversely proportional to
  $V_T$, so the printed speed understates the mid-step thrust, understates
  $\sin\gamma$ and lays the climb down long.
- **Evidence:** reproduction of Volume 3 Part 2 sheet `D2-(Departure_Results)`
  under each reading. The four turboprop departure cases are the only reference
  data that reach this branch, and they are unanimous. On case 56 the final
  profile point is printed at 400814.3 ft: the mid-step altitude reading lands
  it 0.001 ft away, the arithmetic mean 323.944 ft long and the printed root
  mean square 544.944 ft long, against the 0.15 ft the departure distances are
  otherwise matched to. Cases 8, 28 and 68 put the same final point 172.333,
  223.003 and 544.944 ft long under the printed reading and 102.535, 132.673
  and 323.944 ft long under the arithmetic mean, always long and never near the
  printed precision; the mid-step altitude reading is within 0.049 ft of every
  point of all four cases, worst case 28. The departure grows with the height
  of the step, as a convexity error must: on case 8 the printed reading puts
  $V_T$ 0.0225 kt above the mid-step value on the 1500 ft climb and 0.1066 kt
  above it on the 2500 ft one. Verified on PDF page 92 (printed p. B-19) of
  ECAC.CEAC Doc 29, 5th ed., Volume 2: Technical guide, which carries the
  mid-step altitude sentence, the jet branch's $V_C$ and the Eq. (B-12)
  branch's $V_T$ on the one page, and on PDF page 95 (printed p. B-22) of the
  same document for the B6.1.3 pair the Eq. (B-21) line appears to be drawn
  from.
- **Library behaviour:** `flight_performance` evaluates the propeller form at
  the true airspeed the aeroplane has at the mid-step altitude, and the
  Climb-step helper's comment quotes the printed expression, says the model
  departs from it and points here.
  `test_departure_case_reproduces_every_profile_point` pins all 190 departure
  points, four cases of which are flown on Eq. (B-12).
- **Status:** unreported. Of the three Appendix B departures recorded here this
  is the one the reference results decide most sharply, and the only one that
  changes a shipped profile.

## ANSI S1.4-1983, Table V, 20 Hz type 2 cell (a plus sign that lost its bar)

- **Location:** clause 5.2, Table V "Tolerance limits on relative response
  levels for sound at random incidence measured on an instrument's calibration
  range", 20 Hz row, type 2 column (printed p. 6).
- **The print:** the cell reads "**+ 3**", with no second term. Its column
  neighbours at 10, 12.5 and 16 Hz read "+ 5, − ∞", and the type 0 and type 1
  cells of its own row read "± 2" and "± 2.5".
- **The problem:** the table has one notation for an upper-only limit, a pair
  "+ n, − ∞", and it is used three rows above this cell in the same column.
  This cell uses neither that notation nor the "± n" of its row, so it is
  either a limit written in a form the table uses nowhere else or a "±" whose
  bar failed to print. IEC 651:1979 Table V, of which this table is the US
  counterpart and with which the type 2 column agrees at all thirty-three
  other rows, prints "**±3**" at exactly this cell. The intended reading is
  ±3 dB.
- **Evidence:** the cell and its column neighbours, read on PDF page 16
  (printed p. 6) of ANSI S1.4-1983, against the same cell on PDF page 10
  (printed p. 8, marked "[IEC page 19]") of BS 5969:1981, the identical
  British adoption of IEC 651:1979.
- **Library behaviour:** `_ANSI_S14_TABLE5_12` in
  [`weighting_compliance.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/weighting_compliance.py)
  and its `reference_data` twin carry −3 dB as the 20 Hz type 2 lower limit,
  the stricter of the two readings, with the note beside them.
  `test_b_masks_match_reference_data` pins the two transcriptions to each
  other. No shipped verdict moves: the realized B weighting sits 0,05 dB below
  nominal at 20 Hz and clears either reading.
- **Status:** unreported.


---

## ISO 3747:2010, E.4.2.6.2 (the sign of the direct-field level)

- **Location:** Annex E (informative), E.4.2.6.2 "Excess sound pressure,
  measurement distance effect, $\delta_r$", the sentence giving the directly
  radiated pressure and the two sentences that build on it.
- **The print:** "the directly radiated pressure is approximately
  $L_{p,\mathrm{direct}} = L_W + 10 \lg(2\pi r^2/r_0^2)$ dB. Rearranging
  Equation (A.1) using $L_{p,\mathrm{direct}}$, gives
  $L_{p(\mathrm{RSS}),r} = L_{p,\mathrm{direct}} + \Delta L_f - 3$ dB", and the
  sensitivity coefficient that follows,
  $c_r = 10^{-0{,}1(\Delta L_f - 3\ \mathrm{dB})}\,8{,}7/r$.
- **The problem:** the direct field of a source over a reflecting plane falls
  with distance, $L_{p,\mathrm{direct}} = L_W - 10 \lg(2\pi r^2/r_0^2)$ dB; the
  printed plus sign makes it grow. The two sentences that follow hold only
  with the minus sign. Substituting
  $L_{p,\mathrm{direct}} = L_W - 20 \lg(r/r_0) - 8$ dB into Eq. (A.1)
  rearranged, $L_{p(\mathrm{RSS}),r} = L_{W(\mathrm{RSS})} + \Delta L_f - 11 -
  20 \lg(r/r_0)$ dB, gives the printed $L_{p,\mathrm{direct}} + \Delta L_f - 3$
  dB, whereas the plus sign gives
  $L_{p,\mathrm{direct}} + \Delta L_f - 19\ \mathrm{dB} - 40 \lg(r/r_0)$; and
  the $8{,}7/r$ of the sensitivity coefficient is $20/(r \ln 10)$, the
  derivative of $-20 \lg r$, so the printed $c_r$ is the derivative of the
  minus-sign form. A sign misprint in an informative annex.
- **Evidence:** the three consecutive sentences of E.4.2.6.2 read against each
  other and against Eq. (A.1). Verified on PDF page 47 (printed p. 38) and PDF
  page 30 (printed p. 21) of BS EN ISO 3747:2010.
- **Library behaviour:** the Annex E uncertainty budget is not modelled; the
  library evaluates Eq. (A.1) as printed
  ([`excess_sound_pressure_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py)),
  which the misprint does not touch. No number changes.
- **Status:** unreported.

## ISO 3747:2010, E.4.2.5 (the altitude correction quoted against Annex C)

- **Location:** Annex E (informative), E.4.2.5 "Radiation impedance
  correction, $C_2$", the sentences that size $u_{C_2}$.
- **The print:** "For altitudes less than 500 m above sea level, no
  meteorological correction is required. At 120 m altitude and 23 °C, the
  correction is 0 dB and at 500 m altitude, the correction is 0,6 dB.
  Assuming a triangular distribution for this uncertainty, the standard
  deviation is $u_{C_2} = 0{,}6/\sqrt{6} = 0{,}3$ dB."
- **The problem:** the normative Annex C defines the correction as
  $C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + 15 \lg[(273{,}15 +
  \theta)/\theta_\mathrm{ref}]$ with the static pressure of Eq. (C.2),
  $p_\mathrm{s} = p_{\mathrm{s},0}\,(1 - aH_\mathrm{a})^b$. At 23 °C that gives
  0,07 dB at 120 m ($p_\mathrm{s}$ = 99,89 kPa, of which the pressure term
  $-10 \lg(p_\mathrm{s}/p_{\mathrm{s},0})$ is 0,06 dB) and 0,26 dB at 500 m
  ($p_\mathrm{s}$ = 95,46 kPa), not the printed 0,6 dB, and the arithmetic
  printed after it does not close either: $0{,}6/\sqrt{6} = 0{,}245$, printed
  0,3. No altitude below which "no meteorological correction is required"
  appears in Annex C. The informative example is inconsistent with the
  normative annex it cites.
- **Evidence:** recomputation of Eq. (C.2) and $C_2$ from the printed
  constants ($a$ = 2,2560 × 10⁻⁵ m⁻¹, $b$ = 5,255 3, $p_{\mathrm{s},0}$ =
  1,013 25 × 10⁵ Pa, $\theta_\mathrm{ref}$ = 296 K). Verified on PDF page 46
  (printed p. 37) and PDF page 36 (printed p. 27) of BS EN ISO 3747:2010.
- **Library behaviour:** implements Annex C as printed:
  [`static_pressure_from_altitude`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py)
  evaluates Eq. (C.2) and the result's `c2` the correction, so a site at
  500 m gets the 0,26 dB the annex gives. The Annex E budget is not
  modelled. Pinned by `test_static_pressure_from_altitude_eq_c2` in
  [`tests/emission/test_sound_power_in_situ.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_situ.py)
  and by the conformance check "ISO 3747:2010 Eq. C.2".
- **Status:** unreported.

## ISO 3747:2010, Table E.2 (the excess that lost its delta)

- **Location:** Annex E (informative), Table E.2 "Uncertainty budget for
  determinations of $\sigma_{R0}$...", the sensitivity-coefficient cell of the
  $\delta_r$ (measurement distance) row.
- **The print:** $c_i = 10^{-0{,}1(L_f - 3)}\,8{,}7/r$.
- **The problem:** the quantity in the exponent is the *excess* of sound
  pressure level over the free field, $\Delta L_f$ of Eq. (A.1), not a level
  $L_f$; no quantity called $L_f$ is defined anywhere in the standard.
  E.4.2.6.2, which derives this very coefficient, prints it as
  $c_r = 10^{-0{,}1(\Delta L_f - 3\ \mathrm{dB})}\,8{,}7/r$, and its worked
  extreme ($\Delta L_f$ = 7,1 dB, $r$ = 6 m) reproduces the 0,6 quoted there
  only with the excess in the exponent ($10^{-0{,}41} \times 8{,}7/6 =
  0{,}564$). The delta was dropped in the table.
- **Evidence:** the table cell read against the text that derives it, verified
  on PDF page 44 (printed p. 35) and PDF page 47 (printed p. 38) of BS EN ISO
  3747:2010. Table E.2 is specific to this part: the corresponding row of
  ISO 3744:2010 carries the free-field coefficient $c_S = 8{,}7/r$ with no
  excess factor at all, so the slip is not inherited from the family.
- **Library behaviour:** the Annex E uncertainty budget is not modelled, and
  the excess itself is evaluated from Eq. (A.1) by
  [`excess_sound_pressure_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py).
  No number changes.
- **Status:** unreported.

## ISO 3747:2010, Table E.2 (the sampling coefficient its own clause contradicts)

- **Location:** Annex E (informative), Table E.2 "Uncertainty budget for
  determinations of $\sigma_{R0}$...", the sensitivity-coefficient cell of the
  $\delta_\mathrm{mic}$ (sampling) row.
- **The print:** $c_i = 0{,}5$.
- **The problem:** E.4.2.6.3, the clause that derives that very row, prints the
  opposite together with its reason: "Sampling directly affects the total
  uncertainty so $c_\mathrm{mic} = 1$". The budget of E.4.2.12 sides with the
  clause and not with the table: its sixth term is $0{,}7^2$, which is the
  0,7 dB contribution E.4.2.6.3 quotes taken at $c_\mathrm{mic} = 1$. The
  neighbouring row settles that 0,5 is no blanket convention for instrument
  rows, because E.4.2.7 sets $c_\mathrm{slm} = 0{,}5$ *and earns it*: repeated
  readings on one meter let the systematic errors cancel, which halves the
  coefficient, and the clause then reproduces the budget's own term
  ($0{,}5 \times 0{,}5 = 0{,}25$ dB, quoted there as 0,3 dB for each of the two
  sources, and $\sqrt{0{,}3^2 + 0{,}3^2} = 0{,}42$ dB, the 0,4 that E.4.2.12
  sums). The sampling row carries no such derivation, and cannot carry one:
  $\delta_\mathrm{mic}$ is defined on the *difference*
  $\Delta L'_{p(\mathrm{ST-RSS})} = L'_{p(\mathrm{ST})} - L'_{p(\mathrm{RSS})}$,
  which already spans both sources, so there is no second contribution to
  halve. The family agrees with the clause: the corresponding
  $\delta_\mathrm{mic}$ row of Table H.2 in ISO 3744:2010 carries $c_i = 1$,
  and its H.4.2.9 prints $c_\mathrm{mic} = 1$ as well.
- **Evidence:** the table cell, the clause that derives it and the budget that
  sums it, read on PDF pages 44, 47 and 50 (printed pp. 35, 38 and 41) of
  BS EN ISO 3747:2010; the family comparison on PDF pages 79 and 82 (printed
  pp. 70 and 73) of BS EN ISO 3744:2010.
- **Library behaviour:** the Annex E uncertainty budget is not modelled. The
  reproducibility the library reports is the tabulated $\sigma_{R0}$ of Table 2,
  read by accuracy grade. No number changes.
- **Status:** unreported.

## ISO 3747:2010, E.4.2.3 (the equation the derivative is taken of)

- **Location:** Annex E (informative), E.4.2.3 "Sound pressure measurement
  repeatability, $\overline{L'_{p(\mathrm{ST})}}$", the sentence introducing
  the sensitivity coefficient $c_{L'_{p(\mathrm{ST})}}$.
- **The print:** "It is obtained from the derivative of
  $L_{W\mathrm{ref,atm}}$ [Equation (E.1)], with respect to
  $\overline{L'_{p(\mathrm{ST})}}$."
- **The problem:** Equation (E.1) is the standard deviation of the operating
  and mounting conditions, $\sigma_\mathrm{omc} = \sqrt{\frac{1}{N-1}\sum
  (L_{p,j} - L_{p\mathrm{av}})^2}$, which contains no
  $L_{W\mathrm{ref,atm}}$ and cannot be differentiated with respect to
  $\overline{L'_{p(\mathrm{ST})}}$. The model that carries
  $L_{W\mathrm{ref,atm}}$ is Equation (E.2), printed on the facing page, and
  differentiating it (with $K_1$ substituted from Eq. 7) does give the
  printed $c_{L'_{p(\mathrm{ST})}} = 1 + 1/(10^{0,1\Delta L_p} - 1)$. A
  cross-reference misprint: (E.1) for (E.2).
- **Evidence:** verified on PDF page 45 (printed p. 36), which carries the
  sentence and the coefficient, against PDF page 41 (printed p. 32) for
  Eq. (E.1) and PDF page 42 (printed p. 33) for Eq. (E.2), of BS EN ISO
  3747:2010. ISO 3741:2010 prints the same coefficient as "the derivative of
  $L_W$ with respect to $L'_{p(\mathrm{ST})}$" with no equation number, so
  the wrong number is this part's own.
- **Library behaviour:** the Annex E uncertainty budget is not modelled, so no
  library number depends on it. Recorded so that a future reader chasing the
  derivation is not sent to the wrong equation.
- **Status:** unreported.

## ISO 5136:2003, Table A.5, 5 000 Hz row (the leading digit of $a_3$ is missing)

- **Location:** Annex A, Table A.5, "Values of coefficients $a_i$ for the
  determination of the combined mean flow velocity and modal correction
  $C_{3,4}$ of the sampling tube for duct diameters 0,8 m $\le d <$ 1,25 m",
  row 5 000 Hz, column $a_3$.
- **The print:** $- ,24 \times 10^{-05}$: a minus sign, a space, a decimal
  comma and two digits, with no digit before the comma. Every other cell of
  the twelve coefficient tables of Annexes A, H and I prints one digit before
  the comma.
- **The problem:** the coefficient cannot be read from the document, and the
  row is inside the normative range of the standard (5 000 Hz,
  $|U| \le 40$ m/s). The $a_3$ of the same band in the two neighbouring
  tables is $-1{,}17 \times 10^{-5}$ (Table A.4, 0,5 m to 0,8 m) and
  $-1{,}27 \times 10^{-5}$ (Table A.6, 1,25 m to 2 m), which brackets
  $-1{,}24 \times 10^{-5}$; a leading digit of 2 or more would move
  $C_{3,4}$ at 40 m/s by 0,64 dB per unit of the digit
  ($a_3 U^3$ with $U^3 = 6{,}4 \times 10^4$), which no neighbouring band or
  table supports.
- **Evidence:** the cell as printed. PDF page 39 (printed p. 29) of
  ISO 5136:2003, against the same cell of Table A.4 on PDF page 38 (printed
  p. 28) and of Table A.6 on PDF page 40 (printed p. 30).
- **Library behaviour:** reads $-1{,}24 \times 10^{-5}$, the value the
  neighbours bracket, in `_TABLE_A5` of
  [`sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py).
  The table's comment and
  `test_table_a5_5000_hz_reads_the_missing_digit_as_one` in
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py)
  say that it is a reading and not the print; a copy of the standard in
  which the digit survived would settle it.
- **Status:** unreported.

## ISO 5136:2003, Annex D, Annex H and Annex I ($C_{3,4}$ "according to Equation (3)")

- **Location:** the first sentence of Annex D, and the sentence of Annex H
  and of Annex I that introduces their coefficient tables.
- **The print:** "For $d$ = 0,5 m, the values of the coefficients $a_i$ for
  the calculation of $C_{3,4}$ according to Equation (3) are given in Table
  A.4" (Annex D); "Values for the coefficients $a_i$ necessary to compute the
  mean flow velocity-modal corrections $C_{3,4}$ according to Equation (3)
  are given in Tables H.1 to H.3" (Annex H) and "... in Tables I.1 to I.3"
  (Annex I).
- **The problem:** Equation (3) is the cut-on frequency of the first cross
  mode, $f_{1,0} = 0{,}586\,(c/D)\sqrt{1 - (U/c)^2}$, in the definition of
  3.10. The polynomial in $U$ whose coefficients the tables hold is Equation
  (7) of clause 5.3.3.4. The same wrong number is printed three times.
- **Evidence:** PDF pages 45, 64 and 68 (printed pp. 35, 54 and 58) of
  ISO 5136:2003, against Equation (3) on PDF page 16 (printed p. 6) and
  Equation (7) on PDF page 28 (printed p. 18).
- **Library behaviour:** evaluates Equation (7);
  [`flow_modal_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py)
  cites it. No number changes.
- **Status:** unreported (cross-reference defect, no numerical consequence).

## ISO 5136:2003, Annex B, B.2 step 4 ($\Delta L_{\max}$ "given in Table C.1")

- **Location:** Annex B, clause B.2, "Comparative procedure using a
  microphone fitted with a nose cone and a microphone fitted with a sampling
  tube", Step 4.
- **The print:** "Check whether the difference between the circumferentially
  averaged sound pressure levels obtained with the nose cone and the sampling
  tube ($\overline{L_{p\mathrm{NC}}} - \overline{L_{p\mathrm{ST}}}$) is
  smaller than or equal to the maximum allowable difference $\Delta L_{\max}$
  given in Table C.1."
- **The problem:** Table C.1 is the A-weighting $C_j$ of Annex C and holds no
  $\Delta L_{\max}$. The table of the maximum allowable difference against the
  turbulence noise suppression $\Delta L_\mathrm{t}$ of the sampling tube is
  Table B.1, on the page after the step, and the paragraph two above the
  steps already sends the reader to it ("see Table B.1").
- **Evidence:** PDF page 41 (printed p. 31) of ISO 5136:2003, with Table B.1
  on PDF page 42 (printed p. 32) and Table C.1 on PDF page 44 (printed
  p. 34).
- **Library behaviour:** the signal-to-noise procedure of Annex B is a
  qualification of the measurement, not a term of $L_W$, and is not
  implemented. No change was needed.
- **Status:** unreported (cross-reference defect, no numerical consequence).

## ISO 5136:2003, Annex B, B.1 ("the determination of the combined mean flow velocity")

- **Location:** Annex B, clause B.1, "General", the first sentence.
- **The print:** "Two procedures for the determination of the combined mean
  flow velocity are given in B.2 and B.3."
- **The problem:** the annex is titled "Determination of the signal-to-noise
  ratio of sound vs. turbulent pressure fluctuation in the test duct", and
  B.2 and B.3 determine that ratio; nothing in the annex determines a "combined
  mean flow velocity", a phrase that is a fragment of the "combined mean flow
  velocity and modal correction" of clause 5.3.3.4. The sentence also counts
  two procedures where the annex, by the coherence method it closes with,
  gives three.
- **Evidence:** PDF page 41 (printed p. 31) of ISO 5136:2003, the annex
  title and the sentence on the same page, and the coherence procedure on
  PDF page 43 (printed p. 33).
- **Library behaviour:** Annex B is not implemented; nothing to change.
- **Status:** unreported (wording defect).

## ISO 5136:2003, clause 7.4 NOTE (the "hydraulic diameter" $D_\mathrm{h} = \sqrt{S_{\mathrm{f}2}/\pi}$)

- **Location:** clause 7.4, the NOTE that follows the outlet-duct rule for
  large fans in installation category D.
- **The print:** "The hydraulic diameter of the fan outlet area, $S_{\mathrm{f}2}$,
  is given by $D_\mathrm{h} = \sqrt{S_{\mathrm{f}2}/\pi}$".
- **The problem:** $\sqrt{S/\pi}$ is the radius of the circle of area $S$;
  its diameter is $\sqrt{4S/\pi} = 2\sqrt{S/\pi}$. Followed as printed, the
  "2 $D_\mathrm{h}$" the clause asks the outlet duct to be is one equivalent
  diameter long, not two, and whether the rule intended is two diameters or
  two radii cannot be settled from the document.
- **Evidence:** PDF page 33 (printed p. 23) of ISO 5136:2003.
- **Library behaviour:** the duct lengths of clauses 5.2 and 7.4 are facility
  geometry and are not computed; nothing to change.
- **Status:** unreported.

## ISO 5136:2003, Table A.2, coefficient header (the $a_9$ column heads $a9_0$)

- **Location:** Annex A, Table A.2, "Values of coefficients $a_i$ for the
  determination of the combined mean flow velocity and modal correction
  $C_{3,4}$ of the sampling tube for duct diameters 0,2 m $\le d <$ 0,3 m",
  the header row of the coefficient columns, tenth column.
- **The print:** an italic $a$, an italic 9 on the baseline and a subscript
  0, between an $a_8$ and an $a_{10}$ of the same row that both carry their
  index as a subscript.
- **The problem:** a stray subscript zero on a column that is $a_9$. The same
  column is headed $a_9$ in Tables A.1 and A.3 to A.6, the NOTE under every
  one of them sums $a_i U^i$ from $i = 0$ to $i = 10$ over the eleven columns
  the row has, and the single cell this one holds, the
  $4{,}09 \times 10^{-14}$ of the 20 000 Hz row, is the coefficient of
  $U^9$: an $a_{90}$ would have no place in that sum at all.
- **Evidence:** PDF page 36 (printed p. 26) of ISO 5136:2003, against the
  header row of Table A.1 on PDF page 35 (printed p. 25).
- **Library behaviour:** the column is read as $a_9$. `_TABLE_A2` in
  [`sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py)
  carries the 20 000 Hz row as the ten coefficients $a_0$ to $a_9$, and
  `test_table_a2_20_khz_row_reads_the_last_column_as_a9` in
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py)
  multiplies the row out. No coefficient value changes.
- **Status:** unreported (typographic, no numerical consequence).

## ISO 5136:2003, Table A.6, 16 000 Hz row ($a_1$ printed with a doubled multiplication sign)

- **Location:** Annex A, Table A.6, "... for duct diameters 1,25 m $\le d \le$
  2 m", row 16 000 Hz, column $a_1$.
- **The print:** $4{,}52 \times\!\times 10^{-01}$, two multiplication signs
  where every other cell prints one.
- **The problem:** typographic only; the mantissa and the exponent are
  legible and the value is $4{,}52 \times 10^{-1}$, in line with the
  $4{,}51 \times 10^{-1}$ of Table A.5 and the $4{,}52 \times 10^{-1}$ of
  Table I.1 at the same band. The row is in the informative range above
  10 kHz.
- **Evidence:** PDF page 40 (printed p. 30) of ISO 5136:2003.
- **Library behaviour:** $4{,}52 \times 10^{-1}$ in `_TABLE_A6` of
  [`sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py).
- **Status:** unreported (typographic, no numerical consequence).

## ISO 5136:2003, Table I.2 (continued), 20 000 Hz row (the exponents of $a_8$ and $a_9$)

- **Location:** Annex I, Table I.2, "... for duct diameters 3,55 m $\le d
  \le$ 5 m", the continuation page, row 20 000 Hz, columns $a_8$ and $a_9$.
- **The print:** $a_8 = -5{,}88 \times 10^{-10}$ and
  $a_9 = 2{,}25 \times 10^{-10}$.
- **The problem:** at $U$ = 40 m/s the printed $a_9$ alone contributes
  $2{,}25 \times 10^{-10} \times 40^9 \approx 5{,}9 \times 10^4$ dB to
  $C_{3,4}$, which no correction can be. The same row of the neighbouring
  tables prints $a_8 = -5{,}90 \times 10^{-12}$ and
  $a_9 = 2{,}25 \times 10^{-13}$ (Table I.1) and
  $a_9 = 2{,}25 \times 10^{-13}$ (Table I.3), so the exponents are
  $-12$ and $-13$ and the print is short by two and three decades. Annex I
  is informative and the row is in the informative range above 10 kHz.
- **Evidence:** PDF page 72 (printed p. 62) of ISO 5136:2003, against the
  same row of Table I.1 on PDF page 70 (printed p. 60) and of Table I.3 on
  PDF page 74 (printed p. 64).
- **Library behaviour:** the informative Annexes H and I are outside the
  scope the standard states for itself (0,15 m to 2 m) and are not
  implemented; a duct above 2 m is refused. Recorded so that an
  implementation of Annex I does not carry the exponents as printed.
- **Status:** unreported.

## ISO 4869-2:2018, Table C.1 (the reprint that disagrees with the table it reprints)

- **Location:** Annex C (informative), Table C.1, "A-weighted octave-band sound
  pressure levels, $L_{p,\mathrm{A}f(k)i}$, **from Table 2**", PDF page 17
  (printed p. 11), against the normative Table 2 it names, PDF page 11
  (printed p. 5).
- **The print:** the two tables carry the same eight reference noises over the
  same seven octave bands, and seven of the eight rows agree digit for digit.
  The sixth reads 82,0 / **89,3** / **93,3** / 95,6 / 93,0 / 90,1 / 83,0 in
  Table 2 and 82,0 / **89,4** / **93,5** / 95,6 / 93,0 / 90,1 / 83,0 in
  Table C.1. The 250 Hz and 500 Hz cells differ; nothing else does.
- **The problem:** Table C.1 states in its own caption that it comes from
  Table 2, so one of the two is wrong, and the annex's own results say which.
  Formula (15) applied to the sixteen attenuation values of Table A.1 with
  Table 2's row reproduces all sixteen $PNR_{j6}$ of Table C.2 exactly; with
  Table C.1's row, thirteen of the sixteen fall 0,1 dB short. Table 2 is
  therefore the reading the worked example was computed from, and it is also
  the normative one, Table C.1 being an informative reprint. An implementer
  who takes the reference spectra from Annex C, where they sit next to the
  worked example, gets a protector's $H$ and $M$ values a tenth of a decibel
  low.
- **Evidence:** Formula (15), PDF page 11 (printed p. 5), evaluated on
  Table A.1, PDF page 15 (printed p. 9), against the sixth row of Table C.2,
  PDF page 18 (printed p. 12), all of ISO 4869-2:2018.
- **Library behaviour:** `HML_REFERENCE_NOISES` carries Table 2. The test
  suite computes the same row from Table C.1's values and asserts that it
  misses thirteen of the printed sixteen, so the two readings can never be
  silently swapped.
- **Status:** unreported.

## ISO 4869-6:2019, Table A.3 (the uncertainty rows are formed from the rounded row above them)

- **Location:** Annex A (normative), Table A.3 "An example of ANR earmuff
  active insertion loss test data in dB for a given laboratory", the rows
  "Combined standard uncertainty, $u$, ($\sigma/\sqrt{N}$)" and "Expanded
  uncertainty, $U_{95}$", PDF page 16 (printed p. 10), against the definitions
  of A.1 and A.2 on PDF page 14 (printed p. 8).
- **The print:** the table gives the active insertion loss of sixteen subjects
  at the octave frequencies 63 Hz to 8 kHz, then their mean, their standard
  deviation $\sigma$, $u$ and $U_{95}$. The $u$ row reads 0,5 / 0,2 / **0,4** /
  0,5 / 0,4 / 0,4 / 0,4 / 0,2 dB and the $U_{95}$ row **1,0** / 0,4 / **0,8** /
  **1,0** / **0,8** / 0,8 / **0,8** / **0,4** dB. A.2 defines $u$ as "the
  standard deviation of the individual active insertion loss data divided by
  the square root of the number of test subjects, i.e. $\sqrt{16} = 4$", and
  A.1 defines $U_{95}$ as $u$ multiplied by the coverage factor $k = 2$. The
  table carries no note on how it rounds.
- **The problem:** from the sixteen printed rows, the mean and $\sigma$
  reproduce in all sixteen cells, but $u$ at 250 Hz is 0,348 dB, which rounds
  to 0,3 and not 0,4, and $U_{95} = 2\sigma/4$ is 0,935 / 0,355 / 0,697 /
  0,940 / 0,711 / 0,839 / 0,720 / 0,325 dB, which rounds to 0,9 / 0,4 / 0,7 /
  0,9 / 0,7 / 0,8 / 0,7 / 0,3: six of the eight printed cells are 0,1 dB high.
  Every printed cell is instead the formula applied to the **rounded** row
  above it: $1{,}4 / 4 = 0{,}35$ prints as 0,4, and each $U_{95}$ is twice the
  $u$ printed over it. The same table in ISO 4869-1:2018 (its Table A.3, same
  layout) computes at full precision and says so in its NOTE 2, "All
  calculations are made with full precision before rounding to one decimal",
  and all 28 of its derived cells reproduce that way. A reader who applies A.1
  and A.2 to the printed data of ISO 4869-6 gets an expanded uncertainty a
  tenth of a decibel below the printed one in six bands of eight, and cannot
  tell from the page why.
- **Evidence:** the sixteen rows and four derived rows of Table A.3, PDF page
  16 (printed p. 10), recomputed with $u = \sigma/4$ and $U_{95} = 2u$ once at
  full precision and once from the printed $\sigma$ and $u$; A.1 and A.2, PDF
  page 14 (printed p. 8); all of ISO 4869-6:2019. For the contrast, ISO
  4869-1:2018 Table A.3 and its NOTE 2, PDF page 19 (printed p. 13).
- **Library behaviour:** `hearing.active_insertion_loss` returns $u$ and
  $U_{95}$ at full precision from the data, as A.1 and A.2 define them. The
  conformance row and `tests/hearing/test_active_noise_reduction.py` pin the
  mean and $\sigma$ rows as printed, reproduce the $u$ and $U_{95}$ rows the
  way the table forms them, and assert that full precision differs in exactly
  the seven cells named here, each by 0,1 dB.
- **Status:** unreported.

## VDI 2081 Blatt 1:2001-07, Section 6.4 (the English column says the opposite of the German)

- **Location:** printed folio 40 (PDF page 40), Section 6.4 "Verzweigungen" /
  "Junctions", the sentence directly under Equation (35).
- **The print:** the German column reads "Diese in Bild 27 dargestellte Senkung
  des Schallleistungspegels ist **frequenzunabhängig**." The English column of
  the same page, translating the same sentence, reads "This sound power level
  reduction shown in Figure 27 **depends on the frequency**."
- **The problem:** the two say opposite things, and the German is the
  authoritative one: the cover of every VDI guideline states that the German
  version shall be taken as authoritative and that no guarantee is given for
  the English translation. The German is also the one the rest of the document
  agrees with. Figure 27 on the same page plots $\Delta L_W$ against the
  cross-section ratio $S_1 / \sum S_{1,2,3}$ alone and carries no frequency
  axis; Equation (35) itself, $\Delta L_W = |10 \lg (S_1 / \sum_i S_i)|$,
  contains no frequency; and the worked example of VDI 2081 Blatt 2:2005-05
  prints a junction's level reduction as a single number rather than as an
  octave spectrum, in each of its three junctions (Table 1, elements 3, 7 and
  16, printed folios 13 and 15: $5{,}6$, $4{,}8$ and $3{,}0$ dB).
- **The likely mechanism:** the negating prefix of "frequenzunabhängig" is
  absent from the translation, which turns "independent of the frequency" into
  its opposite. Nothing else in the sentence differs.
- **Consequence:** a reader working from the English column alone would look
  for a frequency dependence that neither the equation nor the figure has, and
  might conclude that the guideline is incomplete rather than that the sentence
  is mistranslated.
- **Evidence:** the two columns of the same printed page read against each
  other; Figure 27 on that page; Equation (35) above it; and the three junction
  rows of the worked example in Blatt 2. Verified on PDF page 40 (printed p. 40)
  of VDI 2081 Blatt 1:2001-07 and PDF pages 13 and 15 (printed pp. 13 and 15) of
  VDI 2081 Blatt 2:2005-05.
- **Library behaviour:**
  [`split_loss`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) with
  `model="vdi2081"` returns one value for the junction, the German reading, and
  reproduces all three printed junctions of the worked example.
- **Status:** unreported. Both prints are superseded (Blatt 1:2022-04 and
  Blatt 2:2022-10) and neither successor is held, so whether the translation was
  corrected is not known here.

## VDI 2081 Blatt 2:2005-05, Table 1, element 2 (the hydraulic diameter it prints is not the one it computes with)

- **Location:** Table 1, printed folio 12 (PDF page 12), element 2, the splitter
  silencer: the rows "Hydr. Durchmesser $d_\mathrm{h}$ (m)" and "Strouhalzahl
  $St$".
- **The print:** $d_\mathrm{h} = 0{,}171$ m, and the eight Strouhal numbers
  $0{,}9$, $1{,}7$, $3{,}4$, $6{,}8$, $13{,}5$, $27{,}0$, $54{,}0$ and
  $108{,}0$ over the octaves 63 Hz to 8 kHz, for a clear gap $s = 0{,}100$ m,
  a splitter height $H = 0{,}600$ m and a gap speed $v = 14{,}81$ m/s.
- **The problem:** the two rows disagree. VDI 2081 Blatt 1 Section 7.2.4.2
  defines $St = f_\mathrm{m} d_\mathrm{h} / v_\mathrm{i}$, so the printed
  $d_\mathrm{h}$ and the printed $St$ determine each other. With the printed
  $0{,}171$ m the eight numbers would be $0{,}73$, $1{,}45$, $2{,}89$,
  $5{,}79$, $11{,}57$, $23{,}15$, $46{,}29$ and $92{,}59$: not one of them
  rounds onto the printed row. With $d_\mathrm{h} = 2s = 0{,}200$ m they come
  out as $0{,}851$, $1{,}688$, $3{,}376$, $6{,}752$, $13{,}504$, $27{,}009$,
  $54{,}018$ and $108{,}035$, which round onto all eight.

  Both values are defensible as a hydraulic diameter, which is why this is an
  internal inconsistency rather than a wrong number: $4A/P$ for a $0{,}100$ m
  by $0{,}600$ m gap is $0{,}171$ m, while the parallel-plate limit that a long
  narrow gap tends to is $2s = 0{,}200$ m. The table prints the first and
  computes with the second.
- **Consequence:** following the printed $d_\mathrm{h}$ reproduces neither the
  Strouhal row nor the flow-noise spectrum beneath it. With $2s$ the whole
  element falls out to the last printed decimal: $L_\mathrm{WA} = 52$ dB from
  Equation (49) and the eight octave levels $62{,}7$ down to $35{,}6$ dB from
  Equations (46), (50) and (51), the worst of them 0,046 dB from its printed
  cell.
- **Evidence:** the two rows of the same printed element read against Section
  7.2.4.2 of Blatt 1 (printed folio 53); both candidate diameters evaluated
  over the eight octaves; and the flow-noise spectrum recomputed from each.
  Verified on PDF page 12 (printed p. 12) of VDI 2081 Blatt 2:2005-05 and PDF
  page 53 (printed p. 53) of VDI 2081 Blatt 1:2001-07.
- **Library behaviour:**
  [`silencer_self_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) with
  `model="vdi2081"` takes the clear gap and uses $2s$, so it reproduces the
  worked example. The docstring says which of the two it takes.
- **Status:** unreported. Both prints are superseded and neither successor is
  held.

## VDI 2081 Blatt 2:2005-05, Table 1, element 14 (the element's own row contradicts the one above it)

- **Location:** Table 1, printed folio 15 (PDF page 15), element 14, the round
  bend: the rows "$\Sigma L_\mathrm{W}$" and "$\Sigma L_\mathrm{W}$ (log)",
  8 kHz cell.
- **The print:** the two rows read, over the octaves 63 Hz to 8 kHz, $68{,}5$
  $61{,}7$ $55{,}7$ $43{,}4$ $30{,}1$ $28{,}5$ $34{,}0$ $34$ and $68{,}5$
  $61{,}7$ $55{,}7$ $43{,}4$ $30{,}1$ $28{,}5$ $34{,}0$ $33{,}6$. Seven cells
  agree and the eighth does not.
- **The problem:** the second row is the first with the element's own flow noise
  added, so it can never be lower. Element 13 hands 8 kHz over at $37{,}0$ dB,
  the bend attenuates $3$ dB, and the first row prints the $34{,}0$ dB that
  leaves. The bend's own noise in that band is $-14{,}4$ dB, which the same
  element prints two rows higher, and adding it moves the level by less than
  $0{,}0001$ dB. The second row should therefore print $34{,}0$ dB and prints
  $33{,}6$.

  Read the other way the cell is equally unreachable: $33{,}6$ dB would need
  $36{,}6$ dB to arrive from element 13, and element 13 prints $37{,}0$ dB in
  its own $\Sigma L_\mathrm{W}$ row on the same page.
- **Consequence:** $0{,}4$ dB at 8 kHz, carried into element 15 and everything
  after it. The A-weighted total of the element is printed as $50{,}9$ dB in
  both rows, which is what hides it: at 8 kHz the A-weighting is $-1{,}1$ dB and
  the band is $16$ dB under the 4 kHz one, so $0{,}4$ dB there does not reach
  the first decimal of the total.
- **Evidence:** the two rows of element 14 and the $\Sigma L_\mathrm{W}$ row of
  element 13, with the sum recomputed at full precision from the printed
  hand-over, attenuation and flow noise. Verified on PDF page 15 (printed
  p. 15) of VDI 2081 Blatt 2:2005-05.
- **Library behaviour:** the conformance rows for element 14 compare the flow
  noise the bend makes, $26{,}9$ down to $-14{,}4$ dB, against the row that
  prints it, and the chain row carries the $34{,}0$ dB the arithmetic gives
  rather than the printed $33{,}6$.
- **Status:** unreported. The print is superseded and the successor is not held.

## VDI 2081 Blatt 2:2005-05, Table 1, element 2 (a cross-reference to the wrong clause)

- **Location:** Table 1, printed folio 12 (PDF page 12), element 2, the box
  reading "Tabelle aus VDI 2081 Blatt 1/7.3.2" beside the coefficients
  $a_1$, $a_2$, $b_1$ and $b_2$.
- **The print:** the coefficients $0{,}255$, $0{,}015$, $-2{,}82$ and $-2{,}91$
  are credited to Section 7.3.2 of Blatt 1.
- **The problem:** Section 7.3 of VDI 2081 Blatt 1:2001-07 is "Luftschalldämmung
  eines Bauteils", the airborne sound insulation of a building component, and
  has no such table. The coefficients are printed in Section **7.2.3.2**,
  "Kulissenschalldämpfer", on printed folio 52, whose table gives exactly those
  four values in its 200 mm row, which is the splitter thickness the element
  uses.
- **Consequence:** a reader following the reference lands in the wrong chapter.
  The values themselves are right.
- **Evidence:** the cited clause and the actual one, both read from the printed
  pages. Verified on PDF page 12 (printed p. 12) of VDI 2081 Blatt 2:2005-05
  and PDF page 52 (printed p. 52) of VDI 2081 Blatt 1:2001-07.
- **Library behaviour:** none; the library cites Section 7.2.3.2.
- **Status:** unreported.

## ISO 11200:2014, Annex B (the two case studies compute the same standard deviation two different ways)

- **Location:** Annex B, Table B.1 on printed folio 27 (PDF page 33) and
  Table B.3 on printed folio 30 (PDF page 36). Both tables carry a row labelled
  identically, "Standard deviation of the three values measured, $\sigma_{omc}$".
- **The print:** Table B.1 lists the three readings 94,5 dB; 94,3 dB; 93,8 dB
  and gives $\sigma_{omc} = 0{,}3$ dB. Table B.3 lists 79,0 dB; 80,2 dB;
  82,9 dB and gives $\sigma_{omc} = 2$ dB.
- **The problem:** the two use different estimators. Equation (C.1), printed
  identically in ISO 11201:2010, ISO 11202:2010 and ISO 11204:2010, is the
  **sample** standard deviation,

  $$
  \sigma_\mathrm{omc} = \sqrt{\frac{1}{N-1}
  \sum_{j=1}^{N} \left( L'_{p,j} - \overline{L'_p} \right)^2}
  $$

  With $1/(N-1)$ the first triple gives 0,3606 dB, which rounds to **0,4**, not
  the 0,3 the table prints; the second gives 1,9975 dB, which rounds to the
  **2,0** the table prints. With $1/N$ the first gives 0,2944 → **0,3**, the
  printed value, and the second 1,6310 → 1,6, which is not printed. Table B.1
  therefore divides by $N$ and Table B.3 by $N-1$, in the same annex, under the
  same label, for the same quantity.
- **Consequence:** it is not cosmetic, because the value propagates. Table B.1
  goes on to print $\sigma_\mathrm{tot} = 1{,}5$ dB and $U = 2{,}4$ dB from
  $\sigma_{R0} = 1{,}5$ dB. With the 0,4 dB that Equation (C.1) gives,
  $\sigma_\mathrm{tot} = \sqrt{1{,}5^2 + 0{,}4^2} = 1{,}552 \to 1{,}6$ dB and
  $U = 1{,}6 \times 1{,}552 = 2{,}48 \to 2{,}5$ dB, the coverage factor
  applying to the unrounded total rather than to the decibel it is reported
  as. A reader reproducing the example from the equations does not obtain the
  uncertainty the example publishes.
- **The likely mechanism:** three readings is the smallest sample the equation
  admits, and it is exactly where the two divisors differ most: $\sqrt{3/2}$ is
  a 22 % gap. A spreadsheet's population-standard-deviation function reaches
  for $1/N$ by default, and at three points the slip is large enough to change
  the rounded decibel.
- **Evidence:** both tables read from the printed page, not from extracted
  text. Verified on PDF pages 33 and 36 (printed pp. 27 and 30) of
  ISO 11200:2014, against Equation (C.1) on PDF page 32 (printed p. 26) of
  ISO 11201:2010.
- **Library behaviour:**
  [`operating_standard_deviation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/workstation.py)
  implements Equation (C.1) as printed, with $1/(N-1)$. It reproduces
  Table B.3 and deliberately does not reproduce Table B.1's 0,3 dB;
  `tests/emission/test_workstation.py` pins both halves so the choice cannot
  drift.
- **Status:** unreported.

## ISO 3382-1:2009, A.2.1 (the same symbol names two different levels, a page apart)

- **Location:** Annex A (informative), A.2.1. The "where" list under
  Equations (A.2) and (A.3) on printed folio 13 (PDF page 21), and the "where"
  list under Equation (A.5) on printed folio 14 (PDF page 22).
- **The print:** folio 13 gives "$L_{pE}$ is the sound pressure exposure level
  of $p(t)$", with $p(t)$ "the instantaneous sound pressure of the impulse
  response measured at the measurement point", that is, the receiver in the
  hall under test. Folio 14, inside NOTE 1, gives "$L_{pE}$ is the
  spatial-average sound pressure exposure level measured in the reverberation
  room".
- **The problem:** one symbol, two quantities, same subclause, no
  distinguishing subscript and no note that the symbol has been reused. The
  second is a calibration of the source in a laboratory; the first is the
  measurement the whole annex exists to make.
- **Consequence:** substituting (A.5) into (A.1) as the symbols are printed
  gives

  $$
  G = L_{pE} - L_{pE,10} = L_{pE} - \left[ L_{pE} + 10 \lg (A/S_0) - 37 \right]
    = 37 - 10 \lg (A/S_0)\ \text{dB},
  $$

  in which the hall has vanished and the sound strength depends only on the
  absorption area of the reverberation room the source was calibrated in. The
  substitution is what the printed symbols invite, and it is nonsense.
- **Evidence:** Verified on PDF pages 21 and 22 (printed pp. 13 and 14) of
  BS EN ISO 3382-1:2009.
- **Library behaviour:**
  [`reverberation_room_reference_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py)
  names its argument `reverberation_room_level`, and the hall's own level
  never reaches it: it is measured by
  [`sound_strength`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) from the response
  passed as `ir`. Nothing stops a caller writing the substitution out by hand,
  but no single variable plays both roles, and the two names say which is
  which.
- **Status:** unreported.

## ISO 3382-1:2009, A.2.1 (a directivity survey "at every 12,5 degrees" that does not close the circle)

- **Location:** Annex A (informative), A.2.1, the note immediately under
  Equation (A.4), printed folio 13 (PDF page 21).
- **The print:** "When making such a measurement in a free field, it is
  necessary to make the measurement at every 12,5° around the sound source and
  to calculate the energy-mean value of the sound pressure exposure levels in
  order to average the directivity of the sound source."
- **The problem:** $360 / 12{,}5 = 28{,}8$. There is no whole number of
  12,5° steps that closes a turn: 28 steps reach 350° and leave a 10° gap, 29
  steps overshoot to 362,5°. The instruction cannot be followed literally.
- **Consequence:** two laboratories that both "measure every 12,5°" can use
  different bearing sets, and for a source at the Table 1 directivity limit
  (±6 dB at 4 kHz) their energy means differ. The reference level $L_{pE,10}$
  that every route in A.2.1 leads to is therefore not reproducible from the
  printed instruction alone. The same standard's own source-qualification
  survey in 4.2.1 uses 5°, which divides 360 exactly into 72.
- **Evidence:** Verified on PDF page 21 (printed p. 13) of
  BS EN ISO 3382-1:2009.
- **Library behaviour:**
  [`directivity_energy_average`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) takes
  the reading the note can support: a uniform sampling of the full turn no
  coarser than the printed step, so at least
  $\lceil 360 / 12{,}5 \rceil = 29$ bearings, combined as the energy mean the
  note asks for. Fewer bearings raise `ValueError` rather than averaging a
  turn that was never closed.
- **Status:** unreported.

## ISO 3382-1:2009, C.2.1 and C.2.2 (the prose of both stage supports leaves out an integration limit)

- **Location:** Annex C (informative), C.2.1 on printed folio 23 (PDF
  page 31) and C.2.2 on printed folio 24 (PDF page 32), each in the sentence
  that introduces its own equation.
- **The print:** C.2.1 defines the early support as "the ratio, in decibels,
  of the reflected energy **within the first 0,1 s** relative to the direct
  sound", and prints

  $$
  ST_\mathrm{Early} = 10 \lg \left[
      \frac{\int_{0,020}^{0,100} p^2(t)\ \mathrm{d}t}
           {\int_{0}^{0,010} p^2(t)\ \mathrm{d}t} \right]\ \mathrm{dB}.
  $$

  C.2.2 defines the late support as "the ratio, in decibels, of the
  reflected energy **after the first 0,1 s** relative to the direct sound",
  and prints

  $$
  ST_\mathrm{Late} = 10 \lg \left[
      \frac{\int_{0,100}^{1,000} p^2(t)\ \mathrm{d}t}
           {\int_{0}^{0,010} p^2(t)\ \mathrm{d}t} \right]\ \mathrm{dB}.
  $$

- **The problem:** neither sentence describes the equation beside it.
  Equation (C.1) starts at 0,020 s, not at the 0,010 s the direct-sound
  window ends at, so the interval between them is counted in neither the
  numerator nor the denominator and the prose never mentions the gap.
  Equation (C.2) stops at 1,000 s, where the prose puts no upper limit at
  all.
- **Consequence:** both move a number, and the first moves it further. On an
  exponential decay of $T = 2$ s, a reader who takes "within the first 0,1 s"
  to start where the direct-sound window ends collects the 10 ms to 20 ms
  interval as well, which is 17 % more energy and **0,68 dB** on
  $ST_\mathrm{Early}$, against the 1 dB standard deviation C.2.4 estimates
  for a single reading. The missing ceiling of (C.2) costs 0,01 dB in the
  same hall, because a 2 s decay is already 30 dB down at one second, and
  reaches 0,2 dB at $T = 4$ s and 1,0 dB at $T = 8$ s: it is the cathedral,
  not the concert hall, that the second omission separates.
- **Evidence:** Verified on PDF pages 31 and 32 (printed pp. 23 and 24) of
  BS EN ISO 3382-1:2009.
- **Library behaviour:**
  [`stage_support`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) integrates the
  printed limits, which are the ones in
  [`EARLY_SUPPORT_WINDOW_S`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) and
  `LATE_SUPPORT_WINDOW_S`. `tests/room/test_auditorium_stage.py` drops an
  arrival into the gap and another past the ceiling and requires both to
  change nothing.
- **Status:** unreported.

## ISO 3382-1:2009, Table 1 and A.4 (the same limits are called maximum in one clause and minimum in the other)

- **Location:** the caption of Table 1 and the paragraph of 4.2.1 above it,
  printed folio 3 (PDF page 11), against the fourth paragraph of A.4,
  printed folio 19 (PDF page 27).
- **The print:** 4.2.1 says "Table 1 lists the **maximum** acceptable
  deviations from omnidirectionality when averaged over 'gliding' 30° arcs
  in a free sound field", and the table's own caption reads "Table 1 —
  **Maximum** deviation of directivity of source in decibels for excitation
  with octave bands of pink noise and measured in free field". A.4 says "If
  the source directivity is close to the **minimum** limits given in Table 1,
  the measurement should be repeated with the source turned in at least
  three steps totally."
- **The problem:** one table, two opposite words for what its numbers are.
  The values are ceilings, as their own caption and 4.2.1 both say, and A.4
  calls them a floor.
- **Consequence:** A.4's sentence is the one that tells a laboratory when to
  do extra work, and read as printed it says the opposite of what it means.
  A source "close to the minimum limits" would be a near-perfect one, which
  is the case that needs no repetition at all; what A.4 is asking for is the
  repetition of a survey whose source only just clears the ceiling, because
  that is where the orientation of the source starts to matter to the
  answer. A reader who takes the word literally repeats the measurement for
  the wrong sources and skips it for the right ones.
- **Evidence:** Verified on PDF pages 11 and 27 (printed pp. 3 and 19) of
  BS EN ISO 3382-1:2009.
- **Library behaviour:**
  [`MAX_SOURCE_DIRECTIVITY_DEVIATION_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py)
  and [`source_directivity_limit`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) carry
  them as the maxima their own caption makes them. The three-orientation
  repeat of A.4 is a procedure, not a computation, and the library does not
  implement it.
- **Status:** unreported.

## ISO 3382-1:2009, 4.2.1 (a gliding average whose window has no stated phase)

- **Location:** 4.2.1, the paragraph immediately above Table 1, printed
  folio 3 (PDF page 11).
- **The print:** "Table 1 lists the maximum acceptable deviations from
  omnidirectionality when averaged over 'gliding' 30° arcs in a free sound
  field. In case a turntable cannot be used, measurements per 5° should be
  performed, followed by 'gliding' averages, each covering six neighbouring
  points."
- **The problem:** six 5° points cover 30° of arc read as six sectors, and
  25° read as the span between the first and the last, so the two sentences
  agree only under the sector reading. More to the point, nothing says where
  those six points sit relative to the arc they average: a window may lead
  its bearing, trail it, or straddle it, and the clause does not choose. Nor
  does it say how the six are combined, although the reference they are
  compared with is explicitly "a 360° energetic average".
- **Consequence:** over a full turn the six-point windows are one cyclic set
  whichever end of its arc a window is pinned to, so the phase moves the
  bearing each deviation is reported against by up to half a window, 15° of
  the pattern, and leaves the deviations themselves alone. For a source near
  its Table 1 limit that is still what decides whether the largest deviation
  is reported on a lobe or between two of them, which is the orientation A.4
  then asks to be turned and measured again. The other two silences do move
  the number: the span reading and the combination law both change what an
  arc averages, so two laboratories that follow the clause can report
  different maximum deviations for one source, and the standard gives no way
  to tell which of them read it right.
- **Evidence:** Verified on PDF page 11 (printed p. 3) of
  BS EN ISO 3382-1:2009.
- **Library behaviour:**
  [`gliding_directivity_deviation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py)
  takes the sector reading, averages the arcs energetically as the reference
  is, and starts each window at the bearing it is reported against, wrapping
  round the turn. Its docstring says all three choices are choices.
- **Status:** unreported.

## IEC 60534-8-3:2010, Annex A (the piping geometry factor is printed rounded, and the annex did not use the rounded value)

- **Location:** Annex A (informative), A.2, the "Given data" block on printed
  folio 32 (PDF page 34) of BS EN 60534-8-3:2011, against the Equation (2) row
  of Table A.1 on the same folio.
- **The print:** the given data lists "Piping geometry factor: $F_\mathrm{p} =
  0{,}98$", under the heading "The following values are used in, or determined
  from, calculations based on IEC 60534-2-1." Table A.1 then prints
  $p_{vc} = 567\,787$ Pa for example 1 and five more values for the other
  columns, from
  $p_{vc} = p_1\left[1 - x/(F_{LP}/F_P)^2\right]$ with $F_{LP} = 0{,}792$.
- **The problem:** those two cannot both be right. Solving Equation (2) for
  $(F_{LP}/F_P)^2$ from each printed pair gives 0,647 829, 0,647 827,
  0,647 821, 0,647 829 and 0,647 833 in the five columns that print a value,
  which is $F_p = 0{,}984$ to four digits in every one of them. The printed
  0,98 gives 0,653 128 and $p_{vc} = 571\,294$ Pa, 3 507 Pa away from the
  printed figure. The value is a computed one, not a datum: the annex says it
  comes from IEC 60534-2-1, and the head loss coefficient it prints,
  $\Sigma\zeta = 0{,}86$, gives $F_p = 0{,}984$ for the DN 100 case. So the
  annex computed with three decimals and printed two.
- **Consequence:** every downstream quantity moves. With the printed 0,98 the
  four regime boundaries come out $x_C = 0{,}287$, $\alpha = 0{,}786$,
  $x_B = 0{,}578$ against the printed 0,285, 0,784 and 0,576, and example 1's
  sound power comes out 21,9 W against the printed 22,3 W. Nothing is far
  wrong, and nothing reproduces either: a reader checking their implementation
  against Annex A with the number Annex A prints will not match a single row.
- **Evidence:** the given data and the six $p_{vc}$ values read from the
  printed page. Verified on PDF pages 33 and 34 (printed pp. 31 and 32) of
  BS EN 60534-8-3:2011.
- **Library behaviour:**
  [`valve_aerodynamic_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves.py) takes
  the ratio as an argument and does not hold a value of its own; the
  conformance rows and `tests/noise_control/test_valves.py` pass
  $0{,}792/0{,}984$ and say why in the fixture.
- **Status:** unreported.

## IEC 60534-8-3:2010, Table A.1 (an equivalent orifice diameter ten times too small, contradicted by the row below it)

- **Location:** Annex A (informative), Table A.1, the Equation (8c) row on
  printed folio 33 (PDF page 35), against the Equation (8a) row printed
  immediately below it.
- **The print:** all six columns of the (8c) row read $d_0 = 0.010$ m. The
  given data on folio 31 gives $N_\mathrm{O} = 6$ cage openings and
  $A = 0{,}00137$ m² for one of them, and Equation (8c) is
  $d_o = \sqrt{4 N_o A/\pi}$.
- **The problem:** $\sqrt{4 \times 6 \times 0{,}00137/\pi} = 0{,}102$ m, not
  0,010 m. The two numerals are the same three digits in a different order.
  The row below settles which is meant: Equation (8a) is $F_d = d_H/d_o$, the
  (8b) row prints $d_H = 0{,}030$ m, and the (8a) row prints $F_d = 0{,}30$ in
  all six columns. 0,030/0,102 is 0,30; 0,030/0,010 is 3,0.
- **Consequence:** a reader who takes the printed $d_o$ gets a valve style
  modifier of 3,0, a jet diameter ten times too large from Equation (9), and a
  peak frequency ten times too low, which moves the internal spectrum of
  Equation (19) by more than three octaves. The rest of the table is computed
  with 0,102 m, so the error is confined to the one printed cell.
- **Evidence:** the (8b), (8c) and (8a) rows read from the printed page.
  Verified on PDF pages 33 and 35 (printed pp. 31 and 33) of
  BS EN 60534-8-3:2011.
- **Library behaviour:**
  [`valve_style_modifier`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves.py)
  implements (8b) and (8c) as printed and returns 0,296 for the annex's cage,
  which rounds to the printed $F_d$; the test named after this entry pins both
  readings so the printed $d_o$ cannot come back.
- **Status:** unreported.

## IEC 60534-8-3:2010, Table A.2 (two frequency factors whose exponent is one power of ten out)

- **Location:** Annex A (informative), A.3, the $G_x$ column of Table A.2 on
  printed folio 43 (PDF page 45), bands 5 and 10 of 33.
- **The print:** the column runs $G_{x,4} = 5.6 \times 10^{-9}$,
  $G_{x,5} = 1.4 \times 10^{-9}$, $G_{x,6} = 3.6 \times 10^{-8}$, and later
  $G_{x,9} = 5.8 \times 10^{-7}$, $G_{x,10} = 1.4 \times 10^{-7}$,
  $G_{x,11} = 3.5 \times 10^{-6}$.
- **The problem:** below the internal coincidence frequency Table 6 makes
  $G_x$ proportional to $f_i^4$, so the column has to rise monotonically, and
  it does everywhere except at those two bands, where it falls. Recomputing
  Table 6 for this pipe gives $1{,}4 \times 10^{-8}$ at band 5 and
  $1{,}4 \times 10^{-6}$ at band 10: the mantissa is right in both and the
  exponent is one too small.
- **Consequence:** none for the rest of the annex, and that is what settles
  it. The transmission losses printed two rows further down, $TL_5 = -86{,}1$
  dB and $TL_{10} = -76{,}2$ dB, are what Equation (20a) gives with the
  corrected factors; the printed factors would give $-96{,}1$ dB and
  $-86{,}3$ dB. So Table A.2 computed with the right values and printed the
  wrong ones, and anyone seeding an oracle from the $G_x$ column alone
  inherits a 10 dB error in two bands.
- **Evidence:** the $G_x$ column read from the printed page. Verified on PDF
  pages 45 and 46 (printed pp. 43 and 44) of BS EN 60534-8-3:2011; the 24
  printed transmission losses on the second of them are what the library
  reproduces to within 0,07 dB.
- **Library behaviour:**
  [`pipe_transmission_loss`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves.py)
  computes $G_x$ from Table 6, and the conformance row "Pipe transmission
  loss, example 7, 24 bands" reproduces every printed loss, which the printed
  $G_x$ could not.
- **Status:** unreported.

## IEC 60534-8-4:2005, Equation (12) (the Strouhal number is printed one way in the clause and another in the annex)

- **Location:** Clause 5.1, Equation (12) on printed folio 11 (PDF page 13) of
  BS EN 60534-8-4:2005, against the same equation restated in the Table A.1
  row (12) on printed folio 23 (PDF page 25).
- **The print:** the clause prints
  $N_{STR} = \dfrac{0{,}02\,F_L^2\,C}{N_{34}\,x_{Fzp1}^{1,5}\,d\,d_0}
  \left(\dfrac{1}{p_1-p_v}\right)^{0,57}$ and the annex prints
  $N_{STR} = \dfrac{0{,}036\,F_L^2\,C\,F_d^{\,0,75}}
  {N_{34}\,x_{Fzp1}^{1,5}\,d\,d_0}
  \left(\dfrac{1}{p_1-p_v}\right)^{0,57}$.
- **The problem:** they are two different functions of the valve, not two
  roundings of one. The annex carries a factor $F_d^{0,75}$ the clause does
  not have, and a leading constant 1,8 times larger. The exponents 0,57 and
  1,5, the square on $F_L$ and the product $d\,d_o$ are identical in both, so
  the difference is confined to the numerator. The annex's own numbers settle
  which one it evaluated: with $C_v = 90$, $F_d = 0{,}42$, $F_L = 0{,}92$,
  $N_{34} = 1{,}17$, $x_{Fzp1} = 0{,}2386$, $d = d_o = 0{,}1$ m and
  $p_1 - p_v = 997\,680$ Pa, the annex form gives 0,399 and the clause form
  0,425, and Table A.1 prints $N_{Str} = 0{,}399$ in two of its three columns
  and 0,243 in the third, both of which are the annex form to three digits.
- **Consequence:** the peak frequency of Equation (11), and with it the whole
  band spectrum of 5.4 and the transmission loss of Equation (16b), which is
  evaluated at that frequency. For Annex A's valve the two forms are 6 %
  apart; for a single-port valve with $F_d = 1$ the annex form is 80 % above
  the clause form, five sixths of an octave in the peak frequency. An
  implementation that follows the normative clause cannot reproduce a single
  frequency-dependent row of the informative annex.
- **Evidence:** both printings as they appear on the page. Verified on PDF
  page 13 (printed p. 11) and PDF page 25 (printed p. 23) of
  BS EN 60534-8-4:2005.
- **Library behaviour:**
  [`jet_strouhal_number`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  takes a ``form`` argument and implements both. The default is ``"annex"``,
  the form that reproduces the printed examples, and the conformance row
  "Strouhal number and turbulent peak (Eqs. (11), (12))" pins it; a test named
  after this entry pins the ratio between the two.
- **Status:** unreported.

## IEC 60534-8-4:2005, Table A.1 (a band transmission loss printed without its minus sign)

- **Location:** Annex A (informative), Table A.1, the Equation (22a) row on
  printed folio 25 (PDF page 27), all three columns.
- **The print:** the three cells read "TL (8 000 Hz) = 51,76 dB", with no sign
  before the 5.
- **The problem:** Equation (22a) is $TL(f_i) = TL_{fr} + \Delta TL(f_i)$, and
  the table prints both of its inputs one row above and two folios earlier:
  $\Delta TL(8\,000\ \text{Hz}) = -7{,}053$ dB in the (22b) row on the same
  page, and $TL_{fr} = -44{,}71$ dB in the (15) row on printed folio 23. Their
  sum is $-51{,}763$ dB. The row below settles it too: Equation (21) with
  $L_{pi}(8\,000\ \text{Hz}) = 116{,}3$ dB and the 12,67 dB spreading term
  gives 51,87 dB against the printed $L_{pe,1m} = 51{,}8$, and the unrounded
  116,252 dB of the chain gives 51,82; with $+51{,}76$ it would give
  155,4 dB.
- **Consequence:** none for the annex, which computed with the right sign and
  printed the wrong one, and 103 dB for anyone seeding an oracle from that
  cell. Every other transmission loss in this document is printed negative
  ($-44{,}71$; $-29{,}56$; $-74{,}27$; $-62{,}917$; $-75{,}006$; $-7{,}053$),
  including the one directly above it.
- **Evidence:** the three (22a) cells and the (22b) cells above them, read on
  the printed page. Verified on PDF page 27 (printed p. 25) of
  BS EN 60534-8-4:2005: there is no hyphen, no minus and no leading dash in
  any of the three, and the (22b) cells beside them print theirs.
- **Library behaviour:**
  [`transmission_loss_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  and the ``band_transmission_loss`` of ``valve_hydrodynamic_noise`` return
  $-51{,}76$ dB for this band, which is what the conformance row "Frequency
  route at 8 kHz, examples 1 to 3 (Eqs. (19) to (22))" pins together with the
  external levels the negative value reproduces.
- **Status:** unreported.

## IEC 60534-8-4:2005, 6.3.2 b) (a seat diameter formula whose constant is not in the unit its symbol is declared in)

- **Location:** Clause 6.3.2, item b), the unnumbered display formula on
  printed folio 15 (PDF page 17), against the Clause 3 symbol table on printed
  folio 6 (PDF page 8).
- **The print:** "$d_o = 5{,}2\sqrt{N_{34}\,C_n}$", with no equation number
  and no unit on the constant. The symbol table declares $d_o$ "Seat or
  orifice diameter", unit **m**.
- **The problem:** the two cannot both hold. For the last stage of any real
  multistage trim the formula returns tens: $C_n = 90$ as a $C_v$, with
  $N_{34} = 1{,}17$, gives 53,4, and a seat 53 m across is not a valve. Read
  as millimetres it is 53 mm, half the bore of the DN 100 valve of Annex A,
  which is what a last stage looks like. IEC 60534-8-3 gives the same quantity
  a second route, through its own Equation (27) and the total flow area, and
  for this stage that route gives 48,4 mm.
- **Consequence:** the result of this formula is fed to Equation (12), where
  $d_o$ sits in the denominator beside $d$ in metres. Taking the printed
  number as metres makes the Strouhal number a thousand times too small and
  the peak frequency with it, which moves the spectrum ten octaves.
- **Evidence:** the formula and the symbol table row as printed. Verified on PDF page 17 (printed p. 15) and PDF page 8 (printed p. 6)
  of BS EN 60534-8-4:2005. This entry rests on the arithmetic of the printed
  formula as well as on the print itself: nothing on PDF pages 8 to 20 states
  the unit of the constant 5,2.
- **Library behaviour:**
  [`last_stage_seat_diameter_mm`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  implements the formula as printed and carries the unit in its name, and its
  docstring says to divide by a thousand before passing the result to
  Equation (12). The test named after this entry pins both the value and the
  order of magnitude.
- **Status:** unreported.

## IEC 60534-8-4:2005, Equation (23b) (a stage inlet pressure computed from the next stage instead of the previous one)

- **Location:** Clause 6.2, Equations (23a) and (23b) on printed folio 13
  (PDF page 15) of BS EN 60534-8-4:2005.
- **The print:** (23a) is "$p_{1,i} = p_1$ for $i = 1$" and (23b) is
  "$p_{1,i} = p_{1,i+1} - \dfrac{p_1-p_2}{(C_{i-1}/C)^2}$ for
  $i = 2 \ldots n$".
- **The problem:** as printed, each stage's inlet pressure is computed from
  the **next** stage's by subtracting a positive quantity, so the sequence
  increases with $i$: the last stage would start at the highest pressure and
  the first at the lowest, which contradicts (23a) and reverses the flow. The
  index in the denominator is $C_{i-1}$, the stage *before* the one being
  computed, which is the recursion the equation is written for:
  $p_{1,i} = p_{1,i-1} - (p_1-p_2)/(C_{i-1}/C)^2$. Read that way the equation
  is the series law for flow resistances, $1/C^2 = \sum_i 1/C_i^2$: each stage
  takes a share of the differential in inverse proportion to the square of its
  own capacity, and the shares sum to the whole.
- **Consequence:** every per-stage quantity of Clause 6, since (24a) chains
  the outlet pressures to the inlets and (26) makes each stage's pressure
  ratio from both. Following the printed index gives a trim whose first stage
  sees the smallest differential, which is the opposite of every multistage
  design the clause describes.
- **Evidence:** both equations as printed. Verified on PDF
  page 15 (printed p. 13) of BS EN 60534-8-4:2005: the subscript is $i+1$ on
  the pressure and $i-1$ on the flow coefficient. This
  entry rests on the internal contradiction between (23a) and (23b) as well as
  on the print.
- **Library behaviour:**
  [`stage_conditions`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  implements the forward recursion and says so in its docstring; the test
  named after this entry pins that the inlet pressures fall along the trim.
- **Status:** unreported.

## IEC 60534-8-4:2005, Equations (18a) and (18b) (two conditions that do not divide the domain between them)

- **Location:** Clause 5.3, Equations (18a) and (18b) on printed folio 12
  (PDF page 14) of BS EN 60534-8-4:2005.
- **The print:** (18a) ends "for $x_\mathrm{F} \le x_\mathrm{Fz}$" and (18b)
  ends "for $x_\mathrm{Fzp1} < x_\mathrm{F} \le 1$".
- **The problem:** the two conditions are written against two different
  thresholds. $x_\mathrm{Fz}$ is the characteristic pressure ratio at the
  6 × 10⁵ Pa the estimate of Equation (3a) and the charts of Figures 4 to 9
  are drawn at, and $x_\mathrm{Fzp1}$ is that same ratio moved to the working
  inlet pressure by Equation (3c), so the two are equal only at that one
  pressure. Above it $x_\mathrm{Fzp1} < x_\mathrm{Fz}$ and the interval
  between them is claimed by both equations, the turbulent one by (18a) and
  the cavitating one by (18b); below it the same interval is claimed by
  neither. Everything else in the document tests the corrected ratio: the
  conditions printed above (7a) and (7b), the region printed for (9), the
  NOTE to (17), and the split of 6.3. (18a) is the only condition in the
  document that names $x_\mathrm{Fz}$, and the two do not even agree on the
  boundary itself, which (18a) includes with ≤ and (18b) excludes with <.
- **Consequence:** it grows with the inlet pressure, because the inlet
  pressure is what separates the two thresholds. At the 10 bar of Annex A the
  disputed interval is $0{,}2386 < x_\mathrm{F} \le 0{,}2543$ and the two
  branches differ by at most 0,03 dB inside it, because Equation (9) starts
  the cavitation term at exactly zero on the threshold. At 100 bar the
  interval runs from 0,179 to 0,254 and the two branches differ by up to
  8 dB; at 400 bar, by 10 dB. High-pressure liquid service is where this
  method earns its keep.
- **Evidence:** the two conditions as printed. Verified on PDF page 14
  (printed p. 12) of BS EN 60534-8-4:2005: (18a) reads "for $x_F \le x_{Fz}$"
  with the subscript Fz and no p1, above a (18b) that reads
  "for $x_{Fzp1} < x_F \le 1$".
- **Library behaviour:**
  [`valve_hydrodynamic_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  decides the regime once, on $p_1 - p_2$ against
  $x_\mathrm{Fzp1}(p_1 - p_\mathrm{v})$, which is the test 5.1 prints for
  Equations (7a) and (7b), and the sound power, the transmission loss, the
  external level and the band spectrum all follow that one flag. The test
  named after this entry pins that a point inside the disputed interval comes
  out cavitating.
- **Status:** unreported.

## IEC 60534-8-4:2005, Table A.1 (three printed intermediates its own equations do not reproduce)

- **Location:** Annex A (informative), Table A.1: the Equation (17) row on
  printed folio 24 (PDF page 26), columns 2 and 3; the Equation (20a) row on
  the same folio, column 3; and the Equation (11) row on printed folio 23
  (PDF page 25), column 1.
- **The print:** $TL_{cav} = -62{,}917$ and $-75{,}006$; $F_{turb}(8\,000\
  \text{Hz}) = -36{,}24$; $f_{p,turb} = 494{,}5$ Hz.
- **The problem:** none of the three follows from the values printed beside
  it. Equation (17) with the annex's own $TL_{turb}$, $f_{p,turb}$,
  $f_{p,cav}$ and efficiency ratio gives $-62{,}86$ and $-74{,}93$, which is
  0,06 and 0,08 dB away. Equation (20a) at 8 kHz with the column's own
  $f_{p,turb} = 397{,}93$ Hz gives $-36{,}18$; the printed $-36{,}24$ needs
  396,0 Hz. And the unrounded chain through Equations (12) and (11) gives
  494,64 Hz in the first column, where columns 2 and 3 reproduce their 654,35
  and 397,93 Hz to the last printed digit.
- **Consequence:** small and confined. None of the three reaches a printed
  result: the external levels of Equations (18a) and (18b) round to the same
  62,7 / 81,0 / 66,9 dB either way, and so does the band level of Equation
  (19a). It matters only to an implementer comparing intermediates, who will
  find three rows out of forty that cannot be matched exactly and no
  explanation on the page.
- **Evidence:** the three rows as printed, recomputed from the intermediates
  printed beside them. Verified on PDF pages 25 and 26
  (printed pp. 23 and 24) of BS EN 60534-8-4:2005. This entry rests on a
  recomputation as well as on the print.
- **Library behaviour:** the conformance row "Cavitating transmission loss,
  examples 2 and 3 (Eq. (17))" carries a tolerance of 0,1 dB and names this
  entry as the reason; the tests named after it pin what the equations give
  and record what the annex printed.
- **Status:** unreported.

## ISO 7235:2003, Table 6 (the 160 Hz band belongs to no row)

- **Location:** Clause 6.2.1, Table 6, "Maximum level differences for three
  microphone positions in the test duct", on printed folio 23 (PDF page 33) of
  BS EN ISO 7235:2009.
- **The print:** the frequency column reads 50, 63, 80, 100, 125 and then
  "$> 160$", with 10, 10, 8, 8, 7 and 6 dB beside them. The header of that
  column is "Frequency / Hz".
- **The problem:** the last row is strictly greater than 160, so the 160 Hz
  one-third octave is covered by no row and the table sets it no limit at all.
  Every other row names a single band centre, and 160 Hz is a
  one-third-octave centre of the same series, so the gap is between the rows
  rather than in the frequencies the clause measures over: 6.1 measures every
  one-third octave from 50 Hz to 10 kHz, 160 Hz included. The intended
  reading is "160 and above" or "$\geq 160$", which is also the only reading
  under which the six rows partition the range.
- **Consequence:** the rule the table serves is the one that sends a test duct
  from three microphone positions to five (6.2.1). Read literally, a
  laboratory measuring the 160 Hz band has no criterion to apply and could
  keep three positions whatever the spread between them. Read as intended, the
  limit there is 6 dB.
- **Evidence:** the six rows as printed, read on the page. Verified on PDF
  page 33 (printed p. 23) of BS EN ISO 7235:2009, which endorses ISO 7235:2003
  without modification: the last cell of the frequency column carries the
  strict inequality sign and no equals bar, and the five rows above it carry
  bare numbers.
- **Library behaviour:**
  [`microphone_spread_limit`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_measurement.py)
  returns 6 dB from 160 Hz upwards, and the conformance row "Microphone
  position spread limits (Table 6)" records the last row as "160 Hz and
  above". A test named for the gap pins the value at 160 Hz itself.
- **Status:** unreported.

## EN 16272-3-1:2012, Clause 6 (a railway rating weighted by "the normalised traffic noise spectrum")

- **Location:** Clause 6, "Single-number rating of airborne sound insulation
  $DL_R$", second paragraph, on printed folio 7 (PDF page 9) of
  BS EN 16272-3-1:2012.
- **The print:** "The individual sound reduction index values shall be
  weighted according to the normalised **traffic** noise spectrum defined in
  Table 1."
- **The problem:** Table 1 of this standard is the *normalised railway noise
  spectrum*, and the definition of $L_i$ three lines below the formula says
  so in as many words: "the relative A-weighted sound pressure level (dB) of
  the normalised railway noise spectrum, as defined in Table 1". The word
  "traffic" is the road wording of EN 1793-2:2012 Clause 5.2, from which this
  clause is otherwise copied verbatim, formula included. Clause 5 of the same
  standard, one page earlier, gets it right: it says "normalised railway
  noise spectrum defined in Table 1".
- **Consequence:** none arithmetically, because the sentence names Table 1 and
  the symbol list names the railway spectrum. It matters to a reader, who can
  take "the normalised traffic noise spectrum" as the defined term it is in
  EN 1793-3 and go looking for the road table: the two spectra share their
  eighteen bands and differ by up to 7 dB band by band, so the two readings do
  not give the same rating.
- **Evidence:** the paragraph as printed, read on the page. Verified on PDF
  page 9 (printed p. 7) of BS EN 16272-3-1:2012: the word "traffic" appears in
  the paragraph above Formula (2), and the word "railway" in the definition of
  $L_i$ under it.
- **Library behaviour:**
  [`airborne_insulation_rating`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/noise_reducing_devices.py)
  takes the spectrum by name and weights a railway rating by the railway
  table, which is what the symbol list and Table 1 say. The conformance row
  "EN 16272-3-1:2012 Clause 6 (DLR on the railway spectrum)" records it.
- **Status:** unreported.

## ISO 8041-1:2017, clause 12.7 ("the appropriate weighting factor (see Table 1)" for `Wf`)

- **Location:** clause 12.7, printed folio 30 (PDF page 30 of the ISO release,
  PDF page 38 of the copy read here), fourth paragraph. The clause opens on
  printed folio 29.
- **The print:** "For each frequency weighting provided, a steady sinusoidal
  electrical signal shall be applied to the electrical input facility at the
  appropriate reference frequency. With an input signal adjusted to indicate
  the reference vibration value on the reference measurement range with
  band-limiting frequency weighting, the indicated frequency-weighted
  vibration values shall equal the indicated band-limited weighted vibration
  value multiplied by the appropriate weighting factor (see Table 1) within
  the tolerance limits of Table 2."
- **The problem:** the pointer to Table 1 names a quantity the test cannot be
  satisfied with. The test fixes the input so that the *band-limited*
  indication reads the reference value, so the frequency-weighted indication a
  conforming meter shows is
  $a_\mathrm{ref}\,|H(f_\mathrm{ref})| / |H_\mathrm{BL}(f_\mathrm{ref})|$: the
  factor that closes the identity is the
  **ratio** of the two responses at the reference frequency, not the overall
  weighting Table 1 prints. For eight of the nine weightings the distinction is
  invisible, because their band-limiting weighting sits between 0,999 68 and
  0,999 97 at their own reference frequency and the two readings agree to
  0,03 %. `Wf` is the exception: its reference frequency of 2,5 rad/s =
  0,397 887 Hz falls inside its own band-limiting skirt, whose corners Table 3
  puts at 0,08 Hz and 0,63 Hz. There the band-limiting weighting is 0,928 078
  and the overall weighting 0,388 848, which Table B.5 prints as 0,927 9 and
  0,388 4 at the neighbouring 0,398 1 Hz band centre. Read as the 0,388 8 of
  Table 1, the row demands a value that a conforming `Wf` meter's indication
  exceeds by 7,76 % of that demanded value ($0{,}418\,982 / 0{,}388\,8 - 1$),
  against the ±5 % Table 2 allows low-frequency whole-body vibration: half
  again over the limit, on an instrument with no defect. Read as the ratio
  0,418 982, the row is true by construction.
- **Evidence:** the printed clause against Table 1 (printed folio 9), Table 2
  (printed folio 12), Table 3 (printed folios 12 to 13) and Table B.5. The two
  responses at 2,5 rad/s are evaluated from the Formula (1) to (5) cascade the
  same Table 3 parameters define, and they reproduce the two Table B.5 columns
  at the neighbouring band centre to four figures. Verified on PDF page 38
  (printed p. 30) of ISO 8041-1:2017(E).
- **Consequence for the standard's own tables:** none. Annex B tabulates the
  band-limiting weighting and the overall weighting in separate columns, so
  both readings can be recovered from it; only clause 12.7's one-line
  instruction is ambiguous.
- **Library behaviour:**
  [`band_limited_weighting_factor`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/human/instrumentation.py)
  returns the ratio, which is the reading that makes the test satisfiable, and
  its docstring tabulates the two readings side by side for all nine
  weightings so a report can say which one it used. `reference_indication`
  returns the Table 1 product, which is the other quantity and the one the
  reference-conditions row of Table 1 is about.
- **Status:** unreported.

## ISO 8041-2:2021, clause 12.7 ("the appropriate weighting factor (see Table 1)" for `Wf`, carried over from Part 1)

- **Location:** clause 12.7, printed folio 26 (PDF page 34), the second
  paragraph on that folio. The clause opens on printed folio 25.
- **The print:** the sentence of ISO 8041-1:2017 12.7 recorded in the entry
  above, word for word: "With an input signal adjusted to indicate the
  reference vibration value on the reference measurement range with
  band-limiting frequency weighting, the indicated frequency-weighted
  vibration values shall equal the indicated band-limited weighted vibration
  value multiplied by the appropriate weighting factor (see Table 1) within
  the tolerance limits of Table 2." Table 1 of this document prints the same
  weighting factor for `Wf` at 2,5 rad/s, 0,388 8, and Table 3 the same `Wf`
  parameters, with its band-limiting corners at 0,08 Hz and 0,63 Hz.
- **The problem:** the ISO 8041-1:2017 defect, carried into the personal
  vibration exposure meter. Part 2 keeps `Wf` among the weightings a PVEM may
  provide, with the same reference frequency inside the same band-limiting
  skirt, so the arithmetic of the entry above holds unchanged: read as the
  0,388 8 of Table 1, the paragraph demands a value that a conforming `Wf`
  meter's indication exceeds by 7,76 % of that demanded value
  ($0{,}418\,982 / 0{,}388\,8 - 1$), outside the ±3 % that the second row of
  Table 2 allows the difference and outside the ±5 % its first row allows a
  low-frequency whole-body indication. Read as the ratio of the overall
  weighting to the band-limiting one at the reference frequency, 0,418 982,
  the paragraph is true by construction.
- **Evidence:** the printed clause against Table 1 (printed folio 5) and
  Tables 2 and 3 (printed folio 8), whose `Wf` row carries the parameters
  ISO 8041-1:2017 prints. Verified on PDF pages 13, 16 and 34 (printed pp. 5,
  8 and 26) of ISO 8041-2:2021(E).
- **Consequence for the standard's own tables:** none, as in Part 1.
- **Library behaviour:** unchanged by this entry.
  [`band_limited_weighting_factor`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/human/instrumentation.py)
  returns the ratio, and it serves both parts because Part 2 prints the same
  weightings. The conformance row "ISO 8041-2:2021 Table 2" records the
  tolerances this paragraph is judged against.
- **Status:** unreported.

## ISO 8041-2:2021, clause 12.7 (time weightings graded against a row Table 2 no longer prints)

- **Location:** clause 12.7, printed folio 26 (PDF page 34), the third
  paragraph on that folio; read against Table 2 on printed folio 8, clause
  5.13 on printed folio 15, clause 5.1.2 on printed folio 6 and Table 8 on
  printed folios 13 and 14.
- **The print:** "For an instrument where time weightings are provided, a
  steady sinusoidal electrical signal shall be applied to the electrical input
  facility at the reference frequency. [...] With the same input signal, the
  indicated vibration values on each time weighting shall equal the indicated
  reference vibration value within the tolerance limits of Table 2." Table 2
  prints two rows: the tolerance of indication at the reference frequency
  (±4 %, and ±5 % for low-frequency whole-body vibration) and the difference
  between a frequency-weighted indication and the band-limited one times the
  weighting factor (±3 %). Clause 5.13, "Running RMS acceleration", reads in
  full: "Not applicable for PVEM."
- **The problem:** the paragraph is the one ISO 8041-1:2017 prints in its own
  12.7 (printed folio 30 of that document), with "the vibration meter" turned
  into "the PVEM", and there the limit it points at is the third row of the
  Part 1 Table 2: the running r.m.s. indication against the linear
  time-averaged one, ±2 %. The time weighting in this family of standards is
  that running r.m.s.; Part 1 titles its Tables 10 and 11 "Time-weighting
  decay rates". Part 2 dropped the row, since its 5.13 declares the running
  r.m.s. not applicable, and kept the paragraph that grades it, so the
  paragraph now sends the reader to a table in which no row states a limit for
  a time-weighted indication. And the document itself lets a PVEM carry one:
  its 5.1.2 (printed folio 6) allows a whole-body PVEM to "optionally, measure
  exposure characteristics based on maximum transient vibration value (MTVV)",
  which ISO 8041-1:2017 3.1.2.4, adopted by clause 3, defines as the "maximum
  value of the running r.m.s. vibration acceleration value when the
  integration time is equal to 1 s", and its Table 8 (printed folios 13 and
  14) grades the "MTVV linear" and "MTVV exponential" of that running r.m.s.
  in the burst. For a PVEM that provides no time weighting the paragraph is
  empty; for one that reports the MTVV, the document does not say what limit
  the indication on each time weighting is held to.
- **Evidence:** the three printed passages against each other, against 5.1.2
  and Table 8, and against ISO 8041-1:2017 12.7 and its Table 2, which print
  the running r.m.s. row this paragraph was written for. Verified on PDF
  pages 14, 16, 21, 22, 23 and 34 (printed pp. 6, 8, 13, 14, 15 and 26) of
  ISO 8041-2:2021(E), and on PDF pages 13, 20, 28 and 38 (printed pp. 5, 12,
  20 and 30) of ISO 8041-1:2017(E) for the definition of the MTVV, the Part 1
  Table 2, the title of its Table 10 and its 12.7.
- **Consequence for the standard's own tables:** none. The defect is a
  cross-reference that outlived its row.
- **Library behaviour:**
  [`PVEM_INDICATION_TOLERANCES_PERCENT`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/human/instrumentation.py)
  publishes the two rows Part 2 prints and no running r.m.s. row, so nothing
  in the library grades a PVEM on this paragraph; the Part 1 row remains
  `RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT`, documented as Part 1 only. The
  conformance row "ISO 8041-2:2021 Table 2" records the two rows.
- **Status:** unreported.

## ISO 8041-2:2021, clause 12.22 ("exited" for "excited")

- **Location:** clause 12.22, "Logging capabilities", printed folio 36 (PDF
  page 44), the first paragraph of the clause.
- **The print:** "Part A of the PVEM shall be placed on a shaker and be exited
  2 times for at least 300 s each."
- **The problem:** "exited" where the sense is "excited": the part is put on a
  shaker to be vibrated twice, once at each end of the 12 h run, and the
  paragraph that follows on printed folio 37 counts the 600 logged samples
  that "correspond to the vibration magnitude", which is those two 300 s
  excitations at one sample per second. As printed, the verb says the part
  leaves the shaker twice.
- **Evidence:** PDF page 44 (printed p. 36) of ISO 8041-2:2021(E), and PDF
  page 45 (printed p. 37) for the 600 samples.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** unaffected. The 12 h logging test of 12.22 is a test
  on a physical meter and is not implemented.
- **Status:** unreported (typographic, no numerical consequence).

## DIN 45669-1:2010-09, Table 9 (a peak-velocity row that contradicts Formula (5), and the KB_F row beside it)

- **Location:** Table 9, printed folio 35 (PDF page 35 of the copy read here,
  which prints its folio numbers without an offset), rows "|v|max in mm/s bei
  f_u = 1 Hz und f_o = 80 Hz" and "KB_F(t) ± 2 % Schwankung".
- **The print:** for a sinusoidal input at the test frequencies, the peak row
  reads 0,852 at 1 Hz, 1,000 at 5,6 Hz, 1,000 at 31,5 Hz, 0,843 at 80 Hz and
  0,249 at 315 Hz; the $KB_F$ row of the same five columns reads 0,103, 0,500,
  0,693, 0,594 and 0,071.
- **The problem:** the two rows are computed on different band limitations, and
  the peak row does not follow the standard's own Formula (5). With
  $f_u = 1$ Hz and $f_o = 80$ Hz that formula gives $|H_{u\mathrm{Soll}}|$ =
  0,995 at 31,5 Hz and 0,100 at 315 Hz, against the 1,000 and 0,249 printed. The
  $KB_F$ row settles which of the two is the intended reading: $KB_F$ is
  $|H_{B\mathrm{Soll}}|/\sqrt{2}$ for a 1 mm/s sine, and at 31,5 Hz that is
  0,6928 from 0,995 and 0,6962 from 1,000, so the printed 0,693 is the first;
  at 315 Hz it is 0,0709 from 0,100 and 0,176 from 0,249, so the printed 0,071
  is again the first, by a factor of two and a half. The 0,852 at 1 Hz is the
  same kind of departure at the other end, against the 0,842 of Formula (5).
- **Evidence:** the printed table against Formulae (5) and (6) on printed folio
  18 and the note under Formula (3) that puts the two corners at 0,8 Hz and
  100 Hz. Verified on PDF page 35 (printed p. 35) of DIN 45669-1:2010-09; the
  two rows are adjacent cells of one column, so no
  offset or transcription question arises. What the two anomalous cells do
  match is the maximum a max-hold display shows when the switch-on transient of
  the band limitation is included: a 1 mm/s sine started at a zero crossing
  gives 0,852 at 1 Hz and 0,248 at 315 Hz through the same filter. That
  reading, though, is not what the other three cells of the row show, so the
  row is not consistently one convention or the other.
- **Consequence for the standard's own tables:** confined to that row.
  Berichtigung 1:2012-12 rewrites Table 8 and does not touch Table 9, and the
  reference indications of 6.2.3.12, which are the values the same test signal
  produces at 16 Hz, are reproduced exactly by the formulas.
- **Library behaviour:**
  [`KB_TEST_INDICATIONS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/vibration_meter.py)
  publishes the three rows of Table 9 that follow the formulas, and the
  conformance report runs a 1 mm/s sine through the whole chain and reproduces
  all fifteen of those values to the three decimals they are printed with. The
  peak row is not published and not checked; the module docstring says why, and
  the peak a record shows is computed from the record rather than from a table.
- **Status:** unreported.

## DIN 45672-1:2009-12, Clause 4.5.1, Formulae (1) and (5) (the compression-wave speed of a thin rod, and a radicand short of a factor 2)

- **Location:** Clause 4.5.1, Formulae (1) to (4) on printed page 7 and
  Formula (5) on printed page 8 (PDF pages 7 and 8 of the copy read here, which
  prints its folios without an offset).
- **The print:** Formula (1) gives the compression-wave speed as
  $v_p = \sqrt{E/\rho} = \sqrt{G(1-\nu)/(\rho(1-2\nu))}$, Formula (3) gives
  Poisson's ratio as $\nu = (v_p^2 - 2 v_s^2)/(2(v_p^2 - v_s^2))$, and
  Formula (5) gives the two moduli as $G = v_s^2 \rho$ and $E = v_p^2 \rho$.
- **The problem:** the three cannot all hold. In the unbounded continuum the
  clause says it is describing, the compression wave travels at
  $v_p = \sqrt{2G(1-\nu)/(\rho(1-2\nu))}$, and Formula (3) is exactly the
  inversion of that together with $v_s = \sqrt{G/\rho}$ of Formula (2). The
  second radical of Formula (1) is short of the factor 2, which makes it
  $\sqrt{2}$ too slow at every Poisson's ratio. The first, $\sqrt{E/\rho}$, is
  the speed of a longitudinal wave in a thin rod: with $E = 2G(1+\nu)$ it gives
  $v_p^2/v_s^2 = 2(1+\nu)$, against $2(1-\nu)/(1-2\nu)$ in the continuum. The
  two expressions Formula (1) sets equal agree with each other only at
  $\nu = (\sqrt{17}-1)/8 \approx 0{,}39$. Formula (5) is the rod speed solved
  for $E$, so from a measured $v_p$ it returns the P-wave modulus
  $M = 2G(1-\nu)/(1-2\nu)$ rather than $E$, which overstates $E$ by 35 % at
  $\nu = 0{,}3$ and by a factor of 3,8 at $\nu = 0{,}45$, the range of a
  saturated soil.
- **Evidence:** the three formulas against each other on the same two pages,
  and against the P-wave speed of an isotropic elastic continuum. Verified on
  PDF page 7 (printed p. 7) for Formulae (1) to (4) and on PDF page 8 (printed
  p. 8) for Formula (5) of DIN 45672-1:2009-12: the radicals, the factor
  $(1-\nu)$ over $(1-2\nu)$ and the absence of the factor 2 are all legible on
  the page.
- **Consequence for the standard's own tables:** none; the clause prints no
  worked values. What it changes is a modulus read from two measured speeds.
- **Library behaviour:**
  [`compression_wave_speed`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/ground.py)
  and
  [`youngs_modulus_from_wave_speeds`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/ground.py)
  implement the continuum relations Formula (3) is the inverse of, and the
  tests hold both printed forms to the factors above, so an edit back to the
  print fails.
- **Status:** unreported.

## DIN 45672-2:1995-07, Clause 4 (the start-up of the running r.m.s., quoted in mean square)

- **Location:** Clause 4, last paragraph of printed page 3, and Figure 3 on
  printed page 4 (PDF pages 3 and 4 of the copy read here, which prints its
  folios without an offset).
- **The print:** the running r.m.s. "erst nach einer Dauer von 2τ mit einer
  Unsicherheit von 14 % und nach einer Dauer von 4τ mit einer Unsicherheit von
  2 % zur Verfügung steht, wobei der Mittelwert des gleitenden Effektivwertes
  für ein harmonisches Signal zugrunde gelegt wurde (siehe Bild 3)": it is only
  available after $2\tau$ to within 14 % and after $4\tau$ to within 2 %, taking
  the mean of the running r.m.s. of a harmonic signal.
- **The problem:** 14 % and 2 % are the shortfalls of the running mean square,
  $e^{-2} = 13{,}5$ % and $e^{-4} = 1{,}8$ %, and not of the running r.m.s. the
  sentence names. Formula (1) started from rest gives a mean square that grows
  as $(1 - e^{-t/\tau})$ of its final value once the ripple is averaged out, so
  the r.m.s. grows as the square root of that, and it is short by
  $1 - \sqrt{1 - e^{-2}} = 7{,}0$ % after $2\tau$ and by
  $1 - \sqrt{1 - e^{-4}} = 0{,}9$ % after $4\tau$: about half the printed
  figures.
- **Evidence:** Formula (1) on the same page and Figure 3 on the next, which
  draws $\tilde v_F/\hat v$ of an 8 Hz and a 20 Hz sine against time in units
  of $\tau$ with the mean marked at 0,707. At $2\tau$ both curves oscillate
  around 0,66, which is 93 % of 0,707, and at $4\tau$ around 0,70. Verified on
  PDF page 3 (printed p. 3) and PDF page 4 (printed p. 4) of
  DIN 45672-2:1995-07.
- **Consequence for the standard's own tables:** none. The advice the sentence
  gives, to start the averaging before the train arrives, stands either way;
  what is overstated is the size of the error a late start costs.
- **Library behaviour:**
  [`running_velocity_rms`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway.py)
  says which quantity each figure belongs to, and the conformance report
  reproduces the printed 14 % and 2 % from the mean square of Formula (1)
  started from rest, which is the reading that matches them.
- **Status:** unreported.

## DIN 45669-2:2005-06, Clause 5.1.4 (a coupling clause cited by the wrong number)

- **Location:** Clause 5.1.4, last paragraph of printed page 6 (PDF page 6 of
  the copy read here, which prints its folios without an offset).
- **The print:** "Bei Messungen am Erdreich sollten für die Schwingungsaufnehmer
  die Ankopplungsverfahren nach 5.3.3 angewandt und müssen die durch die
  Ankopplung verursachten Messabweichungen nach 8.2.3 beachtet werden": for
  measurements on the ground, the coupling methods of 5.3.3 apply and the
  deviations of 8.2.3 are to be observed.
- **The problem:** 5.3.3 is "Ankopplung bei weichen Unterlagen", the coupling
  on soft floor coverings, whose method is the spiked device of Figure 1 a)
  pressed through a carpet. The coupling to the ground is 5.3.4, "Ankopplung
  an das Erdreich", and its methods, the stake, the buried transducer, the
  borehole and the bedded plate, are 5.3.4.2 with Table 2. The other reference
  in the same sentence, 8.2.3, is "Ankopplung an das Erdreich" and points back
  to 5.3.4, which is what the first reference was meant to be.
- **Evidence:** the sentence on printed page 6, the heading of 5.3.3 on
  printed page 8 and the heading of 5.3.4 on printed page 9. Verified on PDF
  page 6 (printed p. 6), PDF page 8 (printed p. 8) and PDF page 9 (printed
  p. 9) of DIN 45669-2:2005-06.
- **Consequence for the standard's own tables:** none; a reader who follows
  the number lands on the carpet device instead of on Table 2.
- **Library behaviour:**
  [`vibration.immission.coupling`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/coupling.py)
  carries the loose-mounting limits of 5.3.2 and 5.3.3 and the ground
  deviation of 5.3.4.1, and its docstring names each by the clause that
  prints it.
- **Status:** not reported.

## DIN 4150-2:1999-06, Annex A, Formula (A.1b) (a clock maximum r.m.s. equated to a mean of squares)

- **Location:** Annex A, Formulae (A.1a) and (A.1b) on printed page 11 (PDF
  page 11 of the copy read here, which prints its folios without an offset).
- **The print:** Formula (A.1a) reads $KB_{FTm,j} = \sqrt{\frac{1}{M_j}
  \sum_{i=1}^{M_j} KB^2_{FTi,j}}$ and, "oder", Formula (A.1b) reads
  $KB_{FTm,j} = \frac{1}{Z_j} \sum_{i=1}^{Z_j} KB^2_{FTi,j}$, for the case
  that only $Z_j$ occupied clock intervals of class $j$ were measured.
- **The problem:** the second formula has no root over its sum, so its left
  side is a clock maximum r.m.s. and its right side a mean of squares. The two
  formulas are printed as alternatives for the same quantity and differ in
  nothing but the count they average over, so both need the root or neither
  does; Formula (A.2) beneath them takes $KB^2_{FTm,j}$ as the mean of the
  squares, which is what the right side of (A.1b) is, and the worked Example
  8 on printed page 17 applies (A.1b) with the root: $KB_{FTm,1} =
  \sqrt{\tfrac{1}{3}(0{,}92^2 + 0{,}6^2 + 0{,}9^2)} = 0{,}82$ "aus Gleichung
  (A.1b)". Either the root was lost from (A.1b) or its left side should read
  $KB^2_{FTm,j}$.
- **Evidence:** the two formulas on printed page 11 and the example on
  printed page 17. Verified on PDF page 11 (printed p. 11) and PDF page 17
  (printed p. 17) of DIN 4150-2:1999-06: the radical of (A.1a) is drawn and
  that of (A.1b) is absent on the page.
- **Consequence for the standard's own tables:** none; the example that uses
  the formula uses the correct one.
- **Library behaviour:**
  [`railway_takt_maximum_rms`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/people.py)
  takes the root, and the tests hold it to the 0,82 and 0,22 of Example 8.
- **Status:** unreported.

## E DIN 4150-2:2023-08, Annex B, Example 9 (the night assessed over 920 clock intervals instead of 960)

- **Location:** B.9.3.3, the two night-time formulas on printed page 44 (PDF
  page 44 of the copy read here, which prints its folios without an offset),
  against 6.5.3.2 on printed page 19.
- **The print:** $KB_{FTr,\mathrm{nachts}} = \sqrt{\tfrac{1}{920} \cdot (12 \cdot
  (0{,}9 \cdot 0{,}24)^2 + 18 \cdot (1{,}0 \cdot 0{,}44)^2)} = 0{,}066$ for the
  case without the project and, with the same divisor, $0{,}096 > 0{,}07$
  for the planned case; the daytime formulas on the same page divide by 1920.
- **The problem:** 6.5.3.2 fixes $N_r$ of Formula (6) at 1920 clock
  intervals by day and 960 by night, which is what 8 h of 30 s intervals
  are. The two night results reproduce 920 exactly, 0,0663 and 0,0957, and
  with 960 they are 0,0649 and 0,0937, which print as 0,065 and 0,094. The
  25 % test that follows, $0{,}096 > 1{,}25 \cdot 0{,}066 = 0{,}082$, becomes
  $0{,}094 > 1{,}25 \cdot 0{,}065 = 0{,}081$ and reaches the same conclusion.
- **Evidence:** the divisor 920 in both night formulas on printed page 44
  and the definition of $N_r$ on printed page 19. Verified on PDF page 44
  (printed p. 44) and PDF page 19 (printed p. 19) of E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none; the example's
  conclusion holds either way.
- **Library behaviour:**
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  divides the night by the 960 of 6.5.3.2, and the conformance rows of
  Example 9 compare with 0,065 and 0,094, saying what the print gives.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, Annex B, Figure B.2 b) (clock maxima printed on the figure that do not give the 0,39 the example uses)

- **Location:** Figure B.2 b) on printed page 33 (PDF page 33) and the text
  of B.4.3.3 on printed page 34.
- **The print:** the figure labels the ten clock intervals of hammer B with
  $KB_{FTi}$ = 0,3; 0,41; 0,47; 0,43; 0,47; 0,37; 0,31; 0,04; 0,3; 0,41, and
  the text sets the 0,04 to zero and finds "$KB_{FTmb}$ = 0,39".
- **The problem:** the r.m.s. of those ten values with the 0,04 as zero is
  $\sqrt{1{,}3759 / 10} = 0{,}371$, not 0,39. The labels of hammer A on the
  same figure do give the 0,16 the text uses. The 1999 edition's Figure C.3
  carried no labels and the 0,39 was inherited from it; the draft added the
  labels and they were not fitted to the number. Examples 4 and 5 use 0,39
  and their verdicts do not change with 0,37: 0,150 and 0,188 in place of
  0,154 and 0,195.
- **Evidence:** the ten labels on printed page 33 and, on printed page 34,
  the sentence "Somit ergibt sich aus Bild B.2." with the line
  "$KB_{FTma}$ = 0,16 und $KB_{FTmb}$ = 0,39" under it. Verified on PDF page 33 (printed p. 33) and PDF page 34
  (printed p. 34) of E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none; Examples 4 and 5
  conclude the same with either value.
- **Library behaviour:** the conformance rows of Examples 4 and 5 of the
  1999 edition, whose text and numbers the draft's Examples 4 and 5 repeat,
  take the 0,16 and 0,39 the text prints as inputs; nothing is read off the
  figure.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, Annex A, Figure A.1 (a decision drawn with its answer the wrong way round)

- **Location:** Figure A.1 on printed page 28 (PDF page 28), the diamond of
  the middle column below the dashed line, against the same figure of
  DIN 4150-2:1999-06, Figure B.1 on its printed page 12.
- **The print:** the diamond asks "KB-Werte > Stufe III?" and its "ja" exit
  leads to "Weiterer Betrieb ohne besondere Maßnahmen", its "nein" exit to
  "Weiterer Betrieb nur mit besonderen Maßnahmen".
- **The problem:** a value above stage III is the case that needs special
  measures, which is how the right-hand diamond of the same figure, with the
  same question, is drawn: "ja" to the special measures. The 1999 figure
  prints the middle diamond as "KB-Werte < Stufe III?" with the same exits,
  which reads correctly; the redrawn figure turned the comparison round and
  kept the exits.
- **Evidence:** the three diamonds below the dashed line on printed page 28
  of the draft and the middle diamond on printed page 12 of the 1999
  edition. Verified on PDF page 28 (printed p. 28) of E DIN 4150-2:2023-08
  and PDF page 12 (printed p. 12) of DIN 4150-2:1999-06.
- **Consequence for the standard's own tables:** none; the figure is a
  management flow and nothing in the standard is computed from it.
- **Library behaviour:** none; the flow of Annex A is not implemented.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, Annex B, B.9.3.1 (an extension assessed by the clause for a new line)

- **Location:** B.9.3.1 on printed page 42 (PDF page 42).
- **The print:** "Die Beurteilung erfolgt nach 6.5.3.5."
- **The problem:** 6.5.3.5 is the assessment of a line to be built new.
  Example 9 is the extension of an existing line by a second track, which
  is 6.5.3.6, and the example goes on to apply the 25 % rule of 6.5.3.6 to
  its Nullfall and Planfall.
- **Evidence:** the sentence on printed page 42, the heading of 6.5.3.5 on
  printed page 21 and of 6.5.3.6 on printed page 21. Verified on PDF page 42
  (printed p. 42) and PDF page 21 (printed p. 21) of E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none; the example applies
  the right clause.
- **Library behaviour:**
  [`assess_railway_change`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  is 6.5.3.6 and its docstring names Example 9 as its worked case.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, 6.5.3.6 (requirements met when one condition holds, and an example that needs them all)

- **Location:** 6.5.3.6 on printed page 22 (PDF page 22 of the copy read
  here, which prints its folios without an offset), against B.9.3.3 and
  B.9.4 on printed page 44.
- **The print:** "Falls eine der folgenden Bedingungen für den
  Prognoseplanfall vorliegt, gelten die Anforderungen dieses Dokuments als
  eingehalten:", followed by a) for $KB_{F\mathrm{max}}$ by day, b) for
  $KB_{F\mathrm{max}}$ by night and c) for $KB_{FTr}$, each met either by
  keeping to its guide value or by an increase under 25 % against the case
  without the project.
- **The problem:** read as printed, one condition is enough. Example 9 has
  b) met, "Für den Prognosefall bleibt der $KB_{F\mathrm{max}}$-Wert
  unverändert bei 0,66", an increase of nought, and still concludes in B.9.4
  that mitigation is to be looked into because $KB_{FTr}$ by night exceeds
  $A_r$ and grows by more than 25 %. The three letters are three assessments
  of two quantities, and the example applies every one that fits the case;
  "eine der" says the opposite.
- **Evidence:** the sentence and its three letters on printed page 22, and
  the unchanged 0,66 with the conclusion on printed page 44. Verified on PDF
  page 22 (printed p. 22) and PDF page 44 (printed p. 44) of
  E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none; the example reaches
  the conclusion the clause is for.
- **Library behaviour:**
  [`assess_railway_change`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  requires every condition that applies, as the example does, and its
  docstring says why.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, Annex B, B.8.3.4 (a result that its own four-decimal inputs do not give)

- **Location:** the last formula of B.8.3.4 on printed page 39 (PDF page
  39), against Table B.1 on printed page 38.
- **The print:** $KB_{FTr} = \sqrt{\tfrac{1}{1920} \cdot (144 \cdot (1{,}0
  \cdot 0)^2 + 144 \cdot (1{,}0 \cdot 0)^2 + 80 \cdot (0{,}7 \cdot 0{,}406\,1)^2 +
  80 \cdot (0{,}7 \cdot 0{,}567\,6)^2)} = 0{,}099\,8 > 0{,}07$.
- **The problem:** with the four-decimal 0,406 1 and 0,567 6 the formula
  gives 0,099 72, which prints as 0,099 7; the 0,099 8 printed is what the
  three-decimal 0,406 and 0,568 of Table B.1 give, 0,099 76. The passages of
  Table B.1 themselves give 0,099 72. One unit in the fourth decimal, and
  the verdict, 0,07 exceeded, does not depend on it.
- **Evidence:** the formula and its result on printed page 39 and the
  r.m.s. values of Table B.1 on printed page 38. Verified on PDF page 39
  (printed p. 39) and PDF page 38 (printed p. 38) of E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** the conformance row of Example 8 compares
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  from the 47 passages with 0,099 7 at half a unit of the fourth decimal,
  and says what the print gives.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, Annex B, B.4.3.3 (the clock maximum r.m.s. attributed to Formula (2))

- **Location:** B.4.3.3 on printed page 34 (PDF page 34), against 4.2.5 on
  printed page 12 and 6.4.2 on printed page 16.
- **The print:** "Wegen der Annahme, dass Bild B.2 repräsentativ für die
  gesamten Teileinwirkungszeiten $T_{ea}$ und $T_{eb}$ sei, gilt nach
  Gleichung (2):", followed by $KB_{FTma} = \sqrt{\tfrac{1}{10} \sum_{i=1}^{10}
  KB^2_{FTia}}$ and the same for hammer B.
- **The problem:** that is Formula (1) of 4.2.5, the clock maximum r.m.s.
  over $N$ intervals. Formula (2) of 6.4.2 is the assessment vibration
  severity from partial exposures, which the example applies two lines
  later, and the draft renumbered the 1999 edition's Formula (3), which the
  1999 example cited, as its (1).
- **Evidence:** the sentence on printed page 34, Formula (1) on printed page
  12 and Formula (2) on printed page 16. Verified on PDF page 34 (printed
  p. 34), PDF page 12 (printed p. 12) and PDF page 16 (printed p. 16) of
  E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none; the arithmetic is
  that of Formula (1).
- **Library behaviour:** none to take.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, Annex B, B.3.2 (a note cited under the clause it was moved out of)

- **Location:** the last bullet of B.3.2 on printed page 31 (PDF page 31),
  against the note under 6.3 on printed page 15.
- **The print:** "Es ist zu prüfen, ob das $A_r$-Kriterium hier nicht zu
  berücksichtigen ist (siehe Anmerkung zu 6.2)."
- **The problem:** the note on the $A_r$ criterion, the 4 h by day and 2 h
  by night above which a steady vibration makes $KB_{FTr}$ not worth
  forming, is printed under 6.3 in the draft; 6.2 is the guide values. In
  the 1999 edition the same note stood under 6.2, the procedure, and the
  example's cross-reference was not moved with it.
- **Evidence:** the bullet on printed page 31, the note under 6.3 on
  printed page 15 and the heading of 6.2 on printed page 14. Verified on
  PDF page 31 (printed p. 31), PDF page 15 (printed p. 15) and PDF page 14
  (printed p. 14) of E DIN 4150-2:2023-08, and the note under 6.2 on PDF
  page 6 (printed p. 6) of DIN 4150-2:1999-06.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** none to take.
- **Status:** not reported; the document is a draft under comment.

## E DIN 4150-2:2023-08, 6.3 (a rare event met below the upper value in the prose and at it in the flowchart)

- **Location:** the fourth bullet of 6.3 on printed page 15 (PDF page 15),
  against 6.5.1.1 on printed page 17 and Figure 2 on printed page 15.
- **The print:** "Für selten auftretende, kurzzeitige Einwirkungen ist die
  Anforderung dieses Dokuments eingehalten, wenn $KB_{F\mathrm{max}}$ kleiner
  als $A_o$ ist (siehe 6.5.1)"; 6.5.1.1 reads "wenn die maximale bewertete
  Schwingstärke $KB_{F\mathrm{max}}$ kleiner oder gleich dem (oberen)
  Anhaltswert $A_o$ nach Tabelle 1 ist", and the diamond of Figure 2 asks
  "$KB_{F\mathrm{max}} \le A_o$?".
- **The problem:** a rare event whose $KB_{F\mathrm{max}}$ equals $A_o$ is
  met by the clause and the figure and not by the bullet that refers to
  them.
- **Evidence:** the bullet and the diamond on printed page 15 and the
  sentence of 6.5.1.1 on printed page 17. Verified on PDF page 15 (printed
  p. 15) and PDF page 17 (printed p. 17) of E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:**
  [`assess_people_in_buildings`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/people.py)
  reads the boundary as the clause and the flowchart do, at or below.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, Annex C, C.3 (two assessment severities that weight by the factor once where Formula (11) squares it)

- **Location:** C.3 on printed page 34 (PDF page 34 of the copy read here,
  which prints its folios without an offset) and printed page 35, against
  Formula (11) on printed page 23 and Annex E on printed page 37.
- **The print:** with 200 passages by day and 20 by night, the factor
  $\alpha$ = 0,7 of a surface tram and $KB_{FTm,Zug}$ = 0,4, Formula (11)
  gives "$KB_{FTr,Zug,Tag}$ = 0,11" and "$KB_{FTr,Zug,Nacht}$ = 0,05", and C.4
  finds the day exceeded, "0,11 > $A_{r,Tag}$ = 0,1".
- **The problem:** Formula (11) with those inputs and $N_r$ = 1920 by day and
  960 by night is $0{,}7 \cdot 0{,}4 \cdot \sqrt{200/1920} = 0{,}090$ and
  $0{,}7 \cdot 0{,}4 \cdot \sqrt{20/960} = 0{,}040$. The printed values are
  what the same inputs give with $\alpha$ under the root once instead of
  squared, $0{,}4 \sqrt{0{,}7 \cdot 200/1920} = 0{,}108$ and
  $0{,}4 \sqrt{0{,}7 \cdot 20/960} = 0{,}048$: the example weights the energy
  of the category by the factor where Formula (11) weights its amplitude.
  With the 0,090 of the formula the verdict of C.4 on the day turns round:
  0,09 is below the $A_r$ of 0,1 and the requirement is met.
- **Evidence:** the inputs on printed page 34, the two results at the top
  of printed page 35 and the assessment below them, the formula and its
  $N_r$ on printed page 23 and the factors on printed page 37. Verified on PDF page 34 (printed p. 34), PDF
  page 35 (printed p. 35), PDF page 23 (printed p. 23) and PDF page 37
  (printed p. 37) of E DIN 45672-3:2023-02.
- **Consequence for the standard's own tables:** the example's daytime
  conclusion, that mitigation is to be planned, does not follow from its
  numbers.
- **Library behaviour:**
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  squares the factor as Formula (11) prints it, and the conformance rows of
  C.3 compare with the 0,090 and 0,040 it gives for the printed inputs,
  saying that the print reads 0,11 and 0,05.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, Annex C, Table C.1 (a sum level formed without the weighting Clause 7.1 prescribes)

- **Location:** Table C.1 and the results of C.3 on printed page 34 (PDF
  page 34), against Formulae (8) and (9) on printed pages 21 and 22.
- **The print:** the table closes with the row
  "Schwinggeschwindigkeitssummenpegel der betrachteten Zugkategorie
  ($L_{v,Zug}$):" and 78,1 dB in its last column, and C.3 feeds it to
  Formula (9),
  $KB_{FTm,Zug} = c_{T1} v_0 10^{L/20} = 0{,}4$, then 0,6 by Formula (10) and
  "$v_{\max}$ = 1,81 mm/s" by Formula (12).
- **The problem:** Clause 7.1 a) first adds the KB weighting of Table 2 to
  each band (Formula (8)) and sums the bands from 4 Hz to 80 Hz. The energy
  sum of the 19 printed $L_v$ without any weighting is 78,08 dB, which is
  the 78,1 printed; the weighted sum over 4 Hz to 80 Hz is 77,7 dB, and the
  chain from it is 0,385, 0,577 and 1,73 mm/s. The printed 1,81 mm/s is
  $3 \cdot 1{,}5 \cdot 5 \cdot 10^{-5} \cdot 10^{78{,}1/20} = 1{,}808$, so the
  example carried the unweighted sum through.
- **Evidence:** the sum and the three results on printed page 34 and the
  formulas on printed pages 21 and 22. Verified on PDF page 34 (printed
  p. 34), PDF page 21 (printed p. 21) and PDF page 22 (printed p. 22) of
  E DIN 45672-3:2023-02.
- **Consequence for the standard's own tables:** the results of C.3 are
  4 % high against the standard's own procedure; the verdicts of C.4 are
  the same either way, 0,6 rounds both.
- **Library behaviour:**
  [`predict_train_category`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  weights the bands as 7.1 a) says before it sums them; the conformance rows
  hold the printed chain from 78,1 dB and the test holds the weighted one.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, Annex C, C.2 and Table C.1 (a floor transfer that comes from no table of Annex A, and a figure cited by the wrong number)

- **Location:** C.2 on printed page 33 (PDF page 33) and the column
  $\Delta L_{v,DF}$ of Table C.1 on printed page 34, against Table A.5 on
  printed page 27 and Figure 4 on printed page 15.
- **The print:** C.2 says the foundation-to-floor transfer of the example
  is "die Übertragungen vom Fundament zur Geschossdecke mit einer
  Deckeneigenfrequenz von 20 Hz aus Bild 3", and Table C.1 prints the
  column 1,9; 2,3; 3,1; 3,5; 5,0; 6,9; 11,5; 17,3; 10,0; 5,4; 1,9; 1,5;
  −0,8; −2,3; −3,8; −5,4; −6,5; −8,1; −9,6 dB from 4 Hz to 250 Hz.
- **The problem:** Figure 3 is the transfer from the ground into a
  foundation at ground level; the foundation-to-floor transfer of a concrete
  floor is Figure 4 and Table A.5. Read at the ratios of the bands to 20 Hz,
  Table A.5's mean gives 1,60; 2,06; 2,52; 3,26; 4,19; 6,35; 9,94; 17,26;
  9,85; 4,41; 3,27; 3,25; 1,42; 3,89; 2,83 dB up to 100 Hz and nothing
  above a ratio of 5. Only the peak agrees; neither the mean nor either
  deviation of Table A.5, nor the 20 Hz column of Table A.1, gives the
  printed column, and the table has no values for the last four bands the
  column fills.
- **Evidence:** the sentence on printed page 33, the column on printed
  page 34 and Table A.5 on printed pages 27 and 28. Verified on PDF page 33
  (printed p. 33), PDF page 34 (printed p. 34), PDF page 27 (printed p. 27)
  and PDF page 28 (printed p. 28) of E DIN 45672-3:2023-02.
- **Consequence for the standard's own tables:** the example cannot be
  reproduced from the standard's own tables; its transfer column is an
  input.
- **Library behaviour:** the conformance rows of Table C.1 take the printed
  column as an input of Formula (1) and hold the sum;
  [`foundation_to_floor_transfer_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  reads Table A.5 as printed.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, Annex A, Table A.6 (a lower deviation printed above the mean it deviates from)

- **Location:** Table A.6 on printed page 28 (PDF page 28), and Figure 5 on
  printed page 16.
- **The print:** at the ratios 0,20, 3,10, 4,00 and 5,00 the column
  "Standardabweichung nach unten (E–u)" reads 2,37; 5,26; 5,42 and 7,63 dB
  against a "Mittelwert (E–m)" of 2,19; 3,55; 3,24 and 3,01 dB, and at 5,00
  the "Standardabweichung nach oben (E–o)" is 5,40 dB, below the lower
  one.
- **The problem:** a deviation downward from a mean cannot lie above it, and
  the upper deviation cannot lie below the lower. Figure 5 draws the same
  crossing, its curve 1 ending above curves 2 and 3, so the figure was made
  from the same data; whether two columns were swapped at the tail or the
  statistics are wrong cannot be told from the page. Table A.5, the concrete
  floor, keeps its order in every row.
- **Evidence:** the four rows on printed page 28 and the tail of the curves
  on printed page 16. Verified on PDF page 28 (printed p. 28) and PDF page
  16 (printed p. 16) of E DIN 45672-3:2023-02.
- **Consequence for the standard's own tables:** a reader who takes the
  lower deviation as the safe side of a timber floor's transfer is above
  the mean at those ratios.
- **Library behaviour:**
  [`FOUNDATION_TO_FLOOR_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  carries the table as printed, its docstring says where the order fails,
  and no order between the three statistics is enforced.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, Figures 5, 6 and 7 (legends that name the wrong table and the wrong quantity)

- **Location:** the legend of Figure 5 on printed page 16 (PDF page 16) and
  the axis legends of Figures 6 and 7 on printed pages 17 and 18.
- **The print:** Figure 5, the foundation-to-floor transfer of timber
  floors, labels its curves 1, 2 and 3 "Übertragung Fundament → Erdgeschoss
  und Obergeschosse bei Holzbalkendecken" with "(D–u)", "(D–m)" and
  "(D–o)"; Figures 6
  and 7, the ground-to-floor transfer, label their vertical axis
  "Pegeldifferenz $\Delta L_{v,DF}(f_{Tn})$ in dB".
- **The problem:** the table Figure 5 draws, Table A.6, names its columns
  E–u, E–m and E–o; D–u, D–m and D–o are the columns of Table A.5, the
  concrete floor of Figure 4. And Figures 6 and 7 draw $\Delta L_{v,DB}$,
  the ground-to-floor difference of Tables A.1 and A.2, as their captions
  say; $\Delta L_{v,DF}$ is the foundation-to-floor difference of Figures 4
  and 5.
- **Evidence:** the legends on printed pages 16, 17 and 18 and the column
  headings on printed pages 28, 24 and 25. Verified on PDF page 16 (printed
  p. 16), PDF page 17 (printed p. 17), PDF page 18 (printed p. 18), PDF page
  24 (printed p. 24), PDF page 25 (printed p. 25) and PDF page 28 (printed
  p. 28) of E DIN 45672-3:2023-02.
- **Consequence for the standard's own tables:** none; the captions and the
  tables are right.
- **Library behaviour:** none to take; the tables are what is implemented.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, 5.4.4 (an annex called normative where it is printed informative)

- **Location:** 5.4.4 on printed page 16 (PDF page 16 of the copy read here,
  which prints its folios without an offset), against the heading of
  Annex A on printed page 24.
- **The print:** "Im normativen Anhang A sind die Werte in Tabellenform für
  alle relevanten Deckeneigenfrequenzen zusammengefasst."; the annex is
  headed "Anhang A (informativ)".
- **The problem:** the six tables the prediction is made from are either
  part of the requirements or an information, and the two pages say one
  each.
- **Evidence:** the sentence on printed page 16 and the heading on printed
  page 24. Verified on PDF page 16 (printed p. 16) and PDF page 24 (printed
  p. 24) of E DIN 45672-3:2023-02.
- **Consequence for the standard's own tables:** none to their values.
- **Library behaviour:** the tables are implemented as printed, whatever
  their status.
- **Status:** not reported; the document is a draft under comment.

## E DIN 45672-3:2023-02, Formula (11) (the assessment sum printed without the rule that zeroes a quiet category)

- **Location:** Formula (11) and its symbols on printed page 23 (PDF page
  23), against Formula (6) of E DIN 4150-2:2023-08 on its printed pages 19
  and 20.
- **The print:** "$KB_{FTr} = \sqrt{\sum_{Zug=1}^{N_Z} \tfrac{n_{Zug}}{N_r}
  (\alpha_{Zug} \cdot KB_{FTm,Zug})^2}$", introduced by "Berechnung der
  Beurteilungs-Schwingstärke ($KB_{FTr}$) für den jeweiligen
  Beurteilungszeitraum entsprechend DIN 4150-2", with $N_r$, $N_Z$,
  $n_{Zug}$, $KB_{FTm,Zug}$ and $\alpha_{Zug}$ "nach informativem Anhang E"
  listed under it and nothing else.
- **The problem:** the sum, its symbols and the factors of Annex E are
  Formula (6) and Table 2 of the draft of DIN 4150-2, which prints under
  its formula that a category whose $KB_{FTm,Zug}$ is at or below 0,1 enters
  as zero. The sentence is not reproduced, so a predicted category at or
  below 0,1 counts here and not in the assessment the formula says it
  performs.
- **Evidence:** the formula and its symbol list on printed page 23, and
  the sentence under Formula (6) on printed page 20 of the other draft.
  Verified on PDF page 23 (printed p. 23) of E DIN 45672-3:2023-02 and PDF
  page 20 (printed p. 20) of E DIN 4150-2:2023-08.
- **Consequence for the standard's own tables:** none; the category of
  Annex C is at 0,4.
- **Library behaviour:** the chain of
  [`predict_train_category`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  ends in
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py),
  which applies the rule of the assessment it stands for.
- **Status:** not reported; the document is a draft under comment.

## DIN 4150-1:2001-06, Formulae (5) and (6) (a distance whose unit is printed as millimetres)

- **Location:** the symbol lists of Formula (5) on printed page 9 (PDF page
  9 of the copy read here, which prints its folios without an offset) and of
  Formula (6) on printed page 10.
- **The print:** "$R$ die Entfernung von der Sprengstelle, in mm;" under
  Formula (5) and "$R$ die Entfernung von der Fallstelle, in mm;" under
  Formula (6), each with "$R_0$ = 1 m (Bezugsgröße)" on the line below.
- **The problem:** the distance enters both formulas only as the ratio
  $R/R_0$ against a reference of 1 m, Formula (2) on printed page 5 defines
  $R$ "in m", and every distance axis of Annex A is in metres. A distance in
  millimetres against a reference in metres would put the ratio a thousand
  times too high.
- **Evidence:** the two symbol lists on printed pages 9 and 10 and the
  definition of $R$ under Formula (2) on printed page 5. Verified on PDF
  page 9 (printed p. 9), PDF page 10 (printed p. 10) and PDF page 5 (printed
  p. 5) of DIN 4150-1:2001-06.
- **Consequence for the standard's own tables:** none; the standard prints
  no values of $k$, $b$ or $m$ to compute anything with.
- **Library behaviour:**
  [`blast_peak_velocity_mm_s`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/prediction.py)
  and `impact_peak_velocity_mm_s` take the distance in metres against the
  1 m reference, and their docstrings say the print has millimetres.
- **Status:** not reported.

## DIN 4150-1:2001-06, Clause 5.2.3 (a low working frequency written as a high one)

- **Location:** the first sentence on printed page 11 (PDF page 11), the
  third paragraph of Clause 5.2.3.
- **The print:** "Vibrationsbäre mit tiefer Arbeitsfrequenz ($f$ > 30 Hz)
  können …".
- **The problem:** a low working frequency cannot be one above 30 Hz, and
  the previous paragraph, on printed page 10, has just said that vibrators
  with high working frequencies, $f$ > 35 Hz, are the favourable ones. The
  sign is the wrong way round; the intended reading is a frequency below
  30 Hz.
- **Evidence:** the sentence on printed page 11 and the "$f$ > 35 Hz" of
  5.2.3 on printed page 10. Verified on PDF page 11 (printed p. 11) and PDF
  page 10 (printed p. 10) of DIN 4150-1:2001-06.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** none to take; the clause is prose.
- **Status:** not reported.

## DIN 4150-1:2001-06, Annex A, Figure A.2 (a legend that swaps two line styles)

- **Location:** Figure A.2 on printed page 18 (PDF page 18).
- **The print:** the legend reads "—— Ausgleichsgerade Z-Komponente" and
  "–·– Ausgleichsgerade X-Komponente", with ▽ for the Z and ○ for the X
  measurements.
- **The problem:** in the drawing the dash-dot line is the steepest of the
  three and runs through the ▽ markers, which are the Z values Figure A.1
  prints on printed page 17, from 6,90 mm/s at 270 m to 0,12 mm/s at
  1470 m; the continuous line is the flattest and runs through the ○
  markers of the X component. The dashed line and the □ markers of the Y
  component agree with their legend. The two styles are swapped between
  legend and drawing.
- **Evidence:** the lines and markers on printed page 18 against the Z
  peaks of printed page 17. Verified on PDF page 18 (printed p. 18) and PDF
  page 17 (printed p. 17) of DIN 4150-1:2001-06.
- **Consequence for the standard's own tables:** none; the figure is an
  illustration and Annex A says its numbers are not a basis for a
  prediction.
- **Library behaviour:** none to take.
- **Status:** not reported.

## DIN 4150-1:2001-06, Annex A, A.5.1 (an eccentric moment with the unit of a force)

- **Location:** the "Vorgang" line of A.5.1 on printed page 25 (PDF page
  25).
- **The print:** "Vibrator (Exzentermoment 320 N, Frequenz $f$ = 32 Hz)".
- **The problem:** an eccentric moment is a mass at a radius, in kg·m or
  N·m, which is how A.5.2 on printed page 27 prints its "statisches Moment
  5 kg · m"; a newton is a force. What was meant, 320 N·m or 32 kg·m,
  cannot be told from the page.
- **Evidence:** the line on printed page 25 and the moment of A.5.2 on
  printed page 27. Verified on PDF page 25 (printed p. 25) and PDF page 27
  (printed p. 27) of DIN 4150-1:2001-06.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** none to take; the case is an illustration.
- **Status:** not reported.

## DIN 4150-1:2001-06, Annex A, Figure A.18 (a point labelled all groups at the count of one hall)

- **Location:** Figure A.18 and its legend on printed page 33 (PDF page 33
  of the copy read here, which prints its folios without an offset),
  against Figure A.16 and A.8.1 on printed page 32.
- **The print:** the sixth measured point is drawn at about 110 machines and
  its legend reads "6) alle Gruppen"; A.8.1 says "Betrieb bis 252 Maschinen
  in zwei Maschinensälen", and the table of Figure A.16 counts 63, 7, 8, 6,
  57, 1, 23, 31, 12, 32, 4, 3 and 5 machines in the groups A to Ge, which is
  252.
- **The problem:** all groups are 252 machines, and 110 is what the groups
  E, F and G of the right-hand hall, the one nearest the measuring point,
  add up to (23, 31 and 56). The point before it, "Gruppen F und G", is at
  87 as those two add up, so the abscissa is the count of the groups
  running; the label of the sixth point is not.
- **Evidence:** the point and its legend on printed page 33, the sentence of
  A.8.1 and the table on printed page 32. Verified on PDF page 33 (printed
  p. 33) and PDF page 32 (printed p. 32) of DIN 4150-1:2001-06.
- **Consequence for the standard's own tables:** none; the text under the
  figure says the measured values stay put above about 60 machines because
  the groups switched on after that are farther off, which is what the
  figure shows either way.
- **Library behaviour:** none to take; the conformance rows of Figure A.18
  read the drawn curve, not the measured points.
- **Status:** not reported.

## ISO 11546-1:1995, 9.4 c) (a quantity cross-referenced to the uncertainty clause)

- **Location:** item 9.4 c) 2) on printed page 9 (PDF page 16 of the BS EN ISO
  11546-1:2009 copy read here, whose folios run seven behind the PDF pages),
  against clause 8 on printed page 8.
- **The print:** "2) A-weighted sound power insulation, $D_{WA}$ (see clause
  8);", listed under "9.4 Acoustical data" among the quantities a measurement
  with the actual sound source has to record.
- **The problem:** clause 8 of this part is "Uncertainty", and it says nothing
  about $D_{WA}$: it states the standard deviations expected of each method and
  sends a declared value to ISO 4871. $D_{WA}$ is defined in definition 3.9 and
  computed by Equation (2) of 6.2. A reader following the cross-reference
  arrives at a clause that does not define the quantity it was sent to find.
- **Evidence:** item 9.4 c) 2) on printed page 9 and the heading and body of
  clause 8 on printed page 8. Verified on PDF page 16 (printed p. 9) and PDF
  page 15 (printed p. 8) of ISO 11546-1:1995 as published in BS EN ISO
  11546-1:2009.
- **Consequence for the standard's own tables:** none; Equation (2) is printed
  correctly where it belongs.
- **Library behaviour:**
  [`sound_power_insulation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  returns $D_{WA}$ from Equation (2) and cites 6.2 for it.
- **Status:** not reported.

## ISO 11546-1:1995, clause 8 (a misspelt word in the uncertainty statement)

- **Location:** the first paragraph of clause 8 on printed page 8 (PDF page
  15).
- **The print:** "When the actual sound source or the artificial sound source
  method is used, it is expected that measurements in confirmity with this part
  of ISO 11546 will yield standard deviations which are equal to or less than
  those given in the International Standard used."
- **The problem:** "confirmity" for "conformity". The sentence is the one that
  attaches the whole uncertainty statement of the part to a condition, so the
  misspelt word is the one that says when the statement holds.
- **Evidence:** the first paragraph of clause 8 on printed page 8. Verified on
  PDF page 15 (printed p. 8) of ISO 11546-1:1995 as published in BS EN ISO
  11546-1:2009.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** none to take; no number depends on it.
- **Status:** not reported.

## ISO 11546-2:1995, Annex C, Table C.1 (a column headed with a standard that does not exist)

- **Location:** Table C.1 on printed page 12 (PDF page 18 of the BS EN ISO
  11546-2:2009 copy read here, whose folios run six behind the PDF pages).
- **The print:** the last column of the table is headed "ISO 10204", carrying
  footnote markers 3) and 4), over the cells $K_2 \leq 7$ and
  $\Delta L \geq 6$. Footnote 4) under the same table reads "If $K_2 \leq 2$,
  the method specified in ISO 11204 is classified as an engineering method."
- **The problem:** ISO 10204 is a metallic-products inspection-document
  standard and has nothing to do with acoustics. The column is ISO 11204, as
  its own footnote says and as the paragraph above the table says: the annex
  opens by naming "ISO 3743-1, ISO 3744, ISO 3746, ISO 3747, ISO 9614-1,
  ISO 9614-2, ISO 11201, ISO 11202 and ISO 11204", with no ISO 10204 among
  them, and repeats the list before step a).
- **Evidence:** the column head and its footnote 4) in Table C.1 on printed
  page 12, against the two lists on the same page. Verified on PDF page 18
  (printed p. 12) of ISO 11546-2:1995 as published in BS EN ISO
  11546-2:2009.
- **Consequence for the standard's own tables:** none; the two cells under
  the head are the ISO 11204 requirements and are correct.
- **Library behaviour:**
  [`TEST_ENVIRONMENT_REQUIREMENTS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  keys that column as `"ISO 11204"`, and a test asserts that no `"ISO 10204"`
  key exists.
- **Status:** not reported.

## ISO 11546-2:1995, definition 3.11 (an estimate that points at the wrong annex)

- **Location:** definition 3.11 on printed page 3 (PDF page 9), against
  Annex C and Annex D on printed pages 12 and 15.
- **The print:** "**3.11 estimated noise insulation due to the enclosure,**
  $D_{WA,e}$ or $D_{pA,e}$: Calculated reduction in A-weighted sound power or
  sound pressure level obtained from $D_W$ or $D_p$, measured in accordance
  with this part of ISO 11546, and a specific noise spectrum. (See annex C.)"
- **The problem:** Annex C of this part is "Guidelines for evaluating the
  applicability of different test environments for *in situ* measurements",
  which computes no such estimate. The quantity the definition names is
  computed in **Annex D**, "Estimated noise insulation due to the enclosure
  for a specific noise spectrum". The cross-reference is the one part 1
  carries, where the estimate genuinely is Annex C; part 2 inserted the test
  environment annex before it and the pointer was not moved.
- **Evidence:** the definition on printed page 3 and the titles of Annex C
  and Annex D on printed pages 12 and 15. Verified on PDF page 9 (printed
  p. 3), PDF page 18 (printed p. 12) and PDF page 21 (printed p. 15) of ISO
  11546-2:1995 as published in BS EN ISO 11546-2:2009.
- **Consequence for the standard's own tables:** none; the formula is the
  same in both parts.
- **Library behaviour:**
  [`estimated_a_weighted_insulation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  cites Annex C of part 1 and Annex D of part 2, which is where each prints
  it.
- **Status:** not reported.

## ISO 11546-2:1995, Annex C, steps c) and d) (a subscript on the wrong half of a ratio)

- **Location:** the lettered procedure of Annex C on printed page 12 (PDF
  page 18).
- **The print:** "c) Calculate $S_V/S$ for the actual situation
  ($S_V/S_\text{actual}$)" and "d) If $S_V/S_\text{actual} \geq S_V/S$
  determined from figure C.1, the test environment is estimated to be
  applicable."
- **The problem:** the word "actual" qualifies the situation, not the
  measurement surface, but it is printed as a subscript on $S$ alone, so the
  expression reads as $S_V$ over an "actual $S$" and step d) reads as a
  comparison of two different ratios of the same $S_V$. There is one
  measurement surface in the procedure; the two sides of the inequality are
  the ratio of the room being judged and the ratio read off Figure C.1 at the
  same $\alpha$.
- **Evidence:** steps c) and d) and the paragraph above them on printed page
  12. Verified on PDF page 18 (printed p. 12) of ISO 11546-2:1995 as
  published in BS EN ISO 11546-2:2009.
- **Consequence for the standard's own tables:** none; Figure C.1 is a curve
  and the annex prints no worked case.
- **Library behaviour:**
  [`test_environment_applicability`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  returns `actual_area_ratio` and `required_area_ratio` as two named ratios of
  the same measurement surface, so the comparison cannot be read the other
  way.
- **Status:** not reported.

## ISO 11546-2:1995, Annex C, first paragraph (a normative reference list with a misspelt word)

- **Location:** the opening paragraph of Annex C on printed page 12 (PDF page
  18).
- **The print:** "In these standards, detailed requirements concerning testing
  conditions and evironments are stated."
- **The problem:** "evironments" for "environments". The sentence is the one
  that establishes what the whole annex is for, and the annex title, the
  paragraph after it and Table C.1 all spell the word correctly.
- **Evidence:** the opening paragraph on printed page 12, against the annex
  title on the same page. Verified on PDF page 18 (printed p. 12) of ISO
  11546-2:1995 as published in BS EN ISO 11546-2:2009.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:** none to take; no number depends on it.
- **Status:** not reported.

## ISO 11957:1996, 6.2 (a low-frequency clearance that relaxes the rule above it)

- **Location:** 6.2 "Cabin locations" on printed page 3 (PDF page 12 of the
  BS EN ISO 11957:2009 copy read here, whose folios run nine behind the PDF
  pages).
- **The print:** "For measurements in the frequency range from 100 Hz to
  10 000 Hz, the distance between the cabin and the walls and ceiling of the
  room shall be at least one-half wavelength corresponding to the centre
  frequency of the lowest frequency band of interest. [...] For measurements
  in the frequency range from 50 Hz to 80 Hz, the distance shall be at least
  2 m."
- **The problem:** the two sentences do not join. Half a wavelength at 100 Hz
  is 1,72 m and grows as the frequency falls, so at 80 Hz the first rule
  would ask for 2,14 m and at 50 Hz for 3,43 m. The sentence that takes over
  below 100 Hz therefore **lowers** the requirement, to 2 m, exactly where the
  wavelength argument asks for more. NOTE 11 of 6.4 makes 50 Hz to 10 kHz the
  preferred range, so the relaxed branch is the one a preferred measurement
  uses.
- **Evidence:** the two sentences of 6.2 on printed page 3, against NOTE 11
  of 6.4 on printed page 4. Verified on PDF page 12 (printed p. 3) and PDF
  page 13 (printed p. 4) of ISO 11957:1996 as published in BS EN ISO
  11957:2009.
- **Consequence for the standard's own tables:** none; the standard prints no
  worked layout.
- **Library behaviour:**
  [`minimum_cabin_clearance_m`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  returns the flat 2 m from 50 Hz to 80 Hz and the half wavelength above,
  exactly as printed, and a test asserts that the low branch is the smaller
  of the two so that the non-monotonicity cannot be "fixed" silently.
- **Status:** not reported.

## ISO 11957:1996, 6.2 (a diffuser clearance that restates the wall clearance)

- **Location:** the second sentence of the clearance rule of 6.2 on printed
  page 3 (PDF page 12).
- **The print:** "[...] shall be at least one-half wavelength corresponding to
  the centre frequency of the lowest frequency band of interest. Furthermore,
  the distance between the cabin and any diffusing elements in the room shall
  be at least one-half of this wavelength."
- **The problem:** "this wavelength" is the wavelength at the lowest band
  centre, so "one-half of this wavelength" is the distance the sentence before
  it has just required of the walls and the ceiling. Introduced by
  "Furthermore", the sentence reads as an additional requirement and states
  the same one. Either it is a restatement, or "this wavelength" was meant to
  be the half wavelength itself and the diffuser distance is a quarter of the
  wavelength; the print does not decide.
- **Evidence:** the two sentences, read one after the other, on printed page
  3. Verified on PDF page 12 (printed p. 3) of ISO 11957:1996 as published in
  BS EN ISO 11957:2009.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:**
  [`minimum_cabin_clearance_m`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  returns one distance for the walls, the ceiling and the diffusing elements
  alike, which is the reading the words carry, and says so.
- **Status:** not reported.

## ISO 11957:1996, 6.7 (a correction method named by a word that is not one)

- **Location:** the background-noise sentence of 6.7 on printed page 5 (PDF
  page 14).
- **The print:** "If the difference is in the range 6 dB to 10 dB, the result
  of the measurement shall be corrected for the effect of the background noise
  in acdance with ISO 3741."
- **The problem:** "acdance" for "accordance", in the sentence that says which
  correction to apply to the internal noise level. Clause 6.4 prints the same
  instruction correctly two pages earlier.
- **Evidence:** the sentence on printed page 5, against the corresponding
  sentence of 6.4 on printed page 4. Verified on PDF page 14 (printed p. 5)
  and PDF page 13 (printed p. 4) of ISO 11957:1996 as published in BS EN ISO
  11957:2009.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:**
  [`internal_noise_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  applies the ISO 3741 correction inside the 6 dB to 10 dB window the same
  sentence sets.
- **Status:** not reported.

## ISO 11957:1996, 7.2.1 (a signal-to-background rule with two words transposed)

- **Location:** the source-spectrum paragraph of 7.2.1 on printed page 6 (PDF
  page 15).
- **The print:** "The output shall be sufficiently high to give a sound
  pressure level inside the cabin exceeding the background noise level by at
  least 6 dB and preferably more by than 12 dB for all frequency bands of
  interest."
- **The problem:** "preferably more by than 12 dB" for "preferably by more
  than 12 dB". The same requirement is printed correctly in 6.4, two pages
  earlier, which is what settles the intended reading.
- **Evidence:** the sentence on printed page 6, against the same sentence in
  6.4 on printed page 4. Verified on PDF page 15 (printed p. 6) and PDF page
  13 (printed p. 4) of ISO 11957:1996 as published in BS EN ISO 11957:2009.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:**
  [`MIN_SIGNAL_TO_BACKGROUND_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  and `PREFERRED_SIGNAL_TO_BACKGROUND_DB` carry 6 dB and 12 dB, and the
  warning names the margin that was actually reached.
- **Status:** not reported.

## ISO 11820:1996, Equations (20) and (22) (a temperature ratio the wrong way up)

- **Location:** Equation (20) of 9.1.3 on printed page 11 (PDF page 19) and
  Equation (22) of 9.1.4 on printed page 12 (PDF page 20).
- **The print:**
  $K_2 - K_1 = 5 \lg\!\left(\dfrac{273 + \theta_1}{273 + \theta_2}\right)$ dB,
  with $\theta_1$ "the temperature, in degrees Celsius, on the receiver side"
  and $\theta_2$ "on the source side"; and, for the insertion loss,
  $K_\mathrm{II} - K_\mathrm{I} = 5 \lg\!\left(\dfrac{273 + \theta_\mathrm{I}}
  {273 + \theta_\mathrm{II}}\right)$ dB, with $\theta_\mathrm{I}$ the
  temperature with the silencer and $\theta_\mathrm{II}$ without it. The
  sentence under Equation (20) explains it: "The different temperatures
  determine different sound velocities which result in different conversion
  factors from squared sound pressure to sound power."
- **The problem:** the ratio is inverted, and the sentence says why. The field
  correction $K$ is a conversion from squared sound pressure to sound power,
  and the standard fixes its sign on its own page: Equations (5) and (7) on
  printed page 3 add it, $L_{W1} = \overline{L_{p1}} + 10\lg(S_1/S_0)$ dB
  $+\ K_1$ and $L_{W2} = \overline{L_{p2}} + 10\lg(S_2/S_0)$ dB $+\ K_2$, with
  subscript 1 the receiver side and subscript 2 the source side, the same
  assignment Equation (20) keys. So $K = -10\lg(\rho c / (\rho c)_0)$ + const.
  The sentence counts only the change in $c$, which rises as $\sqrt{T}$, and
  forgets that the density falls: the standard's own Equation (29) on printed
  page 12 gives $\rho_\mathrm{u} = M\,p_\mathrm{amb}/[R(273 + \theta_
  \mathrm{u})]$, so at one ambient pressure $\rho c$ falls as $T^{-1/2}$ and
  $K$ rises as $+5 \lg T$. Hotter gas therefore needs the *more* positive
  correction, and the difference is
  $5 \lg[(273 + \theta_2)/(273 + \theta_1)]$, the reciprocal of the print. Both
  printed forms carry the same inversion, so this is the equation and not a
  misprinted subscript in one of them.
- **Evidence:** the three equations and the two keys read on the page.
  Equation (20) with its key and the explanatory sentence, and Equations (18)
  and (19), are on PDF page 19 (printed p. 11); Equations (5), (7) and their
  keys are on PDF page 11 (printed p. 3); Equation (22) with its key and
  Equation (29) with $R$ = 8 314,4 N·m/(kmol·K) are on PDF page 20 (printed
  p. 12). All of BS EN ISO 11820:1997, which prints EN ISO 11820:1996. A second
  ISO document prints the same quantity the other way up: the reference
  quantity correction of ISO 3741:2010, which its key calls "a function of the
  characteristic impedance of the air", is
  $C_1 = -10\lg(p_\mathrm{s}/p_{\mathrm{s},0})$ dB
  $+\ 5\lg[(273{,}15 + \theta)/\theta_0]$ dB, added to $L_W$ in Equation (20)
  on PDF page 31 (printed p. 22) of BS EN ISO 3741:2010, and it rises with
  temperature.
- **Consequence for the standard's own tables:** ISO 11820 prints no worked
  example, so nothing in the document is wrong on its face. In use the sign
  costs twice the correction: with a receiver at 20 °C and a source at 200 °C
  the print gives -1,04 dB where the impedance gives +1,04 dB, so both the
  transmission loss of Equation (19) and the insertion loss of Equation (21)
  come out 2,08 dB low.
- **Library behaviour:**
  [`temperature_field_correction_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_in_situ.py)
  returns the equation as printed, because a reader holding ISO 11820 has to
  find the standard's own number, and its docstring names this entry. The
  conformance row "ISO 11820:1996 Eqs. (20) and (22)" pins the printed form.
- **Status:** not reported.

## ISO 10847:1997, Table 1 (an upwind class printed with a positive lower bound)

- **Location:** Table 1, "Class of wind conditions", on printed page 6 (PDF
  page 10).
- **The print:** the short-distance block of the table lists three classes
  against the vector component of the wind velocity in m/s: "Downwind + 1 to
  + 5", "Calm − 1 to + 1" and "Upwind + 1 to − 5".
- **The problem:** "+ 1 to − 5" is not an interval. Its two ends run the wrong
  way round, and its lower end is the value at which the downwind class two
  rows above begins, so read literally the upwind class would start inside the
  downwind one and reach backwards through calm. The sign of the lower bound
  is the character at fault: the upwind class is − 1 to − 5, the mirror of the
  downwind row, which is also what the word "upwind" means for a component
  that 6.3.1 defines as positive along the source-to-receiver line.
- **Evidence:** the three short-distance rows read together on printed page 6,
  against the all-distances block above them, which prints the same downwind
  and calm rows and no upwind one at all. Verified on PDF page 10 (printed
  p. 6) of ISO 10847:1997.
- **Consequence for the standard's own tables:** none. No other clause
  computes with the interval.
- **Library behaviour:**
  [`WIND_CLASSES`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py)
  carries the upwind class as − 5 m/s to − 1 m/s and
  [`wind_class`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py)
  returns it for negative components over a short distance alone, which is
  where the table prints it.
- **Status:** not reported.

## ISO 10847:1997, 8.2.2 (one prime asked to mean two different things)

- **Location:** the two level-difference equations of 8.2.2 and the list of
  symbols under them, on printed page 11 (PDF page 15).
- **The print:** $\Delta L_B = L_{\mathrm{ref},B} - (L_{r,B} - C_r)$ and
  $\Delta L_A = L_{\mathrm{ref},A} - (L_{r,A} - C'_r)$, and then "$C_r$ and
  $C'_r$ are correction factors for the type of receiver position; for "hemi
  free-field": $C_r$ = 0 dB; for "on reflecting surfaces": $C'_r$ = 6 dB".
- **The problem:** the prime carries two meanings in the same clause. In the
  equations it separates the "before" campaign from the "after" one, since
  every other symbol in them is subscripted B or A. In the definitions it
  separates one kind of receiver position from the other. Taken literally the
  two readings combine into a rule nothing else in the standard states: that
  the "before" campaign is made in a hemi free field and the "after" one
  against a reflecting surface.
- **Evidence:** the two equations and the symbol list on printed page 11,
  settled by the NOTE that closes the same clause, "It is preferable to choose
  receiver positions where corrections $C_r$ and $C'_r$ are essentially the
  same", which is advice only if each campaign's correction follows its own
  receiver position rather than being fixed by the campaign. Verified on PDF
  page 15 (printed p. 11) of ISO 10847:1997.
- **Consequence for the standard's own tables:** none.
- **Library behaviour:**
  [`measured_insertion_loss_indirect`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py)
  takes `receiver_type_before` and `receiver_type_after`, each of them
  'hemi_free_field' or 'reflecting_surface' and each defaulting to the former,
  and reads its correction out of `RECEIVER_CORRECTIONS_DB`, which holds the
  printed 0 dB and 6 dB. The result carries both corrections so that a report
  shows which was applied to which campaign.
- **Status:** not reported.

## ISO 14257:2001, Annex C (an example that corrects one of its two results)

- **Location:** C.1 on printed page 17 (PDF page 27), against Tables C.7 and
  C.9 on printed page 23 (PDF page 33) and Tables C.8 and C.10 on printed pages
  23 and 24 (PDF pages 33 and 34).
- **The print:** C.1 lists the four things that hold in the example, the second
  of which is that "the experimental reference curve of the sound source is
  known and used for correcting the values measured in the workroom". Table C.5
  is then headed "Values of $D = L_p - L_W$, in octave bands (corrected for
  background noise)" and Table C.6 "Values of $D = L_p - L_W$ ... corrected for
  background noise **and using the experimental reference curves of the
  source**".
- **The problem:** the four result tables are not all computed from the same
  curve. Every value of $\mathrm{DL}_2$ in Tables C.7 and C.8 follows from the
  corrected curve of Table C.6, and every value of $\mathrm{DL}_\mathrm{f}$ in
  Tables C.9 and C.10 follows from the uncorrected curve of Table C.5. Swap
  either one for the other and 28 of the 36 printed results leave the rounding
  of the table they are printed in.
- **Evidence:** the two curves are printed in full, so both routes can be run.
  Taking Table C.6 as printed, the middle range at 1 kHz gives
  $\mathrm{DL}_2$ = 4,39 dB against the printed 4,4 and
  $\mathrm{DL}_\mathrm{f}$ = 6,73 dB against the printed 7,3; taking Table C.5
  instead gives 4,73 dB and 7,29 dB. The same split holds in all three distance
  ranges and all six octave bands, and in the two A-weighted pink-noise tables.
  Verified on PDF pages 27, 31 and 33 (printed pp. 17, 21 and 23) of
  EN ISO 14257:2001 as published in BS EN ISO 14257:2001.
- **Consequence for the standard's own tables:** none for
  $\mathrm{DL}_2$, which is a slope and is barely moved by a correction that is
  nearly constant with distance. For $\mathrm{DL}_\mathrm{f}$, which is a
  level, the difference reaches 1,4 dB in the near range.
- **Library behaviour:**
  [`corrected_distribution_value`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py)
  applies Annex B when it is asked to and never on its own, so the caller
  chooses which curve each descriptor is taken from. The conformance row "ISO
  14257:2001 Annex C (C.1 against Tables C.7 and C.9)" pins the split, and
  `test_the_annex_corrects_the_decay_but_not_the_excess` in
  [`tests/room/test_spatial_decay.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_spatial_decay.py)
  holds both numbers so that neither can drift.
- **Status:** not reported.

## ISO 14257:2001, Equation (5) against Equation (8) (a rounded logarithm)

- **Location:** Equation (5) of 6.3 on printed page 9 (PDF page 19) and
  Equation (8) of 6.4.3 on printed page 10 (PDF page 20).
- **The print:** Equation (5) opens with the factor $-0,3$ in front of the
  least-squares slope; Equation (8), one page later, divides
  $\mathrm{DL}_2(r_n,r_m)$ by $\lg 2$.
- **The problem:** the two are the same conversion, from a rate per decade to a
  rate per distance doubling, written twice with different precision. $\lg 2$
  is 0,301 03, so the printed 0,3 is 0,34 % small, and a document that prints
  the exact form on one page has no reason to round it on the previous one.
- **Evidence:** the two equations on facing pages, both reproduced in the
  entry above from the printed tables. Verified on PDF pages 19 and 20 (printed
  pp. 9 and 10) of EN ISO 14257:2001.
- **Consequence for the standard's own tables:** none that the printed rounding
  can show: the worked example of Annex C is tabulated to one decimal and 0,34 %
  of a 4 dB slope is 0,014 dB.
- **Library behaviour:**
  [`DECADE_TO_DOUBLING`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) carries the
  printed 0,3, because the printed constant is what reproduces the printed
  results, and
  [`level_excess_at`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) divides by
  $\lg 2$ where Equation (8) prints it. Do not unify them.
- **Status:** not reported.

## ISO 14257:2001, Equation (4) against Table 1 (a second rounded constant)

- **Location:** Equation (4) of 4.2.3 and Table 1 immediately beneath it, both
  on printed page 4 (PDF page 14), against the last column of Table C.6 on
  printed page 21 (PDF page 31) and Table C.10 on printed page 24 (PDF
  page 34).
- **The print:** Equation (4) closes
  $D_\text{Norm} = 10\lg\!\left(\sum_j 10^{(D_j + P_j)/10}\right)$ dB
  $-\ 6,2$ dB, and Table 1 gives the $P_j$ of the A-weighted pink-noise
  reference spectrum as $-16{,}1$; $-8{,}6$; $-3{,}2$; $0$; $1{,}2$; $1$ dB at
  125 Hz to 4 kHz.
- **The problem:** the 6,2 dB is the energy sum of the $P_j$, which is what
  normalizes the weighted spectrum back to unit total so that a flat curve
  comes back unchanged, and the six printed $P_j$ sum to 6,251 5 dB, which
  rounds to 6,3 and not to 6,2. The printed constant is 0,051 dB short of the
  printed table. The two are roundings of the same curve made separately:
  the $P_j$ are the A-weighting of IEC 61672-1 at the six octave centres,
  $-16{,}19$; $-8{,}67$; $-3{,}25$; $0$; $1{,}20$; $0{,}96$ dB, printed to
  one decimal as that standard tabulates them, and the energy sum of the
  unrounded curve is 6,23 dB, which prints as the 6,2 of Equation (4). Each
  rounding is right on its own and the printed equation is not: evaluated as
  printed, it returns a flat curve 0,05 dB high. It is the same kind of slip
  as the rounded $\lg 2$ of the entry above, a constant printed to one decimal
  where the document computes to more, and Equation (3), of which Equation
  (4) is the special case for the Table 1 spectrum, carries the same
  normalization exactly, as the logarithm of its denominator.
- **Evidence:** Equation (4), its key and Table 1 read on the page in four
  printings, which agree character for character: ISO 14257:2001(E), PDF
  page 10 (printed p. 4); EN ISO 14257:2001 as published in
  BS EN ISO 14257:2001, PDF page 14 (printed p. 4); UNE-EN ISO 14257:2002,
  PDF page 9 (printed p. 9); and DIN EN ISO 14257:2011-11, PDF page 13
  (printed p. 9), whose national foreword lists the technical errors corrected
  in the German text and does not name this one. The annex settles which
  constant it was computed with. Run from the printed Tables C.2 to C.4
  through Annex B without rounding, the last column of Table C.6 comes back
  with the six printed $P_j$ and their own sum, 6,251 5 dB, inside the
  printed rounding at all 11 positions (worst 0,041 dB, departures of both
  signs), and with the printed 6,2 dB one unit high in the last place at 6 of
  the 11 (worst 0,092 dB, every departure positive, from +0,011 to
  +0,092 dB). Table C.10 does the same: +0,040, +0,004 and +0,045 dB with the
  sum, +0,091, +0,055 and +0,097 dB with 6,2. The unrounded A-weighting with
  its own sum lands the same 14 cells inside the rounding (worst 0,047 dB),
  so the annex does not say which of the two exact normalizations it used,
  only that it used one; with the printed 6,2 dB neither weighting does
  (8 and 9 of 14 outside). Over the printed, already rounded octave columns
  of Table C.6 the split is 3 of 11 against 7 of 11. Table C.8, a slope,
  does not see the constant, and the A-weighted 115,7 dB of Table C.2 adds it
  back. Verified on PDF page 14 (printed p. 4) of EN ISO 14257:2001 for the
  equation and the table, and on PDF pages 31 and 34 (printed pp. 21 and 24)
  of the same document for the two annex tables.
- **Consequence for the standard's own tables:** none for the annex, which
  was normalized exactly. What carries the 0,051 dB is every evaluation of the
  printed equation, which stands that much above the annex on each
  frequency-normalized value and can move a printed cell of Tables C.6, C.10
  and C.12 by one in the last place, always upward, and never by more.
- **Library behaviour:**
  [`NORMALIZED_OFFSET_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) carries the
  printed 6,2, on the same rule as the entry above and as the 11 of
  Equation (2): the printed constant is what a reader checking against the
  page will use, and four printings print it. The exact normalization is
  Equation (3) with the Table 1 weights as the machine spectrum, which
  [`spectrum_distribution_value`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py)
  computes, so the annex's reading is available without a second constant.
  The conformance row "ISO 14257:2001 Annex C, Table C.6 last column" judges
  the printed constant against the annex at 0,1 dB and says why, the row
  "ISO 14257:2001 Eq. (4) against Annex C, Table C.6 last column and Table
  C.10" records that the exact sum lands all fourteen values inside the
  printed rounding and the printed constant does not, and
  `test_the_annex_normalized_with_the_table_one_sum_and_not_the_printed_offset`
  in [`tests/room/test_spatial_decay.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_spatial_decay.py)
  holds both counts so that neither the constant nor the tolerances can
  drift.
- **Status:** not reported.

## ISO 14257:2001, Annex C, Tables C.11 and C.12 (results Equation (8) does not give)

- **Location:** Tables C.11 and C.12 on printed page 24 (PDF page 34), against
  Equation (8) of 6.4.3 on printed page 10 (PDF page 20) and Table C.5 on
  printed page 21 (PDF page 31).
- **The print:** Table C.11 gives $\text{DL}'_\text{fr}$ in six octave bands at
  4 m, 10 m and 30 m from the source: 6,2; 4,0; 4,4; 5,2; 5,3; 3,9 at 4 m;
  7,8; 5,4; 6,4; 6,9; 7,7; 5,8 at 10 m; and 10,6; 7,4; 9,3; 7,2; 9,2; 6,1 at
  30 m. Table C.12 gives 4,8; 6,8; 8,0 dB for the A-weighted pink-noise
  spectrum at the same three distances.
- **The problem:** Equation (8) is the only thing in the document that defines
  $\text{DL}'_\text{fr}$, and it does not produce these numbers. Evaluated over
  the three distance ranges the same annex uses, 2 m to 5 m, 5 m to 24 m and
  24 m to 48 m, on the printed $D$ of Table C.5, it departs from Table C.11 by
  up to 1,55 dB, and the printed rows are not an Equation (8) result for any
  decay rate: solving the equation for the $\text{DL}_2$ the middle row would
  need gives values from -28,9 dB to +20,7 dB per distance doubling. What the
  three rows are is a reading of the printed measurement at a microphone
  position, through Equation (6) rather than Equation (8): the 4 m row is
  Equation (6) at the 4 m position of Table C.5, in all six bands; the 10 m row
  is the mean of Equation (6) at the 8 m and 12 m positions that bracket it, in
  all six bands; and the 30 m row is Equation (6) at the 32 m position with
  $20\lg 32$ entered as 30 dB rather than 30,103 dB, in five bands of six.
- **Evidence:** Tables C.10, C.11 and C.12 read on PDF page 34 (printed p. 24),
  Tables C.5 and C.6 on PDF page 31 (printed p. 21) and Equations (6), (7) and
  (8) with their keys on PDF page 20 (printed p. 10), all of
  EN ISO 14257:2001. Seventeen of the
  eighteen cells of Table C.11 come back from the printed $D$ of Table C.5 by
  the reading above, to the tenth the table prints; the exception is the
  125 Hz cell of the 30 m row, which prints 10,6 where that reading gives 10,7.
  The same digits are printed in the Spanish adoption, UNE-EN ISO 14257:2002,
  Tabla C.11 on printed p. 30, so this is the annex and not one printing of it.
- **Consequence for the standard's own tables:** Tables C.11 and C.12 only. The
  decay rates and excesses of Tables C.7 to C.10 are unaffected, and nothing
  downstream computes with C.11.
- **Library behaviour:**
  [`level_excess_at`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) implements
  Equation (8) as printed and returns the values above rather than the table's.
  The conformance row "ISO 14257:2001 Annex C, Tables C.11 and C.12" records
  the departure so the table is not mistaken for an oracle of Equation (8).
- **Status:** not reported.

## ISO 11690-3:1998, Table C.2 (a value read off the edge of its own diagram)

- **Location:** Table C.2 on printed page 20 (PDF page 30), against Figure C.1
  on printed page 19 (PDF page 29).
- **The print:** the row for machine M8 gives $L_{WA} - L_{pA}$ = 29 dB,
  $\Delta L_A$ = 10 dB and $L'_{pA}$ = 88 dB, in a room whose equivalent
  absorption area C.2.2 puts at 195 m2.
- **The problem:** Figure C.1, the diagram the annex says to read $\Delta L_A$
  off, has a vertical axis that ends at 10 dB, and the curve for a 29 dB
  difference leaves the top of it well before 195 m2. The 10 dB in the table is
  the edge of the diagram rather than a reading of it, and the level it carries
  into the last column is 2,4 dB low.
- **Evidence:** the axis of Figure C.1 runs 0 dB to 10 dB, and the closed form
  the diagram draws, the environmental correction
  $\Delta L_A = 10 \lg(1 + 4S/A)$ of ISO 3744 with
  $S/S_0 = 10^{(L_{WA}-L_{pA})/10}$, gives 12,4 dB for that row. The same
  expression reproduces the other seven rows of the table within 0,4 dB, which
  is the half decibel the diagram is drawn to. Verified on PDF pages 29 and 30
  (printed pp. 19 and 20) of EN ISO 11690-3:1998 as published in
  BS EN ISO 11690-3:1999.
- **Consequence for the standard's own tables:** the last column of that one
  row. Nothing else in the document computes with it.
- **Library behaviour:**
  [`workstation_level_increase`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/workroom_prediction.py)
  evaluates the expression and has no ceiling, so it returns 12,4 dB where the
  table prints 10. The conformance row "ISO 11690-3:1998 Annex C, Figure C.1
  (the eighth machine)" pins it.
- **Status:** not reported.

## ISO 11690-3:1998, Annex B (two workstations whose positions and results are interchanged)

- **Location:** Tables B.5 and B.8 on printed page 18 (PDF page 28), against
  Figure B.1 on printed page 16 (PDF page 26) and the immission columns of
  Tables B.6 and B.9 on printed page 18.
- **The print:** Table B.5 puts workstation W1 at $x$ = 3 m, $y$ = 12 m,
  $z$ = 1,6 m and W2 at 17 m, 4 m, 1,6 m, and Table B.8 repeats those two
  positions for case B. Table B.6 then gives, after the two machines are
  installed, $L_p$ = 82,1 dB at W1 and 80,3 dB at W2; Table B.9 gives 86,2 dB
  at W1 and 85,7 dB at W2 with the first-choice machine, and 83,8 dB and
  82,8 dB with the second. Figure B.1 draws the same two workstations the other
  way round: W1 beside machine M2 on the right of the room, and W2 alone at the
  top left.
- **The problem:** the results belong to the figure's assignment and not to the
  tables'. Machine M2 stands at 17 m, 3 m, 1 m, so the position Table B.5 calls
  W2 is 1,2 m from it and the position it calls W1 is 11,4 m from the nearer
  machine. The far position cannot be the louder of the two, and the
  printed levels say it is. Recomputing case A by the category 1 method the
  annex prescribes, in the 20 m by 15 m by 7 m room of Table B.2 at the mean
  absorption coefficient 0,15 of Table B.3, gives 82,10 dB at 17 m, 4 m, 1,6 m
  and 80,26 dB at 3 m, 12 m, 1,6 m: the two levels Table B.6 prints, each
  against the other workstation's label. Table B.8 contradicts itself on its own
  row, since it prints the far position for W1 and 82 dB, the rounded near
  level, beside it.
- **Evidence:** Figure B.1 with Tables B.2 and B.3 read on PDF page 26 (printed
  p. 16); Table B.4 with the machine positions on PDF page 27 (printed p. 17);
  Tables B.5 to B.9 on PDF page 28 (printed p. 18). All of EN ISO 11690-3:1998
  as published in BS EN ISO 11690-3:1999. Under the figure's assignment the six
  levels of Table B.9 come back within 0,07 dB, and under the tables', the four
  at W1 and W2 miss by 0,48 dB to 1,04 dB (W3 stands in the same place in both)
  while case A misses by 1,8 dB on both rows.
- **Consequence for the standard's own tables:** the Position columns of Tables
  B.5 and B.8 against the labels of Tables B.6 and B.9, in both cases of the
  annex. The prose of case A follows the tables, calling W2 "the workstation of
  M2", so it is on the same side of the contradiction. The numbers themselves
  are right.
- **Library behaviour:** the conformance rows for the two cases of Annex B read
  the printed coordinates and never the labels, and the row "ISO 11690-3:1998
  Annex B, Figure B.1 against Tables B.5 and B.8" records that the results
  reproduce at the positions the figure draws and at no other. The 50 dB of
  background Table B.5 prints against W1 goes with that label rather than with
  the coordinates beside it, so it is heard at the position the figure gives
  W1, next to machine M2. It is worth 0,004 dB: read the other way case A comes
  back 82,09 dB and 80,27 dB instead of 82,10 dB and 80,26 dB, and both
  readings round to the tenth Table B.6 prints.
- **Status:** not reported.

## ISO 11819-1:1997, Annex E (speed spreads that do not fit the regression printed beside them)

- **Location:** Annex E (informative), the example test report, table "Sound
  level and speed regression data (uncorrected for temperature)" on printed
  page 26 (PDF page 34). The print read here is BS EN ISO 11819-1:2001, which
  is identical to ISO 11819-1:1997.
- **The print:** for cars, dual-axle and multi-axle heavy vehicles the table
  gives regression slopes of 32,55, 18,76 and 26,74, correlation coefficients
  of 0,79, 0,51 and 0,49, standard deviations of sound level of 2,2, 2,5 and
  2,3 dB, average speeds of 88,5, 75,8 and 73,7 km/h and standard deviations
  of speed of 13,3, 7,5 and 6,4 km/h, the last two rows marked "Value
  converted from the logarithm of speed".
- **The problem:** a least-squares line of level on $\lg v$ obeys
  $b = r\,s_L / s_{\lg v}$ exactly, so the slope, the correlation and the
  level spread printed in one column fix the spread of $\lg v$ of that column:
  $s_{\lg v} = r\,s_L/b$ = 0,0534 for the cars, 0,0680 for the dual-axle and
  0,0421 for the multi-axle heavy vehicles (0,0518 to 0,0550, 0,0659 to 0,0700
  and 0,0408 to 0,0435 across the rounding of the three printed inputs). The
  dual-axle vehicles therefore have the widest spread of $\lg v$ of the
  three. The ratio of the standard deviation of the speed to its mean depends
  on that spread alone: to first order it is $\ln 10 \, s_{\lg v}$, which
  gives 0,123 for the cars, 0,157 for the dual-axle and 0,097 for the
  multi-axle vehicles, and for a log-normal speed it is
  $\sqrt{\exp[(\ln 10 \, s_{\lg v})^2] - 1}$, which gives 0,123, 0,158 and
  0,097, with the dual-axle vehicles the widest either way. The printed
  standard deviations divided by the printed means give 0,150, 0,099 and
  0,087, with the cars the widest, so the two columns cannot come from the
  same pass-bys. To first order,
  $s_v \approx \bar v \ln 10 \, s_{\lg v}$ gives 10,9, 11,9 and 7,2 km/h where
  13,3, 7,5 and 6,4 km/h are printed.
- **Evidence:** the other columns of the same table agree with one another.
  The line through the mean speed gives the mean level printed beside it
  ($16{,}6 + 32{,}55 \lg 88{,}5 = 79{,}97$, printed 80,0; 81,76 and 84,44,
  printed 81,8 and 84,4), which also shows the average speed to be
  $10^{\overline{\lg v}}$; and $s_L\sqrt{1 - r^2}$ gives 1,35, 2,15 and
  2,00 dB, which agree with the residual standard deviations printed as 1,3,
  2,1 and 2,0 dB within the rounding of the printed $r$ and $s_L$ (1,30 to
  1,39, 2,10 to 2,20 and 1,96 to 2,06 dB across it, and 1,31 to 1,40, 2,13 to
  2,24 and 1,97 to 2,08 dB with the $n - 2$ denominator of a residual). Only
  the row of speed spreads is out of step, and it stays out of step across the
  same rounding. Verified on PDF page 34
  (printed p. 26) of BS EN ISO 11819-1:2001.
- **Consequence for the standard's own example:** none for the vehicle sound
  levels, which need only the intercepts and the slopes. The 9.3 check the
  example passes still passes with the spreads the regression implies: the
  reference speeds of 80 and 70 km/h fall inside 73,6 to 106,4, 64,8 to 88,6
  and 66,9 to 81,2 km/h.
- **Library behaviour:**
  [`PassByRegression`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/statistical_pass_by.py)
  reports the spread of $\lg v$ and the 9.3 window in km/h it gives, and the
  conformance suite does not use the printed speed spreads as an oracle.
- **Status:** unreported.

## ISO 11819-1:1997, Annex D (a table numbered after the next annex)

- **Location:** Annex D (informative), "Example of a normalized reference
  surface", printed page 22 (PDF page 30).
- **The print:** the one table of Annex D is captioned "Table E.1 — Example of
  surfaces, with sound level data, used to establish a normalized reference
  case for the medium speed range".
- **The problem:** a table of an ISO annex is numbered after the annex it
  stands in, so this one is Table D.1. Annex E, which the number points to,
  holds a report form whose boxes carry no table numbers, so the label names a
  table that does not exist.
- **Evidence:** Verified on PDF page 30 (printed p. 22) and PDF pages 31 to 34
  (printed pp. 23 to 26) of BS EN ISO 11819-1:2001.
- **Library behaviour:** none needed.
  `SPB_ANNEX_D_SURFACES_DB` cites the table by its annex and says it is
  printed as "Table E.1".
- **Status:** unreported.

## Mechel (2008), Table 3 (a wall impedance its own Equation (11) does not give)

- **Location:** Table 3, "Density and elastic constants of materials", the row
  "PVC, 30% softener" on printed page 530 (PDF page 545), against Equation
  (11) on printed page 529 (PDF page 544). Non-normative source: a textbook.
- **The print:** the row gives $\rho$ = 1250 kg/m3, $f_{cr}d$ = 48 Hz m and
  $Z_m$ = 1220, with the modulus and the loss-factor columns empty. Equation
  (11), on the facing page, reads
  $F := f/f_{cr}\ ;\ Z_m := f_{cr}m/Z_0 = (f_{cr}d/Z_0)\,\rho$.
- **The problem:** with this row's own density and $f_{cr}d$, that definition
  gives $1250 \times 48 / 413 = 145$. The printed 1220 is 8,4 times it.
- **Evidence:** the same expression reproduces the rest of the table over four
  decades of $Z_m$, from 20 to 1438: thirty-six of the other thirty-seven rows
  within 5 per cent and thirty-four within 3 per cent. The one other row
  outside that band is not a defect either, and shows what one looks like when
  it is not: "Plaster board" prints $Z_m$ = 85 as a single value where its
  $f_{cr}d$ is the range 31 to 35, and 85 is the top of the band the equation
  gives rather than its middle. The conclusion does not turn on the value
  taken for $Z_0$, which the equation writes as a symbol: 400 gives 150 and
  415 gives 144,6, against a printed 1220. Verified against the page as
  printed on PDF pages 544 and 545 (printed pp. 529 and 530) of Mechel
  (2008), *Formulas of Acoustics*, 2nd edition.
- **Consequence for the book's own tables:** that one cell. Nothing else in
  the document computes with it, and the row's density and $f_{cr}d$, which
  are the two columns this library reads, are consistent with each other.
- **Library behaviour:** the catalogue holds the density, the $f_{cr}d$ and
  the loss factor of each row and does not hold $Z_m$, which is a wall
  impedance ratio rather than a property of the material. The row carries the
  discrepancy in its note. The tests
  `test_the_printed_wall_impedance_follows_from_the_books_own_equation` and
  `test_the_one_row_that_does_not_is_the_one_the_errata_names` in
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) pin
  both halves of the evidence.
- **Status:** not reported.

## Bies 5e (2017), Table C.1 (three speeds that do not follow from the two columns they are said to be calculated from)

- **Location:** Table C.1, "Properties of materials", the rows "Brick" and
  "Cork" on printed page 719 (PDF page 748) and "Plywood (fir)" on printed page
  720 (PDF page 749), against the text on printed page 717 (PDF page 746).
  Non-normative source: a textbook.
- **The print:** printed page 717 says "The speed of sound values in column 4
  of Table C.1 were calculated from the values in columns 2 and 3", which are
  the Young's modulus in $10^9$ N/m2 and the density in kg/m3. The three rows
  give, in that order, $E$ = 24 and $\rho$ = 2000 with a speed of 3650 m/s;
  $E$ = 0,1 and $\rho$ = 250 with 500 m/s; and $E$ = 8,3 and $\rho$ = 600 with
  4540 m/s.
- **The problem:** $\sqrt{E/\rho}$ on those cells gives 3464, 632 and 3719 m/s.
  The printed speeds are 5,4 per cent above, 20,9 per cent below and 22,1 per
  cent above what the two columns beside them give.
- **Evidence:** the same expression reproduces the rest of the table. Of the
  eighty-seven rows that print both the modulus and the density as single
  values, seventy-nine agree within 1 per cent and eighty-four within 3, with a
  median offset of 0,03 per cent, across speeds from 190 to 27000 m/s. Only
  these three fall outside, which is the signature of a misprinted cell rather
  than of a looser method than the page describes. Which cell is misprinted
  cannot be told from the page: 4540 m/s would follow from a modulus of 12,4
  rather than 8,3, and 500 m/s from a density of 400 rather than 250. Verified
  against the page as printed on PDF pages 748 and 749 (printed pp. 719 and
  720) of Bies, Hansen and Howard (2017), *Engineering Noise Control*, fifth
  edition.
- **Consequence for the book's own tables:** three cells. Nothing else in the
  document computes with them.
- **Library behaviour:** the catalogue holds the three columns as printed and
  derives nothing over them, and each of the three rows carries the
  disagreement in its note. The test
  `test_three_rows_do_not_follow_from_their_own_two_columns` in
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) pins
  the three, and `test_the_rest_of_the_table_reproduces_to_three_per_cent`
  pins the eighty-four that do follow, which is what makes the three a defect.
- **Status:** not reported.

## Bies 5e (2017), Table C.2 (four molar masses that do not belong to the gas in the row)

- **Location:** Table C.2, "Molecular weights and ratios of specific heats for
  some commonly used gases", the rows "Ammonia", "Fluorine", "Freon 22" and
  "Nitric oxide" on printed page 722 (PDF page 751). Non-normative source: a
  textbook.
- **The print:** the four rows give, in the column headed "Molecular weight,
  $M$ kg/mole", 0.01730, 0.01900, 0.08047 and 0.06301.
- **The problem:** the molar mass of a gas follows from the molecule the row
  names, and none of these four does. Ammonia is NH$_3$ at 17.031 g/mol, not
  17.30. Fluorine gas is F$_2$ at 37.996 g/mol, and 19.00 is the atomic mass of
  one fluorine atom. Freon 22 is CHClF$_2$ at 86.465 g/mol, not 80.47. Nitric
  oxide is NO at 30.006 g/mol, and 63.01 is the molar mass of nitric *acid*,
  HNO$_3$.
- **Evidence:** the rest of the table settles that these are misprints rather
  than a looser convention. Thirty-five of the thirty-seven rows name a
  molecule whose formula mass can be computed; the two that do not are the
  mixtures, air and natural gas. Of those thirty-five, thirty-one reproduce
  their formula mass to better than 0.05 per cent, and the two that are further
  out are further out only because the page rounds: helium at 4.00 against
  4.0026 is 0.07 per cent low and hydrogen at 2.02 against 2.016 is 0.20 per
  cent high, both of them the last printed digit. So the table's own precision
  is two parts in a thousand, against which the four exceptions are 1.6, 6.9,
  50.0 and 110.0 per cent out. Two of them land exactly on a different
  species, which is what a copying slip looks like: 19.00 is atomic fluorine to
  0.01 per cent and 63.01 is HNO$_3$ to 0.003 per cent, the same accuracy the
  correct rows have. The ratio of specific heats printed beside each of the
  four points the same way: 1.36 for fluorine and 1.40 for nitric oxide are
  diatomic values, so the rows mean F$_2$ and NO whatever their mass column
  says. An independent table of the same genre agrees on both counts: the
  Masoneilan *Control Valve Sizing Handbook* (Baker Hughes, BHMN-19540C, 2022),
  which tabulates the same two quantities for the same purpose, prints
  "Fluorine, F$_2$" with a ratio of specific heats of 1.36 on its page 19 and
  "Ammonia, NH$_3$" with a molecular weight of 17.0 on its page 20. Verified
  against the page as printed on PDF page 751 (printed p. 722) of Bies, Hansen
  and Howard (2017), *Engineering Noise Control*, fifth edition, and on pages
  19 and 20 of the Masoneilan handbook.
- **Consequence for the book's own tables:** four cells. Nothing else in the
  document computes with them; the table is offered for the control valve noise
  of Section 10.8, where the gas is chosen by the reader. A reader who did take
  one of the four would get a speed of sound 0.8 per cent low for ammonia, 3.7
  per cent high for Freon 22, 41.4 per cent high for fluorine and 31.0 per cent
  low for nitric oxide, since $c = \sqrt{\gamma R T / M}$.
- **Library behaviour:** the catalogue holds the row and its ratio of specific
  heats, and refuses the molar mass rather than serving it: reading it raises,
  naming the cell, quoting what the page prints and pointing here. The tests
  `test_a_cell_the_errata_names_is_not_served_as_a_value` and
  `test_the_refusal_quotes_the_printed_number_and_points_at_the_registry` in
  [`tests/fluids/test_gas_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas_catalogue.py)
  pin both halves, and `test_no_other_cell_of_either_table_is_called_wrong`
  keeps the claim from spreading to a fifth row.
- **Status:** not reported.

## Bies 5e (2017), Table C.2 (two ratios of specific heats that no gas can have)

- **Location:** Table C.2, "Molecular weights and ratios of specific heats for
  some commonly used gases", the rows "Hydrogen fluoride" and "Octane" on
  printed page 722 (PDF page 751). Non-normative source: a textbook.
- **The print:** the column headed "Ratio of specific heats, $\gamma$" gives
  0.97 for hydrogen fluoride and 1.66 for octane.
- **The problem:** the column is the ratio of specific heats, which its own
  heading names as such and which the table exists to feed into the control
  valve procedure the appendix points at, "particularly useful for calculating
  control valve noise (see Section 10.8)". For any substance in a stable single
  phase $c_p \geq c_v$, so $\gamma \geq 1$ and a printed 0.97 is outside what
  the quantity can be. That is a statement about $c_p/c_v$ and not about every
  exponent an engineer might write as $k$: the real-gas isentropic exponent of
  a strongly associating vapour, which is what hydrogen fluoride is, can fall
  below 1, but it is a different quantity from the one this column names and
  not the one the procedure downstream wants. The octane cell is outside the
  column in the other direction: for an ideal gas $\gamma = 1 + 2/f$ where $f$
  counts the active degrees of freedom, and $f \geq 3$ always, so
  $\gamma \leq 5/3 \approx 1.667$ with equality only for a monatomic one.
  Octane is C$_8$H$_{18}$, twenty-six atoms, with three rotational degrees of
  freedom on top of the three translational ones before any vibration is
  counted, which caps it at $\gamma \leq 4/3$ and puts it near 1.05 in
  practice. That bound is an ideal-gas one, and a real fluid does pass 5/3 near
  its critical point; what rules out reading the cell that way is that this is
  an ideal-gas column, printed against ideal molar masses, giving one value per
  gas rather than one per state.
- **Evidence:** the column is otherwise a clean function of molecular
  complexity, which is what makes the two exceptions visible. The three
  monatomic gases print 1.64 to 1.67, the diatomic ones 1.31 to 1.41, and the
  polyatomic ones fall away with size down to 1.05. Octane's two nearest
  neighbours in that progression are in the same table and one carbon apart:
  n-heptane prints 1.05 and pentane 1.06, so the table itself says what an
  alkane of this size does. Hydrogen fluoride's neighbours are the other
  diatomic rows, and hydrogen chloride, the next halide down, prints 1.41.
  Outside the book, the Masoneilan *Control Valve Sizing Handbook* (Baker
  Hughes, BHMN-19540C, 2022) prints 1.05 for octane in the same $c_p/c_v$
  column on its page 19, between 1.66 for helium and 1.07 for pentane, so the
  progression is not a habit of one author. Verified against the page as
  printed on PDF page 751 (printed p. 722) of
  Bies, Hansen and Howard (2017), *Engineering Noise Control*, fifth edition,
  with both cells re-read at six times magnification: 0.97 and 1.66 are what
  the page prints, with no digit in doubt.
- **Consequence for the book's own tables:** two cells. A reader taking the
  octane row would get a speed of sound 26.0 per cent high; the hydrogen
  fluoride row cannot be used at all, because a speed of sound computed from a
  $\gamma$ below 1 is not the speed of anything.
- **Library behaviour:** the catalogue holds the row and its molar mass, and
  refuses the ratio rather than serving it, the same way and with the same
  message as the four molar masses above. The independent guard is
  [`phonometry.fluids.ideal_gas`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/gas.py), which
  refuses a ratio at or below 1 whoever passes it, and
  `test_a_ratio_of_specific_heats_at_or_below_one_is_refused` in
  [`tests/fluids/test_gas.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas.py) pins that.
- **Status:** not reported.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Appendix D (two rows the table cannot tell apart)

- **Location:** Appendix D, "Random incidence scattering coefficient table",
  the group "Pyramids [6]", on printed pages 499 and 500 (PDF pages 556 and
  557). Non-normative source: a textbook.
- **The print:** the group holds four rows. Printed page 499 carries
  "$h = 30.5$ cm, $L = b = 2h$" and then the same description again with the
  continuation line "One in four pyramid corners raised from baseplate" under
  it. Printed page 500 carries "$h = 30.5$ cm, $L = b = h$" and then, once
  more, "$h = 30.5$ cm, $L = b = 2h$" with the same continuation line under
  it.
- **The problem:** the second and the fourth rows are printed with the same
  description, the same continuation line and different numbers: 0.38 against
  0.44 at 1 kHz, 0.74 against 0.76 at 2 kHz, and 1.00 against an en dash at
  5 kHz. Nothing printed beside either row distinguishes it from the other, so
  a reader who looks up "the 30.5 cm pyramids with one corner in four raised"
  finds two answers and no way to choose. A table of measured values has to
  identify its rows; this one does not.
- **Evidence:** both pages read at six times magnification. The labels are
  character for character the same, the continuation lines are the same, and
  the values differ in thirteen of the eighteen bands, agreeing only at 100,
  125, 160, 200 and 4000 Hz. The block's own
  structure is what makes the reading plain: the table pairs a plain surface
  with a modified one, and printed page 499 pairs $L = b = 2h$ with its
  modified version. Printed page 500 opens with $L = b = h$, so its second row
  is where the modified $L = b = h$ belongs, which would make the printed "2h"
  the defect. That is a reading of the pattern rather than something the page
  states, and the source the group is credited to, Sharma and Bradley,
  *J. Acoust. Soc. Am.* 134(5), 4095 (2013), is a one-page meeting abstract
  that this library has not read, so the errata records what the page does and
  not what it should have said. Verified on PDF page 556 (printed p. 499) and
  PDF page 557 (printed p. 500) of Cox and D'Antonio (2017), Acoustic Absorbers
  and Diffusers, third edition.
- **Library behaviour:** both rows are kept, with the description and the
  continuation line as printed. Their keys carry the printed folio, which is
  the only thing that separates them, and
  `test_two_pyramid_rows_are_told_apart_only_by_the_page_they_sit_on` in
  [`tests/materials/diffusers/test_scattering_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_scattering_catalogue.py)
  pins that they stay two rows with two spectra.
- **Status:** not reported.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Appendix B (a width in centimetres that its own geometry makes metres)

- **Location:** Appendix B, "Normalized diffusion coefficient table", section 1,
  the first surface of the width series, on printed page 482 (PDF page 539).
  Non-normative source: a textbook.
- **The print:** the section is headed "Effect of changing diffuser periodicity
  and width. Semicylinder(s) non-absorbing surfaces, radius 0.3 m (1 cm flat
  section between each period)", and its five surfaces are listed as "1 period,
  0.61 cm wide", "2 periods, 1.22 m wide", "4 cylinders, 2.44 m wide",
  "6 periods, 3.66 m wide" and "12 periods, 7.32 m wide".
- **The problem:** the first width is in centimetres and the other four are in
  metres, and the series doubles: 0.61, 1.22, 2.44, and then 3.66 and 7.32,
  which are six and twelve of the first. One period of the surface the heading
  describes is a semicylinder of radius $0.3$ m plus the $1$ cm flat section,
  so $2 \times 0.3 + 0.01 = 0.61$ m. A width of 0.61 cm is six millimetres, a
  hundredth of what the heading's own geometry gives and a hundredth of what
  the rest of the series requires.
- **Evidence:** the same surface is listed in Table C.3 of the next appendix,
  under a heading with the same geometry, and there it reads "1 period, 0.61 m
  wide". The book therefore prints both spellings of one surface twelve pages
  apart, and the metric one is the one its arithmetic supports. Verified on PDF
  page 539 (printed p. 482) and PDF page 549 (printed p. 492) of Cox and
  D'Antonio (2017), *Acoustic Absorbers and Diffusers*, third edition, with the
  unit re-read at six times magnification on both pages: the appendix really
  prints "cm" and Table C.3 really prints "m".
- **Consequence for the book's own tables:** the description of one surface,
  and of the three rows that carry it. The numbers beside it are unaffected,
  which is what makes the defect easy to miss and worth recording: a reader
  comparing a measured semicylinder against this row would be comparing against
  a 0.61 m device whatever the label says.
- **Library behaviour:** the row keeps the width as printed, because a
  catalogue that silently corrected it would be claiming a reading the page
  does not make. The three rows of the surface are keyed on it and
  `test_every_section_heading_is_kept_whole` in
  [`tests/materials/diffusers/test_diffusion_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_diffusion_catalogue.py)
  pins that the heading with the geometry travels with them, which is what
  lets a reader see the contradiction.
- **Status:** not reported.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Table 6.7 (six porosities printed in per cent in a column of fractions)

- **Location:** Table 6.7, "Effective flow resistivity values for ground
  surfaces and other parameters", the column "Porosity", on printed pages 200
  and 201 (PDF pages 257 and 258). Non-normative source: a textbook.
- **The print:** the column is headed "Porosity" and states no unit, where
  the column beside it is headed "Water content (%)". Every porosity it prints
  is a fraction between 0.15 and 1 ("0.5–0.9" for snow, "0.24" for the sports
  field, "0.44" for fine sand, "0.34–1" and the like for the fitted grasses),
  except on six rows: "Mineral layer beneath mixed deciduous forest" 36.5,
  "Humus on pine forest floor" 58.1, "Pine forest litter (6–7 cm thick)" 38.9,
  "Grass root layer in loamy sand" 48 ± 4, "Loamy sand" 37.5 and "Bare sandy
  plain" 26.9.
- **The problem:** a porosity is the fraction of a volume that is open, so it
  cannot pass 1, and these six are percentages printed in a column that states
  no unit and holds fractions everywhere else. Read in the column's own unit
  they are porosities of 26.9 to 58.1, which no material has; read as per cent
  they are 0.269 to 0.581, which is what soils like these are. The page leaves
  the reader to work out which, and a program that reads the column as printed
  takes the impossible value.
- **Evidence:** Verified on PDF page 257 (printed p. 200) and PDF page 258
  (printed p. 201) of Cox and D'Antonio (2017), *Acoustic Absorbers and
  Diffusers*, third edition: the heading prints no unit, and the six cells
  print the values quoted, the fourth as "48 ± 4".
- **Library behaviour:** in
  [`PUBLISHED_GROUND`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/ground_surfaces.py)
  the six rows leave `GroundSurface.porosity`, which is a fraction from 0 to 1,
  empty, and hold the cell as `misprinted`: `why_missing("porosity")` and the
  refusal of `printed("porosity")` quote the figure the page prints, the
  ± 4 included, and say why it is not served. The library does not convert it
  to 0.365 and so on, because the page does not print the unit that
  conversion would assume. Every catalogue row checks when it is built that a
  porosity is a fraction.
  `test_the_six_percent_porosities_of_cox_are_held_as_misprinted` and
  `test_why_a_per_cent_porosity_is_missing_quotes_the_page` in
  [`tests/io/test_catalogue_row_contract.py`](https://github.com/jmrplens/phonometry/blob/main/tests/io/test_catalogue_row_contract.py)
  pin the six.
- **Status:** unreported.

## Ver & Beranek 2e (2006), TABLE 14.1 (three moduli whose e-notation is corrupted in the printing)

- **Location:** TABLE 14.1, "Properties of Some Commercial Damping Materials",
  on printed page 598 (PDF page 599), in chapter 14, "Structural Damping", by
  Eric E. Ungar and Jeffrey A. Zapfe. Non-normative source: a handbook.
- **The print:** the four moduli columns are set in a notation the table
  defines in its own footnote c: "The number following e represents the power
  of 10 by which the number preceding e is to be multiplied; e.g., 1.2e3
  represents $1.2 \times 10^3$". Every cell of the block obeys it except
  three. Antiphon-13 prints `3.e3e` under $E_{I,\max}$; Soundcoat DYAD 606
  prints `3G5` under $E_{\max}$; and GE SMRD prints `e35` under $E_{\max}$.
- **The problem:** none of the three is a number in that notation. `3.e3e`
  ends with an exponent marker that has no digit after it and has a decimal
  point with no fraction before the first marker; `3G5` puts a capital G where
  the marker belongs, and a capital G appears nowhere else in the table; `e35`
  leads with the marker and has no mantissa at all. A reader cannot recover
  the intended value, because each one is consistent with more than one
  reading: `3.e3e` could be $3 \times 10^3$ with a stray marker or
  $3.3 \times 10^{-3}$ of some other setting, and `e35` could be
  $3 \times 10^5$ or $3.5 \times 10^{?}$.
- **Evidence:** Verified on PDF page 599 (printed p. 598) of Ver & Beranek,
  *Noise and Vibration Control Engineering* 2e (2006). The three strings are
  legible and are what the page carries; the surrounding cells of the same
  block are equally legible and obey the notation, so the defect belongs to
  the printing. The neighbouring columns do not settle any of the three
  either. For Antiphon-13 the chapter's own relation
  $E_{I,\max} \approx \eta_{\max} E_{\mathrm{trans}}$ gives
  $1.8 \times 1.9 \times 10^4 = 3.4 \times 10^4$ psi, which is consistent with
  a mantissa of 3 and an exponent of 4, but the printed string offers 3 and
  no legible exponent, and this library does not publish a value it had to
  finish itself.
- **What the library does:** the three cells are held as `misprinted` in
  [`PUBLISHED_DAMPING`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/damping.py), so the row keeps
  what the book prints and refuses to serve it as a number. Asking for one of
  them by `printed()` raises and names the glyphs. Every other cell of the
  seventeen rows is served normally.
- **Status:** unreported.

## Ver & Beranek 2e (2006), TABLE 14.1 (a transition modulus printed below the smallest modulus of its own row)

- **Location:** TABLE 14.1, "Properties of Some Commercial Damping Materials",
  row "3M ISD-113", on printed page 598 (PDF page 599), in chapter 14,
  "Structural Damping", by Eric E. Ungar and Jeffrey A. Zapfe. Non-normative
  source: a handbook.
- **The print:** the row reads $\eta_{\max} = 1.1$, peak temperatures of
  $-45$, $-20$ and $15\,^\circ\mathrm{F}$, and the four moduli
  $E_{\max} = 1.5\mathrm{e}5$, $E_{\min} = 3\mathrm{e}2$,
  $E_{\mathrm{trans}} = 2.1\mathrm{e}2$ and
  $E_{I,\max} = 2.3\mathrm{e}2$ psi.
- **The problem:** the same page defines $E_{\min}$ as "the smallest value of
  $E$", in the paragraph under the table and again in footnote c, where
  $E_{\max}$ is said to apply at low temperatures, $E_{\min}$ at high ones and
  $E_{\mathrm{trans}}$ in the range of $\eta_{\max}$, which lies between them.
  Here $E_{\mathrm{trans}} = 2.1 \times 10^2$ psi is smaller than
  $E_{\min} = 3 \times 10^2$ psi, so one of the two cells contradicts the
  definition the page gives for the other. The page does not say which. The
  printed $E_{\mathrm{trans}}$ is supported by its neighbour through the
  chapter's own $E_{I,\max} \approx \eta_{\max} E_{\mathrm{trans}}$:
  $1.1 \times 2.1 \times 10^2 = 2.3 \times 10^2$ psi, which is exactly what
  $E_{I,\max}$ prints. Against that, every one of the other fourteen rows that
  prints all three moduli puts $E_{\mathrm{trans}}$ one to two orders of
  magnitude above $E_{\min}$, which is where $E_{\min}$ would have to be for
  this row to behave like its neighbours. Neither reading can be had from the
  page alone.
- **Evidence:** Verified on PDF page 599 (printed p. 598) of Ver & Beranek,
  *Noise and Vibration Control Engineering* 2e (2006). All four cells of the
  row are legible and unambiguous in the notation footnote c defines, and so
  is the sentence that defines $E_{\min}$; the defect is a contradiction
  between two legible cells, not an illegible one. Taking
  $E_{\mathrm{trans}} / \sqrt{E_{\max} E_{\min}}$ as a shape test across the
  fifteen rows that print all three, the other fourteen fall between 0.976
  and 1.054 and this row gives 0.031.
- **What the library does:** both cells are served exactly as printed, because
  correcting either one would be this library choosing between two readings
  the page leaves open. The row carries a note saying so, which the published
  catalogue shows, and a test asserts the ordering holds on every other row so
  that a second occurrence cannot pass unnoticed.
- **Status:** unreported.

## Ver & Beranek 2e (2006), TABLE 8.5 (mass per unit area of the finest mesh, ten times too large in pounds)

- **Location:** TABLE 8.5, "Mechanical Characteristics and Flow Resistance
  $R_s$ of Wire Mesh Cloths", on printed page 262 (PDF page 266), in chapter
  8, "Sound-Absorbing Materials and Sound Absorbers". Non-normative source: a
  handbook.
- **The print:** every quantity of the table is printed twice, but only three
  of the four pairs are one quantity in two systems of units: the wire count,
  the wire diameter and the mass per unit area. The fourth prints the flow
  resistance in N s/m3 and again as a multiple of $\rho_0 c_0$. The mass per unit area column runs, in kg/m2 against
  lb/ft2: 1.6 / 0.32, then 1.2 / 0.25, then 0.63 / 0.13, then 0.48 / 0.1, and
  on the last row, the mesh of 80 wires per centimetre, 0.31 / 0.63.
- **The problem:** one pound per square foot is
  $0.45359237 / 0.09290304 = 4.8824$ kg/m2 by the definitions of the pound and
  the foot, so 0.31 kg/m2 is 0.063 lb/ft2 and not 0.63. The decimal point is
  one place too far right. Three things settle which of the two cells is the
  defective one. The four rows above convert to within the rounding of their
  own last digit, so the column is otherwise sound. The pound column as
  printed would make the finest mesh the heaviest cloth of the table, twice
  the mass of the coarsest, where every other column falls with the mesh.
  And the weave itself gives the mass: a square cloth of $n$ wires per metre
  of diameter $d$ carries $2 n \rho \pi d^2/4$ per unit area, which for 8000
  wires per metre of 57 $\mu$m wire of density $\rho = 7800$ kg/m3 is
  0.32 kg/m2, the printed 0.31 and not the printed 0.63. The page never says
  what the wire is made of, so that density is not read off it: 7800 kg/m3 is
  a stainless steel, and it is stated here because the argument is not
  reproducible without it. The same arithmetic at the same density reproduces
  the four rows above to within three per cent.
- **Evidence:** Verified on PDF page 266 (printed p. 262) of Ver & Beranek,
  *Noise and Vibration Control Engineering* 2e (2006). Two readers transcribed
  the page independently and both read the cell as three glyphs, "0.63", with
  no leading zero lost between them, and both read 0.31 in the cell beside it.
  The other four rows of the same column are equally legible and convert
  correctly, so the defect belongs to this cell and to the printing.
- **What the library does:** this catalogue publishes the SI column of each
  pair, so the defective cell reaches no value served from
  [`PUBLISHED_FLOW_RESISTANCE`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py).
  The row holds the printed 0.31 kg/m2, which the column and the weave both
  support, and its `note` quotes the pound cell and points here, so a reader
  reproducing the book sees what the book says without it reaching a
  calculation. The note and not the `misprinted` hedge: that hedge says a
  number is not served, and it is read back only from the cell it empties,
  while the defective cell here is the customary restatement, for which this
  catalogue holds no column at all.
- **Status:** unreported.

## Ver & Beranek 2e (2006), TABLE 8.6 (the two surface-density columns disagree by one wrong factor on every row)

- **Location:** TABLE 8.6, "Mechanical Characteristics and Flow Resistance
  $R_s$ of Glass Fiber Cloth", on printed page 263 (PDF page 267), in chapter
  8, "Sound-Absorbing Materials and Sound Absorbers". Non-normative source: a
  handbook.
- **The print:** the surface density is printed twice on each of the thirteen
  rows, in oz/yd2 and in g/m2: 3.16 / 96, 5.37 / 164, 6.70 / 204, 8.90 / 272,
  19.2 / 585, 17.7 / 535, 12.3 / 375, 1.87 / 57, 1.94 / 59, 9.60 / 293,
  14.5 / 442, 24.6 / 750 and 12.0 / 366.
- **The problem:** one ounce per square yard is
  $28.349523125 / 0.83612736 = 33.9057\ldots$ g/m2 by the definitions of the
  ounce and the yard, both exact. What is exact is the quotient; 33.906 is
  that quotient to three decimals, and this entry writes it that way whenever
  it is quoted short. The ratio the table prints is between 30.2 and
  30.6 on all thirteen rows and never once 33.9, so the two columns cannot
  both be right, and the offset is the same eleven per cent throughout: one
  wrong conversion applied to the whole column rather than thirteen
  independent slips. Which of the two columns carries it the page does not
  say, and no other column of the table settles it: the weave and the flow
  resistance are printed once each, in one unit, and neither determines a
  surface density.
- **Evidence:** Verified on PDF page 267 (printed p. 263) of Ver & Beranek,
  *Noise and Vibration Control Engineering* 2e (2006). Two readers transcribed
  the thirteen pairs independently and agreed on every digit. The other two
  tables of the chapter are not like this one: TABLE 8.7 converts its own mass
  column correctly on all eleven rows, and TABLE 8.5 on four of its five, the
  fifth being the single defective cell registered in the entry above. One
  cell of one row is a slip of the printing; thirteen rows off by one factor
  is a column, which is what makes this a property of this table rather than
  of the chapter.
- **What the library does:** holds the gramme per square metre the page
  prints, as it prints it, in `surface_density_g_m2`. Every row of this table
  in
  [`PUBLISHED_FLOW_RESISTANCE`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py)
  carries a `note` that quotes both printed values and the exact factor
  between their units and points here, so the contradiction reaches the reader
  with the number rather than instead of it. The library neither chooses
  between the two columns nor converts either of them: it publishes the one
  the page prints in SI and says what the other one says. The cell is not
  `not_derivable`, which is for a value this library declines to compute from
  cells the page did print and never for a quantity the page prints itself.
  The flow resistance of these cloths, which is printed once and in one unit,
  is served normally.
- **Status:** unreported.

## ASHRAE (2019) HVAC Applications Handbook, Chapter 49, folio 49.31 (the sentence that introduces the break-in tables swaps two of them)

- **Location:** Chapter 49, "Noise and Vibration Control", the paragraph
  printed under Equation (24) on printed page 49.31 (PDF page 915), and the
  titles of Tables 32 and 33 printed on that same page. Non-normative source: a
  design handbook.
- **The print:** the paragraph reads "Values for TL_in for rectangular ducts
  are given in Table 32, for round ducts in Table 33, and for flat oval ducts
  in Table 34 (Cummings 1983, 1985)." The two tables it names first are titled,
  on the same page, "Table 32 Experimentally Measured TL_in Versus Frequency
  for Circular Ducts" and "Table 33 TL_in Versus Frequency for Rectangular
  Ducts".
- **The problem:** the first two tables are named the wrong way round. Table 32
  is the circular one and Table 33 the rectangular one, and the sentence says
  the opposite; the third, flat oval, is right. What the tables print settles
  it against the sentence rather than against the titles. Table 32 is indexed
  by a Diameter and a Length, which is what a round duct has and what no
  rectangular one is given anywhere in the chapter, and it prints the marks of
  a measured table, a lower bound and a parenthesised value, under the note
  that explains them; Table 33 is indexed by a Duct Size of two sides in
  millimetres and prints an 8 kHz column, which in this chapter only the two
  rectangular tables do. The companion sentence for breakout on folio 49.29
  pairs the same three shapes with Tables 29, 30 and 31 in the order
  rectangular, round, flat oval, and there the three printed titles agree with
  it. Only this sentence is wrong.
- **Evidence:** Verified on PDF page 915 (printed p. 49.31) of ASHRAE (2019),
  *2019 ASHRAE handbook: Heating, ventilating, and air-conditioning
  applications* (SI ed.), Chapter 49, and against the breakout paragraph on PDF
  page 913 (printed p. 49.29) of the same chapter. Two readers transcribed the
  page independently and both read the sentence and the two titles as they are
  quoted here.
- **What the library does:** nothing, and nothing is needed: the cross
  reference is a label the library never reads. Every row of Tables 32, 33 and
  34 in
  [`PUBLISHED_DUCT_TRANSMISSION_LOSS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/duct_walls.py)
  is filed under the table whose own printed title it was read from, and
  `shape` carries the word that title uses. That sentence is the only credit
  the chapter gives those three tables, so each of their rows quotes it
  verbatim in `attributed_to["table"]` and records there that its first two
  tables are the wrong way round.
- **Status:** unreported.

## Harris 3e (1995), Tables 32.1 to 32.8 (nineteen double-unit pairs whose two halves are not each other)

- **Location:** Tables 32.1 to 32.8, the impact insulation of floor-ceiling
  constructions, on printed folios 32.8 to 32.15 (PDF pages 750 to 757), in
  chapter 32, "Aislamiento del sonido transmitido por estructuras", of the
  Spanish edition. Non-normative source: a handbook.
- **The print:** every dimension and every mass of these eight tables is
  printed twice, SI first and the US customary value in parentheses after it,
  inside the running description of each construction: "Losa de 10 cm (4 in)",
  "cada 40,6 cm (16 in)", "alfombra de 1,5 kg/m2 (44 oz/yd2)". Three hundred
  and twenty-one such pairs are printed over the eight tables.
- **The problem:** nineteen of the three hundred and twenty-one pairs are not each
  other. The inch is 2,54 cm exactly, the pound is 0,45359237 kg exactly and
  the yard 0,9144 m exactly, so one pound per cubic foot is 16,0185 kg/m3, one
  pound per square yard 0,54249 kg/m2 and one ounce per square yard 33,906
  g/m2, and each pair is decided by arithmetic alone. On these pages the US
  customary half is the measurement and the SI half its translation, so a pair
  whose imperial half is a whole number or a fraction is read in that
  direction only, and one whose imperial half is itself printed as a rounded
  decimal is allowed either. A pair counts as sound when the SI half is the
  conversion rounded **or truncated** to the precision it is printed to, which
  forgives the whole of this chapter's loose rounding: "60 cm (24 in)" and
  "2,5 cm (1 in)" are truncations of 60,96 and 2,54 and no more than that, and
  row 17 prints "36,9 cm (14,5 in)", where 36,9 cm is 14,53 in and the page
  would print that as the 14,5 in beside it. The nineteen below survive that
  test. Each one names the row the page numbers, the pair as it is set, and
  the conversion that fails:
  - **Row 9** (PDF page 750, printed folio 32.8): "30,8 cm (16 in)" for the
    batten spacing. $16 \times 2{,}54 = 40{,}64$ cm, which these eight tables
    print as 40,6 cm eighteen times over.
  - **Row 11** (PDF page 751, printed folio 32.9): "53,2 cm (21 in)" for the
    rib spacing. $21 \times 2{,}54 = 53{,}34$ cm, which row 38 prints as
    53,3 cm.
  - **Row 14** (PDF page 752, printed folio 32.10): "15,6 cm (6 in)" for the
    slab. $6 \times 2{,}54 = 15{,}24$ cm, which these eight tables print as
    15,2 cm eleven times over.
  - **Row 18** (PDF page 752, printed folio 32.10): "36,7 cm (14,5 in)" for
    the beam spacing. $14{,}5 \times 2{,}54 = 36{,}83$ cm, which rows 13 and
    15 print as 36,8 cm.
  - **Row 22** (PDF page 753, printed folio 32.11): "60,1 cm (24 in)" for the
    joist spacing. $24 \times 2{,}54 = 60{,}96$ cm, which rows 26, 27, 33 and
    38 print as 61 cm.
  - **Row 23** (PDF page 753, printed folio 32.11): "60,1 cm (24 in)" for the
    joist spacing, the same pair again.
  - **Row 26** (PDF page 754, printed folio 32.12): "32,3 cm (11,75 in)" for
    the total thickness. $11{,}75 \times 2{,}54 = 29{,}85$ cm, and 32,3 cm is
    12,72 in, so neither half is the other.
  - **Row 27** (PDF page 754, printed folio 32.12): "1,89 cm (0,78 in)" for
    the oak strip floor. $0{,}78 \times 2{,}54 = 1{,}98$ cm, which row 26
    prints as 1,98 cm for the same floor.
  - **Row 28** (PDF page 754, printed folio 32.12): "1,89 cm (0,78 in)" for
    the same oak strip floor.
  - **Row 28** (PDF page 754, printed folio 32.12): "31,6 cm (12,5 in)" for
    the total thickness. $12{,}5 \times 2{,}54 = 31{,}75$ cm, which rows 16
    and 18 print as 31,8 cm and row 25 as 31,7 cm.
  - **Row 29** (PDF page 754, printed folio 32.12): "60,8 cm (24 in)" for the
    resilient channels. $24 \times 2{,}54 = 60{,}96$ cm.
  - **Row 31** (PDF page 755, printed folio 32.13): "10,1 cm (2 in)" for the
    batten section. $2 \times 2{,}54 = 5{,}08$ cm, which these eight tables
    print as 5,1 cm twenty-two times over, the same row included.
  - **Row 34A** (PDF page 755, printed folio 32.13): "7,5 cm (3 in)" for the
    furring strips. $3 \times 2{,}54 = 7{,}62$ cm, which these eight tables
    print as 7,6 cm ten times over.
  - **Row 35A** (PDF page 756, printed folio 32.14): "410 kg/m3 (26,1 lb/ft3)"
    for the compressed paper-pulp floor board. $26{,}1 \times 16{,}0185 =
    418{,}1$ kg/m3, and 410 kg/m3 is 25,6 lb/ft3, so neither half is the other.
    The page does not say which of the two carries the defect, and no other
    cell of the eight tables settles it: row 5 prints 35,2 kg/m3 (2,2 lb/ft3)
    and row 37A 2370 kg/m3 (148 lb/ft3), and both of those convert correctly,
    which makes this a property of this cell and not of the chapter.
  - **Row 35B** (PDF page 756, printed folio 32.14): "60,1 cm (24 in)" for the
    steel joist spacing.
  - **Row 36B** (PDF page 756, printed folio 32.14): "60,1 cm (24 in)" for the
    steel joist spacing.
  - **Row 37A** (PDF page 756, printed folio 32.14): "1,5 kg/m2 (3,4 lb/yd2)"
    for the diamond mesh and metal lath. $3{,}4 \times 0{,}54249 = 1{,}84$
    kg/m2, and row 38 converts 4,14 lb/yd2 to 2,25 kg/m2 with that same
    factor.
  - **Row 38** (PDF page 756, printed folio 32.14): "1,81 kg/m2 (40 oz/yd2)"
    for the hair underlay. $40 \times 33{,}906 = 1356$ g/m2, which row 28
    prints as 1,4 kg/m2 for the same cloth.
  - **Row 38** (PDF page 756, printed folio 32.14): "1,99 kg/m2 (44 oz/yd2)"
    for the wool pile carpet. $44 \times 33{,}906 = 1492$ g/m2, which rows 28
    and 30 print as 1,5 kg/m2 for the same cloth. The two carpet cells of this
    row are both 1,334 of their own conversion, so one wrong factor was
    applied to the pair rather than two digits slipping.
- **Evidence:** Verified on PDF pages 750 to 757 (printed pp. 32.8-32.15) of
  Harris (ed.), *Manual de medidas acústicas y control del ruido* 3e (1995),
  the Spanish edition of *Handbook of Acoustical Measurements and Noise
  Control*. Two readers transcribed the eight tables independently and agreed
  on every one of these nineteen pairs; each was then read again on its own
  page, enlarged, before being listed here. The three hundred and twenty-one pairs
  were converted and compared one by one rather than by sampling, which is
  what makes the list closed rather than a sample of what a reader happened to
  notice. The near misses it leaves off are the ones the rule above forgives,
  and three of them are named there.
- **What the library does:** publishes every one of these descriptions exactly
  as the page sets them. The seventeen rows that carry one of the nineteen
  pairs are marked in
  [`PUBLISHED_IMPACT_INSULATION`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/impact_catalogue.py):
  the cell is recorded in `misprinted`, quoting the printed pair and the
  conversion that fails, so a reader reproducing the book sees what the book
  says and a reader using the catalogue is told not to. Eighteen of the
  nineteen sit inside the running description, where this catalogue serves no
  quantity from them and nothing else follows. The nineteenth is row 35A's
  density, which is the one cell of the nineteen this catalogue would lift
  into a field of its own, so `layer_density_kg_m3` is left empty there and
  `why_missing` hands back both printed halves rather than choosing one. Rows
  5 and 37A, whose densities convert, are served normally.
- **Status:** unreported.

## Norton & Karczub 2e (2003), Appendix 4 (the Young's modulus of cork, three powers of ten too large)

- **Location:** Appendix 4, "Physical properties of some common substances",
  part A "Solids", row "Cork", on printed page 605 (PDF page 625).
  Non-normative source: a textbook.
- **The print:** Cork: density $250$ kg/m$^3$, Young's modulus
  $6.2 \times 10^{10}$ Pa, a dash in both the Poisson ratio and the bar speed
  cells, bulk speed $500$ m/s, product of critical frequency and thickness
  $130.7$.
- **The problem:** $6.2 \times 10^{10}$ Pa is the modulus of a glass, and it
  is the value the same table prints for Glass (Pyrex) two rows below. The
  rest of the cork row contradicts it: with the density and the speed the row
  prints, $\rho c^2 = 250 \times 500^2 = 6.25 \times 10^{7}$ Pa, a factor of
  about a thousand smaller. The table's own last column agrees with the
  $500$ m/s rather than with the modulus: it is $c_0^2/(1.8\,c)$ with
  $c_0 = 343$ m/s, and $343^2/(1.8 \times 500) = 130.7$, which is what the page
  prints. The two other foamed or cellular solids in the same block,
  polyurethane and polystyrene, are printed at $1.9 \times 10^{7}$ and
  $1.1 \times 10^{7}$ Pa. The mantissa is consistent with the row and the
  exponent is not.
- **Evidence:** Verified on PDF page 625 (printed p. 605) of Norton &
  Karczub, *Fundamentals of Noise and Vibration Analysis for Engineers* 2e
  (2003). The two moduli, cork's and Pyrex's, are legible and identical on the
  page; the cork row's density, speed and last column are equally legible and
  consistent with each other.
- **What the library does:** the cell is held as `misprinted` in
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py), so the row
  keeps what the book prints and refuses to serve it as a modulus. The page
  does not print the exponent it meant, so no corrected value is supplied. The
  rest of the row is served normally.
- **Status:** unreported.

## Vigran (2008), Table 3.1 (a Poisson ratio whose second endpoint has lost its decimal point)

- **Location:** Table 3.1, "Examples of material properties", row
  "Aluminium", column "Poisson's ratio", on printed page 88 (PDF page 109).
  Non-normative source: a textbook.
- **The print:** "0.33–034".
- **The problem:** a Poisson ratio lies between $-1$ and $0.5$, and $034$ is
  not one. The row above, steel, prints its range as "0.28–0.31" with both
  endpoints written as decimals, and so does every other range in the column.
  The second endpoint of the aluminium range has lost its decimal point.
- **Evidence:** Verified on PDF page 109 (printed p. 88) of Vigran,
  *Building Acoustics* (2008). The cell is legible and reads "0.33–034"; the
  steel cell immediately above it reads "0.28–0.31".
- **What the library does:** the cell is held as `misprinted` in
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py) and refused.
  The intended endpoint is easy to guess from the pattern, but the page does
  not print it, and this library does not finish a value the page left
  unfinished.
- **Status:** unreported.

## Rossing (2014), Table 15.5 (a relative scaling factor that its own row does not give)

- **Location:** Table 15.5, "Typical densities and elastic properties of
  wood used for stringed instrument modelling (after Woodhouse)", column
  "Maple", row "Relative scaling factors", on printed page 622 (PDF page 632).
  Non-normative source: a handbook.
- **The print:** the row prints its symbol as $\sqrt[4]{D_1/D_3}$ and the
  values $1.9$ for spruce and $1.4$ for maple. Maple's $D_1$ is $860$ MPa and
  its $D_3$ is $170$ MPa; the table marks two of maple's stiffnesses with an
  asterisk as estimates, and neither of these two is marked.
- **The problem:** $\sqrt[4]{860/170} = 1.50$, not $1.4$. Spruce's printed
  factor does follow from its row: $\sqrt[4]{1100/84} = 1.90$. The same row
  prints the relation and the value that does not satisfy it, and the page
  does not say whether the factor or one of the two stiffnesses is wrong.
- **Evidence:** Verified on PDF page 632 (printed p. 622) of Rossing (ed.),
  *Springer Handbook of Acoustics* 2e (2014). The running text on the same
  page states the relation independently: "The relative change in scaled
  dimensions is therefore $\sqrt[4]{D_1/D_3}$."
- **What the library does:** every cell is served as printed in
  [`PUBLISHED_ORTHOTROPIC_WOOD`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/orthotropic_wood.py),
  because nothing on the page says which of the three is the wrong one; the
  maple row carries a note saying so, and a test asserts the relation holds
  on every other row.
- **Status:** unreported.

## Rossing (2014), Table 11.4 ("Open-plane" for an open-plan office)

- **Location:** Table 11.4, "Transmission loss and STC values for common
  partitions", ninth row, on printed page 413 (PDF page 428). Non-normative
  source: a handbook.
- **The print:** the row is labelled "Open-plane office partition", with a
  transmission loss of $10$ to $12$ dB in every band and an STC of $12$.
- **The problem:** an open-plan office is one laid out without walls, and a
  plane is not a kind of office. The label is a typing slip for "Open-plan";
  no number on the row is affected, and its low values are those of the
  screen that partitions an open-plan office.
- **Evidence:** Verified on PDF page 428 (printed p. 413) of Rossing (ed.),
  *Springer Handbook of Acoustics* 2e (2014); both independent readings of
  the page and a crop of the cell print "Open-plane".
- **What the library does:** the row is served under the name the page
  prints, in
  [`PUBLISHED_TRANSMISSION_LOSS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/catalogue.py),
  so that a search for the printed word finds it, and its note says what the
  word stands for.
- **Status:** unreported.

## Rossing (2014), Table 8.3 (the 1-pentanol line printed twice)

- **Location:** Table 8.3, "B/A values for organic liquids at atmospheric
  pressure", fourth and fifth lines of the left panel, on printed page 269
  (PDF page 285). Non-normative source: a handbook.
- **The print:** two consecutive lines read "1-Pentanol | 20 | 10 | [8.68]",
  identical in every cell.
- **The problem:** every other substance of the table names itself once and
  leaves the name blank on its further lines, and every other repeated
  temperature of a substance cites a different paper or prints a different
  value. These two lines are one measurement printed twice: the lines above
  and below them run through the 1-alcohols from propanol to decanol, one line
  each and all citing the same paper, and pentanol is the only one that
  appears twice.
- **Evidence:** Verified on PDF page 285 (printed p. 269) of Rossing (ed.),
  *Springer Handbook of Acoustics* 2e (2014); both independent readings of
  the page and a crop of the panel print the line twice.
- **What the library does:** the measurement is held once in
  [`PUBLISHED_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/nonlinearity.py), and
  its note says the page prints it twice.
- **Status:** unreported.

## Rossing (2014), Table 8.1 (a year its own reference list contradicts)

- **Location:** Table 8.1, "B/A values for pure water at atmospheric
  pressure", column "Year", the six rows credited to [8.65], on printed page
  268 (PDF page 284). Non-normative source: a handbook.
- **The print:** the six rows at 30, 40, 50, 60, 70 and 80 °C credited to
  [8.65] print the year 2001.
- **The problem:** the chapter's reference list, on printed page 308 (PDF page
  324), gives [8.65] as Plantier, Daridon and Lagourette, J. Acoust. Soc. Am.
  111, 707-715 (2002). Every other row of the column prints the year its
  reference carries in that list (1974, 1983, 1985, 1989, 1991), so the
  column is the year of the reference, and 2001 is not the year of this one.
- **Evidence:** Verified on PDF pages 284 and 324 (printed pp. 268 and 308) of
  Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014), on the page images.
- **What the library does:** in
  [`PUBLISHED_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/nonlinearity.py) the six
  rows serve no year and mark the cell `misprinted`, quoting both dates; their
  values and their reference are unaffected.
- **Status:** unreported.

## Rossing (2014), Table 8.4 ("at atmospheric pressure" for six gases above their boiling point)

- **Location:** Table 8.4, "B/A values for liquid metals and gases at
  atmospheric pressure", block "Liquid gases", on printed page 269 (PDF page
  285). Non-normative source: a handbook.
- **The print:** the caption gives every row at atmospheric pressure, and the
  block prints argon at −183,15 °C, methane at −153,15, −143,15 and −138,15 °C
  and nitrogen at −193,15 and −183,15 °C.
- **The problem:** at one atmosphere argon boils at −185,85 °C, methane at
  −161,49 °C and nitrogen at −195,79 °C, so at those six temperatures each is a
  gas, and a liquid only under a higher pressure. The rows' own reference,
  [8.74], is titled on PDF page 324 "A study of (B/A) in liquified gases as a
  function of temperature and pressure". The values are not in question; the
  condition the caption attaches to them is.
- **Evidence:** Verified on PDF pages 285 and 324 (printed pp. 269 and 308) of
  Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014), on the page
  images; the normal boiling points are those of the NIST Chemistry WebBook.
- **What the library does:** the six rows are served as printed in
  [`PUBLISHED_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/nonlinearity.py), hold
  no pressure, and each says in its note that the caption's condition cannot
  hold for it.
- **Status:** unreported.

## Harris 3e (1995), Table 30.2 (five pile weights whose two halves are not each other)

- **Location:** Table 30.2, "Absorción del sonido de alfombras sobre hormigón
  desnudo", column "Peso del pelo kg/m$^2$ (oz/yd$^2$)", on printed folio
  30.22 (PDF page 704), in chapter 30 of the Spanish edition. Non-normative
  source: a handbook.
- **The print:** every pile weight is printed twice, SI first and the US
  customary value in parentheses: "1,2 (35)", "1,5 (43)" and so on, eleven
  pairs in the table.
- **The problem:** one ounce per square yard is $0{,}033906$ kg/m$^2$ by
  definition, and five of the eleven pairs are not each other under the
  criterion the Chapter 32 entry uses (the SI half is the conversion rounded or
  truncated to the precision it is printed to):
  - "2,3 (66)", "3,1 (88)" and "2,1 (60)": $66 \times 0{,}0339 = 2{,}24$,
    $88 \times 0{,}0339 = 2{,}98$ and $60 \times 0{,}0339 = 2{,}03$. All three
    are what $0{,}035$ kg/m$^2$ per oz/yd$^2$ gives, a factor that also
    reproduces every pair of Tables 30.2 and 30.3 that does hold, which is how
    these three come out a tenth high: the metric column follows a factor 3 per
    cent above the definition.
  - "1,3 (32)": $32 \times 0{,}0339 = 1{,}08$, and $0{,}035$ gives $1{,}12$;
    neither reaches $1{,}3$.
  - "1,1 (3,2)": $3{,}2$ oz/yd$^2$ is $0{,}11$ kg/m$^2$. The same carpet,
    knotted, cut nylon with a pile of 14 mm, is printed "1,1 (32)" in Table
    30.3, so the imperial half has a stray decimal comma.
- **Evidence:** Verified on PDF page 704 (printed p. 30.22) of Harris (ed.),
  *Manual de medidas acústicas y control del ruido* 3.ª ed. (1995); both
  independent readings of the page and a crop of the column print all five
  pairs as quoted. All eight pairs of Table 30.3, on the same page and the
  next, hold.
- **What the library does:** in
  [`PUBLISHED_CARPETS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/carpets.py) the
  four rows whose kilograms are in doubt serve no pile weight and mark the
  cell `misprinted`, quoting the pair; the fifth serves its 1,1 kg/m$^2$ and
  says in its note that the ounces lost a digit.
- **Status:** unreported.

## Rossing (2014), Table 6.5 ("Flourite" for fluorite)

- **Location:** Table 6.5, "Comparison of room-temperature values of the
  ultrasonic nonlinearity parameters of solids", second row, on printed page
  244 (PDF page 261). Non-normative source: a handbook.
- **The print:** the row is labelled "Flourite", ionic bonding, beta 3,8.
- **The problem:** the crystal structure of calcium fluoride is fluorite; the
  label transposes two letters. No number on the row is affected.
- **Evidence:** Verified on PDF page 261 (printed p. 244) of Rossing (ed.),
  *Springer Handbook of Acoustics* 2e (2014), on the page image and in the
  PDF's own text layer, which both print "Flourite".
- **What the library does:** the row is served under the printed name in
  [`PUBLISHED_SOLID_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/nonlinearity.py),
  so that a search for the printed word finds it, keyed `fluorite`, and its
  note says what the word stands for.
- **Status:** unreported.

## UNE-EN ISO 9295:2015, Tables 1 and 2 (forty-three cells where a 0 of Annex A is printed as another digit)

- **Location:** Tables 1 and 2, "Valores del coeficiente de absorción por el
  aire", on printed folios 15 and 16 of UNE-EN ISO 9295:2015 (October 2015),
  which declares itself the Spanish version of EN ISO 9295:2015 and adopts ISO
  9295:2015 without modification. The two tables give the air absorption
  coefficient $\alpha$ in Np/m at a static pressure of 101,325 kPa, for 26
  frequencies from 10 000 Hz to 22 400 Hz, at 18, 20, 21, 22, 23, 24, 25 and
  27 °C and at 40 %, 50 % and 60 % relative humidity: 624 cells. Clause 7.2
  reads $\alpha$ from them into the room constant of Formula (7), and the
  normative Annex A gives the formulae they are computed from.
- **The print:** every cell carries four decimals, with the decimal comma and
  the last digit set apart, "0,027 7".
- **The problem:** forty-three cells contradict Annex A, and all forty-three
  in the same way: the value Annex A gives ends in 0, and a 0 is printed as
  another digit. In forty of them it is the fourth decimal, printed as the
  third repeated ("0,027 7" where Annex A gives 0,027 0). The other three are
  cells whose Annex A value ends in two zeros (two more such cells, both
  0,020 0 in Table 1, at 10 500 Hz, 20 °C and 50 % and at 11 000 Hz, 18 °C
  and 60 %, are printed correctly), and there it is the third decimal that
  takes the digit before it: "0,033 0" where Annex A gives
  0,030 0, and "0,04 4" and "0,05 50", with their digit groups set out of place
  as well, where Annex A gives 0,040 0 and 0,050 0. The defect is confined to
  zeros and is not a matter of rounding: the other 581 cells are Annex A to
  the last digit (see the evidence below), and of the 60 cells whose Annex A
  value ends in 0, these 43 are misprinted while 17 are printed with their 0.
  The errors run from one unit of the fourth decimal, where the repeated digit
  is a 1 ("0,051 1" for 0,051 0), to 0,005 0 Np/m, where "0,05 50" stands for
  0,050 0 at 21 500 Hz, 27 °C and 60 %. The three cells whose Annex A value
  ends in two zeros are each printed exactly 10 % high; read into Formula (7),
  any of them makes the air absorption area 10 % too large, and the room
  constant, and with it the sound power level of Formula (6), at least 0,41 dB
  too high. The cells, by table and frequency:
  - **Table 1, 13 500 Hz** (PDF page 15, printed folio 15): 20 °C and 60 %, "0,027 7" for 0,027 0; 21 °C and 40 %, "0,036 6" for 0,036 0; 21 °C and 60 %, "0,026 6" for 0,026 0; 22 °C and 40 %, "0,035 5" for 0,035 0.
  - **Table 1, 15 500 Hz** (PDF page 15, printed folio 15): 22 °C and 40 %, "0,044 4" for 0,044 0.
  - **Table 1, 16 500 Hz** (PDF page 15, printed folio 15): 21 °C and 50 %, "0,043 3" for 0,043 0.
  - **Table 1, 18 000 Hz** (PDF page 15, printed folio 15): 20 °C and 60 %, "0,045 5" for 0,045 0.
  - **Table 1, 19 000 Hz** (PDF page 15, printed folio 15): 21 °C and 60 %, "0,048 8" for 0,048 0.
  - **Table 1, 20 000 Hz** (PDF page 15, printed folio 15): 22 °C and 60 %, "0,051 1" for 0,051 0.
  - **Table 2, 10 000 Hz** (PDF page 16, printed folio 16): 27 °C and 50 %, "0,014 4" for 0,014 0.
  - **Table 2, 11 000 Hz** (PDF page 16, printed folio 16): 25 °C and 50 %, "0,018 8" for 0,018 0.
  - **Table 2, 11 500 Hz** (PDF page 16, printed folio 16): 23 °C and 50 %, "0,021 1" for 0,021 0.
  - **Table 2, 13 000 Hz** (PDF page 16, printed folio 16): 25 °C and 60 %, "0,021 1" for 0,021 0.
  - **Table 2, 13 500 Hz** (PDF page 16, printed folio 16): 27 °C and 60 %, "0,021 1" for 0,021 0.
  - **Table 2, 14 000 Hz** (PDF page 16, printed folio 16): 24 °C and 40 %, "0,035 5" for 0,035 0; 24 °C and 60 %, "0,025 5" for 0,025 0.
  - **Table 2, 14 500 Hz** (PDF page 16, printed folio 16): 24 °C and 50 %, "0,031 1" for 0,031 0; 25 °C and 40 %, "0,036 6" for 0,036 0; 25 °C and 50 %, "0,033 0" for 0,030 0; 27 °C and 50 %, "0,028 8" for 0,028 0; 27 °C and 60 %, "0,024 4" for 0,024 0.
  - **Table 2, 15 000 Hz** (PDF page 16, printed folio 16): 24 °C and 50 %, "0,033 3" for 0,033 0.
  - **Table 2, 15 500 Hz** (PDF page 16, printed folio 16): 24 °C and 50 %, "0,035 5" for 0,035 0; 27 °C and 40 %, "0,038 8" for 0,038 0.
  - **Table 2, 16 000 Hz** (PDF page 16, printed folio 16): 24 °C and 40 %, "0,044 4" for 0,044 0; 24 °C and 60 %, "0,032 2" for 0,032 0.
  - **Table 2, 16 500 Hz** (PDF page 16, printed folio 16): 23 °C and 60 %, "0,035 5" for 0,035 0.
  - **Table 2, 17 000 Hz** (PDF page 16, printed folio 16): 25 °C and 50 %, "0,04 4" for 0,040 0.
  - **Table 2, 18 000 Hz** (PDF page 16, printed folio 16): 23 °C and 60 %, "0,041 1" for 0,041 0; 27 °C and 60 %, "0,036 6" for 0,036 0.
  - **Table 2, 18 500 Hz** (PDF page 16, printed folio 16): 24 °C and 40 %, "0,056 6" for 0,056 0; 24 °C and 50 %, "0,048 8" for 0,048 0.
  - **Table 2, 19 500 Hz** (PDF page 16, printed folio 16): 23 °C and 50 %, "0,054 4" for 0,054 0.
  - **Table 2, 20 000 Hz** (PDF page 16, printed folio 16): 24 °C and 60 %, "0,048 8" for 0,048 0.
  - **Table 2, 20 500 Hz** (PDF page 16, printed folio 16): 23 °C and 40 %, "0,067 7" for 0,067 0; 24 °C and 40 %, "0,066 6" for 0,066 0.
  - **Table 2, 21 000 Hz** (PDF page 16, printed folio 16): 23 °C and 60 %, "0,054 4" for 0,054 0.
  - **Table 2, 21 500 Hz** (PDF page 16, printed folio 16): 23 °C and 40 %, "0,072 2" for 0,072 0; 24 °C and 40 %, "0,071 1" for 0,071 0; 27 °C and 60 %, "0,05 50" for 0,050 0.
  - **Table 2, 22 000 Hz** (PDF page 16, printed folio 16): 24 °C and 60 %, "0,057 7" for 0,057 0; 25 °C and 50 %, "0,063 3" for 0,063 0.
  - **Table 2, 22 400 Hz** (PDF page 16, printed folio 16): 25 °C and 50 %, "0,065 5" for 0,065 0.
- **Evidence:** Verified on PDF pages 15 and 16 (printed pp. 15 and 16) of
  UNE-EN ISO 9295:2015, where each of the forty-three cells was read on the
  page before being listed. Annex A, on PDF pages 25 and 26 (printed pp. 25
  and 26) of the same edition, was evaluated for all 624 cells: the 581 not
  listed reproduce to the fourth decimal when the temperature is converted as
  $\theta + 273{,}16$ K, and of the conversions from $\theta + 273{,}15$ K to
  $\theta + 273{,}18$ K in steps of 0,002 K that is the only one that
  reproduces all of them, so the tables were computed with the 273,16 K of
  the triple point where the Celsius scale puts 273,15 K. That offset is a
  property of the tables rather than a misprint, and a small one: at
  $\theta + 273{,}15$ K, 61 of the 581 move by one unit of the fourth
  decimal and none by more than 0,000 063 Np/m.
  For one listed cell the two conversions round apart, 19 500 Hz at 23 °C and
  50 %, which is 0,054 0 at 273,16 K and 0,054 1 at 273,15 K against the
  0,054 4 printed; the entry gives the table's own conversion throughout. The
  2013 draft, BS EN ISO 9295 (DPC 13/30264708), prints the same 624 cells on
  PDF pages 15 and 16 (printed pp. 7 and 8) of ISO/DIS 9295, so the defect
  came through from the draft to the standard.
- **Library behaviour:** does not read the tables. `air_absorption_np_per_m`
  in
  [`sound_power_high_frequency`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_high_frequency.py)
  evaluates Annex A with the library's ISO 9613-1 implementation and
  $T = \theta + 273{,}15$ K, and `room_constant_from_air_absorption` feeds
  it to Formula (7). The 624 cells are transcribed in
  [`tests/reference_data/emission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data/emission.py)
  with the forty-three named in `ISO9295_MISPRINTED_CELLS`;
  [`tests/emission/test_sound_power_high_frequency.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_high_frequency.py)
  and the conformance checks "ISO 9295:2015 Table 1" and "ISO 9295:2015 Table
  2" pin the 581 to the digit and hold each of the forty-three to what the page
  prints: Annex A with its first trailing 0 set as the digit before it.
- **Status:** unreported.

## UNE-EN ISO 9295:2015, Formula (A.5) (the oxygen relaxation frequency set with a digit zero)

- **Location:** Annex A (normative), "Cálculo del coeficiente de absorción
  por el aire", Formula (A.5) on printed folio 26 of UNE-EN ISO 9295:2015
  (October 2015), the Spanish version of EN ISO 9295:2015, which adopts ISO
  9295:2015 without modification.
- **The print:** the symbol list on printed folio 25 defines
  $f_{\mathrm{r,O}}$, "frecuencia de relajación del oxígeno", with the letter
  O, and Formula (A.3) at the top of folio 26 computes it under that name.
  Formula (A.5), which evaluates $\alpha$ from it, sets the same frequency as
  $f_{\mathrm{r,0}}$, with the digit zero, in both places it appears: the
  denominator $f_{\mathrm{r,0}} + f^2/f_{\mathrm{r,0}}$ of the oxygen term.
- **The problem:** the glyph in (A.5) is the narrow digit of $p_{\mathrm{s0}}$
  on the same page, not the round letter of (A.3), and the PDF's own text
  layer agrees, "f r,O" in the symbol list and in (A.3) and "f r,0" twice in
  (A.5). A reader who takes the subscript at its word looks for a quantity
  $f_{\mathrm{r,0}}$ that the annex never defines. The formula is right once
  the symbol is read as the oxygen relaxation frequency, which is the only
  frequency (A.3) gives, so no value of $\alpha$ changes.
- **Evidence:** Verified on PDF pages 25 and 26 (printed pp. 25 and 26) of
  UNE-EN ISO 9295:2015, on the page image and in the text layer. The 2013
  draft, BS EN ISO 9295 (DPC 13/30264708), defines $f_{\mathrm{r,O}}$ on PDF
  page 24 (printed p. 16) and sets $f_{\mathrm{r,0}}$ in (A.5) on PDF page 25
  (printed p. 17), so the slip came through from the draft to the standard.
- **Library behaviour:** unaffected. `air_absorption_np_per_m` in
  [`sound_power_high_frequency`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_high_frequency.py)
  evaluates Annex A through the library's ISO 9613-1 implementation, which
  names the oxygen relaxation frequency `fro`, and the 581 correctly printed
  cells of Tables 1 and 2 confirm the reading.
- **Status:** unreported.

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
  [`ARTIFICIAL_SOURCE_EXAMPLE_LWA_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
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
  [`ISO7235_GAS_CONSTANT`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_measurement.py)
  and `ISO7235_ABSOLUTE_ZERO_OFFSET`, so that a worked result can be
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
  [`sound_power_reverberation.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_reverberation.py)
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
  [`sound_energy_in_situ`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py)
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
  [`flow_modal_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py)
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
  [`silencer_background_correction_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_in_situ.py)
  and
  [`barrier_background_correction_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py),
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
  $\rho_0$ = 1.16, 1.19, 1.21, 1.14 kg/m³, which is the density of air in
  every row; carrying the conversion the other way with $\rho_0$ = 1.18 kg/m³
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

<!-- END GENERATED BODY -->
