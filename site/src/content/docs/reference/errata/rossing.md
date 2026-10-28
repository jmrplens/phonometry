---
title: "Errata in Rossing (2014)"
description: "Errata in Rossing (2014): 6 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 6 entries of the [errata registry](/phonometry/reference/errata/) on Rossing (2014), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
