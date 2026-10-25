#  Copyright (c) 2026. Jose Manuel Requena Plens
"""No test, and no test module as it is imported, changes matplotlib's settings for the tests after it.

A module that changes them at its top, by importing
``scripts/figures/theme.py`` above all, would change them before the first
test of its worker runs: every test the worker ran after it would then draw
with the documentation generator's settings (its grid, its figure size and
resolution, ``savefig.bbox="tight"``), and a figure test would pass or fail
by what else the worker happened to collect. ``matplotlib_guard.py`` puts
back what each module's import changed, the backend aside, so no import can
hand its settings on, whichever module imports the theme first. A test that
leaves a setting changed, by assigning it or by changing a list in place,
fails, and the guard puts the setting back for the tests after it, also when
the test failed on its own. Here the suite is held to loading it, small
projects show what it does with and without it, and on an install with no
matplotlib it lets a test run, since matplotlib is an optional extra; the
settings this run hands its tests are read as one of them.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import child_process
import pytest

if TYPE_CHECKING:
    import subprocess  # nosec B404 - the type of child_process.run's answer

_TESTS = Path(__file__).resolve().parent

#: How long one run of a small project is let go before it is killed [s].
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

#: A test module run after one that changes a setting: each setting it reads
#: must be the one it found, deep, as it was imported.
_FINDS = """\
import copy

import matplotlib

KEYS = ("axes.grid", "lines.linewidth", "font.family")
FOUND = {key: copy.deepcopy(dict.__getitem__(matplotlib.rcParams, key)) for key in KEYS}


def test_that_draws():
    for key in KEYS:
        assert dict.__getitem__(matplotlib.rcParams, key) == FOUND[key], key
"""

#: pytest run by a Python that finds no matplotlib, as on an install of the
#: base dependencies, with the arguments it is given.
_WITHOUT_MATPLOTLIB = '''\
import sys


class _NoMatplotlib:
    """Finds matplotlib nowhere."""

    def find_spec(self, name, path=None, target=None):
        if name == "matplotlib" or name.startswith("matplotlib."):
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return None


sys.meta_path.insert(0, _NoMatplotlib())

import pytest

sys.exit(pytest.main(sys.argv[1:]))
'''

#: A test with no matplotlib to import.
_PLAIN = """\
import sys

import pytest


def test_without_matplotlib():
    with pytest.raises(ModuleNotFoundError):
        import matplotlib
    assert "matplotlib" not in sys.modules
"""


def _pytest(
    project: Path, *args: str, python: tuple[str, ...] = ("-m", "pytest")
) -> subprocess.CompletedProcess[str]:
    """Run pytest on the small project in *project*, with only the plugins *args* ask for.

    The guard is imported from this directory; the plugins installed beside
    pytest are not loaded, nor the options or the backend this run was given.
    """
    (project / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "MPLBACKEND"}
    }
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_TESTS), *filter(None, [os.environ.get("PYTHONPATH")])]
    )
    return child_process.run(
        [
            sys.executable,
            *python,
            *args,
            "-p",
            "no:cacheprovider",
            "-c",
            str(project / "pytest.ini"),
            "--rootdir",
            str(project),
        ],
        capture_output=True,
        text=True,
        cwd=project,
        env=env,
        timeout=_RUN_S,
    )


def test_the_suite_loads_the_guard(pytestconfig: pytest.Config) -> None:
    assert pytestconfig.pluginmanager.has_plugin("matplotlib_guard")


def test_the_guard_lets_a_test_run_where_matplotlib_cannot_be_imported(
    tmp_path: Path,
) -> None:
    """matplotlib is an optional extra: until something imports it, the guard does nothing."""
    (tmp_path / "test_plain.py").write_text(_PLAIN, encoding="utf-8")
    done = _pytest(
        tmp_path,
        "-p",
        "matplotlib_guard",
        "test_plain.py",
        python=("-c", _WITHOUT_MATPLOTLIB),
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert "1 passed" in done.stdout, done.stdout


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
    pytest.importorskip("matplotlib")
    (tmp_path / "styled.py").write_text(_STYLED, encoding="utf-8")
    (tmp_path / "test_a_imports.py").write_text(_IMPORTS, encoding="utf-8")
    (tmp_path / "test_b_draws.py").write_text(_DRAWS, encoding="utf-8")
    done = _pytest(tmp_path, *plugin, "-rf", "test_a_imports.py", "test_b_draws.py")
    assert done.returncode == status, done.stdout + done.stderr
    assert summary in done.stdout, done.stdout


@pytest.mark.parametrize(
    ("change", "setting", "failure"),
    [
        pytest.param(
            'matplotlib.rcParams["axes.grid"] = not matplotlib.rcParams["axes.grid"]',
            "axes.grid",
            None,
            id="assigned",
        ),
        pytest.param(
            'matplotlib.rcParams["lines.linewidth"] += 1.0',
            "lines.linewidth",
            "the test's own failure",
            id="assigned-by-a-test-that-fails",
        ),
        pytest.param(
            'matplotlib.rcParams["font.family"].append("monospace")',
            "font.family",
            None,
            id="changed-in-place",
        ),
    ],
)
def test_a_test_that_leaves_a_setting_changed_fails_and_the_next_test_finds_it_put_back(
    change: str, setting: str, failure: str | None, tmp_path: Path
) -> None:
    """The setting is named in the test's failure, and the test after it finds it as it was.

    A test that fails on its own as well, with *failure*, reports both
    failures, and its setting is put back all the same.
    """
    pytest.importorskip("matplotlib")
    changes = f"import matplotlib\n\n\ndef test_that_changes():\n    {change}\n"
    if failure is not None:
        changes += f"    raise AssertionError({failure!r})\n"
    (tmp_path / "test_a_changes.py").write_text(changes, encoding="utf-8")
    (tmp_path / "test_b_finds.py").write_text(_FINDS, encoding="utf-8")
    done = _pytest(
        tmp_path, "-p", "matplotlib_guard", "-v", "test_a_changes.py", "test_b_finds.py"
    )
    assert done.returncode == 1, done.stdout + done.stderr
    assert "ERROR at teardown of test_that_changes" in done.stdout, done.stdout
    assert f"left 1 matplotlib setting(s) changed ({setting})" in done.stdout, (
        done.stdout
    )
    assert "test_b_finds.py::test_that_draws PASSED" in done.stdout, done.stdout
    if failure is not None:
        assert "test_a_changes.py::test_that_changes FAILED" in done.stdout, done.stdout
        assert f"AssertionError: {failure}" in done.stdout, done.stdout


def test_this_test_starts_with_the_settings_matplotlib_read() -> None:
    """Whatever this worker imported or ran before this test, its settings are matplotlib's own."""
    mpl = pytest.importorskip("matplotlib")
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
