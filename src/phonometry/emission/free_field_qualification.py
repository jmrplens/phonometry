#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Qualification of an anechoic or hemi-anechoic room by the inverse square
law: ISO 26101:2017, with the criteria of ISO 3745:2012 Annex A as
Amendment 1:2017 rewrote it.

A free field is judged by how the level falls away from a small source. Along
each straight microphone traverse the measured level :math:`L_{pi}` at the
distance :math:`r_i` from the mathematical origin of the traverse is compared
with the inverse square law

.. math::

   L_p(r_i) = b - 20 \lg\frac{r_i}{r_0}\ \mathrm{dB}, \qquad r_0 = 1\ \mathrm{m}
   \tag{ISO 26101 Formula (2)}

and the deviation at every point is

.. math::

   \Delta L_{pi} = L_{pi} - L_p(r_i) \tag{ISO 26101 Formula (4)}

where :math:`L_{pi}` has been corrected for the stability of the source with
the monitor microphone,
:math:`L_{pi} = L'_{pi} - L_{p,\mathrm{ref},i} + L_{p,\mathrm{ref},0}`
(Formula (1)). The room is qualified out to the largest distance from the
origin at which every deviation, on every traverse and at every frequency,
stays inside the limits of Table A.1 (the same table in ISO 26101 Annex A and
in the amended ISO 3745 Annex A): :math:`\pm 1{,}5`, :math:`\pm 1{,}0` and
:math:`\pm 1{,}5` dB in an anechoic room for the one-third octave bands up to
630 Hz, from 800 Hz to 5 000 Hz and from 6 300 Hz up, and :math:`\pm 2{,}5`,
:math:`\pm 2{,}0` and :math:`\pm 3{,}0` dB in a hemi-anechoic one.

**The fit of b.** Formula (2) leaves the source strength :math:`b` free: it
"is adjusted to optimize the fit of the measured sound pressure levels into
the tolerance range, to maximize the qualified distance from the test sound
source". Note 1 offers the mean of :math:`L_{pi} + 20 \lg(r_i/r_0)` as a
starting value for an iterative search (Formula (3)); no source prints the
search. This module does not iterate, because the problem it poses has an
exact answer. Write :math:`y_i = L_{pi} + 20 \lg(r_i/r_0)`, so that
:math:`\Delta L_{pi} = y_i - b`. The points out to a distance :math:`R` fit
inside :math:`\pm t` for *some* :math:`b` exactly when the spread of their
:math:`y_i` is at most :math:`2t`, and the spread over the points nearer than
:math:`R` can only grow with :math:`R`. So, for one traverse and one
frequency, the qualified distance is the distance of the last point of the
longest run from the origin whose :math:`y` spread stays within :math:`2t`,
and every :math:`b` in :math:`[\max y - t,\ \min y + t]` over that run
qualifies it. Of those the module takes the midpoint,
:math:`b = (\max y + \min y)/2`, the one that leaves the same margin to both
limits and so the smallest largest deviation. A qualified distance cannot be
extended by any other :math:`b`, and no search can find a longer one.

**The mathematical origin.** ISO 26101:2017 5.1.3.2 and the amended ISO 3745
A.3.3 require every traverse to share one mathematical origin, and that origin
to lie within the physical volume the test source occupies; the 2012 annex
had instead fitted a collinear acoustic-centre offset per traverse. Given a
fixed origin, the distances follow from the measured positions. Given the box
the source occupies, the origin is searched inside it for the largest radius
of A.2.4, the smallest qualified distance over every traverse and every
frequency, since that is the distance Formula (2) asks :math:`b` to maximize
and A.2.4 defines from the origin. A qualified distance ends either where a
deviation leaves Table A.1, which the room decides, or at the last point
measured, which the measurement decides; moving the origin inside the box
moves the distance to that last point by as much as the origin moves, which
says nothing about the room. So the search ranks origins by that smallest
distance with every run that reaches its last point counted at the distance
of that point from the centre of the box, the same for every origin: radii
then differ only where the room ends a run, and radii within the 1 mm to
which the search resolves the origin count as equal. Ties are broken by how
much of the Table A.1 band the curves fill on average (the mean over every
traverse and frequency of the half spread of :math:`y_i` as a share of its
limit), then by the nearer point to the centre of the box; the mean, rather
than the worst band, keeps one band from dragging the origin to the edge of
the source at the others' expense when nothing else separates two origins.
In an exact inverse-square field every run reaches its last point, the
curves are flattest seen from the point the field diverges from, and the
search returns that point. The radius reported is always the distance from
the origin returned. The search is a regular lattice of five points per axis
followed by a compass search that halves its step down to 1 mm; it is
deterministic, stays inside the box by construction and never returns a
worse origin than the best lattice point.

**What the verdict judges.** :func:`check_free_field` holds the qualification
to the amended ISO 3745 Annex A and to the clauses of ISO 26101 it defers to:
the deviations of A.2.2 and the radius of A.2.4; the frequencies of A.2.3
(100 Hz to 10 000 Hz, one-third octave bands below 125 Hz and above 4 000 Hz
and octave mid-band frequencies between); five to eight traverses (A.3.3),
towards the five targets a) to e) of A.3.3 and in the working area, within
the angular limits of the source directionality in a hemi-anechoic room; at
least 10 points on each traverse and 50 in total within the radius, equally
spaced at each frequency, and spaced at most a tenth of a wavelength below
250 Hz and 100 mm above (A.4.3); the spatial resolution of ISO 26101 A.4.3
and the traverse length of ISO 26101 5.1.4.3, which A.2.4 cites; the 6 dB
above background of ISO 26101 5.1.2.2 c); the directionality of the test
source (ISO 26101 Annex B, :func:`verify_source_directionality`); and, in a
hemi-anechoic room, the reflecting plane of A.2.5. A requirement whose data
were not given is listed in :attr:`FreeFieldCheck.not_judged`, and the
verdict does not pass until it is judged.

