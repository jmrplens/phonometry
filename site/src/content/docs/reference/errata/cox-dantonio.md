---
title: "Errata in Cox & D'Antonio (2017)"
description: "Errata in Cox & D'Antonio (2017): 3 defects in the printed text, with the evidence and what phonometry does about each."
searchTitle: "Errata"
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

These are the 3 entries of the [errata registry](/phonometry/reference/errata/) on Cox & D'Antonio (2017), in the order the registry lists them. The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Appendix D (two rows the table cannot tell apart)

- **Location:** Appendix D, "Random incidence scattering coefficient table",
  the group "Pyramids [6]", on printed pages 499 and 500 (PDF pages 556 and
  557). Non-normative source: a textbook.
- **The print:** the group holds four rows. Printed page 499 carries
  "$h = 30.5$ cm, $L = b = 2h$" and then the same description again with the
  continuation line "One in four pyramid corners raised from baseplate" under
  it. Printed page 500 carries "$h = 30.5$ cm, $L = b = h$" and then, once
  more, "$h = 30.5$ cm, $L = b = 2h$" with the same continuation line under
  it.
- **The problem:** the second and the fourth rows are printed with the same
  description, the same continuation line and different numbers: 0.38 against
  0.44 at 1 kHz, 0.74 against 0.76 at 2 kHz, and 1.00 against an en dash at
  5 kHz. Nothing printed beside either row distinguishes it from the other, so
  a reader who looks up "the 30.5 cm pyramids with one corner in four raised"
  finds two answers and no way to choose. A table of measured values has to
  identify its rows; this one does not.
- **Evidence:** both pages read at six times magnification. The labels are
  character for character the same, the continuation lines are the same, and
  the values differ in thirteen of the eighteen bands, agreeing only at 100,
  125, 160, 200 and 4000 Hz. The block's own
  structure is what makes the reading plain: the table pairs a plain surface
  with a modified one, and printed page 499 pairs $L = b = 2h$ with its
  modified version. Printed page 500 opens with $L = b = h$, so its second row
  is where the modified $L = b = h$ belongs, which would make the printed "2h"
  the defect. That is a reading of the pattern rather than something the page
  states, and the source the group is credited to, Sharma and Bradley,
  *J. Acoust. Soc. Am.* 134(5), 4095 (2013), is a one-page meeting abstract
  that this library has not read, so the errata records what the page does and
  not what it should have said. Verified on PDF page 556 (printed p. 499) and
  PDF page 557 (printed p. 500) of Cox and D'Antonio (2017), Acoustic Absorbers
  and Diffusers, third edition.
- **Library behaviour:** both rows are kept, with the description and the
  continuation line as printed. Their keys carry the printed folio, which is
  the only thing that separates them, and
  `test_two_pyramid_rows_are_told_apart_only_by_the_page_they_sit_on` in
  [`tests/materials/diffusers/test_scattering_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_scattering_catalogue.py)
  pins that they stay two rows with two spectra.
- **Status:** not reported.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Appendix B (a width in centimetres that its own geometry makes metres)

- **Location:** Appendix B, "Normalized diffusion coefficient table", section 1,
  the first surface of the width series, on printed page 482 (PDF page 539).
  Non-normative source: a textbook.
- **The print:** the section is headed "Effect of changing diffuser periodicity
  and width. Semicylinder(s) non-absorbing surfaces, radius 0.3 m (1 cm flat
  section between each period)", and its five surfaces are listed as "1 period,
  0.61 cm wide", "2 periods, 1.22 m wide", "4 cylinders, 2.44 m wide",
  "6 periods, 3.66 m wide" and "12 periods, 7.32 m wide".
- **The problem:** the first width is in centimetres and the other four are in
  metres, and the series doubles: 0.61, 1.22, 2.44, and then 3.66 and 7.32,
  which are six and twelve of the first. One period of the surface the heading
  describes is a semicylinder of radius $0.3$ m plus the $1$ cm flat section,
  so $2 \times 0.3 + 0.01 = 0.61$ m. A width of 0.61 cm is six millimetres, a
  hundredth of what the heading's own geometry gives and a hundredth of what
  the rest of the series requires.
- **Evidence:** the same surface is listed in Table C.3 of the next appendix,
  under a heading with the same geometry, and there it reads "1 period, 0.61 m
  wide". The book therefore prints both spellings of one surface twelve pages
  apart, and the metric one is the one its arithmetic supports. Verified on PDF
  page 539 (printed p. 482) and PDF page 549 (printed p. 492) of Cox and
  D'Antonio (2017), *Acoustic Absorbers and Diffusers*, third edition, with the
  unit re-read at six times magnification on both pages: the appendix really
  prints "cm" and Table C.3 really prints "m".
- **Consequence for the book's own tables:** the description of one surface,
  and of the three rows that carry it. The numbers beside it are unaffected,
  which is what makes the defect easy to miss and worth recording: a reader
  comparing a measured semicylinder against this row would be comparing against
  a 0.61 m device whatever the label says.
- **Library behaviour:** the row keeps the width as printed, because a
  catalogue that silently corrected it would be claiming a reading the page
  does not make. The three rows of the surface are keyed on it and
  `test_every_section_heading_is_kept_whole` in
  [`tests/materials/diffusers/test_diffusion_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_diffusion_catalogue.py)
  pins that the heading with the geometry travels with them, which is what
  lets a reader see the contradiction.
