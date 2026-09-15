#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for workroom noise prediction (ISO 11690-3:1998).

ISO 11690-3 works two examples of its own, read here in BS EN ISO
11690-3:1999, whose PDF page is its printed folio plus 10. Annex C gives eight
machines their level increase at their own workstations off a diagram; Annex B
works one 20 m by 15 m by 7 m room twice over, printed to a tenth of a decibel,
with workstation labels that contradict its own results, so the positions here
are named by where they stand and never by W1 and W2 (see the errata
registry).

Where neither annex prints an example, three published ones stand in:

* IFA-LSA 01-234 is Laermschutz-Arbeitsblatt IFA-LSA 01-234, "Raumakustik in
  industriellen Arbeitsraeumen", IFA and DGUV, 2. aktualisierte Ausgabe, April
  2020: the step from a measured reverberation time to an absorption area.
* Ver & Beranek 2e is I. L. Ver and L. L. Beranek (eds.), *Noise and Vibration
  Control Engineering*, 2nd edition, Wiley, 2006: the energy addition at a
  workstation with nine machines around it.
* Barron (2003) is R. F. Barron, *Industrial Noise Control and Acoustics*,
  Marcel Dekker, New York, 2003: the direct-plus-reverberant field each
  contribution is read from. Its Example 7-8 is Table 7-5, which
  :mod:`reference_data.enclosure_cabin_insulation` carries whole; its Example
  7-6, a refiner room and the operator's room beside it, is here, and the
  room-to-room chain reads it too. Barron prints his folios only in the text
  layer of the electronic edition, so they are the book's own pagination; the
  PDF page is the folio plus 12.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ISO 11690-3:1998 Annex C: eight machines at their own workstations
# ---------------------------------------------------------------------------

#: Table C.1 on printed folio 19 (PDF page 29) and Table C.2 on printed folio
#: 20 (PDF page 30): for each machine, the sound power level and the emission
#: sound pressure level it declares, the level increase Table C.2 reads off
#: Figure C.1 and the level L'pA it prints, all in decibels. The eighth machine
#: is kept apart below, because its increase runs off the top of the diagram.
ANNEX_C_MACHINES_DB: dict[str, tuple[float, float, float, float]] = {
    "M1": (105.0, 79.0, 9.5, 89.0),
    "M2": (98.0, 81.0, 3.0, 84.0),
    "M3": (107.0, 87.0, 5.0, 92.0),
    "M4": (94.0, 82.0, 1.0, 83.0),
    "M5": (102.0, 84.0, 4.0, 88.0),
    "M6": (96.0, 82.0, 2.0, 84.0),
    "M7": (101.0, 84.0, 3.0, 87.0),
}

#: The eighth machine of the same two tables, in the same order: Table C.2
#: prints an increase of 10 dB, which is the edge of Figure C.1 and not a
#: reading of it (see the errata registry), and a level of 88 dB.
ANNEX_C_M8_DB: tuple[float, float, float, float] = (107.0, 78.0, 10.0, 88.0)

#: C.2.2: the equivalent absorption area of the example room, in square metres.
ANNEX_C_ABSORPTION_M2: float = 195.0

# ---------------------------------------------------------------------------
# ISO 11690-3:1998 Annex B: one workroom, worked twice
# ---------------------------------------------------------------------------

#: Tables B.2 and B.3 on printed folio 16 (PDF page 26): the box-shaped
#: workroom, in metres, and the one mean absorption coefficient every surface
#: of it is given.
ANNEX_B_ROOM_M: tuple[float, float, float] = (20.0, 15.0, 7.0)
ANNEX_B_MEAN_ABSORPTION: float = 0.15

#: Tables B.5 and B.8 on printed folio 18 (PDF page 28): the three workstation
#: positions, in metres, named by where they stand. The position beside M2 is
#: the one Figure B.1 draws as W1 and Table B.5 tabulates as W2.
ANNEX_B_BESIDE_M2: tuple[float, float, float] = (17.0, 4.0, 1.6)
ANNEX_B_FAR_CORNER: tuple[float, float, float] = (3.0, 12.0, 1.6)
ANNEX_B_BESIDE_THE_NEW_MACHINE: tuple[float, float, float] = (3.0, 4.0, 1.6)

