#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How to install what an optional feature needs, with pip and with conda (private module).

A message the library raises for a missing soft dependency ends with one of
the hints this module builds, so every one names the same two commands: the
pip command that installs the extra, and the conda-forge packages that bring
the same libraries. Followed literally in a conda environment, the pip
command alone installs matplotlib and its dependencies from PyPI beside
conda-forge's NumPy. This is the one place in the package that spells an
install command; ``scripts/check_quoted_extras.py`` refuses one anywhere
else in ``src``.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Literal

__all__ = ["TORCH_CPU_WHEELS", "install_hint", "package_hint"]

type Extra = Literal["audio", "perf", "plot", "report", "torch"]

#: The conda-forge packages that bring what each extra installs:
#: ``matplotlib-base``, since ``matplotlib`` also pulls a GUI toolkit;
#: ``pysoundfile``, conda-forge's name for python-soundfile, which brings
#: libsndfile with it; ``pytorch`` beside ``array-api-compat``, with no index
#: URL for the CPU build.
_CONDA_FORGE_PACKAGES: Final = MappingProxyType(
    {
        "audio": ("pysoundfile",),
        "perf": ("numba",),
        "plot": ("matplotlib-base",),
        "report": ("reportlab", "svglib"),
        "torch": ("pytorch", "array-api-compat"),
    }
)

#: The pip command that installs PyTorch's CPU wheels, which a CPU-only
#: machine runs before the ``[torch]`` extra: the wheels PyPI serves for Linux
#: bring gigabytes of CUDA libraries a CPU never uses.
TORCH_CPU_WHEELS: Final = (
    "pip install torch --index-url https://download.pytorch.org/whl/cpu"
)


def _with_conda(pip: str, packages: tuple[str, ...]) -> str:
    """*pip*, then the conda-forge command that installs *packages*, in parentheses.

    Nothing touches the end of the pip command but a blank, so an index URL
    it ends with copies as it reads.
    """
    return f"{pip} (conda: conda install -c conda-forge {' '.join(packages)})"


def install_hint(*extras: Extra, pip_first: str | None = None) -> str:
    """How to install *extras*: the pip command, then the conda-forge packages.

    ``install_hint("plot")`` is ``pip install "phonometry[plot]" (conda:
    conda install -c conda-forge matplotlib-base)``.

    :param extras: The extras, in the order the requirement names them.
    :param pip_first: A pip command to run before the extra's, joined by
        "and then"; conda needs nothing in its place.
    :return: The hint, to follow "Install it with: " in a message.
    """
    pip = f'pip install "phonometry[{",".join(extras)}]"'
    if pip_first is not None:
        pip = f"{pip_first} and then {pip}"
    packages = tuple(
        package for extra in extras for package in _CONDA_FORGE_PACKAGES[extra]
    )
    return _with_conda(pip, packages)


def package_hint(pip_package: str, conda_package: str) -> str:
    """How to install a library no extra brings, as pip and conda-forge name it.

    :param pip_package: Its name on PyPI.
    :param conda_package: Its name on conda-forge.
    :return: The hint, ``pip install <pip_package> (conda: conda install -c
        conda-forge <conda_package>)``.
    """
    return _with_conda(f"pip install {pip_package}", (conda_package,))
