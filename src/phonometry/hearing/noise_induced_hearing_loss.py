#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Estimation of noise-induced hearing loss (ISO 1999:2013).

Implements the noise-induced permanent threshold shift (NIPTS) of a
noise-exposed population and its combination with the age-related threshold
into the hearing threshold level associated with age and noise (HTLAN), over
the six audiometric frequencies 500 Hz to 6000 Hz.

The median NIPTS for exposure durations of 10 to 40 years is
``N50 = [u + v*lg(t/t0)] * (L_EX,8h - L0)**2`` (clause 6.3.1, Formula 2, with
the values ``u, v, L0`` of Table 1), extrapolated below 10 years by Formula 3.
The statistical distribution about the median is two half-Gaussians whose
spreads ``du`` (worse than the median) and ``dl`` (better) follow Formulae 6/7
with the coefficients of Table 3; a population fractile is
``N50 + z * spread`` with ``z`` the standard-normal quantile (clause 6.3.2,
Formulae 4/5, Table 2), clamped at zero. The HTLAN combines the age component
``H`` (HTLA, database A = ISO 7029) with the noise component ``N`` by
``H' = H + N - H*N/120`` (clause 6.1, Formula 1).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .threshold import age_threshold

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike

# ---------------------------------------------------------------------------
# Normative constants.
# ---------------------------------------------------------------------------

#: Audiometric frequencies of ISO 1999, in hertz (clause 6.3.1, Table 1).
NIPTS_FREQUENCIES: np.ndarray = np.array(
    [500.0, 1000.0, 2000.0, 3000.0, 4000.0, 6000.0], dtype=np.float64
)

#: Table 1 columns ``u``, ``v`` and ``L0`` (dB) for the median NIPTS N50.
_UVL0: np.ndarray = np.array(
    [[-0.033, 0.110, 93.0],
     [-0.020, 0.070, 89.0],
     [-0.045, 0.066, 80.0],
     [0.012, 0.037, 77.0],
     [0.025, 0.025, 75.0],
     [0.019, 0.024, 77.0]],
    dtype=np.float64,
)

#: Table 3 columns ``Xu``, ``Yu``, ``Xl``, ``Yl`` for the spreads du and dl.
_XY: np.ndarray = np.array(
    [[0.044, 0.016, 0.033, 0.002],
     [0.022, 0.016, 0.020, 0.000],
     [0.031, -0.002, 0.016, 0.000],
     [0.007, 0.016, 0.029, -0.010],
     [0.005, 0.009, 0.016, -0.002],
     [0.013, 0.008, 0.028, -0.007]],
    dtype=np.float64,
)

_HTLAN_DENOM = 120.0  # the compression term denominator of Formula (1).


