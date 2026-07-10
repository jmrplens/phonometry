---
title: "Acústica de la edificación y aislamiento"
description: "Aislamiento en campo a ruido aéreo, a impactos y de fachadas (ISO 16283-1/2/3) con índices ponderados de un solo número (ISO 717-1/2), caracterización en laboratorio de elementos constructivos (ISO 10140), predicción de la transmisión por flancos (EN 12354-1/2) e incertidumbre de medición (ISO 12999-1)."
---

Esta guía continúa desde la [guía de Acústica de salas](/phonometry/es/guides/room-acoustics/):
la misma respuesta al impulso, medida a ambos lados de un cerramiento, da su
aislamiento acústico. Donde la acústica de salas describe el campo sonoro dentro
de un único recinto, la acústica de la edificación describe cuánto de ese campo
pasa *entre* recintos. Esta página sigue la cadena del aislamiento: aislamiento
en campo a ruido aéreo, a impactos y de fachadas con índices de un solo número
(ISO 16283-1/2/3, ISO 717-1/2), la caracterización en laboratorio de un elemento
constructivo (ISO 10140), la predicción del comportamiento in situ a partir de la
transmisión por flancos (EN 12354-1/2) y la incertidumbre de medición que
cualifica cada índice (ISO 12999-1).

## 1. Aislamiento en campo e índices de un solo número (ISO 16283-1, ISO 717-1)

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_es.png" alt="Índice de reducción sonora medido en tercios de octava con la curva de referencia de ISO 717-1 desplazada y el índice ponderado resultante a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_es_dark.png" alt="Índice de reducción sonora medido en tercios de octava con la curva de referencia de ISO 717-1 desplazada y el índice ponderado resultante a 500 Hz" style="width:80%">

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
125–2000 Hz (octavas).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_es.png" alt="Nivel de presión de ruido de impactos normalizado medido en tercios de octava con la curva de referencia de ISO 717-2 desplazada y el índice ponderado resultante leído a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_es_dark.png" alt="Nivel de presión de ruido de impactos normalizado medido en tercios de octava con la curva de referencia de ISO 717-2 desplazada y el índice ponderado resultante leído a 500 Hz" style="width:80%">

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

## 2. Medición en laboratorio (ISO 10140)

