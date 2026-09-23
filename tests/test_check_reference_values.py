#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The reference-value gate: what it reads as a reference, and what it lets pass.

``scripts/check_reference_values.py`` holds every reference value declared in
``src`` to the ISO 1683 table: a copy of a table value fails, and a different
value fails unless it names the document it comes from and is listed with its
value. These tests pin the halves that decide that, on small modules written
for the purpose: which names declare a reference, what counts as naming a
document, what happens to each kind of declaration, and which bare literals
are references wherever they stand. The last ones run it over the real tree,
where it has to be silent, put a mistyped number back into real modules,
where it has to speak, and prove that the table it reads from the source is
the table the package publishes.
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

#: The departure the tests that need one list, as the tree lists its own.
_ISO_9611 = {
    ("phonometry.module", "REFERENCE_VELOCITY"): (5e-8, "ISO 9611:1996 clause 7"),
}


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
    different: dict[tuple[str, str], tuple[float, str]] | None = None,
) -> list[crv.Finding]:
    path = package / "module.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    rows = crv.table_rows(package)
    return crv.check_file(path, rows, package, exempt or {}, different or {}).findings


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
        # The absorption area: a weak symbol, not a quantity the name states.
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
    ("name", "expected"),
    [
        ("v0", {"velocity"}),
        ("_V_REF", {"velocity"}),
        ("a0", {"acceleration"}),
        ("_A0", {"acceleration"}),
        ("F0", {"force"}),
        ("F0_REF", {"force"}),
        ("xi0", {"displacement"}),
        ("_D_REF", {"displacement"}),
        # A name that states its quantity is read by the strong rules instead.
        ("_P0", set()),
        # No marker, so not a reference of anything.
        ("velocity", set()),
    ],
)
def test_the_weak_symbols(name: str, expected: set[str]) -> None:
    """The notation the standards print for the vibratory references."""
    assert crv.symbol_quantities_of(name) == expected


@pytest.mark.parametrize(
    "text",
    [
        "ISO/TS 7849-1:2009, Equation 3",
        "DIN 45672-2:1995-07 Formula (2)",
        "Standard mean-sea-level pressure of ECAC Doc 29 Eq. 4-7",
        "ITU-R BS.1770",
        "ECMA-418-2 clause 5.1.8",
        "the Leroy and Parthiot 1998 standard ocean",
        "the W0 of Hopkins (2007) Table 2.1",
        "Bies et al. 2017",
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
        "In 2019 we measured this",
        "Since 2015 unchanged",
        "Changed 2024 by hand",
        "Formula 3, see EN 1",
        "",
    ],
)
def test_what_does_not(text: str) -> None:
    """A clause, a formula number or a sentence with a year does not say which."""
    assert not crv.DOCUMENT.search(text)


@pytest.mark.parametrize(
    "text",
    [
        "(ISO 1683:2015 Table 1)",
        "the 1 µN of ISO 1683 Table 3",
        "UNE-EN ISO 1683:2016, PDF page 8",
        "EN ISO 1683:2015 Table 2",
    ],
)
def test_iso_1683_itself_is_not_the_other_document(text: str) -> None:
    """The table a value departs from cannot be where the departure comes from."""
    assert not crv.names_a_document(text)


@pytest.mark.parametrize(
    "text",
    [
        "ISO 1683:1983",
        "DIN EN 21683",
        "EN 15657:2018 clause 7.1; the 1 pW of ISO 1683:2015 Table 1",
    ],
)
def test_an_earlier_edition_or_another_standard_is(text: str) -> None:
    """An older edition is another document, and so is a standard cited beside."""
    assert crv.names_a_document(text)


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
    found = _findings(package, "REFERENCE_VELOCITY = 5.0e-8\n", different=_ISO_9611)
    assert [finding.name for finding in found] == ["REFERENCE_VELOCITY"]
    assert "names no document" in found[0].detail


@pytest.mark.parametrize(
    "source",
    [
        "#: Reference velocity v0 (ISO/TS 7849-1:2009, Equation 3), m/s.\n"
        "REFERENCE_VELOCITY = 5.0e-8\n",
        "# The 5e-8 m/s of DIN 45672-2:1995-07 Formula (2).\n"
        "# A second line of the same block.\n"
        "REFERENCE_VELOCITY = 5.0e-8\n",
        "REFERENCE_VELOCITY = 5.0e-8  # ISO 9611:1996 clause 7\n",
    ],
)
def test_a_document_above_or_beside_clears_a_listed_value(
    package: pathlib.Path, source: str
) -> None:
    """The comment block above the line, or the comment on it."""
    assert _findings(package, source, different=_ISO_9611) == []


def test_a_different_value_has_to_be_listed(package: pathlib.Path) -> None:
    """A document beside it is not enough: the departure is pinned to its value."""
    source = "REFERENCE_VELOCITY = 5.0e-8  # ISO 9611:1996 clause 7\n"
    found = _findings(package, source)
    assert [finding.name for finding in found] == ["REFERENCE_VELOCITY"]
    assert "DIFFERENT_REFERENCES" in found[0].detail


