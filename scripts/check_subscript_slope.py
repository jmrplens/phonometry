#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Gate for a subscript that means two things on one page.

ISO 80000-2 settles the slope of a subscript by what the subscript *is*: a
quantity symbol stays italic (:math:`L_p`, pressure; :math:`L_W`, power), a
word or an abbreviation is upright (:math:`R_\mathrm{w}`, weighted), a number
is upright by definition, and an index that runs over a sum is italic. The
corpus applies that rule, and CONTRIBUTING.md states it.

What the rule does not settle is the glyph that takes both slopes honestly.
:math:`D_z` is the ISO 9613-2 barrier screening, whose *z* is the difference
between the diffracted and direct path lengths -- a quantity, italic -- and it
is the ISO 2631-5 acceleration dose, whose *z* names a direction -- upright.
Both documents print ``D_z``. Neither spelling is ours to change, so no single
corpus-wide slope for that pair can be right: one of the two modules would be
wrong by construction. Twenty pairs behave this way here.

So the unit of decision is the file, not the glyph. Each module opens with the
standard it implements and each guide with the standard it explains, so inside
one file a subscript has one meaning and therefore one slope. That is the
invariant this checks: **no file writes the same (base, subscript) pair both
ways.** Across files it says nothing, deliberately -- that is where the
legitimate duals live.

A second invariant covers the letter that keeps one meaning under several
bases. DIN 4150-2 names its assessment quantities by the r of "Beurteilung":
the assessment severity :math:`KB_\mathrm{FTr}`, the guide value it is held to,
:math:`A_\mathrm{r}`, the assessment time :math:`T_\mathrm{r}` and the count of
clock intervals in it, :math:`N_\mathrm{r}`, all with one upright r. Those are
four symbols, so the first rule sees four single-valued pairs even when one of
them leans: a page setting :math:`KB_\mathrm{FTr}` against an italic
:math:`A_r` is consistent symbol by symbol and still sets one letter two ways
inside one formula. The members of each family in :data:`LINKED` therefore take
one slope in a file, whichever of them it writes.

A third rule holds the corpus rather than the file, for a base whose sources
disagree with each other. DIN 4150-2, its 2023 draft, DIN 45672-2 and
E DIN 45672-3 print the weighted vibration severity with an italic KB, and the
list of symbols of DIN 45669-1 sets it upright; the corpus follows DIN 4150-2.
That is a choice between sources, not a meaning a file can state, so every
file, the errata register and the drawing modules included, and every image
in the directory, embedded or not, sets each base of :data:`BASES` the one way.

A fourth rule holds every running index italic, in every file and every
image. Some standards print every subscript in one slope, and such a print
cannot tell an index from an abbreviation: UNE-EN 15657:2018 sets the index
of the position levels :math:`L_{\mathrm{v},i}` (Formula (12)) as upright as
the v beside it, and EN 12354-5:2009, IEC 60534-8-3, CNOSSOS-EU, RD 1367/2007
and NT ACOU 112 print their subscripts the same way. There ISO 80000-2
decides, as the corpus has: a running index is a variable and italic, a
descriptive abbreviation upright. So the letter a sum runs over
(:math:`\sum_i`, the Σ of a plate) and an i, j or k that follows another
component of the same subscript (:math:`L_{\mathrm{v},i}`,
:math:`D_{\mathrm{C},i}`, :math:`L_{\mathrm{n,s},ij}`) are italic wherever
they are written, the drawing modules included (:func:`index_slips`). An
upright i that opens a subscript is not read: that is the impact level
:math:`L_\mathrm{i}` of ISO 16283-2, which the first rule already holds
against an index on the same page. The errata register is not read for this
either, since it quotes prints that set the index upright.

What a failure means, in order of how often it is the answer
------------------------------------------------------------

1. **One of the two is an index and can be re-lettered.** A subscript that
   runs over a sum is a bound variable: the letter is ours and means nothing
   outside the formula, while the colliding quantity's letter belongs to the
   standard that defines it. ``insulation.py`` energy-averages positions with
   :math:`\sum_i 10^{L_i/10}` and states ISO 16283-2's impact sound pressure
   level as :math:`L_\mathrm{i}`, on the same page. The index moved to *j*;
   the quantity could not move at all.
2. **One of the two lags.** The file already writes the settled slope
   elsewhere and one occurrence -- typically inside a plotting snippet, where
   the mathematics is a string inside a string -- was missed. Set it the way
   its neighbours are set.
3. **The page really does carry both meanings**, which is what a glossary is
   for. Register it in :data:`DECLARED`, naming both meanings. That list is
   meant to stay short: it is the escape hatch for a page whose subject is the
   collision, not a way to land one.

The images a page embeds
------------------------

A guide is not only its prose. The diagram plates and the figures it embeds
are read here from the committed SVG, because that is what a reader sees, and
neither is reliably in the prose: a plate's source never writes a slope, and a
figure's source is a generator in ``scripts/figures`` that no page quotes. A
page and the images it embeds are then one scope: a plate that draws $L_i$
sloped on a page whose prose sets the impact level $L_\mathrm{i}$ upright is
the page contradicting itself, in the place a reader looks first. A Spanish
page is held against the Spanish image, which is the file the site shows there.

The two kinds are read differently. The composer in
``scripts/diagrams/canvas.py`` decides a plate's slope run by run, so the
plate is read from its glyphs: each label carries its source string in an XML
comment and its glyphs in groups whose ids name the face, so the oblique face
marks an italic letter without reading a font file, and
:func:`plate_sightings` lines the two up. A figure is set by matplotlib's
mathtext, whose slope is the source's own (a bare letter italic, a
``\mathrm`` run upright), and matplotlib keeps that source in an XML comment
ahead of the glyphs of every text it draws, so :func:`figure_sightings` reads
the comments the way :func:`sightings` reads a page.

What this cannot check
----------------------

Whether the slope a file chose is the *right* one for its standard. That is a
reading of a source document, and no script does it. This gate only keeps a
file from asserting two answers at once, which is the failure a reader can see
without leaving the page.

Exit status 0 when every file is single-valued, 1 otherwise.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import html
import itertools
import pathlib
import re
import sys
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

#: Where the prose lives: the module docstrings that become the API reference,
#: and the three editions of the guides.
DEFAULT_ROOTS = (
    "src/phonometry",
    "docs",
    "site/src/content/docs",
)

#: Suffixes carrying mathematics. ``.py`` for the docstrings, the rest for the
#: guides, whose plotting snippets carry labels of their own.
_SUFFIXES = {".py", ".md", ".mdx"}

#: What the file scope does not apply to.
#:
#: The errata registry transcribes what a published page prints, so its slopes
#: are the source's and not this project's to reconcile.
#:
#: The drawing modules are filed by domain rather than by standard -- one
#: ``_plot`` module holds the figures of a dozen of them -- so a file there is
#: not the scope in which a letter has one meaning; the guide that embeds the
#: figure is, and that is read here. The generators of the plates and the
#: figures are never collected, for the same reason and one more: a plate's
#: source never writes a slope, which the composer in
#: ``scripts/diagrams/canvas.py`` decides, so both are read from the committed
#: SVG instead, page by page (:func:`embedded`).
_EXCLUDED = re.compile(r"errata|/_plot/|/_report/", re.IGNORECASE)

