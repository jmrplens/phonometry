#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How the client reaches a node: the ssh command line and the job's placement (private).

One ``ssh`` process carries a remote run: never a prompt (a prompt would
hang a notebook), no terminal, no forwarding of anything of the client's and
no connection shared with another, a dead link noticed in about a minute,
the options ended by ``--`` before the destination. The remote command is a
shell string for the node's POSIX login shell, so every word of it that
comes from the hosts file is quoted.
"""

from __future__ import annotations

import logging
import shlex
import shutil
from typing import TYPE_CHECKING

from ..._internal.programs import past_the_working_directory
from . import bootstrap

if TYPE_CHECKING:
    from ..compute import Compute
    from .hosts import HostEntry

_LOG = logging.getLogger("phonometry.simulation")

#: The options every connection takes. Options on the command line win over
#: ``~/.ssh/config``, so whatever the file says for the host, a run gets no
#: terminal (RequestTTY), no RemoteCommand, no agent, X11 or port forwarding
#: (ForwardAgent, ForwardX11, LocalForward, RemoteForward, DynamicForward),
#: no Kerberos credentials delegated (GSSAPIDelegateCredentials), no
#: LocalCommand (PermitLocalCommand), no connection shared with another
#: (ControlPath), never a prompt (BatchMode), and the keep-alives and the
#: connection timeout below. Every client from OpenSSH 7.6 on knows them;
#: one built without GSSAPI, which delegates nothing, writes that it does
#: not support that option and goes on. SessionType, StdinNull and
#: ForkAfterAuthentication are left out on purpose: a client older than
#: OpenSSH 8.7 refuses them on the command line and would run nothing. A
#: host alias used as a node leaves them at their defaults: a SessionType of
#: none hangs a run until its timeout, a StdinNull of yes makes it fail at
#: once (the node reads an empty input), and a ForkAfterAuthentication of
#: yes detaches the session out of the client's reach.
SSH_OPTIONS: tuple[str, ...] = (
    # No terminal (-T and RequestTTY): a pty turns every LF of a frame into
    # CRLF and reads the package's bytes as keys (0x03 interrupts, 0x04 ends
    # the input).
    "-T",
    # No agent and no X11 forwarding: the node runs code the client sends,
    # and gets nothing of the client's.
    "-a",
    "-x",
    *(
        word
        for setting in (
            "RequestTTY=no",
            # The session runs the command it is given: a RemoteCommand of the
            # file makes ssh refuse to run beside it.
            "RemoteCommand=none",
            # No port forwarding, and no LocalCommand, whose output on this
            # machine would land among the frames.
            "ClearAllForwardings=yes",
            "PermitLocalCommand=no",
            # No Kerberos credentials of the client's handed to the node, which
            # a Kerberos site's config often asks for.
            "GSSAPIDelegateCredentials=no",
            # No connection sharing: every run is a connection of its own,
            # whatever ControlMaster the file sets. A run would otherwise
            # leave a master behind on this machine (ControlPersist), or ride
            # another's master, whose keep-alives and timeout are that
            # connection's and not the ones below: a dead node would go
            # unnoticed past the minute they promise.
            "ControlPath=none",
            # Never a prompt, which would hang a notebook; keep-alives that
            # notice a dead link in about a minute; a connection given up
            # after 30 s.
            "BatchMode=yes",
            "ServerAliveInterval=15",
            "ServerAliveCountMax=4",
            "ConnectTimeout=30",
        )
        for word in ("-o", setting)
    ),
)
#: The one line a Python node runs: it reads the bootstrap from its standard
#: input, its length on the first line, and runs it as a script; what follows
#: on the input is the conversation.
LOADER = (
    "import sys;n=int(sys.stdin.buffer.readline());"
    'exec(compile(sys.stdin.buffer.read(n),"phonometry-bootstrap","exec"),{"__name__":"__main__"})'
)
#: The devices whose Docker container needs a GPU.
_GPU_DEVICES = ("cupy", "torch:cuda")
#: The environment a Docker node's container runs with: the cache, CuPy's
#: compiled kernels kept beside it, and a home and a matplotlib directory
#: any user can write.
_DOCKER_ENVIRONMENT = (
    f"{bootstrap.CACHE_VAR}=/cache",
    "CUPY_CACHE_DIR=/cache/cupy-kernels",
    "HOME=/tmp",
    "MPLCONFIGDIR=/tmp/matplotlib",
)
#: What stands for ``ssh``: ``None`` looks it up on ``PATH``. The tests set
#: it to a stand-in, which on Windows cannot be a batch file on ``PATH``:
#: cmd.exe rewrites the quotes and metacharacters of the remote command.
_SSH_PROGRAM: tuple[str, ...] | None = None


def ssh_program() -> tuple[str, ...]:
    """The program, and its leading arguments, that runs ``ssh``, by the path it was found at.

    On Windows, which looks a bare name up in the working directory before
    ``PATH``, an ``ssh`` there is passed over for the one on ``PATH``, and
    the log says so at INFO on ``phonometry.simulation``; one found nowhere
    else is refused. A working directory that ``PATH`` itself lists is the
    user's own choice, and its ``ssh`` runs.

    :raises FileNotFoundError: when no ``ssh`` is on ``PATH``, or on Windows
        when it was found only in the working directory.
    """
    if _SSH_PROGRAM is not None:
        return _SSH_PROGRAM
    found = shutil.which("ssh")
    if found is None:
        msg = "no ssh client on PATH; install OpenSSH to run on a node"
        raise FileNotFoundError(msg)
    installed = past_the_working_directory("ssh", found)
    if installed is None:
        msg = (
            f"ssh was found only in the working directory ({found}), which Windows "
            "searches before PATH; phonometry does not run a program from there. "
            "Put an OpenSSH client on PATH to run on a node"
        )
        raise FileNotFoundError(msg)
    if installed != found:
        _LOG.info(
            "running %s from PATH, not %s from the working directory, which "
            "Windows searches first",
            installed,
            found,
        )
    return (installed,)


def ssh_argv(entry: HostEntry, request: Compute) -> list[str]:
    """The ssh command that runs a job on *entry* for *request*."""
    return [
        *ssh_program(),
        *SSH_OPTIONS,
        "--",
        entry.ssh,
        remote_command(entry, request),
    ]


def remote_command(entry: HostEntry, request: Compute) -> str:
    """What the node's shell runs: the image's bootstrap, or the interpreter on the loader."""
    if entry.runner == "python":
        return shlex.join([entry.target, "-I", "-c", LOADER])
    docker = [
        "docker",
        "run",
        "--rm",
        "-i",
        "--init",
        "--pull=never",
        "--network",
        "none",
        # No log: Docker copies a container's standard output into its log
        # even while a client is attached, and the result stream is the
        # standard output. The attached client still gets every byte.
        "--log-driver",
        "none",
    ]
    if request.device in _GPU_DEVICES:
        docker += ["--gpus", f"device={request.device_index}"]
    for setting in _DOCKER_ENVIRONMENT:
        docker += ["-e", setting]
    # The bootstrap is the container's entrypoint, whatever image the hosts
    # file names: an image's own ENTRYPOINT runs before the command and may
    # write to standard output, which carries the frames (the CUDA images'
    # prints a banner there). The GPU reaches the container through the
    # runtime's hook, not through that entrypoint.
    docker += ["--entrypoint", "python"]
    image = shlex.join([entry.target, "-I", bootstrap.IMAGE_PATH])
    # The user and the cache are the node's: the shell there expands them. The
    # cache is where the bootstrap looks for it: XDG's, which ignores a
    # relative XDG_CACHE_HOME, else ~/.cache.
    script = (
        'case "$XDG_CACHE_HOME" in /*) base="$XDG_CACHE_HOME" ;; '
        '*) base="$HOME/.cache" ;; esac && '
        'cache="$base/phonometry/remote" && '
        'mkdir -p "$cache" && '
        f'exec {shlex.join(docker)} --user "$(id -u):$(id -g)" -v "$cache:/cache" {image}'
    )
    return shlex.join(["sh", "-c", script])


def node_placement(entry: HostEntry, request: Compute) -> dict[str, object]:
    """The placement the node runs: a Docker node sees its one GPU as index 0."""
    index = (
        0
        if entry.runner == "docker" and request.device in _GPU_DEVICES
        else request.device_index
    )
    return {"device": request.device, "device_index": index, "dtype": request.dtype}
