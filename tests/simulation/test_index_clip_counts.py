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
section embeds it, in a ``Video`` component the page renders: one quoted in
a fence, a code span, a comment or an expression, written behind a
backslash, or written in the frontmatter, embeds nothing. A clip added, dropped or moved leaves the overview failing until it
says the new count and tables the guides that carry the clips now, and a
Spanish page that embeds other clips than its English twin fails on its own.
Every row of the table is read, and one whose first cell does not link a
guide of the page's own language by its site address fails.
"""

from __future__ import annotations

import functools
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

# scripts/ goes on the path first, so the imports come after it.
from figures import registry  # noqa: E402
from markdown_fences import cell_spans, page_lines  # noqa: E402
from markdown_spans import page_markup  # noqa: E402

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
#: A clip a page embeds, the solvers' or not: the ``name`` of its ``Video``
#: component.
_VIDEO = re.compile(r"<Video\b[^>]*?\bname=\"([^\"]+)\"", re.DOTALL)
#: The name of a clip one of the two solvers made.
_SOLVER_CLIP = re.compile(r"anim_(?:fdtd|elastic)_[a-z0-9_]+")
#: The first cell of the header of the overview's table of the guides that
#: carry the acoustic solver's clips, by language.
_TABLE_HEAD = {"en": "Guide", "es": "Guía"}
#: The first cell of a row of that table: a link to the guide by its site
#: address, whose language prefix is caught apart from the guide's route.
_GUIDE_LINK = re.compile(r"\[[^\]]+\]\(/phonometry/(es/)?([a-z0-9/-]+)/\)")
#: The prefix each language's pages put before the route of a guide.
_LANGUAGE_PREFIX = {"en": "", "es": "es/"}


def _embedded_in(text: str) -> list[str]:
    """Every clip a page embeds, in reading order: the ``name`` of each ``Video``
    component it renders.

    The page is read as the site reads it (:func:`markdown_spans.page_markup`):
    a component quoted in a fence, a code span or a comment, or written in the
    frontmatter, renders nothing and embeds no clip. A page that never writes
    the tag is not read at all.

    :param text: The page as written.
    """
    if "<Video" not in text:
        return []
    return _VIDEO.findall(page_markup(text, kind="mdx"))


@functools.cache
def _embedded(page: pathlib.Path) -> tuple[str, ...]:
    """Every clip the page at *page* embeds, read once for every test that asks."""
    return tuple(_embedded_in(page.read_text(encoding="utf-8")))


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
        found.update(clip for clip in _embedded(page) if _SOLVER_CLIP.fullmatch(clip))
    return found


def _guides_with(prefix: str, language: str) -> set[str]:
    """The route of every page of *language* outside the simulation section that embeds a clip named *prefix*."""
    routes: set[str] = set()
    for page, relative in _pages(language):
        if relative.parts[0] == "simulation":
            continue
        if any(clip.startswith(prefix) for clip in _embedded(page)):
            routes.add(relative.with_suffix("").as_posix())
    return routes


def _cells(row: str) -> list[str]:
    """The cells of a row of a table, stripped, its outer pipes opening and closing none."""
    written = row.strip(" \t")
    cells = [written[start:end].strip(" \t") for start, end in cell_spans(written)]
    if len(cells) > 1 and written.startswith("|"):
        cells.pop(0)
    if len(cells) > 1 and written.endswith("|"):
        cells.pop()
    return cells


def _guide_cells(text: str, language: str) -> list[str] | None:
    """The first cell of each row of the page's table of guides, past its header
    and its delimiter row, or ``None`` when the page holds no such table.

    A table is the run of rows a walk of the page reads together, the page read
    as the site renders it (:func:`markdown_spans.page_markup`), so a table in a
    fence or a comment is none; the table of guides is the one whose header
    opens on :data:`_TABLE_HEAD`. Its cells are read as the page writes them.
    """
    lines = text.split("\n")
    shown = page_markup(text, kind="mdx").split("\n")
    tables: list[list[str]] = []
    previous = ""
    for line, read in zip(lines, page_lines(shown), strict=True):
        if read.role == "row":
            if previous != "row":
                tables.append([])
            tables[-1].append(line)
        previous = read.role
    for rows in tables:
        if _cells(rows[0])[0] == _TABLE_HEAD[language]:
            return [_cells(row)[0] for row in rows[2:]]
    return None


def _table_problems(text: str, language: str, wanted: set[str]) -> list[str]:
    """What is wrong with the page's table of guides, against the routes it has to name.

    :param text: The page as written.
    :param language: The page's language, whose guides the rows have to link.
    :param wanted: The route of each guide the table has to give a row.
    """
    cells = _guide_cells(text, language)
    if cells is None:
        return [f"holds no table of guides headed {_TABLE_HEAD[language]!r}"]
    found = [(cell, _GUIDE_LINK.fullmatch(cell)) for cell in cells]
    unlinked = [cell for cell, link in found if link is None]
    links = [link.groups() for _, link in found if link is not None]
    foreign = sorted(
        f"/phonometry/{prefix or ''}{route}/"
        for prefix, route in links
        if (prefix or "") != _LANGUAGE_PREFIX[language]
    )
    rows = [route for _, route in links]
    repeated = sorted({route for route in rows if rows.count(route) > 1})
    problems = []
    if unlinked:
        problems.append(
            f"has rows whose first cell links no guide by its site address: {unlinked}"
        )
    if foreign:
        problems.append(f"links guides of the other language: {foreign}")
    if repeated:
        problems.append(f"gives these guides more than one row: {repeated}")
    if set(rows) != wanted:
        problems.append(
            f"tables {sorted(set(rows) - wanted)} that embed no acoustic solver"
            f" clip, and leaves out {sorted(wanted - set(rows))} that do"
        )
    return problems


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
        english = _embedded(page)
        twin = _DOCS / "es" / relative
        spanish = _embedded(twin) if twin.is_file() else ()
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
    text = (_DOCS / page).read_text(encoding="utf-8")
    problems = _table_problems(text, language, _guides_with("anim_fdtd_", language))
    assert not problems, f"{page}: " + "; ".join(problems)


#: A page that names a clip in each place a page can write one: in its
#: frontmatter, in a fence of backticks and in one of tildes, in a code span,
#: in a comment, behind a backslash, in a string of an expression, and in a
#: ``Video`` component of its own, which is what it embeds, the last ones with
#: two dollar signs and two backticks among their attributes.
_NAMED_EVERYWHERE = """---
description: 'Embeds <Video name="anim_fdtd_frontmatter" /> on the page'
---