#: Pages that carry both meanings on purpose, with the reason. Keyed on the
#: repository-relative path and the ``(base, subscript)`` pair; the path is
#: matched against the tail of the file's own, so the gate declares the same
#: page whether it is run from the repository root or given absolute roots.
_GLOSSARY: dict[tuple[str, str], str] = {
    ("L", "N"): (
        "the ambiguity table's own subject: the percentile level, whose "
        "N is the percentage, against the sonar noise level of "
        "ISO 18405, whose N is the noise"
    ),
    ("L", "s"): (
        "likewise: the mean of the two bands adjacent to a candidate "
        "tone, whose s is unexpanded anywhere in this corpus, against "
        "the equivalent monopole source level of ISO 17208-2"
    ),
    ("D", "z"): (
        "the pair the ambiguity table exists to separate: the barrier "
        "screening of ISO 9613-2, whose z is the difference between the "
        "diffracted and the direct path length, against the acceleration "
        "dose of ISO 2631-5, whose z names the vertical direction. The "
        "table prints the two slopes side by side because that is the "
        "distinction it is describing"
    ),
}

_DIFFUSERS: dict[tuple[str, str], str] = {
    ("d", "n"): (
        "the normalised diffusion coefficient of ISO 17497-2, Formula (7), "
        "whose n stands for normalised and is printed upright, as the "
        "goniometer plate the page embeds draws it, against the well depth "
        "of the quadratic-residue diffuser, whose n counts the wells. Both "
        "pages write both, as their sources do, and the diffusers guide's "
        "note on symbols says that the slope is what tells them apart"
    ),
}

_RD1367: dict[tuple[str, str], str] = {
    ("L", "f"): (
        "RD 1367/2007, Annex IV A.3.3, names two quantities Lf on consecutive "
        "pages: the level of the band f that holds an emergent tone, whose f "
        "is the band and stays italic, and the difference LCeq,Ti - LAeq,Ti "
        "that sets the low-frequency correction, whose f names the "
        "low-frequency component as the f of Kf does and is upright beside "
        "the upright i of the impulsive Li. The BOE sets both in one upright "
        "face, so the print cannot tell them apart and the meaning does"
    ),
}

DECLARED: dict[str, dict[tuple[str, str], str]] = {
    "docs/reference/glossary.md": _GLOSSARY,
    "site/src/content/docs/reference/glossary.mdx": _GLOSSARY,
    "site/src/content/docs/es/reference/glossary.mdx": _GLOSSARY,
    "docs/materials/diffusers/diffusers.md": _DIFFUSERS,
    "site/src/content/docs/materials/diffusers/diffusers.mdx": _DIFFUSERS,
    "site/src/content/docs/es/materials/diffusers/diffusers.mdx": _DIFFUSERS,
    "docs/materials/diffusers/metadiffusers.md": _DIFFUSERS,
    "site/src/content/docs/materials/diffusers/metadiffusers.mdx": _DIFFUSERS,
    "site/src/content/docs/es/materials/diffusers/metadiffusers.mdx": _DIFFUSERS,
    "src/phonometry/environment/assessment/spain.py": _RD1367,
    "site/src/content/docs/reference/api/environment/spain.md": _RD1367,
    "docs/environment/assessment/spanish-noise-regulation.md": _RD1367,
    "site/src/content/docs/environment/assessment/spanish-noise-regulation.mdx": (
        _RD1367
    ),
    "site/src/content/docs/es/environment/assessment/spanish-noise-regulation.mdx": (
        _RD1367
    ),
}


#: Letters that keep one meaning under several bases, each family keyed on what
#: the letter means. A member is a ``(base, subscript)`` pair as
#: :func:`sightings` reads it; a member whose subscript is a run of letters
#: names the run whose last letter is the shared one (the r of ``FTr``), and
#: is read only to be held against its family, as :data:`_LINKED_RUNS` says.
LINKED: dict[str, frozenset[tuple[str, str]]] = {
    (
        'the r of "Beurteilung" in DIN 4150-2:1999-06 (6.2, Table 1, Formulae '
        "(4a), (4b) and (A.3)) and E DIN 4150-2:2023-08 (6.5.3.2, Formula (6)), "
        "printed upright in every one of them"
    ): frozenset({("KB", "FTr"), ("A", "r"), ("T", "r"), ("N", "r")}),
}

#: The members of :data:`LINKED` whose subscript is a run of letters. The
#: single-letter reading passes runs over, so these are recorded by name.
_LINKED_RUNS = frozenset(
    member for members in LINKED.values() for member in members if len(member[1]) > 1
)

#: Letter runs that are one quantity symbol, with the slope the corpus sets
#: each in wherever it is the base of a symbol, and why. Unlike the file rule,
#: this one holds across the whole corpus: the sources of a base like this
#: disagree with each other, so the corpus has chosen one of them, and a file
#: that sets the other has left the choice rather than stated a meaning. A run
#: inside a subscript is not read here: the KB weighting names the filter of
#: :math:`H_\mathrm{KB}` in DIN 4150-2, Formula (1), and is a word there.
BASES: dict[str, tuple[str, str]] = {
    "KB": (
        "italic",
        "the weighted vibration severity, printed with an italic KB by "
        "DIN 4150-2:1999-06 (3.4 to 3.6, PDF page 3), E DIN 4150-2:2023-08, "
        "DIN 45672-2:1995-07 and E DIN 45672-3:2023-02; the list of symbols "
        "of DIN 45669-1:2010-09 (Clause 4, PDF page 10) sets it upright, and "
        "the corpus follows DIN 4150-2",
    ),
}

#: The commands that set their argument upright, as a page or a figure label
#: writes them. ``\rm`` is a switch rather than a command with an argument and
#: is read as one when it opens a group (``{\rm KB}``).
_UPRIGHT_WRAPPERS = frozenset(
    {"mathrm", "text", "textrm", "textup", "operatorname", "mathsf", "mathup", "rm"}
)

#: What a running index is written with in this corpus: i, j and k, alone or
#: paired, as the path ij of a flanking sum is.
_INDEX_RUN = re.compile(r"[ijk]{1,2}")

#: The operators whose subscript is the index they run over: the sum and the
#: product as a page writes them, and the Σ a plate draws, which
#: :func:`_base_symbol` names as a page would.
_RUNNING_OPERATORS = frozenset({"\\sum", "\\prod", "\\Sigma"})

#: The errata register, both editions and its site page, which quotes what a
#: print sets, upright indices included, and so is not held to
#: :func:`index_slips`. Matched on the file name alone.
_TRANSCRIPTIONS = re.compile(r"(?:^|/)errata(?:\.es)?\.mdx?$", re.IGNORECASE)

