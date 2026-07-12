import os
import sys

# Deterministic figure output: pin every numerical thread pool to a single
# thread BEFORE numpy/scipy/numba import their backends, so multi-threaded
# reductions cannot reorder floating-point sums and perturb the rendered bytes
# across machines (the CI "Documentation figures" job runs on a different core
# count than a dev box, which is what made the heavy compute figures flaky).
for _threads_var in (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_threads_var, "1")

from functools import lru_cache  # noqa: E402
from typing import Any, Literal  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
from scipy import signal as scipy_signal  # noqa: E402

# Add src to path to use the local package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from phonometry import OctaveFilterBank  # noqa: E402

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
    # weighting_class_mask figure (IEC 61672-1 Table 3 verifier)
    "Weighting Deviation vs IEC 61672-1:2013 Table 3 Limits":
        "Desviaci\u00f3n de ponderaci\u00f3n vs l\u00edmites de la Tabla 3 de IEC 61672-1:2013",
    "Class 1 acceptance region": "Regi\u00f3n de aceptaci\u00f3n de clase 1",
    "Class 1 upper/lower limit": "L\u00edmite superior/inferior de clase 1",
    "Class 2 upper/lower limit": "L\u00edmite superior/inferior de clase 2",
    "A weighting deviation (48 kHz)": "Desviaci\u00f3n de ponderaci\u00f3n A (48 kHz)",
    "C weighting deviation (48 kHz)": "Desviaci\u00f3n de ponderaci\u00f3n C (48 kHz)",
    "Deviation from design goal [dB]": "Desviaci\u00f3n del objetivo de dise\u00f1o [dB]",
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
    # filter_class0_mask figure (IEC 61260:1995 / ANSI S1.11-2004 class 0)
    "Pass-band Class 0/1/2 Limits (IEC 61260:1995 / ANSI S1.11-2004)":
        "Límites de clase 0/1/2 en banda de paso (IEC 61260:1995 / ANSI S1.11-2004)",
    "Class 0 corridor": "Corredor de clase 0",
    "Class 1 corridor": "Corredor de clase 1",
    "Class 2 corridor": "Corredor de clase 2",
    # intensity_insulation figure (ISO 15186-1)
    "ISO 15186-1 Intensity Sound Reduction Index (RI and RI,M)":
        "Índice de reducción sonora por intensidad ISO 15186-1 (RI y RI,M)",
    "Sound reduction index [dB]": "Índice de reducción sonora [dB]",
    "Kc adaptation": "Adaptación Kc",
    "RI (intensity)": "RI (intensidad)",
    # survey_insulation figure (ISO 10052)
    "ISO 10052 Survey Method: Reverberation-Index Correction":
        "Método de control ISO 10052: corrección por índice de reverberación",
    "Level difference [dB]": "Diferencia de nivel [dB]",
    "D (level difference)": "D (diferencia de nivel)",
    "DnT (standardized)": "DnT (estandarizada)",
    "octave bands, T0 = 0.5 s": "bandas de octava, T0 = 0,5 s",
    # absorption_uncertainty figure (ISO 12999-2)
    "ISO 12999-2 Sound Absorption Coefficient Uncertainty":
        "Incertidumbre del coeficiente de absorción sonora (ISO 12999-2)",
    "+/-U (k = 2), reproducibility": "±U (k = 2), reproducibilidad",
    "alpha_s (ISO 354)": "alpha_s (ISO 354)",
    # floor_covering_improvement figure (ISO 16251-1)
    "ISO 16251-1 Floor-Covering Impact Sound Improvement":
        "Mejora a impacto de revestimientos de suelo (ISO 16251-1)",
    "Improvement of impact sound insulation [dB]":
        "Mejora del aislamiento a impactos [dB]",
    "delta-L (improvement)": "delta-L (mejora)",
    # flanking_transmission figure (ISO 10848)
    "ISO 10848 Junction Vibration Reduction Index":
        "Índice de reducción vibracional de unión (ISO 10848)",
    "Vibration reduction index Kij [dB]":
        "Índice de reducción vibracional Kij [dB]",
    "Kij (ISO 10848)": "Kij (ISO 10848)",
    "mean Kij (200-1250 Hz)": "Kij medio (200-1250 Hz)",
    # tonal_audibility figure (ISO 1996-2)
    "ISO 1996-2 Tonal Adjustment": "Ajuste tonal ISO 1996-2",
    r"Tonal audibility $\Delta L_{ta}$ [dB]":
        r"Audibilidad tonal $\Delta L_{ta}$ [dB]",
    r"Tonal adjustment $K_t$ [dB]": r"Ajuste tonal $K_t$ [dB]",
    r"$K_t(\Delta L_{ta})$ (Formulae C.4-C.6)":
        r"$K_t(\Delta L_{ta})$ (Fórmulas C.4-C.6)",
    "Annex C.5 examples": "ejemplos del Anexo C.5",
    "mid-range tone": "tono de rango medio",
    # reverberation_models figure (Sabine / Eyring / Millington / Fitzroy / Arau)
    "Reverberation-time prediction models":
        "Modelos de predicción del tiempo de reverberación",
    # dynamic_stiffness figure (EN 29052-1)
    "EN 29052-1 Floating-Floor Resonance":
        "Resonancia de suelo flotante EN 29052-1",
    r"Dynamic stiffness per unit area $s'$ [MN/m³]":
        r"Rigidez dinámica por unidad de área $s'$ [MN/m³]",
    r"Natural frequency $f_0$ [Hz]": r"Frecuencia natural $f_0$ [Hz]",
    "design point": "punto de diseño",
    # mechanical_mobility figure (ISO 7626-1)
    "ISO 7626-1 Mechanical Mobility FRFs":
        "FRF de movilidad mecánica ISO 7626-1",
    "Normalized FRF magnitude": "Magnitud FRF normalizada",
    "Receptance $|H|$ (× k)": "Receptancia $|H|$ (× k)",
    r"Mobility $|Y|$ (× k/$\omega_0$)": r"Movilidad $|Y|$ (× k/$\omega_0$)",
    r"Accelerance $|A|$ (× k/$\omega_0^2$)":
        r"Accelerancia $|A|$ (× k/$\omega_0^2$)",
    "resonance $f_0$": "resonancia $f_0$",
    # transfer_stiffness figure (ISO 10846)
    "ISO 10846 Dynamic Transfer Stiffness":
        "Rigidez dinámica de transferencia ISO 10846",
    r"Transfer stiffness level $L_k$ [dB re 1 N/m]":
        r"Nivel de rigidez de transferencia $L_k$ [dB re 1 N/m]",
    r"true $L_k$ of $k_{2,1}=k+j\omega c$":
        r"$L_k$ real de $k_{2,1}=k+j\omega c$",
    r"indirect method $-(2\pi f)^2 m_2 T$":
        r"método indirecto $-(2\pi f)^2 m_2 T$",
    # vibration_sound_power figure (ISO/TS 7849)
    "ISO/TS 7849 Sound Power from Surface Vibration":
        "Potencia sonora desde vibración superficial ISO/TS 7849",
    r"Sound power level $L_W$ [dB re 1 pW]":
        r"Nivel de potencia sonora $L_W$ [dB re 1 pW]",
    "Part 1 upper limit ($\\varepsilon$ = 1)":
        "Parte 1 límite superior ($\\varepsilon$ = 1)",
    "Part 2 engineering ($\\varepsilon$ measured)":
        "Parte 2 ingeniería ($\\varepsilon$ medido)",
    # structure_borne_power figure (EN 15657)
    "EN 15657 Characteristic Structure-Borne Sound Power":
        "Potencia sonora estructural característica EN 15657",
    r"Structure-borne power level $L_{Ws}$ [dB re 1 pW]":
        r"Nivel de potencia estructural $L_{Ws}$ [dB re 1 pW]",
    "low-mobility plate": "placa de baja movilidad",
    "high-mobility plate": "placa de alta movilidad",
    # installed_structure_borne figure (EN 12354-5)
    "EN 12354-5 Installed Structure-Borne Sound":
        "Ruido estructural instalado EN 12354-5",
    r"characteristic $L_{Ws,c}$ (EN 15657)":
        r"característica $L_{Ws,c}$ (EN 15657)",
    r"installed $L_{Ws,inst}$ = $L_{Ws,c}-D_C$":
        r"instalada $L_{Ws,inst}$ = $L_{Ws,c}-D_C$",
    "paths $L_{n,s,ij}$": "caminos $L_{n,s,ij}$",
    r"total $L_{n,s}$": r"total $L_{n,s}$",
    # tone_audibility figure (ISO/PAS 20065)
    "ISO/PAS 20065 Tonal Audibility": "Audibilidad tonal ISO/PAS 20065",
    r"Audibility $\Delta L$ [dB]": r"Audibilidad $\Delta L$ [dB]",
    r"threshold $\Delta L = 0$ dB": r"umbral $\Delta L = 0$ dB",
    # facade_prediction figure (EN 12354-3 Annex F)
    "EN 12354-3 Façade Sound Insulation (Annex F example)":
        "Aislamiento acústico de fachada EN 12354-3 (ejemplo del Anexo F)",
    "Reduction index / level difference [dB]":
        "Índice de reducción / diferencia de niveles [dB]",
    "Rp — wall": "Rp — muro",
    "Rp — window": "Rp — ventana",
    "Rp — skylight": "Rp — claraboya",
    "Rp — air inlet": "Rp — entrada de aire",
    "R′ (façade)": "R′ (fachada)",
    "air inlet limits the low bands": "la entrada de aire limita las bandas bajas",
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
    # Fluctuation strength + psychoacoustic annoyance (Fastl & Zwicker; Osses 2016)
    "Fluctuation Strength — 4 Hz Band-Pass Characteristic":
        "Intensidad de fluctuación — característica de paso de banda a 4 Hz",
    "Fluctuation strength F [vacil]": "Intensidad de fluctuación F [vacil]",
    "AM-tone F, signal model [vacil]":
        "F de tono AM, modelo de señal [vacil]",
    "4 Hz reference": "referencia 4 Hz",
    "Psychoacoustic Annoyance vs Loudness (Fastl & Zwicker)":
        "Molestia psicoacústica vs sonoridad (Fastl y Zwicker)",
    "Percentile loudness N5 [sone]": "Sonoridad percentil N5 [sonios]",
    "Psychoacoustic annoyance PA": "Molestia psicoacústica PA",
    "Baseline: S = 1.75 acum, F = R = 0":
        "Base: S = 1,75 acum, F = R = 0",
    "Sharp: S = 3.5 acum": "Aguda: S = 3,5 acum",
    "Rough + fluctuating: F = 1.2 vacil, R = 0.7 asper":
        "Áspera + fluctuante: F = 1,2 vacil, R = 0,7 asper",
    # Electroacoustics (IEC 60268-3 distortion; Bendat & Piersol response)
    "Harmonic Distortion of a Single-Tone Test (IEC 60268-3)":
        "Distorsión armónica de un ensayo con tono único (IEC 60268-3)",
    "Magnitude spectrum": "Espectro de magnitud",
    "Harmonics n·f₁": "Armónicos n·f₁",
    "Level re fundamental [dB]": "Nivel respecto al fundamental [dB]",
    "Frequency Response and Coherence (Bendat & Piersol)":
        "Respuesta en frecuencia y coherencia (Bendat y Piersol)",
    "True |H|": "|H| verdadero",
    "Estimated |H| (H1)": "|H| estimado (H1)",
    # Underwater acoustics (ISO 17208 ship radiated noise; ISO 18406 pile driving)
    "Ship Equivalent Monopole Source Level (ISO 17208-2)":
        "Nivel de fuente monopolar equivalente de buque (ISO 17208-2)",
    "Source level Ls": "Nivel de fuente Ls",
    "Radiated noise level": "Nivel de ruido radiado",
    "Surface correction ΔL [dB]": "Corrección de superficie ΔL [dB]",
    "Surface correction ΔL": "Corrección de superficie ΔL",
    "Level [dB re 1 µPa·m]": "Nivel [dB re 1 µPa·m]",
    "Percussive Pile-Driving Strike (ISO 18406)":
        "Golpe de hincado de pilotes por percusión (ISO 18406)",
    "Time [ms]": "Tiempo [ms]",
    "Pressure [Pa]": "Presión [Pa]",
    "Number of strikes N": "Número de golpes N",
    "Cumulative SEL [dB re 1 µPa²·s]": "SEL acumulado [dB re 1 µPa²·s]",
    "ICAO Aircraft Flyover — Effective Perceived Noise Level (Annex 16)":
        "Sobrevuelo de aeronave ICAO — Nivel efectivo de ruido percibido (Anexo 16)",
    "Level [PNdB]": "Nivel [PNdB]",
    "10 dB-down window": "Ventana 10 dB por debajo",
    "Wind-Turbine Tonal Audibility (IEC 61400-11)":
        "Audibilidad tonal de aerogenerador (IEC 61400-11)",
    "Narrowband spectrum": "Espectro de banda estrecha",
    "Critical band": "Banda crítica",
    # Underwater propagation (plan-22 P1): transmission loss, sound speed, sonar.
    "Underwater Transmission Loss (Francois–Garrison)":
        "Pérdida por transmisión submarina (Francois–Garrison)",
    "Range [m]": "Distancia [m]",
    "Transmission loss [dB]": "Pérdida por transmisión [dB]",
    "Total transmission loss": "Pérdida por transmisión total",
    "Geometrical spreading": "Ensanchamiento geométrico",
    "Volume absorption": "Absorción de volumen",
    "Sea-Water Sound-Speed Profile (UNESCO)":
        "Perfil de velocidad del sonido en agua de mar (UNESCO)",
    "Sound speed [m/s]": "Velocidad del sonido [m/s]",
    "Depth [m]": "Profundidad [m]",
    "UNESCO sound speed": "Velocidad del sonido UNESCO",
    "Sound-channel axis": "Eje del canal sonoro",
    "Passive Sonar Equation": "Ecuación del sonar pasivo",
    "Signal excess [dB]": "Exceso de señal [dB]",
    "Signal excess": "Exceso de señal",
    "Detection limit (SE = 0)": "Límite de detección (SE = 0)",
    "Figure of merit": "Figura de mérito",
    # Underwater propagation (plan-22 P1 PR-2): seabed, ambient noise, traffic.
    "Seabed Reflection Loss (Rayleigh)":
        "Pérdida por reflexión en el fondo (Rayleigh)",
    "Grazing angle [°]": "Ángulo rasante [°]",
    "Bottom loss [dB]": "Pérdida por reflexión [dB]",
    "Bottom loss (sand)": "Pérdida por reflexión (arena)",
    "Water ρ = 1000, c = 1500\nSand ρ = 1900, c = 1650":
        "Agua ρ = 1000, c = 1500\nArena ρ = 1900, c = 1650",
    "Ocean Ambient Noise (Wenz)": "Ruido ambiental oceánico (Wenz)",
    "Spectrum level [dB re 1 µPa²/Hz]": "Nivel espectral [dB re 1 µPa²/Hz]",
    "Ship Traffic Source Level (JOMOPANS-ECHO)":
        "Nivel de fuente del tráfico marítimo (JOMOPANS-ECHO)",
    "Source spectral density [dB re 1 µPa²/Hz at 1 m]":
        "Densidad espectral de fuente [dB re 1 µPa²/Hz a 1 m]",
    "Wind": "Viento",
    "Thermal": "Térmico",
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
    # --- Tanda 11: Tier-1 animation labels ---
    "tone burst": "ráfaga de tono",
    "Fast (125 ms)": "Rápida (125 ms)",
    "Slow (1000 ms)": "Lenta (1000 ms)",
    "Impulse (35 ms / 1.5 s)": "Impulso (35 ms / 1,5 s)",
    "Time-weighting ballistics (IEC 61672-1)":
        "Balística de la ponderación temporal (IEC 61672-1)",
    "Mean-square response (normalized)":
        "Respuesta cuadrática media (normalizada)",
    "L_AF history": "Historia de L_AF",
    "onset (> 10 dB/s)": "inicio (> 10 dB/s)",
    "Impulse onset detection (NT ACOU 112)":
        "Detección del inicio de impulso (NT ACOU 112)",
    "A-weighted level L_AF [dB]": "Nivel ponderado A L_AF [dB]",
    "listening…": "escuchando…",
    "pressure p": "presión p",
    "velocity u": "velocidad u",
    "intensity p·u": "intensidad p·u",
    "Progressive wave — net power flows":
        "Onda progresiva — fluye potencia neta",
    "Standing wave — energy sloshes":
        "Onda estacionaria — la energía va y viene",
    "amplitude (normalized)": "amplitud (normalizada)",
    "Instantaneous sound intensity p·u":
        "Intensidad sonora instantánea p·u",
    "T20 fit": "ajuste T20",
    "T30 fit": "ajuste T30",
    "Schroeder backward integration (ISO 3382)":
        "Integración inversa de Schroeder (ISO 3382)",
    "integrating from the tail →": "integrando desde la cola →",
}

