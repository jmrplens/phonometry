#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A shard too long for one fetch travels in numbered parts.

The shards exist so that a client that truncates a response reads one whole
area instead of the first pages of everything. Written from the pages' own
Markdown copies, eight areas came out over the budget, the conformance report
alone is twice it, and the errata register four times; raising the budget is
what the budget exists to forbid. The generator cuts such a shard instead: an
area between its pages, a page that alone outgrows a part at its own H2
headings, and a section that still outgrows one between the rows of its
tables, into as few parts as fit. Every part opens each page it holds with the
page's own head, so a passage read from any part says where it comes from, and
the parts joined in order are the copy again; ``llms.txt`` lists every part,
and a row too long for a part is refused by name.

Where a shard is cut cannot depend on the dates the header carries: the build
writes the shards from a dump with them, and ``make llms`` writes the index
that names their files from one without.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from llms_dump import CONTENT_ROOT, Dump, site_dump

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms

if TYPE_CHECKING:
    from guard_caches import FreshCaches

#: A link to a shard file, capturing the name ``llms-`` precedes.
_PART_FILE = re.compile(r"/llms/llms-([a-z0-9-]+)\.txt")


def _bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def _pages_of(shard: str) -> list[str]:
    """The pages a shard file carries, each as the generator wrote it."""
    head, _, body = shard.partition("\n---\n")
    assert head.startswith("# phonometry: "), "the shard has no head"
    pages = []
    for chunk in re.split(r"\n(?=# [^\n]*\n\n> One page of the phonometry)", body):
        if chunk.strip():
            assert chunk.endswith(llms.PAGE_END), (
                f"a page is not closed: {chunk[-40:]!r}"
            )
            pages.append(chunk.removesuffix(llms.PAGE_END).removeprefix("\n"))
    return pages


def _joined(route: str, parts: tuple[str, ...]) -> list[str]:
    """The lines after the head of every part's page of *route*, in order.

    A part that opens between two rows repeats the header row and the
    delimiter row of the table it continues; those are taken out, as the
    check of the build takes them out.
    """
    joined: list[str] = []
    for part in parts:
        for page in _pages_of(part):
            copy = llms._split_copy(route, page + "\n")
            if f"Canonical: {llms.SITE_URL}/{route}/" not in copy.head:
                continue
            rest = copy.rest.split("\n")
            if (
                joined
                and joined[-1].startswith("|")
                and rest[1:2]
                and rest[1].startswith("| ---")
            ):
                rest = rest[2:]
            joined += rest
    return joined


