#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The formula numbers the published text gives for the DB-HR global indices.

CTE DB-HR Annex A prints one formula per global index, all of one shape:
minus ten lg of the energy sum, over the one-third-octave bands 100 Hz to
5 kHz, of the normalised spectrum less the band insulation. ``D2m,nT,A`` is
Formula (A.5) and ``D2m,nT,Atr`` (A.6) on printed page HR A-3, ``DnT,A`` (A.7)
on HR A-4, ``R'A`` (A.14) and ``RA`` (A.17) on HR A-8, and ``RA,tr`` (A.18) on
HR A-9 (CTE DB-HR, December 2019).

The guide's table of spectra cited (A.5), (A.7) for the pink-noise row, whose
first quantity is ``RA``, and (A.6) for the road-traffic row, whose first is
``RA,tr``; the guide gave "Formulae A.5 to A.7" for the index that the same
row computes ``RA`` and ``RA,tr`` with; the conformance row of ``R'A`` cited
(A.5); and ``ra`` and ``ra_tr`` named no formula at all. These tests hold each
of those places to the print.

The table only held the quantities it listed: ``R'A``, which the guide's
worked example computes with ``ra`` from an apparent ``R'`` and its figure
and comparison table name, was in no row, so no sentence tied it to
(A.14), and the API table's row of ``ra`` named (A.17) alone over that
example. So every global index the guide writes in its maths has to be a
quantity of the table, and the API row of ``ra`` names (A.14) too.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

from phonometry.building.regulation import spain as hr

_ROOT = Path(__file__).resolve().parents[3]

#: The formula DB-HR Annex A prints for each global index (see the module
#: docstring for the printed pages).
ANNEX_A_FORMULA = {
    "D2m,nT,A": 5,
    "D2m,nT,Atr": 6,
    "DnT,A": 7,
    "R'A": 14,
    "RA": 17,
    "RA,tr": 18,
}

#: The guide in both languages and its plain-markdown mirror.
GUIDE_PAGES = (
    "site/src/content/docs/buildings/insulation/spanish-building-code.mdx",
    "site/src/content/docs/es/buildings/insulation/spanish-building-code.mdx",
    "docs/buildings/insulation/spanish-building-code.md",
)

#: The public function of each global index, by the quantity it returns.
FUNCTION_OF = {
    "RA": hr.ra,
    "RA,tr": hr.ra_tr,
    "DnT,A": hr.dnt_a,
    "D2m,nT,A": hr.d2m_nt_a,
    "D2m,nT,Atr": hr.d2m_nt_atr,
}

#: A list of formula numbers after the word that introduces it, in either
#: language: "Formulae A.5 to A.7, A.14, A.17 and A.18", "fórmulas (A.5) a
#: (A.7)", "Formulae (A.5)-(A.7)".
_NUMBER = r"(?:\(A\.\d+\)|A\.\d+)"
_FORMULA_LIST = re.compile(
    rf"(?:[Ff]ormulae|[Ff]órmulas)\s+({_NUMBER}(?:(?:,\s*|\s+(?:to|and|a|y)\s+|\s*-\s*){_NUMBER})*)"
)
_RANGE = re.compile(r"A\.(\d+)\)?(?:\s+(?:to|a)\s+|\s*-\s*)\(?A\.(\d+)")

#: An attribute that describes a figure, which says what the figure draws.
_ALT = re.compile(r'\balt="[^"]*"')


def _numbers(listed: str) -> set[int]:
    """The formula numbers a list names, its ranges expanded."""
    found = {int(n) for n in re.findall(r"A\.(\d+)", listed)}
    for low, high in _RANGE.findall(listed):
        found.update(range(int(low), int(high) + 1))
    return found


def _quantities(cell: str) -> list[str]:
    """The DB-HR quantities a table cell writes in its maths, by name."""
    names = []
    for maths in re.findall(r"\$([^$]+)\$", cell):
        name = re.sub(r"\\mathrm|[{}_\s]", "", maths)
        if name in ANNEX_A_FORMULA:
            names.append(name)
    return names


