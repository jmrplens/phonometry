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
    "Field airborne sound insulation between rooms": "Aislamiento acústico a ruido aéreo entre recintos in situ",
    "Field impact sound insulation of floors": "Aislamiento acústico a ruido de impactos de suelos in situ",
    # --- standard-basis line templates -----------------------------------
    "{standard} laboratory measurement of sound insulation. Rating per {part}:2020.": "{standard} medición en laboratorio del aislamiento acústico. Índice según {part}:2020.",
    "Sound insulation rating per {part}:2020.": "Índice de aislamiento acústico según {part}:2020.",
    "Standardized level difference D<sub>nT</sub> measured in accordance with ISO 16283-1:2014 (field measurement). Rating per ISO 717-1:2020.": "Diferencia de niveles estandarizada D<sub>nT</sub> medida de acuerdo con la Norma ISO 16283-1:2014 (medición in situ). Índice según ISO 717-1:2020.",
    "Apparent sound reduction index R&#8242; measured in accordance with ISO 16283-1:2014 (field measurement). Rating per ISO 717-1:2020.": "Índice de reducción acústica aparente R&#8242; medido de acuerdo con la Norma ISO 16283-1:2014 (medición in situ). Índice según ISO 717-1:2020.",
    "Standardized impact sound pressure level L&#8242;<sub>nT</sub> measured in accordance with ISO 16283-2:2020 using the tapping machine. Rating per ISO 717-2:2020.": "Nivel de presión acústica de impactos estandarizado L&#8242;<sub>nT</sub> medido de acuerdo con la Norma ISO 16283-2:2020 con la máquina de impactos. Índice según ISO 717-2:2020.",
    "Normalized impact sound pressure level L&#8242;<sub>n</sub> measured in accordance with ISO 16283-2:2020 using the tapping machine. Rating per ISO 717-2:2020.": "Nivel de presión acústica de impactos normalizado L&#8242;<sub>n</sub> medido de acuerdo con la Norma ISO 16283-2:2020 con la máquina de impactos. Índice según ISO 717-2:2020.",
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
    # --- iso16283 field fiches --------------------------------------------
    "Per-band measurement chain": "Cadena de medición por bandas",
    "Evaluation based on field measurement using results obtained by an engineering method.": "Evaluación basada en resultados de medidas in situ obtenidos mediante un método de ingeniería.",
    "Evaluation based on field measurement results obtained by an engineering method.": "Evaluación basada en resultados de medidas in situ obtenidos mediante un método de ingeniería.",
    "{sym} = {rating} dB, required &#8805; {req} dB": "{sym} = {rating} dB, exigido &#8805; {req} dB",
    "{sym} = {rating} dB, required &#8804; {req} dB": "{sym} = {rating} dB, exigido &#8804; {req} dB",
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
    # --- iso4871 ----------------------------------------------------------
    "Noise emission declaration": "Declaración de emisión sonora",
    "Declaration and verification of noise emission values per ISO 4871:1996; values determined per {standard}.": "Declaración y verificación de valores de emisión sonora según ISO 4871:1996; valores determinados según {standard}.",
    "Declaration and verification of noise emission values per ISO 4871:1996.": "Declaración y verificación de valores de emisión sonora según ISO 4871:1996.",
    "Machine model number, operating conditions, and other identifying information:": "Número de modelo de la máquina, condiciones de funcionamiento y otra información identificativa:",
    "DECLARED DUAL-NUMBER NOISE EMISSION VALUES": "VALORES DECLARADOS DE EMISIÓN SONORA DE DOBLE NÚMERO",
    "DECLARED SINGLE-NUMBER NOISE EMISSION VALUES": "VALORES DECLARADOS DE EMISIÓN SONORA DE NÚMERO ÚNICO",
    "in accordance with ISO 4871:1996": "de acuerdo con ISO 4871:1996",
    "Measured A-weighted sound power level, L<sub>WA</sub> (ref. 1 pW), in decibels": "Nivel de potencia acústica ponderado A medido, L<sub>WA</sub> (ref. 1 pW), en decibelios",
    "Uncertainty, K<sub>WA</sub>, in decibels": "Incertidumbre, K<sub>WA</sub>, en decibelios",
    "Measured A-weighted emission sound pressure level, L<sub>pA</sub> (ref. 20 &#181;Pa) at the work station, in decibels": "Nivel de presión acústica de emisión ponderado A medido, L<sub>pA</sub> (ref. 20 &#181;Pa) en el puesto de trabajo, en decibelios",
    "Uncertainty, K<sub>pA</sub>, in decibels": "Incertidumbre, K<sub>pA</sub>, en decibelios",
    "Declared A-weighted sound power level, L<sub>WAd</sub> = L<sub>WA</sub> + K<sub>WA</sub>, in decibels": "Nivel de potencia acústica ponderado A declarado, L<sub>WAd</sub> = L<sub>WA</sub> + K<sub>WA</sub>, en decibelios",
    "A-weighted sound power level, L<sub>WAd</sub> (ref. 1 pW), in decibels": "Nivel de potencia acústica ponderado A, L<sub>WAd</sub> (ref. 1 pW), en decibelios",
    "A-weighted emission sound pressure level, L<sub>pAd</sub> (ref. 20 &#181;Pa) at the work station, in decibels": "Nivel de presión acústica de emisión ponderado A, L<sub>pAd</sub> (ref. 20 &#181;Pa) en el puesto de trabajo, en decibelios",
    "Values determined according to noise test code {code}, using the basic standard(s) {standards}.": "Valores determinados según el código de ensayo de ruido {code}, utilizando la(s) norma(s) básica(s) {standards}.",
    "Values determined using the basic standard(s) {standards}.": "Valores determinados utilizando la(s) norma(s) básica(s) {standards}.",
    "Values determined according to noise test code {code}.": "Valores determinados según el código de ensayo de ruido {code}.",
    "Values determined in accordance with ISO 4871:1996.": "Valores determinados de acuerdo con ISO 4871:1996.",
    "NOTE The sum of a measured noise emission value and its associated uncertainty represents an upper boundary of the range of values which is likely to occur in measurements.": "NOTA La suma de un valor de emisión sonora medido y su incertidumbre asociada representa un límite superior del intervalo de valores que probablemente se produzca en las mediciones.",
    "NOTE Declared single-number noise emission values are the sum of measured values and the associated uncertainty, and represent upper boundaries of the range of values which is likely to occur in measurements.": "NOTA Los valores declarados de emisión sonora de número único son la suma de los valores medidos y la incertidumbre asociada, y representan límites superiores del intervalo de valores que probablemente se produzca en las mediciones.",
    "Verification (ISO 4871 clause 6.2)": "Verificación (ISO 4871 apartado 6.2)",
    "A-weighted sound power level, {mode}": "Nivel de potencia acústica ponderado A, {mode}",
    "L<sub>1</sub> = {l1} dB": "L<sub>1</sub> = {l1} dB",
    "&#8804; L<sub>WAd</sub> = {ld} dB": "&#8804; L<sub>WAd</sub> = {ld} dB",
    # --- iec60268-5 loudspeaker -------------------------------------------
    "Loudspeaker characteristics": "Características del altavoz",
    "{standard} measurement of loudspeaker rated characteristics per IEC 60268-5:2003+A1:2007; frequency and polar graphs to IEC 60263:1982.": "{standard} medición de las características nominales del altavoz según IEC 60268-5:2003+A1:2007; gráficas de frecuencia y polares según IEC 60263:1982.",
    "Loudspeaker rated characteristics per IEC 60268-5:2003+A1:2007; frequency and polar graphs to IEC 60263:1982.": "Características nominales del altavoz según IEC 60268-5:2003+A1:2007; gráficas de frecuencia y polares según IEC 60263:1982.",
    "Rated characteristics": "Características nominales",
    "Rated impedance": "Impedancia nominal",
    "Characteristic sensitivity": "Sensibilidad característica",
    "Effective frequency range": "Rango de frecuencias efectivo",
    "Rated frequency range": "Rango de frecuencias nominal",
    "Resonance frequency": "Frecuencia de resonancia",
    "Rated noise power": "Potencia de ruido nominal",
    "Rated sinusoidal power": "Potencia sinusoidal nominal",
    "Minimum impedance": "Impedancia mínima",
    "Directivity index": "Índice de directividad",
    "Directivity index at {freq} Hz": "Índice de directividad a {freq} Hz",
    "Tolerance ±{tol} dB": "Tolerancia ±{tol} dB",
    "−10 dB reference": "Referencia −10 dB",
    "On-axis response": "Respuesta en el eje",
    "Effective range": "Rango efectivo",
    "Frequency [Hz]": "Frecuencia [Hz]",
    "Sound pressure level [dB]": "Nivel de presión sonora [dB]",
    "80 % of rated": "80 % de la nominal",
    "Impedance |Z| [{ohm}]": "Impedancia |Z| [{ohm}]",
    "Impedance": "Impedancia",
    "THD [%]": "THD [%]",
    "Total harmonic distortion": "Distorsión armónica total",
    "Directional response": "Respuesta direccional",
    "Directional response at {freq} Hz": "Respuesta direccional a {freq} Hz",
    "Characteristic sensitivity <b>{level} dB</b> (1 W / 1 m); effective frequency range <b>{range}</b>": "Sensibilidad característica <b>{level} dB</b> (1 W / 1 m); rango de frecuencias efectivo <b>{range}</b>",
    "Characteristic sensitivity {level} dB, required &#8805; {req} dB": "Sensibilidad característica {level} dB, exigido &#8805; {req} dB",
    # --- iec60268-4 microphone --------------------------------------------
    "Microphone characteristics": "Características del micrófono",
    "{standard} measurement of microphone rated characteristics per IEC 60268-4:2014; frequency and polar graphs to IEC 60263:1982.": "{standard} medición de las características nominales del micrófono según IEC 60268-4:2014; gráficas de frecuencia y polares según IEC 60263:1982.",
    "Microphone rated characteristics per IEC 60268-4:2014; frequency and polar graphs to IEC 60263:1982.": "Características nominales del micrófono según IEC 60268-4:2014; gráficas de frecuencia y polares según IEC 60263:1982.",
    "Free-field sensitivity": "Sensibilidad en campo libre",
    "Level re 1 V/Pa [dB]": "Nivel re 1 V/Pa [dB]",
    "Min. load impedance": "Impedancia de carga mín.",
    "Equivalent noise level": "Ruido equivalente",
    "Signal-to-noise ratio": "Relación señal-ruido",
    "Max. SPL ({thd} % THD)": "SPL máx. ({thd} % THD)",
    "Max. SPL": "SPL máx.",
    "Powering": "Alimentación",
    "Supply current [mA]": "Corriente de alim. [mA]",
    "Reference frequency": "Frecuencia de referencia",
    "Free-field response": "Respuesta en campo libre",
    "Relative response [dB]": "Respuesta relativa [dB]",
    "Band level [dB]": "Nivel de banda [dB]",
    "Inherent noise spectrum": "Espectro de ruido inherente",
    "{thd} % limit": "Límite del {thd} %",
    "Free-field sensitivity <b>{mv} mV/Pa</b> ({level} dB re 1 V/Pa at {freq} Hz); effective frequency range <b>{range}</b> (±{tol} dB)": "Sensibilidad en campo libre <b>{mv} mV/Pa</b> ({level} dB re 1 V/Pa a {freq} Hz); rango de frecuencias efectivo <b>{range}</b> (±{tol} dB)",
    "Equivalent noise level {level} dB({w}), required &#8804; {req} dB({w})": "Nivel de ruido equivalente {level} dB({w}), exigido &#8804; {req} dB({w})",
    # --- footer -----------------------------------------------------------
    "Laboratory": "Laboratorio",
    "Report no.": "Informe n.º",
    "Date": "Fecha",
    "Notes": "Notas",
    "Operator": "Operador",
    "Signature": "Firma",
    "The results relate only to the tested specimen.": "Los resultados se refieren únicamente a la probeta ensayada.",
    "Generated by phonometry.": "Generado por phonometry.",
    # --- broadcast tolerance rules (EBU R 128 items h / i) -----------------
    "Compliant when I is within {target} LUFS &#177;{tol} LU (EBU R 128 {clause}) and true peak &#8804; {tp} dBTP": "Conforme cuando I está dentro de {target} LUFS &#177;{tol} LU (EBU R 128 {clause}) y el pico real &#8804; {tp} dBTP",
    "Loudness tolerance &#177;0.2 LU for measurement errors in loudness workflows, e.g. Quality Control (EBU R 128 item i).": "Tolerancia de sonoridad &#177;0,2 LU para errores de medida en flujos de trabajo de sonoridad, p. ej. control de calidad (EBU R 128 item i).",
    "Loudness tolerance &#177;1.0 LU, permitted where the Target Level is not achievable practically, e.g. live programmes (EBU R 128 item h).": "Tolerancia de sonoridad &#177;1,0 LU, permitida cuando el nivel objetivo no es alcanzable en la práctica, p. ej. programas en directo (EBU R 128 item h).",
    # --- iso532 clause 7 report items --------------------------------------
    "{standard} loudness. Rating per ISO 532-1:2017 (Zwicker method), {method}.": "{standard} sonoridad. Índice según ISO 532-1:2017 (método de Zwicker), {method}.",
    "Loudness rating per ISO 532-1:2017 (Zwicker method), {method}.": "Índice de sonoridad según ISO 532-1:2017 (método de Zwicker), {method}.",
    "method for stationary sounds (clause 5)": "método para sonidos estacionarios (apartado 5)",
    "method for time-varying sounds (clause 6)": "método para sonidos variables en el tiempo (apartado 6)",
    "Sound field: {field}.": "Campo sonoro: {field}.",
    "free (F)": "libre (F)",
    "diffuse (D)": "difuso (D)",
    "Maximum loudness N<sub>max</sub> [sone]": "Sonoridad máxima N<sub>max</sub> [sone]",
    "Loudness versus time N(t) (clause 6.5)": "Sonoridad en función del tiempo N(t) (apartado 6.5)",
    "{sym} = {value} sone, required &#8804; {req} sone": "{sym} = {value} sone, exigido &#8804; {req} sone",
    # --- epnl reference conditions (Annex 16 Vol I Part II, 3.6.1.5) -------
    "Reference conditions: 25 &#176;C (ISA + 10 &#176;C), 70% relative humidity, 1013.25 hPa sea-level pressure, zero wind (ICAO Annex 16 Vol I Part II, 3.6.1.5).": "Condiciones de referencia: 25 &#176;C (ISA + 10 &#176;C), 70% de humedad relativa, presión a nivel del mar de 1013,25 hPa, viento nulo (OACI Anexo 16 Vol I Parte II, 3.6.1.5).",
    # --- iec61260 edition-aware citations and localised fragments ----------
    "IEC 61260-1:2014, Table 1": "IEC 61260-1:2014, Tabla 1",
    "IEC 61260:1995 / ANSI S1.11-2004, Table 1": "IEC 61260:1995 / ANSI S1.11-2004, Tabla 1",
    "1/1-octave": "1/1 de octava",
    "1/{fraction}-octave": "1/{fraction} de octava",
    "{fraction} bank, sampling rate f<sub>s</sub> = {fs} Hz; relative attenuation referenced to the mid-band level (IEC 61260:1995, 3.13 Note).": "Banco {fraction}, frecuencia de muestreo f<sub>s</sub> = {fs} Hz; atenuación relativa referida al nivel de banda media (IEC 61260:1995, Nota de 3.13).",
    "Stop-band limits verified up to each band's processing Nyquist frequency; the multirate anti-aliasing leaves no signal energy beyond it, but the Table 1 limits there are not demonstrated, so the stated class attests the verified frequency range.": "Límites de banda eliminada verificados hasta la frecuencia de Nyquist de proceso de cada banda; el antisolapamiento multitasa no deja energía de señal más allá, pero los límites de la Tabla 1 en esa zona no se demuestran, por lo que la clase indicada acredita el rango de frecuencias verificado.",
    # --- iso717 octave caption and quantity-symbol verdicts ----------------
    "Octave-band {vh} [dB]": "Banda de octava {vh} [dB]",
    # --- iso11654 shape-indicator note (clause 5.3 NOTE) --------------------
    "A shape indicator applies: ISO 11654 (5.3 NOTE) recommends using &#945;<sub>w</sub> in combination with the complete sound absorption coefficient curve, shown above.": "Se aplica un indicador de forma: ISO 11654 (NOTA de 5.3) recomienda usar &#945;<sub>w</sub> junto con la curva completa del coeficiente de absorción acústica, mostrada más arriba.",
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
