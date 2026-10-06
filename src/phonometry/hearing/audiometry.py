#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Pure-tone audiometry: the test room, the threshold rules and their uncertainty (ISO 8253-1:2010).

ISO 8253-1 sets out how a hearing threshold level is measured with earphones
or a bone vibrator. Three parts of it are arithmetic, and this module carries
them; the rest (preparing and instructing the subject, placing the
transducers, masking, calibrating the audiometer) is procedure a tester
follows.

**The test room (Clause 11).** The ambient noise must not mask the lowest
test tone. Tables 2 and 4 give the maximum permissible ambient sound pressure
levels :math:`L_{S,\mathrm{max}}` in one-third-octave bands from 31,5 Hz to
8 kHz, for air conduction with typical supra-aural earphones and for bone
conduction, each for the lowest test frequency of the audiometry: 125 Hz,
250 Hz or, for air conduction, 500 Hz. They hold for hearing threshold levels
down to 0 dB with at most +2 dB of threshold shift from the noise; the NOTEs
allow 8 dB more for +5 dB, and 11.1 adds the lowest hearing threshold level
to be measured when it is not 0 dB. An earphone that excludes more noise than
the supra-aural one allows a louder room: 11.1 adds the difference between
its attenuation and the supra-aural one of Table 3,

.. math::

   L_{S,\mathrm{max}}' = L_{S,\mathrm{max}} + \left(A_\mathrm{earphone}
   - A_\mathrm{supra\text{-}aural}\right) + L_\mathrm{HT,min}

and Table 3 prints it for an insert (Etymotic ER-3A) and a circumaural
(Sennheiser HDA 200) earphone. :func:`ambient_noise_limits` returns the
limits and :func:`check_audiometric_ambient_noise` judges a measured
spectrum against them, including the sound-field limits of ISO 8253-2:2009
Table 2 (:data:`phonometry.hearing.SOUND_FIELD_AMBIENT_LIMITS_DB`).

**The threshold (6.2.4, 6.3.5, 7.5).** Each audiometric method ends in a rule
that turns the subject's responses into a hearing threshold level:

- the **ascending method** (6.2.3.2, 6.2.4.2) presents tones in 5 dB steps
  upwards until a response, drops 10 dB after each response, and stops when
  three responses fall at one level within at most five ascents (two out of
  three in the shortened version). The threshold is the lowest level at which
  responses occur in more than half of the ascents
  (:func:`ascending_method_threshold`, which also replays a presentation
  sequence and gives the next level to present);
- the **bracketing method** (6.2.4.3) averages the lowest response levels of
  the ascents, and those of the descents, and rounds the mean of the two
  averages to the nearest 5 dB step (:func:`bracketing_method_threshold`);
- **automatic recording** audiometry (6.3.5) averages the peaks and the
  valleys of the tracing, after dropping the first reversal and those of
  excursions of 3 dB or less, and rounds the mean of the two up to the next
  whole decibel (:func:`automatic_audiometry_threshold`);
- **sweep-frequency** audiometry (7.5) averages the three peaks and the three
  valleys closest to a frequency, or runs that average along the tracing
  (:func:`sweep_audiometry_threshold`).

Each also carries the text's own reliability test: a span of more than 10 dB
between the levels it averages.

**The cautions (6.2.3.2, 8.4).** Three more rules of the text judge the
levels once they are found. Step 3 of 6.2.3.2 repeats the measurement at
1 kHz, and the first ear is done when the two agree to 5 dB or less
(:func:`check_retest_agreement`). A hearing level of 40 dB or more calls for
caution because of cross-hearing (6.2.3.2), and a bone-conduction level at the
average vibrotactile threshold of 8.4 may be felt rather than heard
(:data:`VIBROTACTILE_HEARING_LEVELS_DB`); :func:`audiogram_cautions` flags
both.

**The uncertainty (Annex A).** The hearing threshold level is modelled as the
determined value plus seven zero-mean input quantities (Formula (A.1)), all
uncorrelated with a sensitivity coefficient of 1, so the combined standard
uncertainty is their root sum of squares (Formula (A.2)) and the expanded
one twice that:

.. math::

   u = \sqrt{\sum_{i=1}^{8} u_i^2}, \qquad U = 2u

A.3 gives typical values for the repeatability, the audiometer, the
transducer, the ambient noise and the masking;
:func:`audiometric_uncertainty` assembles them into an
:class:`AudiometricUncertaintyBudget`, and for air conduction below 4 kHz
without masking it reproduces the example of Table A.2: :math:`u` = 4,9 dB and
:math:`U` = 10 dB.

Clause, table and formula numbers refer to ISO 8253-1:2010(E).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.boundary import round_half_up, settled
from .._internal.frozen import read_only
from .sound_field_audiometry import (
    SOUND_FIELD_AMBIENT_BANDS_HZ as _SOUND_FIELD_BANDS_HZ,
)
from .sound_field_audiometry import (
    SOUND_FIELD_AMBIENT_LIMITS_DB as _SOUND_FIELD_LIMITS_DB,
)
from .threshold import AUDIOMETRIC_FREQUENCIES as _AUDIOMETRIC_FREQUENCIES

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "AIR_CONDUCTION_AMBIENT_LIMITS_DB",
    "AMBIENT_NOISE_BANDS_HZ",
    "BONE_CONDUCTION_AMBIENT_LIMITS_DB",
    "EARPHONE_ATTENUATION_DB",
    "VIBROTACTILE_HEARING_LEVELS_DB",
    "AmbientNoiseCheck",
    "AscendingThresholdResult",
    "AudiogramCautions",
    "AudiometricUncertaintyBudget",
    "AutomaticThresholdResult",
    "BracketingThresholdResult",
    "RetestAgreementCheck",
    "SweepThresholdResult",
    "ambient_noise_limits",
    "ascending_method_threshold",
    "audiogram_cautions",
    "audiometric_uncertainty",
    "automatic_audiometry_threshold",
    "bracketing_method_threshold",
    "check_audiometric_ambient_noise",
    "check_retest_agreement",
    "sweep_audiometry_threshold",
]

#: The one-third-octave mid-frequencies of Tables 2 to 4, in hertz: 31,5 Hz
#: to 8 kHz.
AMBIENT_NOISE_BANDS_HZ: tuple[float, ...] = _SOUND_FIELD_BANDS_HZ[:-2]

#: Table 2: the maximum permissible ambient sound pressure levels
#: :math:`L_{S,\mathrm{max}}` for air conduction audiometry with typical
#: supra-aural earphones, in dB re 20 µPa, one per band of
#: :data:`AMBIENT_NOISE_BANDS_HZ`, keyed by the lowest test tone frequency in
#: hertz (125, 250 or 500). They hold for hearing threshold levels down to
#: 0 dB with at most +2 dB of threshold shift from the ambient noise.
AIR_CONDUCTION_AMBIENT_LIMITS_DB: Mapping[float, np.ndarray] = MappingProxyType(
    {
        125.0: read_only(
            np.array(
                [56, 52, 47, 42, 38, 33, 28, 23, 20, 19, 18, 18, 18, 18, 20, 23]
                + [25, 27, 30, 32, 34, 36, 35, 34, 33],
                dtype=np.float64,
            )
        ),
        250.0: read_only(
            np.array(
                [66, 62, 57, 52, 48, 43, 39, 30, 20, 19, 18, 18, 18, 18, 20, 23]
                + [25, 27, 30, 32, 34, 36, 35, 34, 33],
                dtype=np.float64,
            )
        ),
        500.0: read_only(
            np.array(
                [78, 73, 68, 64, 59, 55, 51, 47, 42, 37, 33, 24, 18, 18, 20, 23]
                + [25, 27, 30, 32, 34, 36, 35, 34, 33],
                dtype=np.float64,
            )
        ),
    }
)

#: Table 4: the maximum permissible ambient sound pressure levels
#: :math:`L_{S,\mathrm{max}}` for bone conduction audiometry, in dB re 20 µPa,
#: one per band of :data:`AMBIENT_NOISE_BANDS_HZ`, keyed by the lowest test
#: tone frequency in hertz (125 or 250). The ears are open, so no earphone
#: shelters them, and NOTE 2 warns that levels below 5 dB are hard to measure
#: with most sound level meters.
BONE_CONDUCTION_AMBIENT_LIMITS_DB: Mapping[float, np.ndarray] = MappingProxyType(
    {
        125.0: read_only(
            np.array(
                [55, 47, 41, 35, 30, 25, 20, 17, 15, 13, 11, 9, 8, 8, 7, 7, 7, 8]
                + [8, 6, 4, 2, 4, 9, 15],
                dtype=np.float64,
            )
        ),
        250.0: read_only(
            np.array(
                [63, 56, 49, 44, 39, 35, 28, 21, 15, 13, 11, 9, 8, 8, 7, 7, 7, 8]
                + [8, 6, 4, 2, 4, 9, 15],
                dtype=np.float64,
            )
        ),
    }
)

#: Table 3: the average sound attenuation of three earphones, in dB, one per
#: band of :data:`AMBIENT_NOISE_BANDS_HZ`: ``"supra-aural"`` (typical current
#: supra-aural earphones, the ones Table 2 assumes), ``"ER-3A"`` (the Etymotic
#: insert earphone) and ``"HDA 200"`` (the Sennheiser circumaural one). The
#: HDA 200 column prints no value below 63 Hz, which is NaN here.
EARPHONE_ATTENUATION_DB: Mapping[str, np.ndarray] = MappingProxyType(
    {
        "supra-aural": read_only(
            np.array(
                [0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 5, 6, 7, 9, 11, 15, 18, 21, 26, 28]
                + [31, 32, 29, 26, 24],
                dtype=np.float64,
            )
        ),
        "ER-3A": read_only(
            np.array(
                [33, 33, 33, 33, 33, 33, 33, 34, 35, 36, 37, 37, 38, 37, 37, 37]
                + [35, 34, 33, 35, 37, 40, 41, 42, 43],
                dtype=np.float64,
            )
        ),
        "HDA 200": read_only(
            np.array(
                [math.nan, math.nan, math.nan, 17, 16, 15, 15, 15, 16, 16, 18, 20]
                + [23, 25, 27, 29, 30, 31, 32, 37, 41, 46, 45, 45, 44],
                dtype=np.float64,
            )
        ),
    }
)

