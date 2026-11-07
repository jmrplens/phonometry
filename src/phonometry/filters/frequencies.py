#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Frequency calculation logic according to ANSI/IEC standards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.bands import (
    PREFERRED_FREQUENCIES,
    _format_nominal_freq,
    _nominal_freq_for_band,
    bands_held,
)
from .._internal.frozen import OwnsArrays, given_repr, read_only
from .._internal.validation import (
    is_text,
    real_array,
    real_number,
    require_count,
    require_positive,
)
from ._warnings import FilterBankWarning

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from .._internal.types import RealValues

__all__ = [
    "FractionalOctaveBands",
    "nominal_frequencies",
    "normalized_frequencies",
]


@dataclass(frozen=True)
class FractionalOctaveBands(OwnsArrays):
    r"""A set of fractional-octave bands: centres, edges and nominal labels.

    What :func:`nominal_frequencies` returns and what an
    :class:`~phonometry.filters.OctaveFilterBank` is designed on. The three
    frequency arrays are read-only, in hertz, one value per band in ascending
    order; the labels are the IEC 61260-1 nominal mid-band frequencies, as
    text (``"31.5"``, ``"1k"``). It is a record with named fields rather than
    a tuple, so it cannot be unpacked by position: read ``.frequencies``,
    ``.lower_edges``, ``.upper_edges`` or ``.labels``.

    :ivar frequencies: The exact mid-band frequencies :math:`f_\mathrm{m}`,
        in hertz (IEC 61260-1:2014 5.4).
    :ivar lower_edges: The lower band-edge frequencies :math:`f_1`, in hertz.
    :ivar upper_edges: The upper band-edge frequencies :math:`f_2`, in hertz.
    :ivar labels: The nominal mid-band frequency of each band, as a string.
    """

    frequencies: NDArray[np.float64]
    lower_edges: NDArray[np.float64]
    upper_edges: NDArray[np.float64]
    labels: tuple[str, ...]

    def __post_init__(self) -> None:
        """Hold every column as a read-only array or a tuple, one entry per band.

        :raises ValueError: if a column is not one-dimensional, the columns
            disagree in length, or a band's edges do not enclose its centre.
        :raises TypeError: if ``labels`` is one string rather than one label
            per band, which would otherwise be split into its characters.
        """
        if is_text(self.labels):
            msg = (
                "FractionalOctaveBands: 'labels' must hold one label per band, "
                f"not a single string; got {given_repr(self.labels)}."
            )
            raise TypeError(msg)
        columns = {}
        for name in ("frequencies", "lower_edges", "upper_edges"):
            values = np.asarray(getattr(self, name), dtype=np.float64)
            if values.ndim != 1:
                msg = (
                    f"FractionalOctaveBands: '{name}' must be one-dimensional; "
                    f"got shape {values.shape}."
                )
                raise ValueError(msg)
            columns[name] = values
            object.__setattr__(self, name, read_only(values))
        labels = tuple(str(label) for label in self.labels)
        object.__setattr__(self, "labels", labels)
        counts = {name: values.size for name, values in columns.items()}
        counts["labels"] = len(labels)
        if len(set(counts.values())) > 1:
            listed = ", ".join(f"{name}={count}" for name, count in counts.items())
            msg = f"FractionalOctaveBands: one entry per band in every column; got {listed}."
            raise ValueError(msg)
        if not np.all(
            (columns["lower_edges"] < columns["frequencies"])
            & (columns["frequencies"] < columns["upper_edges"])
        ):
            msg = (
                "FractionalOctaveBands: every band's edges must enclose its "
                "centre (lower_edges < frequencies < upper_edges)."
            )
            raise ValueError(msg)


def _band_set(
    frequencies: Sequence[float] | NDArray[np.float64],
    lower_edges: Sequence[float] | NDArray[np.float64],
    upper_edges: Sequence[float] | NDArray[np.float64],
    labels: Sequence[str],
) -> FractionalOctaveBands:
    """A :class:`FractionalOctaveBands` built from the computed columns."""
    return FractionalOctaveBands(
        frequencies=real_array(frequencies, "frequencies"),
        lower_edges=real_array(lower_edges, "lower_edges"),
        upper_edges=real_array(upper_edges, "upper_edges"),
        labels=tuple(labels),
    )


