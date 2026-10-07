#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The sound field of an audiometric test room (ISO 8253-2:2009).

Sound field audiometry presents the test signal through one or more
loudspeakers instead of earphones, so the room becomes part of the
instrument. ISO 8253-2 specifies three sound fields a room may be qualified
as (Clause 5), each measured with the test subject and the chair absent and
with the same signals the audiometry will use (5.1):

- a **free sound field** (5.2): the loudspeaker at least 1 m from the
  reference point, the level 0,15 m to the left, right, above and below it
  within ±1 dB of the level at it up to and including 4 kHz and within ±2 dB
  above, the two ear-side positions within 3 dB of each other above 4 kHz,
  and the difference between the points 0,15 m in front of and behind it on
  the reference axis within ±1 dB of what the inverse distance law gives,

  .. math::

     \Delta L_\mathrm{theory} = 20 \lg \frac{r + d}{r - d}\ \mathrm{dB}

  with :math:`r` the distance from the loudspeaker to the reference point and
  :math:`d` = 0,15 m. Its NOTE says only an anechoic room meets it.
- a **quasi-free sound field** (5.4): the same arrangement with ±2 dB at the
  four lateral positions and the axial pair at :math:`d` = 0,10 m. Its usable
  frequency range is the range in which the requirements are met.
- a **diffuse sound field** (5.3): the level at six positions 0,15 m from the
  reference point, on the front-back, right-left and up-down axes, within
  ±2,5 dB of the level at it and the two ear-side positions within 3 dB of
  each other; from 500 Hz up, the levels a directional microphone reads at
  the reference point in the directions of the largest and the smallest
  incident energy stay within the variation Table 1 allows for the
  microphone's front-to-random sensitivity index (5 dB for an index of 5 dB
  or more, 4,5 dB for 4,5 dB, 4 dB for 4 dB, and a microphone below 4 dB is
  not suitable).

:func:`check_free_sound_field`, :func:`check_quasi_free_sound_field` and
:func:`check_diffuse_sound_field` judge those conditions band by band. The
diffuse-field judgement is the same one ISO 4869-3:2007, 5.2.2, asks of the
random-incidence field of its test site, with its own Table 1;
:func:`phonometry.hearing.check_random_incidence_field` runs it with that
table and returns the same :class:`DiffuseSoundFieldCheck`.

**The ambient noise (Clause 6, Table 2).** The maximum permissible ambient
sound pressure levels for sound field audiometry, in one-third-octave bands
from 31,5 Hz to 12,5 kHz, for a lowest test frequency of 125 Hz or 250 Hz,
are :data:`SOUND_FIELD_AMBIENT_LIMITS_DB`. Its footnote a says they are
derived from ISO 8253-1 for binaural listening, and prints no offset; laid
side by side, from 31,5 Hz to 8 kHz each cell is the bone-conduction limit of
ISO 8253-1:2010 Table 4 less 3 dB, an observation the library makes on the
two printed tables and not a figure the footnote gives. Footnote b asks for
lower limits, by an amount it does not print, when narrow-band noise is the
test signal.
:func:`phonometry.hearing.check_audiometric_ambient_noise` judges a measured
spectrum against them with ``presentation="sound field"``.

**Off-axis loudspeakers (Annex B, informative).** No standardized reference
threshold exists for a loudspeaker away from 0° incidence (4.8, NOTE 1).
Table B.1 prints how much higher the sound pressure level is at the ear
closest to the loudspeaker at 45° and 90°, rounded to the nearest 0,5 dB, which
:data:`INCIDENCE_CORRECTIONS_DB` carries and :func:`incidence_correction`
reads. The paragraph above the table announces it from 200 Hz; its rows start
at 125 Hz, and the library carries every printed row (see ``docs/ERRATA.md``).

Clause, table and annex numbers refer to ISO 8253-2:2009(E).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import require_choice
from .threshold import AUDIOMETRIC_FREQUENCIES as _AUDIOMETRIC_FREQUENCIES

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "DIFFUSE_FIELD_VARIATION_LIMITS",
    "INCIDENCE_CORRECTIONS_DB",
    "INCIDENCE_CORRECTION_FREQUENCIES_HZ",
    "SOUND_FIELD_AMBIENT_BANDS_HZ",
    "SOUND_FIELD_AMBIENT_LIMITS_DB",
    "DiffuseSoundFieldCheck",
    "FreeSoundFieldCheck",
    "check_diffuse_sound_field",
    "check_free_sound_field",
    "check_quasi_free_sound_field",
    "incidence_correction",
]

#: The one-third-octave mid-frequencies of Table 2, in hertz: 31,5 Hz to
#: 12,5 kHz, two bands beyond the 8 kHz at which the earphone tables of
#: ISO 8253-1 stop.
SOUND_FIELD_AMBIENT_BANDS_HZ: tuple[float, ...] = (
    31.5,
    40.0,
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
    12500.0,
)

