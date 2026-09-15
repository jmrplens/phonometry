#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for the spatial sound decay of a workroom (ISO 14257:2001).

The first oracle is Annex C of the standard itself, a measurement in an 83 m by
32 m by 11 m shipyard hall printed all the way through: eleven microphone
positions, the source power, its free-field curve, the room levels, the two
distribution curves and six tables of results. It was read in BS EN ISO
14257:2001, whose PDF page is its printed folio plus 10: Tables C.1 and C.2 on
printed folios 17 and 18, Tables C.3 and C.4 on folio 20, Tables C.5 and C.6
on folio 21, Tables C.7 to C.9 on folio 23 and Tables C.10 to C.12 on folio 24.
The AENOR printing, UNE-EN ISO 14257:2002, carries the same digits.

Annex C is printed in the document that defines the method, so it cannot say
whether the method was read right. Three published sources can:

* Suva 66008.f is W. Lips, "Acoustique des locaux industriels. Informations
  pour projeteurs, architectes et ingenieurs", Suva, 8th revised edition,
  August 2006. It never names ISO 14257: it takes the two descriptors from
  VDI 3760 and EN ISO 11690-1.
* IFA-LSA 01-234 is Laermschutz-Arbeitsblatt IFA-LSA 01-234, "Raumakustik in
  industriellen Arbeitsraeumen", IFA and DGUV, 2. aktualisierte Ausgabe, April
  2020.
* Probst (2006) is W. Probst, "Gestaltung laermarmer Fertigungsstaetten in
  metallverarbeitenden Betrieben", BAuA Schriftenreihe Forschung Fb 1083,
  Dortmund/Berlin/Dresden 2006, whose PDF page numbers equal its folios.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ISO 14257:2001 Annex C
# ---------------------------------------------------------------------------

#: Table C.1: where the eleven microphones stood, in metres.
ANNEX_C_DISTANCES_M: tuple[float, ...] = (
    2.0,
    3.0,
    4.0,
    5.0,
    6.0,
    8.0,
    12.0,
    16.0,
    24.0,
    32.0,
    48.0,
)

#: 6.2 as the example applies it: the boundaries of the three distance ranges,
#: in metres.
ANNEX_C_RANGES_M: dict[str, tuple[float, float]] = {
    "near": (2.0, 5.0),
    "middle": (5.0, 24.0),
    "far": (24.0, 48.0),
}

#: Table C.2: the sound power level of the test source, in decibels, by nominal
#: octave centre in hertz, and the A-weighted total its last column prints.
ANNEX_C_SOURCE_POWER_DB: dict[int, float] = {
    125: 97.6,
    250: 98.6,
    500: 102.2,
    1000: 110.8,
    2000: 111.2,
    4000: 107.4,
}
ANNEX_C_SOURCE_POWER_A_WEIGHTED_DB: float = 115.7

#: C.3 on printed folio 19: the characteristics the annex declares for the test
#: source before it prints "OK", the maximum directivity index and the maximum
#: sound power level difference of adjacent one-third-octave bands, in
#: decibels. No band is attached to the directivity index.
ANNEX_C_SOURCE_DECLARATION_DB: dict[str, float] = {
    "directivity index": 4.4,
    "adjacent band step": 6.5,
}

#: Table C.3: the same source in a free field over a reflecting plane, in
#: decibels, by octave centre in hertz, at the positions of Table C.1.
ANNEX_C_FREE_FIELD_LEVELS_DB: dict[int, tuple[float, ...]] = {
    125: (83.4, 79.8, 76.9, 74.9, 73.2, 70.7, 67.3, 65.1, 61.5, 59.1, 55.6),
    250: (84.8, 80.9, 78.8, 76.4, 75.1, 72.5, 69.1, 66.6, 62.8, 60.5, 56.5),
    500: (89.7, 85.5, 83.2, 81.4, 80.0, 77.5, 74.1, 71.2, 67.4, 65.3, 60.4),
    1000: (98.8, 94.7, 92.3, 90.3, 88.7, 86.1, 82.6, 79.8, 75.7, 73.7, 67.8),
    2000: (99.2, 94.8, 92.2, 90.1, 88.6, 85.9, 82.6, 80.1, 75.3, 73.4, 65.7),
    4000: (92.8, 90.2, 87.3, 85.0, 83.2, 80.4, 76.8, 75.2, 71.0, 68.0, 57.3),
}

