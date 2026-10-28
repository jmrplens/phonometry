#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A name the package does not publish is an error for mypy, not an ``object``.

The package imports its domains lazily, through a module ``__getattr__``
(PEP 562). A type checker that saw that function would read every missing
name through it, so ``phonometry.stpia(...)`` would type as a call on
``object`` and the misspelling would surface only as an unrelated error, or
not at all. The function is defined for the running interpreter only, and a
type checker reads the imports the package declares for it, which name
exactly what is published. The ignore below becomes unused, and fails, the
day a module ``__getattr__`` is visible to the type checker again. CI type
checks every file in this directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

import pytest

import phonometry
from phonometry import filters
from phonometry.filters import compliance


def test_a_misspelt_root_name_is_refused() -> None:
    with pytest.raises(AttributeError, match="no attribute 'no_such_name'"):
        phonometry.no_such_name  # type: ignore[attr-defined]  # noqa: B018


def test_a_published_root_name_is_read_with_its_type() -> None:
    assert phonometry.filters is filters


def test_a_transcription_is_read_from_the_module_that_holds_it() -> None:
    with pytest.raises(AttributeError, match="no attribute '_WEIGHTING_TABLE3'"):
        compliance._WEIGHTING_TABLE3  # type: ignore[attr-defined]  # noqa: B018
