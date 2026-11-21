#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which jobs of Python CI a pull request reaches, from the files it changes.

Python CI (``.github/workflows/python-app.yml``) holds the library on three
systems and three Pythons, at its dependency floors and with its kernel
jitted, and holds every file it generates to its generator. A pull request
that changes only some of what those jobs read cannot move what the others
measure, so each job that can skip names here what reaches it: paths, and the
scripts it runs, each with every module of ``scripts/`` and of ``tests/`` it
imports however deep (the figure and fiche generators import the shared test
fixtures). The ``scope`` job pipes the changed files to this script, which
writes the jobs to skip. A job skips only when it is named, so a scope that
fails or cannot read the change runs everything.

Some jobs run on every pull request, whatever it changes: one leg of the test
suite (its tests read the code, the pages, the edition, the workflows and the
prose alike), lint, the three guard groups (which hold every generated file to
its generator), the release build on Linux and its rebuild on macOS,
SonarCloud and the pull request comment. A change to the library, to what it
is built and pinned with, to the Makefile, or to this workflow, its scripts
and this file reaches every job; so does a file the map does not know, and a
module of ``scripts/`` or ``tests/`` the change deletes or renames, since the
modules left no longer show who imported it. A push to main and a run
dispatched by hand run every job, so a reach drawn too narrow here is caught
on the trunk, not lost.

