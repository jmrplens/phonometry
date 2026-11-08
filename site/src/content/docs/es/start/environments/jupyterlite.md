---
title: "JupyterLite y Pyodide"
description: "phonometry en el navegador con JupyterLite o Pyodide: los extras que instala micropip, qué funciona allí, qué no y cómo publicar un sitio de JupyterLite."
---

JupyterLite ejecuta un cuaderno en una pestaña del navegador, sobre Pyodide:
CPython compilado a WebAssembly, sin nada que instalar en la máquina.
phonometry es Python puro, así que se instala allí con micropip y funciona
sobre el NumPy, el SciPy y el matplotlib que Pyodide compila para el
navegador. Lo que no puede acompañarlo es lo que necesita un paquete
compilado que Pyodide no compila, o un programa propio.

## Instalación en un cuaderno

```py
%pip install "phonometry[plot,report,audio]"
```

La celda no imprime nada cuando todo va bien. numpy, scipy, matplotlib y
soundfile llegan de las compilaciones del propio Pyodide, el último con
libsndfile compilado para el navegador; reportlab y svglib son Python puro y
llegan de PyPI.

**Nombra todos los extras en la primera instalación.** micropip no toca los
extras de un paquete que ya instaló: con phonometry instalado, un
`%pip install "phonometry[report]"` posterior no instala nada, y tampoco
imprime nada. Para añadir lo que habría traído un extra posterior, nombra sus
paquetes:

```py
%pip install reportlab svglib
```

y `%pip install soundfile` para `[audio]`. Un mensaje por un extra que falta
escribe su orden como `pip install "phonometry[...]"`; en una celda de
JupyterLite se ejecuta con un `%` delante.

## Qué funciona en el navegador

Todos los dominios se importan, y las tablas de los resultados, `.plot()`
bajo la celda y `.report()` funcionan como en Jupyter. Los archivos WAV y
FLAC se escriben y se vuelven a leer en la propia carpeta del cuaderno. Las
simulaciones FDTD calculan con NumPy.

```python
import numpy as np
from phonometry import building, filters, io

fs = 48000
x = 0.4 * np.sin(2 * np.pi * 1000.0 * np.arange(fs) / fs)
bands = filters.octave_filter(x, fs, fraction=3)
io.write("tone.wav", 0.5 * x, fs)
tone = io.read("tone.wav")
rating = building.weighted_rating(
    [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58]
)
rating.report("rating.pdf")
```

## Qué no funciona

- **`[perf]`, `[torch]` y `[full]` no se instalan.** micropip no encuentra
  ningún wheel de numba ni de torch que pueda ejecutarse en el navegador, y
  un solo requisito que no puede cumplir detiene la instalación entera:

  ```text
  ValueError: Can't find a pure Python 3 wheel for 'numba>=0.63.0; python_version >= "3.14" and extra == "perf"'.
  ```

  Sin numba, la ponderación temporal `impulse` se ejecuta en Python puro y no
  dice nada.
- **Ningún dispositivo de cálculo salvo `"cpu"`.** `Compute(device="torch:cpu")`
  lanza `ComputeDeviceError: device 'torch:cpu' is not available in Pyodide;
  only 'cpu' is`; con `fallback=True` la simulación calcula con NumPy y avisa
  con `ComputeFallbackWarning`.
- **No hay vídeo.** Un navegador no puede arrancar un programa, así que
  `io.write_video` y las funciones que escriben animaciones FDTD lanzan
  `FFmpegNotFoundError: Pyodide cannot start programs, so it cannot run
  ffmpeg; write the video from Python on a desktop, a server or a node`.

Para convertir en errores los avisos de la biblioteca en un cuaderno de
JupyterLite, filtra por su propia clase, `warnings.simplefilter("error",
phonometry.PhonometryWarning)`. Un `warnings.simplefilter("error")` general
convierte también en error un aviso de obsolescencia que el matplotlib 3.10.8
de Pyodide emite al dibujar, y entonces `.plot()` falla bajo la celda.

## Pyodide sin JupyterLite

En una página o un script de Node.js que carga Pyodide por su cuenta,
micropip es uno de los paquetes de la distribución de Pyodide, que Pyodide no
carga hasta que se le pide. El script lo carga desde JavaScript, después de
`loadPyodide()`:

```js
const pyodide = await loadPyodide();
await pyodide.loadPackage("micropip");
```

y el Python que luego le pasa a `pyodide.runPythonAsync()` instala
phonometry, con los mismos extras y los mismos límites:

```py
import micropip

await micropip.install("phonometry[plot,report,audio]")
```

Sin el paso de `loadPackage`, `import micropip` falla con
`ModuleNotFoundError: No module named 'micropip'`.

## Un sitio de JupyterLite propio

Un curso o un laboratorio puede publicar sus cuadernos como un sitio de
JupyterLite, que se construye una vez y se sirve como archivos estáticos. La
construcción necesita `jupyter-server` junto a los dos paquetes de
JupyterLite, o se detiene con "jupyter-server is not installed. You cannot add
custom content to jupyterlite":

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlite-core jupyterlite-pyodide-kernel jupyter-server
jupyter lite build --contents content --output-dir _output
```

`content` contiene los cuadernos y `_output` es el sitio que hay que servir.
La construcción imprime además dos avisos, sobre `libarchive-c` y sobre
`jupyterlab_server`, que no cambian nada del sitio. Un wheel puesto en una
carpeta `pypi` del directorio donde se construye se publica con el sitio, y
`%pip install` lo toma de allí antes que de PyPI.
