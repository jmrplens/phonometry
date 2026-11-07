#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The floors the minimum-versions job installs are the ones pyproject declares."""

from __future__ import annotations

import ast
import importlib.util
import itertools
import os
import re
import subprocess  # nosec B404 - runs this interpreter's pytest
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import child_process
import conftest
import node_script
import pinned_stack
import pytest
import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

if TYPE_CHECKING:
    from collections.abc import Collection
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
    """On each supported Python, as pip reads the requirements and their markers."""
    project = _pyproject()["project"]
    assert isinstance(project, dict)
    declared = list(project["dependencies"])
    for extra in project["optional-dependencies"].values():
        declared += extra
    for python in _classified_pythons():
        expected = {}
        for spec in map(Requirement, declared):
            if spec.marker is not None and not spec.marker.evaluate(
                {"python_version": python}
            ):
                continue
            expected[canonicalize_name(spec.name)] = next(
                clause.version for clause in spec.specifier if clause.operator == ">="
            )
        assert _MODULE.floors(_pyproject(), python) == expected, python


def test_a_newer_python_never_has_an_older_floor() -> None:
    """A floor never falls from one Python to the next.

    The first wheel for a newer Python comes later, so two markers swapped by
    mistake fail here. And a release a newer Python happens to tolerate is no
    promise for the Pythons its open marker covers, which nobody has measured.
    """
    pythons = _classified_pythons()
    for older, newer in itertools.pairwise(pythons):
        low = _MODULE.floors(_pyproject(), older)
        high = _MODULE.floors(_pyproject(), newer)
        assert list(low) == list(high)
        lowered = [name for name in low if Version(high[name]) < Version(low[name])]
        assert lowered == [], f"Python {newer} below {older}"


#: Extras ``full`` leaves out, with the reason. torch pulls gigabytes of CUDA
#: wheels from PyPI on Linux, which nobody asking for "everything" for the
#: acoustics expects.
_NOT_IN_FULL = {"torch"}


def test_the_full_extra_names_every_other_extra_at_the_same_floor() -> None:
    """``full`` is the union of the other extras, each at the floor it declares."""
    extras = _pyproject()["project"]["optional-dependencies"]  # type: ignore[index]
    full = set(extras.pop("full"))
    others = {
        spec
        for name, specs in extras.items()
        if name not in _NOT_IN_FULL
        for spec in specs
    }
    assert full == others


def test_every_extra_full_leaves_out_is_declared() -> None:
    """A name in ``_NOT_IN_FULL`` that no extra has would exempt nothing."""
    extras = _pyproject()["project"]["optional-dependencies"]  # type: ignore[index]
    assert _NOT_IN_FULL <= set(extras) - {"full"}


def test_a_requirement_without_a_floor_is_refused() -> None:
    project = _project(dependencies=["numpy"])
    with pytest.raises(ValueError, match="'numpy' is not a floor"):
        _MODULE.floors(project)


def test_an_upper_bound_is_refused() -> None:
    project = _project(dependencies=["numpy>=2.0.2,<3"])
    with pytest.raises(ValueError, match="is not a floor"):
        _MODULE.floors(project)


def test_a_release_excluded_above_the_floor_leaves_the_floor_to_pin() -> None:
    """svglib 1.4.0 stops at a pdb prompt: ``!=1.4.0`` keeps 0.9.1 the floor."""
    project = _project(
        dependencies=["svglib>=0.9.1,!=1.4.0", "lxml >= 5.0, != 5.1 , != 5.2.1"]
    )
    assert _MODULE.floors(project) == {"svglib": "0.9.1", "lxml": "5.0"}


@pytest.mark.parametrize(
    "spec",
    ["svglib>=1.4.0,!=1.4.0", "svglib>=1.4,!=1.4.0", "svglib>=1.4.0,!=1.4"],
)
def test_an_exclusion_of_the_floor_itself_is_refused(spec: str) -> None:
    """The job would install a release the requirement refuses."""
    project = _project(dependencies=[spec])
    with pytest.raises(ValueError, match="excludes its own floor"):
        _MODULE.floors(project)


