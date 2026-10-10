#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Amplitude modulation of wind turbine sound at a receptor (IEC TS 61400-11-2:2024, clause 13).

A turbine's level rises and falls once per blade passage, the "swish" or
"thump" a neighbour describes. Clause 13 of IEC TS 61400-11-2:2024 rates it
with the reference method of the UK Institute of Acoustics Amplitude
Modulation Working Group (the AMWG Final Report, 2016), which the TS
implements (13.2) with more specific outputs and the worst case band in each
bin. The input is a series of A-weighted 100 ms ``Leq`` values summed over
seven one-third-octave bands (13.6.2.1.1):
:func:`amplitude_modulation_band_levels` forms it from logged band levels.

**The 10 s block** (13.6.2.3), :func:`amplitude_modulation_block`. The 100
values are de-trended with a cubic least-squares fit, transformed with a
rectangular-window DFT of 0.1 Hz resolution and turned into the power
spectrum

.. math::

   S_{xx} = \frac{|F\{x\}|^2}{m^2}, \qquad m = 100 \tag{12}

The highest local maximum inside the user's range of fundamental modulation
frequencies is the fundamental. Its prominence is the line itself over the
linear mean of the two lines beyond each adjacent line,

.. math::

   p_\mathrm{AM} = \frac{L_\mathrm{pk}}{L_\mathrm{m}} \tag{13}

and a block with no local maximum in the range, or with
:math:`p_\mathrm{AM} < 4`, is "prominence-failed". The second and third
harmonics join if a local maximum sits at (or within one or two lines of)
twice and three times the fundamental and both the fundamental alone and the
harmonic alone swing more than 1.5 dB peak to peak. Three lines about each
kept component, with their negative-frequency mirrors, are transformed back,
and the modulation depth is the 95th percentile of the reconstructed series
minus its 5th percentile (``L5 - L95``).

**The 10 min period** (13.6.3), :func:`amplitude_modulation_period`: the AM
rating is the 90th percentile of the valid 10 s depths when at least 30 of the
60 blocks are valid, and 0 dB otherwise, with the mean and the mode of the
valid fundamental frequencies.

**The bins** (13.6.4), :func:`bin_amplitude_modulation`: the 10 min ratings
of each band are averaged per 1 m/s wind speed bin and 30 degree sector, the
zeros included, and each bin reports the band with the highest mean.

Where the TS and the AMWG Final Report part ways, the TS is implemented: a
period with fewer than 30 valid blocks is kept at 0 dB and counted in its bin
(TS 13.6.3, 13.6.4), where the AMWG discards it (Figure 4.2.2); and the band is
chosen per bin (TS 13.6.4), where the AMWG chooses one band for the whole
survey by regressing the three bands' ratings against each other (Figure
4.2.1, 4.3.2). 13.6.4 also leaves out of the bin mean "any excluded periods
due to pf or other exclusions"; read literally, that would drop the very
periods 13.6.3 rates 0 dB (their blocks failed the prominence test), and the
"including 0 values" of the same sentence, with the count of non-zero values
13.6.4 asks for, would mean nothing. It is read as the periods the
practitioner excludes, the ``excluded`` flags of
:func:`bin_amplitude_modulation`. The TS says both "at least 50 %" (13.6.2.2)
and "greater than 50 % (30 valid 10 s blocks)" (13.6.3) of a period's blocks;
a period of exactly 30 valid blocks is rated, as 13.6.2.2 and the AMWG (4.4.4,
"at least 50 % (i.e. 30)") both say.

Two steps the TS leaves open are read as the IOA's published reference code
reads them: the percentiles interpolate linearly between the order
statistics, and the spectrum runs from 0.1 Hz to 4.9 Hz, without the zero
frequency the de-trending has emptied and without the Nyquist line, whose
three-line window would have no mirror of its own.

