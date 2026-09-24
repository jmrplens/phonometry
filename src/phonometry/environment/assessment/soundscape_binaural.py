#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a soundscape sounds like at the ears: the binaural analysis of
ISO/TS 12913-3:2019 Annex D and ISO/TS 12913-2:2018 Annex D.

A soundscape study records the acoustic environment with an artificial head,
because a binaural recording keeps what a listener hears with both ears. For
the analysis, each of the two channels is processed on its own, after the
recording has been equalized to approximate a monaural microphone
measurement (ISO/TS 12913-3 clause 7, ISO/TS 12913-2 D.4). Every metric of
Table D.1 is determined for each ear, and the **higher of the two values**
is the single representative value "indicating the overall experience"; the
arithmetic mean of the two may be reported as well (D.2). :func:`binaural_indicators`
does that for a calibrated two-channel recording, with the library's own
implementation of each metric:

* **sound pressure level**, ISO 1996-1: :math:`L_{\mathrm{Aeq},T}`,
  :math:`L_{\mathrm{Ceq},T}`, :math:`L_{\mathrm{AF5},T}` and
  :math:`L_{\mathrm{AF95},T}`, from :func:`~phonometry.signals.laeq`,
  :func:`~phonometry.signals.leq` of the C-weighted signal and
  :func:`~phonometry.signals.ln_levels` with time weighting F;
* **loudness**, ISO 532-1: :math:`N_5`, :math:`N_\mathrm{average}`,
  :math:`N_\mathrm{rmc}`, :math:`N_{95}` and the variability ratio
  :math:`N_5/N_{95}` of D.2, from the time-varying method of
  :func:`~phonometry.psychoacoustics.loudness_zwicker`;
* **psychoacoustic tonality** :math:`T`: Table D.1 names ECMA-74, whose
  current edition (the 22nd, Annex G) refers the psychoacoustic tonality
  calculation to ECMA-418-2 clause 6, which
  :func:`~phonometry.psychoacoustics.tonality_ecma` implements in its
  2025 edition;
