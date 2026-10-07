#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The Spanish accent gate, held against the entries that made it necessary.

``scripts/check_spanish_accents.py`` exists because twenty-nine entries of the
building-acoustics figures were typed without their accents and eñes and
shipped that way. These tests fix the reading of those entries, of the words
the gate must leave alone (a plural in -ciones, ``lineal``, ``periodo``,
anything inside mathematics), of the tables it reads and of the exemptions it
keeps honest. The glossary the gate also holds is fixed the same way, against
the sentences that shipped «seno» for the waveform, «incertidumbre
extendida» for the GUM's expanded uncertainty, «media cuadrática» and
«cuadrado medio» for the mean square, and «presupuesto» for a budget of
quantities that add up, which the glossary calls a «balance»; and against
the analysis of variance, the one place «cuadrado medio» is right.
"""

from __future__ import annotations

import pathlib
import sys
import time
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


@pytest.mark.parametrize(
    ("text", "found"),
    [
        # The data qualification and programme loudness diagrams.
        (
            "Media cuadrática por intervalo: $N$ = 20 segmentos iguales",
            [("Media cuadrática", "Valor cuadrático medio")],
        ),
        (
            "Media cuadrática en bloques de 400 ms, 75 % de solape",
            [("Media cuadrática", "Valor cuadrático medio")],
        ),
        # The stationarity figure and the level renderer.
        ("Media cuadrática [FS²]", [("Media cuadrática", "Valor cuadrático medio")]),
        (
            "20 medias cuadráticas por segmento; el conteo $A$ de pares",
            [("medias cuadráticas", "valores cuadráticos medios")],
        ),
        # A page wraps the phrase at any space, and an accent can go missing.
        (
            "el procedimiento de estacionariedad por medias\ncuadráticas de segmento",
            [("medias cuadráticas", "valores cuadráticos medios")],
        ),
        ("una media cuadratica", [("media cuadratica", "valor cuadrático medio")]),
    ],
)
def test_a_mean_square_called_media_cuadratica_is_found(
    text: str, found: list[tuple[str, str]]
) -> None:
    """The labels and sentences that named the mean square a quadratic mean."""
    assert _departures(text) == found
    assert _departures(text, page=True) == found


def test_the_old_figure_table_entries_fail_the_check() -> None:
    """The entries as they shipped in the diagram and figure tables."""
    values = [
        csa.Value(
            "scripts/diagrams/i18n.py",
            2424,
            "Media cuadrática por intervalo: $N$ = 20 segmentos iguales",
        ),
        csa.Value("scripts/figures/i18n.py", 2533, "Media cuadrática por segmento"),
    ]
    offences, _stale = csa.check(values, allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (2424, "Media cuadrática", "Valor cuadrático medio"),
        (2533, "Media cuadrática", "Valor cuadrático medio"),
    ]


@pytest.mark.parametrize(
    "text",
    [
        # The quadratic mean, in each context the tree writes it.
        "la media cuadrática de las dos velocidades verdaderas de los extremos",
        "la\n  media cuadrática de los dos valores de los extremos es un número distinto",
        "lo sitúa en la media cuadrática de los extremos",
        "construida exactamente sobre esta media cuadrática y es autoconsistente",
        "así que la media cuadrática supera a la\n  media aritmética, que supera al "
        "valor de media altitud",
        "la media aritmética 323.944 ft largo y la media cuadrática impresa",
        "la parte de tipo B es la media cuadrática de las incertidumbres de cada",
        "las combinaciones\nbinaurales de media cuadrática de la Fórmula 112",
        # The mean square written as the glossary writes it.
        "Valor cuadrático medio por segmento, 20 valores cuadráticos medios",
        "la presión cuadrática media y las presiones cuadráticas medias",
    ],
)
def test_the_quadratic_mean_and_the_right_terms_are_left_alone(text: str) -> None:
    """What must never fire, in a table and in a page."""
    assert _departures(text) == []
    assert _departures(text, page=True) == []


@pytest.mark.parametrize(
    "text",
    [
        # A mean square set against an arithmetic mean, as energy averaging is.
        "la media cuadrática por segmento frente a la media aritmética del registro",
        "La media aritmética de las bandas y la media cuadrática por segmento",
        # A mean square of two values, of the end points or of two speeds.
        "la media cuadrática de los dos valores de presión por banda",
        "la media cuadrática de los extremos del bloque",
        "la media cuadrática de las dos velocidades medidas",
        "sobre esta media cuadrática se calcula el nivel",
    ],
)
def test_a_quadratic_mean_context_holds_only_its_own_sentence(text: str) -> None:
    """The Doc 9911 contexts are its words, not the shapes a mean square takes."""
    found = [("media cuadrática", "valor cuadrático medio")]
    assert _departures(text) == found
    assert _departures(text, page=True) == found


@pytest.mark.parametrize(
    ("text", "found"),
    [
        # The running mean square of the DIN 45672-2 erratum and its guide.
        (
            "es lo que le falta al cuadrado medio móvil",
            [("cuadrado medio", "valor cuadrático medio")],
        ),
        (
            "y eso es lo que le falta al **cuadrado\nmedio**, `e⁻²` y `e⁻⁴`",
            [("cuadrado medio", "valor cuadrático medio")],
        ),
        # The block processing guide, in the plural.
        (
            "(promediar los cuadrados medios de cada bloque)",
            [("cuadrados medios", "valores cuadráticos medios")],
        ),
        # A table cell of the time weighting guide.
        ("Cuadrado medio de $x$", [("Cuadrado medio", "Valor cuadrático medio")]),
    ],
)
def test_a_mean_square_called_cuadrado_medio_is_found(
    text: str, found: list[tuple[str, str]]
) -> None:
    """The statistician's term for the mean square of a signal, ruled out there."""
    assert _departures(text) == found
    assert _departures(text, page=True) == found


