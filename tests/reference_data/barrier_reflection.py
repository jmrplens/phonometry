#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for the in situ sound reflection of a road device (EN 1793-5:2016).

Read on the rendered pages of BS EN 1793-5:2016 (the English text of EN
1793-5:2016). The PDF carries two unnumbered cover pages, so a printed folio
is the PDF page less two.

* Table 2 (PDF page 18, printed folio 16): the direct and the specular path
  to each microphone and :math:`C_{geo,k}`, to two decimals.
* Table 3 (PDF page 43, printed folio 41): the nominal path differences of
  the two position checks and their tolerance.
* 5.6.1 NOTE 1 (PDF page 37, printed folio 35): the maximum sampled area of a
  4 m by 4 m sample, 1,96 m, at 340 m/s.
* 5.5.5 (PDF page 32, printed folio 30): the three lengths of the 7,9 ms and
  6,0 ms windows; 5.5.1 (PDF page 28, printed folio 26) those of the 1,3 ms
  gain window.
* 5.5.7 (PDF page 35, printed folio 33): the low frequency limit of a 4 m
  sample at microphones 2, 5 and 8, "about" 160 Hz, 170 Hz and 220 Hz.
* Figure 14 (PDF pages 35 and 36, printed folios 33 and 34): the three
  curves of the low frequency limit against the height of the device, read
  off the images embedded in the PDF (906 by 561 pixels each), calibrated on
  the eleven gridlines from 0 Hz to 1 000 Hz and on the 2,0 m and 8,0 m ends
  of the axis, to about 1 %.
* Table B.1 (PDF page 55, printed folio 53): the index of twelve grid
  positions in front of a 4 m absorptive barrier, their average and
  :math:`DL_{RI}` = 8 dB.
* Table B.2 (PDF page 57, printed folio 55): the expanded uncertainty of that
  example from the high column of Table A.1 and :math:`k_p` = 1,96, and
  :math:`DL_{RI}` before rounding, 7,68 dB.
* B.5 (PDF page 56, printed folio 54): the conservative 95 % interval of the
  single number, [6,09, 9,27] dB.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Table 2: d_i,k [m], d_r,k [m], C_geo,k, microphones 1 to 9
# ---------------------------------------------------------------------------
TABLE_2: tuple[tuple[float, float, float], ...] = (
    (1.37, 1.84, 1.80),
    (1.31, 1.80, 1.87),
    (1.37, 1.84, 1.80),
    (1.31, 1.80, 1.87),
    (1.25, 1.75, 1.96),
    (1.31, 1.80, 1.87),
    (1.37, 1.84, 1.80),
    (1.31, 1.80, 1.87),
    (1.37, 1.84, 1.80),
)

# ---------------------------------------------------------------------------
# Table 3: delta d_k5 [m], delta d_k [m], microphones 1 to 9; epsilon_k [m]
# ---------------------------------------------------------------------------
TABLE_3: tuple[tuple[float, float], ...] = (
    (0.122, 0.467),
    (0.062, 0.483),
    (0.122, 0.467),
    (0.062, 0.483),
    (0.000, 0.500),
    (0.062, 0.483),
    (0.122, 0.467),
    (0.062, 0.483),
    (0.122, 0.467),
)
TABLE_3_TOLERANCE_M = 0.025

# ---------------------------------------------------------------------------
# 5.6.1 NOTE 1 and the windows of 5.5.5 and 5.5.1
# ---------------------------------------------------------------------------
SAMPLED_AREA_RADIUS_M = 1.96
SAMPLED_AREA_SPEED_M_S = 340.0
SAMPLED_AREA_WINDOW_S = 7.9e-3
#: total length [s] -> (leading edge, flat part, trailing edge) [s]
WINDOW_PARTS_S: dict[float, tuple[float, float, float]] = {
    7.9e-3: (0.5e-3, 5.18e-3, 2.22e-3),
    6.0e-3: (0.5e-3, 3.85e-3, 1.65e-3),
    1.3e-3: (0.5e-3, 0.56e-3, 0.24e-3),
}

# ---------------------------------------------------------------------------
# 5.5.7: "about" these limits for a 4 m by 4 m sample, per microphone [Hz]
# ---------------------------------------------------------------------------
LOW_FREQUENCY_LIMITS_4M_HZ: dict[int, float] = {2: 160.0, 5: 170.0, 8: 220.0}

# ---------------------------------------------------------------------------
# Figure 14 (a), (b) and (c): the curve of microphones 2, 5 and 8, read off
# the page as (device height [m], low frequency limit [Hz]); the curve of
# microphone 8 starts above the 1 000 Hz top of the axis below 2,5 m.
# ---------------------------------------------------------------------------
FIGURE_14_HZ: dict[int, tuple[tuple[float, float], ...]] = {
    2: (
        (2.0, 560.0),
        (2.5, 351.0),
        (3.0, 252.0),
        (3.5, 195.0),
        (4.0, 160.0),
        (4.5, 134.0),
        (5.0, 116.0),
        (6.0, 92.0),
        (7.0, 75.0),
        (7.9, 65.0),
    ),
    5: (
        (2.5, 398.0),
        (2.75, 327.0),
        (3.0, 277.0),
        (3.5, 211.0),
        (4.0, 170.0),
        (4.5, 142.0),
        (5.0, 121.0),
        (6.0, 94.0),
        (7.0, 77.0),
        (7.9, 65.0),
    ),
    8: (
        (2.5, 848.0),
        (3.0, 443.0),
        (3.5, 296.0),
        (4.0, 220.0),
        (4.5, 175.0),
        (5.0, 145.0),
        (6.0, 108.0),
        (7.0, 85.0),
        (7.9, 72.0),
    ),
}

