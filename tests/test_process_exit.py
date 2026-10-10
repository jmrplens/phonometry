#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every process that records for a figure audit writes its fragment at exit.

The three figure audits (annotations, ticks, language) write what a process
measured from an exit handler registered through
``scripts/process_exit.py``. A child that :mod:`multiprocessing` forks leaves
through ``os._exit``, and only Python 3.13 runs :mod:`atexit` there; on 3.12 a
handler registered with :mod:`atexit` alone never runs in the child and the
child's recording is lost. These tests fork for real, so they fail on 3.12 if
the handler goes back to :mod:`atexit` alone, and on any version if it runs
twice.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import pathlib
import subprocess  # nosec B404 - runs this interpreter on a fixed script
import sys

import pytest

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import figure_language_audit as language_audit
import process_exit

# The figure, diagram and badge tooling is tied to the pinned figure stack its
# artefacts are drawn with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack

_FORK = pytest.mark.skipif(
    "fork" not in multiprocessing.get_all_start_methods(),
    reason="a forked child exists only where os.fork does",
)


def _append_a_line(path: str) -> None:
    with pathlib.Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"{os.getpid()}\n")


def _register_in_child(path: str) -> None:
    """A forked child's whole job: register the handler and return."""
    process_exit.run_at_exit(lambda: _append_a_line(path))


@_FORK
def test_a_forked_child_runs_its_handler_exactly_once(tmp_path: pathlib.Path) -> None:
    """On 3.12 multiprocessing's exit function runs it, on 3.13 atexit does."""
    record = tmp_path / "ran.txt"
    child = multiprocessing.get_context("fork").Process(
        target=_register_in_child, args=(str(record),)
    )
    child.start()
    child.join()

    assert child.exitcode == 0
    assert record.read_text(encoding="utf-8") == f"{child.pid}\n"


def test_a_process_that_exits_normally_runs_its_handler_exactly_once(
    tmp_path: pathlib.Path,
) -> None:
    """At interpreter shutdown atexit and multiprocessing's exit both reach it."""
    record = tmp_path / "ran.txt"
    script = (
        "import pathlib, sys\n"
        f"sys.path.insert(0, {str(_SCRIPTS)!r})\n"
        "import process_exit\n"
        f"path = pathlib.Path({str(record)!r})\n"
        "process_exit.run_at_exit(lambda: path.open('a').write('ran\\n'))\n"
    )
    done = subprocess.run(  # nosec B603 - this interpreter, a fixed script
        [sys.executable, "-c", script], check=False, capture_output=True, text=True
    )

    assert done.returncode == 0, done.stderr
    assert record.read_text(encoding="utf-8") == "ran\n"


# --------------------------------------------------------------------------
# The language audit, whose forked animation variants are the corpus's one
# real fork.


@pytest.fixture
def recording(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    """Recording on into this test's directory, an empty tally, no handler yet."""
    directory = tmp_path / "recording"
    monkeypatch.setenv(language_audit.AUDIT_ENV, str(directory))
    monkeypatch.setattr(language_audit, "_PASSES", {"english": {}, "spanish": {}})
    monkeypatch.setattr(language_audit, "_REGISTERED", False)
    return directory


def _visit_in_child(stem: str) -> None:
    """A forked animation variant: visit one asset in Spanish and exit."""
    language_audit.visit(stem, "es")
    language_audit.untranslated("Untranslated label")


@_FORK
def test_a_variant_forked_after_the_parent_visited_writes_its_own_fragment(
    recording: pathlib.Path,
) -> None:
    """The child's fragment holds the child's asset and not the parent's."""
    language_audit.visit("drawn_in_the_parent", "en")
    assert language_audit._REGISTERED, "the parent has to have registered"

    child = multiprocessing.get_context("fork").Process(
        target=_visit_in_child, args=("drawn_in_the_child",)
    )
    child.start()
    child.join()

    assert child.exitcode == 0
    fragment = recording / f"{child.pid}.json"
    assert fragment.exists(), "the variant recorded an asset and wrote nothing down"
    assert json.loads(fragment.read_text(encoding="utf-8")) == {
        "english": {},
        "spanish": {"drawn_in_the_child": ["Untranslated label"]},
    }
