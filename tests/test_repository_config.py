#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The repository's own configuration, checked against what it describes.

Three files here make claims about other files, and nothing compiled them, so
they can be wrong for as long as nobody rereads them. ``.coderabbit.yaml``
tells the review bot which pages under ``docs/`` are build output, and the bot
will act on that by rejecting a hand edit CI actually requires. The docs
workflow lists the paths that make the site rebuild, and the site build is
where the citation guards live, so a root file the build reads and the trigger
omits is a guard that cannot fail on the pull request that breaks it. And a
comment in the Python workflow quotes a dependency floor that lives in
``pyproject.toml``.

Each test below derives the truth from the thing being described rather than
from a second copy of the claim.
"""

from __future__ import annotations

import builtins
import pathlib
import re
import shlex
import sys
import tomllib
from typing import TYPE_CHECKING

import child_process
import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mirror_overviews

_CODERABBIT = _ROOT / ".coderabbit.yaml"
_DOCS_WORKFLOW = _ROOT / ".github" / "workflows" / "docs.yml"
_PYTHON_WORKFLOW = _ROOT / ".github" / "workflows" / "python-app.yml"
_CITATION_MODULE = _ROOT / "site" / "src" / "data" / "citation.mjs"


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """A glob from ``.coderabbit.yaml`` as a regex over repository paths.

    Only the constructs that file uses are understood: ``**`` for any run of
    directories, ``*`` inside one name, and a whole-segment negation
    ``!(a|b)``. Anything else raises rather than being dropped, so a future
    pattern can never be judged by a translation that quietly ignored half of
    it.
    """
    segments = pattern.split("/")
    out = ""
    for index, segment in enumerate(segments):
        last = index == len(segments) - 1
        if segment == "**":
            out += ".+" if last else r"(?:[^/]+/)*"
            continue
        negated = re.fullmatch(r"!\(([^()]+)\)", segment)
        if negated:
            alternatives = "|".join(re.escape(a) for a in negated.group(1).split("|"))
            out += rf"(?!(?:{alternatives})(?:/|$))[^/]+"
        elif re.fullmatch(r"[\w.*-]+", segment):
            out += re.escape(segment).replace(r"\*", "[^/]*")
        else:
            msg = f"unsupported glob segment {segment!r} in {pattern!r}"
            raise AssertionError(msg)
        if not last:
            out += "/"
    return re.compile(out)


def _path_instructions() -> list[dict[str, str]]:
    config = yaml.safe_load(_CODERABBIT.read_text(encoding="utf-8"))
    rules = config["reviews"]["path_instructions"]
    assert rules, ".coderabbit.yaml carries no path instructions"
    return list(rules)


def _generated_overview_mirrors() -> set[str]:
    """The mirror indexes ``scripts/mirror_overviews.py`` actually writes."""
    return {
        mirror_overviews._mirror_path(
            page.parent.relative_to(mirror_overviews.SITE).as_posix()
        )
        .relative_to(_ROOT)
        .as_posix()
        for page in mirror_overviews._overviews()
    }


def test_the_generated_index_rule_covers_only_generated_indexes() -> None:
    """The rule that says "will be overwritten" must match nothing else.

    ``mirror_overviews.py`` skips ``reference/``, so ``docs/reference/api``
    and ``docs/reference/theory`` keep hand-written indexes. The API one is
    the sharper case: ``scripts/check_api_reference.py`` fails until a new
    public name is added to it by hand, so telling the bot the file is build
    output points it at the opposite of what CI demands.
    """
    generated = _generated_overview_mirrors()
    assert generated, "the overview generator claims to write nothing"

    on_disk = sorted(
        p.relative_to(_ROOT).as_posix() for p in _ROOT.glob("docs/**/*.md")
    )
    rules = [
        r for r in _path_instructions() if "mirror_overviews.py" in r["instructions"]
    ]
    generated_rules = [r for r in rules if "will be overwritten" in r["instructions"]]
    assert len(generated_rules) == 1, (
        "expected exactly one rule declaring the overview mirrors generated"
    )

    matcher = _glob_to_regex(generated_rules[0]["path"])
    matched = {path for path in on_disk if matcher.fullmatch(path)}
    assert matched == generated, (
        "the .coderabbit.yaml glob and the generator disagree; "
        f"claimed but hand-written: {sorted(matched - generated)}; "
        f"generated but unclaimed: {sorted(generated - matched)}"
    )


def test_the_readme_is_not_advertised_as_generated() -> None:
    """``docs/README.md`` is authored, and two gates require editing it.

    ``mirror_overviews.py`` and ``generate_llms.py`` both read it to assert it
    links every mirror page; neither writes it. Listing it among the generated
    files is the same false claim this configuration exists to correct.
    """
    claims = [
        rule["instructions"]
        for rule in _path_instructions()
        if "generated files under" in rule["instructions"]
    ]
    assert claims, (
        "no rule states which files under docs/ are generated; update this test "
        "with the phrasing that replaced it"
    )
    for text in claims:
        paragraph = text[text.index("generated files under") :]
        sentence = paragraph[: paragraph.index(".") + 1]
        assert "README" not in sentence, (
            f"the README is listed as generated output: {sentence!r}"
        )

    assert not any(
        path.endswith("README.md") for path in _generated_overview_mirrors()
    ), "the overview generator writes a README after all; the claim was right"


def _trigger_paths(workflow: pathlib.Path, event: str) -> set[str]:
    parsed = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    # ``on:`` is YAML 1.1's boolean true, which is what safe_load returns here.
    triggers = parsed[True] if True in parsed else parsed["on"]
    return set(triggers[event]["paths"])


def test_the_docs_workflow_triggers_on_every_root_file_the_site_build_reads() -> None:
    """A root file the site build reads has to be able to trigger that build.

    ``site/src/data/citation.mjs`` runs only inside ``astro build``, and that
    build runs only when the docs workflow's path filter matches. Every
    repository-root file the module reads therefore belongs in both filters:
    otherwise a pull request touching one of them merges without the guard
    that reads it ever running, and the failure surfaces later on an unrelated
    pull request that did not change the file at fault.
    """
    module = _CITATION_MODULE.read_text(encoding="utf-8")
    read = {
        match.group(1)
        for match in re.finditer(r"readFileSync\(\s*root\(\s*'([^']+)'", module)
    }
    root_files = sorted(name for name in read if "/" not in name)
    assert root_files, "citation.mjs reads no repository-root file; update this test"

    for event in ("push", "pull_request"):
        listed = _trigger_paths(_DOCS_WORKFLOW, event)
        missing = [name for name in root_files if name not in listed]
        assert not missing, (
            f"docs.yml {event} trigger does not list {missing}, "
            "so the site build that reads them cannot run on a change to them"
        )


def test_the_jit_job_comment_quotes_the_numba_floor_that_is_declared() -> None:
    """The 3.14 job explains itself by quoting pyproject's numba floor."""
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    declared = {
        spec
        for extra in pyproject["project"]["optional-dependencies"].values()
        for spec in extra
        if spec.replace(" ", "").startswith("numba")
    }
    assert declared, "pyproject.toml declares no numba requirement"

    quoted = set(
        re.findall(
            r"numba\s*>=\s*[0-9.]+", _PYTHON_WORKFLOW.read_text(encoding="utf-8")
        )
    )
    assert quoted, "the workflow quotes no numba floor; update this test"
    stale = {spec for spec in quoted if spec.replace(" ", "") not in declared}
    assert not stale, (
        f"python-app.yml quotes {sorted(stale)} but pyproject.toml declares {sorted(declared)}"
    )


