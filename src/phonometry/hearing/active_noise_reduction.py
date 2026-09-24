#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Total attenuation of an active noise reduction earmuff (ISO 4869-6:2019).

An active noise reduction (ANR) earmuff adds a cancellation circuit to a
passive one, and the circuit works mostly at low frequencies, where the
passive shell is weakest. ISO 4869-1 cannot measure it: a threshold test runs
at levels far below those at which the circuit has anything to cancel. So
ISO 4869-6 measures the two halves separately and adds them subject by
subject:

- the **passive** attenuation, the real-ear attenuation at threshold of
  ISO 4869-1 with the circuit off, in octave bands
  (:func:`~phonometry.hearing.real_ear_attenuation`);
- the **active insertion loss** (3.4), measured with a microphone in each
  closed ear canal (MIRE, ISO 11904-1) as the difference between the level at
  the ear in the passive and in the active mode, in one-third-octave bands of a
  broadband noise at 85 dB to 95 dB (5.4.3):

  .. math::

     \alpha_{j,e,f} = L_{\mathrm{passive},j,e,f} - L_{\mathrm{active},j,e,f}

**The chain of 5.5.** For each subject:

a) the passive attenuation is interpolated linearly into the one-third-octave
   bands between 63 Hz (or 125 Hz) and 8 kHz, and extrapolated to 50 Hz (or
   100 Hz) and 10 kHz;
b) in each one-third-octave band, only the ear with the **lower** active
   insertion loss is kept;
c) the two are added, :math:`A_{\mathrm{total},f,j}`;
d) each octave band is the energetic average of its three one-third-octave
   bands (Formula (1)):

   .. math::

      A_{\mathrm{total,oct},j} = -10 \lg \left[\left(
      10^{-0,1 A_{\mathrm{total},f_1,j}} + 10^{-0,1 A_{\mathrm{total},f_2,j}}
      + 10^{-0,1 A_{\mathrm{total},f_3,j}}\right) / 3\right] \mathrm{dB} \tag{1}

e) the sixteen octave-band data sets go into ISO 4869-2 at a protection
   performance of 84 %: the mean, the standard deviation, the APV, the H, M
   and L values and the SNR.

:func:`anr_total_attenuation` runs the whole chain. Clause 5.5 says the
detailed computations are given in the calculation example ISO publishes with
the standard, and that workbook interpolates **linearly in frequency, in
hertz**, between the nominal centre frequencies, not on a logarithmic axis:
80 Hz sits 27 % of the way from 63 Hz to 125 Hz, not a third of it. This
follows the workbook. The workbook also rounds each interpolated value and
each octave result to 0,1 dB, and the mean and standard deviation before it
forms the APV; this computes at full precision throughout, which moves an
octave-band total by less than 0,1 dB.

**The uncertainty (Annex A).** Formula (A.1) is the model of ISO 4869-1
applied to the active insertion loss, and within one laboratory the combined
standard uncertainty is again the standard deviation of the mean over the
sixteen lower-ear values, :math:`u = s/\sqrt{N}` and :math:`U_{95} = 2u`, which
:func:`active_insertion_loss` returns. Table A.2 prints a typical budget,
:data:`ANR_WITHIN_LABORATORY_UNCERTAINTY`.

**Linear operation (5.4.4).** A cancellation circuit saturates, so the active
insertion loss only holds up to some external level. With red noise, the level
at each ear in the 125 Hz octave band is followed while the external level
rises in 5 dB steps from the level of the insertion-loss measurement to at
most 110 dB, and each step at the ear shall also be 5 dB, within ±1 dB.
:func:`assess_anr_linearity` finds the highest external level up to which that
holds for every sample, subject and ear, which is what 5.6 i) reports.

Clause, formula and table numbers refer to ISO 4869-6:2019(E).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .hearing_protectors import (
    AssumedProtectionResult,
    HMLRatingResult,
    SNRRatingResult,
    assumed_protection_value,
    hml_rating,
    snr_rating,
)
from .real_ear_attenuation import ProtectorUncertaintyBudget, RealEarAttenuationResult

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "ANR_WITHIN_LABORATORY_UNCERTAINTY",
    "ActiveInsertionLossResult",
    "AnrLinearityResult",
    "AnrTotalAttenuationResult",
    "active_insertion_loss",
    "anr_total_attenuation",
    "assess_anr_linearity",
]

