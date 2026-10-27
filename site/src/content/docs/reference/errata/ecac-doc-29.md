---
title: "Errata in ECAC Doc 29"
description: "Errata in ECAC Doc 29: 5 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 5 entries of the [errata registry](/phonometry/reference/errata/) on ECAC Doc 29, in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## ECAC Doc 29, 5th ed., Volume 2, Appendix B, Eq. (B-41) (descent deceleration)

- **Location:** Appendix B, section B7.1.1, the deceleration $a$ defined under
  Eq. (B-41), on the page that carries Eq. (B-40) and Eq. (B-41).
- **The print:**
  $a = k^2 \left(\left(\left(\mathrm{Pt1(NextSeg)}_{TAS} - w\right)/\cos\gamma\right)^2 - \left(\left(\mathrm{Point1}_{TAS} - w\right)/\cos\gamma\right)^2\right) / \left(2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma\right)$,
  that is both ground speeds divided by $\cos\gamma$ over twice the slant
  length of the segment.
- **The problem:** the descent slope is counted twice. The mean deceleration
  along the flight path is the change in the square of the along-path speed
  over twice the path length; the printed expression converts the speeds to
  along-path values *and* uses a path length that is already the slant one, so
  it overstates $|a|$ by $1/\cos^2\gamma$. The 4th edition's Eq. (B-21) is
  self-consistent, and the denominator is not what changed: it reads
  $2 \cdot \Delta s/\cos\gamma$ with $\Delta s$ "the ground distance covered",
  which is the same slant length the 5th edition writes as
  $2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma$.
  What changed is the numerator. The 4th edition's Eq. (B-22) defines the
  speeds it divides as *groundspeeds*, $V = V_C\cos\gamma/\sqrt{\sigma} - w$,
  that is the true airspeed resolved into the horizontal plane, so dividing
  each by $\cos\gamma$ correctly restores an along-path speed. The 5th edition
  feeds Eq. (B-41) the profile points' own $\mathrm{TAS}$, which is along-path
  already, and kept the division. Doc 29's own reference results decide it: of
  the twelve points of Volume 3 Part 2 case 2D, flown entirely at that step
  type, nine are reached by the deceleration. The plain ground speeds reproduce
  the tabulated thrust at every one of the twelve, worst deviation 0.047 lb,
  while the printed divided speeds fall short at all nine, by 6.05, 5.47, 4.02,
  3.81, 4.56, 4.45, 0.29, 6.35 and 6.41 lb in profile order: always low, and
  never within the workbook's own 0.05 lb of printed precision. The drag term
  beside it does keep the $\cos\gamma$ the same equation prints, which the same
  points confirm to the same 0.05 lb.
- **Evidence:** reproduction of Volume 3 Part 2 sheet `D1-(Arrival_Results)`
  case 2D under each reading. Verified on PDF page 104 (printed p. B-31) of
  ECAC.CEAC Doc 29, 5th ed., Volume 2: Technical guide, which carries
  Eq. (B-40), Eq. (B-41) and the deceleration under it, and on PDF page 90
  (printed p. B-15) of ECAC.CEAC Doc 29, 4th edition, Volume 2, which carries
  Eq. (B-21) and, immediately under it, the Eq. (B-22) that defines its $V_1$
  and $V_2$ as groundspeeds and so decides the reading.
- **Library behaviour:** `flight_performance` computes the deceleration from
  the plain ground speeds over the slant length, and the helper's docstring
  carries the departure and the numbers above.
  `test_arrival_case_reproduces_every_profile_point` pins all 124 arrival
  points, and the conformance row *ECAC Doc 29 Appendix B approach thrust*
  pins the descent thrust of case 2A.
- **Status:** unreported.

## ECAC Doc 29, 5th ed., Volume 2, Appendix B, Eq. (B-18) (runway gradient)

- **Location:** Appendix B, section B6.1.1, the average acceleration $a$
  defined under Eq. (B-18).
