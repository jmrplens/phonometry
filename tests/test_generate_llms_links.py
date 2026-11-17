#  Copyright (c) 2026. Jose Manuel Requena Plens
"""No llms file carries a link that resolves only beside the page it came from.

``llms-full.txt`` and the shards are flat text served from the site, so a link
written relative to the page that holds it resolves against the export's own
address and leads nowhere: the compute guide's links to
``engine-digests.json`` and ``gpu-parity.lock`` once went out as
``../../engine-digests.json``, which resolves to
docs.jmrp.io/engine-digests.json, a 404. The files were cut from the mirror
under ``docs/`` then, and the generator rewrote the mirror's relative links.

They are written from the site's own Markdown copies now, which link as the
site's pages do: to a page of the site by its root-relative route, which the
copy writer makes absolute (``site/src/lib/agent-md/links.mjs``, held by
``render.test.mjs``), and to anything else by its whole address. A link a
page wrote relative to itself would reach every file the page is carried in
as written, so this holds the committed ``llms.txt``, and every file the
generator writes for the build from a dump of the whole site, to none. The
dump these tests write holds each page's source, not what its components
write; a link a writer transplants into a copy (the conformance report's to
its data) is refused in the copy itself, by the build's check of every copy
(``site/scripts/check-markdown-twins.mjs``), and an llms file carries each
copy as it reads.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest
from llms_dump import CONTENT_ROOT, site_dump

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms
from markdown_fences import NOT_INLINE_ROLES, page_lines
from markdown_spans import blank_inline_spans_by_block

#: The page and the link the 404 above came from.
COMPUTE = "simulation/compute"
DIGESTS = "../../engine-digests.json"


#: A link's destination as CommonMark reads it, in an inline link or image (with
#: or without angle brackets and a title), a reference definition (a footnote's
#: ``[^1]:`` is none), or the ``href`` or ``src`` of a tag.
_DESTINATIONS = (
    re.compile(r"\]\(\s*(?:<([^>\n]*)>|([^)\s]+))"),
    re.compile(r"^ {0,3}\[(?!\^)[^\]\n]+\]:\s*(?:<([^>\n]*)>|(\S+))", re.MULTILINE),
    re.compile(r"""\b(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')"""),
)
_ABSOLUTE = re.compile(r"[A-Za-z][\w+.-]*:|#|/")


def _relative_links(path: Path, base: Path = ROOT) -> list[str]:
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
                    f"{path.relative_to(base)}:{prose.count(chr(10), 0, match.start()) + 1}: {target}"
                )
    return found


def _built(dump: Path, public: Path, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Every file ``generate_llms.py --build`` writes from *dump* into *public*."""
    monkeypatch.setattr(llms, "PUBLIC", public)
    monkeypatch.setattr(llms, "SHARDS_DIR", public / "llms")
    monkeypatch.setattr(llms, "INDEX", public / "index-only.txt")
    # The names this dump's shards publish are its own, not the site's.
    names = public.parent / "llms-shards.json"
    names.write_text('{"published": [], "redirects": {}}', encoding="utf-8")
    monkeypatch.setattr(llms, "SHARD_NAMES", names)
    # main() sets the dump it reads for the module; put it back afterwards.
    monkeypatch.setattr(llms, "PAGES", llms.PAGES)
    llms.main(["--pages", str(dump), "--build"])
    return sorted(public.rglob("*.txt"))


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A dump of the whole English site, every copy its page's source."""
    root = tmp_path_factory.mktemp("site-dump")
    site_dump(root, CONTENT_ROOT)
    return root


def test_the_committed_index_carries_no_relative_link() -> None:
    found = _relative_links(ROOT / "llms.txt")
    assert found == [], "relative links in llms.txt (run `make llms`):\n" + "\n".join(
        found
    )


@pytest.mark.whole_tree
def test_no_export_carries_a_relative_link(
    site: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """llms.txt, llms-full.txt and every shard the build writes, from the whole site."""
    public = tmp_path / "public"
    exports = _built(site, public, monkeypatch)
    assert {path.name for path in exports} >= {"llms.txt", "llms-full.txt"}
    found = [link for path in exports for link in _relative_links(path, public)]
    assert found == [], "relative links in the exports:\n" + "\n".join(found)


@pytest.mark.whole_tree
def test_a_link_a_page_writes_relative_to_itself_is_found_in_every_export(
    site: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The compute guide linking the digests as it once did fails the check, in each file that carries it."""
    planted = tmp_path / "dump"
    shutil.copytree(site, planted)
    copy = planted / COMPUTE / "index.md"
    copy.write_text(
        copy.read_text(encoding="utf-8") + f"\nSee [the digests]({DIGESTS}).\n",
        encoding="utf-8",
    )
    public = tmp_path / "public"
    found = [
        link
        for path in _built(planted, public, monkeypatch)
        for link in _relative_links(path, public)
    ]
    assert len(found) == 2, found
    assert all(link.endswith(f": {DIGESTS}") for link in found), found
    assert {link.split(":", 1)[0] for link in found} >= {"llms-full.txt"}
