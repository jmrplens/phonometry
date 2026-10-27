#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Hold a GPU's NVENC sessions to what its card allows.

A GeForce card runs at most eight NVENC sessions at once, and a node renders
two clips at a time, each in four forked variants: eight encodes, as long as
nothing else opens one. This is the semaphore that keeps it so across
processes that share nothing but a directory. ``PHONOMETRY_ENCODE_SLOTS``
(``<directory>:<count>``), which the node sets for every render lane
(``scripts/clip_node.py``) and a render on this machine's GPU sets for its
workers on POSIX, names a directory of ``count`` lock files, and a GPU
encode holds one while it runs. A lock held by a process that dies is
released with it. Unset, or for a CPU encoder, nothing is held.

The slots count only the encodes that share their directory: one user's
renders on this machine, or the lanes of one node job. The card's limit
counts every NVENC session open on it, whoever opened it, so an encode by
another user, another job or another program is not seen here, and one past
the limit fails when ffmpeg starts it.

The directory is private to the user whose encodes it counts: made with mode
0700 when it is missing, and refused when what is there is a link, belongs
to another user or is open to others, since anyone who can write in it can
put a link where a lock file goes. The directory is judged once it is
open, and each lock file is opened through it, so a directory swapped for a
link after its check cannot send a lock elsewhere; a lock file is opened
without following a link, where the platform can, and never truncated. The
node's lanes count in a directory of the job's own; a render on this
machine's GPU counts in :func:`shared_directory`, this user's in the
temporary directory.

This sits outside the figures package: it decides when an encode may start,
not what it writes, so it is in no clip's fingerprint.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
import stat
import tempfile
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

#: ``<directory>:<count>``: where the slots are and how many.
SLOTS_ENV = "PHONOMETRY_ENCODE_SLOTS"

#: The ffmpeg encoders that take a slot.
GPU_ENCODERS = frozenset({"av1_nvenc"})

#: NVENC sessions a GeForce card runs at once.
NVENC_SESSIONS = 8

#: How long a waiting encode sleeps between two looks at the slots [s].
_POLL_S = 0.2

#: Opens a lock file without following a link, where the platform has it.
_NO_FOLLOW = getattr(os, "O_NOFOLLOW", 0)

#: Opens the slots' directory itself: a directory, never through a link,
#: where the platform has the flags.
_DIRECTORY = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _NO_FOLLOW

#: How a slots' directory that is not one is refused.
_NOT_A_DIRECTORY = "is a link or not a directory"


def shared_directory() -> pathlib.Path:
    """Where this user's encodes on this machine hold their slots; POSIX only.

    In the temporary directory, which every user shares, under a name of
    this user's own (its effective user id, which only POSIX has), so no
    other user's run counts in it or prepares it.
    """
    return (
        pathlib.Path(tempfile.gettempdir()) / f"phonometry-encode-slots-{os.geteuid()}"
    )


def _parse(text: str) -> tuple[pathlib.Path, int]:
    """The directory and the number of slots *text* names.

    :raises ValueError: when *text* does not read ``<directory>:<count>``
        with a directory and a positive whole count.
    """
    directory, _, count = text.rpartition(":")
    try:
        slots = int(count)
    except ValueError:
        slots = 0
    if not directory or slots <= 0:
        msg = f"{SLOTS_ENV} must read <directory>:<count>; got {text!r}"
        raise ValueError(msg)
    return pathlib.Path(directory), slots


def _private(directory: pathlib.Path) -> int:
    """A descriptor of *directory*, made this user's own (mode 0700) when missing, or a refusal.

    The directory is judged once it is open (:func:`os.fstat`), and every
    lock file is opened in it through that descriptor
    (:func:`_open_lock`), so a directory swapped for a link once checked
    cannot send a lock anywhere else. The caller closes the descriptor.

    :raises PermissionError: when it is a link or not a directory, belongs
        to another user, or is open to others.
    :raises OSError: when it cannot be made or opened.
    """
    # Whatever is already there is judged below, a file or a link included,
    # rather than by the mkdir that meets it.
    with contextlib.suppress(FileExistsError):
        directory.mkdir(mode=0o700, parents=True)
    held = _open_directory(directory)
    problem = _not_private(os.fstat(held))
    if problem is None:
        return held
    os.close(held)
    msg = f"the encode slots' directory {directory} {problem}"
    raise PermissionError(msg)


