---
title: "Potencia sonora"
description: "Nivel de potencia sonora LW por cinco vías: presión sonora sobre superficie envolvente (ISO 3744/3746), el método de precisión en sala reverberante con las correcciones de Waterhouse y C1/C2 (ISO 3741), el barrido de intensidad con indicadores de campo y grado alcanzado (ISO 9614-2), el método de precisión en sala anecoica (ISO 3745) y el barrido de intensidad de precisión (ISO 9614-3)."
---

La presión *sonora* depende de dónde te sitúes y de la sala en la que estés;
la **potencia** sonora no. El nivel de potencia sonora `LW` es la energía
acústica total por segundo que radia una fuente, referida a `P0 = 1 pW`, y es
el descriptor de **emisión** independiente del dispositivo que figura en una
ficha técnica, alimenta una predicción de sala (EN 12354) o se contrasta con
un límite de emisión de ruido. Esta página cubre las vías que phonometry
implementa para obtenerlo y cuándo recurrir a cada una: una superficie
envolvente de *presión* en campo (ISO 3744/3746), el campo difuso de una
*sala reverberante* (ISO 3741), el *barrido* de intensidad sobre una
superficie (ISO 9614-2) y —para la máxima exactitud— los grados de precisión
en una *sala anecoica* (ISO 3745) y mediante el *barrido* de intensidad de
precisión (ISO 9614-3).

## Elegir un método

Todas proporcionan la misma magnitud —un `LW` por banda y un total
ponderado A `LWA`— pero bajo entornos, grados de precisión y restricciones
prácticas distintos.

| Método | Norma | Magnitud medida | Entorno | Grado de precisión | Cuándo usarlo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Superficie envolvente | **ISO 3744** (ingeniería) / **ISO 3746** (inspección) | Presión sonora sobre una semiesfera o caja | Campo esencialmente libre sobre uno o varios planos reflectantes | Grado 2 (`σR0 ≈ 1.5 dB`) / grado 3 (`≈ 3.0 dB`) | In situ o en una sala grande; sin instalación de ensayo especial disponible |
| Sala reverberante | **ISO 3741** | Presión sonora en el campo difuso | Sala reverberante cualificada de paredes rígidas | Grado 1 (precisión) | Máxima precisión para fuentes estacionarias de banda ancha en laboratorio |
| Barrido de intensidad | **ISO 9614-2** | Intensidad sonora normal barrida sobre una superficie | Casi cualquiera, tolerante al ruido extraño estacionario | Grado 2 / 3 (a partir de los indicadores de campo por banda) | In situ con ruido de fondo, o una máquina entre muchas |
| Sala anecoica | **ISO 3745** | Presión sonora sobre un conjunto fijo de micrófonos | Sala anecoica o semianecoica cualificada | Grado 1 (precisión) | Emisión de grado de referencia en un laboratorio de campo libre |
| Barrido de intensidad de precisión | **ISO 9614-3** | Intensidad normal barrida, con criterios más estrictos | Casi cualquiera, tolerante al ruido extraño estacionario | Grado 1 (precisión) | Precisión in situ, con las comprobaciones de indicadores de campo de ISO 9614-3 |

Los métodos de presión corrigen el nivel superficial por la sala (`K2`) y por
el ruido de fondo (`K1`); el método en sala reverberante necesita una sala
*cualificada* pero alcanza el grado de precisión; la intensidad rechaza la
energía de fondo estacionaria a costa de una sonda de dos micrófonos y una
comprobación de validez por banda. El resto de la página recorre cada uno por
turno.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_methods_es.svg" alt="Las tres vías de potencia sonora en paralelo: una superficie envolvente de presión sobre un plano reflectante (ISO 3744/3746), una fuente en una sala reverberante muestreada por micrófonos (ISO 3741) y una sonda de intensidad barriendo una superficie alrededor de la fuente (ISO 9614-2)" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_methods_es_dark.svg" alt="Las tres vías de potencia sonora en paralelo: una superficie envolvente de presión sobre un plano reflectante (ISO 3744/3746), una fuente en una sala reverberante muestreada por micrófonos (ISO 3741) y una sonda de intensidad barriendo una superficie alrededor de la fuente (ISO 9614-2)" style="width:92%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import emission

# Una fuente estacionaria (LW por bandas de octava abajo) por tres vías.
freqs = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
lw_true = np.array([85.0, 88.0, 90.0, 89.0, 86.0, 82.0])

# ISO 3744: SPL en 10 posiciones de una semiesfera, r = 2 m (10 lg(S/S0) = 14 dB).
pres = emission.sound_power_pressure(np.tile(lw_true - 14.0, (10, 1)),
                                     "hemisphere", radius=2.0,
                                     frequencies=freqs)
# ISO 9614-2: intensidad normal uniforme barrida sobre seis segmentos de 0.5 m2.
i_n = np.tile(10.0 ** (lw_true / 10.0) * 1e-12 / 3.0, (6, 1))
inten = emission.sound_power_intensity(i_n, np.full(6, 0.5),
                                       frequencies=freqs, band_type="octave")
# ISO 3741: comparación con una fuente de referencia de LW = 84 dB conocido por banda.
comp = emission.sound_power_comparison(lw_true - 20.0, np.full(6, 64.0),
                                       np.full(6, 84.0), frequencies=freqs)

fig, ax = plt.subplots()
for res, style, ms, label in ((pres, "-o", 11, "presión (ISO 3744)"),
                              (inten, "--s", 8, "intensidad (ISO 9614-2)"),
                              (comp, ":^", 5, "fuente de referencia (ISO 3741)")):
    ax.semilogx(freqs, res.sound_power_level, style, markersize=ms,
                label=f"{label}: LWA = {res.sound_power_level_a:.1f} dB")
