#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Band-filter tests: pattern evaluation (IEC 61260-2) and periodic tests (IEC 61260-3).

Four things are pinned here.

The printed numbers of the two test standards. IEC 61260-3:2016 Table C.1
lists the fifteen normalized test frequencies of a one-third-octave filter to
five decimals, and C.2 derives the first of them (Omega_1 ~ 1,026 67 and its
inverse 0,974 02); Table 1 gives the acceptance limits the periodic test
reads at them. Both parts print the same two worked examples in their
Annexes A and B: the level an exponential sweep leaves at the output of a
one-third-octave filter, L_c = 127 dB - 19,03 dB = 107,97 dB (B.5), and the
uncertainty of that level, u ~ 0,057 dB, 0,115 dB expanded and 0,128 dB with a
0,1 dB display (A.3.5). The last reproduces only with the square that the
printed Formula (A.2) leaves off its frequency terms (see the errata
registry).

The conformance rule of IEC 61260-1:2014, whose Table C.1 prints ten worked
examples (the same ten IEC 61672-1:2013 prints), verdict and reason each.

Formulas (2) and (3) of IEC 61260-2, which come with no example: they are
anchored in closed form. An ideal band, flat inside, silent outside and at
half power on its edges, has an effective bandwidth that Formula (2) sums to
tanh(x/2)/(x/2) of the reference one, x = ln G / (bS), so its deviation is
-(10 lg e) x^2/12 to leading order, 3e-4 dB for octaves; and an ideal bank's
summed outputs restore the input exactly, inside a band and on its edges.

The design verdict the library gives on its own one-third-octave bank for the
two requirements Formulas (2) and (3) test (IEC 61260-1:2014 5.12 and 5.16),
and for time-invariant operation (5.14): the swept test runs the multirate
bank itself, and reads each band's effective bandwidth deviation, as Annex G
(G.2.8) says a time-invariant filter does.

Oracles read on the rasterized pages: IEC 61260-3:2016 (PDF page = folio + 2)
Table 1 (folio 13), A.3.5 (18), B.2 (19-20), C.2 and Table C.1 (21-22); IEC
61260-2:2016 (PDF page = folio + 2) Formulas (1) to (3) (10-11), A.3.5 (21),
B.2 (22-23); BS EN 61260-1:2014 (PDF page = folio + 2) Table C.1 (31).
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref

import phonometry as ph
from phonometry.filters.compliance import (
    _G,
    _effective_bandwidth,
    _reference_bandwidth,
    _summation_deviation,
    _test_frequencies,
)

from ..registry import Outcome, count, numeric, record, register, residue_text

_FILTER_TESTS = (
    "Band-filter pattern evaluation and periodic tests (IEC 61260-2, IEC 61260-3)"
)

_VERDICT = {True: "Yes", False: "No"}

#: Where a test frequency lies, which keeps apart the rows of k and -k: the
#: check id is a slug of the quantity, and a slug drops the sign.
_SIDE = {-1: "below the mid-band", 0: "at the mid-band", 1: "above the mid-band"}

#: 10 lg 2 dB: an ideal band at its edge, sharing a tone with its neighbour.
_HALF_POWER_DB = 10.0 * math.log10(2.0)


# --------------------------------------------------------------------------
# IEC 61260-3:2016 Table C.1 and Table 1
# --------------------------------------------------------------------------
def _register_table_c1() -> None:
    """One row per printed normalized test frequency, k = -7 .. 7."""
    omega = ph.filters.periodic_test_frequencies(3)
    for k, (printed, _, _) in ref.IEC61260_3_TABLE_C1.items():

        def check(k: int = k, printed: float = printed) -> Outcome:
            return numeric(printed, float(omega[k + 7]), 5e-6, places=5)

        source = (
            "IEC 61260-3:2016 Table C.1, C.2"
            if abs(k) == 1
            else "IEC 61260-3:2016 Table C.1"
        )
        k_label = "0" if k == 0 else f"{k:+d}"
        register(
            _FILTER_TESTS,
            source,
            f"One-third-octave test frequency Omega_k, k = {k_label} "
            f"({_SIDE[(k > 0) - (k < 0)]}, Formulas (1), (2))",
        )(check)


