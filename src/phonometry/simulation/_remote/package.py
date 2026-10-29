#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The package a client ships to a node, and its digest (private).

A node runs the client's own phonometry, whatever it has installed. The
client sends the files a wheel of its imported package would hold, chosen by
the rules setuptools follows under ``pyproject.toml`` (see
:func:`package_from`), and names them by the digest of
:class:`~.bootstrap.PackageDigest`; the node computes the digest again from
what it receives. A release and a development checkout are handled alike,
and a node receives a package once per digest.

:data:`PACKAGE_DATA`, :data:`PYTHON_FLOOR` and :data:`FLOORS` repeat
``pyproject.toml``, which an installed package does not carry;
``tests/simulation/test_remote_package.py`` holds them to it, and the
settings the rules depend on with them.
"""

from __future__ import annotations

import glob
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

from ..._internal.json_input import escaped
from .bootstrap import PackageDigest, is_safe_path

if TYPE_CHECKING:
    from collections.abc import Mapping

#: The package-data patterns of ``pyproject.toml``, relative to the package.
PACKAGE_DATA: tuple[str, ...] = (
    "py.typed",
    "aircraft/data/anp/*.csv",
    "aircraft/data/anp/*.md",
    "building/data/*.json",
    "environment/propagation/data/*.json",
    "fluids/data/*.json",
    "materials/absorbers/data/*.json",
    "materials/diffusers/data/*.json",
    "materials/resilient/data/*.json",
    "noise_control/data/*.json",
    "solids/data/*.json",
)
#: The oldest Python the package runs on (``requires-python``).
PYTHON_FLOOR = "3.12"
#: The oldest release of each dependency the package runs with.
FLOORS: Mapping[str, str] = MappingProxyType({"numpy": "2.0.2", "scipy": "1.14.0"})

#: The one package a node runs, and the first part of every path it writes.
_NAME = "phonometry"
#: What setuptools takes from every package directory: the modules, and the
#: typing files it adds to the package data by itself.
_EVERY_PACKAGE = ("*.py", "*.pyi", "py.typed")


@dataclass(frozen=True)
class Package:
    """The files of a package, sorted by path, and their digest.

    :ivar files: ``(path, content)`` pairs, the path POSIX and starting with
        ``phonometry/``.
    :ivar digest: Their :class:`~.bootstrap.PackageDigest`.
    """

    files: tuple[tuple[str, bytes], ...]
    digest: str

    @property
    def size(self) -> int:
        """The bytes the files hold together."""
        return sum(len(data) for _, data in self.files)


def _package_directories(root: Path) -> list[Path]:
    """The directories setuptools takes for packages under ``namespaces = false``.

    *root* and, below it, each directory with an ``__init__.py`` and no dot
    in its name whose parent is one of them.
    """
    found = [root]
    pending = [root]
    while pending:
        directory = pending.pop()
        for child in sorted(directory.iterdir()):
            if (
                child.is_dir()
                and "." not in child.name
                and child.name != "__pycache__"
                and (child / "__init__.py").is_file()
            ):
                found.append(child)
                pending.append(child)
    return found


def _matches(directory: Path, pattern: str) -> list[Path]:
    """The files *pattern* matches from *directory*, as setuptools finds them."""
    # glob.glob, which setuptools calls, leaves hidden files out; Path.glob
    # would ship them.
    matched = glob.glob(pattern, root_dir=directory)  # noqa: PTH207
    return [directory / name for name in matched if (directory / name).is_file()]


def package_from(root: Path) -> Package:
    """The wheel's file set of the package whose directory is *root*.

    The files setuptools puts in a wheel of it under ``pyproject.toml``: the
    modules, the ``*.pyi`` stubs and ``py.typed`` of every package directory
    (*root* and, below it, each directory with an ``__init__.py`` and no dot
    in its name whose parent is one of them), and what the
    :data:`PACKAGE_DATA` patterns match from *root*. A hidden file, a module
    of a directory that is not a package and ``__pycache__`` stay out, here
    as in the wheel.

    :raises FileNotFoundError: when *root* has no ``__init__.py``.
    :raises ValueError: when *root* is not named ``phonometry``, the one
        package a node runs; and, naming the file, for one whose path a node
        refuses to write (a space or another character outside letters,
        digits, ``.``, ``_`` and ``-``): said here, before anything connects,
        rather than by the node once the package is on its way.
    """
    if not (root / "__init__.py").is_file():
        msg = f"{escaped(str(root / '__init__.py'))} does not exist: {escaped(str(root))} is not a package"
        raise FileNotFoundError(msg)
    if root.name != _NAME:
        msg = f"{escaped(str(root))} is not named {_NAME!r}: a node runs that package only"
        raise ValueError(msg)
    chosen: set[Path] = set()
    for directory in _package_directories(root):
        for pattern in _EVERY_PACKAGE:
            chosen.update(_matches(directory, pattern))
    for pattern in PACKAGE_DATA:
        chosen.update(_matches(root, pattern))
    # Sorted on the POSIX string, never on the paths: a WindowsPath compares
    # without case, and the digest needs one order on every client.
    named = sorted(
        (f"{_NAME}/{path.relative_to(root).as_posix()}", path) for path in chosen
    )
    for name, path in named:
        if not is_safe_path(name):
            msg = (
                f"{name!r} cannot travel to a node: a package path holds only letters, "
                f"digits, '.', '_' and '-'; rename or remove {escaped(str(path))}"
            )
            raise ValueError(msg)
    files = tuple((name, path.read_bytes()) for name, path in named)
    digest = PackageDigest()
    for name, data in files:
        digest.add(name, data)
    return Package(files=files, digest=digest.hexdigest())


def installed_package() -> Package:
    """The package this process imported, as a node is to run it."""
    return package_from(Path(__file__).resolve().parents[2])
