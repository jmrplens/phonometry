← [Documentation index](../../README.md)

# Type checking

phonometry ships its types in the wheel, with the `py.typed` marker that tells
a type checker to read them, so mypy and pyright check a call into the
library with nothing else installed. Every public module declares what it
publishes, and the lazy domains of `import phonometry as ph` are visible to a
checker as well as at run time.

## A script under the strict modes

```python
import numpy as np

from phonometry import filters, io, signals, simulation

fs = 48000
x = 0.1 * np.sin(2 * np.pi * 1000.0 * np.arange(fs) / fs)

bands = filters.octave_filter(x, fs, fraction=3)
levels = bands.require_levels()          # an array, where bands.levels may be None

recording = io.Signal(x, fs)
weighted = filters.WeightingFilter(fs, "A").filter(recording)   # a Signal in, a Signal out
level = float(signals.leq(weighted))      # leq returns a float, or an array for several channels
print(f"Leq = {level:.1f} dB over {levels.size} bands")

engine = simulation.FDTD2D(c=343.0, dx=0.01, shape=(64, 64))
pressure = engine.numpy_field("p")       # a NumPy array; engine.p is the device's own
print(pressure.shape)
```

`mypy --strict` and pyright, in its basic mode and in its strict mode, report
nothing on this script, on Python 3.12 to 3.14 and with every NumPy the
library accepts there, from NumPy 2.0.2 on Python 3.12 to the newest. Before
NumPy 2.3, `np.ndarray` and the abstract scalar types such as `np.floating`
have no default type arguments, and a checker reads one written alone as
partly unknown; phonometry writes the dtype of every array it annotates
(`NDArray[np.float64]`), so a checker reads its types the same on every
NumPy.

## What a checker catches

A text where the library takes numbers, a choice outside the ones a
parameter accepts, a write into a published table and a field a catalogue
row does not have are all refused before the code runs. In `wrong.py`:

```py
from phonometry import filters, materials, signals

signals.leq("not a signal")
filters.WeightingFilter(48000, "Q")
row = next(iter(materials.PUBLISHED_ABSORPTION.values()))
materials.PUBLISHED_ABSORPTION["mine"] = row
print(row.density)
```

`mypy wrong.py` says:

```text
wrong.py:3: error: Argument 1 to "leq" has incompatible type "str"; expected "Signal | complex | NestedSequence[complex] | SupportsNumericArray | NestedSequence[SupportsNumericArray]"  [arg-type]
wrong.py:4: error: Argument 2 to "WeightingFilter" has incompatible type "Literal['Q']"; expected "Literal['A', 'C', 'B', 'D', 'G', 'AU', '468', 'Z']"  [arg-type]
wrong.py:6: error: Unsupported target for indexed assignment ("Mapping[str, AbsorptionSpectrum]")  [index]
wrong.py:7: error: "AbsorptionSpectrum" has no attribute "density"  [attr-defined]
Found 4 errors in 1 file (checked 1 source file)
```

and pyright refuses the same four lines.

## Where the types are wider than the value

- **A field that may be absent.** `bands.levels` is `None` for a call that
  asked for no level, so its type says `np.ndarray | None`; the result's
  `require_levels()` returns the array, or raises a ValueError that says why
  there is none. `require_bands()` does the same for the per-band waveforms.
- **The type a filter hands back.** `WeightingFilter.filter()` and
  `ParametricEQ.filter()` return a `Signal` for a `Signal` and an array for
  an array, and the checker sees which.
- **The FDTD fields.** `engine.p`, `engine.vx` and the other fields an FDTD
  engine steps are arrays of the library it steps on: a NumPy array, a CuPy
  array or a PyTorch tensor. A checker reads them as `Any`.
  `engine.numpy_field("p")` returns a NumPy copy on every device, typed as
  one.
- **The keyword arguments of a plot.** `.plot()` hands the keyword arguments
  it does not take itself on to matplotlib, typed `Any`, so a checker passes
  a misspelt one such as `bands.plot(colour="red")`, which matplotlib refuses
  with an AttributeError when the line runs.

## Completeness

`pyright --verifytypes phonometry --ignoreexternal` reads the installed
package as a user's checker does and scores it at 100% with every NumPy the
library accepts, from NumPy 2.0.2 on Python 3.12 to the newest: every symbol
the package exports has a known type. The repository's CI runs the same
command on the built wheel with the newest NumPy, and on the package
installed at the oldest versions each Python accepts, and fails below 100%.
