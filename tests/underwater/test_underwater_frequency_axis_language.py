#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the underwater spectrum figures follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels of these figures are written by
``format_frequency_axis`` and by nothing else: a renderer that does not pass
its ``language`` on draws ``31.5`` in a Spanish figure. Every figure below
spans 31,5 Hz, the lowest octave centre whose label carries a decimal, because
a label without one proves nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import underwater
from phonometry.underwater.bioacoustics.audiograms import group_audiogram
from phonometry.underwater.sources.ambient_noise import ocean_ambient_noise
from phonometry.underwater.sources.ship_traffic_noise import ship_source_spectrum

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes

#: 20 Hz to 2 kHz: seven octave labels, the first of them 31,5.
_FREQUENCIES = np.geomspace(20.0, 2000.0, 30)


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def _ship_source_level(language: str) -> Axes:
    result = underwater.monopole_source_level(
        np.full(_FREQUENCIES.size, 150.0), _FREQUENCIES, 8.0
    )
    return result.plot(language=language)


def _ambient_noise(language: str) -> Axes:
    return ocean_ambient_noise(_FREQUENCIES, wind_speed_knots=15.0).plot(
        language=language
    )


def _ship_traffic(language: str) -> Axes:
    return ship_source_spectrum(12.0, 100.0, frequency_hz=_FREQUENCIES).plot(
        language=language
    )


def _audiogram(language: str) -> Axes:
    # Drawn through the shared spectrum axes of the underwater module.
    return group_audiogram(_FREQUENCIES, "VHF").plot(language=language)


_FIGURES: list[Callable[[str], Axes]] = [
    _ship_source_level,
    _ambient_noise,
    _ship_traffic,
    _audiogram,
]


@pytest.mark.parametrize("draw", _FIGURES, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_labels_reach_spanish(draw: Callable[[str], Axes]) -> None:
    labels = _tick_labels(draw("es"))
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _FIGURES, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_labels_are_unchanged_in_english(
    draw: Callable[[str], Axes],
) -> None:
    labels = _tick_labels(draw("en"))
    assert "31.5" in labels, labels
    assert all("," not in label for label in labels), labels
