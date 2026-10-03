#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the building domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from .common import (
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_QUATERNARY,
    _C_REFERENCE,
    _C_SECONDARY,
    _C_SECONDARY_LIGHT,
    _C_TERTIARY,
    _LEGEND_UPPER_LEFT,
    _annotate_impact_500,
    _band_axis,
    _facade_x_axis,
    _format_freq,
    _freq_axis,
    _import_pyplot,
    _new_axes,
    _plot_band_level_bars,
    _plot_insulation_bands,
    _plot_rating,
    _require_rating_curve,
    format_frequency_axis,
    place_legend_clear,
    style_default,
    theme_fill,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes

    from ..building.measurement.flanking_transmission import VibrationReductionResult
    from ..building.measurement.floor_covering_improvement import (
        FloorCoveringImprovementResult,
    )
    from ..building.measurement.heavy_impact import (
        AWeightedMaximumImpactResult,
        HeavyImpactSourceCheck,
        StandardizedMaximumImpactResult,
    )
    from ..building.measurement.insulation import (
        AirborneInsulationResult,
        ExtendedImpactRatingResult,
        ExtendedWeightedRatingResult,
        FacadeInsulationResult,
        ImpactInsulationResult,
        ImpactRatingResult,
        WeightedRatingResult,
    )
    from ..building.measurement.intensity_insulation import (
        LowFrequencyElementResult,
        LowFrequencyIntensityResult,
    )
    from ..building.measurement.lab_improvement import (
        HeavyImpactImprovementResult,
        LabFloorCoveringImprovementResult,
        LabLiningImprovementResult,
        LiningCuringCheck,
    )
    from ..building.measurement.low_frequency import LowFrequencyResult
    from ..building.measurement.rainfall_sound import (
        RainfallReferenceCorrection,
        RainfallSoundResult,
        RainGeneratorVerification,
    )
    from ..building.measurement.ratings import (
        ImpactImprovementRatingResult,
        ReductionImprovementRating,
    )
    from ..building.measurement.service_equipment import (
        BackgroundDurationCheck,
        CalibrationDeviationResult,
        InstrumentAgreementCheck,
        MeasurementDisturbanceCheck,
        PositionSpreadCheck,
        ServiceEquipmentBackgroundResult,
        ServiceEquipmentPositionCheck,
        ServiceEquipmentResult,
        VaryingBackgroundCheck,
    )
    from ..building.measurement.structure_borne_power import StructureBornePowerResult
    from ..building.measurement.uncertainty import BandUncertainty
    from ..building.prediction.aperture_transmission import ApertureTransmissionResult
    from ..building.prediction.ceiling_plenum import (
        CeilingAttenuationResult,
        PlenumFlankingResult,
    )
    from ..building.prediction.detailed_model import (
        DetailedAirborneResult,
        DetailedImpactResult,
        InSituElementResult,
    )
    from ..building.prediction.facade import FacadePredictionResult, RadiatedPowerResult
    from ..building.prediction.installed_structure_borne import InstalledSourceResult
    from ..building.prediction.masonry_cavity_wall import WallTieCouplingResult
    from ..building.prediction.panel_transmission import SoundReductionResult
    from ..building.prediction.resilient_layers import (
        CoveringImprovementResult,
        FloatingFloorImprovementResult,
        LiningImprovementResult,
        TappingForceResult,
    )
    from ..building.prediction.simplified_model import (
        AirbornePredictionResult,
        ImpactPredictionResult,
    )
    from ..building.regulation.spain import (
        DbHrAssessment,
        DbHrGlobalIndexResult,
    )

#: Shared x-axis label for the frequency-domain building plots.
_FREQ_LABEL = "Frequency [Hz]"

#: Shared x-axis label of the plots drawn against band ordinals rather than
#: centre frequencies (the ISO 717 reference-curve shifts).
_BAND_INDEX_LABEL = "Band index"

#: Shared y-axis label of the heavy-impact level figures.
_MAX_IMPACT_LABEL = "Maximum impact sound pressure level [dB]"

#: Shared y-axis label of the figures drawing the sound reduction index under
#: its symbol (the panel and aperture transmission predictions).
_R_INDEX_LABEL = "Sound reduction index $R$ [dB]"

#: The apparent sound reduction index's symbol, as every curve label writes it:
#: composed prime (never the U+2032 character, which sits at x-height and takes
#: a following subscript with it).
_R_PRIME = r"$R^{\prime}$"

#: Shared y-axis label of the sound-insulation figures that spell the quantity
#: out instead (the airborne measurement and prediction curves).
_REDUCTION_INDEX_LABEL = "Sound reduction index [dB]"

#: Shared y-axis label of the impact sound pressure level figures.
_IMPACT_LEVEL_LABEL = "Impact sound pressure level [dB]"

#: Shared y-axis label of the façade figures, which mix level differences and
#: reduction indices on the same axis.
_LEVEL_DIFFERENCE_LABEL = "Level difference / reduction index [dB]"

#: Y-axis label and title of the ISO 16283 low-frequency figure, which plots
#: room levels rather than a difference between two of them.
_SPL_LABEL = "Sound pressure level [dB]"
_LOW_FREQUENCY_TITLE = "Low-frequency procedure (ISO 16283)"

#: Shared y-axis label of the path-contribution figures (the simplified
#: single-number bars and the two detailed per-band ones).
_SHARE_LABEL = "Share of transmitted energy [%]"

#: Shared y-axis label of the impact-improvement figures (the ISO 16251-1
#: measurement and the two resilient-layer predictions).
_IMPROVEMENT_LABEL = r"Improvement of impact sound insulation $\Delta L$ [dB]"

#: Symbols and labels of the ISO 15186-3 low-frequency figure. The index and
#: the field indicator share one figure, so the indicator gets a twin axis and
#: its own spelled-out label.
_R_INTENSITY = "$R_I$"
_D_INTENSITY_ELEMENT = "$D_{I\\mathrm{n,e}}$"

#: Y-axis label of the element figure. The quantity is a normalized level
#: difference and not a reduction index, so it does not share the label of
#: its sibling.
_ELEMENT_DIFFERENCE_LABEL = "Element normalized level difference [dB]"
_F_PI = "$F_{pI}$"
_INDICATOR_LABEL = "Surface pressure-intensity indicator [dB]"

#: Bar width of the ISO 15186-3 figure, shared by the index bars and the
#: hatch that overlays the bands Clause 6.4.2 refuses so the two coincide.
_BAR_WIDTH = 0.7
_LOW_FREQUENCY_INTENSITY_TITLE = (
    "Low-frequency intensity sound insulation (ISO 15186-3)"
)
_LOW_FREQUENCY_ELEMENT_TITLE = (
    "Low-frequency element normalized level difference (ISO 15186-3)"
)

#: Titles of the ISO/DIS 16032 figures.
_SERVICE_TITLE = "Service-equipment level (ISO/DIS 16032)"
_BACKGROUND_TITLE = "Background correction (ISO/DIS 16032, Clause 9)"
_SPREAD_TITLE = "Spread between positions (ISO/DIS 16032, 7.4.1)"
_POSITIONS_TITLE = "Microphone positions (ISO/DIS 16032, 7.2 and 7.3)"
_CALIBRATION_TITLE = "Calibration (ISO/DIS 16032, Clause 5)"
_DURATION_TITLE = "Background measurement time (ISO/DIS 16032, 7.6)"
_VARYING_TITLE = "Varying background (ISO/DIS 16032, NOTE to Clause 9)"
_DISTURBANCE_TITLE = "Maximum against equivalent level (ISO/DIS 16032, Clause 9)"
_AGREEMENT_TITLE = "Calculation against the instrument (ISO/DIS 16032, 7.8)"
#: Legend labels the measurement and background figures of ISO/DIS 16032
#: share.
_BACKGROUND_L2_LABEL = "background $L_2$"
_CORRECTED_LABEL = "corrected for background"
#: Legend label of the measurement at hand, which the calibration figure of
#: ISO/DIS 16032 and the curing figure of ISO 10140-1 share.
_THIS_MEASUREMENT_LABEL = "this measurement"
#: Size of a plan of the positions the renderer draws on a figure of its own,
#: in inches: wide enough for the plan and the key beside it.
_POSITIONS_FIGURE_SIZE_IN = (9.0, 6.0)
#: Where the plan sits on that figure, as (left, bottom, width, height) in
#: figure fractions: the right third is left to the key, the top to the
#: two-line title. A fixed place rather than a layout engine, which settles an
#: equal-aspect axes with a key beside it only after several passes and not
#: the same way with every font.
_POSITIONS_AXES_RECT = (0.08, 0.1, 0.58, 0.76)

#: The verdict words the conformance figures read in their titles.
_CONFORMS = "conforms"
_DOES_NOT_CONFORM = "does not conform"

