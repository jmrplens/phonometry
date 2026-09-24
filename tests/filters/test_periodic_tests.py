#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61260-3:2016: the test frequencies of Clause 13 and the verdict.

The test frequencies are held to Table C.1 and the derivation of C.2; the
verdict to the conformance rule of IEC TC 29 with the acceptance limits of
IEC 61260-3 and the maximum-permitted uncertainties of IEC 61260-1:2014
Annex B, clause by clause, and to the statements of Clause 14.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import filters

_NAN = math.nan

#: A clause 13 row that conforms to class 1, k = -7 .. 7, and its uncertainties.
_ROW = [
    75.0,
    62.0,
    45.0,
    20.0,
    0.8,
    0.3,
    0.1,
    0.0,
    0.1,
    0.2,
    0.7,
    19.0,
    44.0,
    63.0,
    76.0,
]
_ROW_U = [
    0.4,
    0.4,
    0.4,
    0.25,
    0.15,
    0.15,
    0.15,
    0.15,
    0.15,
    0.15,
    0.15,
    0.25,
    0.4,
    0.4,
    0.4,
]


def _record(**overrides: object) -> filters.FilterPeriodicMeasurements:
    """A complete record that conforms to class 1, with fields replaced."""
    fields: dict[str, object] = {
        "midband_attenuations_db": [0.1, -0.2, 0.05],
        "midband_uncertainties_db": [0.15, 0.15, 0.15],
        "set_midband_frequencies_hz": [500.0, 1000.0, 2000.0],
        "linearity_deviations_db": [0.1, 0.2, 0.3, -0.5],
        "linearity_levels_below_upper_db": [0.0, 20.0, 40.0, 55.0],
        "linearity_uncertainties_db": [0.1, 0.1, 0.15, 0.3],
        "relative_attenuations_db": [_ROW, [_NAN, *_ROW[1:]], _ROW],
        "relative_attenuation_uncertainties_db": [_ROW_U, [_NAN, *_ROW_U[1:]], _ROW_U],
        "tested_midband_frequencies_hz": [31.5, 1000.0, 16000.0],
    }
    fields.update(overrides)
    return filters.FilterPeriodicMeasurements(**fields)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# The test frequencies (13.3, Annex C)
# --------------------------------------------------------------------------
def test_test_frequencies_reproduce_table_c1() -> None:
    """Table C.1: the 15 one-third-octave frequencies to five decimals."""
    omega = filters.periodic_test_frequencies(3)
    for k, (printed, _, _) in ref.IEC61260_3_TABLE_C1.items():
        assert round(float(omega[k + 7]), 5) == printed, k


def test_test_frequencies_reproduce_the_derivation_of_c2() -> None:
    """(C.3) and (C.4): Omega_1 ~ 1,026 67 and its inverse ~ 0,974 02."""
    omega = filters.periodic_test_frequencies(3)
    upper, lower = ref.IEC61260_3_C2
    assert round(float(omega[8]), 5) == upper
    assert round(float(omega[6]), 5) == lower
    literal = 1 + (10 ** (1 / 20) - 1) / (10 ** (3 / 20) - 1) * (10 ** (3 / 80) - 1)
    assert float(omega[8]) == pytest.approx(literal, rel=1e-15)


def test_octave_test_frequencies_are_the_frequency_parameters() -> None:
    """13.3 NOTE 2: for octave-band filters Omega_k = R_k."""
    omega = filters.periodic_test_frequencies(1)
    g = 10**0.3
    for k, (exponent, _, _) in ref.IEC61260_3_TABLE_1.items():
        assert omega[k + 7] == pytest.approx(g**exponent, rel=1e-14)
        assert omega[7 - k] == pytest.approx(g**-exponent, rel=1e-14)