_SIGNAL_MEAN_SQUARE = [("cuadrado medio", "valor cuadrático medio")]


@pytest.mark.parametrize(
    ("text", "found"),
    [
        # The time weighting guide as it shipped, beside its degree of freedom.
        (
            "Es una estimación insesgada pero extremadamente ruidosa del cuadrado\n"
            "  medio (un grado de libertad) y, para un tono, depende por completo",
            _SIGNAL_MEAN_SQUARE,
        ),
        # The degrees of freedom of a multitaper estimate.
        (
            "el cuadrado medio promediado acarrea unos $2K$ grados de libertad "
            "chi-cuadrado de un único registro",
            _SIGNAL_MEAN_SQUARE,
        ),
        # What a level accumulates block by block.
        (
            "el cuadrado medio de una grabación no tiene constante de tiempo ni "
            "detector, solo una suma de cuadrados y un recuento de muestras",
            _SIGNAL_MEAN_SQUARE,
        ),
        # The noise a synchronous average leaves.
        (
            "el cuadrado medio del ruido residual cae con el número de promedios",
            _SIGNAL_MEAN_SQUARE,
        ),
        # The mean square error of a filter, which an analysis of variance
        # also writes «cuadrado medio del error».
        ("el cuadrado medio del error del filtro adaptativo", _SIGNAL_MEAN_SQUARE),
        # The definition of an analysis of variance, Montgomery's words
        # (Diseño y análisis de experimentos, 2.ª ed., Limusa Wiley, 2004,
        # PDF page 145, folio 130), which names neither the analysis nor its
        # groups and so is no more than a signal could say.
        (
            "Cada suma de cuadrados dividida por sus grados de libertad es un "
            "cuadrado medio.",
            _SIGNAL_MEAN_SQUARE,
        ),
        # A residual mean square with no degrees of freedom beside it, the
        # error an adaptive canceller leaves.
        (
            "el cuadrado medio residual del cancelador adaptativo",
            _SIGNAL_MEAN_SQUARE,
        ),
        # A round robin and an acoustic treatment compare too.
        (
            "los cuadrados medios de la presión medidos entre laboratorios",
            [("cuadrados medios", "valores cuadráticos medios")],
        ),
        (
            "el cuadrado medio de la presión cambia entre tratamientos del techo",
            _SIGNAL_MEAN_SQUARE,
        ),
        # The ECMA-418-2 loudness guide recalculates its bands «entre grupos»
        # (the advanced loudness guide, at its 0,9845 sone_HMS anchor), and a
        # guide splits machines or bands into groups: groups that do not
        # qualify the term are a signal's.
        (
            "Sin ningún promediado de bandas la cadena da 0,955; y con el "
            "cuadrado medio de bloque recalculado entre grupos que exige la "
            "norma, 0,9845.",
            _SIGNAL_MEAN_SQUARE,
        ),
        (
            "con el recálculo completo entre grupos que exige la norma, el "
            "cuadrado medio de cada banda se promedia",
            _SIGNAL_MEAN_SQUARE,
        ),
        (
            "el cuadrado medio de la vibración dentro de los grupos de máquinas "
            "más cercanos domina la suma",
            _SIGNAL_MEAN_SQUARE,
        ),
        ("el cuadrado medio entre grupos de bandas", _SIGNAL_MEAN_SQUARE),
    ],
)
def test_a_signal_mean_square_fails_beside_the_words_an_anova_shares(
    text: str, found: list[tuple[str, str]]
) -> None:
    """Words an analysis of variance shares with a signal do not make one.

    Each sentence holds a word of the analysis that the mean square of a
    signal takes as well (degrees of freedom, a sum of squares, a residual,
    groups), and so the term in it is the signal's and fails.
    """
    assert _departures(text) == found
    assert _departures(text, page=True) == found