#: Table 2: the maximum permissible ambient sound pressure levels
#: :math:`L_\mathrm{max}` for sound field audiometry, in dB re 20 µPa, one per
#: band of :data:`SOUND_FIELD_AMBIENT_BANDS_HZ`, keyed by the lowest test tone
#: frequency in hertz (125 or 250). They hold for a lowest hearing threshold
#: level of 0 dB with at most +2 dB of threshold shift from the ambient noise;
#: footnote a allows them 8 dB more for +5 dB, and Clause 6 adds the lowest
#: hearing threshold level to be measured when it is not 0 dB. Footnote b says
#: they should be lower when narrow-band noise is the test signal, and prints
#: no figure for how much, so they are the table as printed.
SOUND_FIELD_AMBIENT_LIMITS_DB: Mapping[float, np.ndarray] = MappingProxyType(
    {
        125.0: read_only(
            np.array(
                [52, 44, 38, 32, 27, 22, 17, 14, 12, 10, 8, 6, 5, 5, 4, 4, 4, 5, 5, 3]
                + [1, -1, 1, 6, 12, 14, 15],
                dtype=np.float64,
            )
        ),
        250.0: read_only(
            np.array(
                [60, 53, 46, 41, 36, 32, 25, 18, 12, 10, 8, 6, 5, 5, 4, 4, 4, 5, 5, 3]
                + [1, -1, 1, 6, 12, 14, 15],
                dtype=np.float64,
            )
        ),
    }
)

#: Table 1: the variation of the level at the reference point a directional
#: microphone may read between the directions of largest and smallest
#: incident energy, by its front-to-random sensitivity index. Each pair is
#: ``(lowest index, allowable variation)``, both in dB, from the most
#: directional microphone down: an index of 5 dB or more allows 5 dB, one of
#: 4,5 dB allows 4,5 dB and one of 4 dB allows 4 dB. Below 4 dB the table says
#: the microphone is not suitable. An index between two rows takes the lower
#: row, the one it is sure to reach.
DIFFUSE_FIELD_VARIATION_LIMITS: tuple[tuple[float, float], ...] = (
    (5.0, 5.0),
    (4.5, 4.5),
    (4.0, 4.0),
)

#: The two clauses that judge a diffuse field the same way, each with its own
#: Table 1.
_SOUND_FIELD_CLAUSE = "ISO 8253-2 5.3"
_RANDOM_INCIDENCE_CLAUSE = "ISO 4869-3 5.2.2"

#: The test frequencies of Table B.1, in hertz, 125 Hz to 12,5 kHz. The
#: paragraph above the table announces them from 200 Hz; the table prints
#: rows for 125 Hz and 160 Hz too, and they are kept.
INCIDENCE_CORRECTION_FREQUENCIES_HZ: tuple[float, ...] = (
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
    1500.0,
    1600.0,
    2000.0,
    2500.0,
    3000.0,
    3150.0,
    4000.0,
    5000.0,
    6000.0,
    6300.0,
    8000.0,
    10000.0,
    12500.0,
)

#: Table B.1: the increase in sound pressure level at the ear closest to the
#: loudspeaker when it is moved off axis, relative to 0° incidence, in dB and
#: rounded to the nearest 0,5 dB, one per frequency of
#: :data:`INCIDENCE_CORRECTION_FREQUENCIES_HZ`, keyed by the angle of
#: incidence in degrees (45 or 90). Informative (Annex B), from Shaw and
#: Vaillancourt (1985).
INCIDENCE_CORRECTIONS_DB: Mapping[float, np.ndarray] = MappingProxyType(
    {
        45.0: read_only(
            np.array(
                [0.5, 1, 1, 1, 1.5, 2.5, 3, 3.5, 3.5, 4, 4, 3.5, 3.5, 3, 3.5, 5]
                + [5, 4, 6, 7.5, 7.5, 5.5, 4.5, 1.5],
                dtype=np.float64,
            )
        ),
        90.0: read_only(
            np.array(
                [1, 1.5, 1.5, 2, 2.5, 3.5, 4.5, 5, 5, 5.5, 6, 5, 4.5, 2, 2, 2.5]
                + [2, -0.5, 4, 9.5, 10, 8.5, 6, 8],
                dtype=np.float64,
            )
        ),
    }
)

#: 5.2 a) and 5.4 a): the least distance from the loudspeaker to the
#: reference point, in metres.
_MINIMUM_LOUDSPEAKER_DISTANCE_M = 1.0
#: 5.2 c) and 5.4 c): the axial pair sits this far either side of the
#: reference point, in metres. The lateral positions of 5.2 b), 5.3 a) and
#: 5.4 b) are always 0,15 m from it and enter only as the levels read there.
_FREE_AXIS_OFFSET_M = 0.15
_QUASI_FREE_AXIS_OFFSET_M = 0.10
#: 5.2 b): the lateral tolerance up to and including this frequency is the
#: tighter one, and the right-left difference is limited above it.
_FREE_FIELD_SPLIT_HZ = 4000.0
_FREE_LOW_TOLERANCE_DB = 1.0
_FREE_HIGH_TOLERANCE_DB = 2.0
_QUASI_FREE_TOLERANCE_DB = 2.0
#: 5.2 b) and 5.3 a): the most the two ear-side positions may differ.
_LEFT_RIGHT_TOLERANCE_DB = 3.0
#: 5.2 c) and 5.4 c): the axial difference against the inverse distance law.
_INVERSE_DISTANCE_TOLERANCE_DB = 1.0
#: 5.3 a): the six positions against the level at the reference point.
_DIFFUSE_POSITION_TOLERANCE_DB = 2.5
#: 5.3 b): the directional test applies from this frequency up.
_DIRECTIONAL_FROM_HZ = 500.0
#: A limit reached through floating-point arithmetic, such as 95,3 dB less
#: 94,3 dB, is on the limit, not over it.
_BOUNDARY_SLACK_DB = 1e-9
#: A directional test needs at least two readings to have a spread.
_MINIMUM_DIRECTIONS = 2
#: The readings are a two-dimensional (directions, bands) grid.
_GRID_RANK = 2
#: Relative tolerance for matching a frequency to a tabulated one.
_FREQUENCY_RTOL = 1e-3

_LATERAL_POSITIONS: tuple[str, ...] = ("left", "right", "up", "down")
_DIFFUSE_POSITIONS: tuple[str, ...] = ("front", "back", "left", "right", "up", "down")


