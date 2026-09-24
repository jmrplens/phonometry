#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for the Statistical Pass-By method (ISO 11819-1:1997).

Read in BS EN ISO 11819-1:2001, which is identical to ISO 11819-1:1997 (its
national foreword). The document is a scan: every value below was read on the
printed page. Its PDF page is the printed folio plus 8: Table 1 on folio 13,
the 9.5 formula on folio 14, Table 2 on folio 15, the 7.3 minimum numbers on
folio 10, Annex D on folio 22 and the Annex E report on folios 24 to 26.

Annex E prints the regression of each vehicle category (intercept, slope,
number of vehicles, mean speed and the statistics beside them) but not the
pass-bys, so the fit itself has no printed oracle.
:func:`annex_e_pass_bys` places pass-bys whose least-squares line is exactly the
printed one, so the whole chain can be run from pass-bys to the index; what it
checks is the chain, not the regression.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# ISO 11819-1:1997 Table 1 (folio 13): reference speed (km/h) and weighting
# factor W_x of each vehicle category in each road speed category.
# ---------------------------------------------------------------------------
TABLE_1_REFERENCE_SPEEDS_KMH: dict[str, dict[str, float]] = {
    "low": {"1": 50.0, "2a": 50.0, "2b": 50.0},
    "medium": {"1": 80.0, "2a": 70.0, "2b": 70.0},
    "high": {"1": 110.0, "2a": 85.0, "2b": 85.0},
}
TABLE_1_WEIGHTING_FACTORS: dict[str, dict[str, float]] = {
    "low": {"1": 0.900, "2a": 0.075, "2b": 0.025},
    "medium": {"1": 0.800, "2a": 0.100, "2b": 0.100},
    "high": {"1": 0.700, "2a": 0.075, "2b": 0.225},
}

# ---------------------------------------------------------------------------
# ISO 11819-1:1997 Table 2 (folio 15): standard deviation of individual
# vehicles around L_veh and the 95 % confidence interval around L_veh, dB.
# ---------------------------------------------------------------------------
TABLE_2_STANDARD_DEVIATIONS_DB: dict[str, float] = {"1": 1.5, "2a": 2.0, "2b": 2.0}
TABLE_2_CONFIDENCE_INTERVALS_DB: dict[str, float] = {"1": 0.3, "2a": 0.7, "2b": 0.7}

# ---------------------------------------------------------------------------
# ISO 11819-1:1997 7.3 (folio 10): minimum numbers of vehicles for surface
# classification, "2" being categories 2a and 2b together; and 9.3 (folio 13):
# the standard deviations of speed the reference speed may lie within.
# ---------------------------------------------------------------------------
MINIMUM_VEHICLE_COUNTS: dict[str, int] = {"1": 100, "2a": 30, "2b": 30, "2": 80}
SPEED_WINDOW_STANDARD_DEVIATIONS: dict[str, float] = {"1": 1.5, "2a": 1.0, "2b": 1.0}

# ---------------------------------------------------------------------------
# ISO 11819-1:1997 Annex D (folio 22), the table printed as "Table E.1": L_veh
# (dB) of the seven surfaces and the "Average surface (Normalized reference
# case)" row.
# ---------------------------------------------------------------------------
ANNEX_D_SURFACES_DB: dict[str, dict[str, float]] = {
    "A1": {"1": 76.6, "2a": 81.1, "2b": 84.1},
    "A2": {"1": 75.9, "2a": 80.0, "2b": 83.0},
    "A3": {"1": 76.4, "2a": 81.8, "2b": 84.0},
    "A4": {"1": 77.2, "2a": 81.5, "2b": 84.9},
    "B1": {"1": 76.1, "2a": 81.0, "2b": 84.4},
    "B2": {"1": 76.4, "2a": 80.4, "2b": 83.3},
    "B3": {"1": 76.4, "2a": 81.0, "2b": 84.1},
}
ANNEX_D_AVERAGE_DB: dict[str, float] = {"1": 76.4, "2a": 81.0, "2b": 84.0}

