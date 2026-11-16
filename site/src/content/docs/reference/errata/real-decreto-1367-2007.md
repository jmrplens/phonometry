---
title: "Errata in Real Decreto 1367/2007"
description: "Errata in Real Decreto 1367/2007: 2 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
corrects:
  - "std-rd-1367-2007-boe-a-2007-18397-consolidated-text"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 2 entries of the [errata registry](/phonometry/reference/errata/) on Real Decreto 1367/2007, in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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

## Real Decreto 1367/2007, Article 30.1 and 30.2 (the metrology Order credited to the Ministerio de Fomento)

- **Location:** Article 30 "Instrumentos de medida", sections 1 and 2.
- **The print:** "Los instrumentos de medida y calibradores utilizados para
  la evaluación del ruido deberán cumplir las disposiciones establecidas en
  la Orden del Ministerio de Fomento, de 25 de septiembre de 2007, por la que
  se regula el control metrológico del Estado de los instrumentos destinados
  a la medición de sonido audible y de los calibradores acústicos";
  section 2 refers back to "la Orden del Ministerio de Fomento, de 25 de
  septiembre de 2007".
- **The problem:** the Order of that date and that title was issued by
  another ministry. It is Orden ITC/2845/2007, de 25 de septiembre
  (BOE-A-2007-17278), which the Boletín Oficial del Estado prints under the
  heading "Ministerio de Industria, Turismo y Comercio" and which that
  ministry's minister signs. The Ministerio de Fomento had issued the order
  it replaced: the disposición derogatoria única of Orden ITC/2845/2007
  repeals "la Orden de 16 de diciembre de 1998, del Ministerio de Fomento",
  on the metrological control of sound level meters. A reader who looks for
  an order of the Ministerio de Fomento of 25 September 2007 finds none.
  Orden ITC/2845/2007 has since been repealed, with effect from 24 October
  2020, by Orden ICT/155/2020, de 7 de febrero (BOE-A-2020-2573), and the
  consolidated text of Article 30 still reads as quoted.
- **Evidence:** a comparison of the article with the Order, each read on its
  page: Article 30 on PDF page 16 (printed p. 16) of Real Decreto 1367/2007,
  BOE-A-2007-18397 consolidated text; the heading and title on PDF page 1
  (printed p. 40035), the disposición derogatoria única on PDF page 3
  (printed p. 40037) and the signature on PDF page 4 (printed p. 40038), of
  Orden ITC/2845/2007, BOE núm. 237 of 3 October 2007. The repeal by Orden
  ICT/155/2020 is the one the Boletín Oficial del Estado records against
  BOE-A-2007-17278.
- **Library behaviour:** no change was required: the library computes no
  instrument requirement from Article 30. The Spanish noise regulation guide
  names the Order by its number and its ministry, says it has been
  repealed, and lists both UNE-EN 61260 documents of Article 30.3.
- **Status:** unreported (national regulation, not a standards body).
