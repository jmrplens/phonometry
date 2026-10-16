#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Write the notes of a GitHub Release from the CHANGELOG section of its version.

The Release used to carry one sentence pointing at the changelog and the list
of pull request titles GitHub generated, so the page a reader reaches from
PyPI or Zenodo said nothing about the release itself. The changelog already
says it, under ``## [<version>] - <date>``; this lifts that section out as it
is written, so the release page and the changelog cannot disagree.

A Release body holds at most 125 000 characters, and a major version's section
can be several times that. When the section does not fit, the notes keep what
a reader needs first: the paragraphs before the first ``###`` heading, then
every subsection with the one-line bold title of each of its entries, which is
how the changelog writes them. The full section is one link away, at the tag.

It is also the check that the section exists. A release whose changelog still
files everything under ``[Unreleased]`` fails here, in the preflight, before
anything is built: the notes it would publish are empty.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent

#: A version heading: ``## [4.0.0] - 2026-10-20``.
_HEADING = re.compile(
    r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>\d{4}-\d{2}-\d{2}))?\s*$"
)

#: GitHub refuses a Release body over 125 000 characters; this leaves room
#: for the closing link and for the bytes a character can grow by in transit.
BODY_LIMIT = 100_000

_REPOSITORY = "https://github.com/jmrplens/phonometry"


def section(text: str, version: str) -> str:
    """The body of the changelog section of ``version``, without its heading.

    :param text: The whole CHANGELOG.
    :param version: The version, as ``VERSION`` writes it (``4.0.0rc1``).
    :return: The lines between the version's heading and the next one, with
        the blank lines around them stripped.
    :raises KeyError: The changelog has no section for ``version``.
    :raises ValueError: The section has no release date in its heading, or no
        text under it.
    """
    lines = text.splitlines()
    start: int | None = None
    end = len(lines)
    for index, line in enumerate(lines):
        match = _HEADING.match(line)
        if match is None:
            continue
        if start is not None:
            end = index
            break
        if match["version"] == version:
            if match["date"] is None:
                msg = f"the CHANGELOG heading of {version} carries no release date"
                raise ValueError(msg)
            start = index + 1
    if start is None:
        raise KeyError(version)
    body = "\n".join(lines[start:end]).strip()
    if not body:
        msg = f"the CHANGELOG section of {version} is empty"
        raise ValueError(msg)
    return body


def summary(body: str) -> str:
    """The section reduced to its opening paragraphs and its entry titles.

    A title is the bold sentence that opens an entry, and a long one wraps onto
    the next line, so it is read until its closing ``**``. A section collected
    over several merges repeats its subsections (``### Added`` more than
    once); their titles are gathered under one heading each, in the order the
    headings first appear.

    :param body: A changelog section, as :func:`section` returns it.
    :return: The paragraphs before the first ``###`` heading, then each
        subsection with a bullet for the title of every entry under it.
    """
    intro: list[str] = []
    groups: dict[str, list[str]] = {}
    current: str | None = None
    title: str | None = None
    for line in body.splitlines():
        if line.startswith("### "):
            current = line[4:].strip()
            groups.setdefault(current, [])
            title = None
            continue
        if current is None:
            intro.append(line)
            continue
        if line.startswith("- **"):
            title = line[4:]
        elif title is not None and line.strip():
            title = f"{title} {line.strip()}"
        else:
            title = None
            continue
        if "**" in title:
            groups[current].append(title.split("**", 1)[0].strip())
            title = None
    parts = ["\n".join(intro).strip()]
    for heading, titles in groups.items():
        if titles:
            parts.append(f"### {heading}\n\n" + "\n".join(f"- {t}" for t in titles))
    return "\n\n".join(part for part in parts if part)


def notes(text: str, version: str, *, limit: int = BODY_LIMIT) -> str:
    """The Release body for ``version``: its section, or its summary when too long.

    :param text: The whole CHANGELOG.
    :param version: The version being released.
    :param limit: The most characters the body may hold before the closing
        link.
    :return: The Markdown body, ending with a link to the changelog at the tag.
    :raises KeyError: The changelog has no section for ``version``.
    :raises ValueError: The section is undated or empty.
    """
    body = section(text, version)
    link = f"{_REPOSITORY}/blob/v{version}/CHANGELOG.md"
    if len(body) <= limit:
        return f"{body}\n\n---\n\nThe same notes are in the [changelog]({link}).\n"
    short = summary(body).strip()
    if len(short) > limit:
        cut = short.rfind("\n", 0, limit)
        short = short[: cut if cut > 0 else limit].rstrip() + "\n- ..."
    return (
        f"{short}\n\n---\n\nThis is the list of changes by title; each one is described "
        f"in full in the [changelog]({link}).\n"
    )


def main(argv: list[str] | None = None) -> int:
    """Write the notes of one release to a file, or report why there are none."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--version", help="the version to release (default: the VERSION file)"
    )
    parser.add_argument(
        "--changelog", type=pathlib.Path, default=_ROOT / "CHANGELOG.md"
    )
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    version = args.version or (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    try:
        body = notes(args.changelog.read_text(encoding="utf-8"), version)
    except KeyError:
        print(
            f"::error::CHANGELOG.md has no section '## [{version}] - <date>'; move the "
            "[Unreleased] notes under it before releasing.",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"::error::{exc}.", file=sys.stderr)
        return 1
    args.output.write_text(body, encoding="utf-8")
    print(
        f"Release notes for {version}: {len(body)} characters written to {args.output}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
