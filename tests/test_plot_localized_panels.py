#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every panel a plot function builds writes its numbers in the caller's language.

``localize_axes`` is the last line of a plot function, and for years it was
handed one axes: the one the data was drawn on. A figure is rarely one axes.
A twin carries the second quantity, a colorbar carries the scale of a map, a
3-D panel has a ``z``, and each of them is a separate axes with a formatter of
its own. Those were left in English beside a panel already in Spanish, and the
mixture shipped: ``.github/images/rotorcraft_hemisphere_es.svg`` reads
``Nivel de fuente a 60 m [dB]`` over a scale numbered ``76.8 78.4 80.0``.

The other half was the scale test. ``localize_axes`` skipped any axis that was
not linear, on the argument that a logarithmic axis has been through
``format_frequency_axis`` and has no number left to reformat. That is true of a
frequency axis and of nothing else: a decade axis of distances given a plain
``ScalarFormatter`` writes ``0.10 1.00 10.00``, and a contour colorbar is
spaced by its own boundaries, so its scale reads "function" although its labels
are as numeric as any other. What decides it is the formatter, which these
tests pin from both sides: the numeric panels reach Spanish, and the pinned
frequency labels and category labels are left to the helper that writes them.

Each test reads the labels after a draw, because a tick label written by a
formatter does not exist until then.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import aircraft, emission, room, underwater
from phonometry._plot.geometry import emission as geometry_emission

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.axes import Axes


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _labels(axes: Axes, which: str = "y") -> list[str]:
    """The tick labels of *axes*, as a reader of the drawn figure sees them."""
    axes.figure.canvas.draw()
    axis = getattr(axes, f"{which}axis")
    return [t.get_text() for t in axis.get_ticklabels() if t.get_text()]


def _decimals(labels: list[str]) -> list[str]:
    """The labels that carry a decimal separator, which are the ones at stake."""
    return [s for s in labels if "," in s or "." in s]


def _panels(first: Axes) -> list[Axes]:
    """Every axes of the figure *first* belongs to, in the order it was built."""
    return list(first.figure.get_axes())


# ---------------------------------------------------------------------------
# A logarithmic axis whose labels are still numbers.
# ---------------------------------------------------------------------------
def _steady_field(language: str) -> Axes:
    result = room.steady_state_field(
        sound_power_level=90.0, surface_area=352.0, mean_absorption=0.15
    )
    return result.plot(language=language)


def test_a_log_distance_axis_reaches_spanish() -> None:
    """The decade axis of distances is logarithmic and numeric at once.

    ``0.10 1.00 10.00`` were written by a ``ScalarFormatter`` the plot installed
    on a log axis, so the scale test skipped them while the annotation beside
    them (``r_c = 1,11 m``) carried the comma: one figure, two separators.
    """
    labels = _decimals(_labels(_steady_field("es"), "x"))
    assert labels, "the axis should label at least one decade with a decimal"
    assert all("," in label and "." not in label for label in labels), labels


def test_the_log_distance_axis_is_unchanged_in_english() -> None:
    labels = _decimals(_labels(_steady_field("en"), "x"))
    assert labels
    assert all("." in label and "," not in label for label in labels), labels


# ---------------------------------------------------------------------------
# The twin axis, one per plot function that builds one.
# ---------------------------------------------------------------------------
def _ship_source_level(language: str) -> Axes:
    result = underwater.monopole_source_level(
        [150.0, 149.0, 148.0, 147.0, 146.0],
        [1000.0, 1250.0, 1600.0, 2000.0, 2500.0],
        draught=10.0,
    )
    return np.atleast_1d(result.plot(language=language))[0]


def test_a_twin_axis_reaches_spanish() -> None:
    """The right-hand scale is a second axes, and it was never localised.

    The surface correction of an ISO 17208-2 source level runs to three
    decimals, so the twin is where the English point shows first.
    """
    twin = _panels(_ship_source_level("es"))[1]
    labels = _decimals(_labels(twin))
    assert labels
    assert all("," in label and "." not in label for label in labels), labels


def test_the_twin_axis_is_unchanged_in_english() -> None:
    twin = _panels(_ship_source_level("en"))[1]
    labels = _decimals(_labels(twin))
    assert labels
    assert all("." in label and "," not in label for label in labels), labels


def test_every_twin_axis_of_the_field_indicators_reaches_spanish() -> None:
    """The dimensionless indicators ride on the twin of the level panel."""
    freqs = np.array([125.0, 250.0, 500.0, 1000.0])
    levels = np.tile(np.array([64.0, 66.0, 68.0, 70.0]), (10, 1))
    intensity = 1e-12 * 10.0 ** ((levels - np.array([10.5, 8.5, 6.0, 4.5])) / 10.0)
    result = emission.field_indicators(levels, intensity, freqs)
    twin = _panels(result.plot(language="es"))[1]
    labels = _decimals(_labels(twin))
    assert labels
    assert all("," in label and "." not in label for label in labels), labels


