#  Copyright (c) 2026. Jose M. Requena-Plens
"""Translated fixed strings for the accredited ``.report()`` fiches.

Every fixed English string the six report renderers emit (titles, standard-basis
line templates, table headers, metadata-grid labels, metric-row labels, verdict
prose and the footer identity/disclaimer block) is keyed here by a stable
English string-id and mapped to its English and Spanish forms. English is the
default and is byte-for-byte unchanged; passing ``language="es"`` to a result's
``report`` method renders these strings in Spanish (the decimal separator is
switched to a comma by :func:`phonometry._i18n.format_number`).

Unit symbols (Hz, dB, LUFS, LU, dBTP, sone, phon, EPNdB, PNdB, kPa, m2, m3, C,
%), single-letter quantity symbols (R, alpha, N ...) and published standard
designations (ISO 717-1, EBU R 128 ...) are never translated; only the natural
language around them is. Templates carry ``{}``-style placeholders the renderer
fills after translation.

The user's own free-text metadata *values* (specimen, client, notes ...) are
never translated: only the fixed *labels* live here.
"""

from __future__ import annotations

#: Fixed report strings keyed by a stable English string-id. Each value maps a
#: language code to its rendering. Templates use ``{}``/``{name}`` placeholders.
REPORT_STRINGS: dict[str, dict[str, str]] = {
    # --- titles ----------------------------------------------------------
    "title.airborne": {
        "en": "Airborne sound insulation rating",
        "es": "Índice de aislamiento acústico a ruido aéreo",
    },
    "title.impact": {
        "en": "Impact sound insulation rating",
        "es": "Índice de aislamiento acústico a ruido de impactos",
    },
    "title.absorption": {
        "en": "Sound absorption rating",
        "es": "Índice de absorción acústica",
    },
    "title.loudness": {
        "en": "Loudness rating",
        "es": "Índice de sonoridad",
    },
    "title.program_loudness": {
        "en": "Programme loudness compliance",
        "es": "Conformidad de sonoridad de programa",
    },
    "title.epnl": {
        "en": "Aircraft noise certification - EPNL result",
        "es": "Certificación de ruido de aeronaves - resultado EPNL",
    },
    "title.filter_class": {
        "en": "Filter class compliance",
        "es": "Conformidad de clase de filtro",
    },
    # --- standard-basis line templates -----------------------------------
    "basis.iso717.with_standard": {
        "en": "{standard} laboratory measurement of sound insulation. "
              "Rating per {part}:2020.",
        "es": "{standard} medición en laboratorio del aislamiento acústico. "
              "Índice según {part}:2020.",
    },
    "basis.iso717.plain": {
        "en": "Sound insulation rating per {part}:2020.",
        "es": "Índice de aislamiento acústico según {part}:2020.",
    },
    "basis.iso11654.with_standard": {
        "en": "{standard} laboratory measurement of sound absorption. "
              "Rating per ISO 11654:1997.",
        "es": "{standard} medición en laboratorio de la absorción acústica. "
              "Índice según ISO 11654:1997.",
    },
    "basis.iso11654.plain": {
        "en": "Sound absorption rating per ISO 11654:1997.",
        "es": "Índice de absorción acústica según ISO 11654:1997.",
    },
    "basis.iso532.with_standard": {
        "en": "{standard} loudness. Rating per ISO 532-1:2017 (Zwicker method).",
        "es": "{standard} sonoridad. Índice según ISO 532-1:2017 "
              "(método de Zwicker).",
    },
    "basis.iso532.plain": {
        "en": "Loudness rating per ISO 532-1:2017 (Zwicker method).",
        "es": "Índice de sonoridad según ISO 532-1:2017 (método de Zwicker).",
    },
    "basis.broadcast.with_standard": {
        "en": "{standard} programme loudness. Rating per EBU R 128 / "
              "ITU-R BS.1770-5 (K-weighting, gated).",
        "es": "{standard} sonoridad de programa. Índice según EBU R 128 / "
              "ITU-R BS.1770-5 (ponderación K, con puerta).",
    },
    "basis.broadcast.plain": {
        "en": "Programme loudness per EBU R 128 / ITU-R BS.1770-5 "
              "(K-weighting, gated).",
        "es": "Sonoridad de programa según EBU R 128 / ITU-R BS.1770-5 "
              "(ponderación K, con puerta).",
    },
    "basis.epnl.with_standard": {
        "en": "{standard}. Effective Perceived Noise Level per ICAO Annex 16, "
              "Volume I, Appendix 2.",
        "es": "{standard}. Nivel efectivo de ruido percibido según OACI Anexo 16, "
              "Volumen I, Apéndice 2.",
    },
    "basis.epnl.plain": {
        "en": "Effective Perceived Noise Level (EPNL) per ICAO Annex 16, "
              "Volume I, Appendix 2.",
        "es": "Nivel efectivo de ruido percibido (EPNL) según OACI Anexo 16, "
              "Volumen I, Apéndice 2.",
    },
    "basis.iec61260.with_standard": {
        "en": "{standard} type test. Conformance to {table}.",
        "es": "{standard} ensayo de tipo. Conformidad con {table}.",
    },
    "basis.iec61260.plain": {
        "en": "Conformance to {table}.",
        "es": "Conformidad con {table}.",
    },
    # --- metadata-grid labels --------------------------------------------
    "meta.client": {"en": "Client", "es": "Cliente"},
    "meta.mounted_by": {"en": "Mounted by", "es": "Montado por"},
    "meta.manufacturer": {"en": "Manufacturer", "es": "Fabricante"},
    "meta.manufacturer_tc": {
        "en": "Manufacturer / TC holder",
        "es": "Fabricante / titular del CT",
    },
    "meta.applicant": {"en": "Applicant", "es": "Solicitante"},
    "meta.aircraft": {"en": "Aircraft", "es": "Aeronave"},
    "meta.measurement_point": {"en": "Measurement point", "es": "Punto de medición"},
    "meta.description": {"en": "Description", "es": "Descripción"},
    "meta.signal": {"en": "Signal", "es": "Señal"},
    "meta.programme": {"en": "Programme", "es": "Programa"},
    "meta.filter_instrument": {
        "en": "Filter / instrument",
        "es": "Filtro / instrumento",
    },
    "meta.test_room": {"en": "Test room", "es": "Sala de ensayo"},
    "meta.test_facility": {"en": "Test facility", "es": "Instalación de ensayo"},
    "meta.date_of_test": {"en": "Date of test", "es": "Fecha del ensayo"},
    "meta.mounting": {"en": "Mounting", "es": "Montaje"},
    "meta.sample_area": {
        "en": "Sample area S [m<super>2</super>]",
        "es": "Área de la muestra S [m<super>2</super>]",
    },
    "meta.mass_per_area": {
        "en": "Mass per unit area [kg/m<super>2</super>]",
        "es": "Masa por unidad de superficie [kg/m<super>2</super>]",
    },
    "meta.source_volume": {
        "en": "Source room volume [m<super>3</super>]",
        "es": "Volumen del recinto emisor [m<super>3</super>]",
    },
    "meta.source_temp": {
        "en": "Source room temp. [&#176;C]",
        "es": "Temp. recinto emisor [&#176;C]",
    },
    "meta.source_humidity": {
        "en": "Source room humidity [%]",
        "es": "Humedad recinto emisor [%]",
    },
    "meta.receiving_volume": {
        "en": "Receiving room volume [m<super>3</super>]",
        "es": "Volumen del recinto receptor [m<super>3</super>]",
    },
    "meta.receiving_temp": {
        "en": "Receiving room temp. [&#176;C]",
        "es": "Temp. recinto receptor [&#176;C]",
    },
    "meta.receiving_humidity": {
        "en": "Receiving room humidity [%]",
        "es": "Humedad recinto receptor [%]",
    },
    "meta.temperature": {
        "en": "Temperature [&#176;C]",
        "es": "Temperatura [&#176;C]",
    },
    "meta.relative_humidity": {
        "en": "Relative humidity [%]",
        "es": "Humedad relativa [%]",
    },
    "meta.ambient_pressure": {
        "en": "Ambient pressure [kPa]",
        "es": "Presión ambiente [kPa]",
    },
    # --- table headers ----------------------------------------------------
    "table.frequency": {"en": "Frequency f [Hz]", "es": "Frecuencia f [Hz]"},
    "table.f_hz": {"en": "f [Hz]", "es": "f [Hz]"},
    "table.measured_value": {
        "en": "Measured {vh} [dB]",
        "es": "{vh} medido [dB]",
    },
    "table.value_db": {"en": "{vh} [dB]", "es": "{vh} [dB]"},
    "table.shifted_ref_db": {"en": "Shifted ref. [dB]", "es": "Ref. desplazada [dB]"},
    "table.unfav_dev_db": {"en": "Unfav. dev. [dB]", "es": "Desv. desfav. [dB]"},
    "table.shifted_ref": {"en": "Shifted ref.", "es": "Ref. desplazada"},
    "table.unfav_dev": {"en": "Unfav. dev.", "es": "Desv. desfav."},
    "table.practical_alpha_p": {
        "en": "Practical &#945;<sub>p</sub>",
        "es": "&#945;<sub>p</sub> práctico",
    },
    "table.sum": {"en": "sum", "es": "suma"},
    # --- captions ---------------------------------------------------------
    "caption.one_third_octave_value": {
        "en": "One-third-octave {vh} [dB]",
        "es": "Tercio de octava {vh} [dB]",
    },
    "caption.one_third_octave_alpha": {
        "en": "One-third-octave &#945;<sub>s</sub>, octave &#945;<sub>p</sub>",
        "es": "&#945;<sub>s</sub> en tercio de octava, "
              "&#945;<sub>p</sub> en octava",
    },
    "caption.octave_alpha_p": {
        "en": "Octave-band &#945;<sub>p</sub>",
        "es": "&#945;<sub>p</sub> en banda de octava",
    },
    "caption.loudness_results": {
        "en": "Loudness results",
        "es": "Resultados de sonoridad",
    },
    "caption.compliance_summary": {
        "en": "Compliance summary",
        "es": "Resumen de conformidad",
    },
    "caption.intermediate_quantities": {
        "en": "Intermediate quantities",
        "es": "Cantidades intermedias",
    },
    "caption.per_band_classification": {
        "en": "Per-band classification",
        "es": "Clasificación por bandas",
    },
    "caption.certification_limit": {
        "en": "Certification limit",
        "es": "Límite de certificación",
    },
    # --- compliance-table headers ----------------------------------------
    "col.metric": {"en": "Metric", "es": "Métrica"},
    "col.measured": {"en": "Measured", "es": "Medido"},
    "col.target_limit": {"en": "Target / Limit", "es": "Objetivo / Límite"},
    "col.result": {"en": "Result", "es": "Resultado"},
    # --- verdict / status -------------------------------------------------
    "verdict.pass": {"en": "PASS", "es": "CUMPLE"},
    "verdict.fail": {"en": "FAIL", "es": "NO CUMPLE"},
    "verdict.result_vs_requirement": {
        "en": "Result vs requirement",
        "es": "Resultado frente a requisito",
    },
    "status.informational": {"en": "informational", "es": "informativo"},
    "status.complies": {"en": "COMPLIES", "es": "CUMPLE"},
    "status.does_not_comply": {"en": "Does not comply", "es": "No cumple"},
    # --- metric-row labels ------------------------------------------------
    "metric.total_loudness": {
        "en": "Total loudness N [sone]",
        "es": "Sonoridad total N [sone]",
    },
    "metric.loudness_level": {
        "en": "Loudness level L<sub>N</sub> [phon]",
        "es": "Nivel de sonoridad L<sub>N</sub> [phon]",
    },
    "metric.n5": {"en": "N<sub>5</sub> [sone]", "es": "N<sub>5</sub> [sone]"},
    "metric.n10": {"en": "N<sub>10</sub> [sone]", "es": "N<sub>10</sub> [sone]"},
    "metric.pnltm": {"en": "PNLTM [PNdB]", "es": "PNLTM [PNdB]"},
    "metric.duration_correction": {
        "en": "Duration correction D [dB]",
        "es": "Corrección de duración D [dB]",
    },
    "metric.window_10db_down": {
        "en": "10 dB-down window (records)",
        "es": "Ventana 10 dB por debajo (registros)",
    },
    "metric.bandsharing": {
        "en": "Bandsharing adjustment [dB]",
        "es": "Ajuste por reparto de bandas [dB]",
    },
    "metric.integrated_loudness": {
        "en": "Integrated (Programme) Loudness",
        "es": "Sonoridad integrada (de programa)",
    },
    "metric.max_true_peak": {
        "en": "Maximum True Peak",
        "es": "Pico real máximo",
    },
    "metric.loudness_range": {
        "en": "Loudness Range (LRA)",
        "es": "Rango de sonoridad (LRA)",
    },
    "metric.max_momentary": {"en": "Max Momentary", "es": "Momentánea máxima"},
    "metric.max_short_term": {"en": "Max Short-term", "es": "Corto plazo máxima"},
    "metric.epnl": {"en": "EPNL [EPNdB]", "es": "EPNL [EPNdB]"},
    # --- iso717 verdict ---------------------------------------------------
    "iso717.verdict.impact": {
        "en": "L<sub>n,w</sub> = {rating} dB, required &#8804; {req} dB",
        "es": "L<sub>n,w</sub> = {rating} dB, exigido &#8804; {req} dB",
    },
    "iso717.verdict.airborne": {
        "en": "R<sub>w</sub> = {rating} dB, required &#8805; {req} dB",
        "es": "R<sub>w</sub> = {rating} dB, exigido &#8805; {req} dB",
    },
    # --- iso11654 statement / verdict ------------------------------------
    "iso11654.absorption_class": {
        "en": "Absorption class: {value}",
        "es": "Clase de absorción: {value}",
    },
    "iso11654.shape_indicator": {
        "en": "Shape indicator: {value}",
        "es": "Indicador de forma: {value}",
    },
    "iso11654.applied_shift": {
        "en": "Applied shift: {value}",
        "es": "Desplazamiento aplicado: {value}",
    },
    "iso11654.verdict": {
        "en": "&#945;<sub>w</sub> = {value}, required &#8805; {req}",
        "es": "&#945;<sub>w</sub> = {value}, exigido &#8805; {req}",
    },
    # --- iso532 verdict ---------------------------------------------------
    "iso532.verdict": {
        "en": "N = {value} sone, required &#8804; {req} sone",
        "es": "N = {value} sone, exigido &#8804; {req} sone",
    },
    # --- broadcast --------------------------------------------------------
    "broadcast.limit.integrated": {
        "en": "{target} LUFS &#177;{tol} LU (&#916; {delta} LU)",
        "es": "{target} LUFS &#177;{tol} LU (&#916; {delta} LU)",
    },
    "broadcast.limit.true_peak": {
        "en": "&#8804; {limit} dBTP",
        "es": "&#8804; {limit} dBTP",
    },
    "broadcast.verdict": {
        "en": "Compliant when I is within {target} &#177;{tol} LU and true "
              "peak &#8804; {tp} dBTP",
        "es": "Conforme cuando I está dentro de {target} &#177;{tol} LU y el "
              "pico real &#8804; {tp} dBTP",
    },
    "broadcast.basis_strip": {
        "en": "Gating -70 LUFS absolute / -10 LU relative (ITU-R BS.1770); "
              "1 LU = 1 dB; true peak per EBU Tech 3341; LRA per EBU Tech 3342 "
              "(not recommended for programmes under 60 s).",
        "es": "Puerta -70 LUFS absoluta / -10 LU relativa (ITU-R BS.1770); "
              "1 LU = 1 dB; pico real según EBU Tech 3341; LRA según "
              "EBU Tech 3342 (no recomendado para programas de menos de 60 s).",
    },
    # --- epnl -------------------------------------------------------------
    "epnl.limit_cell": {
        "en": "&#8804; {limit} (margin {margin})",
        "es": "&#8804; {limit} (margen {margin})",
    },
    "epnl.reference_conditions": {
        "en": "Reference conditions: 25 &#176;C, 70% relative humidity, sea "
              "level, zero wind, ISA (ICAO Annex 16 Vol I App. 2).",
        "es": "Condiciones de referencia: 25 &#176;C, 70% de humedad relativa, "
              "nivel del mar, viento nulo, ISA (OACI Anexo 16 Vol I Ap. 2).",
    },
    "epnl.certificate_disclaimer": {
        "en": "This is a computational EPNL result per ICAO Annex 16 Vol I "
              "Appendix 2; it is not an official State noise certificate "
              "(e.g. EASA Form 45).",
        "es": "Este es un resultado EPNL calculado según OACI Anexo 16 Vol I "
              "Apéndice 2; no es un certificado oficial de ruido de un Estado "
              "(p. ej. EASA Formulario 45).",
    },
    # --- iec61260 ---------------------------------------------------------
    "iec61260.basis_strip": {
        "en": "{fraction} bank, sampling rate f<sub>s</sub> = {fs} Hz; "
              "relative attenuation referenced to the mid-band level "
              "(IEC 61260-1 Formula 8).",
        "es": "Banco {fraction}, frecuencia de muestreo f<sub>s</sub> = {fs} Hz; "
              "atenuación relativa referida al nivel de banda media "
              "(IEC 61260-1 Fórmula 8).",
    },
    "iec61260.class_none": {"en": "none", "es": "ninguna"},
    "iec61260.class_n": {"en": "Class {n}", "es": "Clase {n}"},
    "iec61260.statement.complies": {
        "en": "Class <b>{cls}</b> - COMPLIES &nbsp; (margin {margin} dB)",
        "es": "Clase <b>{cls}</b> - CUMPLE &nbsp; (margen {margin} dB)",
    },
    "iec61260.statement.does_not_comply": {
        "en": "<b>Does not comply</b> with class {classes} &nbsp; "
              "(closest margin {margin} dB)",
        "es": "<b>No cumple</b> con la clase {classes} &nbsp; "
              "(margen más próximo {margin} dB)",
    },
    "iec61260.verdict": {
        "en": "Achieved class {achieved}, required class {required}",
        "es": "Clase obtenida {achieved}, clase exigida {required}",
    },
    # --- footer -----------------------------------------------------------
    "footer.laboratory": {"en": "Laboratory", "es": "Laboratorio"},
    "footer.report_no": {"en": "Report no.", "es": "Informe n.º"},
    "footer.date": {"en": "Date", "es": "Fecha"},
    "footer.notes": {"en": "Notes", "es": "Notas"},
    "footer.operator": {"en": "Operator", "es": "Operador"},
    "footer.signature": {"en": "Signature", "es": "Firma"},
    "footer.disclaimer": {
        "en": "The results relate only to the tested specimen.",
        "es": "Los resultados se refieren únicamente a la probeta ensayada.",
    },
    "footer.generated_by": {
        "en": "Generated by phonometry.",
        "es": "Generado por phonometry.",
    },
}


