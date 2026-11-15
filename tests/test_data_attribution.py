#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every page that reads a folder of ``tests/data/audio`` prints its attribution.

Three folders there hold measured data other people published under CC BY 4.0
(``nikolauskapelle/``, ``dublin/``, ``xl2/``), and three guides read them in
front of the reader, as ``io/audio-files`` reads ``xl2/``. The licence lets a
page share the data on four conditions: credit the creators, say it is
licensed and link the licence, and say what was changed. A page that reads the
data without them redistributes it outside its licence, whatever the README
beside the files says. ``tests/data/audio/README.md`` words each folder's
attribution once, ``Attribution: **"..."**`` for the English pages and
``Atribución: **"..."**`` for the Spanish pages, and this test holds every page
to those words (docs/contributing/docs-and-figures.md, rule F75).

What reads a folder: a page that names a path inside it,
``tests/data/audio/<folder>`` followed by anything but a dot, anywhere in its
text, its code included, or that builds one in a Python fence from string
literals: literals put side by side with ``/`` or ``joinpath`` (``repo /
"tests" / "data" / "audio" / "xl2"``, ``Path("tests/data/audio").joinpath("xl2")``),
glued with ``+``, joined by ``"/".join`` of a list or a tuple, or given to one
call together (``Path("tests", "data", "audio", "xl2")``), such a call standing
for the parts it is given wherever it stands in a longer path
(``Path(repo, "tests/data/audio") / "xl2"``). ``tests/data/audio/README.md`` is
no folder, so naming it reads nothing.

