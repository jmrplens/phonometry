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

# recording: una captura de micrófono calibrada (Pa) — grabada con tu cadena de medición. Sintetizada aquí para que la guía funcione por sí sola.
fs = 48000
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
sensitivity = 1.0                                    # calibration_factor (ver Calibración)

# Nivel continuo equivalente de toda la grabación
level = leq(recording, calibration_factor=sensitivity)

# Leq ponderado A (la métrica estándar de ruido ambiental)
la = laeq(recording, fs, calibration_factor=sensitivity)
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

# Un tono constante da L10 = L50 = L90; los percentiles solo cuentan algo con un
# nivel *fluctuante*. Sintetizamos 3 s alternando entre medio segundo tranquilo
# y otro ~10 dB más fuerte para que los estadísticos se separen.
rng = np.random.default_rng(0)
segment = fs // 2                                  # 0.5 s por nivel
quiet = 0.02 * rng.standard_normal(segment)        # fondo
loud = 0.06 * rng.standard_normal(segment)         # eventos ~10 dB más fuertes
varying = np.tile(np.concatenate([quiet, loud]), 3)

stats = ln_levels(varying, fs, n=(10, 50, 90), weighting="A")
print(f"LA10={stats[10]:.1f}  LA50={stats[50]:.1f}  LA90={stats[90]:.1f} dB")
# LA10=66.6  LA50=65.2  LA90=58.5 dB  -> L10 (eventos) > L50 (mediana) > L90 (fondo)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_es.png" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_es_dark.png" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%">

*L10 sigue los picos de los eventos, L50 el nivel mediano y L90 el fondo.*

Opciones: `mode` selecciona la ponderación temporal de la envolvente (`'fast'`, `'slow'`,
`'impulse'`), `weighting` aplica antes la ponderación A/C, y
`calibration_factor`/`dbfs` se comportan como en `leq`. El transitorio de ataque
del integrador (~5τ) se descarta antes de calcular los percentiles, de modo que
la rampa inicial de asentamiento no cuenta en los percentiles bajos.

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
peak = lc_peak(recording, fs, calibration_factor=sensitivity)

# Un único evento de ruido y una muestra de jornada (fragmentos de una grabación real)
event = recording
shift_sample = recording

# Nivel de exposición sonora: nivel del evento normalizado a 1 s (LAE)
lae = sel(event, fs, weighting="A", calibration_factor=sensitivity)

