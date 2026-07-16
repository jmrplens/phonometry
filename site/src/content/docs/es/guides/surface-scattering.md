---
title: "Dispersión superficial, difusión y absorción in situ"
description: "Cómo devuelve una superficie el sonido incidente: el coeficiente de dispersión (scattering) de incidencia aleatoria en sala reverberante (ISO 17497-1), el coeficiente de difusión por autocorrelación de un goniómetro en campo libre (ISO 17497-2) y la absorción in situ de pavimentos por la técnica de sustracción (ISO 13472-1) y el método de tubo puntual (ISO 13472-2)."
---

Cómo devuelve una superficie el sonido incidente —cuánto dispersa fuera de la
dirección especular, con qué uniformidad reparte lo que dispersa y cuánto
absorbe— se mide con una familia de métodos dedicados. La **sala reverberante**
proporciona el *coeficiente de dispersión* de incidencia aleatoria de una
superficie comparando las caídas con la muestra inmóvil y en rotación
(ISO 17497-1). Un **goniómetro en campo libre** mide la respuesta polar del
sonido reflejado y la condensa en un *coeficiente de difusión* (ISO 17497-2). Y
sobre un pavimento, un altavoz y un solo micrófono recuperan la *absorción in
situ* del firme, ya sea sobre una superficie extensa restando la onda incidente
(ISO 13472-1) o a través de un pequeño tubo apoyado sobre la superficie
(ISO 13472-2). Esta página cubre los cuatro.

Los coeficientes de dispersión y de difusión responden a preguntas distintas y no
son intercambiables: la dispersión es *cuánta* energía abandona la dirección
especular; la difusión es *cuán uniformemente* se reparte en ángulo la energía
reflejada.

## 1. Coeficiente de dispersión de incidencia aleatoria (ISO 17497-1)

El coeficiente de dispersión $s$ es la fracción de energía reflejada que **no**
abandona la superficie en la dirección especular. ISO 17497-1 lo mide en una sala
reverberante a partir de cuatro situaciones de tiempo de reverberación: con la
muestra de ensayo montada sobre una plataforma giratoria y mantenida
**inmóvil**, y con la plataforma **en rotación** (que promedia y elimina la
reflexión especular coherente en fase), cada una con y sin una placa base
reflectante.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_scattering_reverb_es.svg" alt="Montaje de dispersión de incidencia aleatoria de ISO 17497-1: una sala reverberante con la muestra de ensayo sobre una plataforma giratoria, un brazo de altavoz giratorio y un micrófono, midiendo el tiempo de reverberación con la muestra inmóvil (que da la absorción de incidencia aleatoria) y en rotación (que da la absorción especular), a partir de los cuales se deriva el coeficiente de dispersión" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_scattering_reverb_es_dark.svg" alt="Montaje de dispersión de incidencia aleatoria de ISO 17497-1: una sala reverberante con la muestra de ensayo sobre una plataforma giratoria, un brazo de altavoz giratorio y un micrófono, midiendo el tiempo de reverberación con la muestra inmóvil (que da la absorción de incidencia aleatoria) y en rotación (que da la absorción especular), a partir de los cuales se deriva el coeficiente de dispersión" style="width:92%">

**Absorción a partir del tiempo de reverberación (cláusula 6).** Cada situación se
convierte en un coeficiente de absorción de Sabine con el propio término de
atenuación del aire de la norma:

$$
\alpha = 55{,}3\,\frac{V}{S}\left(\frac{1}{c_2 T_2} - \frac{1}{c_1 T_1}\right)
        - 4\,\frac{V}{S}\,(m_2 - m_1),
$$

donde $V$ es el volumen de la sala, $S$ el área de la muestra, $T$ el tiempo de
reverberación, $c$ la velocidad del sonido (ec. (2): $c = 343{,}2\sqrt{(273{,}15+t)/293{,}15}$)
y $m$ el coeficiente de atenuación en potencia del aire. El par **inmóvil** da la
absorción de incidencia aleatoria $\alpha_s$ (ec. (1)); el par **en rotación** da
la absorción especular $\alpha_{spec}$ (ec. (4)).

**Coeficiente de dispersión (ec. (5)).** Ambos se combinan en

$$
s = \frac{\alpha_{spec} - \alpha_s}{1 - \alpha_s}.
$$

