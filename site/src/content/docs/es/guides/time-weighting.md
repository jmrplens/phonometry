---
title: "Ponderación temporal"
description: "Balística Fast, Slow e Impulse según IEC 61672-1."
---

La medición precisa de SPL requiere capturar la energía en ventanas temporales
específicas. phonometry implementa las constantes de tiempo exactas de la norma
**IEC 61672-1:2013**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_weighting_analysis_es.png" alt="Respuestas de las ponderaciones temporales Fast, Slow e Impulse a una ráfaga de ruido" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_weighting_analysis_es_dark.png" alt="Respuestas de las ponderaciones temporales Fast, Slow e Impulse a una ráfaga de ruido" style="width:80%">

* **Fast (`fast`):** τ = 125 ms. Estándar para fluctuaciones de ruido.
* **Slow (`slow`):** τ = 1000 ms. Estándar para ruido estacionario.
* **Impulse (`impulse`):** balística **asimétrica**. 35 ms de subida para
  capturar ataques rápidos y 1500 ms de caída para facilitar la lectura.

```python
import numpy as np
from phonometry import time_weighting

# Calcular la envolvente de energía (valor cuadrático medio)
energy_envelope = time_weighting(signal, fs, mode='fast')
# dB SPL respecto a 20 μPa
spl_t = 10 * np.log10(energy_envelope / (2e-5)**2)
```

La balística Impulse asimétrica usa dos constantes — ataque rápido y caída
lenta — conmutando por muestra según el signo del cambio:

$$
y[n] = y[n-1] + \alpha \ (x^2[n] - y[n-1]), \qquad
\alpha = \begin{cases}1 - e^{-1/(f_s \cdot 0.035)} & x^2[n] > y[n-1]\\[2pt] 1 - e^{-1/(f_s \cdot 1.5)} & \text{en otro caso}\end{cases}
$$

## El detector exponencial

La aguja de un sonómetro no puede seguir la forma de onda de presión — muestra
un *valor cuadrático medio* móvil con memoria exponencial. Formalmente
(IEC 61672-1, 3.8):

$$
\tau\ \frac{dy}{dt} + y = x^2(t)
\quad\Longleftrightarrow\quad
y(t) = \frac{1}{\tau} \int_{-\infty}^{t} x^2(\xi)\ e^{-(t-\xi)/\tau}\ d\xi
$$

un paso-bajo de primer orden sobre la señal al cuadrado. La constante de tiempo
τ fija el compromiso: **Fast** (125 ms) sigue fluctuaciones del tipo del habla
y **Slow** (1 s) estabiliza la lectura para ruido cuasi estacionario. Tras un
escalón, la envolvente alcanza el 63 % de su valor final en un τ y ~99,8 %
tras 8τ — por eso los análisis de nivel descartan los primeros instantes de una
grabación.

### Parámetros de `time_weighting()` / `TimeWeighting`

| Parámetro | Tipo | Unidades | Rango / por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | presión (cualquier escala) | no vacío | Se eleva al cuadrado internamente; la salida es una envolvente cuadrática media |
| `fs` | int | Hz | > 0 | |
| `mode` | str | — | `'fast'` (por defecto), `'slow'`, `'impulse'` | τ = 125 ms / 1 s / ataque de 35 ms + caída de 1,5 s |
| `TimeWeighting(fs, mode)` (clase) | — | — | — | Variante con estado para streaming: `process(x)` conserva el estado del integrador entre bloques |

La salida tiene las unidades de $x^2$: toma `10*log10(y / p0**2)` para SPL o
usa las funciones de nivel, que lo hacen por ti.

## Balística verificada (IEC 61672-1, Tabla 4)

La respuesta de la envolvente Fast a ráfagas de tono de 4 kHz cae exactamente
sobre los valores de referencia de la norma — verificado en CI para duraciones
de 1 s a 1 ms (ponderaciones F y S, límites de aceptación de clase 1):

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_burst_iec_es.png" alt="Respuestas de la envolvente Fast a ráfagas de 200, 50 y 10 ms alcanzando exactamente los valores de la Tabla 4 de IEC 61672-1" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_burst_iec_es_dark.png" alt="Respuestas de la envolvente Fast a ráfagas de 200, 50 y 10 ms alcanzando exactamente los valores de la Tabla 4 de IEC 61672-1" style="width:80%">

## Estado inicial

Por defecto, el integrador exponencial parte del reposo (`y[-1] = 0`). Pasar
`initial_state=None` deja ese comportamiento por defecto, mientras que
`initial_state='zero'` lo solicita explícitamente. Si el segmento grabado
comienza con una señal estacionaria ya presente, puedes partir de la energía de
la primera muestra:

```python
energy_envelope = time_weighting(signal, fs, mode='fast', initial_state='first')
```

## Procesado por bloques

Para procesar por bloques, pasa el último valor de salida del bloque anterior
como `initial_state` del siguiente en lugar de reiniciar en cada bloque:

```python
state = None

for block in audio_blocks:
    energy_envelope = time_weighting(block, fs, mode='fast', initial_state=state)
    state = energy_envelope[-1]
```

Para bloques multicanal con el tiempo en el último eje, lleva un estado por
canal: usa `state = energy_envelope[..., -1]`. Un `initial_state` escalar se
aplica a todos los canales, mientras que un array debe coincidir (o difundirse)
con la forma sin el eje temporal, p. ej. `(n_channels,)` para una entrada de
forma `(n_channels, n_samples)`.

O deja que la clase `TimeWeighting` lleve el estado por ti:

```python
from phonometry import TimeWeighting

tw = TimeWeighting(fs, mode='fast')
for block in audio_blocks:
    energy_envelope = tw.process(block)
```

Las salidas concatenadas por bloques son exactamente iguales a una única llamada
continua (verificado para los tres modos, mono y multicanal). Llama a
`tw.reset()` para volver al reposo.

## Nota de rendimiento

El modo `impulse` usa un kernel asimétrico que se compila JIT cuando
[numba](https://numba.pydata.org/) está instalado (`pip install phonometry[perf]`).
Sin numba, un fallback en Python puro produce resultados idénticos, solo que más
lento.

Consulta [Niveles integrados y estadísticos](/phonometry/es/guides/levels/)
para las métricas Leq/LN construidas sobre estas envolventes, y
[Por qué phonometry](/phonometry/es/reference/why-phonometry/) para la
verificación con ráfagas de tono de IEC 61672-1.
