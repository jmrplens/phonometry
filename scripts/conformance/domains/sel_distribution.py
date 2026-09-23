#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How often a blast is how loud: the distribution of its sound exposure level.

ISO 13474:2009 prints one worked example, Annex A: a TOW anti-tank missile
launcher heard at 3 020 m under 27 excess-attenuation classes. Table A.3 gives
the A-weighted single-event level of each class and its probability by day,
by night and over 07:00 to 19:00; Table A.4 sorts the classes and gives their
boundaries and densities; Figure A.3 prints the two long-term levels and five
exceedance levels of the distribution once it has been spread for turbulence.
Every row below starts from Table A.3.

Oracle: BS ISO 13474:2009, which reproduces ISO 13474:2009 without
modification: Tables A.3 and A.4 on printed folios 32 and 33 (PDF pages 40
and 41), the running text on folio 34 (PDF page 42), Figure A.3 on folio 36
(PDF page 44).

Two printed defects sit in this oracle and both are recorded in
``docs/ERRATA.md``. The running text gives the shift of Equation (22) as
1,04 dB with a standard deviation of 5 dB, where the equation gives 2,878 dB;
LT2 and the curve of Figure A.2 were computed with 2,878 dB, so the rows use
the equation. And four of the five exceedance levels of Figure A.3 are not
the roots of Equation (25): they are reproduced to the printed digit by a
curve accumulated from the 15 dB its axis starts at, which the row for them
states and the row for the 50 % level does not need.
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref
from scipy import integrate, optimize

from phonometry import environment

from ..registry import Outcome, count, numeric, register

_ISO13474 = "Impulsive sound exposure distribution (ISO 13474)"

_LEVELS = np.array([row[1] for row in ref.ISO13474_TABLE_A3])
#: The 07:00 to 19:00 probability at full precision, formed from the day and
#: night columns with the proportions the paragraph above Table A.3 gives.
_PERIOD = ref.ISO13474_ANNEX_A_DAY_FRACTION * np.array(
    [row[2] for row in ref.ISO13474_TABLE_A3]
) + ref.ISO13474_ANNEX_A_NIGHT_FRACTION * np.array(
    [row[3] for row in ref.ISO13474_TABLE_A3]
)
#: The 07:00 to 19:00 column as printed, rounded to four decimals.
_PRINTED_PERIOD = np.array([row[4] for row in ref.ISO13474_TABLE_A3])


def _annex_a(probabilities: np.ndarray) -> environment.SelDistribution:
    return environment.sel_distribution(
        _LEVELS,
        probabilities,
        sigma_db=ref.ISO13474_ANNEX_A_SIGMA_DB,
        subclasses=ref.ISO13474_ANNEX_A_SUBCLASSES,
    )


def _table_a4(index: int) -> np.ndarray:
    return np.array([row[index] for row in ref.ISO13474_TABLE_A4])


def _cells_matching(computed: np.ndarray, printed: np.ndarray, places: int) -> int:
    """How many computed cells, rounded as the table prints them, are the cell."""
    return int(np.count_nonzero(np.round(computed, places) == printed))


