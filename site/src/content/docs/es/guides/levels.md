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
L_{eq} = 10\log_{10}\left(\frac{1}{T}\int_0^T \frac{p^2(t)}{p_0^2}\ dt\right) \text{ dB}, \qquad p_0 = 20\ \mu\text{Pa}
$$

y $L_{Aeq}$ es la misma integral tras ponderar A la señal. $L_N$ es el nivel
superado el $N\ \%$ del tiempo — el percentil $(100-N)$ de la distribución del
nivel con ponderación temporal.

```python
import numpy as np
from phonometry import leq, laeq

# Una grabación calibrada en pascales para que la guía funcione por sí sola
fs = 48000
signal = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
sensitivity = 1.0                                    # calibration_factor (ver Calibración)

# Nivel continuo equivalente de toda la grabación
level = leq(signal, calibration_factor=sensitivity)

# Leq ponderado A (la métrica estándar de ruido ambiental)
la = laeq(signal, fs, calibration_factor=sensitivity)
```

Ambas aceptan señales 1D (devuelven un escalar) o arrays 2D
`[channels, samples]` (devuelven un nivel por canal), y admiten `dbfs=True` para
análisis digital a fondo de escala (la calibración no aplica en modo dBFS).

¿Por qué la media *energética* y no la media aritmética de los valores en dB?
Porque las dosis sonoras se suman como energía: dos periodos a 60 dB y 80 dB no
promedian 70 dB — la mitad a 80 dB domina y $L_{eq}$ = 77 dB. Promediar
decibelios directamente subestima cualquier ruido fluctuante. $L_{eq}$ es el
nivel del sonido *estacionario* que transporta la misma energía que el real,
fluctuante, y por eso las normativas se redactan en términos de él.

### Parámetros de `leq()` / `laeq()`

| Parámetro | Tipo / forma | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | unidades digitales (o Pa si está calibrada) | no vacío | 2D es `[channels, samples]`; devuelve un nivel por canal |
| `fs` | int | Hz | > 0 (solo `laeq`) | `leq` no necesita frecuencia de muestreo (integral RMS pura) |
| `calibration_factor` | float | Pa por unidad digital | por defecto `1.0` | De `calculate_sensitivity()` |
| `dbfs` | bool | — | por defecto `False` | `True`: 0 dBFS = seno RMS a fondo de escala; ignora la calibración |

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

Opciones: `mode` selecciona la ponderación temporal de la envolvente (`'fast'`, `'slow'`,
`'impulse'`), `weighting` aplica antes la ponderación A/C, y
`calibration_factor`/`dbfs` se comportan como en `leq`. El transitorio de ataque
del integrador (~2τ) se descarta antes de calcular los percentiles.

Formalmente, $L_N$ es el percentil $(100-N)$ de la distribución del nivel con
ponderación temporal: la grabación se convierte primero en una envolvente de
nivel frente a tiempo (Fast por defecto), y $L_{10}$ es el valor de la
envolvente superado el 10 % del tiempo. Eso hace que la *elección de la
ponderación temporal forme parte de la métrica*: un $L_{10}$ con envolvente
Slow es sistemáticamente más bajo que con una Fast en ruido impulsivo, por lo
que las normativas siempre indican la ponderación temporal.

### Parámetros de `ln_levels()`

| Parámetro | Tipo / forma | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | unidades digitales | no vacío | 2D devuelve diccionarios por canal |
| `fs` | int | Hz | > 0 | Lo necesita el detector de envolvente |
| `n` | tupla de ints | % | por defecto `(10, 50, 90)` | Cualquier porcentaje de excedencia, p. ej. `(1, 5, 95)` |
| `mode` | str | — | `'fast'` (por defecto), `'slow'`, `'impulse'` | Ponderación temporal IEC 61672-1 de la envolvente |
| `weighting` | str o None | — | `'A'`, `'C'`, `'G'`, `'Z'`, `None` (por defecto) | Ponderación frecuencial previa a la envolvente |
| `calibration_factor` / `dbfs` | float / bool | — | como `leq` | Misma semántica que en `leq()` |

## Métricas de pico, evento y ocupacionales

