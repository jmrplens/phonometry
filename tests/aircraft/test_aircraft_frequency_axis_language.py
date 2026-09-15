#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the SAE ARP 5534 band-attenuation figure follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels are written by ``format_frequency_axis``
and by nothing else: a renderer that does not pass its ``language`` on draws
``31.5`` in a Spanish figure. The bands below span 31,5 Hz, the lowest octave
centre whose label carries a decimal, because a label without one proves
nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import pytest

from phonometry.aircraft.atmospheric_absorption import sae_band_attenuation
from phonometry.environment import AtmosphericAbsorptionWarning

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.axes import Axes

_THIRDS = [25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0]


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(language: str) -> list[str]:
    # The bands below 50 Hz are outside ISO 9613-1 Table 1, and the result says so.
    with pytest.warns(AtmosphericAbsorptionWarning, match="tabulated range"):
        result = sae_band_attenuation(_THIRDS, 500.0)
    ax: Axes = result.plot(language=language)
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def test_the_frequency_labels_reach_spanish() -> None:
    labels = _tick_labels("es")
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


def test_the_frequency_labels_are_unchanged_in_english() -> None:
    labels = _tick_labels("en")
    assert "31.5" in labels, labels
    assert all("," not in label for label in labels), labels
