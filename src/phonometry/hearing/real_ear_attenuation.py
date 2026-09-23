#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Real-ear attenuation of a hearing protector and its uncertainty (ISO 4869-1:2018).

ISO 4869-2 starts from a grid of attenuations, one per subject per octave band,
and this is where that grid comes from. ISO 4869-1 measures it subjectively:
each of sixteen test subjects finds their threshold of hearing twice for every
test signal, once with open ears and once with the protector in place, and the
attenuation of that subject in that band is the difference (4.6.2):

.. math::

   A_{j,f} = L_{\mathrm{occluded},j,f} - L_{\mathrm{open},j,f}

The test signals are one-third-octave bands of pink noise centred on the
octave frequencies 125 Hz to 8 kHz, with 63 Hz optional (4.1). The method
measures at threshold, so it describes a passive protector at any level but
underestimates one whose attenuation depends on level (Clause 1).

**What is reported (4.6.3, Clause 6).** The individual attenuations, and per
test signal their mean :math:`m` and standard deviation :math:`s`, together
with the expanded uncertainty of the mean. The uncertainty is the subject of
the normative Annex A, which models the attenuation as the measured value plus
three zero-mean input quantities (Formula (A.1)): the method (subject group,
fitting, threshold determination, tester, specimen), the test equipment and
the environment, each normal with a sensitivity coefficient of 1. Within one
laboratory the combined standard uncertainty of a given measurement is the
standard deviation of the mean (A.2),

.. math::

   u = \frac{s}{\sqrt{N}}, \qquad U_{95} = k\,u, \quad k = 2

which is what :func:`real_ear_attenuation` returns. Table A.2 prints typical
values of the three components within a laboratory and Table B.2 between
laboratories, for earplugs and earmuffs in three frequency ranges;
:data:`REAT_WITHIN_LABORATORY_UNCERTAINTY` and
:data:`REAT_BETWEEN_LABORATORY_UNCERTAINTY` carry the components, and the
combined and expanded values are derived from them rather than copied, which
reproduces every cell the two tables print.

**Are two measurements different? (Annex B).** Two mean attenuations differ
significantly at the 5 % level when their difference exceeds the root sum of
squares of their expanded uncertainties (B.1.2),

.. math::

   |m_1 - m_2| > \sqrt{U_{95,1}^2 + U_{95,2}^2}

which for two equal uncertainties is :math:`\sqrt{2}\,U_{95}`, the minimum
difference of B.1.1 and B.2. :func:`assess_attenuation_difference` applies it
band by band and :func:`minimum_significant_difference` gives the second form.
B.1.1 and B.2 evaluate it on the **rounded** :math:`U_{95}` their tables print,
and say so: "the expanded measurement uncertainty ... is 2,3 dB. The minimum
difference is thus :math:`\sqrt{2}` × 2,3 dB = 3,3 dB". From the unrounded
2,27 dB it is 3,21 dB, and from the unrounded 6,62 dB of Table B.2 it is
9,37 dB rather than 9,3 dB; both are the same rule, fed a different precision.

**The sound field (4.2.2).** The test room is qualified with the subject absent:
the level 15 cm from the reference point along the three axes stays within
±2,5 dB of the level at it, the two ear-side positions within 3 dB of each
other, and from 500 Hz up a directional microphone rotated through 360° sees a
variation no larger than Table 1 allows for its free-field rejection.
:func:`check_reat_sound_field` judges those three conditions, and its verdict
only passes a room whose directionality was measured: without the rotation, b)
is not judged and the room is not shown to qualify.

Clause, formula and table numbers refer to ISO 4869-1:2018(E).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .hearing_protectors import _octave_axis

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "REAT_BETWEEN_LABORATORY_UNCERTAINTY",
    "REAT_FIELD_VARIATION_LIMITS",
    "REAT_FREQUENCY_RANGES",
    "REAT_WITHIN_LABORATORY_UNCERTAINTY",
    "AttenuationDifferenceResult",
    "ProtectorUncertaintyBudget",
    "RealEarAttenuationResult",
    "ReatSoundFieldCheck",
    "allowable_field_variation",
    "assess_attenuation_difference",
    "check_reat_sound_field",
    "minimum_significant_difference",
    "real_ear_attenuation",
    "reat_expanded_uncertainty",
]

#: The coverage factor of Annex A: :math:`U_{95} = 2u`, "appropriate for
#: normally distributed parameters".
_COVERAGE_FACTOR = 2.0

#: A spread needs two dimensions and at least two subjects; 4.4.1 asks for 16.
_GRID_RANK = 2
_MINIMUM_SUBJECTS = 2


