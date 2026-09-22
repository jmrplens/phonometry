#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Vér & Beranek 2e Tables 8.5, 8.6 and 8.7, read a second time from the page.

The catalogue in :mod:`phonometry.materials.absorbers.resistive_sheets` and
this module were transcribed from the rendered pages by two readers who never
saw each other's work, and compared cell by cell before either was kept: two
hundred and six cells, no difference. This is the second reading, kept as the
oracle the tests check against.

Every value is **as the page prints it**, in the page's own units and with its
own trailing zeros, which is what lets the tests check the arithmetic of the
pages as well as the transcription. How much there is to check differs by
table: TABLE 8.5 prints every one of its quantities twice, three of them in SI
and again in US customary units and the fourth, the flow resistance, in N s/m3
and again as a multiple of rho0 c0; TABLE 8.7 prints the thickness and the mass
in the two systems of units and its flow resistance the two ways TABLE 8.5
does; and TABLE 8.6 prints only its surface density twice, and its weave and
its flow resistance once each. Where a quantity is printed in two systems of
units both printings are here, and they agree to the rounding of the coarser
one everywhere except the last row of Table 8.5, where they differ by a factor
of ten, and everywhere in Table 8.6, where they differ by eleven per cent on
every row.

An empty string is a cell the page leaves blank. All eight of them are in the
two flow-resistance columns of Table 8.7, which prints a value once per block
of rows and nothing beneath it; a reading that stopped at the printed cell
would leave eight of the eleven sintered sheets with no flow resistance.
"""

from __future__ import annotations

#: The columns of TABLE 8.5, in printed order: the two mesh counts, the
#: wire diameter twice, the mass per unit area twice and the flow
#: resistance twice.
VER_BERANEK_8_5_COLUMNS: tuple[str, ...] = (
    "Wires/cm",
    "Wires/in.",
    "µm (10−6 m)",
    "mils (10−3 in.)",
    "kg/m2",
    "lb/ft2",
    "N · s/m3",
    "ρ0c0",
)

#: One entry per printed row: the row as the page labels it, then one
#: value per column of :data:`VER_BERANEK_8_5_COLUMNS`. An empty
#: string is a cell the page leaves blank.
VER_BERANEK_8_5: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("12", ("12", "30", "330", "13.0", "1.6", "0.32", "5.7", "0.014")),
    ("20", ("20", "50", "220", "8.7", "1.2", "0.25", "5.9", "0.014")),
    ("40", ("40", "100", "115", "4.5", "0.63", "0.13", "9.0", "0.022")),
    ("47", ("47", "120", "90", "3.6", "0.48", "0.1", "13.5", "0.033")),
    ("80", ("80", "200", "57", "2.25", "0.31", "0.63", "24.6", "0.06")),
)

#: The columns of TABLE 8.6, in printed order: the manufacturer codes, the
#: cloth number, the surface density twice, the weave and the flow
#: resistance.
VER_BERANEK_8_6_COLUMNS: tuple[str, ...] = (
    "Manufacturer",
    "Cloth Number",
    "oz/yd2",
    "g/m2",
    "Construction, Ends × Picks",
    "Flow Resistance, mks rayls (N · s/m3)",
)

#: One entry per printed row: the row as the page labels it, then one
#: value per column of :data:`VER_BERANEK_8_6_COLUMNS`. An empty
#: string is a cell the page leaves blank.
VER_BERANEK_8_6: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("120", ("1, 2, 3", "120", "3.16", "96", "60 × 58", "300")),
    ("126", ("1, 2, 3", "126", "5.37", "164", "34 × 32", "45")),
    ("138", ("1, 2, 3", "138", "6.70", "204", "64 × 60", "2200")),
    ("181", ("1, 2, 3", "181", "8.90", "272", "57 × 54", "380")),
    ("1044", ("3", "1044", "19.2", "585", "14 × 14", "36")),
    ("1544", ("2", "1544", "17.7", "535", "14 × 14", "19")),
    ("3862", ("3", "3862", "12.3", "375", "20 × 38", "350")),
    ("1658", ("1", "1658", "1.87", "57", "24 × 24", "10")),
    ("1562", ("1", "1562", "1.94", "59", "30 × 16", "<5")),
    ("1500", ("1", "1500", "9.60", "293", "16 × 14", "13")),
    ("1582", ("1", "1582", "14.5", "442", "60 × 56", "400")),
    ("1584", ("1", "1584", "24.6", "750", "42 × 36", "200")),
    ("1589", ("1", "1589", "12.0", "366", "13 × 12", "11")),
)

#: The columns of TABLE 8.7, in printed order: the flow resistance twice,
#: the nonlinearity factor, the designation, the thickness twice and the
#: mass per unit area twice.
VER_BERANEK_8_7_COLUMNS: tuple[str, ...] = (
    "ρ0c0",
    "N · s/m3",
    "NLF 500/20",
    "Designation",
    "mm",
    "in.",
    "kg/m2",
    "lb/ft2",
)

#: One entry per printed row: the row as the page labels it, then one
#: value per column of :data:`VER_BERANEK_8_7_COLUMNS`. An empty
#: string is a cell the page leaves blank.
VER_BERANEK_8_7: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("FM 125", ("0.25", "100", "3.6", "FM 125", "1.0", "0.04", "3.9", "0.79")),
    ("FM 127", ("", "", "5.0", "FM 127", "0.76", "0.03", "3.3", "0.67")),
    ("FM 185", ("", "", "2.6", "FM 185", "0.5", "0.02", "2.0", "0.4")),
    (
        "347-10-20-AC3A-A",
        ("", "", "2.0", "347-10-20-AC3A-A", "0.5", "0.02", "1.32", "0.27"),
    ),
    (
        "347-10-30-AC3A-A",
        ("", "", "2.0", "347-10-30-AC3A-A", "0.76", "0.03", "1.1", "0.23"),
    ),
    ("FM 802", ("", "", "2.0", "FM 802", "0.5", "0.02", "1.3", "0.27")),
    ("FM 134", ("0.88", "350", "4.7", "FM 134", "0.89", "0.035", "3.8", "0.77")),
    ("FM 122", ("1.25", "500", "1.8", "FM 122", "0.76", "0.03", "1.4", "0.28")),
    ("FM 126", ("", "", "3.6", "FM 126", "0.66", "0.026", "3.7", "0.76")),
    ("FM 190", ("", "", "3.3", "FM 190", "0.41", "0.016", "2.0", "0.4")),
    (
        "347-50-30-AC3A-A",
        ("", "", "2.0", "347-50-30-AC3A-A", "0.76", "0.03", "1.4", "0.29"),
    ),
)
