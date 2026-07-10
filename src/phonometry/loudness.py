#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Deprecated alias of :mod:`phonometry.loudness_zwicker`.

The module was renamed in phonometry 3.1 so its name states the method it
implements (ISO 532-1 Zwicker loudness) alongside its siblings
:mod:`~phonometry.loudness_ecma` and :mod:`~phonometry.loudness_moore_glasberg`.
This PEP 562 shim keeps ``phonometry.loudness`` importable for one deprecation
cycle: every attribute access warns and resolves to the new module. It will be
removed in phonometry 4.0.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from ._warnings import _warn_renamed

# Resolved through :mod:`sys.modules` (not package attribute lookup): the
# package re-exports the *function* ``loudness_zwicker``, which shadows the
# submodule attribute of the same name on the package object.
_loudness_zwicker = import_module("phonometry.loudness_zwicker")


def __getattr__(name: str) -> Any:
    try:
        attr = getattr(_loudness_zwicker, name)
    except AttributeError:
        raise AttributeError(
            f"module 'phonometry.loudness' has no attribute {name!r}"
        ) from None
    _warn_renamed(
        "the 'phonometry.loudness' module",
        "'phonometry.loudness_zwicker'",
    )
    return attr


def __dir__() -> list[str]:
    return dir(_loudness_zwicker)
