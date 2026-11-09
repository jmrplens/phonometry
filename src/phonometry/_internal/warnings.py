#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Warning hierarchy root, and the one way the library warns (private module, public class).

Every warning the library emits derives from :class:`PhonometryWarning`
so users can filter or escalate all phonometry diagnostics with a single
:func:`warnings.filterwarnings` rule, and every one is emitted through
:func:`warn_caller`, which reports it at the first line outside the package:
the line of the caller's code that made the call. A call that cannot finish
its checks before it advises holds its advisories with
:func:`advisories_held` until its result stands.
"""

from __future__ import annotations

import os
import sys
import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import FrameType

__all__ = ["PhonometryWarning", "advisories_held", "published_by", "warn_caller"]


def published_by[W: type[Warning]](module: str) -> Callable[[W], W]:
    """Name a warning class written in a private module by the module that publishes it.

    A class carries the module it was written in as ``__module__``, and a
    traceback under ``python -W error`` ends with it, a repr prints it and
    :mod:`pickle` reads the class back from it: a warning written in
    ``phonometry.fluids._state`` was named by a path the reference never
    shows and a caller should not import. The decorator names it by the
    public module instead, which exports the same class.

    It sets ``__module__`` once the class exists, never in the class body:
    Python then drops the ``__firstlineno__`` it recorded, so :mod:`inspect`
    says it has no source for the class rather than reading the public
    module's file at the line the private one wrote it on. A class whose
    annotations would be read against that module's globals cannot be
    named so, which is why only warnings are.

    :param module: The public module that exports the class.
    :return: The decorator, which hands the class back.
    """

    def name(cls: W) -> W:
        cls.__module__ = module
        return cls

    return name


@published_by("phonometry")
class PhonometryWarning(UserWarning):
    """Base class for all phonometry warnings."""


def _package_prefix(module_file: str) -> str:
    """The package directory of *module_file*, ``phonometry/<package>/<module>.py``.

    Cut from the string as it is, never through :class:`~pathlib.Path`: a
    frame's ``co_filename`` keeps the path the import system built from the
    ``sys.path`` entry, a ``/./`` or a ``..`` included, and a normalised
    prefix would not match it. The trailing separator stays, so that a
    sibling named like the package (``phonometry_extra/``) does not match.
    """
    return f"{module_file.rsplit(os.sep, 2)[0]}{os.sep}"


#: The package's own directory as the import system wrote it. A warning skips
#: every frame whose file is in it.
_PACKAGE_PREFIX = _package_prefix(__file__)

#: The package's name. A frame compiled from a string, ``<string>``, in the
#: globals of one of the package's modules runs the package's code: the
#: ``__init__`` a dataclass generates for a record, which calls the record's
#: ``__post_init__``, is one.
_PACKAGE = __name__.partition(".")[0]

#: Modules of the standard library whose frames stand between a library
#: function and the line that called it: :mod:`functools` runs the getter of a
#: ``cached_property``, :mod:`contextlib` the exit of a context manager
#: written as a generator, and :func:`dataclasses.replace` the ``__init__`` of
#: the record it copies. Their frames are never the caller's line.
_BETWEEN = frozenset({"contextlib", "dataclasses", "functools"})


def _is_bootstrap(filename: str) -> bool:
    """Whether *filename* is the import system's, whose frames Python itself skips."""
    return "importlib" in filename and "_bootstrap" in filename


def _runs_for_the_package(frame: FrameType) -> bool:
    """Whether *frame*, in no file of the package, still runs on the package's behalf.

    It does when it is generated code of the package (a dataclass's
    ``__init__``) or a frame of :data:`_BETWEEN`. A doctest's example, or the
    code ``python -c`` runs, is the caller's own: its file is ``<doctest ...>``
    or its globals are ``__main__``.
    """
    module = frame.f_globals.get("__name__")
    if not isinstance(module, str):
        return False
    if frame.f_code.co_filename == "<string>":
        return module == _PACKAGE or module.startswith(f"{_PACKAGE}.")
    return module in _BETWEEN


