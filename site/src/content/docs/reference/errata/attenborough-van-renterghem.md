---
title: "Errata in Attenborough & Van Renterghem (2021)"
description: "Errata in Attenborough & Van Renterghem (2021): 2 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 2 entries of the [errata registry](/phonometry/reference/errata/) on Attenborough & Van Renterghem (2021), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Table 5.1

- **Location:** Table 5.1, "Coefficient and exponent values in the Delany and
  Bazley, Miki and modified Miki models", row "Miki [6,7]", coefficient $r$.
- **The print:** $r = 0.0109$.
- **The problem:** the original source (Miki 1990, J. Acoust. Soc. Jpn (E)
  11(1), Eq. (34)) prints
  $\beta(f) = (\omega/c_0)[1 + 0.109 \cdot (f/\sigma)^{-0.618}]$; the table
  drops a digit. With 0.0109 the real part of the Miki wavenumber at
  $f/\sigma = 0.01$ is $1.19$ instead of $2.88$, inconsistent with the same
  table's Delany-Bazley row ($3.10$ from its own $r = 0.0862$, $s = -0.693$)
  and with the "modified Miki" row the book itself derives from it.
- **Evidence:** digit check against the original Miki (1990) paper (Eqs.
  (30)–(34)) and cross-computation of both variants at the fit-range edge.
  Verified on PDF page 168 (printed p. 149) of Attenborough & Van Renterghem,
  Predicting Outdoor Sound 2e:2021, and on PDF page 4 (printed p. 22) of Miki,
  J. Acoust. Soc. Jpn (E) 11(1):1990.
- **Library behaviour:** implements Miki's original 0.109; the digitization
  point $f/\sigma = 0.1$ is pinned in ``tests/reference_data/`` and in the
  conformance check "Miki 1990 Eqs. (30)-(34)".
- **Status:** unreported (textbook rather than a standard).

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Eq. (5.13)

- **Location:** Eq. (5.13), the Johnson-Champoux-Allard bulk complex density,
  with $G(\Lambda) = \sqrt{1 - 4iT\eta\rho_0\omega/(R_S^2\Lambda^2\Omega^2)}$.
- **The print:** the tortuosity $T$ appears to the first power inside
  $G(\Lambda)$.
- **The problem:** Johnson et al. (1987) and the standard JCA formulation (Cox
  & D'Antonio 3e Eq. (6.19); Allard & Atalla) carry $T^2 = \alpha_\infty^2$
  there. The first-power print breaks the high-frequency asymptote that
  defines the viscous characteristic length: with $T^2$ the density tends to
  $(T\rho_0/\Omega)(1 + (1 - j)\delta_v/\Lambda)$ with
  $\delta_v = \sqrt{2\eta/\rho_0\omega}$, while the printed form tends to a
  $\delta_v/(\Lambda\sqrt{T})$ correction, which for $T = 2$ means an error of
  $29\,\%$ in the boundary-layer term for the same $\Lambda$.
- **Evidence:** asymptotic expansion of both variants against the Johnson et
  al. definition of $\Lambda$ and against Cox & D'Antonio Eq. (6.19); the
  library's high-frequency JCA test pins the $T^2$ behaviour. Verified on PDF
  page 173 (printed p. 154) of Predicting Outdoor Sound 2e:2021.
- **Library behaviour:** implements the standard $T^2$ form (Cox & D'Antonio
  Eq. (6.19)); the asymptote is pinned in
  ``test_high_frequency_density_asymptote``.
- **Status:** unreported (textbook rather than a standard).
