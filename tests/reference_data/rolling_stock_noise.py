#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for railway rolling stock noise and its reference track.

ISO 3095:2013 (third edition), read on the rasterized pages of the ISO copy;
its PDF page is the printed folio plus 6. Figure 2 (folio 12) prints every
point of the roughness limit as a number beside it, Figure 3 (folio 13) prints
the decay-rate limits in a table beside the curves, Figure 10 (folio 23)
dimensions the microphone positions of four units, and Table G.2 (folios 50
and 51) is a worked uncertainty budget.

BS EN 15610:2009, identical to EN 15610:2009: the Annex B.9.2 listing (PDF
page 28, folio 26) prints the same roughness limit as a table of numbers, the
"2007 TSI limit", which is a second, independent printing of Figure 2.

BS EN ISO 3095:2005 (second edition), 3.14 (PDF pages 12 and 13, folios 4 and
5): the transit exposure level the 2013 edition dropped.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ISO 3095:2013 Figure 2 (folio 12): nominal wavelength in centimetres and the
# printed label of each point, dB re 1 um. The axis labels the 3,15, 1,25,
# 0,63 and 0,315 cm bands as 3.2, 1.3, 0.6 and 0.3.
# ---------------------------------------------------------------------------
FIGURE_2_WAVELENGTHS_CM: tuple[float, ...] = (
    40.0, 31.5, 25.0, 20.0, 16.0, 12.5, 10.0, 8.0, 6.3, 5.0, 4.0,
    3.15, 2.5, 2.0, 1.6, 1.25, 1.0, 0.8, 0.63, 0.5, 0.4, 0.315,
)  # fmt: skip
FIGURE_2_LIMIT_DB: tuple[float, ...] = (
    17.1, 15.0, 13.0, 11.0, 9.0, 7.0, 4.9, 2.9, 0.9, -1.1, -3.2,
    -5.0, -5.6, -6.2, -6.8, -7.4, -8.0, -8.6, -9.2, -9.8, -10.4, -11.0,
)  # fmt: skip

# ---------------------------------------------------------------------------
# EN 15610:2009 Annex B.9.2 (folio 26): wl_tsi (m) and tsi_rough (dB), as the
# listing types them, 3,15 cm as 0.032 and 3,15 mm as 0.003.
# ---------------------------------------------------------------------------
EN15610_LISTING_WAVELENGTHS_M: tuple[float, ...] = (
    0.400, 0.315, 0.250, 0.200, 0.160, 0.125, 0.100, 0.080, 0.063, 0.050, 0.040,
    0.032, 0.025, 0.020, 0.016, 0.013, 0.010, 0.008, 0.006, 0.005, 0.004, 0.003,
)  # fmt: skip
EN15610_LISTING_LIMIT_DB: tuple[float, ...] = (
    17.1, 15.0, 13.0, 11.0, 9.0, 7.0, 4.9, 2.9, 0.9, -1.1, -3.2, -5.0, -5.6,
    -6.2, -6.8, -7.4, -8.0, -8.6, -9.2, -9.8, -10.4, -11.0,
)  # fmt: skip

# ---------------------------------------------------------------------------
# ISO 3095:2013 Figure 3 (folio 13): the table beside the curves, frequency in
# hertz, A the vertical and B the lateral lower limit, dB/m.
# ---------------------------------------------------------------------------
FIGURE_3_FREQUENCIES_HZ: tuple[float, ...] = (
    250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0,
    2000.0, 2500.0, 3150.0, 4000.0, 5000.0,
)  # fmt: skip
FIGURE_3_VERTICAL_DB_PER_M: tuple[float, ...] = (
    2.00, 2.00, 6.00, 6.00, 6.00, 2.19, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80,
)  # fmt: skip
FIGURE_3_LATERAL_DB_PER_M: tuple[float, ...] = (
    2.04, 1.38, 0.94, 0.64, 0.43, 0.29, 0.20, 0.20, 0.32, 0.50, 0.50, 0.50, 0.50, 0.50,
)  # fmt: skip

