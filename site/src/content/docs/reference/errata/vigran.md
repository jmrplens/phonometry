---
title: "Errata in Vigran (2008)"
description: "Errata in Vigran (2008): 3 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 3 entries of the [errata registry](/phonometry/reference/errata/) on Vigran (2008), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Vigran, Building Acoustics (2008), Figure 8.37 caption (carpet stiffness exponent)

- **Non-normative source** (textbook).
- **Location:** section 8.4.2, the caption of Figure 8.37 on printed p. 320 /
  pdf p. 341, which labels the predicted improvement curves of two floor
  coverings laid on a heavyweight floor.
- **The print:** "Predicted improvement with a linear model: stiffness of
  carpet squares 3.2·10^6 N/m, vinyl covering 5.2·10^6 N/m." (Vigran writes
  the decimal separator as a period.)
- **The problem:** the carpet exponent is one order too high. The body text
  introducing the figure, on printed p. 321, says of the carpet squares that
  "we have assumed that the covering has the same stiffness as used in Figure
  8.36", and Figure 8.36 is labelled $s = 3.2 \cdot 10^{5}\ \text{N/m}$ inside
  the plot, the same value the body text on printed p. 320 gives for it. The
  vinyl value in the same caption is correct.
- **Evidence:** printed p. 320 states $3.2 \cdot 10^{5}\ \text{N/m}$ "giving a
  resonance frequency f0 of approximately 130 Hz with a hammer mass of 0.5
  kg", and $\sqrt{3.2 \cdot 10^{5}/0.5}/(2\pi) = 127.3\ \text{Hz}$ reproduces
  that while $\sqrt{3.2 \cdot 10^{6}/0.5}/(2\pi) = 402.6\ \text{Hz}$ is a
  frequency that appears nowhere in the section. The same arithmetic applied
  to the caption's vinyl value gives
  $\sqrt{5.2 \cdot 10^{6}/0.5}/(2\pi) = 513.3\ \text{Hz}$ against the
  "approximately 510 Hz" printed on p. 321, which fixes the formula and the
  hammer mass the author used. Graphically, the two dashed prediction curves
  of Fig. 8.37 are about two octaves apart, matching the stiffness ratio
  $5.2 \cdot 10^{6}/(3.2 \cdot 10^{5}) = 16.25$ (a factor 4.03 in frequency)
  and not $5.2 \cdot 10^{6}/(3.2 \cdot 10^{6}) = 1.63$ (a factor 1.27).
  Verified on PDF page 341 (printed p. 320) of Vigran, Building
  Acoustics:2008, on which both caption exponents read 6 unambiguously and the
  body text of the same page reads $3.2 \cdot 10^{5}\ \text{N/m}$, with the
  surrounding argument read on PDF page 340 (printed p. 319) and PDF page 342
  (printed p. 321) of the same edition.
- **Library behaviour:** none needed; the library takes the covering stiffness
  from the user through `covering_contact_stiffness`, and the printed cut-off
  frequencies it is anchored on come from Hopkins rather than from this
  caption.
- **Status:** unreported.

## Vigran, Building Acoustics (2008), Eq. (9.18) (receiving-side coefficient)

- **Location:** Section 9.2.3.2, Eq. (9.18) (printed p. 339), the transmission
  factor of the one-dimensional suspended-ceiling plenum model after Mechel
  (1980).
- **The print:** the denominator reads $m_S L_S \cdot m_R L_R h$ with the
  **unprimed** $m_R$, while the exponent of the same expression carries the
  primed $m'_R = m_R + s_R \tau_R / h$ of Eq. (9.17).
