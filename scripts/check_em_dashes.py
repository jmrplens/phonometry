#!/usr/bin/env python3
r"""Refuse an em dash in the prose the project publishes.

The house style writes its prose without the em dash: a clause that would hang
off one is a sentence of its own, a parenthesis, a colon or a comma, chosen by
what the sentence needs. The rule covers everything a reader sees under the
project's name, which is more than the pages of the site: the docs mirrors,
the CHANGELOG, the README, the docstrings the API reference is generated from,
the titles, labels and annotations drawn into the figures, and the robots.txt
the site serves, which a crawler and anyone who opens it read as written.

What is NOT prose keeps its dash, and every exemption below says why:

- **A standard's title reproduced as printed.** ISO, IEC, EN and DIN write
  "Acoustics — Part 2: ..." and "Erschütterungen im Bauwesen — Teil 3: ..."
  with the dash, and a citation reproduces its source. The guard exempts a
  dash that sits in a frontmatter ``title:`` value, in an italic span, in a
  bibliographic entry (author and year first, the title after), inside
  quotation marks or guillemets, or right before a part number: ``— Part 3:``,
  ``— Teil 3:``, ``— Partie 3:`` or ``— Parte 3:``. Each exempts the dash it
  reads and no other on the line, so a title of several dashes is marked as
  one, in italics or quotation marks. A quotation long enough is wrapped by
  the paragraph that carries it, opening on one line and closing two lines
  below, so the open quotation is carried from line to line within a
  paragraph exactly as the italic span is; in a string, whose lines are read
  one by one, a quotation closes on its line or quotes nothing. A value of the
  frontmatter is read as one such text, over the lines it wraps: the site shows
  it as plain text, so it holds no span, no italics, no reference and no empty
  cell, the quotes that delimit it are YAML's, a quotation closes inside the
  value or quotes nothing, and nothing it opens reaches the next value or the
  body.
- **Code.** A fenced block, an inline code span and a string a test compares
  with are data, not prose, and a dash that fills a whole table cell, or a
  whole slash-separated item of one, is the placeholder of an empty cell, not
  a sentence. The glossary cards, the home page's text and the Spanish
  catalogue notes are prose in the site's data modules and are read as such.
- **Two bare dashes** in a table row separator or a horizontal rule are
  hyphens, not em dashes.

Maths on a page (``$...$`` and a ``$$`` block) is not prose either, but it
exempts nothing: the site shows a dash written there, and two dollar signs
are maths to it even where they were meant as money, so the dash is read,
whatever quotation, italic span, reference or part number stands around it.
What maths does not do is mark the prose around it. An asterisk between
dollar signs is a superscript star (``$DI_i^*$``, ``$F v^*$``) and a
quotation mark there is a symbol, so neither opens an italic span or a
quotation that would exempt the rest of the paragraph, and four digits in
parentheses (``$L(1000)$``, or a code span holding ``band(2000)``) open
no bibliographic entry. The code and maths spans are read together, a block
of the page at a time, as the site reads them, and a ``$$`` block is read
apart, as the site reads a fenced code block: a line of it that opens with
``+ ``, ``|`` or ``>`` starts no block of markdown, and the block ends the
paragraph before it, so nothing pairs across it, behind the marks of a
quotation or a list item as anywhere else. An italic span and a quotation stop
at the start of a block as a code span does, so one left open in a list item
is not closed by the next.

The character has other spellings that publish it all the same, and each is
read as the character where it is decoded on its way to a reader: the HTML
entities ``&mdash;``, ``&#8212;`` and ``&#x2014;`` in a page and in a string,
the escapes ``\u2014``, ``\U00002014`` and ``\N{EM DASH}`` in a string of a
module (whose value is what is read, so a raw string keeps its backslash),
``\u2014`` in a JSON string, ``\u2014`` and ``\u{2014}`` in a data module,
and ``\u2014`` and ``\U00002014`` in a double-quoted value of a page's
frontmatter, the one YAML value that decodes an escape, and in the JSON
strings of the JSON-LD its head carries, in a block of text or a single-quoted
value under a ``content`` key that opens as JSON does. Any other single-quoted
or plain value, block of text and comment of the frontmatter show the escape as
written, and so does the body of a page. A backslash escapes the character
after it in each of these languages, so ``\\u2014`` is never the dash.

The dash also has an ASCII spelling, the double hyphen, and the guard refuses
that too. Astro's smartypants turns ``--`` in the text of a page into an em
dash, so a docstring that joins two clauses with `` -- `` reaches the API
reference as the very character this guard refuses, and ``help()`` shows it as
the double hyphen it is. It is looked for where it is published:

- **A page and a docstring** are refused any run of two hyphens or more in
  their prose, spaced or not, because that is what smartypants converts. What
  is not prose keeps it: fenced and inline code, a literal block after ``::``,
  the body of a ``.. math::`` or ``.. code-block::`` directive, a doctest,
  math on a page (``$...$`` and a ``$$`` block, which remark-math keeps from
  smartypants), a link destination, a URL, a comment the page does not show
  (an HTML comment, an MDX comment ``{/* ... */}`` on an MDX page and a
  comment of the frontmatter), the value of an ``href``, ``src``, ``style``,
  ``id`` or ``class`` attribute (``var(--sl-color-accent)``), and a line that
  is only a rule: a docstring's heading underline, a table's separator row, a
  horizontal rule, a frontmatter fence. A run that fills a whole table cell,
  or a whole slash-separated item of one, is the empty-cell mark, as the em
  dash is. A docstring and the page generated from it read the same:
  ``scripts/generate_api_docs.py`` fences a code directive's body and a
  doctest as code, and turns the math into ``$`` and ``$$`` spans.
- **Any other string of a module, and the site's data modules**, are refused
  a double hyphen that stands between spaces (`` -- ``), the one form that is
  a dash there and not an option of a command line (``--keep``) or a
  decrement.
- **A plain-text file** is served as written, so a double hyphen there stays
  two hyphens and only the character is read.
- **A comment** is published nowhere, neither on the site nor by ``help()``,
  and keeps its double hyphens, the section rules (``# -- names ---``) among
  them. So does the docstring of a figure or diagram generator, which
  publishes only what it draws.

One more spelling of the dash is read in one place only: a single hyphen
between spaces that joins a list item's head to its text, as in
``* :func:`npd_level` - the interpolated event level``, in a page or a
package docstring, outside code and outside the comments a page does not
show. The head is an inline literal, a role, an interpreted span, a bold span
or a link, alone or several joined by a slash, a comma, "and" or "or", with
one parenthesis after them at most; the hyphen has to follow it, so a minus
inside a role (``:math:`445.2 F - 344.3```) is never read. Elsewhere a spaced
hyphen is also a minus (``32,3 - 26,3 dB``), and the rule holds there by
review.

Exit status 0 when the prose is clean, 1 otherwise, naming every file and line.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import pathlib
import re
import sys
import tokenize
from dataclasses import dataclass
from typing import TYPE_CHECKING

from markdown_fences import PageLine, code_lines, display_math_parts, page_lines
from markdown_spans import (
    SPAN_MARK,
    blank_inline_spans_by_block,
    block_starts,
    inside_quotation,
    lines_read_whole,
    replace_inline_spans_by_block,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

EM_DASH = "—"
#: What a dash in maths leaves in the text of a page: a private-use character,
#: so that no reading of the prose around it takes it for a dash of that prose.
_MATHS_DASH = "\ue000"

#: Where the published prose lives: the pages and their mirrors, the data
#: modules the site's pages are built from (the glossary cards, the home page's
#: text and examples, the Spanish catalogue notes), the package docstrings the
#: API reference is generated from, the text the figure and diagram
#: generators draw, and the one plain-text file of the site with prose of its
#: own, the robots.txt it serves under its subpath. Tests are not published and
#: keep their dashes, and the llms mirrors and the generated API pages are
#: regenerated from what is listed here and need no scan of their own.
DEFAULT_ROOTS = (
    "docs",
    "site/src/content/docs",
    "site/src/data",
    "src/phonometry",
    "scripts/figures",
    "scripts/diagrams",
    "CHANGELOG.md",
    "README.md",
    "README_PYPI.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "site/public/robots.txt",
)

#: Bold markers, which are not italics and are taken out before counting.
_BOLD = re.compile(r"\*\*")
#: A list bullet written with an asterisk, which is not an italic marker
#: either: left in, it opens a span that swallows the rest of the item.
_BULLET = re.compile(r"^\s*\*(?=\s)")
#: A part number after the dash, which only a standard's title prints.
_PART_AFTER_DASH = re.compile(EM_DASH + r"\s*(?:Part|Teil|Partie|Parte)\s+\d")
#: The delimiter that closes each mark that opens a quotation. A quotation is
#: closed by its own mark, so a straight quote inside guillemets does not end
#: them.
_QUOTE_PAIRS = {'"': '"', "«": "»", "“": "”"}
#: The marks that say which end they are, the only ones a data module's lines
#: can quote with: read as written, a straight quote there delimits a string,
#: and the prose between two of them quotes nothing.
_TYPOGRAPHIC_QUOTE_PAIRS = {"«": "»", "“": "”"}
#: What may sit before a straight quote that opens a quotation. A straight
#: quote is the one mark that opens and closes with the same character, so it
#: is read as an opening one only where an opening one can stand.
_BEFORE_OPENING = ("", " ", "\t", "\n", "(", "[", "{")
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
#: The HTML entities of the em dash, which a page and a string set as HTML
#: publish as the character.
_EM_DASH_ENTITY = re.compile(r"&(?:mdash|#0*8212|#[xX]0*2014);")
#: The escapes of a string literal that stand for the em dash: ``\u2014``,
#: Python's ``\U00002014`` and ``\N{EM DASH}`` (a name Python reads in any
#: case), and JavaScript's ``\u{2014}``. The letter of an escape is read as
#: written: ``\U2014`` is no escape of either language, and ``\u00002014`` is
#: the NUL character and four digits. A line that holds none of them holds no
#: escaped dash in either language; one that does is decoded with the escapes
#: of its own language alone.
_EM_DASH_ESCAPE = re.compile(r"\\(?:u2014|U00002014|N\{(?i:em dash)\}|u\{0*2014\})")
#: The escapes a Python string decodes to the em dash.
_PYTHON_EM_DASH_ESCAPE = re.compile(r"\\(?:u2014|U00002014|N\{(?i:em dash)\})")
#: The escapes a JavaScript or TypeScript string decodes to the em dash. It
#: reads ``\U`` and ``\N`` as the letters themselves, so ``\U00002014`` and
#: ``\N{EM DASH}`` publish letters and digits, never the dash.
_JS_EM_DASH_ESCAPE = re.compile(r"\\(?:u2014|u\{0*2014\})")
#: The escapes a double-quoted YAML value decodes to the em dash. ``\N`` is
#: YAML's next-line character there, not a named escape.
_YAML_EM_DASH_ESCAPE = re.compile(r"\\(?:u2014|U00002014)")
#: The one escape a JSON string has for the em dash.
_JSON_EM_DASH_ESCAPE = re.compile(r"\\u2014")


def _spells_em_dash(text: str) -> bool:
    """Whether the text writes the em dash, as the character or another spelling."""
    return bool(
        EM_DASH in text or _EM_DASH_ENTITY.search(text) or _EM_DASH_ESCAPE.search(text)
    )


def _decode_entities(text: str) -> str:
    """The text with each HTML entity of the em dash read as the character."""
    return _EM_DASH_ENTITY.sub(EM_DASH, text)


def _decode_escapes(text: str, escape: re.Pattern[str]) -> str:
    r"""The text with each escape of the em dash read as the character.

    The text is read from left to right as a string literal is: a backslash
    escapes the character after it, so ``\\u2014`` is an escaped backslash
    and the five characters ``u2014``, never the dash.

    :param escape: The escapes of the em dash in the language the text is
        written in, matched at a backslash.
    """
    pieces: list[str] = []
    done = 0
    while (backslash := text.find("\\", done)) >= 0:
        found = escape.match(text, backslash)
        if found is None:
            pieces.append(text[done : backslash + 2])
            done = backslash + 2
        else:
            pieces.extend((text[done:backslash], EM_DASH))
            done = found.end()
    pieces.append(text[done:])
    return "".join(pieces)


def _decode_spellings(text: str, escape: re.Pattern[str]) -> str:
    """The text with each entity and each escape of the em dash read as the character.

    :param escape: The escapes of the em dash in the language the text is
        written in.
    """
    return _decode_escapes(_decode_entities(text), escape)


def _decode_json_strings(line: str) -> str:
    """The line with the escape of the em dash read as the character in its JSON strings."""
    return _JSON_STRING.sub(
        lambda found: _decode_escapes(found.group(), _JSON_EM_DASH_ESCAPE), line
    )


def _blank_json_quotes(line: str) -> str:
    """The line with the quotes that delimit its JSON strings blanked, its columns kept.

    They are JSON's, so they quote nothing: whatever opens a string, a dash in it
    is read. A quote escaped in a string is one the string shows, so it does quote.
    """
    return _JSON_STRING.sub(
        lambda found: (
            " " + _ESCAPED_YAML_CHARACTER.sub(_shown_quote, found.group()[1:-1]) + " "
        ),
        line,
    )


#: The rest of a double-quoted YAML value, up to its closing quote, and of a
#: single-quoted one, whose only escape is a doubled quote.
_YAML_QUOTED_REST = {
    '"': re.compile(r'(?:[^"\\]|\\.)*"'),
    "'": re.compile(r"(?:[^']|'')*'"),
}
#: A backslash of a double-quoted YAML value or a JSON string, and the character
#: it escapes.
_ESCAPED_YAML_CHARACTER = re.compile(r"\\(.)")
#: What JSON-LD opens with, which tells it from the plain text a ``content`` key
#: of the head may hold as well.
_JSON_OPENS = ("{", "[")


def _shown_quote(escape: re.Match[str]) -> str:
    """An escaped quote as the page shows it, its column kept; any other escape as written."""
    return ' "' if escape.group(1) == '"' else escape.group()


@dataclass
class _Node:
    """Where the reading of one frontmatter line stands."""

    #: The column of the key or the sequence entry the next value belongs to.
    owner: int
    #: Whether a node may open here: at the start of a line, after a colon,
    #: an entry's dash, an opening bracket or a comma of a flow collection.
    open: bool = True
    #: The last key read on the line.
    key: str = ""
    #: Whether the rest of the line is read already.
    done: bool = False


@dataclass
class _Frontmatter:
    r"""A reading of a page's frontmatter, line by line, for its double-quoted values.

    YAML decodes a backslash escape in a double-quoted value only: a
    single-quoted or a plain value, a block of text (``|``, ``>``) and a
    comment show ``\u2014`` as the six characters it is. Each line is
    returned with the escapes decoded where YAML decodes them, and with the
    JSON strings of a ``content`` block decoded too, since that block is the
    JSON-LD of the head, which a search engine reads as JSON. What one line
    leaves open is carried to the next: a quoted value that wraps, a block
    of text and a plain value that wraps.

    The readings of the hyphens read the frontmatter for its comments
    instead: they leave the escapes as written and blank a comment, which
    the page does not show (see :attr:`decode_escapes` and
    :attr:`blank_comments`). The reading of the em dash reads it once more
    for the quotes that delimit a value, which are YAML's and quote nothing,
    and those that delimit a JSON string of the JSON-LD (see :attr:`blank_quotes`).
    """

    #: The quote of a value still open at the end of the last line.
    quote: str = ""
    #: The column a line of an open block of text is indented past.
    block: int | None = None
    #: Whether that block is the JSON-LD of a ``content`` key, which its first
    #: line says: ``None`` until it is read.
    json_block: bool | None = False
    #: Whether the single-quoted value open is the JSON-LD of a ``content`` key.
    json_value: bool = False
    #: The column a line that wraps an open plain value is indented past.
    plain: int | None = None
    #: How deep the line is inside a flow collection (``[...]``, ``{...}``).
    flow: int = 0
    #: Whether an escape of the em dash is read as the character where YAML
    #: decodes it, or left as written.
    decode_escapes: bool = True
    #: Whether a comment is blanked, its columns kept, or returned as written.
    blank_comments: bool = False
    #: Whether the quotes that delimit a value or a JSON string of its JSON-LD are
    #: blanked, its columns kept.
    blank_quotes: bool = False
    #: The column of a key with nothing after it on its line: the value that
    #: opens on the next line, deeper, wraps past that column.
    under_key: int | None = None

    def continues(self, line: str) -> bool:
        """Whether *line* carries on the value the lines above it left open."""
        if self.quote:
            return True
        indent = len(line) - len(line.lstrip(" "))
        return any(
            column is not None and (not line.strip() or indent > column)
            for column in (self.block, self.plain)
        )

    def decode(self, line: str) -> str:
        """The line with each escape of the em dash read where YAML decodes it.

        So it is unless :attr:`decode_escapes` is off; a comment is blanked
        if :attr:`blank_comments` is on.
        """
        indent = len(line) - len(line.lstrip(" "))
        if self.block is not None:
            if not line.strip() or indent > self.block:
                return self._block_line(line)
            self.block = None
        if self.plain is not None:
            if not line.strip() or indent > self.plain:
                return line
            self.plain = None
        pieces: list[str] = []
        at = 0
        if self.quote:
            at = self._quoted(line, 0, self.quote, pieces)
        if at < len(line):
            self._nodes(line, at, indent, pieces)
        return "".join(pieces)

    def _block_line(self, line: str) -> str:
        """A line of the open block of text, read as JSON if the block holds JSON."""
        if self.json_block is None and line.strip():
            self.json_block = line.lstrip().startswith(_JSON_OPENS)
        return self._as_json(line) if self.json_block else line

    def _as_json(self, text: str) -> str:
        """JSON-LD as this reading wants it: its escapes decoded, or its quotes blanked."""
        if self.decode_escapes:
            return _decode_json_strings(text)
        return _blank_json_quotes(text) if self.blank_quotes else text

    def _quoted(self, line: str, start: int, quote: str, pieces: list[str]) -> int:
        """Read a quoted value from ``start``, past its opening quote; return where it ends."""
        found = _YAML_QUOTED_REST[quote].match(line, start)
        end = found.end() if found is not None else len(line)
        self.quote = "" if found is not None else quote
        value = line[start:end]
        if found is not None and self.blank_quotes:
            value = value[:-1] + " "
        if quote == '"' and self.blank_quotes:
            value = _ESCAPED_YAML_CHARACTER.sub(_shown_quote, value)
        if quote == "'" and self.json_value:
            value = self._as_json(value)
        pieces.append(
            _decode_escapes(value, _YAML_EM_DASH_ESCAPE)
            if quote == '"' and self.decode_escapes
            else value
        )
        return end

    def _nodes(self, line: str, at: int, indent: int, pieces: list[str]) -> None:
        """Read the line from ``at`` on, node by node, into ``pieces``."""
        key = self.under_key
        node = _Node(owner=key if key is not None and indent > key else indent)
        while at < len(line) and not node.done:
            found = self._indicator(line, at, node, pieces)
            at = found if found is not None else self._plain(line, at, node, pieces)
        ends_on_key = node.open and bool(node.key) and not self.flow
        self.under_key = node.owner if ends_on_key else None

    def _indicator(
        self, line: str, at: int, node: _Node, pieces: list[str]
    ) -> int | None:
        """Read a blank, a comment, a quoted value or an indicator at ``at``.

        Returns where it ends, or None when a plain scalar opens there.
        """
        char = line[at]
        if char in " \t":
            pieces.append(char)
            return at + 1
        if char == "#" and (at == 0 or line[at - 1] in " \t"):
            comment = line[at:]
            pieces.append(" " * len(comment) if self.blank_comments else comment)
            node.done = True
            return len(line)
        if node.open:
            opened = self._node_start(line, at, node, pieces)
            if opened is not None:
                return opened
        return self._punctuation(line, at, node, pieces)

    def _node_start(
        self, line: str, at: int, node: _Node, pieces: list[str]
    ) -> int | None:
        """Read what may open a node: a quote, a sequence entry or a block of text."""
        char = line[at]
        if char in "\"'":
            self.json_value = (
                char == "'"
                and node.key == "content"
                and line[at + 1 :].lstrip().startswith(_JSON_OPENS)
            )
            pieces.append(" " if self.blank_quotes else char)
            end = self._quoted(line, at + 1, char, pieces)
            node.open, node.done = False, bool(self.quote)
            return end
        if char in "-?" and line[at + 1 : at + 2] in ("", " ", "\t"):
            pieces.append(char)
            node.owner = at
            return at + 1
        if char in "|>" and not self.flow:
            self.block = node.owner
            self.json_block = None if node.key == "content" else False
            pieces.append(line[at:])
            node.done = True
            return len(line)
        return None

    def _punctuation(
        self, line: str, at: int, node: _Node, pieces: list[str]
    ) -> int | None:
        """Read a bracket, a comma of a flow collection or the colon of a key."""
        char = line[at]
        if char in "[{" or (self.flow and char in "]},"):
            self.flow += {"[": 1, "{": 1, "]": -1, "}": -1}.get(char, 0)
            pieces.append(char)
            node.open = char not in "]}"
            return at + 1
        if char == ":" and (line[at + 1 : at + 2] in ("", " ", "\t") or self.flow):
            pieces.append(char)
            node.open = True
            return at + 1
        return None

    def _plain(self, line: str, at: int, node: _Node, pieces: list[str]) -> int:
        """Read a plain scalar from ``at``: a key, or a value that may wrap."""
        end = max(self._plain_end(line, at), at + 1)
        pieces.append(line[at:end])
        if line[end : end + 1] == ":":
            node.key, node.owner = line[at:end].strip(), at
        elif node.open and not self.flow:
            self.plain = node.owner
        node.open = False
        return end

    def _plain_end(self, line: str, start: int) -> int:
        """Where a plain scalar that opens at ``start`` ends on this line."""
        at = start
        while at < len(line):
            char = line[at]
            after = line[at + 1 : at + 2]
            if char == ":" and (after in ("", " ", "\t") or self.flow):
                break
            if char == "#" and line[at - 1] in " \t":
                break
            if self.flow and char in ",[]{}":
                break
            at += 1
        return at


def _decode_page(text: str) -> str:
    r"""A page with every spelling of the em dash it publishes read as the character.

    The entities are decoded wherever they stand, and an escape in the
    frontmatter only where YAML decodes it (see :class:`_Frontmatter`); in
    the body of the page a backslash escape is shown as written.
    """
    lines = _decode_entities(text).split("\n")
    _read_frontmatter(lines, _Frontmatter())
    return "\n".join(lines)


def _read_frontmatter(lines: list[str], reader: _Frontmatter) -> None:
    """Pass each line of a page's frontmatter through ``reader``, in place.

    A frontmatter opens on the page's first line and closes on the next
    ``---``; a page that opens on a ``---`` no later line closes has none, as
    Astro reads it, and its lines are the body's.
    """
    for index in range(1, _frontmatter_end(lines)):
        lines[index] = reader.decode(lines[index])


def _frontmatter_end(lines: list[str]) -> int:
    """The index of the line that closes a page's frontmatter, 0 when it has none.

    Its fences stand at the first column, as Astro reads them.
    """
    if not lines or lines[0].rstrip() != "---":
        return 0
    return next((n for n in range(1, len(lines)) if lines[n].rstrip() == "---"), 0)


def _frontmatter_head(lines: list[str]) -> int:
    """How many lines of a page its frontmatter takes, fences included, 0 with none."""
    closing = _frontmatter_end(lines)
    return closing + 1 if closing else 0


def _outside_italics(line: str, *, italic_open: bool) -> tuple[str, bool]:
    """The characters of the line outside italic spans, and the state at its end.

    A title in italics is a citation reproduced as printed, and the
    bibliography wraps a title over several lines, so the italic state is
    carried from one line to the next within a paragraph.

    Only a citation, though: see :func:`_is_caption`, which is what tells the
    two italics of this corpus apart.
    """
    text = _BULLET.sub(lambda m: " " * len(m.group()), _BOLD.sub("", line))
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
    ] not in ("", " ", "\t", "\n")


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


def _outside_closed_quotations(line: str, pairs: dict[str, str]) -> str:
    """The characters of the line outside each quotation it closes, read left to right.

    A string and a line of a plain-text file have no paragraph to carry an
    open quotation over, so a mark that does not close on its line quotes
    nothing. Reading from the left is what keeps the closing mark of one
    quotation from opening another over the dash between them. Handed the lines
    of one value joined, it reads them as one text, and the line breaks a
    quotation holds stay, so that each line is where it was.

    :param pairs: The mark that opens a quotation, and the one that closes it.
    """
    kept: list[str] = []
    at = 0
    while at < len(line):
        closer = pairs.get(line[at])
        end = line.find(closer, at + 1) if closer and _opens_quotation(line, at) else -1
        if end >= 0:
            kept.append("\n" * line.count("\n", at, end))
            at = end + 1
        else:
            kept.append(line[at])
            at += 1
    return "".join(kept)


def _is_caption(line: str) -> bool:
    """Whether the paragraph this line opens is one italic span, end to end.

    The two italics of this corpus are not the same thing. A citation sets a
    title in italics *inside* a sentence, and the title carries whatever dash
    the document prints. A figure caption sets the whole paragraph in italics,
    and it is the maintainer's own prose, which the house style writes without
    the em dash like every other sentence. Exempting the second along with the
    first is what let 262 dashes stand in the published pages, one to a caption,
    where no other gate could see them.

    The paragraph's first line is what says which: a caption opens with the
    ``*`` that opens the span, a citation opens with the text that introduces
    the title. Bold (``**``) and a list bullet (``* ``) are not italics at all.
    """
    stripped = line.lstrip()
    return (
        stripped.startswith("*")
        and not stripped.startswith("**")
        and not stripped.startswith("* ")
    )


def _strip_exempt_markdown(
    line: str, *, italic_open: bool, quote_closer: str | None, caption: bool = False
) -> tuple[str, bool, str | None]:
    """The line with every exempt use of the dash removed, and the carried state."""
    if _TABLE_ROW.match(line):
        line = "|".join(_PLACEHOLDER_ITEM.sub("", cell) for cell in line.split("|"))
    line, quote_closer = _outside_quotations(line, closer=quote_closer)
    if caption:
        # The whole paragraph is the span, so there is no "outside" to keep:
        # the state still has to be carried, because the closing ``*`` may be
        # several lines below.
        _, italic_open = _outside_italics(line, italic_open=italic_open)
    else:
        line, italic_open = _outside_italics(line, italic_open=italic_open)
    return _PART_AFTER_DASH.sub("", line), italic_open, quote_closer


def _span_remainder(span: str) -> str:
    """What one code or maths span leaves in the text of a page.

    A code span is data and leaves :data:`~markdown_spans.SPAN_MARK` alone,
    with the line breaks it held. A maths span leaves the mark on each of its
    lines, and after it a :data:`_MATHS_DASH` for each em dash that line of
    the span held: see :func:`_drop_code_and_math`.
    """
    if span.startswith("$"):
        return "\n".join(
            SPAN_MARK + _MATHS_DASH * piece.count(EM_DASH) for piece in span.split("\n")
        )
    return SPAN_MARK + "\n" * span.count("\n")


def _drop_code_and_math(text: str, *, kind: str) -> str:
    """The text of a page with its code and maths spans taken out, as the site reads them.

    Code and maths are read together, left to right and a block of the page
    at a time (:func:`markdown_spans.replace_inline_spans_by_block`), so a
    span that crosses a line break is out of both lines. What maths holds is
    read by remark-math, not as prose: its asterisk is a superscript star
    (``$DI_i^*$``, ``$F v^*$``) and its quotation mark a symbol, so neither
    opens an italic span or a quotation, and four digits in parentheses
    there (``$L(1000)$``) are no author's year. A dash in maths is still read,
    because the site shows it, and two dollar signs are maths to the site
    even where they were meant as money. It stays out of the prose's reading,
    as :data:`_MATHS_DASH`, because no title is reproduced in maths: no
    exemption covers it, whatever quotation, italic span, reference or part
    number stands around it.

    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    """
    return replace_inline_spans_by_block(text, _span_remainder, "`$", kind=kind)


@dataclass
class _PageReading:
    """What the reading of a page carries from one line to the next."""

    italic_open: bool = False
    quote_closer: str | None = None
    in_reference: bool = False
    caption: bool = False

    def open_block(self, line: str) -> None:
        """Start a block on ``line``: what the last one left open stays there."""
        self.italic_open, self.quote_closer = False, None
        self.in_reference = False
        self.caption = _is_caption(inside_quotation(line))

    def holds_dash(self, line: str, shown: str) -> bool:
        """Whether the line carries a dash no exemption covers, read through its marks.

        :param line: The line as written.
        :param shown: The same line with its code and maths spans out.
        """
        inner = inside_quotation(shown)
        if _REFERENCE_ENTRY.match(inner):
            self.in_reference = True
        elif not inside_quotation(line).startswith((" ", "\t")):
            self.in_reference = False
        prose, self.italic_open, self.quote_closer = _strip_exempt_markdown(
            inner,
            italic_open=self.italic_open,
            quote_closer=self.quote_closer,
            caption=self.caption,
        )
        return _MATHS_DASH in shown or (EM_DASH in prose and not self.in_reference)


def _lines_with_prose_dash(value: str) -> list[int]:
    """The 0-based lines of a text whose dash is neither quoted nor before a part number.

    As :func:`_holds_prose_dash`, over the lines of one text: a quotation and a
    part number each read across a line break of it.
    """
    outside = _PART_AFTER_DASH.sub(
        lambda part: "\n" * part.group().count("\n"),
        _outside_closed_quotations(value, _QUOTE_PAIRS),
    )
    return [
        offset for offset, line in enumerate(outside.split("\n")) if EM_DASH in line
    ]


def _frontmatter_hits(lines: list[str]) -> list[int]:
    """The 1-based lines of a page's frontmatter that carry a dash.

    A value is plain text the site shows as written, marks and all, so it holds
    no span, no italics, no reference and no empty cell, and the lines it wraps
    are one text (:func:`_lines_with_prose_dash`): what it leaves open stops
    where the next value starts. The quotes that delimit a value are YAML's and
    quote nothing. A ``title:`` value is the one place that word marks a title,
    on every line of the value.
    """
    reader = _Frontmatter(decode_escapes=False, blank_quotes=True)
    values: list[list[int]] = []
    shown = list(lines)
    for index in range(1, _frontmatter_end(lines)):
        if values and reader.continues(lines[index]):
            values[-1].append(index)
        else:
            values.append([index])
        shown[index] = reader.decode(lines[index])
    return [
        value[offset] + 1
        for value in values
        if not _TITLE_LINE.match(lines[value[0]])
        for offset in _lines_with_prose_dash("\n".join(shown[i] for i in value))
    ]


def markdown_hits(text: str, *, mdx: bool = False) -> list[int]:
    """The 1-based lines of a markdown or MDX page that carry a prose dash.

    A fenced block and a display-math block end the paragraph before them, as
    the site reads them, so each reaches the span reader as a blank line:
    nothing pairs across it, whatever its lines open with. An italic span and
    a quotation stop where a code span does, at the start of any block, and a
    line of a quotation is read through its marks. The frontmatter is plain
    text, read apart (:func:`_frontmatter_hits`): nothing a value of it opens
    reaches the body.

    :param mdx: Whether the page is MDX, whose blocks read apart from Markdown's.
    """
    kind = "mdx" if mdx else "md"
    lines = _decode_page(text).splitlines()
    head = _frontmatter_head(lines)
    written = lines[head:]
    code_flags = list(code_lines(written, kind=kind))
    math_flags = _math_lines(written, kind=kind)
    shown = lines_read_whole(written, lambda page: _drop_code_and_math(page, kind=kind))
    reading = _PageReading()
    hits = _frontmatter_hits(lines)
    for index, opens_block in enumerate(block_starts(written, kind=kind)):
        line = written[index]
        if opens_block:
            reading.open_block(line)
        if code_flags[index]:
            found = False
        elif math_flags[index]:
            found = EM_DASH in line
        else:
            found = line.strip() != "" and reading.holds_dash(line, shown[index])
        if found:
            hits.append(head + index + 1)
    return hits


def _holds_prose_dash(line: str, pairs: dict[str, str] = _QUOTE_PAIRS) -> bool:
    """Whether a dash of the line is neither in a quotation nor before a part number.

    Each exemption covers the dash it reads and nothing else on the line.

    :param pairs: The marks that quote on the line.
    """
    return EM_DASH in _PART_AFTER_DASH.sub("", _outside_closed_quotations(line, pairs))


def _text_holds_prose_dash(text: str) -> bool:
    """Whether the text of a string holds a dash that is prose.

    A dash in an inline literal is code; otherwise each line is read for
    itself, so that a title reproduced on one exempts no other line.
    """
    return any(
        _holds_prose_dash(line)
        for line in _mask_paragraphs(text.split("\n"), _blank_docstring_code_spans)
    )


def _string_is_prose(value: str) -> bool:
    """Whether a string literal with a dash holds one that is prose.

    A dash that fills the string is a placeholder; otherwise its text is read
    (:func:`_text_holds_prose_dash`).
    """
    return value.strip() != EM_DASH and _text_holds_prose_dash(value)


def _literal_hits(literal: str, first_line: int) -> list[int]:
    r"""The 1-based lines of one string literal whose value carries a prose dash.

    The value is what is published, so it is the value that is read: an
    escape or an entity of the em dash counts as the character, and a raw
    string's ``\u2014`` stays the six characters it is.

    :param literal: The literal as written.
    :param first_line: The line it opens on.
    """
    try:
        value = ast.literal_eval(literal)
    except (ValueError, SyntaxError):
        value = literal
    if not isinstance(value, str):
        return []
    value = _decode_entities(value)
    if EM_DASH not in value or not _string_is_prose(value):
        return []
    found = [
        first_line + offset
        for offset, line in enumerate(literal.splitlines())
        if _spells_em_dash(line)
        and _string_is_prose(_decode_spellings(line, _PYTHON_EM_DASH_ESCAPE))
    ]
    return found or [first_line]


#: The tokens of an f-string (Python 3.12 on): its opening, the text between
#: its fields, and its closing.
_FSTRING_START = getattr(tokenize, "FSTRING_START", -1)
_FSTRING_MIDDLE = getattr(tokenize, "FSTRING_MIDDLE", -1)
_FSTRING_END = getattr(tokenize, "FSTRING_END", -1)


@dataclass
class _OpenFString:
    """An f-string being read: its text so far, each field a mark in its place.

    A field is unknown text, so it leaves :data:`~markdown_spans.SPAN_MARK`, and
    the line breaks it holds, so that each line of the text is where it was.
    """

    #: Its string prefix without the ``f``, and the quote it opened with.
    prefix: str
    quote: str
    #: The line it opens on.
    first_line: int
    #: How many braces are open at this point, one for a field of its text.
    depth: int = 0
    text: str = ""

    @classmethod
    def opened_by(cls, token: tokenize.TokenInfo) -> _OpenFString:
        """The f-string that *token*, its opening, opens."""
        opening = token.string.rstrip("'\"")
        return cls(
            opening.lower().replace("f", ""),
            token.string[len(opening) :][0],
            token.start[0],
        )

    def read(self, token: tokenize.TokenInfo) -> None:
        """Take in a token that stands inside it, the fields' own strings apart."""
        if token.type == _FSTRING_MIDDLE:
            self.text += token.string
        elif token.exact_type == tokenize.LBRACE:
            self.text += SPAN_MARK if not self.depth else ""
            self.depth += 1
        elif token.exact_type == tokenize.RBRACE:
            self.depth -= 1
            on_line = self.first_line + self.text.count("\n")
            self.text += "\n" * (token.start[0] - on_line) if not self.depth else ""

    def literal(self) -> str:
        """The string literal it would be with no field: its value is the one read."""
        return f"{self.prefix}{self.quote * 3}{self.text}{self.quote * 3}"


