---
title: "Errata in Norton & Karczub (2003)"
description: "Errata in Norton & Karczub (2003): 5 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 5 entries of the [errata registry](/phonometry/reference/errata/) on Norton & Karczub (2003), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Norton & Karczub, Fundamentals of Noise and Vibration Analysis for Engineers 2e (2003), Eq. (6.56)

- **Location:** Section 6.6.1, Eq. (6.56), the coupling loss factor of two
  homogeneous plates joined by $N$ point connections (printed p. 418).
- **The print:** the denominator bracket
  $(\rho_{s1}^2 h_1^2 c_{L1}^2 + \rho_{s2}^2 h_2^2 c_{L2}^2)$ appears to the
  first power.
- **The problem:** as printed the expression is not dimensionless. The
  prefactor $4 N h_1 c_{L1}/(\sqrt{3}\,\omega S_1)$ already has the dimensions
  of $\text{m}^2\,\text{s}^{-1}$ over $\text{m}^2\,\text{s}^{-1}$, i.e. unity,
  so the remaining ratio of the two bracketed products must be dimensionless
  too. That requires the sum to be squared, $A_1 A_2/(A_1 + A_2)^2$.
- **Evidence:** the book's own answer to problem 6.13 (printed p. 617). With
  the squared denominator the twelve-bolt aluminium pair gives
  $\eta_{12} = 1.43 \cdot 10^{-2}$ at 125 Hz against the printed
  $1.44 \cdot 10^{-2}$, and matches the whole 125 Hz to 2 kHz column to better
  than $0.7\,\%$; with the printed (unsquared) denominator the result is not a
  loss factor at all. Verified on PDF page 438 (printed p. 418) of Norton &
  Karczub, Fundamentals of Noise and Vibration Analysis for Engineers 2e:2003.
- **Library behaviour:** `point_connection_coupling_loss_factor` in
  [`_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/_junction_transmission.py)
  implements the squared form, with the printed column pinned by a regression
  test
  ([`tests/vibration/structural/test_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_junction_transmission.py))
  and a note at the formula.
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), problem 6.13 answer (eta_21 column)

- **Location:** Answers to problems, problem 6.13 (printed p. 617), the two
  $\eta_{21}$ columns of the welded and bolted tables.
- **The print:** for the two aluminium plates (plate 1: 3 mm, 2.5 m × 1.2 m;
  plate 2: 5.5 mm, 2.0 m × 1.2 m) the answer gives, at 125 Hz,
  $\eta_{21} = 5.77 \cdot 10^{-3}$ (welded) and $2.64 \cdot 10^{-2}$ (bolted).
- **The problem:** both columns are exactly the corresponding $\eta_{12}$
  column multiplied by $h_2/h_1 = 1.833$. The SEA consistency relationship is
  $n_1 \eta_{12} = n_2 \eta_{21}$ (Eq. 6.8) with the flat-plate modal density
  $n = S\sqrt{12}/(2 c_L h)$ of Eq. (6.25), so the correct factor is
  $n_1/n_2 = (S_1 h_2)/(S_2 h_1) = 2.292$. The printed column drops the plate
  area ratio $S_1/S_2 = 1.25$.
- **Evidence:** the ratio of the printed columns is 1.8333 to five digits in
  every band of both tables, which is $h_2/h_1$ exactly; the $\eta_{12}$
  columns themselves reproduce from Eqs. (6.52) to (6.56) to better than 0.7
  %. Verified on PDF page 637 (printed p. 617) of Norton & Karczub 2e:2003,
  the page that carries both answer tables.
