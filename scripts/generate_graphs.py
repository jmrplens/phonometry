import os
import sys
from functools import lru_cache
from typing import Any, Literal

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy import signal as scipy_signal

# Add src to path to use the local package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from phonometry import OctaveFilterBank

# Constants for professional styling
# ---------------------------------------------------------------------------
# Language support: every figure is also generated in Spanish ("_es" suffix).
# Translation happens at savefig time by walking the figure's Text artists,
# so the generator functions stay single-language (English) internally.
_LANG = "en"
_LANG_SUFFIX = ""

_ES_EXACT = {
    "Frequency [Hz]": "Frecuencia [Hz]",
    # Emitted by phonometry.filter_design._showfilter (not by this script);
    # do not remove as "orphans".
    "Filter Bank Frequency Response": "Respuesta en frecuencia del banco de filtros",
    "Amplitude [dB]": "Amplitud [dB]",
    "Level [dB]": "Nivel [dB]",
    "Time [s]": "Tiempo [s]",
    "Amplitude": "Amplitud",
    "Error [dB]": "Error [dB]",
    "Group delay [ms]": "Retardo de grupo [ms]",
    "Level re steady state [dB]": "Nivel re estado estacionario [dB]",
    # ISO 18233 excitation signals + recovered impulse response
    "ISO 18233 excitation signals": "Señales de excitación ISO 18233",
    "Exponential sine sweep — waveform":
        "Barrido sinusoidal exponencial — forma de onda",
    "Sweep spectrogram (exponential rise)":
        "Espectrograma del barrido (ascenso exponencial)",
    "MLS magnitude spectrum (flat)": "Espectro de magnitud de la MLS (plano)",
    "Recovered room impulse response (ISO 18233)":
        "Respuesta al impulso de la sala recuperada (ISO 18233)",
    "Amplitude (norm.)": "Amplitud (norm.)",
    "Level re peak [dB]": "Nivel re pico [dB]",
    "Magnitude [dB]": "Magnitud [dB]",
    "Sample": "Muestra",
    "direct sound": "sonido directo",
    "reflections": "reflexiones",
    "Log-magnitude envelope": "Envolvente log-magnitud",
    "Schroeder decay (EDC)": "Decaimiento de Schroeder (EDC)",
    "Normalized Response": "Respuesta normalizada",
    "Normalized frequency  f / fm": "Frecuencia normalizada  f / fm",
    "Relative attenuation \u0394A [dB]": "Atenuaci\u00f3n relativa \u0394A [dB]",
    "Sound pressure level [dB re 20 \u00b5Pa]": "Nivel de presi\u00f3n sonora [dB re 20 \u00b5Pa]",
    "1/3 Octave Band Analysis": "An\u00e1lisis en bandas de octava 1/3",
    "1/3 Octave Spectrogram (Fast windows, 50% overlap)":
        "Espectrograma 1/3 de octava (ventanas Fast, 50 % de solape)",
    "4 kHz Toneburst Response vs IEC 61672-1 Table 4 (FAST)":
        "Respuesta a r\u00e1fagas de 4 kHz vs Tabla 4 de IEC 61672-1 (FAST)",
    "A-Weighting": "Ponderaci\u00f3n A",
    "C-Weighting": "Ponderaci\u00f3n C",
    "Z-Weighting (Flat)": "Ponderaci\u00f3n Z (plana)",
    "G-weighting (ISO 7196)": "Ponderaci\u00f3n G (ISO 7196)",
    "G Frequency Weighting for Infrasound (ISO 7196:1995)":
        "Ponderaci\u00f3n frecuencial G para infrasonido (ISO 7196:1995)",
    "Bessel": "Bessel",
    "Bilinear error": "Error del dise\u00f1o bilineal",
    "Butterworth": "Butterworth",
    "Butterworth (Flat)": "Butterworth (plano)",
    "Butterworth order 6 (1 kHz octave band)":
        "Butterworth de orden 6 (banda de octava de 1 kHz)",
    "Causal filtering (group delay)": "Filtrado causal (retardo de grupo)",
    "Chebyshev I": "Chebyshev I",
    "Chebyshev II": "Chebyshev II",
    "Class 1 lower limit @ 12.5 kHz": "L\u00edmite inferior de clase 1 @ 12,5 kHz",
    "Class 2 minimum attenuation": "Atenuaci\u00f3n m\u00ednima de clase 2",
    "Continuous (whole signal)": "Continuo (se\u00f1al completa)",
    "Elliptic": "El\u00edptico",
    "FAST envelope": "Envolvente FAST",
    "Fast (125ms)": "Fast (125 ms)",
    "Fast level $L_p(t)$": "Nivel Fast $L_p(t)$",
    "Filter Architecture Comparison (Order 6, 1kHz Band)":
        "Comparativa de arquitecturas de filtro (orden 6, banda de 1 kHz)",
    "Forbidden for class 1 (too little attenuation)":
        "Prohibido para clase 1 (atenuaci\u00f3n insuficiente)",
    "Forbidden for class 1 (too much attenuation)":
        "Prohibido para clase 1 (atenuaci\u00f3n excesiva)",
    "Frequency Weighting Curves (IEC 61672-1)":
        "Curvas de ponderaci\u00f3n frecuencial (IEC 61672-1)",
    "Group Delay Comparison (1 kHz Octave Band, Order 6)":
        "Comparativa de retardo de grupo (banda de 1 kHz, orden 6)",
    "Hearing threshold $T_f$ (Table 1)": "Umbral de audici\u00f3n $T_f$ (Tabla 1)",
    "High Pass (LR4)": "Paso alto (LR4)",
    "IEC 61672-1 analytic curve": "Curva anal\u00edtica IEC 61672-1",
    "ISO 7196 Table 2 nominals": "Nominales de la Tabla 2 de ISO 7196",
    "Impulse (35ms/1.5s)": "Impulse (35 ms/1,5 s)",
    "Independent blocks (state reset)": "Bloques independientes (estado reiniciado)",
    "Input Burst (Normalized)": "R\u00e1faga de entrada (normalizada)",
    "Input burst (250 Hz)": "R\u00e1faga de entrada (250 Hz)",
    "Left Channel: Pink Noise": "Canal izquierdo: ruido rosa",
    "Linkwitz-Riley Crossover (4th Order @ 1kHz)":
        "Crossover Linkwitz-Riley (4\u00ba orden @ 1 kHz)",
    "Low Pass (LR4)": "Paso bajo (LR4)",
    "Multichannel Analysis (Stereo Input)": "An\u00e1lisis multicanal (entrada est\u00e9reo)",
    "No state: each block restarts the filter transient":
        "Sin estado: cada bloque reinicia el transitorio del filtro",
    "Normal Equal-Loudness-Level Contours (ISO 226:2023)":
        "L\u00edneas isof\u00f3nicas normales (ISO 226:2023)",
    "Original Signal (250 Hz + 1000 Hz Sum) @ 48 kHz":
        "Se\u00f1al original (suma de 250 Hz + 1000 Hz) @ 48 kHz",
    "Oversampled (high_accuracy=True)": "Sobremuestreado (high_accuracy=True)",
    "Plain bilinear (high_accuracy=False)": "Bilineal simple (high_accuracy=False)",
    "Raw PSD": "PSD sin filtrar",
    "Raw Signal Spectrum (PSD)": "Espectro de la se\u00f1al (PSD)",
    "Relative Attenuation vs IEC 61260-1:2014 Class Limits":
        "Atenuaci\u00f3n relativa vs l\u00edmites de clase de IEC 61260-1:2014",
    "Right Channel: Log Sine Sweep": "Canal derecho: barrido senoidal logar\u00edtmico",
    "Slow (1000ms)": "Slow (1000 ms)",
    "Stateful blocks (state carried)": "Bloques con estado (estado conservado)",
    "Statistical Levels L10 / L50 / L90 (Fast envelope)":
        "Niveles estad\u00edsticos L10 / L50 / L90 (envolvente Fast)",
    "Sum (Flat)": "Suma (plana)",
    "Time Weighting Ballistics (IEC 61672-1)":
        "Ponderaci\u00f3n temporal F/S/I (IEC 61672-1)",
    "Zero-Phase Filtering: Group Delay Elimination (250 Hz Band)":
        "Filtrado de fase cero: eliminaci\u00f3n del retardo de grupo (banda de 250 Hz)",
    "Zoom at -3 dB (Log Scale)": "Zoom en -3 dB (escala log)",
    "Zoom: A-weighting is positive (max +1.27 dB @ 2.5 kHz)":
        "Zoom: la ponderaci\u00f3n A es positiva (m\u00e1x +1,27 dB @ 2,5 kHz)",
    "block boundary:\nfilter transient restarts":
        "frontera de bloque:\nse reinicia el transitorio del filtro",
    "high_accuracy error": "Error con high_accuracy",
    "stateful=True: block outputs equal the continuous result":
        "stateful=True: los bloques igualan el resultado continuo",
    "zero_phase=True (aligned)": "zero_phase=True (alineado)",
    "0 dB @ 10 Hz": "0 dB @ 10 Hz",
    # Scattering coefficient spectrum (ISO 17497-1)
    "Random-incidence scattering coefficient (ISO 17497-1)":
        "Coeficiente de dispersión de incidencia aleatoria (ISO 17497-1)",
    "Scattering coefficient s": "Coeficiente de dispersión s",
    # In-situ road-surface absorption (ISO 13472-1)
    "In-situ road-surface absorption (ISO 13472-1)":
        "Absorción in situ de pavimentos (ISO 13472-1)",
    "Absorption coefficient alpha": "Coeficiente de absorción alpha",
    # Human vibration (ISO 8041-1 / ISO 2631 / ISO 5349 / 2002/44/EC)
    "Whole-body vertical weighting Wk (ISO 8041-1)":
        "Ponderación vertical de cuerpo entero Wk (ISO 8041-1)",
    "Weighting factor [dB]": "Factor de ponderación [dB]",
    "One-third-octave band [Hz]": "Banda de tercio de octava [Hz]",
    "Band audibility": "Audibilidad de banda",
    r"Band audibility $A_i$": r"Audibilidad de banda $A_i$",
    r"Importance-weighted $I_i\,A_i$ (scaled)":
        r"Ponderada por importancia $I_i\,A_i$ (escalada)",
    "r.m.s. acceleration [m/s$^2$]": "Aceleración eficaz [m/s$^2$]",
    "Unweighted $a_i$": "Sin ponderar $a_i$",
    "Weighted $W_i\\,a_i$ (Wk)": "Ponderada $W_i\\,a_i$ (Wk)",
    "Daily exposure A(8) [m/s$^2$]": "Exposición diaria A(8) [m/s$^2$]",
    "brush-saw": "desbrozadora",
    "felling": "tala",
    "stripping": "descortezado",
    # Precision sound power (ISO 3745 / ISO 9614-3)
    "Sound power level LW [dB]": "Nivel de potencia sonora LW [dB]",
    "Non-applicable band": "Banda no aplicable",
    "Stable tone (good coupling)": "Tono estable (buen acoplamiento)",
    "3% AM tone (loose coupling)": "Tono con AM del 3 % (acoplamiento flojo)",
    "IEC 60942:2017 class 1 limit (deviation from mean)":
        "L\u00edmite de clase 1 de IEC 60942:2017 (desviaci\u00f3n de la media)",
    "Calibration Tone Stability Check (IEC 60942:2017, 5.3.3)":
        "Comprobaci\u00f3n de estabilidad del tono de calibraci\u00f3n (IEC 60942:2017, 5.3.3)",
    "F-weighted level re mean [dB]": "Nivel con ponderaci\u00f3n F re media [dB]",
    "Fast level of the event": "Nivel Fast del evento",
    "Leq over the whole event": "Leq de todo el evento",
    "SEL: same energy in 1 s": "SEL: la misma energ\u00eda en 1 s",
    "equal energy": "igual energ\u00eda",
    "Sound Exposure Level: the event normalized to 1 s":
        "Nivel de exposici\u00f3n sonora: el evento normalizado a 1 s",
    "Level [dBFS]": "Nivel [dBFS]",
    "Hourly LAeq": "LAeq horario",
    "Lday (+0 dB)": "Ld\u00eda (+0 dB)",
    "Levening + 5 dB": "Ltarde + 5 dB",
    "Lnight + 10 dB": "Lnoche + 10 dB",
    "Day-Evening-Night Level Lden (ISO 1996-1)":
        "Nivel d\u00eda-tarde-noche Lden (ISO 1996-1)",
    "Hour of day": "Hora del d\u00eda",
    "Averaged FFT spectrum (Hann)": "Espectro FFT promediado (Hann)",
    "Critical band around the tone": "Banda cr\u00edtica en torno al tono",
    "Tone-to-Noise Ratio (ECMA-418-1, clause 11)":
        "Relaci\u00f3n tono-ruido (ECMA-418-1, apartado 11)",
    "Bin power [dB]": "Potencia por bin [dB]",
    "Specific Loudness Pattern (ISO 532-1 Zwicker)":
        "Patr\u00f3n de sonoridad espec\u00edfica (Zwicker, ISO 532-1)",
    "Critical-band rate z [Bark]": "Raz\u00f3n de banda cr\u00edtica z [Bark]",
    "Specific loudness N' [sone/Bark]":
        "Sonoridad espec\u00edfica N' [sonios/Bark]",
    "Shaded area = total loudness N": "\u00c1rea sombreada = sonoridad total N",
    "STI vs Reverberation Time (IEC 60268-16)":
        "STI frente al tiempo de reverberaci\u00f3n (IEC 60268-16)",
    "Reverberation time T60 [s]": "Tiempo de reverberaci\u00f3n T60 [s]",
    "Analytic Schroeder MTF (closed form)":
        "MTF de Schroeder anal\u00edtica (forma cerrada)",
    "Measured (sti_from_impulse_response)":
        "Medido (sti_from_impulse_response)",
    "Annex F rating": "Calificaci\u00f3n del Anexo F",
    "Measured": "Medido",
    "Octave-band center frequency [Hz]":
        "Frecuencia central de banda de octava [Hz]",
    "Octave-band sound pressure level [dB]":
        "Nivel de presi\u00f3n sonora por banda de octava [dB]",
    "Rumble tol. (+5 dB)": "Tol. retumbo (+5 dB)",
    "Hiss tol. (+3 dB)": "Tol. siseo (+3 dB)",
    "ISO 7029 — age-related threshold (male)":
        "ISO 7029 — umbral por edad (hombres)",
    "ISO 389-7 — reference threshold of hearing":
        "ISO 389-7 — umbral de referencia de la audición",
    "Audiometric frequency [Hz]": "Frecuencia audiométrica [Hz]",
    "Median threshold deviation from age 18 [dB]":
        "Desviación mediana del umbral respecto a los 18 años [dB]",
    "Reference threshold [dB]": "Umbral de referencia [dB]",
    "Free-field (frontal)": "Campo libre (frontal)",
    "Diffuse-field": "Campo difuso",
    "ANSI S3.5-1997 — speech spectra by vocal effort":
        "ANSI S3.5-1997 — espectros de voz por esfuerzo vocal",
    "Speech spectrum level [dB SPL]": "Nivel del espectro de voz [dB SPL]",
    "SII vs vocal effort in a fixed noise":
        "SII frente al esfuerzo vocal en un ruido fijo",
    "Onset rate [dB/s]": "Tasa de crecimiento [dB/s]",
    "Predicted prominence $P$": "Prominencia prevista $P$",
    "Adjustment $K_I$ [dB]": "Ajuste $K_I$ [dB]",
    "Adjustment to $L_{Aeq}$": "Ajuste a $L_{Aeq}$",
    "Impulses": "Impulsos",
    "threshold $P = 5$": "umbral $P = 5$",
    "Transmissibility  seat $\\rightarrow$ spine":
        "Transmisibilidad  asiento $\\rightarrow$ columna",
    "Seat-to-spine transfer function":
        "Función de transferencia asiento-columna",
    "Stress variable $R$": "Variable de tensión $R$",
    "Probability of lumbar injury [%]": "Probabilidad de lesión lumbar [%]",
    "Injury probability (Annex C)": "Probabilidad de lesión (Anexo C)",
    "male": "hombre",
    "female": "mujer",
    "Equivalent absorption area $A$ [m$^2$]":
        "Área de absorción equivalente $A$ [m$^2$]",
    "Absorption area (Formula 1)": "Área de absorción (Fórmula 1)",
    "Reverberation time $T$ [s]": "Tiempo de reverberación $T$ [s]",
    "Reverberation time (Formula 5)": "Tiempo de reverberación (Fórmula 5)",
    "bare ceiling": "techo desnudo",
    "acoustic ceiling": "techo acústico",
    "Speech Intelligibility Index": "Índice de inteligibilidad del habla",
    "Normal": "Normal",
    "Raised": "Elevada",
    "Loud": "Fuerte",
    "Shout": "Grito",
    r"ISO 1999 — NIPTS at $L_{EX,8h}$ = 95 dB":
        r"ISO 1999 — NIPTS a $L_{EX,8h}$ = 95 dB",
    "ISO 1999 — HTLAN (male, age 60, 95 dB / 30 yr)":
        "ISO 1999 — HTLAN (hombres, 60 años, 95 dB / 30 años)",
    "Median NIPTS [dB]": "NIPTS mediana [dB]",
    "Hearing threshold level [dB]": "Nivel del umbral de audición [dB]",
    "10-90 % band (40 yr)": "Banda 10-90 % (40 años)",
    "Age (HTLA, ISO 7029)": "Edad (HTLA, ISO 7029)",
    "Noise (NIPTS)": "Ruido (NIPTS)",
    "Age + noise (HTLAN)": "Edad + ruido (HTLAN)",
    "GUM uncertainty budget": "Presupuesto de incertidumbre (GUM)",
    "Contribution to combined uncertainty [dB]":
        "Contribución a la incertidumbre combinada [dB]",
    "Monte Carlo (Suppl 1)": "Monte Carlo (Supl. 1)",
    "GUM Gaussian": "Gaussiana GUM",
    "95 % coverage interval": "Intervalo de cobertura 95 %",
    "A-weighted level [dB]": "Nivel ponderado A [dB]",
    "Probability density": "Densidad de probabilidad",
    "Reading": "Lectura",
    "Calibration": "Calibración",
    "Instrument": "Instrumento",
    "Position (Type A)": "Posición (Tipo A)",
    "Sound Intensity with a p-p Probe (IEC 61043)":
        "Intensidad sonora con sonda p-p (IEC 61043)",
    "Plane wave: Lp \u2248 LI": "Onda plana: Lp \u2248 LI",
    "Standing wave: reactive field": "Onda estacionaria: campo reactivo",
    "Pressure level Lp": "Nivel de presi\u00f3n Lp",
    "Intensity level LI": "Nivel de intensidad LI",
    "Schroeder Integration and Reverberation Time (ISO 3382)":
        "Integraci\u00f3n de Schroeder y tiempo de reverberaci\u00f3n (ISO 3382)",
    "Raw squared IR level": "Nivel de la RI al cuadrado",
    "Schroeder decay curve": "Curva de ca\u00edda de Schroeder",
    "T20 fit (\u22125 to \u221225 dB)": "Ajuste T20 (\u22125 a \u221225 dB)",
    "T30 fit (\u22125 to \u221235 dB)": "Ajuste T30 (\u22125 a \u221235 dB)",
    "EDT fit (0 to \u221210 dB)": "Ajuste EDT (0 a \u221210 dB)",
    "EDT slope": "Pendiente EDT",
    "ISO 717-1 Weighted Sound Reduction Index (Annex C example)":
        "\u00cdndice ponderado de reducci\u00f3n sonora (ISO 717-1, ejemplo del Anexo C)",
    "Apparent sound reduction index R' [dB]":
        "\u00cdndice de reducci\u00f3n sonora aparente R' [dB]",
    "Measured R' (third octave)": "R' medido (tercios de octava)",
    "Shifted reference curve (ISO 717-1)":
        "Curva de referencia desplazada (ISO 717-1)",
    "Unfavourable deviations": "Desviaciones desfavorables",
    "Sharpness Weighting g(z) (DIN 45692)":
        "Ponderación de nitidez g(z) (DIN 45692)",
    "Weighting g(z)": "Ponderación g(z)",
    "DIN 45692 g(z)": "g(z) DIN 45692",
    "von Bismarck (Annex B)": "von Bismarck (Anexo B)",
    "DIN knee\n15.8 Bark": "Codo DIN\n15,8 Bark",
    "Bismarck knee\n15 Bark": "Codo Bismarck\n15 Bark",
    "ISO 717-2 Weighted Normalized Impact Sound Level (Annex C example)":
        "Nivel de ruido de impactos normalizado y ponderado "
        "(ISO 717-2, ejemplo del Anexo C)",
    "Normalized impact sound pressure level Ln [dB]":
        "Nivel de presión de ruido de impactos normalizado Ln [dB]",
    "Measured Ln (third octave)": "Ln medido (tercios de octava)",
    "Shifted reference curve (ISO 717-2)":
        "Curva de referencia desplazada (ISO 717-2)",
    "Unfavourable deviations (measured above reference)":
        "Desviaciones desfavorables (medido por encima de la referencia)",
    "Open-Plan Spatial Decay of Speech (ISO 3382-3)":
        "Decaimiento espacial del habla en oficina abierta (ISO 3382-3)",
    "Distance from the talker r [m]": "Distancia al hablante r [m]",
    "A-weighted SPL [dB]": "SPL ponderado A [dB]",
    "Measured Lp,A,S": "Lp,A,S medido",
    "STI vs distance": "STI vs distancia",
    # --- Advanced psychoacoustics figures (plan-17 block A) ---
    "Loudness Models Compared (1 kHz tone)":
        "Modelos de sonoridad comparados (tono de 1 kHz)",
    "Sound pressure level [dB SPL]": "Nivel de presión sonora [dB SPL]",
    "Total loudness N [sone]": "Sonoridad total N [sonios]",
    "Sottek ECMA-418-2": "Sottek ECMA-418-2",
    "Anchor: 1 kHz / 40 dB = 1 sone":
        "Anclaje: 1 kHz / 40 dB = 1 sonio",
    "Models diverge at high levels":
        "Los modelos divergen a niveles altos",
    "Sottek Specific Loudness (ECMA-418-2)":
        "Sonoridad específica de Sottek (ECMA-418-2)",
    "Specific loudness N' [sone_HMS/Bark]":
        "Sonoridad específica N' [sonios_HMS/Bark]",
    "Peak specific loudness": "Sonoridad específica máxima",
    "ECMA-418-2 Tonality T(t)": "Tonalidad T(t) (ECMA-418-2)",
    "Tonality T [tu_HMS]": "Tonalidad T [tu_HMS]",
    "ECMA-418-2 Roughness vs Modulation Frequency":
        "Aspereza vs frecuencia de modulación (ECMA-418-2)",
    "Modulation frequency f_mod [Hz]":
        "Frecuencia de modulación f_mod [Hz]",
    "Roughness R [asper]": "Aspereza R [asper]",
    "1 kHz carrier, 100 % AM": "Portadora de 1 kHz, AM del 100 %",
    "Sound Quality Metrics (ECMA-418-2 Sottek Hearing Model)":
        "Métricas de calidad sonora (modelo auditivo de Sottek, ECMA-418-2)",
    "Time-Varying Loudness (ISO 532-3)":
        "Sonoridad variable en el tiempo (ISO 532-3)",
    "Loudness [sone]": "Sonoridad [sonios]",
    "1 kHz burst, 200 ms": "Ráfaga de 1 kHz, 200 ms",
    "Fast attack / release": "Ataque / relajación rápidos",
    "Slow integration": "Integración lenta",
    # Building acoustics (EN 12354-1 flanking prediction, ISO 12999-1 uncertainty)
    "EN 12354-1 Flanking Transmission (Annex H.3 example)":
        "Transmisión por flancos EN 12354-1 (ejemplo del Anexo H.3)",
    "Share of transmitted energy [%]": "Cuota de energía transmitida [%]",
    "Transmission path": "Camino de transmisión",
    "Dd — direct": "Dd — directo",
    "Ff — flanking–flanking": "Ff — flanco–flanco",
    "Fd — flanking–separating": "Fd — flanco–separador",
    "Df — separating–flanking": "Df — separador–flanco",
    "dominant path": "camino dominante",
    "ISO 12999-1 Measurement Uncertainty (situation B, airborne)":
        "Incertidumbre de medición ISO 12999-1 (situación B, aéreo)",
    "Measured R'": "R' medido",
    "Standard uncertainty ±u": "Incertidumbre típica ±u",
    "Expanded uncertainty ±U (95 %)": "Incertidumbre expandida ±U (95 %)",
    "R'w ± U (single number)": "R'w ± U (valor único)",
    # Outdoor propagation & occupational exposure (PR-C).
    "ISO 9613-1 Atmospheric Absorption α(f)":
        "Absorción atmosférica α(f) (ISO 9613-1)",
    "Attenuation coefficient α [dB/km]":
        "Coeficiente de atenuación α [dB/km]",
    "ISO 9613-2 Attenuation Breakdown (with a 4 m barrier)":
        "Desglose de la atenuación (ISO 9613-2, con barrera de 4 m)",
    "Octave-band centre frequency [Hz]":
        "Frecuencia central de banda de octava [Hz]",
    "Attenuation A [dB]": "Atenuación A [dB]",
    "Adiv — divergence": "Adiv — divergencia",
    "Aatm — atmospheric": "Aatm — atmosférica",
    "Agr — ground": "Agr — suelo",
    "Abar — barrier": "Abar — barrera",
    "A — total": "A — total",
    "ISO 9612 Task-Based Exposure (Annex D)":
        "Exposición por tareas (ISO 9612, Anexo D)",
    "LEX,8h contribution [dB]": "Contribución a LEX,8h [dB]",
    "Measurement task": "Tarea de medición",
    "planning/breaks": "planificación/pausas",
    "welding": "soldadura",
    "cutting/grinding": "corte/amolado",
    "Daily LEX,8h": "LEX,8h diario",
    "LEX,8h + U (one-sided 95 %)": "LEX,8h + U (unilateral 95 %)",
    # Materials: absorption rating, airflow resistance, impedance tube
    "Shifted reference curve (ISO 11654)":
        "Curva de referencia desplazada (ISO 11654)",
    "Practical absorption alpha_p": "Absorción práctica alpha_p",
    "ISO 11654 Weighted Sound Absorption Coefficient (Annex A.2 example)":
        "Coeficiente de absorción sonora ponderado ISO 11654 (ejemplo del Anexo A.2)",
    "Sound absorption coefficient": "Coeficiente de absorción sonora",
    "Through-origin quadratic fit  dp = a u + b u^2":
        "Ajuste cuadrático por el origen  dp = a u + b u^2",
    "Measured pressure drop": "Caída de presión medida",
    "evaluation at 0.5 mm/s": "evaluación a 0,5 mm/s",
    "ISO 9053-1 Static-Method Airflow Resistance":
        "Resistencia al flujo de aire por el método estático (ISO 9053-1)",
    "Linear airflow velocity u [mm/s]": "Velocidad lineal del aire u [mm/s]",
    "Pressure drop dp [Pa]": "Caída de presión dp [Pa]",
    "Absorption coefficient alpha = 1 - |r|^2":
        "Coeficiente de absorción alpha = 1 - |r|^2",
    "Standing-wave level difference L_max - L_min [dB]":
        "Diferencia de nivel de onda estacionaria L_max - L_min [dB]",
    "Sound absorption coefficient alpha": "Coeficiente de absorción sonora alpha",
    "Reflection factor magnitude |r|": "Módulo del factor de reflexión |r|",
    "ISO 10534-1 Standing-Wave-Ratio Method":
        "Método de la razón de onda estacionaria (ISO 10534-1)",
}

