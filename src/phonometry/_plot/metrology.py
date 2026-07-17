#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the metrology domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..metrology.spectra import (
        CoherentOutputSpectrumResult,
        CrossSpectralDensityResult,
        SpectralDensityResult,
    )
    from ..metrology.uncertainty import MonteCarloResult, UncertaintyResult

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_REFERENCE,
    _C_SECONDARY,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
    _new_axes_column,
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


def _db10(values: np.ndarray) -> np.ndarray:
    """``10·lg`` with -inf (not a warning) at empty bins."""
    with np.errstate(divide="ignore"):
        out: np.ndarray = 10.0 * np.log10(values)
    return out


def _psd_ylabel(scaling: str) -> str:
    return (
        "Spectral density [dB re 1/Hz]"
        if scaling == "density"
        else "Power spectrum [dB]"
    )


def plot_spectral_density(
    result: "SpectralDensityResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Spectral density in dB with its chi-square confidence band.

    :param result: A :class:`~phonometry.metrology.spectra.SpectralDensityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the density ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)
    ax.fill_between(
        freqs[pos],
        _db10(np.asarray(result.ci_lower, dtype=np.float64)[pos]),
        _db10(np.asarray(result.ci_upper, dtype=np.float64)[pos]),
        color=color,
        alpha=0.25,
        lw=0.0,
        label=f"{100.0 * result.confidence:g} % confidence ($\\chi^2$, "
        f"$n_d$ = {result.n_averages:.1f})",
    )
    kwargs.setdefault("label", "$\\hat{G}_{xx}(f)$")
    ax.semilogx(freqs[pos], _db10(np.asarray(result.psd)[pos]), color=color, **kwargs)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(_psd_ylabel(result.scaling))
    ax.set_title(
        "Welch spectral density — "
        f"$\\varepsilon_r$ = {100.0 * result.random_error:.1f} %"
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_cross_spectral_density(
    result: "CrossSpectralDensityResult",
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Cross-spectrum magnitude, phase (with ±σ band) and coherence.

    With ``ax`` given, only the magnitude panel is drawn on it.

    :param result: A
        :class:`~phonometry.metrology.spectra.CrossSpectralDensityResult`.
    :param ax: Existing axes for the magnitude panel, or ``None`` for a
        fresh three-panel figure.
    :param kwargs: Forwarded to the magnitude ``plot`` call.
    :return: The magnitude axes (``ax`` given) or the array of three axes.
    """
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _magnitude(axm: Axes) -> None:
        kwargs.setdefault("label", "$|\\hat{G}_{xy}(f)|$")
        axm.semilogx(
            freqs[pos], _db10(result.magnitude[pos]), color=color, **kwargs
        )
        axm.set_ylabel(_psd_ylabel(result.scaling))
        axm.grid(True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel("Frequency [Hz]")
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 7.0))
    _magnitude(axes[0])
    axes[0].set_title("Cross-spectral density (Bendat & Piersol)")
    phase = np.degrees(result.phase[pos])
    sigma = np.degrees(result.phase_std[pos])
    finite = np.isfinite(sigma)
    axes[1].fill_between(
        freqs[pos][finite],
        (phase - sigma)[finite],
        (phase + sigma)[finite],
        color=_C_SECONDARY,
        alpha=0.3,
        lw=0.0,
        label="$\\pm$ s.d.$[\\hat{\\theta}_{xy}]$ (Eq. 9.52)",
    )
    axes[1].semilogx(freqs[pos], phase, color=color)
    axes[1].set_ylabel("Phase [deg]")
    axes[1].grid(True, which="both", alpha=0.3)
    axes[1].legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    axes[2].semilogx(freqs[pos], result.coherence[pos], color=_C_MUTED)
    axes[2].set_ylabel("$\\gamma^2_{xy}$")
    axes[2].set_ylim(0.0, 1.05)
    axes[2].set_xlabel("Frequency [Hz]")
    axes[2].grid(True, which="both", alpha=0.3)
    return axes


def plot_coherent_output_spectrum(
    result: "CoherentOutputSpectrumResult",
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Output, coherent and noise spectra plus the spectral SNR.

    With ``ax`` given, only the spectra panel is drawn on it.

    :param result: A
        :class:`~phonometry.metrology.spectra.CoherentOutputSpectrumResult`.
    :param ax: Existing axes for the spectra panel, or ``None`` for a fresh
        two-panel figure.
    :param kwargs: Forwarded to the coherent-spectrum ``plot`` call.
    :return: The spectra axes (``ax`` given) or the array of two axes.
    """
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _spectra_panel(axs: Axes) -> None:
        axs.semilogx(
            freqs[pos],
            _db10(result.output_psd[pos]),
            color=_C_MUTED,
            label="$\\hat{G}_{yy}$ (output)",
        )
        kwargs.setdefault(
            "label", "$\\hat{G}_{vv} = \\hat{\\gamma}^2_{xy}\\hat{G}_{yy}$"
        )
        axs.semilogx(freqs[pos], _db10(result.coherent_psd[pos]), color=color,
                     **kwargs)
        axs.semilogx(
            freqs[pos],
            _db10(result.noise_psd[pos]),
            color=_C_REFERENCE,
            ls="--",
            label="$\\hat{G}_{nn}$ (noise)",
        )
        axs.set_ylabel(_psd_ylabel(result.scaling))
        axs.grid(True, which="both", alpha=0.3)
        axs.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _spectra_panel(ax)
        ax.set_xlabel("Frequency [Hz]")
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 5.6))
    _spectra_panel(axes[0])
    axes[0].set_title("Coherent output spectrum (Bendat & Piersol 9.2.2)")
    axes[1].semilogx(freqs[pos], result.snr_db[pos], color=_C_SECONDARY)
    axes[1].axhline(0.0, color=_C_MUTED, ls=":", lw=1.0)
    axes[1].set_ylabel("Spectral SNR [dB]")
    axes[1].set_xlabel("Frequency [Hz]")
    axes[1].grid(True, which="both", alpha=0.3)
    return axes
