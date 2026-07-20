#  Copyright (c) 2026. Jose M. Requena-Plens
"""Translated fixed strings for the accredited ``.report()`` fiches.

Every fixed English string the six report renderers emit (titles, standard-basis
line templates, table headers, metadata-grid labels, metric-row labels, verdict
prose and the footer identity/disclaimer block) is keyed here by its own
verbatim English text and mapped to its Spanish form. English is the default
and is byte-for-byte unchanged; passing ``language="es"`` to a result's
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

#: Spanish translations of the fixed strings rendered by the accredited
#: ``.report()`` fiches, keyed by their verbatim English text. ``t`` returns
#: the English key unchanged for any language other than ``"es"``, so the
#: English output is byte-for-byte identical to the pre-i18n renderers.
_STRINGS: dict[str, str] = {
    # --- titles ----------------------------------------------------------
    "Airborne sound insulation rating": "Índice de aislamiento acústico a ruido aéreo",
    "Impact sound insulation rating": "Índice de aislamiento acústico a ruido de impactos",
    "Sound absorption rating": "Índice de absorción acústica",
    "Loudness rating": "Índice de sonoridad",
    "Programme loudness compliance": "Conformidad de sonoridad de programa",
    "Aircraft noise certification - EPNL result": "Certificación de ruido de aeronaves - resultado EPNL",
    "Filter class compliance": "Conformidad de clase de filtro",
    # --- standard-basis line templates -----------------------------------
    "{standard} laboratory measurement of sound insulation. Rating per {part}:2020.": "{standard} medición en laboratorio del aislamiento acústico. Índice según {part}:2020.",
    "Sound insulation rating per {part}:2020.": "Índice de aislamiento acústico según {part}:2020.",
    "{standard} laboratory measurement of sound absorption. Rating per ISO 11654:1997.": "{standard} medición en laboratorio de la absorción acústica. Índice según ISO 11654:1997.",
    "Sound absorption rating per ISO 11654:1997.": "Índice de absorción acústica según ISO 11654:1997.",
    "{standard} loudness. Rating per ISO 532-1:2017 (Zwicker method).": "{standard} sonoridad. Índice según ISO 532-1:2017 (método de Zwicker).",
    "Loudness rating per ISO 532-1:2017 (Zwicker method).": "Índice de sonoridad según ISO 532-1:2017 (método de Zwicker).",
    "{standard} programme loudness. Rating per EBU R 128 / ITU-R BS.1770-5 (K-weighting, gated).": "{standard} sonoridad de programa. Índice según EBU R 128 / ITU-R BS.1770-5 (ponderación K, con puerta).",
    "Programme loudness per EBU R 128 / ITU-R BS.1770-5 (K-weighting, gated).": "Sonoridad de programa según EBU R 128 / ITU-R BS.1770-5 (ponderación K, con puerta).",
    "{standard}. Effective Perceived Noise Level per ICAO Annex 16, Volume I, Appendix 2.": "{standard}. Nivel efectivo de ruido percibido según OACI Anexo 16, Volumen I, Apéndice 2.",
    "Effective Perceived Noise Level (EPNL) per ICAO Annex 16, Volume I, Appendix 2.": "Nivel efectivo de ruido percibido (EPNL) según OACI Anexo 16, Volumen I, Apéndice 2.",
    "{standard} type test. Conformance to {table}.": "{standard} ensayo de tipo. Conformidad con {table}.",
    "Conformance to {table}.": "Conformidad con {table}.",
    # --- metadata-grid labels --------------------------------------------
    "Client": "Cliente",
    "Mounted by": "Montado por",
    "Manufacturer": "Fabricante",
    "Manufacturer / TC holder": "Fabricante / titular del CT",
    "Applicant": "Solicitante",
    "Aircraft": "Aeronave",
    "Measurement point": "Punto de medición",
    "Description": "Descripción",
    "Signal": "Señal",
    "Programme": "Programa",
    "Filter / instrument": "Filtro / instrumento",
    "Test room": "Sala de ensayo",
    "Test facility": "Instalación de ensayo",
    "Date of test": "Fecha del ensayo",
    "Mounting": "Montaje",
    "Sample area S [m<super>2</super>]": "Área de la muestra S [m<super>2</super>]",
    "Mass per unit area [kg/m<super>2</super>]": "Masa por unidad de superficie [kg/m<super>2</super>]",
    "Source room volume [m<super>3</super>]": "Volumen del recinto emisor [m<super>3</super>]",
    "Source room temp. [&#176;C]": "Temp. recinto emisor [&#176;C]",
    "Source room humidity [%]": "Humedad recinto emisor [%]",
    "Receiving room volume [m<super>3</super>]": "Volumen del recinto receptor [m<super>3</super>]",
    "Receiving room temp. [&#176;C]": "Temp. recinto receptor [&#176;C]",
    "Receiving room humidity [%]": "Humedad recinto receptor [%]",
    "Temperature [&#176;C]": "Temperatura [&#176;C]",
    "Relative humidity [%]": "Humedad relativa [%]",
    "Ambient pressure [kPa]": "Presión ambiente [kPa]",
    # --- table headers ----------------------------------------------------
    "Frequency f [Hz]": "Frecuencia f [Hz]",
    "f [Hz]": "f [Hz]",
    "Measured {vh} [dB]": "{vh} medido [dB]",
    "{vh} [dB]": "{vh} [dB]",
    "Shifted ref. [dB]": "Ref. desplazada [dB]",
    "Unfav. dev. [dB]": "Desv. desfav. [dB]",
    "Shifted ref.": "Ref. desplazada",
    "Unfav. dev.": "Desv. desfav.",
    "Practical &#945;<sub>p</sub>": "&#945;<sub>p</sub> práctico",
    "sum": "suma",
    # --- captions ---------------------------------------------------------
    "One-third-octave {vh} [dB]": "Tercio de octava {vh} [dB]",
    "One-third-octave &#945;<sub>s</sub>, octave &#945;<sub>p</sub>": "&#945;<sub>s</sub> en tercio de octava, &#945;<sub>p</sub> en octava",
    "Octave-band &#945;<sub>p</sub>": "&#945;<sub>p</sub> en banda de octava",
    "Loudness results": "Resultados de sonoridad",
    "Compliance summary": "Resumen de conformidad",
    "Intermediate quantities": "Cantidades intermedias",
    "Per-band classification": "Clasificación por bandas",
    "Certification limit": "Límite de certificación",
    # --- compliance-table headers ----------------------------------------
    "Metric": "Métrica",
    "Measured": "Medido",
    "Target / Limit": "Objetivo / Límite",
    "Result": "Resultado",
    # --- verdict / status -------------------------------------------------
    "PASS": "CUMPLE",  # nosec B105 - report verdict label, not a password
    "FAIL": "NO CUMPLE",
    "Result vs requirement": "Resultado frente a requisito",
    "informational": "informativo",
    "COMPLIES": "CUMPLE",
    "Does not comply": "No cumple",
    # --- metric-row labels ------------------------------------------------
    "Total loudness N [sone]": "Sonoridad total N [sone]",
    "Loudness level L<sub>N</sub> [phon]": "Nivel de sonoridad L<sub>N</sub> [phon]",
    "N<sub>5</sub> [sone]": "N<sub>5</sub> [sone]",
    "N<sub>10</sub> [sone]": "N<sub>10</sub> [sone]",
    "PNLTM [PNdB]": "PNLTM [PNdB]",
    "Duration correction D [dB]": "Corrección de duración D [dB]",
    "10 dB-down window (records)": "Ventana 10 dB por debajo (registros)",
    "Bandsharing adjustment [dB]": "Ajuste por reparto de bandas [dB]",
    "Integrated (Programme) Loudness": "Sonoridad integrada (de programa)",
    "Maximum True Peak": "Pico real máximo",
    "Loudness Range (LRA)": "Rango de sonoridad (LRA)",
    "Max Momentary": "Momentánea máxima",
    "Max Short-term": "Corto plazo máxima",
    "EPNL [EPNdB]": "EPNL [EPNdB]",
    # --- iso717 verdict ---------------------------------------------------
    "L<sub>n,w</sub> = {rating} dB, required &#8804; {req} dB": "L<sub>n,w</sub> = {rating} dB, exigido &#8804; {req} dB",
    "R<sub>w</sub> = {rating} dB, required &#8805; {req} dB": "R<sub>w</sub> = {rating} dB, exigido &#8805; {req} dB",
    # --- iso11654 statement / verdict ------------------------------------
    "Absorption class: {value}": "Clase de absorción: {value}",
    "Shape indicator: {value}": "Indicador de forma: {value}",
    "Applied shift: {value}": "Desplazamiento aplicado: {value}",
    "&#945;<sub>w</sub> = {value}, required &#8805; {req}": "&#945;<sub>w</sub> = {value}, exigido &#8805; {req}",
    # --- iso532 verdict ---------------------------------------------------
    "N = {value} sone, required &#8804; {req} sone": "N = {value} sone, exigido &#8804; {req} sone",
    # --- broadcast --------------------------------------------------------
    "{target} LUFS &#177;{tol} LU (&#916; {delta} LU)": "{target} LUFS &#177;{tol} LU (&#916; {delta} LU)",
    "&#8804; {limit} dBTP": "&#8804; {limit} dBTP",
    "Compliant when I is within {target} &#177;{tol} LU and true peak &#8804; {tp} dBTP": "Conforme cuando I está dentro de {target} &#177;{tol} LU y el pico real &#8804; {tp} dBTP",
    "Gating -70 LUFS absolute / -10 LU relative (ITU-R BS.1770); 1 LU = 1 dB; true peak per EBU Tech 3341; LRA per EBU Tech 3342 (not recommended for programmes under 60 s).": "Puerta -70 LUFS absoluta / -10 LU relativa (ITU-R BS.1770); 1 LU = 1 dB; pico real según EBU Tech 3341; LRA según EBU Tech 3342 (no recomendado para programas de menos de 60 s).",
    # --- epnl -------------------------------------------------------------
    "&#8804; {limit} (margin {margin})": "&#8804; {limit} (margen {margin})",
    "Reference conditions: 25 &#176;C, 70% relative humidity, sea level, zero wind, ISA (ICAO Annex 16 Vol I App. 2).": "Condiciones de referencia: 25 &#176;C, 70% de humedad relativa, nivel del mar, viento nulo, ISA (OACI Anexo 16 Vol I Ap. 2).",
    "This is a computational EPNL result per ICAO Annex 16 Vol I Appendix 2; it is not an official State noise certificate (e.g. EASA Form 45).": "Este es un resultado EPNL calculado según OACI Anexo 16 Vol I Apéndice 2; no es un certificado oficial de ruido de un Estado (p. ej. EASA Formulario 45).",
    # --- iec61260 ---------------------------------------------------------
    "{fraction} bank, sampling rate f<sub>s</sub> = {fs} Hz; relative attenuation referenced to the mid-band level (IEC 61260-1 Formula 8).": "Banco {fraction}, frecuencia de muestreo f<sub>s</sub> = {fs} Hz; atenuación relativa referida al nivel de banda media (IEC 61260-1 Fórmula 8).",
    "none": "ninguna",
    "Class {n}": "Clase {n}",
    "Class <b>{cls}</b> - COMPLIES &nbsp; (margin {margin} dB)": "Clase <b>{cls}</b> - CUMPLE &nbsp; (margen {margin} dB)",
    "<b>Does not comply</b> with class {classes} &nbsp; (closest margin {margin} dB)": "<b>No cumple</b> con la clase {classes} &nbsp; (margen más próximo {margin} dB)",
    "Achieved class {achieved}, required class {required}": "Clase obtenida {achieved}, clase exigida {required}",
    # --- footer -----------------------------------------------------------
    "Laboratory": "Laboratorio",
    "Report no.": "Informe n.º",
    "Date": "Fecha",
    "Notes": "Notas",
    "Operator": "Operador",
    "Signature": "Firma",
    "The results relate only to the tested specimen.": "Los resultados se refieren únicamente a la probeta ensayada.",
    "Generated by phonometry.": "Generado por phonometry.",
}


def t(text: str, language: str = "en") -> str:
    """Localise a fixed report string; English is returned verbatim (byte-identical).

    :param text: The exact English display string, doubling as the lookup key.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The translated string (English unchanged for any other language).
    """
    return _STRINGS.get(text, text) if language == "es" else text


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
