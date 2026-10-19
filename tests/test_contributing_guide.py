#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The contributor style guide keeps its own promises.

``docs/contributing/`` states the project's style rules, each with an
identifier and the check that enforces it, for the people and the coding
agents who change phonometry. A guide like that rots quietly: a rule is added
to a page and not to the index, a script it cites is renamed, a guard message
keeps pointing at a CONTRIBUTING section the guide absorbed. These tests hold
the guide to what it says, first on small fake guides that show each failure,
then on the real one.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import sys
import tomllib

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import markdown_fences
import mirror_overviews

#: This file names the absorbed sections and writes a link to a missing anchor
#: on purpose, to show the checks failing; it is the one file they do not read.
_THIS_FILE = pathlib.Path(__file__).resolve()

#: Each topic page and the ID prefixes its rules use.
PAGES: dict[str, str] = {
    "naming.md": "N",
    "api.md": "A",
    "docstrings.md": "DC",
    "numerics.md": "X",
    "tests.md": "T",
    "docs-and-figures.md": "F",
    "prose.md": "P",
}

#: The CONTRIBUTING.md sections the guide absorbed. None may stay a heading
#: there, and nothing may send a reader to one.
MOVED_TITLES: tuple[str, ...] = (
    "Setting a subscript",
    "Passing the language on",
    "Defaulting a style the caller may spell either way",
    "Writing a long number",
    "Judging a computed value at a printed limit",
    "Keeping an array a function was given",
    "Showing a record in a notebook",
    "Writing the code fences of a documentation page",
    "Naming Conventions",
    "The three verbs of a judgement",
    "A lookup that misses",
    "The class of a refusal",
    "Module length",
    "A module and what it publishes",
    "Deprecations",
)
_MOVED_NUMBERS = re.compile(r"\bsections?\s+(?:7[a-g]?|8)\b", re.IGNORECASE)

_HEADING = re.compile(r"^### ([A-Z])(\d+)\. (\S.*)$")
_ENFORCED = re.compile(r"^\*\*Enforced by:\*\* (\S.*)$")
_ROW = re.compile(
    r"^\| \[([A-Z]\d+)\]\(([a-z-]+\.md)#([a-z]\d+)\) \| (.+?) \| (.+?) \|$"
)
_SPAN = re.compile(r"^`([^`]+)`$")
_GUIDE_LINK = re.compile(r"contributing/([a-z-]+\.md)(?:#([\w-]+))?")
_LOCAL_LINK = re.compile(r"\]\(([a-z-]+\.md)(?:#([\w-]+))?\)")
_COMMENT_LEAD = re.compile(r"^\s*(?:#:|#|//|\*|>)?\s*")


@dataclasses.dataclass(frozen=True)
class Rule:
    """One rule as a page states it."""

    rule_id: str
    page: str
    statement: str
    enforced_by: str


@dataclasses.dataclass(frozen=True)
class IndexRow:
    """One row of the index table."""

    rule_id: str
    page: str
    anchor: str
    statement: str
    enforced_by: str


def _prose_lines(text: str) -> list[tuple[int, str]]:
    """``(lineno, line)`` for every line outside a fence."""
    lines = text.splitlines()
    return [
        (n, line)
        for n, (line, code) in enumerate(
            zip(lines, markdown_fences.code_lines(lines), strict=True), 1
        )
        if not code
    ]


def read_page(path: pathlib.Path) -> tuple[list[Rule], list[str]]:
    """The rules ``path`` states, in order, and what is malformed about them."""
    text = path.read_text(encoding="utf-8")
    prose = _prose_lines(text)
    problems: list[str] = []
    starts = [i for i, (_, line) in enumerate(prose) if _HEADING.match(line)]
    rules: list[Rule] = []
    for k, start in enumerate(starts):
        lineno, line = prose[start]
        letter, number, statement = _HEADING.match(line).groups()  # type: ignore[union-attr]
        rule_id = f"{letter}{number}"
        before = [ln for _, ln in prose[:start] if ln.strip()]
        anchor = f'<a id="{rule_id.lower()}"></a>'
        if not before or before[-1].strip() != anchor:
            problems.append(
                f"{path.name}:{lineno}: {rule_id} needs {anchor} as the last line before its heading"
            )
        end = starts[k + 1] if k + 1 < len(starts) else len(prose)
        enforced = [
            m.group(1) for _, ln in prose[start + 1 : end] if (m := _ENFORCED.match(ln))
        ]
        if len(enforced) != 1:
            problems.append(
                f"{path.name}:{lineno}: {rule_id} needs exactly one '**Enforced by:**' line, has {len(enforced)}"
            )
        rules.append(
            Rule(rule_id, path.name, statement, enforced[0] if enforced else "")
        )
    return rules, problems