#: 8.4: the hearing level at which the vibrotactile threshold lies on average
#: for a bone vibrator on the mastoid, in dB, keyed by the frequency in hertz
#: (250 Hz, 500 Hz and 1 kHz, the only ones the text gives). Its NOTE puts
#: them about 10 dB lower for an audiometer calibrated for forehead placement,
#: and the text warns that individuals vary widely about them.
VIBROTACTILE_HEARING_LEVELS_DB: Mapping[float, float] = MappingProxyType(
    {250.0: 40.0, 500.0: 60.0, 1000.0: 70.0}
)

_PRESENTATIONS: tuple[str, ...] = ("air", "bone", "sound field")
_CONDUCTIONS: tuple[str, ...] = ("air", "bone")
#: The NOTEs to Tables 2 and 4 and footnote a to ISO 8253-2 Table 2: the two
#: threshold shifts the limits are written for, and what the larger one adds.
_BASE_THRESHOLD_SHIFT_DB = 2.0
_RELAXED_THRESHOLD_SHIFT_DB = 5.0
_RELAXED_ALLOWANCE_DB = 8.0
#: 11.1: the measuring chain's noise floor sits at least this far below the
#: level it measures.
_NOISE_FLOOR_MARGIN_DB = 6.0
#: A limit reached through floating-point arithmetic is on the limit.
_BOUNDARY_SLACK_DB = 1e-9
#: Relative tolerance for matching a frequency to a tabulated one.
_FREQUENCY_RTOL = 1e-3
#: Tolerance for comparing two levels a tester set on the attenuator.
_LEVEL_ATOL_DB = 1e-6

#: 6.2.3.2 Step 2: the steps of the ascending method.
_ASCENT_STEP_DB = 5.0
_DESCENT_STEP_DB = 10.0
#: 6.2.3.2 Step 1: the first tone sits this far below the lowest familiarization
#: response.
_FIRST_TONE_BELOW_DB = 10.0
#: 6.2.3.2 Step 2: after a series without a threshold, the next one starts this
#: far above the last response.
_RESTART_ABOVE_DB = 10.0
#: 6.2.3.2 Step 2: the full and the shortened ascending method, as (responses
#: needed at one level, most ascents in a series).
_ASCENDING_FULL = (3, 5)
_ASCENDING_SHORT = (2, 3)
#: 6.2.4.2, 6.2.4.3, 6.3.5 and 7.5 NOTE 1: a spread of more than this makes a
#: determination doubtful.
_SPREAD_LIMIT_DB = 10.0
#: 6.2.4.3: the bracketing threshold is rounded to this step.
_BRACKETING_STEP_DB = 5.0
#: 6.2.3.2: the shortened bracketing method needs two ascents and two descents
#: whose four levels lie within this.
_SHORT_BRACKETING_SPREAD_DB = 5.0
_BRACKETING_FULL_COUNT = 3
_BRACKETING_SHORT_COUNT = 2
#: 6.3.5 a): reversals of an excursion this small are ignored.
_SMALL_EXCURSION_DB = 3.0
#: 6.3.5: fewer reversals than this left after a) make a tracing doubtful.
_MINIMUM_REVERSALS = 6
#: 7.5: the peaks and the valleys averaged at one frequency.
_SWEEP_REVERSALS_PER_SIDE = 3
#: 6.2.3.2 Step 3: the repeat at 1 kHz agrees with the first measurement to
#: this, and a change of this much sends the test back to further frequencies.
_RETEST_AGREEMENT_DB = 5.0
_RETEST_DISAGREEMENT_DB = 10.0
#: 6.2.3.2: a hearing level of this much or more calls for caution because of
#: cross-hearing.
_CROSS_HEARING_LEVEL_DB = 40.0
#: 8.4 NOTE: the vibrotactile levels for forehead placement lie this much lower.
_FOREHEAD_OFFSET_DB = 10.0
_PLACEMENTS: tuple[str, ...] = ("mastoid", "forehead")

#: Annex A: where "up to 4 kHz" ends.
_UNCERTAINTY_SPLIT_HZ = 4000.0
#: A.3.2: the standard uncertainty of repeated determinations, by conduction
#: and by whether the frequency is above 4 kHz.
_REPEATABILITY_DB = MappingProxyType({"air": (2.5, 4.0), "bone": (3.0, 5.0)})
#: A.3.3: the maximum deviation of the audiometer's output, likewise.
_EQUIPMENT_DEVIATION_DB = MappingProxyType({"air": (3.0, 5.0), "bone": (4.0, 5.0)})
#: A.3.4: the two transducer components, up to and above 4 kHz.
_TRANSDUCER_TYPE_DB = (1.5, 2.5)
_TRANSDUCER_FITTING_DB = (2.5, 3.0)
#: A.3.5 and A.3.6: ambient noise with Clause 11 met, and masking noise.
_ENVIRONMENT_DB = 2.0
_MASKING_DB = 2.0
#: A.5: the coverage factor for 95 % and a normal distribution.
_COVERAGE_FACTOR = 2.0


def _at_most(values: np.ndarray, bound: np.ndarray | float) -> np.ndarray:
    """Per element, whether ``values`` is at or below ``bound``.

    :param values: The values, in dB.
    :param bound: The bound, a number or one per value, in dB.
    :return: A boolean array; a NaN never qualifies.
    """
    return np.asarray(values <= np.asarray(bound) + _BOUNDARY_SLACK_DB, dtype=bool)


def _at_least(values: np.ndarray, bound: np.ndarray | float) -> np.ndarray:
    """Per element, whether ``values`` is at or above ``bound``.

    :param values: The values, in dB.
    :param bound: The bound, a number or one per value, in dB.
    :return: A boolean array; a NaN never qualifies.
    """
    return np.asarray(values >= np.asarray(bound) - _BOUNDARY_SLACK_DB, dtype=bool)


def _levels(values: ArrayLike, name: str, *, minimum: int = 1) -> np.ndarray:
    """A one-dimensional array of finite levels, in dB.

    :param values: The levels.
    :param name: The argument name, for the error message.
    :param minimum: How many values it needs at least.
    :return: The levels as a float array of its own.
    :raises ValueError: for another shape, too few values or a value that is
        not finite.
    """
    array = np.array(values, dtype=np.float64)
    if array.ndim != 1 or array.size < minimum or not np.all(np.isfinite(array)):
        msg = (
            f"'{name}' must be a one-dimensional array of at least {minimum} "
            "finite levels, in dB."
        )
        raise ValueError(msg)
    return array


def _round_half_up(value: float, step: float) -> float:
    """``value`` rounded to the nearest multiple of ``step``, halves upwards.

    :param value: The value.
    :param step: The step.
    :return: The rounded value.
    """
    return step * float(round_half_up(value / step))


# ---------------------------------------------------------------------------
# The test room (Clause 11)
# ---------------------------------------------------------------------------


def _table_for(
    presentation: str,
) -> tuple[Mapping[float, np.ndarray], tuple[float, ...]]:
    """The limit table and its band axis for a presentation.

    :param presentation: ``"air"``, ``"bone"`` or ``"sound field"``.
    :return: The table keyed by lowest test frequency, and its bands.
    :raises ValueError: for another presentation.
    """
    if presentation == "air":
        return AIR_CONDUCTION_AMBIENT_LIMITS_DB, AMBIENT_NOISE_BANDS_HZ
    if presentation == "bone":
        return BONE_CONDUCTION_AMBIENT_LIMITS_DB, AMBIENT_NOISE_BANDS_HZ
    if presentation == "sound field":
        return _SOUND_FIELD_LIMITS_DB, _SOUND_FIELD_BANDS_HZ
    msg = f"'presentation' must be one of {_PRESENTATIONS}; got {presentation!r}."
    raise ValueError(msg)


def _earphone_allowance(
    presentation: str, earphone: str, earphone_attenuation_db: ArrayLike | None
) -> np.ndarray:
    """What an earphone's extra attenuation adds to the limits of Table 2.

    :param presentation: The presentation.
    :param earphone: A column of Table 3.
    :param earphone_attenuation_db: Or the earphone's own attenuation per band.
    :return: The allowance per band of :data:`AMBIENT_NOISE_BANDS_HZ`, zero
        where Table 3 prints no value.
    :raises ValueError: for an earphone named with bone conduction or sound
        field, for both forms at once, for an unknown earphone, or for an
        attenuation of the wrong length.
    """
    supra_aural = EARPHONE_ATTENUATION_DB["supra-aural"]
    if presentation != "air":
        if earphone != "supra-aural" or earphone_attenuation_db is not None:
            msg = (
                "an earphone only changes the limits of air conduction "
                f"audiometry (ISO 8253-1 11.1), not of {presentation!r}."
            )
            raise ValueError(msg)
        return np.zeros(len(AMBIENT_NOISE_BANDS_HZ))
    if earphone_attenuation_db is not None:
        if earphone != "supra-aural":
            msg = "give either 'earphone' or 'earphone_attenuation_db', not both."
            raise ValueError(msg)
        attenuation = _levels(earphone_attenuation_db, "earphone_attenuation_db")
        if attenuation.size != supra_aural.size:
            msg = (
                "'earphone_attenuation_db' must hold one attenuation per band of "
                f"AMBIENT_NOISE_BANDS_HZ, {supra_aural.size} values."
            )
            raise ValueError(msg)
    elif earphone in EARPHONE_ATTENUATION_DB:
        attenuation = np.asarray(EARPHONE_ATTENUATION_DB[earphone], dtype=np.float64)
    else:
        msg = (
            f"'earphone' must be one of {tuple(EARPHONE_ATTENUATION_DB)}; got "
            f"{earphone!r}."
        )
        raise ValueError(msg)
    allowance = attenuation - supra_aural
    return np.where(np.isfinite(allowance), allowance, 0.0)


