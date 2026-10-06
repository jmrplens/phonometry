#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Refuse a Spanish label written without its accent or its eñe.

Nearly every Spanish word the figures, the diagrams and the library's own
renderers draw comes out of a translation table, and a table entry typed on a
keyboard without the Spanish layout reads fine to every other gate: the language gate
sees a translated string, the parity check sees a pair, and the figure matches
its generator. Twenty-nine entries of the building-acoustics figures shipped
that way ("Correccion por ruido de fondo", "limite de medicion (1,3 dB fijos,
senalar la banda)", "la regla in situ termina aqui") with every gate green,
and so did the RD 1367/2007 example fiche, whose builder writes its phase
labels and header straight into the page ("Maquina ruidosa activa",
"Sonometro integrador-promediador"). The example builders that ask for a
Spanish fiche are therefore read as well (:data:`BUILDERS`). A figure module
can also draw a Spanish string of its own, past both tables, so the labels of
every published Spanish figure are read too, as the figure carries them
(:data:`FIGURES`).

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

The translation glossary is held here too, because a word the glossary has
replaced reads as correct Spanish to every other gate. Its single-word rulings
(:data:`GLOSSARY_TERMS`) and its phrases (:data:`GLOSSARY_PHRASES`) are read in
the tables and the figures, and also in the Spanish pages (:data:`PAGES`: the
site's Spanish edition, its strings, data, components and generated modules,
and the Spanish twins under ``docs/``), where the accent list is not applied:
page prose carries code, identifiers and quotations that only a label is free
of. A Markdown page has its mathematics and inline code blanked; a script, a
component, a data file or a generated module of the site is read as written,
since its dollars and backticks are JavaScript and the Spanish sits between
them.

The waveform is the case that needs more than a list. Spanish names it
«sinusoide», and «seno» is the trigonometric function; «un seno de 1 kHz»,
«seno escalonado» and «seno barrido» shipped in about fifty places, and
«Incertidumbre extendida» in a report fiche, with every gate green. A word
cannot tell the two senses apart, so every «seno» fails unless it stands in
one of the trigonometric contexts of :data:`TRIGONOMETRIC`, each with its
reason; a context that no longer matches anything fails as well. The words
built on «seno» for the waveform («senoidal», «semiseno», ...) are single
words, and the glossary's list names them.

The mean square is the other such case. The glossary writes it «valor
cuadrático medio», or with the adjective after its noun, «presión cuadrática
media», as the Spanish adoptions of the standards do, and keeps «media
cuadrática» for the quadratic mean: the root of the mean of the squares, the
effective value, which is another number. «Media cuadrática por segmento» and
«Media cuadrática en bloques de 400 ms» shipped for the mean square in two
diagrams, two figures, two renderers and three pages, with every gate green.
Where the English says root mean square or quadratic mean the phrase is right,
so every «media cuadrática» fails unless it stands in one of the contexts of
:data:`QUADRATIC_MEAN`, each with its reason, read the way the contexts of
«seno» are (:data:`SENSES`). A context is written on the words of the one
sentence it exempts, never on a shape such as «de los extremos» or «beside
an arithmetic mean», which a mean square can take as well. The statistician's
«cuadrado medio» names nothing else in acoustics, so it is a plain ruling of
the glossary, read as «incertidumbre extendida» is.