What prints the attribution: what the page shows as prose holds the string,
with its runs of blanks and line ends read as one space and a link read as the
words it links (``[10.5281/zenodo.7904680](https://doi.org/...)`` is
``10.5281/zenodo.7904680``). The page is read as the site reads it
(``markdown_spans.page_markup``): its frontmatter, its code, its display maths,
its inline code and maths spans, its comments and its expressions show no
prose, nor does a tag with everything its attributes say, an ``alt`` text
among them; the words between a tag and its closing tag are prose. Nothing
else is read past: the quotes, the punctuation and every word are the
README's.

So that a page whose reading the test stops seeing fails instead of passing,
every guide the README's table of files names as reading a folder has to be
seen reading it, in its English page and its Spanish twin.

The edge cases, each a limit of what a test that reads text can see: a path a
fence assembles from a name (``folder = "xl2"`` and then ``root / folder``, or
an f-string around it) is not followed, so a page writes the folder it reads as
a literal, as every page that reads one does today; a Python fence that does
not parse is read as text alone; the attribution set in a code comment does
not count, since the page shows it as code, not as the credit it is; and a
character behind a backslash escape shows no prose here, so the attribution is
written without one. A page under ``site/src/content/docs/es/`` is Spanish and
every other page is English. The API reference (``reference/api``), which the generator writes
from the docstrings, and the style guide (``docs/contributing/``), which quotes
paths in its examples and shows no data, are not read; nor are the llms copies
and the GitHub edition under ``docs/``, which are written from the pages read
here: a file that opens with the edition's comment is left to its generator
(rule F74), and the files of ``docs/`` written by hand are read.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pytest

#: The repository.
ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = str(ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from github_edition import EDITION_MARK, is_edition_file  # noqa: E402
from markdown_fences import MDX_TAG, fences, page_kind  # noqa: E402
from markdown_spans import page_markup  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

Language = Literal["en", "es"]
#: The folders of measured data, and the README that words their attribution.
AUDIO = ROOT / "tests" / "data" / "audio"
README = AUDIO / "README.md"
#: The site's pages, both languages, and the files of ``docs/``.
SITE = ROOT / "site" / "src" / "content" / "docs"
DOCS = ROOT / "docs"
#: What is not read, relative to its tree (see the module docstring).
SKIPPED = (
    SITE / "reference" / "api",
    SITE / "es" / "reference" / "api",
    DOCS / "contributing",
)
#: Local working notes under docs/, gitignored and never published.
UNPUBLISHED = (DOCS / "superpowers",)

#: The label of each language's attribution in the README.
LABELS: dict[Language, str] = {"en": "Attribution", "es": "Atribución"}
#: How a language is named in a failure.
NAMES: dict[Language, str] = {"en": "English", "es": "Spanish"}

#: A folder's section of the README: ``### `xl2/`: ...``.
_SECTION = re.compile(r"^### `([^`/]+)/`", re.MULTILINE)
#: A heading that ends the sections, ``## Purpose and scope of use``.
_PART = re.compile(r"^## ", re.MULTILINE)
#: A path inside a folder: the folder's name, and anything but a dot after it.
_FOLDER = re.compile(r"tests/data/audio/([A-Za-z0-9_-]+)(?![A-Za-z0-9_.-])")
#: The text between a link's or an image's brackets, which may wrap over one
#: line end.
_BRACKETED = r"\[([^\]\n]*(?:\n[^\]\n]*)?)\]"
#: A link, inline (``[words](url)``) or by reference (``[words][ref]``,
#: ``[words][]``), read as the words it links.
_LINK = re.compile(_BRACKETED + r"(?:\([^)\n]*\)|\[[^\]\n]*\])")
#: An image, inline or by reference: its alt is no prose the page shows.
_IMAGE = re.compile(r"!" + _BRACKETED + r"(?:\([^)\n]*\)|\[[^\]\n]*\])")
#: A link reference definition, ``[ref]: url``, which the page does not show.
_DEFINITION = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*\S.*$", re.MULTILINE)
#: A row of the README's table of files: the file's path, and what reads it.
_ROW = re.compile(r"^\| `([^`/]+)/[^|]*\|[^|]*\|([^|\n]*)\|$", re.MULTILINE)
#: A guide the table names among what reads a file, by its route.
_GUIDE = re.compile(r"the guide `([^`]+)`")
#: The fences whose Python is read for the paths it builds.
_PYTHON = frozenset({"python", "py"})


def _flat(text: str) -> str:
    """*text* with each run of blanks and line ends read as one space."""
    return " ".join(text.split())


def attributions(readme: str) -> dict[str, dict[Language, str]]:
    """Each folder's attribution, by language, as the README words it.

    :param readme: The text of ``tests/data/audio/README.md``.
    :return: The folder's name to its attribution in each language the README
        gives one in, each with its line ends read as spaces.
    """
    first = _SECTION.search(readme)
    if first is None:
        return {}
    end = _PART.search(readme, first.end())
    sections = readme[: end.start() if end else len(readme)]
    heads = list(_SECTION.finditer(sections))
    found: dict[str, dict[Language, str]] = {}
    for index, head in enumerate(heads):
        stop = heads[index + 1].start() if index + 1 < len(heads) else len(sections)
        body = sections[head.end() : stop]
        strings: dict[Language, str] = {}
        for language, label in LABELS.items():
            match = re.search(
                rf'^{label}: \*\*"(.+?)"\*\*', body, re.MULTILINE | re.DOTALL
            )
            if match:
                strings[language] = _flat(match.group(1))
        found[head.group(1)] = strings
    return found


#: A piece of a path an expression builds: the text of the literals it is
#: made of, or ``None`` where something else, a name or a call's result, stands.
Piece = str | None


def _glued(left: list[Piece], right: list[Piece]) -> list[Piece]:
    """*left* and *right* concatenated as ``+`` concatenates two strings."""
    if left and right and left[-1] is not None and right[0] is not None:
        return [*left[:-1], left[-1] + right[0], *right[1:]]
    return [*left, *right]


def _joined(separator: str, items: list[ast.expr]) -> list[Piece]:
    """What ``separator.join(items)`` builds: each run of literal items joined."""
    pieces: list[Piece] = []
    run: list[str] = []
    for item in [*items, None]:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            run.append(item.value)
            continue
        if run:
            pieces.append(separator.join(run))
        run = []
        if item is not None:
            pieces.append(None)
    return pieces


def _pieces(node: ast.expr) -> list[Piece]:
    """The pieces of the path *node* builds, as separate parts of a path.

    A literal is its text; ``/`` and ``joinpath`` put a path's parts side by
    side; ``+`` glues two strings into one; ``"/".join`` of a list or a tuple
    joins its literals with the separator; any other call stands for the parts
    it is given, as ``Path(...)`` and ``os.path.join(...)`` take them. Anything
    else, a name, an f-string, a subscript, is a piece nothing is known of.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return [*_pieces(node.left), *_pieces(node.right)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _glued(_pieces(node.left), _pieces(node.right))
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute) and function.attr == "joinpath":
            return [
                *_pieces(function.value),
                *(piece for arg in node.args for piece in _pieces(arg)),
            ]
        if (
            isinstance(function, ast.Attribute)
            and function.attr == "join"
            and isinstance(function.value, ast.Constant)
            and isinstance(function.value.value, str)
            and len(node.args) == 1
            and isinstance(node.args[0], ast.List | ast.Tuple)
        ):
            return _joined(function.value.value, node.args[0].elts)
        return [piece for arg in node.args for piece in _pieces(arg)]
    return [None]


def consumers(readme: str) -> set[tuple[str, str]]:
    """Each guide the README's table of files names as reading a folder.

    :param readme: The text of ``tests/data/audio/README.md``.
    :return: Each ``(route, folder)``: the route of a guide (``io/audio-files``)
        and the folder of a file the table says it reads.
    """
    return {
        (route, folder)
        for folder, consumed in _ROW.findall(readme)
        for route in _GUIDE.findall(consumed)
    }


def editions(route: str) -> tuple[str, str]:
    """The two pages of the guide at *route*: English and Spanish."""
    return (
        f"site/src/content/docs/{route}.mdx",
        f"site/src/content/docs/es/{route}.mdx",
    )


def unread(
    pages: Iterable[tuple[str, Language, str]], expected: set[tuple[str, str]]
) -> list[str]:
    """Each edition of a guide the README names that the test does not see read.

    A guide whose path into its folder the test stopped following, or whose page
    moved, is no longer held to the attribution: this names it instead.

    :param pages: Each page's name, language and text.
    :param expected: Each ``(route, folder)`` the README names (:func:`consumers`).
    """
    read = {name: folders_read(text, kind=page_kind(name)) for name, _, text in pages}
    return [
        f"{page}: the README names it as reading tests/data/audio/{folder}/, "
        "and the test does not see it read that folder"
        for route, folder in sorted(expected)
        for page in editions(route)
        if folder not in read.get(page, set())
    ]


def _runs(pieces: list[Piece]) -> Iterator[str]:
    """Each run of known pieces among *pieces*, joined by ``/``.

    A piece's own leading or trailing ``/`` (``Path("tests/data/audio/")``)
    is the separator the join adds, so a repeated separator is read as one.
    """
    run: list[str] = []
    for piece in [*pieces, None]:
        if piece is not None:
            run.append(piece)
            continue
        if run:
            yield re.sub(r"/{2,}", "/", "/".join(run))
        run = []


def built_paths(code: str) -> Iterator[str]:
    """The paths a piece of Python builds from string literals.

    Every expression is read for the path it builds (:func:`_pieces`), and each
    run of its pieces that literals alone make is a path. Nothing a name holds
    is followed.

    :param code: The body of a fence; one that does not parse builds nothing.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp | ast.Call | ast.Constant):
            yield from _runs(_pieces(node))


def folders_read(text: str, *, kind: str = "mdx") -> set[str]:
    """The folders of ``tests/data/audio`` a page reads.

    :param text: The page.
    :param kind: Its kind, ``"md"`` or ``"mdx"`` (``markdown_fences.page_kind``).
    """
    found = set(_FOLDER.findall(text))
    if "audio" not in text:
        # Every path into the folders spells the word, whole or in its own
        # literal, so a page without it builds none: no need to walk it.
        return found
    for fence in fences(text, kind=kind):
        if fence.language in _PYTHON:
            for path in built_paths(fence.body):
                found.update(_FOLDER.findall(path))
    return found


def printed_prose(text: str, *, kind: str = "mdx") -> str:
    """What a page shows as prose, links read as their words, flat.

    The page is read as the site reads it (:func:`markdown_spans.page_markup`):
    its frontmatter, its code, fenced or indented, its display maths, its inline
    code and maths spans, its comments, its expressions and its backslash
    escapes show no prose. Of what is left, every tag is markup and shows
    nothing either, its attributes with it (an ``alt``, a ``title``); the
    words between a tag and its closing tag are prose. An image, its alt with
    it, and a link reference definition show nothing; a link, inline or by
    reference, shows its words, wrapped over a line end or not.

    :param text: The page as written.
    :param kind: Its kind, ``"md"`` or ``"mdx"`` (``markdown_fences.page_kind``).
    """
    shown = MDX_TAG.sub(" ", page_markup(text, kind=kind))
    shown = _IMAGE.sub(" ", _DEFINITION.sub(" ", shown))
    return _flat(_LINK.sub(r"\1", shown))


def unattributed(
    pages: Iterable[tuple[str, Language, str]],
    strings: dict[str, dict[Language, str]],
) -> list[str]:
    """Each folder a page reads without printing its attribution.

    :param pages: Each page's name, language and text.
    :param strings: Each folder's attribution by language (:func:`attributions`).
    :return: One line per page and folder, naming what is missing.
    """
    problems: list[str] = []
    for name, language, text in pages:
        kind = page_kind(name)
        read = folders_read(text, kind=kind)
        if not read:
            continue
        prose = printed_prose(text, kind=kind)
        for folder in sorted(read):
            attribution = strings.get(folder, {}).get(language)
            if attribution is None:
                problems.append(
                    f"{name}: reads tests/data/audio/{folder}/, and tests/data/audio/README.md "
                    f'gives that folder no {NAMES[language]} attribution ({LABELS[language]}: **"..."**)'
                )
            elif attribution not in prose:
                problems.append(
                    f"{name}: reads tests/data/audio/{folder}/ and does not print its "
                    f'{NAMES[language]} attribution: "{attribution}"'
                )
    return problems


def published_pages(root: Path = ROOT) -> Iterator[tuple[str, Language, str]]:
    """Every page the site publishes and every file of ``docs/`` written by hand.

    A file of the GitHub edition is left to its generator: ``make llms`` writes
    it from the English page, which is read here.

    :param root: The repository whose trees are read.
    :return: Each page's name, relative to *root*, its language and its text.
    """
    site, docs = root / SITE.relative_to(ROOT), root / DOCS.relative_to(ROOT)
    skipped = tuple(root / path.relative_to(ROOT) for path in (*SKIPPED, *UNPUBLISHED))
    for tree, pattern in ((site, "*.md*"), (docs, "*.md")):
        for path in sorted(tree.rglob(pattern)):
            if any(path.is_relative_to(skip) for skip in skipped):
                continue
            if tree == docs and is_edition_file(path):
                continue
            language: Language = "es" if path.is_relative_to(site / "es") else "en"
            yield (
                path.relative_to(root).as_posix(),
                language,
                path.read_text(encoding="utf-8"),
            )


# A page of each shape the test reads, and the README words it holds them to.
_README = """# Data

| File | Kind | Consumed by |
| :--- | :--- | :--- |
| `chapel/ir.npz` | derived | `tests/test_chapel.py`; the guide `rooms/chapel` and its figure `chapel` |
| `tool/tool.wav` | byte-identical | `tests/test_tool.py` |

## Source, licence and attribution, file by file

### `chapel/`: a chapel (CC BY 4.0)

Attribution: **"Impulse response from A. Author, 'A deposit', Zenodo, 2026,
DOI 10.5281/zenodo.1, licensed CC BY 4.0. Change: one channel extracted."**

Atribución: **"Respuesta al impulso de A. Author, «A deposit», Zenodo, 2026,
DOI 10.5281/zenodo.1, con licencia CC BY 4.0. Cambio: se extrajo un canal."**

### `tool/`: a test file (MIT)

Attribution: **"tool.wav from a project, MIT License."**

## Purpose and scope of use

Attribution: **"Not a folder's."**
"""
_STRINGS = attributions(_README)
_EN = _STRINGS["chapel"]["en"]
_ES = _STRINGS["chapel"]["es"]
_READS = '```python\nir = np.load(repo / "tests/data/audio/chapel/ir.npz")\n```\n'


def test_the_readme_words_each_folder_once_per_language() -> None:
    assert _STRINGS == {
        "chapel": {
            "en": "Impulse response from A. Author, 'A deposit', Zenodo, 2026, DOI 10.5281/zenodo.1, "
            "licensed CC BY 4.0. Change: one channel extracted.",
            "es": "Respuesta al impulso de A. Author, «A deposit», Zenodo, 2026, DOI 10.5281/zenodo.1, "
            "con licencia CC BY 4.0. Cambio: se extrajo un canal.",
        },
        "tool": {"en": "tool.wav from a project, MIT License."},
    }


def test_a_page_that_reads_a_folder_without_its_attribution_is_reported() -> None:
    problems = unattributed([("guide.mdx", "en", _READS)], _STRINGS)
    assert problems == [
        "guide.mdx: reads tests/data/audio/chapel/ and does not print its English attribution: "
        f'"{_EN}"'
    ]


def test_an_attribution_wrapped_over_lines_and_linked_is_printed() -> None:
    wrapped = (
        "Impulse response from A. Author, 'A deposit', Zenodo,\n2026, DOI "
        "[10.5281/zenodo.1](https://doi.org/10.5281/zenodo.1), licensed\n"
        "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Change: one channel extracted.\n"
    )
    assert unattributed([("guide.mdx", "en", _READS + "\n" + wrapped)], _STRINGS) == []


@pytest.mark.parametrize("name", ["guide.md", "guide.mdx"])
def test_a_link_wrapped_over_a_line_end_or_by_reference_prints_its_words(
    name: str,
) -> None:
    head = "Impulse response from A. Author, 'A deposit', Zenodo, 2026, DOI 10.5281/zenodo.1, "
    tail = ". Change: one channel extracted.\n"
    wrapped = f"{head}[licensed CC BY\n4.0](https://creativecommons.org/licenses/by/4.0/){tail}"
    reference = f"{head}[licensed CC BY 4.0][cc]{tail}\n[cc]: https://creativecommons.org/licenses/by/4.0/\n"
    collapsed = f"{head}[licensed CC BY 4.0][]{tail}\n[licensed CC BY 4.0]: https://example.org/\n"
    for page in (wrapped, reference, collapsed):
        assert unattributed([(name, "en", f"{_READS}\n{page}")], _STRINGS) == []


def test_each_language_prints_its_own_attribution() -> None:
    spanish: list[tuple[str, Language, str]] = [
        ("es/guide.mdx", "es", f"{_READS}\n{_EN}\n")
    ]
    assert unattributed(spanish, _STRINGS) == [
        f'es/guide.mdx: reads tests/data/audio/chapel/ and does not print its Spanish attribution: "{_ES}"'
    ]
    assert unattributed([("es/guide.mdx", "es", f"{_READS}\n{_ES}\n")], _STRINGS) == []


def test_a_folder_the_readme_does_not_attribute_in_the_language_is_reported() -> None:
    page = '```python\nx = io.read(repo / "tests/data/audio/tool/a.wav")\n```\n'
    assert unattributed([("es/io.mdx", "es", page)], _STRINGS) == [
        "es/io.mdx: reads tests/data/audio/tool/, and tests/data/audio/README.md gives that "
        'folder no Spanish attribution (Atribución: **"..."**)'
    ]


@pytest.mark.parametrize(
    "code",
    [
        'ir = np.load(repo / "tests" / "data" / "audio" / "chapel" / "ir.npz")',
        'ir = np.load(repo / "tests/data" / "audio/chapel")',
        'ir = np.load(Path("tests", "data", "audio", "chapel", "ir.npz"))',
        'ir = np.load(os.path.join(root, "tests", "data", "audio", "chapel"))',
        'ir = np.load(Path("tests/data/audio") / "chapel" / "ir.npz")',
        'ir = np.load(pathlib.Path(repo, "tests/data/audio") / "chapel" / name)',
        'ir = np.load(Path("tests/data/audio").joinpath("chapel", "ir.npz"))',
        'ir = np.load(repo.joinpath("tests", "data").joinpath("audio", "chapel"))',
        'ir = np.load("tests/data/audio/" + "chapel" + "/ir.npz")',
        'ir = np.load(str(repo) + "/tests/data/audio/" + "chapel")',
        'ir = np.load("/".join(["tests", "data", "audio", "chapel"]))',
        'ir = np.load("/".join(("tests/data/audio", "chapel", "ir.npz")))',
        'ir = np.load(Path("tests/data/audio/") / "chapel" / "ir.npz")',
        'ir = np.load(Path("tests/data/audio") / "/chapel" / "ir.npz")',
        'ir = np.load(os.path.join("tests/data/audio/", "chapel/", "ir.npz"))',
    ],
)
def test_a_path_built_from_literals_reads_its_folder(code: str) -> None:
    assert folders_read(f"```python\n{code}\n```\n") == {"chapel"}


def test_what_reads_no_folder() -> None:
    # The README is no folder; a name is not followed (the documented limit);
    # two literals a name stands between are not one path.
    assert folders_read("Provenance in `tests/data/audio/README.md`.\n") == set()
    assert (
        folders_read(
            '```python\nfolder = "chapel"\nnp.load(repo / "tests/data/audio" / folder)\n```\n'
        )
        == set()
    )
    assert (
        folders_read(
            '```python\nnp.load(repo / "tests/data/audio" / sub / "chapel")\n```\n'
        )
        == set()
    )


def test_a_path_named_in_prose_reads_its_folder() -> None:
    assert folders_read(
        "The take `tests/data/audio/chapel/ir.npz` is committed.\n"
    ) == {"chapel"}


def test_an_attribution_in_a_code_comment_is_not_printed() -> None:
    page = f'```python\n# {_EN}\nir = np.load(repo / "tests/data/audio/chapel/ir.npz")\n```\n'
    assert len(unattributed([("guide.md", "en", page)], _STRINGS)) == 1


@pytest.mark.parametrize(
    ("name", "page"),
    [
        pytest.param("guide.md", f"{_READS}\n<!-- {_EN} -->\n", id="an HTML comment"),
        pytest.param("guide.mdx", f"{_READS}\n{{/* {_EN} */}}\n", id="an MDX comment"),
        pytest.param(
            "guide.mdx",
            f'---\ntitle: "A guide"\ndescription: "{_EN}"\n---\n\n{_READS}',
            id="a frontmatter field",
        ),
        pytest.param(
            "guide.mdx",
            f'{_READS}\n<ThemeImage src="chapel.svg" alt="{_EN}" />\n',
            id="a component's attribute",
        ),
        pytest.param(
            "guide.md", f'{_READS}\n<img src="chapel.svg" alt="{_EN}">\n', id="an alt"
        ),
        pytest.param("guide.mdx", f"{_READS}\nThe data: `{_EN}`\n", id="a code span"),
        pytest.param(
            "guide.md", f"{_READS}\n![{_EN}](chapel.svg)\n", id="a Markdown image's alt"
        ),
        pytest.param(
            "guide.mdx", f"{_READS}\n![{_EN}](chapel.svg)\n", id="an image's alt in MDX"
        ),
        pytest.param(
            "guide.md",
            f"{_READS}\n[{_EN}]: https://example.org/chapel\n",
            id="a link definition",
        ),
    ],
)
def test_an_attribution_the_page_does_not_show_as_prose_is_not_printed(
    name: str, page: str
) -> None:
    # Each is text the page hides or shows as code, never the credit itself.
    assert len(unattributed([(name, "en", page)], _STRINGS)) == 1
    shown = page.replace(_EN, "").rstrip() + f"\n\n{_EN}\n"
    assert unattributed([(name, "en", shown)], _STRINGS) == []


def test_the_readme_names_the_guides_that_read_each_folder() -> None:
    assert consumers(_README) == {("rooms/chapel", "chapel")}


def test_a_named_guide_whose_reading_the_test_does_not_see_is_reported() -> None:
    reads = '```python\nir = np.load(repo / "tests/data/audio/chapel/ir.npz")\n```\n'
    by_name = '```python\nfolder = "chapel"\nir = np.load(repo / "tests/data/audio" / folder)\n```\n'
    pages: list[tuple[str, Language, str]] = [
        ("site/src/content/docs/rooms/chapel.mdx", "en", reads),
        ("site/src/content/docs/es/rooms/chapel.mdx", "es", by_name),
    ]
    assert unread(pages, consumers(_README)) == [
        "site/src/content/docs/es/rooms/chapel.mdx: the README names it as reading "
        "tests/data/audio/chapel/, and the test does not see it read that folder",
    ]


def test_a_file_of_the_github_edition_is_left_to_its_generator(tmp_path: Path) -> None:
    """``make llms`` writes the edition from the English page, which is read here."""
    site = tmp_path / "site" / "src" / "content" / "docs" / "rooms"
    docs = tmp_path / "docs" / "rooms"
    site.mkdir(parents=True)
    docs.mkdir(parents=True)
    (site / "chapel.mdx").write_text(_READS, encoding="utf-8")
    (docs / "chapel.md").write_text(
        f"{EDITION_MARK}rooms/chapel.mdx: edit that page. -->\n\n{_READS}",
        encoding="utf-8",
    )
    (docs / "notes.md").write_text(_READS, encoding="utf-8")
    assert [name for name, _, _ in published_pages(tmp_path)] == [
        "site/src/content/docs/rooms/chapel.mdx",
        "docs/rooms/notes.md",
    ]


def test_every_folder_of_measured_data_is_attributed_in_the_readme() -> None:
    strings = attributions(README.read_text(encoding="utf-8"))
    folders = sorted(path.name for path in AUDIO.iterdir() if path.is_dir())
    assert sorted(strings) == folders
    assert [folder for folder in folders if "en" not in strings[folder]] == []


@pytest.mark.whole_tree
def test_every_page_that_reads_a_data_folder_prints_its_attribution() -> None:
    readme = README.read_text(encoding="utf-8")
    pages = list(published_pages())
    assert len(pages) > 100, "no pages found: the trees moved"
    # Every guide the README names is seen reading its folder, in both
    # languages, so a page the reader stops following fails instead of passing.
    assert unread(pages, consumers(readme)) == []
    assert unattributed(pages, attributions(readme)) == []