#: Table C.4: the levels measured in the workroom, in decibels.
ANNEX_C_ROOM_LEVELS_DB: dict[int, tuple[float, ...]] = {
    125: (85.7, 82.5, 80.8, 78.3, 77.1, 75.4, 73.7, 71.3, 70.4, 67.3, 65.7),
    250: (84.9, 81.9, 79.6, 77.8, 77.9, 74.3, 72.1, 70.3, 69.8, 65.0, 63.5),
    500: (89.8, 85.7, 83.6, 81.8, 80.5, 78.8, 76.8, 76.3, 72.0, 70.5, 69.1),
    1000: (98.9, 95.1, 93.0, 92.0, 91.0, 87.9, 85.8, 83.5, 81.5, 77.0, 75.6),
    2000: (99.7, 96.0, 93.5, 92.2, 91.0, 89.6, 86.6, 85.0, 81.1, 79.4, 76.7),
    4000: (93.8, 91.2, 88.3, 86.8, 85.7, 84.3, 80.4, 78.1, 74.9, 72.5, 70.5),
}

#: Table C.5: the uncorrected curve D = L_p - L_W as printed, in decibels. The
#: excess family of the annex, Table C.9, is computed on this curve and not on
#: the corrected one.
ANNEX_C_TABLE_C5_DB: dict[int, tuple[float, ...]] = {
    125: (-11.9, -15.1, -16.8, -19.3, -20.5, -22.2, -23.9, -26.3, -27.2, -30.3, -31.9),
    250: (-13.7, -16.7, -19.0, -20.8, -20.7, -24.3, -26.5, -28.3, -28.8, -33.6, -35.1),
    500: (-12.4, -16.5, -18.6, -20.4, -21.7, -23.4, -25.4, -25.9, -30.2, -31.7, -33.1),
    1000: (-11.9, -15.7, -17.8, -18.8, -19.8, -22.9, -25.0, -27.3, -29.3, -33.8, -35.2),
    2000: (-11.5, -15.2, -17.7, -19.0, -20.2, -21.6, -24.6, -26.2, -30.1, -31.8, -34.5),
    4000: (-13.6, -16.2, -19.1, -20.6, -21.7, -23.1, -27.0, -29.3, -32.5, -34.9, -36.9),
}

#: Table C.6: the curve after the Annex B correction, in decibels.
ANNEX_C_TABLE_C6_DB: dict[int, tuple[float, ...]] = {
    125: (-11.8, -14.9, -16.5, -19.0, -20.1, -21.9, -23.7, -26.2, -27.1, -30.2, -31.9),
    250: (-13.9, -16.5, -19.2, -20.7, -20.7, -24.3, -26.5, -28.3, -28.7, -33.6, -35.0),
    500: (-13.9, -17.3, -19.6, -21.4, -22.8, -24.4, -26.1, -26.2, -30.4, -32.0, -33.1),
    1000: (-13.8, -16.9, -19.1, -19.8, -20.6, -23.8, -25.6, -27.7, -29.4, -34.2, -34.9),
    2000: (-13.3, -16.1, -18.4, -19.5, -20.7, -21.9, -25.0, -26.5, -30.0, -31.9, -34.0),
    4000: (-13.1, -16.4, -19.0, -20.3, -21.3, -22.7, -26.5, -29.2, -32.2, -34.4, -35.8),
}

#: Table C.6, last column: the same curve collapsed onto A-weighted pink noise
#: by Eq. (4), in decibels. The annex normalised it with the sum of the Table 1
#: weights and not with the printed 6,2 dB (see the errata registry).
ANNEX_C_TABLE_C6_NORMALIZED_DB: tuple[float, ...] = (
    -13.4,
    -16.5,
    -18.9,
    -20.0,
    -21.1,
    -22.8,
    -25.7,
    -27.5,
    -30.4,
    -33.1,
    -34.6,
)

