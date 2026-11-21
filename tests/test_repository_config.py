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

import ast
import builtins
import fnmatch
import io
import json
import os
import pathlib
import posixpath
import re
import shlex
import shutil
import sys
import tomllib
from typing import TYPE_CHECKING

import child_process
import pytest
import yaml

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import github_edition

_CODERABBIT = _ROOT / ".coderabbit.yaml"
_DOCS_WORKFLOW = _ROOT / ".github" / "workflows" / "docs.yml"
_SITE_DEPLOY_WORKFLOW = _ROOT / ".github" / "workflows" / "site-deploy.yml"
_PYTHON_WORKFLOW = _ROOT / ".github" / "workflows" / "python-app.yml"
_MAKEFILE = _ROOT / "Makefile"


def _workflow_files(root: pathlib.Path | None = None) -> list[pathlib.Path]:
    """Every workflow of the repository, sorted by path.

    GitHub runs a workflow written as ``.yml`` or as ``.yaml``, so a check
    over the workflows reads both: one that read ``*.yml`` alone passed a
    ``.yaml`` workflow unread.
    """
    folder = (_ROOT if root is None else root) / ".github" / "workflows"
    return sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])


_CITATION_MODULE = _ROOT / "site" / "src" / "data" / "citation.mjs"
_REPO_STATS_MODULE = _ROOT / "site" / "src" / "data" / "repo-stats.mjs"
_STRUCTURED_DATA_CHECK = _ROOT / "site" / "scripts" / "check-structured-data.mjs"


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


#: How every file of the GitHub edition opens: a comment naming the site page
#: ``site/scripts/agent-md.mjs --docs`` wrote it from
#: (``site/src/lib/agent-md/edition.mjs``, ``EDITION_MARK``).
def _edition_pages() -> set[str]:
    """The files of the GitHub edition under ``docs/``, by the comment they open with."""
    return {
        path.relative_to(_ROOT).as_posix()
        for path in _ROOT.glob("docs/**/*.md")
        if github_edition.is_edition_file(path)
    }


def test_the_python_checks_know_the_edition_by_the_comment_it_is_written_with() -> None:
    """``scripts/github_edition.py`` reads the opening ``edition.mjs`` writes.

    A Python check tells a file of the edition from a hand-written one by its
    first characters; a reworded opening on the JavaScript side would make
    every file of the edition read as written by hand again, silently.
    """
    source = (_ROOT / "site" / "src" / "lib" / "agent-md" / "edition.mjs").read_text(
        encoding="utf-8"
    )
    mark = re.search(r"^export const EDITION_MARK = '([^']*)';$", source, re.MULTILINE)
    assert mark, "edition.mjs no longer states EDITION_MARK as one quoted string"
    assert "`${EDITION_MARK}site/src/content/docs/`" in source
    assert github_edition.EDITION_MARK == f"{mark.group(1)}site/src/content/docs/"


def test_only_a_markdown_file_is_opened_to_tell_the_edition(
    tmp_path: pathlib.Path,
) -> None:
    """The gates ask of every file they walk; only a ``.md`` file is the edition's.

    A module, a site page or a data file that happened to open with the same
    characters is not a file of the edition, and is not opened to find out.
    """
    opening = f"{github_edition.EDITION_MARK}page.mdx: edit that page. -->\n"
    for name in ("page.md", "page.mdx", "module.py"):
        (tmp_path / name).write_text(opening, encoding="utf-8")
    assert github_edition.is_edition_file(tmp_path / "page.md")
    assert not github_edition.is_edition_file(tmp_path / "page.mdx")
    assert not github_edition.is_edition_file(tmp_path / "module.py")
    assert not github_edition.is_edition_file(tmp_path / "absent.json")


@pytest.mark.whole_tree
def test_the_generated_page_rules_cover_only_the_edition() -> None:
    """The rules that say "will be overwritten" must match the edition and nothing else.

    The edition is every page of docs/ that stands for a page of the site, and
    beside it sit files written by hand that CI requires a hand edit of. The
    sharpest is ``docs/reference/api/index.md``, the curated API table:
    ``scripts/check_api_reference.py`` fails until a new public name is added
    to it by hand, so telling the bot the file is build output points it at
    the opposite of what CI demands. ``docs/README.md``, the errata registers
    and ``docs/contributing/`` are the others.
    """
    generated = _edition_pages()
    assert len(generated) > 200, (
        "the edition holds fewer pages than the site has guides"
    )

    on_disk = sorted(
        p.relative_to(_ROOT).as_posix() for p in _ROOT.glob("docs/**/*.md")
    )
    rules = [
        r for r in _path_instructions() if "will be overwritten" in r["instructions"]
    ]
    assert rules, "no rule declares the edition's pages generated"

    matched = {
        path
        for rule in rules
        for path in on_disk
        if _glob_to_regex(rule["path"]).fullmatch(path)
    }
    assert matched == generated, (
        "the .coderabbit.yaml globs and the edition disagree; "
        f"claimed but hand-written: {sorted(matched - generated)}; "
        f"generated but unclaimed: {sorted(generated - matched)}"
    )


@pytest.mark.whole_tree
def test_the_readme_is_not_advertised_as_generated() -> None:
    """``docs/README.md`` is authored, and ``make llms`` requires editing it.

    The edition's generator reads it to assert it links every page of the
    edition; it never writes it. Listing it among the generated files is the
    same false claim this configuration exists to correct.
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
        sentence = paragraph[: paragraph.index(". ") + 1]
        assert "README" not in sentence, (
            f"the README is listed as generated output: {sentence!r}"
        )

    assert "docs/README.md" not in _edition_pages(), (
        "the edition's generator writes the README after all; the claim was right"
    )


def _trigger_paths(workflow: pathlib.Path, event: str) -> set[str]:
    parsed = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    # ``on:`` is YAML 1.1's boolean true, which is what safe_load returns here.
    triggers = parsed[True] if True in parsed else parsed["on"]
    return set(triggers[event]["paths"])


#: The site modules that read files at the repository root, each with the way
#: it names one: ``citation.mjs`` through its ``root('<name>')`` helper,
#: ``repo-stats.mjs`` and the structured-data check, which the docs workflow
#: runs on the build, as ``join(<root>, '<name>')``.
_ROOT_READERS: dict[pathlib.Path, re.Pattern[str]] = {
    _CITATION_MODULE: re.compile(r"readFileSync\(\s*root\(\s*'([^']+)'"),
    _REPO_STATS_MODULE: re.compile(r"\bjoin\(\s*ROOT\s*,\s*'([^']+)'\s*\)"),
    _STRUCTURED_DATA_CHECK: re.compile(
        r"\bjoin\(\s*REPOSITORY_ROOT\s*,\s*'([^']+)'\s*\)"
    ),
}


def test_the_docs_workflow_triggers_on_every_root_file_the_site_build_reads() -> None:
    """A root file the site build reads has to be able to trigger that build.

    ``site/src/data/citation.mjs`` and ``site/src/data/repo-stats.mjs`` run
    only inside ``astro build``, the structured-data check only on its output,
    and both run only when the docs workflow's path filter matches. Every
    repository-root file these modules read therefore belongs in both filters:
    otherwise a pull request touching one of them merges without the guard
    that reads it ever running, and the failure surfaces later on an unrelated
    pull request that did not change the file at fault. ``pyproject.toml`` is
    one: the site states its Python floor and requirements from it, and stops
    on a requirement it cannot state.
    """
    root_files: set[str] = set()
    for module, reads in _ROOT_READERS.items():
        read = {
            match.group(1)
            for match in reads.finditer(module.read_text(encoding="utf-8"))
            if "/" not in match.group(1)
        }
        assert read, (
            f"{module.relative_to(_ROOT)} reads no repository-root file; "
            "update this test"
        )
        root_files |= read

    for event in ("push", "pull_request"):
        listed = _trigger_paths(_DOCS_WORKFLOW, event)
        missing = sorted(name for name in root_files if name not in listed)
        assert not missing, (
            f"docs.yml {event} trigger does not list {missing}, "
            "so the site build that reads them cannot run on a change to them"
        )


def _requests_naming_a_user_agent(tree: ast.AST) -> set[str]:
    """Names bound to a ``urllib.request.Request`` whose headers give a User-Agent."""
    named: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and _is_request_with_user_agent(node.value)
        ):
            named.add(node.targets[0].id)
    return named


def _is_request_with_user_agent(node: ast.AST) -> bool:
    """Whether *node* is a ``urllib.request.Request(...)`` call with a User-Agent header."""
    if not (
        isinstance(node, ast.Call)
        and ast.unparse(node.func) == "urllib.request.Request"
    ):
        return False
    headers = next((kw.value for kw in node.keywords if kw.arg == "headers"), None)
    return isinstance(headers, ast.Dict) and any(
        isinstance(key, ast.Constant) and key.value == "User-Agent"
        for key in headers.keys
    )


def _unnamed_requests(steps: list[dict[str, object]]) -> tuple[int, list[str]]:
    """How many ``urlopen`` calls the steps' Python makes, and those sending no User-Agent.

    Each ``<<'PY'`` heredoc is parsed, and a call is one when its AST says so,
    however it is spaced (``urlopen (url)`` too), so no script that opens a
    URL is left unread. A call names the job when its first argument is a
    ``Request`` built with a User-Agent header, or a name bound to one.
    """
    calls = 0
    bare: list[str] = []
    for step in steps:
        run = str(step.get("run", ""))
        for match in re.finditer(r"<<'PY'\n(.*?)\nPY", run, re.DOTALL):
            tree = ast.parse(match.group(1))
            named = _requests_naming_a_user_agent(tree)
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and ast.unparse(node.func).endswith("urlopen")
                ):
                    continue
                calls += 1
                first = node.args[0] if node.args else None
                if first is None or not (
                    _is_request_with_user_agent(first)
                    or (isinstance(first, ast.Name) and first.id in named)
                ):
                    bare.append(f"urlopen({ast.unparse(first) if first else ''})")
    return calls, bare


def test_every_request_of_the_indexnow_job_names_the_job() -> None:
    """The IndexNow job sends its own User-Agent with every request it makes.

    Cloudflare answers 403 to urllib's default ``Python-urllib/3.x`` on
    phonometry.dev, so a job that fetched the key file without naming itself
    failed at the first deploy on the new host, and IndexNow was told
    nothing. Each ``urlopen`` call is read from the job's Python: its first
    argument has to be a ``Request`` built with a User-Agent header, or a
    name bound to one, never a bare URL.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    steps: list[dict[str, object]] = workflow["jobs"]["indexnow"]["steps"]
    calls, bare = _unnamed_requests(steps)
    assert calls, "no step of the indexnow job opens a URL; update this test"
    assert not bare, f"{bare} send no User-Agent"


#: Where the IndexNow job sends the pages.
_INDEXNOW_API = "https://api.indexnow.org/IndexNow"


