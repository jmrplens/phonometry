#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The refusal-order plugin fails a test whose refusal came after a library advisory.

``tests/refusal_order.py`` wraps every ``pytest.raises`` that waits on an
exception which is not a warning. These cases drive one such context by hand,
so the plugin's verdict is the thing under test.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import warnings
from pathlib import PureWindowsPath

import numpy as np
import pytest
import refusal_order

import phonometry
from phonometry import emission


def _closed(raises: pytest.RaisesExc[ValueError], error: ValueError) -> bool:
    """Leave a ``pytest.raises`` block as if *error* had been raised in it."""
    return bool(raises.__exit__(type(error), error, None))


def test_an_advisory_ahead_of_the_refusal_fails_the_test() -> None:
    raises = pytest.raises(ValueError, match="refused")
    raises.__enter__()
    warnings.warn("a sound power advisory", emission.SoundPowerWarning, stacklevel=1)
    error = ValueError("refused")
    with pytest.raises(pytest.fail.Exception, match="came before the ValueError"):
        _closed(raises, error)


def test_a_warning_shown_at_a_library_line_counts_too() -> None:
    """NumPy's RuntimeWarning is shown at the line of the package that called it."""
    raises = pytest.raises(ValueError, match="refused")
    raises.__enter__()
    warnings.warn_explicit(
        "overflow encountered in multiply",
        RuntimeWarning,
        str(phonometry.__file__),
        1,
    )
    error = ValueError("refused")
    with pytest.raises(pytest.fail.Exception, match="RuntimeWarning"):
        _closed(raises, error)


def test_a_warning_shown_at_a_library_line_counts_on_windows_too(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A warning's file name written with backslashes still names the package.

    Windows writes the package's directory and the file a NumPy warning is
    shown at with backslashes, the drive letter in either case. The plugin
    is handed that platform's paths here, so the case runs on every runner.
    """
    package = r"D:\a\phonometry\src\phonometry"
    spec = importlib.machinery.ModuleSpec(
        "phonometry", None, origin=package + r"\__init__.py"
    )
    find_spec = importlib.util.find_spec

    def found(name: str, package: str | None = None) -> object:
        return spec if name == "phonometry" else find_spec(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", found)
    monkeypatch.setattr(refusal_order, "Path", PureWindowsPath)
    refusal_order._package_directory.cache_clear()
    try:
        inside = warnings.WarningMessage(
            "overflow encountered in multiply",
            RuntimeWarning,
            r"d:\a\phonometry\src\phonometry\filters\core.py",
            1,
        )
        beside = warnings.WarningMessage(
            "overflow encountered in multiply",
            RuntimeWarning,
            r"D:\a\phonometry\src\phonometry_extra\core.py",
            1,
        )
        assert refusal_order._is_library_advisory(inside)
        assert not refusal_order._is_library_advisory(beside)
    finally:
        refusal_order._package_directory.cache_clear()


def test_a_refusal_alone_passes_and_a_warning_of_the_test_is_handed_back() -> None:
    raises = pytest.raises(ValueError, match="refused")
    raises.__enter__()
    with pytest.warns(UserWarning, match="the test's own"):
        warnings.warn("the test's own", UserWarning, stacklevel=1)
    error = ValueError("refused")
    assert _closed(raises, error)


def test_a_warning_the_block_waits_on_is_left_alone() -> None:
    with pytest.warns(emission.SoundPowerWarning):
        emission.sound_power_reverberation(
            np.full((4, 6), 80.0),
            np.full(6, 1.5),
            200.0,
            220.0,
            frequencies=np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]),
        )