def _string_literals(tokens: Iterable[tokenize.TokenInfo]) -> Iterator[tuple[str, int]]:
    """Every string literal of a module and the line it opens on, an f-string read whole."""
    open_fstrings: list[_OpenFString] = []
    for token in tokens:
        if token.type == tokenize.STRING:
            yield token.string, token.start[0]
        elif token.type == _FSTRING_START:
            open_fstrings.append(_OpenFString.opened_by(token))
        elif token.type == _FSTRING_END:
            closed = open_fstrings.pop()
            yield closed.literal(), closed.first_line
        elif open_fstrings:
            open_fstrings[-1].read(token)


def python_hits(text: str) -> list[int]:
    """The 1-based lines of a module whose docstrings, comments or strings carry a dash."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return [
            n
            for n, line in enumerate(text.splitlines(), 1)
            if EM_DASH in _decode_spellings(line, _PYTHON_EM_DASH_ESCAPE)
        ]
    hits = {
        token.start[0]
        for token in tokens
        if token.type == tokenize.COMMENT and EM_DASH in token.string
    }
    for literal, first_line in _string_literals(tokens):
        if _spells_em_dash(literal):
            hits.update(_literal_hits(literal, first_line))
    return sorted(hits)


def data_hits(text: str) -> list[int]:
    """The 1-based lines of a data module (glossary, home page) whose text has a dash.

    A comment is not published and keeps its dash; a standard's title is
    exempt as everywhere else, inside curly quotes or guillemets or before a
    part number, each exempting its own dash. The lines are read as written,
    so a straight quote is the string's and quotes nothing. A string is read
    with JavaScript's escapes, the language of the module
    (:data:`_JS_EM_DASH_ESCAPE`).
    """
    hits: list[int] = []
    for number, written in enumerate(text.splitlines(), start=1):
        line = _decode_spellings(written, _JS_EM_DASH_ESCAPE)
        if line.lstrip().startswith(("//", "*", "/*")):
            continue
        if _holds_prose_dash(line, _TYPOGRAPHIC_QUOTE_PAIRS):
            hits.append(number)
    return hits


#: A JSON string literal, escapes included.
_JSON_STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def json_hits(text: str) -> list[int]:
    """The 1-based lines of a JSON data file whose strings carry a dash.

    Every key and value of the file is a string, so each is read as a
    string literal of a module is: a dash alone is an empty cell, and a dash
    inside quotation marks reproduces what a source prints.
    """
    hits: list[int] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not _spells_em_dash(line):
            continue
        for literal in _JSON_STRING.findall(line):
            try:
                value = json.loads(literal)
            except json.JSONDecodeError:
                value = literal
            value = _decode_entities(value)
            if EM_DASH in value and _string_is_prose(value):
                hits.append(number)
                break
    return hits


def text_hits(text: str) -> list[int]:
    """The 1-based lines of a plain-text file the site serves whose text has a dash.

    The file reaches a reader as written, so every line is read, a comment
    among them: a crawler reads the ``#`` lines of robots.txt with the rules,
    and so does anyone who opens it. Nothing in it is decoded, so an entity
    or an escape is the characters it is, and nothing marks code or an empty
    cell there. A standard's title reproduced as printed keeps its dash, in a
    quotation or before a part number (:func:`_holds_prose_dash`).
    """
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if _holds_prose_dash(line)
    ]


def _mdx_hits(text: str) -> list[int]:
    """:func:`markdown_hits` on an MDX page."""
    return markdown_hits(text, mdx=True)


#: The suffixes the guard reads, each with the reader that knows its kind.
_READERS = {
    ".py": python_hits,
    ".md": markdown_hits,
    ".mdx": _mdx_hits,
    ".mjs": data_hits,
    ".ts": data_hits,
    ".json": json_hits,
    ".txt": text_hits,
}
#: The suffixes a root that is a directory is walked for: all of them but plain
#: text, which is read only where a root names the file. A ``.txt`` file under
#: the roots that are directories would be a data table or a baseline, not
#: prose, and the site's other plain-text files are no prose of their own: the
#: llms files are generated from the pages read here, and reproduce the
#: standards' titles, dashes and all, outside the markup that says they are
#: titles, and the IndexNow key file holds a key.
_WALKED = frozenset(_READERS) - {".txt"}


def scan(path: pathlib.Path) -> list[int]:
    """The offending lines of one file, by its kind."""
    reader = _READERS.get(path.suffix)
    if reader is None:
        return []
    return reader(path.read_text(encoding="utf-8"))


#: Two hyphens or more in a row, the run smartypants publishes as an em dash.
_DOUBLE_HYPHEN = re.compile(r"-{2,}")
#: Two hyphens, no more, with a space or the end of a line on either side: a
#: dash in a string that may also hold an option of a command line
#: (``--keep``), the separator of one (``"--"``, quotes and all) or the rule of
#: a console banner (``--- Generating ---``).
_SPACED_DOUBLE_HYPHEN = re.compile(r"(?<![^\s])--(?![^\s])")
#: A line that is only a rule, as written: a docstring's heading underline, a
#: table's separator row, a horizontal rule or a frontmatter fence. It holds
#: nothing but the characters a rule is drawn with, and a pipe or a run of
#: three of them, so a line that is only a dash (``--``) is not one.
_RULE_LINE = re.compile(r"^[\s\-=~^+*_#|:]*(?:\||([\-=~^+*_#])\1\1)[\s\-=~^+*_#|:]*$")
#: A run of hyphens that fills a whole table cell, or a whole slash-separated
#: item of one: the empty-cell mark, as the em dash is.
_HYPHEN_PLACEHOLDER = re.compile(r"(?:^|(?<=/))\s*-{2,}\s*(?=/|$)")
#: An HTML comment, which the page does not show.
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
#: An MDX comment, an expression that holds nothing but a comment: an MDX page
#: does not show it, and a markdown page shows it as written.
_MDX_COMMENT = re.compile(r"\{\s*/\*.*?\*/\s*\}", re.DOTALL)
#: A link destination, a reference definition's target and a URL, which are
#: addresses: a heading's anchor keeps the double hyphen its slug was given.
_ADDRESSES = (
    re.compile(r"\]\([^)\s]*(?:\s+\"[^\"]*\")?\)"),
    re.compile(r"^\s*\[[^\]]+\]:\s*\S+", re.MULTILINE),
    re.compile(r"<[a-z]+://[^>\s]*>"),
    re.compile(r"[a-z]+://[^\s)>\]]+"),
)
#: An attribute whose value is an address or a style, not text a reader sees.
_ADDRESS_ATTRIBUTE = re.compile(
    r"\b(?:href|src|style|id|class|className)=(?:\"[^\"]*\"|'[^']*'|\{[^}]*\})"
)
#: An inline literal, a role or an interpreted span of a docstring, across the
#: lines of a paragraph if it wraps: ``x``, :func:`x` or `x`.
_DOCSTRING_CODE_SPAN = re.compile(r"``(?:[^`]|`(?!`))+``|(?::[\w:+-]+:)?`[^`]+`")
#: A directive whose body is code or mathematics, not prose: the ones
#: ``scripts/generate_api_docs.py`` publishes as a fenced block or as ``$$``
#: math, so that a docstring and its page read the same.
_CODE_DIRECTIVE = re.compile(
    r"^\s*\.\.\s+(?:code-block|code|sourcecode|math|doctest|testcode|"
    r"parsed-literal)::"
)
#: Any other explicit markup line (``.. note::``): its body is prose.
_EXPLICIT_MARKUP = re.compile(r"^\s*\.\.\s")
#: The prompt that opens a doctest; its continuation and output lines follow
#: it up to the next blank line.
_DOCTEST_PROMPT = re.compile(r"^\s*>>>(?:\s|$)")


def _blank_out(match: re.Match[str]) -> str:
    """The matched text as blanks, its line ends kept so that lines still count."""
    return re.sub(r"[^\n]", " ", match.group())


def _blank_page_spans(text: str, *, walked: list[PageLine]) -> str:
    """The text of a page with every code span and every maths span blanked.

    Read as the site reads them (:mod:`markdown_spans`): left to right and a
    block of the page at a time, the first run of backticks or dollar signs
    that a run of the same length closes is the span, a backslash before an
    opening run shows its first character as written, and one inside a span
    escapes nothing. remark-math reads ``$...$`` as CommonMark reads a code
    span. A span never runs from one list item, heading, table row or
    quotation into the next, so the dollar sign of one item does not pair
    with the one of the next and hide the prose between them.

    :param walked: The walk of the page as written, of which *text* has lines
        blanked.
    """
    return blank_inline_spans_by_block(text, "`$", walked=walked)


def _blank_docstring_code_spans(text: str) -> str:
    """The text of a docstring with every inline literal, role and interpreted span blanked."""
    return _DOCSTRING_CODE_SPAN.sub(_blank_out, text)


def _mask_paragraphs(lines: list[str], blank: Callable[[str], str]) -> list[str]:
    """The lines with every code span blanked, a span that wraps included.

    A span wraps with the block that carries it, so the lines are joined a
    block at a time before the spans are blanked: a blank line and a line
    already blanked out (code) close one, and a list item opens one whatever
    its indentation, since a docstring keeps the indentation of its source.
    """
    masked = list(lines)
    starts = block_starts([line.lstrip() for line in lines])
    opening = [index for index, opens in enumerate(starts) if opens]
    for start, stop in zip(opening, [*opening[1:], len(lines)], strict=True):
        masked[start:stop] = blank("\n".join(lines[start:stop])).split("\n")
    return masked


def _double_hyphen_lines(written: list[str], masked: list[str]) -> list[int]:
    """The 0-based indexes of the lines that keep a double hyphen in prose.

    :param written: The lines as written, which say whether a line is a rule:
        once its code is blanked, a bullet that names a function reads as one.
    :param masked: The same lines with everything that is not prose blanked.
    """
    hits: list[int] = []
    for index, (source, line) in enumerate(zip(written, masked, strict=True)):
        if _RULE_LINE.match(source):
            continue
        if _TABLE_ROW.match(line):
            line = "|".join(
                _HYPHEN_PLACEHOLDER.sub("", cell) for cell in line.split("|")
            )
        if _DOUBLE_HYPHEN.search(line):
            hits.append(index)
    return hits


def _math_lines(lines: list[str], *, kind: str) -> list[bool]:
    """Whether each line of a page is in a display-math block, its fences included.

    The block is read as the site reads it (:func:`display_math_parts`): behind
    the marks of a quotation or a list item as anywhere else, and wherever it
    stands, so the backtick on the other side of its fence closes nothing.

    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    """
    return [part != "prose" for part in display_math_parts(lines, kind=kind)]


def _page_code_lines(lines: list[str], *, kind: str) -> list[bool]:
    """Whether each line of a page is code or display math, not prose.

    The frontmatter holds neither: a value is plain text, and what it opens
    stops there.

    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    """
    head = _frontmatter_head(lines)
    code = code_lines(lines[head:], kind=kind)
    maths = _math_lines(lines[head:], kind=kind)
    return [False] * head + [a or b for a, b in zip(code, maths, strict=True)]


def _page_without_code_or_comments(written: list[str], *, mdx: bool) -> list[str]:
    """The lines of a page with its code, its display math and its comments blanked.

    The comments are the ones the page does not show: an HTML comment and an
    MDX comment of the body, the second on an MDX page only, and a comment of
    the frontmatter, whose values open neither. Every line keeps its place, so
    that a line still counts as the one written.

    :param mdx: Whether the page is MDX, the one kind that hides an MDX comment.
    """
    kind = "mdx" if mdx else "md"
    lines = [
        "" if code else line
        for line, code in zip(
            written, _page_code_lines(written, kind=kind), strict=True
        )
    ]
    _read_frontmatter(lines, _Frontmatter(decode_escapes=False, blank_comments=True))

    def without_comments(text: str) -> str:
        text = _HTML_COMMENT.sub(_blank_out, text)
        return _MDX_COMMENT.sub(_blank_out, text) if mdx else text

    head = _frontmatter_head(lines)
    return lines[:head] + lines_read_whole(lines[head:], without_comments)


def _without_addresses(text: str) -> str:
    """The text with its link destinations, URLs and address or style attributes blanked."""
    for address in _ADDRESSES:
        text = address.sub(_blank_out, text)
    return _ADDRESS_ATTRIBUTE.sub(_blank_out, text)


def markdown_double_hyphen_hits(text: str, *, mdx: bool = False) -> list[int]:
    """The 1-based lines of a page whose prose spells a dash as ``--``.

    Smartypants converts any run of two hyphens in the text of a page, spaced
    or not, so any such run is looked for, once the code, the math, the
    addresses, the comments, the address and style attributes and the rules
    are out. The frontmatter is read apart from the body, as plain text with
    no span in it, so nothing a value of it opens reaches the body.

    :param mdx: Whether the page is MDX, whose MDX comments are not shown.
    """
    written = text.split("\n")
    lines = _page_without_code_or_comments(written, mdx=mdx)
    head = _frontmatter_head(written)
    walked = list(page_lines(written[head:], kind="mdx" if mdx else "md"))
    masked = lines_read_whole(lines[:head], _without_addresses) + lines_read_whole(
        lines[head:],
        lambda body: _blank_page_spans(_without_addresses(body), walked=walked),
    )
    return [
        index + 1
        for index in _double_hyphen_lines(
            [inside_quotation(line) for line in written],
            [inside_quotation(line) for line in masked],
        )
    ]


def _opens_code_block(line: str) -> bool:
    """Whether the lines indented under this one are code.

    A code or math directive opens one, and so does a paragraph that ends in
    ``::``; any other directive (``.. note::``) opens a body of prose.
    """
    if _CODE_DIRECTIVE.match(line):
        return True
    return line.rstrip().endswith("::") and not _EXPLICIT_MARKUP.match(line)


def _docstring_prose(lines: list[str]) -> list[str]:
    """The lines of a docstring with every line that is code blanked.

    A literal block runs from the line after a paragraph that ends in ``::``,
    and a code or math directive's body from the line after the directive, to
    the first line indented no deeper than the line that opened it; a doctest
    runs from its prompt to the next blank line. A note's body is prose.
    """
    prose: list[str] = []
    block_indent: int | None = None
    doctest = False
    for line in lines:
        indent = len(line) - len(line.lstrip())
        in_block = block_indent is not None and (
            not line.strip() or indent > block_indent
        )
        doctest = (doctest and bool(line.strip())) or bool(_DOCTEST_PROMPT.match(line))
        code = in_block or doctest or bool(_CODE_DIRECTIVE.match(line))
        prose.append("" if code else line)
        if not in_block:
            block_indent = indent if _opens_code_block(line) else None
    return prose


def _docstring_ranges(tree: ast.AST) -> list[tuple[int, int, int, int]]:
    """Where each docstring sits: first line, first column, last line, last column.

    A docstring is any string that stands as a statement of its own: the one
    that opens a module, a class or a function, and the one under an
    assignment that documents the name.
    """
    return [
        (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        and node.end_lineno is not None
        and node.end_col_offset is not None
    ]


def python_double_hyphen_hits(text: str, *, docstrings: bool = True) -> list[int]:
    """The 1-based lines of a module whose docstrings or strings spell a dash as ``--``.

    A docstring of the package is published by the API reference, through
    smartypants, and is read as a page is: any run of two hyphens in its
    prose. Any other string is read for the spaced form only, which is a dash
    wherever it stands; a comment is not published and is not read.

    :param docstrings: Whether the module's docstrings are published. Those
        of the figure and diagram generators are not: what those modules
        publish is the text they draw, which their other strings hold.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [
            number
            for number, line in enumerate(text.splitlines(), start=1)
            if _SPACED_DOUBLE_HYPHEN.search(line)
        ]
    ranges = _docstring_ranges(tree)
    hits = _string_hits(
        text, {n for first, _, last, _ in ranges for n in range(first, last + 1)}
    )
    if docstrings:
        source = text.splitlines()
        for first, first_col, last, last_col in ranges:
            hits.update(_docstring_hits(source, first, first_col, last, last_col))
    return sorted(hits)