#: A cheap test for an image that may carry a running index: a sum, or a
#: subscript with a comma in it, braced or wrapped. An image without one is not
#: parsed for them.
_MAY_INDEX = re.compile(r"Σ_|\\(?:sum|prod)_|_(?:\\(?:mathrm|text))?\{\{?[^{}]*,")


def _base_slopes(region: str) -> list[tuple[str, str]]:
    r"""``(base, slope)`` for each run of :data:`BASES` on the baseline of *region*.

    A small reading of TeX, enough to tell where a run stands: a group opened
    by ``_`` or ``^`` is a script, and so is everything inside it; a group
    opened by an upright command (:data:`_UPRIGHT_WRAPPERS`) is upright, and
    so is everything inside it. ``\mathrm{KB}_\mathrm{F}`` is an upright base,
    ``KB_\mathrm{F}`` an italic one, and the KB of ``H_\mathrm{KB}`` or
    ``L_{v,KB}`` is a subscript and is passed over.
    """
    found: list[tuple[str, str]] = []
    # Each open group: (is a script, is upright).
    stack: list[tuple[bool, bool]] = [(False, False)]
    pending_script = False
    pending_upright = False
    i = 0
    while i < len(region):
        ch = region[i]
        script, upright = stack[-1]
        if ch == "\\":
            j = i + 1
            while j < len(region) and region[j].isalpha():
                j += 1
            name = region[i + 1 : j] or region[i + 1 : i + 2]
            j = max(j, i + 2)
            if name in _UPRIGHT_WRAPPERS:
                if name == "rm":
                    stack[-1] = (script, True)
                else:
                    pending_upright = True
            elif pending_script:
                # A command standing alone as the whole script (``_\max``).
                k = j
                while k < len(region) and region[k] == " ":
                    k += 1
                if k >= len(region) or region[k] != "{":
                    pending_script = False
            i = j
            continue
        if ch == "{":
            stack.append((script or pending_script, upright or pending_upright))
            pending_script = pending_upright = False
        elif ch == "}":
            if len(stack) > 1:
                stack.pop()
        elif ch in "_^":
            pending_script = True
        elif ch.isascii() and ch.isalpha():
            j = i
            while j < len(region) and region[j].isascii() and region[j].isalpha():
                j += 1
            if pending_script:
                # A bare script takes one character, the rest of the run is
                # back on the level the script hangs from.
                pending_script = False
                i += 1
                continue
            run = region[i:j]
            if not script and run in BASES:
                found.append((run, "upright" if upright else "italic"))
            i = j
            continue
        elif not ch.isspace():
            pending_script = False
        i += 1
    return found


def base_sightings(text: str, suffix: str) -> Sightings:
    """Every run of :data:`BASES` *text* sets as a base, by slope and line.

    Keyed ``(base, "")`` so that it reads like :func:`sightings`.
    """
    found: Sightings = collections.defaultdict(lambda: collections.defaultdict(list))
    for offset, region in tex_regions(text, suffix):
        line = text.count("\n", 0, offset) + 1
        for base, slope in _base_slopes(region):
            found[(base, "")][slope].append(line)
    return found


def math_regions(text: str, suffix: str) -> list[tuple[int, str]]:
    r"""``(offset, snippet)`` for every mathematics region of *text*.

    ``$$...$$`` and ``$...$`` in every file kind, plus the reStructuredText
    ``:math:`...``` roles and ``.. math::`` blocks the docstrings use. On a
    page an inline formula may wrap onto the next line of its paragraph, so
    its dollars are paired across one line break, never across a blank line:
    paired line by line, the closing dollar of a wrapped formula was taken for
    an opening one, and the formula after it was read as text. In a module a
    dollar belongs to one string on one line, and is paired there.
    """
    out: list[tuple[int, str]] = [
        (m.start(1), m.group(1)) for m in re.finditer(r"\$\$(.+?)\$\$", text, re.DOTALL)
    ]
    inline = _INLINE_LINE if suffix == ".py" else _INLINE_PARAGRAPH
    out.extend((m.start(1), m.group(1)) for m in inline.finditer(text))
    if suffix == ".py":
        out.extend(
            (m.start(1), m.group(1))
            for m in re.finditer(r":math:`(.+?)`", text, re.DOTALL)
        )
        out.extend(_math_blocks(text))
    return out


#: The line that opens a reStructuredText math block, and its indentation.
_MATH_DIRECTIVE = re.compile(r"^([ \t]*)\.\. math::[ \t]*$", re.MULTILINE)


def _math_blocks(text: str) -> list[tuple[int, str]]:
    """``(offset, body)`` of every ``.. math::`` block of *text*.

    A block runs on for as long as its lines are indented past the
    directive, blank lines included: a block of two equations sets them in
    two paragraphs, and the second is as much mathematics as the first.
    Ending the block at its first blank line read the first equation alone.
    """
    out: list[tuple[int, str]] = []
    for match in _MATH_DIRECTIVE.finditer(text):
        indent = len(match.group(1).expandtabs())
        start = match.end() + 1
        end = start
        for line in text[start:].splitlines(keepends=True):
            stripped = line.strip()
            if stripped and len(line) - len(line.lstrip()) <= indent:
                break
            end += len(line)
        out.append((start, text[start:end].rstrip()))
    return out


#: An inline formula: on one line in a module, and within one paragraph on a
#: page, where a single line break may fall inside it.
_INLINE_LINE = re.compile(r"(?<![$\\])\$(?!\$)([^$\n]+?)\$(?!\$)")
_INLINE_PARAGRAPH = re.compile(
    r"(?<![$\\])\$(?!\$)((?:[^$\n]|\n(?![ \t]*\n))+?)\$(?!\$)"
)

#: A run that is a regex or its replacement rather than a label: a capture
#: group, a digit class opening a group, or a backreference is not
#: mathematics, and the Spanish translation tables are made of these. ``(\d``
#: counts only where no letter follows, since ``(\delta`` and ``(\dfrac`` are
#: TeX. A doubled backslash is not on the list: in a formula it is the row
#: break of a ``cases`` or ``aligned`` block, and taking it for a pattern hid
#: every such block from both gates.
_PATTERN_SHAPE = re.compile(r"\(\.\+\)|\(\.\*\)|\(\\d(?![A-Za-z])|\\\d")

#: A command whose backslash is doubled: the label of a plain (not raw) Python
#: string, ``"$\\mathrm{e}^{x}$"``, or such a string quoted in a page's
#: snippet. It is the same TeX with every backslash written twice.
_ESCAPED = re.compile(r"\\\\[A-Za-z]")


def tex_regions(text: str, suffix: str) -> list[tuple[int, str]]:
    r"""The mathematics of *text* as TeX: :func:`math_regions` without the
    regex sources, with the doubled backslashes of a plain string undone.

    Undoing them keeps every line break, so a line counted inside the region
    is the line of the file.
    """
    out: list[tuple[int, str]] = []
    for offset, region in math_regions(text, suffix):
        if _PATTERN_SHAPE.search(region):
            continue
        if _ESCAPED.search(region):
            region = region.replace("\\\\", "\\")
        out.append((offset, region))
    return out


