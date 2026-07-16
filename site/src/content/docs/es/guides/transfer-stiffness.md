---
title: "Rigidez dinámica de transferencia (ISO 10846)"
description: "La rigidez dinámica de transferencia k₂₁ = F₂,b/u₁ de elementos resilientes según ISO 10846: el nivel Lₖ re 1 N/m y el factor de pérdidas (Partes 1-3), el método directo (Parte 2), el método indirecto k₂₁ = −(2πf)²(m₂+m_f)T a partir de la transmisibilidad de vibración (Parte 3, Fórmula 1) y la relación del Anexo A con la impedancia mecánica y la masa efectiva."
---

La propiedad de transferencia vibroacústica de un elemento resiliente —un
aislador de vibraciones, montura, fuelle o manguera— es su **rigidez dinámica de
transferencia** `k₂₁`, el cociente dependiente de la frecuencia entre la *fuerza
de bloqueo* en el lado de salida (receptor) y el desplazamiento en el lado de
entrada (fuente) (ISO 10846-1, 3.7):

$$
k_{2,1} = \frac{F_{2,b}}{u_1} \quad [\mathrm{N/m}].
$$

Como un aislador de vibraciones solo es eficaz entre estructuras de gran rigidez
en el punto de excitación, la fuerza que entrega al receptor aproxima esta fuerza
de bloqueo (ISO 10846-1, Ec. 7), de modo que `k₂₁` es la magnitud que caracteriza
la transmisión del aislador. `k₂₁` alimenta las normas de fuente estructural y
de predicción en edificación: ISO 9611, EN 15657 y EN 12354-5.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/transfer_stiffness_es.svg" alt="Nivel de rigidez dinámica de transferencia de un aislador Kelvin-Voigt: el nivel real y la estimación por el método indirecto, que diverge en la resonancia masa/resorte y converge por encima de ella" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/transfer_stiffness_es_dark.svg" alt="Nivel de rigidez dinámica de transferencia de un aislador Kelvin-Voigt: el nivel real y la estimación por el método indirecto, que diverge en la resonancia masa/resorte y converge por encima de ella" style="width:82%">

## 1. El nivel de rigidez de transferencia y el factor de pérdidas

Los resultados se expresan como un **nivel** re la rigidez de referencia
`k₀ = 1 N/m` (ISO 10846-2 y -3, 3.17) y, en el rango de baja frecuencia donde las
fuerzas de inercia del elemento son despreciables, el **factor de pérdidas** es
la tangente del ángulo de fase de `k₂₁` (ISO 10846-1, 3.8):

$$
L_k = 10\lg\frac{|k_{2,1}|^2}{k_0^2} = 20\lg\frac{|k_{2,1}|}{k_0}, \qquad
\eta = \frac{\mathrm{Im}(k_{2,1})}{\mathrm{Re}(k_{2,1})}.
$$

```python
import phonometry as ph

# Una montura resiliente con |k2,1| = 1 MN/m y un factor de pérdidas del 5 %:
k = 1e6 * (1.0 + 0.05j)
print(round(float(ph.transfer_stiffness_level(k)), 2))   # 120.00  dB re 1 N/m
print(round(float(ph.loss_factor(k)), 3))                # 0.05
```

## 2. Determinación directa e indirecta

¿Por qué una fuerza *bloqueada* y no, por ejemplo, la transmisibilidad del
aislador? Porque una transmisibilidad es una propiedad del conjunto completo:
cambia con las masas y rigideces que el aislador conecte en cada caso, así
que unos datos medidos en un banco no se trasladarían a otra instalación. La
fuerza bloqueada por unidad de desplazamiento de entrada es una propiedad del
elemento solo, y predice la fuerza que el elemento entrega a cualquier
receptor mucho más rígido que el propio elemento, que es exactamente la
situación para la que se diseña un aislador de vibración. Por eso ISO 10846
intercala el aislador entre una masa de entrada excitada y una salida que
está o bien bloqueada rígidamente o bien cargada con una masa conocida:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_transfer_stiffness_rig_es.svg" alt="Bancos de rigidez de transferencia ISO 10846: el aislador bajo ensayo entre una masa de excitación y o bien una salida bloqueada con un transductor de fuerza, el método directo, o bien una masa de bloqueo sobre apoyos resilientes, el método indirecto" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_transfer_stiffness_rig_es_dark.svg" alt="Bancos de rigidez de transferencia ISO 10846: el aislador bajo ensayo entre una masa de excitación y o bien una salida bloqueada con un transductor de fuerza, el método directo, o bien una masa de bloqueo sobre apoyos resilientes, el método indirecto" style="width:92%">

