#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the room figures follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, and it cannot reach a label installed as a fixed string, so the
frequencies of these figures are written by ``format_frequency_axis``
(continuous axes) or ``_format_freq`` (band categories, titles and legend
entries) and by nothing else: a renderer that does not pass its ``language`` on
draws ``31.5`` or ``1.25k`` in a Spanish figure. Every figure below carries
such a frequency, because a label without a decimal proves nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import room
from phonometry.room import noise_criteria

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def _legend_texts(ax: Axes) -> list[str]:
    legend = ax.get_legend()
    return [] if legend is None else [t.get_text() for t in legend.get_texts()]


def _band_categories(language: str) -> Axes:
    """The third-octave band axis of the ISO 3382 decay-time figure."""
    n = 3
    result = room.RoomAcousticsResult(
        frequency=np.array([1000.0, 1250.0, 1600.0]),
        edt=np.full(n, 0.6),
        t20=np.full(n, 0.6),
        t30=np.full(n, 0.6),
        c50=np.zeros(n),
        c80=np.zeros(n),
        d50=np.full(n, 0.5),
        ts=np.full(n, 0.1),
        dynamic_range=np.full(n, 60.0),
        edt_valid=np.ones(n, dtype=bool),
        t20_valid=np.ones(n, dtype=bool),
        t30_valid=np.ones(n, dtype=bool),
        curvature=np.zeros(n),
    )
    # The two panels share the band axis; the lower one carries its labels.
    return result.plot(language=language)[-1]


def _mls_spectrum(language: str) -> Axes:
    # A 1023-sample MLS at 8 kHz spans 7.8 Hz to 4 kHz on its spectrum panel.
    axes = room.plot_excitation(
        room.mls_signal(10), 8000, kind="mls", language=language
    )
    return axes[1]


def _shaped_sweep_spectrum(language: str) -> Axes:
    # The spectrum panel runs from a quarter of f1 (25 Hz) to twice f2.
    result = room.shaped_sweep_signal(48000, 100.0, 5000.0, 0.4, target="pink")
    return result.plot(language=language)[1]


_CONTINUOUS: list[Callable[[str], Axes]] = [_mls_spectrum, _shaped_sweep_spectrum]


@pytest.mark.parametrize("draw", _CONTINUOUS, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_axis_reaches_spanish(draw: Callable[[str], Axes]) -> None:
    labels = _tick_labels(draw("es"))
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _CONTINUOUS, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_axis_is_unchanged_in_english(
    draw: Callable[[str], Axes],
) -> None:
    labels = _tick_labels(draw("en"))
    assert "31.5" in labels, labels
    assert all("," not in label for label in labels), labels


def test_the_band_categories_reach_spanish() -> None:
    assert _tick_labels(_band_categories("es")) == ["1k", "1,25k", "1,6k"]


def test_the_band_categories_are_unchanged_in_english() -> None:
    assert _tick_labels(_band_categories("en")) == ["1k", "1.25k", "1.6k"]


def _decay_title(language: str) -> str:
    time = np.linspace(0.0, 1.0, 100)
    curve = room.DecayCurve(time=time, level=-60.0 * time, band=1250.0)
    return curve.plot(language=language).get_title()


def test_the_decay_curve_band_reaches_spanish() -> None:
    assert _decay_title("es").endswith("(banda 1,25k Hz)")


def test_the_decay_curve_band_is_unchanged_in_english() -> None:
    assert _decay_title("en").endswith("(1.25k Hz band)")


def _nc_31_5() -> noise_criteria.NCResult:
    """An NC-40 spectrum raised 10 dB at 31,5 Hz, which becomes the tangent band.

    The tangency then falls between two curves of the family, so the rating is
    interpolated and carries a decimal of its own.
    """
    levels = noise_criteria.nc_curve(40.0).copy()
    levels[list(noise_criteria.OCTAVE_BANDS).index(31.5)] += 10.0
    result = noise_criteria.noise_criterion(levels)
    assert result.governing_frequency == pytest.approx(31.5)
    return result


def test_the_governing_band_and_designation_reach_spanish() -> None:
    ax = _nc_31_5().plot(language="es")
    assert "Banda dominante (31,5)" in _legend_texts(ax)
    title = ax.get_title()
    assert title.startswith("ANSI/ASA S12.2 NC-"), title
    assert title.endswith("(31,5 Hz)"), title
    assert "." not in title.removeprefix("ANSI/ASA S12.2"), title


def test_the_governing_band_and_designation_are_unchanged_in_english() -> None:
    result = _nc_31_5()
    ax = result.plot(language="en")
    assert "Governing band (31.5)" in _legend_texts(ax)
    assert ax.get_title() == f"ANSI/ASA S12.2 {result.label}"
