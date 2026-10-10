#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The floors the minimum-versions job installs are the ones pyproject declares."""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import subprocess  # nosec B404 - runs this interpreter's pytest
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import conftest
import pinned_stack
import pytest
import yaml

if TYPE_CHECKING:
    from types import ModuleType

_ROOT = Path(__file__).resolve().parent.parent
_WORKFLOW = _ROOT / ".github" / "workflows" / "python-app.yml"


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "minimum_requirements", _ROOT / "scripts" / "minimum_requirements.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["minimum_requirements"] = module
    spec.loader.exec_module(module)
    return module


_MODULE = _module()


def _pyproject() -> dict[str, object]:
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def _project(**fields: object) -> dict[str, object]:
    return {"project": dict(fields)}


def test_every_declared_requirement_is_pinned_at_its_floor() -> None:
    project = _pyproject()["project"]
    assert isinstance(project, dict)
    declared = list(project["dependencies"])
    for extra in project["optional-dependencies"].values():
        declared += extra
    pinned = _MODULE.floors(_pyproject())
    for spec in declared:
        name, version = re.split(r"\s*>=\s*", spec)
        assert pinned[_MODULE._normalise(name)] == version


def test_the_full_extra_names_every_other_extra_at_the_same_floor() -> None:
    """``full`` is the union of the other extras, each at the floor it declares."""
    extras = _pyproject()["project"]["optional-dependencies"]  # type: ignore[index]
    full = set(extras.pop("full"))
    others = {spec for specs in extras.values() for spec in specs}
    assert full == others


def test_a_requirement_without_a_floor_is_refused() -> None:
    project = _project(dependencies=["numpy"])
    with pytest.raises(ValueError, match="'numpy' is not a floor"):
        _MODULE.floors(project)


def test_an_upper_bound_is_refused() -> None:
    project = _project(dependencies=["numpy>=2.0.2,<3"])
    with pytest.raises(ValueError, match="is not a floor"):
        _MODULE.floors(project)


def test_two_floors_for_one_distribution_are_refused() -> None:
    project = _project(
        dependencies=["numpy>=2.0.2"],
        **{"optional-dependencies": {"full": ["NumPy>=2.1.0"]}},
    )
    with pytest.raises(ValueError, match="numpy has two floors"):
        _MODULE.floors(project)


def test_an_environment_off_its_floors_is_reported() -> None:
    problems = _MODULE.mismatches({"pytest": "0.0.1", "no-such-distribution": "1.0"})
    assert any(line.startswith("pytest: ") for line in problems)
    assert "no-such-distribution: not installed, the floor is 1.0" in problems


def test_dependabot_moves_the_pins_and_leaves_the_floors() -> None:
    """``increase`` would rewrite every floor to the release it bumps to.

    The weekly grouped pull request would then raise the floors with no
    failure measured at them; ``increase-if-necessary`` moves an exact pin,
    which never admits the new release, and leaves a floor that does.
    """
    config = yaml.safe_load(
        (_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    )
    pip = [u for u in config["updates"] if u["package-ecosystem"] == "pip"]
    assert pip
    assert {u.get("versioning-strategy") for u in pip} == {"increase-if-necessary"}


def test_the_minimum_job_runs_the_oldest_supported_python() -> None:
    """The job pins the interpreter requires-python names, not another one."""
    floor = _MODULE.python_floor(_pyproject())
    jobs = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    steps = jobs["minimum-versions"]["steps"]
    versions = {
        str(step["with"]["python-version"])
        for step in steps
        if "setup-python" in str(step.get("uses", ""))
    }
    assert versions == {floor}


def _minor(version: str) -> int:
    major, minor = map(int, version.split("."))
    assert major == 3, version
    return minor


def _classified_pythons() -> list[str]:
    """The ``Programming Language :: Python :: 3.N`` classifiers, oldest first."""
    project = _pyproject()["project"]
    assert isinstance(project, dict)
    named = {
        c.rsplit(" :: ", 1)[1]
        for c in project["classifiers"]
        if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", c)
    }
    return sorted(named, key=_minor)


def test_the_classifiers_name_every_supported_python_and_no_older() -> None:
    """From the requires-python floor to the newest one named, with no gap."""
    floor = _MODULE.python_floor(_pyproject())
    named = _classified_pythons()
    expected = [f"3.{minor}" for minor in range(_minor(floor), _minor(named[-1]) + 1)]
    assert named == expected


def test_the_analysers_judge_the_code_for_every_supported_python() -> None:
    """ruff and mypy read the oldest Python, SonarCloud every supported one.

    A rule that depends on the Python version (a construct the oldest one
    lacks, a deprecation a newer one brings) is only applied for the versions
    each tool is told about.
    """
    floor = _MODULE.python_floor(_pyproject())
    tools = _pyproject()["tool"]
    assert isinstance(tools, dict)
    assert tools["ruff"]["target-version"] == "py" + floor.replace(".", "")
    assert tools["mypy"]["python_version"] == floor
    properties = dict(
        line.split("=", 1)
        for line in (_ROOT / "sonar-project.properties")
        .read_text(encoding="utf-8")
        .splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    )
    sonar = [v.strip() for v in properties["sonar.python.version"].split(",")]
    assert sonar == _classified_pythons()


def test_the_test_matrix_runs_every_supported_python() -> None:
    """Each Python the classifiers name is tested, and no other one."""
    matrix = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"]["tests"][
        "strategy"
    ]["matrix"]
    assert sorted(map(str, matrix["python-version"]), key=_minor) == (
        _classified_pythons()
    )


