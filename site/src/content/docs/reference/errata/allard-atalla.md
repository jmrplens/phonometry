---
title: "Errata in Allard & Atalla (2009)"
description: "Errata in Allard & Atalla (2009): 8 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 8 entries of the [errata registry](/phonometry/reference/errata/) on Allard & Atalla (2009), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Allard & Atalla, Propagation of Sound in Porous Media 2e (2009), Eq. (6.85)

*Textbook, not a standard.*

- **Location:** Sect. 6.5.2 (printed p. 123), the second form of the
  shear-wave velocity ratio $\mu_3$.
- **The print:**
  $\mu_3 = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{22})$, offered as
  an alternative to Eq. (6.84), $\mu_3 = -\rho_{12}/\rho_{22}$.
- **The problem:** the two printed forms are not equal. Substituting the shear
  wavenumber of Eq. (6.83),
  $\delta_3^2 = (\omega^2/N)(\rho_{11}\rho_{22} - \rho_{12}^2)/\rho_{22}$,
  into the printed Eq. (6.85) gives $-\rho_{12}^2/\rho_{22}^2$, which is Eq.
  (6.84) multiplied by the spurious factor $\rho_{12}/\rho_{22}$. The
  denominator should read $\omega^2\rho_{12}$.
- **Evidence:** the book's own derivation. Eq. (6.80), printed p. 122, is
  $-\omega^2\rho_{11}\psi_s - \omega^2\rho_{12}\psi_f = N\nabla^2\psi_s = -N\delta_3^2\psi_s$,
  so $(N\delta_3^2 - \omega^2\rho_{11})\psi_s = \omega^2\rho_{12}\psi_f$ and
  therefore
  $\mu_3 = \psi_f/\psi_s = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{12})$.
  With that reading the two forms agree identically wherever $\rho_{12}$ is
  non-zero; at $\rho_{12} = 0$ the corrected quotient is $0/0$ while Eq.
  (6.84) stays defined and gives $\mu_3 = -\rho_{12}/\rho_{22} = 0$, which is
  the value to use there. The printed form instead differs from Eq. (6.84) by
  the factor $\rho_{12}/\rho_{22}$, so it coincides with it only where that
  ratio is exactly 0 or exactly 1. With
  $\rho_{12}/\rho_{22} = \rho_0/(\phi\rho_\text{eq}) - 1$ those two cases ask
  for $\rho_\text{eq} = \rho_0/\phi$ and $\rho_\text{eq} = \rho_0/(2\phi)$,
  both real; the effective density of a lossy porous medium is complex, so
  neither is ever met. Verified on PDF page 132 (printed p. 123) of Allard &
  Atalla, Propagation of Sound in Porous Media 2e:2009, which carries both
  printed forms, and on the facing page for Eq. (6.80).
- **Library behaviour:** `biot_waves` implements Eq. (6.84) as printed, and
  `test_shear_velocity_ratio_matches_the_corrected_second_printed_form` checks
  it against the corrected Eq. (6.85) over four decades of frequency, and also
  asserts that the form exactly as printed disagrees.
- **Status:** unreported.

## Allard & Atalla 2e (2009), Eq. (11.48) and Table 11.1 (poroelastic layer)

*Textbook, not a standard.*

- **Location:** Sect. 11.3.3 (printed pp. 251-252), the fluid normal stress
  $\sigma_{33}^f$ of a poroelastic layer and the matrix $[\Gamma]$ it feeds.
- **The print:** Eq. (11.48) reads

  $$
  \sigma_{33}^f = \sum_i (Q + R\mu_i)(k_t^2 + k_{i3}^2)
  \left\{ -(A_i - A'_i)\cos(k_{i3}x_3) + j(A_i - A'_i)\sin(k_{33}x_3) \right\}
  $$

  and Table 11.1 writes $k_{i3}$ in the two columns that carry $\mu_1$, $D_1$
  and $E_1$.