@pytest.mark.parametrize(
    "text",
    [
        # A full stop, also closed in emphasis.
        "El análisis de la varianza viene en el apartado 7. El cuadrado "
        "medio de la señal se integra con la constante de tiempo.",
        "como en un **ANOVA.** El cuadrado medio de la señal se integra",
        # A colon, a semicolon, a question mark and an exclamation mark.
        "Véase el ANOVA: el cuadrado medio de la señal se integra",
        "Véase el ANOVA; el cuadrado medio de la señal se integra",
        "¿Es un ANOVA? El cuadrado medio de la señal se integra",
        "¡No es un ANOVA! El cuadrado medio de la señal se integra",
        # An item of a list and a heading, which carry no stop.
        "- ANOVA en el anexo\n- el cuadrado medio de la presión con ponderación A",
        "- Cuadro del análisis de la varianza\n* el cuadrado medio de la señal",
        "1. ANOVA en el anexo\n2) el cuadrado medio de la presión",
        "### Análisis de la varianza\nEl cuadrado medio de la señal es su potencia.",
    ],
)
def test_an_analysis_named_in_another_sentence_exempts_nothing(text: str) -> None:
    """The analysis exempts the term only in the sentence that names it."""
    assert _departures(text) == _SIGNAL_MEAN_SQUARE
    assert _departures(text, page=True) == _SIGNAL_MEAN_SQUARE


@pytest.mark.parametrize(
    "text",
    [
        # Montgomery's one-factor table (PDF page 86, folio 71), with groups
        # for the treatments he compares.
        "Observe que el cuadrado medio entre grupos (118,94) es varias veces "
        "mayor que el cuadrado medio dentro de los grupos o cuadrado medio del "
        "error (8,06).",
        # The analysis named, without the article and with it.
        "En la tabla se resume el análisis de varianza, y el cuadrado medio de "
        "cada fuente es su suma de cuadrados dividida por sus grados de libertad",
        "Cada suma de cuadrados dividida por sus grados de libertad es un "
        "cuadrado medio del análisis de la varianza.",
        # The acronym and the plural.
        "Los cuadrados medios del ANOVA de la Tabla 2",
        # The mean square named by its row, without the article and with it,
        # and the residual one beside its degrees of freedom.
        "el cuadrado medio entre grupos vale 3,2",
        "los cuadrados medios entre los grupos y residual",
        "El cuadrado medio residual vale 8,06 con 20 grados de libertad.",
        # A page wraps the term and its row, and so does an item of a list.
        "el cuadrado\nmedio dentro de los grupos estima la varianza de repetibilidad",
        "- el cuadrado medio dentro de los\n  grupos estima la repetibilidad",
        # The analysis named before the colon of a designation or the point
        # of a number, and the term after it.
        "En el ANOVA el valor 118.94 es el cuadrado medio de la tabla",
        "El ANOVA de ISO 5725-2:1994 da el cuadrado medio de la tabla",
    ],
)
def test_a_mean_square_of_an_analysis_of_variance_is_left_alone(text: str) -> None:
    """The statistician's term, in a sentence that names the analysis or its row."""
    assert _departures(text) == []
    assert _departures(text, page=True) == []


