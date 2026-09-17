#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Reading a published table out of a data file (private).

A catalogue row is data, not code. Keeping the rows in JSON beside the module
that publishes them means a new table is a new file rather than a longer
literal, means one row per record in a diff, and means the provenance gate can
read the citation without importing anything.

The document is one published table: a ``source`` in the grammar
``scripts/check_published_sources.py`` enforces, an ``about`` paragraph saying
what the page is and how it was read, and ``rows``. Every row carries a ``key``
unique within the file, and the rest of its fields are named exactly as the
dataclass that will hold them, so a typo in the data is a ``TypeError`` at
import and not a silently missing column.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

_REQUIRED = ("source", "about", "rows")


class CatalogueError(ValueError):
    """A packaged table that does not say what the reader needs to trust it."""


def _reject(filename: str, what: str) -> None:
    """Name the file and the defect, because the caller cannot see either."""
    msg = f"{filename}: {what}"
    raise CatalogueError(msg)


def read_table(package: str, filename: str) -> tuple[str, tuple[dict[str, Any], ...]]:
    """Read one published table from a package's ``data`` directory.

    :param package: The package that owns the data, as ``phonometry.solids``.
        The file is read from its ``data`` subpackage.
    :param filename: The file name inside ``data``, including the extension.
    :return: The citation every row of the file shares, and the rows in the
        order the file lists them, each a plain dictionary ready to be passed
        to the dataclass that holds it.
    :raises CatalogueError: when the document is missing a top-level key, when
        ``rows`` is empty, or when two rows share a key.
    """
    from importlib.resources import files

    text = (files(f"{package}.data") / filename).read_text(encoding="utf-8")
    document = json.loads(text)
    for key in _REQUIRED:
        if key not in document:
            _reject(filename, f"a published table needs a top-level {key!r}")
    rows = document["rows"]
    if not rows:
        _reject(filename, "a published table with no rows publishes nothing")
    seen: set[str] = set()
    for row in rows:
        key = row.get("key")
        if key is None:
            _reject(filename, "every row needs a key of its own")
        if key in seen:
            _reject(filename, f"two rows share the key {key!r}")
        seen.add(key)
    return document["source"], tuple(rows)


def take(row: Mapping[str, Any], *, frozen: tuple[str, ...] = ()) -> dict[str, Any]:
    """The row as constructor keywords: no ``key``, and the named sets frozen.

    :param row: One row as :func:`read_table` returned it.
    :param frozen: Fields the JSON lists but the dataclass holds as a
        ``frozenset``, because a set has no order and a list implies one.
    :return: The remaining fields, ready to splat into the dataclass.
    """
    fields = {name: value for name, value in row.items() if name != "key"}
    for name in frozen:
        if name in fields:
            fields[name] = frozenset(fields[name])
    ranges = fields.get("ranges")
    if ranges is not None:
        fields["ranges"] = {name: tuple(pair) for name, pair in ranges.items()}
    return fields
