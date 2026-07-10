---
title: "Criterios de ruido de salas (NC / RC Mark II)"
description: "Las calificaciones de ruido de salas de ANSI/ASA S12.2-2019: el método de tangencia de los criterios de ruido (NC) sobre las curvas de la Tabla 1, y la calificación Room Criteria Mark II (RC) con su etiqueta espectral de retumbo/siseo/neutro (Anexo D)."
---

El ruido de fondo estacionario de una sala ocupada — de la ventilación, los
difusores o el tráfico lejano — se califica frente a una familia de **curvas de
criterio por bandas de octava**. **ANSI/ASA S12.2-2019**, *Criteria for
Evaluating Room Noise*, define dos calificaciones a partir de un espectro que
phonometry implementa: la calificación **Noise Criteria (NC)** por el método de
tangencia, y la calificación **Room Criteria Mark II (RC)** con su etiqueta
espectral de retumbo/siseo. Ambas trabajan sobre niveles de presión sonora por
banda de octava en las diez bandas de 16 Hz a 8000 Hz.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_noise_es.svg" alt="Los dos métodos de calificación de ANSI S12.2 a partir de un espectro por bandas de octava: a la izquierda el método de tangencia NC (de las curvas de la Tabla 1, el valor NC en cada banda, después NC es la curva más alta tocada, dando NC-NN con una banda determinante); a la derecha el método RC Mark II (la media de frecuencias medias LMF de los niveles de 500, 1000 y 2000 Hz redondeada para dar RC-NN, después la etiqueta espectral R de retumbo, H de siseo o N de neutro por las reglas de desviación de la cláusula D.3)" style="width:94%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_noise_es_dark.svg" alt="Los dos métodos de calificación de ANSI S12.2 a partir de un espectro por bandas de octava: a la izquierda el método de tangencia NC (de las curvas de la Tabla 1, el valor NC en cada banda, después NC es la curva más alta tocada, dando NC-NN con una banda determinante); a la derecha el método RC Mark II (la media de frecuencias medias LMF de los niveles de 500, 1000 y 2000 Hz redondeada para dar RC-NN, después la etiqueta espectral R de retumbo, H de siseo o N de neutro por las reglas de desviación de la cláusula D.3)" style="width:94%">

## 1. Criterios de ruido — el método de tangencia

Las **curvas NC** (ANSI/ASA S12.2-2019, Tabla 1) son una familia de límites por
banda de octava, cada una designada por su valor a 1000 Hz (de NC-15 hasta
NC-70). El **método de tangencia** califica un espectro medido por el valor de
la **curva NC más alta que toca**: para cada banda de octava se busca el índice
NC cuya curva pasa por el nivel medido, y la calificación es el máximo entre
bandas. La banda en la que se alcanza ese máximo — la que empuja el espectro
contra las curvas — se reporta como **banda determinante**.

```python
import numpy as np
import phonometry as ph

# SPL en bandas de octava, 16 Hz - 8000 Hz (una sala dominada por la ventilación).
spl = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])

nc = ph.noise_criterion(spl)
print(round(nc.rating, 1))        # 42.5
print(nc.governing_frequency)     # 250.0  (la banda tangente)
```

Como la calificación interpola entre las curvas tabuladas es un número continuo:
una calificación NC de $42{,}5$ queda a medio camino entre NC-40 y NC-45. Puede
suministrarse un subconjunto de las bandas de octava junto con sus frecuencias
centrales (`ph.noise_criterion(levels, frequencies)`), lo que resulta cómodo
cuando solo se midieron las bandas de interferencia con el habla.

## 2. Room Criteria Mark II — calificación y etiqueta espectral

Las curvas **RC Mark II** (ANSI/ASA S12.2-2019, Anexo D, Tabla D.1) tienen una
pendiente constante de **−5 dB/octava**, ancladas a su valor a 1000 Hz, con el
nivel de 16 Hz igual al de 31,5 Hz y un suelo de baja frecuencia de 55 dB. La
calificación numérica es la **media de frecuencias medias** $\text{LMF}$ — la
media de los niveles de 500, 1000 y 2000 Hz — redondeada al decibelio más
próximo (cláusula D.4):

$$
\text{LMF} = \tfrac{1}{3}\left(L_{500} + L_{1000} + L_{2000}\right),
\qquad \text{RC} = \operatorname{redondeo}(\text{LMF}).
$$

Una **etiqueta espectral** describe entonces el *carácter* del ruido según cómo
se desvía el espectro de la curva RC de referencia (cláusula D.3): **retumbo**
($R$) cuando una banda a 500 Hz o por debajo supera la curva en más de 5 dB,
**siseo** ($H$) cuando una banda a 1000 Hz o por encima la supera en más de
3 dB, y **neutro** ($N$) cuando no ocurre ninguna de las dos.

