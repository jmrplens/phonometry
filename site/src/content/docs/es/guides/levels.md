---
title: "Niveles integrados y estadísticos"
description: "Leq, LAeq, percentiles L10/L50/L90, LCpeak/SEL y dosis de ruido (IEC 61252), Lden y niveles de evaluación (ISO 1996-1), y espectrogramas de octava."
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
| `calibration_factor` | float | Pa por unidad digital | por defecto `1.0` | De `sensitivity()` |
| `dbfs` | bool | — | por defecto `False` | `True`: 0 dBFS = seno RMS a fondo de escala; ignora la calibración |

## Niveles percentiles (LN)

`ln_levels` calcula niveles estadísticos a partir de la envolvente con
ponderación temporal: **L10** es el nivel superado el 10 % del tiempo (picos de
eventos), **L50** la mediana y **L90** el nivel de fondo.

```python
import numpy as np
from phonometry import ln_levels

# Un tono constante da L10 = L50 = L90; los percentiles solo cuentan algo con un
# nivel *fluctuante*. Sintetizamos 3 s alternando entre medio segundo tranquilo
# y otro ~10 dB más fuerte para que los estadísticos se separen.
fs = 48000
rng = np.random.default_rng(0)
segment = fs // 2                                  # 0.5 s por nivel
quiet = 0.02 * rng.standard_normal(segment)        # fondo
loud = 0.06 * rng.standard_normal(segment)         # eventos ~10 dB más fuertes
varying = np.tile(np.concatenate([quiet, loud]), 3)

stats = ln_levels(varying, fs, n=(10, 50, 90), weighting="A")
print(f"LA10={stats[10]:.1f}  LA50={stats[50]:.1f}  LA90={stats[90]:.1f} dB")
# LA10=66.6  LA50=65.2  LA90=58.5 dB  -> L10 (eventos) > L50 (mediana) > L90 (fondo)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_es.svg" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_es_dark.svg" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%">

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

# Usa `recording`, `fs` y `sensitivity` del snippet de Leq anterior.

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept_es.svg" alt="Historia del nivel del paso de un vehículo con su Leq sobre el evento completo y el bloque SEL de un segundo con la misma energía" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept_es_dark.svg" alt="Historia del nivel del paso de un vehículo con su Leq sobre el evento completo y el bloque SEL de un segundo con la misma energía" style="width:80%">

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

`lex_8h` califica *una* grabación; componer una jornada laboral completa a
partir de muestras por tarea o por función —con el presupuesto normativo de
incertidumbre de la ISO 9612— continúa en
[Exposición al ruido en el trabajo](/phonometry/es/guides/occupational-exposure/).

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile_es.svg" alt="Perfil LAeq urbano sintético de 24 horas con las bandas de día, tarde y noche, los niveles por periodo ponderados con +5 y +10 dB y el Lden resultante" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile_es_dark.svg" alt="Perfil LAeq urbano sintético de 24 horas con las bandas de día, tarde y noche, los niveles por periodo ponderados con +5 y +10 dB y el Lden resultante" style="width:80%">

### Parámetros de `lden()` / `ldn()` / `composite_rating_level()`

| Función | Parámetros clave | Notas |
| :--- | :--- | :--- |
| `lden(lday, levening, lnight, hours=(12, 4, 8))` | LAeq por periodo [dB]; `hours` debe sumar 24 | +5 dB tarde, +10 dB noche (3.6.4) |
| `ldn(lday, lnight, hours=(15, 9))` | | +10 dB noche (3.6.5) |
| `composite_rating_level(periods)` | iterable de `(level_db, hours, adjustment_db)` | Fórmulas generales (5)-(6); ajustes según la Tabla A.1 |

Dónde pones el micrófono cambia el número: ISO 1996-2 fija las posiciones del receptor y sus correcciones de fachada. El diagrama es contexto de medida; aplica las correcciones a tus niveles antes del análisis:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_env_measurement_es.svg" alt="Posiciones de medida de ruido ambiental según ISO 1996-2: campo libre, a 2 m de la fachada y enrasado, con sus correcciones" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_env_measurement_es_dark.svg" alt="Posiciones de medida de ruido ambiental según ISO 1996-2: campo libre, a 2 m de la fachada y enrasado, con sus correcciones" style="width:92%">

Combínalo con `laeq()` por periodo para ir de grabaciones a Lden, y con los
veredictos `tone_to_noise_ratio()` / `prominence_ratio()` de
[Tonos discretos prominentes](/phonometry/es/guides/tone-prominence/) para
justificar ajustes tonales.

## Determinación de niveles: ajuste tonal, ruido residual e incertidumbre (ISO 1996-2)

ISO 1996-2:2017 es la parte de **determinación**: cómo el nivel medido se
convierte en nivel de valoración y se reporta con su incertidumbre. La *suma* del
nivel de valoración y las penalizaciones por periodo están en ISO 1996-1 (arriba);
ISO 1996-2 aporta el ajuste tonal, la corrección de ruido residual y el
presupuesto de incertidumbre.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonal_audibility_es.svg" alt="Ajuste tonal Kt de ISO 1996-2 como función a tramos de la audibilidad tonal: cero por debajo de 4 dB, creciendo linealmente hasta 6 dB entre 4 y 10 dB, y 6 dB por encima, con los cuatro ejemplos resueltos del Anexo C.5 y un tono de rango medio marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonal_audibility_es_dark.svg" alt="Ajuste tonal Kt de ISO 1996-2 como función a tramos de la audibilidad tonal: cero por debajo de 4 dB, creciendo linealmente hasta 6 dB entre 4 y 10 dB, y 6 dB por encima, con los cuatro ejemplos resueltos del Anexo C.5 y un tono de rango medio marcados" style="width:80%">

**Ajuste tonal (método de ingeniería, Anexo C).** A partir del nivel tonal
sumado en energía $L_{pt}$ y el nivel de ruido enmascarante $L_{pn}$ en la banda
crítica alrededor de un tono, la audibilidad sobre el umbral de enmascaramiento es
$\Delta L_{ta} = L_{pt} - L_{pn} + 2 + \lg[1 + (f_c/502)^{2.5}]$ dB (Fórmula (C.3)),
y el ajuste es $K_t = 0$ para $\Delta L_{ta} < 4$, $K_t = \Delta L_{ta} - 4$ para
$4 \le \Delta L_{ta} \le 10$ y $K_t = 6$ por encima (Fórmulas (C.4)–(C.6)). El
ancho de banda crítico es 100 Hz hasta 500 Hz y el 20 % de $f_c$ por encima
(Tabla C.1). El **método de cribado** en tercios de octava (`tonal_seeking_survey`)
marca una banda que supera a ambas vecinas en 15/8/5 dB (baja/media/alta), y
`tonal_adjustment_from_mean_audibility` mapea la audibilidad media de ISO/PAS 20065
a $K_t$ (Tabla J.1).

**Corrección de ruido residual (Cláusula 10.4).** `residual_sound_correction()`
aplica $L = 10\lg(10^{L'/10} - 10^{L_\text{res}/10})$ (Fórmula (16)). Con un
residual dentro de 3 dB del nivel medido no se permite corrección alguna: el
valor reportable es entonces el nivel medido *sin corregir* $L'$, como cota
superior del sonido específico (expuesto como `reportable_upper_bound`, con
`reliable=False`). `gaussian_residual_level()` estima el residual a partir de
niveles percentiles (Anexo I) y rechaza ordenaciones de percentiles
invertidas.

**Incertidumbre de medición (Cláusula 4, Anexo F).**
`combined_standard_uncertainty()` forma $u = \sqrt{\sum (c_j u_j)^2}$ (Fórmula (2))
y `environmental_expanded_uncertainty()` aplica $k = 2$ (95 %) o $k = 1.3$ (80 %);
`residual_correction_uncertainty()` lleva la sensibilidad de la corrección residual
(Fórmulas (F.7)/(F.8)) y `uncertainty_from_repeated_measurements()` la
incertidumbre típica de mediciones repetidas — la vía primaria en el dominio
de energía (Fórmulas (17)+(19)), con el sustituto en niveles de la Nota 2
(Fórmula (20)) reportado al lado como `approximate_uncertainty` y un aviso
cuando los niveles se dispersan más de 3 dB, donde el sustituto se infla
groseramente.

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
from phonometry import assess_tonal_audibility

# ISO 1996-2:2007 Anexo C.5, Ejemplo 2 (dos tonos cerca de 400 Hz):
res = assess_tonal_audibility(tone_level=54.1, masking_noise_level=45.2,
                              centre_frequency=430.0)
print(res.audibility, res.adjustment)   # ΔLta ≈ 11,1 dB -> Kt = 6 dB
res.plot()
plt.show()
```
</details>