_ES_PATTERNS = [
    (r"^f = 10 kHz, α = (.+) dB/km\npractical spreading \(R₀ = 1000 m\)$",
     "f = 10 kHz, α = \\1 dB/km\\nensanchamiento práctico (R₀ = 1000 m)"),
    (r"^SL = 140, NL = 60, DI = 15, DT = 8 dB\nfigure of merit = (.+) dB$",
     "SL = 140, NL = 60, DI = 15, DT = 8 dB\\nfigura de mérito = \\1 dB"),
    (r"^(\d+) yr$", r"\1 años"),
    (r"^total \(limit\) (.+) dB$", r"total (límite) \1 dB"),
    (r"^total \(eng\.\) (.+) dB$", r"total (ing.) \1 dB"),
    # tone_audibility decisive legend (mathtext skips the decimal-comma pass).
    (r"^decisive \$\\Delta L\$ = (\d+)\.(\d+) dB @ (\d+)\.(\d+) Hz$",
     r"decisiva $\\Delta L$ = \1,\2 dB @ \3,\4 Hz"),
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
    (r"^AM broadband noise \(closed form, 60 dB\), peak (.+) vacil$",
     r"Ruido de banda ancha AM (forma cerrada, 60 dB), máximo \1 vacil"),
    (r"^AM tone \(signal model, 70 dB\), peak (.+) vacil$",
     r"Tono AM (modelo de señal, 70 dB), máximo \1 vacil"),
    (r"^Worked example \(PA = (.+)\)$",
     r"Ejemplo resuelto (PA = \1)"),
    (r"^PA = (.+)\nwS = (.+), wFR = (.+)$",
     "PA = \\1\\nwS = \\2, wFR = \\3"),
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
    (r"^Enveloping-surface sound power \(ISO 3744\)  LWA = (.+) dB\(A\)$",
     r"Potencia sonora por superficie envolvente (ISO 3744)  LWA = \1 dB(A)"),
    (r"^Reverberation-room sound power \(ISO 3741\)  LWA = (.+) dB\(A\)$",
     r"Potencia sonora en cámara reverberante (ISO 3741)  LWA = \1 dB(A)"),
    (r"^Intensity-scanning sound power \(ISO 9614-2\)  LWA = (.+) dB\(A\)$",
     r"Potencia sonora por barrido de intensidad (ISO 9614-2)  LWA = \1 dB(A)"),
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


# Figures kept as PNG because SVG would be strictly heavier, for two reasons:
#   * raster-backed (pcolormesh / specgram): the SVG would only wrap a base64
#     bitmap ~4.5x larger than the PNG;
#   * dense time series (thousands of vertices): every sample becomes a path
#     coordinate, so the SVG runs 5.5-7.75x the PNG (schroeder_decay 105->820 KB,
#     calibration_stability 99->759 KB, impulse_response 134->747 KB).
# Both clear the ~4.5x "SVG no longer wins" bar; everything else is a vector plot
# written as deterministic SVG (moderate 2.4x cases like sel_concept /
# ln_levels_example stay SVG -- below the bar, and vector crispness is worth it).
_PNG_FIGURES = frozenset(
    {
        "spectrogram_example",
        "excitation_signals",
        "schroeder_decay",
        "calibration_stability",
        "impulse_response",
    }
)


def save_figure(output_dir: str, filename: str, **kwargs: Any) -> None:
    """Translate, theme-suffix and save the current figure.

    Vector figures are written as SVG made byte-reproducible with a fixed
    ``svg.hashsalt`` (deterministic element ids), ``svg.fonttype = "none"``
    (text kept as ``<text>`` rather than freetype glyph outlines, so the
    output does not depend on the font build) and no date metadata -- so
    ``make graphs`` is stable and CI can diff it. The figures in
    :data:`_PNG_FIGURES` stay PNG (SVG would be heavier); their metadata is
    stripped too (matplotlib otherwise stamps a version-dependent ``Software``
    chunk), so the PNG bytes are reproducible across matplotlib builds. In both
    cases ``filename`` may carry any extension; the real one is chosen here.
    """
    _translate_figure(plt.gcf())
    stem = os.path.splitext(filename)[0]
    ext = "png" if stem in _PNG_FIGURES else "svg"
    path = os.path.join(output_dir, f"{stem}{_LANG_SUFFIX}{_FILENAME_SUFFIX}.{ext}")
    if ext == "svg":
        plt.rcParams["svg.hashsalt"] = "phonometry"
        plt.rcParams["svg.fonttype"] = "none"
        kwargs.setdefault("metadata", {"Date": None})
    else:
        # Drop matplotlib's version-stamped Software chunk (and any date) so the
        # committed PNGs match a fresh render on any matplotlib build in CI.
        kwargs.setdefault("metadata", {"Software": None, "Date": None})
    plt.savefig(path, **kwargs)



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
    save_figure(output_dir, "filter_type_comparison.png")
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
            # Draw first, then save through save_figure so the Spanish
            # translation pass runs on the finished figure (it rewrites the
            # live figure's text artists right before the save).
            _showfilter(bank.sos, bank.freq, bank.freq_u, bank.freq_d, fs,
                        bank.factor, show=False, plot_file=None, close=False)
            save_figure(output_dir, filename, dpi=150,
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
        save_figure(output_dir, filename)
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
    save_figure(output_dir, "signal_response_multichannel.png")
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
    save_figure(output_dir, "signal_decomposition.png")
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
    save_figure(output_dir, "weighting_responses.png")
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
    save_figure(output_dir, "g_weighting_response.png")
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
    save_figure(output_dir, "equal_loudness_contours.png")
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
    save_figure(output_dir, "time_weighting_analysis.png")
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
    save_figure(output_dir, "crossover_lr4.png")
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
    save_figure(output_dir, "spectrogram_example.png")
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
    save_figure(output_dir, "ln_levels_example.png")
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
    save_figure(output_dir, "zero_phase_comparison.png")
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
    save_figure(output_dir, "weighting_accuracy_hf.png")
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
    save_figure(output_dir, "group_delay_comparison.png")
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
    save_figure(output_dir, "tone_burst_iec.png")
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
    save_figure(output_dir, "block_processing_continuity.png")
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
    save_figure(output_dir, "class_mask_overlay.png")
    plt.close()


def generate_filter_class0_mask(output_dir: str) -> None:
    """Pass-band class 0/1/2 maximum corridors (IEC 61260:1995 / ANSI S1.11-2004)."""
    print("Generating filter_class0_mask...")
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

    # Restrict to the pass-band [G**-1/2, G**+1/2] where a finite max applies
    # (beyond the band edges the maximum limit is +inf, so plotting there would
    # misleadingly show the filter's natural roll-off "exceeding" a corridor).
    g_octave = 10 ** (3 / 10)  # octave ratio G (IEC 61260)
    edge_lo, edge_hi = g_octave ** -0.5, g_octave ** 0.5
    pb = (omega >= edge_lo) & (omega <= edge_hi)
    omega, delta_a = omega[pb], (attenuation - a_ref)[pb]
    grid = np.linspace(edge_lo, edge_hi, 1500)

    _, ax = plt.subplots(figsize=(10, 6.5))
    # Nested min/max corridors: class 0 (+-0.15 dB reference) is the tightest.
    for cls, colour, name in ((2, COLOR_TERTIARY, "Class 2 corridor"),
                              (1, COLOR_SECONDARY, "Class 1 corridor"),
                              (0, COLOR_PRIMARY, "Class 0 corridor")):
        lo, hi = class_limits(1.0, cls, grid, edition="1995")
        ax.plot(grid, hi, color=colour, linewidth=1.4, label=name)
        ax.plot(grid, lo, color=colour, linewidth=1.4)
    ax.plot(omega, delta_a, color=COLOR_FG, linewidth=2.2,
            label="Butterworth order 6 (1 kHz octave band)")

    ax.set_xscale("log")
    ax.set_xlim(edge_lo, edge_hi)
    ax.set_ylim(-0.7, 6)
    ax.set_title("Pass-band Class 0/1/2 Limits (IEC 61260:1995 / ANSI S1.11-2004)",
                 fontweight="bold", pad=12)
    ax.set_xlabel("Normalized frequency  f / fm")
    ax.set_ylabel("Relative attenuation ΔA [dB]")
    ax.set_xticks([0.707, 0.841, 1, 1.189, 1.414])
    ax.set_xticklabels(["0.707", "0.841", "1", "1.189", "1.414"])
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())  # keep only explicit ticks
    ax.grid(which="major", color=COLOR_GRID, linestyle=":", alpha=0.4)
    ax.legend(loc="upper center", fontsize=9)
    save_figure(output_dir, "filter_class0_mask.png")
    plt.close()


def generate_weighting_class_mask(output_dir: str) -> None:
    """A/C weighting deviation against the IEC 61672-1:2013 Table 3 mask."""
    print("Generating weighting_class_mask.png...")
    from phonometry import WeightingFilter, verify_weighting_class, weighting_class_limits

    freqs, lower1, upper1 = weighting_class_limits(1)
    _, lower2, upper2 = weighting_class_limits(2)
    floor, ceil = -7.0, 7.0  # plotting bounds; -inf limits clip to the floor
    lo1 = np.clip(lower1, floor, ceil)
    lo2 = np.clip(lower2, floor, ceil)

    _, ax = plt.subplots(figsize=(10, 6.5))
    # Allowed corridor for class 1 (between lower and upper limit).
    ax.fill_between(freqs, lo1, upper1, color=COLOR_PRIMARY, alpha=0.10,
                    step="mid", label="Class 1 acceptance region")
    ax.plot(freqs, upper1, color=COLOR_SECONDARY, linewidth=1.3, drawstyle="steps-mid",
            label="Class 1 upper/lower limit")
    ax.plot(freqs, lo1, color=COLOR_SECONDARY, linewidth=1.3, drawstyle="steps-mid")
    ax.plot(freqs, upper2, color=COLOR_TERTIARY, linestyle=":", linewidth=1.1,
            drawstyle="steps-mid", label="Class 2 upper/lower limit")
    ax.plot(freqs, lo2, color=COLOR_TERTIARY, linestyle=":", linewidth=1.1,
            drawstyle="steps-mid")

    for curve, colour, marker in (("A", COLOR_PRIMARY, "o"), ("C", "#9467bd", "s")):
        result = verify_weighting_class(WeightingFilter(48000, curve))
        f = np.array([b["freq"] for b in result["bands"]])
        dev = np.array([b["deviation_db"] for b in result["bands"]])
        ax.plot(f, dev, color=colour, linewidth=1.6, marker=marker, markersize=4,
                label=f"{curve} weighting deviation (48 kHz)")

    ax.set_xscale("log")
    ax.set_xlim(10, 20000)
    ax.set_ylim(floor, ceil)
    ax.set_title("Weighting Deviation vs IEC 61672-1:2013 Table 3 Limits",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Deviation from design goal [dB]")
    ax.grid(which="both", color=COLOR_GRID, linestyle=":", alpha=0.4)
    ax.legend(loc="lower center", fontsize=8, ncol=2)
    save_figure(output_dir, "weighting_class_mask.png")
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
    save_figure(output_dir, "calibration_stability.png")
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
    save_figure(output_dir, "sel_concept.png")
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
    save_figure(output_dir, "lden_profile.png")
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
    save_figure(output_dir, "tonality_spectrum.png")
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
    save_figure(output_dir, "loudness_pattern.png")
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
    save_figure(output_dir, "sti_vs_t60.png")
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
    save_figure(output_dir, "intensity_demo.png")
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
    save_figure(output_dir, "schroeder_decay.png")
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
    save_figure(output_dir, "excitation_signals.png")
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
    save_figure(output_dir, "impulse_response.png")
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
    save_figure(output_dir, "insulation_rating.png")
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
    save_figure(output_dir, "impact_rating.png")
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
    save_figure(output_dir, "sharpness_weighting.png")
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
    save_figure(output_dir, "open_plan_decay.png")
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
    save_figure(output_dir, "loudness_models_comparison.png")
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
    save_figure(output_dir, "sottek_specific_loudness.png")
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
    save_figure(output_dir, "tonality_roughness_demo.png")
    plt.close()


@lru_cache(maxsize=None)
def _fluctuation_am_tone_sweep() -> tuple[np.ndarray, np.ndarray]:
    """Osses 2016 signal-model F of a 1 kHz / 70 dB / 100 %-AM tone vs f_mod.

    Cached (language/theme independent): the signal model is run once for the
    modulation-frequency sweep {1, 2, 4, 8, 16, 32} Hz. Reproduces the band-pass
    sensation with its maximum at 4 Hz (Osses 2016 Table 1 trend).
    """
    from phonometry import fluctuation_strength

    dur = 2.0
    t = np.arange(int(dur * _FS_PSY)) / _FS_PSY
    carrier = np.sin(2.0 * np.pi * 1000.0 * t)
    fmods = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 32.0])
    f_vals = []
    for fm in fmods:
        am = (1.0 + np.sin(2.0 * np.pi * fm * t)) * carrier
        am = am / np.sqrt(np.mean(am ** 2)) * _P_REF * 10.0 ** (70.0 / 20.0)
        f_vals.append(fluctuation_strength(am, float(_FS_PSY)).fluctuation_strength)
    return fmods, np.array(f_vals)


