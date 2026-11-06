#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Warning hierarchy root, and the one way the library warns (private module, public class).

Every warning the library emits derives from :class:`PhonometryWarning`
so users can filter or escalate all phonometry diagnostics with a single
:func:`warnings.filterwarnings` rule, and every one is emitted through
:func:`warn_caller`, which reports it at the first line outside the package:
the line of the caller's code that made the call.
"""

from __future__ import annotations

import os
import sys
import warnings
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from types import FrameType

__all__ = ["PhonometryWarning", "warn_caller"]


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

    :param message: The warning's text, or a warning instance to raise again
        with its own class (the remote client relays a node's warnings so).
    :param category: The topic's published class; left out only with a
        warning instance.
    """
    warnings.warn(
        message,
        category,
        stacklevel=2 + _frames_between(sys._getframe(1)),
        skip_file_prefixes=(_PACKAGE_PREFIX,),
    )
