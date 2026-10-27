#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Refuse an install command whose extras are not quoted.

zsh, the default shell on macOS, reads the brackets of an extras requirement
as a glob and stops with "no matches found" before pip runs, so every install
command the project publishes quotes the requirement that carries extras, as
in ``pip install "phonometry[torch]"`` and ``pip install -e ".[full]"``. This
reads every tracked text file a reader copies a command from (the pages and
their mirrors, the site's home page, the docstrings and the messages the
library raises, the README, the llms files, the CHANGELOG, the workflows and
the Makefile) and names each command with an unquoted one, by file and line.

A command is pip, pip3, ``python -m pip``, ``uv pip``, ``uv add`` or pipx,
then install or add; a sentence that names an extra without installing it is
not one. A command is read on its line and, when its requirement wraps, as a
docstring wraps where its width says, on the next one too. A requirement is
one word of the command, so a quote that opens it quotes all of it, a path
or a variable inside included
(``"dist/phonometry-$VERSION-py3-none-any.whl[full]"``). Two exemptions, each
with its reason: the tests, which are not published; and a line that shows
zsh's own "no matches found", which is the failure shown on purpose (a rule's
counterexample).

Exit status 0 when every command is quoted, 1 otherwise. Standard library
only, so it runs in a job that installs nothing.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

#: An install command, up to a requirement with extras that no quote opens:
#: a word that starts after a blank with no quote, no backtick and no
#: bracket, and carries ``[extra,...]``.
COMMAND = re.compile(
    r"\b(?:pip3?|uv\s+pip|uv|pipx)\s+(?:install|add)\b[^\n`]*?"
    r"(?<=\s)[^\s\"'`\[\]]+\[[\w,.-]+\]"
)

#: A line that ends inside an install command, before its requirement: its
#: last word is the program, the subcommand or an option.
_OPEN_END = re.compile(r"(?:\bpip3?|\binstall|\badd|(?<!\S)--?[\w-]+)\s*$")

#: The failure shown on purpose: zsh's own message.
_SHOWN = "no matches found"

#: The file kinds a command is copied from.
_SUFFIXES = frozenset(
    {
        ".astro",
        ".cfg",
        ".cjs",
        ".ipynb",
        ".js",
        ".json",
        ".md",
        ".mdx",
        ".mjs",
        ".mts",
        ".py",
        ".pyi",
        ".rst",
        ".sh",
        ".toml",
        ".ts",
        ".txt",
        ".yaml",
        ".yml",
    }
)
_NAMES = frozenset({"Dockerfile", "Makefile"})

#: Tracked paths left out: the tests are not published.
SKIPPED = ("tests/",)

#: How long ``git ls-files`` may take [s].
_GIT_S = 60.0


def _wrapped(line: str, following: str) -> re.Match[str] | None:
    """A command that starts on *line* and whose requirement wraps onto *following*.

    A docstring or a paragraph wraps where its width says, so
    ``pip install`` can end one line and the requirement start the next.
    *following* is read only when *line* ends inside the command, its last
    word the program, the subcommand or an option: a command that is whole
    on its line (``pip install phonometry``) takes nothing from the next one,
    whatever bracket it holds (``>>> levels[0]``). The two lines are then
    read as one, joined by a blank; a match counts only when the command
    starts on *line* and *following* holds none of its own, which is named
    on its own line.
    """
    if _OPEN_END.search(line) is None or COMMAND.search(following) is not None:
        return None
    match = COMMAND.search(f"{line} {following.lstrip()}")
    if match is None or match.start() >= len(line):
        return None
    return match


def problems(text: str, label: str) -> list[str]:
    """Each install command in *text* with unquoted extras, as ``label:line: command``.

    A command is named by the line it starts on, also when its requirement
    wraps onto the next line (:func:`_wrapped`).
    """
    found: list[str] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        read = line
        match = COMMAND.search(line)
        if match is None and number < len(lines):
            read = f"{line} {lines[number]}"
            match = _wrapped(line, lines[number])
        if match is not None and _SHOWN not in read:
            found.append(f"{label}:{number}: {match.group(0).strip()}")
    return found


def tracked_files(root: pathlib.Path) -> list[pathlib.Path]:
    """The tracked text files under *root* a reader may copy a command from.

    :raises subprocess.CalledProcessError: when *root* is not a git checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in :data:`_GIT_S`.
    """
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=True,
        timeout=_GIT_S,
    ).stdout
    paths: list[pathlib.Path] = []
    for name in listing.split("\0"):
        if not name or name.startswith(SKIPPED):
            continue
        path = root / name
        if (path.suffix in _SUFFIXES or path.name in _NAMES) and path.is_file():
            paths.append(path)
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    """Name every install command with unquoted extras; 0 when there is none.

    :raises SystemExit: for arguments this command does not take.
    :raises subprocess.CalledProcessError: when the root is not a git checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "root",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent.parent,
        help="the checkout to read (default: this one)",
    )
    args = parser.parse_args(argv)
    found = [
        problem
        for path in tracked_files(args.root)
        for problem in problems(
            path.read_text(encoding="utf-8", errors="replace"),
            path.relative_to(args.root).as_posix(),
        )
    ]
    for line in found:
        sys.stdout.write(f"::error::{line}\n")
    if not found:
        sys.stdout.write("Every install command quotes its extras.\n")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