# ---------------------------------------------------------------------------
# ISO 11819-1:1997 Annex E, "Sound level and speed regression data
# (uncorrected for temperature)", road speed category medium (folio 26).
# ---------------------------------------------------------------------------
ANNEX_E_ROAD_SPEED_CATEGORY = "medium"
ANNEX_E_VEHICLE_COUNTS: dict[str, int] = {"1": 107, "2a": 34, "2b": 53}
ANNEX_E_HEAVY_VEHICLE_COUNT = 87
ANNEX_E_INTERCEPTS_DB: dict[str, float] = {"1": 16.6, "2a": 46.5, "2b": 34.5}
ANNEX_E_SLOPES_DB: dict[str, float] = {"1": 32.55, "2a": 18.76, "2b": 26.74}
ANNEX_E_CORRELATIONS: dict[str, float] = {"1": 0.79, "2a": 0.51, "2b": 0.49}
ANNEX_E_MEAN_LEVELS_DB: dict[str, float] = {"1": 80.0, "2a": 81.8, "2b": 84.4}
ANNEX_E_LEVEL_STANDARD_DEVIATIONS_DB: dict[str, float] = {
    "1": 2.2,
    "2a": 2.5,
    "2b": 2.3,
}
ANNEX_E_RESIDUAL_STANDARD_DEVIATIONS_DB: dict[str, float] = {
    "1": 1.3,
    "2a": 2.1,
    "2b": 2.0,
}
#: "Value converted from the logarithm of speed".
ANNEX_E_MEAN_SPEEDS_KMH: dict[str, float] = {"1": 88.5, "2a": 75.8, "2b": 73.7}
ANNEX_E_SPEED_STANDARD_DEVIATIONS_KMH: dict[str, float] = {
    "1": 13.3,
    "2a": 7.5,
    "2b": 6.4,
}
ANNEX_E_VEHICLE_SOUND_LEVELS_DB: dict[str, float] = {
    "1": 78.5,
    "2a": 81.1,
    "2b": 83.8,
}
#: "Vehicle Sound Level after temp. correction" (folio 26), air 23 °C average
#: (folio 25).
ANNEX_E_CORRECTED_VEHICLE_SOUND_LEVELS_DB: dict[str, float] = {
    "1": 78.8,
    "2a": 81.1,
    "2b": 83.8,
}
ANNEX_E_INDEX_DB = 79.9
ANNEX_E_CORRECTED_INDEX_DB = 80.1
ANNEX_E_REFERENCE_INDEX_DB = 77.3
ANNEX_E_DIFFERENCE_DB = 2.8


def annex_e_pass_bys(category: str) -> tuple[list[float], list[float]]:
    r"""Pass-bys whose least-squares line is exactly the Annex E one.

    Pairs of pass-bys at one speed, one level above the printed line and one
    below it by the same amount, leave both normal equations of the fit
    satisfied, so the line through them is the printed intercept and slope
    exactly; an odd count gets one more pass-by on the line at the mean speed.
    The speeds are spread evenly in ``lg v`` about the logarithm of the printed
    mean speed, so the mean speed :math:`10^{\overline{\lg v}}` is the printed
    one, and the two spreads are set to give the printed correlation
    coefficient and residual standard deviation.

    :param category: ``"1"``, ``"2a"`` or ``"2b"``.
    :return: The speeds, in km/h, and the maximum levels, in dB.
    """
    n = ANNEX_E_VEHICLE_COUNTS[category]
    intercept = ANNEX_E_INTERCEPTS_DB[category]
    slope = ANNEX_E_SLOPES_DB[category]
    r = ANNEX_E_CORRELATIONS[category]
    s_res = ANNEX_E_RESIDUAL_STANDARD_DEVIATIONS_DB[category]
    centre = math.log10(ANNEX_E_MEAN_SPEEDS_KMH[category])
    pairs = n // 2
    # The residual of each pair, so that sum(e^2) / (n - 2) is s_res^2.
    offset = s_res * math.sqrt((n - 2) / (2 * pairs))
    # The spread of lg v that gives the printed r with that residual:
    # r^2 = b^2 s_x^2 / (b^2 s_x^2 + s_res^2 (n - 2) / (n - 1)).
    s_x = r * s_res * math.sqrt((n - 2) / (n - 1)) / (slope * math.sqrt(1 - r * r))
    # Evenly spaced positions u_k, centred on zero, scaled to that spread.
    raw = [k - (pairs - 1) / 2 for k in range(pairs)]
    raw_sd = math.sqrt(2 * sum(u * u for u in raw) / (n - 1))
    speeds: list[float] = []
    levels: list[float] = []
    for u in raw:
        x = centre + s_x * u / raw_sd
        line = intercept + slope * x
        speeds.extend((10.0**x, 10.0**x))
        levels.extend((line + offset, line - offset))
    if n % 2:
        speeds.append(10.0**centre)
        levels.append(intercept + slope * centre)
    return speeds, levels
