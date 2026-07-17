#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Deterministic colored-noise test signals.

Gaussian noise with an exact power-law spectral slope, for exercising and
validating spectral estimators: white (0 dB/octave), pink (-3.01), red
(-6.02, also called Brownian), blue (+3.01) and violet (+6.02). The
autospectral density follows ``Gxx(f) ∝ f^α`` with ``α`` = 0, -1, -2, +1
and +2 respectively, so the level changes by exactly ``3.01·α`` dB per
octave (``10·lg 2 = 3.0103`` dB).

The colors are synthesized by filtering seeded white Gaussian noise in the
frequency domain: the DFT of the white record is multiplied by the exact
magnitude response ``|H(f)| = (f/f_ref)^(α/2)`` bin by bin (a zero-phase
FIR filter applied circularly), so the *expected* spectrum follows the
power law exactly at every synthesis bin above DC and a measured slope
deviates only by the random error of the spectral estimate (thousandths of
a dB per octave over a three-decade regression) - not the piecewise or
few-pole approximations whose pink slope ripples by fractions of a dB. The
DC bin is zeroed for the colored variants (a power law has no finite DC
value) and the record is rescaled to the requested RMS exactly.

With the same ``seed`` the generator is fully deterministic across runs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = ["noise_signal"]

#: Power-law exponent α of ``Gxx(f) ∝ f^α`` per color.
_COLOR_EXPONENTS: dict[str, float] = {
    "white": 0.0,
    "pink": -1.0,
    "red": -2.0,
    "blue": 1.0,
    "violet": 2.0,
}


def noise_signal(
    fs: float,
    seconds: float = 1.0,
    *,
    color: Literal["white", "pink", "red", "blue", "violet"] = "white",
    rms: float = 1.0,
    seed: int | None = None,
) -> "NDArray[np.float64]":
    """Generate Gaussian noise with an exact power-law spectral slope.

    ``Gxx(f) ∝ f^α`` with α = 0 (white), -1 (pink, -3.01 dB/octave),
    -2 (red/Brownian, -6.02), +1 (blue, +3.01) or +2 (violet, +6.02),
    shaped by an exact frequency-domain filter (see the module docstring),
    zero-mean and rescaled to the requested RMS exactly.

    :param fs: Sample rate, in Hz.
    :param seconds: Duration, in seconds (at least 16 samples).
    :param color: Noise color: ``'white'``, ``'pink'``, ``'red'``,
        ``'blue'`` or ``'violet'``.
    :param rms: Root-mean-square value of the returned record.
    :param seed: Seed for :func:`numpy.random.default_rng`; the same seed
        reproduces the same record. ``None`` draws fresh entropy.
    :return: The noise record, ``round(fs·seconds)`` samples.
    :raises ValueError: If the inputs or parameters are invalid.
    """
    fs_v = float(fs)
    if not np.isfinite(fs_v) or fs_v <= 0.0:
        raise ValueError("'fs' must be a positive, finite number.")
    seconds_v = float(seconds)
    if not np.isfinite(seconds_v) or seconds_v <= 0.0:
        raise ValueError("'seconds' must be a positive, finite number.")
    n = int(round(fs_v * seconds_v))
    if n < 16:
        raise ValueError(
            f"'fs'*'seconds' must give at least 16 samples, got {n}."
        )
    if color not in _COLOR_EXPONENTS:
        raise ValueError(
            "'color' must be one of 'white', 'pink', 'red', 'blue', 'violet'."
        )
    rms_v = float(rms)
    if not np.isfinite(rms_v) or rms_v <= 0.0:
        raise ValueError("'rms' must be a positive, finite number.")

    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    if color != "white":
        alpha = _COLOR_EXPONENTS[color]
        spectrum = np.fft.rfft(x)
        freqs = np.fft.rfftfreq(n, d=1.0 / fs_v)
        gain = np.zeros_like(freqs)
        # |H(f)| = (f/f_ref)^(α/2) shapes the PSD by exactly f^α; the
        # reference frequency only sets the overall gain, which the RMS
        # rescaling below removes.
        gain[1:] = (freqs[1:] / freqs[1]) ** (alpha / 2.0)
        x = np.fft.irfft(spectrum * gain, n)
    x = x - float(np.mean(x))
    scale = float(np.sqrt(np.mean(x * x)))
    if scale <= 0.0:  # pragma: no cover - white Gaussian is never all-zero
        raise ValueError("Degenerate all-zero record; use another seed.")
    return np.asarray(x * (rms_v / scale), dtype=np.float64)
