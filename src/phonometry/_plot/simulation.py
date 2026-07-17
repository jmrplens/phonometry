#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the simulation domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import _C_MUTED, _C_REFERENCE, _new_axes

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..simulation.fdtd import FDTDResult


def plot_fdtd_probes(
    result: "FDTDResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Pressure time history at each probe of an FDTD run.

    :param result: A :class:`~phonometry.simulation.fdtd.FDTDResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    t_ms = np.asarray(result.times, dtype=np.float64) * 1000.0
    for k in range(result.pressures.shape[0]):
        x, y = result.probe_positions[k]
        ax.plot(t_ms, result.pressures[k],
                label=f"probe ({x:.2f}, {y:.2f}) m", **kwargs)
    ax.set_xlabel("Time [ms]")
    ax.set_ylabel("Pressure [Pa]")
    ax.set_title("FDTD probe pressure")
    ax.grid(True, alpha=0.3)
    if result.pressures.shape[0]:
        ax.legend(loc="upper right", fontsize="small")
    return ax


def plot_fdtd_snapshot(
    result: "FDTDResult", ax: Axes | None = None, *, frame: int = -1,
    **kwargs: Any
) -> Axes:
    """One recorded pressure-field snapshot with the geometry overlaid.

    The field is rendered as a single raster image (``imshow``, symmetric
    diverging scale); rigid obstacle cells are drawn in grey and the source
    and probe cells are marked.

    :param result: A :class:`~phonometry.simulation.fdtd.FDTDResult` with
        recorded snapshots.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param frame: Snapshot index (default: the last recorded frame).
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    :raises ValueError: If the result holds no snapshots.
    """
    if result.snapshots is None or result.snapshot_times is None:
        raise ValueError("the result holds no snapshots; rerun the "
                         "simulation with snapshot_every set")
    ax = ax if ax is not None else _new_axes()
    field = np.asarray(result.snapshots[frame], dtype=np.float64)
    lx, ly = result.size
    extent = (0.0, lx, ly, 0.0)
    vmax = float(np.abs(field).max()) or 1.0
    img = ax.imshow(
        field,
        **{
            "cmap": "RdBu_r",
            "vmin": -vmax,
            "vmax": vmax,
            "origin": "upper",
            "extent": extent,
            "interpolation": "nearest",
            **kwargs,
        },
    )
    if result.obstacle_mask is not None:
        overlay = np.ma.masked_where(~result.obstacle_mask,
                                     np.ones(result.shape))
        ax.imshow(overlay, cmap="gray", vmin=0.0, vmax=2.0, origin="upper",
                  extent=extent, interpolation="nearest")
    for source in result.sources:
        ax.plot((source.ix + 0.5) * result.dx, (source.iy + 0.5) * result.dx,
                marker="*", markersize=10, color=_C_REFERENCE,
                linestyle="none")
    for k in range(result.probe_positions.shape[0]):
        x, y = result.probe_positions[k]
        ax.plot(x, y, marker="o", markersize=5, color=_C_MUTED,
                markeredgecolor="black", linestyle="none")
    ax.figure.colorbar(img, ax=ax, label="Pressure [Pa]")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    t_ms = float(result.snapshot_times[frame]) * 1000.0
    ax.set_title(f"FDTD pressure field at t = {t_ms:.2f} ms")
    return ax