El **método directo** (ISO 10846-2) mide la fuerza de salida bloqueada y el
desplazamiento de entrada, `k₂₁ = F₂,b/u₁`. El **método indirecto** (ISO 10846-3)
carga la salida con una masa de bloqueo compacta `m₂` y mide la transmisibilidad
de vibración `T = u₂/u₁`; la fuerza de bloqueo es entonces la fuerza de inercia de
la masa (ISO 10846-3, Ec. 1):

$$
k_{2,1} = -(2\pi f)^2\,(m_2 + m_f)\,T \qquad (T \ll 1),
$$

con `m_f` la masa de la brida de salida. La aproximación es válida bastante por
encima de la resonancia masa/resorte, donde `T` es pequeña.

```python
import numpy as np
import phonometry as ph

# Método indirecto: masa de bloqueo de 10 kg, transmisibilidad 0,01 a 500 Hz.
k = ph.transfer_stiffness_indirect(500.0, 0.01, blocking_mass=10.0)
print(f"{abs(complex(k)):.3e}")            # 9.870e+05  N/m

# Agrupa una medición en barrido en un resultado con su nivel y factor de pérdidas:
f = np.logspace(1.5, 3.3, 200)
t = ph.base_transmissibility(f, mass=8.0, stiffness=1e6, damping=120.0)
res = ph.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
print(round(float(res.level[-1]), 1))      # ~126  dB re 1 N/m (alta f)
```

El `TransferStiffnessResult` transporta el `k₂₁` complejo y expone `.level`,
`.loss_factor`, `.magnitude`, `.to("impedance"/"apparent_mass")` y `.plot()`.

Los dos métodos se reparten el eje de frecuencia. El método directo funciona
desde 1 Hz, el límite inferior del alcance de ISO 10846-2 (en la práctica el
suelo lo fijan el banco y su instrumentación), hasta donde se cuelan las
resonancias propias del banco (típicamente unos pocos cientos de hercios
para elementos grandes); el método indirecto solo es válido bastante por
encima de la
resonancia masa de bloqueo/resorte, donde la transmisibilidad es pequeña, y
extiende la caracterización hasta el rango de kilohercios. Un conjunto de
datos completo de un aislador suele ser el empalme de ambos.

## 3. Validez del método indirecto

La ISO 10846-3 (apartado 6) exige que la aproximación `T ≪ 1` sea exacta dentro
de **1 dB** (12 % de la magnitud de la rigidez), lo que acota el rango de
frecuencia utilizable por ambos lados:

* **Desadaptación de impedancias (Desigualdad 2).** Válido solo donde
  `ΔL₁,₂ = La₁ − La₂ ≥ 20 dB`, es decir, `|T| ≤ 0,1` (la constante
  `TRANSMISSIBILITY_LIMIT`). `transfer_stiffness_indirect` calcula el `|T|`
  por banda y emite un `PhonometryWarning` cuando alguna banda lo supera
  (habitual cerca o por debajo de la resonancia masa/resorte, como en la
  figura anterior).
* **Masa de bloqueo rígida (Desigualdad 3).** Por encima de una frecuencia
  superior `f₃` la masa de bloqueo deja de moverse como cuerpo rígido; los
  resultados solo son válidos mientras su masa efectiva medida
  `m₂,eff = 2F₂/(a′₁ + a″₁)` (Ec. 4) se mantenga dentro de 1 dB de la masa
  rígida: `10 lg(m₂,eff²/m₂²) ≤ 1 dB`.
* **Linealidad (apartado 7.6).** Dos espectros de entrada separados 10 dB
  deben dar niveles de rigidez de transferencia dentro de 1,5 dB.

La propia idealización de la fuerza de bloqueo la cuantifica la ISO 10846-1,
Ec. (6): para un aislador con rigidez en el punto de excitación de salida
`k₂,₂` sobre una terminación de rigidez `k_t`, la fuerza entregada es
`F₂/F₂,b = 1/(1 + k₂,₂/k_t)`, dentro del 10 % de la fuerza de bloqueo para
`|k₂,₂| < 0,1 |k_t|` (Ec. 7):