A spectral line within rounding of zero is read as zero: a line no larger than
the square of :math:`10^{-9}` of the block's largest absolute level. Once
de-trended, a steady block, or one that follows a cubic, holds nothing else, so
it has no local maximum and is prominence-failed, the block of 13.6.2.3 d) in
which "there is no significant AM" (the AMWG Final Report, 4.5.2 step 4:
"either no AM, or the block is corrupted"). Read as they come out of the fit,
its rounding lines would decide its status by their last bits.
"""

from __future__ import annotations

import math
from dataclasses import KW_ONLY, dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.levels_math import energy_sum
from ..._internal.validation import (
    is_class_designation,
    require_finite_array,
    require_finite_matrix,
    require_scalar,
)
from .wind_turbine_receptor import _A_WEIGHTING_DB, _bin_keys, _type_a_arithmetic

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "AM_BLOCK_SAMPLES",
    "AM_EXCEEDANCE_THRESHOLDS_DB",
    "AM_FREQUENCY_BANDS_HZ",
    "AM_MINIMUM_VALID_BLOCKS",
    "AM_MODULATION_FREQUENCY_LIMITS_HZ",
    "AM_PERIOD_BLOCKS",
    "AM_PROMINENCE_THRESHOLD",
    "AM_SAMPLE_INTERVAL_S",
    "BinnedModulation",
    "ModulationBlock",
    "ModulationBlockStatus",
    "ModulationPeriod",
    "amplitude_modulation_band_levels",
    "amplitude_modulation_block",
    "amplitude_modulation_period",
    "bin_amplitude_modulation",
]

#: Duration of one sample of the input series, in seconds: the 100 ms
#: ``Leq`` of 13.4 and 13.6.1.
AM_SAMPLE_INTERVAL_S: float = 0.1

#: Samples in one 10 s block, the minor time interval of 13.6.2.2.
AM_BLOCK_SAMPLES: int = 100

#: 10 s blocks in one 10 min period, the major time interval (13.6.2.2).
AM_PERIOD_BLOCKS: int = 60

#: Valid 10 s blocks a 10 min period needs to be rated, half of its sixty
#: (13.6.2.2 "at least 50 %"; 13.6.3).
AM_MINIMUM_VALID_BLOCKS: int = 30

#: Prominence ratio below which a 10 s block is prominence-failed (13.6.2.3 e).
AM_PROMINENCE_THRESHOLD: float = 4.0

#: Modulation frequencies the method applies to, in Hz (13.2: "0,3 Hz to
#: 1,6 Hz"); the user's range of fundamental frequencies lies inside it.
AM_MODULATION_FREQUENCY_LIMITS_HZ: tuple[float, float] = (0.3, 1.6)

#: The seven one-third-octave band centre frequencies each band sums, in Hz.
#: Bands 1 to 3 are the standard ones of 13.6.2.1.1; bands 4 to 6 are the
#: higher ones Annex G.3 suggests where the modulating sound lies above
#: 800 Hz. G.3 ends bands 5 and 6 at "3 200 Hz" and "6 400 Hz"; the
#: seventh band of each is the nominal 3 150 Hz and 6 300 Hz one-third
#: octave.
AM_FREQUENCY_BANDS_HZ: Mapping[int, tuple[float, ...]] = MappingProxyType(
    {
        1: (50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0),
        2: (100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0),
        3: (200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0),
        4: (400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0),
        5: (800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0),
        6: (1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0),
    }
)

#: Modulation depths the binned results count the data points above, in dB
#: (13.7 a) iii)).
AM_EXCEEDANCE_THRESHOLDS_DB: tuple[float, float, float] = (3.0, 6.0, 9.0)

#: Peak-to-peak swing, in dB, that the fundamental alone and a harmonic alone
#: each have to exceed for the harmonic to be kept (13.6.2.3 f)).
_HARMONIC_SWING_DB = 1.5
#: Lines searched either side of 2 and 3 times the fundamental (13.6.2.3 f)).
_HARMONIC_SEARCH_LINES: Mapping[int, int] = MappingProxyType({2: 1, 3: 2})
#: Offsets, in lines, of the masking lines of the prominence (13.6.2.3 e)):
#: the two lines beyond each line adjacent to the peak.
_MASKING_OFFSETS = (-3, -2, 2, 3)
#: Percentiles of the reconstructed series whose difference is the depth.
_UPPER_PERCENTILE, _LOWER_PERCENTILE = 95.0, 5.0
#: Percentile of the valid 10 s depths that rates a 10 min period (13.6.3).
_RATING_PERCENTILE = 90.0
#: Tolerance, in lines, for placing a range limit on the 0.1 Hz grid.
_GRID_TOLERANCE = 1e-9
#: Fraction of a block's largest absolute level under which a spectral
#: component is rounding: a line of the power spectrum no larger than the
#: square of this fraction of that level counts as zero (see
#: :func:`_settled_spectrum`). The cubic fit of a steady 40 dB block leaves a
#: residual of 8e-14 dB, 2e-15 of the level, and a tenth of a decibel of
#: modulation is 2.5e-3 of it.
_ROUNDING_FRACTION = 1e-9
#: Length of one 10 s block, in s: spectrum line k lies at k over it, so the
#: line frequencies are divided out rather than multiplied by 0.1 Hz, which
#: would print 0.7 Hz as 0.7000000000000001.
_BLOCK_DURATION_S = AM_BLOCK_SAMPLES * AM_SAMPLE_INTERVAL_S
#: Relative tolerance matching a supplied band centre to a nominal one.
_NOMINAL_MATCH = 0.01


class ModulationBlockStatus(StrEnum):
    """Why a 10 s block counts or does not (13.6.2.2 and 13.6.2.3).

    ``VALID`` blocks carry a modulation depth. ``NO_PEAK`` and
    ``LOW_PROMINENCE`` are the two prominence-failed (pf) outcomes of
    13.6.2.3 d) and e): no local maximum inside the range of fundamental
    frequencies, or a prominence ratio under 4. A steady block, or one that
    follows a cubic, is ``NO_PEAK``: once de-trended it holds nothing but
    rounding, the case in which d) considers "that there is no significant
    AM". ``EXCLUDED`` is a block the practitioner excluded by hand (13.6.2.2,
    third bullet).
    """

    VALID = "valid"
    NO_PEAK = "no_peak"
    LOW_PROMINENCE = "low_prominence"
    EXCLUDED = "excluded"


def _nominal_index(frequencies: NDArray[np.float64], centre: float) -> int:
    """Index of the supplied band whose centre is the nominal ``centre``."""
    match = np.nonzero(np.abs(frequencies - centre) <= _NOMINAL_MATCH * centre)[0]
    if match.size != 1:
        msg = (
            f"'frequencies_hz' must hold the one-third-octave band centred at "
            f"{centre:g} Hz exactly once."
        )
        raise ValueError(msg)
    return int(match[0])


def amplitude_modulation_band_levels(
    band_levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    band: int,
    weighting: Literal["A", "Z"],
) -> NDArray[np.float64]:
    """Band-limited A-weighted 100 ms levels of one AM band (13.6.2.1.1).

    The 100 ms one-third-octave band ``Leq`` values of the seven bands of
    ``band`` are A-weighted, if they were logged unweighted, and summed
    logarithmically sample by sample into the ``LAeq,100ms (BP)`` series the
    10 s analysis takes. The A-weighting is the IEC 61672-1:2013 Table 3
    value at each nominal centre frequency.

    :param band_levels_db: The logged band levels, in dB: one row per 100 ms
        sample and one column per one-third-octave band (a single sample may
        be given as one row).
    :param frequencies_hz: Nominal centre frequency of each column, in Hz; it
        must include the seven centres of ``band``.
    :param band: The AM band number, 1 to 3 (13.6.2.1.1) or 4 to 6 (Annex
        G.3), as an integer; see :data:`AM_FREQUENCY_BANDS_HZ`.
    :param weighting: ``"A"`` when the band levels are already A-weighted,
        ``"Z"`` when the A-weighting is still to be applied. Required: a wrong
        guess is a 20 dB to 30 dB error at the lowest bands.
    :return: The band-limited ``LAeq,100ms`` series, in dB, one value per
        sample.
    :raises ValueError: If the band is not one of the band numbers (``1.5``
        and ``True`` are not), a band centre is missing or duplicated, the weighting is neither ``"A"`` nor ``"Z"``, or the
        levels are not finite.
    """
    if not is_class_designation(band, tuple(AM_FREQUENCY_BANDS_HZ)):
        msg = (
            f"'band' must be one of the band numbers {sorted(AM_FREQUENCY_BANDS_HZ)}; "
            f"got {band!r}."
        )
        raise ValueError(msg)
    if weighting not in ("A", "Z"):
        msg = f"'weighting' must be 'A' or 'Z'; got {weighting!r}."
        raise ValueError(msg)
    levels = require_finite_matrix(band_levels_db, "band_levels_db")
    freqs = require_finite_array(frequencies_hz, "frequencies_hz")
    if freqs.size != levels.shape[1]:
        msg = (
            f"'frequencies_hz' has {freqs.size} centres but 'band_levels_db' "
            f"has {levels.shape[1]} columns."
        )
        raise ValueError(msg)
    centres = AM_FREQUENCY_BANDS_HZ[int(band)]
    columns = [_nominal_index(freqs, centre) for centre in centres]
    selected = levels[:, columns]
    if weighting == "Z":
        selected = selected + np.array([_A_WEIGHTING_DB[c] for c in centres])
    return np.asarray(energy_sum(selected, axis=1), dtype=np.float64)


def _validated_range(modulation_frequency_range_hz: Sequence[float]) -> tuple[int, int]:
    """Line indices (0.1 Hz grid) bounding the user's fundamental range."""
    values = tuple(float(v) for v in modulation_frequency_range_hz)
    if len(values) != 2 or not all(math.isfinite(v) for v in values):  # noqa: PLR2004
        msg = "'modulation_frequency_range_hz' must be two finite frequencies."
        raise ValueError(msg)
    low, high = values
    limit_low, limit_high = AM_MODULATION_FREQUENCY_LIMITS_HZ
    resolution = 1.0 / (AM_BLOCK_SAMPLES * AM_SAMPLE_INTERVAL_S)
    if not limit_low - _GRID_TOLERANCE <= low < high <= limit_high + _GRID_TOLERANCE:
        msg = (
            "'modulation_frequency_range_hz' must satisfy "
            f"{limit_low:g} Hz <= low < high <= {limit_high:g} Hz (13.2); "
            f"got ({low:g}, {high:g})."
        )
        raise ValueError(msg)
    first = math.ceil(low / resolution - _GRID_TOLERANCE)
    last = math.floor(high / resolution + _GRID_TOLERANCE)
    if first > last:
        msg = (
            "'modulation_frequency_range_hz' holds no line of the 0.1 Hz "
            f"spectrum; got ({low:g}, {high:g})."
        )
        raise ValueError(msg)
    return first, last


