#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Packaging guarantees: PEP 561 typing marker shipped with the package.
"""

import pathlib

import pyoctaveband


def test_py_typed_marker_is_shipped() -> None:
    pkg_dir = pathlib.Path(pyoctaveband.__file__).parent
    assert (pkg_dir / "py.typed").exists(), "PEP 561 marker missing from package"
