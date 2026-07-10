---
title: "Psicoacústica"
description: "Sonoridad de Zwicker (ISO 532-1), Moore-Glasberg (ISO 532-2/3) y Sottek (ECMA-418-2), sharpness (DIN 45692), curvas isofónicas de ISO 226, y tonalidad y aspereza de ECMA-418-2."
---

Las métricas de nivel dicen cuánta *presión sonora* hay; las métricas
psicoacústicas dicen qué *percibe* realmente quien escucha. Esta página cubre
la sonoridad (ISO 532-1), el sharpness (DIN 45692) y las curvas isofónicas de
tonos puros (ISO 226), y luego los modelos avanzados de sonoridad, tonalidad
y aspereza de Moore-Glasberg (ISO 532-2/3) y del modelo de Sottek
(ECMA-418-2). Las métricas de habla tienen guía propia: el STI/STIPA de canal
de transmisión en el
[índice de transmisión del habla](/phonometry/es/guides/speech-transmission/) y
el SII basado en audibilidad en el
[índice de inteligibilidad del habla](/phonometry/es/guides/speech-intelligibility/).

## Sonoridad en sonos (ISO 532-1, Zwicker)

Los decibelios comprimen la percepción: 10 dB más se leen como *el doble de
sonoro*, y dos sonidos con el mismo dB(A) pueden diferir audiblemente según
cómo se reparta su energía entre las **bandas críticas** del oído. El método de
Zwicker modela explícitamente la cadena auditiva — transmisión del oído
externo/medio, análisis en bandas críticas sobre la escala de 24 Bark,
pendientes de enmascaramiento dependientes del nivel — y produce la
**sonoridad N en sonos**, una escala de razón: 4 sonos es el doble de sonoro
que 2 sonos. Por definición, un tono de 1 kHz a 40 dB SPL es 1 sono, y cada
+10 fonios duplica el valor en sonos.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_zwicker_es.svg" alt="Cadena de sonoridad de Zwicker ISO 532-1: 28 niveles de banda de tercio de octava, transmisión y agrupación de bandas críticas inferiores, sonoridad de núcleo de las 20 bandas críticas, sonoridad específica sobre Bark, integrada en la sonoridad total N en sonios y el nivel de sonoridad en fonios" style="width:78%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_zwicker_es_dark.svg" alt="Cadena de sonoridad de Zwicker ISO 532-1: 28 niveles de banda de tercio de octava, transmisión y agrupación de bandas críticas inferiores, sonoridad de núcleo de las 20 bandas críticas, sonoridad específica sobre Bark, integrada en la sonoridad total N en sonios y el nivel de sonoridad en fonios" style="width:78%">

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_pattern_es.png" alt="Patrones de sonoridad específica sobre la escala Bark para un sonido de banda estrecha de 1 kHz y un sonido de banda ancha con el mismo nivel de banda" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_pattern_es_dark.png" alt="Patrones de sonoridad específica sobre la escala Bark para un sonido de banda estrecha de 1 kHz y un sonido de banda ancha con el mismo nivel de banda" style="width:80%">

*Mismo nivel de banda, sonoridad muy distinta: la energía repartida entre
muchas bandas críticas (rojo) suma muchos más sonos que el mismo nivel
concentrado en una sola banda (azul). El área bajo N'(z) es la sonoridad
total.*

