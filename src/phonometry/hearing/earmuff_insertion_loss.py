#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The insertion loss of an earmuff on an acoustic test fixture (ISO 4869-3:2007).

ISO 4869-3 measures an earmuff without a listener. The acoustic test fixture
(ATF) is a metal cylinder of 135 mm diameter with its end faces 145 mm apart,
a pressure microphone flush with one of them and a spacer that carries the
headband (5.1). In a random-incidence field or a plane progressive wave, the
level at the microphone is measured without the earmuff and again with it
seated on the fixture, and the difference in each one-third-octave band is
the insertion loss (3.5, 5.4.2):

.. math::

   IL_f = L_{\mathrm{open},f} - L_{\mathrm{occl},f}

in bands from at least 63 Hz to 8 kHz (5.3), from at least three fittings
unless the device's repeatability is known (5.4.3), reported to the nearest
0,1 dB and drawn with increasing values downwards (Clause 6).

**What it is for, and what it is not (Clause 1).** The method checks
production spreads for type approval or certification and the change of
performance with age, and makes sure the samples sent for the subjective
test of ISO 4869-1 are typical of their type. It is not the basic type test,
and its data "are not intended to be quoted as representing the real-ear
sound attenuation of an ear-muff, nor the protection provided by the
ear-muff"; the Introduction adds that its results are not those of
ISO 4869-1. So :class:`EarmuffInsertionLossResult` is not an input of
:func:`phonometry.hearing.assumed_protection_value`,
:func:`phonometry.hearing.hml_rating` or
:func:`phonometry.hearing.snr_rating`: those take the real-ear attenuation of
sixteen subjects, :func:`phonometry.hearing.real_ear_attenuation`, and
nothing here converts one into the other.

**The test site (5.1.4, 5.2).** :func:`check_random_incidence_field` judges
the random-incidence field of 5.2.2 with the diffuse-field judgement of
ISO 8253-2:2009, 5.3, and this standard's Table 1
(:data:`RANDOM_INCIDENCE_VARIATION_LIMITS`); Annex A notes that the ATF
itself may serve as the directional microphone where its front-to-random
index, :data:`ATF_FRONT_TO_RANDOM_INDEX_DB`, reaches 4 dB.
:func:`check_plane_progressive_wave` judges the plane wave of 5.2.3, and
:func:`verify_fixture_isolation` the acoustic isolation of the fixture with
its isolation cup (5.1.4).

**The uncertainty (Annex B).** The insertion loss is modelled as the two
levels plus three zero-mean inputs for the fixture, the sound field and the
equipment (Formula (B.1)), all normal with a sensitivity coefficient of 1,
so

.. math::

   u = \sqrt{\sum_i (c_i u_i)^2}, \qquad U = 2u

(Formula (B.2)). The standard uncertainty of each level is the standard
deviation of the mean of the repeated measurements; Table B.1 prints typical
values, 0,5 dB open, 1,0 dB occluded, 0,3 dB, 0,5 dB and 0,2 dB, which give
:math:`u` = 1,3 dB and :math:`U` = 2,6 dB
(:data:`EARMUFF_INSERTION_LOSS_UNCERTAINTY`).

Clause, table and formula numbers refer to ISO 4869-3:2007(E).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.boundary import round_half_up
from .._internal.display import RichDisplay
from .._internal.frozen import OwnsArrays
from .sound_field_audiometry import (
    _RANDOM_INCIDENCE_CLAUSE,
    DiffuseSoundFieldCheck,
    _diffuse_field_check,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "ATF_FRONT_TO_RANDOM_INDEX_DB",
    "EARMUFF_INSERTION_LOSS_UNCERTAINTY",
    "EARMUFF_TEST_BANDS_HZ",
    "RANDOM_INCIDENCE_VARIATION_LIMITS",
    "EarmuffInsertionLossResult",
    "FixtureIsolationCheck",
    "InsertionLossUncertaintyBudget",
    "PlaneProgressiveWaveCheck",
    "check_plane_progressive_wave",
    "check_random_incidence_field",
    "earmuff_insertion_loss",
    "verify_fixture_isolation",
]

#: The one-third-octave centre frequencies 5.3 asks for at least, in hertz:
#: 63 Hz to 8 kHz.
EARMUFF_TEST_BANDS_HZ: tuple[float, ...] = (
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
)

#: Table 1: the variation of the level at the reference point a directional
#: microphone may read between any two directions, by its front-to-random
#: sensitivity index, as ``(lowest index, allowable variation)`` pairs in dB:
#: 5 dB from an index of 5 dB up, 4 dB from 4 dB up, and a microphone below
#: 4 dB is not suitable. The table prints its first row as "> 5" and its
#: second as "4 to 5", while the text of 5.2.2 asks for "at least 5 dB" to
#: allow 5 dB; the row for exactly 5 dB follows the text, as the same table of
#: ISO 8253-2 does (see ``docs/ERRATA.md``).
RANDOM_INCIDENCE_VARIATION_LIMITS: tuple[tuple[float, float], ...] = (
    (5.0, 5.0),
    (4.0, 4.0),
)

