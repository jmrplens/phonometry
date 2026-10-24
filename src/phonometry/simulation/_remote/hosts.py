#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The nodes a remote run can go to, named once in a hosts file (private).

.. code-block:: toml

    [hosts.nas]
    ssh = "root@192.168.0.40"      # what ssh takes: user@address or an alias of ~/.ssh/config
    runner = "docker"              # or "python"
    image = "phonometry-node:gpu"  # for runner = "docker"
    # python = "/opt/venv/bin/python"  for runner = "python"
    label = "RTX 4060 on the NAS"  # how messages name it (default: the name)
    timeout_s = 7200               # the longest a run there may take (default: no limit)

The file is ``$PHONOMETRY_HOSTS_FILE`` when that is set; otherwise
``%APPDATA%\phonometry\hosts.toml`` on Windows and
``$XDG_CONFIG_HOME/phonometry/hosts.toml`` elsewhere, macOS included, with
``~/.config`` when the variable is unset or relative. It is read each time a
run names a host, never at import.
"""

from __future__ import annotations

import math
import os
import re
import sys
import threading
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

#: The environment variable that points at another hosts file.
HOSTS_FILE_VAR = "PHONOMETRY_HOSTS_FILE"

#: How a node runs a job.
Runner = Literal["docker", "python"]
_RUNNERS: tuple[Runner, ...] = ("docker", "python")
#: The keys an entry may have.
_KEYS = frozenset({"ssh", "runner", "image", "python", "label", "timeout_s"})
#: A Docker image reference: no whitespace, no quote, nothing a shell reads.
_IMAGE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/:@-]*")
#: C0 and C1 control characters, which no ssh destination holds.
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


@dataclass(frozen=True)
class HostEntry:
    """One node of the hosts file, checked.

    :ivar name: Its name in the file, the ``host`` a request gives.
    :ivar ssh: The destination ``ssh`` takes.
    :ivar runner: How the node runs a job: ``"docker"`` or ``"python"``.
    :ivar target: The image for ``"docker"``, the interpreter for ``"python"``.
    :ivar label: How messages and the log name the node.
    :ivar timeout_s: The longest a run there may take [s], or ``None``.
    """

    name: str
    ssh: str
    runner: Runner
    target: str
    label: str
    timeout_s: float | None


def hosts_file() -> Path:
    """Where the hosts file is, by the variable, the platform and XDG."""
    explicit = os.environ.get(HOSTS_FILE_VAR, "").strip()
    if explicit:
        return Path(explicit).expanduser()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "").strip()
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
        # The XDG specification ignores a relative path.
        base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".config"
    return base / "phonometry" / "hosts.toml"


def load_host(name: str) -> HostEntry:
    """The entry *name* of the hosts file, checked.

    :raises KeyError: when the file does not exist or names no such host.
    :raises ValueError: naming the file, when it cannot be read (a
        directory, a file this user may not read), is not TOML, its
        ``hosts`` is not a table, or the entry is malformed.
    """
    path = hosts_file()
    try:
        raw = path.read_bytes()
    # A path under a file names no file there: Windows reports it as missing,
    # POSIX as a component that is not a directory, and both mean no file.
    except (FileNotFoundError, NotADirectoryError):
        msg = f"no host {name!r}: the hosts file {path} does not exist"
        raise KeyError(msg) from None
    except OSError as exc:
        msg = f"{path}: the hosts file cannot be read: {exc.strerror or exc}"
        raise ValueError(msg) from None
    try:
        # utf-8-sig: Windows Notepad saves UTF-8 with a byte-order mark.
        document = tomllib.loads(raw.decode("utf-8-sig"))
    # ValueError holds UnicodeDecodeError, TOMLDecodeError and Python's refusal
    # of an integer longer than 4300 digits; RecursionError a value nested
    # deeper than the interpreter's limit.
    except (ValueError, RecursionError) as exc:
        msg = f"{path}: not a TOML file: {exc}"
        raise ValueError(msg) from None
    table = document.get("hosts", {})
    if not isinstance(table, dict):
        msg = f"{path}: 'hosts' must be a table of [hosts.<name>] entries"
        raise ValueError(msg)
    if name not in table:
        named = ", ".join(sorted(table)) or "none"
        msg = f"no host {name!r} in {path}; it names {named}"
        raise KeyError(msg)
    return _entry(f"{path}: [hosts.{name}]", name, table[name])


def _entry(where: str, name: str, table: object) -> HostEntry:
    """The checked entry *name*, whose refusals start with *where*."""
    if not isinstance(table, dict):
        msg = f"{where} must be a table"
        raise ValueError(msg)
    unknown = sorted(set(table) - _KEYS)
    if unknown:
        msg = f"{where}: unknown key(s) {unknown}; the keys are {sorted(_KEYS)}"
        raise ValueError(msg)
    ssh = _required_text(where, table, "ssh")
    # A control character would reach the ssh command line, where a NUL
    # stops the process from starting with an error that names no file.
    if (
        ssh.startswith("-")
        or any(character.isspace() for character in ssh)
        or _CONTROL.search(ssh) is not None
    ):
        msg = (
            f"{where}: 'ssh' must be a destination such as user@address or an "
            f"alias of ~/.ssh/config, got {ssh!r}"
        )
        raise ValueError(msg)
    runner = _runner(where, table)
    return HostEntry(
        name=name,
        ssh=ssh,
        runner=runner,
        target=_target(where, table, runner),
        label=_optional_text(where, table, "label") or name,
        timeout_s=_timeout(where, table),
    )


def _runner(where: str, table: dict[str, object]) -> Runner:
    """The entry's runner, one of :data:`_RUNNERS`."""
    value = _required_text(where, table, "runner")
    for runner in _RUNNERS:
        if value == runner:
            return runner
    msg = f"{where}: 'runner' must be 'docker' or 'python', got {value!r}"
    raise ValueError(msg)


