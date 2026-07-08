---
title: "Propagación del sonido en exteriores"
description: "Absorción atmosférica del sonido (ISO 9613-1) y método general ISO 9613-2 para la propagación del sonido en exteriores desde una fuente puntual: divergencia geométrica, absorción atmosférica, efecto del suelo, apantallamiento por barreras y corrección meteorológica, con un desglose por términos de la atenuación en bandas de octava."
---

Predecir el ruido que una fuente lejana entrega a un receptor en exteriores es
un ejercicio de contabilidad: se parte de la **potencia sonora** de la fuente y
se resta, banda a banda, cada mecanismo que atenúa el sonido en su camino —la
divergencia esférica, el propio aire, el suelo y cualquier barrera intermedia—.
Esta página cubre las dos partes de la ISO 9613 que proporcionan esos términos:
la **ISO 9613-1**, el coeficiente de absorción atmosférica de tono puro
$\alpha$, y la **ISO 9613-2**, el método general que combina $\alpha$ con la
divergencia, el suelo y el apantallamiento en una predicción por bandas de
octava. El coeficiente atmosférico también cierra el ciclo con la acústica de
salas, porque la ISO 354 remite por completo su coeficiente de atenuación de
potencia del aire $m$ a $\alpha$.

## 1. Absorción atmosférica (ISO 9613-1)

El aire no es un medio sin pérdidas. Un tono en propagación cede energía a la
viscosidad de cizalla y a la conducción de calor —las pérdidas *clásicas y
rotacionales*, que crecen como $f^2$— y a la **relajación vibracional** de las
moléculas de oxígeno y nitrógeno, cada una un depósito de energía que resuena
cerca de una frecuencia de relajación dependiente de la humedad y la
temperatura. La ISO 9613-1:1993, Ec. (5) reúne todo esto en el coeficiente de
atenuación de tono puro $\alpha$, en decibelios por metro:

$$
\alpha = 8.686\ f^2 \Big[ 1.84\times10^{-11} \big(p_a/p_r\big)^{-1} \big(T/T_0\big)^{1/2}
       + \big(T/T_0\big)^{-5/2} \big( 0.01275\ \tfrac{e^{-2239.1/T}}{f_{rO} + f^2/f_{rO}}
       + 0.1068\ \tfrac{e^{-3352.0/T}}{f_{rN} + f^2/f_{rN}} \big) \Big],
$$

con las frecuencias de relajación del oxígeno y el nitrógeno $f_{rO}$, $f_{rN}$
(Ec. (3)/(4)), las condiciones de referencia $T_0 = 293.15$ K y
$p_r = 101.325$ kPa (apartado 4.2), y la concentración molar de vapor de agua $h$
obtenida de la humedad relativa mediante la conversión psicrométrica del anexo B.
Dominan la forma dos rasgos: a baja frecuencia $\alpha \propto f^2$, por lo que
sube con fuerza; y cerca de cada frecuencia de relajación el término
correspondiente alcanza un máximo y decae. Entre ambos, $\alpha$ crece unas dos
décadas de 50 Hz a 10 kHz y —al fijar la humedad la $f_{rO}$— barrer la humedad
desplaza un pico de relajación por la banda, así que el aire más seco no siempre
es el que menos absorbe.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/air_absorption_alpha_es.png" alt="Coeficiente de atenuación atmosférica de tono puro alfa de la ISO 9613-1 en dB/km frente a la frecuencia en ejes log-log, para cuatro combinaciones de temperatura y humedad, mostrando el crecimiento f-cuadrado en baja frecuencia y el decaimiento de relajación dependiente de la humedad" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/air_absorption_alpha_es_dark.png" alt="Coeficiente de atenuación atmosférica de tono puro alfa de la ISO 9613-1 en dB/km frente a la frecuencia en ejes log-log, para cuatro combinaciones de temperatura y humedad, mostrando el crecimiento f-cuadrado en baja frecuencia y el decaimiento de relajación dependiente de la humedad" style="width:80%">

