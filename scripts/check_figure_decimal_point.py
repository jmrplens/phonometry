#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a committed Spanish figure whose tick labels keep an English point.

A Spanish figure writes its decimals with a comma, and three separate machines
put it there: the library's own ``localize_axes`` at the end of every plot
function, ``format_frequency_axis`` where a caller hands it the language, and
the save-time pass of ``scripts/figures/i18n.py`` over whatever a generator
drew. Each has covered a different set of panels, and a panel none of them
reached shipped ``31.5`` next to ``52,4`` with every gate green: the frequency
axis of a call that did not pass the language on, the log distance axis of a
steady-field plot, the ``z`` of a 3-D microphone array, the zoom inset of a pole
migration, and the colorbar of a contour hemisphere.

Rather than ask each machine whether it covered everything, this reads the
finished asset, which is what a reader sees. Text set with ``svg.fonttype
= "path"`` draws as outlines, but matplotlib writes the string it drew in a
comment beside them, so the committed SVG says what the figure says.

What it looks for is one shape: a label that is a number and nothing else, with
a point between its digits (``31.5``, ``0.10``, ``1.0000``, ``-0.004``). That is
the shape of a tick label, the one a formatter writes and no proofreading pass
can catch, and it is narrow enough to leave prose alone. A decimal inside a
longer label is the business of ``scripts/check_decimal_comma.py``, which reads
the drawn strings at the source.

Not every hit is a defect: a clause number is not a measurement, and keeps its
point in Spanish as it does in English. Those go in :data:`ALLOWED` with the
reason, keyed ``figure: label``. An entry that no longer matches fails too, so
the table cannot rot.

Usage::

    python scripts/check_figure_decimal_point.py

Exit status 0 when no Spanish figure writes a numeric label with a point.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

#: Where the figures are committed.
IMAGES = pathlib.Path(__file__).resolve().parent.parent / ".github" / "images"

#: The Spanish variants of every figure: the light one and its dark twin.
SPANISH = ("*_es.svg", "*_es_dark.svg")

#: The string matplotlib wrote beside the outlines it drew for it.
_COMMENT = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)

#: A label that is a number and nothing else: an optional sign (ASCII or the
#: typographic U+2212 the formatters ship), digits, a point, digits, and the
#: engineering suffix a frequency axis writes (``2.5k``).
_NUMERIC_LABEL = re.compile(r"^[-+−]?\d+\.\d+[kM]?$")

#: Numeric labels that are not measurements, keyed ``figure: label`` with the
#: reason. Nothing belongs here that a pass could write with a comma instead.
ALLOWED: dict[str, str] = {
    f"diagram_workstation_microphone: 9.{clause}": (
        "The panel is captioned with the ISO 11201 clause each work-station "
        "case is drawn from (9.1 operator present to 9.5 no work station). A "
        "clause number is not a quantity and keeps its point in Spanish."
    )
    for clause in range(1, 6)
}


def labels(path: pathlib.Path) -> list[str]:
    """Every string *path* records having drawn."""
    return _COMMENT.findall(path.read_text(encoding="utf-8", errors="replace"))


def stem(path: pathlib.Path) -> str:
    """The figure a Spanish variant belongs to, without the language suffix."""
    name = path.stem
    for suffix in ("_es_dark", "_es"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def check(images: pathlib.Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Find the numeric labels written with a point, and the stale allowances.

    :param images: The directory the figures are committed in.
    :return: The ``(figure, label)`` pairs that keep an English point and are
        not allowed, and the allowance keys nothing matches any more.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    paths = sorted({p for pattern in SPANISH for p in images.glob(pattern)})
    for path in paths:
        figure = stem(path)
        for label in labels(path):
            if not _NUMERIC_LABEL.match(label):
                continue
            key = f"{figure}: {label}"
            seen.add(key)
            if key not in ALLOWED and (figure, label) not in found:
                found.append((figure, label))
    return found, sorted(set(ALLOWED) - seen)


def main(argv: list[str] | None = None) -> int:
    """Report every Spanish figure that writes a number with a point."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("images", nargs="?", default=str(IMAGES))
    args = parser.parse_args(argv)

    images = pathlib.Path(args.images)
    found, stale = check(images)
    total = len({p for pattern in SPANISH for p in images.glob(pattern)})
    if not found and not stale:
        print(
            f"No Spanish figure writes a numeric label with a decimal point: "
            f"{total} files, {len(ALLOWED)} allowed."
        )
        return 0
    for figure, label in found:
        print(
            f"{figure}: the Spanish figure draws {label!r}, which a reader of "
            f"that page reads as a thousands separator",
            file=sys.stderr,
        )
    if found:
        print(
            "\nLocalise the panel where its labels are made: pass the language "
            "to format_frequency_axis, end the plot function on "
            "localize_axes(ax, language) for every axes it built (a twin axis "
            "and a colorbar each carry their own), or call "
            "figures.i18n.localize_panel on a panel the save-time pass cannot "
            "reach. Then regenerate the figure. If the number is not a "
            "measurement, add its key (figure: label) to ALLOWED in "
            "scripts/check_figure_decimal_point.py with the reason.",
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
