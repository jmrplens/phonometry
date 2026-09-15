#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The frequency ticks of the signal renderers reach Spanish.

``localize_axes`` cannot reach tick labels installed as fixed strings, so the
band-centre labels of a continuous frequency axis are written by
``format_frequency_axis`` and by nothing else: a renderer that does not hand
its ``language`` down draws 31.5 on a Spanish figure where 31,5 belongs. Every
range here reaches down past 31,5 Hz, the lowest octave centre whose label
carries a decimal, because a set of labels without one proves nothing.

The multi-panel renderers format the axis from two places, once for the panel
drawn on the caller's axes and once per panel of their own figure, so both
paths are drawn.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

    from phonometry.signals.inversion import InverseFilterResult
    from phonometry.signals.miso import MISOCoherenceResult
    from phonometry.signals.multitaper import MultitaperSpectralDensityResult
    from phonometry.signals.phase import PhaseDecompositionResult
    from phonometry.signals.spectra import (
        CoherentOutputSpectrumResult,
        CrossSpectralDensityResult,
        SpectralDensityResult,
    )
    from phonometry.signals.test_signals import ResampledSignalResult

    Drawn = Axes | NDArray[Any]


class _Plottable(Protocol):
    def plot(self, ax: Axes | None = None, *, language: str = "en") -> Drawn: ...


#: A sampling rate low enough that a 1024-sample segment resolves 7,8 Hz, so
#: every spectrum below starts under the 31,5 Hz octave centre.
FS = 8000.0
NPERSEG = 1024


def _white(seed: int, n: int = 8192) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(n)


def _spectral_density() -> SpectralDensityResult:
    return ph.signals.power_spectral_density(_white(1), FS, nperseg=NPERSEG)


def _multitaper_spectral_density() -> MultitaperSpectralDensityResult:
    return ph.signals.multitaper_psd(_white(2, 4096), FS)


def _cross_spectral_density() -> CrossSpectralDensityResult:
    x = _white(3)
    return ph.signals.cross_spectral_density(
        x, np.roll(x, 5) + 0.1 * _white(4), FS, nperseg=NPERSEG
    )


def _coherent_output_spectrum() -> CoherentOutputSpectrumResult:
    x = _white(5)
    return ph.signals.coherent_output_spectrum(
        x, np.roll(x, 5) + 0.1 * _white(6), FS, nperseg=NPERSEG
    )


def _miso_coherence() -> MISOCoherenceResult:
    x1, x2 = _white(7), _white(8)
    return ph.signals.miso_coherence(
        [x1, x2], x1 + 0.5 * x2 + 0.1 * _white(9), FS, nperseg=NPERSEG
    )


def _phase_decomposition() -> PhaseDecompositionResult:
    response = np.fft.rfft(np.exp(-np.arange(1024) / 50.0))
    return ph.signals.phase_decomposition(response, fs=FS)


def _resampled_signal() -> ResampledSignalResult:
    # 4 kHz down to 200 Hz puts the stopband edge at 100 Hz, and the view runs
    # from an eighth of it (12,5 Hz) to four times it.
    return ph.signals.resample_signal(
        ph.signals.noise_signal(4000.0, 1.0, seed=5), 4000.0, fs_new=200.0
    )


def _inverse_filter() -> InverseFilterResult:
    from scipy import signal as sg

    b, a = sg.butter(2, [50.0, 3000.0], btype="bandpass", fs=FS)
    impulse = np.zeros(1024)
    impulse[0] = 1.0
    return ph.signals.regularized_inverse_filter(
        sg.lfilter(b, a, impulse), FS, f_range=(100.0, 2000.0)
    )


def _own_figure(build: Callable[[], _Plottable]) -> Callable[[str], Drawn]:
    return lambda language: build().plot(language=language)


def _on_axes(build: Callable[[], _Plottable]) -> Callable[[str], Drawn]:
    def draw(language: str) -> Drawn:
        _fig, ax = plt.subplots()
        return build().plot(ax=ax, language=language)

    return draw


_CASES = [
    pytest.param(_own_figure(_spectral_density), id="spectral_density"),
    pytest.param(
        _own_figure(_multitaper_spectral_density), id="multitaper_spectral_density"
    ),
    pytest.param(_own_figure(_cross_spectral_density), id="cross_spectral_density"),
    pytest.param(
        _on_axes(_cross_spectral_density), id="cross_spectral_density-on-axes"
    ),
    pytest.param(_own_figure(_coherent_output_spectrum), id="coherent_output_spectrum"),
    pytest.param(
        _on_axes(_coherent_output_spectrum), id="coherent_output_spectrum-on-axes"
    ),
    pytest.param(_own_figure(_miso_coherence), id="miso_coherence"),
    pytest.param(_on_axes(_miso_coherence), id="miso_coherence-on-axes"),
    pytest.param(_own_figure(_phase_decomposition), id="phase_decomposition"),
    pytest.param(_on_axes(_phase_decomposition), id="phase_decomposition-on-axes"),
    pytest.param(_own_figure(_resampled_signal), id="resampled_signal"),
    pytest.param(_own_figure(_inverse_filter), id="inverse_filter"),
]


def _frequency_tick_labels(drawn: Drawn) -> list[str]:
    """Every non-empty x tick label of the panels a renderer returned.

    A column of panels shares one frequency axis and only the bottom panel
    shows its labels, so the panels are read together.
    """
    axes = drawn.ravel() if isinstance(drawn, np.ndarray) else [drawn]
    return [t.get_text() for ax in axes for t in ax.get_xticklabels() if t.get_text()]


@pytest.mark.parametrize("draw", _CASES)
def test_the_frequency_ticks_reach_spanish(draw: Callable[[str], Drawn]) -> None:
    labels = _frequency_tick_labels(draw("es"))
    plt.close("all")
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _CASES)
def test_the_frequency_ticks_are_unchanged_in_english(
    draw: Callable[[str], Drawn],
) -> None:
    labels = _frequency_tick_labels(draw("en"))
    plt.close("all")
    assert "31.5" in labels, labels