def test_a_listed_value_that_changed_fails(package: pathlib.Path) -> None:
    """A typo in a deliberate departure is caught by the value it is pinned to."""
    source = "REFERENCE_VELOCITY = 5.0e-9  # ISO 9611:1996 clause 7\n"
    found = _findings(package, source, different=_ISO_9611)
    assert [finding.name for finding in found] == ["REFERENCE_VELOCITY"]
    assert "records 5e-08" in found[0].detail


@pytest.mark.parametrize(
    "source",
    [
        # The comment a pointer to Table 1 carries, left above a wrong number.
        "#: Reference sound pressure in air, 20 µPa (ISO 1683:2015 Table 1).\n"
        "_P_REF = 2e-6\n",
        "#: Reference sound power, 1 pW (ISO 1683:2015 Table 1).\n_W0 = 1e-13\n",
        "REFERENCE_FORCE = 1e-5  # ISO 1683 Table 3\n",
        # Another document cited too, as the real pointers do.
        "#: Reference force ``F0`` of the blocked force level (EN 15657), N:\n"
        "#: the 1 µN of ISO 1683:2015 Table 3.\n"
        "REFERENCE_FORCE: float = 1.0e-5\n",
    ],
)
def test_a_mistyped_number_under_a_pointer_comment_fails(
    package: pathlib.Path, source: str
) -> None:
    """The comment survives the typo, so the comment cannot be what clears it."""
    assert len(_findings(package, source)) == 1


def test_a_document_two_statements_up_does_not(package: pathlib.Path) -> None:
    """The citation belongs to the declaration it sits on, not its neighbour."""
    source = """\
        #: The reference charge of DIN 4150-1:2001-06 Formula (5).
        _REFERENCE_CHARGE_KG = 1.0
        _REFERENCE_ENERGY_KJ = 1.0
    """
    found = _findings(package, source)
    assert [finding.name for finding in found] == ["_REFERENCE_ENERGY_KJ"]


def test_every_place_a_name_binds_a_number_is_read(package: pathlib.Path) -> None:
    """Assignments, defaults, keywords, unpacking, dict keys and wrapped literals."""
    source = """\
        import numpy as np

        def level(x, reference_pressure_pa=2e-5, *, reference_power_w=1e-12):
            e0 = 1e-12
            return helper(x, p_ref=1e-6)

        class Meter:
            def __init__(self):
                self._w0 = 1e-12

        _I0 = np.float64(1e-12)
        _P0, _W0 = 1e-6, 1e-12
        REFERENCES = {"i_ref": 1e-12}
    """
    found = _findings(package, source)
    assert sorted(finding.name for finding in found) == [
        "_I0",
        "_P0",
        "_W0",
        "_w0",
        "e0",
        "i_ref",
        "p_ref",
        "reference_power_w",
        "reference_pressure_pa",
    ]


@pytest.mark.parametrize(
    ("source", "name"),
    [
        ("v0 = 1e-9\n", "v0"),
        ("_V_REF = 1e-9\n", "_V_REF"),
        ("F0_REF = 1e-6\n", "F0_REF"),
        ("def f():\n    a0 = 1e-6  # reference acceleration\n    return a0\n", "a0"),
    ],
)
def test_a_weak_symbol_holding_a_table_value_is_a_copy(
    package: pathlib.Path, source: str, name: str
) -> None:
    """``v0 = 1e-9`` is the vibratory velocity reference typed again."""
    assert [finding.name for finding in _findings(package, source)] == [name]


def test_a_weak_symbol_holding_anything_else_is_left_alone(
    package: pathlib.Path,
) -> None:
    """An area, a frequency and a volume are not references of ISO 1683."""
    assert _findings(package, "_A0 = 10.0\nf0 = 1000.0\nV0 = 50.0\n") == []


def test_the_bare_twenty_micropascal_fails_anywhere(package: pathlib.Path) -> None:
    """The one literal that is never anything but the reference."""
    source = """\
        import numpy as np

        def spl(p):
            return 20 * np.log10(p / 2e-5)
    """
    found = _findings(package, source)
    assert [finding.name for finding in found] == ["2e-05"]


@pytest.mark.parametrize(
    "source",
    [
        "def f(p2):\n    return max(p2, 4e-10)\n",
        "def f(p):\n    return p / (20 * 1e-6)\n",
    ],
)
def test_the_squared_and_the_multiplied_out_twenty_micropascal_fail(
    package: pathlib.Path, source: str
) -> None:
    """``4e-10`` and ``20 * 1e-6`` are the same reference written another way."""
    assert len(_findings(package, source)) == 1


