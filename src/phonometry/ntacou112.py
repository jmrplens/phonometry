#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Prominence of impulsive sounds and the LAeq adjustment (NT ACOU 112:2002).

Noise with prominent impulses is more annoying than a steady sound of the same
equivalent level, so the Nordtest method adds an adjustment ``KI`` to the
measured ``LAeq``. The audibility of an impulse is captured by the **predicted
prominence** ``P``, a logarithmic measure of the onset rate and the level
difference of the impulse (clause 7):

``P = 3*lg(onset_rate) + 2*lg(level_difference)``   (Formula 1)

From the impulse with the highest prominence over a 30-minute period, a
graduated adjustment follows (clause 8):

``KI = 1.8*(P - 5)`` dB for ``P > 5``, else ``0``   (Formula 2)

and the rating level over a reference time interval combines the adjusted
sub-interval levels (clause 8, Note 1). An impulse qualifies when its onset
rate exceeds 10 dB/s (clauses 4.5-4.7).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike

# ---------------------------------------------------------------------------
# Normative constants (NT ACOU 112:2002).
# ---------------------------------------------------------------------------

#: Coefficients ``(k1, k2)`` of ``P = k1*lg(onset_rate) + k2*lg(LD)`` (Formula 1).
PROMINENCE_COEFFS: tuple[float, float] = (3.0, 2.0)

#: Adjustment slope ``k3`` in ``KI = k3*(P - k4)`` (Formula 2).
ADJUSTMENT_SLOPE: float = 1.8

#: Prominence threshold ``k4`` below which no adjustment is made (Formula 2).
ADJUSTMENT_THRESHOLD: float = 5.0

#: Minimum onset rate, in dB/s, for a level rise to count as an impulse (4.5).
ONSET_RATE_LIMIT: float = 10.0


@dataclass(frozen=True)
class ImpulseProminence:
    """Prominence of a set of candidate impulses (NT ACOU 112:2002).

    :ivar onset_rates: Onset rate of each impulse, in dB/s.
    :ivar level_differences: Level difference of each impulse, in dB.
    :ivar per_impulse: Predicted prominence ``P`` of each impulse (Formula 1).
    :ivar prominence: The governing prominence (the highest ``P``, clause 7).
    :ivar adjustment: The LAeq adjustment ``KI``, in dB, of the governing
        impulse (Formula 2).
    """

    onset_rates: np.ndarray
    level_differences: np.ndarray
    per_impulse: np.ndarray
    prominence: float
    adjustment: float

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the adjustment curve ``KI(P)`` with the impulses marked.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_impulse_prominence

        return plot_impulse_prominence(self, ax=ax, **kwargs)


def predicted_prominence(
    onset_rate: ArrayLike, level_difference: ArrayLike
) -> np.ndarray:
    """Predicted prominence ``P`` of an impulse (NT ACOU 112, clause 7).

    ``P = 3*lg(onset_rate) + 2*lg(level_difference)`` (Formula 1), with ``lg``
    the base-10 logarithm. Both quantities are read from the A-weighted,
    time-weighting-F level history: the onset rate is the slope of the onset in
    dB/s and the level difference is the level rise over the onset in dB
    (clauses 4.6-4.7). An impulse qualifies when its onset rate exceeds
    :data:`ONSET_RATE_LIMIT` (10 dB/s).

    :param onset_rate: Onset rate(s), in dB/s (> 0).
    :param level_difference: Level difference(s), in dB (> 0).
    :return: The predicted prominence ``P`` (scalar inputs give a 0-d array).
    :raises ValueError: for a non-positive onset rate or level difference.
    """
    orate = np.asarray(onset_rate, dtype=np.float64)
    ld = np.asarray(level_difference, dtype=np.float64)
    if np.any(orate <= 0.0) or np.any(ld <= 0.0):
        raise ValueError("onset_rate and level_difference must be positive.")
    k1, k2 = PROMINENCE_COEFFS
    return k1 * np.log10(orate) + k2 * np.log10(ld)


