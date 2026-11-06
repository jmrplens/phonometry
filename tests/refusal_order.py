#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A refusal the library documents comes before every advisory of the same call.

Under ``python -W error`` a warning raised ahead of a refusal takes its place:
the caller who wrote ``except ValueError`` meets a ``SoundPowerWarning``, an
``STIWarning`` or NumPy's ``RuntimeWarning`` instead, and never learns which
argument was wrong. Refusals of the emission, speech, fluids, hearing and
soundscape domains were in that state, behind advisories on the microphone
positions, the background, the length of a recording or the domain of a
formula, after a first sweep had fixed the ones behind a filter bank.

This plugin holds every refusal the suite waits on. Inside each
``pytest.raises`` block that waits on an exception which is not a warning, it
records every warning with the ``always`` action, whatever the test's own
filters say, since a caller's ``-W error`` overrides them too. When the
awaited exception arrives and a library advisory came before it (a
:class:`~phonometry.PhonometryWarning`, or any warning shown at a line of the
package, which is where NumPy's land), the test fails and names both.
Otherwise the recorded warnings are issued again as they were, so the test's
filters and an enclosing ``pytest.warns`` still see them.

The fix is the library's, not the test's: check every argument first, and
advise once the result stands. ``tests/conftest.py`` loads this plugin;
``test_refusal_order.py`` holds it.
"""

from __future__ import annotations

import importlib.util
import warnings
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import TracebackType

#: A ``pytest.raises`` context, whatever exception it waits on.
type _Raises = pytest.RaisesExc[BaseException]

_ENTER = pytest.RaisesExc.__enter__
_EXIT = pytest.RaisesExc.__exit__

#: The attribute a ``pytest.raises`` context holds its recorder in.
_HELD = "_refusal_order_recorder"


@cache
def _package_directory() -> str:
    """The directory of the installed package, found without importing it."""
    spec = importlib.util.find_spec("phonometry")
    origin = None if spec is None else spec.origin
    return "" if origin is None else str(Path(origin).parent) + "/"


def _waits_on_a_refusal(expected: tuple[object, ...]) -> bool:
    """Whether a ``pytest.raises`` waits on exceptions, none of them a warning."""
    return bool(expected) and all(
        isinstance(kind, type)
        and issubclass(kind, Exception)
        and not issubclass(kind, Warning)
        for kind in expected
    )


def _is_library_advisory(record: warnings.WarningMessage) -> bool:
    """A published warning of the package, or a warning shown at a line of it."""
    from phonometry import PhonometryWarning

    directory = _package_directory()
    return issubclass(record.category, PhonometryWarning) or bool(
        directory and str(record.filename).replace("\\", "/").startswith(directory)
    )


def _enter(self: _Raises) -> pytest.ExceptionInfo[BaseException]:
    """Enter the block, recording every warning when it waits on a refusal."""
    info = _ENTER(self)
    if _waits_on_a_refusal(tuple(self.expected_exceptions)):
        recorder = warnings.catch_warnings(record=True)
        records = recorder.__enter__()
        warnings.simplefilter("always")
        setattr(self, _HELD, (recorder, records))
    return info


def _exit(
    self: _Raises,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: TracebackType | None,
) -> bool:
    """Fail on an advisory ahead of the refusal, else hand the warnings back."""
    held = self.__dict__.pop(_HELD, None)
    if held is None:
        return bool(_EXIT(self, exc_type, exc_val, exc_tb))
    recorder, records = held
    recorder.__exit__(None, None, None)
    ahead = [record for record in records if _is_library_advisory(record)]
    if ahead and exc_val is not None and self.matches(exc_val):
        first = ahead[0]
        pytest.fail(
            f"{first.category.__name__} ({first.message}) came before the "
            f"{exc_type.__name__ if exc_type else 'refusal'} ({exc_val}): under "
            "-W error the advisory replaces the documented refusal. Check every "
            "argument first, and advise once the result stands.",
            pytrace=False,
        )
    for record in records:
        warnings.warn_explicit(
            record.message, record.category, record.filename, record.lineno
        )
    return bool(_EXIT(self, exc_type, exc_val, exc_tb))


# Through setattr: mypy refuses assigning to a method of a class, and B010
# would turn the call back into that assignment.
setattr(pytest.RaisesExc, "__enter__", _enter)  # noqa: B010
setattr(pytest.RaisesExc, "__exit__", _exit)  # noqa: B010
