#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The conformance rule of IEC TC 29 (IEC 60942:2017 5.1.15, IEC 61672-1:2013 5.1.21).

A requirement is met when the measured deviation lies within the acceptance
limits AND the actual expanded uncertainty does not exceed the maximum
permitted, both limits inclusive. The two standards print the rule's worked
examples, eight in IEC 60942 Table E.1 (folio 52) and ten in IEC 61672-1
Table C.1 (folio 45), with the verdict and the reason for each; every one is
reproduced here, the boundary cases (example 6 and 7 of E.1, examples 3 and 7
of C.1) included.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import pytest
from reference_data import (
    IEC60942_TABLE_E1,
    IEC61260_1_TABLE_C1,
    IEC61672_1_TABLE_C1,
    TC29_REASONS,
)

from phonometry import metrology


@pytest.mark.parametrize(
    ("example", "deviation", "limit", "uncertainty", "maximum", "conforms", "outcome"),
    IEC60942_TABLE_E1,
    ids=[f"E.1-{row[0]}" for row in IEC60942_TABLE_E1],
)
def test_iec60942_table_e1(
    example: int,
    deviation: float,
    limit: float,
    uncertainty: float,
    maximum: float,
    conforms: bool,  # noqa: FBT001
    outcome: int,
) -> None:
    """Every example of Table E.1: verdict, outcome and printed reason."""
    result = metrology.verify_conformance(
        deviation,
        uncertainty=uncertainty,
        acceptance_limits=limit,
        max_uncertainty=maximum,
    )
    assert result.passes is conforms, f"example {example}"
    assert result.outcome == outcome
    assert result.reason == TC29_REASONS[outcome]


@pytest.mark.parametrize(
    ("example", "deviation", "limits", "uncertainty", "maximum", "conforms", "outcome"),
    IEC61672_1_TABLE_C1,
    ids=[f"C.1-{row[0]}" for row in IEC61672_1_TABLE_C1],
)
def test_iec61672_1_table_c1(
    example: int,
    deviation: float,
    limits: tuple[float, float],
    uncertainty: float,
    maximum: float,
    conforms: bool,  # noqa: FBT001
    outcome: int,
) -> None:
    """Every example of Table C.1, whose limits are asymmetric (+1,0; -1,2 dB)."""
    upper, lower = limits
    result = metrology.verify_conformance(
        deviation,
        uncertainty=uncertainty,
        acceptance_limits=(lower, upper),
        max_uncertainty=maximum,
    )
    assert result.passes is conforms, f"example {example}"
    assert result.outcome == outcome
    assert result.reason == TC29_REASONS[outcome]
    assert (result.lower_limit, result.upper_limit) == (lower, upper)


def test_a_symmetric_limit_bounds_the_absolute_deviation() -> None:
    """One number is +/- that number, so -0,25 dB conforms against 0,25 dB."""
    below = metrology.verify_conformance(
        -0.25, uncertainty=0.1, acceptance_limits=0.25, max_uncertainty=0.15
    )
    assert below.passes
    assert (below.lower_limit, below.upper_limit) == (-0.25, 0.25)


def test_both_criteria_are_inclusive_and_nothing_beyond() -> None:
    """On a limit conforms; a hundred-thousandth of a decibel past it does not."""
    on_both = metrology.verify_conformance(
        0.25, uncertainty=0.15, acceptance_limits=0.25, max_uncertainty=0.15
    )
    assert on_both.passes
    past_limit = metrology.verify_conformance(
        0.25001, uncertainty=0.15, acceptance_limits=0.25, max_uncertainty=0.15
    )
    assert not past_limit.passes
    assert past_limit.outcome == 3
    past_maximum = metrology.verify_conformance(
        0.25, uncertainty=0.15001, acceptance_limits=0.25, max_uncertainty=0.15
    )
    assert not past_maximum.passes
    assert past_maximum.outcome == 2


def test_a_sum_that_lands_on_the_limit_is_on_it() -> None:
    """0,1 + 0,2 is 0,300 000 000 000 000 04 in binary and still conforms."""
    deviation = 0.1 + 0.2
    assert deviation > 0.3
    result = metrology.verify_conformance(
        deviation, uncertainty=0.1, acceptance_limits=0.3, max_uncertainty=0.2
    )
    assert result.deviation_within_limits


def test_the_uncertainty_is_not_added_to_the_deviation() -> None:
    """Unlike ISO 8041-1 13.1, a deviation on the limit with a large U conforms.

    What the rule refuses is an uncertainty above the maximum, not the sum:
    0,25 dB measured with U = 0,15 dB against 0,25 dB and 0,15 dB conforms.
    """
    result = metrology.verify_conformance(
        0.25, uncertainty=0.15, acceptance_limits=0.25, max_uncertainty=0.15
    )
    assert result.passes


