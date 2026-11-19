<!-- Written by `make llms` from site/src/content/docs/start/environments/conda.md: edit that page and its Spanish twin, then run `make llms`. -->

← [Documentation index](../../README.md) · Published at https://phonometry.dev/start/environments/conda/

# conda and mamba

phonometry installs from PyPI. In a
[conda](https://docs.conda.io/projects/conda/en/stable/) environment, take its
dependencies from [conda-forge](https://conda-forge.org/) first, then install
phonometry with the environment's own pip: pip finds every requirement already
there and adds phonometry alone, so NumPy, SciPy and the rest stay conda-forge
builds.

Checked on 17 November 2026 with phonometry 4.0.0 from PyPI, in the
`condaforge/miniforge3` image: conda 26.9.4 and mamba 2.9.0, Python 3.13.18
with NumPy 2.5.5 from conda-forge, and Python 3.14.10 with pytorch 2.14.1.

## An environment with every extra

```bash
conda create -n acoustics -c conda-forge python=3.13 numpy scipy matplotlib-base numba reportlab svglib pysoundfile
conda activate acoustics
python -m pip install "phonometry[full]"
```

pip reports each requirement as already satisfied and installs phonometry
only. `conda list` then shows phonometry with the channel `pypi` beside the
conda-forge packages, and `python -m pip check` reports nothing broken.
[mamba](https://mamba.readthedocs.io/en/latest/) takes the same arguments:
`mamba create -n acoustics -c conda-forge ...` builds the same environment.
Python 3.12, 3.13 and 3.14 all work. conda-forge publishes no Python 3.12 or
newer for 32-bit Windows or 32-bit Linux, so phonometry installs there with
pip alone, `[plot,report,audio]` in place of `[full]`, as [pip and
uv](pip-and-uv.md) says.

## The extras under their conda-forge names

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
calls `soundfile`. Install the conda-forge packages of the extras you want
before pip runs. A dependency still missing when pip runs comes from PyPI
instead, and `conda list` shows it with the channel `pypi` beside the
conda-forge NumPy.

A feature whose dependency is missing names both spellings:

```text
ImportError: Plotting requires matplotlib. Install it with: pip install "phonometry[plot]" (conda: conda install -c conda-forge matplotlib-base)
```

In a conda environment, the second one is the command to run.

## pytorch

On a machine without a GPU, conda-forge installs its CPU build of pytorch, so
no index has to be named:

```bash
conda create -n fdtd -c conda-forge python=3.14 numpy scipy pytorch array-api-compat
conda activate fdtd
python -m pip install "phonometry[torch]"
```

pip again installs phonometry alone, and an FDTD run on
`Compute(device="torch:cpu")` gives the same pressures as the NumPy run.
