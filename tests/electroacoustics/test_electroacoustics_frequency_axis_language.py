#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency axis of the electroacoustics figures follows the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels of a continuous frequency axis are written
by ``format_frequency_axis`` and by nothing else: a renderer that does not pass
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

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes

FS = 48000


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def _frequency_response() -> ph.electroacoustics.FrequencyResponseResult:
    x = np.random.default_rng(20260915).standard_normal(2**15)
    y = np.convolve(x, np.array([0.5, 0.3, 0.1]), mode="same")
    return ph.electroacoustics.transfer_function(x, y, FS)


def _frequency_response_panels(language: str) -> list[Axes]:
    axes = _frequency_response().plot(language=language)
    assert isinstance(axes, np.ndarray)
    # The three panels share one x-axis, and its labels sit under the last.
    return [axes[-1]]


def _frequency_response_on_given_axes(language: str) -> list[Axes]:
    _fig, ax = plt.subplots()
    drawn = _frequency_response().plot(ax=ax, language=language)
    assert not isinstance(drawn, np.ndarray)
    return [drawn]


def _swept_sine() -> ph.electroacoustics.SweptSineDistortionResult:
    # The sweep starts at 20 Hz so that both panels reach the 31,5 Hz label.
    f1, f2, seconds = 20.0, 8000.0, 1.0
    sweep = ph.electroacoustics.synchronized_sweep_signal(FS, f1, f2, seconds)
    return ph.electroacoustics.swept_sine_distortion(
        sweep + 0.01 * sweep**2, FS, f1=f1, f2=f2, seconds=seconds, n_harmonics=3
    )


def _swept_sine_panels(language: str) -> list[Axes]:
    axes = _swept_sine().plot(language=language)
    assert isinstance(axes, np.ndarray)
    return list(axes)


def _swept_sine_on_given_axes(language: str) -> list[Axes]:
    _fig, ax = plt.subplots()
    drawn = _swept_sine().plot(ax=ax, language=language)
    assert not isinstance(drawn, np.ndarray)
    return [drawn]


def _loudspeaker() -> ph.electroacoustics.LoudspeakerCharacteristics:
    f = np.geomspace(20.0, 24000.0, 200)
    spl = (
        87.0
        - 10 * np.log10(1 + (50.0 / f) ** 6)
        - 10 * np.log10(1 + (f / 16000.0) ** 7)
    )
    fz = np.geomspace(20.0, 20000.0, 120)
    return ph.electroacoustics.loudspeaker_characteristics(
        f,
        spl,
        8.0,
        sensitivity_band=(200.0, 4000.0),
        impedance=(fz, 6.6 + 20 * np.exp(-(np.log2(fz / 52.0) ** 2) / 0.12)),
        distortion=(np.geomspace(25.0, 5000.0, 90), 0.4 + 2.0 * np.ones(90)),
    )


def _microphone() -> ph.electroacoustics.MicrophoneCharacteristics:
    f = np.geomspace(20.0, 20000.0, 200)
    response = -10 * np.log10(1 + (30.0 / f) ** 4) - 10 * np.log10(
        1 + (f / 19000.0) ** 8
    )
    return ph.electroacoustics.microphone_characteristics(
        f,
        response,
        12.5,
        tolerance_db=3.0,
        noise=ph.electroacoustics.MicrophoneNoise(
            voltage=1.25e-6,
            spectrum=(np.geomspace(20.0, 20000.0, 31), np.full(31, 10.0)),
        ),
    )


def _datasheet_panel(
    build: Callable[[], ph.electroacoustics.LoudspeakerCharacteristics]
    | Callable[[], ph.electroacoustics.MicrophoneCharacteristics],
    quantity: str,
) -> Callable[[str], list[Axes]]:
    def draw(language: str) -> list[Axes]:
        return [build().plot(quantity=quantity, language=language)]

    return draw


_FIGURES = [
    pytest.param(_frequency_response_panels, id="frequency-response"),
    pytest.param(_frequency_response_on_given_axes, id="frequency-response-ax"),
    pytest.param(_swept_sine_panels, id="swept-sine"),
    pytest.param(_swept_sine_on_given_axes, id="swept-sine-ax"),
    pytest.param(_datasheet_panel(_loudspeaker, "response"), id="loudspeaker-response"),
    pytest.param(
        _datasheet_panel(_loudspeaker, "impedance"), id="loudspeaker-impedance"
    ),
    pytest.param(_datasheet_panel(_loudspeaker, "thd"), id="loudspeaker-thd"),
    pytest.param(_datasheet_panel(_microphone, "response"), id="microphone-response"),
    pytest.param(_datasheet_panel(_microphone, "noise"), id="microphone-noise"),
]


@pytest.mark.parametrize("draw", _FIGURES)
def test_the_frequency_axis_reaches_spanish(
    draw: Callable[[str], list[Axes]],
) -> None:
    for ax in draw("es"):
        labels = _tick_labels(ax)
        assert any("," in label for label in labels), labels
        assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _FIGURES)
def test_the_frequency_axis_is_unchanged_in_english(
    draw: Callable[[str], list[Axes]],
) -> None:
    for ax in draw("en"):
        labels = _tick_labels(ax)
        assert any("." in label for label in labels), labels
        assert all("," not in label for label in labels), labels


def _harmonic_title(language: str) -> str:
    t = np.arange(FS) / FS
    tone = np.sin(2 * np.pi * 62.5 * t) + 0.03 * np.sin(2 * np.pi * 125.0 * t)
    result = ph.electroacoustics.harmonic_analysis(tone, FS, 62.5)
    return result.plot(language=language).get_title()


def _modulation_title(language: str) -> str:
    t = np.arange(FS) / FS
    x = (
        np.sin(2 * np.pi * 62.5 * t)
        + 0.25 * np.sin(2 * np.pi * 8000.0 * t)
        + 0.02 * np.sin(2 * np.pi * 8062.5 * t)
        + 0.02 * np.sin(2 * np.pi * 7937.5 * t)
    )
    result = ph.electroacoustics.modulation_distortion(x, FS, f_low=62.5, f_high=8000.0)
    return result.plot(language=language).get_title()


@pytest.mark.parametrize(
    "title",
    [
        pytest.param(_harmonic_title, id="harmonic-distortion"),
        pytest.param(_modulation_title, id="modulation-distortion"),
    ],
)
def test_the_title_frequency_follows_the_language(
    title: Callable[[str], str],
) -> None:
    """The tone frequency in the title is a mathtext string, out of the comma pass."""
    assert "$f_1$ = 62,5Hz" in title("es")
    assert "$f_1$ = 62.5Hz" in title("en")
