---
title: "Propagación submarina: pérdida por transmisión, velocidad del sonido y ecuación del sonar"
description: "Propagación submarina de forma cerrada: ensanchamiento geométrico más absorción de volumen (Francois-Garrison, Ainslie-McColm, Thorp), la velocidad del sonido en agua de mar (UNESCO/Chen-Millero, Del Grosso, Mackenzie) y la ecuación del sonar pasiva/activa."
---

Propagación submarina de forma cerrada, complemento de los niveles de referencia
de la página de [Acústica submarina](/phonometry/es/guides/underwater-acoustics/):
la **pérdida por transmisión**, la **velocidad del sonido** en agua de mar y la
**ecuación del sonar**.

## Pérdida por transmisión

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss_es.svg" alt="Pérdida por transmisión submarina frente a la distancia a 10 kHz, con las contribuciones de ensanchamiento geométrico y absorción de volumen dibujadas por separado, la pérdida creciente hacia abajo" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss_es_dark.svg" alt="Pérdida por transmisión submarina frente a la distancia a 10 kHz, con las contribuciones de ensanchamiento geométrico y absorción de volumen dibujadas por separado, la pérdida creciente hacia abajo" style="width:82%">

La pérdida por transmisión es `TL = ensanchamiento + α·R`. El ensanchamiento
geométrico es `20·lg R` (esférico), `10·lg R` (cilíndrico) o esférico hasta una
distancia de transición y cilíndrico después (`"practical"`). El coeficiente de
absorción de volumen `α` (dB/km) procede de **Francois–Garrison** (1982, por
defecto y de referencia), **Ainslie–McColm** (1998) o **Thorp** (1967, solo
frecuencia); los dos primeros coinciden en ~10 % entre 100 Hz y 1 MHz.

```python
import numpy as np
import phonometry as ph

ranges = np.linspace(10.0, 20_000.0, 400)
tl = ph.transmission_loss(ranges, 10e3, law="practical", transition_range=1000.0,
                          temperature=10.0, salinity=35.0, depth=100.0)
print(tl.absorption_coefficient, tl.tl[-1])
tl.plot()   # TL frente a distancia con la separación ensanchamiento/absorción
```

## Velocidad del sonido en agua de mar

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_sound_speed_es.svg" alt="Perfil de velocidad del sonido en agua de mar con la ecuación UNESCO: capa de mezcla cálida, termoclina, eje del canal sonoro en el mínimo y la velocidad creciendo con la presión en profundidad" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_sound_speed_es_dark.svg" alt="Perfil de velocidad del sonido en agua de mar con la ecuación UNESCO: capa de mezcla cálida, termoclina, eje del canal sonoro en el mínimo y la velocidad creciendo con la presión en profundidad" style="width:60%">

`sea_water_sound_speed(T, S, depth, model=…)` usa la ecuación **UNESCO /
Chen–Millero** (por defecto, en la forma Wong & Zhu 1995 ITS-90), **Del Grosso**
(1974) o **Mackenzie** (1981). La profundidad se convierte a presión con
Leroy & Parthiot (1998). Las tres coinciden en ~1 m/s; el valor de verificación
canónico de Mackenzie es `1550,744 m/s` a 25 °C, 35 ‰, 1000 m.

```python
import numpy as np
import phonometry as ph

c = ph.sea_water_sound_speed(25.0, 35.0, 1000.0, model="mackenzie")  # 1550,744
depths = np.linspace(0.0, 3000.0, 121)
temps = 4.0 + 14.0 / (1.0 + (np.maximum(depths - 80.0, 0.0) / 250.0) ** 2)
profile = ph.sound_speed_profile(depths, temps, 35.0, model="unesco")
profile.plot()   # velocidad del sonido frente a profundidad
```

## Ecuación del sonar

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation_es.svg" alt="Ecuación del sonar pasivo: el exceso de señal cae con la pérdida por transmisión y cruza el cero, el límite de detección, en la figura de mérito" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation_es_dark.svg" alt="Ecuación del sonar pasivo: el exceso de señal cae con la pérdida por transmisión y cruza el cero, el límite de detección, en la figura de mérito" style="width:82%">

La ecuación del sonar da el **exceso de señal** `SE` (detección cuando
`SE ≥ 0`) y la **figura de mérito** (la máxima pérdida por transmisión admisible
en `SE = 0`). Pasiva: `SE = SL − TL − (NL − DI) − DT`. Activa (monostática):
`SE = SL − 2·TL + TS − (NL − DI) − DT`, o limitada por reverberación con `RL`.

```python
import numpy as np
import phonometry as ph

tl = np.linspace(40.0, 120.0, 400)
se = ph.passive_sonar_equation(source_level=140.0, transmission_loss=tl,
                               noise_level=60.0, directivity_index=15.0,
                               detection_threshold=8.0)
print(se.figure_of_merit)
se.plot()   # exceso de señal frente a pérdida por transmisión
```

Todos los niveles están en dB (re una onda plana de 1 µPa rms; niveles
espectrales). Los solvers numéricos (trazado de rayos, modos normales, ecuación
parabólica) son una adición futura aparte.
