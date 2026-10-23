#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A stand-in for ``ssh`` in the remote-compute tests: it runs the command here.

It checks the options a client must pass (no prompt, no terminal, no
forwarding, no command of a config file, no shared connection, a
keep-alive, ``--`` before the destination), then runs the remote command on
this machine, split as a POSIX shell splits it, and relays its three
standard streams as ssh does: the client's pipes end at this process, so
killing it, as the client does at its timeout, closes them, and the
command's input ends with them, as when a connection goes down. Handing the
pipes to the command instead would keep them open as long as it runs.
``FAKE_SSH_MODE`` makes it misbehave the ways a real connection can:

* ``refuse``: exit 255 with ssh's words for a refused key;
* ``banner``: print a login banner on standard output first;
* ``hang``: never answer;
* ``garbage``: answer with bytes that are no frame.

``FAKE_SSH_LOG`` names a file that gets a line per start; ``FAKE_SSH_PIDFILE``
one that gets the process id of the command run.

It is started as ``python fake_ssh.py`` through the client's hook for the
ssh program, so it runs alike on Linux, macOS and Windows.
"""

from __future__ import annotations

import contextlib
import json
import os
import shlex
import subprocess  # nosec B404 - the stand-in runs the remote command here, as ssh runs it there
import sys
import threading
import time
from pathlib import Path
from typing import IO

#: Options a client must pass before ``--``: what a real connection relies on.
_REQUIRED = (
    "-T",
    "-a",
    "-x",
    "RequestTTY=no",
    "RemoteCommand=none",
    "ClearAllForwardings=yes",
    "PermitLocalCommand=no",
    "GSSAPIDelegateCredentials=no",
    "ControlPath=none",
    "BatchMode=yes",
    "ServerAliveInterval=15",
    "ServerAliveCountMax=4",
    "ConnectTimeout=30",
)
#: How long a node that never answers keeps quiet, and how long the command
#: run may take before it is killed [s]: past any test's timeout, and short
#: enough that a stand-in left behind ends on its own.
_HANG_S = 600.0
#: How long the command's output may take to reach its end once the command
#: has exited [s]: the rest of a pipe's worth of bytes.
_DRAIN_S = 30.0
#: The most bytes a relay copies at a time.
_CHUNK = 1 << 16


def _copy(source: int, sink: int) -> None:
    """Copy the descriptor *source* to the descriptor *sink* until either ends.

    Descriptors, not buffered files: a relay may still be blocked in a read
    when the process ends, and holds no file's lock there.
    """
    with contextlib.suppress(OSError):
        while chunk := os.read(source, _CHUNK):
            view = memoryview(chunk)
            while view:
                view = view[os.write(sink, view) :]


def _feed(source: int, sink: IO[bytes]) -> None:
    """Copy *source* into the command's input *sink*, and close it once *source* ends."""
    _copy(source, sink.fileno())
    with contextlib.suppress(OSError):
        sink.close()


def main(argv: list[str]) -> int:
    log = os.environ.get("FAKE_SSH_LOG")
    if log:
        with Path(log).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(argv) + "\n")
    if "--" not in argv or not set(_REQUIRED) <= set(argv[: argv.index("--")]):
        sys.stderr.write(f"fake ssh: these are not the client's options: {argv}\n")
        return 2
    destination, *words = argv[argv.index("--") + 1 :]
    mode = os.environ.get("FAKE_SSH_MODE", "run")
    if mode == "refuse":
        sys.stderr.write(f"{destination}: Permission denied (publickey).\n")
        return 255
    if mode == "hang":
        time.sleep(_HANG_S)
        return 0
    if mode == "garbage":
        sys.stdout.buffer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
        sys.stdout.flush()
        return 0
    if mode == "banner":
        sys.stdout.buffer.write(b"Welcome to the node\n")
        sys.stdout.flush()
    # ssh joins the words of the remote command with spaces for the node's
    # shell.
    child = subprocess.Popen(  # nosec B603 - the test's own command line
        shlex.split(" ".join(words)),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert child.stdin is not None
    assert child.stdout is not None
    assert child.stderr is not None
    pidfile = os.environ.get("FAKE_SSH_PIDFILE")
    if pidfile:
        Path(pidfile).write_text(str(child.pid), encoding="utf-8")
    # The input's relay may never end: the client keeps its pipe open while
    # it reads the answer. ssh ends with the command, and so does this.
    threading.Thread(
        target=_feed, args=(sys.stdin.fileno(), child.stdin), daemon=True
    ).start()
    outputs = [
        threading.Thread(target=_copy, args=(pipe.fileno(), sink), daemon=True)
        for pipe, sink in ((child.stdout, 1), (child.stderr, 2))
    ]
    for relay in outputs:
        relay.start()
    try:
        code = child.wait(_HANG_S)
    except subprocess.TimeoutExpired:
        child.kill()
        code = child.wait(_DRAIN_S)
    for relay in outputs:
        relay.join(_DRAIN_S)
    return code


if __name__ == "__main__":
    status = main(sys.argv[1:])
    sys.stdout.flush()
    sys.stderr.flush()
    # The relay of the input may still be blocked in its read, holding the
    # descriptor's lock on Windows: the process ends without the
    # interpreter's shutdown, which would close files under it, as ssh ends.
    os._exit(status)