- **The print:** "$a$ is the average acceleration (ft/s$^2$) along the runway,
  equal to: $a = \left(V_C/\sqrt{\sigma}\right)^2/\left(2 \cdot s_{TOw}\right)$",
  with "$V_C$ is the Calibrated Airspeed (**kt**) at *Point2*" and $s_{TOw}$ in
  feet on the same page.
- **The problem:** the expression is declared in ft/s$^2$ and evaluates in
  kt$^2$/ft. The missing factor is $k^2 = 1.68781^2 = 2.8487$, the square of
  the knots-to-feet-per-second constant Doc 29 fixes in B2.2 and carries
  explicitly in Eq. (B-24) and Eq. (B-41), which build accelerations out of the
  same kind of expression. It is not cosmetic: $a$ enters only through
  $a/(a - g\,G_R)$, so understating it by 2.85 overstates the gradient
  correction, and at a 1 % upslope with $V_{CTO} = 162.65$ kt and
  $s_{TOw} = 4900$ ft the dimensionally correct 7.69 ft/s$^2$ gives a factor of
  1.0437 against the literal reading's 1.1353: 8.8 % of take-off distance. The
  4th edition carries the same omission, so it is inherited rather than
  introduced, and prints $\left(V_C\sqrt{\sigma}\right)^2$ where the 5th prints
  $\left(V_C/\sqrt{\sigma}\right)^2$; only the 5th edition's placement is a
  speed the aeroplane has, since $V_C/\sqrt{\sigma}$ is the true airspeed of
  Eq. (B-7).
- **Evidence:** dimensional analysis against the same document's Eq. (B-24)
  and Eq. (B-41). Verified on PDF page 90 (printed p. B-17) of ECAC.CEAC
  Doc 29, 5th ed., Volume 2: Technical guide, and, for the inherited half, on
  PDF page 86 (printed p. B-11) of ECAC.CEAC Doc 29, 4th edition, Volume 2,
  where the same definition sits under Eq. (B-11) and reads
  $\left(V_C\cdot\sqrt{\sigma}\right)^2/\left(2\cdot s_{TOw}\right)$, ft/s$^2$.
  This one cannot be
  arbitrated against the reference results: Volume 3 Part 2's departure case
  sheet `C8-(Departure_Cases)` has no runway-gradient column, so all 17
  reference cases are flown at $G_R = 0$, where Eq. (B-18) is the identity.
- **Library behaviour:** `flight_performance` restores $k^2$ and takes the 5th
  edition's $\sqrt{\sigma}$ placement; the helper's docstring states both
  departures and that no reference case can detect either.
- **Status:** unreported.

## ECAC Doc 29, 5th ed., Volume 2, Appendix B, Eq. (B-21) (mid-step airspeed)

- **Location:** Appendix B, section B6.1.2, the mid-step corrected net thrust
  $\overline{CNT}$ defined under Eq. (B-21), in the branch that computes it from
  Eq. (B-12), that is for every aeroplane the propeller coefficient table
  carries. B4.1 and B4.2 split the turboprops between them without stating a
  rule, so this is not the same set as "the turboprops": of the 20 in ANP v2.3,
  11 sit in the propeller table and reach Eq. (B-12), the other 9 sit in the jet
  table and reach Eq. (B-9), and the 8 piston aeroplanes are all in the
  propeller table.
- **The print:** $\overline{CNT}$ "is the Corrected Net Thrust of the aircraft
  when being located at mid-step, i.e. at the altitude
  $Alt = E_{Apt} + \left(\mathrm{Point\ 1\_Height} + \mathrm{Point\ 2\_Height}\right)/2$",
  and then, under "In the case of Eq. B-12,",
  $V_T = \sqrt{0.5\left(\left(\mathrm{Point\ 2\_TAS}\right)^2 + \left(\mathrm{Point\ 1\_TAS}\right)^2\right)}$,
  the root mean square of the two endpoint true airspeeds.
