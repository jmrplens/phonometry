#  Copyright (c) 2026. Jose Manuel Requena Plens
import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pinned_stack
import pytest

# Select a non-interactive matplotlib backend for the headless test suite.
# The library no longer forces a backend (see issue #52), so the test harness
# must opt into Agg itself; otherwise matplotlib picks a GUI backend (e.g.
# TkAgg on Windows runners) and figure creation fails without a display/Tcl.
# Set at import time so it takes effect before any test module imports pyplot.
os.environ.setdefault("MPLBACKEND", "Agg")


def pytest_configure(config: pytest.Config) -> None:
    """Configure environment variables for the test session.
    We disable Numba JIT to allow coverage tools to trace inside the kernels.
    """
    # Disable JIT by default for tests to ensure 100% coverage reporting.
    # setdefault: the CI tests-perf job sets NUMBA_DISABLE_JIT=0 explicitly
    # to exercise the jitted kernel; an externally-set value must win.
    os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
    # A placement in the developer's shell must not move the suite onto a GPU
    # or refuse it: the tests that want a device ask for it by name.
    os.environ.pop("PHONOMETRY_COMPUTE", None)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        pinned_stack.OPTION,
        action="store_true",
        default=False,
        dest="without_pinned_stack",
        help=(
            "leave out the tests of the figure, diagram and badge tooling, "
            "which runs on the pinned figure stack only"
        ),
    )


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Leave a pinned-stack test module out before it is imported, when asked.

    At the dependency floors such a module can fail on import, and a module
    that fails on import is an error whatever mark it carries; see
    ``tests/pinned_stack.py``.
    """
    if not config.getoption("without_pinned_stack"):
        return None
    if collection_path.suffix != ".py" or not collection_path.name.startswith("test_"):
        return None
    if pinned_stack.declares(collection_path.read_text(encoding="utf-8")):
        return True
    return None


#: The longest id a test may have [characters]. pytest writes the id of the
#: running test into the PYTEST_CURRENT_TEST environment variable, and Windows
#: holds no variable longer than 32767 characters: a parametrized case whose id
#: is its own large input fails its setup there. The bound is far below that,
#: so such an id fails on every system.
_MAX_NODE_ID = 2000


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Fail a test whose id is longer than :data:`_MAX_NODE_ID` characters.

    It runs before pytest names the test in PYTEST_CURRENT_TEST, so Windows
    shows this message too. A setup hook rather than a collection hook:
    under pytest-xdist the workers collect, and a refusal raised there
    reaches the run as an internal error without its message.
    """
    nodeid = item.nodeid
    if len(nodeid) > _MAX_NODE_ID:
        pytest.fail(
            f"this test's id is {len(nodeid)} characters long, more than the "
            f"{_MAX_NODE_ID} allowed: Windows cannot hold it in PYTEST_CURRENT_TEST. "
            "Give the case a short id (pytest.param(..., id=...) or ids=).",
            pytrace=False,
        )


@pytest.fixture(autouse=True)
def _matplotlib_settings_unchanged() -> Iterator[None]:
    """Fail a test that leaves matplotlib's global settings changed.

    ``plt.style.use`` or an assignment to ``rcParams`` outlives the test that
    made it and draws the figures of whatever test the worker runs next, so a
    figure test passed or failed with the order the workers were dealt: the
    dark page the contrast tests left behind turned a legend frame black, and
    the legend check of another module no longer saw it. A test changes the
    settings inside ``matplotlib.rc_context()`` or ``plt.style.context()``.
    The settings are read raw, so no deprecated key warns.
    """
    matplotlib = sys.modules.get("matplotlib")
    before = None if matplotlib is None else dict.copy(matplotlib.rcParams)
    yield
    if before is None:
        return
    after = dict.copy(sys.modules["matplotlib"].rcParams)
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


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    """Close every pyplot figure a test leaves open.

    A figure made through pyplot, as every ``.plot()`` makes it, stays in
    pyplot's registry until it is closed, so a worker that runs hundreds of
    plotting tests would hold every one of their figures in memory to the end
    of the session and warn past the twentieth. pyplot is looked up rather
    than imported, so a test that never plots does not pay for importing it.
    """
    yield
    pyplot = sys.modules.get("matplotlib.pyplot")
    if pyplot is not None:
        pyplot.close("all")


# The modules whose tests dominate the wall clock (steady-state FDTD runs,
# the conformance registry, ECMA-418-2 chains, report generation). Collection
# order is dispatch order under pytest-xdist, so fronting them lets the long
# tests start while the workers still have plenty of short tests left to
# backfill with; leaving them in alphabetical collection order used to strand
# a 3-5 minute test on a lone worker at the end of the run.
_FRONTLOADED_MODULES = (
    "tests/simulation/test_fdtd_ntff.py",
    "tests/test_conformance_report.py",
    "tests/simulation/test_elastic_fdtd.py",
    "tests/aircraft/test_rotorcraft_norah2.py",
    "tests/test_generate_reports.py",
    "tests/simulation/test_elastic_fluid_solid.py",
    "tests/building/measurement/test_impact_insulation.py",
    "tests/building/measurement/test_insulation.py",
    "tests/psychoacoustics/quality/test_tonality_ecma.py",
    "tests/psychoacoustics/loudness/test_ecma.py",
    "tests/psychoacoustics/quality/test_fluctuation_strength_ecma.py",
    "tests/psychoacoustics/loudness/test_moore_glasberg_time.py",
    "tests/psychoacoustics/loudness/test_zwicker.py",
    "tests/underwater/propagation/test_numerical.py",
    "tests/filters/test_iec61260_report.py",
    "tests/room/test_impulse_response.py",
    "tests/test_golden_baseline.py",
)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Move the known-heavy modules to the front of the dispatch order.

    The sort is stable, so relative order inside every module (and among all
    remaining modules) is untouched.
    """
    rank = {}
    for item in items:
        path = item.nodeid.split("::", 1)[0]
        if path not in rank:
            rank[path] = len(_FRONTLOADED_MODULES)
            for i, module in enumerate(_FRONTLOADED_MODULES):
                # Match on the tail so the rank survives being invoked from
                # a different rootdir (nodeids are rootdir-relative).
                if path.endswith(module) or module.endswith(path):
                    rank[path] = i
                    break
    items.sort(key=lambda item: rank[item.nodeid.split("::", 1)[0]])
    if config.getoption("without_pinned_stack"):
        # A test marked one by one, rather than through its module's
        # pytestmark, is collected and left out here.
        dropped = [i for i in items if i.get_closest_marker(pinned_stack.MARK)]
        if dropped:
            config.hook.pytest_deselected(items=dropped)
            items[:] = [i for i in items if not i.get_closest_marker(pinned_stack.MARK)]


def pytest_report_header(config: pytest.Config) -> list[str]:
    """Report which copy of every heavy oracle set this run will read.

    The suites in ``tests/oracle_data.DATASETS`` prefer a full local copy of
    reference material that cannot be committed and fall back to the small
    committed oracle under ``tests/data/``. Printing the resolution keeps a
    green run from being ambiguous about which of the two produced it.
    """
    import oracle_data

    lines = [oracle_data.resolve(d).describe() for d in oracle_data.DATASETS]
    return ["oracle data:", *[f"  {line}" for line in lines]]
