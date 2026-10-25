#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``shutil.which`` as Windows answers it, for tests of a program lookup that run on any system.

Windows looks a bare name up in the working directory before ``PATH`` and
finds ``name.exe`` for ``name``; a name with a directory is looked up in that
directory alone. :func:`which` does the same on Linux and macOS, so a test
that sets ``sys.platform`` to ``"win32"`` and puts it in the place of
``shutil.which`` holds the Windows rule on every runner.
"""

from __future__ import annotations

import os
from pathlib import Path


def which(name: str) -> str | None:
    """What ``shutil.which(name)`` returns on Windows: the directory it searched as given, ``"."`` included."""
    given = Path(name)
    places = (
        [str(given.parent)]
        if given.name != name
        else [os.curdir, *os.environ["PATH"].split(os.pathsep)]
    )
    for place in places:
        for candidate in (given.name, f"{given.name}.exe"):
            if (Path(place) / candidate).is_file():
                return f"{place}{os.sep}{candidate}"
    return None
