#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The exponential-sweep test of a band filter: time-invariant operation.

IEC 61260-1:2014 5.14 asks a set of filters that claims time-invariant
operation to pass a test a transfer function cannot: driven by a
constant-amplitude sinusoid whose frequency rises at an exponential rate, each
filter's time-averaged output shall stay within :math:`\pm 0.4` dB (class 1)
or :math:`\pm 0.6` dB (class 2) of the level Formula (17) predicts,

.. math::

   L_\mathrm{c} = L_\mathrm{in} - A_\mathrm{ref} + 10\lg\left[
   \frac{T_\mathrm{sweep}}{T_\mathrm{avg}}\,
   \frac{\lg(f_2/f_1)}{\lg(f_\mathrm{end}/f_\mathrm{start})}\right]\ \mathrm{dB},

for a sweep of one decade in 2 s to 5 s (5.14.3). Annex G derives it: the time
average of the swept output is the effective bandwidth over the sweep rate, so
a filter whose effective bandwidth is the reference one (:math:`B_\mathrm{e} =
B_\mathrm{r}`) reads exactly :math:`L_\mathrm{c}` (G.2.8). IEC 61260-2:2016
7.4 is the pattern-evaluation test and IEC 61260-3:2016 10.3 uses the same
sweep to measure the effective bandwidth deviation of a time-invariant filter
in a periodic test.

This module has three things for it:

* :func:`swept_band_level`, Formula (17) itself, which IEC 61260-2 and -3
  Annex B work through to :math:`L_\mathrm{c} = 107.97` dB;
* :func:`swept_level_uncertainty`, the standard uncertainty of that level
  from the uncertainties of the sweep (Annex A of IEC 61260-2 and -3,
  Formula (A.2)); the annexes print :math:`u = 0.057` dB for their example,
  which this reproduces, while the printed Formula (A.2) drops the square on
  the coefficient of its frequency terms (see the errata registry);
* :func:`verify_time_invariance`, the test run on an
  :class:`~phonometry.filters.OctaveFilterBank`: the sweep of Formulas (A.3)
  and (A.4) goes through every band exactly as the bank filters a signal, the
  polyphase decimation of a multirate bank included, so it tests what the
  transfer functions alone cannot.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import signal

from .._internal.frozen import read_only
from .._internal.validation import require_non_negative, require_positive
from .compliance import _G, _band_relative_attenuation
from .core import _decimate_and_filter

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from .core import OctaveFilterBank

__all__ = [
    "TimeInvarianceResult",
    "swept_band_level",
    "swept_level_uncertainty",
    "verify_time_invariance",
]

#: IEC 61260-1:2014 5.14.3: acceptance limits on the deviation of the
#: time-averaged output of an exponential sweep from Formula (17), +/- dB.
_TIME_INVARIANCE_LIMITS_DB: dict[int, float] = {1: 0.4, 2: 0.6}

#: IEC 61260-1:2014 5.14.3: the sweep rates the time-invariance limits hold
#: for, one decade in 2 s to 5 s.
_SECONDS_PER_DECADE_RANGE = (2.0, 5.0)

#: IEC 61260-2:2016 7.4.2: the sweep starts and ends where the relative
#: attenuation of the outermost filters is at least 55 dB.
_SWEEP_EDGE_ATTENUATION_DB = 55.0

#: How far beyond its 55 dB points the design test extends the sweep, in
#: decades. An exponential sweep that starts at full amplitude spreads its
#: energy over a few "ripple widths" around the start frequency, and at
#: 2 s per decade starting at the 55 dB point of a 12.5 Hz one-third-octave
#: band reads that band 0.47 dB high: an artefact of the test, not of the
#: filter. One decade further out the ripple is gone and the reading settles
#: on the band's effective bandwidth deviation. IEC 61260-2 7.4.2 asks for "at
#: least" 55 dB, and its own example (B.2.2) starts at 0.01 Hz for a 6.3 Hz
#: lowest band, almost three decades out.
_SWEEP_GUARD_DECADES = 1.0

#: The energy that may be left in the slowest band's impulse response when
#: the averaging stops: 90 dB below the start, far under anything 0.1 dB can
#: see (IEC 61260-2 7.4.4: the averaging "shall be sufficiently long to also
#: contain parts of the output signal delayed by the operation of the
#: filter").
_TAIL_ENERGY_FLOOR = 1e-9


