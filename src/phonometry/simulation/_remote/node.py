#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a node does with a job: run a library function and send back its arrays (private).

The bootstrap hands the stream here once the package it was sent imports
from the cache. The job names one of :data:`FUNCTIONS` and carries its
arguments as data (:mod:`.wire`). The node runs it on the device the client
asked for, without a fallback (the client decides what a failure means),
records the warnings it raises, and sends back the arrays the client cannot
rebuild, then the stream the job returned if any (a video), the run's
provenance and those warnings. Progress lines go to standard error, at most
one a second.

A job the node cannot read (a function it does not run, a placement other
than a device, an index and a dtype, arguments that do not rebuild) is
refused before anything runs; the bootstrap sends the refusal as an error
frame of the ``job`` stage.

After the job a thread reads standard input until it ends. A client that
closes its connection (an interrupt, a timeout, a closed notebook) ends it,
and the run stops at its next step; a run that has not stopped
:data:`_GRACE_S` seconds later ends the process. A client that vanishes
without closing it (a machine put to sleep, a network that drops) ends it
only when the node's ssh server notices, which its ``ClientAliveInterval``
decides; the guide on remote nodes says how to set it.
"""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import os
import shutil
import sys
import threading
import time
import traceback
import warnings
from types import MappingProxyType
from typing import IO, TYPE_CHECKING, Any

import numpy as np

from .. import _observer
from ..compute import _ENV_VAR, Compute
from ..elastic_fdtd import elastic_fdtd_simulation
from ..fdtd import fdtd_simulation
from . import bootstrap, wire

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from numpy.typing import NDArray

#: A stream a job sends after the arrays: its name and a seekable binary
#: file, read from where it stands.
NodeStream = tuple[str, IO[bytes]]


def _fdtd(**arguments: Any) -> tuple[Any, NodeStream | None]:
    """Run :func:`fdtd_simulation` on the job's run; it sends its arrays and no stream."""
    return fdtd_simulation(**arguments), None


def _elastic(**arguments: Any) -> tuple[Any, NodeStream | None]:
    """Run :func:`elastic_fdtd_simulation` on the job's run; it sends its arrays and no stream."""
    return elastic_fdtd_simulation(**arguments), None


#: The jobs a client may name. Each runs a library function and returns its
#: record with the stream it sends after the arrays, or ``None``; beside it,
#: the array fields of the record that travel, in the order they travel.
FUNCTIONS: Mapping[
    str, tuple[Callable[..., tuple[Any, NodeStream | None]], tuple[str, ...]]
] = MappingProxyType(
    {
        "fdtd_simulation": (_fdtd, ("pressures", "snapshots")),
        "elastic_fdtd_simulation": (_elastic, ("signals", "snapshots")),
    }
)
#: The fields of a job's placement: no host (a run here stays here) and no
#: fallback (the client decides what a failure means).
_PLACEMENT = frozenset({"device", "device_index", "dtype"})
#: The chunk a stream is copied in [bytes], as the client reads it.
_STREAM_CHUNK = bootstrap._CHUNK
#: How long a run may go on once its client is gone [s].
_GRACE_S = 30.0
#: The least time between two progress lines [s].
_PROGRESS_EVERY_S = 1.0
#: The most warnings a job sends back, as many as the client takes.
_MAX_WARNINGS = bootstrap._MAX_WARNINGS


class _Watcher:
    """Stops the run once the client is gone, and writes a progress line now and then."""

    def __init__(self, cancelled: threading.Event) -> None:
        self._cancelled = cancelled
        self._last: float | None = None

    def __call__(self, done: int, total: int) -> None:
        """Called after each step.

        :raises RunCancelled: once the client is gone.
        """
        if self._cancelled.is_set():
            raise _observer.RunCancelled
        now = time.monotonic()
        if done == total or self._last is None or now - self._last >= _PROGRESS_EVERY_S:
            self._last = now
            sys.stderr.write(f"{bootstrap.PROGRESS} {done} {total}\n")
            sys.stderr.flush()