A budget is the third. The glossary writes every budget of quantities that
add up «balance», as UNE-EN ISO 3746:2011 Table D.2 writes the uncertainty
budget «balance de incertidumbre», and keeps «presupuesto» for money.
«Presupuesto de ruido», «presupuesto de absorción», «presupuesto de error» and
«un problema de control de ruido es un presupuesto» shipped in sixteen pages
and a diagram table, with every gate green, beside the «balance de
incertidumbre» of the same edition. So every word of the family
(«presupuesto», «presupuestos», «presupuestario», the verb «presupuestar» in
any of its forms, «presupuéstese» with its written accent among them) fails,
unless it stands in one of the contexts of :data:`MONEY`, where it means
money, each with its reason, read the way the contexts of «seno» are. A
code identifier built on the word (``presupuesto_ruido``) is not prose and is
left alone, as every token with a digit or an underscore is. The word has a
third sense, a premise or the participle of «presuponer» («los presupuestos
del modelo», «lo presupuesto»), which is neither money nor a budget: such a
sentence is reworded («los supuestos», «las hipótesis», «lo que se
presupone»), or, where it must keep the word, goes in :data:`ALLOWED` with its
reason, never written «balance» and never listed in :data:`MONEY`.

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
import html
import pathlib
import re
import sys
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Where the Spanish lives, and the names its tables are bound to. A directory
#: is read file by file, and in the library the body of a ``language == "es"``
#: branch is read too, since a renderer writes its few one-off Spanish strings
#: there instead of in its ``_STRINGS`` table. Every entry must yield at least
#: one value: a table that has been renamed would otherwise empty the gate
#: without a word. The two tables of the figures are two entries, so the exact
#: table cannot keep the pattern table's absence from being noticed.
SOURCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("scripts/figures/i18n.py", ("_ES_EXACT",)),
    ("scripts/figures/i18n.py", ("_ES_PATTERNS",)),
    ("scripts/diagrams/i18n.py", ("_ES",)),
    ("src/phonometry/_plot", ("_STRINGS",)),
    ("src/phonometry/_report", ("_STRINGS",)),
)

#: The example fiches: their builders write metadata and labels straight into
#: the page, past every table. A builder is read, docstring aside, when it
#: asks for the Spanish fiche by name (``language="es"`` in a call, or
#: ``"language": "es"`` among the ``report()`` keywords it returns), which is
#: why a builder of a Spanish fiche names the language even where it is the
#: renderer's default. The directory must hold at least one such builder.
BUILDERS: tuple[str, ...] = ("scripts/reports",)

#: The Spanish pages, as glob patterns relative to the tree: the site's Spanish
#: edition, the strings of its interface, the data files whose ``es`` fields it
#: renders (the glossary cards, the topic labels, the catalogue names), the
#: components that carry their own Spanish strings, the generated modules the
#: site imports (the Spanish labels of the API sidebar, written from
#: ``scripts/api_taxonomy.py``, and the catalogues), and the Spanish twins of
#: ``docs/``. Only the glossary is read in them (see the module docstring), and
#: every pattern must match a file with text in it.
PAGES: tuple[str, ...] = (
    "site/src/content/docs/es/**/*.md",
    "site/src/content/docs/es/**/*.mdx",
    "site/src/content/i18n/es.json",
    "site/src/data/*.mjs",
    "site/src/data/*.ts",
    "site/src/data/*.json",
    "site/src/components/**/*.astro",
    "site/src/generated/*.mjs",
    "docs/*.es.md",
)

#: The published Spanish figures, as glob patterns relative to the tree. A
#: figure module may draw Spanish of its own, past both translation tables: a
#: ``_wt_text(english, spanish)`` pair, or the ``(english, spanish, ...)`` rows
#: of a table the module keeps for one figure. Matplotlib writes every string
#: it draws into the SVG as a ``<!-- ... -->`` comment before its outlines,
#: so the comments are every Spanish label a reader sees, whatever wrote it,
#: and the figure gate keeps them equal to what the generators draw now. Each
#: label is read as a table value, accents and glossary alike, and every
#: pattern must match a figure with a label in it. A raster figure (the few
#: kept as WebP because their SVG would be heavier) carries no text at all,
#: so its Spanish is read only where it comes from a table.
FIGURES: tuple[str, ...] = (
    ".github/images/*_es.svg",
    ".github/images/*_es_dark.svg",
)

#: A page written in Markdown, whose dollars delimit mathematics and whose
#: backticks delimit code. Every other page (a script, a component, a data or
#: strings file of the site) is JavaScript or JSON, where a dollar opens a
#: ``${...}`` substitution or ends a regular expression and a backtick opens a
#: template literal: blanking between them would hide the Spanish strings they
#: hold, so such a page is read as written.
_MARKDOWN: frozenset[str] = frozenset({".md", ".mdx"})