#: Table A.1 (informative): the front-to-random sensitivity index of an ATF
#: with a WS1P microphone, in dB, keyed by frequency in hertz, 500 Hz to
#: 8 kHz. Where it reaches 4 dB the fixture may itself test the directional
#: condition of 5.2.2 (NOTE to Table 1).
ATF_FRONT_TO_RANDOM_INDEX_DB: Mapping[float, float] = MappingProxyType(
    {
        500.0: 1.7,
        630.0: 2.2,
        800.0: 2.8,
        1000.0: 3.2,
        1250.0: 4.6,
        1600.0: 4.6,
        2000.0: 6.3,
        2500.0: 6.5,
        3150.0: 5.9,
        4000.0: 2.9,
        5000.0: -0.6,
        6300.0: 5.1,
        8000.0: 5.9,
    }
)

#: 5.4.3: at least this many repetitions, unless the device's repeatability
#: is known.
_MINIMUM_REPETITIONS = 3
#: 5.3: the isolation cup lowers the reading at least this much below the
#: protector's, and the adjacent bands of the system's response differ by at
#: most this much; the test signal stays within this much of its setting.
_FLOOR_MARGIN_DB = 10.0
_ADJACENT_BAND_STEP_DB = 5.0
_LEVEL_STABILITY_DB = 1.0
#: 5.2.3: the two end-face positions within this, and from 500 Hz the level
#: facing the source this far above the level facing away, read with a
#: microphone of a front-to-rear index greater than 15 dB.
_END_FACE_TOLERANCE_DB = 2.0
_FRONT_TO_BACK_MINIMUM_DB = 10.0
_FRONT_TO_REAR_INDEX_DB = 15.0
_DIRECTIONAL_FROM_HZ = 500.0
#: 5.1.4: the least acoustic isolation of the fixture in three ranges of
#: centre frequency, 63 Hz to 250 Hz, 315 Hz to 4 kHz, and above.
_ISOLATION_LOW_DB = 50.0
_ISOLATION_MID_DB = 65.0
_ISOLATION_HIGH_DB = 55.0
#: The splits between those ranges, halfway between the bands either side on
#: a logarithmic axis, so that nominal and exact centre frequencies fall in
#: the same range.
_ISOLATION_LOW_SPLIT_HZ = math.sqrt(250.0 * 315.0)
_ISOLATION_HIGH_SPLIT_HZ = math.sqrt(4000.0 * 5000.0)
_ISOLATION_FROM_SPLIT_HZ = math.sqrt(50.0 * 63.0)
#: Table B.1's typical standard uncertainties of the two levels, used when
#: fewer than two repetitions give one of them.
_OPEN_LEVEL_U_DB = 0.5
_OCCLUDED_LEVEL_U_DB = 1.0
#: B.4: the coverage factor for about 95 %.
_COVERAGE_FACTOR = 2.0
#: Clause 6: the insertion loss is reported to 0,1 dB, one decimal place.
_REPORT_DECIMALS = 1
#: A limit reached through floating-point arithmetic is on the limit.
_BOUNDARY_SLACK_DB = 1e-9
_GRID_RANK = 2
#: 5.2.3: the two points the centres of the fixture's end faces occupy.
_END_FACE_POSITIONS = 2
_MINIMUM_ROWS_FOR_SPREAD = 2


def _at_most(values: np.ndarray, bound: np.ndarray | float) -> np.ndarray:
    """Per element, whether ``values`` is at or below ``bound``.

    :param values: The values, in dB.
    :param bound: The bound, a number or one per value, in dB.
    :return: A boolean array; a NaN never qualifies.
    """
    return np.asarray(values <= np.asarray(bound) + _BOUNDARY_SLACK_DB, dtype=bool)


def _level_grid(values: ArrayLike, name: str) -> np.ndarray:
    """Levels as a ``(repetitions, bands)`` grid of finite values.

    :param values: One spectrum, or one per repetition.
    :param name: The argument name, for the error message.
    :return: A two-dimensional float array of its own.
    :raises ValueError: for another shape or a value that is not finite.
    """
    grid = np.array(values, dtype=np.float64)
    if grid.ndim == 1:
        grid = grid[None, :]
    if (
        grid.ndim != _GRID_RANK
        or grid.shape[0] == 0
        or grid.shape[1] == 0
        or not np.all(np.isfinite(grid))
    ):
        msg = (
            f"'{name}' must be one spectrum or a (repetitions, bands) grid of "
            "finite levels, in dB."
        )
        raise ValueError(msg)
    return grid


