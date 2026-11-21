---
title: "conda y mamba"
description: "Instala phonometry desde conda-forge con conda o mamba: el paquete, sus extras con los nombres que tienen allí y pytorch sin CUDA."
---

phonometry está en [conda-forge](https://anaconda.org/conda-forge/phonometry).
En un entorno de [conda](https://docs.conda.io/projects/conda/en/stable/),
instálalo desde allí junto con los extras que quieras: NumPy, SciPy y los
paquetes de cada extra también son compilaciones de conda-forge, de modo que
nada del entorno llega de PyPI.

Comprobado el 21 de noviembre de 2026 con phonometry 4.0.1 de conda-forge, en
la imagen `condaforge/miniforge3`: conda 26.9.4 y mamba 2.9.0, Python 3.12.16,
3.13.18 y 3.14.10 con NumPy 2.5.5 y SciPy 1.18.1, y Python 3.14.10 con pytorch
2.14.1.

## Un entorno con todos los extras

```bash
conda create -n acoustics -c conda-forge python=3.13 phonometry matplotlib-base numba reportlab svglib pysoundfile pip
conda activate acoustics
```

`conda list` muestra phonometry con el canal `conda-forge`, como todos los
demás paquetes del entorno, y `python -m pip check` no encuentra nada roto. En
ese entorno `.plot()` dibuja, `.report()` escribe su ficha, `phonometry.io`
escribe y lee FLAC y la ponderación temporal `impulse` se ejecuta con numba.
[mamba](https://mamba.readthedocs.io/en/latest/) acepta los mismos argumentos:
`mamba create -n acoustics -c conda-forge ...` construye el mismo entorno. Para
añadir phonometry a un entorno que ya existe, ejecuta en él
`conda install -c conda-forge phonometry`.

Funcionan Python 3.12, 3.13 y 3.14. conda-forge no publica Python 3.12 ni
posterior para Windows ni para Linux de 32 bits, así que allí phonometry se
instala solo con pip, con `[plot,report,audio]` en lugar de `[full]`, como
dice [pip y uv](/es/start/environments/pip-and-uv/).

## Los extras con sus nombres de conda-forge

El paquete de conda depende solo de NumPy y SciPy, igual que
`pip install phonometry`. Cada extra es un paquete propio de conda-forge, y la
receta lo sujeta al mínimo que ese extra tiene en PyPI para Python 3.12:

| Extra | Paquetes de conda-forge |
|---|---|
| la instalación base | numpy, scipy |
| `[plot]` | matplotlib-base |
| `[report]` | reportlab, svglib, y matplotlib-base para la gráfica de la ficha |
| `[audio]` | pysoundfile, que trae libsndfile |
| `[perf]` | numba |
| `[torch]` | pytorch, array-api-compat |

`matplotlib-base` es matplotlib sin backend gráfico de escritorio, que es con
lo que dibuja la biblioteca; `pysoundfile` es el nombre en conda-forge del
paquete que PyPI llama `soundfile`. Instala los que quieras junto con
phonometry o en cualquier momento después.

Una función a la que le falta su dependencia da las dos órdenes:

```text
ImportError: Plotting requires matplotlib. Install it with: pip install "phonometry[plot]" (conda: conda install -c conda-forge matplotlib-base)
```

En un entorno de conda, la segunda es la que hay que ejecutar.

## pytorch

En una máquina sin GPU, conda-forge instala su compilación de pytorch para
CPU, así que no hace falta indicar ningún índice:

```bash
conda create -n fdtd -c conda-forge python=3.14 phonometry pytorch array-api-compat
conda activate fdtd
```

Una simulación FDTD con `Compute(device="torch:cpu")` da entonces las mismas
presiones que con NumPy, hasta el último bit.

## Una versión antes de que llegue a conda-forge

Una versión nueva llega a conda-forge cuando el bot de conda-forge ha abierto
la actualización en el
[feedstock de phonometry](https://github.com/conda-forge/phonometry-feedstock)
y se ha fusionado. Para tomarla de PyPI antes, instala primero las
dependencias desde conda-forge y después phonometry con el pip del propio
entorno:

```bash
conda create -n acoustics -c conda-forge python=3.13 numpy scipy matplotlib-base numba reportlab svglib pysoundfile pip
conda activate acoustics
python -m pip install "phonometry[full]"
```

Cuando cada requisito ya está instalado en la versión que pide la publicación,
pip instala solo phonometry, de modo que NumPy, SciPy y los extras siguen siendo
compilaciones de conda-forge; `conda list` muestra phonometry con el canal
`pypi`. Una dependencia que todavía falte, o más antigua de lo que pide la
versión nueva, llega de PyPI, y `conda list` la muestra también con el canal
`pypi`.
