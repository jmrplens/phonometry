---
title: "Errata in Barham, Barrera-Figueroa & Avison (2014)"
description: "Errata in Barham, Barrera-Figueroa & Avison (2014): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Barham, Barrera-Figueroa & Avison (2014). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Barham, Barrera-Figueroa & Avison (2014), Metrologia 51, 129, Formulas (1), (2) and (4) (a model that does not give its own Table 2)

- **Location:** section 3.4 "Dissimilarity in reference and test microphones",
  Formulas (1) to (5), Table 1 and Table 2 (printed p. 135). The paper is
  reference [1] of IEC 61094-5:2016 6.5, which refers microphones of
  different diameters to it, and the origin of the corrections of its Table
  A.1. Non-normative source: a journal paper.
- **The print:** Formula (1),
  $u(r) = \sum D_n J_0(k_n r)\,\mathrm{e}^{\mathrm{i}\omega t}$, with "$k_n$ the
  roots of $J_1(k_n) = 0$"; Formula (2),
  $D_n = \frac{2}{a^2 J_0^2(k_n)} \int_b^a J_0(k_n r/a)\,r\,\mathrm{d}r$;
  Formula (4), $S(r) = J_0(j_{01}\varpi r/a)/J_0(j_{01}\varpi)$. Table 1 lists
  "WS3 microphone overall radius 2.975 mm" and "WS3 microphone diaphragm
  radius (b) 2.065 mm", and no formula uses the first. Table 2 prints,
  "calculated with input data from table 1", -0.004 dB at 1000 Hz,
  -0.235 dB at 8000 Hz and -1.443 dB at 20 000 Hz, the column IEC 61094-5:2016
  adopts as Table A.1.
- **The problem:** evaluated as printed, with $b$ = 2.065 mm in (2) and in
  (5), the model gives -0.003 dB, -0.190 dB and -0.986 dB at those
  frequencies at 344.8 m/s, and no speed of sound gives the table: at
  291.7 m/s its two ends round to the printed -0.004 dB and -1.443 dB, but
  8000 Hz is then 0.033 dB off and 16 000 Hz 0.091 dB, and the best
  compromise, about 296.5 m/s, still misses a row by 0.054 dB. Two readings
  together give every row of Table 2 to its printed rounding, and neither
  alone does: the radial sensitivity of (4) is the deflection of a membrane under a uniform
  pressure, $J_0(j_{01}\varpi r/a)/J_0(j_{01}\varpi) - 1$, which is greatest
  at the centre, as IEC 61094-5 6.5 says a microphone's sensitivity is, where
  (4) as printed tends to a uniform sensitivity at low frequency; and the
  lower limit of (2), the inner edge of the annulus through which the sound
  enters the gap, is the overall radius, 2.975 mm, while the average of (5)
  over the test microphone runs over its diaphragm radius $b$. Formula (1)
  besides writes $J_0(k_n r)$ where (2) and (3) write $J_0(k_n r/a)$: with
  $k_n$ a pure number, the argument of (1) has the dimension of a length. The
  paper prints no speed of sound; at 344.8 m/s the two readings reproduce all
  fourteen rows to the thousandth of a decibel, and at the 345.9 m/s of the
  air of IEC 61094-5 clause 4 within 0.01 dB.
- **Evidence:** the model recomputed as printed and in the two readings,
  against Table 2. Verified on PDF page 8 (printed p. 135) of Metrologia 51
  (2014) 129-138, doi:10.1088/0026-1394/51/3/129, the IOPscience download whose
  first page is a cover sheet.
- **Library behaviour:** `metrology.diameter_sound_field_correction` computes
  the model in the two readings, with $k_n r/a$ in (1); the conformance rows on
  IEC 61094-5 6.5 reproduce Table A.1 from the inputs of Table 1
  ([`tests/metrology/test_comparison_diameter_gap_validation.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_comparison_diameter_gap_validation.py)).
- **Status:** unreported (journal paper rather than a standard).