def test_an_exclusion_below_the_floor_is_refused() -> None:
    """It excludes a release the floor already refuses, so it says nothing."""
    project = _project(dependencies=["svglib>=0.9.1,!=0.9.0"])
    with pytest.raises(ValueError, match="excludes nothing the floor admits"):
        _MODULE.floors(project)


@pytest.mark.parametrize(
    "spec", ["svglib>=0.9.1,!=1.4.*", "svglib>=0.9.1,<2,!=1.4.0", "svglib!=1.4.0"]
)
def test_any_other_clause_beside_the_floor_is_still_refused(spec: str) -> None:
    project = _project(dependencies=[spec])
    with pytest.raises(ValueError, match="is not a floor"):
        _MODULE.floors(project)


def test_two_lists_that_exclude_differently_are_refused() -> None:
    project = _project(
        **{
            "optional-dependencies": {
                "report": ["svglib>=0.9.1,!=1.4.0"],
                "full": ["svglib>=0.9.1"],
            }
        },
    )
    with pytest.raises(ValueError, match="svglib excludes"):
        _MODULE.floors(project)


def test_two_floors_for_one_distribution_are_refused() -> None:
    project = _project(
        dependencies=["numpy>=2.0.2"],
        **{"optional-dependencies": {"full": ["NumPy>=2.1.0"]}},
    )
    with pytest.raises(ValueError, match="numpy has two floors"):
        _MODULE.floors(project)


#: numpy's floors as the package declares them per Python: the oldest release
#: with a wheel for each one.
_NUMPY_PER_PYTHON = [
    "numpy>=2.0.2; python_version<'3.13'",
    "numpy>=2.1.0; python_version=='3.13'",
    "numpy>=2.3.2; python_version>='3.14'",
]


@pytest.mark.parametrize(
    ("python", "floor"),
    [("3.12", "2.0.2"), ("3.13", "2.1.0"), ("3.14", "2.3.2"), ("3.15", "2.3.2")],
)
def test_a_python_version_marker_gives_each_python_its_own_floor(
    python: str, floor: str
) -> None:
    """The last marker is open above, so a newer Python takes the newest floor."""
    project = _project(**{"requires-python": ">=3.12"}, dependencies=_NUMPY_PER_PYTHON)
    assert _MODULE.floors(project, python) == {"numpy": floor}


def test_a_marker_is_read_however_pep_508_lets_it_be_spaced_and_quoted() -> None:
    project = _project(
        **{
            "requires-python": ">=3.12",
            "optional-dependencies": {
                "report": [
                    'svglib >= 0.9.1, != 1.4.0 ; python_version < "3.13"',
                    "svglib>=1.0.0,!=1.4.0;python_version>='3.13'",
                ]
            },
        },
    )
    assert _MODULE.floors(project, "3.12") == {"svglib": "0.9.1"}
    assert _MODULE.floors(project, "3.13") == {"svglib": "1.0.0"}


def test_without_a_python_the_floors_are_the_running_interpreter_s() -> None:
    """What the job installs is what the Python it runs on needs."""
    running = f"{sys.version_info.major}.{sys.version_info.minor}"
    project = _project(**{"requires-python": ">=3.12"}, dependencies=_NUMPY_PER_PYTHON)
    assert _MODULE.floors(project) == _MODULE.floors(project, running)


def test_two_floors_one_python_meets_are_refused() -> None:
    """An unmarked floor and a marked one both hold on 3.13: which one is pinned?"""
    project = _project(
        **{"requires-python": ">=3.12"},
        dependencies=["numpy>=2.0.2", "numpy>=2.1.0; python_version>='3.13'"],
    )
    with pytest.raises(ValueError, match=r"numpy has two floors on Python 3\.13"):
        _MODULE.floors(project, "3.12")


def test_markers_that_leave_a_supported_python_out_are_refused() -> None:
    """On 3.13 the package would ask for no numpy at all."""
    project = _project(
        **{"requires-python": ">=3.12"},
        dependencies=[
            "numpy>=2.0.2; python_version<'3.13'",
            "numpy>=2.3.2; python_version>='3.14'",
        ],
    )
    with pytest.raises(ValueError, match=r"numpy has no floor on Python 3\.13"):
        _MODULE.floors(project, "3.12")