def _docstring_hits(
    source: list[str], first: int, first_col: int, last: int, last_col: int
) -> list[int]:
    """The 1-based lines of one docstring whose prose holds a double hyphen."""
    lines = _docstring_lines(source, first, first_col, last, last_col)
    masked = _mask_paragraphs(_docstring_prose(lines), _blank_docstring_code_spans)
    return [first + index for index in _double_hyphen_lines(lines, masked)]


def _docstring_lines(
    source: list[str], first: int, first_col: int, last: int, last_col: int
) -> list[str]:
    """The lines of one docstring, what stands before and after it blanked."""
    lines = source[first - 1 : last]
    lines[-1] = lines[-1][:last_col]
    lines[0] = " " * first_col + lines[0][first_col:]
    return lines


def _string_hits(text: str, docstring_lines: set[int]) -> set[int]:
    """The 1-based lines of the strings that are not docstrings holding `` -- ``."""
    hits: set[int] = set()
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    for literal, first_line in _string_literals(tokens):
        if first_line in docstring_lines:
            continue
        masked = _blank_docstring_code_spans(literal)
        hits.update(
            first_line + offset
            for offset, line in enumerate(masked.split("\n"))
            if _SPACED_DOUBLE_HYPHEN.search(line)
        )
    return hits


def data_double_hyphen_hits(text: str) -> list[int]:
    """The 1-based lines of a data module whose text spells a dash as `` -- ``.

    A comment is not published, as for the em dash; the spaced form is the one
    looked for, since a module's code may hold a decrement or a custom
    property (``var(--sl-color-accent)``).
    """
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if not line.lstrip().startswith(("//", "*", "/*"))
        and _SPACED_DOUBLE_HYPHEN.search(line)
    ]


