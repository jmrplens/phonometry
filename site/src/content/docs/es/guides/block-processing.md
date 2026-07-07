---
title: "Procesado por bloques"
description: "Flujos de streaming con estado de filtro conservado entre bloques."
---

Las clases `OctaveFilterBank`, `WeightingFilter` (para ponderación A, C o Z) y
`TimeWeighting` admiten procesado por bloques (streaming): el estado interno del
filtro se conserva entre llamadas, de modo que las salidas concatenadas por
bloques coinciden con una única pasada sobre la señal completa.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/block_processing_continuity_es.png" alt="Procesado por bloques con estado igual al resultado continuo frente a bloques independientes que reinician el transitorio" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/block_processing_continuity_es_dark.png" alt="Procesado por bloques con estado igual al resultado continuo frente a bloques independientes que reinician el transitorio" style="width:80%">

*Con `stateful=True` las salidas concatenadas por bloques coinciden exactamente
con el resultado continuo; sin estado, cada frontera de bloque reinicia el
transitorio del filtro.*

Crea un banco con estado usando `stateful=True`. El estado interno se inicializa
a cero por defecto, pero puede inicializarse al régimen permanente de la
respuesta al escalón (como `scipy.signal.sosfilt_zi`) con `steady_ic=True`.

Notas al usar un `OctaveFilterBank` con estado:

- El detrending debe desactivarse en procesado por bloques (`detrend=False`), ya
  que puede introducir discontinuidades entre bloques.
- El remuestreo no está soportado en procesado por bloques: usa `resample=False`.
- `zero_phase=True` es incompatible con el modo stateful (el filtrado
  bidireccional necesita la señal completa).
- Un `WeightingFilter` con estado usa el diseño bilineal clásico
  (`high_accuracy=False`); consulta
  [Ponderación frecuencial](/phonometry/es/guides/weighting/).

## Ejemplo

Este ejemplo procesa un WAV por bloques con [`soundfile`](https://pysoundfile.readthedocs.io/),
una dependencia opcional (`pip install soundfile`). Sirve cualquier fuente de bloques
— `scipy.io.wavfile` con troceado manual, o una función de captura en vivo.

```python
import soundfile as sf
from phonometry import OctaveFilterBank, WeightingFilter

fs = 48000
octavefilter = OctaveFilterBank(fs, 1, stateful=True, resample=False)
afilter = WeightingFilter(fs, "A", stateful=True)

for block in sf.blocks("measurement.wav", blocksize=256, overlap=0):

    # Aplicar el filtro A
    weighted = afilter.filter(block)

    # Dividir en bandas de octava
    block_spl, _, block_output = octavefilter.filter(weighted, sigbands=True, detrend=False)

    # procesado posterior de la señal
    ...
```

## Ponderación temporal entre bloques

Usa la clase `TimeWeighting` (el estado se lleva automáticamente):

```python
from phonometry import TimeWeighting

tw = TimeWeighting(fs, mode="fast")
for block in audio_blocks:
    envelope = tw.process(block)
```

O gestiona el estado tú mismo con la API funcional — consulta
[Ponderación temporal](/phonometry/es/guides/time-weighting/#procesado-por-bloques).

## Estado multicanal

Todas las clases con estado gestionan entrada multicanal `(channels, samples)`:
el estado se reserva de forma perezosa en la primera llamada para ajustarse al
número de canales, y se realoja si este cambia (p. ej. pasar de estéreo a mono
reinicia el estado).

## Patrón de sonómetro en tiempo real

El bucle de streaming canónico — ponderar, obtener la envolvente e informar
bloque a bloque con todo el estado conservado entre llamadas:

```python
import numpy as np
from phonometry import TimeWeighting, WeightingFilter

fs, block = 48000, 4800  # bloques de 100 ms
aw = WeightingFilter(fs, "A", stateful=True)
env = TimeWeighting(fs, mode="fast")  # la clase es inherentemente stateful

for x in audio_stream(block):            # tu callback de captura
    y = env.process(aw.filter(x))
    spl = 10 * np.log10(y[..., -1] / (2e-5) ** 2)  # LAF instantáneo
    display(spl)
```

### Restricciones del modo con estado

| Opción | Comportamiento con estado | Motivo |
| :--- | :--- | :--- |
| `detrend` | debe ser `False` | El detrending por bloque crea discontinuidades en las fronteras |
| `resample` | debe ser `False` | El remuestreador no conserva estado |
| `zero_phase` | no soportado | El filtrado bidireccional necesita la señal completa |
| `high_accuracy` (ponderación) | por defecto se resuelve a `False`; pasar `True` explícito lanza `ValueError` | El remuestreo polifásico interno es incompatible con bloques |
| `steady_ic` | opcional | Arranca los filtros en el régimen permanente de la respuesta al escalón |
