---
title: "Predicción del tiempo de reverberación (Sabine, Arau)"
description: "Predicción del tiempo de reverberación de una sala a partir de su volumen, áreas de contorno y absorción de las superficies con cinco modelos de acústica estadística — Sabine, Eyring (Norris-Eyring), Millington-Sette, Fitzroy y Arau-Puchades — incluyendo el término de absorción del aire y los modelos para una distribución de absorción no uniforme."
---

El **tiempo de reverberación** $T$ — el tiempo que tarda el nivel de energía
sonora en caer 60 dB tras detenerse la fuente — se predice aquí a partir del
**volumen** de una sala, sus **áreas de contorno** y los **coeficientes de
absorción** de sus superficies, mediante las fórmulas clásicas de la acústica
estadística. Es la contraparte de diseño del tiempo de reverberación *medido* de
[Acústica de salas](/phonometry/es/guides/room-acoustics/) (ISO 3382) y
complementa el modelo de EN 12354-6 de
[Absorción sonora en recintos](/phonometry/es/guides/enclosed-space-absorption/),
que especializa la misma física a la cláusula 4 de esa norma.

phonometry ofrece cinco modelos, ordenados según cuánto tienen en cuenta una
distribución de absorción **no uniforme**:

| Modelo | Término de absorción en $T = k\,V / (\text{término} + 4mV)$ | Idóneo para |
|:---|:---|:---|
| **Sabine** | $A = \sum_i S_i\alpha_i$ | absorción baja y uniforme |
| **Eyring** (Norris-Eyring) | $-S\ln(1-\bar\alpha)$ | absorción fuerte y uniforme |
| **Millington-Sette** | $-\sum_i S_i\ln(1-\alpha_i)$ | unas pocas superficies muy absorbentes |
| **Fitzroy** | media **aritmética** ponderada por área de tres tiempos de Eyring axiales | salas anisótropas |
| **Arau-Puchades** | media **geométrica** ponderada por área de los mismos tres | salas anisótropas (recomendado por el autor) |

con la constante de Sabine $k = 24\ln 10 / c_0$ (así $k = 0{,}161$ para
$c_0 = 343\ \mathrm{m/s}$) y el término de absorción del aire $4mV$.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reverberation_models_es.svg" alt="Tiempo de reverberación por banda de octava para una sala con suelo y techo absorbentes pero paredes duras, calculado por cinco modelos" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reverberation_models_es_dark.svg" alt="Tiempo de reverberación por banda de octava para una sala con suelo y techo absorbentes pero paredes duras, calculado por cinco modelos" style="width:82%">

## 1. Sabine, Eyring y Millington-Sette

Los tres modelos estadísticos toman el volumen de la sala y una lista de
superficies `(área, coeficiente_de_absorción)`. **Sabine** solo es exacto para
absorción baja y uniforme; **Eyring** sustituye el área de absorción por
$-S\ln(1-\bar\alpha)$ y es correcto donde Sabine sobrestima $T$;
**Millington-Sette** suma el término de Eyring superficie a superficie, de modo
que una única superficie perfectamente absorbente lleva $T$ a cero.

$$
T_{\text{Sab}} = \frac{k V}{\sum_i S_i\alpha_i}, \qquad
T_{\text{Eyr}} = \frac{k V}{-S\ln(1-\bar\alpha)}, \qquad
T_{\text{Mil}} = \frac{k V}{-\sum_i S_i\ln(1-\alpha_i)}.
$$

```python
import phonometry as ph

# Sala rectangular 8 x 5 x 3 m (V = 120 m3, S = 158 m2), alpha uniforme = 0,2.
surfaces = [(40.0, 0.2), (40.0, 0.2), (24.0, 0.2),
            (24.0, 0.2), (15.0, 0.2), (15.0, 0.2)]
print(round(ph.sabine_reverberation_time(120.0, surfaces), 3))            # 0.612 s
print(round(ph.eyring_reverberation_time(120.0, surfaces), 3))            # 0.548 s
print(round(ph.millington_sette_reverberation_time(120.0, surfaces), 3))  # 0.548 s
```

Para una distribución **uniforme**, Eyring y Millington-Sette coinciden, y ambos
quedan por debajo de Sabine — la sobrestimación de Sabine con absorción alta es
la razón de ser de Eyring. Cuando $\alpha \to 0$, Eyring se reduce a Sabine. La
absorción del aire entra en todos los modelos a través del coeficiente de
atenuación de potencia $m$ (en neper por metro, de la
[absorción atmosférica](/phonometry/es/guides/room-acoustics/)):

```python
import phonometry as ph

m = ph.air_attenuation_m(2000.0, temperature=20.0, relative_humidity=50.0)
surfaces = [(40.0, 0.3), (40.0, 0.3), (24.0, 0.3),
            (24.0, 0.3), (15.0, 0.3), (15.0, 0.3)]
print(round(ph.eyring_reverberation_time(120.0, surfaces, air_attenuation=m), 3))
```

