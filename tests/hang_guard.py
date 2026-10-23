#  Copyright (c) 2026. Jose Manuel Requena Plens
"""pytest's limit on how long a test runs, set again once the test has failed.

``faulthandler_timeout`` in ``pyproject.toml`` ends a test still running
after that many seconds, with the stack of every thread. pytest lifts the
limit as soon as a test fails, for the debugger that may follow
(``pytest_exception_interact``), and does not set it again: what the
failed test still runs, its teardown, would then wait without a bound, and
a teardown that hangs would hold its pytest-xdist worker with no name on
it. This plugin sets the limit again right after the failure, unless pdb
is in use, so the rest of the test has the whole limit from that moment.
``tests/conftest.py`` loads it.
"""

from __future__ import annotations

import faulthandler
import os
import sys

import pytest

#: The descriptor the stacks are written to: standard error as it was when
#: the session began. During a test pytest's capture points descriptor 2 at
#: a file of its own, so it is copied before any test runs, as pytest does
#: for its own dump.
_STDERR = pytest.StashKey[int]()


def _limit_s(config: pytest.Config) -> float:
    """``faulthandler_timeout`` [s]; ``0`` when it is off or pytest's faulthandler plugin is."""
    if not config.pluginmanager.has_plugin("faulthandler"):
        return 0.0
    return float(config.getini("faulthandler_timeout") or 0.0)


def _stderr_descriptor() -> int:
    """Standard error's descriptor, read as pytest reads it for its own dump."""
    try:
        descriptor = sys.stderr.fileno()
    except (AttributeError, ValueError):
        descriptor = -1
    if descriptor == -1:
        if sys.__stderr__ is None:
            msg = "the process has no standard error to write a stack to"
            raise RuntimeError(msg)
        descriptor = sys.__stderr__.fileno()
    return descriptor


def pytest_configure(config: pytest.Config) -> None:
    if _limit_s(config) > 0:
        config.stash[_STDERR] = os.dup(_stderr_descriptor())


def pytest_unconfigure(config: pytest.Config) -> None:
    if _STDERR in config.stash:
        os.close(config.stash[_STDERR])
        del config.stash[_STDERR]


@pytest.hookimpl(trylast=True)
def pytest_exception_interact(node: pytest.Item | pytest.Collector) -> None:
    """Set the limit again after pytest's faulthandler plugin lifted it for a failure.

    It runs last, after that plugin and after pdb, which a failure enters
    under ``--pdb``; with pdb in use the limit stays off, as pytest leaves
    it. A failure of collection is no test's, and no limit follows it.
    """
    config = node.config
    if not isinstance(node, pytest.Item) or _STDERR not in config.stash:
        return
    if config.getoption("usepdb"):
        return
    faulthandler.dump_traceback_later(
        _limit_s(config),
        file=config.stash[_STDERR],
        exit=bool(config.getini("faulthandler_exit_on_timeout")),
    )
