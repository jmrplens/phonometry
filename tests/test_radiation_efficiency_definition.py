#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a page introduces the radiation efficiency, it says what divides the power.

The radiation efficiency of Hopkins (2007), Equation 2.198, is the radiated
power divided by the product of the characteristic impedance of air, the
plate area and the mean-square velocity, "the ratio of the radiated power to
the power radiated by a large baffled piston ... with a uniform mean-square
velocity equal to the temporal and spatial average mean-square velocity of
the plate"; ISO/TS 7849-2:2009, 3.5, divides by the same ``Zc S v^2`` for its
radiation factor. The panel guide introduced it as the power a plate radiates
"per unit mean-square velocity", which is a power over a squared velocity in
kilograms per second and not the dimensionless factor the guide then feeds to
ISO 7849; its Spanish twin said the same, the plain-markdown mirror left the
piston out, and the mirror of the vibration theory page named the quantity
without saying what it is at all.

A page that writes the term in bold is introducing it, so the paragraph that
does (with the display formula right after it, which is where an API page
puts the product) has to name the characteristic impedance, the
``rho_0 c_0`` product or the piston, and must not say "per unit mean-square".
The glossary's own entry is held by ``site/scripts/glossary.test.mjs``.

A block that names the divisor through the piston has to say the piston is
a large one, ka >> 1, as Equation 2.198 does: only then is the particle
velocity at its face the face's own (Equations 2.199 and 2.200) and the power
it radiates rho_0 c_0 S <v^2>. A small piston of the same area and velocity
radiates far less: a baffled circular one radiates 1 - J1(2ka)/(ka) of it,
0.12 at ka = 0.5. The mirror of the vibration theory page and both site
theory pages said "a piston" alone.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.whole_tree

_ROOT = Path(__file__).resolve().parent.parent

#: The trees of published prose, in both languages and the mirror.
_TREES = ("docs", "site/src/content/docs")

#: The term in bold, in either language.
_INTRODUCED = re.compile(
    r"\*\*(?:radiation efficiency|eficiencia de radiaci[oó]n)\*\*", re.IGNORECASE
)

#: What the efficiency divides the radiated power by, named in words, in
#: symbols or through the piston that radiates that power.
_DIVISOR = re.compile(
    r"characteristic impedance|impedancia caracter[ií]stica|\\rho_0\s*c_0|"
    r"\brho_0 c_0\b|pist(?:on|ón)",
    re.IGNORECASE,
)

#: The piston named as the radiator of the reference power.
_PISTON = re.compile(r"pist(?:on|ón)", re.IGNORECASE)

#: The condition that makes the piston's power rho_0 c_0 S <v^2>: a large
#: piston, in words or as ka >> 1.
_LARGE_PISTON = re.compile(
    r"\blarge\b[^.]*?\bpiston|pist[oó]n\s+grande|\bka\s*(?:>>|\\gg|≫)\s*1",
    re.IGNORECASE,
)

#: The loose reading: a power per squared velocity.
_PER_UNIT = re.compile(
    r"per\s+unit\s+mean-square|por\s+unidad\s+de\s+velocidad\s+cuadr", re.IGNORECASE
)


def _blocks(text: str) -> list[str]:
    """The page's blocks, a paragraph and a display formula after it joined."""
    blocks = re.split(r"\n\s*\n", text)
    joined: list[str] = []
    for block in blocks:
        if joined and block.lstrip().startswith("$$"):
            joined[-1] += "\n" + block
        else:
            joined.append(block)
    return joined


def _pages() -> list[Path]:
    """The published pages, the glossaries left to their own test."""
    return [
        path
        for tree in _TREES
        for path in sorted((_ROOT / tree).rglob("*"))
        if path.suffix in {".md", ".mdx"} and "glossary" not in path.name
    ]


def test_the_block_reader_keeps_a_display_formula_with_its_paragraph() -> None:
    page = "The **radiation efficiency** relates:\n\n$$\nP = \\rho_0 c_0 S\n$$\n\nNext."
    blocks = _blocks(page)
    assert len(blocks) == 2
    assert _DIVISOR.search(blocks[0])
    assert _PER_UNIT.search("radiates per unit\nmean-square velocity")
    assert not _DIVISOR.search("the radiation factor that ISO 7849 takes as an input")
    assert _LARGE_PISTON.search("a large baffled piston of the same area")
    assert _LARGE_PISTON.search("un pistón grande montado en pantalla")
    assert _LARGE_PISTON.search(r"a baffled piston ($ka \gg 1$)")
    assert not _LARGE_PISTON.search("a piston of the same area. A large plate")


def test_every_page_introducing_the_radiation_efficiency_names_its_divisor() -> None:
    wrong = []
    read = 0
    for path in _pages():
        text = path.read_text(encoding="utf-8")
        if not _INTRODUCED.search(text):
            continue
        for block in _blocks(text):
            if not _INTRODUCED.search(block):
                continue
            read += 1
            where = path.relative_to(_ROOT).as_posix()
            if _PER_UNIT.search(block):
                wrong.append(f"{where}: per unit mean-square velocity")
            if not _DIVISOR.search(block):
                wrong.append(f"{where}: names no divisor")
            if _PISTON.search(block) and not _LARGE_PISTON.search(block):
                wrong.append(f"{where}: a piston, not a large one (ka >> 1)")
    assert read > 0, "no page introduces the radiation efficiency"
    assert wrong == [], "\n".join(wrong)
