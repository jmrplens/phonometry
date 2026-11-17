#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The last step of a grouped CI job names every guard of it that failed.

``.github/scripts/failed_steps.py`` reads the job's ``steps`` context as
JSON and writes one ``::error`` annotation per step whose outcome is a
failure, titled by the step's id, so the checks page of a pull request says
which guards of a group failed without anyone opening the log.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / ".github" / "scripts" / "failed_steps.py"


def _load() -> ModuleType:
    """Import the workflow script, which is not on any import path."""
    spec = importlib.util.spec_from_file_location("failed_steps", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


failed_steps = _load()


def _step(outcome: str) -> dict[str, object]:
    """One entry of the ``steps`` context, as the runner writes it."""
    conclusion = "success" if outcome == "skipped" else outcome
    return {"outputs": {}, "outcome": outcome, "conclusion": conclusion}


def test_every_failed_step_is_named_in_the_order_of_the_job() -> None:
    steps = {
        "python": _step("success"),
        "dead-constants": _step("failure"),
        "raises-blocks": _step("success"),
        "array-aliasing": _step("failure"),
        "clean-tree": _step("skipped"),
    }
    assert failed_steps.failed(steps) == ["dead-constants", "array-aliasing"]
    assert failed_steps.workflow_commands(steps) == [
        "::error title=dead-constants::The step dead-constants failed; its log says why.",
        "::error title=array-aliasing::The step array-aliasing failed; its log says why.",
    ]


def test_a_step_allowed_to_fail_is_named_by_its_outcome() -> None:
    """``continue-on-error`` concludes as a success; the outcome still failed."""
    steps = {"flaky": {"outcome": "failure", "conclusion": "success"}}
    assert failed_steps.failed(steps) == ["flaky"]


def test_a_failure_no_id_names_is_still_reported() -> None:
    """The context holds only steps with an id; the job failed all the same."""
    lines = failed_steps.workflow_commands({"python": _step("success")})
    assert len(lines) == 1
    assert lines[0].startswith("::error title=Unnamed step::")


def test_an_id_is_escaped_for_the_title() -> None:
    lines = failed_steps.workflow_commands({"a:b,c%": _step("failure")})
    assert lines[0].startswith("::error title=a%3Ab%2Cc%25::")


def test_a_context_that_is_not_a_mapping_is_refused() -> None:
    with pytest.raises(TypeError, match="not a mapping"):
        failed_steps.failed(["dead-constants"])


@pytest.mark.parametrize(
    ("environ", "expected"),
    [
        ({}, "::warning::STEPS is not set"),
        ({"STEPS": "not json"}, "::warning::STEPS holds no steps context"),
        ({"STEPS": "[]"}, "::warning::STEPS holds no steps context"),
    ],
)
def test_an_unreadable_context_is_a_warning_and_never_a_second_failure(
    environ: dict[str, str], expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert failed_steps.main(environ) == 0
    assert capsys.readouterr().out.startswith(expected)


def test_the_script_runs_as_the_workflow_runs_it() -> None:
    """``python3 .github/scripts/failed_steps.py`` with the context in STEPS."""
    steps = {"python": _step("success"), "euler-number": _step("failure")}
    result = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
        cwd=_ROOT,
        env={**os.environ, "STEPS": json.dumps(steps)},
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "::error title=euler-number::The step euler-number failed; its log says why."
    ]
