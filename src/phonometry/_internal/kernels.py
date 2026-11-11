#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A serial loop compiled by numba where the ``[perf]`` extra brings it (private module).

numba compiles a decorated function on its first call and keeps the machine
code on disk, so a later process loads it instead of compiling again. It
looks for a directory to keep it in beside the module, under
``NUMBA_CACHE_DIR``, then under the user's home; a service account,
``nobody`` or a container user with no home over a read-only install has
none, and numba refuses the decoration itself with ``RuntimeError: cannot
cache function ...: no locator available``. The decoration runs when the
module is imported, so the import of every package that reaches the kernel
failed. :func:`compiled` compiles such a function without the cache instead:
each process then compiles it once, on its first call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["compiled"]

#: What numba's refusal says when no directory can hold the cache, in numba
#: 0.60.0 to 0.68.1 (``numba.core.caching.CacheImpl``).
_NO_CACHE = "cannot cache function"


def compiled[F: Callable[..., Any]](function: F) -> F:
    """*function* compiled by numba in nopython mode, or *function* itself without numba.

    The compiled function is cached on disk where numba finds a directory
    it can write, and compiled in each process where it finds none.

    :param function: A function numba compiles in nopython mode.
    :return: numba's dispatcher, which calls as *function* does.
    :raises RuntimeError: when numba refuses the decoration for any reason
        but a cache it cannot place.
    """
    try:
        from numba import jit
    except ImportError:
        return function
    try:
        return cast("F", jit(nopython=True, cache=True)(function))
    except RuntimeError as exc:
        if _NO_CACHE not in str(exc):
            raise
    return cast("F", jit(nopython=True)(function))
