#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A field a record's constructor takes, and a writer hands to it, takes for mypy what runs.

A record a caller builds declares its constructor for the type checker under
``if TYPE_CHECKING:``, and the function rules of
``scripts/check_parameter_annotations.py`` read that constructor as any other
method. A sidecar's numbers were annotated ``float`` on the writers while the
record they build takes a NumPy integer, so ``write_sidecar(path,
np.int64(2))`` ran and failed the type check; a frame's size was a list of
``int | np.integer``, which a ``list[int]`` is not, since a list is
invariant in its item. These calls run, and CI type checks every file in this
directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

import numpy as np

from phonometry import io, simulation

if TYPE_CHECKING:
    import pathlib


def test_a_sidecar_is_written_with_the_numbers_its_record_takes(
    tmp_path: pathlib.Path,
) -> None:
    """``np.int64`` is a real number to the writer as to the record it builds."""
    audio = tmp_path / "take.wav"
    io.write_sidecar(
        audio,
        np.int64(2),
        reference_spl=np.int64(94),
        calibrator_frequency=np.int64(1000),
    )
    record = io.read_sidecar(audio)
    assert record is not None
    assert record.calibration_factor == 2.0
    assert record.reference_spl == 94.0
    assert record.calibrator_frequency == 1000.0


def test_a_frame_takes_its_size_as_any_sequence_of_two_counts() -> None:
    """A typed list of either kind of count, a tuple and any other sequence."""
    pixels: list[int] = [960, 540]
    counts: list[np.int64] = [np.int64(960), np.int64(540)]
    for size in (pixels, counts, (960, 540), deque(pixels)):
        frame = simulation.AnimationFrame(size=size)
        assert frame.size == (960, 540)
