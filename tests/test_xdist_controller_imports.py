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
so the receivers find every warning's module already imported.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

import child_process

_TESTS = pathlib.Path(__file__).resolve().parent

#: What a fresh interpreter prints: the domains imported after the hook ran.
_PROBE = textwrap.dedent(
    """
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
    """
)


def _domains_imported(numprocesses: int, *, worker: bool) -> tuple[int, int]:
    done = child_process.run(
        [
            sys.executable,
            "-c",
            _PROBE,
            str(numprocesses),
            "worker" if worker else "controller",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=_TESTS,
        timeout=300,  # importing the 21 domains takes a few seconds
    )
    imported, total = (int(line) for line in done.stdout.split())
    return imported, total


def test_the_controller_of_a_parallel_run_imports_every_domain() -> None:
    imported, total = _domains_imported(4, worker=False)
    assert imported == total


def test_a_worker_and_a_serial_run_import_no_domain_for_it() -> None:
    assert _domains_imported(4, worker=True)[0] == 0
    assert _domains_imported(0, worker=False)[0] == 0
