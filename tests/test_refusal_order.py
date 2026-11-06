#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The refusal-order plugin fails a test whose refusal came after a library advisory.

``tests/refusal_order.py`` wraps every ``pytest.raises`` that waits on an
exception which is not a warning. These cases drive one such context by hand,
so the plugin's verdict is the thing under test.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest

import phonometry
from phonometry import emission


def _closed(raises: pytest.RaisesExc[ValueError], error: ValueError) -> bool:
    """Leave a ``pytest.raises`` block as if *error* had been raised in it."""
    return bool(raises.__exit__(type(error), error, None))


def test_an_advisory_ahead_of_the_refusal_fails_the_test() -> None:
    raises = pytest.raises(ValueError, match="refused")
    raises.__enter__()
    warnings.warn("a sound power advisory", emission.SoundPowerWarning, stacklevel=1)
    error = ValueError("refused")
    with pytest.raises(pytest.fail.Exception, match="came before the ValueError"):
        _closed(raises, error)


def test_a_warning_shown_at_a_library_line_counts_too() -> None:
    """NumPy's RuntimeWarning is shown at the line of the package that called it."""
    raises = pytest.raises(ValueError, match="refused")
    raises.__enter__()
    warnings.warn_explicit(
        "overflow encountered in multiply",
        RuntimeWarning,
        str(phonometry.__file__),
        1,
    )
    error = ValueError("refused")
    with pytest.raises(pytest.fail.Exception, match="RuntimeWarning"):
        _closed(raises, error)


def test_a_refusal_alone_passes_and_a_warning_of_the_test_is_handed_back() -> None:
    raises = pytest.raises(ValueError, match="refused")
    raises.__enter__()
    with pytest.warns(UserWarning, match="the test's own"):
        warnings.warn("the test's own", UserWarning, stacklevel=1)
    error = ValueError("refused")
    assert _closed(raises, error)


def test_a_warning_the_block_waits_on_is_left_alone() -> None:
    with pytest.warns(emission.SoundPowerWarning):
        emission.sound_power_reverberation(
            np.full((4, 6), 80.0),
            np.full(6, 1.5),
            200.0,
            220.0,
            frequencies=np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]),
        )
