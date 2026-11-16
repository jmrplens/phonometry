#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A script that walks ``docs/`` knows the GitHub edition when it meets a file of it.

``make llms`` writes the guides under ``docs/`` from their site pages, and each
file it writes opens with a comment naming its page (``scripts/github_edition.py``).
A check that walks the tree and reads such a file as written by hand reports a
dash, a number or a fence of the page a second time, in a file nobody can fix
by editing it, and keys its registries by a path the generator owns. So every
script that names the ``docs/`` tree itself as a root, rather than one file
under it, imports the module that tells the edition apart; each check then
holds what it does with a file of the edition to a test of its own.

Two kinds of script are read: the Python ones under ``scripts/``, through
their syntax tree, and the site's own code under ``site/`` (its scripts, its
library and its components), line by line, since no JavaScript parser runs
here. A Python script imports ``github_edition``; a module of the site imports
``site/src/lib/agent-md/edition.mjs``, where ``EDITION_MARK`` and
``isEditionFile`` live.
"""

from __future__ import annotations

import ast
import os
import pathlib
import re
import textwrap

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
_SITE = _ROOT / "site"

#: The suffixes of the site's own code.
_SITE_SUFFIXES = frozenset({".js", ".mjs", ".cjs", ".ts", ".mts", ".astro"})
#: The directories under the site that hold installed or built code.
_SITE_SKIPPED = frozenset({"node_modules", "dist", ".astro"})
#: How a comment line opens in the site's code.
_SITE_COMMENTS = ("//", "/*", "*")
#: A ``join`` or ``resolve`` that ends at the tree: ``join(REPO, 'docs')``,
#: ``resolve(here, '..', '..', 'docs')``. The arguments before it are kept, to
#: tell the site's own ``'content', 'docs'`` apart.
_SITE_DOCS_CALL = re.compile(r"""\b(?:join|resolve)\(([^()]*?)['"`]docs/?['"`]\s*\)""")
#: A relative path that ends at the tree, as ``new URL('../../docs/', ...)`` takes it.
_SITE_DOCS_PATH = re.compile(r"""['"`](?:\.\./)+docs/?['"`]""")
#: An import from the site's module of the edition, by any relative path to it.
_SITE_EDITION_IMPORT = re.compile(r"""\bfrom\s+['"][^'"]*\bedition\.mjs['"]""")


def _is_division(node: ast.AST | None) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)


def docs_tree_lines(source: str) -> list[int]:
    """The lines of a module that name the ``docs/`` tree itself as a path.

    ``ROOT / "docs"`` names the tree, and so does the string ``"docs"`` held
    as a root (in a tuple, a list, an assignment or a call). ``ROOT / "docs" /
    "ERRATA.md"`` names one file under it, and ``... / "content" / "docs"``
    another tree, the site's, so neither is the tree.

    :param source: The text of a Python module.
    :return: The 1-based lines, in order.
    """
    tree = ast.parse(source)
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    lines: list[int] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and node.value == "docs"):
            continue
        parent = parents.get(node)
        if _is_division(parent):
            assert isinstance(parent, ast.BinOp)
            under_another = isinstance(parent.left, ast.BinOp) and isinstance(
                parent.left.right, ast.Constant
            )
            grand = parents.get(parent)
            names_a_file = (
                _is_division(grand)
                and isinstance(grand, ast.BinOp)
                and grand.left is parent
            )
            if parent.right is node and not under_another and not names_a_file:
                lines.append(node.lineno)
        elif isinstance(parent, ast.Tuple | ast.List | ast.Assign | ast.Call):
            lines.append(node.lineno)
    return sorted(lines)


def knows_the_edition(source: str) -> bool:
    """Whether a module imports ``github_edition``, by either form of import."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(
            alias.name == "github_edition" for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "github_edition":
            return True
    return False


def site_docs_tree_lines(source: str) -> list[int]:
    """The lines of a module of the site that name the repository's ``docs/`` tree.

    The reading is lexical, as ``scripts/check_fence_readers.py`` reads the
    site: a line of code, not of comment, that ends a ``join`` or a
    ``resolve`` at ``'docs'``, or spells a relative path that ends there. The
    site's own content tree, ``join(SITE, 'src', 'content', 'docs')``, is
    another tree, and ``join(REPO, 'docs', 'CONFORMANCE.md')`` one file.

    :param source: The text of a module of the site.
    :return: The 1-based lines, in order.
    """
    lines: list[int] = []
    for number, line in enumerate(source.splitlines(), start=1):
        code = line.strip()
        if code.startswith(_SITE_COMMENTS):
            continue
        calls = (
            "content" not in match.group(1) for match in _SITE_DOCS_CALL.finditer(code)
        )
        if any(calls) or _SITE_DOCS_PATH.search(code):
            lines.append(number)
    return lines


def site_knows_the_edition(source: str) -> bool:
    """Whether a module of the site imports from ``agent-md/edition.mjs``."""
    return _SITE_EDITION_IMPORT.search(source) is not None


def _site_files() -> list[pathlib.Path]:
    """The site's own code, installed and built code left out."""
    found: list[pathlib.Path] = []
    for directory, subdirectories, names in os.walk(_SITE):
        subdirectories[:] = sorted(
            name for name in subdirectories if name not in _SITE_SKIPPED
        )
        found.extend(
            pathlib.Path(directory) / name
            for name in sorted(names)
            if pathlib.Path(name).suffix in _SITE_SUFFIXES
        )
    return found