def _at_most(values: np.ndarray, bound: np.ndarray | float) -> np.ndarray:
    """Per element, whether ``values`` is at or below ``bound``.

    A last-bit excess from the subtraction of two levels is forgiven, and a
    NaN never qualifies.

    :param values: The values, in dB.
    :param bound: The bound, a number or one per value, in dB.
    :return: A boolean array of the shape of ``values``.
    """
    return np.asarray(values <= np.asarray(bound) + _BOUNDARY_SLACK_DB, dtype=bool)


def _band_values(values: ArrayLike, count: int | None, name: str) -> np.ndarray:
    """A one-dimensional array of finite decibel values, one per band.

    :param values: The values.
    :param count: The number of bands expected, or ``None`` to take it as is.
    :param name: The argument name, for the error message.
    :return: The values as a float array of its own, never the caller's.
    :raises ValueError: for a shape that does not fit or a value that is not
        finite.
    """
    array = np.array(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        msg = f"'{name}' must be a non-empty one-dimensional array of finite values."
        raise ValueError(msg)
    if count is not None and array.size != count:
        msg = f"'{name}' must hold one value per band; got {array.size} for {count}."
        raise ValueError(msg)
    return array


def _frequency_axis(
    frequencies: ArrayLike | None,
    count: int,
    owner: str,
    default: np.ndarray | tuple[float, ...],
) -> np.ndarray:
    """The frequencies of the test signals, or a default of the right length.

    :param frequencies: The caller's frequencies in hertz, or ``None``.
    :param count: How many bands the data carries.
    :param owner: The function name, for the error message.
    :param default: The frequencies assumed when none are given.
    :return: A float array of its own.
    :raises ValueError: if the count does not match, the frequencies are not
        positive, finite and increasing, or no frequencies are given and the
        default has another length.
    """
    if frequencies is None:
        fallback = np.array(default, dtype=np.float64)
        if fallback.size != count:
            msg = (
                f"{owner} needs 'frequencies' for {count} bands; without them it "
                f"assumes the {fallback.size} of "
                f"{fallback[0]:g} Hz to {fallback[-1]:g} Hz."
            )
            raise ValueError(msg)
        return fallback
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
            "increasing frequencies in hertz, one per band."
        )
        raise ValueError(msg)
    return freqs


def _position_grid(
    levels: Mapping[str, ArrayLike],
    positions: tuple[str, ...],
    count: int,
    name: str,
    clause: str,
) -> np.ndarray:
    """The levels at the named positions, one row per position.

    :param levels: The levels keyed by position name.
    :param positions: The names the clause requires, in row order.
    :param count: The number of bands.
    :param name: The argument name, for the error message.
    :param clause: The clause that names the positions, for the message.
    :return: A ``(positions, bands)`` float array.
    :raises ValueError: if a position is missing or unknown, or a row does not
        fit.
    """
    names = set(levels)
    if names != set(positions):
        msg = (
            f"'{name}' must give the positions of {clause}, "
            f"{', '.join(positions)}; got {', '.join(sorted(names)) or 'none'}."
        )
        raise ValueError(msg)
    return np.vstack(
        [_band_values(levels[p], count, f"{name}[{p!r}]") for p in positions]
    )


def _allowable_variation(
    index_db: np.ndarray, limits: tuple[tuple[float, float], ...]
) -> np.ndarray:
    """The allowable field variation per band by a Table 1, or NaN below it.

    :param index_db: The front-to-random sensitivity index per band, in dB.
    :param limits: ``(lowest index, allowable variation)`` rows, most
        directional first.
    :return: The allowable variation per band, NaN where the microphone is
        not suitable.
    """
    allowed = np.full(index_db.shape, np.nan)
    for lowest, variation in reversed(limits):
        allowed = np.where(
            np.isfinite(index_db) & (index_db >= lowest), variation, allowed
        )
    return allowed


def _variation_limits(standard: str) -> tuple[tuple[float, float], ...]:
    """The Table 1 a diffuse-field clause reads the microphone's index against.

    :param standard: ``"ISO 8253-2 5.3"`` or ``"ISO 4869-3 5.2.2"``.
    :return: ``(lowest index, allowable variation)`` rows, most directional
        first.
    :raises ValueError: for another clause.
    """
    if standard == _SOUND_FIELD_CLAUSE:
        return DIFFUSE_FIELD_VARIATION_LIMITS
    if standard == _RANDOM_INCIDENCE_CLAUSE:
        from .earmuff_insertion_loss import RANDOM_INCIDENCE_VARIATION_LIMITS

        return RANDOM_INCIDENCE_VARIATION_LIMITS
    msg = (
        f"'standard' must be {_SOUND_FIELD_CLAUSE!r} or "
        f"{_RANDOM_INCIDENCE_CLAUSE!r}; got {standard!r}."
    )
    raise ValueError(msg)