def ambient_noise_limits(
    presentation: str = "air",
    *,
    lowest_test_frequency_hz: float = 125.0,
    earphone: str = "supra-aural",
    earphone_attenuation_db: ArrayLike | None = None,
    lowest_hearing_level_db: float = 0.0,
    allowed_threshold_shift_db: float = 2.0,
) -> np.ndarray:
    r"""The maximum permissible ambient sound pressure levels of a test room.

    For air conduction (ISO 8253-1 Table 2), bone conduction (Table 4) or
    sound field audiometry (ISO 8253-2 Table 2), in one-third-octave bands:

    .. math::

       L_{S,\mathrm{max}}' = L_{S,\mathrm{max}}
       + \left(A_\mathrm{earphone} - A_\mathrm{supra\text{-}aural}\right)
       + L_\mathrm{HT,min} + \Delta

    with the earphone term of 11.1 for air conduction (Table 3), the lowest
    hearing threshold level :math:`L_\mathrm{HT,min}` to be measured (11.1 and
    ISO 8253-2 Clause 6), and :math:`\Delta` = 8 dB when a threshold shift of
    +5 dB from the ambient noise is accepted instead of +2 dB (NOTE to Table
    2, NOTE 1 to Table 4, footnote a to ISO 8253-2 Table 2). Where Table 3
    prints no attenuation, the HDA 200 below 63 Hz, no allowance is made:
    the supra-aural earphone attenuates nothing there, so none is the
    conservative reading.

    :param presentation: ``"air"`` (default), ``"bone"`` or ``"sound field"``.
    :param lowest_test_frequency_hz: The lowest test tone frequency: 125
        (default), 250, or for air conduction 500.
    :param earphone: A column of :data:`EARPHONE_ATTENUATION_DB`,
        ``"supra-aural"`` (default), ``"ER-3A"`` or ``"HDA 200"``; air
        conduction only.
    :param earphone_attenuation_db: Or the attenuation of another earphone,
        one per band of :data:`AMBIENT_NOISE_BANDS_HZ`, in dB; air conduction
        only.
    :param lowest_hearing_level_db: The lowest hearing threshold level to be
        measured, in dB; 0 by default.
    :param allowed_threshold_shift_db: The threshold shift accepted from the
        ambient noise, 2 (default) or 5, in dB.
    :return: The limits in dB re 20 µPa, one per band of
        :data:`AMBIENT_NOISE_BANDS_HZ` for air and bone conduction and of
        :data:`phonometry.hearing.SOUND_FIELD_AMBIENT_BANDS_HZ` for sound
        field.
    :raises ValueError: for an unknown presentation, lowest test frequency,
        earphone or threshold shift, or an earphone with bone conduction or
        sound field.
    """
    table, _bands = _table_for(presentation)
    lowest = float(lowest_test_frequency_hz)
    column = next(
        (values for key, values in table.items() if math.isclose(lowest, key)), None
    )
    if column is None:
        listed = ", ".join(f"{key:g}" for key in table)
        msg = (
            f"'lowest_test_frequency_hz' for {presentation!r} must be one of "
            f"{listed}; got {lowest:g}."
        )
        raise ValueError(msg)
    shift = float(allowed_threshold_shift_db)
    if math.isclose(shift, _BASE_THRESHOLD_SHIFT_DB):
        allowance = 0.0
    elif math.isclose(shift, _RELAXED_THRESHOLD_SHIFT_DB):
        allowance = _RELAXED_ALLOWANCE_DB
    else:
        msg = (
            "'allowed_threshold_shift_db' must be 2 or 5, the two threshold "
            f"shifts the tables are written for; got {shift:g}."
        )
        raise ValueError(msg)
    hearing_level = float(lowest_hearing_level_db)
    if not math.isfinite(hearing_level):
        msg = "'lowest_hearing_level_db' must be finite, in dB."
        raise ValueError(msg)
    limits = np.array(column, dtype=np.float64) + allowance + hearing_level
    earphone_allowance = _earphone_allowance(
        presentation, earphone, earphone_attenuation_db
    )
    limits[: earphone_allowance.size] += earphone_allowance
    return limits


def _table_rows(presentation: str, frequencies: np.ndarray) -> np.ndarray:
    """The row of the presentation's table each frequency is a band of.

    :param presentation: ``"air"``, ``"bone"`` or ``"sound field"``.
    :param frequencies: The mid-frequencies, in hertz.
    :return: One row index per frequency.
    :raises ValueError: for a frequency the table does not list, or bands
        that are not distinct and in increasing order.
    """
    table = np.asarray(_table_for(presentation)[1], dtype=np.float64)
    rows: list[int] = []
    for f in frequencies:
        matches = np.isclose(table, f, rtol=_FREQUENCY_RTOL, atol=0.0)
        if not matches.any():
            msg = (
                f"{f:g} Hz is not a band of the {presentation!r} table "
                f"({table[0]:g} Hz to {table[-1]:g} Hz)."
            )
            raise ValueError(msg)
        rows.append(int(np.argmax(matches)))
    indices = np.array(rows, dtype=np.int64)
    if np.any(np.diff(indices) <= 0):
        msg = "'frequencies' must be distinct bands in increasing order."
        raise ValueError(msg)
    return indices


