#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The numba kernels where numba has nowhere to write its cache.

With the ``[perf]`` extra the two serial kernels, the impulse time weighting
and the BS.468-4 quasi-peak chain, are compiled by numba and cached on disk.
numba looks for a directory to cache in beside the module, then under
``NUMBA_CACHE_DIR`` and the user's home; a service account, ``nobody`` or a
container user with no home over a read-only install has none, and numba
refuses the decoration with ``RuntimeError: cannot cache function ...: no
locator available``. That decoration runs when the module is imported, so
fifteen domain packages failed to import. Emptying numba's list of locators
(``numba.core.caching.CacheImpl._locator_classes``, the same attribute in
numba 0.60.0 and 0.68.1) is the state such a user is in.

The child process turns the JIT on whatever the suite runs under, since
``tests/conftest.py`` turns it off by default and an interpreted kernel never
reaches numba's cache.
"""

from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

import child_process
import pytest

pytest.importorskip("numba")

_SRC = Path(__file__).resolve().parents[1] / "src"

#: Imports both packages with no cache locator, runs both kernels and prints
#: how many signatures each compiled.
_PROBE = textwrap.dedent(
    """
    import numba.core.caching as caching

    caching.CacheImpl._locator_classes = []

    import numpy as np

    from phonometry import broadcast, filters
    from phonometry.broadcast import quasi_peak
    from phonometry.filters import weighting

    levels = filters.time_weighting(np.ones(64), 48_000, mode="impulse")
    reading = broadcast.quasi_peak_meter(np.ones(4096), 48_000)
    print(
        len(weighting._apply_impulse_kernel.nopython_signatures),
        len(quasi_peak._apply_quasi_peak_kernel.nopython_signatures),
        bool(np.all(np.isfinite(levels))),
    )
    """
)

#: How long the child may take to compile both kernels [s].
_COMPILE_S = 300.0


def test_the_kernels_compile_where_numba_can_cache_nowhere() -> None:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("NUMBA_") and key != "PYTHONPATH"
    }
    env["NUMBA_DISABLE_JIT"] = "0"
    env["PYTHONPATH"] = str(_SRC)
    done = child_process.run(
        [sys.executable, "-c", _PROBE],
        timeout=_COMPILE_S,
        capture_output=True,
        text=True,
        env=env,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["1", "1", "True"]
