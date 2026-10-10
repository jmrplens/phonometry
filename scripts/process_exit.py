#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Run a handler once when the process ends, a forked worker included.

The figure audits write each process's recording from an exit handler, and
:mod:`atexit` alone does not reach every process that draws. A child that
:mod:`multiprocessing` starts with the fork method leaves through
``os._exit``: Python 3.13 runs the child's :mod:`atexit` handlers just before
that, Python 3.12 does not, and the one thing that still runs there is
:mod:`multiprocessing`'s own exit function, which calls the finalizers
registered with :class:`multiprocessing.util.Finalize`. A handler registered
only with :mod:`atexit` is therefore silently skipped by every forked child
on 3.12, and its recording is lost.

:func:`run_at_exit` registers the handler both ways, behind a flag that lets
it run once. Whichever of the two the process reaches first runs it; the
other finds it done.
"""

from __future__ import annotations

import atexit
import multiprocessing.util
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def run_at_exit(handler: Callable[[], None]) -> None:
    """Call *handler* once at exit: interpreter shutdown or a forked child's end."""
    done = False

    def once() -> None:
        nonlocal done
        if not done:
            done = True
            handler()

    atexit.register(once)
    # A finalizer with no object needs an exit priority, and any priority at
    # or above zero runs in the first pass of multiprocessing's exit function.
    multiprocessing.util.Finalize(None, once, exitpriority=0)
