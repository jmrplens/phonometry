#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The strict array backend the engine tests step on, with one guard for all, and a node on this machine.

A plugin rather than ``tests/simulation/conftest.py``: two files named
``conftest.py`` are one module name to a type checker, which then refuses to
read either. ``tests/conftest.py`` loads it, which makes its fixtures visible
to every test; it has no hooks and nothing autouse, so only a test that names
one of them gets it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import pytest

from phonometry.simulation import _backends as bk
from phonometry.simulation._remote import bootstrap, command

if TYPE_CHECKING:
    from collections.abc import Callable

_FAKE_SSH = Path(__file__).parent / "simulation" / "fake_ssh.py"
#: The longest a run on the node may take in these tests [s]: the hosts
#: file's timeout, far above what a run here takes, so no test can hang.
_NODE_TIMEOUT_S = 120


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


@pytest.fixture(scope="module")
def node_cache(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One node cache for the module: the package travels once."""
    return tmp_path_factory.mktemp("node-cache")


@pytest.fixture
def node(tmp_path: Path, node_cache: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """A Python node on this machine, reached through the stand-in for ssh."""
    hosts = tmp_path / "hosts.toml"
    hosts.write_text(
        "[hosts.here]\n"
        'ssh = "node.example"\n'
        'runner = "python"\n'
        f"python = {json.dumps(sys.executable)}\n"
        'label = "this machine"\n'
        f"timeout_s = {_NODE_TIMEOUT_S}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(hosts))
    monkeypatch.setenv(bootstrap.CACHE_VAR, str(node_cache))
    monkeypatch.setattr(command, "_SSH_PROGRAM", (sys.executable, str(_FAKE_SSH)))
    for name in (
        "FAKE_SSH_MODE",
        "FAKE_SSH_LOG",
        "FAKE_SSH_PIDFILE",
        "PHONOMETRY_COMPUTE",
    ):
        monkeypatch.delenv(name, raising=False)
    return "here"