Una superficie totalmente especular refleja toda su energía no absorbida en la
dirección especular, de modo que $\alpha_{spec} = \alpha_s$ y $s = 0$; un difusor
fuerte envía energía en todas direcciones, elevando $\alpha_{spec}$ hacia 1 y $s$
hacia 1.

```python
import phonometry as ph

# Cuatro situaciones de tiempo de reverberación reducidas a dos coeficientes de absorción.
# alpha_s del par inmóvil (ec. 1); alpha_spec del par en rotación (ec. 4).
# V = 200 m^3, S = 10 m^2, c = 343.2 m/s en todo momento.
alpha_s = ph.random_incidence_absorption(200.0, 10.0, c1=343.2, T1=8.0,
                                         c2=343.2, T2=6.0)
alpha_spec = ph.specular_absorption_coefficient(200.0, 10.0, c3=343.2, T3=7.5,
                                                c4=343.2, T4=5.0)
s = ph.scattering_coefficient(alpha_spec, alpha_s)   # ec. (5)
print(round(float(alpha_s), 4))     # 0.1343
print(round(float(alpha_spec), 4))  # 0.2148
print(round(float(s), 4))           # 0.0931
```

Sobre una medición completa en tercios de octava, `scattering_coefficient_spectrum`
empareja los $\alpha_{spec}$ y $\alpha_s$ por banda con sus centros de banda y
devuelve un `ScatteringResult` representable:

```python
import numpy as np
import phonometry as ph

# Una medición de 13 bandas (250-4000 Hz): la absorción de incidencia aleatoria
# alpha_s (muestra inmóvil) y la absorción especular alpha_spec (plataforma en
# rotación). Un difusor dispersa más con la frecuencia, así que s(f) crece.
freqs = np.array([250, 315, 400, 500, 630, 800, 1000,
                  1250, 1600, 2000, 2500, 3150, 4000], float)
alpha_s = np.full_like(freqs, 0.10)
alpha_spec = 0.11 + 0.75 * (np.log10(freqs / 250) / np.log10(4000 / 250))

result = ph.scattering_coefficient_spectrum(freqs, alpha_spec, alpha_s)
print(np.round(result.scattering[[0, 6, 12]], 3))   # [0.011 0.428 0.844]
result.plot()   # s(f) en eje de frecuencia logarítmico, de 0 a 1 (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/scattering_coefficient_es.svg" alt="El coeficiente de dispersión de incidencia aleatoria s de una superficie difusora sobre las 13 bandas de tercio de octava de 250 a 4000 Hz, creciendo suavemente desde casi cero a baja frecuencia hasta 0,84 a 4 kHz" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/scattering_coefficient_es_dark.svg" alt="El coeficiente de dispersión de incidencia aleatoria s de una superficie difusora sobre las 13 bandas de tercio de octava de 250 a 4000 Hz, creciendo suavemente desde casi cero a baja frecuencia hasta 0,84 a 4 kHz" style="width:88%">

*El coeficiente de dispersión asciende con la frecuencia: a baja frecuencia el
relieve de la superficie es pequeño frente a la longitud de onda y la reflexión
permanece especular ($s \to 0$); al acortarse la longitud de onda el relieve
dispersa más energía fuera de la dirección especular ($s \to 1$).*

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# result es el ScatteringResult calculado arriba. En una línea:
result.plot()
plt.show()

# A mano, a partir de los campos del resultado, replicando lo que dibuja ScatteringResult.plot():
fig, ax = plt.subplots()
ax.semilogx(result.frequencies, result.scattering, "o-", color="#1f77b4")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Coeficiente de dispersión s")
ax.set_ylim(0.0, 1.0)
ax.set_title("Coeficiente de dispersión de incidencia aleatoria (ISO 17497-1)")
plt.show()
```

</details>

**Comprobación de la placa base (cláusula 6.4, Tabla 1).** La placa base vacía
debe dispersar por sí sola de forma despreciable, o sesgaría el resultado.
ISO 17497-1 limita el coeficiente de dispersión de la placa base por banda de
tercio de octava; la librería expone esos límites y un comprobador.

```python
from phonometry import (
    BASE_PLATE_BANDS, BASE_PLATE_MAX_SCATTERING, check_base_plate_scattering,
)

# Los techos normativos por banda (Tabla 1): 0.05 hasta 500 Hz, ascendiendo a 0.25.
# BASE_PLATE_BANDS es la tupla de bandas; BASE_PLATE_MAX_SCATTERING asigna banda -> techo.
print(BASE_PLATE_BANDS[0], BASE_PLATE_MAX_SCATTERING[100])   # 100 0.05

# Una placa base cuya dispersión medida se mantiene bajo el techo pasa en silencio;
# una banda que lo supera lanza un ScatteringDiffusionWarning que lista las infractoras.
check_base_plate_scattering([0.02] * len(BASE_PLATE_BANDS))
```