*La curva seca de 20 °C / 10 % absorbe más a frecuencias medias, pero las curvas
húmedas la superan por debajo de ~200 Hz: la firma de la relajación.*

```python
import numpy as np
from phonometry import air_attenuation, air_attenuation_m

bands = [63, 125, 250, 500, 1000, 2000, 4000, 8000]   # centros de banda de octava [Hz]

# Coeficiente de atenuación de tono puro alpha [dB/m] a 20 °C, 50 % HR, una atmósfera
alpha = air_attenuation(bands, temperature=20.0, relative_humidity=50.0)
print(np.round(alpha * 1000.0, 2))          # en dB/km, como tabula la Tabla 1
# [  0.12   0.44   1.31   2.73   4.66   9.89  29.67 105.29]

# Reproduce exactamente una celda de la Tabla 1 de la ISO 9613-1 (10 °C, 70 %, 1 kHz)
cell = air_attenuation(1000.0, 10.0, 70.0, exact_midband=True) * 1000.0
print(round(float(cell), 2))                # 3.66  (dB/km, Tabla 1)

# Alimenta condiciones reales al coeficiente de atenuación de potencia m [1/m] de la ISO 354
m = air_attenuation_m([1000.0, 4000.0], temperature=20.0, relative_humidity=50.0)
print(np.round(m, 5))                        # [0.00107 0.00683]
```

`air_attenuation` devuelve dB/m (la Tabla 1 imprime dB/km, es decir $\times 1000$);
está totalmente vectorizada sobre `frequencies`, con temperatura, humedad y
presión escalares. Pasar `exact_midband=True` ajusta cada frecuencia solicitada a
la frecuencia central exacta de tercio de octava $f_m = 1000 \cdot 10^{k/10}$
(Ec. (6), Nota 5) empleada para calcular la Tabla 1, de modo que la biblioteca
reproduce cada punto tabulado con menos del 0,4 % —la propia precisión de tres
cifras significativas del estándar, muy dentro de su exactitud declarada de
$\pm 10$ % (apartado 7.1)—. Las entradas fuera de los rangos tabulados
(−20…+50 °C, 10…100 % HR, 50…10 000 Hz, o por encima de la envolvente de validez
de 200 kPa) siguen calculándose pero emiten una `AtmosphericAbsorptionWarning`;
las entradas no físicas (frecuencia no positiva, humedad fuera de 0…100 %,
temperatura bajo el cero absoluto) lanzan `ValueError`. `air_attenuation_m`
compone $\alpha$ con la conversión de la ISO 354 $m = \alpha/(10 \lg e)$, de modo
que quien use la ISO 354 puede alimentar condiciones atmosféricas reales
directamente a `absorption_area` / `absorption_coefficient` en vez de introducir
$m$ a mano.

### Parámetros de `air_attenuation()` / `air_attenuation_m()`

| Parámetro | Tipo / forma | Unidades | Rango / def. | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `frequencies` | escalar o array 1D | Hz | > 0 | Vectorizado; 50–10 000 Hz tabulado |
| `temperature` | float | °C | def. `20.0` | −20…+50 tabulado; fuera avisa |
| `relative_humidity` | float | % | def. `50.0` | 10…100 tabulado; se admite `[0, 100]` |
| `pressure` | float | kPa | def. `101.325` | ≤ 200 válido (apartado 7); por encima avisa |
| `exact_midband` | bool | — | def. `False` | Ajusta a $f_m = 1000\cdot10^{k/10}$ (reproduce la Tabla 1) |

`air_attenuation` devuelve $\alpha$ en dB/m; `air_attenuation_m` devuelve
$m = \alpha/(10 \lg e)$ en 1/m para la ISO 354.

## 2. Método general de cálculo (ISO 9613-2)

La ISO 9613-2:1996 predice el nivel por bandas de octava en un receptor situado
**a favor del viento** respecto de una fuente puntual (o bajo la inversión
térmica moderada equivalente, apartado 5). El nivel continuo equivalente a favor
del viento es

