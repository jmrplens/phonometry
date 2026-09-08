#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Predicting the fundamental frequency of a building (ISO 4866 Annex D).

The annex is four empirical predictors and the errors they carry, and every
number in it is printed rather than derived. These rows read each one back
through the library: the measured fit at three heights, the storey rule, the
two ends of each of the three code coefficient ranges as a period a caller
would actually get, the error band the annex puts on any of them, and the two
ends of the measured damping range.

Oracle: ISO 4866:2010, Annex D on printed folios 24 to 26 (PDF pages 30 to
32): Formulae (D.1), (D.2) and (D.3) with their coefficient ranges in D.2, the
``f = 46/h`` fit and the ± 50 % of D.3, and the damping values of D.4.
"""

from __future__ import annotations

import functools

import phonometry as ph

from ..registry import Outcome, numeric, register

_BUILDING_RESPONSE = "Building response prediction (ISO 4866)"

#: D.3: ``f = 46/h`` Hz, read at three heights. A 46 m building comes to
#: exactly 1 Hz, which is the arithmetic the constant is chosen to make easy.
_FIT_HEIGHTS_M = (23.0, 46.0, 92.0)

#: D.2, Formula (D.1): the ends of the ``k1`` range, as the period a 50 m
#: building gets from each.
_HEIGHT_M = 50.0
_K1_ENDS = (0.014, 0.03)

#: D.2, Formula (D.2): the ends of the ``k2`` range, for a 60 m building 20 m
#: wide.
_TALL_M, _WIDE_M = 60.0, 20.0
_K2_ENDS = (0.087, 0.109)

#: D.2, Formula (D.3): the ends of the ``k3`` range, same building.
_K3_ENDS = (0.06, 0.08)

#: D.4: the damping ratios measured on ten buildings, as percentages of
#: critical.
_DAMPING_ENDS_PERCENT = (0.5, 2.1)

#: Every number here is printed to two or three figures.
_TOLERANCE = 5e-4


def _chk_fit(height: float) -> Outcome:
    """The ``f = 46/h`` fit at one height."""
    printed = 46.0 / height
    computed = float(ph.vibration.height_fundamental_frequency(height))
    return numeric(printed, computed, _TOLERANCE, unit="Hz", places=4)


def _register_fit() -> None:
    """Register the measured fit at three heights."""
    for height in _FIT_HEIGHTS_M:
        register(
            _BUILDING_RESPONSE,
            "ISO 4866:2010 D.3",
            f"Fundamental frequency of a {height:g} m building, f = 46/h, Hz",
        )(functools.partial(_chk_fit, height))


_register_fit()


@register(
    _BUILDING_RESPONSE,
    "ISO 4866:2010 D.3",
    "The same fit as a period, T = 0,022 h, s",
)
def _chk_fit_period() -> Outcome:
    """D.3 prints the fit twice, and the two printings have to agree."""
    computed = ph.vibration.HEIGHT_PERIOD_COEFFICIENT_S_PER_M * _HEIGHT_M
    return numeric(1.1, computed, _TOLERANCE, unit="s", places=4)


@register(
    _BUILDING_RESPONSE,
    "ISO 4866:2010 D.2",
    "Fundamental frequency of a ten-storey building, f = 10/n, Hz",
)
def _chk_storeys() -> Outcome:
    """The storey rule, which DIN 4150-3 6.4 prints in the same words."""
    computed = ph.vibration.fundamental_frequency("storeys", storeys=10)
    return numeric(1.0, computed, _TOLERANCE, unit="Hz", places=4)


def _chk_code_period(model: str, coefficient: float, printed: float) -> Outcome:
    """One end of one code coefficient range, as the period it produces."""
    if model == "height":
        computed = ph.vibration.fundamental_period(
            model, height_m=_HEIGHT_M, coefficient=coefficient
        )
    else:
        computed = ph.vibration.fundamental_period(
            model, height_m=_TALL_M, width_m=_WIDE_M, coefficient=coefficient
        )
    return numeric(printed, computed, _TOLERANCE, unit="s", places=4)


#: The period each end of each range produces. Worked by hand from the printed
#: formula and its printed coefficient, so the row exercises the formula and
#: states a period a caller would get rather than repeating a coefficient back
#: at itself. The heights are 50 m for (D.1) and 60 m by 20 m for the other
#: two.
_CODE_CASES = (
    ("height", "D.1", _K1_ENDS[0], 0.7),
    ("height", "D.1", _K1_ENDS[1], 1.5),
    ("height_width", "D.2", _K2_ENDS[0], 1.1673),
    ("height_width", "D.2", _K2_ENDS[1], 1.4625),
    ("slenderness", "D.3", _K3_ENDS[0], 0.6971),
    ("slenderness", "D.3", _K3_ENDS[1], 0.9295),
)


def _register_code_periods() -> None:
    """Register both ends of the three coefficient ranges of D.2."""
    for model, formula, coefficient, printed in _CODE_CASES:
        register(
            _BUILDING_RESPONSE,
            f"ISO 4866:2010 Formula ({formula})",
            f"Fundamental period from the {model} form at k = {coefficient:g}, s",
        )(functools.partial(_chk_code_period, model, coefficient, printed))


_register_code_periods()


@register(
    _BUILDING_RESPONSE,
    "ISO 4866:2010 D.3",
    "Upper end of the error band an empirical prediction carries, Hz",
)
def _chk_band_upper() -> Outcome:
    """The ± 50 % D.3 calls not uncommon, at the top of the band."""
    _, upper = ph.vibration.empirical_frequency_bounds(2.0)
    return numeric(3.0, upper, _TOLERANCE, unit="Hz", places=4)


@register(
    _BUILDING_RESPONSE,
    "ISO 4866:2010 D.3",
    "Lower end of the error band an empirical prediction carries, Hz",
)
def _chk_band_lower() -> Outcome:
    """The same band, at the bottom."""
    lower, _ = ph.vibration.empirical_frequency_bounds(2.0)
    return numeric(1.0, lower, _TOLERANCE, unit="Hz", places=4)


def _chk_damping(index: int) -> Outcome:
    """One end of the damping range of D.4, as a percentage of critical."""
    printed = _DAMPING_ENDS_PERCENT[index]
    computed = 100.0 * ph.vibration.DAMPING_RATIO_RANGE[index]
    return numeric(printed, computed, _TOLERANCE, unit="%", places=4)


def _register_damping() -> None:
    """Register both ends of the measured damping range of D.4."""
    for index, end in enumerate(("Lowest", "Highest")):
        register(
            _BUILDING_RESPONSE,
            "ISO 4866:2010 D.4",
            f"{end} damping ratio measured on a building, % of critical",
        )(functools.partial(_chk_damping, index))


_register_damping()
