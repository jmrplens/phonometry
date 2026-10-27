---
title: "Errata in Jiménez et al. (2017)"
description: "Errata in Jiménez et al. (2017): 2 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 2 entries of the [errata registry](/phonometry/reference/errata/) on Jiménez et al. (2017), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Jiménez, Groby, Pagneux & Romero-García (2017), Appl. Sci. 7(6), 618, Eqs. (7)-(8)

- **Location:** Eqs. (7) and (8), the rectangular-duct visco-thermal effective
  density and bulk modulus (Stinson's series, used for the square necks and
  cavities of the slit + Helmholtz-resonator absorber).
- **The print:** the leading normalising constant of both series is 4:
  $\rho_\text{eff} = -\rho_0 \cdot a^2 b^2/(4 \cdot G_\rho^2 \cdot \Sigma)$
  and the matching $4 \cdot (\gamma - 1) \cdot G_\kappa^2/(a^2 b^2)$ factor
  inside $\kappa_\text{eff}$.
- **The problem:** the correct constant is 64 (a factor-16 error). Only 64
  reproduces the exact limits of the model: as the boundary layers vanish
  $\rho_\text{eff} \to \rho_0$ and $\kappa_\text{eff} \to \kappa_0$ (the
  printed 4 gives $16 \cdot \rho_0$), and at DC the square duct's
  $j\omega \cdot \rho_\text{eff}$ tends to the exact Shah-London Poiseuille
  flow resistivity: the series value $a^6/(64 \cdot S_0) = 28.4542$ matches
  $fRe/2 = 28.455$ (in units of $\eta/a^2$), where $S_0$ is the double
  transverse-mode sum at $G = 0$; the printed 4 gives sixteen times that.
- **Evidence:** evaluation of both constants against the boundary-layer-free
  limits and the Shah-London exact square-duct value; the wide-duct limit of
  the series also only matches the papers' own slit model (Eq. (6)) with 64.
- **Library behaviour:** implements 64 with a docstring note; the limits are
  pinned in
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py)
  and the conformance check "Poiseuille limit (Stinson 1991)".
- **Status:** unreported (journal paper rather than a standard).

## Jiménez et al. (2017), Appl. Sci. 7(6), 618 / Sci. Rep. 7, 5389, slit-radiation term

- **Location:** Appl. Sci. Eq. (3), the characteristic radiation impedance of
  the slits, and the identical Methods reprint in the metadiffusers paper
  (Sci. Rep. 7, 5389, Eq. (5)).
- **The print:**
  $Z_{\Delta l_\text{slit}} = -i\omega \cdot \Delta l_\text{slit} \cdot \rho_0/(\phi t \cdot S_0)$.
- **The problem:** the term models the added radiation mass of the slit mouth,
  but the printed $-i\omega$ prefactor is an opposite-time-convention
  ($\mathrm{e}^{-i\omega t}$) expression inconsistent with the papers' otherwise
  $\mathrm{e}^{+i\omega t}$ transfer-matrix chain (the $+i$ off-diagonal slit matrices
  of Appl. Sci. Eq. (2) and the $-i$ cotangent-type resonator impedance).
  Transcribed literally into that chain, the correction raises the slit-panel
  resonance where an added mass must lower it: for a 1 mm slit with a 30 mm
  lattice step and 50 mm period the absorption peak moves from 378.6 Hz to
  386.8 Hz as printed, against 370.8 Hz with the mass sign. The neck end
  corrections of the same model behave correctly (they lower the resonator
  resonance).
- **Evidence:** numerical evaluation of both signs of the correction against
  the uncorrected panel; the direction of the neck end corrections of the same
  papers as the consistent control.
- **Library behaviour:** uses the added-mass sign ($+j\omega$ in the
  $\mathrm{e}^{+j\omega t}$ convention of the library), conjugating the printed term
  exactly as it conjugates the papers' Stinson duct series; direction and peak
  are pinned by ``test_slit_radiation_correction_lowers_resonance`` in
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py).
- **Status:** unreported (journal papers rather than standards).
