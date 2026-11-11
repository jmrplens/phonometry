---
title: "pip y uv"
description: "Instala phonometry con pip o uv en Python 3.12 a 3.14: cada extra y lo que trae, torch sin CUDA, un proyecto de uv y la instalación desde un clon."
---

phonometry se instala desde PyPI con pip o con uv en Python 3.12, 3.13 y
3.14, como un único wheel sin código compilado propio. Las dos herramientas
llegan a los mismos paquetes; lo que las distingue es cómo guardan las
dependencias de un proyecto y cómo se le indica a cada una que tome torch del
índice de CPU de PyTorch.

## pip en un entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "phonometry[full]"
```

`python -m pip install phonometry` a secas trae NumPy y SciPy y nada más, y
con eso basta para todas las métricas de la biblioteca. `python -m pip check`
no encuentra después ningún requisito roto, con extras o sin ellos. Para
comprobar qué importa el entorno:

```python
import phonometry

print(phonometry.__version__)   # la versión que has instalado
```

## Qué trae cada extra

| Extra | Trae | Para que |
|---|---|---|
| `[plot]` | matplotlib | `.plot()` y las gráficas de respuesta de los filtros dibujen |
| `[report]` | reportlab, svglib | `.report()` escriba una ficha PDF; su panel de gráfica necesita también `[plot]` |
| `[audio]` | python-soundfile, cuyo wheel lleva libsndfile | `phonometry.io` lea FLAC, AIFF, Ogg/Opus, MP3 y WAV comprimido, y escriba FLAC |
| `[perf]` | numba | la ponderación temporal `impulse` se ejecute compilada |
| `[full]` | los cuatro anteriores | estén todas las funciones salvo el cálculo con torch |
| `[torch]` | torch, array-api-compat | las simulaciones FDTD calculen con PyTorch |

Ningún extra necesita un paquete del sistema: en una imagen `python:3.13-slim`
sin nada más, todos se instalan y funcionan desde sus wheels, también
`[audio]`. Sin numba, la ponderación temporal `impulse` se ejecuta en Python
puro y no dice nada. Una función cuyo extra falta dice cuál instalar, con la
orden de pip y la de conda:

```text
ImportError: Plotting requires matplotlib. Install it with: pip install "phonometry[plot]" (conda: conda install -c conda-forge matplotlib-base)
```

La versión más antigua de cada dependencia con la que se prueba la
biblioteca, en cada Python, está en [Primeros
pasos](/phonometry/es/start/getting-started/#desde-pypi-recomendada).
En Windows en ARM, en Linux en ARM con musl y en macOS en Intel, algunas de
esas versiones no tienen wheel, y pip las compila allí desde el código fuente,
salvo torch, que no publica código fuente que compilar y por eso no se instala
allí; la misma sección dice cuáles.

## torch sin CUDA

`[full]` deja fuera `[torch]` porque los wheels de torch que sirve PyPI para
Linux traen gigabytes de bibliotecas de CUDA. En una máquina Linux sin GPU de
NVIDIA, instala primero torch desde el índice de CPU de PyTorch y después el
extra, que conserva el torch que encuentra, en el entorno virtual creado más
arriba:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install "phonometry[torch]"
```

El entorno queda con la compilación de torch para CPU y ningún paquete de
NVIDIA, y una simulación FDTD con `Compute(device="torch:cpu")` da las mismas
presiones que con NumPy. [Dónde se calcula una
simulación](/phonometry/es/simulation/compute/) trata los demás dispositivos.

## Desde un clon

```bash
git clone https://github.com/jmrplens/phonometry.git
cd phonometry
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

pip construye el wheel con setuptools y sin compilador, y la construcción
pasa también con `PYTHONWARNINGS=error`.

## uv

`uv pip` acepta los mismos requisitos que pip, en un entorno que crea uv:

```bash
uv venv
uv pip install "phonometry[full]"
```

Para torch, `--torch-backend cpu` le dice a uv que lo tome del índice de CPU
de PyTorch, sin paquetes de NVIDIA:

```bash
uv pip install "phonometry[torch]" --torch-backend cpu
```

En un proyecto de uv, `uv add` escribe el requisito en `pyproject.toml` y en
el fichero de bloqueo, y `uv run` ejecuta en el entorno del proyecto:

```bash
uv init acoustics
cd acoustics
uv add "phonometry[full]"
uv run python -c "import phonometry; print(phonometry.__version__)"
```

`uv add` resuelve igual en un proyecto para Python 3.12, 3.13 o 3.14.

### torch desde el índice de CPU en un proyecto

Declara el índice en `pyproject.toml`, márcalo como explícito para que solo
se tome torch de él, y dirige torch hacia él:

```toml
[tool.uv.sources]
torch = [{ index = "pytorch-cpu" }]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true
```

Después añade torch por su nombre junto al extra:

```bash
uv add "phonometry[torch]" torch
```

El nombre importa. Una fuente se aplica a una dependencia que el propio
proyecto nombra, así que `uv add "phonometry[torch]"` a secas, con el mismo
`pyproject.toml`, bloquea el torch del índice por defecto de PyPI junto con
sus paquetes de CUDA y de NVIDIA, y no avisa de ello.
