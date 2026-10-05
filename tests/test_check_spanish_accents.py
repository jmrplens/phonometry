#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The Spanish accent gate, held against the entries that made it necessary.

``scripts/check_spanish_accents.py`` exists because twenty-nine entries of the
building-acoustics figures were typed without their accents and eñes and
shipped that way. These tests fix the reading of those entries, of the words
the gate must leave alone (a plural in -ciones, ``lineal``, ``periodo``,
anything inside mathematics), of the tables it reads and of the exemptions it
keeps honest. The glossary the gate also holds is fixed the same way, against
the sentences that shipped «seno» for the waveform and «incertidumbre
extendida» for the GUM's expanded uncertainty.
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
        pages=(),
        figures=(),
    )
    assert len(values) == 2
    assert empty == ["tables.py (_RENAMED)"]


def test_each_table_of_one_file_must_yield_on_its_own(tmp_path: pathlib.Path) -> None:
    """A file with two tables: the one that still yields cannot hide the other."""
    _module(tmp_path, '_ES_EXACT = {"below": "por debajo"}\n')
    _values, empty = csa.read_sources(
        (("tables.py", ("_ES_EXACT",)), ("tables.py", ("_ES_PATTERNS",))),
        root=tmp_path,
        builders=(),
        pages=(),
        figures=(),
    )
    assert empty == ["tables.py (_ES_PATTERNS)"]


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
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=("reports",), pages=(), figures=()
    )
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
    assert csa.unused_contexts(values) == []
    assert len(values) > 5000
    assert any(value.page for value in values)
    assert any(value.script for value in values)
    assert any(value.path.endswith("_es.svg") for value in values)


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("Decimación multitasa", [("Decimación", "Diezmado")]),
        ("sin decimación", [("decimación", "diezmado")]),
        ("a frecuencia decimada", [("decimada", "diezmada")]),
        ("dos decimaciones", [("decimaciones", "diezmados")]),
    ],
)
def test_a_glossary_calque_is_found(text: str, found: list[tuple[str, str]]) -> None:
    """Spanish says diezmado for decimation; the calque shipped once."""
    assert csa.words_needing_marks(text) == found


def _departures(text: str, *, page: bool = False) -> list[tuple[str, str]]:
    """The glossary departures of *text*, without their offsets."""
    return [(w, t) for w, t, _ in csa.glossary_departures(text, page=page)]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        # The excitation paragraph of the transfer-stiffness guide.
        (
            "La fuente puede ser un seno\nescalonado discretamente, un seno "
            "barrido, un seno barrido periódicamente o",
            [("seno", "sinusoide")] * 3,
        ),
        (
            "y un seno por pasos o en barrido debe poner",
            [("seno", "sinusoide")],
        ),
        # The loudness anchor of the BS.1770 diagram.
        (
            "ancla: un seno de 997 Hz a 0 dB FS en un canal frontal marca −3,01 LKFS",
            [("seno", "sinusoide")],
        ),
        (
            "Con un seno de 1 kHz ajustado **7 dB por debajo** del campo",
            [("seno", "sinusoide")],
        ),
        (
            "conservando el factor de cresta de un seno barrido",
            [("seno", "sinusoide")],
        ),
        ("**La excitación, que no es un seno.**", [("seno", "sinusoide")]),
        (
            "Seno de 1 kHz y dos senos de 2 kHz",
            [("Seno", "Sinusoide"), ("senos", "sinusoides")],
        ),
    ],
)
def test_a_waveform_called_seno_is_found(
    text: str, found: list[tuple[str, str]]
) -> None:
    """The sentences that named the waveform after the function."""
    assert _departures(text) == found
    assert _departures(text, page=True) == found


@pytest.mark.parametrize(
    ("text", "found"),
    [
        # The ISO/PAS 20065 fiche, as its table translated it.
        (
            "Incertidumbre extendida U = {u} dB (cobertura del 90 %)",
            [("Incertidumbre extendida", "Incertidumbre expandida")],
        ),
        # A page wraps the phrase at any space.
        (
            "con su incertidumbre\nextendida de medida",
            [("incertidumbre extendida", "incertidumbre expandida")],
        ),
    ],
)
def test_the_extended_uncertainty_calque_is_found(
    text: str, found: list[tuple[str, str]]
) -> None:
    """The GUM's Spanish is «incertidumbre expandida»."""
    assert _departures(text, page=True) == found


