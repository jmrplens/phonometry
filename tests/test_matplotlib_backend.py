#  Copyright (c) 2026. Jose M. Requena-Plens

"""
Tests ensuring the package does not hijack the global matplotlib backend.

Importing pyoctaveband must not force a specific (e.g. non-interactive)
backend, so the package can be used during interactive exploration
(IPython, Jupyter). See issue #52.
"""

import os
import subprocess
import sys


def test_import_does_not_override_matplotlib_backend() -> None:
    """Importing pyoctaveband must preserve the user's chosen backend."""
    code = (
        "import matplotlib\n"
        # Pick an explicit, always-available backend the user might have set.
        "matplotlib.use('svg')\n"
        "before = matplotlib.get_backend()\n"
        "import pyoctaveband\n"
        "after = matplotlib.get_backend()\n"
        "assert before == after, f'backend changed: {before!r} -> {after!r}'\n"
    )
    # Propagate the parent's sys.path so the subprocess can import the package
    # even when it is only on sys.path (e.g. pytest without an installed build).
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
