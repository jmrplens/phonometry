#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Refuse a catalogue link that opens a document other than the one it sits beside.

A link to the ISO or IEC catalogue carries a number and nothing else
(``https://www.iso.org/standard/70242.html``,
``https://webstore.iec.ch/en/publication/1204``), so a slip of the number opens
another document while every page still builds, every link still resolves
and the reader who follows it lands on a steel sheet or a needle-based
injector. A review of the tone-burst guide found its reference to
IEC 60268-1:1985 opening IEC 60264-2-1:1989, and the sweep that followed
found 107 more links of the pages and their mirrors opening something other
than what they sat beside, many of them copied from page to page: 84 opened
another document or none at all (ISO 4871:1996 opened ISO 4878:1981,
ISO 16283-2:2020 two different plastics standards, each of the five
standards of the ISO 11200 series something else, and four parts of
ISO 10140 a number the catalogue does not hold), and 23 opened a later
edition than the one the page cites. This is the guard for that class.

The number alone cannot be read for its document, so :data:`PINNED`
(``scripts/catalogue_ids.json``) holds, for every number the pages link, the
designation its catalogue gives it: ISO's open data for an iso.org number,
the title of the webstore's own page for an IEC one. Every catalogue link in
the pages of the site and in the mirrors under ``docs/`` then has to sit
beside that designation, read where the link is written:

- in a page's frontmatter, the ``designation`` of the reference that carries
  the ``url``;
- in a table, the cell before the link;
- anywhere else, the paragraph or list item up to the link, with the text of
  the other links taken out, so that a "since revised as" link to a newer
  edition names that edition and the entry's own catalogue link names the one
  the entry cites.

The designation is matched by its number and, when the text gives one, its
year: the catalogue page of ISO 717-2:2013 beside "ISO 717-2:2020" is another
document, the edition the page does not cite. IEC renumbered its older
publications by adding 60000 in 1997, so "IEC 651" names what the webstore
lists as IEC 60651.

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

#: The number of a designation and the year right after it.
_DESIGNATION = re.compile(r"(?<![\w.-])(\d+(?:-\d+)*)(?::(\d{4}))?")

#: The characters a page may write inside a designation for a space or a
#: hyphen.
_SPACES = str.maketrans(
    {"\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2011": "-", "\u2010": "-"}
)


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


def _beside_in_frontmatter(text: str, start: int, end: int) -> str:
    """The designation of the reference whose ``url`` is at ``start``."""
    item_start = text.rfind("\n  - ", 0, start)
    item_end = text.find("\n  - ", start)
    if item_end < 0 or item_end > end:
        item_end = end
    item = text[item_start:item_end]
    designation = re.search(r'^\s*designation:\s*"([^"]*)"', item, re.MULTILINE)
    return designation.group(1) if designation else ""


def _beside_in_body(text: str, start: int) -> str:
    """The cell, list item or paragraph a body link is written in, up to it."""
    line_start = text.rfind("\n", 0, start) + 1
    line = text[line_start:start]
    if line.lstrip().startswith("|"):
        return line.rsplit("|", 1)[-1]
    lines = [line]
    cursor = line_start
    while not _BLOCK_START.match(lines[0]) and cursor > 0:
        previous_start = text.rfind("\n", 0, cursor - 1) + 1
        previous = text[previous_start : cursor - 1]
        if not previous.strip():
            break
        lines.insert(0, previous)
        cursor = previous_start
    return "\n".join(lines)


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
            beside = _beside_in_frontmatter(text, start, end)
        else:
            body = _beside_in_body(text, start)
            # A link the label of which names a designation is read by its
            # label; any other is read beside its text, the other links out.
            label = re.search(r"\[([^\]\n]*)\]\($", body)
            if label and _DESIGNATION.search(label.group(1).translate(_SPACES)):
                beside = label.group(1)
            else:
                beside = MARKDOWN_LINK.sub(
                    " ", body[: label.start()] if label else body
                )
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


def _numbers(designation: str, catalogue: str) -> tuple[set[str], str | None]:
    """The numbers a text may give a pinned designation, and the year it carries."""
    match = _DESIGNATION.search(designation)
    if match is None:
        return set(), None
    number, year = match.group(1), match.group(2)
    numbers = {number}
    head, _, rest = number.partition("-")
    if catalogue == "iec" and len(head) == 5 and head.startswith("60"):
        # IEC 651 is IEC 60651: the 1997 renumbering added 60000.
        numbers.add(str(int(head) - 60000) + ("-" + rest if rest else ""))
    return numbers, year


def names(beside: str, designation: str, catalogue: str) -> bool:
    """Whether ``beside`` names ``designation``, by number and, when given, year."""
    numbers, year = _numbers(designation, catalogue)
    years = [
        match.group(2)
        for match in _DESIGNATION.finditer(beside)
        if match.group(1) in numbers
    ]
    if not years:
        return False
    given = [found for found in years if found]
    return not given or year is None or year in given


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