#: A global index by name, as ``_quantities`` normalises maths, standing on its
#: own: ``RA`` is not read inside ``RA,tr`` nor ``R'A``.
_INDEX_IN_MATHS = re.compile(
    r"(?<![\w',])("
    + "|".join(
        re.escape(name) for name in sorted(ANNEX_A_FORMULA, key=len, reverse=True)
    )
    + r")(?![\w,'])"
)


#: A span of maths: a display between ``$$`` and ``$$``, or inline maths on one line.
_MATHS = re.compile(r"\$\$(.+?)\$\$|\$([^$\n]+)\$", re.DOTALL)


def _indices_in_maths(page: str) -> set[str]:
    """Every DB-HR global index a page writes anywhere in its maths."""
    found: set[str] = set()
    for display, inline in _MATHS.findall(page):
        maths = display or inline
        found.update(_INDEX_IN_MATHS.findall(re.sub(r"\\mathrm|[{}_\s]", "", maths)))
    return found


def _spectrum_rows(page: str) -> list[list[str]]:
    """The rows of the guide's table of spectra, one cell per column."""
    rows = []
    for line in page.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.match(r"Tab(?:le|la) A\.\d", cells[1]):
            rows.append(cells)
    return rows


def test_the_helpers_read_the_lists_and_cells_the_guide_writes() -> None:
    assert _numbers("A.5 to A.7, A.14, A.17 and A.18") == {5, 6, 7, 14, 17, 18}
    assert _numbers("(A.5) a (A.7)") == {5, 6, 7}
    assert _numbers("(A.5)-(A.7)") == {5, 6, 7}
    lists = _FORMULA_LIST.findall(
        "the index (Formulae A.5 to A.7) and (fórmulas A.17 y A.18)"
    )
    assert lists == ["A.5 to A.7", "A.17 y A.18"]
    assert _quantities(r"$R_\mathrm{A,tr}$, $D_{2\mathrm{m,n}T,\mathrm{Atr}}$") == [
        "RA,tr",
        "D2m,nT,Atr",
    ]
    assert _quantities(r"$D_{\mathrm{n}T,\mathrm{A}}$ and $R'_\mathrm{A}$") == [
        "DnT,A",
        "R'A",
    ]


@pytest.mark.parametrize("path", GUIDE_PAGES)
def test_each_row_of_the_spectra_table_cites_the_formulae_of_its_quantities(
    path: str,
) -> None:
    rows = _spectrum_rows((_ROOT / path).read_text(encoding="utf-8"))
    assert len(rows) == 4, f"{path}: the table of the four spectra was not found"
    wrong = []
    for spectrum, _table, defined, cited in rows:
        wanted = {ANNEX_A_FORMULA[name] for name in _quantities(defined)}
        given = {int(n) for n in re.findall(r"\(A\.(\d+)\)", cited)}
        if not wanted or given != wanted:
            wrong.append(
                f"{spectrum}: cites {sorted(given)}, the print gives {sorted(wanted)}"
            )
    assert wrong == [], f"{path}:\n" + "\n".join(wrong)


def test_the_reader_of_maths_finds_each_index_on_its_own() -> None:
    page = (
        "$$\nR_\\mathrm{A} = -10 \\lg \\sum\n$$\n\n"
        r"$R'_\mathrm{A} = 51.4$ dBA, $R_\mathrm{A,tr}$ and $D_{\mathrm{n}T,\mathrm{A}}$"
    )
    assert _indices_in_maths(page) == {"RA", "R'A", "RA,tr", "DnT,A"}