_register_table_c1()


@register(
    _FILTER_TESTS,
    "IEC 61260-3:2016 Table 1",
    "Acceptance limits on relative attenuation, 8 frequency parameters x 2 classes",
)
def _chk_periodic_table_1() -> Outcome:
    matching = total = 0
    for k, (_, class1, class2) in ref.IEC61260_3_TABLE_1.items():
        for cls, printed in ((1, class1), (2, class2)):
            lower, upper = ph.filters.PERIODIC_TEST_ATTENUATION_LIMITS_DB[cls][k]
            page_upper = math.inf if printed[1] is None else printed[1]
            matching += (lower == printed[0]) + (upper == page_upper)
            total += 2
    return count(matching, total, subject="cells")


# --------------------------------------------------------------------------
# IEC 61260-1:2014 Table C.1: the conformance rule
# --------------------------------------------------------------------------
def _register_61260_1_table_c1() -> None:
    """One row per example of IEC 61260-1:2014 Table C.1."""
    for example, deviation, (
        upper,
        lower,
    ), uncertainty, maximum, conforms, outcome in ref.IEC61260_1_TABLE_C1:

        def check(
            deviation: float = deviation,
            lower: float = lower,
            upper: float = upper,
            uncertainty: float = uncertainty,
            maximum: float = maximum,
            conforms: bool = conforms,  # noqa: FBT001
            outcome: int = outcome,
        ) -> Outcome:
            result = ph.metrology.verify_conformance(
                deviation,
                uncertainty=uncertainty,
                acceptance_limits=(lower, upper),
                max_uncertainty=maximum,
            )
            expected = {
                "conforms": float(conforms),
                "outcome": float(outcome),
                "reason": 1.0,
            }
            computed = {
                "conforms": float(result.passes),
                "outcome": float(result.outcome),
                "reason": float(result.reason == ref.TC29_REASONS[outcome]),
            }
            return record(
                expected,
                computed,
                label=f"{_VERDICT[conforms]}: {ref.TC29_REASONS[outcome]}",
                computed_label=f"{_VERDICT[result.passes]}: {result.reason}",
            )

        register(
            _FILTER_TESTS,
            "IEC 61260-1:2014 Table C.1",
            f"Example {example}: deviation {deviation:+.1f} dB, U {uncertainty:.1f} dB "
            f"against +{upper:.1f}; {lower:.1f} dB and {maximum:.1f} dB",
        )(check)


_register_61260_1_table_c1()


# --------------------------------------------------------------------------
# Annexes A and B of IEC 61260-2 and -3: the swept test
# --------------------------------------------------------------------------
@register(
    _FILTER_TESTS,
    "IEC 61260-2:2016 / IEC 61260-3:2016 Annex B, Formula (B.5)",
    "Swept output level L_c of a one-third-octave filter (Formula (17) of IEC 61260-1)",
)
def _chk_annex_b() -> Outcome:
    example = ref.IEC61260_B5
    level = ph.filters.swept_band_level(
        example["input_level_db"],
        fraction=example["fraction"],
        sweep_duration_s=example["sweep_duration_s"],
        averaging_time_s=example["averaging_time_s"],
        start_frequency_hz=example["start_frequency_hz"],
        end_frequency_hz=example["end_frequency_hz"],
    )
    return numeric(example["expected_level_db"], level, 0.005, unit="dB", places=2)