def t(key: str, language: str = "en") -> str:
    """Return the ``language`` rendering of the fixed string ``key``.

    Falls back to the English string when the language is not translated, and
    raises :class:`KeyError` for an unknown ``key`` (a programming error).

    :param key: A stable English string-id present in :data:`REPORT_STRINGS`.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The translated string (English if the language has no entry).
    """
    forms = REPORT_STRINGS[key]
    return forms.get(language, forms["en"])


def format_number(
    value: float,
    language: str = "en",
    *,
    decimals: int = 1,
    trim: bool = False,
) -> str:
    """Locale-aware number formatting for the renderers (level-1 re-export).

    Thin wrapper around :func:`phonometry._i18n.format_number` so the report
    renderers, which must not import the top-level ``_i18n`` at module level
    (the package-architecture rule keeps the render leaves free of module-level
    parent imports), reach it through a sibling module instead. The import is
    lazy for the same reason.
    """
    from .._i18n import format_number as _format_number

    return _format_number(value, language, decimals=decimals, trim=trim)


def decimal_comma(value: str, language: str = "en") -> str:
    """Locale-aware separator swap for the renderers (level-1 re-export).

    Thin wrapper around :func:`phonometry._i18n.decimal_comma`; see
    :func:`format_number` for why the renderers reach it through this module.
    """
    from .._i18n import decimal_comma as _decimal_comma

    return _decimal_comma(value, language)