#: Table A.2: the typical budget of the mean active insertion loss of an ANR
#: earmuff within one laboratory, for the sixteen lower-ear values of 5.5 b):
#: 0,6 dB for the method, 0,3 dB for the signal generation and MIRE
#: acquisition, 0,4 dB for the environment. Its combined and expanded values,
#: 0,78 dB and 1,6 dB in the table, are derived from these.
ANR_WITHIN_LABORATORY_UNCERTAINTY = ProtectorUncertaintyBudget(0.6, 0.3, 0.4)

#: The nominal one-third-octave centre frequencies of 5.3.1, 50 Hz to 10 kHz,
#: in hertz. The calculation example interpolates between them as written.
_THIRD_OCTAVE_BANDS_HZ: tuple[float, ...] = (
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
)

#: The octave bands of the total attenuation, 63 Hz to 8 kHz, in hertz; each
#: is the middle one of three consecutive one-third-octave bands above.
_OCTAVE_BANDS_HZ: tuple[float, ...] = _THIRD_OCTAVE_BANDS_HZ[1::3]

#: One-third-octave bands per octave, Formula (1).
_THIRDS_PER_OCTAVE = 3

#: 5.4.1: each subject is measured on both ears.
_EARS = 2

#: The shape of a per-ear grid, ``(subjects, ears, bands)``, and of a grid
#: that already holds one value per subject and band.
_PER_EAR_RANK = 3
_GRID_RANK = 2
_MINIMUM_SUBJECTS = 2

#: The coverage factor of Annex A.
_COVERAGE_FACTOR = 2.0

#: 5.5 e): the protection performance of the ISO 4869-2 ratings.
_PERFORMANCE = 84

#: 5.4.4: the step of the external level, the tolerance on the step at the
#: ear, and the highest external A-weighted level to be applied, all in dB.
_LINEARITY_STEP_DB = 5.0
_LINEARITY_TOLERANCE_DB = 1.0
_MAXIMUM_EXTERNAL_LEVEL_DB = 110.0
#: A step is taken as the 5 dB of 5.4.4 when it is within this much of it:
#: the levels are reported to a tenth of a decibel.
_STEP_READING_DB = 0.05

#: 5.4.4: the 125 Hz octave band at the ear, from the 100, 125 and 160 Hz
#: one-third-octave bands.
_LINEARITY_THIRDS = 3


def _default_bands(count: int, owner: str) -> np.ndarray:
    """The band axis of an insertion-loss grid, by how many bands it has.

    :param count: The number of bands.
    :param owner: The function name, for the error message.
    :return: The centre frequencies in hertz.
    :raises ValueError: for a count no default fits.
    """
    thirds = np.asarray(_THIRD_OCTAVE_BANDS_HZ, dtype=np.float64)
    octaves = np.asarray(_OCTAVE_BANDS_HZ, dtype=np.float64)
    defaults = {
        thirds.size: thirds,
        thirds.size - 3: thirds[3:],
        octaves.size: octaves,
        octaves.size - 1: octaves[1:],
    }
    if count in defaults:
        return np.array(defaults[count], dtype=np.float64)
    msg = (
        f"{owner}: pass 'frequencies' explicitly for {count} bands; only the "
        "one-third-octave bands of 5.3.1 (50 Hz or 100 Hz to 10 kHz) and the "
        "octave bands 63 Hz or 125 Hz to 8 kHz are assumed."
    )
    raise ValueError(msg)


