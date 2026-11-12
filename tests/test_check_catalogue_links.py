#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every ISO and IEC catalogue link opens the document it is written beside.

The catalogue number of a link says nothing a reader can check, so a slip of
one digit opens a steel sheet instead of a building-acoustics standard and
every page still builds. ``scripts/check_catalogue_links.py`` reads each link
beside the designation its page gives and holds it to the one the catalogue
gives the number.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[1] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_catalogue_links as ccl

_PINNED = {
    "iso": {
        "70242": "ISO 12354-1:2017",
        "70238": "ISO 13887:2017",
        "46520": "ISO 3382-3:2012",
        "77437": "ISO 3382-3:2022",
    },
    "iec": {
        "1204": "IEC 60268-1:1985",
        "1180": "IEC 60264-2-1:1989",
        "2777": "IEC 60651:1979",
    },
}

_FRONTMATTER = """---
title: "A page"
references:
  - type: standard
    designation: "{designation}"
    url: "{url}"
    note: "A note."
  - type: book
    title: "Another"
---

Body.
"""


def _problems(text: str, path: str = "docs/page.md") -> list[str]:
    return ccl.problems(ccl.links_in(path, text), _PINNED)


def _named(text: str, path: str = "docs/page.md") -> list[str]:
    """The problems a page has, leaving out the pins it does not link."""
    return [
        problem
        for problem in _problems(text, path)
        if "is linked from no page" not in problem
    ]


def test_a_frontmatter_link_to_another_document_is_named() -> None:
    page = _FRONTMATTER.format(
        designation="IEC 60268-1:1985",
        url="https://webstore.iec.ch/en/publication/1180",
    )
    (problem,) = _named(page, "site/src/content/docs/page.mdx")
    assert "page.mdx:6" in problem
    assert "opens IEC 60264-2-1:1989" in problem


def test_a_frontmatter_link_to_its_own_document_passes() -> None:
    page = _FRONTMATTER.format(
        designation="IEC 60268-1:1985",
        url="https://webstore.iec.ch/en/publication/1204",
    )
    assert _named(page) == []


def test_a_frontmatter_link_is_read_beside_its_own_reference_only() -> None:
    page = """---
references:
  - type: standard
    designation: "ISO 13887:2017"
  - type: standard
    designation: "ISO 12354-1:2017"
    url: "https://www.iso.org/standard/70238.html"
---
"""
    (problem,) = _named(page)
    assert "opens ISO 13887:2017" in problem


def test_an_entry_link_to_another_document_is_named() -> None:
    page = (
        "- International Organization for Standardization. (2017). *Building acoustics*\n"
        "  (ISO 12354-1:2017). [iso.org catalogue](https://www.iso.org/standard/70238.html).\n"
    )
    (problem,) = _named(page)
    assert "page.md:2" in problem
    assert "opens ISO 13887:2017" in problem


def test_an_entry_is_not_read_beside_the_entry_before_it() -> None:
    page = (
        "- Body. (2017). *Steel* (ISO 13887:2017).\n"
        "- Body. (2017). *Building acoustics* (ISO 12354-1:2017).\n"
        "  [iso.org catalogue](https://www.iso.org/standard/70238.html).\n"
    )
    (problem,) = _named(page)
    assert "opens ISO 13887:2017" in problem


def test_a_paragraph_is_not_read_beside_the_paragraph_before_it() -> None:
    page = "ISO 13887:2017 is cited above.\n\nThe [catalogue page](https://www.iso.org/standard/70238.html).\n"
    (problem,) = _named(page)
    assert "opens ISO 13887:2017" in problem


def test_a_newer_edition_link_does_not_vouch_for_the_entry_link() -> None:
    page = (
        "- Body. (2012). *Open plan offices* (ISO 3382-3:2012; since revised as\n"
        "  [ISO 3382-3:2022](https://www.iso.org/standard/77437.html)).\n"
        "  [iso.org catalogue](https://www.iso.org/standard/46520.html).\n"
    )
    assert _named(page) == []
    swapped = page.replace("46520", "77437").replace(
        "[ISO 3382-3:2022](https://www.iso.org/standard/77437",
        "[ISO 3382-3:2022](https://www.iso.org/standard/46520",
    )
    found = _named(swapped)
    assert len(found) == 2
    assert any("opens ISO 3382-3:2022" in problem for problem in found)