@pytest.mark.parametrize(
    ("source", "lines"),
    [
        ('DOCS = ROOT / "docs"\n', [1]),
        ('ROOTS = ("docs", "site/src/content/docs")\n', [1]),
        ('for path in pathlib.Path("docs").rglob("*.md"):\n    pass\n', [1]),
        ('ERRATA = ROOT / "docs" / "ERRATA.md"\n', []),
        ('CONTENT = ROOT / "site" / "src" / "content" / "docs"\n', []),
        ('message = "see docs/README.md"\n', []),
    ],
)
def test_the_reading_tells_the_tree_from_a_file_under_it(
    source: str, lines: list[int]
) -> None:
    assert docs_tree_lines(source) == lines


def test_a_walker_of_the_tree_that_does_not_know_the_edition_is_found() -> None:
    """The defect the rule closes, and the import that clears it."""
    walker = textwrap.dedent(
        """
        DOCS = ROOT / "docs"
        pages = sorted(DOCS.rglob("*.md"))
        """
    )
    assert docs_tree_lines(walker)
    assert not knows_the_edition(walker)
    assert knows_the_edition("from github_edition import is_edition_file\n" + walker)
    assert knows_the_edition("import github_edition\n" + walker)


@pytest.mark.whole_tree
def test_every_script_that_walks_docs_knows_the_edition() -> None:
    """A script that names the tree imports ``github_edition``; one file is no tree."""
    found: dict[str, list[int]] = {}
    for path in sorted(_SCRIPTS.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        lines = docs_tree_lines(source)
        if lines and not knows_the_edition(source):
            found[path.relative_to(_ROOT).as_posix()] = lines
    assert found == {}, (
        "these scripts name the docs/ tree and never ask which of its files "
        f"the GitHub edition writes (scripts/github_edition.py): {found}"
    )
    walkers = [
        path
        for path in _SCRIPTS.rglob("*.py")
        if docs_tree_lines(path.read_text(encoding="utf-8"))
    ]
    assert len(walkers) >= 9, "the reading stopped finding the checks that walk docs/"


@pytest.mark.parametrize(
    ("source", "lines"),
    [
        ("const DOCS = join(REPO, 'docs');\n", [1]),
        ("const dirs = [join(REPO, 'docs'), join(SITE, 'src', 'content')];\n", [1]),
        ("const dir = resolve(here, '..', '..', 'docs');\n", [1]),
        ("const url = new URL('../../docs/', import.meta.url);\n", [1]),
        ("const CONTENT = join(SITE, 'src', 'content', 'docs');\n", []),
        ("const text = read(join(REPO_DIR, 'docs', 'CONFORMANCE.md'));\n", []),
        ("// Usage: node scripts/x.mjs [--sources ../docs]\n", []),
        ("const kind = await getCollection('docs');\n", []),
    ],
)
def test_the_site_reading_tells_the_tree_from_a_file_under_it(
    source: str, lines: list[int]
) -> None:
    assert site_docs_tree_lines(source) == lines


def test_a_site_walker_of_the_tree_that_does_not_know_the_edition_is_found() -> None:
    """The defect the rule closes in the site's code, and the import that clears it.

    ``check-math-render.mjs`` walked ``docs/`` for a stray display delimiter
    and reported each one of a page a second time, at the page's copy.
    """
    walker = "const sourceDirs = [join(REPO, 'docs'), join(SITE, 'src', 'content')];\n"
    assert site_docs_tree_lines(walker)
    assert not site_knows_the_edition(walker)
    for path in ("../src/lib/agent-md/edition.mjs", "../edition.mjs", "./edition.mjs"):
        assert site_knows_the_edition(
            f"import {{ isEditionFile }} from '{path}';\n" + walker
        )


@pytest.mark.whole_tree
def test_every_module_of_the_site_that_walks_docs_knows_the_edition() -> None:
    """A module of the site that names the tree imports from ``edition.mjs``."""
    found: dict[str, list[int]] = {}
    walkers: list[str] = []
    for path in _site_files():
        source = path.read_text(encoding="utf-8")
        lines = site_docs_tree_lines(source)
        if not lines:
            continue
        name = path.relative_to(_ROOT).as_posix()
        walkers.append(name)
        if not site_knows_the_edition(source):
            found[name] = lines
    assert found == {}, (
        "these modules of the site name the docs/ tree and never ask which of "
        f"its files the GitHub edition writes (site/src/lib/agent-md/edition.mjs): {found}"
    )
    assert {"site/scripts/agent-md.mjs", "site/scripts/check-math-render.mjs"} <= set(
        walkers
    ), "the reading stopped finding the site's modules that walk docs/"


def test_the_glossary_copy_is_read_where_its_cards_are_written(
    tmp_path: pathlib.Path,
) -> None:
    """A copy of a page a component writes from data is no copy to skip.

    The glossary page is one ``<Glossary />`` tag; its cards come from
    ``site/src/data/glossary.mjs``, which no check reads, so the subscript,
    Euler-number and digit-grouping checks read the edition's copy of it.
    """
    from github_edition import EDITION_MARK, is_edition_copy, is_edition_file

    glossary = tmp_path / "glossary.md"
    glossary.write_text(
        f"{EDITION_MARK}reference/glossary.mdx: edit that page.\n\n# Glossary\n",
        encoding="utf-8",
    )
    guide = tmp_path / "guide.md"
    guide.write_text(
        f"{EDITION_MARK}signals/levels.mdx: edit that page.\n\n# Levels\n",
        encoding="utf-8",
    )
    assert is_edition_file(glossary)
    assert not is_edition_copy(glossary)
    assert is_edition_copy(guide)
    real = _ROOT / "docs" / "reference" / "glossary.md"
    assert is_edition_file(real)
    assert not is_edition_copy(real)
