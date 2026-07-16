---
title: "Absorción sonora en recintos (EN 12354-6)"
description: "La predicción de EN 12354-6:2003 del área de absorción sonora equivalente total de una sala y su tiempo de reverberación a partir de la absorción de sus superficies y objetos (el modelo normativo de la cláusula 4): el área de absorción de la Fórmula 1, los términos de objetos y aire, y el tiempo de reverberación de la Fórmula 5."
---

**EN 12354-6:2003** predice el **área de absorción sonora equivalente total** de
una sala y su **tiempo de reverberación** a partir de la absorción de sus
superficies y objetos — la contraparte de diseño del tiempo de reverberación
medido. Es el miembro de absorción de la familia de acústica de la edificación
EN 12354 (los miembros de aislamiento aéreo y de impacto están en
[Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/)).
phonometry implementa el modelo normativo de la cláusula 4. (El método
informativo del Anexo D para recintos irregulares queda fuera de alcance.)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_en12354_6_es.svg" alt="Flujo desde las superficies y objetos de la sala hasta el área de absorción equivalente total A, la fracción de objetos psi, y el tiempo de reverberación T = 55,3/c0 por V por (1 menos psi) entre A" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_en12354_6_es_dark.svg" alt="Flujo desde las superficies y objetos de la sala hasta el área de absorción equivalente total A, la fracción de objetos psi, y el tiempo de reverberación T = 55,3/c0 por V por (1 menos psi) entre A" style="width:82%">

## 1. Área de absorción equivalente (cláusula 4.3)

El área de absorción equivalente total suma, sobre las superficies $i$, los
objetos $j$ y las matrices de objetos $k$, el área de cada superficie por su
coeficiente de absorción, las áreas de absorción equivalentes de los objetos,
las matrices de objetos (grupos de objetos idénticos tratados como una
superficie absorbente de área $S_k$) y la absorción del aire (Fórmula 1):

$$
A = \sum_i \alpha_{s,i}\,S_i + \sum_j A_{\mathrm{obj},j}
    + \sum_k \alpha_{s,k}\,S_k + A_{\mathrm{air}}.
$$

Para objetos duros e irregulares cuya absorción no se mide, se usa una
estimación empírica a partir del volumen (Fórmula 4): `Aobj = Vobj**(2/3)`.

```python
import phonometry as ph

# EN 12354-6 Anexo E, sala desnuda (29.75 m3), banda de octava de 1000 Hz.
surfaces = [(12.39, 0.05), (12.39, 0.02), (10.90, 0.04),
            (10.90, 0.04), (6.55, 0.04), (6.55, 0.04)]
print(round(ph.equivalent_absorption_area(surfaces), 2))  # 2.26  m2
print(round(float(ph.hard_object_absorption(0.65)), 3))   # 0.75  m2
```

La absorción del aire usa el coeficiente de atenuación de potencia `m`
(Fórmula 2): `Aair = 4*m*V*(1 - psi)`. Por debajo de 1 kHz y para salas de menos
de 200 m³ puede despreciarse.

## 2. Tiempo de reverberación (cláusula 4.4)

El tiempo de reverberación se obtiene del área de absorción, el volumen y la
fracción de objetos `psi = sum(Vobj)/V` (Fórmula 5):

$$
T = \frac{55{,}3}{c_0}\,\frac{V\,(1 - \psi)}{A},
$$

donde la velocidad del sonido `c0 = 345.6 m/s` hace que el factor `55.3/c0` sea
el familiar `0.16`.

```python
import phonometry as ph

surfaces = [(12.39, 0.05), (12.39, 0.02), (10.90, 0.04),
            (10.90, 0.04), (6.55, 0.04), (6.55, 0.04)]
a = ph.equivalent_absorption_area(surfaces)
print(round(ph.reverberation_time(a, 29.75), 1))          # 2.1  s

# Anexo E caso 2: añadir mobiliario (objetos duros) a la misma sala.
volumes = [0.15, 0.60, 0.05, 0.05, 0.65, 0.65]
aobj = ph.hard_object_absorption(volumes)
psi = ph.object_fraction(volumes, 29.75)                  # 0.072
a2 = ph.equivalent_absorption_area(surfaces, objects=aobj)
print(round(a2, 2), round(ph.reverberation_time(a2, 29.75, object_fraction=psi), 1))
# 5.03 0.9
```

Por banda de octava, una sola llamada toma las superficies (con coeficientes de
absorción por banda) y la condición del aire, y devuelve todo el espectro:

```python
import phonometry as ph

# Coeficientes de absorción por banda (125 Hz a 8 kHz) de cada superficie.
plaster = [0.02, 0.03, 0.03, 0.04, 0.05, 0.05, 0.05]
tile = [0.15, 0.35, 0.65, 0.85, 0.90, 0.90, 0.85]
result = ph.enclosed_space_reverberation(
    [(54.0, plaster), (20.0, plaster), (20.0, tile)],
    volume=60.0, air_condition="20C_50-70",
)
print(result.reverberation_time.round(2))
# [2.13 1.03 0.62 0.48 0.43 0.42 0.4 ]
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosed_space_absorption_es.svg" alt="Dos paneles para una oficina de 60 metros cúbicos con techo desnudo frente a techo acústico: el área de absorción equivalente por banda de octava, mucho mayor con el techo acústico, y el tiempo de reverberación cayendo desde unos cinco segundos a baja frecuencia con el techo desnudo hasta menos de un segundo con el techo acústico" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosed_space_absorption_es_dark.svg" alt="Dos paneles para una oficina de 60 metros cúbicos con techo desnudo frente a techo acústico: el área de absorción equivalente por banda de octava, mucho mayor con el techo acústico, y el tiempo de reverberación cayendo desde unos cinco segundos a baja frecuencia con el techo desnudo hasta menos de un segundo con el techo acústico" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph

plaster = [0.02, 0.03, 0.03, 0.04, 0.05, 0.05, 0.05]
tile = [0.15, 0.35, 0.65, 0.85, 0.90, 0.90, 0.85]
walls_floor = [(54.0, plaster), (20.0, plaster)]
for ceiling in (plaster, tile):
    ph.enclosed_space_reverberation(
        [*walls_floor, (20.0, ceiling)], 60.0, air_condition="20C_50-70",
    ).plot()
plt.show()
```

