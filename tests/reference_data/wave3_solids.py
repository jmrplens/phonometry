#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Six tables of solids and fluids, read a second time from the page.

Norton & Karczub 2e Table 3.1, Table 6.1 and Appendix 4; Vigran (2008) Table
3.1; and Rossing (2014) Table 15.5. Each was transcribed by two readers who
never saw each other's work and compared cell by cell before either was kept:
392 cells, and not one disagreement about a number. The eight disagreements
there were are about typography (a subscript in a heading, an apostrophe, the
spacing inside a formula) plus one footnote mark on a body cell, and each was
settled by looking at the page.

This is the second reading, kept as the oracle the tests check against,
with the one body cell the comparison settled against it put back to what
the page prints: reader B wrote the aerated concrete modulus as ``3.8 2``,
flattening the superscript footnote mark that makes it a static modulus,
and the cropped page shows ``3.8 ²``; and reader B set the symbol of the
scaling factor with a space each side of the solidus, which the comparison
measured on the page and found to be the glyph's own sidebearing. Every
cell is **as the page prints it**: ranges keep their dash, approximations keep
their tilde, a rule is the rule character, powers of ten keep their
superscripts, and a footnote mark stays attached to the cell it marks. Two
cells are misprints the page cannot be read past, and they are here exactly
as printed: they are registered in ``docs/ERRATA.md``.
"""

from __future__ import annotations

#: Norton & Karczub 2e Table 3.1: surface density per millimetre, coincidence
#: height and the plateau frequency ratio B/A, in printed order.
NORTON_KARCZUB_3_1: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Aluminium", ("2.66", "29", "11.0")),
    ("Brick", ("2.10", "37", "4.5")),
    ("Concrete", ("2.28", "38", "4.5")),
    ("Glass", ("2.47", "27", "10.0")),
    ("Lead", ("11.20", "56", "4.0")),
    ("Plaster", ("1.71", "30", "8.0")),
    ("Plywood", ("0.57", "19", "6.5")),
    ("Steel", ("7.60", "40", "11.0")),
)

#: Norton & Karczub 2e Table 6.1: one structural loss factor per printed row.
NORTON_KARCZUB_6_1: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Aluminium", ("1.0 × 10⁻⁴",)),
    ("Brick, concrete", ("1.5 × 10⁻²",)),
    ("Cast iron", ("1.0 × 10⁻³",)),
    ("Copper", ("2.0 × 10⁻³",)),
    ("Glass", ("1.0 × 10⁻³",)),
    ("Plaster", ("5.0 × 10⁻³",)),
    ("Plywood", ("1.5 × 10⁻²",)),
    ("PVC", ("0.3",)),
    ("Sand (dry)", ("0.02–0.2",)),
    ("Steel", ("1–6 × 10⁻⁴",)),
    ("Tin", ("2.0 × 10⁻³",)),
)

#: Norton & Karczub 2e Appendix 4 A: density, Young's modulus, Poisson ratio,
#: bar speed, bulk speed and the critical frequency-thickness product.
NORTON_KARCZUB_APPENDIX_4A: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Aluminium", ("2700", "7.1 × 10¹⁰", "0.33", "5150", "6300", "12.7")),
    ("Brass", ("8500", "10.4 × 10¹⁰", "0.37", "3500", "4700", "18.7")),
    ("Concrete (dense)", ("2600", "∼ 2.5 × 10¹⁰", "–", "–", "3100", "21.1")),
    ("Copper", ("8900", "12.2 × 10¹⁰", "0.35", "3700", "5000", "17.7")),
    ("Cork", ("250", "6.2 × 10¹⁰", "–", "–", "500", "130.7")),
    ("Cast iron", ("7700", "10.5 × 10¹⁰", "0.28", "3700", "4350", "17.7")),
    ("Glass (Pyrex)", ("2300", "6.2 × 10¹⁰", "0.24", "5200", "5600", "12.6")),
    ("Gypsum (plasterboard)", ("650", "–", "–", "–", "6800", "9.61")),
    ("Lead", ("11 300", "1.65 × 10¹⁰", "0.44", "1200", "2050", "54.5")),
    ("Nickel", ("8800", "21 × 10¹⁰", "0.31", "4900", "5850", "13.3")),
    ("Particle board", ("750", "–", "–", "–", "669", "97.7")),
    ("Polyurethane", ("72", "1.9 × 10⁷", "–", "–", "513", "127.4")),
    ("Polystyrene", ("42", "1.1 × 10⁷", "–", "–", "512", "127.6")),
    ("PVC", ("66", "5.5 × 10⁷", "–", "–", "913", "71.6")),
    ("Plywood", ("600", "–", "–", "–", "3080", "21.2")),
    ("Rubber (hard)", ("1100", "2.3 × 10⁹", "0.4", "1450", "2400", "45.1")),
    ("Rubber (soft)", ("950", "5 × 10⁶", "–", "–", "1050", "62.2")),
    ("Silver", ("10 500", "7.8 × 10¹⁰", "0.37", "2700", "3700", "24.2")),
    ("Steel", ("7700", "19.5 × 10¹⁰", "0.28", "5050", "6100", "12.9")),
    ("Tin", ("7300", "4.5 × 10¹⁰", "0.33", "2500", "–", "26.1")),
    ("Wood (hard)", ("650", "1.2 × 10¹⁰", "–", "4300", "–", "15.2")),
)

#: Norton & Karczub 2e Appendix 4 B: density, temperature, ratio of
#: specific heats and speed of sound.
NORTON_KARCZUB_APPENDIX_4B: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Castor oil", ("950", "20", "–", "1540")),
    ("Ethyl alcohol", ("790", "20", "–", "1150")),
    ("Fresh water", ("998", "20", "1.004", "1483")),
    ("Fresh water", ("998", "13", "1.004", "1441")),
    ("Glycerin", ("1260", "20", "–", "1980")),
    ("Mercury", ("13 600", "20", "1.13", "1450")),
    ("Petrol", ("680", "20", "–", "1390")),
    ("Sea water", ("1026", "13", "1.01", "1500")),
    ("Turpentine", ("870", "20", "1.27", "1250")),
)

#: Norton & Karczub 2e Appendix 4 C: the same four columns for gases.
NORTON_KARCZUB_APPENDIX_4C: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Air", ("1.293", "0", "1.402", "332")),
    ("Air", ("1.21", "20", "1.402", "343")),
    ("Carbon dioxide", ("1.84", "20", "1.40", "267")),
    ("Hydrogen", ("0.084", "0", "1.41", "1270")),
    ("Hydrogen", ("0.084", "20", "1.41", "1330")),
    ("Nitrogen", ("1.17", "20", "1.40", "349")),
    ("Oxygen", ("1.43", "0", "1.40", "317")),
    ("Oxygen", ("1.43", "20", "1.40", "326")),
    ("Steam", ("0.6", "100", "1.324", "405")),
)

#: Vigran (2008) Table 3.1: density, dynamic modulus in 10^9 Pa, Poisson
#: ratio and loss factor in units of 10^-3.
VIGRAN_3_1: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Steel", ("7700–7800", "190–210", "0.28–0.31", "~ 0.1")),
    ("Aluminium", ("2700", "66–72", "0.33–034", "~ 0.1")),
    ("Glass", ("2500", "60", "-", "0.6–2.0")),
    ("Concrete", ("2300", "32–40", "0.15–0.2", "4–8")),
    ("Concrete (lightweight aggregate)", ("400–600", "1.0–2.5", "~ 0.2", "10–20")),
    ("Concrete (autoclaved aerated)", ("1300", "3.8 ²", "~ 0.2", "10–20")),
    ("Gypsum plate (plasterboard)", ("800–900", "4.1", "~ 0.3", "10–15")),
    ("Chipboard", ("650–800", "3.8", "~ 0.2", "10–30")),
    ("Fir, spruce", ("400–700", "7–12", "~ 0.4", "8–10")),
)

#: Rossing (2014) Table 15.5 as printed, with the woods as the columns:
#: one entry per printed row, as (symbol, unit, spruce, maple).
ROSSING_15_5: tuple[tuple[str, str, str, str], ...] = (
    ("ρ", "kg/m³", "420", "650"),
    ("D₁", "MPa", "1100", "860"),
    ("D₂", "MPa", "67", "140*"),
    ("D₃", "MPa", "84", "170"),
    ("D₄", "MPa", "230", "230*"),
    ("⁴√(D₁/D₃)", "", "1.9", "1.4"),
)