# ---------------------------------------------------------------------------
# Table B.1: RI_1 ... RI_12 and the average, per band [Hz]
# ---------------------------------------------------------------------------
TABLE_B1_BANDS_HZ: tuple[float, ...] = (
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
)
#: One row per band, the twelve grid positions in order.
TABLE_B1_POSITIONS: tuple[tuple[float, ...], ...] = (
    (0.59, 0.62, 0.57, 0.55, 0.58, 0.59, 0.57, 0.57, 0.51, 0.61, 0.61, 0.62),
    (0.60, 0.62, 0.58, 0.54, 0.57, 0.58, 0.58, 0.58, 0.51, 0.60, 0.59, 0.61),
    (0.63, 0.65, 0.60, 0.55, 0.57, 0.59, 0.60, 0.60, 0.53, 0.60, 0.57, 0.60),
    (0.38, 0.42, 0.31, 0.37, 0.37, 0.35, 0.37, 0.39, 0.31, 0.36, 0.31, 0.32),
    (0.43, 0.47, 0.35, 0.39, 0.39, 0.36, 0.42, 0.43, 0.35, 0.38, 0.34, 0.36),
    (0.43, 0.45, 0.34, 0.37, 0.37, 0.34, 0.37, 0.37, 0.33, 0.33, 0.33, 0.33),
    (0.34, 0.33, 0.26, 0.28, 0.30, 0.27, 0.22, 0.24, 0.22, 0.21, 0.25, 0.23),
    (0.15, 0.15, 0.12, 0.13, 0.15, 0.15, 0.07, 0.08, 0.08, 0.11, 0.12, 0.12),
    (0.05, 0.04, 0.04, 0.07, 0.05, 0.06, 0.06, 0.04, 0.04, 0.09, 0.05, 0.06),
    (0.07, 0.07, 0.06, 0.13, 0.08, 0.07, 0.17, 0.11, 0.09, 0.11, 0.09, 0.07),
    (0.11, 0.10, 0.09, 0.13, 0.11, 0.08, 0.17, 0.16, 0.10, 0.08, 0.07, 0.04),
    (0.11, 0.13, 0.10, 0.07, 0.11, 0.08, 0.10, 0.13, 0.09, 0.10, 0.09, 0.07),
    (0.39, 0.53, 0.16, 0.37, 0.28, 0.21, 0.30, 0.23, 0.18, 0.30, 0.35, 0.29),
    (0.19, 0.28, 0.10, 0.20, 0.15, 0.12, 0.16, 0.15, 0.08, 0.13, 0.17, 0.22),
    (0.15, 0.23, 0.21, 0.14, 0.13, 0.17, 0.15, 0.15, 0.16, 0.12, 0.15, 0.10),
    (0.31, 0.33, 0.27, 0.26, 0.23, 0.19, 0.18, 0.25, 0.18, 0.16, 0.23, 0.21),
    (0.39, 0.27, 0.22, 0.23, 0.26, 0.21, 0.28, 0.22, 0.18, 0.28, 0.21, 0.24),
    (0.55, 0.43, 0.25, 0.52, 0.53, 0.53, 0.40, 0.43, 0.23, 0.46, 0.36, 0.45),
)
TABLE_B1_AVERAGE: tuple[float, ...] = (
    0.58,
    0.58,
    0.59,
    0.35,
    0.39,
    0.36,
    0.26,
    0.12,
    0.05,
    0.09,
    0.10,
    0.10,
    0.30,
    0.16,
    0.16,
    0.23,
    0.25,
    0.43,
)
#: The two averages whose printed particular values mean to an exact half
#: (0,355 and 0,155), printed one down and one up: consistent with averages
#: taken from unrounded particular values, which the print does not show.
TABLE_B1_TIED_BANDS_HZ: tuple[float, ...] = (200.0, 2500.0)
#: The single number printed under the table, and the lowest band it sums.
TABLE_B1_RATING_DB = 8
TABLE_B1_LOWEST_BAND_HZ = 200.0

# ---------------------------------------------------------------------------
# Table B.2: sR (High) and U (95 %), per band; the DL_RI row
# ---------------------------------------------------------------------------
TABLE_B2_REPRODUCIBILITY: tuple[float, ...] = (
    0.32,
    0.18,
    0.12,
    0.14,
    0.13,
    0.13,
    0.12,
    0.12,
    0.14,
    0.15,
    0.13,
    0.15,
    0.16,
    0.15,
    0.15,
    0.17,
    0.20,
    0.23,
)
TABLE_B2_EXPANDED: tuple[float, ...] = (
    0.62,
    0.34,
    0.24,
    0.27,
    0.25,
    0.25,
    0.24,
    0.23,
    0.26,
    0.28,
    0.25,
    0.28,
    0.31,
    0.29,
    0.29,
    0.32,
    0.39,
    0.45,
)
#: The seven cells printed a hundredth below 1,96 times the printed sR, as
#: unrounded standard deviations would give; the print does not show which
#: values the example multiplied (docs/ERRATA.md).
TABLE_B2_LOW_CELLS_HZ: tuple[float, ...] = (
    100.0,
    125.0,
    500.0,
    630.0,
    800.0,
    1250.0,
    3150.0,
)
TABLE_B2_COVERAGE_FACTOR = 1.96
TABLE_B2_RATING_DB = 7.68
TABLE_B2_RATING_REPRODUCIBILITY_DB = 0.81
TABLE_B2_RATING_EXPANDED_DB = 1.59
#: B.5 (PDF page 56, printed folio 54): the conservative 95 % interval of the
#: single number.
TABLE_B2_RATING_INTERVAL_DB: tuple[float, float] = (6.09, 9.27)
