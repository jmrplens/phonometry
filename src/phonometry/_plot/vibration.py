#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the vibration domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .._internal.validation import require_equal_shapes
from .common import (
    _C_EDGE,
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_TERTIARY,
    _band_axis,
    _new_axes,
    _new_axes_column,
    format_frequency_axis,
    style_default,
)

#: The three phasors of the ISO 20816-1 Figure D.1 diagram, named once so
#: the label a curve carries and the key its translation is filed under
#: cannot drift apart.
_LABEL_INITIAL = "initial $A_1$"
_LABEL_FINAL = "final $A_2$"
_LABEL_CHANGE = "change $A_2 - A_1$"

#: The ISO 4866 D.3 height fit, named once for the same reason: it is both the
#: legend entry of the fitted line and the key its Spanish form is filed under.
_LABEL_HEIGHT_FIT = r"$f = 46/h$"

#: Bar colours for the per-operation partial exposures, cycled in order. Blue,
#: green, purple, light blue and grey deliberately avoid the orange EAV and red
#: ELV threshold-line colours, so a bar is never mistaken for a limit line.
_OP_COLORS = (_C_PRIMARY, _C_TERTIARY, _C_QUATERNARY, _C_PRIMARY_LIGHT, _C_MUTED)
#: The combined A(8) bar keeps a distinct neutral-dark colour: it is the
#: root-sum-of-squares of the operations, not one of them.
_A8_COLOR = _C_EDGE

if TYPE_CHECKING:
    from typing import Protocol

    from matplotlib.axes import Axes
    from matplotlib.projections.polar import PolarAxes
    from numpy.typing import ArrayLike, NDArray

    from ..vibration.human.exposure import (
        DailyVibrationExposure,
        WeightedSpectrum,
        WeightingResponse,
    )
    from ..vibration.human.instrumentation import (
        PhaseVerification,
        WeightingVerification,
    )
    from ..vibration.human.multiple_shock import MultipleShockResult
    from ..vibration.human.seat_vibration import SeatTransmissionResult
    from ..vibration.human.signal_burst import SignalBurstVerification
    from ..vibration.immission.railway import TrainPassage
    from ..vibration.immission.vibration_meter import (
        AssessmentVelocity,
        VibrationMeterReading,
        VibrationMeterVerification,
    )
    from ..vibration.machinery.diagnostics import FaultFrequencyResult
    from ..vibration.machinery.evaluation import VectorChangeResult
    from ..vibration.structural.building_damage import DamageAssessment
    from ..vibration.structural.building_response import (
        BuildingFrequencyEstimate,
    )
    from ..vibration.structural.experimental_sea import PowerInjectionResult
    from ..vibration.structural.junction_transmission import (
        JunctionTransmissionResult,
    )
    from ..vibration.structural.mechanical_mobility import (
        MobilityResult,
        RigidMassCalibrationResult,
    )
    from ..vibration.structural.radiation_efficiency import RadiationEfficiencyResult
    from ..vibration.structural.transfer_stiffness import TransferStiffnessResult

    class _SpectrumLike(Protocol):
        """A measured spectrum: anything exposing the two plotted vectors.

        :class:`~phonometry.signals.envelope.EnvelopeSpectrumResult` is the
        expected case, but the fault-line overlay only reads these two
        array-likes, so the contract is stated structurally.
        """

        @property
        def frequencies(self) -> ArrayLike: ...

        @property
        def amplitude(self) -> ArrayLike: ...


#: Shared frequency-axis label of the vibration renderers.
_FREQ_LABEL = "Frequency [Hz]"
#: Mobility ordinate label of the ISO 7626 panels.
_MOBILITY_LABEL = "Mobility $|Y|$ [m/(N·s)]"
#: Deviation ordinate shared by the mobility, seat and signal-burst panels.
_DEVIATION_LABEL = "Deviation [%]"
#: The three legend entries every ISO 8041-1 verifier panel carries: the band
#: Table 5 allows, and the two verdicts a measured point can take in it.
_ISO8041_BAND_LABEL = "ISO 8041-1 tolerance"
_WITHIN_LABEL = "within tolerance"
_OUTSIDE_LABEL = "outside tolerance"
#: The DIN 45669-1 reading figure: its time axis, its ordinate and the two
#: numbers a meter displays, named once so the label a line carries and the
#: key its translation is filed under cannot drift apart.
_TIME_LABEL = "Time [s]"
_KBF_LABEL = "Weighted vibration severity $KB_F$"
_KBF_MAX_LABEL = r"$KB_{{F\mathrm{{max}}}}$ = {value}"
_KBFTM_LABEL = r"$KB_{{FTm}}$ = {value}"
#: The DIN 45672-2 passage figures: the running r.m.s. of Formula (1), its
#: maximum, and the two third-octave spectra of Figure 6.
_RUNNING_RMS_LABEL = r"running r.m.s. $\tilde v_F(t)$"
_RUNNING_MAX_LABEL = r"$\tilde v_{{F\mathrm{{max}}}}$ = {value} mm/s"
_BAND_LEVEL_LABEL = "Velocity level [dB re 5·10⁻⁸ m/s]"
_INTERVAL_LEVEL_LABEL = r"interval level $L_{vF2}$"
_MAX_LEVEL_LABEL = r"maximum level $L_{vF\mathrm{max}}$"
#: Where the brackets of T_1, T_2 and T_3 sit, as fractions of the axes height.
_BRACKET_ROWS = (0.93, 0.855, 0.78)
#: Legend entry of the assessed ISO 2631-5 point (stress variable and
#: injury probability), formatted with ``r`` and ``p``.
_RISK_LABEL = r"$R$ = {r},  $\Pi$ = {p} %"

