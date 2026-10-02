#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A calibration's tone estimate chosen by a plain ``bool``, for mypy too.

``metrology.sensitivity`` reads the tone of a calibrator take by its RMS, or
with ``narrowband=True`` by a coherent detector locked to the tone, which
needs the sample rate: ``fs``, by keyword or in position, or a
:class:`~phonometry.io.Signal` that carries it. A literal ``True`` without
either is refused before it runs. A ``bool`` held in a variable, as when the
choice comes from a setting, is accepted with the rate in either place, and a
Signal is accepted with either estimate; a bare array with a ``bool``
variable and no rate is still refused, because the variable may hold
``True``. The suite checks the values at run time; this file holds the
typing, and it only holds it because CI type checks every file in this
directory alongside ``src`` and ``scripts``, in strict mode, so an ignore
that a call no longer needs fails too. Overloads that take only the two
literals still run, and fail here.
"""

from __future__ import annotations

from typing import assert_type

import numpy as np
import pytest

from phonometry import io, metrology

_FS = 48000
#: Two seconds of a 1 kHz tone at half of full scale: a whole number of
#: cycles, so its RMS is the amplitude over the square root of two.
_AMPLITUDE = 0.5
_TONE = _AMPLITUDE * np.sin(2.0 * np.pi * 1000.0 * np.arange(2 * _FS) / _FS)
_P0_PA = metrology.ISO1683_REFERENCE_VALUES["gas"]["sound_pressure"].value
#: The factor that maps the tone to 94 dB: the pressure over the tone's RMS.
_FACTOR = _P0_PA * 10.0 ** (94.0 / 20.0) / (_AMPLITUDE / np.sqrt(2.0))


@pytest.mark.parametrize("narrowband", [False, True])
def test_a_bool_variable_is_accepted_with_the_rate(*, narrowband: bool) -> None:
    factor = metrology.sensitivity(_TONE, fs=_FS, narrowband=narrowband)
    assert_type(factor, float)
    assert factor == pytest.approx(_FACTOR, rel=1e-9)


@pytest.mark.parametrize("narrowband", [False, True])
def test_a_bool_variable_is_accepted_with_the_rate_in_position(
    *, narrowband: bool
) -> None:
    from_variable = metrology.sensitivity(
        _TONE, 94.0, _P0_PA, _FS, narrowband=narrowband
    )
    assert_type(from_variable, float)
    coherent = metrology.sensitivity(_TONE, 94.0, _P0_PA, _FS, narrowband=True)
    assert_type(coherent, float)
    assert from_variable == pytest.approx(_FACTOR, rel=1e-9)
    assert coherent == pytest.approx(_FACTOR, rel=1e-9)


@pytest.mark.parametrize("narrowband", [False, True])
def test_a_signal_carries_the_rate_for_either_estimate(*, narrowband: bool) -> None:
    take = io.Signal(_TONE, fs=_FS)
    from_variable = metrology.sensitivity(take, narrowband=narrowband)
    assert_type(from_variable, float)
    coherent = metrology.sensitivity(take, narrowband=True)
    assert_type(coherent, float)
    assert from_variable == pytest.approx(_FACTOR, rel=1e-9)
    assert coherent == pytest.approx(_FACTOR, rel=1e-9)


def test_a_bool_variable_without_the_rate_is_still_refused() -> None:
    narrowband = bool(_TONE.size)
    with pytest.raises(ValueError, match="requires 'fs'"):
        metrology.sensitivity(_TONE, narrowband=narrowband)  # type: ignore[call-overload]


def test_a_literal_true_without_the_rate_is_still_refused() -> None:
    with pytest.raises(ValueError, match="requires 'fs'"):
        metrology.sensitivity(_TONE, narrowband=True)  # type: ignore[call-overload]
