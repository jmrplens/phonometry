#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The GitHub edition of the guides, as the repository's Python checks tell it.

The pages under ``docs/`` a reader browses on GitHub, one per English guide of
the site, are written from the site's page sources by ``make llms``
(``site/scripts/agent-md.mjs --docs``), and each opens with a comment that
names the page it is written from. A check that reads the site's sources has
read what such a file says, and a check that rewrites text in place leaves it
to the generator, which writes it again from the source on its next run. The
other files of ``docs/`` open with no such comment: the ones written by hand
(the README, the API index, the errata registers and the contributor guide)
and the conformance report, which ``make conformance`` writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

#: How a file of the edition opens, before the path of its source page:
#: ``EDITION_MARK`` of ``site/src/lib/agent-md/edition.mjs``, followed by the
#: folder every source page sits in.
EDITION_MARK = "<!-- Written by `make llms` from site/src/content/docs/"


def is_edition_file(path: Path) -> bool:
    """Whether *path* is a file of the GitHub edition.

    :param path: A Markdown file under ``docs/``.
    :return: True when it opens with the edition's comment.
    """
    with path.open(encoding="utf-8") as handle:
        return handle.read(len(EDITION_MARK)) == EDITION_MARK