def test_markers_that_leave_out_only_pythons_below_requires_python_are_kept() -> None:
    project = _project(
        **{"requires-python": ">=3.13"},
        dependencies=["numpy>=2.1.0; python_version>='3.13'"],
    )
    assert _MODULE.floors(project, "3.13") == {"numpy": "2.1.0"}


def test_the_newest_marker_has_to_stay_open_above() -> None:
    """A Python newer than every marker names would get no floor."""
    project = _project(
        **{"requires-python": ">=3.12"},
        dependencies=[
            "numpy>=2.0.2; python_version<'3.13'",
            "numpy>=2.1.0; python_version=='3.13'",
        ],
    )
    with pytest.raises(ValueError, match=r"numpy has no floor on Python 3\.14"):
        _MODULE.floors(project, "3.13")


def test_a_python_older_than_requires_python_has_no_floors() -> None:
    project = _project(**{"requires-python": ">=3.12"}, dependencies=_NUMPY_PER_PYTHON)
    with pytest.raises(ValueError, match=r"Python 3\.11 is older than the 3\.12"):
        _MODULE.floors(project, "3.11")


@pytest.mark.parametrize(
    "spec",
    [
        "numpy>=2.0.2; sys_platform == 'linux'",
        "numpy>=2.0.2; python_version<'3.13' and sys_platform=='linux'",
        "numpy>=2.0.2; python_version<'3.13' or python_version>='3.14'",
        "numpy>=2.0.2; python_full_version>='3.13.1'",
        "numpy>=2.0.2; python_version>'3.13'",
        "numpy>=2.0.2; python_version>='3.13.1'",
        "numpy>=2.0.2; python_version>='3.13",
        "numpy>=2.0.2;",
    ],
)
def test_any_marker_but_one_python_version_comparison_is_refused(spec: str) -> None:
    """Only a floor per Python is something the job can pin on each Python."""
    project = _project(**{"requires-python": ">=3.12"}, dependencies=[spec])
    with pytest.raises(ValueError, match="is not a floor"):
        _MODULE.floors(project, "3.13")


def test_the_markers_of_two_lists_have_to_give_one_floor_per_python() -> None:
    """``perf`` and ``full`` both name numba, and each Python reads one floor."""
    project = _project(
        **{
            "requires-python": ">=3.12",
            "optional-dependencies": {
                "perf": [
                    "numba>=0.60.0; python_version<'3.13'",
                    "numba>=0.61.0; python_version>='3.13'",
                ],
                "full": [
                    "numba>=0.60.0; python_version<'3.14'",
                    "numba>=0.63.0; python_version>='3.14'",
                ],
            },
        },
    )
    with pytest.raises(ValueError, match=r"numba has two floors on Python 3\.13"):
        _MODULE.floors(project, "3.12")


def test_an_environment_off_its_floors_is_reported() -> None:
    problems = _MODULE.mismatches({"pytest": "0.0.1", "no-such-distribution": "1.0"})
    assert any(line.startswith("pytest: ") for line in problems)
    assert "no-such-distribution: not installed, the floor is 1.0" in problems


def test_a_local_version_label_is_the_release_it_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """torch from its CPU index installs as ``2.x.y+cpu``, the release ``2.x.y``."""
    installed = {"torch": "2.6.0+cpu", "array-api-compat": "1.12.0"}
    monkeypatch.setattr(_MODULE.metadata, "version", installed.__getitem__)

    assert _MODULE.mismatches({"torch": "2.6.0", "array-api-compat": "1.12.0"}) == []
    assert _MODULE.mismatches({"torch": "2.5.0"}) == [
        "torch: 2.6.0+cpu installed, the floor is 2.5.0"
    ]


