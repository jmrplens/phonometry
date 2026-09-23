#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The reference-value gate: what it reads as a reference, and what it lets pass.

``scripts/check_reference_values.py`` holds every reference value declared in
``src`` to the ISO 1683 table: a copy of a table value fails, and a different
value fails unless it names the document it comes from. These tests pin the
three halves that decide that, on small modules written for the purpose: which
names declare a reference, what counts as naming a document, and what happens
to each kind of declaration. The last ones run it over the real tree, where it
has to be silent, and prove that the table it reads from the source is the
table the package publishes.
"""

from __future__ import annotations

import pathlib
import shutil
import sys
import textwrap

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_reference_values as crv

from phonometry import metrology


@pytest.fixture
def package(tmp_path: pathlib.Path) -> pathlib.Path:
    """A package directory holding the real table and nothing else yet."""
    root = tmp_path / "phonometry"
    (root / "metrology").mkdir(parents=True)
    shutil.copy(crv.SOURCE / crv.TABLE_MODULE, root / crv.TABLE_MODULE)
    return root


def _findings(
    package: pathlib.Path,
    source: str,
    exempt: dict[tuple[str, str], str] | None = None,
) -> list[crv.Finding]:
    path = package / "module.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    rows = crv.table_rows(package)
    found, _used = crv.check_file(path, rows, package, exempt or {})
    return found


def test_the_table_read_from_the_source_is_the_published_one() -> None:
    """The gate reads the AST, so it has to agree with what a caller imports."""
    published = {
        f"{medium}/{key}": (row.value, "note" in row.table)
        for medium, rows in metrology.ISO1683_REFERENCE_VALUES.items()
        for key, row in rows.items()
    }
    read = {row.key: (row.value, row.alternative) for row in crv.table_rows()}
    assert read == published


def test_the_table_holds_the_eighteen_values_and_the_alternative() -> None:
    """Tables 1 to 3 print eighteen values; note b of Table 3 adds the 50 nm/s."""
    rows = crv.table_rows()
    assert len(rows) == 19
    assert [row.key for row in rows if row.alternative] == [
        "solid/velocity_alternative"
    ]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("_P0", {"pressure", "power"}),
        ("_P_REF", {"pressure", "power"}),
        ("p_ref", {"pressure", "power"}),
        ("_W0", {"power"}),
        ("_I0", {"intensity"}),
        ("e0", {"exposure", "energy"}),
        ("REFERENCE_SOUND_POWER", {"power"}),
        ("_POWER_REFERENCE", {"power"}),
        ("FREE_VELOCITY_REFERENCE", {"velocity"}),
        ("reference_pressure_pa", {"pressure"}),
        ("VELOCITY_LEVEL_REFERENCE_MM_S", {"velocity"}),
    ],
)
def test_names_that_declare_a_reference(name: str, expected: set[str]) -> None:
    """A marker and a quantity, spelled out or as its symbol."""
    assert crv.quantities_of(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        # A quantity but no marker: a value of the quantity, not its reference.
        "DEFAULT_STATIC_PRESSURE_PA",
        # A marker but no ISO 1683 quantity.
        "_REFERENCE_FREQUENCY",
        "REFERENCE_DISTANCE_M",
        # The absorption area, whose symbol is not one of the four.
        "_A0",
        # Levels, not references: a decibel value, or a level with no unit.
        "_REFERENCE_PRESSURE_LEVEL_DB",
        "reference_power_level",
        # A tolerance that happens to hold the same number as the power.
        "_EPS",
    ],
)
def test_names_that_do_not(name: str) -> None:
    """Everything else is left alone, however the number reads."""
    assert crv.quantities_of(name) == frozenset()


@pytest.mark.parametrize(
    "text",
    [
        "ISO/TS 7849-1:2009, Equation 3",
        "the 5e-8 m/s of DIN EN 21683 (ISO 1683:1983)",
        "Standard mean-sea-level pressure of ECAC Doc 29 Eq. 4-7",
        "ITU-R BS.1770",
        "ECMA-418-2 clause 5.1.8",
        "the Leroy and Parthiot 1998 standard ocean",
    ],
)
def test_what_names_a_document(text: str) -> None:
    """A standard by body and number, or a book by author and year."""
    assert crv.DOCUMENT.search(text)


@pytest.mark.parametrize(
    "text",
    [
        "Reference force F0 of Formula (A.1), in newtons.",
        "Reference sound power, in watts (clause 3.6.3).",
        "the value THE STANDARD prints",
        "",
    ],
)
def test_what_does_not(text: str) -> None:
    """A clause or a formula number alone does not say which document."""
    assert not crv.DOCUMENT.search(text)


def test_a_copy_of_a_table_value_fails(package: pathlib.Path) -> None:
    """The class the gate exists for: the value typed out again."""
    found = _findings(package, "_P0 = 2.0e-5\n")
    assert [finding.name for finding in found] == ["_P0"]
    assert "repeats" in found[0].detail
    assert "gas/sound_pressure" in found[0].detail


def test_a_copy_fails_even_beside_a_citation(package: pathlib.Path) -> None:
    """Naming a document only excuses a *different* value, never a copy."""
    found = _findings(
        package, "_W0 = 1.0e-12  #: Reference sound power (ISO 9614-2, 3.6.3).\n"
    )
    assert [finding.name for finding in found] == ["_W0"]


def test_a_value_read_from_the_table_passes(package: pathlib.Path) -> None:
    """A pointer is not a number, so there is nothing to compare."""
    source = """\
        from .metrology.reference_values import ISO1683_REFERENCE_VALUES
        _P0 = ISO1683_REFERENCE_VALUES["gas"]["sound_pressure"].value
        _P0_SQUARED = _P0**2
    """
    assert _findings(package, source) == []


def test_a_different_value_needs_a_document(package: pathlib.Path) -> None:
    """The 50 nm/s alternative counts as different, and has to say who uses it."""
    found = _findings(package, "REFERENCE_VELOCITY = 5.0e-8\n")
    assert [finding.name for finding in found] == ["REFERENCE_VELOCITY"]
    assert "names no document" in found[0].detail


@pytest.mark.parametrize(
    "source",
    [
        "#: Reference velocity v0 (ISO/TS 7849-1:2009, Equation 3), m/s.\n"
        "REFERENCE_VELOCITY = 5.0e-8\n",
        "# The 5e-8 m/s of DIN EN 21683.\n# A second line of the same block.\n"
        "REFERENCE_VELOCITY = 5.0e-8\n",
        "REFERENCE_VELOCITY = 5.0e-8  # ISO 9611:1996 clause 7\n",
    ],
)
def test_a_document_above_or_beside_clears_it(
    package: pathlib.Path, source: str
) -> None:
    """The comment block above the line, or the comment on it."""
    assert _findings(package, source) == []


def test_a_document_two_statements_up_does_not(package: pathlib.Path) -> None:
    """The citation belongs to the declaration it sits on, not its neighbour."""
    source = """\
        #: The reference charge of DIN 4150-1:2001-06 Formula (5).
        _REFERENCE_CHARGE_KG = 1.0
        _REFERENCE_ENERGY_KJ = 1.0
    """
    found = _findings(package, source)
    assert [finding.name for finding in found] == ["_REFERENCE_ENERGY_KJ"]


def test_defaults_keywords_and_locals_are_declarations(
    package: pathlib.Path,
) -> None:
    """A number is bound to a name in three places, and all three are read."""
    source = """\
        def level(x, reference_pressure_pa=2e-5):
            e0 = 1e-12
            return helper(x, p_ref=1e-6)
    """
    found = _findings(package, source)
    assert sorted(finding.name for finding in found) == [
        "e0",
        "p_ref",
        "reference_pressure_pa",
    ]


def test_the_bare_twenty_micropascal_fails_anywhere(package: pathlib.Path) -> None:
    """The one literal that is never anything but the reference."""
    source = """\
        import numpy as np

        def spl(p):
            return 20 * np.log10(p / 2e-5)
    """
    found = _findings(package, source)
    assert [finding.name for finding in found] == ["2e-05"]


def test_a_literal_already_judged_is_reported_once(package: pathlib.Path) -> None:
    """The value of a declaration is the declaration's finding, not a second."""
    assert len(_findings(package, "_REF_PRESSURE = 2e-5\n")) == 1


