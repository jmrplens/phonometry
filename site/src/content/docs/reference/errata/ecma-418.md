---
title: "Errata in ECMA-418"
description: "Errata in ECMA-418: 8 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 8 entries of the [errata registry](/phonometry/reference/errata/) on ECMA-418-1:2024 and ECMA-418-2:2025, in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## ECMA-418-1:2024 (3rd edition), clause 4.1.1 NOTE 2 (upper limit of the discrete-tone range)

- **Location:** clause **4.1.1** "frequency range of interest", NOTE 2
  (printed p. 2). An earlier revision of this entry cited clause 4.1.2, which
  is the definition of "ITT equipment" and says nothing about frequency.
- **The print:** "From viewpoint of test implementation by using FFT analyser,
  the frequency range of discrete tones are between 89,1 Hz and 11 220 Hz
  inclusive, referred to *the discrete tone frequency range of interest*."
- **The problem:** every formula and table of the standard works to 11 200 Hz:
  the Table 2 and Table 3 band-edge fits are stated for
  $11\,200 \ge f_t > 1\,600$, and clauses 10, 12.3 and 12.4 permit FFT data
  with $f_1 < 89{,}1\ \text{Hz}$ and $f_2 > 11\,200\ \text{Hz}$. The two
  numbers are the same quantity to different precision rather than a
  typographical error: $10\,000 \cdot 2^{1/6} = 11\,224{,}6\ \text{Hz}$ is the
  upper edge of the 10 kHz one-third-octave band that closes the range of
  interest, which rounds to 11 220 Hz at four significant figures and to
  11 200 Hz at three. An earlier revision of this entry called it a typo and
  added that "no other clause mentions 11 220 Hz"; the last x-axis tick of
  Figure 6 (printed p. 20) is labelled 11220. What clause 4.1 does carry is a
  structural defect: 4.1.2 "ITT equipment" repeats 4.1.1's NOTE 1 verbatim
  ("This range was selected to be identical to that of ECMA-74:2022, 3.1.3"),
  although 4.1.2 defines no range at all, and clause 10 then cross-references
  "NOTE 1 of 4.1.2" for the discrete-tone range, which is the duplicated note
  rather than the NOTE 2 that states it.
- **Evidence:** the arithmetic above, and the Table 2/3 ranges and Figure 6
  axis read side by side with NOTE 2. Verified on PDF page 10 (printed p. 2),
  PDF page 18 (printed p. 10), PDF page 25 (printed p. 17) and PDF page 28
  (printed p. 20) of ECMA-418-1:2024 (3rd edition).
- **Library behaviour:** uses the internally consistent $89{,}1\ \text{Hz}$ to
  11 200 Hz range (upper end exclusive per the formulas), with a code note in
  [`tonality.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tonality.py).
- **Status:** unreported.

## ECMA-418-1:2024 (3rd edition), Formula (21) (repeated constant term)

- **Location:** clause 12.3, Formula (21) (printed p. 17), the curve fit for
  the lower band-edge frequency $f_{1,L}$ of the lower critical band.
- **The print:** $f_{1,L} = C_{L,0} + C_{L,0} f_t + C_{L,2} f_t^{2}$.
- **The problem:** the linear coefficient repeats the constant term. The
  where-list immediately below the formula declares "$C_{L,0}$, $C_{L,1}$,
  $C_{L,2}$ are constants given in Table 2", Table 2 tabulates a $C_{L,1}$
  column, and the parallel Formula (22) for the upper band edge prints
  $f_{2,U} = C_{U,0} + C_{U,1} f_t + C_{U,2} f_t^{2}$ correctly. The misprint
  is numerically fatal, not cosmetic: over the middle fit range
  ($171{,}4 \le f_t \le 1\,600$) Table 2 gives $C_{L,0} = -149{,}5$ and
  $C_{L,1} = 1{,}001$, so the printed form returns
  $-149{,}5 - 149{,}5 f_t - 6{,}90 \cdot 10^{-5} f_t^2$, negative everywhere,
  instead of a band edge a little below $f_t$.
- **Evidence:** the formula, its own where-list and Table 2 on one page, with
  Formula (22) as the consistent control. Verified on PDF page 25 (printed p.
  17) of ECMA-418-1:2024 (3rd edition).
- **Library behaviour:** implements the $C_{L,1}$ reading, which is the only
  one that returns a usable band edge, with a code note in
  [`tonality.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tonality.py).
