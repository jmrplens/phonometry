---
title: "Procesado por bloques"
description: "Flujos de streaming con estado de filtro conservado entre bloques."
---

Las clases `OctaveFilterBank`, `WeightingFilter` (para ponderación A, C o Z) y
`TimeWeighting` admiten procesado por bloques (streaming): el estado interno del
filtro se conserva entre llamadas, de modo que las salidas concatenadas por
bloques coinciden con una única pasada sobre la señal completa.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/block_processing_continuity.png" alt="Procesado por bloques con estado igual al resultado continuo frente a bloques independientes que reinician el transitorio" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/block_processing_continuity_dark.png" alt="Procesado por bloques con estado igual al resultado continuo frente a bloques independientes que reinician el transitorio" style="width:80%">

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
  [Ponderación frecuencial](/PyOctaveBand/es/guides/weighting/).

## Ejemplo

```python
import soundfile as sf
from pyoctaveband import OctaveFilterBank, WeightingFilter

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
from pyoctaveband import TimeWeighting

tw = TimeWeighting(fs, mode="fast")
for block in audio_blocks:
    envelope = tw.process(block)
```

O gestiona el estado tú mismo con la API funcional — consulta
[Ponderación temporal](/PyOctaveBand/es/guides/time-weighting/#procesado-por-bloques).

## Estado multicanal

Todas las clases con estado gestionan entrada multicanal `(channels, samples)`:
el estado se reserva de forma perezosa en la primera llamada para ajustarse al
número de canales, y se realoja si este cambia (p. ej. pasar de estéreo a mono
reinicia el estado).
