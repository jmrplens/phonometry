#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A test whose teardown hangs is ended at pytest's limit, failed or not (``hang_guard``).

Each case runs pytest on a small project of its own, in a process of its
own, with a limit of :data:`_LIMIT_S` seconds and a fixture whose teardown
sleeps :data:`_TEARDOWN_S` seconds: long past the limit, and long past the
time the run may take once the limit has ended it.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import child_process
import pytest

_TESTS = Path(__file__).resolve().parent

#: The limit the project runs under [s].
_LIMIT_S = 2
#: How long the fixture's teardown would sleep if nothing ended it [s].
_TEARDOWN_S = 60
#: How long the run may take once the limit has ended it [s]: the limit,
#: and a start of pytest on a slow runner. Well short of :data:`_TEARDOWN_S`.
_ENDED_S = 30.0
#: How long the run is let go before it is killed [s].
_RUN_S = 120.0

_PROJECT_TESTS = f"""\
import time

import pytest


@pytest.fixture
def slow_to_tear_down():
    yield
    time.sleep({_TEARDOWN_S})


@pytest.fixture
def broken(slow_to_tear_down):
    raise RuntimeError("the setup fails")


def test_that_passes(slow_to_tear_down):
    pass


def test_whose_call_fails(slow_to_tear_down):
    raise AssertionError("the call fails")


def test_whose_setup_fails(broken):
    pass
"""


@pytest.mark.parametrize(
    "case", ["test_that_passes", "test_whose_call_fails", "test_whose_setup_fails"]
)
def test_a_test_whose_teardown_hangs_is_ended_at_the_limit(
    case: str, tmp_path: Path
) -> None:
    """pytest lifts its limit when a test fails; ``hang_guard`` sets it again for the teardown."""
    (tmp_path / "pytest.ini").write_text(
        f"[pytest]\nfaulthandler_timeout = {_LIMIT_S}\n"
        "faulthandler_exit_on_timeout = true\n",
        encoding="utf-8",
    )
    (tmp_path / "test_project.py").write_text(_PROJECT_TESTS, encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
    }
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_TESTS), *filter(None, [os.environ.get("PYTHONPATH")])]
    )
    started = time.monotonic()
    done = child_process.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "hang_guard",
            "-p",
            "no:cacheprovider",
            "-c",
            str(tmp_path / "pytest.ini"),
            "--rootdir",
            str(tmp_path),
            f"test_project.py::{case}",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        timeout=_RUN_S,
    )
    elapsed = time.monotonic() - started
    assert elapsed < _ENDED_S, (
        f"the run took {elapsed:.0f} s: the teardown had no limit"
    )
    assert f"Timeout (0:00:0{_LIMIT_S})!" in done.stderr
    assert "in slow_to_tear_down" in done.stderr, "the stacks do not show the teardown"
    assert done.returncode == 1
