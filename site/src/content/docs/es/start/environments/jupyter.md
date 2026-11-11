---
title: "Jupyter y JupyterLab"
description: "Usa phonometry en Jupyter y JupyterLab: el kernel y los extras, las tablas de los resultados, figuras en línea y en SVG, vídeos, fichas y avisos en una celda."
---

Un cuaderno ejecuta phonometry en un kernel de IPython corriente, así que se
instala igual que en cualquier otro sitio; lo que añade el cuaderno es cómo se
muestra un resultado bajo una celda. [En un
cuaderno](/phonometry/es/start/getting-started/#en-un-cuaderno), en Primeros
pasos, recorre una primera celda y la tabla que muestra; esta página es el
resto de lo que encuentra quien trabaja en un cuaderno.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab "phonometry[full]"
jupyter lab
```

Ese único entorno contiene JupyterLab, el kernel de IPython que arranca y
phonometry con todos los extras salvo `[torch]`.

## Un resultado se muestra como tabla

El valor de la última línea de una celda se muestra como una tabla de sus
campos, con sus unidades, y la línea de debajo dice qué puede dibujar el
resultado:

```python
import numpy as np
from phonometry import building, filters, io

fs = 48000
t = np.arange(fs) / fs
x = 0.4 * np.sin(2 * np.pi * 1000.0 * t)
bands = filters.octave_filter(x, fs, fraction=3)
bands       # la última línea de la celda: el cuaderno muestra su tabla
```

## Figuras

`.plot()` dibuja bajo la celda con el backend en línea, sin `plt.show()`. La
celda imprime además los ejes que devuelve, como
`<Axes: title={'center': 'Band levels'}, ...>`; un punto y coma tras la
llamada deja solo la figura. Las figuras salen en PNG, y una línea en una
celda pasa la sesión a SVG:

```py
%config InlineBackend.figure_formats = ["svg"]
bands.plot();
```

Un `.plot()` que lanza un error, por ejemplo por una palabra clave mal escrita
como `colour=`, no deja bajo la celda ninguna figura a medio dibujar, solo el
error.

## Fichas

```python
rating = building.weighted_rating(
    [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58]
)
rating.report("rating.pdf")
```

El PDF se escribe en la ruta que le das, relativa al directorio de trabajo
del cuaderno; `[report]` lo escribe y `[plot]` dibuja su gráfica.

## Vídeos

`io.write_video` y las funciones que escriben animaciones FDTD ejecutan
ffmpeg, un programa que pip no instala. En Debian llega con los paquetes del
sistema, con `apt install ffmpeg`, y [Escribir
vídeos](/phonometry/es/io/videos/) da la orden para conda, macOS y Windows.
Las clases de visualización del propio IPython muestran después el archivo
bajo la celda:

```python
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure

fig = Figure(figsize=(3.2, 2.4), dpi=100)
ax = fig.add_subplot()
phase = np.linspace(0.0, 2.0 * np.pi, 200)
(line,) = ax.plot(phase, np.sin(phase))


def update(k):
    line.set_ydata(np.sin(phase - 0.2 * k))
    return (line,)


animation = FuncAnimation(fig, update, frames=30, interval=50)
io.write_video("wave.mp4", animation)
io.write_video("wave.gif", animation, video=io.VideoOptions(quality="small"))
```

```py
from IPython.display import Image, Video, display

display(Video("wave.mp4", embed=True))  # un MP4 o un WebM, incrustado en el cuaderno
display(Image(filename="wave.gif"))     # un GIF
```

Una celda muestra solo el valor de su última línea, así que los dos pasan por
`display`: como dos líneas sueltas, la celda mostraría el GIF y no el vídeo.

## Avisos en una celda

Un aviso de la biblioteca nombra la línea de la celda que hizo la llamada, y
aparece bajo cada celda que la hace, no solo bajo la primera:

```text
/tmp/ipykernel_2485/1280619122.py:1: FilterBankWarning: Low sampling rate: fs = 48000 Hz cannot hold the 25 kHz band, whose upper edge 28184 Hz is above fs/2 = 24000 Hz; it was left out of the bank.
  wide = filters.octave_filter(x, fs, fraction=3, limits=[12.0, 25000.0])
```

Para que los avisos lancen un error, pon el filtro en una celda. Todos:

```py
import warnings

warnings.simplefilter("error")
```

o solo los de la biblioteca, con `warnings.simplefilter("error",
phonometry.PhonometryWarning)`. No arranques el kernel con
`PYTHONWARNINGS=error`: el propio kernel se detiene entonces en un
DeprecationWarning de su bucle de eventos antes de responder al cuaderno, y el
cuaderno informa de un kernel que ha muerto.

## VS Code y Colab

Los dos ejecutan los cuadernos sobre un kernel de IPython, así que lo que
muestra esta página debería valer también allí. No se ha probado en ninguno
de los dos.
