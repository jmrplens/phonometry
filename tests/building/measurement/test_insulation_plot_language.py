#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every insulation result draws its rating plot in the caller's language.

The laboratory, intensity and survey results do not draw anything of their
own: ``.plot()`` hands over to the ISO 717 rating plot they carry. A
``language`` that stopped at the result would leave a Spanish page with an
English figure, so each one is drawn in Spanish here and its frequency axis
read back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import building

if TYPE_CHECKING:
    from collections.abc import Callable

_THIRDS = 16
_OCTAVES = 5
_L1 = np.full(_THIRDS, 95.0)
_L2 = np.linspace(60.0, 40.0, _THIRDS)
_T2 = np.full(_THIRDS, 1.2)
_O1 = np.full(_OCTAVES, 95.0)
_O2 = np.linspace(60.0, 45.0, _OCTAVES)
_K = np.zeros(_OCTAVES)

_RESULTS: dict[str, Callable[[], Any]] = {
    "laboratory airborne": lambda: building.laboratory_airborne_insulation(
        _L1, _L2, _T2, area=10.0, volume=60.0
    ),
    "laboratory impact": lambda: building.laboratory_impact_insulation(
        np.linspace(70.0, 55.0, _THIRDS), _T2, volume=60.0
    ),
    "intensity reduction": lambda: building.intensity_sound_reduction(
        _L1, _L2 - 6.0, measurement_area=10.0, area=10.0
    ),
    "intensity element": lambda: building.intensity_element_normalized_difference(
        _L1, _L2 - 6.0, measurement_area=10.0
    ),
    "survey airborne": lambda: building.survey_airborne_insulation(
        _O1, _O2, _K, volume=60.0, area=10.0
    ),
    "survey impact": lambda: building.survey_impact_insulation(
        np.linspace(68.0, 56.0, _OCTAVES), _K, volume=60.0
    ),
    "survey facade": lambda: building.survey_facade_insulation(
        _O1, _O2, _K, volume=60.0
    ),
}


@pytest.mark.parametrize("name", list(_RESULTS))
def test_the_rating_plot_speaks_the_callers_language(name: str) -> None:
    result = _RESULTS[name]()
    english = result.plot().get_xlabel()
    spanish = result.plot(language="es").get_xlabel()
    plt.close("all")
    assert "Frequency" in english
    assert "Frecuencia" in spanish