@pytest.mark.parametrize("fraction", [1, 2, 3, 6, 12, 24])
def test_test_frequencies_are_the_breakpoints_of_61260_1(fraction: int) -> None:
    """Formula (1) is Formula (9) of IEC 61260-1: the Table 1 limits agree."""
    omega = filters.periodic_test_frequencies(fraction)
    for cls in (1, 2):
        limits = filters.PERIODIC_TEST_ATTENUATION_LIMITS_DB[cls]
        low, high = filters.class_limits(fraction, cls, omega)
        for k in range(-7, 8):
            lower, upper = limits[abs(k)]
            if abs(k) >= 4:
                assert low[k + 7] == pytest.approx(lower)
            else:
                assert low[k + 7] == pytest.approx(lower)
                assert high[k + 7] == pytest.approx(upper)


def test_test_frequencies_are_read_only_and_refuse_a_bad_fraction() -> None:
    omega = filters.periodic_test_frequencies(3)
    assert not omega.flags.writeable
    with pytest.raises(ValueError, match="'fraction'"):
        filters.periodic_test_frequencies(0)


def test_the_limits_are_table_1() -> None:
    """Table 1 of IEC 61260-3, and the limit columns of Table C.1."""
    for k, (_, class1, class2) in ref.IEC61260_3_TABLE_1.items():
        for cls, printed in ((1, class1), (2, class2)):
            lower, upper = filters.PERIODIC_TEST_ATTENUATION_LIMITS_DB[cls][k]
            assert lower == printed[0]
            assert upper == (math.inf if printed[1] is None else printed[1])
    for k, (_, class1, class2) in ref.IEC61260_3_TABLE_C1.items():
        for cls, printed in ((1, class1), (2, class2)):
            lower, upper = filters.PERIODIC_TEST_ATTENUATION_LIMITS_DB[cls][abs(k)]
            assert (lower, upper) == (
                printed[0],
                math.inf if printed[1] is None else printed[1],
            )


def test_the_limits_are_immutable() -> None:
    with pytest.raises(TypeError):
        filters.PERIODIC_TEST_ATTENUATION_LIMITS_DB[1] = ()  # type: ignore[index]


# --------------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------------
def test_a_conforming_record_passes_with_the_caveat_of_1_5() -> None:
    """Without public pattern approval the statement is 14 l)."""
    verdict = filters.verify_filter_periodic(1, _record(), fraction=3)
    assert verdict.passes
    assert [c.clause for c in verdict.clauses] == ["10.2", "11.7", "13"]
    assert verdict.missing == ()
    assert "no general statement or conclusion can be made" in verdict.statement
    assert "class 1 specifications" in verdict.statement


def test_a_public_pattern_approval_turns_the_statement_into_14_k() -> None:
    verdict = filters.verify_filter_periodic(
        1, _record(), fraction=3, pattern_approval_public=True
    )
    assert verdict.statement.endswith(
        "the filter submitted for testing conforms to the class 1 specifications "
        "of IEC 61260-1:2014."
    )


def test_a_deviation_on_its_limit_conforms_and_past_it_fails() -> None:
    """The limits of 10.2.2 are inclusive, as the TC 29 rule makes them."""
    on = filters.verify_filter_periodic(
        1, _record(midband_attenuations_db=[0.4, -0.4, 0.0]), fraction=3
    )
    assert on.passes
    past = filters.verify_filter_periodic(
        1, _record(midband_attenuations_db=[0.41, 0.0, 0.0]), fraction=3
    )
    assert not past.passes
    assert past.failed == (("10.2", "500 Hz"),)
    assert past.statement.startswith(
        "The filter submitted for periodic testing did not successfully complete "
        "the class 1 tests of IEC 61260-3."
    )
    assert "10.2 (500 Hz)" in past.statement


def test_class_2_widens_every_limit() -> None:
    record = _record(midband_attenuations_db=[0.55, 0.0, 0.0])
    assert not filters.verify_filter_periodic(1, record, fraction=3).passes
    assert filters.verify_filter_periodic(2, record, fraction=3).passes


