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

The plates a page embeds
------------------------

A guide is not only its prose. The figures it embeds are read through the
plotting snippets on the page, and the diagram plates it embeds are read here
from the plates themselves, because a plate's source never writes a slope: the
composer in ``scripts/diagrams/canvas.py`` decides it, run by run, and the
committed SVG is the only place the decision is visible. Each label of a plate
carries its source string in an XML comment and its glyphs in groups whose ids
name the face, so the oblique face marks an italic letter without reading a
font file; :func:`plate_sightings` lines the two up. A page and the plates it
embeds are then one scope: a plate that draws $L_i$ sloped on a page whose
prose sets the impact level $L_\mathrm{i}$ upright is the page contradicting
itself, in the place a reader looks first. A Spanish page is held against the
Spanish plate, which is the file the site shows there.

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
import html
import pathlib
import re
import sys
import unicodedata

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
#: figure is, and that is read here. The builders of the diagram plates are
#: left out for another reason: their sources never write a slope, which the
#: composer in ``scripts/diagrams/canvas.py`` decides, so the plates are read
#: from the committed SVG instead, page by page (:func:`embedded`).
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
        "of the quadratic-residue diffuser, whose n counts the wells. The "
        "guide's note on symbols is about this pair, and writes the "
        "coefficient d_norm wherever it is its own"
    ),
}

DECLARED: dict[str, dict[tuple[str, str], str]] = {
    "docs/reference/glossary.md": _GLOSSARY,
    "site/src/content/docs/reference/glossary.mdx": _GLOSSARY,
    "site/src/content/docs/es/reference/glossary.mdx": _GLOSSARY,
    "docs/materials/diffusers/diffusers.md": _DIFFUSERS,
    "site/src/content/docs/materials/diffusers/diffusers.mdx": _DIFFUSERS,
    "site/src/content/docs/es/materials/diffusers/diffusers.mdx": _DIFFUSERS,
}


def math_regions(text: str, suffix: str) -> list[tuple[int, str]]:
    r"""``(offset, snippet)`` for every mathematics region of *text*.

    ``$$...$$`` and ``$...$`` in every file kind, plus the reStructuredText
    ``:math:`...``` roles and ``.. math::`` blocks the docstrings use.
    """
    out: list[tuple[int, str]] = [
        (m.start(1), m.group(1)) for m in re.finditer(r"\$\$(.+?)\$\$", text, re.DOTALL)
    ]
    out.extend(
        (m.start(1), m.group(1))
        for m in re.finditer(r"(?<![$\\])\$(?!\$)([^$\n]+?)\$(?!\$)", text)
    )
    if suffix == ".py":
        out.extend(
            (m.start(1), m.group(1))
            for m in re.finditer(r":math:`(.+?)`", text, re.DOTALL)
        )
        out.extend(
            (m.start(2), m.group(2))
            for m in re.finditer(
                r"^([ \t]*)\.\. math::[ \t]*\n(.*?)(?=\n\s*\n|\Z)",
                text,
                re.DOTALL | re.MULTILINE,
            )
        )
    return out


#: A run that is a regex or its replacement rather than a label, by the same
#: shapes ``check_mathtext.py`` recognises: a doubled backslash means "a
#: literal backslash" in a pattern, and a capture group or a backreference is
#: not mathematics. The Spanish translation tables are made of these.
_PATTERN_SHAPE = re.compile(r"\\\\|\(\.\+\)|\(\\d|\(\.\*\)|\\\d")