_ES_PATTERNS = [
    (r"^(\d+) yr$", r"\1 años"),
    (r"^Governing  \$K_I\$ = (\d+)\.(\d+) dB$", r"Determinante  $K_I$ = \1,\2 dB"),
    # The mathtext ($R$) makes the later decimal-comma pass skip this label, so
    # convert the decimal here as part of the translation.
    (r"^Example  \$R\$ = (\d+)\.(\d+)$", r"Ejemplo  $R$ = \1,\2"),
    (r"^Octave Band: (.+) Hz$", r"Banda de octava: \1 Hz"),
    (r"^(\d+) phon$", r"\1 fonios"),
    (r"^TNR = (.+) dB\n\(criterion (.+) dB\)$", "TNR = \\1 dB\\n(criterio \\2 dB)"),
    (r"^MLS — first (\d+) of (\d+) samples$",
     r"MLS — primeras \1 de \2 muestras"),
    (r"^Measured 1/(\d+) Octave Bands$", r"Bandas de 1/\1 de octava medidas"),
    (r"^IEC target (.+) dB$", r"Objetivo IEC \1 dB"),
    (r"^([\d.]+) ms burst$", "R\u00e1faga de \\1 ms"),
    (r"^A-Weighting High-Frequency Accuracy @ fs=(\d+) kHz$",
     "Precisi\u00f3n en alta frecuencia de la ponderaci\u00f3n A @ fs=\\1 kHz"),
    (r"^Impulse Response \((.+) Hz Band\) - Transient/Stability Comparison$",
     "Respuesta al impulso (banda de \\1 Hz) \u2014 transitorio y estabilidad"),
    (r"^1 kHz narrowband - N = (.+) sone$",
     "Banda estrecha de 1 kHz - N = \\1 sonios"),
    (r"^Flat broadband 60 dB - N = (.+) sone$",
     "Banda ancha plana a 60 dB - N = \\1 sonios"),
    (r"^Pressure-intensity index\n\u03b4pI = (.+) dB$",
     "\u00cdndice presi\u00f3n-intensidad\\n\u03b4pI = \\1 dB"),
    (r"^Reference curve shifted by (.+) dB$",
     r"Curva de referencia desplazada \1 dB"),
    (r"^Sum of unfavourable deviations = (.+) dB  \(limit 32\.0 dB\)$",
     "Suma de desviaciones desfavorables = \\1 dB  (l\u00edmite 32,0 dB)"),
    (r"^Aures \(Annex B, N = (.+) sone\)$",
     r"Aures (Anexo B, N = \1 sonios)"),
    (r"^Spatial decay D2,S = (.+) dB$",
     r"Decaimiento espacial D2,S = \1 dB"),
    (r"^Zwicker \(ISO 532-1\), N = (.+) sone$",
     r"Zwicker (ISO 532-1), N = \1 sonios"),
    (r"^Moore-Glasberg \(ISO 532-2\), N = (.+) sone$",
     r"Moore-Glasberg (ISO 532-2), N = \1 sonios"),
    (r"^Sottek \(ECMA-418-2\), N = (.+) sone$",
     r"Sottek (ECMA-418-2), N = \1 sonios"),
    (r"^1 kHz tone, 60 dB \(N = (.+) sone_HMS\)$",
     r"Tono de 1 kHz, 60 dB (N = \1 sonios_HMS)"),
    (r"^Tone in noise \(T = (.+) tu_HMS\)$",
     r"Tono en ruido (T = \1 tu_HMS)"),
    (r"^Pure noise \(T = (.+) tu_HMS\)$",
     r"Ruido puro (T = \1 tu_HMS)"),
    (r"^Peak R = (.+) asper @ (.+) Hz$",
     r"Máximo R = \1 asper @ \2 Hz"),
    (r"^Short-term loudness STL \(STL peak = (.+) sone\)$",
     r"Sonoridad a corto plazo STL (STL máx = \1 sonios)"),
    (r"^Long-term loudness LTL \(LTL peak = (.+) sone\)$",
     r"Sonoridad a largo plazo LTL (LTL máx = \1 sonios)"),
    (r"^floor-(.+)$", r"suelo-\1"),
    (r"^ceiling-(.+)$", r"techo-\1"),
    (r"^facade-(.+)$", r"fachada-\1"),
    (r"^wall-(.+)$", r"tabique-\1"),
    (r"^(.+) °C, (.+) % RH$", r"\1 °C, \2 % HR"),
    # Materials: absorption rating & airflow resistance annotations
    (r"^Reference curve shifted by ([\d.]+)$",
     r"Curva de referencia desplazada \1"),
    (r"^Sum of unfavourable deviations = (.+)  \(limit 0\.10\)$",
     "Suma de desviaciones desfavorables = \\1  (límite 0,10)"),
    (r"^Absorption class (.+)  \(shape indicator: (.+)\)$",
     r"Clase de absorción \1  (indicador de forma: \2)"),
    (r"^Specific airflow resistance R_s = (.+) Pa s/m$",
     r"Resistencia específica al flujo R_s = \1 Pa s/m"),
    (r"^Airflow resistivity sigma = (.+) Pa s/m\^2$",
     r"Resistividad al flujo sigma = \1 Pa s/m^2"),
    (r"^Linear term a = (.+) Pa s/m  \(= R_s at u -> 0\)$",
     r"Término lineal a = \1 Pa s/m  (= R_s en u -> 0)"),
    # Scattering / diffusion / precision power dynamic titles (numeric d / LWA)
    (r"^Directional diffusion  d = (.+)  \(ISO 17497-2\)$",
     r"Difusión direccional  d = \1  (ISO 17497-2)"),
    (r"^Precision sound power \(ISO 3745\)  LWA = (.+) dB\(A\)$",
     r"Potencia sonora de precisión (ISO 3745)  LWA = \1 dB(A)"),
    (r"^Precision intensity scanning \(ISO 9614-3\)  LWA = (.+) dB\(A\)$",
     r"Barrido de intensidad de precisión (ISO 9614-3)  LWA = \1 dB(A)"),
    # Human-vibration dynamic titles (numeric a_w / A(8))
    (r"^Weighted seat acceleration \(ISO 2631-1\)  (.+)$",
     r"Aceleración ponderada del asiento (ISO 2631-1)  \1"),
    (r"^Hand-arm daily exposure \(ISO 5349 / 2002-44-EC\)  (.+)$",
     r"Exposición diaria mano-brazo (ISO 5349 / 2002-44-EC)  \1"),
    # Speech intelligibility dynamic title (numeric SII)
    (r"^Speech Intelligibility Index \(ANSI S3\.5-1997\)   SII = (.+)$",
     r"Índice de inteligibilidad del habla (ANSI S3.5-1997)   SII = \1"),
    # Room-noise criteria (ANSI S12.2-2019) dynamic titles/legends
    (r"^Noise Criteria — tangency method   NC-(.+)$",
     r"Criterios de ruido — método de tangencia   NC-\1"),
    (r"^Room Criteria Mark II   RC-(.+)$",
     r"Criterios de sala Mark II   RC-\1"),
    (r"^Tangent @ (.+) Hz$", r"Tangente @ \1 Hz"),
    (r"^Reference RC-(.+)$", r"Referencia RC-\1"),
    (r"^(\d+) yr$", r"\1 años"),
    (r"^10-90 % band \((\d+) yr\)$", r"banda 10-90 % (\1 años)"),
]


def set_lang(lang: str) -> None:
    """Switch the output language ('en' or 'es')."""
    global _LANG, _LANG_SUFFIX
    _LANG = lang
    _LANG_SUFFIX = "" if lang == "en" else f"_{lang}"


def _translate_figure(fig: Any) -> None:
    """Rewrite every Text artist of *fig* into the active language."""
    import re as _re

    import matplotlib.text as _mtext

    if _LANG == "en":
        return
    import re as _re2

    from matplotlib.ticker import FixedFormatter as _FxF
    from matplotlib.ticker import FuncFormatter as _FF
    from matplotlib.ticker import ScalarFormatter as _SF

    def _comma(s: str) -> str:
        # A letter immediately before the number marks a standard designation
        # (e.g. "S3.5"), not a decimal - leave those untouched.
        return _re2.sub(r"(?<![\d.A-Za-z])(\d+)\.(\d+)(?![.\d])", r"\1,\2", s)

    def _tr_words(s: str) -> str:
        """Apply the exact / pattern lookups (no decimal comma) to *s*."""
        if s in _ES_EXACT:
            return _ES_EXACT[s]
        for pat, repl in _ES_PATTERNS:
            new, n = _re.subn(pat, repl, s)
            if n:
                return new
        return s

    for ax in fig.get_axes():
        for axis in (ax.xaxis, ax.yaxis):
            fmt = axis.get_major_formatter()
            if isinstance(fmt, _FxF):
                # Translate categorical tick labels (e.g. path names) too;
                # numeric labels match nothing and only get the decimal comma.
                fmt.seq = [_comma(_tr_words(s)) for s in fmt.seq]
            elif isinstance(fmt, _FF) and not getattr(fmt, "_phonometry_comma", False):
                # Categorical labels (set_xticklabels installs a FuncFormatter)
                # need the word lookups too; numeric labels are untouched.
                wrapped = _FF(
                    lambda v, pos, _f=fmt: _comma(_tr_words(str(_f(v, pos))))
                )
                wrapped._phonometry_comma = True  # type: ignore[attr-defined]
                axis.set_major_formatter(wrapped)
            elif type(fmt) is _SF and axis.get_scale() == "linear":
                wrapped = _FF(lambda v, pos: _comma(f"{v:g}"))
                axis.set_major_formatter(wrapped)
    for artist in fig.findobj(_mtext.Text):
        s = artist.get_text()
        if not s:
            continue
        if s in _ES_EXACT:
            artist.set_text(_ES_EXACT[s])
        else:
            for pat, repl in _ES_PATTERNS:
                new, n = _re.subn(pat, repl, s)
                if n:
                    artist.set_text(new)
                    break
        # Spanish decimal comma, applied uniformly to every text artist
        # (tick labels included) except mathtext. The substitution itself is
        # conservative -- it only rewrites a bare ``digit.digit`` not adjacent
        # to further digits/dots -- so underscore-bearing unit tokens such as
        # ``sone_HMS`` / ``tu_HMS`` keep their identifier intact while genuine
        # decimals in the same label (e.g. ``8.0 sone_HMS``) still get commas.
        s = artist.get_text()
        if s and "$" not in s and _re.search(r"\d\.\d", s):
            # Clause/version numbers like 5.3.3 and standard designations like
            # "S3.5" (a letter immediately before the number) keep their dots.
            artist.set_text(
                _re.sub(r"(?<![\d.A-Za-z])(\d+)\.(\d+)(?![.\d])", r"\1,\2", s)
            )


LABEL_FREQ_HZ = "Frequency [Hz]"
LABEL_LEVEL_DB = "Level [dB]"
COLOR_PRIMARY = "#1f77b4"
COLOR_SECONDARY = "#d62728"
COLOR_TERTIARY = "#2ca02c"
COLOR_GRID = "#e0e0e0"

# Theme state: every figure is generated twice (light + "_dark" suffix).
# COLOR_FG replaces literal black so annotations stay visible on dark bg.
COLOR_FG = "black"
_FILENAME_SUFFIX = ""

# Global matplotlib configuration
plt.rcParams.update(
    {
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.5,
        "grid.linestyle": "--",
        "figure.figsize": (10, 6),
        "figure.dpi": 150,
        "savefig.bbox": "tight",
    }
)


def set_theme(dark: bool) -> None:
    """Switch between the light (default) and dark documentation themes."""
    global COLOR_FG, COLOR_GRID, _FILENAME_SUFFIX
    if dark:
        plt.style.use("dark_background")
        COLOR_FG = "white"
        COLOR_GRID = "#555555"
        _FILENAME_SUFFIX = "_dark"
    else:
        plt.style.use("default")
        COLOR_FG = "black"
        COLOR_GRID = "#e0e0e0"
        _FILENAME_SUFFIX = ""
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.5,
            "grid.linestyle": "--",
            "figure.figsize": (10, 6),
            "figure.dpi": 150,
            "savefig.bbox": "tight",
        }
    )


def themed_path(output_dir: str, filename: str) -> str:
    """Return the output path for *filename*, adding language + theme suffixes.

    Also translates the current figure's text artists into the active
    language: every generator calls ``plt.savefig(themed_path(...))``, so
    this runs right before each save without patching matplotlib globally.
    """
    _translate_figure(plt.gcf())
    stem, ext = os.path.splitext(filename)
    return os.path.join(output_dir, f"{stem}{_LANG_SUFFIX}{_FILENAME_SUFFIX}{ext}")



def apply_axis_styling(ax: Any, title: str, xlim: tuple[float, float] | None = None, ylim: tuple[float, float] | None = None) -> None:
    """Apply consistent styling to plots."""
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel(LABEL_LEVEL_DB)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-")
    ax.grid(which="minor", color=COLOR_GRID, linestyle=":", alpha=0.4)

    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)

    # Standard Octave Ticks
    xticks = [16, 31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    xticklabels = ["16", "31.5", "63", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)


def plot_psd(ax: Any, x: np.ndarray, fs: int, label: str = "Raw Signal PSD", color: str = "gray", alpha: float = 0.3) -> None:
    """Calculate and plot the Power Spectral Density of the raw signal."""
    # Use Welch's method for a smooth PSD estimate
    f, Pxx = scipy_signal.welch(x, fs, nperseg=4096)
    
    # Convert to dB (relative to max to match SPL scale roughly or just show shape)
    # Since SPL is calibrated differently, we just want to show the 'shape' of the spectrum
    # in the background. We can normalize Pxx to match the peak of the octave bands roughly
    # or just plot it as is if we had calibrated units.
    # Here we'll just plot relative dB
    
    # Avoid log(0)
    Pxx_db = 10 * np.log10(Pxx + 1e-12)
    
    # Normalize PSD peak to 0 dB for visualization shape, then shift down? 
    # Or better: don't normalize, just plot. But PSD density vs Octave Band Power (integrated) 
    # are different units (dB/Hz vs dB).
    # So we will plot it on a secondary Y axis or just scaled to fit nicely in background.
    
    # Let's shift it so its mean roughly aligns with the mean of the SPL for visualization
    # This is purely for qualitative comparison of "where the energy is".
    
    ax.semilogx(f, Pxx_db, color=color, alpha=alpha, linewidth=1, label=label, zorder=0)


def generate_filter_type_comparison(output_dir: str) -> None:
    """Compare different filter architectures with a zoom inset."""
    print("Generating filter_type_comparison.png...")
    fs = 48000
    fraction = 1
    order = 6
    
    # We want exactly the 1000Hz band
    limits = [800.0, 1200.0]
    
    filters = [
        ("butter", "Butterworth", COLOR_PRIMARY, "-"),
        ("cheby1", "Chebyshev I", COLOR_SECONDARY, "--"),
        ("cheby2", "Chebyshev II", COLOR_TERTIARY, ":"),
        ("ellip", "Elliptic", "#9467bd", "-."),
        ("bessel", "Bessel", "#8c564b", "-"),
    ]
    
    _, ax = plt.subplots(figsize=(10, 7))
    
    # Create inset axis for zoom (increased height to 45%)
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    axins = inset_axes(ax, width="35%", height="45%", loc="upper left", borderpad=3)
    axins.set_xscale("log") # Explicitly set log scale
    
    for f_type, label, color, style in filters:
        bank = OctaveFilterBank(fs, fraction=fraction, order=order, limits=limits, filter_type=f_type)
        
        # Find index of 1000Hz band
        idx = np.argmin(np.abs(np.array(bank.freq) - 1000))
        
        fsd = fs / bank.factor[idx]
        w, h = scipy_signal.sosfreqz(bank.sos[idx], worN=16384, fs=fsd)
        mag_db = 20 * np.log10(np.abs(h) + 1e-9)
        
        ax.semilogx(w, mag_db, label=label, color=color, linestyle=style)
        axins.plot(w, mag_db, color=color, linestyle=style)

    ax.axhline(-3, color=COLOR_FG, linestyle=":", alpha=0.3, label="-3 dB")
    axins.axhline(-3, color=COLOR_FG, linestyle=":", alpha=0.3)
    
    apply_axis_styling(ax, "Filter Architecture Comparison (Order 6, 1kHz Band)", xlim=(100, 8000), ylim=(-80, 5))
    
    # Sub-plot styling (Zoom around 1kHz and -3dB)
    axins.set_xlim(650, 1500)
    axins.set_ylim(-4, 0.5)  # Adjusted: from -4 to 0.5
    axins.grid(True, which="both", alpha=0.3)
    axins.set_title("Zoom at -3 dB (Log Scale)", fontsize=9)

    # Fix x-ticks for log scale zoom to look right
    from matplotlib.ticker import NullFormatter, ScalarFormatter

    axins.xaxis.set_major_formatter(ScalarFormatter())
    axins.xaxis.set_minor_formatter(NullFormatter())  # Hide minor tick labels
    axins.xaxis.get_major_formatter().set_scientific(False)  # Disable scientific notation
    axins.set_xticks([707, 1000, 1414])
    axins.set_xticklabels(["707", "1000", "1414"], fontsize=8)

    ax.legend(loc="lower right")
    plt.savefig(themed_path(output_dir, "filter_type_comparison.png"))
    plt.close()


def generate_filter_responses(output_dir: str) -> None:
    """Generate plots for the filter bank responses for different filter types."""
    fs = 48000
    
    # Filter types to generate
    filter_types = [
        ("butter", "butter"),
        ("cheby1", "cheby1"),
        ("cheby2", "cheby2"),
        ("ellip", "ellip"),
        ("bessel", "bessel"),
    ]

    configs = [
        (1, 6),
        (3, 6),
    ]

    for f_type_name, f_type in filter_types:
        for fraction, order in configs:
            filename = f"filter_{f_type_name}_fraction_{fraction}_order_{order}.png"
            print(f"Generating {filename}...")
            bank = OctaveFilterBank(fs=fs, fraction=fraction, order=order, limits=[12.0, 20000.0], filter_type=f_type)
            
            from phonometry.filter_design import _showfilter
            # Draw first, then save through themed_path so the Spanish
            # translation pass runs on the finished figure (it rewrites the
            # live figure's text artists right before the save).
            _showfilter(bank.sos, bank.freq, bank.freq_u, bank.freq_d, fs,
                        bank.factor, show=False, plot_file=None, close=False)
            plt.savefig(themed_path(output_dir, filename), dpi=150,
                        bbox_inches="tight")
            plt.close("all")


def generate_signal_responses(output_dir: str) -> None:
    """Generate spectral analysis plots for a complex signal."""
    fs = 48000
    duration = 5
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    freqs = [20, 100, 500, 2000, 4000, 15000]
    y = 100 * np.sum([np.sin(2 * np.pi * f * t) for f in freqs], axis=0)

    for frac, filename, title in [
        (3, "signal_response_fraction_3.png", "1/3 Octave Band Analysis"),
    ]:
        print(f"Generating {filename}...")
        bank = OctaveFilterBank(fs=fs, fraction=frac, order=6, limits=[12.0, 20000.0])
        spl, freq = bank.filter(y)

        _, ax = plt.subplots()
        
        # Plot PSD of raw signal in background
        # We need to scale PSD to comparable levels. 
        # A simple hack for visualization is to align the max of PSD to max of SPL
        f_psd, Pxx = scipy_signal.welch(y, fs, nperseg=8192)
        Pxx_db = 10 * np.log10(Pxx + 1e-12)
        # Shift PSD to match SPL peak roughly
        Pxx_db += (np.max(spl) - np.max(Pxx_db)) - 5 # Shift slightly below
        
        ax.semilogx(f_psd, Pxx_db, color="gray", alpha=0.6, linewidth=1.2, label="Raw Signal Spectrum (PSD)", zorder=0)
        
        ax.semilogx(
            freq,
            spl,
            marker="o",
            markersize=5,
            linestyle="-",
            color=COLOR_PRIMARY,
            linewidth=1.5,
            markerfacecolor="white",
            markeredgewidth=1.5,
            label=f"Measured 1/{frac} Octave Bands"
        )
        apply_axis_styling(ax, title, xlim=(11, 25000))
        ax.legend(loc="lower right")
        plt.savefig(themed_path(output_dir, filename))
        plt.close()


def generate_multichannel_response(output_dir: str) -> None:
    """Generate analysis plot for a stereo signal with separate subplots."""
    print("Generating signal_response_multichannel.png...")
    fs = 48000
    duration = 5
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)

    rng = np.random.default_rng(42)
    # Channel 1: Pink Noise (Voss-McCartney simplified)
    # Good enough for visualization
    white = rng.standard_normal(len(t))
    b, a = scipy_signal.butter(1, 0.04) # -3dB/oct approx
    ch1 = scipy_signal.lfilter(b, a, white)
    ch1 = (ch1 - np.mean(ch1)) / np.max(np.abs(ch1))

    # Channel 2: Logarithmic Sine Sweep
    ch2 = scipy_signal.chirp(t, f0=50, t1=duration, f1=10000, method="logarithmic")

    x = np.vstack((ch1, ch2))
    bank = OctaveFilterBank(fs=fs, fraction=3, order=6, limits=[20.0, 20000.0])
    spl, freq = bank.filter(x)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Calculate PSDs for background
    f_psd1, Pxx1 = scipy_signal.welch(x[0], fs, nperseg=4096)
    Pxx_db1 = 10 * np.log10(Pxx1 + 1e-12)
    Pxx_db1 += (np.max(spl[0]) - np.max(Pxx_db1)) # Align peaks
    
    f_psd2, Pxx2 = scipy_signal.welch(x[1], fs, nperseg=4096)
    Pxx_db2 = 10 * np.log10(Pxx2 + 1e-12)
    Pxx_db2 += (np.max(spl[1]) - np.max(Pxx_db2)) # Align peaks

    # Plot Left Channel
    ax1.semilogx(f_psd1, Pxx_db1, color="gray", alpha=0.6, linewidth=1.2, label="Raw PSD", zorder=0)
    ax1.semilogx(
        freq,
        spl[0],
        marker="o",
        markersize=5,
        label="Left Channel: Pink Noise",
        color=COLOR_PRIMARY,
        linestyle="-",
        linewidth=1.5,
        markerfacecolor="white",
        markeredgewidth=1.2,
    )
    # Use standard styling but override title
    apply_axis_styling(ax1, "Multichannel Analysis (Stereo Input)", xlim=(16, 20000))
    ax1.legend(loc="lower right")
    # Let Y-axis autoscale

    # Plot Right Channel
    ax2.semilogx(f_psd2, Pxx_db2, color="gray", alpha=0.6, linewidth=1.2, label="Raw PSD", zorder=0)
    ax2.semilogx(
        freq,
        spl[1],
        marker="s",
        markersize=5,
        label="Right Channel: Log Sine Sweep",
        color=COLOR_SECONDARY,
        linestyle="-",
        linewidth=1.5,
        markerfacecolor="white",
        markeredgewidth=1.2,
    )
    apply_axis_styling(ax2, "", xlim=(16, 20000))
    ax2.set_title("") # Remove title from bottom plot
    ax2.legend(loc="lower right")
    # Let Y-axis autoscale

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "signal_response_multichannel.png"))
    plt.close()


