---
title: "Errata in NORAH2 rotorcraft guidance"
description: "Errata in NORAH2 rotorcraft guidance: 8 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 8 entries of the [errata registry](/phonometry/reference/errata/) on NORAH2 rotorcraft guidance, in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
