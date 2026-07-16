---
title: "Vibración con choques múltiples (ISO 2631-5)"
description: "El modelo de respuesta espinal de ISO 2631-5:2018 para la vibración de cuerpo completo con choques múltiples: la función de transferencia asiento-columna y la dosis de aceleración de la cláusula 5, y la tensión compresiva, la variable de tensión acumulada R y la probabilidad de lesión lumbar de Weibull del Anexo C."
---

La vibración que contiene **choques mecánicos** repetidos — vehículos todoterreno,
embarcaciones rápidas, maquinaria de movimiento de tierras — carga la columna
lumbar mucho más de lo que sugiere su nivel eficaz equivalente. **ISO
2631-5:2018** predice la respuesta espinal resultante y el riesgo de lesión
lumbar a partir de la aceleración vertical medida en el asiento. phonometry
implementa el modelo normativo de respuesta espinal de la **cláusula 5** y la
evaluación de efectos sobre la salud del **Anexo C**. (El modelo de elementos
finitos de los Anexos A / E lo distribuye ISO como software aparte y queda fuera
de alcance aquí.)

La frontera con el método básico es explícita. ISO 2631-1 declara su
evaluación eficaz normalmente suficiente hasta un factor de cresta de 9, y
ofrece el eficaz móvil/MTVV y el VDV más allá; ISO 2631-5 es el método
adicional para el régimen posterior, cuando el registro contiene choques
repetidos. Su cláusula 4 divide después ese régimen en dos: las condiciones
*severas*, con posible caída libre o pérdida de contacto con el asiento y un
eje z dominante (vehículos militares todoterreno, embarcaciones rápidas),
usan el modelo de la cláusula 5 implementado aquí, mientras que las
condiciones *menos severas*, en las que el ocupante permanece sentado en todo
momento (tractores, maquinaria forestal y de movimiento de tierras sobre
terreno irregular), corresponden al modelo de elementos finitos del Anexo A.
En caso de duda, la delimitación es cuantitativa: cuando la aceleración de
pico vertical limitada en banda supera 9,81 m/s² (1 g, el umbral de caída
libre), se aplican la cláusula 5 y el Anexo C.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso2631_5_es.svg" alt="Flujo desde la aceleración vertical del asiento az(t) hasta la respuesta espinal, la dosis de aceleración Dz y la dosis diaria Dzd, la tensión compresiva Sd, la variable de tensión R acumulada con la edad, y la probabilidad de lesión lumbar de Weibull" style="width:86%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso2631_5_es_dark.svg" alt="Flujo desde la aceleración vertical del asiento az(t) hasta la respuesta espinal, la dosis de aceleración Dz y la dosis diaria Dzd, la tensión compresiva Sd, la variable de tensión R acumulada con la edad, y la probabilidad de lesión lumbar de Weibull" style="width:86%">

## 1. Respuesta espinal (cláusula 5.2)

Una función de transferencia asiento-columna `H(f)` — un cero complejo y seis
polos complejos, transmisibilidad unidad a 0 Hz y una resonancia cerca de 5 Hz —
transforma la aceleración medida del asiento en la respuesta espinal vertical
`Az(t)` (Fórmula 1/2):

$$
A_z(t) = \mathcal{F}^{-1}\!\left[H(f)\,\mathcal{F}[a_z(t)]\right].
$$

El registro de entrada debe estar **acondicionado (sin componente continua)**:
como `H` es unidad a 0 Hz por diseño, un offset de continua (por ejemplo, la
componente de gravedad de 1 g de un acelerómetro acoplado en continua) pasa
directamente a `Az(t)` y corrompe los picos positivos de respuesta de la dosis.
Reste la media (o aplique un paso alto) antes de procesar.

```python
from phonometry import vibration

# La transmisibilidad alcanza el máximo cerca de la resonancia espinal de ~5 Hz.
print(round(abs(vibration.seat_to_spine_transfer([2.0])[0]), 2))  # 1.06
print(round(abs(vibration.seat_to_spine_transfer([5.0])[0]), 2))  # 1.54
```

## 2. Dosis de aceleración (cláusula 5.3)

La **dosis de aceleración** combina los picos positivos de la respuesta `Az,i`
(cada uno el máximo entre dos cruces por cero consecutivos) con una ley de sexta
potencia, de modo que dominan los choques mayores (Fórmula 3):

$$
D_z = 1{,}07\left(\sum_i A_{z,i}^{\,6}\right)^{1/6}.
$$

Una dosis diaria escala la dosis medida al tiempo de exposición diario `td` sobre
el tiempo de medida `tm` (Fórmula 4): `Dzd = Dz * (td/tm)**(1/6)`.

```python
from phonometry import vibration

# Cinco picos de respuesta de 40 m/s2 al día (el ejemplo del Anexo C).
print(round(vibration.dose_from_peaks([40.0] * 5), 2))  # 55.97  m/s2
```

## 3. Riesgo de lesión (Anexo C)

