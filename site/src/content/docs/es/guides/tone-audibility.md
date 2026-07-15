---
title: "Audibilidad objetiva de tonos en ruido (ISO/PAS 20065)"
description: "El método de ingeniería de ISO/PAS 20065:2016 para la audibilidad ΔL de un tono por encima del umbral de enmascaramiento: la banda crítica en torno al tono (Δfc, Fórmula 2), el nivel de banda crítica del enmascaramiento LG = LS + 10 lg(Δfc/Δf) (Fórmula 12), el índice de enmascaramiento av = −2 − lg[1 + (f/502)²·⁵] (Fórmula 13), la audibilidad ΔL = LT − LG − av (Fórmula 14) y la audibilidad decisiva y media energética (Fórmula 20)."
---

Un tono estacionario inmerso en ruido de banda ancha resalta cuando emerge de
forma audible por encima del ruido que de otro modo lo enmascararía —la
condición objetiva previa a las penalizaciones tonales del análisis de ruido—.
**ISO/PAS 20065:2016** es el *método de ingeniería* que cuantifica esa
audibilidad: a partir de un espectro de banda estrecha (FFT) obtiene, para cada
tono prominente, la **audibilidad** `ΔL` — cuántos decibelios supera el nivel
del tono al umbral de enmascaramiento del ruido circundante. (Que un tono sea
*molesto* es un juicio de valoración posterior e independiente.) Es el método
detallado al que remite **ISO 1996-2:2017** (la vía simplificada del Anexo C
está en [medición ambiental](/phonometry/es/guides/levels/)); la audibilidad
media `ΔL` que produce alimenta el ajuste tonal `Kt` de ISO 1996-2.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_audibility_es.svg" alt="Audibilidad ΔL por tono de los nueve tonos del espectro del motor de combustión del Anexo E de ISO/PAS 20065, con el tono decisivo a 137,3 Hz resaltado y el umbral ΔL = 0 dB marcado" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_audibility_es_dark.svg" alt="Audibilidad ΔL por tono de los nueve tonos del espectro del motor de combustión del Anexo E de ISO/PAS 20065, con el tono decisivo a 137,3 Hz resaltado y el umbral ΔL = 0 dB marcado" style="width:82%">

## 1. La banda crítica en torno al tono

Cada tono de frecuencia `fT` se evalúa dentro de una banda crítica cuyo ancho es
(Fórmula 2)

$$
\Delta f_c = 25{,}0 + 75{,}0\left(1{,}0 + 1{,}4\left(\tfrac{f_T}{1000}\right)^{2}\right)^{0{,}69}\ \mathrm{Hz}.
$$

Con una posición geométrica de las frecuencias de esquina en torno al tono
(Fórmulas 3–5), `√(f₁·f₂) = fT` y `f₂ − f₁ = Δfc`, de modo que
`f₁ = −Δfc/2 + √(Δfc² + 4·fT²)/2` y `f₂ = f₁ + Δfc`.

```python
import phonometry as ph

print(round(ph.critical_bandwidth_engineering(137.3), 2))   # 101.36 Hz
f1, f2 = ph.critical_band_corners(137.3)
print(round(f1, 2), round(f2, 2))                            # 95.67 197.04
```

## 2. Audibilidad de un tono

El nivel medio de banda estrecha `LS` del ruido enmascarante (Fórmula 6, un
promedio energético iterativo de las líneas de la banda crítica) y el nivel del
tono `LT` (Fórmula 8, la suma energética de las líneas tonales) se derivan del
espectro de banda estrecha — `mean_narrowband_level` y `tone_level` lo hacen
directamente (ver §4). El nivel de banda crítica del ruido enmascarante
reparte `LS` sobre el ancho de banda crítico (Fórmula 12), el índice de
enmascaramiento tiene en cuenta el oído (Fórmula 13) y la audibilidad es su
diferencia (Fórmula 14):

$$
L_G = L_S + 10\lg\!\frac{\Delta f_c}{\Delta f}, \qquad
a_v = -2 - \lg\!\Big[1 + \big(\tfrac{f}{502}\big)^{2{,}5}\Big], \qquad
\Delta L = L_T - L_G - a_v .
$$

Un tono proporcionado es *audible* cuando `ΔL > 0`. `Δf` es el espaciado de líneas
(resolución en frecuencia); las sumas energéticas sobre `K > 1` líneas llevan
una corrección de ventana de `10·lg(Δf/Δfe)` (`−1,76 dB` para la ventana de
Hanning recomendada, `Δfe = 1,5·Δf`, Fórmula (8)), mientras que un tono de una
sola línea (`K = 1`) toma su nivel sin cambios (Fórmula (7), sin corrección de
ancho de banda).

```python
import phonometry as ph

# ISO/PAS 20065 Anexo E, tono a 137,3 Hz (Δf = 2,7 Hz):
#   LS = 49,22 dB (Fórmula 6), LT = 67,96 dB (Fórmula 8).
print(round(ph.tone_audibility(67.96, 49.22, 137.3, 2.7), 2))   # 5.01 dB
print(round(ph.masking_index(137.3), 2))                        # -2.02 dB
```

