#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Airborne noise of steam turbine sets: IEC 61063:1991.

IEC 61063 is a noise test code built on the survey method of ISO 3746. It
prints no worked example, and nothing in it can be recomputed from an input it
also prints, so its oracles are the numbers it fixes, read on the printed page
of BS EN 61063:1996, the English text of EN 61063:1996, which is IEC 1063:1991
without modification:

* **Table 2**, printed folio 8 (PDF page 14): the stepped correction for
  background noise, nine rows from 3 dB to "> 10";
* **Table 1**, printed folio 4 (PDF page 10): the standard deviations of the
  survey method, 5 dB with prominent discrete tones and 4 dB without;
* **7.1**, printed folio 7 (PDF page 13): the measurement distance of 1 m,
  and Equation (1) for the area of the stepped measurement surface;
* **Figure A.3**, printed folio 12 (PDF page 18), with **A.3.3** on folios 12
  and 13: the environmental correction, its 7 dB limit and the A/S of 1 the
  clause restates the limit as;
* the NOTE of **8.3**, printed folio 9 (PDF page 15): an arithmetic average
  within 0,7 dB of Equation (2) when the levels span no more than 5 dB;
* the limits of **4.2**, **4.3** and the NOTE of **7.2.2**, on folios 5, 6
  and 8.

Where the page prints a relation rather than a value (Equation (1), the
restatement of A.3.3, the NOTE of 8.3) the row judges the library's output
against a closed form written out here, never against the library itself.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from reference_data import steam_turbines as oracle

from phonometry import emission

from ..registry import Outcome, numeric, record, register

_TURBINES = "Steam turbine sets (IEC 61063)"

#: The large set of Figure 2 b, in reference boxes: HP and IP casings in one
#: box, the LP turbine in its own, then the generator and the exciter. Their
#: cross-sections shrink from the LP box towards both ends, as drawn.
_LARGE_SET = (
    (6.0, 4.0, 3.5),
    (5.0, 5.0, 4.5),
    (7.0, 3.5, 3.0),
    (3.0, 2.5, 2.2),
)


@register(
    _TURBINES,
    "IEC 61063:1991 Table 2 (BS EN 61063:1996, printed folio 8, PDF page 14)",
    "Correction for background noise, the nine printed rows from a difference "
    "of 3 dB to one above 10 dB",
)
def _chk_table_two() -> Outcome:
    """Every row of the stepped table, read at the difference it is printed at.

    The row "> 10" is read twice: at 11 dB, the first whole decibel above 10,
    and at 10,2 dB, which is above 10 dB as measured and would round down to
    the row 10 if the table were rounded before its open row was judged.
    """
    printed = {
        (f"{d} dB" if d <= 10 else "> 10 dB, at 11 dB"): value
        for d, value in oracle.IEC61063_TABLE_2_DB.items()
    }
    computed = {
        (f"{d} dB" if d <= 10 else "> 10 dB, at 11 dB"): float(
            emission.turbine_background_correction(float(d))
        )
        for d in oracle.IEC61063_TABLE_2_DB
    }
    printed["> 10 dB, at 10,2 dB"] = oracle.IEC61063_TABLE_2_DB[11]
    computed["> 10 dB, at 10,2 dB"] = float(
        emission.turbine_background_correction(10.2)
    )
    return record(printed, computed, unit="dB")


@register(
    _TURBINES,
    "IEC 61063:1991 Table 1 (BS EN 61063:1996, printed folio 4, PDF page 10)",
    "Standard deviation of the A-weighted sound power level by the survey "
    "method, with and without prominent discrete tones",
)
def _chk_table_one() -> Outcome:
    """The two rows of Table 1, as the report of clause 10 carries them."""
    levels = np.array([90.0, 91.0, 92.0, 91.5, 90.5])
    result = emission.turbine_sound_power(
        levels,
        surface_area_m2=100.0,
        background_levels_db=None,
        environmental_correction_db=0.0,
    )
    computed = {
        kind: emission.turbine_noise_declaration(
            {"rated load": result},
            turbine="set",
            noise_control="none",
            measured_at="now",
            tonal=kind == "tonal",
        ).standard_deviation_db
        for kind in oracle.IEC61063_TABLE_1_DB
    }
    return record(oracle.IEC61063_TABLE_1_DB, computed, unit="dB")