def test_the_old_report_table_entry_fails_the_check() -> None:
    """The entry as it shipped in the report renderer's Spanish table."""
    value = csa.Value(
        "src/phonometry/_report/_i18n.py",
        780,
        "Incertidumbre extendida U = {u} dB (cobertura del 90 %)",
    )
    offences, _stale = csa.check([value], allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (780, "Incertidumbre extendida", "Incertidumbre expandida")
    ]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("Canal derecho: barrido senoidal logarítmico", [("senoidal", "sinusoidal")]),
        ("Distorsión por barrido senoidal", [("senoidal", "sinusoidal")]),
        ("una senoide pura", [("senoide", "sinusoide")]),
        # The half-sine of the heavy-impact example, beside its «semisinusoidal».
        ("este semiseno sintético no es una pelota", [("semiseno", "semisinusoide")]),
        ("dos semisenos", [("semisenos", "semisinusoides")]),
        ("varía senoidalmente", [("senoidalmente", "sinusoidalmente")]),
    ],
)
def test_the_adjective_and_the_noun_built_on_seno_are_found(
    text: str, found: list[tuple[str, str]]
) -> None:
    """In a table with the accents, and in a page on their own."""
    assert csa.words_needing_marks(text) == found
    assert _departures(text, page=True) == found


@pytest.mark.parametrize(
    "text",
    [
        # The trigonometric function, in each context the tree writes it.
        "modos separados en el seno del ángulo de lanzamiento",
        "por correlación seno/coseno de las envolventes",
        "el medio paso contiene el coseno y el seno de ks a/2",
        "usa una transformada discreta de\nsenos en profundidad",
        "los argumentos en $\\pi$ de los términos seno impresos",
        "  - El seno lleva $k_{33}$, la componente del número de onda",
        "y seno de theta igual a c tau 0 entre la separación d",
        # The bosom of a medium.
        "una barra delgada en vez de en el seno del material",
        # Words that only contain the letters.
        "el coseno de la fase, la señal y su diseño",
        # The waveform written as the glossary writes it.
        "una sinusoide de 1 kHz, un barrido sinusoidal y la incertidumbre expandida",
    ],
)
def test_the_function_and_the_right_terms_are_left_alone(text: str) -> None:
    """What must never fire, in a table and in a page."""
    assert _departures(text) == []
    assert _departures(text, page=True) == []


def test_mathematics_and_inline_code_are_not_read_in_a_page() -> None:
    """A page blanks its mathematics and its code spans, and nothing else."""
    assert _departures("$\\mathrm{seno}$ y `seno` del código", page=True) == []


def test_a_context_exempts_only_its_own_seno() -> None:
    """The function in a sentence does not let the waveform beside it through."""
    text = "el seno del ángulo y un seno de 1 kHz"
    assert csa.glossary_departures(text) == [("seno", "sinusoide", text.rindex("seno"))]


def test_a_context_that_exempts_nothing_is_reported() -> None:
    """A trigonometric context must keep matching a «seno», like ALLOWED."""
    values = [csa.Value("page.md", 1, "el seno del ángulo de incidencia", page=True)]
    contexts = {
        r"seno\s+del\s+ángulo": "the sine of an angle",
        r"seno\s+de\s+psi": "left behind",
    }
    assert csa.unused_contexts(values, contexts) == [r"seno\s+de\s+psi"]
    offences, _stale = csa.check(values, allowed={}, contexts=contexts)
    assert offences == []


_PAGE = """---
title: "Bucles de inducción"
---

Con un seno de 1 kHz, o la señal combi, y el medidor de valor
eficaz verdadero; la etiqueta `seno` es código.

<ThemeImage src="combi.svg" alt="cada ráfaga de seno de 1 segundo sube a 0 dB" />

```python
combi = 0.4 * signal  # ráfagas de seno a 400 mA/m
```

La regla in situ termina aqui, y el seno del ángulo no es una forma de onda.
"""


def test_a_page_is_read_for_the_glossary_with_its_lines(
    tmp_path: pathlib.Path,
) -> None:
    """Prose, the alternative text of a figure and a code comment, each on its line.

    The accent list is not applied to a page: "aqui" passes there, where it
    would fail in a table.
    """
    (tmp_path / "es").mkdir()
    (tmp_path / "es" / "loops.mdx").write_text(_PAGE, encoding="utf-8")
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=(), pages=("es/**/*.mdx",), figures=()
    )
    assert empty == []
    offences, _stale = csa.check(values, allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (5, "seno", "sinusoide"),
        (8, "seno", "sinusoide"),
        (11, "seno", "sinusoide"),
    ]


