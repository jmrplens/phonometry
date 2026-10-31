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
  a sentence. The glossary cards, the home page's text and the Spanish
  catalogue notes are prose in the site's data modules and are read as such.
- **Two bare dashes** in a table row separator or a horizontal rule are
  hyphens, not em dashes.

The character has other spellings that publish it all the same, and each is
read as the character where it is decoded on its way to a reader: the HTML
entities ``&mdash;``, ``&#8212;`` and ``&#x2014;`` in a page and in a string,
the escapes ``\u2014``, ``\U00002014`` and ``\N{EM DASH}`` in a string of a
module (whose value is what is read, so a raw string keeps its backslash),
``\u2014`` in a JSON string, ``\u2014`` and ``\u{2014}`` in a data module,
and ``\u2014`` and ``\U00002014`` in a double-quoted value of a page's
frontmatter, the one YAML value that decodes an escape, and in the JSON
strings of the JSON-LD its head carries. A single-quoted or plain value, a
block of text and a comment of the frontmatter show the escape as written,
and so does the body of a page. A backslash escapes the character after it
in each of these languages, so ``\\u2014`` is never the dash.

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
  smartypants), a link destination, a URL, an HTML comment, the value of an
  ``href``, ``src``,
  ``style``, ``id`` or ``class`` attribute (``var(--sl-color-accent)``), and a
  line that is only a rule: a docstring's heading underline, a table's
  separator row, a horizontal rule, a frontmatter fence. A run that fills a
  whole table cell, or a whole slash-separated item of one, is the empty-cell
  mark, as the em dash is. A docstring and the page generated from it read
  the same: ``scripts/generate_api_docs.py`` fences a code directive's body
  and a doctest as code, and turns the math into ``$`` and ``$$`` spans.
- **Any other string of a module, and the site's data modules**, are refused
  a double hyphen that stands between spaces (`` -- ``), the one form that is
  a dash there and not an option of a command line (``--keep``) or a
  decrement.
- **A comment** is published nowhere, neither on the site nor by ``help()``,
  and keeps its double hyphens, the section rules (``# -- names ---``) among
  them. So does the docstring of a figure or diagram generator, which
  publishes only what it draws.

One more spelling of the dash is read in one place only: a single hyphen
between spaces that joins a list item's head to its text, as in
``* :func:`npd_level` - the interpolated event level``, in a page or a
package docstring. The head is an inline literal, a role, an interpreted
span, a bold span or a link, alone or several joined by a slash, a comma,
"and" or "or", with one parenthesis after them at most; the hyphen has to
follow it, so a minus inside a role (``:math:`445.2 F - 344.3```) is never
read. Elsewhere a spaced hyphen is also a minus (``32,3 - 26,3 dB``), and the
rule holds there by review.

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

from markdown_fences import code_lines

if TYPE_CHECKING:
    from collections.abc import Callable

EM_DASH = "—"

#: Where the published prose lives: the pages and their mirrors, the data
#: modules the site's pages are built from (the glossary cards, the home page's
#: text and examples, the Spanish catalogue notes), the package docstrings the
#: API reference is generated from, and the text the figure and diagram
#: generators draw. Tests are not published and keep their dashes, and the
#: llms mirrors and the generated API pages are regenerated from what is listed
#: here and need no scan of their own.
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
)

#: Bold markers, which are not italics and are taken out before counting.
_BOLD = re.compile(r"\*\*")
#: A list bullet written with an asterisk, which is not an italic marker
#: either: left in, it opens a span that swallows the rest of the item.
_BULLET = re.compile(r"^\s*\*(?=\s)")
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
#: The HTML entities of the em dash, which a page and a string set as HTML
#: publish as the character.
_EM_DASH_ENTITY = re.compile(r"&(?:mdash|#0*8212|#[xX]0*2014);")
#: The escapes of a string literal that stand for the em dash: ``\u2014``,
#: Python's ``\U00002014`` and ``\N{EM DASH}`` (a name Python reads in any
#: case), and JavaScript's ``\u{2014}``. The letter of an escape is read as
#: written: ``\U2014`` is no escape of either language, and ``\u00002014`` is
#: the NUL character and four digits.
_EM_DASH_ESCAPE = re.compile(r"\\(?:u2014|U00002014|N\{(?i:em dash)\}|u\{0*2014\})")
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


def _decode_escapes(text: str, escape: re.Pattern[str] = _EM_DASH_ESCAPE) -> str:
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


