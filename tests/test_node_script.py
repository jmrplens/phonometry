#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A script of the site that fails fails its test with what Node wrote.

The parity tests run the site's readers through :func:`node_script.answer`.
When Node cannot import a reader, or a reader throws, the cause is what Node
wrote on stderr; a :class:`subprocess.CalledProcessError` names only the
command and its status, so the report of the failing test has to carry the
stderr itself, and the status beside it for a Node that ends with nothing on
stderr.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

import node_script
import pytest

if TYPE_CHECKING:
    import pathlib

pytestmark = pytest.mark.skipif(
    node_script.NODE is None, reason="no JavaScript engine to run a script with"
)

#: How long a script here may run [s]: each one ends in well under a second.
_SCRIPT_S = 60.0

#: The time limit of a script that never ends on its own [s].
_PAST_S = 5.0

#: The limits a script that writes on stderr and never ends is run with, one
#: after the other until Node has started and written before it is stopped
#: [s]: a loaded runner can take the first of them only to start Node, which
#: is then stopped with nothing written, and the last bounds the wait.
_PAST_LIMITS_S = (_PAST_S, 4 * _PAST_S, 16 * _PAST_S)

#: A script that reads its input and answers one entry for each entry given.
_DOUBLES = (
    "let input = '';"
    "for await (const chunk of process.stdin) input += chunk;"
    "process.stdout.write(JSON.stringify(JSON.parse(input).map((x) => 2 * x)));"
)


def test_a_script_answers_one_entry_for_each_entry_it_is_given() -> None:
    assert node_script.answer(_DOUBLES, [1, 2.5, -3], timeout=_SCRIPT_S) == [2, 5, -6]


def test_a_script_that_throws_fails_with_what_node_wrote() -> None:
    script = "throw new Error('the reader read past its page');"
    with pytest.raises(AssertionError, match="Error: the reader read past its page"):
        node_script.answer(script, [], timeout=_SCRIPT_S)


def test_a_reader_that_does_not_load_fails_with_what_node_wrote(
    tmp_path: pathlib.Path,
) -> None:
    missing = tmp_path / "markdown-spans.mjs"
    script = f"import {{pageMarkup}} from {json.dumps(missing.as_uri())};"
    with pytest.raises(AssertionError, match="ERR_MODULE_NOT_FOUND"):
        node_script.answer(script, [], timeout=_SCRIPT_S)


def test_a_script_that_ends_with_a_status_and_writes_nothing_fails_with_it() -> None:
    """Pytest does not rewrite the ``assert`` of a module that is not a test
    module, so its message is all the report says: with nothing on stderr, the
    status has to be in it.
    """
    script = "process.exitCode = 3;"
    with pytest.raises(
        AssertionError, match="^Node ended with status 3 and wrote nothing on stderr$"
    ):
        node_script.answer(script, [], timeout=_SCRIPT_S)


@pytest.mark.skipif(
    sys.platform == "win32", reason="a signal stops a process on POSIX only"
)
def test_a_script_stopped_by_a_signal_fails_with_that_signal() -> None:
    """A Node the kernel stops, as it stops a process that runs out of memory,
    writes nothing on stderr: the signal is all there is to report.
    """
    script = "process.kill(process.pid, 'SIGKILL');"
    with pytest.raises(AssertionError, match="^Node was stopped by signal 9 "):
        node_script.answer(script, [], timeout=_SCRIPT_S)


def _stopped(script: str) -> tuple[float, str]:
    """The limit a Node running *script* was stopped at once it had written
    on stderr, and the message it failed with, the limit raised through
    :data:`_PAST_LIMITS_S` while Node was stopped before it wrote anything.
    """
    for limit in _PAST_LIMITS_S:
        with pytest.raises(AssertionError) as caught:
            node_script.answer(script, [], timeout=limit)
        message = str(caught.value)
        if not message.endswith("and wrote nothing on stderr"):
            break
    return limit, message


def test_a_script_that_runs_past_its_time_fails_with_what_node_wrote() -> None:
    """``subprocess.TimeoutExpired`` names the command and the time, and keeps
    what Node wrote on stderr where the report does not show it.
    """
    script = (
        "process.stderr.write('the reader went round line 3 again\\n');"
        "setInterval(() => {}, 1000);"
    )
    limit, message = _stopped(script)
    assert message == (
        f"Node ran past its {limit:g} s and was stopped, and wrote on stderr:\n"
        "the reader went round line 3 again\n"
    )


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="on Windows subprocess decodes what Node wrote before the helper does",
)
def test_a_script_that_runs_past_its_time_keeps_bytes_it_cannot_decode() -> None:
    """On POSIX ``subprocess.TimeoutExpired`` keeps stderr as bytes whatever
    ``text=`` asked for, and a byte that is not UTF-8 is read as a
    replacement character, so the rest of the message is not lost with it.
    """
    script = (
        "process.stderr.write(Buffer.from([0x62, 0x61, 0x64, 0xff, 0x0a]));"
        "setInterval(() => {}, 1000);"
    )
    limit, message = _stopped(script)
    assert message == (
        f"Node ran past its {limit:g} s and was stopped, and wrote on stderr:\n"
        "bad\ufffd\n"
    )


def test_a_script_that_runs_past_its_time_silently_says_so() -> None:
    with pytest.raises(
        AssertionError,
        match=r"^Node ran past its 5 s and was stopped and wrote nothing on stderr$",
    ):
        node_script.answer("setInterval(() => {}, 1000);", [], timeout=_PAST_S)
