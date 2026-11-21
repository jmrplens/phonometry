---
title: "conda and mamba"
description: "Install phonometry from conda-forge with conda or mamba: the package, its extras under their conda-forge names, and pytorch without CUDA."
---

phonometry is on [conda-forge](https://anaconda.org/conda-forge/phonometry).
In a [conda](https://docs.conda.io/projects/conda/en/stable/) environment,
install it from there together with the extras you want: NumPy, SciPy and the
packages of every extra are conda-forge builds as well, so nothing in the
environment comes from PyPI.

Checked on 21 November 2026 with phonometry 4.0.1 from conda-forge, in the
`condaforge/miniforge3` image: conda 26.9.4 and mamba 2.9.0, Python 3.12.16,
3.13.18 and 3.14.10 with NumPy 2.5.5 and SciPy 1.18.1, and Python 3.14.10 with
pytorch 2.14.1.

## An environment with every extra

```bash
conda create -n acoustics -c conda-forge python=3.13 phonometry matplotlib-base numba reportlab svglib pysoundfile pip
conda activate acoustics
```

`conda list` shows phonometry with the channel `conda-forge`, as every other
package in the environment, and `python -m pip check` reports nothing broken.
In that environment `.plot()` draws, `.report()` writes its fiche,
`phonometry.io` writes and reads FLAC and the `impulse` time weighting runs on
numba. [mamba](https://mamba.readthedocs.io/en/latest/) takes the same
arguments: `mamba create -n acoustics -c conda-forge ...` builds the same
environment. To add phonometry to an environment that already exists, run
`conda install -c conda-forge phonometry` in it.

Python 3.12, 3.13 and 3.14 all work. conda-forge publishes no Python 3.12 or
newer for 32-bit Windows or 32-bit Linux, so phonometry installs there with pip
alone, `[plot,report,audio]` in place of `[full]`, as [pip and
uv](/start/environments/pip-and-uv/) says.

## The extras under their conda-forge names

The conda package depends on NumPy and SciPy only, as `pip install phonometry`
does. Each extra is a conda-forge package of its own, and the recipe holds it
to the floor the extra has on PyPI for Python 3.12:

| Extra | conda-forge packages |
|---|---|
| the base install | numpy, scipy |
| `[plot]` | matplotlib-base |
| `[report]` | reportlab, svglib, and matplotlib-base for the fiche's figure |
| `[audio]` | pysoundfile, which brings libsndfile |
| `[perf]` | numba |
| `[torch]` | pytorch, array-api-compat |

`matplotlib-base` is matplotlib without a GUI backend, which is what the
library draws with; `pysoundfile` is the conda-forge name of the package PyPI
calls `soundfile`. Install the ones you want with phonometry or at any time
after it.

A feature whose dependency is missing names both spellings:

```text
ImportError: Plotting requires matplotlib. Install it with: pip install "phonometry[plot]" (conda: conda install -c conda-forge matplotlib-base)
```

In a conda environment, the second one is the command to run.

## pytorch

On a machine without a GPU, conda-forge installs its CPU build of pytorch, so
no index has to be named:

```bash
conda create -n fdtd -c conda-forge python=3.14 phonometry pytorch array-api-compat
conda activate fdtd
```

An FDTD run on `Compute(device="torch:cpu")` then gives the same pressures as
the NumPy run, to the last bit.

## A release before it reaches conda-forge

A new release reaches conda-forge once conda-forge's bot has opened the update
on the [phonometry feedstock](https://github.com/conda-forge/phonometry-feedstock)
and it has been merged. To take it from PyPI before then, install the
dependencies from conda-forge first and phonometry with the environment's own
pip:

```bash
conda create -n acoustics -c conda-forge python=3.13 numpy scipy matplotlib-base numba reportlab svglib pysoundfile pip
conda activate acoustics
python -m pip install "phonometry[full]"
```

When every requirement is already there at the version the release asks for,
pip installs phonometry alone, so NumPy, SciPy and the extras stay conda-forge
builds; `conda list` shows phonometry with the channel `pypi`. A dependency
still missing, or older than the new release requires, comes from PyPI instead,
and `conda list` then shows it with the channel `pypi` too.