#: Table C.7: the printed rate of spatial decay, in decibels per distance
#: doubling, by range and octave centre in hertz.
ANNEX_C_TABLE_C7_DB: dict[str, dict[int, float]] = {
    "near": {125: 5.2, 250: 5.2, 500: 5.7, 1000: 4.6, 2000: 4.8, 4000: 5.5},
    "middle": {125: 3.7, 250: 4.0, 500: 3.5, 1000: 4.4, 2000: 4.5, 4000: 5.4},
    "far": {125: 4.6, 250: 6.0, 500: 2.6, 1000: 5.2, 2000: 4.0, 4000: 3.6},
}

#: Table C.8: the same rate for A-weighted pink noise, in decibels per distance
#: doubling.
ANNEX_C_TABLE_C8_DB: dict[str, float] = {"near": 5.1, "middle": 4.6, "far": 4.1}

#: Table C.9: the printed excess of sound pressure level, in decibels.
ANNEX_C_TABLE_C9_DB: dict[str, dict[int, float]] = {
    "near": {125: 5.6, 250: 3.8, 500: 4.3, 1000: 5.2, 2000: 5.4, 4000: 4.0},
    "middle": {125: 8.1, 250: 6.3, 500: 6.9, 1000: 7.3, 2000: 7.8, 4000: 5.6},
    "far": {125: 11.5, 250: 8.6, 500: 9.8, 1000: 8.3, 2000: 9.4, 4000: 6.6},
}

#: Table C.10: the same excess for A-weighted pink noise, in decibels.
ANNEX_C_TABLE_C10_DB: dict[str, float] = {"near": 4.8, "middle": 7.0, "far": 8.5}

#: Table C.11: the excess the annex prints at the conventional distance of each
#: range, in decibels, by octave centre in hertz. Equation (8) does not give
#: these numbers (see the errata registry).
ANNEX_C_TABLE_C11_DB: dict[str, dict[int, float]] = {
    "near": {125: 6.2, 250: 4.0, 500: 4.4, 1000: 5.2, 2000: 5.3, 4000: 3.9},
    "middle": {125: 7.8, 250: 5.4, 500: 6.4, 1000: 6.9, 2000: 7.7, 4000: 5.8},
    "far": {125: 10.6, 250: 7.4, 500: 9.3, 1000: 7.2, 2000: 9.2, 4000: 6.1},
}

#: Table C.12: the same three figures for A-weighted pink noise, in decibels.
ANNEX_C_TABLE_C12_DB: dict[str, float] = {"near": 4.8, "middle": 6.8, "far": 8.0}

#: Table 1 on printed folio 4 (PDF page 14): the A-weighted pink-noise spectrum,
#: in decibels, by octave centre in hertz.
TABLE_1_PINK_NOISE_WEIGHTS_DB: dict[float, float] = {
    125.0: -16.1,
    250.0: -8.6,
    500.0: -3.2,
    1000.0: 0.0,
    2000.0: 1.2,
    4000.0: 1.0,
}

# ---------------------------------------------------------------------------
# Suva 66008.f (2006): a Swiss workroom survey
# ---------------------------------------------------------------------------

#: The seven columns Tableau 2 and the Figure 7 summary are both printed in,
#: on PDF page 13, printed page 11. The last is the total the instrument
#: printed and not Equation (4) over the other six, which runs 0,02 dB to
#: 0,57 dB above it, so it is carried as a seventh measured column.
SUVA_COLUMNS: tuple[str, ...] = (
    "125 Hz",
    "250 Hz",
    "500 Hz",
    "1 kHz",
    "2 kHz",
    "4 kHz",
    "total",
)

