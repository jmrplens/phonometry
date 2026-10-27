#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Frequency calculation logic according to ANSI/IEC standards."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from .._internal.frozen import OwnsArrays, read_only
from .._internal.validation import require_positive, require_scalar
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

# IEC 61260-1 Annex E.3: a most-significant digit of 1-4 keeps three
# significant figures, one of 5-9 keeps two.
_ANNEX_E3_MSD_THRESHOLD = 5.0

# Adjacent mid-band centre ratio separating the two IEC 61260 band structures:
# octave spacing (2) above it, one-third-octave spacing (2**(1/3) ~ 1.26) below.
# The value is the geometric midpoint of those two nominal steps, equidistant
# from both in ratio space, so a grid must err by more than half a third-octave
# step before it is classed with the wrong structure. One constant, shared with
# the ISO 10848 octave grouping in building.measurement.flanking_transmission:
# the library used to hold 1.5 here and 1.6 there for the same discriminant.
_OCTAVE_SPACING_MIN_RATIO = 2.0 ** (2.0 / 3.0)

# One kilohertz in hertz: the boundary at which a nominal-frequency label
# switches to the abbreviated "k" form, and the Hz-to-kHz divisor.
_HZ_PER_KHZ = 1000


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
        if isinstance(self.labels, (str, bytes)):
            msg = (
                "FractionalOctaveBands: 'labels' must hold one label per band, "
                f"not a single string; got {self.labels!r}."
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
        frequencies=np.asarray(frequencies, dtype=np.float64),
        lower_edges=np.asarray(lower_edges, dtype=np.float64),
        upper_edges=np.asarray(upper_edges, dtype=np.float64),
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

    x = _initindex(limits[0], fr, g, fraction)
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


def _deleteouters(bands: FractionalOctaveBands, fs: int) -> FractionalOctaveBands:
    """Remove the bands whose upper edge exceeds the Nyquist frequency.

    :param bands: The bands the limits asked for.
    :param fs: Sample rate.
    :return: The bands a bank at ``fs`` can hold, in the same order.
    """
    keep = bands.upper_edges <= fs / 2
    if np.all(keep):
        return bands
    warnings.warn(
        "Low sampling rate: frequencies above fs/2 removed",
        FilterBankWarning,
        stacklevel=3,
    )
    return _band_set(
        bands.frequencies[keep],
        bands.lower_edges[keep],
        bands.upper_edges[keep],
        [label for label, kept in zip(bands.labels, keep, strict=True) if kept],
    )


def _genfreqs(limits: RealValues, fraction: float, fs: int) -> FractionalOctaveBands:
    """Determine the bands within limits that a bank at ``fs`` can hold.

    :param limits: [f_min, f_max].
    :param fraction: Bandwidth fraction.
    :param fs: Sample rate.
    :return: The bands, without those above the Nyquist frequency.
    """
    return _deleteouters(nominal_frequencies(fraction, limits), fs)


def _iec_e3_round(f: float) -> float:
    """IEC 61260-1 Annex E.3: 3 sig figs if MSD 1–4, 2 sig figs if MSD 5–9."""
    if f <= 0:
        return f
    exponent = int(np.floor(np.log10(f)))
    msd = f / (10.0**exponent)
    step = (
        10.0 ** (exponent - 2)
        if msd < _ANNEX_E3_MSD_THRESHOLD
        else 10.0 ** (exponent - 1)
    )
    return round(f / step) * step


@lru_cache(maxsize=4)
def _extended_preferred(frac: int) -> list[float]:
    """Cached expansion of the IEC preferred frequency table across decades.

    A decade below the table divides by the power of ten instead of
    multiplying by its reciprocal, which binary cannot hold exactly:
    ``31.5 / 10`` is the double nearest 3.15, ``31.5 * 0.1`` is
    ``3.1500000000000004``.
    """
    base = normalized_frequencies(frac)
    return [f * 10**d if d >= 0 else f / 10**-d for d in range(-3, 4) for f in base]


def _nominal_freq_for_band(exact_freq: float, fraction: float) -> float:
    """Return IEC 61260-1 nominal frequency (float) for an exact mid-band frequency.

    For standard fractions (1, 3), snaps to the IEC preferred table via
    ``normalized_frequencies``.  For non-standard fractions, falls back to Annex E.3
    significant-figure rounding (``_iec_e3_round``).
    """
    frac = round(fraction)
    if np.isclose(fraction, frac) and frac in (1, 3):
        extended = _extended_preferred(frac)
        return min(extended, key=lambda f: abs(np.log(f / exact_freq)))
    return _iec_e3_round(exact_freq)


def _infer_band_fraction(frequency: np.ndarray) -> int:
    """Octave (1) or one-third-octave (3) from adjacent band-centre ratios.

    Distinguishes the two IEC 61260 band structures by the ratio of adjacent
    mid-band centres (2 for octaves, 2**(1/3) ~ 1.26 for one-third octaves).
    Fewer than two bands cannot be told apart, so octave (1) is returned as the
    conventional default. Shared by the room-acoustics plot renderer and the
    report fiche so they classify a band set identically.
    """
    freq = np.asarray(frequency, dtype=np.float64)
    # The fewest values the step below can work with, not a quantity.
    if freq.size < 2:  # noqa: PLR2004
        return 1
    return 1 if float(freq[1] / freq[0]) > _OCTAVE_SPACING_MIN_RATIO else 3


def _format_nominal_freq(f: float) -> str:
    """Format a nominal frequency as a human-readable label string."""
    if f >= _HZ_PER_KHZ:
        return f"{f / _HZ_PER_KHZ:g}k"
    return f"{f:g}"


def normalized_frequencies(fraction: int) -> list[float]:
    """Standardized IEC center frequencies.

    :param fraction: 1 or 3 (Octave or 1/3 Octave).
    :return: List of standard frequencies.
    :raises TypeError: if ``fraction`` is not a single number.
    """
    require_scalar(fraction, "fraction")
    predefined = {
        1: [16, 31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000],
        3: [
            12.5,
            16,
            20,
            25,
            31.5,
            40,
            50,
            63,
            80,
            100,
            125,
            160,
            200,
            250,
            315,
            400,
            500,
            630,
            800,
            1000,
            1250,
            1600,
            2000,
            2500,
            3150,
            4000,
            5000,
            6300,
            8000,
            10000,
            12500,
            16000,
            20000,
        ],
    }
    if fraction not in predefined:
        msg = "Normalized frequencies only available for fraction=1 or 3"
        raise ValueError(msg)
    return predefined[fraction]