def _open_directory(directory: pathlib.Path) -> int:
    """A descriptor of *directory* itself, never of what a link in its place leads to.

    :raises PermissionError: when it is a link or not a directory.
    :raises OSError: when it cannot be opened.
    """
    try:
        held = os.open(directory, _DIRECTORY)
    except OSError:
        if directory.is_symlink() or not directory.is_dir():
            msg = f"the encode slots' directory {directory} {_NOT_A_DIRECTORY}"
            raise PermissionError(msg) from None
        raise
    if directory.is_symlink():
        # Where the platform has no O_NOFOLLOW, the open went through it.
        os.close(held)
        msg = f"the encode slots' directory {directory} {_NOT_A_DIRECTORY}"
        raise PermissionError(msg)
    return held


def _not_private(held: os.stat_result) -> str | None:
    """What keeps the open directory *held* from being this user's alone; None when it is."""
    mode = stat.S_IMODE(held.st_mode)
    if not stat.S_ISDIR(held.st_mode):
        return _NOT_A_DIRECTORY
    if held.st_uid != os.geteuid():
        return f"belongs to user {held.st_uid}, not to this one ({os.geteuid()})"
    if mode & 0o077:
        return f"is open to others (mode {mode:o}); it must be its owner's alone (700)"
    return None


def _open_lock(directory: int, path: pathlib.Path) -> int:
    """A descriptor of the lock file *path* in the open directory *directory*: made if missing, never truncated.

    The file is opened by its name in that directory, through its
    descriptor. A link where the file goes is never followed, where the
    platform can refuse to follow one (``O_NOFOLLOW``), and is refused.

    :raises PermissionError: when the lock file is a link, where the
        platform has ``O_NOFOLLOW``.
    :raises OSError: when it cannot be opened.
    """
    try:
        return os.open(
            path.name, os.O_RDWR | os.O_CREAT | _NO_FOLLOW, 0o600, dir_fd=directory
        )
    except OSError as exc:
        if not _is_link(directory, path.name):
            raise
        msg = f"{path} is a link; an encode slot never follows one"
        raise PermissionError(msg) from exc


def _is_link(directory: int, name: str) -> bool:
    """Whether *name* in the open directory *directory* is a link; False when it cannot be read."""
    try:
        held = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except OSError:
        return False
    return stat.S_ISLNK(held.st_mode)


def _take(directory: int, path: pathlib.Path, count: int) -> int:
    """The descriptor of a slot taken among *count* in the open directory *directory*, waiting for one.

    :raises PermissionError: when a lock file is a link.
    :raises OSError: when a lock file cannot be opened or locked.
    """
    import fcntl

    while True:
        for index in range(count):
            lock = _open_lock(directory, path / f"slot-{index}.lock")
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(lock)
                continue
            except OSError:
                os.close(lock)
                raise
            return lock
        time.sleep(_POLL_S)


@contextlib.contextmanager
def slot(encoder: str) -> Iterator[None]:
    """Hold one encode slot for *encoder* while the block runs.

    :raises ValueError: when ``PHONOMETRY_ENCODE_SLOTS`` is malformed.
    :raises PermissionError: when the slots' directory is a link or not a
        directory, belongs to another user or is open to others, or a lock
        file is a link (where the platform has ``O_NOFOLLOW``).
    :raises OSError: when the directory cannot be made or opened, or a lock
        file cannot be opened or locked.
    :raises ImportError: where there is no :mod:`fcntl` (off POSIX), for a
        GPU encode with the slots set.
    """
    text = os.environ.get(SLOTS_ENV, "").strip()
    if not text or encoder not in GPU_ENCODERS:
        yield
        return
    import fcntl

    path, count = _parse(text)
    directory = _private(path)
    try:
        lock = _take(directory, path, count)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            os.close(lock)
    finally:
        os.close(directory)