def test_check_passes_a_cpu_wheel_at_its_floor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--check`` end to end, as the minimum-versions job runs it."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "x"\ndependencies = ["torch>=2.6.0"]\n', encoding="utf-8"
    )
    monkeypatch.setattr(_MODULE.metadata, "version", {"torch": "2.6.0+cpu"}.__getitem__)

    assert _MODULE.main(["--pyproject", str(pyproject), "--check"]) == 0
    assert capsys.readouterr().out == "OK: 1 distributions at their floors\n"


def test_check_reads_the_floors_of_the_running_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--check`` and the printed pins follow the marker of the interpreter."""
    major, minor = sys.version_info[:2]
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "x"\n'
        'requires-python = ">=3.12"\n'
        "dependencies = [\n"
        f"    \"torch>=1.0.0; python_version<'{major}.{minor}'\",\n"
        f"    \"torch>=2.6.0; python_version=='{major}.{minor}'\",\n"
        f"    \"torch>=9.9.0; python_version>='{major}.{minor + 1}'\",\n"
        "]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_MODULE.metadata, "version", {"torch": "2.6.0+cpu"}.__getitem__)

    assert _MODULE.main(["--pyproject", str(pyproject)]) == 0
    assert capsys.readouterr().out == "torch==2.6.0\n"
    assert _MODULE.main(["--pyproject", str(pyproject), "--check"]) == 0
    assert capsys.readouterr().out == "OK: 1 distributions at their floors\n"


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


def test_the_minimum_job_runs_every_supported_python() -> None:
    """Each Python has floors of its own, and the job installs them on that Python.

    The oldest wheel of numpy, scipy, numba and torch differs from one Python
    to the next, so the floors measured on one prove nothing about another.
    """
    job = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"][
        "minimum-versions"
    ]
    matrix = job["strategy"]["matrix"]["python-version"]
    assert sorted(map(str, matrix), key=_minor) == _classified_pythons()
    versions = {
        str(step["with"]["python-version"])
        for step in job["steps"]
        if "setup-python" in str(step.get("uses", ""))
    }
    assert versions == {"${{ matrix.python-version }}"}


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
        "check_stroke_contrast",
        "clip_frame_audit",
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


@pytest.mark.whole_tree
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


@pytest.mark.whole_tree
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
    tmp_path: Path, pytestconfig: pytest.Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hook reads the mark from the source: the module would raise if imported."""
    tooling, library = _two_modules(tmp_path)

    monkeypatch.setattr(pytestconfig.option, "without_pinned_stack", True)
    assert conftest.pytest_ignore_collect(tooling, pytestconfig) is True
    assert conftest.pytest_ignore_collect(library, pytestconfig) is None
    monkeypatch.setattr(pytestconfig.option, "without_pinned_stack", False)
    assert conftest.pytest_ignore_collect(tooling, pytestconfig) is None


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
        timeout=120,
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
    listed = child_process.run(
        ["git", "ls-files", "-z"],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=120,
    ).stdout.decode("utf-8")
    skip = {".svg", ".png", ".jpg", ".pdf", ".npz", ".wav", ".gz", ".flac", ".webm"}
    return [
        _ROOT / name
        for name in listed.split("\0")
        if name and Path(name).suffix not in skip and name != "CHANGELOG.md"
    ]


#: The tests of the site's scripts, which hand its readers and its checks
#: requirement sentences made up for the case, a floor of another Python and
#: a version longer than the table's among them.
_SITE_SCRIPT_TESTS = ".test.mjs"


@pytest.mark.git_checkout
@pytest.mark.whole_tree
def test_every_statement_of_the_oldest_python_names_requires_python() -> None:
    """Wherever the tree says "Python 3.N or newer", N is the requires-python floor.

    The CHANGELOG is left out: it records what each release needed. So are
    the tests of the site's scripts: what they write is the input of a test,
    not a statement to a reader.
    """
    floor = _MODULE.python_floor(_pyproject())
    wrong = []
    for path in _tracked_text():
        if path.name.endswith(_SITE_SCRIPT_TESTS):
            continue
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


#: The site's files that state the oldest Python, each with the module it
#: reads it from and the name it imports: the landing page writes the floor
#: into its sentences, and astro.config.mjs hands the requirements to the
#: software node. src/data/repo-stats.mjs reads both from pyproject.toml.
_SITE_PYTHON_READERS = {
    "site/src/data/home.ts": ("./repo-stats.mjs", "pythonFloor"),
    "site/astro.config.mjs": ("./src/data/repo-stats.mjs", "softwareRequirements"),
}