#: A text comment of a Matplotlib SVG: the string drawn by the outlines that
#: follow it, with ``&``, ``<`` and ``>`` escaped.
_SVG_LABEL = re.compile(r"<!-- (.*?) -->", re.DOTALL)

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

#: Words the translation glossary replaces with another word rather than an
#: accent. Signal processing says "diezmado" in Spanish for what English calls
#: decimation, and the calque "decimación" once reached the multirate diagram
#: through a table every other gate read as correct Spanish.
GLOSSARY_TERMS: dict[str, str] = {
    "decimación": "diezmado",
    "decimacion": "diezmado",
    "decimaciones": "diezmados",
    "decimado": "diezmado",
    "decimados": "diezmados",
    "decimada": "diezmada",
    "decimadas": "diezmadas",
    "decimar": "diezmar",
    # The waveform is a sinusoide: «senoide» is not in the Real Academia's
    # dictionary, and the Spanish signal-processing literature writes the
    # adjective «sinusoidal» nine times out of ten. The noun «seno» is the
    # trigonometric function and needs its context, so it is read apart
    # (:data:`TRIGONOMETRIC`).
    "senoide": "sinusoide",
    "senoides": "sinusoides",
    "senoidal": "sinusoidal",
    "senoidales": "sinusoidales",
    "senoidalmente": "sinusoidalmente",
    "semisenoidal": "semisinusoidal",
    "semisenoidales": "semisinusoidales",
    # A half-sine pulse is a «semisinusoide»; «semiseno» shipped once in a
    # code comment beside a «semisinusoidal» of the same example.
    "semiseno": "semisinusoide",
    "semisenos": "semisinusoides",
    "semisenoide": "semisinusoide",
    "semisenoides": "semisinusoides",
}

#: Rulings of the glossary that take more than one word, as a pattern (read
#: without regard to case, across a line break) and the Spanish it stands for.
#: «Incertidumbre expandida» is the GUM's own Spanish for expanded uncertainty;
#: the calque «incertidumbre extendida» reached a report fiche through a table.
GLOSSARY_PHRASES: dict[str, str] = {
    r"(?<!\w)incertidumbres?\s+extendidas?(?!\w)": "incertidumbre expandida",
    # The mean square is a «valor cuadrático medio» (:data:`QUADRATIC_MEAN`);
    # the statistician's «cuadrado medio» reached four guides and the
    # DIN 45672-2 erratum, beside a «valor cuadrático medio» on the same page.
    r"(?<!\w)cuadrado\s+medio(?!\w)": "valor cuadrático medio",
    r"(?<!\w)cuadrados\s+medios(?!\w)": "valores cuadráticos medios",
}

#: The contexts in which «seno» is the trigonometric function (or the noun of
#: "en el seno de", the bosom of a medium) and not the waveform, as a pattern
#: read without regard to case on the text as written, mathematics included,
#: and the reason. Outside them every «seno» is the waveform and fails: the
#: waveform is «sinusoide». A context that matches no «seno» of the tree fails
#: the run, so the list cannot outlive its reason.
TRIGONOMETRIC: dict[str, str] = {
    r"(?<!\w)seno\s*/\s*coseno(?!\w)": (
        "a demodulator correlates with the sine and the cosine functions"
    ),
    r"(?<!\w)coseno\s+y\s+(?:el\s+)?seno\s+de(?!\w)": (
        "the cosine and the sine of an argument"
    ),
    r"(?<!\w)seno\s+del\s+ángulo(?!\w)": "the sine of an angle",
    r"(?<!\w)seno\s+de\s+(?:theta|θ)(?!\w)": (
        "the sine of an angle, spelt out for a screen reader"
    ),
    r"(?<!\w)transformada\s+(?:discreta\s+)?de\s+senos(?!\w)": (
        "the discrete sine transform, built on the function"
    ),
    r"(?<!\w)términos\s+seno(?!\w)": "the sine terms of a printed formula",
    r"(?<!\w)seno\s+lleva\s+\$k_\{33\}\$": (
        "the sine term of a printed formula, named by the argument it carries"
    ),
    r"(?<!\w)en\s+el\s+seno\s+del\s+material(?!\w)": (
        "the bosom of a medium, not a function at all"
    ),
}

