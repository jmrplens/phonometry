---
title: "Medición del aislamiento en campo e índices"
description: "Aislamiento en campo a ruido aéreo, a impactos y de fachadas (ISO 16283-1/2/3) con índices ponderados de un solo número (ISO 717-1/2), la incertidumbre de medición que los cualifica (ISO 12999-1) y el método de control de ISO 10052."
---

Esta guía continúa desde la [guía de Acústica de salas](/phonometry/es/guides/room-acoustics/):
la misma respuesta al impulso, medida a ambos lados de un cerramiento, da su
aislamiento acústico. Esta página cubre el aislamiento medido *en el edificio*:
aislamiento en campo a ruido aéreo, a impactos y de fachadas con índices de un
solo número (ISO 16283-1/2/3, ISO 717-1/2), la incertidumbre de medición que
cualifica cada índice (ISO 12999-1) y el método de control rápido de
ISO 10052. La caracterización en laboratorio de un elemento está en
[Medición del aislamiento en laboratorio](/phonometry/es/guides/insulation-lab/)
y la predicción del comportamiento in situ en
[Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/).

## Aislamiento en campo e índices de un solo número (ISO 16283-1, ISO 717-1)

Para calificar una pared o un forjado, mide el nivel promediado en energía en
la sala **emisora** ($L_1$) y en la sala **receptora** ($L_2$) por banda de
tercio de octava y forma la diferencia de niveles $D = L_1 - L_2$. Dos
normalizaciones la hacen comparable entre salas. La **diferencia de niveles
estandarizada** refiere el tiempo de reverberación de la sala receptora $T$ a
$T_0 = 0{,}5$ s (de modo que con $T = 0{,}5$ s, $D_{nT} = D$ exactamente), y el
**índice de reducción sonora aparente** normaliza por la superficie del
cerramiento $S$ y el área de absorción de Sabine $A$:

$$
D_{nT} = D + 10 \log_{10} \frac{T}{T_0}, \qquad
R' = D + 10 \log_{10} \frac{S}{A}, \qquad A = \frac{0{,}16\ V}{T}.
$$

Las posiciones se promedian en energía con
$L = 10 \log_{10}\left( \frac{1}{n} \sum_i 10^{L_i/10} \right)$.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup_es.svg" alt="Montaje de aislamiento a ruido aéreo en campo: un altavoz en la sala emisora, micrófonos promediados en energía en las salas emisora y receptora a través del cerramiento común" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup_es_dark.svg" alt="Montaje de aislamiento a ruido aéreo en campo: un altavoz en la sala emisora, micrófonos promediados en energía en las salas emisora y receptora a través del cerramiento común" style="width:92%">

El espectro por bandas se reduce a un número mediante el **método de la curva
de referencia** de ISO 717-1: una curva de referencia fija se desplaza en
pasos de 1 dB hacia la curva medida hasta que la suma de desviaciones
*desfavorables* (donde la medición cae por debajo de la referencia) es lo más
grande posible pero no mayor que 32,0 dB (16 bandas de tercio de octava) o
10,0 dB (5 bandas de octava). El índice (`Rw`, `R'w`, `DnT,w` …) es la
referencia desplazada leída a 500 Hz. Los **términos de adaptación
espectral** $C$ (ruido rosa) y $C_{tr}$ (tráfico urbano) añaden la
penalización en baja frecuencia de una fuente real.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_es.svg" alt="Índice de reducción sonora medido en tercios de octava con la curva de referencia de ISO 717-1 desplazada y el índice ponderado resultante a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_es_dark.svg" alt="Índice de reducción sonora medido en tercios de octava con la curva de referencia de ISO 717-1 desplazada y el índice ponderado resultante a 500 Hz" style="width:80%">

