#!/usr/bin/env python3
r"""Refuse an em dash in the prose the project publishes.

The house style writes its prose without the em dash: a clause that would hang
off one is a sentence of its own, a parenthesis, a colon or a comma, chosen by
what the sentence needs. The rule covers everything a reader sees under the
project's name, which is more than the pages of the site: the docs mirrors,
the CHANGELOG, the README, the docstrings the API reference is generated from,
and the titles, labels and annotations drawn into the figures.

What is NOT prose keeps its dash, and every exemption below says why:

- **A standard's title reproduced as printed.** ISO, IEC, EN and DIN write
  "Acoustics — Part 2: ..." and "Erschütterungen im Bauwesen — Teil 3: ..."
  with the dash, and a citation reproduces its source. The guard exempts a
  dash that sits in a frontmatter ``title:`` value, in an italic span, in a
  bibliographic entry (author and year first, the title after), inside
  quotation marks or guillemets, or on a line that reads ``— Part 3:``,
  ``— Teil 3:``, ``— Partie 3:`` or ``— Parte 3:``. A quotation long enough
  is wrapped by the paragraph that carries it, opening on one line and
  closing two lines below, so the open quotation is carried from line to
  line within a paragraph exactly as the italic span is.
- **Code.** A fenced block, an inline code span and a string a test compares
  with are data, not prose, and a dash that fills a whole table cell, or a
  whole slash-separated item of one, is the placeholder of an empty cell, not
  a sentence. The glossary cards are prose in a data module and are read as
  such.
- **Two bare dashes** in a table row separator or a horizontal rule are
  hyphens, not em dashes; only U+2014 is looked for.

Exit status 0 when the prose is clean, 1 otherwise, naming every file and line.
"""

from __future__ import annotations

import argparse
import ast
import io
import pathlib
import re
import sys
import tokenize

EM_DASH = "—"

#: Where the published prose lives: the pages and their mirrors, the package
#: docstrings the API reference is generated from, and the text the figure
#: and diagram generators draw. Tests are not published and keep their
#: dashes, and the llms mirrors and the generated API pages are regenerated
#: from what is listed here and need no scan of their own.
DEFAULT_ROOTS = (
    "docs",
    "site/src/content/docs",
    "site/src/data/glossary.mjs",
    "src/phonometry",
    "scripts/figures",
    "scripts/diagrams",
    "CHANGELOG.md",
    "README.md",
    "README_PYPI.md",
    "CONTRIBUTING.md",
)

#: Bold markers, which are not italics and are taken out before counting.
_BOLD = re.compile(r"\*\*")
#: A part number after the dash, which only a standard's title prints.
_PART_AFTER_DASH = re.compile(EM_DASH + r"\s*(?:Part|Teil|Partie|Parte)\s+\d")
#: A dash inside quotation marks or guillemets: the text reproduces a source.
#: Not an attribute value (``alt="..."``) nor a YAML value (``description:
#: "..."``), which are prose of the page's own.
_QUOTED = re.compile(r"(?<!=)(?<!: )[\"«“][^\"»”\n]*" + EM_DASH + r"[^\"»”\n]*[\"»”]")
#: The delimiter that closes each opening one. A quotation is closed by its
#: own mark, so a straight quote inside guillemets does not end them.
_QUOTE_PAIRS = {'"': '"', "«": "»", "“": "”"}
#: What may sit before a straight quote that opens a quotation. A straight
#: quote is the one mark that opens and closes with the same character, so it
#: is read as an opening one only where an opening one can stand.
_BEFORE_OPENING = ("", " ", "\t", "(", "[", "{")
#: An inline code span.
_CODE_SPAN = re.compile(r"`[^`\n]*`")
#: A row of a pipe table.
_TABLE_ROW = re.compile(r"^\s*\|.*\|")
#: A dash that fills a whole cell, or a whole slash-separated item of one: the
#: placeholder for "there is none", not a sentence. A parameter table writes
#: the unit of a name that has none as ``—``, and the unit of a row that
#: documents two names at once as ``— / h``, so the placeholder has to be read
#: item by item or that one row ends up saying "none" where every other row of
#: its column says ``—``.
_PLACEHOLDER_ITEM = re.compile(r"(?:^|(?<=/))\s*" + EM_DASH + r"\s*(?=/|$)")
#: A frontmatter title, which reproduces the document's own title.
_TITLE_LINE = re.compile(r"^\s*(?:-\s*)?title:\s")
#: The first line of a bibliographic entry, author and year: the lines of the
#: entry reproduce a title as printed, dashes and all.
_REFERENCE_ENTRY = re.compile(r"^\s*(?:-|\d+\.)\s.*\(\d{4}[a-z]?\)")


def _outside_italics(line: str, *, italic_open: bool) -> tuple[str, bool]:
    """The characters of the line outside italic spans, and the state at its end.

    A title in italics is a citation reproduced as printed, and the
    bibliography wraps a title over several lines, so the italic state is
    carried from one line to the next within a paragraph.
    """
    text = _BOLD.sub("", line)
    kept: list[str] = []
    for char in text:
        if char == "*":
            italic_open = not italic_open
        elif not italic_open:
            kept.append(char)
    return "".join(kept), italic_open


def _opens_quotation(line: str, index: int) -> bool:
    """Whether the mark at ``index`` opens a quotation.

    A guillemet and a curly quote say which end they are. A straight quote
    does not, so it opens a quotation only where an opening one can stand:
    after nothing, a space or an opening bracket, and before a character that
    is not a space. That also settles the two marks that are not quotation at
    all, an attribute value (``alt="..."``) and a YAML value (``description:
    "..."``): neither of their quotes opens anything, so the prose of the
    value is scanned like any other and the marks do not run on.
    """
    if line[index] != '"':
        return True
    if line[index - 1 : index] == "=" or line[index - 2 : index] == ": ":
        return False
    return line[index - 1 : index] in _BEFORE_OPENING and line[
        index + 1 : index + 2
    ] not in ("", " ", "\t")