def _decode_spellings(text: str) -> str:
    """The text with each entity and each escape of the em dash read as the character."""
    return _decode_escapes(_decode_entities(text))


def _decode_json_strings(line: str) -> str:
    """The line with the escape of the em dash read as the character in its JSON strings."""
    return _JSON_STRING.sub(
        lambda found: _decode_escapes(found.group(), _JSON_EM_DASH_ESCAPE), line
    )


#: The rest of a double-quoted YAML value, up to its closing quote, and of a
#: single-quoted one, whose only escape is a doubled quote.
_YAML_QUOTED_REST = {
    '"': re.compile(r'(?:[^"\\]|\\.)*"'),
    "'": re.compile(r"(?:[^']|'')*'"),
}


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
    """

    #: The quote of a value still open at the end of the last line.
    quote: str = ""
    #: The column a line of an open block of text is indented past.
    block: int | None = None
    #: Whether that block is the JSON-LD of a ``content`` key.
    json_block: bool = False
    #: The column a line that wraps an open plain value is indented past.
    plain: int | None = None
    #: How deep the line is inside a flow collection (``[...]``, ``{...}``).
    flow: int = 0

    def decode(self, line: str) -> str:
        """The line with each escape of the em dash read where YAML decodes it."""
        indent = len(line) - len(line.lstrip(" "))
        if self.block is not None:
            if not line.strip() or indent > self.block:
                return _decode_json_strings(line) if self.json_block else line
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

    def _quoted(self, line: str, start: int, quote: str, pieces: list[str]) -> int:
        """Read a quoted value from ``start``, past its opening quote; return where it ends."""
        found = _YAML_QUOTED_REST[quote].match(line, start)
        end = found.end() if found is not None else len(line)
        self.quote = "" if found is not None else quote
        value = line[start:end]
        pieces.append(
            _decode_escapes(value, _YAML_EM_DASH_ESCAPE) if quote == '"' else value
        )
        return end

    def _nodes(self, line: str, at: int, indent: int, pieces: list[str]) -> None:
        """Read the line from ``at`` on, node by node, into ``pieces``."""
        node = _Node(owner=indent)
        while at < len(line) and not node.done:
            found = self._indicator(line, at, node, pieces)
            at = found if found is not None else self._plain(line, at, node, pieces)

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
            pieces.append(line[at:])
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
            pieces.append(char)
            end = self._quoted(line, at + 1, char, pieces)
            node.open, node.done = False, bool(self.quote)
            return end
        if char in "-?" and line[at + 1 : at + 2] in ("", " ", "\t"):
            pieces.append(char)
            node.owner = at
            return at + 1
        if char in "|>" and not self.flow:
            self.block, self.json_block = node.owner, node.key == "content"
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
    if lines and lines[0].strip() == "---":
        reader = _Frontmatter()
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                break
            lines[index] = reader.decode(lines[index])
    return "\n".join(lines)


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
    if _TITLE_LINE.match(line):
        return "", italic_open, quote_closer
    line = _CODE_SPAN.sub("", line)
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
    if _PART_AFTER_DASH.search(line):
        return "", italic_open, quote_closer
    return line, italic_open, quote_closer


def markdown_hits(text: str) -> list[int]:
    """The 1-based lines of a markdown or MDX page that carry a prose dash."""
    hits: list[int] = []
    italic_open = False
    quote_closer: str | None = None
    in_reference = False
    caption = False
    opening = True
    lines = _decode_page(text).splitlines()
    for number, (line, code) in enumerate(
        zip(lines, code_lines(lines), strict=True), start=1
    ):
        if code:
            continue
        stripped = line.lstrip()
        if not stripped:
            italic_open = False
            quote_closer = None
            in_reference = False
            caption = False
            opening = True
            continue
        if _REFERENCE_ENTRY.match(line):
            in_reference = True
        elif not line.startswith((" ", "\t")):
            in_reference = False
        if opening:
            caption, opening = _is_caption(line), False
        prose, italic_open, quote_closer = _strip_exempt_markdown(
            line, italic_open=italic_open, quote_closer=quote_closer, caption=caption
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


def _string_token_hits(token: tokenize.TokenInfo) -> list[int]:
    r"""The 1-based lines of one string literal whose value carries a prose dash.

    The value is what is published, so it is the value that is read: an
    escape or an entity of the em dash counts as the character, and a raw
    string's ``\u2014`` stays the six characters it is.
    """
    try:
        value = ast.literal_eval(token.string)
    except (ValueError, SyntaxError):
        value = token.string
    if not isinstance(value, str):
        return []
    value = _decode_entities(value)
    if EM_DASH not in value or not _string_is_prose(value):
        return []
    lines = token.string.splitlines()
    found = [
        token.start[0] + offset
        for offset, line in enumerate(lines)
        if _spells_em_dash(line)
    ]
    return found or [token.start[0]]


#: The tokens of an f-string (Python 3.12 on): its opening, the text between
#: its fields, and its closing.
_FSTRING_START = getattr(tokenize, "FSTRING_START", -1)
_FSTRING_MIDDLE = getattr(tokenize, "FSTRING_MIDDLE", -1)
_FSTRING_END = getattr(tokenize, "FSTRING_END", -1)


def _track_fstrings(token: tokenize.TokenInfo, raw_fstrings: list[bool]) -> None:
    """Keep, innermost last, whether each f-string open at ``token`` is raw."""
    if token.type == _FSTRING_START:
        raw_fstrings.append("r" in token.string.lower())
    elif token.type == _FSTRING_END:
        raw_fstrings.pop()


def _token_hits(token: tokenize.TokenInfo, *, raw: bool) -> list[int]:
    """The 1-based lines of one comment or string token that carry a prose dash.

    :param raw: Whether the f-string the token belongs to is raw, so that its
        backslashes are the characters they are.
    """
    if token.type == tokenize.COMMENT:
        return [token.start[0]] if EM_DASH in token.string else []
    if token.type == tokenize.STRING:
        return _string_token_hits(token)
    if token.type == _FSTRING_MIDDLE:
        middle = _decode_entities(token.string)
        if not raw:
            middle = _decode_escapes(middle)
        return [token.start[0]] if EM_DASH in middle else []
    return []


def python_hits(text: str) -> list[int]:
    """The 1-based lines of a module whose docstrings, comments or strings carry a dash."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return [
            n
            for n, line in enumerate(text.splitlines(), 1)
            if EM_DASH in _decode_spellings(line)
        ]
    hits: set[int] = set()
    raw_fstrings: list[bool] = []
    for token in tokens:
        _track_fstrings(token, raw_fstrings)
        if _spells_em_dash(token.string):
            raw = bool(raw_fstrings) and raw_fstrings[-1]
            hits.update(_token_hits(token, raw=raw))
    return sorted(hits)


