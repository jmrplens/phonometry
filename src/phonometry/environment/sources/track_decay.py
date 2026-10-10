#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""How fast vibration dies away along a rail (EN 15461:2008+A1:2010).

A rail struck by a wheel carries the vibration away along itself as vertical
and lateral bending waves, and the length of rail that radiates rolling noise
is set by how fast those waves decay. The **track decay rate** is that
attenuation in decibels per metre, one value per one-third octave band (3.6),
and a vehicle type test by ISO 3095 needs a track whose decay rates are at
least the lower limits of its Figure 3
(:data:`~phonometry.environment.sources.rolling_stock_noise.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`).

**The measurement (clause 6).** An accelerometer is fixed to the rail at the
middle of a sleeper bay, and an instrumented hammer strikes the rail at a grid
of positions measured in sleeper bays from it: every quarter bay out to bay 2
and a half, then every half bay to bay 4, every bay to bay 8, and then at bays
10, 12, 16, 20, 24, 30, 36, 42, 48, 54 and 66 (6.7 and Figure 2,
:data:`TRACK_DECAY_EXCITATION_INDICES`). The frequency response between force
and response at each position, in mobility or accelerance, is reduced to its
one-third octave band magnitude :math:`A(x_n)`; the one at the accelerometer
itself is the direct response :math:`A(x_0)`.

**Clause 7 and Annex A, the rate.** If the response decayed as
:math:`A(x) = A(0)\,\mathrm{e}^{-\beta x}`, the decay rate would be
:math:`\mathrm{DR} = 20 \lg \mathrm{e}^{\beta} = 8{,}686\,\beta` dB/m, and the integral of the
squared response along the rail would be :math:`|A(0)|^2 / 2\beta` (A.1). The
standard estimates it from that integral rather than from a fitted slope,

.. math::

   \mathrm{DR} = \frac{4{,}343}{\displaystyle\sum_{n=0}^{n_\mathrm{max}}
            \frac{|A(x_n)|^2}{|A(x_0)|^2} \, \Delta x_n}\ \mathrm{dB/m}

(Formula 1, A.3), where :math:`\Delta x_n` is the length of rail each
position stands for: from halfway to the position before it to halfway to the
one after it, from 0 to halfway for the direct response and symmetrical about
the last position (A.2) (:func:`track_decay_rate`). The summation is dominated
by the first 10 dB of decay, which is what radiates.

**Formula 2, the floor.** A grid that stops at :math:`x_\mathrm{max}` cannot
measure a rate below :math:`\mathrm{DR}_\mathrm{min} = 4{,}343 / x_\mathrm{max}`; a
band whose rate is less than twice that is unsuitable, and its value only an
upper bound on the true one (clause 7). The response at the far end of the
grid also has to be at least 10 dB below the direct one in every band (6.7).

Read from BS EN 15461:2008+A1:2010, which is identical to EN
15461:2008+A1:2010 (its national foreword).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.validation import (
    require_choice,
    require_positive,
    require_positive_array,
)
from ._shared import _TOLERANCE

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "TRACK_DECAY_DIRECTIONS",
    "TRACK_DECAY_EXCITATION_INDICES",
    "TrackDecayRate",
    "track_decay_excitation_positions",
    "track_decay_rate",
]

#: 6.6: the two directions a decay rate is measured in, the vertical response
#: to a vertical force and the lateral (transverse) response to a lateral one.
TRACK_DECAY_DIRECTIONS: tuple[str, ...] = ("vertical", "lateral")

#: 6.7 and Figure 2: the positions of the hammer impacts, in sleeper bays from
#: the accelerometer at the middle of bay 0. Quarter bays out to 2,5, half
#: bays to 4, whole bays to 8, then the far field of Figure 2; the 29 points
#: Figure 2 draws. 6.7 asks for more beyond bay 66 when the decay is very low.
TRACK_DECAY_EXCITATION_INDICES: tuple[float, ...] = (
    0.0,
    0.25,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    1.75,
    2.0,
    2.25,
    2.5,
    3.0,
    3.5,
    4.0,
    5.0,
    6.0,
    7.0,
    8.0,
    10.0,
    12.0,
    16.0,
    20.0,
    24.0,
    30.0,
    36.0,
    42.0,
    48.0,
    54.0,
    66.0,
)