def _engine_digests_step(steps: list[dict[str, object]], runs: str) -> int:
    """The index of the one step of the engine-digests job whose script has *runs*."""
    found = [i for i, step in enumerate(steps) if runs in str(step.get("run", ""))]
    assert len(found) == 1, f"{len(found)} engine-digests steps run {runs!r}"
    return found[0]


def test_the_engine_digests_test_names_a_moved_digest_after_the_measurement_fails() -> (
    None
):
    """The measurement and the test are two steps, and the test runs after a failure.

    A moved digest fails the measurement; in one step with the test, the step
    stopped there and the test that names the scenario and the key never ran.
    Both steps run under the same switches, and the measured file is kept
    whatever happened.
    """
    workflow = yaml.safe_load(_PYTHON_WORKFLOW.read_text(encoding="utf-8"))
    steps: list[dict[str, object]] = workflow["jobs"]["engine-digests"]["steps"]
    measure = _engine_digests_step(steps, "scripts/engine_digests.py --output")
    test = _engine_digests_step(steps, "tests/simulation/test_engine_golden_digests.py")
    assert measure < test
    condition = str(steps[test].get("if", ""))
    assert "success()" in condition
    assert "failure()" in condition
    assert "always()" not in condition, "a cancelled run should not start the test"
    for index in (measure, test):
        env = steps[index].get("env")
        assert isinstance(env, dict)
        assert env.get("PHONOMETRY_ENGINE_DIGESTS") == "require"
        assert "NPY_DISABLE_CPU_FEATURES" in env
    upload = [
        step
        for step in steps
        if str(step.get("uses", "")).startswith("actions/upload-artifact@")
    ]
    assert [step.get("if") for step in upload] == ["always()"]


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("docs/**/index.md", "docs/signals/index.md", True),
        ("docs/**/index.md", "docs/reference/api/index.md", True),
        ("docs/**/index.md", "docs/README.md", False),
        ("docs/!(reference)/**/index.md", "docs/signals/index.md", True),
        ("docs/!(reference)/**/index.md", "docs/signals/filters/index.md", True),
        ("docs/!(reference)/**/index.md", "docs/reference/api/index.md", False),
        ("docs/!(reference)/**/index.md", "docs/reference/theory/index.md", False),
        ("docs/**", "docs/start/about.md", True),
    ],
)
def test_the_glob_translation_agrees_with_the_matcher_coderabbit_uses(
    pattern: str, path: str, *, expected: bool
) -> None:
    """Pinned against minimatch and picomatch, run by hand on these cases."""
    assert bool(_glob_to_regex(pattern).fullmatch(path)) is expected


