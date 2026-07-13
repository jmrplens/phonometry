#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the metrology domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..metrology.uncertainty import MonteCarloResult, UncertaintyResult

from .common import (
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_REFERENCE,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
)

def plot_uncertainty_budget(
    result: "UncertaintyResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Bar chart of each input's contribution to the combined uncertainty.

    :param result: An :class:`~phonometry.uncertainty.UncertaintyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to :meth:`barh`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    contributions = np.asarray(result.contributions, dtype=np.float64)
    names = list(result.names) or [f"x{i + 1}" for i in range(contributions.size)]
    positions = np.arange(contributions.size)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.barh(positions, contributions, **kwargs)
    ax.axvline(result.combined_uncertainty, color=_C_REFERENCE, ls="--",
               label=f"$u_c$ = {result.combined_uncertainty:.3g}")
    ax.set_yticks(positions)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Contribution to combined uncertainty $|c_i|\\,u(x_i)$")
    ax.set_title(f"GUM uncertainty budget — y = {result.value:.4g}")
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, axis="x", alpha=0.3)
    return ax

def plot_monte_carlo(
    result: "MonteCarloResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Histogram of the Monte Carlo output with the coverage interval marked.

    :param result: A :class:`~phonometry.uncertainty.MonteCarloResult`
        obtained with ``keep_samples=True`` (the histogram needs the raw
        output sample).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.hist`.
    :return: The axes.
    :raises ValueError: If the result carries no output samples.
    """
    if result.samples is None:
        raise ValueError(
            "plot() needs the Monte Carlo output samples; call "
            "monte_carlo(..., keep_samples=True) to retain them."
        )
    ax = ax if ax is not None else _new_axes()
    samples = np.asarray(result.samples, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY_LIGHT)
    kwargs.setdefault("bins", 120)
    kwargs.setdefault("density", True)
    ax.hist(samples, **kwargs)
    low, high = result.interval
    ax.axvspan(low, high, color=_C_PRIMARY, alpha=0.12,
               label=f"{100.0 * result.coverage:g} % coverage interval")
    ax.axvline(result.value, color=_C_REFERENCE, ls="--",
               label=f"y = {result.value:.4g}")
    ax.set_xlabel("Output quantity y")
    ax.set_ylabel("Probability density")
    ax.set_title(
        "Monte Carlo distribution (GUM Supplement 1) — "
        f"u(y) = {result.standard_uncertainty:.3g}"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    return ax