def generate_fluctuation_strength(output_dir: str) -> None:
    """Fluctuation strength F vs modulation frequency: the 4 Hz band-pass peak."""
    print("Generating fluctuation_strength...")
    from phonometry import fluctuation_strength_am_noise

    # Exact closed form (Fastl & Zwicker Eq. 10.2) for AM broadband noise at
    # 60 dB, 100 % modulation, swept over f_mod on a log axis.
    fmod = np.logspace(np.log10(0.5), np.log10(32.0), 240)
    f_bbn = np.array([fluctuation_strength_am_noise(60.0, 1.0, fm) for fm in fmod])
    bbn_peak = int(np.argmax(f_bbn))

    # Osses 2016 signal model on an AM tone (70 dB), same modulation sweep.
    fm_tone, f_tone = _fluctuation_am_tone_sweep()
    tone_peak = int(np.argmax(f_tone))

    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.semilogx(fmod, f_bbn, color=COLOR_PRIMARY, linewidth=2.4,
                label=(f"AM broadband noise (closed form, 60 dB), "
                       f"peak {f_bbn[bbn_peak]:.1f} vacil"))
    ax.plot(fmod[bbn_peak], f_bbn[bbn_peak], "o", color=COLOR_PRIMARY,
            markersize=8, markerfacecolor="white", markeredgewidth=1.6, zorder=6)
    ax.axvline(4.0, color=COLOR_FG, linestyle="--", linewidth=1.0, alpha=0.7,
               label="4 Hz reference")
    ax.set_xlabel("Modulation frequency f_mod [Hz]")
    ax.set_ylabel("Fluctuation strength F [vacil]")
    ax.set_ylim(0.0, float(f_bbn.max()) * 1.18)
    ax.set_title("Fluctuation Strength — 4 Hz Band-Pass Characteristic",
                 fontweight="bold", pad=12)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_formatter(mticker.ScalarFormatter())
    ax.set_xticks([0.5, 1, 2, 4, 8, 16, 32])
    ax.set_xticklabels(["0.5", "1", "2", "4", "8", "16", "32"])

    # Overlay the signal-model AM-tone sweep on a secondary axis (its absolute
    # scale differs from the broadband closed form, but the band-pass shape and
    # 4 Hz maximum coincide).
    ax2 = ax.twinx()
    ax2.plot(fm_tone, f_tone, "s--", color=COLOR_TERTIARY, linewidth=1.8,
             markersize=7, label=(f"AM tone (signal model, 70 dB), "
                                  f"peak {f_tone[tone_peak]:.2f} vacil"))
    ax2.set_ylabel("AM-tone F, signal model [vacil]", color=COLOR_TERTIARY)
    ax2.tick_params(axis="y", labelcolor=COLOR_TERTIARY)
    ax2.set_ylim(0.0, float(f_tone.max()) * 1.18)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "F = 5.8 (1.25 m - 0.25)(0.05 L - 1)",
        "    / [(fmod/5)^2 + 4/fmod + 1.5]  vacil",
    ]
    ax.text(0.015, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=8.5, color=COLOR_FG,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "fluctuation_strength.svg")
    plt.close()


def generate_psychoacoustic_annoyance(output_dir: str) -> None:
    """Psychoacoustic annoyance PA vs loudness N5 for three sensation profiles."""
    print("Generating psychoacoustic_annoyance...")
    from phonometry import psychoacoustic_annoyance

    n5 = np.linspace(4.0, 60.0, 200)
    # (label, sharpness [acum], fluctuation strength [vacil], roughness [asper],
    #  colour, linestyle).
    profiles = [
        ("Baseline: S = 1.75 acum, F = R = 0", 1.75, 0.0, 0.0,
         COLOR_FG, "--"),
        ("Sharp: S = 3.5 acum", 3.5, 0.0, 0.0, COLOR_PRIMARY, "-"),
        ("Rough + fluctuating: F = 1.2 vacil, R = 0.7 asper", 2.0, 1.2, 0.7,
         COLOR_TERTIARY, "-"),
    ]

    fig, ax = plt.subplots(figsize=(10, 6.2))
    for label, s, f, r, color, ls in profiles:
        pa = np.array([psychoacoustic_annoyance(v, s, f, r).annoyance for v in n5])
        lw = 1.6 if ls == "--" else 2.4
        alpha = 0.7 if ls == "--" else 1.0
        ax.plot(n5, pa, color=color, linestyle=ls, linewidth=lw, alpha=alpha,
                label=label)

    # Worked example: N5 = 30 sone, S = 2.0 acum, F = 0.5 vacil, R = 0.3 asper.
    ex = psychoacoustic_annoyance(30.0, 2.0, 0.5, 0.3)
    ax.plot([30.0], [ex.annoyance], "o", color=COLOR_SECONDARY, markersize=10,
            markerfacecolor="white", markeredgewidth=2.0, zorder=6,
            label=f"Worked example (PA = {ex.annoyance:.2f})")
    ax.annotate(f"PA = {ex.annoyance:.2f}\nwS = {ex.w_s:.3f}, wFR = {ex.w_fr:.3f}",
                xy=(30.0, ex.annoyance), xytext=(33.0, ex.annoyance * 0.72),
                fontsize=9, color=COLOR_FG,
                arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_FG})

    ax.set_xlabel("Percentile loudness N5 [sone]")
    ax.set_ylabel("Psychoacoustic annoyance PA")
    ax.set_xlim(0.0, 62.0)
    ax.set_ylim(0.0, None)
    ax.set_title("Psychoacoustic Annoyance vs Loudness (Fastl & Zwicker)",
                 fontweight="bold", pad=12)
    ax.grid(which="major", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "PA = N5 sqrt(1 + wS^2 + wFR^2)",
        "wS  = (S - 1.75) 0.25 lg(N5 + 10)",
        "wFR = (2.18 / N5^0.4)(0.4 F + 0.6 R)",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=8.5, color=COLOR_FG,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "psychoacoustic_annoyance.svg")
    plt.close()


_FS_ELECTRO = 48000  # audio sample rate for the electroacoustic demos


def generate_distortion(output_dir: str) -> None:
    """Annotated harmonic spectrum with the THD of a synthetic amplifier output."""
    print("Generating distortion...")
    from phonometry import harmonic_analysis

    fs = _FS_ELECTRO
    n = fs  # 1 s -> 1 Hz bins; every harmonic lands on a bin
    t = np.arange(n) / fs
    f0 = 1000.0
    # A 1 kHz fundamental with a decaying harmonic series over a broadband
    # noise floor, the kind of output an amplifier under a single-tone test
    # produces. The noise makes THD+N exceed the harmonic-only THD (it also
    # counts the noise), while SINAD reports the noise-and-distortion headroom.
    amps = {1: 1.0, 2: 0.02, 3: 0.012, 4: 0.006, 5: 0.003}
    sig = sum(a * np.sin(2 * np.pi * k * f0 * t) for k, a in amps.items())
    rng = np.random.default_rng(2026)
    sig = sig + rng.standard_normal(n) * 1.2e-2

    res = harmonic_analysis(sig, fs, f0, n_harmonics=len(amps))

    # Magnitude spectrum (coherent-gain normalised) in dB re the fundamental.
    window = np.hanning(n)
    spectrum = np.abs(np.fft.rfft(sig * window)) * 2.0 / np.sum(window)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    ref = np.max(spectrum)
    spec_db = 20.0 * np.log10(np.maximum(spectrum, 1e-12) / ref)

    fig, ax = plt.subplots(figsize=(10, 6.0))
    ax.plot(freqs, spec_db, color=COLOR_PRIMARY, linewidth=1.0, alpha=0.8,
            label="Magnitude spectrum")
    hz = np.asarray(res.harmonic_frequencies)
    ha = np.asarray(res.harmonic_amplitudes)
    hdb = 20.0 * np.log10(np.maximum(ha, 1e-12) / ha[0])
    ax.plot(hz, hdb, "o", color=COLOR_SECONDARY, markersize=7, zorder=6,
            label="Harmonics n·f₁")
    for k, (fk, lk) in enumerate(zip(hz, hdb), start=1):
        ax.annotate(f"n={k}", xy=(fk, lk), xytext=(0, 7),
                    textcoords="offset points", ha="center", fontsize=8,
                    color=COLOR_FG)

    ax.set_xlim(0.0, 9000.0)
    ax.set_ylim(-100.0, 8.0)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Level re fundamental [dB]")
    ax.set_title("Harmonic Distortion of a Single-Tone Test (IEC 60268-3)",
                 fontweight="bold", pad=12)
    ax.grid(which="major", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        f"THD (F) = {res.thd_f * 100:.2f}%",
        f"THD (R) = {res.thd_r * 100:.2f}%",
        f"THD+N   = {res.thd_plus_noise * 100:.2f}%",
        f"SINAD   = {res.sinad_db:.1f} dB",
    ]
    ax.text(0.015, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=9, color=COLOR_FG,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "distortion.svg")
    plt.close()


def generate_frequency_response(output_dir: str) -> None:
    """Bode magnitude and coherence of an estimated frequency response (H1)."""
    print("Generating frequency_response...")
    from scipy import signal as sp_signal

    from phonometry import transfer_function

    fs = _FS_ELECTRO
    n = 400000
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n)
    # A resonant second-order band-pass "device under test".
    b, a = sp_signal.butter(2, [400.0, 4000.0], btype="band", fs=fs)
    y = sp_signal.lfilter(b, a, x)
    # Additive output noise pulls the coherence down where the signal is weak.
    y = y + rng.standard_normal(n) * np.sqrt(np.mean(y**2)) * 0.05

    res = transfer_function(x, y, fs, estimator="H1")
    _, h_true = sp_signal.freqz(b, a, worN=res.frequencies, fs=fs)
    pos = res.frequencies > 0.0
    freqs = res.frequencies[pos]
    true_db = 20.0 * np.log10(np.maximum(np.abs(h_true[pos]), 1e-12))

    fig, (ax_mag, ax_coh) = plt.subplots(
        2, 1, figsize=(10, 7.2), sharex=True,
        gridspec_kw={"height_ratios": [2.0, 1.0]})
    ax_mag.semilogx(freqs, true_db, color=COLOR_FG, linestyle="--",
                    linewidth=1.6, alpha=0.7, label="True |H|")
    ax_mag.semilogx(freqs, res.magnitude_db[pos], color=COLOR_PRIMARY,
                    linewidth=1.8, label="Estimated |H| (H1)")
    ax_mag.set_ylabel("Magnitude [dB]")
    ax_mag.set_ylim(-80.0, 5.0)
    ax_mag.set_title("Frequency Response and Coherence (Bendat & Piersol)",
                     fontweight="bold", pad=12)
    ax_mag.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_mag.set_axisbelow(True)
    ax_mag.legend(loc="lower center", fontsize=9)

    ax_coh.semilogx(freqs, res.coherence[pos], color=COLOR_TERTIARY,
                    linewidth=1.8)
    ax_coh.set_ylabel(r"Coherence $\gamma^2$")
    ax_coh.set_xlabel("Frequency [Hz]")
    ax_coh.set_ylim(0.0, 1.05)
    ax_coh.set_xlim(20.0, fs / 2.0)
    ax_coh.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_coh.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "frequency_response.svg")
    plt.close()


def generate_ship_source_level(output_dir: str) -> None:
    """Ship equivalent monopole source level and the ΔL surface correction."""
    print("Generating ship_source_level...")
    from phonometry import monopole_source_level

    # One-third-octave centres 20 Hz-20 kHz and a plausible broadband ship RNL
    # that rolls off with frequency; draught 6 m -> source depth 4.2 m.
    freqs = np.array([20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315,
                      400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150,
                      4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000],
                     dtype=float)
    rnl = 175.0 - 12.0 * np.log10(freqs / 20.0)
    res = monopole_source_level(rnl, freqs, draught=6.0)

    fig, ax = plt.subplots(figsize=(10, 6.0))
    ax.semilogx(freqs, res.source_level, "o-", color=COLOR_PRIMARY, linewidth=2.0,
                markersize=4, label="Source level Ls")
    ax.semilogx(freqs, res.radiated_noise_level, "s--", color=COLOR_SECONDARY,
                linewidth=1.6, markersize=3, alpha=0.8, label="Radiated noise level")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Level [dB re 1 µPa·m]")
    ax.set_title("Ship Equivalent Monopole Source Level (ISO 17208-2)",
                 fontweight="bold", pad=12)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    twin = ax.twinx()
    twin.semilogx(freqs, res.surface_correction, ":", color=COLOR_TERTIARY,
                  linewidth=2.0, label="Surface correction ΔL")
    twin.set_ylabel("Surface correction ΔL [dB]")

    lines, labels = ax.get_legend_handles_labels()
    tlines, tlabels = twin.get_legend_handles_labels()
    ax.legend(lines + tlines, labels + tlabels, loc="lower left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "Ls = LRN + ΔL",
        "ΔL = -10 lg[(2u^4+14u^2)/(14+2u^2+u^4)]",
        "u = k d_s,  d_s = 0.7 D = 4.2 m",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=8.5, color=COLOR_FG,
            family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "ship_source_level.svg")
    plt.close()


def generate_pile_driving(output_dir: str) -> None:
    """Pile-driving strike waveform, single-strike SEL and cumulative-SEL growth."""
    print("Generating pile_driving...")
    from phonometry import cumulative_sel_identical, pile_strike_metrics

    fs = 48000
    dur = 0.3
    t = np.arange(int(dur * fs)) / fs
    # An impulsive strike: a short rise then an exponentially decaying ring.
    envelope = np.where(t < 0.01, t / 0.01, np.exp(-(t - 0.01) / 0.04))
    pressure = 8000.0 * envelope * np.sin(2.0 * np.pi * 180.0 * t)
    res = pile_strike_metrics(pressure, fs)

    # Cumulative SEL growth over a driving sequence of identical strikes.
    strikes = np.arange(1, 2001)
    sel_cum = np.array([cumulative_sel_identical(res.single_strike_sel, int(n))
                        for n in strikes])

    fig, (ax_w, ax_c) = plt.subplots(
        2, 1, figsize=(10, 7.2),
        gridspec_kw={"height_ratios": [1.4, 1.0]})
    ax_w.plot(t * 1e3, pressure, color=COLOR_PRIMARY, linewidth=0.8)
    peak_idx = int(np.argmax(np.abs(pressure)))
    ax_w.plot([t[peak_idx] * 1e3], [pressure[peak_idx]], "o", color=COLOR_SECONDARY,
              markersize=8, label=f"Peak = {res.peak_spl:.0f} dB re 1 µPa")
    ax_w.set_xlabel("Time [ms]")
    ax_w.set_ylabel("Pressure [Pa]")
    ax_w.set_title("Percussive Pile-Driving Strike (ISO 18406)",
                   fontweight="bold", pad=12)
    ax_w.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_w.set_axisbelow(True)
    ax_w.legend(loc="upper right", fontsize=9)

    ax_c.semilogx(strikes, sel_cum, color=COLOR_TERTIARY, linewidth=2.2)
    ax_c.set_xlabel("Number of strikes N")
    ax_c.set_ylabel("Cumulative SEL [dB re 1 µPa²·s]")
    ax_c.set_title(
        f"SEL_ss = {res.single_strike_sel:.0f} dB;  "
        f"SEL_cum = SEL_ss + 10 lg(N)", fontsize=10)
    ax_c.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_c.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "pile_driving.svg")
    plt.close()


