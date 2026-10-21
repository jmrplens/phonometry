#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The package a client ships to a node, and its digest (private).

A node runs the client's own phonometry, whatever it has installed. The
client sends the files a wheel of its imported package would hold (the
``.py`` files of every package directory and the package data of
``pyproject.toml``, no ``__pycache__``) and names them by the digest of
:class:`~.bootstrap.PackageDigest`; the node computes the digest again from
what it receives. A release and a development checkout are handled alike,
and a node receives a package once per digest.

:data:`PACKAGE_DATA`, :data:`PYTHON_FLOOR` and :data:`FLOORS` repeat
``pyproject.toml``, which an installed package does not carry;
``tests/simulation/test_remote_package.py`` holds them to it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

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
    """The directories setuptools takes for packages: ``__init__.py`` all the way up."""
    found = [root]
    pending = [root]
    while pending:
        directory = pending.pop()
        for child in sorted(directory.iterdir()):
            if (
                child.is_dir()
                and child.name != "__pycache__"
                and (child / "__init__.py").is_file()
            ):
                found.append(child)
                pending.append(child)
    return found


def package_from(root: Path) -> Package:
    """The wheel's file set of the package whose directory is *root*.

    :raises FileNotFoundError: when *root* has no ``__init__.py``.
    :raises ValueError: naming the file, for one whose path a node refuses
        to write (a space or another character outside letters, digits,
        ``.``, ``_`` and ``-``): said here, before anything connects, rather
        than by the node once the package is on its way.
    """
    if not (root / "__init__.py").is_file():
        msg = f"{root / '__init__.py'} does not exist: {root} is not a package"
        raise FileNotFoundError(msg)
    chosen: set[Path] = set()
    for directory in _package_directories(root):
        chosen.update(path for path in directory.glob("*.py") if path.is_file())
    for pattern in PACKAGE_DATA:
        chosen.update(path for path in root.glob(pattern) if path.is_file())
    # Sorted on the POSIX string, never on the paths: a WindowsPath compares
    # without case, and the digest needs one order on every client.
    named = sorted(
        (f"{root.name}/{path.relative_to(root).as_posix()}", path) for path in chosen
    )
    for name, path in named:
        if not is_safe_path(name):
            msg = (
                f"{name!r} cannot travel to a node: a package path holds only letters, "
                f"digits, '.', '_' and '-'; rename or remove {path}"
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