def nominal_frequencies(
    fraction: float,
    limits: RealValues | None = None,
) -> FractionalOctaveBands:
    r"""The fractional-octave bands that cover a frequency range.

    The mid-band frequencies are the base-ten series of IEC 61260-1:2014 5.4,
    :math:`f_\mathrm{m} = 1000\,G^{x/b}` Hz with :math:`G = 10^{3/10}` (an
    even ``fraction`` shifts the series by half a band), and the band edges
    sit a factor :math:`G^{1/(2b)}` either side of each centre. The first band
    is the one nearest ``limits[0]`` and the last the first whose upper edge
    reaches ``limits[1]``.

    :param fraction: Bandwidth fraction ``b`` (e.g., 1 for octaves, 3 for
        one-third octaves).
    :param limits: ``[f_min, f_max]`` in hertz, a sequence or an array of
        the two (Default: ``[12, 20000]``).
    :return: A :class:`FractionalOctaveBands` with the exact centres
        (``.frequencies``), the band edges (``.lower_edges`` and
        ``.upper_edges``) and the nominal labels (``.labels``).
    :raises ValueError: for a non-positive or non-finite ``fraction``.
    :raises TypeError: if ``fraction`` is not a single number.
    """
    # Zero used to reach _bandedge's division, NaN the index rounding, and a
    # negative fraction never terminated: the band centres underflow to 0.0
    # and the edge test stays true forever.
    fraction = require_positive(fraction, "fraction")
    if limits is None:
        limits = [12, 20000]

    g = 10 ** (3 / 10)
    fr = 1000

    x = _initindex(real_number(limits[0], "limits"), fr, g, fraction)
    freq_list = [_ratio(g, x, fraction) * fr]

    while freq_list[-1] * _bandedge(g, fraction) < limits[1]:
        x += 1
        freq_list.append(_ratio(g, x, fraction) * fr)
    freq = np.array(freq_list)

    freq_d = freq / _bandedge(g, fraction)
    freq_u = freq * _bandedge(g, fraction)

    labels = [
        _format_nominal_freq(_nominal_freq_for_band(f, fraction)) for f in freq.tolist()
    ]
    return _band_set(freq, freq_d, freq_u, labels)


def _initindex(f: float, fr: float, g: float, b: float) -> int:
    """Calculate starting index for band generation.

    :param f: Frequency.
    :param fr: Reference frequency.
    :param g: Base ratio.
    :param b: Bandwidth fraction.
    :return: Index integer.
    """
    if round(b) % 2:
        return int(np.round((b * np.log(f / fr) + 30 * np.log(g)) / np.log(g)))
    return int(np.round((2 * b * np.log(f / fr) + 59 * np.log(g)) / (2 * np.log(g))))


def _ratio(g: float, x: int, b: float) -> float:
    """Calculate ratio for center frequency.

    :param g: Base ratio.
    :param x: Index.
    :param b: Bandwidth fraction.
    :return: Frequency ratio.
    """
    if round(b) % 2:
        return float(g ** ((x - 30) / b))
    return float(g ** ((2 * x - 59) / (2 * b)))


def _bandedge(g: float, b: float) -> float:
    """Calculate band-edge ratio.

    :param g: Base ratio.
    :param b: Bandwidth fraction.
    :return: Edge ratio.
    """
    return float(g ** (1 / (2 * b)))


def _genfreqs(
    limits: RealValues, fraction: float, fs: float, *, warn: bool
) -> FractionalOctaveBands:
    """Determine the bands within limits that a bank at ``fs`` can hold.

    A band whose upper edge lies above the Nyquist frequency is left out. A
    caller who asked for those limits is told which with a
    :class:`FilterBankWarning`; the default span is trimmed to what ``fs``
    holds without one, since nobody asked for its top bands at that rate. A
    rate that holds no band of the span at all is refused, whoever chose the
    span: a bank of no band would analyse nothing and say so nowhere.

    :param limits: [f_min, f_max].
    :param fraction: Bandwidth fraction.
    :param fs: Sample rate.
    :param warn: Whether the caller gave the limits, so a band left out is
        named in a warning.
    :return: The bands, without those above the Nyquist frequency.
    :raises ValueError: when the upper edge of every band is above fs/2.
    """
    bands = nominal_frequencies(fraction, limits)
    keep = bands_held(
        bands.labels,
        bands.upper_edges,
        fs,
        warn=warn,
        category=FilterBankWarning,
    )
    if np.all(keep):
        return bands
    return _band_set(
        bands.frequencies[keep],
        bands.lower_edges[keep],
        bands.upper_edges[keep],
        [label for label, kept in zip(bands.labels, keep, strict=True) if kept],
    )


def normalized_frequencies(fraction: int | np.integer[Any]) -> list[float]:
    """Standardized IEC center frequencies.

    :param fraction: 1 or 3 (Octave or 1/3 Octave).
    :return: List of standard frequencies.
    :raises ValueError: for a ``fraction`` other than 1 and 3.
    :raises TypeError: if ``fraction`` is a flag, a text or an array where a
        whole number goes.
    """
    fraction = require_count(fraction, "fraction")
    if fraction not in PREFERRED_FREQUENCIES:
        msg = "Normalized frequencies only available for fraction=1 or 3"
        raise ValueError(msg)
    return list(PREFERRED_FREQUENCIES[fraction])