def _band_axis(frequencies: ArrayLike | None, count: int, owner: str) -> np.ndarray:
    """The centre frequencies, defaulted to the 22 bands of 5.3.

    :param frequencies: The caller's frequencies, or ``None``.
    :param count: How many bands the data carries.
    :param owner: The function name, for the error message.
    :return: A float array of its own.
    :raises ValueError: if the count does not match or the frequencies are not
        positive, finite and increasing.
    """
    if frequencies is None:
        if count != len(EARMUFF_TEST_BANDS_HZ):
            msg = (
                f"{owner} needs 'frequencies' for {count} bands; without them it "
                "assumes the 22 one-third-octave bands of 63 Hz to 8 kHz."
            )
            raise ValueError(msg)
        return np.array(EARMUFF_TEST_BANDS_HZ, dtype=np.float64)
    freqs = np.array(frequencies, dtype=np.float64)
    if (
        freqs.ndim != 1
        or freqs.size != count
        or not np.all(np.isfinite(freqs))
        or np.any(freqs <= 0.0)
        or np.any(np.diff(freqs) <= 0.0)
    ):
        msg = (
            f"{owner}: 'frequencies' must be {count} positive, finite, "
            "increasing centre frequencies in hertz."
        )
        raise ValueError(msg)
    return freqs