```python
import numpy as np
from phonometry import loudness_zwicker, loudness_zwicker_from_spectrum

# Una grabación cruda y su calibración para que la guía funcione por sí sola
fs = 48000
x = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)   # cualquier grabación (unidades digitales)
sens = 1.0                                                # calibration_factor a pascales
levels_28 = np.full(28, 60.0)                             # 28 niveles de tercio de octava (dB)

# Desde una grabación sin calibrar: calibration_factor convierte unidades digitales en Pa
res = loudness_zwicker(x, fs, field="free", calibration_factor=sens)
print(f"N = {res.loudness:.1f} sone  ({res.loudness_level:.0f} phon)")   # 13.1 sone (77 phon)

# Señales variables en el tiempo: la sonoridad percentil N5 es el
# estándar para informes
res = loudness_zwicker(x, fs)          # stationary=False (por defecto)
print(f"{res.n5:.1f} {res.n10:.1f} {res.loudness:.1f}")   # 13.1 13.1 13.1 — N5, N10, Nmax

# Desde 28 niveles de tercio de octava (25 Hz .. 12.5 kHz)
res = loudness_zwicker_from_spectrum(levels_28, field="diffuse")

res.plot()   # N'(z) sobre la escala Bark — el patrón de sonoridad específica (requiere matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — el patrón de sonoridad específica N'(z) desde el resultado:
res.plot()
plt.show()

# O reproduce la figura a mano — dos patrones con el mismo nivel de banda (60 dB),
# la energía repartida entre muchas bandas críticas frente a la banda de 1 kHz:
narrow = loudness_zwicker_from_spectrum(np.r_[np.full(16, -60.0), 60.0, np.full(11, -60.0)])
broad = loudness_zwicker_from_spectrum(np.full(28, 60.0))
z = np.arange(1, narrow.specific.size + 1) * 0.1          # eje Bark
fig, ax = plt.subplots()
for r, color, label in [
    (broad, "#ff7f0e", f"Banda ancha  N = {broad.loudness:.1f} sone"),
    (narrow, "#1f77b4", f"Banda estrecha 1 kHz  N = {narrow.loudness:.1f} sone"),
]:
    ax.fill_between(z, r.specific, color=color, alpha=0.3)
    ax.plot(z, r.specific, color=color, label=label)
ax.set_xlabel("Tasa de banda crítica z [Bark]")
ax.set_ylabel("Sonoridad específica N' [sone/Bark]")
ax.legend()
plt.show()
```

</details>

La implementación es un port de sala limpia del **programa de referencia
normativo** de la norma (Anexo A.4): las doce tablas de datos son exactas
dígito a dígito y el conjunto completo de validación del Anexo B se ejecuta en
CI — el caso de prueba estacionario reproduce el valor publicado hasta el
último dígito impreso, y las trazas N(t) de los pulsos de tono se mantienen
dentro de la banda de tolerancia del 5 % por muestra que fija la norma.

### Parámetros de `loudness_zwicker()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D | Pa (tras calibración) | ≥ 8 ms a 48 kHz | Se remuestrea internamente a 48 kHz si es necesario |
| `fs` | int | Hz | > 0 | |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Corrección de campo sonoro (Tabla A.5) |
| `stationary` | bool | — | por defecto `False` | `True`: un único N a partir del espectro promediado |
| `calibration_factor` | float | Pa por unidad digital | por defecto `1.0` | De `sensitivity()` |

Devuelve un dataclass `ZwickerLoudness`: `loudness` (N, sonos),
`loudness_level` (fonios), `specific` (N′(z), 240 bins de 0,1 Bark) y, para los
análisis variables en el tiempo, `n5`, `n10`, `time`, `loudness_vs_time`
(traza a 500 Hz).

## Sharpness en acum (DIN 45692)

Dos sonidos pueden ser igual de sonoros y aun así uno se percibe más
"afilado" — siseante, metálico — porque su sonoridad se sitúa más arriba en la
escala Bark. El sharpness es el primer momento del patrón de sonoridad
específica ponderado por g(z):

$$
S = k\ \frac{\int_0^{24} N'(z)\ g(z)\ z\ dz}{\int_0^{24} N'(z)\ dz}\ \text{acum}
$$

con $g(z) = 1$ hasta 15,8 Bark y creciendo exponencialmente a partir de ahí, y
$k$ normalizada para que el sonido de referencia — ruido de ancho de banda
crítico a 1 kHz, 60 dB — sea exactamente **1,00 acum** (DIN 45692 apartado 6;
la $k = 0{,}108$ derivada queda dentro de la ventana normativa 0,105–0,115).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting_es.png" alt="Ponderación de nitidez g(z) de DIN 45692 frente a la razón de banda crítica en eje logarítmico, comparando las curvas DIN, von Bismarck y Aures con los codos de 15,8 y 15 Bark marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting_es_dark.png" alt="Ponderación de nitidez g(z) de DIN 45692 frente a la razón de banda crítica en eje logarítmico, comparando las curvas DIN, von Bismarck y Aures con los codos de 15,8 y 15 Bark marcados" style="width:80%">