## 2. Coeficiente de difusión (ISO 17497-2)

El coeficiente de difusión $d$ mide la **uniformidad espacial** del sonido
reflejado, no cuánto se dispersa. Un goniómetro barre un receptor sobre un arco
polar y registra el nivel reflejado $L_i$ en cada ángulo; el coeficiente es la
autocorrelación normalizada de la distribución de energía polar.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_diffusion_goniometer_es.svg" alt="Goniómetro de difusión en campo libre de ISO 17497-2: una muestra de ensayo sobre una plataforma giratoria, una fuente de altavoz fija y un arco semicircular de micrófonos receptores muestreando la respuesta polar reflejada, a partir de la cual se calcula el coeficiente de difusión por autocorrelación" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_diffusion_goniometer_es_dark.svg" alt="Goniómetro de difusión en campo libre de ISO 17497-2: una muestra de ensayo sobre una plataforma giratoria, una fuente de altavoz fija y un arco semicircular de micrófonos receptores muestreando la respuesta polar reflejada, a partir de la cual se calcula el coeficiente de difusión por autocorrelación" style="width:92%">

**Autocorrelación (fórmula (5)).** Para $n$ receptores con espaciado angular
igual, con $p_i = 10^{L_i/10}$ la energía de banda en el receptor $i$,

$$
d = \frac{\left(\sum_i p_i\right)^2 - \sum_i p_i^2}
         {(n-1)\,\sum_i p_i^2}.
$$

Una respuesta polar perfectamente uniforme ($L_i$ todos iguales) da $d = 1$; un
único lóbulo especular agudo da $d = 0$. Cuando los receptores subtienden ángulos
sólidos desiguales, la fórmula (6) pondera por área cada energía con $N_i$ de la
fórmula (8) —y esos factores de área se evalúan en **radianes**, razón por la que
un espaciado de 5° en el cenit produce un peso cercano a 1,57, no a 51,9.

La animación siguiente ejecuta ese experimento de goniómetro numéricamente: el
mismo frente de onda plano incide sobre un panel rígido plano y sobre un
difusor de Schroeder (un perfil de residuos cuadráticos con N = 7), y la
energía dispersada sobre el arco de receptores convierte un haz especular
colimado (d = 0,32) en un abanico ancho (d = 0,63).

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_diffusion_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_diffusion_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: simulación FDTD 2D de un frente de onda plano incidiendo sobre un panel rígido plano y un difusor de Schroeder de residuos cuadráticos lado a lado; el panel plano devuelve un haz especular colimado mientras que los pozos del difusor reparten la misma energía en un abanico ancho, y el campo dispersado sobre un arco de receptores da coeficientes de difusión de 0,32 frente a 0,63" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_diffusion_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_diffusion_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: simulación FDTD 2D de un frente de onda plano incidiendo sobre un panel rígido plano y un difusor de Schroeder de residuos cuadráticos lado a lado; el panel plano devuelve un haz especular colimado mientras que los pozos del difusor reparten la misma energía en un abanico ancho, y el campo dispersado sobre un arco de receptores da coeficientes de difusión de 0,32 frente a 0,63" style="width:88%"></video>

```python
import phonometry as ph

# Respuesta polar de un difusor (niveles en dB en receptores equiespaciados).
levels = [70.0, 74.0, 68.0, 72.0]
d = ph.directional_diffusion_coefficient(levels)   # fórmula (5)
print(round(float(d), 4))            # 0.7367

# Normaliza frente a una superficie de referencia plana para aislar el efecto del
# difusor (fórmula (7)): d_n = (d - d_ref) / (1 - d_ref).
d_n = ph.normalized_diffusion_coefficient(d, 0.10)
print(round(float(d_n), 4))          # 0.7075

# Valor de incidencia aleatoria: promedia los coeficientes de banda sobre las
# posiciones de fuente, con la ponderación 2-D de la norma (0 grados -> 1,
# +/-30/+/-60 grados -> 3).
from phonometry import TWO_DIMENSIONAL_SOURCE_WEIGHTS
d_random = ph.random_incidence_diffusion(
    [0.5, 0.2, 0.2, 0.2, 0.2], weights=TWO_DIMENSIONAL_SOURCE_WEIGHTS)
print(round(float(d_random), 4))     # 0.2231
```

