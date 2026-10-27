#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A worker the kernel kills, for the tests of what waits on one.

A process pool whose worker the out-of-memory killer ends gets no exception
from it, only a process that is gone. The stand-in here ends its own process
the same way, with no cleanup, and imports nothing heavy, since a spawned
worker imports this module to run it.
"""

from __future__ import annotations

import os
import signal


def killed(*args: object) -> None:
    """End this process at once, as the kernel's out-of-memory killer ends one.

    Where there is no SIGKILL (Windows), SIGTERM is what ends a process at
    once there.
    """
    del args
    os.kill(os.getpid(), getattr(signal, "SIGKILL", signal.SIGTERM))