def _write_page(dump: Dump, route: str, sections: list[tuple[str, int]]) -> str:
    """A page with an introduction and one H2 per *sections* entry.

    Each entry is a heading and roughly how many bytes of prose follow it.
    """
    lines = ["An introduction of a few words.", ""]
    for heading, size in sections:
        lines += [f"## {heading}", ""]
        sentence = f"Prose of the section {heading.lower()}, written to fill it. "
        lines += [(sentence * max(1, size // len(sentence))).rstrip(), ""]
    return dump.add(route, "\n".join(lines).rstrip("\n"))


@pytest.fixture
def dump(tmp_path: Path, fresh_caches: FreshCaches) -> Dump:
    """An empty dump the generator reads its pages from, its caches kept to the test."""
    fresh_caches(llms, PAGES=tmp_path / "dump")
    return Dump(tmp_path / "dump")


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A dump of the whole English site, every copy its page's source."""
    root = tmp_path_factory.mktemp("site-dump")
    site_dump(root, CONTENT_ROOT)
    return root


@pytest.mark.whole_tree
def test_a_page_over_the_budget_is_cut_at_its_h2_headings(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every part fits, opens with the page's head and, after the first, on an H2.

    Together the parts hold the page line for line: nothing dropped, nothing
    repeated.
    """
    route = _write_page(dump, "long", [(f"Section {n}", 10_000) for n in range(6)])
    whole = llms._copy(route)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)

    parts = llms._shard_parts("long", "Long", [route])

    assert len(parts) >= 3
    for number, part in enumerate(parts, start=1):
        assert _bytes(part) <= llms.SHARD_LIMIT_BYTES, (
            f"part {number} is {_bytes(part):,} bytes"
        )
        assert (
            part.splitlines()[0] == f"# phonometry: Long, part {number} of {len(parts)}"
        )
        [page] = _pages_of(part)
        assert page.startswith(whole.head + "\n\n"), (
            f"part {number} lost the page's head"
        )
        if number > 1:
            assert page.removeprefix(whole.head + "\n\n").startswith("## "), (
                f"part {number} does not open on an H2 heading"
            )
    assert _joined(route, parts) == whole.rest.split("\n")


def test_a_shard_of_several_pages_is_cut_between_its_pages(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three pages that fit two to a part make two parts, every page whole."""
    routes = [_write_page(dump, f"area/page-{n}", [("Only", 9_000)]) for n in range(3)]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)

    parts = llms._shard_parts("area", "Area", routes)

    assert len(parts) == 2
    assert "The pages of this area in 2 parts, cut between its pages" in parts[0]
    carried = [page for part in parts for page in _pages_of(part)]
    assert carried == [llms._copy(route).text for route in routes]


@pytest.mark.whole_tree
def test_every_shard_that_fits_is_left_as_it_was(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Lowering the budget cuts only the shards it no longer fits."""
    short = _write_page(dump, "short", [("One", 2_000)])
    long = _write_page(dump, "long", [(f"Section {n}", 10_000) for n in range(4)])
    plan = [("short", "Short", [short]), ("long", "Long", [long])]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 10**9)
    before = llms.build_shards(plan)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)

    after = llms.build_shards(plan)

    assert after["short"] == before["short"]
    assert len(after["long"]) > 1
    assert _bytes(before["long"][0]) > llms.SHARD_LIMIT_BYTES


def test_a_fenced_line_that_looks_like_an_h2_is_not_a_cut(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``## `` line inside a code fence is code, not a heading."""
    filler = "Words that fill the section up to its size. " * 60
    route = dump.add(
        "code",
        "\n".join(
            [
                "## First",
                "",
                filler,
                "",
                "```python",
                "## a comment that is not a heading",
                "x = 1",
                "```",
                "",
                filler,
                "",
                "## Second",
                "",
                filler,
            ]
        ),
    )
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 2 * len(filler) + 2_500)

    parts = llms._shard_parts("code", "Code", [route])

    assert len(parts) == 2
    assert "## a comment that is not a heading" in parts[0]
    assert _pages_of(parts[1])[0].split("\n---\n\n", 1)[1].startswith("## Second")


def test_a_cut_falls_at_every_heading_commonmark_reads_as_an_h2() -> None:
    """Indent of up to three spaces and a tab after the hashes still make an H2.

    Four spaces of indent make an indented code block, three hashes an H3,
    and ``##x`` with nothing between is a paragraph: none of them is a cut.
    """
    page = "\n".join(
        [
            "# Title",
            "## Plain",
            "  ## Indented by two",
            "##\tAfter a tab",
            "##",
            "    ## Indented code",
            "### An H3",
            "##not a heading",
        ]
    )

    heads = [section.splitlines()[0] for section in llms._sections(page)]

    assert heads == [
        "# Title",
        "## Plain",
        "  ## Indented by two",
        "##\tAfter a tab",
        "##",
    ]
    assert "\n".join(llms._sections(page)) == page


def test_a_page_under_the_budget_stays_one_file(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = _write_page(dump, "short", [("One", 2_000), ("Two", 2_000)])
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 50_000)

    parts = llms._shard_parts("short", "Short", [route])

    assert len(parts) == 1
    assert " part " not in parts[0].splitlines()[0]
    assert _pages_of(parts[0]) == [llms._copy(route).text]


def test_parts_are_balanced_rather_than_filled_in_turn(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Six equal sections over a budget that holds four make two parts of three.

    Filling the first part to the brim would leave a stub of two sections, and
    the cut would move with every line added near the top of the page.
    """
    route = _write_page(dump, "even", [(f"Section {n}", 10_000) for n in range(6)])
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 44_000)

    parts = llms._shard_parts("even", "Even", [route])

    assert [
        sum(line.startswith("## ") for line in _pages_of(part)[0].split("\n"))
        for part in parts
    ] == [3, 3]


def test_every_part_fits_once_its_head_lists_three_parts_or_more(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each part added to a shard lengthens the head of every part by a link.

    The room for the pages has to be measured under the head that lists every
    part. Under both budgets every part fits, opens on its own number, names
    every part in order, and the index entries of the shard link those same
    files; together the parts hold the page line for line.
    """
    sections = [("Section 0", 10_200)]
    sections += [(f"Section {n}", 10_000) for n in range(1, 6)]
    route = _write_page(dump, "long", sections)
    whole = llms._copy(route).rest.split("\n")
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)
    three = llms._shard_parts("long", "Long", [route])
    tight = max(map(_bytes, three)) - 1
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", tight)
    more = llms._shard_parts("long", "Long", [route])

    for limit, parts in ((25_000, three), (tight, more)):
        files = list(llms._published({"long": parts}))
        entries = llms._full_text_entries("Long", tuple(files))
        for number, (part, entry) in enumerate(zip(parts, entries, strict=True), 1):
            label = f"Long, part {number} of {len(parts)}"
            assert _bytes(part) <= limit, (
                f"{label} is {_bytes(part):,} bytes, over the {limit:,} budget"
            )
            assert part.splitlines()[0] == f"# phonometry: {label}"
            assert re.findall(_PART_FILE, part.split("\n---\n", 1)[0]) == files
            assert entry.startswith(f"- [{label}](")
        assert re.findall(_PART_FILE, "\n".join(entries)) == files
        assert files == [f"long-{number}" for number in range(1, len(parts) + 1)]
        assert _joined(route, parts) == whole
    assert len(more) > len(three)


def test_a_dump_with_dates_and_one_without_cut_every_shard_alike(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The cut is decided as if the dated lines were there, whether they are or not.

    The build writes the shards from copies with their dates, and the index
    that names their files is written by ``make llms`` from copies without
    them. Over budgets on both sides of the one where the page stops fitting
    in two parts, the two cut the page at the same places: the dated parts are
    the undated ones with the two lines added, and still fit.
    """
    body = "\n\n".join(f"## Section {n}\n\n" + "Filler text. " * 700 for n in range(4))
    dated = Dump(tmp_path / "dated")
    dated.add("page", body, dated=True)
    undated = Dump(tmp_path / "undated")
    undated.add("page", body, dated=False)

    def cut(dump: Dump, limit: int) -> tuple[str, ...]:
        monkeypatch.setattr(llms, "PAGES", dump.root)
        monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", limit)
        return llms._shard_parts("page", "Page", ["page"])

    def undate(text: str) -> str:
        return text.replace("Published: 2026-01-06\n", "").replace(
            "Updated: 2026-10-20\n", ""
        )

    # The smallest budget that holds the page in two parts, by bisection.
    low, high = 1_000, _bytes(cut(dated, 10**9)[0])
    while low < high:
        middle = (low + high) // 2
        if len(cut(undated, middle)) <= 2:
            high = middle
        else:
            low = middle + 1
    counts = set()
    for limit in range(high - 150, high + 150):
        with_dates, without = cut(dated, limit), cut(undated, limit)
        assert [undate(part) for part in with_dates] == list(without), limit
        assert all(_bytes(part) <= limit for part in with_dates), limit
        counts.add(len(with_dates))
    assert len(counts) > 1, (
        "the budgets tried do not cross a change in the number of parts"
    )


def test_the_conformance_report_is_cut_at_its_domains(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The report's copy writes each domain as an H2, and a part opens on one."""
    domains = [
        f"## {name}\n\n| Check | Expected | Computed |\n| --- | --- | --- |\n"
        + "\n".join(f"| {name} {n} | 1.0 | 1.0 |" for n in range(120))
        for name in (
            "Filters",
            "Levels",
            "Loudness",
            "Rooms",
            "Insulation",
            "Vibration",
        )
    ]
    route = dump.add(
        llms.CONFORMANCE_ROUTE,
        "The checks, domain by domain.\n\n" + "\n\n".join(domains),
    )
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 12_000)

    parts = llms._shard_parts("conformance", "Conformance report", [route])

    assert len(parts) >= 2
    openings = [
        _pages_of(part)[0].split("\n---\n\n", 1)[1].split("\n", 1)[0]
        for part in parts[1:]
    ]
    assert all(opening.startswith("## ") for opening in openings), openings
    assert "One page in" in parts[0]
    assert "at its own sections" in parts[0]
    assert _joined(route, parts) == llms._copy(route).rest.split("\n")


def test_a_catalogue_over_the_budget_is_cut_between_rows_and_repeats_its_header(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A catalogue is one table under a legend, with no heading to cut it at.

    Each part after the first opens with the table's header row and
    delimiter row, so its rows still say what their columns are, and with
    those taken out the parts joined in order are the copy.
    """
    header = "| Material | Density (kg/m³) | Source |"
    delimiter = "| --- | --- | --- |"
    rows = [
        f"| Material {n} | {1000 + n} | Book, Table 1, page {n} |" for n in range(400)
    ]
    body = "\n".join(
        [
            "What the books print, row by row.",
            "",
            "Each value is the number its page prints.",
            "",
            header,
            delimiter,
            *rows,
            "",
            "[^solids-1]: A note under the table.",
        ]
    )
    route = dump.add("reference/catalogues/solids", body)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 9_000)

    parts = llms._shard_parts("catalogues-solids", "Catalogue of solids", [route])

    assert len(parts) >= 3
    for part in parts:
        assert _bytes(part) <= llms.SHARD_LIMIT_BYTES
    for part in parts[1:]:
        rest = _pages_of(part)[0].split("\n---\n\n", 1)[1].split("\n")
        assert rest[:2] == [header, delimiter]
        assert rest[2].startswith("| Material ")
    assert "between the rows of its tables" in parts[0]
    assert _joined(route, parts) == llms._copy(route).rest.split("\n")


def test_a_cut_that_parts_a_row_from_the_note_it_cites_is_refused_by_name(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A row cut into an early part that cites a note defined under the table.

    The reader of that part would see a mark with no note under it, so the
    build stops and names the page and the note.
    """
    header = "| Material | Density (kg/m³) |"
    delimiter = "| --- | --- |"
    rows = [f"| Material {n}[^solids-1] | {1000 + n} |" for n in range(400)]
    body = "\n".join(
        [header, delimiter, *rows, "", "[^solids-1]: A note under the table."]
    )
    route = dump.add("reference/catalogues/solids", body)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 9_000)

    with pytest.raises(ValueError, match=r"solids: .*cites \[\^solids-1\]"):
        llms._shard_parts("catalogues-solids", "Catalogue of solids", [route])


def test_a_row_too_long_for_a_part_is_refused_by_name(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = [
        "| a | b |",
        "| --- | --- |",
        "| short | row |",
        f"| long | {'x' * 9_000} |",
    ]
    route = dump.add("reference/catalogues/wide", "\n".join(rows))
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 6_000)

    with pytest.raises(
        SystemExit,
        match=r"reference/catalogues/wide cannot be cut.*the table row '\| long",
    ):
        llms._shard_parts("catalogues-wide", "Wide", [route])


@pytest.mark.parametrize(
    ("sections", "named"),
    [
        ([("Small", 2_000), ("Enormous", 60_000), ("Small too", 2_000)], "## Enormous"),
        ([("Enormous on its own", 60_000)], "## Enormous on its own"),
    ],
    ids=["between two that fit", "the only one"],
)
def test_a_section_over_the_budget_with_no_table_is_refused_by_name(
    dump: Dump,
    monkeypatch: pytest.MonkeyPatch,
    sections: list[tuple[str, int]],
    named: str,
) -> None:
    route = _write_page(dump, "huge", sections)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 40_000)

    with pytest.raises(SystemExit, match=rf"huge cannot be cut.*its section '{named}'"):
        llms._shard_parts("huge", "Huge", [route])


def test_a_page_with_no_h2_over_the_budget_is_refused_by_name(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = dump.add("flat", "One long paragraph and no section. " * 1_500)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 40_000)

    with pytest.raises(
        SystemExit, match=r"flat cannot be cut.*the text before its first H2"
    ):
        llms._shard_parts("flat", "Flat", [route])


@pytest.mark.whole_tree
def test_the_index_lists_every_part_and_not_the_whole(
    site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``llms.txt`` names each part file, and no file the run did not write."""
    monkeypatch.setattr(llms, "PAGES", site)
    shards = llms.build_shards()
    files = {slug: llms._part_names(slug, len(parts)) for slug, parts in shards.items()}

    index = llms.build_llms_txt(llms._version(), files)

    linked = set(re.findall(r"/llms/llms-([a-z0-9-]+)\.txt", index))
    assert linked == set(llms._published(shards))
    cut = [slug for slug, names in files.items() if len(names) > 1]
    assert cut, "no shard of the site is cut into parts"
    for slug in cut:
        assert slug not in linked
        for name in files[slug]:
            assert f"({llms.SITE_URL}/llms/llms-{name}.txt)" in index


@pytest.mark.whole_tree
def test_a_carved_out_heading_links_every_part_of_its_shard(
    site: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The index heading of a cut shard offers each part, in order."""
    monkeypatch.setattr(llms, "PAGES", site)
    files: dict[str, tuple[str, ...]] = {
        slug: (slug,) for slug, _l, _r in llms._shard_plan()
    }
    files["devices-emission-intensity"] = llms._part_names(
        "devices-emission-intensity", 2
    )

    index = llms.build_llms_txt(llms._version(), files)

    heading = index.split("### Sound intensity and sound power from it\n\n", 1)[1]
    first = heading.splitlines()[0]
    assert re.findall(r"/llms/llms-([a-z0-9-]+)\.txt", first) == [
        "devices-emission-intensity-1",
        "devices-emission-intensity-2",
    ]


def test_two_shards_that_publish_one_file_name_are_refused() -> None:
    """A shard ``a`` in two parts and a shard ``a-1`` would write one file twice."""
    with pytest.raises(SystemExit, match=r"llms-a-1\.txt"):
        llms._published({"a": ("first", "second"), "a-1": ("third",)})
