#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Refuse a Spanish label written without its accent or its eñe.

Every Spanish word the figures, the diagrams and the library's own renderers
draw comes out of a translation table, and a table entry typed on a keyboard
without the Spanish layout reads fine to every other gate: the language gate
sees a translated string, the parity check sees a pair, and the figure matches
its generator. Twenty-nine entries of the building-acoustics figures shipped
that way ("Correccion por ruido de fondo", "limite de medicion (1,3 dB fijos,
senalar la banda)", "la regla in situ termina aqui") with every gate green.

A spelling check proper would need a dictionary, and a dictionary is exactly
what cannot tell ``limite`` the verb from ``límite`` the noun. So the rule is
narrower and certain: :data:`NEEDS_MARK` lists the unaccented forms that are
never correct Spanish in this corpus, each with the spelling it stands for,
and :data:`_SINGULAR_ION` adds the one family no list can enumerate, the
singulars in -ción, -sión, -xión and -gión written as -cion, -sion, -xion and
-gion. A plural in -ciones, ``lineal``, ``periodo`` (the Real Academia
accepts it with and without the accent) and anything inside ``$...$`` are
not read.

A few listed forms are also a verb, and a sentence may one day need the verb:
``limite`` in "que limite la banda", ``numero`` in "numero las filas". That
case goes in :data:`ALLOWED`, keyed by the Spanish value and the word, with
the reason. An entry whose value has left the tables, or no longer carries
the word, fails, so the list cannot outlive its reason.

The tables are read as source, not imported, so the check needs nothing but
the standard library and runs before anything is installed.

Usage::

    python scripts/check_spanish_accents.py

Exit status 0 when every Spanish value is clean, 1 otherwise, naming the file,
the line, the word and its spelling.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Where the Spanish lives, and the names its tables are bound to. A directory
#: is read file by file, and in the library the body of a ``language == "es"``
#: branch is read too, since a renderer writes its few one-off Spanish strings
#: there instead of in its ``_STRINGS`` table. Every entry must yield at least
#: one value: a table that has been renamed would otherwise empty the gate
#: without a word.
SOURCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("scripts/figures/i18n.py", ("_ES_EXACT", "_ES_PATTERNS")),
    ("scripts/diagrams/i18n.py", ("_ES",)),
    ("src/phonometry/_plot", ("_STRINGS",)),
    ("src/phonometry/_report", ("_STRINGS",)),
)