def test_the_shares_of_each_allowance() -> None:
    """The deviation is read against the limit on its own side."""
    result = metrology.verify_conformance(
        -0.6, uncertainty=0.3, acceptance_limits=(-1.2, 1.0), max_uncertainty=0.5
    )
    assert result.share_of_acceptance_limit == pytest.approx(0.5)
    assert result.share_of_max_uncertainty == pytest.approx(0.6)
    above = metrology.verify_conformance(
        0.5, uncertainty=0.3, acceptance_limits=(-1.2, 1.0), max_uncertainty=0.5
    )
    assert above.share_of_acceptance_limit == pytest.approx(0.5)


def test_a_deviation_past_a_limit_of_zero_has_no_finite_share() -> None:
    """A magnitude judged against (0, L) cannot be negative and conform."""
    result = metrology.verify_conformance(
        -0.1, uncertainty=0.1, acceptance_limits=(0.0, 3.0), max_uncertainty=0.5
    )
    assert not result.passes
    assert math.isinf(result.share_of_acceptance_limit)
    at_zero = metrology.verify_conformance(
        0.0, uncertainty=0.1, acceptance_limits=(0.0, 3.0), max_uncertainty=0.5
    )
    assert at_zero.share_of_acceptance_limit == 0.0


def test_the_verdict_object_has_no_truth_value() -> None:
    """``if verify_conformance(...):`` would pass everything; it raises instead."""
    result = metrology.verify_conformance(
        0.0, uncertainty=0.1, acceptance_limits=0.25, max_uncertainty=0.15
    )
    with pytest.raises(TypeError, match="ConformanceVerification has no truth value"):
        bool(result)


def test_the_verdict_is_derived_not_stored() -> None:
    """A hand-built result cannot claim a verdict its numbers do not give."""
    result = metrology.ConformanceVerification(
        deviation=0.3,
        uncertainty=0.1,
        lower_limit=-0.25,
        upper_limit=0.25,
        max_uncertainty=0.15,
    )
    assert not result.passes
    assert result.unit == "dB"


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"acceptance_limits": -0.25}, "acceptance_limits"),
        ({"acceptance_limits": (0.25, -0.25)}, "lower_limit"),
        ({"acceptance_limits": (0.1, 0.2, 0.3)}, "acceptance_limits"),
        ({"acceptance_limits": math.nan}, "acceptance_limits"),
        ({"uncertainty": -0.1}, "uncertainty"),
        ({"uncertainty": math.inf}, "uncertainty"),
        ({"max_uncertainty": 0.0}, "max_uncertainty"),
    ],
)
def test_inputs_the_rule_cannot_be_read_on(
    kwargs: dict[str, object], fragment: str
) -> None:
    arguments: dict[str, object] = {
        "uncertainty": 0.1,
        "acceptance_limits": 0.25,
        "max_uncertainty": 0.15,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=fragment):
        metrology.verify_conformance(0.0, **arguments)  # type: ignore[arg-type]


def test_a_non_finite_deviation_is_refused() -> None:
    with pytest.raises(ValueError, match="'deviation' must be finite"):
        metrology.verify_conformance(
            math.nan, uncertainty=0.1, acceptance_limits=0.25, max_uncertainty=0.15
        )


# --------------------------------------------------------------------------
# The figure
# --------------------------------------------------------------------------
def _marker_lines(ax: plt.Axes, marker: str) -> list[object]:
    return [line for line in ax.lines if line.get_marker() == marker]


def test_plot_draws_limits_band_error_bar_and_verdict() -> None:
    """Figure E.1 for one example: the band spans +/-Umax about the deviation."""
    result = metrology.verify_conformance(
        -0.6, uncertainty=0.3, acceptance_limits=(-1.2, 1.0), max_uncertainty=0.5
    )
    ax = result.plot()
    limits = sorted(
        line.get_ydata()[0]
        for line in ax.lines
        if line.get_marker() in ("None", "", None) and len(line.get_ydata()) == 2
    )
    assert limits == pytest.approx([-1.2, 1.0])
    diamonds = _marker_lines(ax, "D")
    assert len(diamonds) == 1
    assert diamonds[0].get_ydata()[0] == pytest.approx(-0.6)
    band = [p for p in ax.patches if p.get_height() == pytest.approx(1.0)]
    assert band, "the maximum-permitted band is 2 x 0,5 dB tall"
    assert band[0].get_y() == pytest.approx(-1.1)
    assert "conforms" in ax.get_title()
    plt.close("all")