@dataclass(frozen=True)
class AmbientNoiseCheck:
    """Whether a test room is quiet enough for the audiometry, band by band.

    The fields hold what was measured and what the standard lets the tester
    choose: the presentation, the lowest test frequency, the lowest hearing
    level to be measured, the earphone and the threshold shift accepted. The
    limits themselves (:attr:`limits_db`) are read from the tables with those
    choices, so a check cannot be built against another table.

    :ivar presentation: ``"air"``, ``"bone"`` or ``"sound field"``.
    :ivar frequencies: The one-third-octave mid-frequencies judged, in hertz,
        each one of :attr:`table_bands_hz`.
    :ivar levels_db: The measured ambient sound pressure level per band, in dB.
    :ivar lowest_test_frequency_hz: The lowest test tone frequency, in hertz.
    :ivar lowest_hearing_level_db: The lowest hearing threshold level to be
        measured the limits were raised for, in dB.
    :ivar noise_floor_db: The measuring chain's noise floor per band, in dB,
        or ``None`` when not given.
    :ivar earphone: For air conduction, the earphone the limits were written
        for: a column of Table 3, or ``"own attenuation"`` for an attenuation
        given band by band; ``None`` for bone conduction and sound field.
    :ivar earphone_attenuation_db: The earphone's own attenuation per band of
        :data:`AMBIENT_NOISE_BANDS_HZ`, in dB, when ``earphone`` is
        ``"own attenuation"``; ``None`` otherwise.
    :ivar allowed_threshold_shift_db: The threshold shift accepted from the
        ambient noise, 2 (default) or 5, in dB.

    A band the measurement leaves out is a band the room is not shown to meet,
    so :attr:`passes` needs every band of the table.
    """

    presentation: str
    frequencies: np.ndarray
    levels_db: np.ndarray
    lowest_test_frequency_hz: float
    lowest_hearing_level_db: float
    noise_floor_db: np.ndarray | None = None
    earphone: str | None = None
    earphone_attenuation_db: np.ndarray | None = None
    allowed_threshold_shift_db: float = _BASE_THRESHOLD_SHIFT_DB

    def __post_init__(self) -> None:
        """Reject a check whose bands or choices the tables cannot be read for.

        :raises ValueError: for the reasons :func:`ambient_noise_limits` gives,
            an earphone named where the presentation takes none or an own
            attenuation without the ``"own attenuation"`` name, a frequency
            the table does not list or listed out of order, or levels that do
            not match the bands.
        """
        own = self.earphone_attenuation_db is not None
        if (self.presentation == "air") != (self.earphone is not None) or own != (
            self.earphone == "own attenuation"
        ):
            msg = (
                "AmbientNoiseCheck: 'earphone' names a column of Table 3, or "
                "'own attenuation' with 'earphone_attenuation_db', for air "
                "conduction only."
            )
            raise ValueError(msg)
        rows = self._rows
        if np.asarray(self.levels_db).shape != rows.shape:
            msg = "AmbientNoiseCheck: 'levels_db' must hold one level per band."
            raise ValueError(msg)
        floor = self.noise_floor_db
        if floor is not None and np.asarray(floor).shape != rows.shape:
            msg = "AmbientNoiseCheck: 'noise_floor_db' must hold one level per band."
            raise ValueError(msg)
        if self.limits_db.shape != rows.shape:  # reading them validates the choices
            msg = "AmbientNoiseCheck: the tables give no limit for these bands."
            raise ValueError(msg)

    @property
    def table_bands_hz(self) -> tuple[float, ...]:
        """Every band the table sets a limit for, in hertz."""
        return tuple(float(b) for b in _table_for(self.presentation)[1])

    @property
    def _rows(self) -> np.ndarray:
        return _table_rows(
            self.presentation, np.atleast_1d(np.asarray(self.frequencies, np.float64))
        )

    @property
    def limits_db(self) -> np.ndarray:
        """The maximum permissible level per band, in dB.

        :return: :func:`ambient_noise_limits` of the presentation and the
            tester's choices, at :attr:`frequencies`.
        """
        own = self.earphone_attenuation_db
        column = (
            "supra-aural" if self.earphone is None or own is not None else self.earphone
        )
        limits = ambient_noise_limits(
            self.presentation,
            lowest_test_frequency_hz=self.lowest_test_frequency_hz,
            earphone=column,
            earphone_attenuation_db=own,
            lowest_hearing_level_db=self.lowest_hearing_level_db,
            allowed_threshold_shift_db=self.allowed_threshold_shift_db,
        )
        return np.asarray(limits[self._rows], dtype=np.float64)

    @property
    def exceedance_db(self) -> np.ndarray:
        """The measured level less the limit per band, in dB.

        :return: Positive where the room is too loud.
        """
        return np.asarray(self.levels_db - self.limits_db, dtype=np.float64)

    @property
    def within(self) -> np.ndarray:
        """Per band, whether the measured level is at or below the limit.

        :return: One boolean per band.
        """
        return _at_most(self.levels_db, self.limits_db)

    @property
    def covers_all_bands(self) -> bool:
        """Whether the measurement gives every band the table limits.

        :return: ``True`` when no band of the table is missing.
        """
        return self.frequencies.size == len(self.table_bands_hz)

    @property
    def floor_limited(self) -> np.ndarray:
        """Per band, whether the reading is within 6 dB of the noise floor.

        11.1 asks the measuring chain for a noise floor at least 6 dB below
        the level it measures. A band that misses it reads high, so a band
        within its limit still is; one over its limit may be the floor's.

        :return: One boolean per band, all ``False`` without a floor.
        """
        if self.noise_floor_db is None:
            return np.zeros(self.frequencies.size, dtype=bool)
        return ~_at_least(self.levels_db - self.noise_floor_db, _NOISE_FLOOR_MARGIN_DB)

    @property
    def lowest_measurable_hearing_level_db(self) -> float:
        """The lowest hearing threshold level this room lets be measured, in dB.

        11.1 raises every limit by the lowest hearing threshold level to be
        measured, and ISO 8253-2 Clause 6 does the same for sound field
        audiometry, so the room allows the lowest level that brings every
        measured band under its raised limit. For sound field audiometry,
        ISO 8253-2 11.1 f) asks the report to state it when it is not 0 dB.
        ISO 8253-1 has no such reporting item: with earphones or a bone
        vibrator it is the level the rule of 11.1 implies.

        :return: :attr:`lowest_hearing_level_db` plus the largest exceedance.
        """
        return float(self.lowest_hearing_level_db + np.max(self.exceedance_db))

    @property
    def passes(self) -> bool:
        """Whether every band of the table was measured and is within its limit.

        :return: ``True`` when the room qualifies.
        """
        return bool(self.covers_all_bands and np.all(self.within))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "an AmbientNoiseCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the measured spectrum against the limits, exceedances marked.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the measured spectrum.
        :return: The axes.
        """
        from .._plot.audiometry import plot_ambient_noise

        return plot_ambient_noise(self, ax=ax, language=language, **kwargs)


def check_audiometric_ambient_noise(
    levels_db: ArrayLike,
    *,
    presentation: str = "air",
    lowest_test_frequency_hz: float = 125.0,
    earphone: str = "supra-aural",
    earphone_attenuation_db: ArrayLike | None = None,
    lowest_hearing_level_db: float = 0.0,
    allowed_threshold_shift_db: float = 2.0,
    frequencies: ArrayLike | None = None,
    noise_floor_db: ArrayLike | None = None,
) -> AmbientNoiseCheck:
    """Is the test room quiet enough for the audiometry? (ISO 8253-1 Clause 11).

    Compares the ambient sound pressure level measured at the position of the
    subject's head, with the subject absent and the room as it is during
    testing (ventilation running if it runs then), with the limits of
    :func:`ambient_noise_limits`: ISO 8253-1 Table 2 for air conduction,
    Table 4 for bone conduction, or ISO 8253-2 Table 2 for sound field
    audiometry (its Clause 6).

    With ``presentation="sound field"`` and narrow-band noise as the test
    signal, footnote b to ISO 8253-2 Table 2 says the limits should be lower
    than the table's. It prints no figure for how much, so the check applies
    the table as printed, and a room that passes it may still be too loud for
    a narrow-band noise signal.

    :param levels_db: The measured one-third-octave band levels, in dB re
        20 µPa: one per band of the table, or one per band of ``frequencies``.
    :param presentation: ``"air"`` (default), ``"bone"`` or ``"sound field"``.
    :param lowest_test_frequency_hz: The lowest test tone frequency, 125
        (default), 250, or for air conduction 500.
    :param earphone: A column of Table 3; air conduction only.
    :param earphone_attenuation_db: Or another earphone's attenuation per band
        of Table 3; air conduction only.
    :param lowest_hearing_level_db: The lowest hearing threshold level to be
        measured, in dB; 0 by default.
    :param allowed_threshold_shift_db: The threshold shift accepted from the
        ambient noise, 2 (default) or 5, in dB.
    :param frequencies: The mid-frequencies of the measured bands, in hertz,
        each one of the table's, or ``None`` for all of them. A measurement
        that leaves bands out is judged on those it has, and does not pass.
    :param noise_floor_db: The measuring chain's noise floor per measured
        band, in dB, to flag the bands where 11.1's 6 dB margin is missed.
    :return: :class:`AmbientNoiseCheck`.
    :raises ValueError: for the reasons :func:`ambient_noise_limits` gives, a
        frequency the table does not list, or levels that do not match the
        bands.
    """
    _table, bands = _table_for(presentation)
    # Validates the tester's choices against the tables before anything else.
    ambient_noise_limits(
        presentation,
        lowest_test_frequency_hz=lowest_test_frequency_hz,
        earphone=earphone,
        earphone_attenuation_db=earphone_attenuation_db,
        lowest_hearing_level_db=lowest_hearing_level_db,
        allowed_threshold_shift_db=allowed_threshold_shift_db,
    )
    table = np.asarray(bands, dtype=np.float64)
    freqs = (
        table.copy()
        if frequencies is None
        else table[_table_rows(presentation, _levels(frequencies, "frequencies"))]
    )
    levels = _levels(levels_db, "levels_db")
    if levels.size != freqs.size:
        msg = f"'levels_db' must hold one level per band; got {levels.size} for {freqs.size}."
        raise ValueError(msg)
    floor = None
    if noise_floor_db is not None:
        floor = _levels(noise_floor_db, "noise_floor_db")
        if floor.size != freqs.size:
            msg = (
                "'noise_floor_db' must hold one level per band; got "
                f"{floor.size} for {freqs.size}."
            )
            raise ValueError(msg)
    return AmbientNoiseCheck(
        presentation=presentation,
        frequencies=freqs,
        levels_db=levels,
        lowest_test_frequency_hz=float(lowest_test_frequency_hz),
        lowest_hearing_level_db=float(lowest_hearing_level_db),
        noise_floor_db=floor,
        earphone=_earphone_name(presentation, earphone, earphone_attenuation_db),
        earphone_attenuation_db=(
            None
            if presentation != "air" or earphone_attenuation_db is None
            else _levels(earphone_attenuation_db, "earphone_attenuation_db").copy()
        ),
        allowed_threshold_shift_db=float(allowed_threshold_shift_db),
    )


def _earphone_name(
    presentation: str, earphone: str, earphone_attenuation_db: ArrayLike | None
) -> str | None:
    """The earphone a check's limits were written for, for its figure.

    :param presentation: The presentation.
    :param earphone: The column of Table 3 named.
    :param earphone_attenuation_db: The attenuation given instead, if any.
    :return: The name, ``"own attenuation"``, or ``None`` off air conduction.
    """
    if presentation != "air":
        return None
    return earphone if earphone_attenuation_db is None else "own attenuation"


# ---------------------------------------------------------------------------
# The ascending method (6.2.3.2, 6.2.4.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AscendingThresholdResult:
    """The hearing threshold level by the ascending method (6.2.4.2).

    :ivar ascent_levels_db: The level at which each ascent ended in a
        response, in presentation order, in dB.
    :ivar threshold_db: The hearing threshold level, in dB: the lowest level
        at which responses occur in more than half of the ascents, once the
        stopping rule of 6.2.3.2 is met; NaN until then.
    :ivar determined: Whether the stopping rule is met: three responses at
        one level (two in the shortened version).
    :ivar shortened: Whether the shortened version was applied.
    :ivar series_exhausted: Whether the series used up its ascents (five, or
        three shortened) without a threshold. The full method then starts a
        new series 10 dB above the last response.
    :ivar next_level_db: The level to present next, in dB, when the
        presentations were given and no threshold is determined yet; NaN
        otherwise.
    :ivar presentation_levels_db: The levels presented, in dB, or ``None``
        when only the ascents were given.
    :ivar responses: Whether each presentation drew a response, or ``None``.
    """

    ascent_levels_db: np.ndarray
    threshold_db: float
    determined: bool
    shortened: bool
    series_exhausted: bool
    next_level_db: float
    presentation_levels_db: np.ndarray | None = None
    responses: np.ndarray | None = None

    @property
    def span_db(self) -> float:
        """The spread of the ascents' response levels, in dB.

        :return: The largest less the smallest, 0 for fewer than two ascents.
        """
        if self.ascent_levels_db.size == 0:
            return 0.0
        return float(np.ptp(self.ascent_levels_db))

    @property
    def doubtful(self) -> bool:
        """Whether the response levels span more than 10 dB (6.2.4.2).

        The text says such a test should be considered of doubtful reliability,
        repeated, and noted on the audiogram.

        :return: ``True`` when the span exceeds 10 dB.
        """
        return self.span_db > _SPREAD_LIMIT_DB + _BOUNDARY_SLACK_DB

    @property
    def responses_at_threshold(self) -> int:
        """How many ascents ended at the threshold level.

        :return: The count, 0 when no threshold is determined.
        """
        if not self.determined:
            return 0
        return int(
            np.sum(
                np.isclose(
                    self.ascent_levels_db, self.threshold_db, atol=_LEVEL_ATOL_DB
                )
            )
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the presentations, heard and not heard, and the threshold.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the presentation staircase.
        :return: The axes.
        """
        from .._plot.audiometry import plot_ascending_threshold

        return plot_ascending_threshold(self, ax=ax, language=language, **kwargs)


def _ascending_rule(
    ascents: list[float], *, shortened: bool
) -> tuple[float, bool, bool]:
    """The threshold of 6.2.4.2 and the stopping rule of 6.2.3.2.

    :param ascents: The response level of each ascent so far.
    :param shortened: Whether the shortened version applies.
    :return: ``(threshold, determined, exhausted)``.
    """
    needed, most = _ASCENDING_SHORT if shortened else _ASCENDING_FULL
    counts = Counter(round(level, 6) for level in ascents)
    majority = sorted(
        level for level, n in counts.items() if n > len(ascents) / 2 and n >= needed
    )
    if majority:
        return float(majority[0]), True, False
    return math.nan, False, len(ascents) >= most


def _replay_ascending(
    levels: np.ndarray,
    responses: np.ndarray,
    *,
    shortened: bool,
    familiarization_level_db: float | None,
) -> tuple[list[float], float, bool, bool, float]:
    """Replay a presentation sequence of the ascending method.

    :param levels: The levels presented, in dB.
    :param responses: Whether each drew a response.
    :param shortened: Whether the shortened version applies.
    :param familiarization_level_db: The lowest familiarization response.
    :return: ``(ascents, threshold, determined, exhausted, next level)``.
    :raises ValueError: for a step the method does not take, or presentations
        after the series ended.
    """
    _check_first_tone(levels, familiarization_level_db)
    ascents: list[float] = []
    threshold, determined, exhausted = math.nan, False, False
    for i in range(levels.size):
        if determined or exhausted:
            msg = (
                f"presentation {i} comes after the series ended at presentation "
                f"{i - 1}; a new frequency or a new series is a new call."
            )
            raise ValueError(msg)
        if i == 0:
            continue
        _check_step(levels, responses, i)
        if responses[i] and not responses[i - 1]:
            ascents.append(float(levels[i]))
            threshold, determined, exhausted = _ascending_rule(
                ascents, shortened=shortened
            )
    next_level = _next_ascending_level(
        levels,
        responses,
        ascents,
        familiarization_level_db,
        ended=determined,
        restart=exhausted and not shortened,
    )
    return ascents, threshold, determined, exhausted, next_level