#: Unaccented forms that are never correct Spanish in this corpus, with the
#: spelling each one stands for. Only a form that is not also a common word
#: belongs here: ``esta``, ``solo``, ``mas``, ``aun``, ``si``, ``continua``,
#: ``practica``, ``publica``, ``valida`` and ``especifica`` are all correct
#: Spanish as written, and the context that decides them is beyond a list. The
#: handful kept here that a verb can also spell (``limite``, ``numero``,
#: ``termino``, ``calculo``, ``critica``, ``formula``, ``maquina``, ``modulo``,
#: ``trafico``, ...) are nouns and adjectives everywhere in the tables, and
#: the verb, when it comes, is what :data:`ALLOWED` is for.
NEEDS_MARK: dict[str, str] = {
    # Adverbs and the words a sentence is built with.
    "aqui": "aquí",
    "alli": "allí",
    "ahi": "ahí",
    "asi": "así",
    "ademas": "además",
    "tambien": "también",
    "despues": "después",
    "segun": "según",
    "atras": "atrás",
    "detras": "detrás",
    "traves": "través",
    "podria": "podría",
    "deberia": "debería",
    "habria": "habría",
    "tendria": "tendría",
    # The eñe.
    "senal": "señal",
    "senales": "señales",
    "senalar": "señalar",
    "senala": "señala",
    "senalan": "señalan",
    "senalado": "señalado",
    "senalada": "señalada",
    "senalados": "señalados",
    "senaladas": "señaladas",
    "diseno": "diseño",
    "disenos": "diseños",
    "disenado": "diseñado",
    "disenada": "diseñada",
    "tamano": "tamaño",
    "tamanos": "tamaños",
    "pequeno": "pequeño",
    "pequena": "pequeña",
    "pequenos": "pequeños",
    "pequenas": "pequeñas",
    "espana": "España",
    "espanol": "español",
    "espanola": "española",
    # Nouns.
    "limite": "límite",
    "limites": "límites",
    "numero": "número",
    "numeros": "números",
    "indice": "índice",
    "indices": "índices",
    "metodo": "método",
    "metodos": "métodos",
    "parametro": "parámetro",
    "parametros": "parámetros",
    "diametro": "diámetro",
    "diametros": "diámetros",
    "perimetro": "perímetro",
    "analisis": "análisis",
    "caracteristica": "característica",
    "caracteristicas": "características",
    "caracteristico": "característico",
    "caracteristicos": "característicos",
    "decada": "década",
    "decadas": "décadas",
    "angulo": "ángulo",
    "angulos": "ángulos",
    "pagina": "página",
    "paginas": "páginas",
    "linea": "línea",
    "lineas": "líneas",
    "area": "área",
    "areas": "áreas",
    "energia": "energía",
    "geometria": "geometría",
    "teoria": "teoría",
    "categoria": "categoría",
    "categorias": "categorías",
    "metodologia": "metodología",
    "tecnologia": "tecnología",
    "bibliografia": "bibliografía",
    "garantia": "garantía",
    "caida": "caída",
    "caidas": "caídas",
    "raiz": "raíz",
    "oido": "oído",
    "oidos": "oídos",
    "termino": "término",
    "terminos": "términos",
    "calculo": "cálculo",
    "calculos": "cálculos",
    "formula": "fórmula",
    "formulas": "fórmulas",
    "circulo": "círculo",
    "circulos": "círculos",
    "modulo": "módulo",
    "modulos": "módulos",
    "titulo": "título",
    "titulos": "títulos",
    "vehiculo": "vehículo",
    "vehiculos": "vehículos",
    "estimulo": "estímulo",
    "estimulos": "estímulos",
    "maquina": "máquina",
    "maquinas": "máquinas",
    "trafico": "tráfico",
    "hormigon": "hormigón",
    "piston": "pistón",
    "pistofono": "pistófono",
    "microfono": "micrófono",
    "microfonos": "micrófonos",
    "sonometro": "sonómetro",
    "sonometros": "sonómetros",
    "hidrofono": "hidrófono",
    "hidrofonos": "hidrófonos",
    "acelerometro": "acelerómetro",
    "acelerometros": "acelerómetros",
    "vibrometro": "vibrómetro",
    "vibrometros": "vibrómetros",
    # Adjectives, in every gender and number.
    **{
        stem + ending: accented + ending
        for stem, accented in (
            ("acustic", "acústic"),
            ("aerodinamic", "aerodinámic"),
            ("analitic", "analític"),
            ("armonic", "armónic"),
            ("asimetric", "asimétric"),
            ("atmosferic", "atmosféric"),
            ("basic", "básic"),
            ("clasic", "clásic"),
            ("critic", "crític"),
            ("dinamic", "dinámic"),
            ("electric", "eléctric"),
            ("electronic", "electrónic"),
            ("empiric", "empíric"),
            ("energetic", "energétic"),
            ("estadistic", "estadístic"),
            ("estatic", "estátic"),
            ("fisic", "físic"),
            ("humed", "húmed"),
            ("geometric", "geométric"),
            ("logaritmic", "logarítmic"),
            ("logic", "lógic"),
            ("magnetic", "magnétic"),
            ("matematic", "matemátic"),
            ("maxim", "máxim"),
            ("mecanic", "mecánic"),
            ("minim", "mínim"),
            ("numeric", "numéric"),
            ("optic", "óptic"),
            ("optim", "óptim"),
            ("periodic", "periódic"),
            ("rapid", "rápid"),
            ("rigid", "rígid"),
            ("simetric", "simétric"),
            ("solid", "sólid"),
            ("tecnic", "técnic"),
            ("teoric", "teóric"),
            ("termic", "térmic"),
            ("tipic", "típic"),
            ("ultim", "últim"),
            ("unic", "únic"),
        )
        for ending in ("o", "a", "os", "as")
    },
    "debil": "débil",
    "debiles": "débiles",
    "facil": "fácil",
    "faciles": "fáciles",
    "dificil": "difícil",
    "dificiles": "difíciles",
    "util": "útil",
    "utiles": "útiles",
    "movil": "móvil",
    "moviles": "móviles",
}

