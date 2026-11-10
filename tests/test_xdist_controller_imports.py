#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The pytest-xdist controller imports every domain before a worker reports.

pytest-xdist 3.8 rebuilds each warning a worker forwards in the controller's
receiver threads, and to rebuild it imports the module of the warning's class
by its dotted name, in as many threads as there are workers. Two of them
importing ``phonometry.emission._shared`` and
``phonometry.environment.propagation.barrier_in_situ`` at once lost the race
to ``_DeadlockError``, and with ``--max-worker-restart=0`` the run ended at an
INTERNALERROR with the rest of its tests unrun. ``tests/conftest.py`` imports
the domains on the controller, in its main thread, before any worker starts,
so the receivers find every warning's module already imported. The modules
that define a warning class are read off the source, not off what an import
loaded, so a warning moved to a module no domain package imports fails here
instead of waiting for the race.
"""

from __future__ import annotations

import ast
import json
import pathlib
import sys
import textwrap

import child_process
import pytest

import phonometry

_TESTS = pathlib.Path(__file__).resolve().parent

#: The two modules whose warnings the receivers deadlocked on.
_REPORTED = (
    "phonometry.emission._shared",
    "phonometry.environment.propagation.barrier_in_situ",
)


def _warning_modules() -> list[str]:
    """Every module of the package whose source defines a warning class."""
    package = pathlib.Path(phonometry.__file__).resolve().parent
    found: list[str] = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(
            isinstance(node, ast.ClassDef)
            and any("Warning" in ast.unparse(base) for base in node.bases)
            for node in tree.body
        ):
            parts = path.relative_to(package.parent).with_suffix("").parts
            found.append(".".join(parts[:-1] if parts[-1] == "__init__" else parts))
    return found


#: What a fresh interpreter prints: the domains imported after the hook ran.
_PROBE = textwrap.dedent(
    """
    import json
    import sys
    import types

    import conftest
    import phonometry

    numprocesses, worker = int(sys.argv[1]), sys.argv[2] == "worker"
    config = types.SimpleNamespace(option=types.SimpleNamespace(numprocesses=numprocesses))
    if worker:
        config.workerinput = {"workerid": "gw0"}
    conftest.import_domains_on_the_xdist_controller(config)
    print(sum(f"phonometry.{name}" in sys.modules for name in phonometry._PACKAGES))
    print(len(phonometry._PACKAGES))
    print(json.dumps([name for name in json.loads(sys.argv[3]) if name not in sys.modules]))
    """
)


def _probe(
    numprocesses: int, *, worker: bool, warning_modules: list[str]
) -> tuple[int, int, list[str]]:
    """The domains imported after the hook ran, of how many, and those of
    *warning_modules* still not imported.
    """
    done = child_process.run(
        [
            sys.executable,
            "-c",
            _PROBE,
            str(numprocesses),
            "worker" if worker else "controller",
            json.dumps(warning_modules),
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=_TESTS,
        timeout=300,  # importing the 21 domains takes a few seconds
    )
    imported, total, unloaded = done.stdout.splitlines()[-3:]
    return int(imported), int(total), json.loads(unloaded)


def _domains_imported(numprocesses: int, *, worker: bool) -> tuple[int, int]:
    imported, total, _ = _probe(numprocesses, worker=worker, warning_modules=[])
    return imported, total


def test_the_controller_of_a_parallel_run_imports_every_domain() -> None:
    imported, total = _domains_imported(4, worker=False)
    assert imported == total


@pytest.mark.whole_tree
def test_the_controller_imports_every_module_that_defines_a_warning() -> None:
    """A receiver imports a warning's module by its name; the hook has done it first."""
    modules = _warning_modules()
    assert set(_REPORTED) <= set(modules)
    assert _probe(4, worker=False, warning_modules=modules)[2] == []


def test_a_worker_and_a_serial_run_import_no_domain_for_it() -> None:
    assert _domains_imported(4, worker=True)[0] == 0
    assert _domains_imported(0, worker=False)[0] == 0