- **Status:** unreported.

## ECMA-418-1:2024 (3rd edition), clause 11.3 (unresolved field references)

- **Location:** clause 11.3 "Determination of masking noise level" (printed p.
  12), the sentence introducing the critical bandwidth.
- **The print:** "The critical bandwidth Δf_c is determined from Formula
  **Error! Reference source not found.Error! Reference source not found.**
  with f_0 set equal to the frequency of the discrete tone under
  investigation, f_t".
- **The problem:** two unresolved word-processor field references were
  typeset, in bold, in place of the formula numbers, and shipped in the
  published third edition. The intended targets are unambiguous from the rest
  of the sentence, which goes on to name Formulae (4) and (5) or (7) and (8)
  for the band edges: the critical bandwidth itself is Formula (2), and
  Formula (3) is the relation $f_2 - f_1 = \Delta f_c$ that turns it into band
  edges.
- **Evidence:** the clause as printed. Verified on PDF page 20 (printed p.
  12), PDF page 18 (printed p. 10) and PDF page 30 (printed p. 22) of
  ECMA-418-1:2024 (3rd edition).
- **Library behaviour:** none required; the library implements the critical
  bandwidth from Formulae (3)/(6) directly.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 5.1.5.2 (last block index)

- **Location:** clause 5.1.5.2, the segmentation of the zero-padded signal for
  the roughness/fluctuation-strength block sizes.
- **The print:** the index of the last block is given as
  $l_\text{last} = \lceil (n + s_b)/s_h \rceil$.
- **The problem:** the formula is internally inconsistent: blocks placed at
  that index overrun the zero-padded signal defined by clause 5.1.2.2, and the
  resulting Formula (103) time grid becomes non-monotonic. The only
  self-consistent reading is to stop at the last block that fits inside the
  padded signal and align it flush with its end.
- **Evidence:** direct evaluation of the block start indices against the
  padded length for the clause 7.1.1 block/hop sizes; the flush-to-end reading
  reproduces the Clause 7 roughness calibration ($1\ \text{asper}$) to
  $0{,}9999$.
