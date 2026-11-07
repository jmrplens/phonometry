#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A script of the site that fails fails its test with what Node wrote.

The parity tests run the site's readers through :func:`node_script.answer`.
When Node cannot import a reader, or a reader throws, the cause is what Node
wrote on stderr; a :class:`subprocess.CalledProcessError` names only the
command and its status, so the report of the failing test has to carry the
stderr itself.
"""

from __future__ import annotations

import json
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