```python
from phonometry import lc_peak, sel, sound_exposure, lex_8h

# Pico ponderado C (IEC 61672-1 §5.13): los límites de acción laborales usan esto
peak = lc_peak(signal, fs, calibration_factor=sensitivity)

# Un único evento de ruido y una muestra de jornada (fragmentos de una grabación real)
event = signal
shift_sample = signal

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

### SEL: comparar eventos de distinta duración

Un paso de tren de 4 s y otro de 30 s no pueden compararse solo por su
$L_{Aeq}$ — el evento más largo entrega más energía al mismo nivel. El **nivel
de exposición sonora** comprime la energía del evento *completo* en
exactamente un segundo:

$$
L_E = L_{eq,T} + 10\log_{10}\frac{T}{T_0}, \qquad T_0 = 1\ \text{s}
$$

de modo que los eventos de cualquier duración resultan directamente
comparables, y $N$ eventos idénticos se suman como $+10\log_{10}N$. Es el
bloque básico de los modelos de ruido aeroportuario y ferroviario.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept_es.png" alt="Historia del nivel del paso de un vehículo con su Leq sobre el evento completo y el bloque SEL de un segundo con la misma energía" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept_es_dark.png" alt="Historia del nivel del paso de un vehículo con su Leq sobre el evento completo y el bloque SEL de un segundo con la misma energía" style="width:80%">

### Dosis de ruido: exposición sonora y LEX,8h

Las normativas laborales limitan la *dosis* diaria, no el nivel. IEC 61252 la
expresa como **exposición sonora** $E$ en pascales al cuadrado por hora — la
integral temporal de la presión ponderada A al cuadrado — y el **nivel
normalizado a 8 h** equivalente:

$$
E = \int_0^T p_A^2(t)\ dt \quad [\text{Pa}^2\text{h}], \qquad
L_{EX,8h} = 10\log_{10}\frac{E}{8\ \text{h} \cdot p_0^2}
$$

El ancla que conviene memorizar: **3,2 Pa²h ⇔ exactamente 90 dB durante 8 h**
(la suite de CI lo verifica). La mitad de dosis son −3 dB; el doble de
duración al mismo nivel son +3 dB.

### Parámetros de pico / evento / dosis

| Función | Parámetros clave | Devuelve | Ancla normativa |
| :--- | :--- | :--- | :--- |
| `lc_peak(x, fs, calibration_factor=1.0, dbfs=False)` | `dbfs=True` referencia el *pico* a fondo de escala (`1.0`), no el RMS | LCpeak [dB] | IEC 61672-1 §5.13, ráfagas de tono de la Tabla 5 |
| `sel(x, fs, weighting=None, ...)` | `weighting='A'` da el LAE | SEL [dB] | IEC 61672-1 Tabla 4 (columna LAE) |
| `sound_exposure(x, fs, duration_hours=None, ...)` | `duration_hours` trata `x` como muestra de ese periodo | E [Pa²h] | IEC 61252 |
| `lex_8h(x, fs, duration_hours=None, ...)` | misma semántica de muestreo | LEX,8h [dB] | IEC 61252 (≡ LEP,d) |

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

x = signal                                  # la grabación calibrada del inicio de la página
tnr = tone_to_noise_ratio(x, fs)            # pico más alto, o tone_freq=...
pr = prominence_ratio(x, fs, tone_freq=1000.0)
print(tnr.ratio_db, tnr.criterion_db, tnr.prominent)
```

Los métodos se apoyan en la **banda crítica** — el ancho de banda de análisis
del oído, $\Delta f_c = 25 + 75\ [1 + 1.4(f/1000)^2]^{0.69}$ Hz (162 Hz a
1 kHz): a un tono solo lo enmascara el ruido que hay *dentro* de su banda
crítica, así que ambos ratios comparan el tono exactamente con ese ruido, no
con todo el espectro.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_es.png" alt="Espectro promediado de un tono en ruido con la banda crítica sombreada y la relación tono-ruido anotada frente a su criterio de prominencia" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_es_dark.png" alt="Espectro promediado de un tono en ruido con la banda crítica sombreada y la relación tono-ruido anotada frente a su criterio de prominencia" style="width:80%">