- **Library behaviour:** implements the flush-to-end reading with a code note
  in
  [`_roughness_ecma.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/_roughness_ecma.py).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9.1.4, Formula (127) (HSA kernel phase)

- **Location:** clause 9.1.4, Formula (127), the spectral kernel of the
  envelope analysis window used by the High-resolution Spectral Analysis.
- **The print:** the kernel's phase factor is
  $\exp(-j \cdot 2\pi \cdot f_n(k) \cdot (\tilde{s}_b - n_{ze} + n_{zb} - 1))$.
- **The problem:** the kernel is, by construction, the DFT of the rectangular
  analysis window of Formula (120) modulated to the candidate rate; that is
  the model Formula (124) fits to the measured DFT spectrum. That DFT has the
  phase
  $\exp(-j \cdot \pi \cdot f_n \cdot (\tilde{s}_b - n_{ze} + n_{zb} - 1))$;
  the printed factor doubles it (and is also inconsistent with the $\pi$
  arguments of the printed sine terms of the same formula). With the printed
  phase the fitted model cannot reproduce the spectrum of a noiseless windowed
  sinusoid, contradicting the clause's own statement that the HSA achieves
  "theoretically infinite resolution for signals without noise".
- **Evidence:** independent derivation of the window DFT plus numerical
  recomputation: with $\pi$ the least-squares fit recovers the constant part,
  amplitudes and phases of synthetic noiseless envelopes to machine precision
  and the Formula (135) residual vanishes; with the printed $2\pi$ the kernel
  deviates from the window DFT by amounts of the order of the kernel itself
  and the residual stays of the order of the signal energy.
- **Library behaviour:** implements the $\pi$ reading, pinned by a regression
  test on the exact recovery of synthetic line pairs.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9.1.5, Formula (144) (bin offset)

- **Location:** clause 9.1.5, Formula (144), the modulation rate of a local
  maximum of the envelope power spectrum.
- **The print:** the rate is the three-bin amplitude-weighted centroid of the
  peak position **minus one**, scaled by $\Delta f$.
- **The problem:** clause 9.1.4 (below Formula (122)) defines the spectral
  index $k$ as mapping to the modulation rate
  $k \cdot \tilde{r}_s/\tilde{s}_b$ with $k$ starting at 0. A symmetric local
  maximum at bin $k$ has centroid $k$, and the printed formula then assigns it
  the rate $(k - 1) \cdot \Delta f$, one full bin ($0{,}73\ \text{Hz}$) low,
  which at fluctuation-strength rates is fatal (a true $1{,}46\ \text{Hz}$
  modulation would be reported as $0{,}73\ \text{Hz}$). The offset is only
  consistent with 1-based spectral-line positions, contradicting the
  standard's own definition of $k$.
- **Evidence:** cross-check of Formula (144) against the $k$-to-rate mapping
  stated below Formula (122).
- **Library behaviour:** uses the centroid directly (no offset) with the
  0-based $k$ of Formula (122).
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9.1.7 (units of the fine-tuning constants)

- **Location:** clause 9.1.7, Formulae (149)-(152), the damped Newton fine
  tuning of the dominant modulation rate.
- **The print:** differential step $\Delta x = 10^{-5}$, damped-step cap
  $2 \cdot 10^{-4}$, stop tolerance $10^{-7}$ and an iteration limit of 40,
  with the starting point $x_0 = \tilde{f}_{c,i_\text{max}}$ (a rate in Hz)
  and the failure check
  $|f_{c,1,\text{opt}} - \tilde{f}_{c,i_\text{max}}| > 1{,}25 \cdot \Delta f$.
- **The problem:** the constants carry no units. Read in Hz, the damped step
  is capped at $5 \cdot 10^{-5}\ \text{Hz}$ per iteration
  ($2 \cdot 10^{-3}\ \text{Hz}$ over all 40 iterations), so the tuning cannot
  move appreciably and the $1{,}25 \cdot \Delta f$
  ($\approx 0{,}92\ \text{Hz}$) failure check is unreachable; the whole clause
  would be inert. Read as normalized modulation rates $f/\tilde{r}_s$ (the
  variable in which the Formula (127) kernel frequencies are expressed), the
  same constants give a $0{,}075\ \text{Hz}$ damped per-iteration cap
  ($\approx 2{,}9\ \text{Hz}$ over the 39 iterations), a
  $1{,}5 \cdot 10^{-4}\ \text{Hz}$ stop tolerance and a reachable failure
  check, all consistent with the clause's purpose.
- **Evidence:** dimensional analysis of the printed constants against the
  $0{,}7324\ \text{Hz}$ spectral resolution and the failure threshold.
- **Library behaviour:** applies the constants as normalized modulation rates.
- **Status:** unreported.

## ECMA-418-2:2025 (4th edition), clause 9 introduction (broken cross-reference)

- **Location:** clause 9, third paragraph of the introduction, on the
  HSA-based loudness prediction.
- **The print:** "loudness scaling is improved by using HSA-based loudness
  prediction (see Clause 0)".
- **The problem:** "Clause 0" does not exist; the HSA-based loudness scaling
  is described in clause 9.1.10 (an unresolved field reference).
- **Evidence:** the clause listing of the standard itself.
- **Library behaviour:** none required (the intended target is unambiguous).
- **Status:** unreported.
