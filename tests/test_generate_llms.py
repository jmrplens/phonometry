#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The index of ``llms.txt`` must not file a guide under the wrong shard.

``llms.txt`` groups its guides under a ``##`` heading per area and, where an
area is split, a ``###`` heading per carved-out shard. Each heading names the
full-text shard the run under it belongs to, so a client that wants one part
fetches one file. That promise is only kept if the run under a heading is
exactly the shard's own membership.

It was not. The index used to emit a heading the first time it met a route
from a different shard and never switch back, so any guide of the parent shard
that came after the carve-out in the folder's reading order was listed under
the carved-out heading. In ``devices/emission`` that put the surface-velocity
route, which measures no sound at all, under a heading about sound intensity,
and pointed a reader at a shard that does not contain it. Nothing caught it:
the artefact regenerates deterministically, so the freshness job compared a
wrong file against itself and passed.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from llms_dump import CONTENT_ROOT, FULL_TEXT_KINDS, Dump, page_kind, site_dump
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms
import generate_site_reports as site_reports
import site_target
import yaml

if TYPE_CHECKING:
    from guard_caches import FreshCaches

#: The kind of each route, as site/src/lib/page-markdown.mjs ``pageKind`` gives
#: it; site/src/lib/agent-md/test/dump.test.mjs holds ``pageKind`` to the same
#: table.
PAGE_KINDS = ROOT / "site" / "src" / "lib" / "agent-md" / "test" / "page-kinds.json"


def _shard_of_links(line: str) -> str:
    """The shard whose full text a heading's links fetch.

    One link names the shard's own file; a shard cut into parts links each
    part, ``llms-<shard>-1.txt`` onwards, and every one must be there in order.
    """
    names: list[str] = re.findall(r"/llms/llms-([a-z0-9-]+)\.txt", line)
    if len(names) == 1:
        return names[0]
    shard = names[0].rsplit("-", 1)[0]
    assert tuple(names) == llms._part_names(shard, len(names)), (
        f"a heading links parts of more than one shard, or not all of them: {names}"
    )
    return shard


#: A link to a page of the site the run links, its route captured: the site
#: and its base path come from the target, as the llms files are written.
_PAGE_LINK = re.compile(rf"\]\({re.escape(llms.SITE_URL)}/(\S+?)/\)")


def _runs_of(text: str) -> dict[str, list[str]]:
    """The routes listed under each ``###`` heading, keyed by its shard slug.

    The shard is read from the ``full text`` link the heading carries rather
    than from the heading's words, because the link is what a client follows.
    """
    runs: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = None
        elif line.startswith("### "):
            current = ""
        elif current == "" and "/llms/llms-" in line:
            current = _shard_of_links(line)
            runs.setdefault(current, [])
        elif current and (m := _PAGE_LINK.search(line)):
            runs[current].append(m.group(1))
    return runs


def test_every_carved_out_heading_lists_only_its_own_shard() -> None:
    members = llms._shard_members()
    runs = _runs_of((ROOT / "llms.txt").read_text(encoding="utf-8"))
    assert runs, "the index carries no carved-out shard headings to check"
    for slug, listed in runs.items():
        expected = members.get(slug)
        assert expected is not None, (
            f"the index names a shard that does not exist: {slug}"
        )
        assert listed == expected, (
            f"the guides listed under the {slug} heading are not that shard's "
            f"own: listed {listed}, shard holds {expected}"
        )


@pytest.mark.parametrize("slug", ["devices-emission-intensity"])
def test_the_intensity_shard_holds_only_the_intensity_routes(slug: str) -> None:
    """The split of ``devices/emission`` is by the quantity measured.

    Named rather than left to the general check above, because this is the
    one the defect was found in: the surface-velocity route belongs with the
    pressure routes of the parent shard, not with the two that read intensity.
    """
    members = llms._shard_members()
    assert members[slug] == [
        "devices/emission/sound-power-intensity",
        "devices/emission/intensity",
    ]
    assert "devices/emission/vibration-sound-power" in members["devices-emission"]


# The index lists every English page of the site and says what each is about.
#
# It used to name the pages docs/ mirrors and a hand-kept few, each by its
# title alone: the 96 errata families, the catalogues, the task index and the
# start and reference section pages were in the sitemap and nowhere in
# llms.txt, and a reader of the index chose among 300 pages by title.

_SITE = llms.SITE_URL


def _page(title: str, description: str, body: str = "") -> str:
    return f'---\ntitle: "{title}"\ndescription: "{description}"\n---\n\n{body}\n'


