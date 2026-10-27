---
title: "Errata in Ver & Beranek (2006)"
description: "Errata in Ver & Beranek (2006): 4 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 4 entries of the [errata registry](/phonometry/reference/errata/) on Ver & Beranek (2006), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
  [`PUBLISHED_RESISTIVE_SHEETS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py).
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
  [`PUBLISHED_RESISTIVE_SHEETS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py)
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