def generate_epnl(output_dir: str) -> None:
    """ICAO aircraft-flyover EPNL: PNL/PNLT time history with the 10 dB-down window."""
    print("Generating epnl...")
    from phonometry import NOY_BANDS, effective_perceived_noise_level

    k = 41
    dt = 0.5
    idx = np.arange(k)
    # Broadband flyover spectrum with a mid-frequency emphasis, modulated by a
    # Gaussian overall-level envelope; a fan tone in the 2500 Hz band adds a
    # tone correction near the closest-point-of-approach.
    shape = 15.0 * np.exp(-((np.log10(NOY_BANDS) - np.log10(400.0)) ** 2) / 0.5)
    gain = 30.0 * np.exp(-((idx - 20.0) ** 2) / (2 * 5.0**2)) - 5.0
    spectra = (55.0 + shape)[None, :] + gain[:, None]
    spectra[:, 17] += 12.0 * np.exp(-((idx - 20.0) ** 2) / (2 * 6.0**2))
    res = effective_perceived_noise_level(spectra, dt)
    kf, kl = res.band_limits

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axvspan(res.times[kf], res.times[kl], color=COLOR_TERTIARY, alpha=0.15,
               label="10 dB-down window")
    ax.plot(res.times, res.pnl, color="#8c8c8c", linestyle="--", linewidth=1.4,
            label="PNL")
    ax.plot(res.times, res.pnlt, color=COLOR_PRIMARY, linewidth=2.2, label="PNLT")
    km = int(np.argmax(res.pnlt))
    ax.plot([res.times[km]], [res.pnltm], "o", color=COLOR_SECONDARY, markersize=9,
            label=f"PNLTM = {res.pnltm:.1f} PNdB")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Level [PNdB]")
    ax.set_title(
        "ICAO Aircraft Flyover — Effective Perceived Noise Level (Annex 16)",
        fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    ax.text(0.02, 0.95,
            f"EPNL = {res.epnl:.1f} EPNdB\nD = {res.duration_correction:+.1f} dB",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox={"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6})
    plt.tight_layout()
    save_figure(output_dir, "epnl.svg")
    plt.close()


def generate_wind_turbine_tonality(output_dir: str) -> None:
    """IEC 61400-11 wind-turbine tonal audibility: narrowband spectrum + masking."""
    print("Generating wind_turbine_tonality...")
    from phonometry import wind_turbine_tonality
    from phonometry.wind_turbine_noise import _critical_band_edges

    # A narrowband spectrum: a shaped broadband floor with a blade-passing-style
    # tone near 200 Hz, at 2 Hz resolution.
    df = 2.0
    freqs = np.arange(50.0, 400.0 + df, df)
    floor = 42.0 - 6.0 * np.log10(freqs / 100.0)
    tone_bin = int(np.argmin(np.abs(freqs - 200.0)))
    levels = floor.copy()
    levels[tone_bin] += 22.0
    res = wind_turbine_tonality(levels, freqs, tone_frequency=200.0)

    fig, ax = plt.subplots(figsize=(10, 6))
    band_lo, band_hi = _critical_band_edges(res.tone_frequency)
    ax.axvspan(band_lo, band_hi, color=COLOR_TERTIARY, alpha=0.15,
               label="Critical band")
    ax.plot(freqs, levels, color=COLOR_PRIMARY, linewidth=1.0,
            label="Narrowband spectrum")
    ax.axhline(res.masking_level, color="#ff7f0e", linestyle="--", linewidth=1.5,
               label=f"Masking level = {res.masking_level:.1f} dB")
    ax.plot([res.tone_frequency], [res.tone_level], "o", color=COLOR_SECONDARY,
            markersize=9, label=f"Tone = {res.tone_level:.1f} dB")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Level [dB]")
    ax.set_title("Wind-Turbine Tonal Audibility (IEC 61400-11)",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    ax.text(0.02, 0.95,
            f"Tonal audibility ΔLₐ = {res.tonal_audibility:.1f} dB\n"
            f"{'audible' if res.is_audible else 'not audible'}",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox={"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6})
    plt.tight_layout()
    save_figure(output_dir, "wind_turbine_tonality.svg")
    plt.close()


def generate_underwater_transmission_loss(output_dir: str) -> None:
    """Underwater TL vs range: geometrical spreading + volume absorption."""
    print("Generating underwater_transmission_loss...")
    from phonometry import transmission_loss

    ranges = np.linspace(10.0, 20_000.0, 400)
    res = transmission_loss(
        ranges, 10_000.0, law="practical", transition_range=1000.0,
        temperature=10.0, salinity=35.0, depth=100.0, model="francois-garrison",
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(res.range_m, res.tl, color=COLOR_PRIMARY, linewidth=2.0,
            label="Total transmission loss")
    ax.plot(res.range_m, res.spreading, color="#8c8c8c", linestyle="--", linewidth=1.4,
            label="Geometrical spreading")
    ax.plot(res.range_m, res.absorption, color=COLOR_SECONDARY, linestyle=":", linewidth=1.6,
            label="Volume absorption")
    ax.set_xlabel("Range [m]")
    ax.set_ylabel("Transmission loss [dB]")
    ax.set_title("Underwater Transmission Loss (Francois–Garrison)",
                 fontweight="bold", pad=12)
    ax.invert_yaxis()
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9)
    ax.text(0.02, 0.05,
            f"f = 10 kHz, α = {res.absorption_coefficient:.2f} dB/km\n"
            "practical spreading (R₀ = 1000 m)",
            transform=ax.transAxes, va="bottom", fontsize=10,
            bbox={"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6})
    plt.tight_layout()
    save_figure(output_dir, "underwater_transmission_loss.svg")
    plt.close()


def generate_underwater_sound_speed(output_dir: str) -> None:
    """Sea-water sound-speed profile (UNESCO): mixed layer, thermocline, deep channel."""
    print("Generating underwater_sound_speed...")
    from phonometry import sound_speed_profile

    depths = np.linspace(0.0, 3000.0, 121)
    # A warm mixed layer (18 °C to 80 m), a thermocline down to 4 °C at 1000 m,
    # then an isothermal deep layer; the pressure term then lifts c with depth.
    temps = 4.0 + 14.0 / (1.0 + (np.maximum(depths - 80.0, 0.0) / 250.0) ** 2)
    prof = sound_speed_profile(depths, temps, 35.0, model="unesco")
    axis_depth = depths[int(np.argmin(prof.sound_speed))]
    fig, ax = plt.subplots(figsize=(7, 8))
    ax.plot(prof.sound_speed, prof.depth, color=COLOR_PRIMARY, linewidth=2.0,
            label="UNESCO sound speed")
    ax.axhline(axis_depth, color=COLOR_SECONDARY, linestyle="--", linewidth=1.4,
               label="Sound-channel axis")
    ax.set_xlabel("Sound speed [m/s]")
    ax.set_ylabel("Depth [m]")
    ax.set_title("Sea-Water Sound-Speed Profile (UNESCO)",
                 fontweight="bold", pad=12)
    ax.invert_yaxis()
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=9)
    plt.tight_layout()
    save_figure(output_dir, "underwater_sound_speed.svg")
    plt.close()


def generate_sonar_equation(output_dir: str) -> None:
    """Passive sonar equation: signal excess vs transmission loss."""
    print("Generating sonar_equation...")
    from phonometry import passive_sonar_equation

    tl = np.linspace(40.0, 120.0, 400)
    res = passive_sonar_equation(140.0, tl, 60.0, directivity_index=15.0,
                                 detection_threshold=8.0)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(res.transmission_loss, res.signal_excess, color=COLOR_PRIMARY, linewidth=2.0,
            label="Signal excess")
    ax.axhline(0.0, color=COLOR_SECONDARY, linestyle="--", linewidth=1.4,
               label="Detection limit (SE = 0)")
    ax.axvline(res.figure_of_merit, color="#8c8c8c", linestyle=":", linewidth=1.6,
               label="Figure of merit")
    ax.set_xlabel("Transmission loss [dB]")
    ax.set_ylabel("Signal excess [dB]")
    ax.set_title("Passive Sonar Equation", fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    ax.text(0.02, 0.05,
            f"SL = 140, NL = 60, DI = 15, DT = 8 dB\n"
            f"figure of merit = {res.figure_of_merit:.1f} dB",
            transform=ax.transAxes, va="bottom", fontsize=10,
            bbox={"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6})
    plt.tight_layout()
    save_figure(output_dir, "sonar_equation.svg")
    plt.close()


def generate_seabed_reflection(output_dir: str) -> None:
    """Seabed reflection loss vs grazing angle, marking the critical angle."""
    print("Generating seabed_reflection...")
    from phonometry import bottom_reflection_loss

    phi = np.linspace(0.0, 90.0, 361)
    res = bottom_reflection_loss(phi, rho1=1000.0, c1=1500.0, rho2=1900.0, c2=1650.0)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(res.grazing_angle, res.reflection_loss, color=COLOR_PRIMARY, linewidth=2.0,
            label="Bottom loss (sand)")
    if res.critical_angle is not None:
        ax.axvline(res.critical_angle, color=COLOR_SECONDARY, linestyle="--", linewidth=1.4,
                   label=f"Critical angle ({res.critical_angle:.1f}°)")
    ax.set_xlabel("Grazing angle [°]")
    ax.set_ylabel("Bottom loss [dB]")
    ax.set_title("Seabed Reflection Loss (Rayleigh)", fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    ax.text(0.02, 0.95,
            "Water ρ = 1000, c = 1500\nSand ρ = 1900, c = 1650",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox={"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6})
    plt.tight_layout()
    save_figure(output_dir, "seabed_reflection.svg")
    plt.close()


def generate_ocean_ambient_noise(output_dir: str) -> None:
    """Wenz ambient-noise curves: wind + thermal energy sum vs frequency."""
    print("Generating ocean_ambient_noise...")
    from phonometry import ocean_ambient_noise

    freqs = np.logspace(2, 5.5, 300)
    fig, ax = plt.subplots(figsize=(10, 6))
    # Label the wind/thermal components only once to avoid repeated legend rows.
    for i, (u, color) in enumerate(((5.0, COLOR_SECONDARY), (20.0, COLOR_PRIMARY))):
        res = ocean_ambient_noise(freqs, wind_speed_knots=u)
        _plot_ambient_curve(res, u, color, label_components=(i == 0))
    ax.set_xscale("log")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Spectrum level [dB re 1 µPa²/Hz]")
    ax.set_title("Ocean Ambient Noise (Wenz)", fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    save_figure(output_dir, "ocean_ambient_noise.svg")
    plt.close()


def _plot_ambient_curve(res: object, wind_speed: float, color: str,
                        label_components: bool = False) -> None:
    ax = plt.gca()
    ax.plot(res.frequency, res.spectrum_level, color=color, linewidth=2.0,  # type: ignore[attr-defined]
            label=f"Total ({wind_speed:.0f} kn)")
    ax.plot(res.frequency, res.wind, color=color, linewidth=1.0, linestyle="--", alpha=0.6,  # type: ignore[attr-defined]
            label="Wind" if label_components else None)
    ax.plot(res.frequency, res.thermal, color="#8c8c8c", linewidth=1.0, linestyle=":", alpha=0.8,  # type: ignore[attr-defined]
            label="Thermal" if label_components else None)


def generate_ship_traffic_noise(output_dir: str) -> None:
    """JOMOPANS-ECHO ship source-level spectra for three vessel classes."""
    print("Generating ship_traffic_noise...")
    from phonometry import ship_source_spectrum

    fig, ax = plt.subplots(figsize=(10, 6))
    cases = (
        ("containership", 18.0, 300.0, COLOR_PRIMARY),
        ("cruise", 17.1, 250.0, COLOR_SECONDARY),
        ("tug", 3.7, 30.0, "#8c8c8c"),
    )
    for vessel_class, speed, length, color in cases:
        s = ship_source_spectrum(speed, length, vessel_class=vessel_class)
        ax.plot(s.frequency, s.source_psd, color=color, linewidth=2.0,
                label=f"{vessel_class} ({speed:.0f} kn, {length:.0f} m)")
    ax.set_xscale("log")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Source spectral density [dB re 1 µPa²/Hz at 1 m]")
    ax.set_title("Ship Traffic Source Level (JOMOPANS-ECHO)", fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    save_figure(output_dir, "ship_traffic_noise.svg")
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
    save_figure(output_dir, "moore_glasberg_time_loudness.png")
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
    save_figure(output_dir, "prediction_flanking_demo.png")
    plt.close()


def generate_facade_prediction(output_dir: str) -> None:
    """EN 12354-3 façade airborne insulation prediction (Annex F worked example)."""
    print("Generating facade_prediction.png...")
    from phonometry import FacadeElement, facade_sound_reduction

    bands = [125.0, 250.0, 500.0, 1000.0, 2000.0]
    # Annex F elements: double wall, two windows (area, R) + a small air inlet (Dn,e).
    elements = [
        FacadeElement(name="wall", area=6.0, r=[41, 46, 52, 58, 64]),
        FacadeElement(name="window", area=4.5, r=[23, 22, 30, 36, 37]),
        FacadeElement(name="skylight", area=0.5, r=[24, 27, 30, 33, 30]),
        FacadeElement(name="air inlet", dn_e=[28, 23, 25, 38, 44]),
    ]
    result = facade_sound_reduction(
        elements, area=11.3, volume=50.0, frequencies=bands, bands="octave"
    )

    x = np.arange(len(bands))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    # Per-element partial indices Rp: thin, faded — they set the transmission floor.
    el_colors = [COLOR_PRIMARY, COLOR_SECONDARY, "#9467bd", "#ff7f0e"]
    for (name, rp), colour in zip(result.element_r.items(), el_colors):
        ax.plot(x, rp, "--", color=colour, linewidth=1.1, alpha=0.65,
                marker=".", markersize=6, label=f"Rp — {name}")
    # Façade apparent reduction R' and standardized level difference D2m,nT.
    ax.plot(x, result.r_prime, "-", color=COLOR_FG, linewidth=2.6, marker="o",
            markersize=6, zorder=5, label="R′ (façade)")
    ax.plot(x, result.d_2m_nt, "-", color=COLOR_TERTIARY, linewidth=2.2, marker="s",
            markersize=6, zorder=5, label="D2m,nT")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(b)}" for b in bands])
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Reduction index / level difference [dB]")
    ax.set_title("EN 12354-3 Façade Sound Insulation (Annex F example)",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9, ncol=2)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        f"R′tr,s,w = {result.r_tr_s_w} dB   (Ctr = {result.c_tr})",
        f"D2m,nT,w = {result.d_2m_nt_w} dB",
        "air inlet limits the low bands",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "facade_prediction.png")
    plt.close()


def generate_intensity_insulation(output_dir: str) -> None:
    """ISO 15186-1 intensity SRI and the Kc-modified index RI,M = RI + Kc."""
    print("Generating intensity_insulation...")
    from phonometry import adaptation_term_kc, intensity_sound_reduction

    # 16 one-third-octave bands (100-3150 Hz); reuse the ISO 717-1 Annex C
    # airborne shape as the intensity SRI target (RI,w = 30 dB, a light wall).
    freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
                      1000, 1250, 1600, 2000, 2500, 3150], dtype=float)
    ri = np.array([20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
                   28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5])
    lp1, sm, s = 85.0, 12.0, 10.0
    # Levels that make Formula (7) land on RI, then modify with Kc (Annex B).
    l_in = lp1 - 6.0 - 10.0 * np.log10(sm / s) - ri
    kc = adaptation_term_kc(freqs)
    result = intensity_sound_reduction(
        np.full(16, lp1), l_in, measurement_area=sm, area=s, kc=kc
    )
    assert result.r_i_modified is not None
    assert result.rating is not None and result.rating_modified is not None

    x = np.arange(len(freqs))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    # Shade the Kc adaptation lift between RI and RI,M (largest at low bands).
    ax.fill_between(x, result.r_i, result.r_i_modified, color=COLOR_TERTIARY,
                    alpha=0.18, zorder=0, label="Kc adaptation")
    ax.plot(x, result.r_i, "-", color=COLOR_PRIMARY, linewidth=2.6, marker="o",
            markersize=6, zorder=5, label="RI (intensity)")
    ax.plot(x, result.r_i_modified, "--", color=COLOR_TERTIARY, linewidth=2.2,
            marker="s", markersize=6, zorder=5, label="RI,M = RI + Kc")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(f)}" for f in freqs], rotation=45, ha="right",
                       fontsize=8)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound reduction index [dB]")
    ax.set_title("ISO 15186-1 Intensity Sound Reduction Index (RI and RI,M)",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    # Data-only info box (language-neutral); the Kc lift is explained by the
    # shaded "Kc adaptation" legend entry, which the ES translator handles.
    info = [
        f"RI,w = {result.rating.rating} dB",
        f"RI,M,w = {result.rating_modified.rating} dB",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "intensity_insulation.png")
    plt.close()


def generate_survey_insulation(output_dir: str) -> None:
    """ISO 10052 survey method: the reverberation-index correction D -> DnT."""
    print("Generating survey_insulation...")
    from phonometry import reverberation_index, survey_airborne_insulation

    bands = [125.0, 250.0, 500.0, 1000.0, 2000.0]
    # A masonry partition: raw level difference D and the measured receiving-
    # room reverberation time T per octave band.
    l1 = np.array([88.0, 90.0, 92.0, 92.0, 90.0])
    l2 = np.array([55.0, 51.0, 47.0, 41.0, 35.0])
    t = np.array([0.7, 0.6, 0.5, 0.45, 0.4])
    k = reverberation_index(t)
    res = survey_airborne_insulation(l1, l2, k, volume=50.0)
    assert res.rating is not None

    x = np.arange(len(bands))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    # Shade the reverberation-index correction k between D and DnT.
    ax.fill_between(x, res.d, res.d_nt, color=COLOR_TERTIARY, alpha=0.18,
                    zorder=0, label="k = 10 lg(T/T0)")
    ax.plot(x, res.d, "--", color=COLOR_PRIMARY, linewidth=1.8, marker="o",
            markersize=6, zorder=5, label="D (level difference)")
    ax.plot(x, res.d_nt, "-", color=COLOR_FG, linewidth=2.6, marker="s",
            markersize=6, zorder=5, label="DnT (standardized)")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(b)}" for b in bands])
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Level difference [dB]")
    ax.set_title("ISO 10052 Survey Method: Reverberation-Index Correction",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        f"DnT,w = {res.rating.rating} dB  (C = {res.rating.c})",
        "octave bands, T0 = 0.5 s",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "survey_insulation.png")
    plt.close()


def generate_floor_covering_improvement(output_dir: str) -> None:
    """ISO 16251-1 floor-covering impact-sound improvement spectrum ΔL with ΔLw."""
    print("Generating floor_covering_improvement...")
    from phonometry import impact_improvement

    freqs = [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0,
             630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0]
    # A soft carpet: acceleration levels on the bare plate and with the covering.
    bare = np.full(16, 78.0)
    covering = bare - np.array([0, 0, 1, 2, 4, 7, 11, 15, 18, 21,
                                23, 25, 27, 28, 29, 30], dtype=float)
    res = impact_improvement(bare, covering, freqs)
    assert res.delta_lw is not None

    x = np.arange(len(freqs))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.fill_between(x, 0.0, res.improvement, color=COLOR_TERTIARY, alpha=0.18,
                    zorder=0)
    ax.plot(x, res.improvement, "-", color=COLOR_PRIMARY, linewidth=2.4,
            marker="o", markersize=6, zorder=5, label="delta-L (improvement)")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(b)}" for b in freqs], rotation=45, fontsize=8)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Improvement of impact sound insulation [dB]")
    ax.set_ylim(bottom=0.0)
    ax.set_title("ISO 16251-1 Floor-Covering Impact Sound Improvement",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        f"delta-Lw = {res.delta_lw} dB  (ISO 717-2)",
        "one-third octave, mock-up (a0 = 1e-6 m/s^2)",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "floor_covering_improvement.png")
    plt.close()


def generate_flanking_transmission(output_dir: str) -> None:
    """ISO 10848 vibration reduction index Kij per band with the mean K̄ij."""
    print("Generating flanking_transmission...")
    from phonometry import vibration_reduction_index

    freqs = [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0,
             800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0]
    # A rigid T-junction of two heavy walls: measured direction-averaged velocity
    # level difference rising gently with frequency (typical laboratory data).
    dv = np.array([4.5, 4.8, 5.2, 5.6, 6.0, 6.5, 7.0, 7.6, 8.1, 8.7, 9.2, 9.8,
                   10.3, 10.9, 11.4, 11.9, 12.3, 12.7])
    res = vibration_reduction_index(
        dv, junction_length=4.0, area_i=12.0, area_j=10.0,
        frequency=freqs,
        structural_reverberation_time_i=0.35,
        structural_reverberation_time_j=0.40,
    )
    assert res.single_number is not None

    x = np.arange(len(freqs))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.plot(x, res.k_ij, "-", color=COLOR_PRIMARY, linewidth=2.4, marker="o",
            markersize=6, zorder=5, label="Kij (ISO 10848)")
    ax.axhline(res.single_number, color=COLOR_SECONDARY, linestyle="--",
               linewidth=1.6, zorder=4, label="mean Kij (200-1250 Hz)")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(b)}" for b in freqs], rotation=45, fontsize=8)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Vibration reduction index Kij [dB]")
    ax.set_title("ISO 10848 Junction Vibration Reduction Index",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "rigid T-junction, two heavy walls",
        "lij = 4 m, Si = 12 m^2, Sj = 10 m^2",
        "Formula (13), one-third octave",
        f"mean Kij = {res.single_number:.1f} dB",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "flanking_transmission.png")
    plt.close()


def generate_reverberation_models(output_dir: str) -> None:
    """Sabine/Eyring/Millington/Fitzroy/Arau reverberation time over octaves."""
    print("Generating reverberation_models...")
    from phonometry import air_attenuation_m, reverberation_time_models

    bands = [125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]
    # A 10 x 7 x 3.5 m room (V = 245 m3, S = 259 m2) with a strongly anisotropic
    # absorption distribution: a very absorptive floor/ceiling pair (carpet plus
    # an acoustic ceiling) against hard end walls and lightly treated side walls.
    # This is where the axial models (Fitzroy, Arau-Puchades) part company with
    # the isotropic Sabine and Eyring estimates.
    alpha_x = [0.06, 0.07, 0.08, 0.09, 0.10, 0.10]   # hard end walls
    alpha_y = [0.12, 0.14, 0.16, 0.18, 0.20, 0.20]   # lightly treated side walls
    alpha_z = [0.30, 0.50, 0.65, 0.78, 0.82, 0.80]   # carpet + acoustic ceiling
    m = air_attenuation_m(bands, 20.0, 50.0)
    res = reverberation_time_models(
        (10.0, 7.0, 3.5), (alpha_x, alpha_y, alpha_z),
        air_attenuation=m, frequencies=bands,
    )

    x = np.arange(len(bands))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    styles = [
        ("Sabine", res.sabine, COLOR_SECONDARY, "s", 1.8),
        ("Eyring", res.eyring, COLOR_TERTIARY, "^", 1.8),
        ("Millington-Sette", res.millington_sette, "#9467bd", "v", 1.8),
        ("Fitzroy", res.fitzroy, "#ff7f0e", "D", 1.8),
        ("Arau-Puchades", res.arau_puchades, COLOR_PRIMARY, "o", 2.6),
    ]
    for label, curve, color, marker, lw in styles:
        ax.plot(x, curve, color=color, linewidth=lw, marker=marker,
                markersize=6, label=label, zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(b)}" for b in bands])
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel(r"Reverberation time $T$ [s]")
    ax.set_title("Reverberation-time prediction models", fontweight="bold", pad=12)
    ax.set_ylim(bottom=0.0)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "room 10 x 7 x 3.5 m",
        "V = 245 m^3, S = 259 m^2",
        "anisotropic: absorptive floor/ceiling",
        "c0 = 343 m/s, air at 20 C / 50 % RH",
    ]
    ax.text(0.015, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "reverberation_models.svg")
    plt.close()


def generate_dynamic_stiffness(output_dir: str) -> None:
    """EN 29052-1 floating-floor natural frequency f0(s') for typical floors."""
    print("Generating dynamic_stiffness...")
    from phonometry import natural_frequency

    s_mn = np.logspace(np.log10(2.0), np.log10(100.0), 300)   # MN/m3
    fig, ax = plt.subplots(figsize=(10, 6.2))
    # Two typical floating-floor masses per unit area (light vs heavy screed).
    for m, color, label in ((40.0, COLOR_SECONDARY, "m' = 40 kg/m^2"),
                             (120.0, COLOR_PRIMARY, "m' = 120 kg/m^2")):
        f0 = np.asarray(natural_frequency(s_mn * 1e6, m), dtype=float)
        ax.plot(s_mn, f0, color=color, linewidth=2.2, label=label)

    # A worked design point: s' = 10 MN/m3 on the 120 kg/m2 floor.
    s0, m0 = 10.0, 120.0
    f00 = float(natural_frequency(s0 * 1e6, m0))
    ax.scatter([s0], [f00], color=COLOR_TERTIARY, s=90, zorder=6,
               label=f"design point ({s0:g} MN/m^3, {f00:.0f} Hz)")
    ax.plot([s0, s0], [0, f00], color=COLOR_GRID, ls=":", lw=1.0, zorder=1)
    ax.plot([s_mn[0], s0], [f00, f00], color=COLOR_GRID, ls=":", lw=1.0, zorder=1)

    ax.set_xscale("log")
    ax.set_xlabel(r"Dynamic stiffness per unit area $s'$ [MN/m³]")
    ax.set_ylabel(r"Natural frequency $f_0$ [Hz]")
    ax.set_title("EN 29052-1 Floating-Floor Resonance", fontweight="bold", pad=12)
    ax.set_ylim(bottom=0.0)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=10)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "f0 = (1/2pi) sqrt(s'/m')  (Formula 2)",
        "s'  = s't + s'a  (clause 8.2)",
        "s't = 4 pi^2 m't fr^2  (Formula 4)",
        "s'a = p0/(d eps) ~ 111/d MN/m^3  (NOTE)",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=10, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "dynamic_stiffness.svg")
    plt.close()


def generate_mechanical_mobility(output_dir: str) -> None:
    """ISO 7626-1 receptance/mobility/accelerance of a SDOF resonator."""
    print("Generating mechanical_mobility...")
    from phonometry import (
        convert_frf,
        resonance_frequency,
        sdof_receptance,
    )

    m, k, c = 2.0, 8000.0, 5.0
    f0 = resonance_frequency(m, k)
    freq = np.logspace(np.log10(f0 / 20.0), np.log10(f0 * 20.0), 600)
    w0 = 2.0 * np.pi * f0
    h = sdof_receptance(freq, m, k, c)
    y = convert_frf(h, freq, "receptance", "mobility")
    a = convert_frf(h, freq, "receptance", "accelerance")
    # Normalise each FRF to O(1) near resonance so all three share one axis.
    curves = [
        (np.abs(h) * k, COLOR_PRIMARY, "Receptance $|H|$ (× k)"),
        (np.abs(y) * k / w0, COLOR_SECONDARY, r"Mobility $|Y|$ (× k/$\omega_0$)"),
        (np.abs(a) * k / w0**2, COLOR_TERTIARY, r"Accelerance $|A|$ (× k/$\omega_0^2$)"),
    ]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    for mag, color, label in curves:
        ax.loglog(freq, mag, color=color, linewidth=2.0, label=label)
    ax.axvline(f0, color=COLOR_GRID, linestyle="--", linewidth=1.2,
               label="resonance $f_0$")

    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Normalized FRF magnitude")
    ax.set_title("ISO 7626-1 Mechanical Mobility FRFs", fontweight="bold", pad=12)
    ax.set_xlim(freq[0], freq[-1])
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="lower center", fontsize=9, ncol=2)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "SDOF: m = 2 kg, k = 8000 N/m, c = 5 N.s/m",
        "H = 1/(k - w^2 m + j w c)",
        "Y = j w H,   A = -w^2 H  (Table 1)",
        f"f0 = {f0:.1f} Hz,  |Y(f0)| = 1/c",
    ]
    ax.text(0.985, 0.97, "\n".join(info), transform=ax.transAxes,
            va="top", ha="right", fontsize=10, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "mechanical_mobility.svg")
    plt.close()