def test_the_content_routes_are_named_as_the_site_names_them(
    tmp_path: Path, fresh_caches: FreshCaches
) -> None:
    for name in (
        "index.mdx",
        "start/index.md",
        "a/index.mdx",
        "a/b.mdx",
        "es/a/b.mdx",
        "es/index.mdx",
    ):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(_page("T", "D"), encoding="utf-8")
    fresh_caches(llms, CONTENT=tmp_path)
    assert llms._content_routes() == {"", "start", "a", "a/b"}


def test_a_page_the_index_does_not_link_stops_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llms, "_content_routes", lambda: {"", "a", "b/c"})
    with pytest.raises(
        SystemExit, match=r"links no line to 1 English page\(s\) of the site: b/c\."
    ):
        llms._check_index_covers_the_site(
            f"- [A]({_SITE}/a/): about a\n- [C](https://example.org/b/c/)\n"
        )
    llms._check_index_covers_the_site(
        f"- [A]({_SITE}/a/): about a\n- [C]({_SITE}/b/c/) (3 rows): c\n"
    )


@pytest.mark.whole_tree
def test_the_committed_index_links_every_english_page_of_the_site() -> None:
    llms._check_index_covers_the_site((ROOT / "llms.txt").read_text(encoding="utf-8"))


def test_the_index_links_the_quick_api_table_that_llms_full_leaves_out() -> None:
    """llms-full.txt carries the site's pages; the curated table is a file of docs/."""
    index = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert f"]({llms.REPO_URL}/blob/main/{llms.QUICK_API_TABLE}): " in index
    assert (ROOT / llms.QUICK_API_TABLE).is_file()


#: The sections of the index whose lines are not a page and what it is about:
#: hand-written lines with words of their own, counts, shards and the API.
_UNDESCRIBED = {
    "Evidence and provenance",
    "Source and metadata",
    "Errata by source",
    "Full text",
    "Spanish",
    "Markdown copies",
    "Optional",
}