def generate_decomposition_plot(output_dir: str) -> None:
    """Generate time-domain decomposition plot comparing two filter types (Butterworth vs Chebyshev II)."""
    print("Generating signal_decomposition.png with comparison (Butter vs Cheby2) @ 48kHz...")
    fs = 48000
    duration = 0.5
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)

    # Signal: sum of 250Hz and 1000Hz sines
    y = np.sin(2 * np.pi * 250 * t) + np.sin(2 * np.pi * 1000 * t)

    # Filter into 1/1 octave bands with two different architectures
    # We use Chebyshev II (flat passband, no ripple)
    bank_butter = OctaveFilterBank(fs=fs, fraction=1, order=6, limits=[100.0, 2000.0], filter_type="butter")
    bank_cheby2 = OctaveFilterBank(fs=fs, fraction=1, order=6, limits=[100.0, 2000.0], filter_type="cheby2")
    
    # Cast to 3-tuple to satisfy mypy unpacking
    _, freq, xb_butter = bank_butter.filter(y, sigbands=True)
    
    _, _, xb_cheby2 = bank_cheby2.filter(y, sigbands=True)

    if xb_butter is None or xb_cheby2 is None:
        raise ValueError("Signal bands should not be None")

    num_plots = len(xb_butter) + 2 # +1 for original, +1 for impulse response
    fig, axes = plt.subplots(num_plots, 1, figsize=(10, 2.2 * num_plots), sharex=False)


    # Fixed Y limits for decomposition
    y_lim = (-2.8, 2.8)

    # 1. Original Signal
    axes[0].plot(t, y, color=COLOR_FG, linewidth=1.5)
    axes[0].set_title("Original Signal (250 Hz + 1000 Hz Sum) @ 48 kHz", fontweight="bold")
    axes[0].set_ylim(y_lim)
    axes[0].set_xlim(0, 0.04)

    # 2. Filtered Bands Comparison
    for i, (f_center) in enumerate(freq):
        axes[i + 1].plot(t, xb_butter[i], color=COLOR_PRIMARY, linewidth=1.5, label="Butterworth (Flat)")
        axes[i + 1].plot(t, xb_cheby2[i], color=COLOR_SECONDARY, linewidth=1.2, linestyle="--", alpha=0.9, label="Chebyshev II")
        axes[i + 1].set_title(f"Octave Band: {f_center:.0f} Hz", fontsize=11, fontweight="bold")
        axes[i + 1].set_ylim(y_lim)
        axes[i + 1].set_xlim(0, 0.04)
        if i == 0:
            axes[i+1].legend(loc="upper right", fontsize=9, framealpha=0.8)

    # 3. Impulse Response (Stability/Transient Visualization)
    impulse = np.zeros(len(t))
    impulse[0] = 1.0
    _, _, ir_butter = bank_butter.filter(impulse, sigbands=True)
    _, _, ir_cheby2 = bank_cheby2.filter(impulse, sigbands=True)
    
    idx_1000 = np.argmin(np.abs(np.array(freq) - 1000))
    axes[-1].plot(t, ir_butter[idx_1000], color=COLOR_PRIMARY, linewidth=1.5, label="Butterworth")
    axes[-1].plot(t, ir_cheby2[idx_1000], color=COLOR_SECONDARY, linewidth=1.2, linestyle="--", alpha=0.9, label="Chebyshev II")
    axes[-1].set_title(f"Impulse Response ({freq[idx_1000]:.0f} Hz Band) - Transient/Stability Comparison", fontweight="bold")
    axes[-1].set_xlim(0, 0.04)
    axes[-1].set_xlabel("Time [s]")
    axes[-1].legend(loc="upper right", fontsize=9, framealpha=0.8)

    for ax in axes:
        ax.set_ylabel("Amplitude")
        ax.grid(True, which="both", alpha=0.4, linestyle=":")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "signal_decomposition.png"))
    plt.close()



def measure_weighting_response(
    fs: int, curve: str, freqs: "np.ndarray | None" = None
) -> tuple[np.ndarray, np.ndarray]:
    """
    Measure a weighting curve the way the docs figure plots it: impulse
    response through the real filter path, evaluated with ``freqz`` (DTFT
    of the measured response).

    The impulse is placed at the CENTER of the buffer: the high-accuracy
    weighting path resamples with polyphase FIRs, and an impulse at sample 0
    loses the anti-causal half of the interpolation kernel (edge truncation),
    which once shipped a figure with curves ~2.4 dB low. Centering only adds
    linear phase, which does not affect the magnitude.

    :param fs: Sample rate in Hz.
    :param curve: 'A', 'C' or 'Z'.
    :param freqs: Optional exact frequencies to evaluate; defaults to a
        dense 8192-point grid for plotting.
    :return: Tuple (frequencies, magnitude in dB).
    """
    from phonometry import weighting_filter

    impulse = np.zeros(fs)
    impulse[fs // 2] = 1.0
    weighted = weighting_filter(impulse, fs, curve=curve)

    worn = 8192 if freqs is None else np.asarray(freqs, dtype=float)
    w, h = scipy_signal.freqz(weighted, [1], worN=worn, fs=fs)
    mag_db = 20 * np.log10(np.abs(h) + 1e-9)
    if freqs is None:
        # Drop the 0 Hz point: it cannot be drawn on a log frequency axis.
        return w[1:], mag_db[1:]
    return w, mag_db


def generate_weighting_responses(output_dir: str) -> None:
    """Plot A, C and Z weighting frequency responses."""
    print("Generating weighting_responses.png...")
    fs = 48000

    _, ax = plt.subplots(figsize=(10, 7))

    # Zoom inset: the A curve is POSITIVE (+1.27 dB max at ~2.5 kHz per
    # IEC 61672-1 Table 2), invisible at the full -50..5 dB scale.
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    axins = inset_axes(ax, width="42%", height="38%", loc="lower center", borderpad=2)
    axins.set_xscale("log")

    curves = [
        ("A", "A-Weighting", COLOR_PRIMARY),
        ("C", "C-Weighting", COLOR_SECONDARY),
        ("Z", "Z-Weighting (Flat)", COLOR_FG)
    ]

    for code, label, color in curves:
        # measure_weighting_response is covered by tests/test_graph_measurements.py
        w, mag_db = measure_weighting_response(fs, code)
        ax.semilogx(w, mag_db, label=label, color=color)
        axins.plot(w, mag_db, color=color)

    ax.axhline(0, color=COLOR_FG, linestyle=":", alpha=0.3, linewidth=1)
    apply_axis_styling(ax, "Frequency Weighting Curves (IEC 61672-1)", xlim=(10, 22000), ylim=(-50, 5))

    axins.axhline(0, color=COLOR_FG, linestyle=":", alpha=0.4, linewidth=1)
    axins.set_xlim(500, 8000)
    axins.set_ylim(-3, 2)
    axins.grid(True, which="both", alpha=0.3)
    axins.set_title("Zoom: A-weighting is positive (max +1.27 dB @ 2.5 kHz)", fontsize=9)
    axins.annotate(
        "+1.27 dB", xy=(2500, 1.27), xytext=(4200, 1.55), fontsize=8,
        arrowprops={"arrowstyle": "->", "lw": 0.8},
    )
    from matplotlib.ticker import NullFormatter, ScalarFormatter
    axins.xaxis.set_major_formatter(ScalarFormatter())
    axins.xaxis.set_minor_formatter(NullFormatter())
    axins.set_xticks([500, 1000, 2500, 5000, 8000])
    axins.set_xticklabels(["500", "1k", "2.5k", "5k", "8k"], fontsize=8)

    ax.legend(loc="lower right")
    plt.savefig(themed_path(output_dir, "weighting_responses.png"))
    plt.close()


def generate_g_weighting_response(output_dir: str) -> None:
    """Plot the ISO 7196 G-weighting curve against the Table 2 nominals."""
    print("Generating g_weighting_response.png...")
    from scipy import signal as sp_signal

    from phonometry import WeightingFilter

    fs = 48000
    # ISO 7196:1995 Table 2 - nominal one-third-octave frequency, response dB
    table2 = [
        (0.25, -88.0), (0.5, -64.3), (1.0, -43.0), (2.0, -28.3),
        (4.0, -16.0), (8.0, -4.0), (10.0, 0.0), (16.0, 7.7), (20.0, 9.0),
        (31.5, -4.0), (63.0, -28.0), (125.0, -52.0), (250.0, -76.0),
    ]
    freqs = np.logspace(np.log10(0.1), np.log10(1000), 800)
    sos = WeightingFilter(fs, "G").sos
    _, h = sp_signal.sosfreqz(sos, worN=freqs, fs=fs)
    mag_db = 20 * np.log10(np.abs(h))

    _, ax = plt.subplots(figsize=(10, 6))
    ax.semilogx(freqs, mag_db, color=COLOR_PRIMARY, label="G-weighting (ISO 7196)")
    tf = [f for f, _ in table2]
    tv = [v for _, v in table2]
    ax.plot(tf, tv, "o", color=COLOR_SECONDARY, markersize=5,
            label="ISO 7196 Table 2 nominals", zorder=5)
    ax.axhline(0, color=COLOR_FG, linestyle=":", alpha=0.3, linewidth=1)
    ax.axvline(10, color=COLOR_FG, linestyle=":", alpha=0.3, linewidth=1)
    ax.annotate("0 dB @ 10 Hz", xy=(10, 0), xytext=(20, -18), fontsize=9,
                arrowprops={"arrowstyle": "->", "lw": 0.8})
    apply_axis_styling(
        ax, "G Frequency Weighting for Infrasound (ISO 7196:1995)",
        xlim=(0.1, 1000), ylim=(-95, 15),
    )
    from matplotlib.ticker import NullFormatter, ScalarFormatter
    ticks = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 125, 315, 1000]
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticklabels(["0.1", "0.25", "0.5", "1", "2", "5", "10", "20", "50", "125", "315", "1k"])
    ax.legend(loc="upper right")
    plt.savefig(themed_path(output_dir, "g_weighting_response.png"))
    plt.close()


def generate_equal_loudness_contours(output_dir: str) -> None:
    """Plot the ISO 226:2023 normal equal-loudness-level contours."""
    print("Generating equal_loudness_contours.png...")
    from phonometry import equal_loudness_contour, hearing_threshold

    _, ax = plt.subplots(figsize=(10, 7))
    for phon in [20, 40, 60, 80, 90]:
        freqs, spl = equal_loudness_contour(float(phon))
        ax.semilogx(freqs, spl, color=COLOR_PRIMARY, linewidth=1.5)
        ax.annotate(f"{phon} phon", xy=(1000, phon), xytext=(1150, phon + 1),
                    fontsize=9, color=COLOR_PRIMARY)
    ft, tf = hearing_threshold()
    ax.semilogx(ft, tf, color=COLOR_SECONDARY, linestyle="--",
                label="Hearing threshold $T_f$ (Table 1)")
    ax.plot(1000, 0, alpha=0)  # keep 0 dB in view
    apply_axis_styling(
        ax, "Normal Equal-Loudness-Level Contours (ISO 226:2023)",
        xlim=(20, 12500), ylim=(-10, 130),
    )
    ax.set_ylabel("Sound pressure level [dB re 20 \u00b5Pa]")
    ax.legend(loc="upper right")
    plt.savefig(themed_path(output_dir, "equal_loudness_contours.png"))
    plt.close()


def generate_time_weighting_plot(output_dir: str) -> None:
    """Visualize Fast, Slow and Impulse time weighting response to a burst."""
    print("Generating time_weighting_analysis.png...")
    fs = 1000
    t = np.linspace(0, 4, fs * 4, endpoint=False)
    
    # 500ms burst of noise starting at 1.0s
    rng = np.random.default_rng(42)
    x = np.zeros_like(t)
    start_idx = int(fs * 1.0)
    end_idx = int(fs * 1.5)
    x[start_idx:end_idx] = rng.standard_normal(end_idx - start_idx)
    
    from phonometry import time_weighting
    
    # Square for energy
    x_sq = x**2
    fast = time_weighting(x, fs, mode="fast")
    slow = time_weighting(x, fs, mode="slow")
    impulse = time_weighting(x, fs, mode="impulse")
    
    _, ax = plt.subplots()
    # Normalize for better visualization
    # We normalized x_sq to peak at 1 for the plot
    peak = np.max(x_sq)
    x_sq /= peak
    fast /= peak
    slow /= peak
    impulse /= peak
    
    ax.plot(t, x_sq, color="#9e9e9e", alpha=0.6, label="Input Burst (Normalized)")
    ax.plot(t, fast, color=COLOR_PRIMARY, label="Fast (125ms)")
    ax.plot(t, slow, color=COLOR_SECONDARY, label="Slow (1000ms)")
    ax.plot(t, impulse, color="purple", linestyle="-.", linewidth=1.5, label="Impulse (35ms/1.5s)")
    
    ax.set_title("Time Weighting Ballistics (IEC 61672-1)", fontweight="bold")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Normalized Response")
    ax.legend(loc="upper right")
    ax.set_xlim(0.8, 3.5)
    plt.savefig(themed_path(output_dir, "time_weighting_analysis.png"))
    plt.close()


def generate_crossover_plot(output_dir: str) -> None:
    """Visualize Linkwitz-Riley 4th Order Crossover."""
    print("Generating crossover_lr4.png...")
    fs = 48000
    
    from phonometry import linkwitz_riley
    
    # Frequency analysis
    # Measure response using IR
    impulse = np.zeros(fs)
    impulse[0] = 1.0
    lp_ir, hp_ir = linkwitz_riley(impulse, fs, freq=1000, order=4)
    
    w, h_lp = scipy_signal.freqz(lp_ir, worN=8192, fs=fs)
    _, h_hp = scipy_signal.freqz(hp_ir, worN=8192, fs=fs)
    
    _, ax = plt.subplots()
    ax.semilogx(w, 20 * np.log10(np.abs(h_lp) + 1e-9), color=COLOR_PRIMARY, label="Low Pass (LR4)")
    ax.semilogx(w, 20 * np.log10(np.abs(h_hp) + 1e-9), color=COLOR_SECONDARY, label="High Pass (LR4)")
    ax.semilogx(w, 20 * np.log10(np.abs(h_lp + h_hp) + 1e-9), color=COLOR_FG, linestyle="--", label="Sum (Flat)")

    apply_axis_styling(ax, "Linkwitz-Riley Crossover (4th Order @ 1kHz)", xlim=(20, 20000), ylim=(-60, 5))
    ax.legend(loc="lower right")
    plt.savefig(themed_path(output_dir, "crossover_lr4.png"))
    plt.close()


def generate_spectrogram_example(output_dir: str) -> None:
    """Visualize OctaveFilterBank.spectrogram on a time-varying signal."""
    print("Generating spectrogram_example.png...")
    fs = 48000
    duration = 4.0
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)

    # Log sweep + two tone bursts to show time-frequency localization
    rng = np.random.default_rng(42)
    x = 0.5 * scipy_signal.chirp(t, f0=80, t1=duration, f1=8000, method="logarithmic")
    x[int(1.0 * fs):int(1.3 * fs)] += np.sin(2 * np.pi * 4000 * t[int(1.0 * fs):int(1.3 * fs)])
    x[int(2.5 * fs):int(2.8 * fs)] += np.sin(2 * np.pi * 250 * t[int(2.5 * fs):int(2.8 * fs)])
    x += 0.01 * rng.standard_normal(len(t))

    bank = OctaveFilterBank(fs=fs, fraction=3, order=6, limits=[50.0, 12000.0])
    levels, freq, times = bank.spectrogram(x, window_time=0.125, overlap=0.5)

    _, ax = plt.subplots()
    mesh = ax.pcolormesh(times, freq, levels, shading="auto", cmap="magma")
    ax.set_yscale("log")
    ax.set_title("1/3 Octave Spectrogram (Fast windows, 50% overlap)", fontweight="bold", pad=12)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel(LABEL_FREQ_HZ)
    yticks = [63, 125, 250, 500, 1000, 2000, 4000, 8000]
    ax.set_yticks(yticks)
    ax.set_yticklabels(["63", "125", "250", "500", "1k", "2k", "4k", "8k"])
    plt.colorbar(mesh, ax=ax, label=LABEL_LEVEL_DB)
    plt.savefig(themed_path(output_dir, "spectrogram_example.png"))
    plt.close()


def generate_ln_levels_example(output_dir: str) -> None:
    """Visualize statistical LN levels over the Fast envelope."""
    print("Generating ln_levels_example.png...")
    fs = 8000
    duration = 30.0
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)

    from phonometry import ln_levels, time_weighting

    # Fluctuating "traffic-like" noise: background + random events
    rng = np.random.default_rng(42)
    x = 0.05 * rng.standard_normal(len(t))
    for _ in range(12):
        start = rng.uniform(1, duration - 3)
        length = rng.uniform(0.5, 2.0)
        idx = (t >= start) & (t < start + length)
        envelope = np.hanning(int(idx.sum()))
        x[idx] += envelope * rng.uniform(0.3, 1.0) * rng.standard_normal(int(idx.sum()))

    envelope_ms = time_weighting(x, fs, mode="fast")
    level_t = 10 * np.log10(np.maximum(envelope_ms, 1e-12) / (2e-5) ** 2)
    stats = ln_levels(x, fs, n=(10, 50, 90))

    _, ax = plt.subplots()
    ax.plot(t, level_t, color=COLOR_PRIMARY, linewidth=0.8, label="Fast level $L_p(t)$")
    for n_value, color, style in [(10, COLOR_SECONDARY, "--"), (50, COLOR_FG, "-"), (90, COLOR_TERTIARY, "-.")]:
        ax.axhline(
            float(stats[n_value]), color=color, linestyle=style, linewidth=1.5,
            label=f"L{n_value} = {float(stats[n_value]):.1f} dB",
        )
    ax.set_title("Statistical Levels L10 / L50 / L90 (Fast envelope)", fontweight="bold", pad=12)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel(LABEL_LEVEL_DB)
    ax.set_xlim(0, duration)
    ax.legend(loc="lower right")
    plt.savefig(themed_path(output_dir, "ln_levels_example.png"))
    plt.close()


def generate_zero_phase_comparison(output_dir: str) -> None:
    """Compare causal vs zero-phase band filtering of a tone burst."""
    print("Generating zero_phase_comparison.png...")
    fs = 48000
    duration = 0.15
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)

    # 250 Hz tone burst in the middle of the frame
    x = np.zeros_like(t)
    start, end = int(0.05 * fs), int(0.10 * fs)
    x[start:end] = np.sin(2 * np.pi * 250 * t[start:end]) * np.hanning(end - start)

    bank = OctaveFilterBank(fs=fs, fraction=1, order=6, limits=[200.0, 300.0])
    _, _, bands_fwd = bank.filter(x, sigbands=True, calculate_level=False)
    _, _, bands_zp = bank.filter(x, sigbands=True, calculate_level=False, zero_phase=True)

    _, ax = plt.subplots()
    ax.plot(t, x, color="gray", alpha=0.5, linewidth=1.0, label="Input burst (250 Hz)")
    ax.plot(t, bands_fwd[0], color=COLOR_PRIMARY, linewidth=1.3, label="Causal filtering (group delay)")
    ax.plot(t, bands_zp[0], color=COLOR_SECONDARY, linewidth=1.3, linestyle="--", label="zero_phase=True (aligned)")
    ax.set_title("Zero-Phase Filtering: Group Delay Elimination (250 Hz Band)", fontweight="bold", pad=12)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Amplitude")
    ax.legend(loc="upper right")
    plt.savefig(themed_path(output_dir, "zero_phase_comparison.png"))
    plt.close()


def generate_weighting_accuracy_hf(output_dir: str) -> None:
    """Compare A-weighting HF accuracy: analytic vs bilinear vs high_accuracy."""
    print("Generating weighting_accuracy_hf.png...")
    fs = 48000

    from phonometry import WeightingFilter

    freqs = np.logspace(np.log10(1000), np.log10(20000), 40)

    def analytic_a(f: np.ndarray) -> np.ndarray:
        ra = (12194**2 * f**4) / (
            (f**2 + 20.6**2)
            * np.sqrt((f**2 + 107.7**2) * (f**2 + 737.9**2))
            * (f**2 + 12194**2)
        )
        return np.asarray(20 * np.log10(ra) + 2.0)

    def measured_gains(wf: WeightingFilter) -> np.ndarray:
        gains = []
        for f0 in freqs:
            tt = np.arange(int(fs * 0.2)) / fs
            x = np.sin(2 * np.pi * f0 * tt)
            y = wf.filter(x)
            n0 = int(0.05 * fs)  # skip filter transient
            gains.append(20 * np.log10(np.std(y[n0:]) / np.std(x[n0:])))
        return np.array(gains)

    legacy = measured_gains(WeightingFilter(fs, "A", high_accuracy=False))
    accurate = measured_gains(WeightingFilter(fs, "A"))
    reference = analytic_a(freqs)

    _, (ax, ax_err) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax.semilogx(freqs, reference, color=COLOR_FG, linewidth=2, label="IEC 61672-1 analytic curve")
    ax.semilogx(freqs, legacy, color=COLOR_SECONDARY, linestyle="--", label="Plain bilinear (high_accuracy=False)")
    ax.semilogx(freqs, accurate, color=COLOR_PRIMARY, linestyle="-.", label="Oversampled (high_accuracy=True)")
    ax.set_title(f"A-Weighting High-Frequency Accuracy @ fs={fs//1000} kHz", fontweight="bold", pad=12)
    ax.set_ylabel(LABEL_LEVEL_DB)
    ax.legend(loc="lower left")

    ax_err.semilogx(freqs, legacy - reference, color=COLOR_SECONDARY, linestyle="--", label="Bilinear error")
    ax_err.semilogx(freqs, accurate - reference, color=COLOR_PRIMARY, linestyle="-.", label="high_accuracy error")
    ax_err.axhline(-2.5, color="gray", linestyle=":", label="Class 1 lower limit @ 12.5 kHz")
    ax_err.set_ylabel("Error [dB]")
    ax_err.set_xlabel(LABEL_FREQ_HZ)
    ax_err.set_ylim(-8, 2)
    ax_err.legend(loc="lower left")

    for a in (ax, ax_err):
        xticks = [1000, 2000, 4000, 8000, 12500, 16000, 20000]
        a.set_xticks(xticks)
        a.set_xticklabels(["1k", "2k", "4k", "8k", "12.5k", "16k", "20k"])

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "weighting_accuracy_hf.png"))
    plt.close()


def generate_group_delay_comparison(output_dir: str) -> None:
    """Group delay of the 1 kHz band for every architecture (docs: filter-banks)."""
    print("Generating group_delay_comparison.png...")
    fs = 48000
    limits = [800.0, 1200.0]

    filters = [
        ("butter", "Butterworth", COLOR_PRIMARY, "-"),
        ("cheby1", "Chebyshev I", COLOR_SECONDARY, "--"),
        ("cheby2", "Chebyshev II", COLOR_TERTIARY, ":"),
        ("ellip", "Elliptic", "#9467bd", "-."),
        ("bessel", "Bessel", "#8c564b", "-"),
    ]

    _, ax = plt.subplots()
    for f_type, label, color, style in filters:
        bank = OctaveFilterBank(fs, fraction=1, order=6, limits=limits, filter_type=f_type)
        idx = int(np.argmin(np.abs(np.array(bank.freq) - 1000)))
        fsd = fs / bank.factor[idx]
        # Group delay of an SOS cascade = sum of the sections' group delays.
        w = np.logspace(np.log10(500), np.log10(2000), 1024)
        gd = np.zeros_like(w)
        for section in bank.sos[idx]:
            w_s, gd_s = scipy_signal.group_delay((section[:3], section[3:]), w=w, fs=fsd)
            gd += gd_s
        ax.semilogx(w, gd / fsd * 1000, label=label, color=color, linestyle=style)

    ax.set_title("Group Delay Comparison (1 kHz Octave Band, Order 6)", fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Group delay [ms]")
    ax.set_xlim(500, 2000)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([500, 707, 1000, 1414, 2000])
    ax.set_xticklabels(["500", "707", "1k", "1.41k", "2k"])
    ax.legend(loc="upper right")
    plt.savefig(themed_path(output_dir, "group_delay_comparison.png"))
    plt.close()


def generate_tone_burst_iec(output_dir: str) -> None:
    """FAST envelope response to 4 kHz tonebursts vs IEC 61672-1 Table 4 targets."""
    print("Generating tone_burst_iec.png...")
    fs = 48000

    from phonometry import time_weighting

    cases = [(0.2, -1.0), (0.05, -4.8), (0.01, -11.1)]  # Table 4, class 1 rows
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), sharey=True)

    t_all = np.arange(int(fs * 2.0)) / fs
    steady = np.sin(2 * np.pi * 4000 * t_all)
    ref = time_weighting(steady, fs, mode="fast")[int(1.5 * fs):].mean()

    for ax, (duration, target) in zip(axes, cases):
        burst = np.zeros_like(t_all)
        start = int(0.5 * fs)
        burst[start:start + round(duration * fs)] = steady[start:start + round(duration * fs)]
        env_db = 10 * np.log10(np.maximum(time_weighting(burst, fs, mode="fast") / ref, 1e-6))

        ax.plot(t_all, env_db, color=COLOR_PRIMARY, linewidth=1.3, label="FAST envelope")
        ax.axhline(target, color=COLOR_SECONDARY, linestyle="--", linewidth=1.2,
                   label=f"IEC target {target} dB")
        ax.set_title(f"{duration * 1000:g} ms burst", fontsize=11, fontweight="bold")
        ax.set_xlim(0.4, 1.4)
        ax.set_ylim(-30, 3)
        ax.set_xlabel("Time [s]")
        ax.legend(loc="upper right", fontsize=8)
    axes[0].set_ylabel("Level re steady state [dB]")

    fig.suptitle("4 kHz Toneburst Response vs IEC 61672-1 Table 4 (FAST)", fontweight="bold")
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "tone_burst_iec.png"))
    plt.close()


