#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A test that reads the repository whole carries a mark, and two jobs leave it out.

``tests/whole_tree.py`` counts the files of the repository each test opens and
fails an unmarked test that opened enough of them to be reading the
repository whole; under ``--without-whole-tree``, which the numba and
dependency-floors jobs pass, it deselects the marked ones. The tests below run
pytest on planted tests in a child process, as those jobs run it, so the
count of the run under test is not this run's own.
"""

from __future__ import annotations

import ast
import os
import subprocess  # nosec B404 - runs this interpreter's pytest
import sys
import textwrap
from pathlib import Path

import pytest
import whole_tree
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW = _ROOT / ".github" / "workflows" / "python-app.yml"

#: A test module that opens *count* modules of the package, through the
#: fixture *scope* names, or in the test itself when it names none.
_READER = """
from pathlib import Path

import pytest

PACKAGE = Path({package!r})


def _read(count):
    files = sorted(PACKAGE.rglob("*.py"))[:count]
    assert len(files) == count
    return [path.read_text(encoding="utf-8") for path in files]
"""


def _run(directory: Path, *options: str) -> subprocess.CompletedProcess[str]:
    """Run pytest on *directory* with this suite's conftest, and its plugins, loaded.

    The short test summary is left out (``-rN``): pytest cuts its lines to the
    terminal width, but prints them whole when ``CI`` is set, so a message the
    tests count would appear once here and twice on CI.
    """
    (directory / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    path = [str(_ROOT / "tests"), *filter(None, [os.environ.get("PYTHONPATH")])]
    return subprocess.run(  # nosec B603 - this interpreter, fixed arguments
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rN",
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


def _plant(directory: Path, name: str, body: str) -> None:
    package = _ROOT / "src" / "phonometry"
    source = _READER.format(package=str(package)) + textwrap.dedent(body)
    (directory / name).write_text(source, encoding="utf-8")


def test_an_unmarked_test_that_reads_the_package_fails(tmp_path: Path) -> None:
    """The class the mark closes: a guard run over the tree, written without it."""
    _plant(
        tmp_path,
        "test_reads.py",
        f"""
        def test_the_tree_passes():
            assert len(_read({whole_tree.LIMIT})) == {whole_tree.LIMIT}
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert f"the test opened {whole_tree.LIMIT} files of the repository" in done.stdout
    assert f"({whole_tree.LIMIT} in src/)" in done.stdout
    assert "carries no whole_tree mark" in done.stdout