@pytest.mark.whole_tree
def test_every_page_line_says_what_the_page_is_about(
    site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llms, "PAGES", site)
    section = ""
    described: set[str] = set()
    for line in (ROOT / "llms.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:]
            continue
        found = re.match(
            rf"- \[[^\]]*\]\({re.escape(_SITE)}/([^)]*?)/?\)( \(\d+ rows?\))?: ", line
        )
        if section in _UNDESCRIBED or not line.startswith("- ["):
            continue
        assert found, f"{section}: a line that says nothing of its page: {line}"
        route = found.group(1)
        assert line[found.end() :].startswith(llms._description(route)), (section, line)
        described.add(route)
    # The errata families are listed with their entry counts under their own
    # heading (see the test of the errata lines); every guide says what it is.
    assert {r for r in llms._routes() if llms._page(r).kind == "guide"} <= described


#: The one section whose lines link pages and say nothing of them: the API
#: reference, one line per module, which its own index describes.
_BARE_BY_DESIGN = {"Optional"}


def test_no_line_outside_the_api_links_a_page_and_says_nothing_of_it() -> None:
    # The sections the test above leaves out write words of their own, so it
    # cannot hold their lines to a page's description; it still holds each
    # line that links a page of the site to say what is there. The
    # bibliography and the About page were linked bare under "Evidence and
    # provenance" while every other page of the index said what it held.
    section = ""
    bare = []
    for line in (ROOT / "llms.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:]
            continue
        found = re.match(
            rf"- \[[^\]]*\]\({re.escape(_SITE)}/[^)]*/\)(?: \([^)]*\))?(?P<rest>.*)$",
            line,
        )
        if found and section not in _BARE_BY_DESIGN:
            rest = found.group("rest")
            if not rest.startswith(": ") or not rest[2:].strip():
                bare.append(f"{section}: {line}")
    assert not bare, bare


def test_an_errata_line_counts_the_entries_the_register_files_under_its_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fresh_caches: FreshCaches
) -> None:
    """Entries are counted where the register files them, not by a page's headings.

    The page of properties that are not errata holds nineteen of them under a
    single heading, and the index said "1 entry" for it under "Errata by
    source"; it is no family and has no entries, so it is listed on its own
    with what it is about.
    """
    pages = site_reports.plan_families(
        [
            "ISO 1, Table 2",
            "ISO 1, Annex B",
            "ISO 2, clause 3",
            site_reports.NOT_ERRATA_HEADING,
        ]
    )
    monkeypatch.setattr(llms, "_errata_families", lambda: pages)
    errata = tmp_path / "reference" / "errata"
    errata.mkdir(parents=True)
    one_heading = "## ISO 1, Table 2\n\nText.\n"
    (errata / "iso-1.md").write_text(
        _page("Errata in ISO 1", "Two", one_heading), encoding="utf-8"
    )
    two_headings = "## ISO 2, clause 3\n\n## A heading of the page's own\n"
    (errata / "iso-2.md").write_text(
        _page("Errata in ISO 2", "One", two_headings), encoding="utf-8"
    )
    items = "## Related\n\n- **A:** one.\n- **B:** two.\n- **C:** three.\n"
    (errata / "not-errata.md").write_text(
        _page("Not errata", "Properties that look like misprints.", items),
        encoding="utf-8",
    )
    fresh_caches(llms, CONTENT=tmp_path)
    lines = llms._errata_section()
    url = f"{_SITE}/reference/errata"
    assert f"- [Errata in ISO 1]({url}/iso-1/): 2 entries" in lines
    assert f"- [Errata in ISO 2]({url}/iso-2/): 1 entry" in lines
    apart = lines.index("## Properties that are not errata")
    assert lines[apart + 2] == (
        f"- [Not errata]({url}/not-errata/): Properties that look like misprints."
    )
    assert not any("not-errata" in line for line in lines[:apart])
    assert not any(f"{url}/index/" in line or f"{url}/)" in line for line in lines[4:])


def test_a_catalogue_line_counts_the_rows_it_tables(
    tmp_path: Path, fresh_caches: FreshCaches
) -> None:
    data = tmp_path / "catalogues.mjs"
    rows: dict[str, dict[str, list[dict[str, str]]]] = {
        "a": {"columns": [], "rows": [{}] * 3},
        "b": {"columns": [], "rows": [{}] * 2},
    }
    data.write_text(
        "// Auto-generated.\nexport const catalogues = "
        + json.dumps(rows, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    pages = tmp_path / "content" / "reference" / "catalogues"
    pages.mkdir(parents=True)
    (pages / "index.mdx").write_text(
        _page("Published catalogues", "Every gas the library reads from a page."),
        encoding="utf-8",
    )
    body = '<Catalogues catalogue="a" lang="en" />\n\nAlso `<Catalogues catalogue="b" />` in code.\n\n<Catalogues catalogue="b" lang="en" />'
    (pages / "both.mdx").write_text(
        _page("Catalogue of both", "Two tables.", body), encoding="utf-8"
    )
    fresh_caches(llms, CONTENT=tmp_path / "content", CATALOGUE_DATA=data, ROOT=tmp_path)
    lines = llms._catalogue_section()
    # The scope is the index page's own, never a wider claim of the index.
    assert lines[2].startswith("Every gas the library reads from a page. ")
    assert (
        f"- [Catalogue of both]({_SITE}/reference/catalogues/both/) (5 rows): Two tables."
        in lines
    )
    (pages / "both.mdx").write_text(
        _page("X", "Y", '<Catalogues catalogue="c" />'), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match=r"tables \['c'\]"):
        llms._catalogue_section()


def test_the_index_is_held_to_its_budget() -> None:
    llms._check_index_budget("x" * llms.LLMS_TXT_LIMIT_BYTES)
    with pytest.raises(SystemExit, match=r"over the 200000-byte budget"):
        llms._check_index_budget("x" * (llms.LLMS_TXT_LIMIT_BYTES + 1))
    committed = (ROOT / "llms.txt").read_bytes()
    assert len(committed) <= llms.LLMS_TXT_LIMIT_BYTES


#: An address as a reader of plain text takes it: from the scheme to the
#: first character no address holds unescaped, or a single quote
#: (site/scripts/check-markdown-twins.mjs, ``ADDRESS``).
_ADDRESS = re.compile(r"https?://[^\s<>\"'`\[\]{}|\\^]+")


def _bare_addresses_read_with_punctuation(text: str) -> list[str]:
    """Every bare address of *text* that runs into the punctuation after it.

    The rule of site/scripts/check-markdown-twins.mjs (``bareAddressProblems``),
    which holds the built llms files to it: a link's destination and an
    autolink end where Markdown ends them, and any other address that ends on
    a full stop, a comma, a semicolon, a colon, ``!``, ``?``, ``*``, ``_``,
    ``~`` or a closing parenthesis it did not open is fetched with it.
    """
    found = []
    for line in text.splitlines():
        for match in _ADDRESS.finditer(line):
            before = line[max(0, match.start() - 2) : match.start()]
            address = match.group()
            if before.endswith("<") or before == "](":
                continue
            if address[-1] in ".,;:!?*_~" or (
                address.endswith(")") and address.count(")") > address.count("(")
            ):
                found.append(address)
    return found


def test_the_index_ends_no_sentence_on_a_bare_address() -> None:
    """A crawler that reads an address up to the next space fetches its full stop too.

    Two did, on the day the site moved to its own host: 24 requests for agent
    files with the full stop of the sentence that named them on the end, every
    one a 404. The index names each address as a link.
    """
    assert (
        _bare_addresses_read_with_punctuation(
            (ROOT / "llms.txt").read_text(encoding="utf-8")
        )
        == []
    )


def test_a_shard_head_and_a_part_head_link_every_address_they_name() -> None:
    head = llms._part_head(
        slug="signals",
        title="Signal analysis",
        number=2,
        count=3,
        single_page=False,
        cuts=["page", "section"],
    )
    assert _bare_addresses_read_with_punctuation(head) == []
    assert f"Part of [llms.txt]({llms.SITE_URL}/llms.txt). " in head
    assert (
        f"[part 1]({llms.SITE_URL}/llms/llms-signals-1.txt), "
        f"[part 2]({llms.SITE_URL}/llms/llms-signals-2.txt) and "
        f"[part 3]({llms.SITE_URL}/llms/llms-signals-3.txt)."
    ) in head
    shards = {"theory": ("theory-1", "theory-2"), "glossary": ("glossary",)}
    assert llms._shard_links(shards, "theory", "theory") == (
        f"[theory, part 1 of 2]({llms.SITE_URL}/llms/llms-theory-1.txt) and "
        f"[theory, part 2 of 2]({llms.SITE_URL}/llms/llms-theory-2.txt)"
    )
    assert llms._shard_links(shards, "glossary", "glossary") == (
        f"[glossary]({llms.SITE_URL}/llms/llms-glossary.txt)"
    )


def test_the_rule_finds_what_a_crawler_misreads_and_passes_what_markdown_ends() -> None:
    misread = (
        "Part of https://x.dev/llms.txt. Then https://x.dev/a, https://x.dev/b; "
        "https://x.dev/c: and (index: https://x.dev/d/)."
    )
    assert _bare_addresses_read_with_punctuation(misread) == [
        "https://x.dev/llms.txt.",
        "https://x.dev/a,",
        "https://x.dev/b;",
        "https://x.dev/c:",
        "https://x.dev/d/).",
    ]
    ended = (
        "Part of [llms.txt](https://x.dev/llms.txt). An autolink <https://x.dev/a>. "
        "On https://en.wikipedia.org/wiki/Decibel_(unit) and at the end https://x.dev/b"
    )
    assert _bare_addresses_read_with_punctuation(ended) == []


_NODE = shutil.which("node")


def test_the_copies_sentence_names_the_pages_the_site_does_not_translate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A page with no Spanish page has no Spanish copy, and the sentence says so.

    It said every page listed had its Spanish twin's copy too, and the 269
    pages of the API reference have none: their Spanish addresses show the
    English page and point to its copy.
    """
    english = {
        "",
        "start/guides",
        "reference/api",
        "reference/api/a",
        "reference/api/b",
    }
    monkeypatch.setattr(llms, "_content_routes", lambda: english)
    monkeypatch.setattr(llms, "_spanish_routes", lambda: {""})
    guides = llms._frontmatter_field(llms._source_of("start/guides"), "title")
    assert (
        f'The 3 pages of the API reference and the "{guides}" page are in English '
        "only: at the Spanish address the site shows the English page, which "
        "points to its English copy."
    ) in llms._copies_sentence()
    monkeypatch.setattr(llms, "_content_routes", lambda: {"", "reference/api"})
    assert "The 1 page of the API reference is in English only:" in (
        llms._copies_sentence()
    )


def test_the_copies_sentence_says_every_page_has_a_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every page publishes a copy written from its own source, so none is named as having none."""
    monkeypatch.setattr(llms, "_content_routes", lambda: {"", "start/guides"})
    monkeypatch.setattr(llms, "_spanish_routes", lambda: {"", "start/guides"})
    sentence = llms._copies_sentence()
    assert sentence.startswith("Every page listed here has a Markdown copy beside it")
    assert "publish none" not in sentence


def test_the_spanish_routes_are_named_without_their_prefix(
    tmp_path: Path, fresh_caches: FreshCaches
) -> None:
    for name in ("index.mdx", "a/b.mdx", "es/index.mdx", "es/a/index.md", "es/a/b.mdx"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(_page("T", "D"), encoding="utf-8")
    fresh_caches(llms, CONTENT=tmp_path)
    assert llms._spanish_routes() == {"", "a", "a/b"}


# A page's title and description are read as the site's YAML parser reads
# them. The reader took a backslash and the character after it for that
# character, so `\u00e7` came out as `u00e7`: the API page of the facade
# models was described as a "Fau00e7ade sound insulation" model.


def test_a_frontmatter_scalar_is_read_with_the_escapes_and_quotes_of_yaml(
    tmp_path: Path,
) -> None:
    page = tmp_path / "page.md"
    cases = {
        r'"Fa\u00e7ade \"sound\" \\ \x41\U0001F600"': 'Façade "sound" \\ A\U0001f600',
        "'It''s a page'": "It's a page",
        "A bare one # with a comment": "A bare one",
        "C# is a language": "C# is a language",
    }
    for written, read in cases.items():
        page.write_text(f"---\ntitle: {written}\n---\n\nBody.\n", encoding="utf-8")
        assert llms._frontmatter_field(page, "title") == read, written
        assert yaml.safe_load(f"title: {written}")["title"] == read, written
    for written in (r'"A \q escape"', ">-", "|", "[a, b]", '"runs on'):
        page.write_text(f"---\ntitle: {written}\n---\n\nBody.\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            llms._frontmatter_field(page, "title")


@pytest.mark.whole_tree
def test_every_title_and_description_reads_as_the_sites_yaml_parser_reads_it() -> None:
    read = 0
    for path in sorted(llms.CONTENT.rglob("*.md*")):
        text = path.read_text(encoding="utf-8")
        head = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        if head is None:
            continue
        data = yaml.safe_load(head.group(1)) or {}
        for name in ("title", "description"):
            if name in data:
                assert llms._frontmatter_field(path, name) == data[name], (path, name)
                read += 1
    assert read > 1000


def test_a_file_outside_the_repository_is_named_whole_in_a_refusal(
    tmp_path: Path, fresh_caches: FreshCaches
) -> None:
    """The catalogue data and pages a test points at a tree of its own are named
    in full when the run stops, where naming them relative to the repository
    raised a ``ValueError`` in place of the refusal.
    """
    data = tmp_path / "catalogues.mjs"
    data.write_text("export const catalogues = [];\n", encoding="utf-8")
    pages = tmp_path / "content" / "reference" / "catalogues"
    pages.mkdir(parents=True)
    (pages / "index.mdx").write_text(_page("Catalogues", "All."), encoding="utf-8")
    (pages / "none.mdx").write_text(_page("None", "No table."), encoding="utf-8")
    fresh_caches(llms, CONTENT=tmp_path / "content", CATALOGUE_DATA=data)
    with pytest.raises(SystemExit, match=re.escape(f"{data} is not the")):
        llms._catalogue_rows()
    data.write_text(
        'export const catalogues = {"a": {"rows": []}};\n', encoding="utf-8"
    )
    with pytest.raises(
        SystemExit,
        match=re.escape(f"{pages / 'none.mdx'} tables no catalogue of {data}"),
    ):
        llms._catalogue_section()


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A dump of the whole English site, every copy its page's source."""
    root = tmp_path_factory.mktemp("site-dump")
    site_dump(root, CONTENT_ROOT)
    return root


@pytest.mark.whole_tree
def test_every_page_the_llms_files_carry_is_in_exactly_one_shard(
    site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guides, the catalogues and the errata families, each in one shard.

    The API reference and the landing page are in none: llms.txt lists the
    first as optional reading and does the second's work itself.
    """
    monkeypatch.setattr(llms, "PAGES", site)
    plan = llms._shard_plan()
    held = [route for _slug, _label, routes in plan for route in routes]
    pages = llms._dump()

    assert sorted(held) == llms._routes()
    assert len(held) == len(set(held))
    assert {pages[route].kind for route in held} == {
        "guide",
        "catalogue",
        "errata-family",
    }
    slugs = [slug for slug, _label, _routes in plan]
    assert slugs.index("conformance") < slugs.index("errata")
    assert all(
        slug == f"catalogues-{routes[0].rsplit('/', 1)[1]}"
        for slug, _label, routes in plan
        if pages[routes[0]].kind == "catalogue"
    )
    errata = next(routes for slug, _label, routes in plan if slug == "errata")
    assert errata[0] == llms.ERRATA_ROUTE
    assert {pages[route].kind for route in errata[1:]} == {"errata-family"}


@pytest.mark.whole_tree
def test_a_page_left_out_of_every_shard_or_put_in_two_is_refused(
    site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llms, "PAGES", site)
    plan = llms._shard_plan()
    slug, label, routes = plan[0]
    dropped = [(slug, label, routes[1:]), *plan[1:]]
    with pytest.raises(
        SystemExit, match=rf"page\(s\) in no shard: {re.escape(routes[0])}"
    ):
        llms._check_every_page_in_one_shard(dropped)
    twice = [*plan, ("extra", "Extra", [routes[0]])]
    with pytest.raises(SystemExit, match=r"page\(s\) in two shards: .*llms-extra"):
        llms._check_every_page_in_one_shard(twice)


@pytest.mark.whole_tree
def test_llms_full_carries_every_page_whole_after_the_index(
    site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llms, "PAGES", site)
    plan = llms._shard_plan()
    index = "# phonometry\n\nThe index.\n"

    full = llms.build_llms_full(index, plan)

    assert full.startswith(index + "\n---\n")
    for _slug, _label, routes in plan:
        for route in routes:
            assert full.count(f"\n{llms._copy(route).text}{llms.PAGE_END}") == 1, route
    assert "/reference/api/" not in "".join(
        line for line in full.splitlines() if line.startswith("Canonical: ")
    )


@pytest.mark.whole_tree
def test_a_dump_older_than_the_site_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: Path
) -> None:
    """A dump left from an earlier checkout names pages that moved and misses new ones."""
    stale = tmp_path / "stale"
    shutil.copytree(site, stale)
    listing = json.loads((stale / "routes.json").read_text(encoding="utf-8"))
    gone = listing["pages"].pop(1)["route"]
    listing["pages"].append(dict(listing["pages"][1], route="signals/moved-away"))
    (stale / "routes.json").write_text(json.dumps(listing), encoding="utf-8")
    monkeypatch.setattr(llms, "PAGES", stale)

    with pytest.raises(
        SystemExit,
        match=rf"does not hold: {re.escape(gone)}.*no longer has: signals/moved-away",
    ):
        llms._check_dump_matches_the_tree()


def test_a_missing_dump_or_a_text_that_is_no_copy_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llms, "PAGES", tmp_path / "nowhere")
    with pytest.raises(
        SystemExit, match=r"cannot read the pages at .*routes\.json.*make llms"
    ):
        llms._dump()
    with pytest.raises(
        SystemExit, match=r"the dump's copy of x does not open as a Markdown copy"
    ):
        llms._split_copy("x", "Just some text.\n")
    dump = Dump(tmp_path / "dump")
    dump.add("x", "The body.")
    monkeypatch.setattr(llms, "PAGES", dump.root)
    copy = llms._copy("x")
    assert copy.text + "\n" == (dump.root / "x" / "index.md").read_text(
        encoding="utf-8"
    )
    assert copy.rest == "The body."


@pytest.mark.whole_tree
def test_the_build_writes_what_the_site_publishes_and_retires_stale_shards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: Path
) -> None:
    """``--build`` writes llms.txt, llms-full.txt and every shard into public/.

    A shard file the run no longer produces is removed, and so is one an older
    layout left at the site root; ``make llms`` writes the index alone, and
    the same index.
    """
    public = tmp_path / "public"
    (public / "llms").mkdir(parents=True)
    (public / "llms" / "llms-retired.txt").write_text("old", encoding="utf-8")
    (public / "llms-signals.txt").write_text("old", encoding="utf-8")
    monkeypatch.setattr(llms, "PUBLIC", public)
    monkeypatch.setattr(llms, "SHARDS_DIR", public / "llms")
    monkeypatch.setattr(llms, "INDEX", tmp_path / "llms.txt")
    # The names this dump's shards publish are its own, not the site's; the
    # run without --build writes them into the record, here a copy of its own.
    names = tmp_path / "llms-shards.json"
    names.write_text('{"published": [], "redirects": {}}', encoding="utf-8")
    monkeypatch.setattr(llms, "SHARD_NAMES", names)
    # main() sets the dump it reads for the module; put it back afterwards.
    monkeypatch.setattr(llms, "PAGES", llms.PAGES)

    llms.main(["--pages", str(site), "--build"])
    llms.main(["--pages", str(site)])

    written = {path.name for path in (public / "llms").iterdir()}
    linked = set(
        re.findall(
            r"/llms/(llms-[a-z0-9-]+\.txt)",
            (public / "llms.txt").read_text(encoding="utf-8"),
        )
    )
    assert written == linked
    assert "llms-retired.txt" not in written
    assert not (public / "llms-signals.txt").exists()
    assert (
        (public / "llms-full.txt")
        .read_text(encoding="utf-8")
        .startswith((public / "llms.txt").read_text(encoding="utf-8"))
    )
    assert (tmp_path / "llms.txt").read_text(encoding="utf-8") == (
        public / "llms.txt"
    ).read_text(encoding="utf-8")
    recorded = json.loads(names.read_text(encoding="utf-8"))
    assert {f"llms-{name}.txt" for name in recorded["published"]} == written


def test_the_test_dumps_give_every_route_the_kind_the_site_gives_it() -> None:
    """The fake dumps class each route as ``agent-md.mjs --dump`` would.

    ``tests/llms_dump.py`` ports ``pageKind`` to Python to write dumps with no
    Node, and a port drifts: a route the site came to class otherwise would
    still be carried, or left out, by every dump these tests read. The site's
    function and this port answer to one table.
    """
    data = json.loads(PAGE_KINDS.read_text(encoding="utf-8"))
    table: dict[str, str] = data["routes"]
    assert set(table.values()) == llms.KINDS
    assert set(data["fullTextKinds"]) == FULL_TEXT_KINDS
    wrong = {
        route: (page_kind(route), kind)
        for route, kind in table.items()
        if page_kind(route) != kind
    }
    assert not wrong, f"page_kind disagrees with the site (got, wanted): {wrong}"


_PRE_RELEASES = json.loads(
    (ROOT / "site" / "src" / "data" / "pep440-pre-releases.json").read_text(
        encoding="utf-8"
    )
)["cases"]


@pytest.mark.parametrize(("version", "pre"), sorted(_PRE_RELEASES.items()))
def test_a_version_is_a_pre_release_as_pep_440_and_packaging_say(
    *, version: str, pre: bool
) -> None:
    """The table the site is tested on, and packaging's reading of PEP 440."""
    assert llms._is_pre_release(version) is pre
    assert Version(version).is_prerelease is pre


def test_the_index_says_a_pre_release_is_not_on_pypi_yet_and_nothing_at_the_stamp() -> (
    None
):
    said = "phonometry 4.0.0rc1 is a pre-release, which pip installs only when it is asked for by version or with --pre."
    assert said in llms._summary("4.0.0rc1")
    final = "\n".join(llms._summary("4.0.0"))
    assert "not on PyPI" not in final
    assert "pre-release" not in final


def test_the_site_url_follows_phonometry_site_as_the_site_build_does() -> None:
    """The llms files name the host the site was built for, from the same closed table.

    ``PHONOMETRY_SITE`` picks the host in ``site/src/data/site-targets.json``,
    which the site build reads too, so the llms files link the pages where the
    build serves them: phonometry.dev at the root, unset or named; any other
    value, the host the site was published on before among them, stops the run.
    """
    assert llms.site_url(None) == "https://phonometry.dev"
    assert llms.site_url("") == "https://phonometry.dev"
    assert llms.site_url("phonometry.dev") == "https://phonometry.dev"
    with pytest.raises(
        SystemExit, match=r"PHONOMETRY_SITE=docs\.jmrp\.io is not one of"
    ):
        llms.site_url("docs.jmrp.io")
    with pytest.raises(
        SystemExit, match=r"PHONOMETRY_SITE=phonometry\.org is not one of"
    ):
        llms.site_url("phonometry.org")
    table = json.loads(site_target.TARGETS.read_text(encoding="utf-8"))
    for name, target in table["targets"].items():
        assert llms.site_url(name) == f"{target['siteUrl']}{target['basePath']}"


def test_the_guide_order_reads_the_links_the_pages_write() -> None:
    """The reading order of an area comes from the links its overview writes.

    A link in the source carries the base path the pages are written under,
    and one in a copy the site the run links; a route named in prose or in
    code is no link. When the pattern reads none of an overview's links (a
    base path it lags), the run stops instead of listing the guides in
    sorted order.
    """
    base, site = llms.SITE_BASE, llms.SITE_URL
    text = (
        f"Read [B]({base}/signals/b/) first, then [A]({site}/signals/a/#x); "
        f"the path `{base}/signals/c/` and {base}/signals/d/ are no links."
    )
    assert llms._linked(text, ["signals/a", "signals/b", "signals/c", "signals/d"]) == [
        "signals/b",
        "signals/a",
    ]
    assert llms._linked(f"[A]({base}/other/a/)", ["signals/a"]) == []


def test_an_overview_whose_links_name_no_guide_stops_the_run(tmp_path: Path) -> None:
    """An overview none of whose links names a page of its area fails loudly.

    Matching the pattern is not enough: at the root the base is empty, and
    every root-relative link matches, a stale one too. What the reading order
    needs is a link that names a guide or a subgroup, so that is what the run
    asks for, and a link to no such page stops it at any base.
    """
    overview = tmp_path / "index.md"
    candidates = {"signals/a", "signals/metrology"}
    overview.write_text(
        f"[A]({llms.SITE_BASE}/no-such-area/a/) and [B](/somewhere-else/signals/a/)\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match=r"index\.md links no guide of its area by"):
        llms._require_site_links(overview, candidates)
    overview.write_text(
        f"![Diagram]({llms.SITE_BASE}/signals/a/diagram.svg)\n", encoding="utf-8"
    )
    with pytest.raises(SystemExit, match=r"index\.md links no guide of its area by"):
        llms._require_site_links(overview, candidates)
    overview.write_text(f"[A]({llms.SITE_BASE}/signals/a/)\n", encoding="utf-8")
    llms._require_site_links(overview, candidates)
    overview.write_text(
        f'[A]({llms.SITE_BASE}/signals/a/#levels "Levels")\n', encoding="utf-8"
    )
    llms._require_site_links(overview, candidates)
    overview.write_text(f"[M]({llms.SITE_URL}/signals/metrology/)\n", encoding="utf-8")
    llms._require_site_links(overview, candidates)


@pytest.mark.parametrize("name", ["index.md", "index.mdx"])
def test_a_link_written_only_inside_code_links_nothing(
    tmp_path: Path, name: str
) -> None:
    """A link inside a code span or a fence is shown as code, and orders nothing.

    An overview whose only link to its area sits in code would otherwise pass
    the check and order the area by an example; with a real link beside it,
    the real one is read and the code one is not.
    """
    base = llms.SITE_BASE
    overview = tmp_path / name
    candidates = {"signals/a", "signals/b"}
    for text in (
        f"Write `[A]({base}/signals/a/)` to link it.\n",
        f"Write ``[A]({base}/signals/a/)`` to link it.\n",
        f"```markdown\n[A]({base}/signals/a/)\n```\n",
        f"~~~\n[A]({base}/signals/a/)\n~~~\n",
    ):
        overview.write_text(text, encoding="utf-8")
        with pytest.raises(SystemExit, match=r"links no guide of its area"):
            llms._require_site_links(overview, candidates)
    overview.write_text(
        f"`[B]({base}/signals/b/)` aside, read [A]({base}/signals/a/) first.\n",
        encoding="utf-8",
    )
    llms._require_site_links(overview, candidates)
    assert llms._linked(overview.read_text(encoding="utf-8"), candidates) == [
        "signals/a"
    ]
    lone = f"A lone ` here.\n\nRead [B]({base}/signals/b/), then ` closes nothing.\n"
    assert llms._linked(lone, candidates) == ["signals/b"]
    items = f"- A literal `\n- Read [A]({base}/signals/a/), then a literal `.\n"
    assert llms._linked(items, candidates) == ["signals/a"]
    comment = (
        "<!-- a lone ` here -->" if name.endswith(".md") else "{/* a lone ` here */}"
    )
    commented = f"{comment} Read [A]({base}/signals/a/), then a literal `.\n"
    assert llms._linked(commented, candidates, kind=llms.page_kind(name)) == [
        "signals/a"
    ]
    hidden = "<!-- [B](" if name.endswith(".md") else "{/* [B]("
    hidden += f"{base}/signals/b/) " + ("-->" if name.endswith(".md") else "*/}")
    assert llms._linked(hidden + "\n", candidates, kind=llms.page_kind(name)) == []
    wrapped = f"Write `[A]({base}/signals/a/)\nacross` two lines, then [B]({base}/signals/b/).\n"
    assert llms._linked(wrapped, candidates) == ["signals/b"]


def test_an_overview_linking_only_another_areas_guide_stops_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A link to a guide of another area is no link of the overview's own area.

    An overview cross-references guides elsewhere, and those links say nothing
    about its own reading order: one whose only link names a guide of another
    area would let its area fall back to sorted order without a word, so the
    run stops on it as it does on an overview that links nothing.
    """
    base = llms.SITE_BASE
    pages = {
        "signals/index.md": f"See [rooms]({base}/buildings/rooms/room-acoustics/).\n",
        "signals/a.md": "",
        "buildings/index.md": f"Start with [rooms]({base}/buildings/rooms/).\n",
        "buildings/rooms/index.md": "",
        "buildings/rooms/room-acoustics.md": "",
    }
    for name, text in pages.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    monkeypatch.setattr(llms, "CONTENT", tmp_path)
    monkeypatch.setattr(
        llms, "AREAS", (("signals", "Signals"), ("buildings", "Buildings"))
    )
    with pytest.raises(
        SystemExit, match=r"signals[\\/]index\.md links no guide of its area"
    ):
        llms._area_members()
    (tmp_path / "signals/index.md").write_text(
        f"Read [A]({base}/signals/a/), then [rooms]({base}/buildings/rooms/room-acoustics/).\n",
        encoding="utf-8",
    )
    assert llms._area_members() == {
        "signals": ["signals/a"],
        "buildings": ["buildings/rooms/room-acoustics"],
    }


def test_at_the_root_a_link_under_the_old_base_stops_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the pages served at the root, a link left under the old base fails loudly.

    The pattern built from an empty base reads ``](/phonometry/signals/a/)`` as
    the route ``phonometry/signals/a``, which names no guide, so the run stops
    instead of listing the area in sorted order.
    """
    monkeypatch.setattr(
        llms, "_SITE_LINK", llms._site_link("https://phonometry.dev", "")
    )
    overview = tmp_path / "index.md"
    overview.write_text("[A](/phonometry/signals/a/)\n", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"links no guide of its area"):
        llms._require_site_links(overview, {"signals/a"})
    overview.write_text("[A](/signals/a/)\n", encoding="utf-8")
    llms._require_site_links(overview, {"signals/a"})