@pytest.mark.parametrize(
    "source",
    [
        "import numpy as np\ndef f(w):\n    return 10 * np.log10(w / 1e-12)\n",
        "import math\ndef f(v):\n    return 20 * math.log10(v / 1e-9)\n",
        "import numpy as np\ndef f(c, f):\n    return np.log10(c * f / 1.0e-12)\n",
        "def f(level):\n    return 10.0 ** (level / 10.0) * 1e-12\n",
        "import numpy as np\n"
        "def f(lv, lf):\n    return np.sqrt(10.0 ** ((lv - lf) / 10.0) * 1.0e-6)\n",
    ],
)
def test_a_table_value_in_the_arithmetic_of_a_level_fails(
    package: pathlib.Path, source: str
) -> None:
    """The divisor inside a logarithm, or the factor of an antilogarithm."""
    assert len(_findings(package, source)) == 1


@pytest.mark.parametrize(
    "source",
    [
        "import numpy as np\ndef f(x):\n    return 10 * np.log10(x + 1e-12)\n",
        "import numpy as np\ndef f(x):\n    return np.log10(np.maximum(x, 1e-12))\n",
        "def f(x):\n    return x * 1e-12\n",
    ],
)
def test_a_floor_or_a_tolerance_is_not_a_reference(
    package: pathlib.Path, source: str
) -> None:
    """``1e-12`` added to a logarithm's argument is a floor, not a reference."""
    assert _findings(package, source) == []


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
    _found, stale = crv.check_tree(package, {("phonometry.module", "gone"): "why"}, {})
    assert stale == ["EXEMPT_LITERALS: phonometry.module.gone"]


def test_an_unused_departure_is_stale(package: pathlib.Path) -> None:
    """A listed departure whose declaration is gone is reported the same way."""
    (package / "module.py").write_text("x = 1\n", encoding="utf-8")
    _found, stale = crv.check_tree(package, {}, _ISO_9611)
    assert stale == ["DIFFERENT_REFERENCES: phonometry.module.REFERENCE_VELOCITY"]


def test_main_fails_on_a_tree_with_a_copy(package: pathlib.Path) -> None:
    """The exit status is what CI reads."""
    (package / "module.py").write_text("_I0 = 1.0e-12\n", encoding="utf-8")
    assert crv.main(["--root", str(package)]) == 1


def test_the_package_is_clean() -> None:
    """The gate itself: every reference in src points at the table or cites."""
    findings, stale = crv.check_tree()
    assert findings == []
    assert stale == []


#: Real declarations and expressions of the tree, each with the number a slip
#: of the keyboard would put in its place: the pointers of this tree, and the
#: two references that used to be written inline in the arithmetic of a level.
_MUTATIONS = [
    (
        "electroacoustics/loudspeaker.py",
        '_P_REF = ISO1683_REFERENCE_VALUES["gas"]["sound_pressure"].value',
        "_P_REF = 2e-6",
    ),
    (
        "building/measurement/structure_borne_power.py",
        'REFERENCE_FORCE: float = ISO1683_REFERENCE_VALUES["solid"]["force"].value',
        "REFERENCE_FORCE: float = 1.0e-5",
    ),
    (
        "underwater/sources/ambient_noise.py",
        '_P_REF = ISO1683_REFERENCE_VALUES["liquid"]["sound_pressure"].value',
        "_P_REF = 1e-5",
    ),
    (
        "noise_control/valves.py",
        '_REFERENCE_SOUND_POWER_W = ISO1683_REFERENCE_VALUES["gas"]["sound_power"]'
        ".value",
        "_REFERENCE_SOUND_POWER_W = 1.0e-11",
    ),
    (
        "vibration/immission/railway.py",
        "VELOCITY_LEVEL_REFERENCE_MM_S: float = 5.0e-5",
        "VELOCITY_LEVEL_REFERENCE_MM_S: float = 5.0e-6",
    ),
    (
        "building/measurement/structure_borne_power.py",
        "* np.sqrt(10.0 ** ((lv - lf) / 10.0) * _MOBILITY_LEVEL_CONSTANT)",
        "* np.sqrt(10.0 ** ((lv - lf) / 10.0) * 1.0e-6)",
    ),
    (
        "building/prediction/installed_structure_borne.py",
        "np.log10(coefficient * f / _FORCE_REFERENCE_SQUARED)",
        "np.log10(coefficient * f / 1.0e-12)",
    ),
]


@pytest.mark.parametrize(("module", "pointer", "typo"), _MUTATIONS)
def test_a_real_reference_with_a_wrong_number_fails(
    package: pathlib.Path, module: str, pointer: str, typo: str
) -> None:
    """The regression the gate exists for, put back into the real modules.

    Every comment is left as it is in the tree, citations included, because
    that is what a slip of the keyboard leaves behind.
    """
    text = (crv.SOURCE / module).read_text(encoding="utf-8")
    assert text.count(pointer) == 1
    path = package / module
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(pointer, typo), encoding="utf-8")
    rows = crv.table_rows(package)
    result = crv.check_file(path, rows, package, {}, crv.DIFFERENT_REFERENCES)
    assert len(result.findings) == 1
