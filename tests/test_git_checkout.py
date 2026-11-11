#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A test that asks git about the repository carries a mark, and a source archive skips it.

``tests/git_checkout.py`` notes the git commands each test runs on the
repository and fails an unmarked test that ran one; where the repository has
no ``.git``, as a source archive unpacks, it skips the marked tests. The
tests below run pytest on planted tests in a child process, so the record of
the run under test is not this run's own. The planted tests that ask git
about the repository do it in that child process, which the check does not
see, so the tests that plant them carry the mark themselves.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess  # nosec B404 - runs this interpreter's pytest
import sys
import textwrap
from pathlib import Path

import git_checkout
import pytest

_ROOT = Path(__file__).resolve().parent.parent

#: The check reads the arguments of the ``subprocess.Popen`` audit event,
#: which Windows gives as one command line, so there it reads none.
_ARGUMENTS_READ = pytest.mark.skipif(
    sys.platform == "win32",
    reason="on Windows the audit event carries one command line, which the check leaves unread",
)

#: What a planted test module starts with: the repository, and git run on it.
_HEAD = """
import subprocess
from pathlib import Path

import pytest

ROOT = Path({root!r})


def _git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, timeout=60
    )
"""


def _run(directory: Path, *options: str) -> subprocess.CompletedProcess[str]:
    """Run pytest on *directory* with this suite's conftest, and its plugins, loaded."""
    (directory / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    path = [str(_ROOT / "tests"), *filter(None, [os.environ.get("PYTHONPATH")])]
    return subprocess.run(  # nosec B603 - this interpreter, fixed arguments
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rs",
            "-n",
            "0",
            "-p",
            "no:cacheprovider",
            "-p",
            "conftest",
            "-c",
            str(directory / "pytest.ini"),
            "--rootdir",
            str(directory),
            *options,
            str(directory),
        ],
        cwd=directory,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(path)},
        timeout=300,
        check=False,
        capture_output=True,
        text=True,
    )


def _plant(directory: Path, body: str, root: Path = _ROOT) -> None:
    source = _HEAD.format(root=str(root)) + textwrap.dedent(body)
    (directory / "test_planted.py").write_text(source, encoding="utf-8")