def _target(where: str, table: dict[str, object], runner: Runner) -> str:
    """The image of a Docker node, or the interpreter of a Python one."""
    key, other, owner = (
        ("image", "python", "python")
        if runner == "docker"
        else ("python", "image", "docker")
    )
    if other in table:
        msg = f'{where}: {other!r} belongs to runner = "{owner}"'
        raise ValueError(msg)
    value = _required_text(where, table, key)
    if runner == "docker" and _IMAGE.fullmatch(value) is None:
        msg = f"{where}: 'image' must be a Docker image reference, got {value!r}"
        raise ValueError(msg)
    if runner == "python" and ("\n" in value or "\x00" in value):
        msg = f"{where}: 'python' must be one line, the interpreter's path"
        raise ValueError(msg)
    if runner == "python" and value.startswith("~"):
        # The remote command quotes the path, so the node's shell never
        # expands the "~".
        msg = (
            f"{where}: 'python' starts with '~', which the node does not expand; "
            "write the path absolute or relative to the home directory, where "
            f"ssh runs the command, got {value!r}"
        )
        raise ValueError(msg)
    return value


def _optional_text(where: str, table: dict[str, object], key: str) -> str | None:
    """A text field of the entry, ``None`` when absent."""
    value = table.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        msg = f"{where}: {key!r} must be a non-empty text, got {value!r}"
        raise ValueError(msg)
    return value


def _required_text(where: str, table: dict[str, object], key: str) -> str:
    """A text field the entry must have."""
    value = _optional_text(where, table, key)
    if value is None:
        msg = f"{where}: {key!r} is missing"
        raise ValueError(msg)
    return value


def _timeout(where: str, table: dict[str, object]) -> float | None:
    """The entry's ``timeout_s``, ``None`` when absent."""
    value = table.get("timeout_s")
    if value is None:
        return None
    msg = f"{where}: 'timeout_s' must be a positive number of seconds, got {value!r}"
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(msg)
    try:
        seconds = float(value)
    except OverflowError:
        # tomllib reads an integer of any size, and one past the range of a
        # float is no number of seconds a run can wait.
        raise ValueError(msg) from None
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError(msg)
    if seconds > threading.TIMEOUT_MAX:
        # The timer that stops a run would die on a longer one, and the run
        # would have no timeout at all.
        msg = (
            f"{where}: 'timeout_s' must be at most {int(threading.TIMEOUT_MAX)} "
            f"seconds, the longest a timer here waits, got {value!r}"
        )
        raise ValueError(msg)
    return seconds