_REVISED = """---
references:
  - type: standard
    designation: "ISO 3382-3:2012"
    url: "https://www.iso.org/standard/{url}.html"
    note: "The quantities this page implements. {written} (https://www.iso.org/standard/{note}.html); the 2012 edition is the implemented one."
---
"""


def test_a_note_link_to_the_later_edition_it_names_passes() -> None:
    page = _REVISED.format(
        url="46520", written="Since revised as ISO 3382-3:2022", note="77437"
    )
    assert _named(page) == []


def test_a_note_link_to_another_edition_than_the_note_names_is_named() -> None:
    page = _REVISED.format(
        url="46520", written="Since revised as ISO 3382-3:2022", note="46520"
    )
    (problem,) = _named(page)
    assert "page.md:6" in problem
    assert "opens ISO 3382-3:2012" in problem


def test_the_reference_url_is_read_beside_its_designation_and_not_its_note() -> None:
    page = _REVISED.format(
        url="77437", written="Since revised as ISO 3382-3:2022", note="77437"
    )
    (problem,) = _named(page)
    assert "page.md:5" in problem
    assert "opens ISO 3382-3:2022" in problem


def test_a_note_naming_no_designation_is_read_beside_its_reference() -> None:
    page = _REVISED.format(url="46520", written="The catalogue page", note="46520")
    assert _named(page) == []
    (problem,) = _named(page.replace("standard/46520.html);", "standard/77437.html);"))
    assert "page.md:6" in problem
    assert "opens ISO 3382-3:2022" in problem


def test_a_note_names_the_designation_of_the_link_catalogue_only() -> None:
    page = _REVISED.format(
        url="46520", written="Measured with an IEC 61672-1:2013 meter", note="46520"
    )
    assert _named(page) == []


@pytest.mark.parametrize(
    "written",
    [
        "Adopted in Europe as EN ISO 3382-3:2012, the edition implemented here;"
        " since revised as ISO 3382-3:2022",
        "Adoptada en Europa como EN ISO 3382-3:2012, la edición implementada aquí;"
        " revisada después como ISO 3382-3:2022",
        "Adopted in Europe as EN ISO 3382-3:2012, the edition implemented here,"
        " and since revised as ISO 3382-3:2022",
    ],
)
def test_a_note_link_is_read_beside_the_last_designation_of_its_clause(
    written: str,
) -> None:
    assert _named(_REVISED.format(url="46520", written=written, note="77437")) == []
    (problem,) = _named(_REVISED.format(url="46520", written=written, note="46520"))
    assert "page.md:6" in problem
    assert "opens ISO 3382-3:2012" in problem


def test_a_note_link_is_not_read_beside_the_link_before_it() -> None:
    written = (
        "Since revised as ISO 3382-3:2022 (https://www.iso.org/standard/77437.html)"
        " and ISO 12354-1:2017"
    )
    assert _named(_REVISED.format(url="46520", written=written, note="70242")) == []
    (problem,) = _named(_REVISED.format(url="46520", written=written, note="77437"))
    assert "opens ISO 3382-3:2022, which the link is not written beside" in problem
    assert problem.endswith("'ISO 12354-1:2017 ('")


@pytest.mark.parametrize(
    ("revised", "label"),
    [
        ("the edition\n  implemented here; since revised as", "iso.org catalogue"),
        ("la edición\n  implementada aquí; revisada después como", "Catálogo iso.org"),
        ("withdrawn, superseded by", "iso.org catalogue"),
        ("retirada, sustituida por", "Catálogo iso.org"),
    ],
)
def test_an_entry_link_is_not_read_beside_the_edition_its_entry_names_as_later(
    revised: str, label: str
) -> None:
    entry = (
        "- International Organization for Standardization. (2012). *Open plan\n"
        f"  offices* (ISO 3382-3:2012, {revised} ISO 3382-3:2022).\n"
        f"  [{label}](https://www.iso.org/standard/{{}}.html).\n"
    )
    assert _named(entry.format("46520")) == []
    (problem,) = _named(entry.format("77437"))
    # The link is on the entry's last line.
    assert f"page.md:{entry.count(chr(10))}:" in problem
    assert "opens ISO 3382-3:2022" in problem


