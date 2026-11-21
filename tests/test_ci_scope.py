#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which jobs of Python CI a pull request reaches, and what each one reads.

``scripts/ci_scope.py`` reads the files a pull request changes and names the
jobs none of them reaches; the ``scope`` job of
``.github/workflows/python-app.yml`` hands the answer to the jobs that can
skip and narrows the test matrix to one leg. These tests fix what reaches
which job, that a doubt runs every job, that the map knows every file the
repository tracks and names none it does not, that the matrix the script
narrows is the workflow's own, and which jobs run on every pull request, so
a job added to the workflow takes a side on purpose.
"""

from __future__ import annotations

import ast
import io
import json
import pathlib
import sys
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import child_process
import ci_scope
import guard_caches
import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator

#: The map reads the imports of every module under scripts/ and tests/ once,
#: and the tests that ask it share that read on one worker (rule T19).
pytestmark = [pytest.mark.whole_tree, pytest.mark.xdist_group("ci-scope")]

_WORKFLOW = _ROOT / ".github" / "workflows" / "python-app.yml"

#: The jobs that run on every pull request, each with why no change spares it.
_ALWAYS = {
    "scope": "says which jobs run",
    "tests": "one leg: its tests read the code, the pages, the edition and the prose",
    "quality": "lint, types and the published clips, over every file",
    "release-build": "the release build, on every pull request",
    "release-rebuild-macos": "the release rebuilt on macOS, on every pull request",
    "guards-package": "the API reference and the conformance report regenerated",
    "guards-prose": "the prose rules and the llms files regenerated",
    "guards-source": "the rules that read the code and the pages together",
    "sonar": "reads the leg every pull request runs",
    "pr-comment": "reads the legs that ran",
}

#: The one condition each job of _ALWAYS may carry: none, the lane link that
#: waits out a red job before it, or its own rule for the event it reports
#: on. Anything else could leave a pull request without the job.
_ALWAYS_CONDITIONS = {
    "tests": "${{ !cancelled() }}",
    "guards-package": "${{ !cancelled() }}",
    "guards-prose": "${{ !cancelled() }}",
    "guards-source": "${{ !cancelled() }}",
    "sonar": (
        "github.actor != 'dependabot[bot]' && (github.event_name == 'pull_request' "
        "|| github.ref == 'refs/heads/master' || github.ref == 'refs/heads/main')"
    ),
    "pr-comment": "${{ !cancelled() && github.event_name == 'pull_request' }}",
}

_EVERY_JOB = ci_scope.jobs_to_skip([])


@pytest.fixture(scope="module", autouse=True)
def _forget_the_map() -> Iterator[None]:
    """Let go of the patterns the map read once this module's tests are done."""
    yield
    guard_caches.forget(ci_scope)


def _jobs() -> dict[str, dict[str, object]]:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    jobs: dict[str, dict[str, object]] = workflow["jobs"]
    return jobs


def _needs(job: dict[str, object]) -> list[str]:
    """The jobs *job* waits on, whether ``needs`` names one or a list."""
    wanted = job.get("needs", [])
    if isinstance(wanted, str):
        return [wanted]
    return [str(name) for name in wanted] if isinstance(wanted, list) else []


def _condition(job: str) -> str:
    """The condition a job that can skip runs under: every answer but its name."""
    return (
        f"${{{{ !cancelled() && (!contains(needs.scope.outputs.skip, ',{job},')) }}}}"
    )


def _runs(paths: list[str]) -> set[str]:
    """The jobs of the map a change of *paths* runs."""
    return set(ci_scope.JOBS) - set(ci_scope.jobs_to_skip(paths))