def _check_first_tone(
    levels: np.ndarray, familiarization_level_db: float | None
) -> None:
    """6.2.3.2 Step 1: the first tone 10 dB below the familiarization response.

    :raises ValueError: for a first tone at another level.
    """
    if familiarization_level_db is None or not levels.size:
        return
    first = float(familiarization_level_db) - _FIRST_TONE_BELOW_DB
    if not math.isclose(levels[0], first, abs_tol=_LEVEL_ATOL_DB):
        msg = (
            f"the first tone must be {first:g} dB, 10 dB below the lowest "
            f"familiarization response (6.2.3.2 Step 1); got {levels[0]:g} dB."
        )
        raise ValueError(msg)


def _check_step(levels: np.ndarray, responses: np.ndarray, i: int) -> None:
    """6.2.3.2: 10 dB down after a response, 5 dB up after none.

    :raises ValueError: for presentation ``i`` at another level.
    """
    step = -_DESCENT_STEP_DB if responses[i - 1] else _ASCENT_STEP_DB
    expected = levels[i - 1] + step
    if not math.isclose(levels[i], expected, abs_tol=_LEVEL_ATOL_DB):
        after = "a response" if responses[i - 1] else "no response"
        msg = (
            f"presentation {i} is at {levels[i]:g} dB; after {after} at "
            f"{levels[i - 1]:g} dB the ascending method presents "
            f"{expected:g} dB (6.2.3.2)."
        )
        raise ValueError(msg)


def _next_ascending_level(
    levels: np.ndarray,
    responses: np.ndarray,
    ascents: list[float],
    familiarization_level_db: float | None,
    *,
    ended: bool,
    restart: bool,
) -> float:
    """The level to present next, or NaN when there is none.

    The first tone for an empty sequence, 10 dB above the last response for a
    full series exhausted without a threshold (6.2.3.2), and otherwise the
    next step of the method after the last tone.
    """
    if ended or not levels.size:
        return (
            float(familiarization_level_db) - _FIRST_TONE_BELOW_DB
            if not levels.size and familiarization_level_db is not None
            else math.nan
        )
    if restart:
        return ascents[-1] + _RESTART_ABOVE_DB
    step = -_DESCENT_STEP_DB if responses[-1] else _ASCENT_STEP_DB
    return float(levels[-1] + step)


def ascending_method_threshold(
    ascent_levels_db: ArrayLike | None = None,
    *,
    presentation_levels_db: ArrayLike | None = None,
    responses: ArrayLike | None = None,
    shortened: bool = False,
    familiarization_level_db: float | None = None,
) -> AscendingThresholdResult:
    """The hearing threshold level by the ascending method (6.2.3.2, 6.2.4.2).

    The method presents tones of 1 s to 2 s. Step 1 starts 10 dB below the
    lowest level the subject responded to during familiarization and rises
    in 5 dB steps until a response; Step 2 drops 10 dB after each response
    until there is none, and ascends again in 5 dB steps. The series stops
    when three responses fall at one level within at most five ascents, or,
    in the shortened version, two within at most three. The hearing threshold
    level is then the lowest level at which responses occur in more than half
    of the ascents (6.2.4.2).

    Give either the level at which each ascent ended in a response, or the
    whole presentation sequence with its responses. The sequence is replayed
    against the steps of 6.2.3.2, an ascent being a response reached from a
    tone that drew none, and the result says what to present next, which is
    the level a computer-controlled audiometer (6.4) can be given: call it
    with an empty sequence and the familiarization level for the first tone.

    After five ascents without three responses at one level the series is
    exhausted, and 6.2.3.2 starts a new one 10 dB above the last response;
    that is a new call. 6.2.3.2 does not say what follows a shortened series
    that ends its three ascents without two responses at one level; the
    library's choice is to continue it with the full method on the same
    presentations, a new call with ``shortened=False``.

    :param ascent_levels_db: The response level of each ascent, in dB, in
        order.
    :param presentation_levels_db: Or the hearing level of every tone
        presented, in dB, in order.
    :param responses: With it, whether each tone drew a response.
    :param shortened: ``True`` for the shortened version.
    :param familiarization_level_db: The lowest level of the subject's
        responses during familiarization (6.2.2), in dB, to check the first
        tone of a sequence, or to give it when the sequence is empty.
    :return: :class:`AscendingThresholdResult`.
    :raises ValueError: if neither form or both are given, the responses do
        not match the presentations, a step differs from 6.2.3.2, a
        presentation follows the end of the series, or more ascents are given
        than a series holds.
    """
    sequence = presentation_levels_db is not None or responses is not None
    if ascent_levels_db is not None and not sequence:
        return _threshold_from_ascents(ascent_levels_db, shortened=shortened)
    if (
        ascent_levels_db is not None
        or presentation_levels_db is None
        or responses is None
    ):
        msg = (
            "give either 'ascent_levels_db', or both 'presentation_levels_db' "
            "and 'responses', and not both forms."
        )
        raise ValueError(msg)
    return _threshold_from_sequence(
        presentation_levels_db,
        responses,
        shortened=shortened,
        familiarization_level_db=familiarization_level_db,
    )


def _threshold_from_ascents(
    ascent_levels_db: ArrayLike, *, shortened: bool
) -> AscendingThresholdResult:
    """6.2.4.2 on the response level of each ascent, checked against 6.2.3.2.

    :raises ValueError: for levels that are not finite, more ascents than a
        series holds, or ascents after the series ended.
    """
    levels = np.array(ascent_levels_db, dtype=np.float64)
    if levels.ndim != 1 or not np.all(np.isfinite(levels)):
        msg = "'ascent_levels_db' must be a one-dimensional array of finite levels."
        raise ValueError(msg)
    most = (_ASCENDING_SHORT if shortened else _ASCENDING_FULL)[1]
    if levels.size > most:
        msg = (
            f"a series of the {'shortened ' if shortened else ''}ascending "
            f"method holds at most {most} ascents; got {levels.size}."
        )
        raise ValueError(msg)
    ascents = [float(level) for level in levels]
    threshold, determined, exhausted = math.nan, False, False
    for count in range(1, len(ascents) + 1):
        threshold, determined, exhausted = _ascending_rule(
            ascents[:count], shortened=shortened
        )
        if determined and count < len(ascents):
            msg = (
                f"the series ended at ascent {count}; the ascents after it "
                "belong to another series."
            )
            raise ValueError(msg)
    return AscendingThresholdResult(
        ascent_levels_db=np.array(ascents, dtype=np.float64),
        threshold_db=threshold,
        determined=determined,
        shortened=shortened,
        series_exhausted=exhausted,
        next_level_db=math.nan,
    )


def _threshold_from_sequence(
    presentation_levels_db: ArrayLike,
    responses: ArrayLike,
    *,
    shortened: bool,
    familiarization_level_db: float | None,
) -> AscendingThresholdResult:
    """6.2.4.2 on a whole presentation sequence, replayed against 6.2.3.2.

    :raises ValueError: for levels that are not finite, responses that do not
        match them, or a sequence the method does not produce.
    """
    levels = np.array(presentation_levels_db, dtype=np.float64)
    heard = np.array(responses, dtype=bool)
    if (
        levels.ndim != 1
        or heard.shape != levels.shape
        or not np.all(np.isfinite(levels))
    ):
        msg = (
            "'presentation_levels_db' must be finite levels and 'responses' one "
            "boolean per presentation."
        )
        raise ValueError(msg)
    ascents, threshold, determined, exhausted, next_level = _replay_ascending(
        levels,
        heard,
        shortened=shortened,
        familiarization_level_db=familiarization_level_db,
    )
    return AscendingThresholdResult(
        ascent_levels_db=np.array(ascents, dtype=np.float64),
        threshold_db=threshold,
        determined=determined,
        shortened=shortened,
        series_exhausted=exhausted,
        next_level_db=next_level,
        presentation_levels_db=levels,
        responses=heard,
    )


