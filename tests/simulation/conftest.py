#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The strict array backend the engine tests step on, with one guard for all."""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

import pytest

from phonometry.simulation import _backends as bk

if TYPE_CHECKING:
    from collections.abc import Callable


def _refuse_host_conversion(*_args: object, **_kwargs: object) -> NoReturn:
    msg = (
        "a NumPy call read an array-api-strict array through __array__ or the "
        "buffer protocol, which the Array API standard does not have; bring a "
        "field to the host with Backend.to_host"
    )
    raise TypeError(msg)


def _go_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Load array-api-strict for 'cpu' and refuse every non-standard way out.

    array-api-strict refuses a function outside the standard called on its
    namespace, but NumPy still reads its arrays through ``__array__`` and the
    buffer protocol, so ``np.concatenate`` on device arrays would pass here
    and fail on CuPy. Both routes raise for the test; the backend brings an
    array to the host through DLPack, the standard's interchange.
    """
    strict = pytest.importorskip("array_api_strict")
    monkeypatch.setitem(bk.LOADERS, "cpu", bk.strict_backend)
    array_type = type(strict.asarray(0.0))
    monkeypatch.setattr(array_type, "__array__", _refuse_host_conversion)
    monkeypatch.setattr(array_type, "__buffer__", _refuse_host_conversion)


@pytest.fixture
def on_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Step on array-api-strict, where a NumPy call on a device array raises."""
    _go_strict(monkeypatch)


@pytest.fixture
def go_strict(monkeypatch: pytest.MonkeyPatch) -> Callable[[], None]:
    """Move to array-api-strict, under the same guard, when the test says so.

    For a test that runs on NumPy first and then on the strict backend.
    """

    def switch() -> None:
        _go_strict(monkeypatch)

    return switch
