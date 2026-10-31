#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every function whose sample rate is annotated ``float`` runs at a fractional rate.

The rate of these functions was annotated ``int`` while any positive number
ran, so the ``float`` rate ``signals.resample_signal`` returns, or the one a
Signal holds, was a type error the call did not raise. Each is called here at
48000.5 Hz, the rate its annotation now says it takes. The functions that
need a whole number of samples per second (the test-signal generators,
``loudness_zwicker`` and the functions that resample by an integer ratio)
keep ``int | np.integer[Any]`` and refuse it, and
``scripts/check_parameter_annotations.py`` lists them with their reason;
``io.write`` takes ``float | np.integer[Any] | None``, since every Signal
reaches it, and refuses a fraction when the call runs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import numpy as np
import pytest

from phonometry import (
    electroacoustics,
    emission,
    filters,
    io,
    metrology,
    psychoacoustics,
    room,
    signals,
    speech,
)

if TYPE_CHECKING:
    from collections.abc import Callable

mpl.use("Agg")

FS = 48000.5
_RNG = np.random.default_rng(20261027)
_X = _RNG.standard_normal(int(FS))
_TONE = np.sin(2.0 * np.pi * 1000.0 * np.arange(int(FS)) / FS)
_DECAY = np.exp(-np.arange(int(1.5 * FS)) / (0.1 * FS))
_IR = _DECAY * _RNG.standard_normal(_DECAY.size)
_MLS = room.mls_signal(12)
_GOLAY = room.golay_pair(10)


def _plot_excitation() -> object:
    import matplotlib.pyplot as plt

    ax = room.plot_excitation(room.sweep_signal(FS, 100.0, 1000.0, 0.2), FS)
    plt.close("all")
    return ax


_CALLS: dict[str, Callable[[], object]] = {
    "room.plot_excitation": _plot_excitation,
    "electroacoustics.check_limiting_test_signal": lambda: (
        electroacoustics.check_limiting_test_signal(_X, FS)
    ),
    "electroacoustics.synchronized_sweep_signal": lambda: (
        electroacoustics.synchronized_sweep_signal(FS, 100.0, 1000.0, 0.5)
    ),
    "emission.sound_intensity": lambda: emission.sound_intensity(
        _X, 0.9 * _X, FS, spacing_m=0.012
    ),
    "filters.OctaveFilterBank": lambda: filters.OctaveFilterBank(FS).filter(_X),
    "filters.octave_filter": lambda: filters.octave_filter(_X, FS),
    "filters.WeightingFilter": lambda: filters.WeightingFilter(FS, "A").filter(_X),
    "filters.weighting_filter": lambda: filters.weighting_filter(_X, FS, "A"),
    "filters.TimeWeighting": lambda: filters.TimeWeighting(FS, "fast").process(_X),
    "filters.time_weighting": lambda: filters.time_weighting(_X, FS, "fast"),
    "filters.linkwitz_riley": lambda: filters.linkwitz_riley(_X, FS, frequency=1000.0),
    "metrology.sensitivity": lambda: metrology.sensitivity(
        0.1 * _TONE, fs=FS, validate=False
    ),
    "psychoacoustics.tone_to_noise_ratio": lambda: psychoacoustics.tone_to_noise_ratio(
        _TONE + 0.01 * _X, FS
    ),
    "psychoacoustics.prominence_ratio": lambda: psychoacoustics.prominence_ratio(
        _TONE + 0.01 * _X, FS
    ),
    "room.sweep_signal": lambda: room.sweep_signal(FS, 100.0, 1000.0, 0.2),
    "room.inverse_filter": lambda: room.inverse_filter(FS, 100.0, 1000.0, 0.2),
    "room.shaped_sweep_signal": lambda: room.shaped_sweep_signal(
        FS, 100.0, 1000.0, 0.2
    ),
    "room.impulse_response": lambda: room.impulse_response(_X, _X, FS),
    "room.mls_impulse_response": lambda: room.mls_impulse_response(
        np.tile(_MLS, 2), _MLS, fs=FS
    ),
    "room.golay_impulse_response": lambda: room.golay_impulse_response(
        _GOLAY[0], _GOLAY[1], _GOLAY, fs=FS
    ),
    "room.decay_curve": lambda: room.decay_curve(_IR, FS, 1000.0),
    "room.room_parameters": lambda: room.room_parameters(_IR, FS),
    "room.sound_pressure_exposure_level": lambda: room.sound_pressure_exposure_level(
        _IR, FS
    ),
    "room.sound_strength": lambda: room.sound_strength(_IR, _IR, FS),
    "room.early_lateral_energy_fraction": lambda: room.early_lateral_energy_fraction(
        _IR, 0.5 * _IR, FS
    ),
    "room.late_lateral_sound_level": lambda: room.late_lateral_sound_level(
        _IR, 0.5 * _IR, _IR, FS
    ),
    "room.interaural_cross_correlation": lambda: room.interaural_cross_correlation(
        _IR, 0.9 * _IR, FS
    ),
    "room.stage_support": lambda: room.stage_support(_IR, FS),
    "signals.laeq": lambda: signals.laeq(_X, FS),
    "signals.ln_levels": lambda: signals.ln_levels(_X, FS),
    "signals.lc_peak": lambda: signals.lc_peak(_X, FS),
    "signals.sel": lambda: signals.sel(_X, FS),
    "signals.sound_exposure": lambda: signals.sound_exposure(_X, FS),
    "signals.lex_8h": lambda: signals.lex_8h(_X, FS),
    "speech.sti_from_impulse_response": lambda: speech.sti_from_impulse_response(
        _IR, FS
    ),
    "speech.stipa": lambda: speech.stipa(
        speech.stipa_signal(FS, duration_s=18.0, seed=1), FS
    ),
    "speech.stipa_signal": lambda: speech.stipa_signal(FS, duration_s=1.0, seed=1),
    "io.Signal": lambda: io.Signal(_X, FS),
}