def data_hits(text: str) -> list[int]:
    """The 1-based lines of a data module (glossary, home page) whose text has a dash.

    A comment is not published and keeps its dash; a standard's title is
    exempt as everywhere else.
    """
    hits: list[int] = []
    for number, written in enumerate(text.splitlines(), start=1):
        line = _decode_spellings(written)
        if EM_DASH not in line or line.lstrip().startswith(("//", "*", "/*")):
            continue
        if _PART_AFTER_DASH.search(line):
            continue
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


#: The suffixes the guard reads, each with the reader that knows its kind.
_READERS = {
    ".py": python_hits,
    ".md": markdown_hits,
    ".mdx": markdown_hits,
    ".mjs": data_hits,
    ".ts": data_hits,
    ".json": json_hits,
}


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
#: A run of backticks, which opens or closes a code span of a page.
_BACKTICK_RUN = re.compile(r"`+")
#: A run of dollar signs no backslash escapes, which opens or closes a math
#: span of a page: remark-math reads ``$...$`` as CommonMark reads a code span.
_DOLLAR_RUN = re.compile(r"(?<!\\)\$+")
#: The line that opens a display-math block of a page, and the one that
#: closes it: two dollar signs or more, and no other dollar sign after them.
_MATH_FENCE = re.compile(r"^\s*\${2,}[^$]*$")
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


def _blank_code_spans(text: str) -> str:
    """The text of a page with every code span blanked (CommonMark 6.1)."""
    return _blank_runs(text, _BACKTICK_RUN)


def _blank_page_spans(text: str) -> str:
    """The text of a page with every code span, then every math span, blanked.

    The code goes first: a dollar sign in a code span is the character, and
    opens no math.
    """
    return _blank_runs(_blank_code_spans(text), _DOLLAR_RUN)


