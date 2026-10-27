#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Gate for markdown that does not render the way it reads.

The guides are hard-wrapped, so a sentence long enough to wrap can put a
``-``, a ``>`` or a digit-and-dot at the start of a line. CommonMark does not
read that as the middle of a sentence: it reads it as a list item, a block
quote or an ordered list, and it ends the paragraph there. The author sees a
paragraph; the reader gets two blocks, or worse.

Six checks. The first two are the same defect seen twice, and they are not
equally visible; the other four are different ones with the same shape, a
source that looks right and renders wrong.

1. **Unclosed inline maths.** An inline ``$...$`` that wraps onto a block
   marker never closes: the marker ends the paragraph first. The maths is then
   published as literal text, and in MDX the subscript braces become a
   JavaScript expression, so the page does not render at all. This is what
   ``$L_{n,ij,w} = ... - \Delta R_{j,w}`` followed by ``- K_{ij} ...`` did:
   the site build failed with ``ReferenceError: n is not defined``, ``n`` being
   the first subscript. A list marker is only reported when it interrupts an
   open ``$``, because a list that legitimately follows its introducing line
   without a blank line is ordinary in this corpus (3830 of them) and is not a
   defect.

2. **A wrapped comparison operator.** ``>`` at the start of a line, where the
   line before it is ordinary paragraph text, is a greater-than sign that
   wrapped, not a quotation: it turned the tail of a sentence into a quoted
   block. This one is silent. Nothing renders wrong, nothing fails to build,
   and it ships. Three were found this way, two of them the same sentence in
   two languages. A deliberate block quote in this corpus is preceded by a
   blank line, which is why the rule can be this simple.

