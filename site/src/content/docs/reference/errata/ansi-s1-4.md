---
title: "Errata in ANSI S1.4"
description: "Errata in ANSI S1.4: 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on ANSI S1.4-1983. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## ANSI S1.4-1983, Table V, 20 Hz type 2 cell (a plus sign that lost its bar)

- **Location:** clause 5.2, Table V "Tolerance limits on relative response
  levels for sound at random incidence measured on an instrument's calibration
  range", 20 Hz row, type 2 column (printed p. 6).
- **The print:** the cell reads "**+ 3**", with no second term. Its column
  neighbours at 10, 12.5 and 16 Hz read "+ 5, − ∞", and the type 0 and type 1
  cells of its own row read "± 2" and "± 2.5".
- **The problem:** the table has one notation for an upper-only limit, a pair
  "+ n, − ∞", and it is used three rows above this cell in the same column.
  This cell uses neither that notation nor the "± n" of its row, so it is
  either a limit written in a form the table uses nowhere else or a "±" whose
  bar failed to print. IEC 651:1979 Table V, of which this table is the US
  counterpart and with which the type 2 column agrees at all thirty-three
  other rows, prints "**±3**" at exactly this cell. The intended reading is
  ±3 dB.
- **Evidence:** the cell and its column neighbours, read on PDF page 16
  (printed p. 6) of ANSI S1.4-1983, against the same cell on PDF page 10
  (printed p. 8, marked "[IEC page 19]") of BS 5969:1981, the identical
  British adoption of IEC 651:1979.
- **Library behaviour:** `_ANSI_S14_TABLE5_12` in
  [`weighting_compliance.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/weighting_compliance.py)
  and its `reference_data` twin carry −3 dB as the 20 Hz type 2 lower limit,
  the stricter of the two readings, with the note beside them.
  `test_b_masks_match_reference_data` pins the two transcriptions to each
  other. No shipped verdict moves: the realized B weighting sits 0,05 dB below
  nominal at 20 Hz and clears either reading.
- **Status:** unreported.
