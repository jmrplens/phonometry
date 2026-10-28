---
title: "Errata in Maa (1998)"
description: "Errata in Maa (1998): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Maa (1998). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Maa (1998), "Potential of microperforated panel absorber", JASA 104(5), Eq. (5b)

- **Location:** Eq. (5b), the mass-reactance coefficient of the
  microperforated panel, printed as
  $k_m = 1 + [1 + k^2/2]^{-1/2} + 0.85\,d/t$.
- **The print:** the first bracket term reads $(1 + k^2/2)^{-1/2}$.
- **The problem:** the same paper's Eq. (4), from which (5b) is factored,
  prints the term as $(3^2 + k^2/2)^{-1/2}$, and only that form reproduces the
  Crandall low-$k$ limit $Z_1 \to (4/3) j\omega\rho_0 t$ of the paper's own
  Eq. (3a): at $k \to 0$ the printed (5b) gives an internal mass factor of 2
  instead of 4/3. The paper's own Fig. 1 confirms it: with
  $0.85 \cdot d/t = 0.85$ the plotted $k_m$ starts near $2.2$ ($= 4/3 + 0.85$)
  at $k = 0.1$, not at $2.85$.
- **Evidence:** recomputation of both bracket variants against Eq. (4), Eq.
  (3a) and the Fig. 1 curve; the exact Bessel solution of Eq. (2) agrees with
  Eq. (4) within Maa's stated $\sim 6\,\%$ only with the $3^2$ form (the 1
  form errs by $>30\,\%$ at low $k$). Verified on PDF page 2 (printed p. 2862)
  of Maa (1998), "Potential of microperforated panel absorber", JASA 104(5),
  which carries Eq. (4) and Eq. (5b) fifteen lines apart on the same column.
- **Library behaviour:** implements the exact Eq. (2) (no approximation), so
  the misprint does not enter the code; the regression test
  ``test_maa_exact_vs_wide_range_approximation`` pins the exact solution to
  the corrected Eq. (4) form.
- **Status:** unreported (journal paper; the correct form appears in Maa's
  earlier 1975/1987 papers and in secondary literature).
