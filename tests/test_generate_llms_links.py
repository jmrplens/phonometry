#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The links of the mirror reach the exports as addresses that resolve.

``llms-full.txt`` and the shards are flat text served from the site, so a link
written relative to the mirror page that holds it resolves against the export's
own address and leads nowhere. The generator only rewrote links to ``.md``
pages: the compute guide's links to ``engine-digests.json`` and
``gpu-parity.lock`` went out as ``../../engine-digests.json``, which resolves to
docs.jmrp.io/engine-digests.json, a 404. Every relative target is now resolved
in the repository: a mirror page becomes its route on the site, any other file
its address on GitHub, and a target that names no file stops the run.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms
from markdown_fences import NOT_INLINE_ROLES, page_lines
from markdown_spans import blank_inline_spans_by_block

if TYPE_CHECKING:
    from guard_caches import FreshCaches

BLOB = "https://github.com/jmrplens/phonometry/blob/main"
TREE = "https://github.com/jmrplens/phonometry/tree/main"
SITE = "https://docs.jmrp.io/phonometry"
PAGE = "simulation/compute.md"


def test_a_link_to_a_file_of_the_repository_becomes_its_address_on_github() -> None:
    text = "[lock](../../gpu-parity.lock) and [digests](../../engine-digests.json#L1)"
    assert llms._absolutize_links(text, PAGE) == (
        f"[lock]({BLOB}/gpu-parity.lock) and [digests]({BLOB}/engine-digests.json#L1)"
    )


@pytest.mark.parametrize(
    ("written", "published"),
    [
        (
            '[lock](../../gpu-parity.lock "the proof")',
            f'[lock]({BLOB}/gpu-parity.lock "the proof")',
        ),
        ("[lock](<../../gpu-parity.lock>)", f"[lock]({BLOB}/gpu-parity.lock)"),
        (
            "[lock](../../gpu-parity.lock?plain=1)",
            f"[lock]({BLOB}/gpu-parity.lock?plain=1)",
        ),
        ("[lock]: ../../gpu-parity.lock", f"[lock]: {BLOB}/gpu-parity.lock"),
        (
            '<a href="../../gpu-parity.lock">lock</a>',
            f'<a href="{BLOB}/gpu-parity.lock">lock</a>',
        ),
    ],
)
def test_every_form_of_a_link_is_rewritten(written: str, published: str) -> None:
    """A title, angle brackets, a query, a reference definition and a tag's attribute."""
    assert llms._absolutize_links(written, PAGE) == published


def test_a_mirror_page_becomes_its_route_and_one_with_no_site_page_its_file() -> None:
    text = (
        "[banks](../signals/filters/filter-banks.md#bands), [signals](../signals/), "
        "[guide](../contributing/index.md), [report](../CONFORMANCE.md)"
    )
    assert llms._absolutize_links(text, PAGE) == (
        f"[banks]({SITE}/signals/filters/filter-banks/#bands), [signals]({SITE}/signals/), "
        f"[guide]({BLOB}/docs/contributing/index.md), [report]({SITE}/reference/conformance/)"
    )


@pytest.mark.parametrize(
    "target",
    [
        "../../no-such.json",
        "../filters/filter-banks.md",
        "../../../outside.md",
        "../no-such-folder/",
    ],
)
def test_a_target_that_names_no_file_of_the_repository_stops_the_run(
    target: str,
) -> None:
    with pytest.raises(
        SystemExit,
        match=rf"docs/{re.escape(PAGE)} links {re.escape(target)}, which names no file",
    ):
        llms._absolutize_links(f"[x]({target})", PAGE)


def test_a_page_of_a_tree_outside_the_repository_is_resolved_in_that_tree(
    tmp_path: Path, fresh_caches: FreshCaches
) -> None:
    """The mirror is read from wherever ``DOCS`` points, as the tests of the shards point it.

    A page of the tree is named as git lists it, ``docs/`` and its path under
    the tree, so a link to another page of it becomes that page's route on
    the site and a link to no file stops the run with the page and the link,
    where the page's path was taken relative to the repository and stopped
    the run with a ``ValueError``.
    """
    docs, content = tmp_path / "docs", tmp_path / "content"
    for tree in (docs, content):
        (tree / "a").mkdir(parents=True)
        for name in ("a/one.md", "a/two.md"):
            (tree / name).write_text("# A page\n", encoding="utf-8")
    fresh_caches(llms, DOCS=docs, CONTENT=content)

    assert llms._absolutize_links("[two](two.md#top)", "a/one.md") == (
        f"[two]({SITE}/a/two/#top)"
    )
    with pytest.raises(
        SystemExit, match=r"docs/a/one\.md links three\.md, which names no file"
    ):
        llms._absolutize_links("[three](three.md)", "a/one.md")


