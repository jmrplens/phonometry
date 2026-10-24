#  Copyright (c) 2026. Jose Manuel Requena Plens
"""No test module changes matplotlib's settings as it is imported.

A module that changes them at its top, by importing
``scripts/figures/theme.py`` above all, changes them before the first test of
its worker runs: every test the worker runs after it then draws with the
documentation generator's settings (its grid, its figure size and resolution,
``savefig.bbox="tight"``), and a figure test passes or fails by what else the
worker happened to collect. ``conftest.py`` notes the first module whose
import leaves a setting changed; this test reads that note, so a full run
names the module.
"""

from __future__ import annotations

import pytest


def test_importing_the_test_modules_changes_no_matplotlib_setting(
    settings_changed_by_collection: tuple[str, tuple[str, ...]] | None,
) -> None:
    if settings_changed_by_collection is None:
        return
    module, settings = settings_changed_by_collection
    pytest.fail(
        f"importing {module} changed {len(settings)} matplotlib setting(s) "
        f"({', '.join(settings)}) for every test collected after it; import a "
        "module of scripts/figures inside matplotlib.rc_context(), and ask for "
        "the figure_theme fixture in a test that draws with the generator's "
        "settings",
        pytrace=False,
    )