def _string_constants(source: str) -> set[str]:
    """Every string literal a Python source holds, read from its AST."""
    return {
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _indexnow_submission() -> str:
    """The Python of the IndexNow job's step that sends the pages."""
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    steps: list[dict[str, object]] = workflow["jobs"]["indexnow"]["steps"]
    sources = [
        match.group(1)
        for step in steps
        for match in re.finditer(
            r"<<'PY'\n(.*?)\nPY", str(step.get("run", "")), re.DOTALL
        )
        if _INDEXNOW_API in _string_constants(match.group(1))
    ]
    assert len(sources) == 1, "one step of the indexnow job sends the pages"
    return sources[0]


@pytest.mark.parametrize(
    ("answers", "posts", "ends"),
    [
        ([403, 200], 2, "IndexNow HTTP 200 (2 URLs submitted)"),
        ([429, 429, 202], 3, "IndexNow HTTP 202 (2 URLs submitted)"),
        ([403] * 5, 5, "HTTP Error 403: refused"),
        ([400, 200], 1, "HTTP Error 400: refused"),
    ],
)
def test_indexnow_tries_a_403_or_a_429_again_and_nothing_else(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    answers: list[int],
    posts: int,
    ends: str,
) -> None:
    """The submission retries what api.indexnow.org has refused for a moment.

    Its first answer after the move to phonometry.dev was a 403 to a request
    it took by hand a moment later, so a 403 or a 429 is tried again, five
    tries in all, after a wait that doubles; any other refusal stops the job
    at once. The step's own Python runs here with its requests answered
    in-process.
    """
    import time
    import urllib.error
    import urllib.request

    key, base = "k" * 32, "https://phonometry.dev"
    (tmp_path / "indexnow").mkdir()
    (tmp_path / "indexnow" / "urls.json").write_text(
        json.dumps(
            {
                "urls": [f"{base}/a/", f"{base}/b/"],
                "full": False,
                "changed": ["a"],
                "new": ["b"],
                "removed": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("INDEXNOW_KEY", key)
    monkeypatch.setenv("PAGE_URL", f"{base}/")
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    left = list(answers)
    sent: list[str] = []

    class _Answer(io.BytesIO):
        status = 200

    def urlopen(request: urllib.request.Request, timeout: float) -> _Answer:
        url = request.full_url
        if url == f"{base}/{key}.txt":
            return _Answer(key.encode())
        assert url == _INDEXNOW_API, url
        sent.append(url)
        code = left.pop(0)
        if code >= 400:
            raise urllib.error.HTTPError(url, code, "refused", {}, None)  # type: ignore[arg-type]
        answer = _Answer(b"")
        answer.status = code
        return answer

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    source = _indexnow_submission()
    try:
        # The workflow's own script, run against the stubs above.
        exec(compile(source, "indexnow-submission", "exec"), {"__name__": "__main__"})  # noqa: S102
    except urllib.error.HTTPError as error:
        outcome = str(error)
    else:
        outcome = capsys.readouterr().out.strip().splitlines()[-1]
    assert len(sent) == posts
    assert outcome == ends


def test_a_urlopen_call_is_read_however_it_is_spaced() -> None:
    """The scripts are picked by the calls their AST holds, not by their text.

    A heredoc picked by the substring ``urlopen(`` would leave out one written
    ``urlopen (url)``, and the bare request in it would pass unread.
    """
    spaced = 'import urllib.request\nurllib.request.urlopen ("https://x/")\n'
    named = (
        "import urllib.request\n"
        'r = urllib.request.Request("https://x/", headers={"User-Agent": "j"})\n'
        "urllib.request.urlopen (r)\n"
    )
    assert _unnamed_requests([{"run": f"python3 - <<'PY'\n{spaced}PY\n"}]) == (
        1,
        ["urlopen('https://x/')"],
    )
    assert _unnamed_requests([{"run": f"python3 - <<'PY'\n{named}PY\n"}]) == (1, [])
    assert _unnamed_requests([{"run": "echo no python here"}]) == (0, [])


def test_the_docs_workflow_triggers_on_every_file_outside_the_site_the_base_path_check_reads() -> (
    None
):
    """A file the F76 check reads outside the site can trigger the run that checks it.

    ``site/scripts/base-path.mjs`` reads the README, the security policy, the
    package metadata, the paper and the issue templates for the old host, and
    it runs only in the docs workflow. A file it reads that the path filter
    leaves out could be given the old host again in a pull request that never
    runs the check.
    """
    source = (_ROOT / "site" / "scripts" / "base-path.mjs").read_text(encoding="utf-8")
    block = re.search(
        r"export const OUTSIDE = Object\.freeze\(\[(.*?)\]\);", source, re.DOTALL
    )
    assert block, "site/scripts/base-path.mjs has no OUTSIDE list; update this test"
    outside = [
        name.removeprefix("../") for name in re.findall(r"'([^']+)'", block.group(1))
    ]
    assert outside, "the OUTSIDE list of site/scripts/base-path.mjs is empty"
    for event in ("push", "pull_request"):
        listed = _trigger_paths(_DOCS_WORKFLOW, event)
        missing = [
            name
            for name in outside
            if name not in listed
            and not any(
                pattern.endswith("/**") and name.startswith(pattern[:-2])
                for pattern in listed
            )
            and f"{name}/**" not in listed
        ]
        assert not missing, f"docs.yml {event} trigger does not list {missing}"


_INDEXNOW_SCRIPT = _ROOT / "site" / "scripts" / "indexnow-diff.mjs"

#: The events that deploy the site: a push to main, and a run dispatched by
#: hand or by a merge on jmrp.io, whose identity data the site carries. A
#: newer run cancels an older one in the same queue, so a dispatch that comes
#: right after a merge is the run that deploys that merge's pages.
_DEPLOYING_EVENTS = ("push", "workflow_dispatch")

#: One token of a job's or step's ``if:``, in the part of GitHub's expression
#: language a condition on the event uses.
_CONDITION_TOKEN = re.compile(
    r"\s*(\(|\)|&&|\|\||==|!=|!|'(?:[^']|'')*'|[A-Za-z_][\w.-]*(?:\(\))?)"
)


def _runs_on(
    condition: object,
    event: str,
    variables: Mapping[str, str] | None = None,
    ref: str | None = None,
) -> bool:
    """Whether a job or a step whose ``if:`` is *condition* runs on *event*.

    No ``if:`` runs on every event. The reader knows ``github.event_name``
    compared with a string (case-insensitively, as GitHub compares strings),
    ``!``, ``&&``, ``||``, parentheses and ``success()``, a repository
    variable ``vars.NAME`` when *variables* is given (one it does not name is
    unset and reads as the empty string, as on GitHub), and ``github.ref``
    when *ref* is given, the ref the run was started on
    (``refs/heads/main``); anything else raises, so a condition that also
    depends on what this test cannot see is never judged by half of it.
    """
    if condition is None:
        return True
    text = str(condition).strip()
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2].strip()
    tokens: list[str] = []
    position = 0
    while position < len(text):
        match = _CONDITION_TOKEN.match(text, position)
        if match is None:
            msg = f"cannot read {text[position:]!r} in {condition!r}"
            raise ValueError(msg)
        tokens.append(match.group(1))
        position = match.end()
    at = 0

    def peek() -> str | None:
        return tokens[at] if at < len(tokens) else None

    def take() -> str:
        nonlocal at
        if at == len(tokens):
            msg = f"{condition!r} ends too soon"
            raise ValueError(msg)
        at += 1
        return tokens[at - 1]

    def operand() -> str | bool:
        token = take()
        if token == "(":
            value = either()
            if take() != ")":
                msg = f"unbalanced parentheses in {condition!r}"
                raise ValueError(msg)
            return value
        if token == "!":
            return not operand()
        if token.startswith("'"):
            return token[1:-1].replace("''", "'")
        if token == "github.event_name":
            return event
        if token == "github.ref" and ref is not None:
            return ref
        if token == "success()":
            return True
        if token.startswith("vars.") and variables is not None:
            return variables.get(token.removeprefix("vars."), "")
        msg = f"{condition!r} reads {token}, which this test cannot know"
        raise ValueError(msg)

    def comparison() -> str | bool:
        left = operand()
        if peek() in {"==", "!="}:
            equal = take() == "=="
            right = operand()
            same = str(left).casefold() == str(right).casefold()
            return same if equal else not same
        return left

    def both() -> str | bool:
        value = comparison()
        while peek() == "&&":
            take()
            right = comparison()
            value = right if value else value
        return value

    def either() -> str | bool:
        value = both()
        while peek() == "||":
            take()
            right = both()
            value = value or right
        return value

    result = either()
    if at != len(tokens):
        msg = f"cannot read {' '.join(tokens[at:])!r} in {condition!r}"
        raise ValueError(msg)
    return bool(result)


def test_the_event_reader_follows_the_conditions_the_workflows_write() -> None:
    """The reader of ``if:`` gives each event the answer GitHub would."""
    assert _runs_on(None, "push")
    assert not _runs_on("github.event_name != 'pull_request'", "pull_request")
    assert _runs_on("${{ github.event_name != 'pull_request' }}", "workflow_dispatch")
    assert not _runs_on("github.event_name == 'push'", "workflow_dispatch")
    assert _runs_on("github.event_name == 'PUSH'", "push")
    condition = "!(github.event_name == 'push' || github.event_name == 'schedule')"
    assert _runs_on(condition, "workflow_dispatch")
    assert not _runs_on(condition, "push")
    assert not _runs_on("success() && github.event_name == 'push'", "pull_request")
    held = "github.event_name == 'push' && vars.HOLD != 'true'"
    assert _runs_on(held, "push", {})
    assert _runs_on(held, "push", {"HOLD": "false"})
    assert not _runs_on(held, "push", {"HOLD": "True"})
    assert not _runs_on(held, "pull_request", {})
    on_main = "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'"
    assert _runs_on(on_main, "workflow_dispatch", ref="refs/heads/main")
    assert not _runs_on(on_main, "workflow_dispatch", ref="refs/heads/feature")
    assert not _runs_on(on_main, "pull_request", ref="refs/heads/main")
    with pytest.raises(
        ValueError, match=r"reads github\.ref, which this test cannot know"
    ):
        _runs_on(on_main, "workflow_dispatch")
    for unknown in (
        "steps.found.outputs.run-id != ''",
        "always()",
        "github.ref == 'x'",
        "vars.HOLD != 'true'",
    ):
        with pytest.raises(ValueError, match="which this test cannot know"):
            _runs_on(unknown, "push")


def _steps_running(
    steps: list[dict[str, object]], command: str
) -> list[tuple[int, dict[str, object]]]:
    """The steps whose ``run:`` holds *command*, with their positions."""
    return [
        (index, step)
        for index, step in enumerate(steps)
        if command in str(step.get("run", ""))
    ]


def _steps_using(
    steps: list[dict[str, object]], action: str, name: str
) -> list[tuple[int, dict[str, object]]]:
    """The steps that use *action* on the artifact *name*, with their positions."""
    found = []
    for index, step in enumerate(steps):
        inputs = step.get("with")
        if (
            str(step.get("uses", "")).startswith(f"{action}@")
            and isinstance(inputs, dict)
            and inputs.get("name") == name
        ):
            found.append((index, step))
    return found


def _the_one(
    found: list[tuple[int, dict[str, object]]], what: str
) -> tuple[int, dict[str, object]]:
    assert len(found) == 1, f"docs.yml has {len(found)} steps that {what}"
    return found[0]


def _shell_path(path: object) -> str:
    """A path as a ``run:`` and a ``with:`` input would both spell it."""
    return str(path).replace("${{ runner.temp }}", "$RUNNER_TEMP").rstrip("/")


def _of_this_run(step: dict[str, object]) -> bool:
    """Whether a download step takes an artifact of this run, naming no other run."""
    inputs = step.get("with")
    return isinstance(inputs, dict) and "run-id" not in inputs


def _needs(job: dict[str, object]) -> set[str]:
    """The jobs a job waits for, whether ``needs:`` names one or a list."""
    needs = job.get("needs")
    if isinstance(needs, str):
        return {needs}
    return {str(name) for name in needs} if isinstance(needs, list) else set()


#: The job of docs.yml that deploys the pages a run built: a call of
#: site-deploy.yml, which serves them on phonometry.dev. No other job of the
#: workflow deploys anything.
_DEPLOY = "deploy-site"


def _site_deploy_job() -> tuple[str, dict[str, object]]:
    """The one job of site-deploy.yml, by name: the steps the call runs."""
    deploy = yaml.safe_load(_SITE_DEPLOY_WORKFLOW.read_text(encoding="utf-8"))
    jobs: dict[str, dict[str, object]] = deploy["jobs"]
    assert len(jobs) == 1, "site-deploy.yml deploys in one job"
    [(name, job)] = jobs.items()
    return name, job


def test_every_deploying_event_tells_indexnow_the_pages_it_changed() -> None:
    """A deploy dispatched by hand or by jmrp.io is compared like a push.

    The IndexNow submission cannot run on a pull request, so nothing but this
    test shows that the steps behind it run on every event that deploys: the
    one that finds the record of the pages IndexNow was last sent, the one
    that downloads it, the comparison, the hand-over of its list to the
    IndexNow job, and in that job the steps that take the list, submit it and
    keep the record. A step limited to ``push`` would leave a dispatched
    deploy with no list, or with every URL of the site, or with a record of
    pages it never sent, and still deploy green. They run in the order the
    record needs, and none of them, nor any of the three jobs, lets the run go
    on past a failure: a comparison made before the record is downloaded
    sends every URL on every deploy, and a submission that fails quietly
    keeps a record of pages the engines were never told about. The download
    of the record is the one step of these that goes on (the list a later
    deploy handed, read beside it, goes on too, and has a test of its own): a
    record that expired, was deleted or cannot be downloaded is not a reason
    to stop the deploy, so what it left is set aside and the full list goes
    out, as it does with no record at all, with a warning on the run. The record has
    to travel too: the IndexNow job keeps the manifest it was handed, only
    once its submission went through, under the name the build looks for, in
    the folder the comparison reads, and the build may read it from an
    earlier run. And the job keeps it only while no deploy has gone out
    after its run's, which it learns from the moment the deploy job wrote: a
    failed job re-run after a newer deploy would otherwise put back an older
    manifest, and a page that deploy added and the next one removes would
    never be sent as removed.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow[True] if True in workflow else workflow["on"]
    assert set(_DEPLOYING_EVENTS) <= set(triggers), (
        f"docs.yml deploys on {_DEPLOYING_EVENTS}, and its triggers are {sorted(triggers)}"
    )
    jobs: dict[str, dict[str, object]] = workflow["jobs"]
    build: list[dict[str, object]] = workflow["jobs"]["build"]["steps"]
    indexnow: list[dict[str, object]] = workflow["jobs"]["indexnow"]["steps"]
    script = _INDEXNOW_SCRIPT.read_text(encoding="utf-8")
    record = re.search(r"export const SUBMITTED_ARTIFACT = '([^']+)'", script)
    assert record, "indexnow-diff.mjs names no SUBMITTED_ARTIFACT"
    submitted = record.group(1)
    environment = re.search(r"export const PAGES_ENVIRONMENT = '([^']+)'", script)
    assert environment, "indexnow-diff.mjs names no PAGES_ENVIRONMENT"

    built_at, _ = _the_one(_steps_running(build, "pnpm build"), "build the site")
    find_at, find = _the_one(
        _steps_running(build, "indexnow-diff.mjs last-submitted"),
        "find the record of the last submission",
    )
    fetch_at, fetch = _the_one(
        _steps_using(build, "actions/download-artifact", submitted),
        f"download {submitted}",
    )
    compare_at, compare = _the_one(
        _steps_running(build, "indexnow-diff.mjs diff"), "compare the manifests"
    )
    hand_at, hand = _the_one(
        _steps_using(build, "actions/upload-artifact", "indexnow-urls"),
        "hand the list to the IndexNow job",
    )
    received_at, download = _the_one(
        [
            (index, step)
            for index, step in _steps_using(
                indexnow, "actions/download-artifact", "indexnow-urls"
            )
            if _of_this_run(step)
        ],
        "take the list in the IndexNow job",
    )
    sent_at, submit = _the_one(
        _steps_running(indexnow, "api.indexnow.org"), "submit to IndexNow"
    )
    kept_at, keep = _the_one(
        _steps_using(indexnow, "actions/upload-artifact", submitted),
        f"keep {submitted}",
    )
    checked_at, check = _the_one(
        _steps_running(indexnow, "indexnow-diff.mjs keep-record"),
        "check that no deploy went out after this run's",
    )

    # The record is kept only once the submission went through, and only
    # when the check says no deploy has gone out after this run's. A
    # condition with no status function runs only when every step before it
    # succeeded.
    checker = check.get("id")
    assert keep.get("if") == f"steps.{checker}.outputs.keep == 'true'", (
        "a record kept whatever the check says can replace a newer deploy's"
    )

    # Every step the pages go through runs on every event that deploys. The
    # download of the record is held to the step that names its run instead,
    # below, which is what it waits for on any event.
    on_every_event = {
        "finding": find,
        "comparing": compare,
        "handing": hand,
        "receiving": download,
        "submitting": submit,
        "checking": check,
    }
    for event in _DEPLOYING_EVENTS:
        for what, step in on_every_event.items():
            assert _runs_on(step.get("if"), event), f"the {what} step skips {event}"
        for job in ("build", _DEPLOY, "indexnow"):
            assert _runs_on(jobs[job].get("if"), event, {}, "refs/heads/main"), (
                f"the {job} job skips {event}"
            )
    assert _runs_on(compare.get("if"), "pull_request"), (
        "a pull request no longer prints what its merge would send"
    )
    assert not _runs_on(hand.get("if"), "pull_request")

    # A failure anywhere on the way stops the run before the record is kept,
    # but for the download of the record, held below to going on.
    for what, step in {**on_every_event, "keeping": keep}.items():
        assert not step.get("continue-on-error"), (
            f"a failure of the {what} step lets its job go on, "
            "so a record can be kept of pages that were not sent"
        )
    for job in ("build", _DEPLOY, "indexnow"):
        assert not jobs[job].get("continue-on-error"), (
            f"a failure of the {job} job lets the run go on, "
            "so a record can be kept of pages that were not sent"
        )

    # In the order the record needs: the build writes the manifest, the run
    # of the record is found, the record fetched, the manifests compared and
    # the list handed over; the IndexNow job waits for the deploy, takes the
    # list, submits it and only then keeps the record.
    assert find_at < fetch_at, (
        "the record is fetched before the step that names its run, so it never is"
    )
    assert fetch_at < compare_at, (
        "the comparison runs before the record is fetched, "
        "so every deploy sends the full list"
    )
    assert built_at < compare_at, (
        "the comparison runs before the build wrote the manifest"
    )
    assert compare_at < hand_at, (
        "the list is handed over before the comparison wrote it"
    )
    assert "build" in _needs(jobs[_DEPLOY])
    assert _DEPLOY in _needs(jobs["indexnow"]), "IndexNow is told before the deploy"
    assert received_at < sent_at, "the submission runs before the list is taken"
    assert sent_at < checked_at < kept_at, (
        "the record is kept before the submission went through, or unchecked"
    )

    # The record is fetched from the run the finding step names, whatever
    # event this run is, and the build is allowed to read it.
    finder = find.get("id")
    assert fetch.get("if") == f"steps.{finder}.outputs.run-id != ''"
    inputs = fetch["with"]
    assert isinstance(inputs, dict)
    assert inputs.get("run-id") == f"${{{{ steps.{finder}.outputs.run-id }}}}"
    assert inputs.get("github-token"), "another run's artifact needs a token"

    # A record that cannot be downloaded does not stop the deploy: the
    # download goes on past its failure, and the step after it, which runs
    # only then, takes away whatever the download left, so the comparison
    # finds no record and the full list goes out.
    fetcher = fetch.get("id")
    assert fetcher, (
        "the download of the record has no id for a step to read its outcome by"
    )
    assert fetch.get("continue-on-error") is True, (
        "a record that expired, was deleted or cannot be downloaded stops the build, "
        "and with it the deploy, where the full list should go out"
    )
    discard_at, discard = _the_one(
        [
            (index, step)
            for index, step in enumerate(build)
            if step.get("if") == f"steps.{fetcher}.outcome == 'failure'"
        ],
        "set aside a record that could not be downloaded",
    )
    assert fetch_at < discard_at < compare_at, (
        "what a failed download left is set aside after the comparison read it"
    )
    removal = f'rm -rf "{_shell_path(inputs["path"])}"'
    assert removal in " ".join(str(discard.get("run", "")).split()), (
        f"the step after a failed download does not run {removal}, "
        "so the comparison can read a part of the record"
    )
    assert "::warning::" in str(discard.get("run", "")), (
        "a record that could not be downloaded sends the full list with no word on the run"
    )
    assert not discard.get("continue-on-error")
    permissions = jobs["build"].get("permissions")
    assert isinstance(permissions, dict)
    assert permissions.get("actions") == "read"
    finder_env = find.get("env")
    assert isinstance(finder_env, dict)
    assert finder_env.get("GITHUB_TOKEN")

    # The check places this run's deploy among the deployments of the site:
    # it reads the moment the deploy job wrote once its pages went out, in a
    # step after the Worker went live, from the environment the script lists,
    # with a token that may list the deployments. The deploy is a call of
    # site-deploy.yml, so its steps and its environment are that job's.
    _, deploy_job = _site_deploy_job()
    deploy_steps: list[dict[str, object]] = deploy_job["steps"]  # type: ignore[assignment]
    deployed_at, _ = _the_one(
        [
            (index, step)
            for index, step in enumerate(deploy_steps)
            if str(step.get("name", "")).startswith("Deploy the Worker")
        ],
        "deploy the pages",
    )
    clock_outputs = deploy_job.get("outputs")
    assert isinstance(clock_outputs, dict)
    clock_output = re.fullmatch(
        r"\$\{\{ steps\.([\w-]+)\.outputs\.(\w+) \}\}",
        str(clock_outputs.get("deployed-at")),
    )
    assert clock_output, "the deploy job writes no deployed-at output"
    clock_at, clock = _the_one(
        [
            (index, step)
            for index, step in enumerate(deploy_steps)
            if step.get("id") == clock_output.group(1)
        ],
        "write the moment the pages went out",
    )
    assert deployed_at < clock_at, "the moment is taken before the pages went out"
    clock_command = f"{clock_output.group(2)}=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    assert clock_command in str(clock["run"]), clock["run"]
    environment_of = deploy_job.get("environment")
    assert isinstance(environment_of, dict)
    assert environment_of.get("name") == environment.group(1), (
        "the check lists the deployments of another environment than the deploy's"
    )
    check_env = check.get("env")
    assert isinstance(check_env, dict)
    assert check_env.get("GITHUB_TOKEN")
    moment = re.search(r'--deployed-at "\$(\w+)"', " ".join(str(check["run"]).split()))
    assert moment, check["run"]
    assert check_env.get(moment.group(1)) == (
        f"${{{{ needs.{_DEPLOY}.outputs.deployed-at }}}}"
    )
    indexnow_permissions = jobs["indexnow"].get("permissions")
    assert isinstance(indexnow_permissions, dict)
    assert indexnow_permissions.get("deployments") == "read"

    # The comparison reads the record where it was downloaded, and writes the
    # list and the manifest where the hand-over takes them from.
    command = " ".join(str(compare["run"]).split())
    previous = re.search(r'--previous "?([^"\s]+)', command)
    out = re.search(r'--out "?([^"\s]+)', command)
    assert previous, command
    assert out, command
    assert previous.group(1) == f"{_shell_path(inputs['path'])}/indexnow-manifest.json"
    handed = hand["with"]
    assert isinstance(handed, dict)
    assert _shell_path(handed["path"]) == out.group(1)

    # The IndexNow job keeps the manifest it was handed, under the name the
    # build looks for.
    kept_inputs = keep["with"]
    downloaded = download["with"]
    assert isinstance(kept_inputs, dict)
    assert isinstance(downloaded, dict)
    assert kept_inputs["path"] == f"{downloaded['path']}/indexnow-manifest.json"


def test_the_build_reads_the_list_a_deploy_after_the_record_handed_indexnow() -> None:
    """A page a deploy submitted with no record kept, and the next one removed, is sent as removed.

    The IndexNow job can submit and keep no record: the deployments cannot be
    listed, a newer push cancels the run before the record, its upload
    fails, or IndexNow takes the submission and the step fails after it. A
    page that deploy added and the next one removes is then in no record, so
    the build downloads the list the newest deploy after the record handed
    its IndexNow job, from the run the finding step names, and the comparison
    reads it. The list is kept as long as a record is, so it outlives any gap
    a record covers, and like the record a list that cannot be downloaded is
    set aside with a warning instead of stopping the deploy.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    build: list[dict[str, object]] = workflow["jobs"]["build"]["steps"]
    indexnow: list[dict[str, object]] = workflow["jobs"]["indexnow"]["steps"]
    script = _INDEXNOW_SCRIPT.read_text(encoding="utf-8")
    handed_name = re.search(r"export const HANDED_ARTIFACT = '([^']+)'", script)
    record_name = re.search(r"export const SUBMITTED_ARTIFACT = '([^']+)'", script)
    assert handed_name, "indexnow-diff.mjs names no HANDED_ARTIFACT"
    assert record_name, "indexnow-diff.mjs names no SUBMITTED_ARTIFACT"

    find_at, find = _the_one(
        _steps_running(build, "indexnow-diff.mjs last-submitted"),
        "find the record of the last submission",
    )
    compare_at, compare = _the_one(
        _steps_running(build, "indexnow-diff.mjs diff"), "compare the manifests"
    )
    _, hand = _the_one(
        _steps_using(build, "actions/upload-artifact", handed_name.group(1)),
        "hand the list to the IndexNow job",
    )
    _, keep = _the_one(
        _steps_using(indexnow, "actions/upload-artifact", record_name.group(1)),
        "keep the record",
    )
    pending_at, pending = _the_one(
        _steps_using(build, "actions/download-artifact", handed_name.group(1)),
        "download the list a deploy after the record handed IndexNow",
    )

    finder = find.get("id")
    assert pending.get("if") == f"steps.{finder}.outputs.pending-run-id != ''"
    inputs = pending["with"]
    assert isinstance(inputs, dict)
    assert inputs.get("run-id") == f"${{{{ steps.{finder}.outputs.pending-run-id }}}}"
    assert inputs.get("github-token"), "another run's artifact needs a token"
    assert pending.get("continue-on-error") is True, (
        "a list that expired or cannot be downloaded stops the deploy"
    )
    assert find_at < pending_at < compare_at, (
        "the list is read before the step that names its run, or after the comparison"
    )
    puller = pending.get("id")
    assert puller, (
        "the download of the list has no id for a step to read its outcome by"
    )
    discard_at, discard = _the_one(
        [
            (index, step)
            for index, step in enumerate(build)
            if step.get("if") == f"steps.{puller}.outcome == 'failure'"
        ],
        "set aside a list that could not be downloaded",
    )
    assert pending_at < discard_at < compare_at
    removal = f'rm -rf "{_shell_path(inputs["path"])}"'
    assert removal in " ".join(str(discard.get("run", "")).split())
    assert "::warning::" in str(discard.get("run", ""))

    command = " ".join(str(compare["run"]).split())
    read = re.search(r'--pending "?([^"\s]+)', command)
    assert read, f"the comparison reads no handed list: {command}"
    assert read.group(1) == _shell_path(inputs["path"])

    def kept_days(step: dict[str, object]) -> int:
        given = step["with"]
        assert isinstance(given, dict)
        return int(str(given.get("retention-days", 90)))

    assert kept_days(hand) >= kept_days(keep), (
        "the list a deploy hands IndexNow expires before the record it stands in for"
    )


#: The condition the steps of a deploy re-run in the IndexNow job run on: the
#: deploy job ran in another attempt than the build. A re-run runs a job again
#: with every job that needs it, so the deploy job never runs in an earlier
#: attempt than the build it needs, and another attempt is a later one.
_DEPLOY_RE_RUN = f"needs.{_DEPLOY}.outputs.attempt != needs.build.outputs.attempt"


def test_a_deploy_re_run_works_its_list_out_again_against_the_newest_record() -> None:
    """A deploy job re-run after a newer deploy sends what its pages change on the site.

    "Re-run failed jobs" on a run whose deploy failed runs the deploy job and
    the IndexNow job again, and the build keeps its outputs and its list. The
    deploy puts this run's pages back on the site after whatever deploy went
    out since, and the list was worked out before that deploy, against the
    record of the build's time. So both jobs say which attempt they ran in,
    and when the deploy's is another than the build's, the IndexNow job finds
    the newest record and the newest list handed on after it, its own run's
    left out, downloads both from the runs the finding step names, as the
    build does, sets aside one that cannot be downloaded, works the list out
    again over the one it was handed, and hands it on beside the build's
    before it submits it: the build's list is older than the record it was
    compared with, so no later build reads it, and a job that submits and
    keeps no record would leave the pages it sent to no one. It deletes no
    list to make room for its own: a list replaced (``overwrite``) is deleted
    before its replacement is uploaded, and an upload that failed in between,
    on a re-run of this job alone after one that submitted and kept no
    record, would leave the run with no list of the pages that job sent. On
    any other run none of those steps runs, and the job may read another
    run's artifacts only for them.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    jobs: dict[str, dict[str, object]] = workflow["jobs"]
    indexnow: list[dict[str, object]] = workflow["jobs"]["indexnow"]["steps"]
    script = _INDEXNOW_SCRIPT.read_text(encoding="utf-8")
    handed_name = re.search(r"export const HANDED_ARTIFACT = '([^']+)'", script)
    record_name = re.search(r"export const SUBMITTED_ARTIFACT = '([^']+)'", script)
    assert handed_name, "indexnow-diff.mjs names no HANDED_ARTIFACT"
    assert record_name, "indexnow-diff.mjs names no SUBMITTED_ARTIFACT"

    _, deploy_job = _site_deploy_job()
    for job, where in ((jobs["build"], "build"), (deploy_job, "deploy")):
        outputs = job.get("outputs")
        assert isinstance(outputs, dict), f"the {where} job has no outputs"
        assert outputs.get("attempt") == "${{ github.run_attempt }}", (
            f"the {where} job does not say which attempt it ran in"
        )
    assert {"build", _DEPLOY} <= _needs(jobs["indexnow"]), (
        "the IndexNow job cannot read the attempts of the build and the deploy"
    )
    permissions = jobs["indexnow"].get("permissions")
    assert isinstance(permissions, dict)
    assert permissions.get("actions") == "read", (
        "the IndexNow job cannot list or download another run's artifacts"
    )

    received_at, received = _the_one(
        [
            (index, step)
            for index, step in _steps_using(
                indexnow, "actions/download-artifact", handed_name.group(1)
            )
            if _of_this_run(step)
        ],
        "take the list in the IndexNow job",
    )
    received_inputs = received["with"]
    assert isinstance(received_inputs, dict)
    folder = _shell_path(received_inputs["path"])

    # The newest record and the newest list after it, this run's left out.
    find_at, find = _the_one(
        _steps_running(indexnow, "indexnow-diff.mjs last-submitted"),
        "find the newest record on a deploy re-run",
    )
    assert find.get("if") == _DEPLOY_RE_RUN, (
        "the IndexNow job looks for the newest record on a run that is no deploy re-run, or never"
    )
    assert '--except-run "$GITHUB_RUN_ID"' in " ".join(str(find["run"]).split()), (
        "the IndexNow job reads its own run's list as the newest one handed on"
    )
    finder_env = find.get("env")
    assert isinstance(finder_env, dict)
    assert finder_env.get("GITHUB_TOKEN")
    finder = find.get("id")
    assert finder

    def downloaded(
        name: str, output: str, what: str
    ) -> tuple[int, int, dict[str, object]]:
        """The download of *name* from the run the finding step names as *output*, and the step that sets it aside."""
        fetch_at, fetch = _the_one(
            [
                (index, step)
                for index, step in _steps_using(
                    indexnow, "actions/download-artifact", name
                )
                if not _of_this_run(step)
            ],
            f"download {what} on a deploy re-run",
        )
        assert fetch.get("if") == f"steps.{finder}.outputs.{output} != ''"
        inputs = fetch["with"]
        assert isinstance(inputs, dict)
        assert inputs.get("run-id") == f"${{{{ steps.{finder}.outputs.{output} }}}}"
        assert inputs.get("github-token"), "another run's artifact needs a token"
        assert fetch.get("continue-on-error") is True, (
            f"{what} that cannot be downloaded stops the IndexNow job"
        )
        fetcher = fetch.get("id")
        assert fetcher
        discard_at, discard = _the_one(
            [
                (index, step)
                for index, step in enumerate(indexnow)
                if step.get("if") == f"steps.{fetcher}.outcome == 'failure'"
            ],
            f"set aside {what} that could not be downloaded",
        )
        path = _shell_path(inputs["path"])
        assert f'rm -rf "{path}"' in " ".join(str(discard.get("run", "")).split())
        assert "::warning::" in str(discard.get("run", ""))
        return fetch_at, discard_at, {"path": path}

    fetch_at, record_set_aside_at, record = downloaded(
        record_name.group(1), "run-id", "the record"
    )
    pending_at, list_set_aside_at, pending = downloaded(
        handed_name.group(1), "pending-run-id", "the list handed on after it"
    )

    # The list worked out again over the one the build handed on, which the
    # job submits and whose manifest it keeps.
    again_at, again = _the_one(
        _steps_running(indexnow, "indexnow-diff.mjs diff"),
        "work the list out again on a deploy re-run",
    )
    assert again.get("if") == _DEPLOY_RE_RUN, (
        "the IndexNow job works its list out again on a run that is no deploy re-run, or never"
    )
    command = " ".join(str(again["run"]).split())
    for option, path in {
        "--current": f"{folder}/indexnow-manifest.json",
        "--previous": f"{record['path']}/indexnow-manifest.json",
        "--pending": pending["path"],
        "--out": folder,
    }.items():
        given = re.search(rf'{option} "?([^"\s]+)', command)
        assert given, f"the comparison of a deploy re-run gives no {option}: {command}"
        assert given.group(1) == path, command
    sent_at, submit = _the_one(
        _steps_running(indexnow, "api.indexnow.org"), "submit to IndexNow"
    )
    assert f"{folder}/urls.json" in str(submit["run"]), (
        "the submission reads another list than the one worked out again"
    )
    assert (
        received_at
        < find_at
        < fetch_at
        < record_set_aside_at
        < pending_at
        < list_set_aside_at
        < again_at
        < sent_at
    ), "the list is worked out again out of order, or after the submission"

    # The list worked out again is handed on before the submission, beside
    # the ones the run handed on before, as long as a record is kept, so the
    # next build reads it when this job submits and keeps no record, and a
    # later attempt of this job downloads it, the run's newest, with the
    # manifest it keeps.
    hand_at, hand = _the_one(
        _steps_using(indexnow, "actions/upload-artifact", handed_name.group(1)),
        "hand the list worked out again on",
    )
    assert hand.get("if") == _DEPLOY_RE_RUN, (
        "the IndexNow job hands its list on on a run that is no deploy re-run, or never"
    )
    hand_inputs = hand["with"]
    assert isinstance(hand_inputs, dict)
    assert _shell_path(hand_inputs["path"]) == folder, (
        "the IndexNow job hands on another list than the one it worked out again"
    )
    assert hand_inputs.get("overwrite") in (None, False, "false"), (
        "the list worked out again deletes the one the run handed on before it is "
        "uploaded, so an upload that fails in between leaves the run with neither"
    )
    assert hand_inputs.get("if-no-files-found") == "error"
    _, keep = _the_one(
        _steps_using(indexnow, "actions/upload-artifact", record_name.group(1)),
        "keep the record",
    )
    keep_inputs = keep["with"]
    assert isinstance(keep_inputs, dict)
    assert int(str(hand_inputs.get("retention-days", 90))) >= int(
        str(keep_inputs.get("retention-days", 90))
    ), "the list handed on expires before the record it stands in for"
    assert again_at < hand_at < sent_at, (
        "the list is handed on before it is worked out again, or after the submission"
    )
    for step in (find, again, hand):
        assert not step.get("continue-on-error")


def _workflow_steps(
    root: pathlib.Path | None = None,
) -> Iterator[tuple[str, str, dict[str, object]]]:
    """Every step of every workflow, as ``(file, job, step)``."""
    for path in _workflow_files(root):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_id, job in (workflow.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                yield path.name, str(job_id), step


#: An HTTP DELETE as curl, gh api, wget and PowerShell spell it: ``-X DELETE``,
#: ``-XDELETE``, ``--request DELETE``, ``--method=DELETE``, ``-Method Delete``.
_DELETE_METHOD = re.compile(
    r"(?:-X\s*|--request[=\s]+|--method[=\s]+|-Method\s+)['\"]?DELETE\b", re.IGNORECASE
)

#: Where a deletion names the artifacts of the API: the REST path, or the
#: method of the client ``actions/github-script`` hands its script.
_ARTIFACTS_ENDPOINT = re.compile(r"actions/artifacts")
_SCRIPT_DELETES = re.compile(
    r"\bdeleteArtifact\b|DELETE\s+/repos/[^\s'\"]*/actions/artifacts", re.IGNORECASE
)


def _logical_commands(run: str) -> list[str]:
    """The commands of a ``run:``, a line continued with a backslash joined to the next."""
    return re.sub(r"\\[ \t]*\r?\n", " ", run).splitlines()


def _deletes_an_artifact(step: dict[str, object]) -> str | None:
    """How a step deletes an artifact, or None when it deletes none.

    By the ``overwrite`` input of ``actions/upload-artifact``, by an action
    that deletes artifacts, by a command of its ``run:`` that sends DELETE
    to the artifacts endpoint, or by a script of ``actions/github-script``
    that calls the API's deleteArtifact.
    """
    uses = str(step.get("uses", ""))
    inputs = step.get("with")
    given = inputs if isinstance(inputs, dict) else {}
    if uses.startswith("actions/upload-artifact@") and given.get("overwrite") not in (
        None,
        False,
        "false",
    ):
        return "overwrite"
    if "delete-artifact" in uses:
        return uses
    for command in _logical_commands(str(step.get("run", ""))):
        if _DELETE_METHOD.search(command) and _ARTIFACTS_ENDPOINT.search(command):
            return "an API call that deletes an artifact"
    if _SCRIPT_DELETES.search(str(given.get("script", ""))):
        return "a script that deletes an artifact through the API"
    return None


def test_no_workflow_deletes_an_artifact_before_its_replacement_exists() -> None:
    """A step hands an artifact on beside the one before, never in its place.

    ``overwrite`` on ``actions/upload-artifact`` deletes the run's newest
    artifact of the name and then uploads, with nothing between to put the
    old one back: an upload that fails there leaves the run with neither.
    The IndexNow job of a deploy re-run handed its list on so, and a re-run
    of that job alone, after one that submitted and kept no record, could
    delete the only list of the pages that job sent and hand on none, so no
    later deploy would send a page it removed from them. A run keeps the
    artifacts of every attempt and its readers take the newest of a name, so
    no step deletes one, by that input, by an action that deletes artifacts,
    or through the API, from a command or from a script.
    """
    deleting = [
        f"{name}, job {job}, step {step.get('name') or step.get('uses')}: {how}"
        for name, job, step in _workflow_steps()
        if (how := _deletes_an_artifact(step)) is not None
    ]
    assert deleting == [], (
        "these steps delete an artifact before its replacement is uploaded, so a "
        f"failure in between leaves the run with neither: {deleting}"
    )


@pytest.mark.parametrize(
    ("step", "how"),
    [
        (
            {
                "uses": "actions/upload-artifact@v7",
                "with": {"name": "a", "overwrite": True},
            },
            "overwrite",
        ),
        ({"uses": "geekyeggo/delete-artifact@v5"}, "geekyeggo/delete-artifact@v5"),
        (
            {"run": 'gh api -X DELETE "repos/o/r/actions/artifacts/${ID}"'},
            "an API call that deletes an artifact",
        ),
        (
            {
                "run": 'gh api \\\n  -X DELETE \\\n  "repos/o/r/actions/artifacts/${ID}"\n'
            },
            "an API call that deletes an artifact",
        ),
        (
            {"run": 'gh api --method=DELETE "repos/o/r/actions/artifacts/${ID}"'},
            "an API call that deletes an artifact",
        ),
        (
            {
                "run": 'curl -XDELETE -H "Authorization: x" "$API/repos/o/r/actions/artifacts/$ID"'
            },
            "an API call that deletes an artifact",
        ),
        (
            {"run": 'curl --request DELETE "$API/repos/o/r/actions/artifacts/$ID"'},
            "an API call that deletes an artifact",
        ),
        (
            {
                "run": 'Invoke-RestMethod -Method Delete -Uri "$api/actions/artifacts/$id"'
            },
            "an API call that deletes an artifact",
        ),
        (
            {
                "uses": "actions/github-script@v8",
                "with": {
                    "script": "await github.rest.actions.deleteArtifact({owner, repo, artifact_id})"
                },
            },
            "a script that deletes an artifact through the API",
        ),
        (
            {
                "uses": "actions/github-script@v8",
                "with": {
                    "script": "await github.request('DELETE /repos/{owner}/{repo}/actions/artifacts/{id}')"
                },
            },
            "a script that deletes an artifact through the API",
        ),
    ],
)
def test_each_way_a_step_deletes_an_artifact_is_found(
    step: dict[str, object], how: str
) -> None:
    """A step that deletes an artifact, whichever way it is written."""
    assert _deletes_an_artifact(step) == how


@pytest.mark.parametrize(
    "step",
    [
        {"uses": "actions/upload-artifact@v7", "with": {"name": "a"}},
        {
            "uses": "actions/upload-artifact@v7",
            "with": {"name": "a", "overwrite": "false"},
        },
        {"run": 'gh api "repos/o/r/actions/artifacts" --jq ".artifacts[].name"'},
        {"run": 'gitlab_request DELETE "$link"'},
        {"run": 'gh api -X DELETE "repos/o/r/git/refs/tags/x"\necho actions/artifacts'},
    ],
)
def test_a_step_that_deletes_no_artifact_passes(step: dict[str, object]) -> None:
    """An upload that keeps the one before, a read of the list, a DELETE of something else."""
    assert _deletes_an_artifact(step) is None


def test_a_workflow_written_as_yaml_is_read(tmp_path: pathlib.Path) -> None:
    """GitHub runs ``.yaml`` workflows too, so the steps of one are read."""
    folder = tmp_path / ".github" / "workflows"
    folder.mkdir(parents=True)
    (folder / "deploy.yaml").write_text(
        "jobs:\n  a:\n    steps:\n      - name: caught\n"
        '        run: gh api -X DELETE "repos/o/r/actions/artifacts/1"\n',
        encoding="utf-8",
    )
    steps = list(_workflow_steps(tmp_path))
    assert [(name, job, step.get("name")) for name, job, step in steps] == [
        ("deploy.yaml", "a", "caught")
    ]
    assert _deletes_an_artifact(steps[0][2]) == "an API call that deletes an artifact"


def _input_of(step: dict[str, object], name: str, default: str) -> str:
    """The input *name* a step gives its action, or the action's *default*."""
    inputs = step.get("with")
    return str((inputs if isinstance(inputs, dict) else {}).get(name, default))


def test_the_deploy_takes_the_pages_of_the_build_it_needs() -> None:
    """A build re-run hands the deploy its own pages, under a name of its attempt.

    A run keeps the artifacts of every attempt, and a later attempt may
    upload one of a name an earlier attempt used. The pages a build hands the
    deploy went under the one name ``actions/upload-pages-artifact`` gives
    them unless told otherwise, so a build re-run in a later attempt ("Re-run
    all jobs") uploaded a second artifact of that name, and a download by
    that name finds two. The build names its pages after the attempt it ran
    in; the call of the deploy hands site-deploy.yml the attempt the build it
    needs ran in, which a re-run of the deploy job alone reads too, and
    every download there takes the pages of that attempt.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    jobs: dict[str, dict[str, object]] = workflow["jobs"]
    build: list[dict[str, object]] = workflow["jobs"]["build"]["steps"]
    _, upload = _the_one(
        [
            (index, step)
            for index, step in enumerate(build)
            if str(step.get("uses", "")).startswith("actions/upload-pages-artifact@")
        ],
        "hand the pages to the deploy",
    )
    attempt = "${{ github.run_attempt }}"
    outputs = jobs["build"].get("outputs")
    assert isinstance(outputs, dict)
    assert outputs.get("attempt") == attempt, (
        "the build job does not say which attempt it ran in"
    )
    assert "build" in _needs(jobs[_DEPLOY])
    uploaded = _input_of(upload, "name", "github-pages")
    assert attempt in uploaded, (
        f"the pages go under {uploaded!r}, a name that does not change with the "
        "attempt, so a build re-run leaves the run two artifacts of it"
    )
    given = jobs[_DEPLOY].get("with")
    assert isinstance(given, dict)
    assert given.get("attempt") == "${{ needs.build.outputs.attempt }}", (
        "the deploy is not told the attempt the build it needs ran in"
    )
    _, deploy_job = _site_deploy_job()
    steps: list[dict[str, object]] = deploy_job["steps"]  # type: ignore[assignment]
    downloads = [
        step
        for step in steps
        if str(step.get("uses", "")).startswith("actions/download-artifact@")
    ]
    assert downloads, "site-deploy.yml downloads no pages"
    of_the_build = uploaded.replace(attempt, "${{ inputs.attempt }}")
    for step in downloads:
        assert _input_of(step, "name", "") == of_the_build, (
            f"a download takes {_input_of(step, 'name', '')!r}, and the build "
            f"hands its pages on as {uploaded!r}"
        )


def test_only_phonometry_dev_is_deployed_and_indexnow_waits_for_the_hold() -> None:
    """The run that builds the site deploys it to phonometry.dev and nowhere else.

    GitHub Pages served the build under docs.jmrp.io/phonometry/; a build at
    the root published there would be served under that base with every
    link and asset pointing at the root of docs.jmrp.io, so no job of
    docs.yml deploys Pages any more, and none asks for the permissions a
    Pages deploy needs. The last Pages deployment stays published as it was.
    The IndexNow job announces phonometry.dev only while the repository
    variable ``INDEXNOW_HOLD`` is not ``true``: it is set before the root
    build is merged and cleared once the site is proven and the old addresses
    answer their permanent redirects, so nothing is announced that could
    answer 404 after a rollback.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    jobs: dict[str, dict[str, object]] = workflow["jobs"]
    for name, job in jobs.items():
        for step in job.get("steps", []) or []:  # type: ignore[union-attr]
            uses = str(step.get("uses", ""))
            assert not uses.startswith("actions/deploy-pages@"), (
                f"the {name} job deploys GitHub Pages"
            )
        permissions = job.get("permissions")
        if isinstance(permissions, dict):
            assert "pages" not in permissions, f"the {name} job may write Pages"
            assert "id-token" not in permissions, (
                f"the {name} job asks for an OIDC token, which only a Pages deploy needed"
            )
        environment = job.get("environment")
        name_of = (
            environment.get("name") if isinstance(environment, dict) else environment
        )
        assert name_of != "github-pages", f"the {name} job deploys to github-pages"
    indexnow = jobs["indexnow"]
    for event in _DEPLOYING_EVENTS:
        for unheld in ({}, {"INDEXNOW_HOLD": "false"}):
            assert _runs_on(indexnow.get("if"), event, unheld), (
                f"IndexNow is not told on {event} with {unheld}"
            )
        assert not _runs_on(indexnow.get("if"), event, {"INDEXNOW_HOLD": "true"}), (
            f"INDEXNOW_HOLD does not hold IndexNow on {event}"
        )
    assert _needs(indexnow) == {"build", _DEPLOY}
    text = _DOCS_WORKFLOW.read_text(encoding="utf-8")
    assert "needs.deploy.outputs" not in text, (
        "a step reads the outputs of the Pages deploy, which no longer runs"
    )
    script = _INDEXNOW_SCRIPT.read_text(encoding="utf-8")
    environment = re.search(r"export const PAGES_ENVIRONMENT = '([^']+)'", script)
    assert environment, "indexnow-diff.mjs names no PAGES_ENVIRONMENT"
    _, deploy_job = _site_deploy_job()
    deploy_environment = deploy_job.get("environment")
    assert isinstance(deploy_environment, dict)
    assert environment.group(1) == deploy_environment.get("name")


def test_every_build_that_publishes_is_deployed_to_phonometry_dev_by_its_own_run() -> (
    None
):
    """docs.yml calls site-deploy.yml after the build, with this run's pages.

    The site on phonometry.dev follows main only if nothing has to be
    dispatched by hand: the job that calls the deploy runs on every event
    that publishes and never on a pull request, waits for the build, and
    hands it this run's id and the attempt the build ran in, so a re-run of
    the deploy alone takes the pages that build uploaded, as the Pages deploy
    does. It names the two Cloudflare tokens, secrets of the environment the
    called job names, which a called workflow reads only when the caller hands
    them by name, and nothing else of the repository's secrets reaches it. The
    called workflow takes the same three inputs by hand as when called, and
    hands back the address it deployed, the moment the pages went out and
    the attempt it ran in, the three things the IndexNow job reads of a
    deploy.

    A rollback by hand lasts only until the next run on main deploys again,
    so the repository variable ``SITE_DEPLOY_HOLD`` set to ``true`` skips the
    job until it is cleared; unset or anything else, every publishing run
    deploys. Its own concurrency group, which runs by hand share, keeps two
    deploys from uploading their pairs at once and never cancels one halfway.
    """
    docs = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    jobs: dict[str, dict[str, object]] = docs["jobs"]
    callers = [
        name
        for name, job in jobs.items()
        if job.get("uses") == "$/.github/workflows/site-deploy.yml"
    ]
    assert callers == ["deploy-site"], f"site-deploy.yml is called by {callers}"
    caller = jobs["deploy-site"]
    assert _needs(caller) == {"build"}
    main = "refs/heads/main"
    for unheld in ({}, {"SITE_DEPLOY_HOLD": "false"}):
        for event in _DEPLOYING_EVENTS:
            assert _runs_on(caller.get("if"), event, unheld, main), (
                f"the site is not deployed on {event} with {unheld}"
            )
        assert not _runs_on(caller.get("if"), "pull_request", unheld, main), (
            "a pull request would deploy the site"
        )
        # docs.yml dispatched by hand on another branch builds it, and the
        # called deploy refuses a build of anything but main: the job is
        # skipped there, so the run does not end red after a good build.
        assert not _runs_on(
            caller.get("if"), "workflow_dispatch", unheld, "refs/heads/feature"
        ), "a run dispatched on a branch would call the deploy, which refuses it"
    for event in _DEPLOYING_EVENTS:
        assert not _runs_on(
            caller.get("if"), event, {"SITE_DEPLOY_HOLD": "true"}, main
        ), f"SITE_DEPLOY_HOLD does not hold the deploy on {event}"
    assert caller.get("with") == {
        "run_id": "${{ github.run_id }}",
        "attempt": "${{ needs.build.outputs.attempt }}",
        "apply_rules": True,
    }
    # A called workflow reads an environment secret only when the caller
    # names it (unnamed it is an empty string, with no error), so the call
    # names the two Cloudflare tokens and nothing else, never `inherit`.
    assert caller.get("secrets") == {
        "CF_PHONOMETRY_DEPLOY_TOKEN": "${{ secrets.CF_PHONOMETRY_DEPLOY_TOKEN }}",
        "CF_PHONOMETRY_RULES_TOKEN": "${{ secrets.CF_PHONOMETRY_RULES_TOKEN }}",
    }, "the call must name the two Cloudflare tokens, and only them"
    assert caller.get("permissions") == {"contents": "read", "actions": "read"}
    assert not caller.get("continue-on-error")

    deploy = yaml.safe_load(_SITE_DEPLOY_WORKFLOW.read_text(encoding="utf-8"))
    triggers = deploy[True] if True in deploy else deploy["on"]
    assert set(triggers) == {"workflow_call", "workflow_dispatch"}, (
        "site-deploy.yml runs on something else than a call or a dispatch by hand"
    )
    called_secrets = triggers["workflow_call"].get("secrets") or {}
    assert {name: spec.get("required") for name, spec in called_secrets.items()} == {
        "CF_PHONOMETRY_DEPLOY_TOKEN": True,
        "CF_PHONOMETRY_RULES_TOKEN": True,
    }, "a call must hand both Cloudflare tokens, or it would deploy with empty ones"
    called = triggers["workflow_call"]
    by_hand = triggers["workflow_dispatch"]
    inputs = {"run_id": "string", "attempt": "string", "apply_rules": "boolean"}
    for trigger, how in ((called, "called"), (by_hand, "by hand")):
        declared = trigger["inputs"]
        assert {name: spec["type"] for name, spec in declared.items()} == inputs, how
        assert declared["run_id"]["required"] is True, how
    deploy_jobs: dict[str, dict[str, object]] = deploy["jobs"]
    assert len(deploy_jobs) == 1, "site-deploy.yml deploys in one job"
    [(job_name, job)] = deploy_jobs.items()
    assert job.get("concurrency") == {
        "group": "site-deploy",
        "cancel-in-progress": False,
    }, "a deploy called and one run by hand can upload their pairs at once"
    job_outputs = job.get("outputs")
    assert isinstance(job_outputs, dict)
    assert job_outputs.get("attempt") == "${{ github.run_attempt }}"
    handed = called.get("outputs")
    assert isinstance(handed, dict)
    for name in ("page_url", "deployed-at", "attempt"):
        assert name in job_outputs, f"the deploy job writes no {name}"
        assert handed[name]["value"] == f"${{{{ jobs.{job_name}.outputs.{name} }}}}", (
            f"the call hands back no {name}"
        )

    # The moment the pages went out is taken once the Worker is deployed.
    steps: list[dict[str, object]] = job["steps"]  # type: ignore[assignment]
    clock = re.fullmatch(
        r"\$\{\{ steps\.([\w-]+)\.outputs\.(\w+) \}\}",
        str(job_outputs["deployed-at"]),
    )
    assert clock, job_outputs["deployed-at"]
    deployed_at, _ = _the_one(
        [
            (index, step)
            for index, step in enumerate(steps)
            if str(step.get("name", "")).startswith("Deploy the Worker")
        ],
        "deploy the Worker",
    )
    clock_at, clock_step = _the_one(
        [
            (index, step)
            for index, step in enumerate(steps)
            if step.get("id") == clock.group(1)
        ],
        "write the moment the pages went out",
    )
    assert deployed_at < clock_at, "the moment is taken before the Worker went out"
    assert f"{clock.group(2)}=$(date -u +%Y-%m-%dT%H:%M:%SZ)" in str(clock_step["run"])


def test_a_push_to_main_never_cancels_the_deploy_of_the_push_before() -> None:
    """A newer run on main waits for the one deploying, a pull request does not.

    The deploy uploads two Worker versions as a pair and puts one live; a run
    cancelled between the two leaves the quota guard half a pair. Runs on main
    therefore queue (GitHub keeps the newest one waiting), while a push to a
    pull request still cancels the build of the commit it replaces. A
    cancellation of the calling run reaches the called deploy too, so the
    deploy's own concurrency group alone would not protect it.
    """
    docs = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    concurrency = docs.get("concurrency")
    assert isinstance(concurrency, dict)
    assert concurrency.get("cancel-in-progress") == (
        "${{ github.event_name == 'pull_request' }}"
    )
    group = str(concurrency.get("group"))
    assert "github.event.pull_request.number" in group, (
        "pull requests share one group and cancel each other's builds"
    )


#: A Python script of the repository named on a command line: ``python3
#: scripts/x.py`` in a workflow step, ``python3 ../scripts/x.py`` from site/.
_SCRIPT_RUN = re.compile(r"\bpython3?\s+(?:\.\./)?scripts/([A-Za-z0-9_]+)\.py\b")


def _local_imports(script: pathlib.Path) -> set[str]:
    """The modules of ``scripts/`` a script imports, as sibling modules."""
    tree = ast.parse(script.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return {name for name in names if (script.parent / f"{name}.py").is_file()}


def _scripts_the_site_build_runs() -> set[str]:
    """Every ``scripts/*.py`` the docs workflow runs, and what each imports.

    Read from the ``run:`` steps of docs.yml and the scripts of
    site/package.json (``prebuild`` runs the llms generator inside ``pnpm
    build``), then closed over the sibling modules each script imports.
    """
    workflow = yaml.safe_load(_DOCS_WORKFLOW.read_text(encoding="utf-8"))
    commands = [
        str(step["run"])
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "run" in step
    ]
    package = json.loads((_ROOT / "site" / "package.json").read_text(encoding="utf-8"))
    commands += [str(command) for command in package["scripts"].values()]
    pending = {name for command in commands for name in _SCRIPT_RUN.findall(command)}
    found: set[str] = set()
    while pending:
        name = pending.pop()
        if name in found:
            continue
        found.add(name)
        script = _ROOT / "scripts" / f"{name}.py"
        assert script.is_file(), (
            f"docs.yml or site/package.json runs a missing scripts/{name}.py"
        )
        pending |= _local_imports(script)
    return {f"scripts/{name}.py" for name in found}


def test_the_docs_workflow_triggers_on_every_script_it_runs() -> None:
    """A script the site build runs has to be able to trigger that build.

    The docs workflow runs Python scripts of the repository before and after
    the build (the llms generator, the static check of the llms files, the
    conformance claims), and ``pnpm build`` runs the llms generator again. A script
    outside the workflow's paths can be broken by a pull request that never
    runs the workflow, and the site build then fails on the next pull request
    that touches site/, which changed nothing at fault. The modules those
    scripts import from scripts/ are held the same way.
    """
    scripts = _scripts_the_site_build_runs()
    assert "scripts/generate_llms.py" in scripts, (
        "the site build runs no llms generator; update this test"
    )
    assert "scripts/markdown_fences.py" in scripts, (
        "the imports of the scripts were not followed; update this test"
    )
    for event in ("push", "pull_request"):
        missing = sorted(scripts - _trigger_paths(_DOCS_WORKFLOW, event))
        assert not missing, (
            f"docs.yml {event} trigger does not list {missing}, "
            "so a change to them cannot run the site build that runs them"
        )


def test_the_jit_job_comment_quotes_the_numba_floor_that_is_declared() -> None:
    """The 3.14 job explains itself by quoting pyproject's numba floor.

    A floor is quoted without its marker: the comment says which Python it is for.
    """
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    declared = {
        spec.split(";", 1)[0].replace(" ", "")
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
    """The index of the one step of the baseline-glibc job whose script has *runs*.

    The digests are steps of that job, beside the glibc tests, which run no
    digest script and so never match.
    """
    found = [i for i, step in enumerate(steps) if runs in str(step.get("run", ""))]
    assert len(found) == 1, f"{len(found)} baseline-glibc steps run {runs!r}"
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
    steps: list[dict[str, object]] = workflow["jobs"]["baseline-glibc"]["steps"]
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


#: What the scan is told the project version is: the output of the step that
#: reads VERSION, expanded by the runner into an input of the scan action.
_SONAR_VERSION_ARGS = "-Dsonar.projectVersion=${{ steps.version.outputs.version }}"


def _sonar_steps() -> tuple[dict[str, object], dict[str, object], int, int]:
    """The step that reads VERSION and the scan step, with their positions."""
    workflow = yaml.safe_load(_PYTHON_WORKFLOW.read_text(encoding="utf-8"))
    steps: list[dict[str, object]] = workflow["jobs"]["sonar"]["steps"]
    read = [i for i, step in enumerate(steps) if step.get("id") == "version"]
    scan = [
        i
        for i, step in enumerate(steps)
        if str(step.get("uses", "")).startswith("SonarSource/sonarqube-scan-action@")
    ]
    assert len(read) == 1, f"the sonar job has {len(read)} steps with id 'version'"
    assert len(scan) == 1, f"the sonar job has {len(scan)} scan steps"
    return steps[read[0]], steps[scan[0]], read[0], scan[0]


def test_the_sonar_scan_is_told_the_version_in_VERSION() -> None:
    """The scan names the project version, so a release opens a new-code period.

    SonarCloud counts as new code everything written since the project version
    last changed. A scan that names no version records it as "not provided",
    and every analysis from the first one on did, so the period never moved
    and every smell ever written counted as new. The version is read from
    VERSION by the step before the scan and handed to the scan action as an
    input, never written out by hand and never put through a shell, and
    ``sonar-project.properties`` fixes none of its own.
    """
    read, scan, read_at, scan_at = _sonar_steps()
    assert read_at < scan_at
    assert "VERSION" in str(read.get("run", ""))
    given = scan.get("with")
    assert isinstance(given, dict)
    assert given.get("args") == _SONAR_VERSION_ARGS
    properties = (_ROOT / "sonar-project.properties").read_text(encoding="utf-8")
    assert not re.search(r"^\s*sonar\.projectVersion\s*=", properties, re.MULTILINE)


def _version_patterns(script: str) -> list[str]:
    """The regexes a workflow script hands to ``grep -Eq``, in order."""
    return re.findall(r"grep -Eq '([^']+)'", script)


def test_the_version_step_holds_version_to_the_pattern_the_release_holds_it_to() -> (
    None
):
    """The scan and the release accept the same versions, written once each.

    The PEP 440 normal form is written out in two workflows: the release reads
    VERSION into the artefact names, the scan into the project version. If one
    copy is edited and the other is not, the scan can record a version the
    release refuses, or refuse one the release publishes, and the comment above
    the step goes false without a sound.
    """
    read, _, _, _ = _sonar_steps()
    release = (_ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    scan_patterns = _version_patterns(str(read["run"]))
    release_patterns = _version_patterns(release)
    assert len(scan_patterns) == 1, f"the version step has {len(scan_patterns)} regexes"
    assert release_patterns, "release.yml checks VERSION with no grep -Eq"
    assert scan_patterns[0] == release_patterns[0]


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="the step is a bash script that runs on Ubuntu",
)
@pytest.mark.parametrize(
    ("version", "accepted"),
    [
        ((_ROOT / "VERSION").read_text(encoding="utf-8").strip(), True),
        ("4.0.0", True),
        ("4.0.1rc2", True),
        ("4.0.0.post1", True),
        ("4.0.0 -Dsonar.host.url=https://example.org", False),
        ("v4.0.0", False),
        ("4.0", False),
        ("", False),
    ],
)
def test_the_version_step_hands_on_a_release_version_and_nothing_else(
    tmp_path: pathlib.Path, version: str, *, accepted: bool
) -> None:
    """The step's own script, run as the runner runs it, against a VERSION file.

    A release version goes to the step's output as it is written; anything
    else, a second scanner argument above all, stops the job before the
    scanner reads it.
    """
    read, _, _, _ = _sonar_steps()
    (tmp_path / "VERSION").write_text(f"{version}\n", encoding="utf-8")
    output = tmp_path / "github-output"
    output.touch()
    done = child_process.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", str(read["run"])],
        cwd=tmp_path,
        env={**os.environ, "GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    if accepted:
        assert done.returncode == 0, done.stdout + done.stderr
        assert output.read_text(encoding="utf-8") == f"version={version}\n"
    else:
        assert done.returncode != 0
        assert "VERSION is not a PEP 440 normal-form version" in done.stdout
        assert output.read_text(encoding="utf-8") == ""


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
    for path in _workflow_files():
        for action, ref in re.findall(
            r"uses:\s*([\w.-]+/[\w./-]+)@(\S+)", path.read_text(encoding="utf-8")
        ):
            if _ACTION_CHANNELS.get(action) == ref or _RELEASE_TAG.fullmatch(ref):
                continue
            unpinned.append(f"{path.name}: {action}@{ref}")
    assert unpinned == []


def _strings(node: object) -> Iterator[str]:
    """Every string a parsed workflow holds, keys and values, at any depth."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from _strings(key)
            yield from _strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _strings(item)


#: The Ubuntu releases a workflow may name: the one ``ubuntu-latest`` names
#: now, and the one whose glibc a few jobs hold their numbers to.
_UBUNTU_RELEASES = ("ubuntu-26.04", "ubuntu-24.04")


def test_no_workflow_runs_on_the_moving_ubuntu_label() -> None:
    """Every Linux job names the Ubuntu release it runs on.

    ``ubuntu-latest`` is a label GitHub moves: from 2026-10-19 it began to
    point at Ubuntu 26.04 instead of 24.04. The release build is held to the
    same bytes twice and the coverage upload to one cell of the matrix, so a
    job that followed the label changed under them on the day it moved, with
    no commit of ours. The jobs name ubuntu-26.04, the image the label names
    now. Three name ubuntu-24.04, two of them because they hold their numbers
    to its glibc: the baseline-glibc job, where the FDTD engines' golden
    digests were measured and the weighting design runs on glibc's routines
    without FMA, which only that release's baseline build of glibc carries,
    and the remote-node job, which compares its runs with those of the node
    image built on ``ubuntu:24.04``.
    A release is moved by an edit to the workflows and to the pair above,
    once the gates pass on it.
    """
    moving: list[str] = []
    unnamed: list[str] = []
    for path in _workflow_files():
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for text in _strings(workflow):
            if "ubuntu-latest" in text:
                moving.append(f"{path.name}: {text!r}")
            unnamed += [
                f"{path.name}: {release}"
                for release in re.findall(r"ubuntu-\d+\.\d+", text)
                if release not in _UBUNTU_RELEASES
            ]
    assert moving == [], (
        "these workflow strings name ubuntu-latest, which GitHub moves to a new "
        "Ubuntu release on its own; name the release, ubuntu-26.04, or "
        f"ubuntu-24.04 for a job held to that release's glibc: {moving}"
    )
    assert unnamed == [], (
        "these workflow strings name an Ubuntu release this test does not "
        f"accept, {' or '.join(_UBUNTU_RELEASES)}; a release joins "
        f"_UBUNTU_RELEASES once the gates pass on it: {unnamed}"
    )


def test_every_workflow_that_runs_pip_turns_its_version_notice_off() -> None:
    """pip says nothing in a job's log about its own newer releases.

    Four jobs of every pull request printed "A new release of pip is
    available" whenever the runner's pip, or the pip of a fresh venv, lagged
    the newest one, a notice about the tool rather than the build. The setting
    sits in the workflow's own ``env``, so a job added later inherits it.
    """
    missing = []
    for path in _workflow_files():
        text = path.read_text(encoding="utf-8")
        if "pip install" not in text and "-m pip" not in text:
            continue
        workflow_env = yaml.safe_load(text).get("env") or {}
        if str(workflow_env.get("PIP_DISABLE_PIP_VERSION_CHECK")) != "1":
            missing.append(path.name)
    assert missing == [], (
        f'these workflows run pip without PIP_DISABLE_PIP_VERSION_CHECK: "1" in their env: {missing}'
    )


#: The actions of a ``filterwarnings`` entry that let a warning through.
_LETS_THROUGH = frozenset({"ignore", "default", "always", "module", "once"})


def test_a_stray_warning_fails_the_suite(tmp_path: pathlib.Path) -> None:
    """A UserWarning or RuntimeWarning that no test asked for is an error.

    Before, 63 tests in 14 files met an advisory of the library they did not
    assert, and the suite printed each in its summary, where a new one beside
    them read as one more of the same. The configuration turns both classes
    into errors, and no later entry lets either class back through whole: an
    entry after them may let one warning through by its message, never the
    class. A planted file under the configuration shows it: a stray topic
    warning and a stray division by zero fail, an asserted one passes.
    """
    options = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    entries = options["tool"]["pytest"]["ini_options"]["filterwarnings"]
    assert "error::UserWarning" in entries
    assert "error::RuntimeWarning" in entries
    first = min(
        entries.index("error::UserWarning"), entries.index("error::RuntimeWarning")
    )
    whole_class = []
    for entry in entries[first + 1 :]:
        action, message, category = (entry.split(":") + ["", ""])[:3]
        if (
            action in _LETS_THROUGH
            and not message
            and category
            in {
                "",
                "Warning",
                "UserWarning",
                "RuntimeWarning",
            }
        ):
            whole_class.append(entry)
    assert whole_class == []
    planted = tmp_path / "test_planted.py"
    planted.write_text(
        "import warnings\n\n"
        "import numpy as np\n"
        "import pytest\n\n"
        "from phonometry.filters import FilterBankWarning\n\n\n"
        "def test_a_stray_advisory():\n"
        "    warnings.warn('stray', FilterBankWarning, stacklevel=1)\n\n\n"
        "def test_a_stray_division_by_zero():\n"
        "    np.log10(np.zeros(1))\n\n\n"
        "def test_an_asserted_advisory():\n"
        "    with pytest.warns(FilterBankWarning, match='asked for'):\n"
        "        warnings.warn('asked for', FilterBankWarning, stacklevel=1)\n",
        encoding="utf-8",
    )
    result = child_process.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-c",
            str(_ROOT / "pyproject.toml"),
            "--rootdir",
            str(tmp_path),
            str(planted),
        ],
        timeout=120,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert "2 failed, 1 passed" in result.stdout, result.stdout + result.stderr


def test_a_cache_pytest_cannot_write_fails_no_run(tmp_path: pathlib.Path) -> None:
    """A run whose tests pass passes where pytest cannot write its cache.

    pytest warns with a PytestCacheWarning, a UserWarning, when its cache
    directory cannot be made or written, as in a read-only checkout or
    container a packager's run can be. Raised once the last test has run,
    the warning ended such a run with a traceback, exit status 1 and no
    summary line. The configuration shows it instead.
    """
    planted = tmp_path / "test_planted.py"
    planted.write_text("def test_a_pass():\n    assert True\n", encoding="utf-8")
    # A cache directory under a file: no platform can make it, root included.
    (tmp_path / "a-file").write_text("", encoding="utf-8")
    result = child_process.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-c",
            str(_ROOT / "pyproject.toml"),
            "--rootdir",
            str(tmp_path),
            "-o",
            f"cache_dir={tmp_path / 'a-file' / 'cache'}",
            str(planted),
        ],
        timeout=120,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 passed, 1 warning" in result.stdout, result.stdout
    assert "could not create cache path" in result.stdout


#: ``<interpreter> -m pip [options] install <rest>``: the pip of that
#: interpreter, unless ``--python`` hands the install to another one, which
#: the interpreter's own pip still runs.
_MODULE_PIP_INSTALL = re.compile(
    r'(?P<owner>"[^"]+"|[\w./$-]+)\s+-m\s+pip\s+(?:--python\s+\S+\s+)?install\b(?P<rest>.*)'
)
#: ``pip install <rest>`` run bare, which is the pip of the Python on PATH.
_BARE_PIP_INSTALL = re.compile(r"(?:^|[\s;&|(])pip\s+install\b(?P<rest>.*)")
#: The requirement that upgrades pip itself.
_UPGRADES_PIP = re.compile(r"(?:--upgrade|-U)\s+pip(?:\s|$)")


def _pip_installs(job: Mapping[str, object]) -> Iterator[tuple[str, str]]:
    """``(interpreter, what follows install)`` for each pip install of a job, in order."""
    steps = job.get("steps") or []
    assert isinstance(steps, list)
    for step in steps:
        run = step.get("run") if isinstance(step, dict) else None
        if not isinstance(run, str):
            continue
        for raw in run.splitlines():
            line = raw.strip()
            if line.startswith("#"):
                continue
            module = _MODULE_PIP_INSTALL.search(line)
            if module is not None:
                yield module["owner"].strip('"'), module["rest"]
                continue
            bare = _BARE_PIP_INSTALL.search(line)
            if bare is not None:
                yield "python", bare["rest"]


def test_every_job_that_installs_with_pip_upgrades_it_first() -> None:
    """Each pip a job installs with is brought to the newest release first.

    The pip of a setup-python runner, and the one a fresh ``venv`` bundles,
    lags the newest release by whatever the image is behind, so a job that
    installed with it resolved with an older pip than a contributor following
    the documentation gets. Every interpreter whose pip a job installs with,
    the runner's and each virtual environment's, upgrades pip before its
    first install.
    """
    late = []
    for path in _workflow_files():
        jobs = yaml.safe_load(path.read_text(encoding="utf-8")).get("jobs") or {}
        for name, job in jobs.items():
            upgraded: set[str] = set()
            for owner, rest in _pip_installs(job):
                if _UPGRADES_PIP.search(rest):
                    upgraded.add(owner)
                elif owner not in upgraded:
                    late.append(f"{path.name}:{name}: {owner} -m pip install{rest}")
                    upgraded.add(owner)
    assert late == [], (
        "these jobs install with a pip they have not upgraded; run "
        f"`<python> -m pip install --upgrade pip` first: {late}"
    )


@pytest.mark.parametrize(
    ("line", "found"),
    [
        ("python -m pip install --upgrade pip", ("python", " --upgrade pip")),
        (
            '"$RUNNER_TEMP/env/bin/python" -m pip install x',
            ("$RUNNER_TEMP/env/bin/python", " x"),
        ),
        ('python -m pip --python "$E/bin/python" install w.whl', ("python", " w.whl")),
        ("pip install -e .", ("python", " -e .")),
        (
            'if python -m pip install --no-cache-dir "p==1"; then',
            ("python", ' --no-cache-dir "p==1"; then'),
        ),
        ("# python -m pip install x", None),
        ("python -m pipx install x", None),
    ],
)
def test_the_pip_install_reader_names_the_pip_that_runs(
    line: str, found: tuple[str, str] | None
) -> None:
    installs = list(_pip_installs({"steps": [{"run": line}]}))
    assert installs == ([] if found is None else [found])


def test_every_job_that_runs_corepack_turns_its_download_prompt_off() -> None:
    """corepack fetches the pinned pnpm without announcing it in the log.

    The first ``pnpm`` a corepack shim runs downloads the release the
    ``packageManager`` field pins and prints that it is about to; the pin is
    the decision, and the line is noise in every build. The setting is read
    from the job's environment, the workflow's or the step's.
    """
    missing = []
    for path in _workflow_files():
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        workflow_env = workflow.get("env") or {}
        for name, job in (workflow.get("jobs") or {}).items():
            job_env = {**workflow_env, **(job.get("env") or {})}
            for step in job.get("steps") or []:
                if "corepack" not in str(step.get("run", "")):
                    continue
                env = {**job_env, **(step.get("env") or {})}
                if str(env.get("COREPACK_ENABLE_DOWNLOAD_PROMPT")) != "0":
                    missing.append(f"{path.name}:{name}: {step.get('name')}")
    assert missing == [], (
        'these steps run corepack without COREPACK_ENABLE_DOWNLOAD_PROMPT: "0" '
        f"in their environment: {missing}"
    )


def test_the_pyodide_job_keeps_the_packages_pyodide_downloads() -> None:
    """The wheels Pyodide fetches from its CDN are restored between runs.

    ``node_modules/pyodide`` is a link pnpm makes into its own store, so a
    cache of that path would keep the link and none of the wheels behind it.
    The job hands ``smoke.mjs`` a directory of its own instead, which the
    script passes to ``loadPyodide`` as ``packageCacheDir``, and caches that
    directory under the lockfile that pins Pyodide, so a new Pyodide starts
    from an empty one. The Pyodide steps are those of the built-package job,
    which builds the wheel they load.
    """
    workflow = yaml.safe_load(
        (_ROOT / ".github" / "workflows" / "python-app.yml").read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["built-package"]["steps"]
    caches = [
        step for step in steps if str(step.get("uses", "")).startswith("actions/cache@")
    ]
    assert len(caches) == 1, caches
    cache = caches[0]["with"]
    assert "hashFiles('tests/pyodide/pnpm-lock.yaml')" in cache["key"]
    smoke = [
        step for step in steps if "tests/pyodide/smoke.mjs" in str(step.get("run", ""))
    ]
    assert len(smoke) == 2, smoke
    for step in smoke:
        assert steps.index(step) > steps.index(caches[0])
        assert (step.get("env") or {}).get("PYODIDE_PACKAGE_CACHE_DIR") == cache["path"]
    script = (_ROOT / "tests" / "pyodide" / "smoke.mjs").read_text(encoding="utf-8")
    assert "process.env.PYODIDE_PACKAGE_CACHE_DIR" in script
    assert "packageCacheDir" in script


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


#: The directories whose package.json pins the pnpm corepack installs: the
#: documentation site and the Pyodide smoke test.
_PNPM_PROJECTS = ("site", "tests/pyodide")

#: A corepack pin: a pnpm release and the SHA-512 of its tarball, in hex.
_PNPM_PIN = re.compile(r"pnpm@(?P<version>\d+\.\d+\.\d+)\+sha512\.[0-9a-f]{128}")


def _pnpm_pin_problems(root: pathlib.Path) -> list[str]:
    """What disagrees among the pnpm pins of the projects under ``root``.

    Each project's ``packageManager`` has to be a release with its hash, its
    lockfile has to record the same release (pnpm 12 writes the pnpm it
    installs into ``packageManagerDependencies``), and every project has to
    pin the same one.
    """
    problems: list[str] = []
    versions: dict[str, str] = {}
    for project in _PNPM_PROJECTS:
        manifest = json.loads(
            (root / project / "package.json").read_text(encoding="utf-8")
        )
        pin = str(manifest.get("packageManager", ""))
        match = _PNPM_PIN.fullmatch(pin)
        if match is None:
            problems.append(
                f"{project}/package.json pins {pin!r}, not pnpm@<release>+sha512.<hex>"
            )
            continue
        versions[project] = match["version"]
        lockfile = (root / project / "pnpm-lock.yaml").read_text(encoding="utf-8")
        locked = {
            str(
                document["importers"]["."]["packageManagerDependencies"]["pnpm"][
                    "version"
                ]
            )
            for document in yaml.safe_load_all(lockfile)
            if isinstance(document, dict)
            and "packageManagerDependencies"
            in document.get("importers", {}).get(".", {})
        }
        if locked != {match["version"]}:
            problems.append(
                f"{project}/pnpm-lock.yaml records pnpm {sorted(locked)}, its package.json "
                f"pins {match['version']}; run pnpm install --lockfile-only there"
            )
    if len(set(versions.values())) > 1:
        problems.append(f"the projects pin different pnpm releases: {versions}")
    return problems


def test_every_project_pins_one_pnpm_and_locks_the_one_it_pins() -> None:
    """The site and the Pyodide smoke test install with one pnpm release.

    The two pins were moved by hand, together, each time; nothing held them
    together or to their lockfiles, and pnpm 12 records its own release in the
    lockfile beside the dependencies, so a pin moved without the lockfile it
    goes with leaves the two disagreeing about the pnpm a frozen install runs.
    """
    problems = _pnpm_pin_problems(_ROOT)
    assert problems == [], problems


def test_the_pnpm_pin_check_sees_a_pin_moved_alone(tmp_path: pathlib.Path) -> None:
    """A pin moved in one project, or without its lockfile, is reported."""
    for project in _PNPM_PROJECTS:
        (tmp_path / project).mkdir(parents=True)
        for name in ("package.json", "pnpm-lock.yaml"):
            shutil.copyfile(_ROOT / project / name, tmp_path / project / name)
    manifest_path = tmp_path / "site" / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["packageManager"] = "pnpm@99.0.0+sha512." + "0" * 128
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    problems = _pnpm_pin_problems(tmp_path)
    assert any("site/pnpm-lock.yaml records pnpm" in problem for problem in problems), (
        problems
    )
    assert any("different pnpm releases" in problem for problem in problems), problems


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

#: A variable set for the one command it precedes: ``MYPYPATH=tests mypy``.
_SET_BEFORE = r"[A-Za-z_][A-Za-z0-9_]*=\S*\s+"

#: A program that runs the command after it, with its own options: ``env``,
#: ``time``, ``exec``, or a tool's ``run`` (``uv run``, ``poetry run``).
_WRAPPER = r"(?:env|time|exec|(?:uv|poetry|pdm|pipx|hatch)\s+run)(?:\s+-\S+)*\s+"

#: A Python interpreter under any path, or a Makefile variable that names
#: one, with the options it takes before ``-m``.
_INTERPRETER = (
    r"(?:(?:\S*/)?python[0-9.]*|py|\$\([A-Za-z_]+\)|\$\{[A-Za-z_]+\})"
    r"(?:\s+-[XW]\s*\S+|\s+-\S+)*?"
)


def _command_pattern(variables: str) -> re.Pattern[str]:
    """A type-check command at the start of a command, up to its end.

    The program is ``mypy`` under any path, an interpreter running it as a
    module, or a Makefile variable that holds it, *variables* being a regex
    of their names. Variables set before it and wrappers that run it are part
    of the command; ``prefix`` holds them and ``arguments`` what follows the
    program.
    """
    program = (
        rf"{_INTERPRETER}\s+-m\s*mypy"
        r"|(?:\S*/)?mypy"
        rf"|\$\((?:{variables})\)|\$\{{(?:{variables})\}}"
    )
    return re.compile(
        rf"(?:^|&&|\|\||[;|(])\s*(?P<prefix>(?:{_SET_BEFORE}|{_WRAPPER})*)"
        rf"(?:{program})(?=\s|$|[;&|)])(?P<arguments>[^;&|)\n]*)"
    )


#: The command as CI, the pages and the scripts write it: the Makefile's
#: ``$(MYPY)`` is the one variable they may name.
_MYPY_COMMAND = _command_pattern("MYPY")

#: A command already found, read back with any variable as its program.
_FOUND_COMMAND = _command_pattern("[A-Za-z_][A-Za-z0-9_]*")

#: A variable assignment of a Makefile, in any of make's flavours, possibly
#: indented inside a conditional.
_MAKE_ASSIGNMENT = re.compile(
    r"^ *(?:(?:export|override) +)*(?P<name>[A-Za-z_][A-Za-z0-9_]*) *"
    r"(?P<operator>:{1,3}=|[?+!]?=) *(?P<value>.*)$"
)

#: A shell comment, from a ``#`` that starts a word to the end of the line.
_COMMENT = re.compile(r"(?:^|\s)#.*")

#: A Markdown fence, opening or closing: its run of three or more backticks or
#: tildes.
_FENCE = re.compile(r"^\s*(?P<run>`{3,}|~{3,})")

#: An assignment to ``MYPYPATH``: a shell's, before a command or on a line of
#: its own, one written into ``$GITHUB_ENV``, or a Makefile's in any of make's
#: flavours. A read of ``$MYPYPATH`` is none.
_SETS_MYPYPATH = re.compile(r"(?<![\w$])MYPYPATH *(?:[:?+!]|:{2,3})?=")

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

#: Pages that tell a user how to type check their own code against the
#: installed package, where an option and a file name are the point: that is
#: not the repository's type check, so ``files`` under [tool.mypy] does not
#: hold their arguments. Each must still state a mypy command, so an entry
#: that outlived its page fails.
_TYPE_CHECKS_OF_A_USERS_CODE = dict.fromkeys(
    (
        "site/src/content/docs/start/environments/index.md",
        "site/src/content/docs/start/environments/type-checking.md",
        "site/src/content/docs/es/start/environments/index.md",
        "site/src/content/docs/es/start/environments/type-checking.md",
    ),
    "the Environments pages type check a user's script, not this repository",
)

#: The roots bare `mypy` has to keep checking: the package, the scripts, the
#: transition shim, the static typing pins and the script that writes the pull
#: request comment.
_MYPY_ROOTS = ("src", "scripts", "stub/src", "tests/static_typing", ".github/scripts")

#: The files mypy reads its configuration from before ``pyproject.toml``.
_MYPY_SHADOWING_CONFIGS = ("mypy.ini", ".mypy.ini")


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


def _values_of(node: object, key: str) -> list[object]:
    """Every value *key* is given in the mappings of a YAML document, at any depth."""
    if isinstance(node, dict):
        found = [node[key]] if key in node else []
        for value in node.values():
            found += _values_of(value, key)
        return found
    if isinstance(node, list):
        return [value for item in node for value in _values_of(item, key)]
    return []


def _scripts_of(node: object) -> list[str]:
    """Every ``run:`` script of a workflow or an action, at any depth."""
    return [script for script in _values_of(node, "run") if isinstance(script, str)]


def _joined(text: str) -> list[str]:
    """The lines of a script, each continued line joined to the next."""
    return text.replace("\\\n", " ").splitlines()


def _commands_in(
    lines: Sequence[str], pattern: re.Pattern[str] = _MYPY_COMMAND
) -> list[str]:
    """The type-check commands in *lines*, each as written, spaces folded."""
    return [
        " ".join(match.group(0).strip(" ;&|(").split())
        for line in lines
        for match in pattern.finditer(line.strip().lstrip("@-+"))
    ]


def _spells_out(command: str) -> bool:
    """Whether *command* gives mypy anything ``pyproject.toml`` should hold.

    That is an argument (a path, an option, a comment aside), or a search
    path set before it in ``MYPYPATH``, which is ``mypy_path`` by another
    name.
    """
    match = _FOUND_COMMAND.match(command)
    if match is None:
        msg = f"not a type-check command: {command!r}"
        raise ValueError(msg)
    arguments = _COMMENT.sub("", match["arguments"]).strip()
    return bool(arguments) or bool(re.search(r"(?:^|\s)MYPYPATH=", match["prefix"]))


def _fence_after(fence: str, line: str) -> str | None:
    """The fence still open after *line*, or ``None`` when *line* is not one.

    Outside a block, *fence* being empty, any fence opens one. Inside, as
    CommonMark has it, only a run of the opening character at least as long
    as the opening run, alone on its line, closes it: a shorter fence shown
    inside a longer one is a line of the block.
    """
    found = _FENCE.match(line)
    if found is None:
        return None
    if not fence:
        return found["run"]
    closes = found["run"].startswith(fence) and line.strip() == found["run"]
    return "" if closes else None


def _markdown_code(text: str) -> list[str]:
    """The code a page gives: its fenced lines and its inline code spans.

    Prose that names the tool is not code; a code span or a fenced block is
    how every page here writes something to run. A fenced line that ends in
    a backslash goes on in the next one.
    """
    code: list[str] = []
    fence = ""
    continued = ""
    for line in text.splitlines():
        after = None if continued else _fence_after(fence, line)
        if after is not None:
            fence = after
            continue
        if fence:
            if line.rstrip().endswith("\\"):
                continued += line.rstrip()[:-1] + " "
                continue
            code.append(continued + line)
            continued = ""
        else:
            code += [span.strip() for span in _CODE_SPAN.findall(line)]
    return code


def _markdown_commands(text: str) -> list[str]:
    """The type-check commands a page gives, in its fenced lines and code spans."""
    return _commands_in(_markdown_code(text))


def _makefile_commands(text: str) -> list[str]:
    """The type-check commands of a Makefile, in its variables and recipes.

    A recipe runs ``$(MYPY)``, whose value is set apart, indented inside
    ``ifeq`` where no recipe line is; so every assignment is read as well, a
    variable that holds the program is followed into the recipes that name
    it, and a ``+=`` onto one is an argument given to the program.
    """
    lines = _joined(text)
    assignments = [
        found
        for line in lines
        if not line.startswith("\t") and (found := _MAKE_ASSIGNMENT.match(line))
    ]
    holders = {"MYPY"}
    while True:
        pattern = _command_pattern("|".join(sorted(holders)))
        grown = holders | {
            found["name"]
            for found in assignments
            if _commands_in([found["value"]], pattern)
        }
        if grown == holders:
            break
        holders = grown
    commands: list[str] = []
    for found in assignments:
        if found["operator"] == "+=" and found["name"] in holders:
            commands.append(f"$({found['name']}) {found['value']}".strip())
        else:
            commands += _commands_in([found["value"]], pattern)
    recipes = [line for line in lines if line.startswith("\t")]
    return commands + _commands_in(recipes, pattern)


def _stated_files() -> dict[str, str]:
    """The text of every tracked file that may tell anyone to run the type check.

    Workflows and actions, Makefiles, shell scripts and hooks, and pages. The
    CHANGELOG is left out: it records the commands of past releases. So is the
    GitHub edition under ``docs/``: ``make llms`` writes each of its files from
    a site page read here, and an entry keyed by its path would be a second
    entry for one page.
    """
    names = _tracked(
        ".github/*.yml",
        ".github/*.yaml",
        "Makefile",
        "*/Makefile",
        "*.mk",
        "*.sh",
        "hooks/*",
        "*.md",
        "*.mdx",
    )
    return {
        name: (_ROOT / name).read_text(encoding="utf-8")
        for name in names
        if name != "CHANGELOG.md" and not github_edition.is_edition_file(_ROOT / name)
    }


def _is_workflow(name: str) -> bool:
    """Whether *name* is a workflow or an action, read for its ``run:`` scripts."""
    return name.endswith((".yml", ".yaml"))


def _code_of(name: str, text: str) -> list[str]:
    """The lines of code the file *name* gives to be run, continued lines joined.

    A workflow's or an action's ``run:`` scripts, a page's fenced lines and
    code spans, and every line of a Makefile, a script or a hook.
    """
    if _is_workflow(name):
        document = yaml.safe_load(text)
        return [line for script in _scripts_of(document) for line in _joined(script)]
    if name.endswith((".md", ".mdx")):
        return _markdown_code(text)
    return _joined(text)


def _stated_mypy_commands() -> dict[str, list[str]]:
    """Every type-check command the tracked tree tells anyone to run, by file."""
    stated = {
        name: (
            _makefile_commands(text)
            if pathlib.PurePosixPath(name).name == "Makefile" or name.endswith(".mk")
            else _commands_in(_code_of(name, text))
        )
        for name, text in _stated_files().items()
    }
    return {name: commands for name, commands in stated.items() if commands}


def _mypypath_settings_in(name: str, text: str) -> list[str]:
    """Where the file *name* sets ``MYPYPATH``, each place as it is written.

    A line of its code that assigns it, a comment aside, and in a workflow or
    an action an ``env`` mapping that names it.
    """
    found = [
        " ".join(line.split())
        for line in _code_of(name, text)
        if _SETS_MYPYPATH.search(_COMMENT.sub("", line))
    ]
    if _is_workflow(name):
        found += [
            f"MYPYPATH: {value}"
            for value in _values_of(yaml.safe_load(text), "MYPYPATH")
        ]
    return found


@pytest.mark.git_checkout
@pytest.mark.whole_tree
def test_every_stated_type_check_is_bare_mypy() -> None:
    """CI, ``make lint`` and every page run the type check as plain ``mypy``.

    A path list written out in one of them is a second copy of ``files``,
    and the copies drift: the Makefile and the pull request template had
    both lost ``stub/src`` while CI still checked it. Any spelling of the
    program counts, ``python -m mypy`` and ``.venv/bin/mypy`` among them, and
    so does the value the Makefile gives ``$(MYPY)``.
    """
    stated = _stated_mypy_commands()
    missing = [name for name in _MYPY_STATED_IN if name not in stated]
    assert not missing, (
        f"no type-check command found in {missing}; if one moved, update "
        "_MYPY_STATED_IN, and if the scan stopped finding it, fix the scan"
    )
    stale = [name for name in _TYPE_CHECKS_OF_A_USERS_CODE if name not in stated]
    assert not stale, (
        f"these pages state no mypy command any more; drop them from "
        f"_TYPE_CHECKS_OF_A_USERS_CODE: {stale}"
    )
    spelled_out = [
        f"{name}: {command}"
        for name, commands in sorted(stated.items())
        if name not in _TYPE_CHECKS_OF_A_USERS_CODE
        for command in commands
        if _spells_out(command)
    ]
    assert not spelled_out, (
        f"run the type check as bare `mypy`, whose paths are `files` under "
        f"[tool.mypy] in pyproject.toml: {spelled_out}"
    )


@pytest.mark.git_checkout
@pytest.mark.whole_tree
def test_no_stated_place_sets_a_search_path_for_mypy() -> None:
    """``MYPYPATH`` is ``mypy_path`` by another name, and mypy searches it first.

    Set where the type check runs, in a workflow's ``env`` or ``$GITHUB_ENV``,
    a shell line or a Makefile, it gives bare ``mypy`` a search path that
    ``pyproject.toml`` does not show, and a module there would take the place
    of an oracle table of the same name. A Makefile's assignment reaches the
    recipes whether it is exported or not, as soon as the variable is in the
    environment make starts from.
    """
    found = {
        name: settings
        for name, text in sorted(_stated_files().items())
        if (settings := _mypypath_settings_in(name, text))
    }
    assert not found, (
        f"give mypy its search path in `mypy_path` under [tool.mypy], "
        f"not through MYPYPATH: {found}"
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
        ("Its settings would move to `mypy.ini`.\n", []),
        ("```\npython -m mypy src\n```\n", ["python -m mypy src"]),
        ("`python3.12 -I -m mypy`\n", ["python3.12 -I -m mypy"]),
        ("`.venv/bin/mypy src scripts`\n", [".venv/bin/mypy src scripts"]),
        ("```\nMYPYPATH=tests mypy\n```\n", ["MYPYPATH=tests mypy"]),
        ("`uv run --frozen mypy src`\n", ["uv run --frozen mypy src"]),
        ("```\nmypy \\\n  src \\\n  scripts\n```\n", ["mypy src scripts"]),
        ("````md\n```bash\nmypy src\n```\n````\n", ["mypy src"]),
        ("~~~~\n~~~\nmypy src\n~~~\n~~~~\nRun `mypy`.\n", ["mypy src", "mypy"]),
    ],
    ids=[
        "fenced",
        "code span",
        "bare in prose",
        "prose",
        "chained",
        "other tool",
        "config file",
        "module",
        "module with options",
        "path",
        "variable set before",
        "wrapped",
        "continued",
        "shorter fence shown in a longer one",
        "tildes, and the prose after the block",
    ],
)
def test_the_command_reader_finds_a_command_and_only_a_command(
    text: str, expected: list[str]
) -> None:
    """The scan reads code, not prose, and any spelling of the program."""
    assert _markdown_commands(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("MYPY = $(BIN)/mypy\n\nlint:\n\t$(MYPY)\n", ["$(BIN)/mypy", "$(MYPY)"]),
        (
            "ifeq (,$(wildcard .venv))\n    MYPY = mypy\nelse\n"
            "    MYPY = $(BIN)/mypy src\nendif\n",
            ["mypy", "$(BIN)/mypy src"],
        ),
        ("MYPY = mypy\nMYPY += src\n", ["mypy", "$(MYPY) src"]),
        ("lint:\n\t$(PYTHON) -m mypy\n", ["$(PYTHON) -m mypy"]),
        (
            "CHECK := $(BIN)/mypy\n\nlint:\n\t@$(CHECK) \\\n\t    src\n",
            ["$(BIN)/mypy", "$(CHECK) src"],
        ),
        (
            "FIGURE_ENV = OMP_NUM_THREADS=1 \\\n\tPYTHONHASHSEED=0\n",
            [],
        ),
    ],
    ids=[
        "variable and recipe",
        "assignment inside ifeq",
        "appended",
        "module in a recipe",
        "another variable, continued",
        "no type check",
    ],
)
def test_the_makefile_reader_follows_the_program_into_its_variables(
    text: str, expected: list[str]
) -> None:
    """Assignments are read where they sit, and a holder of mypy is followed."""
    assert _makefile_commands(text) == expected


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("mypy", False),
        ("$(MYPY)", False),
        (".venv/bin/mypy", False),
        ("python -m mypy", False),
        ("$(PYTHON) -m mypy", False),
        ("uv run mypy", False),
        ("mypy # the gate", False),
        ("mypy src", True),
        ("mypy --strict", True),
        ("python -m mypy src", True),
        ("$(BIN)/mypy src", True),
        ("$(MYPY) $(MYPYFLAGS)", True),
        ("MYPYPATH=tests mypy", True),
    ],
)
def test_a_bare_command_is_told_from_one_that_spells_its_paths_out(
    command: str, *, expected: bool
) -> None:
    """What follows the program, or a search path set before it, is spelled out."""
    assert _spells_out(command) is expected


@pytest.mark.parametrize(
    ("name", "text", "expected"),
    [
        (
            "Makefile",
            "export MYPYPATH = vendor\nMYPY = mypy\n\nlint:\n\t$(MYPY)\n",
            ["export MYPYPATH = vendor"],
        ),
        ("Makefile", "MYPYPATH := vendor\n", ["MYPYPATH := vendor"]),
        ("Makefile", "override MYPYPATH += vendor\n", ["override MYPYPATH += vendor"]),
        ("Makefile", "lint:\n\tunset MYPYPATH; $(MYPY)\n", []),
        ("Makefile", "# MYPYPATH = vendor would shadow the oracles\n", []),
        (
            ".github/workflows/ci.yml",
            "jobs:\n  lint:\n    env:\n      MYPYPATH: tests\n"
            "    steps:\n    - run: mypy\n",
            ["MYPYPATH: tests"],
        ),
        (
            ".github/workflows/ci.yml",
            "jobs:\n  lint:\n    steps:\n"
            '    - run: echo "MYPYPATH=tests" >> "$GITHUB_ENV"\n',
            ['echo "MYPYPATH=tests" >> "$GITHUB_ENV"'],
        ),
        ("hooks/pre-push", "export MYPYPATH=tests\nmypy\n", ["export MYPYPATH=tests"]),
        ("tool.sh", 'echo "$MYPYPATH"\n[ "$MYPYPATH" = x ]\n', []),
        (
            "CONTRIBUTING.md",
            "```bash\nMYPYPATH=tests mypy\n```\n",
            ["MYPYPATH=tests mypy"],
        ),
        ("CONTRIBUTING.md", "Never set MYPYPATH=tests; `mypy` reads it.\n", []),
    ],
    ids=[
        "exported in a Makefile",
        "assigned in a Makefile",
        "appended with override",
        "unset in a recipe",
        "named in a comment",
        "workflow env",
        "written into GITHUB_ENV",
        "exported by a hook",
        "read, not set",
        "set before a fenced command",
        "named in prose",
    ],
)
def test_the_mypypath_reader_finds_an_assignment_and_only_one(
    name: str, text: str, expected: list[str]
) -> None:
    """Every way a file here could set ``MYPYPATH`` is read, and nothing else."""
    assert _mypypath_settings_in(name, text) == expected


def _covers(entry: str, root: str) -> bool:
    """Whether the ``files`` entry *entry* reaches every file under *root*."""
    within = pathlib.PurePosixPath(entry).parts
    return pathlib.PurePosixPath(root).parts[: len(within)] == within


@pytest.mark.parametrize(
    ("entry", "root", "expected"),
    [
        ("tests/static_typing", "tests/static_typing", True),
        ("tests", "tests/static_typing", True),
        (".", "src", True),
        ("tests/static", "tests/static_typing", False),
        ("tests/static_typing", "tests", False),
    ],
)
def test_a_files_entry_covers_itself_and_what_lies_under_it(
    entry: str, root: str, *, expected: bool
) -> None:
    """A parent directory in ``files`` covers a root; a sibling prefix does not."""
    assert _covers(entry, root) is expected


def test_bare_mypy_checks_every_root_the_gate_needs() -> None:
    """``files`` under [tool.mypy] reaches every root CI has to type check."""
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        files = tomllib.load(handle)["tool"]["mypy"]["files"]
    missing = [
        root for root in _MYPY_ROOTS if not any(_covers(entry, root) for entry in files)
    ]
    assert not missing, f"[tool.mypy] files no longer reaches {missing}"


@pytest.mark.git_checkout
def test_bare_mypy_reads_every_tracked_file_under_the_roots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Asked which files bare ``mypy`` checks, mypy names every one under the roots.

    ``files`` reaching a root is not enough: ``exclude`` drops whatever it
    matches while mypy walks the tree down from ``files``, each directory
    tested with a slash after its name, so a pattern can take part of a root
    out without a word. mypy's own discovery, run on the configuration bare
    ``mypy`` reads, answers for the patterns as mypy applies them.
    """
    # The job at the dependency floors installs no mypy.
    find_sources = pytest.importorskip("mypy.find_sources")
    config_parser = pytest.importorskip("mypy.config_parser")
    options_module = pytest.importorskip("mypy.options")
    # mypy resolves `files` and `exclude` from the working directory, and
    # records the configuration's directory in the environment.
    monkeypatch.chdir(_ROOT)
    monkeypatch.delenv("MYPY_CONFIG_FILE_DIR", raising=False)
    options = options_module.Options()
    complaints = io.StringIO()
    config_parser.parse_config_file(
        options, lambda: None, str(_ROOT / "pyproject.toml"), complaints, complaints
    )
    assert not complaints.getvalue(), complaints.getvalue()
    read = {
        pathlib.PurePath(source.path).as_posix()
        for source in find_sources.create_source_list(options.files, options)
    }
    tracked = _tracked(
        *(f"{root}/*.{suffix}" for root in _MYPY_ROOTS for suffix in ("py", "pyi"))
    )
    unread = sorted(set(tracked) - read)
    assert not unread, f"bare `mypy` no longer reads {unread}"


#: The error codes that, turned off, let an import mypy cannot read pass as
#: ``Any``: ``import`` and the two it covers.
_IMPORT_ERROR_CODES = frozenset({"import", "import-not-found", "import-untyped"})


def _silences_imports(settings: Mapping[str, object]) -> list[str]:
    """The settings among *settings* that let an import pass as ``Any`` unseen.

    A module mypy cannot find or read types for, ignored or with its error
    code turned off, and imports left unfollowed, which mypy reads as ``Any``.
    """
    found = ["ignore_missing_imports"] if settings.get("ignore_missing_imports") else []
    disabled = settings.get("disable_error_code", [])
    codes = disabled.split(",") if isinstance(disabled, str) else disabled
    if isinstance(codes, list):
        found += [
            f"disable_error_code {code}"
            for code in codes
            if str(code).strip() in _IMPORT_ERROR_CODES
        ]
    if settings.get("follow_imports") == "skip":
        found.append("follow_imports = skip")
    return found


def test_only_the_listed_packages_are_read_without_types() -> None:
    """No setting lets every import, or one of the repository's own, pass as ``Any``.

    A global ``ignore_missing_imports`` is what hid the oracle tables from the
    scripts that compare with them: mypy could not find them, and said
    nothing. The exemption lives in an override and names the packages that
    ship no types or that CI does not install, never a module of the
    package, the transition shim or a directory on ``mypy_path``.
    """
    with (_ROOT / "pyproject.toml").open("rb") as handle:
        mypy = tomllib.load(handle)["tool"]["mypy"]
    silenced = _silences_imports(mypy)
    assert not silenced, (
        f"[tool.mypy] lets every import mypy cannot read pass as Any: "
        f"{silenced}; name the packages in an override"
    )
    own = {
        entry.stem
        for directory in ("src", "stub/src", *mypy.get("mypy_path", []))
        for entry in (_ROOT / directory).iterdir()
        if entry.suffix in {".py", ".pyi"}
        or (entry.is_dir() and not entry.name.startswith((".", "_")))
    }
    exempted = [
        module
        for override in mypy.get("overrides", [])
        if _silences_imports(override)
        for module in (
            [override["module"]]
            if isinstance(override["module"], str)
            else override["module"]
        )
        if module.split(".")[0] in own
    ]
    assert not exempted, (
        f"an override lets the repository's own modules {exempted} pass as Any "
        f"when mypy cannot find them; they are found through mypy_path"
    )


def test_no_config_file_takes_the_place_of_pyproject() -> None:
    """mypy reads ``mypy.ini`` or ``.mypy.ini`` before ``pyproject.toml``.

    Either one, tracked or left behind locally, would make bare ``mypy``
    ignore ``[tool.mypy]`` without a word, and check whatever it lists.
    """
    present = [name for name in _MYPY_SHADOWING_CONFIGS if (_ROOT / name).exists()]
    assert not present, f"{present} would replace [tool.mypy] in pyproject.toml"


@pytest.mark.git_checkout
def test_no_llms_file_the_site_build_writes_is_tracked() -> None:
    """The shards and llms-full.txt are written by the build, with dated headers.

    ``.gitignore`` does not untrack a file already committed: a shard left in
    the index would be deleted from the working tree by every build
    (``generate_llms.py --build`` removes a shard the run did not write) while
    CI stayed green. Only the dateless ``llms.txt`` at the root is committed.
    """
    tracked = _tracked(
        "site/public/llms",
        "site/public/llms-full.txt",
        "site/public/llms.txt",
        "llms-full.txt",
    )
    assert tracked == [], tracked


def test_every_python_ci_job_has_a_time_limit() -> None:
    """A hung job of Python CI ends at its own limit, never at GitHub's six hours.

    Seven jobs had none, so one that hung held a runner for 360 minutes,
    and the account runs at most forty jobs at a time across its
    repositories: every runner a hung job holds is one a test leg of the
    next pull request waits for. Each job states its limit, above the
    longest run measured for it with room for a slow mirror or a loaded
    runner.
    """
    jobs = yaml.safe_load(_PYTHON_WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    unlimited = [name for name, job in jobs.items() if "timeout-minutes" not in job]
    assert unlimited == [], (
        f"these Python CI jobs have no timeout-minutes, so a hang holds a runner "
        f"for six hours: {unlimited}"
    )


#: The lanes of Python CI and the durations they are balanced on.
_CI_LANES = _ROOT / "tests" / "ci_lanes.json"
#: The condition of every link after the head of a lane: whatever the link
#: before it said, unless the run was cancelled, with any condition of the
#: job's own after it.
_LINK_CONDITION = re.compile(r"^\$\{\{ !cancelled\(\)(?: && \(.+\))? \}\}$")


def _ci_lanes() -> dict[str, object]:
    record: dict[str, object] = json.loads(_CI_LANES.read_text(encoding="utf-8"))
    return record


def _lane_shape_problems(
    jobs: Mapping[str, Mapping[str, object]], record: Mapping[str, object]
) -> list[str]:
    """Why the jobs of Python CI do not run in the lanes *record* lists, or ``[]``.

    Every job is a lane link, a job that starts with the run, or a job that
    waits on another for what it reads, and exactly one of them. There are at
    most two lanes and a job is in one: the head of a lane waits on nothing,
    each other link on the link before it alone, under ``!cancelled()``, so a
    red link skips none after it. A job outside the lanes waits only on the
    head of a lane, so it is not held up by the links before.
    """
    lanes = record["lanes"]
    parallel, after = record["parallel_jobs"], record["after_jobs"]
    assert isinstance(lanes, list)
    assert isinstance(parallel, dict)
    assert isinstance(after, dict)
    # The scope job answers before anything that may skip reads it, and waits
    # on nothing: a job's wait on it is no place in the lanes.
    scope = str(record.get("scope_job", ""))
    problems = []
    if scope and scope in jobs and _needs(dict(jobs[scope])):
        problems.append(f"{scope}: the scope job waits on another job")
    if len(lanes) > 2:
        problems.append(f"{len(lanes)} lanes, where two hold the short jobs")
    lane_of: dict[str, int] = {}
    for number, lane in enumerate(lanes, start=1):
        for name in lane:
            if name in lane_of:
                problems.append(f"{name}: in lane {lane_of[name]} and in lane {number}")
            else:
                lane_of[name] = number
    kinds = (
        ("a lane", lane_of),
        ("parallel_jobs", parallel),
        ("after_jobs", after),
        ("scope_job", {scope} - {""}),
    )
    for name in sorted(set(jobs) | set(lane_of) | set(parallel) | set(after)):
        listed = [kind for kind, names in kinds if name in names]
        if name not in jobs:
            problems.append(
                f"{name}: listed in {listed}, but Python CI has no such job"
            )
        elif len(listed) != 1:
            problems.append(
                f"{name}: listed in {listed or 'none'} of the lanes, parallel_jobs "
                "and after_jobs, where each job is in exactly one"
            )
    for lane in lanes:
        for index, name in enumerate(lane):
            if name not in jobs:
                continue
            job = jobs[name]
            needs = _needs(dict(job)) - {scope}
            before = lane[index - 1] if index else None
            wanted = {before} if before else set()
            if needs != wanted:
                problems.append(
                    f"{name}: waits on {sorted(needs) or 'nothing'}, where its lane "
                    f"has it wait on {before or 'nothing'}"
                )
            condition = str(job.get("if", ""))
            if before and not _LINK_CONDITION.match(condition):
                problems.append(
                    f"{name}: runs on {condition or 'the default success()'!r}, so a "
                    f"red {before} skips it and every link after it"
                )
    heads = {lane[0] for lane in lanes if lane}
    problems += [
        f"{name}: waits on another job, so it does not start with the run"
        for name in sorted(set(parallel) & set(jobs))
        if _needs(dict(jobs[name])) - {scope}
    ]
    for name in sorted(set(after) & set(jobs)):
        needs = _needs(dict(jobs[name])) - {scope}
        if not needs:
            problems.append(
                f"{name}: waits on no job, so it is no job that runs after one"
            )
        problems += [
            f"{name}: waits on {need}, which is no head of a lane, so it waits for "
            "the links before it"
            for need in sorted(needs & set(lane_of) - heads)
        ]
    return problems


def _lane_time_problems(record: Mapping[str, object]) -> list[str]:
    """Why a lane of *record* could end after the test matrix, or ``[]``.

    A lane takes the longer measured run of each of its jobs and the allowance
    for each link after its head, and stays within the bound; the bound is at
    most two thirds of the shortest matrix measured, and the allowance at least
    the longest wait measured for a job queued once the jobs it waits on ended.
    In each run measured with the lanes, the links of a lane waited no longer
    in all than the allowance for each, and the lane ended within the bound.
    """
    lanes, measured = record["lanes"], record["measured"]
    matrix, bound = record["tests_matrix_wall_s"], record["lane_bound_s"]
    allowance, link_waits = record["link_allowance_s"], record["link_waits_s"]
    assert isinstance(lanes, list)
    assert isinstance(measured, dict)
    assert isinstance(matrix, dict)
    assert isinstance(bound, int)
    assert isinstance(allowance, int)
    assert isinstance(link_waits, dict)
    run_s = measured["run_s"]
    problems = []
    walls = [seconds for run, seconds in matrix.items() if run != "about"]
    if not walls or 3 * bound > 2 * min(walls):
        problems.append(
            f"the bound of {bound} s is above two thirds of the shortest test "
            f"matrix measured ({min(walls, default=0)} s)"
        )
    waits = [
        seconds
        for run, by_job in link_waits.items()
        if run != "about"
        for seconds in by_job.values()
    ]
    if not waits or allowance < max(waits):
        problems.append(
            f"the allowance of {allowance} s for each link is below the longest "
            f"wait measured for a job queued after another ended "
            f"({max(waits, default=0)} s)"
        )
    lane_runs = record["lane_runs"]
    assert isinstance(lane_runs, dict)
    for run, seen in lane_runs.items():
        if run == "about":
            continue
        assert isinstance(seen, dict)
        for number, (lane, lane_waits, end) in enumerate(
            zip(lanes, seen["link_waits_s"], seen["end_s"], strict=True), start=1
        ):
            if len(lane_waits) != len(lane) - 1:
                problems.append(
                    f"run {run}, lane {number}: {len(lane_waits)} link waits "
                    f"recorded for {len(lane) - 1} links"
                )
            elif sum(lane_waits) > allowance * len(lane_waits):
                problems.append(
                    f"run {run}, lane {number}: its links waited {sum(lane_waits)} s "
                    f"in all, above the allowance of {allowance} s for each of its "
                    f"{len(lane_waits)} links"
                )
            if end > bound:
                problems.append(
                    f"run {run}, lane {number} ended {end} s after the run started, "
                    f"above the bound of {bound} s"
                )
    in_lanes = {name for lane in lanes for name in lane}
    problems += [
        f"{name}: a duration is recorded for a job in no lane"
        for name in sorted(set(run_s) - in_lanes)
    ]
    for number, lane in enumerate(lanes, start=1):
        missing = [name for name in lane if not run_s.get(name)]
        if missing:
            problems.append(f"lane {number}: no measured duration for {missing}")
            continue
        total = sum(max(run_s[name]) for name in lane) + allowance * (len(lane) - 1)
        if total > bound:
            problems.append(
                f"lane {number} takes {total} s, above the bound of {bound} s: move "
                "a job to the other lane or out of the lanes"
            )
    return problems


def _matrix_cells(job: Mapping[str, object]) -> list[dict[str, str]]:
    """Every cell of the plain list matrix of *job*, one cell when it has none."""
    strategy = job.get("strategy", {})
    assert isinstance(strategy, dict)
    matrix = strategy.get("matrix", {})
    assert isinstance(matrix, dict)
    cells: list[dict[str, str]] = [{}]
    for key, values in matrix.items():
        if isinstance(values, list):
            cells = [{**cell, key: str(value)} for cell in cells for value in values]
    return cells


def _uploaded_artifacts(job: Mapping[str, object]) -> set[str]:
    """The name of each artifact *job* uploads, in every cell of its matrix.

    An expression the matrix does not resolve stays as written, and matches
    nothing a reader names.
    """
    steps = job.get("steps", [])
    assert isinstance(steps, list)
    names = set()
    for step in steps:
        if str(step.get("uses", "")).startswith("actions/upload-artifact@"):
            name = str(step.get("with", {}).get("name", ""))
            for cell in _matrix_cells(job):
                resolved = name
                for key, value in cell.items():
                    expression = r"\$\{\{\s*matrix\." + re.escape(key) + r"\s*\}\}"
                    resolved = re.sub(expression, value.replace("\\", r"\\"), resolved)
                names.add(resolved)
    return names - {""}


def _downloaded_artifacts(job: Mapping[str, object]) -> list[re.Pattern[str]]:
    """What each download step of *job* takes, as the action matches it.

    ``name`` is one exact artifact name; ``pattern`` is a glob over the names.
    """
    steps = job.get("steps", [])
    assert isinstance(steps, list)
    readers = []
    for step in steps:
        if str(step.get("uses", "")).startswith("actions/download-artifact@"):
            given = step.get("with", {})
            if given.get("name"):
                readers.append(re.compile(re.escape(str(given["name"]))))
            elif given.get("pattern"):
                readers.append(re.compile(fnmatch.translate(str(given["pattern"]))))
    return readers


def _outside_lane_problems(
    jobs: Mapping[str, Mapping[str, object]], record: Mapping[str, object]
) -> list[str]:
    """Why a job of *record* outside the lanes should be in one, or ``[]``.

    A job starts with the run when it holds a macOS runner, whose cap of five
    the test legs fill, or when its shortest measured run takes longer than a
    quarter of the lane bound; any shorter job belongs in a lane. A job waits
    on another only to read an artifact that a job it waits on uploads.
    """
    parallel, after = record["parallel_jobs"], record["after_jobs"]
    measured, bound = record["measured"], record["lane_bound_s"]
    assert isinstance(parallel, dict)
    assert isinstance(after, dict)
    assert isinstance(measured, dict)
    assert isinstance(bound, int)
    run_s = measured["parallel_run_s"]
    problems = [
        f"{name}: a duration is recorded for a job that does not start with the run"
        for name in sorted(set(run_s) - set(parallel))
    ]
    for name in sorted(set(parallel) & set(jobs)):
        if str(jobs[name].get("runs-on", "")).startswith("macos"):
            continue
        if not run_s.get(name):
            problems.append(f"{name}: starts with the run, with no measured duration")
        elif 4 * min(run_s[name]) <= bound:
            problems.append(
                f"{name}: starts with the run, but its shortest measured run "
                f"({min(run_s[name])} s) is no longer than a quarter of the lane "
                f"bound ({bound} s), so it belongs in a lane"
            )
    for name in sorted(set(after) & set(jobs)):
        uploaded = {
            artifact
            for need in _needs(dict(jobs[name]))
            if need in jobs
            for artifact in _uploaded_artifacts(jobs[need])
        }
        if not any(
            reader.fullmatch(artifact)
            for reader in _downloaded_artifacts(jobs[name])
            for artifact in uploaded
        ):
            problems.append(
                f"{name}: reads no artifact of the jobs it waits on, so it belongs "
                "in a lane or with the jobs that start with the run"
            )
    return problems


def test_the_short_jobs_of_python_ci_run_in_two_lanes_that_skip_no_link() -> None:
    """A run starts its long jobs and the head of two lanes, not every job at once.

    The account runs at most forty jobs at a time across its repositories, and
    a run that started its twenty-eight jobs together filled the queue with
    short ones while the test legs of the next pull request waited. The short
    jobs keep a job, a check and an environment each, and run one after
    another: a red link leaves the rest of its lane to run, a cancelled run
    stops it, and the jobs that wait on quality or on the release build find
    them at the head of a lane.
    """
    problems = _lane_shape_problems(_python_ci_jobs(), _ci_lanes())
    assert problems == [], "\n".join(problems)


def test_each_lane_of_python_ci_ends_well_inside_the_test_matrix() -> None:
    """No lane, run one job after another, becomes the critical path of a run."""
    problems = _lane_time_problems(_ci_lanes())
    assert problems == [], "\n".join(problems)


def test_only_long_or_macos_jobs_start_with_the_run_and_only_readers_wait() -> None:
    """A short job cannot leave its lane to start with the run or to wait on a head.

    A job starts with the run when it holds a macOS runner, where a link would
    queue behind the test legs that fill the cap of five, or when it takes, in
    its shortest measured run, longer than a quarter of the lane bound. A job
    outside the lanes that waits on another reads an artifact it uploads.
    """
    problems = _outside_lane_problems(_python_ci_jobs(), _ci_lanes())
    assert problems == [], "\n".join(problems)


def test_a_lane_that_skips_a_link_or_shares_a_job_is_reported() -> None:
    """The lane readers name a link without its guard, a job in two lanes, a job
    left out of every list, a link that waits on the other lane and a lane
    measured past its bound.
    """
    jobs = _python_ci_jobs()
    record = _ci_lanes()
    lanes = record["lanes"]
    assert isinstance(lanes, list)
    first, second = lanes
    link = first[1]
    unguarded = {**jobs, link: {k: v for k, v in jobs[link].items() if k != "if"}}
    assert _lane_shape_problems(unguarded, record) == [
        f"{link}: runs on 'the default success()', so a red {first[0]} skips it and "
        "every link after it"
    ]
    shared = {**record, "lanes": [first, [*second, first[-1]]]}
    assert f"{first[-1]}: in lane 1 and in lane 2" in _lane_shape_problems(jobs, shared)
    merged = {**jobs, first[-1]: {**jobs[first[-1]], "needs": [first[-2], second[-1]]}}
    assert any(
        problem.startswith(f"{first[-1]}: waits on ")
        for problem in _lane_shape_problems(merged, record)
    )
    stray_job: dict[str, object] = {"name": "Stray / job"}
    stray = {**jobs, "stray": stray_job}
    assert _lane_shape_problems(stray, record) == [
        "stray: listed in none of the lanes, parallel_jobs and after_jobs, where "
        "each job is in exactly one"
    ]
    late = {**jobs, "sonar": {**jobs["sonar"], "needs": [first[1]]}}
    assert _lane_shape_problems(late, record) == [
        f"sonar: waits on {first[1]}, which is no head of a lane, so it waits for "
        "the links before it"
    ]
    measured = record["measured"]
    assert isinstance(measured, dict)
    slow = {
        **record,
        "measured": {
            **measured,
            "run_s": {**measured["run_s"], second[-1]: [record["lane_bound_s"]]},
        },
    }
    assert any(
        problem.startswith("lane 2 takes ") for problem in _lane_time_problems(slow)
    )
    loose = {**record, "lane_bound_s": 10**6}
    assert _lane_time_problems(loose)[0].startswith("the bound of 1000000 s")
    idle = {**record, "link_allowance_s": 30}
    assert any(
        problem.startswith("the allowance of 30 s for each link is below")
        for problem in _lane_time_problems(idle)
    )
    slow = {
        **record,
        "lane_runs": {
            "1": {"link_waits_s": [[900, 1, 1, 1, 1], [1, 1, 1]], "end_s": [2084, 1]}
        },
    }
    assert [
        problem for problem in _lane_time_problems(slow) if problem.startswith("run 1")
    ] == [
        "run 1, lane 1: its links waited 904 s in all, above the allowance of 180 s "
        "for each of its 5 links",
        "run 1, lane 1 ended 2084 s after the run started, above the bound of 2083 s",
        "run 1, lane 2: 3 link waits recorded for 4 links",
    ]


def test_a_short_job_outside_the_lanes_is_reported() -> None:
    """The reader names a short job that starts with the run, a job that starts
    with the run with no duration, and a job that waits on a head it reads
    nothing from; a job on a macOS runner starts with the run whatever its
    length.
    """
    jobs = _python_ci_jobs()
    record = _ci_lanes()
    parallel, measured = record["parallel_jobs"], record["measured"]
    assert isinstance(parallel, dict)
    assert isinstance(measured, dict)
    run_s, parallel_run_s = measured["run_s"], measured["parallel_run_s"]
    out = {
        **record,
        "parallel_jobs": {**parallel, "guards-source": "x"},
        "measured": {
            **measured,
            "parallel_run_s": {
                **parallel_run_s,
                "guards-source": run_s["guards-source"],
            },
        },
    }
    assert _outside_lane_problems(jobs, out) == [
        "guards-source: starts with the run, but its shortest measured run (325 s) "
        "is no longer than a quarter of the lane bound (2083 s), so it belongs in a "
        "lane"
    ]
    unmeasured = {**out, "measured": measured}
    assert _outside_lane_problems(jobs, unmeasured) == [
        "guards-source: starts with the run, with no measured duration"
    ]
    after = record["after_jobs"]
    assert isinstance(after, dict)
    waiting = {**record, "after_jobs": {**after, "video": "x"}}
    video = {**jobs, "video": {**jobs["video"], "needs": "quality"}}
    assert _outside_lane_problems(video, waiting) == [
        "video: reads no artifact of the jobs it waits on, so it belongs in a lane "
        "or with the jobs that start with the run"
    ]
    blind = {**jobs, "sonar": {**jobs["sonar"], "needs": "quality"}}
    assert _outside_lane_problems(blind, record) == [
        "sonar: reads no artifact of the jobs it waits on, so it belongs in a lane "
        "or with the jobs that start with the run"
    ]

    def reading(job: str, given: dict[str, str]) -> dict[str, dict[str, object]]:
        steps = jobs[job]["steps"]
        assert isinstance(steps, list)
        swapped = [
            {**step, "with": given}
            if str(step.get("uses", "")).startswith("actions/download-artifact@")
            else step
            for step in steps
        ]
        return {**jobs, job: {**jobs[job], "steps": swapped}}

    # An exact name is not a prefix: no leg uploads "test-results" itself.
    assert _outside_lane_problems(
        reading("sonar", {"name": "test-results"}), record
    ) == [
        "sonar: reads no artifact of the jobs it waits on, so it belongs in a lane "
        "or with the jobs that start with the run"
    ]
    assert _outside_lane_problems(
        reading("pr-comment", {"pattern": "test-results-linux-*"}), record
    ) == [
        "pr-comment: reads no artifact of the jobs it waits on, so it belongs in a "
        "lane or with the jobs that start with the run"
    ]
    assert (
        _outside_lane_problems(
            reading("sonar", {"name": "test-results-windows-latest-3.12"}), record
        )
        == []
    )
    assert str(jobs["mps"]["runs-on"]).startswith("macos")
    short_mps = {
        **record,
        "measured": {**measured, "parallel_run_s": {**parallel_run_s, "mps": [1]}},
    }
    assert _outside_lane_problems(jobs, short_mps) == []
    stale = {
        **record,
        "measured": {
            **measured,
            "parallel_run_s": {**parallel_run_s, "video": run_s["video"]},
        },
    }
    assert _outside_lane_problems(jobs, stale) == [
        "video: a duration is recorded for a job that does not start with the run"
    ]


#: The jobs of Python CI that group several guards or checks, each run as a
#: step of its own: the five built from jobs that each ran one, and the four
#: kept apart that carry several verdicts.
_GROUPED_JOBS = (
    "guards-prose",
    "guards-source",
    "guards-package",
    "built-package",
    "baseline-glibc",
)
_SEVERAL_VERDICTS = ("quality", "figures", "minimum-versions", "tests-perf")
#: The jobs that install nothing with pip, so every script they run stays in
#: the probe of tests/test_scripts_without_numpy.py that imports it bare.
_INSTALL_NOTHING = ("guards-prose", "guards-source")
#: The ids of the steps that set a job up, after its checkout.
_SETUP_IDS = frozenset({"checkout", "python", "install", "tooling"})
#: A condition that runs a step whatever the steps before it said, unless the
#: run was cancelled, and names the step it needs.
_RUNS_UNLESS_CANCELLED = re.compile(r"^\$\{\{ !cancelled\(\) && .*\}\}$")
_NEEDS_STEP = re.compile(r"steps\.([\w-]+)\.outcome == 'success'")
#: The two conditions a test holds literally elsewhere: the golden-digest test
#: runs after a failed measurement and the measured file is kept whatever
#: happened (test_the_engine_digests_test_names_a_moved_digest_after_the_
#: measurement_fails).
_KEPT_CONDITIONS = frozenset(
    {"(success() || failure()) && steps.avx512.outcome == 'success'", "always()"}
)
#: The last step of a grouped job, and the condition it runs on: after a
#: failure, unless the failure was the checkout, which leaves no script to run
#: and would fail the job a second time.
_SUMMARY = "python3 .github/scripts/failed_steps.py"
_SUMMARY_CONDITION = "${{ failure() && steps.checkout.outcome == 'success' }}"
#: A guard that only reads: a checker script, or a generator asked to compare.
_READS_ONLY = re.compile(r"\bscripts/check_\w+\.py\b|\s--check\b")
#: A step that writes what a drift gate then compares.
_REGENERATES = re.compile(r"^make [\w-]+$|\bscripts/generate_\w+\.py(?!.*--check)")
#: The step that puts a checkout back as committed.
_RESETS = ("git reset --hard", "git clean -fd")


def _python_ci_jobs(text: str | None = None) -> dict[str, dict[str, object]]:
    """The jobs of python-app.yml, or of *text* written in its place."""
    if text is None:
        text = _PYTHON_WORKFLOW.read_text(encoding="utf-8")
    jobs: dict[str, dict[str, object]] = yaml.safe_load(text)["jobs"]
    return jobs


def _steps_of(job: Mapping[str, object]) -> list[dict[str, object]]:
    steps = job.get("steps")
    assert isinstance(steps, list)
    return steps


def _is_setup(step: Mapping[str, object]) -> bool:
    uses = str(step.get("uses", ""))
    return uses.startswith("actions/checkout@") or step.get("id") in _SETUP_IDS


def _step_shape_problems(name: str, job: Mapping[str, object]) -> list[str]:
    """Why the steps of *job* would let one check hide another, or ``[]``.

    After the steps that set the job up, every step has an id and runs under
    ``!cancelled()`` and the outcome of a step before it that it needs; none
    runs under ``always()``, which starts a step in a cancelled run. The
    summary of a grouped job, its last step, runs on ``failure()`` once the
    checkout succeeded, and the two conditions of the golden digests are kept
    as their test holds them.
    """
    steps = _steps_of(job)
    problems = []
    seen: set[str] = set()
    setup = True
    for index, step in enumerate(steps):
        label = f"{name} step {index} ({step.get('name') or step.get('uses')})"
        if setup and _is_setup(step):
            if "id" in step:
                seen.add(str(step["id"]))
            continue
        setup = False
        condition = str(step.get("if", ""))
        if _SUMMARY in str(step.get("run", "")):
            if condition != _SUMMARY_CONDITION:
                problems.append(
                    f"{label}: the summary runs on {condition!r}, so a failed "
                    "checkout fails the job again on a script that is not there"
                )
            elif "checkout" not in seen:
                problems.append(f"{label}: the summary needs a checkout with that id")
            continue
        if condition in _KEPT_CONDITIONS:
            if "id" in step:
                seen.add(str(step["id"]))
            continue
        if "id" not in step:
            problems.append(f"{label}: no id, so its outcome cannot be named")
        if "always()" in condition:
            problems.append(f"{label}: always() starts it in a cancelled run")
        if not _RUNS_UNLESS_CANCELLED.match(condition):
            problems.append(
                f"{label}: runs on {condition or 'the default success()'!r}, so a "
                "failure before it hides its verdict"
            )
        needed = _NEEDS_STEP.findall(condition)
        if not needed:
            problems.append(f"{label}: names no step it needs")
        problems += [
            f"{label}: needs {other!r}, which is no step before it"
            for other in needed
            if other not in seen
        ]
        if "id" in step:
            seen.add(str(step["id"]))
    return problems


def _group_problems(name: str, job: Mapping[str, object]) -> list[str]:
    """Why a grouped job is not shaped as its guards need, or ``[]``."""
    steps = _steps_of(job)
    problems = []
    env = job.get("env") or {}
    assert isinstance(env, dict)
    if str(env.get("PYTHONDONTWRITEBYTECODE")) != "1":
        problems.append(f"{name}: a guard may write bytecode into the checkout")
    if "timeout-minutes" not in job:
        problems.append(f"{name}: no timeout-minutes")
    summary_env = steps[-1].get("env") if steps else None
    if not steps or _SUMMARY not in str(steps[-1].get("run", "")):
        problems.append(f"{name}: the last step does not name the failed steps")
    elif not isinstance(summary_env, dict) or (
        summary_env.get("STEPS") != "${{ toJSON(steps) }}"
    ):
        problems.append(f"{name}: the summary is not handed the steps context")
    for index, step in enumerate(steps):
        run = str(step.get("run", ""))
        if _READS_ONLY.search(run) and len(run.strip().splitlines()) != 1:
            problems.append(
                f"{name} step {index}: a guard shares its run with other lines, "
                "so a probe that reads it one line at a time misses it"
            )
    return problems


def _drift_order_problems(name: str, job: Mapping[str, object]) -> list[str]:
    """Why a guard of *job* reads a checkout a regeneration wrote, or ``[]``.

    The guards that only read come first; then a step fails when one of them
    wrote into the checkout; then each regeneration starts from a checkout
    put back as committed since the one before it, so a drift gate says only
    what is its own. The gates that compare are shell after their
    regeneration, never a checker script.
    """
    problems = []
    clean_tree_at = None
    regenerated = False
    reset_since = False
    for index, step in enumerate(_steps_of(job)):
        run = str(step.get("run", "")).strip()
        if step.get("id") == "clean-tree":
            clean_tree_at = index
        if all(command in run for command in _RESETS):
            if clean_tree_at is None:
                problems.append(
                    f"{name} step {index}: resets before the clean-tree step"
                )
            reset_since = True
            continue
        if _READS_ONLY.search(run) and (regenerated or reset_since):
            problems.append(
                f"{name} step {index}: a guard after a reset or a regeneration "
                "reads a checkout it did not find"
            )
        if _REGENERATES.search(run):
            if not reset_since:
                problems.append(
                    f"{name} step {index}: regenerates without first putting the "
                    "checkout back as committed"
                )
            regenerated = True
            reset_since = False
    if clean_tree_at is None:
        problems.append(f"{name}: no step fails when a guard wrote into the checkout")
    return problems


def test_no_check_of_a_grouped_job_hides_another() -> None:
    """Each guard is a step that runs whatever the others said, and names itself.

    Thirty-five jobs each ran one guard or two; grouped into five, a guard
    that ran only when every one before it passed would leave its verdict to
    the next run, one failure at a time. The jobs kept apart that carry
    several checks are held the same way: a ruff finding used to hide mypy,
    bandit and zizmor. A grouped job ends on a step that names every step
    that failed, and writes no bytecode beside what its guards read.
    """
    jobs = _python_ci_jobs()
    problems = []
    for name in (*_GROUPED_JOBS, *_SEVERAL_VERDICTS):
        problems += _step_shape_problems(name, jobs[name])
    for name in _GROUPED_JOBS:
        problems += _group_problems(name, jobs[name])
    assert problems == []


def test_every_drift_gate_of_the_guard_groups_starts_from_the_committed_checkout() -> (
    None
):
    """A drift gate says what is stale on its own, never what a guard left.

    The conformance gate reads git status over the whole checkout: run after
    a guard that wrote a file, or after the API reference regeneration, it
    would call the report stale for a file that is not its own.
    """
    jobs = _python_ci_jobs()
    problems = []
    for name in ("guards-prose", "guards-source", "guards-package"):
        problems += _drift_order_problems(name, jobs[name])
    assert problems == []


def test_the_guard_groups_that_install_nothing_stay_so() -> None:
    """A pip line in either job would take its scripts out of the bare probe.

    tests/test_scripts_without_numpy.py imports every script of a job that
    installs nothing with no site-packages at all; a job that installs the
    project is left out of that probe, so one pip line would drop thirty
    scripts from it without failing anything.
    """
    jobs = _python_ci_jobs()
    installing = [
        f"{name}: {line.strip()}"
        for name in _INSTALL_NOTHING
        for step in _steps_of(jobs[name])
        for line in str(step.get("run", "")).splitlines()
        if re.search(r"\bpip3?\s+install\b|-m\s+pip\b", line)
    ]
    assert installing == []


#: The methods by which a script writes a file named by a path.
_PATH_WRITES = frozenset({"write_text", "write_bytes"})


def _written_paths(script: str) -> list[str]:
    """Where *script* writes, relative to the root, by its own ``ROOT`` paths.

    Every call of ``write_text`` or ``write_bytes`` is read, and its path is
    resolved through the module's ``NAME = ROOT / "a" / "b"`` constants; an
    f-string part stands for one sample name of its pattern, and any other
    part built at run time ends the path at the directory before it. A write
    whose path does not resolve is returned as ``?<line>``, so a script that
    writes somewhere this reader cannot follow fails the test instead of
    passing it unseen.
    """
    tree = ast.parse((_ROOT / script).read_text(encoding="utf-8"))
    constants: dict[str, list[str]] = {"ROOT": []}

    def resolve(node: ast.expr) -> list[str] | None:
        if isinstance(node, ast.Name):
            return constants.get(node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            head = resolve(node.left)
            if head is None:
                return None
            if isinstance(node.right, ast.Constant) and isinstance(
                node.right.value, str
            ):
                return [*head, node.right.value]
            if isinstance(node.right, ast.JoinedStr):
                # A name built at run time, as one sample of its pattern.
                sample = "".join(
                    str(part.value) if isinstance(part, ast.Constant) else "0"
                    for part in node.right.values
                )
                return [*head, sample]
            return head
        return None

    for statement in tree.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            value = resolve(statement.value)
            if isinstance(target, ast.Name) and value is not None:
                constants[target.id] = value
    written = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _PATH_WRITES
        ):
            parts = resolve(node.func.value)
            written.append("/".join(parts) if parts else f"?{node.lineno}")
    return sorted(set(written))


def _llms_outputs(recipe: str) -> list[str]:
    """The paths ``make llms`` writes, by the commands of its *recipe*."""
    outputs = []
    for line in recipe.splitlines():
        words = shlex.split(line)
        if "scripts/agent-md.mjs" in words:
            # The recipe runs it from site/, so its paths start from there.
            base = pathlib.PurePosixPath("site")
            for option in ("--dump", "--docs"):
                if option in words:
                    path = base / words[words.index(option) + 1]
                    outputs.append(posixpath.normpath(path.as_posix()))
        script = next((word for word in words if word.endswith(".py")), None)
        if script is not None:
            outputs += _written_paths(script)
    return outputs


def _llms_gate_problems(
    recipe: str, gate: str, ignored: Callable[[list[str]], set[str]]
) -> list[str]:
    """The committed paths ``make llms`` writes that the llms gate never diffs."""
    match = re.search(r"git diff --exit-code -- ([^;\n]+?)(?:;|\n|$)", gate)
    if match is None:
        return ["the llms gate runs no `git diff --exit-code -- <paths>`"]
    compared = shlex.split(match.group(1))
    outputs = _llms_outputs(recipe)
    unreadable = [path for path in outputs if path.startswith("?")]
    committed = sorted(set(outputs) - set(unreadable) - ignored(outputs))
    return [
        f"scripts/generate_llms.py writes at line {path[1:]} to a path this "
        "test cannot follow"
        for path in unreadable
    ] + [
        f"make llms writes {path}, which the llms gate does not compare"
        for path in committed
        if not any(path == root or path.startswith(f"{root}/") for root in compared)
    ]


def _git_ignored(paths: list[str]) -> set[str]:
    """The *paths* git ignores, so that no commit ever carries them."""
    named = [path for path in paths if not path.startswith("?")]
    listed = child_process.run(
        ["git", "check-ignore", "--no-index", "--", *named],
        cwd=_ROOT,
        capture_output=True,
        timeout=120,
    ).stdout.decode("utf-8")
    return set(listed.splitlines())


def _llms_recipe() -> str:
    text = (_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^llms:.*\n((?:\t.*\n)+)", text, re.MULTILINE)
    assert match is not None, "the Makefile has no llms target"
    return match.group(1)


@pytest.mark.git_checkout
def test_the_llms_gate_compares_every_committed_file_make_llms_writes() -> None:
    """A file the generator starts writing is held to its commit at once.

    The gate regenerates with `make llms` and then diffs a list of paths
    typed into the workflow. A new committed output of the generator, left
    out of that list, would be rewritten on every run and never compared:
    the gate stays green while the committed file goes stale.
    """
    gate = next(
        str(step.get("run", ""))
        for step in _steps_of(_python_ci_jobs()["guards-prose"])
        if step.get("id") == "llms"
    )
    assert _llms_gate_problems(_llms_recipe(), gate, _git_ignored) == []


def test_the_llms_gate_reader_names_an_output_left_out_of_the_diff() -> None:
    """The reader above, on a gate that dropped ``docs`` from its list."""
    gate = "if ! git diff --exit-code -- llms.txt; then\n  exit 1\nfi\n"

    def ignored(paths: list[str]) -> set[str]:
        return {path for path in paths if path.startswith(("build/", "site/"))}

    assert _llms_gate_problems(_llms_recipe(), gate, ignored) == [
        "make llms writes docs, which the llms gate does not compare"
    ]


#: The groups of Python CI, in the order their jobs stand in the file.
_JOB_GROUPS = (
    "Scope",
    "Tests",
    "Generated",
    "Docs",
    "Lint",
    "Guards",
    "Package",
    "Platform",
    "FDTD",
    "Runtime",
    "Report",
)
#: The longest visible job name the checks list of a pull request shows whole.
_JOB_NAME_BUDGET = 24
_JOB_NAME = re.compile(r"^(?P<group>[A-Za-z]+) / \S.*$")


def job_name_problems(jobs: Mapping[str, Mapping[str, object]]) -> list[str]:
    """Each job of *jobs* whose visible name is not ``<Group> / <subject>``.

    A name says the group first and what the job checks after it, a group is
    one of ``_JOB_GROUPS`` and the jobs of one group stand together, in that
    order, and a name with nothing to fill in fits the checks list whole.
    """
    problems: list[str] = []
    last = 0
    for key, job in jobs.items():
        name = str(job.get("name") or "")
        match = _JOB_NAME.match(name)
        if match is None or match.group("group") not in _JOB_GROUPS:
            problems.append(
                f"{key}: {name or '(no name)'!r} is not '<Group> / <subject>'"
            )
            continue
        rank = _JOB_GROUPS.index(match.group("group"))
        if rank < last:
            problems.append(
                f"{key}: {name!r} stands after a job of {_JOB_GROUPS[last]}"
            )
        last = max(last, rank)
        if "${{" not in name and len(name) > _JOB_NAME_BUDGET:
            problems.append(f"{key}: {name!r} is longer than {_JOB_NAME_BUDGET}")
    return problems


def test_a_job_name_is_reported_unless_it_says_its_group_and_its_subject() -> None:
    jobs: dict[str, Mapping[str, object]] = {
        "quality": {"name": "Lint / code, workflows"},
        "tests": {"name": "Tests / numba JIT 3.14"},
        "sonar": {},
        "video": {"name": "Videos encode with a real ffmpeg"},
        "notebook": {"name": "Runtime / phonometry runs in a notebook kernel"},
        "remote": {"name": "Remote / node"},
    }
    assert job_name_problems(jobs) == [
        "tests: 'Tests / numba JIT 3.14' stands after a job of Lint",
        "sonar: '(no name)' is not '<Group> / <subject>'",
        "video: 'Videos encode with a real ffmpeg' is not '<Group> / <subject>'",
        "notebook: 'Runtime / phonometry runs in a notebook kernel' is longer than 24",
        "remote: 'Remote / node' is not '<Group> / <subject>'",
    ]
    assert (
        job_name_problems({"tests": {"name": "Tests / ${{ matrix.os }} and more"}})
        == []
    )


#: The start of a step name that orders a check rather than saying what holds:
#: a verdict step is named for its invariant, and a step that builds and then
#: compares or checks is a verdict step too.
_IMPERATIVE_VERDICT = re.compile(
    r"^(?:Check|Fail|Run|Lint|Compare|Rebuild|Verify|Test|Audit|Validate|Ensure)\b"
    r"|\band (?:compare|check)\b"
)


def step_name_problems(jobs: Mapping[str, Mapping[str, object]]) -> list[str]:
    """Each step of *jobs* whose name orders a check instead of stating it.

    The checks page lists a failed step by its name: "Check the metadata"
    says what ran, "The sdist and wheel pass twine check" says what no
    longer holds.
    """
    problems = []
    for key, job in jobs.items():
        steps = job.get("steps")
        assert isinstance(steps, list)
        for step in steps:
            name = str(step.get("name") or "")
            if _IMPERATIVE_VERDICT.search(name):
                problems.append(f"{key}: {name!r} orders a check; name what holds")
    return problems


def test_a_step_named_as_an_order_to_check_is_reported() -> None:
    jobs: dict[str, Mapping[str, object]] = {
        "quality": {
            "steps": [
                {"name": "Check formatting with Ruff"},
                {"name": "Every file is formatted (ruff)"},
                {"name": "Build both again and compare them"},
                {"name": "Install the runtime dependencies"},
                {"uses": "actions/checkout@v7"},
            ]
        },
        "remote": {"steps": [{"name": "Lint the Dockerfile"}]},
    }
    assert step_name_problems(jobs) == [
        "quality: 'Check formatting with Ruff' orders a check; name what holds",
        "quality: 'Build both again and compare them' orders a check; name what holds",
        "remote: 'Lint the Dockerfile' orders a check; name what holds",
    ]


def test_every_python_ci_verdict_step_is_named_for_what_holds() -> None:
    """A step that judges says the invariant it holds, as the guards' steps do."""
    assert step_name_problems(_python_ci_jobs()) == []


def test_every_python_ci_job_says_its_group_and_what_it_checks() -> None:
    """The checks list of a pull request cuts a job's name at about 24 characters.

    Named for its invariant, most jobs read the same up to the cut, and
    fifteen began with "Every". Named ``<Group> / <subject>``, the group
    sorts the list and the subject stays whole; the guide cites each check by
    its job key and step id, so a renamed job leaves every citation standing.
    """
    assert job_name_problems(_python_ci_jobs()) == []


#: The guard groups of Python CI that the Makefile runs as one target each.
_MAKE_GUARD_GROUPS = ("guards-prose", "guards-source", "guards-package")
_GUARD_RUN = re.compile(r"^python3? (scripts/\S+\.py(?: [^|;&]*)?)$")
_RECIPE_GUARD = re.compile(
    r'^\$\(PYTHON\) (scripts/\S+\.py(?: [^|;&]*?)?) \|\| failed="\$\$failed ([\w-]+)"; \\$'
)


def ci_guards(job: Mapping[str, object]) -> list[tuple[str, str]]:
    """The guard commands of *job* in the order it runs them, each with its step id."""
    guards: list[tuple[str, str]] = []
    for step in _steps_of(job):
        match = _GUARD_RUN.match(str(step.get("run", "")).strip())
        if match is not None:
            guards.append((match.group(1).strip(), str(step.get("id"))))
    return guards


def make_guards(makefile: str, target: str) -> list[tuple[str, str]] | None:
    """The guard commands the recipe of *target* runs, each with the id it reports.

    None when the Makefile has no such target. A line of the recipe that runs
    a script some other way than one guard that reports its id is returned as
    it stands, with no id, so a comparison with the job names it.
    """
    lines = makefile.splitlines()
    try:
        start = lines.index(f"{target}:")
    except ValueError:
        return None
    guards: list[tuple[str, str]] = []
    for line in lines[start + 1 :]:
        if not line.startswith("\t"):
            break
        body = line.strip()
        match = _RECIPE_GUARD.match(body)
        if match is not None:
            guards.append((match.group(1).strip(), match.group(2)))
        elif "scripts/" in body:
            guards.append((body, ""))
    return guards


def test_a_make_guard_group_that_parts_from_its_job_is_reported() -> None:
    job = {
        "steps": [
            {"id": "python", "uses": "actions/setup-python@v6"},
            {"id": "dead-constants", "run": "python scripts/check_dead_constants.py"},
            {
                "id": "decimal-comma",
                "run": "python scripts/check_decimal_comma.py --english",
            },
        ]
    }
    assert ci_guards(job) == [
        ("scripts/check_dead_constants.py", "dead-constants"),
        ("scripts/check_decimal_comma.py --english", "decimal-comma"),
    ]
    recipe = (
        "guards-x:\n"
        '\t@failed=""; \\\n'
        '\t$(PYTHON) scripts/check_dead_constants.py || failed="$$failed dead-constants"; \\\n'
        '\t$(PYTHON) scripts/check_decimal_comma.py || failed="$$failed decimal-comma"; \\\n'
        "\t$(PYTHON) scripts/check_em_dashes.py; \\\n"
        '\tif [ -n "$$failed" ]; then exit 1; fi\n'
        "\n"
        "other:\n"
        "\t$(PYTHON) scripts/check_raises_blocks.py\n"
    )
    assert make_guards(recipe, "guards-x") == [
        ("scripts/check_dead_constants.py", "dead-constants"),
        ("scripts/check_decimal_comma.py", "decimal-comma"),
        ("$(PYTHON) scripts/check_em_dashes.py; \\", ""),
    ]
    assert make_guards(recipe, "guards-y") is None


def test_each_make_guard_group_runs_what_its_ci_job_runs() -> None:
    """``make guards-source`` and its two siblings are the CI job, on a laptop.

    Each target runs the guards of its job with the same arguments, in the
    same order, and reports a failed one by its step id, so a guard added to
    a job and not to its target, or run there with other flags, fails here.
    """
    jobs = _python_ci_jobs()
    makefile = _MAKEFILE.read_text(encoding="utf-8")
    parted = {
        group: (ci_guards(jobs[group]), make_guards(makefile, group))
        for group in _MAKE_GUARD_GROUPS
        if ci_guards(jobs[group]) != make_guards(makefile, group)
    }
    assert parted == {}
