#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a screen on the shop floor is worth (ISO 11821:1997).

A **removable screen** is a panel or a flexible curtain put between a machine
and the people near it, breaking the line of sight and nothing more. It is the
cheapest thing in noise control and the hardest to quote a number for, because
what it is worth depends on the room it stands in as much as on the screen.

ISO 11821 measures that number where the screen stands. The quantity is an
insertion loss, the difference between the level at a position with the screen
removed and the level at the same position with it in place:

.. math::

   D_p = L_{p1} - L_{p2}

Clause 5.8 prints that without an equation number, and the whole of the
standard is arranging for those two levels to be comparable.

What it is not for
------------------

The Introduction draws three lines. A screen in an open-plan office is
ISO 10053; an outdoor community-noise barrier is ISO 10847, which is
:mod:`phonometry.environment.propagation.barrier_in_situ`; and this method is
not a qualification of a screen as a product but a measurement of one
installation. Indoors the room decides a large part of the answer, so two
screens may only be compared where the test conditions were the same.

Within its own scope it wants a screen at least 1,5 m high and 1,5 m long, and
outdoors it stops at 25 m from the screen.

One number or several
---------------------

Where the screen protects a defined operator position, 5.5.1 puts three
microphones on a sphere of 0,3 m radius around the head and the answer is one
number. Where it shields an area, 5.5.2 puts them along a line perpendicular
to the screen at a quarter, a half, once and twice the screen height, never
closer than 1 m, and the answer is a range: NOTE 2 says the smallest
attenuation will be found at the most remote position and the largest at the
nearest, which is why the Introduction asks for the maximum and the minimum
rather than a mean.

The two guards worth knowing
----------------------------

Clause 5.7 corrects for the background with the ordinary energy subtraction,
not with a table, and it draws two hard lines: under 6 dB "the environmental
conditions are not acceptable", and over 10 dB there is nothing to correct.
:func:`background_corrected_level_db` refuses the first and skips the second.

Clause 5.9 is the other: the A-weighted attenuation :math:`D_{pA}` **shall not
be determined when an artificial sound source is used**, because an A-weighted
number belongs to the spectrum that produced it and a loudspeaker's spectrum is
not the machine's. :func:`screen_attenuation` refuses it rather than compute a
number the standard forbids.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from .._internal.levels_math import energy_mean
from .._internal.validation import (
    require_choice,
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .._internal.warnings import PhonometryWarning
from .cabin_insulation import OPERATOR_SPHERE_RADIUS_M

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "ISO11821_BAND_RANGE_HZ",
    "BACKGROUND_CORRECTION_WINDOW_DB",
    "DIRECTIVITY_CIRCLE_RADIUS_M",
    "DIRECTIVITY_INDEX_LIMIT_DB",
    "DIRECTIVITY_POSITIONS",
    "ENGINEERING_STANDARD_DEVIATION_DB",
    "IMPULSE_INVALID_DEVIATION_DB",
    "IMPULSE_REPEATS",
    "IMPULSE_REPEAT_DEVIATION_DB",
    "ISO11821_MINIMUM_BACKGROUND_MARGIN_DB",
    "MINIMUM_MICROPHONE_DISTANCE_M",
    "MINIMUM_SCREEN_DIMENSION_M",
    "OPERATOR_HEIGHT_M",
    "OPERATOR_HEIGHT_TOLERANCE_M",
    "OPERATOR_SPHERE_RADIUS_M",
    "OUTDOOR_RANGE_M",
    "ISO11821_PREFERRED_BACKGROUND_MARGIN_DB",
    "SCREEN_DISTANCE_FACTORS",
    "ScreenInSituResult",
    "ScreenInSituWarning",
    "background_corrected_level_db",
    "directivity_index_db",
    "impulse_mean_level_db",
    "microphone_distances_m",
    "screen_attenuation",
]

#: 5.2.1 and 5.2.2: the margin over the background the level behind the screen
#: must keep, and the margin the standard would rather have.
ISO11821_MINIMUM_BACKGROUND_MARGIN_DB: float = 6.0
ISO11821_PREFERRED_BACKGROUND_MARGIN_DB: float = 10.0

