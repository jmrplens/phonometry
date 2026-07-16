---
title: "Medición del aislamiento en laboratorio"
description: "Caracterización en laboratorio de elementos constructivos (ISO 10140), aislamiento acústico por intensidad (ISO 15186), mejora a impactos de revestimientos de suelo en maqueta pequeña (ISO 16251-1) y transmisión por flancos en laboratorio (ISO 10848)."
---

Para valorar un elemento constructivo por sí solo (un tipo de pared, un suelo
flotante, una ventana) se lleva a un laboratorio cualificado, donde la
transmisión por flancos suprimida hace que la transmisión directa sea toda la
historia. Esta página cubre la cadena de laboratorio: el índice de reducción
sonora y el nivel de impactos normalizado de ISO 10140, la alternativa por
intensidad sonora de ISO 15186, la mejora de revestimientos de suelo en maqueta
pequeña de ISO 16251-1 y la medición de la transmisión por flancos de
ISO 10848. La medición en campo y sus índices están en
[Medición del aislamiento en campo e índices](/phonometry/es/guides/insulation-field/),
y la predicción que consume estos índices de laboratorio en
[Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/).

## Medición en laboratorio (ISO 10140)

Una [medición ISO 16283 en campo](/phonometry/es/guides/insulation-field/) da las magnitudes
con prima ($R'$, $L'_n$): el número que un edificio real alcanza, con
transmisión por flancos incluida. Para valorar un elemento por sí solo —un tipo de pared, un suelo
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
| Índice aéreo de elemento | $R'$ aparente (con flancos) | $R$ directo (flancos suprimidos) |
| Aéreo de pareja de salas | $D_{nT}$, $D_n$ (sin prima: magnitudes de sala) | — |
| Impactos | $L'_n$, $L'_{nT}$ aparentes | $L_n$ directo |
| Índice global | $R'_w$, $D_{nT,w}$, $L'_{n,w}$, $L'_{nT,w}$ | $R_w$, $L_{n,w}$ |
| Área de absorción | medida en la sala | propiedad de la instalación |

El apóstrofo es el marcador de flancos de la acústica de edificios, y viaja
con la magnitud hasta su índice global: $R_w$ califica un espectro de
laboratorio, $R'_w$ uno de campo. Las diferencias de nivel estandarizada y
normalizada $D_{nT}$ y $D_n$ no llevan prima porque describen la pareja de
salas y no un elemento, así que no hay contraparte sin flancos que marcar. En
una construcción bien ejecutada $R'_w$ queda unos pocos dB por debajo del
$R_w$ de laboratorio de la misma partición; una diferencia mucho mayor dice
que dominan los flancos, y el
[modelo EN 12354](/phonometry/es/guides/insulation-prediction/) dice qué vía
domina.

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

## Aislamiento acústico por intensidad (ISO 15186)

El método de laboratorio de ISO 10140, más arriba, lee la potencia transmitida de forma
*indirecta*, a partir del nivel de la sala receptora y de su área de absorción —
lo que falla cuando los flancos filtran una potencia que la sala integra
igualmente. El método por **intensidad sonora** (ISO 15186) lo evita: una sonda
de intensidad barre una superficie de medición que envuelve el espécimen y mide
la potencia radiada de forma *directa*, así que solo contribuye el elemento
ensayado. Es la herramienta preferida cuando la transmisión por flancos es alta
(ISO 15186-1:2000, cláusula 1). A partir del nivel de la sala emisora $L_{p1}$ y
del nivel medio de intensidad normal $L_{In}$ sobre la superficie (área $S_m$),
para un espécimen de área $S$,

$$
R_I = L_{p1} - 6 - \left[ L_{In} + 10 \log_{10}\frac{S_m}{S} \right],
$$

donde los $6$ dB son el desfase de campo difuso entre el nivel de presión sonora
y el nivel de intensidad incidente. La misma fórmula da el índice aparente
$R'_I$ en campo (ISO 15186-2). Como el método por intensidad *subestima*
ligeramente la potencia radiada a una sala receptora real, un **índice
modificado** $R_{I,M} = R_I + K_c$ reproduce el resultado por presión de la
ISO 10140-2; el término de adaptación $K_c$ (Anexo B) es
$10 \log_{10}(1 + S_{b2}\lambda/8V_2)$ para una sala bien definida, o el
independiente de la sala $10 \log_{10}(1 + 61,4/f)$. Para elementos pequeños, la
**diferencia de niveles normalizada por elemento** sustituye $10\lg(S_m/S)$ por
$10\lg(S_m/A_0) + 10\lg N$ ($A_0 = 10\ \text{m}^2$, $N$ unidades de elemento).

