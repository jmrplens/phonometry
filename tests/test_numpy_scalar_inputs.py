#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A count, a band fraction or a rate given as a numpy scalar is read as the number it holds.

The annotations take ``np.int64`` and ``np.True_`` where the validators do;
a result record that validates such a field keeps the plain ``int`` the
validator returns, so its annotation (``int``, ``BandFraction``) is what a
reader gets whatever the producer handed it. ``io.write`` refuses a
fractional rate whether it is given or a Signal's own, since the header
holds a whole number of samples per second.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from result_factories import (
    _coherence_check,
    _correction_verification,
    _intensity_power_negative,
    _plant_contour,
    _service_equipment,
)

from phonometry import filters, io, metrology

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Callable


@pytest.mark.parametrize(
    ("record", "field"),
    [
        (_service_equipment, "fraction"),
        (_intensity_power_negative, "fraction"),
        (_correction_verification, "clause"),
        (_coherence_check, "n_impacts"),
        (_coherence_check, "min_n_records"),
        (_plant_contour, "n_positions"),
    ],
)
def test_a_result_record_stores_the_int_a_numpy_integer_holds(
    record: Callable[[], Any], field: str
) -> None:
    built = record()
    value = getattr(built, field)
    rebuilt = dataclasses.replace(built, **{field: np.int64(value)})
    stored = getattr(rebuilt, field)
    assert stored == value
    assert type(stored) is int


def test_a_capillary_tube_keeps_the_count_it_is_given() -> None:
    """An input record takes ``int | np.integer[Any]`` and keeps it as given."""
    tubes = metrology.CapillaryTube(
        length_m=0.05, radius_m=1.0 / 6000.0, n_tubes=np.int64(2)
    )
    assert tubes.n_tubes == 2


def test_the_filter_bank_reads_a_numpy_bandwidth_as_the_int_it_holds() -> None:
    bank = filters.OctaveFilterBank(48000.0, fraction=np.int64(3))
    assert bank.fraction == 3
    assert type(bank.fraction) is int
    assert "fraction=3," in repr(bank) or "fraction=3)" in repr(bank)
    assert type(filters.OctaveFilterBank(48000.0, fraction=3).fraction) is int


def test_io_write_refuses_a_signal_at_a_fractional_rate(
    tmp_path: pathlib.Path,
) -> None:
    """The header holds a whole rate; a Signal's own fractional one is refused."""
    signal = io.Signal(np.zeros(64), 44100.5)
    with pytest.raises(ValueError, match=r"'fs' must be a whole number, got 44100\.5"):
        io.write(tmp_path / "fractional.wav", signal)
    assert not (tmp_path / "fractional.wav").exists()


def test_io_write_takes_a_whole_float_rate_and_a_numpy_integer(
    tmp_path: pathlib.Path,
) -> None:
    io.write(tmp_path / "float.wav", np.zeros(64), fs=48000.0)
    io.write(tmp_path / "numpy.wav", np.zeros(64), fs=np.int64(48000))
    assert io.read(tmp_path / "float.wav").fs == 48000
    assert io.read(tmp_path / "numpy.wav").fs == 48000