```python
import numpy as np
from phonometry import airborne_insulation, weighted_rating, energy_average_level

# Promedia en energía varias posiciones de micrófono en una sala (dB)
print(round(float(energy_average_level([60.0, 66.0])), 1))   # 64.0

# Aislamiento en campo por banda; la superficie S y el volumen V añaden R'
l1 = np.full(16, 80.0)                                # niveles de la sala emisora
l2 = np.full(16, 40.0)                                # niveles de la sala receptora
t2 = np.full(16, 0.5)                                 # T de la sala receptora (s)
ins = airborne_insulation(l1, l2, t2, area=10.0, volume=50.0)
print(round(float(ins.dnt[0]), 1))                   # 40.0  (= D ya que T = T0)
print(round(float(ins.r_prime[0]), 1))               # 38.0

# Índice de un solo número desde un espectro R medido de 16 bandas (ISO 717-1 Anexo C)
R = [20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
     28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5]
w = weighted_rating(R)
print(w.rating, w.c, w.ctr)                          # 30 -2 -3  ->  Rw(C;Ctr) = 30(-2;-3)

w.plot()   # R' medido frente a la referencia ISO 717-1 desplazada, desviaciones sombreadas (requiere matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — la curva medida frente a la referencia ISO 717-1 desplazada:
w.plot()
plt.show()

# A mano, con los campos de la curva por banda que ahora lleva el resultado:
fig, ax = plt.subplots()
ax.semilogx(w.band_centers, w.measured, "o-", label="R' medido")
ax.semilogx(w.band_centers, w.shifted_reference, "s--", label="Referencia desplazada")
ax.fill_between(w.band_centers, w.measured, w.shifted_reference,
                where=w.measured < w.shifted_reference, interpolate=True,
                alpha=0.3, label="Desviaciones desfavorables")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Índice de reducción sonora [dB]")
ax.set_title(f"Rw = {w.rating} dB  (C={w.c:+d}; Ctr={w.ctr:+d})")
ax.legend()
plt.show()
```

</details>

Calcula `l1`, `l2` y `t2` en las mismas 16 bandas de tercio de octava de
100 Hz a 3150 Hz — obtén `t2` de
`room_parameters(ir, fs, limits=(100, 3150), fraction=3).t30`, por ejemplo — y
pásalos a `airborne_insulation`. Alimenta el espectro `dnt` (o `r_prime`) de esa
función a `weighted_rating`, de modo que cada banda quede alineada índice a
índice con la curva de referencia ISO 717-1.

### Parámetros de `airborne_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Niveles de la sala emisora (2D se promedia en energía) |
| `l2` | array 1D o 2D | dB | mismo número de bandas | Niveles de la sala receptora |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `area` | float, opcional | m² | > 0, con `volume` | Superficie del cerramiento `S` (habilita `R'`) |
| `volume` | float, opcional | m³ | > 0, con `area` | Volumen de la sala receptora `V` |
| `t0` | float | s | por defecto `0.5` | Tiempo de reverberación de referencia `T0` |

### Parámetros de `weighted_rating()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `values_by_band` | array 1D | dB | 16 (tercios) o 5 (octavas) | `R`, `R'`, `DnT` … medidos por banda |
| `bands` | str o `None` | — | `'third-octave'` / `'octave'` / `None` | `None` lo infiere del número de bandas |

`airborne_insulation()` devuelve un `AirborneInsulationResult` (`d`, `dnt`,
`r_prime` o `None`); `weighted_rating()` devuelve un `WeightedRatingResult`
(`rating`, `c`, `ctr`, `unfavourable_sum`, todos enteros salvo la suma).

### Rangos de frecuencia ampliados e índices con un decimal

Cuando la medición cubre más que las 16 bandas básicas de 100–3150 Hz, el
Anexo B de ISO 717-1 define términos de adaptación adicionales con el rango
como subíndice ($C_{50\text{–}3150}$, $C_{50\text{–}5000}$,
$C_{100\text{–}5000}$ y sus homólogos $C_{tr}$), calculados con los espectros de
la Tabla B.1 sobre el rango ampliado. `weighted_rating_extended` toma los
valores por banda *con sus frecuencias centrales* y devuelve el índice básico
más todos los términos ampliados que cubra la entrada (la variante de impactos
`weighted_impact_rating_extended` añade $C_{I,50\text{–}2500}$). Con
`one_decimal=True` la curva de referencia se desplaza en pasos de 0,1 dB y
todas las reducciones conservan un decimal: la variante que ISO 717 prescribe
«para la expresión de la incertidumbre» y que el Anexo B de ISO 12999-1 exige
al declarar la incertidumbre de un valor único.

```python
from phonometry import weighted_rating_extended

freqs = [50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
         630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
r_ext = [18.7, 19.2, 20.0, *R, 26.8, 29.2]     # ISO 717-1 Anexo C, Tabla C.2
ext = weighted_rating_extended(r_ext, freqs)
print(ext.rating, ext.c, ext.ctr, ext.c_50_5000, ext.ctr_50_5000)
# 30 -2 -3 -2 -4   ->  Rw(C;Ctr;C50-5000;Ctr,50-5000) = 30(-2;-3;-2;-4)

one_dp = weighted_rating_extended(r_ext, freqs, one_decimal=True)
print(one_dp.rating)   # 30.0, el índice en pasos de 0,1 dB para incertidumbres
```