def test_a_paragraph_link_in_a_since_revised_clause_is_read_beside_that_clause() -> (
    None
):
    paragraph = (
        "The quantities follow ISO 3382-3:2012. Since revised as ISO 3382-3:2022\n"
        "(https://www.iso.org/standard/{}.html).\n"
    )
    assert _named(paragraph.format("77437")) == []
    (problem,) = _named(paragraph.format("46520"))
    assert "opens ISO 3382-3:2012" in problem


_AMENDED = {
    "iso": {"31397": "ISO 17497-1:2004", "60686": "ISO 17497-1:2004/Amd 1:2014"},
    "iec": {
        "1222": "IEC 60268-5:2003/AMD1:2007",
        "1223": "IEC 60268-5:2003",
        "1224": "IEC 60268-5:2003+AMD1:2007 CSV",
    },
}


def _amended(designation: str, url: str) -> list[str]:
    """The problems of a reference beside the amended editions pinned."""
    page = _FRONTMATTER.format(designation=designation, url=url)
    return [
        problem
        for problem in ccl.problems(ccl.links_in("docs/page.md", page), _AMENDED)
        if "is linked from no page" not in problem
    ]


@pytest.mark.parametrize(
    ("designation", "url", "opens"),
    [
        (
            "IEC 60268-5:2003+A1:2007",
            "https://webstore.iec.ch/en/publication/1223",
            "IEC 60268-5:2003",
        ),
        (
            "IEC 60268-5:2003",
            "https://webstore.iec.ch/en/publication/1224",
            "IEC 60268-5:2003+AMD1:2007 CSV",
        ),
        (
            "IEC 60268-5:2003+A1:2007",
            "https://webstore.iec.ch/en/publication/1222",
            "IEC 60268-5:2003/AMD1:2007",
        ),
        (
            "ISO 17497-1:2004+A1:2014",
            "https://www.iso.org/standard/60686.html",
            "ISO 17497-1:2004/Amd 1:2014",
        ),
    ],
)
def test_an_edition_its_amendment_and_their_consolidation_are_told_apart(
    designation: str, url: str, opens: str
) -> None:
    (problem,) = _amended(designation, url)
    assert f"opens {opens}, which" in problem


@pytest.mark.parametrize(
    ("designation", "url"),
    [
        ("IEC 60268-5:2003+A1:2007", "https://webstore.iec.ch/en/publication/1224"),
        (
            "IEC 60268-5:2003+AMD1:2007 CSV",
            "https://webstore.iec.ch/en/publication/1224",
        ),
        ("IEC 60268-5:2003", "https://webstore.iec.ch/en/publication/1223"),
        ("IEC 60268-5:2003/AMD1:2007", "https://webstore.iec.ch/en/publication/1222"),
        # ISO numbers no consolidated edition: the page of the edition lists
        # its amendment.
        ("ISO 17497-1:2004+A1:2014", "https://www.iso.org/standard/31397.html"),
        ("ISO 17497-1:2004/Amd 1:2014", "https://www.iso.org/standard/60686.html"),
    ],
)
def test_an_amended_designation_names_the_page_its_catalogue_gives_it(
    designation: str, url: str
) -> None:
    assert _amended(designation, url) == []


def test_another_edition_of_the_cited_document_is_named() -> None:
    page = _FRONTMATTER.format(
        designation="ISO 3382-3:2022", url="https://www.iso.org/standard/46520.html"
    )
    (problem,) = _named(page)
    assert "opens ISO 3382-3:2012" in problem


def test_a_designation_without_a_year_is_matched_by_its_number() -> None:
    page = (
        "Read [ISO 12354-1](https://www.iso.org/standard/70242.html) for the model.\n"
    )
    assert _named(page) == []


def test_a_table_link_to_another_document_than_its_row_names_is_named() -> None:
    page = (
        "| Standard | Link |\n| --- | --- |\n"
        "| ISO 12354-1:2017 | [catalogue](https://www.iso.org/standard/70238.html) |\n"
    )
    (problem,) = _named(page)
    assert "opens ISO 13887:2017" in problem


def test_a_table_link_is_read_beside_the_designation_in_the_cell_before_it() -> None:
    page = (
        "| Standard | Link |\n| --- | --- |\n"
        "| ISO 12354-1:2017 | [catalogue](https://www.iso.org/standard/70242.html) |\n"
    )
    assert _named(page) == []