```python
import numpy as np
import phonometry as ph

spl = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])

rc = ph.room_criterion(spl)
print(rc.label)             # RC-35(R)   -  una sala retumbante
print(round(rc.lmf, 1))     # 35.3
print(rc.classification)    # R
```

El fuerte contenido de baja frecuencia de este espectro eleva las bandas de
63–250 Hz muy por encima de la curva de referencia, así que el ruido se etiqueta
como $R$ (retumbo) — el "zumbido" subjetivo de una climatizadora sobredimensionada.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/room_noise_criteria_es.png" alt="Dos paneles para el mismo espectro de sala dominado por la ventilación. Izquierda: los niveles medidos por banda de octava sobre la familia de curvas NC, con un rombo rojo que marca el punto de tangencia a 250 Hz que fija la calificación NC-42,5. Derecha: el mismo espectro sobre la curva de referencia RC-35, con las bandas de baja frecuencia atravesando la tolerancia de retumbo sombreada (más 5 dB por debajo de 500 Hz) de modo que el ruido se clasifica como RC-35(R), y la tolerancia de siseo (más 3 dB a 1000 Hz y por encima) sombreada para comparar" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/room_noise_criteria_es_dark.png" alt="Dos paneles para el mismo espectro de sala dominado por la ventilación. Izquierda: los niveles medidos por banda de octava sobre la familia de curvas NC, con un rombo rojo que marca el punto de tangencia a 250 Hz que fija la calificación NC-42,5. Derecha: el mismo espectro sobre la curva de referencia RC-35, con las bandas de baja frecuencia atravesando la tolerancia de retumbo sombreada (más 5 dB por debajo de 500 Hz) de modo que el ruido se clasifica como RC-35(R), y la tolerancia de siseo (más 3 dB a 1000 Hz y por encima) sombreada para comparar" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

spl = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])

# En una línea cada uno:
ph.noise_criterion(spl).plot()
ph.room_criterion(spl).plot()
plt.show()

# A mano, reproduciendo lo que dibujan NCResult.plot() / RCResult.plot():
from phonometry.room_noise import NC_CURVES, NC_INDICES, OCTAVE_BANDS
nc, rc = ph.noise_criterion(spl), ph.room_criterion(spl)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

for row, idx in zip(NC_CURVES, NC_INDICES):
    ax1.plot(OCTAVE_BANDS, row, color="#bbbbbb", lw=0.8)
ax1.plot(OCTAVE_BANDS, spl, "o-", label="Measured")
gov = spl[OCTAVE_BANDS == nc.governing_frequency][0]
ax1.plot([nc.governing_frequency], [gov], "D", color="#d62728")
ax1.set_xscale("log"); ax1.set_title(f"NC-{nc.rating:g}")

ref = rc.reference_curve
low, high = OCTAVE_BANDS <= 500, OCTAVE_BANDS >= 1000
ax2.plot(OCTAVE_BANDS, ref, "s--", color="#7f7f7f", label=f"Reference RC-{rc.rating}")
ax2.fill_between(OCTAVE_BANDS[low], ref[low], ref[low] + 5, color="#ffbb78", alpha=0.35)
ax2.fill_between(OCTAVE_BANDS[high], ref[high], ref[high] + 3, color="#aec7e8", alpha=0.45)
ax2.plot(OCTAVE_BANDS, spl, "o-", label="Measured")
ax2.set_xscale("log"); ax2.set_title(rc.label)
plt.show()
```

</details>

El `NCResult` lleva la calificación `rating`, la `governing_frequency` y los
`levels` medidos; el `RCResult` lleva la calificación `rating`, la `lmf`, la
`classification`, la `reference_curve` y una etiqueta `label` de conveniencia en
la forma `RC-NN(A)`. Cada uno expone un `.plot()` que dibuja su panel de arriba.

Los criterios de ruido balanceados (NCB), el criterio de ruido de sala para
ruido de baja frecuencia fluctuante (RNC, que necesita una serie temporal en
lugar de un único espectro) y el índice numérico de evaluación de calidad (QAI,
que la norma remite a referencias externas) no forman parte de este módulo.

---

**Normas.** ANSI/ASA S12.2-2019, *Criteria for Evaluating Room Noise* — las
curvas NC y el método de tangencia (Tabla 1), y las curvas RC Mark II (Anexo D,
Tabla D.1), la calificación por media de frecuencias medias (cláusula D.4) y la
etiqueta espectral neutro/retumbo/siseo (cláusula D.3).