### Ruido de impactos (ISO 16283-2, ISO 717-2)

El ruido de pisadas se califica al revés. En lugar de cuánto *bloquea* un
forjado, el aislamiento a impactos mide cuánto introduce en la sala inferior
una **máquina de impactos normalizada** situada en el forjado superior —así que
un número *mayor* es *peor*. El nivel de presión de ruido de impactos $L_i$
promediado en energía en la sala receptora se normaliza igual que el caso
aéreo, pero con un cambio de signo en el término de reverberación:

$$
L'_{nT} = L_i - 10 \log_{10} \frac{T}{T_0}, \qquad
L'_n = L_i + 10 \log_{10} \frac{A}{A_0}, \quad
A_0 = 10\ \text{m}^2,\ A = \frac{0{,}16\ V}{T}.
$$

El nivel de impactos **estandarizado** $L'_{nT}$ ($T_0 = 0{,}5$ s para viviendas)
solo necesita el $T$ de la sala receptora, así que con $T = 0{,}5$ s es igual a
$L_i$; el nivel **normalizado** $L'_n$ (referido a un área de absorción de
10 m²) necesita además el volumen de la sala receptora. Fíjate en el signo
**menos** —más reverberación *reduce* $L'_{nT}$, al contrario que el $D_{nT}$
aéreo.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impact_setup_es.svg" alt="Montaje de aislamiento a impactos en campo: una máquina de impactos normalizada sobre el suelo de la sala emisora superior, micrófonos promediados en energía en la sala receptora inferior, y el tiempo de reverberación de la sala receptora" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impact_setup_es_dark.svg" alt="Montaje de aislamiento a impactos en campo: una máquina de impactos normalizada sobre el suelo de la sala emisora superior, micrófonos promediados en energía en la sala receptora inferior, y el tiempo de reverberación de la sala receptora" style="width:92%">

El índice de un solo número (ISO 717-2) desplaza el mismo estilo de curva de
referencia, pero una **desviación desfavorable se produce ahora donde la
medición *supera* la referencia** (el ruido de impactos es peor cuanto más
alto) —el signo opuesto a ISO 717-1. El índice (`Ln,w`, `L'n,w`, `L'nT,w`) es
la referencia desplazada leída a 500 Hz; para bandas de octava se reduce además
en 5 dB. El término de adaptación espectral $C_I = L_{n,\text{sum}} - 15 - L_{n,w}$
usa la suma energética sobre 100–2500 Hz (16 tercios excluyendo 3150 Hz) o
125–2000 Hz (octavas). Para mediciones ampliadas hasta 50 Hz,
`weighted_impact_rating_extended` devuelve además el término de rango ampliado
$C_{I,50\text{–}2500}$ (NOTA de A.2.1) y, con `one_decimal=True`, el índice en
pasos de 0,1 dB usado en las declaraciones de incertidumbre (reproduce los
valores impresos $L_{n,r,0,w} = 77,6$ dB y $C_{I,r,0} = -10,3$ dB de A.2.2).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_es.svg" alt="Nivel de presión de ruido de impactos normalizado medido en tercios de octava con la curva de referencia de ISO 717-2 desplazada y el índice ponderado resultante leído a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_es_dark.svg" alt="Nivel de presión de ruido de impactos normalizado medido en tercios de octava con la curva de referencia de ISO 717-2 desplazada y el índice ponderado resultante leído a 500 Hz" style="width:80%">