#: Spanish translations of the fixed labels/titles/legends rendered by the
#: building-domain ``.plot()`` renderers, keyed by their verbatim English
#: text. ``_t`` returns the English key unchanged for any language other
#: than ``"es"``, so the English output is byte-for-byte identical to the
#: pre-i18n renderers.
_STRINGS: dict[str, str] = {
    _FREQ_LABEL: "Frecuencia [Hz]",
    "Band": "Banda",
    _BAND_INDEX_LABEL: "Índice de banda",
    "predicted $R$": "$R$ previsto",
    _R_INDEX_LABEL: "Índice de reducción acústica $R$ [dB]",
    "Predicted sound insulation": "Aislamiento acústico previsto",
    "coincidence plateau (A to B)": "meseta de coincidencia (A a B)",
    "coincidence range ($f_{c1}$ to $f_{c2}$)": "rango de coincidencia ($f_{c1}$ a $f_{c2}$)",
    "aperture $R$": "$R$ de abertura",
    "Aperture sound transmission (Gomperts / Wilson-Soroka)": "Transmisión sonora por abertura (Gomperts / Wilson-Soroka)",
    _REDUCTION_INDEX_LABEL: "Índice de reducción acústica [dB]",
    r"$\Sigma$ unfav.": r"$\Sigma$ desfav.",
    "impact rating": "índice de impacto",
    _IMPACT_LEVEL_LABEL: "Nivel de presión acústica de impactos [dB]",
    _LEVEL_DIFFERENCE_LABEL: "Diferencia de nivel / índice de reducción [dB]",
    _SPL_LABEL: "Nivel de presión acústica [dB]",
    _LOW_FREQUENCY_TITLE: "Procedimiento de baja frecuencia (ISO 16283)",
    _INDICATOR_LABEL: "Indicador presión-intensidad superficial [dB]",
    _LOW_FREQUENCY_INTENSITY_TITLE: "Aislamiento acústico por intensidad a baja frecuencia (ISO 15186-3)",
    _LOW_FREQUENCY_ELEMENT_TITLE: "Diferencia de niveles normalizada de elemento a baja frecuencia (ISO 15186-3)",
    _ELEMENT_DIFFERENCE_LABEL: "Diferencia de niveles normalizada de elemento [dB]",
    "not qualified (6.4.2)": "no cualificada (6.4.2)",
    "limit": "límite",
    "Façade sound insulation (ISO 16283-3)": "Aislamiento acústico de fachada (ISO 16283-3)",
    "Reduction index / level difference [dB]": "Índice de reducción / diferencia de nivel [dB]",
    "Façade insulation prediction (EN 12354-3)": "Predicción del aislamiento de fachada (EN 12354-3)",
    "Radiated sound power level [dB]": "Nivel de potencia acústica radiada [dB]",
    "Radiated sound power (EN 12354-4)": "Potencia acústica radiada (EN 12354-4)",
    "Vibration reduction index $K_{ij}$ [dB]": "Índice de reducción de vibraciones $K_{ij}$ [dB]",
    "Vibration reduction index (ISO 10848)": "Índice de reducción de vibraciones (ISO 10848)",
    "Structure-borne power level $L_{W\\mathrm{s}}$ [dB re 1 pW]": "Nivel de potencia estructural $L_{W\\mathrm{s}}$ [dB re 1 pW]",
    "EN 15657 characteristic structure-borne sound power": "Potencia acústica estructural característica EN 15657",
    "paths": "trayectos",
    "total $L_\\mathrm{n,s}$": "total $L_\\mathrm{n,s}$",
    "Normalised SPL $L_\\mathrm{n,s}$ [dB]": "NPS normalizado $L_\\mathrm{n,s}$ [dB]",
    "EN 12354-5 installed structure-borne sound": "Ruido estructural instalado EN 12354-5",
    "Transmission path": "Trayecto de transmisión",
    "Share of transmitted energy [%]": "Fracción de energía transmitida [%]",
    "flanking prediction": "predicción de transmisión por flancos",
    "Level / correction [dB]": "Nivel / corrección [dB]",
    "impact prediction": "predicción de impacto",
    "Airborne sound insulation (ISO 16283-1)": "Aislamiento a ruido aéreo (ISO 16283-1)",
    "Impact sound insulation (ISO 16283-2)": "Aislamiento a ruido de impacto (ISO 16283-2)",
    "Standard uncertainty $u$ [dB]": "Incertidumbre típica $u$ [dB]",
    "band uncertainty": "incertidumbre por banda",
    "situation": "situación",
    r"$\sigma_\mathrm{R95}$ upper limit": r"límite superior $\sigma_\mathrm{R95}$",
    r"limit of measurement (> $\Delta L$)": r"límite de medición (> $\Delta L$)",
    "enlarged range (Annex B)": "rango ampliado (Anexo B)",
    "enlarged range (A.2.1)": "rango ampliado (A.2.1)",
    "Measured": "Medido",
    "Shifted reference (core bands)": "Referencia desplazada (bandas 100-3150 Hz)",
    _IMPROVEMENT_LABEL: r"Mejora del aislamiento a ruido de impacto $\Delta L$ [dB]",
    "ISO 16251-1 Floor-Covering Impact Sound Improvement": "Mejora del aislamiento a ruido de impacto de revestimiento de suelo ISO 16251-1",
    "band insulation": "aislamiento por banda",
    "transmitted level $L_{x,i} - X_i$": "nivel transmitido $L_{x,i} - X_i$",
    "Band insulation $X_i$ [dB]": "Aislamiento por banda $X_i$ [dB]",
    "Transmitted level [dBA]": "Nivel transmitido [dBA]",
    "pink noise": "ruido rosa",
    "road traffic": "ruido de automóviles",
    "railway": "ruido ferroviario",
    "aircraft": "ruido de aeronaves",
    "CTE DB-HR global index": "Índice global CTE DB-HR",
    "achieved": "obtenido",
    "required": "exigido",
    "Value": "Valor",
    "CTE DB-HR requirement check": "Comprobación de exigencias CTE DB-HR",
    "detailed prediction": "predicción detallada",
    "other paths": "otros trayectos",
    "In-situ element performance (ISO 12354)": "Comportamiento del elemento in situ (ISO 12354)",
    "Reduction index / impact level [dB]": "Índice de reducción / nivel de impactos [dB]",
    "tolerance band": "banda de tolerancia",
    "nominal $L_{FE}$": "$L_{FE}$ nominal",
    "measured $L_{FE}$": "$L_{FE}$ medido",
    "outside tolerance": "fuera de tolerancia",
    "Impact force exposure level $L_{FE}$ [dB re 1 N]": "Nivel de exposición a la fuerza de impacto $L_{FE}$ [dB re 1 N]",
    _CONFORMS: "cumple",
    _DOES_NOT_CONFORM: "no cumple",
    "Heavy impact source conformance": "Conformidad de la fuente de impacto pesada",
    "rubber ball": "pelota de caucho",
    "bang machine": "máquina de neumático",
    r"$L_\mathrm{i,Fmax}$ (measured)": r"$L_\mathrm{i,Fmax}$ (medido)",
    r"$L^{\prime}_{\mathrm{i,Fmax},V,T}$ (standardized)": r"$L^{\prime}_{\mathrm{i,Fmax},V,T}$ (estandarizado)",
    "standardization correction": "corrección de estandarización",
    _MAX_IMPACT_LABEL: "Nivel máximo de presión acústica de impactos [dB]",
    "ISO 16283-2 rubber-ball standardization": "Estandarización de la pelota de caucho ISO 16283-2",
    "A-weighted contribution": "contribución ponderada A",
    r"$X_\mathrm{i,Fmax}$ (unweighted)": r"$X_\mathrm{i,Fmax}$ (sin ponderar)",
    "ISO 717-2 Annex D heavy-impact rating": "Índice de impacto pesado ISO 717-2 Anexo D",
    "one-third octave": "tercio de octava",
    "octave": "octava",
    "Normalized ceiling attenuation": "Diferencia de niveles normalizada del techo",
    "Normalized ceiling attenuation $D_\\mathrm{n,c}$ [dB]": "Diferencia de niveles normalizada del techo $D_\\mathrm{n,c}$ [dB]",
    "$R_\\mathrm{S} + R_\\mathrm{R}$ (two ceilings)": "$R_\\mathrm{S} + R_\\mathrm{R}$ (dos techos)",
    r"$R_\mathrm{cl}$ (ceiling/plenum path)": r"$R_\mathrm{cl}$ (trayecto techo/plenum)",
    "plenum penalty": "penalización del plenum",
    "Suspended-ceiling plenum path": "Trayecto por plenum de techo suspendido",
    "rigid connection ($Y_\\mathrm{c}$ = 0)": "unión rígida ($Y_\\mathrm{c}$ = 0)",
    "resilient tie array": "conjunto de llaves elásticas",
    "isolation gained by the tie": "aislamiento aportado por la llave",
    "Coupling loss factor $\\eta_{ij}$": "Factor de pérdidas por acoplamiento $\\eta_{ij}$",
    "Wall-tie structure-borne coupling": "Acoplamiento estructural por llaves de muro",
    "ties/m²": "llaves/m²",
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Band index": "Índice de banda",
    "force spectrum $|F_n|$": "espectro de fuerza $|F_n|$",
    "Magnitude of the peak force $|F_n|$ [N]": "Magnitud de la fuerza de pico $|F_n|$ [N]",
    "ISO tapping machine force spectrum": "Espectro de fuerza de la máquina de impactos ISO",
    "over-critical": "sobrecrítico",
    "under-critical": "subcrítico",
    "band force ratio (Eq. 4.114)": "cociente de fuerzas por banda (Ec. 4.114)",
    "two-line estimate (0 dB, 12 dB/oct)": "estimación de dos rectas (0 dB, 12 dB/oct)",
    "Soft floor covering improvement (Hopkins 4.4.3.1)": "Reducción por revestimiento de suelo blando (Hopkins 4.4.3.1)",
    "Floating floor improvement (ISO 12354-2 Annex C)": "Reducción por suelo flotante (ISO 12354-2 Anexo C)",
    "Sound reduction index improvement [dB]": "Mejora del índice de reducción acústica [dB]",
    "Additional-layer rating (ISO 12354-1 Annex D)": "Magnitud global de capa adicional (ISO 12354-1 Anexo D)",
    _SERVICE_TITLE: "Nivel de los equipamientos (ISO/DIS 16032)",
    _BACKGROUND_TITLE: "Corrección por ruido de fondo (ISO/DIS 16032, cap. 9)",
    _SPREAD_TITLE: "Dispersión entre posiciones (ISO/DIS 16032, apartado 7.4.1)",
    _POSITIONS_TITLE: "Posiciones de micrófono (ISO/DIS 16032, apartados 7.2 y 7.3)",
    "average of the readings": "promedio de las lecturas",
    _BACKGROUND_L2_LABEL: "ruido de fondo $L_2$",
    "measured $L_1$": "medido $L_1$",
    _CORRECTED_LABEL: "corregido por ruido de fondo",
    "standardized $L_\\mathrm{nT}$": "estandarizado $L_\\mathrm{nT}$",
    "upper limit (background)": "límite superior (ruido de fondo)",
    "not standardized (7.7)": "sin estandarizar (apartado 7.7)",
    "Reading": "Lectura",
    "A-weighted level [dB]": "Nivel ponderado A [dB]",
    "corner": "esquina",
    "room positions": "posiciones en la sala",
    "allowed spread": "dispersión admitida",
    "proceed": "se continúa",
    "add positions": "añadir posiciones",
    "interrupt": "interrumpir",
    "and": "y",
    "room outline": "contorno de la sala",
    "surface clearance": "distancia a las superficies",
    "corner position": "posición de esquina",
    "reverberant-field positions": "posiciones en campo reverberante",
    "sound source": "fuente sonora",
    "distance to a source": "distancia a una fuente",
    "Length $x$ [m]": "Longitud $x$ [m]",
    "Width $y$ [m]": "Anchura $y$ [m]",
    "requirements met": "requisitos cumplidos",
    "requirements not met": "requisitos no cumplidos",
    _CALIBRATION_TITLE: "Calibración (ISO/DIS 16032, cap. 5)",
    _DURATION_TITLE: "Tiempo de medición del ruido de fondo (ISO/DIS 16032, apartado 7.6)",
    _VARYING_TITLE: "Ruido de fondo variable (ISO/DIS 16032, NOTA del cap. 9)",
    _DISTURBANCE_TITLE: "Nivel máximo frente al equivalente (ISO/DIS 16032, cap. 9)",
    _AGREEMENT_TITLE: "Cálculo frente al instrumento (ISO/DIS 16032, apartado 7.8)",
    "Calibration": "Calibración",
    "Calibrator reading [dB]": "Lectura del calibrador [dB]",
    "earlier calibrations": "calibraciones anteriores",
    "earlier": "anterior",
    "beginning": "inicio",
    "end": "final",
    _THIS_MEASUREMENT_LABEL: "esta medición",
    "within 0.5 dB of every earlier calibration": "a 0,5 dB o menos de cada calibración anterior",
    "largest deviation": "desviación máxima",
    "equipment may be used": "el equipo puede usarse",
    "equipment out of use until clarified": "equipo fuera de uso hasta aclararlo",
    "Background measurement": "Medición del ruido de fondo",
    "Measurement time [s]": "Tiempo de medición [s]",
    "measurement time": "tiempo de medición",
    "30 s of 7.6": "30 s del apartado 7.6",
    "tolerance accepted": "tolerancia aceptada",
    "beyond the tolerance": "fuera de la tolerancia",
    "every background within {tolerance} s of 30 s": (
        "todo el ruido de fondo a {tolerance} s o menos de 30 s"
    ),
    "largest departure {departure} s, beyond the {tolerance} s accepted": (
        "mayor desviación {departure} s, fuera de la tolerancia aceptada de {tolerance} s"
    ),
    "service equipment": "equipamiento",
    "background maximum": "máximo del ruido de fondo",
    "10 dB below the equipment": "10 dB por debajo del equipamiento",
    "less than 10 dB below": "menos de 10 dB por debajo",
    "valid without correction": "válido sin corrección",
    "not valid without correction": "no válido sin corrección",
    "watched for": "observado durante",
    "Measurement period": "Periodo de medición",
    "Maximum less equivalent level [dB]": "Nivel máximo menos nivel equivalente [dB]",
    "difference per period": "diferencia por periodo",
    "5 dB of Clause 9": "5 dB del cap. 9",
    "disturbed": "perturbado",
    "no period disturbed": "ningún periodo perturbado",
    "disturbed periods": "periodos perturbados",
    "Single number": "Valor único",
    "Calculated less instrument [dB]": "Calculado menos instrumento [dB]",
    "within 2 dB": "dentro de 2 dB",
    "calculated less instrument": "calculado menos instrumento",
    "calculation agrees": "el cálculo concuerda",
    "more than 2 dB apart: check the calculation": "más de 2 dB de diferencia: revisar el cálculo",
}

#: Localised names of the two standard heavy and soft impact sources.
_HEAVY_IMPACT_SOURCE_LABELS = {
    "rubber_ball": "rubber ball",
    "bang_machine": "bang machine",
}

#: Localised names of the two ISO 717-2 Annex D rating band widths.
_HEAVY_IMPACT_BAND_LABELS = {"third": "one-third octave", "octave": "octave"}


def _t(text: str, language: str = "en") -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    return _STRINGS.get(text, text) if language == "es" else text


def _verdict_word(*, passes: bool, language: str) -> str:
    """``conforms`` or ``does not conform``, localised."""
    return _t(_CONFORMS if passes else _DOES_NOT_CONFORM, language)


