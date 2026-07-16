---
title: "Ruido estructural instalado (EN 12354-5)"
description: "La predicción según EN 12354-5:2009 del nivel de presión sonora en un recinto receptor por equipos de servicio del edificio que inyectan ruido estructural: el término de acoplamiento D_C a partir de las movilidades de fuente y receptor (Fórmula 19b-e), la potencia instalada L_Ws,inst = L_Ws,c − D_C (Fórmula 18b) y el nivel de presión normalizado por camino con su total energético (Fórmulas 18a/17)."
---

La **EN 12354-5:2009** predice el nivel de presión sonora en un recinto receptor
causado por equipos de servicio del edificio (bombas, ventiladores, ascensores,
instalaciones de agua) que inyectan **ruido estructural** en el edificio. Cierra
la cadena de vibroacústica estructural: la fuente se describe por su nivel de
potencia sonora estructural característica `L_Ws,c`, derivado de la medición
sobre placa receptora de EN 15657 mediante la conversión de las Fórmulas
(15)/(17) y una corrección de movilidad (**no** el nivel bruto inyectado en la
placa; véase [EN 15657](/phonometry/es/guides/structure-borne-power/)); las
movilidades puntuales de fuente y receptor fijan cuánta potencia se acopla
realmente a la estructura, y la transmisión del edificio la lleva al recinto
receptor. La corrección de movilidad del Anexo I,
`installed_power_from_reception_plate`, refiere el nivel característico de
placa receptora `L_Ws,n` al receptor real,
`L_Ws,inst = L_Ws,n + 10 lg(Y_∞,i / Y_∞,rec)` con `Y_∞,rec = 5·10⁻⁶ m/(N·s)`;
con la movilidad de la fuente en su lugar da `L_Ws,c` (Anexo I.3, Tabla I.8).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/installed_structure_borne_es.svg" alt="La cascada de EN 12354-5 por banda de octava: potencia característica, potencia instalada tras el término de acoplamiento, niveles de presión sonora por camino y su total energético" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/installed_structure_borne_es_dark.svg" alt="La cascada de EN 12354-5 por banda de octava: potencia característica, potencia instalada tras el término de acoplamiento, niveles de presión sonora por camino y su total energético" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import building

# Potencia característica EN 15657 y movilidades puntuales ilustrativas.
bands = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
lws_c = np.array([78.0, 82.0, 84.0, 81.0, 77.0, 72.0, 66.0])
ys = (2e-4 + 1e-4j) * (bands / 250.0)        # movilidad de la fuente
yi = (3e-5 + 1e-5j) * np.ones_like(bands)    # movilidad del receptor
dc = np.array([float(building.coupling_term(a, b)) for a, b in zip(ys, yi)])

# Dos vías de transmisión: el forjado excitado y una pared de flanco.
paths = [
    {"adjustment_term": 6.0, "element_area": 12.0,
     "flanking_reduction_index": np.linspace(44.0, 62.0, 7)},
    {"adjustment_term": 7.0, "element_area": 9.0,
     "flanking_reduction_index": np.linspace(46.0, 64.0, 7)},
]
res = building.installed_source_prediction(lws_c, dc, paths, frequencies=bands)
res.plot()   # potencia característica e instalada, niveles por vía y el total
plt.show()
```

</details>

## 1. Acoplamiento y potencia instalada

Solo parte de la potencia característica se inyecta en el elemento soporte; la
pérdida es el **término de acoplamiento** `D_C` (siempre positivo), fijado para
una excitación puntual por la movilidad de la fuente `Y_s` y la del receptor
`Y_i` (Fórmula 19b):

$$
D_{C,i} = 10\lg\frac{|Y_s + Y_i|^2}{|Y_s|\,\mathrm{Re}\{Y_i\}},
$$

que se reduce a `10 lg(|Y_s|/Re{Y_i})` para una **fuente de fuerza** (movilidad
de fuente alta, Fórmula 19c) y a `−10 lg(|Y_s|·Re{Z_i})` para una **fuente de
velocidad** (movilidad de fuente baja, Fórmula 19d); un soporte elástico añade su
movilidad de transferencia `Y_k` dentro del módulo (Fórmula 19e). El nivel de
potencia **instalada** es entonces (Fórmula 18b) `L_Ws,inst = L_Ws,c − D_C`.

```python
from phonometry import building