def _watch_input(
    stream: IO[bytes], cancelled: threading.Event, finished: threading.Event
) -> None:
    """Set *cancelled* when the input ends; end the process if the run then does not stop.

    :raises OSError: when the input cannot be copied for the thread that
        reads it, as with no descriptor left (``EMFILE``).
    """
    # The thread reads a descriptor of its own, duplicated here before it
    # starts, and closes it when the input ends. The stream stays the
    # caller's, who may close it as soon as serve returns: a number taken
    # from it inside the thread could by then name the next file opened, and
    # the thread would read that file's bytes. On Windows the copy also has
    # a lock of its own, so closing the stream never waits for this read. An
    # input that is no file, or one already closed, is an ended one; a copy
    # that cannot be made is an error, not a client gone.
    try:
        number: int | None = stream.fileno()
    except (OSError, ValueError):
        number = None
    descriptor = None if number is None else os.dup(number)

    def watch() -> None:
        try:
            if descriptor is not None:
                _read_to_end(descriptor)
        finally:
            cancelled.set()
        if not finished.wait(_GRACE_S):
            sys.stderr.write(
                "phonometry: the client is gone and the run did not stop; the node exits\n"
            )
            sys.stderr.flush()
            os._exit(130)

    threading.Thread(target=watch, name="phonometry-node-input", daemon=True).start()


def _read_to_end(descriptor: int) -> None:
    """Read *descriptor* until it ends, then close it; a read that fails ends it too.

    Anything the client sends after the job is ignored: only its end
    matters. The descriptor is read, not a buffered file: a thread blocked
    in a file's read holds its lock, and the interpreter aborts at exit
    when it cannot take that lock. A read refused for a descriptor that is
    no longer open (``EBADF``) leaves the number alone: closed by another
    hand, it may already name a file of someone else's.
    """
    try:
        chunk = os.read(descriptor, 1 << 16)
        while chunk:
            chunk = os.read(descriptor, 1 << 16)
    except OSError as exc:
        if exc.errno == errno.EBADF:
            return
    with contextlib.suppress(OSError):
        os.close(descriptor)


def _forget_host() -> None:
    """Take ``PHONOMETRY_COMPUTE`` out of this node's environment: a run here stays here.

    The job names its placement, which the run is given explicitly, so the
    variable decides nothing on the node; a host left in it would send a
    run on to the node it names.
    """
    os.environ.pop(_ENV_VAR, None)


def _little_endian(array: NDArray[Any]) -> memoryview:
    little = np.ascontiguousarray(array, dtype=array.dtype.newbyteorder("<"))
    # Flattened before the byte view, as the arguments are (:mod:`.wire`).
    return memoryview(little.reshape(-1).view(np.uint8))


def _caught(records: Sequence[warnings.WarningMessage]) -> list[dict[str, str]]:
    """The warnings a run raised, once each, as class path and message.

    Each message is cut to the length an error frame carries, before two are
    compared: as many long messages as a result takes still fit its header.
    """
    seen: list[dict[str, str]] = []
    for record in records:
        item = {
            "category": f"{record.category.__module__}:{record.category.__qualname__}",
            "message": str(record.message)[: bootstrap._MAX_MESSAGE],
        }
        if item not in seen:
            seen.append(item)
    return seen[:_MAX_WARNINGS]


def _stream_length(file: IO[bytes]) -> int:
    """The bytes left in *file*, which is read from where it stands."""
    start = file.tell()
    end = file.seek(0, os.SEEK_END)
    file.seek(start)
    return end - start


def _send_result(
    frames: IO[bytes],
    # The record of any job of FUNCTIONS, which share no type: read by the
    # field names the table gives, never through a type of its own.
    result: Any,  # noqa: ANN401
    outputs: tuple[str, ...],
    stream: NodeStream | None,
    caught: list[dict[str, str]],
) -> None:
    """Send the record's arrays that are not ``None``, then the stream, in one frame."""
    present = [
        (name, array)
        for name in outputs
        if (array := getattr(result, name)) is not None
    ]
    described: list[dict[str, object]] = [
        {"name": name, "dtype": array.dtype.name, "shape": list(array.shape)}
        for name, array in present
    ]
    views = [_little_endian(array) for _, array in present]
    sizes = [view.nbytes for view in views]
    if stream is not None:
        length = _stream_length(stream[1])
        described.append({"name": stream[0], "dtype": "uint8", "shape": [length]})
        sizes.append(length)
    header = {
        "type": "result",
        "provenance": dataclasses.asdict(result.provenance),
        "warnings": caught,
        "arrays": described,
        "buffers": sizes,
    }
    bootstrap.write_header(frames, header)
    frames.writelines(views)
    if stream is not None:
        shutil.copyfileobj(stream[1], frames, _STREAM_CHUNK)
    frames.flush()


