---
title: "Errata in RANDI 3.1 Physics Description"
description: "Errata in RANDI 3.1 Physics Description: 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on RANDI 3.1 Physics Description. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## RANDI 3.1 Physics Description (NRL, Breeding et al.), Table 2

- **Location:** Table 2 (representative ship source levels).
- **The print:** two cells deviate from the report's own Eqs. (2) to (5)
  evaluated with the Table 1 average lengths and speeds: the Merchant value at
  25 Hz (about 3 dB high) and the Tanker value at 300 Hz (about 1 dB low). The
  Fishing Vessel row is not reproducible from the Table 1 averages at all (a
  constant offset of about 3.8 dB suggests different assumed inputs).
- **The problem:** the report does not state the exact inputs used for Table
  2, and two cells contradict its own equations while every Large Tanker and
  Super Tanker cell agrees to 0.06 dB.
- **Evidence:** recomputation of all 25 cells from Eqs. (2) to (5).
- **Library behaviour:** the regression test pins the reproducible rows and
  excludes the contradicting cells with the rationale in the test.
- **Status:** unreported (technical report rather than a standard).