Todo lo anterior es una medición **en campo** (las magnitudes con prima $R'$,
$L'_n$): el número que un edificio real alcanza, con transmisión por flancos
incluida. Para valorar un elemento por sí solo —un tipo de pared, un suelo
flotante, una ventana— se lleva a un **laboratorio** cualificado (ISO 10140),
donde la transmisión por flancos suprimida hace que la transmisión *directa* sea
toda la historia. Las fórmulas pierden sus primas: el **índice de reducción
sonora** $R$ (no $R'$) y el **nivel de impactos normalizado** $L_n$ (no $L'_n$),
con el área de absorción de la sala receptora $A = 0{,}16\ V/T$ ahora una propiedad
conocida de la instalación:

$$
R = L_1 - L_2 + 10 \log_{10}\frac{S}{A}, \qquad
L_n = L_i + 10 \log_{10}\frac{A}{A_0}, \quad A_0 = 10\ \text{m}^2.
$$

| | Campo (ISO 16283) | Laboratorio (ISO 10140) |
| :--- | :--- | :--- |
| Ruido aéreo | $R'$ aparente (con flancos) | $R$ directo (flancos suprimidos) |
| Impactos | $L'_n$ aparente | $L_n$ directo |
| Área de absorción | medida en la sala | propiedad de la instalación |

Los índices de un solo número reutilizan los mismísimos motores de ISO 717-1/2
(`weighted_rating`, `weighted_impact_rating`): un espectro $R$ se valora a $R_w$
exactamente igual que un espectro $R'$ se valoraba a $R'_w$. Antes de formar el
índice, los niveles de la sala receptora deben **corregirse por ruido de fondo**
(Cláusula 4.3): la resta energética $10 \log_{10}(10^{L_{sb}/10} - 10^{L_b/10})$
se aplica para un margen señal-fondo de 6–15 dB, una corrección fija de 1,3 dB
(el *límite de medición*) en 6 dB o por debajo, y ninguna corrección en 15 dB o
por encima.

```python
import numpy as np
from phonometry import (lab_airborne_insulation, lab_impact_insulation,
                        background_correction)

# Niveles emisor/receptor y T de la sala receptora en las 16 bandas de tercio
# de octava; S es el área libre de la abertura de ensayo, V el volumen de la sala receptora.
l1 = np.full(16, 80.0)
l2 = np.full(16, 40.0)
t2 = np.full(16, 0.5)
lab = lab_airborne_insulation(l1, l2, t2, area=10.0, volume=50.0)
print(round(float(lab.r[0]), 1))              # 38.0  R = L1 - L2 + 10 lg(S/A)
print(round(float(lab.absorption[0]), 1))     # 16.0  A = 0.16 V / T (m^2)
print(lab.rating.rating, lab.rating.c, lab.rating.ctr)   # 38 0 0  ->  Rw(C;Ctr)

# Impactos: el nivel de la máquina de impactos Li normalizado a A0 = 10 m^2 da Ln
li = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
               73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])
imp = lab_impact_insulation(li, t2, volume=50.0)
print(round(float(imp.l_n[0]), 1))            # 64.1  Ln = Li + 10 lg(A/A0)
print(imp.rating.rating, imp.rating.ci)       # 81 -11  ->  Ln,w(CI)

# Corrección por ruido de fondo: márgenes 6 / 1 / 20 dB -> saturado / saturado / sin cambio
corrected = background_correction([30.0, 33.0, 50.0], [24.0, 32.0, 30.0])
print(np.round(corrected, 1))                 # [28.7 31.7 50.0]  (saturación de 1.3 dB dos veces)

lab.rating.plot()   # R medido frente a la referencia ISO 717-1 desplazada (requiere matplotlib)
```

Un margen en 6 dB o por debajo emite un `LabInsulationWarning` y marca la banda
como el límite de medición; captúralo con `warnings.simplefilter("error",
LabInsulationWarning)`. El índice automático se forma solo cuando se suministran
exactamente 16 valores en tercio de octava o 5 en octava (`rating` es `None` en
caso contrario).

### Parámetros de `lab_airborne_insulation()` / `lab_impact_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1` / `l2` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Niveles emisor / receptor (ruido aéreo) |
| `li` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | SPL de impactos de la máquina de impactos (impactos) |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `area` | float | m² | > 0 | Área libre de la abertura de ensayo `S` (solo ruido aéreo) |
| `volume` | float | m³ | > 0 | Volumen de la sala receptora `V` |

`lab_airborne_insulation()` devuelve un `LabAirborneInsulationResult` (`r`,
`absorption`, `rating`); `lab_impact_insulation()` un
`LabImpactInsulationResult` (`l_n`, `absorption`, `rating`);
`background_correction(signal_and_background, background)` devuelve los niveles
corregidos directamente.

## 3. Predicción del comportamiento (EN 12354)

Un índice de laboratorio describe un elemento de forma aislada, pero el sonido
que un edificio transmite realmente también viaja *alrededor* del cerramiento
—por el suelo, por la fachada, a través de las paredes de flanco— y se vuelve a
radiar en la sala receptora. Esta **transmisión por flancos** es toda la
diferencia entre el $R$ de laboratorio y el $R'$ de campo. EN 12354 predice el
índice aparente in situ a partir de los índices de laboratorio de los elementos
más la transmisión vibratoria de sus uniones.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths_es.svg" alt="El camino directo Dd a través del elemento separador y los tres caminos de flanco Ff, Df y Fd en cada unión entre un elemento de flanco y el elemento separador" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths_es_dark.svg" alt="El camino directo Dd a través del elemento separador y los tres caminos de flanco Ff, Df y Fd en cada unión entre un elemento de flanco y el elemento separador" style="width:92%">

Cada unión entre un elemento de flanco y el elemento separador lleva tres
caminos —$Ff$ (flanco→flanco), $Df$ (directo→flanco) y $Fd$ (flanco→directo)—
junto al único camino directo $Dd$. El **modelo simplificado de un solo número**
los combina energéticamente (Fórmula 26):

$$
R'_w = -10 \log_{10}\Big[ 10^{-R_{Dd,w}/10}
      + \sum 10^{-R_{Ff,w}/10} + \sum 10^{-R_{Df,w}/10}
      + \sum 10^{-R_{Fd,w}/10} \Big],