def _a35(*, display: bool) -> float:
    inputs = ref.IEC61260_A35_INPUTS
    u_in = math.hypot(
        inputs["level_resolution_db"] / (2.0 * math.sqrt(3.0)),
        inputs["level_constancy_db"],
    )
    return ph.filters.swept_level_uncertainty(
        input_level_uncertainty_db=u_in,
        sweep_duration_s=inputs["sweep_duration_s"],
        sweep_duration_uncertainty_s=inputs["sweep_duration_uncertainty_s"],
        averaging_time_s=inputs["averaging_time_s"],
        averaging_time_uncertainty_s=inputs["averaging_time_uncertainty_s"],
        start_frequency_hz=inputs["start_frequency_hz"],
        start_frequency_uncertainty_hz=inputs["start_frequency_uncertainty_hz"],
        end_frequency_hz=inputs["end_frequency_hz"],
        end_frequency_uncertainty_hz=inputs["end_frequency_uncertainty_hz"],
        display_resolution_db=inputs["display_resolution_db"] if display else 0.0,
    )


@register(
    _FILTER_TESTS,
    "IEC 61260-2:2016 / IEC 61260-3:2016 A.3.5, Formula (A.2)",
    "Standard uncertainty u_Lc of the swept output level",
)
def _chk_annex_a_standard() -> Outcome:
    return numeric(
        ref.IEC61260_A35_PRINTED["u_lc_db"],
        _a35(display=False),
        0.0005,
        unit="dB",
        places=3,
    )


@register(
    _FILTER_TESTS,
    "IEC 61260-2:2016 / IEC 61260-3:2016 A.3.5",
    "Expanded uncertainty of the test signal (k = 2)",
)
def _chk_annex_a_expanded() -> Outcome:
    return numeric(
        ref.IEC61260_A35_PRINTED["expanded_db"],
        2.0 * _a35(display=False),
        0.0005,
        unit="dB",
        places=3,
    )


@register(
    _FILTER_TESTS,
    "IEC 61260-2:2016 / IEC 61260-3:2016 A.3.5",
    "Expanded uncertainty read on a 0.1 dB display (k = 2)",
)
def _chk_annex_a_display() -> Outcome:
    return numeric(
        ref.IEC61260_A35_PRINTED["expanded_with_display_db"],
        2.0 * _a35(display=True),
        0.0005,
        unit="dB",
        places=3,
    )


# --------------------------------------------------------------------------
# Formulas (2) and (3) of IEC 61260-2, in closed form
# --------------------------------------------------------------------------
@register(
    _FILTER_TESTS,
    "IEC 61260-2:2016 Formula (2) / IEC 61260-1:2014 Formulas (15), (16)",
    "Ideal octave band: Delta B = 10 lg(tanh(x/2)/(x/2)), x = ln G / (bS), S = 24 (closed form)",
)
def _chk_ideal_bandwidth() -> Outcome:
    fraction, points = 1, 24
    n = 2 * points
    omega = _test_frequencies(fraction, points, -n, n + 1)
    half = points // 2
    delta_a = [
        0.0 if abs(i) < half else (_HALF_POWER_DB if abs(i) == half else math.inf)
        for i in range(-n, n + 2)
    ]
    b_e = _effective_bandwidth(omega, np.asarray(delta_a))
    computed = 10.0 * math.log10(b_e / _reference_bandwidth(fraction))
    x = math.log(_G) / (fraction * points)
    expected = 10.0 * math.log10(math.tanh(x / 2.0) / (x / 2.0))
    return numeric(expected, computed, 1e-12, unit="dB", places=6)


@register(
    _FILTER_TESTS,
    "IEC 61260-2:2016 Formula (3)",
    "Ideal bank: summed outputs restore the input inside a band and on its edges (closed form)",
)
def _chk_ideal_summation() -> Outcome:
    inside = _summation_deviation(np.array([[math.inf], [0.0], [math.inf]]))[0]
    edge = _summation_deviation(
        np.array([[math.inf], [_HALF_POWER_DB], [_HALF_POWER_DB]])
    )[0]
    return numeric(
        0.0,
        max(abs(inside), abs(edge)),
        1e-12,
        unit="dB",
        places=6,
        computed_label=(
            f"max |Delta P| {residue_text(max(abs(inside), abs(edge)), 'dB', '.1e')}"
        ),
    )


