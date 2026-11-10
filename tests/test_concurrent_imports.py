#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Two threads importing packages of phonometry at once never deadlock.

CPython locks a module before it imports the module's parent package, so a
module that imports a leaf of another package, ``from ..filters.weighting
import ...`` while ``phonometry.filters`` is not loaded, deadlocks against a
thread importing ``phonometry.filters`` itself, whose ``__init__`` imports
that leaf: one of them raises ``_DeadlockError``. A user meets it after a
plain ``import phonometry``, from a thread pool that reads two domains.

:mod:`import_race` makes that window certain instead of likely, so the first
test fails on every run while one such import is left, and passes on every
run once none is.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import threading
from pathlib import Path

import child_process
import pytest

import phonometry

_RACE = Path(__file__).with_name("import_race.py")

#: The twenty-one domain packages the root publishes.
DOMAINS = sorted(
    name for name in phonometry.__all__ if name.islower() and not name.startswith("_")
)

#: How long one import under the probe may take [s]: the slowest domain takes
#: two seconds on a warm cache, about ten on a cold one.
_IMPORT_S = 300


@pytest.mark.parametrize("domain", DOMAINS)
def test_importing_a_domain_loses_no_race_to_a_second_thread(domain: str) -> None:
    """No module of the domain reaches into a package another thread may be importing."""
    done = child_process.run(
        [sys.executable, str(_RACE), domain],
        timeout=_IMPORT_S,
        capture_output=True,
        text=True,
        check=True,
    )
    races = json.loads(done.stdout.splitlines()[-1])
    assert not races, f"importing phonometry.{domain} can deadlock:\n" + "\n".join(
        f"  {race['importer']} imports {race['imports']} before "
        f"{race['racer_imports']} is loaded; a thread importing "
        f"{race['racer_imports']} meanwhile waits on {race['waits_on']}"
        for race in races
    )


#: Records whose renderer imports code of a domain the record's own domain does
#: not load: how the record is made, with only its domain imported, and the
#: call that draws or prints it. ``{path}`` is a file the call may write.
_RENDERS: dict[str, tuple[str, str]] = {
    "TimeWeightedEnvelope.plot": (
        "import numpy as np\n"
        "from phonometry import filters, io\n"
        "signal = io.Signal(np.ones(4800), 48000.0, calibration_factor=1.0)\n"
        "record = filters.time_weighting(signal)\n",
        "record.plot()",
    ),
    "Signal.plot(scale='db')": (
        "import numpy as np\n"
        "from phonometry import io\n"
        "record = io.Signal(np.ones(480), 48000.0, calibration_factor=1.0)\n",
        "record.plot(scale='db')",
    ),
    "TransferStiffnessResult.report": (
        "import numpy as np\n"
        "from phonometry import vibration\n"
        "frequencies = np.array([100.0, 125.0, 160.0, 200.0])\n"
        "u1 = np.full(4, 1e-6 + 0j)\n"
        "force = (1e6 + 2j * np.pi * frequencies * 80.0) * u1\n"
        "record = vibration.TransferStiffnessResult(\n"
        "    frequencies=frequencies,\n"
        "    transfer_stiffness=vibration.transfer_stiffness_direct(force, u1),\n"
        "    blocking_mass=None,\n"
        ")\n",
        "record.report({path})",
    ),
    "StructureBornePowerResult.report": (
        "import numpy as np\n"
        "from phonometry import building\n"
        "record = building.reception_plate_power(\n"
        "    np.array([88.0, 90.0, 86.0, 82.0]),\n"
        "    frequency=np.array([125.0, 250.0, 500.0, 1000.0]),\n"
        "    mass_per_area=25.0,\n"
        "    area=1.2,\n"
        "    reverberation_time=0.3,\n"
        ")\n",
        "record.report({path})",
    ),
    "ToneAudibilityResult.report": (
        "import reference_data as ref\n"
        "from phonometry import psychoacoustics\n"
        "record = psychoacoustics.analyze_spectrum(\n"
        "    ref.ISO20065_E1_LEVELS,\n"
        "    frequencies=ref.ISO20065_E1_FREQUENCIES,\n"
        "    line_spacing_hz=ref.ISO20065_LINE_SPACING,\n"
        ")\n",
        "record.report({path})",
    ),
}


