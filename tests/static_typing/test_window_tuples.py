#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A window takes its parameters, for mypy too.

``scipy.signal.get_window`` reads ``("kaiser", 8.6)`` as it reads
``"hann"``, and so does every function of the package that hands its
``window`` to it or to a Welch estimator. These parameters were annotated
``str``, so a type checker refused the tuple the call ran with. CI type
checks every file in this directory alongside ``src`` and ``scripts``;
``scripts/check_parameter_annotations.py`` holds every such parameter to the
annotation.
"""

from __future__ import annotations

import numpy as np

from phonometry import electroacoustics, signals

_FS = 48000.0
_T = np.arange(int(_FS)) / _FS
_TONE = np.sin(2 * np.pi * 1000 * _T) + 0.01 * np.sin(2 * np.pi * 2000 * _T)
_NOISE = np.random.default_rng(3).standard_normal(_T.size)


def test_a_welch_estimate_with_a_kaiser_window() -> None:
    """The Welch estimators and the spectrogram take a window with its beta."""
    psd = signals.power_spectral_density(_NOISE, _FS, window=("kaiser", 8.6))
    assert psd.window == ("kaiser", 8.6)
    csd = signals.cross_spectral_density(_NOISE, _NOISE, _FS, window=("tukey", 0.5))
    assert np.all(csd.coherence > 0.99)
    frames = signals.spectrogram(_NOISE, _FS, window=("general_cosine", [0.5, 0.5]))
    assert frames.window == ("general_cosine", (0.5, 0.5))


def test_a_distortion_reading_with_a_flat_top_window() -> None:
    """A harmonic read through a window given with its parameters."""
    weights = np.array([0.2156, 0.4160, 0.2781, 0.0836, 0.0069])
    ratio = electroacoustics.thd(_TONE, _FS, 1000.0, window=("general_cosine", weights))
    assert 0.005 < ratio < 0.02