def _tracked() -> list[str]:
    listing = child_process.run(
        ["git", "-C", str(_ROOT), "ls-files", "-z"],
        timeout=60,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return [name for name in listing.split("\0") if name]


def test_no_change_and_any_doubt_skip_nothing() -> None:
    assert _EVERY_JOB == []
    assert (
        ci_scope.jobs_to_skip(["docs/start/privacy.md"] * ci_scope.API_FILE_LIMIT) == []
    )


@pytest.mark.parametrize(
    "path",
    [
        "src/phonometry/__init__.py",
        "pyproject.toml",
        "requirements-dev.txt",
        "VERSION",
        "Makefile",
        ".gitattributes",
        ".github/workflows/python-app.yml",
        ".github/scripts/failed_steps.py",
        "scripts/ci_scope.py",
        # A file the map does not know.
        "benchmarks/run.py",
        ".github/actions/setup/action.yml",
        # A module the change removed: the modules left no longer show who
        # imported it.
        "scripts/no_such_module.py",
        "tests/no_such_helper.py",
    ],
)
def test_the_library_the_workflow_and_an_unknown_file_run_every_job(path: str) -> None:
    assert ci_scope.jobs_to_skip(["site/src/content/docs/start/privacy.md", path]) == []


@pytest.mark.parametrize(
    ("paths", "runs"),
    [
        # A page: its examples run, and the fiche gate reads the fiches pages embed.
        (["site/src/content/docs/start/privacy.md"], {"doc-snippets", "reports"}),
        (["site/src/content/docs/es/start/privacy.md"], {"doc-snippets", "reports"}),
        # The edition and the hand-written files of docs/ hold examples too.
        (["docs/ERRATA.md"], {"doc-snippets"}),
        # The package's description runs examples and is built into the package.
        (["README.md"], {"doc-snippets", "built-package"}),
        # The site's code, the prose and the other workflows reach none.
        (["site/src/components/Figure.astro"], set()),
        (["CHANGELOG.md", "CONTRIBUTING.md", "llms.txt"], {"doc-snippets"}),
        ([".github/workflows/docs.yml", ".github/dependabot.yml"], set()),
        # A test runs everything that runs the suite, and nothing that draws.
        (
            ["tests/test_basic.py"],
            {
                "tests-legs",
                "tests-perf",
                "minimum-versions",
                "baseline-glibc",
                "array-api",
                "mps",
                "remote-node",
                "video",
            },
        ),
        # A guard reaches the suite, whose tests exercise it on every leg.
        (
            ["scripts/check_em_dashes.py"],
            {"tests-legs", "tests-perf", "minimum-versions"},
        ),
        # The node image reaches the job that builds it.
        (["docker/node/Dockerfile"], {"remote-node"}),
        # The stub is built and tested.
        (
            ["stub/pyproject.toml"],
            {"tests-legs", "tests-perf", "minimum-versions", "built-package"},
        ),
        # The committed figures and fiches reach their own check.
        ([".github/images/absorber_stack_geometry_dark.svg"], {"figures"}),
        ([".github/reports/ansi_s12_2_noise_criteria_example.pdf"], {"reports"}),
    ],
)
def test_each_change_runs_the_jobs_that_read_it(
    paths: list[str], runs: set[str]
) -> None:
    assert _runs(paths) == runs


def test_a_generator_reaches_its_job_and_the_test_fixtures_it_imports() -> None:
    # The figure and fiche generators import the shared test fixtures, so a
    # fixture reaches them; a figure module reaches the figures alone.
    figures = ci_scope.job_patterns()["figures"]
    assert "scripts/figures/room.py" in figures
    assert "tests/iso12354_building.py" in figures
    assert "tests/reference_data/__init__.py" in figures
    assert "figures" in _runs(["tests/iso12354_building.py"])
    assert "reports" in _runs(["tests/reference_data/building.py"])
    # A figure module reaches the figures and the suite, and the engine jobs
    # whose tests import the clip modules that import it; never the fiches or
    # the examples.
    room = _runs(["scripts/figures/room.py"])
    assert {"tests-legs", "tests-perf", "minimum-versions", "figures"} <= room
    assert not room & {"reports", "doc-snippets", "built-package", "notebook"}
    # The guides load the test data in their examples.
    assert "doc-snippets" in _runs(["tests/data/cnossos/README.md"])


def test_a_change_the_other_legs_cannot_read_runs_one_leg() -> None:
    lines = ci_scope.outputs(["site/src/content/docs/start/privacy.md\n"]).splitlines()
    answer = dict(line.split("=", 1) for line in lines)
    skip = answer["skip"].strip(",").split(",")
    assert set(skip) == set(ci_scope.JOBS) - {"doc-snippets", "reports"}
    assert answer["skip"].startswith(",")
    assert answer["skip"].endswith(",")
    exclude = json.loads(answer["tests-exclude"])
    kept = {
        (os_name, python)
        for os_name in ci_scope.TEST_OSES
        for python in ci_scope.TEST_PYTHONS
    } - {(cell["os"], cell["python-version"]) for cell in exclude}
    assert kept == {ci_scope.DOCS_LEG}


def test_a_change_the_suite_reads_runs_every_leg() -> None:
    lines = ci_scope.outputs(["tests/test_basic.py\n"]).splitlines()
    answer = dict(line.split("=", 1) for line in lines)
    assert answer["tests-exclude"] == "[]"
    assert ",figures," in answer["skip"]


def test_a_scope_it_cannot_read_runs_every_job(monkeypatch: pytest.MonkeyPatch) -> None:
    class Unreadable:
        """A standard input whose bytes are not text."""

        def __iter__(self) -> Unreadable:
            encoding = "utf-8"
            raise UnicodeDecodeError(encoding, b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(sys, "stdin", Unreadable())
    written = io.StringIO()
    with redirect_stdout(written):
        assert ci_scope.main() == 0
    assert written.getvalue() == "skip=\ntests-exclude=[]\n"


def test_the_reasons_name_the_file_that_reaches_each_job() -> None:
    reasons = ci_scope.explain(["docker/node/Dockerfile", "docker/node/provision.sh"])
    assert "remote-node: runs (docker/node/Dockerfile and 1 more)" in reasons
    assert "figures: skips" in reasons
    # An answer that runs everything says why.
    assert ci_scope.explain([]) == "every job runs: no changed file was read\n"
    assert (
        ci_scope.explain(["VERSION"]) == "every job runs: VERSION reaches every job\n"
    )
    assert ci_scope.explain(["benchmarks/run.py"]) == (
        "every job runs: benchmarks/run.py is a file the map does not know\n"
    )
    assert ci_scope.explain(["scripts/no_such_module.py"]) == (
        "every job runs: scripts/no_such_module.py is a module the change removes\n"
    )


@pytest.mark.git_checkout
def test_the_map_knows_every_tracked_file_and_names_none_that_is_gone() -> None:
    # A new kind of file runs every job until the map says what it reaches,
    # and a renamed or removed path would leave a pattern matching nothing.
    tracked = _tracked()
    patterns = ci_scope.job_patterns()
    known = [
        *ci_scope.EVERY_JOB,
        *ci_scope.NO_JOB,
        *(pattern for job in patterns.values() for pattern in job),
    ]
    unknown = [
        path for path in tracked if not any(ci_scope.matches(path, k) for k in known)
    ]
    assert unknown == []
    written = [
        *ci_scope.EVERY_JOB,
        *ci_scope.NO_JOB,
        *(pattern for reach in ci_scope.JOBS.values() for pattern in reach.paths),
    ]
    dead = [
        p for p in written if not any(ci_scope.matches(path, p) for path in tracked)
    ]
    assert dead == []


def test_every_module_a_job_runs_is_a_module_of_scripts() -> None:
    with pytest.raises(ValueError, match="no such module in scripts or tests: nowhere"):
        ci_scope.module_closure(["nowhere"])
    for reach in ci_scope.JOBS.values():
        for module in reach.modules:
            assert (_ROOT / "scripts" / f"{module}.py").is_file(), module


def test_a_job_that_runs_tests_is_reached_by_what_they_import_and_read() -> None:
    # The simulation tests import the engine scenarios from scripts/ and
    # compare against the engine records at the root: each reaches the jobs
    # that run those tests, beside the suite.
    engines = {"array-api", "mps", "remote-node", "video", "baseline-glibc"}
    suite = {"tests-legs", "tests-perf", "minimum-versions"}
    assert _runs(["scripts/engine_scenarios.py"]) >= engines | suite
    for record in ci_scope.ENGINE_RECORDS:
        assert _runs([record]) >= engines - {"video"}
    assert ci_scope.module_closure(iter(["engine_scenarios"]))


@pytest.mark.git_checkout
def test_every_root_file_a_job_names_reaches_it() -> None:
    # A file at the root that a job's scripts or tests name by a string is one
    # the job reads; a change to it alone must not skip the job, unless the map
    # sends it to no job that can skip (the changelog, whose numbers the
    # published-numbers tests hold on the leg every pull request runs).
    tracked = {path for path in _tracked() if "/" not in path}
    patterns = ci_scope.job_patterns()
    missing = []
    for job, reach in ci_scope.JOBS.items():
        if not reach.modules and not reach.tests:
            continue
        files = ci_scope.module_closure(reach.modules) + ci_scope.test_files(
            reach.tests
        )
        named = {
            node.value
            for path in files
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Constant) and node.value in tracked
        }
        for name in sorted(named):
            reached_by = [*ci_scope.EVERY_JOB, *ci_scope.NO_JOB, *patterns[job]]
            if not any(ci_scope.matches(name, pattern) for pattern in reached_by):
                missing.append(f"{job}: {name}")
    assert missing == []


def test_the_matrix_the_script_narrows_is_the_workflow_matrix() -> None:
    tests = _jobs()["tests"]
    strategy = tests["strategy"]
    assert isinstance(strategy, dict)
    matrix = strategy["matrix"]
    assert matrix["os"] == list(ci_scope.TEST_OSES)
    assert [str(version) for version in matrix["python-version"]] == list(
        ci_scope.TEST_PYTHONS
    )
    assert matrix["exclude"] == (
        "${{ fromJSON(needs.scope.outputs.tests-exclude || '[]') }}"
    )
    assert tests["needs"] == "scope"
    # A failed scope leaves the matrix whole instead of skipping the tests.
    assert tests["if"] == "${{ !cancelled() }}"


def test_the_leg_every_pull_request_runs_is_the_one_its_readers_read() -> None:
    os_name, python = ci_scope.DOCS_LEG
    steps = _jobs()["sonar"]["steps"]
    assert isinstance(steps, list)
    downloads = [
        step["with"]["name"]
        for step in steps
        if str(step.get("uses", "")).startswith("actions/download-artifact@")
    ]
    assert downloads == [f"test-results-{os_name}-{python}"]


def test_every_job_runs_always_or_skips_on_its_own_name() -> None:
    # A new job takes a side here: listed in _ALWAYS with its reason, or in
    # the map, waiting on the scope under a condition that runs it on any
    # answer that does not name it.
    jobs = _jobs()
    problems = []
    for name, job in jobs.items():
        condition = str(job.get("if", ""))
        if name in _ALWAYS:
            allowed = _ALWAYS_CONDITIONS.get(name, "")
            if condition != allowed:
                problems.append(
                    f"{name}: runs always under {allowed!r}, not {condition!r}"
                )
            continue
        if name not in ci_scope.JOBS:
            problems.append(f"{name}: neither listed as running always nor in the map")
        elif "scope" not in _needs(job) or condition != _condition(name):
            problems.append(f"{name}: does not skip on its own name (if {condition!r})")
    assert problems == []
    assert set(_ALWAYS) <= set(jobs)
    # tests-legs stands for the matrix cells beside the leg that always runs.
    assert set(ci_scope.JOBS) - {"tests-legs"} <= set(jobs)


def test_the_scope_job_reads_both_names_of_a_renamed_file() -> None:
    scope = _jobs()["scope"]
    assert "needs" not in scope
    assert scope["outputs"] == {
        "skip": "${{ steps.scope.outputs.skip }}",
        "tests-exclude": "${{ steps.scope.outputs.tests-exclude }}",
    }
    steps = scope["steps"]
    assert isinstance(steps, list)
    runs = "\n".join(str(step.get("run", "")) for step in steps)
    assert "pulls/$PULL/files" in runs
    assert ".previous_filename // empty" in runs
    assert "python scripts/ci_scope.py < changed.txt" in runs
    # A scope that fails before it writes shows red instead of a green step
    # with an empty answer (which still runs every job).
    assert runs.lstrip().startswith("set -o pipefail")
    # The checkout holds every module the map reads, so a module missing from
    # it is one the change removed.
    checkout = steps[0]["with"]
    assert checkout["sparse-checkout"].split() == ["scripts/**/*.py", "tests/**/*.py"]