#: ``base_subscript``: a Greek command or a run of letters, an optional prime,
#: then the subscript, braced or bare. The prime stays with the base, so the
#: apparent quantity :math:`R'` and the quantity :math:`R` are two symbols, and
#: so does the whole run: the transmission loss ``TL_n``, the signal-to-noise
#: ratio ``SNR_s`` and the vibration rating ``KB_F`` are symbols of their own,
#: not an ``L``, an ``R`` or a ``B`` carrying a subscript. A plotting snippet that
#: formats its label writes the braces of an upright subscript twice
#: (``rf"$f_\mathrm{{e}}$ = {f:g} Hz"``), and that is read as the upright
#: subscript it renders.
_SUBSCRIPTED = re.compile(
    r"(\\[A-Za-z]+|[A-Za-z]+)('*)"
    r"_(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\\(?:mathrm|text)\{\{[^{}]*\}\}"
    r"|\\mathrm\{[^{}]*\}|\\text\{[^{}]*\}|.)"
)

#: A subscript, or one component of one, set upright the two ways this corpus
#: writes one. The wrapper may hold the whole comma-separated run
#: (``L_\mathrm{n,w,eq}``) or one component of it (``\alpha_{\mathrm{s},i}``).
_UPRIGHT = re.compile(r"^\\(?:mathrm|text)\{\{?([^{}]*)\}?\}$")

#: The two shapes of one Greek letter are one symbol: a page writes the
#: epsilon of a random error as ``\varepsilon`` or ``\epsilon`` and a plate
#: draws one glyph for both, so the comparison is made on the plain name.
_GREEK_SHAPES = {
    "\\varepsilon": "\\epsilon",
    "\\varphi": "\\phi",
    "\\vartheta": "\\theta",
    "\\varrho": "\\rho",
    "\\varsigma": "\\sigma",
    "\\varpi": "\\pi",
}

#: A bare letter, which inside mathematics is italic.
_ITALIC = re.compile(r"^[A-Za-z]$")

#: Where a symbol was written, slope by slope: ``{(base, sub): {slope: lines}}``.
Sightings = dict[tuple[str, str], dict[str, list[int]]]


def _components(body: str) -> list[str]:
    r"""The comma-separated components of a subscript, read at brace depth zero.

    A comma inside an upright wrapper belongs to the wrapper:
    ``D_{I,\mathrm{n,e}}`` has two components, the italic ``I`` and the
    upright run ``\mathrm{n,e}``. Split on every comma, the run came apart into
    ``\mathrm{n`` and ``e}``, which read as no letter and as nothing upright.
    """
    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(body):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(body[start:index].strip())
            start = index + 1
    parts.append(body[start:].strip())
    return parts


def _flat_components(sub: str) -> list[tuple[str, bool]]:
    r"""The components of the subscript *sub* in order, each with its slope.

    ``(component, upright)``, read as :func:`sightings` reads them: where the
    upright command wraps the whole run (``\mathrm{v,i}``) every component is
    upright, and a run the command wraps inside braces
    (``{\mathrm{v},i}``) is upright while what stands beside it bare is not.
    """
    whole = _UPRIGHT.match(sub.strip())
    if whole:
        return [(part.strip(), True) for part in whole.group(1).split(",")]
    out: list[tuple[str, bool]] = []
    for part in _components(sub):
        wrapped = _UPRIGHT.match(part)
        if wrapped:
            out.extend((inner.strip(), True) for inner in wrapped.group(1).split(","))
        else:
            out.append((part, False))
    return out


def _subscripts(region: str) -> Iterator[tuple[str, str, str]]:
    """``(symbol, subscript, as written)`` for each subscripted symbol of *region*."""
    for match in _SUBSCRIPTED.finditer(region):
        base, prime, raw = match.group(1), match.group(2), match.group(3)
        base = _GREEK_SHAPES.get(base, base)
        sub = raw[1:-1] if raw.startswith("{") else raw
        yield base + prime, sub, match.group(0)


def sightings(text: str, suffix: str) -> Sightings:
    r"""Every one-letter subscript of *text*, by symbol and by slope.

    A comma-separated subscript is read component by component, since that is
    how a reader reads it: :math:`\alpha_{\mathrm{s},i}` is the Sabine
    absorption of surface *i*, one abbreviation and one index, and the letter
    that matters is the one being compared. Where the upright command wraps the
    whole run, as ``L_\mathrm{n,w,eq}`` does, every component of it is upright,
    and so is every component of a run the command wraps inside a braced
    subscript, as the ``n`` and the ``e`` of ``D_{I,\mathrm{n,e}}``.
    Any component that is not a single letter is passed over: a digit, a
    weighting prefix and a word are not what this is about.
    """
    found: Sightings = collections.defaultdict(lambda: collections.defaultdict(list))
    for offset, region in tex_regions(text, suffix):
        line = text.count("\n", 0, offset) + 1
        for symbol, sub, _ in _subscripts(region):
            for part, upright in _flat_components(sub):
                if _ITALIC.match(part) or (symbol, part) in _LINKED_RUNS:
                    slope = "upright" if upright else "italic"
                    found[(symbol, part)][slope].append(line)
    return found


def _upright_indices(symbol: str, sub: str) -> list[str]:
    r"""The running indices the subscript *sub* of *symbol* sets upright.

    The subscript of a sum is its index, up to an ``=`` (``\sum_{i=1}``),
    where it is one letter: ``\sum_\mathrm{Zug}`` runs over the named train
    categories of DIN 4150-2 and is a word. Elsewhere an index is an i, j or
    k that follows another component (``L_{\mathrm{v},i}``); one that opens
    the subscript is the impact level ``L_\mathrm{i}`` as often as an index,
    and is left to the file rule.
    """
    if symbol in _RUNNING_OPERATORS:
        index = sub.split("=", 1)[0].strip()
        wrapped = _UPRIGHT.match(index)
        if wrapped and _ITALIC.match(wrapped.group(1).strip()):
            return [wrapped.group(1).strip()]
        return []
    return [
        part
        for k, (part, upright) in enumerate(_flat_components(sub))
        if k and upright and _INDEX_RUN.fullmatch(part)
    ]


#: A running index set upright: ``(symbol as written, index, where)``, the
#: place a line of a file or the label of an image.
Slip = tuple[str, str, int | str]


def index_slips(text: str, suffix: str) -> list[Slip]:
    """Every running index *text* sets upright, with the symbol and line."""
    out: list[Slip] = []
    for offset, region in tex_regions(text, suffix):
        line = text.count("\n", 0, offset) + 1
        for symbol, sub, written in _subscripts(region):
            out.extend(
                (written, index, line) for index in _upright_indices(symbol, sub)
            )
    return out


#: Where the generators write the plates and the figures, and where every page
#: embeds them from.
PLATES = ".github/images"

#: An image a page embeds from :data:`PLATES`, by its base name. A page names
#: the light English file and the site derives the dark and the Spanish twins
#: from it, so the suffixes are read off and the language chosen here. The
#: plates and the figures share the directory; :func:`_image` tells them apart.
_IMAGE_REF = re.compile(r"\.github/images/([A-Za-z0-9_]+?)(?:_es)?(?:_dark)?\.svg")