#: The one action whose maintainers publish no moving major tag: its README
#: names the ``release/v1`` branch as the channel to follow, and every v1.x
#: tag is cut from it.
_ACTION_CHANNELS = {"pypa/gh-action-pypi-publish": "release/v1"}
#: A release tag: ``v7``, ``v1.0``, ``v4.2.2``.
_RELEASE_TAG = re.compile(r"v\d+(?:\.\d+)*")


def test_every_action_is_pinned_to_a_release_tag() -> None:
    """An action runs at a release its maintainers tagged, never at a branch.

    zizmor's ``ref-pin`` policy (``.github/zizmor.yml``) accepts any ref, so a
    workflow that used an action at ``@master`` passed it: the JOSS draft
    action did, and a push to that branch would have run in the next build of
    the paper. Commit SHAs are not used either; a tag is what Dependabot moves
    and what a reader can check against the action's releases.
    """
    unpinned = []
    for path in sorted((_ROOT / ".github" / "workflows").glob("*.yml")):
        for action, ref in re.findall(
            r"uses:\s*([\w.-]+/[\w./-]+)@(\S+)", path.read_text(encoding="utf-8")
        ):
            if _ACTION_CHANNELS.get(action) == ref or _RELEASE_TAG.fullmatch(ref):
                continue
            unpinned.append(f"{path.name}: {action}@{ref}")
    assert unpinned == []


def _config_time_filters(options: Mapping[str, str | Sequence[str]]) -> list[str]:
    """Every warning filter pytest resolves while it reads its configuration.

    Those are the ``filterwarnings`` entries and the ``-W`` options in
    ``addopts``; a ``filterwarnings`` mark is resolved when its test runs.
    A string is read as pytest reads it: ``filterwarnings`` one filter per
    non-blank line, ``addopts`` split as a shell would split it.
    """
    entries = options.get("filterwarnings", [])
    if isinstance(entries, str):
        filters = [line.strip() for line in entries.split("\n") if line.strip()]
    else:
        filters = list(entries)
    addopts = options.get("addopts", [])
    args = shlex.split(addopts) if isinstance(addopts, str) else list(addopts)
    for index, arg in enumerate(args):
        if arg in {"-W", "--pythonwarnings"} and index + 1 < len(args):
            filters.append(args[index + 1])
        elif arg.startswith("--pythonwarnings="):
            filters.append(arg.partition("=")[2])
        elif arg.startswith("-W") and arg != "-W":
            filters.append(arg[2:].removeprefix("="))
    return filters


def _category(warning_filter: str) -> str:
    """The category field of ``action:message:category:module:lineno``."""
    fields = warning_filter.split(":")
    return fields[2].strip() if len(fields) > 2 else ""


def _names_a_builtin_warning(category: str) -> bool:
    """Whether pytest resolves ``category`` without importing anything.

    An empty category stands for :class:`Warning`, and a name without a dot is
    looked up in :mod:`builtins`. pytest imports the module of any dotted name,
    whether it lies in phonometry, in a helper on pytest's path, in a package
    at the repository root or in a third-party package.
    """
    if not category:
        return True
    found = None if "." in category else getattr(builtins, category, None)
    return isinstance(found, type) and issubclass(found, Warning)


