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
[absorción atmosférica](/phonometry/es/guides/outdoor-propagation/) de
ISO 9613-1):

```python
import phonometry as ph

m = ph.air_attenuation_m(2000.0, temperature=20.0, relative_humidity=50.0)
surfaces = [(40.0, 0.3), (40.0, 0.3), (24.0, 0.3),
            (24.0, 0.3), (15.0, 0.3), (15.0, 0.3)]
print(round(ph.eyring_reverberation_time(120.0, surfaces, air_attenuation=m), 3))
```

Todos los modelos estadísticos suponen además un **campo difuso**, y las
bajas frecuencias son las primeras en romper esa suposición: por debajo de
la frecuencia de Schroeder la sala responde como un conjunto de modos
discretos, no como una mezcla reverberante. La simulación FDTD 2D siguiente
excita una sala rígida de 5 m por 3,5 m exactamente en su modo (2,1) y
después entre dos modos; el patrón de onda estacionaria que se forma en
resonancia es lo que Sabine y Eyring no pueden ver.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: simulación FDTD 2D de una sala de 5 por 3,5 metros excitada en el modo (2,1) de 84 Hz y en una frecuencia fuera de modo; en resonancia un patrón de onda estacionaria con líneas nodales fijas crece hasta dominar el mapa de presión RMS, fuera de resonancia la respuesta forzada se mantiene débil y desorganizada" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: simulación FDTD 2D de una sala de 5 por 3,5 metros excitada en el modo (2,1) de 84 Hz y en una frecuencia fuera de modo; en resonancia un patrón de onda estacionaria con líneas nodales fijas crece hasta dominar el mapa de presión RMS, fuera de resonancia la respuesta forzada se mantiene débil y desorganizada" style="width:88%"></video>

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

## 4. Elegir un modelo, y cuándo fallan todos

Las cinco fórmulas no compiten en un único eje de precisión; cada una tiene
su dominio de validez:

- **Sabine** es la herramienta para salas vivas con absorción baja y
  razonablemente repartida ($\bar\alpha$ media hasta aproximadamente 0,2):
  aulas, salas de actos, cámaras reverberantes. Es además la convención
  integrada en la práctica de medida, porque el coeficiente de absorción de
  ISO 354 se *define* mediante la fórmula de Sabine, así que devolver datos
  de cámara reverberante a Sabine es autoconsistente incluso donde la
  fórmula se tensa. Su defecto estructural aparece con absorción alta: con
  $\alpha = 1$ en todas las superficies (una abertura en todas las
  direcciones) sigue prediciendo un tiempo de reverberación finito.
- **Eyring** es la elección para salas tratadas de forma uniforme con
  absorción considerable: estudios, oficinas tratadas, salas de escucha.
  Alcanza $T = 0$ con absorción total, y su corrección sobre Sabine crece
  con $\bar\alpha$ (en torno a un 10 % más corto con $\bar\alpha = 0{,}2$,
  un 30 % con 0,5).
- **Millington-Sette** maneja una mezcla de superficies muy absorbentes y
  duras mejor que una única media, pero está pensado para coeficientes
  medidos por debajo de la unidad: una sola superficie con $\alpha_i = 1$
  lleva toda la predicción a cero. Los coeficientes de cámara reverberante
  iguales o superiores a 1,0 (un resultado documentado de ISO 354, ver la
  sección de absorción de
  [Acústica de salas](/phonometry/es/guides/room-acoustics/)) quedan fuera
  del dominio de los modelos logarítmicos, cuyo $\ln(1-\alpha)$ no está
  definido ahí, y phonometry los rechaza en todas las fórmulas de este
  módulo. Llevar un coeficiente así a $[0, 1)$ es una decisión de modelado
  que las fórmulas no prescriben: el ajuste que elijas (es habitual
  limitarlo justo por debajo de 1) debe registrarse junto a la predicción.
- **Fitzroy** y **Arau-Puchades** apuntan a salas rectangulares con la
  absorción concentrada en un eje, la oficina o vivienda típica con suelo y
  techo blandos entre paredes duras. La media geométrica de Arau templa la
  conocida sobrepredicción de Fitzroy cuando un par de paredes es muy
  reflectante.

**Cuándo fallan todas las fórmulas.** Las cinco heredan la misma hipótesis:
un campo difuso, con sonido llegando por igual desde todas las direcciones
en todos los puntos, que permanece difuso mientras decae. Las rupturas
habituales:

- **Por debajo de la frecuencia de Schroeder** la banda contiene un puñado
  de modos discretos (la animación del §1) y un tiempo de reverberación
  estadístico ni siquiera está definido; cada modo decae a su propio ritmo,
  fijado por las impedancias de las paredes que realmente toca.
- **Los volúmenes acoplados** (una sala con la caja escénica abierta, dos
  recintos a través de una puerta) producen decaimientos de doble
  pendiente; no existe un único $T$, y los T20 y T30 medidos discrepan (el
  diagnóstico de curvatura de
  [Acústica de salas](/phonometry/es/guides/room-acoustics/)).
