---
title: "Primeros pasos"
description: "Instala phonometry y ejecuta tu primer análisis de octava fraccional."
---

## Instalación

**Opción 1: Desde PyPI (recomendada)**

```bash
pip install phonometry
```

Extras opcionales:

```bash
pip install phonometry[plot]   # matplotlib, para las gráficas de respuesta
pip install phonometry[perf]  # numba, ponderación temporal 'impulse' más rápida
pip install phonometry[full]  # ambos
```

**Opción 2: Clonar e instalar**

```bash
git clone https://github.com/jmrplens/phonometry.git
cd phonometry
pip install .
```

**Opción 3: Submódulo de git**

```bash
git submodule add https://github.com/jmrplens/phonometry.git
# Después, instálalo en modo editable para usarlo desde tu proyecto
pip install -e ./phonometry
```

## Uso básico: análisis en tercios de octava

Analiza una señal y obtén el nivel de presión sonora (SPL) por banda de frecuencia.

```python
import numpy as np
from phonometry import octavefilter

fs = 48000
t = np.linspace(0, 1, fs, endpoint=False)
# Señal compuesta: 100 Hz + 1000 Hz
signal = np.sin(2 * np.pi * 100 * t) + np.sin(2 * np.pi * 1000 * t)

# Aplicar el banco de filtros de 1/3 de octava
spl, freq = octavefilter(signal, fs=fs, fraction=3)

print(f"Bandas: {freq}")
print(f"SPL [dB]: {spl}")
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_fraction_3.png" alt="Análisis en tercios de octava de una señal multitono con la PSD cruda de fondo" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_fraction_3_dark.png" alt="Análisis en tercios de octava de una señal multitono con la PSD cruda de fondo" style="width:80%">

*Ejemplo de análisis espectral en tercios de octava de una señal compleja.*

## Analizar un archivo de audio

```python
from scipy.io import wavfile
from phonometry import octavefilter

# Cargar un archivo WAV estándar
fs, signal = wavfile.read("measurement.wav")

# Analizar
# Nota: para obtener valores SPL reales debes calibrar la entrada.
# Consulta la guía de calibración.
spl, freq = octavefilter(signal, fs=fs, fraction=3)
```

El audio entero (por ejemplo, datos int16 de un WAV) se convierte internamente a
float64, así que es seguro pasar directamente la salida de `wavfile.read`.

## Siguientes pasos

- [Bancos de filtros](/phonometry/es/guides/filter-banks/) — elige una arquitectura e inspecciona sus respuestas
- [Calibración y dBFS](/phonometry/es/guides/calibration/) — obtén valores SPL reales
- [Referencia de la API](/phonometry/es/reference/api/) — todos los parámetros de cada función