# Dosis diaria de ruido (IEC 61252): exposición en Pa²·h y LEX,8h / LEP,d
E = sound_exposure(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
lex = lex_8h(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
```

`lc_peak` está verificado contra las respuestas de referencia de ciclo
único/semiciclo de la Tabla 5 de IEC 61672-1:2013, `sel` contra la columna LAE
de la Tabla 4, y las funciones de dosis contra las anclas de IEC 61252
(3,2 Pa²h ↔ exactamente 90 dB). `lc_peak` sobremuestrea (polifásico) la señal
ponderada C por `oversample` (por defecto `8`) antes de tomar el máximo,
recuperando el verdadero pico inter-muestra: un máximo en rejilla subestima los
tonos de HF sostenidos hasta ~1,15 dB (un tono de 8 kHz a 48 kHz tiene solo
6 muestras/ciclo). Usa `oversample=1` para detectar el pico en la rejilla
original. Con `duration_hours`, la entrada se trata como muestra representativa
de ese periodo de exposición; sin él, la entrada es el evento completo.

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

## Estrategias de exposición al ruido en el trabajo e incertidumbre (ISO 9612)

`lex_8h`, más arriba, convierte *una* grabación en un nivel diario. La
ISO 9612:2009 —el método de ingeniería (clase de exactitud 2)— es el diseño de
la medición *en torno* a esa primitiva: cómo muestrear una jornada laboral real,
cómo combinar las partes y cómo adjuntar la incertidumbre normativa que necesita
todo informe de higiene laboral. El módulo `occupational_exposure` añade las tres
**estrategias de medición** y el presupuesto de incertidumbre del **anexo C**
sobre la maquinaria del promediado en energía.

La estrategia *basada en tareas* (apartado 9) divide la jornada nominal en
tareas, toma $I \ge 3$ muestras por tarea y suma en energía las contribuciones de
cada tarea

$$
L_{EX,8h,m} = L_{p,A,eqT,m} + 10 \log_{10}(T_m/T_0), \qquad T_0 = 8\ \text{h},
$$

de modo que una tarea ruidosa pero corta contribuye poco. Las estrategias
*basada en la función* (apartado 10) y *de jornada completa* (apartado 11) toman
en cambio $N \ge 5$ (o tres jornadas completas) muestras aleatorias sobre un grupo
de exposición homogéneo y normalizan la duración efectiva de la jornada. El nivel
diario es el mismo en ambos casos; las estrategias difieren en cómo se construye
la **incertidumbre**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/exposure_uncertainty_es.png" alt="Exposición por tareas del anexo D de la ISO 9612: las tres contribuciones de tarea a LEX,8h como barras, la línea del LEX,8h diario sumado en energía y la banda del límite superior unilateral al 95 % LEX,8h + U por encima" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/exposure_uncertainty_es_dark.png" alt="Exposición por tareas del anexo D de la ISO 9612: las tres contribuciones de tarea a LEX,8h como barras, la línea del LEX,8h diario sumado en energía y la banda del límite superior unilateral al 95 % LEX,8h + U por encima" style="width:80%">

```python
from phonometry.occupational_exposure import (
    Task, task_based_exposure, job_based_exposure, full_day_exposure,
)

# ISO 9612 anexo D — la jornada de un soldador dividida en tres tareas. El nivel
# de cada tarea es el promedio en energía de sus muestras Lp,A,eqT; las
# duraciones llevan un rango medido.
tasks = [
    Task(samples=(70.0,), duration_hours=1.5, label="planning/breaks"),
    Task(samples=(80.1, 82.2, 79.6), duration_hours=5.0,
         duration_range=(4.0, 6.0), label="welding"),
    Task(samples=(86.5, 92.4, 89.3, 93.2, 87.8, 86.2), duration_hours=1.5,
         duration_range=(1.0, 2.0), label="cutting/grinding"),
]
res = task_based_exposure(tasks, include_duration_uncertainty=False, warn=False)
print(f"LEX,8h = {res.lex_8h:.1f} dB   U = {res.expanded_uncertainty:.1f} dB")
# LEX,8h = 84.3 dB   U = 2.7 dB
print(f"one-sided 95 % upper limit LEX,8h + U = {res.upper_limit:.1f} dB")   # 87.0 dB
for t in res.tasks:
    print(f"  {t.label:<16} Lp,A,eqT = {t.lp_aeqt:5.1f}   contributes {t.lex_8h_contribution:5.1f} dB")
#   planning/breaks  Lp,A,eqT =  70.0   contributes  62.7 dB
#   welding          Lp,A,eqT =  80.8   contributes  78.7 dB
#   cutting/grinding Lp,A,eqT =  90.1   contributes  82.8 dB

# La misma jornada medida basada en la función (anexo E) y de jornada completa
# (anexo F): ambas usan el presupuesto de muestreo Ec C.9 / Tabla C.4 con
# k = 1.65 (unilateral 95 %).
job = job_based_exposure([88.1, 86.1, 89.7, 86.5, 91.1, 86.7], effective_duration_hours=7.5)
full = full_day_exposure([88.0, 91.9, 87.6, 90.4, 89.0, 88.4], effective_duration_hours=9.25)
print(f"job      LEX,8h = {job.lex_8h:.1f} dB   U = {job.expanded_uncertainty:.1f} dB")
# job      LEX,8h = 88.2 dB   U = 3.8 dB
print(f"full-day LEX,8h = {full.lex_8h:.1f} dB   U = {full.expanded_uncertainty:.1f} dB")
# full-day LEX,8h = 90.1 dB   U = 3.4 dB
```

Conviene detallar dos sutilezas. Primero, el factor de cobertura es $k = 1.65$
para un intervalo **unilateral** al 95 % (apartado 14), porque al higienista solo
le importa la cota *superior*: `res.upper_limit` = $L_{EX,8h} + U$ es el valor por
debajo del cual queda el 95 % de las mediciones, el número que se compara con un
valor de acción. Segundo, los métodos por tareas y por función ponderan de forma
distinta la *misma* dispersión de muestras. La incertidumbre de muestreo de la
tarea $u_{1a}$ (Ec. C.6) divide la suma de desviaciones al cuadrado entre
$I(I-1)$ —el error típico de la media, menor en un factor $\sqrt{I}$—, mientras
que la incertidumbre de muestreo por función/jornada completa $u_1$ (Ec. C.12) es
la desviación típica muestral simple con denominador $N-1$, cuya contribución
$c_1 u_1$ se lee luego de la **Tabla C.4** en función de $(N, u_1)$. La misma
dispersión bruta infla, por tanto, más la estimación por función, que es la
penalización que el estándar impone a un muestreo más grueso y con menos
muestras. (El $L_{EX,8h}$ por función impreso es $88.2$ dB donde el anexo E
declara $88.1$: el estándar redondea el nivel de jornada efectiva a $88.4$ antes
de la normalización de la duración; la biblioteca lo mantiene sin redondear.)

Cuando las muestras de una tarea abarcan **3 dB o más** (apartado 9.3), o la
contribución por función $c_1 u_1$ supera 3,5 dB (apartado 10.4), o se cubren
demasiado pocos trabajadores (duración acumulada de la Tabla 1), el resultado fija
`sampling_advisory=True` y, con `warn=True`, emite una `ExposureWarning` que
recomienda más mediciones. Los niveles de pico $L_{p,Cpeak}$ se declaran **sin**
incertidumbre —el anexo C no da método para ellos (Tabla C.5, Nota 1)—, así que
la incertidumbre de pico queda fuera del alcance. Los tres ejemplos resueltos de
los anexos D/E/F anteriores se reproducen con la precisión impresa de la norma
(el redondeo final del anexo E se explica más arriba), y la teoría se deriva
en la página de [Teoría](/phonometry/es/reference/theory/).

### Parámetros de `task_based_exposure()` / `job_based_exposure()` / `full_day_exposure()`

| Parámetro | Se aplica a | Tipo | Unidades | Rango / def. | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tasks` | tarea | lista de `Task` | — | ≥ 1 | Cada `Task` tiene `samples`, `duration_hours`, `duration_range`/`duration_samples` opcionales, `label`, `instrument` |
| `samples` | función / jornada | secuencia | dB | ≥ 2 (≥ 5 / ≥ 3 recomendado) | Muestras aleatorias `Lp,A,eqT` |
| `effective_duration_hours` | función / jornada | float | h | > 0 | Duración efectiva de la jornada $T_e$ |
| `instrument` | todas | str | — | `'class1'`, `'class2'`, `'personal_exposimeter'` (def.) | Selecciona $u_2$ (Tabla C.5) |
| `u3` | todas | float | dB | def. `1.0` | Incertidumbre de posición del micrófono (apartado C.6) |
| `include_duration_uncertainty` | tarea | bool | — | def. `True` | `False` omite el término $(c_{1b}u_{1b})^2$ (anexo D caso a) |
| `n_workers` / `sample_duration_hours` | función | int / float | — / h | def. `None` | Comprobación de duración acumulada de la Tabla 1 |
| `warn` | todas | bool | — | def. `True` | Emitir `ExposureWarning` para los avisos de muestreo |

Las tres devuelven un `ExposureResult` con `lex_8h`, `combined_standard_uncertainty`
$u$, `expanded_uncertainty` $U = 1.65\ u$, `upper_limit` = $L_{EX,8h} + U$,
`sampling_advisory` y (basada en tareas) el desglose por tarea en `tasks`.

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
import numpy as np
from phonometry import tone_to_noise_ratio, prominence_ratio

fs = 48000
rng = np.random.default_rng(0)
t = np.arange(fs) / fs
x = np.sin(2 * np.pi * 1000 * t) + 0.05 * rng.standard_normal(fs)  # tono de 1 kHz en ruido
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
levels, freq, times = bank.spectrogram(recording, window_time=0.125, overlap=0.5)
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
