#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The Spanish accent gate, held against the entries that made it necessary.

``scripts/check_spanish_accents.py`` exists because twenty-nine entries of the
building-acoustics figures were typed without their accents and eñes and
shipped that way. These tests fix the reading of those entries, of the words
the gate must leave alone (a plural in -ciones, ``lineal``, ``periodo``,
anything inside mathematics), of the tables it reads and of the exemptions it
keeps honest.
"""

from __future__ import annotations

import pathlib
import sys
import unicodedata

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_spanish_accents as csa


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "limite de medicion\n(1,3 dB fijos, senalar la banda)",
            [("limite", "límite"), ("medicion", "medición"), ("senalar", "señalar")],
        ),
        ("la regla in situ termina aqui", [("aqui", "aquí")]),
        (
            "Correccion aplicada, $L_\\mathrm{sb} - L$ [dB]",
            [("Correccion", "Corrección")],
        ),
        (
            "Margen senal-fondo $L_\\mathrm{sb} - L_\\mathrm{b}$ [dB]",
            [("senal", "señal")],
        ),
        ("Numero global [dB]", [("Numero", "Número")]),
        ("El mismo indice ponderado", [("indice", "índice")]),
        (
            "despues absorcion en el recinto",
            [("despues", "después"), ("absorcion", "absorción")],
        ),
        ("hormigon denso de 150 mm", [("hormigon", "hormigón")]),
        (
            "una conexion rigida y la region lejana",
            [("conexion", "conexión"), ("rigida", "rígida"), ("region", "región")],
        ),
        ("el nivel acustico maximo", [("acustico", "acústico"), ("maximo", "máximo")]),
    ],
)
def test_the_words_that_shipped_without_their_marks_are_found(
    text: str, expected: list[tuple[str, str]]
) -> None:
    """The entries the gate was written for, with the spelling each one needs."""
    assert csa.words_needing_marks(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        # Plurals in -ciones, -siones and -xiones carry no accent.
        "correcciones, mediciones, transmisiones y conexiones",
        # Correct as written.
        "respuesta lineal",
        "el periodo de la señal y sus periodos",
        "un guion bajo",
        # Correct because the accent is there.
        "límite de medición (1,3 dB fijos, señalar la banda)",
        "la regla in situ termina aquí, después de la corrección",
        # Mathematics is not prose.
        "$L_\\mathrm{limite}$ y $\\mathrm{medicion}$",
        # A placeholder, an identifier and markup are not prose either.
        "{numero} bandas, numero_bandas, area2 y <limite>",
        "la etiqueta `medicion` del código",
        # A form a verb can take, and a monosyllable a list cannot decide.
        "si la banda continua y esta practica se publica",
    ],
)
def test_correct_spanish_is_left_alone(text: str) -> None:
    """What must never fire, whatever the list grows into."""
    assert csa.words_needing_marks(text) == []


def test_an_escaped_dollar_does_not_open_mathematics() -> None:
    """A literal dollar leaves the prose after it readable."""
    assert csa.words_needing_marks("10 \\$ por metro de linea") == [("linea", "línea")]


def _strip_marks(text: str) -> str:
    """*text* without its accents, diaeresis and the tilde of the eñe."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def test_every_listed_spelling_only_restores_the_marks() -> None:
    """The list maps a word to itself with its marks, never to another word."""
    for bare, spelt in csa.NEEDS_MARK.items():
        assert bare == bare.lower()
        assert spelt != bare
        assert _strip_marks(spelt) == bare


_TABLES = """
_ES_EXACT = {
    "the field rule stops here": "la regla in situ termina aqui",
    "limit": "límite",
    **_OTHER,
}
_ES_PATTERNS = [
    (r"^(\\d+) dB below$", r"\\1 dB por debajo del limite"),
]
_NOT_A_TABLE = {"aqui": "aqui"}


def label(language):
    title = "Correccion" if language == "es" else "Correction"
    if language == "es":
        note = "senal"
    else:
        note = "medicion"
    return title, note
"""


def _module(tmp_path: pathlib.Path, text: str = _TABLES) -> pathlib.Path:
    path = tmp_path / "tables.py"
    path.write_text(text, encoding="utf-8")
    return path