@dataclass(frozen=True)
class TimeInvarianceResult:
    r"""The time-invariance verdict of a filter bank, IEC 61260-1:2014 5.14.

    What :func:`verify_time_invariance` returns. For every sweep rate and
    every band it holds the time-averaged output level of the bank driven by
    an exponential sweep and the level Formula (17) predicts for it,

    .. math::

       L_\mathrm{c} = L_\mathrm{in} - A_\mathrm{ref} + 10\lg\left[
       \frac{T_\mathrm{sweep}}{T_\mathrm{avg}}\,
       \frac{\lg(f_2/f_1)}{\lg(f_\mathrm{end}/f_\mathrm{start})}\right],

    whose difference 5.14.3 bounds by :math:`\pm 0.4` dB for class 1 and
    :math:`\pm 0.6` dB for class 2. The levels are in decibels relative to
    the level of the input sweep, whose effective value is 1 (IEC 61260-2
    Formula (A.4)), so :math:`L_\mathrm{in} = 0` dB.

    :ivar band_frequencies: The exact mid-band frequencies, Hz.
    :ivar fraction: The bandwidth designator denominator ``b``.
    :ivar fs: The bank's sampling rate, Hz.
    :ivar seconds_per_decade: The sweep rates, one decade in so many seconds.
    :ivar start_frequency_hz: :math:`f_\mathrm{start}` of every sweep.
    :ivar end_frequency_hz: :math:`f_\mathrm{end}` of every sweep.
    :ivar sweep_durations_s: :math:`T_\mathrm{sweep}`, one per rate.
    :ivar averaging_times_s: :math:`T_\mathrm{avg}`, one per rate: the sweep
        and the silence after it during which the slowest band's output dies
        away.
    :ivar output_levels_db: The measured time-averaged output level
        :math:`L_\mathrm{out}`, shape ``(rates, bands)``.
    :ivar expected_levels_db: :math:`L_\mathrm{c}` of Formula (17), same shape.
    """

    band_frequencies: np.ndarray
    fraction: float
    fs: float
    seconds_per_decade: tuple[float, ...]
    start_frequency_hz: float
    end_frequency_hz: float
    sweep_durations_s: tuple[float, ...]
    averaging_times_s: tuple[float, ...]
    output_levels_db: np.ndarray
    expected_levels_db: np.ndarray

    def __post_init__(self) -> None:
        """Freeze the arrays and refuse levels the verdict cannot be read on.

        :raises ValueError: if the level arrays are not one row per sweep rate
            and one column per band, or hold a non-finite value.
        """
        freqs = np.array(self.band_frequencies, dtype=np.float64)
        out = np.array(self.output_levels_db, dtype=np.float64)
        expected = np.array(self.expected_levels_db, dtype=np.float64)
        shape = (len(self.seconds_per_decade), freqs.size)
        for name, arr in (("output_levels_db", out), ("expected_levels_db", expected)):
            if arr.shape != shape:
                msg = (
                    f"'{name}' must be shaped (rates, bands) = {shape}; "
                    f"got {arr.shape}."
                )
                raise ValueError(msg)
            if not np.all(np.isfinite(arr)):
                msg = f"'{name}' must hold finite levels."
                raise ValueError(msg)
        for name, value in (
            ("sweep_durations_s", self.sweep_durations_s),
            ("averaging_times_s", self.averaging_times_s),
        ):
            if len(value) != len(self.seconds_per_decade):
                msg = f"'{name}' must carry one value per sweep rate."
                raise ValueError(msg)
        object.__setattr__(self, "band_frequencies", read_only(freqs))
        object.__setattr__(self, "output_levels_db", read_only(out))
        object.__setattr__(self, "expected_levels_db", read_only(expected))

    @property
    def deviations_db(self) -> np.ndarray:
        r""":math:`L_\mathrm{out} - L_\mathrm{c}`, shape ``(rates, bands)``."""
        return np.asarray(self.output_levels_db - self.expected_levels_db)

    @property
    def band_classes(self) -> tuple[int | None, ...]:
        """The strictest class each band meets at every sweep rate."""
        worst = np.max(np.abs(self.deviations_db), axis=0)
        return tuple(_time_invariance_class(float(w)) for w in worst)

    @property
    def overall_class(self) -> int | None:
        """The strictest class every band meets, ``None`` if one meets none."""
        classes = self.band_classes
        if not classes or None in classes:
            return None
        return max(c for c in classes if c is not None)

    @property
    def worst_deviation_db(self) -> float:
        """The deviation of largest magnitude, signed, over bands and rates."""
        flat = self.deviations_db.ravel()
        return float(flat[int(np.argmax(np.abs(flat)))])

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`overall_class`.
        """
        msg = (
            "a TimeInvarianceResult has no truth value; read its "
            "'.overall_class' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot every band's deviation from Formula (17), one line per rate.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.filters.plot_time_invariance`.
        """
        from .._i18n import check_language
        from .._plot.filters import plot_time_invariance

        check_language(language)
        return plot_time_invariance(self, ax=ax, language=language, **kwargs)


