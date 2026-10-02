#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A survey's reverberation index form chosen by a plain ``bool``, for mypy too.

``estimate_reverberation_index`` reads the five octave-band values of the
reverberation index ``k``, or the single index of the ``A, C`` column with
``weighted=True``, for service equipment noise that is weighted globally
(ISO 10052:2021 Table 4). A literal ``True`` or ``False`` picks the narrow
type; a ``bool`` held in a variable, as when the form comes from a setting,
is accepted and gives either. The suite checks the values at run time; this
file holds the typing, and it only holds it because CI type checks every
file in this directory alongside ``src`` and ``scripts``. Overloads that
take only the two literals still run, and fail here.
"""

from __future__ import annotations

from typing import assert_type

import numpy as np
import pytest

from phonometry import building

#: A furnished living room of 40 m³, in the 35 m³ to 60 m³ row of Table 4.
_VOLUME_M3 = 40.0
_ROOM = "furnished"


def test_a_literal_form_gives_the_narrow_type() -> None:
    bands = building.estimate_reverberation_index(_VOLUME_M3, _ROOM)
    assert_type(bands, np.ndarray)
    bands_named = building.estimate_reverberation_index(
        _VOLUME_M3, _ROOM, weighted=False
    )
    assert_type(bands_named, np.ndarray)
    single = building.estimate_reverberation_index(_VOLUME_M3, _ROOM, weighted=True)
    assert_type(single, float)
    assert bands.shape == (5,)
    np.testing.assert_array_equal(bands_named, bands)
    assert isinstance(single, float)


@pytest.mark.parametrize("weighted", [False, True])
def test_a_bool_variable_is_accepted_and_gives_either_form(*, weighted: bool) -> None:
    index = building.estimate_reverberation_index(_VOLUME_M3, _ROOM, weighted=weighted)
    assert_type(index, np.ndarray | float)
    if weighted:
        single = building.estimate_reverberation_index(_VOLUME_M3, _ROOM, weighted=True)
        assert isinstance(index, float)
        assert index == pytest.approx(single)
    else:
        bands = building.estimate_reverberation_index(_VOLUME_M3, _ROOM)
        assert isinstance(index, np.ndarray)
        np.testing.assert_array_equal(index, bands)