@dataclass(frozen=True)
class NiptsResult:
    """Noise-induced permanent threshold shift (ISO 1999:2013, clause 6.3).

    All arrays are in dB and aligned with :data:`NIPTS_FREQUENCIES`.

    :ivar l_ex: Noise exposure level normalized to 8 h, ``L_EX,8h``, in dB.
    :ivar years: Exposure duration, in years.
    :ivar fractile: Population fractile of ``value`` (0-1); the fraction of the
        population with a smaller shift, so ``0.9`` is the most-susceptible 10 %.
    :ivar frequencies: Audiometric frequencies, in hertz.
    :ivar median: Median NIPTS ``N50`` (Formula 2/3).
    :ivar value: NIPTS at ``fractile`` (Formula 4/5), clamped at zero.
    :ivar spread_upper: Upper half-Gaussian spread ``du`` (Formula 6).
    :ivar spread_lower: Lower half-Gaussian spread ``dl`` (Formula 7).
    """

    l_ex: float
    years: float
    fractile: float
    frequencies: np.ndarray
    median: np.ndarray
    value: np.ndarray
    spread_upper: np.ndarray
    spread_lower: np.ndarray

    def plot(self, ax: "Axes | None" = None, *, language: str = "en", **kwargs: Any) -> "Axes":
        """Plot the NIPTS spectrum with the fractile band over frequency.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.hearing import plot_nipts

        return plot_nipts(self, ax=ax, language=check_language(language), **kwargs)


@dataclass(frozen=True)
class HtlanResult:
    """Hearing threshold level associated with age and noise (clause 6.1).

    All arrays are in dB and aligned with :data:`NIPTS_FREQUENCIES`.

    :ivar age: Listener age, in years.
    :ivar sex: ``"male"`` or ``"female"``.
    :ivar l_ex: Noise exposure level normalized to 8 h, in dB.
    :ivar years: Exposure duration, in years.
    :ivar fractile: Population fractile (0-1) applied to both components.
    :ivar frequencies: Audiometric frequencies, in hertz.
    :ivar htla: Age component ``H`` (HTLA, database A = ISO 7029).
    :ivar nipts: Noise component ``N`` (NIPTS at ``fractile``).
    :ivar threshold: Combined HTLAN ``H' = H + N - H*N/120``.
    """

    age: float
    sex: str
    l_ex: float
    years: float
    fractile: float
    frequencies: np.ndarray
    htla: np.ndarray
    nipts: np.ndarray
    threshold: np.ndarray

    def plot(self, ax: "Axes | None" = None, *, language: str = "en", **kwargs: Any) -> "Axes":
        """Plot the age, noise and combined threshold components over frequency.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.hearing import plot_htlan

        return plot_htlan(self, ax=ax, language=check_language(language), **kwargs)


def _select(values: np.ndarray, frequencies: ArrayLike | None) -> np.ndarray:
    """Return ``values`` for a requested frequency subset, or all of them."""
    if frequencies is None:
        return values.copy()
    fr = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    idx = []
    for f in fr:
        matches = np.isclose(NIPTS_FREQUENCIES, f, rtol=1e-3)
        if not matches.any():
            raise ValueError(
                f"frequency {f} Hz is not an ISO 1999 audiometric frequency "
                f"(500 Hz - 6000 Hz)."
            )
        idx.append(int(np.argmax(matches)))
    return values[idx]