#: Montgomery's Table 3-4 (Diseño y análisis de experimentos, 2.ª ed., Limusa
#: Wiley, 2004, PDF page 86, folio 71) as printed, whose rows name neither the
#: analysis nor its groups: only the header says what the table is.
_MONTGOMERY_TABLE = (
    "| Fuente de variación | Suma de cuadrados | Grados de libertad "
    "| Cuadrado medio | $F_0$ | Valor $P$ |\n"
    "|---|---|---|---|---|---|\n"
    "| Peso porcentual del algodón | 475.76 | 4 | 118.94 | $F_0$=14.76 | <0.01 |\n"
    "| Error | 161.20 | 20 | 8.06 | | |\n"
    "| Total | 636.96 | 24 | | | |"
)


@pytest.mark.parametrize(
    ("table", "found"),
    [
        (_MONTGOMERY_TABLE, []),
        # The same header over a comparison of laboratories.
        (
            "| Fuente | Suma de cuadrados | Grados de libertad | Cuadrado medio |\n"
            "|---|---|---|---|\n"
            "| Entre laboratorios | 475,76 | 4 | 118,94 |\n"
            "| Residual | 161,20 | 20 | 8,06 |",
            [],
        ),
        # A table of a signal, with the degrees of freedom of each band but no
        # sum of squares.
        (
            "| Banda | Cuadrado medio | Grados de libertad |\n"
            "|---|---|---|\n"
            "| 1 kHz | 0,2 | 2 |",
            [("Cuadrado medio", "Valor cuadrático medio")],
        ),
    ],
)
def test_a_table_is_one_of_an_analysis_of_variance_by_its_header(
    table: str, found: list[tuple[str, str]]
) -> None:
    """A sum of squares, its degrees of freedom and their mean square, side by side."""
    assert _departures(table, page=True) == found


@pytest.mark.parametrize(
    "text",
    [
        _MONTGOMERY_TABLE + "\nEl cuadrado medio de la señal se mide en Pa².",
        "El cuadrado medio de la señal se mide en Pa²\n" + _MONTGOMERY_TABLE,
    ],
)
def test_a_table_of_an_analysis_of_variance_exempts_no_prose_beside_it(
    text: str,
) -> None:
    """Prose written against a table, with no blank line, is a sentence apart."""
    assert _departures(text, page=True) == [
        ("cuadrado medio", "valor cuadrático medio")
    ]


def test_a_long_run_without_a_stop_is_read_in_linear_time() -> None:
    """The sentence of a term is cut once, not tried from every character.

    A 20 kB table with one «cuadrado medio» and no stop took about forty
    seconds while each context was a pattern spanning its sentence, since the
    pattern was tried again from every character before it.
    """
    table = "| Cuadrado medio |" + " 0,5 |" * 4_000
    start = time.perf_counter()
    found = _departures(table, page=True)
    assert time.perf_counter() - start < 2.0
    assert found == [("Cuadrado medio", "Valor cuadrático medio")]


def test_an_analysis_of_variance_exempts_only_its_own_term() -> None:
    """A sentence of the analysis lets no waveform, quadratic mean or budget through."""
    text = (
        "En el análisis de la varianza, un seno de 1 kHz, la media cuadrática "
        "por segmento, un presupuesto de ruido y el cuadrado medio entre grupos"
    )
    assert _departures(text) == [
        ("seno", "sinusoide"),
        ("media cuadrática", "valor cuadrático medio"),
        ("presupuesto", "balance"),
    ]