#: Tables B.4 and B.7 on printed folios 17 and 18 (PDF pages 27 and 28): each
#: machine's sound power level and emission sound pressure level in decibels,
#: its position in metres, and the workstation it is the machine of, if it has
#: one. The emission level of M1 is printed in brackets, which the footnote of
#: both tables says means it is not used in the calculation; M1 is the machine
#: of no workstation. M3 and M4 are the two machines on offer for case B.
ANNEX_B_MACHINES: dict[
    str,
    tuple[float, float, tuple[float, float, float], tuple[float, float, float] | None],
] = {
    "M1": (95.0, 80.0, (10.0, 3.0, 1.0), None),
    "M2": (90.0, 77.0, (17.0, 3.0, 1.0), ANNEX_B_BESIDE_M2),
    "M3": (100.0, 87.0, (3.0, 3.0, 1.0), ANNEX_B_BESIDE_THE_NEW_MACHINE),
    "M4": (95.0, 82.0, (3.0, 3.0, 1.0), ANNEX_B_BESIDE_THE_NEW_MACHINE),
}

#: Table B.5: what the existing workstation already hears, in decibels.
ANNEX_B_BACKGROUND_DB: float = 50.0

#: Table B.6 on printed folio 18, the "after" column of case A, and the
#: "before" column of Table B.9, in decibels, by position.
ANNEX_B_PRINTED_CASE_A_DB: dict[str, float] = {"beside M2": 82.1, "far corner": 80.3}

#: Table B.9 on printed folio 18, the two "after" columns, in decibels, by
#: position.
ANNEX_B_PRINTED_CASE_B_DB: dict[str, dict[str, float]] = {
    "first choice, M3 at 100 dB": {
        "beside M2": 86.2,
        "far corner": 85.7,
        "beside the new machine": 89.4,
    },
    "second choice, M4 at 95 dB": {
        "beside M2": 83.8,
        "far corner": 82.8,
        "beside the new machine": 85.4,
    },
}

# ---------------------------------------------------------------------------
# IFA-LSA 01-234 (2020), Tab. 4.2: a production hall
# ---------------------------------------------------------------------------

#: Tab. 4.2 on printed folio 14 (PDF page 14): two-measurement means of T20 in
#: a production hall, in seconds, from 500 Hz to 4 kHz by octave.
IFA_LSA_01_234_REVERBERATION_S: tuple[float, ...] = (3.5, 3.8, 3.3, 2.5)

#: The same page prints "V = 30 . 20 . 10 m3 = 6000 m3" and
#: "S = 2 . 20 . 30 m2 + 2 . 10 . 30 m2 + 2 . 10 . 20 m2 = 2200 m2": the length,
#: breadth and height of the hall, in metres.
IFA_LSA_01_234_HALL_M: tuple[float, float, float] = (30.0, 20.0, 10.0)

#: Eq. (4.1) of the same sheet is printed with the 0,163 form of the Sabine
#: constant, which is 24 ln 10 / c at c = 339 m/s, in metres per second.
IFA_LSA_01_234_SPEED_M_S: float = 339.0

#: Tab. 4.2: the absorption area printed for each band, in square metres, and
#: the mean absorption coefficient printed beside it.
IFA_LSA_01_234_PRINTED_AREA_M2: tuple[float, ...] = (279.0, 257.0, 296.0, 391.0)
IFA_LSA_01_234_PRINTED_ABSORPTION: tuple[float, ...] = (0.13, 0.12, 0.13, 0.18)

# ---------------------------------------------------------------------------
# Ver & Beranek 2e (2006), Table 7.4: nine machines around one bench
# ---------------------------------------------------------------------------

