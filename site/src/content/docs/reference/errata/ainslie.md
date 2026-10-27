---
title: "Errata in Ainslie (2010)"
description: "Errata in Ainslie (2010): 2 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 2 entries of the [errata registry](/phonometry/reference/errata/) on Ainslie (2010), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Ainslie (2010), Equation (4.6) vs its own folio 177, and the exponent of Equation (4.13)

- **Location:** *Principles of Sonar Performance Modelling* (Springer 2010),
  Equation (4.6) on printed folio 127; the sea-water density quoted in
  Section 4.4 on printed folio 177; Equation (4.13) on printed folio 135.
- **The print:** Equation (4.6) gives the density of sea water as
  $\hat\rho = 1027 + 4{,}3\times10^{-7}\hat P_\mathrm{w} + 0{,}75[S-35] -
  0{,}16[\hat T-10] - 0{,}004[\hat T-10]^2$, attributed to Pierce (1989,
  p. 34), with the units fixed by Equations (4.7) to (4.10) on folio 128:
  pressure in pascals, temperature in degrees Celsius, density in $\text{kg/m}^3$.
  Equation (4.4) on folio 127 defines that pressure as
  $P_\mathrm{w}(z) = P_\mathrm{atm} + \int_0^z \rho g\,\mathrm{d}\zeta$,
  and Equation (4.11) on folio 128 evaluates it to $98\,066{,}5 \times 1{,}04
  = 101\,989{,}16$ Pa at the surface. Folio 177 then states, for the ratios
  that scale the Bachman sediment correlations, "*standard conditions involving
  atmospheric pressure, a temperature of 23 °C, and salinity 35*" with
  $\rho_\mathrm{w} = 1024{,}2\ \text{kg/m}^3$.
- **The problem:** two defects, of different kinds.

  (a) The 1024,2 of folio 177 does not follow from Equation (4.6) read with
  Equation (4.4). At 23 °C, salinity 35 and one atmosphere the equation gives
  1024,287 9, which prints as 1024,3. The printed 1024,2 is what the equation
  gives with its pressure term set to zero, that is, reading $P_\mathrm{w}$ as
  a gauge pressure against the definition the same chapter states. The
  difference is $0{,}043\,9\ \text{kg/m}^3$, or 4,3 parts in a hundred thousand.

  (b) Equation (4.13), which rearranges (4.6) to estimate salinity from a
  measured density, prints the pressure coefficient as $4{,}3\times10^{-5}$
  where (4.6) has $4{,}3\times10^{-7}$. Two orders of magnitude, and not a
  restatement of a different quantity: it is the same coefficient in the same
  role. Carried through at 23 °C it gives $1028{,}63\ \text{kg/m}^3$ against 1024,29, an
  error of 0,42 %.
- **Evidence:** Equation (4.6) evaluated at the stated conditions with the
  pressure of Equation (4.11), against the value folio 177 prints; and the two
  printed exponents compared directly. Verified on PDF pages 157, 158, 165 and
  207 (printed pp. 127, 128, 135 and 177) of the Springer 2010 edition.