def test_a_table_link_is_read_beside_the_nearest_designation_cell() -> None:
    row = (
        "| ISO 13887:2017 | ISO 12354-1:2017 | Part 1 |"
        " [catalogue](https://www.iso.org/standard/{}.html) |\n"
    )
    assert _named(row.format("70242")) == []
    (problem,) = _named(row.format("70238"))
    assert "opens ISO 13887:2017" in problem


def test_a_table_cell_that_names_a_designation_is_read_on_its_own() -> None:
    page = (
        "| ISO 12354-1:2017 | ISO 13887:2017,"
        " [catalogue](https://www.iso.org/standard/70242.html) |\n"
    )
    (problem,) = _named(page)
    assert "opens ISO 12354-1:2017" in problem


@pytest.mark.parametrize("label", ["2017 catalogue", "catálogo de 2017", "Part 1"])
def test_a_label_naming_no_designation_is_read_beside_the_text_before_it(
    label: str,
) -> None:
    page = "ISO 12354-1:2017. [{}](https://www.iso.org/standard/{}.html).\n"
    assert _named(page.format(label, "70242")) == []
    (problem,) = _named(page.format(label, "70238"))
    assert "opens ISO 13887:2017, which the link is not written beside" in problem


def test_a_label_naming_a_designation_of_the_other_catalogue_is_read_by_its_label() -> (
    None
):
    # The text before it names the document the link opens, but the label
    # tells the reader it opens another one.
    page = "ISO 12354-1:2017 ([IEC 12354-1:2017](https://www.iso.org/standard/70242.html)).\n"
    (problem,) = _named(page)
    assert "opens ISO 12354-1:2017, which" in problem
    assert problem.endswith("'IEC 12354-1:2017'")


_NOTE_LINK = """---
references:
  - type: standard
    designation: "{designation}"
    url: "https://www.iso.org/standard/{url}.html"
    note: "The quantities this page implements. {written}(https://www.iso.org/standard/{note}.html); the 2012 edition is the implemented one."
---
"""


@pytest.mark.parametrize(
    ("page", "label"),
    [
        # A cell before it names the document the link opens.
        (
            "| ISO 12354-1:2017 |"
            " [IEC 12354-1:2017](https://www.iso.org/standard/70242.html) |\n",
            "IEC 12354-1:2017",
        ),
        (
            "| ISO 12354-1:2017 | Part 1 |"
            " [IEC 12354-1:2017](https://www.iso.org/standard/70242.html) |\n",
            "IEC 12354-1:2017",
        ),
        # So does the reference's designation, and the clause of the note.
        (
            _NOTE_LINK.format(
                designation="ISO 3382-3:2022",
                url="77437",
                written="The catalogue page [IEC 3382-3:2022]",
                note="77437",
            ),
            "IEC 3382-3:2022",
        ),
        (
            _NOTE_LINK.format(
                designation="ISO 3382-3:2012",
                url="46520",
                written="Since revised as ISO 3382-3:2022, see [IEC 3382-3:2022]",
                note="77437",
            ),
            "IEC 3382-3:2022",
        ),
    ],
)
def test_a_label_naming_another_document_is_read_by_its_label_in_a_table_or_a_note(
    page: str, label: str
) -> None:
    # The label tells the reader which document the link opens, wherever the
    # link is written: a cell or a reference before it that names the right
    # one does not vouch for a label that names another.
    (problem,) = _named(page)
    assert "which the link is not written beside" in problem
    assert problem.endswith(f"{label!r}")


@pytest.mark.parametrize(
    ("page", "number"),
    [
        (
            "| ISO 13887:2017 |"
            " [ISO 12354-1:2017](https://www.iso.org/standard/{}.html) |\n",
            "70242",
        ),
        (
            _NOTE_LINK.format(
                designation="ISO 3382-3:2012",
                url="46520",
                written="The later edition [ISO 3382-3:2022]",
                note="{}",
            ),
            "77437",
        ),
    ],
)
def test_a_label_naming_the_document_is_read_by_its_label_in_a_table_or_a_note(
    page: str, number: str
) -> None:
    # A cell before it, or the reference, naming another document does not
    # hold a link whose label names the one it opens.
    assert _named(page.format(number)) == []
    (problem,) = _named(page.format("70238"))
    assert "opens ISO 13887:2017, which the link is not written beside" in problem