# Una fuente casi de fuerza (Y_s >> Y_i) sobre un forjado de hormigón:
dc = building.coupling_term(2e-4 + 1e-4j, 3e-5 + 1e-5j)
print(round(float(dc), 2))                                          # ~8.5 dB
print(round(float(building.installed_structure_borne_power_level(82.0, dc)), 1))  # L_Ws instalada
```

## 2. Transmisión al recinto receptor

Las partes 1 y 2 de EN 12354 tratan recintos excitados por vía aérea y por la
máquina de impactos normalizada; la parte 5 cubre las fuentes que sacuden el
edificio *directamente*: bombas, ventiladores, ascensores, bañeras de
hidromasaje, cisternas y las conducciones que las anclan a paredes y forjados.
Una vez que la potencia instalada está en la estructura, varios elementos
radian al recinto receptor: el propio elemento excitado y cada elemento al
que la vibración llega a través de las uniones. Cada par elemento
excitado/elemento radiante `i→j` es una vía de transmisión con su propio
término de ajuste y su índice de flancos:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_installed_paths_es.svg" alt="Vías de instalación EN 12354-5: una bomba sobre apoyos resilientes inyecta potencia estructural en el forjado, el forjado excitado radia al recinto receptor de abajo, una segunda vía recorre el forjado hasta la pared de flanco, y la cascada de predicción va de la potencia característica al nivel de presión sonora normalizado" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_installed_paths_es_dark.svg" alt="Vías de instalación EN 12354-5: una bomba sobre apoyos resilientes inyecta potencia estructural en el forjado, el forjado excitado radia al recinto receptor de abajo, una segunda vía recorre el forjado hasta la pared de flanco, y la cascada de predicción va de la potencia característica al nivel de presión sonora normalizado" style="width:92%">

Cada camino de transmisión `i→j` da un nivel de presión sonora normalizado a
partir de la potencia instalada, el término de ajuste estructura-a-aéreo `D_sa`,
el índice de reducción sonora de flancos `R_ij,ref` (EN 12354-1) y el área del
elemento (Fórmula 18a):

$$
L_{n,s,ij} = L_{Ws,\mathrm{inst},i} - D_{sa,i} - R_{ij,\mathrm{ref}}
             - 10\lg\frac{S_i}{S_0} - 10\lg\frac{A_0}{4},
$$

con `S₀ = A₀ = 10 m²`, y los caminos se combinan energéticamente (Fórmula 17):

```python
import numpy as np
from phonometry import building

bands = np.array([250.0, 500.0, 1000.0])
res = building.installed_source_prediction(
    characteristic_power_level=np.array([80.0, 82.0, 78.0]),
    coupling_term=np.array([9.0, 10.0, 11.0]),
    paths=[
        {"adjustment_term": 5.0,
         "flanking_reduction_index": np.array([50.0, 52.0, 55.0]), "element_area": 12.0},
        {"adjustment_term": 6.0,
         "flanking_reduction_index": np.array([52.0, 54.0, 57.0]), "element_area": 8.0},
    ],
    frequencies=bands,
)
print(np.round(res.total_level, 1))      # total L_n,s por banda
print(round(res.overall_level, 1))       # nivel sumado en bandas [dB]
```

El `InstalledSourceResult` transporta los niveles por camino, el total por banda,
el nivel de potencia instalada y `.overall_level`, y su `.plot()` dibuja toda la
cascada.

## Referencias

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3.ª ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  El acoplamiento de movilidades fuente-receptor y la transmisión estructural
  a través de uniones tras el término de acoplamiento y el modelo de vías.

## Normas

EN 12354-5:2009, *Building acoustics — Estimation of acoustic
performance of buildings from the performance of elements — Part 5: Sound levels
due to service equipment*: el término de acoplamiento (cláusula 4.4.3, Fórmulas
19a-19e), el nivel de potencia estructural instalada (Fórmula 18b), el término de
ajuste estructura-a-aéreo (cláusula 4.4.4, Fórmulas 20a/20b) y el nivel de presión
sonora normalizado por camino y su combinación energética (Fórmulas 18a, 17). La
conformidad se ancla en el límite de fuente de fuerza del término de
acoplamiento y en los ejemplos resueltos del propio Anexo I de la norma: la
bañera de hidromasaje de I.2 (Tabla I.6a: corrección de movilidad y camino 11)
y la cisterna de I.3 (Tablas I.8/I.9: conversión de la fuente, los cuatro
caminos de transmisión, el total de la Fórmula 17 y su cierre a 29 dB(A)),
dentro del redondeo de ±0,15 dB de los intermedios impresos con un decimal.
`D_sa` y `R_ij,ref` son entradas (de medición / EN 12354-1 / Anexos D y F).

## Véase también

- Referencia de la API: [`building.installed_structure_borne`](/phonometry/es/reference/api/building/installed-structure-borne/).