The answer is written as ``GITHUB_OUTPUT`` lines: ``skip``, the jobs to skip
between commas (``,figures,reports,``), and ``tests-exclude``, the cells of
the test matrix to leave out, a JSON list that is empty unless the other test
legs skip. Standard error says, job by job, which changed file reaches it.
"""

from __future__ import annotations

import ast
import fnmatch
import functools
import itertools
import json
import pathlib
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The directories whose modules import each other by bare name: the scripts
#: put ``scripts/`` on ``sys.path``, pytest puts ``tests/`` there, and the
#: generators put ``tests/`` there to share the test fixtures.
MODULE_ROOTS = ("scripts", "tests")

#: A change to any of these reaches every job: the library, what it is built
#: and pinned with, the Makefile the jobs run their targets from, the
#: workflow, the scripts its steps run, and this scope. A pattern ending in
#: ``/`` is a directory; one with ``*`` matches by wildcard.
EVERY_JOB = (
    "src/",
    "pyproject.toml",
    "requirements*.txt",
    "VERSION",
    "Makefile",
    ".gitattributes",
    ".github/workflows/python-app.yml",
    ".github/scripts/",
    "scripts/ci_scope.py",
)

#: What the suite reads that can behave differently on another system, on
#: another Python or at the dependency floors: the tests and their data, the
#: scripts they exercise, the stub, and the digests, locks and conformance
#: artefact the tests compare against.
SUITE = (
    "tests/",
    "scripts/",
    "stub/",
    "engine-digests.json",
    "gpu-parity.lock",
    "assets.lock",
    "docs/conformance.json",
    "docs/CONFORMANCE.md",
)

#: What the package is built from besides the library, its pins and VERSION
#: (scripts/check_release_artifacts.py lists the sdist's own files).
PACKAGE = (
    "README.md",
    "README_PYPI.md",
    "LICENSE",
    "LICENSES/",
    "MANIFEST.in",
    "stub/",
)

#: The scripts the figures job runs, directly or through ``make graphs``.
FIGURE_SCRIPTS = (
    "generate_graphs",
    "generate_diagrams",
    "check_mathtext",
    "check_decimal_comma",
    "check_figures",
    "check_figure_contrast",
    "check_stroke_contrast",
    "check_figure_language",
    "check_figure_annotations",
    "check_figure_ticks",
    "check_figure_decimal_point",
    "check_figure_legends",
    "check_figure_tick_clearance",
    "check_figure_text_clearance",
    "check_figure_minus_sign",
)


@dataclass(frozen=True)
class Reach:
    """What reaches a job beyond :data:`EVERY_JOB`.

    :param paths: files and directories (ending in ``/``) the job reads.
    :param modules: the modules of ``scripts/`` the job runs; each reaches it
        with every module of :data:`MODULE_ROOTS` it imports.
    """

    paths: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()


#: The jobs that can skip, keyed as python-app.yml keys them; ``tests-legs``
#: stands for the cells of the test matrix beside :data:`DOCS_LEG`.
JOBS: dict[str, Reach] = {
    "tests-legs": Reach(paths=SUITE),
    "tests-perf": Reach(paths=SUITE),
    "minimum-versions": Reach(paths=SUITE),
    # The figure generators draw from the test data and the clips' manifest
    # and fingerprints, not only from the library.
    "figures": Reach(
        paths=(".github/images/", "tests/data/", "assets.lock", "engine-digests.json"),
        modules=FIGURE_SCRIPTS,
    ),
    # The fiche gate reads the pages for the fiches they embed.
    "reports": Reach(
        paths=(".github/reports/", "site/src/content/docs/", "tests/data/"),
        modules=("generate_reports", "check_reports"),
    ),
    # The examples run against the test data some guides load.
    "doc-snippets": Reach(
        paths=(
            "site/src/content/docs/",
            "site/src/data/home.ts",
            "docs/",
            "README.md",
            "README_PYPI.md",
            "llms.txt",
            "tests/data/",
        ),
        modules=("check_doc_snippets",),
    ),
    "built-package": Reach(
        paths=(*PACKAGE, "tests/pyodide/"),
        modules=("build_release", "check_stub_metadata"),
    ),
    # The jobs below run a part of the suite that imports helpers from all
    # over tests/; any change to the tests reaches them, and they take minutes.
    "baseline-glibc": Reach(
        paths=("tests/", "engine-digests.json"), modules=("engine_digests",)
    ),
    "array-api": Reach(paths=("tests/",)),
    "mps": Reach(paths=("tests/",)),
    "remote-node": Reach(paths=("tests/", "docker/")),
    "video": Reach(paths=("tests/",)),
    "notebook": Reach(paths=("tests/notebooks/",), modules=("check_notebook",)),
}

#: What reaches none of :data:`JOBS`: files the jobs that run on every pull
#: request hold (the site, the edition, the prose, the other workflows, the
#: repository's own settings). A file matching nothing here, in
#: :data:`EVERY_JOB` or in a reach is one the map does not know, and runs
#: every job.
NO_JOB = (
    "site/",
    "docs/",
    "paper/",
    ".github/workflows/",
    ".github/ISSUE_TEMPLATE/",
    ".github/DISCUSSION_TEMPLATE/",
    ".github/badges/",
    ".github/brand/",
    ".github/dependabot.yml",
    ".github/FUNDING.yml",
    ".github/labeler.yml",
    ".github/pull_request_template.md",
    ".github/zizmor.yml",
    "hooks/",
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "llms.txt",
    "CITATION.cff",
    ".zenodo.json",
    "codecov.yml",
    "sonar-project.properties",
    ".coderabbit.yaml",
    ".editorconfig",
    ".env.example",
    ".gitignore",
    ".git-blame-ignore-revs",
)

#: The test matrix of python-app.yml, which tests/test_ci_scope.py holds equal
#: to the workflow's.
TEST_OSES = ("ubuntu-26.04", "macos-latest", "windows-latest")
TEST_PYTHONS = ("3.12", "3.13", "3.14")

#: The leg every pull request runs: the one whose coverage and test results
#: SonarCloud and the pull request comment read.
DOCS_LEG = ("ubuntu-26.04", "3.13")

#: The most files the pull request files API lists; a list this long may be
#: cut, so it is never taken for the whole change.
API_FILE_LIMIT = 3000


def matches(path: str, pattern: str) -> bool:
    """Whether *path* is *pattern*, lies under it, or matches its wildcards."""
    if pattern.endswith("/"):
        return path.startswith(pattern)
    return fnmatch.fnmatchcase(path, pattern)


def _modules() -> dict[str, list[pathlib.Path]]:
    """Each module of :data:`MODULE_ROOTS` by name, with the files it holds.

    A module is a file or a package; a name the standard library holds is
    never one of ours, whatever a directory is called.
    """
    found: dict[str, list[pathlib.Path]] = {}
    for root in MODULE_ROOTS:
        base = ROOT / root
        for path in sorted(base.glob("*.py")):
            found.setdefault(path.stem, []).append(path)
        for path in sorted(base.iterdir()):
            if path.is_dir() and (path / "__init__.py").is_file():
                found.setdefault(path.name, []).extend(sorted(path.rglob("*.py")))
    return {
        name: files
        for name, files in found.items()
        if name not in sys.stdlib_module_names
    }


def _imported(path: pathlib.Path) -> set[str]:
    """The top-level names the file at *path* imports by absolute name."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    return names