$$
L_{fT}(DW) = L_W + D_c - A, \qquad A = A_{div} + A_{atm} + A_{gr} + A_{bar} + A_{misc},
$$

(Ec. (3)/(4)) donde $L_W$ es el nivel de potencia sonora por bandas de octava,
$D_c$ la corrección de directividad (índice de directividad más un índice de
ángulo sólido $D_\Omega$) y $A$ la atenuación total. La biblioteca implementa los
cuatro términos generales del apartado 7; el $A_{misc}$ informativo (vegetación,
zonas industriales, edificación; anexo A) y las reflexiones en obstáculos
verticales (apartado 7.5) **no están implementados** —el estándar los trata como
informativos y se dejan a criterio del usuario—.

La geometría del término de apantallamiento fija el vocabulario: el borde de
difracción divide la distancia fuente-receptor en $d_{ss}$ y $d_{sr}$, y el
exceso de recorrido sobre el borde es $z = d_{ss} + d_{sr} - d$:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_outdoor_geometry_es.svg" alt="Geometría fuente-barrera-receptor de la ISO 9613-2: una fuente puntual a altura hs, una barrera cuyo borde superior divide el recorrido en dss y dsr, y un receptor a altura hr, con el rayo directo bloqueado y el rayo difractado sobre el borde, la diferencia de camino z y la fórmula de Dz" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_outdoor_geometry_es_dark.svg" alt="Geometría fuente-barrera-receptor de la ISO 9613-2: una fuente puntual a altura hs, una barrera cuyo borde superior divide el recorrido en dss y dsr, y un receptor a altura hr, con el rayo directo bloqueado y el rayo difractado sobre el borde, la diferencia de camino z y la fórmula de Dz" style="width:92%">

### Los cuatro términos de atenuación

* **Divergencia geométrica** $A_{div} = 20 \log_{10}(d/d_0) + 11$ dB, $d_0 = 1$ m
  (Ec. (7)): expansión esférica desde una fuente puntual. Exactamente 51 dB a
  100 m, +6 dB por cada duplicación de la distancia. El $+11$ ($= 10 \lg 4\pi$)
  fija el nivel a la distancia de referencia de 1 m.
* **Absorción atmosférica** $A_{atm} = \alpha\ d$ (Ec. (8)) con $\alpha$ el
  coeficiente de la ISO 9613-1 —despreciable a baja frecuencia, dominante a 8 kHz
  en recorridos largos—. Las funciones de la ISO 9613-2 usan por defecto 20 °C y
  una humedad relativa del 70 % —una de las atmósferas de referencia que la norma
  tabula en su Tabla 2—, mientras que `air_attenuation` usa por defecto el 50 %
  habitual de la ISO 9613-1.
* **Efecto del suelo** $A_{gr} = A_s + A_r + A_m$ (Ec. (9)) suma una región
  fuente, receptor y media, cada una a partir de las funciones $a'/b'/c'/d'$ de
  la Tabla 3 y su factor de suelo $G$ (0 = duro/reflectante, 1 =
  poroso/absorbente). Un $A_{gr}$ **negativo** es una *ganancia* neta por la
  reflexión constructiva en el suelo.
* **Apantallamiento** por una barrera es la pérdida por inserción por difracción
  $D_z = 10 \log_{10}\big[ 3 + (C_2/\lambda)\ C_3\ z\ K_{met} \big]$ (Ec. (14)),
  limitada a 20 dB (un borde) o 25 dB (doble borde). Para una barrera de borde
  superior, el efecto del suelo del recorrido apantallado se integra en él,
  $A_{bar} = D_z - A_{gr} \ge 0$ (Ec. (12), Nota 13); para una barrera lateral
  $A_{bar} = D_z$ y se conserva el término del suelo (Ec. (13)).

