---
title: "Propagación submarina del sonido"
description: "Propagación submarina de forma cerrada: ensanchamiento geométrico más absorción de volumen (Francois-Garrison, Ainslie-McColm, Thorp), la velocidad del sonido en agua de mar (UNESCO/Chen-Millero, Del Grosso, Mackenzie), la ecuación del sonar, la pérdida por reflexión en el fondo (Rayleigh) y el espectro de ruido ambiental oceánico (viento/térmico de Wenz más tráfico marítimo JOMOPANS-ECHO)."
---

Propagación submarina de forma cerrada, complemento de los niveles de referencia
de la página de [Acústica submarina](/phonometry/es/guides/underwater-acoustics/):
la **pérdida por transmisión**, la **velocidad del sonido** en agua de mar, la
**ecuación del sonar**, la **pérdida por reflexión en el fondo** y el espectro de
**ruido ambiental oceánico**.

## Pérdida por transmisión

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss_es.svg" alt="Pérdida por transmisión submarina frente a la distancia a 10 kHz, con las contribuciones de ensanchamiento geométrico y absorción de volumen dibujadas por separado, la pérdida creciente hacia abajo" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss_es_dark.svg" alt="Pérdida por transmisión submarina frente a la distancia a 10 kHz, con las contribuciones de ensanchamiento geométrico y absorción de volumen dibujadas por separado, la pérdida creciente hacia abajo" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import underwater

# 10 kHz a 10 °C, 35 ppt y 100 m de profundidad; ensanchamiento "practical" con R0 = 1000 m.
ranges = np.linspace(10.0, 20_000.0, 400)
tl = underwater.transmission_loss(ranges, 10e3, law="practical",
                                  transition_range=1000.0, temperature=10.0,
                                  salinity=35.0, depth=100.0)
print(f"alpha = {tl.absorption_coefficient:.2f} dB/km")   # alpha = 0.95 dB/km
tl.plot()   # TL total con las contribuciones de ensanchamiento y absorción
plt.show()
```

</details>

La pérdida por transmisión es

$$
TL = \text{ensanchamiento} + \alpha R .
$$

El ensanchamiento geométrico es $20 \lg R$ (esférico), $10 \lg R$ (cilíndrico)
o esférico hasta una distancia de transición $R_0$ y cilíndrico más allá
de esta (`"practical"`). El coeficiente de absorción de volumen $\alpha$ (dB/km)
procede de **Francois–Garrison** (1982, por
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

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import underwater

# Capa de mezcla cálida, termoclina hasta 4 °C y capa profunda isoterma.
depths = np.linspace(0.0, 3000.0, 121)
temps = 4.0 + 14.0 / (1.0 + (np.maximum(depths - 80.0, 0.0) / 250.0) ** 2)
profile = underwater.sound_speed_profile(depths, temps, 35.0, model="unesco")
profile.plot()   # velocidad del sonido frente a profundidad, mínimo en el eje del canal
plt.show()
```

</details>

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

El mínimo de $c(z)$ actúa como una guía de ondas (el canal SOFAR): los frentes
de onda que se apartan del eje se refractan de vuelta hacia él, mientras que
el sonido generado fuera del canal se fuga hacia el fondo, como muestra la
simulación siguiente con un gradiente exagerado a propósito. Este atrapamiento
es la razón de que el sonido de baja frecuencia pueda cruzar océanos enteros.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: simulación FDTD 2D de un pulso de baja frecuencia en un canal sonoro submarino tipo SOFAR con el perfil de velocidad del sonido dibujado junto al campo; lanzados en el eje del canal los frentes de onda se refractan de vuelta hacia el mínimo de velocidad y quedan atrapados, lanzada cerca de la superficie la energía cruza el canal y se fuga hacia el fondo" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: simulación FDTD 2D de un pulso de baja frecuencia en un canal sonoro submarino tipo SOFAR con el perfil de velocidad del sonido dibujado junto al campo; lanzados en el eje del canal los frentes de onda se refractan de vuelta hacia el mínimo de velocidad y quedan atrapados, lanzada cerca de la superficie la energía cruza el canal y se fuga hacia el fondo" style="width:88%"></video>

