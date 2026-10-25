#  Copyright (c) 2026. Jose Manuel Requena Plens
"""matplotlib's settings, left by each test as it found them and put back after each import.

A setting changed for good draws the figures of whatever the worker runs
next, so a figure test would pass or fail with the order the workers were
dealt. Two places change them for good:

* a test, through ``plt.style.use``, an assignment to ``rcParams`` or a
  list of theirs changed in place: the dark page the contrast tests left
  behind turned a legend frame black, and the legend check of another
  module no longer saw it. Such a test fails
  (:func:`_matplotlib_settings_unchanged`), and the settings it found are
  put back, also when it failed on its own, so the tests after it draw with
  them; a test changes the settings inside ``matplotlib.rc_context()`` or
  ``plt.style.context()``;
* a test module, as it is imported, by importing
  ``scripts/figures/theme.py`` above all (it sets the documentation
  generator's grid, figure size and resolution, and
  ``savefig.bbox="tight"``): that happens before the first test of the
  worker, so the check of each test cannot see it, and which module does it
  depends on the order, since only the first import of the theme changes
  anything. Every node is collected as inside ``rc_context``
  (:func:`pytest_make_collect_report`), so whatever an import changes is put
  back before any test runs. A test that draws with the generator's
  settings asks for the ``figure_theme`` fixture.

Neither looks at the two settings that choose the backend, which
``matplotlib.use`` sets and which change no figure: ``matplotlib.use("Agg")``
at a module's top still holds, and a test that calls it again passes. The
settings are read and written raw, as ``rc_context`` does, so no deprecated
key warns, and each value is copied deep, so a list changed in place is seen
and put back.

matplotlib is an optional extra, so the plugin imports it nowhere: until a
test or a module imports it there is nothing to guard, and the settings it
read as it was imported (``rcParamsOrig``) stand for the ones before that
import. ``tests/conftest.py`` loads this plugin; ``test_matplotlib_guard.py``
holds it.
"""

from __future__ import annotations

import copy
import sys
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

#: The settings ``matplotlib.use`` sets: they change no figure.
_BACKEND_SETTINGS = frozenset({"backend", "backend_fallback"})


def _rc() -> dict[str, Any] | None:
    """matplotlib's settings, if something has imported matplotlib; ``None`` otherwise."""
    matplotlib = sys.modules.get("matplotlib")
    return None if matplotlib is None else matplotlib.rcParams


def _copy(settings: dict[str, Any]) -> dict[str, Any]:
    """A deep copy of *settings*, read raw, the backend's aside."""
    return {
        key: copy.deepcopy(value)
        for key, value in dict.items(settings)
        if key not in _BACKEND_SETTINGS
    }


def _found_before(found: dict[str, Any] | None) -> dict[str, Any]:
    """The settings before: *found*, or, when matplotlib was imported since, the ones it read then."""
    if found is not None:
        return found
    return _copy(sys.modules["matplotlib"].rcParamsOrig)


@pytest.fixture(autouse=True)
def _matplotlib_settings_unchanged() -> Iterator[None]:
    """Fail a test that leaves matplotlib's settings changed, and put back the ones it found."""
    rc = _rc()
    found = None if rc is None else _copy(rc)
    yield
    rc = _rc()
    if rc is None:
        return
    before = _found_before(found)
    changed = sorted(
        key
        for key in dict.keys(rc) | before.keys()
        if key not in _BACKEND_SETTINGS and dict.get(rc, key) != before.get(key)
    )
    if not changed:
        return
    dict.update(rc, before)
    pytest.fail(
        f"the test left {len(changed)} matplotlib setting(s) changed "
        f"({', '.join(changed[:8])}{', ...' if len(changed) > 8 else ''}); "
        "change them inside matplotlib.rc_context() or plt.style.context()"
    )


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(
    collector: pytest.Collector,
) -> Generator[None, pytest.CollectReport, pytest.CollectReport]:
    """Collect *collector*, then put back every setting its imports changed."""
    rc = _rc()
    found = None if rc is None else _copy(rc)
    try:
        return (yield)
    finally:
        rc = _rc()
        if rc is not None:
            dict.update(rc, _found_before(found))
