---
title: "Errata in Real Decreto 1367/2007"
description: "Errata in Real Decreto 1367/2007: 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Real Decreto 1367/2007. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
