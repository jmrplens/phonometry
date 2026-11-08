---
title: "pip and uv"
description: "Install phonometry with pip or uv on Python 3.12 to 3.14: each extra and what it brings, torch without CUDA, a uv project and an install from a clone."
---

phonometry installs from PyPI with pip or uv on Python 3.12, 3.13 and 3.14,
as one wheel with no compiled code of its own. Both tools land on the same
packages; the difference is how they keep a project's dependencies, and how
each is told to take torch from PyTorch's CPU index.

## pip in a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "phonometry[full]"
```

`python -m pip install phonometry` alone brings NumPy and SciPy and nothing
else; that is enough for every metric of the library. `python -m pip check`
reports no broken requirement afterwards, with or without extras. Check what
the environment imports:

```python
import phonometry

print(phonometry.__version__)   # the release you installed
```

## What each extra brings

| Extra | Brings | So that |
|---|---|---|
| `[plot]` | matplotlib | `.plot()` and the filter response plots draw |
| `[report]` | reportlab, svglib | `.report()` writes a PDF fiche; its figure panel also needs `[plot]` |
| `[audio]` | python-soundfile, whose wheel carries libsndfile | `phonometry.io` reads FLAC, AIFF, Ogg/Opus, MP3 and compressed WAV, and writes FLAC |
| `[perf]` | numba | the `impulse` time weighting runs compiled |
| `[full]` | all four above | every feature but the torch backend |
| `[torch]` | torch, array-api-compat | the FDTD engines step on PyTorch |

No extra needs a system package: on a bare `python:3.13-slim` image every one
of them installs and runs from its wheels, `[audio]` included. Without numba
the `impulse` time weighting runs as plain Python and says nothing about it.
A feature whose extra is missing says which one to install, with its pip and
its conda spelling:

```text
ImportError: Plotting requires matplotlib. Install it with: pip install "phonometry[plot]" (conda: conda install -c conda-forge matplotlib-base)
```

The oldest release of each dependency the library is tested with, on each
Python, is listed in [Getting
Started](/phonometry/start/getting-started/#from-pypi-recommended).

## torch without CUDA

`[full]` leaves `[torch]` out, because the torch wheels PyPI serves on Linux
bring gigabytes of CUDA libraries. On a Linux machine without an NVIDIA GPU,
install torch from PyTorch's CPU index first, then the extra, which keeps the
torch it finds, in the virtual environment made above:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install "phonometry[torch]"
```

The environment then holds the CPU build of torch and no NVIDIA package, and
an FDTD run on `Compute(device="torch:cpu")` gives the same pressures as the
NumPy run. [Where a simulation runs](/phonometry/simulation/compute/) covers the
other devices.

## From a clone

```bash
git clone https://github.com/jmrplens/phonometry.git
cd phonometry
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

pip builds the wheel with setuptools and no compiler, and the build also
passes under `PYTHONWARNINGS=error`.

## uv

`uv pip` takes the same requirements as pip, in an environment uv creates:

```bash
uv venv
uv pip install "phonometry[full]"
```

For torch, `--torch-backend cpu` tells uv to take torch from PyTorch's CPU
index, with no NVIDIA package:

```bash
uv pip install "phonometry[torch]" --torch-backend cpu
```

In a uv project, `uv add` writes the requirement into `pyproject.toml` and the
lock file, and `uv run` runs in the project's environment:

```bash
uv init acoustics
cd acoustics
uv add "phonometry[full]"
uv run python -c "import phonometry; print(phonometry.__version__)"
```

`uv add` resolves the same way in a project for Python 3.12, 3.13 or 3.14.

### torch from the CPU index in a project

Name the index in `pyproject.toml`, mark it explicit so that only torch is
taken from it, and route torch to it:

```toml
[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

Then add torch by name beside the extra:

```bash
uv add "phonometry[torch]" torch
```

The name matters. A source applies to a dependency the project names itself,
so `uv add "phonometry[torch]"` alone, with the same `pyproject.toml`, locks
the torch of PyPI's default index together with its CUDA and NVIDIA packages,
and says nothing about it.