```python
import numpy as np
from phonometry import (intensity_sound_reduction, adaptation_term_kc,
                        surface_pressure_intensity_indicator)

# Nivel de sala emisora Lp1 y nivel medio de intensidad normal LIn sobre la
# superficie de medición (Sm), para un espécimen de área S; 16 bandas 1/3 octava.
lp1 = np.full(16, 85.0)
l_in = np.full(16, 40.0)
freqs = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
         1000, 1250, 1600, 2000, 2500, 3150]   # centros nominales 1/3 octava
kc = adaptation_term_kc(freqs)                  # Anexo B (B.2)
res = intensity_sound_reduction(lp1, l_in, measurement_area=12.0, area=10.0, kc=kc)
print(round(float(res.r_i[0]), 2))          # 38.21  RI = Lp1 - 6 - [LIn + 10 lg(Sm/S)]
print(round(float(res.r_i_modified[0]), 2)) # 40.29  RI,M = RI + Kc
print(res.rating.rating)                     # 38  ->  RI,w (motor ISO 717-1)

# Cualifica la superficie de medición: FpI = Lp - LIn debe quedar < 10 dB (< 6 dB
# si el lado receptor es absorbente); el índice residual de la sonda > FpI+10.
fpi = surface_pressure_intensity_indicator(np.full(16, 46.0), l_in)
print(round(float(fpi[0]), 1))               # 6.0

res.plot()   # RI medido vs curva de referencia ISO 717-1 desplazada (necesita matplotlib)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_insulation_es.svg" alt="Índice de reducción sonora por intensidad RI y el índice modificado RI,M a lo largo de las bandas de tercio de octava, con el aumento de adaptación del Anexo B sombreado entre las dos curvas" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_insulation_es_dark.svg" alt="Índice de reducción sonora por intensidad RI y el índice modificado RI,M a lo largo de las bandas de tercio de octava, con el aumento de adaptación del Anexo B sombreado entre las dos curvas" style="width:80%">

*El índice modificado $R_{I,M} = R_I + K_c$ eleva $R_I$ — más en las bandas
bajas, donde $K_c$ es mayor — de modo que una medición por intensidad reproduce
el resultado por presión de la ISO 10140-2. El índice automático solo se forma
con exactamente 16 valores de tercio de octava o 5 de octava
(`rating`/`rating_modified` son `None` en otro caso). Las subáreas barridas por
separado se combinan primero con `combine_subareas` (Fórmulas (11)-(12)); una
subárea cuya energía neta fluye de vuelta hacia el espécimen se introduce con
área negativa, aplicando la regla del signo menos de la Cláusula 6.4.6
mientras $S_m$ conserva la suma de áreas sin signo.*

### Parámetros de `intensity_sound_reduction()` / `adaptation_term_kc()`

| Parámetro | Tipo | Unidades | Rango / def. | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `lp1` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Nivel de presión de la sala emisora |
| `l_in` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Nivel de intensidad normal sobre la superficie |
| `measurement_area` | float | m² | > 0 | Área de la superficie de medición `Sm` |
| `area` | float | m² | > 0 | Área del espécimen `S` |
| `kc` | array 1D | dB | uno por banda / `None` | Término de adaptación para el índice modificado |
| `freq` | array 1D | Hz | > 0 | Frecuencias centrales (`adaptation_term_kc`) |
| `boundary_area` / `volume` | float | m² / m³ | > 0, ambos o ninguno | Sala `Sb2` / `V2` para la Fórmula (B.1) |

`intensity_sound_reduction()` devuelve un `IntensityReductionResult` (`r_i`,
`r_i_modified`, `rating`, `rating_modified`);
`intensity_element_normalized_difference()` un
`IntensityElementNormalizedResult` (`d_i_n_e`, `rating`);
`surface_pressure_intensity_indicator()` y `combine_subareas()` devuelven arrays.

## Mejora a impacto de revestimientos de suelo (ISO 16251-1)

La ISO 16251-1:2014 es un método de laboratorio para la **mejora del aislamiento
a ruido de impactos** $\Delta L$ de un revestimiento de suelo blando y de reacción
local (moqueta, PVC, linóleo). Las dos salas de ISO 10140 se sustituyen por una
pequeña placa de hormigón con apoyo elástico; una máquina de impactos normalizada
la excita y se mide el **nivel de aceleración** estructural en la cara inferior con
y sin el revestimiento. Para revestimientos de reacción local, esa diferencia de
niveles de aceleración equivale a la reducción de ruido de impactos de ISO 10140.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/floor_covering_improvement_es.svg" alt="Mejora a impacto de revestimientos de suelo ISO 16251-1: la mejora delta-L de una moqueta blanda creciendo con la frecuencia en bandas de tercio de octava de 100 Hz a 3150 Hz, con el área de mejora sombreada y el número único ponderado delta-Lw anotado" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/floor_covering_improvement_es_dark.svg" alt="Mejora a impacto de revestimientos de suelo ISO 16251-1: la mejora delta-L de una moqueta blanda creciendo con la frecuencia en bandas de tercio de octava de 100 Hz a 3150 Hz, con el área de mejora sombreada y el número único ponderado delta-Lw anotado" style="width:80%">

**Nivel de aceleración (Fórmula (1)).** $L_a = 10\lg(\langle a^2\rangle / a_0^2)$ dB,
referencia $a_0 = 10^{-6}\ \text{m/s}^2$. La **corrección de ruido de fondo
(Fórmula (2))** sigue la regla de tres ramas de ISO 10140 (sin cambio si ≥ 15 dB;
sustracción energética para 6 ≤ margen < 15 dB; el límite de 1,3 dB por debajo de
6 dB, marcado como $> \Delta L$). La mejora es la diferencia promediada por
posiciones $\Delta L = L_0 - L_1$ (Fórmulas (3)/(4)); las octavas siguen
$\Delta L_\text{oct} = -10\lg[\tfrac{1}{3}\sum 10^{-\Delta L_n/10}]$ (Fórmula (5)).

**Mejora ponderada.** $\Delta L_w$ es la reducción ponderada de ISO 717-2: la
mejora se aplica al **suelo de referencia** pesado $L_{n,r,0}$ (ISO 717-2 Tabla 4),
$L_{n,r} = L_{n,r,0} - \Delta L$, y $\Delta L_w = 78 - L_{n,r,w}$ — calculada por
`weighted_impact_improvement()`, que reutiliza el motor de valoración de
ISO 717-2. Una medición según el apartado 6.3 abarca 18 bandas (100–5000 Hz,
opcionalmente ampliadas hasta 50 Hz); la valoración se forma sobre el subrango
100–3150 Hz de cualquier espectro que lo contenga. La expresión de resultados
(apartado 8 e)) incluye además el término de adaptación espectral
$C_{I,\Delta} = C_{I,r,0} - C_{I,r}$ (ISO 717-2:2020, Fórmula (A.4)), expuesto
como `ci_delta` en el resultado y de forma independiente como
`impact_improvement_adaptation_term()`.

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import impact_improvement

freqs = [100, 125, 160, 200, 250, 315, 400, 500,
         630, 800, 1000, 1250, 1600, 2000, 2500, 3150]
bare = np.full(16, 78.0)                       # nivel de aceleración de la placa desnuda
covering = bare - np.array([0, 0, 1, 2, 4, 7, 11, 15,
                            18, 21, 23, 25, 27, 28, 29, 30])
res = impact_improvement(bare, covering, freqs)
print(res.delta_lw)   # mejora ponderada delta-Lw (ISO 717-2)
res.plot()
plt.show()
```

