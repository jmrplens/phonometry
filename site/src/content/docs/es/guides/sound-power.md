---
title: "Potencia sonora"
description: "Nivel de potencia sonora LW por tres vías: presión sonora sobre superficie envolvente (ISO 3744/3746), el método de precisión en sala reverberante con las correcciones de Waterhouse y C1/C2 (ISO 3741) y el barrido de intensidad con indicadores de campo y grado alcanzado (ISO 9614-2)."
---

La presión *sonora* depende de dónde te sitúes y de la sala en la que estés;
la **potencia** sonora no. El nivel de potencia sonora `LW` es la energía
acústica total por segundo que radia una fuente, referida a `P0 = 1 pW`, y es
el descriptor de **emisión** independiente del dispositivo que figura en una
ficha técnica, alimenta una predicción de sala (ISO 12354) o se contrasta con
un límite de emisión de ruido. Esta página cubre las tres vías que phonometry
implementa para obtenerlo y cuándo recurrir a cada una: una superficie
envolvente de *presión* en campo (ISO 3744/3746), el campo difuso de una
*sala reverberante* (ISO 3741) y el *barrido* de intensidad sobre una
superficie (ISO 9614-2).

## Elegir un método

Las tres proporcionan la misma magnitud —un `LW` por banda y un total
ponderado A `LWA`— pero bajo entornos, grados de precisión y restricciones
prácticas distintos.

| Método | Norma | Magnitud medida | Entorno | Grado de precisión | Cuándo usarlo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Superficie envolvente | **ISO 3744** (ingeniería) / **ISO 3746** (control) | Presión sonora sobre una semiesfera o caja | Campo esencialmente libre sobre uno o varios planos reflectantes | Grado 2 (`σR0 ≈ 1.5 dB`) / grado 3 (`≈ 3.0 dB`) | In situ o en una sala grande; sin instalación de ensayo especial disponible |
| Sala reverberante | **ISO 3741** | Presión sonora en el campo difuso | Sala reverberante cualificada de paredes rígidas | Grado 1 (precisión) | Máxima precisión para fuentes estacionarias de banda ancha en laboratorio |
| Barrido de intensidad | **ISO 9614-2** | Intensidad sonora normal barrida sobre una superficie | Casi cualquiera, tolerante al ruido extraño estacionario | Grado 2 / 3 (a partir de los indicadores de campo por banda) | In situ con ruido de fondo, o una máquina entre muchas |