@pytest.mark.parametrize("path", GUIDE_PAGES)
def test_every_index_the_guide_writes_is_a_quantity_of_the_spectra_table(
    path: str,
) -> None:
    page = (_ROOT / path).read_text(encoding="utf-8")
    table = {
        name
        for _spectrum, _table, defined, _cited in _spectrum_rows(page)
        for name in _quantities(defined)
    }
    missing = sorted(_indices_in_maths(page) - table)
    assert missing == [], (
        f"{path}: the guide writes {missing}, which no row of the table of spectra "
        "ties to its formula"
    )


def test_the_api_row_of_ra_names_the_formula_of_each_index_it_computes() -> None:
    table = (_ROOT / "docs" / "reference" / "api" / "index.md").read_text(
        encoding="utf-8"
    )
    row = next(line for line in table.splitlines() if line.startswith("| `ra` |"))
    given = {int(n) for n in re.findall(r"A\.(\d+)", row)}
    wanted = {ANNEX_A_FORMULA["RA"]}
    if "r_prime" in row:
        wanted.add(ANNEX_A_FORMULA["R'A"])
    assert given == wanted, (
        f"the row of ra cites {sorted(given)}, it computes {sorted(wanted)}"
    )


@pytest.mark.parametrize("path", GUIDE_PAGES)
def test_every_formula_list_for_the_index_reaches_every_quantity_of_the_table(
    path: str,
) -> None:
    page = (_ROOT / path).read_text(encoding="utf-8")
    table = {
        ANNEX_A_FORMULA[name]
        for _spectrum, _table, defined, _cited in _spectrum_rows(page)
        for name in _quantities(defined)
    }
    lists = _FORMULA_LIST.findall(_ALT.sub("", page))
    assert lists, f"{path}: no list of formulae was found"
    short = [
        f"{listed}: lacks {sorted(table - _numbers(listed))}"
        for listed in lists
        if table - _numbers(listed)
    ]
    assert short == [], f"{path}:\n" + "\n".join(short)


def test_each_global_index_function_names_the_formula_of_its_quantity() -> None:
    wrong = []
    for name, function in FUNCTION_OF.items():
        summary = (inspect.getdoc(function) or "").split("\n\n", 1)[0]
        given = {int(n) for n in re.findall(r"Formula \(A\.(\d+)\)", summary)}
        if given != {ANNEX_A_FORMULA[name]}:
            wrong.append(
                f"{function.__name__}: {sorted(given)}, the print gives (A.{ANNEX_A_FORMULA[name]})"
            )
    assert wrong == [], "\n".join(wrong)


def test_the_general_index_names_the_formula_of_every_quantity_it_computes() -> None:
    wanted = set(ANNEX_A_FORMULA.values())
    for where, text in (
        ("module", inspect.getdoc(hr) or ""),
        ("db_hr_global_index", inspect.getdoc(hr.db_hr_global_index) or ""),
    ):
        lists = _FORMULA_LIST.findall(text)
        assert lists, f"{where}: no list of formulae was found"
        short = [
            f"{listed}: lacks {sorted(wanted - _numbers(listed))}"
            for listed in lists
            if wanted - _numbers(listed)
        ]
        assert short == [], f"{where}:\n" + "\n".join(short)


def test_each_conformance_row_of_a_global_index_cites_its_formula() -> None:
    scripts = str(_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import conformance_report

    wrong = []
    read = 0
    for check in conformance_report.CHECKS:
        cited = re.match(r"CTE DB-HR Annex A, Formula \(A\.(\d+)\)", check.standard)
        if cited is None:
            continue
        read += 1
        named = [
            name
            for name in ANNEX_A_FORMULA
            if re.search(rf"(?<![\w',]){re.escape(name)}(?![\w,'])", check.quantity)
        ]
        if [ANNEX_A_FORMULA[name] for name in named] != [int(cited[1])]:
            wrong.append(
                f"{check.standard} | {check.quantity}: the print gives {named}"
            )
    assert read > 0, "no conformance row of a DB-HR global index was found"
    assert wrong == [], "\n".join(wrong)