#: 5.7: the window inside which the background correction is made. Under the
#: first value the environmental conditions are not acceptable; over the
#: second there is nothing to correct.
BACKGROUND_CORRECTION_WINDOW_DB: tuple[float, float] = (6.0, 10.0)

#: 3.10: the directivity index is read over twelve positions evenly spaced on
#: a horizontal circle of this radius, in metres, around the source.
DIRECTIVITY_POSITIONS: int = 12
DIRECTIVITY_CIRCLE_RADIUS_M: float = 1.5

#: 5.2.2: an artificial source qualifies while its directivity index stays
#: under this, in decibels, in every one of the twelve positions.
DIRECTIVITY_INDEX_LIMIT_DB: float = 8.0

#: 5.2.2: the band range the measurement covers, by band fraction.
ISO11821_BAND_RANGE_HZ: dict[int, tuple[float, float]] = {
    3: (100.0, 5000.0),
    1: (125.0, 4000.0),
}

#: 5.5.2 and the key to Figure 2: the height a microphone stands at where no
#: operator height is specified, in metres, and its tolerance.
OPERATOR_HEIGHT_M: float = 1.55
OPERATOR_HEIGHT_TOLERANCE_M: float = 0.075

#: 5.5.2: the four distances from the screen, as multiples of its height.
SCREEN_DISTANCE_FACTORS: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0)

#: 5.5.2: no microphone stands closer than this to the screen, in metres,
#: whatever the height says.
MINIMUM_MICROPHONE_DISTANCE_M: float = 1.0

#: The Introduction: the method holds for a screen at least this high and this
#: long, in metres, and a smaller one by agreement.
MINIMUM_SCREEN_DIMENSION_M: float = 1.5

#: The Introduction: outdoors the measurement stops at this distance from the
#: screen, in metres, and goes further by agreement.
OUTDOOR_RANGE_M: float = 25.0

#: 5.6.2.1: how many times an impulsive measurement is repeated, the spread
#: that asks for three more, and the spread that invalidates it.
IMPULSE_REPEATS: int = 3
IMPULSE_REPEAT_DEVIATION_DB: float = 3.0
IMPULSE_INVALID_DEVIATION_DB: float = 5.0

#: Clause 6: the standard deviation of the mean, in decibels, which is the
#: engineering grade of accuracy and the only uncertainty number printed.
ENGINEERING_STANDARD_DEVIATION_DB: float = 2.0

SourceKind = Literal["actual", "artificial"]
_SOURCE_KINDS: tuple[str, ...] = ("actual", "artificial")


class ScreenInSituWarning(PhonometryWarning):
    """The measurement is outside a condition ISO 11821 states."""


def background_corrected_level_db(
    levels_db: ArrayLike, background_levels_db: ArrayLike
) -> NDArray[np.float64]:
    r"""The level with the background taken off, clause 5.7.

    .. math::

       L_p = 10 \lg \left(10^{L_{ps}/10} - 10^{L_{pb}/10}\right)

    The plain energy subtraction, applied band by band at each measurement
    position. Where ISO 11820 corrects from a stepped table, this standard
    prints the formula and boxes it.

    Clause 5.7 draws the window itself. A margin over 10 dB needs no
    correction and the level is returned unchanged. A margin under 6 dB means
    "the environmental conditions are not acceptable", which is a refusal and
    not a warning: the background it names includes wind-generated noise, so
    the remedy is to wait for a quieter day rather than to correct harder.

    :param levels_db: The level with the sources on, per band, in decibels.
    :param background_levels_db: The level with them off, per band, in
        decibels.
    :return: The corrected level per band, in decibels.
    :raises ValueError: For inputs that do not match band for band, or a
        margin under :data:`ISO11821_MINIMUM_BACKGROUND_MARGIN_DB`.
    """
    levels = require_finite_array(levels_db, "levels_db")
    background = require_finite_array(background_levels_db, "background_levels_db")
    if levels.shape != background.shape:
        msg = "'levels_db' and 'background_levels_db' must match band for band."
        raise ValueError(msg)
    lower, upper = BACKGROUND_CORRECTION_WINDOW_DB
    margin = levels - background
    if float(np.min(margin)) < lower:
        msg = (
            f"ISO 11821 5.7 calls the environmental conditions unacceptable "
            f"under {lower:g} dB over the background, wind-generated noise "
            f"included; the smallest margin is {float(np.min(margin)):.1f} dB."
        )
        raise ValueError(msg)
    corrected = 10.0 * np.log10(10.0 ** (levels / 10.0) - 10.0 ** (background / 10.0))
    return np.asarray(np.where(margin > upper, levels, corrected), dtype=np.float64)