def _settled_spectrum(
    spectrum: NDArray[np.float64], levels: NDArray[np.float64]
) -> NDArray[np.float64]:
    """``spectrum`` with every line at rounding set to zero.

    A steady block, or one that follows a cubic, leaves after the de-trending
    of 13.6.2.3 a) a residual of a few units in the last place of its levels,
    and in exact arithmetic that residual and every line of its spectrum are
    zero: the block has no local maximum and no modulation (13.6.2.3 d)).
    Read as they come out of the fit, the rounding lines have local maxima and
    prominences of their own, and the verdict would follow the last bits of
    the levels. A line no larger than :math:`(10^{-9} L)^2`, with :math:`L` the
    largest absolute level of the block, is therefore zero before the local
    maxima, the fundamental, the harmonics and the prominence are read. A line
    is at most the square of the largest de-trended value, so a block whose
    de-trended series stays within :math:`10^{-9} L` has no line left and is
    ``NO_PEAK``.

    :param spectrum: The power spectrum of Equation (12).
    :param levels: The block's levels, in dB.
    :return: A copy of the spectrum with the lines at rounding set to zero.
    """
    floor = (_ROUNDING_FRACTION * float(np.max(np.abs(levels)))) ** 2
    return np.where(spectrum > floor, spectrum, 0.0)


def _local_maxima(spectrum: NDArray[np.float64]) -> NDArray[np.bool_]:
    """Lines higher than both neighbours; the two end lines never are."""
    flags = np.zeros(spectrum.size, dtype=np.bool_)
    flags[1:-1] = (spectrum[1:-1] > spectrum[:-2]) & (spectrum[1:-1] > spectrum[2:])
    return flags


def _reconstruct(
    transform: NDArray[np.complex128], lines: Sequence[int]
) -> NDArray[np.float64]:
    """Inverse DFT of only ``lines`` (positive indices) and their mirrors."""
    kept = np.zeros_like(transform)
    size = transform.size
    for line in lines:
        kept[line] = transform[line]
        kept[size - line] = transform[size - line]
    return np.asarray(np.real(np.fft.ifft(kept)), dtype=np.float64)


def _window(line: int, last_line: int) -> tuple[int, ...]:
    """The three lines centred on ``line`` that lie inside 1..``last_line``."""
    return tuple(k for k in (line - 1, line, line + 1) if 1 <= k <= last_line)


