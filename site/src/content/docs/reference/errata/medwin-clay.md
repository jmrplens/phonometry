---
title: "Errata in Medwin & Clay (1998)"
description: "Errata in Medwin & Clay (1998): 2 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 2 entries of the [errata registry](/phonometry/reference/errata/) on Medwin & Clay (1998), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

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