@dataclass(frozen=True)
class DiffuseSoundFieldCheck:
    r"""Whether a sound field is diffuse enough, band by band.

    The verdict of ISO 8253-2:2009, 5.3, and of the random-incidence field of
    ISO 4869-3:2007, 5.2.2, which ask the same two things and differ only in
    the Table 1 that turns a microphone's front-to-random sensitivity index
    into the variation it may read.

    :ivar frequencies: The centre frequencies of the test signals, in hertz.
    :ivar position_deviation_db: The level at each of the six positions
        0,15 m from the reference point less the level at it, one row per
        position in the order of :attr:`positions`, in dB.
    :ivar left_right_difference_db: The difference between the right and left
        positions per band, as an absolute value, in dB.
    :ivar directional_variation_db: The largest less the smallest level the
        directional microphone read at the reference point per band, in dB,
        or NaN where no reading was given or the band is below 500 Hz.
    :ivar front_to_random_index_db: The directional microphone's
        front-to-random sensitivity index per band, in dB, or ``None`` when
        no directional reading was given.
    :ivar standard: The clause this check applies, ``"ISO 8253-2 5.3"`` or
        ``"ISO 4869-3 5.2.2"``, which picks the Table 1 the index is read
        against.
    :ivar positions: The position names, in row order.

    What Table 1 allows the variation (:attr:`allowable_variation_db`) is read
    from the microphone's index and the standard's table, not stored, so a
    check cannot be built against another table.

    The directional test is a requirement, not an option: a band from 500 Hz
    up without a suitable microphone's reading is not judged,
    :attr:`directionality_judged` says so, and :attr:`passes` is ``False``
    until it is. :attr:`uniform` and :attr:`balanced` still give the verdict
    of the six positions on their own.
    """

    frequencies: np.ndarray
    position_deviation_db: np.ndarray
    left_right_difference_db: np.ndarray
    directional_variation_db: np.ndarray
    front_to_random_index_db: np.ndarray | None
    standard: str
    positions: tuple[str, ...] = _DIFFUSE_POSITIONS

    def __post_init__(self) -> None:
        """Reject a clause with no Table 1, or an index on other bands.

        :raises ValueError: for a standard other than the two that share this
            check, or an index that is not one value per band.
        """
        _variation_limits(self.standard)
        index = self.front_to_random_index_db
        if index is not None and np.shape(index) != np.shape(self.frequencies):
            msg = (
                "DiffuseSoundFieldCheck: 'front_to_random_index_db' must hold "
                "one index per band."
            )
            raise ValueError(msg)

    @property
    def allowable_variation_db(self) -> np.ndarray:
        """What the Table 1 allows the directional variation per band, in dB.

        :return: The allowance, or NaN where it is not judged: below 500 Hz,
            without a directional reading, or where the microphone's index is
            below the table's last row.
        """
        index = self.front_to_random_index_db
        if index is None:
            return np.full(np.shape(self.frequencies), np.nan)
        allowed = _allowable_variation(
            np.asarray(index, dtype=np.float64), _variation_limits(self.standard)
        )
        return np.where(self.directional_required, allowed, np.nan)

    @property
    def uniform(self) -> np.ndarray:
        """Per band, whether all six positions stay within ±2,5 dB.

        :return: One boolean per band.
        """
        return np.all(
            _at_most(
                np.abs(self.position_deviation_db), _DIFFUSE_POSITION_TOLERANCE_DB
            ),
            axis=0,
        )

    @property
    def balanced(self) -> np.ndarray:
        """Per band, whether right and left differ by 3 dB at most.

        :return: One boolean per band.
        """
        return _at_most(self.left_right_difference_db, _LEFT_RIGHT_TOLERANCE_DB)

    @property
    def directional_required(self) -> np.ndarray:
        """Per band, whether the directional test applies (500 Hz and up).

        :return: One boolean per band.
        """
        return np.asarray(self.frequencies >= _DIRECTIONAL_FROM_HZ, dtype=bool)

    @property
    def directional_judged(self) -> np.ndarray:
        """Per band, whether the directional test was judged.

        :return: ``True`` where a suitable microphone's reading was given,
            and below 500 Hz, where the test does not apply.
        """
        judged = np.isfinite(self.directional_variation_db) & np.isfinite(
            self.allowable_variation_db
        )
        return np.asarray(~self.directional_required | judged, dtype=bool)

    @property
    def diffuse(self) -> np.ndarray:
        """Per band, whether the directional variation stays within Table 1.

        Bands the test does not reach, below 500 Hz, count as meeting it; a
        band from 500 Hz up that was not judged reads ``False``.

        :return: One boolean per band.
        """
        within = _at_most(self.directional_variation_db, self.allowable_variation_db)
        return np.asarray(~self.directional_required | within, dtype=bool)

    @property
    def directionality_judged(self) -> bool:
        """Whether every band from 500 Hz up was judged by a suitable microphone.

        :return: ``True`` when none is left unjudged.
        """
        return bool(np.all(self.directional_judged))

    @property
    def passes(self) -> bool:
        """Whether the field qualifies as diffuse, every requirement judged.

        :return: ``True`` when every band meets the six positions, the
            right-left difference and the directional test.
        """
        return bool(
            np.all(self.uniform) and np.all(self.balanced) and np.all(self.diffuse)
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a DiffuseSoundFieldCheck has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each condition against its limit, band by band.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the worst position deviation curve.
        :return: The axes.
        """
        from .._plot.audiometry import plot_diffuse_sound_field

        return plot_diffuse_sound_field(self, ax=ax, language=language, **kwargs)


def _diffuse_field_check(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    directional_levels_db: ArrayLike | None,
    front_to_random_index_db: ArrayLike | None,
    frequencies: ArrayLike | None,
    default_frequencies: np.ndarray | tuple[float, ...],
    standard: str,
    owner: str,
) -> DiffuseSoundFieldCheck:
    """The diffuse-field judgement both ISO 8253-2 and ISO 4869-3 make.

    :param position_levels_db: The levels at the six positions, keyed by name.
    :param reference_levels_db: The level at the reference point per band.
    :param directional_levels_db: A ``(directions, bands)`` grid of the levels
        a directional microphone read at the reference point, or ``None``.
    :param front_to_random_index_db: That microphone's front-to-random
        sensitivity index, one number or one per band, in dB.
    :param frequencies: The centre frequencies, or ``None`` for the default.
    :param default_frequencies: The frequencies assumed when none are given.
    :param standard: The clause, which picks the Table 1 that applies.
    :param owner: The public function name, for the messages.
    :return: :class:`DiffuseSoundFieldCheck`.
    :raises ValueError: for positions that are missing or unknown, bands that
        do not match, a directional reading without its index or the other way
        round, a single index below the table's last row, or fewer than two
        finite readings in a band from 500 Hz up.
    """
    reference = _band_values(reference_levels_db, None, "reference_levels_db")
    count = reference.size
    levels = _position_grid(
        position_levels_db, _DIFFUSE_POSITIONS, count, "position_levels_db", standard
    )
    freqs = _frequency_axis(frequencies, count, owner, default_frequencies)
    deviation = levels - reference[None, :]
    left = levels[_DIFFUSE_POSITIONS.index("left")]
    right = levels[_DIFFUSE_POSITIONS.index("right")]
    variation, index = _directional_variation(
        directional_levels_db,
        front_to_random_index_db,
        freqs,
        limits=_variation_limits(standard),
        standard=standard,
    )
    return DiffuseSoundFieldCheck(
        frequencies=freqs,
        position_deviation_db=deviation,
        left_right_difference_db=np.abs(right - left),
        directional_variation_db=variation,
        front_to_random_index_db=index,
        standard=standard,
    )


def _directional_variation(
    directional_levels_db: ArrayLike | None,
    front_to_random_index_db: ArrayLike | None,
    freqs: np.ndarray,
    *,
    limits: tuple[tuple[float, float], ...],
    standard: str,
) -> tuple[np.ndarray, np.ndarray | None]:
    """The directional test: the spread of the readings and the index per band.

    Per band, from 500 Hz up: the largest less the smallest level a
    directional microphone read at the reference point, NaN below 500 Hz and
    in every band when no directional reading is given; and the
    microphone's front-to-random sensitivity index per band, ``None`` when
    no directional reading is given.

    :raises ValueError: for a directional reading without its index or the
        other way round, an index that is not one number or one per band, a
        single index below the table's last row, a grid on other bands, or
        fewer than two finite readings in a band from 500 Hz up.
    """
    count = freqs.size
    variation = np.full(count, np.nan)
    if (directional_levels_db is None) != (front_to_random_index_db is None):
        msg = (
            "give 'directional_levels_db' and 'front_to_random_index_db' "
            "together: Table 1 sets the limit by the microphone's index."
        )
        raise ValueError(msg)
    if directional_levels_db is None or front_to_random_index_db is None:
        return variation, None
    index = _front_to_random_index(front_to_random_index_db, count, limits, standard)
    readings = np.asarray(directional_levels_db, dtype=np.float64)
    if readings.ndim != _GRID_RANK or readings.shape[1] != count:
        msg = (
            "'directional_levels_db' must be a (directions, bands) grid on "
            f"the same {count} bands."
        )
        raise ValueError(msg)
    required = freqs >= _DIRECTIONAL_FROM_HZ
    judged = readings[:, required]
    if judged.shape[0] < _MINIMUM_DIRECTIONS or not np.all(np.isfinite(judged)):
        msg = (
            "'directional_levels_db' needs at least two finite readings in "
            "every band from 500 Hz up."
        )
        raise ValueError(msg)
    variation[required] = judged.max(axis=0) - judged.min(axis=0)
    return variation, index


def _front_to_random_index(
    front_to_random_index_db: ArrayLike,
    count: int,
    limits: tuple[tuple[float, float], ...],
    standard: str,
) -> np.ndarray:
    """The microphone's front-to-random sensitivity index, one per band.

    :raises ValueError: for a single index below the table's last row, or an
        index that is not one number or one per band.
    """
    index = np.array(front_to_random_index_db, dtype=np.float64)
    if index.ndim == 0:
        lowest = limits[-1][0]
        if not math.isfinite(float(index)) or float(index) < lowest:
            msg = (
                f"a front-to-random sensitivity index of {float(index):g} dB "
                f"is below {lowest:g} dB, for which Table 1 of {standard} "
                "says the microphone is not suitable."
            )
            raise ValueError(msg)
        return np.full(count, float(index))
    if index.shape != (count,):
        msg = (
            "'front_to_random_index_db' must be one number or one per band, "
            f"{count} values."
        )
        raise ValueError(msg)
    return index


def check_diffuse_sound_field(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    directional_levels_db: ArrayLike | None = None,
    front_to_random_index_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> DiffuseSoundFieldCheck:
    r"""Is the sound field of the test room diffuse? (ISO 8253-2, 5.3).

    Measured with the test subject and the chair absent, with the signals the
    audiometry will use:

    - a) the level at each of the six positions 0,15 m from the reference
      point, front and back, left and right, up and down, read with an
      omnidirectional microphone kept in one orientation, stays within
      ±2,5 dB of the level at the reference point, and the extreme right and
      left positions within 3 dB of each other;
    - b) from 500 Hz up, the levels a directional microphone reads at the
      reference point in the directions of the largest and smallest incident
      energy stay within the variation Table 1 allows for its front-to-random
      sensitivity index (:data:`DIFFUSE_FIELD_VARIATION_LIMITS`).

    The readings of b) are taken in as many directions as the microphone and
    the loudspeakers need, including the two planes where the extremes are
    expected (footnote a); the variation is the largest less the smallest of
    them.

    :param position_levels_db: The level at each position per test signal, in
        dB, keyed ``"front"``, ``"back"``, ``"left"``, ``"right"``, ``"up"``
        and ``"down"``.
    :param reference_levels_db: The level at the reference point per test
        signal, in dB.
    :param directional_levels_db: The levels the directional microphone read
        at the reference point, a ``(directions, bands)`` grid in dB on the
        same band axis; bands below 500 Hz are not read and may be NaN.
        ``None`` leaves b) unjudged, and the verdict then does not pass.
    :param front_to_random_index_db: The microphone's front-to-random
        sensitivity index, in dB, one number or one per band; required with
        ``directional_levels_db``. A band where it is below 4 dB, or NaN, is
        left unjudged, since Table 1 says the microphone is not suitable
        there.
    :param frequencies: The frequencies of the test signals, in hertz, or
        ``None`` for the eleven audiometric frequencies from 125 Hz to 8 kHz.
    :return: :class:`DiffuseSoundFieldCheck`.
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
        default_frequencies=_AUDIOMETRIC_FREQUENCIES,
        standard=_SOUND_FIELD_CLAUSE,
        owner="check_diffuse_sound_field",
    )