ax.set(xlabel="Frecuencia [Hz]", ylabel="Nivel de potencia sonora LW [dB]")
ax.legend()
plt.show()
```

</details>

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_power_two_rooms_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_power_two_rooms_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: la misma fuente en una cámara anecoica y en una cámara reverberante produce presiones de micrófono distintas, y las fórmulas de campo libre y campo difuso convergen al mismo nivel de potencia sonora L_W" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_power_two_rooms_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_power_two_rooms_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: la misma fuente en una cámara anecoica y en una cámara reverberante produce presiones de micrófono distintas, y las fórmulas de campo libre y campo difuso convergen al mismo nivel de potencia sonora L_W" style="width:88%"></video>

### Una ruta de decisión

La tabla se condensa en una breve secuencia de preguntas (ISO 3740 dedica su
Tabla 3 y su Anexo D exactamente a esta decisión). Recórrelas en orden; la
primera coincidencia nombra la norma.

1. **¿Para qué es el número?** Una declaración de ficha técnica o una
   comprobación frente a un límite piden normalmente grado de ingeniería
   (grado 2, el grado preferido para las declaraciones de ruido); una fuente
   de referencia, una clasificación de productos o un litigio piden precisión
   (grado 1); un primer reconocimiento de una nave ruidosa tolera el grado de
   inspección (grado 3). El grado 1 solo existe en una sala de laboratorio
   cualificada (ISO 3741, ISO 3745) o mediante los métodos de intensidad de
   precisión (ISO 9614-1 en puntos discretos, ISO 9614-3 por barrido).
2. **¿Puede la fuente viajar al laboratorio?** ISO 3741 quiere la fuente
   pequeña frente a la sala (volumen no mayor de aproximadamente el 2 % del
   volumen de la sala) y su ruido estacionario; ISO 3745 la quiere dentro de
   una sala anecoica o semianecoica cualificada con una dimensión
   característica menor que la mitad del radio de medición, y es la vía que
   además proporciona la directividad. Una máquina anclada a su bancada
   descarta ambas y deja los métodos in situ.
3. **¿Cómo de silencioso y de seco es el emplazamiento?** ISO 3744 necesita
   el fondo al menos 6 dB por debajo de la fuente (preferiblemente más de
   15 dB) y `K2 ≤ 4 dB`. Si solo se alcanza un margen de 3 dB o `K2 ≤ 7 dB`, los
   mismos micrófonos y fórmulas pasan sin más a ISO 3746 en grado de
   inspección.
4. **¿Es el fondo el problema?** Cuando las máquinas vecinas no se pueden
   apagar, o el margen es directamente negativo, los métodos de presión
   quedan descartados. El barrido de intensidad (ISO 9614-2, o ISO 9614-3
   para el grado 1) tolera ruido extraño estacionario incluso unos 10 dB
   *por encima* de la fuente, porque solo cuenta el flujo neto de energía a
   través de la superficie; los indicadores de campo por banda deciden
   después el grado realmente alcanzado.

### Qué significan los grados de precisión

El grado es una afirmación sobre la **reproducibilidad**: `σR0` es la
desviación típica que verías si laboratorios distintos midieran la misma
fuente, cada uno siguiendo la norma correctamente. Los valores ponderados A
típicos son `σR0 ≈ 0.5 dB` para el grado 1 (ISO 3741), `1.5 dB` para el
grado 2 (ISO 3744, ISO 9614-2) y `3 dB` o más para el grado 3 (aún mayores
cuando `K2` es grande o el espectro es tonal). Los valores
por banda son mayores en los extremos del espectro. El campo `uncertainty`
de los resultados de los métodos de presión (superficie envolvente y sala
anecoica) es la incertidumbre expandida `U = 2·σtot` (95 % de
cobertura), donde `σtot = √(σR0² + σomc²)` incorpora además la inestabilidad
de operación/montaje `σomc` que tú estimas y pasas; el grado solo acota la
parte del presupuesto que corresponde al método.

En la práctica: un `LWA` de grado 2 de 92,4 dB lleva `U ≈ 3 dB`, así que dos
resultados de grado 2 separados 2 dB son estadísticamente indistinguibles, y
contrastar esa misma fuente con un límite de 93 dB es cara o cruz. Elige el
grado por la decisión que el número debe sostener, no por la instalación que
esté libre.

## 1. Superficie envolvente, presión sonora (ISO 3744 / ISO 3746)

Coloca la fuente sobre un plano reflectante e imagina una **superficie de
medición** de área `S` que la envuelve: una semiesfera para una fuente
compacta, una caja (paralelepípedo recto) para una grande o alargada.
Muestrea el nivel de presión sonora en un conjunto de posiciones de micrófono
sobre esa superficie, promédialas en energía, y la potencia sonora se obtiene
porque una superficie suficientemente difusa capta toda la energía radiada:

$$
\bar{L}_p = 10 \log_{10}\left( \frac{1}{N_M} \sum_i 10^{L_{pi}/10} \right), \qquad
L_W = \bar{L}_p - K_1 - K_2 + 10 \log_{10}\frac{S}{S_0},\quad S_0 = 1\ \text{m}^2 .
$$

Dos correcciones depuran el nivel superficial. La **corrección por ruido de
fondo** elimina la energía que habría estado presente con la fuente apagada, a
partir del margen `ΔLp` entre los niveles con la fuente encendida y los de
fondo,

$$
K_1 = -10 \log_{10}\left( 1 - 10^{-\Delta L_p/10} \right),
$$

y la **corrección ambiental** elimina la acumulación reverberante de la sala
de ensayo a partir de su área de absorción sonora equivalente `A`,

$$
K_2 = 10 \log_{10}\left( 1 + \frac{4 S}{A} \right).
$$

El área de la superficie es una forma cerrada de la geometría: una semiesfera
es `S = 2πr²` sobre un plano reflectante (dividida entre dos y entre cuatro
para dos y tres planos), y una caja de un plano es `S = 4(ab + bc + ca)` con
`a = 0.5·l1 + d`, `b = 0.5·l2 + d`, `c = l3 + d` para la distancia de medición
`d`. ISO 3746 (inspección) comparte todas las fórmulas pero es más burda: menos
posiciones de micrófono, un criterio de fondo de 3 dB en lugar de 6 dB, y
validez hasta `K2 ≤ 7 dB` en lugar de 4 dB.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sound_power_surfaces_es.svg" alt="Superficies de medición de ISO 3744: una semiesfera de radio r envolviendo una fuente compacta sobre un plano reflectante, y un paralelepípedo recto (caja) a la distancia de medición d alrededor de una fuente grande, ambas con las posiciones de micrófono marcadas" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sound_power_surfaces_es_dark.svg" alt="Superficies de medición de ISO 3744: una semiesfera de radio r envolviendo una fuente compacta sobre un plano reflectante, y un paralelepípedo recto (caja) a la distancia de medición d alrededor de una fuente grande, ambas con las posiciones de micrófono marcadas" style="width:88%">

```python
import numpy as np
from phonometry import sound_power_pressure, measurement_positions

# SPL en banda de octava (dB) en las 10 posiciones de la semiesfera de ISO 3744
# (Anexo B), con la fuente en marcha, más el espectro de fondo con ella apagada.
freqs = np.array([63, 125, 250, 500, 1000, 2000, 4000, 8000])
base = np.array([70.0, 74.0, 78.0, 80.0, 79.0, 76.0, 72.0, 66.0])
rng = np.random.default_rng(0)
levels = base + rng.normal(0.0, 0.5, size=(10, 8))     # (posiciones, bandas)
background = np.full((10, 8), 55.0)

# Coordenadas de micrófono del Anexo B de ISO 3744 en una semiesfera de radio 1.5 m.
mic_xyz = measurement_positions("hemisphere", radius=1.5, reflecting_planes=1)
print(mic_xyz.shape)                                    # (10, 3)