- **The problem:** the two sides of the plenum are integrated the same way.
  The receiving-side integral is
  $\int_0^{L_R} \exp(-\varepsilon m'_R x)\,dx = (1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R)$,
  so the factor that normalises it must be $m'_R L_R$, exactly as the
  source-side one is $m_S L_S$. Read literally, the printed expression is not
  a transmission factor at all: it carries a spurious
  $m'_R/m_R = 1 + s_R \tau_R/(h m_R)$, so it grows without bound as the plenum
  damping falls. Two consequences are visible with ordinary inputs
  ($L_S = L_R = 5\ \text{m}$, $h = 0.6\ \text{m}$,
  $R_S = R_R = 25\ \text{dB}$, $\varepsilon = 2$, $s_S = s_R = 0.5$): the
  model **diverges as the plenum damping vanishes**, giving
  $R_\text{cl} = 40.26\ \text{dB}$ at $m_R = 0.01\ \text{1/m}$ but only 26.48
  dB at $10^{-4}$ and 6.64 dB at $10^{-6}$, against the finite 40.85 dB that
  the derived reading returns for the same bare plenum, where the leakage term
  $s_R \tau_R/h$ bounds the path; a plenum with no absorber at all is
  therefore predicted arbitrarily worse than the leak-limited value rather
  than equal to it. It also **breaks energy conservation**, returning
  $\tau_\text{cl} = 4.45$ at $R_S = R_R = 6\ \text{dB}$, $m_R = 0.01$ and
  $\tau_\text{cl} = 829$ at $R_S = R_R = 0\ \text{dB}$, $m_R = 10^{-3}$.
- **Evidence:** with $m'_R$ in the denominator every one of those pathologies
  disappears: $\tau_\text{cl}$ flattens onto the leak-limited value as the
  damping vanishes, where the printed form keeps growing, and is bounded above
  by 1 because
  $(1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R L_R) \le 1$, and
  reduces to Vigran's own small-attenuation result, Eq. (9.19)
  $\tau_\text{cl} = \varepsilon^2 \tau_S \tau_R L_R/(4h)$, whenever $m_S L_S$
  and $m'_R L_R$ are both small. With the printed $m_R$ the same limit picks
  up the factor $m'_R/m_R$, which diverges, so Eq. (9.18) as printed does not
  reduce to Eq. (9.19) at all: the two equations the book presents as a pair
  are inconsistent with each other. Verified on PDF page 361 (printed p. 339)
  of Vigran, Building Acoustics:2008, which shows the denominator carrying the
  unprimed $m_R$ while the exponent of the same expression carries the primed
  $m'_R$ of Eq. (9.17).
- **Library behaviour:** `plenum_flanking_reduction_index` in
  [`ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/prediction/ceiling_plenum.py)
  implements the derived $m'_R$ in both the exponent and the denominator, with
  the reading documented at the formula, and rejects a transmission factor
  above unity rather than reporting a negative sound reduction index. Tests
  pin the physics the model owes (monotonicity in the damping, the
  $\tau_\text{cl} \le 1$ bound, the size of the Eq. (9.17) leakage term at a
  realistic ceiling) and the one property that separates the two readings: a
  bare plenum no worse than the undamped Eq. (9.20) value
  ([`tests/building/prediction/test_ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_ceiling_plenum.py)).
- **Status:** unreported (textbook rather than a standard). Mechel's original
  1980 paper, which Vigran reproduces, was not available to check whether the
  misprint originates there.

## Vigran (2008), Table 3.1 (a Poisson ratio whose second endpoint has lost its decimal point)

- **Location:** Table 3.1, "Examples of material properties", row
  "Aluminium", column "Poisson's ratio", on printed page 88 (PDF page 109).
  Non-normative source: a textbook.
- **The print:** "0.33–034".
- **The problem:** a Poisson ratio lies between $-1$ and $0.5$, and $034$ is
  not one. The row above, steel, prints its range as "0.28–0.31" with both
  endpoints written as decimals, and so does every other range in the column.
  The second endpoint of the aluminium range has lost its decimal point.
- **Evidence:** Verified on PDF page 109 (printed p. 88) of Vigran,
  *Building Acoustics* (2008). The cell is legible and reads "0.33–034"; the
  steel cell immediately above it reads "0.28–0.31".
- **What the library does:** the cell is held as `misprinted` in
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py) and refused.
  The intended endpoint is easy to guess from the pattern, but the page does
  not print it, and this library does not finish a value the page left
  unfinished.
- **Status:** unreported.