#: The contexts in which «media cuadrática» is the quadratic mean, the root of
#: the mean of the squares, and not the mean square, as a pattern read without
#: regard to case on the text as written, and the reason. Outside them every
#: «media cuadrática» is the mean square and fails: the mean square is «valor
#: cuadrático medio». A context that matches no «media cuadrática» of the tree
#: fails the run, as a trigonometric one does.
QUADRATIC_MEAN: dict[str, str] = {
    r"(?<!\w)media\s+cuadrática\s+de\s+las\s+dos\s+velocidades\s+verdaderas\s+"
    r"de\s+los\s+extremos(?!\w)": (
        "the root of the mean of the two squared end-point speeds that ICAO "
        "Doc 9911 prints under its Eq. (B-12), in the erratum that reads it"
    ),
    r"(?<!\w)media\s+cuadrática\s+de\s+los\s+dos\s+valores\s+de\s+los\s+"
    r"extremos\s+es\s+un\s+número\s+distinto(?!\w)": (
        "the same Doc 9911 end-point speed, set against the mid-step one"
    ),
    r"(?<!\w)lo\s+sitúa\s+en\s+la\s+media\s+cuadrática\s+de\s+los\s+"
    r"extremos(?!\w)": (
        "the same Doc 9911 end-point speed, where the Eq. (B-12) branch puts "
        "the aircraft"
    ),
    r"(?<!\w)construida\s+exactamente\s+sobre\s+esta\s+media\s+"
    r"cuadrática(?!\w)": (
        "the same root-mean-square speed, which Doc 9911 B6.1.3 is built on"
    ),
    r"(?<!\w)media\s+cuadrática\s+supera\s+a\s+la\s+media\s+aritmética,\s+"
    r"que\s+supera\s+al\s+valor\s+de\s+media\s+altitud(?!\w)": (
        "the Doc 9911 root-mean-square speed ranked above the arithmetic mean "
        "of the end points and the mid-altitude speed"
    ),
    r"(?<!\w)media\s+aritmética\s+323\.944\s+ft\s+largo\s+y\s+la\s+media\s+"
    r"cuadrática\s+impresa(?!\w)": (
        "the printed root-mean-square candidate of Doc 9911 case 56, set "
        "beside the arithmetic one"
    ),
    r"(?<!\w)media\s+cuadrática\s+de\s+las\s+incertidumbres(?!\w)": (
        "the root mean square of the per-period uncertainties of IEC 61400-11"
    ),
    r"(?<!\w)binaurales\s+de\s+media\s+cuadrática(?!\w)": (
        "the quadratic-mean combination of the two ears in ECMA-418-2"
    ),
}

#: The contexts in which «presupuesto» (or a word of its family) is money and
#: not a budget of quantities that add up, as a pattern read without regard to
#: case on the text as written, and the reason. Outside them every such word
#: fails: the budget is a «balance» (de ruido, de absorción, de error, ...).
#: Only money belongs here: a premise («los presupuestos del modelo») is
#: reworded instead (see the module docstring). No sentence of the tree means
#: money, so the table is empty; a context added for one must keep matching
#: it, as a trigonometric one must.
MONEY: dict[str, str] = {}


class Sense(NamedTuple):
    """A term that names two things, of which the glossary keeps one apart.

    Each match of *word* fails with the glossary's term, *singular* or
    *plural* as the form is, unless it stands in one of *contexts*, where the
    term has its other sense. *table* is the name the contexts are bound to
    and *term* the term as a report names it. When *noun* is given, only the
    forms it matches whole are nouns that the glossary's term replaces; any
    other form of the family (a verb, an adjective) gets
    :data:`REWORD_PREFIX` and the term instead, because no noun can stand in
    its place and the sentence has to be reworded around the term.
    """

    word: re.Pattern[str]
    singular: str
    plural: str
    contexts: dict[str, str]
    table: str
    term: str
    noun: re.Pattern[str] | None = None