@dataclass(frozen=True)
class FreeSoundFieldCheck:
    r"""Whether a free or quasi-free sound field is met, band by band.

    The verdict of ISO 8253-2:2009, 5.2 (free) or 5.4 (quasi-free).

    :ivar field: ``"free"`` or ``"quasi-free"``.
    :ivar frequencies: The frequencies of the test signals, in hertz.
    :ivar lateral_deviation_db: The level at each of the four positions
        0,15 m from the reference point less the level at it, one row per
        position in the order of :attr:`positions`, in dB.
    :ivar axis_difference_db: The level at the axial point in front of the
        reference point, towards the loudspeaker, less the level at the one
        behind it, per band, in dB.
    :ivar loudspeaker_distance_m: :math:`r`, the distance from the loudspeaker
        to the reference point, in metres.
    :ivar positions: The lateral position names, in row order.

    Where the axial points sit (:attr:`axis_offset_m`) is the clause's, and
    so is the difference the inverse distance law gives there
    (:attr:`inverse_distance_difference_db`): both are read from the field and
    the loudspeaker distance and are not fields, so a check cannot be built
    against another offset or another law.
    """

    field: str
    frequencies: np.ndarray
    lateral_deviation_db: np.ndarray
    axis_difference_db: np.ndarray
    loudspeaker_distance_m: float
    positions: tuple[str, ...] = _LATERAL_POSITIONS

    def __post_init__(self) -> None:
        """Refuse a field the clause does not name or a loudspeaker inside it.

        :raises ValueError: If the field is not ``"free"`` or
            ``"quasi-free"``, or the loudspeaker is not farther from the
            reference point than the axial points.
        """
        require_choice(self.field, "field", ("free", "quasi-free"))
        distance = float(self.loudspeaker_distance_m)
        if not math.isfinite(distance) or distance <= self.axis_offset_m:
            msg = (
                "FreeSoundFieldCheck: 'loudspeaker_distance_m' must be a finite "
                f"distance larger than the {self.axis_offset_m:g} m of the axial "
                f"points; got {distance:g} m."
            )
            raise ValueError(msg)

    @property
    def axis_offset_m(self) -> float:
        """:math:`d`, how far the axial points sit from the reference point.

        :return: 0,15 m for a free field (5.2 c)), 0,10 m for a quasi-free one
            (5.4 c)), in metres.
        """
        return (
            _FREE_AXIS_OFFSET_M if self.field == "free" else _QUASI_FREE_AXIS_OFFSET_M
        )

    @property
    def inverse_distance_difference_db(self) -> float:
        r"""What the inverse distance law gives for the axial difference, in dB.

        :return: :math:`20 \lg((r + d)/(r - d))` with :math:`r` the loudspeaker
            distance and :math:`d` the axial offset.
        """
        r, d = float(self.loudspeaker_distance_m), self.axis_offset_m
        return 20.0 * math.log10((r + d) / (r - d))

    @property
    def lateral_tolerance_db(self) -> np.ndarray:
        """The tolerance of the four lateral positions per band, in dB.

        :return: ±1 dB up to and including 4 kHz and ±2 dB above for a free
            field (5.2 b)), ±2 dB throughout for a quasi-free one (5.4 b)).
        """
        if self.field == "quasi-free":
            return np.full(self.frequencies.size, _QUASI_FREE_TOLERANCE_DB)
        return np.where(
            self.frequencies <= _FREE_FIELD_SPLIT_HZ,
            _FREE_LOW_TOLERANCE_DB,
            _FREE_HIGH_TOLERANCE_DB,
        )

    @property
    def uniform(self) -> np.ndarray:
        """Per band, whether all four lateral positions stay within tolerance.

        :return: One boolean per band.
        """
        return np.all(
            _at_most(
                np.abs(self.lateral_deviation_db), self.lateral_tolerance_db[None, :]
            ),
            axis=0,
        )

    @property
    def left_right_difference_db(self) -> np.ndarray:
        """The difference between the right and left positions, in dB.

        :return: Its absolute value per band.
        """
        left = self.lateral_deviation_db[self.positions.index("left")]
        right = self.lateral_deviation_db[self.positions.index("right")]
        return np.asarray(np.abs(right - left), dtype=np.float64)

    @property
    def balanced(self) -> np.ndarray:
        """Per band, whether right and left differ by 3 dB at most above 4 kHz.

        5.2 b) asks it of a free field above 4 kHz only; below, and for a
        quasi-free field, the band reads ``True``.

        :return: One boolean per band.
        """
        if self.field == "quasi-free":
            return np.ones(self.frequencies.size, dtype=bool)
        within = _at_most(self.left_right_difference_db, _LEFT_RIGHT_TOLERANCE_DB)
        return np.asarray(
            (self.frequencies <= _FREE_FIELD_SPLIT_HZ) | within, dtype=bool
        )

    @property
    def inverse_distance_deviation_db(self) -> np.ndarray:
        """The axial difference less what the inverse distance law gives, in dB.

        :return: One value per band.
        """
        return self.axis_difference_db - self.inverse_distance_difference_db

    @property
    def follows_inverse_distance_law(self) -> np.ndarray:
        """Per band, whether the axial difference is within ±1 dB of the law.

        :return: One boolean per band.
        """
        return _at_most(
            np.abs(self.inverse_distance_deviation_db), _INVERSE_DISTANCE_TOLERANCE_DB
        )

    @property
    def distance_adequate(self) -> bool:
        """Whether the loudspeaker is at least 1 m from the reference point.

        :return: ``True`` when 5.2 a) or 5.4 a) is met.
        """
        return self.loudspeaker_distance_m >= _MINIMUM_LOUDSPEAKER_DISTANCE_M

    @property
    def compliant(self) -> np.ndarray:
        """Per band, whether every positional requirement is met.

        :return: One boolean per band.
        """
        return np.asarray(
            self.uniform & self.balanced & self.follows_inverse_distance_law,
            dtype=bool,
        )

    @property
    def usable_frequencies(self) -> np.ndarray:
        """The frequencies at which the field meets its requirements, in hertz.

        For a quasi-free field this is its usable frequency range (5.4).

        :return: The frequencies of the compliant bands.
        """
        return np.asarray(self.frequencies[self.compliant], dtype=np.float64)

    @property
    def passes(self) -> bool:
        """Whether the field qualifies at every test frequency given.

        :return: ``True`` when the loudspeaker distance and every band meet
            the clause.
        """
        return bool(self.distance_adequate and np.all(self.compliant))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a FreeSoundFieldCheck has no truth value; read its '.passes' for "
            "the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the lateral and axial conditions against their limits.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the worst lateral deviation curve.
        :return: The axes.
        """
        from .._plot.audiometry import plot_free_sound_field

        return plot_free_sound_field(self, ax=ax, language=language, **kwargs)


def _free_field_check(
    lateral_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    front_levels_db: ArrayLike,
    back_levels_db: ArrayLike,
    loudspeaker_distance_m: float,
    frequencies: ArrayLike | None,
    field: str,
    owner: str,
) -> FreeSoundFieldCheck:
    """The free or quasi-free judgement of 5.2 or 5.4.

    :param lateral_levels_db: The levels at the four lateral positions.
    :param reference_levels_db: The level at the reference point per band.
    :param front_levels_db: The level on the axis towards the loudspeaker.
    :param back_levels_db: The level on the axis away from it.
    :param loudspeaker_distance_m: The distance to the reference point.
    :param frequencies: The frequencies, or ``None`` for the default.
    :param field: ``"free"`` or ``"quasi-free"``.
    :param owner: The public function name, for the messages.
    :return: :class:`FreeSoundFieldCheck`.
    :raises ValueError: for positions that are missing or unknown, bands that
        do not match, or a distance that is not larger than the axial offset.
    """
    clause = "ISO 8253-2 5.2" if field == "free" else "ISO 8253-2 5.4"
    offset = _FREE_AXIS_OFFSET_M if field == "free" else _QUASI_FREE_AXIS_OFFSET_M
    distance = float(loudspeaker_distance_m)
    if not math.isfinite(distance) or distance <= offset:
        msg = (
            f"'loudspeaker_distance_m' must be a finite distance larger than the "
            f"{offset:g} m of the axial points of {clause}; got {distance:g} m."
        )
        raise ValueError(msg)
    reference = _band_values(reference_levels_db, None, "reference_levels_db")
    count = reference.size
    lateral = _position_grid(
        lateral_levels_db, _LATERAL_POSITIONS, count, "lateral_levels_db", clause
    )
    front = _band_values(front_levels_db, count, "front_levels_db")
    back = _band_values(back_levels_db, count, "back_levels_db")
    freqs = _frequency_axis(frequencies, count, owner, _AUDIOMETRIC_FREQUENCIES)
    return FreeSoundFieldCheck(
        field=field,
        frequencies=freqs,
        lateral_deviation_db=lateral - reference[None, :],
        axis_difference_db=front - back,
        loudspeaker_distance_m=distance,
    )


def check_free_sound_field(
    lateral_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    front_levels_db: ArrayLike,
    back_levels_db: ArrayLike,
    loudspeaker_distance_m: float,
    frequencies: ArrayLike | None = None,
) -> FreeSoundFieldCheck:
    r"""Is the sound field of the test room free? (ISO 8253-2, 5.2).

    Measured with the test subject and the chair absent, the loudspeaker at
    the head height of a seated listener with its reference axis through the
    reference point:

    - a) the loudspeaker is at least 1 m from the reference point;
    - b) the level 0,15 m from the reference point to the left, right, above
      and below it stays within ±1 dB of the level at it up to and including
      4 kHz and within ±2 dB above, and above 4 kHz the right and left
      positions differ by 3 dB at most;
    - c) the level at the point 0,15 m in front of the reference point on the
      reference axis less the level 0,15 m behind it stays within ±1 dB of the
      inverse distance law,

      .. math::

         \Delta L_\mathrm{theory} = 20 \lg \frac{r + 0{,}15\ \mathrm{m}}
         {r - 0{,}15\ \mathrm{m}}\ \mathrm{dB}

      with :math:`r` the distance from the loudspeaker to the reference
      point, the point source the law assumes.

    Pure tones may only be used in a field that meets this (4.2), and the NOTE
    to 5.2 says only an anechoic room does.

    :param lateral_levels_db: The level at each lateral position per test
        signal, in dB, keyed ``"left"``, ``"right"``, ``"up"`` and ``"down"``.
    :param reference_levels_db: The level at the reference point per test
        signal, in dB.
    :param front_levels_db: The level on the reference axis 0,15 m in front of
        the reference point, towards the loudspeaker, in dB.
    :param back_levels_db: The level 0,15 m behind it, in dB.
    :param loudspeaker_distance_m: :math:`r`, in metres. A distance under 1 m
        is judged, not refused: the verdict fails a).
    :param frequencies: The test frequencies, in hertz, or ``None`` for the
        eleven audiometric frequencies from 125 Hz to 8 kHz.
    :return: :class:`FreeSoundFieldCheck`.
    :raises ValueError: if a position is missing or unknown, if the bands do
        not match, or if the distance is not larger than 0,15 m.
    """
    return _free_field_check(
        lateral_levels_db,
        reference_levels_db,
        front_levels_db=front_levels_db,
        back_levels_db=back_levels_db,
        loudspeaker_distance_m=loudspeaker_distance_m,
        frequencies=frequencies,
        field="free",
        owner="check_free_sound_field",
    )


def check_quasi_free_sound_field(
    lateral_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    front_levels_db: ArrayLike,
    back_levels_db: ArrayLike,
    loudspeaker_distance_m: float,
    frequencies: ArrayLike | None = None,
) -> FreeSoundFieldCheck:
    r"""Is the sound field of the test room quasi-free? (ISO 8253-2, 5.4).

    The field a room that is not anechoic can still offer, measured with the
    test subject and the chair absent and all other working conditions kept:

    - a) the loudspeaker's reference point is at least 1 m from the
      reference point;
    - b) the level 0,15 m from the reference point to the left, right, above
      and below it stays within ±2 dB of the level at it;
    - c) the level 0,10 m in front of the reference point on the reference
      axis less the level 0,10 m behind it stays within ±1 dB of the inverse
      distance law,

      .. math::

         \Delta L_\mathrm{theory} = 20 \lg \frac{r + 0{,}10\ \mathrm{m}}
         {r - 0{,}10\ \mathrm{m}}\ \mathrm{dB}

    The usable frequency range of the field is the range in which these hold,
    which :attr:`FreeSoundFieldCheck.usable_frequencies` gives.

    :param lateral_levels_db: The level at each lateral position per test
        signal, in dB, keyed ``"left"``, ``"right"``, ``"up"`` and ``"down"``.
    :param reference_levels_db: The level at the reference point per test
        signal, in dB.
    :param front_levels_db: The level on the reference axis 0,10 m in front of
        the reference point, towards the loudspeaker, in dB.
    :param back_levels_db: The level 0,10 m behind it, in dB.
    :param loudspeaker_distance_m: :math:`r`, in metres. A distance under 1 m
        is judged, not refused: the verdict fails a).
    :param frequencies: The test frequencies, in hertz, or ``None`` for the
        eleven audiometric frequencies from 125 Hz to 8 kHz.
    :return: :class:`FreeSoundFieldCheck` with ``field="quasi-free"``.
    :raises ValueError: if a position is missing or unknown, if the bands do
        not match, or if the distance is not larger than 0,10 m.
    """
    return _free_field_check(
        lateral_levels_db,
        reference_levels_db,
        front_levels_db=front_levels_db,
        back_levels_db=back_levels_db,
        loudspeaker_distance_m=loudspeaker_distance_m,
        frequencies=frequencies,
        field="quasi-free",
        owner="check_quasi_free_sound_field",
    )


def incidence_correction(
    frequencies: ArrayLike, *, incidence_angle_deg: float
) -> np.ndarray:
    """How much louder the nearer ear is with the loudspeaker off axis (Table B.1).

    The increase in sound pressure level at the ear closest to the
    loudspeaker at 45° or 90° incidence, relative to 0°, rounded to the
    nearest 0,5 dB as Annex B prints it. The annex is informative and says
    no standardized reference threshold exists for these angles (4.8,
    NOTE 1); how a report uses the increase is left to it.

    :param frequencies: Test frequencies in hertz, each one of
        :data:`INCIDENCE_CORRECTION_FREQUENCIES_HZ`.
    :param incidence_angle_deg: 45 or 90.
    :return: The increase per frequency, in dB.
    :raises ValueError: for another angle, or a frequency Table B.1 does not
        list.
    """
    angle = float(incidence_angle_deg)
    column = next(
        (
            values
            for key, values in INCIDENCE_CORRECTIONS_DB.items()
            if math.isclose(angle, key)
        ),
        None,
    )
    if column is None:
        msg = (
            "'incidence_angle_deg' must be 45 or 90, the two angles Table B.1 "
            f"prints; got {angle:g}."
        )
        raise ValueError(msg)
    freqs = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    table = np.asarray(INCIDENCE_CORRECTION_FREQUENCIES_HZ, dtype=np.float64)
    out = np.empty(freqs.shape, dtype=np.float64)
    for position, f in np.ndenumerate(freqs):
        matches = np.isclose(table, f, rtol=_FREQUENCY_RTOL, atol=0.0)
        if not matches.any():
            msg = (
                f"{f:g} Hz is not a test frequency of Table B.1 (125 Hz to 12 500 Hz)."
            )
            raise ValueError(msg)
        out[position] = column[int(np.argmax(matches))]
    return out