def _swing(series: NDArray[np.float64]) -> float:
    """Peak-to-peak value of a series (footnote 5 of 13.6.2.3)."""
    return float(np.max(series) - np.min(series))


@dataclass(frozen=True)
class ModulationBlock(OwnsArrays):
    r"""The analysis of one 10 s block (IEC TS 61400-11-2:2024, 13.6.2.3).

    :ivar levels_db: The 100 band-limited ``LAeq,100ms`` values analysed, in dB.
    :ivar detrended_db: ``levels_db`` minus its cubic least-squares fit, in dB.
    :ivar frequencies_hz: The spectrum lines, 0.1 Hz to 4.9 Hz.
    :ivar power_spectrum: :math:`S_{xx}` of Equation (12) at those lines,
        from the positive frequencies (the half magnitude the TS allows).
    :ivar modulation_frequency_range_hz: The user's range of fundamental
        modulation frequencies, in Hz.
    :ivar fundamental_frequency_hz: The fundamental modulation frequency, the
        highest local maximum in the range, in Hz; ``None`` for ``NO_PEAK``.
    :ivar prominence: The prominence ratio :math:`p_\mathrm{AM}` of Equation
        (13); ``None`` for ``NO_PEAK``, infinite for a peak whose masking
        lines hold nothing above rounding.
    :ivar harmonic_frequencies_hz: The frequencies of the harmonics kept in
        the reconstruction, second before third; empty when none is.
    :ivar reconstructed_db: The reconstructed series, in dB about zero; empty
        for a prominence-failed block.
    :ivar modulation_depth_db: ``L5 - L95`` of the reconstructed series, in
        dB; ``None`` unless the block is valid.
    :ivar excluded: Whether the practitioner excluded the block by hand
        (13.6.2.2, third bullet).

    :attr:`status` is read from the prominence, the threshold of 4 of
    13.6.2.3 e) and the exclusion, so it is not a field.
    """

    levels_db: NDArray[np.float64]
    detrended_db: NDArray[np.float64]
    frequencies_hz: NDArray[np.float64]
    power_spectrum: NDArray[np.float64]
    modulation_frequency_range_hz: tuple[float, float]
    _: KW_ONLY
    fundamental_frequency_hz: float | None
    prominence: float | None
    harmonic_frequencies_hz: tuple[float, ...]
    reconstructed_db: NDArray[np.float64]
    modulation_depth_db: float | None
    excluded: bool = False

    def __post_init__(self) -> None:
        """Refuse a block whose analysis does not match the status it reads as.

        The status follows from the prominence, so what else the block holds
        has to agree with it: a peak and its prominence come together, and a
        modulation depth exists exactly when the block is valid.

        :raises ValueError: if the fundamental and the prominence are not
            given together, the prominence is negative or NaN, or the
            modulation depth is present on a block that is not valid or
            missing on one that is.
        """
        if (self.fundamental_frequency_hz is None) != (self.prominence is None):
            msg = (
                "ModulationBlock: a fundamental and its prominence come together "
                "(13.6.2.3 d) and e)); give both or neither."
            )
            raise ValueError(msg)
        require_scalar(self.prominence, "prominence")
        if self.prominence is not None and (
            math.isnan(self.prominence) or self.prominence < 0.0
        ):
            msg = "ModulationBlock: 'prominence' must be a non-negative ratio."
            raise ValueError(msg)
        if (self.modulation_depth_db is None) == self.valid:
            msg = (
                "ModulationBlock: a modulation depth is read from a valid block "
                f"and from no other; this block reads as {self.status.value!r}."
            )
            raise ValueError(msg)

    @property
    def status(self) -> ModulationBlockStatus:
        """:class:`ModulationBlockStatus` of the block (13.6.2.2 and 13.6.2.3).

        ``EXCLUDED`` when the practitioner excluded it, ``NO_PEAK`` without a
        local maximum in the range, ``LOW_PROMINENCE`` for a prominence under
        :data:`AM_PROMINENCE_THRESHOLD`, ``VALID`` otherwise.
        """
        if self.excluded:
            return ModulationBlockStatus.EXCLUDED
        if self.prominence is None:
            return ModulationBlockStatus.NO_PEAK
        if self.prominence < AM_PROMINENCE_THRESHOLD:
            return ModulationBlockStatus.LOW_PROMINENCE
        return ModulationBlockStatus.VALID

    @property
    def valid(self) -> bool:
        """Whether the block carries a modulation depth (13.6.2.2)."""
        return self.status is ModulationBlockStatus.VALID

    @property
    def included_frequencies_hz(self) -> tuple[float, ...]:
        """The spectrum lines transformed back, three about each component."""
        if not self.valid or self.fundamental_frequency_hz is None:
            return ()
        last = self.frequencies_hz.size
        lines: set[int] = set()
        for centre in (self.fundamental_frequency_hz, *self.harmonic_frequencies_hz):
            lines.update(_window(round(centre * _BLOCK_DURATION_S), last))
        return tuple(k / _BLOCK_DURATION_S for k in sorted(lines))

    def plot(
        self,
        ax: Axes | None = None,
        *,
        kind: Literal["spectrum", "series"] = "spectrum",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Plot the block's power spectrum (Figure 1) or its two time series.

        ``kind="spectrum"`` draws :math:`S_{xx}` with the range of fundamental
        frequencies, the lines kept in the reconstruction and the prominence,
        as Figure 1 of the TS does. ``kind="series"`` draws the de-trended
        series with the reconstructed one over it and the ``L5`` and ``L95``
        of the reconstruction.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param kind: ``"spectrum"`` (default) or ``"series"``.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the primary artist.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_modulation_block

        return plot_modulation_block(
            self, ax=ax, kind=kind, language=check_language(language), **kwargs
        )


def _prominence(spectrum: NDArray[np.float64], peak: int) -> float:
    """Equation (13): the peak line over the mean of its masking lines.

    ``spectrum`` is the settled one (:func:`_settled_spectrum`), so a masking
    level of zero means masking lines that hold nothing but rounding, and the
    prominence is then infinite however the rounding fell.
    """
    masking = [peak + k for k in _MASKING_OFFSETS if 0 <= peak + k < spectrum.size]
    masking_level = float(np.mean(spectrum[masking]))
    if masking_level <= 0.0:
        return math.inf
    return float(spectrum[peak] / masking_level)


def _harmonic_line(
    spectrum: NDArray[np.float64],
    maxima: NDArray[np.bool_],
    fundamental: int,
    order: int,
) -> int | None:
    """Line index (1-based) of harmonic ``order``, or ``None`` if none is found.

    The fundamental lies at 1.6 Hz at most, line 16 (13.2, enforced by
    :func:`_validated_range`), so three times it, line 48, is always inside
    the 49 lines of the spectrum.
    """
    target = order * fundamental
    last = spectrum.size
    if maxima[target - 1]:
        return target
    reach = _HARMONIC_SEARCH_LINES[order]
    candidates = [
        k
        for k in range(target - reach, target + reach + 1)
        if 1 <= k <= last and maxima[k - 1]
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda k: spectrum[k - 1])


def amplitude_modulation_block(
    levels_db: ArrayLike,
    *,
    modulation_frequency_range_hz: Sequence[float],
) -> ModulationBlock:
    r"""Analyse one 10 s block of 100 ms levels (IEC TS 61400-11-2, 13.6.2.3).

    Steps a) to f) of 13.6.2.3 and the reconstruction after them: cubic
    de-trending, a rectangular-window DFT of 0.1 Hz resolution, the power
    spectrum of Equation (12), the fundamental as the highest local maximum
    within ``modulation_frequency_range_hz``, its prominence (Equation (13))
    against the threshold of 4, the second and third harmonics under the two
    1.5 dB conditions, and the modulation depth ``L5 - L95`` of the series
    transformed back from three lines about each kept component.

    The local maxima, the fundamental, the harmonics and the prominence are
    read with the lines at rounding set to zero: a line no larger than
    :math:`(10^{-9} L)^2`, :math:`L` the largest absolute level of the block.
    A steady block, or one that follows a cubic, then has no local maximum
    and is ``NO_PEAK`` rather than a verdict drawn from the last bits of its
    levels, and a peak whose masking lines hold only rounding has an infinite
    prominence. :attr:`ModulationBlock.power_spectrum` keeps every line as
    Equation (12) gives it.

    :param levels_db: The 100 band-limited A-weighted ``Leq,100ms`` values of
        the block, in dB (see :func:`amplitude_modulation_band_levels`).
    :param modulation_frequency_range_hz: ``(low, high)`` range, in Hz, where
        the fundamental modulation frequency is expected: the blade passage
        frequencies of the turbines with some tolerance (13.6.2.1.2), within
        0.3 Hz to 1.6 Hz (13.2).
    :return: A :class:`ModulationBlock`.
    :raises ValueError: If the block does not hold 100 finite values or the
        range is outside 0.3 Hz to 1.6 Hz or holds no spectrum line.
    """
    first, last_in_range = _validated_range(modulation_frequency_range_hz)
    levels = require_finite_array(levels_db, "levels_db")
    if levels.size != AM_BLOCK_SAMPLES:
        msg = (
            f"'levels_db' must hold the {AM_BLOCK_SAMPLES} values of one 10 s "
            f"block of 100 ms levels; got {levels.size}."
        )
        raise ValueError(msg)
    time_s = np.arange(AM_BLOCK_SAMPLES) * AM_SAMPLE_INTERVAL_S
    fit = np.polynomial.polynomial.polyfit(time_s, levels, 3)
    detrended = levels - np.polynomial.polynomial.polyval(time_s, fit)
    transform = np.fft.fft(detrended)
    last_line = AM_BLOCK_SAMPLES // 2 - 1
    lines = np.arange(1, last_line + 1)
    spectrum = np.abs(transform[lines]) ** 2 / AM_BLOCK_SAMPLES**2
    frequencies = lines / _BLOCK_DURATION_S
    low, high = (float(v) for v in modulation_frequency_range_hz)
    common: dict[str, Any] = {
        "levels_db": levels,
        "detrended_db": read_only(detrended),
        "frequencies_hz": read_only(frequencies),
        "power_spectrum": read_only(spectrum),
        "modulation_frequency_range_hz": (low, high),
    }
    settled = _settled_spectrum(spectrum, levels)
    maxima = _local_maxima(settled)
    in_range = [k for k in range(first, last_in_range + 1) if maxima[k - 1]]
    if not in_range:
        return ModulationBlock(
            **common,
            fundamental_frequency_hz=None,
            prominence=None,
            harmonic_frequencies_hz=(),
            reconstructed_db=read_only(np.zeros(0)),
            modulation_depth_db=None,
        )
    fundamental = max(in_range, key=lambda k: settled[k - 1])
    prominence = _prominence(settled, fundamental - 1)
    if prominence < AM_PROMINENCE_THRESHOLD:
        return ModulationBlock(
            **common,
            fundamental_frequency_hz=fundamental / _BLOCK_DURATION_S,
            prominence=prominence,
            harmonic_frequencies_hz=(),
            reconstructed_db=read_only(np.zeros(0)),
            modulation_depth_db=None,
        )
    kept = set(_window(fundamental, last_line))
    harmonics: list[float] = []
    if _swing(_reconstruct(transform, sorted(kept))) > _HARMONIC_SWING_DB:
        for order in (2, 3):
            line = _harmonic_line(settled, maxima, fundamental, order)
            if line is None:
                continue
            window = _window(line, last_line)
            if _swing(_reconstruct(transform, window)) > _HARMONIC_SWING_DB:
                kept.update(window)
                harmonics.append(line / _BLOCK_DURATION_S)
    reconstructed = _reconstruct(transform, sorted(kept))
    depth = float(
        np.percentile(reconstructed, _UPPER_PERCENTILE)
        - np.percentile(reconstructed, _LOWER_PERCENTILE)
    )
    return ModulationBlock(
        **common,
        fundamental_frequency_hz=fundamental / _BLOCK_DURATION_S,
        prominence=prominence,
        harmonic_frequencies_hz=tuple(harmonics),
        reconstructed_db=read_only(reconstructed),
        modulation_depth_db=depth,
    )


@dataclass(frozen=True)
class ModulationPeriod(OwnsArrays):
    """The AM rating of one 10 min period (IEC TS 61400-11-2:2024, 13.6.3).

    Everything but the blocks is read from them, against the 30 valid blocks
    of 13.6.2.2 and the 90th percentile of 13.6.3, so a period cannot be
    built to rate blocks the TS does not count.

    :ivar blocks: The sixty :class:`ModulationBlock` analyses, in time order.
    """

    blocks: tuple[ModulationBlock, ...]

    @property
    def modulation_depths_db(self) -> NDArray[np.float64]:
        """The depth of each block, in dB; NaN where the block is not valid."""
        return np.array(
            [
                b.modulation_depth_db
                if b.valid and b.modulation_depth_db is not None
                else np.nan
                for b in self.blocks
            ],
            dtype=np.float64,
        )

    @property
    def fundamental_frequencies_hz(self) -> NDArray[np.float64]:
        """The fundamental of each valid block, in Hz; NaN elsewhere."""
        return np.array(
            [
                b.fundamental_frequency_hz
                if b.valid and b.fundamental_frequency_hz is not None
                else np.nan
                for b in self.blocks
            ],
            dtype=np.float64,
        )

    @property
    def valid_blocks(self) -> int:
        """Number of valid blocks, the ``n`` number of 13.6.2.2."""
        return int(np.count_nonzero(np.isfinite(self.modulation_depths_db)))

    @property
    def rated(self) -> bool:
        """Whether at least 30 blocks are valid (13.6.2.2)."""
        return self.valid_blocks >= AM_MINIMUM_VALID_BLOCKS

    @property
    def rating_db(self) -> float:
        """The AM rating of the period, in dB.

        The 90th percentile of the valid depths when :attr:`rated`, else
        0 dB (13.6.3).
        """
        if not self.rated:
            return 0.0
        depths = self.modulation_depths_db
        return float(np.percentile(depths[np.isfinite(depths)], _RATING_PERCENTILE))

    @property
    def mean_modulation_frequency_hz(self) -> float | None:
        """Mean fundamental of the valid blocks, in Hz; ``None`` when not :attr:`rated`."""
        if not self.rated:
            return None
        fundamentals = self._valid_fundamentals()
        lines = np.rint(fundamentals * _BLOCK_DURATION_S)
        return float(np.mean(lines)) / _BLOCK_DURATION_S

    @property
    def mode_modulation_frequency_hz(self) -> float | None:
        """Most frequent fundamental of the valid blocks, in Hz.

        The lowest of equally frequent ones; ``None`` when not :attr:`rated`.
        """
        if not self.rated:
            return None
        return _mode_frequency(self._valid_fundamentals())

    def _valid_fundamentals(self) -> NDArray[np.float64]:
        valid = np.isfinite(self.modulation_depths_db)
        return self.fundamental_frequencies_hz[valid]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the 10 s depths through the period and the 10 min rating.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the 10 s depths.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_modulation_period

        return plot_modulation_period(
            self, ax=ax, language=check_language(language), **kwargs
        )


def amplitude_modulation_period(
    levels_db: ArrayLike,
    *,
    modulation_frequency_range_hz: Sequence[float],
    excluded_blocks: ArrayLike | None = None,
) -> ModulationPeriod:
    """Rate one 10 min period of 100 ms levels (IEC TS 61400-11-2, 13.6.3).

    The 6 000 values are cut into sixty consecutive 10 s blocks, each analysed
    by :func:`amplitude_modulation_block`. With at least 30 valid blocks the
    rating is the 90th percentile of their depths and the mean and mode of
    their fundamentals are reported; otherwise the rating is 0 dB and no
    modulation frequency is given. That 0 dB period is kept, and counted in
    its bin by :func:`bin_amplitude_modulation`, as the TS says (13.6.3,
    13.6.4); the AMWG Final Report discards it instead.

    :param levels_db: The 6 000 band-limited ``LAeq,100ms`` values of the
        period, in dB, synchronised to the hour (13.6.3).
    :param modulation_frequency_range_hz: ``(low, high)`` range of the
        fundamental, in Hz, as for :func:`amplitude_modulation_block`.
    :param excluded_blocks: Optional sixty flags, ``True`` for a block the
        practitioner excludes by hand (13.6.2.2); those blocks are not
        analysed and do not count as valid. The TS notes that standard
        practice excludes whole 10 min periods, so excluding single blocks is
        an adaptation to be justified.
    :return: A :class:`ModulationPeriod`.
    :raises ValueError: If the period does not hold 6 000 finite values or the
        exclusion flags are not sixty booleans (or 0 and 1).
    """
    levels = require_finite_array(levels_db, "levels_db")
    samples = AM_BLOCK_SAMPLES * AM_PERIOD_BLOCKS
    if levels.size != samples:
        msg = (
            f"'levels_db' must hold the {samples} values of one 10 min period "
            f"of 100 ms levels; got {levels.size}."
        )
        raise ValueError(msg)
    if excluded_blocks is None:
        excluded = np.zeros(AM_PERIOD_BLOCKS, dtype=np.bool_)
    else:
        excluded = _exclusion_flags(excluded_blocks, "excluded_blocks")
        if excluded.size != AM_PERIOD_BLOCKS:
            msg = (
                f"'excluded_blocks' must flag each of the {AM_PERIOD_BLOCKS} "
                f"blocks; got {excluded.size}."
            )
            raise ValueError(msg)
    blocks: list[ModulationBlock] = []
    for index in range(AM_PERIOD_BLOCKS):
        block = amplitude_modulation_block(
            levels[index * AM_BLOCK_SAMPLES : (index + 1) * AM_BLOCK_SAMPLES],
            modulation_frequency_range_hz=modulation_frequency_range_hz,
        )
        if excluded[index]:
            block = _excluded(block)
        blocks.append(block)
    return ModulationPeriod(blocks=tuple(blocks))


def _exclusion_flags(flags: ArrayLike, name: str) -> NDArray[np.bool_]:
    """Exclusion flags as booleans, refusing what only converts to them.

    ``True``/``False`` (or the integers 1 and 0) are flags; a string such as
    ``"False"`` or ``"no"`` is truthy and a NaN converts to ``True``, so
    either would exclude a block or a period without a word.
    """
    array = np.asarray(flags)
    if array.dtype == np.bool_:
        return array.ravel()
    if array.dtype.kind in "iu":
        if np.all((array == 0) | (array == 1)):
            return array.astype(np.bool_).ravel()
        found = "an integer other than 0 and 1"
    else:
        found = f"values of type {array.dtype}"
    msg = f"'{name}' must hold booleans (True to exclude), or 0 and 1; got {found}."
    raise ValueError(msg)


def _excluded(block: ModulationBlock) -> ModulationBlock:
    """The same block, marked as excluded by the practitioner."""
    return ModulationBlock(
        levels_db=block.levels_db,
        detrended_db=block.detrended_db,
        frequencies_hz=block.frequencies_hz,
        power_spectrum=block.power_spectrum,
        modulation_frequency_range_hz=block.modulation_frequency_range_hz,
        fundamental_frequency_hz=block.fundamental_frequency_hz,
        prominence=block.prominence,
        harmonic_frequencies_hz=(),
        reconstructed_db=read_only(np.zeros(0)),
        modulation_depth_db=None,
        excluded=True,
    )


def _mode_frequency(fundamentals: NDArray[np.float64]) -> float:
    """Most frequent fundamental, the lowest of equally frequent ones."""
    lines = np.rint(fundamentals * _BLOCK_DURATION_S).astype(np.int64)
    values, counts = np.unique(lines, return_counts=True)
    return float(values[int(np.argmax(counts))] / _BLOCK_DURATION_S)


@dataclass(frozen=True)
class BinnedModulation(OwnsArrays):
    """AM ratings binned by wind speed and direction (IEC TS 61400-11-2, 13.6.4).

    One row per occupied bin, sorted by wind direction sector then wind
    speed; one column per band in ``bands``.

    :ivar bands: The AM bands analysed, in the column order of the arrays.
    :ivar wind_speeds_m_s: Centre of each bin's 1 m/s wind speed class.
    :ivar wind_directions_deg: Centre of each bin's direction sector, or
        ``None`` when the ratings were binned by wind speed alone.
    :ivar counts: Number of 10 min data points in each bin.
    :ivar nonzero_counts: Number of those with a non-zero rating, per band.
    :ivar mean_ratings_db: Mean 10 min rating per bin and band, the zeros of
        unrated periods included (13.6.4), in dB.
    :ivar type_a_uncertainty_db: Standard deviation of that mean, Equation
        (9) of 10.3.3 (13.6.5); NaN for a bin of one data point.
    :ivar exceedance_percent: Percentage of the bin's data points rated above
        3 dB, 6 dB and 9 dB (:data:`AM_EXCEEDANCE_THRESHOLDS_DB`), shape
        ``(bins, bands, 3)``.
    :ivar selected_bands: The band with the highest mean rating in each bin,
        the lowest-numbered of equally high ones.
    :ivar selected_ratings_db: The mean rating of that band, in dB.
    """

    bands: tuple[int, ...]
    wind_speeds_m_s: NDArray[np.float64]
    wind_directions_deg: NDArray[np.float64] | None
    counts: NDArray[np.int64]
    nonzero_counts: NDArray[np.int64]
    mean_ratings_db: NDArray[np.float64]
    type_a_uncertainty_db: NDArray[np.float64]
    exceedance_percent: NDArray[np.float64]
    _: KW_ONLY
    selected_bands: NDArray[np.int64]
    selected_ratings_db: NDArray[np.float64]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the worst-band mean rating of each bin against wind speed.

        One line per direction sector, in its own colour (or one line when
        binned by wind speed alone), each point labelled with the band that
        bin selected. The twelve 30° sectors of 13.7 take twelve colours;
        narrower sectors past the twelfth take them again, in the same order.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the lines.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.wind_turbine_receptor import plot_binned_modulation

        return plot_binned_modulation(
            self, ax=ax, language=check_language(language), **kwargs
        )


def bin_amplitude_modulation(
    ratings_db: ArrayLike,
    wind_speeds_m_s: ArrayLike,
    wind_directions_deg: ArrayLike | None = None,
    *,
    bands: Iterable[int] = (1, 2, 3),
    excluded: ArrayLike | None = None,
    sector_width_deg: float = 30.0,
) -> BinnedModulation:
    """Bin 10 min AM ratings and pick the worst band per bin (13.6.4).

    Each 10 min period is a data point of its rating in each band, aligned
    with the period's wind speed and direction. Wind speed bins are 1 m/s
    wide and centred on the integers (0.5 m/s to 1.5 m/s is bin 1);
    direction sectors are ``sector_width_deg`` wide and the first is centred
    on north (345 degrees to 15 degrees for 30 degree sectors). The mean
    rating of each bin includes the 0 dB of unrated periods; ``excluded``
    periods are left out altogether. Each bin reports the band with the
    highest mean.

    :param ratings_db: The 10 min ratings, in dB, one row per period and one
        column per band of ``bands`` (see :attr:`ModulationPeriod.rating_db`).
    :param wind_speeds_m_s: The reference wind speed of each period, in m/s.
    :param wind_directions_deg: The wind direction of each period, in degrees
        from north, or ``None`` to bin by wind speed alone.
    :param bands: The AM band numbers of the columns, as integers.
    :param excluded: Optional flags, ``True`` for a period the practitioner
        excluded; 13.6.4 leaves excluded periods out of the bin mean, whatever
        the reason. A period rated 0 dB for having fewer than 30 valid blocks
        is not excluded: it counts, at 0 dB, since 13.6.4 averages "including
        0 values" and 13.6.3 assigns that 0 to such a period (the "excluded
        periods due to pf" of 13.6.4 are read as periods excluded by hand).
    :param sector_width_deg: Width of the direction sectors, in degrees; it
        must divide 360. Wider sectors (downwind, crosswind) are reached by
        rotating the directions so that the sector of interest is centred on
        zero.
    :return: A :class:`BinnedModulation`.
    :raises ValueError: If the shapes disagree, a value is not finite, a
        wind speed is negative, a band is not a band number or is repeated,
        the exclusion flags are not booleans (or 0 and 1), or the sector
        width does not divide 360 degrees.
    """
    if isinstance(bands, str):
        msg = f"'bands' must be a sequence of band numbers; got {bands!r}."
        raise ValueError(msg)
    # Read once, so that an iterator is validated and converted from the same
    # values rather than consumed by the check.
    band_values = tuple(bands)
    unknown = [
        b
        for b in band_values
        if not is_class_designation(b, tuple(AM_FREQUENCY_BANDS_HZ))
    ]
    if unknown:
        msg = (
            f"'bands' holds {unknown!r}, which are not band numbers "
            f"{sorted(AM_FREQUENCY_BANDS_HZ)}; see AM_FREQUENCY_BANDS_HZ."
        )
        raise ValueError(msg)
    band_tuple = tuple(int(b) for b in band_values)
    if not band_tuple or len(set(band_tuple)) != len(band_tuple):
        msg = "'bands' must name at least one band, each once."
        raise ValueError(msg)
    ratings = require_finite_matrix(ratings_db, "ratings_db")
    if ratings.shape[1] != len(band_tuple):
        msg = (
            f"'ratings_db' must hold one row per period and one column per "
            f"band; it has {ratings.shape[1]} columns for {len(band_tuple)} bands."
        )
        raise ValueError(msg)
    if np.any(ratings < 0.0):
        msg = "'ratings_db' must not be negative: a depth is L5 - L95."
        raise ValueError(msg)
    periods = ratings.shape[0]
    bins = _bin_keys(
        wind_speeds_m_s,
        wind_directions_deg,
        count=periods,
        bin_width_m_s=1.0,
        sector_width_deg=sector_width_deg,
    )
    if excluded is None:
        keep = np.ones(periods, dtype=np.bool_)
    else:
        keep = ~_exclusion_flags(excluded, "excluded")
        if keep.size != periods:
            msg = f"'excluded' must flag each of the {periods} periods."
            raise ValueError(msg)
    occupied = sorted({key for key, kept in zip(bins.keys, keep, strict=True) if kept})
    if not occupied:
        msg = "Every period is excluded; there is nothing to bin."
        raise ValueError(msg)
    n_bins, n_bands = len(occupied), len(band_tuple)
    counts = np.zeros(n_bins, dtype=np.int64)
    nonzero = np.zeros((n_bins, n_bands), dtype=np.int64)
    means = np.zeros((n_bins, n_bands))
    type_a = np.zeros((n_bins, n_bands))
    exceed = np.zeros((n_bins, n_bands, len(AM_EXCEEDANCE_THRESHOLDS_DB)))
    for row, key in enumerate(occupied):
        values = ratings[bins.members(key) & keep]
        counts[row] = values.shape[0]
        nonzero[row] = np.count_nonzero(values > 0.0, axis=0)
        means[row] = np.mean(values, axis=0)
        type_a[row] = [_type_a_arithmetic(values[:, j]) for j in range(n_bands)]
        for t, threshold in enumerate(AM_EXCEEDANCE_THRESHOLDS_DB):
            exceed[row, :, t] = 100.0 * np.mean(values > threshold, axis=0)
    best = np.argmax(means, axis=1)
    centres = [bins.centres(key) for key in occupied]
    return BinnedModulation(
        bands=band_tuple,
        wind_speeds_m_s=np.array([c[1] for c in centres]),
        wind_directions_deg=(
            np.array([c[0] for c in centres]) if bins.by_direction else None
        ),
        counts=read_only(counts),
        nonzero_counts=read_only(nonzero),
        mean_ratings_db=read_only(means),
        type_a_uncertainty_db=read_only(type_a),
        exceedance_percent=read_only(exceed),
        selected_bands=np.array([band_tuple[j] for j in best], dtype=np.int64),
        selected_ratings_db=read_only(means[np.arange(n_bins), best]),
    )