def json_double_hyphen_hits(text: str) -> list[int]:
    """The 1-based lines of a JSON data file whose strings spell a dash as `` -- ``."""
    hits: list[int] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for literal in _JSON_STRING.findall(line):
            if _SPACED_DOUBLE_HYPHEN.search(literal):
                hits.append(number)
                break
    return hits


#: The marker of a list item, bulleted or numbered, and the space after it.
_LIST_MARKER = re.compile(r"\s*(?:[*+-]|\d+[.)]|#\.)\s+")
#: An inline literal of a docstring, or a code span of two backticks on a page.
_DOUBLE_TICK_HEAD = re.compile(r"``(?:[^`\n]|`(?!`))+``")
#: A bold span, in a docstring or on a page.
_BOLD_HEAD = re.compile(r"\*\*[^*\n]+\*\*")
#: The heads a docstring's list item opens with: an inline literal, a role or
#: an interpreted span, or a bold span.
_DOCSTRING_HEADS = (
    _DOUBLE_TICK_HEAD,
    re.compile(r"(?::[\w:+-]+:)?`[^`\n]+`"),
    _BOLD_HEAD,
)
#: The heads a page's list item opens with: a code span, a bold span or a link.
_PAGE_HEADS = (
    _DOUBLE_TICK_HEAD,
    re.compile(r"`[^`\n]+`"),
    _BOLD_HEAD,
    re.compile(r"__[^_\n]+__"),
    re.compile(r"\[[^\]\n]+\](?:\([^)\n]*\))?"),
)
#: What joins two heads of one item: a slash, a comma, "and" or "or".
_HEAD_JOINER = re.compile(r"\s*(?:/|,|and\b|or\b)\s*")
#: A parenthesis after the heads, which still belongs to them.
_HEAD_ASIDE = re.compile(r"\s+\([^()\n]*\)")
#: A single hyphen between spaces, or at the end of the line.
_SPACED_HYPHEN = re.compile(r"\s+-(?=\s|$)")


