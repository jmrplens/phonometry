#  Copyright (c) 2026. Jose M. Requena-Plens

"""EN/ES language option of the electroacoustics ``.plot()`` renderers."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import phonometry as ph  # noqa: E402

FS = 48000
RNG = np.random.default_rng(20260720)


def _labels(obj: object) -> str:
    axes = obj if isinstance(obj, np.ndarray) else [obj]
    parts = []
    for a in axes:
        parts += [a.get_xlabel(), a.get_ylabel(), a.get_title()]
        leg = a.get_legend()
        if leg is not None:
            parts += [t.get_text() for t in leg.get_texts()]
    return " || ".join(parts)


def _tone() -> np.ndarray:
    t = np.arange(FS) / FS
    return (np.sin(2 * np.pi * 1000.0 * t)
            + 0.03 * np.sin(2 * np.pi * 2000.0 * t)
            + 0.01 * np.sin(2 * np.pi * 3000.0 * t))


def test_harmonic_distortion_es() -> None:
    res = ph.harmonic_analysis(_tone(), FS, 1000.0)
    ax = res.plot(language="es")
    assert ax.get_ylabel() == "Nivel respecto al fundamental [dB]"
    assert ax.get_xlabel().startswith("Orden del armónico")
    plt.close("all")
    with pytest.raises(ValueError):
        res.plot(language="xx")


def test_frequency_response_es() -> None:
    x = RNG.standard_normal(2 ** 15)
    y = np.convolve(x, np.array([0.5, 0.3, 0.1]), mode="same")
    axes = ph.transfer_function(x, y, FS).plot(language="es")
    text = _labels(axes)
    assert "Respuesta en frecuencia" in text and "coherencia" in text
    assert "Magnitud [dB]" in text
    plt.close("all")


def test_swept_sine_distortion_es() -> None:
    f1, f2, seconds = 100.0, 8000.0, 1.0
    sweep = ph.synchronized_sweep_signal(FS, f1, f2, seconds)
    rec = sweep + 0.01 * sweep ** 2
    res = ph.swept_sine_distortion(rec, FS, f1, f2, seconds, n_harmonics=3)
    # Two-panel figure: harmonic responses (title) + THD(f) (excitation axis).
    axes = res.plot(language="es")
    text = _labels(axes)
    assert "Respuestas en frecuencia de los armónicos" in text
    assert "Frecuencia de excitación [Hz]" in text
    plt.close("all")
    # Single-panel case (ax given) carries the swept-THD title.
    fig, ext = plt.subplots()
    single = res.plot(ax=ext, language="es")
    assert single.get_title() == "THD de barrido sinusoidal (Farina / Novak)"
    plt.close("all")
    with pytest.raises(ValueError):
        res.plot(language="xx")


def test_piston_impedance_es() -> None:
    res = ph.radiating_piston(0.05, np.geomspace(50.0, 5000.0, 60))
    ax = res.plot(language="es")
    assert "pistón circular con pantalla" in ax.get_title()
    assert "Impedancia de radiación normalizada" in ax.get_ylabel()
    plt.close("all")
    with pytest.raises(ValueError):
        res.plot(language="xx")