@dataclass(frozen=True)
class ActiveInsertionLossResult:
    r"""The active insertion loss of an ANR earmuff on a panel of subjects.

    :ivar insertion_loss_db: :math:`\alpha` per subject and band, the ear with
        the lower value in each band (5.5 b)), in dB.
    :ivar per_ear_db: The value of each ear, a ``(subjects, 2, bands)`` grid
        with the left ear first, in dB, or ``None`` when only the lower-ear
        values were given.
    :ivar mean_db: The mean over the subjects per band, in dB.
    :ivar standard_deviation_db: The sample standard deviation per band, in dB.
    :ivar standard_uncertainty_db: :math:`u = s/\sqrt{N}` (A.2), in dB.
    :ivar expanded_uncertainty_db: :math:`U_{95} = 2u` (A.1), in dB.
    :ivar frequencies: The centre frequencies of the bands, in hertz.
    :ivar subjects: The number of test subjects :math:`N`.
    """

    insertion_loss_db: np.ndarray
    per_ear_db: np.ndarray | None
    mean_db: np.ndarray
    standard_deviation_db: np.ndarray
    standard_uncertainty_db: np.ndarray
    expanded_uncertainty_db: np.ndarray
    frequencies: np.ndarray
    subjects: int

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the mean active insertion loss with its expanded uncertainty.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the mean curve.
        :return: The axes.
        """
        from .._plot.hearing import plot_active_insertion_loss

        return plot_active_insertion_loss(self, ax=ax, language=language, **kwargs)


def _levels(values: ArrayLike, name: str) -> np.ndarray:
    """A ``(subjects, ears, bands)`` grid of finite MIRE levels in dB.

    :param values: The levels.
    :param name: The argument name, for the error message.
    :return: The grid as a float array of its own, never the caller's.
    :raises ValueError: for a shape other than two ears per subject, fewer
        than two subjects, or a value that is not finite.
    """
    grid = np.array(values, dtype=np.float64)
    if grid.ndim != _PER_EAR_RANK or grid.shape[1] != _EARS:
        msg = (
            f"'{name}' must be a (subjects, 2, bands) grid: 5.4.1 measures "
            "both ears of every subject."
        )
        raise ValueError(msg)
    if grid.shape[0] < _MINIMUM_SUBJECTS or grid.shape[2] == 0:
        msg = (
            f"'{name}' needs at least two subjects and one band; 5.4.1 asks "
            "for sixteen subjects."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(grid)):
        msg = f"'{name}' must contain only finite values, in dB."
        raise ValueError(msg)
    return grid


def _lower_ear_from_insertion_loss(
    insertion_loss_db: ArrayLike,
) -> tuple[np.ndarray | None, np.ndarray]:
    """The per-ear grid, if one was given, and the lower ear of each subject."""
    grid = np.asarray(insertion_loss_db, dtype=np.float64)
    if grid.ndim == _PER_EAR_RANK:
        per_ear = _levels(grid, "insertion_loss_db")
        return per_ear, per_ear.min(axis=1)
    if grid.ndim != _GRID_RANK:
        msg = (
            "'insertion_loss_db' must be a (subjects, 2, bands) grid per "
            "ear or a (subjects, bands) grid of the lower ear."
        )
        raise ValueError(msg)
    if grid.shape[0] < _MINIMUM_SUBJECTS or grid.shape[1] == 0:
        msg = (
            "'insertion_loss_db' needs at least two subjects and one "
            "band; 5.4.1 asks for sixteen subjects."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(grid)):
        msg = "'insertion_loss_db' must contain only finite values, in dB."
        raise ValueError(msg)
    return None, np.array(grid, dtype=np.float64)


def _insertion_loss_from_levels(
    passive_levels_db: ArrayLike, active_levels_db: ArrayLike
) -> np.ndarray:
    """The insertion loss of each ear, passive minus active level (5.4.1)."""
    passive = _levels(passive_levels_db, "passive_levels_db")
    active = _levels(active_levels_db, "active_levels_db")
    if passive.shape != active.shape:
        msg = (
            "'passive_levels_db' and 'active_levels_db' must cover the same "
            f"subjects, ears and bands; got {passive.shape} and {active.shape}."
        )
        raise ValueError(msg)
    return np.asarray(passive - active, dtype=np.float64)


def _band_frequencies(frequencies: ArrayLike | None, count: int) -> np.ndarray:
    """The centre frequencies given, or the default grid for *count* bands."""
    if frequencies is None:
        return _default_bands(count, "active_insertion_loss")
    freqs = np.asarray(frequencies, dtype=np.float64)
    if freqs.ndim != 1 or freqs.size != count or not np.all(np.isfinite(freqs)):
        msg = (
            "active_insertion_loss: 'frequencies' must be one centre "
            f"frequency per band; got {freqs.size} for {count} bands."
        )
        raise ValueError(msg)
    return freqs


def active_insertion_loss(
    insertion_loss_db: ArrayLike | None = None,
    *,
    passive_levels_db: ArrayLike | None = None,
    active_levels_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> ActiveInsertionLossResult:
    r"""The active insertion loss, its lower ear and its uncertainty (5.4, 5.5 b), A.2).

    Give the levels at the ears in the two modes, both ``(subjects, 2,
    bands)`` grids with the left ear first, and the insertion loss of each ear
    is their difference (5.4.1):

    .. math::

       \alpha_{j,e,f} = L_{\mathrm{passive},j,e,f} - L_{\mathrm{active},j,e,f}

    or give the insertion loss directly, per ear on the same grid or already
    reduced to one value per subject and band. Per subject and band only the
    ear with the lower value is kept (5.5 b)), and over those the mean, the
    standard deviation and the uncertainty of the mean of Annex A are formed:

    .. math::

       u = \frac{s}{\sqrt{N}}, \qquad U_{95} = 2u

    A negative value is a band in which the circuit adds sound, which ANR
    earmuffs commonly do above 1 kHz; it is kept as it is.

    :param insertion_loss_db: The active insertion loss in dB, a
        ``(subjects, 2, bands)`` grid per ear or a ``(subjects, bands)`` grid
        of the lower ear.
    :param passive_levels_db: The MIRE levels in the passive mode, a
        ``(subjects, 2, bands)`` grid in dB, given together with
        ``active_levels_db`` instead of ``insertion_loss_db``.
    :param active_levels_db: The MIRE levels in the active mode, on the same
        grid.
    :param frequencies: The centre frequencies in hertz, or ``None`` for the
        one-third-octave bands 50 Hz to 10 kHz (24 bands) or 100 Hz to 10 kHz
        (21), or the octave bands 63 Hz to 8 kHz (8) or 125 Hz to 8 kHz (7),
        by the number of bands.
    :return: :class:`ActiveInsertionLossResult`.
    :raises ValueError: if neither form or both are given, if a grid has the
        wrong shape, fewer than two subjects or a value that is not finite, if
        the two level grids differ in shape, or if ``frequencies`` does not
        match.
    """
    levels_given = passive_levels_db is not None or active_levels_db is not None
    per_ear: np.ndarray | None
    if insertion_loss_db is not None and not levels_given:
        per_ear, lower = _lower_ear_from_insertion_loss(insertion_loss_db)
    elif (
        insertion_loss_db is None
        and passive_levels_db is not None
        and active_levels_db is not None
    ):
        per_ear = _insertion_loss_from_levels(passive_levels_db, active_levels_db)
        lower = per_ear.min(axis=1)
    else:
        msg = (
            "give either 'insertion_loss_db', or both 'passive_levels_db' and "
            "'active_levels_db' (5.4.1), and not both forms."
        )
        raise ValueError(msg)
    freqs = _band_frequencies(frequencies, lower.shape[1])
    subjects = int(lower.shape[0])
    mean = np.asarray(lower.mean(axis=0), dtype=np.float64)
    spread = np.asarray(lower.std(axis=0, ddof=1), dtype=np.float64)
    standard = spread / math.sqrt(subjects)
    return ActiveInsertionLossResult(
        insertion_loss_db=lower,
        per_ear_db=per_ear,
        mean_db=mean,
        standard_deviation_db=spread,
        standard_uncertainty_db=standard,
        expanded_uncertainty_db=_COVERAGE_FACTOR * standard,
        frequencies=np.array(freqs, dtype=np.float64),
        subjects=subjects,
    )


@dataclass(frozen=True)
class AnrTotalAttenuationResult:
    r"""The total attenuation of an ANR earmuff and its ISO 4869-2 ratings (5.5).

    :ivar total_octave_db: :math:`A_{\mathrm{total,oct},j}` per subject and
        octave band, Formula (1), in dB. This is the grid of 5.5 e).
    :ivar total_third_octave_db: :math:`A_{\mathrm{total},f,j}` per subject
        and one-third-octave band, 5.5 c), in dB.
    :ivar reat_third_octave_db: The passive attenuation interpolated and
        extrapolated into the one-third-octave bands, 5.5 a), in dB.
    :ivar insertion_loss_db: The lower-ear active insertion loss in the same
        bands, 5.5 b), in dB.
    :ivar frequencies: The octave bands, in hertz.
    :ivar third_octave_frequencies: The one-third-octave bands, in hertz.
    :ivar assumed_protection: Mean, standard deviation and APV at 84 %.
    :ivar hml: The H, M and L values at 84 %.
    :ivar snr: The SNR at 84 %.
    """

    total_octave_db: np.ndarray
    total_third_octave_db: np.ndarray
    reat_third_octave_db: np.ndarray
    insertion_loss_db: np.ndarray
    frequencies: np.ndarray
    third_octave_frequencies: np.ndarray
    assumed_protection: AssumedProtectionResult
    hml: HMLRatingResult
    snr: SNRRatingResult

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the passive, active and total attenuation and the APV.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the mean total attenuation curve.
        :return: The axes.
        """
        from .._plot.hearing import plot_anr_total_attenuation

        return plot_anr_total_attenuation(self, ax=ax, language=language, **kwargs)