def _placement(header: Mapping[str, object]) -> Compute:
    """The device, index and dtype the job asks for, and nothing else.

    :raises Refused: for a placement with other fields, or one
        :class:`Compute` refuses.
    """
    fields = bootstrap.field(header, "compute", dict)
    if set(fields) != _PLACEMENT:
        msg = (
            f"a job's placement holds {sorted(_PLACEMENT)}, not {sorted(fields)!r:.200}"
        )
        raise bootstrap.Refused(msg, stage="job")
    try:
        return Compute(**fields)
    except (TypeError, ValueError) as exc:
        msg = f"the job's placement is refused: {type(exc).__name__}: {exc}"
        raise bootstrap.Refused(msg, stage="job") from None


def _arguments(header: Mapping[str, object], stream: IO[bytes]) -> dict[str, object]:
    """The job's arguments, rebuilt from the data and the buffers it sent.

    :raises Refused: for arguments that do not rebuild, whatever the reason
        (a form the client would not write, a buffer it did not send, a
        record its constructor refuses, a tree nested too deep), named with
        the error that stopped them.
    :raises FrameError: for buffers the stream does not hold.
    """
    counts = bootstrap.field(header, "buffers", list)
    buffers = [bytearray(bootstrap.read_exact(stream, n)) for n in counts]
    tree = bootstrap.field(header, "arguments", dict)
    try:
        return wire.decode_arguments(tree, buffers)
    # Anything a client sends is data; whatever stops it from rebuilding is
    # a refusal the client hears, not a failure of the node.
    except Exception as exc:
        msg = f"the job's arguments do not rebuild: {type(exc).__name__}: {exc}"
        raise bootstrap.Refused(msg, stage="job") from None


def _read_job(stream: IO[bytes]) -> tuple[str, dict[str, object], Compute]:
    """The function a job names, its arguments and its placement.

    :raises Refused: for a frame that is no job, a function the node does
        not run, or a placement or arguments it cannot rebuild.
    :raises FrameError: for a job frame that breaks the framing.
    """
    header = bootstrap.read_header(stream)
    kind = bootstrap.field(header, "type", str)
    if kind != "job":
        msg = f"expected a job, not a {kind!r:.80} frame"
        raise bootstrap.Refused(msg, stage="job")
    name = bootstrap.field(header, "function", str)
    if name not in FUNCTIONS:
        msg = f"the node runs {sorted(FUNCTIONS)}, not {name!r:.80}"
        raise bootstrap.Refused(msg, stage="job")
    placement = _placement(header)
    return name, _arguments(header, stream), placement


def serve(stream: IO[bytes], frames: IO[bytes]) -> int:
    """Run the one job on *stream* and answer on *frames*.

    :return: ``0`` once the result is sent, ``1`` when the run raised (the
        client has the error frame), ``3`` when the client went away.
    :raises Refused: for a job that names a function the node does not run,
        or whose placement or arguments do not rebuild.
    :raises FrameError: for a job frame that breaks the framing.
    :raises OSError: when the input cannot be copied for the thread that
        watches it, as with no descriptor left; the bootstrap sends it as an
        error frame.
    """
    _forget_host()
    name, arguments, placement = _read_job(stream)
    function, outputs = FUNCTIONS[name]
    cancelled, finished = threading.Event(), threading.Event()
    _watch_input(stream, cancelled, finished)
    try:
        with (
            warnings.catch_warnings(record=True) as records,
            _observer.observing(_Watcher(cancelled)),
        ):
            result, sent_after = function(**arguments, compute=placement)
    except _observer.RunCancelled:
        return 3
    except Exception as exc:
        bootstrap.send_error(
            frames, "job", f"{type(exc).__name__}: {exc}", traceback.format_exc()
        )
        return 1
    finally:
        finished.set()
    try:
        _send_result(frames, result, outputs, sent_after, _caught(records))
    finally:
        if sent_after is not None:
            sent_after[1].close()
    return 0
