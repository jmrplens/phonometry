---
title: "Niveles integrados y estadísticos"
description: "Leq, LAeq, percentiles L10/L50/L90 y espectrogramas de octava."
---

Métricas de ruido ambiental calculadas directamente sobre la señal cruda
(calibrada).

## Leq y LAeq

El nivel continuo equivalente integra la presión al cuadrado durante el tiempo
de medición:

$$
L_{eq} = 10\log_{10}\!\left(\frac{1}{T}\int_0^T \frac{p^2(t)}{p_0^2}\,dt\right) \text{ dB}, \qquad p_0 = 20\ \mu\text{Pa}
$$

y $L_{Aeq}$ es la misma integral tras ponderar A la señal. $L_N$ es el nivel
superado el $N\,\%$ del tiempo — el percentil $(100-N)$ de la distribución del
nivel con ponderación temporal.

```python
from phonometry import leq, laeq

# Nivel continuo equivalente de toda la grabación
level = leq(signal, calibration_factor=sensitivity)

# Leq ponderado A (la métrica estándar de ruido ambiental)
la = laeq(signal, fs, calibration_factor=sensitivity)
```

Ambas aceptan señales 1D (devuelven un escalar) o arrays 2D
`[channels, samples]` (devuelven un nivel por canal), y admiten `dbfs=True` para
análisis digital a fondo de escala (la calibración no aplica en modo dBFS).

## Niveles percentiles (LN)

`ln_levels` calcula niveles estadísticos a partir de la envolvente con
ponderación temporal: **L10** es el nivel superado el 10 % del tiempo (picos de
eventos), **L50** la mediana y **L90** el nivel de fondo.

```python
from phonometry import ln_levels

stats = ln_levels(signal, fs, n=(10, 50, 90), weighting="A")
print(f"LA10={stats[10]:.1f}  LA50={stats[50]:.1f}  LA90={stats[90]:.1f} dB")
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_es.png" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_es_dark.png" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%">

*L10 sigue los picos de los eventos, L50 el nivel mediano y L90 el fondo.*

Opciones: `mode` selecciona la balística de la envolvente (`'fast'`, `'slow'`,
`'impulse'`), `weighting` aplica antes la ponderación A/C, y
`calibration_factor`/`dbfs` se comportan como en `leq`. El transitorio de ataque
del integrador (~2τ) se descarta antes de calcular los percentiles.

## Métricas de pico, evento y ocupacionales

```python
from phonometry import lc_peak, sel, sound_exposure, lex_8h

# Pico ponderado C (IEC 61672-1 §5.13): los límites de acción laborales usan esto
peak = lc_peak(signal, fs, calibration_factor=sensitivity)

# Nivel de exposición sonora: nivel del evento normalizado a 1 s (LAE)
lae = sel(event, fs, weighting="A", calibration_factor=sensitivity)

