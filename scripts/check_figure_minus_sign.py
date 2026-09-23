#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a committed figure that signs a number with a hyphen.

The corpus writes a negative number with the minus sign, U+2212, in every
figure and in both languages: matplotlib's own formatters do it through
``axes.unicode_minus``, mathtext does it for every ``-`` between dollars, and a
reading a generator builds goes through ``_fmt_minus`` (the library's own
renderers through ``fmt_minus``). The hyphen-minus is shorter and sits lower,
so a figure that mixes the two puts the short one wherever a label escaped
all three, beside the proper one on the next tick.

Three ways it escapes, all found by this check when it was written:

* a formatter that bypasses ``axes.unicode_minus``. The polar
  ``ThetaFormatter`` builds its degree labels with a plain format spec, and
  the half disc of ``cnossos_rail_directivity`` read "-30°" under "−15";
* a reading assembled with an f-string and never passed through
  ``_fmt_minus`` ("$c_3$ = -0.6");
* the plates, which set the characters they are given and have no formatter
  in front of them at all: a decay range numbered "-10" to "-70".

What it reads
-------------
Every committed SVG, all four variants, figures and plates alike. Text is
drawn as outlines, but both matplotlib and the plate canvas write the string
they drew in a comment beside the outlines, so the committed file says what
the reader sees, as :mod:`check_figure_decimal_point` relies on.

A hyphen-minus is a sign when a digit follows it (``-3``, ``-0.6``, ``-.5``)
and no letter, digit or point comes before it. After one of those it is
something else and is left alone: a standard's designation (``61672-1``), a
compound (``nmfs-2024``), a range (``10-90``) or an exponent (``1e-05``),
which ``_fmt_minus`` leaves as ``format`` wrote it.

Mathtext is not read in a matplotlib figure, because matplotlib itself sets
the ``-`` of ``$-3$`` as U+2212. The plates set their mathematics with a
composer of their own that draws the character it is given, so there it is
read like any other text.

Not every hit is a sign. A part number written after a slash or a comma,
"ISO 9053-1/-2", keeps the hyphen of the designation it abbreviates, and code
is quoted in the characters the reader types. Those go in :data:`ALLOWED`,
keyed ``figure: string`` with the reason; an entry that no longer matches
anything fails too, so the table cannot rot.

Usage::

    python scripts/check_figure_minus_sign.py            # every committed figure
    python scripts/check_figure_minus_sign.py IMAGES     # another directory

Exit status 0 when no figure signs a number with a hyphen.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

#: Where the figures are committed.
IMAGES = pathlib.Path(__file__).resolve().parent.parent / ".github" / "images"

#: The string a drawing wrote beside the outlines it drew for it.
_COMMENT = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)

#: A hyphen-minus in front of a number, and not after a letter, a digit or a
#: point: the shape of a sign. See the module docstring for what the
#: lookbehind leaves alone.
_SIGN = re.compile(r"(?<![\w.])-(?=\.?\d)")

#: A mathtext run, which matplotlib sets with U+2212 for every ``-`` in it.
_MATH = re.compile(r"(?<!\\)\$.*?(?<!\\)\$", re.DOTALL)

#: What a matplotlib figure writes and a plate does not: its root group.
_MATPLOTLIB = 'id="figure_1"'

#: The language and theme suffixes of the four variants of one figure.
_SUFFIXES = ("_es_dark", "_dark", "_es")

