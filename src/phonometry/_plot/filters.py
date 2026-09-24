#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the filters domain (lazy imports from result .plot())."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from ..filters.compliance import FilterComplianceResult
    from ..filters.core import OctaveFilterResult
    from ..filters.equalizer import EQResponseResult
    from ..filters.periodic_tests import (
        FilterPeriodicVerification,
        PeriodicTestClause,
    )
    from ..filters.time_invariance import TimeInvarianceResult
    from ..filters.weighting import TimeWeightedEnvelope
    from ..metrology.conformance import ConformanceVerification

from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _LEGEND_UPPER_RIGHT,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
    place_legend_clear,
    style_default,
    style_pop,
    theme_fill,
    theme_line,
)

#: Cap on how many per-section light magnitude lines of the parametric-EQ
#: cascade get their own legend entry; sections past the eighth still draw
#: but unlabeled, keeping the legend from swallowing the axes.
_MAX_LABELED_SECTIONS = 8

#: Spanish translations of the fixed strings rendered by the filters
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
#: Axis label shared by the class-corridor and the EQ renderers.
_FREQ_LABEL = "Frequency [Hz]"
#: Per-channel legend entry, shared by the two renderers that draw one
#: line per channel. It is a format string: ``_t`` fills the ``n``.
_CHANNEL_LABEL = "Channel {n}"
#: Axis label of every plot drawn against the normalised frequency.
_NORMALISED_FREQ_LABEL = r"Normalised frequency $f\,/\,f_{\mathrm{m}}$"
#: Axis label of the plots drawn against the mid-band frequency.
_MID_BAND_LABEL = "Mid-band frequency [Hz]"
#: Legend entry of a result IEC 61260-3 5.3 makes unusable.
_UNUSABLE_LABEL = "Unusable (§5.3)"
#: Title of a periodic-test panel: ``_t`` fills the clause and the verdict.
_PERIODIC_TITLE = "IEC 61260-3 {clause}: {verdict}"

_STRINGS: dict[str, str] = {
    _FREQ_LABEL: "Frecuencia [Hz]",
    "Magnitude [dB]": "Magnitud [dB]",
    "Phase [deg]": "Fase [grados]",
    "Class {cls} pass corridor": "Corredor de aceptación clase {cls}",
    r"Measured $\Delta A$": r"$\Delta A$ medida",
    "Out of tolerance": "Fuera de tolerancia",
    _NORMALISED_FREQ_LABEL: r"Frecuencia normalizada $f\,/\,f_{\mathrm{m}}$",
    "Relative attenuation [dB]": "Atenuación relativa [dB]",
    # The mid-band subscript is upright (m abbreviates "mid-band", as
    # IEC 61260-1:2014 5.4.1 prints it); its braces are doubled because this
    # title is the one string here that goes through ``str.format``.
    r"IEC 61260-1 class {cls} mask: $f_{{\mathrm{{m}}}}$ = {fm} Hz": r"Máscara clase {cls} IEC 61260-1: $f_{{\mathrm{{m}}}}$ = {fm} Hz",
    "lowpass": "paso bajo",
    "highpass": "paso alto",
    "magnitude": "magnitud",
    "Cascade": "Cascada",
    "Parametric EQ response (Audio EQ Cookbook)": "Respuesta del EQ paramétrico (Audio EQ Cookbook)",
    "peaking": "campana",
    "lowshelf": "shelf de graves",
    "highshelf": "shelf de agudos",
    "bandpass": "paso banda",
    "bandpass_skirt": "paso banda (faldón)",
    "notch": "muesca",
    "allpass": "paso todo",
    _CHANNEL_LABEL: "Canal {n}",
    "Time [s]": "Tiempo [s]",
    "Sound pressure level [dB re 20 uPa]": "Nivel de presión sonora [dB re 20 uPa]",
    "Mean square [FS²]": "Media cuadrática [FS²]",
    "{mode} time-weighted level": "Nivel con ponderación temporal {mode}",
    "fast": "rápida",
    "slow": "lenta",
    "impulse": "impulsiva",
    "Band level [dB]": "Nivel de banda [dB]",
    "Band levels": "Niveles de banda",
    "Band centre frequency [Hz]": "Frecuencia central de banda [Hz]",
    _MID_BAND_LABEL: "Frecuencia central de banda [Hz]",
    r"Effective bandwidth deviation $\Delta B$ [dB]": r"Desviación del ancho de banda efectivo $\Delta B$ [dB]",
    r"$\Delta B$ per band": r"$\Delta B$ por banda",
    "Class {cls} limits": "Límites clase {cls}",
    "IEC 61260-1 §5.12 effective bandwidth: class {cls}": "Ancho de banda efectivo IEC 61260-1 §5.12: clase {cls}",
    "IEC 61260-1 §5.12 effective bandwidth: no class": "Ancho de banda efectivo IEC 61260-1 §5.12: ninguna clase",
    r"Summed output $\Delta P_j$ [dB]": r"Salida sumada $\Delta P_j$ [dB]",
    r"$\Delta P_j$ of each band": r"$\Delta P_j$ de cada banda",
    r"Binding band, $f_{{\mathrm{{m}}}}$ = {fm} Hz": r"Banda determinante, $f_{{\mathrm{{m}}}}$ = {fm} Hz",
    "IEC 61260-1 §5.16 summation of outputs: class {cls}": "Suma de salidas IEC 61260-1 §5.16: clase {cls}",
    "IEC 61260-1 §5.16 summation of outputs: no class": "Suma de salidas IEC 61260-1 §5.16: ninguna clase",
    r"Deviation from $L_{\mathrm{c}}$ [dB]": r"Desviación respecto a $L_{\mathrm{c}}$ [dB]",
    "{rate} s per decade": "{rate} s por década",
    "IEC 61260-1 §5.14 time-invariant operation: class {cls}": "Funcionamiento invariante en el tiempo IEC 61260-1 §5.14: clase {cls}",
    "IEC 61260-1 §5.14 time-invariant operation: no class": "Funcionamiento invariante en el tiempo IEC 61260-1 §5.14: ninguna clase",
    "Margin to the nearer acceptance limit [dB]": "Margen hasta el límite de aceptación más próximo [dB]",
    "Acceptance limit": "Límite de aceptación",
    "Conforms": "Conforme",
    "Does not conform": "No conforme",
    _UNUSABLE_LABEL: "No utilizable (§5.3)",
    "conforms": "conforme",
    "does not conform": "no conforme",
    _PERIODIC_TITLE: _PERIODIC_TITLE,
    "IEC 61260-3 periodic tests, class {cls}: {verdict}": "Ensayos periódicos IEC 61260-3, clase {cls}: {verdict}",
    "not usable (§5.3)": "no utilizable (§5.3)",
    "passed": "superados",
    "not passed": "no superados",
    "Clause": "Apartado",
    "Measurement": "Medida",
}