def generate_transfer_stiffness(output_dir: str) -> None:
    """ISO 10846 dynamic transfer stiffness: true vs indirect-method recovery."""
    print("Generating transfer_stiffness...")
    from phonometry import (
        base_transmissibility,
        transfer_stiffness_indirect,
        transfer_stiffness_level,
    )

    # Kelvin-Voigt isolator k + jwc, loaded by a blocking mass m2.
    k, c, m2 = 1.0e6, 120.0, 8.0
    f0 = np.sqrt(k / m2) / (2.0 * np.pi)
    freq = np.logspace(np.log10(f0 / 5.0), np.log10(f0 * 40.0), 600)
    w = 2.0 * np.pi * freq

    k_true = k + 1j * w * c                                # exact transfer stiffness
    t = base_transmissibility(freq, m2, k, c)              # mass-loaded transmissibility
    k_indirect = transfer_stiffness_indirect(freq, t, m2)  # ISO 10846-3 Eq. (1)

    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.semilogx(freq, transfer_stiffness_level(k_true), color=COLOR_PRIMARY,
                linewidth=2.2, label=r"true $L_k$ of $k_{2,1}=k+j\omega c$")
    ax.semilogx(freq, transfer_stiffness_level(k_indirect), color=COLOR_SECONDARY,
                linewidth=2.0, linestyle="--",
                label=r"indirect method $-(2\pi f)^2 m_2 T$")
    ax.axvline(f0, color=COLOR_GRID, linestyle=":", linewidth=1.2,
               label="resonance $f_0$")
    ax.axvspan(freq[0], 3.0 * f0, color=COLOR_GRID, alpha=0.12)

    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel(r"Transfer stiffness level $L_k$ [dB re 1 N/m]")
    ax.set_title("ISO 10846 Dynamic Transfer Stiffness", fontweight="bold", pad=12)
    ax.set_xlim(freq[0], freq[-1])
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "Kelvin-Voigt: k = 1 MN/m, c = 120 N.s/m",
        f"blocking mass m2 = 8 kg,  f0 = {f0:.1f} Hz",
        "indirect valid for T << 1  (f >> f0)",
        "shaded: T not small -> method invalid",
    ]
    ax.text(0.985, 0.05, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=10, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "transfer_stiffness.svg")
    plt.close()