# ---------------------------------------------------------------------------
# The bracketing method (6.2.4.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BracketingThresholdResult:
    """The hearing threshold level by the bracketing method (6.2.4.3).

    :ivar ascent_levels_db: The lowest response level of each ascent, in dB.
    :ivar descent_levels_db: The lowest response level of each descent, in dB.
    :ivar mean_db: The mean of the two averages, unrounded, in dB.
    :ivar threshold_db: That mean rounded to the nearest 5 dB step, in dB; a
        mean halfway between two steps goes to the higher one.
    """

    ascent_levels_db: np.ndarray
    descent_levels_db: np.ndarray
    mean_db: float
    threshold_db: float

    @property
    def ascent_mean_db(self) -> float:
        """The average of the ascents' lowest response levels, in dB.

        :return: The mean.
        """
        return float(np.mean(self.ascent_levels_db))

    @property
    def descent_mean_db(self) -> float:
        """The average of the descents' lowest response levels, in dB.

        :return: The mean.
        """
        return float(np.mean(self.descent_levels_db))

    @property
    def complete(self) -> bool:
        """Whether the series is long enough (6.2.3.2 Step 2).

        :return: ``True`` for three ascents and three descents, or for two of
            each whose four levels differ by no more than 5 dB (the shortened
            version).
        """
        ups, downs = self.ascent_levels_db.size, self.descent_levels_db.size
        if min(ups, downs) >= _BRACKETING_FULL_COUNT:
            return True
        if min(ups, downs) < _BRACKETING_SHORT_COUNT:
            return False
        four = np.concatenate(
            [
                self.ascent_levels_db[:_BRACKETING_SHORT_COUNT],
                self.descent_levels_db[:_BRACKETING_SHORT_COUNT],
            ]
        )
        return bool(np.ptp(four) <= _SHORT_BRACKETING_SPREAD_DB + _BOUNDARY_SLACK_DB)

    @property
    def repeat_advised(self) -> bool:
        """Whether the ascents or the descents spread over more than 10 dB.

        6.2.4.3 says the test should then be repeated.

        :return: ``True`` when either set of levels spans more than 10 dB.
        """
        limit = _SPREAD_LIMIT_DB + _BOUNDARY_SLACK_DB
        return bool(
            np.ptp(self.ascent_levels_db) > limit
            or np.ptp(self.descent_levels_db) > limit
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the ascents' and descents' levels, their means and the threshold.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the ascents' markers.
        :return: The axes.
        """
        from .._plot.audiometry import plot_bracketing_threshold

        return plot_bracketing_threshold(self, ax=ax, language=language, **kwargs)


def bracketing_method_threshold(
    ascent_levels_db: ArrayLike, descent_levels_db: ArrayLike
) -> BracketingThresholdResult:
    r"""The hearing threshold level by the bracketing method (6.2.4.3).

    The bracketing method ascends in 5 dB steps to a response, rises 5 dB and
    descends in 5 dB steps until there is none, three ascents and three
    descents in all, or two of each when their four lowest response levels
    are within 5 dB of each other (6.2.3.2). The threshold averages the lowest
    response levels of the ascents, averages those of the descents, and
    rounds the mean of the two averages to the nearest 5 dB step:

    .. math::

       L_\mathrm{HT} = 5\ \mathrm{dB} \times \operatorname{round}\left(
       \frac{\bar L_\mathrm{asc} + \bar L_\mathrm{desc}}{2 \times 5\ \mathrm{dB}}
       \right)

    A mean halfway between two steps goes to the higher step, the rounding
    the library applies wherever a standard says "nearest" without a rule for
    the tie.

    :param ascent_levels_db: The lowest level at which a response occurred in
        each ascent, in dB.
    :param descent_levels_db: The lowest level at which a response occurred in
        each descent, in dB.
    :return: :class:`BracketingThresholdResult`, which also says whether the
        series is complete and whether 6.2.4.3 advises a repeat.
    :raises ValueError: for an empty or non-finite set of levels.
    """
    ups = _levels(ascent_levels_db, "ascent_levels_db")
    downs = _levels(descent_levels_db, "descent_levels_db")
    mean = 0.5 * (float(np.mean(ups)) + float(np.mean(downs)))
    return BracketingThresholdResult(
        ascent_levels_db=ups,
        descent_levels_db=downs,
        mean_db=mean,
        threshold_db=_round_half_up(mean, _BRACKETING_STEP_DB),
    )


# ---------------------------------------------------------------------------
# Automatic recording audiometry (6.3.5)
# ---------------------------------------------------------------------------


def _reversal_kinds(levels: np.ndarray, name: str) -> np.ndarray:
    """Which reversals of a tracing are peaks, the rest being valleys.

    :param levels: The levels at successive reversals, in dB.
    :param name: The argument name, for the error message.
    :return: ``True`` for a peak.
    :raises ValueError: when successive reversals do not alternate between
        peaks and valleys.
    """
    steps = np.diff(levels)
    if not np.all(np.abs(steps) > 0.0) or np.any(steps[1:] * steps[:-1] > 0.0):
        msg = (
            f"'{name}' must alternate between peaks and valleys: each reversal "
            "turns the trace, so successive ones cannot be equal or keep going "
            "the same way."
        )
        raise ValueError(msg)
    peak_first = bool(steps[0] < 0.0)
    kinds = np.zeros(levels.size, dtype=bool)
    kinds[0 if peak_first else 1 :: 2] = True
    return kinds


@dataclass(frozen=True)
class AutomaticThresholdResult:
    """The hearing threshold level from an automatic recording (6.3.5).

    :ivar reversal_levels_db: The levels at the reversals of the tracing at
        one frequency, in order, in dB.
    :ivar is_peak: Whether each reversal is a peak (a local maximum of the
        level), the others being valleys.
    :ivar retained: Whether each reversal is kept after 6.3.5 a): the first
        is ignored, and so are both ends of every excursion of 3 dB or less.
    :ivar mean_db: The mean of the average peak and the average valley, in dB.
    :ivar threshold_db: That mean rounded up to the next whole decibel, in dB.
    """

    reversal_levels_db: np.ndarray
    is_peak: np.ndarray
    retained: np.ndarray
    mean_db: float
    threshold_db: float

    @property
    def peaks_db(self) -> np.ndarray:
        """The retained peaks, in dB.

        :return: Their levels, in order.
        """
        return np.asarray(
            self.reversal_levels_db[self.retained & self.is_peak], dtype=np.float64
        )

    @property
    def valleys_db(self) -> np.ndarray:
        """The retained valleys, in dB.

        :return: Their levels, in order.
        """
        return np.asarray(
            self.reversal_levels_db[self.retained & ~self.is_peak], dtype=np.float64
        )

    @property
    def doubtful(self) -> bool:
        """Whether the recording should be repeated (6.3.5).

        :return: ``True`` when the peaks or the valleys deviate by more than
            10 dB from each other, or fewer than six reversals remain.
        """
        limit = _SPREAD_LIMIT_DB + _BOUNDARY_SLACK_DB
        return bool(
            np.ptp(self.peaks_db) > limit
            or np.ptp(self.valleys_db) > limit
            or int(np.sum(self.retained)) < _MINIMUM_REVERSALS
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the tracing through its reversals, the ignored ones faded.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the tracing.
        :return: The axes.
        """
        from .._plot.audiometry import plot_automatic_threshold

        return plot_automatic_threshold(self, ax=ax, language=language, **kwargs)


def automatic_audiometry_threshold(
    reversal_levels_db: ArrayLike,
) -> AutomaticThresholdResult:
    """The hearing threshold level from an automatic recording (6.3.5).

    The subject holds the level down while the tone is heard and lets it rise
    when it is not, so the tracing zigzags about the threshold. At one
    frequency, 6.3.5:

    - a) ignores the first reversal after the change of frequency and every
      reversal of an excursion of 3 dB or less (both reversals that bound it);
    - b) averages the remaining peaks, and averages the remaining valleys;
    - c) takes the mean of the two averages, rounded up to the nearest whole
      number of decibels, as the hearing threshold level.

    The recording is of doubtful reliability, and should be repeated, when the
    peaks or the valleys deviate by more than 10 dB from each other or fewer
    than six reversals remain after a). NOTE 2 to 6.3.5 puts automatic
    thresholds 3 dB lower on average than manual ones with 5 dB steps; that
    is a property of the method, and nothing here corrects for it.

    :param reversal_levels_db: The hearing level at each reversal of the
        tracing at one frequency, in dB, in the order they were traced.
    :return: :class:`AutomaticThresholdResult`.
    :raises ValueError: for fewer than three reversals, reversals that do not
        alternate between peaks and valleys, or a tracing that keeps no peak
        or no valley after a).
    """
    levels = _levels(reversal_levels_db, "reversal_levels_db", minimum=3)
    kinds = _reversal_kinds(levels, "reversal_levels_db")
    retained = np.ones(levels.size, dtype=bool)
    retained[0] = False
    small = np.abs(np.diff(levels)) <= _SMALL_EXCURSION_DB + _BOUNDARY_SLACK_DB
    retained[:-1] &= ~small
    retained[1:] &= ~small
    peaks = levels[retained & kinds]
    valleys = levels[retained & ~kinds]
    if peaks.size == 0 or valleys.size == 0:
        msg = (
            "no peak or no valley of the tracing is left after 6.3.5 a) "
            "ignores the first reversal and the excursions of 3 dB or less."
        )
        raise ValueError(msg)
    mean = 0.5 * (float(np.mean(peaks)) + float(np.mean(valleys)))
    return AutomaticThresholdResult(
        reversal_levels_db=levels,
        is_peak=kinds,
        retained=retained,
        mean_db=mean,
        # Settled first, so a mean such as 12,000 000 000 000 002 dB is not
        # taken up to 13 dB by a last-bit excess.
        threshold_db=float(math.ceil(float(settled(mean)))),
    )