```python
import numpy as np
from phonometry import impact_insulation, weighted_impact_rating

# 16 niveles de impactos Li en tercios de octava (100 Hz - 3150 Hz), dB, del
# ejemplo resuelto del Anexo C de ISO 717-2, y el T de la sala receptora por banda.
li = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
               73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])
t2 = np.full(16, 0.5)

imp = impact_insulation(li, t2, volume=50.0)
print(round(float(imp.l_n_t[0]), 1))          # 62.1  (= Li ya que T = T0)
print(round(float(imp.l_n[0]), 1))            # 64.1  normalizado a A0 = 10 m^2

# Índice de impactos ponderado + término de adaptación espectral CI (ISO 717-2)
res_imp = weighted_impact_rating(imp.l_n_t)
print(res_imp.rating, res_imp.ci, res_imp.unfavourable_sum)   # 79 -11 28.0  ->  L'nT,w(CI)=79(-11)

# Los datos en banda de octava llevan la reducción extra de -5 dB (Cláusula 4.3.2)
octave = np.array([65.3, 64.5, 58.0, 55.8, 43.0])
print(weighted_impact_rating(octave).rating)  # 54

res_imp.plot()   # L'nT medido frente a la referencia ISO 717-2 desplazada, exceso sombreado (requiere matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — L'nT medido frente a la referencia ISO 717-2 desplazada (exceso sombreado):
res_imp.plot()
plt.show()

# A mano, con la curva por banda que ahora lleva el resultado (signo opuesto: la
# desviación desfavorable está donde el nivel MEDIDO supera la referencia).
# Aquí la entrada fue l_n_t, así que la magnitud valorada es el nivel de campo L'nT,w:
fig, ax = plt.subplots()
ax.semilogx(res_imp.band_centers, res_imp.measured, "o-", label="L'nT medido")
ax.semilogx(res_imp.band_centers, res_imp.shifted_reference, "s--", label="Referencia desplazada")
ax.fill_between(res_imp.band_centers, res_imp.shifted_reference, res_imp.measured,
                where=res_imp.measured > res_imp.shifted_reference, interpolate=True,
                alpha=0.3, label="Desviaciones desfavorables")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de presión sonora de impacto [dB]")
ax.set_title(f"L'nT,w = {res_imp.rating} dB  (CI={res_imp.ci:+d})")
ax.legend()
plt.show()
```

</details>

Pasa el `l_n_t` (o `l_n`) de `impact_insulation` directamente a
`weighted_impact_rating`; el índice y `CI` reproducen los valores del Anexo C de
ISO 717-2 (tercios `L'nT,w = 79`, `CI = −11`; octava `54`, `CI = 0`).

#### Parámetros de `impact_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `li` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | SPL de impactos promediado en energía (2D se promedia sobre las posiciones) |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `volume` | float, opcional | m³ | > 0 | `V` de la sala receptora (habilita `L'n`) |
| `t0` | float | s | por defecto `0.5` | Tiempo de reverberación de referencia `T0` |

#### Parámetros de `weighted_impact_rating()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `values_by_band` | array 1D | dB | 16 (tercios) o 5 (octavas) | `Ln`, `L'n` o `L'nT` medidos por banda |
| `bands` | str o `None` | — | `'third-octave'` / `'octave'` / `None` | `None` lo infiere del número de bandas |

`impact_insulation()` devuelve un `ImpactInsulationResult` (`l_n_t`, `l_n` o
`None`); `weighted_impact_rating()` devuelve un `ImpactRatingResult` (`rating`,
`ci` enteros, `unfavourable_sum` en dB).

### Aislamiento a ruido aéreo de fachadas en campo (ISO 16283-3)

La misma lógica fuente/receptor alcanza la **fachada** del edificio, pero ahora
la fuente está *en el exterior*: un altavoz a 45° o el propio tráfico rodado. En
lugar de una diferencia de niveles a través de un cerramiento interior,
ISO 16283-3 referencia el nivel de la sala receptora $L_2$ al nivel **2 m frente
a la fachada** $L_{1,2m}$, dando la diferencia de niveles $D_{2m}$ y, exactamente
como en el caso a ruido aéreo, sus formas estandarizada y normalizada:

$$
D_{2m} = L_{1,2m} - L_2, \quad
D_{2m,nT} = D_{2m} + 10 \log_{10}\frac{T}{T_0}, \quad
D_{2m,n} = D_{2m} - 10 \log_{10}\frac{A}{A_0},
$$

con $T_0 = 0{,}5$ s, $A_0 = 10$ m² y $A = 0{,}16\ V/T$ (viviendas). Cuando el
micrófono se sitúa **sobre el elemento de ensayo** (nivel superficial $L_{1,s}$),
el método del *elemento* también da un índice de reducción sonora aparente, que
lleva una corrección fija por ángulo de incidencia: $-1{,}5$ dB para el método del
altavoz a 45° y $-3$ dB para el método de tráfico rodado con todos los ángulos:

$$
R'_{45°} = L_{1,s} - L_2 + 10 \log_{10}\frac{S}{A} - 1{,}5, \qquad
R'_{tr,s} = L_{1,s} - L_2 + 10 \log_{10}\frac{S}{A} - 3.
$$