- **The problem:** the speed contradicts the altitude named one line above it. A
  Climb step is flown at a held calibrated airspeed, so the true airspeed at the
  mid-step altitude is fixed and is $V_C/\sqrt{\sigma}$ evaluated at the
  mid-step $\sigma$ (Eq. B-7); the root mean square of the two endpoint values
  is a different number. The two branches of the same list therefore describe
  two different aeroplanes at the one point they both call mid-step: the jet
  branch prints
  $V_C = \mathrm{Point\ 2\_TAS} \cdot \sqrt{\sigma_{Point\ 2}}$, which is
  the step's own held calibrated airspeed and so places the aeroplane at
  $V_C/\sqrt{\sigma}$ halfway up, while the Eq. (B-12) branch places it at the
  root mean square of the ends. The mean also reads as transplanted. Section
  B6.1.3, for the Accelerate step, is built on exactly this root mean square
  and is self-consistent about it, giving *both* branches the same
  $\overline{V_T} = \sqrt{\left(V_{T2}^2 + V_{T1}^2\right)/2}$ and converting
  it for the jet form with the mid-step $\sqrt{\sigma_{Alt}}$; B6.1.2 keeps the
  Eq. (B-12) line but replaces the jet line with a Point 2 quantity, and only
  one of the two survives the substitution. Of the candidates the printed one
  is the largest: at constant $V_C$ the true airspeed rises convexly with
  altitude, so the root mean square exceeds the arithmetic mean, which exceeds
  the mid-altitude value. Eq. (B-12) makes thrust inversely proportional to
  $V_T$, so the printed speed understates the mid-step thrust, understates
  $\sin\gamma$ and lays the climb down long.
- **Evidence:** reproduction of Volume 3 Part 2 sheet `D2-(Departure_Results)`
  under each reading. The four turboprop departure cases are the only reference
  data that reach this branch, and they are unanimous. On case 56 the final
  profile point is printed at 400814.3 ft: the mid-step altitude reading lands
  it 0.001 ft away, the arithmetic mean 323.944 ft long and the printed root
  mean square 544.944 ft long, against the 0.15 ft the departure distances are
  otherwise matched to. Cases 8, 28 and 68 put the same final point 172.333,
  223.003 and 544.944 ft long under the printed reading and 102.535, 132.673
  and 323.944 ft long under the arithmetic mean, always long and never near the
  printed precision; the mid-step altitude reading is within 0.049 ft of every
  point of all four cases, worst case 28. The departure grows with the height
  of the step, as a convexity error must: on case 8 the printed reading puts
  $V_T$ 0.0225 kt above the mid-step value on the 1500 ft climb and 0.1066 kt
  above it on the 2500 ft one. Verified on PDF page 92 (printed p. B-19) of
  ECAC.CEAC Doc 29, 5th ed., Volume 2: Technical guide, which carries the
  mid-step altitude sentence, the jet branch's $V_C$ and the Eq. (B-12)
  branch's $V_T$ on the one page, and on PDF page 95 (printed p. B-22) of the
  same document for the B6.1.3 pair the Eq. (B-21) line appears to be drawn
  from.
- **Library behaviour:** `flight_performance` evaluates the propeller form at
  the true airspeed the aeroplane has at the mid-step altitude, and the
  Climb-step helper's comment quotes the printed expression, says the model
  departs from it and points here.
  `test_departure_case_reproduces_every_profile_point` pins all 190 departure
  points, four cases of which are flown on Eq. (B-12).
- **Status:** unreported. Of the three Appendix B departures recorded here this
  is the one the reference results decide most sharply, and the only one that
  changes a shipped profile.

## ECAC Doc 29, 5th ed., Volume 2, Appendix D, Table D-6c (the last row is the last row of Table D-6b)

- **Location:** Appendix D, Table D-6c "Revised JETW NPD data using
  SAE-ARP-866A", last row (JETW, SEL, operation D, power setting 22500).
- **The print:** 109.8, 106.0, 103.2, 100.2, 95.2, 89.8, 85.8, 81.4, 76.8 and
  72.3 dB from 200 ft to 25000 ft: the ten values of the last row of Table
  D-6b, the same aeroplane revised with SAE-ARP-5534, printed a few lines above
  it on the same page.