#: Tableau 2: the sound distribution curve, printed as "SAK en dB", which is
#: D = Lp - Lw of Equation (1), in decibels. One entry per printed row: the
#: distance in metres against the seven columns above.
SUVA_CURVE_DB: dict[float, tuple[float, ...]] = {
    1.0: (-9.9, -10.2, -8.0, -10.5, -8.1, -9.1, -8.9),
    2.0: (-15.0, -11.7, -13.1, -15.0, -12.2, -11.3, -13.0),
    3.0: (-21.7, -12.1, -15.0, -16.2, -12.6, -14.0, -14.2),
    4.0: (-19.2, -14.6, -15.4, -16.3, -13.3, -15.1, -14.9),
    5.0: (-19.4, -15.9, -15.9, -17.9, -13.8, -15.3, -15.6),
    6.0: (-20.5, -16.1, -14.9, -17.8, -14.1, -16.0, -15.6),
    7.0: (-20.0, -15.3, -16.4, -18.3, -15.3, -16.1, -16.4),
    8.0: (-19.5, -16.4, -17.3, -19.1, -15.5, -16.7, -17.0),
    9.0: (-20.3, -15.3, -18.2, -19.6, -15.8, -16.9, -17.4),
    10.0: (-22.1, -17.4, -18.1, -19.7, -16.0, -17.0, -17.6),
    12.0: (-21.0, -16.3, -18.9, -19.9, -16.7, -18.3, -18.2),
    14.0: (-23.3, -18.1, -19.7, -20.5, -16.3, -18.3, -18.4),
    16.0: (-23.1, -18.0, -20.4, -20.3, -17.4, -19.0, -19.0),
    18.0: (-22.4, -19.2, -18.6, -20.6, -16.9, -19.3, -18.7),
    20.0: (-22.3, -17.8, -21.5, -22.7, -18.4, -20.5, -20.3),
    24.0: (-24.5, -21.4, -21.6, -23.6, -19.2, -21.6, -21.2),
    28.0: (-25.0, -20.3, -21.3, -24.2, -19.7, -22.6, -21.5),
    32.0: (-24.7, -22.6, -23.7, -24.4, -20.7, -23.4, -22.7),
    36.0: (-24.9, -22.9, -22.7, -24.7, -21.5, -23.9, -23.0),
    40.0: (-26.4, -24.4, -23.0, -25.5, -21.1, -24.4, -23.2),
    48.0: (-26.5, -25.1, -24.7, -25.7, -22.3, -25.3, -24.2),
}

#: The Figure 7 summary: the decay rate the survey's own analysis program read
#: off that curve, in decibels per distance doubling. The printed rows are
#: labelled "pres", "moyen" and "loin".
SUVA_DECAY_DB: dict[str, tuple[float, ...]] = {
    "near": (4.5, 2.3, 3.4, 3.0, 2.4, 2.9, 2.8),
    "middle": (2.2, 1.4, 3.1, 1.7, 2.0, 2.2, 2.1),
    "far": (2.6, 4.7, 2.9, 3.4, 3.4, 4.1, 3.5),
}

#: The same summary: the excess of sound pressure level, in decibels.
SUVA_EXCESS_DB: dict[str, tuple[float, ...]] = {
    "near": (1.7, 5.8, 5.0, 3.3, 6.3, 5.7, 5.1),
    "middle": (9.0, 13.5, 12.4, 10.8, 14.4, 13.0, 12.8),
    "far": (15.4, 18.5, 17.9, 16.1, 20.1, 17.5, 18.2),
}

#: 2.6.2 on PDF page 11, printed page 9: the three distance ranges, printed
#: with both bounds, in metres. The path stops at 48 m, so the far range is
#: evaluated over 16 m to 48 m.
SUVA_RANGES_M: dict[str, tuple[float, float]] = {
    "near": (1.0, 5.0),
    "middle": (5.0, 16.0),
    "far": (16.0, 64.0),
}

#: 2.6.3, the same page: the radii it tells a surveyor to stand at, in metres.
SUVA_RADII_M: tuple[float, ...] = (
    1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0, 16.0, 18.0,
    20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 48.0, 56.0, 64.0,
)  # fmt: skip

# ---------------------------------------------------------------------------
# IFA-LSA 01-234 (2020): four positions and the decay they give
# ---------------------------------------------------------------------------

