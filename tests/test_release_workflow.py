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
- the built wheel is verified on the same platforms and Python versions the
  test suite runs on.
"""

from __future__ import annotations

import pathlib
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
    uploading = {
        job
        for job, step in _steps(workflow)
        if step.get("uses", "").startswith("pypa/gh-action-pypi-publish")
    }
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