def generate_block_processing_continuity(output_dir: str) -> None:
    """Stateful vs stateless block processing (docs: block-processing)."""
    print("Generating block_processing_continuity.png...")
    fs = 8000
    n_blocks, block = 4, 1000
    rng = np.random.default_rng(42)
    x = rng.standard_normal(n_blocks * block)
    t = np.arange(len(x)) / fs

    def band_output(stateful: bool) -> np.ndarray:
        bank = OctaveFilterBank(fs, fraction=1, limits=[900, 1100],
                                stateful=stateful, resample=False)
        if stateful:
            parts = [
                bank.filter(x[i * block:(i + 1) * block], sigbands=True,
                            detrend=False, calculate_level=False)[2][0]
                for i in range(n_blocks)
            ]
        else:
            parts = []
            for i in range(n_blocks):
                b2 = OctaveFilterBank(fs, fraction=1, limits=[900, 1100], resample=False)
                parts.append(b2.filter(x[i * block:(i + 1) * block], sigbands=True,
                                       detrend=False, calculate_level=False)[2][0])
        return np.concatenate(parts)

    continuous = OctaveFilterBank(fs, fraction=1, limits=[900, 1100], resample=False).filter(
        x, sigbands=True, detrend=False, calculate_level=False)[2][0]
    y_stateful = band_output(stateful=True)
    y_stateless = band_output(stateful=False)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)
    zoom = slice(int(0.9 * block), int(1.4 * block))  # around the first boundary

    ax1.plot(t[zoom], continuous[zoom], color=COLOR_FG, linewidth=2.2, alpha=0.35,
             label="Continuous (whole signal)")
    ax1.plot(t[zoom], y_stateful[zoom], color=COLOR_PRIMARY, linewidth=1.1,
             label="Stateful blocks (state carried)")
    ax1.set_title("stateful=True: block outputs equal the continuous result",
                  fontsize=11, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=9)

    ax2.plot(t[zoom], continuous[zoom], color=COLOR_FG, linewidth=2.2, alpha=0.35,
             label="Continuous (whole signal)")
    ax2.plot(t[zoom], y_stateless[zoom], color=COLOR_SECONDARY, linewidth=1.1,
             label="Independent blocks (state reset)")
    ax2.axvline(block / fs, color=COLOR_FG, linestyle=":", alpha=0.6)
    ax2.annotate("block boundary:\nfilter transient restarts", xy=(block / fs, 0),
                 xytext=(block / fs + 0.02, ax2.get_ylim()[0] * 0.55 if ax2.get_ylim()[0] < 0 else -1),
                 fontsize=8, arrowprops={"arrowstyle": "->", "lw": 0.8})
    ax2.set_title("No state: each block restarts the filter transient",
                  fontsize=11, fontweight="bold")
    ax2.set_xlabel("Time [s]")
    ax2.legend(loc="upper right", fontsize=9)
    for a in (ax1, ax2):
        a.set_ylabel("Amplitude")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "block_processing_continuity.png"))
    plt.close()


def generate_class_mask_overlay(output_dir: str) -> None:
    """Band response against the IEC 61260-1:2014 class limit mask."""
    print("Generating class_mask_overlay.png...")
    fs = 48000

    from phonometry.compliance import class_limits

    bank = OctaveFilterBank(fs, fraction=1, order=6, limits=[800, 1200], filter_type="butter")
    idx = int(np.argmin(np.abs(np.array(bank.freq) - 1000)))
    fm = bank.freq[idx]
    fsd = fs / bank.factor[idx]
    w, h = scipy_signal.sosfreqz(bank.sos[idx], worN=2 ** 15, fs=fsd)
    attenuation = -20 * np.log10(np.abs(h) + 1e-12)
    a_ref = float(np.interp(fm, w, attenuation))
    omega = w / fm
    valid = (omega > 0.05) & (omega < 8)
    omega, delta_a = omega[valid], (attenuation - a_ref)[valid]

    grid = np.logspace(np.log10(0.05), np.log10(8), 2000)
    lo1, hi1 = class_limits(1.0, 1, grid)
    lo2, _ = class_limits(1.0, 2, grid)

    _, ax = plt.subplots(figsize=(10, 6.5))
    # Forbidden regions for class 1: below the minimum required attenuation
    # (stop band) and above the maximum allowed attenuation (pass band).
    ax.fill_between(grid, -10, lo1, color=COLOR_SECONDARY, alpha=0.15,
                    label="Forbidden for class 1 (too little attenuation)")
    finite = np.isfinite(hi1)
    ax.fill_between(grid[finite], hi1[finite], 90, color="#9467bd", alpha=0.15,
                    label="Forbidden for class 1 (too much attenuation)")
    ax.plot(grid, lo2, color=COLOR_TERTIARY, linestyle=":", linewidth=1.2,
            label="Class 2 minimum attenuation")

    ax.plot(omega, delta_a, color=COLOR_PRIMARY, linewidth=1.6,
            label="Butterworth order 6 (1 kHz octave band)")

    ax.set_xscale("log")
    ax.set_xlim(0.08, 8)
    ax.set_ylim(-6, 90)
    ax.set_title("Relative Attenuation vs IEC 61260-1:2014 Class Limits", fontweight="bold", pad=12)
    ax.set_xlabel("Normalized frequency  f / fm")
    ax.set_ylabel("Relative attenuation ΔA [dB]")
    ax.set_xticks([0.125, 0.25, 0.5, 0.707, 1, 1.414, 2, 4, 8])
    ax.set_xticklabels(["0.125", "0.25", "0.5", "0.707", "1", "1.41", "2", "4", "8"])
    ax.legend(loc="upper left", fontsize=9)
    plt.savefig(themed_path(output_dir, "class_mask_overlay.png"))
    plt.close()


def generate_og_image(output_path: str = "site/public/og-image.png") -> None:
    """FALLBACK social preview card (1200x630) for the docs site.

    Not wired into generate_all(): the committed site/public/og-image.png is
    a designed asset (AI-generated card chosen by the maintainer). Run this
    only if that asset is lost and a quick replacement is needed.
    """
    print("Generating og-image.png...")
    fs = 48000

    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor("#0f1216")

    # Background: 1/3-octave bank response, dimmed.
    ax_bg = fig.add_axes((0.0, 0.0, 1.0, 0.52))
    ax_bg.set_facecolor("none")
    bank = OctaveFilterBank(fs=fs, fraction=3, order=6, limits=[20.0, 20000.0])
    for idx in range(bank.num_bands):
        fsd = fs / bank.factor[idx]
        w, h = scipy_signal.sosfreqz(bank.sos[idx], worN=2048, fs=fsd)
        mag = 20 * np.log10(np.abs(h) + 1e-9)
        ax_bg.semilogx(w, mag, color="#1f77b4", alpha=0.55, linewidth=1.4)
    ax_bg.set_xlim(20, 20000)
    ax_bg.set_ylim(-40, 2)
    ax_bg.axis("off")

    fig.text(0.055, 0.82, "phonometry", color="white", fontsize=46, fontweight="bold")
    fig.text(0.057, 0.70, "Fractional octave analysis for Python", color="#a6d0ee", fontsize=22)
    fig.text(
        0.057, 0.60,
        "ANSI S1.11 / IEC 61260-1 filter banks  ·  IEC 61672-1 A/C/Z & Fast/Slow/Impulse  ·  Leq, LN, spectrograms",
        color="#8ea4b8", fontsize=13.5,
    )
    # Exact 1200x630: bypass the global savefig.bbox="tight" rcParam.
    with plt.rc_context({"savefig.bbox": None}):
        fig.savefig(output_path, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_calibration_stability(output_dir: str) -> None:
    """Stable vs unstable calibration tone against the IEC 60942 limit."""
    print("Generating calibration_stability.png...")
    from phonometry import time_weighting

    fs = 48000
    seconds = 6.0
    tt = np.arange(int(fs * seconds)) / fs
    stable = 0.5 * np.sin(2 * np.pi * 1000 * tt)
    # 3 % amplitude modulation at 2 Hz: ~0.14 dB deviation, clearly over
    unstable = 0.5 * (1 + 0.03 * np.sin(2 * np.pi * 2.0 * tt)) * np.sin(2 * np.pi * 1000 * tt)

    _, ax = plt.subplots(figsize=(10, 6))
    skip = fs  # discard the F-integrator attack (~8*tau = 1 s)
    for x, color, label in [
        (stable, COLOR_PRIMARY, "Stable tone (good coupling)"),
        (unstable, COLOR_SECONDARY, "3% AM tone (loose coupling)"),
    ]:
        env = time_weighting(x, fs, mode="fast")[skip:]
        level = 10 * np.log10(np.maximum(env, np.finfo(float).eps))
        rel = level - np.mean(level)
        ax.plot(tt[skip:], rel, color=color, linewidth=1.4, label=label)

    ax.axhline(0.07, color=COLOR_FG, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.axhline(-0.07, color=COLOR_FG, linestyle="--", linewidth=1.2, alpha=0.7,
               label="IEC 60942:2017 class 1 limit (deviation from mean)")
    ax.fill_between([1, seconds], -0.07, 0.07, color=COLOR_PRIMARY, alpha=0.06)
    ax.set_title("Calibration Tone Stability Check (IEC 60942:2017, 5.3.3)",
                 fontweight="bold", pad=12)
    ax.set_xlim(1, seconds)
    ax.set_ylim(-0.2, 0.2)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("F-weighted level re mean [dB]")
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "calibration_stability.png"))
    plt.close()


def generate_sel_concept(output_dir: str) -> None:
    """SEL: the whole event compressed into one second of equal energy."""
    print("Generating sel_concept.png...")
    from phonometry import leq, sel, time_weighting

    fs = 48000
    seconds = 8.0
    tt = np.arange(int(fs * seconds)) / fs
    rng = np.random.default_rng(11)
    # A vehicle pass-by: noise with a gaussian energy envelope
    envelope = np.exp(-0.5 * ((tt - 4.0) / 1.1) ** 2)
    x = envelope * rng.standard_normal(tt.size) * 0.3

    env = time_weighting(x, fs, mode="fast")
    level = 10 * np.log10(np.maximum(env, 1e-12))
    l_sel = float(sel(x, fs, dbfs=True))
    l_eq = float(leq(x, fs, dbfs=True))

    _, ax = plt.subplots(figsize=(10, 6))
    ax.plot(tt, level, color=COLOR_PRIMARY, linewidth=1.2,
            label="Fast level of the event")
    ax.hlines(l_eq, 0, seconds, color=COLOR_TERTIARY, linestyle="--",
              linewidth=1.6, label="Leq over the whole event")
    # SEL: same energy squeezed into 1 s (drawn as a 1 s block)
    ax.fill_between([3.5, 4.5], -55, l_sel, color=COLOR_SECONDARY, alpha=0.25)
    ax.hlines(l_sel, 3.5, 4.5, color=COLOR_SECONDARY, linewidth=2.2,
              label="SEL: same energy in 1 s")
    ax.annotate("equal energy", xy=(4.5, l_sel - 3), xytext=(5.6, l_sel - 1),
                fontsize=10, arrowprops={"arrowstyle": "->", "lw": 0.9})
    ax.set_title("Sound Exposure Level: the event normalized to 1 s",
                 fontweight="bold", pad=12)
    ax.set_xlim(0, seconds)
    ax.set_ylim(-55, l_sel + 6)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Level [dBFS]")
    ax.legend(loc="lower left", fontsize=9)
    plt.savefig(themed_path(output_dir, "sel_concept.png"))
    plt.close()


def generate_lden_profile(output_dir: str) -> None:
    """A 24 h urban level profile with the Lden period weightings."""
    print("Generating lden_profile.png...")
    from phonometry import lden

    hours = np.arange(24)
    # Typical urban road profile (synthetic hourly LAeq, dB)
    laeq_h = np.array([48, 46, 45, 45, 46, 50, 56, 64, 66, 65, 63, 63,
                       64, 63, 63, 64, 65, 66, 65, 64, 63, 62, 61, 50],
                      dtype=float)

    def _period_leq(idx: "np.ndarray") -> float:
        return float(10 * np.log10(np.mean(10 ** (0.1 * laeq_h[idx]))))

    ld = _period_leq(np.arange(7, 19))    # day 07-19
    le = _period_leq(np.arange(19, 23))   # evening 19-23
    ln_ = _period_leq(np.r_[np.arange(23, 24), np.arange(0, 7)])  # night 23-07
    l_den = lden(ld, le, ln_)

    _, ax = plt.subplots(figsize=(10, 6))
    ax.axvspan(7, 19, color=COLOR_TERTIARY, alpha=0.10)
    ax.axvspan(19, 23, color="#e8a838", alpha=0.15)
    ax.axvspan(23, 24, color=COLOR_PRIMARY, alpha=0.12)
    ax.axvspan(0, 7, color=COLOR_PRIMARY, alpha=0.12)
    ax.step(np.r_[hours, 24], np.r_[laeq_h, laeq_h[-1]], where="post",
            color=COLOR_FG, linewidth=1.6, label="Hourly LAeq")
    ax.hlines(ld, 7, 19, color=COLOR_TERTIARY, linestyle="--", linewidth=2,
              label="Lday (+0 dB)")
    ax.hlines(le + 5, 19, 23, color="#e8a838", linestyle="--", linewidth=2,
              label="Levening + 5 dB")
    ax.hlines(ln_ + 10, 23, 24, color=COLOR_PRIMARY, linestyle="--", linewidth=2)
    ax.hlines(ln_ + 10, 0, 7, color=COLOR_PRIMARY, linestyle="--", linewidth=2,
              label="Lnight + 10 dB")
    ax.hlines(l_den, 0, 24, color=COLOR_SECONDARY, linewidth=2.4,
              label=f"Lden = {l_den:.1f} dB")
    ax.set_title("Day-Evening-Night Level Lden (ISO 1996-1)",
                 fontweight="bold", pad=12)
    ax.set_xlim(0, 24)
    ax.set_ylim(42, 80)
    ax.set_xticks([0, 4, 7, 12, 16, 19, 23])
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Level [dB]")
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    plt.savefig(themed_path(output_dir, "lden_profile.png"))
    plt.close()


def generate_tonality_spectrum(output_dir: str) -> None:
    """Annotated spectrum for the tone-to-noise ratio method."""
    print("Generating tonality_spectrum.png...")
    from phonometry import tone_to_noise_ratio
    from phonometry.tonality import _averaged_spectrum, _critical_band

    fs = 48000
    rng = np.random.default_rng(21)
    tt = np.arange(fs * 30) / fs
    x = (np.sqrt(2) * 0.1 * np.sin(2 * np.pi * 1000 * tt)
         + 0.05 * rng.standard_normal(tt.size))
    result = tone_to_noise_ratio(x, fs)
    freqs, power, _ = _averaged_spectrum(x - np.mean(x), fs, 1.0)
    f1, f2, _ = _critical_band(result.frequency)

    _, ax = plt.subplots(figsize=(10, 6))
    sel_band = (freqs > 700) & (freqs < 1400)
    db = 10 * np.log10(np.maximum(power, 1e-18))
    ax.plot(freqs[sel_band], db[sel_band], color=COLOR_PRIMARY, linewidth=1.0,
            label="Averaged FFT spectrum (Hann)")
    ax.axvspan(f1, f2, color=COLOR_TERTIARY, alpha=0.15,
               label="Critical band around the tone")
    ax.axvline(result.frequency, color=COLOR_SECONDARY, linewidth=1.4,
               linestyle="--")
    ax.annotate(
        f"TNR = {result.ratio_db:.1f} dB\n(criterion {result.criterion_db:.1f} dB)",
        xy=(result.frequency, db.max() - 2), xytext=(1120, db.max() - 8),
        fontsize=11, arrowprops={"arrowstyle": "->", "lw": 1.0},
    )
    ax.set_title("Tone-to-Noise Ratio (ECMA-418-1, clause 11)",
                 fontweight="bold", pad=12)
    ax.set_xlim(700, 1400)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Bin power [dB]")
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "tonality_spectrum.png"))
    plt.close()


def generate_loudness_pattern(output_dir: str) -> None:
    """Specific loudness N'(z) of a narrowband vs a broadband sound."""
    print("Generating loudness_pattern.png...")
    from phonometry import loudness_zwicker_from_spectrum

    # 28 one-third-octave band levels, 25 Hz .. 12.5 kHz (ISO 532-1
    # clause 5.3). Index 16 is the 1 kHz band.
    narrow_levels = np.full(28, -60.0)
    narrow_levels[16] = 60.0
    narrow = loudness_zwicker_from_spectrum(narrow_levels)
    flat = loudness_zwicker_from_spectrum(np.full(28, 60.0))

    z = np.arange(1, 241) * 0.1  # 0.1-Bark steps up to 24 Bark

    _, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(z, flat.specific, color=COLOR_SECONDARY, alpha=0.25)
    ax.plot(z, flat.specific, color=COLOR_SECONDARY, linewidth=1.6,
            label=f"Flat broadband 60 dB - N = {flat.loudness:.1f} sone")
    ax.fill_between(z, narrow.specific, color=COLOR_PRIMARY, alpha=0.35)
    ax.plot(z, narrow.specific, color=COLOR_PRIMARY, linewidth=1.6,
            label=f"1 kHz narrowband - N = {narrow.loudness:.1f} sone")

    peak_z = float(z[np.argmax(narrow.specific)])
    ax.annotate(
        "Shaded area = total loudness N",
        xy=(peak_z + 0.6, float(narrow.specific.max()) * 0.45),
        xytext=(12.5, float(narrow.specific.max()) * 0.75),
        fontsize=10, arrowprops={"arrowstyle": "->", "lw": 0.9},
    )
    ax.set_title("Specific Loudness Pattern (ISO 532-1 Zwicker)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Critical-band rate z [Bark]")
    ax.set_ylabel("Specific loudness N' [sone/Bark]")
    ax.set_xlim(0, 24)
    # Headroom above the tallest pattern so the legend stays clear of it.
    ax.set_ylim(0, float(flat.specific.max()) * 1.28)
    ax.set_xticks([0, 4, 8, 12, 16, 20, 24])
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "loudness_pattern.png"))
    plt.close()


def generate_sti_curve(output_dir: str) -> None:
    """STI vs reverberation time: pipeline points vs the analytic MTF."""
    print("Generating sti_vs_t60.png...")
    from phonometry import sti_from_impulse_response

    fs = 48000
    t60_points = [0.3, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0]

    # The 14 full-STI modulation frequencies and the male alpha/beta
    # factors of IEC 60268-16 Ed.5 Table A.1 (phonometry.sti keeps them
    # private, so they are restated here for the analytic reference).
    mod_freqs = np.array([0.63, 0.80, 1.00, 1.25, 1.60, 2.00, 2.50,
                          3.15, 4.00, 5.00, 6.30, 8.00, 10.0, 12.5])
    alpha = np.array([0.085, 0.127, 0.230, 0.233, 0.309, 0.224, 0.173])
    beta = np.array([0.085, 0.078, 0.065, 0.011, 0.047, 0.095])

    def analytic_sti(t60: float) -> float:
        # Schroeder MTF of an exponential decay: m(F) = 1/sqrt(1+(2*pi*F*T/13.8)^2)
        m = 1.0 / np.sqrt(1.0 + (2 * np.pi * mod_freqs * t60 / 13.8) ** 2)
        snr_eff = np.clip(10 * np.log10(m / (1 - m)), -15.0, 15.0)
        mti = np.full(7, ((snr_eff + 15.0) / 30.0).mean())
        return float(np.dot(alpha, mti) - np.dot(beta, np.sqrt(mti[:-1] * mti[1:])))

    rng = np.random.default_rng(2026)
    measured = []
    for t60 in t60_points:
        t = np.arange(int(2 * t60 * fs)) / fs
        ir = rng.standard_normal(t.size) * np.exp(-6.9077 * t / t60)
        measured.append(sti_from_impulse_response(ir, fs).sti)

    t_dense = np.logspace(np.log10(0.25), np.log10(6.0), 200)
    sti_dense = [analytic_sti(float(t)) for t in t_dense]

    _, ax = plt.subplots(figsize=(10, 6))
    # Annex F qualification bands (informative): edges 0.36 .. 0.76.
    edges = [0.36, 0.40, 0.44, 0.48, 0.52, 0.56, 0.60, 0.64, 0.68, 0.72, 0.76]
    letters = ["U", "J", "I", "H", "G", "F", "E", "D", "C", "B", "A", "A+"]
    y_min, y_max = 0.15, 0.95
    bounds = [y_min] + edges + [y_max]
    cmap = plt.get_cmap("RdYlGn")
    for i, letter in enumerate(letters):
        lo, hi = bounds[i], bounds[i + 1]
        ax.axhspan(lo, hi, color=cmap(i / (len(letters) - 1)), alpha=0.13, lw=0)
        ax.text(0.985, (lo + hi) / 2, letter, transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=8, color=COLOR_FG, alpha=0.7)
    ax.text(0.92, 0.985, "Annex F rating", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color=COLOR_FG, alpha=0.7)

    ax.plot(t_dense, sti_dense, color=COLOR_PRIMARY, linestyle="--",
            linewidth=1.5, label="Analytic Schroeder MTF (closed form)")
    ax.plot(t60_points, measured, "o", color=COLOR_SECONDARY, markersize=7,
            markerfacecolor="white", markeredgewidth=1.6,
            label="Measured (sti_from_impulse_response)")

    ax.set_xscale("log")
    ax.set_title("STI vs Reverberation Time (IEC 60268-16)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Reverberation time T60 [s]")
    ax.set_ylabel("STI")
    ax.set_xlim(0.25, 6.0)
    ax.set_ylim(y_min, y_max)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(t60_points)
    ax.set_xticklabels(["0.3", "0.5", "0.8", "1.2", "2", "3", "5"])
    ax.legend(loc="lower left", fontsize=9)
    plt.savefig(themed_path(output_dir, "sti_vs_t60.png"))
    plt.close()


def generate_intensity_demo(output_dir: str) -> None:
    """p-p intensity: plane progressive wave vs reactive standing wave."""
    print("Generating intensity_demo.png...")
    from phonometry import sound_intensity

    fs = 48000
    dr, c = 0.012, 343.0
    duration = 4.0
    n = int(fs * duration)

    # Broadband noise, band-limited and scaled to ~70 dB SPL, in pascals.
    rng = np.random.default_rng(2026)
    noise = rng.standard_normal(n)
    sos = scipy_signal.butter(4, [80.0, 6000.0], btype="bandpass", fs=fs, output="sos")
    noise = scipy_signal.sosfilt(sos, noise)
    noise *= 0.063 / np.std(noise)

    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / fs)
    k = 2 * np.pi * freqs / c

    # Plane progressive wave: microphone 2 sees the wave dr/c later.
    p1_plane = noise
    p2_plane = np.fft.irfft(spectrum * np.exp(-2j * np.pi * freqs * dr / c), n)
    plane = sound_intensity(p1_plane, p2_plane, fs, dr, fraction=3, limits=[100.0, 5000.0])

    # Standing wave: equal counter-propagating waves, probe centred at x0.
    x0 = 0.30
    def standing_pressure(pos: float) -> np.ndarray:
        return np.fft.irfft(spectrum * 2.0 * np.cos(k * pos), n)
    standing = sound_intensity(
        standing_pressure(x0 - dr / 2), standing_pressure(x0 + dr / 2),
        fs, dr, fraction=3, limits=[100.0, 5000.0],
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, res, title in [
        (ax1, plane, "Plane wave: Lp ≈ LI"),
        (ax2, standing, "Standing wave: reactive field"),
    ]:
        ax.semilogx(res.frequency, res.pressure_level, marker="o", markersize=5,
                    color=COLOR_PRIMARY, linewidth=1.5, markerfacecolor="white",
                    markeredgewidth=1.3, label="Pressure level Lp")
        ax.semilogx(res.frequency, res.intensity_level, marker="s", markersize=5,
                    color=COLOR_SECONDARY, linewidth=1.5, linestyle="--",
                    markerfacecolor="white", markeredgewidth=1.3,
                    label="Intensity level LI")
        apply_axis_styling(ax, title, xlim=(90, 5600), ylim=(0, 85))
        # The standard octave ticks extend past the band range: re-clamp.
        ax.set_xlim(90, 5600)
        dpi_db = round(float(res.total_pressure_intensity_index), 1) + 0.0
        ax.text(0.05, 0.33, f"Pressure-intensity index\nδpI = {dpi_db:.1f} dB",
                transform=ax.transAxes, fontsize=10, va="bottom", color=COLOR_FG)
        ax.legend(loc="upper right", fontsize=9)
    ax2.set_ylabel("")

    fig.suptitle("Sound Intensity with a p-p Probe (IEC 61043)", fontweight="bold")
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "intensity_demo.png"))
    plt.close()