</details>

```python
from phonometry import impact_improvement, weighted_impact_improvement

# delta-Lw directo de un espectro de mejora (16 bandas de tercio de octava):
delta_l = [0, 0, 1, 2, 4, 7, 11, 15, 18, 21, 23, 25, 27, 28, 29, 30]
print(weighted_impact_improvement(delta_l))    # p. ej. 19 dB

# A partir de los niveles de aceleración medidos (desnudo/cubierto) y un fondo:
freqs = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
         1000, 1250, 1600, 2000, 2500, 3150]
bare_levels = [72, 73, 74, 74, 75, 75, 76, 76, 77, 77, 78, 78, 79, 79, 80, 80]
covered_levels = [b - d for b, d in zip(bare_levels, delta_l)]
bg = [40.0] * 16
res = impact_improvement(bare_levels, covered_levels, freqs, background=bg)
res.improvement       # delta-L por banda
res.delta_lw          # número único ponderado (valorado sobre el subrango 100-3150 Hz)
res.ci_delta          # término de adaptación espectral CI,delta (Fórmula (A.4))
res.limited           # bandas en el límite de medida de 1,3 dB (> delta-L)
res.octave_bands()    # (frec. de octava, delta-L_oct) vía Fórmula (5)
```

## Transmisión por flancos en laboratorio (ISO 10848)