#: A singular in -ción, -sión, -xión or -gión written without its accent. The
#: plural (-ciones) ends in -es and is never matched, and ``guion`` (which the
#: Real Academia writes without the accent since 2010) ends in -uion.
_SINGULAR_ION = re.compile(r"[^\W\d_]*[cgsx]ion")

#: Legitimate uses of a listed form, keyed by the Spanish value that carries it
#: and the word, with the reason. The verb a listed noun can also spell is the
#: case this is for; an entry that no longer matches anything fails the run.
ALLOWED: dict[tuple[str, str], str] = {}

#: What is not prose inside a value: a ``{placeholder}`` a renderer fills, an
#: HTML tag or entity of a report fiche, and an inline code span. Mathematics
#: is taken out separately, by :func:`_maths_runs`, because an escaped dollar
#: does not open it.
_NOT_PROSE = re.compile(r"\{[^{}]*\}|<[^<>]*>|&#?\w+;|`[^`]*`")

#: A run of word characters. A token that holds a digit or an underscore is an
#: identifier or a quantity, not a word, and is skipped whole: split on the
#: underscore, ``numero_bandas`` would read as a misspelt ``número``.
_TOKEN = re.compile(r"\w+")


class Value(NamedTuple):
    """One Spanish value, with where it is written."""

    path: str
    line: int
    text: str


class Offence(NamedTuple):
    """A word of a value that needs its accent or its eñe."""

    value: Value
    word: str
    spelling: str


def _maths_runs(text: str) -> list[tuple[int, int]]:
    """Index pairs of the ``$...$`` regions of *text*, escaped dollars aside."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, char in enumerate(text):
        if char != "$" or (i and text[i - 1] == "\\"):
            continue
        if start is None:
            start = i
        else:
            runs.append((start, i))
            start = None
    return runs


def prose(text: str) -> str:
    """*text* with its mathematics, placeholders, markup and code blanked."""
    chars = list(text)
    for lo, hi in _maths_runs(text):
        chars[lo : hi + 1] = " " * (hi + 1 - lo)
    return _NOT_PROSE.sub(lambda m: " " * len(m.group(0)), "".join(chars))


def _spelling(word: str) -> str | None:
    """The spelling *word* stands for, or None when it is correct as written."""
    lower = word.lower()
    right = NEEDS_MARK.get(lower)
    if right is None and _SINGULAR_ION.fullmatch(lower):
        right = lower[:-3] + "ión"
    if right is None:
        return None
    return right[0].upper() + right[1:] if word[0].isupper() else right


def words_needing_marks(text: str) -> list[tuple[str, str]]:
    """Every word of *text* that needs its accent or eñe, with its spelling."""
    found: list[tuple[str, str]] = []
    for match in _TOKEN.finditer(prose(text)):
        word = match.group(0)
        if not word.isalpha():
            continue
        right = _spelling(word)
        if right is not None:
            found.append((word, right))
    return found


def _is_spanish_branch(test: ast.expr) -> bool:
    """Whether *test* is ``language == "es"`` (or any ``... == "es"``)."""
    return (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "es"
    )


def _strings(node: ast.AST) -> list[ast.Constant]:
    """Every string constant under *node*."""
    return [
        sub
        for sub in ast.walk(node)
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str)
    ]


def _table_strings(value: ast.expr) -> list[ast.Constant]:
    """The Spanish strings of one table literal.

    A dictionary gives its values (a ``**spread`` has no key and is skipped),
    and a list of ``(pattern, replacement)`` pairs gives the replacements.
    """
    if isinstance(value, ast.Dict):
        return [
            item
            for key, item in zip(value.keys, value.values, strict=True)
            if key is not None
            and isinstance(item, ast.Constant)
            and isinstance(item.value, str)
        ]
    if isinstance(value, ast.List | ast.Tuple):
        return [
            pair.elts[1]
            for pair in value.elts
            if isinstance(pair, ast.Tuple)
            and len(pair.elts) == 2  # noqa: PLR2004 - a (pattern, replacement) pair
            and isinstance(pair.elts[1], ast.Constant)
            and isinstance(pair.elts[1].value, str)
        ]
    return []


def spanish_values(
    path: pathlib.Path, names: tuple[str, ...], *, branches: bool = False
) -> list[Value]:
    """The Spanish values of one source file.

    :param path: The Python file to read.
    :param names: The module-level names its tables are bound to.
    :param branches: Also read the body of every ``... == "es"`` branch, the
        conditional expression and the ``if`` statement alike.
    :return: One :class:`Value` per string, in source order.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    name = _named(path)
    constants: list[ast.Constant] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        else:
            continue
        if node.value is not None and any(t in names for t in targets):
            constants.extend(_table_strings(node.value))
    if branches:
        for branch in ast.walk(tree):
            if isinstance(branch, ast.IfExp) and _is_spanish_branch(branch.test):
                constants.extend(_strings(branch.body))
            elif isinstance(branch, ast.If) and _is_spanish_branch(branch.test):
                for statement in branch.body:
                    constants.extend(_strings(statement))
    constants.sort(key=lambda c: (c.lineno, c.col_offset))
    return [Value(name, c.lineno, str(c.value)) for c in constants]