- **Library behaviour:** implements Equation (4.6) with the absolute pressure
  its own Equation (4.4) defines, because a printed definition outranks a
  rounded quotation of a derived value three chapters later. The discrepancy is
  below every tolerance in this library, so nothing turns on the choice; what
  would have turned on it is picking a side silently. Equation (4.13) is not
  implemented ([`tests/fluids/test_water.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_water.py),
  conformance checks "Sea water (Ainslie 2010)").
- **Status:** unreported.

## Ainslie, Principles of Sonar Performance Modelling (2010), Eq. (9.57)

*Textbook, not a standard.*

- **Location:** Section 9.1.1.2.4 (printed p. 457), the transition range
  between the mode-stripping and single-mode regimes of the Weston flux model.
- **The print:** $r_\text{MS} \approx k^2 H_e^3/(9\eta)$, where $H$ is the
  water depth, $H_e$ the Weston effective depth of Eq. (9.55),
  $k = \omega/c_w$ and $\eta$ the reflection loss gradient.
- **The problem:** the sentence immediately above it prescribes the
  derivation, "estimated by equating θ_n and θ_eff with n = 3/2". The two
  angles are four printed pages apart, not on the same page as an earlier
  revision of this entry stated:
  - Eq. (9.47), $\theta_\text{eff} = (\pi H/(4\eta r))^{1/2}$, **printed p.
    453**, with the **true water depth $H$** (it comes from the multipath
    integral Eq. (9.46), whose $1/(rH)$ prefactor is the cylinder area
    $A_\text{CS} = 2\pi r H$ of Eq. (9.44), so $H$ is the depth that counts
    bottom bounces);
  - Eq. (9.56), $\theta_n \approx n\pi/(k H_e)$, **printed p. 457**, with the
    **effective depth $H_e$** (mode angles are set by the apparent
    pressure-release boundary).

  Equating them at $n = 3/2$ gives $\pi H/(4\eta r) = 9\pi^2/(4k^2H_e^2)$,
  that is **$r_\text{MS} = k^2H_e^2H/(9\pi\eta)$**. The printed form is larger
  by $\pi H_e/H$. The factor $\pi$ is unconditional: it survives even if $H_e$
  is substituted for $H$ in Eq. (9.47), which is presumably how the printed
  $H_e^3$ arose, and that reading would give $k^2H_e^3/(9\pi\eta)$, still
  $\pi$ below the print. The residual $H_e/H$ is the depth substitution
  itself, and it tends to 1 at high frequency. The other transition of the
  same section, Eq. (9.50) $r_\text{CS} = \pi H/(4\eta\psi_c^2)$, follows its
  own derivation exactly (it is where Eq. (9.42) and Eq. (9.49) cross), so the
  defect is confined to Eq. (9.57).
- **Evidence:** the symbolic re-derivation above, checked numerically for
  $H = 50\ \text{m}$, $f = 250\ \text{Hz}$, $c_w = 1500\ \text{m/s}$ over the
  Table 9.1 sand seabed ($\eta = 0.28\ \text{Np/rad}$, $\psi_c = 33.56^\circ$,
  $H_e = 53.63\ \text{m}$, $k = 1.047\ \text{m}^{-1}$):

  | | $r_\text{MS}$ | $\theta_\text{eff}$ there (Eq. 9.47) |
  |---|---|---|
  | derivation, $k^2H_e^2H/(9\pi\eta)$ | 19.9 km | 4.808° |
  | printed Eq. (9.57), $k^2H_e^3/(9\eta)$ | 67.1 km | 2.619° |

  The ratio $67.1/19.9$ is $\pi H_e/H = 3.3695$ to every digit carried. The
  angle column is an independent check that does not depend on how the
  derivation is read: the first two mode angles of Eq. (9.56) are
  $\theta_1 = 3.205^\circ$ and $\theta_2 = 6.410^\circ$, so
  $\theta_{3/2} = 4.808^\circ$. At the derived range the effective angle is
  exactly $\theta_{3/2}$, halfway between the first two modes, which is what
  the text asks for. At the printed range it has fallen to 2.619°, **below
  $\theta_1$ itself**: the second mode would have been stripped long before,
  so that range cannot be where the single-mode regime begins. Both printed
  formulae are confirmed on PDF page 483 (printed p. 453) and PDF page 487
  (printed p. 457) of Ainslie, Principles of Sonar Performance Modelling
  (2010).
- **Library behaviour:** `weston_regime_boundaries` in
  [`propagation/weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/propagation/weston_regimes.py)
  implements the derivation-consistent $k^2H_e^2H/(9\pi\eta)$, which is also
  what keeps $\theta_\text{eff}$ defined with $H$ everywhere the module
  evaluates Eq. (9.47). The equating rule is pinned by
  `test_mode_stripping_boundary_equates_theta_eff_with_mode_3_over_2`, which
  rebuilds both angles from the printed equations rather than from the
  implementation, and the shared definition of $\theta_\text{eff}$ by
  `test_composite_loss_and_the_boundary_use_the_same_effective_angle` (both in
  [`tests/underwater/propagation/test_weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/tests/underwater/propagation/test_weston_regimes.py)).
- **Status:** unreported (textbook rather than a standard).