#: What src/data/repo-stats.mjs gives the site, as Node imports it.
_SITE_PYTHON = (
    "import { pathToFileURL } from 'node:url';"
    "let input = '';"
    "for await (const chunk of process.stdin) input += chunk;"
    "const stats = await import(pathToFileURL(JSON.parse(input)).href);"
    "process.stdout.write(JSON.stringify("
    "  [stats.pythonFloor, stats.targetPlatform, stats.softwareRequirements]));"
)


@pytest.mark.skipif(
    node_script.NODE is None, reason="no JavaScript engine to ask the site"
)
def test_the_site_reads_the_oldest_python_from_requires_python() -> None:
    """The floor, the platform of the API pages and the software node's
    requirements, as the site's module gives them, state requires-python.

    src/data/repo-stats.mjs reads pyproject.toml with no package of the
    site's, so Node imports it here as the build does.
    """
    floor = _MODULE.python_floor(_pyproject())
    module = _ROOT / "site" / "src" / "data" / "repo-stats.mjs"
    stated, platform, requirements = node_script.answer(
        _SITE_PYTHON, str(module), timeout=60
    )
    assert stated == floor
    assert _stated_floors(str(platform)) == [floor]
    # The sentence opens with the floor; a requirement of its own for a later
    # Python, behind a marker, may name that Python after it.
    assert _stated_floors(str(requirements))[:1] == [floor]


@pytest.mark.parametrize(("name", "reader"), sorted(_SITE_PYTHON_READERS.items()))
def test_the_site_states_the_oldest_python_it_reads_from_pyproject(
    name: str, reader: tuple[str, str]
) -> None:
    """The site's files name no Python of their own: they import it."""
    module, imported = reader
    text = (_ROOT / name).read_text(encoding="utf-8")
    imports = re.findall(r"import \{([^}]*)\} from '([^']+)'", text)
    assert any(
        source == module and imported in re.split(r"[\s,]+", names)
        for names, source in imports
    ), f"{name} does not import {imported} from {module}"
    assert _stated_floors(text) == []


def test_the_landing_page_writes_the_floor_it_imports_in_both_languages() -> None:
    """Each language's install sentence names the floor the page imports."""
    text = (_ROOT / "site" / "src" / "data" / "home.ts").read_text(encoding="utf-8")
    for phrase in (
        "Python ${pythonFloor} or newer",
        "Python ${pythonFloor} o posterior",
    ):
        assert phrase in text, phrase


#: How the installation instructions spell each floored distribution.
_DISPLAY_NAMES = {
    "numpy": "NumPy",
    "scipy": "SciPy",
    "matplotlib": "matplotlib",
    "reportlab": "reportlab",
    "svglib": "svglib",
    "numba": "numba",
    "soundfile": "python-soundfile",
    "torch": "torch",
    "array-api-compat": "array-api-compat",
}


def test_every_floored_distribution_has_a_display_name() -> None:
    assert set(_MODULE.floors(_pyproject())) == set(_DISPLAY_NAMES)


def _names_release(text: str, distribution: str, version: str) -> bool:
    """Whether ``text`` names ``version`` of ``distribution``.

    A release is named when its version stands next to the name of its
    distribution. The version may end a sentence, but not run on into a
    longer one: "torch 2.9.0." names 2.9.0, "torch 2.9.0.1" does not.
    """
    return bool(
        re.search(
            rf"(?<![\w-]){re.escape(_DISPLAY_NAMES[distribution])}\s+"
            rf"{re.escape(version)}(?!\w|\.\w)",
            text,
        )
    )


def _unnamed_floors(text: str, distributions: Collection[str]) -> list[str]:
    """The floors of ``distributions``, on each Python, that ``text`` leaves out."""
    floors = {
        (distribution, version)
        for python in _classified_pythons()
        for distribution, version in _MODULE.floors(_pyproject(), python).items()
        if distribution in distributions
    }
    return [
        f"{_DISPLAY_NAMES[distribution]} {version}"
        for distribution, version in sorted(floors)
        if not _names_release(text, distribution, version)
    ]


