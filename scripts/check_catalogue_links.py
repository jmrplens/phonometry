#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Refuse a catalogue link that opens a document other than the one it sits beside.

A link to the ISO or IEC catalogue carries a number and nothing else
(``https://www.iso.org/standard/70242.html``,
``https://webstore.iec.ch/en/publication/1204``), so a slip of the number opens
another document while every page still builds, every link still resolves
and the reader who follows it lands on a steel sheet or a needle-based
injector. A review of the tone-burst guide found its reference to
IEC 60268-1:1985, in English and in Spanish, opening IEC 60264-2-1:1989,
and the sweep that followed found 89 more links of the pages and their
mirrors opening something other than what they sat beside, many of them
copied from page to page: 84 opened another document or none at all
(ISO 4871:1996 opened ISO 4878:1981, ISO 16283-2:2020 two different
plastics standards, each of the five standards of the ISO 11200 series the
workstation guide cites something else, and four parts of ISO 10140 a
number the catalogue does not hold), and 5 opened a later edition than the
one the page cites. A review of this check found 5 more opening
IEC 60268-5:2003 beside the amended edition, IEC 60268-5:2003+A1:2007,
that the pages cite. This is the guard for that class.

The number alone cannot be read for its document, so :data:`PINNED`
(``scripts/catalogue_ids.json``) holds, for every number the pages link, the
designation its catalogue gives it: ISO's open data for an iso.org number,
the title of the webstore's own page for an IEC one. Every catalogue link in
the pages of the site and in the mirrors under ``docs/`` then has to sit
beside that designation, read where the link is written:

- in a page's frontmatter, the ``url`` of a reference beside the
  reference's ``designation``, and a link in its ``note`` beside its own
  clause (the note after the link before it, the last semicolon or the last
  full stop, up to the link), from the last designation of the link's
  catalogue the clause names: "Adopted in Europe as EN ISO 3382-3:2012, the
  edition implemented here; since revised as ISO 3382-3:2022 (https://...)"
  holds the link to the 2022 edition alone, while the reference's own
  ``url`` stays on the 2012 one it cites; a note link whose clause names no
  designation of its catalogue speaks of its own reference, and is read
  beside the reference's ``designation``;
- in a table, the link's own cell up to the link, or, when that names no
  designation of the link's catalogue, the nearest cell before it in the
  row that names one;
- anywhere else, the link's own clause read the same way, or, when that
  names no designation of the link's catalogue, the paragraph or list item
  up to the link without the other links and without the clauses that name
  a later edition ("since revised as ISO 13472-1:2022", "superseded by" and
  the Spanish "revisada después como" and "sustituida por"), so that an
  entry's own catalogue link names the edition the entry cites and not the
  one it was revised as.

A link whose label names a designation, publisher and number, is read by its
label alone. A catalogue address in a code block, an inline code span or a
comment is an example or a note, and no link: the spans and the comments are
read by ``scripts/markdown_spans.py``, as the site reads them. A frontmatter is
YAML, whose note the site shows as text with every address in it a link, so
each address there is read.

The designation is matched by a publisher that publishes it, its number and,
when the text gives them, its year and its amendments. The publishers are the
ones the catalogue's own designation writes: "IEC 12354-1:2017" does not name
ISO 12354-1:2017, while either publisher names a joint document
(ISO/IEC Guide 98-3:2008) in either catalogue, and IEC alone names one of the
IEC documents ISO's catalogue lists under their own designation. The catalogue
page of ISO 717-2:2013 beside "ISO 717-2:2020" is another document, the
edition the page does not cite.
The IEC webstore numbers an edition, that edition consolidated with its
amendment and the amendment alone apart (IEC 60268-5:2003,
IEC 60268-5:2003+AMD1:2007 CSV and IEC 60268-5:2003/AMD1:2007), so
"IEC 60268-5:2003+A1:2007" names the second of them only. ISO's open data
holds no consolidated edition, and the page of an ISO edition lists its
amendments, so "ISO 17497-1:2004+A1:2014" names the page of
ISO 17497-1:2004; an ISO amendment alone (ISO 17497-1:2004/Amd 1:2014) has
a number of its own. IEC renumbered its older publications by adding 60000
in 1997, so "IEC 651" names what the webstore lists as IEC 60651.

A number the table does not hold fails, and so does a pinned number no page
links any more, so the table is the census of what the pages link and
nothing else. ``--refresh`` resolves the numbers the pages link and the
table lacks (and, with ``--all``, every number again) from the two
catalogues, and drops the ones no page links; it is the only step that needs
the network, and a maintainer runs it when a page gains a catalogue link.
ISO's open data is a file of about 80 MB, which ``--iso-open-data`` reads
from a local copy instead of downloading it.

Exit status 0 when every catalogue link sits beside its document, 1
otherwise. The check itself is standard library only and reads nothing from
the network, so it runs in a job that installs nothing.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass

from markdown_fences import code_lines, page_kind, page_lines
from markdown_spans import blank_inline_spans_by_block

#: The repository.
ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The trees whose pages are read: the site's pages, in both languages, and
#: the mirrors GitHub serves.
PAGE_ROOTS = ("site/src/content/docs", "docs")

#: The pinned designations, by catalogue and number.
PINNED = ROOT / "scripts" / "catalogue_ids.json"

#: ISO's open data: one JSON record per deliverable, with its catalogue
#: number (``id``) and its designation (``reference``).
ISO_OPEN_DATA = (
    "https://isopublicstorageprod.blob.core.windows.net/opendata/_latest/"
    "iso_deliverables_metadata/json/iso_deliverables_metadata.jsonl"
)

#: The page of one IEC publication; its title is the designation.
IEC_PAGE = "https://webstore.iec.ch/en/publication/{number}"

#: A catalogue link: the ISO catalogue or the IEC webstore, and its number.
LINK = re.compile(
    r"https?://(?:www\.)?(?:iso\.org/standard/(?P<iso>\d+)(?:\.html)?"
    r"|webstore\.iec\.ch/(?:en/)?publication/(?P<iec>\d+))"
)

#: A markdown link, label and destination, taken out of the text a catalogue
#: link is read beside.
MARKDOWN_LINK = re.compile(r"\[[^\]\n]*\]\([^)\s]*\)")

#: The start of a list item, a table row or a heading: a block of its own.
_BLOCK_START = re.compile(r"\s*(?:[-*+]\s|\d+\.\s|\||#)")

#: The number of a designation, the year right after it and the amendments
#: written after that: ``+A1:2007`` (or ``+AMD1:2007``) for the edition with
#: its amendment, ``/AMD1:2007`` (or ``/Amd 1:2007``) for the amendment
#: alone.
_DESIGNATION = re.compile(
    r"(?<![\w.-])(\d+(?:-\d+)*)(?::(\d{4}))?"
    r"((?:\s?[+/]\s?(?:AMD|Amd|A)\.?\s?\d+(?::\d{4})?)*)"
)

#: One amendment of a designation: ``+`` or ``/``, its number and its year.
_AMENDMENT = re.compile(r"([+/])\s?(?:AMD|Amd|A)\.?\s?(\d+)(?::(\d{4}))?")

#: What stands for a link taken out of the text a link is read beside.
_LINK_GAP = "\x00"

#: The end of a clause: a link taken out, a semicolon, or a full stop before
#: a space or a line break.
_CLAUSE_END = re.compile(r"\x00|;|\.(?=\s)")

#: The words the pages write for a document since revised or superseded, in
#: English and in Spanish, and the rest of their clause: the edition they
#: name is a later one, never the one the entry's own link opens.
_REVISED = re.compile(
    r"(?i:\b(?:since\s+revised\s+as|revisad[ao]\s+después\s+como"
    r"|superseded\s+by|sustituid[ao]\s+por)\b)[^;.,)\x00]*"
)

#: The characters a page may write inside a designation for a space or a
#: hyphen.
_SPACES = str.maketrans(
    {"\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2011": "-", "\u2010": "-"}
)

#: The kind of deliverable a designation may write after its publishers and
#: before its number (IEC TS 61094-8, ISO/IEC Guide 98-3; the IEC webstore
#: writes GUIDE).
_KIND = r"(?:\s+(?:TS|TR|PAS|Guide|GUIDE))?"

#: A designation of each catalogue as a page writes one: the publisher, the
#: kind of deliverable if any (ISO/TS, ISO/IEC, IEC TS) and the number. A text
#: that holds none of the link's catalogue does not say which document the
#: link opens.
_NAMED = {
    catalogue: re.compile(rf"(?<![\w-]){publisher}(?:/[A-Z]+)*{_KIND}\s+\d")
    for catalogue, publisher in (("iso", "ISO"), ("iec", "IEC"))
}

#: The two publishers whose catalogues the check reads, by catalogue.
PUBLISHERS = {"iso": "ISO", "iec": "IEC"}

#: The publishers a designation writes right before its number: ISO, IEC or
#: both, alone or joined by slashes to each other or to the kind of
#: deliverable (ISO/IEC, IEC/ISO, ISO/TS, ISO/IEC/IEEE), with a kind after
#: them if any (IEC TS, ISO/IEC Guide). An adoption keeps the publisher it
#: adopts in front of the number (EN ISO 3382-3, UNE-EN ISO 717-1).
_PUBLISHED_BY = re.compile(
    rf"(?<![\w-])((?:[A-Z]+/)*(?:ISO|IEC)(?:/[A-Z]+)*){_KIND}\s+$"
)

#: A key of a page's frontmatter, at the top level or of a reference, and the
#: start of its value.
_FRONTMATTER_KEY = re.compile(r"^(?:  - |    )?([A-Za-z_][\w-]*):[ \t]*", re.MULTILINE)

#: The border between two cells of a table row: a pipe the page does not
#: escape.
_CELL_BORDER = re.compile(r"(?<!\\)\|")


@dataclass(frozen=True)
class Link:
    """One catalogue link, where it is written and what it is read beside."""

    path: str
    line: int
    catalogue: str
    number: str
    beside: str


def _frontmatter_end(text: str) -> int:
    """The offset where a page's frontmatter ends, or 0 when it has none."""
    if not text.startswith("---\n"):
        return 0
    end = text.find("\n---", 4)
    return max(end, 0)


def _names_a_designation(text: str, catalogue: str) -> bool:
    """Whether a text names some designation of the link's catalogue."""
    return _NAMED[catalogue].search(text.translate(_SPACES)) is not None


def _names_any_designation(text: str) -> bool:
    """Whether a text names some designation of either catalogue."""
    return any(_names_a_designation(text, catalogue) for catalogue in _NAMED)


def _links_out(text: str, gap: str = " ") -> str:
    """The text with its markdown links and bare catalogue addresses taken out."""
    return LINK.sub(gap, MARKDOWN_LINK.sub(gap, text))


def _own_clause(written: str, catalogue: str) -> str:
    """The clause a link ends, from the last designation of its catalogue on.

    The clause starts after the link before it, the last semicolon or the
    last full stop, whichever comes later. Read from its last designation of
    the link's catalogue, "Adopted in Europe as EN ISO 3382-3:2012, and since
    revised as ISO 3382-3:2022 (...)" holds the link to the 2022 edition.
    An empty text when the clause names none: the link then speaks of the
    entry or the reference it is written in.
    """
    clause = _CLAUSE_END.split(_links_out(written, _LINK_GAP))[-1]
    named = list(_NAMED[catalogue].finditer(clause.translate(_SPACES)))
    return clause[named[-1].start() :] if named else ""


def _read_up_to(written: str, catalogue: str) -> str:
    """What a link is read beside in the text written up to it.

    A link whose label names a designation, a publisher and its number
    ("[ISO 3382-3:2022](...)"), is read by its label, whichever catalogue the
    designation belongs to: a label that names an IEC document on an iso.org
    link tells the reader what it opens, and is held to that. A label that
    gives a number and no publisher ("[2017 catalogue](...)", "[Part 1](...)")
    names no document, and the link is read as any other: beside its own
    clause when that names a designation of the link's catalogue, and
    otherwise beside the whole text before it, without the other links and
    without the clauses that name a later edition ("since revised as
    ISO 13472-1:2022"): an entry's own catalogue link opens the edition the
    entry cites, not the one it was revised as.
    """
    label = re.search(r"\[([^\]\n]*)\]\($", written)
    if label and _names_any_designation(label.group(1)):
        return label.group(1)
    before = written[: label.start()] if label else written
    own = _own_clause(before, catalogue)
    if own:
        return own
    return _REVISED.sub(" ", _links_out(before, _LINK_GAP)).replace(_LINK_GAP, " ")


def _beside_in_frontmatter(text: str, start: int, end: int, catalogue: str) -> str:
    """What a link in a page's frontmatter is read beside.

    The ``url`` of a reference is read beside the reference's
    ``designation``. A link written in any other field, a ``note`` above all,
    is read beside its own clause in that field, from the last designation
    of the link's catalogue the clause names: a note that says "Adopted in
    Europe as EN ISO 3382-3:2012, the edition implemented here; since revised
    as ISO 3382-3:2022 (https://www.iso.org/standard/77437.html)" links the
    edition it names there, not the one its reference cites, and its link is
    held to ISO 3382-3:2022 alone. A second link of the note is read after
    the first, not beside it.

    A link whose clause names no designation of its catalogue ("The
    catalogue page (https://...) lists the corrigenda") speaks of its own
    reference, so it is read beside the reference's ``designation``, as the
    ``url`` is. That still holds the number to a document: refusing the
    link would ask the note to repeat the designation its reference already
    gives, and letting it through would leave the number unread.
    """
    item_start = text.rfind("\n  - ", 0, start)
    item_end = text.find("\n  - ", start)
    if item_end < 0 or item_end > end:
        item_end = end
    item = text[max(item_start, 0) : item_end]
    designation = re.search(r'^\s*designation:\s*"([^"]*)"', item, re.MULTILINE)
    own = designation.group(1) if designation else ""
    keys = list(_FRONTMATTER_KEY.finditer(text, item_start + 1, start))
    if not keys or keys[-1].group(1) == "url":
        return own
    return _own_clause(text[keys[-1].end() : start].lstrip("\"'"), catalogue) or own


def _beside_in_body(text: str, start: int, catalogue: str) -> str:
    """What a link in a page's body is read beside.

    In a table, the link's own cell up to the link; when that names no
    designation of the link's catalogue (a cell that holds only
    "[catalogue](...)"), the nearest cell before it in the row that names
    one, with its links taken out. Anywhere else, the list item or paragraph
    the link is written in, up to it. The link's own cell, list item or
    paragraph is read as :func:`_read_up_to` reads the text up to a link.
    """
    line_start = text.rfind("\n", 0, start) + 1
    line = text[line_start:start]
    if line.lstrip().startswith("|"):
        *cells, cell = _CELL_BORDER.split(line)
        own = _read_up_to(cell, catalogue)
        if _names_a_designation(own, catalogue):
            return own
        # The text before the row's first border is its indentation.
        for previous in map(_links_out, reversed(cells[1:])):
            if _names_a_designation(previous, catalogue):
                return previous
        return own
    lines = [line]
    cursor = line_start
    while not _BLOCK_START.match(lines[0]) and cursor > 0:
        previous_start = text.rfind("\n", 0, cursor - 1) + 1
        previous = text[previous_start : cursor - 1]
        if not previous.strip():
            break
        lines.insert(0, previous)
        cursor = previous_start
    return _read_up_to("\n".join(lines), catalogue)


def _blank(text: str) -> str:
    """The text with every character but a line end a space."""
    return re.sub(r"[^\n]", " ", text)


def _without_code(path: str, text: str, end: int) -> str:
    """The page with its code and its comments blanked, its frontmatter as written.

    A catalogue address in a fenced or indented code block, in an inline code
    span or in a comment is an example of one or a note to the maintainer,
    not a link a reader follows (rule F70 shows a wrong one as its
    counterexample, and a page may show the form of an address in backticks).
    The body is read as the site reads it, by :mod:`markdown_spans`: a code
    span opens on a run of backticks and closes on the next run as long, never
    past its paragraph, list item or table cell, and a backslash before the
    run shows the backtick and opens nothing; the page's comments are read in
    the same pass. The frontmatter is YAML, not Markdown: the site shows a
    reference's note as text and links every address in it, backticks or not,
    so it is kept whole. Every blanked character but a line end becomes a
    space, so every offset still points where it did.

    :param end: Where the page's frontmatter ends (:func:`_frontmatter_end`).
    """
    kind = page_kind(path)
    lines = (_blank(text[:end]) + text[end:]).split("\n")
    walked = list(page_lines(lines, kind=kind))
    body = "\n".join(
        " " * len(line) if code else line
        for line, code in zip(
            lines, code_lines(lines, kind=kind, walked=walked), strict=True
        )
    )
    prose = blank_inline_spans_by_block(body, "`", kind, kind=kind, walked=walked)
    return text[:end] + prose[end:]


def links_in(path: str, text: str) -> list[Link]:
    """Every catalogue link of a page, with the text that should name its document."""
    if LINK.search(text) is None:
        # Most pages link no catalogue: they need no reading.
        return []
    end = _frontmatter_end(text)
    text = _without_code(path, text, end)
    found = []
    for match in LINK.finditer(text):
        start = match.start()
        catalogue = "iso" if match.group("iso") else "iec"
        number = match.group("iso") or match.group("iec")
        if start < end:
            beside = _beside_in_frontmatter(text, start, end, catalogue)
        else:
            beside = _beside_in_body(text, start, catalogue)
        found.append(
            Link(
                path,
                text.count("\n", 0, start) + 1,
                catalogue,
                number,
                beside.translate(_SPACES),
            )
        )
    return found


#: The amendments a designation writes after its year, each as its sign
#: (``+`` with the edition, ``/`` alone), its number and its year if given.
type Amendments = tuple[tuple[str, str, str], ...]


def _amendments(written: str, catalogue: str) -> Amendments:
    """The amendments a designation names, as its catalogue numbers them.

    The IEC webstore gives an edition consolidated with its amendments a
    number of its own (IEC 60268-5:2003+AMD1:2007 CSV, apart from
    IEC 60268-5:2003), and ISO's open data holds no consolidated edition at
    all: the catalogue page of an ISO edition lists its amendments, so the
    ``+A1:2014`` of an ISO designation names the edition itself. An amendment
    alone (``/Amd 1:2014``) has a number of its own in both.
    """
    return tuple(
        (sign, number, year)
        for sign, number, year in _AMENDMENT.findall(written)
        if sign == "/" or catalogue == "iec"
    )


def _publishers(text: str, at: int) -> frozenset[str]:
    """The publishers, of ISO and IEC, a text writes right before the number at ``at``.

    None when the number stands alone: "717-2" in "ISO 717-1 and 717-2"
    names no publisher, and so no document of either catalogue.
    """
    written = _PUBLISHED_BY.search(text[:at])
    if written is None:
        return frozenset()
    return frozenset(written.group(1).split("/")) & frozenset(PUBLISHERS.values())


def _numbers(
    designation: str, catalogue: str
) -> tuple[set[str], str | None, Amendments, frozenset[str]]:
    """The numbers a text may give a pinned designation, its year, its
    amendments and the publishers that name it.

    The publishers are those the catalogue's own designation writes: ISO
    alone for ISO 12354-1:2017, both for ISO/IEC Guide 98-3:2008, which
    either names, and IEC alone for IEC 60974-1:1998, one of the IEC
    documents ISO's catalogue lists under their own designation. A
    designation that writes neither is the catalogue's own publisher's.
    """
    match = _DESIGNATION.search(designation)
    if match is None:
        return set(), None, (), frozenset()
    number, year = match.group(1), match.group(2)
    numbers = {number}
    head, _, rest = number.partition("-")
    if catalogue == "iec" and len(head) == 5 and head.startswith("60"):
        # IEC 651 is IEC 60651: the 1997 renumbering added 60000.
        numbers.add(str(int(head) - 60000) + ("-" + rest if rest else ""))
    publishers = _publishers(designation, match.start()) or frozenset(
        {PUBLISHERS[catalogue]}
    )
    return numbers, year, _amendments(match.group(3), catalogue), publishers


def _same_amendments(written: Amendments, pinned: Amendments) -> bool:
    """Whether a text names the amendments a pinned designation carries.

    ``+A1:2007`` and ``+AMD1:2007`` are the same amendment, and a year the
    text leaves out does not tell two apart.
    """
    return len(written) == len(pinned) and all(
        sign == pinned_sign
        and number == pinned_number
        and (not year or not pinned_year or year == pinned_year)
        for (sign, number, year), (pinned_sign, pinned_number, pinned_year) in zip(
            written, pinned, strict=True
        )
    )


def names(beside: str, designation: str, catalogue: str) -> bool:
    """Whether ``beside`` names ``designation``.

    By a publisher that publishes it, its number and, when the text gives
    them, its year and its amendments. "IEC 12354-1:2017" does not name
    ISO 12354-1:2017: a number is read only behind a publisher the
    catalogue's designation writes (:func:`_numbers`), so the IEC number of
    an iso.org link, or an ISO one of a webstore link, names another
    document. The edition, the edition with its amendment and the amendment
    alone are three documents, wherever their catalogue numbers them apart.
    """
    beside = beside.translate(_SPACES)
    numbers, year, amended, publishers = _numbers(designation, catalogue)
    written = [
        (match.group(2), _amendments(match.group(3), catalogue))
        for match in _DESIGNATION.finditer(beside)
        if match.group(1) in numbers and _publishers(beside, match.start()) & publishers
    ]
    dated = [found for found in written if found[0]]
    return any(
        (year is None or found is None or found == year)
        and _same_amendments(amendments, amended)
        for found, amendments in dated or written
    )


def pages(root: pathlib.Path | None = None) -> list[str]:
    """The tracked pages of :data:`PAGE_ROOTS`."""
    root = ROOT if root is None else root
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--", *PAGE_ROOTS],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout.split("\n")
    return sorted(path for path in listed if path.endswith((".md", ".mdx")))


def read_links(root: pathlib.Path | None = None) -> list[Link]:
    """Every catalogue link of every page."""
    root = ROOT if root is None else root
    found = []
    for path in pages(root):
        found.extend(links_in(path, (root / path).read_text(encoding="utf-8")))
    return found


def load_pinned(path: pathlib.Path | None = None) -> dict[str, dict[str, str]]:
    """The pinned designations, by catalogue and number."""
    path = PINNED if path is None else path
    data = json.loads(path.read_text(encoding="utf-8"))
    return {catalogue: dict(data.get(catalogue, {})) for catalogue in ("iso", "iec")}


def problems(links: list[Link], pinned: dict[str, dict[str, str]]) -> list[str]:
    """Each link beside another document, each number unpinned, each pin unused."""
    found = []
    used: dict[str, set[str]] = {"iso": set(), "iec": set()}
    for link in links:
        used[link.catalogue].add(link.number)
        designation = pinned[link.catalogue].get(link.number)
        where = f"{link.path}:{link.line}"
        if designation is None:
            found.append(
                f"{where}: {link.catalogue} catalogue number {link.number} is not pinned in "
                f"{PINNED.relative_to(ROOT)}; run python scripts/check_catalogue_links.py --refresh"
            )
        elif not designation:
            found.append(
                f"{where}: {link.catalogue} catalogue number {link.number} opens no document "
                "the catalogue lists"
            )
        elif not names(link.beside, designation, link.catalogue):
            shown = " ".join(link.beside.split())[-120:] or "(no designation)"
            found.append(
                f"{where}: {link.catalogue} catalogue number {link.number} opens {designation}, "
                f"which the link is not written beside: {shown!r}"
            )
    for catalogue, numbers in pinned.items():
        found.extend(
            f"{PINNED.relative_to(ROOT)}: {catalogue} catalogue number {number} "
            f"({numbers[number] or 'no document'}) is linked from no page; run --refresh to drop it"
            for number in sorted(set(numbers) - used[catalogue], key=int)
        )
    return found


def _iec_designation(number: str) -> str:
    """The designation the IEC webstore's own page gives a publication number."""
    # A fixed https URL of the IEC webstore, with only the number filled in.
    request = urllib.request.Request(  # noqa: S310
        IEC_PAGE.format(number=number),
        headers={"User-Agent": "Mozilla/5.0 (catalogue link check)"},
    )
    # The same URL.
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        page = response.read().decode("utf-8", "replace")
    title = re.search(r"<title>\s*(IEC[^<|]+?)\s*(?:\|[^<]*)?</title>", page)
    return title.group(1) if title else ""


def _iso_designations(
    numbers: set[str], open_data: pathlib.Path | None
) -> dict[str, str]:
    """The designations ISO's open data gives the catalogue numbers asked for."""
    if open_data is None:
        request = urllib.request.Request(ISO_OPEN_DATA)
        # A fixed https URL of ISO's open data.
        with urllib.request.urlopen(request, timeout=600) as response:  # noqa: S310
            lines = response.read().decode("utf-8").splitlines()
    else:
        lines = open_data.read_text(encoding="utf-8").splitlines()
    found = {}
    for line in lines:
        record = json.loads(line)
        if str(record["id"]) in numbers:
            found[str(record["id"])] = str(record["reference"])
    # A number ISO's open data does not hold opens no deliverable: it is
    # pinned to no designation, and every link to it fails.
    return {number: found.get(number, "") for number in numbers}


def refresh(links: list[Link], *, every: bool, open_data: pathlib.Path | None) -> None:
    """Pin the numbers the pages link, from the catalogues, and drop the rest."""
    pinned = load_pinned() if PINNED.exists() and not every else {"iso": {}, "iec": {}}
    linked = {
        catalogue: {link.number for link in links if link.catalogue == catalogue}
        for catalogue in pinned
    }
    iso_new = linked["iso"] - set(pinned["iso"])
    if iso_new:
        pinned["iso"].update(_iso_designations(iso_new, open_data))
    for number in sorted(linked["iec"] - set(pinned["iec"]), key=int):
        pinned["iec"][number] = _iec_designation(number)
    kept = {
        catalogue: {
            number: pinned[catalogue][number]
            for number in sorted(linked[catalogue], key=int)
        }
        for catalogue in ("iso", "iec")
    }
    PINNED.write_text(
        json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    """Name each catalogue link that opens another document, or refresh the table."""
    parser = argparse.ArgumentParser(
        description="Refuse a catalogue link that opens a document other than the one it sits beside."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="pin the linked numbers from the catalogues",
    )
    parser.add_argument(
        "--all", action="store_true", help="with --refresh, resolve every number again"
    )
    parser.add_argument(
        "--iso-open-data", type=pathlib.Path, help="a local copy of ISO's open data"
    )
    args = parser.parse_args(argv)
    links = read_links()
    if args.refresh:
        refresh(links, every=args.all, open_data=args.iso_open_data)
    found = problems(links, load_pinned())
    for problem in found:
        print(problem)
    if found:
        print(
            f"\n{len(found)} catalogue link problem(s) in {len(links)} links.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Every one of the {len(links)} catalogue links sits beside the document it opens."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