def _passive_octaves(
    reat: ArrayLike | RealEarAttenuationResult,
) -> tuple[np.ndarray, np.ndarray]:
    """The passive attenuation grid and its octave bands.

    :param reat: A result of :func:`real_ear_attenuation`, or its grid.
    :return: The ``(subjects, octaves)`` grid and the octave frequencies.
    :raises ValueError: for a grid that is not on the octave bands 63 Hz or
        125 Hz to 8 kHz.
    """
    octaves = np.asarray(_OCTAVE_BANDS_HZ, dtype=np.float64)
    if isinstance(reat, RealEarAttenuationResult):
        grid = np.asarray(reat.attenuation_db, dtype=np.float64)
        freqs = np.asarray(reat.frequencies, dtype=np.float64)
    else:
        grid = np.asarray(reat, dtype=np.float64)
        if grid.ndim != _GRID_RANK:
            msg = (
                "'reat' must be a (subjects, octave bands) grid of attenuations in dB."
            )
            raise ValueError(msg)
        freqs = (
            octaves[octaves.size - grid.shape[1] :]
            if grid.shape[1] <= octaves.size
            else octaves
        )
    for start in (0, 1):
        expected = octaves[start:]
        if freqs.size == expected.size and np.allclose(freqs, expected):
            if grid.shape[0] < _MINIMUM_SUBJECTS or not np.all(np.isfinite(grid)):
                msg = "'reat' needs at least two subjects and only finite values."
                raise ValueError(msg)
            return grid, expected
    msg = (
        "'reat' must be on the octave bands 63 Hz or 125 Hz to 8 kHz of "
        f"ISO 4869-1; got {freqs.tolist()}."
    )
    raise ValueError(msg)