@dataclass(frozen=True)
class ProtectorUncertaintyBudget:
    r"""The three standard uncertainties of a hearing protector measurement.

    The budget of Table A.1: each component is normally distributed with a
    mean of zero and a sensitivity coefficient of 1, so the combined standard
    uncertainty is their root sum of squares (Formula (A.2)) and the expanded
    one is twice that. ISO 4869-6:2019 Annex A uses the same model for the
    active insertion loss of an active noise reduction earmuff.

    :ivar method_db: :math:`u_\mathrm{meth}`, the uncertainty of the mean of
        the individual attenuations of 16 test subjects: subject group,
        fitting, threshold determination, tester and specimen, in dB.
    :ivar equipment_db: :math:`u_\mathrm{eq}`, the uncertainty of the test
        signal generation equipment, in dB.
    :ivar environment_db: :math:`u_\mathrm{env}`, the uncertainty of the
        deviations from the ideal test environment, in dB.
    """

    method_db: float
    equipment_db: float
    environment_db: float

    @property
    def combined_db(self) -> float:
        r""":math:`u = \sqrt{u_\mathrm{meth}^2 + u_\mathrm{eq}^2 + u_\mathrm{env}^2}`, in dB.

        :return: The combined standard uncertainty, unrounded.
        """
        return math.hypot(self.method_db, self.equipment_db, self.environment_db)

    @property
    def expanded_db(self) -> float:
        """:math:`U_{95} = 2u`, in dB.

        :return: The expanded uncertainty for a 95 % coverage, unrounded.
        """
        return _COVERAGE_FACTOR * self.combined_db


#: The three frequency ranges Tables A.2 and B.2 print a column for, lowest
#: first: below 250 Hz, 250 Hz up to 4 kHz (both ends included), and above
#: 4 kHz. With the test signals of 4.1 that puts 63 Hz and 125 Hz in the
#: first, 250 Hz to 4 kHz in the second and 8 kHz alone in the third.
REAT_FREQUENCY_RANGES: tuple[str, ...] = (
    "below 250 Hz",
    "250 Hz up to 4 kHz",
    "above 4 kHz",
)

_LOW, _MID, _HIGH = REAT_FREQUENCY_RANGES
_RANGE_LOWER_EDGE_HZ = 250.0
_RANGE_UPPER_EDGE_HZ = 4000.0

#: Table A.2: typical uncertainty components within one laboratory, keyed by
#: protector type (``"earplug"``, ``"earmuff"``) and then by frequency range
#: (:data:`REAT_FREQUENCY_RANGES`). The combined and expanded rows of the table
#: are :attr:`ProtectorUncertaintyBudget.combined_db` and
#: :attr:`ProtectorUncertaintyBudget.expanded_db`; the table rounds them to
#: one decimal after computing them at full precision (its NOTE).
REAT_WITHIN_LABORATORY_UNCERTAINTY: Mapping[
    str, Mapping[str, ProtectorUncertaintyBudget]
] = MappingProxyType(
    {
        "earplug": MappingProxyType(
            {
                _LOW: ProtectorUncertaintyBudget(1.5, 0.2, 0.5),
                _MID: ProtectorUncertaintyBudget(1.0, 0.2, 0.5),
                _HIGH: ProtectorUncertaintyBudget(1.5, 0.2, 0.5),
            }
        ),
        "earmuff": MappingProxyType(
            {
                _LOW: ProtectorUncertaintyBudget(1.0, 0.2, 0.5),
                _MID: ProtectorUncertaintyBudget(0.6, 0.2, 0.5),
                _HIGH: ProtectorUncertaintyBudget(1.0, 0.2, 0.5),
            }
        ),
    }
)

#: Table B.2: the same components between laboratories, keyed the same way.
#: Every component is larger, and the method component most of all: what two
#: laboratories disagree on is mostly how their subjects fit the protector.
REAT_BETWEEN_LABORATORY_UNCERTAINTY: Mapping[
    str, Mapping[str, ProtectorUncertaintyBudget]
] = MappingProxyType(
    {
        "earplug": MappingProxyType(
            {
                _LOW: ProtectorUncertaintyBudget(4.0, 0.3, 0.8),
                _MID: ProtectorUncertaintyBudget(3.2, 0.3, 0.8),
                _HIGH: ProtectorUncertaintyBudget(3.2, 0.3, 0.8),
            }
        ),
        "earmuff": MappingProxyType(
            {
                _LOW: ProtectorUncertaintyBudget(1.8, 0.3, 0.8),
                _MID: ProtectorUncertaintyBudget(2.3, 0.3, 0.8),
                _HIGH: ProtectorUncertaintyBudget(3.2, 0.3, 0.8),
            }
        ),
    }
)