#: Tab. 4.4 on PDF page 17, printed folio 17: the four positions of the path,
#: in metres, which are the distances the German technical rules for noise at
#: work ask for.
IFA_LSA_01_234_DISTANCES_M: tuple[float, ...] = (0.75, 1.50, 3.00, 6.00)

#: Tab. 4.4: the sound pressure levels measured there, in decibels, by octave
#: band centre in hertz, from the nearest position outwards. They are bare Lp
#: rather than D = Lp - Lw, which Equation (5) does not mind, because a
#: constant offset cancels in a least-squares slope. The source is a test sound
#: source.
IFA_LSA_01_234_LEVELS_DB: dict[int, tuple[float, float, float, float]] = {
    500: (79.2, 74.4, 70.2, 67.1),
    1000: (81.9, 77.1, 73.0, 69.8),
    2000: (80.4, 75.3, 71.0, 67.4),
    4000: (84.3, 78.5, 73.2, 69.3),
}

#: Tab. 4.5 on PDF page 18, printed folio 18: the difference printed between
#: each pair of neighbouring positions, in decibels, in the band order of
#: Tab. 4.4.
IFA_LSA_01_234_DIFFERENCES_DB: dict[str, tuple[float, float, float, float]] = {
    "Lp1 - Lp2": (4.8, 4.8, 5.1, 5.8),
    "Lp2 - Lp3": (4.2, 4.1, 4.7, 5.3),
    "Lp3 - Lp4": (3.1, 3.2, 3.6, 3.9),
}

#: The one cell of Tab. 4.5 that its own Tab. 4.4 does not support: 75,3 dB
#: less 71,0 dB is 4,3 dB and the table prints 4,7 dB. The row and the band
#: centre in hertz. The regression settles which cell is right: only the
#: printed level gives the printed decay rate.
IFA_LSA_01_234_MISPRINT: tuple[str, int] = ("Lp2 - Lp3", 2000)

#: Tab. 4.5: the decay rate the sheet prints for each band, in decibels per
#: distance doubling, identical under its two printed methods.
IFA_LSA_01_234_DECAY_DB: dict[int, float] = {
    500: 4.0,
    1000: 4.0,
    2000: 4.3,
    4000: 5.0,
}

# ---------------------------------------------------------------------------
# Probst (2006), BAuA Fb 1083: fitting densities
# ---------------------------------------------------------------------------

#: Anh. 1, one table per surveyed workroom, headed "Streukoerperberechnung nach
#: VDI 3760, 1996": the room, the fittings and the density each table prints.
#: The room is its length, breadth and height in metres followed by the volume
#: it prints in cubic metres; each fitting is a count and three dimensions in
#: metres; the last two entries are the cumulative fitting surface in square
#: metres and the density in reciprocal metres. These four rooms are plain
#: boxes whose printed volume is the product of their printed dimensions; other
#: tables in the annex carry a footnote on a dimension and a volume that is not
#: that product, and are left out.
PROBST_ROOMS: dict[
    str,
    tuple[
        tuple[float, float, float, float],
        tuple[tuple[int, float, float, float], ...],
        float,
        float,
    ],
] = {
    "Tab. 3, folio 79": (
        (14.0, 20.0, 4.5, 1260.0),
        ((5, 4.0, 2.0, 2.0), (1, 5.0, 5.0, 5.0), (10, 0.3, 0.3, 3.0)),
        321.9,
        0.064,
    ),
    "Tab. 6, folio 82": (
        (14.0, 22.0, 6.0, 1848.0),
        ((2, 3.0, 1.0, 2.0), (3, 6.0, 1.0, 2.0)),
        140.0,
        0.019,
    ),
    "Tab. 13, folio 93": (
        (23.0, 20.0, 6.0, 2760.0),
        ((5, 4.0, 2.0, 2.0),),
        160.0,
        0.014,
    ),
    "Tab. 22, folio 105": (
        (18.0, 11.0, 3.5, 693.0),
        ((1, 4.0, 3.0, 3.0),),
        54.0,
        0.019,
    ),
}
