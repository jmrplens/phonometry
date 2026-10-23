#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Hold a GPU's NVENC sessions to what its card allows.

A GeForce card runs at most eight NVENC sessions at once, and a node renders
two clips at a time, each in four forked variants: eight encodes, as long as
nothing else opens one. This is the semaphore that keeps it so across
processes that share nothing but a directory. ``PHONOMETRY_ENCODE_SLOTS``
(``<directory>:<count>``), which the node sets for every render lane
(``scripts/clip_node.py``) and a render on this machine's GPU sets for its
workers, names a directory of ``count`` lock files, and a GPU encode holds
one while it runs. A lock held by a process that dies is released with it.
Unset, or for a CPU encoder, nothing is held.

This sits outside the figures package: it decides when an encode may start,
not what it writes, so it is in no clip's fingerprint.
"""

from __future__ import annotations

import contextlib
import os
import pathlib
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


@contextlib.contextmanager
def slot(encoder: str) -> Iterator[None]:
    """Hold one encode slot for *encoder* while the block runs.

    :raises ValueError: when ``PHONOMETRY_ENCODE_SLOTS`` is malformed.
    """
    text = os.environ.get(SLOTS_ENV, "").strip()
    if not text or encoder not in GPU_ENCODERS:
        yield
        return
    import fcntl

    directory, count = _parse(text)
    directory.mkdir(parents=True, exist_ok=True)
    while True:
        for index in range(count):
            handle = (directory / f"slot-{index}.lock").open("w")
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                continue
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)
                handle.close()
            return
        time.sleep(_POLL_S)
