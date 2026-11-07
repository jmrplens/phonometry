#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A script of the site's own JavaScript, run by Node on what a test hands it.

The parity tests hand pages to the site's readers and compare what comes
back with what the scripts' Python readers make of the same pages.
:func:`answer` gives the script its input as JSON on stdin and reads its
answer as JSON from stdout. When Node fails, to import a reader or inside
one, the test fails with how Node ended and what it wrote on stderr: the
cause is there, and a :class:`subprocess.CalledProcessError` names only the
command and its status.
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
        stderr.
    """
    assert NODE is not None, "no JavaScript engine on the path"
    ran = subprocess.run(  # nosec B603 - a fixed argument list
        [NODE, "--input-type=module", "-e", script],
        input=json.dumps(given),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        check=False,
    )
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
    if not ran.stderr:
        return f"{ended} and wrote nothing on stderr"
    return f"{ended}, and wrote on stderr:\n{ran.stderr}"
