---
title: "Niveles integrados y estadísticos"
description: "Leq, LAeq, percentiles L10/L50/L90 y espectrogramas de octava."
---

Métricas de ruido ambiental calculadas directamente sobre la señal cruda
(calibrada).

## Leq y LAeq

El nivel continuo equivalente integra la presión al cuadrado durante el tiempo
de medición:

$$
L_{eq} = 10\log_{10}\!\left(\frac{1}{T}\int_0^T \frac{p^2(t)}{p_0^2}\,dt\right) \text{ dB}, \qquad p_0 = 20\ \mu\text{Pa}
$$

y $L_{Aeq}$ es la misma integral tras ponderar A la señal. $L_N$ es el nivel
superado el $N\,\%$ del tiempo — el percentil $(100-N)$ de la distribución del
nivel con ponderación temporal.

```python
from pyoctaveband import leq, laeq

# Nivel continuo equivalente de toda la grabación
level = leq(signal, calibration_factor=sensitivity)

# Leq ponderado A (la métrica estándar de ruido ambiental)
la = laeq(signal, fs, calibration_factor=sensitivity)
```

Ambas aceptan señales 1D (devuelven un escalar) o arrays 2D
`[channels, samples]` (devuelven un nivel por canal), y admiten `dbfs=True` para
análisis digital a fondo de escala (la calibración no aplica en modo dBFS).

## Niveles percentiles (LN)

`ln_levels` calcula niveles estadísticos a partir de la envolvente con
ponderación temporal: **L10** es el nivel superado el 10 % del tiempo (picos de
eventos), **L50** la mediana y **L90** el nivel de fondo.

```python
from pyoctaveband import ln_levels

stats = ln_levels(signal, fs, n=(10, 50, 90), weighting="A")
print(f"LA10={stats[10]:.1f}  LA50={stats[50]:.1f}  LA90={stats[90]:.1f} dB")
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/ln_levels_example.png" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/ln_levels_example_dark.png" alt="Historia del nivel Fast de un ruido fluctuante con los niveles estadísticos L10, L50 y L90 marcados" style="width:80%">

*L10 sigue los picos de los eventos, L50 el nivel mediano y L90 el fondo.*

Opciones: `mode` selecciona la balística de la envolvente (`'fast'`, `'slow'`,
`'impulse'`), `weighting` aplica antes la ponderación A/C, y
`calibration_factor`/`dbfs` se comportan como en `leq`. El transitorio de ataque
del integrador (~2τ) se descarta antes de calcular los percentiles.

## Espectrograma de octavas (niveles vs tiempo)

Análisis de octava fraccional en tiempo corto: un nivel por banda y ventana,
alineado en el tiempo entre bandas.

```python
from pyoctaveband import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3)
levels, freq, times = bank.spectrogram(signal, window_time=0.125, overlap=0.5)
# levels: (bandas, ventanas) — listo para pcolormesh(times, freq, levels)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/spectrogram_example.png" alt="Espectrograma en tercios de octava de un barrido logarítmico con dos ráfagas de tono" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/spectrogram_example_dark.png" alt="Espectrograma en tercios de octava de un barrido logarítmico con dos ráfagas de tono" style="width:80%">

*Un barrido logarítmico y dos ráfagas de tono, resueltos en el tiempo y en
bandas normalizadas de tercio de octava.*

- Una entrada multicanal `(channels, samples)` devuelve `(channels, bands, frames)`.
- `times` contiene el centro de cada ventana en segundos.
- `mode='peak'` da niveles de pico por ventana en lugar de RMS.
- `zero_phase=True` filtra las bandas hacia delante y atrás para que el retardo
  de grupo por banda no desplace las ventanas (solo análisis offline).

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
mesh = ax.pcolormesh(times, freq, levels, shading="auto")
ax.set_yscale("log")
ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Frecuencia [Hz]")
fig.colorbar(mesh, label="Nivel [dB]")
```

Consulta [Calibración y dBFS](/PyOctaveBand/es/guides/calibration/) para
convertir unidades digitales a SPL físico, y
[Ponderación temporal](/PyOctaveBand/es/guides/time-weighting/) para los
detalles de la envolvente.