def directivity_index_db(levels_db: ArrayLike) -> NDArray[np.float64]:
    r"""The directivity index of a source, definition 3.10.

    :math:`DI_i = L_{360} - L_{30,i}`, where :math:`L_{360}` is the
    logarithmic mean of the levels at twelve positions evenly spaced on a
    horizontal circle of about 1,5 m radius around the source, and
    :math:`L_{30,i}` the level at one of them.

    The sign is the way round to notice. Written as the mean less the
    position, the index is **positive where the position is quieter than the
    mean**, which is the opposite of the directivity index of the emission
    standards. Clause 5.2.2 then reads naturally: an artificial source
    qualifies while no position falls more than
    :data:`DIRECTIVITY_INDEX_LIMIT_DB` below the mean, which is a bound on how
    much of a shadow the source casts on itself.

    :param levels_db: The levels at the twelve positions, in decibels.
    :return: :math:`DI_i` at each position, in decibels.
    :raises ValueError: For a count that is not
        :data:`DIRECTIVITY_POSITIONS`.
    """
    levels = require_finite_array(levels_db, "levels_db")
    if levels.size != DIRECTIVITY_POSITIONS:
        msg = (
            f"Definition 3.10 of ISO 11821 reads the directivity index over "
            f"{DIRECTIVITY_POSITIONS} positions on a circle; got "
            f"{levels.size}."
        )
        raise ValueError(msg)
    return np.asarray(float(energy_mean(levels)) - levels, dtype=np.float64)


def microphone_distances_m(screen_height_m: float) -> NDArray[np.float64]:
    r"""Where the microphones stand in front of a screen, 5.5.2.

    A quarter, a half, once and twice the screen height, along a line
    perpendicular to the screen, and never closer than
    :data:`MINIMUM_MICROPHONE_DISTANCE_M`. Under 4 m the quarter-height
    position falls inside that floor and is pushed out to it; at 2 m and under
    the half-height one is pushed out too, and then the two nearest positions
    coincide. The clause keeps the floor rather than the factor, so the
    returned distances may repeat, and that is the printed rule rather than an
    oversight here.

    NOTE 2 of 5.5.2 says what the spread of the answers means: the smallest
    attenuation will be found at the most remote position and the largest at
    the nearest, which is why the Introduction asks for both rather than for
    an average.

    :param screen_height_m: The screen height, in metres.
    :return: The four distances from the screen, in metres.
    :raises ValueError: For a non-positive height.
    """
    height = require_positive(screen_height_m, "screen_height_m")
    if height < MINIMUM_SCREEN_DIMENSION_M:
        msg = (
            f"ISO 11821 applies to a screen at least "
            f"{MINIMUM_SCREEN_DIMENSION_M:g} m high and long, and a smaller "
            f"one only by agreement; this one is {height:g} m."
        )
        warnings.warn(msg, ScreenInSituWarning, stacklevel=2)
    factors = np.asarray(SCREEN_DISTANCE_FACTORS, dtype=np.float64)
    return np.maximum(factors * height, MINIMUM_MICROPHONE_DISTANCE_M)