#: What a form that is not a noun is told to do, followed by the glossary term.
REWORD_PREFIX = "reword around "


#: The terms read by sense: the noun the waveform and the function share, the
#: phrase the mean square and the quadratic mean share, and the word a budget
#: of summed quantities and money share. The family of «presupuesto» is matched
#: whole, the accented stem of «presupuéstese» included, so the verb and the
#: adjective built on it cannot carry the budget past the gate; like every
#: other word, it stops at a digit or an underscore, so an identifier such as
#: ``presupuesto_ruido`` is not read as prose.
SENSES: tuple[Sense, ...] = (
    Sense(
        re.compile(r"(?<!\w)senos?(?!\w)", re.IGNORECASE),
        "sinusoide",
        "sinusoides",
        TRIGONOMETRIC,
        "TRIGONOMETRIC",
        "«seno»",
    ),
    Sense(
        re.compile(r"(?<!\w)medias?\s+cuadr[aá]ticas?(?!\w)", re.IGNORECASE),
        "valor cuadrático medio",
        "valores cuadráticos medios",
        QUADRATIC_MEAN,
        "QUADRATIC_MEAN",
        "«media cuadrática»",
    ),
    Sense(
        re.compile(r"(?<!\w)presupu[eé]st[^\W\d_]*(?!\w)", re.IGNORECASE),
        "balance",
        "balances",
        MONEY,
        "MONEY",
        "«presupuesto»",
        re.compile(r"presupuestos?", re.IGNORECASE),
    ),
)

