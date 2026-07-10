---
title: "Umbral de audición (edad y cero de referencia)"
description: "La distribución del umbral de audición por edad de ISO 7029:2017 (mediana, dispersión y fractiles poblacionales por edad y sexo) y el umbral de referencia de la audición en campo libre y campo difuso de ISO 389-7:2006, sobre las frecuencias audiométricas de 125 Hz a 8000 Hz."
---

Dos normas describen dónde se sitúa el umbral de audición. **ISO 7029:2017** da
la **distribución estadística del umbral de audición con la edad** para una
población otológicamente normal — la pérdida lenta y primero en altas
frecuencias conocida como presbiacusia. **ISO 389-7:2006** fija el **umbral de
referencia de la audición**, el cero audiométrico (0 dB HL) expresado como nivel
de presión sonora en escucha de campo libre y campo difuso. Ambas se definen
sobre las frecuencias audiométricas de 125 Hz a 8000 Hz.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_hearing_threshold_es.svg" alt="El modelo del umbral de audición: la edad, el sexo y un fractil poblacional alimentan la cadena de ISO 7029 — la desviación mediana respecto a los 18 años, las dispersiones superior e inferior su y sl, y el umbral del fractil — dando el nivel del umbral de audición esperado en dB HL, referido al cero audiométrico de campo libre o campo difuso de ISO 389-7" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_hearing_threshold_es_dark.svg" alt="El modelo del umbral de audición: la edad, el sexo y un fractil poblacional alimentan la cadena de ISO 7029 — la desviación mediana respecto a los 18 años, las dispersiones superior e inferior su y sl, y el umbral del fractil — dando el nivel del umbral de audición esperado en dB HL, referido al cero audiométrico de campo libre o campo difuso de ISO 389-7" style="width:82%">

## 1. Umbral por edad (ISO 7029)

Para una persona mayor de 18 años, la desviación **mediana** del umbral de
audición respecto al valor a los 18 años crece como una ley de potencias de la
edad (ISO 7029, cláusula 4.2, Tabla 1):

$$
\Delta H_{md} = a\,(Y - 18)^{b},
$$

con coeficientes $a$, $b$ por frecuencia y sexo. La dispersión en torno a la
mediana se modela con dos semi-gaussianas cuyas desviaciones típicas $s_u$ (peor
que la mediana) y $s_l$ (mejor) son polinomios de grado cinco en $(Y - 18)$
(cláusula 4.3, Tablas 2–5). Cualquier **fractil poblacional** $Q$ se obtiene del
cuantil normal estándar $z(Q)$ (cláusula 4.4): $\Delta H_Q = \Delta H_{md} +
z(Q)\,s$, usando $s_u$ cuando $z \ge 0$ y $s_l$ en caso contrario.

```python
import phonometry as ph

# Desviación mediana del umbral de un hombre de 65 años, todas las frecuencias audiométricas.
result = ph.age_threshold(65, "male", fractile=0.5)
print(result.median.round(1))     # [ 6.6  7.6  8.  9.  10.4 13.4 16.3 21.6 26.2 33.7 39.5]
print(result.median[8].round(1))  # 26.2 dB a 4000 Hz

# El decil que peor oye (percentil 90) a 4000 Hz:
print(ph.age_threshold(65, "male", fractile=0.9).threshold[8].round(1))  # 50.3
```

La pérdida es mayor en las altas frecuencias y crece con la edad — el
audiograma descendente clásico de la presbiacusia. Hombres y mujeres siguen
coeficientes distintos (el argumento `sex`), y puede pedirse un subconjunto de
las frecuencias audiométricas con `frequencies=`.

## 2. Umbral de referencia de la audición (ISO 389-7)

El cero audiométrico no es un nivel de presión sonora fijo: depende de cómo
llega el sonido al oyente. La Tabla 1 de ISO 389-7:2006 da el umbral de
referencia para escucha de **campo libre** (incidencia frontal) y **campo
difuso**.

```python
import phonometry as ph

print(ph.reference_threshold("free-field"))
# [22.1 11.4  4.4  2.4  2.4  2.4 -1.3 -5.8 -5.4  4.3 12.6]
print(ph.reference_threshold("diffuse-field")[4])   # 0.8 dB a 1000 Hz
```

Ambos campos coinciden en baja frecuencia y divergen por encima de 1 kHz
aproximadamente, donde la resonancia del canal auditivo y la difracción de la
cabeza hacen del campo libre frontal la condición más sensible (un umbral más
bajo) en torno a 3–4 kHz.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_threshold_es.png" alt="Dos paneles. Izquierda: la desviación mediana del umbral de audición de ISO 7029 para hombres a los 20, 40, 60 y 80 años en un eje de audiograma invertido, con la banda del 10 al 90 por ciento en torno a la curva de 70 años; la pérdida se acentúa hacia las altas frecuencias y con la edad. Derecha: el umbral de referencia de campo libre y campo difuso de ISO 389-7, que coinciden por debajo de 1 kHz y divergen por encima, con un mínimo cerca de 3 a 4 kHz" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_threshold_es_dark.png" alt="Dos paneles. Izquierda: la desviación mediana del umbral de audición de ISO 7029 para hombres a los 20, 40, 60 y 80 años en un eje de audiograma invertido, con la banda del 10 al 90 por ciento en torno a la curva de 70 años; la pérdida se acentúa hacia las altas frecuencias y con la edad. Derecha: el umbral de referencia de campo libre y campo difuso de ISO 389-7, que coinciden por debajo de 1 kHz y divergen por encima, con un mínimo cerca de 3 a 4 kHz" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph
from phonometry.hearing import AUDIOMETRIC_FREQUENCIES as f

# En una línea, la distribución por edad:
ph.age_threshold(70, "male", 0.5).plot()
plt.show()

# A mano, ambos paneles:
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
for age in (20, 40, 60, 80):
    r = ph.age_threshold(age, "male", 0.5)
    ax1.plot(f, r.median, "o-", label=f"{age} yr")
ax1.set_xscale("log"); ax1.invert_yaxis(); ax1.legend()

ax2.plot(f, ph.reference_threshold("free-field"), "o-", label="Free-field")
ax2.plot(f, ph.reference_threshold("diffuse-field"), "s--", label="Diffuse-field")
ax2.set_xscale("log"); ax2.legend()
plt.show()
```

</details>

El `AgeThresholdResult` lleva la `median`, las dispersiones `spread_upper` y
`spread_lower`, y el `threshold` en el fractil pedido, y su `.plot()` dibuja la
mediana con la banda del 10–90 %. El desplazamiento permanente del umbral
inducido por ruido de ISO 1999 — que añade una componente de ruido sobre esta
componente de edad — es un tema aparte.

---

**Normas.** ISO 7029:2017, *Statistical distribution of hearing thresholds
related to age and gender* — la mediana (cláusula 4.2, Tabla 1), la dispersión
en torno a la mediana (cláusula 4.3, Tablas 2–5) y su aplicación (cláusula 4.4).
ISO 389-7:2006, *Reference zero for the calibration of audiometric equipment —
Reference threshold of hearing under free-field and diffuse-field listening
conditions* (Tabla 1).
