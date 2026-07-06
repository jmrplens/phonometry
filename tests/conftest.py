#  Copyright (c) 2026. Jose M. Requena-Plens
import os
import pytest

# Select a non-interactive matplotlib backend for the headless test suite.
# The library no longer forces a backend (see issue #52), so the test harness
# must opt into Agg itself; otherwise matplotlib picks a GUI backend (e.g.
# TkAgg on Windows runners) and figure creation fails without a display/Tcl.
# Set at import time so it takes effect before any test module imports pyplot.
os.environ.setdefault("MPLBACKEND", "Agg")

def pytest_configure(config):
    """
    Configure environment variables for the test session.
    We disable Numba JIT to allow coverage tools to trace inside the kernels.
    """
    # Disable JIT by default for tests to ensure 100% coverage reporting.
    # setdefault: the CI tests-perf job sets NUMBA_DISABLE_JIT=0 explicitly
    # to exercise the jitted kernel; an externally-set value must win.
    os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

@pytest.fixture(autouse=True)
def handle_performance_tests(request):
    """
    Special fixture to re-enable JIT for performance tests.
    """
    if "test_performance.py" in request.node.fspath.strpath:
        # Re-enable JIT for performance measurements
        os.environ["NUMBA_DISABLE_JIT"] = "0"
        # Note: Numba might have already compiled/cached some things, 
        # but this ensures the performance test runs at native speed.
    yield
