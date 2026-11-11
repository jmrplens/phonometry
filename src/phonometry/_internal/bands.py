#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The fractional-octave bands of IEC 61260-1, as numbers every package reads.

The preferred nominal frequencies, the snap of an exact mid-band frequency to
its nominal value (Annex E), the ratio that tells an octave grid from a
one-third-octave one, and the rule that leaves out of a bank at ``fs`` the
bands whose upper edge lies above the Nyquist frequency. The filter bank of
:mod:`phonometry.filters` designs on them, and the band levels of
:mod:`phonometry.emission`, the band grouping of :mod:`phonometry.building`
and the band labels of :mod:`phonometry.vibration` read them directly,
without importing another domain.
"""

from __future__ import annotations

from functools import lru_cache
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

from .validation import real_array
from .warnings import warn_caller

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from numpy.typing import NDArray

    from .warnings import PhonometryWarning

__all__ = ["PREFERRED_FREQUENCIES", "bands_held"]

# One kilohertz in hertz: the boundary at which a nominal-frequency label
# switches to the abbreviated "k" form, and the Hz-to-kHz divisor.
_HZ_PER_KHZ = 1000

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

#: The preferred nominal mid-band frequencies of IEC 61260-1, in hertz, keyed
#: by the bandwidth fraction: octaves (1) and one-third octaves (3).
PREFERRED_FREQUENCIES: Mapping[int, tuple[float, ...]] = MappingProxyType(
    {
        1: (16, 31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000),
        3: (
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
        ),
    }
)


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
    base = PREFERRED_FREQUENCIES[frac]
    return [f * 10**d if d >= 0 else f / 10**-d for d in range(-3, 4) for f in base]


def _nominal_freq_for_band(exact_freq: float, fraction: float) -> float:
    """Return IEC 61260-1 nominal frequency (float) for an exact mid-band frequency.

    For standard fractions (1, 3), snaps to the IEC preferred table of
    :data:`PREFERRED_FREQUENCIES`.  For non-standard fractions, falls back to Annex E.3
    significant-figure rounding (``_iec_e3_round``).
    """
    frac = round(fraction)
    if np.isclose(fraction, frac) and frac in (1, 3):
        extended = _extended_preferred(frac)
        return min(extended, key=lambda f: abs(np.log(f / exact_freq)))
    return _iec_e3_round(exact_freq)


def _infer_band_fraction(frequency: NDArray[np.float64]) -> int:
    """Octave (1) or one-third-octave (3) from adjacent band-centre ratios.

    Distinguishes the two IEC 61260 band structures by the ratio of adjacent
    mid-band centres (2 for octaves, 2**(1/3) ~ 1.26 for one-third octaves).
    Fewer than two bands cannot be told apart, so octave (1) is returned as the
    conventional default. Shared by the room-acoustics plot renderer and the
    report fiches so they classify a band set identically.
    """
    freq = real_array(frequency, "frequency")
    # The fewest values the step below can work with, not a quantity.
    if freq.size < 2:  # noqa: PLR2004
        return 1
    return 1 if float(freq[1] / freq[0]) > _OCTAVE_SPACING_MIN_RATIO else 3


def _format_nominal_freq(f: float) -> str:
    """Format a nominal frequency as a human-readable label string."""
    if f >= _HZ_PER_KHZ:
        return f"{f / _HZ_PER_KHZ:g}k"
    return f"{f:g}"


def _band_name(label: str) -> str:
    """A nominal label as a frequency a reader says: ``"20k"`` is 20 kHz."""
    if label.endswith("k"):
        return f"{label[:-1]} kHz"
    return f"{label} Hz"


def _left_out(
    labels: Sequence[str],
    upper_edges: NDArray[np.float64],
    keep: NDArray[np.bool_],
    fs: float,
) -> str:
    """The warning that names the bands a bank at ``fs`` leaves out.

    It opens with ``Low sampling rate``, the text a filter on the message and
    the upgrading guide read, and names the bands and fs/2.
    """
    names = [
        _band_name(label)
        for label, kept in zip(labels, keep.tolist(), strict=True)
        if not kept
    ]
    if len(names) == 1:
        edge = upper_edges[~keep][0]
        return (
            f"Low sampling rate: fs = {fs:g} Hz cannot hold the {names[0]} band, "
            f"whose upper edge {edge:.0f} Hz is above fs/2 = {fs / 2:g} Hz; it "
            "was left out of the bank."
        )
    return (
        f"Low sampling rate: fs = {fs:g} Hz cannot hold the {len(names)} bands "
        f"from {names[0]} to {names[-1]}, whose upper edges are above fs/2 = "
        f"{fs / 2:g} Hz; they were left out of the bank."
    )


def _holds_none(
    labels: Sequence[str], upper_edges: NDArray[np.float64], fs: float
) -> str:
    """The refusal of a rate that holds not one band of the span."""
    names = [_band_name(label) for label in labels]
    edge = upper_edges[0]
    if len(names) == 1:
        return (
            f"fs = {fs:g} Hz cannot hold the {names[0]} band, the only one of "
            f"the bank: its upper edge, {edge:.4g} Hz, is above fs/2 = "
            f"{fs / 2:g} Hz."
        )
    return (
        f"fs = {fs:g} Hz cannot hold any band from {names[0]} to {names[-1]}: "
        f"the upper edge of the lowest, {edge:.4g} Hz, is above fs/2 = "
        f"{fs / 2:g} Hz."
    )


def bands_held(
    labels: Sequence[str],
    upper_edges: NDArray[np.float64],
    fs: float,
    *,
    warn: bool,
    category: type[PhonometryWarning],
) -> NDArray[np.bool_]:
    """Which bands a bank at ``fs`` holds: those whose upper edge is at most fs/2.

    A rate that holds no band at all is refused, whoever chose the span: a
    bank of no band would analyse nothing and say so nowhere. When the caller
    was handed the limits, the bands left out are named in a warning of
    *category*; the default span is trimmed to what ``fs`` holds without one.

    :param labels: The nominal label of each band.
    :param upper_edges: The upper band-edge frequencies, in hertz.
    :param fs: Sample rate, in Hz.
    :param warn: Whether the caller was handed the limits, so a band left out
        is named in a warning.
    :param category: The warning that names the bands left out.
    :return: One flag per band, ``True`` where the bank holds it.
    :raises ValueError: when the upper edge of every band is above fs/2.
    """
    keep = upper_edges <= fs / 2
    if np.all(keep):
        return keep
    if not np.any(keep):
        raise ValueError(_holds_none(labels, upper_edges, fs))
    if warn:
        warn_caller(_left_out(labels, upper_edges, keep, fs), category)
    return keep