* **roughness** :math:`R_{10}`, :math:`R_{50}` and **fluctuation strength**
  :math:`F_{10}`, :math:`F_{50}`: Table D.1 cites Fastl and Zwicker for both,
  and ISO/TS 12913-2 Annex B notes that no standardized method existed in
  2018. The library computes both with the hearing model of ECMA-418-2:2025
  (:func:`~phonometry.psychoacoustics.roughness_ecma`,
  :func:`~phonometry.psychoacoustics.fluctuation_strength_ecma`), whose
  time-dependent values give the percentiles; the method is named in every
  result, as ISO/TS 12913-2 4.2 requires ("the used calculation method shall
  be reported").

**Sharpness** :math:`S_5`, :math:`S_\mathrm{average}` and :math:`S_{95}` are
**not computed**. They are percentiles of a sharpness that varies in time,
and the library's DIN 45692 sharpness
(:func:`~phonometry.psychoacoustics.sharpness_din`) is taken from the
stationary specific loudness of ISO 532-1; its time-varying loudness does not
publish the specific loudness over time that a time-varying sharpness needs.
The result says so in ``not_implemented`` rather than filling the row with a
stationary value under a percentile's name.

Recording requirements of ISO/TS 12913-2 Annex D that the signal itself can
show are checked with a :class:`SoundscapeWarning`: a measurement interval
of at least 3 min (D.3) and a sampling frequency of at least 44,1 kHz (D.6).
The equalization (D.4), the position (D.2) and the calibration are the
caller's: the channels are taken as equalized sound pressure, left first.

The ISO/TS 12913-3 implemented is the first edition, of 2019; ISO has since
published ISO/TS 12913-3:2025, which revises Annex A (the questionnaire
analysis, :mod:`phonometry.environment.assessment.soundscape`).

**Computing cost.** The ECMA-418-2 metrics run the full hearing model on
every channel, and on a 3 min recording they take minutes each, tonality
most of all. ``parameters`` chooses which rows of Table D.1 to compute.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.validation import require_choice
from ..._internal.warnings import PhonometryWarning
from ...filters.weighting import weighting_filter
from ...io._resolve import resolve_calibration, resolve_fs, resolve_samples
from ...psychoacoustics.loudness.zwicker import _percentile, loudness_zwicker
from ...psychoacoustics.quality.fluctuation_strength_ecma import (
    _TRANSIENT as _FLUCTUATION_SETTLING_FRAMES,
)
from ...psychoacoustics.quality.fluctuation_strength_ecma import (
    fluctuation_strength_ecma,
)
from ...psychoacoustics.quality.roughness_ecma import (
    _TRANSIENT as _ROUGHNESS_SETTLING_FRAMES,
)
from ...psychoacoustics.quality.roughness_ecma import roughness_ecma
from ...psychoacoustics.quality.tonality_ecma import tonality_ecma
from ...signals.levels import laeq, leq, ln_levels

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

    from ...io._resolve import SignalInput

__all__ = [
    "BINAURAL_PARAMETERS",
    "BinauralIndicators",
    "BinauralMetric",
    "BinauralParameter",
    "SoundscapeWarning",
    "binaural_indicators",
]


class SoundscapeWarning(PhonometryWarning):
    """A recording falls short of what ISO/TS 12913-2 Annex D requires of it."""


@dataclass(frozen=True)
class BinauralParameter:
    """One row of ISO/TS 12913-3 Table D.1, "Metrics and representative
    single values".

    :ivar parameter: The parameter, as the first column prints it.
    :ivar metrics: The metrics to be determined for each channel separately,
        as their symbols print, in the printed order.
    :ivar average_allowed: Whether the row offers "the average of left and
        right metric values" as an alternative to the higher value; the
        sound pressure level row does not.
    :ivar reference: The document the row cites.
    """

    parameter: str
    metrics: tuple[str, ...]
    average_allowed: bool
    reference: str


#: ISO/TS 12913-3:2019 Table D.1, keyed by the name :func:`binaural_indicators`
#: takes in ``parameters``. For every row the representative single value is
#: the higher of the left and right metric values; all but the first also
#: allow their average. The symbols are the printed ones: ``Naverage`` is the
#: arithmetic mean of the loudness over time and ``Nrmc`` its root mean cube
#: (ISO/TS 12913-2 A.3 f)). The reference printed as ``[32]`` is an entry of
#: the bibliography of ISO/TS 12913-3, the psychoacoustics textbook it cites for
#: roughness and fluctuation strength.
BINAURAL_PARAMETERS: Mapping[str, BinauralParameter] = MappingProxyType(
    {
        "sound_pressure_level": BinauralParameter(
            parameter="Sound pressure level",
            metrics=("LAeq,T", "LCeq,T", "LAF5,T", "LAF95,T"),
            average_allowed=False,
            reference="ISO 1996-1",
        ),
        "loudness": BinauralParameter(
            parameter="Loudness (time-variant loudness)",
            metrics=("N5", "Naverage", "Nrmc", "N95", "N5/N95"),
            average_allowed=True,
            reference="ISO 532-1",
        ),
        "sharpness": BinauralParameter(
            parameter="Sharpness",
            metrics=("S5", "Saverage", "S95"),
            average_allowed=True,
            reference="DIN 45692",
        ),
        "tonality": BinauralParameter(
            parameter="Psychoacoustic tonality",
            metrics=("T",),
            average_allowed=True,
            reference="ECMA 74",
        ),
        "roughness": BinauralParameter(
            parameter="Roughness",
            metrics=("R10", "R50"),
            average_allowed=True,
            reference="[32]",
        ),
        "fluctuation_strength": BinauralParameter(
            parameter="Fluctuation strength",
            metrics=("F10", "F50"),
            average_allowed=True,
            reference="[32]",
        ),
    }
)

#: ISO/TS 12913-2 D.3: "a measurement time interval shall not be shorter than
#: 3 min", in seconds.
_MINIMUM_INTERVAL_S = 180.0

#: ISO/TS 12913-2 D.6: "The sampling frequency shall be at least 44,1 kHz."
_MINIMUM_FS_HZ = 44_100.0

#: A binaural recording has two channels, left and right.
_CHANNELS = 2

#: The sound fields the loudness and hearing-model metrics take.
_Field = Literal["free", "diffuse"]
_FIELDS = ("free", "diffuse")

#: Why the sharpness row of Table D.1 is left empty.
_SHARPNESS_REASON = (
    "DIN 45692 sharpness is computed by the library from the stationary "
    "specific loudness of ISO 532-1 (psychoacoustics.sharpness_din); S5, "
    "Saverage and S95 are percentiles of a time-varying sharpness, which needs "
    "the specific loudness over time, and the library's ISO 532-1 time-varying "
    "loudness does not publish it."
)

#: The methods each metric is computed with, as reported in the result.
_METHODS: Mapping[str, str] = MappingProxyType(
    {
        "LAeq,T": "IEC 61672-1 A-weighting, energy mean over the record (ISO 1996-1)",
        "LCeq,T": "IEC 61672-1 C-weighting, energy mean over the record (ISO 1996-1)",
        "LAF5,T": (
            "A-weighted, time weighting F, level exceeded 5 % of the time (ISO 1996-1)"
        ),
        "LAF95,T": (
            "A-weighted, time weighting F, level exceeded 95 % of the time (ISO 1996-1)"
        ),
        "N5": "ISO 532-1:2017 time-varying loudness, percentile of clause 6.5",
        "Naverage": "ISO 532-1:2017 time-varying loudness, arithmetic mean over time",
        "Nrmc": (
            "ISO 532-1:2017 time-varying loudness, root mean cube over time "
            "(ISO/TS 12913-2 A.3 f))"
        ),
        "N95": "ISO 532-1:2017 time-varying loudness, loudness exceeded 95 % of the time",
        "N5/N95": "ratio of N5 to N95 (ISO/TS 12913-3 D.2)",
        "T": "ECMA-418-2:2025 psychoacoustic tonality, Formula (63)",
        "R10": (
            "ECMA-418-2:2025 roughness, value of R(l50) exceeded 10 % of the time "
            "(its single value of clause 7.1.10)"
        ),
        "R50": "ECMA-418-2:2025 roughness, median of R(l50)",
        "F10": (
            "ECMA-418-2:2025 fluctuation strength, value of F(l50) exceeded 10 % "
            "of the time (its single value of clause 9.1.14)"
        ),
        "F50": "ECMA-418-2:2025 fluctuation strength, median of F(l50)",
    }
)

#: The unit of each metric.
_UNITS: Mapping[str, str] = MappingProxyType(
    {
        "LAeq,T": "dB",
        "LCeq,T": "dB",
        "LAF5,T": "dB",
        "LAF95,T": "dB",
        "N5": "sone",
        "Naverage": "sone",
        "Nrmc": "sone",
        "N95": "sone",
        "N5/N95": "1",
        "T": "tu_HMS",
        "R10": "asper_HMS",
        "R50": "asper_HMS",
        "F10": "vacil_HMS",
        "F50": "vacil_HMS",
    }
)

#: The results ISO/TS 12913-2 A.3 f) requires a report to give.
_REPORTED_RESULTS = ("LAeq,T", "LCeq,T", "LAF5,T", "LAF95,T", "N5", "N95", "Nrmc")


@dataclass(frozen=True)
class BinauralMetric:
    """One metric of Table D.1 at both ears (ISO/TS 12913-3 D.2).

    :ivar symbol: The metric, as Table D.1 prints it (``"LAeq,T"``,
        ``"N5"``...).
    :ivar parameter: The row of Table D.1 it belongs to, a key of
        :data:`BINAURAL_PARAMETERS`.
    :ivar left: The value at the left ear.
    :ivar right: The value at the right ear.
    :ivar unit: Its unit.
    :ivar method: How the library computed it.
    """

    symbol: str
    parameter: str
    left: float
    right: float
    unit: str
    method: str

    def __post_init__(self) -> None:
        """Refuse a value that is not a finite number.

        :raises ValueError: for a non-finite value at either ear.
        """
        for side in ("left", "right"):
            if not math.isfinite(getattr(self, side)):
                msg = f"BinauralMetric {self.symbol!r}: '{side}' must be finite."
                raise ValueError(msg)

    @property
    def representative(self) -> float:
        """The higher of the two ears, the single representative value of D.2."""
        return max(self.left, self.right)

    @property
    def mean(self) -> float:
        """The arithmetic mean of the two ears, which D.2 allows in addition."""
        return 0.5 * (self.left + self.right)


@dataclass(frozen=True)
class BinauralIndicators:
    """The binaural analysis of a soundscape recording (ISO/TS 12913-3
    Annex D, Table D.1).

    :ivar metrics: Every metric computed, keyed by its Table D.1 symbol, in
        the order of the table.
    :ivar not_implemented: Every metric of a requested row that the library
        does not compute, keyed by its symbol, with the reason.
    :ivar parameters: The rows of Table D.1 that were requested.
    :ivar fs: The sampling frequency of the recording, in Hz.
    :ivar duration_s: Its duration, in s.
    :ivar field: The sound field the loudness and hearing-model metrics
        assumed, ``"free"`` or ``"diffuse"``.
    """

    metrics: Mapping[str, BinauralMetric]
    not_implemented: Mapping[str, str]
    parameters: tuple[str, ...]
    fs: float
    duration_s: float
    field: str

    def __post_init__(self) -> None:
        """Freeze the two mappings and refuse unknown rows.

        :raises ValueError: for a row that is not in Table D.1, or a metric
            keyed under a symbol other than its own.
        """
        for name in self.parameters:
            require_choice(name, "parameters", tuple(BINAURAL_PARAMETERS))
        for symbol, metric in self.metrics.items():
            if metric.symbol != symbol:
                msg = f"BinauralIndicators: metric {metric.symbol!r} filed under {symbol!r}."
                raise ValueError(msg)
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(
            self, "not_implemented", MappingProxyType(dict(self.not_implemented))
        )

    def representative(self, symbol: str) -> float:
        """The single representative value of a metric: the higher ear (D.2).

        :param symbol: The metric, as Table D.1 prints it.
        :return: The higher of the left and right values.
        :raises KeyError: if the metric was not computed; a metric the library
            does not implement says why in :attr:`not_implemented`.
        """
        if symbol not in self.metrics:
            reason = self.not_implemented.get(symbol, "it was not requested")
            msg = f"{symbol!r} was not computed: {reason}"
            raise KeyError(msg)
        return self.metrics[symbol].representative

    def reporting_results(self) -> dict[str, float]:
        r"""The results ISO/TS 12913-2 A.3 f) requires a report to give.

        The representative value of each of :math:`L_{\mathrm{Aeq},T}`,
        :math:`L_{\mathrm{Ceq},T}`, :math:`L_{\mathrm{AF5},T}`,
        :math:`L_{\mathrm{AF95},T}`, :math:`N_5`, :math:`N_{95}` and
        :math:`N_\mathrm{rmc}`, keyed by those symbols, ready for
        :class:`~phonometry.environment.assessment.soundscape.SoundscapeAcousticEnvironment`.

        :return: A new dictionary, symbol to value.
        :raises KeyError: if the sound pressure level or the loudness row was
            not computed.
        """
        return {symbol: self.representative(symbol) for symbol in _REPORTED_RESULTS}

    def plot(
        self,
        ax: Axes | None = None,
        *,
        parameter: str | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Plot one row of Table D.1: each metric at both ears, with the
        representative value marked.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param parameter: The row to draw, a key of
            :data:`BINAURAL_PARAMETERS`; ``None`` draws the first one computed.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the left-ear bars.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        :raises ValueError: if the row was not computed or nothing was.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_binaural_indicators

        computed = [
            name
            for name in BINAURAL_PARAMETERS
            if any(m.parameter == name for m in self.metrics.values())
        ]
        if not computed:
            msg = "No metric of Table D.1 was computed, so there is nothing to plot."
            raise ValueError(msg)
        chosen = computed[0] if parameter is None else parameter
        if chosen not in computed:
            msg = f"'parameter' must be one of the rows computed, {computed}; got {parameter!r}."
            raise ValueError(msg)
        return plot_binaural_indicators(
            self, ax=ax, parameter=chosen, language=check_language(language), **kwargs
        )


def _two_channels(
    x: SignalInput, fs: float | None, calibration_factor: float | None
) -> tuple[NDArray[np.float64], float]:
    """The two channels in pascals, left first, and the sampling frequency."""
    rate = resolve_fs(x, fs)
    factor = resolve_calibration(x, calibration_factor)
    if not math.isfinite(factor) or factor <= 0.0:
        msg = "'calibration_factor' must be a positive, finite number."
        raise ValueError(msg)
    samples = np.asarray(resolve_samples(x, calibrate=False), dtype=np.float64)
    if samples.ndim != 2 or samples.shape[0] != _CHANNELS:  # noqa: PLR2004
        msg = (
            "'x' must be a binaural recording of shape (2, samples), left ear "
            f"first; got shape {samples.shape}."
        )
        raise ValueError(msg)
    if samples.shape[1] == 0:
        msg = "'x' must not be empty."
        raise ValueError(msg)
    if not math.isfinite(rate) or rate <= 0.0:
        msg = f"'fs' must be a positive sampling frequency, got {rate!r}."
        raise ValueError(msg)
    return samples * factor, float(rate)


def _check_recording(duration_s: float, fs: float) -> None:
    """Warn where the recording falls short of ISO/TS 12913-2 Annex D."""
    if duration_s < _MINIMUM_INTERVAL_S:
        warnings.warn(
            f"The recording lasts {duration_s:.1f} s; ISO/TS 12913-2 D.3 requires a "
            "measurement time interval of at least 3 min.",
            SoundscapeWarning,
            stacklevel=3,
        )
    if fs < _MINIMUM_FS_HZ:
        warnings.warn(
            f"The sampling frequency is {fs:g} Hz; ISO/TS 12913-2 D.6 requires at "
            "least 44,1 kHz.",
            SoundscapeWarning,
            stacklevel=3,
        )


def _metric(symbol: str, parameter: str, left: float, right: float) -> BinauralMetric:
    return BinauralMetric(
        symbol=symbol,
        parameter=parameter,
        left=float(left),
        right=float(right),
        unit=_UNITS[symbol],
        method=_METHODS[symbol],
    )


def _sound_pressure_levels(
    pressure: NDArray[np.float64], fs: float
) -> list[BinauralMetric]:
    """``LAeq,T``, ``LCeq,T``, ``LAF5,T`` and ``LAF95,T`` of each ear."""
    rate = int(round(fs))
    a_eq = np.atleast_1d(laeq(pressure, rate, calibration_factor=1.0))
    c_eq = np.atleast_1d(
        leq(weighting_filter(pressure, rate, "C"), calibration_factor=1.0)
    )
    percentiles = ln_levels(
        pressure, rate, n=(5, 95), mode="fast", weighting="A", calibration_factor=1.0
    )
    l5 = np.atleast_1d(percentiles[5])
    l95 = np.atleast_1d(percentiles[95])
    parameter = "sound_pressure_level"
    return [
        _metric("LAeq,T", parameter, a_eq[0], a_eq[1]),
        _metric("LCeq,T", parameter, c_eq[0], c_eq[1]),
        _metric("LAF5,T", parameter, l5[0], l5[1]),
        _metric("LAF95,T", parameter, l95[0], l95[1]),
    ]


def _loudness(
    pressure: NDArray[np.float64], fs: float, field: _Field
) -> list[BinauralMetric]:
    """``N5``, ``Naverage``, ``Nrmc``, ``N95`` and ``N5/N95`` of each ear.

    ``N5`` is the library's ISO 532-1 value, taken on the full-rate series of
    the reference program. ``N95`` is the same percentile rule applied to the
    published 500 Hz loudness-versus-time trace, and ``Naverage`` and
    ``Nrmc`` are its arithmetic mean and root mean cube (ISO/TS 12913-2 A.3
    f)).
    """
    values: dict[str, list[float]] = {
        s: [] for s in BINAURAL_PARAMETERS["loudness"].metrics
    }
    for channel in pressure:
        result = loudness_zwicker(
            channel,
            round(fs),
            field=field,
            calibration_factor=1.0,
        )
        trace = np.asarray(result.loudness_vs_time, dtype=np.float64)
        n5 = float(result.n5) if result.n5 is not None else math.nan
        n95 = _percentile(trace, 95)
        values["N5"].append(n5)
        values["Naverage"].append(float(np.mean(trace)))
        values["Nrmc"].append(float(np.cbrt(np.mean(trace**3))))
        values["N95"].append(n95)
        values["N5/N95"].append(n5 / n95 if n95 > 0.0 else math.inf)
    for symbol in ("N5", "N95", "N5/N95"):
        if not all(math.isfinite(v) for v in values[symbol]):
            msg = (
                "The loudness exceeded 95 % of the time is zero at an ear, so the "
                "ratio N5/N95 of ISO/TS 12913-3 D.2 is undefined; is the recording "
                "silent for most of its duration?"
            )
            raise ValueError(msg)
    return [_metric(s, "loudness", v[0], v[1]) for s, v in values.items()]


def _percentiles_after_settling(
    series: NDArray[np.float64], settling_frames: int
) -> tuple[float, float]:
    """The values exceeded 10 % and 50 % of the time, as ECMA-418-2 takes its
    single value: the first frames, while the model settles, left out.
    """
    kept = series[settling_frames:] if series.size > settling_frames else series
    if kept.size == 0:
        return 0.0, 0.0
    return float(np.percentile(kept, 90)), float(np.percentile(kept, 50))


def _roughness(
    pressure: NDArray[np.float64], fs: float, field: _Field
) -> list[BinauralMetric]:
    ten, fifty = [], []
    for channel in pressure:
        result = roughness_ecma(channel, fs, field=field)
        r10, r50 = _percentiles_after_settling(
            np.asarray(result.roughness_vs_time), _ROUGHNESS_SETTLING_FRAMES
        )
        ten.append(r10)
        fifty.append(r50)
    return [
        _metric("R10", "roughness", ten[0], ten[1]),
        _metric("R50", "roughness", fifty[0], fifty[1]),
    ]


def _fluctuation(
    pressure: NDArray[np.float64], fs: float, field: _Field
) -> list[BinauralMetric]:
    ten, fifty = [], []
    for channel in pressure:
        result = fluctuation_strength_ecma(channel, fs, field=field)
        f10, f50 = _percentiles_after_settling(
            np.asarray(result.fluctuation_strength_vs_time),
            _FLUCTUATION_SETTLING_FRAMES,
        )
        ten.append(f10)
        fifty.append(f50)
    return [
        _metric("F10", "fluctuation_strength", ten[0], ten[1]),
        _metric("F50", "fluctuation_strength", fifty[0], fifty[1]),
    ]


def _tonality(
    pressure: NDArray[np.float64], fs: float, field: _Field
) -> list[BinauralMetric]:
    values = [
        float(tonality_ecma(channel, fs, field=field).tonality) for channel in pressure
    ]
    return [_metric("T", "tonality", values[0], values[1])]


def binaural_indicators(
    x: SignalInput,
    fs: float | None = None,
    *,
    calibration_factor: float | None = None,
    field: Literal["free", "diffuse"] = "free",
    parameters: Sequence[str] = tuple(BINAURAL_PARAMETERS),
) -> BinauralIndicators:
    r"""The metrics of ISO/TS 12913-3 Table D.1 at each ear of a binaural
    recording, with their representative values (Annex D, D.2).

    Each channel is analysed on its own and every metric is reported for the
    left and the right ear; :attr:`BinauralMetric.representative` is the
    higher of the two, the single value D.2 uses "for all metrics
    considered", and :attr:`BinauralMetric.mean` their arithmetic mean. The
    loudness row adds the variability ratio :math:`N_5/N_{95}` D.2 suggests.
    Which library function computes which metric, and why the sharpness row
    stays empty, is in the module docstring; each metric carries its method.

    :param x: The equalized binaural recording, shape ``(2, samples)`` with
        the left ear first, in pascals after ``calibration_factor``; a
        :class:`~phonometry.io.Signal` with two channels brings its own rate
        and calibration.
    :param fs: Sampling frequency, in Hz. Required for a bare array; a
        :class:`~phonometry.io.Signal` brings its own, and an explicit value
        that disagrees with it raises.
    :param calibration_factor: Multiplier from the recorded units to pascals,
        the same for both channels. An explicit value wins over the one a
        Signal carries; a bare array with neither is taken to be in pascals.
    :param field: The sound field the recording was equalized for, ``"free"``
        (default) or ``"diffuse"``, passed to the loudness and the
        hearing-model metrics.
    :param parameters: The rows of Table D.1 to compute, keys of
        :data:`BINAURAL_PARAMETERS`; all of them by default.
    :return: A :class:`BinauralIndicators`.
    :raises ValueError: for a recording that is not two channels, an unknown
        field or row, or a loudness exceeded 95 % of the time of zero, which
        leaves :math:`N_5/N_{95}` undefined.
    :warns SoundscapeWarning: for a recording shorter than the 3 min of
        ISO/TS 12913-2 D.3 or sampled below the 44,1 kHz of D.6.
    """
    require_choice(field, "field", _FIELDS)
    if isinstance(parameters, str):
        parameters = (parameters,)
    rows = tuple(dict.fromkeys(parameters))
    if not rows:
        msg = "'parameters' must name at least one row of Table D.1."
        raise ValueError(msg)
    for name in rows:
        require_choice(name, "parameters", tuple(BINAURAL_PARAMETERS))
    pressure, rate = _two_channels(x, fs, calibration_factor)
    duration = pressure.shape[1] / rate
    _check_recording(duration, rate)
    computed: dict[str, BinauralMetric] = {}
    missing: dict[str, str] = {}
    for name in BINAURAL_PARAMETERS:
        if name not in rows:
            continue
        if name == "sound_pressure_level":
            found = _sound_pressure_levels(pressure, rate)
        elif name == "loudness":
            found = _loudness(pressure, rate, field)
        elif name == "sharpness":
            missing.update(
                dict.fromkeys(BINAURAL_PARAMETERS[name].metrics, _SHARPNESS_REASON)
            )
            continue
        elif name == "tonality":
            found = _tonality(pressure, rate, field)
        elif name == "roughness":
            found = _roughness(pressure, rate, field)
        else:
            found = _fluctuation(pressure, rate, field)
        computed.update({metric.symbol: metric for metric in found})
    return BinauralIndicators(
        metrics=computed,
        not_implemented=missing,
        parameters=rows,
        fs=rate,
        duration_s=duration,
        field=field,
    )