def test_plot_marks_a_failure_with_a_cross() -> None:
    result = metrology.verify_conformance(
        0.40, uncertainty=0.50, acceptance_limits=0.25, max_uncertainty=0.20
    )
    ax = result.plot()
    assert len(_marker_lines(ax, "X")) == 1
    assert not _marker_lines(ax, "D")
    assert ax.get_title().endswith("does not conform")
    plt.close("all")


def test_plot_in_spanish_and_a_bad_language() -> None:
    result = metrology.verify_conformance(
        0.0, uncertainty=0.1, acceptance_limits=0.25, max_uncertainty=0.15
    )
    ax = result.plot(language="es")
    assert ax.get_title() == "Regla de conformidad del IEC TC 29: conforme"
    assert ax.get_ylabel() == "Desviación respecto al objetivo de diseño [dB]"
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Incertidumbre máxima permitida" in labels
    plt.close("all")
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")


# --------------------------------------------------------------------------
# IEC 61260-1:2014 Table C.1 and the intervals open on one side
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("example", "deviation", "limits", "uncertainty", "maximum", "conforms", "outcome"),
    IEC61260_1_TABLE_C1,
    ids=[f"61260-C.1-{row[0]}" for row in IEC61260_1_TABLE_C1],
)
def test_iec61260_1_table_c1(
    example: int,
    deviation: float,
    limits: tuple[float, float],
    uncertainty: float,
    maximum: float,
    conforms: bool,  # noqa: FBT001
    outcome: int,
) -> None:
    """IEC 61260-1:2014 Table C.1 (folio 31) prints the ten examples again."""
    upper, lower = limits
    result = metrology.verify_conformance(
        deviation,
        uncertainty=uncertainty,
        acceptance_limits=(lower, upper),
        max_uncertainty=maximum,
    )
    assert result.passes is conforms, example
    assert result.outcome == outcome, example
    assert result.reason == TC29_REASONS[outcome], example


def test_a_stop_band_minimum_is_an_interval_open_above() -> None:
    """IEC 61260-1 Table 1 prints "+70; +inf": a minimum and no maximum."""
    deep = metrology.verify_conformance(
        75.0, uncertainty=0.4, acceptance_limits=(70.0, math.inf), max_uncertainty=0.5
    )
    shallow = metrology.verify_conformance(
        65.0, uncertainty=0.4, acceptance_limits=(70.0, math.inf), max_uncertainty=0.5
    )
    assert deep.passes
    assert deep.upper_limit == math.inf
    assert deep.share_of_acceptance_limit == 0.0
    assert not shallow.passes
    assert shallow.outcome == 3
    assert shallow.share_of_acceptance_limit == math.inf


def test_an_interval_open_below_bounds_the_top_only() -> None:
    """A level that shall not exceed a stated limit, and nothing more."""
    result = metrology.verify_conformance(
        -12.0, uncertainty=0.1, acceptance_limits=(-math.inf, 0.0), max_uncertainty=0.2
    )
    assert result.passes
    assert result.lower_limit == -math.inf


@pytest.mark.parametrize(
    ("limits", "fragment"),
    [
        ((-math.inf, math.inf), "both open"),
        ((math.inf, 80.0), "acceptance_limits"),
        ((10.0, -math.inf), "acceptance_limits"),
        ((math.nan, 1.0), "acceptance_limits"),
    ],
)
def test_an_interval_open_the_wrong_way_is_refused(
    limits: tuple[float, float], fragment: str
) -> None:
    with pytest.raises(ValueError, match=fragment):
        metrology.verify_conformance(
            0.0, uncertainty=0.1, acceptance_limits=limits, max_uncertainty=0.2
        )


def test_a_symmetric_limit_stays_finite() -> None:
    with pytest.raises(ValueError, match="'acceptance_limits' must be finite"):
        metrology.verify_conformance(
            0.0, uncertainty=0.1, acceptance_limits=math.inf, max_uncertainty=0.2
        )


def test_an_open_interval_plots_its_finite_limit_only() -> None:
    result = metrology.verify_conformance(
        75.0, uncertainty=0.4, acceptance_limits=(70.0, math.inf), max_uncertainty=0.5
    )
    ax = result.plot()
    low, high = ax.get_ylim()
    assert math.isfinite(low)
    assert math.isfinite(high)
    assert low < 70.0 < 75.0 < high
    plt.close("all")
