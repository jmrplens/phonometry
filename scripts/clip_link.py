#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The pieces of the remote machinery the clip transport borrows (private).

``phonometry.simulation`` sends a computation to a node over SSH with its
own private machinery: the hosts file, the SSH and container command, a
loader that runs whatever program it is sent, frames made of a JSON
header and raw buffers, the header read before any buffer, and the
escaping of what a node says before it is shown. The
documentation clips travel the same road with another load, the
repository and the ten files of each clip, so the clip transport
(``scripts/clip_transport.py`` and ``scripts/clip_node.py``) uses those
pieces rather than a copy of them, and this is the one file that names
them. When that machinery renames one, this file changes and nothing else
does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, BinaryIO

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from phonometry.simulation import Compute
    from phonometry.simulation._remote.hosts import HostEntry


def host_entry(name: str) -> HostEntry:
    """The hosts-file entry *name*.

    :raises KeyError: for a name the hosts file does not have, or no hosts
        file at all.
    :raises ValueError: for a hosts file that cannot be read or does not parse.
    """
    from phonometry.simulation._remote import hosts

    return hosts.load_host(name)


def node_command(entry: HostEntry, compute: Compute) -> list[str]:
    """The ssh argv that runs the node's Python on the loader, for *compute*'s GPU.

    :raises FileNotFoundError: when no ``ssh`` is on ``PATH``.
    """
    from phonometry.simulation._remote import command

    return command.ssh_argv(entry, compute, loader=True)


def lane_placement(entry: HostEntry, compute: Compute) -> str:
    """``PHONOMETRY_COMPUTE`` for the node's lanes: the device as the node sees it, no host."""
    from phonometry.simulation._remote import command

    placement = command.node_placement(entry, compute)
    device, index = str(placement["device"]), int(str(placement["device_index"]))
    text = device + (f":{index}" if index else "")
    return text + (",fallback" if compute.fallback else "")


def loader() -> str:
    """The one line a node's Python runs to take its program from standard input."""
    from phonometry.simulation._remote import command

    return command.LOADER


def send_program(stream: BinaryIO, code: str) -> None:
    """Send *code* to the loader: its length on one line, then the program."""
    data = code.encode("utf-8")
    stream.write(b"%d\n" % len(data) + data)
    stream.flush()


def send(
    stream: BinaryIO, header: Mapping[str, object], buffers: Sequence[bytes] = ()
) -> None:
    """Write one frame, *header* with the byte count of each buffer, and flush it."""
    from phonometry.simulation._remote import bootstrap

    bootstrap.write_frame(stream, header, buffers)
    stream.flush()


def receive(
    stream: BinaryIO, sizes: Callable[[dict[str, Any]], Sequence[int]]
) -> tuple[dict[str, Any], list[bytes]]:
    """Read one frame; *sizes* checks its header and says what each buffer must weigh.

    :raises ValueError: when *sizes* refuses the header, or the frame
        announces other byte counts than *sizes* expects; no buffer is read.
    :raises EOFError: when the stream breaks: it ends, or is not a frame.
    """
    from phonometry.simulation._remote import bootstrap

    try:
        header: dict[str, Any] = bootstrap.read_header(stream)
    except bootstrap.FrameError as exc:
        raise EOFError(str(exc)) from exc
    expected = list(sizes(header))
    # The reader has checked that the frame announces a list of byte counts.
    announced: list[int] = header["buffers"]
    if announced != expected:
        msg = f"the frame announces buffers of {announced!r:.80} bytes, not {expected!r:.80}"
        raise ValueError(msg)
    try:
        return header, [bootstrap.read_exact(stream, size) for size in announced]
    except bootstrap.FrameError as exc:
        raise EOFError(str(exc)) from exc


def printable(text: str) -> str:
    """*text* from a node, every control character but newline and tab written as an escape.

    A node's words (a clip's log tail, the reasons of a refusal) reach this
    terminal through an error or a log line; a node must not write escape
    sequences there.
    """
    from phonometry.simulation._remote import client

    return client._printable(text)