def _interpolate_passive(
    grid: np.ndarray, octaves: np.ndarray, thirds: np.ndarray
) -> np.ndarray:
    """5.5 a): linear in frequency between the octaves, the ends extended.

    Linear in hertz, between the nominal centre frequencies, as ISO's
    calculation example does it; the bands below the lowest octave and above
    the highest continue the straight line of the first and the last segment.

    :param grid: The ``(subjects, octaves)`` passive attenuation, in dB.
    :param octaves: Its octave centre frequencies, in hertz.
    :param thirds: The one-third-octave bands to fill, in hertz.
    :return: The ``(subjects, thirds)`` passive attenuation, in dB.
    """
    below = thirds < octaves[0]
    above = thirds > octaves[-1]
    out = np.empty((grid.shape[0], thirds.size), dtype=np.float64)
    for row, values in enumerate(grid):
        out[row] = np.interp(thirds, octaves, values)
        low_slope = (values[1] - values[0]) / (octaves[1] - octaves[0])
        high_slope = (values[-1] - values[-2]) / (octaves[-1] - octaves[-2])
        out[row, below] = values[0] + low_slope * (thirds[below] - octaves[0])
        out[row, above] = values[-1] + high_slope * (thirds[above] - octaves[-1])
    return out


def _lower_ear_thirds(
    insertion_loss: ArrayLike | ActiveInsertionLossResult, thirds: np.ndarray
) -> np.ndarray:
    """The lower-ear active insertion loss on the bands the chain needs.

    :param insertion_loss: A result of :func:`active_insertion_loss`, or its
        grid per ear or of the lower ear, on the one-third-octave bands of
        5.3.1.
    :param thirds: The one-third-octave bands the passive side reaches.
    :return: The ``(subjects, thirds)`` lower-ear insertion loss, in dB.
    :raises ValueError: if the insertion loss does not cover those bands.
    """
    result = (
        insertion_loss
        if isinstance(insertion_loss, ActiveInsertionLossResult)
        else active_insertion_loss(insertion_loss)
    )
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    columns = []
    for band in thirds:
        matches = np.flatnonzero(np.isclose(freqs, band, rtol=1e-3))
        if matches.size != 1:
            msg = (
                "the active insertion loss must cover every one-third-octave "
                f"band from {thirds[0]:g} Hz to {thirds[-1]:g} Hz; {band:g} Hz "
                "is missing."
            )
            raise ValueError(msg)
        columns.append(int(matches[0]))
    return np.asarray(result.insertion_loss_db, dtype=np.float64)[:, columns]