#: Hyphens before a digit that are not signs, keyed ``figure: string`` with
#: the reason. Nothing belongs here that could be written with a minus sign.
ALLOWED: dict[str, str] = {
    **dict.fromkeys(
        (
            "diagram_airflow_resistance: Airflow resistance: static and "
            "alternating methods (ISO 9053-1/-2)",
            "diagram_airflow_resistance: Resistencia al flujo: métodos "
            "estático y alternante (ISO 9053-1/-2)",
            "diagram_railway_prediction_chain: DIN SPEC 45673-2, -3",
            "diagram_soundfield_audiometry: fitted (ISO 389-1 / -2 / -8), "
            "referred to a",
            "diagram_soundfield_audiometry: colocado (ISO 389-1 / -2 / -8), "
            "referido a un",
            "sound_power_methods: ISO/TS 7849-1 / -2",
            "sound_power_methods: $ε$ assumed (-1) or measured (-2)",
            "sound_power_methods: $ε$ supuesto (-1) o medido (-2)",
        ),
        "The parts of one standard, written the way a designation abbreviates "
        "them after the first: '-2' is part 2 of the standard just named, and "
        "its hyphen belongs to the designation. It is not a sign.",
    ),
    **dict.fromkeys(
        (
            "diagram_block_processing: y[-1]",
            "diagram_block_processing: y[-1] (or the sosfilt zi vector) seeds "
            "the next block → identical to one continuous call",
            "diagram_block_processing: y[-1] (o el vector zi de sosfilt) "
            "inicializa el bloque siguiente → idéntico a una llamada continua",
        ),
        "y[-1] is the Python index of the last output sample, quoted as the "
        "reader types it; code is written in the characters the interpreter "
        "reads.",
    ),
}


def figure(path: pathlib.Path) -> str:
    """The figure a variant belongs to, without its language or theme suffix."""
    name = path.stem
    for suffix in _SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def signed_with_hyphen(text: str, *, mathtext: bool) -> bool:
    """Whether *text* writes a number with a hyphen-minus for its sign.

    :param text: One drawn string.
    :param mathtext: Whether the drawing's mathematics is set by matplotlib,
        which writes U+2212 for every ``-`` between dollars itself.
    """
    if mathtext:
        text = _MATH.sub(" ", text)
    return _SIGN.search(text) is not None


def check(images: pathlib.Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Find the strings that sign a number with a hyphen, and the stale allowances.

    :param images: The directory the figures are committed in.
    :return: The ``(figure, string)`` pairs that are not allowed, in the order
        met, and the allowance keys nothing matches any more.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for path in sorted(images.glob("*.svg")):
        name = figure(path)
        source = path.read_text(encoding="utf-8", errors="replace")
        mathtext = _MATPLOTLIB in source
        for text in _COMMENT.findall(source):
            if not signed_with_hyphen(text, mathtext=mathtext):
                continue
            key = f"{name}: {text}"
            seen.add(key)
            if key not in ALLOWED and (name, text) not in found:
                found.append((name, text))
    return found, sorted(set(ALLOWED) - seen)


def main(argv: list[str] | None = None) -> int:
    """Report every figure that signs a number with a hyphen."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("images", nargs="?", default=str(IMAGES))
    args = parser.parse_args(argv)

    images = pathlib.Path(args.images)
    found, stale = check(images)
    total = len(list(images.glob("*.svg")))
    if not found and not stale:
        print(
            f"No figure signs a number with a hyphen: {total} files, "
            f"{len(ALLOWED)} allowed."
        )
        return 0
    for name, text in found:
        print(
            f"{name}: draws {text!r}, whose sign is a hyphen-minus rather than "
            "the minus sign U+2212",
            file=sys.stderr,
        )
    if found:
        print(
            "\nWrite the sign where the label is made: format a reading with "
            "_fmt_minus (figures.i18n) or fmt_minus (phonometry._i18n), give a "
            "formatter that ignores axes.unicode_minus one that signs with "
            "U+2212 (the polar ThetaFormatter is one), and type a plate's "
            "number with '−'. Then regenerate the figure. If the hyphen is not "
            "a sign, add its key (figure: string) to ALLOWED in "
            "scripts/check_figure_minus_sign.py with the reason.",
            file=sys.stderr,
        )
    for key in stale:
        print(
            f"ALLOWED lists {key!r}, which no figure draws any more: drop the entry",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