Un TNR por encima de $8 + 8.33\log_{10}(1000/f_t)$ dB (8 dB de 1 kHz hacia
arriba) clasifica el tono como *prominente*; el criterio del PR es
$9 + 10\log_{10}(1000/f_t)$ dB. Las frecuencias bajas reciben umbrales más
altos porque unas bandas relativamente más anchas enmascaran más.

ECMA-74 (que delega la evaluación tonal en ECMA-418-1) también fija dónde medir alrededor de un equipo:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_tonality_positions_es.svg" alt="Posiciones de medida de emisión ECMA-74: micrófono del operador sentado a 0,25 m y 1,20 m, y las cuatro posiciones de observador a 1 m" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_tonality_positions_es_dark.svg" alt="Posiciones de medida de emisión ECMA-74: micrófono del operador sentado a 0,25 m y 1,20 m, y las cuatro posiciones de observador a 1 m" style="width:92%">

Los tonos secundarios próximos en la misma banda crítica se combinan según el
apartado 11.6; para complejos armónicos evalúa cada componente (`tone_freq=`).
Ambos métodos trabajan sobre espectros promediados RMS con ventana Hann y no
necesitan calibración absoluta (los ratios son diferencias de nivel).

### Parámetros de `tone_to_noise_ratio()` / `prominence_ratio()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D | cualquiera (vale sin calibrar) | ≥ `fs/resolution_hz` muestras | Los ratios son diferencias de nivel: la calibración se cancela |
| `fs` | int | Hz | > 0 | |
| `tone_freq` | float, opcional | Hz | 89,1–11 200; por defecto `None` | `None` evalúa el pico más alto del rango de interés |
| `resolution_hz` | float | Hz | > 0; por defecto `1.0` | La banda del tono debe quedar dentro del 15 % de la banda crítica (apartado 11.2) |

Ambos devuelven un `ToneAssessment(frequency, ratio_db, criterion_db, prominent)`.

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile_es.png" alt="Perfil LAeq urbano sintético de 24 horas con las bandas de día, tarde y noche, los niveles por periodo ponderados con +5 y +10 dB y el Lden resultante" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile_es_dark.png" alt="Perfil LAeq urbano sintético de 24 horas con las bandas de día, tarde y noche, los niveles por periodo ponderados con +5 y +10 dB y el Lden resultante" style="width:80%">

### Parámetros de `lden()` / `ldn()` / `composite_rating_level()`

| Función | Parámetros clave | Notas |
| :--- | :--- | :--- |
| `lden(lday, levening, lnight, hours=(12, 4, 8))` | LAeq por periodo [dB]; `hours` debe sumar 24 | +5 dB tarde, +10 dB noche (3.6.4) |
| `ldn(lday, lnight, hours=(15, 9))` | | +10 dB noche (3.6.5) |
| `composite_rating_level(periods)` | iterable de `(level_db, hours, adjustment_db)` | Fórmulas generales (5)-(6); ajustes según la Tabla A.1 |

Dónde pones el micrófono cambia el número: ISO 1996-2 fija las posiciones del receptor y sus correcciones de fachada:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_env_measurement_es.svg" alt="Posiciones de medida de ruido ambiental según ISO 1996-2: campo libre, a 2 m de la fachada y enrasado, con sus correcciones" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_env_measurement_es_dark.svg" alt="Posiciones de medida de ruido ambiental según ISO 1996-2: campo libre, a 2 m de la fachada y enrasado, con sus correcciones" style="width:92%">

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

### Parámetros de `OctaveFilterBank.spectrogram()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | unidades digitales | no vacío | 2D devuelve `(channels, bands, frames)` |
| `window_time` | float | s | > 0; por defecto `0.125` | Longitud de la ventana (0,125 s replica Fast) |
| `overlap` | float | — | 0 ≤ overlap < 1; por defecto `0.5` | Fracción de solape entre ventanas (0 = sin solape) |
| `mode` | str | — | `'rms'` (por defecto) o `'peak'` | Detector por ventana |
| `detrend` | bool | — | por defecto `True` | Elimina el offset DC de cada banda antes del nivel (mejora la precisión en graves) |
| `zero_phase` | bool | — | por defecto `False` | Filtrado hacia delante y atrás (solo offline) |
| `calibration_factor` / `dbfs` | — | — | solo constructor | Se fijan en `OctaveFilterBank(...)`, no por llamada |

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