## 3. Audibilidad decisiva y media

La audibilidad **decisiva** de un espectro de banda estrecha es la mayor
audibilidad de tono en él (apartado 5.3.8). Sobre `J` espectros escalonados en
el tiempo, la **audibilidad media** es su media energética (Fórmula 20); un
espectro en el que no se encuentra ningún tono aporta `ΔLj = −10 dB`
(Fórmula 21). `assess_tones` aplica toda la cadena a los tonos de un espectro e
informa del tono decisivo.

```python
import phonometry as ph

# Espectro 1 del motor de combustión (Anexo E): nueve tonos (fT, LT, LS), Δf = 2,7 Hz.
fT = [118.4, 137.3, 158.8, 314.9, 433.4, 592.2, 629.8, 643.3, 1582.7]
LT = [64.56, 67.96, 68.63, 68.50, 73.17, 78.31, 75.00, 79.75, 71.07]
LS = [48.91, 49.22, 50.50, 52.85, 58.29, 59.53, 59.71, 61.98, 54.16]
res = ph.assess_tones(fT, LT, LS, 2.7)
print(round(res.decisive_audibility, 2), res.decisive_frequency)  # 5.01 137.3

# Audibilidad media de los cinco espectros medidos (valores decisivos, Tabla E.3):
print(round(ph.mean_audibility([9.18, 6.04, 7.46, 2.67, 7.17]), 2))  # 6.98 dB
```

### 3.1 Incertidumbre extendida de la audibilidad

La cláusula 5.4 asocia a cada audibilidad una incertidumbre extendida `U`
(bilateral al 90 %), y la cláusula 6 la hace obligatoria cuando se han
promediado menos de 12 espectros. `assess_tones` la calcula por tono
(`res.extended_uncertainties`), `audibility_uncertainty` la evalúa
directamente desde las líneas del espectro y `mean_audibility_uncertainty`
la propaga a la audibilidad media energética de un conjunto de espectros
(Anexo E: `U = 2.80 dB` para el tono de 137.3 Hz frente al 2,79 impreso).

## 4. Desde el espectro de banda estrecha

Dadas las líneas FFT de la banda crítica en torno a un tono,
`mean_narrowband_level` ejecuta el procedimiento iterativo de la Fórmula 6
(media energética, descartando toda línea que supere en más de 6 dB la `LS` en
curso, hasta estabilizarse en ±0,005 dB o quedar menos de cinco líneas por lado
— Anexo D) y `tone_level` suma las líneas tonales contiguas al pico (por encima
de `LS + 6 dB` y de `L_pico − 10 dB`). La media lleva siempre la corrección de
ancho de banda de Hanning de −1,76 dB; el nivel del tono solo cuando el tramo
abarca más de una línea (Fórmulas (7)/(8)).

```python
import phonometry as ph

# Anexo E Tabla E.1: las 38 líneas de la banda crítica de 137,3 Hz (Δf = 2,7 Hz).
freqs = [96.9, 99.6, 102.3, 105.0, 107.7, 110.4, 113.0, 115.7, 118.4, 121.1,
         123.8, 126.5, 129.2, 131.9, 134.6, 137.3, 140.0, 142.7, 145.3, 148.0,
         150.7, 153.4, 156.1, 158.8, 161.5, 164.2, 166.9, 169.6, 172.3, 175.0,
         177.6, 180.3, 183.0, 185.7, 188.4, 191.1, 193.8, 196.5]
levels = [49.40, 50.68, 50.09, 53.37, 44.47, 50.91, 51.41, 59.40, 64.54, 57.57,
          51.02, 50.76, 59.93, 62.94, 58.49, 65.87, 62.66, 50.25, 51.32, 52.30,
          52.58, 53.15, 67.04, 67.27, 57.40, 57.17, 52.56, 51.39, 52.49, 47.68,
          51.26, 49.03, 61.42, 59.52, 48.43, 50.84, 48.20, 55.95]

ls = ph.mean_narrowband_level(levels, freqs, 137.3)
lt = ph.tone_level(levels, freqs, 137.3, ls)
print(round(ls, 2), round(lt, 2))                         # 49.22 67.96
print(round(ph.tone_audibility(lt, ls, 137.3, 2.7), 2))   # 5.01 dB
```

## 5. Detección sobre el espectro completo

`analyze_spectrum` ejecuta todo el front-end sobre un espectro — nivel medio de
banda estrecha por línea, detección de picos (apartado 5.3.8 Paso 1, un tono no
puede estar en un flanco), nivel del tono, el criterio de distinción (apartado
5.3.4: ancho de banda `≤ 26·(1 + 0,001·fT)` Hz y pendiente de flanco `≥ 24 dB`)
y la audibilidad — y devuelve los tonos distintos y audibles. Después aplica
el **Paso 3**: los tonos audibles que comparten una banda crítica suman
energéticamente sus niveles de tono (Fórmula 17, líneas compartidas contadas
una sola vez, vía `combined_tone_level`) en una entrada combinada «FG»
valorada en el miembro más audible — salvo que la excepción de exactamente
dos tonos por debajo de 1000 Hz de §5.1 los mantenga separados. El
`group_sizes` del resultado distingue tonos individuales (`1`) de entradas FG
(`N ≥ 2`), y la audibilidad decisiva (Paso 4) es el máximo sobre todas las
entradas.