La magnitud de fachada es a ruido aéreo, así que su índice de un solo número usa
la curva de referencia de **ISO 717-1** a través de `weighted_rating` sin cambios
(Anexo F).

```python
import numpy as np
from phonometry import facade_insulation, weighted_rating

# Nivel exterior 2 m frente a la fachada, nivel de la sala receptora y T por
# banda de tercio de octava; surface_level es el micrófono sobre el elemento de ensayo.
l1_2m = np.full(16, 75.0)                              # L1,2m en el exterior
l2 = np.full(16, 33.0)                                 # L2 de la sala receptora
t2 = np.full(16, 0.5)                                  # T de la sala receptora (s)

fac = facade_insulation(l1_2m, l2, t2, volume=50.0, area=11.5,
                        surface_level=np.full(16, 78.0), method="loudspeaker")
print(round(float(fac.d_2m[0]), 1))                    # 42.0  D2m = L1,2m - L2
print(round(float(fac.d_2m_nt[0]), 1))                 # 42.0  (= D2m ya que T = T0)
print(round(float(fac.d_2m_n[0]), 1))                  # 40.0  normalizado a A0 = 10 m^2
print(round(float(fac.r_prime[0]), 1))                 # 42.1  R'45deg (altavoz, -1.5 dB)

# El método del elemento por tráfico rodado lleva en su lugar la corrección de -3 dB para todos los ángulos
tr = facade_insulation(l1_2m, l2, t2, volume=50.0, area=11.5,
                       surface_level=np.full(16, 78.0), method="road_traffic")
print(round(float(tr.r_prime[0]), 1))                  # 40.6  R'tr,s (tráfico, -3 dB)

# La magnitud de fachada es a ruido aéreo: valora D2m,nT con el motor de ISO 717-1
print(weighted_rating(fac.d_2m_nt).rating)             # 42  Dls,2m,nT,w

fac.plot()   # D2m,nT por banda con D2m, D2m,n y R' superpuestos (requiere matplotlib)
```

`surface_level`, `area` y `volume` son todos opcionales: solo con `l1_2m`, `l2`
y `t2` la función devuelve `d_2m` y `d_2m_nt`; añade `volume` para `d_2m_n`;
añade `surface_level` **y** `area` **y** `volume` para `r_prime`. Las posiciones
se promedian en energía con la fórmula del nivel superficial (Cláusula 9.5.1);
se asume que los niveles por banda ya están corregidos por ruido de fondo.

#### Parámetros de `facade_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1_2m` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Nivel 2 m frente a la fachada `L1,2m` |
| `l2` | array 1D o 2D | dB | mismo número de bandas | Niveles de la sala receptora |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `area` | float, opcional | m² | > 0, con `surface_level`, `volume` | Superficie del elemento de ensayo `S` (habilita `R'`) |
| `volume` | float, opcional | m³ | > 0 | Sala receptora `V` (habilita `D2m,n`; requerido para `R'`) |
| `surface_level` | array 1D/2D, opcional | dB | mismo número de bandas | Nivel superficial `L1,s` sobre el elemento (habilita `R'`) |
| `method` | str | — | `'loudspeaker'` (−1,5 dB) / `'road_traffic'` (−3 dB) | Corrección por ángulo de incidencia de `R'` |
| `t0` | float | s | por defecto `0.5` | Tiempo de reverberación de referencia `T0` |
| `frequencies` | array 1D, opcional | Hz | — | Centros de banda que lleva el resultado para representar |

`facade_insulation()` devuelve un `FacadeInsulationResult` (`d_2m`, `d_2m_nt`,
`d_2m_n` o `None`, `r_prime` o `None`, `frequencies`); pasa cualquier magnitud de
fachada de 16 bandas a `weighted_rating` para su número único de ISO 717-1.

## Incertidumbre de medición (ISO 12999-1)

Un índice sin incertidumbre es solo medio resultado. ISO 12999-1 no vuelve a
medir nada; tabula la **incertidumbre típica** $u$ de cada magnitud de
aislamiento acústico —derivada de ensayos interlaboratorio— y prescribe cómo
expandirla y combinarla. Qué desviación típica es $u$ depende de la **situación
de medición** (Cláusula 5.2):

| Situación | Significado | Incertidumbre típica $u$ |
| :--- | :--- | :--- |
| **A** | caracterización en laboratorio (ISO 10140) | reproducibilidad $\sigma_R$ |
| **B** | misma ubicación, equipos distintos | in situ $\sigma_{situ}$ |
| **C** | misma ubicación, mismo operador repetido | repetibilidad $\sigma_r$ |

