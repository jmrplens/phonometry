#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A public parameter the body converts takes, for mypy too, what it converts.

``np.asarray`` takes a list of integers, a tuple, an integer array and a
nested list, and so does every function that hands its argument to it; a
parameter annotated ``list[float]`` or ``NDArray[np.float64]`` refused them
for mypy while the call ran, and ``list`` refused a list of a narrower type
besides (a ``list[AirLayer]`` is no ``list[Layer]``). These calls run, and
CI type checks every file in this directory alongside ``src`` and
``scripts``, so each one holds an annotation to what its body takes.
``scripts/check_parameter_annotations.py`` holds every public parameter to
the rule; this file holds the forms a caller writes.
"""

from __future__ import annotations

import math
from typing import assert_type

import numpy as np
from numpy.typing import NDArray

from phonometry import (
    aircraft,
    broadcast,
    electroacoustics,
    filters,
    materials,
    metrology,
    noise_control,
    room,
    signals,
    vibration,
)

#: Two channels of samples, ``[channels, samples]``, as a nested list.
_TWO_CHANNELS = [[0.1, -0.2, 0.3, -0.1] * 100, [0.05, 0.1, -0.1, 0.0] * 100]


def test_a_nested_list_is_a_multichannel_signal() -> None:
    """The ``[channels, samples]`` list ``true_peak_level`` documents."""
    levels = broadcast.true_peak_level(_TWO_CHANNELS, fs=48000.0)
    assert_type(levels, float | NDArray[np.float64])
    assert np.shape(levels) == (2,)


def test_integers_and_nested_lists_reach_a_table() -> None:
    """A list of integers is no ``list[float]`` to mypy; ``ArrayLike`` takes it."""
    powers = [1000, 2000]
    distances_m = [200, 400, 800]
    levels = [[90, 85, 80], [92, 87, 82]]
    out = aircraft.npd_level(powers, distances_m, levels, 1500.0, (300, 600))
    assert_type(out, NDArray[np.float64])
    assert out.shape == (2,)


def test_an_integer_array_and_a_list_of_integers_are_signals() -> None:
    """The array head of an overloaded filter takes any array-like.

    The integer array is named, with its type, before the call: written in
    the call, ``np.zeros(..., dtype=np.int64)`` takes its type from the
    parameter, which mypy reads as ``NDArray[Any]`` when the parameter is a
    floating array, so the case would pass however narrow the parameter were.
    """
    weighted = filters.weighting_filter([0, 1, 0, -1] * 1000, 48000)
    assert_type(weighted, np.ndarray)
    integers: NDArray[np.int64] = np.zeros(4000, dtype=np.int64)
    counted = filters.weighting_filter(integers, 48000)
    assert_type(counted, np.ndarray)


def test_a_list_of_one_kind_of_layer_is_a_sequence_of_layers() -> None:
    """A ``list[AirLayer]`` is no ``list[Layer]``, and is a ``Sequence[Layer]``."""
    layers: list[materials.AirLayer] = [materials.AirLayer(thickness_m=0.05)]
    result = materials.layered_absorber((250, 500, 1000), layers)
    assert_type(result, materials.LayeredAbsorberResult)


def test_a_nested_list_is_a_four_pole_matrix_and_an_uncertainty_pair() -> None:
    """Each matrix ``cascade`` collects and each pair of a budget is converted alone.

    So a nested list is a four-pole matrix as an array is, and a list pair,
    a mixed list and an array of pairs are contributions as a tuple pair is.
    """
    identity = [[[1, 0], [0, 1]]] * 3
    compound = noise_control.cascade(identity, np.ones((3, 2, 2)))
    assert_type(compound, NDArray[np.complex128])
    assert compound.shape == (3, 2, 2)
    pairs = metrology.combined_standard_uncertainty([[0.5, 1.0], [0.2, 2.0]])
    mixed = metrology.combined_standard_uncertainty([0.3, (0.5, 1.0)])
    stacked = metrology.combined_standard_uncertainty(
        np.array([[0.5, 1.0], [0.2, 2.0]])
    )
    assert_type(pairs, float)
    assert math.isclose(pairs, math.sqrt(0.41))
    assert math.isclose(mixed, math.sqrt(0.34))
    assert math.isclose(stacked, pairs)


def test_integer_arrays_are_contributions_as_float_arrays_are() -> None:
    """The body reads each value with ``float`` and each pair with ``np.asarray``.

    So an integer array of products, of pairs read row by row, and a list
    of integer pairs are contributions as their float forms are.
    """
    products: NDArray[np.int64] = np.array([3, 4], dtype=np.int64)
    rows: NDArray[np.int64] = np.array([[3, 1], [4, 1]], dtype=np.int64)
    pairs = [np.array([3, 1], dtype=np.int64), np.array([4, 1], dtype=np.int64)]
    from_products = metrology.combined_standard_uncertainty(products)
    from_rows = metrology.combined_standard_uncertainty(rows)
    from_pairs = metrology.combined_standard_uncertainty(pairs)
    assert_type(from_products, float)
    assert math.isclose(from_products, 5.0)
    assert math.isclose(from_rows, 5.0)
    assert math.isclose(from_pairs, 5.0)


def test_records_from_a_generator_and_codes_as_lists_are_inputs() -> None:
    """A generator of records is an input set; a Golay pair may hold lists."""
    rng = np.random.default_rng(7)
    x1, x2 = rng.standard_normal(4096), rng.standard_normal(4096)
    records = (record for record in (x1, x2))
    miso = signals.miso_coherence(records, x1 + x2, 1000.0, nperseg=256)
    assert_type(miso, signals.MISOCoherenceResult)
    assert miso.n_inputs == 2
    # The order-2 pair of golay_pair(2), written as lists.
    code_a, code_b = [1.0, 1.0, 1.0, -1.0], [1.0, 1.0, -1.0, 1.0]
    ir = room.golay_impulse_response(code_a * 2, code_b * 2, (code_a, code_b))
    assert_type(ir, room.ImpulseResponseResult)


def test_a_curve_given_as_one_array_of_two_rows_is_a_pair() -> None:
    """A record that holds a curve as two arrays takes them as one two-row array too.

    ``pair_of_arrays`` unpacks a tuple, a list or an array of rows alike;
    the declared constructor said ``Sequence[ArrayLike]``, which a numpy
    array is not to mypy, so ``np.vstack((x, y))`` ran and failed the type
    check. Each array is named, with its type, before the call: written in
    the call, it would take its type from the parameter.
    """
    pattern: NDArray[np.float64] = np.vstack(
        ([0.0, 90.0, 180.0, 270.0], [0.0, -3.0, -10.0, -3.0])
    )
    noise: NDArray[np.float64] = np.vstack(
        ([100.0, 1000.0, 10000.0], [12.0, 8.0, 10.0])
    )
    distortion: NDArray[np.float64] = np.vstack(
        ([110.0, 120.0, 130.0], [0.1, 0.5, 2.0])
    )
    microphone = electroacoustics.MicrophoneDirectivity(polar=pattern)
    loudspeaker = electroacoustics.LoudspeakerDirectivity(polar=pattern)
    spectrum = electroacoustics.MicrophoneNoise(spectrum=noise)
    overload = electroacoustics.MicrophoneOverload(distortion=distortion)
    for held, given in (
        (microphone.polar, pattern),
        (loudspeaker.polar, pattern),
        (spectrum.spectrum, noise),
        (overload.distortion, distortion),
    ):
        assert held is not None
        np.testing.assert_array_equal(held[0], given[0])
        np.testing.assert_array_equal(held[1], given[1])


def test_the_axes_of_an_elevation_model_given_as_one_array_are_a_grid() -> None:
    """The ``(x, y, z)`` of a rotorcraft's terrain arrive in one array too.

    ``z`` is a grid over ``(y, x)``, so the three rows are no rectangular
    array of floats; an array of three objects holds them, and the record
    unpacks it as it unpacks a tuple.
    """
    x = np.array([0.0, 500.0, 1000.0])
    y = np.array([0.0, 500.0])
    axes: NDArray[np.object_] = np.empty(3, dtype=object)
    axes[0], axes[1], axes[2] = x, y, np.zeros((2, 3))
    ground = aircraft.RotorcraftGround(terrain=axes)
    assert ground.terrain is not None
    np.testing.assert_array_equal(ground.terrain[0], x)
    assert ground.terrain[2].shape == (2, 3)


def test_three_risk_thresholds_given_as_an_array_are_a_triple() -> None:
    """The thresholds of a multiple-shock result are any three real numbers.

    ``floats_of`` reads a tuple, a list or an array of three; the declared
    constructor said ``Sequence[float]``, which refused the array and a list
    of numpy floats for mypy while the call ran. The array is named, with
    its type, before the call.
    """
    peaks: NDArray[np.float64] = np.full(5, 40.0)
    thresholds: NDArray[np.float64] = np.array([0.72, 1.42, 2.17])
    result = vibration.MultipleShockResult(
        sex="male",
        acceleration_dose=1.0,
        daily_dose=1.0,
        compression_dose=0.5,
        risk=1.22,
        probability=0.37,
        start_age=20.0,
        exposure_duration_years=20,
        days_per_year=120.0,
        peaks=peaks,
        risk_thresholds=thresholds,
    )
    assert result.risk_thresholds == (0.72, 1.42, 2.17)
