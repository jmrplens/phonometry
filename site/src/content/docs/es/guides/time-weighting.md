---
title: "Ponderación temporal"
description: "Balística Fast, Slow e Impulse según IEC 61672-1."
---

La medición precisa de SPL requiere capturar la energía en ventanas temporales
específicas. PyOctaveBand implementa las constantes de tiempo exactas de la norma
**IEC 61672-1:2013**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/time_weighting_analysis.png" width="80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/time_weighting_analysis_dark.png" width="80%">

* **Fast (`fast`):** τ = 125 ms. Estándar para fluctuaciones de ruido.
* **Slow (`slow`):** τ = 1000 ms. Estándar para ruido estacionario.
* **Impulse (`impulse`):** balística **asimétrica**. 35 ms de subida para
  capturar ataques rápidos y 1500 ms de caída para facilitar la lectura.

```python
import numpy as np
from pyoctaveband import time_weighting

# Calcular la envolvente de energía (valor cuadrático medio)
energy_envelope = time_weighting(signal, fs, mode='fast')
# dB SPL respecto a 20 μPa
spl_t = 10 * np.log10(energy_envelope / (2e-5)**2)
```

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
from pyoctaveband import TimeWeighting

tw = TimeWeighting(fs, mode='fast')
for block in audio_blocks:
    energy_envelope = tw.process(block)
```

Las salidas concatenadas por bloques son exactamente iguales a una única llamada
continua (verificado para los tres modos, mono y multicanal). Llama a
`tw.reset()` para volver al reposo.

## Nota de rendimiento

El modo `impulse` usa un kernel asimétrico que se compila JIT cuando
[numba](https://numba.pydata.org/) está instalado (`pip install PyOctaveBand[perf]`).
Sin numba, un fallback en Python puro produce resultados idénticos, solo que más
lento.

Consulta [Niveles integrados y estadísticos](/PyOctaveBand/es/guides/levels/)
para las métricas Leq/LN construidas sobre estas envolventes, y
[Por qué PyOctaveBand](/PyOctaveBand/es/reference/why-pyoctaveband/) para la
verificación con ráfagas de tono de IEC 61672-1.