def test_a_page_pattern_that_matches_nothing_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """A Spanish edition that moves cannot leave the glossary unread."""
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=(), pages=("es/**/*.mdx",), figures=()
    )
    assert values == []
    assert empty == ["es/**/*.mdx"]


_SCRIPT = """export const home = {
  es: {
    lead: `${domains} dominios`,
    title: 'Para quién mide un seno de 1 kHz',
    cite: `Cita ${DOI} con su incertidumbre extendida`,
  },
};
"""

_COMPONENT = """---
const trimmed = value.replace(/0+$/, '');
const label = 'un seno barrido';
const tail = text.replace(/\\.$/, '');
---
<span>{`+${n} más, un seno`}</span>
"""


def test_a_script_page_is_read_as_written(tmp_path: pathlib.Path) -> None:
    """In JavaScript a dollar and a backtick hide no Spanish.

    The site's data and components are one paragraph after another of
    ``${...}`` substitutions, regular expressions ending in ``$`` and template
    literals: read as Markdown, the strings between two dollars were blanked
    as mathematics and a template literal as code, and the waveform passed.
    """
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "home.ts").write_text(_SCRIPT, encoding="utf-8")
    (tmp_path / "components").mkdir()
    (tmp_path / "components" / "Chips.astro").write_text(_COMPONENT, encoding="utf-8")
    values, empty = csa.read_sources(
        (),
        root=tmp_path,
        builders=(),
        pages=("data/*.ts", "components/**/*.astro"),
        figures=(),
    )
    assert empty == []
    assert all(value.script for value in values)
    offences, _stale = csa.check(values, allowed={})
    assert [(o.value.path.rsplit("/", 1)[-1], o.line, o.word) for o in offences] == [
        ("home.ts", 4, "seno"),
        ("home.ts", 5, "incertidumbre extendida"),
        ("Chips.astro", 3, "seno"),
        ("Chips.astro", 6, "seno"),
    ]


def test_a_markdown_page_still_reads_dollars_as_mathematics() -> None:
    """Only a page that is not Markdown is read as written."""
    text = "el ${}^{3}$He de la tabla, `seno` y $\\mathrm{seno}$ de un seno"
    assert _departures(text, page=True) == [("seno", "sinusoide")]
    found = csa.glossary_departures(text, page=True, script=True)
    assert [word for word, _term, _offset in found] == ["seno"] * 3


_FIGURE = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg">
 <g id="text_1">
  <!-- Barrido exponencial $x(t)$ -->
  <g transform="translate(10 20)"/>
 </g>
 <g id="text_2">
  <!-- Ajuste por modulación de amplitud
con un seno de 1 kHz -->
 </g>
 <g id="text_3">
  <!-- Incertidumbre extendida &lt;U&gt; -->
  <!-- Correccion por ruido de fondo -->
 </g>
</svg>
"""


def test_the_labels_of_a_spanish_figure_are_read(tmp_path: pathlib.Path) -> None:
    """Every string drawn, whatever module wrote it, accents and glossary alike.

    A figure module can draw Spanish of its own, past both translation
    tables (``_wt_text(english, spanish)``); Matplotlib writes each drawn
    string into the SVG as a comment, and that is what is read.
    """
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "rating_es.svg").write_text(_FIGURE, encoding="utf-8")
    (tmp_path / "images" / "rating.svg").write_text(
        _FIGURE.replace("un seno", "a sine"), encoding="utf-8"
    )
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=(), pages=(), figures=("images/*_es.svg",)
    )
    assert empty == []
    assert [value.line for value in values] == [4, 8, 12, 13]
    assert values[2].text == "Incertidumbre extendida <U>"
    offences, _stale = csa.check(values, allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (8, "seno", "sinusoide"),
        (12, "Incertidumbre extendida", "Incertidumbre expandida"),
        (13, "Correccion", "Corrección"),
    ]


def test_a_figure_pattern_that_matches_nothing_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """Spanish figures that move cannot leave their labels unread."""
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=(), pages=(), figures=("images/*_es.svg",)
    )
    assert values == []
    assert empty == ["images/*_es.svg"]