@register(
    _TURBINES,
    "IEC 61063:1991 7.1 (BS EN 61063:1996, printed folio 7, PDF page 13)",
    "The measurement surface stands 1 m from the reference box on every side "
    "but the floor",
)
def _chk_measurement_distance() -> Outcome:
    """A single box grows by d at each end, on each side and on top."""
    box = emission.TurbineReferenceBox(8.0, 3.0, 2.5)
    surface = emission.turbine_measurement_surface([box])
    d = oracle.IEC61063_MEASUREMENT_DISTANCE_M
    printed = {"length": 2.0 * d, "width": 2.0 * d, "height": d}
    computed = {
        "length": float(surface.lengths_m[0]) - box.length_m,
        "width": float(surface.widths_m[0]) - box.width_m,
        "height": float(surface.heights_m[0]) - box.height_m,
    }
    return record(printed, computed, unit="m")


@register(
    _TURBINES,
    "IEC 61063:1991 Equation (1) (BS EN 61063:1996, printed folio 7, PDF page 13)",
    "Area of the measurement surface around the large set of Figure 2 b "
    "against the exact area of the stepped surface",
)
def _chk_equation_one() -> Outcome:
    """Equation (1) is the exact area when the sections nest, as drawn.

    The expected value is the area of the stepped surface summed face by face
    here: the tops and long sides of the four parallelepipeds, the two ends,
    and at each step the part of the larger section the smaller one leaves
    uncovered.
    """
    d = oracle.IEC61063_MEASUREMENT_DISTANCE_M
    lengths = [box[0] for box in _LARGE_SET]
    lengths[0] += d
    lengths[-1] += d
    widths = [box[1] + 2.0 * d for box in _LARGE_SET]
    heights = [box[2] + d for box in _LARGE_SET]
    faces = sum(
        length * (2.0 * height + width)
        for length, width, height in zip(lengths, widths, heights, strict=True)
    )
    ends = widths[0] * heights[0] + widths[-1] * heights[-1]
    steps = sum(
        abs(widths[i] * heights[i] - widths[i + 1] * heights[i + 1])
        for i in range(len(widths) - 1)
    )
    surface = emission.turbine_measurement_surface(
        [emission.TurbineReferenceBox(*box) for box in _LARGE_SET]
    )
    return numeric(faces + ends + steps, surface.area_m2, 1e-9, unit="m2", places=3)


@register(
    _TURBINES,
    "IEC 61063:1991 Figure A.3 (BS EN 61063:1996, printed folio 12, PDF page 18)",
    "The environmental correction against the formula the figure prints, "
    "K = 10 lg[1 + 4/(A/S)], across the A/S it labels",
)
def _chk_figure_a3() -> Outcome:
    """K from the room absorption against the printed formula, written out here.

    At the A/S values the figure labels on its axis, 0,5 to 300, and at 2 and
    7,32 (the hall of the guide). A factor other than the printed 4 moves K
    by tenths of a decibel at every one of them.
    """
    surface = 100.0
    ratios = (0.5, 1.0, 2.0, 5.0, 7.32, 10.0, 50.0, 100.0, 300.0)
    worst = max(
        abs(
            emission.turbine_environmental_correction(
                surface, absorption_area_m2=ratio * surface
            ).environmental_correction_db
            - 10.0 * math.log10(1.0 + 4.0 / ratio)
        )
        for ratio in ratios
    )
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="dB",
        places=3,
        expected_label="max abs(K - 10 lg[1 + 4/(A/S)]) <= 1e-9 dB at 9 values of A/S",
    )


@register(
    _TURBINES,
    "IEC 61063:1991 Figure A.3 against A.3.3 (BS EN 61063:1996, printed folios "
    "12 and 13, PDF pages 18 and 19)",
    "The A/S at which the environmental correction reaches the 7 dB limit, "
    "against the A/S of 1 the clause restates the limit as",
)
def _chk_ratio_at_limit() -> Outcome:
    """Bisect the library's Figure A.3 for K = 7 dB and compare with A/S = 1.

    A.3.3 prints the requirement "K ≤ 7" and restates it as "A/S ≥ 1". The
    two agree to the whole unit the restatement is printed in: the curve of
    Figure A.3 reaches 7 dB at an A/S of 0,997, and at A/S = 1 it gives
    10 lg 5 = 6,99 dB. The tolerance is half the last printed digit of the 1.
    """
    surface = 100.0
    low, high = 0.5, 2.0
    for _ in range(60):
        middle = 0.5 * (low + high)
        k = emission.turbine_environmental_correction(
            surface, absorption_area_m2=middle * surface
        ).environmental_correction_db
        if k > oracle.IEC61063_K_LIMIT_DB:
            low = middle
        else:
            high = middle
    return numeric(oracle.IEC61063_MINIMUM_RATIO, high, 0.5, places=4)