def generate_vibration_sound_power(output_dir: str) -> None:
    """ISO/TS 7849 sound power from surface vibration: upper limit vs engineering."""
    print("Generating vibration_sound_power...")
    from phonometry import radiated_sound_power_level

    bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
    # A plausible surface velocity level spectrum and a measured radiation factor.
    lv = np.array([78.0, 82.0, 85.0, 83.0, 79.0, 74.0])
    eps = np.array([0.20, 0.45, 0.75, 0.95, 1.00, 1.00])
    area = 1.6

    lw_max = radiated_sound_power_level(lv, area)                    # Part 1, eps=1
    lw_eng = radiated_sound_power_level(lv, area, radiation_factor=eps)  # Part 2

    x = np.arange(bands.size)
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.bar(x - 0.2, lw_max, width=0.4, color=COLOR_SECONDARY, edgecolor=COLOR_FG,
           linewidth=0.6, label="Part 1 upper limit ($\\varepsilon$ = 1)")
    ax.bar(x + 0.2, lw_eng, width=0.4, color=COLOR_PRIMARY, edgecolor=COLOR_FG,
           linewidth=0.6, label="Part 2 engineering ($\\varepsilon$ measured)")

    total_max = 10.0 * np.log10(np.sum(10.0 ** (0.1 * lw_max)))
    total_eng = 10.0 * np.log10(np.sum(10.0 ** (0.1 * lw_eng)))
    ax.axhline(total_max, color=COLOR_SECONDARY, ls="--", lw=1.2,
               label=f"total (limit) {total_max:.1f} dB")
    ax.axhline(total_eng, color=COLOR_PRIMARY, ls="--", lw=1.2,
               label=f"total (eng.) {total_eng:.1f} dB")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{b:g}" for b in bands])
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel(r"Sound power level $L_W$ [dB re 1 pW]")
    ax.set_title("ISO/TS 7849 Sound Power from Surface Vibration",
                 fontweight="bold", pad=12)
    ax.grid(which="major", axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "LW = Lv + 10 lg(S/S0) + 10 lg(e) + 10 lg(411/400)",
        f"S = {area:g} m2,  S0 = 1 m2",
        "Part 1: e = 1 -> upper limit LW,max",
    ]
    ax.text(0.015, 0.02, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=9, color=COLOR_FG, family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "vibration_sound_power.svg")
    plt.close()


def generate_structure_borne_power(output_dir: str) -> None:
    """EN 15657 characteristic structure-borne sound power by reception plate."""
    print("Generating structure_borne_power...")
    from phonometry import reception_plate_power

    bands = np.array([50.0, 100.0, 200.0, 400.0, 800.0, 1600.0, 3150.0])
    # A pump-like source on a low-mobility (heavy) and a high-mobility (light)
    # reception plate; the two determinations should agree within the method.
    lv_low = np.array([88.0, 90.0, 87.0, 84.0, 80.0, 76.0, 71.0])
    lv_high = lv_low + 6.0                      # lighter plate vibrates more
    res_low = reception_plate_power(lv_low, bands, mass_per_area=600.0, area=2.0,
                                    reverberation_time=0.8)
    res_high = reception_plate_power(lv_high, bands, mass_per_area=150.0, area=2.0,
                                     reverberation_time=0.5)

    x = np.arange(bands.size)
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.bar(x - 0.2, res_low.power_level, width=0.4, color=COLOR_PRIMARY,
           edgecolor=COLOR_FG, linewidth=0.6, label="low-mobility plate")
    ax.bar(x + 0.2, res_high.power_level, width=0.4, color=COLOR_SECONDARY,
           edgecolor=COLOR_FG, linewidth=0.6, label="high-mobility plate")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{b:g}" for b in bands])
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel(r"Structure-borne power level $L_{Ws}$ [dB re 1 pW]")
    ax.set_title("EN 15657 Characteristic Structure-Borne Sound Power",
                 fontweight="bold", pad=12)
    ax.grid(which="major", axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "LWs = 10 lg(2 pi f eta m S) + Lv - 60 dB",
        "eta = 2.2/(f Ts),  v0 = 1 nm/s",
        "reception-plate method (clause 7)",
    ]
    ax.text(0.015, 0.02, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=9, color=COLOR_FG, family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "structure_borne_power.svg")
    plt.close()


def generate_installed_structure_borne(output_dir: str) -> None:
    """EN 12354-5 installed structure-borne sound: characteristic power to SPL."""
    print("Generating installed_structure_borne...")
    from phonometry import (
        coupling_term,
        installed_source_prediction,
        installed_structure_borne_power_level,
    )

    bands = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
    lws_c = np.array([78.0, 82.0, 84.0, 81.0, 77.0, 72.0, 66.0])   # EN 15657 source
    # Frequency-dependent source / receiver point mobilities (illustrative).
    ys = (2.0e-4 + 1.0e-4j) * (bands / 250.0)
    yi = (3.0e-5 + 1.0e-5j) * np.ones_like(bands)
    dc = np.array([float(coupling_term(a, b)) for a, b in zip(ys, yi)])
    lws_inst = installed_structure_borne_power_level(lws_c, dc)
    paths = [
        {"adjustment_term": 6.0,
         "flanking_reduction_index": np.array([44., 47., 50., 53., 56., 59., 62.]),
         "element_area": 12.0},
        {"adjustment_term": 7.0,
         "flanking_reduction_index": np.array([46., 49., 52., 55., 58., 61., 64.]),
         "element_area": 9.0},
    ]
    res = installed_source_prediction(lws_c, dc, paths, frequencies=bands)

    x = np.arange(bands.size)
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.plot(x, lws_c, color=COLOR_SECONDARY, marker="o", lw=2.0,
            label=r"characteristic $L_{Ws,c}$ (EN 15657)")
    ax.plot(x, lws_inst, color=COLOR_TERTIARY, marker="s", lw=2.0,
            label=r"installed $L_{Ws,inst}$ = $L_{Ws,c}-D_C$")
    for k, p in enumerate(res.path_levels):
        ax.plot(x, p, color=COLOR_GRID, lw=1.0, ls=":", marker=".",
                label="paths $L_{n,s,ij}$" if k == 0 else None)
    ax.plot(x, res.total_level, color=COLOR_PRIMARY, marker="D", lw=2.4,
            label=r"total $L_{n,s}$")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{b:g}" for b in bands])
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Level [dB]")
    ax.set_title("EN 12354-5 Installed Structure-Borne Sound",
                 fontweight="bold", pad=12)
    ax.grid(which="major", axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "DC = 10 lg(|Ys+Yi|^2 / (|Ys| Re Yi))",
        "Ln,s,ij = LWs,inst - Dsa - Rij - 10 lg(Si/S0) - 10 lg(A0/4)",
        "Ln,s = 10 lg(sum 10^(Ln,s,ij/10)),  S0 = A0 = 10 m2",
    ]
    ax.text(0.015, 0.02, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=8.5, color=COLOR_FG, family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "installed_structure_borne.svg")
    plt.close()


def generate_tone_audibility(output_dir: str) -> None:
    """ISO/PAS 20065 tonal audibility: per-tone ΔL of the Annex E example."""
    print("Generating tone_audibility...")
    from phonometry import assess_tones

    # Annex E combustion-engine example, spectrum 1 (Tables E.2/E.3),
    # line spacing Δf = 2.7 Hz. Each tuple is (fT, LS, LT).
    tones = [
        (118.4, 48.91, 64.56), (137.3, 49.22, 67.96), (158.8, 50.50, 68.63),
        (314.9, 52.85, 68.50), (433.4, 58.29, 73.17), (592.2, 59.53, 78.31),
        (629.8, 59.71, 75.00), (643.3, 61.98, 79.75), (1582.7, 54.16, 71.07),
    ]
    freqs = [t[0] for t in tones]
    res = assess_tones(freqs, [t[2] for t in tones], [t[1] for t in tones], 2.7)

    x = np.arange(len(freqs))
    decisive = int(np.argmax(res.audibilities))
    colors = [COLOR_PRIMARY] * len(freqs)
    colors[decisive] = COLOR_SECONDARY

    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.bar(x, res.audibilities, width=0.7, color=colors, edgecolor=COLOR_FG,
           linewidth=0.6)
    ax.axhline(0.0, color=COLOR_FG, ls="--", lw=1.0,
               label=r"threshold $\Delta L = 0$ dB")
    ax.bar([decisive], [res.audibilities[decisive]], width=0.7,
           color=COLOR_SECONDARY, edgecolor=COLOR_FG, linewidth=0.6,
           label=(rf"decisive $\Delta L$ = {res.decisive_audibility:.1f} dB "
                  rf"@ {res.decisive_frequency:g} Hz"))

    ax.set_xticks(x)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel(r"Audibility $\Delta L$ [dB]")
    ax.set_title("ISO/PAS 20065 Tonal Audibility", fontweight="bold", pad=12)
    ax.grid(which="major", axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "dfc = 25 + 75 (1 + 1.4 (fT/1000)^2)^0.69",
        "LG = LS + 10 lg(dfc/df),  av = -2 - lg(1 + (f/502)^2.5)",
        "dL = LT - LG - av  (combustion engine, Annex E)",
    ]
    ax.text(0.015, 0.02, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="left", fontsize=8.5, color=COLOR_FG, family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "tone_audibility.svg")
    plt.close()


def generate_absorption_uncertainty(output_dir: str) -> None:
    """ISO 12999-2 absorption-coefficient uncertainty: alpha_s with a +/-U ribbon."""
    print("Generating absorption_uncertainty...")
    from phonometry import sound_absorption_coefficient_uncertainty

    # The standard's worked Example (Table 4): a measured sound absorption
    # coefficient alpha_s per one-third-octave band and its reproducibility
    # expanded uncertainty at k = 2.
    freqs = np.array([63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
                      630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000],
                     dtype=float)
    alpha_s = np.array([0.33, 0.35, 0.39, 0.38, 0.37, 0.36, 0.36, 0.36, 0.43,
                        0.49, 0.58, 0.63, 0.68, 0.71, 0.73, 0.75, 0.77, 0.79,
                        0.81, 0.81])
    res = sound_absorption_coefficient_uncertainty(alpha_s, freqs, confidence=0.95)
    u = res.expanded_uncertainty

    x = np.arange(len(freqs))
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.fill_between(x, alpha_s - u, alpha_s + u, color=COLOR_TERTIARY, alpha=0.22,
                    zorder=0, label="+/-U (k = 2), reproducibility")
    ax.plot(x, alpha_s, "-", color=COLOR_PRIMARY, linewidth=2.4, marker="o",
            markersize=6, zorder=5, label="alpha_s (ISO 354)")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(b)}" for b in freqs], rotation=45, fontsize=8)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound absorption coefficient")
    ax.set_ylim(0.0, 1.15)
    ax.set_title("ISO 12999-2 Sound Absorption Coefficient Uncertainty",
                 fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "sigma_R = m alpha_s + n  (Table 1)",
        "U = k u,  k = 2  (95 %)",
    ]
    ax.text(0.985, 0.03, "\n".join(info), transform=ax.transAxes,
            va="bottom", ha="right", fontsize=11, color=COLOR_FG,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "absorption_uncertainty.png")
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
    save_figure(output_dir, "insulation_uncertainty_demo.png")
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
    save_figure(output_dir, "air_absorption_alpha.png")
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
    # Separate positive and negative cumulative baselines so a negative term
    # (Agr is a net gain at 63 Hz here) stacks below zero instead of being
    # drawn on top of the previous bars; the signed heights sum to a_total.
    pos_bottom = np.zeros(len(bands))
    neg_bottom = np.zeros(len(bands))
    for term, color, label in [
        (att.a_div, COLOR_PRIMARY, "Adiv — divergence"),
        (att.a_atm, COLOR_TERTIARY, "Aatm — atmospheric"),
        (att.a_gr, "#9467bd", "Agr — ground"),
        (att.a_bar, "#ff7f0e", "Abar — barrier"),
    ]:
        bottom = np.where(term >= 0.0, pos_bottom, neg_bottom)
        ax.bar(x, term, bottom=bottom, color=color, edgecolor=COLOR_FG,
               linewidth=0.6, label=label, zorder=3)
        pos_bottom += np.maximum(term, 0.0)
        neg_bottom += np.minimum(term, 0.0)
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
    save_figure(output_dir, "outdoor_attenuation_breakdown.png")
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
    save_figure(output_dir, "exposure_uncertainty.png")
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
    save_figure(output_dir, "absorption_rating.png")
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
    save_figure(output_dir, "airflow_resistance.png")
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
    save_figure(output_dir, "impedance_tube.png")
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
    save_figure(output_dir, "scattering_coefficient.png")
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
    save_figure(output_dir, "diffusion_polar.png")
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
    save_figure(output_dir, "insitu_absorption.png")
    plt.close()