def impulse_mean_level_db(repeat_levels_db: ArrayLike) -> float:
    r"""The level of an impulsive measurement, 5.6.2.1.

    A single-impulse source is measured at least three times with the S time
    weighting, and the level is the **arithmetic** mean of the repeats, not
    the energy mean: the clause says "arithmetic mean values" and means it.

    The spread decides whether the set counts. Past
    :data:`IMPULSE_REPEAT_DEVIATION_DB` the clause asks for three more
    repeats, which is reported here; past
    :data:`IMPULSE_INVALID_DEVIATION_DB` the measurement is invalid, which is
    refused.

    :param repeat_levels_db: The levels of the repeats, in decibels.
    :return: The arithmetic mean, in decibels.
    :raises ValueError: For fewer than :data:`IMPULSE_REPEATS` repeats or a
        spread past :data:`IMPULSE_INVALID_DEVIATION_DB`.
    """
    levels = require_finite_array(repeat_levels_db, "repeat_levels_db")
    if levels.size < IMPULSE_REPEATS:
        msg = (
            f"ISO 11821 5.6.2.1 repeats an impulsive measurement at least "
            f"{IMPULSE_REPEATS} times; got {levels.size}."
        )
        raise ValueError(msg)
    spread = float(np.max(levels) - np.min(levels))
    if spread > IMPULSE_INVALID_DEVIATION_DB:
        msg = (
            f"ISO 11821 5.6.2.1 calls the measurement invalid past a "
            f"{IMPULSE_INVALID_DEVIATION_DB:g} dB deviation; this set spreads "
            f"{spread:.1f} dB."
        )
        raise ValueError(msg)
    if spread > IMPULSE_REPEAT_DEVIATION_DB:
        msg = (
            f"ISO 11821 5.6.2.1 asks for {IMPULSE_REPEATS} more repeats past a "
            f"{IMPULSE_REPEAT_DEVIATION_DB:g} dB deviation; this set spreads "
            f"{spread:.1f} dB."
        )
        warnings.warn(msg, ScreenInSituWarning, stacklevel=2)
    return float(np.mean(levels))