#: ``base_subscript``: a single letter or a Greek command, an optional prime,
#: then the subscript, braced or bare. The prime stays with the base, so the
#: apparent quantity :math:`R'` and the quantity :math:`R` are two symbols. A
#: plotting snippet that formats its label writes the braces of an upright
#: subscript twice (``rf"$f_\mathrm{{e}}$ = {f:g} Hz"``), and that is read as
#: the upright subscript it renders.
_SUBSCRIPTED = re.compile(
    r"(\\[A-Za-z]+|[A-Za-z])('*)"
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
    for offset, region in math_regions(text, suffix):
        if _PATTERN_SHAPE.search(region):
            continue
        line = text.count("\n", 0, offset) + 1
        for match in _SUBSCRIPTED.finditer(region):
            base, prime, raw = match.group(1), match.group(2), match.group(3)
            base = _GREEK_SHAPES.get(base, base)
            sub = raw[1:-1] if raw.startswith("{") else raw
            whole = _UPRIGHT.match(sub.strip())
            body = whole.group(1) if whole else sub
            parts = [p.strip() for p in body.split(",")] if whole else _components(body)
            for part in parts:
                upright = _UPRIGHT.match(part)
                if upright:
                    for inner in (p.strip() for p in upright.group(1).split(",")):
                        if _ITALIC.match(inner):
                            found[(base + prime, inner)]["upright"].append(line)
                elif _ITALIC.match(part):
                    slope = "upright" if whole else "italic"
                    found[(base + prime, part)][slope].append(line)
    return found


#: Where the generator writes the plates, and where every page embeds them from.
PLATES = ".github/images"

#: An image a page embeds from :data:`PLATES`, by its base name. A page names
#: the light English file and the site derives the dark and the Spanish twins
#: from it, so the suffixes are read off and the language chosen here. The
#: figures live in the same directory; :func:`_plate` tells the two apart.
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

#: A script group is set at 0.70 of its label's size, and the labels never
#: mix sizes otherwise, so anything clearly smaller than the largest group of
#: a label is a script.
_SCRIPT_RATIO = 0.85

#: How a page writes a base the plates write as a glyph: a Greek letter as its
#: command, a prime as an apostrophe.
_PRIMES = {"′": "'", "″": "''"}


def _base_symbol(chars: list[tuple[str, int]], end: int) -> str | None:
    r"""The symbol a script at *end* attaches to, as a page would write it.

    ``None`` for anything a page cannot write the same way: a base carrying a
    combining mark (a page writes ``\bar{L}``, which the reading of
    :func:`sightings` passes over too), or no letter at all.
    """
    prime = ""
    k = end - 1
    while k >= 0 and chars[k][0] in _PRIMES and chars[k][1] == 0:
        prime = _PRIMES[chars[k][0]] + prime
        k -= 1
    if k < 0 or chars[k][1] != 0:
        return None
    letter = chars[k][0]
    if letter.isascii() and letter.isalpha():
        return letter + prime
    name = unicodedata.name(letter, "")
    if name.startswith("GREEK SMALL LETTER "):
        return "\\" + name.removeprefix("GREEK SMALL LETTER ").lower() + prime
    if name.startswith("GREEK CAPITAL LETTER "):
        return "\\" + name.removeprefix("GREEK CAPITAL LETTER ").title() + prime
    return None


def _label_levels(source: str) -> list[tuple[str, int]]:
    """Each character of a plate label with its level: 0, 1 (sub) or -1 (sup).

    The composer's own reading of the markup, without its style decisions:
    outside ``$...$`` everything sits on the baseline, and inside, ``_`` and
    ``^`` take the braced run or the single character after them.
    """
    out: list[tuple[str, int]] = []
    for k, segment in enumerate(source.split("$")):
        if k % 2 == 0:
            out.extend((ch, 0) for ch in segment)
            continue
        i = 0
        while i < len(segment):
            ch = segment[i]
            if ch in "_^" and i + 1 < len(segment):
                level = 1 if ch == "_" else -1
                if segment[i + 1] == "{":
                    end = segment.find("}", i + 2)
                    end = len(segment) if end < 0 else end
                    payload, i = segment[i + 2 : end], end + 1
                else:
                    payload, i = segment[i + 1], i + 2
                out.extend((c, level) for c in payload)
            else:
                out.append((ch, 0))
                i += 1
    return out


def _chunks(levels: list[int]) -> list[tuple[int, int]]:
    """``(level, count)`` for each run of one level, adjacent runs merged."""
    out: list[tuple[int, int]] = []
    for level in levels:
        if out and out[-1][0] == level:
            out[-1] = (level, out[-1][1] + 1)
        else:
            out.append((level, 1))
    return out


def _read_label(source: str, body: str) -> list[tuple[str, int, bool | None]] | None:
    """``(character, level, italic)`` along one label, or ``None`` if unreadable.

    Blank characters draw nothing, so the drawn glyphs line up with the
    label's other characters. A script is short and is held glyph for glyph;
    a baseline run is not (a ligature draws two letters as one glyph), and a
    baseline style is never what is read, so it is matched as a run and its
    characters keep ``None``.
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
    size = max(scale for _, scale, _ in groups)
    baseline = next(y for y, scale, _ in groups if scale == size)
    drawn: list[tuple[int, list[bool]]] = []
    for y, scale, faces in groups:
        level = 0 if scale > _SCRIPT_RATIO * size else (1 if y > baseline else -1)
        if drawn and drawn[-1][0] == level:
            drawn[-1][1].extend(faces)
        else:
            drawn.append((level, list(faces)))
    written = _chunks([chars[i][1] for i in inked])
    if [level for level, _ in written] != [level for level, _ in drawn]:
        return None
    out: list[tuple[str, int, bool | None]] = [(ch, lv, None) for ch, lv in chars]
    start = 0
    for (level, count), (_, faces) in zip(written, drawn, strict=True):
        if level != 0:
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
    label whose glyphs do not line up with its source is returned by name
    rather than skipped, so a plate the gate cannot read fails it instead of
    passing unread.
    """
    found: PlateSightings = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    unreadable: list[str] = []
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
            if chars[i][1] != 1:
                i += 1
                continue
            j = i
            while j < len(chars) and chars[j][1] == 1:
                j += 1
            base = _base_symbol([(c, lv) for c, lv, _ in chars], i)
            component: list[tuple[str, int, bool | None]] = []
            for item in [*chars[i:j], (",", 1, None)]:
                if item[0] != ",":
                    component.append(item)
                    continue
                letters = [c for c in component if not c[0].isspace()]
                if base and len(letters) == 1 and _ITALIC.match(letters[0][0]):
                    slope = "italic" if letters[0][2] else "upright"
                    found[(base, letters[0][0])][slope].append(source)
                component = []
            i = j
    return found, unreadable


#: What each image file holds: the reading of a plate, ``"figure"`` for any
#: other image, ``None`` for a file that is not there.
_PLATE_CACHE: dict[pathlib.Path, tuple[PlateSightings, list[str]] | str | None] = {}


def _plate(path: pathlib.Path) -> tuple[PlateSightings, list[str]] | str | None:
    """:func:`plate_sightings` of *path*, ``"figure"`` for a figure, ``None`` if absent."""
    if path not in _PLATE_CACHE:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            _PLATE_CACHE[path] = None
        else:
            plate = text.startswith(_PLATE_HEAD)
            _PLATE_CACHE[path] = plate_sightings(text) if plate else "figure"
    return _PLATE_CACHE[path]


def embedded(
    text: str, path: pathlib.Path, plates: pathlib.Path
) -> tuple[dict[tuple[str, str], dict[str, list[str]]], list[str]]:
    """What the plates *text* embeds set, and what keeps one from being read.

    Each sighting is a location, ``diagram_x.svg: "label"``; a Spanish page
    (one under an ``es`` directory) is held against the Spanish plate.
    """
    spanish = "es" in path.parts
    found: dict[tuple[str, str], dict[str, list[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(list)
    )
    problems: list[str] = []
    for name in sorted(set(_IMAGE_REF.findall(text))):
        plate = f"{name}_es.svg" if spanish else f"{name}.svg"
        read = _plate(plates / plate)
        if read is None and spanish:
            # A figure drawn once for both languages has no Spanish file.
            plate = f"{name}.svg"
            read = _plate(plates / plate)
        if read is None or isinstance(read, str):
            # A figure, or an image this directory does not hold: a broken
            # embed is the link checker's to report, not this gate's.
            continue
        symbols, unreadable = read
        problems.extend(
            f"cannot line up the glyphs of {plate} label {label!r}"
            for label in unreadable
        )
        for symbol, slopes in symbols.items():
            for slope, labels in slopes.items():
                found[symbol][slope].extend(
                    f'{plate}: "{label}"' for label in dict.fromkeys(labels)
                )
    return found, problems


def collect(roots: list[str]) -> list[pathlib.Path]:
    """The files to read, in a stable order."""
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
    return [p for p in paths if not _EXCLUDED.search(p.as_posix())]


def declared(path: pathlib.Path) -> dict[tuple[str, str], str]:
    """The symbols *path* is registered as carrying both ways, if any."""
    posix = path.as_posix()
    for key, symbols in DECLARED.items():
        if posix == key or posix.endswith("/" + key):
            return symbols
    return {}


def _where(lines: list[int], plates: list[str]) -> str:
    """Where one slope was written: the page's lines, then the plates' labels."""
    parts: list[str] = []
    if lines:
        parts.append("on line " + ", ".join(str(n) for n in sorted(set(lines))))
    parts.extend(f"in {label}" for label in dict.fromkeys(plates))
    return "; ".join(parts)


def check(
    paths: list[pathlib.Path], plates: pathlib.Path | None = None
) -> tuple[int, list[str]]:
    """``(files read, one report per undeclared collision)``.

    *plates* is the directory the embedded plates are read from, the
    repository's :data:`PLATES` by default.
    """
    plate_dir = pathlib.Path(PLATES) if plates is None else plates
    failures: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
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
    return len(paths), failures


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
        help=f"directory the embedded plates are read from (default: {PLATES})",
    )
    args = parser.parse_args(argv)

    plates = pathlib.Path(args.plates)
    if not any(plates.glob("*.svg")):
        # Read from the wrong directory, every plate would simply be absent
        # and the gate would pass having read none of them.
        print(f"No images in {plates}: run from the repository root.", file=sys.stderr)
        return 1
    paths = collect(args.roots)
    read, failures = check(paths, plates)
    if not failures:
        print(
            f"Every subscript is single-valued in each of {read} files "
            "and the plates they embed."
        )
        return 0

    print(
        f"{len(failures)} subscripts carry both slopes inside one file "
        "or the plates it embeds:\n",
        file=sys.stderr,
    )
    for failure in failures:
        print(failure, file=sys.stderr)
    print(
        "\nRe-letter the index, set the lagging one the way its neighbours "
        "are set, or\ndeclare the page in DECLARED naming both meanings. A "
        "plate's slope is set\nin scripts/diagrams; regenerate the plate "
        "after changing it.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