@pytest.mark.parametrize(
    "page",
    [
        # A paragraph that shows the address as an example.
        "Write `https://www.iso.org/standard/70238.html`, never a bare number.\n",
        # The same, in a list item and in a table cell.
        "- An example: `https://www.iso.org/standard/70238.html`.\n",
        "| Example | `https://www.iso.org/standard/70238.html` |\n| --- | --- |\n",
        # A span of two backticks, and one that wraps over two lines of its
        # paragraph.
        "An example: ``https://www.iso.org/standard/70238.html``.\n",
        "An example of a\nspan that wraps: `see\nhttps://www.iso.org/standard/70238.html`.\n",
        # A comment the page does not show.
        "<!-- https://www.iso.org/standard/70238.html -->\n",
    ],
)
def test_a_catalogue_address_in_inline_code_or_a_comment_is_no_link(page: str) -> None:
    assert ccl.links_in("docs/page.md", page) == []
    assert ccl.links_in("site/src/content/docs/page.mdx", page) == []


def test_an_address_between_escaped_backticks_is_a_link() -> None:
    page = "ISO 13887:2017 \\`https://www.iso.org/standard/70238.html\\`.\n"
    (link,) = ccl.links_in("docs/page.md", page)
    assert link.number == "70238"
    assert _named(page) == []


def test_an_address_in_inline_code_does_not_end_the_clause_of_a_link() -> None:
    page = (
        "ISO 12354-1:2017, unlike `https://www.iso.org/standard/70238.html`,"
        " [catalogue](https://www.iso.org/standard/70242.html).\n"
    )
    (link,) = ccl.links_in("docs/page.md", page)
    assert "ISO 12354-1:2017" in link.beside
    assert _named(page) == []


_PATHS = ("docs/page.md", "site/src/content/docs/page.mdx")


@pytest.mark.parametrize("path", _PATHS)
@pytest.mark.parametrize(
    "page",
    [
        # A label set in code names the document the reader expects.
        "- Not ISO 13887:2017: the model is"
        " [`ISO 12354-1:2017`](https://www.iso.org/standard/70238.html).\n",
        # So does a designation in code before the link, in its own clause.
        "Unlike ISO 13887:2017, the `ISO 12354-1:2017` model"
        " ([catalogue](https://www.iso.org/standard/70238.html)).\n",
    ],
)
def test_a_designation_in_inline_code_does_not_let_another_document_pass(
    page: str, path: str
) -> None:
    # The page shows the text of a code span: only an address in one is no
    # link, and the designation it writes is what the reader reads the link
    # beside.
    (problem,) = _named(page, path)
    assert "opens ISO 13887:2017, which the link is not written beside" in problem
    assert "ISO 12354-1:2017" in problem


@pytest.mark.parametrize("path", _PATHS)
@pytest.mark.parametrize(
    "page",
    [
        "The building model follows"
        " [`ISO 12354-1:2017`](https://www.iso.org/standard/70242.html).\n",
        'Pass `standard="ISO 12354-1:2017"`'
        " ([catalogue](https://www.iso.org/standard/70242.html)).\n",
    ],
)
def test_a_designation_in_inline_code_names_the_document_its_link_opens(
    page: str, path: str
) -> None:
    (link,) = ccl.links_in(path, page)
    assert "ISO 12354-1:2017" in link.beside
    assert _named(page, path) == []


@pytest.mark.parametrize("path", _PATHS)
def test_a_link_written_in_inline_code_is_text_and_not_a_link(path: str) -> None:
    # The page shows the markdown of a link in a code span as written: its
    # label is a designation the reader reads, not a link taken out.
    page = (
        "Unlike ISO 13887:2017, `[ISO 12354-1:2017](https://example.com)` is"
        " the form ([catalogue](https://www.iso.org/standard/{}.html)).\n"
    )
    assert _named(page.format("70242"), path) == []
    (problem,) = _named(page.format("70238"), path)
    assert "opens ISO 13887:2017, which the link is not written beside" in problem


@pytest.mark.parametrize("path", _PATHS)
def test_a_label_holding_a_bracket_in_inline_code_is_read_as_the_label(
    path: str,
) -> None:
    # A bracket in a code span opens and closes no link, so the label still
    # runs from its own bracket to the link, and the IEC designation it names
    # is what the reader expects the iso.org link to open.
    page = (
        "ISO 12354-1:2017 ([`gains[0]` of IEC 12354-1:2017]"
        "(https://www.iso.org/standard/70242.html)).\n"
    )
    (problem,) = _named(page, path)
    assert "opens ISO 12354-1:2017, which the link is not written beside" in problem
    assert problem.endswith("of IEC 12354-1:2017'")
    assert "gains" in problem