$$

con el camino directo $R_{Dd,w} = R_{s,w} + \Delta R_{Dd,w}$ (Fórmula 27) y cada
camino de flanco (Fórmula 28a)

$$
R_{ij,w} = \tfrac{R_{i,w} + R_{j,w}}{2} + \Delta R_{ij,w} + K_{ij}
         + 10 \log_{10}\frac{S_s}{l_0\ l_f},
$$

donde $l_0 = 1$ m es la longitud de acoplamiento de referencia, $l_f$ la longitud
de acoplamiento de la unión y $K_{ij}$ el **índice de reducción vibracional** de
la unión (Anexo E, empírico en la relación de masas
$M = \log_{10}(m'_{\perp,i}/m'_i)$).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo_es.png" alt="Índices de reducción sonora por camino para el ejemplo del Anexo H.3 de EN 12354-1 y la fracción de energía transmitida de cada camino, mostrando el camino directo dominando en R'w = 52 dB" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo_es_dark.png" alt="Índices de reducción sonora por camino para el ejemplo del Anexo H.3 de EN 12354-1 y la fracción de energía transmitida de cada camino, mostrando el camino directo dominando en R'w = 52 dB" style="width:80%">

```python
import numpy as np
from phonometry import (junction_vibration_reduction, flanking_element,
                        predicted_airborne_insulation)

# EN 12354-1 Anexo H.3: una pared separadora Rs,w = 57 dB, área Ss = 11.5 m², con
# cuatro elementos de flanco. El modelo simplificado lee el Kij de cada unión a
# 500 Hz a partir de la relación de masas m'perp / m' (Anexo E); aquí la unión
# rígida en cruz del suelo (la relación de masas está redondeada, de ahí 12.5 vs Anexo 12.4):
print(round(junction_vibration_reduction("rigid_cross", "through", 1.61), 1))  # 12.5  KFf
print(round(junction_vibration_reduction("rigid_cross", "corner",  1.61), 1))  #  8.9  KFd = KDf

# Construye los tres caminos de flanco (Ff, Df, Fd) de cada elemento a partir del
# Kij tabulado del Anexo H, luego combina el camino directo Dd energéticamente (Fórmula 26).
elements = [   # (nombre, Rw, KFf, KFd = KDf, longitud de acoplamiento lf)
    ("floor",    49, 12.4,  8.9, 4.50),
    ("ceiling",  46, 14.4,  9.2, 4.50),
    ("facade",   42, 12.6,  6.7, 2.55),
    ("int-wall", 33, 33.5, 15.7, 2.55),
]
paths = []
for name, rw, k_ff, k_fd, lf in elements:
    paths += flanking_element(label=name, r_flanking=rw, r_separating=57,
                              k_ff=k_ff, k_fd=k_fd, k_df=k_fd,
                              separating_area=11.5, coupling_length=lf)

res = predicted_airborne_insulation(r_direct=57.0, flanking_paths=paths)
print(round(res.r_prime_w, 1))                          # 52.2  ->  R'w = 52 dB
print(res.dominant.label, round(res.dominant.fraction, 2))   # Dd 0.33 (domina el directo)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# Usa `paths` y `res` del snippet anterior.
# Índice de reducción sonora por camino y fracción de energía transmitida de cada
# camino para el resultado del Anexo H.3 calculado arriba.
labels = [p.label for p in res.paths]
r_w = [p.r_w for p in res.paths]
frac = [100.0 * p.fraction for p in res.paths]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
ax1.bar(labels, r_w, color="tab:blue")
ax1.axhline(res.r_prime_w, ls="--", color="k", label=f"R'w = {res.r_prime_w:.1f} dB")
ax1.set_ylabel("Rij,w del camino [dB]"); ax1.legend()
ax2.bar(labels, frac, color="tab:orange")
ax2.set_ylabel("Fracción de energía [%]"); ax2.set_xlabel("Camino de transmisión")
for ax in (ax1, ax2):
    ax.tick_params(axis="x", rotation=45)
fig.suptitle("EN 12354-1 Anexo H.3 — transmisión por flancos")
fig.tight_layout()
plt.show()
```

