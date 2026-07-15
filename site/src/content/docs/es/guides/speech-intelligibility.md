---
title: "Índice de inteligibilidad del habla"
description: "El índice de inteligibilidad del habla (SII) por bandas de tercio de octava de ANSI S3.5-1997: niveles espectrales equivalentes de habla/ruido/umbral, la función de importancia de banda (Tabla 3), la automáscara del habla y la propagación ascendente de la máscara, la función de audibilidad de banda y el índice en ruido y en pérdida auditiva."
---

El **índice de inteligibilidad del habla** predice cuánto de una señal de habla
es audible, y por tanto inteligible, para un oyente en una condición dada de
ruido y audición. Reduce un espectro de habla, un espectro de ruido y un umbral
auditivo a un único número en `[0, 1]`: `0` cuando nada útil alcanza al oyente,
`1` cuando todo el espectro portador del habla es audible. Esta página cubre el
**método por bandas de tercio de octava** de **ANSI S3.5-1997 (R2017)** — 18
bandas de 160 Hz a 8000 Hz.

:::note
**SII frente a STI.** El SII predice la inteligibilidad desde la
*audibilidad* — cuánto del espectro del habla supera el ruido y el umbral de
audición en el oído de quien escucha —, mientras que el STI caracteriza un
*canal de transmisión*: cuánta de la modulación del habla conserva una sala o
un sistema de sonido. Para esto último, consulta la
[guía del índice de transmisión del habla](/phonometry/es/guides/speech-transmission/).
:::

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_speech_intelligibility_es.svg" alt="El flujo de cálculo del SII: tres entradas de nivel espectral equivalente (habla Ei', ruido Ni', umbral de audición Ti') alimentan la etapa de automáscara del habla y propagación de la máscara (nivel espectral de enmascaramiento equivalente Zi), después la perturbación equivalente Di, después la función de audibilidad de banda Ai acotada a [0, 1], y por último la suma ponderada por importancia de banda SII sobre las 18 bandas de tercio de octava" style="width:94%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_speech_intelligibility_es_dark.svg" alt="El flujo de cálculo del SII: tres entradas de nivel espectral equivalente (habla Ei', ruido Ni', umbral de audición Ti') alimentan la etapa de automáscara del habla y propagación de la máscara (nivel espectral de enmascaramiento equivalente Zi), después la perturbación equivalente Di, después la función de audibilidad de banda Ai acotada a [0, 1], y por último la suma ponderada por importancia de banda SII sobre las 18 bandas de tercio de octava" style="width:94%">

## 1. Entradas y la función de importancia de banda

Las tres entradas son **niveles espectrales equivalentes** (ANSI S3.5-1997,
cláusulas 3.11 y 3.55) muestreados en los 18 centros de banda de tercio de
octava: el nivel espectral del habla $E_i'$, el nivel espectral del ruido $N_i'$
(ambos en dB SPL) y el umbral de audición $T_i'$ (en dB HL). Cada banda $i$
contribuye a la inteligibilidad en proporción a su **función de importancia de
banda** $I_i$ (ANSI S3.5-1997 Tabla 3, material de habla promedio), que suma uno
sobre las 18 bandas.

```python
import phonometry as ph

# El espectro de habla estándar de esfuerzo normal (Tabla 3) en silencio, audición normal.
result = ph.speech_intelligibility_index("normal")
print(round(result.sii, 3))          # 0.996  (casi todo audible)
print(round(ph.sii.BAND_IMPORTANCE.sum(), 6))   # 1.0
```

Sin ruido y con un umbral de audición normal, el espectro de habla estándar es casi
totalmente audible, por lo que el índice se acerca a uno; el pequeño déficit es
la propia **automáscara del habla** del oyente.

## 2. Enmascaramiento y la función de audibilidad de banda

