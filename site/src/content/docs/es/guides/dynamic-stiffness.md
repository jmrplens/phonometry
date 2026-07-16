---
title: "Rigidez dinámica de materiales resilientes (EN 29052-1)"
description: "La determinación según EN 29052-1:1992 de la rigidez dinámica por unidad de área de materiales resilientes bajo suelos flotantes a partir de la resonancia de la placa de carga: la rigidez aparente de la Fórmula 4, el término del gas encerrado de la Fórmula 7, los regímenes por resistividad al flujo de la cláusula 8.2 y la frecuencia natural del suelo flotante de la Fórmula 2."
---

Un **suelo flotante** es una losa pesada que descansa sobre una capa resiliente;
ambos forman un sistema masa-resorte cuya **frecuencia natural** determina cuánto
mejora el suelo el aislamiento a impacto y aéreo. **EN 29052-1:1992** (idéntica a
ISO 9052-1:1989) mide la **rigidez dinámica por unidad de área** `s'` de la capa
resiliente a partir de la resonancia de una placa de carga normalizada sobre una
probeta de 200 mm × 200 mm. `s'` es la entrada al término de suelo flotante del
modelo de impacto de EN 12354-2 tratado en
[Predicción del aislamiento acústico (EN 12354)](/phonometry/es/guides/insulation-prediction/). (La
ISO 16251-1 no aplica aquí: su alcance se limita a revestimientos blandos de
reacción local y excluye expresamente los suelos flotantes.)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness_es.svg" alt="Frecuencia natural del suelo flotante frente a la rigidez dinámica por unidad de área de la capa resiliente para un suelo flotante ligero y uno pesado, con un punto de diseño" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness_es_dark.svg" alt="Frecuencia natural del suelo flotante frente a la rigidez dinámica por unidad de área de la capa resiliente para un suelo flotante ligero y uno pesado, con un punto de diseño" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import materials

s = np.logspace(np.log10(2.0), np.log10(100.0), 300)   # MN/m3
for m in (40.0, 120.0):
    plt.semilogx(s, materials.natural_frequency(s * 1e6, m), label=f"m' = {m:g} kg/m²")
plt.xlabel("Rigidez dinámica s' [MN/m³]"); plt.ylabel("Frecuencia natural f₀ [Hz]")
plt.legend(); plt.show()
```

</details>

## 1. Rigidez dinámica y resonancia

La rigidez dinámica por unidad de área es una fuerza dinámica por área dividida
entre el cambio de espesor resultante (Fórmula 1): `s' = (F/S)/Δd`. El suelo
soportado resilientemente es un resonador cuya frecuencia natural (Fórmula 2) y,
en la disposición de laboratorio, la frecuencia de resonancia medida (Fórmula 3)
son

$$
f_0 = \frac{1}{2\pi}\sqrt{\frac{s'}{m'}}, \qquad
f_r = \frac{1}{2\pi}\sqrt{\frac{s'_t}{m'_t}},
$$

por lo que la rigidez dinámica **aparente** se obtiene de la resonancia
(Fórmula 4):

$$
s'_t = 4\pi^2\,m'_t\,f_r^2 .
$$

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_dynamic_stiffness_rig_es.svg" alt="Banco de resonancia ISO 9052-1: un excitador vertical y un acelerómetro sobre la placa de carga encima de la probeta resiliente de 200 mm por 200 mm, leído como un sistema masa-resorte cuyo pico de respuesta da la frecuencia de resonancia y la rigidez dinámica aparente" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_dynamic_stiffness_rig_es_dark.svg" alt="Banco de resonancia ISO 9052-1: un excitador vertical y un acelerómetro sobre la placa de carga encima de la probeta resiliente de 200 mm por 200 mm, leído como un sistema masa-resorte cuyo pico de respuesta da la frecuencia de resonancia y la rigidez dinámica aparente" style="width:92%">

En la disposición de ensayo la probeta queda entre la base rígida y una placa
de carga cuya masa total por unidad de área, placa más carga añadida, es de
200 kg/m² (8 kg sobre la probeta de 0,04 m²). Esa carga reproduce la precarga
estática de un suelo flotante típico, unos 2 kPa. Un excitador vertical mueve
la placa, un acelerómetro recoge su respuesta y la resonancia vertical
fundamental $f_r$ del sistema placa-probeta se lee del pico de la respuesta;
la Fórmula 4 la convierte en $s'_t$.

```python
from phonometry import materials

# Placa de carga normalizada de 8 kg sobre la probeta de 0,04 m2 -> m't = 200 kg/m2;
# la resonancia fundamental se mide en 25 Hz.
s_t = materials.apparent_dynamic_stiffness(resonant_frequency=25.0, total_mass_per_area=200.0)
print(round(s_t / 1e6, 3))                              # 4.935  MN/m3

# Instalada sobre una losa flotante de 120 kg/m2 con s' = 10 MN/m3:
print(round(materials.natural_frequency(10e6, 120.0), 1))      # 45.9  Hz
```

## 2. El término del gas encerrado y la resistividad al flujo

