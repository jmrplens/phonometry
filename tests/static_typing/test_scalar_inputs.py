#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A count, a flag, a band mapping and a sample rate take, for mypy too, what runs.

NumPy code hands over a count as ``np.int64`` (from ``np.argmax`` or a
shape) and a flag as ``np.True_`` (from a comparison); a parameter annotated
``int`` or ``bool`` refused them for mypy while the validator took them. A
spectrum keyed by band centre is written ``{125: ...}`` as often as
``{125.0: ...}``, and ``Mapping`` is invariant in its key. A sample rate
one function returns as a ``float`` was refused by the next one typed
``int``. These calls run, and CI type checks every file in this directory
alongside ``src`` and ``scripts``, so each one holds an annotation to what
its body takes. ``scripts/check_parameter_annotations.py`` holds every
public parameter to the rule; this file holds the forms a caller writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_type

import numpy as np

from phonometry import (
    building,
    electroacoustics,
    filters,
    io,
    metrology,
    signals,
    vibration,
)

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Mapping

    from numpy.typing import NDArray

    from phonometry.vibration.human.signal_burst import BurstQuantity

#: The sixteen one-third-octave centres ISO 717-1 rates, as integers.
_THIRDS = (100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600)
_BANDS = (*_THIRDS, 2000, 2500, 3150)


def test_a_numpy_integer_is_a_count() -> None:
    """``np.argmax`` and ``len`` of an array give a count numpy code passes on."""
    n_turns = np.int64(np.argmax([0.0, 1.0, 2.0]))
    field = electroacoustics.loop_center_field(1.0, 2.0, width_m=1.0, n_turns=n_turns)
    assert_type(field, float)
    plain = electroacoustics.loop_center_field(1.0, 2.0, width_m=1.0, n_turns=2)
    assert field == plain
    teeth = vibration.gear_mesh_frequencies(1500.0, np.int64(23), n_harmonics=2)
    assert teeth.frequencies.size > 0
    # Indices validated one at a time: a list may mix the two kinds.
    levels = [50.0, 52.0, 51.0, 49.0]
    corner = building.loudest_corner(levels, excluded=[np.int64(1), 2])
    assert corner == 0


def test_a_numpy_integer_is_a_band_fraction() -> None:
    """``BandFraction | np.integer[Any]``: 1 and 3 as numpy hands them over."""
    loss = building.mass_law_transmission_loss(500.0, 10.0, fraction=np.int64(1))
    plain = building.mass_law_transmission_loss(500.0, 10.0, fraction=1)
    assert np.array_equal(loss, plain)


def test_a_numpy_integer_is_a_filter_bandwidth() -> None:
    """The bank keeps the plain int a numpy integer holds, as it keeps an int."""
    bank = filters.OctaveFilterBank(48000.0, fraction=np.int64(3))
    assert bank.fraction == 3
    assert type(bank.fraction) is int


def test_a_numpy_truth_value_is_a_flag() -> None:
    """A comparison of numpy values gives ``np.True_``, which a flag takes."""
    precise = np.float64(1.0) > 0.0
    weighting = filters.WeightingFilter(48000.0, "A", high_accuracy=precise)
    assert weighting.fs == 48000.0


def test_a_band_mapping_keyed_by_integers() -> None:
    """``dict[int, float]`` is no ``Mapping[float, float]``; ``BandMapping`` takes it."""
    by_band: dict[int, float] = dict.fromkeys(_BANDS, 30.0)
    rated = building.weighted_rating(by_band)
    keyed_by_float: dict[float, float] = {float(f): v for f, v in by_band.items()}
    assert rated.rating == building.weighted_rating(keyed_by_float).rating


def test_burst_indications_keyed_by_integers_alone() -> None:
    """The continuous row is optional: a ``dict[int, ...]`` leaves it out.

    Each row is keyed by the columns the printed table is keyed by, so the
    table's own rows go in as they are.
    """
    test = vibration.SAWTOOTH_BURST_TESTS["whole-body"]
    measured: dict[int, Mapping[BurstQuantity, float]] = {
        cycles: vibration.SIGNAL_BURST_RESPONSE["whole-body", "Wk", cycles]
        for cycles in test.cycle_counts
    }
    verdict = vibration.verify_signal_burst_response("whole-body", "Wk", measured)
    assert verdict.passes


def test_the_rate_one_function_returns_is_the_rate_the_next_one_takes() -> None:
    """A resampled rate is a ``float``, and so is every rate a function takes."""
    x = np.sin(2.0 * np.pi * 1000.0 * np.arange(4800) / 48000.0)
    resampled = signals.resample_signal(x, fs=48000.0, fs_new=32000.0)
    assert_type(resampled.fs, float)
    bank = filters.OctaveFilterBank(resampled.fs)
    assert bank.fs == 32000.0
    level = signals.laeq(np.asarray(resampled.signal), fs=resampled.fs)
    assert np.isfinite(level)


def test_a_signal_rate_is_a_float(tmp_path: pathlib.Path) -> None:
    """``Signal.fs`` is whatever positive rate it was given, and ``io.write`` takes it."""
    fractional = io.Signal(np.zeros(16), 44100.5)
    assert_type(fractional.fs, float)
    whole = io.Signal(np.zeros(16), 44100.0)
    io.write(tmp_path / "whole.wav", whole, fs=whole.fs)
    assert io.read(tmp_path / "whole.wav").fs == 44100


def _scalar(gain: float, offset: float) -> float:
    return gain * offset


def _vectorised(
    gain: float | NDArray[np.float64], offset: float | NDArray[np.float64]
) -> float | NDArray[np.float64]:
    return gain * offset


def test_a_model_returns_one_number_or_an_array_of_trials() -> None:
    """The law of propagation reads one number, Monte Carlo an array of trials."""
    inputs = [
        metrology.Quantity(value=2.0, uncertainty=0.1),
        metrology.Quantity(value=3.0, uncertainty=0.2),
    ]
    propagated = metrology.uncertainty_propagation(_scalar, inputs)
    sampled = metrology.monte_carlo(_vectorised, inputs, n_trials=1000, seed=1)
    assert np.isclose(propagated.value, sampled.value, rtol=0.05)
    assert metrology.monte_carlo(_scalar, inputs, n_trials=1000, seed=1).value > 0.0


def test_an_array_model_is_refused_by_the_law_of_propagation() -> None:
    """A model of arrays of trials is Monte Carlo's; mypy refuses it here."""
    inputs = [metrology.Quantity(value=2.0, uncertainty=0.1)]

    def trials(gain: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.asarray(gain * 2.0)

    result = metrology.uncertainty_propagation(
        trials,  # type: ignore[arg-type]
        inputs,
    )
    assert np.isclose(result.value, 4.0)