#: Spanish translations of the fixed strings rendered by the vibration
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
_STRINGS: dict[str, str] = {
    _FREQ_LABEL: "Frecuencia [Hz]",
    "Weighting factor [dB]": "Factor de ponderación [dB]",
    "Unweighted $a_i$": "Sin ponderar $a_i$",
    "r.m.s. acceleration [m/s²]": "Aceleración eficaz [m/s²]",
    "Vibration exposure $A(8)$ [m/s²]": "Exposición a vibración $A(8)$ [m/s²]",
    "driving-point mobility": "movilidad en punto de excitación",
    "transfer mobility": "movilidad de transferencia",
    _MOBILITY_LABEL: "Movilidad $|Y|$ [m/(N·s)]",
    "Transfer stiffness level $L_k$ [dB re 1 N/m]": "Nivel de rigidez de transferencia $L_k$ [dB re 1 N/m]",
    r"Radiation efficiency $\sigma$": r"Eficiencia de radiación $\sigma$",
    "Stress variable $R$": "Variable de tensión $R$",
    "Probability of lumbar injury [%]": "Probabilidad de lesión lumbar [%]",
    "ISO 7626-1 mechanical mobility": "ISO 7626-1 movilidad mecánica",
    "ISO 7626-2 rigid-mass calibration check": "ISO 7626-2 verificación de calibración con masa rígida",
    "Accelerance $|A|$ [1/kg]": "Acelerancia $|A|$ [1/kg]",
    "Deviation [%]": "Desviación [%]",
    r"expected $|A| = 1/m$": r"esperado $|A| = 1/m$",
    r"expected $|Y| = 1/(2\pi f m)$": r"esperado $|Y| = 1/(2\pi f m)$",
    "measured (within tolerance)": "medido (dentro de tolerancia)",
    "measured (out of tolerance)": "medido (fuera de tolerancia)",
    r"$\pm${p} % tolerance": r"tolerancia $\pm${p} %",
    "ISO 10846 dynamic transfer stiffness": "ISO 10846 rigidez dinámica de transferencia",
    "Plate radiation efficiency (Leppington / Maidanik)": "Eficiencia de radiación de placa (Leppington / Maidanik)",
    "Frequency weighting {name} (ISO 8041-1)": "Ponderación en frecuencia {name} (ISO 8041-1)",
    "Band-limiting weighting of {name} (ISO 8041-1)": "Ponderación limitadora de banda de {name} (ISO 8041-1)",
    "Weighted $W_i a_i$ ({name})": "Ponderada $W_i a_i$ ({name})",
    "{designation} weighted acceleration spectrum  ($a_\\mathrm{{w}}$ = {aw} m/s²)": "{designation} espectro de aceleración ponderada  ($a_\\mathrm{{w}}$ = {aw} m/s²)",
    "Directive 2002/44/EC daily {kind} exposure  ($A(8)$ = {a8} m/s², {zone})": "Directiva 2002/44/CE exposición diaria {kind}  ($A(8)$ = {a8} m/s², {zone})",
    "below action": "por debajo de la acción",
    "action": "acción",
    "limit": "límite",
    "peak at {v} Hz": "máximo en {v} Hz",
    "ISO 2631-5 injury probability — {sex}": "ISO 2631-5 probabilidad de lesión — {sex}",
    "male": "hombre",
    "female": "mujer",
    _RISK_LABEL: r"$R$ = {r},  $\Pi$ = {p} %",
    "envelope spectrum": "espectro de envolvente",
    "Envelope amplitude": "Amplitud de la envolvente",
    "Predicted fault line": "Línea de fallo prevista",
    "Predicted fault lines: {src}, shaft {fs} Hz": "Líneas de fallo previstas: {src}, eje {fs} Hz",
    "rolling-contact bearing": "rodamiento de contacto rodante",
    "gear pair": "engranaje",
    "induction motor": "motor de inducción",
    "bladed rotor": "rotor con álabes",
    "shaft": "eje",
    "bearing": "rodamiento",
    "gear": "engranaje",
    "motor": "motor",
    "blade": "álabe",
    "Loss factor": "Factor de pérdidas",
    "Power-injection SEA loss factors ({method})": "Factores de pérdidas SEA por inyección de potencia ({method})",
    "single-drive": "excitación única",
    "two-drive": "doble excitación",
    # Plate-junction transmission (moved here with its renderer: _plot
    # holds one module per domain, and a junction is a vibration result).
    "Incidence angle [deg]": "Ángulo de incidencia [grados]",
    r"Transmission coefficient $\tau$": r"Coeficiente de transmisión $\tau$",
    "Bending-wave transmission, {junction}-junction "
    "($\\chi$ = {chi}, $\\psi$ = {psi})": "Transmisión de onda de flexión, unión {junction} "
    "($\\chi$ = {chi}, $\\psi$ = {psi})",
    r"corner $\tau_{12}(\theta)$": r"esquina $\tau_{12}(\theta)$",
    r"straight $\tau_{13}(\theta)$": r"recta $\tau_{13}(\theta)$",
    r"corner average $\bar\tau_{12}$ = {value}": r"media esquina $\bar\tau_{12}$ = {value}",
    r"straight average $\bar\tau_{13}$ = {value}": r"media recta $\bar\tau_{13}$ = {value}",
    _LABEL_INITIAL: "inicial $A_1$",
    _LABEL_FINAL: "final $A_2$",
    _LABEL_CHANGE: "cambio $A_2 - A_1$",
    "Change in vibration: magnitude {mag}, vector {vec}": "Cambio de vibración: magnitud {mag}, vector {vec}",
    # Seat transmission (ISO 10326-1): the runs of one test and the SEAT
    # factor between their means.
    "Test run": "Pasada",
    "platform $a_\\mathrm{wP}$": "plataforma $a_\\mathrm{wP}$",
    "seat $a_\\mathrm{wS}$": "asiento $a_\\mathrm{wS}$",
    "mean {value}": "media {value}",
    "Weighted r.m.s. acceleration [m/s²]": "Aceleración eficaz ponderada [m/s²]",
    "Seat transmission (ISO 10326-1): SEAT = {value}": "Transmisión del asiento (ISO 10326-1): SEAT = {value}",
    # Effects of vibration on structures (DIN 4150-3 Table 1, Bild 1).
    "Peak velocity $v_i$ [mm/s]": "Velocidad de pico $v_i$ [mm/s]",
    "commercial and industrial": "comercial e industrial",
    "dwellings": "viviendas",
    "especially sensitive": "especialmente sensible",
    # Instrument verification (ISO 8041-1 Tables 4 and 5).
    "design goal": "objetivo de diseño",
    "ISO 8041-1 tolerance": "tolerancia de ISO 8041-1",
    "accepted with U = {u} %": "aceptado con U = {u} %",
    "within tolerance": "dentro de tolerancia",
    "outside tolerance": "fuera de tolerancia",
    "Weighting factor": "Factor de ponderación",
    "{w} weighting against ISO 8041-1: {verdict}": "Ponderación {w} frente a ISO 8041-1: {verdict}",
    "Characteristic phase deviation [deg]": "Desviación característica de fase [grados]",
    "{w} characteristic phase deviation against ISO 8041-1: {verdict}": "Desviación característica de fase de {w} frente a ISO 8041-1: {verdict}",
    "PASS": "CUMPLE",  # nosec B105 - verdict label, not a password
    "FAIL": "NO CUMPLE",
    "measured {v} mm/s at {f} Hz": "medido {v} mm/s a {f} Hz",
    "measured {v} mm/s": "medido {v} mm/s",
    "Building class": "Clase de edificio",
    "Guideline values at the foundation (DIN 4150-3 Table 1)": "Valores de referencia en el cimiento (DIN 4150-3, tabla 1)",
    "Guideline values in the topmost floor plane (DIN 4150-3 Table 1)": "Valores de referencia en el plano de la última planta (DIN 4150-3, tabla 1)",
    "Long-term guideline values in the topmost floor plane (DIN 4150-3 Table 3)": "Valores de referencia de larga duración en el plano de la última planta (DIN 4150-3, tabla 3)",  # Empirical fundamental frequency of a building (ISO 4866 Figure D.1).
    "Building height $h$ [m]": "Altura del edificio $h$ [m]",
    _LABEL_HEIGHT_FIT: _LABEL_HEIGHT_FIT,
    r"$\pm$50 %, which D.3 calls not uncommon": r"$\pm$50 %, que D.3 llama nada raro",
    "{model} model: {f} Hz at {h} m": "modelo de {model}: {f} Hz a {h} m",
    "Empirical fundamental frequency of a building (ISO 4866 D.3)": "Frecuencia fundamental empírica de un edificio (ISO 4866, D.3)",
    "storeys": "plantas",
    "height": "altura",
    "height_width": "altura y anchura",
    "slenderness": "esbeltez",
    # Saw-tooth signal-burst response (ISO 8041-1 Tables 6 to 9).
    "Saw-tooth cycles per burst": "Ciclos de diente de sierra por ráfaga",
    "continuous": "continua",
    "r.m.s. value": "valor eficaz",
    "MTVV linear": "MTVV lineal",
    "MTVV exponential": "MTVV exponencial",
    r"printed tolerance $\pm${p} %": r"tolerancia impresa $\pm${p} %",
    r"printed tolerance $\pm${p} % (VDV)": r"tolerancia impresa $\pm${p} % (VDV)",
    "hand-arm": "mano-brazo",
    "whole-body": "cuerpo entero",
    "low-frequency whole-body": "cuerpo entero de baja frecuencia",
    "band limiting": "limitación de banda",
    "Signal-burst response (ISO 8041-1)\n{name}, {application}": "Respuesta a ráfaga de señal (ISO 8041-1)\n{name}, {application}",
    # Vibration immission meter (DIN 45669-1 Tables 2 and 3, 5.1.6, Annex E).
    _TIME_LABEL: "Tiempo [s]",
    "DIN 45669-1 tolerance": "tolerancia de DIN 45669-1",
    "Response deviation $F(f)$ [%]": "Desviación de la respuesta $F(f)$ [%]",
    "{weighting} response against DIN 45669-1: {verdict}": "Respuesta {weighting} frente a DIN 45669-1: {verdict}",
    "KB": "KB",
    "unweighted": "sin ponderar",
    _KBF_LABEL: "Intensidad de vibración ponderada $KB_F$",
    _KBF_MAX_LABEL: _KBF_MAX_LABEL,
    _KBFTM_LABEL: _KBFTM_LABEL,
    "clock maximum": "máximo por intervalo",
    "Vibration immission over {duration} s ({range} range)": "Inmisión de vibración en {duration} s (rango {range})",
    "building": "edificios",
    "railway": "ferrocarril",
    "Assessment velocity $v_B$ [mm/s]": "Velocidad de valoración $v_B$ [mm/s]",
    "guideline {value} mm/s": "valor de referencia {value} mm/s",
    "peak {value} mm/s": "pico {value} mm/s",
    "Short-term vibration by DIN 45669-1 Annex E ({cls}): {verdict}": "Vibración de corta duración según DIN 45669-1, anexo E ({cls}): {verdict}",
    # Railway vibration evaluation (DIN 45672-2 Figures 2, 4 and 6).
    "velocity $v(t)$": "velocidad $v(t)$",
    _RUNNING_RMS_LABEL: r"valor eficaz móvil $\tilde v_F(t)$",
    _RUNNING_MAX_LABEL: _RUNNING_MAX_LABEL,
    "Velocity [mm/s]": "Velocidad [mm/s]",
    "Train passage by DIN 45672-2: $v_E$ = {value} mm/s": "Paso de tren según DIN 45672-2: $v_E$ = {value} mm/s",
    _BAND_LEVEL_LABEL: "Nivel de velocidad [dB re 5·10⁻⁸ m/s]",
    _INTERVAL_LEVEL_LABEL: r"nivel de intervalo $L_{vF2}$",
    _MAX_LEVEL_LABEL: r"nivel máximo $L_{vF\mathrm{max}}$",
    "Third-octave spectra of one passage (DIN 45672-2)": "Espectros en tercios de octava de un paso (DIN 45672-2)",
}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def _plot_verdict_points(
    ax: Axes,
    freqs: NDArray[np.float64],
    values: NDArray[np.float64],
    inside: NDArray[np.bool_],
    kwargs: dict[str, Any],
    language: str,
) -> None:
    """The measured points of a verifier, green inside the band and red outside.

    The pair ``plot_db_hr_assessment`` already uses for a complies/fails
    verdict. The measured series cannot take _C_PRIMARY, which the design goal
    and its band carry in every verifier, and it must not take _C_REFERENCE,
    which would paint a conforming point in the colour of a refusal. The
    caller's kwargs reach the conforming points, so a colour or a label the
    caller names wins over these defaults.
    """
    style_default(kwargs, "color", _C_TERTIARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "markersize", 5)
    style_default(kwargs, "ls", "none")
    kwargs.setdefault("label", _t(_WITHIN_LABEL, language))
    ax.plot(freqs[inside], values[inside], **kwargs)
    if not inside.all():
        ax.plot(
            freqs[~inside],
            values[~inside],
            color=_C_REFERENCE,
            marker="X",
            markersize=9,
            ls="none",
            label=_t(_OUTSIDE_LABEL, language),
        )


def plot_vibration_weighting(
    result: WeightingResponse,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Frequency-weighting factor (dB) versus frequency (ISO 8041-1).

    :param result: A
        :class:`~phonometry.vibration.human.exposure.WeightingResponse` exposing
        ``name``, ``frequencies`` and ``magnitude_db``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the weighting curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    mag_db = np.asarray(result.magnitude_db, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.semilogx(freqs, mag_db, **kwargs)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Weighting factor [dB]", language))
    title = (
        "Band-limiting weighting of {name} (ISO 8041-1)"
        if result.band_limiting
        else "Frequency weighting {name} (ISO 8041-1)"
    )
    ax.set_title(_t(title, language).format(name=result.name))
    ax.grid(visible=True, which="both", alpha=0.3)
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()))
    localize_axes(ax, language)
    return ax