- **The problem:** two independent misprints in the same equation, plus a
  subscript slip in the table.
  - The coefficient of the *symmetric* amplitude $(A_i + A'_i)$ is missing:
    Eq. (11.48) attaches both terms to $(A_i - A'_i)$, which would leave the
    first and third columns of $[\Gamma]$ with no $\sigma_{33}^f$ entry at
    all, contradicting Table 11.1, whose row 6 prints $-E_1 \cos(k_{13}x_3)$
    and $-E_2 \cos(k_{23}x_3)$ in exactly those columns. The first term is
    $-(A_i + A'_i)\cos(k_{i3} x_3)$.
  - The sine carries $k_{33}$, the *shear* wave-number component, inside a sum
    over the two compressional waves $i = 1, 2$. It must be $k_{i3}$. Table
    11.1 again gives the intended reading: its row 6 has
    $j E_1 \sin(k_{13}x_3)$ and $j E_2 \sin(k_{23}x_3)$, and zero in both
    shear columns, because a shear wave produces no dilatation and therefore
    no $\sigma_{33}^f$.
  - Table 11.1 prints the running subscript $k_{i3}$ in its first two columns,
    which belong to the first compressional wave alone: the $\mu_1$, $D_1$ and
    $E_1$ in the same columns make $k_{13}$ the only consistent reading.
- **Evidence:** the two readings above are forced by Table 11.1, which the
  same page declares to be the tabulation of Eqs. (11.37), (11.38) and
  (11.46)-(11.48). They are also what the stress-strain relation Eq. (11.41),
  $\sigma_{33}^f = R\,\mathrm{div}\,u_f + Q\,\mathrm{div}\,u_s$, gives when
  the displacement potentials of Eqs. (11.22)-(11.25) are differentiated
  directly. Verified on PDF page 257 (printed p. 251) and PDF page 258
  (printed p. 252) of Allard & Atalla, Propagation of Sound in Porous Media
  2e:2009, which carry Eq. (11.48) and the two Table 11.1 columns as printed.
- **Library behaviour:** the $[\Gamma]$ of Table 11.1 is implemented with the
  corrected readings, and
  `test_gamma_matches_the_field_rebuilt_from_the_potentials` checks all
  thirty-six of its entries at three frequencies, three depths and three
  angles of incidence against the field rebuilt from Eqs. (11.22)-(11.28)
  without going through the table.
- **Status:** unreported.

## Allard & Atalla 2e (2009), Sect. 6.6.3 (thickness of the second sample)

*Textbook, not a standard.*

- **Location:** Sect. 6.6.3, printed p. 129, the two glass-wool samples whose
  measured and predicted surface impedances are Figures 6.10 and 6.11.
- **The print:** the first sentence says the impedances are shown "for l = 10
  cm and l = 5.4 cm"; two sentences later the peak of the second sample is
  placed at "860 Hz for l = 5.6 cm", and the caption of Figure 6.11 says "l =
  5.6 cm".
- **The problem:** the two thicknesses cannot both be right.
- **Evidence:** textual, and only textual. Two printed statements carry 5.6
  cm, the sentence about the 860 Hz peak and the independent caption of Figure
  6.11, against one carrying 5.4 cm; a single slip in the opening sentence is
  the shorter explanation than the same slip made twice. The numbers do
  **not** settle it, and this entry does not claim they do. The book gives no
  peak-finding rule, and the answer follows the rule chosen:
  - Taking the peak as the maximum of $\text{Im}(Z_s)$, Eq. (6.107) on the
    fully specified Table 6.1 glass wool gives 863.5 Hz for 5.6 cm (+0.4 %
    against the printed 860) and 896.2 Hz for 5.4 cm (+4.2 %), which favours
    5.6 cm. But the same rule puts the undisputed 10 cm sample at 480.0 Hz
    against its printed 470, a +2.1 % bias of the same size as the effect
    being resolved.
  - Taking the peak as the maximum of $|Z_s - Z_{s,\text{rigid}}|$, which is
    the departure the same paragraph describes ("close to each other, except
    around the peaks which are not predicted by the one-wave model"), the 10
    cm sample lands at 469.2 Hz (-0.2 %) and **both** printed frequencies then
    come out of the pair (10 cm, 5.4 cm): 861.2 Hz for 5.4 cm (+0.1 %) against
    831.0 Hz for 5.6 cm (-3.4 %). That rule favours 5.4 cm.
  - Scaling the 10 cm peak is no help either, and leans the other way from the
    conclusion: $470 \times (10/5.4) = 870\ \text{Hz}$ is 10 Hz from the
    published 860, $470 \times (10/5.6) = 839\ \text{Hz}$ is 21 Hz from it.
  - The agreement of "860 Hz" with "5.6 cm" is in any case partly circular,
    since both sit in the same clause: it tests that sentence against itself,
    not which of the two sentences is the misprint.
  Verified on PDF page 138 (printed p. 129) of Allard & Atalla, Propagation of
  Sound in Porous Media 2e:2009, on which the lone 5.4 cm and the 5.6 cm of
  the 860 Hz clause sit on the same page, and on PDF page 139 (printed p. 130)
  of the same edition for the Figure 6.11 caption, the second sentence
  carrying 5.6 cm.
- **Library behaviour:** recorded, with no effect on the implementation.
  `test_impedance_peak_of_the_thin_layer_resolves_the_printed_thickness` pins
  the 5.6 cm peak against the published 860 Hz under the $\text{Im}(Z_s)$ rule
  and checks that the 5.4 cm reading is the worse of the two under that rule.
- **Status:** unreported, and the weakest of the four entries here: the
  conclusion rests on the two-against-one reading of the printed page, not on
  a computation.

## Allard & Atalla 2e (2009), Sect. 6.5.4 (the frame-borne velocity ratio)

*Textbook, not a standard.*

- **Location:** Sect. 6.5.4, printed p. 125, the one sentence of the book that
  quotes computed values of $\mu_b$ for the Table 6.1 glass wool.
- **The print:** "The ratio modulus $|\mu_b|$ of the velocities of the frame
  and the air for the frame-borne wave decreases from 1.0 at 50 Hz to 0.82 at
  1500 Hz."
- **The problem:** the two quoted values are the *real part* of $\mu_b$, not
  its modulus. $\mu_b$ is complex, and the sentence names the modulus
  explicitly.
- **Evidence:** on the fully specified Table 6.1 material the model gives
  $\mu_b(1500\ \text{Hz}) = 0.811 + 0.473j$. Its real part is **0.811**, 1.1 %
  from the printed 0.82; its modulus is **0.939**, 14.5 % away. Read as the
  real part, the sentence is right at both ends and describes a monotone
  decrease: $\text{Re}(\mu_b)$ is 1.002 at 50 Hz and passes through 0.82 at
  1467 Hz, 2.2 % from the printed 1500 Hz. Read as the modulus it is right at
  neither: $|\mu_b|$ is 1.002 at 50 Hz but *rises* to 1.008 by 400 Hz before
  turning over, and only reaches 0.82 at 2634 Hz, 76 % above the printed
  frequency. No admissible reading of the printed inputs closes that gap. With
  the loss factor at 0 or at 0.2, the viscous length halved or doubled,
  $\Lambda' = 2\Lambda$ in place of the printed $1.1 \cdot 10^{-4}\ \text{m}$,
  the resistivity halved or doubled, the tortuosity at 1 or the Poisson
  coefficient at 0.3, $|\mu_b(1500)|$ moves only between 0.874 and 1.073. The
  closest of the eight, 0.874 at zero loss factor, is still 6.6 % from the
  printed 0.82, and it loses the 495 Hz branch crossing of the same section
  altogether; the only variant that keeps that crossing
  ($\Lambda' = 2\Lambda$, 495.2 Hz) leaves $|\mu_b|$ at 0.937. Reading the
  sentence as $\text{Re}(\mu_b)$ needs no variant at all. Verified on PDF page
  134 (printed p. 125) of Allard & Atalla, Propagation of Sound in Porous
  Media 2e:2009, which carries the sentence and its 0.82.
- **Library behaviour:** `biot_waves` computes $\mu_b$ from Eq. (6.71) as
  printed. The conformance row and
  `test_frame_borne_velocity_ratio_matches_the_two_published_values` are
  written against $\text{Re}(\mu_b)$, and say so.
- **Status:** unreported.

## Allard & Atalla 2e (2009), Table 11.7 (the figure its caption names)

*Textbook, not a standard.*

- **Location:** Table 11.7, PDF page 280, printed p. 274, the parameter table
  of the carpet, screen and fibrous layer of Sect. 11.7.2.
- **The print:** the caption reads "The parameters used to predict the surface
  impedance of the material represented in Figure 11.6".
- **The problem:** Figure 11.6 is on printed p. 266 and is the plastic foam
  under a sheet of glass wool, whose parameters are Table 11.3. The structure
  Table 11.7 tabulates, a carpet in two layers over an impervious screen over
  a fibrous layer, is Figure 11.16, printed on the same page as the table.
- **Evidence:** the prose beside Figure 11.16 says the material parameters are
  given in Table 11.7, and the four row names of the table are the four layers
  Figure 11.16 labels. Verified on PDF page 280 (printed p. 274) and PDF page
  272 (printed p. 266) of Allard & Atalla, Propagation of Sound in Porous
  Media 2e:2009.
- **Library behaviour:** the three porous rows are transcribed as printed and
  the data file's `about` names Figure 11.16 as the structure, with the
  caption's own wording quoted.
- **Status:** unreported.

## Allard & Atalla 2e (2009), Table 11.8 (the thickness of the glass wool)

*Textbook, not a standard.*

- **Location:** Table 11.8, PDF page 281, printed p. 275, the glass wool
  bonded onto an aluminium plate for the normal-incidence transmission example
  of Sect. 11.7.3.
- **The print:** the table gives the glass wool a thickness of 3,8 mm; the
  prose of Sect. 11.7.3 on the facing folio says "A layer of the glass wool
  studied in Section 6.5.4, of thickness 5 cm, is bonded on to a plate of
  aluminium, of thickness 1 mm".
- **The problem:** the two thicknesses differ by more than an order of
  magnitude and cannot both describe the layer of Figure 11.18.
- **Evidence:** the plate agrees between the two, 1 mm in both, which is what
  makes the glass wool the disagreeing cell rather than a column read out of
  order. Verified on PDF page 281 (printed p. 275) for the table and PDF page
  280 (printed p. 274) for the sentence, in Allard & Atalla, Propagation of
  Sound in Porous Media 2e:2009.
- **Library behaviour:** the row carries the printed 3,8 mm, and its `note`
  records the sentence. Nothing computes with the thickness: the equivalent
  fluid of this specimen does not use it.
- **Status:** unreported.

## Allard & Atalla 2e (2009), Table 11.9 (the thickness of the plate)

*Textbook, not a standard.*

- **Location:** Table 11.9, PDF page 282, printed p. 276, the foam and plate
  of the diffuse-field transmission example of Sect. 11.7.4.
- **The print:** the plate row gives a thickness of 1,6 mm; the prose of
  Sect. 11.7.4 on the facing folio says "The material is a foam of thickness
  h = 2 . 54 cm bonded onto a 0.6 mm aluminium plate".
- **The problem:** 1,6 against 0,6 mm for the same plate.
- **Evidence:** the foam agrees between the two, the table's 25,4 mm being the
  sentence's 2,54 cm, which places the disagreement in the plate row alone.
  Verified on PDF page 282 (printed p. 276) for the table and PDF page 281
  (printed p. 275) for the sentence, in Allard & Atalla, Propagation of Sound
  in Porous Media 2e:2009.
- **Library behaviour:** the plate is not a porous material and is not in the
  catalogue; the foam row's `note` records the disagreement so that a reader
  reproducing the figure knows which plate the curve assumes.
- **Status:** unreported.

## Allard & Atalla 2e (2009), Table 13.2 (the Young's modulus of the rockwool)

*Textbook, not a standard.*

- **Location:** Table 13.2, PDF page 341, printed p. 337, the 5,75 cm rockwool
  with a central perforation of the double-porosity example.
- **The print:** the column headed E (Pa) carries 4400 for a frame of
  130 kg/m3.
- **The problem:** a frame modulus of 4,4 kPa at that density gives a frame
  wave speed of $\sqrt{4400/130} = 5,8$ m/s, so the quarter-wave resonance of
  a 5,75 cm layer lands near 25 Hz. The text on the next page says the
  numerical model captures "the skeleton resonance occurring around 1350 Hz",
  which the printed modulus cannot produce: 1350 Hz would need about 12,7 MPa,
  three orders of magnitude above the cell.
- **Evidence:** arithmetic on the page's own two cells against the page's own
  sentence. Nothing on the page says what the modulus should be, so this entry
  reports the inconsistency and does not repair it. Verified on PDF page 341
  (printed p. 337) for the table and PDF page 342 (printed p. 338) for the
  sentence, in Allard & Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Library behaviour:** the row carries the printed 4400 Pa and its `note`
  records the resonance the text reports. No example of this library computes
  a skeleton resonance from it.
- **Status:** unreported.