# ---------------------------------------------------------------------------
# ISO 3095:2013 Figure 10 (folio 23): the four units it draws, their length in
# metres and the distances it dimensions, from the front measurement cross
# section backwards: 10 m ahead of the unit, then the gaps to each further
# position. Converted to positions behind the front of the unit.
# ---------------------------------------------------------------------------
FIGURE_10_POSITIONS_M: dict[float, tuple[float, ...]] = {
    42.0: (-10.0,),
    54.0: (-10.0, 17.0),
    87.0: (-10.0, 33.5),
    108.0: (-10.0, 17.0, 44.0),
}

# ---------------------------------------------------------------------------
# ISO 3095:2013 Table G.2 (folios 50 and 51): the uncertainty budget of a
# standstill measurement. Each row: quantity, "possible typical range" (the
# mean value correction, dB) and standard uncertainty u(x_i), dB; every
# sensitivity coefficient is 1. The reading is 55 dB.
# ---------------------------------------------------------------------------
TABLE_G2_READING_DB = 55.0
TABLE_G2_ROWS: tuple[tuple[str, float, float], ...] = (
    ("cal, reference", 0.0, 0.14),
    ("cal, long term", 0.0, 0.04),
    ("cal, supply voltage", 0.0, 0.06),
    ("cal, distortion factor", 0.105, 0.06),
    ("slm, direction", 0.0, 0.25),
    ("slm frequency", 0.0, 0.25),
    ("slm, level linearity", 0.0, 0.46),
    ("calibrator, meteorological", 0.0, 0.14),
    ("slm, wind screen", 0.06, 0.03),
    ("tripod", 0.0, 0.35),
    ("distance", 0.0, 0.06),
    ("ground level", 0.515, 0.30),
    ("rounding", 0.0, 0.29),
)
#: The last row of Table G.2 and the two lines under it.
TABLE_G2_LEVEL_DB = 55.68
TABLE_G2_COMBINED_UNCERTAINTY_DB = 0.83
TABLE_G2_EXPANDED_UNCERTAINTY_DB = 1.66

# ---------------------------------------------------------------------------
# ISO 3095:2013 Figure G.1 (folio 51): the order its bars are drawn in, from
# the largest share of the variance to the smallest, as its axis labels them.
# The bar heights carry no printed number; the order does.
# ---------------------------------------------------------------------------
FIGURE_G1_ORDER: tuple[str, ...] = (
    "slm, level linearity",
    "tripod",
    "ground level",
    "rounding",
    "slm, direction",
    "slm frequency",
    "cal, reference",
    "calibrator, meteorological",
    "cal, supply voltage",
    "cal, distortion factor",
    "distance",
    "cal, long term",
    "slm, wind screen",
)

# ---------------------------------------------------------------------------
# ISO 3095:2013 Table G.1 (folios 48 and 49): the rectangular rows whose
# printed standard uncertainty is the half-width over the square root of 3
# (Formula G.2), as (quantity, half-width a, printed u), dB. The two rows that
# are not (the 25 m distance, printed 0,004 dB, and the 7,5 m ground level,
# printed 0,55 dB) are in the errata register.
# ---------------------------------------------------------------------------
TABLE_G1_RECTANGULAR_ROWS: tuple[tuple[str, float, float], ...] = (
    ("cal, reference", 0.25, 0.14),
    ("cal, long term", 0.07, 0.04),
    ("cal, supply voltage", 0.10, 0.06),
    ("cal, distortion factor", 0.105, 0.06),
    ("slm, direction", 0.44, 0.25),
    ("slm frequency", 0.44, 0.25),
    ("slm, level linearity", 0.8, 0.46),
    ("slm, impuls", 1.25, 0.72),
    ("calibrator, meteorological", 0.25, 0.14),
    ("slm, air pressure", 0.9, 0.52),
    ("slm, temperature", 0.5, 0.29),
    ("slm, humidity", 0.5, 0.29),
    ("slm, wind screen", 0.06, 0.03),
    ("tripod", 0.6, 0.35),
    ("train speed", 0.3, 0.17),
    ("distance, 7,5 m", 0.23, 0.13),
    ("ground level, 25 m", 0.165, 0.10),
    ("rounding", 0.5, 0.29),
)
TABLE_G1_DISTANCE_25M = ("distance, 25 m", 0.07, 0.004)
TABLE_G1_GROUND_LEVEL_7_5M = ("ground level, 7,5 m", 0.515, 0.55)