#: Table 1: the variation of the sound-field level a directional microphone
#: may see when rotated at the reference point, by its free-field rejection.
#: Each pair is ``(lowest rejection, allowable variation)``, both in dB, from
#: the most directional microphone down: a rejection of at least 25 dB allows
#: 20 dB, one from 10 dB up to 15 dB allows 5 dB, and below 10 dB the
#: microphone is not suitable.
REAT_FIELD_VARIATION_LIMITS: tuple[tuple[float, float], ...] = (
    (25.0, 20.0),
    (20.0, 15.0),
    (15.0, 10.0),
    (10.0, 5.0),
)

#: 4.2.2 a): each of the six positions 15 cm from the reference point stays
#: within this many decibels of the level at it.
_POSITION_TOLERANCE_DB = 2.5
#: 4.2.2 a): and the right and left positions within this many of each other.
_LEFT_RIGHT_TOLERANCE_DB = 3.0
#: 4.2.2 b): the directionality is evaluated from this test signal up.
_DIRECTIONALITY_FROM_HZ = 500.0
#: 4.2.2 a): the six positions, two on each of the three axes.
_POSITIONS: tuple[str, ...] = ("front", "back", "left", "right", "up", "down")


def _band_axis(frequencies: ArrayLike | None, count: int, owner: str) -> np.ndarray:
    """The centre frequencies of the test signals, defaulted to those of 4.1.

    :param frequencies: The caller's frequencies in hertz, or ``None``.
    :param count: How many bands the data carries.
    :param owner: The function name, for the error message.
    :return: The frequencies as a float array.
    :raises ValueError: if the count does not match, or no default fits.
    """
    given = None if frequencies is None else np.array(frequencies, dtype=np.float64)
    return _octave_axis(given, count, owner)


def _subject_grid(values: ArrayLike, name: str) -> np.ndarray:
    """A ``(subjects, bands)`` grid of finite decibel values.

    :param values: One row per test subject, one column per test signal.
    :param name: The argument name, for the error message.
    :return: The grid as a float array.
    :raises ValueError: if it is not two-dimensional, holds fewer than two
        subjects, or holds a value that is not finite.
    """
    grid = np.asarray(values, dtype=np.float64)
    if grid.ndim != _GRID_RANK:
        msg = (
            f"'{name}' must be a (subjects, bands) grid: ISO 4869-1 measures "
            "one threshold per subject per test signal."
        )
        raise ValueError(msg)
    if grid.shape[0] < _MINIMUM_SUBJECTS:
        msg = (
            f"'{name}' needs at least two subjects for a standard deviation; "
            "4.4.1 asks for 16."
        )
        raise ValueError(msg)
    if grid.shape[1] == 0 or not np.all(np.isfinite(grid)):
        msg = f"'{name}' must hold at least one band and only finite values, in dB."
        raise ValueError(msg)
    return grid