def test_the_values_of_the_named_tables_are_read(tmp_path: pathlib.Path) -> None:
    """Dictionary values and pattern replacements, never the English keys."""
    path = _module(tmp_path)
    values = csa.spanish_values(path, ("_ES_EXACT", "_ES_PATTERNS"))
    assert [v.text for v in values] == [
        "la regla in situ termina aqui",
        "límite",
        "\\1 dB por debajo del limite",
    ]
    assert [v.line for v in values] == [3, 4, 8]


def test_the_spanish_branch_of_a_renderer_is_read(tmp_path: pathlib.Path) -> None:
    """Only the ``== "es"`` side, in an expression and in a statement."""
    path = _module(tmp_path)
    texts = [v.text for v in csa.spanish_values(path, (), branches=True)]
    assert texts == ["Correccion", "senal"]


def test_a_renamed_table_empties_no_gate_silently(tmp_path: pathlib.Path) -> None:
    """A source that yields nothing is reported, not passed."""
    _module(tmp_path)
    values, empty = csa.read_sources(
        (("tables.py", ("_ES_EXACT",)), ("tables.py", ("_RENAMED",))),
        root=tmp_path,
        builders=(),
    )
    assert len(values) == 2
    assert empty == ["tables.py"]


_BUILDERS = """
def _spanish_example():
    \"\"\"A docstring is not printed: the medicion here is never read.\"\"\"
    metadata = ReportMetadata(test_room="punto de evaluacion", client="Example client")
    return result, metadata, "spanish.pdf", {"language": "es"}


def _spanish_call_example():
    return render(result, language="es", title="Maquina ruidosa activa")


def _english_example():
    metadata = ReportMetadata(notes="Transmission and precision of the version")
    return result, metadata, "english.pdf"
"""


def test_a_builder_that_asks_for_spanish_is_read(tmp_path: pathlib.Path) -> None:
    """Both ways of naming the language, the docstring left out."""
    path = tmp_path / "builders.py"
    path.write_text(_BUILDERS, encoding="utf-8")
    texts = [v.text for v in csa.builder_values(path)]
    assert "punto de evaluacion" in texts
    assert "Maquina ruidosa activa" in texts
    assert not any("medicion" in text for text in texts)
    assert not any("Transmission" in text for text in texts)
    offences, _stale = csa.check(csa.builder_values(path), allowed={})
    assert [o.word for o in offences] == ["evaluacion", "Maquina"]


def test_a_builder_directory_without_spanish_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """A Spanish fiche that stops naming its language cannot leave silently."""
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "english.py").write_text(
        "def _example():\n    return 1, 2, 'x.pdf'\n", encoding="utf-8"
    )
    values, empty = csa.read_sources((), root=tmp_path, builders=("reports",))
    assert values == []
    assert empty == ["reports"]


def test_the_report_names_file_line_word_and_spelling(tmp_path: pathlib.Path) -> None:
    """What CI prints comes from these fields."""
    path = _module(tmp_path)
    offences, stale = csa.check(csa.spanish_values(path, ("_ES_EXACT",)), allowed={})
    assert [(o.value.line, o.word, o.spelling) for o in offences] == [
        (3, "aqui", "aquí")
    ]
    assert stale == []


def test_an_allowed_verb_is_exempt_and_a_stale_exemption_fails() -> None:
    """The escape hatch covers one word of one value and must keep matching."""
    verb = csa.Value("tables.py", 1, "que limite la banda")
    allowed = {
        ("que limite la banda", "limite"): "subjunctive of limitar",
        ("un valor que ya no existe", "numero"): "left behind",
    }
    offences, stale = csa.check([verb], allowed=allowed)
    assert offences == []
    assert stale == [("un valor que ya no existe", "numero")]


def test_an_exemption_covers_only_its_own_word() -> None:
    """Allowing the verb does not let a second defect in the same value through."""
    value = csa.Value("tables.py", 1, "que limite la medicion")
    offences, _stale = csa.check([value], allowed={(value.text, "limite"): "verb"})
    assert [o.word for o in offences] == ["medicion"]


def test_the_published_tables_carry_every_accent() -> None:
    """The tables as committed: every source found, nothing flagged, nothing stale."""
    values, empty = csa.read_sources()
    offences, stale = csa.check(values)
    assert empty == []
    assert offences == []
    assert stale == []
    assert len(values) > 5000