# Dosis diaria de ruido (IEC 61252): exposición en Pa²·h y LEX,8h / LEP,d
E = sound_exposure(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
lex = lex_8h(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
```

`lc_peak` está verificado contra las respuestas de referencia de ciclo
único/semiciclo de la Tabla 5 de IEC 61672-1:2013, `sel` contra la columna LAE
de la Tabla 4, y las funciones de dosis contra las anclas de IEC 61252
(3,2 Pa²h ↔ exactamente 90 dB). Con `duration_hours`, la entrada se trata como
muestra representativa de ese periodo de exposición; sin él, la entrada es el
evento completo.

## Nivel de sonoridad de tonos puros (ISO 226:2023)

Las curvas isofónicas normales relacionan el SPL de un tono puro con su *nivel
de sonoridad* percibido en fonos (el SPL de un tono de 1 kHz igual de fuerte).
`equal_loudness_contour(phon)` evalúa la Fórmula (1) de ISO 226:2023 en las 29
frecuencias preferentes de tercio de octava de la Tabla 1,
`loudness_level(spl, frequency)` es la inversa exacta (Fórmula 2) y
`hearing_threshold()` devuelve la columna del umbral de audición:

```python
from phonometry import equal_loudness_contour, loudness_level

freqs, spl = equal_loudness_contour(40.0)   # la clásica isofónica de 40 fonos
phon = loudness_level(73.0, 63.0)           # 73 dB @ 63 Hz -> 40 fonos
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/equal_loudness_contours_es.png" alt="Curvas isofónicas normales de ISO 226:2023 de 20 a 90 fonos con la curva del umbral de audición" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/equal_loudness_contours_es_dark.png" alt="Curvas isofónicas normales de ISO 226:2023 de 20 a 90 fonos con la curva del umbral de audición" style="width:80%">

Validez según el apartado 4.1: 20–90 fonos (80 fonos por encima de 4 kHz); la
implementación se verifica en CI contra las tablas del Anexo B. Ojo: esto es la
sonoridad de *tonos puros* — la sonoridad de señales arbitrarias (sonos,
ISO 532) es una feature distinta, prevista más adelante.

## Tonos discretos prominentes (ECMA-418-1)

Los componentes tonales del ruido de maquinaria molestan mucho más de lo que
sugiere su nivel. ECMA-418-1:2024 (referenciada por el Anexo D de ECMA-74)
define dos métodos FFT para decidir si un tono discreto es *prominente*:
`tone_to_noise_ratio()` compara el nivel del tono con el ruido enmascarante de
su banda crítica (apartado 11) y `prominence_ratio()` compara la banda crítica
centrada en el tono con las dos bandas contiguas (apartado 12). Ambos devuelven
un veredicto estructurado frente a los criterios de prominencia dependientes de
la frecuencia:

```python
from phonometry import tone_to_noise_ratio, prominence_ratio

tnr = tone_to_noise_ratio(x, fs)            # pico más alto, o tone_freq=...
pr = prominence_ratio(x, fs, tone_freq=1000.0)
print(tnr.ratio_db, tnr.criterion_db, tnr.prominent)
```

Los tonos secundarios próximos en la misma banda crítica se combinan según el
apartado 11.6; para complejos armónicos evalúa cada componente (`tone_freq=`).
Ambos métodos trabajan sobre espectros promediados RMS con ventana Hann y no
necesitan calibración absoluta (los ratios son diferencias de nivel).

## Ruido ambiental: Lden, Ldn y niveles de evaluación (ISO 1996-1)

La evaluación regulatoria del ruido pondera más las tardes y las noches.
`lden()` implementa el nivel día-tarde-noche de ISO 1996-1:2016 (3.6.4:
+5 dB tarde, +10 dB noche, periodos 12/4/8 h por defecto — ajustables, porque
cada país los define distinto), `ldn()` la variante día-noche (3.6.5) y
`composite_rating_level()` el compuesto general de jornada completa del
apartado 6.5 (Fórmulas 5-6) para periodos arbitrarios con ajustes por fuente o
carácter (Tabla A.1: p. ej. +5 dB impulsivo regular, +12 dB altamente
impulsivo, +3 a +6 dB tonos prominentes):

```python
from phonometry import lden, composite_rating_level

l = lden(63.2, 58.1, 51.4)                      # desde LAeq por periodo
r = composite_rating_level([(63.2, 12, 0.0),    # día
                            (58.1, 4, 5.0),     # tarde (+5)
                            (51.4, 8, 10.0)])   # noche (+10) == lden
```

Combínalo con `laeq()` por periodo para ir de grabaciones a Lden, y con
`tone_to_noise_ratio()` / `prominence_ratio()` para justificar ajustes tonales.

## Espectrograma de octavas (niveles vs tiempo)

Análisis de octava fraccional en tiempo corto: un nivel por banda y ventana,
alineado en el tiempo entre bandas.

```python
from phonometry import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3)
levels, freq, times = bank.spectrogram(signal, window_time=0.125, overlap=0.5)
# levels: (bandas, ventanas) — listo para pcolormesh(times, freq, levels)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/spectrogram_example_es.png" alt="Espectrograma en tercios de octava de un barrido logarítmico con dos ráfagas de tono" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/spectrogram_example_es_dark.png" alt="Espectrograma en tercios de octava de un barrido logarítmico con dos ráfagas de tono" style="width:80%">

*Un barrido logarítmico y dos ráfagas de tono, resueltos en el tiempo y en
bandas normalizadas de tercio de octava.*

- Una entrada multicanal `(channels, samples)` devuelve `(channels, bands, frames)`.
- `times` contiene el centro de cada ventana en segundos.
- `mode='peak'` da niveles de pico por ventana en lugar de RMS.
- `zero_phase=True` filtra las bandas hacia delante y atrás para que el retardo
  de grupo por banda no desplace las ventanas (solo análisis offline).

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
mesh = ax.pcolormesh(times, freq, levels, shading="auto")
ax.set_yscale("log")
ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Frecuencia [Hz]")
fig.colorbar(mesh, label="Nivel [dB]")
```

Consulta [Calibración y dBFS](/phonometry/es/guides/calibration/) para
convertir unidades digitales a SPL físico, y
[Ponderación temporal](/phonometry/es/guides/time-weighting/) para los
detalles de la envolvente.
