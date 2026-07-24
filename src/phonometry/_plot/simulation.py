#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the simulation domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import _C_MUTED, _C_REFERENCE, _new_axes

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..simulation.fdtd import FDTDResult

#: Spanish translations of the fixed strings rendered by the simulation
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
_STRINGS: dict[str, str] = {
    "Time [ms]": "Tiempo [ms]",
    "Pressure [Pa]": "Presión [Pa]",
    "FDTD pressure field at t = {t_txt} ms": "Campo de presión FDTD en t = {t_txt} ms",
    "FDTD probe pressure": "Presión en las sondas FDTD",
    "probe": "sonda",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def plot_fdtd_probes(
    result: FDTDResult, ax: Axes | None = None, *, language: str = "en",
    **kwargs: Any
) -> Axes:
    """Pressure time history at each probe of an FDTD run.

    :param result: A :class:`~phonometry.simulation.fdtd.FDTDResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``Axes.plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    t_ms = np.asarray(result.times, dtype=np.float64) * 1000.0
    label = _t("probe", language)
    for k in range(result.pressures.shape[0]):
        x, y = result.probe_positions[k]
        px = format_number(x, language, decimals=2)
        py = format_number(y, language, decimals=2)
        ax.plot(t_ms, result.pressures[k],
                label=f"{label} ({px}, {py}) m", **kwargs)
    ax.set_xlabel(_t("Time [ms]", language))
    ax.set_ylabel(_t("Pressure [Pa]", language))
    ax.set_title(_t("FDTD probe pressure", language))
    ax.grid(True, alpha=0.3)
    if result.pressures.shape[0]:
        ax.legend(loc="upper right", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_fdtd_snapshot(
    result: FDTDResult, ax: Axes | None = None, *, frame: int = -1,
    language: str = "en", **kwargs: Any
) -> Axes:
    """One recorded pressure-field snapshot with the geometry overlaid.

    The field is rendered as a single raster image (``imshow``, symmetric
    diverging scale); rigid obstacle cells are drawn in grey and the source
    and probe cells are marked.

    :param result: A :class:`~phonometry.simulation.fdtd.FDTDResult` with
        recorded snapshots.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param frame: Snapshot index (default: the last recorded frame).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    :raises ValueError: If the result holds no snapshots.
    """
    from .._i18n import format_number, localize_axes

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
    ax.figure.colorbar(img, ax=ax, label=_t("Pressure [Pa]", language))
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    t_ms = float(result.snapshot_times[frame]) * 1000.0
    t_txt = format_number(t_ms, language, decimals=2)
    ax.set_title(_t("FDTD pressure field at t = {t_txt} ms", language, t_txt=t_txt))
    localize_axes(ax, language)
    return ax