ISO 10848:2006/2010 es el método de laboratorio que **mide** el **índice de
reducción vibracional** de unión $K_{ij}$ que la [predicción EN 12354](/phonometry/es/guides/insulation-prediction/)
toma como entrada, junto con los descriptores globales de flanco $D_{n,f}$
(aéreo) y $L_{n,f}$ (impacto). Es la contraparte de medición de la función
empírica `junction_vibration_reduction()` de esa predicción.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/flanking_transmission_es.svg" alt="Índice de reducción vibracional de unión Kij ISO 10848 creciendo entre 100 Hz y 5000 Hz en tercios de octava para una unión rígida en T de dos paredes pesadas, con el Kij medio de un solo número entre 200 y 1250 Hz en línea discontinua" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/flanking_transmission_es_dark.svg" alt="Índice de reducción vibracional de unión Kij ISO 10848 creciendo entre 100 Hz y 5000 Hz en tercios de octava para una unión rígida en T de dos paredes pesadas, con el Kij medio de un solo número entre 200 y 1250 Hz en línea discontinua" style="width:80%">

**Índice de reducción vibracional (Fórmula (13)).**
$K_{ij} = \overline{D}_{v,ij} + 10\lg\!\big(l_{ij} / \sqrt{a_i a_j}\big)$ dB, a
partir de la diferencia de nivel de velocidad promediada en dirección
$\overline{D}_{v,ij} = \tfrac{1}{2}(D_{v,ij} + D_{v,ji})$ (Fórmula (11), que hace
$K_{ij}$ simétrico), la longitud de unión de arista común $l_{ij}$ y las
**longitudes de absorción equivalentes**
$a_j = 2.2\pi^2 S_j /(T_{s,j} c_0)\sqrt{f_\text{ref}/f}$ (Fórmula (12),
$f_\text{ref} = 1000$ Hz). Para elementos ligeros y bien amortiguados
$a_j = S_j / l_0$ ($l_0 = 1$ m) y la Fórmula (13) se reduce a la Fórmula (14)
simplificada. El **factor de pérdidas total** asociado es $\eta = 2.2/(f T_s)$.

**Descriptores globales.** $D_{n,f} = L_1 - L_2 - 10\lg(A/A_0)$ (Fórmula (4),
aéreo) y $L_{n,f} = L_2 + 10\lg(A/A_0)$ (Fórmula (5), máquina de impactos),
$A_0 = 10\ \text{m}^2$; sus números únicos $D_{n,f,w}$ / $L_{n,f,w}$ reutilizan
los motores de ISO 717. El número único $\overline{K}_{ij}$ es la media
aritmética entre 200 y 1250 Hz en tercios de octava, o entre 125 y 1000 Hz en
bandas de octava (Anexo A).

**Validez.** $K_{ij}$ se apoya en una simplificación de análisis estadístico de
energía: `strong_coupling_satisfied()` comprueba la desigualdad de la
Fórmula (15), y —para las uniones pesadas de la Parte 4— `modal_density()`,
`band_mode_count()` y `modal_overlap_factor()` (Fórmulas (5)/(4)/(6)) cuantifican
dónde el número de modos es demasiado bajo para que $K_{ij}$ sea fiable. Pasa el
factor de solapamiento modal por banda a
`vibration_reduction_index(..., modal_overlap=M)`: las bandas con $M < 0.25$ se
marcan en `result.bracketed` y quedan excluidas del número único
$\overline{K}_{ij}$, como exige la Cláusula 9 de la Parte 4.
Como ISO 10848 no contiene ningún ejemplo numérico resuelto, la conformidad se
ancla en identidades de forma cerrada ($K_{ij}$ simplificado, $a_j$ a
$f_\text{ref}$, $\eta$).

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import vibration_reduction_index