#: 6.7: the sleeper bay the grid assumes where the rail has no discrete
#: supports, in metres.
_DEFAULT_SLEEPER_SPACING_M = 0.6

#: Formula 1 and Formula 2: :math:`10 \lg e` rounded as the standard prints it,
#: half the 8,686 of A.2 because the summation is of squared amplitudes.
_DECAY_CONSTANT_DB = 4.343

#: Clause 7: a rate is suitable only when the floor of Formula 2 is at most
#: this fraction of it.
_SUITABLE_FRACTION = 0.5

#: 6.7: the drop the response at the farthest position must show below the
#: direct one, in decibels.
_FAR_FIELD_DROP_DB = 10.0

#: Formula 1 and A.2: the direct response and at least one position beyond it.
_MINIMUM_POSITIONS = 2


def track_decay_excitation_positions(
    *, sleeper_spacing_m: float = _DEFAULT_SLEEPER_SPACING_M
) -> NDArray[np.float64]:
    """The hammer positions of Figure 2, in metres from the accelerometer.

    :param sleeper_spacing_m: The distance between sleepers, in metres; the
        0,6 m 6.7 prescribes for a rail without periodic supports by default.
    :return: The 29 distances of :data:`TRACK_DECAY_EXCITATION_INDICES`
        times the sleeper spacing, read-only.
    :raises ValueError: For a spacing that is not positive.
    """
    spacing = require_positive(sleeper_spacing_m, "sleeper_spacing_m")
    return read_only(np.asarray(TRACK_DECAY_EXCITATION_INDICES) * spacing)


def _intervals(distances: NDArray[np.float64]) -> NDArray[np.float64]:
    """The length of rail each response stands for, A.2.

    From halfway to the previous position to halfway to the next; the direct
    response from 0 to halfway to the next, and the last position
    symmetrical about itself, so its interval is its distance from the one
    before.
    """
    midpoints = (distances[1:] + distances[:-1]) / 2.0
    lower = np.concatenate(([0.0], midpoints))
    last = distances[-1] + (distances[-1] - distances[-2]) / 2.0
    upper = np.concatenate((midpoints, [last]))
    return upper - lower


def _response_magnitudes(responses: ArrayLike, band_count: int) -> NDArray[np.float64]:
    """The responses as positive, finite magnitudes, one column per band.

    Formula 1 divides each by the direct response, so none may be zero, and a
    level in decibels, which may be negative, is not a magnitude. A single
    column may be given as a one-dimensional array.

    :raises ValueError: For a shape that is not one column per band, or a
        magnitude that is not positive and finite.
    """
    matrix = np.asarray(responses, dtype=np.float64)
    if matrix.ndim == 1:
        matrix = matrix[:, None]
    if matrix.ndim != 2 or matrix.shape[1] != band_count:  # noqa: PLR2004
        msg = "'responses' needs one row per position and one column per band."
        raise ValueError(msg)
    if not np.all(np.isfinite(matrix)) or np.any(matrix <= 0.0):
        msg = "'responses' are magnitudes and must be positive and finite."
        raise ValueError(msg)
    return matrix


def _excitation_grid(distances_m: ArrayLike) -> NDArray[np.float64]:
    """The excitation positions as the grid Formula 1 sums over.

    6.7 and Figure 2 put the direct response at the accelerometer, position
    0, and the impacts outward from it; A.2 gives each position the rail from
    halfway to the one before to halfway to the one after. So the grid is a
    finite one-dimensional array of at least two positions, the first at 0 m
    and each farther than the last.

    :raises ValueError: For a grid that is not that.
    """
    distances = np.atleast_1d(np.asarray(distances_m, dtype=np.float64))
    if distances.ndim != 1:
        msg = "'distances_m' must be one-dimensional, one distance per position."
        raise ValueError(msg)
    if distances.size < _MINIMUM_POSITIONS:
        msg = "'distances_m' needs at least the direct position and one more."
        raise ValueError(msg)
    if not np.all(np.isfinite(distances)):
        msg = "'distances_m' must be finite."
        raise ValueError(msg)
    if abs(distances[0]) > 0.0 or np.any(np.diff(distances) <= 0.0):
        msg = "'distances_m' must start at the accelerometer, 0 m, and increase."
        raise ValueError(msg)
    return distances