- **Library behaviour:** the $\eta_{12}$ columns are used as the regression
  oracle; $\eta_{21}$ is obtained from Eq. (6.8) with the full modal
  densities, and a test pins the 2.292 ratio explicitly
  ([`tests/vibration/structural/test_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_junction_transmission.py)).
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), problem 6.10 (platform area)

- **Location:** Problems, problem 6.10 (printed pp. 593-594) and its answer
  (printed p. 617): a satellite platform coupled to an aluminium cylinder, 500
  Hz octave, printed answers $\eta_{12} = 4.26 \cdot 10^{-4}$,
  $\eta_{21} = 3.92 \cdot 10^{-4}$ and $\Pi_\text{in} = 1.31\ \text{W}$.
- **The print:** the statement gives the aluminium platform as "5 mm thick and
  3.5 m × 3 m", i.e. $10.5\ \text{m}^2$.
- **The problem:** that area is inconsistent with the three printed answers.
  Eq. (6.12) fixes $E_1/E_2 = (\eta_2 + \eta_{21})/\eta_{12} = 6.554$ from the
  printed loss factors alone, whereas the stated geometry with the printed
  velocities (27.2 and 13.2 mm/s) gives 7.88. The energy ratio is independent
  of the modal densities and of the wave speed, so no choice of those can
  reconcile it; only the platform area can. The area the answers imply is 8.73
  $\text{m}^2$, which is $3.5 \times 3$ minus the $\pi(0.75\ \text{m})^2$ footprint of
  the cylinder that Fig. P6.10 shows passing through the platform.
- **Evidence:** with $8.73\ \text{m}^2$ the inversion of Eqs. (6.15), (6.8) and (6.10)
  returns $\eta_{12} = 4.256 \cdot 10^{-4}$, $\eta_{21} = 3.910 \cdot 10^{-4}$
  and $\Pi_\text{in} = 1.306\ \text{W}$, i.e. all three printed answers within
  0.4 %; the cylinder's own energy and modal density come out unchanged either
  way. Verified on PDF page 613 (printed p. 593), which carries the statement
  and its dimensions, and PDF page 637 (printed p. 617), which carries the
  three answers, of Norton & Karczub 2e:2003.
- **Library behaviour:** `power_injection_clf` in
  [`experimental_sea.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/experimental_sea.py)
  implements the inversion as published; the regression test uses the free
  platform area and documents the discrepancy
  ([`tests/vibration/structural/test_experimental_sea.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_experimental_sea.py)).
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), problem 3.14 (structural loss factor)

- **Location:** Problems, problem 3.14 (printed p. 580) and its answer
  (printed p. 611): the octave-band transmission loss of a 20 mm particle
  board panel.
- **The print:** the statement gives the panel a structural loss factor of
  "~$1.5 \times 10^{-2}$"; the answer gives 27 dB at 8 kHz and 38.6 dB at 16 kHz.
- **The problem:** those two values are above the panel's critical frequency
  (4885 Hz for Appendix 4 particle board, $f_c t = 97.7\ \text{m/s}$) and
  therefore follow Cremer's Eq. (3.110), which contains $10\log_{10}(\eta)$.
  With $\eta = 1.5 \cdot 10^{-2}$ the equation gives 37.0 dB and 48.5 dB, ten
  decibels above the printed answers; with $\eta = 1.5 \cdot 10^{-3}$ it gives
  27.0 dB and 38.5 dB.
- **Evidence:** the 10 dB offset is exactly one decade of $10\log_{10}(\eta)$,
  and the frequency dependence of the printed pair independently fixes
  $f_c = 4939\ \text{Hz}$ against the Appendix 4 value of 4885 Hz. The eight
  values below coincidence reproduce exactly from Eq. (3.104) and do not
  involve $\eta$. The discrepancy is a decade in a printed exponent, so the
  two figures were read as images rather than through the text layer. Verified
  on PDF page 600 (printed p. 580) and PDF page 631 (printed p. 611) of Norton
  & Karczub 2e (2003).
- **Library behaviour:** the regression test uses $\eta = 1.5 \cdot 10^{-3}$,
  the value the printed answers require
  ([`tests/building/prediction/test_panel_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_panel_transmission.py)).
- **Status:** unreported (textbook rather than a standard).

## Norton & Karczub 2e (2003), Appendix 4 (the Young's modulus of cork, three powers of ten too large)

- **Location:** Appendix 4, "Physical properties of some common substances",
  part A "Solids", row "Cork", on printed page 605 (PDF page 625).
  Non-normative source: a textbook.
- **The print:** Cork: density $250$ kg/m$^3$, Young's modulus
  $6.2 \times 10^{10}$ Pa, a dash in both the Poisson ratio and the bar speed
  cells, bulk speed $500$ m/s, product of critical frequency and thickness
  $130.7$.
- **The problem:** $6.2 \times 10^{10}$ Pa is the modulus of a glass, and it
  is the value the same table prints for Glass (Pyrex) two rows below. The
  rest of the cork row contradicts it: with the density and the speed the row
  prints, $\rho c^2 = 250 \times 500^2 = 6.25 \times 10^{7}$ Pa, a factor of
  about a thousand smaller. The table's own last column agrees with the
  $500$ m/s rather than with the modulus: it is $c_0^2/(1.8\,c)$ with
  $c_0 = 343$ m/s, and $343^2/(1.8 \times 500) = 130.7$, which is what the page
  prints. The two other foamed or cellular solids in the same block,
  polyurethane and polystyrene, are printed at $1.9 \times 10^{7}$ and
  $1.1 \times 10^{7}$ Pa. The mantissa is consistent with the row and the
  exponent is not.
- **Evidence:** Verified on PDF page 625 (printed p. 605) of Norton &
  Karczub, *Fundamentals of Noise and Vibration Analysis for Engineers* 2e
  (2003). The two moduli, cork's and Pyrex's, are legible and identical on the
  page; the cork row's density, speed and last column are equally legible and
  consistent with each other.
- **What the library does:** the cell is held as `misprinted` in
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py), so the row
  keeps what the book prints and refuses to serve it as a modulus. The page
  does not print the exponent it meant, so no corrected value is supplied. The
  rest of the row is served normally.
- **Status:** unreported.