- **Status:** not reported.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Table 6.7 (six porosities printed in per cent in a column of fractions)

- **Location:** Table 6.7, "Effective flow resistivity values for ground
  surfaces and other parameters", the column "Porosity", on printed pages 200
  and 201 (PDF pages 257 and 258). Non-normative source: a textbook.
- **The print:** the column is headed "Porosity" and states no unit, where
  the column beside it is headed "Water content (%)". Every porosity it prints
  is a fraction between 0.15 and 1 ("0.5–0.9" for snow, "0.24" for the sports
  field, "0.44" for fine sand, "0.34–1" and the like for the fitted grasses),
  except on six rows: "Mineral layer beneath mixed deciduous forest" 36.5,
  "Humus on pine forest floor" 58.1, "Pine forest litter (6–7 cm thick)" 38.9,
  "Grass root layer in loamy sand" 48 ± 4, "Loamy sand" 37.5 and "Bare sandy
  plain" 26.9.
- **The problem:** a porosity is the fraction of a volume that is open, so it
  cannot pass 1, and these six are percentages printed in a column that states
  no unit and holds fractions everywhere else. Read in the column's own unit
  they are porosities of 26.9 to 58.1, which no material has; read as per cent
  they are 0.269 to 0.581, which is what soils like these are. The page leaves
  the reader to work out which, and a program that reads the column as printed
  takes the impossible value.
- **Evidence:** Verified on PDF page 257 (printed p. 200) and PDF page 258
  (printed p. 201) of Cox and D'Antonio (2017), *Acoustic Absorbers and
  Diffusers*, third edition: the heading prints no unit, and the six cells
  print the values quoted, the fourth as "48 ± 4".
- **Library behaviour:** in
  [`PUBLISHED_GROUND_SURFACES`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/ground_surfaces.py)
  the six rows leave `GroundSurface.porosity`, which is a fraction from 0 to 1,
  empty, and hold the cell as `misprinted`: `why_missing("porosity")` and the
  refusal of `printed("porosity")` quote the figure the page prints, the
  ± 4 included, and say why it is not served. The library does not convert it
  to 0.365 and so on, because the page does not print the unit that
  conversion would assume. Every catalogue row checks when it is built that a
  porosity is a fraction.
  `test_the_six_percent_porosities_of_cox_are_held_as_misprinted` and
  `test_why_a_per_cent_porosity_is_missing_quotes_the_page` in
  [`tests/io/test_catalogue_row_contract.py`](https://github.com/jmrplens/phonometry/blob/main/tests/io/test_catalogue_row_contract.py)
  pin the six.
- **Status:** unreported.