## Ecuación del sonar

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation_es.svg" alt="Ecuación del sonar pasivo: el exceso de señal cae con la pérdida por transmisión y cruza el cero, el límite de detección, en la figura de mérito" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation_es_dark.svg" alt="Ecuación del sonar pasivo: el exceso de señal cae con la pérdida por transmisión y cruza el cero, el límite de detección, en la figura de mérito" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import underwater

tl = np.linspace(40.0, 120.0, 400)
se = underwater.passive_sonar_equation(source_level=140.0, transmission_loss=tl,
                                       noise_level=60.0, directivity_index=15.0,
                                       detection_threshold=8.0)
print(f"figura de mérito = {se.figure_of_merit:.1f} dB")  # figura de mérito = 87.0 dB
se.plot()   # exceso de señal frente a pérdida por transmisión, cruce por cero en la FOM
plt.show()
```

</details>

La ecuación del sonar da el **exceso de señal** $SE$ (detección cuando
$SE \ge 0$) y la **figura de mérito** (la máxima pérdida por transmisión
admisible en $SE = 0$):

$$
SE = SL - TL - (NL - DI) - DT \ \ \text{(pasiva)},
$$

$$
SE = SL - 2\,TL + TS - (NL - DI) - DT \ \ \text{(activa, monostática)},
$$

o limitada por reverberación con $RL$ en lugar de $NL - DI$.

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

Los niveles de sonar, propagación y ambiental están en dB re una onda plana de
1 µPa rms (niveles espectrales). Los niveles de fuente (más abajo) usan la
convención de fuente, dB re 1 µPa²/Hz **a 1 m**.

## Pérdida por reflexión en el fondo

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seabed_reflection_es.svg" alt="Pérdida por reflexión en el fondo frente al ángulo rasante para un fondo arenoso rápido: pérdida nula por debajo del ángulo rasante crítico, creciendo bruscamente por encima" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seabed_reflection_es_dark.svg" alt="Pérdida por reflexión en el fondo frente al ángulo rasante para un fondo arenoso rápido: pérdida nula por debajo del ángulo rasante crítico, creciendo bruscamente por encima" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import underwater

# Reflexión de Rayleigh fluido-fluido: agua sobre un fondo arenoso rápido.
phi = np.linspace(0.0, 90.0, 361)
bl = underwater.bottom_reflection_loss(phi, rho1=1000.0, c1=1500.0,
                                       rho2=1900.0, c2=1650.0)
print(f"ángulo crítico = {bl.critical_angle:.1f} deg")   # ángulo crítico = 24.6 deg
bl.plot()   # pérdida en el fondo frente al ángulo rasante
plt.show()
```

</details>

Una onda plana que incide en el fondo se refleja con el **coeficiente de
reflexión de Rayleigh** fluido–fluido (Medwin & Clay). Para un fondo más rápido ($c_2 > c_1$)
existe un **ángulo rasante crítico** $\varphi_c = \arccos(c_1/c_2)$, por
debajo del cual la onda se refleja totalmente ($|R| = 1$, pérdida nula). La
pérdida es $BL = -20 \lg |R|$.

```python
import numpy as np
import phonometry as ph

phi = np.linspace(0.0, 90.0, 361)   # ángulo rasante desde la interfaz, grados
bl = ph.bottom_reflection_loss(phi, rho1=1000.0, c1=1500.0,   # agua
                               rho2=1900.0, c2=1650.0)          # arena
print(bl.critical_angle)            # 24,6°
bl.plot()   # pérdida por reflexión frente al ángulo rasante
```

## Ruido ambiental oceánico

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ocean_ambient_noise_es.svg" alt="Niveles espectrales de ruido ambiental de Wenz para dos velocidades de viento, con el ruido de viento cayendo 5 dB por octava y el ruido térmico creciendo por encima de unos 50 kHz" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ocean_ambient_noise_es_dark.svg" alt="Niveles espectrales de ruido ambiental de Wenz para dos velocidades de viento, con el ruido de viento cayendo 5 dB por octava y el ruido térmico creciendo por encima de unos 50 kHz" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import underwater

# Ruido ambiental de Wenz (regla de los cincos + térmico de Mellen) a dos vientos.
freqs = np.logspace(2, 5.5, 300)
fig, ax = plt.subplots()
for u in (5.0, 20.0):
    noise = underwater.ocean_ambient_noise(freqs, wind_speed_knots=u)
    ax.semilogx(noise.frequency, noise.spectrum_level, label=f"Total ({u:.0f} kn)")