```mdx
<Video name="anim_fdtd_fenced" />
```

~~~
<Video name="anim_fdtd_tilde" />
~~~

Embed one with `<Video name="anim_fdtd_spanned" />` in the guide.

{/* <Video name="anim_fdtd_commented" /> */}

<Video
  name="anim_fdtd_embedded"
  width={2400}
/>

Write \\<Video name="anim_fdtd_escaped" /> to embed one.

<code>{'<Video name="anim_fdtd_string" />'}</code>

<Video alt="from $20" name="anim_fdtd_priced" caption="to $30" />

<Video alt="a `b" name="anim_fdtd_ticked" caption="c` d" />
"""


def test_a_clip_named_outside_a_component_the_page_renders_is_not_embedded() -> None:
    assert _embedded_in(_NAMED_EVERYWHERE) == [
        "anim_fdtd_embedded",
        "anim_fdtd_priced",
        "anim_fdtd_ticked",
    ]


@pytest.mark.parametrize(
    "opening",
    [
        pytest.param("\n", id="a blank line"),
        pytest.param("\n  \n", id="blank lines"),
        pytest.param("\ufeff", id="a byte order mark"),
    ],
)
def test_a_clip_named_in_a_frontmatter_behind_its_opening_is_not_embedded(
    opening: str,
) -> None:
    """Astro reads a frontmatter after a byte order mark or blank lines too."""
    page = (
        f"{opening}---\n"
        "description: '<Video name=\"anim_fdtd_frontmatter\" />'\n"
        "---\n"
        "\n"
        '<Video name="anim_fdtd_embedded" />\n'
    )
    assert _embedded_in(page) == ["anim_fdtd_embedded"]


#: An English table of guides, with the rows each check is for.
_TABLE = """Eighteen of the acoustic solver's nineteen are on these guides:

| Guide | What its animations show |
|---|---|
| [Room acoustics](/phonometry/buildings/rooms/room-acoustics/) | room modes |
{row}
"""


@pytest.mark.parametrize(
    ("row", "problem"),
    [
        pytest.param(
            "| [Acústica de salas](https://docs.jmrp.io/phonometry/es/buildings/rooms/room-acoustics/) | modos |",
            "first cell links no guide by its site address",
            id="the other language by an absolute address",
        ),
        pytest.param(
            "| [Room acoustics](../buildings/rooms/room-acoustics/) | modes |",
            "first cell links no guide by its site address",
            id="a relative link",
        ),
        pytest.param(
            "| Room acoustics | modes |",
            "first cell links no guide by its site address",
            id="no link",
        ),
        pytest.param(
            "| [Acústica de salas](/phonometry/es/buildings/rooms/room-acoustics/) | modos |",
            "links guides of the other language",
            id="the other language by its site address",
        ),
        pytest.param(
            "| [Room acoustics](/phonometry/buildings/rooms/room-acoustics/) | modes |",
            "more than one row",
            id="a guide twice",
        ),
    ],
)
def test_every_row_of_the_table_is_read(row: str, problem: str) -> None:
    """A row the table holds is checked whatever its first cell is."""
    problems = _table_problems(
        _TABLE.format(row=row), "en", {"buildings/rooms/room-acoustics"}
    )
    assert any(problem in found for found in problems), problems


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("No table here.\n", id="no table"),
        pytest.param(
            "{/*\n" + _TABLE.format(row="") + "*/}\n", id="a table in a comment"
        ),
        pytest.param("```md\n" + _TABLE.format(row="") + "```\n", id="a fenced table"),
    ],
)
def test_a_page_without_the_table_of_guides_fails(text: str) -> None:
    problems = _table_problems(text, "en", {"buildings/rooms/room-acoustics"})
    assert any("no table of guides" in found for found in problems), problems


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_the_overview_counts_the_clips_the_registry_and_the_guides_hold(
    page: str, language: str
) -> None:
    text = " ".join((_DOCS / page).read_text(encoding="utf-8").split())
    missing = [phrase for phrase in _phrases(language) if phrase not in text]
    assert not missing, f"{page} does not say: {missing}"
