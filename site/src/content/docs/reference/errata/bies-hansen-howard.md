---
title: "Errata in Bies, Hansen & Howard (2017)"
description: "Errata in Bies, Hansen & Howard (2017): 4 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 4 entries of the [errata registry](/phonometry/reference/errata/) on Bies, Hansen & Howard (2017), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Bies, Hansen & Howard, Engineering Noise Control 5e (2017), Eq. (8.141)

- **Location:** Section 8.9.1, Eq. (8.141) (printed p. 461), the transmission
  loss of a muffler from the elements of its total four-pole matrix.
- **The print:**
  $$
  TL = 10 \lg\left[ \left(\frac{1+M_n}{1+M_1}\right)^2 \cdot \tfrac{1}{4} \cdot
  \left| \frac{Z_{A1}}{Z_{An}} T_{11} + \frac{T_{12}}{Z_{An}}
  + Z_{A1} T_{21} + \frac{Z_{An}}{Z_{A1}} T_{22} \right|^2 \right],
  $$
  i.e. with the impedance ratio $Z_{A1}/Z_{An}$ weighting $T_{11}$ and its
  inverse weighting $T_{22}$.
- **The problem:** the source the equation itself cites (Munjal, *Acoustics of
  Ducts and Mufflers* 2e, Eq. (3.27), p. 105) carries the overall prefactor
  $Z_{An}/Z_{A1}$ (equivalently $\sqrt{S_1/S_n}$ inside a $20\log_{10}$ form)
  with $T_{11}$ unweighted and $Z_{A1}/Z_{An}$ on $T_{22}$. As printed, Eq.
  (8.141) fails the sudden-expansion limit: a zero-length element ($T = I$)
  between $S_1 = 0.01\ \text{m}^2$ and $S_n = 0.02\ \text{m}^2$ is a sudden
  area expansion with the classic
  $TL = 10\log_{10}[(1+m)^2/(4m)] = 0.512\ \text{dB}$ ($m = S_n/S_1 = 2$), but
  the printed equation gives
  $\tfrac{1}{4} \cdot (Z_{A1}/Z_{An} + Z_{An}/Z_{A1})^2 = 1.938\ \text{dB}$.
  Reading the ratios as an overall $Z_{A1}/Z_{An}$ prefactor instead is also
  wrong: it gives 6.532 dB on the same oracle and violates reciprocity
  ($11.34$ vs -0.70 dB for an expansion chamber between unequal pipes; a
  negative TL for a passive element). The misprint is invisible whenever the
  inlet and outlet areas are equal, where every variant reduces to Eq.
  (8.148).
- **Evidence:** numeric evaluation of the zero-length identity element and of
  an unequal-port expansion chamber under the printed form, the inverted
  prefactor and Munjal Eq. (3.27); only Munjal's form reproduces the
  sudden-expansion classic (0.512 dB, both directions) and is reciprocal.
- **Library behaviour:** `transmission_loss` in
  [`silencers.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencers.py) implements
  Munjal Eq. (3.27), with the sudden-expansion limit and TL reciprocity pinned
  by regression tests
  ([`tests/noise_control/test_silencers.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_silencers.py))
  and a defensive note at the formula.
- **Status:** unreported (textbook rather than a standard).

## Bies 5e (2017), Table C.1 (three speeds that do not follow from the two columns they are said to be calculated from)

- **Location:** Table C.1, "Properties of materials", the rows "Brick" and
  "Cork" on printed page 719 (PDF page 748) and "Plywood (fir)" on printed page
  720 (PDF page 749), against the text on printed page 717 (PDF page 746).
  Non-normative source: a textbook.
- **The print:** printed page 717 says "The speed of sound values in column 4
  of Table C.1 were calculated from the values in columns 2 and 3", which are
  the Young's modulus in $10^9$ N/m2 and the density in kg/m3. The three rows
  give, in that order, $E$ = 24 and $\rho$ = 2000 with a speed of 3650 m/s;
  $E$ = 0,1 and $\rho$ = 250 with 500 m/s; and $E$ = 8,3 and $\rho$ = 600 with
  4540 m/s.
- **The problem:** $\sqrt{E/\rho}$ on those cells gives 3464, 632 and 3719 m/s.
  The printed speeds are 5,4 per cent above, 20,9 per cent below and 22,1 per
  cent above what the two columns beside them give.
