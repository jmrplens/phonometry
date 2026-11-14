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
session. The ``fresh_caches`` fixture of ``tests/conftest.py`` calls it on both
sides of a test that points a module's globals at a tree of its own, so that
the test reads no answer kept from another tree and leaves none of its own.

:func:`forget` clears the caches of functions. A module can keep what it read
in a dict, set or list of its own too, bound at its top empty and filled as it
runs, which no ``cache_clear`` reaches: :func:`containers_filled_as_it_runs`
names those, so that the fixture refuses a module that keeps one instead of
handing the test what another test read.
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

#: What the ``fresh_caches`` fixture hands a test: ``(module, NAME=value, ...)``
#: points those globals of the module elsewhere for the test.
FreshCaches = Callable[..., None]


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


def _starts_empty(value: ast.expr) -> bool:
    """Whether an expression builds an empty dict, set or list."""
    if isinstance(value, ast.Dict):
        return not value.keys
    if isinstance(value, ast.List):
        return not value.elts
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in {"dict", "set", "list"}
        and not value.args
        and not value.keywords
    )


def containers_filled_as_it_runs(module: ModuleType) -> list[str]:
    """The names *module* binds at its top to an empty dict, set or list.

    Read from its source, not its values: what a module starts empty and
    fills as it runs is a cache of what it read, whatever it holds by the
    time a test asks, and :func:`forget` does not clear it.
    """
    names: list[str] = []
    for statement in ast.parse(inspect.getsource(module)).body:
        if isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets, value = [statement.target], statement.value
        elif isinstance(statement, ast.Assign):
            targets, value = statement.targets, statement.value
        else:
            continue
        if _starts_empty(value):
            names.extend(
                target.id for target in targets if isinstance(target, ast.Name)
            )
    return sorted(names)