```python
import phonometry as ph

# El mismo espectro de la Tabla E.1 de arriba.
res = ph.analyze_spectrum(levels, freqs, 2.7)
singles = res.group_sizes == 1
print([round(f, 1) for f in res.tone_frequencies[singles]])  # [118.4, 137.3, 158.8]

# El Paso 3 ya combinó los tres tonos de la misma banda en una entrada FG:
fg = res.group_sizes > 1
print(int(res.group_sizes[fg][0]), round(float(res.tone_levels[fg][0]), 2))  # 3 72.15

# La misma combinación de la Fórmula 17, llamada directamente (LS de la Tabla E.2):
lt_fg = ph.combined_tone_level(levels, freqs, [118.4, 137.3, 158.8],
                               [48.91, 49.22, 50.50])
print(round(lt_fg, 2))                                # 72.15
```

Reproducir una audibilidad *decisiva* exacta requiere el espectro de banda
estrecha **completo**: la Tabla E.1 está truncada a la banda crítica de 137,3 Hz,
así que el nivel medio de banda estrecha del tono de 158,8 Hz se subestima a
partir de ella (el algoritmo en sí coincide con el programa de referencia de la
norma madre DIN 45681:2005-03). La detección de picos y la combinación FG se
verifican contra el ejemplo resuelto del Anexo E (las tres frecuencias de tono y
`LT = 72,15 dB`).

### 5.1 Dos tonos por debajo de 1000 Hz

Cuando **exactamente dos** tonos comparten una banda crítica y ambos están por
debajo de 1000 Hz, el oído todavía puede distinguirlos — y entonces se evalúan
*por separado* en lugar de combinarse en FG — si su diferencia de frecuencia
`|fT1 − fT2|` (Fórmula 18) supera

```text
fD = 21·10^(1,2·|lg(fT/212)|^1,8)  Hz     (Fórmula 19, 88 Hz < fT < 1000 Hz)
```

evaluada en el tono más prominente `fT` (el de mayor audibilidad `ΔL`). El umbral
alcanza su mínimo de `21 Hz` en `fT = 212 Hz` y crece a ambos lados.
`two_tone_separation_frequency` da `fD`; `resolve_tones_separately` aplica la
decisión.

```python
import phonometry as ph

ph.two_tone_separation_frequency(212.0)             # 21,0 Hz (mínimo)
ph.resolve_tones_separately(200.0, 260.0, 3.0, 2.0) # True  → evaluar por separado
ph.resolve_tones_separately(118.4, 137.3, 4.0, 5.0) # False → combinar (Δf < fD)
```

:::note
Ningún ejemplo resuelto de ISO/PAS 20065 ejercita esta rama — la banda del Anexo
E agrupa *tres* tonos, así que la regla de «exactamente dos tonos» nunca se
dispara ahí. La fórmula y la decisión se implementan en clean-room desde el texto
y se verifican contra el programa de referencia del Anexo J de
**DIN 45681:2005-03** (`fD = 21 * 10 ^ (1.2 * Abs(Log(fT / 212) / Log(10)) ^
1.8)`). Como refuerzo, evaluado en los tonos del Anexo E el umbral (`≈ 24 Hz` en
137,3 Hz) los mantiene combinados, coherente con la agrupación FG de ese ejemplo.
:::

## Normas

ISO/PAS 20065:2016, *Acoustics — Objective method for assessing the audibility
of tones in noise — Engineering method*: el ancho de banda crítico `Δfc`
(Fórmula 2) y sus frecuencias de esquina (Fórmulas 3–5), el nivel de banda
crítica `LG` (Fórmula 12), el índice de enmascaramiento `av` (Fórmula 13), la
audibilidad `ΔL = LT − LG − av` (Fórmula 14) y la audibilidad media energética
(Fórmula 20). El nivel medio de banda estrecha `LS` (Fórmula 6, iterativa Anexo
D) y el nivel del tono `LT` (Fórmula 8) se calculan desde el espectro de banda
crítica, y `analyze_spectrum` añade la detección de picos (apartado 5.3.8) con
los criterios de distinción (apartado 5.3.4) y la combinación multitono `FG`
(Fórmula 17), además de la evaluación separada de dos tonos por debajo de 1000 Hz
(Fórmulas 18/19). La corrección de ancho de banda de Hanning de −1,76 dB, el
procedimiento iterativo del nivel de enmascaramiento y la lógica de
detección/combinación están confirmados frente a la norma madre
**DIN 45681:2005-03** (su programa de referencia del Anexo J). La conformidad se
ancla en el ejemplo resuelto del motor de combustión del Anexo E (Tablas
E.1/E.2/E.3): `LS` y `LT` desde el espectro, la detección de tonos y el nivel
combinado `FG`, la audibilidad por tono, el índice de enmascaramiento y la
audibilidad media de los cinco espectros.