def test_an_uncertainty_above_its_maximum_makes_the_result_unusable() -> None:
    """5.3: such a result "shall not be used to evaluate conformance"."""
    verdict = filters.verify_filter_periodic(
        1, _record(midband_uncertainties_db=[0.15, 0.25, 0.15]), fraction=3
    )
    assert not verdict.passes
    assert verdict.unusable == (("10.2", "1 kHz"),)
    assert verdict.failed == ()
    assert "cannot be used to evaluate conformance" in verdict.statement
    assert "5.3" in verdict.statement


def test_linearity_limits_and_maxima_switch_40_db_below_the_upper_boundary() -> None:
    """5.13.3 within 40 dB of the upper boundary, 5.13.4 beyond; Annex B follows."""
    near = _record(
        linearity_deviations_db=[0.6],
        linearity_levels_below_upper_db=[35.0],
        linearity_uncertainties_db=[0.1],
    )
    far = _record(
        linearity_deviations_db=[0.6],
        linearity_levels_below_upper_db=[45.0],
        linearity_uncertainties_db=[0.1],
    )
    assert not filters.verify_filter_periodic(1, near, fraction=3).clause("11.7").passes
    assert filters.verify_filter_periodic(1, far, fraction=3).clause("11.7").passes
    wide = _record(
        linearity_deviations_db=[0.0, 0.0],
        linearity_levels_below_upper_db=[30.0, 50.0],
        linearity_uncertainties_db=[0.3, 0.3],
    )
    clause = filters.verify_filter_periodic(1, wide, fraction=3).clause("11.7")
    assert clause.unusable == ("30 dB below the upper boundary",)


def test_clause_13_reads_its_maximum_off_the_attenuation() -> None:
    """Annex B: 0,20 dB up to 2 dB, 0,30 dB up to 40 dB, 0,50 dB beyond."""
    verdict = filters.verify_filter_periodic(1, _record(), fraction=3)
    maxima = {
        label: v.max_uncertainty
        for label, v in zip(
            verdict.clause("13").labels, verdict.clause("13").verifications, strict=True
        )
    }
    assert maxima["31.5 Hz, k = 0"] == 0.20
    assert maxima["31.5 Hz, k = 4"] == 0.30
    assert maxima["31.5 Hz, k = 7"] == 0.50


def test_clause_13_judges_the_stop_band_on_its_minimum_alone() -> None:
    """ "+70; +inf": 75 dB conforms, 65 dB does not."""
    row = list(_ROW)
    row[14] = 65.0
    record = _record(
        relative_attenuations_db=[row, _ROW, _ROW],
        relative_attenuation_uncertainties_db=[_ROW_U, _ROW_U, _ROW_U],
    )
    verdict = filters.verify_filter_periodic(1, record, fraction=3)
    assert verdict.clause("13").failed == ("31.5 Hz, k = 7",)
    stop = next(
        v
        for label, v in zip(
            verdict.clause("13").labels, verdict.clause("13").verifications, strict=True
        )
        if label == "1 kHz, k = 7"
    )
    assert stop.upper_limit == math.inf
    assert stop.passes


def test_clause_13_skips_the_frequencies_13_4_drops() -> None:
    verdict = filters.verify_filter_periodic(1, _record(), fraction=3)
    labels = verdict.clause("13").labels
    assert "1 kHz, k = -7" not in labels
    assert len(labels) == 3 * 15 - 1


def test_the_swept_test_of_10_3_replaces_10_2() -> None:
    record = _record(
        midband_attenuations_db=None,
        midband_uncertainties_db=None,
        bandwidth_deviations_db=[0.05, 0.04, 0.06],
        bandwidth_uncertainties_db=[0.12, 0.12, 0.12],
    )
    verdict = filters.verify_filter_periodic(1, record, fraction=3)
    assert verdict.passes
    assert verdict.clause("10.3").verifications[0].max_uncertainty == 0.20