def _time_invariance_class(worst_db: float) -> int | None:
    """The strictest class of 5.14.3 a deviation of *worst_db* meets."""
    for cls in sorted(_TIME_INVARIANCE_LIMITS_DB):
        if worst_db <= _TIME_INVARIANCE_LIMITS_DB[cls]:
            return cls
    return None


def _edge_frequency_hz(
    sos: np.ndarray, mid_hz: float, rate_hz: float, edge_hz: float, *, below: bool
) -> float | None:
    """Where a band's skirt first reaches 55 dB beyond one of its edges.

    Searched on a logarithmic grid three decades out from the edge (below the
    lower edge or above the upper one, up to the band's processing Nyquist
    frequency), as IEC 61260-2 7.4.2 places the start and the end of the
    sweep.

    :return: The frequency, or ``None`` when the skirt does not reach 55 dB
        on that side before the processing Nyquist frequency.
    """
    span = np.logspace(0.0, -3.0 if below else 3.0, 3001)
    grid = edge_hz * span
    if not below:
        grid = grid[grid < rate_hz / 2.0]
    attenuation = _band_relative_attenuation(sos, mid_hz, rate_hz, grid)
    hits = np.nonzero(attenuation >= _SWEEP_EDGE_ATTENUATION_DB)[0]
    return float(grid[hits[0]]) if hits.size else None


def _decay_time_s(sos: np.ndarray, rate_hz: float) -> float:
    r"""How long the band's impulse response takes to lose all but 1e-9 of it.

    Read off the slowest pole: the energy of a response whose largest pole
    radius is :math:`\rho` falls as :math:`\rho^{2n}` after :math:`n`
    samples.
    """
    _, poles, _ = signal.sos2zpk(sos)
    radius = float(np.max(np.abs(poles))) if poles.size else 0.0
    if radius <= 0.0:
        return 0.0
    samples = math.log(_TAIL_ENERGY_FLOOR) / (2.0 * math.log(radius))
    return samples / rate_hz


def _exponential_sweep(
    start_hz: float, end_hz: float, duration_s: float, fs: float
) -> np.ndarray:
    r"""IEC 61260-2:2016 Formulas (A.3) and (A.4): the sampled sweep.

    :math:`s_n = \sqrt{2}\,\sin\!\left(\frac{2\pi}{r} f_\mathrm{start}
    \left[\exp\!\left(\frac{r}{f_\mathrm{s}} n\right) - 1\right]\right)`,
    :math:`r = \ln(f_\mathrm{end}/f_\mathrm{start}) / T_\mathrm{sweep}`, for
    :math:`n` from zero to the whole number closest to
    :math:`f_\mathrm{s}\,T_\mathrm{sweep}`: effective value 1.
    """
    rate = math.log(end_hz / start_hz) / duration_s
    n = np.arange(round(fs * duration_s) + 1, dtype=np.float64)
    phase = 2.0 * np.pi / rate * start_hz * np.expm1(rate / fs * n)
    return np.asarray(math.sqrt(2.0) * np.sin(phase))


