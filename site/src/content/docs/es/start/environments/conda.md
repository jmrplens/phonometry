---
title: "conda y mamba"
description: "Usa phonometry en un entorno de conda o mamba: sus dependencias desde conda-forge con los nombres que tienen allí y después phonometry con pip."
---

phonometry se instala desde PyPI. En un entorno de conda, toma primero sus
dependencias de conda-forge y después instala phonometry con el pip del propio
entorno: pip encuentra ya instalado cada requisito y añade solo phonometry, de
modo que NumPy, SciPy y los demás siguen siendo compilaciones de conda-forge.

## Un entorno con todos los extras

```bash
conda create -n acoustics -c conda-forge python=3.13 numpy scipy matplotlib-base numba reportlab svglib pysoundfile
conda activate acoustics
python -m pip install "phonometry[full]"
```

pip da cada requisito por satisfecho e instala solo phonometry. `conda list`
muestra entonces phonometry con el canal `pypi` junto a los paquetes de
conda-forge, y `python -m pip check` no encuentra nada roto. mamba acepta los
mismos argumentos: `mamba create -n acoustics -c conda-forge ...` construye el
mismo entorno. Funcionan Python 3.12, 3.13 y 3.14.
conda-forge no publica Python 3.12 ni posterior para Windows ni para Linux de
32 bits, así que allí phonometry se instala solo con pip, con
`[plot,report,audio]` en lugar de `[full]`, como dice [pip y
uv](/phonometry/es/start/environments/pip-and-uv/).

## Los extras con sus nombres de conda-forge

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
paquete que PyPI llama `soundfile`. Instala los paquetes de conda-forge de los
extras que quieras antes de que se ejecute pip. Una dependencia que todavía
falte cuando pip se ejecuta llega de PyPI, y `conda list` la muestra con el
canal `pypi` junto al NumPy de conda-forge.

Una función a la que le falta su dependencia da las dos órdenes:

```text
ImportError: Plotting requires matplotlib. Install it with: pip install "phonometry[plot]" (conda: conda install -c conda-forge matplotlib-base)
```

En un entorno de conda, la segunda es la que hay que ejecutar.

## pytorch

En una máquina sin GPU, conda-forge instala su compilación de pytorch para
CPU, así que no hace falta indicar ningún índice:

```bash
conda create -n fdtd -c conda-forge python=3.14 numpy scipy pytorch array-api-compat
conda activate fdtd
python -m pip install "phonometry[torch]"
```

pip vuelve a instalar solo phonometry, y una simulación FDTD con
`Compute(device="torch:cpu")` da las mismas presiones que con NumPy.
