← [Documentation index](../../README.md)

# Environments

phonometry is pure Python on top of NumPy and SciPy, published as one wheel
for every operating system, and it needs Python 3.12 or newer. The same
package therefore installs wherever those run, from a virtual environment on a
laptop to a container on a server or a notebook in a browser tab. What changes
from one place to the next is how its dependencies arrive and which of the
optional extras can follow them. The pages of this section take one place
each, with commands that were run there.

| Where | How phonometry arrives | What runs | What does not |
|---|---|---|---|
| [pip and uv](pip-and-uv.md) | `python -m pip install "phonometry[full]"` in a virtual environment, or `uv add "phonometry[full]"` | everything; `[torch]` adds the FDTD engines on PyTorch | nothing is left out |
| [conda and mamba](conda.md) | the dependencies from conda-forge, then `python -m pip install "phonometry[full]"` | everything, pytorch from conda-forge included | nothing is left out |
| [Jupyter and JupyterLab](jupyter.md) | `python -m pip install jupyterlab "phonometry[full]"` | record tables, inline figures, fiches, videos once ffmpeg is installed | a kernel started with `PYTHONWARNINGS=error` |
| [JupyterLite and Pyodide](jupyterlite.md) | `%pip install "phonometry[plot,report,audio]"` in the first cell | metrics, record tables, figures, fiches, WAV and FLAC, FDTD on NumPy | `[perf]`, `[torch]` and `[full]`, video, every compute device but `"cpu"` |
| [Docker and servers](docker.md) | a virtual environment inside a `python:3.13-slim` image | everything, under any user id and on a read-only root with a writable `/tmp`, from wheels on x86-64 and ARM64 | the wheels on the image's six other architectures, where pip builds NumPy, SciPy and most extras from source |
| [Type checking](type-checking.md) | nothing to add: the wheel ships `py.typed` | `mypy --strict` and pyright's strict mode, on every NumPy the library accepts | the FDTD field arrays and the keyword arguments `.plot()` hands to matplotlib, typed `Any` |

## Warnings as errors

Importing phonometry and every one of its domains raises no warning, so a
program, a test suite or a notebook can run with warnings turned into errors
from the first line. Every warning the library itself gives is a
`phonometry.PhonometryWarning`, which lets you make the library's warnings
errors without making errors of every other package's:

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

The limits asked for here reach past half the sample rate, which the bank
reports; a call that stays below it raises nothing. That narrower filter is
the one to use in JupyterLite, where the matplotlib Pyodide ships gives a
deprecation warning of its own while it draws, which a blanket
`warnings.simplefilter("error")` turns into an error.

## A GPU

None of these pages covers one. [Where a simulation
runs](../../simulation/compute.md) says what each device of the FDTD
engines needs, from the PyTorch wheels to CuPy's for an NVIDIA GPU, and how a
run falls back to NumPy when its device is missing.

## The pages

- [pip and uv](pip-and-uv.md): a virtual environment, each extra and what it brings, torch without CUDA, a uv project and an install from a clone.
- [conda and mamba](conda.md): the dependencies under their conda-forge names, then phonometry with pip in the same environment.
- [Jupyter and JupyterLab](jupyter.md): the kernel, record tables, inline and SVG figures, videos, fiches and how warnings show in a cell.
- [JupyterLite and Pyodide](jupyterlite.md): what installs with micropip, what runs in a browser and what cannot, and building a JupyterLite site.
- [Docker and servers](docker.md): a slim image, any user id, a read-only root file system and ffmpeg for videos.
- [Type checking](type-checking.md): what mypy and pyright see on every NumPy the library accepts, the choices they check and where a type is wider than its value.