@pytest.mark.git_checkout
@_ARGUMENTS_READ
def test_an_unmarked_test_that_lists_the_tracked_files_fails(tmp_path: Path) -> None:
    """The class the mark closes: a test of a git-backed helper, written without it."""
    _plant(
        tmp_path,
        """
        def test_the_tracked_files():
            assert _git("-C", str(ROOT), "ls-files", "-z").stdout
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert "the test ran git on the repository" in done.stdout
    assert "(git -C <repository> ls-files -z)" in done.stdout
    assert "carries no git_checkout mark" in done.stdout


@pytest.mark.git_checkout
@_ARGUMENTS_READ
def test_git_run_from_the_repository_counts_as_asking_it(tmp_path: Path) -> None:
    """No ``-C``: git starts in the working directory, here the repository's."""
    _plant(
        tmp_path,
        """
        def test_the_head_commit():
            assert _git("log", "-1", "--format=%H", cwd=ROOT).stdout
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert "(git log -1 --format=%H)" in done.stdout


@pytest.mark.git_checkout
@_ARGUMENTS_READ
def test_a_git_run_in_a_module_fixture_counts_for_every_test_that_uses_it(
    tmp_path: Path,
) -> None:
    """The fixture runs git once, while the first test sets up; both tests ask."""
    _plant(
        tmp_path,
        """
        @pytest.fixture(scope="module")
        def tracked():
            return _git("-C", str(ROOT), "ls-files", "-z").stdout

        def test_first(tracked):
            assert tracked

        def test_second(tracked):
            assert tracked
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert "2 failed" in done.stdout
    assert done.stdout.count("carries no git_checkout mark") == 2


@pytest.mark.git_checkout
def test_a_marked_test_passes_and_a_git_of_no_repository_needs_no_mark(
    tmp_path: Path,
) -> None:
    """Marked one by one or by its module's ``pytestmark``; ``git --version`` asks nothing."""
    _plant(
        tmp_path,
        """
        @pytest.mark.git_checkout
        def test_the_tracked_files():
            assert _git("-C", str(ROOT), "ls-files", "-z").stdout

        def test_the_git_version():
            assert _git("--version", cwd=ROOT).stdout.startswith("git version")
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.OK, done.stdout + done.stderr
    assert "2 passed" in done.stdout


def test_a_repository_of_the_tests_own_needs_no_mark(tmp_path: Path) -> None:
    """``git init`` started from the repository makes another one, and asks this one nothing."""
    planted = tmp_path / "planted"
    planted.mkdir()
    _plant(
        planted,
        """
        def test_its_own_repository(tmp_path):
            _git("init", "-q", str(tmp_path), cwd=ROOT)
            (tmp_path / "page.md").write_text("text\\n", encoding="utf-8")
            _git("-C", str(tmp_path), "add", "page.md")
            assert _git("-C", str(tmp_path), "ls-files").stdout == "page.md\\n"
        """,
    )

    done = _run(planted)

    assert done.returncode == pytest.ExitCode.OK, done.stdout + done.stderr


def test_a_tree_with_no_git_skips_the_marked_tests_and_says_why(tmp_path: Path) -> None:
    """A copy of the plugins in a tree with no ``.git``, as a source archive unpacks."""
    tree = tmp_path / "tree"
    (tree / "tests").mkdir(parents=True)
    shutil.copy(_ROOT / "tests" / "git_checkout.py", tree / "tests" / "git_checkout.py")
    (tree / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    git_checkout: needs a git checkout\n",
        encoding="utf-8",
    )
    (tree / "tests" / "test_planted.py").write_text(
        textwrap.dedent(
            """
            import pytest


            @pytest.mark.git_checkout
            def test_asks_git():
                pass


            def test_asks_nothing():
                pass
            """
        ),
        encoding="utf-8",
    )

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # nosec B603 - this interpreter, fixed arguments
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-rs",
                "-p",
                "no:cacheprovider",
                "-p",
                "git_checkout",
                "-c",
                str(tree / "pytest.ini"),
                "--rootdir",
                str(tree),
                str(tree / "tests"),
            ],
            cwd=tree,
            env={**os.environ, "PYTHONPATH": str(tree / "tests")},
            timeout=300,
            check=False,
            capture_output=True,
            text=True,
        )

    archive = run()
    (tree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    checkout = run()

    assert archive.returncode == pytest.ExitCode.OK, archive.stdout + archive.stderr
    assert "1 passed, 1 skipped" in archive.stdout
    assert git_checkout.NOT_A_CHECKOUT in archive.stdout
    assert checkout.returncode == pytest.ExitCode.OK, checkout.stdout + checkout.stderr
    assert "2 passed" in checkout.stdout


@pytest.mark.parametrize(
    ("argv", "cwd", "env", "asked"),
    [
        (["git", "-C", "{root}", "ls-files"], "{elsewhere}", {}, ["{root}"]),
        (
            ["git", "-C", "{root}", "-C", "src", "ls-files"],
            "{elsewhere}",
            {},
            ["{root}"],
        ),
        (["git", "ls-files"], "{root}/src", {}, ["{root}"]),
        (["git", "-c", "user.name=x", "status"], "{root}", {}, ["{root}"]),
        (["git", "--git-dir={root}/.git", "log"], "{elsewhere}", {}, ["{root}"]),
        (["git", "--git-dir", "{root}/.git", "log"], "{elsewhere}", {}, ["{root}"]),
        (["git", "log"], "{elsewhere}", {"GIT_DIR": "{root}/.git"}, ["{root}"]),
        (["git", "clone", "-q", "{root}", "copy"], "{elsewhere}", {}, ["{root}"]),
        (["git", "clone", "https://example.org/x.git"], "{root}", {}, []),
        (["git", "init", "-q", "{elsewhere}"], "{root}", {}, []),
        (["git", "--version"], "{root}", {}, []),
        (["git", "-C", "{elsewhere}", "status"], "{root}", {}, []),
    ],
)
def test_the_repository_a_git_command_asks_about(
    tmp_path: Path, argv: list[str], cwd: str, env: dict[str, str], asked: list[str]
) -> None:
    """The ``-C`` chain, ``--git-dir``, ``GIT_DIR``, ``clone``'s source and the commands that ask nothing."""
    root = tmp_path / "root"
    (root / "src").mkdir(parents=True)
    (root / ".git").mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    def fill(text: str) -> str:
        return text.format(root=root, elsewhere=elsewhere)

    got = git_checkout.asked_about(
        [fill(word) for word in argv],
        fill(cwd),
        {key: fill(value) for key, value in env.items()},
    )

    assert got == [Path(fill(path)).resolve() for path in asked]


def test_a_checkout_has_a_git_directory_or_file(tmp_path: Path) -> None:
    """A clone holds ``.git`` as a directory, a linked worktree as a file."""
    clone, worktree, archive = (
        tmp_path / name for name in ("clone", "worktree", "archive")
    )
    for directory in (clone, worktree, archive):
        directory.mkdir()
    (clone / ".git").mkdir()
    (worktree / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    assert git_checkout.is_a_checkout(clone)
    assert git_checkout.is_a_checkout(worktree)
    assert not git_checkout.is_a_checkout(archive)


def test_a_helper_that_takes_the_refusal_as_an_answer_needs_no_mark(
    tmp_path: Path,
) -> None:
    """``generate_llms`` lists what git ignores, and a refusal is an empty list."""
    _plant(
        tmp_path,
        f"""
        import sys

        sys.path.insert(0, {str(_ROOT / "scripts")!r})

        import generate_llms


        def test_the_ignored_files():
            assert isinstance(generate_llms._ignored_paths(), frozenset)
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.OK, done.stdout + done.stderr


def test_a_process_is_charged_to_the_code_that_started_it() -> None:
    """The first frame outside ``subprocess``, the suite's runner and the plugin."""

    def start() -> str | None:
        return git_checkout.started_by(sys._getframe(0))

    assert start() == (
        "tests/test_git_checkout.py::"
        "test_a_process_is_charged_to_the_code_that_started_it.<locals>.start"
    )


def test_every_tolerated_helper_exists_and_says_why() -> None:
    """An entry outliving its helper would excuse the next one written under its name."""
    for entry, reason in git_checkout.TOLERATES_NO_CHECKOUT.items():
        assert reason.strip(), entry
        path, qualname = entry.split("::")
        module = _ROOT / path
        assert module.is_file(), entry
        body: list[ast.stmt] = ast.parse(module.read_text(encoding="utf-8")).body
        for name in qualname.split("."):
            found = [
                node
                for node in body
                if isinstance(node, ast.FunctionDef | ast.ClassDef)
                and node.name == name
            ]
            assert found, entry
            body = found[0].body