# ---------------------------------------------------------------------------
# The colorbar, which is an axes of the figure and not of the plot.
# ---------------------------------------------------------------------------
def _image_source(language: str) -> Axes:
    result = room.image_source_rir(
        dimensions=(6.2, 4.1, 2.8),
        source=(1.2, 1.0, 1.5),
        receiver=(4.0, 3.0, 1.2),
        absorption=0.25,
        max_order=3,
        fs=8000.0,
    )
    return np.atleast_1d(result.plot(language=language))[0]


def test_a_colorbar_reaches_spanish() -> None:
    """The reflection-order scale is drawn on an axes of its own."""
    colorbar = _panels(_image_source("es"))[1]
    labels = _decimals(_labels(colorbar))
    assert labels
    assert all("," in label and "." not in label for label in labels), labels


def test_the_colorbar_is_unchanged_in_english() -> None:
    colorbar = _panels(_image_source("en"))[1]
    labels = _decimals(_labels(colorbar))
    assert labels
    assert all("." in label and "," not in label for label in labels), labels


def test_a_contour_colorbar_reaches_spanish() -> None:
    """A contour colorbar is spaced by its boundaries, so its scale is not linear.

    Its labels are numbers all the same, which is why the formatter and not the
    scale is what decides whether they are localised.
    """
    powers = [8000.0, 12000.0]
    distances = [60.0, 120.0, 240.0, 480.0, 960.0]
    sel = [[98.0, 92.0, 86.0, 80.0, 74.0], [104.0, 98.0, 92.0, 86.0, 80.0]]
    lmax = [[94.0, 88.0, 82.0, 76.0, 70.0], [100.0, 94.0, 88.0, 82.0, 76.0]]
    xs = np.linspace(0.0, 9000.0, 12)
    path = np.column_stack(
        [
            xs,
            np.zeros_like(xs),
            np.clip((xs - 1500.0) * 0.11, 0.0, 2500.0),
            np.full_like(xs, 10000.0),
            np.full_like(xs, 82.3),
        ]
    )
    result = aircraft.noise_contour(
        path,
        powers,
        distances,
        sel,
        lmax,
        x=np.linspace(-1000.0, 9000.0, 14),
        y=np.linspace(-2000.0, 2000.0, 12),
    )
    figure = np.atleast_1d(result.plot(language="es"))[0].figure
    figure.canvas.draw()
    for axes in figure.get_axes()[1:]:
        labels = _decimals(_labels(axes))
        assert all("," in label and "." not in label for label in labels), labels


# ---------------------------------------------------------------------------
# The third axis of a 3-D panel.
# ---------------------------------------------------------------------------
def _microphone_positions(language: str) -> Axes:
    figure = plt.figure()
    axes = figure.add_subplot(projection="3d")
    positions = emission.precision_positions("hemisphere", count=20, radius=1.0)
    return geometry_emission.plot_microphone_positions(
        positions, ax=axes, radius=1.0, language=language
    )


def test_the_z_axis_of_a_3d_panel_reaches_spanish() -> None:
    """``x`` and ``y`` were localised and ``z`` was not, in the same drawing."""
    axes = _microphone_positions("es")
    for which in ("x", "y", "z"):
        labels = _decimals(_labels(axes, which))
        assert labels, which
        assert all("," in label and "." not in label for label in labels), (
            which,
            labels,
        )


def test_the_3d_panel_is_unchanged_in_english() -> None:
    axes = _microphone_positions("en")
    for which in ("x", "y", "z"):
        labels = _decimals(_labels(axes, which))
        assert labels, which
        assert all("." in label and "," not in label for label in labels), (
            which,
            labels,
        )


# ---------------------------------------------------------------------------
# What must stay as it is.
# ---------------------------------------------------------------------------
def test_a_pinned_frequency_axis_is_left_to_its_own_helper() -> None:
    """The octave centres are fixed strings, and overwriting them loses them.

    ``format_frequency_axis`` writes ``31,5`` itself from the language it is
    given. If ``localize_axes`` reformatted the axis, the labels would come back
    as the bare tick positions it locked them to.
    """
    freqs = np.array([31.5, 63.0, 125.0, 250.0, 500.0, 1000.0])
    result = underwater.monopole_source_level(
        [150.0, 149.0, 148.0, 147.0, 146.0, 145.0], freqs, draught=10.0
    )
    axes = np.atleast_1d(result.plot(language="es"))[0]
    assert "31,5" in _labels(axes, "x"), _labels(axes, "x")