- **Evidence:** the same expression reproduces the rest of the table. Of the
  eighty-seven rows that print both the modulus and the density as single
  values, seventy-nine agree within 1 per cent and eighty-four within 3, with a
  median offset of 0,03 per cent, across speeds from 190 to 27000 m/s. Only
  these three fall outside, which is the signature of a misprinted cell rather
  than of a looser method than the page describes. Which cell is misprinted
  cannot be told from the page: 4540 m/s would follow from a modulus of 12,4
  rather than 8,3, and 500 m/s from a density of 400 rather than 250. Verified
  against the page as printed on PDF pages 748 and 749 (printed pp. 719 and
  720) of Bies, Hansen and Howard (2017), *Engineering Noise Control*, fifth
  edition.
- **Consequence for the book's own tables:** three cells. Nothing else in the
  document computes with them.
- **Library behaviour:** the catalogue holds the three columns as printed and
  derives nothing over them, and each of the three rows carries the
  disagreement in its note. The test
  `test_three_rows_do_not_follow_from_their_own_two_columns` in
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) pins
  the three, and `test_the_rest_of_the_table_reproduces_to_three_per_cent`
  pins the eighty-four that do follow, which is what makes the three a defect.
- **Status:** not reported.

## Bies 5e (2017), Table C.2 (four molar masses that do not belong to the gas in the row)

- **Location:** Table C.2, "Molecular weights and ratios of specific heats for
  some commonly used gases", the rows "Ammonia", "Fluorine", "Freon 22" and
  "Nitric oxide" on printed page 722 (PDF page 751). Non-normative source: a
  textbook.
- **The print:** the four rows give, in the column headed "Molecular weight,
  $M$ kg/mole", 0.01730, 0.01900, 0.08047 and 0.06301.
- **The problem:** the molar mass of a gas follows from the molecule the row
  names, and none of these four does. Ammonia is NH$_3$ at 17.031 g/mol, not
  17.30. Fluorine gas is F$_2$ at 37.996 g/mol, and 19.00 is the atomic mass of
  one fluorine atom. Freon 22 is CHClF$_2$ at 86.465 g/mol, not 80.47. Nitric
  oxide is NO at 30.006 g/mol, and 63.01 is the molar mass of nitric *acid*,
  HNO$_3$.
- **Evidence:** the rest of the table settles that these are misprints rather
  than a looser convention. Thirty-five of the thirty-seven rows name a
  molecule whose formula mass can be computed; the two that do not are the
  mixtures, air and natural gas. Of those thirty-five, thirty-one reproduce
  their formula mass to better than 0.05 per cent, and the two that are further
  out are further out only because the page rounds: helium at 4.00 against
  4.0026 is 0.07 per cent low and hydrogen at 2.02 against 2.016 is 0.20 per
  cent high, both of them the last printed digit. So the table's own precision
  is two parts in a thousand, against which the four exceptions are 1.6, 6.9,
  50.0 and 110.0 per cent out. Two of them land exactly on a different
  species, which is what a copying slip looks like: 19.00 is atomic fluorine to
  0.01 per cent and 63.01 is HNO$_3$ to 0.003 per cent, the same accuracy the
  correct rows have. The ratio of specific heats printed beside each of the
  four points the same way: 1.36 for fluorine and 1.40 for nitric oxide are
  diatomic values, so the rows mean F$_2$ and NO whatever their mass column
  says. An independent table of the same genre agrees on both counts: the
  Masoneilan *Control Valve Sizing Handbook* (Baker Hughes, BHMN-19540C, 2022),
  which tabulates the same two quantities for the same purpose, prints
  "Fluorine, F$_2$" with a ratio of specific heats of 1.36 on its page 19 and
  "Ammonia, NH$_3$" with a molecular weight of 17.0 on its page 20. Verified
  against the page as printed on PDF page 751 (printed p. 722) of Bies, Hansen
  and Howard (2017), *Engineering Noise Control*, fifth edition, and on pages
  19 and 20 of the Masoneilan handbook.
- **Consequence for the book's own tables:** four cells. Nothing else in the
  document computes with them; the table is offered for the control valve noise
  of Section 10.8, where the gas is chosen by the reader. A reader who did take
  one of the four would get a speed of sound 0.8 per cent low for ammonia, 3.7
  per cent high for Freon 22, 41.4 per cent high for fluorine and 31.0 per cent
  low for nitric oxide, since $c = \sqrt{\gamma R T / M}$.