- **Las salas desproporcionadas** (pasillos, salas bajas y extensas) con la
  absorción en un solo par de superficies mantienen un campo rasante
  paralelo a las superficies duras que el absorbente apenas toca; el tiempo
  medido puede llegar a duplicar cualquier predicción estadística, la
  experiencia práctica recogida en EN 12354-6 (ver
  [Absorción sonora en recintos](/phonometry/es/guides/enclosed-space-absorption/)).
- **Las geometrías focalizantes** (cúpulas, paredes traseras curvas)
  concentran la energía tardía en lugar de mezclarla, produciendo
  decaimientos dependientes de la posición que ninguna fórmula de un solo
  número puede representar.

Los objetos difusores restauran la mezcla que los modelos suponen: una sala
amueblada sigue la predicción estadística claramente mejor que la misma
sala vacía, más allá de lo que explica el área de absorción propia del
mobiliario. En la práctica, indica una *banda* de predicciones (Sabine y
Eyring, o Fitzroy y Arau-Puchades en los casos axiales) en lugar de un
único valor; donde los modelos se separan, la sala está diciendo que su
campo no es difuso.

## Referencias

- Sabine, W. C. (1922). *Collected papers on acoustics*. Harvard University
  Press. [Escaneo libre en Internet Archive](https://archive.org/details/collectedpaperso00sabi).
  Los experimentos originales de reverberación y la ley $T = 0{,}161\,V/A$
  del §1.
- Eyring, C. F. (1930). Reverberation time in "dead" rooms. *The Journal of
  the Acoustical Society of America*, 1(2A), 217-241.
  [doi:10.1121/1.1915175](https://doi.org/10.1121/1.1915175).
  La derivación por recorrido libre medio tras el término
  $-S\ln(1-\bar\alpha)$ del §1.
- Millington, G. (1932). A modified formula for reverberation. *The Journal
  of the Acoustical Society of America*, 4(1), 69-82.
  [doi:10.1121/1.1915588](https://doi.org/10.1121/1.1915588).
  El término logarítmico de absorción por superficie del §1.
- Fitzroy, D. (1959). Reverberation formula which seems to be more accurate
  with nonuniform distribution of absorption. *The Journal of the
  Acoustical Society of America*, 31(7), 893-897.
  [doi:10.1121/1.1907814](https://doi.org/10.1121/1.1907814).
  La división axial en tres decaimientos por pares de paredes del §2.
- Arau-Puchades, H. (1988). An improved reverberation formula. *Acustica*,
  65(4), 163-180.
  [Ficha del editor en Ingenta](https://www.ingentaconnect.com/content/dav/aaua/1988/00000065/00000004/art00003).
  La combinación por media geométrica del §2 (su Fórmula 18).
- Kuttruff, H. (2016). *Room acoustics* (6.ª ed.). CRC Press.
  [doi:10.1201/9781315372150](https://doi.org/10.1201/9781315372150).
  La teoría del campo difuso, sus límites y la valoración moderna de las
  fórmulas clásicas tras el §4.
- Everest, F. A. (2001). *Master handbook of acoustics* (4.ª ed.).
  McGraw-Hill. ISBN 978-0-07-136097-5.
  [Ficha en Open Library](https://openlibrary.org/isbn/9780071360975).
  El ejemplo resuelto de la Fig. 7-22 que reproduce la batería de
  conformidad.
- Carrión Isbert, A. (1998). *Diseño acústico de espacios arquitectónicos*.
  Edicions UPC. ISBN 978-84-8301-252-9.
  [Ficha en Open Library](https://openlibrary.org/books/OL23159935M).
  Un tratamiento en español de los modelos de reverberación y su uso en el
  diseño de salas.

---

**Normas.** Las fórmulas clásicas de reverberación son anteriores al mundo
normativo; entran en él a través de EN 12354-6:2003, cuyo modelo de la
cláusula 4 es un cálculo de Sabine con términos de objetos y de aire (ver
[Absorción sonora en recintos](/phonometry/es/guides/enclosed-space-absorption/)),
y a través de ISO 354:2003, que define el coeficiente de absorción medido
mediante la fórmula de Sabine. La absorción del aire sigue ISO 9613-1:1993,
*Acoustics — Attenuation of sound during propagation outdoors — Part 1:
Calculation of the absorption of sound by the atmosphere* (ver
[Propagación en exteriores](/phonometry/es/guides/outdoor-propagation/)).
La batería de conformidad se ancla en un ejemplo resuelto real, el
Ejemplo 1 de la Fig. 7-22 de Everest (una sala sin tratar de
23,3 × 16 × 10 ft), cuyos seis tiempos de reverberación de Sabine impresos
reproduce la implementación SI con ≤ 0,02 s, reforzado por valores en forma
cerrada calculados a mano y las identidades entre modelos (todo modelo
colapsa a Eyring con absorción uniforme; Eyring colapsa a Sabine cuando
$\alpha \to 0$), que trasladan transitivamente ese anclaje de datos reales
a toda la familia.

## Véase también

- Referencia de la API: [`room.reverberation_prediction`](/phonometry/es/reference/api/rooms/reverberation-prediction/) y [`environmental.air_absorption`](/phonometry/es/reference/api/environment/air-absorption/).