#: Every context of every term read by sense. The patterns of one term never
#: match another's, so one mapping serves them all.
CONTEXTS: dict[str, str] = {
    pattern: reason for sense in SENSES for pattern, reason in sense.contexts.items()
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

#: What is not prose in a page: an inline code span on one line. A page's tags
#: stay, because the alternative text of a figure is Spanish a reader hears,
#: and so does a fenced block, whose comments and labels are Spanish too.
_NOT_PAGE_PROSE = re.compile(r"`[^`\n]*`")

#: A paragraph of a page: a run of lines up to the next blank one. Mathematics
#: is paired inside a paragraph, so one stray dollar cannot hide the page.
_PARAGRAPH = re.compile(r"(?:[^\n]|\n(?![ \t]*\n))+")

#: A run of word characters. A token that holds a digit or an underscore is an
#: identifier or a quantity, not a word, and is skipped whole: split on the
#: underscore, ``numero_bandas`` would read as a misspelt ``número``.
_TOKEN = re.compile(r"\w+")


class Value(NamedTuple):
    """One Spanish value, with where it is written.

    A table entry is one value, and so is a label of a figure; a page is read
    paragraph by paragraph, each one a value whose *line* is its first and
    whose *text* is the page as written, so the line of a word inside it can
    be counted. A page that is not Markdown (*script*: a script, a component,
    a data or strings file) is read with nothing blanked, since its dollars
    and backticks are JavaScript (see :data:`_MARKDOWN`).
    """

    path: str
    line: int
    text: str
    page: bool = False
    script: bool = False


class Offence(NamedTuple):
    """A word of a value that needs its accent or its eñe, or its glossary term."""

    value: Value
    word: str
    spelling: str
    line: int


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
    right = NEEDS_MARK.get(lower) or GLOSSARY_TERMS.get(lower)
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


def page_prose(text: str, *, script: bool = False) -> str:
    """A page paragraph with its mathematics and its inline code blanked.

    Unlike :func:`prose`, a tag and a fenced block stay readable: the
    alternative text of a figure and the comments of an example are Spanish a
    reader meets (see :data:`_NOT_PAGE_PROSE`).

    :param text: The paragraph as written.
    :param script: The page is not Markdown (see :data:`_MARKDOWN`), and
        *text* comes back as written.
    """
    if script:
        return text
    chars = list(text)
    for lo, hi in _maths_runs(text):
        chars[lo : hi + 1] = " " * (hi + 1 - lo)
    return _NOT_PAGE_PROSE.sub(lambda m: " " * len(m.group(0)), "".join(chars))


def _cased(word: str, right: str) -> str:
    """*right* with the capital *word* starts with, if it starts with one."""
    return right[0].upper() + right[1:] if word[0].isupper() else right


def glossary_departures(
    text: str,
    *,
    page: bool = False,
    script: bool = False,
    contexts: dict[str, str] | None = None,
    used: set[str] | None = None,
) -> list[tuple[str, str, int]]:
    """Every place *text* departs from the glossary, with the glossary's term.

    :param text: A table value, or a page paragraph as written.
    :param page: Read *text* as a page (:func:`page_prose`), and read the
        single-word rulings of :data:`GLOSSARY_TERMS` here too; in a table
        they come with the accents, from :func:`words_needing_marks`.
    :param script: With *page*, the page is not Markdown and nothing of it
        is blanked (see :data:`_MARKDOWN`).
    :param contexts: The contexts in which a term of :data:`SENSES` keeps
        its other sense, :data:`CONTEXTS` (the trigonometric «seno», the
        quadratic mean and money) by default.
    :param used: A set that receives every context that exempted a term.
    :return: ``(as written, glossary term, offset in text)`` in text order.
    """
    contexts = CONTEXTS if contexts is None else contexts
    readable = page_prose(text, script=script) if page else prose(text)
    found: list[tuple[str, str, int]] = []
    for pattern, right in GLOSSARY_PHRASES.items():
        for match in re.finditer(pattern, readable, re.IGNORECASE):
            written = " ".join(match.group(0).split())
            found.append((written, _cased(written, right), match.start()))
    if page:
        for match in _TOKEN.finditer(readable):
            word = match.group(0)
            term = GLOSSARY_TERMS.get(word.lower())
            if term is not None and word.isalpha():
                found.append((word, _cased(word, term), match.start()))
    for sense in SENSES:
        found.extend(_departures_by_sense(sense, text, readable, contexts, used))
    found.sort(key=lambda item: item[2])
    return found


def _departures_by_sense(
    sense: Sense,
    text: str,
    readable: str,
    contexts: dict[str, str],
    used: set[str] | None,
) -> list[tuple[str, str, int]]:
    """Every match of one term read by sense that stands in none of *contexts*.

    :param sense: The term and its glossary terms.
    :param text: The value as written, where the contexts are matched.
    :param readable: The same value with what is not prose blanked, where the
        term is matched; both have the same length, so offsets agree.
    :param contexts: The contexts that exempt a match lying inside one.
    :param used: A set that receives every context that exempted a match.
    :return: ``(as written, glossary term, offset in text)`` per match.
    """
    matches = list(sense.word.finditer(readable))
    spans = [
        (match.start(), match.end(), pattern)
        for pattern in (contexts if matches else ())
        for match in re.finditer(pattern, text, re.IGNORECASE)
    ]
    found: list[tuple[str, str, int]] = []
    for match in matches:
        exempt = {p for lo, hi, p in spans if lo <= match.start() and match.end() <= hi}
        if exempt:
            if used is not None:
                used.update(exempt)
            continue
        written = " ".join(match.group(0).split())
        if sense.noun is not None and not sense.noun.fullmatch(written):
            found.append((written, f"{REWORD_PREFIX}«{sense.singular}»", match.start()))
            continue
        plural = written.split()[0].lower().endswith("s")
        right = sense.plural if plural else sense.singular
        found.append((written, _cased(written, right), match.start()))
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


def _names_spanish(function: ast.FunctionDef) -> bool:
    """Whether *function* asks for a Spanish fiche by name."""
    for node in ast.walk(function):
        if (
            isinstance(node, ast.keyword)
            and node.arg == "language"
            and isinstance(node.value, ast.Constant)
            and node.value.value == "es"
        ):
            return True
        if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant)
            and key.value == "language"
            and isinstance(item, ast.Constant)
            and item.value == "es"
            for key, item in zip(node.keys, node.values, strict=True)
        ):
            return True
    return False


