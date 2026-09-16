#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where the provenance gate draws its lines.

``scripts/check_published_sources.py`` is the guard for a class of defect this
repository has now met twice: a published number that says which table it came
from and not which page, and a citation that names a folio the page does not
print. These tests fix the grammar it accepts, the shapes it looks inside, and
the two directions its allowlist ratchets in.

The gate's own end-to-end result, run against the real package, is the ``make
published-sources`` target; what is pinned here is the behaviour a future
change could quietly loosen.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_published_sources as gate

_GOOD = "Hopkins (2007) Table A3, PDF page 637 (printed p. 610)"


@dataclasses.dataclass(frozen=True)
class _Record:
    name: str = "specimen"
    source: str = _GOOD


@dataclasses.dataclass(frozen=True)
class _Unsourced:
    name: str = "specimen"


class TestCitationGrammar:
    """What a ``source`` field may say."""

    def test_the_shipped_form_passes(self) -> None:
        assert gate.citation_problems(_GOOD) == []

    def test_two_pages_are_joined_by_a_semicolon(self) -> None:
        """A specimen whose columns come off two pages names both."""
        both = (
            "Allard & Atalla 2e Table 6.1, PDF page 133 (printed p. 124); "
            "Allard & Atalla 2e Sect. 6.5.4, PDF page 132 (printed p. 123)"
        )
        assert gate.citation_problems(both) == []

    def test_an_absent_folio_has_its_own_spelling(self) -> None:
        """A landscape plate prints no folio, and says so rather than inventing one."""
        absent = (
            "Hopkins (2007) Table A2, PDF pages 635-636 "
            "(no printed folio; between folios 607 and 610)"
        )
        assert gate.citation_problems(absent) == []

    def test_a_missing_page_fails(self) -> None:
        problems = gate.citation_problems("Hopkins (2007) Table A3 (printed p. 610)")
        assert len(problems) == 1
        assert "PDF page N" in problems[0]

    def test_a_missing_folio_fails(self) -> None:
        problems = gate.citation_problems("Hopkins (2007) Table A3, PDF page 637")
        assert len(problems) == 1
        assert "PDF page N" in problems[0]

    def test_a_bare_folio_fails(self) -> None:
        """This is the defect the gate was proved red on."""
        problems = gate.citation_problems("Hopkins (2007) Table A3, PDF page 637 (610)")
        assert len(problems) == 1
        assert "writes the folio as '610'" in problems[0]

    def test_an_empty_source_fails(self) -> None:
        assert gate.citation_problems("") == [
            "is empty; every published value names the page it was read on"
        ]

    def test_a_file_path_is_not_a_document(self) -> None:
        """The registry cites documents; a path pins the claim to one machine."""
        problems = gate.citation_problems(
            "plan/literature/hopkins.pdf, PDF page 637 (printed p. 610)"
        )
        assert len(problems) == 1

    def test_a_document_outside_the_bibliography_fails(self) -> None:
        problems = gate.citation_problems(
            "Nobody & Nowhere (1999) Table 1, PDF page 1 (printed p. 1)"
        )
        assert len(problems) == 1
        assert "bibliography" in problems[0]


class TestWhereItLooks:
    """A record, a mapping of records and a sequence of records are all tables."""

    def test_a_bare_record_is_found(self) -> None:
        assert list(gate._sourced_records(_Record())) != []

    def test_records_inside_a_mapping_are_found(self) -> None:
        found = list(gate._sourced_records({"a": _Record(), "b": _Record()}))
        assert len(found) == 2

    def test_records_inside_a_sequence_are_found(self) -> None:
        assert len(list(gate._sourced_records((_Record(), _Record())))) == 2

    def test_a_record_without_the_field_is_not_one(self) -> None:
        assert list(gate._sourced_records(_Unsourced())) == []

    def test_a_string_is_not_a_sequence_of_records(self) -> None:
        assert list(gate._sourced_records("Hopkins (2007) Table A3")) == []


class TestTheCensus:
    """What counts as a transcribed table, so the registry cannot go stale."""

    def test_a_book_banner_naming_a_table_is_a_transcription(self) -> None:
        banner = "Hopkins (2007) Table A4, PDF page 637 (printed p. 610)"
        assert gate.BOOK_OR_PAPER.search(banner)
        assert gate.LOCATOR.search(banner)

    def test_a_standard_is_outside_the_registry(self) -> None:
        """ISO numbers its own tables, and this project cites them that way."""
        banner = "The seven rows of ISO 11546-2:1995 Table C.2, Annex C."
        assert gate.BOOK_OR_PAPER.search(banner) is None

    def test_a_book_named_without_a_locator_is_not_a_table(self) -> None:
        banner = "Default air density, in kg/m3 (Bies 5e: 1,205 at 20 degC)."
        assert gate.LOCATOR.search(banner) is None

    def test_a_banner_is_read_upwards_from_the_assignment(self) -> None:
        lines = [
            "#: first line",
            "#: second line",
            "TABLE = {1: 2, 3: 4}",
            "OTHER = ()",
        ]
        assert gate.banner_above(lines, 2) == "first line second line"
        assert gate.banner_above(lines, 3) == ""

    def test_only_a_collection_is_a_table(self, tmp_path: pathlib.Path) -> None:
        """A scalar is a cited number; the errata registry covers those."""
        module = tmp_path / "sample.py"
        module.write_text(
            "#: Hopkins (2007) Table A4, PDF page 637 (printed p. 610).\n"
            "TABLE = {'a': 1, 'b': 2}\n"
            "#: Hopkins (2007) Table A4, PDF page 637 (printed p. 610).\n"
            "SCALAR = 1.0\n"
            "#: Hopkins (2007) Table A4, PDF page 637 (printed p. 610).\n"
            "_PRIVATE_TABLE = (1.0, 2.0)\n"
            "lowercase = (1.0, 2.0)\n",
            encoding="utf-8",
        )
        found = {name for name, _ in gate.module_tables(module)}
        assert found == {"TABLE", "_PRIVATE_TABLE"}


class TestTheRatchet:
    """The registry and its allowlist, in both directions."""

    def test_the_real_tree_is_green(self) -> None:
        assert gate.registry_problems() == []
        assert gate.record_problems() == []

    def test_the_allowlist_is_empty_and_says_so(self) -> None:
        """Every source this repository transcribes from is one it can open."""
        assert gate.PAGE_UNKNOWN == {}

    def test_every_registered_table_names_a_document_and_what_it_holds(self) -> None:
        for (module, name), reason in gate.SOURCED.items():
            assert module.endswith(".py"), name
            assert "," in reason, name
            assert gate.BOOK_OR_PAPER.search(reason), name