@register(
    _TURBINES,
    "IEC 61063:1991 8.3 NOTE (BS EN 61063:1996, printed folio 9, PDF page 15)",
    "Largest gap between the arithmetic average and Equation (2) for levels "
    "spanning 5 dB",
)
def _chk_arithmetic_note() -> Outcome:
    """The worst set of levels within the 5 dB the NOTE allows.

    For a fixed range the energy average leads the arithmetic one most when
    every level sits at one end of the range or the other, so the largest gap
    is found over sets of 1000 positions split between the two ends. It comes
    to 0,707 dB, which the NOTE prints to one decimal; the tolerance is half
    that decimal.
    """
    worst = 0.0
    span = oracle.IEC61063_ARITHMETIC_RANGE_DB
    for louder in range(1, 1000, 7):
        levels = np.r_[np.full(louder, 90.0 + span), np.full(1000 - louder, 90.0)]
        result = emission.turbine_sound_power(
            levels,
            surface_area_m2=100.0,
            background_levels_db=None,
            environmental_correction_db=0.0,
        )
        worst = max(worst, result.surface_pressure_level_db - result.arithmetic_mean_db)
    return numeric(
        oracle.IEC61063_ARITHMETIC_DEVIATION_DB, worst, 0.05, unit="dB", places=3
    )


@register(
    _TURBINES,
    "IEC 61063:1991 4.2, 4.3, 7.2.2 and A.3.3 (BS EN 61063:1996, printed folios "
    "5, 6, 8 and 12)",
    "The background, wind, overhead and environmental limits, judged at the "
    "printed value and just past it",
)
def _chk_printed_limits() -> Outcome:
    """Each limit holds at the printed number and fails a hair beyond it.

    4.2: a background exactly 3 dB below is not an upper limit, 2,99 dB is.
    4.3: 5,99 m/s is within the wind limit, 6 m/s is not. A.3.3: K = 7 dB
    qualifies, a little more does not. 7.2.2: overhead positions that move the
    level by 1,0 dB may be deleted, and by a micro-decibel more may not. The
    effect is the difference of two energy means near 80 dB, so at 1,0 dB it
    comes out a unit or two of their last place either side of the printed
    value, which side depending on the machine; the row asks that it be judged
    on the limit whichever side it lands.
    """
    tiny = 1e-6
    levels = np.full(5, 90.0)

    def upper(margin_db: float) -> bool:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", emission.SoundPowerWarning)
            return emission.turbine_sound_power(
                levels,
                surface_area_m2=100.0,
                background_levels_db=levels - margin_db,
                environmental_correction_db=0.0,
            ).upper_limit

    def overhead(level_db: float) -> emission.TurbineSoundPowerResult:
        # Four positions at 80 dB and one overhead position.
        return emission.turbine_sound_power(
            np.array([80.0, 80.0, 80.0, 80.0, level_db]),
            surface_area_m2=100.0,
            background_levels_db=None,
            environmental_correction_db=0.0,
            overhead_mask=np.array([False, False, False, False, True]),
        )

    def at_effect(effect_db: float) -> float:
        # The closed form: the overhead level that moves four at 80 dB by
        # effect_db, 80 + 10 lg(5 x 10^(effect/10) - 4) dB.
        return 80.0 + 10.0 * math.log10(5.0 * 10.0 ** (effect_db / 10.0) - 4.0)

    criterion = oracle.IEC61063_BACKGROUND_CRITERION_DB
    wind = oracle.IEC61063_WIND_LIMIT_M_S
    k = oracle.IEC61063_K_LIMIT_DB
    effect = oracle.IEC61063_OVERHEAD_EFFECT_DB
    check = emission.check_turbine_test_environment
    exact = overhead(at_effect(effect))
    beyond = overhead(at_effect(effect + tiny))
    judged = {
        "4.2 at 3 dB": not upper(criterion),
        "4.2 below 3 dB": upper(criterion - 0.01),
        "4.3 below 6 m/s": bool(
            check(environmental_correction_db=0.0, wind_speed_m_s=wind - 0.01).wind_ok
        ),
        "4.3 at 6 m/s": not check(
            environmental_correction_db=0.0, wind_speed_m_s=wind
        ).wind_ok,
        "A.3.3 at 7 dB": check(environmental_correction_db=k).passes,
        "A.3.3 above 7 dB": not check(environmental_correction_db=k + tiny).passes,
        "7.2.2 at 1,0 dB": exact.overhead_effect_db is not None
        and math.isclose(exact.overhead_effect_db, effect, rel_tol=0.0, abs_tol=1e-12)
        and bool(exact.overhead_may_be_deleted),
        "7.2.2 above 1,0 dB": not beyond.overhead_may_be_deleted,
    }
    printed = dict.fromkeys(judged, 1.0)
    return record(
        printed,
        {name: float(held) for name, held in judged.items()},
        label="every limit holds at the printed value and fails past it",
    )