</details>

Cada camino de flanco añadido rebaja estrictamente $R'_w$ por debajo del directo
$R_{Dd,w} = 57$; `res.paths` expone la fracción de energía transmitida de cada
camino, de modo que el camino dominante queda visible. `flanking_element` es una
función de conveniencia que construye de una vez los tres caminos de una unión; el constructor
de camino único que hay detrás, `flanking_path`, construye un camino `Ff`, `Df`
o `Fd` cada vez (Fórmula 28a). La Cláusula 4.4.2 también
impone un límite inferior $K_{ij} \ge K_{ij,\min}$ a partir de la geometría de la
unión: calcúlalo con `junction_min_vibration_reduction` y pásalo a
`flanking_path(..., kij_min=...)`, que eleva un $K_{ij}$ por debajo del límite
hasta el mínimo:

```python
from phonometry import junction_min_vibration_reduction
# Kij,min = 10 lg[lf·l0·(1/Si + 1/Sj)]; los elementos grandes dan un límite bajo
# (aquí negativo), así que un Kij tabulado realista rara vez se satura.
print(round(junction_min_vibration_reduction(coupling_length=4.5,
                                             s_i=11.5, s_j=11.5), 1))     # -1.1
```

La contrapartida a impactos (EN 12354-2, Fórmula 21) es una resta directa:
$L'_{n,w} = L_{n,w,eq} - \Delta L_w + K$, con el nivel equivalente del suelo
desnudo $L_{n,w,eq} = 164 - 35 \log_{10}(m'/m'_0)$ (Anexo B), la mejora del
revestimiento $\Delta L_w$ (ISO 717-2) y la corrección por flancos $K$ de la
Tabla 1.

```python
from phonometry import (equivalent_impact_level, impact_flanking_correction,
                        predicted_impact_insulation, standardized_impact_level)

# EN 12354-2 Anexo E.3: un forjado de hormigón de 0.14 m (m' = 322 kg/m²) con un
# suelo flotante (ΔLw = 33 dB), salas una sobre otra, masa media de flanco 145 kg/m².
ln_eq = equivalent_impact_level(322.0)                   # 164 - 35 lg(m')
k = impact_flanking_correction(322.0, 145.0)             # Tabla 1 (sep 322, flk 145)
imp = predicted_impact_insulation(ln_w_eq=ln_eq, delta_l_w=33.0, k_correction=k)
print(round(ln_eq, 1), k, round(imp.l_prime_n_w, 1))     # 76.2 2 45.2  ->  L'n,w = 45 dB
print(round(standardized_impact_level(imp.l_prime_n_w, 50.0), 1))   # 43.0  L'nT,w
```

### Parámetros de `junction_vibration_reduction()` / `flanking_element()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `junction_type` | str | — | `'rigid_cross'` / `'rigid_t'` / `'flexible_t'` / `'lightweight_facade'` | Geometría de la unión (Anexo E) |
| `path` | str | — | `'through'` (K13) / `'corner'` (K12 = K23) | Rama del camino |
| `mass_ratio` | float | — | > 0 | `m'⊥,i / m'i` (Fórmula E.2) |
| `frequency` | float | Hz | por defecto `500` | Solo `flexible_t` depende de la frecuencia |
| `r_flanking` / `r_separating` | float | dB | — | Índices ponderados del elemento de flanco / separador |
| `k_ff` / `k_fd` / `k_df` | float | dB | — | `Kij` de la unión para los tres caminos |
| `separating_area` | float | m² | > 0 | Superficie del elemento separador `Ss` |
| `coupling_length` | float | m | > 0 | Longitud de acoplamiento de la unión `lf` |
| `delta_r_ff` / `delta_r_fd` / `delta_r_df` | float | dB | por defecto `0` | Mejoras del trasdosado por camino |