ax.semilogx(freqs, underwater.thermal_noise_spectrum(freqs), ":", label="Térmico")
ax.set(xlabel="Frecuencia [Hz]", ylabel="Nivel espectral [dB re 1 µPa²/Hz]")
ax.legend()
ax.grid(True, which="both", alpha=0.3)
plt.show()
```

</details>

El nivel espectral de ruido ambiental es la suma energética de las componentes
físicas de Wenz: el ruido de **viento / superficie** por la "regla de los cincos"
(el ancla histórica de 25 dB a 1 kHz con 5 nudos es re 20 µPa, es decir ~51 dB
re 1 µPa; válida en ~500 Hz–5 kHz) y el ruido **térmico de
Mellen** (dominante por encima de ~50 kHz). El rango amplio del ejemplo mantiene
la curva de viento más allá de ~5 kHz solo como extrapolación para mostrar el
cruce con el térmico. El espectro de **tráfico** lo aporta quien llama.

```python
import numpy as np
import phonometry as ph

freqs = np.logspace(2, 5.5, 300)
noise = ph.ocean_ambient_noise(freqs, wind_speed_knots=15.0)
noise.plot()   # espectro compuesto con las componentes viento/térmico
```

## Nivel de fuente del tráfico marítimo

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ship_traffic_noise_es.svg" alt="Espectros de nivel de fuente predichos por JOMOPANS-ECHO para un portacontenedores, un crucero y un remolcador, con los buques de carga mostrando una joroba de baja frecuencia por debajo de 100 Hz" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ship_traffic_noise_es_dark.svg" alt="Espectros de nivel de fuente predichos por JOMOPANS-ECHO para un portacontenedores, un crucero y un remolcador, con los buques de carga mostrando una joroba de baja frecuencia por debajo de 100 Hz" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
from phonometry import underwater

# Espectros de fuente JOMOPANS-ECHO para tres clases de buque (velocidad, eslora).
fig, ax = plt.subplots()
for vessel_class, speed, length in (("containership", 18.0, 300.0),
                                    ("cruise", 17.1, 250.0),
                                    ("tug", 3.7, 30.0)):
    s = underwater.ship_source_spectrum(speed, length, vessel_class=vessel_class)
    ax.semilogx(s.frequency, s.source_psd,
                label=f"{vessel_class} ({speed:.0f} kn, {length:.0f} m)")
ax.set(xlabel="Frecuencia [Hz]",
       ylabel="Densidad espectral de fuente [dB re 1 µPa²/Hz a 1 m]")
ax.legend()
ax.grid(True, which="both", alpha=0.3)
plt.show()
```

</details>

Cuando no hay espectro medido, el nivel de fuente de un buque puede
**estimarse** a partir de su clase, velocidad y eslora con **JOMOPANS-ECHO**
(MacGillivray & de Jong 2021, por defecto, validado contra 1862 medidas),
**RANDI 3.1** o **Wales & Heitmeyer** (2002).

```python
import phonometry as ph

ship = ph.ship_source_spectrum(18.0, 300.0, vessel_class="containership")
ship.plot()                     # densidad espectral de fuente frente a frecuencia
print(ph.VESSEL_CLASSES)        # las 13 clases de buque de JOMOPANS-ECHO

# Alimenta la predicción al ruido ambiental como término de tráfico:
noise = ph.ocean_ambient_noise(ship.frequency, wind_speed_knots=10.0,
                               shipping=ship.source_psd)
```

## Solvers numéricos

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/numerical_propagation_es.png" alt="Un perfil de velocidad del sonido de Munk, trayectorias de rayos formando zonas de convergencia, y la pérdida por transmisión de modos normales frente a la ecuación parabólica coincidiendo en tendencia" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/numerical_propagation_es_dark.png" alt="Un perfil de velocidad del sonido de Munk, trayectorias de rayos formando zonas de convergencia, y la pérdida por transmisión de modos normales frente a la ecuación parabólica coincidiendo en tendencia" style="width:100%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import underwater

# Un perfil de Munk de velocidad del sonido en aguas profundas.
z = np.linspace(0.0, 5000.0, 60)
eta = 2.0 * (z - 1300.0) / 1300.0
c = 1500.0 * (1.0 + 0.00737 * (eta - 1.0 + np.exp(-eta)))