```python
from phonometry import (
    assess_tonal_audibility, residual_sound_correction,
    combined_standard_uncertainty, environmental_expanded_uncertainty,
)

kt = assess_tonal_audibility(54.1, 45.2, 430.0).adjustment      # 6 dB
corr = residual_sound_correction(measured_level=58.0, residual_level=50.0)
u = combined_standard_uncertainty([0.59, 0.3, 2.0, 0.40, 0.38])  # 2,18 dB (G.2)
environmental_expanded_uncertainty(u)                            # 4,36 dB (k = 2)
```

## Espectrograma de octavas (niveles vs tiempo)

Análisis de octava fraccional en tiempo corto: un nivel por banda y ventana,
alineado en el tiempo entre bandas.

```python
from phonometry import OctaveFilterBank

# Usa `recording` del snippet de Leq anterior.
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

# Usa `levels`, `freq` y `times` del snippet del espectrograma anterior.
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
detalles de la envolvente. Las estrategias ocupacionales de la ISO 9612
continúan en
[Exposición al ruido en el trabajo](/phonometry/es/guides/occupational-exposure/),
los veredictos de prominencia tonal de ECMA-418-1 en
[Tonos discretos prominentes](/phonometry/es/guides/tone-prominence/), y las
curvas isofónicas de ISO 226 viven con las métricas de percepción en
[Sonoridad](/phonometry/es/guides/loudness/).

---

**Normas.** IEC 61672-1:2013, *Electroacoustics — Sound level meters —
Part 1: Specifications* — la ponderación temporal Fast/Slow/Impulse de la
envolvente de `ln_levels`, el pico ponderado C del §5.13 (verificado contra
las ráfagas de tono de la Tabla 5) y el nivel de exposición sonora verificado
contra la columna LAE de la Tabla 4. IEC 61252, *Electroacoustics —
Specifications for personal sound exposure meters* — la exposición sonora E en
Pa²h y el nivel normalizado a 8 h LEX,8h (≡ LEP,d), anclados en
3,2 Pa²h ⇔ exactamente 90 dB. ISO 1996-1:2016, *Acoustics — Description,
measurement and assessment of environmental noise — Part 1: Basic quantities
and assessment procedures* — Lden (3.6.4), Ldn (3.6.5) y el nivel de
evaluación compuesto de jornada completa del apartado 6.5 (Fórmulas 5-6,
ajustes de la Tabla A.1).

## Véase también

- Referencia de la API: [`metrology.levels`](/phonometry/es/reference/api/levels/levels/), [`environmental.measurement`](/phonometry/es/reference/api/environment/measurement/) y [`environmental.rating`](/phonometry/es/reference/api/environment/rating/).