@dataclass(frozen=True)
class RealEarAttenuationResult:
    r"""The attenuation of a hearing protector on a panel of subjects (4.6).

    :ivar attenuation_db: The individual attenuations :math:`A_{j,f}`, one row
        per subject and one column per test signal, in dB. This is the grid
        :func:`phonometry.hearing.assumed_protection_value`,
        :func:`phonometry.hearing.hml_rating` and
        :func:`phonometry.hearing.snr_rating` take, unchanged.
    :ivar mean_db: The mean attenuation :math:`m` per test signal, in dB.
    :ivar standard_deviation_db: The standard deviation :math:`s` per test
        signal over the subjects, the sample one over :math:`N - 1`, in dB.
    :ivar standard_uncertainty_db: :math:`u = s/\sqrt{N}`, the standard
        deviation of the mean (A.2), in dB.
    :ivar expanded_uncertainty_db: :math:`U_{95} = 2u` (A.1), in dB.
    :ivar frequencies: The centre frequencies of the test signals, in hertz.
    :ivar subjects: The number of test subjects :math:`N`.
    """

    attenuation_db: np.ndarray
    mean_db: np.ndarray
    standard_deviation_db: np.ndarray
    standard_uncertainty_db: np.ndarray
    expanded_uncertainty_db: np.ndarray
    frequencies: np.ndarray
    subjects: int

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the mean attenuation the way Clause 6 l) asks for it.

        Increasing attenuation points downwards and, on a figure this creates,
        50 dB on the vertical axis spans one decade on the horizontal one
        (IEC 60263). The individual attenuations are drawn faint behind the
        mean, and the expanded uncertainty as bars on it.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the mean curve.
        :return: The axes.
        """
        from .._plot.hearing import plot_real_ear_attenuation

        return plot_real_ear_attenuation(self, ax=ax, language=language, **kwargs)


def real_ear_attenuation(
    attenuation_db: ArrayLike | None = None,
    *,
    open_threshold_db: ArrayLike | None = None,
    occluded_threshold_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> RealEarAttenuationResult:
    r"""The attenuation of a protector, its spread and its uncertainty (4.6, A.2).

    Give the individual attenuations, or the two thresholds they come from
    (4.6.2):

    .. math::

       A_{j,f} = L_{\mathrm{occluded},j,f} - L_{\mathrm{open},j,f}

    and this returns, per test signal, the mean, the standard deviation over
    the subjects, the standard uncertainty of the mean and the expanded
    uncertainty of Annex A:

    .. math::

       u = \frac{s}{\sqrt{N}}, \qquad U_{95} = 2u

    Everything is computed at full precision; Tables A.3 and B.1 round to one
    decimal afterwards, and so should a report. The two thresholds only need
    to share a reference: a threshold in sound pressure level and one in
    hearing level give the same difference.

    :param attenuation_db: A ``(subjects, bands)`` grid of individual
        attenuations, in dB.
    :param open_threshold_db: The thresholds of hearing with open ears, a
        ``(subjects, bands)`` grid in dB, given together with
        ``occluded_threshold_db`` instead of ``attenuation_db``.
    :param occluded_threshold_db: The thresholds with the protector in place,
        in dB, on the same grid.
    :param frequencies: The centre frequencies of the test signals, in hertz,
        or ``None`` for the seven of 4.1 (125 Hz to 8 kHz) when the grid has
        seven columns, or those eight with the optional 63 Hz when it has
        eight.
    :return: :class:`RealEarAttenuationResult`.
    :raises ValueError: if neither form or both are given, if a grid is not
        two-dimensional or holds fewer than two subjects or a value that is not
        finite, if the two thresholds differ in shape, or if ``frequencies``
        does not match the grid.
    """
    thresholds = open_threshold_db is not None or occluded_threshold_db is not None
    if attenuation_db is not None and not thresholds:
        grid = _subject_grid(attenuation_db, "attenuation_db")
    elif (
        attenuation_db is None
        and open_threshold_db is not None
        and occluded_threshold_db is not None
    ):
        open_ears = _subject_grid(open_threshold_db, "open_threshold_db")
        occluded = _subject_grid(occluded_threshold_db, "occluded_threshold_db")
        if open_ears.shape != occluded.shape:
            msg = (
                "'open_threshold_db' and 'occluded_threshold_db' must be the "
                f"same subjects and bands; got {open_ears.shape} and "
                f"{occluded.shape}."
            )
            raise ValueError(msg)
        grid = occluded - open_ears
    else:
        msg = (
            "give either 'attenuation_db', or both 'open_threshold_db' and "
            "'occluded_threshold_db' (4.6.2), and not both forms."
        )
        raise ValueError(msg)
    freqs = _band_axis(frequencies, grid.shape[1], "real_ear_attenuation")
    subjects = int(grid.shape[0])
    mean = np.asarray(grid.mean(axis=0), dtype=np.float64)
    spread = np.asarray(grid.std(axis=0, ddof=1), dtype=np.float64)
    standard = spread / math.sqrt(subjects)
    return RealEarAttenuationResult(
        attenuation_db=np.array(grid, dtype=np.float64),
        mean_db=mean,
        standard_deviation_db=spread,
        standard_uncertainty_db=standard,
        expanded_uncertainty_db=_COVERAGE_FACTOR * standard,
        frequencies=freqs,
        subjects=subjects,
    )


def _frequency_range(frequency: float) -> str:
    """The Table A.2 and B.2 column a test signal falls in.

    :param frequency: The centre frequency of the test signal, in hertz.
    :return: One of :data:`REAT_FREQUENCY_RANGES`.
    """
    if frequency < _RANGE_LOWER_EDGE_HZ:
        return _LOW
    if frequency <= _RANGE_UPPER_EDGE_HZ:
        return _MID
    return _HIGH


def reat_expanded_uncertainty(
    frequencies: ArrayLike,
    *,
    protector: str,
    between_laboratories: bool = False,
) -> np.ndarray:
    """The typical :math:`U_{95}` of a mean attenuation, band by band (A.2, B.2).

    Reads the budget of Table A.2 (within one laboratory) or Table B.2
    (between laboratories) for the protector type and the frequency range each
    test signal falls in, and returns its expanded uncertainty at full
    precision. These are the typical values B.1.1 and B.2 draw on when no data
    of a specific measurement are at hand; the text of both uses them rounded
    to one decimal, as the tables print them (see
    :func:`minimum_significant_difference`).

    :param frequencies: The centre frequencies of the test signals, in hertz.
    :param protector: ``"earplug"`` or ``"earmuff"``.
    :param between_laboratories: ``False`` (default) for Table A.2, ``True``
        for Table B.2.
    :return: :math:`U_{95}` per band, in dB.
    :raises ValueError: for a protector type the tables do not list, or for
        frequencies that are not positive and finite.
    """
    table = (
        REAT_BETWEEN_LABORATORY_UNCERTAINTY
        if between_laboratories
        else REAT_WITHIN_LABORATORY_UNCERTAINTY
    )
    if protector not in table:
        listed = ", ".join(repr(key) for key in table)
        msg = f"'protector' must be one of {listed}; got {protector!r}."
        raise ValueError(msg)
    freqs = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    if freqs.ndim != 1 or not np.all(np.isfinite(freqs)) or np.any(freqs <= 0.0):
        msg = "'frequencies' must be positive, finite centre frequencies in hertz."
        raise ValueError(msg)
    column = table[protector]
    return np.array(
        [column[_frequency_range(float(f))].expanded_db for f in freqs],
        dtype=np.float64,
    )


def minimum_significant_difference(
    expanded_uncertainty_db: ArrayLike,
) -> float | np.ndarray:
    r"""The smallest difference between two means that is significant (B.1.1).

    For two measurements with the same expanded uncertainty the criterion of
    B.1.2 reduces to

    .. math::

       \Delta_\mathrm{min} = \frac{2\,U_{95}}{\sqrt{2}} = \sqrt{2}\,U_{95}

    and two means that differ by more than that differ significantly at the
    95 % confidence level. B.1.1 and B.2 evaluate it on the uncertainty their
    tables print rounded to one decimal, and say so: with the 2,3 dB of Table
    A.2 it is 3,3 dB, where the unrounded 2,27 dB gives 3,21 dB. Feed this the
    value the comparison should rest on.

    :param expanded_uncertainty_db: :math:`U_{95}`, in dB, a number or an
        array.
    :return: :math:`\sqrt{2}\,U_{95}`, in dB, a float for a scalar input and an
        array otherwise.
    :raises ValueError: for an uncertainty that is negative or not finite.
    """
    values = np.asarray(expanded_uncertainty_db, dtype=np.float64)
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        msg = "'expanded_uncertainty_db' must be finite and not negative, in dB."
        raise ValueError(msg)
    difference = math.sqrt(2.0) * values
    return float(difference) if difference.ndim == 0 else difference


@dataclass(frozen=True)
class AttenuationDifferenceResult:
    r"""Whether two mean attenuations differ significantly, band by band (B.1.2).

    :ivar difference_db: :math:`|m_1 - m_2|` per band, in dB.
    :ivar criterion_db: :math:`\sqrt{U_{95,1}^2 + U_{95,2}^2}` per band, in
        dB. A difference larger than this is significant at the 5 % level.
    :ivar significant: Whether each band's difference exceeds its criterion.
    :ivar first_mean_db: :math:`m_1` per band, in dB.
    :ivar second_mean_db: :math:`m_2` per band, in dB.
    :ivar first_expanded_uncertainty_db: :math:`U_{95,1}` per band, in dB.
    :ivar second_expanded_uncertainty_db: :math:`U_{95,2}` per band, in dB.
    :ivar frequencies: The centre frequencies of the test signals, in hertz.
    """

    difference_db: np.ndarray
    criterion_db: np.ndarray
    significant: np.ndarray
    first_mean_db: np.ndarray
    second_mean_db: np.ndarray
    first_expanded_uncertainty_db: np.ndarray
    second_expanded_uncertainty_db: np.ndarray
    frequencies: np.ndarray

    @property
    def any_significant(self) -> bool:
        """Whether the two measurements differ significantly in any band.

        :return: ``True`` when at least one band's difference exceeds its
            criterion.
        """
        return bool(np.any(self.significant))

    @property
    def significant_frequencies(self) -> np.ndarray:
        """The test signals at which the two measurements differ, in hertz.

        :return: The centre frequencies of the significant bands.
        """
        return np.asarray(self.frequencies[self.significant], dtype=np.float64)

    def __bool__(self) -> bool:
        """Refuse to stand in for a verdict that is one per band.

        ``if assess_attenuation_difference(...):`` would otherwise be true for
        every comparison, since an object is. Read :attr:`significant` for the
        bands or :attr:`any_significant` for the whole.

        :raises TypeError: Always.
        """
        msg = (
            "an AttenuationDifferenceResult has no truth value; read "
            "'.significant' per band or '.any_significant' for the whole"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each band's difference against the criterion it has to beat.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the difference bars.
        :return: The axes.
        """
        from .._plot.hearing import plot_attenuation_difference

        return plot_attenuation_difference(self, ax=ax, language=language, **kwargs)