def dont_fence_problems(path: pathlib.Path) -> list[str]:
    """A fence right after '**Don't**' that would run, or one after '**Do**' that would not."""
    lines = path.read_text(encoding="utf-8").splitlines()
    problems: list[str] = []
    label = None
    for n, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped in ("**Do**", "**Don't**"):
            label = stripped
            continue
        if label and stripped.startswith(("```", "~~~")):
            language = stripped.lstrip("`~").split(" ", 1)[0]
            if label == "**Don't**" and language == "python":
                problems.append(
                    f"{path.name}:{n}: a Don't example is fenced as python, so it runs; fence it as py"
                )
            if label == "**Do**" and language == "py":
                problems.append(
                    f"{path.name}:{n}: a Do example is fenced as py, so it never runs; fence it as python"
                )
            label = None
        elif stripped:
            label = None
    return problems


def read_index(path: pathlib.Path) -> list[IndexRow]:
    """The rows of the index table, in order."""
    return [
        IndexRow(*m.groups())
        for _, line in _prose_lines(path.read_text(encoding="utf-8"))
        if (m := _ROW.match(line))
    ]


def _items(enforced_by: str) -> list[str]:
    return [item.strip() for item in enforced_by.rstrip(".").split(",")]


def enforcer_problem(item: str, root: pathlib.Path) -> str | None:
    """Why ``item`` (one entry of an 'Enforced by' line) names nothing real, or None."""
    if item == "review":
        return None
    span = _SPAN.match(item)
    if span is None:
        return f"{item!r} is neither 'review' nor one code span"
    target = span.group(1)
    if target.startswith("make "):
        name = target.removeprefix("make ").strip()
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        return (
            None
            if re.search(rf"^{re.escape(name)}\s*:", makefile, re.MULTILINE)
            else f"no Makefile target {name!r}"
        )
    if target.startswith("ruff "):
        code = target.removeprefix("ruff ").strip()
        if code == "format":
            return None
        config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        selected = config["tool"]["ruff"]["lint"]["select"]
        return (
            None
            if any(code.startswith(prefix) for prefix in selected)
            else f"ruff {code} is not selected"
        )
    if target.startswith("CI: "):
        # A job's name, or the name of one step of a job (``- name:``).
        job = target.removeprefix("CI: ").strip().strip('"')
        workflows = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (root / ".github" / "workflows").glob("*.yml")
        )
        return (
            None
            if re.search(
                rf"^\s*(?:-\s+)?name:\s*['\"]?{re.escape(job)}['\"]?\s*$",
                workflows,
                re.MULTILINE,
            )
            else f"no CI job or step named {job!r}"
        )
    if target in ("mypy", "bandit"):
        return (
            None
            if target
            in (root / ".github" / "workflows" / "python-app.yml").read_text(
                encoding="utf-8"
            )
            else f"CI never runs {target}"
        )
    file_part, _, test_name = target.partition("::")
    path = root / file_part
    if not path.exists():
        return f"{file_part} does not exist"
    if test_name and f"def {test_name.split('[')[0]}" not in path.read_text(
        encoding="utf-8"
    ):
        return f"{file_part} has no {test_name}"
    return None


