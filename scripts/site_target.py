#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The hosts the site is built for, read from the file the site build reads.

``site/src/data/site-targets.json`` holds, for each host the site can be built
for, its origin and the base path the pages are served under, and names the
target a build with ``PHONOMETRY_SITE`` unset or empty is made for.
``site/src/data/site.mjs`` serves the same file to the build, the site scripts
and the Worker; this module serves it to the generators that write site links:
``generate_api_docs.py`` (the API reference), ``generate_site_reports.py``
(the errata pages) and ``generate_llms.py`` (the llms files). One file, read
by both languages, so a base path cannot lag in one of them, and no Python
code reads JavaScript to find it.
"""

from __future__ import annotations

import functools
import json
import pathlib
import re
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
#: The targets, as the site build reads them.
TARGETS = ROOT / "site" / "src" / "data" / "site-targets.json"

#: A base path: empty, or segments each led by ``/``, with no ``/`` at the
#: end, since every reader appends ``/<route>/`` to it. site.mjs holds the
#: file to the same shape.
_BASE_PATH = re.compile(r"(?:/[a-z0-9-]+)*")
#: An origin: ``https://`` and a host, nothing after it, a port neither.
#: site.mjs refuses the same values, a port among them, so a target the build
#: accepts never stops a generator here.
_ORIGIN = re.compile(r"https://[a-z0-9.-]+")


class Target(NamedTuple):
    """One host the site is built for."""

    #: The origin, ``https://host``, with no path and no trailing slash.
    site_url: str
    #: The path the pages are served under: empty at the root, or a path
    #: such as ``/docs``.
    base_path: str


class _Table(NamedTuple):
    default: str
    targets: dict[str, Target]


def _string(value: object, what: str) -> str:
    if not isinstance(value, str):
        msg = f"{TARGETS.name}: {what} is not a string: {value!r}"
        raise TypeError(msg)
    return value


@functools.cache
def _table(path: pathlib.Path = TARGETS) -> _Table:
    """The targets and the default, read once and checked.

    :param path: The file, site-targets.json unless a test hands another.
    :return: The default target's name and every target by name.
    :raises ValueError: When an origin or a base path has the wrong shape, or
        the default names no target.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    targets: dict[str, Target] = {}
    for name, entry in dict(data["targets"]).items():
        site_url = _string(entry["siteUrl"], f"the siteUrl of {name}")
        base_path = _string(entry["basePath"], f"the basePath of {name}")
        if _ORIGIN.fullmatch(site_url) is None:
            msg = f"{path.name}: the siteUrl of {name} is not an https origin with no port: {site_url!r}"
            raise ValueError(msg)
        if _BASE_PATH.fullmatch(base_path) is None:
            msg = f"{path.name}: the basePath of {name} is neither empty nor /segment: {base_path!r}"
            raise ValueError(msg)
        targets[_string(name, "a target name")] = Target(site_url, base_path)
    default = _string(data["default"], "the default")
    if default not in targets:
        msg = f"{path.name}: the default {default} is not one of {', '.join(targets)}"
        raise ValueError(msg)
    return _Table(default, targets)


def target(name: str | None) -> Target:
    """The target a value of ``PHONOMETRY_SITE`` names, as the site build reads it.

    :param name: The variable's value, or None when it is not set; unset or
        empty names the default target.
    :return: Its origin and base path.
    :raises ValueError: For any other value, worded as the site build words it.
    """
    table = _table()
    key = name or table.default
    if key not in table.targets:
        msg = f"PHONOMETRY_SITE={name} is not one of {', '.join(table.targets)}"
        raise ValueError(msg)
    return table.targets[key]


def site_url(name: str | None) -> str:
    """The origin of the target *name* names: ``https://host``.

    :param name: The value of ``PHONOMETRY_SITE``, or None.
    :return: The origin, without a path or a trailing slash.
    :raises ValueError: For a value that names no target.
    """
    return target(name).site_url


def base_path(name: str | None) -> str:
    """The base path of the target *name* names: empty at the root, or a path.

    :param name: The value of ``PHONOMETRY_SITE``, or None.
    :return: The base path, without a trailing slash.
    :raises ValueError: For a value that names no target.
    """
    return target(name).base_path


def targets() -> dict[str, Target]:
    """Every target by name, in the order the file lists them.

    :return: A fresh dict, so a caller cannot change what the next one reads.
    """
    return dict(_table().targets)
