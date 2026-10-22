#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A hook the simulation functions call after each step (private).

A node watches its run through it, to stop a run whose client went away
and to write a progress line now and then. Where nobody watches, the call is
one context-variable read per step.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


class RunCancelled(Exception):
    """The client of a remote run went away; the run stops at this step."""


_WATCHER: ContextVar[Callable[[int, int], None] | None] = ContextVar(
    "phonometry_watcher", default=None
)


def step_done(done: int, total: int) -> None:
    """Tell the watcher, if there is one, that *done* of *total* steps are done."""
    watcher = _WATCHER.get()
    if watcher is not None:
        watcher(done, total)


@contextmanager
def observing(watcher: Callable[[int, int], None]) -> Iterator[None]:
    """Make *watcher* see every step a simulation function takes inside the block."""
    token = _WATCHER.set(watcher)
    try:
        yield
    finally:
        _WATCHER.reset(token)
