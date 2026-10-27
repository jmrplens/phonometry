#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A ``.plot()`` returns, for mypy too, the type the argument that decides it says.

A multi-panel plot draws one panel on the axes it is handed and returns that
axes, and without one makes a column of panels and returns a tuple of them;
a plot that draws on a polar axes returns ``PolarAxes``, always or for the
``view`` or ``quantity`` that chooses the polar panel. The overload heads say
which, so ``result.plot(ax=ax).set_title(...)`` needs no narrowing and
``top, bottom = result.plot()`` unpacks two axes. ``tests/test_result_plots.py``
holds every plot to its heads at run time; this file holds one plot of each
family to them for mypy, and it only holds them because CI type checks every
file in this directory alongside ``src`` and ``scripts``. A head that returns
the union again, or a polar plot typed plain ``Axes``, still runs, and fails
here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_type, cast

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.projections.polar import PolarAxes

from phonometry import electroacoustics, materials, metrology, psychoacoustics, room

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from numpy.typing import NDArray

_FS = 48000
_RNG = np.random.default_rng(20261027)


def _decay(seconds: float = 0.8, t60: float = 0.5) -> NDArray[np.float64]:
    """A noise burst decaying 60 dB in ``t60`` seconds."""
    t = np.arange(int(seconds * _FS)) / _FS
    burst: NDArray[np.float64] = np.exp(-3.0 * np.log(10.0) / t60 * t)
    return burst * _RNG.standard_normal(t.size)


def _polar(figure: Figure) -> PolarAxes:
    # matplotlib types a projected subplot as Axes; this one is polar.
    return cast("PolarAxes", figure.add_subplot(projection="polar"))


def test_a_two_panel_plot_returns_two_axes_or_the_one_it_was_handed() -> None:
    result = room.room_parameters(_decay(), _FS, limits=(250.0, 2000.0))
    top, bottom = result.plot()
    assert_type(top, Axes)
    assert_type(bottom, Axes)
    ax = plt.figure().add_subplot()
    drawn = result.plot(ax, language="es")
    assert_type(drawn, Axes)
    assert drawn is ax
    plt.close("all")


def test_a_three_panel_plot_returns_three_axes() -> None:
    x = _RNG.standard_normal(2**14)
    result = electroacoustics.transfer_function(x, np.roll(x, 3), _FS)
    panels = result.plot()
    assert_type(panels, tuple[Axes, Axes, Axes])
    assert len(panels) == 3
    plt.close("all")


def test_an_axes_that_may_be_none_gives_either() -> None:
    result = room.room_parameters(_decay(), _FS, limits=(250.0, 2000.0))
    maybe: Axes | None = None
    assert_type(result.plot(maybe), Axes | tuple[Axes, Axes])
    plt.close("all")


def test_the_excitation_helper_follows_its_axes() -> None:
    sweep = room.sweep_signal(_FS, 100.0, 4000.0, 0.1)
    assert_type(room.plot_excitation(sweep, _FS), tuple[Axes, Axes])
    ax = plt.figure().add_subplot()
    assert_type(room.plot_excitation(sweep, _FS, ax=ax), Axes)
    plt.close("all")


def test_zwicker_loudness_keeps_the_union_the_data_decide() -> None:
    noise = 0.02 * _RNG.standard_normal(_FS)
    result = psychoacoustics.loudness_zwicker(noise, _FS, stationary=False)
    drawn = result.plot()
    assert_type(drawn, Axes | tuple[Axes, Axes])
    assert isinstance(drawn, tuple)
    ax = plt.figure().add_subplot()
    assert_type(result.plot(ax), Axes)
    plt.close("all")


def test_a_plot_that_needs_a_polar_axes_returns_one() -> None:
    result = electroacoustics.piston_directivity_pattern([3.0, 8.0])
    drawn = result.plot()
    assert_type(drawn, PolarAxes)
    assert drawn.name == "polar"
    polar = _polar(plt.figure())
    assert_type(result.plot(polar), PolarAxes)
    plt.close("all")


def test_a_plot_polar_only_without_axes_returns_what_it_is_handed() -> None:
    result = materials.directional_diffusion([-30.0, 0.0, 30.0], [70.0, 72.0, 69.0])
    assert_type(result.plot(), PolarAxes)
    ax = plt.figure().add_subplot()
    assert_type(result.plot(ax), Axes)
    plt.close("all")


def test_a_plot_whose_view_chooses_the_projection_returns_its_axes() -> None:
    phi = np.radians(np.arange(36) * 10.0)
    levels = 94.0 + 20.0 * np.log10(0.6 + 0.4 * np.cos(phi))
    result = metrology.directivity_factor(np.vstack((levels, levels)))
    response = result.plot()
    assert_type(response, PolarAxes)
    assert response.name == "polar"
    weights = result.plot(view="weights")
    assert_type(weights, Axes)
    assert weights.name == "rectilinear"
    plt.close("all")
