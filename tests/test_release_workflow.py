#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The release workflow's guarantees, read off the workflow files themselves.

The release cannot be exercised end to end by a test: it uploads to PyPI, and
a version can be uploaded once. What it promises can still be read from the
YAML, and these tests hold the promises a careless edit would break without
any run failing until the day of a release:

- a manual run is a rehearsal, and no step that publishes, tags or attests
  runs in one;
- the only identity that can upload is an OIDC token in a job that holds
  nothing else, and no workflow reads a stored PyPI token any more;
- no job is granted a token by default;
- neither phonometry nor the PyOctaveBand stub is uploaded from a commit on
  which Python CI did not succeed: the upload waits for that run, nothing on
  the way lets it go ahead after the wait failed, and the wait has the time it
  allows itself;
- the built wheel is verified on the same platforms and Python versions the
  test suite runs on.
"""

from __future__ import annotations

import pathlib
import re
from typing import Any

import pytest
import yaml

_WORKFLOWS = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows"

#: What a release step does that a rehearsal must never do.
_PUBLISHING_ACTIONS = (
    "pypa/gh-action-pypi-publish",
    "actions/attest-build-provenance",
    "actions/attest-sbom",
)
_PUBLISHING_COMMANDS = ("gh release create", "gh workflow run")
_GUARD = "env.REHEARSAL != 'true'"

#: The step that waits for Python CI on the commit being published.
_CI_WAIT = "Require a green Python CI on this commit"

#: Where the wait sets the time it gives Python CI to finish, in seconds.
_FINISH_DEADLINE = re.compile(r"finish_deadline=\$\(\( SECONDS \+ (\d+) \)\)")

#: The condition the wait runs under in each workflow: the release skips it for
#: a version already tagged, which publishes nothing, and the stub always runs it.
_CI_WAIT_CONDITION = {
    "release.yml": "steps.version.outputs.skip != 'true'",
    "publish-stub.yml": None,
}

#: A status function in a job's ``if``. Without one a job runs only when every
#: job it needs succeeded; with ``always()``, ``!cancelled()``, ``failure()`` or
#: ``success() || ...`` it can run after one of them failed.
_STATUS_FUNCTION = re.compile(r"\b(?:always|success|failure|cancelled)\s*\(")


def _load(name: str) -> dict[str, Any]:
    return yaml.safe_load((_WORKFLOWS / name).read_text(encoding="utf-8"))


def _steps(workflow: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [
        (job_id, step)
        for job_id, job in workflow["jobs"].items()
        for step in job.get("steps", [])
    ]


def _publishes(step: dict[str, Any]) -> bool:
    uses = step.get("uses", "")
    run = step.get("run", "")
    return uses.startswith(_PUBLISHING_ACTIONS) or any(
        command in run for command in _PUBLISHING_COMMANDS
    )


def _upstream(workflow: dict[str, Any], job: str) -> set[str]:
    """Every job *job* waits for, directly or through another."""
    needs = workflow["jobs"][job].get("needs", [])
    direct = {needs} if isinstance(needs, str) else set(needs)
    return direct.union(*(_upstream(workflow, other) for other in direct))


def _uploaders(workflow: dict[str, Any]) -> set[str]:
    """The jobs that upload to PyPI."""
    return {
        job
        for job, step in _steps(workflow)
        if step.get("uses", "").startswith("pypa/gh-action-pypi-publish")
    }


def _between(workflow: dict[str, Any], first: str, last: str) -> set[str]:
    """Every job on a chain of ``needs`` from *first* to *last*, both included."""
    return {
        job
        for job in workflow["jobs"]
        if (job == first or first in _upstream(workflow, job))
        and (job == last or job in _upstream(workflow, last))
    }


def _ci_wait(workflow: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """The job that waits for Python CI, and the step that does the waiting."""
    found = [
        (job, step) for job, step in _steps(workflow) if step.get("name") == _CI_WAIT
    ]
    assert len(found) == 1, f"expected one step named {_CI_WAIT!r}, found {len(found)}"
    return found[0]


def test_the_stub_is_published_only_after_the_wait_for_ci() -> None:
    """The stub waits for Python CI before anything is built, as the release does.

    A version number cannot be uploaded twice, and the stub's build job holds
    ten minutes and no Actions permission, which is why the wait is a job of
    its own that the build needs. The step is the release's own, so a later
    change to how long it waits, or to what it accepts, reaches both or fails
    here.
    """
    stub = _load("publish-stub.yml")
    job, step = _ci_wait(stub)
    assert job == "preflight"
    assert stub["jobs"][job]["permissions"] == {"actions": "read"}
    assert not any("uses" in other for other in stub["jobs"][job]["steps"]), (
        "the wait reads the API, not the checkout, and runs no action"
    )
    uploading = _uploaders(stub)
    assert uploading
    for name in uploading:
        assert job in _upstream(stub, name), f"{name} does not wait for {job}"
    assert job in _upstream(stub, "build"), "the build runs before CI has passed"
    _, released = _ci_wait(_load("release.yml"))
    assert step["run"] == released["run"]
    assert step["env"] == released["env"]


@pytest.mark.parametrize("name", ["release.yml", "publish-stub.yml"])
def test_nothing_lets_the_upload_go_ahead_after_the_wait_for_ci_failed(
    name: str,
) -> None:
    """A failed wait stops every job between it and the upload.

    The ``needs`` alone do not say so. A step whose ``if`` is false does not
    run, a step or a job marked ``continue-on-error`` counts as passed when it
    fails, and a job whose ``if`` calls a status function runs after a job it
    needs failed. Each is one line, and with any of them the wait is still
    there, still the release's word for word, and nothing waits for it.
    """
    workflow = _load(name)
    job, step = _ci_wait(workflow)
    assert "continue-on-error" not in step, f"{name}: the wait may fail and pass"
    assert step.get("if") == _CI_WAIT_CONDITION[name], (
        f"{name}: the wait runs under {step.get('if')!r}"
    )
    uploaders = _uploaders(workflow)
    assert uploaders, f"{name} no longer uploads through trusted publishing"
    for uploader in uploaders:
        assert job in _upstream(workflow, uploader), f"{uploader} does not wait"
        for between in sorted(_between(workflow, job, uploader)):
            settings = workflow["jobs"][between]
            assert "continue-on-error" not in settings, (
                f"{name}: {between} lets {uploader} run after it failed"
            )
            condition = str(settings.get("if", ""))
            assert not _STATUS_FUNCTION.search(condition), (
                f"{name}: {between} runs under {condition!r}, which does not "
                f"stop at a failed {job}"
            )


@pytest.mark.parametrize("name", ["release.yml", "publish-stub.yml"])
def test_the_wait_for_ci_ends_before_its_job_is_killed(name: str) -> None:
    """The job's ceiling lies above the wait's own deadline.

    Below it, the runner kills the job mid-wait with a cancellation that names
    no cause, where the wait would have said what it was still waiting on.
    """
    workflow = _load(name)
    job, step = _ci_wait(workflow)
    deadline = _FINISH_DEADLINE.search(step["run"])
    assert deadline is not None, f"{name}: the wait no longer sets finish_deadline"
    timeout_seconds = 60 * int(workflow["jobs"][job]["timeout-minutes"])
    assert timeout_seconds > int(deadline.group(1)), (
        f"{name}: {job} is killed after {timeout_seconds} s, before the wait "
        f"gives up at {deadline.group(1)} s"
    )


def test_a_manual_run_is_a_rehearsal() -> None:
    release = _load("release.yml")
    assert (
        release["env"]["REHEARSAL"] == "${{ github.event_name == 'workflow_dispatch' }}"
    )


def test_no_step_that_publishes_runs_in_a_rehearsal() -> None:
    release = _load("release.yml")
    publishing = [(job, step) for job, step in _steps(release) if _publishes(step)]
    assert len(publishing) >= 5, (
        "the release no longer uploads, attests, tags and dispatches"
    )
    unguarded = [
        f"{job}: {step.get('name', step.get('uses'))}"
        for job, step in publishing
        if _GUARD not in step.get("if", "")
    ]
    assert unguarded == []


def test_a_rehearsal_proves_the_trusted_publisher_without_uploading() -> None:
    release = _load("release.yml")
    proof = [
        step
        for _, step in _steps(release)
        if "_/oidc/mint-token" in step.get("run", "")
    ]
    assert len(proof) == 1
    assert proof[0]["if"] == "env.REHEARSAL == 'true'"
    assert "workflow release.yml" in proof[0]["run"], (
        "the message must name this file, which is what PyPI matches"
    )


@pytest.mark.parametrize("name", ["release.yml", "publish-stub.yml"])
def test_no_job_inherits_a_token(name: str) -> None:
    workflow = _load(name)
    assert workflow["permissions"] == {}
    assert all("permissions" in job for job in workflow["jobs"].values())


@pytest.mark.parametrize("name", ["release.yml", "publish-stub.yml"])
def test_the_upload_holds_nothing_but_its_oidc_token(name: str) -> None:
    workflow = _load(name)
    uploading = _uploaders(workflow)
    assert uploading, f"{name} no longer uploads through trusted publishing"
    for job in uploading:
        assert workflow["jobs"][job]["permissions"] == {"id-token": "write"}
        assert not any(
            "actions/checkout" in step.get("uses", "")
            for step in workflow["jobs"][job]["steps"]
        )


def test_no_workflow_reads_a_stored_pypi_token() -> None:
    readers = [
        path.name
        for path in _WORKFLOWS.glob("*.yml")
        if "PYPI_TOKEN" in path.read_text(encoding="utf-8")
    ]
    assert readers == []


def test_the_wheel_is_verified_where_the_suite_runs() -> None:
    verify = _load("release.yml")["jobs"]["verify"]["strategy"]["matrix"]
    tests = _load("python-app.yml")["jobs"]["tests"]["strategy"]["matrix"]
    assert verify["os"] == tests["os"]
    assert verify["python-version"] == tests["python-version"]


def test_the_mirror_is_dispatched_rather_than_triggered_by_another_run() -> None:
    mirror = _load("gitlab-mirror.yml")
    triggers = mirror.get("on", mirror.get(True))
    assert "workflow_run" not in triggers
    assert "workflow_dispatch" in triggers
    dispatches = [
        step["run"]
        for _, step in _steps(_load("release.yml"))
        if "gh workflow run" in step.get("run", "")
    ]
    assert dispatches == [
        'gh workflow run gitlab-mirror.yml --repo "$GITHUB_REPOSITORY" --ref main'
    ]