@pytest.mark.parametrize("render", sorted(_RENDERS))
def test_a_record_draws_and_prints_without_a_race(render: str, tmp_path: Path) -> None:
    """A renderer reaches another domain's code only through its package.

    A record draws or prints itself with its own domain loaded and, when it is
    the only one, no other: a renderer that imports a module inside another
    domain (``from ..signals.levels import ...``) takes that module's lock
    before its package's, and a thread importing the package meanwhile
    deadlocks against it, as two threads importing two domains did.
    """
    setup, call = _RENDERS[render]
    # The child imports matplotlib before anything else, and a report draws
    # its figures with it, so every case needs it and a report reportlab too.
    pytest.importorskip("matplotlib")
    if call.startswith("record.report"):
        pytest.importorskip("reportlab")
    program = "\n".join(
        [
            "import json",
            "import sys",
            f"sys.path.insert(0, {str(_RACE.parent)!r})",
            "import matplotlib",
            "matplotlib.use('Agg')",
            "import import_race",
            setup,
            "races = import_race.watch()",
            call.format(path=repr(str(tmp_path / "record.pdf"))),
            "print(json.dumps(races))",
        ]
    )
    done = child_process.run(
        [sys.executable, "-c", program],
        timeout=_IMPORT_S,
        capture_output=True,
        text=True,
        check=True,
    )
    races = json.loads(done.stdout.splitlines()[-1])
    assert not races, f"{render} can deadlock:\n" + "\n".join(
        f"  {race['importer']} imports {race['imports']} before "
        f"{race['racer_imports']} is loaded; a thread importing "
        f"{race['racer_imports']} meanwhile waits on {race['waits_on']}"
        for race in races
    )


def test_two_domains_read_from_a_thread_pool_both_import() -> None:
    """The user's case: one ``import phonometry``, then two domains from two threads."""
    program = textwrap.dedent(
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor

        import phonometry as ph

        names = ["electroacoustics", "vibration"]
        barrier = threading.Barrier(len(names))

        def touch(name):
            barrier.wait(60)
            return getattr(ph, name).__name__

        with ThreadPoolExecutor(len(names)) as pool:
            futures = [pool.submit(touch, name) for name in names]
            print([future.result(timeout=120) for future in futures])
        """
    )
    done = child_process.run(
        [sys.executable, "-c", program],
        timeout=_IMPORT_S,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == str(
        ["phonometry.electroacoustics", "phonometry.vibration"]
    )


def test_the_root_imports_one_domain_at_a_time(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two threads reading two domains off the root take turns at the import.

    The first touch of ``phonometry.<domain>`` imports the package, and the
    root holds a lock around that import, so a thread pool reading several
    domains imports them one after another rather than interleaving their
    module locks. The import is replaced by one that waits for a second
    thread to join it: with the lock the second never does.
    """
    entered = threading.Event()
    joined = threading.Event()
    inside = 0
    most = 0
    count = threading.Lock()

    def slow_import(name: str, package: str | None = None) -> object:
        nonlocal inside, most
        with count:
            inside += 1
            most = max(most, inside)
            if inside > 1:
                joined.set()
        entered.set()
        joined.wait(1.0)  # with no lock the second thread arrives at once
        with count:
            inside -= 1
        return object()

    monkeypatch.setattr(phonometry, "import_module", slow_import)
    for name in ("filters", "signals"):
        monkeypatch.setattr(phonometry, name, getattr(phonometry, name))
    getattr_ = vars(phonometry)["__getattr__"]
    first = threading.Thread(target=getattr_, args=("filters",))
    second = threading.Thread(target=getattr_, args=("signals",))
    first.start()
    assert entered.wait(30)
    second.start()
    first.join(30)
    second.join(30)
    assert not first.is_alive()
    assert not second.is_alive()
    assert most == 1


@pytest.mark.skipif(not hasattr(os, "fork"), reason="the platform does not fork")
def test_a_forked_child_reads_a_domain_while_another_thread_held_the_lock() -> None:
    """A child forked while a thread held the root's lock gets a lock of its own.

    The thread that held it does not exist in the child, so the inherited lock
    would never be released and the child's first ``phonometry.<domain>``
    would wait for ever.
    """
    program = textwrap.dedent(
        """
        import os
        import threading
        import time

        import phonometry as ph

        held = threading.Event()

        def hold():
            with ph._FIRST_TOUCH:
                held.set()
                time.sleep(5)

        threading.Thread(target=hold, daemon=True).start()
        held.wait(60)
        pid = os.fork()
        if pid == 0:
            print(ph.filters.__name__, flush=True)
            os._exit(0)
        for _ in range(600):
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                break
            time.sleep(0.05)
        else:
            os.kill(pid, 9)
            os.waitpid(pid, 0)
            raise SystemExit("the child waited on the inherited lock")
        """
    )
    done = child_process.run(
        [sys.executable, "-W", "ignore::DeprecationWarning", "-c", program],
        timeout=_IMPORT_S,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "phonometry.filters"