En un material permeable al aire, el aire de los poros añade una rigidez en
paralelo por su compresión isoterma (Fórmula 7): `s'a = p₀/(d·ε)`, con `p₀` la
presión atmosférica, `d` el espesor bajo carga y `ε` la porosidad. La NOTA
resuelta de la norma (`p₀ = 0,1 MPa`, `ε = 0,9`) es `s'a = 111/d` MN/m³ con `d`
en milímetros:

```python
from phonometry import materials

print(round(materials.enclosed_gas_stiffness(thickness=0.020, porosity=0.9) / 1e6, 2))
# 5.56  MN/m3   (los 111/20 = 5.55 MN/m3 de la NOTA)
```

La rigidez dinámica del material *instalado* la fija entonces la resistividad
lateral al flujo `r` (cláusula 8.2): `s' = s't` para `r ≥ 100 kPa·s/m²`,
`s' = s't + s'a` para `10 ≤ r < 100 kPa·s/m²`, y para `r < 10 kPa·s/m²` el método
solo resuelve `s' = s't` cuando el término del gas es despreciable.
`floating_floor_resonance` encadena toda la determinación:

```python
from phonometry import materials

res = materials.floating_floor_resonance(
    resonant_frequency=25.0, total_mass_per_area=200.0,
    floor_mass_per_area=120.0,
    airflow_resistivity=50.0, thickness=0.020, porosity=0.9,
)
print(round(res.dynamic_stiffness / 1e6, 2), round(res.natural_frequency, 1))
# 10.49 47.1
```

El `DynamicStiffnessResult` contiene las rigideces aparente, del gas encerrado e
instalada, la resonancia del ensayo y la frecuencia natural del suelo instalado,
y su `.plot()` dibuja la curva de diseño `f₀(s')`.

## 3. Qué asume el método de resonancia, y dónde muerde

La evaluación trata el banco como un sistema de un grado de libertad: la
placa de carga se mueve como un pistón rígido sobre un resorte sin masa. Eso
se cumple mientras la probeta sea ligera frente a la placa y su primera
resonancia interna quede bastante por encima de $f_r$; una capa pesada o muy
gruesa empieza a comportarse como un sistema distribuido y la lectura simple
de la Fórmula 4 se degrada. De la precarga se derivan tres trampas prácticas:

* **`s'` es una rigidez *a la precarga normalizada*.** Las capas resilientes
  son visiblemente no lineales con la carga estática: la lana mineral se
  rigidiza al comprimirse, algunas espumas se ablandan. La placa de carga de
  200 kg/m² fija el punto de trabajo, así que la `s'` tabulada describe en
  rigor suelos próximos a esa masa superficial. Diseñar un recrecido mucho
  más pesado con la misma `s'` extrapola más allá de la medición.
* **Excitar poco.** La rigidez tangente se define para deformaciones
  dinámicas pequeñas; excitar fuerte la placa lleva la capa a su rango no
  lineal y desplaza la resonancia aparente hacia abajo. Mantén la excitación
  en el nivel más bajo que dé un pico limpio.
* **Cuidar el contacto.** La norma asienta la placa de carga sobre una capa
  fina de unión (una pasta de yeso) para que toda el área de la probeta
  soporte la carga. Un contacto seco e irregular concentra la fuerza,
  rigidiza la respuesta localmente y sesga $f_r$ hacia arriba.

La frecuencia natural que importa al final no es la $f_r$ del banco sino la
$f_0$ del suelo instalado según la Fórmula 2: el suelo flotante solo mejora
el aislamiento bastante por encima de $f_0$, y por eso una `s'` baja (una
capa blanda bajo una losa pesada) es el objetivo de diseño.

## Referencias

- Vigran, T. E. (2008). *Building acoustics*. CRC Press.
  ISBN 978-0-415-42853-8.
  [doi:10.1201/9781482266016](https://doi.org/10.1201/9781482266016).
  El diseño de suelos flotantes y el papel de la rigidez dinámica de la capa
  resiliente en la mejora a ruido de impactos.
- International Organization for Standardization. (1989). *Acoustics —
  Determination of dynamic stiffness — Part 1: Materials used under floating
  floors in dwellings* (ISO 9052-1:1989).
  [Catálogo iso.org](https://www.iso.org/standard/16620.html).
  El original internacional de EN 29052-1, el método que implementa esta
  página.

## Normas

EN 29052-1:1992 (= ISO 9052-1:1989), *Acoustics — Determination of
dynamic stiffness — Part 1: Materials used under floating floors in dwellings*:
la rigidez dinámica por unidad de área (Fórmula 1), las relaciones de resonancia
(Fórmulas 2-4), el término del gas encerrado (Fórmula 7, NOTA de la cláusula 8.2
`s'a = 111/d` MN/m³) y los regímenes por resistividad al flujo (Fórmulas 5-6). La
conformidad se ancla en la NOTA numérica de la propia norma más valores en forma
cerrada calculados a mano de las relaciones de resonancia.

## Véase también

- Referencia de la API: [`materials.dynamic_stiffness`](/phonometry/es/reference/api/materials/dynamic-stiffness/).