Two readings are this module's, since no source settles them. The spacing
rules of A.4.3 name a frequency below which a tenth of a wavelength applies
and above which a fixed length does (250 Hz and 100 mm in the amended
ISO 3745, 1 kHz and 25 mm in ISO 26101), and neither says which holds at the
edge itself; the one-third octave band that contains the edge frequency is
held to the stricter of the two. And "equally spaced" comes with no
tolerance: the points within the radius are equally spaced when, walking out
from the first, every next point of the grid lies within a tenth of the
median gap of where one step would put it. Points between two of them are
the additional measurements the last paragraph of A.4.3 recommends near a
peak deviation, and do not break the grid.
"""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from functools import partial
from itertools import product
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.frozen import read_only_copy
from .._internal.validation import require_finite, require_positive

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

FreeFieldRoom = Literal["anechoic", "hemi-anechoic"]
QualificationBandwidth = Literal["discrete-frequency", "broadband"]

_ROOMS: tuple[str, ...] = ("anechoic", "hemi-anechoic")
#: ISO 3745:2012/Amd.1:2017 A.3.3 a) to e): at least one traverse path towards
#: a dihedral corner, one towards a trihedral corner, one towards the centre of
#: the most uniform boundary surface, one towards the closest boundary surface
#: and one towards the boundary surfaces with unique features.
_PATH_TARGETS: tuple[str, ...] = (
    "dihedral corner",
    "trihedral corner",
    "boundary centre",
    "closest boundary",
    "unique features",
)
_BANDWIDTHS: tuple[str, ...] = ("discrete-frequency", "broadband")

#: Reference distance of Formula (2), in metres.
_R0_M = 1.0

#: ISO 26101:2017 Table A.1 and ISO 3745:2012/Amd.1:2017 Table A.1 (the two
#: print the same cells): allowable deviation from the inverse square law, in
#: decibels, for the one-third octave bands up to 630 Hz, from 800 Hz to
#: 5 000 Hz and from 6 300 Hz up.
_TABLE_A1_DB: dict[str, tuple[float, float, float]] = {
    "anechoic": (1.5, 1.0, 1.5),
    "hemi-anechoic": (2.5, 2.0, 3.0),
}

#: ISO 26101:2017 Table B.1: allowable deviation of the test source
#: directionality, in decibels, for the bands up to 630 Hz, 800 Hz to 5 000 Hz,
#: 6 300 Hz to 10 000 Hz and above 10 000 Hz.
_TABLE_B1_DB: dict[str, tuple[float, float, float, float]] = {
    "anechoic": (1.5, 2.0, 2.5, 5.0),
    "hemi-anechoic": (2.0, 2.5, 3.0, 5.0),
}

#: One-third octave band indices (0 is 1 kHz, 10 lg(f / 1 kHz) rounded) of the
#: band edges the two tables use: 630 Hz, 800 Hz, 5 000 Hz, 6 300 Hz, 10 kHz.
_K_630 = -2
_K_5000 = 7
_K_10000 = 10

#: ISO 266 nominal one-third octave mid-band frequencies from 10 Hz to 40 kHz,
#: indexed from band -20 (10 Hz) to band 16 (40 kHz).
_NOMINAL_THIRDS_HZ: tuple[float, ...] = (
    10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0,
    100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0,
    1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0,
    8000.0, 10000.0, 12500.0, 16000.0, 20000.0, 25000.0, 31500.0, 40000.0,
)  # fmt: skip
_LOWEST_K = -20

#: ISO 3745:2012/Amd.1:2017 A.2.3: the frequency range to be qualified is at
#: least 100 Hz (band -10) to 10 000 Hz (band 10); below 125 Hz (band -9) and
#: above 4 000 Hz (band 6) every one-third octave band is evaluated, between
#: them the octave mid-band frequencies (every third band).
_K_CORE_LOW = -10
_K_CORE_HIGH = 10
_K_OCTAVE_LOW = -9
_K_OCTAVE_HIGH = 6
_OCTAVE_STEP = 3

#: A.3.3: at least five and not more than eight traverse paths.
_MIN_TRAVERSES = 5
_MAX_TRAVERSES = 8
#: A.4.3: at least 10 points on each traverse and 50 in total within the
#: qualified radius.
_MIN_POINTS_PER_TRAVERSE = 10
_MIN_POINTS_TOTAL = 50
#: A.4.3 (amended ISO 3745): a tenth of a wavelength below 250 Hz (band -6),
#: 100 mm above it.
_K_250 = -6
_SPACING_ISO3745_M = 0.100
#: ISO 26101:2017 A.4.3: a tenth of a wavelength below 1 kHz (band 0), 25 mm
#: above it.
_K_1000 = 0
_SPACING_ISO26101_M = 0.025
_WAVELENGTH_FRACTION_SPACING = 10.0
#: A.4.3 and ISO 26101 5.1.4.3: equally spaced points at each frequency. No
#: source prints a tolerance: the next point of the grid lies within a tenth of
#: the median gap of where one step from the last one puts it.
_EQUAL_SPACING_TOLERANCE = 0.1
#: ISO 26101:2017 5.1.4.3: start at most, and traverse at least, a quarter of
#: the wavelength at the lowest frequency to be qualified.
_WAVELENGTH_FRACTION_LENGTH = 4.0
#: ISO 26101:2017 5.1.2.2 c): the levels at least 6 dB above the background.
_MIN_BACKGROUND_MARGIN_DB = 6.0
#: ISO 3745:2012/Amd.1:2017 A.2.5: absorption coefficient of the reflecting
#: plane at most 0,06, and the plane extends at least a quarter of a
#: wavelength and at least 0,75 m beyond the projection of the measurement
#: surface.
_MAX_PLANE_ABSORPTION = 0.06
_MIN_PLANE_MARGIN_M = 0.75
#: ISO 26101:2017 B.3.2: the directionality is measured at the angles of
#: elevation 20 deg to 80 deg (hemi-anechoic) or 20 deg to 160 deg
#: (anechoic), counted from the vertical above the source.
_DIRECTIONALITY_POLAR_DEG: dict[str, tuple[float, ...]] = {
    "hemi-anechoic": (80.0, 60.0, 40.0, 20.0),
    "anechoic": (80.0, 60.0, 40.0, 20.0, 100.0, 120.0, 140.0, 160.0),
}
_DIRECTIONALITY_AZIMUTH_DEG: tuple[float, ...] = (
    0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0,
)  # fmt: skip
#: B.3.2: r = 1,5 m.
_DIRECTIONALITY_RADIUS_M = 1.5

#: Origin search: points per axis of the starting lattice and the step at
#: which the compass search stops, in metres.
_ORIGIN_LATTICE = 5
_ORIGIN_RESOLUTION_M = 1.0e-3
_ORIGIN_MAX_ITERATIONS = 400
#: Rounding allowance on the comparisons of the search and of the criteria: a
#: spread exactly on the limit of Table A.1 qualifies, and floating point must
#: not turn that into a failure. Far below any measurable difference.
_SLACK = 1.0e-9

_POSITIONS_RANK = 2
_COORDINATES = 3


def _band_index(frequency_hz: float) -> int:
    """The one-third octave band of a frequency, 0 at 1 kHz (base-ten bands)."""
    if not math.isfinite(frequency_hz) or frequency_hz <= 0.0:
        msg = f"'frequencies_hz' must be positive and finite; got {frequency_hz!r}."
        raise ValueError(msg)
    k = round(10.0 * math.log10(frequency_hz / 1000.0))
    if not 0 <= k - _LOWEST_K < len(_NOMINAL_THIRDS_HZ):
        msg = (
            f"{frequency_hz:g} Hz lies outside the one-third octave bands from "
            "10 Hz to 40 kHz this qualification reads."
        )
        raise ValueError(msg)
    return int(k)


def _nominal(k: int) -> float:
    """ISO 266 nominal mid-band frequency of band ``k``."""
    return _NOMINAL_THIRDS_HZ[k - _LOWEST_K]


def _lookup_bands(frequencies_hz: ArrayLike) -> list[int]:
    """Band indices of one frequency or a 1-D array of them, for a table lookup."""
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    if freqs.ndim != 1:
        msg = "'frequencies_hz' must be one frequency or a 1-D array of frequencies."
        raise ValueError(msg)
    return [_band_index(float(f)) for f in freqs]


def _band_indices(frequencies_hz: ArrayLike) -> np.ndarray:
    """Band indices of a 1-D frequency axis, refusing two in one band."""
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    if freqs.ndim != 1 or freqs.size == 0:
        msg = "'frequencies_hz' must be a non-empty 1-D array of frequencies."
        raise ValueError(msg)
    ks = np.array([_band_index(float(f)) for f in freqs], dtype=np.int64)
    if np.unique(ks).size != ks.size:
        msg = (
            "'frequencies_hz' holds two frequencies in the same one-third octave "
            "band; each band is qualified once."
        )
        raise ValueError(msg)
    return ks


def _check_room(room: str) -> None:
    if room not in _ROOMS:
        msg = f"'room' must be 'anechoic' or 'hemi-anechoic'; got {room!r}."
        raise ValueError(msg)


def _table_a1(k: int, room: str) -> float:
    low, mid, high = _TABLE_A1_DB[room]
    if k <= _K_630:
        return low
    if k <= _K_5000:
        return mid
    return high


def _table_b1(k: int, room: str) -> float:
    low, mid, high, top = _TABLE_B1_DB[room]
    if k <= _K_630:
        return low
    if k <= _K_5000:
        return mid
    if k <= _K_10000:
        return high
    return top


def inverse_square_law_tolerance_db(
    frequencies_hz: ArrayLike, *, room: FreeFieldRoom
) -> np.ndarray:
    """Allowable deviation from the inverse square law per band (Table A.1).

    ISO 26101:2017 Annex A and ISO 3745:2012/Amd.1:2017 A.2.2 print the same
    table. A frequency is read in the one-third octave band that contains it,
    so a tone at 794 Hz is held to the 800 Hz row.

    :param frequencies_hz: Test frequencies or band mid-frequencies, in hertz.
    :param room: ``"anechoic"`` or ``"hemi-anechoic"``.
    :return: The half-width of the tolerance band, in dB, per frequency.
    :raises ValueError: for an unknown room, a non-positive frequency or
        frequencies that are not one value or a 1-D array.
    """
    _check_room(room)
    return np.array(
        [_table_a1(k, room) for k in _lookup_bands(frequencies_hz)], dtype=np.float64
    )


def directionality_tolerance_db(
    frequencies_hz: ArrayLike, *, room: FreeFieldRoom
) -> np.ndarray:
    """Allowable deviation of the test source directionality (ISO 26101 Table B.1).

    :param frequencies_hz: One-third octave mid-band frequencies, in hertz.
    :param room: ``"anechoic"`` or ``"hemi-anechoic"``.
    :return: The half-width of the tolerance band, in dB, per frequency.
    :raises ValueError: for an unknown room, a non-positive frequency or
        frequencies that are not one value or a 1-D array.
    """
    _check_room(room)
    return np.array(
        [_table_b1(k, room) for k in _lookup_bands(frequencies_hz)], dtype=np.float64
    )


def qualification_frequencies_hz(
    low_hz: float = 100.0, high_hz: float = 10000.0
) -> np.ndarray:
    """The frequencies ISO 3745:2012/Amd.1:2017 A.2.3 evaluates over a range.

    Below 125 Hz and above 4 000 Hz every one-third octave band, between them
    the octave mid-band frequencies 125, 250, 500, 1 000, 2 000 and 4 000 Hz.
    The default range is the least A.2.3 allows, 100 Hz to 10 000 Hz: eleven
    frequencies.

    :param low_hz: Lowest band of the range, in hertz (read in its band).
    :param high_hz: Highest band of the range, in hertz.
    :return: The nominal frequencies to evaluate, ascending, in hertz.
    :raises ValueError: if the range is empty.
    """
    k_lo, k_hi = _band_index(low_hz), _band_index(high_hz)
    if k_hi < k_lo:
        msg = "'high_hz' must not lie below 'low_hz'."
        raise ValueError(msg)
    return np.array(
        [_nominal(k) for k in range(k_lo, k_hi + 1) if _on_grid(k)],
        dtype=np.float64,
    )


def _on_grid(k: int) -> bool:
    """Whether band ``k`` is one A.2.3 requires to be evaluated."""
    if _K_OCTAVE_LOW <= k <= _K_OCTAVE_HIGH:
        return (k - _K_OCTAVE_LOW) % _OCTAVE_STEP == 0
    return True


def _grid_contiguous(k_lo: int, k_hi: int, evaluated: set[int]) -> bool:
    """Whether every A.2.3 frequency from band ``k_lo`` to ``k_hi`` is evaluated."""
    return all(k in evaluated for k in range(k_lo, k_hi + 1) if _on_grid(k))


def _wavelength_m(frequency_hz: float, speed_of_sound: float) -> float:
    return speed_of_sound / frequency_hz


# ---------------------------------------------------------------------------
# Input: one straight microphone traverse
# ---------------------------------------------------------------------------


def _as_levels(value: ArrayLike, n_points: int, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    if arr.ndim != _POSITIONS_RANK or arr.shape[0] != n_points:
        msg = (
            f"'{name}' must hold one row per measurement point ({n_points}), "
            "one column per frequency."
        )
        raise ValueError(msg)
    return np.array(arr, dtype=np.float64)


def _checked_targets(targets: str | Sequence[str]) -> tuple[str, ...]:
    """The A.3.3 targets of a traverse, one name or several, as a tuple."""
    named = (targets,) if isinstance(targets, str) else tuple(targets)
    unknown = [t for t in named if t not in _PATH_TARGETS]
    if unknown:
        msg = (
            f"'targets' must be among {', '.join(map(repr, _PATH_TARGETS))} "
            f"(ISO 3745:2012/Amd.1:2017, A.3.3); got {unknown[0]!r}."
        )
        raise ValueError(msg)
    return named


def _checked_positions(value: ArrayLike) -> np.ndarray:
    """An ``(N, 3)`` array of finite coordinates with at least two points."""
    positions = np.array(value, dtype=np.float64)
    if (
        positions.ndim != _POSITIONS_RANK
        or positions.shape[1] != _COORDINATES
        or positions.shape[0] < _POSITIONS_RANK
    ):
        msg = (
            "'positions_m' must be an (N, 3) array of at least two points, "
            "one (x, y, z) row per point."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(positions)):
        msg = "'positions_m' must be finite."
        raise ValueError(msg)
    return positions


def _checked_traverse_levels(value: ArrayLike, n_points: int) -> np.ndarray:
    """The levels of a traverse: finite, or ``nan`` where not measured."""
    levels = _as_levels(value, n_points, "levels_db")
    if np.any(np.isinf(levels)):
        msg = (
            "'levels_db' must be finite, with nan only where a point was not "
            "measured at a frequency."
        )
        raise ValueError(msg)
    return levels


def _checked_monitor(value: ArrayLike, levels: np.ndarray) -> np.ndarray:
    """The monitor readings, finite wherever Formula (1) reads them."""
    monitor = _as_levels(value, levels.shape[0], "monitor_levels_db")
    if monitor.shape != levels.shape:
        msg = "'monitor_levels_db' must have the shape of 'levels_db'."
        raise ValueError(msg)
    # Formula (1) corrects every point to the reading of point 0.
    measured = np.isfinite(levels)
    needed = measured.copy()
    needed[0] |= measured.any(axis=0)
    if np.any(needed & ~np.isfinite(monitor)):
        msg = (
            "'monitor_levels_db' must be finite at every measured point "
            "and in its first row, the reading every point is corrected "
            "to (ISO 26101:2017, Formula (1))."
        )
        raise ValueError(msg)
    return monitor


def _checked_background(value: ArrayLike, levels: np.ndarray) -> np.ndarray:
    """The background, per point or one row, finite at every measured point."""
    background = np.asarray(value, dtype=np.float64)
    if background.ndim == 1 and background.shape[0] == levels.shape[1]:
        background = np.broadcast_to(background, levels.shape)
    background = _as_levels(background, levels.shape[0], "background_levels_db")
    if background.shape != levels.shape:
        msg = (
            "'background_levels_db' must have the shape of 'levels_db', "
            "or be one row for the whole traverse."
        )
        raise ValueError(msg)
    if np.any(np.isfinite(levels) & ~np.isfinite(background)):
        msg = "'background_levels_db' must be finite at every measured point."
        raise ValueError(msg)
    return background


@dataclass(frozen=True)
class MicrophoneTraverse:
    r"""One straight microphone traverse of ISO 26101:2017 5.1.3.2.

    :ivar positions_m: The measurement points, one row per point, as
        ``(x, y, z)`` coordinates in metres in the room frame: ``z`` points up
        and, in a hemi-anechoic room, the reflecting plane is ``z = 0``. The
        mathematical origin of the traverse is given to
        :func:`inverse_square_law_deviations` in the same frame.
    :ivar levels_db: The measured sound pressure level :math:`L'_{pi}` at each
        point, one row per point and one column per test frequency, in dB. A
        ``nan`` marks a point not measured at that frequency, which is how a
        spacing that changes with frequency is written (ISO 3745 A.4.3 asks
        for equally spaced points *at each frequency*). Every other level is
        finite.
    :ivar monitor_levels_db: The monitor microphone level
        :math:`L_{p,\mathrm{ref},i}` recorded with each point, same shape; the
        first row is the level for the initial point 0, which every point is
        corrected to. It is finite wherever a level was measured and in the
        first row of every frequency measured. ``None`` applies no stability
        correction.
    :ivar background_levels_db: The background level at each point, same
        shape, or one row for the whole traverse, finite wherever a level was
        measured; ``None`` leaves the 6 dB requirement of ISO 26101
        5.1.2.2 c) unjudged.
    :ivar name: A label for the traverse (the path it follows: a dihedral
        corner, the nearest wall, a door).
    :ivar targets: What the path is selected towards, among the five of the
        amended ISO 3745 A.3.3 a) to e): ``"dihedral corner"``,
        ``"trihedral corner"``, ``"boundary centre"`` (the centre of the most
        uniform boundary surface), ``"closest boundary"`` and ``"unique
        features"`` (a door, a window, a ventilation opening). One path may
        serve more than one target, as A.3.3 NOTE 1 allows for c) and d); an
        empty tuple names none.
    """

    positions_m: np.ndarray
    levels_db: np.ndarray
    monitor_levels_db: np.ndarray | None = None
    background_levels_db: np.ndarray | None = None
    name: str = ""
    targets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Hold every array as a float64 copy and refuse inconsistent shapes.

        :raises ValueError: if the positions are not an ``(N, 3)`` array of
            finite coordinates with at least two points, a level array does
            not have one row per point, a level is infinite, a monitor or
            background reading a measured level needs is not finite, or a
            target is not one of A.3.3.
        """
        object.__setattr__(self, "targets", _checked_targets(self.targets))
        positions = _checked_positions(self.positions_m)
        levels = _checked_traverse_levels(self.levels_db, positions.shape[0])
        object.__setattr__(self, "positions_m", positions)
        object.__setattr__(self, "levels_db", levels)
        if self.monitor_levels_db is not None:
            monitor = _checked_monitor(self.monitor_levels_db, levels)
            object.__setattr__(self, "monitor_levels_db", monitor)
        if self.background_levels_db is not None:
            background = _checked_background(self.background_levels_db, levels)
            object.__setattr__(self, "background_levels_db", background)

    @classmethod
    def along(
        cls,
        direction: ArrayLike,
        distances_m: ArrayLike,
        levels_db: ArrayLike,
        *,
        start_m: ArrayLike = (0.0, 0.0, 0.0),
        monitor_levels_db: ArrayLike | None = None,
        background_levels_db: ArrayLike | None = None,
        name: str = "",
        targets: Sequence[str] = (),
    ) -> MicrophoneTraverse:
        """A traverse laid out along a straight line from ``start_m``.

        :param direction: The direction of the path, any non-zero 3-vector.
        :param distances_m: The distance of each point from ``start_m`` along
            the path, in metres.
        :param levels_db: One row per point, one column per frequency, in dB.
        :param start_m: The point the distances are counted from, in metres;
            the room frame's origin by default.
        :param monitor_levels_db: As for the class.
        :param background_levels_db: As for the class.
        :param name: As for the class.
        :param targets: As for the class.
        :return: The traverse.
        :raises ValueError: for a direction that is zero or not finite.
        """
        unit = np.asarray(direction, dtype=np.float64).reshape(_COORDINATES)
        norm = float(np.linalg.norm(unit))
        if not math.isfinite(norm) or norm <= 0.0:
            msg = "'direction' must be a finite, non-zero 3-vector."
            raise ValueError(msg)
        unit = unit / norm
        s = np.atleast_1d(np.asarray(distances_m, dtype=np.float64))
        start = np.asarray(start_m, dtype=np.float64).reshape(_COORDINATES)
        return cls(
            positions_m=start[np.newaxis, :] + s[:, np.newaxis] * unit[np.newaxis, :],
            levels_db=np.asarray(levels_db, dtype=np.float64),
            monitor_levels_db=(
                None
                if monitor_levels_db is None
                else np.asarray(monitor_levels_db, dtype=np.float64)
            ),
            background_levels_db=(
                None
                if background_levels_db is None
                else np.asarray(background_levels_db, dtype=np.float64)
            ),
            name=name,
            targets=tuple(targets),
        )


