#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A window is a name or a tuple of a name and its parameters, everywhere.

Every function that hands its ``window`` to :func:`scipy.signal.get_window`
(or to a Welch estimator that does) takes ``("kaiser", 8.6)`` as it takes
``"hann"``; nineteen of them were annotated ``str``, so a type checker
refused the tuple the call ran with. ``("general_cosine", [0.5, 0.5])`` is
the Hann window spelt as its cosine weights, so each function must give with
it what it gives with ``"hann"``: the tuple reaches the window, and is not
dropped on the way. A record that stores the window holds the tuple, a list
of weights as a tuple and an array of them as a read-only copy, so editing
the caller's weights afterwards does not rename the window it was computed
with. ``scripts/check_parameter_annotations.py`` holds every parameter that
reaches a window reader of SciPy to the annotation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry import electroacoustics, signals

if TYPE_CHECKING:
    from collections.abc import Callable

    from phonometry._internal.types import WindowSpec

_FS = 48000.0
_T = np.arange(int(_FS)) / _FS
_RNG = np.random.default_rng(7)
_NOISE = _RNG.standard_normal(_T.size)
_OTHER = _RNG.standard_normal(_T.size)
_DELAYED = np.roll(_NOISE, 5) + 0.1 * _RNG.standard_normal(_T.size)
_TONE = np.sin(2 * np.pi * 1000 * _T) + 0.01 * np.sin(2 * np.pi * 2000 * _T)
_TWO_TONE = (
    np.sin(2 * np.pi * 60 * _T)
    + 0.25 * np.sin(2 * np.pi * 7000 * _T)
    + 1e-3 * np.sin(2 * np.pi * 7060 * _T)
)
_CCIF = np.sin(2 * np.pi * 8000 * _T) + np.sin(2 * np.pi * 11950 * _T)
_DIM = np.sin(2 * np.pi * 15000 * _T) + np.sign(np.sin(2 * np.pi * 3150 * _T))
_AM = (1 + 0.5 * np.sin(2 * np.pi * 7 * _T)) * np.sin(2 * np.pi * 2000 * _T)

#: The Hann window spelt as the weights of a general cosine window.
_HANN_AS_COSINE: WindowSpec = ("general_cosine", [0.5, 0.5])


def _array(value: object) -> np.ndarray:
    return np.asarray(value, dtype=np.float64)


#: Each function that takes a window, with what it gives back to compare.
_CASES: dict[str, Callable[[WindowSpec], Any]] = {
    "power_spectral_density": lambda w: signals.power_spectral_density(
        _NOISE, _FS, window=w
    ),
    "cross_spectral_density": lambda w: signals.cross_spectral_density(
        _NOISE, _DELAYED, _FS, window=w
    ),
    "coherent_output_spectrum": lambda w: signals.coherent_output_spectrum(
        _NOISE, _DELAYED, _FS, window=w
    ),
    "miso_coherence": lambda w: signals.miso_coherence(
        [_NOISE, _OTHER], _DELAYED + 0.5 * _OTHER, _FS, window=w
    ),
    "spectrogram": lambda w: signals.spectrogram(_NOISE, _FS, window=w),
    "zoom_fft": lambda w: signals.zoom_fft(
        _TONE, _FS, f_min=900.0, f_max=1100.0, window=w
    ),
    "envelope_spectrum": lambda w: signals.envelope_spectrum(_AM, _FS, window=w),
    "time_delay": lambda w: signals.time_delay(_NOISE, _DELAYED, _FS, window=w),
    "harmonic_analysis": lambda w: electroacoustics.harmonic_analysis(
        _TONE, _FS, window=w
    ),
    "harmonic_distortion": lambda w: electroacoustics.harmonic_distortion(
        _TONE, _FS, fundamental=1000.0, order=2, window=w
    ),
    "sinad": lambda w: electroacoustics.sinad(_TONE, _FS, window=w),
    "thd_plus_noise": lambda w: electroacoustics.thd_plus_noise(_TONE, _FS, window=w),
    "thd": lambda w: electroacoustics.thd(_TONE, _FS, 1000.0, window=w),
    "weighted_thd": lambda w: electroacoustics.weighted_thd(_TONE, _FS, window=w),
    "difference_frequency_distortion": lambda w: (
        electroacoustics.difference_frequency_distortion(
            _CCIF, _FS, f1=8000.0, f2=11950.0, window=w
        )
    ),
    "dynamic_intermodulation_distortion": lambda w: (
        electroacoustics.dynamic_intermodulation_distortion(_DIM, _FS, window=w)
    ),
    "modulation_distortion": lambda w: electroacoustics.modulation_distortion(
        _TWO_TONE, _FS, f_low=60.0, f_high=7000.0, window=w
    ),
    "total_difference_frequency_distortion": lambda w: (
        electroacoustics.total_difference_frequency_distortion(_CCIF, _FS, window=w)
    ),
    "dynamic_range": lambda w: electroacoustics.dynamic_range(_TONE, _FS, window=w),
}

#: The number each result is compared by.
_READS: dict[str, Callable[[Any], np.ndarray]] = {
    "power_spectral_density": lambda r: _array(r.psd),
    "cross_spectral_density": lambda r: _array(r.magnitude),
    "coherent_output_spectrum": lambda r: _array(r.coherent_psd),
    "miso_coherence": lambda r: _array(r.multiple_coherence),
    "spectrogram": lambda r: _array(r.power),
    "zoom_fft": lambda r: _array(r.amplitude),
    "envelope_spectrum": lambda r: _array(r.amplitude),
    "time_delay": lambda r: _array(r.delay),
    "harmonic_analysis": lambda r: _array(r.harmonic_amplitudes),
    "modulation_distortion": lambda r: _array(r.sideband_amplitudes),
}


@pytest.mark.parametrize("name", sorted(_CASES))
def test_a_window_given_by_its_parameters_is_the_window_it_names(name: str) -> None:
    """The cosine weights of Hann give what the name ``"hann"`` gives."""
    call = _CASES[name]
    read: Callable[[Any], np.ndarray] = _READS.get(name, _array)
    by_name = read(call("hann"))
    by_weights = read(call(_HANN_AS_COSINE))
    np.testing.assert_allclose(by_weights, by_name, rtol=1e-9, atol=1e-12)
    kaiser = read(call(("kaiser", 8.6)))
    assert np.all(np.isfinite(kaiser))


#: The functions whose result stores the window it was computed with.
_STORED = sorted(
    {
        "power_spectral_density",
        "cross_spectral_density",
        "coherent_output_spectrum",
        "miso_coherence",
        "spectrogram",
        "zoom_fft",
        "envelope_spectrum",
    }
)


@pytest.mark.parametrize("name", _STORED)
def test_a_result_holds_the_window_with_parameters_of_its_own(name: str) -> None:
    """A list of weights is held as a tuple, an array as a read-only copy."""
    call = _CASES[name]
    assert call("hann").window == "hann"
    assert call(("kaiser", 8.6)).window == ("kaiser", 8.6)
    assert call(_HANN_AS_COSINE).window == ("general_cosine", (0.5, 0.5))
    weights = np.array([0.5, 0.5])
    held = call(("general_cosine", weights)).window
    weights[0] = 0.1
    assert isinstance(held, tuple)
    assert not held[1].flags.writeable
    np.testing.assert_array_equal(held[1], [0.5, 0.5])
