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
  test suite runs on;
- every file the GitHub Release carries has build provenance, and the
  checksum file is named for its version, as SECURITY.md says;
- every package uploaded to PyPI is built with the setuptools
  ``requirements-release.txt`` pins, and the release builds twice and holds
  the second build to the checksum file of the first;
- after a release, a job on another operating system rebuilds the tag the
  way SECURITY.md tells anyone to and compares it with PyPI, holding no
  token; in a rehearsal it rebuilds the commit and compares it with the run's
  own files, which publishes nothing.
"""

from __future__ import annotations

import pathlib
import re
import tomllib
from typing import Any

import pytest
import yaml
from packaging.requirements import Requirement

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WORKFLOWS = _ROOT / ".github" / "workflows"

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


# ==========================================================================
# Provenance for every file, and a build anyone can repeat
# ==========================================================================
#: Where a release's files lie when the GitHub Release job attests and uploads
#: them: the sdist and the wheel, and the checksum file and the SBOM.
_RELEASE_GLOBS = {"dist/*", "extras/*"}

#: The checksum file, as the build job names it and as SECURITY.md shows it.
_CHECKSUM_FILE = re.compile(r"phonometry-(?:\$VERSION|\d+\.\d+\.\d+)\.sha256")


def _security_section(heading: str) -> str:
    text = (_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    start = text.index(f"## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else None]


def _bash_blocks(text: str) -> str:
    """The commands of every ``bash`` block of *text*, a line ending in a backslash joined to the next."""
    blocks = re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL)
    return re.sub(r"\\\n\s*", "", "\n".join(blocks))


def _job_runs(workflow: dict[str, Any], job: str) -> str:
    return "\n".join(
        step.get("run", "") for step in workflow["jobs"][job].get("steps", [])
    )


def _python_of(workflow: dict[str, Any], job: str) -> str:
    versions = [
        step["with"]["python-version"]
        for step in workflow["jobs"][job]["steps"]
        if step.get("uses", "").startswith("actions/setup-python@")
    ]
    assert len(versions) == 1, f"{job} sets up {len(versions)} Pythons"
    return str(versions[0])


def test_every_file_the_release_uploads_is_attested() -> None:
    """The provenance names the same globs the release uploads, and nothing less.

    It named ``dist/*`` alone, while the release also uploaded the checksum
    file and the SBOM, so two of its four files could not be traced to the
    run that wrote them.
    """
    job = _load("release.yml")["jobs"]["github-release"]
    attested = [
        step["with"]["subject-path"]
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/attest-build-provenance@")
    ]
    assert len(attested) == 1
    assert set(attested[0].split()) == _RELEASE_GLOBS
    uploads = [
        step["run"]
        for step in job["steps"]
        if "gh release create" in step.get("run", "")
    ]
    assert len(uploads) == 1
    assert set(re.findall(r"(?:dist|extras)/\S*", uploads[0])) == _RELEASE_GLOBS
    downloaded = {
        step["with"]["path"]
        for step in job["steps"]
        if step.get("uses", "").startswith("actions/download-artifact@")
    }
    assert {glob.removesuffix("/*") for glob in _RELEASE_GLOBS} <= downloaded


def test_the_checksum_file_is_named_for_its_version_where_it_is_written_and_read() -> (
    None
):
    build = _job_runs(_load("release.yml"), "build")
    assert _CHECKSUM_FILE.search(build), (
        "the build job writes no phonometry-$VERSION.sha256"
    )
    for document in ("SECURITY.md", "CONTRIBUTING.md"):
        text = (_ROOT / document).read_text(encoding="utf-8")
        assert "SHA256SUMS" not in text, f"{document} still names SHA256SUMS"
    assert _CHECKSUM_FILE.search(_security_section("Verifying a release"))
    for path in _WORKFLOWS.glob("*.yml"):
        assert "SHA256SUMS" not in path.read_text(encoding="utf-8"), path.name


@pytest.mark.parametrize("name", ["release.yml", "publish-stub.yml"])
def test_every_upload_is_built_with_the_pinned_back_end(name: str) -> None:
    """The setuptools of ``requirements-release.txt``, not the newest of the day.

    ``python -m build`` makes an environment of its own and installs whatever
    setuptools is newest into it, so two builds of one commit a week apart
    could differ; a build of either package that reaches PyPI uses the
    pinned one in place, through ``--no-isolation`` directly or through
    ``scripts/build_release.py``.
    """
    workflow = _load(name)
    uploaders = _uploaders(workflow)
    builders = [
        job
        for job in sorted(set().union(*(_upstream(workflow, u) for u in uploaders)))
        if "python -m build" in _job_runs(workflow, job)
        or "scripts/build_release.py" in _job_runs(workflow, job)
    ]
    assert builders, f"{name}: no job upstream of the upload builds anything"
    for job in builders:
        runs = _job_runs(workflow, job)
        assert "-m pip install -r requirements-release.txt" in runs, job
        commands = re.findall(r"python -m build\b[^\n]*", runs)
        assert all("--no-isolation" in command for command in commands), commands


def test_the_pinned_back_end_satisfies_both_packages() -> None:
    """``--no-isolation`` builds with what is installed, so the pins must fit."""
    pins = {}
    for line in (
        (_ROOT / "requirements-release.txt").read_text(encoding="utf-8").splitlines()
    ):
        line = line.split("#", 1)[0].strip()
        if line:
            requirement = Requirement(line)
            (pinned,) = requirement.specifier
            assert pinned.operator == "==", f"{line} is not an exact pin"
            pins[requirement.name.lower()] = pinned.version
    assert "setuptools" in pins
    for project in ("pyproject.toml", "stub/pyproject.toml"):
        with (_ROOT / project).open("rb") as handle:
            requires = tomllib.load(handle)["build-system"]["requires"]
        for entry in requires:
            requirement = Requirement(entry)
            name = requirement.name.lower()
            assert name in pins, f"{project} builds with {name}, which nothing pins"
            assert requirement.specifier.contains(pins[name]), (
                f"{project} asks for {entry}, and the release pins {name} {pins[name]}"
            )


def test_the_release_builds_twice_and_holds_the_second_to_the_first() -> None:
    build = _load("release.yml")["jobs"]["build"]
    runs = [step.get("run", "") for step in build["steps"]]
    builds = [run for run in runs if "scripts/build_release.py" in run]
    assert len(builds) == 2, builds
    assert "--check" not in builds[0]
    assert re.search(r"--check \S*phonometry-\$VERSION\.sha256", builds[1])
    assert not any("python -m build" in run for run in runs)


def test_the_rebuild_runs_after_the_release_holding_no_token() -> None:
    """On another operating system, after the tag and the upload exist."""
    release = _load("release.yml")
    rebuild = release["jobs"]["rebuild"]
    assert rebuild["runs-on"] == "macos-latest"
    assert release["jobs"]["build"]["runs-on"] != rebuild["runs-on"]
    assert rebuild["permissions"] == {}
    assert {"publish", "github-release"} <= _upstream(release, "rebuild")
    assert "continue-on-error" not in rebuild
    assert not any(_publishes(step) for step in rebuild["steps"])
    assert _python_of(release, "rebuild") == _python_of(release, "build")


def test_the_rebuild_compares_a_rehearsal_with_its_run_and_a_release_with_pypi() -> (
    None
):
    steps = _load("release.yml")["jobs"]["rebuild"]["steps"]
    rehearsal = "env.REHEARSAL == 'true'"
    release = "env.REHEARSAL != 'true'"
    comparisons = {
        step.get("if"): step["run"]
        for step in steps
        if "scripts/build_release.py" in step.get("run", "")
    }
    assert set(comparisons) == {rehearsal, release}
    assert "--check-pypi" in comparisons[release]
    assert _CHECKSUM_FILE.search(comparisons[rehearsal])
    fetched = [
        step
        for step in steps
        if step.get("uses", "").startswith("actions/download-artifact@")
    ]
    assert [(step.get("if"), step["with"]["name"]) for step in fetched] == [
        (rehearsal, "release-extras")
    ]
    clone = next(step["run"] for step in steps if "git clone" in step.get("run", ""))
    assert '--branch "$TAG"' in clone
    assert '"$GITHUB_SHA"' in clone
    assert clone.count("autocrlf") == 2, "each way of fetching sets core.autocrlf"


def test_the_rebuild_follows_the_recipe_security_md_gives() -> None:
    """What the page tells anyone to run is what the release runs on itself."""
    recipe = _bash_blocks(_security_section("Rebuilding a release"))
    release = _load("release.yml")
    job = _job_runs(release, "rebuild")
    for fragment in (
        "--depth 1 --branch",
        "--config core.autocrlf=false",
        "-m venv",
        "-m pip install -r",
        "requirements-release.txt",
        "scripts/build_release.py --outdir",
        "--check-pypi",
    ):
        assert fragment in recipe, f"SECURITY.md no longer says {fragment!r}"
        assert fragment in job, f"the rebuild job no longer runs {fragment!r}"
    assert f"python{_python_of(release, 'build')} -m venv" in recipe