# ---------------------------------------------------------------------------
# The fit: Formulae (1) to (4) and the origin
# ---------------------------------------------------------------------------


def _stability_corrected(traverse: MicrophoneTraverse) -> tuple[np.ndarray, np.ndarray]:
    """Formula (1) and the largest monitor excursion per frequency."""
    levels = traverse.levels_db
    if traverse.monitor_levels_db is None:
        return levels.copy(), np.full(levels.shape[1], np.nan)
    monitor = traverse.monitor_levels_db
    drift = monitor - monitor[0][np.newaxis, :]
    excursion = np.nanmax(np.abs(drift), axis=0)
    return levels - drift, np.asarray(excursion, dtype=np.float64)


@dataclass(frozen=True)
class _Evaluation:
    r"""Radii and spreads of one origin, over every traverse and frequency.

    ``rank`` is the radius the origin search compares: the smallest qualified
    distance over the runs a deviation ends, capped at the distance from the
    fixed reference of the search to the nearest last point measured, which
    is the same for every origin. A run that reaches its last point is ended
    by the measurement, not by the room, and moving the origin towards or away
    from that point says nothing about the room, so only the runs the room
    ends tell origins apart. ``share`` is the mean, over every traverse and
    frequency, of the half spread of :math:`L_{pi} + 20 \lg(r_i/r_0)` within
    the radius as a share of its Table A.1 limit: how much of the tolerance
    band the curves fill on average, least where the origin sits at the centre
    the field diverges from.
    """

    traverse_radius: np.ndarray  # (NT, NF)
    band_radius: np.ndarray  # (NF,)
    radius: float
    rank: float
    share: float
    distances: tuple[np.ndarray, ...]


