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


def test_a_table_cell_is_read_on_its_own() -> None:
    page = (
        "| Standard | Link |\n| --- | --- |\n"
        "| ISO 12354-1:2017 | [catalogue](https://www.iso.org/standard/70238.html) |\n"
    )
    (problem,) = _named(page)
    assert "opens ISO 13887:2017" in problem


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