def swept_band_level(
    input_level_db: float,
    *,
    fraction: float,
    sweep_duration_s: float,
    averaging_time_s: float,
    start_frequency_hz: float,
    end_frequency_hz: float,
    reference_attenuation_db: float = 0.0,
) -> float:
    r"""IEC 61260-1:2014 Formula (17): the time-averaged output of a sweep.

    .. math::

       L_\mathrm{c} = L_\mathrm{in} - A_\mathrm{ref} + 10\lg\left[
       \frac{T_\mathrm{sweep}}{T_\mathrm{avg}}\,
       \frac{\lg(f_2/f_1)}{\lg(f_\mathrm{end}/f_\mathrm{start})}\right]

    with :math:`\lg(f_2/f_1) = 3/(10b)` for a base-ten filter of bandwidth
    designator :math:`1/b` (NOTE 1 to 5.14.2): the level an exponential sweep
    of constant amplitude leaves, averaged over :math:`T_\mathrm{avg}`, at the
    output of a filter whose relative attenuation is zero in its pass band and
    infinite outside it (NOTE 2). The deviation of a measured output from it
    is what 5.14.3 and IEC 61260-3:2016 10.3.6 grade.

    :param input_level_db: :math:`L_\mathrm{in}`, the level of the sweep.
    :param fraction: The bandwidth designator denominator ``b``.
    :param sweep_duration_s: :math:`T_\mathrm{sweep}`, the time from the start
        frequency to the end frequency.
    :param averaging_time_s: :math:`T_\mathrm{avg}`, the averaging time of the
        output level.
    :param start_frequency_hz: :math:`f_\mathrm{start}`.
    :param end_frequency_hz: :math:`f_\mathrm{end}`, above the start.
    :param reference_attenuation_db: :math:`A_\mathrm{ref}`, the reference
        attenuation of 5.9 (0 dB by default).
    :return: :math:`L_\mathrm{c}` in the unit of ``input_level_db``.
    :raises ValueError: for a non-positive bandwidth designator, duration,
        averaging time or frequency, or an end frequency not above the start.
    """
    b = require_positive(fraction, "fraction")
    t_sweep = require_positive(sweep_duration_s, "sweep_duration_s")
    t_avg = require_positive(averaging_time_s, "averaging_time_s")
    f_start = require_positive(start_frequency_hz, "start_frequency_hz")
    f_end = require_positive(end_frequency_hz, "end_frequency_hz")
    if f_end <= f_start:
        msg = (
            f"'end_frequency_hz' ({f_end:g}) must be above "
            f"'start_frequency_hz' ({f_start:g})."
        )
        raise ValueError(msg)
    band_ratio_lg = math.log10(_G) / b
    return (
        float(input_level_db)
        - float(reference_attenuation_db)
        + 10.0
        * math.log10(t_sweep / t_avg * band_ratio_lg / math.log10(f_end / f_start))
    )