def _head_end(line: str, start: int, heads: tuple[re.Pattern[str], ...]) -> int | None:
    """Where the head that opens at ``start`` ends, or None when none opens there."""
    for head in heads:
        found = head.match(line, start)
        if found is not None:
            return found.end()
    return None


def _joins_head_with_hyphen(line: str, heads: tuple[re.Pattern[str], ...]) -> bool:
    """Whether a list item joins its head to its text with a spaced hyphen.

    The heads are matched whole from the marker on, so the hyphen is looked
    for right after the last of them: a minus inside a role
    (``:math:`445.2 F - 344.3```) is part of the head and never read.
    """
    marker = _LIST_MARKER.match(line)
    if marker is None:
        return False
    at = _head_end(line, marker.end(), heads)
    if at is None:
        return False
    while joiner := _HEAD_JOINER.match(line, at):
        more = _head_end(line, joiner.end(), heads)
        if more is None:
            break
        at = more
    aside = _HEAD_ASIDE.match(line, at)
    if aside is not None:
        at = aside.end()
    return _SPACED_HYPHEN.match(line, at) is not None


def markdown_bullet_hyphen_hits(text: str, *, mdx: bool = False) -> list[int]:
    """The 1-based lines of a page whose list item joins its head to its text with ``-``.

    A list item in code or in a comment the page does not show is not read,
    and an entry of the frontmatter is no list item: the site shows it as text.

    :param mdx: Whether the page is MDX, whose MDX comments are not shown.
    """
    written = text.split("\n")
    prose = _page_without_code_or_comments(written, mdx=mdx)
    head = _frontmatter_head(written)
    return [
        number
        for number, line in enumerate(prose[head:], start=head + 1)
        if _joins_head_with_hyphen(inside_quotation(line), _PAGE_HEADS)
    ]


