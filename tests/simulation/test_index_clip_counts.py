#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The simulation overview counts the solvers' clips the way the registry and the guides hold them.

The overview says, in English and in Spanish, how many of the
documentation's animations the two solvers made, how many each made, how
many of them sit on the guides whose physics they settle rather than in the
simulation section, and how many of each solver's are among those, and
it gives a table of the guides that carry the acoustic solver's clips.
Each count and each row is taken here from where it is decided: a clip of
the acoustic solver is one ``scripts/figures/registry.py`` names
``anim_fdtd_*``, one of the elastic solver ``anim_elastic_*``, and a clip is
on a guide when a page of the overview's language outside the simulation
section embeds it. A clip added, dropped or moved leaves the overview
failing until it says the new count and tables the guides that carry the
clips now, and a Spanish page that embeds other clips than its English twin
fails on its own.
"""

from __future__ import annotations

import pathlib
import re
import sys

import pytest

pytest.importorskip("matplotlib")

pytestmark = [
    # The registry imports the figure stack.
    pytest.mark.pinned_stack,
    # Each test reads every guide of the site to find the clips it embeds.
    pytest.mark.whole_tree,
]

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))

# scripts/ goes on the path first, so the import comes after it.
from figures import registry  # noqa: E402

_DOCS = _ROOT / "site" / "src" / "content" / "docs"
#: How each language writes a count, capitalised when a sentence opens
#: with it. A count moved to a number the table does not hold raises
#: KeyError: add its words here and to both pages. Spanish counts
#: animations, a feminine noun, so 21 is "veintiuna".
_WORDS = {
    "en": {
        3: "three",
        5: "five",
        18: "eighteen",
        19: "nineteen",
        21: "twenty-one",
        24: "twenty-four",
    },
    "es": {
        3: "tres",
        5: "cinco",
        18: "dieciocho",
        19: "diecinueve",
        21: "veintiuna",
        24: "veinticuatro",
    },
}
#: The two overview pages and their language.
_PAGES = [
    ("simulation/index.mdx", "en"),
    ("es/simulation/index.mdx", "es"),
]
#: A clip a page embeds: the ``name`` of its ``Video`` component.
_EMBEDDED = re.compile(r"\bname=\"(anim_(?:fdtd|elastic)_[a-z0-9_]+)\"")
#: A row of the overview's table of the guides that carry the acoustic
#: solver's clips: its first cell links the guide by its site address,
#: whose language prefix is caught apart from the guide's route.
_GUIDE_ROW = re.compile(
    r"^\| \[[^\]]+\]\(/phonometry/(es/)?([a-z0-9/-]+)/\) \|", re.MULTILINE
)
#: The prefix each language's pages put before the route of a guide.
_LANGUAGE_PREFIX = {"en": "", "es": "es/"}
#: Any clip a page embeds, the solvers' or not.
_VIDEO = re.compile(r"<Video\b[^>]*?\bname=\"([^\"]+)\"", re.DOTALL)


def _clips(prefix: str) -> set[str]:
    return {clip for clip in registry._ANIMATIONS if clip.startswith(prefix)}


def _pages(language: str) -> list[tuple[pathlib.Path, pathlib.Path]]:
    """Each page of *language* and its path below the language's root."""
    root = _DOCS / "es" if language == "es" else _DOCS
    pages = []
    for page in sorted(root.rglob("*.mdx")):
        relative = page.relative_to(root)
        if language == "en" and relative.parts[0] == "es":
            continue
        pages.append((page, relative))
    return pages


def _on_guides(language: str) -> set[str]:
    """Every solver clip a page of *language* outside the simulation section embeds."""
    found: set[str] = set()
    for page, relative in _pages(language):
        if relative.parts[0] == "simulation":
            continue
        found.update(_EMBEDDED.findall(page.read_text(encoding="utf-8")))
    return found


