#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the metrology domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..metrology.compliance import FilterComplianceResult
    from ..metrology.correlation import (
        AlignedImpulseResponseResult,
        CorrelationResult,
        TimeDelayResult,
    )
    from ..metrology.envelope import EnvelopeResult
    from ..metrology.phase import PhaseDecompositionResult
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
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
)

#: Shared frequency-axis label of the spectral renderers.
_FREQ_LABEL = "Frequency [Hz]"

#: Spanish translations of the fixed strings rendered by the metrology
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
_STRINGS: dict[str, str] = {
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Lag [s]": "Retardo [s]",
    "Time [s]": "Tiempo [s]",
    "Amplitude": "Amplitud",
    "Magnitude [dB]": "Magnitud [dB]",
    "Phase [deg]": "Fase [grados]",
    "Phase [rad]": "Fase [rad]",
    "Class {cls} pass corridor": "Corredor de aceptación clase {cls}",
    r"Measured $\Delta A$": r"$\Delta A$ medida",
    "Out of tolerance": "Fuera de tolerancia",
    r"Normalised frequency $f\,/\,f_m$": r"Frecuencia normalizada $f\,/\,f_m$",
    "Relative attenuation [dB]": "Atenuación relativa [dB]",
    "IEC 61260-1 class {cls} mask — $f_m$ = {fm} Hz": "Máscara clase {cls} IEC 61260-1 — $f_m$ = {fm} Hz",
    r"Contribution to combined uncertainty $|c_i|\,u(x_i)$": r"Contribución a la incertidumbre combinada $|c_i|\,u(x_i)$",
    "GUM uncertainty budget — y = {value}": "Presupuesto de incertidumbre (GUM) — y = {value}",
    "{pct} % coverage interval": "Intervalo de cobertura {pct} %",
    "Output quantity y": "Magnitud de salida y",
    "Probability density": "Densidad de probabilidad",
    "Monte Carlo distribution (GUM Supplement 1) — u(y) = {uy}": "Distribución de Monte Carlo (GUM Suplemento 1) — u(y) = {uy}",
    "Spectral density [dB re 1/Hz]": "Densidad espectral [dB re 1/Hz]",
    "Power spectrum [dB]": "Espectro de potencia [dB]",
    r"{pct} % confidence ($\chi^2$, $n_d$ = {nd})": r"{pct} % de confianza ($\chi^2$, $n_d$ = {nd})",
    r"Welch spectral density — $\varepsilon_r$ = {er} %": r"Densidad espectral de Welch — $\varepsilon_r$ = {er} %",
    "Cross-spectral density (Bendat & Piersol)": "Densidad espectral cruzada (Bendat y Piersol)",
    r"$\pm$ s.d.$[\hat{\theta}_{xy}]$ (Eq. 9.52)": r"$\pm$ d.e.$[\hat{\theta}_{xy}]$ (Ec. 9.52)",
    r"$\hat{G}_{yy}$ (output)": r"$\hat{G}_{yy}$ (salida)",
    r"$\hat{G}_{nn}$ (noise)": r"$\hat{G}_{nn}$ (ruido)",
    "Coherent output spectrum (Bendat & Piersol 9.2.2)": "Espectro de salida coherente (Bendat y Piersol 9.2.2)",
    "Spectral SNR [dB]": "SNR espectral [dB]",
    "Correlation coefficient": "Coeficiente de correlación",
    "Correlation ({norm})": "Correlación ({norm})",
    "{kind} estimate (Bendat & Piersol)": "Estimación de {kind} (Bendat y Piersol)",
    "Autocorrelation": "autocorrelación",
    "Cross-correlation": "correlación cruzada",
    r"$\hat{R}_{xy}(\tau)$ (context)": r"$\hat{R}_{xy}(\tau)$ (contexto)",
    "95 % interval (Eq. 8.130)": "Intervalo 95 % (Ec. 8.130)",
    "Normalized correlation": "Correlación normalizada",
    "Time-delay estimate — {method}": "Estimación del retardo temporal — {method}",
    "Reference IR": "RI de referencia",
    "Aligned IR (delay {n} samples)": "RI alineada (retardo {n} muestras)",
    "Impulse-response alignment (sub-sample)": "Alineación de la respuesta al impulso (submuestra)",
    "Signal": "Señal",
    "Envelope $A(t)$ (Eq. 13.17)": "Envolvente $A(t)$ (Ec. 13.17)",
    "Hilbert envelope (Bendat & Piersol Ch. 13)": "Envolvente de Hilbert (Bendat y Piersol Cap. 13)",
    "Instantaneous frequency [Hz]": "Frecuencia instantánea [Hz]",
    "Measured phase": "Fase medida",
    "Minimum phase (from |H|)": "Fase mínima (de |H|)",
    "Excess phase (all-pass)": "Fase de exceso (pasa-todo)",
    "Phase decomposition": "Descomposición de fase",
    "Minimum-phase / all-pass decomposition": "Descomposición fase mínima / pasa-todo",
    "Group delay": "Retardo de grupo",
    "Excess group delay": "Retardo de grupo de exceso",
    "Group delay [ms]": "Retardo de grupo [ms]",
    "biased": "sesgada",
    "unbiased": "insesgada",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


# ---------------------------------------------------------------------------
# IEC 61260-1 filter class compliance
# ---------------------------------------------------------------------------


def _worst_band_index(result: "FilterComplianceResult") -> int:
    """Index of the band with the smallest margin to the reference class."""
    key = f"margin_class{result.reference_class()}_db"
    margins = [float(band[key]) for band in result.bands]
    return int(np.argmin(margins))


def plot_filter_class(
    result: "FilterComplianceResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Measured relative attenuation of the binding band over its class corridor.

    Selects the worst-margin band (the one whose margin to the achieved class
    is smallest, or, when the bank meets no class, the band that misses the
    loosest class by the most) and draws its measured relative attenuation
    ``ΔA`` against the normalized frequency ``f / f_m`` on a logarithmic axis.
    The acceptance corridor of the reference class is shaded green (between the
    lower and upper limits of Table 1) and any part of the measured curve that
    leaves the corridor is marked red, following the MATLAB
    ``octaveFilter.visualize`` convention.

    :param result: A
        :class:`~phonometry.metrology.compliance.FilterComplianceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from scipy import signal

    from .._i18n import format_number, localize_axes
    from ..metrology.compliance import class_limits

    ax = ax if ax is not None else _new_axes()
    cls = result.reference_class()
    idx = _worst_band_index(result)
    fm = float(result.band_frequencies[idx])
    fsd = result.fs / float(result.factors[idx])
    sos = np.asarray(result.sos[idx], dtype=np.float64)

    # Recompute the relative attenuation exactly as verify_filter_class does:
    # -20 lg|H| minus the attenuation at the exact mid-band frequency.
    eps = np.finfo(float).eps
    w, h = signal.sosfreqz(sos, worN=result.num_points, fs=fsd)
    attenuation = -20.0 * np.log10(np.abs(h) + eps)
    _, h_ref = signal.sosfreqz(sos, worN=np.array([fm]), fs=fsd)
    a_ref = float(-20.0 * np.log10(np.abs(h_ref[0]) + eps))
    delta_a = attenuation - a_ref
    omega = w / fm

    keep = omega > 0.0
    omega, delta_a = omega[keep], delta_a[keep]
    order = np.argsort(omega)
    omega, delta_a = omega[order], delta_a[order]

    lower, upper = class_limits(result.fraction, cls, omega, edition=result.edition)

    # Symmetric log window centred on the mid-band (f / f_m = 1).
    omega_max = float(omega[-1])
    lo_x, hi_x = 1.0 / omega_max, omega_max
    win = (omega >= lo_x) & (omega <= hi_x)
    if not np.any(win):
        # Degenerate band (mid-band at or above the decimated Nyquist), so the
        # symmetric window is empty; fail clearly instead of a cryptic reduction.
        raise ValueError(
            "Cannot plot the filter class corridor: the mid-band frequency is at "
            "or above the analysis Nyquist, so the f/f_m window is empty."
        )
    finite_upper = np.isfinite(upper)

    # Scale the axis to the mask, not to the measured curve: a steep bank
    # reaches hundreds of dB of attenuation deep in the stop-band, which would
    # squash the corridor to a sliver. The measured curve is allowed to leave
    # the top; what matters is that it stays inside the green corridor.
    corridor_top = float(np.max(lower[win]))
    y_top = max(20.0, float(np.ceil((corridor_top + 8.0) / 10.0) * 10.0))
    y_bot = min(-2.0, float(np.floor(np.min(delta_a[win]) - 1.0)))

    # Green acceptance corridor; the upper limit is +inf in the stop-band
    # (unbounded attenuation allowed), so it is clipped to the axis top there.
    upper_fill = np.where(finite_upper, upper, y_top)
    ax.fill_between(
        omega[win], lower[win], upper_fill[win], color=_C_TERTIARY, alpha=0.18,
        lw=0.0, label=_t("Class {cls} pass corridor", language, cls=cls),
    )
    ax.plot(omega[win], lower[win], color=_C_TERTIARY, lw=1.0, ls="--")
    fin = win & finite_upper
    ax.plot(omega[fin], upper[fin], color=_C_TERTIARY, lw=1.0, ls="--")

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("lw", 1.6)
    kwargs.setdefault("label", _t(r"Measured $\Delta A$", language))
    ax.plot(omega[win], delta_a[win], **kwargs)

    violated = (delta_a < lower - 1e-9) | (finite_upper & (delta_a > upper + 1e-9))
    viol_win = violated & win
    if np.any(viol_win):
        ax.plot(
            omega[viol_win], delta_a[viol_win], ls="", marker="o", ms=3.5,
            color=_C_REFERENCE, label=_t("Out of tolerance", language),
        )

    ax.axvline(1.0, color=_C_MUTED, ls=":", lw=1.0)
    _normalized_frequency_axis(ax, lo_x, hi_x)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(y_bot, y_top)
    ax.set_xlabel(_t(r"Normalised frequency $f\,/\,f_m$", language))
    ax.set_ylabel(_t("Relative attenuation [dB]", language))
    ax.set_title(
        _t("IEC 61260-1 class {cls} mask — $f_m$ = {fm} Hz", language, cls=cls,
           fm=format_number(fm, language, decimals=0))
    )
    ax.legend(loc="upper center", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def _normalized_frequency_axis(ax: Axes, lo: float, hi: float) -> None:
    """Label a logarithmic ``f / f_m`` axis with plain decimal ratios."""
    import matplotlib.ticker as mticker

    ax.set_xscale("log")
    ticks = [t for t in (0.25, 0.5, 0.7, 1.0, 1.4, 2.0, 4.0) if lo <= t <= hi]
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(
        mticker.FixedFormatter([f"{t:g}" for t in ticks])
    )
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())


def plot_uncertainty_budget(
    result: "UncertaintyResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Bar chart of each input's contribution to the combined uncertainty.

    :param result: An :class:`~phonometry.uncertainty.UncertaintyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`barh`.
    :return: The axes.
    """
    # The y-axis carries categorical input names (a FixedFormatter), so
    # localize_axes is intentionally not applied here: it would overwrite
    # those labels with comma-formatted tick numbers.
    from .._i18n import decimal_comma

    ax = ax if ax is not None else _new_axes()
    contributions = np.asarray(result.contributions, dtype=np.float64)
    names = list(result.names) or [f"x{i + 1}" for i in range(contributions.size)]
    positions = np.arange(contributions.size)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.barh(positions, contributions, **kwargs)
    uc = decimal_comma(f"{result.combined_uncertainty:.3g}", language)
    ax.axvline(result.combined_uncertainty, color=_C_REFERENCE, ls="--",
               label=f"$u_c$ = {uc}")
    ax.set_yticks(positions)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel(_t(r"Contribution to combined uncertainty $|c_i|\,u(x_i)$", language))
    value = decimal_comma(f"{result.value:.4g}", language)
    ax.set_title(_t("GUM uncertainty budget — y = {value}", language, value=value))
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(True, axis="x", alpha=0.3)
    return ax

def plot_monte_carlo(
    result: "MonteCarloResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Histogram of the Monte Carlo output with the coverage interval marked.

    :param result: A :class:`~phonometry.uncertainty.MonteCarloResult`
        obtained with ``keep_samples=True`` (the histogram needs the raw
        output sample).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.hist`.
    :return: The axes.
    :raises ValueError: If the result carries no output samples.
    """
    from .._i18n import decimal_comma, localize_axes

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
    pct = decimal_comma(f"{100.0 * result.coverage:g}", language)
    ax.axvspan(low, high, color=_C_PRIMARY, alpha=0.12,
               label=_t("{pct} % coverage interval", language, pct=pct))
    value = decimal_comma(f"{result.value:.4g}", language)
    ax.axvline(result.value, color=_C_REFERENCE, ls="--",
               label=f"y = {value}")
    ax.set_xlabel(_t("Output quantity y", language))
    ax.set_ylabel(_t("Probability density", language))
    uy = decimal_comma(f"{result.standard_uncertainty:.3g}", language)
    ax.set_title(_t("Monte Carlo distribution (GUM Supplement 1) — u(y) = {uy}", language, uy=uy))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def _db10(values: np.ndarray) -> np.ndarray:
    """``10·lg`` with -inf (not a warning) at empty bins."""
    with np.errstate(divide="ignore"):
        out: np.ndarray = 10.0 * np.log10(values)
    return out


def _psd_ylabel(scaling: str, language: str = "en") -> str:
    return (
        _t("Spectral density [dB re 1/Hz]", language)
        if scaling == "density"
        else _t("Power spectrum [dB]", language)
    )


def plot_spectral_density(
    result: "SpectralDensityResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Spectral density in dB with its chi-square confidence band.

    :param result: A :class:`~phonometry.metrology.spectra.SpectralDensityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the density ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)
    pct = decimal_comma(f"{100.0 * result.confidence:g}", language)
    nd = format_number(result.n_averages, language, decimals=1)
    ax.fill_between(
        freqs[pos],
        _db10(np.asarray(result.ci_lower, dtype=np.float64)[pos]),
        _db10(np.asarray(result.ci_upper, dtype=np.float64)[pos]),
        color=color,
        alpha=0.25,
        lw=0.0,
        label=_t(r"{pct} % confidence ($\chi^2$, $n_d$ = {nd})", language, pct=pct, nd=nd),
    )
    kwargs.setdefault("label", "$\\hat{G}_{xx}(f)$")
    ax.semilogx(freqs[pos], _db10(np.asarray(result.psd)[pos]), color=color, **kwargs)
    ax.set_xlabel(_t("Frequency [Hz]", language))
    ax.set_ylabel(_psd_ylabel(result.scaling, language))
    er = format_number(100.0 * result.random_error, language, decimals=1)
    ax.set_title(_t(r"Welch spectral density — $\varepsilon_r$ = {er} %", language, er=er))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    format_frequency_axis(ax, float(freqs[pos].min()), float(freqs[pos].max()))
    localize_axes(ax, language)
    return ax


def plot_cross_spectral_density(
    result: "CrossSpectralDensityResult",
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Cross-spectrum magnitude, phase (with ±σ band) and coherence.

    With ``ax`` given, only the magnitude panel is drawn on it.

    :param result: A
        :class:`~phonometry.metrology.spectra.CrossSpectralDensityResult`.
    :param ax: Existing axes for the magnitude panel, or ``None`` for a
        fresh three-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the magnitude ``plot`` call.
    :return: The magnitude axes (``ax`` given) or the array of three axes.
    """
    from .._i18n import localize_axes

    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _magnitude(axm: Axes) -> None:
        kwargs.setdefault("label", "$|\\hat{G}_{xy}(f)|$")
        axm.semilogx(
            freqs[pos], _db10(result.magnitude[pos]), color=color, **kwargs
        )
        axm.set_ylabel(_psd_ylabel(result.scaling, language))
        axm.grid(True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    fmin, fmax = float(freqs[pos].min()), float(freqs[pos].max())
    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel(_t("Frequency [Hz]", language))
        format_frequency_axis(ax, fmin, fmax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 7.0))
    _magnitude(axes[0])
    axes[0].set_title(_t("Cross-spectral density (Bendat & Piersol)", language))
    phase = np.degrees(result.phase[pos])
    # Cap the drawn band at +/-180 deg: at near-zero coherence the Eq. 9.52
    # s.d. diverges and a literal band would blow the panel's autoscale.
    sigma = np.minimum(np.degrees(result.phase_std[pos]), 180.0)
    finite = np.isfinite(sigma)
    axes[1].fill_between(
        freqs[pos][finite],
        (phase - sigma)[finite],
        (phase + sigma)[finite],
        color=_C_SECONDARY,
        alpha=0.3,
        lw=0.0,
        label=_t(r"$\pm$ s.d.$[\hat{\theta}_{xy}]$ (Eq. 9.52)", language),
    )
    axes[1].semilogx(freqs[pos], phase, color=color)
    axes[1].set_ylabel(_t("Phase [deg]", language))
    axes[1].grid(True, which="both", alpha=0.3)
    axes[1].legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    axes[2].semilogx(freqs[pos], result.coherence[pos], color=_C_MUTED)
    axes[2].set_ylabel("$\\gamma^2_{xy}$")
    axes[2].set_ylim(0.0, 1.05)
    axes[2].set_xlabel(_t("Frequency [Hz]", language))
    axes[2].grid(True, which="both", alpha=0.3)
    for axf in axes:
        format_frequency_axis(axf, fmin, fmax)
        localize_axes(axf, language)
    return axes


def plot_coherent_output_spectrum(
    result: "CoherentOutputSpectrumResult",
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Output, coherent and noise spectra plus the spectral SNR.

    With ``ax`` given, only the spectra panel is drawn on it.

    :param result: A
        :class:`~phonometry.metrology.spectra.CoherentOutputSpectrumResult`.
    :param ax: Existing axes for the spectra panel, or ``None`` for a fresh
        two-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the coherent-spectrum ``plot`` call.
    :return: The spectra axes (``ax`` given) or the array of two axes.
    """
    from .._i18n import localize_axes

    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0
    color = kwargs.pop("color", _C_PRIMARY)

    def _spectra_panel(axs: Axes) -> None:
        axs.semilogx(
            freqs[pos],
            _db10(result.output_psd[pos]),
            color=_C_MUTED,
            label=_t(r"$\hat{G}_{yy}$ (output)", language),
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
            label=_t(r"$\hat{G}_{nn}$ (noise)", language),
        )
        axs.set_ylabel(_psd_ylabel(result.scaling, language))
        axs.grid(True, which="both", alpha=0.3)
        axs.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    fmin, fmax = float(freqs[pos].min()), float(freqs[pos].max())
    if ax is not None:
        _spectra_panel(ax)
        ax.set_xlabel(_t("Frequency [Hz]", language))
        format_frequency_axis(ax, fmin, fmax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 5.6))
    _spectra_panel(axes[0])
    axes[0].set_title(_t("Coherent output spectrum (Bendat & Piersol 9.2.2)", language))
    axes[1].semilogx(freqs[pos], result.snr_db[pos], color=_C_SECONDARY)
    axes[1].axhline(0.0, color=_C_MUTED, ls=":", lw=1.0)
    axes[1].set_ylabel(_t("Spectral SNR [dB]", language))
    axes[1].set_xlabel(_t("Frequency [Hz]", language))
    axes[1].grid(True, which="both", alpha=0.3)
    for axf in axes:
        format_frequency_axis(axf, fmin, fmax)
        localize_axes(axf, language)
    return axes


_LAG_LABEL = "Lag [s]"
_TIME_AXIS_LABEL = "Time [s]"


def plot_correlation(
    result: "CorrelationResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Correlation estimate against the lag in seconds.

    :param result: A :class:`~phonometry.metrology.correlation.CorrelationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    symbol = (
        "\\hat{\\rho}" if result.normalization == "coefficient" else "\\hat{R}"
    )
    sub = "xx" if result.kind == "autocorrelation" else "xy"
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", f"${symbol}_{{{sub}}}(\\tau)$")
    ax.plot(result.lags, result.values, **kwargs)
    ax.axvline(0.0, color=_C_MUTED, ls=":", lw=1.0)
    ax.set_xlabel(_t("Lag [s]", language))
    if result.normalization == "coefficient":
        ax.set_ylabel(_t("Correlation coefficient", language))
    else:
        norm = (_t(result.normalization, language)
                if result.normalization in _STRINGS
                else result.normalization)
        ax.set_ylabel(_t("Correlation ({norm})", language, norm=norm))
    kind_en = result.kind.capitalize()
    kind = _t(kind_en, language) if kind_en in _STRINGS else kind_en
    ax.set_title(_t("{kind} estimate (Bendat & Piersol)", language, kind=kind))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_time_delay(
    result: "TimeDelayResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes:
    """Correlation function with the estimated delay marked.

    :param result: A :class:`~phonometry.metrology.correlation.TimeDelayResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the correlation ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    label = {
        "direct": "$\\hat{\\rho}_{xy}(\\tau)$",
        "gcc": f"GCC ({result.weighting})",
        "phase": _t(r"$\hat{R}_{xy}(\tau)$ (context)", language),
    }[result.method]
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", label)
    ax.plot(result.lags, result.correlation, **kwargs)
    if result.delay_interval is not None:
        ax.axvspan(
            result.delay_interval[0],
            result.delay_interval[1],
            color=_C_SECONDARY,
            alpha=0.25,
            lw=0.0,
            label=_t("95 % interval (Eq. 8.130)", language),
        )
    tau = decimal_comma(f"{1e3 * result.delay:.4g}", language)
    ax.axvline(
        result.delay,
        color=_C_REFERENCE,
        ls="--",
        label=f"$\\hat{{\\tau}}_0$ = {tau} ms",
    )
    ax.set_xlabel(_t("Lag [s]", language))
    ax.set_ylabel(
        _t("Correlation coefficient", language)
        if result.method == "direct"
        else _t("Normalized correlation", language)
    )
    ax.set_title(_t("Time-delay estimate — {method}", language, method=result.method))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_aligned_impulse_response(
    result: "AlignedImpulseResponseResult",
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Reference and aligned impulse responses overlaid.

    :param result: An
        :class:`~phonometry.metrology.correlation.AlignedImpulseResponseResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the aligned-IR ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    t = np.arange(result.reference.size) / result.fs
    ax.plot(t, result.reference, color=_C_MUTED, lw=1.0,
            label=_t("Reference IR", language))
    kwargs.setdefault("color", _C_PRIMARY)
    n = decimal_comma(f"{result.delay_samples:+.3f}", language)
    kwargs.setdefault("label", _t("Aligned IR (delay {n} samples)", language, n=n))
    ax.plot(t, result.aligned, lw=1.2, **kwargs)
    ax.set_xlabel(_t("Time [s]", language))
    ax.set_ylabel(_t("Amplitude", language))
    ax.set_title(_t("Impulse-response alignment (sub-sample)", language))
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    ax.grid(True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_envelope(
    result: "EnvelopeResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes | np.ndarray:
    """Signal with its Hilbert envelope, plus the instantaneous frequency.

    With ``ax`` given, only the signal/envelope panel is drawn on it.

    :param result: An :class:`~phonometry.metrology.envelope.EnvelopeResult`.
    :param ax: Existing axes for the envelope panel, or ``None`` for a
        fresh two-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the envelope ``plot`` call.
    :return: The envelope axes (``ax`` given) or the array of two axes.
    """
    from .._i18n import localize_axes

    t_signal = np.arange(result.signal.size) / result.signal_fs

    def _envelope_panel(axe: Axes) -> None:
        axe.plot(
            t_signal, result.signal, color=_C_MUTED, lw=0.7,
            label=_t("Signal", language)
        )
        kwargs.setdefault("color", _C_PRIMARY)
        kwargs.setdefault("label", _t("Envelope $A(t)$ (Eq. 13.17)", language))
        axe.plot(result.times, result.envelope, lw=1.8, **kwargs)
        axe.set_ylabel(_t("Amplitude", language))
        axe.grid(True, alpha=0.3)
        axe.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _envelope_panel(ax)
        ax.set_xlabel(_t("Time [s]", language))
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 5.6))
    _envelope_panel(axes[0])
    axes[0].set_title(_t("Hilbert envelope (Bendat & Piersol Ch. 13)", language))
    axes[1].plot(
        result.times,
        result.instantaneous_frequency,
        color=_C_SECONDARY,
        lw=1.0,
    )
    axes[1].set_ylabel(_t("Instantaneous frequency [Hz]", language))
    axes[1].set_xlabel(_t("Time [s]", language))
    axes[1].grid(True, alpha=0.3)
    for axf in axes:
        localize_axes(axf, language)
    return axes


def plot_phase_decomposition(
    result: "PhaseDecompositionResult", ax: Axes | None = None, *,
    language: str = "en", **kwargs: Any
) -> Axes | np.ndarray:
    """Magnitude, phase decomposition and group delay of a response.

    Three stacked panels: ``|H|`` in dB, the measured / minimum / excess
    phases in radians, and the total and excess group delays in
    milliseconds. With ``ax`` given, only the phase panel is drawn on it.

    :param result: A :class:`~phonometry.metrology.phase.PhaseDecompositionResult`.
    :param ax: Existing axes for the phase panel, or ``None`` for a fresh
        three-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-phase ``plot`` call.
    :return: The phase-panel axes (``ax`` given) or the array of three axes.
    """
    from .._i18n import localize_axes

    freqs = np.asarray(result.frequencies, dtype=np.float64)
    pos = freqs > 0.0

    def _phase_panel(axp: Axes) -> None:
        kwargs.setdefault("color", _C_PRIMARY)
        kwargs.setdefault("label", _t("Measured phase", language))
        axp.semilogx(freqs[pos], result.phase[pos], **kwargs)
        axp.semilogx(
            freqs[pos], result.minimum_phase[pos], color=_C_SECONDARY,
            ls="--", label=_t("Minimum phase (from |H|)", language),
        )
        axp.semilogx(
            freqs[pos], result.excess_phase[pos], color=_C_MUTED,
            label=_t("Excess phase (all-pass)", language),
        )
        axp.set_ylabel(_t("Phase [rad]", language))
        axp.grid(True, which="both", alpha=0.3)
        axp.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    fmin, fmax = float(freqs[pos].min()), float(freqs[pos].max())
    if ax is not None:
        _phase_panel(ax)
        ax.set_xlabel(_t("Frequency [Hz]", language))
        ax.set_title(_t("Phase decomposition", language))
        format_frequency_axis(ax, fmin, fmax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(3, sharex=True, figsize=(8.0, 8.0))
    tiny = np.finfo(np.float64).tiny
    axes[0].semilogx(
        freqs[pos],
        20.0 * np.log10(np.maximum(result.magnitude[pos], tiny)),
        color=_C_PRIMARY,
    )
    axes[0].set_ylabel(_t("Magnitude [dB]", language))
    axes[0].set_title(_t("Minimum-phase / all-pass decomposition", language))
    axes[0].grid(True, which="both", alpha=0.3)
    _phase_panel(axes[1])
    axes[2].semilogx(
        freqs[pos], 1e3 * result.group_delay[pos], color=_C_PRIMARY,
        label=_t("Group delay", language),
    )
    axes[2].semilogx(
        freqs[pos], 1e3 * result.excess_group_delay[pos], color=_C_MUTED,
        label=_t("Excess group delay", language),
    )
    axes[2].set_ylabel(_t("Group delay [ms]", language))
    axes[2].set_xlabel(_t("Frequency [Hz]", language))
    axes[2].grid(True, which="both", alpha=0.3)
    axes[2].legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    for axf in axes:
        format_frequency_axis(axf, fmin, fmax)
        localize_axes(axf, language)
    return axes
