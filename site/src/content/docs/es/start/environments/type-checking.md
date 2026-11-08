---
title: "Comprobación de tipos"
description: "Comprueba con mypy o pyright los tipos del código que usa phonometry: el wheel trae py.typed, se comprueban opciones y números y los campos FDTD son Any."
---

phonometry trae sus tipos dentro del wheel, con la marca `py.typed` que le
indica a un comprobador de tipos que los lea, así que mypy y pyright
comprueban una llamada a la biblioteca sin instalar nada más. Cada módulo
público declara lo que publica, y los dominios perezosos de
`import phonometry as ph` los ve tanto el comprobador como la ejecución.

## Un script que pasa los modos estrictos

```python
import numpy as np

from phonometry import filters, io, signals, simulation

fs = 48000
x = 0.1 * np.sin(2 * np.pi * 1000.0 * np.arange(fs) / fs)

bands = filters.octave_filter(x, fs, fraction=3)
levels = bands.require_levels()          # un array, donde bands.levels puede ser None

recording = io.Signal(x, fs)
weighted = filters.WeightingFilter(fs, "A").filter(recording)   # entra un Signal, sale un Signal
level = float(signals.leq(weighted))      # leq devuelve un float, o un array si hay varios canales
print(f"Leq = {level:.1f} dB en {levels.size} bandas")

engine = simulation.FDTD2D(c=343.0, dx=0.01, shape=(64, 64))
pressure = engine.numpy_field("p")       # un array de NumPy; engine.p es el del propio dispositivo
print(pressure.shape)
```

`mypy --strict` y pyright, en su modo básico y en el estricto, no señalan nada
en este script, en Python 3.12 a 3.14.

## Qué detecta un comprobador

Un texto donde la biblioteca espera números, una opción fuera de las que
acepta un parámetro, una escritura en una tabla publicada y un campo que una
fila de catálogo no tiene se rechazan antes de ejecutar el código. En
`wrong.py`:

```py
from phonometry import filters, materials, signals

signals.leq("not a signal")
filters.WeightingFilter(48000, "Q")
row = next(iter(materials.PUBLISHED_ABSORPTION.values()))
materials.PUBLISHED_ABSORPTION["mine"] = row
print(row.density)
```

`mypy wrong.py` dice:

```text
wrong.py:3: error: Argument 1 to "leq" has incompatible type "str"; expected "Signal | complex | NestedSequence[complex] | SupportsNumericArray | NestedSequence[SupportsNumericArray]"  [arg-type]
wrong.py:4: error: Argument 2 to "WeightingFilter" has incompatible type "Literal['Q']"; expected "Literal['A', 'C', 'B', 'D', 'G', 'AU', '468', 'Z']"  [arg-type]
wrong.py:6: error: Unsupported target for indexed assignment ("Mapping[str, AbsorptionSpectrum]")  [index]
wrong.py:7: error: "AbsorptionSpectrum" has no attribute "density"  [attr-defined]
Found 4 errors in 1 file (checked 1 source file)
```

y pyright rechaza las mismas cuatro líneas.

## Donde el tipo es más amplio que el valor

- **Un campo que puede faltar.** `bands.levels` es `None` en una llamada que
  no pidió niveles, así que su tipo dice `np.ndarray | None`; el
  `require_levels()` del resultado devuelve el array, o lanza un ValueError
  que explica por qué no lo hay. `require_bands()` hace lo mismo con las
  señales de cada banda.
- **El tipo que devuelve un filtro.** `WeightingFilter.filter()` y
  `ParametricEQ.filter()` devuelven un `Signal` para un `Signal` y un array
  para un array, y el comprobador ve cuál.
- **Los campos de las simulaciones FDTD.** `engine.p`, `engine.vx` y los
  demás campos que avanza un motor FDTD son arrays de la biblioteca con la que
  calcula: un array de NumPy, uno de CuPy o un tensor de PyTorch. Un
  comprobador los lee como `Any`. `engine.numpy_field("p")` devuelve una
  copia de NumPy en cualquier dispositivo, con su tipo.

## Completitud

`pyright --verifytypes phonometry --ignoreexternal` lee el paquete instalado
como lo hace el comprobador de un usuario y le da un 100 %: cada símbolo que
exporta el paquete tiene un tipo conocido. La CI del repositorio ejecuta la
misma orden sobre el wheel construido y falla por debajo del 100 %.
