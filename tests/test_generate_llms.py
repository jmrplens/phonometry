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
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms
import generate_site_reports as site_reports
import yaml

if TYPE_CHECKING:
    from guard_caches import FreshCaches


def _shard_of_links(line: str) -> str:
    """The shard whose full text a heading's links fetch.

    One link names the shard's own file; a shard cut into parts links each
    part, ``llms-<shard>-1.txt`` onwards, and every one must be there in order.
    """
    names = re.findall(r"/llms/llms-([a-z0-9-]+)\.txt", line)
    if len(names) == 1:
        return names[0]
    shard = names[0].rsplit("-", 1)[0]
    assert tuple(names) == llms._part_names(shard, len(names)), (
        f"a heading links parts of more than one shard, or not all of them: {names}"
    )
    return shard


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
        elif current and (m := re.search(r"\]\(\S+?/phonometry/(\S+?)/\)", line)):
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


def test_the_contributor_guide_stays_out_of_llms() -> None:
    """docs/contributing/ is repository-only: it has no site page and no llms entry.

    Without the exclusion ``_routes()`` raises, because a mirror page with no
    page on the site is exactly what it exists to catch.
    """
    routes = [route for _, route in llms._routes()]
    assert not any(route.startswith("contributing") for route in routes)


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
def test_every_page_line_says_what_the_page_is_about() -> None:
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
    assert {route for _, route in llms._routes()} <= described


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


_NODE = shutil.which("node")


@pytest.mark.whole_tree
@pytest.mark.skipif(_NODE is None, reason="no JavaScript engine to ask the site")
def test_the_pages_without_a_copy_are_the_ones_the_site_withholds() -> None:
    """The sentence of the index names the pages the site's own rule withholds."""
    module = ROOT / "site" / "src" / "lib" / "page-markdown.mjs"
    script = (
        f"import {{ withheldRoutes }} from {json.dumps(module.as_uri())};"
        f"const routes = withheldRoutes({{ contentDir: {json.dumps(str(llms.CONTENT))}, "
        f"docsDir: {json.dumps(str(llms.DOCS))} }});"
        "process.stdout.write(JSON.stringify([...routes].sort()));"
    )
    ran = subprocess.run(
        [str(_NODE), "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        check=False,
    )
    assert ran.returncode == 0, ran.stderr
    site = json.loads(ran.stdout)
    assert sorted(llms._withheld_routes()) == site
    assert len(site) > 2


def test_the_copies_sentence_names_the_withheld_pages_by_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    withheld = {
        "",
        "es",
        "reference/catalogues/solids",
        "es/reference/catalogues/solids",
        "reference/catalogues/gases",
        "es/reference/catalogues/gases",
        "reference/reports",
        "es/reference/reports",
        "es/reference/glossary",
    }
    monkeypatch.setattr(llms, "_withheld_routes", lambda: frozenset(withheld))
    english = {"", "start/getting-started", "reference/reports", "reference/glossary"}
    monkeypatch.setattr(llms, "_content_routes", lambda: english)
    monkeypatch.setattr(llms, "_spanish_routes", lambda: set(english))
    sentence = llms._copies_sentence()
    assert sentence.startswith(
        "Every page listed here but the ones named at the end of this section has "
        f"a Markdown copy beside it at `<page>/index.md`, for example {_SITE}/start/"
        "getting-started/index.md, and its Spanish twin under `/es/` has one too "
        "where the page is translated. The 9 pages"
    )
    assert sentence.endswith(
        "The 9 pages that show their data through a component publish none and are read on the "
        'page itself: the two landing pages, the 2 catalogues and the "Report fiches" page in '
        'both languages and the Spanish "Glossary" page.'
    )
    assert "English only" not in sentence


def test_the_copies_sentence_names_the_pages_the_site_does_not_translate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A page with no Spanish page has no Spanish copy, and the sentence says so.

    It said every page listed had its Spanish twin's copy too, and the 269
    pages of the API reference have none: their Spanish addresses show the
    English page and point to its copy.
    """
    monkeypatch.setattr(llms, "_withheld_routes", lambda: frozenset({"", "es"}))
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
