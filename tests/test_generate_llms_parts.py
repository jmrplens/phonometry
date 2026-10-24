#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A page too long for one fetch travels in numbered parts, cut at its H2s.

The shards exist so that a client that truncates a response reads one whole
area instead of the first pages of everything. A shard that holds a single page
has nothing left to narrow: when the upgrade guide alone came within a few
hundred bytes of the budget, the only ways out were to split the guide on the
site, which serves its readers worse, or to raise the budget, which the budget
exists to forbid. The generator cuts such a page at its own H2 headings
instead, into as few parts as fit, lists every part in ``llms.txt``, and
refuses by name a page with a section that is over the budget by itself.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms

_HEAD_END = "\n---\n"
_SOURCE = re.compile(r"^Source: \S+$", re.MULTILINE)
#: A link to a shard file, capturing the name ``llms-`` precedes.
_PART_FILE = re.compile(r"/llms/llms-([a-z0-9-]+)\.txt")


def _bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def _page_lines(shard: str) -> list[str]:
    """The non-blank lines of the page a one-page shard carries.

    A shard opens with its own head, then the page's attribution (an HTML
    comment and a ``Source:`` line), the page, and a closing rule.
    """
    body = shard.split(_HEAD_END, 1)[1]
    source = _SOURCE.search(body)
    assert source is not None, "the shard carries no Source: line"
    page = body[source.end() :].rsplit(_HEAD_END, 1)[0]
    return [line for line in page.splitlines() if line.strip()]


