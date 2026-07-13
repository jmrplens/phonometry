#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Noise-Power-Distance (NPD) event-level interpolation (ECAC Doc 29).

The ECAC Doc 29 airport-noise method describes an aircraft's noise emission with
**Noise-Power-Distance (NPD)** tables: the event noise level (``LAmax`` or the
sound exposure level ``SEL``) of an aircraft in steady straight flight on an
infinite path, tabulated over a grid of engine power settings and slant
distances at reference conditions. Placing an aircraft's noise at a receiver
starts by reading a level from this table for an arbitrary power and distance.

* :func:`npd_level` -- the interpolated event level ``L(P, d)``, linear in power
  and log-linear in distance (Eqs. 4-3/4-4), with extrapolation beyond the
  tabulated envelope.
* :func:`npd_curve` -- the level over a distance sweep at one power, returned as
  an :class:`NpdLevelResult` with a ``.plot()``.

This is the NPD engine that underpins the segmentation and contour stages of the
method (deferred). Source (clean-room, implemented from the standard text):
ECAC Doc 29, 4th ed., Vol 2 (2016), §4.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray


def _clean_table(
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    levels: "NDArray[np.float64] | list[list[float]]",
) -> "tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]":
    p = np.asarray(powers, dtype=np.float64).ravel()
    d = np.asarray(distances, dtype=np.float64).ravel()
    lv = np.asarray(levels, dtype=np.float64)
    if p.size < 2 or d.size < 2:
        raise ValueError("'powers' and 'distances' must each have at least two values.")
    if lv.shape != (p.size, d.size):
        raise ValueError("'levels' must have shape (len(powers), len(distances)).")
    if not (np.all(np.isfinite(p)) and np.all(np.isfinite(d)) and np.all(np.isfinite(lv))):
        raise ValueError("'powers', 'distances' and 'levels' must be finite.")
    if np.any(d <= 0.0):
        raise ValueError("'distances' must be strictly positive (slant range in m).")
    if np.any(np.diff(p) <= 0.0):
        raise ValueError("'powers' must be strictly increasing.")
    if np.any(np.diff(d) <= 0.0):
        raise ValueError("'distances' must be strictly increasing.")
    return p, d, lv


def _interp_distance(logd_tab: "NDArray[np.float64]", row: "NDArray[np.float64]",
                     logd: "NDArray[np.float64]") -> "NDArray[np.float64]":
    """Log-linear interpolation/extrapolation of one NPD row over distance (Eq. 4-4)."""
    idx = np.clip(np.searchsorted(logd_tab, logd) - 1, 0, logd_tab.size - 2)
    x0 = logd_tab[idx]
    x1 = logd_tab[idx + 1]
    y0 = row[idx]
    y1 = row[idx + 1]
    return np.asarray(y0 + (y1 - y0) / (x1 - x0) * (logd - x0), dtype=np.float64)


@dataclass(frozen=True)
class NpdLevelResult:
    """NPD event level over a distance sweep at one power (ECAC Doc 29).

    :ivar distance: Slant distances, in metres.
    :ivar level: Interpolated event level per distance, in dB.
    :ivar power: The engine power setting queried.
    :ivar table_distances: The tabulated slant distances, in metres.
    :ivar table_levels: The tabulated levels at the queried power, in dB.
    """

    distance: "NDArray[np.float64]"
    level: "NDArray[np.float64]"
    power: float
    table_distances: "NDArray[np.float64]"
    table_levels: "NDArray[np.float64]"

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the interpolated level versus slant distance (log axis)."""
        from ._plotting import plot_npd_level

        return plot_npd_level(self, ax=ax, **kwargs)


def npd_level(
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    levels: "NDArray[np.float64] | list[list[float]]",
    power: float,
    distance: "NDArray[np.float64] | list[float] | float",
) -> "NDArray[np.float64]":
    """Interpolated NPD event level ``L(P, d)`` (ECAC Doc 29 §4.2, Eqs. 4-3/4-4).

    Interpolates log-linearly in slant distance (Eq. 4-4) at the two bracketing
    tabulated powers, then linearly in power (Eq. 4-3). Queries outside the
    tabulated envelope are extrapolated from the terminal segments.

    :param powers: Tabulated engine power settings (1-D, strictly increasing).
    :param distances: Tabulated slant distances, in metres (1-D, strictly
        increasing, positive).
    :param levels: Tabulated event levels, shape ``(len(powers), len(distances))``,
        in dB.
    :param power: Query engine power setting ``P``.
    :param distance: Query slant distance(s) ``d``, in metres.
    :return: The interpolated event level per query distance, in dB.
    :raises ValueError: If the table or inputs are invalid.
    """
    p, d, lv = _clean_table(powers, distances, levels)
    dq = np.atleast_1d(np.asarray(distance, dtype=np.float64))
    if dq.size == 0 or not np.all(np.isfinite(dq)) or np.any(dq <= 0.0):
        raise ValueError("'distance' must be finite and strictly positive.")
    pq = float(power)
    if not np.isfinite(pq):
        raise ValueError("'power' must be finite.")

    logd_tab = np.log10(d)
    logdq = np.log10(dq)
    # Log-linear interpolation over distance for every tabulated power row.
    rows = np.array([_interp_distance(logd_tab, lv[i], logdq) for i in range(p.size)])
    # Linear interpolation/extrapolation over power between the bracketing rows.
    j = int(np.clip(np.searchsorted(p, pq) - 1, 0, p.size - 2))
    frac = (pq - p[j]) / (p[j + 1] - p[j])
    return np.asarray(rows[j] + (rows[j + 1] - rows[j]) * frac, dtype=np.float64)


def npd_curve(
    powers: "NDArray[np.float64] | list[float]",
    distances: "NDArray[np.float64] | list[float]",
    levels: "NDArray[np.float64] | list[list[float]]",
    power: float,
    query_distances: "NDArray[np.float64] | list[float] | None" = None,
) -> NpdLevelResult:
    """NPD event level over a distance sweep at one power setting.

    :param powers: Tabulated engine power settings.
    :param distances: Tabulated slant distances, in metres.
    :param levels: Tabulated event levels, shape ``(len(powers), len(distances))``.
    :param power: Query engine power setting.
    :param query_distances: Distances to evaluate, in metres; defaults to a log
        sweep across the tabulated envelope.
    :return: An :class:`NpdLevelResult`.
    :raises ValueError: If the inputs are invalid.
    """
    p, d, lv = _clean_table(powers, distances, levels)
    if query_distances is None:
        dq = np.logspace(np.log10(d[0]), np.log10(d[-1]), 200)
    else:
        dq = np.atleast_1d(np.asarray(query_distances, dtype=np.float64))
    level = npd_level(p, d, lv, power, dq)
    row = npd_level(p, d, lv, power, d)  # tabulated levels at the queried power
    return NpdLevelResult(
        distance=dq,
        level=level,
        power=float(power),
        table_distances=d,
        table_levels=row,
    )