```python
from phonometry import sharpness_din

# Usa `x`, `fs` y `sens` del snippet anterior.
s = sharpness_din(x, fs, calibration_factor=sens)      # acum
s_aures = sharpness_din(x, fs, method="aures")          # variante del Anexo B
```

CI verifica los valores objetivo de la Tabla A.2 (desde 0,38 acum a 250 Hz
hasta 2,82 acum a 4 kHz) dentro de la tolerancia del 5 % / 0,05 acum de la
norma.

## Nivel de sonoridad de tonos puros (ISO 226:2023)

Las curvas isofónicas normales relacionan el SPL de un tono puro con su *nivel
de sonoridad* percibido en fonios (el SPL de un tono de 1 kHz igual de fuerte).
`equal_loudness_contour(phon)` evalúa la Fórmula (1) de ISO 226:2023 en las 29
frecuencias preferentes de tercio de octava de la Tabla 1,
`loudness_level(spl, frequency)` es la inversa exacta (Fórmula 2) y
`hearing_threshold()` devuelve la columna del umbral de audición:

```python
from phonometry import equal_loudness_contour, loudness_level

freqs, spl = equal_loudness_contour(40.0)   # la clásica isofónica de 40 fonios
phon = loudness_level(73.0, 63.0)           # 73 dB @ 63 Hz -> 40 fonios
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/equal_loudness_contours_es.png" alt="Curvas isofónicas normales de ISO 226:2023 de 20 a 90 fonios con la curva del umbral de audición" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/equal_loudness_contours_es_dark.png" alt="Curvas isofónicas normales de ISO 226:2023 de 20 a 90 fonios con la curva del umbral de audición" style="width:80%">

Validez según el apartado 4.1: 20–90 fonios (80 fonios por encima de 4 kHz); la
implementación se verifica en CI contra las tablas del Anexo B. Ojo: esto es la
sonoridad de *tonos puros* — la sonoridad de señales arbitrarias en sonos es lo
que calculan los modelos ISO 532 de esta página.

## Modelos avanzados de sonoridad y calidad sonora

La ISO 532-1 de arriba es uno de los **tres** modelos de sonoridad que incluye
phonometry, y la sonoridad es solo la mitad de la historia de la calidad
sonora: dos sonidos igual de sonoros pueden diferir aún en cuán *tonales* o cuán
*ásperos* son. Esta sección añade la sonoridad de **Moore-Glasberg** de
ISO 532-2/532-3 y la sonoridad, la tonalidad y la aspereza del **modelo de
Sottek** de ECMA-418-2:2025.

### Elegir un modelo de sonoridad

| Modelo | Norma | Estacionario / variable en el tiempo | Salida | Cuándo usarlo |
| :--- | :--- | :--- | :--- | :--- |
| Zwicker | ISO 532-1:2017 | ambos | sonos | Método de referencia; entrada en tercios de octava; rápido y muy citado |
| Moore-Glasberg | ISO 532-2:2017 | estacionario | sonos | Patrón de excitación roex; mejor para tonos y con suma binaural explícita |
| Moore-Glasberg-Schlittenlacher | ISO 532-3:2023 | variable en el tiempo | sonos (STL/LTL) | Sonoridad variable en el tiempo con trazas de corto/largo plazo y el pico N_max |
| Sottek (modelo auditivo) | ECMA-418-2:2025 | variable en el tiempo | sone_HMS | Comparte un único front-end auditivo con las métricas de tonalidad y aspereza de ECMA |

Los tres están anclados de modo que un **tono de 1 kHz a 40 dB SPL es ≈ 1 sono**;
los valores no son intercambiables dígito a dígito porque los modelos difieren
en sus filtros auditivos y en su suma de sonoridad.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_models_comparison_es.png" alt="Sonoridad de un tono de 1 kHz en función del nivel para los modelos de Zwicker, Moore-Glasberg y Sottek, todos pasando por 1 sono a 40 dB SPL" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_models_comparison_es_dark.png" alt="Sonoridad de un tono de 1 kHz en función del nivel para los modelos de Zwicker, Moore-Glasberg y Sottek, todos pasando por 1 sono a 40 dB SPL" style="width:80%">

*Los tres modelos coinciden en el ancla de 1 sono / 40 dB y divergen con el
nivel: Zwicker duplica el valor en sonos cada +10 fonios, mientras que el modelo
de Sottek crece más lentamente (alrededor de 1,65× por cada 10 dB), una
diferencia intrínseca entre las sumas auditivas, no un error de calibración.*

### Sonoridad de Moore-Glasberg (ISO 532-2)

Donde Zwicker usa bandas críticas fijas sobre la escala Bark, Moore-Glasberg
construye un **patrón de excitación** con filtros auditivos exponenciales
redondeados (roex) dependientes del nivel sobre la escala del número ERB
("Cam"), y luego aplica una transformación compresiva de excitación →
sonoridad específica con C = 0,0617 sonos/Cam (ISO 532-2:2017, Fórmula 7) y una
etapa de inhibición binaural. Reproduce los casos de tono y de banda ancha del
Anexo B con un uno o dos por ciento de error y, a diferencia de ISO 532-1,
modela la suma binaural explícitamente.

```python
import numpy as np
from phonometry import (
    loudness_moore_glasberg,
    loudness_moore_glasberg_from_spectrum,
)

