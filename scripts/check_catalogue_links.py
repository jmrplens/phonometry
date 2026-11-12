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
  reference's ``designation``, and a link in its ``note`` beside the note up
  to the link, with the other links taken out, so that "Since revised as
  ISO 3382-3:2022 (https://...)" holds the link to the 2022 edition while
  the reference's own ``url`` stays on the 2012 one it cites; a note that
  names no designation of the link's catalogue before the link speaks of
  its own reference, and its link is read beside the reference's
  ``designation``;
- in a table, the link's own cell up to the link, or, when that names no
  designation of the link's catalogue, the nearest cell before it in the
  row that names one;
- anywhere else, the paragraph or list item up to the link, with the text of
  the other links taken out, so that a "since revised as" link to a newer
  edition names that edition and the entry's own catalogue link names the one
  the entry cites.

The designation is matched by its number and, when the text gives them, its
year and its amendments: the catalogue page of ISO 717-2:2013 beside
"ISO 717-2:2020" is another document, the edition the page does not cite.
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

from markdown_fences import code_lines, page_kind

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


#: The characters a page may write inside a designation for a space or a
#: hyphen.
_SPACES = str.maketrans(
    {"\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2011": "-", "\u2010": "-"}
)

#: A designation of each catalogue as a page writes one: the publisher, the
#: kind of deliverable if any (ISO/TS, ISO/IEC, IEC TS) and the number. A text
#: that holds none of the link's catalogue does not say which document the
#: link opens.
_NAMED = {
    catalogue: re.compile(
        rf"(?<![\w-]){publisher}(?:/[A-Z]+)*(?:\s+(?:TS|TR|PAS|Guide))?\s+\d"
    )
    for catalogue, publisher in (("iso", "ISO"), ("iec", "IEC"))
}

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


def _links_out(text: str) -> str:
    """The text with its markdown links and bare catalogue addresses taken out."""
    return LINK.sub(" ", MARKDOWN_LINK.sub(" ", text))


def _read_up_to(written: str) -> str:
    """What a link is read beside in the text written up to it.

    A link whose label names a designation is read by its label; any other is
    read beside the text before it, with the other links taken out.
    """
    label = re.search(r"\[([^\]\n]*)\]\($", written)
    if label and _DESIGNATION.search(label.group(1).translate(_SPACES)):
        return label.group(1)
    return _links_out(written[: label.start()] if label else written)


def _beside_in_frontmatter(text: str, start: int, end: int, catalogue: str) -> str:
    """What a link in a page's frontmatter is read beside.

    The ``url`` of a reference is read beside the reference's
    ``designation``. A link written in any other field, a ``note`` above all,
    is read beside that field's text up to the link, with the other links
    taken out, as a paragraph of the body is: a note that says "Since revised
    as ISO 3382-3:2022 (https://www.iso.org/standard/77437.html)" links the
    edition it names there, not the one its reference cites, and its link
    is held to ISO 3382-3:2022.

    A note that names no designation of the link's catalogue before the link
    ("The catalogue page (https://...) lists the corrigenda") speaks of its
    own reference, so its link is read beside the reference's
    ``designation``, as the ``url`` is. That still holds the number to a
    document: refusing the link would ask the note to repeat the designation
    its reference already gives, and letting it through would leave the
    number unread.
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
    written = _links_out(text[keys[-1].end() : start].lstrip("\"'"))
    return written if _names_a_designation(written, catalogue) else own


def _beside_in_body(text: str, start: int, catalogue: str) -> str:
    """What a link in a page's body is read beside.

    In a table, the link's own cell up to the link; when that names no
    designation of the link's catalogue (a cell that holds only
    "[catalogue](...)"), the nearest cell before it in the row that names
    one, with its links taken out. Anywhere else, the list item or paragraph
    the link is written in, up to it.
    """
    line_start = text.rfind("\n", 0, start) + 1
    line = text[line_start:start]
    if line.lstrip().startswith("|"):
        *cells, cell = _CELL_BORDER.split(line)
        own = _read_up_to(cell)
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
    return _read_up_to("\n".join(lines))


def _without_code(path: str, text: str) -> str:
    """The page with each line of a fenced or indented code block blanked.

    A catalogue address in a code block is an example of one, not a link a
    reader follows (rule F70 shows a wrong one as its counterexample). The
    lines keep their length, so every offset still points where it did.
    """
    lines = text.split("\n")
    return "\n".join(
        " " * len(line) if code else line
        for line, code in zip(
            lines, code_lines(lines, kind=page_kind(path)), strict=True
        )
    )


def links_in(path: str, text: str) -> list[Link]:
    """Every catalogue link of a page, with the text that should name its document."""
    end = _frontmatter_end(text)
    text = _without_code(path, text)
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


def _numbers(
    designation: str, catalogue: str
) -> tuple[set[str], str | None, Amendments]:
    """The numbers a text may give a pinned designation, its year and amendments."""
    match = _DESIGNATION.search(designation)
    if match is None:
        return set(), None, ()
    number, year = match.group(1), match.group(2)
    numbers = {number}
    head, _, rest = number.partition("-")
    if catalogue == "iec" and len(head) == 5 and head.startswith("60"):
        # IEC 651 is IEC 60651: the 1997 renumbering added 60000.
        numbers.add(str(int(head) - 60000) + ("-" + rest if rest else ""))
    return numbers, year, _amendments(match.group(3), catalogue)


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

    By its number and, when the text gives them, its year and its
    amendments: the edition, the edition with its amendment and the
    amendment alone are three documents, wherever their catalogue numbers
    them apart.
    """
    numbers, year, amended = _numbers(designation, catalogue)
    written = [
        (match.group(2), _amendments(match.group(3), catalogue))
        for match in _DESIGNATION.finditer(beside)
        if match.group(1) in numbers
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