`directional_diffusion` mantiene los ángulos de los receptores junto a los
niveles de un barrido completo de goniómetro y devuelve un `DiffusionResult`
representable:

```python
import numpy as np
import phonometry as ph

# Un barrido de goniómetro de una superficie difusora: niveles reflejados L_i en
# 37 receptores de -90 a 90 grados (espaciado de 5 grados). La energía se reparte
# casi uniformemente en ángulo, así que el coeficiente d de la fórmula (5) es alto.
angles = np.arange(-90.0, 90.5, 5.0)
rng = np.random.default_rng(3)
levels = 70.0 + 2.0 * np.sin(np.radians(angles) * 3.0) + rng.normal(0.0, 1.0, angles.size)

result = ph.directional_diffusion(angles, levels)
print(round(result.coefficient, 2))   # 0.82
result.plot()   # respuesta polar reflejada, d en el título (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diffusion_polar_es.svg" alt="Un diagrama polar del nivel de presión sonora reflejado de una superficie difusora sobre 37 receptores de -90 a 90 grados, con la respuesta repartida casi uniformemente en ángulo, dando un coeficiente de difusión por autocorrelación d de aproximadamente 0,82" style="width:72%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diffusion_polar_es_dark.svg" alt="Un diagrama polar del nivel de presión sonora reflejado de una superficie difusora sobre 37 receptores de -90 a 90 grados, con la respuesta repartida casi uniformemente en ángulo, dando un coeficiente de difusión por autocorrelación d de aproximadamente 0,82" style="width:72%">

*La energía reflejada llena todo el semicírculo en lugar de concentrarse en un
lóbulo especular, de modo que el coeficiente de difusión por autocorrelación es
alto ($d \approx 0{,}82$). Una superficie plana colapsaría la respuesta en un pico
estrecho y llevaría $d$ hacia cero.*

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# result es el DiffusionResult calculado arriba. En una línea:
result.plot()
plt.show()

# A mano: un diagrama polar de los niveles, con d anotado en el título.
fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
theta = np.radians(result.angles)
ax.plot(theta, result.levels, "o-", color="#1f77b4")
ax.fill(theta, result.levels, color="#1f77b4", alpha=0.15)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_thetamin(-90)
ax.set_thetamax(90)
ax.set_title(f"Difusión direccional  d = {result.coefficient:.2f}  (ISO 17497-2)")
plt.show()
```

</details>

## ¿Dispersión o difusión? Dos coeficientes, dos trabajos

Los dos coeficientes anteriores se tratan de forma rutinaria como
intercambiables, en fichas de producto y a veces en manuales de simulación. No
lo son, y ninguno puede calcularse a partir del otro. El coeficiente de
dispersión $s$ (ISO 17497-1) hace **contabilidad de energía**: qué fracción de
la energía reflejada abandona la dirección especular. No dice nada sobre a
dónde va esa energía. El coeficiente de difusión $d$ (ISO 17497-2) califica la
**calidad espacial**: cuán uniformemente cubre la energía reflejada el arco de
receptores, para una dirección de fuente cada vez. No dice nada sobre cómo se
reparte la energía entre el lóbulo especular y el resto.

Un par de contraejemplos los mantiene separados. Un elemento curvo o inclinado
que *redirige* la reflexión concentra casi toda la energía reflejada en un
lóbulo intenso alejado de la dirección especular: casi todo es no especular,
así que $s$ es alto, pero el haz queda tan colimado como el de un espejo, así
que $d$ se mantiene bajo. A la inversa, un panel plano pequeño medido a baja
frecuencia envía casi toda la energía reflejada hacia la dirección especular,
así que $s$ se queda cerca de cero, y sin embargo la difracción de borde
reparte esa reflexión tan ampliamente sobre el arco de receptores que el $d$
medido sale sorprendentemente alto. Un $s$ alto no significa uniforme; un $d$
decente no significa que se dispersara mucha energía.

**Cuál usar en diseño.** Los dos números sirven a consumidores distintos:

