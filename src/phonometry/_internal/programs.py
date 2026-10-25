#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which file runs for a program the library does not ship, named by a bare name (private).

Windows looks a bare name such as ``"ssh"`` up in the working directory
before the directories ``PATH`` lists, and ``shutil.which`` does the same
unless ``NoDefaultCurrentDirectoryInExePath`` is set, so an ``ssh.exe`` or an
``ssh.bat`` left in a notebook's folder would run in place of the program the
user installed. :func:`past_the_working_directory` passes over such a file.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _first_on_path(name: str) -> str | None:
    """The first *name* in the directories ``PATH`` lists, in their order.

    Each directory is searched by a name that holds it, which
    ``shutil.which`` looks up in that directory alone, never in the working
    directory first.
    """
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if directory:
            installed = shutil.which(str(Path(directory) / name))
            if installed is not None:
                return installed
    return None


def past_the_working_directory(name: str, found: str) -> str | None:
    """The file to run for the program *name*, which ``shutil.which`` found at *found*.

    On Windows a *found* in the working directory, which ``PATH`` does not
    list, is passed over for the first *name* on ``PATH``, run by the path
    found there: that path holds a directory, so the file in the working
    directory does not run. Elsewhere, for a *name* with a directory, or for
    a working directory that ``PATH`` lists (the user's own choice), *found*
    is the file to run.

    :param name: The name the program was looked up by, ``"ssh"`` say.
    :param found: What ``shutil.which(name)`` returned.
    :return: The path to run, or ``None`` for a program found only in the
        working directory, which the caller refuses with its own error.
    """
    if sys.platform != "win32" or Path(name).name != name:
        return found
    here = Path.cwd().resolve()
    if Path(found).parent.resolve() != here:
        return found
    listed = os.environ.get("PATH", "").split(os.pathsep)
    if any(directory and Path(directory).resolve() == here for directory in listed):
        return found
    return _first_on_path(name)
