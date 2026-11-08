---
title: "Entornos"
description: "Dónde funciona phonometry y cómo se instala en cada sitio: pip y uv, conda, Jupyter, JupyterLite, Docker y los comprobadores de tipos."
---

phonometry es Python puro sobre NumPy y SciPy, se publica como un único wheel
para todos los sistemas operativos y necesita Python 3.12 o posterior. El
mismo paquete se instala, por tanto, allí donde funcionen ellos: en un entorno
virtual de un portátil, en un contenedor de un servidor o en un cuaderno
dentro de una pestaña del navegador. Lo que cambia de un sitio a otro es cómo
llegan sus dependencias y cuáles de los extras opcionales pueden seguirlas.
Cada página de esta sección trata un sitio, con órdenes que se han ejecutado
allí.

| Dónde | Cómo llega phonometry | Qué funciona | Qué no |
|---|---|---|---|
| [pip y uv](/phonometry/es/start/environments/pip-and-uv/) | `python -m pip install "phonometry[full]"` en un entorno virtual, o `uv add "phonometry[full]"` | todo; `[torch]` añade las simulaciones FDTD sobre PyTorch | no se queda nada fuera |
| [conda y mamba](/phonometry/es/start/environments/conda/) | las dependencias desde conda-forge y después `python -m pip install "phonometry[full]"` | todo, también pytorch de conda-forge | no se queda nada fuera |
| [Jupyter y JupyterLab](/phonometry/es/start/environments/jupyter/) | `python -m pip install jupyterlab "phonometry[full]"` | tablas de los resultados, figuras en línea, fichas y vídeos en cuanto está ffmpeg | un kernel arrancado con `PYTHONWARNINGS=error` |
| [JupyterLite y Pyodide](/phonometry/es/start/environments/jupyterlite/) | `%pip install "phonometry[plot,report,audio]"` en la primera celda | métricas, tablas, figuras, fichas, WAV y FLAC, FDTD con NumPy | `[perf]`, `[torch]` y `[full]`, el vídeo y cualquier dispositivo de cálculo que no sea `"cpu"` |
| [Docker y servidores](/phonometry/es/start/environments/docker/) | un entorno virtual dentro de una imagen `python:3.13-slim` | todo, con cualquier usuario y sobre una raíz de solo lectura con un `/tmp` escribible | no se queda nada fuera |
| [Comprobación de tipos](/phonometry/es/start/environments/type-checking/) | nada que añadir: el wheel trae `py.typed` | `mypy --strict` y el modo estricto de pyright, con cualquier NumPy que acepte la biblioteca | los campos de las simulaciones FDTD y los argumentos de palabra clave que `.plot()` pasa a matplotlib, con tipo `Any` |

## Avisos convertidos en errores

Importar phonometry y cada uno de sus dominios no emite ningún aviso, así que
un programa, una batería de tests o un cuaderno pueden convertir los avisos en
errores desde la primera línea. Todos los avisos que da la biblioteca son
`phonometry.PhonometryWarning`, y eso permite convertir en errores los de la
biblioteca sin convertir los de cualquier otro paquete:

```python
import warnings

import numpy as np
import phonometry
from phonometry import filters

fs = 48000
x = np.sin(2 * np.pi * 1000.0 * np.arange(fs) / fs)
with warnings.catch_warnings():
    warnings.simplefilter("error", phonometry.PhonometryWarning)
    try:
        filters.octave_filter(x, fs, fraction=3, limits=[12.0, 25000.0])
    except filters.FilterBankWarning as warning:
        print(warning)   # Low sampling rate: fs = 48000 Hz cannot hold the 25 kHz band, ...
```

Los límites que se piden aquí pasan de la mitad de la frecuencia de muestreo,
y el banco lo avisa; una llamada que se queda por debajo no lanza nada. Ese
filtro más estrecho es el que conviene en JupyterLite, donde el matplotlib que
trae Pyodide emite al dibujar un aviso de obsolescencia propio que un
`warnings.simplefilter("error")` general convierte en error.

## Una GPU

Ninguna de estas páginas la trata. [Dónde se calcula una
simulación](/phonometry/es/simulation/compute/) explica qué necesita cada
dispositivo de las simulaciones FDTD, desde los wheels de PyTorch hasta el de
CuPy para una GPU de NVIDIA, y cómo una simulación vuelve a NumPy cuando falta
su dispositivo.

## Las páginas

- [pip y uv](/phonometry/es/start/environments/pip-and-uv/): un entorno virtual, cada extra y lo que trae, torch sin CUDA, un proyecto de uv y la instalación desde un clon.
- [conda y mamba](/phonometry/es/start/environments/conda/): las dependencias con sus nombres de conda-forge y después phonometry con pip en el mismo entorno.
- [Jupyter y JupyterLab](/phonometry/es/start/environments/jupyter/): el kernel, las tablas de los resultados, las figuras en línea y en SVG, los vídeos, las fichas y cómo se ven los avisos en una celda.
- [JupyterLite y Pyodide](/phonometry/es/start/environments/jupyterlite/): qué se instala con micropip, qué funciona en el navegador y qué no, y cómo se construye un sitio de JupyterLite.
- [Docker y servidores](/phonometry/es/start/environments/docker/): una imagen ligera, cualquier identificador de usuario, una raíz de solo lectura y ffmpeg para los vídeos.
- [Comprobación de tipos](/phonometry/es/start/environments/type-checking/): qué ven mypy y pyright con cualquier NumPy que acepte la biblioteca, las opciones que comprueban y dónde el tipo es más amplio que el valor.