# El ancla definitoria: una componente sinusoidal de 1 kHz a 40 dB SPL,
# campo libre, binaural -> 1 sono / 40 fonios por construcción del sono.
res = loudness_moore_glasberg_from_spectrum([(1000.0, 40.0)], field="free")
print(f"N = {res.loudness:.3f} sone  ({res.loudness_level:.1f} phon)")   # 1.000 sono (40.0 fonios)

# Desde una grabación calibrada: se forma el espectro de líneas de banda
# estrecha (FFT, normalización que preserva la potencia) y se alimenta al
# método exacto de componentes sinusoidales (ISO 532-2 apartados 5.2/5.4).
fs = 48000
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
res = loudness_moore_glasberg(x, fs, field="free", presentation="binaural")

res.plot()   # sonoridad específica N'(i) sobre la escala del número ERB (Cam)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — el patrón de sonoridad específica N'(i) directo del resultado:
res.plot()
plt.show()

# O dibújalo a mano desde la rejilla del número ERB que ya lleva el resultado:
fig, ax = plt.subplots()
ax.fill_between(res.erb_number, res.specific, alpha=0.3)
ax.plot(res.erb_number, res.specific)
ax.set_xlabel("Número ERB [Cam]")
ax.set_ylabel("Sonoridad específica N' [sone/Cam]")
plt.show()
```

</details>

#### Parámetros de `loudness_moore_glasberg()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D | Pa | no vacío | Señal de presión calibrada (envoltorio de señal) |
| `components` | lista de `(f, L)` | Hz, dB SPL | — | `_from_spectrum`: componentes sinusoidales discretas |
| `band_levels` | vector de 29 | dB SPL | 25 Hz .. 16 kHz | Entrada de `_from_third_octave` (bandas IEC 61260-1) |
| `fs` | int | Hz | > 0 | Solo en el envoltorio de señal |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` / `'eardrum'` | Transferencia del oído externo |
| `presentation` | str | — | `'binaural'` (por defecto) / `'diotic'` / `'monaural'` | Suma binaural |

Devuelve un `MooreGlasbergLoudness`: `loudness` (N, sonos), `loudness_level`
(fonios), `specific` (N′(i), 372 bins de 0,1 Cam), `erb_number`,
`centre_frequencies`, `field`, `presentation`.

### Sonoridad variable en el tiempo (ISO 532-3)

ISO 532-3 envuelve el mismo modelo de excitación / sonoridad específica en un
análisis espectral multirresolución deslizante (seis FFT paralelas, actualizadas
cada 1 ms) y dos integradores temporales en cascada: la **sonoridad de corto
plazo** S′(t), rápida, y la **sonoridad de largo plazo** S″(t), más lenta. La
sonoridad de largo plazo de pico N_max predice la sonoridad de sonidos de hasta
unos 5 s.

```python
import numpy as np
from phonometry import loudness_moore_glasberg_time