### Parámetros de `flanking_path()`

| Parámetro | Tipo | Unidades | Rango / defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `label` | str | — | — | Nombre visible del camino |
| `kind` | str | — | `'Ff'` / `'Df'` / `'Fd'` | Rama de flanco del camino |
| `r_source` / `r_receive` | float | dB | — | Índices ponderados de los elementos lado emisor / lado receptor |
| `k_ij` | float | dB | — | Índice de reducción vibracional de la unión para este camino |
| `separating_area` | float | m² | > 0 | Área del elemento separador `Ss` |
| `coupling_length` | float | m | > 0 | Longitud de acoplamiento `lf` |
| `delta_r` | float | dB | def.: `0` | Mejora por revestimiento en este camino |
| `kij_min` | float | dB | def.: `None` | Si se da, `k_ij` se acota inferiormente a este mínimo de la Fórmula E.4 |

`predicted_airborne_insulation()` devuelve un `AirbornePredictionResult`
(`r_prime_w`, `r_direct_w`, `paths` de `PathContribution`, `dominant`);
`predicted_impact_insulation()` un `ImpactPredictionResult` (`l_prime_n_w`,
`ln_w_eq`, `delta_l_w`, `k_correction`). El modelo simplificado lleva una
desviación típica declarada de unos 2 dB (Cláusula 5).

## 4. Incertidumbre de medición (ISO 12999-1)

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_es.png" alt="Un índice ponderado informado con su incertidumbre expandida bilateral al 95 % en las situaciones A, B y C, con la incertidumbre de reproducibilidad más ancha y la de repetibilidad más estrecha" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_es_dark.png" alt="Un índice ponderado informado con su incertidumbre expandida bilateral al 95 % en las situaciones A, B y C, con la incertidumbre de reproducibilidad más ancha y la de repetibilidad más estrecha" style="width:80%">

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

---

**Normas.** ISO 16283-1:2014, ISO 16283-2 e ISO 16283-3:2016, *Acoustics —
Field measurement of sound insulation in buildings and of building elements* —
las diferencias de nivel, normalizaciones y métodos de elemento del §1;
ISO 717-1 e ISO 717-2 — los índices de un solo número por curva de referencia y
los términos de adaptación espectral C, Ctr y CI; ISO 10140-2:2010, ISO 10140-3:2010 e
ISO 10140-4:2010 — los R y Ln de laboratorio con la corrección de ruido de
fondo del §2; EN 12354-1:2000 y EN 12354-2:2000 — las predicciones
simplificadas de transmisión por flancos del §3 (uniones del Anexo E, ejemplos
resueltos H.3 y E.3); ISO 12999-1:2020 — las incertidumbres típicas por
situación de medición y los factores de cobertura del §4; su marco de
precisión se apoya en ISO 5725 (contexto, no implementada directamente).

## Véase también

- [Acústica de salas](/phonometry/es/guides/room-acoustics/) — la respuesta al impulso,
  los parámetros de sala y la absorción sonora sobre los que se apoya la cadena de aislamiento de esta guía.
- [Niveles](/phonometry/es/guides/levels/) — el promediado en energía y las métricas de
  nivel tras los niveles de las salas emisora/receptora.
- [Bancos de filtros](/phonometry/es/guides/filter-banks/) — los filtros de octava
  fraccionaria IEC 61260 usados para los espectros de aislamiento.
- [Potencia sonora](/phonometry/es/guides/sound-power/) — los métodos de `LW` que comparten
  la maquinaria del área de absorción de la sala receptora.
- [Teoría](/phonometry/es/reference/theory/) — la derivación de la curva de referencia tras
  los índices ponderados de un solo número.
