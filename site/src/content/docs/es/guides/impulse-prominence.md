---
title: "Prominencia de sonidos impulsivos (NT ACOU 112)"
description: "El método Nordtest NT ACOU 112:2002 para la prominencia de los sonidos impulsivos: la prominencia prevista P a partir de la tasa de crecimiento y la diferencia de nivel de cada impulso (cláusula 7), el ajuste graduado KI que se suma al LAeq (cláusula 8) y el nivel de evaluación sobre un intervalo de tiempo de referencia."
---

El ruido con impulsos prominentes — martilleo, remachado, hinca de pilotes — es
más molesto que un sonido estacionario del mismo nivel equivalente. **NT ACOU
112:2002** (un método Nordtest) cuantifica cuán *prominente* es un impulso y lo
convierte en un ajuste graduado `KI` que se suma al `LAeq` medido. La
prominencia se lee de dos propiedades del arranque de cada impulso en el
historial de nivel ponderado A con ponderación temporal F: la rapidez con que
crece (la **tasa de crecimiento**) y cuánto crece (la **diferencia de nivel**).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ntacou112_es.svg" alt="Flujo desde el historial de nivel ponderado A (un arranque es donde el gradiente supera 10 dB/s) hasta la tasa de crecimiento y la diferencia de nivel, la prominencia prevista P = 3 lg(OR) + 2 lg(LD), el ajuste KI = 1,8 (P - 5) para P mayor que 5, y el nivel de evaluación sobre el tiempo de referencia" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ntacou112_es_dark.svg" alt="Flujo desde el historial de nivel ponderado A (un arranque es donde el gradiente supera 10 dB/s) hasta la tasa de crecimiento y la diferencia de nivel, la prominencia prevista P = 3 lg(OR) + 2 lg(LD), el ajuste KI = 1,8 (P - 5) para P mayor que 5, y el nivel de evaluación sobre el tiempo de referencia" style="width:82%">

## 1. Prominencia prevista (cláusula 7)

Para cada impulso candidato, la **prominencia prevista** `P` combina la tasa de
crecimiento (en dB/s) y la diferencia de nivel (en dB) en escala logarítmica
(Fórmula 1):

$$
P = 3\,\lg(\text{tasa de crecimiento}) + 2\,\lg(\text{diferencia de nivel}).
$$

Los coeficientes se ajustaron a partir de ensayos de escucha y `P` está diseñada
para alcanzar unos 15 en impulsos muy súbitos e intensos. El impulso con la `P`
**más alta** en un periodo de 30 minutos es el determinante. Una subida de
nivel solo *cualifica* como impulso cuando su tasa de subida supera 10 dB/s
(apartado 4.5; el apartado 8 aplica el ajuste únicamente «para sonidos con
tasas de subida mayores de 10 dB/s»): `impulse_prominence` marca los eventos
no cualificados en su máscara `qualifies`, avisa de ellos y nunca les permite
fijar la prominencia determinante ni un `KI` (el ajuste es 0 dB cuando ningún
evento cualifica).

```python
import phonometry as ph

# Tres impulsos candidatos: (tasa de crecimiento dB/s, diferencia de nivel dB).
result = ph.impulse_prominence([1200.0, 300.0, 60.0], [32.0, 18.0, 11.0])
print(result.per_impulse.round(2))  # [12.25  9.94  7.42]
print(round(result.prominence, 2))  # 12.25  (el impulso determinante)
print(round(result.adjustment, 2))  # 13.05  dB
```

Un solo impulso se evalúa directamente con `predicted_prominence`:

```python
import phonometry as ph

# P = 3*lg(1000) + 2*lg(30) = 9 + 2.95 = 11.95.
print(round(ph.predicted_prominence(1000.0, 30.0), 4))  # 11.9542
```

## 2. Ajuste al LAeq (cláusula 8)

Por debajo de una prominencia de 5 el impulso no es lo bastante audible como para
importar; por encima, el ajuste crece linealmente (Fórmula 2):