def test_a_note_address_between_backticks_is_still_a_link() -> None:
    # A frontmatter is YAML: the site shows a note as text and links every
    # address in it, backticks or not.
    page = _REVISED.format(
        url="46520", written="Since revised as ISO 3382-3:2022 `", note="46520"
    ).replace(".html);", ".html)`;")
    (problem,) = _named(page)
    assert "page.md:6" in problem
    assert "opens ISO 3382-3:2012" in problem


@pytest.mark.parametrize(
    "page",
    [
        "IEC 12354-1:2017 [catalogue](https://www.iso.org/standard/70242.html).\n",
        "See [IEC 12354-1:2017](https://www.iso.org/standard/70242.html).\n",
        "| IEC 12354-1:2017 | [catalogue](https://www.iso.org/standard/70242.html) |\n",
        _FRONTMATTER.format(
            designation="IEC 12354-1:2017",
            url="https://www.iso.org/standard/70242.html",
        ),
        "ISO 60268-1:1985 [catalogue](https://webstore.iec.ch/en/publication/1204).\n",
    ],
)
def test_a_designation_of_another_publisher_does_not_vouch_for_the_link(
    page: str,
) -> None:
    (problem,) = _named(page)
    assert "which the link is not written beside" in problem


@pytest.mark.parametrize(
    "written",
    [
        "ISO 12354-1:2017",
        "EN ISO 12354-1:2017",
        "UNE-EN ISO 12354-1:2017",
        "ISO/IEC 12354-1:2017",
        "IEC/ISO 12354-1:2017",
        "ISO\u00a012354-1:2017",
    ],
)
def test_a_designation_that_names_the_publisher_of_the_link_passes(
    written: str,
) -> None:
    page = f"{written}. [catalogue](https://www.iso.org/standard/70242.html).\n"
    assert _named(page) == []


_JOINT = {
    "iso": {"50461": "ISO/IEC Guide 98-3:2008", "2430": "IEC 60974-1:1998"},
    "iec": {"1176": "ISO/IEC GUIDE 98-3:2008", "2777": "IEC 60651:1979"},
}


@pytest.mark.parametrize(
    ("written", "url", "passes"),
    [
        # A joint document is named by either of its publishers, in either
        # catalogue.
        ("ISO/IEC Guide 98-3:2008", "https://www.iso.org/standard/50461.html", True),
        ("ISO/IEC Guide 98-3:2008", "https://webstore.iec.ch/publication/1176", True),
        ("IEC Guide 98-3:2008", "https://www.iso.org/standard/50461.html", True),
        ("ISO Guide 98-3:2008", "https://webstore.iec.ch/publication/1176", True),
        # ISO's catalogue lists some IEC documents on their own: the IEC
        # designation names them, an ISO one does not.
        ("IEC 60974-1:1998", "https://www.iso.org/standard/2430.html", True),
        ("ISO 60974-1:1998", "https://www.iso.org/standard/2430.html", False),
        # The 1997 renumbering still holds, under its own publisher only.
        ("IEC 651:1979", "https://webstore.iec.ch/publication/2777", True),
        ("ISO 651:1979", "https://webstore.iec.ch/publication/2777", False),
    ],
)
def test_the_publishers_that_name_a_document_are_those_its_catalogue_gives(
    written: str, url: str, *, passes: bool
) -> None:
    page = _FRONTMATTER.format(designation=written, url=url)
    found = [
        problem
        for problem in ccl.problems(ccl.links_in("docs/page.md", page), _JOINT)
        if "is linked from no page" not in problem
    ]
    assert (found == []) is passes


def test_the_old_iec_number_names_the_renumbered_publication() -> None:
    page = _FRONTMATTER.format(
        designation="IEC 651:1979", url="https://webstore.iec.ch/en/publication/2777"
    )
    assert _named(page) == []