def generate_sound_power_pressure_result(output_dir: str) -> None:
    """ISO 3744: enveloping-surface LW spectrum from hemisphere pressure levels."""
    print("Generating sound_power_pressure_result.png...")
    from phonometry import sound_power_pressure

    # The sound-power guide's section-1 example: octave-band SPL at the 10
    # hemisphere positions of ISO 3744 (Annex B) around a machine on one
    # reflecting plane, with a flat 55 dB background, corrected for background
    # (K1) and for the test room (K2 from T = 0.6 s, V = 300 m^3). The library
    # forms LW = Lp_bar - K1 - K2 + 10 lg(S/S0) per band and the A-weighted
    # total LWA.
    freqs = np.array([63, 125, 250, 500, 1000, 2000, 4000, 8000], dtype=float)
    base = np.array([70.0, 74.0, 78.0, 80.0, 79.0, 76.0, 72.0, 66.0])
    rng = np.random.default_rng(0)
    levels = base + rng.normal(0.0, 0.5, size=(10, 8))
    background = np.full((10, 8), 55.0)
    result = sound_power_pressure(
        levels, "hemisphere", radius=1.5, reflecting_planes=1,
        background_levels=background, frequencies=freqs,
        reverberation_time=0.6, volume=300.0,
    )

    lw = result.sound_power_level
    lwa = result.sound_power_level_a
    positions = np.arange(freqs.size, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.bar(positions, lw, width=0.7, color=COLOR_PRIMARY, edgecolor=COLOR_FG,
           linewidth=0.7, zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(f"Enveloping-surface sound power (ISO 3744)  LWA = {lwa:.1f} dB(A)",
                 fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound power level LW [dB]")
    ax.set_ylim(0.0, float(np.nanmax(lw)) + 8.0)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "sound_power_pressure_result.png")
    plt.close()


def generate_sound_power_reverberation_result(output_dir: str) -> None:
    """ISO 3741: reverberation-room LW spectrum (direct method)."""
    print("Generating sound_power_reverberation_result.png...")
    from phonometry import sound_power_reverberation

    # The sound-power guide's section-2 example: one-third-octave mean room
    # SPL from 100 Hz to 10 kHz in a qualified 200 m^3 reverberation room with
    # T60 = 2 s, carried to LW through the Sabine absorption area, the
    # Waterhouse correction and the meteorological corrections C1/C2
    # (ISO 3741 Eq. 20).
    freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000,
                      1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
                      10000], dtype=float)
    lp = np.linspace(80.0, 70.0, freqs.size)
    t60 = np.full(freqs.size, 2.0)
    result = sound_power_reverberation(
        lp, t60, volume=200.0, surface_area=220.0, frequencies=freqs,
        temperature=20.0, static_pressure=101.0,
    )

    lw = result.sound_power_level
    lwa = result.sound_power_level_a
    positions = np.arange(freqs.size, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.bar(positions, lw, width=0.7, color=COLOR_PRIMARY, edgecolor=COLOR_FG,
           linewidth=0.7, zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(
        f"Reverberation-room sound power (ISO 3741)  LWA = {lwa:.1f} dB(A)",
        fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound power level LW [dB]")
    ax.set_ylim(0.0, float(np.nanmax(lw)) + 8.0)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "sound_power_reverberation_result.png")
    plt.close()


def generate_sound_power_intensity_result(output_dir: str) -> None:
    """ISO 9614-2: intensity-scanning LW spectrum from segment sweeps."""
    print("Generating sound_power_intensity_result.png...")
    from phonometry import sound_power_intensity

    # The sound-power guide's section-3 example: two repeated intensity sweeps
    # over 6 surface segments and 6 octave bands, with the segment surface SPL
    # and the probe's pressure-residual intensity index. The partial powers
    # In_i * Si sum to the band LW; every band passes the field-indicator
    # criteria at engineering grade here (no SoundPowerWarning fires).
    freqs = np.array([125, 250, 500, 1000, 2000, 4000], dtype=float)
    areas = np.full(6, 0.5)
    rng = np.random.default_rng(0)
    scan1 = np.abs(rng.normal(1e-4, 2e-5, size=(6, 6)))
    scan2 = scan1 * (1.0 + rng.normal(0.0, 0.02, size=(6, 6)))
    pressure = np.full((6, 6), 80.0)
    result = sound_power_intensity(
        scan1, areas, normal_intensity_2=scan2, pressure_levels=pressure,
        pressure_residual_index=12.0, frequencies=freqs,
        band_type="octave", grade="engineering",
    )

    lw = result.sound_power_level
    lwa = result.sound_power_level_a
    positions = np.arange(freqs.size, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 6.3))
    # Plot only the determinable (finite-LW) bands; an undeterminable band
    # (net inflow -> NaN) is left as a gap rather than faked to 0 dB. All six
    # bands are finite with this synthetic data, so this is future-proofing.
    finite = np.isfinite(lw)
    ax.bar(positions[finite], lw[finite], width=0.7, color=COLOR_PRIMARY,
           edgecolor=COLOR_FG, linewidth=0.7, zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(
        f"Intensity-scanning sound power (ISO 9614-2)  LWA = {lwa:.1f} dB(A)",
        fontweight="bold", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Sound power level LW [dB]")
    ax.set_ylim(0.0, float(np.nanmax(lw)) + 8.0)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "sound_power_intensity_result.png")
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
    save_figure(output_dir, "precision_anechoic_power.png")
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
    save_figure(output_dir, "intensity_scan_power.png")
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
    save_figure(output_dir, "vibration_weighting.png")
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
    save_figure(output_dir, "weighted_acceleration.png")
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
    save_figure(output_dir, "daily_vibration_exposure.png")
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
    save_figure(output_dir, "speech_intelligibility.png")
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
    save_figure(output_dir, "sii_vocal_efforts.png")
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
    save_figure(output_dir, "impulse_prominence.png")
    plt.close()


def generate_tonal_audibility(output_dir: str) -> None:
    """ISO 1996-2: tonal adjustment Kt(ΔLta) with the Annex C.5 examples."""
    print("Generating tonal_audibility...")
    from phonometry import assess_tonal_audibility, tonal_adjustment

    # The four ISO 1996-2:2007 Annex C.5 worked examples: (Lpt, Lpn, fc).
    examples = [(46.7, 37.3, 4000.0), (54.1, 45.2, 430.0),
                (53.6, 45.5, 755.0), (54.6, 45.5, 308.0)]
    assessed = [assess_tonal_audibility(lpt, lpn, fc) for lpt, lpn, fc in examples]
    # A synthetic mid-range tone to exercise the sloped branch.
    mid = assess_tonal_audibility(50.0, 44.0, 500.0)

    grid = np.linspace(0.0, 15.0, 300)
    curve = np.array([tonal_adjustment(d) for d in grid])

    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.plot(grid, curve, "-", color=COLOR_PRIMARY, linewidth=2.4, zorder=5,
            label=r"$K_t(\Delta L_{ta})$ (Formulae C.4-C.6)")
    for x in (4.0, 10.0):
        ax.axvline(x, color=COLOR_GRID, linestyle=":", alpha=0.8, zorder=1)
    ax.scatter([a.audibility for a in assessed], [a.adjustment for a in assessed],
               color=COLOR_SECONDARY, marker="o", s=70, zorder=6,
               label="Annex C.5 examples")
    ax.scatter([mid.audibility], [mid.adjustment], color=COLOR_TERTIARY,
               marker="*", s=150, zorder=7, label="mid-range tone")

    ax.set_xlabel(r"Tonal audibility $\Delta L_{ta}$ [dB]")
    ax.set_ylabel("Tonal adjustment $K_t$ [dB]")
    ax.set_ylim(-0.3, 6.6)
    ax.set_title("ISO 1996-2 Tonal Adjustment", fontweight="bold", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "Kt = 0            (dLta < 4)",
        "Kt = dLta - 4  (4 <= dLta <= 10)",
        "Kt = 6            (dLta > 10)",
    ]
    ax.text(0.015, 0.97, "\n".join(info), transform=ax.transAxes,
            va="top", ha="left", fontsize=10, color=COLOR_FG, family="monospace",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": panel,
                  "edgecolor": COLOR_GRID})
    plt.tight_layout()
    save_figure(output_dir, "tonal_audibility.png")
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
    save_figure(output_dir, "multiple_shock.png")
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
    save_figure(output_dir, "enclosed_space_absorption.png")
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
    save_figure(output_dir, "room_noise_criteria.png")
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
    save_figure(output_dir, "hearing_threshold.png")
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
    save_figure(output_dir, "noise_induced_hearing_loss.png")
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
    save_figure(output_dir, "uncertainty_budget.png")
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
    generate_filter_class0_mask(img_dir)
    generate_weighting_class_mask(img_dir)
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
    generate_facade_prediction(img_dir)
    generate_intensity_insulation(img_dir)
    generate_survey_insulation(img_dir)
    generate_floor_covering_improvement(img_dir)
    generate_flanking_transmission(img_dir)
    generate_reverberation_models(img_dir)
    generate_dynamic_stiffness(img_dir)
    generate_mechanical_mobility(img_dir)
    generate_transfer_stiffness(img_dir)
    generate_vibration_sound_power(img_dir)
    generate_structure_borne_power(img_dir)
    generate_installed_structure_borne(img_dir)
    generate_tone_audibility(img_dir)
    generate_absorption_uncertainty(img_dir)
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

    # Sound power result spectra for the three most-used routes
    # (ISO 3744 enveloping surface, ISO 3741 reverberation room,
    # ISO 9614-2 intensity scanning)
    generate_sound_power_pressure_result(img_dir)
    generate_sound_power_reverberation_result(img_dir)
    generate_sound_power_intensity_result(img_dir)

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
    generate_tonal_audibility(img_dir)
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

    # Fluctuation strength (Fastl & Zwicker Eq. 10.2 + Osses 2016 signal model)
    # and psychoacoustic annoyance (Fastl & Zwicker Eqs 16.2-16.4).
    generate_fluctuation_strength(img_dir)
    generate_psychoacoustic_annoyance(img_dir)

    # Electroacoustics (plan-18): distortion metrics (IEC 60268-3) and
    # frequency-response / coherence estimators (Bendat & Piersol).
    generate_distortion(img_dir)
    generate_frequency_response(img_dir)

    # Underwater acoustics (plan-19A): ship radiated noise / monopole source
    # level (ISO 17208) and pile-driving sound exposure (ISO 18406).
    generate_ship_source_level(img_dir)
    generate_pile_driving(img_dir)

    # Aircraft noise (plan-19B): ICAO Annex 16 Effective Perceived Noise Level.
    generate_epnl(img_dir)

    # Wind-turbine noise (plan-19B2): IEC 61400-11 tonal audibility.
    generate_wind_turbine_tonality(img_dir)

    # Underwater propagation (plan-22 P1): transmission loss, sound-speed
    # profile and the sonar equation.
    generate_underwater_transmission_loss(img_dir)
    generate_underwater_sound_speed(img_dir)
    generate_sonar_equation(img_dir)

    # Underwater propagation (plan-22 P1 PR-2): seabed reflection, ambient
    # noise (Wenz) and ship-traffic source level (JOMOPANS-ECHO).
    generate_seabed_reflection(img_dir)
    generate_ocean_ambient_noise(img_dir)
    generate_ship_traffic_noise(img_dir)


# ===========================================================================
# Animations (Tier 1 pilot)
# ---------------------------------------------------------------------------
# Deterministic FuncAnimation clips of the level-vs-time phenomena the library
# already computes. Each is rendered to WebM (site <video>) in all four
# language x theme variants, and to an animated GIF for the English GitHub
# docs (both themes). Kept out of generate_all()/`make graphs` so ordinary
# PNG regeneration stays fast; produced by `make animations`.
# ===========================================================================

_ANIM_FPS = 20
_ANIM_SECONDS = 6
_ANIM_FRAMES = _ANIM_FPS * _ANIM_SECONDS
_ANIM_FIGSIZE = (8.0, 4.5)   # inches at _ANIM_DPI -> 800 x 450 px
_ANIM_DPI = 100
# The GitHub-docs GIF is a compact fallback for the smooth site WebM: a lower
# frame rate, smaller frame and capped palette keep even the detail-dense
# clips (the p·u oscillations) near half a megabyte.
_GIF_FPS = 12
_GIF_SCALE = 640
_GIF_COLORS = 64


def _translate_str(s: str) -> str:
    """Translate one label to the active language (exact + pattern + comma).

    Mirrors :func:`_translate_figure` for a single string, so animation labels
    -- which are rewritten every frame and never pass through ``save_figure``
    -- can be localised at creation time instead.
    """
    import re as _re

    if _LANG == "en" or not s:
        return s
    if s in _ES_EXACT:
        out = _ES_EXACT[s]
    else:
        out = s
        for pat, repl in _ES_PATTERNS:
            new, n = _re.subn(pat, repl, s)
            if n:
                out = new
                break
    if "$" not in out and _re.search(r"\d\.\d", out):
        out = _re.sub(r"(?<![\d.A-Za-z])(\d+)\.(\d+)(?![.\d])", r"\1,\2", out)
    return out


def _anim_path(output_dir: str, stem: str, ext: str) -> str:
    """Animation output path with the active language + theme suffixes."""
    return os.path.join(output_dir, f"{stem}{_LANG_SUFFIX}{_FILENAME_SUFFIX}.{ext}")


def _new_anim_fig() -> tuple[Any, Any]:
    """A fixed-size themed figure for a clip (constant canvas across frames)."""
    fig, ax = plt.subplots(figsize=_ANIM_FIGSIZE, dpi=_ANIM_DPI, layout="constrained")
    ax.grid(True, color=COLOR_GRID, linestyle="--", alpha=0.5)
    return fig, ax


def _save_animation(anim: Any, fig: Any, output_dir: str, stem: str,
                    make_gif: bool = True) -> None:
    """Write *anim* to WebM (always) and, for English, an animated GIF.

    The GIF is derived from the just-written WebM with an ffmpeg palette pass
    so the GitHub docs get a compact, self-contained loop; the site embeds the
    WebM directly. ``savefig.bbox`` is forced to ``standard`` so every frame
    keeps the same canvas size (a ``tight`` box would jitter and break the
    encoder).
    """
    import subprocess

    from matplotlib.animation import FFMpegWriter

    webm = _anim_path(output_dir, stem, "webm")
    writer = FFMpegWriter(
        fps=_ANIM_FPS, codec="libvpx-vp9",
        extra_args=["-b:v", "0", "-crf", "40", "-pix_fmt", "yuv420p",
                    "-an", "-loglevel", "error"],
    )
    with plt.rc_context({"savefig.bbox": "standard"}):
        anim.save(webm, writer=writer, dpi=_ANIM_DPI,
                  savefig_kwargs={"facecolor": fig.get_facecolor()})
    made_gif = False
    if make_gif and _LANG == "en":
        gif = _anim_path(output_dir, stem, "gif")
        palette = os.path.join(output_dir, f".{stem}{_FILENAME_SUFFIX}_pal.png")
        vf = f"fps={_GIF_FPS},scale={_GIF_SCALE}:-1:flags=lanczos"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", webm, "-vf",
             f"{vf},palettegen=max_colors={_GIF_COLORS}:stats_mode=diff",
             "-update", "1", palette],
            check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", webm, "-i", palette,
             "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
             "-loop", "0", gif], check=True)
        os.remove(palette)
        made_gif = True
    plt.close(fig)
    theme = "dark" if _FILENAME_SUFFIX else "light"
    print(f"  {stem} [{_LANG} {theme}] -> webm" + (" + gif" if made_gif else ""))


