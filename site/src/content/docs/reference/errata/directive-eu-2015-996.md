---
title: "Errata in Directive (EU) 2015/996"
description: "Errata in Directive (EU) 2015/996: 6 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 6 entries of the [errata registry](/phonometry/reference/errata/) on Directive (EU) 2015/996, in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
  works over the corrected 63 Hz to 8 kHz grid (`ROAD_OCTAVE_BANDS_HZ`), pinned
  by `test_octave_bands_are_the_corrected_range` and by the workbook cases,
  whose published levels cover all eight bands.
- **Status:** corrected by the issuing body (corrigendum of 10 January 2018);
  recorded because the uncorrected 2015 text is still the one most often
  downloaded and quoted.

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