#: Table 7.4 on printed folio 200 (PDF page 204): the level each of nine
#: machines contributes at one assembly bench before the ceiling is treated
#: and after, in decibels, and the two totals it prints.
VER_BERANEK_TABLE_7_4_BEFORE_DB: tuple[float, ...] = (
    70.7,
    79.1,
    71.1,
    75.6,
    64.2,
    69.1,
    69.6,
    67.6,
    69.0,
)
VER_BERANEK_TABLE_7_4_AFTER_DB: tuple[float, ...] = (
    65.3,
    74.8,
    67.5,
    73.5,
    60.0,
    65.5,
    65.6,
    63.8,
    63.2,
)
VER_BERANEK_TABLE_7_4_TOTALS_DB: tuple[float, float] = (82.4, 78.7)

#: The text on printed folio 199 (PDF page 203): the benefit of the treatment,
#: printed as the difference of the two totals, in decibels.
VER_BERANEK_TREATMENT_BENEFIT_DB: float = 3.7

# ---------------------------------------------------------------------------
# Barron (2003): the room of Example 7-8 and the rooms of Example 7-6
# ---------------------------------------------------------------------------

#: Eqs. (7-18) and (7-73) carry 10 lg(rho c / 400) as the literal +0,1 dB the
#: book rounds it to, and every worked line adds exactly that, in decibels.
BARRON_IMPEDANCE_TERM_DB: float = 0.1

#: Example 7-6 on printed folio 298 (PDF page 310): a Jordan refiner in a paper
#: mill. The refiner room has a total surface area of 900 m2 and an average
#: absorption coefficient of 0,05; the refiner a sound power level of 105 dB and
#: a directivity factor of 2,0, 4 m from the wall of the operator's room. The
#: operator's room has 100 m2 of surface at 0,35; the wall between the two has
#: a transmission loss of 30 dB and 16 m2 of area; the operator stands 1,5 m
#: from it. Areas in square metres, levels and losses in decibels, distances in
#: metres.
BARRON_EXAMPLE_7_6_SOURCE_SURFACE_M2: float = 900.0
BARRON_EXAMPLE_7_6_SOURCE_ABSORPTION: float = 0.05
BARRON_EXAMPLE_7_6_POWER_LEVEL_DB: float = 105.0
BARRON_EXAMPLE_7_6_DIRECTIVITY: float = 2.0
BARRON_EXAMPLE_7_6_SOURCE_DISTANCE_M: float = 4.0
BARRON_EXAMPLE_7_6_RECEIVING_SURFACE_M2: float = 100.0
BARRON_EXAMPLE_7_6_RECEIVING_ABSORPTION: float = 0.35
BARRON_EXAMPLE_7_6_TRANSMISSION_LOSS_DB: float = 30.0
BARRON_EXAMPLE_7_6_WALL_M2: float = 16.0
BARRON_EXAMPLE_7_6_OPERATOR_DISTANCE_M: float = 1.5

#: What the same page prints on the way: R_1 = 47,37 m2, L_p1 = 94,8 dB,
#: R_2 = 53,85 m2, r* = (S_w/2 pi)^1/2 = 1,596 m, the two terms -16,8 dB and
#: +3,4 dB of the last line, and L_p2 = 61,7 dB, in square metres, decibels and
#: metres.
BARRON_EXAMPLE_7_6_SOURCE_ROOM_CONSTANT_M2: float = 47.37
BARRON_EXAMPLE_7_6_SOURCE_ROOM_LEVEL_DB: float = 94.8
BARRON_EXAMPLE_7_6_RECEIVING_ROOM_CONSTANT_M2: float = 53.85
BARRON_EXAMPLE_7_6_NEAR_WALL_DISTANCE_M: float = 1.596
BARRON_EXAMPLE_7_6_ROOM_TERM_DB: float = -16.8
BARRON_EXAMPLE_7_6_WALL_TERM_DB: float = 3.4
BARRON_EXAMPLE_7_6_OPERATOR_LEVEL_DB: float = 61.7