@pytest.mark.parametrize(
    "url",
    [
        "https://www.iso.org/standard/99999.html",
        "https://webstore.iec.ch/publication/99999",
    ],
)
def test_a_number_the_table_does_not_hold_is_named(url: str) -> None:
    page = _FRONTMATTER.format(designation="ISO 12354-1:2017", url=url)
    (problem,) = _named(page)
    assert "99999 is not pinned" in problem
    assert "--refresh" in problem


def test_a_number_pinned_to_no_document_is_named() -> None:
    pinned = {"iso": {"79262": ""}, "iec": {}}
    page = _FRONTMATTER.format(
        designation="ISO 10140-2:2021", url="https://www.iso.org/standard/79262.html"
    )
    (problem,) = ccl.problems(ccl.links_in("docs/page.md", page), pinned)
    assert "opens no document the catalogue lists" in problem


def test_a_pinned_number_no_page_links_is_named() -> None:
    page = _FRONTMATTER.format(
        designation="IEC 60268-1:1985",
        url="https://webstore.iec.ch/en/publication/1204",
    )
    stale = [
        problem for problem in _problems(page) if "is linked from no page" in problem
    ]
    assert len(stale) == 6
    assert any("1180 (IEC 60264-2-1:1989)" in problem for problem in stale)


def test_a_spanish_label_and_a_non_breaking_space_are_read() -> None:
    page = (
        "- Organización. (2017). *Acústica* (ISO 12354‑1:2017).\n"
        "  [Catálogo iso.org](https://www.iso.org/standard/70242.html).\n"
    )
    assert _named(page) == []


def test_a_link_in_a_code_block_is_an_example_and_not_read() -> None:
    page = (
        "The rule's counterexample:\n\n```markdown\n"
        "(ISO 12354-1:2017). [iso.org catalogue](https://www.iso.org/standard/70238.html).\n"
        "```\n"
    )
    assert ccl.links_in("docs/page.md", page) == []


def test_main_names_each_link_and_fails(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=60)
    page = tmp_path / "docs" / "page.md"
    page.parent.mkdir()
    page.write_text(
        "See [ISO 12354-1:2017](https://www.iso.org/standard/70238.html).\n",
        encoding="utf-8",
    )
    pinned = tmp_path / "catalogue_ids.json"
    pinned.write_text(
        json.dumps({"iso": {"70238": "ISO 13887:2017"}, "iec": {}}), encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "docs/page.md"], check=True, timeout=60
    )
    monkeypatch.setattr(ccl, "ROOT", tmp_path)
    monkeypatch.setattr(ccl, "PINNED", pinned)
    assert ccl.main([]) == 1
    assert (
        "docs/page.md:1: iso catalogue number 70238 opens ISO 13887:2017"
        in capsys.readouterr().out
    )
    page.write_text(
        "See [ISO 13887:2017](https://www.iso.org/standard/70238.html).\n",
        encoding="utf-8",
    )
    assert ccl.main([]) == 0


def test_refresh_pins_from_the_catalogues_and_drops_what_no_page_links(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    open_data = tmp_path / "iso.jsonl"
    open_data.write_text(
        json.dumps({"id": 70242, "reference": "ISO 12354-1:2017"}) + "\n",
        encoding="utf-8",
    )
    pinned = tmp_path / "catalogue_ids.json"
    pinned.write_text(
        json.dumps({"iso": {"1": "ISO 1:2002"}, "iec": {"1204": "kept"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(ccl, "PINNED", pinned)
    monkeypatch.setattr(
        ccl, "_iec_designation", lambda number: f"IEC title of {number}"
    )
    links = [
        ccl.Link("docs/a.md", 1, "iso", "70242", ""),
        ccl.Link("docs/a.md", 2, "iso", "79262", ""),
        ccl.Link("docs/a.md", 3, "iec", "1204", ""),
        ccl.Link("docs/a.md", 4, "iec", "1176", ""),
    ]
    ccl.refresh(links, every=False, open_data=open_data)
    assert json.loads(pinned.read_text(encoding="utf-8")) == {
        "iso": {"70242": "ISO 12354-1:2017", "79262": ""},
        "iec": {"1176": "IEC title of 1176", "1204": "kept"},
    }


@pytest.mark.whole_tree
@pytest.mark.git_checkout
def test_every_catalogue_link_of_the_pages_opens_the_document_beside_it() -> None:
    links = ccl.read_links()
    assert len(links) > 800
    assert ccl.problems(links, ccl.load_pinned()) == []