@pytest.mark.parametrize("name", _FLOOR_STATEMENTS)
def test_the_installation_instructions_name_every_floor(name: str) -> None:
    """Each floor of each Python stands next to the name of its distribution."""
    text = (_ROOT / name).read_text(encoding="utf-8")
    assert _unnamed_floors(text, _DISPLAY_NAMES) == []


#: The floors whose wheel for their Python serves one platform only, as
#: ``(distribution, Python, floor): (that platform, the first release with a
#: wheel on the others)``, read from the files PyPI lists for each release:
#: torch 2.5.0's one wheel for Python 3.13 is for Linux on x86-64, the platform
#: of the minimum-versions job, and 2.6.0 has one for macOS on ARM, Windows on
#: x86-64 and Linux on ARM as well.
_FLOORS_OF_ONE_PLATFORM = {("torch", "3.13", "2.5.0"): ("x86-64", "2.6.0")}


def test_a_floor_of_one_platform_is_still_the_declared_floor() -> None:
    """Each entry above is a floor pyproject declares, so none outlives its floor."""
    for distribution, python, floor in _FLOORS_OF_ONE_PLATFORM:
        assert _MODULE.floors(_pyproject(), python)[distribution] == floor


@pytest.mark.parametrize("name", _FLOOR_STATEMENTS)
def test_a_floor_of_one_platform_is_stated_with_the_release_the_others_take(
    name: str,
) -> None:
    """A floor with a wheel on one platform names it, and the oldest the others take.

    The instructions call each floor the oldest release with a wheel for its
    Python; for a floor whose wheel serves one platform, that holds there only.
    """
    text = " ".join((_ROOT / name).read_text(encoding="utf-8").split())
    missing = [
        f"{_DISPLAY_NAMES[distribution]} {elsewhere} beside {platform}"
        for (distribution, _, _), (platform, elsewhere) in (
            _FLOORS_OF_ONE_PLATFORM.items()
        )
        if platform not in text or not _names_release(text, distribution, elsewhere)
    ]
    assert missing == []


@pytest.mark.parametrize("name", [*_FLOOR_STATEMENTS, "CHANGELOG.md"])
def test_the_release_the_others_take_is_not_said_to_be_what_pip_installs(
    name: str,
) -> None:
    """The oldest release that installs on the other platforms is not pip's choice.

    pip installs it in neither way it is run: the minimum-versions job pins
    each distribution to its floor, and ``torch==2.5.0`` finds no wheel on
    those platforms, while a plain ``pip install "phonometry[torch]"`` takes
    the newest torch. Only a resolver held at the oldest releases, as
    ``uv pip install --resolution lowest-direct`` is, lands on it. The
    CHANGELOG is read too: its entries for the floors state the same release.
    """
    text = " ".join((_ROOT / name).read_text(encoding="utf-8").split())
    clauses = [
        clause
        for clause in re.split(r"(?<=[.;])\s+", text)
        for (distribution, _, _), (_, elsewhere) in _FLOORS_OF_ONE_PLATFORM.items()
        if _names_release(clause, distribution, elsewhere)
    ]
    assert clauses, f"{name} names no release the other platforms take"
    assert [clause for clause in clauses if re.search(r"\bpip\b", clause)] == []


#: Where the documentation pages are written: the mirror GitHub serves and the
#: site's sources, in both languages.
_DOC_TREES = ("docs", "site/src/content/docs")

#: A table row that says how to install an extra, which group 1 names.
_EXTRA_ROW = re.compile(r'^\|.*`pip install "phonometry\[([\w-]+)\]"`')

#: The rows the test below must find, so that it cannot pass on finding none.
_KNOWN_EXTRA_ROWS = {
    "docs/simulation/compute.md",
    "site/src/content/docs/simulation/compute.mdx",
    "site/src/content/docs/es/simulation/compute.mdx",
}


