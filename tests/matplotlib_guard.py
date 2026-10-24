#  Copyright (c) 2026. Jose Manuel Requena Plens
"""matplotlib's settings, left by each test as it found them and put back after each import.

A setting changed for good draws the figures of whatever the worker runs
next, so a figure test would pass or fail with the order the workers were
dealt. Two places change them for good:

* a test, through ``plt.style.use`` or an assignment to ``rcParams``: the
  dark page the contrast tests left behind turned a legend frame black, and
  the legend check of another module no longer saw it. Such a test fails
  (:func:`_matplotlib_settings_unchanged`); a test changes the settings
  inside ``matplotlib.rc_context()`` or ``plt.style.context()``;
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
key warns. ``tests/conftest.py`` loads this plugin;
``test_matplotlib_guard.py`` holds it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

#: The settings ``matplotlib.use`` sets: they change no figure.
_BACKEND_SETTINGS = frozenset({"backend", "backend_fallback"})


def _settings() -> dict[str, object]:
    """matplotlib's settings now, read raw, the backend's aside."""
    return {
        key: value
        for key, value in dict.items(mpl.rcParams)
        if key not in _BACKEND_SETTINGS
    }


@pytest.fixture(autouse=True)
def _matplotlib_settings_unchanged() -> Iterator[None]:
    """Fail a test that leaves matplotlib's settings changed."""
    before = _settings()
    yield
    after = _settings()
    if after == before:
        return
    changed = sorted(
        key for key in after.keys() | before.keys() if after.get(key) != before.get(key)
    )
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
    found = _settings()
    try:
        return (yield)
    finally:
        dict.update(mpl.rcParams, found)
