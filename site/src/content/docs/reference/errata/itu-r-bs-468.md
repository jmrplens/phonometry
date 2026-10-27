---
title: "Errata in ITU-R BS.468"
description: "Errata in ITU-R BS.468: 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on ITU-R BS.468-4. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## ITU-R BS.468-4, Table 2, 5 ms upper limit (the dB cell should read −6.7)

- **Location:** clause 2.1, Table 2, "Limiting values — upper limit", the 5 ms
  column (printed p. 4). The same pair of cells is printed identically in
  IEC 60268-1:1985 Table AII and in the Amendment 1:1988 table that replaces
  it, so the defect is inherited from the CCIR text rather than introduced by
  either edition.
- **The print:** `46` in the (%) row and `−6.6` in the (dB) row.
- **The problem:** the two disagree. 46 % is 20 lg(0.46) = **−6.745 dB**, and
  −6.6 dB is 46.8 %. All 33 cells of Tables 2 and 3 were audited against their
  own counterpart; 32 agree to within 0.050 dB, the rounding of a
  two-significant-figure percentage, and this one is out by 0.145 dB. The
  neighbouring 5 ms *lower* limit (`34`, `−9.3`) is out by 0.070 dB and is
  benign, because 34 % as a rounded two-figure percentage covers 33.5 % to
  34.5 %, that is −9.500 dB to −9.241 dB, and −9.3 lies inside it. The upper
  cell is not benign: 46 % covers 45.5 % to 46.5 %, that is −6.840 dB to
  −6.651 dB, which excludes −6.6.
- **Which cell is wrong:** the dB one. Read as percentages, the acceptance
  window is a very steady −1.4 dB / +1.2 dB about the reference reading for
  every duration from 5 ms to 200 ms (+1.18 to +1.24 dB above, −1.37 to
  −1.45 dB below). 46 % puts the 5 ms upper limit +1.214 dB above its
  reference, on that pattern; 46.774 %, which is what −6.6 dB means, would put
  it +1.360 dB above, off it. So 46 % is right and the dB cell should read
  **−6.7**.
- **Evidence:** 20 lg of each printed percentage compared with the printed dB
  cell beside it, for all 24 cells of Table 2 and all 9 of Table 3, and the
  upper- and lower-limit offsets about the reference row recomputed across the
  five durations from 5 ms to 200 ms. Verified on PDF page 4 (printed p. 4) of
  Recommendation ITU-R BS.468-4, on PDF page 33 (printed p. 31) of IEC
  60268-1:1985, and on PDF page 3 (printed p. 3) of IEC 60268-1:1985
  Amendment 1:1988.
- **Library behaviour:** the percentage rows are primary and the dB rows are
  derived from them, which is the decision this entry forces. The eleven
  acceptance windows are stored as percentages in
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data) and checked as
  percentages, in the test suite and in the conformance rows "ITU-R BS.468-4
  Table 2" and "ITU-R BS.468-4 Table 3".
- **Status:** unreported.