def _scanned_files(root: pathlib.Path) -> list[pathlib.Path]:
    files = [
        root / name
        for name in (
            "CONTRIBUTING.md",
            "AGENTS.md",
            "CLAUDE.md",
            "README.md",
            ".coderabbit.yaml",
        )
    ]
    for folder, pattern in (
        ("src", "*.py"),
        ("scripts", "*.py"),
        ("tests", "*.py"),
        ("docs", "*.md"),
        (".github", "*.yml"),
    ):
        files += sorted((root / folder).rglob(pattern))
    return [
        p
        for p in files
        if p.is_file() and "superpowers" not in p.parts and p.resolve() != _THIS_FILE
    ]


def link_problems(root: pathlib.Path) -> list[str]:
    """Every link into the guide that does not land on a page and an anchor that exist."""
    guide = root / "docs" / "contributing"
    problems: list[str] = []
    for path in _scanned_files(root):
        text = path.read_text(encoding="utf-8")
        found = [(m.group(1), m.group(2)) for m in _GUIDE_LINK.finditer(text)]
        if path.parent == guide:
            found += [(m.group(1), m.group(2)) for m in _LOCAL_LINK.finditer(text)]
        for page, fragment in found:
            target = guide / page
            if not target.exists():
                problems.append(
                    f"{path.relative_to(root).as_posix()}: links {page}, which does not exist"
                )
            elif fragment and fragment not in mirror_overviews._fragments(target):
                problems.append(
                    f"{path.relative_to(root).as_posix()}: links {page}#{fragment}, which is not an anchor there"
                )
    return problems


def _collapsed(text: str) -> str:
    """The text as one line, comment leaders removed, so a wrapped reference reads whole."""
    return " ".join(_COMMENT_LEAD.sub("", line) for line in text.splitlines())


def moved_reference_problems(root: pathlib.Path) -> list[str]:
    """Text that still sends a reader to a CONTRIBUTING section the guide absorbed."""
    problems: list[str] = []
    titles = [t.lower() for t in MOVED_TITLES]
    for path in _scanned_files(root):
        text = _collapsed(path.read_text(encoding="utf-8"))
        for m in re.finditer("CONTRIBUTING", text):
            window = text[m.end() : m.end() + 160]
            lowered = window.lower()
            hit = next((t for t in titles if t in lowered), None)
            if hit is None and (number := _MOVED_NUMBERS.search(window)):
                hit = number.group(0)
            if hit:
                problems.append(
                    f"{path.relative_to(root).as_posix()}: sends the reader to CONTRIBUTING ({hit!r}), which moved to docs/contributing/"
                )
    return problems


# --- the failures, shown on fake guides -------------------------------------


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


_GOOD_RULE = '<a id="n1"></a>\n### N1. A name says what it returns\n\n**Why.** Because.\n\n**Enforced by:** review\n'


def test_a_rule_without_its_anchor_is_reported(tmp_path: pathlib.Path) -> None:
    page = _write(tmp_path / "naming.md", _GOOD_RULE.replace('<a id="n1"></a>\n', ""))
    _, problems = read_page(page)
    assert any('needs <a id="n1"></a>' in p for p in problems)


def test_a_rule_without_an_enforcer_line_is_reported(tmp_path: pathlib.Path) -> None:
    page = _write(
        tmp_path / "naming.md", _GOOD_RULE.replace("**Enforced by:** review\n", "")
    )
    _, problems = read_page(page)
    assert any("exactly one '**Enforced by:**'" in p for p in problems)


def test_a_well_formed_rule_reads_back(tmp_path: pathlib.Path) -> None:
    page = _write(tmp_path / "naming.md", _GOOD_RULE)
    assert read_page(page) == (
        [Rule("N1", "naming.md", "A name says what it returns", "review")],
        [],
    )


def test_a_dont_example_that_would_run_is_reported(tmp_path: pathlib.Path) -> None:
    page = _write(
        tmp_path / "naming.md",
        _GOOD_RULE + "\n**Don't**\n\n```python\nget_level()\n```\n",
    )
    assert dont_fence_problems(page)


def test_an_enforcer_that_does_not_exist_is_reported() -> None:
    assert (
        enforcer_problem("`scripts/check_nothing_here.py`", _ROOT)
        == "scripts/check_nothing_here.py does not exist"
    )
    assert enforcer_problem("make no-such-target", _ROOT) is not None
    assert (
        enforcer_problem("`make no-such-target`", _ROOT)
        == "no Makefile target 'no-such-target'"
    )
    assert enforcer_problem("`ruff ZZZ999`", _ROOT) == "ruff ZZZ999 is not selected"