def plot_sound_reduction(
    result: SoundReductionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Predicted sound reduction index ``R(f)`` (Bies 7.2).

    :param result: A
        :class:`~phonometry.building.prediction.panel_transmission.SoundReductionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``R(f)`` curve ``plot``.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    r = np.asarray(result.transmission_loss, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "markersize", 3)
    kwargs.setdefault("label", _t("predicted $R$", language))
    ax.semilogx(freq, r, **kwargs)
    if result.critical_frequency is not None:
        symbol = (
            "$f_{c1}$"
            if result.critical_frequency_upper is not None
            else "$f_\\mathrm{c}$"
        )
        ax.axvline(
            result.critical_frequency,
            color=_C_REFERENCE,
            ls="--",
            lw=1.0,
            label=f"{symbol} = "
            f"{format_number(result.critical_frequency, language, decimals=0)} Hz",
        )
    if (
        result.critical_frequency is not None
        and result.critical_frequency_upper is not None
    ):
        # An orthotropic panel has a coincidence *range*, not a dip: shade it,
        # because that band is where R flattens below the mass law.
        ax.axvspan(
            result.critical_frequency,
            result.critical_frequency_upper,
            color=theme_fill(_C_TERTIARY, ax),
            lw=0,
            zorder=0,
            label=_t("coincidence range ($f_{c1}$ to $f_{c2}$)", language),
        )
        ax.axvline(
            result.critical_frequency_upper,
            color=_C_REFERENCE,
            ls="--",
            lw=1.0,
            label="$f_{c2}$ = "
            f"{format_number(result.critical_frequency_upper, language, decimals=0)} Hz",
        )
    if result.resonance_frequency is not None:
        ax.axvline(
            result.resonance_frequency,
            color=_C_SECONDARY,
            ls="--",
            lw=1.0,
            label=f"$f_0$ = {format_number(result.resonance_frequency, language, decimals=0)} Hz",
        )
    if result.plateau_start is not None and result.plateau_end is not None:
        # Shade the coincidence plateau of the Watters construction, whose two
        # construction points A and B are what the whole estimate hangs on.
        ax.axvspan(
            result.plateau_start,
            result.plateau_end,
            color=theme_fill(_C_SECONDARY, ax),
            lw=0,
            zorder=0,
            label=_t("coincidence plateau (A to B)", language),
        )
    format_frequency_axis(ax, float(freq.min()), float(freq.max()), language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_R_INDEX_LABEL, language))
    ax.set_title(f"{_t('Predicted sound insulation', language)} ({result.model})")
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_aperture_transmission(
    result: ApertureTransmissionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Aperture sound reduction index ``R(f) = -10 log10(tau)`` (Hopkins 4.3.10).

    :param result: An
        :class:`~phonometry.building.prediction.aperture_transmission.ApertureTransmissionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``R(f)`` curve ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    r = np.asarray(result.transmission_loss, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", f"{result.kind} {_t('aperture $R$', language)}")
    ax.semilogx(freq, r, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, ls=":", lw=0.9)
    format_frequency_axis(ax, float(freq.min()), float(freq.max()), language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_R_INDEX_LABEL, language))
    ax.set_title(_t("Aperture sound transmission (Gomperts / Wilson-Soroka)", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_weighted_rating(
    result: WeightedRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Airborne rating curve vs shifted reference (ISO 717-1).

    :param result: A :class:`~phonometry.building.measurement.insulation.WeightedRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    _require_rating_curve(result)
    ax = _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=False,
        title=(
            # Sign only when negative, the style of ISO 717-1's own examples.
            rf"ISO 717-1 $R_\mathrm{{w}}$ "
            rf"($C$={format_number(result.c, language, decimals=0)}; "
            rf"$C_\mathrm{{tr}}$={format_number(result.ctr, language, decimals=0)}) = "
            rf"{result.rating} dB  ({_t(r'$\Sigma$ unfav.', language)} = "
            rf"{format_number(result.unfavourable_sum, language, decimals=1)} dB)"
        ),
        ylabel=_t(_REDUCTION_INDEX_LABEL, language),
        ax=ax,
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_impact_rating(
    result: ImpactRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Impact rating curve vs shifted reference (ISO 717-2).

    The drawn shifted-reference curve is the normatively honest ``ref -
    shift``; for octave-band data the rating is that curve read at 500 Hz
    *minus 5 dB* (Clause 4.3.2), so the plot marks the 500 Hz read value on
    the (undistorted) curve and annotates the -5 dB reduction rather than
    pulling the curve down to the rating.

    :param result: An :class:`~phonometry.building.measurement.insulation.ImpactRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    _require_rating_curve(result)
    band_centers = np.asarray(result.band_centers, dtype=np.float64)
    reference = np.asarray(result.shifted_reference, dtype=np.float64)
    ax = _plot_rating(
        band_centers,
        np.asarray(result.measured, dtype=np.float64),
        reference,
        impact=True,
        # The rated quantity depends on the input (Ln,w, L'n,w or L'nT,w);
        # the dataclass does not carry which, so the figure uses the neutral
        # "impact rating" label rather than hard-coding one specific symbol.
        title=(
            # Sign only when negative, the style of ISO 717-2's own examples.
            rf"ISO 717-2 {_t('impact rating', language)} "
            rf"($C_\mathrm{{I}}$={format_number(result.ci, language, decimals=0)}) = "
            rf"{result.rating} dB  ({_t(r'$\Sigma$ unfav.', language)} = "
            rf"{format_number(result.unfavourable_sum, language, decimals=1)} dB)"
        ),
        ylabel=_t(_IMPACT_LEVEL_LABEL, language),
        ax=ax,
        language=language,
        **kwargs,
    )
    _annotate_impact_500(
        ax, band_centers, reference, int(result.rating), language=language
    )
    localize_axes(ax, language)
    return ax


def _require_extended_curve(
    result: ExtendedWeightedRatingResult | ExtendedImpactRatingResult,
) -> None:
    if result.band_centers is None or result.measured is None:
        msg = (
            "This extended rating result carries no band curve to plot (it "
            "was constructed without band_centers/measured data)."
        )
        raise ValueError(msg)


def _plot_extended_rating(
    result: ExtendedWeightedRatingResult | ExtendedImpactRatingResult,
    *,
    impact: bool,
    title: str,
    ylabel: str,
    span_label: str,
    ax: Axes | None,
    language: str,
    **kwargs: Any,
) -> Axes:
    """Shared renderer for the two enlarged-range ISO 717 rating plots."""
    from .._i18n import localize_axes
    from .common import _t as _t_common

    _require_extended_curve(result)
    _require_rating_curve(result.core)
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.band_centers, dtype=np.float64)
    measured = np.asarray(result.measured, dtype=np.float64)
    core_freqs = np.asarray(result.core.band_centers, dtype=np.float64)
    core_measured = np.asarray(result.core.measured, dtype=np.float64)
    core_ref = np.asarray(result.core.shifted_reference, dtype=np.float64)

    # Mark the bands outside the 100-3150 Hz core as the enlarged range, with
    # an opaque wash that stays visible on a dark page as on a light one.
    enlarged = theme_fill(_C_MUTED, ax)
    if float(freqs.min()) < float(core_freqs.min()):
        ax.axvspan(
            float(freqs.min()),
            float(core_freqs.min()),
            color=enlarged,
            lw=0,
            zorder=0,
            label=_t(span_label, language),
        )
    if float(freqs.max()) > float(core_freqs.max()):
        label = (
            None
            if float(freqs.min()) < float(core_freqs.min())
            else _t(span_label, language)
        )
        ax.axvspan(
            float(core_freqs.max()),
            float(freqs.max()),
            color=enlarged,
            lw=0,
            zorder=0,
            label=label,
        )

    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("Measured", language))
    ax.plot(freqs, measured, "o-", **kwargs)
    ax.plot(
        core_freqs,
        core_ref,
        "s--",
        color=_C_REFERENCE,
        label=_t("Shifted reference (core bands)", language),
    )
    unfavourable = core_measured > core_ref if impact else core_measured < core_ref
    ax.fill_between(
        core_freqs,
        core_measured,
        core_ref,
        where=unfavourable.tolist(),
        color=_C_SECONDARY,
        alpha=0.4,
        label=_t_common("Unfavourable deviations", language),
        interpolate=True,
    )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def _extended_terms_line(
    terms: list[tuple[str, float | None]], language: str, decimals: int
) -> str:
    """Format the available Annex B adaptation terms as ``name = value dB``."""
    from .._i18n import format_number

    parts = [
        f"{name} = {format_number(value, language, decimals=decimals)}"
        for name, value in terms
        if value is not None
    ]
    return "; ".join(parts)


def plot_extended_weighted_rating(
    result: ExtendedWeightedRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Enlarged-range airborne rating curve vs shifted reference (ISO 717-1 Annex B).

    :param result: An
        :class:`~phonometry.building.measurement.insulation.ExtendedWeightedRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number

    decimals = 0 if float(result.rating).is_integer() else 1
    title = (
        rf"ISO 717-1 $R_\mathrm{{w}}$ "
        rf"($C$={format_number(result.c, language, decimals=decimals)}; "
        rf"$C_\mathrm{{tr}}$="
        rf"{format_number(result.ctr, language, decimals=decimals)}) = "
        rf"{format_number(result.rating, language, decimals=decimals)} dB"
    )
    extended = _extended_terms_line(
        [
            # U+2010 HYPHEN, not an ASCII one: inside mathematics a hyphen is
            # the binary minus, and mathtext would space the range like a
            # subtraction ("50 − 3150").
            ("$C_{50‐3150}$", result.c_50_3150),
            ("$C_{50‐5000}$", result.c_50_5000),
            ("$C_{100‐5000}$", result.c_100_5000),
            (r"$C_{\mathrm{tr},50‐3150}$", result.ctr_50_3150),
            (r"$C_{\mathrm{tr},50‐5000}$", result.ctr_50_5000),
            (r"$C_{\mathrm{tr},100‐5000}$", result.ctr_100_5000),
        ],
        language,
        decimals,
    )
    if extended:
        title = f"{title}\n{extended}"
    return _plot_extended_rating(
        result,
        impact=False,
        title=title,
        ylabel=_t(_REDUCTION_INDEX_LABEL, language),
        span_label="enlarged range (Annex B)",
        ax=ax,
        language=language,
        **kwargs,
    )


def plot_extended_impact_rating(
    result: ExtendedImpactRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Enlarged-range impact rating curve vs shifted reference (ISO 717-2 A.2.1).

    :param result: An
        :class:`~phonometry.building.measurement.insulation.ExtendedImpactRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number

    decimals = 0 if float(result.rating).is_integer() else 1
    title = (
        rf"ISO 717-2 {_t('impact rating', language)} "
        rf"($C_\mathrm{{I}}$="
        rf"{format_number(result.ci, language, decimals=decimals)}) = "
        rf"{format_number(result.rating, language, decimals=decimals)} dB"
    )
    if result.ci_50_2500 is not None:
        title = (
            f"{title}\n"
            # U+2010 HYPHEN: a range, not the binary minus (see Annex B above).
            rf"$C_{{\mathrm{{I}},50‐2500}}$ = "
            rf"{format_number(result.ci_50_2500, language, decimals=decimals)}"
        )
    return _plot_extended_rating(
        result,
        impact=True,
        title=title,
        ylabel=_t(_IMPACT_LEVEL_LABEL, language),
        span_label="enlarged range (A.2.1)",
        ax=ax,
        language=language,
        **kwargs,
    )


def plot_facade_insulation(
    result: FacadeInsulationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band façade sound-insulation profile (ISO 16283-3).

    Draws the standardized level difference ``D2m,nT`` first, then the
    other available quantities (``D2m``, ``D2m,n``, ``R'``) against
    frequency. Works for
    :class:`~phonometry.building.measurement.insulation.FacadeInsulationResult`.

    :param result: A façade result exposing ``d_2m``, ``d_2m_nt``,
        ``d_2m_n``, ``r_prime`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary ``D2m,nT`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    dnt = np.asarray(result.d_2m_nt, dtype=np.float64)
    n = dnt.size
    x = _facade_x_axis(ax, getattr(result, "frequencies", None), n, language=language)

    # D2m,nT first so it is lines[0]; other quantities follow when present.
    curves = [("$D_{2m,nT}$", dnt)]
    curves.append(("$D_{2m}$", np.asarray(result.d_2m, dtype=np.float64)))
    if result.d_2m_n is not None:
        curves.append(("$D_{2m,n}$", np.asarray(result.d_2m_n, dtype=np.float64)))
    if result.r_prime is not None:
        curves.append((_R_PRIME, np.asarray(result.r_prime, dtype=np.float64)))
    # Forward user kwargs to the primary D2m,nT curve only, so styling kwargs
    # (label=, color=) neither collide with the per-curve labels nor make the
    # companion curves indistinguishable.
    for index, (label, y) in enumerate(curves):
        opts: dict[str, Any] = {"label": label}
        if index == 0:
            opts.update(kwargs)
        ax.plot(x, y, "o-", **opts)

    ax.set_ylabel(_t(_LEVEL_DIFFERENCE_LABEL, language))
    ax.set_title(_t("Façade sound insulation (ISO 16283-3)", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_facade_prediction(
    result: FacadePredictionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Predicted façade insulation profile (EN 12354-3:2000).

    Draws the per-element partial indices ``Rp = -10 log10 τ`` as thin dashed
    lines, then the façade apparent reduction ``R'`` and the standardized
    level difference ``D2m,nT`` as bold curves, against frequency. Works for
    :class:`~phonometry.building.prediction.facade.FacadePredictionResult`.

    :param result: A façade prediction result exposing ``r_prime``,
        ``d_2m_nt``, ``element_r`` and (optionally) ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary ``R'`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    r_prime = np.asarray(result.r_prime, dtype=np.float64)
    n = r_prime.size
    x = _facade_x_axis(ax, result.frequencies, n, language=language)

    for name, rp in result.element_r.items():
        ax.plot(
            x, np.asarray(rp, dtype=np.float64), "--", lw=0.9, alpha=0.6, label=name
        )

    opts: dict[str, Any] = {"label": _R_PRIME, "color": "black", "lw": 2.0}
    opts.update(kwargs)
    ax.plot(x, r_prime, "o-", **opts)
    ax.plot(
        x,
        np.asarray(result.d_2m_nt, dtype=np.float64),
        "s-",
        color="tab:blue",
        lw=2.0,
        label="$D_{2m,nT}$",
    )

    ax.set_ylabel(_t("Reduction index / level difference [dB]", language))
    ax.set_title(_t("Façade insulation prediction (EN 12354-3)", language))
    ax.legend(loc="best", fontsize="small", ncol=2)
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_radiated_power(
    result: RadiatedPowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Radiated sound power level ``LW`` per band (EN 12354-4:2000).

    Draws the segment radiated power level as bars, annotating the A-weighted
    single number when available. Works for
    :class:`~phonometry.building.prediction.facade.RadiatedPowerResult`.

    :param result: A :class:`~phonometry.building.prediction.facade.RadiatedPowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``bar`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    l_w = np.asarray(result.l_w, dtype=np.float64)
    n = l_w.size
    positions = np.arange(n, dtype=np.float64)
    if result.frequencies is None:
        labels = [f"{_t('Band', language)} {i + 1}" for i in range(n)]
    else:
        labels = [
            _format_freq(f, language=language)
            for f in np.asarray(result.frequencies, dtype=np.float64)
        ]

    opts: dict[str, Any] = {"color": "tab:red", "alpha": 0.8, "label": "$L_W$"}
    opts.update(kwargs)
    ax.bar(positions, l_w, **opts)
    _band_axis(ax, labels, xlabel=_t(_FREQ_LABEL, language), language=language)

    if result.l_w_dba is not None:
        ax.axhline(
            result.l_w_dba,
            color="black",
            ls="--",
            lw=1.2,
            label=f"$L_{{W\\mathrm{{A}}}}$ = {format_number(result.l_w_dba, language, decimals=1)} dB(A)",
        )
    ax.set_ylabel(_t("Radiated sound power level [dB]", language))
    ax.set_title(_t("Radiated sound power (EN 12354-4)", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_vibration_reduction(
    result: VibrationReductionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Vibration reduction index ``Kij`` versus frequency (ISO 10848).

    Draws the per-band ``Kij`` and, when available, a dashed line at the
    single-number mean ``K̄ij`` (200-1250 Hz, Annex A). Falls back to a
    band-index axis when the result carries no frequencies.

    :param result: A
        :class:`~phonometry.building.measurement.flanking_transmission.VibrationReductionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``Kij`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    k_ij = np.asarray(result.k_ij, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", "$K_{ij}$")
    if result.frequencies is not None:
        freqs = np.asarray(result.frequencies, dtype=np.float64)
        ax.plot(freqs, k_ij, **kwargs)
        _freq_axis(ax, freqs, language=language)
    else:
        ax.plot(np.arange(k_ij.size), k_ij, **kwargs)
        ax.set_xlabel(_t(_BAND_INDEX_LABEL, language))
    if result.single_number is not None:
        ax.axhline(
            result.single_number,
            color=_C_REFERENCE,
            ls="--",
            lw=1.0,
            label=rf"$\overline{{K}}_{{ij}}$ = {format_number(result.single_number, language, decimals=1)} dB",
        )
    ax.set_ylabel(_t("Vibration reduction index $K_{ij}$ [dB]", language))
    ax.set_title(_t("Vibration reduction index (ISO 10848)", language))
    ax.grid(visible=True, alpha=0.3)
    ax.legend()
    localize_axes(ax, language)
    return ax


def plot_structure_borne_power(
    result: StructureBornePowerResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Characteristic structure-borne sound power level per band (EN 15657).

    :param result: A :class:`~phonometry.building.measurement.structure_borne_power.StructureBornePowerResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the bar ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = _plot_band_level_bars(
        ax,
        result.power_level,
        result.frequencies,
        result.total_level,
        ylabel=_t(
            r"Structure-borne power level $L_{W\mathrm{s}}$ [dB re 1 pW]", language
        ),
        title=_t("EN 15657 characteristic structure-borne sound power", language),
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_installed_structure_borne(
    result: InstalledSourceResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-path and total normalised structure-borne SPL (EN 12354-5).

    :param result: An :class:`~phonometry.building.prediction.installed_structure_borne.InstalledSourceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the total-level ``plot``.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    paths = np.atleast_2d(np.asarray(result.path_levels, dtype=np.float64))
    total = np.atleast_1d(np.asarray(result.total_level, dtype=np.float64))
    n_bands = total.size
    if result.frequencies is not None:
        x = np.asarray(result.frequencies, dtype=np.float64)
        ax.set_xscale("log")
        ax.set_xlabel(_t(_FREQ_LABEL, language))
    else:
        x = np.arange(1, n_bands + 1, dtype=np.float64)
        ax.set_xlabel(_t("Band", language))
    for k, path in enumerate(paths):
        ax.plot(
            x,
            path,
            color=_C_MUTED,
            lw=1.0,
            ls=":",
            marker=".",
            label=_t("paths", language) if k == 0 else None,
        )
    style_default(kwargs, "color", _C_PRIMARY)
    style_default(kwargs, "lw", 2.2)
    kwargs.setdefault("label", _t(r"total $L_\mathrm{n,s}$", language))
    ax.plot(x, total, **kwargs)
    ax.set_ylabel(_t(r"Normalised SPL $L_\mathrm{n,s}$ [dB]", language))
    ax.set_title(_t("EN 12354-5 installed structure-borne sound", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, which="both", alpha=0.3)
    if result.frequencies is not None:
        format_frequency_axis(ax, float(x.min()), float(x.max()), language=language)
    localize_axes(ax, language)
    return ax


def plot_airborne_prediction(
    result: AirbornePredictionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-path shares of the transmitted energy (EN 12354-1).

    One bar per transmission path (direct plus flanking), sorted by its
    share of the total transmitted sound energy, largest first.

    :param result: An
        :class:`~phonometry.building.prediction.simplified_model.AirbornePredictionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the path :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    contribs = sorted(result.paths, key=lambda c: c.fraction, reverse=True)
    shares = [100.0 * c.fraction for c in contribs]
    positions = np.arange(len(shares), dtype=np.float64)
    style_default(
        kwargs, "color", [_C_PRIMARY if c.kind == "Dd" else _C_MUTED for c in contribs]
    )
    ax.bar(positions, shares, **kwargs)
    ax.set_xticks(positions)
    ax.set_xticklabels([c.label for c in contribs], rotation=45, ha="right")
    ax.set_xlabel(_t("Transmission path", language))
    ax.set_ylabel(_t(_SHARE_LABEL, language))
    ax.set_title(
        rf"EN 12354-1 {_t('flanking prediction', language)}: "
        rf"$R^{{\prime}}_\mathrm{{w}}$ = "
        rf"{format_number(result.r_prime_w, language, decimals=1)} dB "
        rf"($R_\mathrm{{Dd,w}}$ = "
        rf"{format_number(result.r_direct_w, language, decimals=1)} dB)"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_impact_prediction(
    result: ImpactPredictionResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Terms of the apparent impact-level prediction (EN 12354-2).

    Bars for the Formula 21 terms (the bare-floor equivalent level, the
    covering improvement, the flanking correction) and the resulting
    apparent level ``L'n,w = Ln,w,eq - DLw + K``.

    :param result: An
        :class:`~phonometry.building.prediction.simplified_model.ImpactPredictionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the term :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    labels = (
        r"$L_\mathrm{n,w,eq}$",
        r"$-\Delta L_\mathrm{w}$",
        "$+K$",
        r"$L^{\prime}_\mathrm{n,w}$",
    )
    values = (
        result.ln_w_eq,
        -result.delta_l_w,
        result.k_correction,
        result.l_prime_n_w,
    )
    positions = np.arange(len(values), dtype=np.float64)
    style_default(kwargs, "color", [_C_MUTED, _C_TERTIARY, _C_SECONDARY, _C_PRIMARY])
    ax.bar(positions, values, **kwargs)
    ax.axhline(0.0, color=_C_MUTED, lw=0.8)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel(_t("Level / correction [dB]", language))
    ax.set_title(
        rf"EN 12354-2 {_t('impact prediction', language)}: "
        rf"$L^{{\prime}}_\mathrm{{n,w}}$ = "
        rf"{format_number(result.l_prime_n_w, language, decimals=1)} dB"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


#: Maximum number of individually coloured paths in the detailed-prediction
#: stacked bars; the remaining ones are pooled into a single "other paths" bar.
_MAX_NAMED_PATHS = 6


def _plot_path_shares(
    result: DetailedAirborneResult | DetailedImpactResult,
    total: np.ndarray,
    *,
    total_label: str,
    ylabel: str,
    title: str,
    ax: Axes | None,
    language: str,
    **kwargs: Any,
) -> Axes:
    """Stacked per-band path shares with the resulting total on a twin axis.

    Shared body of the two detailed-model renderers (EN/ISO 12354-1 airborne
    and -2 impact): one stacked bar per band showing which transmission path
    carries the energy, plus the resulting apparent quantity on a right-hand
    axis. The paths are ordered by their *largest* per-band share, so every
    path that dominates a band is named, and any beyond
    :data:`_MAX_NAMED_PATHS` are pooled.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    fractions = np.atleast_2d(np.asarray(result.fractions, dtype=np.float64))
    labels = [p.label for p in result.paths]
    order = list(np.argsort(-fractions.max(axis=1)))
    named = order[:_MAX_NAMED_PATHS]
    pooled = order[_MAX_NAMED_PATHS:]

    positions = _band_axis(ax, np.asarray(result.frequencies), language=language)
    palette = (
        _C_PRIMARY,
        _C_SECONDARY,
        _C_TERTIARY,
        _C_QUATERNARY,
        _C_PRIMARY_LIGHT,
        _C_SECONDARY_LIGHT,
    )
    bottom = np.zeros(positions.size, dtype=np.float64)
    for colour, k in zip(palette, named, strict=False):  # fewer paths than colours
        share = 100.0 * fractions[k]
        # A copy per bar, not one `setdefault` before the loop: this renderer
        # draws one bar per transmission path and each carries its own name,
        # so a single default would put the first path's label on all of them.
        path_kwargs = dict(kwargs)
        path_kwargs.setdefault("label", labels[k])
        ax.bar(
            positions,
            share,
            bottom=bottom,
            width=0.85,
            color=colour,
            edgecolor="none",
            zorder=0,
            **path_kwargs,
        )
        bottom = bottom + share
    if pooled:
        share = 100.0 * fractions[pooled].sum(axis=0)
        pooled_kwargs = dict(kwargs)
        pooled_kwargs.setdefault("label", _t("other paths", language))
        ax.bar(
            positions,
            share,
            bottom=bottom,
            width=0.85,
            color=_C_MUTED,
            edgecolor="none",
            zorder=0,
            **pooled_kwargs,
        )
    ax.set_ylabel(_t(_SHARE_LABEL, language))
    ax.set_ylim(0.0, 100.0)
    ax.set_title(title)

    twin = ax.twinx()
    twin.plot(
        positions,
        np.asarray(total, dtype=np.float64),
        color=_C_REFERENCE,
        lw=2.0,
        marker="o",
        ms=4,
        label=total_label,
        zorder=3,
    )
    twin.set_ylabel(_t(ylabel, language))
    handles, texts = ax.get_legend_handles_labels()
    extra_handles, extra_texts = twin.get_legend_handles_labels()
    legend = ax.legend(
        handles + extra_handles,
        texts + extra_texts,
        fontsize="small",
        ncol=2,
    )
    place_legend_clear(legend, twin)
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    localize_axes(twin, language)
    return ax


def plot_detailed_airborne_prediction(
    result: DetailedAirborneResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band path contributions and ``R'`` (EN/ISO 12354-1 detailed model).

    :param result: A
        :class:`~phonometry.building.prediction.detailed_model.DetailedAirborneResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the stacked :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number

    title = f"EN 12354-1 {_t('detailed prediction', language)}"
    if result.rating is not None:
        title += (
            rf": $R^{{\prime}}_\mathrm{{w}}$ = "
            rf"{format_number(result.rating.rating, language, decimals=0)} dB"
        )
    return _plot_path_shares(
        result,
        result.r_prime,
        total_label=_R_PRIME,
        ylabel=_REDUCTION_INDEX_LABEL,
        title=title,
        ax=ax,
        language=language,
        **kwargs,
    )


def plot_detailed_impact_prediction(
    result: DetailedImpactResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band path contributions and ``L'n`` (EN/ISO 12354-2 detailed model).

    :param result: A
        :class:`~phonometry.building.prediction.detailed_model.DetailedImpactResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the stacked :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    from .._i18n import format_number

    title = f"EN 12354-2 {_t('detailed prediction', language)}"
    if result.rating is not None:
        title += (
            rf": $L^{{\prime}}_\mathrm{{n,w}}$ = "
            rf"{format_number(result.rating.rating, language, decimals=0)} dB"
        )
    return _plot_path_shares(
        result,
        result.l_prime_n,
        total_label=r"$L^{\prime}_\mathrm{n}$",
        ylabel=_IMPACT_LEVEL_LABEL,
        title=title,
        ax=ax,
        language=language,
        **kwargs,
    )


def plot_in_situ_element(
    result: InSituElementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """In-situ ``Rsitu`` and ``Ln,situ`` of one element (EN/ISO 12354).

    :param result: An
        :class:`~phonometry.building.prediction.detailed_model.InSituElementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``Rsitu`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 4)
    kwargs.setdefault("label", r"$R_\mathrm{situ}$")
    ax.plot(freqs, result.sound_reduction_index, **kwargs)
    ax.plot(
        freqs,
        result.impact_level,
        color=_C_SECONDARY,
        marker="s",
        ms=4,
        label=r"$L_\mathrm{n,situ}$",
    )
    ax.set_xscale("log")
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Reduction index / impact level [dB]", language))
    ax.set_title(
        f"{_t('In-situ element performance (ISO 12354)', language)}: {result.label}"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()), language=language)
    localize_axes(ax, language)
    return ax


def plot_airborne_insulation(
    result: AirborneInsulationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band airborne insulation quantities (ISO 16283-1).

    Draws the standardized level difference ``DnT`` first (the primary
    curve), then the level difference ``D`` and, when available, the
    apparent sound reduction index ``R'``.

    :param result: An :class:`~phonometry.building.measurement.insulation.AirborneInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary ``DnT`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    curves = [
        ("$D_\\mathrm{nT}$", np.asarray(result.dnt, dtype=np.float64)),
        ("$D$", np.asarray(result.d, dtype=np.float64)),
    ]
    if result.r_prime is not None:
        curves.append((_R_PRIME, np.asarray(result.r_prime, dtype=np.float64)))
    ax = _plot_insulation_bands(
        curves,
        ylabel=_t(_LEVEL_DIFFERENCE_LABEL, language),
        title=_t("Airborne sound insulation (ISO 16283-1)", language),
        ax=ax,
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_impact_insulation(
    result: ImpactInsulationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Per-band impact sound pressure levels (ISO 16283-2).

    Draws the standardized level ``L'nT`` first (the primary curve) and,
    when available, the normalized level ``L'n``.

    :param result: An :class:`~phonometry.building.measurement.insulation.ImpactInsulationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary ``L'nT`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    curves = [(r"$L^{\prime}_\mathrm{nT}$", np.asarray(result.l_n_t, dtype=np.float64))]
    if result.l_n is not None:
        curves.append(
            (r"$L^{\prime}_\mathrm{n}$", np.asarray(result.l_n, dtype=np.float64))
        )
    ax = _plot_insulation_bands(
        curves,
        ylabel=_t(_IMPACT_LEVEL_LABEL, language),
        title=_t("Impact sound insulation (ISO 16283-2)", language),
        ax=ax,
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_low_frequency_procedure(
    result: LowFrequencyResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The three low-frequency bands of ISO 16283, default against corner.

    Draws the combined low-frequency level :math:`L_\mathrm{LF}` first (the
    reported quantity), then the two levels it was built from: the
    default-procedure level ``L`` and the corner level
    :math:`L_\mathrm{Corner}`. Only the 50 Hz, 63 Hz and 80 Hz bands are
    drawn, because they are the only ones the procedure touches.

    :param result: A
        :class:`~phonometry.building.measurement.low_frequency.LowFrequencyResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the primary :math:`L_\mathrm{LF}` curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    bands = np.asarray(result.low_frequency_bands, dtype=np.float64)
    x = _facade_x_axis(ax, bands, bands.size, language=language)
    curves = (
        (r"$L_\mathrm{LF}$", np.asarray(result.l_lf, dtype=np.float64)),
        (r"$L$", np.asarray(result.l_default, dtype=np.float64)),
        (r"$L_\mathrm{Corner}$", np.asarray(result.l_corner, dtype=np.float64)),
    )
    # User kwargs style the reported L_LF curve only, the way every other
    # building renderer forwards them to its primary curve.
    for index, (label, y) in enumerate(curves):
        opts: dict[str, Any] = {"label": label}
        if index == 0:
            opts.update(kwargs)
        ax.plot(x, y, "o-", **opts)
    ax.set_ylabel(_t(_SPL_LABEL, language))
    ax.set_title(_t(_LOW_FREQUENCY_TITLE, language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_band_uncertainty(
    result: BandUncertainty, ax: Axes | None = None, language: str = "en", **kwargs: Any
) -> Axes:
    """Per-band standard uncertainty of an insulation quantity (ISO 12999-1).

    :param result: A
        :class:`~phonometry.building.measurement.uncertainty.BandUncertainty`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the uncertainty curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs, u = result.to_arrays()
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freqs, u, **kwargs)
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t("Standard uncertainty $u$ [dB]", language))
    ax.set_ylim(bottom=0.0)
    quantity = (
        _t(r"$\sigma_\mathrm{R95}$ upper limit", language)
        if result.upper_limit
        else "$u$"
    )
    ax.set_title(
        f"ISO 12999-1 {_t('band uncertainty', language)} ({quantity}): "
        f"{result.measurand}, {_t('situation', language)} {result.situation}"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    localize_axes(ax, language)
    return ax


def _plot_improvement(
    ax: Axes,
    freqs: np.ndarray,
    dl: np.ndarray,
    limited: np.ndarray | None,
    title: str,
    language: str,
    kwargs: dict[str, Any],
) -> Axes:
    """The improvement spectrum ``ΔL`` against frequency, titled *title*.

    Shared by the ISO 16251-1 result and the ISO 717-2 rating of a covering:
    the curve, the bands at the limit of measurement when a mask is given,
    the frequency axis and the legend.
    """
    from .._i18n import localize_axes

    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.plot(freqs, dl, **kwargs)
    # Mark bands at the limit of measurement (reported as > delta-L).
    if limited is not None and limited.size and bool(np.any(limited)):
        ax.plot(
            freqs[limited],
            dl[limited],
            ls="",
            marker="v",
            color=_C_SECONDARY,
            ms=9,
            mfc="none",
            mew=1.6,
            zorder=5,
            label=_t(r"limit of measurement (> $\Delta L$)", language),
        )
    _freq_axis(ax, freqs, language=language)
    ax.set_ylabel(_t(_IMPROVEMENT_LABEL, language))
    # The axis starts at 0 dB only when no band is below it: a floating
    # floor's mass-spring resonance makes the covering worsen the floor in
    # its low bands, and those negative bands are the ones CI,Δ answers to.
    finite = dl[np.isfinite(dl)]
    if not finite.size or bool(np.all(finite >= 0.0)):
        ax.set_ylim(bottom=0.0)
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend()
    localize_axes(ax, language)
    return ax


def plot_floor_covering_improvement(
    result: FloorCoveringImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Impact-sound improvement spectrum ΔL of a floor covering (ISO 16251-1).

    :param result: A
        :class:`~phonometry.building.measurement.floor_covering_improvement.FloorCoveringImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma

    title = _t("ISO 16251-1 Floor-Covering Impact Sound Improvement", language)
    if result.delta_lw is not None:
        title += (
            r"  ($\Delta L_\mathrm{w}$ = "
            f"{decimal_comma(str(result.delta_lw), language)} dB)"
        )
    return _plot_improvement(
        ax if ax is not None else _new_axes(),
        result.frequencies,
        result.improvement,
        result.limited,
        title,
        language,
        kwargs,
    )


def plot_impact_improvement_rating(
    result: ImpactImprovementRatingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    r"""The improvement spectrum ΔL a covering is rated from (ISO 717-2).

    The title gives the rating in the form of the other ISO 717 renderers,
    the symbols carrying the names: :math:`\Delta L_\mathrm{w}` with
    :math:`C_{\mathrm{I},\Delta}` and :math:`C_\mathrm{I,r}` in parentheses.

    :param result: A
        :class:`~phonometry.building.measurement.ratings.ImpactImprovementRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number

    title = (
        # Sign only when negative, the style of ISO 717-2's own examples.
        r"ISO 717-2 $\Delta L_\mathrm{w}$ "
        rf"($C_{{\mathrm{{I}},\Delta}}$={format_number(result.ci_delta, language, decimals=0)}; "
        rf"$C_\mathrm{{I,r}}$={format_number(result.ci_r, language, decimals=0)}) = "
        rf"{format_number(result.delta_lw, language, decimals=0)} dB"
    )
    return _plot_improvement(
        ax if ax is not None else _new_axes(),
        result.band_centers,
        result.improvement,
        None,
        title,
        language,
        kwargs,
    )


#: Localised names of the DB-HR normalised source spectra.
_DB_HR_SPECTRUM_LABELS = {
    "pink": "pink noise",
    "traffic": "road traffic",
    "railway": "railway",
    "aircraft": "aircraft",
}


def plot_db_hr_global_index(
    result: DbHrGlobalIndexResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Band insulation and per-band transmitted level of a DB-HR global index.

    The band insulation ``X_i`` is drawn as bars and the weighted per-band
    transmitted level ``L_x,i - X_i`` as a line: the global index is minus the
    energy sum of that line, so the bands where it peaks are the ones that set
    the index.

    :param result: A
        :class:`~phonometry.building.regulation.spain.DbHrGlobalIndexResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the band-insulation ``bar`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    values = np.asarray(result.band_values, dtype=np.float64)
    contributions = np.asarray(result.band_contributions, dtype=np.float64)
    positions = _band_axis(ax, freqs, language=language)

    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("alpha", 0.85)
    kwargs.setdefault("label", _t("band insulation", language))
    ax.bar(positions, values, width=0.72, **kwargs)
    ax.set_ylabel(_t("Band insulation $X_i$ [dB]", language))

    # The two quantities live on disjoint ranges (a positive insulation of
    # tens of dB against a negative weighted level), so the transmitted level
    # goes on its own axis; the bands where it peaks are the ones that set the
    # index, which is minus the energy sum of that curve.
    twin = ax.twinx()
    twin.plot(
        positions,
        contributions,
        "o-",
        color=_C_SECONDARY,
        ms=4.0,
        label=_t("transmitted level $L_{x,i} - X_i$", language),
    )
    twin.set_ylabel(_t("Transmitted level [dBA]", language))

    spectrum = _t(_DB_HR_SPECTRUM_LABELS[result.spectrum], language)
    ax.set_title(
        f"{_t('CTE DB-HR global index', language)}: {result.name} = "
        f"{format_number(result.value, language, decimals=1)} dBA ({spectrum})"
    )
    handles, labels = ax.get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    ax.legend(
        handles + extra_handles,
        labels + extra_labels,
        loc=_LEGEND_UPPER_LEFT,
        fontsize="small",
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    localize_axes(twin, language)
    return ax


def plot_db_hr_assessment(
    result: DbHrAssessment, ax: Axes | None = None, language: str = "en", **kwargs: Any
) -> Axes:
    """Achieved values against their CTE DB-HR requirements.

    Each check is a horizontal lollipop from its requirement to the achieved
    value: a stem reaching to the right of the requirement marker means a
    compliant "at least" requirement, and the exceedance colour marks a check
    that is not met.

    :param result: A
        :class:`~phonometry.building.regulation.spain.DbHrAssessment`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the achieved-value ``scatter`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    checks = list(result.checks)
    rows = np.arange(len(checks), dtype=np.float64)
    achieved = np.array([c.reported for c in checks], dtype=np.float64)
    limits = np.array([c.requirement.limit for c in checks], dtype=np.float64)
    colours = [_C_TERTIARY if c.complies else _C_REFERENCE for c in checks]

    ax.hlines(rows, limits, achieved, colors=colours, linewidth=2.0)
    ax.scatter(
        limits,
        rows,
        marker="|",
        s=220,
        color=_C_MUTED,
        label=_t("required", language),
        zorder=4,
    )
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("s", 55)
    kwargs.setdefault("label", _t("achieved", language))
    ax.scatter(achieved, rows, color=colours, zorder=5, **kwargs)

    ax.set_yticks(rows)
    ax.set_yticklabels(
        [f"{c.requirement.quantity} ({c.requirement.unit})" for c in checks]
    )
    ax.invert_yaxis()
    ax.set_xlabel(_t("Value", language))
    ax.set_title(_t("CTE DB-HR requirement check", language))
    ax.legend(loc="best", fontsize="small")
    ax.grid(visible=True, axis="x", alpha=0.3)
    localize_axes(ax, language)
    return ax


def _plot_shaded_band_pair(
    ax: Axes | None,
    frequencies: np.ndarray | None,
    reference: np.ndarray,
    curve: np.ndarray,
    *,
    reference_label: str,
    curve_label: str,
    fill_label: str,
    ylabel: str,
    title: str,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Two band curves on a categorical axis with the gap between them shaded.

    Shared by the heavy-impact standardization figure (measured against
    standardized level) and the ceiling/plenum figure (the two ceilings against
    the path they form): both draw a dashed reference, a solid main curve and
    the difference as a filled band, on band positions labelled either with the
    centre frequencies or with a plain band index when none were supplied.
    """
    ax = ax if ax is not None else _new_axes()
    labels = frequencies if frequencies is not None else np.arange(curve.size) + 1.0
    positions = _band_axis(
        ax,
        labels,
        # Translated here: "Band index" is this module's string, and the
        # table _band_axis translates its label with does not hold it.
        xlabel=_t(
            _FREQ_LABEL if frequencies is not None else _BAND_INDEX_LABEL, language
        ),
        language=language,
    )
    ax.plot(
        positions,
        reference,
        "s--",
        color=_C_REFERENCE,
        lw=1.2,
        label=_t(reference_label, language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", _t(curve_label, language))
    ax.plot(positions, curve, "-", **kwargs)
    ax.fill_between(
        positions,
        reference,
        curve,
        color=theme_fill(_C_SECONDARY, ax),
        lw=0,
        zorder=0,
        label=_t(fill_label, language),
    )
    ax.set_ylabel(_t(ylabel, language))
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    return ax


def plot_heavy_impact_source(
    result: HeavyImpactSourceCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Measured heavy-impact source ``LFE`` against its printed tolerance band.

    :param result: A
        :class:`~phonometry.building.measurement.heavy_impact.HeavyImpactSourceCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies, language=language)
    lower = result.nominal - result.tolerance
    upper = result.nominal + result.tolerance
    ax.fill_between(
        positions,
        lower,
        upper,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=_t("tolerance band", language),
    )
    ax.plot(
        positions,
        result.nominal,
        "s--",
        color=_C_REFERENCE,
        lw=1.2,
        label=_t("nominal $L_{FE}$", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", _t("measured $L_{FE}$", language))
    ax.plot(positions, result.measured, "-", **kwargs)
    failing = ~result.within_tolerance
    if bool(np.any(failing)):
        ax.plot(
            positions[failing],
            result.measured[failing],
            ls="",
            marker="X",
            color=_C_SECONDARY,
            ms=11,
            zorder=6,
            label=_t("outside tolerance", language),
        )
    ax.set_ylabel(_t("Impact force exposure level $L_{FE}$ [dB re 1 N]", language))
    verdict = _verdict_word(passes=result.passes, language=language)
    source = _t(_HEAVY_IMPACT_SOURCE_LABELS[result.source], language)
    ax.set_title(
        f"{_t('Heavy impact source conformance', language)}: {source} ({verdict})"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_standardized_maximum_impact(
    result: StandardizedMaximumImpactResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Measured and standardized maximum impact levels (ISO 16283-2 3.16).

    :param result: A
        :class:`~phonometry.building.measurement.heavy_impact.StandardizedMaximumImpactResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the standardized-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = _plot_shaded_band_pair(
        ax,
        result.frequencies,
        result.measured,
        result.standardized,
        reference_label=r"$L_\mathrm{i,Fmax}$ (measured)",
        curve_label=r"$L^{\prime}_{\mathrm{i,Fmax},V,T}$ (standardized)",
        fill_label="standardization correction",
        ylabel=_MAX_IMPACT_LABEL,
        title=(
            f"{_t('ISO 16283-2 rubber-ball standardization', language)} "
            f"($V$ = {format_number(result.volume, language, decimals=1)} m³)"
        ),
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_a_weighted_maximum_impact(
    result: AWeightedMaximumImpactResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """A-weighted maximum impact level and its band contributions (ISO 717-2 D).

    :param result: An
        :class:`~phonometry.building.measurement.heavy_impact.AWeightedMaximumImpactResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``bar`` call for the corrected values.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies, language=language)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("A-weighted contribution", language))
    ax.bar(positions, result.corrected, width=0.7, zorder=2, **kwargs)
    ax.plot(
        positions,
        result.levels,
        "s--",
        color=_C_REFERENCE,
        lw=1.2,
        zorder=3,
        label=_t(r"$X_\mathrm{i,Fmax}$ (unweighted)", language),
    )
    ax.axhline(
        result.rating,
        color=_C_SECONDARY,
        ls="-",
        lw=1.6,
        zorder=4,
        label=rf"$X_\mathrm{{iA,Fmax}}$ = {result.rating} dB",
    )
    ax.set_ylabel(_t(_MAX_IMPACT_LABEL, language))
    ax.set_title(
        f"{_t('ISO 717-2 Annex D heavy-impact rating', language)} "
        f"({_t(_HEAVY_IMPACT_BAND_LABELS[result.band], language)}, "
        f"{format_number(result.unrounded, language, decimals=2)} dB)"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_ceiling_attenuation(
    result: CeilingAttenuationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Normalized ceiling attenuation against the fitted ASTM E413 contour.

    :param result: A
        :class:`~phonometry.building.prediction.ceiling_plenum.CeilingAttenuationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = _plot_rating(
        result.frequencies,
        result.measured,
        result.shifted_reference,
        impact=False,
        title=(
            f"ASTM E413 CAC = {result.rating} dB  "
            rf"({_t(r'$\Sigma$ unfav.', language)} = "
            f"{format_number(result.deficiency_sum, language, decimals=1)} dB)"
        ),
        measured_label="Normalized ceiling attenuation",
        ylabel=_t("Normalized ceiling attenuation $D_\\mathrm{n,c}$ [dB]", language),
        ax=ax,
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_plenum_flanking(
    result: PlenumFlankingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Ceiling/plenum flanking path ``Rcl`` against the two ceilings.

    :param result: A
        :class:`~phonometry.building.prediction.ceiling_plenum.PlenumFlankingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``Rcl`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = _plot_shaded_band_pair(
        ax,
        result.frequencies,
        result.reduction_index_source + result.reduction_index_receiving,
        result.reduction_index,
        reference_label="$R_\\mathrm{S} + R_\\mathrm{R}$ (two ceilings)",
        curve_label=r"$R_\mathrm{cl}$ (ceiling/plenum path)",
        fill_label="plenum penalty",
        ylabel=_R_INDEX_LABEL,
        title=(
            f"{_t('Suspended-ceiling plenum path', language)} "
            f"($h$ = {format_number(result.plenum_height, language, decimals=2)} m, "
            f"$L_\\mathrm{{R}}$ = {format_number(result.ceiling_length, language, decimals=2)} m, "
            f"$\\varepsilon$ = {result.epsilon:.0f})"
        ),
        language=language,
        **kwargs,
    )
    localize_axes(ax, language)
    return ax


def plot_wall_tie_coupling(
    result: WallTieCouplingResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Wall-tie coupling loss factor against the rigid-connection ceiling.

    :param result: A
        :class:`~phonometry.building.prediction.masonry_cavity_wall.WallTieCouplingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``eta_ij`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freq = np.asarray(result.frequencies, dtype=np.float64)
    ax.loglog(
        freq,
        result.rigid_coupling_loss_factor,
        "--",
        color=_C_REFERENCE,
        lw=1.2,
        label=_t("rigid connection ($Y_\\mathrm{c}$ = 0)", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", _t("resilient tie array", language))
    ax.loglog(freq, result.coupling_loss_factor, **kwargs)
    ax.fill_between(
        freq,
        result.coupling_loss_factor,
        result.rigid_coupling_loss_factor,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=_t("isolation gained by the tie", language),
    )
    format_frequency_axis(ax, float(freq.min()), float(freq.max()), language=language)
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Coupling loss factor $\\eta_{ij}$", language))
    stiffness = (
        ""
        if result.tie_stiffness is None
        else ", $k$ = "
        f"{format_number(result.tie_stiffness / 1e6, language, decimals=1)} MN/m"
    )
    ax.set_title(
        f"{_t('Wall-tie structure-borne coupling', language)} "
        f"({format_number(result.ties_per_area, language, decimals=1)} "
        f"{_t('ties/m²', language)}{stiffness})"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


# --------------------------------------------------------------------------- #
# Resilient-layer prediction (tapping force, coverings, floating floors,
# linings). The two improvement spectra share one drawing helper so the
# reference-slope decoration is written once.
# --------------------------------------------------------------------------- #
def _plot_improvement_spectrum(
    ax: Axes,
    freqs: np.ndarray,
    curves: Sequence[tuple[np.ndarray, str, str, str]],
    marker_frequency: float | None,
    marker_label: str,
    language: str,
    kwargs: dict[str, Any],
) -> None:
    """Draw one or more ``ΔL(f)`` curves with an optional vertical marker."""
    first, *rest = curves
    values, label, colour, style = first
    style_default(kwargs, "color", colour)
    style_default(kwargs, "ls", style)
    # The caller may name the curve; do not hand matplotlib two labels.
    kwargs.setdefault("label", kwargs.pop("label", _t(label, language)))
    ax.plot(freqs, values, **kwargs)
    for values, label, colour, style in rest:
        ax.plot(freqs, values, color=colour, ls=style, label=_t(label, language))
    if marker_frequency is not None:
        ax.axvline(
            marker_frequency,
            color=_C_MUTED,
            ls=":",
            lw=1.2,
            label=f"{_t(marker_label, language)} = {_format_freq(marker_frequency, language=language)} Hz",
        )
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t(_IMPROVEMENT_LABEL, language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()), language=language)


def plot_tapping_force(
    result: TappingForceResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Force spectrum of the ISO tapping machine on one walking surface.

    Draws ``|Fn|(f)`` from the mass-spring-dashpot model with the two
    low-frequency asymptotes ``|Fn|lower`` / ``|Fn|upper`` and the cut-off
    frequency ``fco`` marked.

    :param result: A
        :class:`~phonometry.building.prediction.resilient_layers.TappingForceResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the force-spectrum ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault(
        "label", kwargs.pop("label", _t("force spectrum $|F_n|$", language))
    )
    ax.plot(freqs, result.peak_force, **kwargs)
    ax.axhline(
        result.upper_limit,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=r"$|F_n|_\mathrm{upper}$",
    )
    ax.axhline(
        result.lower_limit,
        color=_C_MUTED,
        ls="--",
        lw=1.2,
        label=r"$|F_n|_\mathrm{lower}$",
    )
    ax.axvline(
        result.cut_off_frequency,
        color=_C_SECONDARY,
        ls=":",
        lw=1.2,
        label=rf"$f_\mathrm{{co}}$ = {_format_freq(result.cut_off_frequency, language=language)} Hz",
    )
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Magnitude of the peak force $|F_n|$ [N]", language))
    ax.set_yscale("log")
    regime = "over-critical" if result.over_critical else "under-critical"
    ax.set_title(
        f"{_t('ISO tapping machine force spectrum', language)} ({_t(regime, language)})"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    format_frequency_axis(ax, float(freqs.min()), float(freqs.max()), language=language)
    localize_axes(ax, language)
    return ax


def plot_covering_improvement(
    result: CoveringImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Predicted ``ΔL`` of a soft floor covering beside its two-line estimate.

    :param result: A
        :class:`~phonometry.building.prediction.resilient_layers.CoveringImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the force-ratio curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    _plot_improvement_spectrum(
        ax,
        freqs,
        [
            (result.improvement, "band force ratio (Eq. 4.114)", _C_PRIMARY, "-"),
            (
                result.two_line,
                "two-line estimate (0 dB, 12 dB/oct)",
                _C_SECONDARY,
                "--",
            ),
        ],
        result.cut_off_frequency,
        r"$f_\mathrm{co}$",
        language,
        kwargs,
    )
    ax.set_title(_t("Soft floor covering improvement (Hopkins 4.4.3.1)", language))
    localize_axes(ax, language)
    return ax


def plot_floating_floor_improvement(
    result: FloatingFloorImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Predicted ``ΔL`` of a floating floor above its mass-spring resonance.

    :param result: A
        :class:`~phonometry.building.prediction.resilient_layers.FloatingFloorImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the improvement curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import decimal_comma, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    label = rf"{result.model} ({result.slope:.0f} log10(f/$f_\mathrm{{o}}$))"
    _plot_improvement_spectrum(
        ax,
        freqs,
        [(result.improvement, label, _C_PRIMARY, "-")],
        result.resonance_frequency,
        r"$f_\mathrm{o}$",
        language,
        kwargs,
    )
    title = _t("Floating floor improvement (ISO 12354-2 Annex C)", language)
    if result.delta_lw is not None:
        value = decimal_comma(f"{result.delta_lw:.1f}", language)
        # ``decimal_comma`` has already localised the value: the dollars below
        # would otherwise stop the save-time comma pass over the whole string.
        title += rf"  ($\Delta L_\mathrm{{w}}$ = {value} dB)"
    ax.set_title(title)
    localize_axes(ax, language)
    return ax


def plot_lining_improvement(
    result: LiningImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Annex D single-number ratings of an additional layer against ``fo``.

    Sweeps the resonance frequency over the Annex D range, draws ``ΔRw``,
    ``ΔRA`` and ``ΔRA,tr`` for this system (the analogue of Figures D.2 and
    D.3) and marks the result's own resonance frequency.

    :param result: A
        :class:`~phonometry.building.prediction.resilient_layers.LiningImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``ΔRw`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes
    from ..building.prediction.resilient_layers import lining_improvement

    ax = ax if ax is not None else _new_axes()
    # The endpoints are written back exactly: np.logspace lands a few ulps
    # below 30 Hz, which is outside the range Annex D is stated for and would
    # make drawing the curve emit an extrapolation warning.
    sweep = np.logspace(np.log10(30.0), np.log10(5000.0), 300)
    sweep[0], sweep[-1] = 30.0, 5000.0
    ratings: list[tuple[float, float, float]] = [
        lining_improvement(
            float(f),
            system=result.system,
            anchors=result.anchors,
            glued_area=result.glued_area,
        ).ratings
        for f in sweep
    ]
    curves = np.asarray(ratings, dtype=np.float64)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("label", kwargs.pop("label", r"$\Delta R_\mathrm{w}$"))
    ax.plot(sweep, curves[:, 0], **kwargs)
    ax.plot(
        sweep, curves[:, 1], color=_C_SECONDARY, ls="--", label=r"$\Delta R_\mathrm{A}$"
    )
    ax.plot(
        sweep,
        curves[:, 2],
        color=_C_TERTIARY,
        ls="-.",
        label=r"$\Delta R_\mathrm{A,tr}$",
    )
    ax.plot(
        [result.resonance_frequency],
        [result.delta_rw],
        marker="o",
        ms=8,
        color=_C_REFERENCE,
        ls="",
        label=rf"$f_\mathrm{{o}}$ = "
        rf"{_format_freq(result.resonance_frequency, language=language)} Hz",
    )
    ax.set_xlabel(_t(_FREQ_LABEL, language))
    ax.set_ylabel(_t("Sound reduction index improvement [dB]", language))
    ax.set_title(
        f"{_t('Additional-layer rating (ISO 12354-1 Annex D)', language)}: "
        f"{result.system}"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    format_frequency_axis(ax, float(sweep.min()), float(sweep.max()), language=language)
    localize_axes(ax, language)
    return ax


def _plot_low_frequency(
    result: LowFrequencyIntensityResult | LowFrequencyElementResult,
    values: np.ndarray,
    *,
    symbol: str,
    title: str,
    ylabel: str,
    ax: Axes | None,
    language: str,
    kwargs: dict[str, Any],
) -> Axes:
    """One band figure for either ISO 15186-3 quantity.

    The index and the element-normalized level difference are read the same
    way, band by band against the Clause 6.4.2 verdict, so they are drawn by
    one renderer and differ only in the symbol on the bars and the title.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    r_i = np.asarray(values, dtype=np.float64)
    # Categorical positions, not a log frequency axis: the standard fixes the
    # band set at three to six bands, and bars over so short a span read
    # better evenly spaced. Without centres the bands are labelled by order.
    band_word = _t("Band", language)
    labels: Sequence[str] | np.ndarray = (
        result.frequencies
        if result.frequencies is not None
        else [f"{band_word} {i + 1}" for i in range(r_i.size)]
    )
    positions = _band_axis(
        ax,
        labels,
        xlabel=_FREQ_LABEL if result.frequencies is not None else "Band",
        language=language,
    )
    qualified = (
        np.ones(r_i.size, dtype=bool)
        if result.qualified is None
        else np.asarray(result.qualified, dtype=bool)
    )

    bar_kwargs = dict(kwargs)
    bar_kwargs.setdefault("label", symbol)
    style_default(bar_kwargs, "color", _C_PRIMARY)
    bar_kwargs.setdefault("edgecolor", "none")
    bar_kwargs.setdefault("zorder", 0)
    ax.bar(positions, r_i, width=_BAR_WIDTH, **bar_kwargs)
    # Hatch on top of the bar rather than recolouring it: the refused bands
    # still carry a computed index, the hatch says it is not qualified.
    if not qualified.all():
        ax.bar(
            positions[~qualified],
            r_i[~qualified],
            width=_BAR_WIDTH,
            facecolor="none",
            edgecolor=_C_REFERENCE,
            hatch="///",
            lw=1.0,
            zorder=1,
            label=_t("not qualified (6.4.2)", language),
        )
    ax.set_ylabel(_t(ylabel, language))
    ax.set_title(_t(title, language))

    handles, texts = ax.get_legend_handles_labels()
    # The indicator only exists where the receiving-side pressure was measured
    # alongside the intensity, so the twin axis is drawn only then.
    twin: Axes | None = None
    if result.surface_pressure_intensity_indicator is not None:
        limit = result.indicator_limit
        twin = ax.twinx()
        twin.plot(
            positions,
            np.asarray(result.surface_pressure_intensity_indicator, dtype=np.float64),
            color=_C_SECONDARY,
            lw=2.0,
            marker="o",
            ms=4,
            label=_F_PI,
            zorder=3,
        )
        twin.axhline(
            limit,
            color=_C_REFERENCE,
            ls="--",
            lw=1.2,
            label=f"{_F_PI} {_t('limit', language)} = {limit:.0f} dB",
            zorder=2,
        )
        twin.set_ylabel(_t(_INDICATOR_LABEL, language))
        extra_handles, extra_texts = twin.get_legend_handles_labels()
        handles += extra_handles
        texts += extra_texts
        localize_axes(twin, language)
    legend = ax.legend(handles, texts, loc="best", fontsize="small")
    if twin is not None:
        place_legend_clear(legend, twin)
    ax.grid(visible=True, axis="y", alpha=0.3)
    localize_axes(ax, language)
    return ax


def plot_low_frequency_intensity(
    result: LowFrequencyIntensityResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Low-frequency intensity sound reduction index (ISO 15186-3).

    Draws ``RI`` per band as bars, hatching any band the Clause 6.4.2 field
    indicator refuses, and overlays the indicator ``FpI`` with its applicable
    limit on a twin axis. Works for
    :class:`~phonometry.building.measurement.intensity_insulation.LowFrequencyIntensityResult`.

    :param result: A low-frequency result exposing ``r_i``,
        ``surface_pressure_intensity_indicator``, ``qualified`` and ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``RI`` bar call.
    :return: The axes.
    """
    return _plot_low_frequency(
        result,
        result.r_i,
        symbol=_R_INTENSITY,
        title=_LOW_FREQUENCY_INTENSITY_TITLE,
        ylabel=_REDUCTION_INDEX_LABEL,
        ax=ax,
        language=language,
        kwargs=kwargs,
    )


def plot_low_frequency_element(
    result: LowFrequencyElementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Low-frequency element normalized level difference (ISO 15186-3).

    The same figure as :func:`plot_low_frequency_intensity` for the
    small-element quantity of Formula (8). Works for
    :class:`~phonometry.building.measurement.intensity_insulation.LowFrequencyElementResult`.

    :param result: An element result exposing ``d_i_n_e``,
        ``surface_pressure_intensity_indicator``, ``qualified`` and ``frequencies``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``DI,n,e`` bar call.
    :return: The axes.
    """
    return _plot_low_frequency(
        result,
        result.d_i_n_e,
        symbol=_D_INTENSITY_ELEMENT,
        title=_LOW_FREQUENCY_ELEMENT_TITLE,
        ylabel=_ELEMENT_DIFFERENCE_LABEL,
        ax=ax,
        language=language,
        kwargs=kwargs,
    )


def _rating_symbol(key: str) -> str:
    """Table 1 notation as mathtext: ``"LA,eq,nT"`` to an upright subscript."""
    return rf"$L_\mathrm{{{key[1:]}}}$"


def _headline_rating(result: ServiceEquipmentResult) -> str | None:
    """The A-weighted single number of the curve the figure draws last."""
    for suffix in (",nT", ""):
        key = f"LA,{result.quantity}{suffix}"
        if key in result.ratings:
            return key
    return None


def _mark_upper_limits(
    ax: Axes,
    positions: np.ndarray,
    levels: np.ndarray,
    limited: np.ndarray,
    language: str,
) -> None:
    """Mark the bands the background held at 2,2 dB as upper limits."""
    ax.plot(
        positions[limited],
        np.asarray(levels)[limited],
        ls="",
        marker="v",
        ms=10,
        color=_C_SECONDARY,
        zorder=6,
        label=_t("upper limit (background)", language),
    )


def plot_service_equipment_level(
    result: ServiceEquipmentResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Band spectrum of a service-equipment measurement, step by step.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.ServiceEquipmentResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the curve of the final band levels.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies_hz, language=language)
    if result.standardized_db is not None:
        shade = theme_fill(_C_MUTED, ax)
        for x in positions[~np.asarray(result.standardizable)]:
            ax.axvspan(x - 0.5, x + 0.5, color=shade, lw=0, zorder=0)
        ax.fill_between(
            [], [], color=shade, lw=0, label=_t("not standardized (7.7)", language)
        )
    ax.plot(
        positions,
        result.average_db,
        "o--",
        color=_C_REFERENCE,
        lw=1.0,
        ms=4,
        label=_t("average of the readings", language),
    )
    if result.background is not None:
        ax.plot(
            positions,
            result.background.background_db,
            ":",
            color=_C_MUTED,
            lw=1.4,
            label=_t(_BACKGROUND_L2_LABEL, language),
        )
    final = result.corrected_db
    final_label = _t(_CORRECTED_LABEL, language)
    if result.standardized_db is not None:
        ax.plot(
            positions,
            result.corrected_db,
            "-",
            color=_C_TERTIARY,
            lw=1.2,
            label=final_label,
        )
        final = result.standardized_db
        final_label = _t("standardized $L_\\mathrm{nT}$", language)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "s")
    kwargs.setdefault("label", final_label)
    ax.plot(positions, final, "-", **kwargs)
    if result.background is not None and result.background.influenced:
        _mark_upper_limits(ax, positions, final, result.background.limited, language)
    ax.set_ylabel(_t(_SPL_LABEL, language))
    headline = _headline_rating(result)
    title = _t(_SERVICE_TITLE, language)
    if headline is not None:
        title = f"{title}: {_rating_symbol(headline)} = {result.ratings[headline]} dB"
    ax.set_title(title)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_service_equipment_background(
    result: ServiceEquipmentBackgroundResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Measured, background and corrected band levels (ISO/DIS 16032 Clause 9).

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.ServiceEquipmentBackgroundResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the corrected-level curve.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = result.frequencies_hz
    labels = freqs if freqs is not None else np.arange(result.measured_db.size) + 1.0
    positions = _band_axis(
        ax,
        labels,
        # Translated here, for the reason given in _plot_shaded_band_pair.
        xlabel=_t(_FREQ_LABEL if freqs is not None else _BAND_INDEX_LABEL, language),
        language=language,
    )
    ax.plot(
        positions,
        result.measured_db,
        "o--",
        color=_C_REFERENCE,
        lw=1.0,
        ms=4,
        label=_t("measured $L_1$", language),
    )
    ax.plot(
        positions,
        result.background_db,
        ":",
        color=_C_MUTED,
        lw=1.4,
        label=_t(_BACKGROUND_L2_LABEL, language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "s")
    kwargs.setdefault("label", _t(_CORRECTED_LABEL, language))
    ax.plot(positions, result.corrected_db, "-", **kwargs)
    if result.influenced:
        _mark_upper_limits(ax, positions, result.corrected_db, result.limited, language)
    ax.set_ylabel(_t(_SPL_LABEL, language))
    ax.set_title(_t(_BACKGROUND_TITLE, language))
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def _reading_names(count: int) -> list[str]:
    """Position numbers of the readings of 7.4.1: 1, 2, 3, 1, 4, 5, 1, 6, 7."""
    names: list[str] = []
    room = 2
    for i in range(count):
        if i % 3 == 0:
            names.append("1")
        else:
            names.append(str(room))
            room += 1
    return names


def plot_position_spread(
    result: PositionSpreadCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The A-weighted readings of 7.4.1 against the spread their stage allows.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.PositionSpreadCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers of the room positions.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    levels = np.asarray(result.levels_db, dtype=np.float64)
    x = np.arange(levels.size, dtype=np.float64)
    corner = np.zeros(levels.size, dtype=bool)
    corner[::3] = True
    low = float(np.min(levels))
    ax.fill_between(
        [-0.5, levels.size - 0.5],
        [low, low],
        [low + result.limit_db] * 2,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=(
            f"{_t('allowed spread', language)} "
            f"({format_number(result.limit_db, language)} dB)"
        ),
    )
    ax.plot(
        x[corner],
        levels[corner],
        ls="",
        marker="s",
        ms=9,
        color=_C_SECONDARY,
        zorder=4,
        label=_t("corner", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 8)
    kwargs.setdefault("label", _t("room positions", language))
    ax.plot(x[~corner], levels[~corner], ls="", zorder=4, **kwargs)
    ax.set_xticks(x)
    ax.set_xticklabels(_reading_names(levels.size))
    ax.set_xlim(-0.5, levels.size - 0.5)
    ax.set_xlabel(_t("Reading", language))
    ax.set_ylabel(_t("A-weighted level [dB]", language))
    if result.action == "add_positions":
        a, b = result.next_positions
        verdict = f"{_t('add positions', language)} {a} {_t('and', language)} {b}"
    else:
        verdict = _t(result.action, language)
    ax.set_title(
        f"{_t(_SPREAD_TITLE, language)}: "
        f"{format_number(result.spread_db, language)} dB, {verdict}"
    )
    span = max(result.limit_db, result.spread_db)
    ax.set_ylim(low - 0.4 * span, low + 1.6 * span)
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_service_equipment_positions(
    result: ServiceEquipmentPositionCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Plan view of the room with the microphone positions of 7.2 and 7.3.

    The key stands beside the plan, which has no empty corner to spare. A
    figure the renderer creates itself is wide enough for it, with the plan
    placed to leave the key and the title room, so a plain ``savefig()`` or
    ``plt.show()`` keeps both on the canvas; on axes the caller passes, the
    caller lays the figure out (``plt.tight_layout()``).

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.ServiceEquipmentPositionCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers of the reverberant-field positions.
    :return: The axes.
    """
    from matplotlib.patches import Rectangle

    from .._i18n import format_number, localize_axes
    from .geometry._draft import _chip

    if ax is None:
        figure = _import_pyplot().figure(figsize=_POSITIONS_FIGURE_SIZE_IN)
        ax = figure.add_axes(_POSITIONS_AXES_RECT)
    length = float(result.room_dimensions_m[0])
    width = float(result.room_dimensions_m[1])
    ax.add_patch(
        Rectangle(
            (0.0, 0.0),
            length,
            width,
            fill=False,
            # The spine colour, so the walls read on a dark page as well.
            edgecolor=ax.spines["bottom"].get_edgecolor(),
            lw=1.6,
            label=_t("room outline", language),
        )
    )
    clearance = result.surface_limit_m
    # The zone the reverberant-field positions may take, washed and edged in
    # a hue of its own: a grey dashed edge would pass for one more gridline,
    # and on a dark page its lower edge sat on the 0.5 m line and vanished.
    # The wash stays under the grid, which still reads across it, and the
    # edge is drawn again over the grid, so a gridline under it cannot cut it.
    zone = (clearance, clearance)
    zone_length = length - 2.0 * clearance
    zone_width = width - 2.0 * clearance
    edge: dict[str, Any] = {"edgecolor": _C_TERTIARY, "ls": "--", "lw": 1.4}
    ax.add_patch(
        Rectangle(
            zone,
            zone_length,
            zone_width,
            facecolor=theme_fill(_C_TERTIARY, ax),
            zorder=1,
            label=_t("surface clearance", language),
            **edge,
        )
    )
    ax.add_patch(Rectangle(zone, zone_length, zone_width, fill=False, zorder=2, **edge))
    sources = np.asarray(result.source_positions_m)
    rooms = np.asarray(result.room_positions_m)
    # A plan cannot show a distance in three dimensions, and a source in the
    # ceiling can sit above a position that is well clear of it; so each
    # source is joined to its nearest room position and the line carries the
    # true distance, rather than a circle the plan would misdraw.
    for i, source in enumerate(sources):
        gaps = np.linalg.norm(rooms - source, axis=1)
        nearest = rooms[int(np.argmin(gaps))]
        ax.plot(
            [source[0], nearest[0]],
            [source[1], nearest[1]],
            ls=":",
            lw=1.2,
            color=_C_REFERENCE,
            zorder=2,
            label=_t("distance to a source", language) if i == 0 else None,
        )
        ax.annotate(
            f"{format_number(float(np.min(gaps)), language, decimals=2)} m",
            ((source[0] + nearest[0]) / 2.0, (source[1] + nearest[1]) / 2.0),
            ha="center",
            va="center",
            fontsize="small",
            zorder=7,
            bbox=_chip(ax, 0.2),
        )
    if sources.size:
        ax.plot(
            sources[:, 0],
            sources[:, 1],
            ls="",
            marker="X",
            ms=11,
            color=_C_REFERENCE,
            zorder=5,
            label=_t("sound source", language),
        )
    corner = np.asarray(result.corner_position_m)
    ax.plot(
        [corner[0]],
        [corner[1]],
        ls="",
        marker="s",
        ms=10,
        color=_C_SECONDARY,
        zorder=6,
        label=_t("corner position", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 9)
    kwargs.setdefault("label", _t("reverberant-field positions", language))
    ax.plot(rooms[:, 0], rooms[:, 1], ls="", zorder=6, **kwargs)
    # Numbered as the draft numbers them: the corner is position 1 (7.2) and
    # the reverberant-field positions follow from 2.
    points = [(float(corner[0]), float(corner[1]))]
    points += [(float(px), float(py)) for px, py, _ in rooms]
    for number, (px, py) in enumerate(points, start=1):
        ax.annotate(
            str(number),
            (px, py),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize="small",
            zorder=7,
        )
    ax.set_aspect("equal")
    ax.set_xlim(-0.3, length + 0.3)
    ax.set_ylim(-0.3, width + 0.3)
    ax.set_xlabel(_t("Length $x$ [m]", language))
    ax.set_ylabel(_t("Width $y$ [m]", language))
    verdict = "requirements met" if result.passes else "requirements not met"
    # The verdict on a line of its own: beside the key, one line of title
    # and verdict is wider than the plan in Spanish.
    ax.set_title(f"{_t(_POSITIONS_TITLE, language)}\n{_t(verdict, language)}")
    ax.legend(fontsize="small", loc=_LEGEND_UPPER_LEFT, bbox_to_anchor=(1.02, 1.0))
    localize_axes(ax, language)
    return ax


# --- ISO/DIS 16032 on-site checks (Clause 5, 7.6, 7.8 and Clause 9) ---------


#: The two calibrations Clause 5 asks of a measurement, as the ticks name them.
_CLAUSE_5_READINGS = ("beginning", "end")


def _calibration_names(previous: int, current: int, language: str) -> list[str]:
    """Tick names: the earlier calibrations, then beginning and end."""
    earlier = _t("earlier", language)
    names = (
        [earlier] if previous == 1 else [f"{earlier} {i + 1}" for i in range(previous)]
    )
    if current <= len(_CLAUSE_5_READINGS):
        names += [_t(name, language) for name in _CLAUSE_5_READINGS[:current]]
    else:
        names += [str(i + 1) for i in range(current)]
    return names


def plot_calibration_deviation(
    result: CalibrationDeviationResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each calibration reading against the window the earlier ones leave it.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.CalibrationDeviationResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers of this measurement's readings.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes
    from .geometry._draft import _chip

    ax = ax if ax is not None else _new_axes()
    previous = np.asarray(result.previous_levels_db, dtype=np.float64)
    levels = np.asarray(result.levels_db, dtype=np.float64)
    history = np.concatenate((previous, levels))
    x_previous = np.arange(previous.size, dtype=np.float64)
    x_levels = previous.size + np.arange(levels.size, dtype=np.float64)
    shade = theme_fill(_C_TERTIARY, ax)
    drawn_window = False
    for i, x in enumerate(x_levels):
        earlier = history[: previous.size + i]
        if not earlier.size:
            continue
        # Inside this window a reading is no more than the limit from every
        # earlier calibration: above the highest less the limit, below the
        # lowest plus it.
        low = float(np.max(earlier)) - result.limit_db
        high = float(np.min(earlier)) + result.limit_db
        if high > low:
            ax.fill_between(
                [x - 0.3, x + 0.3],
                [low, low],
                [high, high],
                color=shade,
                lw=0,
                zorder=0,
                label=(
                    None
                    if drawn_window
                    else _t("within 0.5 dB of every earlier calibration", language)
                ),
            )
            drawn_window = True
    if previous.size:
        ax.plot(
            x_previous,
            previous,
            ls="",
            marker="s",
            ms=8,
            color=_C_MUTED,
            zorder=4,
            label=_t("earlier calibrations", language),
        )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 9)
    kwargs.setdefault("label", _t(_THIS_MEASUREMENT_LABEL, language))
    ax.plot(x_levels, levels, ls="", zorder=5, **kwargs)
    for x, level, deviation in zip(x_levels, levels, result.deviations_db, strict=True):
        if not np.isfinite(deviation):
            continue
        ax.annotate(
            f"{format_number(float(deviation), language, decimals=2)} dB",
            (x, level),
            xytext=(14, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize="small",
            zorder=7,
            bbox=_chip(ax, 0.2),
        )
    ax.set_xticks(np.concatenate((x_previous, x_levels)))
    ax.set_xticklabels(_calibration_names(previous.size, levels.size, language))
    ax.set_xlim(-0.6, history.size - 0.4)
    span = max(float(np.ptp(history)), result.limit_db)
    ax.set_ylim(
        float(np.min(history)) - 1.2 * span, float(np.max(history)) + 1.6 * span
    )
    ax.set_xlabel(_t("Calibration", language))
    ax.set_ylabel(_t("Calibrator reading [dB]", language))
    verdict = (
        "equipment may be used"
        if result.passes
        else "equipment out of use until clarified"
    )
    ax.set_title(
        f"{_t(_CALIBRATION_TITLE, language)}\n"
        f"{_t('largest deviation', language)} "
        f"{format_number(result.largest_deviation_db, language, decimals=2)} dB: "
        f"{_t(verdict, language)}"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_background_duration(
    result: BackgroundDurationCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each background measurement time against the 30 s of 7.6 and the tolerance.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.BackgroundDurationCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers of the durations.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    durations = np.asarray(result.durations_s, dtype=np.float64)
    x = np.arange(1, durations.size + 1, dtype=np.float64)
    nominal = result.nominal_duration_s
    tolerance = result.tolerance_s
    if tolerance > 0.0:
        ax.fill_between(
            [0.4, durations.size + 0.6],
            [nominal - tolerance] * 2,
            [nominal + tolerance] * 2,
            color=theme_fill(_C_TERTIARY, ax),
            lw=0,
            zorder=0,
            label=_t("tolerance accepted", language),
        )
    ax.axhline(
        nominal,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        zorder=2,
        label=_t("30 s of 7.6", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 9)
    kwargs.setdefault("label", _t("measurement time", language))
    ax.plot(x, durations, ls="", zorder=5, **kwargs)
    outside = ~np.asarray(result.within_tolerance)
    if np.any(outside):
        # A ring round each duration beyond the tolerance, which leaves the
        # marker of the duration itself in sight.
        ax.plot(
            x[outside],
            durations[outside],
            ls="",
            marker="o",
            ms=17,
            mfc="none",
            mew=2.0,
            color=_C_SECONDARY,
            zorder=6,
            label=_t("beyond the tolerance", language),
        )
    ax.set_xticks(x)
    ax.set_xlim(0.4, durations.size + 0.6)
    # Centred on 30 s and wide enough for the band and the largest departure,
    # so that a departure of a second or two stays visible.
    reach = 1.8 * max(result.largest_departure_s, tolerance, 1.0)
    ax.set_ylim(max(0.0, nominal - reach), nominal + reach)
    ax.set_xlabel(_t("Background measurement", language))
    ax.set_ylabel(_t("Measurement time [s]", language))
    tolerance_text = format_number(tolerance, language, trim=True)
    if result.passes:
        verdict = _t("every background within {tolerance} s of 30 s", language).format(
            tolerance=tolerance_text
        )
    else:
        verdict = _t(
            "largest departure {departure} s, beyond the {tolerance} s accepted",
            language,
        ).format(
            departure=format_number(result.largest_departure_s, language, trim=True),
            tolerance=tolerance_text,
        )
    ax.set_title(f"{_t(_DURATION_TITLE, language)}\n{verdict}")
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_varying_background(
    result: VaryingBackgroundCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The equipment level, the background maximum and the 10 dB line, per band.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.VaryingBackgroundCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the curve of the equipment level.
    :return: The axes.
    """
    from .._i18n import format_number, localize_axes

    ax = ax if ax is not None else _new_axes()
    freqs = result.frequencies_hz
    equipment = np.asarray(result.equipment_levels_db, dtype=np.float64)
    background = np.asarray(result.background_maximum_db, dtype=np.float64)
    labels = freqs if freqs is not None else np.arange(equipment.size) + 1.0
    positions = _band_axis(
        ax,
        labels,
        # Translated here, for the reason given in _plot_shaded_band_pair.
        xlabel=_t(_FREQ_LABEL if freqs is not None else _BAND_INDEX_LABEL, language),
        language=language,
    )
    threshold = equipment - result.limit_db
    ax.plot(
        positions,
        threshold,
        "--",
        color=_C_TERTIARY,
        lw=1.2,
        label=_t("10 dB below the equipment", language),
    )
    ax.plot(
        positions,
        background,
        ":",
        color=_C_MUTED,
        lw=1.6,
        marker=".",
        label=_t("background maximum", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "s")
    kwargs.setdefault("label", _t("service equipment", language))
    ax.plot(positions, equipment, "-", **kwargs)
    short = ~np.asarray(result.margin_ok)
    if np.any(short):
        ax.plot(
            positions[short],
            background[short],
            ls="",
            marker="v",
            ms=10,
            color=_C_SECONDARY,
            zorder=6,
            label=_t("less than 10 dB below", language),
        )
    ax.set_ylabel(_t(_SPL_LABEL, language))
    verdict = (
        "valid without correction" if result.passes else "not valid without correction"
    )
    minutes = format_number(result.observation_time_s / 60.0, language, trim=True)
    ax.set_title(
        f"{_t(_VARYING_TITLE, language)}\n{_t(verdict, language)}, "
        f"{_t('watched for', language)} {minutes} min"
    )
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_measurement_disturbance(
    result: MeasurementDisturbanceCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each period's maximum less equivalent level against the 5 dB of Clause 9.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.MeasurementDisturbanceCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers of the differences.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    differences = np.asarray(result.differences_db, dtype=np.float64)
    x = np.arange(1, differences.size + 1, dtype=np.float64)
    top = max(float(np.max(differences)), result.limit_db) + 0.5 * result.limit_db
    ax.fill_between(
        [0.4, differences.size + 0.6],
        [result.limit_db] * 2,
        [top] * 2,
        color=theme_fill(_C_SECONDARY, ax),
        lw=0,
        zorder=0,
        label=_t("disturbed", language),
    )
    ax.axhline(
        result.limit_db,
        color=_C_SECONDARY,
        ls="--",
        lw=1.2,
        zorder=2,
        label=_t("5 dB of Clause 9", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 9)
    kwargs.setdefault("label", _t("difference per period", language))
    ax.plot(x, differences, ls="", zorder=5, **kwargs)
    ax.set_xticks(x)
    ax.set_xlim(0.4, differences.size + 0.6)
    ax.set_ylim(min(0.0, float(np.min(differences))), top)
    ax.set_xlabel(_t("Measurement period", language))
    ax.set_ylabel(_t("Maximum less equivalent level [dB]", language))
    if result.passes:
        verdict = _t("no period disturbed", language)
    else:
        periods = ", ".join(str(i + 1) for i in result.disturbed_periods)
        verdict = f"{_t('disturbed periods', language)}: {periods}"
    ax.set_title(f"{_t(_DISTURBANCE_TITLE, language)}\n{verdict}")
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


def plot_instrument_agreement(
    result: InstrumentAgreementCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each calculated-less-instrument difference against the 2 dB of 7.8.

    :param result: A
        :class:`~phonometry.building.measurement.service_equipment.InstrumentAgreementCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the markers of the differences.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    keys = list(result.differences_db)
    differences = np.array([result.differences_db[k] for k in keys], dtype=np.float64)
    x = np.arange(differences.size, dtype=np.float64)
    limit = result.limit_db
    ax.fill_between(
        [-0.6, differences.size - 0.4],
        [-limit] * 2,
        [limit] * 2,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=_t("within 2 dB", language),
    )
    ax.axhline(0.0, color=_C_REFERENCE, lw=0.8, zorder=1)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    style_default(kwargs, "ms", 9)
    kwargs.setdefault("label", _t("calculated less instrument", language))
    ax.plot(x, differences, ls="", zorder=5, **kwargs)
    ax.set_xticks(x)
    ax.set_xticklabels([_rating_symbol(k) for k in keys])
    ax.set_xlim(-0.6, differences.size - 0.4)
    reach = max(float(np.max(np.abs(differences))), limit) + 0.8 * limit
    ax.set_ylim(-reach, reach)
    ax.set_xlabel(_t("Single number", language))
    ax.set_ylabel(_t("Calculated less instrument [dB]", language))
    verdict = (
        "calculation agrees"
        if result.passes
        else "more than 2 dB apart: check the calculation"
    )
    ax.set_title(f"{_t(_AGREEMENT_TITLE, language)}\n{_t(verdict, language)}")
    ax.grid(visible=True, axis="y", alpha=0.3)
    place_legend_clear(ax.legend(fontsize="small"))
    localize_axes(ax, language)
    return ax


# --- ISO 10140-1:2021 Annexes G, H and K ------------------------------------

#: Labels of the laboratory improvement and rainfall figures, kept as names so
#: the renderers and :data:`_LAB_STRINGS` cannot drift apart.
_DELTA_R_LABEL = r"Sound reduction improvement index $\Delta R$ [dB]"
_INTENSITY_LEVEL_LABEL = r"Sound intensity level $L_I$ [dB re 1 pW/m²]"
_LINING_TITLE = "Lining improvement (ISO 10140-1 Annex G)"
_LINING_RATING_TITLE = "Lining rated on the reference curve (ISO 717-1 Annex D)"
_COVERING_TITLE = "Floor-covering improvement (ISO 10140-1 Annex H)"
_HEAVY_SOFT_TITLE = "Heavy/soft impact improvement (ISO 10140-1 H.6.1)"
_CURING_TITLE = "Curing of the basic element (ISO 10140-1 G.4)"
_RAIN_TITLE = "Rainfall sound (ISO 10140-1 Annex K)"
_RAIN_REFERENCE_TITLE = "Reference specimen correction (ISO 10140-5 Annex I)"
_RAIN_GENERATOR_TITLE = "Rain generator (ISO 10140-5 Table H.1)"

#: Spanish translations of the figures above, merged into :data:`_STRINGS`.
_LAB_STRINGS: dict[str, str] = {
    _DELTA_R_LABEL: r"Mejora del índice de reducción acústica $\Delta R$ [dB]",
    _INTENSITY_LEVEL_LABEL: r"Nivel de intensidad acústica $L_I$ [dB re 1 pW/m²]",
    _LINING_TITLE: "Mejora por trasdosado (ISO 10140-1 Anexo G)",
    _LINING_RATING_TITLE: "Trasdosado sobre la curva de referencia (ISO 717-1 Anexo D)",
    _COVERING_TITLE: "Mejora por revestimiento de suelo (ISO 10140-1 Anexo H)",
    _HEAVY_SOFT_TITLE: "Mejora con impacto pesado y blando (ISO 10140-1 H.6.1)",
    _CURING_TITLE: "Curado del elemento base (ISO 10140-1 G.4)",
    _RAIN_TITLE: "Ruido de lluvia (ISO 10140-1 Anexo K)",
    _RAIN_REFERENCE_TITLE: "Corrección con el vidrio de referencia (ISO 10140-5 Anexo I)",
    _RAIN_GENERATOR_TITLE: "Generador de lluvia (ISO 10140-5 Tabla H.1)",
    "heavy wall": "pared pesada",
    "heavy floor": "suelo pesado",
    "lightweight wall": "pared ligera",
    "heavyweight floor": "suelo de referencia pesado",
    "lightweight floor No 1": "suelo de referencia ligero n.º 1",
    "lightweight floor No 2": "suelo de referencia ligero n.º 2",
    "lightweight floor No 3": "suelo de referencia ligero n.º 3",
    "no rating (bands missing)": "sin índice (faltan bandas)",
    "Time from construction to the first measurement [d]": (
        "Tiempo desde la construcción hasta la primera medición [d]"
    ),
    "Time between the two measurements [d]": "Tiempo entre las dos mediciones [d]",
    "admissible": "admisible",
    "lag = curing time / 3": "intervalo = tiempo de curado / 3",
    "required curing": "curado exigido",
    "rainfall rate": "intensidad de lluvia",
    "drop diameter": "diámetro de gota",
    "fall velocity": "velocidad de caída",
    "Deviation from nominal / tolerance": "Desviación respecto al nominal / tolerancia",
    "measured drops": "gotas medidas",
    "measured rate": "intensidad medida",
    "intense rain": "lluvia intensa",
    "heavy rain": "lluvia fuerte",
    "normalized": "normalizado",
    "Maximum impact level improvement": "Mejora del nivel máximo de impactos",
    r"$L_{I\mathrm{c,ref}}$ (Table I.1)": r"$L_{I\mathrm{c,ref}}$ (Tabla I.1)",
    "lightweight floors No 1 and No 2": "suelos de referencia ligeros n.º 1 y n.º 2",
    "Reference floors (ISO 717-2 Table 4)": "Suelos de referencia (ISO 717-2 Tabla 4)",
}
_STRINGS.update(_LAB_STRINGS)

#: Localised names of the three standard basic elements and the four
#: reference floors, as the figure titles write them.
_BASIC_ELEMENT_LABELS = {
    "heavy_wall": "heavy wall",
    "heavy_floor": "heavy floor",
    "lightweight_wall": "lightweight wall",
}
_REFERENCE_FLOOR_LABELS = {
    "heavyweight": "heavyweight floor",
    "lightweight_1": "lightweight floor No 1",
    "lightweight_2": "lightweight floor No 2",
    "lightweight_3": "lightweight floor No 3",
}

#: Mathtext symbol of the weighted reduction on each reference floor.
_FLOOR_SYMBOLS = {
    "heavyweight": r"$\Delta L_\mathrm{w}$",
    "lightweight_1": r"$\Delta L_\mathrm{t,1,w}$",
    "lightweight_2": r"$\Delta L_\mathrm{t,2,w}$",
    "lightweight_3": r"$\Delta L_\mathrm{t,3,w}$",
}

#: Mathtext symbol of its spectrum adaptation term: ``CI,Δ`` on the heavyweight
#: floor, as ISO 10140-1:2021 H.5 h) prints it, and ``CIΔ,t1`` to ``CIΔ,t3`` on
#: the lightweight floors of type C1 to C3 (ISO 717-2:2020 A.2.3).
_FLOOR_ADAPTATION_SYMBOLS = {
    "heavyweight": r"$C_{\mathrm{I},\Delta}$",
    "lightweight_1": r"$C_{\mathrm{I}\Delta,\mathrm{t1}}$",
    "lightweight_2": r"$C_{\mathrm{I}\Delta,\mathrm{t2}}$",
    "lightweight_3": r"$C_{\mathrm{I}\Delta,\mathrm{t3}}$",
}


def _db(value: float, language: str) -> str:
    """A decibel value for a title: typographic minus, the locale's separator."""
    from .._i18n import decimal_comma, fmt_minus

    spec = "g" if float(value).is_integer() else ".1f"
    return decimal_comma(fmt_minus(float(value), spec), language)


def _improvement_curve(
    ax: Axes,
    freqs: np.ndarray,
    values: np.ndarray,
    label: str,
    language: str,
    kwargs: dict[str, Any],
) -> None:
    """Draw one improvement spectrum on a band axis with its zero line."""
    positions = _band_axis(ax, freqs, language=language)
    ax.axhline(0.0, color=_C_MUTED, lw=1.0, zorder=1)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", label)
    ax.plot(positions, values, **kwargs)
    ax.grid(visible=True, which="both", alpha=0.3)


def plot_reduction_improvement_rating(
    result: ReductionImprovementRating,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """The two curves ISO 717-1 Annex D rates, and the improvement between them.

    :param result: A
        :class:`~phonometry.building.measurement.ratings.ReductionImprovementRating`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``Rref,with`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    without, with_ = result.without_lining, result.with_lining
    if without.band_centers is None or without.measured is None:
        msg = "The rating carries no reference curve to plot."
        raise ValueError(msg)
    if with_.measured is None:
        msg = "The rating carries no curve with the lining to plot."
        raise ValueError(msg)
    positions = _band_axis(ax, without.band_centers, language=language)
    ax.plot(
        positions,
        without.measured,
        "s--",
        color=_C_REFERENCE,
        lw=1.2,
        label=rf"$R_\mathrm{{ref,without}}$ ($R_\mathrm{{w}}$ = "
        rf"{_db(without.rating, language)} dB)",
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault(
        "label",
        rf"$R_\mathrm{{ref,with}}$ ($R_\mathrm{{w}}$ = {_db(with_.rating, language)} dB)",
    )
    ax.plot(positions, with_.measured, **kwargs)
    ax.set_ylabel(_t(_R_INDEX_LABEL, language))
    element = _t(_BASIC_ELEMENT_LABELS[result.basic_element], language)
    ax.set_title(
        f"{_t(_LINING_RATING_TITLE, language)}\n{element}: "
        rf"$\Delta R_\mathrm{{w,{result.index}}}$ = {_db(result.delta_rw, language)} dB"
    )
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_lab_lining_improvement(
    result: LabLiningImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Improvement ``ΔR`` of a lining per band (ISO 10140-1:2021 Annex G).

    :param result: A
        :class:`~phonometry.building.measurement.lab_improvement.LabLiningImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _improvement_curve(
        ax, result.frequencies_hz, result.delta_r_db, r"$\Delta R$", language, kwargs
    )
    ax.set_ylabel(_t(_DELTA_R_LABEL, language))
    if result.rating is not None:
        element = _t(_BASIC_ELEMENT_LABELS[result.rating.basic_element], language)
        headline = (
            rf"{element}: $\Delta R_\mathrm{{w,{result.rating.index}}}$ = "
            f"{_db(result.rating.delta_rw, language)} dB"
        )
    elif result.delta_rw_direct_db is not None:
        headline = (
            r"$\Delta R_\mathrm{w,direct}$ = "
            f"{_db(result.delta_rw_direct_db, language)} dB"
        )
    else:
        headline = _t("no rating (bands missing)", language)
    ax.set_title(f"{_t(_LINING_TITLE, language)}\n{headline}")
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_lining_curing_check(
    result: LiningCuringCheck,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Admissible curing time and time lag of ISO 10140-1:2021 G.4.

    The admissible region is the union of the two ways out G.4 allows: a
    curing time of at least the required period, whatever the lag, and a lag
    of at most a third of the curing time.

    :param result: A
        :class:`~phonometry.building.measurement.lab_improvement.LiningCuringCheck`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the marker of this measurement.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    x_max = 1.3 * max(result.required_curing_days, result.curing_time_days, 1.0)
    y_max = 1.3 * max(x_max / 3.0, result.time_lag_days, 0.5)
    curing = np.linspace(0.0, x_max, 400)
    ceiling = np.where(curing >= result.required_curing_days, y_max, curing / 3.0)
    ax.fill_between(
        curing,
        0.0,
        ceiling,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=_t("admissible", language),
    )
    ax.plot(
        curing,
        curing / 3.0,
        color=_C_REFERENCE,
        ls="--",
        lw=1.2,
        label=_t("lag = curing time / 3", language),
    )
    ax.axvline(
        result.required_curing_days,
        color=_C_MUTED,
        ls=":",
        lw=1.4,
        label=f"{_t('required curing', language)} = "
        f"{_db(result.required_curing_days, language)} d",
    )
    style_default(kwargs, "color", _C_PRIMARY if result.passes else _C_SECONDARY)
    kwargs.setdefault("marker", "o" if result.passes else "X")
    style_default(kwargs, "ms", 10)
    style_default(kwargs, "ls", "")
    kwargs.setdefault("label", _t(_THIS_MEASUREMENT_LABEL, language))
    ax.plot([result.curing_time_days], [result.time_lag_days], **kwargs)
    ax.set_xlim(0.0, x_max)
    ax.set_ylim(0.0, y_max)
    ax.set_xlabel(_t("Time from construction to the first measurement [d]", language))
    ax.set_ylabel(_t("Time between the two measurements [d]", language))
    verdict = _verdict_word(passes=result.passes, language=language)
    ax.set_title(f"{_t(_CURING_TITLE, language)}: {verdict}")
    ax.grid(visible=True, alpha=0.3)
    ax.legend(loc=_LEGEND_UPPER_LEFT, fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_lab_floor_covering_improvement(
    result: LabFloorCoveringImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Improvement ``ΔL`` of a floor covering per band (ISO 10140-1:2021 Annex H).

    :param result: A
        :class:`~phonometry.building.measurement.lab_improvement.LabFloorCoveringImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _improvement_curve(
        ax,
        result.frequencies_hz,
        result.improvement_db,
        r"$\Delta L$",
        language,
        kwargs,
    )
    ax.set_ylabel(_t(_IMPROVEMENT_LABEL, language))
    floor = _t(_REFERENCE_FLOOR_LABELS[result.reference_floor], language)
    if result.delta_lw_db is not None and result.ci_delta_db is not None:
        headline = (
            f"{floor}: {_FLOOR_SYMBOLS[result.reference_floor]} = "
            f"{_db(result.delta_lw_db, language)} dB "
            f"({_FLOOR_ADAPTATION_SYMBOLS[result.reference_floor]} = "
            f"{_db(result.ci_delta_db, language)} dB)"
        )
    else:
        headline = f"{floor}: {_t('no rating (bands missing)', language)}"
    ax.set_title(f"{_t(_COVERING_TITLE, language)}\n{headline}")
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_heavy_impact_improvement(
    result: HeavyImpactImprovementResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Improvement ``ΔLr`` of a floor covering under the rubber ball (H.6.1).

    :param result: A
        :class:`~phonometry.building.measurement.lab_improvement.HeavyImpactImprovementResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the improvement-curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    _improvement_curve(
        ax,
        result.frequencies_hz,
        result.improvement_db,
        r"$\Delta L_\mathrm{r}$",
        language,
        kwargs,
    )
    ax.set_ylabel(f"{_t('Maximum impact level improvement', language)} [dB]")
    ax.set_title(_t(_HEAVY_SOFT_TITLE, language))
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_rain_generator_verification(
    result: RainGeneratorVerification,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Each quantity of the generated rain against its tolerance window.

    Every quantity is drawn as its deviation from the nominal value of
    Table H.1 in units of its tolerance, so the window is -1 to 1 on every
    row: the rainfall rate as one marker, and the measured drops, when given,
    as a strip of points.

    :param result: A
        :class:`~phonometry.building.measurement.rainfall_sound.RainGeneratorVerification`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the rainfall-rate marker.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    nominal = result.nominal
    rows: list[tuple[str, np.ndarray]] = [
        (
            "rainfall rate",
            np.asarray(
                [result.rate_deviation_mm_h / nominal.rainfall_rate_tolerance_mm_h]
            ),
        )
    ]
    if result.drop_diameters_mm is not None:
        rows.append(
            (
                "drop diameter",
                (result.drop_diameters_mm - nominal.median_drop_diameter_mm)
                / nominal.drop_diameter_tolerance_mm,
            )
        )
    if result.fall_velocities_m_s is not None:
        rows.append(
            (
                "fall velocity",
                (result.fall_velocities_m_s - nominal.fall_velocity_m_s)
                / nominal.fall_velocity_tolerance_m_s,
            )
        )
    reach = max(1.5, 1.15 * max(float(np.max(np.abs(v))) for _, v in rows))
    ax.axvspan(-1.0, 1.0, color=theme_fill(_C_TERTIARY, ax), lw=0, zorder=0)
    ax.axvline(0.0, color=_C_MUTED, lw=1.0, zorder=1)
    style_default(kwargs, "color", _C_PRIMARY if result.rate_ok else _C_SECONDARY)
    kwargs.setdefault("marker", "o" if result.rate_ok else "X")
    style_default(kwargs, "ms", 10)
    style_default(kwargs, "ls", "")
    kwargs.setdefault("label", _t("measured rate", language))
    ax.plot(rows[0][1], [0.0], **kwargs)
    drops_labelled = False
    for index, (_, values) in enumerate(rows[1:], start=1):
        # Spread the drops over the height of their row on a fixed pattern,
        # so the strip reads as a distribution and the figure is reproducible.
        spread = 0.25 * ((np.arange(values.size) % 7) / 3.0 - 1.0)
        ax.plot(
            values,
            index + spread,
            ls="",
            marker=".",
            ms=5,
            color=_C_REFERENCE,
            label=None if drops_labelled else _t("measured drops", language),
        )
        drops_labelled = True
    ax.set_yticks(np.arange(len(rows)))
    ax.set_yticklabels([_t(name, language) for name, _ in rows])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(-reach, reach)
    ax.set_xlabel(_t("Deviation from nominal / tolerance", language))
    verdict = _verdict_word(passes=result.passes, language=language)
    rain = _t(f"{result.rain_type} rain", language)
    ax.set_title(f"{_t(_RAIN_GENERATOR_TITLE, language)}\n{rain}: {verdict}")
    ax.grid(visible=True, axis="x", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_rainfall_reference_correction(
    result: RainfallReferenceCorrection,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Corrected level of the reference pane against Table I.1 (Annex I).

    :param result: A
        :class:`~phonometry.building.measurement.rainfall_sound.RainfallReferenceCorrection`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the corrected-level curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies_hz, language=language)
    ax.fill_between(
        positions,
        result.l_ic_ref_db,
        result.l_i_m_ref_db,
        color=theme_fill(_C_TERTIARY, ax),
        lw=0,
        zorder=0,
        label=r"$\Delta L_{I\mathrm{c}}$",
    )
    ax.plot(
        positions,
        result.l_ic_ref_db,
        "s--",
        color=_C_REFERENCE,
        lw=1.2,
        label=_t(r"$L_{I\mathrm{c,ref}}$ (Table I.1)", language),
    )
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", r"$L_{I,\mathrm{m,ref}}$")
    ax.plot(positions, result.l_i_m_ref_db, **kwargs)
    ax.set_ylabel(_t(_INTENSITY_LEVEL_LABEL, language))
    ax.set_title(_t(_RAIN_REFERENCE_TITLE, language))
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax


def plot_rainfall_sound(
    result: RainfallSoundResult,
    ax: Axes | None = None,
    language: str = "en",
    **kwargs: Any,
) -> Axes:
    """Sound intensity level of a specimen under rain, per band (Annex K).

    :param result: A
        :class:`~phonometry.building.measurement.rainfall_sound.RainfallSoundResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to the ``L_I`` curve ``plot`` call.
    :return: The axes.
    """
    from .._i18n import localize_axes

    ax = ax if ax is not None else _new_axes()
    positions = _band_axis(ax, result.frequencies_hz, language=language)
    style_default(kwargs, "color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("label", r"$L_I$")
    ax.plot(positions, result.l_i_db, **kwargs)
    if result.l_i_norm_db is not None:
        ax.plot(
            positions,
            result.l_i_norm_db,
            "s--",
            color=_C_SECONDARY,
            lw=1.2,
            label=rf"$L_{{I\mathrm{{norm}}}}$ ({_t('normalized', language)})",
        )
    ax.set_ylabel(_t(_INTENSITY_LEVEL_LABEL, language))
    title = _t(_RAIN_TITLE, language)
    if result.l_ia_db is not None:
        title += "\n" + (
            rf"$L_{{I\mathrm{{A}}}}$ = {_db(round(result.l_ia_db, 1), language)} dB"
        )
        if result.l_ia_norm_db is not None:
            title += (
                rf", $L_{{I\mathrm{{A,norm}}}}$ = "
                f"{_db(round(result.l_ia_norm_db, 1), language)} dB"
            )
    ax.set_title(title)
    ax.grid(visible=True, which="both", alpha=0.3)
    ax.legend(loc="best", fontsize="small")
    localize_axes(ax, language)
    return ax
