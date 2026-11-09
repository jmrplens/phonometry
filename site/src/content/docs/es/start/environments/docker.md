---
title: "Docker y servidores"
description: "Ejecuta phonometry en un contenedor o un servidor: una imagen ligera con un entorno virtual, cualquier usuario, una raíz de solo lectura y ffmpeg para vídeos."
---

phonometry no necesita del sistema operativo nada más que Python: todos los
extras se instalan desde wheels, incluida la libsndfile que va dentro del
wheel de soundfile, así que basta con una imagen `python:*-slim`. El único
paquete del sistema que merece la pena añadir es ffmpeg, y solo para los
vídeos.

## Una imagen

```dockerfile
FROM python:3.13-slim
RUN python -m venv /opt/venv \
 && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/python -m pip install --no-cache-dir "phonometry[full]"
ENV PATH=/opt/venv/bin:$PATH MPLCONFIGDIR=/tmp/matplotlib
COPY analyse.py /app/analyse.py
WORKDIR /tmp
CMD ["python", "/app/analyse.py"]
```

El entorno virtual saca del registro de la construcción el aviso de pip sobre
ejecutarse como root. `analyse.py` hace las veces de tu propio trabajo; este
escribe un espectro en bandas, su figura y una ficha:

```python
"""Un trabajo por lotes: un análisis en tercios de octava, su figura y una ficha."""
from pathlib import Path

import numpy as np

from phonometry import building, filters

out = Path("out")
out.mkdir(exist_ok=True)

fs = 48000
t = np.arange(2 * fs) / fs
x = 0.1 * np.sin(2 * np.pi * 1000 * t)

bands = filters.octave_filter(x, fs, fraction=3)
bands.plot().figure.savefig(out / "bands.png")
impulse = filters.time_weighting(x, fs, mode="impulse")
rating = building.weighted_rating(
    [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58]
)
rating.report(out / "rating.pdf")
print(f"{len(bands.frequencies)} bands, impulse maximum {float(np.max(impulse)):.4f}")
print("wrote", sorted(p.name for p in out.iterdir()))
```

```bash
docker build -t acoustics .
mkdir -p out
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/tmp/out" acoustics
```

```text
33 bands, impulse maximum 0.0092
wrote ['bands.png', 'rating.pdf']
```

El trabajo escribe en `out` bajo su directorio de trabajo, `/tmp/out` en el
contenedor, y `--rm` borra el contenedor con sus archivos cuando el trabajo
termina. El montaje `-v` lleva esa carpeta a tu máquina como `out` en el
directorio desde el que lo ejecutas, donde la figura y la ficha se quedan;
`--user` ejecuta el trabajo como tú, así que los archivos son tuyos y no de
root. Crea antes la carpeta: la que Docker crea para el montaje pertenece a
root, y el trabajo, que corre como tú, no puede escribir en ella.

matplotlib elige por sí solo su backend Agg en un contenedor sin pantalla, así
que nada tiene que fijar `MPLBACKEND`.

## Cualquier usuario, cualquier sistema de archivos

La imagen ejecuta el mismo trabajo como root, como un identificador de usuario
cualquiera (`docker run --user 12345:12345`), como `nobody` y sobre un sistema
de archivos raíz de solo lectura con un `/tmp` escribible
(`docker run --read-only --tmpfs /tmp`). Una carpeta montada para los
resultados tiene que ser escribible para el usuario con el que corre el
trabajo, como lo es `out` para ti arriba. Dos cachés y un directorio deciden
lo callado que lo hace:

- **`MPLCONFIGDIR`.** matplotlib guarda su configuración y su caché bajo el
  directorio personal del usuario. Para un usuario sin directorio personal
  escribible imprime "Matplotlib created a temporary cache directory at ..."
  cada vez que arranca; la línea `ENV` de arriba lo lleva a `/tmp`, y no dice
  nada.
- **La caché de numba.** numba guarda el núcleo compilado de `impulse` junto
  al paquete o bajo el directorio personal. Donde no puede escribir en
  ninguno de los dos, compila el núcleo una vez en cada proceso y no dice
  nada. Con `NUMBA_CACHE_DIR=/tmp/numba` lo escribe ahí, para los procesos que
  vengan después en el mismo contenedor.
- **Una raíz de solo lectura.** El trabajo necesita algún sitio donde
  escribir: aquí su directorio de trabajo, `/tmp`, que `--tmpfs /tmp`
  mantiene escribible, y la carpeta `out` montada dentro de él desde tu
  máquina. Sin ningún montaje escribible, el trabajo se detiene en su propio
  `out.mkdir`.

## Vídeos

`io.write_video` y las funciones que escriben animaciones FDTD ejecutan
ffmpeg. Instálalo desde los paquetes de la propia imagen antes del entorno
virtual:

```dockerfile
FROM python:3.13-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv \
 && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/python -m pip install --no-cache-dir "phonometry[full]"
ENV PATH=/opt/venv/bin:$PATH MPLCONFIGDIR=/tmp/matplotlib
```

WebM y MP4 se codifican entonces en la CPU, igual como `nobody` que sobre una
raíz de solo lectura con un `/tmp` escribible. [Escribir
vídeos](/phonometry/es/io/videos/) trata los codificadores y un nodo con GPU.

## Servidores e hilos

Un servidor que atiende peticiones en un grupo de hilos puede importar desde
esos hilos los dominios que necesita, varios a la vez. [Enviar una simulación
a un nodo remoto](/phonometry/es/simulation/remote-node/) trata una simulación
FDTD que el servidor no debe calcular por sí mismo.