def test_the_hatch_clears_one_function_and_not_another(
    package: pathlib.Path,
) -> None:
    """Keyed by the function: the next copy in the same module still fails."""
    source = """\
        def gravity(z):
            return 9.8 - 2e-5 * z

        def spl(p):
            return p / 2e-5
    """
    exempt = {("phonometry.module", "gravity"): "a gravity gradient"}
    found = _findings(package, source, exempt)
    assert [(finding.name, finding.line) for finding in found] == [("2e-05", 5)]


def test_an_unused_exemption_is_stale(package: pathlib.Path) -> None:
    """A hatch entry that clears nothing any more is reported, so it cannot rot."""
    (package / "module.py").write_text("x = 1\n", encoding="utf-8")
    _findings_found, stale = crv.check_tree(
        package, {("phonometry.module", "gone"): "why"}
    )
    assert stale == ["phonometry.module.gone"]


def test_main_fails_on_a_tree_with_a_copy(package: pathlib.Path) -> None:
    """The exit status is what CI reads."""
    (package / "module.py").write_text("_I0 = 1.0e-12\n", encoding="utf-8")
    assert crv.main(["--root", str(package)]) == 1


def test_the_package_is_clean() -> None:
    """The gate itself: every reference in src points at the table or cites."""
    findings, stale = crv.check_tree()
    assert findings == []
    assert stale == []
