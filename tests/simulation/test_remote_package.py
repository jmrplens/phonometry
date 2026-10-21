#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The package a client ships is the file set of a wheel of its own phonometry."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from phonometry.simulation._remote import bootstrap, package

_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_the_package_data_is_the_wheel_s() -> None:
    assert (
        list(package.PACKAGE_DATA)
        == _PYPROJECT["tool"]["setuptools"]["package-data"]["phonometry"]
    )


def test_the_floors_a_node_checks_are_the_package_s() -> None:
    floors = {}
    for requirement in _PYPROJECT["project"]["dependencies"]:
        found = re.fullmatch(r"([A-Za-z0-9_.-]+)>=([0-9.]+)", requirement)
        assert found is not None, requirement
        name, floor = found.groups()
        floors[name] = floor
    assert dict(package.FLOORS) == floors
    assert _PYPROJECT["project"]["requires-python"] == f">={package.PYTHON_FLOOR}"


def test_the_installed_package_is_what_a_wheel_holds() -> None:
    shipped = package.installed_package()
    paths = [path for path, _ in shipped.files]
    assert paths == sorted(paths)
    assert "phonometry/__init__.py" in paths
    assert "phonometry/py.typed" in paths
    assert "phonometry/simulation/fdtd.py" in paths
    assert "phonometry/simulation/_remote/bootstrap.py" in paths
    assert any(
        path.startswith("phonometry/solids/data/") and path.endswith(".json")
        for path in paths
    )
    assert not any("__pycache__" in path or path.endswith(".pyc") for path in paths)
    assert all(bootstrap.is_safe_path(path) for path in paths)


def test_the_digest_names_the_files_and_moves_with_any_of_them() -> None:
    shipped = package.installed_package()
    digest = bootstrap.PackageDigest()
    for path, data in shipped.files:
        digest.add(path, data)
    assert shipped.digest == digest.hexdigest()
    assert package.installed_package().digest == shipped.digest


def test_a_changed_byte_or_name_moves_the_digest(tmp_path: Path) -> None:
    # The node keeps a package under its digest: one that stayed put would
    # run the code the node already holds instead of the client's.
    root = tmp_path / "phonometry"
    _tree(root, {"__init__.py": b"", "mod.py": b"x = 1\n"})
    digests = [package.package_from(root).digest]
    (root / "mod.py").write_bytes(b"x = 2\n")
    digests.append(package.package_from(root).digest)
    (root / "mod.py").rename(root / "other.py")
    digests.append(package.package_from(root).digest)
    assert len(set(digests)) == 3


def _tree(root: Path, files: dict[str, bytes]) -> None:
    # Bytes, not text: Windows would write "x = 1\r\n" and change every size.
    for name, data in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)


def test_a_directory_that_is_not_a_package_ships_only_its_data(tmp_path: Path) -> None:
    root = tmp_path / "phonometry"
    _tree(
        root,
        {
            "__init__.py": b"",
            "py.typed": b"",
            "sub/__init__.py": b"",
            "sub/mod.py": b"x = 1\n",
            "orphan/stray.py": b"y = 2\n",
            "solids/data/steel.json": b"{}",
            "sub/__pycache__/mod.cpython-313.pyc": b"",
            "notes.txt": b"not package data\n",
        },
    )
    shipped = package.package_from(root)
    assert [path for path, _ in shipped.files] == [
        "phonometry/__init__.py",
        "phonometry/py.typed",
        "phonometry/solids/data/steel.json",
        "phonometry/sub/__init__.py",
        "phonometry/sub/mod.py",
    ]
    assert shipped.size == len(b"x = 1\n") + len(b"{}")


def test_a_package_without_its_init_is_no_package(tmp_path: Path) -> None:
    root = tmp_path / "phonometry"
    root.mkdir()
    with pytest.raises(FileNotFoundError, match="__init__.py"):
        package.package_from(root)


def test_a_file_no_node_would_take_is_refused_here_by_name(tmp_path: Path) -> None:
    # A stray file of a development checkout: the node would refuse the whole
    # package after the connection opened; the client says which file first.
    root = tmp_path / "phonometry"
    _tree(root, {"__init__.py": b"", "draft copy.py": b""})
    with pytest.raises(
        ValueError, match="'phonometry/draft copy.py' cannot travel to a node"
    ):
        package.package_from(root)