```python
import warnings
import phonometry as ph

# |T| = 0,5 viola la Desigualdad (2): el resultado indirecto queda avisado.
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    ph.transfer_stiffness_indirect(50.0, 0.5, blocking_mass=10.0)
print(caught[0].category.__name__)                     # PhonometryWarning

# Aproximación de la fuerza de bloqueo en el límite del 10 % (ISO 10846-1, Ec. 6):
print(round(abs(complex(ph.blocking_force_ratio(1e5, 1e6))), 4))   # 0.9091
```

## 4. Relación con la familia de FRF

La rigidez dinámica es un miembro de la familia de funciones de respuesta en
frecuencia (ISO 10846-1, Anexo A / Tabla A.2): es la recíproca de la receptancia
y se relaciona con la impedancia mecánica `Z` y la masa efectiva `m_eff` por
`k = jω·Z = −ω²·m_eff`. Estas conversiones son el mismo pivote `convert_frf` de la
[movilidad mecánica](/phonometry/es/guides/mechanical-mobility/):

```python
import phonometry as ph

k = 1e6 + 5e4j                                  # N/m, a 250 Hz
Z = ph.convert_frf(k, 250.0, "dynamic_stiffness", "impedance")
print(abs(complex(ph.convert_frf(Z, 250.0, "impedance", "dynamic_stiffness"))))  # 1.0012e6
```

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

k, c, m2 = 1e6, 120.0, 8.0
f0 = np.sqrt(k / m2) / (2 * np.pi)
f = np.logspace(np.log10(f0 / 5), np.log10(f0 * 40), 600)
w = 2 * np.pi * f
t = ph.base_transmissibility(f, m2, k, c)
plt.semilogx(f, ph.transfer_stiffness_level(k + 1j * w * c), label="$L_k$ real")
plt.semilogx(f, ph.transfer_stiffness_level(ph.transfer_stiffness_indirect(f, t, m2)),
             "--", label="método indirecto")
plt.axvline(f0, ls=":", color="0.6"); plt.legend()
plt.xlabel("Frecuencia [Hz]"); plt.ylabel("$L_k$ [dB re 1 N/m]"); plt.show()
```

</details>

## Referencias

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3.ª ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  Teoría del aislamiento de vibraciones: por qué el comportamiento de un
  aislador depende de las movilidades de fuente y receptor, la física que sustenta la
  caracterización por fuerza bloqueada.
- International Organization for Standardization. (2008). *Acoustics and
  vibration — Laboratory measurement of vibro-acoustic transfer properties of
  resilient elements — Part 1: Principles and guidelines* (ISO 10846-1:2008).
  [Catálogo iso.org](https://www.iso.org/standard/38936.html).
  La parte de principios de la serie: la idealización de fuerza de bloqueo y
  las relaciones FRF que implementa esta página.

## Normas

ISO 10846 (partes 1-5), *Acoustics and vibration — Laboratory
measurement of vibro-acoustic transfer properties of resilient elements*: la
rigidez dinámica de transferencia `k₂₁ = F₂,b/u₁` y sus relaciones FRF (Parte 1,
cláusula 5 y Anexo A / Tabla A.2), el nivel `L_k` re 1 N/m y el factor de pérdidas
(Partes 2 y 3, cláusulas 3.8/3.17), el método directo (Parte 2) y el método
indirecto `k₂₁ = −(2πf)²(m₂+m_f)T` (Parte 3, Fórmula 1) con sus condiciones de
validez (Parte 3, apartado 6: Desigualdades 2 y 3; linealidad del 7.6) y la
aproximación de la fuerza de bloqueo (Parte 1, Ecs. 6/7). Las partes 4 y 5 extienden
las mismas magnitudes a elementos distintos de los soportes y al método de punto
de excitación en baja frecuencia. La conformidad se ancla en las definiciones en
forma cerrada de la norma: el nivel de una década de rigidez, la relación de
inercia del método indirecto, la identidad de la Tabla A.2 `k = jω·Z`, el límite
de validez `|T| = 0,1 ↔ ΔL₁,₂ = 20 dB` con su cota de exactitud de 1 dB (12 %),
el cociente de fuerzas de la Ec. (6) `1/1,1` y el criterio de linealidad del 7.6.

## Véase también

- Referencia de la API: [`vibration.transfer_stiffness`](/phonometry/es/reference/api/vibration/transfer-stiffness/) y [`vibration.mechanical_mobility`](/phonometry/es/reference/api/vibration/mechanical-mobility/).
