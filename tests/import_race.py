#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Import one package of phonometry while a second thread races each first touch.

Run as ``python import_race.py <package>`` in a fresh interpreter; it prints a
JSON list of the races the import loses and exits 0.

CPython takes the lock of a module before it imports the module's parent
package. A module that imports a leaf of another package, ``from
..filters.weighting import weighting_filter``, while ``phonometry.filters`` is
not loaded yet, therefore holds the lock of ``filters.weighting`` and then asks
for the lock of ``filters``. A second thread importing ``phonometry.filters``
at that moment holds that lock, runs the package's ``__init__``, which imports
``filters.weighting``, and asks for the lock the first thread holds: CPython
finds the cycle and raises ``_DeadlockError`` in one of them. Two threads
released together hit that window often but not always, so a test built on a
plain race passes by luck.

This probe makes the window certain. It wraps the three functions of the
import system every import goes through. Whenever the main thread, importing
the package it was given, takes the lock of a module of phonometry whose
parent package is not loaded, on behalf of a module of another top-level
package, it pauses there and starts a second thread that imports that parent
package, and waits for it. The second thread never waits on the first: the
moment it asks for a module whose lock the first thread holds, which in a real
interleaving is the deadlock, the probe records the race and stops that
import. The main thread then carries on, and the import completes, so one run
reports every race the package can lose, not only the first.

An import a function makes once its module is loaded, as a renderer's ``from
..signals.levels import _REF_PRESSURE`` when a record draws, has no module
being imported above it; the probe takes the module whose function runs the
statement for its importer, so :func:`watch` reports the races a call loses.
"""

from __future__ import annotations

# The import system's own module: every import statement goes through the
# three functions this probe wraps, looked up on it at each import.
import _frozen_importlib as bootstrap
import importlib
import inspect
import json
import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    #: How the import system hands a module to import on: ``_gcd_import``.
    Importer = Callable[[str], ModuleType]

#: How long the second thread may take to import a package [s]: the slowest
#: domain imports in under ten seconds on a cold cache.
_RACE_S = 120.0


class _Refused(BaseException):
    """Stops the second thread's import where it would wait on the first.

    A ``BaseException``, so that no ``except ImportError`` or ``except
    Exception`` in the code being imported takes it for its own failure.
    """


class _Probe:
    """The wrapped import functions and what they saw."""

    def __init__(self) -> None:
        self.find_and_load: Callable[[str, Importer], ModuleType] = (
            bootstrap._find_and_load
        )
        self.find_and_load_unlocked: Callable[[str, Importer], ModuleType] = (
            bootstrap._find_and_load_unlocked
        )
        self.lock_unlock_module: Callable[[str], None] = bootstrap._lock_unlock_module
        self.local = threading.local()
        #: The modules whose lock the main thread holds while it imports them.
        self.held: dict[str, str] = {}
        self.racers: set[int] = set()
        self.races: list[dict[str, str]] = []

    def stack(self) -> list[str]:
        """The modules the current thread is importing, outermost first."""
        stack: list[str] | None = getattr(self.local, "stack", None)
        if stack is None:
            stack = self.local.stack = []
        return stack

    def refuse_a_held_module(self, name: str) -> None:
        """Record and stop the second thread when it asks for a held module."""
        if threading.get_ident() not in self.racers or name not in self.held:
            return
        race = dict(self.local.race)
        race["waits_on"] = name
        race["while_importing"] = " > ".join(self.stack())
        self.races.append(race)
        raise _Refused(name)

    def wrapped_find_and_load(self, name: str, import_: Importer) -> ModuleType:
        """``_find_and_load``: the entry of every import not yet in sys.modules."""
        self.refuse_a_held_module(name)
        stack = self.stack()
        stack.append(name)
        try:
            return self.find_and_load(name, import_)
        finally:
            stack.pop()

    def wrapped_lock_unlock_module(self, name: str) -> None:
        """``_lock_unlock_module``: the wait on a module another thread is running."""
        self.refuse_a_held_module(name)
        self.lock_unlock_module(name)

    def wrapped_find_and_load_unlocked(
        self, name: str, import_: Importer
    ) -> ModuleType:
        """``_find_and_load_unlocked``: runs with the module's lock held."""
        if threading.get_ident() in self.racers:
            return self.find_and_load_unlocked(name, import_)
        stack = self.stack()
        importer = stack[-2] if len(stack) > 1 else _caller()
        # A module can come back here while it is loading, as a parent of its
        # own import or through an import cycle: the outer call keeps it held.
        outer = name in self.held
        self.held[name] = importer
        try:
            parent = name.rpartition(".")[0]
            if (
                parent.startswith("phonometry.")
                and parent not in sys.modules
                and importer.startswith("phonometry.")
                and _top(importer) != _top(name)
            ):
                self.race(parent, holder=name, importer=importer)
            return self.find_and_load_unlocked(name, import_)
        finally:
            if not outer:
                del self.held[name]

    def race(self, package: str, *, holder: str, importer: str) -> None:
        """Import *package* in a second thread while this one holds *holder*."""
        outcome: list[BaseException] = []

        def run() -> None:
            self.racers.add(threading.get_ident())
            self.local.race = {
                "importer": importer,
                "imports": holder,
                "racer_imports": package,
            }
            try:
                importlib.import_module(package)
            except _Refused:
                pass
            # Every failure of the racing import is a finding.
            except BaseException as error:  # noqa: BLE001
                outcome.append(error)

        racer = threading.Thread(target=run, name=f"racing {package}")
        racer.start()
        racer.join(_RACE_S)
        if racer.is_alive():
            self.races.append(
                {
                    "importer": importer,
                    "imports": holder,
                    "racer_imports": package,
                    "waits_on": f"nothing it finished within {_RACE_S:g} s",
                }
            )
        for error in outcome:
            self.races.append(
                {
                    "importer": importer,
                    "imports": holder,
                    "racer_imports": package,
                    "waits_on": f"{type(error).__name__}: {error}",
                }
            )

    def install(self) -> None:
        """Put the wrappers where the import system looks them up."""
        bootstrap._find_and_load = self.wrapped_find_and_load
        bootstrap._find_and_load_unlocked = self.wrapped_find_and_load_unlocked
        bootstrap._lock_unlock_module = self.wrapped_lock_unlock_module


def _caller() -> str:
    """The module of phonometry whose code runs an import no other import holds.

    The import statement runs in a frame of that module, under the frames of
    the import system and of this probe, none of which belongs to phonometry.
    ``""`` when no frame does: the import comes from the probe's caller.
    """
    frame = inspect.currentframe()
    while frame is not None:
        name = frame.f_globals.get("__name__", "")
        if name.startswith("phonometry."):
            return str(name)
        frame = frame.f_back
    return ""


def _top(module: str) -> str:
    """The top-level package of phonometry *module* is in, ``""`` for the root."""
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else ""


def watch() -> list[dict[str, str]]:
    """Put the probe in place from here on, and return the list of its races.

    The list fills as the process imports: run what the test drives, then read
    it. The probe stays in place until the process ends.
    """
    probe = _Probe()
    probe.install()
    return probe.races


def main(package: str) -> int:
    """Import ``phonometry.<package>`` under the probe and print its races."""
    import phonometry  # the root imports no package of its own, so it races nothing

    probe = _Probe()
    probe.install()
    importlib.import_module(f"{phonometry.__name__}.{package}")
    print(json.dumps(probe.races))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