- **The problem:** the text under Table D-5 builds Table D-6c as the Table D-6a
  levels plus the SAE-ARP-866A increments of Table D-5, and the other six rows
  of the table are exactly that, to the last digit. The last row of Table D-6a
  (109.7, 105.7, 102.8, 99.5, 94.0, 88.0, 83.7, 79.0, 73.9 and 68.7 dB) plus
  the DEP_103 increments of Table D-5 (+0.2, +0.3, +0.4, +0.6, +0.9, +1.3,
  +1.5, +1.8, +2.2 and +2.8 dB) gives 109.9, 106.0, 103.2, 100.1, 94.9, 89.3,
  85.2, 80.8, 76.1 and 71.5 dB, and the unrounded increments give the same ten
  values. Eight of the ten printed cells differ from these, by up to 0.8 dB at
  25000 ft; the two that agree, at 400 ft and 630 ft, are the two where the
  increments of the two routes round to the same sum. The row has been copied
  from Table D-6b rather than computed.
- **Evidence:** recomputation from Tables D-6a and D-5 of the same example.
  Verified on PDF page 133 (printed p. D-9) of ECAC.CEAC Doc 29, 5th ed.,
  Volume 2: Technical guide, which carries Tables D-6a, D-6b and D-6c on the
  one page, and on PDF page 132 (printed p. D-8) of the same document for the
  increments of Table D-5.
- **Library behaviour:** `revise_npd_curves` adds the increment to Table D-6a
  and gives the recomputed row.
  `test_revised_npd_data_is_table_d6c_but_its_misprinted_row` pins it, and the
  conformance row *ECAC Doc 29 Appendix D Table D-6c* holds the other 60 cells
  of the table.
- **Status:** unreported.

## ECAC Doc 29, 5th ed., Volume 2, Appendix D, text under Table D-2 (Tables D-3b and D-3c paired with the wrong methods)

- **Location:** Appendix D, the paragraph under Table D-2 that introduces the
  three attenuation tables of the worked example.
- **The print:** "together with the absorption coefficients in Table D-1 for
  the AIR-1845 atmosphere and using attenuation values calculated using
  SAE-ARP-5534 and SAE-ARP-866A for the specified atmosphere [...]. All three
  sets of attenuation values are listed in Tables D-3a, D-3b and D-3c
  respectively."
- **The problem:** "respectively" gives SAE-ARP-5534 to Table D-3b and
  SAE-ARP-866A to Table D-3c, and the tables are titled the other way round:
  Table D-3b "calculated using SAE-ARP-866A", Table D-3c "calculated using
  SAE-ARP-5534". The values follow the titles. SAE ARP 5534 reproduces all 240
  cells of Table D-3c to the printed digit, and SAE ARP 866A 208 of the 240 of
  Table D-3b, the other 32 (the longest high-frequency paths) within half a
  unit of the printed digit plus 7 parts per million, while the pairing the
  sentence states is off by as much as 177 dB, at 10 kHz and 25000 ft
  (921.851 dB against 744.810 dB). The text after the tables, which gives
  Table D-4 to SAE-ARP-5534 and Table D-5 to SAE-ARP-866A, follows the titles
  too.
- **Evidence:** comparison of the sentence with the two table titles, and
  recomputation of both tables by both methods. Verified on PDF page 128
  (printed p. D-4) of ECAC.CEAC Doc 29, 5th ed., Volume 2: Technical guide for
  the sentence, and on PDF pages 130 and 131 (printed pp. D-6 and D-7) of the
  same document for the titles and values of Tables D-3b and D-3c.
- **Library behaviour:** none needed; the library pairs each table with the
  method its title names, which is the pairing its values confirm. The
  conformance rows *ECAC Doc 29 Appendix D Table D-3b* and *Table D-3c* hold
  the two tables.
- **Status:** unreported.