`outdoor_propagation_attenuation` ensambla los cuatro términos en un resultado
`OutdoorAttenuation` cuyos arrays por banda suman, banda a banda, a `a_total`, de
modo que las contribuciones de divergencia, atmosférica, suelo y barrera quedan
separables. El desglose apilado hace evidente el carácter frecuencial: la barrera
ayuda más a alta frecuencia (longitud de onda corta) hasta saturar en el límite,
la absorción atmosférica solo muerde a 8 kHz y la caída del suelo vive en las
bandas medias.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/outdoor_attenuation_breakdown_es.png" alt="Desglose por bandas de octava de la atenuación ISO 9613-2 como barra apilada de Adiv, Aatm, Agr y Abar con el total A superpuesto, para un recorrido de 200 m sobre suelo poroso con una barrera de 4 m" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/outdoor_attenuation_breakdown_es_dark.png" alt="Desglose por bandas de octava de la atenuación ISO 9613-2 como barra apilada de Adiv, Aatm, Agr y Abar con el total A superpuesto, para un recorrido de 200 m sobre suelo poroso con una barrera de 4 m" style="width:80%">

```python
import numpy as np
from phonometry import (
    Barrier, outdoor_propagation_attenuation, predicted_receiver_level,
)

bands = [63, 125, 250, 500, 1000, 2000, 4000, 8000]   # centros de banda de octava [Hz]

# Fuente y receptor a 1.5 m de altura, separados 200 m sobre suelo poroso
# (G = 1), apantallados a media distancia por una barrera que eleva el recorrido
# sobre su borde superior (dss = dsr ~ 101 m). La geometría alimenta las
# ecuaciones de diferencia de recorrido.
barrier = Barrier(source_to_edge=101.0, edge_to_receiver=101.0)
att = outdoor_propagation_attenuation(
    200.0, source_height=1.5, receiver_height=1.5, frequencies=bands,
    ground_source=1.0, ground_middle=1.0, ground_receiver=1.0,
    barrier=barrier, temperature=15.0, humidity=70.0,
)
print(np.round(att.a_div, 1))     # [57. 57. 57. 57. 57. 57. 57. 57.]  divergencia
print(np.round(att.a_gr, 2))      # [-4.65  2.34 13.79  9.76  1.3  -0.   -0.   -0.  ]
print(np.round(att.a_bar, 2))     # [13.78  8.89  0.    6.69 18.01 20.   20.   20.  ]
print(np.round(att.a_total, 1))   # [66.2 68.3 71.  73.9 77.1 78.8 82.3 96. ]

# Nivel predicho en el receptor a partir de una potencia sonora por bandas Lw = 95 dB
lw = np.full(len(bands), 95.0)
lp = predicted_receiver_level(
    lw, 200.0, 1.5, 1.5, bands, 1.0, 1.0, 1.0,
    barrier=barrier, temperature=15.0, humidity=70.0,
)
print(np.round(lp, 1))            # [28.8 26.7 24.  21.1 17.9 16.2 12.7 -1. ]
```

`predicted_receiver_level` compone $L_{fT}(DW) = L_W + D_c - A$ con
$D_c = $ `directivity_index` $+ $ `d_omega`. Pasa `c0=` para restar la corrección
meteorológica $C_{met}$ (Ec. (21)/(22)) banda a banda y obtener una media a largo
plazo —ten en cuenta que el estándar aplica $C_{met}$ al nivel ponderado A, así
que la forma por bandas aquí es una **comodidad**, no una lectura literal del
apartado 8—.

### Suelo: el método alternativo ponderado A

Cuando solo importa el nivel ponderado A en el receptor y el sonido viaja sobre
suelo poroso o mayoritariamente poroso (y no es un tono puro), el 7.3.2 ofrece
una forma cerrada más simple $A_{gr} = 4.8 - \frac{2 h_m}{d}\left(17 + \frac{300}{d}\right) \ge 0$
(Ec. (10), los resultados negativos se recortan a cero), acompañada del índice de
ángulo sólido $D_\Omega$ (Ec. (11)) que debe entonces sumarse a $D_c$. Se exponen
como `ground_attenuation_alternative` y `directivity_omega`, pero **no se conectan
automáticamente** en `outdoor_propagation_attenuation` (que siempre usa el método
general por regiones del 7.3.1); combínalos a mano cuando proceda el método
alternativo.

