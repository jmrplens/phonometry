#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The anchors GitHub gives a Markdown file of this repository.

A link into a page of the contributor guide (``docs/contributing/``), written
in the guide itself, in a docstring, a workflow comment or the README, points
at a heading by the anchor github.com derives from it, or at one the page pins
with ``<a id="n4"></a>``. ``tests/test_contributing_guide.py`` holds every such
link to an anchor the page has, and reads them here.

The GitHub edition of the guides under ``docs/`` is written from the site by
``site/scripts/agent-md.mjs --docs``, which makes a link relative only when
GitHub would find its anchor on the target (``site/src/lib/agent-md/edition.mjs``
``githubAnchors``, with github-slugger itself); this module is the same reading
for the pages written by hand.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from markdown_fences import code_lines, page_kind

if TYPE_CHECKING:
    from pathlib import Path

#: Punctuation GitHub strips before turning a heading into its automatic
#: anchor, mirrored from the character classes and literals ``github-slugger``
#: removes. This is what actually renders the ``#...`` next to a heading on
#: github.com, not a guess at one. Built only from ``chr()`` code points and
#: ``re.escape()`` of a literal string, so this is one flat character class
#: with no alternation or repetition for a ReDoS scanner to flag.
_SLUG_PUNCTUATION = re.compile(
    "["
    + chr(0x2000)
    + "-"
    + chr(0x206F)
    + chr(0x2E00)
    + "-"
    + chr(0x2E7F)
    + re.escape("""\'!"#$%&()*+,./:;<=>?@[]^`{|}~""")
    + "]"
)

_ATX_HEADING = re.compile(r"^#{1,6}(?:\s+(.*?))?\s*#*\s*$")
_LINK_LABEL = re.compile(r"\[([^\]]*)\]\([^)]*\)")

#: An anchor a page declares itself, ``<a id="n4"></a>``: GitHub keeps it (as
#: ``user-content-n4``, which a ``#n4`` link reaches), and it survives a
#: reworded heading, which is why the contributor guide pins its rules with it.
_EXPLICIT_ANCHOR = re.compile(r'<a\s+(?:id|name)="([^"]+)"\s*>\s*</a>')


def slug(heading: str) -> str:
    """The anchor GitHub assigns *heading*, before duplicate-numbering.

    A heading that is itself a link anchors on its label, not its target:
    ``[Absorbers](i.md)`` slugs to ``absorbers``. Inline code needs no
    separate unwrapping: the backticks are in the punctuation class above and
    fall out either way, so ``Report metadata (`ReportMetadata`)`` slugs to
    ``report-metadata-reportmetadata``.

    :param heading: The heading's text as written after the ``#`` marks.
    :return: The anchor.
    """
    text = _LINK_LABEL.sub(r"\1", heading).lower()
    text = _SLUG_PUNCTUATION.sub("", text)
    return text.replace(" ", "-")


def _unfenced_lines(text: str, kind: str) -> list[str]:
    """The lines of *text* outside fenced code blocks.

    A fence can hold anything that merely looks like Markdown: a Python
    comment that starts a line with ``#``, or a snippet demonstrating link
    syntax. Read through ``markdown_fences`` so that this agrees with every
    other check on where a fence closes; *kind* is the page's, ``"md"`` or
    ``"mdx"`` (:func:`markdown_fences.page_kind`).
    """
    lines = text.splitlines()
    return [
        line
        for line, code in zip(lines, code_lines(lines, kind=kind), strict=True)
        if not code
    ]


def fragments(path: Path) -> set[str]:
    """The anchors *path* answers for.

    Every heading's anchor, with the ``-1``, ``-2`` GitHub appends when the
    same one recurs later on the page, in appearance order, and every explicit
    ``<a id="...">`` anchor outside a fence.

    :param path: A Markdown file.
    :return: The anchors.
    """
    lines = _unfenced_lines(path.read_text(encoding="utf-8"), page_kind(path.name))
    seen: dict[str, int] = {}
    found: set[str] = set()
    for line in lines:
        match = _ATX_HEADING.match(line)
        if match and match.group(1):
            anchor = slug(match.group(1))
            n = seen.get(anchor, 0)
            seen[anchor] = n + 1
            found.add(anchor if n == 0 else f"{anchor}-{n}")
        found.update(_EXPLICIT_ANCHOR.findall(line))
    return found
