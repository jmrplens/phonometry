#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The frequency ticks of the noise-control renderers reach Spanish.

``localize_axes`` cannot reach tick labels installed as fixed strings, so the
band-centre labels of a continuous frequency axis are written by
``format_frequency_axis`` and by nothing else: a renderer that does not hand
its ``language`` down draws 31.5 on a Spanish figure where 31,5 belongs. Every
range here reaches down to 31,5 Hz, the lowest octave centre whose label
carries a decimal, because a set of labels without one proves nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

from phonometry import noise_control

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.axes import Axes

    from phonometry.noise_control.duct_path import DuctPathResult
    from phonometry.noise_control.enclosures import EnclosureResult
    from phonometry.noise_control.hvac import HvacSpectrumResult
    from phonometry.noise_control.room_to_room import RoomToRoomResult
    from phonometry.noise_control.silencers import ReactiveSilencerResult

#: Octave bands from 31,5 Hz up; eight of them, as every spectrum below.
_BANDS = np.array([31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


class _Plottable(Protocol):
    def plot(self, ax: Axes | None = None, *, language: str = "en") -> Axes: ...


def _reactive_silencer() -> ReactiveSilencerResult:
    # The chamber cuts on at 891 Hz, so the sweep stays in the plane-wave range.
    return noise_control.expansion_chamber(
        np.geomspace(20.0, 800.0, 200), 0.3, 0.04, 0.01
    )


def _hvac_spectrum() -> HvacSpectrumResult:
    return noise_control.end_reflection_loss(_BANDS, 0.3)


def _duct_path() -> DuctPathResult:
    return noise_control.duct_path(
        _BANDS,
        [92.0, 90.0, 86.0, 82.0, 79.0, 77.0, 75.0, 71.0],
        [noise_control.DuctElement("Duct", 3.0)],
    )


def _room_to_room() -> RoomToRoomResult:
    return noise_control.room_to_room_transmission(
        _BANDS,
        40.0,
        20.0,
        np.full(_BANDS.size, 20.0),
        source=noise_control.SourceRoom(level=np.full(_BANDS.size, 90.0)),
    )


def _enclosure() -> EnclosureResult:
    return noise_control.enclosure_insertion_loss(
        np.linspace(15.0, 50.0, _BANDS.size), 6.0, 5.0, 0.3, frequencies=_BANDS
    )


_CASES = [
    pytest.param(_reactive_silencer, id="reactive_silencer"),
    pytest.param(_hvac_spectrum, id="hvac_spectrum"),
    pytest.param(_duct_path, id="duct_path"),
    pytest.param(_room_to_room, id="room_to_room"),
    pytest.param(_enclosure, id="enclosure"),
]


def _frequency_tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


@pytest.mark.parametrize("build", _CASES)
def test_the_frequency_ticks_reach_spanish(build: Callable[[], _Plottable]) -> None:
    labels = _frequency_tick_labels(build().plot(language="es"))
    plt.close("all")
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("build", _CASES)
def test_the_frequency_ticks_are_unchanged_in_english(
    build: Callable[[], _Plottable],
) -> None:
    labels = _frequency_tick_labels(build().plot(language="en"))
    plt.close("all")
    assert "31.5" in labels, labels


def _room_to_room_axes(language: str) -> tuple[Axes, Axes]:
    ax = _room_to_room().plot(language=language)
    (twin,) = (other for other in ax.figure.axes if other is not ax)
    return ax, twin


def test_the_room_to_room_twin_axis_reaches_spanish() -> None:
    """The twin is formatted last, and it shares the frequency axis.

    ``twinx`` builds a second axes on the same x-axis, so formatting the twin
    rewrites the labels of the first: one call that forgets the language
    leaves 31.5 on both, whatever the call before it was told.
    """
    ax, twin = _room_to_room_axes("es")
    labels = {"axes": _frequency_tick_labels(ax), "twin": _frequency_tick_labels(twin)}
    plt.close("all")
    for side in labels.values():
        assert "31,5" in side, labels
        assert all("." not in label for label in side), labels


def test_the_room_to_room_twin_axis_is_unchanged_in_english() -> None:
    ax, twin = _room_to_room_axes("en")
    labels = {"axes": _frequency_tick_labels(ax), "twin": _frequency_tick_labels(twin)}
    plt.close("all")
    for side in labels.values():
        assert "31.5" in side, labels