def _prefix_radius(
    r: np.ndarray, y: np.ndarray, tolerance: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """The qualified distance of one traverse per frequency, for a fixed origin.

    ``r`` is ``(N,)``, ``y`` is ``(N, NF)`` with ``nan`` for points not
    measured. The run from the origin qualifies while the spread of ``y``
    stays within twice the tolerance.

    :return: The distance per frequency, and per frequency whether a deviation
        ended the run (``False`` when it reaches the last point measured).
    """
    order = np.argsort(r, kind="stable")
    rs = r[order]
    ys = y[order]
    valid = np.isfinite(ys)
    upper = np.maximum.accumulate(np.where(valid, ys, -np.inf), axis=0)
    lower = np.minimum.accumulate(np.where(valid, ys, np.inf), axis=0)
    spread = upper - lower
    failing = valid & (spread > 2.0 * tolerance[np.newaxis, :] + _SLACK)
    n_points, n_bands = ys.shape
    radius = np.zeros(n_bands, dtype=np.float64)
    for j in range(n_bands):
        fails = np.flatnonzero(failing[:, j])
        stop = int(fails[0]) if fails.size else n_points
        passed = np.flatnonzero(valid[:stop, j])
        radius[j] = float(rs[passed[-1]]) if passed.size else 0.0
    return radius, np.any(failing, axis=0)


def _evaluate(
    origin: np.ndarray,
    positions: Sequence[np.ndarray],
    levels: Sequence[np.ndarray],
    tolerance: np.ndarray,
    reference: np.ndarray | None = None,
) -> _Evaluation:
    """Qualified distances for one origin: per traverse, per band, overall.

    ``reference`` is the point from which the search measures the last
    points (see :class:`_Evaluation`); ``None`` takes the origin.
    """
    distances = tuple(
        np.asarray(np.linalg.norm(p - origin[np.newaxis, :], axis=1), dtype=np.float64)
        for p in positions
    )
    for r in distances:
        if not np.all(r > 0.0):
            msg = (
                "a measurement point coincides with the mathematical origin; "
                "the inverse square law is undefined there."
            )
            raise ValueError(msg)
    ys = [
        lv + 20.0 * np.log10(r / _R0_M)[:, np.newaxis]
        for lv, r in zip(levels, distances, strict=True)
    ]
    runs = [_prefix_radius(r, y, tolerance) for r, y in zip(distances, ys, strict=True)]
    traverse_radius = np.vstack([radius for radius, _ in runs])
    ended = np.vstack([failed for _, failed in runs])
    band_radius = traverse_radius.min(axis=0)
    radius = float(band_radius.min())
    anchor = origin if reference is None else reference
    # The farthest point measured at each frequency on each traverse, seen
    # from the reference: the most any origin could qualify there.
    reach = min(
        float(
            np.min(
                np.max(
                    np.where(
                        np.isfinite(lv),
                        np.linalg.norm(p - anchor[np.newaxis, :], axis=1)[
                            :, np.newaxis
                        ],
                        -np.inf,
                    ),
                    axis=0,
                )
            )
        )
        for p, lv in zip(positions, levels, strict=True)
    )
    room = float(np.min(np.where(ended, traverse_radius, np.inf)))
    shares = []
    for r, y in zip(distances, ys, strict=True):
        inside = (r <= radius + _SLACK)[:, np.newaxis] & np.isfinite(y)
        hi = np.where(inside, y, -np.inf).max(axis=0)
        lo = np.where(inside, y, np.inf).min(axis=0)
        half = np.where(np.isfinite(hi - lo), (hi - lo) / 2.0, 0.0)
        shares.append(half / tolerance)
    share = float(np.mean(shares))
    return _Evaluation(
        traverse_radius, band_radius, radius, min(room, reach), share, distances
    )


def _better(
    a: _Evaluation,
    a_origin: np.ndarray,
    b: _Evaluation,
    b_origin: np.ndarray,
    centre: np.ndarray,
) -> bool:
    """Lexicographic order of the origin search: rank, share, then centring.

    Two ranks within the millimetre to which the search resolves the origin
    are a tie, and the flatter curves decide.
    """
    if a.rank > b.rank + _ORIGIN_RESOLUTION_M:
        return True
    if a.rank < b.rank - _ORIGIN_RESOLUTION_M:
        return False
    if a.share < b.share - _SLACK:
        return True
    if a.share > b.share + _SLACK:
        return False
    return (
        float(np.linalg.norm(a_origin - centre))
        < float(np.linalg.norm(b_origin - centre)) - _SLACK
    )


def _compass_step(
    evaluate: Callable[[np.ndarray], _Evaluation],
    best: _Evaluation,
    best_origin: np.ndarray,
    step: np.ndarray,
    box: np.ndarray,
) -> tuple[_Evaluation, np.ndarray, bool]:
    """One pass of the compass search: a step either way along each axis.

    :return: The best evaluation and origin after the pass, and whether the
        pass moved the origin.
    """
    lo, hi = box[0], box[1]
    centre = (lo + hi) / 2.0
    improved = False
    for axis in range(_COORDINATES):
        if step[axis] <= 0.0:
            continue
        for sign in (1.0, -1.0):
            candidate = best_origin.copy()
            candidate[axis] = min(
                max(candidate[axis] + sign * step[axis], lo[axis]), hi[axis]
            )
            trial = evaluate(candidate)
            if _better(trial, candidate, best, best_origin, centre):
                best, best_origin = trial, candidate
                improved = True
    return best, best_origin, improved


def _search_origin(
    box: np.ndarray,
    positions: Sequence[np.ndarray],
    levels: Sequence[np.ndarray],
    tolerance: np.ndarray,
) -> tuple[np.ndarray, _Evaluation]:
    """Lattice then compass search of the origin inside the source box."""
    lo, hi = box[0], box[1]
    centre = (lo + hi) / 2.0
    evaluate = partial(
        _evaluate,
        positions=positions,
        levels=levels,
        tolerance=tolerance,
        reference=centre,
    )
    axes = [
        np.linspace(lo[i], hi[i], _ORIGIN_LATTICE)
        if hi[i] > lo[i]
        else np.array([lo[i]])
        for i in range(_COORDINATES)
    ]
    best_origin = centre.copy()
    best = evaluate(best_origin)
    for point in product(*axes):
        candidate = np.array(point, dtype=np.float64)
        trial = evaluate(candidate)
        if _better(trial, candidate, best, best_origin, centre):
            best, best_origin = trial, candidate
    step = (hi - lo) / (_ORIGIN_LATTICE - 1) / 2.0
    for _ in range(_ORIGIN_MAX_ITERATIONS):
        if float(step.max()) < _ORIGIN_RESOLUTION_M:
            break
        best, best_origin, improved = _compass_step(
            evaluate, best, best_origin, step, box
        )
        if not improved:
            step = step / 2.0
    return best_origin, best


def _chebyshev_centre(y: np.ndarray, inside: np.ndarray) -> np.ndarray:
    """Midpoint of the spread of ``y`` over the points ``inside``, per band.

    Every band must have at least one point inside.
    """
    hi = np.where(inside, y, -np.inf).max(axis=0)
    lo = np.where(inside, y, np.inf).min(axis=0)
    return np.asarray((hi + lo) / 2.0, dtype=np.float64)


def _same_radii(given: ArrayLike, qualified: np.ndarray) -> bool:
    """Whether ``given`` holds the radii :func:`_evaluate` qualified."""
    radii = np.asarray(given, dtype=np.float64)
    return radii.shape == qualified.shape and bool(
        np.allclose(radii, qualified, rtol=0.0, atol=_SLACK, equal_nan=True)
    )


@dataclass(frozen=True)
class InverseSquareLawResult:
    r"""Deviations from the inverse square law of one test source (ISO 26101 5.1.5).

    :ivar frequencies_hz: The test frequencies, in hertz, as given.
    :ivar room: ``"anechoic"`` or ``"hemi-anechoic"``.
    :ivar origin_m: The mathematical origin of the traverses, ``(x, y, z)`` in
        metres.
    :ivar origin_fitted: ``True`` when the origin was searched inside
        :attr:`source_box_m`.
    :ivar source_box_m: The box the test source occupies, ``(2, 3)`` rows of
        lower and upper corner, or ``None`` for a fixed origin.
    :ivar traverse_names: The label of each traverse as given, ``""`` when
        none was.
    :ivar traverse_targets: What each traverse was selected towards (A.3.3
        a) to e)), as given.
    :ivar positions_m: The measurement points of each traverse, ``(N, 3)``.
    :ivar distances_m: The distance :math:`r_i` of each point from the origin,
        in metres.
    :ivar levels_db: :math:`L_{pi}` of each traverse after the stability
        correction of Formula (1), ``(N, NF)``, ``nan`` where not measured.
    :ivar background_margin_db: :math:`L'_{pi}` less the background at each
        point, ``(N, NF)``, or ``None`` for a traverse without background.
    :ivar source_stability_db: The largest excursion of the monitor
        microphone from its reading at point 0, per frequency, or ``nan``
        without a monitor.
    :ivar source_strength_db: :math:`b` of Formula (2) per traverse and
        frequency, ``(NT, NF)``: the midpoint of the admissible interval over
        the points within :attr:`band_radius_m` (over the traverse's own
        qualified run when its first point lies beyond that radius).
    :ivar initial_source_strength_db: The starting value of Formula (3), the
        mean of :math:`L_{pi} + 20 \lg(r_i/r_0)` over every point, ``(NT, NF)``.
    :ivar deviations_db: :math:`\Delta L_{pi}` of Formula (4) at every point,
        ``(N, NF)`` per traverse.
    :ivar traverse_radius_m: The qualified distance of each traverse at each
        frequency, ``(NT, NF)``, in metres.
    :ivar band_radius_m: The distance to which each frequency is qualified on
        every traverse at once, ``(NF,)``, in metres.
    """

    frequencies_hz: np.ndarray
    room: str
    origin_m: np.ndarray
    origin_fitted: bool
    source_box_m: np.ndarray | None
    traverse_names: tuple[str, ...]
    traverse_targets: tuple[tuple[str, ...], ...]
    positions_m: tuple[np.ndarray, ...]
    distances_m: tuple[np.ndarray, ...]
    levels_db: tuple[np.ndarray, ...]
    background_margin_db: tuple[np.ndarray | None, ...]
    source_stability_db: tuple[np.ndarray, ...]
    source_strength_db: np.ndarray
    initial_source_strength_db: np.ndarray
    deviations_db: tuple[np.ndarray, ...]
    traverse_radius_m: np.ndarray
    band_radius_m: np.ndarray

    def __post_init__(self) -> None:
        """Reject a room, a frequency or a radius Table A.1 does not give.

        The qualified radii are the verdict judged against the Table A.1
        limits of the room, so they are checked against the radii the
        corrected levels reach from the origin within those limits: a result
        cannot be built, or rewritten with :func:`dataclasses.replace`, with a
        radius the levels do not qualify.

        :raises ValueError: for an unknown room, a frequency that is not
            positive, or radii other than the ones the levels qualify.
        """
        _check_room(self.room)
        _lookup_bands(self.frequencies_hz)
        evaluation = _evaluate(
            np.asarray(self.origin_m, dtype=np.float64),
            self.positions_m,
            self.levels_db,
            self.tolerance_db,
        )
        if not (
            _same_radii(self.traverse_radius_m, evaluation.traverse_radius)
            and _same_radii(self.band_radius_m, evaluation.band_radius)
        ):
            msg = (
                "InverseSquareLawResult: the qualified radii are not the ones "
                "the levels reach within the Table A.1 limits of the room."
            )
            raise ValueError(msg)

    @property
    def tolerance_db(self) -> np.ndarray:
        """The Table A.1 limit of each frequency, in dB, read from the room.

        :return: :func:`inverse_square_law_tolerance_db` of
            :attr:`frequencies_hz` in :attr:`room`.
        """
        return np.array(
            [_table_a1(k, self.room) for k in _lookup_bands(self.frequencies_hz)],
            dtype=np.float64,
        )

    @property
    def maximum_qualified_radius_m(self) -> float:
        """The largest radius every traverse meets at every frequency (A.2.4).

        :return: The smallest of :attr:`band_radius_m`, in metres.
        """
        return float(np.min(self.band_radius_m))

    @property
    def largest_deviation_db(self) -> np.ndarray:
        r"""The largest :math:`|\Delta L_{pi}|` within each band's radius.

        :return: One value per frequency, in dB.
        """
        worst = np.zeros(self.frequencies_hz.size, dtype=np.float64)
        for r, dev in zip(self.distances_m, self.deviations_db, strict=True):
            inside = (
                r[:, np.newaxis] <= self.band_radius_m[np.newaxis, :] + _SLACK
            ) & (np.isfinite(dev))
            worst = np.maximum(worst, np.where(inside, np.abs(dev), 0.0).max(axis=0))
        return worst

    def plot(
        self,
        ax: Axes | None = None,
        *,
        frequency_hz: float | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the deviations along every traverse at one frequency.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param frequency_hz: The test frequency to draw; ``None`` draws the
            one qualified to the shortest distance.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the deviation curves.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.free_field import plot_inverse_square_law

        check_language(language)
        return plot_inverse_square_law(
            self, ax=ax, frequency_hz=frequency_hz, language=language, **kwargs
        )


@dataclass(frozen=True)
class _Prepared:
    """The traverses of one source, read for the fit."""

    positions: list[np.ndarray]
    levels: list[np.ndarray]  # after the stability correction of Formula (1)
    margins: tuple[np.ndarray | None, ...]
    stability: tuple[np.ndarray, ...]


def _prepared_traverses(
    traverses: Sequence[MicrophoneTraverse], n_bands: int
) -> _Prepared:
    """Correct every traverse by Formula (1), refusing one that cannot be fitted."""
    positions: list[np.ndarray] = []
    levels: list[np.ndarray] = []
    margins: list[np.ndarray | None] = []
    stability: list[np.ndarray] = []
    for index, traverse in enumerate(traverses):
        if traverse.levels_db.shape[1] != n_bands:
            msg = (
                f"traverse {index} has {traverse.levels_db.shape[1]} level columns "
                f"for {n_bands} frequencies in 'frequencies_hz'."
            )
            raise ValueError(msg)
        corrected, excursion = _stability_corrected(traverse)
        if not np.all(np.any(np.isfinite(corrected), axis=0)):
            msg = f"traverse {index} has no level at one of the frequencies."
            raise ValueError(msg)
        positions.append(traverse.positions_m)
        levels.append(corrected)
        stability.append(excursion)
        margins.append(
            None
            if traverse.background_levels_db is None
            else traverse.levels_db - traverse.background_levels_db
        )
    return _Prepared(positions, levels, tuple(margins), tuple(stability))


def _placed_origin(
    origin_m: ArrayLike | None,
    source_box_m: ArrayLike | None,
    positions: Sequence[np.ndarray],
    levels: Sequence[np.ndarray],
    tolerance: np.ndarray,
) -> tuple[np.ndarray, np.ndarray | None, _Evaluation]:
    """The origin given, or searched inside the source box, and its evaluation.

    :return: The origin, the box (``None`` for a fixed origin) and the
        qualified distances seen from the origin.
    """
    if origin_m is not None and source_box_m is not None:
        msg = "give 'origin_m' or 'source_box_m', not both."
        raise ValueError(msg)
    if source_box_m is not None:
        box = np.asarray(source_box_m, dtype=np.float64).reshape(2, _COORDINATES)
        if not np.all(np.isfinite(box)) or np.any(box[1] < box[0]):
            msg = (
                "'source_box_m' must be ((x_min, y_min, z_min), (x_max, y_max, "
                "z_max)) with each upper coordinate at or above the lower."
            )
            raise ValueError(msg)
        origin, evaluation = _search_origin(box, positions, levels, tolerance)
        return origin, box, evaluation
    origin = (
        np.zeros(_COORDINATES)
        if origin_m is None
        else np.asarray(origin_m, dtype=np.float64).reshape(_COORDINATES)
    )
    if not np.all(np.isfinite(origin)):
        msg = "'origin_m' must be finite."
        raise ValueError(msg)
    return origin, None, _evaluate(origin, positions, levels, tolerance)


def _source_strengths(
    evaluation: _Evaluation, levels: Sequence[np.ndarray]
) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    """``b`` of Formula (2), the start of Formula (3) and the deviations of (4).

    :return: ``b`` and the starting value per traverse and frequency, and the
        deviations of each traverse.
    """
    shape = (len(levels), evaluation.band_radius.size)
    strengths = np.empty(shape, dtype=np.float64)
    initial = np.empty(shape, dtype=np.float64)
    deviations: list[np.ndarray] = []
    for t, (r, lv) in enumerate(zip(evaluation.distances, levels, strict=True)):
        y = lv + 20.0 * np.log10(r / _R0_M)[:, np.newaxis]
        valid = np.isfinite(y)
        # b centres the points within the radius every traverse meets; a
        # traverse whose first point lies beyond that radius is centred over
        # its own qualified run instead, so that its deviations stay defined.
        reach = np.where(
            np.any(
                valid & (r[:, np.newaxis] <= evaluation.band_radius + _SLACK), axis=0
            ),
            evaluation.band_radius,
            evaluation.traverse_radius[t],
        )
        inside = valid & (r[:, np.newaxis] <= reach[np.newaxis, :] + _SLACK)
        strengths[t] = _chebyshev_centre(y, inside)
        initial[t] = np.nanmean(y, axis=0)
        deviations.append(np.asarray(y - strengths[t][np.newaxis, :], dtype=np.float64))
    return strengths, initial, deviations


def inverse_square_law_deviations(
    traverses: Sequence[MicrophoneTraverse],
    *,
    frequencies_hz: ArrayLike,
    room: FreeFieldRoom,
    origin_m: ArrayLike | None = None,
    source_box_m: ArrayLike | None = None,
) -> InverseSquareLawResult:
    r"""Deviations from the inverse square law along the traverses of one source.

    Applies Formula (1) with the monitor microphone, then Formulae (2) and (4)
    with the source strength :math:`b` that maximizes the qualified distance
    under the Table A.1 limits of ``room`` (see the module notes: the midpoint
    of the admissible interval, an exact rather than an iterative answer), and
    reports the starting value of Formula (3) beside it.

    One call covers one test source: ISO 26101 5.1.2.2 allows two or more to
    span the frequency range, each with its own mathematical origin, and
    :func:`check_free_field` takes one result per source.

    :param traverses: The straight traverses, all measured at
        ``frequencies_hz``.
    :param frequencies_hz: The test frequencies (tones or one-third octave
        mid-bands), in hertz, one per level column.
    :param room: ``"anechoic"`` or ``"hemi-anechoic"``, which selects the
        Table A.1 limits.
    :param origin_m: The mathematical origin of every traverse, ``(x, y, z)``
        in metres; ``None`` with no ``source_box_m`` takes the room frame's
        origin.
    :param source_box_m: The box the test source physically occupies, as
        ``((x_min, y_min, z_min), (x_max, y_max, z_max))`` in metres; the
        origin is then searched inside it (ISO 26101 5.1.3.2, ISO 3745 A.3.3).
        A zero extent on an axis holds the origin on that coordinate.
    :return: :class:`InverseSquareLawResult`.
    :raises ValueError: if both ``origin_m`` and ``source_box_m`` are given, a
        traverse's level columns do not match the frequencies, a traverse has
        no level at a frequency, or a point coincides with the origin.
    """
    _check_room(room)
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    ks = _band_indices(freqs)
    if len(traverses) == 0:
        msg = "'traverses' must hold at least one MicrophoneTraverse."
        raise ValueError(msg)
    tolerance = np.array([_table_a1(int(k), room) for k in ks], dtype=np.float64)
    prepared = _prepared_traverses(traverses, freqs.size)
    positions, levels = prepared.positions, prepared.levels
    origin, box, evaluation = _placed_origin(
        origin_m, source_box_m, positions, levels, tolerance
    )
    strengths, initial, deviations = _source_strengths(evaluation, levels)

    return InverseSquareLawResult(
        frequencies_hz=read_only_copy(freqs),
        room=room,
        origin_m=read_only_copy(origin, dtype=np.float64),
        origin_fitted=box is not None,
        source_box_m=read_only_copy(box),
        traverse_names=tuple(t.name for t in traverses),
        traverse_targets=tuple(tuple(t.targets) for t in traverses),
        positions_m=tuple(read_only_copy(p) for p in positions),
        distances_m=evaluation.distances,
        levels_db=tuple(levels),
        background_margin_db=prepared.margins,
        source_stability_db=prepared.stability,
        source_strength_db=strengths,
        initial_source_strength_db=initial,
        deviations_db=tuple(deviations),
        traverse_radius_m=evaluation.traverse_radius,
        band_radius_m=evaluation.band_radius,
    )


# ---------------------------------------------------------------------------
# ISO 26101 Annex B: the test source directionality
# ---------------------------------------------------------------------------


def directionality_positions(
    room: FreeFieldRoom, *, radius_m: float = _DIRECTIONALITY_RADIUS_M
) -> np.ndarray:
    r"""Microphone positions of the directionality test (ISO 26101 B.3.2).

    The angle of elevation :math:`\varphi` is counted from the vertical above
    the source (90 deg is the reflecting plane), the azimuth :math:`\Theta`
    from the ``x`` axis. The rows run :math:`\varphi` = 80, 60, 40 and 20 deg
    (then 100, 120, 140 and 160 deg in an anechoic room), and within each
    :math:`\Theta` = 0 to 315 deg in steps of 45 deg: 32 positions in a
    hemi-anechoic room, 64 in an anechoic one (Figure B.1).

    :param room: ``"anechoic"`` or ``"hemi-anechoic"``.
    :param radius_m: The radius, in metres; 1,5 m in B.3.2.
    :return: ``(32, 3)`` or ``(64, 3)`` coordinates, in metres.
    """
    _check_room(room)
    radius = require_positive(radius_m, "radius_m")
    rows = []
    for polar in _DIRECTIONALITY_POLAR_DEG[room]:
        for azimuth in _DIRECTIONALITY_AZIMUTH_DEG:
            phi, theta = math.radians(polar), math.radians(azimuth)
            rows.append(
                (
                    radius * math.sin(phi) * math.cos(theta),
                    radius * math.sin(phi) * math.sin(theta),
                    radius * math.cos(phi),
                )
            )
    return np.array(rows, dtype=np.float64)


@dataclass(frozen=True)
class SourceDirectionalityResult:
    """Whether a test source is uniform enough to qualify a room (ISO 26101 B.4).

    :ivar frequencies_hz: The one-third octave mid-band frequencies, in hertz.
    :ivar room: The room type the source is to qualify.
    :ivar mean_level_db: The arithmetic mean of the decibel levels per band.
    :ivar maximum_positive_deviation_db: The largest level above the mean.
    :ivar maximum_negative_deviation_db: The largest level below the mean, a
        negative number.
    """

    frequencies_hz: np.ndarray
    room: str
    mean_level_db: np.ndarray
    maximum_positive_deviation_db: np.ndarray
    maximum_negative_deviation_db: np.ndarray

    def __post_init__(self) -> None:
        """Reject a room or a frequency Table B.1 cannot be read for.

        :raises ValueError: for an unknown room or a frequency that is not
            positive.
        """
        _check_room(self.room)
        _lookup_bands(self.frequencies_hz)

    @property
    def tolerance_db(self) -> np.ndarray:
        """The Table B.1 limit per band, in dB, read from the room.

        :return: :func:`directionality_tolerance_db` of :attr:`frequencies_hz`
            in :attr:`room`.
        """
        return np.array(
            [_table_b1(k, self.room) for k in _lookup_bands(self.frequencies_hz)],
            dtype=np.float64,
        )

    @property
    def within_tolerance(self) -> np.ndarray:
        """Per band, whether both extreme deviations are within Table B.1.

        :return: One boolean per band.
        """
        limit = self.tolerance_db + _SLACK
        return np.asarray(
            (self.maximum_positive_deviation_db <= limit)
            & (-self.maximum_negative_deviation_db <= limit),
            dtype=bool,
        )

    @property
    def passes(self) -> bool:
        """Whether the directionality is within Table B.1 in every band.

        :return: ``True`` when every band is within its limit.
        """
        return bool(np.all(self.within_tolerance))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SourceDirectionalityResult has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the extreme deviations per band against Table B.1.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the deviation bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.free_field import plot_source_directionality

        check_language(language)
        return plot_source_directionality(self, ax=ax, language=language, **kwargs)


def verify_source_directionality(
    levels_db: ArrayLike, *, frequencies_hz: ArrayLike, room: FreeFieldRoom
) -> SourceDirectionalityResult:
    """May this source qualify an anechoic or hemi-anechoic room? (ISO 26101 Annex B).

    The one-third octave band levels are measured at the 32 positions of a
    hemisphere or the 64 of a sphere of radius 1,5 m
    (:func:`directionality_positions`). Per band, the arithmetic mean of the
    decibel levels and the largest positive and negative deviations from it
    are computed (B.3.2); the source is suitable when every deviation is within
    Table B.1 (B.4). The amended ISO 3745 A.3.1 lets the measurement be made in
    the room being qualified.

    :param levels_db: One row per position (32 hemi-anechoic, 64 anechoic),
        one column per band, in dB; a 1-D array is one band.
    :param frequencies_hz: The one-third octave mid-band frequencies, in hertz.
    :param room: ``"anechoic"`` or ``"hemi-anechoic"``.
    :return: :class:`SourceDirectionalityResult`.
    :raises ValueError: for the wrong number of positions, levels that are not
        finite, or bands that do not match.
    """
    _check_room(room)
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    _band_indices(freqs)  # refuses two frequencies in one band
    levels = np.asarray(levels_db, dtype=np.float64)
    if levels.ndim == 1:
        levels = levels[:, np.newaxis]
    expected = len(_DIRECTIONALITY_POLAR_DEG[room]) * len(_DIRECTIONALITY_AZIMUTH_DEG)
    if levels.ndim != _POSITIONS_RANK or levels.shape != (expected, freqs.size):
        msg = (
            f"'levels_db' must be ({expected}, {freqs.size}): the {expected} "
            f"positions of B.3.2 in a {room} room, one column per band."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(levels)):
        msg = "'levels_db' must be finite."
        raise ValueError(msg)
    mean = levels.mean(axis=0)
    deviation = levels - mean[np.newaxis, :]
    return SourceDirectionalityResult(
        frequencies_hz=read_only_copy(freqs),
        room=room,
        mean_level_db=mean,
        maximum_positive_deviation_db=deviation.max(axis=0),
        maximum_negative_deviation_db=deviation.min(axis=0),
    )


# ---------------------------------------------------------------------------
# The verdict: ISO 3745:2012/Amd.1:2017 Annex A
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Band:
    """One evaluated frequency and where its data are."""

    k: int
    frequency_hz: float
    source: int
    column: int


def _spacing_limit(
    k: int, frequency_hz: float, speed_of_sound: float, *, iso26101: bool
) -> float:
    """Largest spacing between points: amended ISO 3745 A.4.3 or ISO 26101 A.4.3.

    A tenth of a wavelength below the edge (250 Hz or 1 kHz) and a fixed
    length above it (100 mm or 25 mm). Neither clause says which rule holds at
    the edge itself; the one-third octave band that contains the edge is held
    to the stricter of the two.
    """
    tenth = _wavelength_m(frequency_hz, speed_of_sound) / _WAVELENGTH_FRACTION_SPACING
    edge, fixed = (
        (_K_1000, _SPACING_ISO26101_M) if iso26101 else (_K_250, _SPACING_ISO3745_M)
    )
    if k < edge:
        return tenth
    if k > edge:
        return fixed
    return min(tenth, fixed)


def _equally_spaced(ps: np.ndarray) -> bool:
    """Whether the points of one traverse sit on one equally spaced grid (A.4.3).

    The points are taken along the line of the traverse. The step is the
    median gap; walking out from the first point, the next point of the grid
    must lie within a tenth of the step of where one step puts it, and the
    points between two of them are the additional measurements the last
    paragraph of A.4.3 recommends near a peak deviation. No source prints a
    tolerance, so the tenth is this module's.
    """
    if ps.shape[0] <= _POSITIONS_RANK:
        return True
    axis = ps[-1] - ps[0]
    length = float(np.linalg.norm(axis))
    if length <= 0.0:
        return False
    along = np.sort((ps - ps[0][np.newaxis, :]) @ (axis / length))
    step = float(np.median(np.diff(along)))
    if step <= 0.0:
        return False
    tolerance = _EQUAL_SPACING_TOLERANCE * step + _SLACK
    s: list[float] = along.tolist()
    node, last = 0, len(s) - 1
    while node < last:
        target = s[node] + step
        low = bisect_left(s, target - tolerance, node + 1)
        high = bisect_right(s, target + tolerance, node + 1)
        if low == high:
            # Only added points may follow the last node, all short of the
            # next step; a point beyond it means a node is missing.
            return s[-1] < target - tolerance
        nearest = low
        for index in range(low + 1, high):
            if abs(s[index] - target) < abs(s[nearest] - target):
                nearest = index
        node = nearest
    return True


@dataclass(frozen=True)
class _BandVerdict:
    points: bool
    equal_spacing: bool
    spacing: bool
    spacing_iso26101: bool
    length: bool
    background: bool | None
    directionality: bool | None


def _judge_band(
    band: _Band,
    fit: InverseSquareLawResult,
    radius: float,
    lowest_hz: float,
    directionality: SourceDirectionalityResult | None,
    speed_of_sound: float,
) -> _BandVerdict:
    """The per-frequency requirements of A.2.4 and A.4.3 within ``radius``."""
    quarter = _wavelength_m(lowest_hz, speed_of_sound) / _WAVELENGTH_FRACTION_LENGTH
    limit_3745 = _spacing_limit(
        band.k, band.frequency_hz, speed_of_sound, iso26101=False
    )
    limit_26101 = _spacing_limit(
        band.k, band.frequency_hz, speed_of_sound, iso26101=True
    )
    total = 0
    points = equal = spacing = spacing_26101 = length = True
    background: bool | None = True
    for r, p, lv, margin in zip(
        fit.distances_m,
        fit.positions_m,
        fit.levels_db,
        fit.background_margin_db,
        strict=True,
    ):
        use = np.isfinite(lv[:, band.column]) & (r <= radius + _SLACK)
        order = np.argsort(r[use], kind="stable")
        rs = r[use][order]
        ps = p[use][order]
        count = int(rs.size)
        total += count
        points &= count >= _MIN_POINTS_PER_TRAVERSE
        if count >= _POSITIONS_RANK:
            equal &= _equally_spaced(ps)
            gaps = np.linalg.norm(np.diff(ps, axis=0), axis=1)
            spacing &= float(gaps.max()) <= limit_3745 + _SLACK
            spacing_26101 &= float(gaps.max()) <= limit_26101 + _SLACK
        if count:
            length &= float(rs[0]) <= quarter + _SLACK
            length &= float(rs[-1] - rs[0]) >= quarter - _SLACK
        else:
            length = False
        if margin is None:
            background = None
        elif background is not None:
            margins = margin[use, band.column]
            background &= bool(np.all(margins >= _MIN_BACKGROUND_MARGIN_DB - _SLACK))
    points &= total >= _MIN_POINTS_TOTAL
    directional: bool | None = None
    if directionality is not None:
        bands = [_band_index(float(f)) for f in directionality.frequencies_hz]
        directional = band.k in bands and bool(
            directionality.within_tolerance[bands.index(band.k)]
        )
    return _BandVerdict(
        bool(points),
        bool(equal),
        bool(spacing),
        bool(spacing_26101),
        bool(length),
        background,
        directional,
    )


def _path_angles_ok(fit: InverseSquareLawResult, radius: float) -> bool:
    """A.3.3: in a hemi-anechoic room every path within 20 to 80 deg of the vertical.

    A path is judged by its direction, the line from its first to its last
    point within ``radius``: the angles of B.3.2 are directions from the
    source, and the direction of a straight traverse is that of its line,
    where the angle of a single point near the source would move with any
    offset of the origin inside the source.
    """
    low, high = (
        min(_DIRECTIONALITY_POLAR_DEG["hemi-anechoic"]),
        max(_DIRECTIONALITY_POLAR_DEG["hemi-anechoic"]),
    )
    for p, r in zip(fit.positions_m, fit.distances_m, strict=True):
        inside = np.flatnonzero(r <= radius + _SLACK)
        if inside.size == 0:
            continue
        ordered = inside[np.argsort(r[inside], kind="stable")]
        first = fit.origin_m if ordered.size == 1 else p[ordered[0]]
        direction = p[ordered[-1]] - first
        length = float(np.linalg.norm(direction))
        if length <= 0.0:
            continue
        polar = math.degrees(math.acos(min(max(direction[2] / length, -1.0), 1.0)))
        if polar < low - _SLACK or polar > high + _SLACK:
            return False
    return True


@dataclass(frozen=True)
class FreeFieldCheck:
    r"""Whether a room qualifies as anechoic or hemi-anechoic for ISO 3745.

    The verdict of the amended ISO 3745:2012 Annex A over the frequencies
    evaluated, with the ISO 26101:2017 clauses it defers to. Every per-band
    array is aligned with :attr:`frequencies_hz` (ascending) and judged within
    :attr:`maximum_qualified_radius_m`.

    :ivar room: ``"anechoic"`` or ``"hemi-anechoic"``.
    :ivar bandwidth: ``"discrete-frequency"`` or ``"broadband"`` (A.4.1): a
        room qualified with broadband noise is qualified only for sources that
        radiate broadband noise.
    :ivar results: The inverse-square-law analysis of each test source.
    :ivar frequencies_hz: Every evaluated frequency, ascending, in hertz.
    :ivar band_radius_m: The distance to which each frequency is qualified on
        every traverse, in metres.
    :ivar maximum_qualified_radius_m: The A.2.4 radius over every evaluated
        frequency, in metres.
    :ivar measurement_radius_m: The measurement radius to be used, if given.
    :ivar points_met: At least 10 points on each traverse and 50 in total
        within the radius (A.4.3), per band.
    :ivar equal_spacing_met: The points of every traverse within the radius
        equally spaced at the frequency (A.4.3, ISO 26101 5.1.4.3), points
        added between two of them near a peak deviation allowed (see the
        module notes for the tolerance), per band.
    :ivar spacing_met: Spacing at most a tenth of a wavelength below 250 Hz
        and 100 mm above (amended ISO 3745 A.4.3), per band; the band that
        contains 250 Hz is held to the stricter of the two.
    :ivar iso26101_spacing_met: Spacing at most a tenth of a wavelength below
        1 kHz and 25 mm above (ISO 26101 A.4.3, cited by A.2.4), per band;
        the band that contains 1 kHz is held to the stricter of the two.
    :ivar length_met: Traverse starting at most, and running at least, a
        quarter wavelength at the lowest frequency (ISO 26101 5.1.4.3), per
        band.
    :ivar background_met: Levels at least 6 dB above the background at every
        point (ISO 26101 5.1.2.2 c)), per band, or ``None`` when a traverse
        came without background.
    :ivar directionality_met: The test source within Table B.1 in the band,
        or ``None`` without a directionality result for its source.
    :ivar traverse_count_met: Five to eight traverses for every source (A.3.3).
    :ivar path_targets_met: Every source has traverses towards each of the
        five targets of A.3.3 a) to e), or ``None`` when a source names no
        target on any traverse.
    :ivar working_area_met: The traverse paths lie in the working area of the
        room, the part normally used for measurements (A.3.3), as declared,
        or ``None`` when not declared.
    :ivar path_angles_met: In a hemi-anechoic room, the direction of every
        traverse within the 20 deg to 80 deg from the vertical of the
        directionality test (A.3.3); ``None`` in an anechoic room, where A.3.3
        sets no such limit.
    :ivar reflecting_plane_met: A.2.5 in a hemi-anechoic room, ``None`` when
        not judged or in an anechoic room.
    :ivar full_frequency_range: Whether every frequency A.2.3 requires from
        100 Hz to 10 000 Hz was evaluated.
    :ivar conforming_range_hz: The widest contiguous range (in the A.2.3
        sense) over which every judged requirement is met, ``(low, high)`` in
        hertz, or ``None``; with :attr:`not_judged` empty it is the reduced
        range A.2.3 lets a report state "in conformity".
    :ivar conforming_radius_m: The radius qualified over that range, in
        metres, or ``nan``.
    :ivar not_judged: The requirements without data, by name.
    """

    room: str
    bandwidth: str
    results: tuple[InverseSquareLawResult, ...]
    frequencies_hz: np.ndarray
    band_radius_m: np.ndarray
    maximum_qualified_radius_m: float
    measurement_radius_m: float | None
    points_met: np.ndarray
    equal_spacing_met: np.ndarray
    spacing_met: np.ndarray
    iso26101_spacing_met: np.ndarray
    length_met: np.ndarray
    background_met: np.ndarray | None
    directionality_met: np.ndarray | None
    traverse_count_met: bool
    path_targets_met: bool | None
    working_area_met: bool | None
    path_angles_met: bool | None
    reflecting_plane_met: bool | None
    full_frequency_range: bool
    conforming_range_hz: tuple[float, float] | None
    conforming_radius_m: float
    not_judged: tuple[str, ...]

    @property
    def band_met(self) -> np.ndarray:
        """Per band, whether every judged per-band requirement is met.

        :return: One boolean per evaluated frequency.
        """
        met = (
            self.points_met
            & self.equal_spacing_met
            & self.spacing_met
            & self.iso26101_spacing_met
            & self.length_met
        )
        if self.background_met is not None:
            met = met & self.background_met
        if self.directionality_met is not None:
            met = met & self.directionality_met
        if self.measurement_radius_m is not None:
            met = met & (self.band_radius_m >= self.measurement_radius_m - _SLACK)
        return np.asarray(met, dtype=bool)

    @property
    def passes(self) -> bool:
        """Whether the room is qualified in full conformity with ISO 3745.

        Every requirement judged and met at every evaluated frequency, the
        whole of 100 Hz to 10 000 Hz evaluated (A.2.3), and the measurement
        radius, if given, within the qualified one.

        :return: ``True`` for a room in full conformity.
        """
        room_level = self.traverse_count_met and self.path_angles_met is not False
        room_level = room_level and self.reflecting_plane_met is not False
        room_level = room_level and self.path_targets_met is not False
        room_level = room_level and self.working_area_met is not False
        radius_ok = self.measurement_radius_m is None or (
            self.maximum_qualified_radius_m >= self.measurement_radius_m - _SLACK
        )
        return bool(
            not self.not_judged
            and self.full_frequency_range
            and room_level
            and radius_ok
            and np.all(self.band_met)
        )

    @property
    def discrete_frequency(self) -> bool:
        """Whether the qualification holds for tonal sources too (A.4.1).

        :return: ``True`` for a discrete-frequency qualification.
        """
        return self.bandwidth == "discrete-frequency"

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a FreeFieldCheck has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the qualified distance per frequency against the radius judged.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the radius bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.free_field import plot_free_field_check

        check_language(language)
        return plot_free_field_check(self, ax=ax, language=language, **kwargs)


def _collect_bands(fits: Sequence[InverseSquareLawResult]) -> list[_Band]:
    bands: list[_Band] = []
    seen: set[int] = set()
    for s, fit in enumerate(fits):
        for c, f in enumerate(fit.frequencies_hz):
            k = _band_index(float(f))
            if k in seen:
                msg = (
                    f"the band of {float(f):g} Hz is evaluated by two test sources; "
                    "give each frequency to one source."
                )
                raise ValueError(msg)
            seen.add(k)
            bands.append(_Band(k, float(f), s, c))
    return sorted(bands, key=lambda b: b.k)


def _run_verdict(
    run: Sequence[_Band],
    fits: Sequence[InverseSquareLawResult],
    radius: float,
    directionality: Sequence[SourceDirectionalityResult | None],
    speed_of_sound: float,
) -> list[_BandVerdict]:
    lowest = min(b.frequency_hz for b in run)
    return [
        _judge_band(
            b, fits[b.source], radius, lowest, directionality[b.source], speed_of_sound
        )
        for b in run
    ]


def _band_ok(v: _BandVerdict) -> bool:
    return (
        v.points
        and v.equal_spacing
        and v.spacing
        and v.spacing_iso26101
        and v.length
        and v.background is not False
        and v.directionality is not False
    )


def _path_targets_ok(fits: Sequence[InverseSquareLawResult]) -> bool | None:
    """A.3.3 a) to e): every source has a traverse towards each target.

    ``None`` when a source names no target on any of its traverses.
    """
    named = [{t for targets in fit.traverse_targets for t in targets} for fit in fits]
    if any(not n for n in named):
        return None
    return all(set(_PATH_TARGETS) <= n for n in named)


def _plane_ok(
    absorption: float | None,
    margin_m: float | None,
    lowest_hz: float,
    speed_of_sound: float,
) -> bool | None:
    if absorption is None or margin_m is None:
        return None
    needed = max(
        _wavelength_m(lowest_hz, speed_of_sound) / _WAVELENGTH_FRACTION_LENGTH,
        _MIN_PLANE_MARGIN_M,
    )
    return bool(
        absorption <= _MAX_PLANE_ABSORPTION + _SLACK and margin_m >= needed - _SLACK
    )


def _checked_plane(
    absorption: float | None, margin_m: float | None
) -> tuple[float | None, float | None]:
    """The A.2.5 inputs, refused when they cannot describe a plane."""
    if absorption is not None:
        value = float(absorption)
        if not 0.0 <= value <= 1.0:
            msg = (
                "'reflecting_plane_absorption_coefficient' must lie between 0 and 1; "
                f"got {absorption!r}."
            )
            raise ValueError(msg)
        absorption = value
    if margin_m is not None:
        margin_m = require_finite(margin_m, "reflecting_plane_margin_m")
    return absorption, margin_m


def _checked_declaration(value: object, name: str) -> bool | None:
    """A declaration that is True, False or None, and nothing that merely looks it."""
    if value is None:
        return None
    if not isinstance(value, (bool, np.bool_)):
        msg = (
            f"'{name}' must be True, False or None: a declaration of another type "
            "would be read as a verdict."
        )
        raise ValueError(msg)
    return bool(value)


def _checked_fits(
    results: InverseSquareLawResult | Sequence[InverseSquareLawResult],
    bandwidth: str,
) -> tuple[InverseSquareLawResult, ...]:
    """The results of every test source, all for one room, and a known bandwidth."""
    fits = (results,) if isinstance(results, InverseSquareLawResult) else tuple(results)
    if not fits:
        msg = "'results' must hold at least one InverseSquareLawResult."
        raise ValueError(msg)
    if bandwidth not in _BANDWIDTHS:
        msg = f"'bandwidth' must be 'discrete-frequency' or 'broadband'; got {bandwidth!r}."
        raise ValueError(msg)
    room = fits[0].room
    if any(fit.room != room for fit in fits):
        msg = "every result must be for the same room type."
        raise ValueError(msg)
    return fits


def _aligned_directionality(
    source_directionality: (
        SourceDirectionalityResult | Sequence[SourceDirectionalityResult | None] | None
    ),
    n_sources: int,
    room: str,
) -> tuple[SourceDirectionalityResult | None, ...]:
    """One directionality result, or ``None``, per test source, all for ``room``."""
    if isinstance(source_directionality, SourceDirectionalityResult) or (
        source_directionality is None
    ):
        directionality: tuple[SourceDirectionalityResult | None, ...] = (
            source_directionality,
        ) * n_sources
    else:
        directionality = tuple(source_directionality)
        if len(directionality) != n_sources:
            msg = (
                "'source_directionality' must hold one result per test source "
                f"({n_sources})."
            )
            raise ValueError(msg)
    if any(d is not None and d.room != room for d in directionality):
        msg = "the directionality result is for another room type."
        raise ValueError(msg)
    return directionality


def _free_field_not_judged(
    verdicts: Sequence[_BandVerdict],
    directionality: Sequence[SourceDirectionalityResult | None],
    *,
    plane_unjudged: bool,
    targets: bool | None,
    working: bool | None,
) -> tuple[str, ...]:
    """The requirements of the verdict whose data were not given, by name."""
    unjudged = (
        ("background", any(v.background is None for v in verdicts)),
        ("source directionality", any(d is None for d in directionality)),
        ("reflecting plane", plane_unjudged),
        ("path targets", targets is None),
        ("working area", working is None),
    )
    return tuple(name for name, missing in unjudged if missing)


def _judged_column(verdicts: Sequence[_BandVerdict], name: str) -> np.ndarray | None:
    """One flag per band, or ``None`` when a band was not judged on it."""
    values = [getattr(v, name) for v in verdicts]
    if any(value is None for value in values):
        return None
    return np.array(values, dtype=bool)


def check_free_field(
    results: InverseSquareLawResult | Sequence[InverseSquareLawResult],
    *,
    bandwidth: QualificationBandwidth,
    source_directionality: (
        SourceDirectionalityResult | Sequence[SourceDirectionalityResult | None] | None
    ) = None,
    measurement_radius_m: float | None = None,
    reflecting_plane_absorption_coefficient: float | None = None,
    reflecting_plane_margin_m: float | None = None,
    paths_in_working_area: bool | None = None,
    speed_of_sound: float = 343.0,
) -> FreeFieldCheck:
    """Is this room anechoic or hemi-anechoic enough for ISO 3745? (Annex A as amended).

    Judges the inverse-square-law analysis of one or more test sources
    (:func:`inverse_square_law_deviations`) against the amended ISO 3745:2012
    Annex A and the ISO 26101:2017 clauses it defers to (see the module
    notes). The radius of A.2.4 is the smallest qualified distance over every
    traverse and every evaluated frequency; the per-band requirements are
    judged within it. When the full range fails, the widest contiguous range
    that meets every requirement is reported as the reduced range A.2.3
    allows, "in conformity" but not "in full conformity".

    :param results: One :class:`InverseSquareLawResult` per test source, their
        frequencies disjoint, all for the same room.
    :param bandwidth: ``"discrete-frequency"`` (the default of A.4.1, tones or
        a narrow-band analysis) or ``"broadband"`` (noise in one-third octave
        bands, sufficient only for sources that radiate broadband noise).
    :param source_directionality: The :func:`verify_source_directionality`
        result of each test source (one, or a sequence aligned with
        ``results``); ``None`` leaves ISO 26101 Annex B unjudged.
    :param measurement_radius_m: The radius of the measurement surface to be
        used, in metres; the room must be qualified at least that far.
    :param reflecting_plane_absorption_coefficient: The largest sound
        absorption coefficient of the reflecting plane over the frequency
        range (A.2.5), hemi-anechoic only.
    :param reflecting_plane_margin_m: How far the reflecting plane extends
        beyond the projection of the measurement surface, in metres (A.2.5),
        hemi-anechoic only.
    :param paths_in_working_area: Whether the traverse paths lie in the
        working area of the room, the part normally used for measurements
        (A.3.3); a declaration, since the positions cannot tell. ``None``
        leaves it unjudged. The targets of A.3.3 a) to e) are read from
        :attr:`MicrophoneTraverse.targets`.
    :param speed_of_sound: Speed of sound, in m/s, for the wavelengths of
        A.4.3, ISO 26101 5.1.4.3 and A.2.5 (default 343).
    :return: :class:`FreeFieldCheck`.
    :raises ValueError: for results of different rooms, a frequency given to
        two sources, directionality results that do not align with
        ``results``, an unknown bandwidth, an absorption coefficient outside
        0 to 1, a margin that is not finite, or a working-area declaration
        that is not ``True``, ``False`` or ``None``.
    """
    fits = _checked_fits(results, bandwidth)
    room = fits[0].room
    speed = require_positive(speed_of_sound, "speed_of_sound")
    directionality = _aligned_directionality(source_directionality, len(fits), room)
    measurement = (
        None
        if measurement_radius_m is None
        else require_positive(measurement_radius_m, "measurement_radius_m")
    )
    hemi = room == "hemi-anechoic"
    absorption, margin = _checked_plane(
        reflecting_plane_absorption_coefficient, reflecting_plane_margin_m
    )
    if not hemi:
        absorption = margin = None
    working = _checked_declaration(paths_in_working_area, "paths_in_working_area")

    bands = _collect_bands(fits)
    band_radius = np.array(
        [fits[b.source].band_radius_m[b.column] for b in bands], dtype=np.float64
    )
    radius = float(band_radius.min())
    verdicts = _run_verdict(bands, fits, radius, directionality, speed)
    traverse_count = all(
        _MIN_TRAVERSES <= len(fit.traverse_names) <= _MAX_TRAVERSES for fit in fits
    )
    angles = all(_path_angles_ok(fit, radius) for fit in fits) if hemi else None
    lowest = bands[0].frequency_hz
    plane = _plane_ok(absorption, margin, lowest, speed) if hemi else None
    targets = _path_targets_ok(fits)
    not_judged = _free_field_not_judged(
        verdicts,
        directionality,
        plane_unjudged=hemi and plane is None,
        targets=targets,
        working=working,
    )

    evaluated = {b.k for b in bands}
    full = _grid_contiguous(_K_CORE_LOW, _K_CORE_HIGH, evaluated)
    conforming, conforming_radius = _widest_conforming_run(
        bands,
        fits,
        band_radius,
        directionality,
        speed,
        measurement,
        room_level=traverse_count and targets is not False and working is not False,
        hemi=hemi,
        absorption=absorption,
        margin=margin,
    )

    def column(name: str) -> np.ndarray:
        return np.array([getattr(v, name) for v in verdicts], dtype=bool)

    return FreeFieldCheck(
        room=room,
        bandwidth=bandwidth,
        results=fits,
        frequencies_hz=np.array([b.frequency_hz for b in bands], dtype=np.float64),
        band_radius_m=band_radius,
        maximum_qualified_radius_m=radius,
        measurement_radius_m=measurement,
        points_met=column("points"),
        equal_spacing_met=column("equal_spacing"),
        spacing_met=column("spacing"),
        iso26101_spacing_met=column("spacing_iso26101"),
        length_met=column("length"),
        background_met=_judged_column(verdicts, "background"),
        directionality_met=_judged_column(verdicts, "directionality"),
        traverse_count_met=traverse_count,
        path_targets_met=targets,
        working_area_met=working,
        path_angles_met=angles,
        reflecting_plane_met=plane,
        full_frequency_range=full,
        conforming_range_hz=conforming,
        conforming_radius_m=conforming_radius,
        not_judged=not_judged,
    )


def _contiguous_runs(bands: Sequence[_Band]) -> Iterator[tuple[int, int]]:
    """Every run ``bands[i..j]`` that leaves no evaluated band out, as ``(i, j)``."""
    evaluated = {b.k for b in bands}
    n = len(bands)
    for i in range(n):
        for j in range(i, n):
            if not _grid_contiguous(bands[i].k, bands[j].k, evaluated):
                break
            yield i, j


def _run_conforms(
    run: Sequence[_Band],
    radius: float,
    fits: Sequence[InverseSquareLawResult],
    directionality: Sequence[SourceDirectionalityResult | None],
    speed_of_sound: float,
    measurement: float | None,
    *,
    hemi: bool,
    absorption: float | None,
    margin: float | None,
) -> bool:
    """Whether a run of bands, qualified to ``radius``, meets every judged requirement."""
    if measurement is not None and radius < measurement - _SLACK:
        return False
    verdicts = _run_verdict(run, fits, radius, directionality, speed_of_sound)
    if not all(_band_ok(v) for v in verdicts):
        return False
    if not hemi:
        return True
    sources = {b.source for b in run}
    if not all(_path_angles_ok(fits[s], radius) for s in sources):
        return False
    return (
        _plane_ok(absorption, margin, run[0].frequency_hz, speed_of_sound) is not False
    )


def _widest_conforming_run(
    bands: Sequence[_Band],
    fits: Sequence[InverseSquareLawResult],
    band_radius: np.ndarray,
    directionality: Sequence[SourceDirectionalityResult | None],
    speed_of_sound: float,
    measurement: float | None,
    *,
    room_level: bool,
    hemi: bool,
    absorption: float | None,
    margin: float | None,
) -> tuple[tuple[float, float] | None, float]:
    """The widest contiguous run of bands that meets every judged requirement.

    ``room_level`` is whether the requirements that hold for every band at
    once (the traverse count, the path targets and the working area of A.3.3)
    are met or not judged.
    """
    if not room_level:
        return None, float("nan")
    best: tuple[int, float, int, int] | None = None
    for i, j in _contiguous_runs(bands):
        radius = float(band_radius[i : j + 1].min())
        if not _run_conforms(
            bands[i : j + 1],
            radius,
            fits,
            directionality,
            speed_of_sound,
            measurement,
            hemi=hemi,
            absorption=absorption,
            margin=margin,
        ):
            continue
        key = (bands[j].k - bands[i].k, radius, -i, j)
        if best is None or key > best:
            best = key
    if best is None:
        return None, float("nan")
    _, radius, neg_i, j = best
    i = -neg_i
    return (bands[i].frequency_hz, bands[j].frequency_hz), radius


__all__ = [
    "FreeFieldCheck",
    "InverseSquareLawResult",
    "MicrophoneTraverse",
    "SourceDirectionalityResult",
    "check_free_field",
    "directionality_positions",
    "directionality_tolerance_db",
    "inverse_square_law_deviations",
    "inverse_square_law_tolerance_db",
    "qualification_frequencies_hz",
    "verify_source_directionality",
]