@dataclass(frozen=True)
class ScreenInSituResult:
    r"""The in-situ attenuation of a removable screen, ISO 11821 clause 5.8.

    :ivar frequencies: Nominal band centres, in hertz, or ``None``.
    :ivar unscreened_levels_db: :math:`L_{p1}`, the level with the screen
        removed, per band.
    :ivar screened_levels_db: :math:`L_{p2}`, the level with it in place, per
        band.
    :ivar attenuation_db: :math:`D_p` per band, in decibels.
    :ivar a_weighted_attenuation_db: :math:`D_{pA}`, in decibels, or ``None``.
        Clause 5.9 allows it only with the actual source.
    :ivar source_kind: ``"actual"`` or ``"artificial"``.
    :ivar distance_m: How far the position stands from the screen, in metres,
        or ``None``.
    """

    frequencies: NDArray[np.float64] | None
    unscreened_levels_db: NDArray[np.float64]
    screened_levels_db: NDArray[np.float64]
    attenuation_db: NDArray[np.float64]
    a_weighted_attenuation_db: float | None
    source_kind: str
    distance_m: float | None

    def rounded(self) -> NDArray[np.int_]:
        """The band values as 7.4 c) reports them, to the nearest integer.

        :attr:`attenuation_db` keeps the unrounded difference. A tie goes to
        the even decibel, Rule A of ISO 80000-1:2009 Annex B, as in the other
        in-situ standards of this library.
        """
        return np.asarray(np.rint(self.attenuation_db), dtype=np.int_)

    def rounded_a_weighted(self) -> int | None:
        """:math:`D_{pA}` as 7.4 c) reports it, to the nearest integer.

        The clause gives the A-weighted attenuation the same rounding as the
        band values. ``None`` where no A-weighted pair was given.
        """
        if self.a_weighted_attenuation_db is None:
            return None
        return int(np.rint(self.a_weighted_attenuation_db))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the two levels and the attenuation between them.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.noise_control.plot_screen_in_situ`.
        :return: The :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.noise_control import plot_screen_in_situ

        check_language(language)
        return plot_screen_in_situ(self, ax=ax, language=language, **kwargs)


def screen_attenuation(
    unscreened_levels_db: ArrayLike,
    screened_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    source_kind: SourceKind = "actual",
    a_weighted_unscreened_level_db: float | None = None,
    a_weighted_screened_level_db: float | None = None,
    distance_m: float | None = None,
) -> ScreenInSituResult:
    r"""The in-situ attenuation of a screen, clauses 5.8 and 5.9.

    :math:`D_p = L_{p1} - L_{p2}`, the unscreened level less the screened one
    at the same position, band by band. Clause 5.8 adds the condition that
    makes the subtraction mean anything: either both levels are time-averaged,
    or both are arithmetic means of several :math:`L_{S\text{max}}` values.
    The two kinds are not mixed, and :func:`impulse_mean_level_db` is the
    second of them.

    :math:`D_{pA} = L_{pA1} - L_{pA2}` is clause 5.9, and it carries the
    standard's one flat prohibition: it **shall not be determined when an
    artificial sound source is used**. An A-weighted number belongs to the
    spectrum that produced it, and a loudspeaker's spectrum is not the
    machine's, so the pair is refused rather than computed under
    ``source_kind="artificial"``.

    :param unscreened_levels_db: :math:`L_{p1}` per band, in decibels.
    :param screened_levels_db: :math:`L_{p2}` per band, in decibels.
    :param frequencies: Nominal band centres, in hertz.
    :param source_kind: ``"actual"`` (default) or ``"artificial"``.
    :param a_weighted_unscreened_level_db: :math:`L_{pA1}`, in decibels.
    :param a_weighted_screened_level_db: :math:`L_{pA2}`, in decibels.
    :param distance_m: How far this position stands from the screen, in
        metres, carried into the result because 5.5.2 reports the spread over
        the line rather than one number.
    :return: The attenuation, as a :class:`ScreenInSituResult`.
    :raises ValueError: For spectra that do not match, a band centre or a
        distance that is not strictly positive, an unknown source kind, half an
        A-weighted pair, or an A-weighted pair with an artificial source.
    """
    unscreened = require_finite_array(unscreened_levels_db, "unscreened_levels_db")
    screened = require_finite_array(screened_levels_db, "screened_levels_db")
    if unscreened.shape != screened.shape:
        msg = (
            "'unscreened_levels_db' and 'screened_levels_db' must match band for band."
        )
        raise ValueError(msg)
    kind = require_choice(str(source_kind), "source_kind", _SOURCE_KINDS)
    freqs: NDArray[np.float64] | None = None
    if frequencies is not None:
        freqs = require_positive_array(frequencies, "frequencies")
        if freqs.shape != unscreened.shape:
            msg = "'frequencies' must match the spectra band for band."
            raise ValueError(msg)
    weighted: float | None = None
    given = (
        a_weighted_unscreened_level_db is not None,
        a_weighted_screened_level_db is not None,
    )
    if any(given):
        if not all(given):
            msg = (
                "Clause 5.9 is a difference, so give both "
                "'a_weighted_unscreened_level_db' and "
                "'a_weighted_screened_level_db' or neither."
            )
            raise ValueError(msg)
        if kind == "artificial":
            msg = (
                "ISO 11821 5.9: the A-weighted attenuation D_pA shall not be "
                "determined when an artificial sound source is used."
            )
            raise ValueError(msg)
        weighted = require_finite(
            a_weighted_unscreened_level_db or 0.0, "a_weighted_unscreened_level_db"
        ) - require_finite(
            a_weighted_screened_level_db or 0.0, "a_weighted_screened_level_db"
        )
    return ScreenInSituResult(
        frequencies=freqs,
        unscreened_levels_db=unscreened,
        screened_levels_db=screened,
        attenuation_db=np.asarray(unscreened - screened, dtype=np.float64),
        a_weighted_attenuation_db=weighted,
        source_kind=kind,
        distance_m=(
            None if distance_m is None else require_positive(distance_m, "distance_m")
        ),
    )