3. **A link to an accented heading.** Markdown percent-encodes non-ASCII in a
   URL, so ``[La medición](#la-medición-...)`` ships as
   ``href="#la-medici%C3%B3n-..."`` while the heading keeps its id unencoded.
   A browser resolves it; the accessibility audit compares the raw attribute
   against the ids and reports a dangling anchor, and it only samples 66 URLs,
   so five of the six the corpus had went unreported. The same holds for a
   link into another page of the site, ``(/phonometry/es/...#la-medición)``,
   and a search engine audit of the published site reported 150 of those as
   broken. The fix the corpus already used is an ASCII ``<span id=...>``
   above the heading. A link to another site is its own business and is not
   read.

4. **An opening ``$$`` with the formula on the same line.** Display maths is a
   fence, and like a code fence everything after the opening delimiter is read
   as *meta*, not as content. So ``$$\tau = ...`` opens a block that only ends
   at the next line that is exactly ``$$``, and a trailing ``$$`` at the end of
   the second line does not close it. The block then swallows the document
   until the next display block, which becomes its terminator: two hundred
   lines of prose vanished into a maths node, and the first ``{`` past the
   stolen terminator was handed to MDX as JavaScript. The build failed with
   ``Could not parse expression with acorn`` pointing two hundred lines away
   from the cause, and took five later checks down with it, each reporting a
   half-built site rather than the defect. If the tail does close on the same
   line the failure is silent instead: it parses as *inline* maths, so a
   centred display equation ships as a small one in the run of text.

Only that opening form is a hazard: a ``$$`` alone on its line is exactly what
the convention wants, opening and closing.

5. **A less-than sign glued to what follows it, in MDX.** MDX reads ``<`` as
   the start of a JSX tag, and a tag name has to start with a letter. So a
   quoted "<0,02 above 200 Hz" in the prose of an ``.mdx`` page does not
   reach the reader as text: the build fails with ``Unexpected character `0`
   before name``, and only the site build sees it. A ``<`` followed by a
   space, one in inline code or in maths, and an escaped ``\<`` are all
   fine. So is one inside a quoted attribute value of a JSX tag, on however
   many lines the tag takes: an ``alt`` text such as "a band of <0.1 dB" is
   a string, and MDX never reads it as prose. One between the attributes of
   a tag is not, and MDX fails there too. A plain ``.md`` page is not read
   as MDX, so only the ``<`` of MDX prose followed by something no tag name
   can start with is reported.

   The page is read from left to right, as MDX reads it, so whichever of
   these starts first wins: a ``<`` inside a code span starts no tag, and a
   backtick inside an attribute value opens no code span. A code span,
   inline maths and a tag in the middle of a paragraph run across line
   breaks until the paragraph ends, at a blank line or at a line that opens
   a block, as they do in MDX. A tag that has its lines to itself is a
   block of its own, and MDX lets it run across blank lines as well.

6. **A wrapped line of nothing but ``=`` or ``-``.** Under a line of text,
   such a line is not the continuation of a sentence: CommonMark reads it as
   a setext underline and turns the text above into a heading, ``=`` an h1
   and ``-`` an h2. A formula wrapped just before its ``=`` did this to the
   errata page: the list item above became a second h1 of the page, its open
   ``$`` was cut off by the heading, and every later ``$`` of the item paired
   with the wrong partner, so its prose rendered as maths and its formulas as
   raw TeX. GitHub's rendering of the mirror showed the same heading. A real
   heading is written with ``#`` here, and a thematic break stands after a
   blank line, so a line like this right under text is always the defect.
   Inside a display block it is neither: ``=`` alone on a line of a formula
   written one term per line is maths, and so is the line under it.

Display maths is read the way ``remark-math`` reads it, as a fence of ``$``:
a run of two or more opens it, with a meta after it that holds no ``$``, and
only a line of a run as long or longer, with nothing after it, closes it. No
rule but the fourth reads the opening line, and none reads what follows it
until the block closes: like code, it is not markdown. Fenced code is not
read at all, a ``math`` fence included.

The YAML frontmatter at the top of a page is not markdown: it is read as
data, and Astro blanks it before MDX compiles the body. No rule reads it, so
a ``description`` may say "<0,02 dB".

Usage::

    python scripts/check_markdown_hazards.py

Exit status 0 when every page is clean, 1 otherwise, with the file, the line
and the offending text.
"""

from __future__ import annotations

import pathlib
import re
import sys

from markdown_fences import code_lines

_ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Trees of hand-written markdown. The API reference is generated from the
#: docstrings and the plans folder is local scratch, so neither is checked.
_ROOTS = (
    _ROOT / "site" / "src" / "content" / "docs",
    _ROOT / "docs",
)
_SKIP = ("reference/api/", "superpowers/")

#: The markers that open a new CommonMark block at the start of a line.
_BLOCK_MARKER = r"[-*+]\s|>|#{1,6}\s|\d{1,9}[.)]\s|\||```|~~~"

#: A line that opens a new CommonMark block rather than continuing a paragraph.
_BLOCK = re.compile(rf"^\s{{0,3}}(?:{_BLOCK_MARKER})")

#: ``>`` opening a line with content after it: a wrapped comparison operator,
#: unless the paragraph deliberately starts a quotation, which is always
#: preceded by a blank line.
_QUOTE = re.compile(r"^>\s*\S")

#: Text that continues a paragraph rather than starting a block of its own.
_PROSE = re.compile(r"^\s{0,3}[^\s\-*+>#|<:0-9]")

#: A link with a fragment: the address before the ``#``, which is empty on a
#: same-page link, and the fragment, which is checked for a character markdown
#: will percent-encode on the way out.
_ANCHOR = re.compile(r"\]\(([^)\s#]*)#([^)\s]+)\)")

#: An address with a scheme: a link off this site, whose ids are not ours.
_EXTERNAL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

#: An opening display-maths fence with the formula on the same line. The tail
#: is the fence's meta, so the block does not end where the author thinks.
_MATH_META = re.compile(r"^[ \t]*\$\$\s*\S")

#: A line of nothing but ``=`` or ``-``: a setext underline when text is above it.
_SETEXT = re.compile(r"^[ \t]*(?:=+|-+)[ \t]*$")

#: A line that opens display maths, as remark-math reads it: a run of two
#: ``$`` or more and a meta with no ``$`` in it. A line with another ``$``
#: after the run opens nothing: it is a paragraph that holds inline maths.
_DISPLAY_OPEN = re.compile(r"^[ \t]*(\${2,})[^$]*$")

#: A line that may close display maths: a run of ``$`` and nothing after it
#: but blanks. It closes the block when the run is as long as the opening one.
_DISPLAY_CLOSE = re.compile(r"^[ \t]*(\${2,})[ \t]*$")

#: The line that opens and closes the YAML frontmatter, and nothing else.
_FRONTMATTER = "---"

#: In MDX prose, a ``<`` followed by a character no JSX tag can start with:
#: MDX still reads it as a tag and the build fails. An escaped ``\<`` never
#: gets here, since the escapes are blanked with the rest of what is not prose.
_MDX_LESS_THAN = re.compile(r"<(?=[^A-Za-z/!_$>\s])")

#: One character of a paragraph: anything but a line break, or a line break
#: that neither leaves a blank line nor starts a line that opens a block.
_IN_PARAGRAPH = rf"(?:[^\n]|\n(?![ \t]*\n)(?![ \t]{{0,3}}(?:{_BLOCK_MARKER})))"


def _span(name: str, delimiter: str) -> str:
    """Inline code or inline maths, as CommonMark and remark-math read them.

    A run of ``delimiter`` closed by a run of the same length, within one
    paragraph. Nothing inside is escaped.
    """
    mark = re.escape(delimiter)
    return (
        rf"(?P<{name}>{mark}+)(?!{mark}){_IN_PARAGRAPH}*?"
        rf"(?<!{mark})(?P={name})(?!{mark})"
    )


def _jsx_tag(char: str) -> str:
    """A JSX tag, opening or closing, every character of it a ``char``.

    A name, then everything up to the first ``>`` outside a quoted value.
    """
    between = rf"(?:(?![\"'>]){char})*"
    value = rf"\"(?:(?!\"){char})*\"|'(?:(?!'){char})*'"
    return rf"</?[A-Za-z_$]{between}(?:(?:{value}){between})*>"


#: What MDX does not read as prose, found from left to right so that the
#: first one to start wins, as in MDX. A tag with its lines to itself is a
#: block and may run across blank lines; one within a paragraph may not. An
#: escape, a code span and inline maths are blanked whole, a tag only in its
#: quoted values, and a run of backticks or dollars that nothing closes is
#: plain text.
_MDX_READING = re.compile(
    rf"(?P<tag>^[ \t]*{_jsx_tag(r'[\s\S]')}(?=[ \t]*$)|{_jsx_tag(_IN_PARAGRAPH)})"
    rf"|(?P<literal>\\[!-/:-@\[-`{{-~]|{_span('code', '`')}|{_span('maths', '$')})"
    r"|`+|\$+",
    re.MULTILINE,
)

#: A quoted attribute value, which MDX reads as a string, never as prose.
_JSX_VALUE = re.compile(r"\"[^\"]*\"|'[^']*'")


#: An inline code span: a run of backticks, its text, and a run of the same
#: length again. Each run is a whole run, as CommonMark reads it, so one tick
#: of a longer run never closes a shorter one. A ``$`` inside a span is code
#: (the ``$schema`` key of a JSON document), and CommonMark reads the span
#: before any maths could open in it.
_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")


def _unescaped_dollars(line: str) -> int:
    r"""Inline ``$`` delimiters on a line, ignoring ``\$``, ``$$`` and code spans."""
    prose = _CODE_SPAN.sub("", line)
    return len(re.findall(r"(?<!\\)\$", re.sub(r"\$\$", "", prose)))


def _blank(match: re.Match[str]) -> str:
    """The matched text with every character but its line breaks a space."""
    return re.sub(r"[^\n]", " ", match.group())


def _as_mdx_reads_it(found: re.Match[str]) -> str:
    """One find of ``_MDX_READING``, blanked where MDX reads no prose.

    A tag keeps all but its quoted values; an escape, a code span and inline
    maths go whole; plain text stays.
    """
    if found["tag"] is not None:
        return _JSX_VALUE.sub(_blank, found.group())
    if found["literal"] is not None:
        return _blank(found)
    return found.group()


def _body_start(lines: list[str]) -> int:
    """Index of the first line after the YAML frontmatter, 0 with none."""
    if not lines or lines[0].rstrip() != _FRONTMATTER:
        return 0
    for index in range(1, len(lines)):
        if lines[index].rstrip() == _FRONTMATTER:
            return index + 1
    return 0


def _display_maths(lines: list[str], code: list[bool]) -> list[str]:
    """Each line's part in display maths: ``"open"``, ``"maths"`` or ``"prose"``.

    ``"maths"`` is a line of the formula or the line that closes it. A line of
    code opens nothing, and a block never closed runs to the end of the page,
    as remark-math has it.
    """
    parts: list[str] = []
    opening = ""
    for line, is_code in zip(lines, code, strict=True):
        if opening:
            closing = _DISPLAY_CLOSE.match(line)
            if closing and len(closing.group(1)) >= len(opening):
                opening = ""
            parts.append("maths")
            continue
        found = None if is_code else _DISPLAY_OPEN.match(line)
        if found is None:
            parts.append("prose")
        else:
            opening = found.group(1)
            parts.append("open")
    return parts


def _mdx_prose(lines: list[str], start: int) -> list[str]:
    """The lines as MDX reads their prose, everything else blanked.

    The frontmatter, the code fences and the display maths go whole, line by
    line; escapes, inline code, inline maths and the quoted attribute values
    of a JSX tag go where they stand, read from left to right over the whole
    page, since each can run over several lines. Blanking rather than
    dropping keeps every character on its line and column.
    """
    body = lines[start:]
    code = list(code_lines(body))
    kept = [""] * start + [
        line if not is_code and part == "prose" else ""
        for line, is_code, part in zip(
            body, code, _display_maths(body, code), strict=True
        )
    ]
    return _MDX_READING.sub(_as_mdx_reads_it, "\n".join(kept)).split("\n")


def _less_than_problems(rel: str, lines: list[str], start: int) -> list[str]:
    """Rule 5: a ``<`` in MDX prose that MDX reads as the start of a tag."""
    return [
        f"{rel}:{number}: {prose[glued.start() : glued.start() + 12]!r} "
        f"puts a '<' before a character no tag name starts with, and MDX "
        f"reads it as a tag: the site build fails. Write it in words, put "
        f"a space after '<', or escape it as '\\<'."
        for number, prose in enumerate(_mdx_prose(lines, start), start=1)
        for glued in _MDX_LESS_THAN.finditer(prose)
    ]


def _cut_maths_problems(
    where: str, line: str, line_before: int, *, open_math: bool
) -> list[str]:
    """Rule 1: inline maths still open when a block marker ends the paragraph."""
    if not (open_math and _BLOCK.match(line)):
        return []
    return [
        f"{where}: inline maths opened on line {line_before} is cut off by a "
        f"block marker; rewrap so the line does not start with "
        f"{line.lstrip()[:2]!r}"
    ]


def _wrapped_quote_problems(where: str, line: str, before: str) -> list[str]:
    """Rule 2: a ``>`` that wrapped to the start of a line of a paragraph."""
    if not (_QUOTE.match(line) and _PROSE.match(before)):
        return []
    return [
        f"{where}: {line.strip()[:40]!r} continues the sentence above but "
        f"starts a block quote; rewrap so '>' does not start the line"
    ]


def _anchor_problems(where: str, line: str) -> list[str]:
    """Rule 3: a link into this site that the href will percent-encode."""
    return [
        f"{where}: the link "
        f"'{anchor.group(1)}#{anchor.group(2)}' will be percent-encoded in the href, "
        f"and crawlers and the accessibility audit compare the raw attribute "
        f"against the ids, so it reads as a dangling anchor. Put "
        f'<span id="ascii-slug"></span> above the heading and link to that, as '
        f"the pages that already hit this do."
        for anchor in _ANCHOR.finditer(line)
        if not anchor.group(2).isascii() and not _EXTERNAL.match(anchor.group(1))
    ]


def _math_meta_problems(where: str, line: str) -> list[str]:
    """Rule 4: an opening ``$$`` with the formula on the same line."""
    if not _MATH_META.match(line):
        return []
    if line.rstrip().endswith("$$"):
        consequence = (
            "It closes on this line, so it ships as inline maths instead of a "
            "centred display block."
        )
    else:
        consequence = (
            "Nothing closes it until a line that is exactly '$$', so it "
            "swallows the prose in between and breaks the build far from here."
        )
    return [
        f"{where}: {line.strip()[:40]!r} puts the formula on the opening "
        f"'$$', where it is read as the fence's meta, not as maths. "
        f"{consequence} Put '$$' alone on its own line, above and below."
    ]


def _setext_problems(where: str, line: str, before: str) -> list[str]:
    """Rule 6: a line of ``=`` or ``-`` that turns the text above into a heading."""
    if not (_SETEXT.match(line) and before.strip()):
        return []
    # A fence line above is code, and the caller does not ask about it; what is
    # left to tell apart is a heading, a table row, a tag and a rule of its own.
    if before.lstrip().startswith(("#", "|", "<")) or _SETEXT.match(before):
        return []
    level = "an h1" if "=" in line else "an h2"
    return [
        f"{where}: a line of only {line.strip()[0]!r} under text is a setext "
        f"underline, so the text above becomes {level}; rewrap so the line "
        f"carries text, or leave a blank line before a thematic break"
    ]


def _maths_left_open(line: str, *, open_math: bool) -> bool:
    """Whether an inline ``$`` is still open once this line is read."""
    if not line.strip() or _BLOCK.match(line):
        open_math = False
    if _unescaped_dollars(line) % 2 == 1:
        open_math = not open_math
    return open_math


def _markdown_problems(rel: str, lines: list[str], start: int) -> list[str]:
    """Rules 1 to 4 and 6, which read the page line by line as CommonMark does.

    Code and display maths are not markdown, so no rule reads them, but the
    fourth reads the line that opens a display block, which is its business.
    """
    problems: list[str] = []
    open_math = False
    body = lines[start:]
    code = list(code_lines(body))
    parts = [""] * start + [
        "code" if is_code else part
        for is_code, part in zip(code, _display_maths(body, code), strict=True)
    ]
    for index in range(start, len(lines)):
        line = lines[index]
        where = f"{rel}:{index + 1}"
        if parts[index] == "open":
            problems.extend(_math_meta_problems(where, line))
        if parts[index] != "prose":
            open_math = False
            continue
        before = lines[index - 1] if index else ""
        problems.extend(_cut_maths_problems(where, line, index, open_math=open_math))
        problems.extend(_wrapped_quote_problems(where, line, before))
        problems.extend(_anchor_problems(where, line))
        problems.extend(_math_meta_problems(where, line))
        if index > start and parts[index - 1] == "prose":
            problems.extend(_setext_problems(where, line, before))
        open_math = _maths_left_open(line, open_math=open_math)
    return problems


def check_text(text: str, rel: str) -> list[str]:
    """Every hazard of one page; ``rel`` names it, and an ``.mdx`` one is MDX."""
    lines = text.splitlines()
    start = _body_start(lines)
    problems = _markdown_problems(rel, lines, start)
    if rel.endswith(".mdx"):
        problems.extend(_less_than_problems(rel, lines, start))
    return problems


def _check(path: pathlib.Path) -> list[str]:
    return check_text(
        path.read_text(encoding="utf-8"), path.relative_to(_ROOT).as_posix()
    )


def main() -> int:
    problems: list[str] = []
    checked = 0
    for root in _ROOTS:
        for path in sorted(root.rglob("*.md*")):
            if any(part in path.as_posix() for part in _SKIP):
                continue
            checked += 1
            problems.extend(_check(path))

    if problems:
        print(
            "::error::markdown that does not render the way it reads", file=sys.stderr
        )
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"Markdown renders the way it reads: {checked} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