def test_the_pytest_configuration_filters_warnings_by_builtin_class() -> None:
    """Every warning filter in the pytest configuration names a builtin class.

    pytest imports the class a filter names while it reads its configuration,
    before pytest-cov starts measuring and before ``tests/conftest.py`` runs.
    A filter that named ``phonometry.filters.FilterBankWarning`` imported most
    of the package there, and every line that runs at import time (the
    imports, the ``def`` lines, the module constants) was reported uncovered
    by Codecov and SonarCloud alike. A builtin class imports nothing; a
    warning its message cannot single out under one is filtered by a
    ``filterwarnings`` mark on the tests concerned, which pytest resolves when
    they run.
    """
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        options = tomllib.load(handle)["tool"]["pytest"]["ini_options"]
    filters = _config_time_filters(options)
    assert filters, (
        "the pytest configuration carries no warning filter; update this test"
    )
    offending = [f for f in filters if not _names_a_builtin_warning(_category(f))]
    assert offending == [], (
        f"these warning filters name a class pytest imports before coverage starts: "
        f"{offending}; name the builtin class the warning derives from "
        "(docs/contributing/tests.md#t25)"
    )


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({"filterwarnings": ["ignore:Low:phonometry.filters.FilterBankWarning"]}, True),
        ({"filterwarnings": "ignore::oracle_data.OracleWarning"}, True),
        ({"addopts": ["-W", "error::phonometry.PhonometryWarning"]}, True),
        ({"addopts": "-q -Werror::phonometry.PhonometryWarning"}, True),
        ({"addopts": ["--pythonwarnings=ignore::phonometry.PhonometryWarning"]}, True),
        ({"filterwarnings": "ignore::reference_data.room.RoomWarning"}, True),
        (
            {"filterwarnings": "ignore::UserWarning\nignore::phonometry.X"},
            True,
        ),
        ({"addopts": "-q\n-W error::phonometry.PhonometryWarning"}, True),
        ({"filterwarnings": ["ignore:Low sampling rate:UserWarning"]}, False),
        ({"filterwarnings": ["error:.*since phonometry.*:DeprecationWarning"]}, False),
        ({"filterwarnings": ["ignore::scripts.check_raises_blocks.X"]}, True),
        ({"filterwarnings": ["ignore::numpy.exceptions.ComplexWarning"]}, True),
        ({"filterwarnings": ["ignore::ValueError"]}, True),
        ({"filterwarnings": ["ignore:Low sampling rate"]}, False),
    ],
)
def test_the_filter_reader_sees_every_form_pytest_accepts(
    options: Mapping[str, str | Sequence[str]], *, expected: bool
) -> None:
    """A class pytest would import is found in each place and spelling it reads."""
    found = [_category(f) for f in _config_time_filters(options)]
    assert any(not _names_a_builtin_warning(c) for c in found) is expected


# ---------------------------------------------------------------------------
# The type check is one command, bare `mypy`, wherever it is given to be run.
# Its paths live in one place, `files` under [tool.mypy] in pyproject.toml.
# While CI, the Makefile and three pages each spelled the list out, the
# Makefile and the pull request template had both dropped `stub/src`, and
# nothing compared any of them with another.

#: A type-check command: `mypy`, or the Makefile's `$(MYPY)`, at the start of
#: a command, with whatever follows it up to the end of that command.
_MYPY_COMMAND = re.compile(
    r"(?:^|&&|\|\||[;|(])\s*(?:mypy|\$\(MYPY\))(?=\s|$|[;&|)])(?P<arguments>[^;&|)\n]*)"
)

#: A Markdown fence, opening or closing.
_FENCE = re.compile(r"^\s*(?:```|~~~)")

#: An inline code span of a Markdown page.
_CODE_SPAN = re.compile(r"`([^`\n]+)`")

#: Where the command is given today. Each must still be found, so the scan
#: cannot pass by reading nothing.
_MYPY_STATED_IN = (
    ".github/pull_request_template.md",
    ".github/workflows/python-app.yml",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "Makefile",
)

#: The roots bare `mypy` has to keep checking: the package, the scripts, the
#: transition shim and the script that writes the pull request comment.
_MYPY_ROOTS = ("src", "scripts", "stub/src", ".github/scripts")


