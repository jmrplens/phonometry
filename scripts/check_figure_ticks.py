#!/usr/bin/env python3
"""Fail on tick labels that run into each other.

A band axis set by hand is the usual way to get this. A generator puts the
band centres on a logarithmic axis with ``set_xticks`` and its own labels,
leaves the minor formatter where the scale put it, and matplotlib goes on
labelling the minor ticks in its own notation between the ones the generator
wrote: an axis that should read "125 250 500 1k" reads "2 × 10²50 4 × 10²500".
The figure matches its generator, its colours pass, the annotation audit
measures the labels a generator places in the plot and not the ones an axis
draws, and ``svg.fonttype = "path"`` leaves no text in the committed file to
look for the tick in.

Where the numbers come from
---------------------------

:mod:`figure_tick_audit` measures every axis during the generation run, on the
live figure, and writes down two things:

* **stray** minor labels: minor ticks labelled by the scale's own formatter on
  an axis whose major ticks were set by hand. Every one fails, whether or not
  it happens to touch a neighbour, because the labels nobody asked for are
  the defect: in scientific notation between band labels they read as a
  second scale even where they fit. The fix is the one the library helpers
  already apply: ``format_frequency_axis(ax, language=_LANG)`` on a frequency
  axis, and ``axis.set_minor_formatter(NullFormatter())`` on any other.
* **overlaps**: two labels drawn by one axis whose boxes run into each other,
  with how deep, in points.

Every overlap fails, at any depth. A label's box is as wide as the advances
of its characters, so two boxes that touch are set as closely as two letters
of one word and the reader cannot tell where one label stops:
``diffuser_modulation`` ran its radial labels 0.08 pt into each other and
read "−10−15−20". A line box is also taller than the digits in it, so two
labels stacked down an axis could share a sliver of box with no ink near it;
that is where a tolerance would go if one is ever needed, and the corpus has
no such pair (when the gate was written, the only overlaps in it were the
three drawings it fixed: labels side by side and radial labels on a ray).

Running it
----------

The measurement comes from a generation run, so the check needs one::

    make graphs         # records into build/figure-ticks
    make figure-ticks   # reads it

``make graphs`` empties the directory first. The check requires the recording
to cover every committed figure in both languages, because a Spanish label
carries a decimal comma and a longer word; ``--partial`` is for a run of
some figures only (``--figure``), and checks what that run drew.

Exit status 0 when no axis runs its labels together, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import check_figure_annotations as annotation_check
import figure_tick_audit as audit

#: What to do about each kind, printed under the axes that fire it.
ADVICE = {
    audit.STRAY: (
        "clear the minor labels: format_frequency_axis(ax, language=_LANG) on a "
        "frequency axis, axis.set_minor_formatter(NullFormatter()) on any other"
    ),
    audit.OVERLAP: (
        "thin the labels (a label on every other tick, the ticks kept), turn "
        "them, or give the axis the room they need"
    ),
}

#: How each kind reads in the failure report.
HEADLINE = {
    audit.STRAY: "label their minor ticks beside major ticks set by hand",
    audit.OVERLAP: "draw two tick labels into each other",
}


def describe(key: str, hit: dict[str, Any]) -> str:
    """One report line: the drawing, the axis, the labels and how deep."""
    labels = ", ".join(json.dumps(label, ensure_ascii=False) for label in hit["labels"])
    depth = f" ({hit['depth_pt']:.2f} pt)" if hit["kind"] == audit.OVERLAP else ""
    return f"  {key}: {hit['axis']}: {labels}{depth}"


def report(recorded: dict[str, list[dict[str, Any]]]) -> int:
    """Fail on every stray minor label and every overlap in *recorded*."""
    failures = [(key, hit) for key in sorted(recorded) for hit in recorded[key]]
    if not failures:
        print(
            "No axis runs its tick labels together "
            f"({len(recorded)} drawing(s) measured)."
        )
        return 0
    print("::error::tick labels on a figure run into each other")
    for kind in (audit.STRAY, audit.OVERLAP):
        of_kind = [(key, hit) for key, hit in failures if hit["kind"] == kind]
        if not of_kind:
            continue
        axes = len({(key, hit["axis"]) for key, hit in of_kind})
        drawings = len({key for key, _ in of_kind})
        print(f"{axes} axis/axes across {drawings} drawing(s) {HEADLINE[kind]}:")
        for key, hit in of_kind:
            print(describe(key, hit))
        print(f"  -> {ADVICE[kind]}.")
    return 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; see the module docstring."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--audit",
        default=audit.DEFAULT_DIR,
        metavar="DIR",
        help=f"where the generation run recorded (default: {audit.DEFAULT_DIR})",
    )
    parser.add_argument(
        "--partial",
        action="store_true",
        help="the run generated only some of the figures: check what it drew "
        "and do not require full coverage",
    )
    args = parser.parse_args(argv)

    directory = pathlib.Path(args.audit)
    recorded = audit.load(str(directory)) if directory.is_dir() else {}
    if not recorded:
        print(
            f"::error::no tick-label recording in {directory}. It is written by "
            f"the generation run itself: run `make graphs` with {audit.AUDIT_ENV} "
            "set, which is what the graphs target does, and check again."
        )
        return 1

    if not args.partial:
        missing = annotation_check.committed_figures() - set(recorded)
        if missing:
            print(
                f"::error::the recording in {directory} covers {len(recorded)} "
                f"drawing(s) and misses {len(missing)} that `make graphs` "
                "produces (every figure in both languages, the `_es` twin "
                f"included), so it is not a full run: "
                f"{', '.join(sorted(missing)[:5])}..."
            )
            print("  -> run `make graphs` (it empties the directory first).")
            return 1

    return report(recorded)


if __name__ == "__main__":
    sys.exit(main())