La incertidumbre expandida es $U = k\ u$ (Fórmula 2) con el factor de cobertura
$k$ de la Tabla 8. Un intervalo bilateral $Y = y \pm U$ (Fórmula 3, $k = 1{,}96$ al
95 %) *informa* un valor; el factor **unilateral** ($k = 1{,}65$ al 95 %) *declara
conformidad* con un requisito (Fórmulas 4/5).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso12999_es.svg" alt="Flujo de incertidumbre ISO 12999-1: incertidumbre típica de las tablas, reducida por mediciones repetidas y combinada en cuadratura, y luego expandida por el factor de cobertura de la Tabla 8 en un informe bilateral o una decisión de conformidad unilateral" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso12999_es_dark.svg" alt="Flujo de incertidumbre ISO 12999-1: incertidumbre típica de las tablas, reducida por mediciones repetidas y combinada en cuadratura, y luego expandida por el factor de cobertura de la Tabla 8 en un informe bilateral o una decisión de conformidad unilateral" style="width:82%">

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_es.svg" alt="Un índice ponderado informado con su incertidumbre expandida bilateral al 95 % en las situaciones A, B y C, con la incertidumbre de reproducibilidad más ancha y la de repetibilidad más estrecha" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_es_dark.svg" alt="Un índice ponderado informado con su incertidumbre expandida bilateral al 95 % en las situaciones A, B y C, con la incertidumbre de reproducibilidad más ancha y la de repetibilidad más estrecha" style="width:80%">

```python
from phonometry import (band_uncertainty, single_number_uncertainty,
                        uncertain_value, satisfies_lower_requirement)

# Situación B (mismo edificio, equipos distintos) -> la desviación típica in situ.
print(single_number_uncertainty("r_w", "B"))       # 0.9  dB  (Tabla 3)
u = band_uncertainty("airborne", "B")              # u por banda (Tabla 2)
print(len(u.frequencies), u.uncertainties[10])     # 21 1.1  (la banda de 500 Hz)

# Informa R'w = 52 dB con un intervalo bilateral al 95 % (k = 1.96, Tabla 8):
uv = uncertain_value(52.0, "rprime_w", "B")        # los alias resuelven a r_w
print(uv.coverage_factor, round(uv.expanded_uncertainty, 1))    # 1.96 1.8
print(round(uv.lower, 1), round(uv.upper, 1))      # 50.2 53.8  ->  52 ± 1.8 dB

# Declarar conformidad usa el factor UNILATERAL (k = 1.65): ¿supera R'w de forma
# demostrable un requisito de 50 dB?
uc = uncertain_value(52.0, "rprime_w", "B", one_sided=True)
print(satisfies_lower_requirement(52.0, uc.expanded_uncertainty, 50.0))   # True
```

Las magnitudes a impactos ofrecen solo las situaciones B/C (Tabla 4, sin banda de
500 Hz en la edición de 2020), y $\Delta L$ solo la situación A. Los descriptores
son insensibles a mayúsculas y con alias (`rprime_w`/`dnt_w`→`r_w`,
`lprime_n_w`→`ln_w`); combina componentes independientes en cuadratura con
`combine_uncertainties`, y redúcelas por $m$ mediciones independientes con
`reduce_by_independent_measurements` ($u/\sqrt{m}$).

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
from phonometry import uncertain_value

# El mismo R'w = 52 dB informado en cada situación con su U bilateral al 95 %.
situations = ["A", "B", "C"]
vals = [uncertain_value(52.0, "r_w", s) for s in situations]

fig, ax = plt.subplots(figsize=(7, 4))
ax.errorbar(situations, [v.value for v in vals],
            yerr=[v.expanded_uncertainty for v in vals],
            fmt="o", capsize=8, color="tab:blue")
for s, v in zip(situations, vals):
    ax.annotate(f"±{v.expanded_uncertainty:.1f}", (s, v.upper),
                textcoords="offset points", xytext=(8, 4))