def _measurement(
    distances_m: ArrayLike, responses: ArrayLike, band_count: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The grid and the responses of a set of measurements, checked together.

    :raises ValueError: For what :func:`_response_magnitudes` and
        :func:`_excitation_grid` refuse, or a row count that is not the
        number of positions.
    """
    matrix = _response_magnitudes(responses, band_count)
    distances = _excitation_grid(distances_m)
    if distances.size != matrix.shape[0]:
        msg = f"'responses' has {matrix.shape[0]} rows for {distances.size} positions."
        raise ValueError(msg)
    return distances, matrix


@dataclass(frozen=True)
class TrackDecayRate(OwnsArrays):
    r"""The decay rates of a rail in one direction, by one-third octave band (EN 15461).

    Built by :func:`track_decay_rate` from a set of frequency responses, or
    directly from the rates of a report, which is all the ISO 3095 check
    needs.

    :param direction: ``"vertical"`` or ``"lateral"``.
    :param frequencies_hz: The nominal band frequencies, in hertz.
    :param decay_rates_db_per_m: The decay rate of each band, in dB/m.
    :param distances_m: The excitation positions, in metres from the
        accelerometer: the direct one at 0 m first, then strictly increasing,
        at least two in all; ``None`` for rates taken from a report.
    :param responses: The magnitude :math:`|A(x_n)|` of each response, one row
        per position and one column per band, positive and finite, in whatever
        unit the mobility or accelerance was measured in; ``None`` for rates
        taken from a report.
    """

    direction: str
    frequencies_hz: NDArray[np.float64]
    decay_rates_db_per_m: NDArray[np.float64]
    distances_m: NDArray[np.float64] | None = None
    responses: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Hold every array read-only and check that they agree.

        :raises ValueError: For an unknown direction, frequencies or rates
            that are not positive, frequencies that do not name distinct
            one-third octave bands in increasing order, arrays of different
            lengths, only one of the two measurement arrays, or a measurement
            :func:`track_decay_rate` refuses: a grid that is not finite, has
            fewer than two positions, does not start at 0 m or does not
            strictly increase, or responses that are not positive and finite.
        """
        require_choice(self.direction, "direction", TRACK_DECAY_DIRECTIONS)
        frequencies = require_positive_array(self.frequencies_hz, "frequencies_hz")
        bands = np.round(10.0 * np.log10(frequencies)).astype(np.int64)
        if np.any(np.diff(bands) <= 0):
            msg = (
                "'frequencies_hz' must name distinct one-third octave bands in "
                "increasing order."
            )
            raise ValueError(msg)
        rates = require_positive_array(
            self.decay_rates_db_per_m, "decay_rates_db_per_m"
        )
        if frequencies.size != rates.size:
            msg = "'frequencies_hz' and 'decay_rates_db_per_m' need one value per band each."
            raise ValueError(msg)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies))
        object.__setattr__(self, "decay_rates_db_per_m", read_only(rates))
        if (self.distances_m is None) != (self.responses is None):
            msg = "'distances_m' and 'responses' come together or not at all."
            raise ValueError(msg)
        if self.distances_m is not None and self.responses is not None:
            distances, responses = _measurement(
                self.distances_m, self.responses, frequencies.size
            )
            object.__setattr__(self, "distances_m", read_only(distances))
            object.__setattr__(self, "responses", read_only(responses))

    @property
    def minimum_measurable_db_per_m(self) -> float | None:
        r"""The floor :math:`4{,}343 / x_\mathrm{max}` of Formula 2, in dB/m; ``None`` without the grid."""
        if self.distances_m is None:
            return None
        return float(_DECAY_CONSTANT_DB / self.distances_m[-1])

    @property
    def suitable(self) -> NDArray[np.bool_]:
        """Per band, whether the floor of Formula 2 is at most half the rate (clause 7).

        A band that is not is an upper bound on the true rate. Every band is
        taken as suitable when the grid is not known.
        """
        floor = self.minimum_measurable_db_per_m
        if floor is None:
            return np.ones(self.frequencies_hz.size, dtype=bool)
        return np.asarray(
            floor <= _SUITABLE_FRACTION * self.decay_rates_db_per_m + _TOLERANCE
        )

    @property
    def far_field_drops_db(self) -> NDArray[np.float64] | None:
        """How far the response at the farthest position is below the direct one, per band, in dB (6.7)."""
        if self.responses is None:
            return None
        return np.asarray(20.0 * np.log10(self.responses[0] / self.responses[-1]))

    @property
    def far_field_sufficient(self) -> bool | None:
        """Whether the farthest response is at least 10 dB below the direct one in every band (6.7)."""
        drops = self.far_field_drops_db
        if drops is None:
            return None
        return bool(np.all(drops >= _FAR_FIELD_DROP_DB - _TOLERANCE))

    def rate_at(self, frequency_hz: float) -> float:
        """The decay rate of the band a nominal frequency names, in dB/m.

        :param frequency_hz: A nominal band frequency, in hertz.
        :return: The rate of that band.
        :raises KeyError: If the spectrum has no such band.
        """
        band = round(10.0 * np.log10(require_positive(frequency_hz, "frequency_hz")))
        bands = np.round(10.0 * np.log10(self.frequencies_hz)).astype(int)
        matches = np.flatnonzero(bands == band)
        if matches.size == 0:
            msg = f"the rates have no band at {frequency_hz:g} Hz."
            raise KeyError(msg)
        return float(self.decay_rates_db_per_m[matches[0]])

    def plot(
        self,
        ax: Axes | None = None,
        *,
        limit_db_per_m: Mapping[float, float] | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the rates as EN 15461 9.2 presents them.

        Decay rate on a logarithmic axis from 0,01 dB/m to 100 dB/m against
        equidistant one-third octave bands, with the bands clause 7 finds
        unsuitable marked and a lower limit drawn when one is given.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param limit_db_per_m: A lower limit, nominal frequency to rate, such
            as one direction of
            :data:`~phonometry.environment.sources.rolling_stock_noise.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the rate line.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_track_decay_rate

        check_language(language)
        return plot_track_decay_rate(
            self, ax, limit_db_per_m=limit_db_per_m, language=language, **kwargs
        )


def track_decay_rate(
    responses: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    distances_m: ArrayLike | None = None,
    sleeper_spacing_m: float = _DEFAULT_SLEEPER_SPACING_M,
    direction: str = "vertical",
) -> TrackDecayRate:
    r"""The decay rate of a rail from its responses along it (clause 7, Formula 1).

    .. math::

       \mathrm{DR} = \frac{4{,}343}{\displaystyle\sum_{n=0}^{n_\mathrm{max}}
                \frac{|A(x_n)|^2}{|A(x_0)|^2} \, \Delta x_n}

    in each band, with :math:`\Delta x_n` the length of rail each position
    stands for (A.2). Mobility and accelerance give the same rates, since only
    the ratio to the direct response enters.

    :param responses: The one-third octave band magnitudes :math:`|A(x_n)|`,
        one row per excitation position, nearest first, the direct response in
        the first row, and one column per band. Magnitudes, not levels: a
        level in decibels is ``10 ** (level / 20)``.
    :param frequencies_hz: The nominal frequency of each band, in hertz; 6.6
        asks for at least 100 Hz to 5 000 Hz.
    :param distances_m: The excitation positions, in metres from the
        accelerometer, starting at 0 and increasing. When omitted, the 29
        positions of Figure 2 at ``sleeper_spacing_m``.
    :param sleeper_spacing_m: The sleeper spacing the Figure 2 grid is laid
        out in, in metres, when ``distances_m`` is omitted.
    :param direction: ``"vertical"`` or ``"lateral"``.
    :return: The rates, with the grid and the responses they came from.
    :raises ValueError: For responses that are not positive and finite, a
        grid that is not finite, has fewer than two positions, does not start
        at 0 or does not strictly increase, frequencies that do not name
        distinct bands in increasing order, or shapes that do not agree.
    """
    frequencies = require_positive_array(frequencies_hz, "frequencies_hz")
    grid: ArrayLike = (
        track_decay_excitation_positions(sleeper_spacing_m=sleeper_spacing_m)
        if distances_m is None
        else distances_m
    )
    distances, matrix = _measurement(grid, responses, frequencies.size)
    ratios = (matrix / matrix[0]) ** 2
    accumulated = _intervals(distances) @ ratios
    rates = _DECAY_CONSTANT_DB / accumulated
    return TrackDecayRate(
        direction=direction,
        frequencies_hz=frequencies,
        decay_rates_db_per_m=rates,
        distances_m=distances,
        responses=matrix,
    )