def plot_weighted_spectrum(
    result: WeightedSpectrum,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Unweighted vs weighted one-third-octave acceleration spectrum.

    Draws the measured band accelerations and, overlaid, the weighted band
    contributions ``W_i*a_i``; the overall ``a_w`` is annotated in the title.

    :param result: A
        :class:`~phonometry.vibration.human.exposure.WeightedSpectrum` exposing
        ``frequencies``, ``band_accelerations``, ``weighted``, ``overall`` and
        ``weighting_name``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the weighted (primary) bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    raw = np.asarray(result.band_accelerations, dtype=np.float64)
    weighted = np.asarray(result.weighted, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    width = 0.4
    # The weighted bars are the primary artist; forward user kwargs there.
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(
        positions - width / 2,
        raw,
        width,
        color=_C_MUTED,
        label=_t("Unweighted $a_i$", language),
    )
    kwargs.setdefault(
        "label",
        _t("Weighted $W_i a_i$ ({name})", language).format(name=result.weighting_name),
    )
    ax.bar(
        positions + width / 2,
        weighted,
        width,
        **kwargs,
    )
    ax.set_ylabel(_t("r.m.s. acceleration [m/s²]", language))
    # Wh is the hand-arm weighting of ISO 5349-1; the others (Wk, Wd, Wm...)
    # are the whole-body weightings of ISO 2631.
    designation = "ISO 5349-1" if str(result.weighting_name) == "Wh" else "ISO 2631"
    ax.set_title(
        _t(
            "{designation} weighted acceleration spectrum  ($a_\\mathrm{{w}}$ = {aw} m/s²)",
            language,
        ).format(
            designation=designation,
            aw=format_number(float(result.overall), language, decimals=3),
        )
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    # localize_axes leaves the categorical band axis (a FuncFormatter) alone.
    localize_axes(ax, language)
    return ax


def plot_daily_exposure(
    result: DailyVibrationExposure,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Partial daily exposures against the EAV / ELV (Directive 2002/44/EC).

    Draws one bar per operation (its partial exposure ``A_i(8)``), a combined
    ``A(8)`` bar, and the exposure action and limit value as horizontal lines.

    :param result: A
        :class:`~phonometry.vibration.human.exposure.DailyVibrationExposure` exposing
        ``labels``, ``partials``, ``a8`` and ``assessment``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to each exposure :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import decimal_comma, format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    partials = np.asarray(result.partials, dtype=np.float64)
    n_ops = partials.size
    values = [*partials.tolist(), float(result.a8)]
    # A small gap separates the combined A(8) bar from the operation bars.
    positions = [*range(n_ops), n_ops + 0.5]

    # One bar per operation, each with its own colour and legend label, so the
    # operation identity lives in the legend rather than in crowded, rotated
    # x-axis category labels. The combined A(8) bar takes the distinct A(8)
    # colour. A caller-supplied colour/width would collide with the per-bar
    # colouring, so those keys are consumed here.
    kwargs.pop("color", None)
    width = kwargs.pop("width", 0.7)
    edgecolor = kwargs.pop("edgecolor", _C_EDGE)
    for i in range(n_ops):
        # A copy per bar, not one `setdefault` before the loop: each task bar
        # carries its own name and the total carries another, so a single
        # default would put the first task's label on every one of them.
        task_kwargs = dict(kwargs)
        task_kwargs.setdefault("label", str(result.labels[i]))
        ax.bar(
            positions[i],
            partials[i],
            width=width,
            color=_OP_COLORS[i % len(_OP_COLORS)],
            edgecolor=edgecolor,
            linewidth=0.6,
            zorder=3,
            **task_kwargs,
        )
    total_kwargs = dict(kwargs)
    total_kwargs.setdefault("label", "$A(8)$")
    ax.bar(
        positions[-1],
        values[-1],
        width=width,
        color=_A8_COLOR,
        edgecolor=edgecolor,
        linewidth=0.6,
        zorder=3,
        **total_kwargs,
    )
    # The legend carries the bar identity, so the crowded category ticks go.
    ax.set_xticks([])
    ax.set_ylabel(_t("Vibration exposure $A(8)$ [m/s²]", language))

    assessment = result.assessment
    eav = float(assessment.action_value)
    elv = float(assessment.limit_value)
    ax.axhline(
        eav,
        color=_C_SECONDARY,
        ls="--",
        lw=1.4,
        label="EAV = " + decimal_comma(f"{eav:g}", language),
    )
    ax.axhline(
        elv,
        color=_C_REFERENCE,
        ls="--",
        lw=1.4,
        label="ELV = " + decimal_comma(f"{elv:g}", language),
    )
    top = max(elv, float(np.max(values))) * 1.28
    ax.set_ylim(0.0, top)
    kind = str(assessment.kind).upper()
    zone = _t(str(assessment.zone), language)
    ax.set_title(
        _t(
            "Directive 2002/44/EC daily {kind} exposure  ($A(8)$ = {a8} m/s², {zone})",
            language,
        ).format(
            kind=kind,
            a8=format_number(float(result.a8), language, decimals=2),
            zone=zone,
        )
    )
    handles, leg_labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        leg_labels,
        loc="upper center",
        ncol=min(3, len(handles)),
        fontsize="small",
        frameon=True,
        framealpha=0.9,
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    localize_axes(ax, language)
    return ax


def plot_mobility(
    result: MobilityResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Mobility magnitude ``|Y(f)|`` on log-log axes (ISO 7626-1).

    :param result: A :class:`~phonometry.vibration.structural.mechanical_mobility.MobilityResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the magnitude ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    mag = np.asarray(result.magnitude, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    label = (
        _t("driving-point mobility", language)
        if result.driving_point
        else _t("transfer mobility", language)
    )
    kwargs.setdefault("label", label)
    ax.loglog(freq, mag, **kwargs)
    # Mark the mobility peak (a resonance for a driving-point FRF).
    peak = int(np.argmax(mag))
    ax.plot(
        freq[peak],
        mag[peak],
        "o",
        color=_C_REFERENCE,
        zorder=5,
        label=_t("peak at {v} Hz", language).format(
            v=format_number(freq[peak], language, decimals=1)
        ),
    )
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_MOBILITY_LABEL, language))
    ax.set_title(_t("ISO 7626-1 mechanical mobility", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_rigid_mass_calibration(
    result: RigidMassCalibrationResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes | np.ndarray:
    """Rigid-mass operational calibration check (ISO 7626-2, 7.5.2).

    The single-concept calibration-check figure: the measured driving-point
    FRF magnitude against the known rigid-mass line with its +/- tolerance
    band (upper panel), and the relative deviation against the same tolerance
    band (lower panel, where the few-percent band is actually readable). A
    point outside the band is a failed frequency and is drawn in the
    out-of-tolerance colour; the title carries the overall verdict.

    With ``ax`` supplied, only the deviation diagnostic is drawn on it and that
    axes is returned; otherwise a fresh two-panel column is created and the
    two-axes array is returned.

    :param result: A
        :class:`~phonometry.vibration.structural.mechanical_mobility.RigidMassCalibrationResult`.
    :param ax: Existing axes for the deviation panel, or ``None`` for a fresh
        two-panel figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary artist: the measured-magnitude
        curve for the full two-panel figure, or the deviation curve when ``ax``
        is supplied.
    :return: The deviation axes (``ax`` given) or the two-axes array.
    """
    from .._i18n import format_number, localize_axes

    freq = np.asarray(result.frequencies, dtype=np.float64)
    measured = np.asarray(result.measured, dtype=np.float64)
    expected = np.asarray(result.expected, dtype=np.float64)
    deviation = np.asarray(result.deviation, dtype=np.float64)
    within = np.asarray(result.within_tolerance, dtype=bool)
    tol = float(result.tolerance)
    tol_pct = 100.0 * tol
    fmin, fmax = float(freq.min()), float(freq.max())
    p = format_number(tol_pct, language, decimals=1, trim=True)
    band_label = _t(r"$\pm${p} % tolerance", language).format(p=p)
    exp_label = (
        _t(r"expected $|A| = 1/m$", language)
        if result.quantity == "accelerance"
        else _t(r"expected $|Y| = 1/(2\pi f m)$", language)
    )
    mag_ylabel = (
        _t("Accelerance $|A|$ [1/kg]", language)
        if result.quantity == "accelerance"
        else _t(_MOBILITY_LABEL, language)
    )
    within_label = _t("measured (within tolerance)", language)
    outside_label = _t("measured (out of tolerance)", language)

    def _deviation_panel(axd: Axes, **line_kwargs: Any) -> None:
        axd.axhspan(-tol_pct, tol_pct, color=_C_REFERENCE, alpha=0.15, label=band_label)
        axd.axhline(0.0, color=_C_MUTED, ls=":", lw=0.9)
        line_kwargs.setdefault("color", _C_PRIMARY)
        axd.semilogx(freq, 100.0 * deviation, "-", lw=1.4, zorder=2, **line_kwargs)
        axd.plot(
            freq[within],
            100.0 * deviation[within],
            "o",
            color=_C_PRIMARY,
            zorder=3,
            label=within_label,
        )
        if not np.all(within):
            axd.plot(
                freq[~within],
                100.0 * deviation[~within],
                "o",
                color=_C_SECONDARY,
                zorder=4,
                label=outside_label,
            )
        axd.set_xlabel(_t(_FREQ_LABEL, language))
        axd.set_ylabel(_t(_DEVIATION_LABEL, language))
        axd.grid(visible=True, which="both", alpha=0.3)
        axd.legend(loc="best", fontsize="small")

    if ax is not None:
        _deviation_panel(ax, **kwargs)
        format_frequency_axis(ax, fmin, fmax)
        localize_axes(ax, language)
        return ax

    axes = _new_axes_column(2, sharex=True, figsize=(8.0, 6.6))
    axm, axd = axes[0], axes[1]
    kwargs.setdefault("color", _C_PRIMARY)
    axm.fill_between(
        freq,
        expected * (1.0 - tol),
        expected * (1.0 + tol),
        color=_C_REFERENCE,
        alpha=0.15,
        label=band_label,
    )
    axm.loglog(freq, expected, ls="--", color=_C_REFERENCE, lw=1.4, label=exp_label)
    kwargs.setdefault("label", within_label)
    axm.loglog(freq, measured, "o-", lw=1.4, **kwargs)
    if not np.all(within):
        axm.plot(
            freq[~within],
            measured[~within],
            "o",
            color=_C_SECONDARY,
            zorder=4,
            label=outside_label,
        )
    axm.set_ylabel(mag_ylabel)
    axm.grid(visible=True, which="both", alpha=0.3)
    axm.legend(loc="best", fontsize="small")
    if result.passed:
        verdict = "CORRECTO" if language == "es" else "PASS"
    else:
        verdict = "INCORRECTO" if language == "es" else "FAIL"
    axm.set_title(
        _t("ISO 7626-2 rigid-mass calibration check", language) + f" ({verdict})"
    )
    _deviation_panel(axd)
    for axf in axes:
        format_frequency_axis(axf, fmin, fmax)
        localize_axes(axf, language)
    return axes


def plot_transfer_stiffness(
    result: TransferStiffnessResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Dynamic transfer stiffness level ``L_k(f)`` on a log-frequency axis.

    :param result: A :class:`~phonometry.vibration.structural.transfer_stiffness.TransferStiffnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the level ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    level = np.asarray(result.level, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", r"$L_k = 20\,\log_{10}(|k_{2,1}|/k_0)$")
    ax.semilogx(freq, level, **kwargs)
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Transfer stiffness level $L_k$ [dB re 1 N/m]", language))
    ax.set_title(_t("ISO 10846 dynamic transfer stiffness", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_radiation_efficiency(
    result: RadiationEfficiencyResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Radiation efficiency ``sigma(f)`` on log-log axes (Hopkins 2.9.4).

    :param result: A
        :class:`~phonometry.vibration.structural.radiation_efficiency.RadiationEfficiencyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``sigma`` curve ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    sigma = np.asarray(result.radiation_efficiency, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("markersize", 3)
    kwargs.setdefault("label", r"$\sigma(f)$")
    ax.loglog(freq, sigma, **kwargs)
    ax.axhline(1.0, color=_C_MUTED, ls=":", lw=0.9, label=r"$\sigma = 1$")
    ax.axvline(
        result.critical_frequency,
        color=_C_REFERENCE,
        ls="--",
        lw=1.0,
        label=f"$f_\\mathrm{{c}}$ = {result.critical_frequency:.0f} Hz",
    )
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(r"Radiation efficiency $\sigma$", language))
    ax.set_title(_t("Plate radiation efficiency (Leppington / Maidanik)", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_seat_transmission(
    result: SeatTransmissionResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The runs of one simulated input vibration test, and the SEAT between them.

    Platform and seat side by side for each run, with the mean of each set as
    a line, which is what the SEAT factor is the ratio of.

    :param result: A
        :class:`~phonometry.vibration.human.seat_vibration.SeatTransmissionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the seat bars.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    runs = np.arange(len(result.platform_runs)) + 1.0
    width = 0.36
    platform_bars = ax.bar(
        runs - width / 2,
        result.platform_runs,
        width=width,
        color=_C_PRIMARY,
        label=_t(r"platform $a_\mathrm{wP}$", language),
    )
    kwargs.setdefault("color", _C_TERTIARY)
    kwargs.setdefault("label", _t(r"seat $a_\mathrm{wS}$", language))
    seat_bars = ax.bar(runs + width / 2, result.seat_runs, width=width, **kwargs)
    means = [
        ax.axhline(
            value,
            color=colour,
            ls="--",
            lw=1.1,
            label=_t("mean {value}", language).format(
                value=format_number(value, language, decimals=2)
            ),
        )
        for value, colour in (
            (result.platform_acceleration, _C_PRIMARY),
            (result.seat_acceleration, _C_TERTIARY),
        )
    ]
    ax.set_xticks(runs)
    ax.set_xlabel(_t("Test run", language))
    ax.set_ylabel(_t("Weighted r.m.s. acceleration [m/s²]", language))
    ax.set_title(
        _t("Seat transmission (ISO 10326-1): SEAT = {value}", language).format(
            value=format_number(result.seat_factor, language, decimals=2)
        )
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    # Each mean beside the set it belongs to: matplotlib would otherwise list
    # the two dashed lines first, leaving colour as the only clue to which
    # surface each average came from.
    ax.legend(
        handles=[platform_bars, means[0], seat_bars, means[1]],
        loc="best",
        fontsize="small",
    )
    localize_axes(ax, language)
    return ax


def plot_weighting_verification(
    result: WeightingVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A measured weighting response inside the band ISO 8041-1 allows it.

    The design goal as a line, the Table 5 tolerance band around it as a
    shaded region, and the measurement as points, the ones outside the band
    marked apart. The band is drawn from the tolerances rather than from a
    fixed number of decibels, so it widens at the transition frequencies of
    Table 4 exactly where the standard widens it.

    :param result: A
        :class:`~phonometry.vibration.human.instrumentation.WeightingVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-point ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..vibration.human.instrumentation import (
        UNCONSTRAINED_BELOW,
        weighting_tolerance_percent,
    )

    ax = ax if ax is not None else _new_axes()
    order = np.argsort(result.frequencies_hz)
    freqs = result.frequencies_hz[order]
    design = result.design[order]
    measured = result.measured[order]
    inside = result.within_tolerance[order]

    upper, lower = weighting_tolerance_percent(result.weighting, freqs)
    ax.fill_between(
        freqs,
        design * (1.0 + lower / 100.0),
        design * (1.0 + upper / 100.0),
        color=_C_PRIMARY,
        alpha=0.15,
        label=_t(_ISO8041_BAND_LABEL, language),
    )
    # 13.1 and 14.1 subtract the laboratory's own expanded uncertainty from
    # both limits, so with one supplied the band a measurement is actually
    # accepted in is narrower than the printed one. Drawing only the printed
    # band would put a failing point inside the shaded region with nothing to
    # explain it. The tail keeps its lower edge, exactly as the verdict does.
    uncertainty = result.expanded_uncertainty_percent
    if uncertainty > 0.0:
        unconstrained = lower <= UNCONSTRAINED_BELOW
        effective_lower = np.where(unconstrained, lower, lower + uncertainty)
        ax.fill_between(
            freqs,
            design * (1.0 + effective_lower / 100.0),
            design * (1.0 + (upper - uncertainty) / 100.0),
            color=_C_PRIMARY,
            alpha=0.3,
            label=_t("accepted with U = {u} %", language).format(
                u=format_number(uncertainty, language, decimals=2, trim=True)
            ),
        )
    ax.plot(freqs, design, color=_C_PRIMARY, lw=2.0, label=_t("design goal", language))

    _plot_verdict_points(ax, freqs, measured, inside, kwargs, language)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Weighting factor", language))
    verdict = _t("PASS" if result.passes else "FAIL", language)
    ax.set_title(
        _t("{w} weighting against ISO 8041-1: {verdict}", language).format(
            w=result.weighting, verdict=verdict
        )
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_phase_verification(
    result: PhaseVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The characteristic phase deviation inside the band ISO 8041-1 allows it.

    The quantity drawn is Formula (6), not the phase error: a modulus, one
    value per adjacent pair of frequencies, attributed to the lower one. So
    the band is drawn from the axis floor up to the Table 5 limit rather than
    symmetrically about a line, and the two tails, where the standard sets no
    limit, are filled to the top of the axes.

    :param result: A
        :class:`~phonometry.vibration.human.instrumentation.PhaseVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-point ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..vibration.human.instrumentation import SKIRT_TOLERANCE_PERCENT

    ax = ax if ax is not None else _new_axes()
    freqs = result.characteristic_frequencies_hz
    deviation = result.characteristic_deviation_deg
    inside = result.within_tolerance
    limits = result.tolerance_deg

    finite = limits[np.isfinite(limits)]
    tallest = max(
        float(finite.max()) if finite.size else 0.0,
        float(deviation.max()) if deviation.size else 0.0,
    )
    ceiling = 1.2 * tallest if tallest > 0.0 else float(SKIRT_TOLERANCE_PERCENT[2])
    band = np.where(np.isfinite(limits), limits, ceiling)
    # Table 5 is a piecewise-constant limit that steps at the Table 4
    # transition frequencies, so the band is held between samples and stepped
    # at them rather than ramped, which would draw a limit the standard never
    # sets across the one-third octave either side of a corner.
    ax.fill_between(
        freqs,
        np.zeros_like(band),
        band,
        step="post",
        color=_C_PRIMARY,
        alpha=0.15,
        label=_t(_ISO8041_BAND_LABEL, language),
    )

    _plot_verdict_points(ax, freqs, deviation, inside, kwargs, language)

    # A plain logarithmic axis rather than the octave-centre ticks of
    # format_frequency_axis, and for the same reason the magnitude verdict
    # beside this one uses one: the nominal centres that helper labels start
    # at 1 Hz, and half of the whole-body range is below that.
    ax.set_xscale("log")
    ax.set_ylim(0.0, ceiling)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Characteristic phase deviation [deg]", language))
    verdict = _t("PASS" if result.passes else "FAIL", language)
    ax.set_title(
        _t(
            "{w} characteristic phase deviation against ISO 8041-1: {verdict}",
            language,
        ).format(w=result.weighting, verdict=verdict)
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


#: The three rows of Table 1, in the order DIN 4150-3 prints them.
_DAMAGE_CLASS_LABELS = {
    "commercial": "commercial and industrial",
    "residential": "dwellings",
    "sensitive": "especially sensitive",
}
_DAMAGE_CLASS_COLORS = (_C_PRIMARY, _C_TERTIARY, _C_SECONDARY)


def _damage_curves(ax: Axes, result: DamageAssessment, language: str) -> float:
    """Draw Bild 1 and return where the reading sits on the frequency axis."""
    from ..vibration.structural.building_damage import (
        BUILDING_CLASSES,
        FOUNDATION_FREQUENCIES_HZ,
        SHORT_TERM_FOUNDATION_MM_S,
    )

    if result.frequency_hz is None:
        # DamageAssessment is public, so one can be built by hand with the
        # short-term foundation case and no frequency, which is the one case
        # Table 1 does not cover. Parking the point at the axis limit and
        # labelling it "at 100 Hz" would report a frequency nobody measured.
        msg = (
            "A short-term foundation assessment is read off Bild 1 at the "
            "dominant frequency, and this one carries none; there is nowhere "
            "on the frequency axis to place it."
        )
        raise ValueError(msg)
    freqs = np.asarray(FOUNDATION_FREQUENCIES_HZ, dtype=np.float64)
    for cls, color in zip(BUILDING_CLASSES, _DAMAGE_CLASS_COLORS, strict=True):
        assessed = cls == result.building_class
        ax.plot(
            freqs,
            np.asarray(SHORT_TERM_FOUNDATION_MM_S[cls], dtype=np.float64),
            color=color,
            lw=2.0 if assessed else 1.2,
            alpha=1.0 if assessed else 0.45,
            marker="o",
            markersize=3,
            label=_t(_DAMAGE_CLASS_LABELS[cls], language),
        )
    x_point = float(result.frequency_hz)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_xlim(0.0, max(float(freqs[-1]), x_point) * 1.02)
    return x_point


def _damage_bars(ax: Axes, result: DamageAssessment, language: str) -> float:
    """Draw the printed value per class and return where the reading sits."""
    from ..vibration.structural.building_damage import (
        BUILDING_CLASSES,
        LONG_TERM_TOP_FLOOR_MM_S,
        SHORT_TERM_TOP_FLOOR_MM_S,
    )

    table = (
        LONG_TERM_TOP_FLOOR_MM_S
        if result.duration == "long_term"
        else SHORT_TERM_TOP_FLOOR_MM_S
    )
    positions = np.arange(len(BUILDING_CLASSES), dtype=np.float64)
    for position, cls, color in zip(
        positions, BUILDING_CLASSES, _DAMAGE_CLASS_COLORS, strict=True
    ):
        # No legend entry: the class of each bar is its own tick label, and the
        # one being assessed is the bar the marker sits on.
        ax.bar(
            position,
            table[cls],
            width=0.6,
            color=color,
            alpha=1.0 if cls == result.building_class else 0.45,
        )
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [_t(_DAMAGE_CLASS_LABELS[cls], language) for cls in BUILDING_CLASSES]
    )
    ax.set_xlabel(_t("Building class", language))
    return float(positions[BUILDING_CLASSES.index(result.building_class)])


def _damage_title(result: DamageAssessment, language: str) -> str:
    """Name the table the reading was read against."""
    if result.location == "foundation":
        return _t("Guideline values at the foundation (DIN 4150-3 Table 1)", language)
    if result.duration == "long_term":
        return _t(
            "Long-term guideline values in the topmost floor plane "
            "(DIN 4150-3 Table 3)",
            language,
        )
    return _t(
        "Guideline values in the topmost floor plane (DIN 4150-3 Table 1)", language
    )


def plot_damage_assessment(
    result: DamageAssessment,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The guideline values the assessment was actually read against.

    A short-term foundation assessment gets Bild 1: the three Table 1 curves
    against frequency, with the measurement as a point on them. Every other
    assessment is read off a table that prints one value per building class
    and none per frequency, so it gets that table instead, as one bar per
    class with the measurement beside its own. Drawing the foundation curves
    for a top-floor or a long-term reading would show a criterion that did
    not apply to it.

    :param result: A
        :class:`~phonometry.vibration.structural.building_damage.DamageAssessment`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-point ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    reading = format_number(result.velocity_mm_s, language, decimals=1, trim=True)
    on_bild_1 = result.location == "foundation" and result.duration == "short_term"

    if on_bild_1:
        x_point = _damage_curves(ax, result, language)
        point_label = _t("measured {v} mm/s at {f} Hz", language).format(
            v=reading, f=format_number(x_point, language, decimals=0)
        )
    else:
        x_point = _damage_bars(ax, result, language)
        point_label = _t("measured {v} mm/s", language).format(v=reading)

    style_default(kwargs, "color", _C_REFERENCE)
    kwargs.setdefault("marker", "D")
    style_default(kwargs, "markersize", 7)
    style_default(kwargs, "ls", "none")
    kwargs.setdefault("label", point_label)
    ax.plot([x_point], [result.velocity_mm_s], **kwargs)
    ax.set_ylabel(_t("Peak velocity $v_i$ [mm/s]", language))
    ax.set_title(_damage_title(result, language))
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    localize_axes(ax, language)
    return ax


def plot_building_frequency(
    result: BuildingFrequencyEstimate,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Figure D.1 of ISO 4866 with one estimate on it.

    The ``f = 46/h`` fit against building height on logarithmic axes, the
    ± 50 % band D.3 puts around an empirical prediction, and the estimate as a
    point. A prediction from another of the annex's forms lands off the line,
    which is the comparison the figure is for.

    :param result: A
        :class:`~phonometry.vibration.structural.building_response.BuildingFrequencyEstimate`
        carrying a height.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the estimate-point ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..vibration.structural.building_response import (
        EMPIRICAL_FREQUENCY_TOLERANCE,
        height_fundamental_frequency,
    )

    ax = ax if ax is not None else _new_axes()
    height = float(result.height_m or 0.0)
    span = np.logspace(np.log10(3.0), np.log10(300.0), 300)
    fit = np.asarray(height_fundamental_frequency(span), dtype=np.float64)
    ax.plot(fit, span, color=_C_PRIMARY, lw=2.0, label=_t(_LABEL_HEIGHT_FIT, language))
    ax.fill_betweenx(
        span,
        fit * (1.0 - EMPIRICAL_FREQUENCY_TOLERANCE),
        fit * (1.0 + EMPIRICAL_FREQUENCY_TOLERANCE),
        color=_C_PRIMARY,
        alpha=0.15,
        label=_t(r"$\pm$50 %, which D.3 calls not uncommon", language),
    )
    style_default(kwargs, "color", _C_REFERENCE)
    kwargs.setdefault("marker", "D")
    style_default(kwargs, "markersize", 7)
    style_default(kwargs, "ls", "none")
    kwargs.setdefault(
        "label",
        _t("{model} model: {f} Hz at {h} m", language).format(
            model=_t(result.model, language),
            f=format_number(result.frequency_hz, language, decimals=2),
            h=format_number(height, language, decimals=0),
        ),
    )
    ax.plot([result.frequency_hz], [height], **kwargs)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Building height $h$ [m]", language))
    ax.set_title(
        _t("Empirical fundamental frequency of a building (ISO 4866 D.3)", language)
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_multiple_shock(
    result: MultipleShockResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Injury-probability curve ``P(R)`` with this assessment's ``R`` marked.

    :param result: A :class:`~phonometry.vibration.human.multiple_shock.MultipleShockResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``R`` marker ``scatter``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from ..vibration.human.multiple_shock import injury_probability

    ax = ax if ax is not None else _new_axes()
    r10, r50, r90 = result.risk_thresholds
    r_max = max(result.risk, r90) * 1.3
    grid = np.linspace(0.0, r_max, 240)
    prob = np.asarray(injury_probability(grid, sex=result.sex), dtype=np.float64)
    ax.plot(
        grid,
        100.0 * prob,
        color=_C_PRIMARY,
        label=r"$\Pi(R) = 1 - e^{-(R/\alpha)^{\beta}}$",
    )
    for level, r_val in zip((10, 50, 90), (r10, r50, r90), strict=True):
        ax.axhline(level, color=_C_MUTED, ls=":", lw=0.8)
        ax.plot([r_val, r_val], [0.0, level], color=_C_MUTED, ls=":", lw=0.8)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 4)
    kwargs.setdefault("s", 90)
    kwargs.setdefault(
        "label",
        _t(_RISK_LABEL, language).format(
            r=format_number(result.risk, language, decimals=2),
            p=format_number(100.0 * result.probability, language, decimals=0),
        ),
    )
    ax.scatter([result.risk], [100.0 * result.probability], **kwargs)
    ax.set_xlabel(_t("Stress variable $R$", language))
    ax.set_ylabel(_t("Probability of lumbar injury [%]", language))
    ax.set_title(
        _t("ISO 2631-5 injury probability — {sex}", language).format(
            sex=_t(str(result.sex), language)
        )
    )
    ax.set_xlim(left=0.0)
    ax.set_ylim(0.0, 100.0)
    ax.legend(loc="lower right", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


#: Marker colour of each fault-line family, so shaft harmonics never read as
#: bearing evidence on the overlay.
_FAMILY_COLORS: dict[str, str] = {
    "shaft": _C_MUTED,
    "bearing": _C_REFERENCE,
    "gear": _C_TERTIARY,
    "motor": _C_QUATERNARY,
    "blade": _C_SECONDARY,
}


def _draw_measured_spectrum(
    ax: Axes,
    frequencies: NDArray[np.float64] | None,
    amplitude: NDArray[np.float64] | None,
    f_max: float,
    language: str,
    kwargs: dict[str, Any],
) -> float:
    """Draw the measured curve under the overlay; return its peak amplitude.

    Without a spectrum only the axis label is set and the reference height is
    1, so the predicted lines fill the axes on their own.
    """
    if frequencies is None or amplitude is None:
        ax.set_ylabel(_t("Predicted fault line", language))
        return 1.0
    keep = frequencies <= f_max
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("lw", 1.0)
    kwargs.setdefault("label", _t("envelope spectrum", language))
    ax.plot(frequencies[keep], amplitude[keep], **kwargs)
    ax.set_ylabel(_t("Envelope amplitude", language))
    return float(np.max(amplitude[keep])) if np.any(keep) else 1.0


#: Gap between a fault line and its own rotated label, in points.
_LABEL_PAD_PT = 2.0
#: Horizontal room one rotated ``x-small`` label needs, in points. The name is
#: turned through 90 degrees, so what it occupies across the axis is its text
#: height, not its length. Used when the names cannot be measured on the
#: figure's own renderer.
_LABEL_WIDTH_PT = 8.5
#: Fallback axis width, in points, when the axes geometry is not available.
_LABEL_FALLBACK_WIDTH_PT = 400.0
#: Fallback axis height, in points, when the axes geometry is not available.
_LABEL_FALLBACK_HEIGHT_PT = 260.0
#: Gap kept above the names, between them and the top of the axes, in points.
#: Wide enough to absorb the shrinking a later ``tight_layout`` does to the
#: axes: the strip is cut before the caller composes the figure, so a name
#: measured against a taller panel still has room in the one that is drawn.
_LABEL_TOP_PAD_PT = 8.0
#: Lowest the name strip is allowed to start, as a fraction of the axes: a name
#: long enough to want more than this is given the strip it fits in, rather than
#: the one it asks for, so the spectrum is never squeezed out of its own panel.
_LABEL_BAND_FLOOR = 0.62
#: White space kept between one name and the next, in points, on top of the
#: measured width of a name: two of them are only told apart by the gap.
_LABEL_GAP_PT = 1.0


def _axis_extent_points(ax: Axes) -> tuple[float, float]:
    """Width and height of the axes box in points, for laying names out in it."""
    try:
        box = ax.get_window_extent()
        dpi = float(ax.get_figure().dpi)  # type: ignore[union-attr]
        width_pt, height_pt = box.width * 72.0 / dpi, box.height * 72.0 / dpi
    except (AttributeError, ValueError):  # pragma: no cover - defensive
        return _LABEL_FALLBACK_WIDTH_PT, _LABEL_FALLBACK_HEIGHT_PT
    return (
        width_pt if width_pt > 0.0 else _LABEL_FALLBACK_WIDTH_PT,
        height_pt if height_pt > 0.0 else _LABEL_FALLBACK_HEIGHT_PT,
    )


def _axis_width_points(ax: Axes) -> float:
    """Width of the axes box in points, for laying labels out across it."""
    return _axis_extent_points(ax)[0]


def _label_strip(ax: Axes, names: list[str]) -> tuple[float, float]:
    """Where the names go: strip start as an axes fraction, and their thickness.

    The names are set turned through 90 degrees, so the room they need above
    the lines is the length of the longest of them and the room they take
    across the axis is the height of one line of text. Both are measured on
    the figure's own renderer, so the strip is cut to the width the reader will
    actually see rather than to an assumed one.
    """
    _, height_pt = _axis_extent_points(ax)
    probe = ax.text(0.0, 0.0, "", rotation=90, fontsize="x-small", alpha=0.0)
    length_pt, thickness_pt = 0.0, 0.0
    try:
        dpi = float(ax.get_figure().dpi)  # type: ignore[union-attr]
        for name in names:
            probe.set_text(name)
            box = probe.get_window_extent()
            length_pt = max(length_pt, box.height * 72.0 / dpi)
            thickness_pt = max(thickness_pt, box.width * 72.0 / dpi)
    except (AttributeError, RuntimeError, ValueError):  # pragma: no cover
        length_pt, thickness_pt = 0.0, 0.0
    finally:
        probe.remove()
    if thickness_pt <= 0.0:  # pragma: no cover - defensive
        return 1.0, _LABEL_WIDTH_PT
    band = 1.0 - (length_pt + _LABEL_TOP_PAD_PT) / height_pt
    return max(band, _LABEL_BAND_FLOOR), thickness_pt + _LABEL_GAP_PT


def _label_offsets(
    frequencies: list[float],
    f_max: float,
    width_pt: float,
    label_pt: float = _LABEL_WIDTH_PT,
) -> dict[int, float]:
    """Horizontal label offsets in points, keyed by index into *frequencies*.

    The names are drawn rotated, so each occupies a narrow vertical strip and
    two of them collide when their lines sit less than *label_pt* apart across
    the axis. Walking the lines in frequency order and pushing each label just
    far enough right to clear the previous one separates a crowded group with
    the least displacement that fits: an isolated line keeps its label exactly
    where it was, and a run of evenly spaced sidebands drifts by the difference
    between the label width and the spacing, no more.
    """
    scale = width_pt / f_max if f_max > 0.0 else 0.0
    offsets: dict[int, float] = {}
    cursor = -np.inf
    for i in sorted(range(len(frequencies)), key=lambda i: frequencies[i]):
        anchor = frequencies[i] * scale + _LABEL_PAD_PT
        placed = max(anchor, cursor)
        offsets[i] = placed - frequencies[i] * scale
        cursor = placed + label_pt
    return offsets


def _draw_fault_lines(
    ax: Axes,
    result: FaultFrequencyResult,
    f_max: float,
    language: str,
    *,
    annotate: bool,
) -> float:
    """Draw one dashed line per predicted fault frequency, coloured by family.

    Each family contributes a single legend entry, so shaft harmonics never
    read as bearing evidence. The lines stop where their names begin, so a
    crowded group -- gear sidebands sit a shaft rate apart, a few points on a
    kilohertz axis -- reads as a strip of names above a strip of lines instead
    of names struck through by their neighbours' lines. The strip start is
    returned as an axes fraction, for the caller to keep the spectrum and its
    legend below it.
    """
    visible = [line for line in result.lines if line.frequency <= f_max]
    band, label_pt = 1.0, _LABEL_WIDTH_PT
    if annotate:
        band, label_pt = _label_strip(ax, [line.name for line in visible])
    offsets = _label_offsets(
        [line.frequency for line in visible],
        f_max,
        _axis_width_points(ax),
        label_pt,
    )
    labelled: set[str] = set()
    for i, line in enumerate(visible):
        colour = _FAMILY_COLORS.get(line.family, _C_EDGE)
        label = None if line.family in labelled else _t(line.family, language)
        labelled.add(line.family)
        ax.axvline(
            line.frequency,
            ymax=band,
            color=colour,
            ls="--",
            lw=1.0,
            alpha=0.85,
            label=label,
            zorder=2,
        )
        if annotate:
            ax.annotate(
                line.name,
                xy=(line.frequency, band),
                xycoords=("data", "axes fraction"),
                xytext=(offsets[i], _LABEL_PAD_PT),
                textcoords="offset points",
                rotation=90,
                fontsize="x-small",
                color=colour,
                ha="left",
                va="bottom",
            )
    return band


def _measured_spectrum_vectors(
    spectrum: _SpectrumLike,
) -> tuple[np.ndarray, np.ndarray]:
    """The two vectors of ``spectrum``, measured before either scales an axis.

    ``spectrum`` is a structural contract, anything exposing the two vectors,
    so there is no construction of ours to pin it at and the refusals belong
    where the caller's parameter is named. Our own producer,
    :func:`phonometry.signals.envelope.envelope_spectrum`, satisfies all three
    of them, which is why every mistake here is in what the caller assembled.

    Each check answers a failure the next one cannot see. **A run of bins** is
    what the equal-shape pin cannot ask for on its own, since two bare numbers
    agree on the empty shape and two grids agree on both of theirs: an empty
    pair then dies in the axis scaling as numpy's own "zero-size array to
    reduction operation maximum which has no identity", while the numbers and
    the grid are drawn in silence, the first as a single point under limits
    matplotlib widens for being singular, the second as one line per column
    over an axis that was never measured on them. **One amplitude per bin**,
    because the curve is drawn from the mask ``frequencies <= f_max`` applied
    to both, and a shorter amplitude indexed by a mask built on the longer
    axis stops the render with "boolean index did not match indexed array".
    **Finite throughout**, because both vectors scale an axis with ``np.max``,
    so one non-finite sample becomes the whole limit and matplotlib refuses it
    with "Axis limits cannot be NaN or Inf". None of those three names this
    argument or the field inside it.

    :param spectrum: The measured spectrum drawn under the fault lines.
    :returns: Its frequency and amplitude vectors, as ``float64``.
    :raises ValueError: if either vector is not a non-empty one-dimensional
        run of bins, if the two disagree in shape, or if either carries a
        non-finite sample.
    """
    frequencies = np.asarray(spectrum.frequencies, dtype=np.float64)
    amplitude = np.asarray(spectrum.amplitude, dtype=np.float64)
    vectors = (("frequencies", frequencies), ("amplitude", amplitude))
    for field, values in vectors:
        if values.ndim != 1 or values.size == 0:
            msg = (
                f"'spectrum.{field}' must be a non-empty one-dimensional "
                f"run of frequency bins; got shape {values.shape}."
            )
            raise ValueError(msg)
    require_equal_shapes(
        "FaultFrequencyResult.plot",
        {
            "spectrum.frequencies": frequencies.shape,
            "spectrum.amplitude": amplitude.shape,
        },
        "frequency bin",
    )
    for field, values in vectors:
        if not np.all(np.isfinite(values)):
            msg = f"'spectrum.{field}' must contain only finite values."
            raise ValueError(msg)
    return frequencies, amplitude


def plot_fault_frequencies(
    result: FaultFrequencyResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    spectrum: _SpectrumLike | None = None,
    max_frequency: float | None = None,
    annotate: bool = True,
    **kwargs: Any,
) -> Axes:
    """Predicted machine fault lines over a measured envelope spectrum.

    The working diagnostic view: the envelope spectrum of a band-passed
    vibration record with the kinematic lines of the bearing, gear, motor or
    impeller drawn on top and named. A peak is only evidence when it lands on
    a named line, which is what the overlay makes readable.

    :param result: A
        :class:`~phonometry.vibration.machinery.diagnostics.FaultFrequencyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param spectrum: Measured spectrum to draw underneath: an
        :class:`~phonometry.signals.envelope.EnvelopeSpectrumResult`, or any
        object exposing ``frequencies`` and ``amplitude``. Without it the
        predicted lines are drawn alone.
    :param max_frequency: Upper limit of the frequency axis, in hertz
        (Default: the spectrum's own upper limit, or 1,15 x the highest line).
    :param annotate: Label each line with its name (Default: ``True``).
    :param kwargs: Forwarded to the spectrum curve.
    :return: The axes.
    :raises ValueError: If the result carries no lines, or *spectrum* carries a
        non-finite frequency or amplitude, or its two vectors disagree in shape.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    if freqs.size == 0:
        msg = "the result carries no fault lines to plot."
        raise ValueError(msg)

    f_max = max_frequency
    spectrum_f = spectrum_a = None
    if spectrum is not None:
        spectrum_f, spectrum_a = _measured_spectrum_vectors(spectrum)
        if f_max is None:
            f_max = float(spectrum_f.max())
    if f_max is None:
        f_max = 1.15 * float(freqs.max())

    top = _draw_measured_spectrum(ax, spectrum_f, spectrum_a, f_max, language, kwargs)
    band = _draw_fault_lines(ax, result, f_max, language, annotate=annotate)
    ax.set_ylim(0.0, 1.03 * top / band)
    ax.set_xlim(0.0, f_max)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_title(
        _t("Predicted fault lines: {src}, shaft {fs} Hz", language).format(
            src=_t(result.source, language),
            fs=format_number(result.shaft_rate, language, decimals=2, trim=True),
        )
    )
    # The legend belongs to the spectrum, so it is anchored to the part of the
    # axes the spectrum has: above the strip start there are only line names.
    ax.legend(loc="upper right", fontsize="small", bbox_to_anchor=(0.0, 0.0, 1.0, band))
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_power_injection(
    result: PowerInjectionResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Loss-factor budget of a two-subsystem SEA model (Norton Ch. 6).

    The measured coupling loss factors against the internal loss factors on
    one logarithmic axis: SEA is only trustworthy where the coupling stays
    below the internal damping, so the ordering of the four curves is the
    diagnosis.

    :param result: A
        :class:`~phonometry.vibration.structural.experimental_sea.PowerInjectionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``eta_12`` curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("markersize", 4)
    kwargs.setdefault("label", r"$\eta_{12}$")
    ax.loglog(freq, result.coupling_loss_factor12, **kwargs)
    ax.loglog(
        freq,
        result.coupling_loss_factor21,
        color=_C_SECONDARY,
        marker="s",
        markersize=4,
        label=r"$\eta_{21}$",
    )
    ax.loglog(
        freq,
        result.internal_loss_factor1,
        color=_C_TERTIARY,
        ls="--",
        lw=1.1,
        label=r"$\eta_{1}$",
    )
    ax.loglog(
        freq,
        result.internal_loss_factor2,
        color=_C_QUATERNARY,
        ls=":",
        lw=1.3,
        label=r"$\eta_{2}$",
    )
    format_frequency_axis(ax, float(freq.min()), float(freq.max()))
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Loss factor", language))
    ax.set_title(
        _t("Power-injection SEA loss factors ({method})", language).format(
            method=_t(result.method, language)
        )
    )
    ax.legend(loc="best", fontsize="small", ncol=2)
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_junction_transmission(
    result: JunctionTransmissionResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Plot ``tau(theta)`` versus incidence angle (Hopkins Eqs 5.12/5.13).

    Draws the corner coefficient and, where it exists, the straight-section
    coefficient, with their diffuse-field angular averages as horizontal
    reference lines.

    :param result: A
        :class:`~phonometry.vibration.structural.junction_transmission.JunctionTransmissionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the corner-curve ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    angles = np.asarray(result.angles_deg, dtype=np.float64)
    corner = np.asarray(result.corner, dtype=np.float64)

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", _t(r"corner $\tau_{12}(\theta)$", language))
    ax.plot(angles, corner, **kwargs)
    ax.axhline(
        result.corner_average,
        color=_C_PRIMARY,
        ls="--",
        lw=1.0,
        label=_t(r"corner average $\bar\tau_{12}$ = {value}", language).replace(
            "{value}", format_number(result.corner_average, language, decimals=4)
        ),
    )
    if result.straight is not None and result.straight_average is not None:
        straight = np.asarray(result.straight, dtype=np.float64)
        ax.plot(
            angles,
            straight,
            color=_C_SECONDARY,
            label=_t(r"straight $\tau_{13}(\theta)$", language),
        )
        ax.axhline(
            result.straight_average,
            color=_C_SECONDARY,
            ls=":",
            lw=1.0,
            label=_t(r"straight average $\bar\tau_{13}$ = {value}", language).replace(
                "{value}", format_number(result.straight_average, language, decimals=4)
            ),
        )

    ax.set_xlim(0.0, 90.0)
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel(_t("Incidence angle [deg]", language))
    ax.set_ylabel(_t(r"Transmission coefficient $\tau$", language))
    ax.set_title(
        _t(
            "Bending-wave transmission, {junction}-junction "
            "($\\chi$ = {chi}, $\\psi$ = {psi})",
            language,
        ).format(
            junction=result.junction,
            chi=format_number(result.chi, language, decimals=3),
            psi=format_number(result.psi, language, decimals=3),
        )
    )
    ax.grid(visible=True, color=_C_MUTED, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def _radial_label_angle(first: complex, second: complex) -> float:
    """Where to park the radial tick labels, in degrees.

    The middle of the widest gap between the two phasors and the chord that
    joins them, so the labels never run along a drawn line.
    """
    drawn = sorted(
        float(np.degrees(np.angle(z)) % 360.0) for z in (first, second, second - first)
    )
    gaps = [
        (drawn[(i + 1) % len(drawn)] - angle) % 360.0 for i, angle in enumerate(drawn)
    ]
    widest = int(np.argmax(gaps))
    return (drawn[widest] + gaps[widest] / 2.0) % 360.0


def _polar_chord(
    first: complex, second: complex, points: int = 64
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Sample the straight Cartesian segment between two phasors.

    A polar axes interpolates between two points along an arc, so a chord
    drawn as two points comes out bowed. The change vector of Annex D is a
    straight line between the tips of the two states, and a bowed one would
    misread as a path the vibration took, so the segment is sampled in the
    plane and converted point by point.
    """
    t = np.linspace(0.0, 1.0, points)
    line = first + (second - first) * t
    return np.angle(line), np.abs(line)


def plot_vector_change(
    result: VectorChangeResult,
    ax: Axes | None = None,
    *,
    language: str = "en",
    unit: str | None = None,
    **kwargs: Any,
) -> Axes:
    """Change in vibration between two steady states (ISO 20816-1, Figure D.1).

    The two states as phasors from the origin and the change as the chord
    joining their tips. The picture is the argument of Annex D: the chord can
    be far longer than the difference of the two radii, so a criterion written
    on broad-band magnitude alone misses the change entirely.

    :param result: A
        :class:`~phonometry.vibration.machinery.evaluation.VectorChangeResult`.
    :param ax: Existing polar axes, or ``None`` to create a polar figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param unit: Unit of the two magnitudes, appended to the title's numbers.
        The result carries whichever unit its inputs were in and cannot know
        it, so the caller names it or the title stays bare.
    :param kwargs: Forwarded to the change chord.
    :return: The (polar) axes.
    :raises ValueError: If *ax* is not a polar axes.
    """
    from .._i18n import format_number, localize_axes
    from .electroacoustics import _new_polar_axes, _sign_theta_labels

    if ax is not None and getattr(ax, "name", None) != "polar":
        msg = (
            "'ax' must be a polar axes (subplot_kw={'projection': 'polar'}); "
            "pass ax=None to create one."
        )
        raise ValueError(msg)
    polar = cast("PolarAxes", ax) if ax is not None else _new_polar_axes()
    ax = polar

    first = result.initial[0] * np.exp(1j * np.radians(result.initial[1]))
    second = result.final[0] * np.exp(1j * np.radians(result.final[1]))
    for phasor, color, key in (
        (first, _C_PRIMARY, _LABEL_INITIAL),
        (second, _C_SECONDARY, _LABEL_FINAL),
    ):
        angle = float(np.angle(phasor))
        ax.plot(
            [0.0, angle],
            [0.0, float(abs(phasor))],
            color=color,
            linewidth=2.0,
            marker="o",
            markevery=[1],
            label=_t(key, language),
        )
    kwargs.setdefault("color", _C_TERTIARY)
    kwargs.setdefault("linewidth", 2.0)
    kwargs.setdefault("linestyle", "--")
    theta, radius = _polar_chord(first, second)
    kwargs.setdefault("label", _t(_LABEL_CHANGE, language))
    ax.plot(theta, radius, **kwargs)

    _sign_theta_labels(polar)
    # The radial ticks would otherwise run along whichever phasor happens to
    # lie near the default position; park them where no vector points.
    polar.set_rlabel_position(_radial_label_angle(first, second))
    suffix = f" {unit}" if unit else ""
    ax.set_title(
        _t("Change in vibration: magnitude {mag}, vector {vec}", language).format(
            mag=format_number(result.magnitude_change, language, decimals=2, trim=True)
            + suffix,
            vec=format_number(result.magnitude, language, decimals=2, trim=True)
            + suffix,
        )
    )
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="lower left", fontsize="small", bbox_to_anchor=(-0.15, -0.1))
    localize_axes(ax, language)
    return ax


#: The printed columns of ISO 8041-1 Tables 7 to 9 and the label each series
#: carries. The two dose values keep their acronyms, which are identifiers.
_BURST_QUANTITY_LABELS: dict[str, str] = {
    "rms": "r.m.s. value",
    "vdv": "VDV",
    "mtvv_linear": "MTVV linear",
    "mtvv_exponential": "MTVV exponential",
    "msdv": "MSDV",
}
#: One colour and one marker per printed column, in printed order.
_BURST_COLORS = (_C_PRIMARY, _C_SECONDARY, _C_TERTIARY, _C_QUATERNARY, _C_REFERENCE)
_BURST_MARKERS = ("o", "s", "^", "D", "v")
#: The row of Tables 7 to 9 that grades the band-limiting response, spelled as
#: :data:`phonometry.vibration.BAND_LIMITING` spells it.
_BAND_LIMITING_ROW = "band-limiting"
#: The application keys of Table 6, as a title spells them.
_BURST_APPLICATIONS: dict[str, str] = {
    "hand-arm": "hand-arm",
    "whole-body": "whole-body",
    "low-frequency-whole-body": "low-frequency whole-body",
}


def plot_signal_burst_verification(
    result: SignalBurstVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Signal-burst deviations against the tolerance printed beside them.

    One marker series per printed column of Table 7, 8 or 9, across the burst
    lengths the table prints, inside the shaded band the same table allows.
    The vibration dose value is allowed 12 % where every other column is
    allowed 10 %, so the wider pair is drawn as a dashed edge instead of
    widening the band under all of them.

    :param result: A
        :class:`~phonometry.vibration.human.signal_burst.SignalBurstVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to every marker series.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = np.arange(len(result.cycle_counts), dtype=np.float64)
    inner = float(np.min(result.tolerance_percent))
    outer = float(np.max(result.tolerance_percent))
    ax.axhspan(
        -inner,
        inner,
        color=_C_MUTED,
        alpha=0.18,
        label=_t(r"printed tolerance $\pm${p} %", language).format(
            p=format_number(inner, language, decimals=0)
        ),
    )
    if outer > inner:
        wider = _t(r"printed tolerance $\pm${p} % (VDV)", language).format(
            p=format_number(outer, language, decimals=0)
        )
        # The label goes on the first edge only: the pair is one band, and
        # matplotlib would otherwise list it twice.
        for index, edge in enumerate((-outer, outer)):
            ax.axhline(
                edge,
                color=_C_MUTED,
                ls="--",
                lw=1.0,
                label=wider if index == 0 else None,
            )
    ax.axhline(0.0, color=_C_EDGE, lw=0.8)

    # The continuous row has no burst length, so the axis is a list of rows
    # and not a scale: a line drawn from the longest burst to it would read as
    # a trend across an interval that does not exist. The bursts are joined to
    # one another, the continuous row is left as a detached marker, and a rule
    # says where the list stops being ordered by anything.
    detached_from = next(
        (k for k, cycles in enumerate(result.cycle_counts) if cycles is None),
        len(result.cycle_counts),
    )
    if 0 < detached_from < len(result.cycle_counts):
        ax.axvline(
            float(detached_from) - 0.5,
            color=_C_MUTED,
            ls=":",
            lw=0.9,
            zorder=0,
        )

    for index, quantity in enumerate(result.quantities):
        style = dict(kwargs)
        style_default(style, "color", _BURST_COLORS[index % len(_BURST_COLORS)])
        style_default(style, "marker", _BURST_MARKERS[index % len(_BURST_MARKERS)])
        style_default(style, "linewidth", 1.2)
        style.setdefault("label", _t(_BURST_QUANTITY_LABELS[quantity], language))
        values = result.deviation_percent[:, index]
        ax.plot(positions[:detached_from], values[:detached_from], **style)
        if detached_from < len(result.cycle_counts):
            detached = {
                key: value
                for key, value in style.items()
                if key not in {"label", "linestyle", "ls"}
            }
            detached["ls"] = "none"
            ax.plot(positions[detached_from:], values[detached_from:], **detached)

    ax.set_xticks(list(positions))
    ax.set_xticklabels(
        [
            _t("continuous", language)
            if cycles is None
            else format_number(cycles, language, decimals=0)
            for cycles in result.cycle_counts
        ]
    )
    ax.set_xlabel(_t("Saw-tooth cycles per burst", language))
    ax.set_ylabel(_t(_DEVIATION_LABEL, language))
    row = (
        _t("band limiting", language)
        if result.weighting == _BAND_LIMITING_ROW
        else result.weighting
    )
    application = _t(_BURST_APPLICATIONS[result.application], language)
    ax.set_title(
        _t(
            "Signal-burst response (ISO 8041-1)\n{name}, {application}", language
        ).format(name=row, application=application)
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_vibration_meter_verification(
    result: VibrationMeterVerification,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A measured response inside the band DIN 45669-1 Tables 2 and 3 allow.

    The deviation ``F(f)`` of Formula (7) against frequency, with the two
    limits as a shaded region around zero. The band is drawn from the tables
    rather than from a fixed number, so it steps out from 10 % to 20 % at
    ``1,25 f_u`` and ``0,8 f_o`` exactly where the standard steps it, and the
    frequencies where the lower limit is 100 % are where the standard stops
    constraining the response from below at all.

    :param result: A
        :class:`~phonometry.vibration.immission.vibration_meter.VibrationMeterVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-point ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    order = np.argsort(result.frequencies_hz)
    freqs = result.frequencies_hz[order]
    deviation = result.deviation_percent[order]
    lower = result.lower_percent[order]
    upper = result.upper_percent[order]
    inside = result.within_tolerance[order]

    # The upper limit is infinite where the measured response sits below the
    # 0,01 of footnote a. Drawing an infinite edge would blank the axes, so
    # the band is closed at the largest finite limit and the points still
    # carry the verdict.
    finite_upper = upper[np.isfinite(upper)]
    ceiling = float(np.max(finite_upper)) if finite_upper.size else 100.0
    ax.fill_between(
        freqs,
        -lower,
        np.where(np.isfinite(upper), upper, ceiling),
        color=_C_PRIMARY,
        alpha=0.15,
        label=_t("DIN 45669-1 tolerance", language),
    )
    ax.axhline(0.0, color=_C_PRIMARY, lw=1.5)

    _plot_verdict_points(ax, freqs, deviation, inside, kwargs, language)

    ax.set_xscale("log")
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Response deviation $F(f)$ [%]", language))
    ax.set_title(
        _t("{weighting} response against DIN 45669-1: {verdict}", language).format(
            weighting=_t("KB" if result.weighting == "kb" else "unweighted", language),
            verdict=_t("PASS" if result.passes else "FAIL", language),
        )
    )
    format_frequency_axis(ax, float(freqs[0]), float(freqs[-1]), language=language)
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_vibration_meter_reading(
    result: VibrationMeterReading,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The weighted vibration severity of one record, with what it reduces to.

    ``KB_F(t)`` against time, the maximum it reaches, and the clock maxima
    that Formula (2) averages, each drawn at the middle of the 30 s interval
    it belongs to. The two horizontal lines are the numbers a meter displays,
    and the distance between them is what a long quiet stretch does to a
    reading dominated by a short event.

    :param result: A
        :class:`~phonometry.vibration.immission.vibration_meter.VibrationMeterReading`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``KB_F(t)`` ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    times = np.arange(result.kbf.size) / result.fs_hz
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.2)
    kwargs.setdefault("label", _t(_KBF_LABEL, language))
    ax.plot(times, result.kbf, **kwargs)
    ax.axhline(
        result.kbf_max,
        color=_C_REFERENCE,
        ls="--",
        lw=1.5,
        label=_t(_KBF_MAX_LABEL, language).format(
            value=format_number(result.kbf_max, language, decimals=3, trim=True)
        ),
    )
    if result.takt_maxima.size:
        takt_s = result.averaging_time_s / result.takt_maxima.size
        centres = (np.arange(result.takt_maxima.size) + 0.5) * takt_s
        ax.plot(
            centres,
            result.takt_maxima,
            color=_C_TERTIARY,
            marker="s",
            markersize=6,
            ls="none",
            label=_t("clock maximum", language),
        )
        ax.axhline(
            result.kbf_takt_rms,
            color=_C_TERTIARY,
            ls=":",
            lw=1.5,
            label=_t(_KBFTM_LABEL, language).format(
                value=format_number(
                    result.kbf_takt_rms, language, decimals=3, trim=True
                )
            ),
        )
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t(_KBF_LABEL, language))
    ax.set_title(
        _t("Vibration immission over {duration} s ({range} range)", language).format(
            duration=format_number(
                result.measuring_time_s, language, decimals=0, trim=True
            ),
            range=_t(result.working_range, language),
        )
    )
    ax.set_ylim(bottom=0.0)
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_assessment_velocity(
    result: AssessmentVelocity,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The Annex E assessment velocity against the one value it is judged by.

    ``v_B(t)`` against time with the guideline value of Table E.2 as a pair of
    lines, above and below zero because the quantity judged is the largest
    absolute value. There is no frequency axis and no guideline curve: that is
    the whole point of Annex E.

    :param result: An
        :class:`~phonometry.vibration.immission.vibration_meter.AssessmentVelocity`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``v_B(t)`` ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    times = np.arange(result.velocity_mm_s.size) / result.fs_hz
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.0)
    kwargs.setdefault(
        "label",
        _t("peak {value} mm/s", language).format(
            value=format_number(
                result.assessment_velocity_mm_s, language, decimals=2, trim=True
            )
        ),
    )
    ax.plot(times, result.velocity_mm_s, **kwargs)
    guide = result.guide_value_mm_s
    ax.axhline(
        guide,
        color=_C_REFERENCE,
        ls="--",
        lw=1.5,
        label=_t("guideline {value} mm/s", language).format(
            value=format_number(guide, language, decimals=0, trim=True)
        ),
    )
    ax.axhline(-guide, color=_C_REFERENCE, ls="--", lw=1.5)
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t("Assessment velocity $v_B$ [mm/s]", language))
    ax.set_title(
        _t(
            "Short-term vibration by DIN 45669-1 Annex E ({cls}): {verdict}",
            language,
        ).format(
            cls=_t(_DAMAGE_CLASS_LABELS[result.building_class], language),
            verdict=_t("PASS" if result.within_guideline else "FAIL", language),
        )
    )
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_train_passage(
    result: TrainPassage,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """One passage against time, with the three stretches it is read over.

    The velocity the meter's band limitation leaves, drawn light, its running
    r.m.s. of Formula (1) over it, and the maximum of that; above the record,
    the brackets of Figure 2 mark :math:`T_1`, :math:`T_2` and :math:`T_3`, so
    the reader sees at once that the event value is formed over more than the
    train and the characteristic values over less.

    :param result: A
        :class:`~phonometry.vibration.immission.railway.TrainPassage`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the running r.m.s. ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    times = np.arange(result.velocity_mm_s.size) / result.fs_hz
    ax.plot(
        times,
        result.velocity_mm_s,
        color=_C_MUTED,
        lw=0.6,
        alpha=0.6,
        label=_t("velocity $v(t)$", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("label", _t(_RUNNING_RMS_LABEL, language))
    ax.plot(times, result.running_rms_mm_s, **kwargs)
    ax.axhline(
        result.running_rms_max_mm_s,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=_t(_RUNNING_MAX_LABEL, language).format(
            value=format_number(
                result.running_rms_max_mm_s, language, decimals=3, trim=True
            )
        ),
    )
    # The brackets of Figure 2 sit above the record in axes coordinates, one
    # row per stretch with T_1 on top, and the record is scaled into the band
    # between them and the one-row legend underneath, so neither covers it.
    top = float(np.max(np.abs(result.velocity_mm_s)))
    if top <= 0.0:
        top = 1.0
    bracket_axes = ax.get_xaxis_transform()
    for index, ((start, end), row) in enumerate(
        zip(result.intervals_s, _BRACKET_ROWS, strict=True)
    ):
        ax.annotate(
            "",
            xy=(end, row),
            xytext=(start, row),
            xycoords=bracket_axes,
            textcoords=bracket_axes,
            arrowprops={"arrowstyle": "<->", "color": _C_EDGE, "lw": 1.0},
        )
        ax.text(
            0.5 * (start + end),
            row + 0.01,
            f"$T_{index + 1}$",
            transform=bracket_axes,
            ha="center",
            va="bottom",
            color=_C_EDGE,
        )
    ax.set_ylim(-1.5 * top, 1.9 * top)
    ax.set_xlabel(_t(_TIME_LABEL, language))
    ax.set_ylabel(_t("Velocity [mm/s]", language))
    ax.set_title(
        _t("Train passage by DIN 45672-2: $v_E$ = {value} mm/s", language).format(
            value=format_number(
                result.event_velocity_mm_s, language, decimals=4, trim=True
            )
        )
    )
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="lower center", ncol=3, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_train_passage_spectrum(
    result: TrainPassage,
    ax: Axes | None = None,
    *,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The interval and maximum third-octave levels of one passage (Figure 6).

    The interval level over :math:`T_2` of Formula (6) and the maximum level
    over :math:`T_3` of Formula (7), band by band. The gap between them is the
    crest of the running r.m.s. in each band: wide where the vibration comes
    in bursts, narrow where it is steady for the whole passage.

    :param result: A
        :class:`~phonometry.vibration.immission.railway.TrainPassage`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the maximum-level ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.band_centres_hz, language=language)
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 1.6)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "markersize", 4)
    kwargs.setdefault("label", _t(_MAX_LEVEL_LABEL, language))
    ax.plot(positions, result.band_max_levels_db, **kwargs)
    ax.plot(
        positions,
        result.band_interval_levels_db[1],
        color=_C_TERTIARY,
        ls="--",
        lw=1.4,
        marker="s",
        markersize=4,
        label=_t(_INTERVAL_LEVEL_LABEL, language),
    )
    ax.set_ylabel(_t(_BAND_LEVEL_LABEL, language))
    ax.set_title(_t("Third-octave spectra of one passage (DIN 45672-2)", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax
