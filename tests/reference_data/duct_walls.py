#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ASHRAE Chapter 49 Tables 29 to 34 and 40, read a second time from the page.

The catalogues in :mod:`phonometry.noise_control.duct_walls` and
:mod:`phonometry.building.catalogue` and this module were transcribed from the
rendered pages by two readers who never saw each other's work, and compared
cell by cell before either was kept: no difference on any data cell.  This is
the second reading, kept as the oracle the tests check against.

Every cell is **as the page prints it**, as the glyphs that are in it and not
as a number: ``"21"`` where a value is printed, ``">45"`` where the page writes
a lower bound, ``"(53)"`` where it flags a measurement as less certain than
usual, and the em-dash where it prints one and explains it nowhere.  Keeping
the printed marks here rather than the values is what lets the tests check how
each mark was read as well as which digits were.

One reading feeds two catalogues.  Tables 29 to 34 are the walls of a duct,
measured in two directions and indexed by cross section, length and sheet
gauge, and they are published from ``noise_control``.  Table 40 is a machine
room wall, floor or ceiling, which is an ordinary partition and the same
quantity Bies Table 7.6 prints, so its nine rows are published from
``building`` beside it.  The reading is one because the chapter is one.
"""

from __future__ import annotations

#: The octave bands each table prints a column for, in hertz.  Tables 29 and
#: 33 run to 8 kHz and the other four stop at 4 kHz, which is why a row's
#: values are read against its own table's bands and not against one list.
ASHRAE_49_BANDS_HZ: dict[str, tuple[int, ...]] = {
    "Table 29": (63, 125, 250, 500, 1000, 2000, 4000, 8000),
    "Table 30": (63, 125, 250, 500, 1000, 2000, 4000),
    "Table 31": (63, 125, 250, 500, 1000, 2000, 4000),
    "Table 32": (63, 125, 250, 500, 1000, 2000, 4000),
    "Table 33": (63, 125, 250, 500, 1000, 2000, 4000, 8000),
    "Table 34": (63, 125, 250, 500, 1000, 2000, 4000),
}

#: One entry per printed row of Tables 29 to 34, in printed order: the table,
#: the group heading it sits under, the row label as printed, the gauge as
#: printed, the length as printed, and one string per octave band of
#: :data:`ASHRAE_49_BANDS_HZ`.  A label or a length that is the empty string is
#: a cell the page leaves blank.
ASHRAE_49_DUCT_WALLS: tuple[tuple[str, str, str, str, str, tuple[str, ...]], ...] = (
    (
        "Table 29",
        "",
        "305 × 305",
        "24",
        "",
        ("21", "24", "27", "30", "33", "36", "41", "45"),
    ),
    (
        "Table 29",
        "",
        "305 × 610",
        "24",
        "",
        ("19", "22", "25", "28", "31", "35", "41", "45"),
    ),
    (
        "Table 29",
        "",
        "305 × 1220",
        "22",
        "",
        ("19", "22", "25", "28", "31", "37", "43", "45"),
    ),
    (
        "Table 29",
        "",
        "610 × 610",
        "22",
        "",
        ("20", "23", "26", "29", "32", "37", "43", "45"),
    ),
    (
        "Table 29",
        "",
        "610 × 1220",
        "20",
        "",
        ("20", "23", "26", "29", "31", "39", "45", "45"),
    ),
    (
        "Table 29",
        "",
        "1220 × 1220",
        "18",
        "",
        ("21", "24", "27", "30", "35", "41", "45", "45"),
    ),
    (
        "Table 29",
        "",
        "1220 × 2440",
        "18",
        "",
        ("19", "22", "25", "29", "35", "41", "45", "45"),
    ),
    (
        "Table 30",
        "Long Seam Ducts",
        "200",
        "26",
        "4.6",
        (">45", "(53)", "55", "52", "44", "35", "34"),
    ),
    (
        "Table 30",
        "Long Seam Ducts",
        "350",
        "24",
        "4.6",
        (">50", "60", "54", "36", "34", "31", "25"),
    ),
    (
        "Table 30",
        "Long Seam Ducts",
        "560",
        "22",
        "4.6",
        (">47", "53", "37", "33", "33", "27", "25"),
    ),
    (
        "Table 30",
        "Long Seam Ducts",
        "810",
        "22",
        "4.6",
        ("(51)", "46", "26", "26", "24", "22", "38"),
    ),
    (
        "Table 30",
        "Spiral Wound Ducts",
        "300",
        "26*",
        "3.6",
        ("52", "51", "53", "51", "50", "46", "36"),
    ),
    (
        "Table 30",
        "Spiral Wound Ducts",
        "610",
        "24",
        "7.3",
        ("51", "53", "51", "44", "36", "26", "29"),
    ),
    (
        "Table 30",
        "Spiral Wound Ducts",
        "",
        "24*",
        "7.3",
        ("51", "51", "54", "44", "39", "33", "47"),
    ),
    (
        "Table 30",
        "Spiral Wound Ducts",
        "",
        "16",
        "3",
        (">48", "53", "36", "32", "32", "28", "41"),
    ),
    (
        "Table 30",
        "Spiral Wound Ducts",
        "915",
        "20",
        "7.3",
        ("51", "51", "52", "46", "36", "32", "55"),
    ),
    ("Table 31", "", "305 × 152", "24", "", ("31", "34", "37", "40", "43", "—", "—")),
    ("Table 31", "", "610 × 152", "24", "", ("24", "27", "30", "33", "36", "—", "—")),
    ("Table 31", "", "610 × 305", "24", "", ("28", "31", "34", "37", "—", "—", "—")),
    ("Table 31", "", "1220 × 305", "22", "", ("23", "26", "29", "32", "—", "—", "—")),
    ("Table 31", "", "1220 × 610", "22", "", ("27", "30", "33", "—", "—", "—", "—")),
    ("Table 31", "", "2440 × 610", "20", "", ("22", "25", "28", "—", "—", "—", "—")),
    ("Table 31", "", "2440 × 1220", "18", "", ("28", "31", "—", "—", "—", "—", "—")),
    (
        "Table 32",
        "Long Seam Ducts",
        "203",
        "26",
        "4.57",
        (">17", "(31)", "39", "42", "41", "32", "31"),
    ),
    (
        "Table 32",
        "Long Seam Ducts",
        "356",
        "24",
        "4.57",
        (">27", "43", "43", "31", "31", "28", "22"),
    ),
    (
        "Table 32",
        "Long Seam Ducts",
        "559",
        "22",
        "4.57",
        (">28", "40", "30", "30", "30", "24", "22"),
    ),
    (
        "Table 32",
        "Long Seam Ducts",
        "813",
        "22",
        "4.57",
        ("(35)", "36", "23", "23", "21", "19", "35"),
    ),
    (
        "Table 32",
        "Spiral Wound Ducts",
        "203",
        "26",
        "3.05",
        (">20", ">42", ">59", ">62", "53", "43", "26"),
    ),
    (
        "Table 32",
        "Spiral Wound Ducts",
        "356",
        "26",
        "3.05",
        (">20", ">36", "44", "28", "31", "32", "22"),
    ),
    (
        "Table 32",
        "Spiral Wound Ducts",
        "660",
        "24",
        "3.05",
        (">27", "38", "20", "23", "22", "19", "33"),
    ),
    (
        "Table 32",
        "Spiral Wound Ducts",
        "660",
        "16",
        "3.05",
        (">30", ">41", "30", "29", "29", "25", "38"),
    ),
    (
        "Table 32",
        "Spiral Wound Ducts",
        "813",
        "22",
        "3.05",
        (">27", "32", "25", "22", "23", "21", "37"),
    ),
    (
        "Table 33",
        "",
        "305 × 305",
        "24",
        "",
        ("16", "16", "16", "25", "30", "33", "38", "42"),
    ),
    (
        "Table 33",
        "",
        "305 × 610",
        "24",
        "",
        ("15", "15", "17", "25", "28", "32", "38", "42"),
    ),
    (
        "Table 33",
        "",
        "305 × 1220",
        "22",
        "",
        ("14", "14", "22", "25", "28", "34", "40", "42"),
    ),
    (
        "Table 33",
        "",
        "610 × 610",
        "22",
        "",
        ("13", "13", "21", "26", "29", "34", "40", "42"),
    ),
    (
        "Table 33",
        "",
        "610 × 1220",
        "20",
        "",
        ("12", "15", "23", "26", "28", "36", "42", "42"),
    ),
    (
        "Table 33",
        "",
        "1220 × 1220",
        "18",
        "",
        ("10", "19", "24", "27", "32", "38", "42", "42"),
    ),
    (
        "Table 33",
        "",
        "1220 × 2440",
        "18",
        "",
        ("11", "19", "22", "26", "32", "38", "42", "42"),
    ),
    ("Table 34", "", "305 × 152", "24", "", ("18", "18", "22", "31", "40", "—", "—")),
    ("Table 34", "", "610 × 152", "24", "", ("17", "17", "18", "30", "33", "—", "—")),
    ("Table 34", "", "610 × 305", "24", "", ("15", "16", "25", "34", "—", "—", "—")),
    ("Table 34", "", "1220 × 305", "22", "", ("14", "14", "26", "29", "—", "—", "—")),
    ("Table 34", "", "1220 × 610", "22", "", ("12", "21", "30", "—", "—", "—", "—")),
    ("Table 34", "", "2440 × 610", "20", "", ("11", "22", "25", "—", "—", "—", "—")),
    ("Table 34", "", "2440 × 1220", "18", "", ("19", "28", "—", "—", "—", "—", "—")),
)

#: What each table's own printed title calls the duct, and which of the two
#: quantities that title says the table prints.  The chapter writes "Round"
#: over Table 30 and "Circular" over Table 32 for the same geometry, and each
#: row keeps the word its own page prints.
ASHRAE_49_TABLE_TITLES: dict[str, tuple[str, str]] = {
    "Table 29": ("rectangular", "breakout"),
    "Table 30": ("round", "breakout"),
    "Table 31": ("flat oval", "breakout"),
    "Table 32": ("circular", "break-in"),
    "Table 33": ("rectangular", "break-in"),
    "Table 34": ("flat oval", "break-in"),
}

#: The one sentence of running text that credits each set of three tables, as
#: the page prints it, with the PDF page and the printed folio it is on.  None
#: of the six tables carries a source line of its own, so this sentence is the
#: whole of the credit and every row of its three tables has to carry it.  The
#: break-in sentence names its first two tables the wrong way round against
#: their own printed titles; it is quoted as printed and the defect is
#: registered in ``docs/ERRATA.md``.
ASHRAE_49_CREDITS: dict[str, tuple[int, str, str]] = {
    "breakout": (
        913,
        "49.29",
        "Values of TLout for rectangular ducts are given in Table 29, for "
        "round ducts in Table 30, and for flat oval ducts in Table 31 "
        "(Cummings 1983, 1985; Lilly 1987).",
    ),
    "break-in": (
        915,
        "49.31",
        "Values for TLin for rectangular ducts are given in Table 32, for "
        "round ducts in Table 33, and for flat oval ducts in Table 34 "
        "(Cummings 1983, 1985).",
    ),
}

#: The rows of Table 30 whose diameter cell the page leaves blank, by their
#: index in :data:`ASHRAE_49_DUCT_WALLS`, and the diameter each inherits.  One
#: printed 610 covers three consecutive rows of the spiral wound block.
ASHRAE_49_INHERITED_DIAMETERS: dict[int, str] = {13: "610", 14: "610"}

#: The octave bands Table 40 prints, in hertz.  It stops at 4 kHz.
ASHRAE_49_TABLE_40_BANDS_HZ: tuple[int, ...] = (63, 125, 250, 500, 1000, 2000, 4000)

#: One entry per printed row of Table 40, in printed order: the construction as
#: printed, its Sound Transmission Class as printed, and one string per octave
#: band of :data:`ASHRAE_49_TABLE_40_BANDS_HZ`.
ASHRAE_49_TABLE_40: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("200 mm CMU*", "50", ("35", "35", "41", "44", "50", "57", "64")),
    (
        "200 mm CMU with 16 mm GWB* on furring strips",
        "53",
        ("33", "32", "44", "50", "56", "59", "65"),
    ),
    (
        "16 mm GWB on both sides of 92 mm metal studs",
        "38",
        ("18", "16", "33", "47", "55", "43", "47"),
    ),
    (
        "16 mm GWB on both sides of 92 mm metal studs with fiberglass insulation in cavity",
        "49",
        ("16", "23", "44", "58", "64", "52", "53"),
    ),
    (
        "2 layers of 16 mm GWB on both sides of 92 mm metal studs with fiberglass insulation in cavity",
        "56",
        ("19", "32", "50", "62", "67", "58", "63"),
    ),
    (
        "Double row of 92 mm metal studs, 25 mm apart, each with 2 layers of 16 mm GWB and fiberglass insulation in cavity",
        "64",
        ("23", "40", "54", "62", "71", "69", "74"),
    ),
    (
        "150 mm solid concrete floor/ceiling",
        "53",
        ("40", "40", "40", "49", "58", "67", "76"),
    ),
    (
        "150 mm solid concrete floor with 100 mm isolated concrete slab and fiberglass insulation in cavity",
        "72",
        ("44", "52", "58", "73", "87", "97", "100"),
    ),
    (
        "150 mm solid concrete floor with two layers of 16 mm GWB hung on spring isolators with fiberglass insulation in cavity",
        "84",
        ("53", "63", "70", "84", "93", "104", "105"),
    ),
)