def python_bullet_hyphen_hits(text: str) -> list[int]:
    """The 1-based lines of a module's docstrings whose list item joins its head with ``-``.

    The docstring is read as :func:`python_double_hyphen_hits` reads it, with
    its literal blocks, code and math directives and doctests left out.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    source = text.splitlines()
    hits: list[int] = []
    for first, first_col, last, last_col in _docstring_ranges(tree):
        lines = _docstring_lines(source, first, first_col, last, last_col)
        hits.extend(
            first + index
            for index, line in enumerate(_docstring_prose(lines))
            if _joins_head_with_hyphen(line, _DOCSTRING_HEADS)
        )
    return sorted(hits)


#: The package, whose docstrings the API reference is generated from.
_PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "src" / "phonometry"

#: The suffixes the double-hyphen reading covers, each with its reader. A
#: module and a page are read by :func:`scan_double_hyphens`, which knows
#: where a module sits and which kind a page is.
_DOUBLE_HYPHEN_READERS = {
    ".mjs": data_double_hyphen_hits,
    ".ts": data_double_hyphen_hits,
    ".json": json_double_hyphen_hits,
}


def scan_double_hyphens(path: pathlib.Path) -> list[int]:
    """The lines of one file whose prose spells a dash as a double hyphen."""
    text = path.read_text(encoding="utf-8") if path.suffix in _READERS else ""
    if path.suffix == ".py":
        published = path.resolve().is_relative_to(_PACKAGE)
        return python_double_hyphen_hits(text, docstrings=published)
    if path.suffix in (".md", ".mdx"):
        return markdown_double_hyphen_hits(text, mdx=path.suffix == ".mdx")
    reader = _DOUBLE_HYPHEN_READERS.get(path.suffix)
    return reader(text) if reader is not None else []


def scan_bullet_hyphens(path: pathlib.Path) -> list[int]:
    """The lines of one file whose list item joins its head to its text with ``-``.

    Read in the pages and in the package's docstrings, which are published;
    a generator's docstring is not.
    """
    if path.suffix in (".md", ".mdx"):
        text = path.read_text(encoding="utf-8")
        return markdown_bullet_hyphen_hits(text, mdx=path.suffix == ".mdx")
    if path.suffix == ".py" and path.resolve().is_relative_to(_PACKAGE):
        return python_bullet_hyphen_hits(path.read_text(encoding="utf-8"))
    return []


def findings(path: pathlib.Path) -> list[tuple[int, str]]:
    """Every dash of one file's published prose, by line, with what it is."""
    found = [(number, "em dash") for number in scan(path)]
    found += [
        (number, "double hyphen, published as an em dash")
        for number in scan_double_hyphens(path)
    ]
    found += [
        (number, "spaced hyphen as a dash after a list item's head")
        for number in scan_bullet_hyphens(path)
    ]
    return sorted(found)


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
                if p.suffix in _WALKED
                and not any(str(p).startswith(u) for u in _UNPUBLISHED)
            )
    return files


#: What a clean run says: every form the guard refuses, so a green run does
#: not read as narrower than the check it ran.
GREEN = (
    "No em dash, no double hyphen and no spaced hyphen after a list item's head "
    "in the published prose."
)


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
        found = findings(path)
        if not found:
            continue
        files += 1
        total += len(found)
        if args.count:
            print(f"{path}: {len(found)}")
            continue
        for number, what in found:
            print(f"{path}:{number}: {what} in published prose")
    if total:
        print(
            f"{total} dash(es) in the published prose of {files} file(s); "
            "rewrite each as a sentence, a parenthesis, a colon or a comma.",
            file=sys.stderr,
        )
        return 1
    print(GREEN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