# ---------------------------------------------------------------------------
# Sweep-frequency audiometry (7.5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SweepThresholdResult:
    """Hearing threshold levels from a sweep-frequency tracing (7.5).

    :ivar reversal_frequencies: The frequency of each reversal, in hertz.
    :ivar reversal_levels_db: The hearing level of each reversal, in dB.
    :ivar is_peak: Whether each reversal is a peak, the others being valleys.
    :ivar frequencies: The frequencies the threshold was determined at, in
        hertz.
    :ivar mean_db: At each, the mean of the average of the three nearest peaks
        and the average of the three nearest valleys, in dB.
    :ivar threshold_db: That mean rounded to the nearest whole decibel, in dB.
    :ivar spread_db: At each, the larger spread of the three peaks and of the
        three valleys it averaged, in dB.
    :ivar running_frequencies: The geometric mean frequency of each run of six
        consecutive reversals, in hertz.
    :ivar running_threshold_db: The arithmetic mean level of each run, in dB,
        the semicontinuous threshold of 7.5.
    """

    reversal_frequencies: np.ndarray
    reversal_levels_db: np.ndarray
    is_peak: np.ndarray
    frequencies: np.ndarray
    mean_db: np.ndarray
    threshold_db: np.ndarray
    spread_db: np.ndarray
    running_frequencies: np.ndarray
    running_threshold_db: np.ndarray

    @property
    def less_reliable(self) -> np.ndarray:
        """Per frequency, whether its peaks or valleys spread over 10 dB.

        7.5 NOTE 1 calls such a determination less reliable.

        :return: One boolean per frequency.
        """
        return np.asarray(self.spread_db > _SPREAD_LIMIT_DB + _BOUNDARY_SLACK_DB)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the tracing, its running threshold and the thresholds found.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the running threshold.
        :return: The axes.
        """
        from .._plot.audiometry import plot_sweep_threshold

        return plot_sweep_threshold(self, ax=ax, language=language, **kwargs)


def sweep_audiometry_threshold(
    reversal_frequencies: ArrayLike,
    reversal_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> SweepThresholdResult:
    r"""Hearing threshold levels from a sweep-frequency tracing (7.5).

    The frequency sweeps continuously, normally at 0,5 to 2 octaves per
    minute, while the subject tracks the threshold as in automatic
    audiometry. At a specified frequency, 7.5 averages the three peaks and the
    three valleys of the tracing closest to it and takes the mean of the two
    averages, rounded to the nearest whole decibel, as the hearing threshold
    level there. Closest is measured on the logarithmic frequency axis the
    sweep runs on, and a mean halfway between two decibels goes up.

    As a semicontinuous function of frequency, 7.5 runs the average along the
    tracing: each run of three consecutive pairs of peaks and valleys, six
    consecutive reversals, gives the arithmetic mean of its six levels at the
    geometric mean of its six frequencies,

    .. math::

       L_\mathrm{HT}\left(\sqrt[6]{f_1 f_2 \cdots f_6}\right)
       = \frac{1}{6} \sum_{k=1}^{6} L_k

    and the run advances one reversal at a time.

    :param reversal_frequencies: The frequency at each reversal, in hertz, in
        the order traced; the sweep may run upwards or downwards.
    :param reversal_levels_db: The hearing level at each reversal, in dB.
    :param frequencies: The frequencies to determine the threshold at, in
        hertz, or ``None`` for the audiometric frequencies from 125 Hz to
        8 kHz that the tracing spans.
    :return: :class:`SweepThresholdResult`.
    :raises ValueError: for arrays that do not match, fewer than three peaks
        or three valleys, reversals that do not alternate, a sweep that does
        not run one way, or no frequency to determine.
    """
    levels = _levels(reversal_levels_db, "reversal_levels_db", minimum=6)
    freqs = _levels(reversal_frequencies, "reversal_frequencies", minimum=6)
    if freqs.size != levels.size or np.any(freqs <= 0.0):
        msg = (
            "'reversal_frequencies' must hold one positive frequency per "
            "reversal level."
        )
        raise ValueError(msg)
    steps = np.diff(freqs)
    if not (np.all(steps > 0.0) or np.all(steps < 0.0)):
        msg = "'reversal_frequencies' must run one way, as a sweep does."
        raise ValueError(msg)
    kinds = _reversal_kinds(levels, "reversal_levels_db")
    peaks, valleys = np.flatnonzero(kinds), np.flatnonzero(~kinds)
    if min(peaks.size, valleys.size) < _SWEEP_REVERSALS_PER_SIDE:
        msg = "a sweep-frequency tracing needs at least three peaks and three valleys."
        raise ValueError(msg)
    if frequencies is None:
        low, high = float(np.min(freqs)), float(np.max(freqs))
        audiometric = np.asarray(_AUDIOMETRIC_FREQUENCIES, dtype=np.float64)
        targets = audiometric[(audiometric >= low) & (audiometric <= high)]
        if targets.size == 0:
            msg = (
                "the tracing spans no audiometric frequency; give 'frequencies' "
                "to determine the threshold at."
            )
            raise ValueError(msg)
    else:
        targets = _levels(frequencies, "frequencies")
        if np.any(targets <= 0.0):
            msg = "'frequencies' must be positive, in hertz."
            raise ValueError(msg)
    log_f = np.log(freqs)
    means = np.empty(targets.size)
    spreads = np.empty(targets.size)
    for k, target in enumerate(targets):
        distance = np.abs(log_f - math.log(target))
        near_peaks = levels[peaks[np.argsort(distance[peaks], kind="stable")[:3]]]
        near_valleys = levels[valleys[np.argsort(distance[valleys], kind="stable")[:3]]]
        means[k] = 0.5 * (float(np.mean(near_peaks)) + float(np.mean(near_valleys)))
        spreads[k] = max(float(np.ptp(near_peaks)), float(np.ptp(near_valleys)))
    window = 2 * _SWEEP_REVERSALS_PER_SIDE
    runs = levels.size - window + 1
    running_f = np.array(
        [math.exp(float(np.mean(log_f[i : i + window]))) for i in range(runs)]
    )
    running_l = np.array([float(np.mean(levels[i : i + window])) for i in range(runs)])
    return SweepThresholdResult(
        reversal_frequencies=freqs,
        reversal_levels_db=levels,
        is_peak=kinds,
        frequencies=np.array(targets, dtype=np.float64),
        mean_db=means,
        threshold_db=np.array([_round_half_up(m, 1.0) for m in means]),
        spread_db=spreads,
        running_frequencies=running_f,
        running_threshold_db=running_l,
    )


# ---------------------------------------------------------------------------
# The repeat at 1 kHz and the cautions (6.2.3.2, 8.4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetestAgreementCheck:
    """Whether a repeat measurement confirms the first one (6.2.3.2 Step 3).

    :ivar first_db: The hearing threshold level measured first, in dB.
    :ivar repeat_db: The hearing threshold level of the repeat measurement, in
        dB.
    :ivar frequency_hz: The frequency of both, in hertz: 1 kHz for the repeat
        Step 3 asks for, another for a further frequency retested after it.
    """

    first_db: float
    repeat_db: float
    frequency_hz: float

    @property
    def difference_db(self) -> float:
        """The repeat less the first measurement, in dB.

        :return: Positive for a worsening, negative for an improvement.
        """
        return float(self.repeat_db - self.first_db)

    @property
    def passes(self) -> bool:
        """Whether the two agree to 5 dB or less, and the test moves on.

        :return: ``True`` when the difference is at most 5 dB either way.
        """
        return abs(self.difference_db) <= _RETEST_AGREEMENT_DB + _BOUNDARY_SLACK_DB

    @property
    def retest_further_frequencies(self) -> bool:
        """Whether Step 3 sends the test back to the further frequencies.

        :return: ``True`` for an improvement or a worsening of 10 dB or more.
        """
        return abs(self.difference_db) >= _RETEST_DISAGREEMENT_DB - _BOUNDARY_SLACK_DB

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a RetestAgreementCheck has no truth value; read its '.passes' for "
            "the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two measurements and the 5 dB either side of the first.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the two measurements' markers.
        :return: The axes.
        """
        from .._plot.audiometry import plot_retest_agreement

        return plot_retest_agreement(self, ax=ax, language=language, **kwargs)


def check_retest_agreement(
    first_db: float, repeat_db: float, *, frequency_hz: float = 1000.0
) -> RetestAgreementCheck:
    """Does the repeat measurement confirm the first? (6.2.3.2 Step 3).

    Once every frequency of the first ear is tested, Step 3 repeats the
    measurement at 1 kHz. If the repeat agrees with the first measurement to
    5 dB or less, the test proceeds to the other ear; if it shows an
    improvement or a worsening of 10 dB or more, the further frequencies are
    retested in the same order until agreement to 5 dB or less is obtained.
    ISO 8253-2 8.1 asks for the same repeat at 1 kHz in sound field
    audiometry.

    The text is written for the 5 dB steps of a manual audiometer, where a
    difference is either 5 dB or less or 10 dB or more. A finer control can
    give a difference in between; it is not agreement to 5 dB or less, so it
    does not pass, and the text names no action for it, so
    :attr:`RetestAgreementCheck.retest_further_frequencies` is ``False`` too.

    :param first_db: The hearing threshold level measured first, in dB.
    :param repeat_db: The hearing threshold level of the repeat, in dB.
    :param frequency_hz: The frequency of both, in hertz; 1 kHz by default.
    :return: :class:`RetestAgreementCheck`.
    :raises ValueError: for a level that is not finite or a frequency that is
        not positive.
    """
    first, repeat = float(first_db), float(repeat_db)
    if not (math.isfinite(first) and math.isfinite(repeat)):
        msg = "'first_db' and 'repeat_db' must be finite hearing levels, in dB."
        raise ValueError(msg)
    f = float(frequency_hz)
    if not math.isfinite(f) or f <= 0.0:
        msg = f"'frequency_hz' must be a positive frequency in hertz; got {f:g}."
        raise ValueError(msg)
    return RetestAgreementCheck(first_db=first, repeat_db=repeat, frequency_hz=f)