def impulse_adjustment(prominence: ArrayLike) -> np.ndarray:
    """Adjustment ``KI`` to ``LAeq`` from the prominence (clause 8, Formula 2).

    ``KI = 1.8*(P - 5)`` dB for ``P > 5``, else ``0`` dB. The adjustment is made
    to ``LAeq,30min`` on the basis of the single impulse with the highest ``P``.

    :param prominence: Predicted prominence ``P``.
    :return: The adjustment ``KI``, in dB, clamped at zero.
    """
    p = np.asarray(prominence, dtype=np.float64)
    return np.maximum(ADJUSTMENT_SLOPE * (p - ADJUSTMENT_THRESHOLD), 0.0)


def impulse_prominence(
    onset_rates: ArrayLike, level_differences: ArrayLike
) -> ImpulseProminence:
    """Governing prominence and adjustment of a set of impulses (clauses 7-8).

    Evaluates the predicted prominence of each candidate impulse (Formula 1),
    takes the highest as the governing prominence (clause 7) and derives its
    ``LAeq`` adjustment (Formula 2).

    :param onset_rates: Onset rate of each impulse, in dB/s (> 0).
    :param level_differences: Level difference of each impulse, in dB (> 0).
    :return: An :class:`ImpulseProminence` with the per-impulse and governing
        values and ``.plot()``.
    :raises ValueError: for empty input, mismatched lengths, or a non-positive
        onset rate or level difference.
    """
    orate = np.asarray(onset_rates, dtype=np.float64).ravel()
    ld = np.asarray(level_differences, dtype=np.float64).ravel()
    if orate.size == 0:
        raise ValueError("at least one impulse is required.")
    if orate.shape != ld.shape:
        raise ValueError(
            f"onset_rates and level_differences must have the same shape; "
            f"got {orate.shape} and {ld.shape}."
        )
    per_impulse = predicted_prominence(orate, ld)
    governing = float(np.max(per_impulse))
    return ImpulseProminence(
        onset_rates=orate,
        level_differences=ld,
        per_impulse=per_impulse,
        prominence=governing,
        adjustment=float(impulse_adjustment(governing)),
    )


def rating_level(
    laeq: ArrayLike,
    adjustment: ArrayLike,
    durations: ArrayLike,
    reference_time: float,
) -> float:
    """Rating level over a reference time interval (clause 8, Note 1).

    Combines the impulse-adjusted equivalent levels of the measurement
    sub-intervals into a single rating level::

        LAr,T = 10*lg( (1/T) * sum_N dt_N * 10**((LAeq,N + KI,N) / 10) )

    :param laeq: Equivalent level ``LAeq,N`` of each sub-interval, in dB.
    :param adjustment: Adjustment ``KI,N`` of each sub-interval, in dB.
    :param durations: Duration ``dt_N`` of each sub-interval (any time unit,
        consistent with ``reference_time``).
    :param reference_time: Reference time interval ``T`` (same unit as
        ``durations``); commonly the sum of the durations.
    :return: The rating level ``LAr,T``, in dB.
    :raises ValueError: for mismatched lengths or a non-positive time.
    """
    le = np.atleast_1d(np.asarray(laeq, dtype=np.float64))
    ki = np.atleast_1d(np.asarray(adjustment, dtype=np.float64))
    dt = np.atleast_1d(np.asarray(durations, dtype=np.float64))
    if not le.shape == ki.shape == dt.shape:
        raise ValueError("laeq, adjustment and durations must have equal length.")
    if le.size == 0:
        raise ValueError("at least one sub-interval is required.")
    if reference_time <= 0.0 or np.any(dt <= 0.0):
        raise ValueError("reference_time and durations must be positive.")
    energy = np.sum(dt * 10.0 ** ((le + ki) / 10.0))
    return float(10.0 * np.log10(energy / reference_time))