def anr_total_attenuation(
    reat: ArrayLike | RealEarAttenuationResult,
    insertion_loss: ArrayLike | ActiveInsertionLossResult,
) -> AnrTotalAttenuationResult:
    r"""The total attenuation of an ANR earmuff, subject by subject (5.5).

    Runs 5.5 a) to e): the passive attenuation of ISO 4869-1 is interpolated
    into one-third-octave bands, linearly in hertz and extended at both ends;
    the lower-ear active insertion loss is added to it; each octave band is
    the energetic average of its three one-third-octave bands,

    .. math::

       A_{\mathrm{total,oct},j} = -10 \lg \left[\left(
       \sum_{i=1}^{3} 10^{-0,1 A_{\mathrm{total},f_i,j}}\right) / 3\right]
       \mathrm{dB} \tag{1}

    and the octave-band totals of all subjects go into ISO 4869-2 at 84 %. The
    same subjects are measured passively and actively (5.4.3), so the two
    inputs must have the same subjects, in the same order.

    The passive attenuation from 63 Hz needs the active insertion loss from
    50 Hz; from 125 Hz, it needs it from 100 Hz. An insertion loss that starts
    at 100 Hz can only give the total from 125 Hz (5.3.1); a passive
    attenuation from 63 Hz then still places the 100 Hz band, by interpolation.

    :param reat: The passive attenuation, a
        :class:`~phonometry.hearing.RealEarAttenuationResult` or its
        ``(subjects, octaves)`` grid in dB on the octave bands 63 Hz or 125 Hz
        to 8 kHz.
    :param insertion_loss: The active insertion loss, an
        :class:`ActiveInsertionLossResult` or a grid
        :func:`active_insertion_loss` accepts, on the one-third-octave bands of
        5.3.1.
    :return: :class:`AnrTotalAttenuationResult`.
    :raises ValueError: if the passive attenuation is not on the octave bands
        of ISO 4869-1, if the insertion loss does not reach the bands it needs,
        or if the two do not have the same number of subjects.
    """
    passive, octaves = _passive_octaves(reat)
    result = (
        insertion_loss
        if isinstance(insertion_loss, ActiveInsertionLossResult)
        else active_insertion_loss(insertion_loss)
    )
    thirds_all = np.asarray(_THIRD_OCTAVE_BANDS_HZ, dtype=np.float64)
    start = _THIRD_OCTAVE_BANDS_HZ.index(float(octaves[0])) - 1
    interpolated = _interpolate_passive(passive, octaves, thirds_all[start:])
    kept = octaves
    lowest_active = float(np.min(result.frequencies))
    if octaves[0] < _OCTAVE_BANDS_HZ[1] and lowest_active > thirds_all[0] * 1.01:
        # 5.3.1: without the bands below 100 Hz the total starts at 125 Hz.
        # The 63 Hz passive value still places the 100 Hz one, between two
        # measured octaves rather than beyond the last of them.
        kept = octaves[1:]
        interpolated = interpolated[:, _THIRDS_PER_OCTAVE:]
    thirds = thirds_all[_THIRD_OCTAVE_BANDS_HZ.index(float(kept[0])) - 1 :]
    active = _lower_ear_thirds(result, thirds)
    if active.shape[0] != passive.shape[0]:
        msg = (
            "the passive attenuation and the active insertion loss must come "
            f"from the same subjects (5.4.3); got {passive.shape[0]} and "
            f"{active.shape[0]}."
        )
        raise ValueError(msg)
    total_thirds = interpolated + active
    grouped = total_thirds.reshape(total_thirds.shape[0], kept.size, _THIRDS_PER_OCTAVE)
    total_octaves = -10.0 * np.log10(np.mean(10.0 ** (-0.1 * grouped), axis=2))
    return AnrTotalAttenuationResult(
        total_octave_db=total_octaves,
        total_third_octave_db=total_thirds,
        reat_third_octave_db=interpolated,
        insertion_loss_db=active,
        frequencies=np.array(kept, dtype=np.float64),
        third_octave_frequencies=np.array(thirds, dtype=np.float64),
        assumed_protection=assumed_protection_value(
            total_octaves, performance=_PERFORMANCE, frequencies=kept
        ),
        hml=hml_rating(total_octaves, performance=_PERFORMANCE),
        snr=snr_rating(total_octaves, performance=_PERFORMANCE),
    )


