---
title: "Por qué PyOctaveBand"
description: "Verificación de conformidad con IEC 61672-1 y comparación con otras librerías."
---

Cómo se relaciona la ponderación temporal de PyOctaveBand con la norma
**IEC 61672-1:2013** (Electroacústica — Sonómetros), y en qué se diferencia de
otras librerías de Python como `python-acoustics`. Esta página resume el
análisis publicado originalmente en la
[incidencia #38](https://github.com/jmrplens/PyOctaveBand/issues/38).

## Filosofía de diseño

La ponderación temporal estándar se define como una **función continua del
tiempo** mediante la ecuación diferencial

$$
\tau \frac{dy(t)}{dt} + y(t) = x^2(t)
$$

que corresponde a un filtro paso-bajo de primer orden estable con un polo en el
semiplano izquierdo ($s = -1/\tau$).

| | PyOctaveBand | python-acoustics |
| :--- | :--- | :--- |
| Salida | Envolvente continua (un valor por muestra) | Salida escalonada (un valor cada τ segundos) |
| Unidades de entrada | Presión sonora cruda (Pa); se eleva al cuadrado internamente | Se espera la magnitud energética (Pa²) como entrada |
| Filtro | Promediado exponencial estable (polo en $s=-1/\tau$) | Diseño teóricamente inestable (polo en el semiplano derecho) estabilizado reiniciando el estado cada τ segundos |
| Comportamiento | Ponderación temporal IEC verdadera | Más cercano a un integrador por bloques ($L_{eq,\tau}$) |

Un polo en el eje real negativo corresponde a una respuesta al impulso
exponencial decreciente ($h(t) \propto e^{-t/\tau}$) — exactamente lo que
significa "ponderación temporal exponencial": los eventos pasados se olvidan
exponencialmente. Un polo en el eje real positivo crece sin límite; el reinicio
por bloques lo oculta, pero cambia la naturaleza de la medición.

## Verificación frente a IEC 61672-1 (ráfagas de tono)

La prueba rigurosa para la ponderación temporal es la **respuesta a ráfaga de
tono** (IEC 61672-1, Tabla 3), usando una ráfaga senoidal de 4 kHz referida al
nivel de régimen estacionario.

**Resultados de PyOctaveBand (FAST):**

| Duración de la ráfaga | Objetivo IEC (dB) | PyOctaveBand (dB) | Error (dB) | Estado |
| :--- | :--- | :--- | :--- | :--- |
| 200 ms | −1.0 | −0.98 | +0.02 | ✅ PASA |
| 50 ms | −4.8 | −4.82 | −0.02 | ✅ PASA |
| 10 ms | −11.1 | −11.14 | −0.04 | ✅ PASA |
| 1 ms | −20.9 | −20.99 | −0.09 | ✅ PASA |

**Resultados de python-acoustics (FAST, pasando la señal al cuadrado como
requiere esa librería):**

| Duración de la ráfaga | Objetivo IEC (dB) | python-acoustics (dB) | Error (dB) | Estado |
| :--- | :--- | :--- | :--- | :--- |
| 200 ms | −1.0 | −0.97 | +0.03 | ✅ PASA |
| 50 ms | −4.8 | −3.93 | **+0.87** | ⚠️ FALLA |
| 10 ms | −11.1 | −10.90 | +0.20 | ✅ PASA |
| 1 ms | −20.9 | −20.90 | +0.00 | ✅ PASA |

PyOctaveBand mantiene alta precisión en todos los casos. El enfoque por bloques
se desvía significativamente (> 0,8 dB) en la ráfaga de 50 ms porque los bloques
de 125 ms no pueden resolver con precisión eventos transitorios cortos — el
resultado depende de cómo se alinee la ráfaga con los límites de los bloques.

## Qué significa esto en la práctica

- Si necesitas **envolventes Fast/Slow/Impulse conformes con la norma**
  (comportamiento de sonómetro, un nivel por muestra), usa
  [`time_weighting`](/PyOctaveBand/es/guides/time-weighting/) de PyOctaveBand.
- Si necesitas un **Leq promediado por intervalos**, esa es una métrica
  distinta e igualmente válida — puedes calcularla con
  [`leq`](/PyOctaveBand/es/guides/levels/) sobre segmentos consecutivos.
- Ambas librerías son útiles; simplemente responden preguntas distintas. La
  discrepancia reportada en la incidencia #38 proviene de comparar una
  envolvente continua con un integrador por bloques, no de un error de
  implementación.

## Más allá de la ponderación temporal

El mismo enfoque de "primero la norma" se aplica a toda la librería:

- Los bancos de filtros sitúan sus puntos de −3 dB en los bordes de banda de
  **ANSI S1.11** para todas las arquitecturas (incluidos Chebyshev II y Bessel,
  donde la parametrización cruda de scipy no lo haría).
- La ponderación A/C se mantiene dentro de las tolerancias de **clase 1 de
  IEC 61672-1** hasta 16 kHz a las frecuencias de muestreo habituales, gracias
  al sobremuestreo interno (consulta
  [Ponderación frecuencial](/PyOctaveBand/es/guides/weighting/)).
- Los objetivos de ráfaga de tono IEC de arriba están integrados en la batería
  de tests, de modo que las regresiones se detectan en CI.
