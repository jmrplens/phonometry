#  Copyright (c) 2026. Jose M. Requena-Plens
"""Committed oracle: gating and LRA stages on the authentic-programme series.

The EBU loudness test set's authentic-programme audio cannot be committed
(its licence covers technical testing only and the programme content carries
its own rights), but the per-block loudness series measured from it are
plain measurement data and cannot reconstruct the audio. This file pins the
gating and loudness-range stages to those committed series everywhere,
including CI cells without network access:

* ``*_momentary``: 400 ms blocks at the 100 ms hop of the BS.1770-5 gate,
  i.e. exactly the integrated-loudness gate input, in LUFS;
* ``*_short_term``: 3 s blocks at a 100 ms hop, the EBU Tech 3342 input.

The series were measured with :func:`phonometry.broadcast.program_loudness`
from ``seq-3341-7_seq-3342-5`` (NLR) and ``seq-3341-2011-8_seq-3342-6``
(WLR) and stored rounded to 0.0001 LU, three orders of magnitude below the
official tolerances. The full chain (K front end included) runs against the
original audio in ``test_ebu_material_oracle.py`` wherever the set is
present.
"""

import pathlib

import numpy as np
import pytest

from phonometry.broadcast import loudness_range
from phonometry.broadcast.program_loudness import _integrated_from_blocks

_NPZ = (
    pathlib.Path(__file__).parents[1]
    / "data"
    / "broadcast"
    / "ebu_programme_block_loudness.npz"
)
with np.load(_NPZ) as _f:
    _SERIES = {key: _f[key] for key in _f.files}


@pytest.mark.parametrize(
    ("key", "case"),
    [("nlr", "Tech 3341 case 7 (NLR)"), ("wlr", "Tech 3341 case 8 (WLR)")],
)
def test_gated_integrated_loudness_from_series(key: str, case: str) -> None:
    integrated, _ = _integrated_from_blocks(_SERIES[f"{key}_momentary"])
    assert integrated == pytest.approx(-23.0, abs=0.1), case


@pytest.mark.parametrize(
    ("key", "expected", "case"),
    [
        ("nlr", 5.0, "Tech 3342 case 5 (NLR)"),
        ("wlr", 15.0, "Tech 3342 case 6 (WLR)"),
    ],
)
def test_loudness_range_from_series(key: str, expected: float, case: str) -> None:
    assert loudness_range(_SERIES[f"{key}_short_term"]) == pytest.approx(
        expected, abs=1.0
    ), case