fs = 32000
t = np.arange(int(1.3 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = loudness_moore_glasberg_time(x, fs, field="free")
print(f"N_max = {res.n_max:.3f} sone  ({res.loudness_level_max:.0f} phon)")   # 1.000 sono (40 fonios)
print(f"sonoridad de largo plazo superada el 5% del tiempo: {res.percentiles[5.0]:.3f} sone")   # 0.999 sone

res.plot()   # sonoridad de corto plazo S'(t) y de largo plazo S''(t) frente al tiempo
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/moore_glasberg_time_loudness_es.png" alt="Trazas de sonoridad de corto plazo y de largo plazo de Moore-Glasberg para un pulso de tono, mostrando el ataque rápido de la sonoridad de corto plazo y la relajación más lenta de la de largo plazo" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/moore_glasberg_time_loudness_es_dark.png" alt="Trazas de sonoridad de corto plazo y de largo plazo de Moore-Glasberg para un pulso de tono, mostrando el ataque rápido de la sonoridad de corto plazo y la relajación más lenta de la de largo plazo" style="width:80%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# El resultado lleva ambas trazas sobre un eje temporal de 1 ms:
res.plot()
plt.show()

# O dibújalas directamente para ver la STL rápida frente a la LTL lenta:
fig, ax = plt.subplots()
ax.plot(res.time, res.short_term_loudness, label="Corto plazo S'(t)")
ax.plot(res.time, res.long_term_loudness, label="Largo plazo S''(t)")
ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Sonoridad [sone]")
ax.legend()
plt.show()
```

</details>

#### Parámetros de `loudness_moore_glasberg_time()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `signal` | array 1D o `(n, 2)` | Pa | no vacío | Mono = diótico; dos columnas = oídos izquierdo/derecho |
| `fs` | int | Hz | > 0 | |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` / `'eardrum'` | Transferencia del oído externo |
| `presentation` | str | — | `'binaural'` (por defecto) / `'diotic'` / `'monaural'` | Suma binaural |
| `percentiles` | secuencia | porcentaje | por defecto `(1, 5, 10, 50, 90, 95)` | Niveles de sonoridad de largo plazo excedidos |

Devuelve un `MooreGlasbergTimeVaryingLoudness`: `time` (rejilla de 1 ms),
`short_term_loudness` / `long_term_loudness` (sonos), sus `_level` en fonios,
`n_max`, `loudness_level_max`, un dict `percentiles`, `field`, `presentation`.

### Sonoridad del modelo de Sottek (ECMA-418-2)

ECMA-418-2:2025 especifica un único front-end auditivo — filtrado del oído
externo/medio, un banco de 53 filtros de tipo gammatone sobre la escala Bark_HMS
(z = 0,5 .. 26,5), rectificación de media onda, RMS de bloque y una no
linealidad compresiva (Fórmula 23) — que **comparten** sus métricas de
sonoridad, tonalidad y aspereza. La sonoridad N se expresa en **sone_HMS**, y el
mismo ancla de 1 kHz/40 dB calibra el front-end (nuestro valor de sala limpia
0,996).

```python
import numpy as np
from phonometry import loudness_ecma

fs = 48000
t = np.arange(int(1.2 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = loudness_ecma(x, fs, field="free")
print(f"N = {res.loudness:.3f} sone_HMS")   # 0.996 sone_HMS
print(res.specific_loudness.shape)          # (53,) sonoridad específica media N'(z)

res.plot()   # sonoridad específica media N'(z) + N(l) dependiente del tiempo a 187.5 Hz
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sottek_specific_loudness_es.png" alt="Sonoridad específica media N'(z) del modelo de Sottek sobre las 53 bandas Bark_HMS para un tono de 1 kHz, con máximo en la banda crítica del tono" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sottek_specific_loudness_es_dark.png" alt="Sonoridad específica media N'(z) del modelo de Sottek sobre las 53 bandas Bark_HMS para un tono de 1 kHz, con máximo en la banda crítica del tono" style="width:80%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# El resultado lleva la sonoridad específica media sobre las 53 bandas Bark_HMS:
res.plot()
plt.show()

# O dibuja N'(z) a mano frente a la escala de tasa de banda crítica:
fig, ax = plt.subplots()
ax.fill_between(res.bark, res.specific_loudness, alpha=0.3)
ax.plot(res.bark, res.specific_loudness)
ax.set_xlabel("Tasa de banda crítica z [Bark_HMS]")
ax.set_ylabel("Sonoridad específica N' [sone_HMS/Bark_HMS]")
plt.show()
```

</details>

#### Parámetros de `loudness_ecma()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | array 1D | Pa | no vacío | Señal de presión calibrada |
| `fs` | float | Hz | > 0 | Se remuestrea a 48 kHz internamente si es necesario (apartado 5.1.1) |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Filtro del oído externo/medio (apartado 5.1.3) |

Devuelve un `EcmaLoudness`: `loudness` (N, sone_HMS), `specific_loudness`
(N′(z), 53 bandas), `bark`, `centre_frequencies`, `time`, `loudness_vs_time`
(N(l) a 187,5 Hz), `field`.

### Tonalidad (ECMA-418-2)

Una componente tonal — un silbido, el tono de paso de pala de un ventilador —
destaca incluso a bajo nivel. ECMA-418-2 la cuantifica a partir de la **función
de autocorrelación** (ACF) de la señal rectificada de cada banda: una componente
periódica (tonal) mantiene una ACF alta a retardo no nulo, y la relación entre
sonoridad tonal y de ruido impulsa la tonalidad específica T′(z). El valor único
T se da en **tu_HMS**, calibrado de modo que un tono de 1 kHz/40 dB sea
≈ 1 tu_HMS; el resultado también sigue la frecuencia tonal f_ton por banda.

```python
import numpy as np
from phonometry import tonality_ecma

fs = 48000
t = np.arange(int(1.2 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = tonality_ecma(x, fs, field="free")
peak = int(np.argmax(res.specific_tonality))
print(f"T = {res.tonality:.3f} tu_HMS")                    # 1.000 tu_HMS
print(f"f_ton = {res.tonal_frequencies[peak]:.0f} Hz")     # 999 Hz

res.plot()   # tonalidad específica media T'(z) + T(l) dependiente del tiempo
```

#### Parámetros de `tonality_ecma()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | array 1D | Pa | no vacío | Señal de presión calibrada |
| `fs` | float | Hz | > 0 | Se remuestrea a 48 kHz internamente si es necesario |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Filtro del oído externo/medio |
| `f_low` | float, opcional | Hz | por defecto `None` | Borde inferior de una banda de usuario para la búsqueda de T(l) |
| `f_high` | float, opcional | Hz | por defecto `None` | Borde superior de la banda de usuario |

Devuelve un `EcmaTonality`: `tonality` (T, tu_HMS), `specific_tonality`
(T′(z), 53 bandas), `bark`, `centre_frequencies`, `tonal_frequencies`
(f_ton,z), `time`, `tonality_vs_time` (T(l)), `tonal_frequency_vs_time`,
`field`.

### Aspereza (ECMA-418-2) — capacidad nueva

La aspereza es la sensación áspera y zumbante de una modulación de amplitud
rápida (aproximadamente 20–300 Hz, con máximo cerca de 70 Hz) — la cualidad de
un ralentí diésel o de un altavoz distorsionado. Es una **métrica nueva** en
phonometry. ECMA-418-2 extrae la envolvente de cada banda, pondera su espectro
de modulación por la tasa y la profundidad de modulación, y correlaciona la
modulación entre bandas; el resultado R se da en **asper**. El sonido de
referencia (portador de 1 kHz, modulado en amplitud al 100 % a 70 Hz, 60 dB SPL)
se define como 1 asper — esta implementación de sala limpia devuelve
1,0735 asper (alrededor de +7 %), una varianza honesta: la constante de
calibración tabulada c_R (Fórmula 104) se usa **sin** reajustarla hacia atrás al
objetivo.

```python
import numpy as np
from phonometry import roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
carrier = np.sin(2 * np.pi * 1000 * t)
amp = np.sqrt(2) * 2e-5 * 10 ** (60 / 20)                  # portador a 60 dB SPL
x = amp * (1.0 + np.cos(2 * np.pi * 70 * t)) * carrier      # AM al 100 % a 70 Hz

res = roughness_ecma(x, fs, field="free")
print(f"R = {res.roughness:.4f} asper")   # 1.0735 asper (objetivo de referencia 1.0)

res.plot()   # aspereza R(l50) dependiente del tiempo + mapa de calor de aspereza específica
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo_es.png" alt="Demostración de calidad sonora ECMA-418-2: un sonido tonal puntúa alta tonalidad y aspereza casi nula, mientras que un sonido modulado en amplitud a 70 Hz puntúa alta aspereza y baja tonalidad" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo_es_dark.png" alt="Demostración de calidad sonora ECMA-418-2: un sonido tonal puntúa alta tonalidad y aspereza casi nula, mientras que un sonido modulado en amplitud a 70 Hz puntúa alta aspereza y baja tonalidad" style="width:80%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import tonality_ecma, roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
amp = np.sqrt(2) * 2e-5 * 10 ** (60 / 20)

# Un tono puro (tonal, suave) frente a un tono modulado en amplitud a 70 Hz (áspero):
tone = amp * np.sin(2 * np.pi * 1000 * t)
rough = amp * (1.0 + np.cos(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 1000 * t)

scores = {
    "Tono puro": (tonality_ecma(tone, fs).tonality, roughness_ecma(tone, fs).roughness),
    "Tono AM 70 Hz": (tonality_ecma(rough, fs).tonality, roughness_ecma(rough, fs).roughness),
}
labels = list(scores)
tonal = [scores[k][0] for k in labels]
rough_v = [scores[k][1] for k in labels]
xpos = np.arange(len(labels))
fig, ax = plt.subplots()
ax.bar(xpos - 0.2, tonal, 0.4, label="Tonalidad [tu_HMS]")
ax.bar(xpos + 0.2, rough_v, 0.4, label="Aspereza [asper]")
ax.set_xticks(xpos)
ax.set_xticklabels(labels)
ax.legend()
plt.show()
```

</details>

#### Parámetros de `roughness_ecma()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | array 1D | Pa | no vacío | Señal de presión calibrada |
| `fs` | float | Hz | > 0 | Se remuestrea a 48 kHz internamente si es necesario |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Filtro del oído externo/medio |

Devuelve un `EcmaRoughness`: `roughness` (R, asper, el percentil 90 de
R(l50)), `specific_roughness` (R′(z), 53 bandas), `bark`, `centre_frequencies`,
`time`, `roughness_vs_time` (R(l50)), `specific_roughness_vs_time`
(array de (n_times, 53)), `field`.

Consulta [Tonos discretos prominentes](/phonometry/es/guides/tone-prominence/)
para los veredictos TNR/PR de ECMA-418-1, el
[índice de transmisión del habla](/phonometry/es/guides/speech-transmission/)
para el STI/STIPA, y [Teoría](/phonometry/es/reference/theory/) para la
matemática subyacente.

---

**Normas.** ISO 532-1:2017, *Acoustics — Methods for calculating
loudness — Part 1: Zwicker method* — sonoridad estacionaria y variable en el
tiempo en sonos a partir del programa de referencia normativo del Anexo A.4,
con la sonoridad percentil N5/N10, validada frente al conjunto del Anexo B.
ISO 532-2:2017, *... Part 2: Moore-Glasberg method* — sonoridad estacionaria a
partir de patrones de excitación roex sobre la escala del número ERB, con suma
binaural explícita. ISO 532-3:2023, *... Part 3:
Moore-Glasberg-Schlittenlacher method* — sonoridad variable en el tiempo de
corto y largo plazo y el pico N_max. DIN 45692:2009, *Messtechnische
Simulation der Hörempfindung Schärfe* — sharpness en acum (ponderación del
apartado 6, variantes von Bismarck y Aures del Anexo B, objetivos de la
Tabla A.2). ISO 226:2023, *Acoustics — Normal equal-loudness-level contours* —
las curvas isofónicas (Fórmula 1), el nivel de sonoridad de tonos puros
(Fórmula 2) y el umbral de audición. ECMA-418-2:2025, *Psychoacoustic metrics
for ITT equipment — Part 2 (methods for describing human perception based on
the Sottek Hearing Model)* — la sonoridad (sone_HMS), la tonalidad (tu_HMS) y
la aspereza (asper) del modelo de Sottek.