# PE split-step de Fourier a 50 Hz; una malla gruesa mantiene el cálculo rápido.
field = underwater.parabolic_equation(50.0, z, c, source_depth=1000.0,
                                      max_range=50_000.0, range_step=50.0,
                                      n_depth_points=512)
field.plot()   # campo TL(z, r) mostrando las zonas de convergencia
plt.show()
```

</details>

Para entornos independientes de la distancia el campo puede calcularse
numéricamente con tres solvers (Jensen et al., *Computational Ocean Acoustics*):

- **`normal_modes`** — el problema de autovalores de Sturm-Liouville separado en
  profundidad, resuelto por diferencias finitas y sumado en pérdida por
  transmisión (validado contra los modos exactos de la guía ideal).
- **`ray_trace`** — las ecuaciones de trayectoria de rayos integradas con
  Runge-Kutta, vectorizadas sobre todos los rayos a la vez (validado contra los
  arcos de círculo de un gradiente lineal).
- **`parabolic_equation`** — la PE estándar (Tappert) por el algoritmo split-step
  de Fourier (validado contra el esparcimiento esférico en campo libre).

```python
import numpy as np
import phonometry as ph

z = np.linspace(0.0, 5000.0, 60)
eta = 2.0 * (z - 1300.0) / 1300.0
c = 1500.0 * (1.0 + 0.00737 * (eta - 1.0 + np.exp(-eta)))   # perfil de Munk
ph.ray_trace(z, c, source_depth=1000.0,
             launch_angles_deg=np.linspace(-12, 12, 21), max_range=100e3).plot()

modes = ph.normal_modes(50.0, [0.0, 200.0], [1500.0, 1500.0],
                        source_depth=50.0, receiver_depth=100.0)
ph.parabolic_equation(50.0, [0.0, 200.0], [1500.0, 1500.0],
                      source_depth=50.0, max_range=20e3).plot()