def _blank_runs(text: str, run: re.Pattern[str]) -> str:
    """The text with every span between two matching runs blanked.

    A span opens on a run (of backticks, or of dollar signs) and closes on
    the next run of the same length; a run that no later run matches opens
    nothing. Read run by run rather than with one pattern, because a pattern
    that has to find the matching run backtracks over everything between.
    """
    runs = list(run.finditer(text))
    pieces: list[str] = []
    done = 0
    index = 0
    while index < len(runs):
        opening = runs[index]
        width = len(opening.group())
        closing = next(
            (k for k in range(index + 1, len(runs)) if len(runs[k].group()) == width),
            None,
        )
        if closing is None:
            index += 1
            continue
        end = runs[closing].end()
        pieces.append(text[done : opening.start()])
        pieces.append(re.sub(r"[^\n]", " ", text[opening.start() : end]))
        done = end
        index = closing + 1
    pieces.append(text[done:])
    return "".join(pieces)


def _blank_docstring_code_spans(text: str) -> str:
    """The text of a docstring with every inline literal, role and interpreted span blanked."""
    return _DOCSTRING_CODE_SPAN.sub(_blank_out, text)


def _mask_paragraphs(lines: list[str], blank: Callable[[str], str]) -> list[str]:
    """The lines with every code span blanked, a span that wraps included.

    A span wraps with the paragraph that carries it, so the lines are joined a
    paragraph at a time, blank line to blank line, before the spans are
    blanked; a line already blanked out (code) closes a paragraph too.
    """
    masked = list(lines)
    start = 0
    for index in range(len(lines) + 1):
        if index < len(lines) and lines[index].strip():
            continue
        if index > start:
            joined = blank("\n".join(lines[start:index]))
            masked[start:index] = joined.split("\n")
        start = index + 1
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


def _math_lines(lines: list[str], code: list[bool]) -> list[bool]:
    """Whether each line of a page is in a display-math block, its fences included.

    A line that is code is never a fence, and a block never closed runs to
    the end of the page, as a fenced code block does.
    """
    math: list[bool] = []
    inside = False
    for line, is_code in zip(lines, code, strict=True):
        fence = not is_code and bool(_MATH_FENCE.match(line))
        math.append(inside or fence)
        if fence:
            inside = not inside
    return math


def _page_code_lines(lines: list[str]) -> list[bool]:
    """Whether each line of a page is code or display math, not prose."""
    code = list(code_lines(lines))
    return [a or b for a, b in zip(code, _math_lines(lines, code), strict=True)]


def markdown_double_hyphen_hits(text: str) -> list[int]:
    """The 1-based lines of a page whose prose spells a dash as ``--``.

    Smartypants converts any run of two hyphens in the text of a page, spaced
    or not, so any such run is looked for, once the code, the math, the
    addresses, the HTML comments, the address and style attributes and the
    rules are out.
    """
    written = text.split("\n")
    text = "\n".join(
        "" if code else line
        for line, code in zip(written, _page_code_lines(written), strict=True)
    )
    text = _HTML_COMMENT.sub(_blank_out, text)
    for address in _ADDRESSES:
        text = address.sub(_blank_out, text)
    text = _ADDRESS_ATTRIBUTE.sub(_blank_out, text)
    masked = _mask_paragraphs(text.split("\n"), _blank_page_spans)
    return [index + 1 for index in _double_hyphen_lines(written, masked)]


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
    kinds = (tokenize.STRING, _FSTRING_MIDDLE)
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type not in kinds or token.start[0] in docstring_lines:
            continue
        masked = _blank_docstring_code_spans(token.string)
        hits.update(
            token.start[0] + offset
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


def markdown_bullet_hyphen_hits(text: str) -> list[int]:
    """The 1-based lines of a page whose list item joins its head to its text with ``-``."""
    lines = text.split("\n")
    return [
        number
        for number, (line, code) in enumerate(
            zip(lines, _page_code_lines(lines), strict=True), start=1
        )
        if not code and _joins_head_with_hyphen(line, _PAGE_HEADS)
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
#: module is read by :func:`scan_double_hyphens`, which knows where it sits.
_DOUBLE_HYPHEN_READERS = {
    ".md": markdown_double_hyphen_hits,
    ".mdx": markdown_double_hyphen_hits,
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
    reader = _DOUBLE_HYPHEN_READERS.get(path.suffix)
    return reader(text) if reader is not None else []


def scan_bullet_hyphens(path: pathlib.Path) -> list[int]:
    """The lines of one file whose list item joins its head to its text with ``-``.

    Read in the pages and in the package's docstrings, which are published;
    a generator's docstring is not.
    """
    if path.suffix in (".md", ".mdx"):
        return markdown_bullet_hyphen_hits(path.read_text(encoding="utf-8"))
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
                if p.suffix in _READERS
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
    print("No em dash and no double hyphen in the published prose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
