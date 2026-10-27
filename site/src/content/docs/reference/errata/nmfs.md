---
title: "Errata in NMFS (2024)"
description: "Errata in NMFS (2024): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on NMFS (2024). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## NMFS (2024) Updated Technical Guidance v3.0, Table 5 / Table ES2 (otariid C)

*Regulatory guidance document, not a standard.*

- **Location:** Table 5 (printed p. 25), repeated as Table ES2 (printed p. 3)
  and again as Table 8 (printed p. 35): the auditory weighting parameter $C$
  of the otariid pinniped in-water group (OW / OCW).
- **The print:** $C = 1.37\ \text{dB}$.
- **The problem:** the correct value is 1.36 dB. NMFS states so itself in the
  table's own footnote: "During the public comment period, an error was
  identified with the Navy's rounding, where this value should be 1.36,
  instead of 1.37. Because this is such a minor error and to remain consistent
  with the Navy, NMFS decided rely upon the value the Navy originally
  provided." The document therefore knowingly publishes the wrong digit.
- **Evidence:** independent recomputation of $C$ from its own definition, the
  negated peak of $W(f)$, with the same row's parameters $a = 1.58$, $b = 5$,
  $f_1 = 2.53\ \text{kHz}$, $f_2 = 43.8\ \text{kHz}$: $C = 1.3643\ \text{dB}$,
  which rounds to 1.36. The published weighted TTS onset of the same row
  ($179\ \text{dB} = K + C$ with $K = 178$) is unaffected by the third digit.
  The same recomputation reproduces every other row of the table to the
  printed two decimals, so the OW row is the only one that does not round from
  its own parameters. Verified on PDF page 36 (printed p. 25), PDF page 14
  (printed p. 3) and PDF page 46 (printed p. 35) of NMFS Updated Technical
  Guidance v3.0:2024, all three carrying 1.37 with the identical footnote.
- **Library behaviour:**
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py)
  implements 1.36 and keeps the printed 1.37 available as
  `WeightingParameters.c_db_as_printed`, so an assessment that must reproduce
  the published table verbatim still can. Pinned by
  `test_nmfs_2024_otariid_c_uses_the_corrected_1_36`.
- **Status:** unreported (the issuing body has already documented it).