Los métodos de presión corrigen el nivel superficial por la sala (`K2`) y por
el ruido de fondo (`K1`); el método en sala reverberante necesita una sala
*cualificada* pero alcanza el grado de precisión; la intensidad rechaza la
energía de fondo estacionaria a costa de una sonda de dos micrófonos y una
comprobación de validez por banda. El resto de la página recorre cada uno por
turno.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_methods_es.svg" alt="Las tres vías de potencia sonora en paralelo: una superficie envolvente de presión sobre un plano reflectante (ISO 3744/3746), una fuente en una sala reverberante muestreada por micrófonos (ISO 3741) y una sonda de intensidad barriendo una superficie alrededor de la fuente (ISO 9614-2)" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_methods_es_dark.svg" alt="Las tres vías de potencia sonora en paralelo: una superficie envolvente de presión sobre un plano reflectante (ISO 3744/3746), una fuente en una sala reverberante muestreada por micrófonos (ISO 3741) y una sonda de intensidad barriendo una superficie alrededor de la fuente (ISO 9614-2)" style="width:92%">

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
`d`. ISO 3746 (control) comparte todas las fórmulas pero es más burda: menos
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
    reverberation_time=0.6, room_volume=300.0,          # datos de sala -> K2
)
print(round(res.surface_area, 2))                       # 14.14 m^2 (= 2*pi*1.5^2)
print(round(float(res.environmental_correction[0]), 2)) # K2 = 2.32 dB
print(round(res.sound_power_level_a, 1))                # LWA = 92.4 dB
print(round(res.uncertainty, 1))                        # U = 3.0 dB (2*sigma_R0)
print(np.round(res.sound_power_level, 1))               # LW por banda
```

El total ponderado A `LWA` se combina a partir de las potencias por banda con
las correcciones de ponderación A del Anexo E de ISO 3744, así que necesita
`frequencies`. Pasar los datos de sala (`reverberation_time` + `room_volume`,
o `absorption_area`, o `mean_absorption_coefficient` + `room_surface`) habilita
`K2`; omítelos y el campo se trata como libre (`K2 = 0`). Si el margen de fondo
cae por debajo del criterio del grado o `K2` supera el límite de validez, un
`SoundPowerWarning` avisa de que los niveles son cotas superiores —la
determinación se devuelve igualmente.

### Parámetros de `sound_power_pressure()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `levels_positions` | array 2D | dB | `(NM, NB)` | Una fila por posición, una columna por banda (o una única columna ponderada A) |
| `surface` | str | — | `'hemisphere'` / `'box'` | Forma de la superficie de medición |
| `radius` | float | m | > 0 (semiesfera) | Radio de la semiesfera `r` |
| `dimensions` | (float, float, float) | m | > 0 (caja) | `(l1, l2, l3)` del paralelepípedo de referencia |
| `distance` | float | m | > 0 (caja) | Distancia de medición `d` |
| `reflecting_planes` | int | — | `1` / `2` / `3`, por defecto `1` | Divide entre dos/cuatro el área de la semiesfera |
| `background_levels` | array 2D | dB | misma forma que `levels` | Habilita `K1` |
| `frequencies` | array 1D | Hz | centros de banda nominales | Habilita `LWA` (Anexo E) |
| `absorption_area` | float | m² | > 0 | `A` para `K2` (directo) |
| `reverberation_time`, `room_volume` | float | s, m³ | > 0 | `A = 0.16 V/T` para `K2` |
| `mean_absorption_coefficient`, `room_surface` | float | —, m² | `(0,1]`, > 0 | `A = α·Sv` para `K2` |
| `grade` | str | — | `'engineering'` (por defecto) / `'survey'` | ISO 3744 vs ISO 3746 |
| `omc_uncertainty` | float | dB | por defecto `0.0` | `σomc`, inestabilidad de operación/montaje, incorporada a `U` |

Devuelve un `SoundPowerResult`: `sound_power_level` (`LW` por banda),
`surface_pressure_level` (`Lp` tras K1/K2), `mean_pressure_level`,
`background_correction`/`environmental_correction` (`K1`/`K2`),
`directivity_index` (índice de directividad aparente `DIi*` por posición de
micrófono), `surface_area`, `sound_power_level_a` (`LWA`), `uncertainty`
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
L_W = \bar{L}_p + 10 \log_{10}\frac{A}{A_0} + 4.34\ \frac{A}{S}
      + 10 \log_{10}\left( 1 + \frac{S c}{8 V f} \right) + C_1 + C_2 - 6 .
$$

El término entre paréntesis es la **corrección de Waterhouse**: cerca de los
contornos de la sala la densidad de energía sonora es mayor que en el interior,
y este término (que se anula al crecer la frecuencia) restituye la energía que
los micrófonos del interior no captan. `C1` (cantidad de referencia) y `C2`
(impedancia de radiación) llevan el resultado a las condiciones meteorológicas
de referencia de 23 °C y 101,325 kPa,

$$
C_1 = -10 \log_{10}\frac{p_s}{p_{s0}} + 5 \log_{10}\frac{273.15 + \theta}{314}, \qquad
C_2 = -10 \log_{10}\frac{p_s}{p_{s0}} + 15 \log_{10}\frac{273.15 + \theta}{296},
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
```

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
fuente de referencia y su potencia conocida. Ambas devuelven un
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
grado **ingeniería** cuando se cumplen los criterios 1, 2 y 3, de **control**
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
```

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

## Véase también

- [Intensidad sonora (p-p)](/phonometry/es/guides/intensity/) — la sonda de dos
  micrófonos, su sesgo por diferencias finitas y los indicadores de campo de
  ISO 9614-1 que sustentan el método de barrido.
- [Acústica de salas y edificación](/phonometry/es/guides/room-acoustics/) — el tiempo
  de reverberación y el área de absorción sonora equivalente (ISO 354) que
  alimentan `K2` y el área de absorción de ISO 3741; aislamiento a impactos y a
  ruido aéreo.
- [Niveles](/phonometry/es/guides/levels/) — el promediado en energía y la ponderación A
  tras `LWA`.
- [Teoría](/phonometry/es/reference/theory/) — las derivaciones de Waterhouse, K1/K2 y
  C1/C2.