def _guides_with(prefix: str, language: str) -> set[str]:
    """The route of every page of *language* outside the simulation section that embeds a clip named *prefix*."""
    routes: set[str] = set()
    for page, relative in _pages(language):
        if relative.parts[0] == "simulation":
            continue
        clips = _EMBEDDED.findall(page.read_text(encoding="utf-8"))
        if any(clip.startswith(prefix) for clip in clips):
            routes.add(relative.with_suffix("").as_posix())
    return routes


def _phrases(language: str) -> list[str]:
    acoustic, elastic = _clips("anim_fdtd_"), _clips("anim_elastic_")
    guides = _on_guides(language)
    words = _WORDS[language]
    total = words[len(acoustic) + len(elastic)]
    n_acoustic, n_elastic = words[len(acoustic)], words[len(elastic)]
    n_guides = words[len(guides & (acoustic | elastic))]
    n_acoustic_guides = words[len(guides & acoustic)].capitalize()
    n_elastic_guides = words[len(guides & elastic)].capitalize()
    if language == "en":
        return [
            f"{total} of the animations in this documentation are output from"
            f" these two solvers, {n_acoustic} from the acoustic one and"
            f" {n_elastic} from the elastic one, and {n_guides} of them are filed"
            " on the guides whose physics they settle",
            f"{n_acoustic_guides} of the acoustic solver's {n_acoustic} are on"
            " these guides:",
            f"{n_elastic_guides} of the elastic solver's {n_elastic} are on guides too",
        ]
    return [
        f"{total} de las animaciones de esta documentación son salida de estos"
        f" dos esquemas, {n_acoustic} del acústico y {n_elastic} del elástico,"
        f" y {n_guides} de ellas están archivadas en las guías cuya física zanjan",
        f"{n_acoustic_guides} de las {n_acoustic} del esquema acústico están en"
        " estas guías:",
        f"{n_elastic_guides} de las {n_elastic} del esquema elástico están también en guías",
    ]


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_clip_on_a_guide_is_one_the_registry_lists(language: str) -> None:
    unknown = _on_guides(language) - _clips("anim_fdtd_") - _clips("anim_elastic_")
    assert not unknown, (
        f"pages embed clips the registry does not list: {sorted(unknown)}"
    )


def test_each_spanish_page_embeds_the_clips_of_its_english_twin() -> None:
    """Each Spanish page embeds its English twin's clips, which the counts take as read."""
    differ = []
    for page, relative in _pages("en"):
        english = _VIDEO.findall(page.read_text(encoding="utf-8"))
        twin = _DOCS / "es" / relative
        spanish = (
            _VIDEO.findall(twin.read_text(encoding="utf-8")) if twin.is_file() else []
        )
        if sorted(english) != sorted(spanish):
            differ.append(
                f"{relative}: {sorted(english)} in English, {sorted(spanish)} in Spanish"
            )
    assert not differ, (
        "a Spanish page embeds other clips than its English twin:\n" + "\n".join(differ)
    )


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_the_overview_tables_each_guide_that_carries_an_acoustic_clip_once(
    page: str, language: str
) -> None:
    """The overview's table names, once each, the guides of its own language that embed an acoustic solver clip."""
    links = _GUIDE_ROW.findall((_DOCS / page).read_text(encoding="utf-8"))
    foreign = sorted(
        f"/phonometry/{prefix}{route}/"
        for prefix, route in links
        if prefix != _LANGUAGE_PREFIX[language]
    )
    assert not foreign, f"{page} links guides of the other language: {foreign}"
    rows = [route for _, route in links]
    repeated = sorted({route for route in rows if rows.count(route) > 1})
    assert not repeated, f"{page} gives these guides more than one row: {repeated}"
    wanted = _guides_with("anim_fdtd_", language)
    assert set(rows) == wanted, (
        f"{page} tables {sorted(set(rows) - wanted)} that embed no acoustic"
        f" solver clip, and leaves out {sorted(wanted - set(rows))} that do"
    )


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_the_overview_counts_the_clips_the_registry_and_the_guides_hold(
    page: str, language: str
) -> None:
    text = " ".join((_DOCS / page).read_text(encoding="utf-8").split())
    missing = [phrase for phrase in _phrases(language) if phrase not in text]
    assert not missing, f"{page} does not say: {missing}"