def test_the_vocabulary_of_an_analysis_of_variance_never_goes_stale(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No sentence of the tree is an analysis of variance, and none has to be.

    The contexts of the analysis are its vocabulary, not the words of one
    sentence each, so they are left out of the contexts that must keep
    matching, and a run that meets a signal's «cuadrado medio» sends the
    author to the analysis, not to a stale table.
    """
    assert set(csa.ANALYSIS_OF_VARIANCE).isdisjoint(csa.CONTEXTS)
    value = csa.Value("page.md", 1, "el cuadrado medio de la señal", page=True)
    assert set(csa.ANALYSIS_OF_VARIANCE).isdisjoint(csa.unused_contexts([value]))
    monkeypatch.setattr(csa, "read_sources", lambda: ([value], []))
    assert csa.main([]) == 1
    out = capsys.readouterr().out
    assert "'cuadrado medio' is written 'valor cuadrático medio'" in out
    assert "a sentence of an analysis of variance (ANALYSIS_OF_VARIANCE)" in out
    assert "any other label of the analysis goes in ALLOWED" in out
    assert "ANALYSIS_OF_VARIANCE lists" not in out


_ANOVA_PAGE = """---
title: "Precisión de un método de medida"
---

En el análisis de la varianza de la Tabla 2, el cuadrado medio entre grupos
es varias veces mayor que el cuadrado medio dentro de los grupos.

| Fuente de variación | Suma de cuadrados | Grados de libertad | Cuadrado medio |
|---|---|---|---|
| Entre grupos | 475,76 | 4 | 118,94 |
| Dentro de los grupos | 161,20 | 20 | 8,06 |

El nivel del registro sale del cuadrado medio de la presión, que la
ponderación temporal integra con su constante de tiempo.
"""


def test_a_page_keeps_its_analysis_of_variance_and_loses_its_signal(
    tmp_path: pathlib.Path,
) -> None:
    """The prose and the table of the analysis pass; the signal's term fails."""
    (tmp_path / "es").mkdir()
    (tmp_path / "es" / "precision.md").write_text(_ANOVA_PAGE, encoding="utf-8")
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=(), pages=("es/*.md",), figures=()
    )
    assert empty == []
    offences, _stale = csa.check(values, allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (13, "cuadrado medio", "valor cuadrático medio")
    ]


def test_a_label_of_an_analysis_of_variance_goes_in_allowed() -> None:
    """A label that names neither the analysis nor its row passes by ALLOWED."""
    value = csa.Value("scripts/figures/i18n.py", 12, "Cuadrado medio")
    offences, _stale = csa.check([value], allowed={})
    assert [(o.word, o.spelling) for o in offences] == [
        ("Cuadrado medio", "Valor cuadrático medio")
    ]
    allowed = {("Cuadrado medio", "Cuadrado medio"): "a column of an ANOVA table"}
    assert csa.check([value], allowed=allowed) == ([], [])


def test_a_context_exempts_only_its_own_quadratic_mean() -> None:
    """The quadratic mean in a sentence does not let the mean square through."""
    text = "la media cuadrática de las incertidumbres y la media cuadrática por banda"
    assert csa.glossary_departures(text) == [
        ("media cuadrática", "valor cuadrático medio", text.rindex("media"))
    ]


def test_a_quadratic_mean_context_that_exempts_nothing_is_reported() -> None:
    """A context of the quadratic mean must keep matching, like a «seno» one."""
    values = [csa.Value("page.md", 1, "la media cuadrática de las incertidumbres")]
    unused = csa.unused_contexts(values)
    assert r"(?<!\w)binaurales\s+de\s+media\s+cuadrática(?!\w)" in unused
    assert r"(?<!\w)media\s+cuadrática\s+de\s+las\s+incertidumbres(?!\w)" not in unused
    assert set(csa.TRIGONOMETRIC) <= set(unused)