res = sound_power_pressure(
    levels, "hemisphere", radius=1.5, reflecting_planes=1,
    background_levels=background, frequencies=freqs,
    reverberation_time=0.6, volume=300.0,          # datos de sala -> K2
)
print(round(res.surface_area, 2))                       # 14.14 m^2 (= 2*pi*1.5^2)
print(round(float(res.environmental_correction[0]), 2)) # K2 = 2.32 dB
print(round(res.sound_power_level_a, 1))                # LWA = 92.4 dB
print(round(res.uncertainty, 1))                        # U = 3.0 dB (2*sigma_R0)
print(np.round(res.sound_power_level, 1))               # LW por banda

res.plot()   # barras de nivel de potencia sonora por banda; LWA en el título (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_pressure_result_es.svg" alt="El espectro de nivel de potencia sonora por superficie envolvente del ejemplo de semiesfera de ISO 3744, una barra por banda de octava de 63 Hz a 8 kHz con pico cerca de 500 Hz, con el total ponderado A de 92,4 dB(A) en el título" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_pressure_result_es_dark.svg" alt="El espectro de nivel de potencia sonora por superficie envolvente del ejemplo de semiesfera de ISO 3744, una barra por banda de octava de 63 Hz a 8 kHz con pico cerca de 500 Hz, con el total ponderado A de 92,4 dB(A) en el título" style="width:88%">

*Una barra por banda: la presión superficial promediada en energía menos las
correcciones de fondo (`K1`) y ambiental (`K2`) más el término de superficie
`10 lg(S/S0)` dan `LW(f)`, y la suma energética ponderada A entre bandas da el
número único `LWA` del título.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# res es el SoundPowerResult calculado arriba. Una línea:
res.plot()
plt.show()