ax.set_ylabel("R'w [dB]"); ax.set_xlabel("Situación de medición")
ax.set_title("R'w = 52 dB con incertidumbre expandida al 95 % (ISO 12999-1)")
fig.tight_layout()
plt.show()
```

</details>

### Parámetros de `band_uncertainty()` / `single_number_uncertainty()` / `uncertain_value()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `measurand` | str | — | `'airborne'` / `'impact'` / `'impact_reduction'` | Selecciona la Tabla 2 / 4 / 6 |
| `quantity` | str | — | `'r_w'`, `'ln_w'`, `'delta_lw'` (+ alias, variantes `+c`/`+ctr`) | Descriptor de un solo número |
| `situation` | str | — | `'A'` / `'B'` / `'C'` | Situación de medición (Cláusula 5.2) |
| `value` | float | dB | — | Mejor estimación `y` a la que adjuntar `U` |
| `coverage` | float | — | por defecto `0.95` | Nivel de confianza (Tabla 8) |
| `one_sided` | bool | — | por defecto `False` | Factor unilateral para verificaciones de conformidad |
| `upper_limit` | bool | — | por defecto `False` | Selecciona el límite superior σR95 (ruido aéreo, situación A) |

`band_uncertainty()` devuelve una `BandUncertainty` (`frequencies`,
`uncertainties`, `.to_arrays()`); `single_number_uncertainty()` un float;
`uncertain_value()` un `UncertainValue` (`value`, `standard_uncertainty`,
`coverage_factor`, `expanded_uncertainty`, `.lower`, `.upper`). El mapa de solo
lectura `COVERAGE_FACTORS` expone la Tabla 8 indexada por `(confidence, one_sided)`.

## Método de control en campo (ISO 10052)

Los métodos de ingeniería anteriores compran precisión con esfuerzo —
micrófonos barridos, tiempos de reverberación por banda, corrección de ruido de
fondo cuidadosa—. Para una comprobación rápida en una vivienda, ISO 10052 define
un **método de control (survey)**: bandas de octava, un sonómetro de mano y una
sola magnitud — el **índice de reverberación** `k = 10 lg(T/T0)` (`T0 = 0,5 s`)
— que arrastra la corrección de la sala receptora. Cada magnitud del control es
entonces una simple suma de `k`: la diferencia de niveles estandarizada
`DnT = D + k`, la normalizada `Dn = D + k + 10 lg(A0 T0 / (0,16 V))`, la aparente
`R' = D + k + 10 lg(S T0 / (0,16 V))` (usando `V/7,5` como `S` cuando es mayor) y,
para impactos y fachadas, `L'nT = Li - k` y `D2m,nT = D2m + k`. Las referencias a
cláusulas siguen ISO 10052:2021; las fórmulas y la tabla del índice de
reverberación son idénticas en la armonizada EN ISO 10052:2004+A1:2010.

El índice de reverberación se **mide** —pasa el tiempo de reverberación a
`reverberation_index(T)`— o, en un control, se **estima** a partir del tipo de
sala y el volumen con `estimate_reverberation_index(V, room)` (Tabla 4:
amueblada `"kitchen"` / `"bathroom"` / `"furnished"`, o las clases de
construcción sin amueblar `"a"`–`"h"` y las mixtas `"a+e"`…`"d+h"`). Una cuarta
magnitud propia de este método es el **ruido de equipos de servicio** `LXY` — la
media energética de tres posiciones ponderadas A o C.

