---
title: "Errata in ICAO Annex 16"
description: "Errata in ICAO Annex 16: 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on ICAO Annex 16. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## ICAO Annex 16, Volume I, 8th edition (2017), Appendix 2, 4.4.2 (the minus sign of the bandsharing adjustment missing)

- **Location:** Appendix 2, section 4.4.2 (PDF page 158, printed p. APP 2-20)
  of ICAO Annex 16, Volume I, Eighth Edition, July 2017.
- **The print:** "If $C_\mathrm{avg} > C(k_\mathrm{M})$, then
  $\Delta_\mathrm{B} = C_\mathrm{avg}\ C(k_\mathrm{M})$ and
  $\mathrm{PNLTM} = \mathrm{PNLT}(k_\mathrm{M}) + \Delta_\mathrm{B}$".
- **The problem:** no operator stands between the two tone corrections; the
  adjustment is $\Delta_\mathrm{B} = C_\mathrm{avg} - C(k_\mathrm{M})$. The
  section fixes the reading itself: the paragraph above the formula calls for
  an adjustment when $C(k_\mathrm{M})$ is less than the average of the five
  spectra, the formula applies only when $C_\mathrm{avg} > C(k_\mathrm{M})$,
  and the Nomenclature defines $\Delta_\mathrm{B}$ as "the adjustment to be
  added to the maximum PNLT", so the adjustment is the positive shortfall of
  the tone correction at PNLTM below the average. The text layer of the page
  carries no character between the two terms either, while the minus signs of
  $(k_\mathrm{M} - 2)$ in the line above are present in the print and in
  the text layer alike.
- **Evidence:** Verified on PDF page 158 (printed p. APP 2-20) of ICAO Annex
  16, Volume I, Eighth Edition (2017), section 4.4.2, against the
  Nomenclature entry for $\Delta_\mathrm{B}$ on PDF page 27 (printed p. I-7)
  of the same edition.
- **Library behaviour:** implements the difference.
  `aircraft.epnl_from_pnlt` takes $\Delta_\mathrm{B}$ as the average tone
  correction of the records within one second of PNLTM less the tone
  correction at PNLTM, and zero when that is not positive; the bandsharing
  tests of
  [`tests/aircraft/test_certification.py`](https://github.com/jmrplens/phonometry/blob/main/tests/aircraft/test_certification.py)
  pin a hand-built case at 1.6 dB.
- **Status:** unreported.