## 2. Fitzroy y Arau-Puchades (salas anisótropas)

Cuando la absorción se concentra en un eje — un suelo enmoquetado y un techo
acústico frente a paredes por lo demás duras — una única media $\bar\alpha$
tergiversa el campo. **Fitzroy** y **Arau-Puchades** dividen una sala
rectangular en los tres pares de paredes opuestas y combinan los tiempos de
reverberación de Eyring *axiales* $T_i$ (cada uno con la superficie total $S$ y
la absorción media $\bar\alpha_i$ del par de paredes perpendicular al eje $i$):

$$
T_{\text{Fitz}} = \sum_i \frac{S_i}{S}\,T_i \quad(\text{aritmética}), \qquad
T_{\text{Arau}} = \prod_i T_i^{\,S_i/S} \quad(\text{geométrica}).
$$

```python
import phonometry as ph

# Sala 8 x 5 x 3 m, par de paredes x absorbente (alpha 0,5), duro el resto (0,1).
dims = (8.0, 5.0, 3.0)
absorption = (0.5, 0.1, 0.1)   # alpha medio de los pares de paredes (x, y, z)
print(round(ph.arau_puchades_reverberation_time(dims, absorption), 3))  # 0.812 s
print(round(ph.fitzroy_reverberation_time(dims, absorption), 3))        # 0.974 s
```

Por la desigualdad de las medias aritmética y geométrica, el tiempo de
Arau-Puchades nunca supera al de Fitzroy; se sabe que Fitzroy sobrepredice
cuando un par de paredes es muy reflectante, por lo que Arau-Puchades recomienda
la media geométrica. Ambos se reducen exactamente a Eyring para una distribución
de absorción uniforme.

## 3. Comparación de los cinco modelos por banda

`reverberation_time_models` construye las seis superficies de contorno de una
sala rectangular a partir de sus dimensiones y las tres absorciones medias de
los pares de paredes, evalúa los cinco modelos en igualdad de condiciones y
devuelve un `ReverberationModelResult` cuyo `.plot()` dibuja la figura anterior.

```python
import phonometry as ph

# Sala 10 x 7 x 3,5 m, suelo/techo absorbentes frente a paredes más duras.
res = ph.reverberation_time_models(
    (10.0, 7.0, 3.5),
    (
        [0.06, 0.07, 0.08, 0.09, 0.10, 0.10],   # par x: paredes de fondo duras
        [0.12, 0.14, 0.16, 0.18, 0.20, 0.20],   # par y: paredes poco tratadas
        [0.30, 0.50, 0.65, 0.78, 0.82, 0.80],   # par z: moqueta + techo acústico
    ),
    frequencies=[125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0],
)
print(res.sabine.round(2))         # [0.74 0.47 0.37 0.31 0.3  0.3 ]
print(res.arau_puchades.round(2))  # [0.79 0.51 0.38 0.29 0.26 0.27]
print(res.fitzroy.round(2))        # [1.02 0.79 0.66 0.57 0.51 0.51]
```

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph

m = ph.air_attenuation_m([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0], 20.0, 50.0)
ph.reverberation_time_models(
    (10.0, 7.0, 3.5),
    (
        [0.06, 0.07, 0.08, 0.09, 0.10, 0.10],
        [0.12, 0.14, 0.16, 0.18, 0.20, 0.20],
        [0.30, 0.50, 0.65, 0.78, 0.82, 0.80],
    ),
    air_attenuation=m,
    frequencies=[125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0],
).plot()
plt.show()
```

</details>

---

**Referencias.** W. C. Sabine, *Collected Papers on Acoustics* (1922); C. F.
Eyring (1930); G. Millington (1932); D. Fitzroy, *J. Acoust. Soc. Am.* **31**
(1959) 893; H. Arau-Puchades, «An improved reverberation formula», *Acustica*
**65** (1988) 163 (Fórmula 18). Libros de texto: A. Carrión Isbert, *Diseño
acústico de espacios arquitectónicos*; F. A. Everest y K. C. Pohlmann, *Master
Handbook of Acoustics*, 4.ª ed. La absorción del aire sigue ISO 9613-1:1993. La
batería de conformidad se ancla en un **ejemplo resuelto real** — el Ejemplo 1
de la Fig. 7-22 de Everest, cuyos seis tiempos de reverberación de Sabine
impresos reproduce la implementación SI con ≤ 0,02 s — reforzado por valores en
forma cerrada calculados a mano y las identidades entre modelos.

## Véase también

- Referencia de la API: [`room.reverberation_prediction`](/phonometry/es/reference/api/rooms/reverberation-prediction/) y [`environmental.air_absorption`](/phonometry/es/reference/api/environment/air-absorption/).