$$
K_I = 1{,}8\,(P - 5)\ \text{dB} \quad (P > 5), \qquad K_I = 0 \quad (P \le 5).
$$

```python
import phonometry as ph

print(float(ph.impulse_adjustment(10.0)))  # 9.0 dB
print(float(ph.impulse_adjustment(5.0)))   # 0.0 dB (en el umbral)
```

El ajuste se aplica al `LAeq,30min` del evento con la prominencia más alta. El
**nivel de evaluación** sobre un tiempo de referencia mayor combina los niveles
equivalentes ajustados por impulso de los subintervalos (cláusula 8, Nota 1):

$$
L_{Ar,T} = 10\,\lg\!\left(\frac{1}{T}\sum_N \Delta t_N\,
10^{(L_{Aeq,N} + K_{I,N})/10}\right).
$$

```python
import phonometry as ph

# Dos periodos de 30 min: uno impulsivo (KI = 7.6 dB), otro tranquilo.
print(round(ph.rating_level([72.0, 66.0], [7.6, 0.0], [30.0, 30.0], 60.0), 2))
# 76.78 dB
```

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_onset_detection_es.webm" autoplay loop muted controls playsinline title="Animación: una historia de nivel ponderado A dibujándose, con el tramo de inicio (gradiente por encima de 10 dB/s) resaltado y la tasa de inicio, la diferencia de nivel, la prominencia P y el ajuste KI en vivo" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_onset_detection_es_dark.webm" autoplay loop muted controls playsinline title="Animación: una historia de nivel ponderado A dibujándose, con el tramo de inicio (gradiente por encima de 10 dB/s) resaltado y la tasa de inicio, la diferencia de nivel, la prominencia P y el ajuste KI en vivo" style="width:88%"></video>

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_prominence_es.svg" alt="Izquierda: la prominencia prevista P creciendo con la tasa de crecimiento (eje logarítmico) para diferencias de nivel de 5, 15 y 30 dB, llegando a unos 15 en un impulso súbito e intenso. Derecha: el ajuste KI, plano en cero hasta el umbral P = 5 y luego lineal, con tres impulsos marcados y el determinante en KI = 13 dB" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_prominence_es_dark.svg" alt="Izquierda: la prominencia prevista P creciendo con la tasa de crecimiento (eje logarítmico) para diferencias de nivel de 5, 15 y 30 dB, llegando a unos 15 en un impulso súbito e intenso. Derecha: el ajuste KI, plano en cero hasta el umbral P = 5 y luego lineal, con tres impulsos marcados y el determinante en KI = 13 dB" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

# Una línea para la curva de ajuste con los impulsos marcados:
ph.impulse_prominence([1200.0, 300.0, 60.0], [32.0, 18.0, 11.0]).plot()
plt.show()

# A mano, el panel izquierdo — P frente a la tasa de crecimiento para tres LD:
orate = np.logspace(1, 4, 200)
for ld in (5.0, 15.0, 30.0):
    plt.plot(orate, ph.predicted_prominence(orate, np.full_like(orate, ld)),
             label=f"LD = {ld:g} dB")
plt.xscale("log"); plt.legend(); plt.show()
```

</details>

El `ImpulseProminenceResult` lleva las prominencias `per_impulse`, la `prominence`
determinante y su `adjustment`, y su `.plot()` dibuja la curva `KI(P)` con los
impulsos marcados. El método es un complemento a la medida de ruido ambiental de
[ISO 1996-2](/phonometry/es/guides/levels/).

---

**Normas.** NT ACOU 112:2002 (Nordtest), *Prominence of impulsive sounds and for
adjustment of LAeq* — la prominencia prevista (cláusula 7, Fórmula 1), el ajuste
al LAeq (cláusula 8, Fórmula 2) y el nivel de evaluación (cláusula 8, Nota 1),
con el arranque definido en las cláusulas 4.5-4.7.

## Véase también

- Referencia de la API: [`environmental.impulse_prominence`](/phonometry/es/reference/api/environment/impulse-prominence/).