def _tracked(*patterns: str) -> list[str]:
    """The tracked paths that match *patterns*, relative to the root."""
    listed = child_process.run(
        ["git", "ls-files", "-z", "--", *patterns],
        cwd=_ROOT,
        check=True,
        capture_output=True,
        timeout=120,
    ).stdout.decode("utf-8")
    return [name for name in listed.split("\0") if name]


def _scripts_of(node: object) -> list[str]:
    """Every ``run:`` script of a workflow or an action, at any depth."""
    if isinstance(node, dict):
        found = [node["run"]] if isinstance(node.get("run"), str) else []
        for value in node.values():
            found += _scripts_of(value)
        return found
    if isinstance(node, list):
        return [script for item in node for script in _scripts_of(item)]
    return []


def _commands_in(lines: Sequence[str]) -> list[str]:
    """The type-check commands in *lines*, each as written."""
    return [
        match.group(0).strip(" ;&|(")
        for line in lines
        for match in _MYPY_COMMAND.finditer(line.strip().lstrip("@-+"))
    ]


def _markdown_commands(text: str) -> list[str]:
    """The type-check commands a page gives: fenced lines and inline code.

    Prose that names the tool is not a command; a code span or a fenced
    block is how every page here writes something to run.
    """
    commands: list[str] = []
    fenced = False
    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            commands += _commands_in([line])
        else:
            spans = [span.strip() for span in _CODE_SPAN.findall(line)]
            commands += _commands_in(spans)
    return commands


def _stated_mypy_commands() -> dict[str, list[str]]:
    """Every type-check command the tracked tree tells anyone to run, by file.

    The CHANGELOG is left out: it records the commands of past releases.
    """
    stated: dict[str, list[str]] = {}
    for name in _tracked(".github/*.yml", ".github/*.yaml"):
        document = yaml.safe_load((_ROOT / name).read_text(encoding="utf-8"))
        scripts = _scripts_of(document)
        stated[name] = _commands_in(
            [line for script in scripts for line in script.splitlines()]
        )
    for name in _tracked("Makefile", "*/Makefile"):
        text = (_ROOT / name).read_text(encoding="utf-8")
        stated[name] = _commands_in(
            [line for line in text.splitlines() if line.startswith("\t")]
        )
    for name in _tracked("*.md", "*.mdx"):
        if name == "CHANGELOG.md":
            continue
        text = (_ROOT / name).read_text(encoding="utf-8")
        stated[name] = _markdown_commands(text)
    return {name: commands for name, commands in stated.items() if commands}


def test_every_stated_type_check_is_bare_mypy() -> None:
    """CI, ``make lint`` and every page run the type check as plain ``mypy``.

    A path list written out in one of them is a second copy of ``files``,
    and the copies drift: the Makefile and the pull request template had
    both lost ``stub/src`` while CI still checked it.
    """
    stated = _stated_mypy_commands()
    missing = [name for name in _MYPY_STATED_IN if name not in stated]
    assert not missing, (
        f"no type-check command found in {missing}; if one moved, update "
        "_MYPY_STATED_IN, and if the scan stopped finding it, fix the scan"
    )
    spelled_out = [
        f"{name}: {command}"
        for name, commands in sorted(stated.items())
        for command in commands
        if command not in ("mypy", "$(MYPY)")
    ]
    assert not spelled_out, (
        f"run the type check as bare `mypy`, whose paths are `files` under "
        f"[tool.mypy] in pyproject.toml: {spelled_out}"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("```bash\nmypy src scripts\n```\n", ["mypy src scripts"]),
        ("- [ ] `mypy src`\n", ["mypy src"]),
        ("Run (`pytest`, `mypy`, `ruff`).\n", ["mypy"]),
        ("mypy takes the paths it is given.\n", []),
        ("```\nruff check . && mypy stub/src\n```\n", ["mypy stub/src"]),
        ("```\nmypyc build\n```\n", []),
    ],
    ids=["fenced", "code span", "bare in prose", "prose", "chained", "other tool"],
)
def test_the_command_reader_finds_a_command_and_only_a_command(
    text: str, expected: list[str]
) -> None:
    """The scan reads code, not prose, and a command after ``&&`` too."""
    assert _markdown_commands(text) == expected


def test_bare_mypy_checks_every_root_the_gate_needs() -> None:
    """``files`` under [tool.mypy] holds every root CI has to type check."""
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        files = tomllib.load(handle)["tool"]["mypy"]["files"]
    missing = [root for root in _MYPY_ROOTS if root not in files]
    assert not missing, f"[tool.mypy] files no longer lists {missing}"