#: How a plate opens, and a figure never does: the canvas writes the root
#: element first, where matplotlib writes an XML declaration.
_PLATE_HEAD = '<svg xmlns="http://www.w3.org/2000/svg" width="'

#: One label of a plate: the source string the composer was handed, kept in an
#: XML comment, then the glyph groups it wrote for that string, one per styled
#: run and face, in the order of the string.
_PLATE_LABEL = re.compile(
    r"<!-- (.*?) -->((?:<g [^>]*>(?:<use [^>]*/>)*</g>)*)", re.DOTALL
)

#: One glyph group: its baseline, its scale (a script is set smaller than the
#: label it belongs to) and its glyphs.
_PLATE_GROUP = re.compile(
    r'<g [^>]*transform="translate\([-\d.]+ ([-\d.]+)\) scale\(([\d.e-]+) [^)]*\)">'
    r"((?:<use [^>]*/>)*)</g>"
)

#: A glyph, by the id the plate's atlas stores it under: the face file the
#: composer took it from, then the glyph number. The face is all this needs:
#: the composer sets a letter italic by taking it from an oblique face.
_PLATE_GLYPH = re.compile(r'<use href="#([^"]*)-[0-9a-f]+"')

#: A script group is set at 0.70 of the size of what it hangs from, and the
#: labels never mix sizes otherwise, so anything clearly smaller than the
#: largest group of a label is a script, and anything clearly smaller than a
#: script (0.49 of the label, the subscripted level inside an exponent) is a
#: script of a script. The second bound sits halfway between the two scales.
_SCRIPT_RATIO = 0.85
_NESTED_RATIO = 0.595

#: How a page writes a base the plates write as a glyph: a Greek letter as its
#: command, a prime as an apostrophe.
_PRIMES = {"′": "'", "″": "''"}

#: A character's script level, as the path of markers that put it there: ""
#: on the baseline, "_" in a subscript, "^" in a superscript, "^_" in the
#: subscript of a superscript (the ``i`` of ``10^{L_i/10}``).
Level = str


def _is_ascii_letter(char: str) -> bool:
    """Whether *char* is one of the letters a base run is made of."""
    return char.isascii() and char.isalpha()


def _base_symbol(chars: list[tuple[str, Level]], end: int) -> str | None:
    r"""The symbol a script at *end* attaches to, as a page would write it.

    The base sits one level up from the script, on the baseline for a
    subscript and in the exponent for the subscript of an exponent. ``None``
    for anything a page cannot write the same way: a base carrying a
    combining mark (a page writes ``\bar{L}``, which the reading of
    :func:`sightings` passes over too), or no letter at all. A run of letters
    is one base, as :data:`_SUBSCRIPTED` reads it on a page.
    """
    parent = chars[end][1][:-1]
    prime = ""
    k = end - 1
    while k >= 0 and chars[k][0] in _PRIMES and chars[k][1] == parent:
        prime = _PRIMES[chars[k][0]] + prime
        k -= 1
    if k < 0 or chars[k][1] != parent:
        return None
    letter = chars[k][0]
    if _is_ascii_letter(letter):
        start = k
        while (
            start > 0
            and chars[start - 1][1] == parent
            and _is_ascii_letter(chars[start - 1][0])
        ):
            start -= 1
        return "".join(c for c, _ in chars[start : k + 1]) + prime
    name = unicodedata.name(letter, "")
    if name.startswith("GREEK SMALL LETTER "):
        return "\\" + name.removeprefix("GREEK SMALL LETTER ").lower() + prime
    if name.startswith("GREEK CAPITAL LETTER "):
        return "\\" + name.removeprefix("GREEK CAPITAL LETTER ").title() + prime
    return None