```python
import numpy as np
from phonometry import (reverberation_index, estimate_reverberation_index,
                        survey_airborne_insulation, survey_service_equipment_level)

# Niveles por banda de octava (125-2000 Hz) y el T medido de la sala receptora.
l1 = np.array([88.0, 90.0, 92.0, 92.0, 90.0])
l2 = np.array([55.0, 51.0, 47.0, 41.0, 35.0])
k = reverberation_index([0.70, 0.60, 0.50, 0.45, 0.40])   # k = 10 lg(T/0.5)
res = survey_airborne_insulation(l1, l2, k, volume=50.0, area=12.0)
print(np.round(res.d_nt, 1))          # [34.5 39.8 45.  50.5 54. ]  DnT = D + k
print(res.rating.rating, res.rating.c)        # 49 -1  ->  DnT,w (C)
print(res.r_prime_rating.rating)               # 48  ->  R'w

# ¿Sin T medido? Estima k con la Tabla 4 (paredes pesadas, suelo duro,
# 35-60 m³ -> clase "g").
k_est = estimate_reverberation_index(50.0, "g")
print(k_est)                                   # [4.5 5.  5.5 5.5 5.5]

# Ruido de equipos de servicio: media energética de tres posiciones (dB(A)).
se = survey_service_equipment_level([35.0, 30.0, 32.0], 3.0, volume=50.0)
print(round(float(se.l_xy), 1), round(float(se.l_xy_nt), 1))   # 32.8 29.8

res.plot()   # DnT vs curva de referencia ISO 717-1 desplazada (necesita matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/survey_insulation_es.svg" alt="Aislamiento aéreo por el método de control: la diferencia de niveles bruta D y la estandarizada DnT en las cinco bandas de octava, con la corrección por índice de reverberación k sombreada entre ambas" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/survey_insulation_es_dark.svg" alt="Aislamiento aéreo por el método de control: la diferencia de niveles bruta D y la estandarizada DnT en las cinco bandas de octava, con la corrección por índice de reverberación k sombreada entre ambas" style="width:80%">

*El índice de reverberación `k = 10 lg(T/T0)` desplaza la diferencia de niveles
bruta `D` hacia la estandarizada `DnT` — hacia arriba donde la sala es viva
(`T > T0`), hacia abajo donde es apagada. El índice automático solo se forma con
exactamente 5 valores de octava (o 16 de tercio de octava).*

### Parámetros de `survey_airborne_insulation()` y afines

| Parámetro | Tipo | Unidades | Rango / def. | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1` / `l2` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Niveles emisor / receptor (o exterior `l1_2m`) |
| `li` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Niveles de impacto (media energética de posiciones) |
| `reverberation_index` | escalar o array 1D | dB | uno por banda | `k` de `reverberation_index` o `estimate_reverberation_index`; `survey_service_equipment_level()` también acepta un `k` escalar |
| `volume` | float | m³ | > 0 | Volumen receptor `V` (para `Dn` / `L'n` / `R'` / normalizadas) |
| `area` | float | m² | > 0 | Área de partición común `S` (aéreo `R'`; regla `V/7,5`) |
| `measurements` | array | dB | exactamente 3 | Posiciones de equipo de servicio (`survey_service_equipment_level`) |
| `room` | str | — | `"kitchen"`/`"bathroom"`/`"furnished"`/`"a"`–`"h"`/`"a+e"`… | Clase de sala para `estimate_reverberation_index` (Tabla 4) |

`survey_airborne_insulation()` devuelve un `SurveyAirborneResult` (`d`, `d_nt`,
`d_n`, `r_prime`, `rating`, `r_prime_rating`); `survey_impact_insulation()` un
`SurveyImpactResult` (`l_i`, `l_nt`, `l_n`, `rating`);
`survey_facade_insulation()` un `SurveyFacadeResult`;
`survey_service_equipment_level()` un `SurveyServiceEquipmentResult` (`l_xy`,
`l_xy_nt`, `l_xy_n`).

---

**Normas.** ISO 16283-1:2014, ISO 16283-2 e ISO 16283-3:2016, *Acoustics —
Field measurement of sound insulation in buildings and of building elements* —
las diferencias de nivel, normalizaciones y métodos de elemento; ISO 717-1 e
ISO 717-2 — los índices de un solo número por curva de referencia y los
términos de adaptación espectral C, Ctr y CI; ISO 12999-1:2020 — las
incertidumbres típicas por situación de medición y los factores de cobertura;
su marco de precisión se apoya en ISO 5725 (contexto, no implementada
directamente); ISO 10052:2021 (armonizada como EN ISO 10052:2004+A1:2010) — el
método de control en campo: la corrección por índice de reverberación, las
magnitudes aérea, de impacto y de fachada estandarizadas/normalizadas, y el
ruido de equipos de servicio.

## Véase también

- [Medición del aislamiento en laboratorio](/phonometry/es/guides/insulation-lab/):
  la caracterización de elementos de ISO 10140 con la que se comparan estas
  magnitudes de campo.
- [Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/):
  el comportamiento in situ predicho a partir de datos de elemento de laboratorio.
- [Acústica de salas](/phonometry/es/guides/room-acoustics/) — la respuesta al impulso,
  los parámetros de sala y la absorción sonora sobre los que se apoya la cadena de aislamiento de esta guía.
- [Niveles](/phonometry/es/guides/levels/) — el promediado en energía y las métricas de
  nivel tras los niveles de las salas emisora/receptora.
- [Bancos de filtros](/phonometry/es/guides/filter-banks/) — los filtros de octava
  fraccionaria IEC 61260 usados para los espectros de aislamiento.
- [Teoría](/phonometry/es/reference/theory/) — la derivación de la curva de referencia tras
  los índices ponderados de un solo número.