def generate_schroeder_decay(output_dir: str) -> None:
    """Schroeder backward integration with T20/T30/EDT regressions (ISO 3382)."""
    print("Generating schroeder_decay.png...")
    from phonometry import decay_curve, room_parameters
    from phonometry.room_acoustics import (
        _EDT_RANGE,
        _T20_RANGE,
        _T30_RANGE,
        _onset_index,
    )

    fs = 48000
    reverb_t = 1.2  # target reverberation time (s)
    duration = 2.5
    rng = np.random.default_rng(2026)
    t = np.arange(int(duration * fs)) / fs
    # Exponential decay (T = 1.2 s) excited by white noise + a realistic
    # background-noise floor (~-45 dB re the peak envelope).
    ir = rng.standard_normal(t.size) * np.exp(-6.9077 * t / reverb_t)
    ir = ir + rng.standard_normal(t.size) * 10.0 ** (-45.0 / 20.0)

    # Library outputs: the annotated numbers are exactly these.
    time, level = decay_curve(ir, fs)
    res = room_parameters(ir, fs, limits=None)
    edt, t20, t30 = float(res.edt[0]), float(res.t20[0]), float(res.t30[0])

    # Raw squared-IR level trace (onset-trimmed, normalized to its peak):
    # the noisy line the backward integration smooths into the decay curve.
    p2 = ir.astype(np.float64) ** 2
    p2 = p2[_onset_index(p2):]
    t_raw = np.arange(p2.size) / fs
    raw_db = 10.0 * np.log10(np.maximum(p2, p2.max() * 1e-12) / p2.max())

    def fit_line(decay_range: tuple[float, float]) -> tuple[float, float]:
        """Least-squares (slope, intercept) over an evaluation range,
        replicating room_acoustics._fit_decay_time so the drawn line has
        slope -60/T with the annotated T."""
        mask = (level <= -decay_range[0]) & (level >= -decay_range[1])
        slope, intercept = np.polyfit(time[mask], level[mask], 1)
        return float(slope), float(intercept)

    _, ax = plt.subplots(figsize=(10, 6.5))
    ax.plot(t_raw, raw_db, color="gray", alpha=0.28, linewidth=0.6, zorder=0,
            label="Raw squared IR level")
    ax.plot(time, level, color=COLOR_PRIMARY, linewidth=2.4, zorder=5,
            label="Schroeder decay curve")

    lines = [
        (_EDT_RANGE, "#9467bd", "-", "EDT fit (0 to −10 dB)", (0.0, -13.0)),
        (_T20_RANGE, COLOR_SECONDARY, "--", "T20 fit (−5 to −25 dB)", (0.0, -60.0)),
        (_T30_RANGE, COLOR_TERTIARY, "-.", "T30 fit (−5 to −35 dB)", (0.0, -60.0)),
    ]
    for decay_range, color, style, label, (lo, hi) in lines:
        slope, intercept = fit_line(decay_range)
        t_lo, t_hi = (lo - intercept) / slope, (hi - intercept) / slope
        ax.plot([t_lo, t_hi], [lo, hi], color=color, linestyle=style,
                linewidth=1.7, zorder=4, label=label)

    # Evaluation levels -5 / -25 / -35 dB and the decay-curve crossings.
    for target in (-5.0, -25.0, -35.0):
        ax.axhline(target, color=COLOR_FG, linestyle=":", alpha=0.35, linewidth=1)
        t_cross = float(np.interp(target, level[::-1], time[::-1]))
        ax.plot(t_cross, target, "o", color=COLOR_FG, markersize=5, zorder=6)
        # Place level labels clear of the upper-right legend.
        ax.text(1.40, target + 0.8, f"{target:.0f} dB", ha="left",
                va="bottom", fontsize=8, color=COLOR_FG, alpha=0.85)

    ax.text(0.12, -7.0, "EDT slope", fontsize=8, color="#9467bd", rotation=0)
    facecolor = plt.rcParams["axes.facecolor"]
    ax.text(0.04, 0.06,
            f"EDT = {edt:.2f} s\nT20 = {t20:.2f} s\nT30 = {t30:.2f} s",
            transform=ax.transAxes, va="bottom", ha="left", fontsize=11,
            bbox={"boxstyle": "round", "facecolor": facecolor,
                  "edgecolor": COLOR_FG, "alpha": 0.85})

    ax.set_title("Schroeder Integration and Reverberation Time (ISO 3382)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Level re steady state [dB]")
    ax.set_xlim(0, duration)
    ax.set_ylim(-65, 3)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "schroeder_decay.png"))
    plt.close()


def generate_excitation_signals(output_dir: str) -> None:
    """ISO 18233 excitations: ESS waveform + spectrogram and MLS + spectrum."""
    print("Generating excitation_signals.png...")
    from phonometry import mls_signal, sweep_signal

    fs = 48000
    f1, f2, secs = 50.0, 20000.0, 1.0
    sweep = sweep_signal(fs, f1, f2, secs)
    t = np.arange(sweep.size) / fs
    mls = mls_signal(12)  # length 2**12 - 1 = 4095

    fig, axes = plt.subplots(2, 2, figsize=(12, 7.2))
    (ax_sw, ax_sp), (ax_ml, ax_ms) = axes

    # Exponential sine sweep: time-domain waveform.
    ax_sw.plot(t, sweep, color=COLOR_PRIMARY, linewidth=0.5)
    ax_sw.set_title("Exponential sine sweep — waveform", fontweight="bold")
    ax_sw.set_xlabel("Time [s]")
    ax_sw.set_ylabel("Amplitude")
    ax_sw.set_xlim(0.0, secs)
    ax_sw.set_ylim(-1.2, 1.2)
    ax_sw.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)

    # Sweep spectrogram: the exponential frequency rise.
    ax_sp.specgram(sweep, NFFT=1024, Fs=fs, noverlap=512, cmap="magma")
    ax_sp.set_title("Sweep spectrogram (exponential rise)", fontweight="bold")
    ax_sp.set_xlabel("Time [s]")
    ax_sp.set_ylabel("Frequency [Hz]")
    ax_sp.set_ylim(0.0, fs / 2)

    # MLS: first samples of the bipolar sequence.
    show = 100
    ax_ml.step(np.arange(show), mls[:show], where="mid", color=COLOR_PRIMARY,
               linewidth=1.2)
    ax_ml.set_title(f"MLS — first {show} of {mls.size} samples", fontweight="bold")
    ax_ml.set_xlabel("Sample")
    ax_ml.set_ylabel("Amplitude")
    ax_ml.set_ylim(-1.4, 1.4)
    ax_ml.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)

    # MLS magnitude spectrum: essentially flat (white excitation).
    spec = np.abs(np.fft.rfft(mls))
    freqs = np.fft.rfftfreq(mls.size, d=1.0 / fs)
    ax_ms.semilogx(freqs[1:], 20.0 * np.log10(spec[1:] / np.median(spec[1:])),
                   color=COLOR_SECONDARY, linewidth=0.7)
    ax_ms.set_title("MLS magnitude spectrum (flat)", fontweight="bold")
    ax_ms.set_xlabel("Frequency [Hz]")
    ax_ms.set_ylabel("Magnitude [dB]")
    ax_ms.set_xlim(20.0, fs / 2)
    ax_ms.set_ylim(-12.0, 12.0)
    ax_ms.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)

    fig.suptitle("ISO 18233 excitation signals", fontweight="bold")
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "excitation_signals.png"))
    plt.close()


def generate_impulse_response(output_dir: str) -> None:
    """ISO 18233 recovered IR: waveform + log-magnitude / Schroeder decay."""
    print("Generating impulse_response.png...")
    from scipy.signal import fftconvolve

    from phonometry import impulse_response, sweep_signal

    fs = 48000
    sweep = sweep_signal(fs, 20.0, 20000.0, 1.5)

    # A synthetic room: direct sound, two early reflections and an
    # exponentially decaying diffuse tail (T ~ 0.6 s) plus a low noise floor.
    rng = np.random.default_rng(2026)
    n = int(0.7 * fs)
    system = np.zeros(n)
    system[80] = 1.0                       # direct sound
    system[1400] = 0.5                     # early reflection
    system[3100] = 0.32                    # second reflection
    tail_t = np.arange(n) / fs
    system += rng.standard_normal(n) * np.exp(-6.9077 * tail_t / 0.6) * 0.08
    system += rng.standard_normal(n) * 10.0 ** (-60.0 / 20.0)

    recorded = fftconvolve(sweep, system)
    ir = impulse_response(recorded, sweep, fs, length=n)

    h = np.asarray(ir, dtype=np.float64)
    time = np.arange(h.size) / fs
    peak = float(np.max(np.abs(h)))
    tiny = np.finfo(np.float64).tiny
    env_db = 20.0 * np.log10(np.maximum(np.abs(h), tiny) / peak)
    energy = np.cumsum(h[::-1] ** 2)[::-1]
    edc_db = 10.0 * np.log10(np.maximum(energy, tiny) / energy[0])

    fig, (ax_w, ax_d) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax_w.plot(time, h / peak, color=COLOR_PRIMARY, linewidth=0.7)
    ax_w.set_title("Recovered room impulse response (ISO 18233)",
                   fontweight="bold", pad=10)
    ax_w.set_ylabel("Amplitude (norm.)")
    ax_w.set_ylim(-1.1, 1.1)
    ax_w.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_w.annotate("direct sound", xy=(80 / fs, 1.0), xytext=(0.06, 0.86),
                  textcoords="axes fraction", fontsize=9, color=COLOR_FG,
                  arrowprops={"arrowstyle": "->", "color": COLOR_FG, "alpha": 0.7})
    ax_w.annotate("reflections", xy=(1400 / fs, 0.5), xytext=(0.20, 0.62),
                  textcoords="axes fraction", fontsize=9, color=COLOR_FG,
                  arrowprops={"arrowstyle": "->", "color": COLOR_FG, "alpha": 0.7})

    ax_d.plot(time, env_db, color="#9ecae1", linewidth=0.7,
              label="Log-magnitude envelope")
    ax_d.plot(time, edc_db, color=COLOR_SECONDARY, linewidth=1.9,
              label="Schroeder decay (EDC)")
    ax_d.set_xlabel("Time [s]")
    ax_d.set_ylabel("Level re peak [dB]")
    ax_d.set_xlim(0.0, n / fs)
    ax_d.set_ylim(-80.0, 5.0)
    ax_d.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_d.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "impulse_response.png"))
    plt.close()


def generate_insulation_rating(output_dir: str) -> None:
    """ISO 717-1 weighted rating: measured R', shifted reference, deviations."""
    print("Generating insulation_rating.png...")
    from phonometry.insulation import (
        _INDEX_500_THIRD,
        _REF_THIRD_OCTAVE,
        weighted_rating,
    )

    # ISO 717-1 Annex C worked example (Table C.1), 100 Hz .. 3150 Hz.
    freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
                      1000, 1250, 1600, 2000, 2500, 3150], dtype=float)
    measured = np.array([20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
                         28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5])

    result = weighted_rating(measured)
    reference = np.asarray(_REF_THIRD_OCTAVE, dtype=float)
    shift = result.rating - _REF_THIRD_OCTAVE[_INDEX_500_THIRD]
    shifted = reference + shift  # shifted reference read at 500 Hz == Rw

    _, ax = plt.subplots(figsize=(10, 6.5))
    ax.fill_between(freqs, measured, shifted, where=(measured < shifted).tolist(),
                    interpolate=True, color=COLOR_SECONDARY, alpha=0.25,
                    zorder=1, label="Unfavourable deviations")
    ax.semilogx(freqs, shifted, marker="s", color=COLOR_FG, linewidth=1.6,
                linestyle="--", markersize=4, zorder=3,
                label="Shifted reference curve (ISO 717-1)")
    ax.semilogx(freqs, measured, marker="o", color=COLOR_PRIMARY, linewidth=1.8,
                markersize=5, markerfacecolor="white", markeredgewidth=1.4,
                zorder=4, label="Measured R' (third octave)")

    # Rw is the shifted reference read at 500 Hz.
    ax.axvline(500, color=COLOR_FG, linestyle=":", alpha=0.4)
    ax.plot(500, result.rating, "D", color=COLOR_SECONDARY, markersize=9, zorder=6)
    ax.annotate(f"Rw = {result.rating} dB", xy=(500, result.rating),
                xytext=(560, result.rating - 9), fontsize=12, fontweight="bold",
                arrowprops={"arrowstyle": "->", "lw": 1.0})

    for dy, text in (
        (0.97, f"Reference curve shifted by {shift} dB"),
        (0.90, f"Sum of unfavourable deviations = {result.unfavourable_sum:.1f}"
               f" dB  (limit 32.0 dB)"),
        (0.83, f"Rw (C ; Ctr) = {result.rating} "
               f"({result.c:+d} ; {result.ctr:+d}) dB"),
    ):
        ax.text(0.03, dy, text, transform=ax.transAxes, va="top", ha="left",
                fontsize=9.5, color=COLOR_FG)

    ax.set_title("ISO 717-1 Weighted Sound Reduction Index (Annex C example)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Apparent sound reduction index R' [dB]")
    ax.set_xscale("log")
    ax.set_xlim(90, 3600)
    ax.set_ylim(8, 44)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(freqs)
    ax.set_xticklabels(
        ["100", "125", "160", "200", "250", "315", "400", "500", "630", "800",
         "1k", "1.25k", "1.6k", "2k", "2.5k", "3.15k"], fontsize=8)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.legend(loc="lower right", fontsize=9)
    plt.savefig(themed_path(output_dir, "insulation_rating.png"))
    plt.close()


def generate_impact_rating(output_dir: str) -> None:
    """ISO 717-2 weighted impact rating: measured Ln, shifted reference, CI."""
    print("Generating impact_rating.png...")
    from phonometry.insulation import (
        _INDEX_500_THIRD,
        _REF_IMPACT_THIRD_OCTAVE,
        weighted_impact_rating,
    )

    # ISO 717-2 Annex C worked example (Table C.1): laboratory bare massive
    # floor, one-third octave 100 Hz .. 3150 Hz.
    freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
                      1000, 1250, 1600, 2000, 2500, 3150], dtype=float)
    measured = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
                         73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])

    result = weighted_impact_rating(measured)
    reference = np.asarray(_REF_IMPACT_THIRD_OCTAVE, dtype=float)
    shift = result.rating - _REF_IMPACT_THIRD_OCTAVE[_INDEX_500_THIRD]
    shifted = reference + shift  # shifted reference read at 500 Hz == Ln,w

    _, ax = plt.subplots(figsize=(10, 6.5))
    # For impact sound an unfavourable deviation occurs where the MEASURED
    # curve lies ABOVE the reference (opposite sign to ISO 717-1 airborne).
    ax.fill_between(freqs, shifted, measured, where=(measured > shifted).tolist(),
                    interpolate=True, color=COLOR_SECONDARY, alpha=0.25,
                    zorder=1, label="Unfavourable deviations (measured above reference)")
    ax.semilogx(freqs, shifted, marker="s", color=COLOR_FG, linewidth=1.6,
                linestyle="--", markersize=4, zorder=3,
                label="Shifted reference curve (ISO 717-2)")
    ax.semilogx(freqs, measured, marker="o", color=COLOR_PRIMARY, linewidth=1.8,
                markersize=5, markerfacecolor="white", markeredgewidth=1.4,
                zorder=4, label="Measured Ln (third octave)")

    # Ln,w is the shifted reference read at 500 Hz.
    ax.axvline(500, color=COLOR_FG, linestyle=":", alpha=0.4)
    ax.plot(500, result.rating, "D", color=COLOR_SECONDARY, markersize=9, zorder=6)
    # The annotation sits in the clear gap between the rising measured curve
    # and the flat low-frequency reference plateau; the string is identical
    # in both languages, so the placement holds for every variant.
    ax.annotate(f"Ln,w = {result.rating} dB", xy=(500, result.rating),
                xytext=(135, result.rating - 4.2), fontsize=12,
                fontweight="bold",
                arrowprops={"arrowstyle": "->", "lw": 1.0})

    for dy, text in (
        (0.97, f"Reference curve shifted by {shift} dB"),
        (0.90, f"Sum of unfavourable deviations = {result.unfavourable_sum:.1f}"
               f" dB  (limit 32.0 dB)"),
        (0.83, f"Ln,w = {result.rating} dB ; CI = {result.ci:+d} dB"),
    ):
        ax.text(0.03, dy, text, transform=ax.transAxes, va="top", ha="left",
                fontsize=9.5, color=COLOR_FG)

    ax.set_title("ISO 717-2 Weighted Normalized Impact Sound Level "
                 "(Annex C example)", fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Normalized impact sound pressure level Ln [dB]")
    ax.set_xscale("log")
    ax.set_xlim(90, 3600)
    ax.set_ylim(55, 86)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(freqs)
    ax.set_xticklabels(
        ["100", "125", "160", "200", "250", "315", "400", "500", "630", "800",
         "1k", "1.25k", "1.6k", "2k", "2.5k", "3.15k"], fontsize=8)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.legend(loc="lower left", fontsize=9)
    plt.savefig(themed_path(output_dir, "impact_rating.png"))
    plt.close()


def generate_sharpness_weighting(output_dir: str) -> None:
    """DIN 45692 sharpness weighting g(z): DIN vs Aures vs von Bismarck."""
    print("Generating sharpness_weighting.png...")
    from phonometry.sharpness import _Z, _g_aures, _g_bismarck, _g_din

    z = _Z                       # 0.1 .. 24 Bark, 0.1-Bark steps
    total_n = 4.0                # reference loudness for the Aures variant (sone)
    g_din = _g_din(z)
    g_bismarck = _g_bismarck(z)
    g_aures = _g_aures(z, total_n)

    _, ax = plt.subplots(figsize=(10, 6.5))
    ax.semilogy(z, g_din, color=COLOR_PRIMARY, linewidth=2.2,
                label="DIN 45692 g(z)")
    ax.semilogy(z, g_bismarck, color=COLOR_TERTIARY, linewidth=1.7,
                linestyle="--", label="von Bismarck (Annex B)")
    ax.semilogy(z, g_aures, color=COLOR_SECONDARY, linewidth=1.7,
                linestyle="-.", label=f"Aures (Annex B, N = {total_n:.0f} sone)")

    # DIN weighting is flat (g = 1) up to 15.8 Bark, von Bismarck up to 15.
    ax.axhline(1.0, color=COLOR_FG, linestyle="-", alpha=0.15, linewidth=1)
    ax.axvline(15.8, color=COLOR_PRIMARY, linestyle=":", alpha=0.5, linewidth=1)
    ax.axvline(15.0, color=COLOR_TERTIARY, linestyle=":", alpha=0.5, linewidth=1)
    ax.annotate("DIN knee\n15.8 Bark", xy=(15.8, 1.0), xytext=(10.2, 2.3),
                fontsize=9, color=COLOR_PRIMARY, ha="center",
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_PRIMARY})
    ax.annotate("Bismarck knee\n15 Bark", xy=(15.0, 1.0), xytext=(7.0, 0.5),
                fontsize=9, color=COLOR_TERTIARY, ha="center",
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_TERTIARY})

    ax.set_title("Sharpness Weighting g(z) (DIN 45692)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Critical-band rate z [Bark]")
    ax.set_ylabel("Weighting g(z)")
    ax.set_xlim(0, 24)
    ax.set_ylim(0.4, 30)
    ax.set_xticks([0, 4, 8, 12, 16, 20, 24])
    ax.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "sharpness_weighting.png"))
    plt.close()


def generate_open_plan_decay(output_dir: str) -> None:
    """ISO 3382-3 spatial decay: speech SPL and STI vs source distance."""
    print("Generating open_plan_decay.png...")
    from phonometry import open_plan_metrics

    # The worked example from the room-acoustics guide (matches its numbers).
    r = np.array([2.0, 4.0, 6.0, 8.0, 12.0, 16.0])   # distances (m)
    lp = 65.0 - 7.0 * np.log2(r)                      # A-weighted speech level (dB)
    sti = 0.70 - 0.03 * r                             # STI per position
    m = open_plan_metrics(r, lp, sti)

    # Reconstruct the two regressions the metrics come from (2-16 m window).
    b_log = -m.d2s / np.log10(2.0)                    # slope vs lg(r/r0)
    a_lp = m.lp_as_4m - b_log * np.log10(4.0)
    d_sti, c_sti = np.polyfit(r, sti, 1)              # STI vs distance

    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.set_xscale("log")
    rr = np.logspace(np.log10(2.0), np.log10(16.0), 100)
    line_spl, = ax.plot(rr, a_lp + b_log * np.log10(rr), color=COLOR_PRIMARY,
                        linestyle="--", linewidth=1.8,
                        label=f"Spatial decay D2,S = {m.d2s:.1f} dB")
    pts_spl, = ax.plot(r, lp, "o", color=COLOR_PRIMARY, markersize=7,
                       markerfacecolor="white", markeredgewidth=1.6,
                       label="Measured Lp,A,S")
    ax.axvline(4.0, color=COLOR_FG, linestyle=":", alpha=0.35, linewidth=1)
    mark_4m, = ax.plot(4.0, m.lp_as_4m, "D", color=COLOR_SECONDARY, markersize=9,
                       zorder=6, label=f"Lp,A,S,4m = {m.lp_as_4m:.0f} dB")
    ax.annotate(f"Lp,A,S,4m = {m.lp_as_4m:.0f} dB", xy=(4.0, m.lp_as_4m),
                xytext=(4.7, m.lp_as_4m + 4.5), fontsize=10,
                arrowprops={"arrowstyle": "->", "lw": 1.0})

    ax.set_title("Open-Plan Spatial Decay of Speech (ISO 3382-3)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Distance from the talker r [m]")
    ax.set_ylabel("A-weighted SPL [dB]", color=COLOR_PRIMARY)
    ax.set_xlim(1.7, 18.0)
    ax.set_ylim(30, 62)
    from matplotlib.ticker import NullFormatter, ScalarFormatter
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([2, 3, 4, 6, 8, 12, 16])
    ax.set_xticklabels(["2", "3", "4", "6", "8", "12", "16"])
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.4)

    # Right axis: STI vs distance with the distraction / privacy crossings.
    ax2 = ax.twinx()
    rr2 = np.linspace(1.7, 18.0, 100)
    line_sti, = ax2.plot(rr2, c_sti + d_sti * rr2, color=COLOR_TERTIARY,
                         linewidth=1.7, label="STI vs distance")
    ax2.plot(r, sti, "s", color=COLOR_TERTIARY, markersize=5,
             markerfacecolor="white", markeredgewidth=1.3)
    for dist, level, name in [(m.rd, 0.50, "rD"), (m.rp, 0.20, "rP")]:
        ax2.axhline(level, color=COLOR_FG, linestyle=":", alpha=0.25, linewidth=1)
        ax2.plot(dist, level, "v", color=COLOR_SECONDARY, markersize=9, zorder=6)
        ax2.annotate(f"{name} = {dist:.1f} m", xy=(dist, level),
                     xytext=(dist * 0.62, level + 0.03), fontsize=9,
                     color=COLOR_SECONDARY,
                     arrowprops={"arrowstyle": "->", "lw": 0.9,
                                 "color": COLOR_SECONDARY})
    ax2.set_ylabel("STI", color=COLOR_TERTIARY)
    ax2.set_ylim(0.1, 0.75)

    handles = [pts_spl, line_spl, mark_4m, line_sti]
    ax.legend(handles, [str(h.get_label()) for h in handles],
              loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "open_plan_decay.png"))
    plt.close()


# ---------------------------------------------------------------------------
# Advanced psychoacoustics (plan-17 block A): the ECMA-418-2 Sottek model
# (loudness, tonality, roughness) and the Moore-Glasberg ISO 532-2/-3 models.
# The heavy computations (ECMA loudness ~5 s/call, tonality ~8 s/call) are
# cached so they run once and are reused across the four themed/language
# passes rather than four times over.
# ---------------------------------------------------------------------------
_P_REF = 2e-5  # reference sound pressure [Pa]
_FS_PSY = 48000  # ECMA-418-2 / ISO 532 operate at 48 kHz


def _pure_tone(freq: float, spl_db: float, dur: float,
               fs: int = _FS_PSY) -> np.ndarray:
    """Calibrated sinusoid: sound pressure in pascals at *spl_db* dB SPL."""
    t = np.arange(int(round(dur * fs))) / fs
    amp = _P_REF * 10.0 ** (spl_db / 20.0) * np.sqrt(2.0)
    return np.asarray(amp * np.sin(2.0 * np.pi * freq * t))


@lru_cache(maxsize=None)
def _loudness_models_data() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Total loudness (sone) vs level for the three loudness models."""
    from phonometry import (
        loudness_ecma,
        loudness_moore_glasberg_from_spectrum,
        loudness_zwicker,
    )

    levels = np.arange(20.0, 81.0, 10.0)  # 20..80 dB SPL
    zw, mg, ec = [], [], []
    for spl in levels:
        x = _pure_tone(1000.0, float(spl), 1.0)
        zw.append(loudness_zwicker(x, _FS_PSY, stationary=True).loudness)
        mg.append(
            loudness_moore_glasberg_from_spectrum([(1000.0, float(spl))]).loudness
        )
        ec.append(loudness_ecma(x, _FS_PSY).loudness)
    return levels, np.array(zw), np.array(mg), np.array(ec)


def generate_loudness_models_comparison(output_dir: str) -> None:
    """Zwicker vs Moore-Glasberg vs Sottek loudness for a 1 kHz tone."""
    print("Generating loudness_models_comparison.png...")
    levels, zw, mg, ec = _loudness_models_data()

    _, ax = plt.subplots(figsize=(10, 6))
    ax.plot(levels, zw, "o-", color=COLOR_PRIMARY, linewidth=2.0, markersize=6,
            label=f"Zwicker (ISO 532-1), N = {zw[2]:.1f} sone")
    ax.plot(levels, mg, "s--", color=COLOR_TERTIARY, linewidth=1.8, markersize=6,
            label=f"Moore-Glasberg (ISO 532-2), N = {mg[2]:.1f} sone")
    ax.plot(levels, ec, "^-.", color=COLOR_SECONDARY, linewidth=1.8, markersize=6,
            label=f"Sottek (ECMA-418-2), N = {ec[2]:.1f} sone")

    # The three models are anchored to 1 sone at 1 kHz / 40 dB SPL.
    ax.axhline(1.0, color=COLOR_FG, linestyle=":", alpha=0.35, linewidth=1)
    ax.plot(40.0, 1.0, "o", color=COLOR_FG, markersize=9,
            markerfacecolor="none", markeredgewidth=1.6, zorder=5)
    ax.annotate("Anchor: 1 kHz / 40 dB = 1 sone",
                xy=(40.0, 1.0), xytext=(21.5, 6.5), fontsize=10,
                color=COLOR_FG,
                arrowprops={"arrowstyle": "->", "lw": 1.0, "color": COLOR_FG})
    ax.annotate("Models diverge at high levels",
                xy=(80.0, float(zw[-1])), xytext=(52.0, 13.5), fontsize=9,
                color=COLOR_FG, ha="center",
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_FG})

    ax.set_title("Loudness Models Compared (1 kHz tone)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Sound pressure level [dB SPL]")
    ax.set_ylabel("Total loudness N [sone]")
    ax.set_xlim(18, 82)
    ax.set_ylim(0, float(zw[-1]) * 1.08)
    ax.set_xticks([20, 30, 40, 50, 60, 70, 80])
    ax.legend(loc="upper left", fontsize=9)
    plt.savefig(themed_path(output_dir, "loudness_models_comparison.png"))
    plt.close()


@lru_cache(maxsize=None)
def _sottek_specific_data() -> tuple[np.ndarray, np.ndarray, float]:
    """ECMA-418-2 specific loudness N'(z) of a 1 kHz / 60 dB tone."""
    from phonometry import loudness_ecma

    el = loudness_ecma(_pure_tone(1000.0, 60.0, 1.0), _FS_PSY)
    return el.bark.copy(), el.specific_loudness.copy(), float(el.loudness)