def _write_page(docs: Path, name: str, sections: list[tuple[str, int]]) -> str:
    """A mirror page with an H1, an intro and one H2 per *sections* entry.

    Each entry is a heading and roughly how many bytes of prose follow it.
    """
    lines = ["# A long page", "", "An introduction of a few words.", ""]
    for heading, size in sections:
        lines += [f"## {heading}", ""]
        sentence = f"Prose of the section {heading.lower()}, written to fill it. "
        lines += [(sentence * max(1, size // len(sentence))).rstrip(), ""]
    (docs / name).write_text("\n".join(lines), encoding="utf-8")
    return name


@pytest.fixture
def docs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty mirror tree the generator reads its pages from."""
    monkeypatch.setattr(llms, "DOCS", tmp_path)
    return tmp_path


def _whole_shards(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Every shard in one file, built under a budget each of them fits whole.

    The real budget may already have cut the upgrade guide, and will once a
    branch adds to it, so a test that needs the page in one piece builds it
    with no budget to speak of and sets the one it tests afterwards.
    """
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 10**9)
    shards = llms.build_shards()
    assert all(len(parts) == 1 for parts in shards.values())
    return {slug: parts[0] for slug, parts in shards.items()}


def test_the_upgrade_guide_over_the_budget_is_cut_at_its_h2_headings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real page, against a budget it no longer fits in.

    Every part fits, every part after the first opens on an H2, and the parts
    together hold the page line for line: nothing dropped, nothing repeated.
    """
    text = _whole_shards(monkeypatch)["upgrading"]
    limit = _bytes(text) * 3 // 5
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", limit)

    parts = llms.build_shards()["upgrading"]

    assert len(parts) >= 2, f"a {_bytes(text):,} byte page fits {limit:,} bytes"
    for number, part in enumerate(parts, start=1):
        assert _bytes(part) <= limit, f"part {number} is {_bytes(part):,} bytes"
        assert f"part {number} of {len(parts)}" in part.splitlines()[0]
        assert _SOURCE.search(part), f"part {number} lost the page's attribution"
        if number > 1:
            assert _page_lines(part)[0].startswith("## "), (
                f"part {number} does not open on an H2 heading"
            )
    assert [line for part in parts for line in _page_lines(part)] == _page_lines(text)


def test_every_shard_that_fits_is_left_as_it_was(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lowering the budget cuts only the one-page shards it no longer fits.

    A shard of several pages over it stays whole, for the budget check to
    refuse and a narrower split to fix; every shard under it is byte for byte
    what it was.
    """
    before = _whole_shards(monkeypatch)
    limit = _bytes(before["upgrading"]) * 3 // 5
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", limit)

    after = llms.build_shards()

    assert after.keys() == before.keys()
    cut = {slug for slug, parts in after.items() if len(parts) > 1}
    assert "upgrading" in cut
    for slug, parts in after.items():
        if slug not in cut:
            assert parts == (before[slug],), f"llms-{slug}.txt changed"
        else:
            assert _bytes(before[slug]) > limit


def test_a_fenced_line_that_looks_like_an_h2_is_not_a_cut(
    docs: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``## `` line inside a code fence is code, not a heading."""
    filler = "Words that fill the section up to its size. " * 60
    page = "\n".join(
        [
            "# A page with code",
            "",
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
    )
    (docs / "code.md").write_text(page, encoding="utf-8")
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 2 * len(filler) + 2_000)

    parts = llms._shard_parts("code", "Code", [("code.md", "code")])

    assert len(parts) == 2
    assert "## a comment that is not a heading" in parts[0]
    assert _page_lines(parts[1])[0] == "## Second"


def test_a_page_under_the_budget_stays_one_file(
    docs: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = _write_page(docs, "short.md", [("One", 2_000), ("Two", 2_000)])
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 50_000)

    parts = llms._shard_parts("short", "Short", [(name, "short")])

    assert parts == (llms._shard_text("Short", [(name, "short")]),)
    assert " part " not in parts[0].splitlines()[0]


def test_parts_are_balanced_rather_than_filled_in_turn(
    docs: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Six equal sections over a budget that holds four make two parts of three.

    Filling the first part to the brim would leave a stub of two sections, and
    the cut would move with every line added near the top of the page.
    """
    name = _write_page(docs, "even.md", [(f"Section {n}", 10_000) for n in range(6)])
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 43_000)

    parts = llms._shard_parts("even", "Even", [(name, "even")])

    assert [
        sum(line.startswith("## ") for line in _page_lines(part)) for part in parts
    ] == [3, 3]


def test_every_part_fits_once_its_head_lists_three_parts_or_more(
    docs: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each part added to a page lengthens the head of every part by a link.

    The fixed page needs three parts under a budget of 25,000 bytes. One byte
    under the largest of them, the same three no longer fit, although the
    shorter head of a page in two would still leave them room: the room for
    the page has to be measured under the head that lists every part, and that
    takes this page to four. Under both budgets every part fits, opens on its
    own number, names every part in order, and the index entries of the shard
    link those same files; together the parts hold the page line for line.
    """
    sections = [("Section 0", 10_200)]
    sections += [(f"Section {n}", 10_000) for n in range(1, 6)]
    page = [(_write_page(docs, "long.md", sections), "long")]
    whole = _page_lines(llms._shard_text("Long", page))
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)
    three = llms._shard_parts("long", "Long", page)
    tight = max(map(_bytes, three)) - 1
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", tight)
    four = llms._shard_parts("long", "Long", page)

    for limit, parts, count in ((25_000, three, 3), (tight, four, 4)):
        files = list(llms._published({"long": parts}))
        entries = llms._full_text_entries("Long", tuple(files))
        for number, (part, entry) in enumerate(zip(parts, entries, strict=True), 1):
            label = f"Long, part {number} of {len(parts)}"
            assert _bytes(part) <= limit, (
                f"{label} is {_bytes(part):,} bytes, over the {limit:,} budget"
            )
            assert part.splitlines()[0] == f"# phonometry: {label}"
            assert re.findall(_PART_FILE, part.split(_HEAD_END, 1)[0]) == files
            assert entry.startswith(f"- [{label}](")
        assert re.findall(_PART_FILE, "\n".join(entries)) == files
        assert files == [f"long-{number}" for number in range(1, count + 1)], (
            f"{len(parts)} parts under {limit:,} bytes, not {count}"
        )
        assert [line for part in parts for line in _page_lines(part)] == whole


@pytest.mark.parametrize(
    ("sections", "named"),
    [
        ([("Small", 2_000), ("Enormous", 60_000), ("Small too", 2_000)], "Enormous"),
        ([("Enormous on its own", 60_000)], "Enormous on its own"),
    ],
    ids=["between two that fit", "the only one"],
)
def test_a_section_over_the_budget_by_itself_is_refused_by_name(
    docs: Path,
    monkeypatch: pytest.MonkeyPatch,
    sections: list[tuple[str, int]],
    named: str,
) -> None:
    name = _write_page(docs, "huge.md", sections)
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 40_000)

    with pytest.raises(SystemExit, match=rf"docs/huge\.md.*## {named}\b"):
        llms._shard_parts("huge", "Huge", [(name, "huge")])


def test_a_page_with_no_h2_over_the_budget_is_refused_by_name(
    docs: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal gives the size the shard would have, not the source's.

    The shard adds its head, the attribution and absolute links to the page,
    so a page whose own file fits the budget can still make a shard over it:
    quoting the source's size would report a number under the budget as the
    reason the run stopped.
    """
    limit = 40_000
    source = "# Flat\n\n" + "One long paragraph and no section. " * 1_141
    (docs / "flat.md").write_text(source, encoding="utf-8")
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", limit)
    shard = _bytes(llms._shard_text("Flat", [("flat.md", "flat")]))
    assert _bytes(source) <= limit < shard

    with pytest.raises(
        SystemExit,
        match=rf"docs/flat\.md makes llms-flat\.txt {shard:,} bytes.*no H2 heading",
    ):
        llms._shard_parts("flat", "Flat", [("flat.md", "flat")])


def test_the_index_lists_every_part_and_not_the_whole(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``llms.txt`` names each part file, and no file the run did not write."""
    upgrading = _whole_shards(monkeypatch)["upgrading"]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", _bytes(upgrading) * 3 // 5)
    shards = llms.build_shards()
    files = {slug: llms._part_names(slug, len(parts)) for slug, parts in shards.items()}

    index = llms.build_llms_txt(llms._version(), files)

    linked = set(re.findall(r"/llms/llms-([a-z0-9-]+)\.txt", index))
    assert linked == set(llms._published(shards))
    assert "upgrading" not in linked
    count = len(files["upgrading"])
    for number in range(1, count + 1):
        assert (
            f"- [Upgrading from 3.3 to 4.0, part {number} of {count}]"
            f"({llms.SITE_URL}/llms/llms-upgrading-{number}.txt)"
        ) in index


def test_a_carved_out_heading_links_every_part_of_its_shard() -> None:
    """The index heading of a cut shard offers each part, in order."""
    files: dict[str, tuple[str, ...]] = {slug: (slug,) for slug in llms.build_shards()}
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


def test_the_committed_index_links_every_committed_shard_file() -> None:
    """What ``site/public/llms/`` serves is what ``llms.txt`` lists."""
    index = (ROOT / "llms.txt").read_text(encoding="utf-8")
    linked = set(re.findall(r"/llms/(llms-[a-z0-9-]+\.txt)", index))
    served = {path.name for path in (ROOT / "site" / "public" / "llms").glob("*.txt")}
    assert linked == served, (
        f"listed but not served: {sorted(linked - served)}; "
        f"served but not listed: {sorted(served - linked)}"
    )


def test_two_shards_that_publish_one_file_name_are_refused() -> None:
    """A shard ``a`` in two parts and a shard ``a-1`` would write one file twice."""
    with pytest.raises(SystemExit, match=r"llms-a-1\.txt"):
        llms._published({"a": ("first", "second"), "a-1": ("third",)})