def _extra_rows_that_name_a_version() -> list[tuple[str, str, set[str]]]:
    """Each table row installing an extra that gives a version of what it brings.

    Each comes as the page, the row and the distributions the extra brings.
    """
    extras = _pyproject()["project"]["optional-dependencies"]  # type: ignore[index]
    brings: dict[str, set[str]] = {
        extra: {canonicalize_name(Requirement(spec).name) for spec in specs}
        for extra, specs in extras.items()
    }
    found: list[tuple[str, str, set[str]]] = []
    for tree in _DOC_TREES:
        for path in sorted((_ROOT / tree).rglob("*.md*")):
            if path.suffix not in {".md", ".mdx"}:
                continue
            for row in path.read_text(encoding="utf-8").splitlines():
                match = _EXTRA_ROW.match(row)
                if match is None or match[1] not in brings:
                    continue
                brought = brings[match[1]]
                if any(
                    re.search(
                        rf"(?<![\w-]){re.escape(_DISPLAY_NAMES[name])}\s+\d+\.\d",
                        row,
                    )
                    for name in brought
                ):
                    found.append((path.relative_to(_ROOT).as_posix(), row, brought))
    return found


@pytest.mark.whole_tree
def test_a_row_that_installs_an_extra_names_its_floors_on_each_python() -> None:
    """A row of ``pip install "phonometry[<extra>]"`` with versions names every floor.

    A row that gives a version of what the extra brings states its floors, so
    it names the floor of each distribution on each Python. Only the row is
    read: the rest of a page can name the releases a bound was measured at.
    """
    rows = _extra_rows_that_name_a_version()
    assert {name for name, _, _ in rows} >= _KNOWN_EXTRA_ROWS
    wrong = [
        f"{name}: {missing}"
        for name, row, brought in rows
        if (missing := _unnamed_floors(row, brought))
    ]
    assert wrong == []


# --------------------------------------------------------------------------
# What a user gets at the floors.

#: A fiche with its figure panel, the path through matplotlib, svglib and
#: reportlab that ``.report()`` takes: the notebook smoke test's ISO 717-1
#: rating.
_FICHE = """
import pathlib
import sys

from phonometry import building

rating = building.weighted_rating(
    [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58]
)
written = pathlib.Path(rating.report(sys.argv[1]))
assert written.read_bytes()[:5] == b"%PDF-", written
"""

#: What rendering the fiche needs beside the package.
_REPORT_STACK = ("matplotlib", "reportlab", "svglib")


@pytest.mark.skipif(
    any(importlib.util.find_spec(name) is None for name in _REPORT_STACK),
    reason="the report and plot extras are not installed",
)
def test_a_fiche_renders_in_a_fresh_interpreter_without_a_warning(
    tmp_path: Path,
) -> None:
    r"""``.report()`` warns nothing, in an interpreter that compiles every module.

    The fiche is rendered under ``-W error`` with a bytecode cache of its own,
    empty, so every module is compiled from its source as on the first import
    after an install that did not precompile, as uv installs. A dependency
    that warns there fails the test: a SyntaxWarning while a module compiles
    (svglib 0.9.0, ``invalid escape sequence '\d'``) as much as a
    DeprecationWarning while one imports (reportlab 4.0.4 to 4.2.5, through
    ``load_module`` and ``ast.NameConstant``). The minimum-versions job runs it
    at the floors of the report extra, so a floor that warns cannot stand.
    """
    done = subprocess.run(  # nosec B603 - this interpreter, fixed arguments
        [
            sys.executable,
            "-W",
            "error",
            "-X",
            f"pycache_prefix={tmp_path / 'pycache'}",
            "-c",
            _FICHE,
            str(tmp_path / "iso717.pdf"),
        ],
        cwd=tmp_path,
        env={**os.environ, "MPLBACKEND": "Agg"},
        # svglib 1.4.0 stops at a pdb prompt, which reads its input here and
        # ends at once rather than waiting on a terminal.
        stdin=subprocess.DEVNULL,
        # Six seconds here, most of it compiling NumPy, SciPy and matplotlib.
        timeout=300,
        check=False,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
