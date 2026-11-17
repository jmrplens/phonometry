#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Dumps of the site's pages, as ``site/scripts/agent-md.mjs --dump`` writes one.

``scripts/generate_llms.py`` reads nothing of a page but the dump: a
``routes.json`` naming every English route with its kind, title and the path
of its Markdown copy, and the copies themselves. The tests that run it have no
Node to write a real dump with, so this writes dumps of the same shape: small
ones of a few pages written for one test, and one of the whole English site,
with every route the content tree has and, for a copy, the page's source under
a header, which keeps the headings, the tables and the sizes of the real pages
close enough for the shards to fall where they do.
"""

from __future__ import annotations

import json
import pathlib
import re

import yaml

#: The site's content collection, which a dump of the whole site is read from.
CONTENT_ROOT = (
    pathlib.Path(__file__).resolve().parents[1] / "site" / "src" / "content" / "docs"
)

SITE_URL = "https://docs.jmrp.io/phonometry"

#: The sentence under every copy's title (site/src/lib/agent-md/header.mjs).
LEAD = (
    "> One page of the phonometry documentation, as Markdown. "
    f"Index: {SITE_URL}/llms.txt"
)

#: The kinds whose copies a dump holds (site/src/lib/page-markdown.mjs
#: ``FULL_TEXT_KINDS``).
FULL_TEXT_KINDS = frozenset({"guide", "catalogue", "errata-family"})

#: The frontmatter block at the head of a page source.
_FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)


def page_kind(route: str) -> str:
    """The kind of a route, as site/src/lib/page-markdown.mjs ``pageKind`` says.

    A port, held with ``pageKind`` itself to one table of routes and kinds
    (site/src/lib/agent-md/test/page-kinds.json) by
    tests/test_generate_llms.py and site/src/lib/agent-md/test/dump.test.mjs.
    """
    english = "" if route == "es" else route.removeprefix("es/")
    if english == "":
        return "home"
    if re.match(r"reference/api(?:/|$)", english):
        return "api"
    if re.fullmatch(r"reference/catalogues/[^/]+", english):
        return "catalogue"
    if re.fullmatch(r"reference/errata/[^/]+", english):
        return "errata-family"
    return "guide"


def copy_text(
    route: str,
    body: str,
    *,
    title: str = "A page",
    dated: bool = True,
    license_line: bool = True,
) -> str:
    """A Markdown copy as the site writes one: title, lead, header and body.

    ``dated`` writes the two lines git dates (``Published:`` and
    ``Updated:``), which ``agent-md.mjs --dump --undated`` leaves out.
    """
    canonical = f"{SITE_URL}/{route}/" if route else f"{SITE_URL}/"
    lines = [
        f"# {title}",
        "",
        LEAD,
        "",
        f"Canonical: {canonical}",
        "Language: en",
        "Version: phonometry 4.0.0",
        'Install: pip install "phonometry[full]"',
        "Author: José Manuel Requena Plens (https://orcid.org/0000-0003-1250-6212)",
        *(["Published: 2026-01-06", "Updated: 2026-10-20T10:00:00Z"] if dated else []),
        *(
            ["License: MIT (https://github.com/jmrplens/phonometry/blob/main/LICENSE)"]
            if license_line
            else []
        ),
        "Summary: What the page is about.",
        "",
        "---",
    ]
    text = "\n".join(lines)
    return f"{text}\n\n{body}\n" if body else f"{text}\n"


class Dump:
    """A dump written page by page into a directory."""

    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.pages: list[dict[str, object]] = []
        self.write()

    def add(
        self,
        route: str,
        body: str = "The body.",
        *,
        title: str | None = None,
        kind: str | None = None,
        dated: bool = True,
        description: str = "What the page is about.",
        write: bool = True,
    ) -> str:
        """Adds one page, with its copy when its kind is one the dump carries.

        ``write=False`` leaves routes.json as it was, for a caller adding many
        pages that writes it once at the end (:meth:`write`).
        """
        kind = page_kind(route) if kind is None else kind
        carried = kind in FULL_TEXT_KINDS
        name = title if title is not None else f"Page {route}"
        if carried:
            target = self.root / route / "index.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                copy_text(
                    route,
                    body,
                    title=name,
                    dated=dated,
                    license_line=kind != "catalogue",
                ),
                encoding="utf-8",
            )
        self.pages.append(
            {
                "route": route,
                "kind": kind,
                "title": name,
                "description": description,
                "standards": [],
                "copy": f"{route}/index.md" if carried else None,
            }
        )
        if write:
            self.write()
        return route

    def write(self) -> None:
        """Writes routes.json as the pages stand."""
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "routes.json").write_text(
            json.dumps({"pages": self.pages}, indent=1) + "\n", encoding="utf-8"
        )


def site_dump(root: pathlib.Path, content: pathlib.Path, *, dated: bool = True) -> Dump:
    """A dump of every English page under *content*, each copy its own source.

    The copy of a page is its source after the frontmatter under a header:
    not what the renderer writes, but the same headings, tables and size,
    which is what decides where the shards fall.
    """
    dump = Dump(root)
    for path in sorted(content.rglob("*.md*")):
        relative = path.relative_to(content).with_suffix("").as_posix()
        if relative.split("/")[0] == "es":
            continue
        route = re.sub(r"(?:^|/)index$", "", relative)
        source = path.read_text(encoding="utf-8")
        head = _FRONTMATTER.match(source)
        data = yaml.safe_load(head.group(1)) if head else {}
        body = source[head.end() :] if head else source
        title = str(data.get("title", route)) if isinstance(data, dict) else route
        dump.add(route, body.strip("\n"), title=title, dated=dated, write=False)
    dump.write()
    return dump