@dataclass(frozen=True)
class InsertionLossUncertaintyBudget(RichDisplay):
    r"""The uncertainty budget of an insertion loss (Annex B, Table B.1).

    Five normal inputs with a sensitivity coefficient of 1 (B.3), so the
    combined standard uncertainty is their root sum of squares (Formula
    (B.2)) and the expanded one twice that (B.4).

    :ivar open_level_db: The standard uncertainty of :math:`L_\mathrm{open}`,
        the standard deviation of the mean of repeated measurements, in dB.
    :ivar occluded_level_db: That of :math:`L_\mathrm{occl}`, which also
        carries the refitting of the earmuff, in dB.
    :ivar fixture_db: :math:`\delta_1`, the fixture's departure from its
        specification, in dB.
    :ivar sound_field_db: :math:`\delta_2`, the field's departure from an
        ideal random-incidence field or plane wave, in dB.
    :ivar equipment_db: :math:`\delta_3`, the measuring equipment, in dB.
    """

    open_level_db: float
    occluded_level_db: float
    fixture_db: float
    sound_field_db: float
    equipment_db: float

    def __post_init__(self) -> None:
        """Refuse a component that is negative or not finite.

        :raises ValueError: for such a component.
        """
        for value in self.components_db:
            if not math.isfinite(value) or value < 0.0:
                msg = "every component must be finite and not negative, in dB."
                raise ValueError(msg)

    @property
    def labels(self) -> tuple[str, ...]:
        """The five input quantities of Table B.1, in its order.

        :return: Their symbols.
        """
        return ("L_open", "L_occl", "delta_1", "delta_2", "delta_3")

    @property
    def components_db(self) -> tuple[float, ...]:
        """The five standard uncertainties in the order of Table B.1, in dB.

        :return: The components.
        """
        return (
            float(self.open_level_db),
            float(self.occluded_level_db),
            float(self.fixture_db),
            float(self.sound_field_db),
            float(self.equipment_db),
        )

    @property
    def combined_db(self) -> float:
        r""":math:`u = \sqrt{\sum (c_i u_i)^2}` (Formula (B.2)), in dB.

        :return: The combined standard uncertainty, unrounded.
        """
        return math.hypot(*self.components_db)

    @property
    def expanded_db(self) -> float:
        """:math:`U = 2u` (B.4), in dB.

        :return: The expanded uncertainty, unrounded.
        """
        return _COVERAGE_FACTOR * self.combined_db

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the five contributions as bars, with the combined value.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the contribution bars.
        :return: The axes.
        """
        from .._plot.audiometry import plot_insertion_loss_uncertainty

        return plot_insertion_loss_uncertainty(self, ax=ax, language=language, **kwargs)


#: Table B.1: the typical budget, "generally valid for mid-range frequencies
#: and for ear-muff type protectors that are not especially sensitive to the
#: positioning on the ATF": :math:`u` = 1,3 dB and :math:`U` = 2,6 dB.
EARMUFF_INSERTION_LOSS_UNCERTAINTY = InsertionLossUncertaintyBudget(
    open_level_db=_OPEN_LEVEL_U_DB,
    occluded_level_db=_OCCLUDED_LEVEL_U_DB,
    fixture_db=0.3,
    sound_field_db=0.5,
    equipment_db=0.2,
)


@dataclass(frozen=True)
class EarmuffInsertionLossResult(OwnsArrays):
    r"""The insertion loss of an earmuff on the test fixture (5.4, Annex B).

    A screening quantity, not an attenuation at the ear: Clause 1 says the
    data are not to be quoted as the real-ear attenuation of the earmuff nor
    as the protection it provides, and nothing in the library feeds them to
    the ISO 4869-2 methods.

    :ivar insertion_loss_db: :math:`IL_f`, the mean open level less the mean
        occluded level per band, in dB, unrounded.
    :ivar repetition_insertion_loss_db: The mean open level less each fitting's
        occluded level, one row per repetition, in dB.
    :ivar open_levels_db: The levels without the earmuff, one row per
        measurement, in dB.
    :ivar occluded_levels_db: The levels with it, one row per fitting, in dB.
    :ivar open_uncertainty_db: The standard uncertainty of the mean open level
        per band, in dB: the standard deviation of the mean when at least two
        open measurements were given, else Table B.1's 0,5 dB.
    :ivar occluded_uncertainty_db: That of the mean occluded level, from at
        least two fittings, else Table B.1's 1,0 dB.
    :ivar fixture_uncertainty_db: :math:`u(\delta_1)`, in dB.
    :ivar sound_field_uncertainty_db: :math:`u(\delta_2)`, in dB.
    :ivar equipment_uncertainty_db: :math:`u(\delta_3)`, in dB.
    :ivar frequencies: The centre frequencies, in hertz.
    :ivar isolation_cup_levels_db: The level with the isolation cup in place
        of the earmuff per band, in dB, or ``None``.
    """

    insertion_loss_db: np.ndarray
    repetition_insertion_loss_db: np.ndarray
    open_levels_db: np.ndarray
    occluded_levels_db: np.ndarray
    open_uncertainty_db: np.ndarray
    occluded_uncertainty_db: np.ndarray
    fixture_uncertainty_db: float
    sound_field_uncertainty_db: float
    equipment_uncertainty_db: float
    frequencies: np.ndarray
    isolation_cup_levels_db: np.ndarray | None = None

    @property
    def repetitions(self) -> int:
        """The number of fittings measured.

        :return: The count of occluded measurements.
        """
        return int(self.occluded_levels_db.shape[0])

    @property
    def repetitions_sufficient(self) -> bool:
        """Whether at least three fittings were measured (5.4.3).

        Fewer are allowed when the device's repeatability is known, which is
        the tester's judgement.

        :return: ``True`` from three repetitions.
        """
        return self.repetitions >= _MINIMUM_REPETITIONS

    @property
    def reported_db(self) -> np.ndarray:
        """The insertion loss as Clause 6 reports it, to the nearest 0,1 dB.

        :return: One value per band, halves rounded upwards.
        """
        return round_half_up(self.insertion_loss_db, _REPORT_DECIMALS)

    @property
    def standard_uncertainty_db(self) -> np.ndarray:
        """The combined standard uncertainty per band (Formula (B.2)), in dB.

        :return: One value per band.
        """
        return np.asarray(
            np.sqrt(
                self.open_uncertainty_db**2
                + self.occluded_uncertainty_db**2
                + self.fixture_uncertainty_db**2
                + self.sound_field_uncertainty_db**2
                + self.equipment_uncertainty_db**2
            ),
            dtype=np.float64,
        )

    @property
    def expanded_uncertainty_db(self) -> np.ndarray:
        """The expanded uncertainty per band, :math:`U = 2u` (B.4), in dB.

        :return: One value per band.
        """
        return _COVERAGE_FACTOR * self.standard_uncertainty_db

    def budget(self, frequency: float) -> InsertionLossUncertaintyBudget:
        """The budget of Table B.1 for one band of this measurement.

        :param frequency: A centre frequency of the measurement, in hertz.
        :return: :class:`InsertionLossUncertaintyBudget`.
        :raises ValueError: for a frequency the measurement does not have.
        """
        matches = np.isclose(self.frequencies, float(frequency), rtol=1e-3, atol=0.0)
        if not matches.any():
            msg = f"{float(frequency):g} Hz is not a band of this measurement."
            raise ValueError(msg)
        k = int(np.argmax(matches))
        return InsertionLossUncertaintyBudget(
            open_level_db=float(self.open_uncertainty_db[k]),
            occluded_level_db=float(self.occluded_uncertainty_db[k]),
            fixture_db=self.fixture_uncertainty_db,
            sound_field_db=self.sound_field_uncertainty_db,
            equipment_db=self.equipment_uncertainty_db,
        )

    @property
    def floor_margin_db(self) -> np.ndarray | None:
        """The mean occluded level less the isolation cup's, per band, in dB.

        :return: The margin, or ``None`` when no cup levels were given.
        """
        if self.isolation_cup_levels_db is None:
            return None
        margin = self.occluded_levels_db.mean(axis=0) - self.isolation_cup_levels_db
        return np.asarray(margin, dtype=np.float64)

    @property
    def floor_adequate(self) -> np.ndarray | None:
        """Per band, whether the isolation cup reads 10 dB lower at least (5.3).

        :return: One boolean per band, or ``None`` without cup levels.
        """
        margin = self.floor_margin_db
        if margin is None:
            return None
        return np.asarray(margin >= _FLOOR_MARGIN_DB - _BOUNDARY_SLACK_DB, dtype=bool)

    @property
    def level_drift_db(self) -> np.ndarray:
        """How far the open level strayed from its first measurement, in dB.

        5.3 keeps the test signal within ±1 dB of the level set before the
        measurement; with one open measurement nothing can be seen and the
        drift reads 0.

        :return: The largest absolute departure per band.
        """
        return np.max(np.abs(self.open_levels_db - self.open_levels_db[0]), axis=0)

    @property
    def level_stable(self) -> np.ndarray:
        """Per band, whether the open level stayed within ±1 dB (5.3).

        :return: One boolean per band.
        """
        return _at_most(self.level_drift_db, _LEVEL_STABILITY_DB)

    @property
    def response_smooth(self) -> bool:
        """Whether adjacent bands of the open level differ by 5 dB at most (5.3).

        :return: ``True`` when the system's one-third-octave response has no
            step larger than 5 dB between neighbouring bands.
        """
        mean_open = self.open_levels_db.mean(axis=0)
        return bool(
            np.all(_at_most(np.abs(np.diff(mean_open)), _ADJACENT_BAND_STEP_DB))
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the insertion loss as Clause 6 asks, increasing downwards.

        The scale is IEC 60263's 50 dB per decade of frequency, which Clause 6
        asks of every graph, so given axes take that aspect too.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the insertion loss curve.
        :return: The axes.
        """
        from .._plot.audiometry import plot_earmuff_insertion_loss

        return plot_earmuff_insertion_loss(self, ax=ax, language=language, **kwargs)