La dosis diaria se convierte en una **tensión compresiva** diaria
`Sd = mz * Dzd` (Fórmula C.1), donde `mz` (0,029 MPa por m/s² para un hombre de
82 kg, 0,025 para una mujer de 64 kg) convierte la aceleración en tensión
vertebral. La tensión se acumula sobre los años de exposición frente a la
resistencia última decreciente de la columna que envejece
`Su = 6,75 - Sage*(b+i)` (Fórmulas C.3/C.4):

$$
R = \left[\sum_{i=0}^{n-1}
\left(\frac{S_d\,N^{1/6}}{S_{u,i} - S_{\mathrm{stat}}}\right)^{6}\right]^{1/6},
$$

y un modelo de Weibull da la probabilidad de lesión lumbar (Fórmula C.5):

$$
\Pi(R) = 1 - \exp\!\left[-\left(\frac{R}{\alpha}\right)^{\beta}\right].
$$

```python
from phonometry import vibration

# Ejemplo del Anexo C: 5 x 40 m/s2/día, hombre de 82 kg, edad 20 durante 20
# años, 120 días/año.
dz = vibration.dose_from_peaks([40.0] * 5)
sd = vibration.compression_dose(dz)                     # 1.62 MPa
r = vibration.injury_risk(sd, start_age=20, years=20, days_per_year=120)
print(round(r, 2))                               # 1.22
print(round(100 * vibration.injury_probability(r)))     # 37  % de riesgo de lesión
```

Desde un registro temporal medido, toda la cadena es una sola llamada:

```python
import numpy as np
from phonometry import vibration

# Un registro sintético de asiento de 10 s a 256 Hz con cinco choques de
# 60 m/s2 (sustituto de un az(t) medido).
fs = 256.0
az = np.zeros(2560)
az[256::512] = 60.0
result = vibration.multiple_shock_assessment(
    az, fs, start_age=20, years=20, days_per_year=120, sex="male",
)
print(round(result.acceleration_dose, 2))  # 20.94  m/s2
print(round(result.risk, 2))               # 0.46
print(round(result.probability, 2))        # 0.03
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/multiple_shock_es.svg" alt="Izquierda: la transmisibilidad asiento-columna sube hasta cerca de 1,6 en una resonancia de 5 Hz y luego cae casi a cero en 80 Hz. Derecha: la probabilidad de lesión lumbar de Weibull frente a la variable de tensión R para hombre y mujer, con los niveles de riesgo del 10, 50 y 90 por ciento y el ejemplo masculino del Anexo C en R = 1,22, en torno al 37 por ciento" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/multiple_shock_es_dark.svg" alt="Izquierda: la transmisibilidad asiento-columna sube hasta cerca de 1,6 en una resonancia de 5 Hz y luego cae casi a cero en 80 Hz. Derecha: la probabilidad de lesión lumbar de Weibull frente a la variable de tensión R para hombre y mujer, con los niveles de riesgo del 10, 50 y 90 por ciento y el ejemplo masculino del Anexo C en R = 1,22, en torno al 37 por ciento" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from phonometry import vibration

# Izquierda: la magnitud de la función de transferencia asiento-columna.
f = np.logspace(np.log10(0.5), np.log10(80.0), 400)
plt.plot(f, np.abs(vibration.seat_to_spine_transfer(f)))
plt.xscale("log"); plt.show()

# Derecha: la curva de probabilidad de lesión con la R de esta evaluación
# (az/fs como en el snippet anterior).
fs = 256.0
az = np.zeros(2560)
az[256::512] = 60.0
vibration.multiple_shock_assessment(
    az, fs, start_age=20, years=20, days_per_year=120,
).plot()
plt.show()
```

</details>

El `MultipleShockResult` lleva la dosis `Dz`, la dosis diaria `Dzd`, la tensión
compresiva `Sd`, la variable de tensión `R`, la probabilidad de lesión y los
picos de respuesta, y su `.plot()` dibuja la curva de probabilidad de lesión con
los umbrales de riesgo del 10/50/90 % de la Tabla C.2. Complementa las métricas
eficaz, eficaz móvil/MTVV y VDV de
[Vibración en humanos](/phonometry/es/guides/human-vibration/) (ISO 2631-1).

## Referencias

- Griffin, M. J. (1996). *Handbook of human vibration*. Academic Press.
  ISBN 978-0-12-303041-2.
  [Página del editor](https://shop.elsevier.com/books/handbook-of-human-vibration/griffin/978-0-12-303041-2).
  Contexto sobre la exposición a choques de cuerpo completo, la biodinámica
  espinal y los efectos lumbares sobre la salud que cuantifica el modelo de
  dosis de ISO 2631-5.

## Normas

ISO 2631-5:2018, *Mechanical vibration and shock — Evaluation of
human exposure to whole-body vibration — Part 5: Method for evaluation of
vibration containing multiple shocks* — la función de transferencia
asiento-columna (cláusula 5.2, Fórmula 1), la dosis de aceleración y diaria
(cláusula 5.3, Fórmulas 3-5) y la evaluación de efectos sobre la salud del
Anexo C (Fórmulas C.1, C.3-C.5, Tablas C.1/C.2).

## Véase también

- Referencia de la API: [`vibration.multiple_shock_vibration`](/phonometry/es/reference/api/vibration/multiple-shock-vibration/).