```

Los tres asumen una columna de agua independiente de la distancia con superficie
de presión-liberada.

## Referencias

- Francois, R. E., & Garrison, G. R. (1982). Sound absorption based on ocean
  measurements: Part I: Pure water and magnesium sulfate contributions.
  *The Journal of the Acoustical Society of America*, 72(3), 896-907.
  [doi:10.1121/1.388170](https://doi.org/10.1121/1.388170).
  Las componentes de agua pura y sulfato de magnesio del modelo de absorción por
  defecto de la sección de pérdida por transmisión.
- Francois, R. E., & Garrison, G. R. (1982). Sound absorption based on ocean
  measurements. Part II: Boric acid contribution and equation for total
  absorption. *The Journal of the Acoustical Society of America*, 72(6),
  1879-1890.
  [doi:10.1121/1.388673](https://doi.org/10.1121/1.388673).
  El término de ácido bórico y la ecuación completa de absorción total de
  Francois-Garrison, el modelo por defecto implementado.
- Ainslie, M. A., & McColm, J. G. (1998). A simplified formula for viscous and
  chemical absorption in sea water. *The Journal of the Acoustical Society of
  America*, 103(3), 1671-1672.
  [doi:10.1121/1.421258](https://doi.org/10.1121/1.421258).
  El modelo de absorción simplificado y legible (`"ainslie-mccolm"`).
- Thorp, W. H. (1967). Analytic description of the low-frequency attenuation
  coefficient. *The Journal of the Acoustical Society of America*, 42(1), 270.
  [doi:10.1121/1.1910566](https://doi.org/10.1121/1.1910566).
  La fórmula de absorción de baja frecuencia dependiente solo de la frecuencia (`"thorp"`).
- Chen, C.-T., & Millero, F. J. (1977). Speed of sound in seawater at high
  pressures. *The Journal of the Acoustical Society of America*, 62(5),
  1129-1135.
  [doi:10.1121/1.381646](https://doi.org/10.1121/1.381646).
  La ecuación de velocidad del sonido UNESCO, el estándar internacional.
- Wong, G. S. K., & Zhu, S. (1995). Speed of sound in seawater as a function
  of salinity, temperature, and pressure. *The Journal of the Acoustical
  Society of America*, 97(3), 1732-1736.
  [doi:10.1121/1.413048](https://doi.org/10.1121/1.413048).
  La reformulación ITS-90 de los coeficientes UNESCO, la forma implementada.
- Del Grosso, V. A. (1974). New equation for the speed of sound in natural
  waters (with comparisons to other equations). *The Journal of the
  Acoustical Society of America*, 56(4), 1084-1091.
  [doi:10.1121/1.1903388](https://doi.org/10.1121/1.1903388).
  La ecuación alternativa de velocidad del sonido basada en presión
  (`"del-grosso"`).
- Mackenzie, K. V. (1981). Nine-term equation for sound speed in the oceans.
  *The Journal of the Acoustical Society of America*, 70(3), 807-812.
  [doi:10.1121/1.386920](https://doi.org/10.1121/1.386920).
  La ecuación de nueve términos basada en profundidad y su valor de
  comprobación de 1550.744 m/s.
- Leroy, C. C., & Parthiot, F. (1998). Depth-pressure relationships in the
  oceans and seas. *The Journal of the Acoustical Society of America*, 103(3),
  1346-1352.
  [doi:10.1121/1.421275](https://doi.org/10.1121/1.421275).
  La conversión de profundidad a presión que alimenta las ecuaciones UNESCO
  y Del Grosso.
- Urick, R. J. (1983). *Principles of underwater sound* (3.ª ed.).
  McGraw-Hill; reimpreso en 1996 por Peninsula Publishing.
  ISBN 978-0-932146-62-5.
  [Ficha en Open Library](https://openlibrary.org/books/OL9317725M).
  El marco de la ecuación del sonar (exceso de señal, figura de mérito).
- Medwin, H., & Clay, C. S. (1998). *Fundamentals of acoustical oceanography*.
  Academic Press. ISBN 978-0-12-487570-8.
  [Página del editor](https://shop.elsevier.com/books/fundamentals-of-acoustical-oceanography/medwin/978-0-12-487570-8).
  El coeficiente de reflexión de Rayleigh fluido-fluido y el ángulo rasante
  crítico de la sección de reflexión en el fondo.
- Wenz, G. M. (1962). Acoustic ambient noise in the ocean: Spectra and
  sources. *The Journal of the Acoustical Society of America*, 34(12),
  1936-1956.
  [doi:10.1121/1.1909155](https://doi.org/10.1121/1.1909155).
  El estudio de ruido ambiental tras las componentes eólica y térmica de
  la sección de ruido ambiental oceánico.
- Carey, W. M., & Evans, R. B. (2011). *Ocean ambient noise: Measurement and
  theory*. Springer.
  [doi:10.1007/978-1-4419-7832-5](https://doi.org/10.1007/978-1-4419-7832-5).
  El anclaje de la "regla de los cincos" del viento y la derivación del ruido
  térmico de Mellen.
- MacGillivray, A., & de Jong, C. (2021). A reference spectrum model for
  estimating source levels of marine shipping based on automated
  identification system data. *Journal of Marine Science and Engineering*,
  9(4), 369.
  [doi:10.3390/jmse9040369](https://doi.org/10.3390/jmse9040369).
  El modelo de nivel de fuente de buques JOMOPANS-ECHO (acceso abierto); su
  calculadora del archivo S1 es el oráculo de validación.
- Wales, S. C., & Heitmeyer, R. M. (2002). An ensemble source spectra model
  for merchant ship-radiated noise. *The Journal of the Acoustical Society of
  America*, 111(3), 1211-1231.
  [doi:10.1121/1.1427355](https://doi.org/10.1121/1.1427355).
  El modelo de espectro de conjunto de buques mercantes de la sección de
  tráfico marítimo.
- Jensen, F. B., Kuperman, W. A., Porter, M. B., & Schmidt, H. (2011).
  *Computational ocean acoustics* (2.ª ed.). Springer.
  [doi:10.1007/978-1-4419-8678-8](https://doi.org/10.1007/978-1-4419-8678-8).
  Los solvers de modos normales, trazado de rayos y ecuación parabólica
  split-step Fourier de la sección de solvers numéricos.

## Véase también

- Referencia de la API: [`underwater.propagation`](/phonometry/es/reference/api/underwater/propagation/), [`underwater.numerical_propagation`](/phonometry/es/reference/api/underwater/numerical-propagation/) y [`underwater.sound_speed`](/phonometry/es/reference/api/underwater/sound-speed/).