def _level_uncertainty(grid: np.ndarray, typical_db: float) -> np.ndarray:
    r"""The standard uncertainty of a mean level, per band.

    :param grid: ``(repetitions, bands)`` levels.
    :param typical_db: Table B.1's value, used with a single repetition.
    :return: :math:`s/\sqrt{n}` per band, or the typical value.
    """
    rows = grid.shape[0]
    if rows < _MINIMUM_ROWS_FOR_SPREAD:
        return np.full(grid.shape[1], typical_db)
    return grid.std(axis=0, ddof=1) / math.sqrt(rows)


def earmuff_insertion_loss(
    open_levels_db: ArrayLike,
    occluded_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    isolation_cup_levels_db: ArrayLike | None = None,
    fixture_uncertainty_db: float = 0.3,
    sound_field_uncertainty_db: float = 0.5,
    equipment_uncertainty_db: float = 0.2,
) -> EarmuffInsertionLossResult:
    r"""The insertion loss of an earmuff on the acoustic test fixture (5.4).

    The level at the fixture's microphone is measured without the earmuff,
    the earmuff is seated on the fixture (5.4.1), and after about 30 s the
    level is measured again (5.4.2); the difference in each one-third-octave
    band is the insertion loss. With repeated fittings (5.4.3) it is the mean
    open level less the mean occluded level:

    .. math::

       IL_f = \overline{L}_{\mathrm{open},f} - \overline{L}_{\mathrm{occl},f}

    Annex B's uncertainty is evaluated band by band: the standard uncertainty
    of each mean level is the standard deviation of the mean of its repeated
    measurements (B.3), or Table B.1's typical 0,5 dB open and 1,0 dB occluded
    when fewer than two were given, and the three :math:`\delta` terms default
    to Table B.1's 0,3 dB, 0,5 dB and 0,2 dB.

    The result is an insertion loss on a fixture. It screens production and
    ageing and is not the real-ear attenuation ISO 4869-2 needs (Clause 1);
    use :func:`phonometry.hearing.real_ear_attenuation` for that.

    :param open_levels_db: The levels without the earmuff, one spectrum or a
        ``(repetitions, bands)`` grid, in dB.
    :param occluded_levels_db: The levels with it, one spectrum or one per
        fitting, in dB.
    :param frequencies: The centre frequencies, in hertz, or ``None`` for the
        22 bands of 63 Hz to 8 kHz (:data:`EARMUFF_TEST_BANDS_HZ`).
    :param isolation_cup_levels_db: The level with the isolation cup in place
        of the earmuff per band, in dB, to check that it reads at least 10 dB
        lower (5.3).
    :param fixture_uncertainty_db: :math:`u(\delta_1)`, in dB.
    :param sound_field_uncertainty_db: :math:`u(\delta_2)`, in dB.
    :param equipment_uncertainty_db: :math:`u(\delta_3)`, in dB.
    :return: :class:`EarmuffInsertionLossResult`.
    :raises ValueError: for levels that are not finite, grids of different
        bands, cup levels that do not match, frequencies that do not fit, or an
        uncertainty that is negative or not finite.
    """
    open_grid = _level_grid(open_levels_db, "open_levels_db")
    occluded = _level_grid(occluded_levels_db, "occluded_levels_db")
    count = open_grid.shape[1]
    if occluded.shape[1] != count:
        msg = (
            "'open_levels_db' and 'occluded_levels_db' must share their bands; "
            f"got {count} and {occluded.shape[1]}."
        )
        raise ValueError(msg)
    freqs = _band_axis(frequencies, count, "earmuff_insertion_loss")
    cup = None
    if isolation_cup_levels_db is not None:
        cup = np.array(isolation_cup_levels_db, dtype=np.float64)
        if cup.shape != (count,) or not np.all(np.isfinite(cup)):
            msg = (
                "'isolation_cup_levels_db' must hold one finite level per band, "
                f"{count} values."
            )
            raise ValueError(msg)
    deltas = (
        fixture_uncertainty_db,
        sound_field_uncertainty_db,
        equipment_uncertainty_db,
    )
    if any(not math.isfinite(float(d)) or float(d) < 0.0 for d in deltas):
        msg = "the three delta uncertainties must be finite and not negative, in dB."
        raise ValueError(msg)
    mean_open = open_grid.mean(axis=0)
    return EarmuffInsertionLossResult(
        insertion_loss_db=mean_open - occluded.mean(axis=0),
        repetition_insertion_loss_db=mean_open[None, :] - occluded,
        open_levels_db=open_grid,
        occluded_levels_db=occluded,
        open_uncertainty_db=_level_uncertainty(open_grid, _OPEN_LEVEL_U_DB),
        occluded_uncertainty_db=_level_uncertainty(occluded, _OCCLUDED_LEVEL_U_DB),
        fixture_uncertainty_db=float(fixture_uncertainty_db),
        sound_field_uncertainty_db=float(sound_field_uncertainty_db),
        equipment_uncertainty_db=float(equipment_uncertainty_db),
        frequencies=freqs,
        isolation_cup_levels_db=cup,
    )


