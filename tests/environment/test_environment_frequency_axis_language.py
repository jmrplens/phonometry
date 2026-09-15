#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the ISO 9613-1 attenuation figure follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels are written by ``format_frequency_axis``
and by nothing else: a renderer that does not pass its ``language`` on draws
``31.5`` in a Spanish figure. The curve below starts at 31,5 Hz, the lowest
octave centre whose label carries a decimal, because a label without one proves
nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import pytest

from phonometry.environment import AtmosphericAbsorptionWarning
from phonometry.environment.propagation.air_absorption import atmospheric_attenuation

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.axes import Axes


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(language: str) -> list[str]:
    # 31,5 Hz is below the 50 Hz start of Table 1, and the result warns about it.
    with pytest.warns(AtmosphericAbsorptionWarning, match="tabulated range"):
        result = atmospheric_attenuation([31.5, 63.0, 125.0, 250.0, 500.0])
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