def generate_sottek_specific_loudness(output_dir: str) -> None:
    """ECMA-418-2 (Sottek) specific loudness N'(z) over the Bark-rate scale."""
    print("Generating sottek_specific_loudness.png...")
    bark, spec, total = _sottek_specific_data()

    _, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(bark, spec, color=COLOR_PRIMARY, alpha=0.30)
    ax.plot(bark, spec, color=COLOR_PRIMARY, linewidth=1.8,
            label=f"1 kHz tone, 60 dB (N = {total:.1f} sone_HMS)")

    peak_i = int(np.argmax(spec))
    ax.annotate("Peak specific loudness",
                xy=(float(bark[peak_i]), float(spec[peak_i])),
                xytext=(float(bark[peak_i]) + 4.5, float(spec[peak_i]) * 0.92),
                fontsize=10, color=COLOR_FG,
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_FG})

    ax.set_title("Sottek Specific Loudness (ECMA-418-2)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Critical-band rate z [Bark]")
    ax.set_ylabel("Specific loudness N' [sone_HMS/Bark]")
    ax.set_xlim(0, float(bark[-1]))
    ax.set_ylim(0, float(spec.max()) * 1.25)
    ax.set_xticks([0, 4, 8, 12, 16, 20, 24])
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "sottek_specific_loudness.png"))
    plt.close()


@lru_cache(maxsize=None)
def _tonality_data() -> tuple[np.ndarray, np.ndarray, float, np.ndarray, np.ndarray, float]:
    """ECMA-418-2 tonality T(t) for a 1 kHz tone-in-noise vs pure noise."""
    from phonometry import tonality_ecma

    rng = np.random.default_rng(2026)
    dur = 2.0
    t = np.arange(int(dur * _FS_PSY)) / _FS_PSY
    noise = rng.standard_normal(t.size)
    noise = noise / np.sqrt(np.mean(noise ** 2)) * _P_REF * 10.0 ** (50.0 / 20.0)
    tone = _P_REF * 10.0 ** (50.0 / 20.0) * np.sqrt(2.0) * np.sin(2.0 * np.pi * 1000.0 * t)

    tin = tonality_ecma(tone + noise, _FS_PSY)
    pn = tonality_ecma(noise, _FS_PSY)
    return (tin.time.copy(), tin.tonality_vs_time.copy(), float(tin.tonality),
            pn.time.copy(), pn.tonality_vs_time.copy(), float(pn.tonality))


@lru_cache(maxsize=None)
def _roughness_sweep_data() -> tuple[np.ndarray, np.ndarray]:
    """ECMA-418-2 roughness R vs AM frequency, 1 kHz carrier, 100 % AM, 60 dB."""
    from phonometry import roughness_ecma

    dur = 1.0
    t = np.arange(int(dur * _FS_PSY)) / _FS_PSY
    fmods = np.array([20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0,
                      100.0, 120.0, 150.0, 180.0, 200.0])
    r = []
    for fm in fmods:
        am = (1.0 + 1.0 * np.sin(2.0 * np.pi * fm * t)) * np.sin(2.0 * np.pi * 1000.0 * t)
        am = am / np.sqrt(np.mean(am ** 2)) * _P_REF * 10.0 ** (60.0 / 20.0)
        r.append(roughness_ecma(am, _FS_PSY).roughness)
    return fmods, np.array(r)