# A mano: un espectro de barras de LW con el total ponderado A en el título.
freqs = res.frequencies
positions = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(positions, res.sound_power_level, width=0.7, color="#1f77b4")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de potencia sonora LW [dB]")
ax.set_title(
    f"Potencia sonora por superficie envolvente (ISO 3744)  "
    f"LWA = {res.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

El total ponderado A `LWA` se combina a partir de las potencias por banda con
las correcciones de ponderación A del Anexo E de ISO 3744, así que necesita
`frequencies`. Pasar los datos de sala (`reverberation_time` + `volume`,
o `absorption_area`, o `mean_absorption_coefficient` + `room_surface`) habilita
`K2`; omítelos y el campo se trata como libre (`K2 = 0`). Si el margen de fondo
cae por debajo del criterio del grado o `K2` supera el límite de validez, un
`SoundPowerWarning` avisa de que los niveles son cotas superiores —la
determinación se devuelve igualmente.

### Trampas de K1 y K2

Ambas correcciones restan energía al nivel superficial, así que sobreestimar
cualquiera de las dos subestima la emisión. Por eso las normas las acotan, y
por eso la mayoría de las disputas sobre un resultado de superficie
envolvente se remontan a uno de estos hábitos:

- **K1 tiene un precipicio, no una pendiente.** Con 15 dB de margen la
  corrección es de tan solo 0,14 dB (despreciable); en el criterio de
  ingeniería de 6 dB ya es 1,26 dB, el mayor valor que acepta el grado. Por
  debajo del criterio la norma no permite aplicar la fórmula: `K1` se acota
  y el resultado se declara cota superior. Nunca extrapoles la resta a un
  margen menor; aumenta el margen (emplazamiento más silencioso, superficie más cercana) o
  pásate al método de intensidad.
- **K1 supone un fondo estacionario.** La lectura con la fuente apagada debe
  tomarse en las mismas posiciones y con la sala en el mismo estado, y la
  energía de fondo debe ser la misma durante ambas lecturas. Un sistema de
  ventilación que cicla o un vehículo que pasa durante cualquiera de las dos
  invalida la pareja; la resta energética supone además que la fuente y el
  fondo son incoherentes, lo que vale para el ruido ajeno pero no para las
  reflexiones de la propia fuente.
- **K2 elimina la acumulación media de la sala, no las reflexiones
  discretas.** Una pared cercana, un carro u otra máquina justo fuera de la
  superficie añaden una contribución especular concentrada en unos pocos
  micrófonos. Ese desequilibrio aflora en el índice de directividad aparente
  `DIi*`, y ninguna corrección promedio de sala puede eliminarlo: desplaza
  la superficie, retira el reflector o trátalo con absorción.
- **K2 vale lo que valga `A`.** Con `A` de Sabine (`0.16·V/T`), los errores
  en el tiempo de reverberación o en el volumen se propagan directamente. En
  el límite de validez `K2 = 4 dB` cerca del 60 % de la energía medida
  proviene de la sala, no de la fuente, y un error del 20 % en `A` aún
  modifica `LW` en unos 0,5 dB.
  Prefiere un `T60` medido a un coeficiente de absorción estimado, y mantén
  la distancia de medición lo bastante pequeña para que `K2` quede
  holgadamente por debajo del límite.

### Parámetros de `sound_power_pressure()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `levels_positions` | array 2D | dB | `(NM, NB)` | Una fila por posición, una columna por banda (o una única columna ponderada A) |
| `surface` | str | — | `'hemisphere'` / `'box'` | Forma de la superficie de medición |
| `radius` | float | m | > 0 (semiesfera) | Radio de la semiesfera `r` |
| `dimensions` | (float, float, float) | m | > 0 (caja) | `(l1, l2, l3)` del paralelepípedo de referencia |
| `distance` | float | m | > 0 (caja) | Distancia de medición `d` |
| `reflecting_planes` | int | — | `1` / `2` / `3`, por defecto `1` | Divide entre dos/cuatro el área de la semiesfera |
| `background_levels` | array 2D o espectro | dB | `(NM, NB)`, o `(NB,)` / `(1, NB)` | Habilita `K1`; un espectro único se difunde a todas las posiciones |
| `frequencies` | array 1D | Hz | centros de banda nominales | Habilita `LWA` (Anexo E) |
| `absorption_area` | float o array 1D | m² | > 0 | `A` para `K2` (directo); un array por banda → `K2` por banda |
| `reverberation_time`, `volume` | float/array, float | s, m³ | > 0 | `A = 0.16 V/T` para `K2`; `T` por banda → `K2` por banda |
| `mean_absorption_coefficient`, `room_surface` | float/array, float | —, m² | `(0,1]`, > 0 | `A = α·Sv` (Ec. A.7); `α` por banda → `K2` por banda |
| `grade` | str | — | `'engineering'` (por defecto) / `'survey'` | ISO 3744 vs ISO 3746 |
| `omc_uncertainty` | float | dB | por defecto `0.0` | `σomc`, inestabilidad de operación/montaje, incorporada a `U` |

Devuelve un `SoundPowerResult`: `sound_power_level` (`LW` por banda),
`surface_pressure_level` (`Lp` tras K1/K2), `mean_pressure_level`,
`background_correction`/`environmental_correction` (`K1`/`K2`),
`directivity_index` (índice de directividad aparente `DIi*` por posición de
micrófono **y** banda de frecuencia, forma `(NM, NB)`; ISO 3744 cláusula 8.6),
`surface_area`, `sound_power_level_a` (`LWA`), `uncertainty`
(expandida, 95 %) y `grade`. `measurement_positions('hemisphere', radius=…,
reflecting_planes=…, tones=…, grade=…)` devuelve las coordenadas normativas
`(N, 3)` de micrófono (Tabla B.1 para fuentes tonales, B.2 para banda ancha).

## 2. Sala reverberante, grado de precisión (ISO 3741)

En una **sala reverberante** cualificada de paredes rígidas el campo es
difuso, así que un puñado de micrófonos muestrea toda la energía radiada y el
método alcanza el grado 1. La potencia sonora proviene del nivel medio de la
sala `Lp(ST)`, el área de absorción de Sabine `A = (55.26/c)·(V/T60)` y una
cadena de pequeñas correcciones (ISO 3741 Ec. 20):

$$
L_W = \bar{L}_p + 10 \log_{10}\frac{A}{A_0} + 4{,}34\ \frac{A}{S}
      + 10 \log_{10}\left( 1 + \frac{S c}{8 V f} \right) + C_1 + C_2 - 6 .
$$

El término entre paréntesis es la **corrección de Waterhouse**: cerca de los
contornos de la sala la densidad de energía sonora es mayor que en el interior,
y este término (que se anula al crecer la frecuencia) restituye la energía que
los micrófonos del interior no captan. `C1` (cantidad de referencia) y `C2`
(impedancia de radiación) llevan el resultado a las condiciones meteorológicas
de referencia de 23 °C y 101,325 kPa,

$$
C_1 = -10 \log_{10}\frac{p_s}{p_{s0}} + 5 \log_{10}\frac{273{,}15 + \theta}{314}, \qquad
C_2 = -10 \log_{10}\frac{p_s}{p_{s0}} + 15 \log_{10}\frac{273{,}15 + \theta}{296},
$$

con la velocidad del sonido `c = 20.05·√(273 + θ)`. El **método de comparación**
sustituye los términos de área de absorción, Waterhouse y `C1` por una fuente
sonora de referencia de potencia conocida `LW(RSS)` medida en la misma sala, de
modo que la sala no necesita caracterizarse:
`LW = LW(RSS) + (Lp(ST) − Lp(RSS) + C2)`.

```python
import numpy as np
from phonometry import sound_power_reverberation, sound_power_comparison

# SPL medio de sala en tercios de octava (dB), 100 Hz - 10 kHz, y el T60 de la sala.
freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000,
                  1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000],
                 dtype=float)
lp = np.linspace(80.0, 70.0, freqs.size)
t60 = np.full(freqs.size, 2.0)

rev = sound_power_reverberation(
    lp, t60, volume=200.0, surface_area=220.0, frequencies=freqs,
    temperature=20.0, static_pressure=101.0,
)
print(round(rev.speed_of_sound, 1))                     # c = 343.2 m/s
print(round(float(rev.absorption_area[0]), 1))          # A = 16.1 m^2 a 100 Hz
print(round(float(rev.waterhouse_correction[0]), 2))    # 1.68 dB a 100 Hz
print(round(float(rev.sound_power_level[0]), 1))        # LW = 87.9 dB
print(round(rev.sound_power_level_a, 1))                # LWA = 92.1 dB

# Método de comparación: una fuente de referencia de LW conocido medida en los mismos puntos.
lw_rss = np.full(freqs.size, 85.0)
lp_rss = np.linspace(78.0, 69.0, freqs.size)
cmp = sound_power_comparison(lp, lp_rss, lw_rss, frequencies=freqs, temperature=20.0)
print(round(float(cmp.sound_power_level[0]), 1), cmp.method)   # 86.9 comparison

rev.plot()   # espectro LW de la sala reverberante; LWA en el título (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_reverberation_result_es.svg" alt="El espectro de nivel de potencia sonora en cámara reverberante del ejemplo de ISO 3741, una barra por banda de tercio de octava de 100 Hz a 10 kHz descendiendo suavemente con la frecuencia, con el total ponderado A de 92,1 dB(A) en el título" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_reverberation_result_es_dark.svg" alt="El espectro de nivel de potencia sonora en cámara reverberante del ejemplo de ISO 3741, una barra por banda de tercio de octava de 100 Hz a 10 kHz descendiendo suavemente con la frecuencia, con el total ponderado A de 92,1 dB(A) en el título" style="width:88%">

*El nivel medio de la sala llevado a través de los términos de área de
absorción, de Waterhouse y meteorológicos de la Ec. 20 da el `LW(f)` por tercio
de octava, y la suma energética ponderada A entre las 21 bandas da el `LWA` del
título.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# rev es el ReverberationSoundPowerResult calculado arriba. Una línea:
rev.plot()
plt.show()

# A mano: un espectro de barras de LW con el total ponderado A en el título.
freqs = rev.frequencies
positions = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(positions, rev.sound_power_level, width=0.7, color="#1f77b4")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de potencia sonora LW [dB]")
ax.set_title(
    f"Potencia sonora en cámara reverberante (ISO 3741)  "
    f"LWA = {rev.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

`levels` puede ser un espectro medio 1D o un array 2D `(NM, NB)` promediado
sobre las posiciones. Cuando el volumen de la sala, su tiempo de reverberación
o el número de micrófonos incumplen un criterio de cualificación de ISO 3741
(volumen mínimo de la Tabla 1, el suelo de reverberación `V/S`, menos de 6
posiciones, o una dispersión entre posiciones superior a 1,5 dB), se emite un
`SoundPowerWarning` de aviso y el resultado se devuelve igualmente.

### Parámetros de `sound_power_reverberation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `levels` | array 1D o 2D | dB | por banda, o `(NM, NB)` | SPL medio de sala; 2D se promedia en energía sobre las posiciones |
| `t60` | float o array 1D | s | > 0 | Tiempo de reverberación de la sala (el escalar se difunde) |
| `volume` | float | m³ | > 0 | Volumen de la sala `V` |
| `surface_area` | float | m² | > 0 | Superficie total de la sala `S` (Waterhouse, `A/S`) |
| `frequencies` | array 1D | Hz | uno por banda | Obligatorio (Waterhouse necesita `f`); habilita `LWA` |
| `background_levels` | array 1D o 2D | dB | coincide con `levels` | `K1` por banda (criterio dependiente de la frecuencia) |
| `temperature` | float | °C | por defecto `23.0` | Fija `c`, `C1`, `C2` |
| `static_pressure` | float | kPa | por defecto `101.325` | Fija `C1`, `C2` |

`sound_power_comparison(levels, levels_ref, lw_ref, *, frequencies=None,
background_levels=…, background_levels_ref=…, temperature=23.0,
static_pressure=101.325)` toma los mismos niveles de sala más los niveles de la
fuente de referencia y su potencia conocida.

| Parámetro | Tipo | Unidades | Rango / defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `levels_ref` | array 1D o 2D | dB | coincide con `levels` | SPL medio de sala con la fuente de referencia (RSS) en marcha |
| `lw_ref` | array 1D | dB | por banda | Potencia sonora conocida `LW(RSS)` de la fuente de referencia |
| `background_levels` | array 1D o 2D | dB | coincide con `levels` | Ruido de fondo de la fuente de ensayo; `K1` por banda sobre `Lp(ST)` |
| `background_levels_ref` | array 1D o 2D | dB | coincide con `levels_ref` | Ruido de fondo de la fuente de **referencia**; `K1` por banda sobre `Lp(RSS)` |

`background_levels_ref` corrige por ruido de fondo el nivel de sala de la fuente
de referencia `Lp(RSS)` igual que `background_levels` lo hace para la fuente de
ensayo; ambos requieren `frequencies` (el criterio ISO 3741 depende de la
frecuencia). Ambas devuelven un
`ReverberationSoundPowerResult` (`sound_power_level`, `mean_pressure_level`,
`absorption_area`, `waterhouse_correction`, `background_correction`, `c1`, `c2`,
`speed_of_sound`, `sound_power_level_a`, `method`; los campos de
absorción/Waterhouse/`c1` son `NaN` para el método de comparación).

## 3. Barrido de intensidad (ISO 9614-2)

La **intensidad** sonora es el flujo neto de energía, así que distingue la
energía que *sale* de la fuente de la energía estacionaria que solo atraviesa
la superficie —por eso el método de intensidad tolera el ruido de fondo que
derrotaría a los métodos de presión. Una sonda p-p (véase la
[guía de Intensidad sonora](/phonometry/es/guides/intensity/)) se barre de forma
continua sobre cada uno de los `N` segmentos de una superficie que encierra la
fuente, informando de la intensidad normal con signo promediada por segmento
`<In,i>`. Las potencias parciales suman el total:

$$
P_i = \langle I_{n,i} \rangle\ S_i, \qquad P = \sum_i P_i, \qquad
L_W = 10 \log_{10}\frac{P}{P_0},\quad P_0 = 1\ \text{pW} .
$$

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: una sonda p-p recorre el barrido en serpentina sobre la cara superior de la caja de medición mientras aparecen detrás las flechas de intensidad normal, y las potencias parciales de las cinco caras se acumulan en el nivel de potencia sonora L_W" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: una sonda p-p recorre el barrido en serpentina sobre la cara superior de la caja de medición mientras aparecen detrás las flechas de intensidad normal, y las potencias parciales de las cinco caras se acumulan en el nivel de potencia sonora L_W" style="width:88%"></video>

Una banda en la que `P < 0` (flujo neto entrante, de una fuente más fuerte
fuera de la superficie) es **no determinable** y se informa como `NaN`. Dos
indicadores de campo normativos cualifican cada banda. El **indicador
superficial presión-intensidad** `FpI` mide cuán reactivo es el campo, y el
**indicador de potencia parcial negativa** `F+/-` mide cuánta energía circula
hacia dentro y hacia fuera:

$$
F_{pI} = [L_p] - L_W + 10 \log_{10}\frac{S}{S_0}, \qquad
F_{+/-} = 10 \log_{10}\frac{\sum_i \lvert P_i \rvert}{\lvert \sum_i P_i \rvert} .
$$

La **capacidad dinámica** de la sonda `Ld = δpI0 − K` (índice de intensidad
residual de presión menos el factor de sesgo `K`, 10 dB para el grado 2 y 7 dB
para el grado 3) debe superar `FpI` (criterio 1); `F+/- ≤ 3 dB` es el criterio
2 (obligatorio para el grado 2); y los dos barridos repetidos deben coincidir
dentro del límite `s` de la Tabla 2 por segmento (criterio 3). Una banda es de
grado **ingeniería** cuando se cumplen los criterios 1, 2 y 3, de **inspección**
cuando se cumplen 1 y 3, y en caso contrario `none`.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_es.svg" alt="Una sonda de intensidad sonora p-p de dos micrófonos: dos micrófonos de presión separados por un separador, a partir de los cuales se estima el gradiente de presión y, por tanto, la intensidad normal" style="width:70%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_es_dark.svg" alt="Una sonda de intensidad sonora p-p de dos micrófonos: dos micrófonos de presión separados por un separador, a partir de los cuales se estima el gradiente de presión y, por tanto, la intensidad normal" style="width:70%">

```python
import numpy as np
from phonometry import sound_power_intensity

# 6 segmentos de superficie x 6 bandas de octava: intensidad normal con signo (W/m^2)
# de dos barridos repetidos, las áreas de los segmentos y el SPL superficial por segmento (dB).
freqs = np.array([125, 250, 500, 1000, 2000, 4000], dtype=float)
areas = np.full(6, 0.5)                                 # 0.5 m^2 por segmento
rng = np.random.default_rng(0)
scan1 = np.abs(rng.normal(1e-4, 2e-5, size=(6, 6)))     # (segmentos, bandas)
scan2 = scan1 * (1.0 + rng.normal(0.0, 0.02, size=(6, 6)))
pressure = np.full((6, 6), 80.0)

res = sound_power_intensity(
    scan1, areas, normal_intensity_2=scan2, pressure_levels=pressure,
    pressure_residual_index=12.0, frequencies=freqs,
    band_type="octave", grade="engineering",
)
print(np.round(res.sound_power_level, 1))               # LW por banda
print(round(res.sound_power_level_a, 1))                # LWA sobre las bandas determinables
print(round(float(res.dynamic_capability_index[0]), 1)) # Ld = 12 - 10 = 2.0 dB
print(round(float(res.surface_pressure_intensity_index[0]), 2))   # FpI
print(list(res.achieved_grade))                         # grado por banda

res.plot()   # espectro LW; bandas no positivas (indeterminables) con trama (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_intensity_result_es.svg" alt="El espectro de nivel de potencia sonora por barrido de intensidad del ejemplo de ISO 9614-2, una barra por banda de octava de 125 Hz a 4 kHz todas cerca de 85 dB, con el total ponderado A de 90,9 dB(A) en el título" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_intensity_result_es_dark.svg" alt="El espectro de nivel de potencia sonora por barrido de intensidad del ejemplo de ISO 9614-2, una barra por banda de octava de 125 Hz a 4 kHz todas cerca de 85 dB, con el total ponderado A de 90,9 dB(A) en el título" style="width:88%">

*Las potencias parciales `<In,i>·Si` de los seis segmentos suman el `LW` de
cada banda; aquí todas las bandas tienen potencia neta positiva y superan los
criterios de indicadores de campo en grado de ingeniería, así que las seis
barras se sostienen, y el total ponderado A de 90,9 dB(A) encabeza el título.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# res es el SoundPowerIntensityResult calculado arriba. Una línea:
res.plot()
plt.show()

# A mano: un espectro de barras de LW con el total ponderado A en el título.
freqs = res.frequencies
positions = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(positions, res.sound_power_level, width=0.7, color="#1f77b4")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de potencia sonora LW [dB]")
ax.set_title(
    f"Potencia sonora por barrido de intensidad (ISO 9614-2)  "
    f"LWA = {res.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

Suministrar `normal_intensity_2` (el segundo barrido) promedia ambos para las
potencias parciales y evalúa el criterio 3; `pressure_levels` habilita `FpI`;
`pressure_residual_index` (`δpI0`) más un segundo barrido habilita el grado
alcanzado por banda. La intensidad por diferencias finitas de la sonda tiene un
sesgo dependiente de la frecuencia que se trata en la
[guía de intensidad](/phonometry/es/guides/intensity/).

### Parámetros de `sound_power_intensity()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `normal_intensity` | array 2D | W/m² | `(N_seg, N_bands)` | Intensidad normal con signo promediada por segmento `<In,i>` (primer barrido) |
| `areas` | array 1D | m² | > 0, `(N_seg,)` | Áreas de los segmentos `Si` |
| `normal_intensity_2` | array 2D | W/m² | misma forma | Segundo barrido → criterio 3 y promediado |
| `pressure_levels` | array 2D | dB | misma forma | SPL por segmento `Lpi` → `FpI` |
| `pressure_residual_index` | float o array 1D | dB | — | `δpI0` → `Ld` / criterio 1 |
| `frequencies` | array 1D | Hz | centros nominales | `LWA` y límites de la Tabla 2 |
| `band_type` | str | — | `'third'` (por defecto) / `'octave'` | Consulta de la Tabla 2 |
| `grade` | str | — | `'engineering'` (por defecto) / `'survey'` | Selecciona `K` |
| `repeatability_limit` | float o array 1D | dB | por defecto Tabla 2 | Sobrescribe `s` del criterio 3 |

Devuelve un `SoundPowerIntensityResult`: `partial_power`/`partial_power_level`
por segmento y banda, `sound_power`/`sound_power_level` (total de banda, `NaN`
donde `negative_band`), `surface_pressure_intensity_index` (`FpI`),
`negative_partial_power_index` (`F+/-`), `repeatability`,
`dynamic_capability_index` (`Ld`), `achieved_grade`, `surface_area`,
`sound_power_level_a` y `grade`.

## 4. Grado de precisión, sala anecoica (ISO 3745)

Cuando se requiere la máxima exactitud, ISO 3745 mide la potencia sonora en una
**sala anecoica** o **semianecoica** cualificada, donde el campo libre permite que
un conjunto fijo de micrófonos muestree directamente la presión sonora radiada. Es
la contraparte de grado 1 del método de superficie envolvente de la Sección 1, con
coordenadas de micrófono normalizadas, una corrección por ruido de fondo por
posición y una corrección meteorológica explícita.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_precision_anechoic_es.svg" alt="Potencia sonora de precisión de ISO 3745 en una sala anecoica: paredes revestidas de cuñas, el dispositivo bajo ensayo en el centro y un conjunto hemisférico de micrófonos a un radio fijo, con el nivel de potencia sonora formado a partir de la presión promediada en la superficie más las correcciones de área, ruido de fondo y meteorológica" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_precision_anechoic_es_dark.svg" alt="Potencia sonora de precisión de ISO 3745 en una sala anecoica: paredes revestidas de cuñas, el dispositivo bajo ensayo en el centro y un conjunto hemisférico de micrófonos a un radio fijo, con el nivel de potencia sonora formado a partir de la presión promediada en la superficie más las correcciones de área, ruido de fondo y meteorológica" style="width:92%">

**Nivel de potencia sonora (Cláusula 8).** El nivel de potencia sonora por banda es
el nivel de presión promediado en la superficie más el término de superficie y las
correcciones:

$$
L_W = \overline{L_p} + 10\lg\frac{S}{S_0} + C_1 + C_2 + C_3,
$$

con $S = 4\pi r^2$ sobre la esfera o $S = 2\pi r^2$ sobre la semiesfera,
$S_0 = 1\ \text{m}^2$. $C_1$ y $C_2$ son las correcciones meteorológicas
(términos de referencia e impedancia de radiación); $C_3$ tiene en cuenta la
absorción del aire sobre el radio de medición. Las posiciones de micrófono son los
conjuntos normalizados de vectores unitarios de las Tablas D.1 (esfera), E.1
(semiesfera) y E.2 (semiesfera, banda ancha).

```python
import numpy as np
import phonometry as ph

# Las 40 posiciones normalizadas de la semiesfera (vectores unitarios escalados por el radio).
pos = ph.precision_positions("hemisphere", radius=1.0, count=40)
print(pos.shape)                      # (40, 3)

# SPL en banda de octava/tercio (dB) en cada una de las 40 posiciones; aquí un
# valor uniforme de 74 dB en una banda. El resultado lleva S = 2*pi*r^2 y LW con C1+C2+C3.
levels = np.full((40, 1), 74.0)
res = ph.sound_power_anechoic(levels, "hemisphere", radius=1.0)
print(round(res.surface_area, 3))                 # 6.283  (2*pi*1^2)
print(np.round(res.sound_power_level, 2))         # [81.85]
```

**Correcciones por ruido de fondo y meteorológica.** La corrección por ruido de
fondo $K_1$ se aplica **por posición** y se acota donde la diferencia
señal-fondo es pequeña (Ec. 11); la corrección meteorológica se evalúa a partir de
la temperatura y la presión estática medidas.

```python
import numpy as np
import phonometry as ph

# K1 para una diferencia señal-fondo de 6 dB en una banda de borde <=200 Hz: el
# límite es 1.26 dB (Ec. 11). Los niveles de fuente y fondo son [posiciones, bandas].
k1 = ph.precision_background_correction(
    np.array([[56.0]]), np.array([[50.0]]), np.array([200.0]))
print(round(float(k1[0, 0]), 4))      # 1.2563

# Correcciones meteorológicas en la referencia de 23 C, 101.325 kPa (Ec. 16):
mc = ph.meteorological_corrections(23.0, 101.325)
print(round(mc.c1, 4), round(mc.c2, 4))   # -0.1282 0.0

# Incertidumbre expandida (EJEMPLO de la Cláusula 10.5): sigma_R0 = 0.5, sigma_omc = 2.0,
# k = 2 -> U = 4.1 dB.
print(round(ph.precision_uncertainty(0.5, 2.0, 2.0), 3))   # 4.123
```

Sobre varias bandas `sound_power_anechoic` devuelve un `PrecisionSoundPowerResult`
representable que lleva el `LW` por banda y el total ponderado A:

```python
import numpy as np
import phonometry as ph

# Una máquina con pico en frecuencias medias medida sobre el conjunto hemisférico de
# 40 posiciones (Anexo E). levels_positions es el espectro de presión superficial
# (40, NB): un espectro base con pico cerca de 1 kHz más una pequeña dispersión espacial por posición.
freqs = np.array([125, 250, 500, 1000, 2000, 4000, 8000], float)
base = 70.0 + 8.0 * np.exp(-(np.log2(freqs / 1000.0) ** 2) / 2.0)
rng = np.random.default_rng(7)
levels = base[None, :] + rng.normal(0.0, 1.0, (40, freqs.size))

result = ph.sound_power_anechoic(levels, "hemisphere", radius=1.0, frequencies=freqs)
print(round(result.sound_power_level_a, 1))   # 89.3
result.plot()   # espectro LW, LWA en el título (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/precision_anechoic_power_es.svg" alt="El espectro de nivel de potencia sonora de precisión de una máquina con pico en frecuencias medias medida sobre el conjunto hemisférico de ISO 3745, una barra por banda con pico cerca de 1 kHz, con el total ponderado A de 89,3 dB(A) en el título" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/precision_anechoic_power_es_dark.svg" alt="El espectro de nivel de potencia sonora de precisión de una máquina con pico en frecuencias medias medida sobre el conjunto hemisférico de ISO 3745, una barra por banda con pico cerca de 1 kHz, con el total ponderado A de 89,3 dB(A) en el título" style="width:88%">

*Una barra por banda: la presión promediada en la superficie más las correcciones
de área, ruido de fondo y meteorológica dan `LW(f)`, y la suma energética ponderada
A entre bandas da el número único `LWA` del título.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# result es el PrecisionSoundPowerResult calculado arriba. Una línea:
result.plot()
plt.show()

# A mano: un espectro de barras de LW con el total ponderado A en el título.
freqs = result.frequencies
positions = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(positions, result.sound_power_level, width=0.7, color="#1f77b4")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de potencia sonora LW [dB]")
ax.set_title(
    f"Potencia sonora de precisión (ISO 3745)  LWA = {result.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

## 5. Barrido de intensidad de precisión (ISO 9614-3)

ISO 9614-3 es el método de barrido de grado 1: como ISO 9614-2, integra la
intensidad normal sobre una superficie que encierra la fuente, pero con un barrido
continuo, criterios de indicadores de campo más estrictos y un presupuesto de
incertidumbre explícito.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_intensity_scan_es.svg" alt="Barrido de intensidad sonora de precisión de ISO 9614-3: una fuente encerrada por una superficie de medición dividida en segmentos, una sonda de intensidad de dos micrófonos barrida a lo largo de un recorrido en serpentina sobre cada segmento, y la potencia sonora formada sumando la intensidad normal por el área del segmento, sujeta a los criterios de aceptación de los indicadores de campo" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_intensity_scan_es_dark.svg" alt="Barrido de intensidad sonora de precisión de ISO 9614-3: una fuente encerrada por una superficie de medición dividida en segmentos, una sonda de intensidad de dos micrófonos barrida a lo largo de un recorrido en serpentina sobre cada segmento, y la potencia sonora formada sumando la intensidad normal por el área del segmento, sujeta a los criterios de aceptación de los indicadores de campo" style="width:92%">

**Potencia y nivel (Cláusula 7).** La potencia parcial de cada segmento es
$P_i = I_{n,i}\,S_i$; el total $P = \sum_i P_i$ da
$L_W = 10\lg(P/P_0)$, $P_0 = 1\ \text{pW}$. Una banda cuya intensidad neta es
negativa (más potencia entrando que saliendo) se marca no aplicable en lugar de
registrarse. Los indicadores de campo (variabilidad temporal $F_T$, los
indicadores presión-intensidad con y sin signo, y la no uniformidad $F_S$)
gobiernan los cinco criterios de aceptación.

```python
import numpy as np
import phonometry as ph

# Una superficie totalmente envolvente con una intensidad normal uniforme In = W/S
# recupera exactamente la potencia de la fuente: LW = 10*lg(W/P0). Aquí W = 100 uW -> 80 dB.
areas = np.array([0.5, 1.0, 0.25, 2.0])
w = 1.0e-4
i_n = np.full(areas.shape, w / float(areas.sum()))
res = ph.sound_power_intensity_precision(i_n, areas)
print(round(float(res.sound_power[0]), 6))          # 0.0001
print(round(float(res.sound_power_level[0]), 2))    # 80.0
```

A lo largo de varias bandas el resultado lleva el `LW` por banda (`NaN` donde la
potencia neta es no positiva) y marca esas bandas como `not_applicable`:

```python
import numpy as np
import phonometry as ph

# Cuatro superficies parciales barridas sobre cinco bandas de tercio de octava. Cada
# celda de partial_intensity es la intensidad normal con signo In_i (W/m^2); areas son
# las áreas de las superficies parciales Si. La banda de 250 Hz tiene potencia neta
# negativa (un campo localmente reactivo), así que ISO 9614-3 la marca no aplicable (cláusula 9.2) -> NaN.
freqs = np.array([250, 500, 1000, 2000, 4000], float)
areas = np.array([0.5, 1.0, 0.75, 0.5])
base_intensity = np.array([2.0e-6, 8.0e-6, 2.0e-5, 1.0e-5, 3.0e-6])
partial_intensity = base_intensity[None, :] * np.array([1.0, 1.1, 0.9, 1.05])[:, None]
partial_intensity[:, 0] = [2.0e-6, -3.0e-6, -4.0e-6, -1.0e-6]   # banda de potencia neta negativa

result = ph.sound_power_intensity_precision(partial_intensity, areas, frequencies=freqs)
print(result.not_applicable_band.tolist())   # [True, False, False, False, False]
print(round(result.sound_power_level_a, 1))   # 80.6
result.plot()   # espectro LW; la banda no aplicable con trama (requiere matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_scan_power_es.svg" alt="El espectro de nivel de potencia sonora del barrido de intensidad de precisión sobre cinco bandas de tercio de octava, cuatro barras determinadas y una banda de 250 Hz con trama y en gris marcada como no aplicable porque su intensidad neta es negativa, con el total ponderado A de 80,6 dB(A) en el título" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_scan_power_es_dark.svg" alt="El espectro de nivel de potencia sonora del barrido de intensidad de precisión sobre cinco bandas de tercio de octava, cuatro barras determinadas y una banda de 250 Hz con trama y en gris marcada como no aplicable porque su intensidad neta es negativa, con el total ponderado A de 80,6 dB(A) en el título" style="width:88%">

*La banda de 250 Hz da un neto negativo (más energía entrando que saliendo), así que
ISO 9614-3 la declara no aplicable —la figura la trama y la agrisa mientras las
cuatro bandas determinadas y el total ponderado A se mantienen.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# result es el PrecisionIntensityResult calculado arriba. Una línea:
result.plot()
plt.show()

# A mano: bandas determinadas como barras de LW; una banda no aplicable (su LW es NaN)
# se señala con una franja gris y con trama a plena altura en lugar de una barra de altura cero.
freqs = result.frequencies
positions = np.arange(freqs.size)
neg = result.not_applicable_band
lw = np.nan_to_num(result.sound_power_level)
fig, ax = plt.subplots()
ax.bar(positions[~neg], lw[~neg], width=0.7, color="#1f77b4")
for pos in positions[neg]:
    ax.axvspan(pos - 0.35, pos + 0.35, facecolor="#888888", alpha=0.28,
               hatch="//", edgecolor="#888888")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de potencia sonora LW [dB]")
ax.set_title(
    f"Barrido de intensidad de precisión (ISO 9614-3)  "
    f"LWA = {result.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

## Véase también

- [Intensidad sonora (p-p)](/phonometry/es/guides/intensity/) — la sonda de dos
  micrófonos, su sesgo por diferencias finitas y los indicadores de campo de
  ISO 9614-1 que sustentan el método de barrido.
- [Acústica de salas](/phonometry/es/guides/room-acoustics/) — el tiempo
  de reverberación y el área de absorción sonora equivalente (ISO 354) que
  alimentan `K2` y el área de absorción de ISO 3741.
- [Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/) — los
  índices de aislamiento a ruido aéreo y a impactos y las predicciones de emisión
  de EN 12354 que consumen una `LW` de fuente.
- [Niveles](/phonometry/es/guides/levels/) — el promediado en energía y la ponderación A
  que sustentan `LWA`.
- [Teoría](/phonometry/es/reference/theory/environment-transport/) — las derivaciones de Waterhouse, K1/K2 y
  C1/C2.
- Referencia de la API: [`emission.sound_power`](/phonometry/es/reference/api/power/sound-power/), [`emission.sound_power_reverberation`](/phonometry/es/reference/api/power/sound-power-reverberation/) y [`emission.sound_power_intensity`](/phonometry/es/reference/api/power/sound-power-intensity/).

## Referencias

- Fahy, F. J. (1995). *Sound intensity* (2.ª ed.). E&FN Spon.
  ISBN 978-0-419-19810-9.
  [doi:10.4324/9780203475386](https://doi.org/10.4324/9780203475386).
  La monografía sobre el flujo de energía sonora: por qué la intensidad
  separa la energía que sale de la fuente de la energía estacionaria que
  solo pasa, detrás de los métodos de barrido de las secciones 3 y 5.
- Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound fields and
  transducers*. Academic Press. ISBN 978-0-12-391421-7.
  [doi:10.1016/C2011-0-05897-0](https://doi.org/10.1016/C2011-0-05897-0).
  Radiación y campos sonoros: las relaciones entre presión y potencia en
  campo libre y campo difuso sobre las que descansan los métodos de
  superficie envolvente y de sala reverberante.
- International Organization for Standardization. (2019). *Acoustics —
  Determination of sound power levels of noise sources — Guidelines for the
  use of basic standards* (ISO 3740:2019).
  [Catálogo iso.org](https://www.iso.org/standard/45107.html).
  La guía de selección detrás de "Elegir un método": grados, entornos y
  criterios de tamaño de fuente y de ruido de fondo para toda la familia.
- International Organization for Standardization. (2010). *Acoustics —
  Determination of sound power levels and sound energy levels of noise
  sources using sound pressure — Precision methods for reverberation test
  rooms* (ISO 3741:2010).
  [Catálogo iso.org](https://www.iso.org/standard/52053.html).
  El método en sala reverberante de la sección 2.
- International Organization for Standardization. (2010). *Acoustics —
  Determination of sound power levels and sound energy levels of noise
  sources using sound pressure — Engineering methods for an essentially free
  field over a reflecting plane* (ISO 3744:2010).
  [Catálogo iso.org](https://www.iso.org/standard/52055.html).
  El método de superficie envolvente de la sección 1.
- International Organization for Standardization. (2012). *Acoustics —
  Determination of sound power levels and sound energy levels of noise
  sources using sound pressure — Precision methods for anechoic rooms and
  hemi-anechoic rooms* (ISO 3745:2012).
  [Catálogo iso.org](https://www.iso.org/standard/45362.html).
  El método de precisión en sala anecoica de la sección 4.

## Normas

ISO 3744:2010, *Acoustics — Determination of sound power levels
and sound energy levels of noise sources using sound pressure — Engineering
methods for an essentially free field over a reflecting plane* — el método de
superficie envolvente: las áreas de la semiesfera y la caja, las correcciones
`K1`/`K2`, las posiciones de micrófono del Anexo B y la ponderación A del
Anexo E. ISO 3746:2010, *… Survey method using an enveloping measurement
surface over a reflecting plane* — el grado de inspección que comparte las
mismas fórmulas con criterios más laxos. ISO 3741:2010, *… Precision methods
for reverberation test rooms* — los métodos directo (Ec. 20) y de comparación
con las correcciones de Waterhouse y meteorológicas y los criterios de
cualificación de la Tabla 1. ISO 3745:2012, *… Precision methods for anechoic
rooms and hemi-anechoic rooms* — el nivel de potencia de la cláusula 8, la
corrección de fondo por posición (Ec. 11), las correcciones meteorológicas y
los conjuntos de micrófonos normalizados. ISO 9614-2:1996, *Acoustics —
Determination of sound power levels of noise sources using sound intensity —
Part 2: Measurement by scanning* — las potencias parciales, los indicadores de
campo `FpI` y `F+/-` y los criterios de grado. ISO 9614-3:2002, *… Part 3:
Precision method for measurement by scanning* — el método de barrido de
grado 1, sus indicadores de campo y el marcado de no aplicable de la
cláusula 9.2.