def builder_values(path: pathlib.Path) -> list[Value]:
    """The strings of every example builder in *path* that asks for Spanish.

    :param path: A module of example-fiche builders.
    :return: One :class:`Value` per string of each such top-level function,
        its docstring left out, in source order.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    name = _named(path)
    constants: list[ast.Constant] = []
    for function in tree.body:
        if not isinstance(function, ast.FunctionDef) or not _names_spanish(function):
            continue
        body = function.body
        if ast.get_docstring(function) is not None:
            body = body[1:]
        for statement in body:
            constants.extend(_strings(statement))
    constants.sort(key=lambda c: (c.lineno, c.col_offset))
    return [Value(name, c.lineno, str(c.value)) for c in constants]


def page_values(path: pathlib.Path) -> list[Value]:
    """The paragraphs of a Spanish page, each one a value read as a page.

    :param path: A page, or a data file of the site, read as text.
    :return: One :class:`Value` per paragraph that holds anything but blanks,
        its line the paragraph's first, its text the paragraph as written,
        marked *script* unless the page is Markdown.
    """
    text = path.read_text(encoding="utf-8")
    name = _named(path)
    script = path.suffix not in _MARKDOWN
    return [
        Value(name, line, match.group(0), page=True, script=script)
        for line, match in _numbered(text, _PARAGRAPH)
        if match.group(0).strip()
    ]


def figure_values(path: pathlib.Path) -> list[Value]:
    """The labels of a published Spanish figure, each one a value.

    :param path: A Matplotlib SVG.
    :return: One :class:`Value` per text comment that holds anything but
        blanks, its line the comment's, its text the string as drawn.
    """
    text = path.read_text(encoding="utf-8")
    name = _named(path)
    return [
        Value(name, line, html.unescape(match.group(1)))
        for line, match in _numbered(text, _SVG_LABEL)
        if match.group(1).strip()
    ]


def _numbered(
    text: str, pattern: re.Pattern[str]
) -> Iterator[tuple[int, re.Match[str]]]:
    """Every match of *pattern* in *text*, with the line it starts on."""
    line, counted = 1, 0
    for match in pattern.finditer(text):
        line += text.count("\n", counted, match.start())
        counted = match.start()
        yield line, match


def _named(path: pathlib.Path) -> str:
    """The path as a report prints it: relative to the tree, forward slashes."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_sources(
    sources: tuple[tuple[str, tuple[str, ...]], ...] = SOURCES,
    root: pathlib.Path = ROOT,
    builders: tuple[str, ...] = BUILDERS,
    pages: tuple[str, ...] = PAGES,
    figures: tuple[str, ...] = FIGURES,
) -> tuple[list[Value], list[str]]:
    """Every Spanish value of the tables, figures and pages, and the empty sources.

    :param sources: Pairs of a file or directory (relative to *root*) and the
        table names to read in it.
    :param root: The tree the paths are relative to.
    :param builders: Directories of example-fiche builders (relative to
        *root*), read with :func:`builder_values`.
    :param pages: Glob patterns of Spanish pages (relative to *root*), read
        with :func:`page_values`.
    :param figures: Glob patterns of Spanish figures (relative to *root*),
        read with :func:`figure_values`.
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
            empty.append(f"{where} ({', '.join(names)})")
        values.extend(found)
    for where in builders:
        found = [
            value
            for path in sorted((root / where).rglob("*.py"))
            for value in builder_values(path)
        ]
        if not found:
            empty.append(where)
        values.extend(found)
    for patterns, read in ((pages, page_values), (figures, figure_values)):
        for pattern in patterns:
            found = [
                value
                for path in sorted(root.glob(pattern))
                if path.is_file()
                for value in read(path)
            ]
            if not found:
                empty.append(pattern)
            values.extend(found)
    return values, empty


def check(
    values: list[Value],
    allowed: dict[tuple[str, str], str] | None = None,
    contexts: dict[str, str] | None = None,
) -> tuple[list[Offence], list[tuple[str, str]]]:
    """The words that need a mark or a glossary term, and the stale exemptions.

    :param values: The Spanish values to read.
    :param allowed: The exemptions, :data:`ALLOWED` by default.
    :param contexts: The contexts of the terms read by sense,
        :data:`CONTEXTS` by default.
    :return: One :class:`Offence` per word not exempted, and the exemptions
        that matched no word of any value.
    """
    allowed = ALLOWED if allowed is None else allowed
    offences: list[Offence] = []
    used: set[tuple[str, str]] = set()
    for value in values:
        found = [
            (word, right, value.line)
            for word, right in ([] if value.page else words_needing_marks(value.text))
        ]
        for word, right, offset in glossary_departures(
            value.text, page=value.page, script=value.script, contexts=contexts
        ):
            line = value.line
            if value.page:
                line += value.text.count("\n", 0, offset)
            found.append((word, right, line))
        for word, right, line in found:
            key = (value.text, word)
            if key in allowed:
                used.add(key)
                continue
            offences.append(Offence(value, word, right, line))
    return offences, sorted(set(allowed) - used)


def unused_contexts(
    values: list[Value], contexts: dict[str, str] | None = None
) -> list[str]:
    """The contexts that exempt no term of *values* read by sense.

    :param values: The Spanish values to read.
    :param contexts: The contexts, :data:`CONTEXTS` by default.
    :return: The patterns that exempted nothing, in their listed order.
    """
    contexts = CONTEXTS if contexts is None else contexts
    used: set[str] = set()
    for value in values:
        glossary_departures(
            value.text,
            page=value.page,
            script=value.script,
            contexts=contexts,
            used=used,
        )
    return [pattern for pattern in contexts if pattern not in used]


def _quoted(offence: Offence) -> str:
    """The line of the value that holds the offence, as the report quotes it."""
    lines = offence.value.text.splitlines() or [""]
    index = offence.line - offence.value.line if offence.value.page else 0
    return lines[min(index, len(lines) - 1)].strip()[:100]


def main(argv: list[str] | None = None) -> int:
    """Report every Spanish value that lost an accent, an eñe or its term."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args(argv)

    values, empty = read_sources()
    offences, stale = check(values)
    unused = unused_contexts(values)
    if not offences and not stale and not empty and not unused:
        print(
            f"Every accent, eñe and glossary term is in place: {len(values)} "
            "Spanish values across "
            f"{len(SOURCES) + len(BUILDERS) + len(PAGES) + len(FIGURES)} sources."
        )
        return 0
    for where in empty:
        print(f"::error::no Spanish found in {where}; was a table renamed?")
    if offences:
        print(
            f"::error::{len(offences)} Spanish word(s) without their accent, "
            "eñe or glossary term"
        )
        for offence in offences:
            advice = (
                offence.spelling
                if offence.spelling.startswith(REWORD_PREFIX)
                else f"is written {offence.spelling!r}"
            )
            print(f"  {offence.value.path}:{offence.line}: {offence.word!r} {advice}")
            print(f"      {_quoted(offence)!r}")
        print(
            "  -> write the accent or the glossary's term. A verb that really "
            "is spelt without an accent goes in ALLOWED, a trigonometric "
            "«seno» in TRIGONOMETRIC, a quadratic mean, the root of a mean "
            "square, in QUADRATIC_MEAN and a «presupuesto» that is money in "
            "MONEY, with its reason. A «presupuesto» that is a premise is "
            "reworded («supuesto», «hipótesis»), never written «balance»."
        )
    for text, word in stale:
        print(
            f"::error::ALLOWED lists {word!r} in {text[:60]!r}, which no longer needs it"
        )
    for pattern in unused:
        sense = next(sense for sense in SENSES if pattern in sense.contexts)
        print(
            f"::error::{sense.table} lists {pattern!r}, which no longer exempts "
            f"any {sense.term}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
