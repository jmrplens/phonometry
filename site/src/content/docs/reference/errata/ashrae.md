---
title: "Errata in ASHRAE (2019)"
description: "Errata in ASHRAE (2019): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on ASHRAE (2019). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
