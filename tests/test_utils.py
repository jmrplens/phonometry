#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for internal utility helpers.
"""

import numpy as np

from pyoctaveband.utils import _resample_to_length


def test_resample_to_length_padding_and_trimming() -> None:
    """Verify _resample_to_length pads and trims 1D and 2D signals."""
    x = np.ones(10)
    y = _resample_to_length(x, 1, 12)
    assert len(y) == 12
    assert np.all(y[10:] == 0)

    x2 = np.ones((2, 10))
    y2 = _resample_to_length(x2, 1, 12)
    assert y2.shape == (2, 12)
    assert np.all(y2[:, 10:] == 0)

    y3 = _resample_to_length(x, 1, 8)
    assert len(y3) == 8

    y4 = _resample_to_length(x2, 1, 8)
    assert y4.shape == (2, 8)