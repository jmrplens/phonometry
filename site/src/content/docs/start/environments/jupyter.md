---
title: "Jupyter and JupyterLab"
description: "Use phonometry in Jupyter and JupyterLab: the kernel and the extras, record tables, inline and SVG figures, videos, fiches and warnings in a cell."
---

A notebook runs phonometry in an ordinary IPython kernel, so it installs as
anywhere else; what the notebook adds is how a result shows itself under a
cell. [In a notebook](/phonometry/start/getting-started/#in-a-notebook), in
Getting Started, walks through a first cell and the table it displays; this
page is the rest of what a notebook user meets.

## Installing

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab "phonometry[full]"
jupyter lab
```

On Windows the environment is activated with `.venv\Scripts\activate.bat`
in cmd or `.venv\Scripts\Activate.ps1` in PowerShell in place of
`source .venv/bin/activate`.
PowerShell on a Windows client refuses scripts under its default
execution policy, so `Activate.ps1` runs there once
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` has allowed local ones;
cmd needs no such step.

That one environment holds JupyterLab, the IPython kernel it starts and
phonometry with every extra but `[torch]`.

On 32-bit Windows numba is not supported, and neither is `[full]`, which
holds it: `python -m pip install jupyterlab "phonometry[plot,report,audio]"`
installs JupyterLab with the other three extras. PyPI has no 32-bit Windows
wheel of SciPy, matplotlib or kiwisolver, nor of psutil and pywinpty, which
JupyterLab needs there, nor of PyYAML on Python 3.14, so pip builds those
from source there, which takes a C and a C++ compiler, a Fortran compiler for
SciPy and Rust for pywinpty.

## A result shows a table

The value on the last line of a cell displays as a table of its fields, with
their units, and the line under it names what the result can draw:

```python
import numpy as np
from phonometry import building, filters, io

fs = 48000
t = np.arange(fs) / fs
x = 0.4 * np.sin(2 * np.pi * 1000.0 * t)
bands = filters.octave_filter(x, fs, fraction=3)
bands       # the last line of the cell: the notebook shows its table
```

## Figures

`.plot()` draws under the cell through the inline backend, with no
`plt.show()`. The cell also prints the axes it returns, as
`<Axes: title={'center': 'Band levels'}, ...>`; a semicolon after the call
leaves the figure alone. The figures come out as PNG; one line in a cell
switches the session to SVG:

```py
%config InlineBackend.figure_formats = ["svg"]
bands.plot();
```

A `.plot()` that raises, on a misspelt keyword such as `colour=` for instance,
leaves no half-drawn figure under the cell, only the error.

## Fiches

```python
rating = building.weighted_rating(
    [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58]
)
rating.report("rating.pdf")
```

The PDF is written to the path you give, relative to the notebook's working
directory; `[report]` writes it and `[plot]` draws its figure.

## Videos

`io.write_video` and the FDTD animation writers run ffmpeg, a program that
pip does not install. On Debian it comes from the system's packages, with
`apt install ffmpeg`, and [Writing videos](/phonometry/io/videos/) gives the
command for conda, macOS and Windows. IPython's own display classes then show
the file under the cell:

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

display(Video("wave.mp4", embed=True))  # an MP4 or a WebM, embedded in the notebook
display(Image(filename="wave.gif"))     # a GIF
```

A cell displays the value of its last line only, so both go through
`display`: as two bare lines, the cell would show the GIF and not the video.

## Warnings in a cell

A warning the library gives names the line of the cell that made the call,
and it shows under every cell that makes one, not only the first:

```text
/tmp/ipykernel_2485/1280619122.py:1: FilterBankWarning: Low sampling rate: fs = 48000 Hz cannot hold the 25 kHz band, whose upper edge 28184 Hz is above fs/2 = 24000 Hz; it was left out of the bank.
  wide = filters.octave_filter(x, fs, fraction=3, limits=[12.0, 25000.0])
```

To have warnings raise instead, set the filter in a cell. All of them:

```py
import warnings

warnings.simplefilter("error")
```

or the library's alone, `warnings.simplefilter("error",
phonometry.PhonometryWarning)`. Do not start the kernel with
`PYTHONWARNINGS=error`: the kernel itself then stops on a DeprecationWarning
of its own event loop before it answers the notebook, and the notebook
reports a kernel that died.

## VS Code and Colab

Both run notebooks on an IPython kernel, so what this page shows should
apply there as well. Neither was tried for this page.
