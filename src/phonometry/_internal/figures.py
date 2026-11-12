#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A plot that raises closes the figures it made (private module).

A ``.plot()`` makes its figure first and draws into it after, so a keyword
matplotlib refuses (``colour="red"`` for ``color``) raised from the drawing
and left the half-drawn figure open: a notebook showed it under the
traceback, and :mod:`matplotlib.pyplot` held it until the kernel ended.
:func:`closes_its_figures` wraps a plotting method so that, when it raises,
every figure that opened during the call is closed; a figure open before
the call, the one an axes the caller handed it belongs to among them, is the
caller's and stays. :class:`~phonometry._internal.display.RichDisplay` wraps
the ``plot`` and ``plot_*`` methods of every record this way as the class is
made, and a plotting class that is no record takes the decorator itself.

The same wrapper names the extra when matplotlib is missing: a plot imports
what it draws with (``matplotlib.patches``, ``matplotlib.ticker``) inside the
function, and such an import met before the figure is made raised a bare
``ModuleNotFoundError``; the wrapper raises the install hint in its place,
with the missing module as its cause.
"""

from __future__ import annotations

import functools
import sys
from typing import TYPE_CHECKING, Any, cast

from .extras import PLOT_INSTALL_HINT

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["closes_its_figures", "is_plotting_method"]

#: The attribute that marks a method :func:`closes_its_figures` has wrapped,
#: so that the class a ``slots=True`` dataclass makes anew is not wrapped twice.
_MARK = "_closes_its_figures"


def _open_figures() -> set[int]:
    """The numbers of the figures :mod:`matplotlib.pyplot` holds open now.

    No figure is open while pyplot has not been imported, which this does not
    do: a plot that fails before it reaches matplotlib leaves it unimported.
    """
    pyplot = sys.modules.get("matplotlib.pyplot")
    if pyplot is None:
        return set()
    return {int(number) for number in pyplot.get_fignums()}


def _without_matplotlib(error: BaseException) -> bool:
    """Whether *error* is the import of a matplotlib module that is not there."""
    if not isinstance(error, ModuleNotFoundError) or error.name is None:
        return False
    return error.name == "matplotlib" or error.name.startswith("matplotlib.")


def is_plotting_method(name: str) -> bool:
    """Whether a method called *name* draws: ``plot`` or ``plot_*``."""
    return name == "plot" or name.startswith("plot_")


def closes_its_figures[F: Callable[..., Any]](plot: F) -> F:
    """*plot*, closing every figure it opened when it raises.

    A matplotlib module that cannot be imported is raised as the install
    hint of the ``[plot]`` extra, with the missing module as its cause.

    :param plot: A function or method that may open figures.
    :return: The wrapped function, with *plot*'s name, signature and
        docstring.
    """
    if getattr(plot, _MARK, False):
        return plot

    @functools.wraps(plot)
    def drawn(*args: object, **kwargs: object) -> object:
        before = _open_figures()
        try:
            return plot(*args, **kwargs)
        except BaseException as exc:
            pyplot = sys.modules.get("matplotlib.pyplot")
            if pyplot is not None:
                for number in sorted(_open_figures() - before):
                    pyplot.close(number)
            if _without_matplotlib(exc):
                raise ImportError(PLOT_INSTALL_HINT) from exc
            raise

    setattr(drawn, _MARK, True)
    return cast("F", drawn)
