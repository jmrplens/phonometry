#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A stand-in for ``ssh`` in the remote-compute tests: it runs the command here.

It checks the options a client must pass (no prompt, no terminal, no
forwarding, no command of a config file, no shared connection, a
keep-alive, ``--`` before the destination), then runs the remote command on this machine, split as a POSIX
shell splits it, on its own standard streams. ``FAKE_SSH_MODE`` makes it
misbehave the ways a real connection can:

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

import json
import os
import shlex
import subprocess  # nosec B404 - the stand-in runs the remote command here, as ssh runs it there
import sys
import time
from pathlib import Path

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
#: How long a node that never answers keeps quiet [s]: past any test's
#: timeout, and short enough that a stand-in left behind ends on its own.
_HANG_S = 600.0


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
    # shell. The standard streams are handed over by name: Windows passes a
    # pipe on to a child only when it is told to.
    child = subprocess.Popen(  # nosec B603 - the test's own command line
        shlex.split(" ".join(words)),
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    pidfile = os.environ.get("FAKE_SSH_PIDFILE")
    if pidfile:
        Path(pidfile).write_text(str(child.pid), encoding="utf-8")
    return child.wait()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
