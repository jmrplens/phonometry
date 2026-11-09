#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A script of the site's own JavaScript, run by Node on what a test hands it.

The parity tests hand pages to the site's readers and compare what comes
back with what the scripts' Python readers make of the same pages.
:func:`answer` gives the script its input as JSON on stdin and reads its
answer as JSON from stdout. When Node fails, to import a reader or inside
one, or runs past its time and is stopped, the test fails with how Node
ended and what it wrote on stderr: the cause is there, and a
:class:`subprocess.CalledProcessError` or :class:`subprocess.TimeoutExpired`
names only the command and its status or its time.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 - the tests' own scripts, never a shell

#: The JavaScript engine on the path, or ``None`` where there is none.
NODE = shutil.which("node")


def answer(script: str, given: object, *, timeout: float) -> list[object]:
    """What *script*, run by Node as a module with *given* as JSON on its
    stdin, writes on stdout, read as JSON.

    :param script: A module that reads its stdin to the end and writes one
        JSON array.
    :param given: What the script reads.
    :param timeout: How long Node may take [s].
    :raises AssertionError: when Node ends with a status other than 0, with
        that status, or the signal that stopped it, and what it wrote on
        stderr; and when it runs past *timeout* and is stopped, with what it
        wrote on stderr before then. Node writes on stdout and on stderr
        what a script hands it, so a byte that is not UTF-8 is read as a
        replacement character on either rather than failing the read.
    """
    assert NODE is not None, "no JavaScript engine on the path"
    try:
        ran = subprocess.run(  # nosec B603 - a fixed argument list
            [NODE, "--input-type=module", "-e", script],
            input=json.dumps(given),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as stopped:
        ended = f"Node ran past its {timeout:g} s and was stopped"
        raise AssertionError(_with_stderr(ended, stopped.stderr)) from None
    assert ran.returncode == 0, _how_node_ended(ran)
    read: list[object] = json.loads(ran.stdout)
    return read


def _how_node_ended(ran: subprocess.CompletedProcess[str]) -> str:
    """What the report of a failed test says of a Node that ended badly.

    Pytest rewrites the ``assert`` of a test module to show the values it
    compares, and not this module's, so the message is all the report says:
    it names the status, or the signal that stopped Node, which a process
    killed for running out of memory has and nothing on stderr besides.

    :param ran: How Node ended.
    """
    if ran.returncode < 0:
        ended = f"Node was stopped by signal {-ran.returncode}"
    else:
        ended = f"Node ended with status {ran.returncode}"
    return _with_stderr(ended, ran.stderr)


def _with_stderr(ended: str, stderr: bytes | str | None) -> str:
    """*ended*, how Node ended, with what it wrote on *stderr*.

    :param stderr: What Node wrote there: text for a Node that ended, and for
        one stopped at its time limit what :class:`subprocess.TimeoutExpired`
        kept, bytes on POSIX whatever ``text=`` asked for, text on Windows,
        ``None`` for nothing. Bytes are decoded as :func:`answer` decodes
        text, a byte that is not UTF-8 read as a replacement character.
    """
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if not stderr:
        return f"{ended} and wrote nothing on stderr"
    return f"{ended}, and wrote on stderr:\n{stderr}"