def generate_tonality_roughness_demo(output_dir: str) -> None:
    """Two-panel ECMA-418-2 sound-quality demo: tonality T(t) and roughness."""
    print("Generating tonality_roughness_demo.png...")
    (t_tin, tv_tin, t_single, _t_pn, tv_pn, pn_single) = _tonality_data()
    fmods, r = _roughness_sweep_data()

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 8.5))

    # -- Top: time-dependent tonality, tone-in-noise vs pure noise -----------
    ax0.plot(t_tin, tv_tin, color=COLOR_PRIMARY, linewidth=1.8,
             label=f"Tone in noise (T = {t_single:.2f} tu_HMS)")
    ax0.plot(_t_pn, tv_pn, color=COLOR_SECONDARY, linewidth=1.8,
             label=f"Pure noise (T = {pn_single:.2f} tu_HMS)")
    ax0.set_title("ECMA-418-2 Tonality T(t)", fontweight="bold", pad=10)
    ax0.set_xlabel("Time [s]")
    ax0.set_ylabel("Tonality T [tu_HMS]")
    ax0.set_xlim(0, float(t_tin[-1]))
    ax0.set_ylim(0, max(1.0, float(tv_tin.max()) * 1.30))
    ax0.legend(loc="upper right", fontsize=9)

    # -- Bottom: roughness vs modulation frequency (peak near 70 Hz) ---------
    ax1.plot(fmods, r, "o-", color=COLOR_TERTIARY, linewidth=2.0, markersize=6,
             label="1 kHz carrier, 100 % AM")
    peak_i = int(np.argmax(r))
    ax1.plot(fmods[peak_i], r[peak_i], "o", color=COLOR_SECONDARY, markersize=9,
             markerfacecolor="none", markeredgewidth=1.6, zorder=5)
    ax1.annotate(f"Peak R = {r[peak_i]:.1f} asper @ {fmods[peak_i]:.0f} Hz",
                 xy=(float(fmods[peak_i]), float(r[peak_i])),
                 xytext=(105.0, float(r[peak_i]) * 0.95), fontsize=10,
                 color=COLOR_FG,
                 arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_FG})
    ax1.set_title("ECMA-418-2 Roughness vs Modulation Frequency",
                  fontweight="bold", pad=10)
    ax1.set_xlabel("Modulation frequency f_mod [Hz]")
    ax1.set_ylabel("Roughness R [asper]")
    ax1.set_xlim(10, 210)
    ax1.set_ylim(0, float(r.max()) * 1.25)
    ax1.legend(loc="upper right", fontsize=9)

    fig.suptitle("Sound Quality Metrics (ECMA-418-2 Sottek Hearing Model)",
                 fontweight="bold", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    plt.savefig(themed_path(output_dir, "tonality_roughness_demo.png"))
    plt.close()


@lru_cache(maxsize=None)
def _time_loudness_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ISO 532-3 STL(t)/LTL(t) for a 1 kHz / 60 dB burst (on 200-400 ms)."""
    from phonometry import loudness_moore_glasberg_time

    dur = 0.8
    t = np.arange(int(dur * _FS_PSY)) / _FS_PSY
    sig = np.zeros_like(t)
    on = (t >= 0.2) & (t < 0.4)
    sig[on] = _P_REF * 10.0 ** (60.0 / 20.0) * np.sqrt(2.0) * np.sin(
        2.0 * np.pi * 1000.0 * t[on]
    )
    tv = loudness_moore_glasberg_time(sig, _FS_PSY)
    return (tv.time.copy(), tv.short_term_loudness.copy(),
            tv.long_term_loudness.copy())


def generate_moore_glasberg_time_loudness(output_dir: str) -> None:
    """ISO 532-3 short-term vs long-term loudness for a 1 kHz tone burst."""
    print("Generating moore_glasberg_time_loudness.png...")
    time, stl, ltl = _time_loudness_data()

    _, ax = plt.subplots(figsize=(10, 6))
    # Shade the burst window (200-400 ms).
    ax.axvspan(0.2, 0.4, color=COLOR_FG, alpha=0.07, linewidth=0)
    ax.plot(time, stl, color=COLOR_PRIMARY, linewidth=1.8,
            label=f"Short-term loudness STL (STL peak = {stl.max():.1f} sone)")
    ax.plot(time, ltl, color=COLOR_SECONDARY, linewidth=2.0,
            label=f"Long-term loudness LTL (LTL peak = {ltl.max():.1f} sone)")

    ax.annotate("1 kHz burst, 200 ms", xy=(0.3, 0.0),
                xytext=(0.3, float(stl.max()) * 1.02), fontsize=10,
                color=COLOR_FG, ha="center")
    ax.annotate("Fast attack / release",
                xy=(float(time[int(np.argmax(stl))]), float(stl.max())),
                xytext=(0.45, float(stl.max()) * 0.82), fontsize=9,
                color=COLOR_PRIMARY,
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_PRIMARY})
    ax.annotate("Slow integration",
                xy=(0.55, float(np.interp(0.55, time, ltl))),
                xytext=(0.58, float(ltl.max()) * 0.55), fontsize=9,
                color=COLOR_SECONDARY,
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_SECONDARY})

    ax.set_title("Time-Varying Loudness (ISO 532-3)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Loudness [sone]")
    ax.set_xlim(0, float(time[-1]))
    ax.set_ylim(0, float(stl.max()) * 1.18)
    ax.legend(loc="upper right", fontsize=9)
    plt.savefig(themed_path(output_dir, "moore_glasberg_time_loudness.png"))
    plt.close()


def generate_prediction_flanking_demo(output_dir: str) -> None:
    """EN 12354-1 simplified flanking prediction (Annex H.3 worked example)."""
    print("Generating prediction_flanking_demo.png...")
    from phonometry.building_prediction import (
        FlankingPath,
        flanking_element,
        predicted_airborne_insulation,
    )

    # Annex H.3 inputs: separating wall Rs,w = 57 dB, Ss = 11.5 m², four
    # flanking elements. Columns: (label, Rw, KFf, KFd=KDf, coupling length lf).
    elements = [
        ("floor", 49, 12.4, 8.9, 4.50),
        ("ceiling", 46, 14.4, 9.2, 4.50),
        ("facade", 42, 12.6, 6.7, 2.55),
        ("wall", 33, 33.5, 15.7, 2.55),
    ]
    paths: list[FlankingPath] = []
    for name, rw, k_ff, k_side, lf in elements:
        ff, df, fd = flanking_element(
            label=name, r_flanking=float(rw), r_separating=57.0,
            k_ff=k_ff, k_fd=k_side, k_df=k_side,
            separating_area=11.5, coupling_length=lf,
        )
        paths.extend((ff, df, fd))
    result = predicted_airborne_insulation(r_direct=57.0, flanking_paths=paths)

    # Sort every path (direct + 12 flanking) by its share of the transmitted
    # energy, largest first.
    contribs = sorted(result.paths, key=lambda c: c.fraction, reverse=True)
    labels = [c.label for c in contribs]
    fracs = [c.fraction * 100.0 for c in contribs]
    df_orange = "#ff7f0e"
    kind_color = {
        "Dd": COLOR_TERTIARY, "Ff": COLOR_PRIMARY,
        "Fd": COLOR_SECONDARY, "Df": df_orange,
    }
    colors = [kind_color[c.kind] for c in contribs]

    direct_share = next(c.fraction for c in result.paths if c.kind == "Dd") * 100.0
    flank_share = 100.0 - direct_share

    fig, ax = plt.subplots(figsize=(11, 6.4))
    bars = ax.bar(range(len(fracs)), fracs, color=colors, edgecolor=COLOR_FG,
                  linewidth=0.7, zorder=3)
    bars[0].set_linewidth(2.2)  # highlight the dominant path
    ax.annotate("dominant path", xy=(0, fracs[0]), xytext=(1.5, fracs[0] + 3.5),
                fontsize=10, fontweight="bold", color=COLOR_FG,
                arrowprops={"arrowstyle": "->", "lw": 1.1})

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("Share of transmitted energy [%]")
    ax.set_xlabel("Transmission path")
    ax.set_ylim(0, max(fracs) + 9.0)
    ax.set_title("EN 12354-1 Flanking Transmission (Annex H.3 example)",
                 fontweight="bold", pad=12)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=COLOR_TERTIARY, edgecolor=COLOR_FG, label="Dd — direct"),
        Patch(facecolor=COLOR_PRIMARY, edgecolor=COLOR_FG,
              label="Ff — flanking–flanking"),
        Patch(facecolor=COLOR_SECONDARY, edgecolor=COLOR_FG,
              label="Fd — flanking–separating"),
        Patch(facecolor=df_orange, edgecolor=COLOR_FG,
              label="Df — separating–flanking"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=9)

    rw_dd = result.r_direct_w
    rpw = result.r_prime_w
    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    lines = [
        f"Rw (Dd) = {rw_dd:.1f} dB",
        f"R'w = {rpw:.1f} dB",
        f"R'w − Rw = {rpw - rw_dd:.1f} dB",
        f"Dd {direct_share:.1f} %   ΣFf,Fd,Df {flank_share:.1f} %",
    ]
    ax.text(0.985, 0.62, "\n".join(lines), transform=ax.transAxes,
            va="top", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "prediction_flanking_demo.png"))
    plt.close()


def generate_insulation_uncertainty_demo(output_dir: str) -> None:
    """ISO 12999-1 per-band + single-number measurement uncertainty (situation B)."""
    print("Generating insulation_uncertainty_demo.png...")
    from phonometry.building_uncertainty import (
        band_uncertainty,
        insulation_coverage_factor,
        insulation_expanded_uncertainty,
        single_number_uncertainty,
    )
    from phonometry.insulation import weighted_rating

    # Reuse the ISO 717-1 Annex C measured R' curve (100 Hz .. 3150 Hz); its
    # weighted rating is R'w = 30 dB.
    freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
                      1000, 1250, 1600, 2000, 2500, 3150], dtype=float)
    measured = np.array([20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
                         28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5])
    rating = weighted_rating(measured).rating

    # Per-band standard uncertainty u (ISO 12999-1 Table 2, situation B); match
    # each measured band to its tabulated value, then expand at k = 1.96 (95 %).
    band = band_uncertainty("airborne", "B")
    band_f, band_u = band.to_arrays()
    idx = [int(np.argmin(np.abs(band_f - f))) for f in freqs]
    u_band = band_u[idx]
    k = insulation_coverage_factor(0.95)
    exp_band = np.array(
        [insulation_expanded_uncertainty(float(v), 0.95) for v in u_band]
    )

    # Single-number expanded uncertainty for the rating.
    u_single = single_number_uncertainty("r_w", "B")
    exp_single = insulation_expanded_uncertainty(u_single, 0.95)

    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.fill_between(freqs, measured - exp_band, measured + exp_band,
                    color=COLOR_PRIMARY, alpha=0.14, zorder=1,
                    label="Expanded uncertainty ±U (95 %)")
    ax.fill_between(freqs, measured - u_band, measured + u_band,
                    color=COLOR_PRIMARY, alpha=0.30, zorder=2,
                    label="Standard uncertainty ±u")
    ax.semilogx(freqs, measured, marker="o", color=COLOR_PRIMARY, linewidth=1.9,
                markersize=5, markerfacecolor="white", markeredgewidth=1.4,
                zorder=4, label="Measured R'")

    # Single-number R'w with its expanded uncertainty, read at 500 Hz.
    ax.errorbar(500, rating, yerr=exp_single, fmt="D", color=COLOR_SECONDARY,
                markersize=9, capsize=6, elinewidth=1.8, zorder=6,
                label="R'w ± U (single number)")
    ax.axvline(500, color=COLOR_FG, linestyle=":", alpha=0.35, zorder=0)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    # Word-free box (the situation and band meanings are in the title/legend, so
    # translation reduces to the automatic decimal-comma substitution).
    box = [
        f"R'w = {rating} ± {exp_single:.1f} dB",
        f"U = k·u ,  k = {k:g} (95 %)",
    ]
    ax.text(0.03, 0.97, "\n".join(box), transform=ax.transAxes, va="top",
            ha="left", fontsize=10, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})

    ax.set_title("ISO 12999-1 Measurement Uncertainty (situation B, airborne)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Apparent sound reduction index R' [dB]")
    ax.set_xscale("log")
    ax.set_xlim(90, 3600)
    ax.set_ylim(8, 42)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(freqs)
    ax.set_xticklabels(
        ["100", "125", "160", "200", "250", "315", "400", "500", "630", "800",
         "1k", "1.25k", "1.6k", "2k", "2.5k", "3.15k"], fontsize=8)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.legend(loc="lower right", fontsize=9)
    plt.savefig(themed_path(output_dir, "insulation_uncertainty_demo.png"))
    plt.close()


def generate_air_absorption_alpha(output_dir: str) -> None:
    """ISO 9613-1 pure-tone atmospheric attenuation coefficient alpha(f)."""
    print("Generating air_absorption_alpha.png...")
    from phonometry import air_attenuation

    freqs = np.logspace(np.log10(50.0), np.log10(10000.0), 400)
    # Four representative (temperature, relative humidity) conditions spanning
    # the relaxation behaviour: the reference, a dry warm day, a cold humid day
    # and a hot humid day. alpha is returned in dB/m; plot in dB/km (Table 1).
    conditions = [
        (20.0, 50.0, COLOR_PRIMARY),
        (20.0, 10.0, COLOR_SECONDARY),
        (0.0, 70.0, COLOR_TERTIARY),
        (30.0, 80.0, "#ff7f0e"),
    ]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    for temp, rh, color in conditions:
        alpha_km = air_attenuation(freqs, temp, rh) * 1000.0
        ax.loglog(freqs, alpha_km, color=color, linewidth=2.0,
                  label=f"{temp:g} °C, {rh:g} % RH")
    ax.set_title("ISO 9613-1 Atmospheric Absorption α(f)", fontweight="bold",
                 pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Attenuation coefficient α [dB/km]")
    ax.set_xlim(50.0, 10000.0)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", fontsize=10)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "air_absorption_alpha.png"))
    plt.close()


def generate_outdoor_attenuation_breakdown(output_dir: str) -> None:
    """ISO 9613-2 per-term octave-band attenuation breakdown, with a barrier."""
    print("Generating outdoor_attenuation_breakdown.png...")
    from phonometry import Barrier, outdoor_propagation_attenuation

    bands = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
    # A point source 200 m away over porous ground (G = 1), screened by a 4 m
    # barrier midway (source and receiver 1,5 m high; the diffraction geometry
    # gives dss = dsr ~ 100 m over the raised edge).
    barrier = Barrier(source_to_edge=101.0, edge_to_receiver=101.0)
    att = outdoor_propagation_attenuation(
        200.0, 1.5, 1.5, bands, ground_source=1.0, ground_middle=1.0,
        ground_receiver=1.0, barrier=barrier, temperature=15.0, relative_humidity=70.0,
    )
    x = np.arange(len(bands))
    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.bar(x, att.a_div, color=COLOR_PRIMARY, edgecolor=COLOR_FG, linewidth=0.6,
           label="Adiv — divergence", zorder=3)
    ax.bar(x, att.a_atm, bottom=att.a_div, color=COLOR_TERTIARY,
           edgecolor=COLOR_FG, linewidth=0.6, label="Aatm — atmospheric",
           zorder=3)
    base = att.a_div + att.a_atm
    ax.bar(x, att.a_gr, bottom=base, color="#9467bd", edgecolor=COLOR_FG,
           linewidth=0.6, label="Agr — ground", zorder=3)
    base = base + att.a_gr
    ax.bar(x, att.a_bar, bottom=base, color="#ff7f0e", edgecolor=COLOR_FG,
           linewidth=0.6, label="Abar — barrier", zorder=3)
    ax.plot(x, att.a_total, marker="D", color=COLOR_SECONDARY, linewidth=2.0,
            markersize=6, markerfacecolor="white", markeredgewidth=1.4,
            zorder=5, label="A — total")

    ax.set_title("ISO 9613-2 Attenuation Breakdown (with a 4 m barrier)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Octave-band centre frequency [Hz]")
    ax.set_ylabel("Attenuation A [dB]")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{b:g}" for b in bands])
    ax.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.6)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9, ncol=2)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "outdoor_attenuation_breakdown.png"))
    plt.close()


def generate_exposure_uncertainty(output_dir: str) -> None:
    """ISO 9612 Annex D task-based exposure with its expanded uncertainty."""
    print("Generating exposure_uncertainty.png...")
    from phonometry.occupational_exposure import Task, task_based_exposure

    tasks = [
        Task(samples=(70.0,), duration_hours=1.5, label="planning/breaks"),
        Task(samples=(80.1, 82.2, 79.6), duration_hours=5.0,
             duration_range=(4.0, 6.0), label="welding"),
        Task(samples=(86.5, 92.4, 89.3, 93.2, 87.8, 86.2), duration_hours=1.5,
             duration_range=(1.0, 2.0), label="cutting/grinding"),
    ]
    result = task_based_exposure(tasks, include_duration_uncertainty=False,
                                 warn=False)
    labels = [t.label for t in result.tasks]
    contribs = [t.lex_8h_contribution for t in result.tasks]
    lex = result.lex_8h
    upper = result.upper_limit  # LEX,8h + U

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.bar(x, contribs, color=COLOR_PRIMARY, edgecolor=COLOR_FG, linewidth=0.7,
           width=0.6, zorder=3, label="Measurement task")
    for xi, c in zip(x, contribs):
        ax.text(float(xi), c - 2.5, f"{c:.1f}", ha="center", va="top",
                fontsize=9, color="white", fontweight="bold")

    # Daily energy-summed level and its one-sided 95 % upper limit LEX,8h + U.
    ax.axhspan(lex, upper, color=COLOR_SECONDARY, alpha=0.14, zorder=0,
               label="LEX,8h + U (one-sided 95 %)")
    ax.axhline(lex, color=COLOR_SECONDARY, linewidth=2.0, zorder=4,
               label="Daily LEX,8h")
    ax.axhline(upper, color=COLOR_SECONDARY, linewidth=1.2, linestyle="--",
               zorder=4)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    box = [
        f"LEX,8h = {lex:.1f} dB",
        f"U = {result.expanded_uncertainty:.1f} dB (k = 1.65)",
        f"LEX,8h + U = {upper:.1f} dB",
    ]
    ax.text(0.03, 0.78, "\n".join(box), transform=ax.transAxes, va="top",
            ha="left", fontsize=10, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})

    ax.set_title("ISO 9612 Task-Based Exposure (Annex D)", fontweight="bold",
                 pad=12)
    ax.set_xlabel("Measurement task")
    ax.set_ylabel("LEX,8h contribution [dB]")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0.0, upper + 10.0)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "exposure_uncertainty.png"))
    plt.close()


def generate_absorption_rating(output_dir: str) -> None:
    """ISO 11654 alpha_w: practical curve, shifted reference, deviations (Annex A.2)."""
    print("Generating absorption_rating.png...")
    from phonometry import weighted_absorption

    # ISO 11654:1997 Annex A.2 worked example -> alpha_w = 0.60(M).
    alpha_p = [0.35, 1.00, 0.65, 0.60, 0.55]
    result = weighted_absorption(alpha_p)
    freqs = np.asarray(result.band_centers, dtype=float)
    measured = np.asarray(result.measured, dtype=float)
    shifted = np.asarray(result.shifted_reference, dtype=float)

    _, ax = plt.subplots(figsize=(10, 6.5))
    ax.fill_between(freqs, measured, shifted, where=(measured < shifted).tolist(),
                    interpolate=True, color=COLOR_SECONDARY, alpha=0.25,
                    zorder=1, label="Unfavourable deviations")
    ax.semilogx(freqs, shifted, marker="s", color=COLOR_FG, linewidth=1.6,
                linestyle="--", markersize=5, zorder=3,
                label="Shifted reference curve (ISO 11654)")
    ax.semilogx(freqs, measured, marker="o", color=COLOR_PRIMARY, linewidth=1.8,
                markersize=6, markerfacecolor="white", markeredgewidth=1.4,
                zorder=4, label="Practical absorption alpha_p")

    # alpha_w is the shifted reference read at 500 Hz.
    ax.axvline(500, color=COLOR_FG, linestyle=":", alpha=0.4)
    ax.plot(500, result.alpha_w, "D", color=COLOR_SECONDARY, markersize=9, zorder=6)
    ax.annotate(f"alpha_w = {result.rating_label}", xy=(500, result.alpha_w),
                xytext=(600, result.alpha_w - 0.16), fontsize=12, fontweight="bold",
                arrowprops={"arrowstyle": "->", "lw": 1.0})

    # Placed low-left, clear of the practical curve that peaks top-centre.
    for dy, text in (
        (0.30, f"Reference curve shifted by {result.shift:.2f}"),
        (0.23, f"Sum of unfavourable deviations = {result.unfavourable_sum:.2f}"
               f"  (limit 0.10)"),
        (0.16, f"Absorption class {result.absorption_class}  "
               f"(shape indicator: {result.shape_indicator or 'none'})"),
    ):
        ax.text(0.03, dy, text, transform=ax.transAxes, va="top", ha="left",
                fontsize=9.5, color=COLOR_FG)

    ax.set_title("ISO 11654 Weighted Sound Absorption Coefficient (Annex A.2 example)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound absorption coefficient")
    ax.set_xscale("log")
    ax.set_xlim(220, 4600)
    ax.set_ylim(0.0, 1.08)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks(freqs)
    ax.set_xticklabels(["250", "500", "1k", "2k", "4k"], fontsize=9)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.legend(loc="lower right", fontsize=9)
    plt.savefig(themed_path(output_dir, "absorption_rating.png"))
    plt.close()


def generate_airflow_resistance(output_dir: str) -> None:
    """ISO 9053-1 static method: dp vs u, through-origin quadratic fit, R_s at 0.5 mm/s."""
    print("Generating airflow_resistance.png...")
    from phonometry import static_airflow_resistance

    # A porous specimen (area 100 mm dia, 50 mm thick) measured stepwise. The
    # pressure drop is slightly super-linear in velocity; the through-origin
    # quadratic fit dp = a*u + b*u**2 recovers R_s = a at the reference 0.5 mm/s.
    area = float(np.pi) * (0.05 ** 2)  # 100 mm diameter cell
    r_s_true, curvature = 1.6e4, 4.0e5  # Pa*s/m, Pa*s2/m2
    u = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 12.0]) * 1e-3  # m/s
    dp = r_s_true * u + curvature * u**2
    result = static_airflow_resistance(u, dp, area=area, thickness=0.05)

    u_fit = np.linspace(0.0, 13e-3, 200)
    dp_fit = result.linear_coefficient * u_fit + result.quadratic_coefficient * u_fit**2

    _, ax = plt.subplots(figsize=(10, 6.5))
    ax.plot(u_fit * 1e3, dp_fit, color=COLOR_PRIMARY, linewidth=1.8, zorder=2,
            label="Through-origin quadratic fit  dp = a u + b u^2")
    ax.plot(u * 1e3, dp, "o", color=COLOR_SECONDARY, markersize=7,
            markerfacecolor="white", markeredgewidth=1.6, zorder=4,
            label="Measured pressure drop")

    u_ref = result.evaluation_velocity
    ax.axvline(u_ref * 1e3, color=COLOR_FG, linestyle=":", alpha=0.4)
    ax.plot(u_ref * 1e3, result.pressure_drop, "D", color=COLOR_TERTIARY,
            markersize=9, zorder=6)
    ax.annotate("evaluation at 0.5 mm/s", xy=(u_ref * 1e3, result.pressure_drop),
                xytext=(2.0, result.pressure_drop + 40), fontsize=10,
                arrowprops={"arrowstyle": "->", "lw": 1.0})

    for dy, text in (
        (0.97, f"Specific airflow resistance R_s = {result.specific_resistance:.0f}"
               f" Pa s/m"),
        (0.90, f"Airflow resistivity sigma = {result.resistivity:.0f} Pa s/m^2"),
        (0.83, f"Linear term a = {result.linear_coefficient:.0f} Pa s/m"
               f"  (= R_s at u -> 0)"),
    ):
        ax.text(0.03, dy, text, transform=ax.transAxes, va="top", ha="left",
                fontsize=9.5, color=COLOR_FG)

    ax.set_title("ISO 9053-1 Static-Method Airflow Resistance", fontweight="bold",
                 pad=12)
    ax.set_xlabel("Linear airflow velocity u [mm/s]")
    ax.set_ylabel("Pressure drop dp [Pa]")
    ax.set_xlim(0.0, 13.0)
    ax.set_ylim(bottom=0.0)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.legend(loc="lower right", fontsize=9)
    plt.savefig(themed_path(output_dir, "airflow_resistance.png"))
    plt.close()


def generate_impedance_tube(output_dir: str) -> None:
    """ISO 10534-1 standing-wave-ratio method: alpha and |r| vs level difference."""
    print("Generating impedance_tube.png...")
    from phonometry import (
        standing_wave_absorption,
        standing_wave_reflection_magnitude,
        standing_wave_ratio_from_level,
    )

    # Level difference between pressure maximum and minimum (Eq. 15): a large dL
    # means a strong reflection (little absorption); dL -> 0 is a perfect absorber.
    level_diff = np.linspace(0.5, 40.0, 300)
    swr = np.array([standing_wave_ratio_from_level(dl) for dl in level_diff])
    alpha = np.array([standing_wave_absorption(s) for s in swr])
    r_mag = np.array([standing_wave_reflection_magnitude(s) for s in swr])

    _, ax = plt.subplots(figsize=(10, 6.5))
    ax.plot(level_diff, alpha, color=COLOR_PRIMARY, linewidth=2.0, zorder=3,
            label="Absorption coefficient alpha = 1 - |r|^2")
    ax.set_xlabel("Standing-wave level difference L_max - L_min [dB]")
    ax.set_ylabel("Sound absorption coefficient alpha")
    ax.set_ylim(0.0, 1.02)
    ax.set_xlim(0.0, 40.0)

    ax_r = ax.twinx()
    ax_r.plot(level_diff, r_mag, color=COLOR_SECONDARY, linewidth=1.8,
              linestyle="--", zorder=2, label="Reflection factor magnitude |r|")
    ax_r.set_ylabel("Reflection factor magnitude |r|")
    ax_r.set_ylim(0.0, 1.02)

    # Mark the didactic anchor: dL = 9.54 dB -> s = 3 -> |r| = 0.5 -> alpha = 0.75.
    dl_anchor = 20.0 * float(np.log10(3.0))
    ax.plot(dl_anchor, 0.75, "D", color=COLOR_TERTIARY, markersize=9, zorder=6)
    # Text sits in the lens that opens between the diverging alpha and |r| curves.
    ax.annotate("s = 3 -> |r| = 0.5 -> alpha = 0.75",
                xy=(dl_anchor, 0.75), xytext=(15.0, 0.44),
                fontsize=10, arrowprops={"arrowstyle": "->", "lw": 1.0})

    ax.set_title("ISO 10534-1 Standing-Wave-Ratio Method", fontweight="bold", pad=12)
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax_r.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=9)
    plt.savefig(themed_path(output_dir, "impedance_tube.png"))
    plt.close()


def generate_scattering_coefficient(output_dir: str) -> None:
    """ISO 17497-1: scattering coefficient s(f) from a per-band measurement."""
    print("Generating scattering_coefficient.png...")
    from phonometry import scattering_coefficient_spectrum

    # A realistic reverberation-room measurement reduced to two absorption
    # spectra over the 13 one-third-octave bands 250-4000 Hz: the random-
    # incidence absorption alpha_s (stationary sample) and the specular
    # absorption alpha_spec (rotating turntable). A diffuser scatters more with
    # frequency, so alpha_spec climbs above alpha_s and s(f) = (alpha_spec -
    # alpha_s)/(1 - alpha_s) rises smoothly from near 0 towards 0.8.
    freqs = np.array(
        [250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000],
        dtype=float,
    )
    alpha_s = np.full_like(freqs, 0.10)
    alpha_spec = 0.11 + 0.75 * (np.log10(freqs / 250.0) / np.log10(4000.0 / 250.0))
    result = scattering_coefficient_spectrum(freqs, alpha_spec, alpha_s)

    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.semilogx(result.frequencies, result.scattering, color=COLOR_PRIMARY,
                linewidth=1.9, marker="o", markersize=6, markerfacecolor="white",
                markeredgewidth=1.4, zorder=3)
    ax.set_title("Random-incidence scattering coefficient (ISO 17497-1)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Scattering coefficient s")
    ax.set_xlim(freqs.min() * 0.9, freqs.max() * 1.1)
    ax.set_ylim(0.0, 1.0)
    from matplotlib.ticker import NullFormatter, ScalarFormatter
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([250, 500, 1000, 2000, 4000])
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "scattering_coefficient.png"))
    plt.close()


def generate_diffusion_polar(output_dir: str) -> None:
    """ISO 17497-2: polar reflected response and its diffusion coefficient d."""
    print("Generating diffusion_polar.png...")
    from phonometry import directional_diffusion

    # Reflected sound-pressure levels L_i(theta) on a 37-point semicircle
    # (-90 to 90 deg, 5 deg spacing) of a diffusing surface: the energy is
    # spread almost uniformly over angle, so the ISO 17497-2 Formula (5)
    # autocorrelation coefficient d is high.
    angles = np.arange(-90.0, 90.5, 5.0)
    rng = np.random.default_rng(3)
    levels = 70.0 + 2.0 * np.sin(np.radians(angles) * 3.0) + rng.normal(
        0.0, 1.0, angles.size
    )
    result = directional_diffusion(angles, levels)

    fig, ax = plt.subplots(figsize=(8.0, 7.5),
                           subplot_kw={"projection": "polar"})
    # The theta-* setters live on PolarAxes, not the base Axes type.
    polar: Any = ax
    theta = np.radians(result.angles)
    polar.plot(theta, result.levels, color=COLOR_PRIMARY, linewidth=1.9,
               marker="o", markersize=4, zorder=3)
    polar.fill(theta, result.levels, color=COLOR_PRIMARY, alpha=0.15, zorder=1)
    polar.set_theta_zero_location("N")
    polar.set_theta_direction(-1)
    polar.set_thetamin(-90)
    polar.set_thetamax(90)
    polar.set_title(
        f"Directional diffusion  d = {result.coefficient:.2f}  (ISO 17497-2)",
        fontweight="bold", pad=20,
    )
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "diffusion_polar.png"))
    plt.close()


def generate_insitu_absorption(output_dir: str) -> None:
    """ISO 13472-1: in-situ one-third-octave absorption spectrum alpha(f)."""
    print("Generating insitu_absorption.png...")
    from phonometry import geometric_spreading_factor, insitu_absorption_spectrum

    # A synthetic-but-realistic in-situ measurement. The incident impulse hi is
    # a unit spike; the road reflection is hr = Kr * r0 * roll(hi, shift) with
    # Kr the geometrical-spreading factor (2/3 for ds=1.25 m, dm=0.25 m), a
    # mildly frequency-dependent r0 realised by a gentle low-pass (a porous
    # surface reflects less as frequency rises), and the reflected-path delay
    # shift = round(2 dm / c * fs). The library forms the narrow-band
    # alpha = 1 - (1/Kr^2)|Hr/Hi|^2 and reduces it to one-third-octave bands.
    fs, n = 48000.0, 8192
    kr = geometric_spreading_factor()  # (ds - dm)/(ds + dm) = 2/3
    hi = np.zeros(n)
    hi[0] = 1.0
    r0 = 0.85
    taps = scipy_signal.firwin(41, 1200.0, fs=fs)
    taps = taps / taps.sum()
    shift = int(round(2.0 * 0.25 / 340.0 * fs))  # reflected-path delay 2 dm / c
    hr = kr * r0 * np.roll(scipy_signal.lfilter(taps, 1.0, hi), shift)
    result = insitu_absorption_spectrum(hi, hr, fs)

    freqs = result.frequencies
    positions = np.arange(freqs.size, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.bar(positions, np.nan_to_num(result.absorption), width=0.7,
           color=COLOR_PRIMARY, edgecolor=COLOR_FG, linewidth=0.7, zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title("In-situ road-surface absorption (ISO 13472-1)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Absorption coefficient alpha")
    ax.set_ylim(0.0, 1.0)
    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    ax.text(0.04, 0.94, "Kr = 2/3\nalpha = 1 - (1/Kr^2)|Hr/Hi|^2",
            transform=ax.transAxes, va="top", ha="left", fontsize=10,
            color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "insitu_absorption.png"))
    plt.close()


def generate_precision_anechoic_power(output_dir: str) -> None:
    """ISO 3745: precision LW spectrum from a hemisphere pressure measurement."""
    print("Generating precision_anechoic_power.png...")
    from phonometry import sound_power_anechoic

    # A mid-frequency-peaked machine measured over the 40-position hemisphere
    # array (ISO 3745 Annex E) in a hemi-anechoic room. levels_positions is the
    # (40, NB) surface pressure spectrum: a base machine spectrum peaked near
    # 1 kHz plus a small per-position spatial variation. The library forms the
    # surface-averaged LW = Lp_bar + 10 lg(S/S0) + C1+C2+C3 and the A-weighted
    # total LWA.
    freqs = np.array([125, 250, 500, 1000, 2000, 4000, 8000], dtype=float)
    base = 70.0 + 8.0 * np.exp(-(np.log2(freqs / 1000.0) ** 2) / 2.0)
    rng = np.random.default_rng(7)
    levels = base[None, :] + rng.normal(0.0, 1.0, (40, freqs.size))
    result = sound_power_anechoic(levels, "hemisphere", radius=1.0,
                                  frequencies=freqs)

    lw = result.sound_power_level
    lwa = result.sound_power_level_a
    positions = np.arange(freqs.size, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.bar(positions, lw, width=0.7, color=COLOR_PRIMARY, edgecolor=COLOR_FG,
           linewidth=0.7, zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(f"Precision sound power (ISO 3745)  LWA = {lwa:.1f} dB(A)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound power level LW [dB]")
    ax.set_ylim(0.0, float(np.nanmax(lw)) + 8.0)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "precision_anechoic_power.png"))
    plt.close()


def generate_intensity_scan_power(output_dir: str) -> None:
    """ISO 9614-3: precision LW spectrum by intensity scanning (with a NaN band)."""
    print("Generating intensity_scan_power.png...")
    import warnings

    from phonometry import sound_power_intensity_precision

    # Four partial surfaces scanned over five one-third-octave bands. Each cell
    # of partial_intensity is the signed normal intensity In_i (W/m^2) already
    # reduced to the two-scan result; areas are the partial-surface areas Si.
    # The 250 Hz band has net-negative power (more energy flowing in than out),
    # so ISO 9614-3 flags it not-applicable (clause 9.2) and it is hatched.
    freqs = np.array([250, 500, 1000, 2000, 4000], dtype=float)
    areas = np.array([0.5, 1.0, 0.75, 0.5])
    base_intensity = np.array([2.0e-6, 8.0e-6, 2.0e-5, 1.0e-5, 3.0e-6])
    per_segment = np.array([1.0, 1.1, 0.9, 1.05])
    partial_intensity = base_intensity[None, :] * per_segment[:, None]
    # A locally reactive 250 Hz band: the segment intensities cancel to a
    # net-negative total.
    partial_intensity[:, 0] = np.array([2.0e-6, -3.0e-6, -4.0e-6, -1.0e-6])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = sound_power_intensity_precision(partial_intensity, areas,
                                                 frequencies=freqs)

    lw = result.sound_power_level
    neg = result.not_applicable_band
    lwa = result.sound_power_level_a
    positions = np.arange(freqs.size, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6.3))
    # Determinate bands: a solid LW bar. Non-applicable bands carry no LW (NaN),
    # so instead of a zero-height bar they are flagged by a full-height greyed,
    # hatched span - clearly a marker, not a plotted value (ISO 9614-3, 9.2).
    ax.bar(positions[~neg], np.nan_to_num(lw)[~neg], width=0.7, color=COLOR_PRIMARY,
           edgecolor=COLOR_FG, linewidth=0.7, zorder=3)
    for pos, is_neg in zip(positions, neg):
        if is_neg:
            ax.axvspan(pos - 0.35, pos + 0.35, facecolor="#888888", alpha=0.28,
                       hatch="//", edgecolor="#888888", linewidth=0.8, zorder=2)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(f"Precision intensity scanning (ISO 9614-3)  LWA = {lwa:.1f} dB(A)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound power level LW [dB]")
    ax.set_ylim(0.0, float(np.nanmax(lw)) + 8.0)
    from matplotlib.patches import Patch
    handle = Patch(facecolor="#888888", alpha=0.28, hatch="//",
                   edgecolor="#888888", label="Non-applicable band")
    ax.legend(handles=[handle], loc="upper right", fontsize=9)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "intensity_scan_power.png"))
    plt.close()


def generate_vibration_weighting(output_dir: str) -> None:
    """ISO 8041-1: the whole-body vertical weighting Wk over its band."""
    print("Generating vibration_weighting.png...")
    from phonometry import frequency_weighting

    # A user evaluates the principal ISO 2631-1 weighting Wk on a fine
    # frequency grid across the whole-body band (0,4-100 Hz). The result is the
    # ISO 8041-1 cascade H(f): a gentle +0,5 dB peak near 6 Hz, a band-limiting
    # roll-off below 0,4 Hz and above ~16 Hz.
    freqs = np.geomspace(0.4, 100.0, 240)
    result = frequency_weighting("Wk", freqs)

    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.semilogx(result.frequencies, result.magnitude_db, color=COLOR_PRIMARY,
                linewidth=1.9, zorder=3)
    ax.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.4, zorder=1)
    ax.set_title("Whole-body vertical weighting Wk (ISO 8041-1)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_xlim(0.4, 100.0)
    ax.set_ylim(-40.0, 5.0)
    from matplotlib.ticker import NullFormatter
    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50, 100])
    # Explicit string labels install a FixedFormatter so the Spanish pass can
    # apply the decimal comma (a log-axis ScalarFormatter would not be caught).
    ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50", "100"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "vibration_weighting.png"))
    plt.close()


def generate_weighted_acceleration(output_dir: str) -> None:
    """ISO 2631-1: measured seat spectrum weighted to a_w (Eq. (9))."""
    print("Generating weighted_acceleration.png...")
    from phonometry import weighted_acceleration

    # A measured vertical seat-pan acceleration spectrum (r.m.s. per one-third
    # octave, m/s^2) from a vehicle seat: energy concentrated in the 2-8 Hz
    # whole-body range. Weighting it with Wk gives the health-relevant a_w.
    freqs = np.array([1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0,
                      10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 63.0, 80.0])
    accel = np.array([0.18, 0.24, 0.33, 0.46, 0.52, 0.55, 0.48, 0.39, 0.31,
                      0.26, 0.21, 0.17, 0.13, 0.10, 0.078, 0.060, 0.045,
                      0.028, 0.020])
    result = weighted_acceleration(accel, freqs, "Wk")

    positions = np.arange(freqs.size, dtype=float)
    width = 0.4
    fig, ax = plt.subplots(figsize=(10.5, 6.3))
    ax.bar(positions - width / 2, result.band_accelerations, width,
           color="#9e9e9e", edgecolor=COLOR_FG, linewidth=0.5,
           label="Unweighted $a_i$", zorder=2)
    ax.bar(positions + width / 2, result.weighted, width, color=COLOR_PRIMARY,
           edgecolor=COLOR_FG, linewidth=0.5, label="Weighted $W_i\\,a_i$ (Wk)",
           zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(
        f"Weighted seat acceleration (ISO 2631-1)  $a_w$ = {result.overall:.3f} "
        "m/s$^2$", fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("r.m.s. acceleration [m/s$^2$]")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "weighted_acceleration.png"))
    plt.close()


def generate_daily_vibration_exposure(output_dir: str) -> None:
    """ISO 5349 + Directive 2002/44/EC: A(8) vs the EAV/ELV thresholds."""
    print("Generating daily_vibration_exposure.png...")
    from phonometry import daily_vibration_exposure

    # A forestry worker's day across three chain-saw tasks (the ISO 5349-2
    # Annex E.3 worked example): each task's a_hv and duration give a partial
    # exposure A_i(8); they combine to A(8) = 3,6 m/s^2, assessed against the
    # hand-arm action (2,5) and limit (5,0) values of Directive 2002/44/EC.
    result = daily_vibration_exposure(
        [4.6, 6.0, 3.6],
        [2 * 3600.0, 1 * 3600.0, 2 * 3600.0],
        kind="hav",
        labels=["brush-saw", "felling", "stripping"],
    )

    labels = [*result.labels, "A(8)"]
    values = [*result.partials.tolist(), result.a8]
    positions = np.arange(len(values), dtype=float)
    colors = ["#9e9e9e"] * result.partials.size + [COLOR_PRIMARY]
    fig, ax = plt.subplots(figsize=(9.5, 6.3))
    ax.bar(positions, values, width=0.62, color=colors, edgecolor=COLOR_FG,
           linewidth=0.6, zorder=3)
    eav = result.assessment.action_value
    elv = result.assessment.limit_value
    ax.axhline(eav, color=COLOR_TERTIARY, linestyle="--", linewidth=1.6,
               label=f"EAV = {eav:g} m/s$^2$", zorder=2)
    ax.axhline(elv, color=COLOR_SECONDARY, linestyle="--", linewidth=1.6,
               label=f"ELV = {elv:g} m/s$^2$", zorder=2)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Daily exposure A(8) [m/s$^2$]")
    ax.set_ylim(0.0, elv * 1.2)
    ax.set_title(
        f"Hand-arm daily exposure (ISO 5349 / 2002-44-EC)  A(8) = "
        f"{result.a8:.2f} m/s$^2$", fontweight="bold", pad=12)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "daily_vibration_exposure.png"))
    plt.close()


def generate_speech_intelligibility(output_dir: str) -> None:
    """ANSI S3.5-1997: band audibility and the SII in broadband noise."""
    print("Generating speech_intelligibility.png...")
    from phonometry import speech_intelligibility_index, standard_speech_spectrum

    # Standard normal-effort speech in a descending broadband masking noise
    # (an office/ventilation-like spectrum): the band-audibility function A_i
    # is partial across the band, and the importance-weighted contribution
    # I_i*A_i (ANSI S3.5-1997 clause 6) sums to the index SII.
    speech = standard_speech_spectrum("normal")
    noise = np.array([38.0, 37.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0, 24.0,
                      22.0, 20.0, 18.0, 16.0, 14.0, 12.0, 10.0, 8.0, 6.0])
    result = speech_intelligibility_index(speech, noise)

    freqs = result.frequencies
    positions = np.arange(freqs.size)
    weighted = result.band_audibility * result.band_importance

    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.bar(positions, result.band_audibility, width=0.8, color=COLOR_PRIMARY,
           alpha=0.35, zorder=2, label=r"Band audibility $A_i$")
    ax.bar(positions, weighted / weighted.max(), width=0.45, color=COLOR_PRIMARY,
           zorder=3, label=r"Importance-weighted $I_i\,A_i$ (scaled)")
    ax.set_title(
        f"Speech Intelligibility Index (ANSI S3.5-1997)   SII = {result.sii:.2f}",
        fontweight="bold", pad=12)
    ax.set_xlabel("One-third-octave band [Hz]")
    ax.set_ylabel("Band audibility")
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.grid(which="major", axis="y", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "speech_intelligibility.png"))
    plt.close()


def generate_sii_vocal_efforts(output_dir: str) -> None:
    """ANSI S3.5-1997 Table 3 standard speech spectra by vocal effort."""
    print("Generating sii_vocal_efforts.png...")
    from phonometry import speech_intelligibility_index, standard_speech_spectrum
    from phonometry.sii import BAND_CENTERS, VOCAL_EFFORTS

    freqs = BAND_CENTERS
    # Distinct hues (not COLOR_GRID, which blends into the gridlines and is
    # near-invisible on a light background) for the four ordered efforts.
    colours = {"normal": COLOR_TERTIARY, "raised": "#7f7f7f",
               "loud": COLOR_PRIMARY, "shout": COLOR_SECONDARY}
    fig, (ax_s, ax_i) = plt.subplots(1, 2, figsize=(12.5, 5.6))

    # --- Left: the four standard speech spectra. ---
    for effort in VOCAL_EFFORTS:
        ax_s.plot(freqs, standard_speech_spectrum(effort), "o-",
                  color=colours[effort], label=effort.capitalize())
    ax_s.set_xscale("log")
    ax_s.set_xticks(list(freqs))
    ax_s.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax_s.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_s.set_xlabel("One-third-octave band [Hz]")
    ax_s.set_ylabel("Speech spectrum level [dB SPL]")
    ax_s.set_title("ANSI S3.5-1997 — speech spectra by vocal effort",
                   fontweight="bold", pad=10)
    ax_s.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_s.set_axisbelow(True)
    ax_s.legend(loc="upper right")

    # --- Right: SII in a fixed broadband noise rises with vocal effort. ---
    noise = np.array([48.0, 47.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0,
                      32.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0])
    indices = [speech_intelligibility_index(e, noise).sii for e in VOCAL_EFFORTS]
    positions = np.arange(len(VOCAL_EFFORTS))
    bar_colours = [colours[e] for e in VOCAL_EFFORTS]
    ax_i.bar(positions, indices, width=0.6, color=bar_colours, zorder=2)
    for x, v in zip(positions, indices):
        ax_i.text(x, v + 0.01, f"{v:.2f}", ha="center", va="bottom",
                  fontweight="bold")
    ax_i.set_xticks(positions)
    ax_i.set_xticklabels([e.capitalize() for e in VOCAL_EFFORTS])
    ax_i.set_ylim(0.0, 1.0)
    ax_i.set_ylabel("Speech Intelligibility Index")
    ax_i.set_title("SII vs vocal effort in a fixed noise",
                   fontweight="bold", pad=10)
    ax_i.grid(which="major", axis="y", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax_i.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "sii_vocal_efforts.png"))
    plt.close()


def generate_impulse_prominence(output_dir: str) -> None:
    """NT ACOU 112: predicted prominence and the LAeq adjustment."""
    print("Generating impulse_prominence.png...")
    from phonometry import (
        impulse_adjustment,
        impulse_prominence,
        predicted_prominence,
    )
    from phonometry.impulse_prominence import ADJUSTMENT_THRESHOLD

    fig, (ax_p, ax_k) = plt.subplots(1, 2, figsize=(12.5, 5.4))

    # --- Left: P vs onset rate for three level differences (Formula 1). ---
    orate = np.logspace(1, 4, 200)  # 10 to 10000 dB/s
    # Distinct hues (not COLOR_GRID, which is near-invisible on a light ground).
    for ld, colour in ((5.0, COLOR_TERTIARY), (15.0, COLOR_PRIMARY),
                       (30.0, COLOR_SECONDARY)):
        ax_p.plot(orate, predicted_prominence(orate, np.full_like(orate, ld)),
                  color=colour, label=f"LD = {ld:g} dB")
    ax_p.set_xscale("log")
    ax_p.set_xlabel("Onset rate [dB/s]")
    ax_p.set_ylabel("Predicted prominence $P$")
    ax_p.set_title(r"$P = 3\,\lg(\mathrm{OR}) + 2\,\lg(\mathrm{LD})$",
                   fontweight="bold", pad=10)
    ax_p.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_p.set_axisbelow(True)
    ax_p.legend(loc="upper left")

    # --- Right: the adjustment KI(P) with example impulses. ---
    result = impulse_prominence([1200.0, 300.0, 60.0], [32.0, 18.0, 11.0])
    grid = np.linspace(0.0, 16.0, 200)
    ax_k.plot(grid, impulse_adjustment(grid), color=COLOR_PRIMARY,
              label=r"$K_I = 1.8\,(P-5)$")
    ax_k.axvline(ADJUSTMENT_THRESHOLD, color="#7f7f7f", linestyle=":",
                 label=f"threshold $P = {ADJUSTMENT_THRESHOLD:g}$")
    ax_k.scatter(result.per_impulse, impulse_adjustment(result.per_impulse),
                 color="#aec7e8", zorder=3, label="Impulses")
    ax_k.scatter([result.prominence], [result.adjustment], color=COLOR_SECONDARY,
                 marker="*", s=140, zorder=4,
                 label=f"Governing  $K_I$ = {result.adjustment:.1f} dB")
    ax_k.set_xlabel("Predicted prominence $P$")
    ax_k.set_ylabel("Adjustment $K_I$ [dB]")
    ax_k.set_title("Adjustment to $L_{Aeq}$", fontweight="bold", pad=10)
    ax_k.set_ylim(bottom=0.0)
    ax_k.grid(color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_k.set_axisbelow(True)
    ax_k.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "impulse_prominence.png"))
    plt.close()


def generate_multiple_shock(output_dir: str) -> None:
    """ISO 2631-5: seat-to-spine transmissibility and the injury probability."""
    print("Generating multiple_shock.png...")
    from phonometry import (
        compression_dose,
        dose_from_peaks,
        injury_probability,
        injury_risk,
        seat_to_spine_transfer,
    )
    from phonometry.multiple_shock_vibration import (
        MZ_MALE,
        RISK_THRESHOLDS_MALE,
    )

    fig, (ax_h, ax_r) = plt.subplots(1, 2, figsize=(12.5, 5.4))

    # --- Left: seat-to-spine transmissibility |H(f)| (Formula 1). ---
    freq = np.logspace(np.log10(0.5), np.log10(80.0), 400)
    ax_h.plot(freq, np.abs(seat_to_spine_transfer(freq)), color=COLOR_PRIMARY,
              label=r"$|H(f)|$")
    ax_h.axhline(1.0, color=COLOR_GRID, linestyle="--", alpha=0.7)
    ax_h.set_xscale("log")
    ax_h.set_xlabel("Frequency [Hz]")
    ax_h.set_ylabel("Transmissibility  seat $\\rightarrow$ spine")
    ax_h.set_title("Seat-to-spine transfer function", fontweight="bold", pad=10)
    ax_h.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_h.set_axisbelow(True)
    ax_h.legend(loc="upper right")

    # --- Right: injury probability Pi(R) with the Annex C male example. ---
    grid = np.linspace(0.0, 3.0, 300)
    sexes: tuple[tuple[Literal["male", "female"], str], ...] = (
        ("male", COLOR_PRIMARY),
        ("female", COLOR_SECONDARY),
    )
    for sex, colour in sexes:
        prob = 100.0 * injury_probability(grid, sex=sex)
        ax_r.plot(grid, prob, color=colour, label=f"{sex}")
    # The worked example: five 40 m/s2 peaks, 82 kg male -> R = 1.22.
    sd = compression_dose(dose_from_peaks([40.0] * 5), mz=MZ_MALE)
    r_male = injury_risk(sd, start_age=20, years=20, days_per_year=120, sex="male")
    for level, r_val in zip((10, 50, 90), RISK_THRESHOLDS_MALE):
        ax_r.axhline(level, color="#7f7f7f", linestyle=":", lw=0.8)
        ax_r.plot([r_val, r_val], [0.0, level], color="#7f7f7f", linestyle=":", lw=0.8)
    ax_r.scatter([r_male], [100.0 * injury_probability(r_male, sex="male")],
                 color=COLOR_TERTIARY, marker="*", s=160, zorder=4,
                 label=f"Example  $R$ = {r_male:.2f}")
    ax_r.set_xlabel("Stress variable $R$")
    ax_r.set_ylabel("Probability of lumbar injury [%]")
    ax_r.set_title("Injury probability (Annex C)", fontweight="bold", pad=10)
    ax_r.set_xlim(left=0.0)
    ax_r.set_ylim(0.0, 100.0)
    ax_r.grid(color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_r.set_axisbelow(True)
    ax_r.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "multiple_shock.png"))
    plt.close()


def generate_enclosed_space_absorption(output_dir: str) -> None:
    """EN 12354-6: absorption area and reverberation time of a room."""
    print("Generating enclosed_space_absorption.png...")
    from phonometry import enclosed_space_reverberation
    from phonometry.enclosed_space_absorption import OCTAVE_BANDS

    # A 5 x 4 x 3 m office (60 m3): hard plaster walls and floor; the ceiling is
    # either bare plaster or lined with an absorbing acoustic tile.
    volume = 60.0
    plaster = [0.02, 0.03, 0.03, 0.04, 0.05, 0.05, 0.05]
    tile = [0.15, 0.35, 0.65, 0.85, 0.90, 0.90, 0.85]
    walls_floor = [(54.0, plaster), (20.0, plaster)]  # walls + floor
    bare = enclosed_space_reverberation(
        [*walls_floor, (20.0, plaster)], volume, air_condition="20C_50-70")
    treated = enclosed_space_reverberation(
        [*walls_floor, (20.0, tile)], volume, air_condition="20C_50-70")

    fig, (ax_a, ax_t) = plt.subplots(1, 2, figsize=(12.5, 5.4))
    freq = OCTAVE_BANDS
    labels = [f"{f:g}" if f < 1000 else f"{f / 1000:g}k" for f in freq]

    for res, colour, name in ((bare, COLOR_SECONDARY, "bare ceiling"),
                              (treated, COLOR_PRIMARY, "acoustic ceiling")):
        ax_a.semilogx(freq, res.absorption_area, color=colour, marker="o", label=name)
        ax_t.semilogx(freq, res.reverberation_time, color=colour, marker="o",
                      label=name)
    for ax, ylab, title in (
        (ax_a, "Equivalent absorption area $A$ [m$^2$]", "Absorption area (Formula 1)"),
        (ax_t, "Reverberation time $T$ [s]", "Reverberation time (Formula 5)"),
    ):
        ax.set_xticks(freq)
        ax.set_xticklabels(labels)
        ax.set_xlabel("Octave-band centre frequency [Hz]")
        ax.set_ylabel(ylab)
        ax.set_title(title, fontweight="bold", pad=10)
        ax.set_ylim(bottom=0.0)
        ax.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
        ax.set_axisbelow(True)
        ax.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "enclosed_space_absorption.png"))
    plt.close()


def generate_room_noise_criteria(output_dir: str) -> None:
    """ANSI S12.2-2019: NC tangency rating and RC Mark II classification."""
    print("Generating room_noise_criteria.png...")
    from phonometry import noise_criterion, room_criterion
    from phonometry.room_noise import NC_CURVES, NC_INDICES, OCTAVE_BANDS

    # A ventilation-dominated room spectrum: the low-frequency bands rise well
    # above the sloped RC reference (a rumble tag under RC Mark II) while the
    # mid bands set the NC tangency.
    spectrum = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])
    nc = noise_criterion(spectrum)
    rc = room_criterion(spectrum)

    fig, (ax_nc, ax_rc) = plt.subplots(1, 2, figsize=(12.5, 5.6))

    # --- Left: NC curves + tangency rating. ---
    for row, idx in zip(NC_CURVES, NC_INDICES):
        ax_nc.plot(OCTAVE_BANDS, row, color=COLOR_GRID, lw=0.8, zorder=1)
        ax_nc.annotate(f"{idx:.0f}", (OCTAVE_BANDS[-1], row[-1]),
                       fontsize=7, color="#999999", va="center")
    ax_nc.plot(OCTAVE_BANDS, spectrum, "o-", color=COLOR_PRIMARY, zorder=3,
               label="Measured")
    gov = spectrum[OCTAVE_BANDS == nc.governing_frequency][0]
    ax_nc.plot([nc.governing_frequency], [gov], "D", color=COLOR_SECONDARY,
               ms=9, zorder=4, label=f"Tangent @ {nc.governing_frequency:g} Hz")
    ax_nc.set_xscale("log")
    ax_nc.set_xticks(list(OCTAVE_BANDS))
    ax_nc.set_xticklabels([f"{f:g}" for f in OCTAVE_BANDS], rotation=45, ha="right")
    ax_nc.set_xlabel("Octave-band center frequency [Hz]")
    ax_nc.set_ylabel("Octave-band sound pressure level [dB]")
    ax_nc.set_title(f"Noise Criteria — tangency method   NC-{nc.rating:g}",
                    fontweight="bold", pad=10)
    ax_nc.grid(which="both", axis="y", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_nc.set_axisbelow(True)
    ax_nc.legend(loc="upper right")

    # --- Right: RC Mark II reference + rumble/hiss tolerances. ---
    ref = rc.reference_curve
    low = OCTAVE_BANDS <= 500.0
    high = OCTAVE_BANDS >= 1000.0
    ax_rc.plot(OCTAVE_BANDS, ref, "s--", color="#7f7f7f",
               label=f"Reference RC-{rc.rating}")
    ax_rc.fill_between(OCTAVE_BANDS[low], ref[low], ref[low] + 5.0,
                       color="#ff7f0e", alpha=0.25, label="Rumble tol. (+5 dB)")
    ax_rc.fill_between(OCTAVE_BANDS[high], ref[high], ref[high] + 3.0,
                       color=COLOR_PRIMARY, alpha=0.20, label="Hiss tol. (+3 dB)")
    ax_rc.plot(OCTAVE_BANDS, spectrum, "o-", color=COLOR_PRIMARY, zorder=3,
               label="Measured")
    ax_rc.set_xscale("log")
    ax_rc.set_xticks(list(OCTAVE_BANDS))
    ax_rc.set_xticklabels([f"{f:g}" for f in OCTAVE_BANDS], rotation=45, ha="right")
    ax_rc.set_xlabel("Octave-band center frequency [Hz]")
    ax_rc.set_ylabel("Octave-band sound pressure level [dB]")
    ax_rc.set_title(f"Room Criteria Mark II   {rc.label}",
                    fontweight="bold", pad=10)
    ax_rc.grid(which="both", axis="y", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_rc.set_axisbelow(True)
    ax_rc.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "room_noise_criteria.png"))
    plt.close()


def generate_hearing_threshold(output_dir: str) -> None:
    """ISO 7029 age-related threshold and ISO 389-7 reference threshold."""
    print("Generating hearing_threshold.png...")
    from phonometry import age_threshold, reference_threshold
    from phonometry.hearing import AUDIOMETRIC_FREQUENCIES

    freqs = AUDIOMETRIC_FREQUENCIES
    fig, (ax_age, ax_ref) = plt.subplots(1, 2, figsize=(12.5, 5.6))

    # --- Left: ISO 7029 median threshold by age (male) + 10-90 % band @70. ---
    ages = [(20, "#9e9e9e"), (40, "#7f7f7f"), (60, COLOR_PRIMARY),
            (80, COLOR_SECONDARY)]
    for age, color in ages:
        r = age_threshold(age, "male", 0.5)
        ax_age.plot(freqs, r.median, "o-", color=color, label=f"{age} yr")
    r70 = age_threshold(70, "male", 0.5)
    z90 = 1.2816
    ax_age.fill_between(freqs, r70.median - z90 * r70.spread_lower,
                        r70.median + z90 * r70.spread_upper,
                        color=COLOR_PRIMARY, alpha=0.12,
                        label="10-90 % band (70 yr)")
    ax_age.set_xscale("log")
    ax_age.set_xticks(list(freqs))
    ax_age.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax_age.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_age.invert_yaxis()
    ax_age.set_xlabel("Audiometric frequency [Hz]")
    ax_age.set_ylabel("Median threshold deviation from age 18 [dB]")
    ax_age.set_title("ISO 7029 — age-related threshold (male)",
                     fontweight="bold", pad=10)
    ax_age.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_age.set_axisbelow(True)
    ax_age.legend(loc="lower left")

    # --- Right: ISO 389-7 reference threshold, free vs diffuse field. ---
    ax_ref.plot(freqs, reference_threshold("free-field"), "o-",
                color=COLOR_PRIMARY, label="Free-field (frontal)")
    ax_ref.plot(freqs, reference_threshold("diffuse-field"), "s--",
                color=COLOR_SECONDARY, label="Diffuse-field")
    ax_ref.set_xscale("log")
    ax_ref.set_xticks(list(freqs))
    ax_ref.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax_ref.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_ref.set_xlabel("Audiometric frequency [Hz]")
    ax_ref.set_ylabel("Reference threshold [dB]")
    ax_ref.set_title("ISO 389-7 — reference threshold of hearing",
                     fontweight="bold", pad=10)
    ax_ref.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_ref.set_axisbelow(True)
    ax_ref.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "hearing_threshold.png"))
    plt.close()


def generate_noise_induced_hearing_loss(output_dir: str) -> None:
    """ISO 1999 noise-induced permanent threshold shift and HTLAN combination."""
    print("Generating noise_induced_hearing_loss.png...")
    from phonometry import htlan, nipts
    from phonometry.noise_induced_hearing_loss import NIPTS_FREQUENCIES

    freqs = NIPTS_FREQUENCIES
    fig, (ax_n, ax_h) = plt.subplots(1, 2, figsize=(12.5, 5.6))

    # --- Left: median NIPTS growth with exposure duration at 95 dB. ---
    durations = [(10, "#9e9e9e"), (20, "#7f7f7f"), (30, COLOR_PRIMARY),
                 (40, COLOR_SECONDARY)]
    for years, color in durations:
        r = nipts(95.0, years, 0.5)
        ax_n.plot(freqs, r.median, "o-", color=color, label=f"{years} yr")
    r40 = nipts(95.0, 40.0, 0.5)
    z90 = 1.2816
    ax_n.fill_between(freqs, np.maximum(r40.median - z90 * r40.spread_lower, 0.0),
                      r40.median + z90 * r40.spread_upper,
                      color=COLOR_SECONDARY, alpha=0.12,
                      label="10-90 % band (40 yr)")
    ax_n.set_xscale("log")
    ax_n.set_xticks(list(freqs))
    ax_n.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax_n.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_n.invert_yaxis()
    ax_n.set_xlabel("Audiometric frequency [Hz]")
    ax_n.set_ylabel("Median NIPTS [dB]")
    ax_n.set_title(r"ISO 1999 — NIPTS at $L_{EX,8h}$ = 95 dB",
                   fontweight="bold", pad=10)
    ax_n.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_n.set_axisbelow(True)
    ax_n.legend(loc="lower left")

    # --- Right: HTLAN = age + noise for a 60-year-old worker, 95 dB / 30 yr. ---
    h = htlan(60, "male", 95.0, 30.0, 0.5)
    ax_h.plot(freqs, h.htla, "o-", color=COLOR_PRIMARY,
              label="Age (HTLA, ISO 7029)")
    ax_h.plot(freqs, h.nipts, "^-", color="#ff7f0e", label="Noise (NIPTS)")
    ax_h.plot(freqs, h.threshold, "s--", color=COLOR_SECONDARY,
              label="Age + noise (HTLAN)")
    ax_h.set_xscale("log")
    ax_h.set_xticks(list(freqs))
    ax_h.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax_h.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax_h.invert_yaxis()
    ax_h.set_xlabel("Audiometric frequency [Hz]")
    ax_h.set_ylabel("Hearing threshold level [dB]")
    ax_h.set_title("ISO 1999 — HTLAN (male, age 60, 95 dB / 30 yr)",
                   fontweight="bold", pad=10)
    ax_h.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_h.set_axisbelow(True)
    ax_h.legend(loc="lower left")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "noise_induced_hearing_loss.png"))
    plt.close()


def generate_uncertainty(output_dir: str) -> None:
    """GUM uncertainty budget and Monte Carlo distribution (Guide 98-3 + S1)."""
    print("Generating uncertainty_budget.png...")
    import phonometry as ph

    # A-weighted level: reading plus calibration, instrument and positional
    # corrections (all zero-mean); the model is their sum.
    quantities = [
        ph.Quantity(74.0, 0.0, name="Reading"),
        ph.rectangular(0.0, 0.20, name="Calibration"),
        ph.rectangular(0.0, 0.30, name="Instrument"),
        ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
    ]
    model = lambda a, b, c, d: a + b + c + d  # noqa: E731

    result = ph.combine_uncertainty(model, quantities)
    mc = ph.monte_carlo(model, quantities, trials=1_000_000, coverage=0.95, seed=1)
    k, big = result.expanded(0.95)

    fig, (ax_b, ax_m) = plt.subplots(1, 2, figsize=(12.5, 5.4))

    # --- Left: uncertainty budget (contributions). ---
    contrib = result.contributions
    names = list(result.names)
    pos = np.arange(len(names))
    ax_b.barh(pos, contrib, color=COLOR_PRIMARY, zorder=2)
    ax_b.axvline(result.combined_uncertainty, color=COLOR_SECONDARY, ls="--",
                 label=f"$u_c$ = {result.combined_uncertainty:.3f} dB")
    ax_b.set_yticks(pos)
    ax_b.set_yticklabels(names)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Contribution to combined uncertainty [dB]")
    ax_b.set_title("GUM uncertainty budget", fontweight="bold", pad=10)
    ax_b.grid(which="major", axis="x", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax_b.set_axisbelow(True)
    ax_b.legend(loc="lower right")

    # --- Right: Monte Carlo output vs the GUM Gaussian. ---
    rng = np.random.default_rng(1)
    samples = (74.0 + rng.uniform(-0.20, 0.20, 200000)
               + rng.uniform(-0.30, 0.30, 200000)
               + rng.normal(0.0, 0.35, 200000))
    ax_m.hist(samples, bins=120, density=True, color=COLOR_PRIMARY, alpha=0.35,
              label="Monte Carlo (Suppl 1)")
    grid = np.linspace(samples.min(), samples.max(), 400)
    gauss = (np.exp(-0.5 * ((grid - result.value) / result.combined_uncertainty) ** 2)
             / (result.combined_uncertainty * np.sqrt(2 * np.pi)))
    ax_m.plot(grid, gauss, color=COLOR_SECONDARY, lw=2, label="GUM Gaussian")
    ax_m.axvspan(mc.interval[0], mc.interval[1], color=COLOR_PRIMARY, alpha=0.12,
                 label="95 % coverage interval")
    ax_m.set_xlabel("A-weighted level [dB]")
    ax_m.set_ylabel("Probability density")
    ax_m.set_title(f"Y = {result.value:.2f} dB,  U = {big:.2f} dB (k = {k:.2f})",
                   fontweight="bold", pad=10)
    ax_m.grid(color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_m.set_axisbelow(True)
    ax_m.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(themed_path(output_dir, "uncertainty_budget.png"))
    plt.close()


def generate_all(img_dir: str) -> None:
    """Generate every documentation figure for the currently active theme."""
    generate_filter_type_comparison(img_dir)
    generate_filter_responses(img_dir)
    generate_signal_responses(img_dir)
    generate_multichannel_response(img_dir)
    generate_decomposition_plot(img_dir)

    generate_weighting_responses(img_dir)
    generate_g_weighting_response(img_dir)
    generate_equal_loudness_contours(img_dir)
    generate_time_weighting_plot(img_dir)
    generate_crossover_plot(img_dir)

    # Feature documentation plots (levels, spectrogram, zero-phase, weighting accuracy)
    generate_spectrogram_example(img_dir)
    generate_ln_levels_example(img_dir)
    generate_zero_phase_comparison(img_dir)
    generate_weighting_accuracy_hf(img_dir)

    # Docs-enrichment plots (group delay, IEC toneburst, block continuity, class mask)
    generate_group_delay_comparison(img_dir)
    generate_tone_burst_iec(img_dir)
    generate_block_processing_continuity(img_dir)
    generate_class_mask_overlay(img_dir)
    generate_calibration_stability(img_dir)
    generate_sel_concept(img_dir)
    generate_lden_profile(img_dir)
    generate_tonality_spectrum(img_dir)

    # Psychoacoustics / intensity plots (loudness, STI, p-p intensity)
    generate_loudness_pattern(img_dir)
    generate_sti_curve(img_dir)
    generate_intensity_demo(img_dir)

    # Room / building acoustics plots (ISO 18233 excitations + IR, Schroeder
    # decay, ISO 717-1/-2 ratings)
    generate_excitation_signals(img_dir)
    generate_impulse_response(img_dir)
    generate_schroeder_decay(img_dir)
    generate_insulation_rating(img_dir)
    generate_impact_rating(img_dir)

    # Building-acoustics prediction / uncertainty (EN 12354-1, ISO 12999-1)
    generate_prediction_flanking_demo(img_dir)
    generate_insulation_uncertainty_demo(img_dir)

    # Outdoor propagation & occupational exposure (ISO 9613-1/2, ISO 9612)
    generate_air_absorption_alpha(img_dir)
    generate_outdoor_attenuation_breakdown(img_dir)
    generate_exposure_uncertainty(img_dir)

    # Materials: absorption rating, airflow resistance, impedance tube
    # (ISO 11654, ISO 9053-1/-2, ISO 10534-1/-2, ASTM E2611)
    generate_absorption_rating(img_dir)
    generate_airflow_resistance(img_dir)
    generate_impedance_tube(img_dir)

    # Scattering/diffusion, in-situ road absorption, precision sound power
    # (ISO 17497-1/-2, ISO 13472-1, ISO 3745 / ISO 9614-3)
    generate_scattering_coefficient(img_dir)
    generate_diffusion_polar(img_dir)
    generate_insitu_absorption(img_dir)
    generate_precision_anechoic_power(img_dir)
    generate_intensity_scan_power(img_dir)

    # Human vibration (ISO 8041-1, ISO 2631-1/-2/-4, ISO 5349-1/-2,
    # Directive 2002/44/EC): frequency weighting, weighted a_w, daily A(8)
    generate_vibration_weighting(img_dir)
    generate_weighted_acceleration(img_dir)
    generate_daily_vibration_exposure(img_dir)

    # Speech intelligibility (ANSI S3.5-1997): band audibility and the SII.
    generate_speech_intelligibility(img_dir)
    generate_sii_vocal_efforts(img_dir)
    generate_impulse_prominence(img_dir)

    # Room-noise criteria (ANSI S12.2-2019): NC tangency and RC Mark II.
    generate_room_noise_criteria(img_dir)

    # Hearing threshold (ISO 7029 age-related, ISO 389-7 reference).
    generate_hearing_threshold(img_dir)

    # Noise-induced hearing loss (ISO 1999 NIPTS and HTLAN).
    generate_noise_induced_hearing_loss(img_dir)

    # Multiple-shock whole-body vibration (ISO 2631-5 Clause 5 + Annex C).
    generate_multiple_shock(img_dir)

    # Sound absorption in enclosed spaces (EN 12354-6 Clause 4).
    generate_enclosed_space_absorption(img_dir)

    # Measurement uncertainty (GUM Guide 98-3 + Supplement 1 Monte Carlo).
    generate_uncertainty(img_dir)

    # Psychoacoustics / open-plan plots (sharpness weighting, spatial decay)
    generate_sharpness_weighting(img_dir)
    generate_open_plan_decay(img_dir)

    # Advanced psychoacoustics (plan-17 block A): ECMA-418-2 Sottek model and
    # Moore-Glasberg ISO 532-2/-3 loudness (models, specific loudness, sound
    # quality metrics, time-varying loudness).
    generate_loudness_models_comparison(img_dir)
    generate_sottek_specific_loudness(img_dir)
    generate_tonality_roughness_demo(img_dir)
    generate_moore_glasberg_time_loudness(img_dir)


if __name__ == "__main__":
    img_dir = ".github/images"
    os.makedirs(img_dir, exist_ok=True)

    # Every figure is produced four times: light/dark theme x English/Spanish
    # ("_dark" / "_es" / "_es_dark" suffixes) so both site languages can
    # follow the user's mode.
    for lang in ("en", "es"):
        set_lang(lang)
        for dark in (False, True):
            set_theme(dark)
            print(f"--- Generating {lang} {'dark' if dark else 'light'} theme figures ---")
            generate_all(img_dir)

    print("Graphics generated successfully.")