def _frames_between(frame: FrameType | None) -> int:
    """How many frames outside the package's files stand between *frame* and the caller.

    Python skips by itself the frames whose file starts with
    :data:`_PACKAGE_PREFIX`, given as ``skip_file_prefixes``, and those of the
    import system; this counts the others the walk out from *frame* meets
    before the caller's line, a generated ``__init__`` or a frame of
    :data:`_BETWEEN`, each of which costs one more step of ``stacklevel``.
    """
    between = 0
    while frame is not None:
        filename = frame.f_code.co_filename
        if not (filename.startswith(_PACKAGE_PREFIX) or _is_bootstrap(filename)):
            if not _runs_for_the_package(frame):
                break
            between += 1
        frame = frame.f_back
    return between


@overload
def warn_caller(message: str, category: type[Warning]) -> None: ...


@overload
def warn_caller(message: Warning) -> None: ...


def warn_caller(message: str | Warning, category: type[Warning] | None = None) -> None:
    """Emit a warning at the first line outside the package, the caller's.

    A fixed ``stacklevel`` counts the frames of one route to the warning, and
    the same advisory is reached through several: a public function, a
    method, a record's ``__post_init__``, another domain that calls it. Each
    route that is deeper or shallower than the count put the warning on a
    library line, where a filter by the caller's module missed it and
    Python's ``default`` action showed it once per process, since the line it
    keys its memory on was the same for every call. Skipping the package's
    frames by their file, and counting the few that run the package's code
    from elsewhere, lands on the caller's line however deep the route is.

    Inside :func:`advisories_held` the warning is kept, not issued, until
    the block that holds it ends.

    :param message: The warning's text, or a warning instance to raise again
        with its own class (the remote client relays a node's warnings so).
    :param category: The topic's published class; left out only with a
        warning instance.
    """
    held = _HELD.get()
    if held is not None:
        held.append((message, category))
        return
    warnings.warn(
        message,
        category,
        stacklevel=2 + _frames_between(sys._getframe(1)),
        skip_file_prefixes=(_PACKAGE_PREFIX,),
    )


#: An advisory as :func:`warn_caller` received it: its text and class, or a
#: warning instance and ``None``.
type _Advisory = tuple[str | Warning, type[Warning] | None]

#: The advisories of the innermost :func:`advisories_held` block that is
#: running, in the order they were raised; ``None`` outside every block. A
#: context variable, so a block holds only the warnings of its own thread or
#: task.
_HELD: ContextVar[list[_Advisory] | None] = ContextVar(
    "phonometry_held_advisories", default=None
)


@contextmanager
def advisories_held() -> Iterator[None]:
    """Hold every advisory raised in the block until the block ends without an exception.

    Rule A63 asks a call to check every argument before it advises, so that
    under ``python -W error`` the caller meets the refusal the docstring
    names rather than the advisory. A call cannot always order its steps so:
    a function it composes advises on its way to a value a later check
    needs, a correction advises before the A-weighted total refuses a band
    the table does not hold, a record it builds refuses after the
    measurement was advised on. Inside the block :func:`warn_caller` keeps
    each warning instead of issuing it. When the block ends normally they
    are issued in the order they were raised, each at the caller's line as
    it would have been; when it ends with an exception they are dropped,
    and the exception is what the caller meets. A block inside another
    hands its warnings on to the outer one.
    """
    held: list[_Advisory] = []
    token = _HELD.set(held)
    try:
        yield
    finally:
        _HELD.reset(token)
    for message, category in held:
        # As warnings.warn reads them: an instance carries its own class, and
        # a text given no class is a UserWarning.
        if isinstance(message, Warning):
            warn_caller(message)
        else:
            warn_caller(message, UserWarning if category is None else category)