def test_a_record_without_clause_13_is_incomplete() -> None:
    record = _record(
        relative_attenuations_db=None, relative_attenuation_uncertainties_db=None
    )
    verdict = filters.verify_filter_periodic(1, record, fraction=3)
    assert verdict.missing == ("13",)
    assert not verdict.passes
    assert "incomplete" in verdict.statement


def test_the_other_level_ranges_of_11_9_are_graded_30_db_down() -> None:
    record = _record(
        range_linearity_deviations_db=[0.2, 0.55],
        range_linearity_uncertainties_db=[0.1, 0.1],
    )
    clause = filters.verify_filter_periodic(1, record, fraction=3).clause("11.9")
    assert clause.failed == ("level range 2, 30 dB below its upper boundary",)


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"midband_uncertainties_db": None}, "clause 10.2 needs"),
        ({"midband_uncertainties_db": [0.1, 0.1]}, "must have the same length"),
        ({"midband_uncertainties_db": [0.1, -0.1, 0.1]}, "must be non-negative"),
        ({"midband_attenuations_db": [0.1, _NAN, 0.1]}, "must hold finite values"),
        ({"set_midband_frequencies_hz": [500.0, 1000.0]}, "labels 2 filters"),
        ({"relative_attenuations_db": [_ROW[:14]] * 3}, "one row of 15 values"),
        (
            {"relative_attenuation_uncertainties_db": [_ROW_U, _ROW_U, _ROW_U]},
            "must leave the same test frequencies out",
        ),
    ],
)
def test_records_the_rule_cannot_be_read_on_are_refused(
    overrides: dict[str, object], fragment: str
) -> None:
    with pytest.raises(ValueError, match=fragment):
        _record(**overrides)


def test_the_verifier_refuses_a_foreign_class_and_an_empty_record() -> None:
    record = _record()
    with pytest.raises(ValueError, match="'filter_class' must be 1 or 2"):
        filters.verify_filter_periodic(0, record, fraction=3)
    empty = filters.FilterPeriodicMeasurements()
    with pytest.raises(ValueError, match="holds no result to grade"):
        filters.verify_filter_periodic(1, empty, fraction=3)


def test_the_verdicts_have_no_truth_value() -> None:
    verdict = filters.verify_filter_periodic(1, _record(), fraction=3)
    with pytest.raises(
        TypeError, match="FilterPeriodicVerification has no truth value"
    ):
        bool(verdict)
    clause = verdict.clause("13")
    with pytest.raises(TypeError, match="PeriodicTestClause has no truth value"):
        bool(clause)
    with pytest.raises(KeyError, match="'10.3' was not measured"):
        verdict.clause("10.3")


def test_the_record_is_frozen_into_tuples() -> None:
    record = _record()
    assert isinstance(record.midband_attenuations_db, tuple)
    assert isinstance(record.relative_attenuations_db, tuple)
    assert isinstance(record.relative_attenuations_db[0], tuple)


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_verdict_and_its_clauses_plot(language: str) -> None:
    verdict = filters.verify_filter_periodic(1, _record(), fraction=3)
    ax = verdict.plot(language=language)
    assert ax.get_yscale() == "symlog"
    assert [t.get_text() for t in ax.get_xticklabels()] == ["§10.2", "§11.7", "§13"]
    plt.close("all")
    ax = verdict.clause("13").plot(language=language)
    assert ax.get_xscale() == "log"
    plt.close("all")
    ax = verdict.clause("11.7").plot(language=language)
    assert "§11.7" in ax.get_title()
    plt.close("all")


def test_an_unusable_result_is_drawn_hollow() -> None:
    verdict = filters.verify_filter_periodic(
        1, _record(midband_uncertainties_db=[0.15, 0.25, 0.15]), fraction=3
    )
    ax = verdict.plot()
    hollow = [
        line
        for line in ax.lines
        if line.get_marker() == "o" and line.get_markerfacecolor() == "none"
    ]
    assert len(hollow) == 1
    assert np.isfinite(np.asarray(hollow[0].get_ydata(), dtype=float)).all()
    plt.close("all")