@pytest.mark.filterwarnings("ignore")
@pytest.mark.parametrize("name", sorted(_CALLS))
def test_a_fractional_rate_runs(name: str) -> None:
    assert _CALLS[name]() is not None


def test_a_whole_number_rate_refuses_a_fraction() -> None:
    """The rates the guard lists as whole numbers refuse 48000.5 when the call runs."""
    with pytest.raises(ValueError, match=r"'fs' must be a whole number"):
        electroacoustics.loop_test_noise(
            FS,  # type: ignore[arg-type]
            1.0,
        )
    with pytest.raises(ValueError, match=r"'fs' must be a whole number"):
        psychoacoustics.loudness_zwicker(
            _TONE,
            FS,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match=r"'fs' must be a whole number"):
        room.image_source_rir(
            (5.0, 4.0, 3.0),
            (1.0, 1.0, 1.0),
            (4.0, 3.0, 1.5),
            0.3,
            fs=FS,  # type: ignore[arg-type]
            max_order=2,
        )


def test_a_resampled_signal_keeps_its_fractional_rate() -> None:
    """A Signal resamples to a fractional rate and carries it, as an array does."""
    resampled = signals.resample_signal(io.Signal(_X, 2.0 * FS), fs_new=FS)
    assert resampled.fs == FS
    assert isinstance(resampled.signal, io.Signal)
    assert resampled.signal.fs == FS


def _spy(monkeypatch: pytest.MonkeyPatch, module: object, name: str) -> list[float]:
    """The rates the function *name* of *module* is called with."""
    seen: list[float] = []
    original = getattr(module, name)

    def spy(*args: object, **kwargs: object) -> object:
        seen.append(float(args[1]))  # type: ignore[arg-type]
        return original(*args, **kwargs)

    monkeypatch.setattr(module, name, spy)
    return seen


def test_a_fractional_rate_reaches_the_weighting_unrounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The weighted residual of a THD is filtered at the record's own rate."""
    from phonometry.filters import weighting

    seen = _spy(monkeypatch, weighting, "weighting_filter")
    tone = np.sin(2.0 * np.pi * 1000.0 * np.arange(48000) / FS)
    electroacoustics.weighted_thd(
        tone + 0.01 * tone**2, FS, fundamental=1000.0, weighting="A"
    )
    assert seen == [FS]


@pytest.mark.filterwarnings("ignore")
def test_a_fractional_rate_reaches_the_band_analysis_unrounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The one-third octaves of a limiting test signal run at its own rate."""
    from phonometry.filters import core

    seen = _spy(monkeypatch, core, "octave_filter")
    noise = np.clip(np.random.default_rng(3).standard_normal(96000), -2.0, 2.0)
    electroacoustics.check_limiting_test_signal(noise, FS)
    assert seen == [FS]