def _t(text: str, language: str = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


#: The Table 1 breakpoint, as the exponent of G, past which the class figure
#: of a band does not open its window: G**2, where the stop band asks for
#: 40 dB and more.
_WINDOW_EXPONENT = 2.0


def _worst_band_index(result: FilterComplianceResult) -> int:
    """Index of the band with the smallest margin to the reference class."""
    key = f"margin_class{result.reference_class()}_db"
    margins = [float(band[key]) for band in result.bands]
    return int(np.argmin(margins))


def plot_filter_class(
    result: FilterComplianceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
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
        :class:`~phonometry.filters.compliance.FilterComplianceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from scipy import signal

    from .._i18n import format_number, localize_axes
    from ..filters.compliance import _map_breakpoint, class_limits

    ax = ax if ax is not None else _new_axes()
    cls = result.reference_class()
    idx = _worst_band_index(result)
    fm = float(result.band_frequencies[idx])
    fsd = result.fs / float(result.factors[idx])
    sos = np.asarray(result.sos[idx], dtype=np.float64)

    # Recompute the relative attenuation exactly as verify_filter_class does:
    # -20 log10|H| minus the attenuation at the exact mid-band frequency.
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

    # Symmetric log window centred on the mid-band (f / f_m = 1), out to the
    # band's processing Nyquist and no further than the G**2 breakpoint of
    # Table 1 (Formula (9) carries it to 1/b): a band filtered at the full
    # rate would otherwise open four decades, the pass-band corridor the
    # figure is for would be a sliver, and its ratio labels would collide.
    omega_max = min(
        float(omega[-1]), _map_breakpoint(_WINDOW_EXPONENT, result.fraction)
    )
    lo_x, hi_x = 1.0 / omega_max, omega_max
    win = (omega >= lo_x) & (omega <= hi_x)
    if not np.any(win):  # pragma: no cover - the bank designer rejects the band
        # Degenerate band (mid-band at or above the decimated Nyquist), so the
        # symmetric window is empty. Unreachable through the public verifier,
        # which never designs such a band; kept so a future designer that does
        # fails clearly instead of on a cryptic reduction.
        msg = (
            "Cannot plot the filter class corridor: the mid-band frequency is at "
            "or above the analysis Nyquist, so the f/f_m window is empty."
        )
        raise ValueError(msg)
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
        omega[win],
        lower[win],
        upper_fill[win],
        color=theme_fill(_C_TERTIARY, ax),
        lw=0.0,
        label=_t("Class {cls} pass corridor", language, cls=cls),
    )
    ax.plot(omega[win], lower[win], color=_C_TERTIARY, lw=1.0, ls="--")
    fin = win & finite_upper
    ax.plot(omega[fin], upper[fin], color=_C_TERTIARY, lw=1.0, ls="--")

    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("label", _t(r"Measured $\Delta A$", language))
    ax.plot(omega[win], delta_a[win], **kwargs)

    violated = (delta_a < lower - 1e-9) | (finite_upper & (delta_a > upper + 1e-9))
    viol_win = violated & win
    if np.any(viol_win):
        ax.plot(
            omega[viol_win],
            delta_a[viol_win],
            ls="",
            marker="o",
            ms=3.5,
            color=_C_REFERENCE,
            label=_t("Out of tolerance", language),
        )

    ax.axvline(1.0, color=_C_MUTED, ls=":", lw=1.0)
    _normalized_frequency_axis(ax, lo_x, hi_x, language)
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(y_bot, y_top)
    ax.set_xlabel(_t(_NORMALISED_FREQ_LABEL, language))
    ax.set_ylabel(_t("Relative attenuation [dB]", language))
    ax.set_title(
        _t(
            r"IEC 61260-1 class {cls} mask: $f_{{\mathrm{{m}}}}$ = {fm} Hz",
            language,
            cls=cls,
            fm=format_number(fm, language, decimals=0),
        )
    )
    ax.legend(loc="upper center", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


#: Room above and below the data of a requirement figure, as a share of the
#: span its limits and data cover.
_DATA_PAD_SHARE = 0.08


def _cover(
    low: float, high: float, data: np.ndarray | list[float]
) -> tuple[float, float]:
    """A y-range that keeps *low* to *high* and every finite value of *data*.

    A requirement figure is framed on its acceptance limits; a failing band
    lies past them, and it is the one a reader plots the verdict to see.
    """
    values = np.asarray(data, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return low, high
    lo, hi = float(np.min(values)), float(np.max(values))
    pad = _DATA_PAD_SHARE * (max(high, hi) - min(low, lo))
    return min(low, lo - pad), max(high, hi + pad)


def _class_title(met: str, unmet: str, cls: int | None, language: str) -> str:
    """A requirement's title: *met* with its class, or *unmet* when none."""
    if cls is None:
        return _t(unmet, language)
    return _t(met, language, cls=cls)


def _limit_lines(
    ax: Axes,
    limits: dict[int, tuple[float, float]],
    language: str,
) -> None:
    """Dashed horizontal acceptance limits, one colour per class."""
    colours = {1: _C_TERTIARY, 2: _C_SECONDARY}
    styles = {1: "--", 2: ":"}
    for cls, (lower, upper) in limits.items():
        ax.axhline(
            upper,
            color=colours.get(cls, _C_MUTED),
            ls=styles.get(cls, "-."),
            lw=1.4,
            label=_t("Class {cls} limits", language, cls=cls),
        )
        ax.axhline(
            lower,
            color=colours.get(cls, _C_MUTED),
            ls=styles.get(cls, "-."),
            lw=1.4,
        )


def plot_filter_bandwidth(
    result: FilterComplianceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The effective bandwidth deviation of every band against 5.12.2.

    One marker per band at its mid-band frequency, :math:`\Delta B` from
    IEC 61260-2:2016 Formulas (1), (2) and IEC 61260-1:2014 Formula (16),
    between the class 1 and class 2 acceptance limits.

    :param result: A
        :class:`~phonometry.filters.compliance.FilterComplianceResult` of the
        2014 edition.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the marker ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..filters.compliance import _BANDWIDTH_LIMITS_DB

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.band_frequencies, dtype=np.float64)
    deviation = np.array([float(b["bandwidth_deviation_db"]) for b in result.bands])
    limits = {
        c: (-_BANDWIDTH_LIMITS_DB[c], _BANDWIDTH_LIMITS_DB[c])
        for c in result.available_classes()
    }
    _limit_lines(ax, limits, language)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "linestyle", "-")
    style_default(kwargs, "lw", 1.0)
    kwargs.setdefault("label", _t(r"$\Delta B$ per band", language))
    ax.plot(freqs, deviation, **kwargs)
    ax.set_xscale("log")
    ax.set_xlim(freqs[0] / 1.1, freqs[-1] * 1.1)
    top = max(limits[c][1] for c in limits)
    ax.set_ylim(*_cover(-1.6 * top, 1.6 * top, deviation))
    format_frequency_axis(ax, language=language)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xlabel(_t(_MID_BAND_LABEL, language))
    ax.set_ylabel(_t(r"Effective bandwidth deviation $\Delta B$ [dB]", language))
    ax.set_title(
        _class_title(
            "IEC 61260-1 §5.12 effective bandwidth: class {cls}",
            "IEC 61260-1 §5.12 effective bandwidth: no class",
            result.requirement_class("effective_bandwidth"),
            language,
        )
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small", ncols=3)
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_filter_summation(
    result: FilterComplianceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The summation of adjacent outputs across every inner band, against 5.16.

    Each band that has a neighbour on both sides draws its Formula (3) curve
    of IEC 61260-2:2016 over its own test frequencies, from its lower to its
    upper band edge; the band that comes closest to a limit is drawn heavier.
    The acceptance limits of IEC 61260-1:2014 5.16 are the dashed lines.

    :param result: A
        :class:`~phonometry.filters.compliance.FilterComplianceResult` of the
        2014 edition with at least three bands.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the binding band's curve.
    :return: The axes.
    """
    import matplotlib.ticker as mticker

    from .._i18n import decimal_comma, format_number, localize_axes
    from ..filters.compliance import _SUMMATION_LIMITS_DB, _bank_summation

    ax = ax if ax is not None else _new_axes()
    mids = np.asarray(result.band_frequencies, dtype=np.float64)
    rates = np.asarray([result.fs / float(f) for f in result.factors])
    inner = [
        k for k, band in enumerate(result.bands) if band["summation_min_db"] is not None
    ]
    cls = result.requirement_class("summation")
    reference = cls if cls is not None else max(result.available_classes())
    key = f"summation_margin_class{reference}_db"
    binding = min(inner, key=lambda k: float(result.bands[k][key]))
    limits = {c: _SUMMATION_LIMITS_DB[c] for c in result.available_classes()}
    _limit_lines(ax, limits, language)
    shade = theme_line(_C_PRIMARY, ax, quiet=0.45)
    first = True
    drawn: list[np.ndarray] = []
    for k in inner:
        omega, curve = _bank_summation(
            result.sos, mids, rates, result.fraction, result.points_per_bandwidth, k
        )
        drawn.append(curve)
        if k == binding:
            continue
        ax.plot(
            omega,
            curve,
            color=shade,
            lw=0.9,
            label=_t(r"$\Delta P_j$ of each band", language) if first else "_nolegend_",
        )
        first = False
    omega, curve = _bank_summation(
        result.sos, mids, rates, result.fraction, result.points_per_bandwidth, binding
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 2.0)
    kwargs.setdefault(
        "label",
        _t(
            r"Binding band, $f_{{\mathrm{{m}}}}$ = {fm} Hz",
            language,
            fm=format_number(float(mids[binding]), language, decimals=0),
        ),
    )
    ax.plot(omega, curve, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    lo_x, hi_x = float(omega[0]), float(omega[-1])
    ax.set_xscale("log")
    ax.set_xlim(lo_x, hi_x)
    # The band edges and the mid-band: the three frequencies the test is
    # about, whatever the bandwidth.
    edges = (lo_x, 1.0, hi_x)
    ax.xaxis.set_major_locator(mticker.FixedLocator(edges))
    ax.xaxis.set_major_formatter(
        mticker.FixedFormatter([decimal_comma(f"{e:.3g}", language) for e in edges])
    )
    ax.xaxis.set_minor_locator(mticker.NullLocator())
    bottom = min(limits[c][0] for c in limits)
    top = max(limits[c][1] for c in limits)
    ax.set_ylim(*_cover(bottom - 0.6, top + 1.4, np.concatenate(drawn)))
    ax.set_xlabel(_t(_NORMALISED_FREQ_LABEL, language))
    ax.set_ylabel(_t(r"Summed output $\Delta P_j$ [dB]", language))
    ax.set_title(
        _class_title(
            "IEC 61260-1 §5.16 summation of outputs: class {cls}",
            "IEC 61260-1 §5.16 summation of outputs: no class",
            cls,
            language,
        )
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small", ncols=2)
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_time_invariance(
    result: TimeInvarianceResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each band's swept output against Formula (17), one line per sweep rate.

    :param result: A
        :class:`~phonometry.filters.compliance.TimeInvarianceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every rate's ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes
    from ..filters.time_invariance import _TIME_INVARIANCE_LIMITS_DB

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.band_frequencies, dtype=np.float64)
    limits = {
        c: (-_TIME_INVARIANCE_LIMITS_DB[c], _TIME_INVARIANCE_LIMITS_DB[c])
        for c in (1, 2)
    }
    _limit_lines(ax, limits, language)
    colours = (_C_PRIMARY, _C_QUATERNARY, _C_EDGE)
    markers = ("o", "s", "^")
    deviations = result.deviations_db
    for k, rate in enumerate(result.seconds_per_decade):
        style = dict(kwargs)
        style_default(style, "color", colours[k % len(colours)])
        style_default(style, "marker", markers[k % len(markers)])
        style_default(style, "lw", 1.0)
        if k > 0:
            # Hollow, so a rate that reads the same as the first still shows.
            style_default(style, "markerfacecolor", "none")
            style_default(style, "markersize", 9)
        style.setdefault(
            "label",
            _t(
                "{rate} s per decade",
                language,
                rate=decimal_comma(f"{rate:g}", language),
            ),
        )
        ax.plot(freqs, deviations[k], **style)
    ax.set_xscale("log")
    ax.set_xlim(freqs[0] / 1.1, freqs[-1] * 1.1)
    ax.set_ylim(*_cover(-1.0, 1.0, deviations))
    format_frequency_axis(ax, language=language)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xlabel(_t(_MID_BAND_LABEL, language))
    ax.set_ylabel(_t(r"Deviation from $L_{\mathrm{c}}$ [dB]", language))
    ax.set_title(
        _class_title(
            "IEC 61260-1 §5.14 time-invariant operation: class {cls}",
            "IEC 61260-1 §5.14 time-invariant operation: no class",
            result.overall_class,
            language,
        )
    )
    ax.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small", ncols=2)
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def _margin_db(verification: ConformanceVerification) -> float:
    """The distance from a deviation to its nearer acceptance limit, dB.

    Positive inside the limits, negative outside; an open end of the
    interval (a stop-band ``+inf``) is no limit to be near.
    """
    margins = []
    if math.isfinite(verification.lower_limit):
        margins.append(verification.deviation - verification.lower_limit)
    if math.isfinite(verification.upper_limit):
        margins.append(verification.upper_limit - verification.deviation)
    return min(margins)


def _draw_margins(
    ax: Axes,
    positions: np.ndarray,
    verifications: tuple[ConformanceVerification, ...],
    language: str,
    kwargs: dict[str, Any],
    shown: set[str],
) -> None:
    """One marker per result at its margin, with its uncertainty as error bar.

    A diamond conforms, a cross does not, and a hollow marker is a result
    5.3 of IEC 61260-3 forbids using (its uncertainty exceeds the maximum).
    """
    for x, v in zip(positions, verifications, strict=True):
        margin = _margin_db(v)
        style = dict(kwargs)
        if not v.uncertainty_within_maximum:
            key = _UNUSABLE_LABEL
            style_default(style, "color", _C_SECONDARY)
            style.setdefault("marker", "o")
            style_default(style, "markerfacecolor", "none")
        elif v.passes:
            key = "Conforms"
            style_default(style, "color", _C_TERTIARY)
            style.setdefault("marker", "D")
        else:
            key = "Does not conform"
            style_default(style, "color", _C_REFERENCE)
            style.setdefault("marker", "X")
        style_default(style, "markersize", 7)
        style_default(style, "linestyle", "none")
        if "label" in kwargs:
            # A caller's label names the whole series once, not each verdict.
            style["label"] = "_nolegend_" if "label" in shown else kwargs["label"]
            shown.add("label")
        else:
            style["label"] = "_nolegend_" if key in shown else _t(key, language)
            shown.add(key)
        ax.errorbar(
            [x],
            [margin],
            yerr=[v.uncertainty],
            ecolor=_C_MUTED,
            elinewidth=1.0,
            capsize=3,
            zorder=3,
            **style,
        )


#: The margins a periodic-test figure may mark, dB; those inside the axis
#: range are the ticks.
_MARGIN_TICKS_DB = (
    -20.0,
    -10.0,
    -5.0,
    -2.0,
    -1.0,
    -0.5,
    0.0,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    20.0,
    50.0,
)


def _margin_axis(
    ax: Axes, verifications: list[ConformanceVerification], language: str
) -> None:
    """The zero line and a symmetric-log margin axis with plain labels.

    Margins run from a few hundredths of a decibel in the pass band to tens
    of decibels deep in the stop band; the axis is linear within one decibel
    of the limit and logarithmic beyond it, labelled in decibels rather than
    in powers of ten.
    """
    import matplotlib.ticker as mticker

    from .._i18n import decimal_comma, fmt_minus

    ax.axhline(
        0.0, color=_C_REFERENCE, lw=1.4, ls="--", label=_t("Acceptance limit", language)
    )
    ax.set_yscale("symlog", linthresh=1.0)
    reach = [
        (_margin_db(v) - v.uncertainty, _margin_db(v) + v.uncertainty)
        for v in verifications
    ]
    bottom = min(-0.5, min(lo for lo, _ in reach) * 1.3)
    top = max(1.0, max(hi for _, hi in reach) * 1.6)
    ax.set_ylim(bottom, top)
    ticks = [t for t in _MARGIN_TICKS_DB if bottom <= t <= top]
    ax.yaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.yaxis.set_major_formatter(
        mticker.FixedFormatter(
            [decimal_comma(fmt_minus(t, "g"), language) for t in ticks]
        )
    )
    ax.yaxis.set_minor_locator(mticker.NullLocator())
    ax.set_ylabel(_t("Margin to the nearer acceptance limit [dB]", language))
    ax.grid(visible=True, which="major", alpha=0.3)


def plot_periodic_clause(
    result: PeriodicTestClause,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One clause of IEC 61260-3:2016 against its acceptance limits.

    Clauses 10 and 11 as IEC 61260-1:2014 Figure C.1; clause 13 as each
    result's margin to its nearer limit against its test frequency. A result
    whose uncertainty exceeds its maximum is drawn hollow, as 5.3 forbids
    using it, and the title says the clause does not conform only when a
    usable result fails.

    :param result: A
        :class:`~phonometry.filters.periodic_tests.PeriodicTestClause`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the verdict markers.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from .metrology import _draw_conformance

    ax = ax if ax is not None else _new_axes()
    if result.failed:
        verdict = _t("does not conform", language)
    elif result.unusable:
        verdict = _t("not usable (§5.3)", language)
    else:
        verdict = _t("conforms", language)
    if result.normalized_frequencies is None:
        _draw_conformance(
            ax,
            result.verifications,
            language,
            kwargs,
            unusable_label=_t(_UNUSABLE_LABEL, language),
        )
        ax.set_xlabel(_t("Measurement", language))
    else:
        omega = np.asarray(result.normalized_frequencies, dtype=np.float64)
        _draw_margins(ax, omega, result.verifications, language, kwargs, set())
        _margin_axis(ax, list(result.verifications), language)
        lo, hi = float(np.min(omega)) / 1.15, float(np.max(omega)) * 1.15
        _normalized_frequency_axis(ax, lo, hi, language)
        ax.set_xlim(lo, hi)
        ax.set_xlabel(_t(_NORMALISED_FREQ_LABEL, language))
        place_legend_clear(ax.legend(fontsize="small"))
    ax.set_title(
        _t(
            _PERIODIC_TITLE,
            language,
            clause=f"§{result.clause}",
            verdict=verdict,
        )
    )
    localize_axes(ax, language)
    return ax


def plot_periodic_verification(
    result: FilterPeriodicVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Every result of the periodic tests at its margin, grouped by clause.

    :param result: A
        :class:`~phonometry.filters.periodic_tests.FilterPeriodicVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the verdict markers.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    shown: set[str] = set()
    start = 1.0
    centres: list[float] = []
    names: list[str] = []
    for k, clause in enumerate(result.clauses):
        count = len(clause.verifications)
        positions = start + np.arange(count, dtype=np.float64)
        _draw_margins(ax, positions, clause.verifications, language, kwargs, shown)
        centres.append(float(positions.mean()))
        names.append(f"§{clause.clause}")
        if k > 0:
            ax.axvline(start - 1.0, color=_C_MUTED, lw=0.8, ls=":")
        start += count + 1.0
    _margin_axis(ax, [v for c in result.clauses for v in c.verifications], language)
    ax.set_xlim(0.0, start - 1.0)
    ax.set_xticks(centres)
    ax.set_xticklabels(names)
    ax.set_xlabel(_t("Clause", language))
    verdict = _t("passed" if result.passes else "not passed", language)
    ax.set_title(
        _t(
            "IEC 61260-3 periodic tests, class {cls}: {verdict}",
            language,
            cls=result.filter_class,
            verdict=verdict,
        )
    )
    place_legend_clear(ax.legend(fontsize="small", ncols=2))
    return ax


def _normalized_frequency_axis(
    ax: Axes, lo: float, hi: float, language: str = "en"
) -> None:
    """Label a logarithmic ``f / f_m`` axis with plain decimal ratios.

    The labels are fixed strings on a logarithmic axis, so
    :func:`~phonometry._i18n.localize_axes` cannot reach them (it only
    reformats the default numeric formatter of a linear axis). Half of these
    ratios carry a decimal, so the separator is localised here or nowhere.
    """
    import matplotlib.ticker as mticker

    from .._i18n import decimal_comma

    ax.set_xscale("log")
    ticks = [t for t in (0.25, 0.5, 0.7, 1.0, 1.4, 2.0, 4.0) if lo <= t <= hi]
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
    ax.xaxis.set_major_formatter(
        mticker.FixedFormatter([decimal_comma(f"{t:g}", language) for t in ticks])
    )
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())


def plot_parametric_eq(
    result: EQResponseResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    show_sections: bool = True,
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Magnitude and phase response of a parametric-EQ cascade.

    With ``ax`` given, only the magnitude panel is drawn on it.

    :param result: An
        :class:`~phonometry.filters.equalizer.EQResponseResult`.
    :param ax: Existing axes for the magnitude panel, or ``None`` for a
        fresh two-panel (magnitude + phase) figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param show_sections: Also draw each section's magnitude (light lines)
        when the cascade has more than one section.
    :param kwargs: Forwarded to the cascade magnitude line.
    :return: The magnitude axes (``ax`` given) or the array of two axes.
    """
    from .._i18n import decimal_comma, localize_axes

    freqs = np.asarray(result.frequencies, dtype=np.float64)
    fmin, fmax = float(freqs[0]), float(freqs[-1])
    color = style_pop(kwargs, "color", _C_PRIMARY)

    def _magnitude(axm: Axes) -> None:
        if show_sections and result.section_magnitude_db.shape[0] > 1:
            for idx, section in enumerate(result.sections):
                # The key doubles as the lookup value (``_t`` is called with
                # the raw ``EQFilterType`` token), so the underscore of
                # ``bandpass_skirt`` can only be dropped at the label, never by
                # renaming the key: outside maths it draws as a literal
                # underscore in a legend whose every other entry reads as
                # prose. A no-op for the other eight types and for every
                # Spanish value, none of which carries one.
                label = decimal_comma(
                    f"{_t(section.filter_type, language).replace('_', ' ')} "
                    f"{section.f0:g} Hz",
                    language,
                )
                axm.semilogx(
                    freqs,
                    result.section_magnitude_db[idx],
                    color=_C_MUTED,
                    lw=0.9,
                    alpha=0.7,
                    label=label if idx < _MAX_LABELED_SECTIONS else None,
                )
        style_default(kwargs, "lw", 1.8)
        kwargs.setdefault("label", _t("Cascade", language))
        axm.semilogx(freqs, result.magnitude_db, color=color, **kwargs)
        # Quiet by colour, not by opacity: half opacity on a 0.8 pt line
        # composites to within a level or two of the dark page and the
        # reference disappears, while reading fine on the white one.
        axm.axhline(
            0.0, color=theme_line(_C_REFERENCE, axm, quiet=0.6), linestyle=":", lw=0.8
        )
        axm.set_ylabel(_t("Magnitude [dB]", language))
        axm.grid(visible=True, which="both", alpha=0.3)
        axm.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if ax is not None:
        _magnitude(ax)
        ax.set_xlabel(_t(_FREQ_LABEL, language))
        format_frequency_axis(ax, fmin, fmax, language=language)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.4))
    _magnitude(axes[0])
    axes[0].set_title(_t("Parametric EQ response (Audio EQ Cookbook)", language))
    axes[1].semilogx(freqs, np.degrees(result.phase_rad), color=color, lw=1.4)
    axes[1].set_ylabel(_t("Phase [deg]", language))
    axes[1].set_xlabel(_t(_FREQ_LABEL, language))
    axes[1].grid(visible=True, which="both", alpha=0.3)
    for axf in axes:
        format_frequency_axis(axf, fmin, fmax, language=language)
        localize_axes(axf, language)
    return axes


def plot_time_weighted_envelope(
    result: TimeWeightedEnvelope,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The level trace of a :class:`~phonometry.filters.TimeWeightedEnvelope`.

    Draws ``10 lg(mean square / p0^2)`` against time, which is the trace a
    sound level meter shows: A-weight the record first and this is
    ``L_pAF``. An uncalibrated record has no reference to count decibels
    from, so its mean square is drawn as it is and the axis says so rather
    than implying a sound pressure level.

    :param result: A :class:`~phonometry.filters.TimeWeightedEnvelope`.
    :param ax: Existing axes to draw on, or ``None`` for a fresh figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every channel's ``plot`` call.
    :return: The axes drawn on.
    """
    from .._i18n import localize_axes

    # Deferred, not tidiness: signals.levels imports io, which imports this
    # tree, so reaching for the reference pressure at module level is an
    # import cycle that the package whitelist test cannot see.
    from ..signals.levels import _REF_PRESSURE

    envelope = np.atleast_2d(np.asarray(result.mean_square, dtype=np.float64))
    if result.calibrated:
        with np.errstate(divide="ignore"):
            y = 10.0 * np.log10(envelope / _REF_PRESSURE**2)
    else:
        y = envelope

    new_figure = ax is None
    axw = _new_axes() if ax is None else ax
    style_default(kwargs, "lw", 0.9)
    if envelope.shape[0] == 1:
        style_default(kwargs, "color", _C_PRIMARY)
        axw.plot(result.times, y[0], **kwargs)
    else:
        for index, channel in enumerate(y):
            # setdefault, not label=: `label` is an ordinary matplotlib
            # keyword, so a caller who passes one through **kwargs would
            # otherwise hit "got multiple values for keyword argument
            # 'label'". Theirs wins.
            per_channel = dict(kwargs)
            per_channel.setdefault("label", _t(_CHANNEL_LABEL, language, n=index + 1))
            axw.plot(result.times, channel, **per_channel)
        axw.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")
    axw.set_xlabel(_t("Time [s]", language))
    axw.set_ylabel(
        _t(
            "Sound pressure level [dB re 20 uPa]"
            if result.calibrated
            else "Mean square [FS\u00b2]",
            language,
        )
    )
    axw.grid(visible=True, alpha=0.3)
    if new_figure:
        axw.set_title(
            _t(
                "{mode} time-weighted level",
                language,
                mode=_t(result.mode, language).capitalize(),
            )
        )
    localize_axes(axw, language)
    return axw


def plot_octave_levels(
    result: OctaveFilterResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The band levels of an :class:`~phonometry.filters.OctaveFilterResult`.

    One point per band, on the log frequency axis the rest of the corpus uses,
    so a third-octave spectrum reads the way a meter displays it. A
    multichannel result draws one line per channel.

    A result whose call asked for no level has nothing to draw, and says so
    rather than opening an empty figure.

    :param result: An :class:`~phonometry.filters.OctaveFilterResult`.
    :param ax: Existing axes to draw on, or ``None`` for a fresh figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every channel's ``plot`` call.
    :return: The axes drawn on.
    :raises ValueError: when the result carries no level.
    """
    from .._i18n import localize_axes

    if result.levels is None:
        msg = (
            "this result carries no level to plot: it was made by a call with "
            "calculate_level=False"
        )
        raise ValueError(msg)

    levels = np.atleast_2d(np.asarray(result.levels, dtype=np.float64))
    # The nominal labels are strings; the band index is what they sit on, and
    # the axis then reads them out. Exact centres plot on the frequency axis.
    nominal = bool(result.frequencies) and isinstance(result.frequencies[0], str)
    x = (
        np.arange(len(result.frequencies), dtype=np.float64)
        if nominal
        else np.asarray(result.frequencies, dtype=np.float64)
    )

    new_figure = ax is None
    axw = _new_axes() if ax is None else ax
    style_default(kwargs, "lw", 1.2)
    style_default(kwargs, "marker", "o")
    style_default(kwargs, "ms", 3.0)
    if levels.shape[0] == 1:
        style_default(kwargs, "color", _C_PRIMARY)
        axw.plot(x, levels[0], **kwargs)
    else:
        for index, channel in enumerate(levels):
            per_channel = dict(kwargs)
            per_channel.setdefault("label", _t(_CHANNEL_LABEL, language, n=index + 1))
            axw.plot(x, channel, **per_channel)
        axw.legend(loc=_LEGEND_UPPER_RIGHT, fontsize="small")

    if nominal:
        # set_xticklabels installs fixed strings, and localize_axes below does
        # not reach inside them, so a Spanish nominal plot would keep the
        # English decimal point that every other figure in the corpus avoids.
        from .._i18n import decimal_comma

        axw.set_xticks(x)
        axw.set_xticklabels(
            [decimal_comma(str(f), language) for f in result.frequencies]
        )
        axw.set_xlabel(_t("Band centre frequency [Hz]", language))
    else:
        format_frequency_axis(axw, language=language)
        axw.set_xlabel(_t(_FREQ_LABEL, language))
    axw.set_ylabel(_t("Band level [dB]", language))
    if new_figure:
        axw.set_title(_t("Band levels", language))
    localize_axes(axw, language)
    return axw