def _close_brace(run: str, opening: int) -> int:
    """The index of the ``}`` closing the ``{`` at *opening*, or -1."""
    depth = 0
    for index in range(opening, len(run)):
        if run[index] == "{":
            depth += 1
        elif run[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _math_levels(run: str, level: Level, out: list[tuple[str, Level]]) -> None:
    """Append each character of the math *run* with its level, *level* first."""
    i = 0
    while i < len(run):
        ch = run[i]
        if ch in "_^" and i + 1 < len(run):
            if run[i + 1] == "{":
                end = _close_brace(run, i + 1)
                end = len(run) if end < 0 else end
                payload, i = run[i + 2 : end], end + 1
            else:
                payload, i = run[i + 1], i + 2
            _math_levels(payload, level + ch, out)
        else:
            out.append((ch, level))
            i += 1


def _label_levels(source: str) -> list[tuple[str, Level]]:
    """Each character of a plate label with its :data:`Level`.

    The composer's own reading of the markup, without its style decisions:
    outside ``$...$`` everything sits on the baseline, and inside, ``_`` and
    ``^`` take the braced run or the single character after them, one level
    further down or up, a script inside a script included.
    """
    out: list[tuple[str, Level]] = []
    for k, segment in enumerate(source.split("$")):
        if k % 2 == 0:
            out.extend((ch, "") for ch in segment)
        else:
            _math_levels(segment, "", out)
    return out


def _chunks(levels: list[Level]) -> list[tuple[Level, int]]:
    """``(level, count)`` for each run of one level, adjacent runs merged."""
    out: list[tuple[Level, int]] = []
    for level in levels:
        if out and out[-1][0] == level:
            out[-1] = (level, out[-1][1] + 1)
        else:
            out.append((level, 1))
    return out


def _drawn_levels(
    groups: list[tuple[float, float, list[bool]]],
) -> list[tuple[Level, list[bool]]]:
    """The :data:`Level` of each glyph group, adjacent groups of one level merged.

    The scale says how deep a group sits and the baseline whether it hangs
    below or rises above what it belongs to: the label's baseline for a
    script, the script before it for a script of a script.
    """
    size = max(scale for _, scale, _ in groups)
    baseline = next(y for y, scale, _ in groups if scale == size)
    parents: dict[int, tuple[float, Level]] = {0: (baseline, "")}
    drawn: list[tuple[Level, list[bool]]] = []
    for y, scale, faces in groups:
        ratio = scale / size
        depth = 0 if ratio > _SCRIPT_RATIO else (1 if ratio > _NESTED_RATIO else 2)
        if depth == 0:
            level = ""
        else:
            parent_y, parent = parents.get(depth - 1, (baseline, ""))
            level = parent + ("_" if y > parent_y else "^")
            parents[depth] = (y, level)
        if drawn and drawn[-1][0] == level:
            drawn[-1][1].extend(faces)
        else:
            drawn.append((level, list(faces)))
    return drawn


def _read_label(source: str, body: str) -> list[tuple[str, Level, bool | None]] | None:
    """``(character, level, italic)`` along one label, or ``None`` if unreadable.

    Blank characters draw nothing, so the drawn glyphs line up with the
    label's other characters. A script is short and is held glyph for glyph.
    A baseline run is held glyph for glyph too where it can be, which is what
    the base of a symbol is read from (:data:`BASES`); where a ligature has
    drawn two of its letters as one glyph it cannot, and its characters keep
    ``None``.
    """
    chars = _label_levels(source)
    inked = [i for i, (ch, _) in enumerate(chars) if not ch.isspace()]
    groups: list[tuple[float, float, list[bool]]] = [
        (
            float(m.group(1)),
            float(m.group(2)),
            ["Oblique" in face for face in _PLATE_GLYPH.findall(m.group(3))],
        )
        for m in _PLATE_GROUP.finditer(body)
    ]
    if not groups:
        return None
    drawn = _drawn_levels(groups)
    written = _chunks([chars[i][1] for i in inked])
    if [level for level, _ in written] != [level for level, _ in drawn]:
        return None
    out: list[tuple[str, Level, bool | None]] = [(ch, lv, None) for ch, lv in chars]
    start = 0
    for (level, count), (_, faces) in zip(written, drawn, strict=True):
        if not level and count == len(faces):
            # A baseline run with no ligature in it lines up glyph for glyph,
            # which is what the base of a symbol is read from.
            for i, italic in zip(inked[start : start + count], faces, strict=True):
                out[i] = (chars[i][0], level, italic)
        elif level:
            if count != len(faces):
                # A ligature (the ff of "eff" and "diff") draws two letters
                # as one glyph, and it only forms inside one run, so a script
                # drawn in a single face still says what every letter is.
                if len(set(faces)) != 1:
                    return None
                faces = faces[:1] * count
            for i, italic in zip(inked[start : start + count], faces, strict=True):
                out[i] = (chars[i][0], level, italic)
        start += count
    return out


#: What a plate sets, slope by slope: ``{(base, sub): {slope: [label, ...]}}``.
PlateSightings = dict[tuple[str, str], dict[str, list[str]]]


def plate_sightings(svg: str) -> tuple[PlateSightings, list[str]]:
    """Every one-letter subscript a plate draws, and the labels it cannot read.

    Read as :func:`sightings` reads a page: a comma-separated subscript
    component by component, and only the components that are one letter. A
    subscript inside an exponent is read like any other, against the symbol
    in the exponent it hangs from. A label whose glyphs do not line up with
    its source is returned by name rather than skipped, so a plate the gate
    cannot read fails it instead of passing unread.
    """
    found: PlateSightings = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    unreadable: list[str] = []
    for source, base, components in _plate_scripts(svg, unreadable):
        for letters in components:
            run = "".join(c[0] for c in letters)
            if len(letters) == 1 and _ITALIC.match(letters[0][0]):
                slope = "italic" if letters[0][2] else "upright"
                found[(base, letters[0][0])][slope].append(source)
            elif (base, run) in _LINKED_RUNS and len({c[2] for c in letters}) == 1:
                slope = "italic" if letters[-1][2] else "upright"
                found[(base, run)][slope].append(source)
    return found, unreadable


#: One component of a script a plate draws: its inked characters, each with
#: its level and whether it is drawn from the oblique face.
PlateComponent = list[tuple[str, Level, bool | None]]


def _plate_scripts(
    svg: str, unreadable: list[str]
) -> Iterator[tuple[str, str, list[PlateComponent]]]:
    """``(label, base, components)`` for each subscript a plate draws.

    A subscript is split at its commas into components, blanks dropped, and
    hangs from the symbol :func:`_base_symbol` names; a subscript that hangs
    from nothing a page could write is passed over. A label whose glyphs do
    not line up with its source is appended to *unreadable* instead.
    """
    for match in _PLATE_LABEL.finditer(svg):
        source = html.unescape(match.group(1))
        if "$" not in source or "_" not in source:
            continue
        chars = _read_label(source, match.group(2))
        if chars is None:
            unreadable.append(source)
            continue
        i = 0
        while i < len(chars):
            level = chars[i][1]
            if not level.endswith("_"):
                i += 1
                continue
            j = i
            while j < len(chars) and chars[j][1] == level:
                j += 1
            base = _base_symbol([(c, lv) for c, lv, _ in chars], i)
            components: list[PlateComponent] = [[]]
            for item in chars[i:j]:
                if item[0] == ",":
                    components.append([])
                elif not item[0].isspace():
                    components[-1].append(item)
            if base:
                yield source, base, components
            i = j


def plate_index_slips(svg: str) -> list[Slip]:
    """Every running index a plate draws upright, by label.

    Read as :func:`index_slips` reads a page: the one letter a Σ runs over,
    up to an ``=``, and an i, j or k drawn after another component of a
    subscript. A label the plate reading cannot line up is reported by
    :func:`plate_sightings`, not here.
    """
    out: list[Slip] = []
    for source, base, components in _plate_scripts(svg, []):
        spelled = ["".join(c[0] for c in letters) for letters in components]
        written = f"{base}_{{{','.join(spelled)}}}"
        if base in _RUNNING_OPERATORS:
            index = list(itertools.takewhile(lambda c: c[0] != "=", components[0]))
            found = [index] if len(index) == 1 and _ITALIC.match(index[0][0]) else []
        else:
            found = [
                letters
                for k, letters in enumerate(components)
                if k and _INDEX_RUN.fullmatch(spelled[k])
            ]
        out.extend(
            (written, "".join(c[0] for c in letters), source)
            for letters in found
            if all(c[2] is False for c in letters)
        )
    return out


def _in_math(source: str) -> list[bool]:
    """Whether each character :func:`_label_levels` reads is inside ``$...$``."""
    flags: list[bool] = []
    for k, segment in enumerate(source.split("$")):
        if k % 2 == 0:
            flags.extend(False for _ in segment)
        else:
            inner: list[tuple[str, Level]] = []
            _math_levels(segment, "", inner)
            flags.extend(True for _ in inner)
    return flags


def plate_bases(svg: str) -> tuple[PlateSightings, list[str]]:
    """Every run of :data:`BASES` a plate draws as a base, and what it cannot read.

    A run counts where it stands on the baseline of a ``$...$`` span, as a
    whole run of letters. A label whose baseline cannot be lined up glyph for
    glyph (a ligature) and that carries one is returned by name, so an
    unreadable plate fails rather than passing unread.
    """
    found: PlateSightings = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    unreadable: list[str] = []
    for match in _PLATE_LABEL.finditer(svg):
        source = html.unescape(match.group(1))
        if "$" not in source or not any(base in source for base in BASES):
            continue
        chars = _read_label(source, match.group(2))
        math = _in_math(source)
        if chars is None or len(math) != len(chars):
            unreadable.append(source)
            continue
        i = 0
        while i < len(chars):
            if not (math[i] and chars[i][1] == "" and _is_ascii_letter(chars[i][0])):
                i += 1
                continue
            j = i
            while (
                j < len(chars)
                and math[j]
                and chars[j][1] == ""
                and _is_ascii_letter(chars[j][0])
            ):
                j += 1
            run = "".join(c for c, _, _ in chars[i:j])
            if run in BASES:
                faces = {italic for _, _, italic in chars[i:j]}
                if None in faces:
                    unreadable.append(source)
                else:
                    slope = "italic" if faces == {True} else "upright"
                    found[(run, "")][slope].append(source)
            i = j
    return found, unreadable


#: One text a figure draws: matplotlib writes the string it was handed, its
#: mathtext source included, in an XML comment ahead of the glyphs.
_FIGURE_TEXT = re.compile(r"<!-- (.*?) -->", re.DOTALL)


def figure_sightings(svg: str) -> PlateSightings:
    r"""Every one-letter subscript a matplotlib figure draws.

    mathtext sets a bare letter italic and a ``\mathrm`` run upright, so the
    slope a reader sees is the slope the source writes, and the source is in
    the comment: each text is read as :func:`sightings` reads a page.
    """
    found: PlateSightings = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for match in _FIGURE_TEXT.finditer(svg):
        source = html.unescape(match.group(1))
        if "$" not in source or "_" not in source:
            continue
        for symbol, slopes in sightings(source, ".md").items():
            for slope in slopes:
                found[symbol][slope].append(source)
    return found


def figure_bases(svg: str) -> PlateSightings:
    """Every run of :data:`BASES` a matplotlib figure sets as a base.

    Read from the comments as :func:`base_sightings` reads a page.
    """
    found: PlateSightings = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    for match in _FIGURE_TEXT.finditer(svg):
        source = html.unescape(match.group(1))
        if "$" not in source or not any(base in source for base in BASES):
            continue
        for symbol, slopes in base_sightings(source, ".md").items():
            for slope in slopes:
                found[symbol][slope].append(source)
    return found


def figure_index_slips(svg: str) -> list[Slip]:
    """Every running index a matplotlib figure sets upright, by text.

    Read from the comments as :func:`index_slips` reads a page.
    """
    out: list[Slip] = []
    for match in _FIGURE_TEXT.finditer(svg):
        source = html.unescape(match.group(1))
        if "$" not in source or "_" not in source:
            continue
        out.extend(
            (written, index, source) for written, index, _ in index_slips(source, ".md")
        )
    return out


@dataclasses.dataclass(frozen=True)
class Image:
    """What one image sets: its subscripts, its bases, the running indices it
    sets upright, and what it cannot read.
    """

    symbols: PlateSightings
    bases: PlateSightings
    slips: list[Slip]
    unreadable: list[str]


#: What each image file holds, as :func:`_image` reads it, or ``None`` for a
#: file that is not there.
_IMAGE_CACHE: dict[pathlib.Path, Image | None] = {}


def _image(path: pathlib.Path) -> Image | None:
    """What the image at *path* sets, and the labels that keep it from being read.

    A plate is read from its glyphs (:func:`plate_sightings`,
    :func:`plate_bases`, :func:`plate_index_slips`) and a figure from its
    comments (:func:`figure_sightings`, :func:`figure_bases`,
    :func:`figure_index_slips`), which are always readable. ``None`` if
    there is no such file.
    """
    if path not in _IMAGE_CACHE:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            _IMAGE_CACHE[path] = None
        else:
            if text.startswith(_PLATE_HEAD):
                symbols, unreadable = plate_sightings(text)
                bases, unread_bases = plate_bases(text)
                _IMAGE_CACHE[path] = Image(
                    symbols,
                    bases,
                    plate_index_slips(text),
                    list(dict.fromkeys(unreadable + unread_bases)),
                )
            else:
                _IMAGE_CACHE[path] = Image(
                    figure_sightings(text),
                    figure_bases(text),
                    figure_index_slips(text),
                    [],
                )
    return _IMAGE_CACHE[path]


def _embedded_images(
    text: str, path: pathlib.Path, plates: pathlib.Path
) -> list[tuple[str, Image]]:
    """``(file name, reading)`` for each image *text* embeds that *plates* holds.

    A Spanish page (one under an ``es`` directory) is held against the Spanish
    image, and falls back to the English one where there is no Spanish file.
    """
    spanish = "es" in path.parts
    out: list[tuple[str, Image]] = []
    for name in sorted(set(_IMAGE_REF.findall(text))):
        plate = f"{name}_es.svg" if spanish else f"{name}.svg"
        read = _image(plates / plate)
        if read is None and spanish:
            # An image drawn once for both languages has no Spanish file.
            plate = f"{name}.svg"
            read = _image(plates / plate)
        if read is None:
            # An image this directory does not hold: a broken embed is the
            # link checker's to report, not this gate's.
            continue
        out.append((plate, read))
    return out


def embedded(
    text: str, path: pathlib.Path, plates: pathlib.Path
) -> tuple[dict[tuple[str, str], dict[str, list[str]]], list[str]]:
    """What the images *text* embeds set, and what keeps one from being read.

    Each sighting is a location, ``diagram_x.svg: "label"``; a Spanish page
    (one under an ``es`` directory) is held against the Spanish image.
    """
    found: dict[tuple[str, str], dict[str, list[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    problems: list[str] = []
    for plate, read in _embedded_images(text, path, plates):
        problems.extend(
            f"cannot line up the glyphs of {plate} label {label!r}"
            for label in read.unreadable
        )
        for symbol, slopes in read.symbols.items():
            for slope, labels in slopes.items():
                found[symbol][slope].extend(
                    f'{plate}: "{label}"' for label in dict.fromkeys(labels)
                )
    return found, problems


def collect(roots: list[str], *, everything: bool = False) -> list[pathlib.Path]:
    """The files to read, in a stable order.

    *everything* keeps the files the file scope does not apply to
    (:data:`_EXCLUDED`), which :data:`BASES` is still read in.
    """
    paths: list[pathlib.Path] = []
    for root in roots:
        target = pathlib.Path(root)
        if target.is_file():
            paths.append(target)
            continue
        paths.extend(
            p
            for p in sorted(target.rglob("*"))
            if p.suffix in _SUFFIXES and p.is_file()
        )
    # Matched on the posix spelling, not on ``str(p)``: the pattern writes its
    # directory anchors with forward slashes, and on Windows ``str`` hands back
    # backslashes, so every exclusion silently stopped matching there and the
    # drawing modules were read after all. The same normalisation is why
    # ``declared`` below reads ``as_posix``.
    if everything:
        return paths
    return [p for p in paths if not _EXCLUDED.search(p.as_posix())]


def declared(path: pathlib.Path) -> dict[tuple[str, str], str]:
    """The symbols *path* is registered as carrying both ways, if any."""
    posix = path.as_posix()
    for key, symbols in DECLARED.items():
        if posix == key or posix.endswith("/" + key):
            return symbols
    return {}


def _where(lines: list[int], plates: list[str]) -> str:
    """Where one slope was written: the page's lines, then the images' labels."""
    parts: list[str] = []
    if lines:
        parts.append("on line " + ", ".join(str(n) for n in sorted(set(lines))))
    parts.extend(f"in {label}" for label in dict.fromkeys(plates))
    return "; ".join(parts)


def _base_reports(
    where: str, found: Mapping[tuple[str, str], Mapping[str, Sequence[int | str]]]
) -> list[str]:
    """One report per run of :data:`BASES` *where* sets against the corpus."""
    out: list[str] = []
    for (base, _), slopes in sorted(found.items()):
        wanted, reason = BASES[base]
        for slope, places in sorted(slopes.items()):
            if slope == wanted:
                continue
            lines = [p for p in places if isinstance(p, int)]
            labels = [f'"{p}"' for p in places if isinstance(p, str)]
            out.append(
                f"  {where}\n"
                f"      {base} {slope} {_where(lines, labels)}\n"
                f"      {' ' * len(base)} is {wanted} everywhere: {reason}"
            )
    return out


def _index_reports(where: str, slips: Sequence[Slip]) -> list[str]:
    """One report per running index *where* sets upright."""
    out: list[str] = []
    for (written, index), places in itertools.groupby(
        sorted(slips, key=lambda slip: (slip[0], slip[1], str(slip[2]))),
        key=lambda slip: (slip[0], slip[1]),
    ):
        spots = [place for _, _, place in places]
        lines = [p for p in spots if isinstance(p, int)]
        labels = [f'"{p}"' for p in spots if isinstance(p, str)]
        out.append(
            f"  {where}\n"
            f"      {written}: the index {index} is upright "
            f"{_where(lines, labels)}\n"
            "      a running index is italic everywhere: ISO 80000-2 sets it "
            "as a variable, and where a standard prints every subscript in "
            "one slope the corpus follows ISO 80000-2"
        )
    return out


def _read_text(path: pathlib.Path) -> str | None:
    """The text of *path*, or ``None`` for a file that cannot be read as text."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check(
    paths: list[pathlib.Path],
    plates: pathlib.Path | None = None,
    *,
    bases_only: Iterable[pathlib.Path] = (),
    every_image: bool = False,
) -> tuple[int, list[str]]:
    """``(files read, one report per undeclared collision)``.

    *plates* is the directory the embedded plates and figures are read from,
    the repository's :data:`PLATES` by default. Every file in *paths* and
    every image they embed is also held to :data:`BASES` and to
    :func:`index_slips`, and so is every file in *bases_only*, which the file
    scope does not apply to, the errata register excepted from the index rule
    (:data:`_TRANSCRIPTIONS`), and with *every_image* every image in *plates*,
    embedded or not.
    """
    plate_dir = pathlib.Path(PLATES) if plates is None else plates
    failures: list[str] = []
    images: dict[str, Image] = {}
    for path in paths:
        text = _read_text(path)
        if text is None:
            continue
        registered = declared(path)
        prose = sightings(text, path.suffix)
        drawn, problems = embedded(text, path, plate_dir)
        failures.extend(f"  {path}\n      {problem}" for problem in problems)
        for base, sub in sorted(set(prose) | set(drawn)):
            if (base, sub) in registered:
                continue
            lines = prose.get((base, sub), {})
            labels = drawn.get((base, sub), {})
            if len(set(lines) | set(labels)) < 2:
                continue
            italic = _where(lines.get("italic", []), labels.get("italic", []))
            upright = _where(lines.get("upright", []), labels.get("upright", []))
            failures.append(
                f"  {path}\n"
                f"      {base}_{sub}: italic {italic}\n"
                f"      {' ' * len(base)}  upright {upright}"
            )
        failures.extend(
            f"  {path}\n      {problem}" for problem in _family_splits(prose, drawn)
        )
        failures.extend(_base_reports(str(path), base_sightings(text, path.suffix)))
        failures.extend(_index_reports(str(path), index_slips(text, path.suffix)))
        images.update(_embedded_images(text, path, plate_dir))
    for path in bases_only:
        text = _read_text(path)
        if text is not None:
            failures.extend(_base_reports(str(path), base_sightings(text, path.suffix)))
            if not _TRANSCRIPTIONS.search(path.as_posix()):
                failures.extend(
                    _index_reports(str(path), index_slips(text, path.suffix))
                )
    if every_image:
        for svg in sorted(plate_dir.glob("*.svg")):
            if svg.name in images:
                continue
            text = _read_text(svg)
            if text is None or not (
                any(base in text for base in BASES) or _MAY_INDEX.search(text)
            ):
                continue
            read = _image(svg)
            if read is not None:
                images[svg.name] = read
                failures.extend(
                    f"  {svg.name}\n      cannot line up the glyphs of label {label!r}"
                    for label in read.unreadable
                )
    for name, read in sorted(images.items()):
        failures.extend(_base_reports(name, read.bases))
        failures.extend(_index_reports(name, read.slips))
    return len(paths), failures


def _family_splits(
    prose: Sightings, drawn: dict[tuple[str, str], dict[str, list[str]]]
) -> list[str]:
    """One report per :data:`LINKED` family set both ways in one file."""
    out: list[str] = []
    for meaning, members in LINKED.items():
        by_slope: dict[str, list[str]] = collections.defaultdict(list)
        for base, sub in sorted(members):
            lines = prose.get((base, sub), {})
            labels = drawn.get((base, sub), {})
            for slope in set(lines) | set(labels):
                where = _where(lines.get(slope, []), labels.get(slope, []))
                by_slope[slope].append(f"{base}_{sub} {where}")
        if len(by_slope) < 2:
            continue
        out.append(
            f"one letter set two ways, {meaning}:\n"
            f"        italic: {'; '.join(by_slope['italic'])}\n"
            f"        upright: {'; '.join(by_slope['upright'])}"
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "roots",
        nargs="*",
        default=list(DEFAULT_ROOTS),
        help="files or directories to scan (default: the prose)",
    )
    parser.add_argument(
        "--plates",
        default=PLATES,
        help=(
            "directory the embedded plates and figures are read from "
            f"(default: {PLATES})"
        ),
    )
    args = parser.parse_args(argv)

    plates = pathlib.Path(args.plates)
    if not any(plates.glob("*.svg")):
        # Read from the wrong directory, every image would simply be absent
        # and the gate would pass having read none of them.
        print(f"No images in {plates}: run from the repository root.", file=sys.stderr)
        return 1
    paths = collect(args.roots)
    kept = set(paths)
    others = [p for p in collect(args.roots, everything=True) if p not in kept]
    read, failures = check(paths, plates, bases_only=others, every_image=True)
    if not failures:
        print(
            f"Every subscript is single-valued in each of {read} files "
            "and the images they embed, every "
            + ", ".join(sorted(BASES))
            + " takes the slope the corpus sets it in, and every running "
            "index is italic."
        )
        return 0

    print(
        f"{len(failures)} subscripts carry both slopes inside one file "
        "or the images it embeds, a base is set against the corpus, or a "
        "running index is upright:\n",
        file=sys.stderr,
    )
    for failure in failures:
        print(failure, file=sys.stderr)
    print(
        "\nRe-letter the index, set the lagging one the way its neighbours "
        "are set, or\ndeclare the page in DECLARED naming both meanings; set "
        "a base the way BASES\nsays and a running index italic. A plate's "
        "slope is set in\nscripts/diagrams and a figure's in scripts/figures; "
        "regenerate the image\nafter changing it.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
