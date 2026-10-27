---
title: "Errata in Mechel (2008)"
description: "Errata in Mechel (2008): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Mechel (2008). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