- **El coeficiente de dispersión alimenta la simulación de salas.** Los
  motores de acústica geométrica deciden en cada reflexión de pared cuánta
  energía continúa especularmente y cuánta se redistribuye; el $s$ de
  incidencia aleatoria por banda de cada superficie es precisamente ese
  reparto, que es lo que ISO 17497-1 se redactó para suministrar. Equivocarlo
  se traduce en predicciones erróneas de tiempo de reverberación y claridad
  en salas no mezcladoras.
- **El coeficiente de difusión califica difusores.** Cuando la tarea es
  deshacer un eco, un flutter o una reflexión focalizada, lo que importa es
  que la energía reflejada se reparta en ángulo, y $d$ mide exactamente eso.
  El $d_n$ normalizado (fórmula (7)) resta además la difracción de borde que
  exhibe todo panel finito, de modo que productos de tamaños distintos puedan
  compararse con justicia.

Intercambiarlos falla en ambos sentidos: un coeficiente de difusión metido en
la casilla de dispersión de un simulador sesga el reparto de energía, y un
coeficiente de dispersión citado como prueba de "difusión" puede describir una
superficie que simplemente redirige la reflexión problemática a otro sitio.
Ambos coeficientes son funciones por banda de tercio de octava que en general
crecen cuando el relieve de la superficie deja de ser pequeño frente a la
longitud de onda; un número único ciego a la frecuencia ("dispersa el 90 % del
sonido") no es ninguno de los dos.

## 3. Absorción in situ de pavimentos — técnica de sustracción (ISO 13472-1)

En campo no hay sala reverberante. ISO 13472-1 mide la absorción sonora de un
pavimento (o de cualquier superficie plana extensa) *in situ* disparando un
impulso desde un altavoz a la altura $d_s$ hacia la superficie y registrando la
respuesta al impulso en un micrófono a la altura $d_m$. Las componentes
**incidente** y **reflejada** se separan en el tiempo con una ventana de
Adrienne; su función de transferencia da el factor de reflexión y de ahí la
absorción.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insitu_subtraction_es.svg" alt="Absorción in situ de pavimentos por la técnica de sustracción de ISO 13472-1: un altavoz a 1,25 m y un micrófono a 0,25 m sobre la superficie del pavimento, con los trayectos de rayo directo y reflejado por el pavimento y una medición de referencia en campo libre, con la componente reflejada aislada por una ventana temporal de Adrienne" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insitu_subtraction_es_dark.svg" alt="Absorción in situ de pavimentos por la técnica de sustracción de ISO 13472-1: un altavoz a 1,25 m y un micrófono a 0,25 m sobre la superficie del pavimento, con los trayectos de rayo directo y reflejado por el pavimento y una medición de referencia en campo libre, con la componente reflejada aislada por una ventana temporal de Adrienne" style="width:92%">

**Divergencia geométrica (cláusula 4.1).** La onda reflejada recorre más camino
que la directa, así que se atenúa por el factor de divergencia geométrica

$$
K_r = \frac{d_s - d_m}{d_s + d_m},
$$

que vale $2/3$ para la geometría obligatoria $d_s = 1{,}25$ m, $d_m = 0{,}25$ m. La
absorción se obtiene de los espectros incidente y reflejado enventanados $H_i$,
$H_r$:

$$
\alpha(f) = 1 - \frac{1}{K_r^2}\left|\frac{H_r(f)}{H_i(f)}\right|^2.
$$

```python
import numpy as np
import phonometry as ph

# Una respuesta al impulso incidente limitada en banda y una reflexión de
# pavimento sintética hr = Kr * r0 * delayed(hi): una reflexión de magnitud
# r0 = 0.4, retardada por el camino adicional y escalada por el factor de
# divergencia geométrica Kr.
fs, n = 48000.0, 4096
t = np.arange(n) / fs
hi = np.zeros(n)
hi[:64] = np.hanning(64) * np.cos(2.0 * np.pi * 1500.0 * t[:64])

kr = ph.geometric_spreading_factor()          # (ds - dm)/(ds + dm) = 2/3
hr = kr * 0.4 * np.roll(hi, 96)

# Absorción de banda estrecha, luego reducida a tercios de octava en 250-4000 Hz.
alpha = ph.insitu_absorption_coefficient(hi, hr)   # 1 - (1/Kr^2)|Hr/Hi|^2
freq = np.fft.rfftfreq(n, 1.0 / fs)
centres, band = ph.one_third_octave_absorption(freq, alpha)
print(round(kr, 4))                # 0.6667
print(round(float(band[2]), 3))    # 0.84  (alpha = 1 - 0.4^2 = 0.84)
```

**Ventana de Adrienne (cláusula 6.4).** La ventana temporal que aísla la
reflexión solo exige un flanco de subida abrupto, una porción plana de 5 ms y un
flanco de bajada de coseno cuadrado o Blackman-Harris —las duraciones exactas se
informan en cada medición, no son fijas, así que aquí son configurables.

```python
from phonometry import adrienne_window

# Por defecto: flanco de subida de 0.5 ms, meseta de 5 ms, bajada Blackman-Harris de 5 ms.
w = adrienne_window(48000.0)
print(w.shape[0])          # 504 muestras a 48 kHz
print(round(float(w.max()), 3))   # 1.0  (la meseta y los flancos se encuentran en la unidad)
```

**Espectro de principio a fin.** `insitu_absorption_spectrum` ejecuta toda la
cadena —de las respuestas al impulso incidente y reflejada enventanadas a la
absorción de banda estrecha y de ahí a las bandas de tercio de octava— y devuelve
un `InsituAbsorptionResult` representable:

```python
import numpy as np
import phonometry as ph
from scipy.signal import firwin, lfilter

# Una medición sintética pero realista. hi es un impulso incidente unitario; la
# reflexión del pavimento hr = Kr * r0 * roll(hi, shift) usa el factor de
# divergencia geométrica Kr, un r0 levemente dependiente de la frecuencia (un
# suave paso-bajo, de modo que una superficie porosa refleja menos al subir la
# frecuencia) y el retardo del camino reflejado shift = round(2 dm / c * fs).
fs, n = 48000.0, 8192
kr = ph.geometric_spreading_factor()           # (ds - dm)/(ds + dm) = 2/3
hi = np.zeros(n)
hi[0] = 1.0
taps = firwin(41, 1200.0, fs=fs)
taps = taps / taps.sum()
shift = int(round(2.0 * 0.25 / 340.0 * fs))     # retardo del camino reflejado 2 dm / c
hr = kr * 0.85 * np.roll(lfilter(taps, 1.0, hi), shift)

result = ph.insitu_absorption_spectrum(hi, hr, fs)
print(result.frequencies[[0, -1]].astype(int))     # [ 250 4000]
print(np.round(result.absorption[[0, 6, 12]], 2))  # [0.31 0.65 1.  ]
result.plot()   # diagrama de barras alpha(f) en 250-4000 Hz (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insitu_absorption_es.svg" alt="Un espectro de absorción de pavimento in situ en tercios de octava calculado por la vía del factor de reflexión a partir de una reflexión de pavimento sintética, creciendo desde cerca de 0,3 a 250 Hz hasta casi 1,0 por encima de 2 kHz" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insitu_absorption_es_dark.svg" alt="Un espectro de absorción de pavimento in situ en tercios de octava calculado por la vía del factor de reflexión a partir de una reflexión de pavimento sintética, creciendo desde cerca de 0,3 a 250 Hz hasta casi 1,0 por encima de 2 kHz" style="width:88%">

*La absorción crece con la frecuencia porque la superficie refleja menos energía
de alta frecuencia, exactamente como dicta el factor de reflexión paso-bajo
$r_0(f)$ a través de $\alpha = 1 - (1/K_r^2)\,|H_r/H_i|^2$.*

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# result es el InsituAbsorptionResult calculado arriba. En una línea:
result.plot()
plt.show()

# A mano: un diagrama de barras de alpha sobre las bandas de tercio de octava.
freqs = result.frequencies
positions = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(positions, np.nan_to_num(result.absorption), width=0.7, color="#1f77b4")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Coeficiente de absorción alpha")
ax.set_ylim(0.0, 1.0)
ax.set_title("Absorción in situ de pavimentos (ISO 13472-1)")
plt.show()
```

</details>

**Área máxima muestreada (Anexo A).** La ventana temporal finita limita cuánta
superficie contribuye a la reflexión. El área máxima muestreada es un círculo
cuyo radio la librería calcula a partir de la geometría y la anchura de la
ventana; el ejemplo trabajado del Anexo A ($d_s = 1{,}25$ m, $d_m = 0{,}25$ m,
$c = 340$ m/s, ventana plana de 5 ms) da unos 1,34 m.

```python
import phonometry as ph
print(round(ph.max_sampled_area_radius(5.0e-3), 3))   # 1.343  (metros)
```

## 4. Absorción in situ de pavimentos — método puntual (ISO 13472-2)

Para parches más pequeños, ISO 13472-2 sella un tubo circular corto sobre la
superficie y mide la absorción con el método de la función de transferencia de
dos micrófonos de ISO 10534-2. La librería aporta la geometría del método puntual
y los ayudantes de validez; el propio DSP de la función de transferencia es la
rutina de tubo de impedancia `two_microphone_impedance` (véase la
[guía de Materiales acústicos](/phonometry/es/guides/materials/)).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_spot_tube_es.svg" alt="Método puntual de ISO 13472-2: un tubo circular corto sellado sobre la superficie del pavimento con un altavoz en la parte superior y dos micrófonos enrasados en la pared del tubo con espaciado s, midiendo la absorción de 250 a 1600 Hz mediante el método de la función de transferencia de dos micrófonos de ISO 10534-2" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_spot_tube_es_dark.svg" alt="Método puntual de ISO 13472-2: un tubo circular corto sellado sobre la superficie del pavimento con un altavoz en la parte superior y dos micrófonos enrasados en la pared del tubo con espaciado s, midiendo la absorción de 250 a 1600 Hz mediante el método de la función de transferencia de dos micrófonos de ISO 10534-2" style="width:92%">

**Límites de onda plana (cláusula 5.4).** El tubo solo soporta ondas planas por
debajo de

$$
f_u = 0{,}58\,\frac{c_0}{d},
$$

con $d$ el diámetro del tubo, y el espaciado de micrófonos $s$ debe situarse entre
$0{,}05\,c_0/f_{min}$ y $0{,}45\,c_0/f_{max}$. El rango informado son las bandas de
tercio de octava de 250 a 1600 Hz.

```python
import phonometry as ph

# Frecuencia superior utilizable de un tubo de 100 mm y la ventana de espaciado válida.
print(round(ph.spot_tube_upper_frequency(0.100, 343.0), 1))      # 1989.4 Hz
s_min, s_max = ph.spot_microphone_spacing_bounds(
    343.0, f_min=220.0, f_max=1800.0)
print(round(s_min, 3), round(s_max, 3))    # 0.078 0.086  (metros)
```

## Referencias

- Cox, T. J., & D'Antonio, P. (2017). *Acoustic absorbers and diffusers:
  Theory, design and application* (3.ª ed.). CRC Press.
  ISBN 978-1-4987-4099-9.
  [doi:10.1201/9781315369211](https://doi.org/10.1201/9781315369211).
  La monografía de referencia sobre teoría y diseño de difusores, de los
  autores tras el método del coeficiente de difusión de ISO 17497-2: la
  distinción dispersión-difusión, los montajes de
  medida y la guía de diseño que esta página condensa.
- International Organization for Standardization. (2004). *Acoustics —
  Sound-scattering properties of surfaces — Part 1: Measurement of the
  random-incidence scattering coefficient in a reverberation room*
  (ISO 17497-1:2004).
  [Catálogo iso.org](https://www.iso.org/standard/31397.html).
  El método de mesa giratoria de la sección 1 y los límites de placa base de
  la Tabla 1.
- International Organization for Standardization. (2012). *Acoustics —
  Sound-scattering properties of surfaces — Part 2: Measurement of the
  directional diffusion coefficient in a free field* (ISO 17497-2:2012).
  [Catálogo iso.org](https://www.iso.org/standard/55293.html).
  El coeficiente de autocorrelación del goniómetro de la sección 2, su
  ponderación por área y el $d_n$ normalizado.

---

**Normas.** ISO 17497-1:2004 (coeficiente de
dispersión), ISO 17497-2:2012 (coeficiente de difusión), ISO 13472-1:2002
(absorción in situ, superficie extensa), ISO 13472-2:2010 (absorción in situ,
método puntual), e ISO 9613-1:1993 — solo el coeficiente de atenuación de
tono puro α que consumen las relaciones de atenuación del aire del apartado 8 de
ISO 17497-1 (Ecs. (2)/(3)); el modelo completo de absorción atmosférica se
cubre en [Propagación en exteriores](/phonometry/es/guides/outdoor-propagation/).

## Véase también

- Referencia de la API: [`materials.scattering_diffusion`](/phonometry/es/reference/api/materials/scattering-diffusion/) y [`materials.road_absorption`](/phonometry/es/reference/api/materials/road-absorption/).
