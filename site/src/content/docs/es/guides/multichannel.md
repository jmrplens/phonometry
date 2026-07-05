---
title: "Multicanal y rendimiento"
description: "Análisis multicanal vectorizado y notas de rendimiento."
---

## Soporte multicanal

PyOctaveBand soporta de forma nativa señales multicanal (estéreo, 5.1, arrays de
micrófonos…) mediante **operaciones totalmente vectorizadas**. Los arrays de
entrada con forma `(N_channels, N_samples)` se procesan en paralelo, con
ganancias de rendimiento significativas frente a bucles iterativos.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_response_multichannel.png" width="80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_response_multichannel_dark.png" width="80%">

*Análisis simultáneo de una señal estéreo: canal izquierdo (ruido rosa) vs canal
derecho (barrido senoidal logarítmico).*

La convención es consistente en toda la librería: el tiempo siempre es el
**último eje**. Aplica a `octavefilter`, `OctaveFilterBank`, `weighting_filter`,
`time_weighting`, `leq`, `laeq`, `ln_levels` y `spectrogram`.

```python
import numpy as np
from pyoctaveband import octavefilter

stereo = np.stack([left, right])          # (2, n_samples)
spl, freq = octavefilter(stereo, fs, fraction=3)
# spl tiene forma (2, n_bands): una fila por canal
```

## Rendimiento: vectorización y caché

La clase `OctaveFilterBank` está muy optimizada para procesado en tiempo real y
por lotes. Usa vectorización NumPy para manejar arrays de audio multicanal
(p. ej. arrays de micrófonos de 64 canales) sin bucles Python explícitos.

```python
from pyoctaveband import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3, filter_type='butter')

# Propiedades calculadas
# bank.freq (centros), bank.freq_d (bordes inferiores), bank.freq_u (superiores), bank.sos

# Procesar múltiples señales de forma eficiente
for frame in stream:
    # detrend=True (por defecto) elimina el offset DC y mejora la precisión en graves
    spl, freq = bank.filter(frame, detrend=True)
```

Notas adicionales de rendimiento:

- **Caché de diseño**: `octavefilter()` reutiliza los diseños del banco entre
  llamadas con parámetros idénticos (caché LRU de 32 entradas), así que llamarla
  en bucle no rediseña el banco cada vez. `OctaveFilterBank` te da control
  explícito sobre el ciclo de vida del diseño.
- **Diezmado multitasa**: las bandas graves se filtran a una frecuencia diezmada,
  lo que es a la vez más rápido y numéricamente más estable (consulta
  [Teoría](/PyOctaveBand/es/reference/theory/)).
- **numba opcional**: el kernel del modo `impulse` de la ponderación temporal se
  compila JIT cuando numba está instalado (`pip install PyOctaveBand[perf]`).