def _named(path: pathlib.Path) -> str:
    """The path as a report prints it: relative to the tree, forward slashes."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_sources(
    sources: tuple[tuple[str, tuple[str, ...]], ...] = SOURCES,
    root: pathlib.Path = ROOT,
) -> tuple[list[Value], list[str]]:
    """Every Spanish value of the tables, and the sources that yielded none.

    :param sources: Pairs of a file or directory (relative to *root*) and the
        table names to read in it.
    :param root: The tree the paths are relative to.
    :return: The values, and the source paths that gave no value at all.
    """
    values: list[Value] = []
    empty: list[str] = []
    for where, names in sources:
        target = root / where
        files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
        found = [
            value
            for path in files
            if path.is_file()
            for value in spanish_values(path, names, branches=target.is_dir())
        ]
        if not found:
            empty.append(where)
        values.extend(found)
    return values, empty


def check(
    values: list[Value], allowed: dict[tuple[str, str], str] | None = None
) -> tuple[list[Offence], list[tuple[str, str]]]:
    """The words that need a mark, and the stale :data:`ALLOWED` entries.

    :param values: The Spanish values to read.
    :param allowed: The exemptions, :data:`ALLOWED` by default.
    :return: One :class:`Offence` per word not exempted, and the exemptions
        that matched no word of any value.
    """
    allowed = ALLOWED if allowed is None else allowed
    offences: list[Offence] = []
    used: set[tuple[str, str]] = set()
    for value in values:
        for word, right in words_needing_marks(value.text):
            key = (value.text, word)
            if key in allowed:
                used.add(key)
                continue
            offences.append(Offence(value, word, right))
    return offences, sorted(set(allowed) - used)


def main(argv: list[str] | None = None) -> int:
    """Report every Spanish value that lost an accent or an eñe."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)

    values, empty = read_sources()
    offences, stale = check(values)
    if not offences and not stale and not empty:
        print(
            f"Every accent and eñe is in place: {len(values)} Spanish values "
            f"across {len(SOURCES)} sources."
        )
        return 0
    for where in empty:
        print(f"::error::no Spanish table found in {where}; was it renamed?")
    if offences:
        print(f"::error::{len(offences)} Spanish word(s) without their accent or eñe")
        for offence in offences:
            print(
                f"  {offence.value.path}:{offence.value.line}: "
                f"{offence.word!r} is written {offence.spelling!r}"
            )
            print(f"      {offence.value.text[:100]!r}")
        print(
            "  -> write the accent. A verb that really is spelt without one "
            "goes in ALLOWED with its reason."
        )
    for text, word in stale:
        print(
            f"::error::ALLOWED lists {word!r} in {text[:60]!r}, which no longer needs it"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