@dataclass(frozen=True)
class AudiogramCautions:
    """The levels of an audiogram that call for caution (6.2.3.2, 8.4).

    :ivar frequencies: The test frequencies, in hertz.
    :ivar air_conduction_db: The air-conduction hearing threshold levels of one
        ear, in dB, one per frequency, or ``None``.
    :ivar bone_conduction_db: The bone-conduction hearing threshold levels, in
        dB, one per frequency, or ``None``.
    :ivar vibrator_placement: ``"mastoid"`` or ``"forehead"``, the placement
        the audiometer's bone conduction is calibrated for.
    """

    frequencies: np.ndarray
    air_conduction_db: np.ndarray | None
    bone_conduction_db: np.ndarray | None
    vibrator_placement: str

    @property
    def vibrotactile_levels_db(self) -> np.ndarray:
        """The average vibrotactile threshold of 8.4 at each frequency, in dB.

        :return: One level per frequency, 10 dB lower for forehead placement,
            NaN where 8.4 gives none.
        """
        offset = _FOREHEAD_OFFSET_DB if self.vibrator_placement == "forehead" else 0.0
        levels = np.full(self.frequencies.size, math.nan)
        for key, level in VIBROTACTILE_HEARING_LEVELS_DB.items():
            at = np.isclose(self.frequencies, key, rtol=_FREQUENCY_RTOL, atol=0.0)
            levels[at] = level - offset
        return levels

    @property
    def cross_hearing(self) -> np.ndarray:
        """Per frequency, whether the air-conduction level is 40 dB or more.

        6.2.3.2 asks for such results to be interpreted with caution because
        of cross-hearing: the tone may be heard by the other ear, and
        contralateral masking can be necessary.

        :return: One boolean per frequency, all ``False`` without air
            conduction levels.
        """
        if self.air_conduction_db is None:
            return np.zeros(self.frequencies.size, dtype=bool)
        return np.asarray(
            self.air_conduction_db >= _CROSS_HEARING_LEVEL_DB - _BOUNDARY_SLACK_DB,
            dtype=bool,
        )

    @property
    def vibrotactile(self) -> np.ndarray:
        """Per frequency, whether the bone-conduction level reaches 8.4's level.

        At or above the average vibrotactile threshold the subject may feel
        the vibrator rather than hear the tone, and 8.4 says care shall be
        taken that such a sensation is not taken for hearing.

        :return: One boolean per frequency, ``False`` where 8.4 gives no level
            or without bone conduction levels.
        """
        if self.bone_conduction_db is None:
            return np.zeros(self.frequencies.size, dtype=bool)
        return _at_least(self.bone_conduction_db, self.vibrotactile_levels_db)

    @property
    def any_caution(self) -> bool:
        """Whether any level is flagged by either rule.

        :return: ``True`` when some level calls for caution.
        """
        return bool(np.any(self.cross_hearing) or np.any(self.vibrotactile))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the audiogram with the caution levels and the levels flagged.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the air-conduction curve.
        :return: The axes.
        """
        from .._plot.audiometry import plot_audiogram_cautions

        return plot_audiogram_cautions(self, ax=ax, language=language, **kwargs)


def audiogram_cautions(
    frequencies: ArrayLike,
    *,
    air_conduction_db: ArrayLike | None = None,
    bone_conduction_db: ArrayLike | None = None,
    vibrator_placement: str = "mastoid",
) -> AudiogramCautions:
    """Flag the levels of an audiogram that call for caution (6.2.3.2, 8.4).

    Two rules of ISO 8253-1 judge a hearing threshold level by its size:

    - **cross-hearing** (6.2.3.2): an air-conduction hearing level of 40 dB
      or more, in either ear at any frequency, is to be interpreted with
      caution, because the tone may reach the other ear; contralateral
      masking can then be necessary;
    - **vibrotactile sensation** (8.4): with the bone vibrator on the
      mastoid, the vibrotactile threshold lies on average at a hearing level
      of about 40 dB at 250 Hz, 60 dB at 500 Hz and 70 dB at 1 kHz, about
      10 dB lower for an audiometer calibrated for forehead placement, and a
      bone-conduction response at such a level may be felt rather than heard.

    Give the levels of one ear; the caution of 6.2.3.2 holds for the results
    when either ear reaches 40 dB. Bone conduction gets no cross-hearing flag,
    because 40 dB is not its limit: 8.1 asks for the non-test ear to be
    masked at every level for a precise monaural result. 8.4 gives no
    vibrotactile level at other frequencies, where nothing is flagged, and its
    levels are averages about which individuals vary widely.

    :param frequencies: The test frequencies, in hertz.
    :param air_conduction_db: The air-conduction hearing threshold levels, in
        dB, one per frequency.
    :param bone_conduction_db: The bone-conduction hearing threshold levels,
        in dB, one per frequency.
    :param vibrator_placement: ``"mastoid"`` (default) or ``"forehead"``, the
        placement the bone conduction is calibrated for.
    :return: :class:`AudiogramCautions`.
    :raises ValueError: for neither set of levels, levels that do not match
        the frequencies, a frequency that is not positive, or an unknown
        placement.
    """
    freqs = _levels(frequencies, "frequencies")
    if np.any(freqs <= 0.0):
        msg = "'frequencies' must be positive, in hertz."
        raise ValueError(msg)
    if vibrator_placement not in _PLACEMENTS:
        msg = (
            f"'vibrator_placement' must be one of {_PLACEMENTS}; got "
            f"{vibrator_placement!r}."
        )
        raise ValueError(msg)
    if air_conduction_db is None and bone_conduction_db is None:
        msg = "give 'air_conduction_db', 'bone_conduction_db' or both."
        raise ValueError(msg)
    sets: dict[str, np.ndarray | None] = {}
    for name, values in (
        ("air_conduction_db", air_conduction_db),
        ("bone_conduction_db", bone_conduction_db),
    ):
        if values is None:
            sets[name] = None
            continue
        levels = _levels(values, name)
        if levels.size != freqs.size:
            msg = (
                f"'{name}' must hold one level per frequency; got {levels.size} "
                f"for {freqs.size}."
            )
            raise ValueError(msg)
        sets[name] = levels
    return AudiogramCautions(
        frequencies=freqs,
        air_conduction_db=sets["air_conduction_db"],
        bone_conduction_db=sets["bone_conduction_db"],
        vibrator_placement=vibrator_placement,
    )


# ---------------------------------------------------------------------------
# The uncertainty (Annex A)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AudiometricUncertaintyBudget:
    r"""The uncertainty budget of a hearing threshold level (Annex A).

    The eight standard uncertainties of Table A.1, each with a sensitivity
    coefficient of 1 and uncorrelated with the others (A.2), so the combined
    standard uncertainty is their root sum of squares (Formula (A.2)) and the
    expanded one is :math:`U = k u` with :math:`k` = 2 (A.5).

    :ivar repeatability_db: :math:`u_1`, repeated determinations of
        :math:`L'_\mathrm{HT}` (A.3.2), in dB.
    :ivar equipment_db: :math:`u_2`, the audiometer (A.3.3), in dB; its
        distribution is rectangular, the others normal.
    :ivar transducer_db: :math:`u_3`, the transducer and its fitting (A.3.4),
        in dB.
    :ivar environment_db: :math:`u_4`, the ambient noise (A.3.5), in dB.
    :ivar masking_db: :math:`u_5`, a non-optimized masking noise (A.3.6), in
        dB.
    :ivar tester_db: :math:`u_6`, the tester's experience (A.3.7), in dB.
    :ivar subject_db: :math:`u_7`, the subject's responses (A.3.8), in dB.
    :ivar special_db: :math:`u_8`, an unusually difficult measurement (A.3.9),
        in dB.
    """

    repeatability_db: float
    equipment_db: float
    transducer_db: float
    environment_db: float
    masking_db: float = 0.0
    tester_db: float = 0.0
    subject_db: float = 0.0
    special_db: float = 0.0

    def __post_init__(self) -> None:
        """Refuse a component that is negative or not finite.

        :raises ValueError: for such a component.
        """
        for name, value in zip(self.labels, self.components_db, strict=True):
            if not math.isfinite(value) or value < 0.0:
                msg = f"the {name} component must be finite and not negative, in dB."
                raise ValueError(msg)

    @property
    def labels(self) -> tuple[str, ...]:
        """The eight input quantities of Table A.1, in its order.

        :return: Their symbols.
        """
        return (
            "L'_HT",
            "delta_eq",
            "delta_tr",
            "delta_n",
            "delta_m",
            "delta_te",
            "delta_su",
            "delta_pr",
        )

    @property
    def components_db(self) -> tuple[float, ...]:
        """The eight standard uncertainties in the order of Table A.1, in dB.

        :return: :math:`u_1` to :math:`u_8`.
        """
        return (
            float(self.repeatability_db),
            float(self.equipment_db),
            float(self.transducer_db),
            float(self.environment_db),
            float(self.masking_db),
            float(self.tester_db),
            float(self.subject_db),
            float(self.special_db),
        )

    @property
    def combined_db(self) -> float:
        r""":math:`u = \sqrt{\sum u_i^2}` (Formula (A.2)), in dB.

        :return: The combined standard uncertainty, unrounded.
        """
        return math.hypot(*self.components_db)

    @property
    def expanded_db(self) -> float:
        """:math:`U = 2u` for a coverage probability of 95 % (A.5), in dB.

        :return: The expanded uncertainty, unrounded; A.6 reports it rounded
            to the nearest full decibel.
        """
        return _COVERAGE_FACTOR * self.combined_db

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the eight contributions as bars, with the combined value.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the contribution bars.
        :return: The axes.
        """
        from .._plot.audiometry import plot_audiometric_uncertainty

        return plot_audiometric_uncertainty(self, ax=ax, language=language, **kwargs)


def audiometric_uncertainty(
    frequency: float,
    *,
    conduction: str = "air",
    masked: bool = False,
    level_step_db: float = 5.0,
    environment_db: float = _ENVIRONMENT_DB,
    tester_db: float = 0.0,
    subject_db: float = 0.0,
    special_db: float = 0.0,
) -> AudiometricUncertaintyBudget:
    r"""The typical uncertainty budget of a hearing threshold level (A.3).

    Fills Table A.1 with the values A.3 gives, which differ up to and above
    4 kHz:

    - :math:`u_1` (A.3.2): 2,5 dB and 4 dB for air conduction, 3 dB and 5 dB
      for bone conduction;
    - :math:`u_2` (A.3.3): the audiometer's maximum output deviation
      :math:`a` of IEC 60645-1 (±3 dB and ±5 dB for air, ±4 dB and ±5 dB for
      bone), rectangular, with the attenuator step :math:`s` rounding the
      level, also rectangular:

      .. math::

         u_2 = \sqrt{\left(\frac{a}{\sqrt{3}}\right)^2
         + \left(\frac{s}{2\sqrt{3}}\right)^2}

      which for air conduction up to 4 kHz and 5 dB steps is 2,3 dB;
    - :math:`u_3` (A.3.4): :math:`\sqrt{1{,}5^2 + 2{,}5^2}` = 2,9 dB up to
      4 kHz and :math:`\sqrt{2{,}5^2 + 3^2}` = 3,9 dB above;
    - :math:`u_4` (A.3.5): 2 dB when the ambient noise meets Clause 11 and the
      subject's threshold is near 0 dB. It may be negligible for thresholds
      well above 0 dB and is considerably larger in a room that exceeds the
      limits; give it with ``environment_db``;
    - :math:`u_5` (A.3.6): 2 dB when masking noise is applied;
    - :math:`u_6` to :math:`u_8` (A.3.7 to A.3.9): zero in usual situations,
      where the repeatability already covers them; give them when an
      exceptional situation calls for them.

    For air conduction below 4 kHz without masking this is the example of
    Table A.2: :math:`u` = 4,9 dB and :math:`U` = 10 dB.

    :param frequency: The test frequency, in hertz.
    :param conduction: ``"air"`` (default) or ``"bone"``.
    :param masked: Whether masking noise was applied (A.3.6).
    :param level_step_db: The step of the hearing level control, in dB; 5 by
        default, 0 for a control fine enough not to count.
    :param environment_db: :math:`u_4`, in dB; 2 by default (A.3.5).
    :param tester_db: :math:`u_6`, in dB.
    :param subject_db: :math:`u_7`, in dB.
    :param special_db: :math:`u_8`, in dB.
    :return: :class:`AudiometricUncertaintyBudget`.
    :raises ValueError: for an unknown conduction, a frequency that is not
        positive, or a component or step that is negative or not finite.
    """
    if conduction not in _CONDUCTIONS:
        msg = f"'conduction' must be one of {_CONDUCTIONS}; got {conduction!r}."
        raise ValueError(msg)
    f = float(frequency)
    if not math.isfinite(f) or f <= 0.0:
        msg = f"'frequency' must be a positive frequency in hertz; got {f:g}."
        raise ValueError(msg)
    step = float(level_step_db)
    if not math.isfinite(step) or step < 0.0:
        msg = f"'level_step_db' must be finite and not negative; got {step:g}."
        raise ValueError(msg)
    high = int(f > _UNCERTAINTY_SPLIT_HZ)
    deviation = _EQUIPMENT_DEVIATION_DB[conduction][high]
    root3 = math.sqrt(3.0)
    return AudiometricUncertaintyBudget(
        repeatability_db=_REPEATABILITY_DB[conduction][high],
        equipment_db=math.hypot(deviation / root3, step / (2.0 * root3)),
        transducer_db=math.hypot(
            _TRANSDUCER_TYPE_DB[high], _TRANSDUCER_FITTING_DB[high]
        ),
        environment_db=float(environment_db),
        masking_db=_MASKING_DB if masked else 0.0,
        tester_db=float(tester_db),
        subject_db=float(subject_db),
        special_db=float(special_db),
    )