@pytest.mark.git_checkout
def test_a_file_git_ignores_is_no_file_of_the_repository(
    fresh_caches: FreshCaches,
) -> None:
    """The check reads what git keeps, not what one checkout holds: a local plan is on disk and nowhere else."""
    fresh_caches(llms)
    kept = llms._repository_files()
    assert kept is not None
    assert "pyproject.toml" in kept
    fresh_caches(llms, _repository_files=lambda: kept - {"pyproject.toml"})
    with pytest.raises(
        SystemExit, match=r"links \.\./\.\./pyproject\.toml, which names no file"
    ):
        llms._absolutize_links("[p](../../pyproject.toml)", PAGE)


def test_a_file_git_keeps_is_one_of_the_repository_where_the_checkout_leaves_it_out(
    monkeypatch: pytest.MonkeyPatch, fresh_caches: FreshCaches
) -> None:
    """The docs build checks out a sparse cone (.github, docs, scripts, site).

    There src/ and tests/ are in git's index and not on disk, and a link into
    them still names a file GitHub serves. A file git does not keep yet counts
    only while it is on disk.
    """
    cached = ["src/phonometry/filters/_not_in_this_checkout.py", "pyproject.toml"]
    others = ["docs/simulation/listed-and-gone.md"]

    def ls_files(args: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        assert args[:2] == ["git", "ls-files"], args
        listed = (cached if "--cached" in args else []) + (
            others if "--others" in args else []
        )
        return subprocess.CompletedProcess(
            args, 0, "".join(f"{n}\0" for n in listed), ""
        )

    fresh_caches(llms)
    llms._ignored_paths()  # read from git once, before the listing is replaced
    monkeypatch.setattr(subprocess, "run", ls_files)
    text = "[f](../../src/phonometry/filters/_not_in_this_checkout.py), [s](../../src/)"
    assert llms._absolutize_links(text, PAGE) == (
        f"[f]({BLOB}/src/phonometry/filters/_not_in_this_checkout.py), [s]({TREE}/src)"
    )
    with pytest.raises(SystemExit, match=r"listed-and-gone\.md, which names no file"):
        llms._absolutize_links("[g](listed-and-gone.md)", PAGE)


@pytest.mark.parametrize(
    "text",
    [
        "```python\nfs[0](x)\n```",
        "The first band, `levels[0](t)`, is the lowest.",
        "Its transform $h[n](z)$ is causal.",
        "[site](https://docs.jmrp.io/phonometry/), [here](#leq), [root](/phonometry/)",
    ],
)
def test_code_maths_and_absolute_addresses_are_left_as_written(text: str) -> None:
    """Not red on the old rewrite, which matched ``.md`` targets only: they guard the wider match."""
    assert llms._absolutize_links(text, PAGE) == text


#: A link's destination as CommonMark reads it, in an inline link or image (with
#: or without angle brackets and a title), a reference definition, or the
#: ``href`` or ``src`` of a tag.
_DESTINATIONS = (
    re.compile(r"\]\(\s*(?:<([^>\n]*)>|([^)\s]+))"),
    re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*(?:<([^>\n]*)>|(\S+))", re.MULTILINE),
    re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')"""),
)
_ABSOLUTE = re.compile(r"[A-Za-z][\w+.-]*:|#|/")


def _relative_links(path: Path) -> list[str]:
    """Each relative destination outside code and maths in an export, with its line."""
    lines = path.read_text(encoding="utf-8").split("\n")
    prose = blank_inline_spans_by_block(
        "\n".join(
            "" if walked.role in NOT_INLINE_ROLES else line
            for line, walked in zip(lines, page_lines(lines, kind="md"), strict=True)
        ),
        "`$",
        kind="md",
    )
    found = []
    for pattern in _DESTINATIONS:
        for match in pattern.finditer(prose):
            target = next(group for group in match.groups() if group is not None)
            if target and not _ABSOLUTE.match(target):
                found.append(
                    f"{path.relative_to(ROOT)}:{prose.count(chr(10), 0, match.start()) + 1}: {target}"
                )
    return found


def test_no_export_carries_a_relative_link() -> None:
    exports = [
        ROOT / "llms.txt",
        ROOT / "llms-full.txt",
        *sorted((ROOT / "site" / "public" / "llms").glob("*.txt")),
    ]
    found = [link for path in exports for link in _relative_links(path)]
    assert found == [], (
        "relative links in the exports (run `make llms`):\n" + "\n".join(found)
    )