def swept_level_uncertainty(
    *,
    input_level_uncertainty_db: float,
    sweep_duration_s: float,
    sweep_duration_uncertainty_s: float,
    averaging_time_s: float,
    averaging_time_uncertainty_s: float,
    start_frequency_hz: float,
    start_frequency_uncertainty_hz: float,
    end_frequency_hz: float,
    end_frequency_uncertainty_hz: float,
    display_resolution_db: float = 0.0,
) -> float:
    r"""The standard uncertainty of :func:`swept_band_level`, from the sweep.

    Annex A of IEC 61260-2:2016 and of IEC 61260-3:2016 propagates the
    standard uncertainties of the input level, the sweep time, the averaging
    time and the two end frequencies through Formula (17) (A.1):

    .. math::

       u_{L_\mathrm{c}}^2 = u_{L_\mathrm{in}}^2
       + \left(\frac{10}{\ln 10}\right)^2 \left[
       \left(\frac{u_{T_\mathrm{sweep}}}{T_\mathrm{sweep}}\right)^2
       + \left(\frac{u_{T_\mathrm{avg}}}{T_\mathrm{avg}}\right)^2\right]
       + \left(\frac{10}{\ln(f_\mathrm{end}/f_\mathrm{start})\,\ln 10}
       \right)^2 \left[
       \left(\frac{u_{f_\mathrm{end}}}{f_\mathrm{end}}\right)^2
       + \left(\frac{u_{f_\mathrm{start}}}{f_\mathrm{start}}\right)^2\right]

    Formula (A.2) as printed in both parts leaves the square off the
    coefficient of the frequency terms; the square is what the derivative of
    Formula (17) gives, and it is the only reading that reproduces the
    annexes' own example (A.3.5): :math:`u_{L_\mathrm{c}} \approx 0.057` dB and
    an expanded uncertainty of 0.115 dB, where the printed form gives
    0.075 dB. See the errata registry.

    A reading taken from a display adds its resolution as a rectangular
    distribution of half-width half the resolution (IEC 61260-3:2016 5.2):
    ``display_resolution_db=0.1`` turns the example's 0.115 dB into the
    0.128 dB of A.3.5.

    :param input_level_uncertainty_db: :math:`u_{L_\mathrm{in}}`, standard.
    :param sweep_duration_s: :math:`T_\mathrm{sweep}`.
    :param sweep_duration_uncertainty_s: Its standard uncertainty.
    :param averaging_time_s: :math:`T_\mathrm{avg}`.
    :param averaging_time_uncertainty_s: Its standard uncertainty.
    :param start_frequency_hz: :math:`f_\mathrm{start}`.
    :param start_frequency_uncertainty_hz: Its standard uncertainty.
    :param end_frequency_hz: :math:`f_\mathrm{end}`, above the start.
    :param end_frequency_uncertainty_hz: Its standard uncertainty.
    :param display_resolution_db: The resolution of the display the output
        level is read from, 0 when it is not read from one.
    :return: :math:`u_{L_\mathrm{c}}`, the standard uncertainty in dB; the
        annexes expand it with a coverage factor of 2.
    :raises ValueError: for a negative uncertainty or resolution, a
        non-positive duration or frequency, or an end frequency not above the
        start.
    """
    u_in = require_non_negative(
        input_level_uncertainty_db, "input_level_uncertainty_db"
    )
    t_sweep = require_positive(sweep_duration_s, "sweep_duration_s")
    u_sweep = require_non_negative(
        sweep_duration_uncertainty_s, "sweep_duration_uncertainty_s"
    )
    t_avg = require_positive(averaging_time_s, "averaging_time_s")
    u_avg = require_non_negative(
        averaging_time_uncertainty_s, "averaging_time_uncertainty_s"
    )
    f_start = require_positive(start_frequency_hz, "start_frequency_hz")
    u_start = require_non_negative(
        start_frequency_uncertainty_hz, "start_frequency_uncertainty_hz"
    )
    f_end = require_positive(end_frequency_hz, "end_frequency_hz")
    u_end = require_non_negative(
        end_frequency_uncertainty_hz, "end_frequency_uncertainty_hz"
    )
    resolution = require_non_negative(display_resolution_db, "display_resolution_db")
    if f_end <= f_start:
        msg = (
            f"'end_frequency_hz' ({f_end:g}) must be above "
            f"'start_frequency_hz' ({f_start:g})."
        )
        raise ValueError(msg)
    time_coefficient = 10.0 / math.log(10.0)
    frequency_coefficient = 10.0 / (math.log(f_end / f_start) * math.log(10.0))
    variance = (
        u_in**2
        + time_coefficient**2 * ((u_sweep / t_sweep) ** 2 + (u_avg / t_avg) ** 2)
        + frequency_coefficient**2 * ((u_end / f_end) ** 2 + (u_start / f_start) ** 2)
        + (resolution / (2.0 * math.sqrt(3.0))) ** 2
    )
    return math.sqrt(variance)