def animate_time_weighting_ballistics(output_dir: str) -> None:
    """F/S/I exponential detectors chasing a tone burst (IEC 61672-1)."""
    from matplotlib.animation import FuncAnimation

    from phonometry import time_weighting

    T = _translate_str
    fs = 8000
    t = np.linspace(0, 4.0, int(fs * 4.0), endpoint=False)
    # A steady 250 Hz tone burst (unit amplitude) from 1.0 s to 2.5 s. The
    # carrier is high enough that even the 35 ms Impulse detector smooths the
    # squared ripple, so each detector shows its own clean rise and decay
    # (a noise burst would drown the ballistics in fluctuation).
    x = np.zeros_like(t)
    on = (t >= 1.0) & (t < 2.5)
    x[on] = np.sin(2 * np.pi * 250 * t[on])
    ref = 0.5  # mean square of a unit-amplitude tone
    fast = time_weighting(x, fs, mode="fast") / ref
    slow = time_weighting(x, fs, mode="slow") / ref
    imp = time_weighting(x, fs, mode="impulse") / ref

    fig, ax = _new_anim_fig()
    ax.set_xlim(0.6, 4.0)
    ax.set_ylim(0, 1.2)
    ax.axvspan(1.0, 2.5, color=COLOR_GRID, alpha=0.4, lw=0)
    ax.text(1.75, 1.14, T("tone burst"), ha="center", va="top", color=COLOR_FG,
            fontsize=9, alpha=0.8)
    (l_f,) = ax.plot([], [], color=COLOR_PRIMARY, lw=2.2, label=T("Fast (125 ms)"))
    (l_s,) = ax.plot([], [], color=COLOR_SECONDARY, lw=2.2, label=T("Slow (1000 ms)"))
    (l_i,) = ax.plot([], [], color="#7e57c2", lw=1.8, ls="-.",
                     label=T("Impulse (35 ms / 1.5 s)"))
    cursor = ax.axvline(0.6, color=COLOR_FG, lw=1.0, alpha=0.45)
    readout = ax.text(0.985, 0.96, "", transform=ax.transAxes, ha="right",
                      va="top", family="monospace", fontsize=11, color=COLOR_FG)
    ax.set_title(T("Time-weighting ballistics (IEC 61672-1)"), fontweight="bold")
    ax.set_xlabel(T("Time [s]"))
    ax.set_ylabel(T("Mean-square response (normalized)"))
    ax.legend(loc="upper left", fontsize=9)

    tmin, tmax = 0.6, 4.0

    def update(k: int) -> tuple[Any, ...]:
        tc = tmin + (tmax - tmin) * k / (_ANIM_FRAMES - 1)
        m = t <= tc
        l_f.set_data(t[m], fast[m])
        l_s.set_data(t[m], slow[m])
        l_i.set_data(t[m], imp[m])
        cursor.set_xdata([tc, tc])
        i = max(0, min(len(t) - 1, int(round(tc * fs))))
        readout.set_text(T(f"F {fast[i]:.2f}\nS {slow[i]:.2f}\nI {imp[i]:.2f}"))
        return l_f, l_s, l_i, cursor, readout

    anim = FuncAnimation(fig, update, frames=_ANIM_FRAMES,
                         interval=1000 / _ANIM_FPS, blit=False)
    _save_animation(anim, fig, output_dir, "anim_time_weighting")


def animate_onset_detection(output_dir: str) -> None:
    """An impulse onset drawn on L_AF, with OR/LD/P/KI live (NT ACOU 112)."""
    from matplotlib.animation import FuncAnimation

    from phonometry import impulse_adjustment, predicted_prominence

    T = _translate_str
    fs = 500
    t = np.linspace(0, 3.0, int(fs * 3.0), endpoint=False)
    ls, le = 55.0, 85.0    # start and end level of the onset, dB
    t0, rise = 1.0, 0.05   # onset at 1.0 s, lasting 50 ms
    laf = np.full_like(t, ls)
    ramp = (t >= t0) & (t < t0 + rise)
    laf[ramp] = ls + (le - ls) * 0.5 * (1 - np.cos(np.pi * (t[ramp] - t0) / rise))
    after = t >= t0 + rise
    laf[after] = ls + (le - ls) * np.exp(-(t[after] - t0 - rise) / 0.6)
    onset_rate = (le - ls) / rise      # 600 dB/s
    level_diff = le - ls               # 30 dB
    prom = float(predicted_prominence(onset_rate, level_diff))
    ki = float(impulse_adjustment(prom))
    is_onset = np.gradient(laf, t) > 10.0   # clauses 4.5-4.7

    fig, ax = _new_anim_fig()
    ax.set_xlim(0.6, 3.0)
    ax.set_ylim(45, 95)
    (base,) = ax.plot([], [], color=COLOR_PRIMARY, lw=2.0, label=T("L_AF history"))
    (hot,) = ax.plot([], [], color=COLOR_SECONDARY, lw=3.6,
                     label=T("onset (> 10 dB/s)"))
    cursor = ax.axvline(0.6, color=COLOR_FG, lw=1.0, alpha=0.45)
    ann = ax.text(0.985, 0.06, "", transform=ax.transAxes, ha="right",
                  va="bottom", family="monospace", fontsize=11, color=COLOR_FG)
    ax.set_title(T("Impulse onset detection (NT ACOU 112)"), fontweight="bold")
    ax.set_xlabel(T("Time [s]"))
    ax.set_ylabel(T("A-weighted level L_AF [dB]"))
    ax.legend(loc="upper right", fontsize=9)
    tmin, tmax = 0.6, 3.0

    def update(k: int) -> tuple[Any, ...]:
        tc = tmin + (tmax - tmin) * k / (_ANIM_FRAMES - 1)
        m = t <= tc
        base.set_data(t[m], laf[m])
        oh = m & is_onset
        hot.set_data(t[oh], laf[oh])
        cursor.set_xdata([tc, tc])
        if tc >= t0 + rise:
            ann.set_text(T(f"OR {onset_rate:.0f} dB/s\nLD {level_diff:.0f} dB\n"
                           f"P {prom:.1f}\nKI {ki:.1f} dB"))
        else:
            ann.set_text(T("listening…"))
        return base, hot, cursor, ann

    anim = FuncAnimation(fig, update, frames=_ANIM_FRAMES,
                         interval=1000 / _ANIM_FPS, blit=False)
    _save_animation(anim, fig, output_dir, "anim_onset_detection")


def animate_instantaneous_intensity(output_dir: str) -> None:
    """Instantaneous p·u: a progressive wave flows, a standing wave sloshes."""
    from matplotlib.animation import FuncAnimation

    T = _translate_str
    t = np.linspace(0, 3.0, 600)
    w = 2 * np.pi * 2.0
    # Progressive: p and u in phase -> p·u >= 0, non-zero mean (net flow).
    # Standing (at a point): p and u 90 deg out of phase -> p·u averages zero.
    panels_data = [
        ("Progressive wave — net power flows",
         np.sin(w * t), np.sin(w * t)),
        ("Standing wave — energy sloshes",
         np.cos(w * t), np.sin(w * t)),
    ]
    fig, axes = plt.subplots(1, 2, figsize=_ANIM_FIGSIZE, dpi=_ANIM_DPI,
                             layout="constrained", sharey=True)
    panels = []
    for ax, (title, p, u) in zip(axes, panels_data, strict=True):
        ax.grid(True, color=COLOR_GRID, linestyle="--", alpha=0.5)
        ax.set_xlim(0, 3.0)
        ax.set_ylim(-1.15, 1.15)
        ax.plot(t, p, color=COLOR_PRIMARY, alpha=0.35, lw=1.2, label=T("pressure p"))
        ax.plot(t, u, color=COLOR_TERTIARY, alpha=0.35, lw=1.2,
                label=T("velocity u"))
        (iline,) = ax.plot([], [], color=COLOR_SECONDARY, lw=2.0,
                           label=T("intensity p·u"))
        mline = ax.axhline(0.0, color=COLOR_FG, ls="--", lw=1.0, alpha=0.65)
        cursor = ax.axvline(0.0, color=COLOR_FG, lw=1.0, alpha=0.4)
        txt = ax.text(0.5, 0.02, "", transform=ax.transAxes, ha="center",
                      va="bottom", family="monospace", fontsize=10, color=COLOR_FG)
        ax.set_title(T(title), fontweight="bold", fontsize=11)
        ax.set_xlabel(T("Time [s]"))
        ax.legend(loc="upper right", fontsize=8)
        panels.append({"ax": ax, "I": p * u, "iline": iline, "mline": mline,
                       "cursor": cursor, "txt": txt, "fill": None})
    axes[0].set_ylabel(T("amplitude (normalized)"))
    fig.suptitle(T("Instantaneous sound intensity p·u"), fontweight="bold")

    def update(k: int) -> tuple[Any, ...]:
        tc = 3.0 * k / (_ANIM_FRAMES - 1)
        arts: list[Any] = []
        for pn in panels:
            idx = max(1, int(np.searchsorted(t, tc)))
            pn["iline"].set_data(t[:idx], pn["I"][:idx])
            if pn["fill"] is not None:
                pn["fill"].remove()
            pn["fill"] = pn["ax"].fill_between(t[:idx], 0.0, pn["I"][:idx],
                                               color=COLOR_SECONDARY, alpha=0.22)
            mean = float(np.mean(pn["I"][:idx]))
            pn["mline"].set_ydata([mean, mean])
            pn["cursor"].set_xdata([tc, tc])
            pn["txt"].set_text(T(f"⟨p·u⟩ = {mean:+.2f}"))
            arts += [pn["iline"], pn["fill"], pn["mline"], pn["cursor"], pn["txt"]]
        return tuple(arts)

    anim = FuncAnimation(fig, update, frames=_ANIM_FRAMES,
                         interval=1000 / _ANIM_FPS, blit=False)
    _save_animation(anim, fig, output_dir, "anim_instantaneous_intensity")


def animate_schroeder(output_dir: str) -> None:
    """Backward integration of p²(t) revealing the decay curve (ISO 3382)."""
    from matplotlib.animation import FuncAnimation

    from phonometry import decay_curve, room_parameters
    from phonometry.room_acoustics import _T20_RANGE, _T30_RANGE, _onset_index

    T = _translate_str
    fs, reverb_t = 48000, 1.2
    rng = np.random.default_rng(2026)
    t = np.arange(int(2.0 * fs)) / fs
    ir = (rng.standard_normal(t.size) * np.exp(-6.9077 * t / reverb_t)
          + rng.standard_normal(t.size) * 10.0 ** (-45.0 / 20.0))
    time, level = decay_curve(ir, fs)
    res = room_parameters(ir, fs, limits=None)
    t20, t30 = float(res.t20[0]), float(res.t30[0])
    p2 = ir.astype(np.float64) ** 2
    p2 = p2[_onset_index(p2):]
    t_raw = np.arange(p2.size) / fs
    raw_db = 10.0 * np.log10(np.maximum(p2, p2.max() * 1e-12) / p2.max())

    # Regression lines drawn once the sweep finishes: slope -60/T over each
    # evaluation range, extended to the -60 dB crossing at t = T.
    def _fit(rng_db: tuple[float, float]) -> tuple[float, float] | None:
        mask = (level <= -rng_db[0]) & (level >= -rng_db[1])
        if int(mask.sum()) < 2:
            return None
        slope, intercept = np.polyfit(time[mask], level[mask], 1)
        if slope >= 0.0:   # a non-decaying fit has no meaningful -60 dB crossing
            return None
        return float(slope), float(intercept)

    fits = []
    for rng_db, color, style, key in (
        (_T20_RANGE, COLOR_SECONDARY, "--", "T20 fit"),
        (_T30_RANGE, COLOR_TERTIARY, "-.", "T30 fit"),
    ):
        fit = _fit(rng_db)
        if fit is None:
            continue
        slope, intercept = fit
        fits.append((color, style, key,
                     (-intercept / slope, (-60.0 - intercept) / slope)))
    tmax = float(time.max())
    xmax = max([tmax, *(f[3][1] for f in fits)]) * 1.03

    fig, ax = _new_anim_fig()
    ax.set_xlim(0, xmax)
    ax.set_ylim(-65, 3)
    ax.plot(t_raw, raw_db, color="gray", alpha=0.25, lw=0.6,
            label=T("Raw squared IR level"))
    (curve,) = ax.plot([], [], color=COLOR_PRIMARY, lw=2.4,
                       label=T("Schroeder decay curve"))
    fit_lines = []
    for color, style, key, span in fits:
        (fl,) = ax.plot([], [], color=color, ls=style, lw=1.7, label=T(key))
        fit_lines.append((fl, span))
    front = ax.axvline(tmax, color=COLOR_FG, lw=1.3, alpha=0.55)
    fill = {"art": None}
    ann = ax.text(0.035, 0.06, "", transform=ax.transAxes, ha="left", va="bottom",
                  family="monospace", fontsize=11, color=COLOR_FG)
    ax.set_title(T("Schroeder backward integration (ISO 3382)"), fontweight="bold")
    ax.set_xlabel(T("Time [s]"))
    ax.set_ylabel(T("Level [dB]"))
    ax.legend(loc="upper right", fontsize=9)

    reveal = int(_ANIM_FRAMES * 0.8)   # sweep for 80% of frames, then annotate

    def update(k: int) -> tuple[Any, ...]:
        xf = tmax * (1.0 - k / (reveal - 1)) if k < reveal else 0.0
        m = time >= xf
        curve.set_data(time[m], level[m])
        front.set_xdata([xf, xf])
        if fill["art"] is not None:
            fill["art"].remove()
        mr = t_raw >= xf
        fill["art"] = ax.fill_between(t_raw[mr], -65, raw_db[mr],
                                      color=COLOR_SECONDARY, alpha=0.12)
        arts: list[Any] = [curve, front, fill["art"], ann]
        if k >= reveal:
            for fl, (t_lo, t_hi) in fit_lines:
                fl.set_data([t_lo, t_hi], [0.0, -60.0])
                arts.append(fl)
            ann.set_text(T(f"T20 = {t20:.2f} s\nT30 = {t30:.2f} s"))
        else:
            ann.set_text(T("integrating from the tail →"))
        return tuple(arts)

    anim = FuncAnimation(fig, update, frames=_ANIM_FRAMES,
                         interval=1000 / _ANIM_FPS, blit=False)
    _save_animation(anim, fig, output_dir, "anim_schroeder")


def generate_animations(output_dir: str) -> None:
    """Render every Tier-1 animation in the active language/theme."""
    import shutil

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg was not found on PATH; it is required to encode the "
            "animation WebM/GIF outputs. Install ffmpeg and retry."
        )
    animate_time_weighting_ballistics(output_dir)
    animate_onset_detection(output_dir)
    animate_instantaneous_intensity(output_dir)
    animate_schroeder(output_dir)


if __name__ == "__main__":
    img_dir = ".github/images"
    os.makedirs(img_dir, exist_ok=True)

    # `--animations` renders only the Tier-1 clips (slow ffmpeg encoding, kept
    # out of the default PNG run); `--all` does both. Every asset is produced
    # four times: light/dark theme x English/Spanish ("_dark" / "_es" /
    # "_es_dark" suffixes) so both site languages follow the user's mode.
    only_anim = "--animations" in sys.argv
    do_figs = not only_anim or "--all" in sys.argv
    do_anim = only_anim or "--all" in sys.argv

    for lang in ("en", "es"):
        set_lang(lang)
        for dark in (False, True):
            set_theme(dark)
            mode = f"{lang} {'dark' if dark else 'light'}"
            if do_figs:
                print(f"--- Generating {mode} theme figures ---")
                generate_all(img_dir)
            if do_anim:
                print(f"--- Generating {mode} animations ---")
                generate_animations(img_dir)

    print("Graphics generated successfully.")
