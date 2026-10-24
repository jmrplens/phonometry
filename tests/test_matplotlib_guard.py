#  Copyright (c) 2026. Jose Manuel Requena Plens
"""No test module changes matplotlib's settings for the tests after it as it is imported.

A module that changes them at its top, by importing
``scripts/figures/theme.py`` above all, would change them before the first
test of its worker runs: every test the worker ran after it would then draw
with the documentation generator's settings (its grid, its figure size and
resolution, ``savefig.bbox="tight"``), and a figure test would pass or fail
by what else the worker happened to collect. ``matplotlib_guard.py`` puts
back what each module's import changed, the backend aside, so no import can
hand its settings on, whichever module imports the theme first. Here the
suite is held to loading it, a small project of two modules shows that the
second draws with matplotlib's own settings with it and with the first
one's without it, and the settings this run hands its tests are read as one
of them.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import child_process
import matplotlib as mpl
import pytest

_TESTS = Path(__file__).resolve().parent

#: How long one run of the small project is let go before it is killed [s].
_RUN_S = 120.0

#: The settings that choose the backend: ``matplotlib.use("Agg")`` at a
#: module's top sets them, and they change no figure.
_BACKEND_SETTINGS = frozenset({"backend", "backend_fallback"})

#: A module that changes matplotlib's settings as it is imported, as the
#: generator's theme does.
_STYLED = """\
import matplotlib

matplotlib.rcParams["axes.grid"] = True
matplotlib.rcParams["savefig.bbox"] = "tight"
"""

#: A test module that imports it at its top, after choosing its backend.
_IMPORTS = """\
import matplotlib

matplotlib.use("Agg")

import styled


def test_that_imports_the_styled_module():
    assert styled
"""

#: A test module collected after it, which draws with what it finds: the
#: backend the first one chose, and matplotlib's own settings otherwise.
_DRAWS = """\
import matplotlib


def test_that_draws():
    for key in ("axes.grid", "savefig.bbox"):
        assert matplotlib.rcParams[key] == matplotlib.rcParamsOrig[key], key
    assert dict.__getitem__(matplotlib.rcParams, "backend").lower() == "agg"
    assert dict.__getitem__(matplotlib.rcParams, "backend_fallback") is False
"""


def test_the_suite_loads_the_guard(pytestconfig: pytest.Config) -> None:
    assert pytestconfig.pluginmanager.has_plugin("matplotlib_guard")


@pytest.mark.parametrize(
    ("plugin", "status", "summary"),
    [
        pytest.param(("-p", "matplotlib_guard"), 0, "2 passed", id="guarded"),
        pytest.param((), 1, "FAILED test_b_draws.py::test_that_draws", id="unguarded"),
    ],
)
def test_a_module_that_changes_the_settings_as_it_is_imported_changes_them_for_no_test(
    plugin: tuple[str, ...], status: int, summary: str, tmp_path: Path
) -> None:
    """With the guard the later test draws with matplotlib's own settings; without it, with the module's."""
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "styled.py").write_text(_STYLED, encoding="utf-8")
    (tmp_path / "test_a_imports.py").write_text(_IMPORTS, encoding="utf-8")
    (tmp_path / "test_b_draws.py").write_text(_DRAWS, encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "MPLBACKEND"}
    }
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_TESTS), *filter(None, [os.environ.get("PYTHONPATH")])]
    )
    done = child_process.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *plugin,
            "-p",
            "no:cacheprovider",
            "-c",
            str(tmp_path / "pytest.ini"),
            "--rootdir",
            str(tmp_path),
            "-rf",
            "test_a_imports.py",
            "test_b_draws.py",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        timeout=_RUN_S,
    )
    assert done.returncode == status, done.stdout + done.stderr
    assert summary in done.stdout, done.stdout


def test_this_test_starts_with_the_settings_matplotlib_read() -> None:
    """Whatever this worker imported or ran before this test, its settings are matplotlib's own."""
    now = dict.copy(mpl.rcParams)
    read = dict.copy(mpl.rcParamsOrig)
    changed = sorted(
        key
        for key in now.keys() | read.keys()
        if key not in _BACKEND_SETTINGS and now.get(key) != read.get(key)
    )
    if changed:
        pytest.fail(
            f"this test started with {len(changed)} matplotlib setting(s) "
            f"({', '.join(changed)}) other than the ones matplotlib read when it "
            "was imported. A test module changes them as it is imported when "
            "matplotlib_guard is not loaded; a fixture wider than one "
            "test that does not put them back changes them too. A test that "
            "draws with the generator's settings asks for the figure_theme "
            "fixture.",
            pytrace=False,
        )
