---
title: "Errata in Osses, García & Kohlrausch (2016)"
description: "Errata in Osses, García & Kohlrausch (2016): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Osses, García & Kohlrausch (2016). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Osses, García & Kohlrausch (2016), fluctuation-strength model, Eq. (3)

- **Location:** Eq. (3), the critical-band-rate (Bark) transformation of the
  excitation-pattern front-end.
- **The print:**
  $z(f) = 13 \cdot \arctan(0.76 \cdot 10^{-4} \cdot f) + 3.5 \cdot \arctan((f/7500)^2)$.
- **The problem:** the first coefficient is the Zwicker-Terhardt
  $0.76 \cdot 10^{-3}$ with the exponent misprinted. The paper's own anchors
  disprove the print: it states $0.5\ \text{Bark} = 50\ \text{Hz}$ and
  $23.5\ \text{Bark} = 13.2\ \text{kHz}$ (section 2.1.2) and
  $15\ \text{Bark} = 2.7\ \text{kHz}$ (section 3.1), all of which require
  $10^{-3}$. With $10^{-4}$, $z(1\ \text{kHz}) = 1.05$ instead of
  $8.51\ \text{Bark}$ and the model's 47 filter centres would span 491 Hz to
  20 kHz instead of 50 Hz to 13.2 kHz.
- **Evidence:** evaluation of Eq. (3) under both exponents against the paper's
  printed Bark/frequency anchors. The printed section 2.1.2 range "0.5 Bark
  (50 Hz) to 23.5 Bark (13.2 kHz)" and the section 3.1 anchor "15 Bark (2.7
  kHz)" all reproduce under the Zwicker-Terhardt $0.76 \cdot 10^{-3}$ (50.6
  Hz, 13.07 kHz and 2.71 kHz) and none of them under the printed exponent.
  Verified on PDF page 4 (printed p. 4) of Osses, García & Kohlrausch,
  ICA:2016, with the anchors on PDF page 7 (printed p. 7) of the same paper.
- **Library behaviour:** implements $0.76 \cdot 10^{-3}$ with a note at the
  formula; the carrier-frequency sweep test would catch a regression to the
  printed value
  ([`_fluctuation_strength.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/_fluctuation_strength.py)).
- **Status:** unreported (conference paper rather than a standard).