@dataclass(frozen=True)
class AnrLinearityResult:
    r"""How far up an ANR earmuff stays linear (5.4.4).

    :ivar external_levels_db: The external A-weighted levels applied, in dB,
        in 5 dB steps.
    :ivar ear_levels_db: The 125 Hz octave-band level at the ear, one row per
        sample, subject and ear, one column per external level, in dB.
    :ivar increments_db: The step at the ear for each step outside, in dB.
    """

    external_levels_db: np.ndarray
    ear_levels_db: np.ndarray
    increments_db: np.ndarray

    @property
    def linear(self) -> np.ndarray:
        """Per ear and step, whether the step at the ear is 5 dB ± 1 dB.

        :return: A ``(ears, steps)`` boolean grid.
        """
        external = np.diff(self.external_levels_db)
        deviation = np.abs(self.increments_db - external[None, :])
        return np.asarray(deviation <= _LINEARITY_TOLERANCE_DB, dtype=bool)

    @property
    def maximum_linear_level_db(self) -> float:
        """The highest external level up to which every ear stayed linear, in dB.

        Read from :attr:`linear`, the same judgement :attr:`passes` makes: the
        level before the first step at which any ear leaves 5 dB ± 1 dB, or
        the last level applied when none does. The lowest level applied when
        the first step already fails.

        :return: The level 5.6 i) reports, in dB.
        """
        step_ok = np.all(self.linear, axis=0)
        failing = np.flatnonzero(~step_ok)
        last = int(failing[0]) if failing.size else self.external_levels_db.size - 1
        return float(self.external_levels_db[last])

    @property
    def passes(self) -> bool:
        """Whether every step at every ear stayed linear.

        :return: ``True`` when the earmuff is linear over the whole range
            tested.
        """
        return bool(np.all(self.linear))

    @property
    def linear_to_110_db(self) -> bool:
        """Whether it stayed linear up to 110 dB, which 5.6 i) then states.

        :return: ``True`` when every step is linear and the last external
            level is 110 dB.
        """
        top = float(self.external_levels_db[-1])
        return self.passes and abs(top - _MAXIMUM_EXTERNAL_LEVEL_DB) <= _STEP_READING_DB

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`, and the
            rating is :attr:`maximum_linear_level_db`.
        """
        msg = (
            "an AnrLinearityResult has no truth value; read '.passes' or "
            "'.maximum_linear_level_db'"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw every step at the ear against the 5 dB ± 1 dB it should be.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the median step curve.
        :return: The axes.
        """
        from .._plot.hearing import plot_anr_linearity

        return plot_anr_linearity(self, ax=ax, language=language, **kwargs)


def assess_anr_linearity(
    external_levels_db: ArrayLike,
    ear_levels_db: ArrayLike | None = None,
    *,
    ear_third_octave_levels_db: ArrayLike | None = None,
) -> AnrLinearityResult:
    r"""Up to what external level does the earmuff stay linear? (5.4.4).

    With red noise (5.3.2) and the circuit on, the external A-weighted level
    starts at the level of the insertion-loss measurement and rises in 5 dB
    steps to at most 110 dB. At each ear the level in the 125 Hz octave band,
    the energy sum of the 100 Hz, 125 Hz and 160 Hz one-third-octave bands,
    shall rise by the same 5 dB, within ±1 dB. The highest external level up
    to which that holds for every sample and subject is what 5.6 i) reports,
    and if it holds up to 110 dB, that is stated.

    :param external_levels_db: The external A-weighted levels applied, in dB,
        in increasing 5 dB steps up to 110 dB.
    :param ear_levels_db: The 125 Hz octave-band level at the ear, in dB, with
        the external levels on the last axis and any number of leading axes
        (sample, subject, ear).
    :param ear_third_octave_levels_db: Instead, the 100 Hz, 125 Hz and 160 Hz
        one-third-octave levels at the ear, with those three on the last axis
        and the external levels on the one before.
    :return: :class:`AnrLinearityResult`.
    :raises ValueError: if the external levels are not 5 dB steps, if they pass
        110 dB, if neither or both of the ear-level forms are given, or if the
        shapes do not match.
    """
    external = np.asarray(external_levels_db, dtype=np.float64)
    if (
        external.ndim != 1
        or external.size < _GRID_RANK
        or not np.all(np.isfinite(external))
    ):
        msg = "'external_levels_db' must hold at least two finite levels, in dB."
        raise ValueError(msg)
    steps = np.diff(external)
    if np.any(np.abs(steps - _LINEARITY_STEP_DB) > _STEP_READING_DB):
        msg = (
            "'external_levels_db' must rise in the 5 dB steps of 5.4.4; got "
            f"steps of {steps.tolist()} dB."
        )
        raise ValueError(msg)
    if external[-1] > _MAXIMUM_EXTERNAL_LEVEL_DB + _STEP_READING_DB:
        msg = (
            "5.4.4 applies no external A-weighted level above 110 dB; got "
            f"{external[-1]:g} dB."
        )
        raise ValueError(msg)
    if (ear_levels_db is None) == (ear_third_octave_levels_db is None):
        msg = (
            "give either 'ear_levels_db' (the 125 Hz octave band) or "
            "'ear_third_octave_levels_db' (its three one-third-octave bands), "
            "not both."
        )
        raise ValueError(msg)
    if ear_levels_db is not None:
        levels = np.asarray(ear_levels_db, dtype=np.float64)
    else:
        thirds = np.asarray(ear_third_octave_levels_db, dtype=np.float64)
        if thirds.ndim < _GRID_RANK or thirds.shape[-1] != _LINEARITY_THIRDS:
            msg = (
                "'ear_third_octave_levels_db' must carry the 100 Hz, 125 Hz "
                "and 160 Hz bands on its last axis."
            )
            raise ValueError(msg)
        levels = 10.0 * np.log10(np.sum(10.0 ** (0.1 * thirds), axis=-1))
    if levels.ndim < 1 or levels.shape[-1] != external.size:
        msg = (
            "the ear levels must carry one value per external level on their "
            f"last axis; got {levels.shape} for {external.size} levels."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(levels)):
        msg = "the ear levels must contain only finite values, in dB."
        raise ValueError(msg)
    grid = levels.reshape(-1, external.size)
    return AnrLinearityResult(
        external_levels_db=np.array(external, dtype=np.float64),
        ear_levels_db=np.array(grid, dtype=np.float64),
        increments_db=np.diff(grid, axis=1),
    )
