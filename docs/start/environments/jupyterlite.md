← [Documentation index](../../README.md)

# JupyterLite and Pyodide

JupyterLite runs a notebook in a browser tab, on Pyodide: CPython compiled to
WebAssembly, with nothing to install on the machine. phonometry is pure
Python, so it installs there with micropip and runs on the NumPy, SciPy and
matplotlib that Pyodide builds for the browser. What cannot follow it is
anything that needs a compiled package Pyodide does not build, or a program
of its own.

## Installing in a notebook

```py
%pip install "phonometry[plot,report,audio]"
```

The cell prints nothing when it succeeds. numpy, scipy, matplotlib and
soundfile come from Pyodide's own builds, the last one with libsndfile
compiled for the browser; reportlab and svglib are pure Python and come from
PyPI.

**Name every extra in the first install.** micropip leaves the extras of a
package it already installed alone: once phonometry is there, a later
`%pip install "phonometry[report]"` installs nothing, and prints nothing
either. To add what a later extra would have brought, name its packages:

```py
%pip install reportlab svglib
```

and `%pip install soundfile` for `[audio]`. A message for a missing extra
spells its command as `pip install "phonometry[...]"`; in a JupyterLite cell
it runs with a `%` in front.

## What runs in the browser

Every domain imports, and the record tables, `.plot()` under the cell and
`.report()` work as in Jupyter. WAV and FLAC files are written and read back
in the notebook's own folder. The FDTD engines step on NumPy.

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

## What does not

- **`[perf]`, `[torch]` and `[full]` do not install.** micropip finds no
  wheel of numba or torch it can run in the browser, and one requirement it
  cannot meet stops the whole install:

  ```text
  ValueError: Can't find a pure Python 3 wheel for 'numba>=0.63.0; python_version >= "3.14" and extra == "perf"'.
  ```

  Without numba, the `impulse` time weighting runs as plain Python and says
  nothing about it.
- **No compute device but `"cpu"`.** `Compute(device="torch:cpu")` raises
  `ComputeDeviceError: device 'torch:cpu' is not available in Pyodide; only
  'cpu' is`; with `fallback=True` the run steps on NumPy and warns
  `ComputeFallbackWarning` instead.
- **No video.** A browser cannot start a program, so `io.write_video` and the
  FDTD animation writers raise `FFmpegNotFoundError: Pyodide cannot start
  programs, so it cannot run ffmpeg; write the video from Python on a
  desktop, a server or a node`.

To make the library's warnings errors in a JupyterLite notebook, filter on
its own class, `warnings.simplefilter("error",
phonometry.PhonometryWarning)`. A blanket `warnings.simplefilter("error")`
also turns into an error a deprecation warning that Pyodide's matplotlib
3.10.8 gives while it draws, and `.plot()` then fails under the cell.

## Pyodide without JupyterLite

In a page or a Node.js script that loads Pyodide itself, micropip is one of
the packages of the Pyodide distribution, which Pyodide does not load until
it is asked to. The script loads it from JavaScript, after `loadPyodide()`:

```js
const pyodide = await loadPyodide();
await pyodide.loadPackage("micropip");
```

and the Python it then hands to `pyodide.runPythonAsync()` installs
phonometry, with the same extras and the same limits:

```py
import micropip

await micropip.install("phonometry[plot,report,audio]")
```

Without the `loadPackage` step, `import micropip` fails with
`ModuleNotFoundError: No module named 'micropip'`.

## A JupyterLite site of your own

A course or a lab can publish its notebooks as a JupyterLite site, built once
and served as static files. The build needs `jupyter-server` beside the two
JupyterLite packages, or it stops with "jupyter-server is not installed. You
cannot add custom content to jupyterlite":

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlite-core jupyterlite-pyodide-kernel jupyter-server
jupyter lite build --contents content --output-dir _output
```

`content` holds the notebooks, and `_output` is the site to serve. The build
also prints two notices, about `libarchive-c` and `jupyterlab_server`, that
change nothing in the site. A wheel placed in a `pypi` folder of the
directory the build runs in is published with the site, and `%pip install`
takes it from there before PyPI.
