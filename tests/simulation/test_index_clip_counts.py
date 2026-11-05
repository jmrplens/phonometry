#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The simulation overview counts the solvers' clips the way the registry and the guides hold them.

The overview says, in English and in Spanish, how many of the
documentation's animations the two solvers made, how many each made, how
many of them sit on the guides whose physics they settle rather than in the
simulation section, and how many of the elastic solver's are among those.
Each count is taken here from where it is decided: a clip of the acoustic
solver is one ``scripts/figures/registry.py`` names ``anim_fdtd_*``, one of
the elastic solver ``anim_elastic_*``, and a clip is on a guide when an
English page outside the simulation section embeds it. A clip added, dropped
or moved leaves the overview failing until it says the new count.
"""

from __future__ import annotations

import pathlib
import re
import sys

import pytest

pytest.importorskip("matplotlib")

_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts"))

from figures import registry  # noqa: E402  (scripts/ goes on the path first)

_DOCS = _ROOT / "site" / "src" / "content" / "docs"
#: How each language writes a count, capitalised when a sentence opens
#: with it. A count moved to a number the table does not hold raises
#: KeyError: add its words here and to both pages. Spanish counts
#: animations, a feminine noun, so 21 is "veintiuna".
_WORDS = {
    "en": {3: "three", 5: "five", 19: "nineteen", 21: "twenty-one", 24: "twenty-four"},
    "es": {
        3: "tres",
        5: "cinco",
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


def _clips(prefix: str) -> set[str]:
    return {clip for clip in registry._ANIMATIONS if clip.startswith(prefix)}


def _on_guides() -> set[str]:
    """Every solver clip an English page outside the simulation section embeds."""
    found: set[str] = set()
    for page in _DOCS.rglob("*.mdx"):
        parts = page.relative_to(_DOCS).parts
        if parts[0] in {"es", "simulation"}:
            continue
        found.update(_EMBEDDED.findall(page.read_text(encoding="utf-8")))
    return found


def _phrases(language: str) -> list[str]:
    acoustic, elastic = _clips("anim_fdtd_"), _clips("anim_elastic_")
    guides = _on_guides()
    words = _WORDS[language]
    total = words[len(acoustic) + len(elastic)]
    n_acoustic, n_elastic = words[len(acoustic)], words[len(elastic)]
    n_guides = words[len(guides & (acoustic | elastic))]
    n_elastic_guides = words[len(guides & elastic)].capitalize()
    if language == "en":
        return [
            f"{total} of the animations in this documentation are output from"
            f" these two solvers, {n_acoustic} from the acoustic one and"
            f" {n_elastic} from the elastic one, and {n_guides} of them are filed"
            " on the guides whose physics they settle",
            f"{n_elastic_guides} of the elastic solver's {n_elastic} are on guides too",
        ]
    return [
        f"{total} de las animaciones de esta documentación son salida de estos"
        f" dos esquemas, {n_acoustic} del acústico y {n_elastic} del elástico,"
        f" y {n_guides} de ellas están archivadas en las guías cuya física zanjan",
        f"{n_elastic_guides} de las {n_elastic} del esquema elástico están también en guías",
    ]


def test_every_clip_on_a_guide_is_one_the_registry_lists() -> None:
    unknown = _on_guides() - _clips("anim_fdtd_") - _clips("anim_elastic_")
    assert not unknown, (
        f"pages embed clips the registry does not list: {sorted(unknown)}"
    )


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_the_overview_counts_the_clips_the_registry_and_the_guides_hold(
    page: str, language: str
) -> None:
    text = " ".join((_DOCS / page).read_text(encoding="utf-8").split())
    missing = [phrase for phrase in _phrases(language) if phrase not in text]
    assert not missing, f"{page} does not say: {missing}"