# --------------------------------------------------------------------------
# The design verdicts on the library's one-third-octave bank
# --------------------------------------------------------------------------
def _third_octave_bank() -> ph.filters.OctaveFilterBank:
    return ph.filters.OctaveFilterBank(48000, fraction=3, order=6, limits=[100, 10000])


@register(
    _FILTER_TESTS,
    "IEC 61260-1:2014 5.12.2 / IEC 61260-2:2016 7.2.3",
    "One-third-octave Butterworth bank (fs=48 kHz): largest |Delta B| within the class 1 +/-0.4 dB",
)
def _chk_bank_bandwidth() -> Outcome:
    result = ph.filters.verify_filter_class(_third_octave_bank())
    worst = max(abs(b["bandwidth_deviation_db"]) for b in result.bands)
    margin = result.binding_margin_db("effective_bandwidth", 1)
    return Outcome(
        expected="class 1 (|Delta B| <= 0.4 dB)",
        computed=f"class {result.requirement_class('effective_bandwidth')} "
        f"(|Delta B| <= {worst:.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=result.requirement_class("effective_bandwidth") == 1,
    )


@register(
    _FILTER_TESTS,
    "IEC 61260-1:2014 5.16 / IEC 61260-2:2016 7.2.4",
    "One-third-octave Butterworth bank (fs=48 kHz): summed outputs within the class 1 +0.8/-1.8 dB",
)
def _chk_bank_summation() -> Outcome:
    result = ph.filters.verify_filter_class(_third_octave_bank())
    inner = [b for b in result.bands if b["summation_min_db"] is not None]
    low = min(b["summation_min_db"] for b in inner)
    high = max(b["summation_max_db"] for b in inner)
    margin = result.binding_margin_db("summation", 1)
    return Outcome(
        expected="class 1 (-1.8 dB <= Delta P <= +0.8 dB)",
        computed=f"class {result.requirement_class('summation')} "
        f"({low:+.3f} dB to {high:+.3f} dB)",
        delta=f"{margin:+.3f} dB",
        passed=result.requirement_class("summation") == 1,
    )


@register(
    _FILTER_TESTS,
    "IEC 61260-1:2014 5.14.3 / IEC 61260-2:2016 7.4",
    "One-third-octave multirate bank swept at 2 and 5 s per decade: |L_out - L_c| within class 1 +/-0.4 dB",
)
def _chk_bank_time_invariance() -> Outcome:
    result = ph.filters.verify_time_invariance(_third_octave_bank())
    worst = abs(result.worst_deviation_db)
    return Outcome(
        expected="class 1 (|L_out - L_c| <= 0.4 dB)",
        computed=f"class {result.overall_class} (|L_out - L_c| <= {worst:.3f} dB)",
        delta=f"{0.4 - worst:+.3f} dB",
        passed=result.overall_class == 1,
    )


@register(
    _FILTER_TESTS,
    "IEC 61260-1:2014 Annex G, G.2.8",
    "Swept deviation of a time-invariant band equals its effective bandwidth deviation",
)
def _chk_annex_g() -> Outcome:
    bank = _third_octave_bank()
    swept = ph.filters.verify_time_invariance(bank)
    design = ph.filters.verify_filter_class(bank)
    delta_b = np.array([b["bandwidth_deviation_db"] for b in design.bands])
    worst = float(np.max(np.abs(swept.deviations_db - delta_b)))
    return numeric(
        0.0,
        worst,
        0.01,
        unit="dB",
        places=4,
        computed_label=f"max |(L_out - L_c) - Delta B| {worst:.4f} dB",
    )