#: The development tooling whose output is tied to the pinned figure stack.
_PINNED_TOOLING = frozenset(
    {
        "animation_fingerprint",
        "conformance_badges",
        "diagrams",
        "figure_annotation_audit",
        "figure_language_audit",
        "figure_tick_audit",
        "figures",
        "generate_diagrams",
        "generate_graphs",
        "glyph_census",
        "process_exit",
    }
)


def _imported_tooling(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return {
        name
        for name in names
        if name in _PINNED_TOOLING or name.startswith("check_figure_")
    }


def test_every_module_testing_the_figure_tooling_is_kept_off_the_floors() -> None:
    """A test of the figure or diagram tooling carries the ``pinned_stack`` mark.

    Without it the minimum-versions job would run the module on the floor
    matplotlib, where the generators and checkers it exercises were never
    meant to run, and fail for a reason that says nothing about the library.
    """
    unmarked = []
    for path in sorted((_ROOT / "tests").rglob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        if _imported_tooling(ast.parse(source)) and not pinned_stack.declares(source):
            unmarked.append(path.relative_to(_ROOT).as_posix())
    assert unmarked == []


def _marks_pinned_stack(tree: ast.Module) -> bool:
    """Whether the module applies the mark anywhere, as ``pytestmark`` or a decorator."""
    return any(
        isinstance(node, ast.Attribute)
        and node.attr == pinned_stack.MARK
        and ast.unparse(node.value) == "pytest.mark"
        for node in ast.walk(tree)
    )


def test_only_a_module_testing_the_figure_tooling_is_kept_off_the_floors() -> None:
    """The converse: the mark leaves a test out of the minimum-versions job.

    A library test that carried it would stop running at the floors, which is
    the one place it is there to be run, and nothing would say so.
    """
    marked_without_tooling = []
    for path in sorted((_ROOT / "tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _marks_pinned_stack(tree) and not _imported_tooling(tree):
            marked_without_tooling.append(path.relative_to(_ROOT).as_posix())
    assert marked_without_tooling == []


def test_the_minimum_job_leaves_the_pinned_stack_tests_out() -> None:
    """The job runs pytest with the option, so the mark is what decides."""
    steps = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"][
        "minimum-versions"
    ]["steps"]
    commands = [
        line.strip()
        for step in steps
        for line in str(step.get("run", "")).splitlines()
        if line.strip().startswith("pytest ")
    ]
    assert len(commands) == 1
    assert pinned_stack.OPTION in commands[0].split()


@pytest.mark.parametrize(
    ("declaration", "declared"),
    [
        ("pytestmark = pytest.mark.pinned_stack", True),
        ("pytestmark = [pytest.mark.slow, pytest.mark.pinned_stack]", True),
        ("pytestmark: object = pytest.mark.pinned_stack", True),
        ("pytestmark = pytest.mark.slow", False),
        ("marks = pytest.mark.pinned_stack", False),
        ("# pytestmark = pytest.mark.pinned_stack", False),
    ],
)
def test_the_declaration_is_read_from_the_module_level_pytestmark(
    declaration: str, *, declared: bool
) -> None:
    assert pinned_stack.declares(f"import pytest\n{declaration}\n") is declared


def _options(*, without_pinned_stack: bool) -> SimpleNamespace:
    return SimpleNamespace(
        getoption=lambda name: {"without_pinned_stack": without_pinned_stack}[name]
    )


def _two_modules(directory: Path) -> tuple[Path, Path]:
    """A tooling module that fails on import, as at the floors, and a library one."""
    tooling = directory / "test_tooling.py"
    tooling.write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.pinned_stack\n"
        "raise ImportError('a name only the pinned stack has')\n",
        encoding="utf-8",
    )
    library = directory / "test_library.py"
    library.write_text("def test_it() -> None:\n    pass\n", encoding="utf-8")
    return tooling, library


def test_a_pinned_stack_module_is_left_out_before_it_is_imported(
    tmp_path: Path,
) -> None:
    """The hook reads the mark from the source: the module would raise if imported."""
    tooling, library = _two_modules(tmp_path)
    on, off = _options(without_pinned_stack=True), _options(without_pinned_stack=False)

    assert conftest.pytest_ignore_collect(tooling, on) is True  # type: ignore[arg-type]
    assert conftest.pytest_ignore_collect(library, on) is None  # type: ignore[arg-type]
    assert conftest.pytest_ignore_collect(tooling, off) is None  # type: ignore[arg-type]


def _collect(directory: Path, *options: str) -> subprocess.CompletedProcess[str]:
    """Collect *directory* with this suite's conftest loaded as a plugin."""
    (directory / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    path = [str(_ROOT / "tests"), *filter(None, [os.environ.get("PYTHONPATH")])]
    return subprocess.run(  # nosec B603 - this interpreter, fixed arguments
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
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
        check=False,
        capture_output=True,
        text=True,
    )


def test_with_the_option_pytest_never_imports_a_pinned_stack_module(
    tmp_path: Path,
) -> None:
    """End to end, the way the job collects: a directory, not a list of files."""
    _two_modules(tmp_path)

    done = _collect(tmp_path, pinned_stack.OPTION)

    assert done.returncode == 0, done.stdout + done.stderr
    assert "test_library.py::test_it" in done.stdout
    assert "test_tooling" not in done.stdout + done.stderr


def test_without_the_option_the_same_module_is_a_collection_error(
    tmp_path: Path,
) -> None:
    """The counterpart: a mark alone does not keep the import from failing."""
    _two_modules(tmp_path)

    done = _collect(tmp_path, "-m", f"not {pinned_stack.MARK}")

    assert done.returncode == pytest.ExitCode.INTERRUPTED, done.stdout + done.stderr
    assert "ImportError" in done.stdout


# --------------------------------------------------------------------------
# What the documentation says the package needs.

#: A sentence that states the oldest Python, in either language.
_PYTHON_FLOOR_PHRASE = re.compile(
    r"Python (3\.\d+) (?:or newer|o posterior)|Python >= ?(3\.\d+)"
)


def _stated_floors(text: str) -> list[str]:
    return [a or b for a, b in _PYTHON_FLOOR_PHRASE.findall(text)]


#: Where a reader learns which Python the package needs; each must say it.
_PYTHON_STATEMENTS = (
    "README.md",
    "README_PYPI.md",
    ".zenodo.json",
    "llms.txt",
    "docs/start/getting-started.md",
    "docs/start/index.md",
    "site/src/content/docs/start/getting-started.mdx",
    "site/src/content/docs/es/start/getting-started.mdx",
    "site/src/content/docs/start/index.md",
    "site/src/content/docs/es/start/index.md",
    "site/src/data/home.ts",
    "site/astro.config.mjs",
)

#: The installation instructions, which name every floor.
_FLOOR_STATEMENTS = (
    "README.md",
    "README_PYPI.md",
    "docs/start/getting-started.md",
    "site/src/content/docs/start/getting-started.mdx",
    "site/src/content/docs/es/start/getting-started.mdx",
)


def _tracked_text() -> list[Path]:
    listed = subprocess.run(  # nosec B603 B607 - git on this checkout
        ["git", "ls-files", "-z"],
        cwd=_ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    skip = {".svg", ".png", ".jpg", ".pdf", ".npz", ".wav", ".gz", ".flac", ".webm"}
    return [
        _ROOT / name
        for name in listed.split("\0")
        if name and Path(name).suffix not in skip and name != "CHANGELOG.md"
    ]


def test_every_statement_of_the_oldest_python_names_requires_python() -> None:
    """Wherever the tree says "Python 3.N or newer", N is the requires-python floor.

    The CHANGELOG is left out: it records what each release needed.
    """
    floor = _MODULE.python_floor(_pyproject())
    wrong = []
    for path in _tracked_text():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        wrong += [
            f"{path.relative_to(_ROOT).as_posix()}: Python {found}"
            for found in _stated_floors(text)
            if found != floor
        ]
    assert wrong == []


@pytest.mark.parametrize("name", _PYTHON_STATEMENTS)
def test_the_pages_a_reader_installs_from_state_the_oldest_python(name: str) -> None:
    floor = _MODULE.python_floor(_pyproject())
    text = (_ROOT / name).read_text(encoding="utf-8")
    assert floor in _stated_floors(text)


#: How the installation instructions spell each floored distribution.
_DISPLAY_NAMES = {
    "numpy": "NumPy",
    "scipy": "SciPy",
    "matplotlib": "matplotlib",
    "reportlab": "reportlab",
    "svglib": "svglib",
    "numba": "numba",
    "soundfile": "python-soundfile",
}


def test_every_floored_distribution_has_a_display_name() -> None:
    assert set(_MODULE.floors(_pyproject())) == set(_DISPLAY_NAMES)


@pytest.mark.parametrize("name", _FLOOR_STATEMENTS)
def test_the_installation_instructions_name_every_floor(name: str) -> None:
    """Each floor stands next to the name of its distribution, not just anywhere."""
    text = (_ROOT / name).read_text(encoding="utf-8")
    missing = [
        f"{_DISPLAY_NAMES[distribution]} {version}"
        for distribution, version in _MODULE.floors(_pyproject()).items()
        if not re.search(
            rf"(?<![\w-]){re.escape(_DISPLAY_NAMES[distribution])}\s+"
            rf"{re.escape(version)}(?![\w.])",
            text,
        )
    ]
    assert missing == []