def _band_values(values: ArrayLike, count: int | None, name: str) -> np.ndarray:
    """A one-dimensional array of finite decibel values, one per band.

    :param values: The values, or a scalar to broadcast over ``count`` bands.
    :param count: The number of bands expected, or ``None`` to take it as is.
    :param name: The argument name, for the error message.
    :return: The values as a float array of its own, never the caller's.
    :raises ValueError: for a shape that does not fit or a value that is not
        finite.
    """
    array = np.array(values, dtype=np.float64)
    if array.ndim == 0 and count is not None:
        array = np.full(count, float(array))
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        msg = f"'{name}' must be a non-empty one-dimensional array of finite values."
        raise ValueError(msg)
    if count is not None and array.size != count:
        msg = f"'{name}' must hold one value per band; got {array.size} for {count}."
        raise ValueError(msg)
    return array


def _mean_and_uncertainty(
    measurement: ArrayLike | RealEarAttenuationResult,
    uncertainty: ArrayLike | None,
    which: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """The mean, the expanded uncertainty and the band axis of one measurement.

    :param measurement: A result, or the mean attenuations as an array.
    :param uncertainty: The expanded uncertainty, required with an array and
        refused with a result, which carries its own.
    :param which: ``"first"`` or ``"second"``, for the error messages.
    :return: The mean, :math:`U_{95}`, and the frequencies when the result
        carries them.
    :raises ValueError: if the uncertainty is missing for an array, or given
        twice for a result.
    """
    name = f"{which}_expanded_uncertainty_db"
    if isinstance(measurement, RealEarAttenuationResult):
        if uncertainty is not None:
            msg = (
                f"'{name}' is carried by the {which} result already; pass the "
                "means as an array to compare them with another uncertainty."
            )
            raise ValueError(msg)
        return (
            np.array(measurement.mean_db, dtype=np.float64),
            np.array(measurement.expanded_uncertainty_db, dtype=np.float64),
            np.array(measurement.frequencies, dtype=np.float64),
        )
    mean = _band_values(measurement, None, which)
    if uncertainty is None:
        msg = (
            f"'{name}' is required when the {which} measurement is given as "
            "its means: the test of B.1.2 weighs a difference against both "
            "uncertainties."
        )
        raise ValueError(msg)
    spread = _band_values(uncertainty, mean.size, name)
    if np.any(spread < 0.0):
        msg = f"'{name}' must not be negative."
        raise ValueError(msg)
    return mean, spread, None


def assess_attenuation_difference(
    first: ArrayLike | RealEarAttenuationResult,
    second: ArrayLike | RealEarAttenuationResult,
    *,
    first_expanded_uncertainty_db: ArrayLike | None = None,
    second_expanded_uncertainty_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> AttenuationDifferenceResult:
    r"""Do two attenuation measurements differ significantly? (Annex B).

    Annex B asks it of two tests of the same earmuff in two configurations
    (B.1.2), of two earplugs in one laboratory (B.1.1) and of one earplug in
    two laboratories (B.2), and answers band by band the same way: the means
    differ significantly at the 5 % level when

    .. math::

       |m_1 - m_2| > \sqrt{U_{95,1}^2 + U_{95,2}^2}

    Each measurement is either a :class:`RealEarAttenuationResult`, which
    carries its own :math:`U_{95}` from its own data (B.1.2), or its mean
    attenuations with an uncertainty given alongside, such as the typical one
    :func:`reat_expanded_uncertainty` reads from Table A.2 or B.2 (B.1.1,
    B.2).

    :param first: The first measurement, as a result or as its means in dB.
    :param second: The second measurement, the same way.
    :param first_expanded_uncertainty_db: :math:`U_{95,1}` in dB, a number or
        one per band, when ``first`` is given as means.
    :param second_expanded_uncertainty_db: :math:`U_{95,2}` in dB, likewise.
    :param frequencies: The centre frequencies, in hertz, or ``None`` to take
        them from a result or, for bare means, to assume the test signals of
        4.1 as :func:`real_ear_attenuation` does.
    :return: :class:`AttenuationDifferenceResult`.
    :raises ValueError: if an uncertainty is missing for bare means or given
        twice for a result, if the two measurements cover different bands, or
        if a value is not finite.
    """
    m1, u1, f1 = _mean_and_uncertainty(first, first_expanded_uncertainty_db, "first")
    m2, u2, f2 = _mean_and_uncertainty(second, second_expanded_uncertainty_db, "second")
    if m1.size != m2.size:
        msg = (
            "the two measurements must cover the same test signals; got "
            f"{m1.size} and {m2.size} bands."
        )
        raise ValueError(msg)
    carried = [axis for axis in (f1, f2) if axis is not None]
    if frequencies is not None:
        freqs = _band_axis(frequencies, m1.size, "assess_attenuation_difference")
    elif carried:
        freqs = carried[0]
    else:
        freqs = _band_axis(None, m1.size, "assess_attenuation_difference")
    for axis in carried:
        if not np.allclose(axis, freqs):
            msg = (
                "the two measurements were taken at different test signals: "
                f"{axis.tolist()} against {freqs.tolist()}."
            )
            raise ValueError(msg)
    difference = np.abs(m1 - m2)
    criterion = np.hypot(u1, u2)
    return AttenuationDifferenceResult(
        difference_db=difference,
        criterion_db=criterion,
        significant=np.asarray(difference > criterion, dtype=bool),
        first_mean_db=m1,
        second_mean_db=m2,
        first_expanded_uncertainty_db=u1,
        second_expanded_uncertainty_db=u2,
        frequencies=np.asarray(freqs, dtype=np.float64),
    )


def allowable_field_variation(free_field_rejection_db: float) -> float:
    """How much a rotated directional microphone may see vary (Table 1).

    :param free_field_rejection_db: The free-field rejection of the
        directional microphone at the test signal, in dB: front to side for a
        cosine microphone, front to back for a cardioid one (4.2.2 b)).
    :return: The allowable variation of the sound-field level, in dB.
    :raises ValueError: for a rejection below 10 dB, for which Table 1 says the
        microphone is not suitable, or one that is not finite.
    """
    rejection = float(free_field_rejection_db)
    if not math.isfinite(rejection):
        msg = "'free_field_rejection_db' must be finite, in dB."
        raise ValueError(msg)
    for lowest, allowed in REAT_FIELD_VARIATION_LIMITS:
        if rejection >= lowest:
            return allowed
    minimum = REAT_FIELD_VARIATION_LIMITS[-1][0]
    msg = (
        f"a free-field rejection of {rejection:g} dB is below {minimum:g} dB, "
        "for which Table 1 says the microphone is not suitable for 4.2.2 b)."
    )
    raise ValueError(msg)


@dataclass(frozen=True)
class ReatSoundFieldCheck:
    r"""Whether the test site's sound field qualifies for ISO 4869-1 (4.2.2).

    :ivar frequencies: The centre frequencies of the test signals, in hertz.
    :ivar position_deviation_db: The level at each of the six positions 15 cm
        from the reference point less the level at it, one row per position in
        the order of :attr:`positions`, in dB.
    :ivar left_right_difference_db: The difference between the right and left
        positions per band, as an absolute value, in dB.
    :ivar rotation_variation_db: The spread of the levels a rotated directional
        microphone saw per band, in dB, or ``nan`` where 4.2.2 b) does not
        apply (below 500 Hz) or no rotation was given.
    :ivar allowable_variation_db: What Table 1 allows that spread, in dB, or
        ``None`` when no rotation was given.
    :ivar positions: The position names, in row order.

    4.2.2 b) is a requirement of the clause, not an option: a check made
    without the rotation leaves it unjudged whenever a band reaches 500 Hz,
    :attr:`directionality_judged` says so, and :attr:`passes` is ``False``
    until it is judged. :attr:`uniform` and :attr:`balanced` still give the
    verdict of a) on its own.
    """

    frequencies: np.ndarray
    position_deviation_db: np.ndarray
    left_right_difference_db: np.ndarray
    rotation_variation_db: np.ndarray
    allowable_variation_db: float | None
    positions: tuple[str, ...] = _POSITIONS

    @property
    def uniform(self) -> np.ndarray:
        """Per band, whether all six positions stay within ±2,5 dB (4.2.2 a)).

        :return: One boolean per band.
        """
        return np.all(
            np.abs(self.position_deviation_db) <= _POSITION_TOLERANCE_DB, axis=0
        )

    @property
    def balanced(self) -> np.ndarray:
        """Per band, whether right and left differ by 3 dB at most (4.2.2 a)).

        :return: One boolean per band.
        """
        return self.left_right_difference_db <= _LEFT_RIGHT_TOLERANCE_DB

    @property
    def diffuse(self) -> np.ndarray:
        """Per band, whether the rotation stays within Table 1 (4.2.2 b)).

        Bands the clause does not reach, below 500 Hz, count as meeting it.
        With no rotation given nothing was measured, every band reads
        ``True`` here and :attr:`directionality_judged` is ``False``.

        :return: One boolean per band.
        """
        if self.allowable_variation_db is None:
            return np.ones(self.frequencies.size, dtype=bool)
        judged = np.isfinite(self.rotation_variation_db)
        within = self.rotation_variation_db <= self.allowable_variation_db
        return np.asarray(~judged | within, dtype=bool)

    @property
    def directionality_judged(self) -> bool:
        """Whether 4.2.2 b) was judged.

        :return: ``True`` when a rotation was given, or when no test signal
            reaches the 500 Hz from which b) applies.
        """
        reached = bool(np.any(self.frequencies >= _DIRECTIONALITY_FROM_HZ))
        return self.allowable_variation_db is not None or not reached

    @property
    def passes(self) -> bool:
        """Whether the sound field qualifies for 4.2.2, a) and b) both judged.

        :return: ``True`` when every band meets a) and b); ``False`` when a
            band fails either, or when b) was not judged.
        """
        return bool(
            self.directionality_judged
            and np.all(self.uniform)
            and np.all(self.balanced)
            and np.all(self.diffuse)
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a ReatSoundFieldCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each condition of 4.2.2 against its limit, band by band.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the worst position deviation curve.
        :return: The axes.
        """
        from .._plot.hearing import plot_reat_sound_field

        return plot_reat_sound_field(self, ax=ax, language=language, **kwargs)


def check_reat_sound_field(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    rotation_levels_db: ArrayLike | None = None,
    free_field_rejection_db: float | None = None,
    frequencies: ArrayLike | None = None,
) -> ReatSoundFieldCheck:
    r"""Is the sound field of the test site diffuse enough? (4.2.2).

    Measured with the subject and the chair absent (4.2.1):

    - a) the level at each of the six positions 15 cm from the reference point,
      front and back, left and right, up and down, stays within ±2,5 dB of the
      level at the reference point, and the right and left positions within
      3 dB of each other;
    - b) from the 500 Hz test signal up, a directional microphone rotated
      through 360° in the horizontal plane at the reference point sees the
      level vary by no more than Table 1 allows for its free-field rejection
      (:func:`allowable_field_variation`).

    The reverberation time of 4.2.3 and the ambient noise of 4.2.4 are
    separate requirements of the test site and are not judged here.

    :param position_levels_db: The level at each position per test signal, in
        dB, keyed ``"front"``, ``"back"``, ``"left"``, ``"right"``, ``"up"``
        and ``"down"``.
    :param reference_levels_db: The level at the reference point per test
        signal, in dB.
    :param rotation_levels_db: The levels the directional microphone saw while
        rotated, a ``(readings, bands)`` grid in dB, on the same band axis;
        bands below 500 Hz are not read and may be ``nan``. ``None`` leaves
        b) unjudged, and the verdict then does not pass.
    :param free_field_rejection_db: The free-field rejection of that
        microphone, in dB, required with ``rotation_levels_db``.
    :param frequencies: The centre frequencies, in hertz, or ``None`` for the
        test signals of 4.1 as :func:`real_ear_attenuation` assumes them.
    :return: :class:`ReatSoundFieldCheck`.
    :raises ValueError: if a position is missing or unknown, if the bands do
        not match, if a rotation is given without its microphone's rejection
        or the other way round, or if that rejection is below the 10 dB Table 1
        accepts.
    """
    names = set(position_levels_db)
    if names != set(_POSITIONS):
        msg = (
            "'position_levels_db' must give the six positions of 4.2.2 a), "
            f"{', '.join(_POSITIONS)}; got {', '.join(sorted(names))}."
        )
        raise ValueError(msg)
    reference = _band_values(reference_levels_db, None, "reference_levels_db")
    count = reference.size
    levels = np.vstack(
        [
            _band_values(
                position_levels_db[name], count, f"position_levels_db[{name!r}]"
            )
            for name in _POSITIONS
        ]
    )
    freqs = _band_axis(frequencies, count, "check_reat_sound_field")
    deviation = levels - reference[None, :]
    left = levels[_POSITIONS.index("left")]
    right = levels[_POSITIONS.index("right")]
    variation = np.full(count, np.nan)
    allowed: float | None = None
    if (rotation_levels_db is None) != (free_field_rejection_db is None):
        msg = (
            "give 'rotation_levels_db' and 'free_field_rejection_db' "
            "together: Table 1 sets the limit by the microphone's rejection."
        )
        raise ValueError(msg)
    if rotation_levels_db is not None and free_field_rejection_db is not None:
        allowed = allowable_field_variation(free_field_rejection_db)
        rotation = np.asarray(rotation_levels_db, dtype=np.float64)
        if rotation.ndim != _GRID_RANK or rotation.shape[1] != count:
            msg = (
                "'rotation_levels_db' must be a (readings, bands) grid on the "
                f"same {count} bands."
            )
            raise ValueError(msg)
        judged = freqs >= _DIRECTIONALITY_FROM_HZ
        readings = rotation[:, judged]
        if readings.shape[0] < _MINIMUM_SUBJECTS or not np.all(np.isfinite(readings)):
            msg = (
                "'rotation_levels_db' needs at least two finite readings in "
                "every band from 500 Hz up."
            )
            raise ValueError(msg)
        variation[judged] = readings.max(axis=0) - readings.min(axis=0)
    return ReatSoundFieldCheck(
        frequencies=np.asarray(freqs, dtype=np.float64),
        position_deviation_db=deviation,
        left_right_difference_db=np.abs(right - left),
        rotation_variation_db=variation,
        allowable_variation_db=allowed,
    )