freqs = [100, 125, 160, 200, 250, 315, 400, 500, 630,
         800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
# Diferencia de nivel de velocidad promediada en dirección de una unión en T (dB):
dv = np.array([4.5, 4.8, 5.2, 5.6, 6.0, 6.5, 7.0, 7.6, 8.1, 8.7,
               9.2, 9.8, 10.3, 10.9, 11.4, 11.9, 12.3, 12.7])
res = vibration_reduction_index(
    dv, junction_length=4.0, area_i=12.0, area_j=10.0, frequency=freqs,
    structural_reverberation_time_i=0.35, structural_reverberation_time_j=0.40,
)
print(res.single_number)   # Kij medio entre 200 y 1250 Hz (Anexo A)
res.plot()
plt.show()
```

</details>

```python
import numpy as np
from phonometry import (
    direction_averaged_level_difference, vibration_reduction_index,
    normalized_flanking_level_difference, modal_overlap_factor,
)

freqs = [200, 250, 315, 400, 500, 630, 800, 1000, 1250]
lij, s_i, s_j = 4.0, 12.0, 10.0     # longitud de unión (m), áreas de elemento (m^2)
ts = np.linspace(0.30, 0.10, 9)     # tiempo de reverberación estructural Ts (s)
dv_ij = [5.6, 6.0, 6.5, 7.0, 7.6, 8.1, 8.7, 9.2, 9.8]    # elemento i excitado (dB)
dv_ji = [6.4, 6.8, 7.3, 7.8, 8.4, 8.9, 9.5, 10.0, 10.6]  # elemento j excitado (dB)

# Kij desde ambas direcciones de excitación (simétrico por el promedio direccional):
dbar = direction_averaged_level_difference(dv_ij, dv_ji)
res = vibration_reduction_index(dbar, lij, s_i, s_j, frequency=freqs,
                                structural_reverberation_time_i=ts,
                                structural_reverberation_time_j=ts)
res.k_ij           # Kij por banda (Fórmula (13))
res.single_number  # Kij medio entre 200 y 1250 Hz, o None sin ese conjunto de bandas
res.octave_bands() # Kij en octavas (su número único promedia 125-1000 Hz)

# Descriptor global aéreo de flanco y una comprobación de validez de la Parte 4:
dnf = normalized_flanking_level_difference(np.full(9, 75.0), np.full(9, 42.0),
                                           absorption_area=np.full(9, 12.0))
m = modal_overlap_factor(s_i, critical_frequency=85.0,
                         structural_reverberation_time=ts)
res_m = vibration_reduction_index(dbar, lij, s_i, s_j, frequency=freqs,
                                  modal_overlap=m)   # bandas con M < 0.25 acotadas
res_m.bracketed    # marcas por banda; las bandas acotadas salen del número único
```

## Referencias

- Hopkins, C. (2007). *Sound insulation*. Butterworth-Heinemann.
  ISBN 978-0-7506-6526-1.
  [doi:10.4324/9780080550473](https://doi.org/10.4324/9780080550473).
  La monografía de referencia para la medición del aislamiento en
  laboratorio, la transmisión por flancos y el índice de reducción de
  vibraciones.
- Vigran, T. E. (2008). *Building acoustics*. CRC Press.
  ISBN 978-0-415-42853-8.
  [doi:10.1201/9781482266016](https://doi.org/10.1201/9781482266016).
  La teoría de transmisión de construcciones simples y dobles que cuantifican
  los índices de laboratorio.

---

**Normas.** ISO 10140-2:2010, ISO 10140-3:2010 e ISO 10140-4:2010 — los R y Ln
de laboratorio con la corrección de ruido de fondo; ISO 15186-1:2000 e
ISO 15186-2:2003 — el índice de reducción sonora por intensidad $R_I$, su forma
modificada por $K_c$ y la diferencia de niveles normalizada por elemento
(laboratorio y campo); ISO 16251-1:2014 — el método de laboratorio en maqueta
pequeña para la mejora a impactos $\Delta L$ de revestimientos de suelo, con
$\Delta L_w$ vía el suelo de referencia de ISO 717-2; ISO 10848-1:2006,
ISO 10848-2:2006, ISO 10848-3:2006 e ISO 10848-4:2010 — la medición en
laboratorio de la transmisión por flancos: el índice de reducción vibracional
$K_{ij}$, la longitud de absorción equivalente, los descriptores de flanco
normalizados $D_{n,f}$ / $L_{n,f}$ y las comprobaciones de validez por
solapamiento modal que alimentan la predicción EN 12354.

## Véase también

- [Medición del aislamiento en campo e índices](/phonometry/es/guides/insulation-field/):
  las mediciones aéreas, de impactos y de fachada en el edificio, sus índices
  de un solo número y su incertidumbre.
- [Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/):
  el modelo de flancos que consume los $R$, $L_n$ y $K_{ij}$ de laboratorio.
- [Potencia sonora](/phonometry/es/guides/sound-power/) — los métodos de `LW` que comparten
  la maquinaria del área de absorción de la sala receptora.
- Referencia de la API: [`building.lab_insulation`](/phonometry/es/reference/api/building/lab-insulation/), [`building.intensity_insulation`](/phonometry/es/reference/api/building/intensity-insulation/) y [`building.flanking_transmission`](/phonometry/es/reference/api/building/flanking-transmission/).