@register(
    _ISO13474,
    "ISO 13474:2009 Equations (10) to (13), Table A.4",
    "Sorted levels and class boundaries of the 27 classes",
)
def _chk_table_a4_boundaries() -> Outcome:
    """The order of the classes and every boundary, from Table A.3 alone.

    Two pairs of classes share a level, 30,8 dB and 31,8 dB; Equation (11)
    puts their common boundary at that level and Table A.4 keeps both classes
    of each pair, in the order of Table A.3. The outer boundaries mirror the
    nearest inner one about the end level, Equations (12) and (13).
    """
    dist = _annex_a(_PERIOD)
    matching = (
        _cells_matching(dist.levels_db, _table_a4(1), 1)
        + _cells_matching(dist.lower_bounds_db, _table_a4(3), 2)
        + _cells_matching(dist.upper_bounds_db, _table_a4(4), 2)
    )
    return count(matching, 81, subject="levels and boundaries of Table A.4")


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (14), Table A.4",
    "Probability of each class over 07:00 to 19:00, sorted with its level",
)
def _chk_table_a4_probabilities() -> Outcome:
    """The probability column follows its class through the sort.

    The input is the day and night columns of Table A.3 at 80 % and 20 %, as
    the annex states; rounded to four decimals, the sorted column is Table
    A.4's.
    """
    dist = _annex_a(_PERIOD)
    matching = _cells_matching(dist.probabilities, _table_a4(2), 4)
    return count(matching, 27, subject="probabilities of Table A.4")


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (15), Table A.4",
    "Probability density of each class, in 1/dB",
)
def _chk_table_a4_densities() -> Outcome:
    """All 27 densities to the four printed decimals.

    The table divides the full-precision probability, not the rounded column
    beside it: 0,1860 / 0,15 would print 1,2400 where the table prints 1,2399,
    and 0,0042 / 0,25 would print 0,0168 where it prints 0,0170.
    """
    dist = _annex_a(_PERIOD)
    matching = _cells_matching(dist.class_densities_per_db, _table_a4(5), 4)
    return count(matching, 27, subject="densities of Table A.4")


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (7), Figure A.3",
    "Long-term average single-event level LT1 of the TOW launcher",
)
def _chk_lt1() -> Outcome:
    """Equation (7) with a single atmospheric-absorption class of probability 1."""
    value = environment.long_term_sel(_LEVELS, _PERIOD)
    return numeric(ref.ISO13474_FIGURE_A3_LT1_DB, value, 0.05, unit="dB", places=2)


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (A.4), Figure A.3",
    "Long-term level LT2 from the distribution spread with sigma = 5 dB",
)
def _chk_lt2() -> Outcome:
    """The long-term level taken again over the continuous density.

    The shift of Equation (22) keeps the energy of every subclass, so LT2
    differs from LT1 only by the spreading of each class over its width,
    about 0,05 dB here, and both print 37,0 dB. With the 1,04 dB the running
    text gives for the shift, every level would move up by 1,84 dB and LT2
    would read 38,8 dB.
    """
    value = _annex_a(_PERIOD).distribution_long_term_level_db
    return numeric(ref.ISO13474_FIGURE_A3_LT2_DB, value, 0.05, unit="dB", places=2)


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (22)",
    "Shift of the Gaussian subclasses at sigma = 5 dB, against the printed integral",
)
def _chk_level_shift() -> Outcome:
    """Equation (22) as printed, integrated numerically, against the closed form.

    The page gives no value of the equation it can be checked against: its
    one number, 1,04 dB, is the equation at 3 dB and not at the 5 dB of the
    same paragraph (see docs/ERRATA.md). The expected side is therefore the
    printed integral evaluated by quadrature, which shares nothing with the
    library's ``sigma**2 * ln(10) / 20``.
    """
    sigma = ref.ISO13474_ANNEX_A_SIGMA_DB
    ln10 = math.log(10.0)
    peak = 0.1 * ln10 * sigma * sigma
    integral, _ = integrate.quad(
        lambda x: math.exp(0.1 * ln10 * x - x * x / (2.0 * sigma * sigma)),
        peak - 40.0 * sigma,
        peak + 40.0 * sigma,
        points=[peak],
        limit=200,
        epsabs=0.0,
        epsrel=1e-13,
    )
    expected = 10.0 * math.log10(integral / (sigma * math.sqrt(2.0 * math.pi)))
    value = environment.turbulence_level_shift(sigma)
    return numeric(expected, value, 1e-9, unit="dB", places=9)


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (25), Figure A.3",
    "Level exceeded by 50 % of the events, L50",
)
def _chk_l50() -> Outcome:
    """The median of the spread distribution, the root of Equation (25) at 0,5."""
    value = float(_annex_a(_PERIOD).exceedance_level(50.0))
    return numeric(
        ref.ISO13474_FIGURE_A3_EXCEEDANCE_DB[50], value, 0.05, unit="dB", places=2
    )


@register(
    _ISO13474,
    "ISO 13474:2009 Equation (24), Figure A.3",
    "The five printed exceedance levels, with the curve accumulated from 15 dB",
)
def _chk_figure_a3_exceedance_levels() -> Outcome:
    """L95, L50, L10, L5 and L1 as Figure A.3 prints them.

    Solved exactly, Equation (25) gives 21,6 / 31,5 / 40,5 / 43,0 / 47,5 dB,
    and the figure prints 21,7 / 31,5 / 40,6 / 43,2 / 48,0 dB. The five are
    reproduced to the printed digit, with the 07:00 to 19:00 column as printed,
    when the cumulative curve is formed from the lower end of the plotted range
    rather than from minus infinity: 1 minus the integral of the density from
    15 dB to x. The probability below 15 dB, about 0,2 %, is then counted in
    every exceedance, which moves the rarest levels most, 0,5 dB at L1. The
    curve of Figure A.3 starts at 15 dB at exactly 1, which is what that
    reading draws. The row takes the exceedance from the library and the
    15 dB from the figure, and records each level's distance from the print.
    """
    dist = _annex_a(_PRINTED_PERIOD)
    floor = float(dist.exceedance(ref.ISO13474_FIGURE_A3_LOWER_LIMIT_DB))
    worst = 0.0
    for percent, printed in ref.ISO13474_FIGURE_A3_EXCEEDANCE_DB.items():
        target = percent / 100.0
        level = optimize.brentq(
            lambda x, p=target: 1.0 - (floor - float(dist.exceedance(x))) - p,
            ref.ISO13474_FIGURE_A3_LOWER_LIMIT_DB + 1e-6,
            100.0,
            xtol=1e-10,
        )
        worst = max(worst, abs(level - printed))
    return numeric(
        0.0,
        worst,
        0.05,
        unit="dB",
        places=3,
        expected_label="L95/L50/L10/L5/L1 = 21.7/31.5/40.6/43.2/48.0 dB (+/-0.05 dB)",
        computed_label=f"largest difference {worst:.3f} dB",
    )