def test_a_ci_job_or_one_of_its_steps_is_an_enforcer(tmp_path: pathlib.Path) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "jobs:\n  quality:\n    name: Quality gate\n    steps:\n"
        "    - name: Audit the workflows\n      run: zizmor .github/\n",
    )
    assert enforcer_problem("`CI: Quality gate`", tmp_path) is None
    assert enforcer_problem("`CI: Audit the workflows`", tmp_path) is None
    assert (
        enforcer_problem("`CI: Audit the docs`", tmp_path)
        == "no CI job or step named 'Audit the docs'"
    )


def test_a_link_to_a_missing_anchor_is_reported(tmp_path: pathlib.Path) -> None:
    _write(tmp_path / "docs" / "contributing" / "naming.md", _GOOD_RULE)
    _write(
        tmp_path / "scripts" / "check_x.py",
        '"""See docs/contributing/naming.md#n9."""\n',
    )
    assert link_problems(tmp_path) == [
        "scripts/check_x.py: links naming.md#n9, which is not an anchor there"
    ]


def test_a_wrapped_reference_to_a_moved_section_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    _write(
        tmp_path / "scripts" / "canvas.py",
        '#: two files may disagree (CONTRIBUTING.md, "Setting a\n#: subscript").\n',
    )
    assert moved_reference_problems(tmp_path)


# --- the real guide -----------------------------------------------------------

GUIDE = _ROOT / "docs" / "contributing"


def _all_rules() -> list[Rule]:
    rules: list[Rule] = []
    for name in PAGES:
        rules += read_page(GUIDE / name)[0]
    return rules


@pytest.mark.parametrize("name", sorted(PAGES))
def test_every_page_is_well_formed(name: str) -> None:
    rules, problems = read_page(GUIDE / name)
    assert rules, f"{name} states no rule"
    assert problems == []
    assert dont_fence_problems(GUIDE / name) == []
    for prefix in PAGES[name]:
        numbers = [int(r.rule_id[1:]) for r in rules if r.rule_id[0] == prefix]
        assert numbers == list(range(1, len(numbers) + 1)), (
            f"{name}: {prefix} rules must be numbered 1..n in order"
        )
    assert {r.rule_id[0] for r in rules} <= set(PAGES[name])


def test_index_matches_the_pages() -> None:
    rows = read_index(GUIDE / "index.md")
    by_id = {r.rule_id: r for r in _all_rules()}
    assert [row.rule_id for row in rows] == list(by_id), (
        "the index lists every rule once, in page order"
    )
    for row in rows:
        rule = by_id[row.rule_id]
        assert (row.page, row.anchor) == (rule.page, rule.rule_id.lower()), row.rule_id
        assert row.statement == rule.statement, row.rule_id
        assert row.enforced_by == rule.enforced_by, row.rule_id


def test_every_enforcer_exists() -> None:
    problems = [
        f"{rule.rule_id}: {problem}"
        for rule in _all_rules()
        for item in _items(rule.enforced_by)
        if (problem := enforcer_problem(item, _ROOT))
    ]
    assert problems == []


def test_every_link_into_the_guide_resolves() -> None:
    assert link_problems(_ROOT) == []


def test_no_reference_to_a_moved_section() -> None:
    headings = (_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    still = [
        t
        for t in MOVED_TITLES
        if re.search(rf"^#+ .*{re.escape(t)}\s*$", headings, re.MULTILINE)
    ]
    assert still == [], (
        "these sections moved to docs/contributing/ and must leave CONTRIBUTING.md"
    )
    assert moved_reference_problems(_ROOT) == []


def test_agents_md_states_no_rule() -> None:
    """AGENTS.md points at the guide; a rule written there would drift from it."""
    agents = (_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/contributing/index.md" in agents
    assert not re.search(r"^### [A-Z]\d+\. ", agents, re.MULTILINE)
    assert (_ROOT / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