```python
from phonometry import (
    ground_attenuation_alternative, directivity_omega, meteorological_correction,
)

# Término de suelo alternativo (altura media del recorrido hm = 2 m, d = 200 m)
print(round(ground_attenuation_alternative(200.0, 2.0), 2))          # 4.43 dB
# Su índice de ángulo sólido asociado (súmalo a Dc al usar la Ec. (10))
print(round(directivity_omega(1.5, 1.5, 200.0), 2))                  # 3.01 dB
# Corrección meteorológica a largo plazo (C0 = 2 dB) a restar de LAT(DW)
print(round(meteorological_correction(200.0, 1.5, 1.5, 2.0), 2))     # 1.7 dB
```

### `Barrier` y el término de apantallamiento

La clase `Barrier` describe la geometría de difracción directamente, que es el
ajuste más limpio a las Ec. (14)/(16)/(17). La difracción simple (una pantalla
delgada) deja `edge_separation=None` ($C_3 = 1$); dar la separación de bordes `e`
selecciona la difracción doble (barrera gruesa) con el factor $C_3$ de la
Ec. (15) y el límite de 25 dB. `ground_reflections_by_image=True` cambia $C_2$ de
20 a 40 (reflexiones tratadas por fuentes imagen) y `lateral=True` selecciona la
difracción por borde vertical (Ec. (13), $K_{met}=1$, se conserva el término del
suelo).

### Parámetros de `outdoor_propagation_attenuation()`

| Parámetro | Tipo / forma | Unidades | Rango / def. | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `distance` | float | m | > 0 | Distancia fuente–receptor en línea recta $d$ |
| `source_height` / `receiver_height` | float | m | ≥ 0 | $h_s$, $h_r$ sobre el suelo |
| `frequencies` | array 1D | Hz | def. 8 octavas 63–8000 | `DEFAULT_FREQUENCIES` |
| `ground_source` / `ground_middle` / `ground_receiver` | float | — | `[0, 1]`, def. `0.0` | Factor de suelo $G$ (0 duro, 1 poroso) |
| `barrier` | `Barrier` o None | — | def. `None` | Obstáculo de apantallamiento |
| `temperature` / `humidity` / `pressure` | float | °C / % / kPa | 20 / 70 / 101.325 | Pasados a $A_{atm}$ |
| `projected_distance` | float o None | m | def. $\sqrt{d^2-(h_s-h_r)^2}$ | $d_p$ proyectada sobre el suelo |

Devuelve un `OutdoorAttenuation` con `a_div`, `a_atm`, `a_gr`, `a_bar`,
`a_total` y `d_omega`, todos un valor por banda.

### Campos de `Barrier`

| Campo | Tipo | Unidades | Def. | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `source_to_edge` | float | m | — | $d_{ss}$, fuente al primer borde |
| `edge_to_receiver` | float | m | — | $d_{sr}$, (último) borde al receptor |
| `parallel_distance` | float | m | `0.0` | Componente $a$ paralela al borde |
| `edge_separation` | float o None | m | `None` | $e$; si se da ⇒ difracción doble (límite 25 dB) |
| `ground_reflections_by_image` | bool | — | `False` | `True` ⇒ $C_2 = 40$ |
| `lateral` | bool | — | `False` | `True` ⇒ difracción por borde vertical (Ec. (13)) |

La exactitud declarada del método es de $\pm 1$ a $\pm 3$ dB para ruido de banda
ancha hasta 1000 m (Tabla 5). Consulta la página de [Teoría](/phonometry/es/reference/theory/)
para la derivación completa, la [guía de Acústica de salas y edificación](/phonometry/es/guides/room-acoustics/)
para cómo $\alpha$ alimenta la ISO 354, y la [guía de Niveles](/phonometry/es/guides/levels/)
para la exposición al ruido en el trabajo (ISO 9612) que consume niveles
ponderados A.