def _nipts_components(l_ex: float, years: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Median N50 and the spreads du, dl at every audiometric frequency."""
    u, v, l0 = _UVL0[:, 0], _UVL0[:, 1], _UVL0[:, 2]
    # L_EX,8h deemed equal to L0 where it is smaller, so the effect is zero.
    excess2 = np.maximum(l_ex - l0, 0.0) ** 2
    lg_t = math.log10(years)  # lg(t / t0), t0 = 1 year

    n50_10 = (u + v * math.log10(10.0)) * excess2
    if years >= 10.0:
        n50 = (u + v * lg_t) * excess2
    else:
        # Formula (3): extrapolate below 10 years from the 10-year value.
        n50 = (math.log10(years + 1.0) / math.log10(11.0)) * n50_10
    n50 = np.maximum(n50, 0.0)

    xu, yu, xl, yl = _XY[:, 0], _XY[:, 1], _XY[:, 2], _XY[:, 3]
    # The spreads are half-Gaussian standard deviations and must stay >= 0; the
    # linear term can only turn negative for a sub-1-year extrapolation, outside
    # the standard's range, where it would otherwise invert the percentiles.
    # Reading note (ISO 1999:2013): below 10 years the median N50 follows the
    # Formula (3) lg(t+1)/lg(11) extrapolation, but Formulae (6)/(7) for the
    # spreads carry no such provision, so du/dl keep the raw lg(t) here. That
    # is a faithful reading of the standard's text; Annex D tabulates no
    # sub-10-year fractile cells that could arbitrate it.
    du = np.maximum((xu + yu * lg_t) * excess2, 0.0)
    dl = np.maximum((xl + yl * lg_t) * excess2, 0.0)
    return n50, du, dl


def nipts(
    l_ex: float,
    years: float,
    fractile: float = 0.5,
    frequencies: ArrayLike | None = None,
) -> NiptsResult:
    """Noise-induced permanent threshold shift (ISO 1999:2013, clause 6.3).

    Returns, per audiometric frequency, the median NIPTS ``N50`` (Formula 2,
    extrapolated below 10 years by Formula 3), the upper/lower spreads
    ``du``/``dl`` (Formulae 6/7) and the NIPTS at the requested population
    ``fractile`` (Formulae 4/5): ``N50 + z * spread`` where ``z`` is the
    standard-normal quantile of ``fractile`` and the spread is the upper one for
    ``z >= 0`` (worse than the median) or the lower one otherwise, clamped at
    zero.

    :param l_ex: Noise exposure level normalized to a nominal 8 h working day,
        ``L_EX,8h``, in dB.
    :param years: Exposure duration, in years (> 0; the standard establishes
        10-40 years and extrapolates 1-10 years by Formula 3, below 1 year the
        result is a further extrapolation).
    :param fractile: Population fractile in the open interval (0, 1); ``0.5``
        gives the median. The reliable range of the standard is 0.05-0.95.
    :param frequencies: Optional subset of the audiometric frequencies, in
        hertz; ``None`` uses all six (500 Hz - 6000 Hz).
    :return: A :class:`NiptsResult` with the distribution and ``.plot()``.
    :raises ValueError: for a non-positive duration, a fractile outside (0, 1),
        or an unknown frequency.
    """
    if years <= 0.0:
        raise ValueError(f"years must be positive; got {years}.")
    if not 0.0 < fractile < 1.0:
        raise ValueError(f"fractile must be in (0, 1); got {fractile}.")

    from scipy.special import ndtri  # standard-normal quantile

    n50, du, dl = _nipts_components(float(l_ex), float(years))
    z = float(ndtri(fractile))
    value = np.maximum(n50 + z * (du if z >= 0.0 else dl), 0.0)

    return NiptsResult(
        l_ex=float(l_ex),
        years=float(years),
        fractile=float(fractile),
        frequencies=_select(NIPTS_FREQUENCIES, frequencies),
        median=_select(n50, frequencies),
        value=_select(value, frequencies),
        spread_upper=_select(du, frequencies),
        spread_lower=_select(dl, frequencies),
    )


def htlan(
    age: float,
    sex: Literal["male", "female"],
    l_ex: float,
    years: float,
    fractile: float = 0.5,
    frequencies: ArrayLike | None = None,
) -> HtlanResult:
    """Hearing threshold level associated with age and noise (clause 6.1).

    Combines the age component ``H`` (HTLA from database A, i.e. ISO 7029, at
    the same population fractile) with the noise component ``N`` (the NIPTS at
    that fractile) by Formula (1): ``H' = H + N - H*N/120``. The formula applies
    to corresponding percentage values, so the same ``fractile`` drives both
    components.

    :param age: Listener age, in years (at least 18, the ISO 7029 lower limit).
    :param sex: ``"male"`` or ``"female"``.
    :param l_ex: Noise exposure level normalized to 8 h, ``L_EX,8h``, in dB.
    :param years: Exposure duration, in years.
    :param fractile: Population fractile in (0, 1) applied to both components.
    :param frequencies: Optional subset of the audiometric frequencies, in
        hertz; ``None`` uses all six (500 Hz - 6000 Hz).
    :return: An :class:`HtlanResult` with ``htla``, ``nipts``, ``threshold`` and
        ``.plot()``.
    :raises ValueError: for an age below 18, an unknown sex, a non-positive
        duration, a fractile outside (0, 1), or an unknown frequency.
    """
    freqs = _select(NIPTS_FREQUENCIES, frequencies)
    htla = age_threshold(age, sex, fractile, frequencies=freqs).threshold
    noise = nipts(l_ex, years, fractile, frequencies=freqs).value
    threshold = htla + noise - htla * noise / _HTLAN_DENOM

    return HtlanResult(
        age=float(age),
        sex=sex,
        l_ex=float(l_ex),
        years=float(years),
        fractile=float(fractile),
        frequencies=freqs,
        htla=htla,
        nipts=noise,
        threshold=threshold,
    )
