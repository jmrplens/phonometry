#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a guard keeps for the tests of one module, let go once the module is done.

A guard that reads the whole package keeps what it read in ``functools`` caches,
so that the next question costs nothing: ``scripts/check_choice_literals.py``
keeps the constants, the imports and the aliases of every module it read, more
than a gigabyte once it has read the package. The tests of a guard ask it
together, on one worker (``xdist_group``, rule T19 of
``docs/contributing/tests.md``), and once the worker leaves their module nothing
asks again: a module-scoped fixture of the module calls :func:`forget` there, so
that the next guard's caches do not pile up on top of them for the rest of the
session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


def forget(*modules: ModuleType) -> None:
    """Clear every cache a function of *modules* keeps, ``functools.cache`` and
    ``functools.lru_cache`` alike: what each read comes back on the next call.

    A function a module imports from another is that module's, and is left alone.
    """
    for module in modules:
        for value in list(vars(module).values()):
            if getattr(value, "__module__", None) != module.__name__:
                continue
            clear = getattr(value, "cache_clear", None)
            if callable(clear):
                clear()
