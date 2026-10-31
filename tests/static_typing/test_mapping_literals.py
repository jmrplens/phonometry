#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A ``dict`` written in the call is read against the mapping it is passed for.

mypy infers a ``dict`` display against the type of the parameter only when
that type holds one mapping; against a union of two or more it infers the
display on its own, a ``Literal`` column name as a ``str`` and two inner
mappings of different key types as ``object``. Each call below runs and was
refused that way: the parameter took a union of mappings, one per key a
caller may write. Each mapping is now offered in an overload head of its
own. CI type checks every file in this directory alongside ``src`` and
``scripts``, so a call here that stops type checking fails the build;
``scripts/check_parameter_annotations.py`` holds every public parameter to
the rule.
"""

from __future__ import annotations

import pytest

from phonometry import aircraft, vibration


def test_burst_indications_written_in_the_call() -> None:
    """A burst length, the continuous row, or both, keyed by printed column."""
    one = vibration.verify_signal_burst_response(
        "whole-body", "Wk", {16: {"rms": 0.115}}
    )
    assert one.passes
    continuous = vibration.verify_signal_burst_response(
        "whole-body", "Wk", {None: {"rms": 0.362, "vdv": 1.15}}
    )
    assert continuous.passes
    both = vibration.verify_signal_burst_response(
        "whole-body", "Wk", {16: {"rms": 0.115}, None: {"rms": 0.362}}
    )
    assert both.cycle_counts == (16, None)


def test_a_misspelt_column_written_in_the_call_is_refused() -> None:
    """The column names are read as the ``Literal`` they are, not as ``str``."""
    verify = vibration.verify_signal_burst_response
    with pytest.raises(ValueError, match="does not print"):
        verify("whole-body", "Wk", {16: {"r.m.s.": 0.115}})  # type: ignore[call-overload]


def test_a_directional_response_with_a_fractional_angle() -> None:
    """One band read at 22.5 degrees beside bands read at whole degrees."""
    verdict = aircraft.verify_aircraft_noise_system(
        directional={1000: {30: 0.2, 60: 0.3}, 2000: {22.5: 0.1, 60: 0.2}}
    )
    assert verdict.passes
    by_float = aircraft.verify_aircraft_noise_system(directional={1000.0: {30: 0.2}})
    assert by_float.passes