def verify_time_invariance(
    bank: OctaveFilterBank,
    *,
    seconds_per_decade: tuple[float, ...] = _SECONDS_PER_DECADE_RANGE,
) -> TimeInvarianceResult:
    r"""Test the time-invariant operation of a bank, IEC 61260-1:2014 5.14.

    The swept-frequency test of IEC 61260-2:2016 7.4, run on the bank itself:
    an exponential sweep of effective value 1 (Formulas (A.3) and (A.4))
    goes through every band exactly as :meth:`OctaveFilterBank.filter`
    processes it, the polyphase decimation of a multirate bank included, and
    each band's time-averaged output is compared with the level
    :math:`L_\mathrm{c}` of Formula (17). A bank whose bands do what their
    transfer functions say reads, band by band, its effective bandwidth
    deviation (Annex G, G.2.8); decimation that folds energy back into a
    band, or state that is not carried from one sample to the next, reads as
    more.

    * The sweep starts one decade below the frequency at which the lowest
      band's relative attenuation reaches 55 dB below its lower band edge,
      and ends one decade above the matching point of the highest band, or
      at the Nyquist frequency if that comes first (7.4.2 asks for "at
      least" 55 dB; the extra decade keeps the start transient of the sweep
      out of the lowest band).
    * The averaging runs from the start of the sweep until the slowest
      band's impulse response has lost all but :math:`10^{-9}` of its energy
      after the sweep ends (7.4.4).
    * The reference attenuation is each band's attenuation at its exact
      mid-band frequency, as :func:`verify_filter_class` takes it.

    A time-invariant design is an optional claim: 5.14.4 has the instruction
    manual state the bandwidths and frequency ranges it applies to, and the
    verdict here is for the bank as configured.

    :param bank: The filter bank; its designed sections and decimation
        factors are run, and a stateful bank's carried state is left alone.
    :param seconds_per_decade: The sweep rates to run, one decade in so many
        seconds, each within the 2 s to 5 s for which 5.14.3 sets its limits.
        The default runs both ends of that range.
    :return: A :class:`TimeInvarianceResult`.
    :raises ValueError: for no sweep rate, a rate outside 2 s to 5 s per
        decade, or a bank with no bands.
    """
    rates_spd = tuple(float(r) for r in seconds_per_decade)
    low, high = _SECONDS_PER_DECADE_RANGE
    if not rates_spd or any(not low <= r <= high for r in rates_spd):
        msg = (
            "'seconds_per_decade' must hold one or more sweep rates of 2 s to 5 s "
            f"per decade (IEC 61260-1:2014 5.14.3); got {seconds_per_decade!r}."
        )
        raise ValueError(msg)
    if bank.num_bands < 1:
        msg = "The bank has no bands to test."
        raise ValueError(msg)
    fs = float(bank.fs)
    mids = [float(f) for f in bank.freq]
    rates_hz = [fs / float(f) for f in bank.factor]
    guard = 10.0**_SWEEP_GUARD_DECADES
    lowest = _edge_frequency_hz(
        bank.sos[0], mids[0], rates_hz[0], float(bank.freq_d[0]), below=True
    )
    start_hz = (
        lowest if lowest is not None else float(bank.freq_d[0]) / 1000.0
    ) / guard
    highest = _edge_frequency_hz(
        bank.sos[-1], mids[-1], rates_hz[-1], float(bank.freq_u[-1]), below=False
    )
    end_hz = min(highest * guard, fs / 2.0) if highest is not None else fs / 2.0
    decay_s = max(
        _decay_time_s(sos, rate) for sos, rate in zip(bank.sos, rates_hz, strict=True)
    )

    sweep_ratio_lg = math.log10(end_hz / start_hz)
    outputs = np.empty((len(rates_spd), bank.num_bands))
    expected = np.empty_like(outputs)
    sweeps: list[float] = []
    averages: list[float] = []
    for row, spd in enumerate(rates_spd):
        duration_s = spd * sweep_ratio_lg
        sweep = _exponential_sweep(start_hz, end_hz, duration_s, fs)
        tail = np.zeros(math.ceil(decay_s * fs))
        x = np.concatenate([sweep, tail])
        t_sweep = (sweep.size - 1) / fs
        t_avg = x.size / fs
        sweeps.append(t_sweep)
        averages.append(t_avg)
        for idx in range(bank.num_bands):
            y = _decimate_and_filter(x, bank.sos[idx], int(bank.factor[idx]))
            energy = float(np.sum(y * y)) / rates_hz[idx]
            outputs[row, idx] = 10.0 * math.log10(energy / t_avg)
            _, h_ref = signal.sosfreqz(
                bank.sos[idx], worN=np.array([mids[idx]]), fs=rates_hz[idx]
            )
            a_ref = -20.0 * math.log10(abs(h_ref[0]) + np.finfo(float).eps)
            expected[row, idx] = swept_band_level(
                0.0,
                fraction=bank.fraction,
                sweep_duration_s=t_sweep,
                averaging_time_s=t_avg,
                start_frequency_hz=start_hz,
                end_frequency_hz=end_hz,
                reference_attenuation_db=a_ref,
            )
    return TimeInvarianceResult(
        band_frequencies=np.asarray(mids),
        fraction=float(bank.fraction),
        fs=fs,
        seconds_per_decade=rates_spd,
        start_frequency_hz=start_hz,
        end_frequency_hz=end_hz,
        sweep_durations_s=tuple(sweeps),
        averaging_times_s=tuple(averages),
        output_levels_db=outputs,
        expected_levels_db=expected,
    )