def _outside_quotations(line: str, *, closer: str | None) -> tuple[str, str | None]:
    """The characters of the line outside quotations, and the state at its end.

    A citation is reproduced as printed, and a title long enough is wrapped by
    the paragraph that quotes it: the opening mark sits on one line and the
    closing one two lines below, with the dash of the title in between. A
    line-scoped match cannot see that such a dash is inside the quotation, so
    the open quotation is carried from one line to the next within a
    paragraph, as the italic state is.
    """
    kept: list[str] = []
    for index, char in enumerate(line):
        if closer is not None:
            if char == closer:
                closer = None
            continue
        if char in _QUOTE_PAIRS and _opens_quotation(line, index):
            closer = _QUOTE_PAIRS[char]
            continue
        kept.append(char)
    return "".join(kept), closer


def _strip_exempt_markdown(
    line: str, *, italic_open: bool, quote_closer: str | None
) -> tuple[str, bool, str | None]:
    """The line with every exempt use of the dash removed, and the carried state."""
    if _TITLE_LINE.match(line):
        return "", italic_open, quote_closer
    line = _CODE_SPAN.sub("", line)
    if _TABLE_ROW.match(line):
        line = "|".join(_PLACEHOLDER_ITEM.sub("", cell) for cell in line.split("|"))
    line, quote_closer = _outside_quotations(line, closer=quote_closer)
    line, italic_open = _outside_italics(line, italic_open=italic_open)
    if _PART_AFTER_DASH.search(line):
        return "", italic_open, quote_closer
    return line, italic_open, quote_closer


def markdown_hits(text: str) -> list[int]:
    """The 1-based lines of a markdown or MDX page that carry a prose dash."""
    hits: list[int] = []
    in_fence = False
    fence = ""
    italic_open = False
    quote_closer: str | None = None
    in_reference = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence = True, marker
            elif marker == fence:
                in_fence = False
            continue
        if in_fence:
            continue
        if not stripped:
            italic_open = False
            quote_closer = None
            in_reference = False
            continue
        if _REFERENCE_ENTRY.match(line):
            in_reference = True
        elif not line.startswith((" ", "\t")):
            in_reference = False
        prose, italic_open, quote_closer = _strip_exempt_markdown(
            line, italic_open=italic_open, quote_closer=quote_closer
        )
        if EM_DASH in prose and not in_reference:
            hits.append(number)
    return hits


def _string_is_prose(value: str) -> bool:
    """Whether a string literal with a dash is prose and not a placeholder."""
    if value.strip() == EM_DASH:
        return False
    if _PART_AFTER_DASH.search(value):
        return False
    return not _QUOTED.search(value)


def python_hits(text: str) -> list[int]:
    """The 1-based lines of a module whose docstrings, comments or strings carry a dash."""
    hits: set[int] = set()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return [n for n, line in enumerate(text.splitlines(), 1) if EM_DASH in line]
    for token in tokens:
        if EM_DASH not in token.string:
            continue
        if token.type == tokenize.COMMENT:
            hits.add(token.start[0])
        elif token.type == tokenize.STRING:
            try:
                value = ast.literal_eval(token.string)
            except (ValueError, SyntaxError):
                value = token.string
            if isinstance(value, str) and _string_is_prose(value):
                for offset, line in enumerate(token.string.splitlines()):
                    if EM_DASH in line:
                        hits.add(token.start[0] + offset)
        elif token.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
            hits.add(token.start[0])
    return sorted(hits)


def data_hits(text: str) -> list[int]:
    """The 1-based lines of a data module (the glossary cards) whose text carries a dash.

    A comment is not published and keeps its dash; a standard's title is
    exempt as everywhere else.
    """
    hits: list[int] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if EM_DASH not in line or line.lstrip().startswith(("//", "*", "/*")):
            continue
        if _PART_AFTER_DASH.search(line):
            continue
        hits.append(number)
    return hits


def scan(path: pathlib.Path) -> list[int]:
    """The offending lines of one file, by its kind."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        return python_hits(text)
    if path.suffix in {".md", ".mdx"}:
        return markdown_hits(text)
    if path.suffix == ".mjs":
        return data_hits(text)
    return []


#: Local working notes under docs/, gitignored and never published.
_UNPUBLISHED = ("docs/superpowers",)


def iter_files(roots: tuple[str, ...]) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for root in roots:
        base = pathlib.Path(root)
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            files.extend(
                p
                for p in sorted(base.rglob("*"))
                if p.suffix in {".py", ".md", ".mdx", ".mjs"}
                and not any(str(p).startswith(u) for u in _UNPUBLISHED)
            )
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", default=DEFAULT_ROOTS)
    parser.add_argument(
        "--count", action="store_true", help="print one line per file with its count"
    )
    args = parser.parse_args()
    total = 0
    files = 0
    for path in iter_files(tuple(args.paths)):
        lines = scan(path)
        if not lines:
            continue
        files += 1
        total += len(lines)
        if args.count:
            print(f"{path}: {len(lines)}")
        else:
            for number in lines:
                print(f"{path}:{number}: em dash in published prose")
    if total:
        print(
            f"{total} em dash(es) in the published prose of {files} file(s); "
            "rewrite each as a sentence, a parenthesis, a colon or a comma.",
            file=sys.stderr,
        )
        return 1
    print("No em dash in the published prose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