def test_a_stale_context_is_reported_under_its_own_table(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The report names the table a stale context sits in, and its term."""
    values = [csa.Value("page.md", 1, "el seno del ángulo de incidencia", page=True)]
    monkeypatch.setattr(csa, "read_sources", lambda: (values, []))
    assert csa.main([]) == 1
    out = capsys.readouterr().out
    assert "::error::QUADRATIC_MEAN lists" in out
    assert "which no longer exempts any «media cuadrática»" in out
    assert "::error::TRIGONOMETRIC lists" in out
    assert r"seno\s+del\s+ángulo" not in out


@pytest.mark.parametrize(
    ("text", "found"),
    [
        # The opening line of the noise-control overview.
        (
            "Un problema de control de ruido es un **presupuesto**, no una elección de",
            [("presupuesto", "balance")],
        ),
        # The spectral analysis guide and the intensity references.
        (
            "El **sesgo de resolución** es la otra mitad del presupuesto de error: un",
            [("presupuesto", "balance")],
        ),
        (
            "intensidad activa y reactiva, el estimador p-p y el presupuesto de "
            "error por desfase que hay detrás de esta página.",
            [("presupuesto", "balance")],
        ),
        # The absorption guide, wrapped where the page wrapped it.
        (
            "entra en una estimación de Sabine, en un\npresupuesto de absorción "
            "EN 12354-6 o en el pliego de un concurso",
            [("presupuesto", "balance")],
        ),
        # The verb, at the start of a sentence of the enclosure caption.
        (
            "y un interior duro sin revestir costaría mucho más. Presupuesta\n"
            "el revestimiento junto con los paneles",
            [("Presupuesta", csa.REWORD_PREFIX + "«balance»")],
        ),
        # The same instruction worded as an impersonal or with a pronoun,
        # where the stem carries its written accent.
        (
            "Presupuéstese el revestimiento junto con los paneles.",
            [("Presupuéstese", csa.REWORD_PREFIX + "«balance»")],
        ),
        (
            "presupuéstalo antes de cotizar",
            [("presupuéstalo", csa.REWORD_PREFIX + "«balance»")],
        ),
        ("PRESUPUÉSTALO", [("PRESUPUÉSTALO", csa.REWORD_PREFIX + "«balance»")]),
        # The plural, and the rest of the family.
        ("dos presupuestos de ruido", [("presupuestos", "balances")]),
        (
            "Presupuesto de ruido presupuestado y presupuestario",
            [
                ("Presupuesto", "Balance"),
                ("presupuestado", csa.REWORD_PREFIX + "«balance»"),
                ("presupuestario", csa.REWORD_PREFIX + "«balance»"),
            ],
        ),
    ],
)
def test_a_budget_called_presupuesto_is_found(
    text: str, found: list[tuple[str, str]]
) -> None:
    """The sentences that named a budget of summed quantities after money."""
    assert _departures(text) == found
    assert _departures(text, page=True) == found


def test_a_form_that_is_not_a_noun_is_told_to_reword(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A verb or an adjective of the family gets a rewording, not «balance»."""
    value = csa.Value("site/x.mdx", 3, "Presupuéstese el revestimiento.")
    offences, _stale = csa.check([value], allowed={})
    assert [(o.word, o.spelling) for o in offences] == [
        ("Presupuéstese", "reword around «balance»")
    ]
    monkeypatch.setattr(csa, "read_sources", lambda: ([value], []))
    assert csa.main([]) == 1
    out = capsys.readouterr().out
    assert "'Presupuéstese' reword around «balance»" in out
    assert "is written 'reword" not in out


def test_the_old_diagram_table_entry_fails_the_check() -> None:
    """The decay-range title as it sat in the diagram table."""
    value = csa.Value(
        "scripts/diagrams/i18n.py",
        2879,
        "El presupuesto de rango de caída de una banda: INR, truncamiento y "
        "ventanas de evaluación (ISO 3382)",
    )
    offences, _stale = csa.check([value], allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (2879, "presupuesto", "balance")
    ]


@pytest.mark.parametrize(
    "text",
    [
        # The budget written as the glossary writes it.
        "el balance de incertidumbre de la Tabla D.2 y dos balances de error",
        "Un problema de control de ruido es un **balance**, no una elección",
        "el balance de absorción EN 12354-6 y el balance de ruido de válvula",
        # Words that share letters with the family and are not in it.
        "el modelo presupone una capa infinita, por supuesto, y lo supuesto",
    ],
)
def test_a_balance_and_its_neighbours_are_left_alone(text: str) -> None:
    """What must never fire, in a table and in a page."""
    assert _departures(text) == []
    assert _departures(text, page=True) == []


_IDENTIFIERS = """Con el balance de ruido:

```python
presupuesto_ruido = balance(3)
presupuesto2 = 3
mi_presupuesto = presupuesto_ruido + presupuesto2
```
"""


def test_an_identifier_built_on_presupuesto_is_not_prose() -> None:
    """A token with an underscore or a digit is code, wherever the word sits in it.

    The rest of the gate skips such a token whole (``numero_bandas`` is not a
    misspelt ``número``), so the family of «presupuesto» does too, whether
    the word opens the identifier or closes it.
    """
    assert _departures(_IDENTIFIERS) == []
    assert _departures(_IDENTIFIERS, page=True) == []
    assert _departures("el presupuesto_ruido y su presupuesto", page=True) == [
        ("presupuesto", "balance")
    ]


_PREMISE = "los presupuestos teóricos del modelo de Sabine no valen aquí"


def test_a_premise_is_not_money_and_takes_its_exemption_from_allowed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A premise fails like a budget, and the report says to reword it.

    The check cannot tell a premise from a budget, so it fails; the hint
    sends the author to «supuesto» rather than «balance», and a sentence that
    must keep the word is exempted in ALLOWED, never in MONEY.
    """
    value = csa.Value("page.md", 1, _PREMISE, page=True)
    offences, _stale = csa.check([value], allowed={})
    assert [(o.word, o.spelling) for o in offences] == [("presupuestos", "balances")]
    offences, stale = csa.check(
        [value], allowed={(_PREMISE, "presupuestos"): "a premise of the model"}
    )
    assert offences == []
    assert stale == []
    monkeypatch.setattr(csa, "read_sources", lambda: ([value], []))
    assert csa.main([]) == 1
    out = capsys.readouterr().out
    assert "premise is reworded («supuesto», «hipótesis»)" in out


_SIDEBAR = """// Auto-generated by scripts/generate_api_docs.py (make api-docs).
export const apiSections = {
  'signals': {
    label: 'Signal analysis',
    translations: { es: 'Análisis de señal' },
  },
  'noise': {
    label: 'Noise budget',
    translations: { es: 'Presupuesto de ruido' },
  },
};
"""


def test_a_generated_module_of_the_site_is_read(tmp_path: pathlib.Path) -> None:
    """The Spanish labels of the API sidebar are read as the site imports them.

    They are written from ``scripts/api_taxonomy.py`` into a generated module
    that no other source of the check reaches.
    """
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "api-sidebar.mjs").write_text(_SIDEBAR, encoding="utf-8")
    values, empty = csa.read_sources(
        (), root=tmp_path, builders=(), pages=("generated/*.mjs",), figures=()
    )
    assert empty == []
    assert all(value.script for value in values)
    offences, _stale = csa.check(values, allowed={})
    assert [(o.line, o.word, o.spelling) for o in offences] == [
        (9, "Presupuesto", "Balance")
    ]


def test_the_generated_api_sidebar_is_among_the_pages() -> None:
    """The committed sidebar is read, so its Spanish labels hold the glossary."""
    assert "site/src/generated/*.mjs" in csa.PAGES
    values, _empty = csa.read_sources()
    assert any(
        value.path == "site/src/generated/api-sidebar.mjs" and "es:" in value.text
        for value in values
    )


_MONEY = {
    r"(?<!\w)presupuesto\s+del\s+proyecto(?!\w)": "the money a project is given",
}


def test_a_money_context_exempts_only_its_own_presupuesto() -> None:
    """Money in a sentence does not let the budget of decibels beside it through."""
    text = "el presupuesto del proyecto no cubre el presupuesto de ruido"
    assert csa.glossary_departures(text, contexts=_MONEY) == [
        ("presupuesto", "balance", text.rindex("presupuesto"))
    ]


def test_a_money_context_that_exempts_nothing_is_reported() -> None:
    """A money context must keep matching a «presupuesto», as a «seno» one must."""
    values = [csa.Value("page.md", 1, "el presupuesto del proyecto", page=True)]
    contexts = {**_MONEY, r"presupuesto\s+de\s+obra": "left behind"}
    assert csa.unused_contexts(values, contexts) == [r"presupuesto\s+de\s+obra"]
    offences, _stale = csa.check(values, allowed={}, contexts=contexts)
    assert offences == []


def test_a_stale_money_context_is_reported_under_its_own_table(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The report names MONEY and the term when a money context goes stale."""
    pattern = r"(?<!\w)presupuesto\s+de\s+obra(?!\w)"
    monkeypatch.setitem(csa.MONEY, pattern, "left behind")
    monkeypatch.setitem(csa.CONTEXTS, pattern, "left behind")
    values = [csa.Value("page.md", 1, "un balance de ruido", page=True)]
    monkeypatch.setattr(csa, "read_sources", lambda: (values, []))
    assert csa.main([]) == 1
    out = capsys.readouterr().out
    assert f"::error::MONEY lists {pattern!r}" in out
    assert "which no longer exempts any «presupuesto»" in out


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