def check_random_incidence_field(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    directional_levels_db: ArrayLike | None = None,
    front_to_random_index_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> DiffuseSoundFieldCheck:
    """Is the random-incidence field of the test site good enough? (5.2.2).

    With the fixture removed, the level read by an omnidirectional microphone
    kept in one orientation at six positions 150 mm from the reference point,
    on the front-back, right-left and up-down axes, stays within ±2,5 dB of
    the level at the reference point, and the right and left positions within
    3 dB of each other; from the 500 Hz band up, the levels a directional
    microphone reads at the reference point in any two directions, the
    directions of the extremes among them, stay within the variation Table 1
    allows for its front-to-random sensitivity index
    (:data:`RANDOM_INCIDENCE_VARIATION_LIMITS`).

    This is the diffuse-field judgement of ISO 8253-2:2009, 5.3, with this
    standard's Table 1, and it returns the same
    :class:`~phonometry.hearing.DiffuseSoundFieldCheck`. The fixture itself
    may be the directional microphone in the bands where its index
    (:data:`ATF_FRONT_TO_RANDOM_INDEX_DB`) reaches 4 dB; pass the index band
    by band, NaN where it has none, and the bands it cannot judge are left
    unjudged.

    :param position_levels_db: The level at each position per band, in dB,
        keyed ``"front"``, ``"back"``, ``"left"``, ``"right"``, ``"up"`` and
        ``"down"``.
    :param reference_levels_db: The level at the reference point per band, in
        dB.
    :param directional_levels_db: The directional microphone's readings at the
        reference point, a ``(directions, bands)`` grid in dB; bands below
        500 Hz are not read and may be NaN. ``None`` leaves the directional
        test unjudged, and the verdict then does not pass.
    :param front_to_random_index_db: The directional microphone's
        front-to-random sensitivity index, in dB, one number or one per band;
        required with ``directional_levels_db``.
    :param frequencies: The centre frequencies, in hertz, or ``None`` for the
        22 bands of 63 Hz to 8 kHz.
    :return: :class:`~phonometry.hearing.DiffuseSoundFieldCheck`.
    :raises ValueError: if a position is missing or unknown, if the bands do
        not match, if a reading is given without its index or the other way
        round, if a single index is below 4 dB, or if a band from 500 Hz up has
        fewer than two finite readings.
    """
    return _diffuse_field_check(
        position_levels_db,
        reference_levels_db,
        directional_levels_db=directional_levels_db,
        front_to_random_index_db=front_to_random_index_db,
        frequencies=frequencies,
        default_frequencies=EARMUFF_TEST_BANDS_HZ,
        standard=_RANDOM_INCIDENCE_CLAUSE,
        owner="check_random_incidence_field",
    )


@dataclass(frozen=True)
class PlaneProgressiveWaveCheck(OwnsArrays):
    """Whether the plane progressive wave of the test site is good enough (5.2.3).

    :ivar frequencies: The centre frequencies, in hertz.
    :ivar end_face_difference_db: The difference between the levels at the
        two points the centres of the fixture's end faces occupy, as an
        absolute value per band, in dB.
    :ivar front_to_back_db: From 500 Hz up, the level a directional microphone
        at the reference point reads facing the source less the level facing
        away from it, per band, in dB; NaN below 500 Hz or where not measured.
    :ivar front_to_rear_index_db: The microphone's front-to-rear sensitivity
        index per band, in dB, NaN where not given.
    """

    frequencies: np.ndarray
    end_face_difference_db: np.ndarray
    front_to_back_db: np.ndarray
    front_to_rear_index_db: np.ndarray

    @property
    def end_faces_matched(self) -> np.ndarray:
        """Per band, whether the two end-face positions are within 2 dB.

        :return: One boolean per band.
        """
        return _at_most(self.end_face_difference_db, _END_FACE_TOLERANCE_DB)

    @property
    def directional_required(self) -> np.ndarray:
        """Per band, whether the directional test applies (500 Hz and up).

        :return: One boolean per band.
        """
        return np.asarray(self.frequencies >= _DIRECTIONAL_FROM_HZ, dtype=bool)

    @property
    def microphone_suitable(self) -> np.ndarray:
        """Per band, whether the microphone's front-to-rear index exceeds 15 dB.

        :return: One boolean per band; ``False`` where no index was given.
        """
        return np.asarray(self.front_to_rear_index_db > _FRONT_TO_REAR_INDEX_DB)

    @property
    def progressive(self) -> np.ndarray:
        """Per band, whether facing the source reads at least 10 dB more.

        Bands below 500 Hz count as meeting it; a band from 500 Hz up without
        a suitable microphone's reading reads ``False``.

        :return: One boolean per band.
        """
        margin = self.front_to_back_db >= _FRONT_TO_BACK_MINIMUM_DB - _BOUNDARY_SLACK_DB
        judged = margin & self.microphone_suitable
        return np.asarray(~self.directional_required | judged, dtype=bool)

    @property
    def directionality_judged(self) -> bool:
        """Whether every band from 500 Hz up was read with a suitable microphone.

        :return: ``True`` when none is left unjudged.
        """
        read = np.isfinite(self.front_to_back_db) & self.microphone_suitable
        return bool(np.all(~self.directional_required | read))

    @property
    def passes(self) -> bool:
        """Whether the plane wave qualifies, every requirement judged.

        :return: ``True`` when every band meets both conditions.
        """
        return bool(np.all(self.end_faces_matched) and np.all(self.progressive))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a PlaneProgressiveWaveCheck has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw both conditions against their limits, band by band.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the end-face difference curve.
        :return: The axes.
        """
        from .._plot.audiometry import plot_plane_progressive_wave

        return plot_plane_progressive_wave(self, ax=ax, language=language, **kwargs)


def check_plane_progressive_wave(
    end_face_levels_db: ArrayLike,
    *,
    facing_levels_db: ArrayLike | None = None,
    facing_away_levels_db: ArrayLike | None = None,
    front_to_rear_index_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> PlaneProgressiveWaveCheck:
    """Is the plane progressive wave of the test site good enough? (5.2.3).

    With the fixture removed:

    - the levels at the two points the centres of the fixture's end faces
      normally occupy, each read at 0° incidence, differ by 2 dB at most;
    - from the 500 Hz band up, a directional microphone at the reference point
      reads at least 10 dB more facing the source than turned 180° away from
      it, the microphone having a front-to-rear sensitivity index greater
      than 15 dB (different microphones may serve different bands).

    During the insertion loss measurement the fixture is turned so that the
    wave meets its end faces at grazing incidence; that is its orientation,
    not a condition judged here.

    :param end_face_levels_db: The levels at the two end-face points, a
        ``(2, bands)`` grid in dB.
    :param facing_levels_db: The directional microphone's level facing the
        source per band, in dB; bands below 500 Hz may be NaN.
    :param facing_away_levels_db: Its level facing away, per band, in dB.
    :param front_to_rear_index_db: The microphone's front-to-rear sensitivity
        index, one number or one per band, in dB.
    :param frequencies: The centre frequencies, in hertz, or ``None`` for the
        22 bands of 63 Hz to 8 kHz.
    :return: :class:`PlaneProgressiveWaveCheck`. Without the directional
        readings the directional test is not judged and the verdict does not
        pass.
    :raises ValueError: for an end-face grid that is not two rows of finite
        levels, directional readings given in part, or arrays that do not
        match.
    """
    faces = np.array(end_face_levels_db, dtype=np.float64)
    if (
        faces.ndim != _GRID_RANK
        or faces.shape[0] != _END_FACE_POSITIONS
        or not np.all(np.isfinite(faces))
    ):
        msg = "'end_face_levels_db' must be a (2, bands) grid of finite levels, in dB."
        raise ValueError(msg)
    count = faces.shape[1]
    freqs = _band_axis(frequencies, count, "check_plane_progressive_wave")
    directional = (facing_levels_db, facing_away_levels_db, front_to_rear_index_db)
    front_to_back = np.full(count, np.nan)
    index = np.full(count, np.nan)
    if any(value is not None for value in directional):
        if any(value is None for value in directional):
            msg = (
                "give 'facing_levels_db', 'facing_away_levels_db' and "
                "'front_to_rear_index_db' together."
            )
            raise ValueError(msg)
        facing = np.array(facing_levels_db, dtype=np.float64)
        away = np.array(facing_away_levels_db, dtype=np.float64)
        given_index = np.array(front_to_rear_index_db, dtype=np.float64)
        if given_index.ndim == 0:
            given_index = np.full(count, float(given_index))
        if (
            facing.shape != (count,)
            or away.shape != (count,)
            or given_index.shape != (count,)
        ):
            msg = f"the directional readings and index must give one value per band, {count}."
            raise ValueError(msg)
        required = freqs >= _DIRECTIONAL_FROM_HZ
        if not np.all(np.isfinite(facing[required]) & np.isfinite(away[required])):
            msg = (
                "the directional readings must be finite in every band from 500 Hz up."
            )
            raise ValueError(msg)
        front_to_back = np.where(required, facing - away, np.nan)
        index = given_index
    return PlaneProgressiveWaveCheck(
        frequencies=freqs,
        end_face_difference_db=np.abs(faces[0] - faces[1]),
        front_to_back_db=front_to_back,
        front_to_rear_index_db=index,
    )


def _isolation_requirement(frequencies: np.ndarray) -> np.ndarray:
    """The least acoustic isolation of 5.1.4 per band, NaN below 63 Hz.

    :param frequencies: The centre frequencies, in hertz.
    :return: The requirement per band, in dB.
    """
    return np.select(
        [
            frequencies < _ISOLATION_FROM_SPLIT_HZ,
            frequencies < _ISOLATION_LOW_SPLIT_HZ,
            frequencies < _ISOLATION_HIGH_SPLIT_HZ,
        ],
        [np.nan, _ISOLATION_LOW_DB, _ISOLATION_MID_DB],
        default=_ISOLATION_HIGH_DB,
    )


@dataclass(frozen=True)
class FixtureIsolationCheck(OwnsArrays):
    """Whether the test fixture isolates its microphone well enough (5.1.4).

    The requirement is the clause's, read from the bands as
    :attr:`required_db`, so a check cannot be built against another one.

    :ivar frequencies: The centre frequencies, in hertz.
    :ivar isolation_db: The acoustic isolation (3.7), the level with the
        isolation cup absent less the level with it sealed on, per band, in
        dB.
    """

    frequencies: np.ndarray
    isolation_db: np.ndarray

    def __post_init__(self) -> None:
        """Reject a check whose isolation does not follow its bands.

        :raises ValueError: if the isolation does not hold one value per band.
        """
        if np.asarray(self.isolation_db).shape != np.asarray(self.frequencies).shape:
            msg = "FixtureIsolationCheck: 'isolation_db' must hold one value per band."
            raise ValueError(msg)

    @property
    def required_db(self) -> np.ndarray:
        """The least isolation 5.1.4 asks per band, in dB.

        :return: 50 dB from 63 Hz to 250 Hz, 65 dB from 315 Hz to 4 kHz and
            55 dB above; NaN below 63 Hz, where it asks nothing.
        """
        return _isolation_requirement(np.asarray(self.frequencies, dtype=np.float64))

    @property
    def sufficient(self) -> np.ndarray:
        """Per band, whether the isolation reaches the requirement.

        :return: One boolean per band; ``True`` where nothing is required.
        """
        reached = self.isolation_db >= self.required_db - _BOUNDARY_SLACK_DB
        return np.asarray(np.isnan(self.required_db) | reached, dtype=bool)

    @property
    def margin_db(self) -> np.ndarray:
        """The isolation less the requirement per band, in dB.

        :return: Negative where the fixture falls short, NaN where nothing is
            required.
        """
        return np.asarray(self.isolation_db - self.required_db, dtype=np.float64)

    @property
    def passes(self) -> bool:
        """Whether the fixture's isolation meets 5.1.4 in every band.

        :return: ``True`` when no band falls short.
        """
        return bool(np.all(self.sufficient))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a FixtureIsolationCheck has no truth value; read its '.passes' for "
            "the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the isolation against the requirement, band by band.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the isolation curve.
        :return: The axes.
        """
        from .._plot.audiometry import plot_fixture_isolation

        return plot_fixture_isolation(self, ax=ax, language=language, **kwargs)


def verify_fixture_isolation(
    open_levels_db: ArrayLike,
    cup_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> FixtureIsolationCheck:
    """Does the test fixture isolate its microphone well enough? (5.1.4).

    With the test signal of 5.3 at the actual test site, the microphone is
    covered by an acoustic isolation test cup sealed to the fixture, and the
    acoustic isolation (3.7) is the level without the cup less the level with
    it. 5.1.4 asks for at least 50 dB in the bands centred from 63 Hz to
    250 Hz, 65 dB from 315 Hz to 4 kHz, and 55 dB above. Airborne and
    structure-borne paths both count, which is why the fixture sits on a
    resilient mounting (5.1.2).

    :param open_levels_db: The level at the microphone without the cup, per
        band, in dB.
    :param cup_levels_db: The level with the cup sealed on, per band, in dB.
    :param frequencies: The centre frequencies, in hertz, or ``None`` for the
        22 bands of 63 Hz to 8 kHz.
    :return: :class:`FixtureIsolationCheck`.
    :raises ValueError: for levels that are not finite or do not match the
        bands.
    """
    open_levels = _level_grid(open_levels_db, "open_levels_db")
    cup = _level_grid(cup_levels_db, "cup_levels_db")
    if open_levels.shape[0] != 1 or cup.shape != open_levels.shape:
        msg = "'open_levels_db' and 'cup_levels_db' must be one spectrum each on the same bands."
        raise ValueError(msg)
    freqs = _band_axis(frequencies, open_levels.shape[1], "verify_fixture_isolation")
    return FixtureIsolationCheck(
        frequencies=freqs,
        isolation_db=open_levels[0] - cup[0],
    )