def test_an_unmarked_test_that_reads_the_committed_figures_fails(
    tmp_path: Path,
) -> None:
    """The figures under ``.github/`` count: a guard over them reads them whole."""
    images = _ROOT / ".github" / "images"
    (tmp_path / "test_figures.py").write_text(
        textwrap.dedent(
            f"""
            from pathlib import Path


            def test_the_committed_figures_pass():
                figures = sorted(Path({str(images)!r}).rglob("*.svg"))
                figures = figures[:{whole_tree.LIMIT}]
                assert len(figures) == {whole_tree.LIMIT}
                assert all(path.read_bytes() for path in figures)
            """
        ),
        encoding="utf-8",
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert f"({whole_tree.LIMIT} in .github/)" in done.stdout
    assert "carries no whole_tree mark" in done.stdout


def test_a_test_that_reads_fewer_files_than_the_limit_passes(tmp_path: Path) -> None:
    _plant(
        tmp_path,
        "test_reads.py",
        f"""
        def test_a_few_modules():
            assert len(_read({whole_tree.LIMIT - 1})) == {whole_tree.LIMIT - 1}
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.OK, done.stdout + done.stderr


def test_a_read_in_a_module_fixture_counts_for_every_test_that_uses_it(
    tmp_path: Path,
) -> None:
    """The fixture reads once, while the first test sets up; both tests read the tree."""
    _plant(
        tmp_path,
        "test_reads.py",
        f"""
        @pytest.fixture(scope="module")
        def tree():
            return _read({whole_tree.LIMIT})

        def test_first(tree):
            assert tree

        def test_second(tree):
            assert tree
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert "2 failed" in done.stdout
    assert done.stdout.count("carries no whole_tree mark") == 2


def test_a_fixture_set_up_again_counts_what_that_setup_opened(tmp_path: Path) -> None:
    """A module fixture with two parameters is set up once for each: a test
    counts what the setup it was given opened, not what both opened together.

    Both setups added to one set, so the second test of a fixture whose
    setups each opened fewer files than the limit counted both and failed.
    """
    below, at = whole_tree.LIMIT - 1, whole_tree.LIMIT
    _plant(
        tmp_path,
        "test_parameters.py",
        f"""
        def _part(index, count):
            files = sorted(PACKAGE.rglob("*.py"))[index * count : (index + 1) * count]
            assert len(files) == count
            return [path.read_text(encoding="utf-8") for path in files]

        @pytest.fixture(scope="module", params=[0, 1])
        def few(request):
            return _part(request.param, {below})

        @pytest.fixture(scope="module", params=[0, 1])
        def many(request):
            return _part(request.param, {at})

        def test_few(few):
            assert few

        def test_many(many):
            assert many
        """,
    )

    done = _run(tmp_path, "-rA")

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert "2 failed, 2 passed" in done.stdout
    assert "PASSED test_parameters.py::test_few[0]" in done.stdout
    assert "PASSED test_parameters.py::test_few[1]" in done.stdout
    assert done.stdout.count(f"the test opened {at} files of the repository") == 2


def test_a_fixture_asked_for_by_name_or_set_up_inside_another_counts(
    tmp_path: Path,
) -> None:
    """A module fixture a test asks for with ``request.getfixturevalue``,
    once it is set up and again from its cache, or through a fixture that
    asks for it, counts for the test; so does one a module fixture asks for
    in its own setup, for each test that takes that one, and the one a class
    fixture overrides and asks for under its own name, for each test of the
    class.

    The count read the fixtures the test was collected with, each name the
    fixture of the narrowest scope, and a fixture set up inside another's
    setup added what it opened to its own count alone, so each of these
    tests counted none of the files and passed.
    """
    _plant(
        tmp_path,
        "test_asked.py",
        f"""
        @pytest.fixture(scope="module")
        def tree():
            return _read({whole_tree.LIMIT})

        @pytest.fixture
        def wrapped(request):
            return request.getfixturevalue("tree")

        def test_asks(request):
            assert request.getfixturevalue("tree")

        def test_asks_again(request):
            assert request.getfixturevalue("tree")

        def test_through_a_fixture(wrapped):
            assert wrapped

        @pytest.fixture(scope="module")
        def later():
            return _read({whole_tree.LIMIT})

        @pytest.fixture(scope="module")
        def held(request):
            return request.getfixturevalue("later")

        def test_holds(held):
            assert held

        def test_holds_again(held):
            assert held

        class TestOverridden:
            @pytest.fixture(scope="class")
            @classmethod
            def tree(cls, tree):
                return tree

            def test_first(self, tree):
                assert tree

            def test_second(self, tree):
                assert tree
        """,
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.TESTS_FAILED, done.stdout + done.stderr
    assert "7 failed" in done.stdout
    assert done.stdout.count("carries no whole_tree mark") == 7


def test_a_marked_test_passes_and_the_option_leaves_it_out(tmp_path: Path) -> None:
    """Marked one by one or by its module's ``pytestmark``, it is deselected."""
    _plant(
        tmp_path,
        "test_marked.py",
        f"""
        @pytest.mark.whole_tree
        def test_the_tree_passes():
            assert len(_read({whole_tree.LIMIT})) == {whole_tree.LIMIT}

        def test_a_library_test():
            pass
        """,
    )
    _plant(
        tmp_path,
        "test_module_marked.py",
        f"""
        pytestmark = pytest.mark.whole_tree

        def test_the_tree_passes_too():
            assert len(_read({whole_tree.LIMIT})) == {whole_tree.LIMIT}
        """,
    )

    everything = _run(tmp_path)
    left = _run(tmp_path, whole_tree.OPTION, "-rA")

    assert everything.returncode == pytest.ExitCode.OK, everything.stdout
    assert "3 passed" in everything.stdout
    assert left.returncode == pytest.ExitCode.OK, left.stdout + left.stderr
    assert "1 passed, 2 deselected" in left.stdout
    assert "PASSED test_marked.py::test_a_library_test" in left.stdout


def test_the_package_reading_its_own_files_is_not_counted(tmp_path: Path) -> None:
    """The remote runner ships the package's own modules: that is the library at work."""
    (tmp_path / "test_ships.py").write_text(
        textwrap.dedent(
            """
            from phonometry.simulation._remote import package


            def test_the_package_is_shipped():
                assert len(package.installed_package().files) > 100
            """
        ),
        encoding="utf-8",
    )

    done = _run(tmp_path)

    assert done.returncode == pytest.ExitCode.OK, done.stdout + done.stderr


def test_an_import_is_not_a_read_and_a_read_is(tmp_path: Path) -> None:
    """Importing a module opens its source; only a read the test makes counts.

    In a child process, so that its audit hook does not stay in this worker:
    a planted repository whose modules are imported with no bytecode to fall
    back on, then read.
    """
    package = tmp_path / "repository" / "src" / "planted"
    package.mkdir(parents=True)
    for number in range(3):
        (package / f"module_{number}.py").write_text("x = 1\n", encoding="utf-8")
    script = textwrap.dedent(
        """
        import importlib
        import sys
        from pathlib import Path

        import whole_tree

        root = Path(sys.argv[1])
        reads = whole_tree.TreeReads(root)
        sys.addaudithook(reads.audit)
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root / "src"))
        imported, read = set(), set()
        with reads.counting(imported):
            for number in range(3):
                importlib.import_module(f"planted.module_{number}")
        with reads.counting(read):
            for path in sorted((root / "src" / "planted").glob("*.py")):
                path.read_text(encoding="utf-8")
        print(len(imported), sorted(read))
        """
    )
    path = [str(_ROOT / "tests"), *filter(None, [os.environ.get("PYTHONPATH")])]

    done = subprocess.run(  # nosec B603 - this interpreter, fixed arguments
        [sys.executable, "-c", script, str(tmp_path / "repository")],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(path)},
        timeout=120,
        check=True,
        capture_output=True,
        text=True,
    )

    expected = [f"src/planted/module_{number}.py" for number in range(3)]
    assert done.stdout.strip() == f"0 {expected}"


@pytest.mark.parametrize(
    ("nodeid", "key"),
    [
        ("tests/test_x.py::test_y", "tests/test_x.py::test_y"),
        ("tests/test_x.py::test_y[a-b]", "tests/test_x.py::test_y"),
        ("tests/test_x.py::test_y@group", "tests/test_x.py::test_y"),
        ("tests/test_x.py::test_y[a@b]@group", "tests/test_x.py::test_y"),
        ("tests/test_x.py::TestZ::test_y[1]", "tests/test_x.py::TestZ::test_y"),
    ],
)
def test_a_test_is_keyed_by_its_path_and_function(nodeid: str, key: str) -> None:
    assert whole_tree.key(nodeid) == key


def test_every_test_that_runs_the_library_exists_and_says_why() -> None:
    """An entry outliving its test would excuse the next one written under its name."""
    for entry, reason in whole_tree.RUNS_THE_LIBRARY.items():
        assert reason.strip(), entry
        path, *names = entry.split("::")
        module = _ROOT / path
        assert module.is_file(), entry
        body: list[ast.stmt] = ast.parse(module.read_text(encoding="utf-8")).body
        for name in names:
            found = [
                node
                for node in body
                if isinstance(node, ast.FunctionDef | ast.ClassDef)
                and node.name == name
            ]
            assert found, entry
            body = found[0].body


def test_the_numba_and_floors_jobs_leave_the_whole_tree_tests_out() -> None:
    """The two jobs pass the option, and the matrix, which runs these tests, does not."""
    jobs = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"]

    def pytest_commands(job: str) -> list[list[str]]:
        return [
            line.split()
            for step in jobs[job]["steps"]
            for line in str(step.get("run", "")).splitlines()
            if line.strip().startswith("pytest ") and " -n " in line
        ]

    for job in ("tests-perf", "minimum-versions"):
        (command,) = pytest_commands(job)
        assert whole_tree.OPTION in command, job
    (matrix,) = pytest_commands("tests")
    assert whole_tree.OPTION not in matrix
