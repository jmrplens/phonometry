---
title: "Errata in ANSI S3.5"
description: "Errata in ANSI S3.5: 2 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 2 entries of the [errata registry](/phonometry/reference/errata/) on ANSI S3.5-1997, in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## ANSI S3.5-1997, Annex C worked examples (official WG S3-79 errata)

> **Not verified against the page.** ANSI S3.5-1997 is not held locally
> (the R package `SII` vignette is held, not the standard),
> so what this entry calls "the print" is the working group's own description
> of it, not a page this project has read. The recomputations below are
> independent and do reproduce, but the *printed characters* rest on the
> errata list alone. The standard is on the maintainer's pending-acquisition
> list; when a copy arrives the entry is to be re-verified against the print of
> printed pp. 21-22 and this notice removed.

- **Location:** Annex C, Table C.1 (octave-band worked example, p. 21) and
  Table C.2 (one-third-octave worked example, p. 22) of the 1997 printing.
- **The print (per the working group's errata):** (a) Table C.1, row $i = 5$,
  the level-distortion factor $L_i$ under Step 6 is printed as $0.10$; (b)
  Table C.2, first row, the self-speech-masking slope $C_i$ is printed as
  $-45.59$.
- **The problem:** both cells contradict the standard's own normative
  formulas. (a) Clause 5.7 with the example's inputs ($E'_5 = 20\ \text{dB}$,
  $U_5 = 9.33\ \text{dB}$) gives $L_5 = 1 - (20 - 9.33 - 10)/160 = 0.9958$,
  which prints to two decimals as $1.00$, not $0.10$. (b) Clause 5.4 with the
  example's inputs ($B_1 = 40\ \text{dB}$, $f_1 = 160\ \text{Hz}$) gives
  $C_1 = -80 + 0.6 (40 + 10\log_{10} 160 - 6.353) = -46.587$, which prints as
  $-46.59$, not $-45.59$; the example's $Z_i$ column is only consistent with
  the corrected slope ($Z_2$ recomputes to $34.658$ = printed 34.66 dB,
  whereas the misprinted slope would give 34.76 dB). The Table C.1 example is
  the octave-band procedure and the Table C.2 example the one-third-octave
  procedure, so one cell of each is affected.
- **Evidence:** the official errata list published by ASA Working Group S3-79,
  the committee that maintains ANSI S3.5, on its support site (sii.to): "Page
  21, Table C1, row i=5, column Li under Step 6: the value printed as 0.10
  should be changed to 1.00" and "Page 22, Table C2, the first row of numbers,
  value −45.59 should be −46.59"; plus independent recomputation of both cells
  from the normative clauses (above). The same list carries five further
  corrections (a reference spelling, the Tables 1-4 caption wording recorded
  in the next entry, the insertion gain $G_i$ missing from Eq. 23, and two
  Annex B fixes, a cross-reference "B16" that should read "B15" and a wording
  change about the audio-visual approximation); none of those touches a
  formula this library implements. The source is the WG S3-79 errata list at
  sii.to/html/errata.html (captured 2026-07-30, re-checked live 2026-08-04).
  It is not the printed page and cannot substitute for it, which is why this
  entry carries the notice above.
- **Library behaviour:** unaffected; the library computes the corrected values
  from the normative clauses and always did. Its Annex C.2 anchors
  ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data),
  `ANSIS3_5_ANNEX_C1*` and `ANSIS3_5_ANNEX_C2*`) pin the errata-consistent
  chain of both examples, cross-checked to double precision against the
  working group's own reference implementation `SII.C` and its published
  test-case results. The Table C.1 cell is pinned directly: the
  level-distortion factor of clause 5.7 for row $i = 5$ of the Annex C.1
  octave-band example computes to $0.99581$, which prints as the corrected
  $1.00$.
- **Status:** published corrections by the issuing working group; nothing to
  report upstream.

## ANSI S3.5-1997, captions of Tables 1 to 4 (official WG S3-79 erratum)

> **Not verified against the page.** As with the entry above, ANSI S3.5-1997 is not
> held locally, so the wording of the four captions is taken from the working
> group's errata list rather than from a page this project has read. The
> argument that the tables carry no threshold column is independent and does
> hold against the transcribed constants. Re-verify against the print of
> printed pp. 3-5 when the standard is acquired.

- **Location:** the captions of Tables 1, 2, 3 and 4 (pp. 3-5 of the 1997
  printing), the constant tables of the four band procedures: critical band
  (21 bands), equally-contributing critical band (17 bands), one-third octave
  (18 bands) and octave (6 bands).
- **The print (per the working group's errata):** each caption lists the
  quantities the table tabulates and includes the phrase "hearing threshold
  levels,".
- **The problem:** none of the four tables tabulates a hearing threshold
  level. Each carries the band centre frequency (and, for Tables 1, 2 and 4,
  the band limits), the band-importance function $I_i$, the standard speech
  spectrum level $U_i$ by vocal effort and the reference internal noise
  spectrum level $X_i$. The hearing threshold level $T'_i$ is a *user input*
  to the procedure (clause 5.5, where the equivalent internal noise spectrum
  level is $X'_i = X_i + T'_i$), which is exactly the quantity the caption
  invites the reader to look for in the table and to confuse with $X_i$.
- **Evidence:** the official errata list published by ASA Working Group S3-79,
  the committee that maintains ANSI S3.5, on its support site (sii.to): "Pages
  3-5, Tables 1-4: In each of the **figure** captions the phrase 'hearing
  threshold levels,' should be deleted" (the WG S3-79 errata list at
  sii.to/html/errata.html, captured 2026-07-30, re-checked live 2026-08-04; an
  earlier revision of this entry dropped the word "figure" from the
  quotation); plus the tables themselves, which have no such column.
- **Library behaviour:** unaffected. The four tables are implemented with the
  columns they actually carry, exposed per procedure by `sii_procedure()` as
  `band_importance`, `speech_spectrum` ($U_i$) and `internal_noise` ($X_i$),
  and the hearing threshold stays the `threshold=` argument of
  `speech_intelligibility_index`
  ([`src/phonometry/speech/sii.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sii.py)).
- **Status:** published correction by the issuing working group; nothing to
  report upstream.