def module_closure(entries: Iterable[str]) -> list[pathlib.Path]:
    """The files of *entries* and of every module they import, however deep."""
    modules = _modules()
    missing = sorted(set(entries) - set(modules))
    if missing:
        msg = f"no such module in {' or '.join(MODULE_ROOTS)}: {', '.join(missing)}"
        raise ValueError(msg)
    seen: set[str] = set()
    todo = list(entries)
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        for path in modules[name]:
            todo.extend((_imported(path) & set(modules)) - seen)
    return sorted({path for name in seen for path in modules[name]})


def reach_patterns(reach: Reach) -> tuple[str, ...]:
    """Every pattern that reaches a job: its paths and its modules' files."""
    files = (
        path.relative_to(ROOT).as_posix() for path in module_closure(reach.modules)
    )
    return (*reach.paths, *files)


@functools.cache
def job_patterns() -> dict[str, tuple[str, ...]]:
    """The patterns of every job of :data:`JOBS`, read from the checkout once."""
    return {job: reach_patterns(reach) for job, reach in JOBS.items()}


def _gone_module(path: str) -> bool:
    """Whether *path* is a module of :data:`MODULE_ROOTS` the change removed."""
    return (
        path.endswith(".py")
        and path.startswith(tuple(f"{root}/" for root in MODULE_ROOTS))
        and not (ROOT / path).is_file()
    )


def reached(paths: Sequence[str]) -> dict[str, list[str]] | None:
    """The changed files that reach each job of :data:`JOBS`.

    ``None`` when every job runs: no path at all (the list could not be
    fetched), a list as long as the API's limit, a path that reaches every
    job, a path the map does not know, or a removed module.
    """
    if not paths or len(paths) >= API_FILE_LIMIT:
        return None
    if any(matches(path, pattern) for path in paths for pattern in EVERY_JOB):
        return None
    if any(_gone_module(path) for path in paths):
        return None
    patterns = job_patterns()
    known = [*NO_JOB, *itertools.chain.from_iterable(patterns.values())]
    if not all(any(matches(path, pattern) for pattern in known) for path in paths):
        return None
    return {
        job: [path for path in paths if any(matches(path, p) for p in own)]
        for job, own in patterns.items()
    }


def jobs_to_skip(paths: Sequence[str]) -> list[str]:
    """The jobs of :data:`JOBS` that no file of *paths* reaches."""
    reach = reached(paths)
    if reach is None:
        return []
    return [job for job, files in reach.items() if not files]


def tests_exclude(skip: Iterable[str]) -> list[dict[str, str]]:
    """The cells of the test matrix to leave out when the other legs skip."""
    if "tests-legs" not in set(skip):
        return []
    return [
        {"os": os_name, "python-version": python}
        for os_name, python in itertools.product(TEST_OSES, TEST_PYTHONS)
        if (os_name, python) != DOCS_LEG
    ]


def explain(paths: Sequence[str]) -> str:
    """One line per job: whether it runs, and the first changed file reaching it."""
    reach = reached(paths)
    if reach is None:
        return "every job runs\n"
    lines = []
    for job, files in reach.items():
        if not files:
            lines.append(f"{job}: skips")
        else:
            more = f" and {len(files) - 1} more" if len(files) > 1 else ""
            lines.append(f"{job}: runs ({files[0]}{more})")
    return "\n".join(lines) + "\n"


def outputs(lines: Iterable[str]) -> str:
    """The ``GITHUB_OUTPUT`` lines for the changed files read from *lines*."""
    paths = [line.strip() for line in lines if line.strip()]
    skip = jobs_to_skip(paths)
    exclude = json.dumps(tests_exclude(skip), separators=(",", ":"))
    named = "," + ",".join(skip) + "," if skip else ""
    return f"skip={named}\ntests-exclude={exclude}\n"


def main() -> int:
    """Read the changed files from standard input, write the answer out."""
    try:
        paths = [line.strip() for line in sys.stdin if line.strip()]
        answer = outputs(paths)
        reasons = explain(paths)
    # Any doubt runs every job: a scope that cannot be read is no scope.
    except Exception as error:  # noqa: BLE001
        print(f"::warning::ci_scope: {error}; running every job", file=sys.stderr)
        answer, reasons = outputs([]), explain([])
    sys.stderr.write(reasons)
    sys.stdout.write(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