</details>

El `ReverberationResult` lleva el área de absorción y el tiempo de reverberación
por banda, el volumen y la fracción de objetos, y su `.plot()` dibuja el espectro
del tiempo de reverberación. Es la contraparte de predicción del tiempo de
reverberación medido en
[Acústica de salas](/phonometry/es/guides/room-acoustics/)
(ISO 3382) y de la absorción en cámara reverberante de
[Materiales acústicos](/phonometry/es/guides/materials/) (ISO 354).

## 3. De dónde salen los datos de entrada

**Coeficientes de superficie.** La norma espera que los $\alpha_{s,i}$
procedan de mediciones de laboratorio según EN ISO 354, el método de cámara
reverberante de
[Materiales acústicos](/phonometry/es/guides/materials/); se admiten
valores teóricos, empíricos o de campo siempre que se declare la fuente de
los datos. ISO 354 entrega datos en tercios de octava, y un cálculo en
bandas de octava toma como entrada la media aritmética de los tres tercios.
Un coeficiente de cámara reverberante puede superar 1,0 (la difracción de
borde dispersa hacia la muestra más energía de la que intercepta su área
plana); entra en la Fórmula 1 tal como se midió, sin recorte, porque la
misma convención de campo difuso que lo produjo es la que supone el modelo.

**Mobiliario y ocupantes.** Los objetos contribuyen por tres vías: un área
de absorción equivalente medida $A_{obj}$ cuando existe (personas y
asientos tienen valores tabulados en el Anexo C informativo), la estimación
de la Fórmula 4 $V_{obj}^{2/3}$ para objetos duros, irregulares y sin
medir (mobiliario, maquinaria), y los *conjuntos* de objetos valorados como
una superficie absorbente $\alpha_s S_k$ cuando muchos objetos similares
cubren una zona (un público sentado, una estantería de almacén). Los objetos
también desplazan aire: su volumen sumado entra en la fracción de objetos
$\psi$ que acorta $T$ en la Fórmula 5 más allá de lo que haría su absorción
sola.

**Aire.** El término de aire $A_{air} = 4mV(1-\psi)$ usa el coeficiente de
atenuación de potencia $m$ de la Tabla 1 de la norma, resuelto por las
cadenas `air_condition` (clase de temperatura y humedad relativa, derivada
de ISO 9613-1); solo importa por encima de 1 kHz y crece con el volumen.
Los seis perfiles integrados, de `"10C_30-50"` a `"20C_70-90"` (la
cláusula 4.3 recomienda `"20C_50-70"` cuando no se especifican
condiciones), cubren solo las bandas de octava estándar de 125 Hz a 8 kHz
y no pueden combinarse con un eje de frecuencias propio;
`air_condition=None` (el valor por defecto) omite el término de aire, y
para otras frecuencias o condiciones, calcula $m$ según ISO 9613-1 y
encadena `air_absorption_area` con `equivalent_absorption_area`.

**Límites de validez (cláusula 4.6).** El modelo supone una sala corriente
y razonablemente difusa: ninguna dimensión más de 5 veces otra, pares de
superficies opuestas cuyos coeficientes difieran en menos de un factor 3
(salvo que haya objetos difusores) y una fracción de objetos por debajo de
0,2. Fuera de esos límites el campo no es difuso y el modelo yerra por el
lado optimista: la propia cláusula de precisión de la norma registra
tiempos de reverberación medidos de hasta el doble de la predicción en
salas de baja difusividad. Las alternativas clásicas para esos casos viven
en
[Predicción del tiempo de reverberación](/phonometry/es/guides/reverberation-prediction/).

## Referencias

- European Committee for Standardization. (2003). *Building acoustics —
  Estimation of acoustic performance of buildings from the performance of
  elements — Part 6: Sound absorption in enclosed spaces*
  (EN 12354-6:2003).
  [Ficha en BSI Knowledge (BS EN 12354-6:2003)](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-of-buildings-from-the-performance-of-elements-sound-absorption-in-enclosed-spaces).
  El modelo de la cláusula 4, sus reglas de datos de entrada y sus límites
  de validez.
- International Organization for Standardization. (2003). *Acoustics —
  Measurement of sound absorption in a reverberation room* (ISO 354:2003).
  [Catálogo iso.org](https://www.iso.org/standard/34545.html).
  La medición de laboratorio de la que salen los coeficientes de
  superficies y conjuntos.
- Kuttruff, H. (2016). *Room acoustics* (6.ª ed.). CRC Press.
  [doi:10.1201/9781315372150](https://doi.org/10.1201/9781315372150).
  La teoría estadística de la reverberación que las fórmulas de la norma
  especializan.

---

**Normas.** EN 12354-6:2003, *Building acoustics — Estimation of acoustic
performance of buildings from the performance of elements — Part 6: Sound
absorption in enclosed spaces* — el área de absorción equivalente total
(cláusula 4.3, Fórmulas 1-4, Tabla 1) y el tiempo de reverberación (cláusula
4.4, Fórmula 5), validados frente a los tres casos resueltos del Anexo E.

## Véase también

- Referencia de la API: [`room.enclosed_space_absorption`](/phonometry/es/reference/api/rooms/enclosed-space-absorption/).
