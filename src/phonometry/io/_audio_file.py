#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The audio file a caller names, read only when it is a regular file (private).

Every reader of audio here opens the file a caller names, and a name can hold
something other than a file: a named pipe no one writes to keeps an open
waiting for a writer that may never come, a device such as ``/dev/zero``
keeps a read going without end, and a directory holds no samples at all.
Each is refused with a :class:`ValueError` that names it, before the reader
opens it. The readers of this package open the file through
:func:`open_audio`, which looks at the name, opens it without waiting and asks
the open file again what it is; where python-soundfile or SciPy opens the name
itself, :func:`require_regular_audio` looks first.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from .._internal.json_input import (
    NotRegularError,
    escaped,
    not_regular_at,
    open_regular,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO


def _refusal(path: str | Path, kind: str) -> ValueError:
    """The refusal of *path*, which holds *kind* rather than a regular file."""
    return ValueError(
        f"{escaped(str(path))}: is {kind}, and audio is read only from a regular file"
    )


def require_regular_audio(path: str | Path) -> None:
    """Refuse *path* unless it names a regular file, or nothing.

    A link is followed, so a link to a recording is read and a link to a pipe
    is refused. A name with nothing at it passes, for the reader's own open to
    raise :class:`FileNotFoundError` as it always has.

    :raises ValueError: for a named pipe, a device, a socket or a directory
        at *path*, naming what it is.
    :raises OSError: as the file system raises it, untouched.
    """
    kind = not_regular_at(Path(path))
    if kind is not None:
        raise _refusal(path, kind)


@contextlib.contextmanager
def open_audio(path: str | Path) -> Iterator[BinaryIO]:
    """The regular file *path*, open for reading in binary, closed on leaving.

    Opened through :func:`~phonometry._internal.json_input.open_regular`: what
    is not a regular file is refused before it is opened, and a pipe put in
    the place of the file between the look and the open is refused rather
    than waited on.

    :raises ValueError: for a named pipe, a device, a socket or a directory
        at *path*, naming what it is.
    :raises OSError: as the file system raises it, untouched:
        :class:`FileNotFoundError` for a name with nothing at it.
    """
    try:
        handle = open_regular(Path(path))
    except NotRegularError as exc:
        raise _refusal(path, exc.kind) from None
    with handle:
        yield handle