- **Library behaviour:** the catalogue holds the row and its ratio of specific
  heats, and refuses the molar mass rather than serving it: reading it raises,
  naming the cell, quoting what the page prints and pointing here. The tests
  `test_a_cell_the_errata_names_is_not_served_as_a_value` and
  `test_the_refusal_quotes_the_printed_number_and_points_at_the_registry` in
  [`tests/fluids/test_gas_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas_catalogue.py)
  pin both halves, and `test_no_other_cell_of_either_table_is_called_wrong`
  keeps the claim from spreading to a fifth row.
- **Status:** not reported.

## Bies 5e (2017), Table C.2 (two ratios of specific heats that no gas can have)

- **Location:** Table C.2, "Molecular weights and ratios of specific heats for
  some commonly used gases", the rows "Hydrogen fluoride" and "Octane" on
  printed page 722 (PDF page 751). Non-normative source: a textbook.
- **The print:** the column headed "Ratio of specific heats, $\gamma$" gives
  0.97 for hydrogen fluoride and 1.66 for octane.
- **The problem:** the column is the ratio of specific heats, which its own
  heading names as such and which the table exists to feed into the control
  valve procedure the appendix points at, "particularly useful for calculating
  control valve noise (see Section 10.8)". For any substance in a stable single
  phase $c_p \geq c_v$, so $\gamma \geq 1$ and a printed 0.97 is outside what
  the quantity can be. That is a statement about $c_p/c_v$ and not about every
  exponent an engineer might write as $k$: the real-gas isentropic exponent of
  a strongly associating vapour, which is what hydrogen fluoride is, can fall
  below 1, but it is a different quantity from the one this column names and
  not the one the procedure downstream wants. The octane cell is outside the
  column in the other direction: for an ideal gas $\gamma = 1 + 2/f$ where $f$
  counts the active degrees of freedom, and $f \geq 3$ always, so
  $\gamma \leq 5/3 \approx 1.667$ with equality only for a monatomic one.
  Octane is C$_8$H$_{18}$, twenty-six atoms, with three rotational degrees of
  freedom on top of the three translational ones before any vibration is
  counted, which caps it at $\gamma \leq 4/3$ and puts it near 1.05 in
  practice. That bound is an ideal-gas one, and a real fluid does pass 5/3 near
  its critical point; what rules out reading the cell that way is that this is
  an ideal-gas column, printed against ideal molar masses, giving one value per
  gas rather than one per state.
- **Evidence:** the column is otherwise a clean function of molecular
  complexity, which is what makes the two exceptions visible. The three
  monatomic gases print 1.64 to 1.67, the diatomic ones 1.31 to 1.41, and the
  polyatomic ones fall away with size down to 1.05. Octane's two nearest
  neighbours in that progression are in the same table and one carbon apart:
  n-heptane prints 1.05 and pentane 1.06, so the table itself says what an
  alkane of this size does. Hydrogen fluoride's neighbours are the other
  diatomic rows, and hydrogen chloride, the next halide down, prints 1.41.
  Outside the book, the Masoneilan *Control Valve Sizing Handbook* (Baker
  Hughes, BHMN-19540C, 2022) prints 1.05 for octane in the same $c_p/c_v$
  column on its page 19, between 1.66 for helium and 1.07 for pentane, so the
  progression is not a habit of one author. Verified against the page as
  printed on PDF page 751 (printed p. 722) of
  Bies, Hansen and Howard (2017), *Engineering Noise Control*, fifth edition,
  with both cells re-read at six times magnification: 0.97 and 1.66 are what
  the page prints, with no digit in doubt.
- **Consequence for the book's own tables:** two cells. A reader taking the
  octane row would get a speed of sound 26.0 per cent high; the hydrogen
  fluoride row cannot be used at all, because a speed of sound computed from a
  $\gamma$ below 1 is not the speed of anything.
- **Library behaviour:** the catalogue holds the row and its molar mass, and
  refuses the ratio rather than serving it, the same way and with the same
  message as the four molar masses above. The independent guard is
  [`phonometry.fluids.ideal_gas`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/gas.py), which
  refuses a ratio at or below 1 whoever passes it, and
  `test_a_ratio_of_specific_heats_at_or_below_one_is_refused` in
  [`tests/fluids/test_gas.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas.py) pins that.
- **Status:** not reported.