El procedimiento (ANSI S3.5-1997, cláusula 5) convierte las entradas en una
audibilidad por banda. El habla se enmascara a sí misma hacia abajo desde cada
banda ($V_i = E_i' - 24$); el mayor entre eso y el ruido externo, $B_i$, se
propaga **hacia arriba** en frecuencia con una pendiente dependiente del nivel
para dar el nivel espectral de enmascaramiento equivalente $Z_i$ (cláusula 5.4):

$$
Z_i = 10\log_{10}\!\left(10^{0{,}1 N_i'} + \sum_{k<i}
      10^{0{,}1\left(B_k + 3{,}32\,C_k\,\log_{10}(0{,}89\,f_i/f_k)\right)}\right).
$$

El enmascaramiento se combina con el ruido interno equivalente
($X_i' = X_i + T_i'$, el ruido interno de referencia desplazado por la pérdida
auditiva) en la **perturbación equivalente** $D_i$ (cláusula 5.6), y la
**función de audibilidad de banda** es la razón habla-perturbación escalada a
$[0, 1]$ (cláusula 5.8):

$$
A_i = \operatorname{clip}\!\left(\frac{E_i' - D_i + 15}{30},\; 0,\; 1\right).
$$

A niveles de habla muy por encima del esfuerzo normal, un **factor de distorsión
de nivel** de la cláusula 5.7 —la unidad para los espectros estándar usados en
esta página— reduce aún más $A_i$; phonometry lo aplica automáticamente.

## 3. El índice en ruido

El índice de inteligibilidad del habla es la suma de las audibilidades de banda
ponderada por la importancia de banda (ANSI S3.5-1997, cláusula 6):

$$
\text{SII} = \sum_{i} I_i\, A_i .
$$

```python
import numpy as np
import phonometry as ph

speech = ph.standard_speech_spectrum("normal")
# Un ruido de enmascaramiento de banda ancha descendente (espectro tipo oficina/ventilación).
noise = np.array([38.0, 37.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0, 24.0,
                  22.0, 20.0, 18.0, 16.0, 14.0, 12.0, 10.0, 8.0, 6.0])

result = ph.speech_intelligibility_index(speech, noise)
print(round(result.sii, 2))                # 0.46
print(result.band_audibility.round(2))     # Ai por banda
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/speech_intelligibility_es.svg" alt="Audibilidad de banda del espectro de habla estándar de esfuerzo normal en un ruido de banda ancha descendente: las barras claras son la audibilidad por banda Ai sobre las 18 bandas de tercio de octava de 160 Hz a 8000 Hz, las barras más oscuras la contribución ponderada por importancia Ii*Ai (escalada), y el SII global es 0,46" style="width:90%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/speech_intelligibility_es_dark.svg" alt="Audibilidad de banda del espectro de habla estándar de esfuerzo normal en un ruido de banda ancha descendente: las barras claras son la audibilidad por banda Ai sobre las 18 bandas de tercio de octava de 160 Hz a 8000 Hz, las barras más oscuras la contribución ponderada por importancia Ii*Ai (escalada), y el SII global es 0,46" style="width:90%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

speech = ph.standard_speech_spectrum("normal")
noise = np.array([38.0, 37.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0, 24.0,
                  22.0, 20.0, 18.0, 16.0, 14.0, 12.0, 10.0, 8.0, 6.0])
result = ph.speech_intelligibility_index(speech, noise)

# En una línea:
result.plot()
plt.show()

# A mano, replicando lo que dibuja SIIResult.plot():
pos = np.arange(result.frequencies.size)
weighted = result.band_audibility * result.band_importance
fig, ax = plt.subplots()
ax.bar(pos, result.band_audibility, color="#c6dbef", label=r"Audibilidad de banda $A_i$")
ax.bar(pos, weighted / weighted.max(), width=0.5, color="#1f77b4",
       label=r"Ponderada por importancia $I_i A_i$ (escalada)")
ax.set_xticks(pos)
ax.set_xticklabels([f"{f:g}" for f in result.frequencies], rotation=45, ha="right")
ax.set_xlabel("Banda de tercio de octava [Hz]")
ax.set_ylabel("Audibilidad de banda")
ax.set_title(f"SII = {result.sii:.2f}")
ax.legend()
plt.show()
```

</details>

Un umbral de audición elevado (`threshold=`) sube el ruido interno equivalente y
reduce el índice, igual que lo hace añadir ruido de enmascaramiento. El
`SIIResult` también lleva el enmascaramiento por banda $Z_i$, la perturbación
$D_i$, la audibilidad $A_i$ y la importancia $I_i$, y su `.plot()` dibuja la
figura de arriba.

## 4. Esfuerzo vocal

Los hablantes elevan la voz en ruido, y la norma da cuatro **espectros de voz
estándar** para los esfuerzos vocales *normal*, *elevada*, *fuerte* y *grito*
(ANSI S3.5-1997, Tabla 3). Al pasar el nombre del esfuerzo se selecciona el
espectro correspondiente; hablar más fuerte sube todo el espectro y, en un ruido
fijo, aumenta el índice.

```python
import numpy as np
import phonometry as ph

# El mismo ruido de banda ancha, cuatro esfuerzos vocales.
noise = np.array([48.0, 47.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0,
                  32.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0])
for effort in ph.sii.VOCAL_EFFORTS:
    print(effort, round(ph.speech_intelligibility_index(effort, noise).sii, 2))
# normal 0.12 | raised 0.36 | loud 0.59 | shout 0.79

print(ph.standard_speech_spectrum("loud")[8])  # 42.16 dB SPL a 1 kHz
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_vocal_efforts_es.svg" alt="Izquierda: los cuatro espectros de voz estándar de ANSI S3.5-1997 (normal, elevada, fuerte, grito) de 160 Hz a 8000 Hz, cada esfuerzo mayor sube todo el espectro. Derecha: el SII resultante en un ruido de banda ancha fijo, subiendo de 0,12 (normal) a 0,79 (grito)" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_vocal_efforts_es_dark.svg" alt="Izquierda: los cuatro espectros de voz estándar de ANSI S3.5-1997 (normal, elevada, fuerte, grito) de 160 Hz a 8000 Hz, cada esfuerzo mayor sube todo el espectro. Derecha: el SII resultante en un ruido de banda ancha fijo, subiendo de 0,12 (normal) a 0,79 (grito)" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import phonometry as ph

# Los cuatro espectros de la Tabla 3 de ANSI S3.5-1997 y el ruido fijo de arriba.
noise = np.array([48.0, 47.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0,
                  32.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0])
efforts = ph.sii.VOCAL_EFFORTS         # ("normal", "raised", "loud", "shout")
freqs = ph.sii.BAND_CENTERS            # los 18 centros de banda de tercio de octava
nombres = {"normal": "Normal", "raised": "Elevada",
           "loud": "Fuerte", "shout": "Grito"}

fig, (ax_s, ax_i) = plt.subplots(1, 2, figsize=(12, 5))

# Izquierda: cada esfuerzo vocal mayor sube todo el espectro de voz.
for effort in efforts:
    ax_s.plot(freqs, ph.standard_speech_spectrum(effort), "o-",
              label=nombres[effort])
ax_s.set_xscale("log")
ax_s.set_xticks(list(freqs))
ax_s.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax_s.xaxis.set_minor_formatter(NullFormatter())
ax_s.set_xlabel("Banda de tercio de octava [Hz]")
ax_s.set_ylabel("Nivel espectral del habla [dB SPL]")
ax_s.legend()

# Derecha: el SII que alcanza cada espectro en el ruido fijo.
sii = [ph.speech_intelligibility_index(e, noise).sii for e in efforts]
pos = np.arange(len(efforts))
ax_i.bar(pos, sii)
ax_i.set_xticks(pos)
ax_i.set_xticklabels([nombres[e] for e in efforts])
ax_i.set_ylim(0.0, 1.0)
ax_i.set_ylabel("Índice de inteligibilidad del habla")
plt.show()
```

</details>

Los nombres de esfuerzo vocal funcionan en cualquier sitio donde se espere un
espectro de voz, incluido como primer argumento de
`speech_intelligibility_index`.

## Véase también

- [Índice de transmisión del habla](/phonometry/es/guides/speech-transmission/) — el
  índice de transmisión STI/STIPA que el SII complementa.
- [Sonoridad](/phonometry/es/guides/loudness/) y
  [Métricas de calidad sonora](/phonometry/es/guides/sound-quality/) — la sonoridad, el
  sharpness y las métricas de percepción de lo que oye quien escucha.
- [Bancos de filtros](/phonometry/es/guides/filter-banks/) — las bandas de tercio de octava
  sobre las que se evalúa el SII.
- [Niveles](/phonometry/es/guides/levels/) — los niveles espectrales y de banda tras las
  entradas de nivel espectral equivalente.

---

**Normas.** ANSI S3.5-1997 (R2017), *American National Standard Methods for the
Calculation of the Speech Intelligibility Index* — el método por bandas de
tercio de octava (18 bandas), la función de importancia de banda (Tabla 3), el
nivel espectral del habla estándar y el ruido interno de referencia (Tabla 3), y
el procedimiento de enmascaramiento, perturbación y audibilidad de banda
(cláusula 5) y el índice (cláusula 6).
